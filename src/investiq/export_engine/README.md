Une infrastructure modulaire, déterministe et extensible pour construire des **pipelines d’export** robustes.  

Utilisée dans _InvestIQ-v1_ (moteur de trading/backtesting), documentée séparément ici afin d’être **réutilisable dans tout autre projet**.

---
# 1. Objectif

Ce moteur fournit une abstraction générique pour exécuter des exports structurés en **trois étapes** :

1. **Formatage** d’un ensemble de données brutes (`RawT → FormattedT`)
2. **Encodage** en représentation persistable (`FormattedT → EncodedT`)
3. **Persistance atomique** de l’artefact (`EncodedT → Artifact`)

Chaque étape est isolée dans une classe dédiée, avec un **cycle de vie strict** garantissant :

- déterminisme,
- absence d’effets de bord,
- persistance atomique,
- gestion propre des erreurs,
- testabilité.

L’architecture peut être utilisée pour exporter :

- fichiers JSON, CSV, Parquet
- rapports de backtests
- snapshots de marché
- données agrégées
- logs structurés
- n’importe quel artefact sérialisable

---
# 2. Architecture Générale

```sql
RawT ──► Formatter ──► FormattedT ──► WriterCore ──► EncodedT ──► Sink ──► Artifact
```

Chaque transformation est explicitement typée.

---

# 3. Composants
## 2.1 BatchFormatter :  Formatage (RawT → FormattedT)

Un **BatchFormatter** est un composant purement fonctionnel dont la responsabilité est de **convertir un ensemble de données brutes `RawT` en une structure intermédiaire `FormattedT`**.

Il s’agit d’une transformation totale :
$$Iterable[RawT] \rightarrow FormattedT$$
Aucune I/O n’est autorisée : le Formatter ne fait **que du calcul en mémoire**.

### Rôle du Formatter

- Construire la représentation structurée utilisée par le `WriterCore`.
- Appliquer éventuellement une **validation élémentaire** sur chaque `RawT` via un validateur optionnel.
- Fournir la **première étape du pipeline**, strictement déterministe.

### Méthode à implémenter : `_format`

Les sous-classes doivent implémenter le hook :
``` python
def _format(self, data: Iterable[RawT]) -> FormattedT:
    ...
```

Cette méthode contient **toute** la logique de transformation.

La méthode publique `format(...)` se charge :

- d'appeler le validateur optionnel (`raw_validator`)
- de tracer les erreurs
- d’appeler `_format(...)`

### Exemple
``` python
class OrderFormatter(BatchFormatter[RawOrder, StructuredOrders]):
    """
    Convertit une séquence de RawOrder en un objet StructuredOrders.
    Aucun I/O. Transformation pure et déterministe.
    """

    def _format(self, data: Iterable[RawOrder]) -> StructuredOrders:
        # Toute la logique métier de transformation est ici.
        return StructuredOrders.from_raw(data)
```
### Points importants :

- **Validation**  
    Si un `raw_validator` est fourni à l’initialisation, il sera appliqué automatiquement à chaque `RawOrder` avant `_format`.

- **Pureté**  
    Le Formatter ne doit pas écrire de fichiers, ni communiquer avec un service, ni effectuer d’I/O quelconque.

- **Unicité du rôle**  
    Il sert exclusivement à **préparer une représentation structurée** pour l’étape suivante (WriterCore).

## 2.2 BatchWriterCore : Encodage (FormattedT → EncodedT)

Le **BatchWriterCore** est le composant responsable de l’**encodage** du résultat formaté (`FormattedT`) en un artefact sérialisé (`EncodedT`) prêt à être persisté.

Il correspond à la transformation :
$$FormattedT \rightarrow EncodedT$$

Cette étape est strictement **sans I/O** : le WriterCore ne touche jamais au disque, ni au réseau.  
Son rôle est purement algorithmique : sérialisation, compression, conversion de structure, etc.

---
### Rôle du WriterCore

- Préparer un artefact encodé prêt à être écrit par le `BatchSink`.
- Garantir un **encodage déterministe** : même `FormattedT` → même `EncodedT`.
- Gérer un **cycle de vie explicite et sécurisé**.
- Ne jamais interagir avec des ressources externes (aucun I/O).

C’est une brique **pure**, isolée, contrôlée, essentielle pour la reproductibilité.

---
### Cycle de vie

Le WriterCore suit un automate strict :
```sql
NEW → STARTED → ENCODED → ENDED
              ↘ ERROR ↗
```
Signification :

- `NEW` → instance initialisée
- `STARTED` → ressource ou buffer interne prêt
- `ENCODED` → un encodage a été produit
- `ENDED` → finalisation propre
- `ERROR` → état terminal en cas d’échec

