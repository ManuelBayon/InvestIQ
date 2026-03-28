import pandas as pd


def round_price_columns(df: pd.DataFrame, price_columns: list[str]) -> pd.DataFrame:
    for col in price_columns:
        if col in df.columns:
            df[col] = df[col].astype(float).round(2)
    return df