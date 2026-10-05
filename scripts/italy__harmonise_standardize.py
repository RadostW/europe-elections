import pandas as pd
import numpy as np

columns_standard = [
    "comune_clean",
    "comune_provincia_clean",
    "collegio_uninominale",
    "collegio_plurinominale",
    "circoscrizione",
    "comune",
    "provincia",
    "regione",
    "eligible_voters",
    "issued_ballots",
    "list_name",
    "votes",
]

columns_locality = [
    "comune_clean",
    "comune_provincia_clean",
    "collegio_uninominale",    
    "collegio_plurinominale",
    "circoscrizione",
    "comune",
    "provincia",
    "regione",
    "issued_ballots",
    "eligible_voters",
]

columns_neighbourhood = [
    "provincia",
    "circoscrizione",
    "regione",
    "collegio_plurinominale",
    "collegio_uninominale",
]


def standardize_columns(df, config):
    columns = df.columns

    for c in columns:
        is_target = False
        target_name = ""
        for key, targets in config["column_names"].items():
            if c in targets:
                is_target = True
                target_name = key
                df = df.rename(columns={c: target_name})

        print(
            f"{'+' if is_target else ' '} {c[:20].ljust(20) + ('...' if len(c) > 20 else '   ')} -> {target_name}"
        )

    df["comune_clean"] = df["comune"].normalize_string()

    if "provincia" in df.columns:
        df["comune_provincia_clean"] = (
            df["comune"].normalize_string()
            + " ( "
            + df["provincia"].normalize_string()
            + " )"
        )
    else:
        df["comune_provincia_clean"] = (
            df["comune"].normalize_string()            
        )

    for c in columns_neighbourhood:
        if c not in df.columns:
            df[c] = np.nan

    df = df[columns_standard]

    assert (
        len(set(df["list_name"]) - set(config["choices_names"].keys())) == 0
    )  # no missing keys

    df["list_name"] = df["list_name"].map(config["choices_names"])

    return df
