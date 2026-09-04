import pathlib
import pandas as pd
import unidecode

here = pathlib.Path(__file__).resolve().parent

raw_data_dir = (here / "../data/hungary/raw_datasets/").resolve()
european_paths = {
    2024: raw_data_dir / "EP_2024.xls",
    2019: raw_data_dir / "EP_2019.xls",
    2014: raw_data_dir / "EP_2014.csv",
    2009: (raw_data_dir / "EP_2009.txt", raw_data_dir / "EP_2009_meta.txt"),
}
european_election_dates = {
    2024: "2024-06-09",
    2019: "2019-05-26",
    2014: "2014-05-25",
    2009: "2009-06-07",
}


parliament_paths = {
    2026: raw_data_dir / "parliament_2026/",
    2022: raw_data_dir / "parliament_2022.csv",
    2018: raw_data_dir / "parliament_2018.csv",
    2014: raw_data_dir / "parliament_2014.csv",
    2010: (
        raw_data_dir / "parliament_2010__lis_szkt.txt",
        raw_data_dir / "parliament_2010__lis_szkf.txt",
    ),
    2006: (
        raw_data_dir / "parliament_2006__lis_szkt.txt",
        raw_data_dir / "parliament_2006__lis_szkf.txt",
    ),
    2002: (
        raw_data_dir / "parliament_2002__lis_szkt.txt",
        raw_data_dir / "parliament_2002__lis_szkf.txt",
    ),
}
parliament_election_dates = {
    2026: "2026-04-12",
    2022: "2022-04-03",
    2018: "2018-04-08",
    2014: "2014-04-06",
    2010: "2010-04-11",
    2006: "2006-04-09",
    2002: "2002-04-07",
}


european_records = []

