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

    df = drop_columns(df, columns)

    return df


def prepare(df: pandas.DataFrame) -> pandas.DataFrame:
    df = df[df["S%"] != '--']
    #df = df[df["P"] != 0]
    #df = df[df["GP"] > 4]

    df["EVA"] = df["EVP"] - df["EVG"]
    df["PPA"] = df["PPP"] - df["PPG"]

    df["Forward"] = df["Pos"].isin(['C', 'L', 'R']).astype(int)
    #df["Def"] = (df["Pos"] == 'D').astype(int)

    df = normalize_per_gp(df, ["EVA", "EVG", "PPA", "PPG", "S"])
    #df = normalize_per_gp(df, ["S"])
    df["S%"] = df["S%"].astype(float) / 100

    #df = drop_columns(df, ["Season", "#", "FOW%", "G", "A", "P", "Shoots",
    #                       "Pos", "EVP", "SHP", "PPP", "OTG", "GWG", "EVG",  "PPG",
    #                       "Team", "TOI/GP", "GP", "SHG",  "+/-", "PIM"])

    df = drop_columns(df, ["Season", "#", "FOW%", "G", "A", "P", "Shoots",
                           "Pos", "EVP", "SHP", "PPP", "P/GP", "OTG", "GWG",
                           "Team", "TOI/GP", "GP", "SHG",  "+/-", "PIM"])

    return df