Toutes les transitions illégales déclenchent un `ExportError`.

### Méthodes à implémenter

Les sous-classes doivent implémenter **cinq hooks internes** :
```python
def _start(self) -> None: ...
def _encode(self, data: FormattedT) -> EncodedT: ...
def _finalize_empty(self) -> None: ...
def _finalize(self) -> None: ...
def _cleanup_after_error(self) -> None: ...
```
#### Leur rôle :

- **_start()** : préparer l’état interne (buffers, tables, accumulateurs).
- **_encode()** : transformer `FormattedT` en `EncodedT`.
- **_finalize()** : nettoyer et terminer après encodage.
- **_finalize_empty()** : cas particulier si aucun encode n’a été appelé.
- **_cleanup_after_error()** : nettoyage minimal en cas d’exception.

Les méthodes publiques (`on_start`, `on_encode`, `on_end`) sont déjà implémentées et **orchestrées** par la classe de base : l’utilisateur ne les surcharge jamais.

---

### Exemple minimal
``` python
class JsonWriterCore(BatchWriterCore[StructuredOrders, bytes]):
    """
    Encode StructuredOrders en bytes JSON.
    Aucun I/O : uniquement du calcul en mémoire.
    """

    def _start(self):
        # Initialisation optionnelle
        pass

    def _encode(self, data: StructuredOrders) -> bytes:
        return json.dumps(data.to_dict()).encode()

    def _finalize(self):
        # Rien de spécial ici
        pass

    def _finalize_empty(self):
        # Si aucun encode n'a été appelé
        pass

    def _cleanup_after_error(self):
        # Nettoyage minimal
        pass
```


## 2.3 BatchSink : Persistance atomique (EncodedT → Artifact)

Le **BatchSink** est la composante responsable de la **persistance** de l’artefact encodé.  
C’est la seule partie du pipeline autorisée à faire de l’I/O.

Transformée conceptuelle :
$$EncodedT \rightarrow Artifact$$
Le Sink prend un artefact déjà encodé (`EncodedT`) et le rend **durable**, de manière atomique (une seule réussite possible, jamais partielle).

---
### 3.1. Rôle du BatchSink

Un Sink :

- écrit des artefacts sur un support (fichier, cloud, base de données, mémoire partagée…),
- garantit qu’un **unique commit** est possible,
- empêche la génération d’artefacts partiels,
- fournit un mécanisme de **rollback** si le pipeline se ferme sans commit,
- assure un nettoyage après erreur.

Le Sink est le composant qui impose les invariants d’I/O du système.

---
### Cycle de vie strict

Le Sink suit un automate contrôlé par la classe de base :
``` sql
NEW → OPENED → COMMITTED → CLOSED
         ↘ ERROR ↗
```

- **NEW** : non initialisé.
- **OPENED** : prêt à écrire.
- **COMMITTED** : persistance atomique réussie.
- **CLOSED** : ressources libérées.
- **ERROR** : état terminal après échec.

Toute transition illégale lève un `ExportError`.

---
### 3.3. Méthodes à implémenter

Les sous-classes doivent uniquement fournir **six hooks internes**, la classe abstraite s’occupant du reste :
```python
def _open(self) -> None: ...
def _write(self, data: EncodedT) -> None: ...
def _commit(self) -> None: ...
def _rollback(self) -> None: ...
def _finalize_resources(self) -> None: ...
def _cleanup_after_error(self) -> None: ...
```
#### Signification des hooks :

**_open()**
- Allocation des ressources (fichier temporaire, connexion, buffer…)
- Jamais de données écrites ici.

**_write(data)**
- Persisté ou mis en tampon.
- Autorisé uniquement en état OPENED.
**_commit()**
- Opération atomique (rename, transaction commit, upload final…).
- Doit être **idempotente**.

**_rollback()**
- Nettoie toute écriture non validée.
- Appelé automatiquement si fermeture sans commit.

**_finalize_resources()**
- Libère les ressources après un commit réussi.

**_cleanup_after_error()**
- Nettoie l’état du système (artefacts partiels, buffers).
- Ne doit jamais lever d'exception.

---
### 3.4 Exemple concret
```python
class JsonFileSink(BatchSink[bytes]):
    """
    Persistance atomique d'un fichier JSON encodé en bytes.
    """
    def _open(self):
        self._tmp = open(self.tmp_path, "wb")

    def _write(self, data: bytes):
        self._tmp.write(data)

    def _commit(self):
        os.rename(self.tmp_path, self.final_path)

    def _rollback(self):
        safe_delete(self.tmp_path)

    def _finalize_resources(self):
        self._tmp.close()

    def _cleanup_after_error(self):
        safe_delete(self.tmp_path)
```