for year, path in european_paths.items():
    if year == 2024:
        raw_data = pd.read_excel(path, None)
        column_names = {
            "Település neve": "harmonised_name",
            "A": "eligible_voters",
            "K": "issued_ballots",
            "1": "MEMO",
            "2": "LMP – Zöldek",
            "3": "DK-MSZP-Párbeszéd- ZÖLDEK",
            "4": "2RK Párt",
            "5": "MMN",
            "6": "Momentum",
            "7": "FIDESZ-KDNP",
            "8": "Jobbik",
            "9": "TISZA",
            "10": "MKKP",
            "11": "Mi Hazánk",
        }
        sheet_names = [x for x in raw_data.keys() if x != "Paraméterek"]
        year_records = []
        for sn in sheet_names:
            df = raw_data[sn].iloc[:-1]  # drop 'sum' row
            df = df.rename(columns=column_names)[column_names.values()]

            df_long = df.melt(
                id_vars="harmonised_name", var_name="name", value_name="votes"
            )

            df_long["type"] = (
                df_long["name"]
                .map({"eligible_voters": 0, "issued_ballots": 1})
                .fillna(2)
                .astype(int)
            )

            # ,election_date,election_type,harmonised_name,type,name,votes
            df_long["election_date"] = european_election_dates[year]
            df_long["election_type"] = "european"

            df_long = df_long[
                [
                    "election_date",
                    "election_type",
                    "harmonised_name",
                    "type",
                    "name",
                    "votes",
                ]
            ]
            df_long = df_long.sort_values(by=list(df_long.columns))
            year_records.append(df_long)

        df_year = pd.concat(year_records)
        european_records.append(df_year)
    elif year == 2019:
        raw_data = pd.read_excel(path, None, skiprows=4)
        column_names = {
            "Település": "harmonised_name",
            "A": "eligible_voters",
            "K": "issued_ballots",
            "01": "MSZP-PÁRBESZÉD",
            "02": "MKKP",
            "03": "JOBBIK",
            "04": "FIDESZ",
            "05": "MOMENTUM",
            "06": "DK",
            "07": "MI HAZÁNK",
            "08": "MUNKÁSPÁRT",
            "09": "LMP",
        }
        sheet_names = [x for x in raw_data.keys() if x != "Paraméterek"]
        year_records = []
        for sn in sheet_names:
            df = raw_data[sn].iloc[:-1]  # drop 'sum' row
            df = df.rename(columns=column_names)[column_names.values()]

            df_long = df.melt(
                id_vars="harmonised_name", var_name="name", value_name="votes"
            )

            df_long["type"] = (
                df_long["name"]
                .map({"eligible_voters": 0, "issued_ballots": 1})
                .fillna(2)
                .astype(int)
            )

            # ,election_date,election_type,harmonised_name,type,name,votes
            df_long["election_date"] = european_election_dates[year]
            df_long["election_type"] = "european"

            df_long = df_long[
                [
                    "election_date",
                    "election_type",
                    "harmonised_name",
                    "type",
                    "name",
                    "votes",
                ]
            ]
            df_long = df_long.sort_values(by=list(df_long.columns))
            year_records.append(df_long)

        df_year = pd.concat(year_records)
        european_records.append(df_year)

    elif year == 2014:
        raw_data = pd.read_csv(path)
        df_eligible = raw_data[raw_data["VÁLASZTÓPOLGÁR"] > 0].copy()
        df_eligible["votes"] = df_eligible["VÁLASZTÓPOLGÁR"]
        df_eligible["harmonised_name"] = df_eligible["TELEPÜLÉS"]
        df_eligible["name"] = "eligible_voters"

        df_issued = raw_data[raw_data["VÁLASZTÓPOLGÁR"] > 0].copy()
        df_issued["votes"] = df_issued["MEGJELENTEK"]
        df_issued["harmonised_name"] = df_issued["TELEPÜLÉS"]
        df_issued["name"] = "issued_ballots"

        df_list_votes = raw_data.copy()
        df_list_votes = (df_list_votes.ffill())[raw_data["VÁLASZTÓPOLGÁR"].isna()]
        df_list_votes["harmonised_name"] = df_list_votes["TELEPÜLÉS"]
        df_list_votes["name"] = df_list_votes["LISTA"]
        df_list_votes["votes"] = df_list_votes["SZAVAZAT"]

        selected_columns = ["harmonised_name", "name", "votes"]
        df_year = (
            pd.concat(
                [
                    df_eligible[selected_columns],
                    df_issued[selected_columns],
                    df_list_votes[selected_columns],
                ]
            )
            .groupby(["harmonised_name", "name"])
            .agg("sum")
            .reset_index()
        )

        df_year["type"] = (
            df_year["name"]
            .map({"eligible_voters": 0, "issued_ballots": 1})
            .fillna(2)
            .astype(int)
        )
        df_year["election_date"] = european_election_dates[year]
        df_year["election_type"] = "european"
        df_year = df_year[
            [
                "election_date",
                "election_type",
                "harmonised_name",
                "type",
                "name",
                "votes",
            ]
        ]
        df_year = df_year.sort_values(by=list(df_year.columns))
        european_records.append(df_year)

    elif year == 2009:
        path_data, path_meta = path
        raw_data = pd.read_csv(
            path_data,
            sep="|",
            encoding="cp1250",
        )
        raw_data.columns = [x.replace(" ", "") for x in raw_data.columns]
        raw_data = raw_data.map(lambda x: x.strip() if isinstance(x, str) else x)
        raw_data = raw_data[raw_data["name"] != "KÜLKÉPVISELETEK"]  # drop sum

        raw_meta = pd.read_csv(
            path_meta,
            sep="|",
            encoding="cp1250",
        )
        raw_meta.columns = [x.replace(" ", "") for x in raw_meta.columns]
        raw_meta = raw_meta[raw_meta["name"] != "KÜLKÉPVISELETEK"]  # drop sum
        raw_meta = raw_meta.map(lambda x: x.strip() if isinstance(x, str) else x)
        raw_meta["ev"] = "eligible_voters"
        raw_meta["ib"] = "issued_ballots"

        df_year = pd.concat(
            [
                raw_data[["tname", "pname", "votes"]],
                raw_meta[["tname", "ev", "registe"]].rename(
                    columns={"registe": "votes", "ev": "pname"}
                ),
                raw_meta[["tname", "ib", "issued"]].rename(
                    columns={"issued": "votes", "ib": "pname"}
                ),
            ]
        ).rename(columns={"pname": "name", "tname": "harmonised_name"})

        df_year["type"] = (
            df_year["name"]
            .map({"eligible_voters": 0, "issued_ballots": 1})
            .fillna(2)
            .astype(int)
        )
        df_year["election_date"] = european_election_dates[year]
        df_year["election_type"] = "european"
        df_year = df_year[
            [
                "election_date",
                "election_type",
                "harmonised_name",
                "type",
                "name",
                "votes",
            ]
        ]
        df_year = df_year.sort_values(by=list(df_year.columns))
        european_records.append(df_year)

    else:
        raise NotImplementedError

df_euro = pd.concat(european_records)

parliament_records = []

