import pandas
from typing import Sequence


def drop_columns(df: pandas.DataFrame, columns: Sequence[str]) -> pandas.DataFrame:
    for col in columns:
        df = df.drop(col, axis=1)

    return df


def normalize_per_gp(df: pandas.DataFrame, columns: Sequence[str]) -> pandas.DataFrame:
    games_played: int = df["GP"].astype(float)

    for col in columns:
        df[f"{col}/GP"] = df[col].astype(float) / games_played
        df[f"{col}/GP/max"] = df[f"{col}/GP"] / df[f"{col}/GP"].max()
        df.drop(f"{col}/GP", axis=1)

    df = drop_columns(df, columns)

    return df


def extract_features(df: pandas.DataFrame) -> pandas.DataFrame:
    df = df[df["S%"] != '--']
    df = df[df["GP"] > 8]
    df = df[df["P"] > 0]

    df["TOI/GP"] = df["TOI/GP"].apply(lambda x: int(x.split(':')[0])*60+int(x.split(':')[1])) / 3600
    df["EVA"] = df["EVP"] - df["EVG"]
    df["PPA"] = df["PPP"] - df["PPG"]

    df["Forward"] = df["Pos"].isin(['C', 'L', 'R']).astype(int)

    df = normalize_per_gp(df, ["EVA", "EVG", "PPA", "PPG", "S"])
    df["S%"] = df["S%"].astype(float) / 100

    df = drop_columns(df, ["Season", "#", "FOW%", "G", "A", "P", "Shoots",
                           "Pos", "EVP", "SHP", "PPP", "P/GP", "OTG", "GWG",
                           "Team", "TOI/GP", "GP", "SHG",  "+/-", "PIM"])

    return df
