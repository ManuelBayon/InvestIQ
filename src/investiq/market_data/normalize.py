import pandas as pd

def normalize_timestamp_column(df: pd.DataFrame, *, canonical: str = "timestamp") -> pd.DataFrame:
    """
    Rename any timestamp-like column to the canonical name.
    Raise an error if none or multiple are found.
    """

    # Possible timestamp column names
    aliases = ["timestamp", "Timestamp", "date", "Date", "datetime", "Datetime"]

    # Columns that match the aliases
    present = [c for c in aliases if c in df.columns]

    # Already normalized
    if canonical in df.columns:
        return df

    # No timestamp column
    if len(present) == 0:
        raise KeyError("No timestamp column found.")

    # More than one candidate column
    if len(present) > 1:
        raise ValueError(f"Multiple timestamp columns found: {present}")

    # Rename the detected column to the canonical name
    return df.rename(columns={present[0]: canonical})

def standardize_timestamp_utc(
    df: pd.DataFrame,
    col: str = "timestamp",
    tz_col: str = "timezone"
) -> pd.DataFrame:
    """
    Convert timestamp column to UTC-naive and store original timezone
    in an adjacent column.
    """

    if col not in df.columns:
        raise KeyError(f"{col} not found")

    s = pd.to_datetime(df[col], errors="raise")

    # Extract original timezone (if present)
    if hasattr(s.dt, "tz") and s.dt.tz is not None:
        df[tz_col] = str(s.dt.tz)
        s = s.dt.tz_convert("UTC")
    else:
        df[tz_col] = "naive"

    # Drop timezone info (UTC-naive canonical form)
    df[col] = s.dt.tz_localize(None)

    return df

def validate_ohlc(df: pd.DataFrame) -> None:
    """
    Validate basic OHLC invariants and timestamp ordering.
    """

    # Check timestamp monotonicity if present
    if "timestamp" in df.columns:
        ts = df["timestamp"]
        if not ts.is_monotonic_increasing:
            raise ValueError("Non-monotonic timestamps")

    cols = set(df.columns)
    required_cols = {"open", "high", "low", "close", "volume"}

    # Run OHLC checks only if all required columns exist
    if required_cols.issubset(cols):

        # Extract price series
        o: pd.Series = df["open"]
        h: pd.Series = df["high"]
        l: pd.Series = df["low"]
        c: pd.Series = df["close"]
        v: pd.Series = df["volume"]

        # OHLC consistency masks
        m1 = l.le(o)
        m2 = l.le(c)
        m3 = l.le(h)

        m11 = h.ge(o)
        m12 = h.ge(c)

        # Volume must be non-negative
        mv = v.ge(0)

        # Rows violating any invariant
        bad: pd.Series = ~(m1 & m2 & m3 & m11 & m12 & mv)

        if bad.any():
            idx = bad.idxmax()
            raise ValueError(f"Invalid OHLCV at row={idx}")