## 2.4 BatchWriter : Orchestrateur contrôlé WriterCore/Sink

Le **BatchWriter** est le composant qui orchestre l’interaction entre :

- le **BatchWriterCore** _(encodage, sans I/O)_
- le **BatchSink** _(persistance atomique)_

Il constitue la couche de coordination du pipeline d’export.  
Son rôle est de garantir une séquence d’opérations **déterministe**, **sécurisée** et **correctement ordonnancée**, quelles que soient les erreurs rencontrées.

Transformée conceptuelle :
$$FormattedT\rightarrow(EncodedT\rightarrow Artifact)$$
---

### 4.1. Rôle du BatchWriter

Le `BatchWriter` :

1. initialise le WriterCore et le Sink,
2. encode les données formatées,
3. valide les données si des validateurs sont présents,
4. persiste l’artefact via le Sink,
5. applique un commit atomique,
6. garantit un nettoyage systématique des ressources (même en cas d’exception).

Il agit comme le **cerveau du pipeline** : il impose l’ordre correct des opérations et empêche toute utilisation illégale de l’infrastructure.

---
### 4.2 Cycle de vie strict

Le BatchWriter suit un automate clair :
```sql
NEW → ACTIVE → COMMITTED → CLOSED
         ↘ ERROR ↗
```
- **NEW** : non initialisé.
- **ACTIVE** : Core et Sink ouverts, prêts à écrire.
- **COMMITTED** : persistance garantie.
- **CLOSED** : ressources libérées, Writer consommé.
- **ERROR** : état irréversible après échec (interdit toute écriture future).

Tout appel invalide (`write` hors ACTIVE, `commit` hors ACTIVE…) déclenche un `ExportError`.

---
### 4.3. Méthodes publiques (non surchargées)

Les sous-classes ne redéfinissent jamais les méthodes publiques.  
Le `BatchWriter` impose toute la logique d’orchestration : les sous-classes ne font qu’hériter.

#### 1. start()

Initialise le WriterCore et ouvre le Sink.

Séquence :
```python
_core.on_start()
_sink.open()
_state = ACTIVE
```

#### 2. write(formatted)

Applique la chaîne complète :
```sql
formatted → validate → encode → validate → write
```

- validation optionnelle du `FormattedT`,
- encodage via `_writer_core.on_encode`,
- validation optionnelle de `EncodedT`,
- écriture via `_sink.write`.

#### 3. commit()

Finalise le WriterCore et effectue un commit atomique du Sink.

Séquence :
```python
_writer_core.on_end()
_sink.commit()
_state = COMMITTED
```

#### 4. close()

Ferme le Sink proprement selon l’état courant :

- COMMITTED → fermeture normale
- ACTIVE → rollback automatique
- ERROR → nettoyage minimal
- CLOSED → no-op

Cette méthode est toujours appelée automatiquement via le context manager.

---

### 4.4 Usage typique 
```python
with writer:
    writer.write(formatted_data)
    writer.commit()
```

Sémantique :
- l’ouverture (`start`) se fait en entrée du `with`
- la fermeture (`close`) est garantie par `__exit__`, même en cas d’exception
- aucune fuite de ressources n’est possible

---
### 4.5 Exemple minimal
``` python
writer = BatchWriter(
    logger=my_logger,
    writer_core=my_core,
    sink=my_sink
)

with writer:
    writer.write(formatted)
    writer.commit()
```

Le BatchWriter ne contient aucune logique métier :  
il ne fait qu’imposer le **cycle de vie** et orchestrer les composants.


## 2.5 BatchExportService : Pipeline utilisateur

Il combine :

- un **BatchFormatter** (RawT → FormattedT)
- un **BatchWriter** (FormattedT → EncodedT → Artifact)

L’utilisateur ne manipule ni WriterCore ni Sink :  
le service encapsule toute la logique interne du pipeline.

Transformation conceptuelle : 
$$Iterable[RawT] \rightarrow Artifact$$
---
### 5.1 Rôle du BatchExportService

Le service :

1. **valide et formatte** les données brutes,
2. **ouvre le writer**,
3. **encode + persist**,
4. **commit**,
5. **assure la fermeture propre**, même en cas d’exception.

Il représente l’API finale destinée à l’utilisateur ou au moteur de backtest.

### 5.2. Méthode principale : `export(raw_data)`

``` python
service.export(raw_data)
```

Séquence interne :
``` python
formatted = formatter.format(raw_data)
with writer:
    writer.write(formatted)
    writer.commit()
```

Garanties :

- toutes les erreurs sont capturées et converties en `ExportError`,
- le Sink est toujours fermé,
- aucun artefact partiel n’est jamais produit.

### 5.3. Exemple minimal