for year, path in parliament_paths.items():
    if year == 2026:

        DATA_DIR = path

        VOTE_COLUMNS = ["01", "02", "03", "04", "05"]
        KEEP_COLUMNS = [
            "Település",
            "Szavazókör azonosító",
            "AL",
            *VOTE_COLUMNS,
        ]

        dfs = []

        for file in sorted(DATA_DIR.glob("*.xls")):
            # print(f"Loading {file.name}")

            # First row contains the county name
            county = pd.read_excel(
                file,
                sheet_name=1,
                header=None,
                nrows=1,
                engine="xlrd",
            ).iloc[0, 0]

            # Actual table starts on the second row
            df = pd.read_excel(
                file,
                sheet_name=1,
                header=1,
                engine="xlrd",
            )

            # Keep only the columns of interest
            df = df[KEEP_COLUMNS].copy()

            # Add county column
            df.insert(0, "Vármegye", county)

            dfs.append(df)

        # Combine all counties
        election_df = pd.concat(dfs, ignore_index=True)

        election_df = election_df.rename(
            columns={
                "AL": "Registered_Voters",
                "01": "Party_01",
                "02": "Party_02",
                "03": "Party_03",
                "04": "Party_04",
                "05": "Party_05",
            }
        )

        election_df = election_df.rename(
            columns={
                "Vármegye": "county",
                "Település": "municipality",
                "Szavazókör azonosító": "polling_station",
                "Registered_Voters": "eligible_voters",
                "Party_01": "mkkp",
                "Party_02": "tisza",
                "Party_03": "mi_hazank",
                "Party_04": "dk",
                "Party_05": "fidesz",
            }
        )

        election_df["county"] = (
            election_df["county"]
            .str.replace(r"\s+vármegye$", "", regex=True)
            .str.replace(r"\s+főváros$", "", regex=True)
            .str.title()
        )

        mask = election_df["municipality"].str.contains("Budapest ")
        election_df.loc[mask, "municipality"] = "Budapest"

        election_df["issued_ballots"] = election_df[
            ["mkkp", "tisza", "mi_hazank", "dk", "fidesz"]
        ].sum(axis=1)

        election_df = (
            election_df.groupby(["municipality", "county"])[
                [
                    "issued_ballots",
                    "eligible_voters",
                    "mkkp",
                    "tisza",
                    "mi_hazank",
                    "dk",
                    "fidesz",
                ]
            ]
            .sum()
            .reset_index()
        )

        df_year = election_df.melt(
            id_vars=["municipality", "county"], var_name="name", value_name="votes"
        )

        df_year["type"] = (
            df_year["name"]
            .map({"eligible_voters": 0, "issued_ballots": 1})
            .fillna(2)
            .astype(int)
        )
        df_year["election_date"] = parliament_election_dates[year]
        df_year["election_type"] = "parliament"
        df_year["harmonised_name"] = df_year["municipality"]

        df_year = df_year[
            [
                "election_date",
                "election_type",
                "harmonised_name",
                "type",
                "name",
                "votes",
            ]
        ]
        df_year = df_year.sort_values(by=list(df_year.columns))
        df_year = (
            df_year.groupby(
                ["election_date", "election_type", "harmonised_name", "type", "name"]
            )
            .agg("sum")
            .reset_index()
        )
        parliament_records.append(df_year)

    elif year in [2022, 2018, 2014]:

        raw_data = pd.read_csv(path)

        meta_rows = raw_data[raw_data["'LISTÁS'"] == "Listás"].copy()
        meta_rows["ev"] = "eligible_voters"
        meta_rows["ib"] = "issued_ballots"
        vote_rows = raw_data.ffill()[raw_data["'LISTÁS'"] != "Listás"].copy()

        df_year = pd.concat(
            [
                vote_rows[["TELEPÜLÉS", "LISTA", "SZAVAZAT"]].rename(
                    columns={
                        "TELEPÜLÉS": "harmonised_name",
                        "LISTA": "name",
                        "SZAVAZAT": "votes",
                    }
                ),
                meta_rows[["TELEPÜLÉS", "ev", "VÁLASZTÓPOLGÁR"]].rename(
                    columns={
                        "TELEPÜLÉS": "harmonised_name",
                        "ev": "name",
                        "VÁLASZTÓPOLGÁR": "votes",
                    }
                ),
                meta_rows[["TELEPÜLÉS", "ib", "URNÁBAN_LEVŐ"]].rename(
                    columns={
                        "TELEPÜLÉS": "harmonised_name",
                        "ib": "name",
                        "URNÁBAN_LEVŐ": "votes",
                    }
                ),
            ]
        )

        df_year["type"] = (
            df_year["name"]
            .map({"eligible_voters": 0, "issued_ballots": 1})
            .fillna(2)
            .astype(int)
        )
        df_year["election_date"] = parliament_election_dates[year]
        df_year["election_type"] = "parliament"
        df_year = df_year[
            [
                "election_date",
                "election_type",
                "harmonised_name",
                "type",
                "name",
                "votes",
            ]
        ]
        df_year = df_year.sort_values(by=list(df_year.columns))
        df_year = (
            df_year.groupby(
                ["election_date", "election_type", "harmonised_name", "type", "name"]
            )
            .agg("sum")
            .reset_index()
        )
        parliament_records.append(df_year)
    elif year in [2010, 2006, 2002]:
        path_data, path_meta = path
        raw_data = pd.read_csv(
            path_data,
            sep="|",
            encoding="cp1250",
        )
        raw_data.columns = [x.replace(" ", "") for x in raw_data.columns]
        raw_data = raw_data.map(lambda x: x.strip() if isinstance(x, str) else x)

        raw_meta = pd.read_csv(
            path_meta,
            sep="|",
            encoding="cp1250",
        )
        raw_meta.columns = [x.replace(" ", "") for x in raw_meta.columns]
        raw_meta = raw_meta.map(lambda x: x.strip() if isinstance(x, str) else x)
        raw_meta["ev"] = "eligible_voters"
        raw_meta["ib"] = "issued_ballots"
        vote_rows = pd.merge(
            left=raw_data,
            right=raw_meta[["ci", "tid", "sid", "telepules_name"]],
            left_on=["ci", "tid", "sid"],
            right_on=["ci", "tid", "sid"],
            how="left",
        )

        df_year = pd.concat(
            [
                vote_rows[["telepules_name", "list_name", "votes"]].rename(
                    columns={
                        "telepules_name": "harmonised_name",
                        "list_name": "name",
                    }
                ),
                raw_meta[["telepules_name", "ev", "eligibl"]].rename(
                    columns={
                        "telepules_name": "harmonised_name",
                        "ev": "name",
                        "eligibl": "votes",
                    }
                ),
                raw_meta[["telepules_name", "ib", "issued"]].rename(
                    columns={
                        "telepules_name": "harmonised_name",
                        "ib": "name",
                        "issued": "votes",
                    }
                ),
            ]
        )
        df_year["type"] = (
            df_year["name"]
            .map({"eligible_voters": 0, "issued_ballots": 1})
            .fillna(2)
            .astype(int)
        )
        df_year["election_date"] = parliament_election_dates[year]
        df_year["election_type"] = "parliament"
        df_year = df_year[
            [
                "election_date",
                "election_type",
                "harmonised_name",
                "type",
                "name",
                "votes",
            ]
        ]
        df_year = df_year.sort_values(by=list(df_year.columns))
        df_year = (
            df_year.groupby(
                ["election_date", "election_type", "harmonised_name", "type", "name"]
            )
            .agg("sum")
            .reset_index()
        )
        parliament_records.append(df_year)
    else:
        raise NotImplementedError

