from investiq.api.enums import FIFOSide


class FIFOReader:

    def active_entries(self, side: FIFOSide) -> tuple[InventoryEntry, ...]:
        ...

    def available_quantity(self, side: FIFOSide) -> float:
        ...

    def require_capacity(self, side: FIFOSide, quantity: float) -> None:
        ...


class FIFOView:
    reader: FIFOReader