``` python
service = BatchExportService(
    logger=my_logger,
    formatter=OrderFormatter(...),
    writer=OrderWriter(...)
)

service.export(raw_orders)
```

## 2.6 Registre et composition dynamique

Le moteur utilise un système de **registres** pour déclarer les pipelines d’export disponibles.

Un registre est une simple correspondance :
``` sql
ExportKey → BatchExportBinding
```

Un **BatchExportBinding** décrit entièrement un pipeline :

- formatter_cls
- writer_core_cls
- sink_cls
- writer_cls (optionnel)

Le registre ne fait _rien d’autre_.  
Il **stocke** simplement les bindings déclarés.

---
### 6.1 Rôle du Binding : invariants structurels

Le binding est l’unique endroit où la **cohérence structurelle** est imposée :

$$
\mathrm{RawT}
\;\xrightarrow{\mathrm{Formatter}}\;
\mathrm{FormattedT}

\;\xrightarrow{\mathrm{WriterCore}}\;
\mathrm{EncodedT}

\;\xrightarrow{\mathrm{Sink}}\;
\mathrm{Artifact}
$$

Si ces relations ne s’alignent pas, le binding ne peut pas être construit.

---
### 6.2 ## Rôle du Registry : stockage uniquement

Le registre :

- ne valide pas les types,
- n’instancie rien,
- ne fait aucune logique,
- ne manipule que des références.

C’est un **annuaire**.

---
### 6.3 Rôle de la Factory : composition runtime

La factory prend un binding stocké dans le registre et construit un pipeline complet :

``` sql
binding → formatter, writer_core, sink → BatchExportService
```

Elle :

- instancie les classes,
- injecte logger et options,
- vérifie l’instanciabilité runtime,
- assemble un service complètement fonctionnel.

La cohérence structurelle n’est _pas_ son rôle : elle repose sur les bindings.

---
### 6.4 Exemple : récupération d'un pipeline

``` python
service = factory.create_backtest_batch_export_service(ExportKey.ORDERS)
service.export(raw_orders)
```

---

# 4. Guide d'utilisation complet

Cette section montre à l’utilisateur comment créer et utiliser un pipeline personnalisé.

---
## Étape 1 : Créer un Formatter

``` python
class OrderFormatter(BatchFormatter[RawOrder, StructuredOrders]):
    def _format(self, data: Iterrable[RawOrder]) -> StructuredOrders:
        return StructuredOrders.from_raw(data)
```

Rappel : aucun I/O, fonction pure RawT → FormattedT.

---
## Étape 2 : Créer un WriterCore

``` python
class OrdersWriterCore(BatchWriterCore[StructuredOrders, bytes]):
    def _encode(self, data: StructuredOrders) -> bytes:
        return json.dumps(data.to_dict()).encode()

    def _start(self): pass
    def _finalize(self): pass
    def _finalize_empty(self): pass
    def _cleanup_after_error(self): pass
```

Rappel : aucun I/O, uniquement de la sérialisation.

---
### Étape 3 : Créer un Sink

``` python
class JsonFileSink(BatchSink[bytes]):
    def _open(self):
        self._tmp = open(self.tmp_path, "wb")

    def _write(self, data):
        self._tmp.write(data)

    def _commit(self):
        os.rename(self.tmp_path, self.final_path)

    def _rollback(self):
        safe_delete(self.tmp_path)

    def _finalize_resources(self):
        self._tmp.close()

    def _cleanup_after_error(self):
        safe_delete(self.tmp_path)
```

Rappel : un seul commit autorisé, rollback obligatoire.

---
## Étape 4 : Déclarer le pipeline dans un Binding

```python
binding = BatchExportBinding[
    RawOrder,
    StructuredOrders,
    bytes
](
    formatter_cls=OrderFormatter,
    writer_core_cls=OrdersWriterCore,
    sink_cls=JsonFileSink,
)
```

---
## Étape 5 : Enregistrer le pipeline dans le Registry

``` python
BacktestExportRegistry.register(
    ExportKey.ORDERS,
    binding
)
```

Ou via décorateur :
```python
@BacktestExportRegistry.bind(ExportKey.ORDERS)
class OrdersExport:
    formatter_cls = OrderFormatter
    writer_core_cls = OrdersWriterCore
    sink_cls = JsonFileSink
```

---
## Étape 6 : Construire un service via la Factory

``` python
service = factory.create_backtest_batch_export_service(
    ExportKey.ORDERS
)
```

---
## Étape 7 : Exécuter l’export

```python
service.export(raw_orders)
```

Le moteur applique automatiquement :

- formatage,
- encodage,
- validation,
- persistence atomique,
- gestion des cycles de vie et erreurs.

