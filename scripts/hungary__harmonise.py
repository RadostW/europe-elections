import pathlib
import pandas as pd

here = pathlib.Path(__file__).resolve().parent

raw_data_dir = (here / "../data/hungary/raw_datasets/").resolve()
european_paths = {
    2024: raw_data_dir / "EP_2024.xls",
    2019: raw_data_dir / "EP_2019.xls",
    2014: raw_data_dir / "EP_2014.csv",
    2009: raw_data_dir / "EP_2009.txt",
}
election_dates = {
    2024: "2024-06-09",
    2019: "2019-05-26",
    2014: "2014-05-25",
    2009: "2009-06-07",
}

records = []

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
            df_long["election_date"] = election_dates[year]
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
        records.append(df_year)

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
            df_long["election_date"] = election_dates[year]
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
        records.append(df_year)

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
        df_year["election_date"] = election_dates[year]
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

    else:
        raise NotImplementedError