df_parliament = pd.concat(parliament_records)

df_hungary = pd.concat([df_parliament, df_euro])
df_hungary = df_hungary.sort_values(by=list(df_hungary.columns))

# deal with Budapest districts
df_hungary["harmonised_name"] = df_hungary["harmonised_name"].map(
    lambda x: "budapest" if "budapest" in x.lower() else x
)
df_hungary = (
    df_hungary.groupby(
        ["election_date", "election_type", "harmonised_name", "type", "name"]
    )
    .agg("sum")
    .reset_index()
)

# drop non-telepules rows
df_hungary = df_hungary[df_hungary["harmonised_name"] != "OVI székhelye"]

df_hungary["merge_name"] = (
    df_hungary["harmonised_name"]
    .str.lower()
    .replace({"kömlő": "koemlo"})
    .replace({"kömörő": "keomörő"})
    .map(lambda x: unidecode.unidecode(x))
)

merge_to_canonical = (
    df_hungary.loc[
        (df_hungary["election_date"] == "2026-04-12") & (df_hungary["type"] == 0),
        ["merge_name", "harmonised_name"],
    ]
    .set_index("merge_name")["harmonised_name"]
    .to_dict()
)
df_hungary["harmonised_name"] = df_hungary["merge_name"].map(merge_to_canonical)


q = df_hungary[df_hungary["type"] == 0]
w = q.merge_name.value_counts()
