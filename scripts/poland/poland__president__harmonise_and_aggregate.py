import os
import pandas as pd
from glob import glob
import csv

# Define directory paths
intermediate_dir = os.path.join(
    os.path.dirname(__file__), "../../data/poland/intermediate_datasets"
)
base_dir = os.path.join(os.path.dirname(__file__), "../../data/poland/raw_datasets")


def detect_delimiter(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        first_line = f.readline()
    return ";" if first_line.count(";") > first_line.count(",") else ","


def validate_merge(df_left, df_right, key):
    keys_left, keys_right = set(df_left[key].unique()), set(df_right[key].unique())

    # Find missing keys
    missing_in_right = keys_left - keys_right
    missing_in_left = keys_right - keys_left

    if missing_in_right:
        print(f"Keys in df_left but missing in df_right: {missing_in_right}")
    if missing_in_left:
        print(f"Keys in df_right but missing in df_left: {missing_in_left}")

    # Check for duplicate keys
    duplicates_left = df_left[key].duplicated().any()
    duplicates_right = df_right[key].duplicated().any()

    if duplicates_left:
        print("Duplicate keys found in df_left.")
    if duplicates_right:
        print("Duplicate keys found in df_right.")

    return not (
        missing_in_right or missing_in_left or duplicates_left or duplicates_right
    )


def get_replacements(standard_name):
    if standard_name == "poland__president_2000_a":
        candidates_replacements = {
            "Dariusz Maciej GRABOWSKI": "Dariusz_Maciej_GRABOWSKI",
            "Piotr IKONOWICZ": "Piotr_IKONOWICZ",
            "Jarosław KALINOWSKI": "Jarosław_KALINOWSKI",
            "Janusz KORWIN-MIKKE": "Janusz_KORWIN_MIKKE",
            "Marian KRZAKLEWSKI": "Marian_KRZAKLEWSKI",
            "Aleksander KWAŚNIEWSKI": "Aleksander_KWAŚNIEWSKI",
            "Andrzej LEPPER": "Andrzej_LEPPER",
            "Jan ŁOPUSZAŃSKI": "Jan_ŁOPUSZAŃSKI",
            "Andrzej Marian OLECHOWSKI": "Andrzej_Marian_OLECHOWSKI",
            "Bogdan PAWŁOWSKI": "Bogdan_PAWŁOWSKI",
            "Lech WAŁĘSA": "Lech_WAŁĘSA",
            "Tadeusz Adam WILECKI": "Tadeusz_Adam_WILECKI",
        }
        other_replacements = {
            "Uprawnieni": "eligible_voters",
            "Karty wydane": "issued_ballots",
            "Głosy nieważne": "invalid_ballots",
        }
    elif standard_name == "poland__president_2005_a":
        candidates_replacements = {
            "Bochniarz Henryka Teodora": "Henryka_Teodora_BOCHNIARZ",
            "Borowski Marek Stefan": "Marek_Stefan_BOROWSKI",
            "Bubel Leszek Henryk": "Leszek_Henryk_BUBEL",
            "Ilasz Liwiusz Marian": "Liwiusz_Marian_ILASZ",
            "Kaczyński Lech Aleksander": "Lech_Aleksander_KACZYŃSKI",
            "Kalinowski Jarosław": "Jarosław_KALINOWSKI",
            "Korwin-Mikke Janusz Ryszard": "Janusz_Ryszard_KOWRIN-MIKKE",
            "Lepper Andrzej Zbigniew": "Andrzej_Zbigniew_LEPPER",
            "Pyszko Jan": "Jan_PYSZKO",
            "Słomka Adam Andrzej": "Adam_Andrzej_SŁOMKA",
            "Tusk Donald Franciszek": "Donald_Franciszek_TUSK",
            "Tymiński Stanisław": "Stanisław_TYMIŃSKI",
        }
        other_replacements = {
            "Uprawnieni do głosowania": "eligible_voters",
            "Karty wydane (frekwencja)": "issued_ballots",
            "Głosy nieważne": "invalid_ballots",
        }
    elif standard_name == "poland__president_2005_b":
        candidates_replacements = {
            "Lech Aleksander Kaczyński": "Lech_Aleksander_KACZYŃSKI",
            "Donald Franciszek Tusk": "Donald_Franciszek_TUSK",
        }
        other_replacements = {
            "Uprawnieni do głosowania": "eligible_voters",
            "Wydane karty do głosowania": "issued_ballots",
            "Głosy nieważne": "invalid_ballots",
        }
    elif standard_name == "poland__president_2010_a":
        candidates_replacements = {
            "JUREK Marek": "Marek_JUREK",
            "KACZYŃSKI Jarosław Aleksander": "Jarosław_Aleksander_KACZYŃSKI",
            "KOMOROWSKI Bronisław Maria": "Bronisław_Maria_KOMOROWSKI",
            "KORWIN-MIKKE Janusz Ryszard": "Janusz_Ryszard_KORWIN-MIKKE",
            "LEPPER Andrzej Zbigniew": "Andrzej_Zbigniew_LEPPER",
            "MORAWIECKI Kornel Andrzej": "Kornel_Andrzej_MORAWIECKI",
            "NAPIERALSKI Grzegorz Bernard": "Grzegorz_Bernard_NAPIERALSKI",
            "OLECHOWSKI Andrzej Marian": "Andrzej_Marian_OLECHOWSKI",
            "PAWLAK Waldemar": "Waldemar_PAWLAK",
            "ZIĘTEK Bogusław Zbigniew": "Bogusław_Zbigniew_ZIĘTEK",
        }
        other_replacements = {
            "Upr.": "eligible_voters",
            "Frekw.": "issued_ballots",
            "Głosy nieważne": "invalid_ballots",
        }
    elif standard_name == "poland__president_2010_b":
        candidates_replacements = {
            "KACZYŃSKI Jarosław Aleksander": "Jarosław_Aleksander_KACZYŃSKI",
            "KOMOROWSKI Bronisław Maria": "Bronisław_Maria_KOMOROWSKI",
        }
        other_replacements = {
            "Upr.": "eligible_voters",
            "Frekw.": "issued_ballots",
            "Głosy nieważne": "invalid_ballots",
        }
    elif standard_name == "poland__president_2015_a":
        candidates_replacements = {
            "Braun Grzegorz Michał": "Grzegorz_Michał_BRAUN",
            "Duda Andrzej Sebastian": "Andrzej_Sebastian_DUDA",
            "Jarubas Adam Sebastian": "Adam_Sebastian_JARUBAS",
            "Komorowski Bronisław Maria": "Bronisław_Maria_KOMOROWSKI",
            "Korwin-Mikke Janusz Ryszard": "Janusz_Ryszard_KORWIN-MIKKE",
            "Kowalski Marian Janusz": "Marian_Janusz_KOWALSKI",
            "Kukiz Paweł Piotr": "Paweł_Piotr_KUKIZ",
            "Ogórek Magdalena Agnieszka": "Magdalena_Agnieszka_OGÓREK",
            "Palikot Janusz Marian": "Janusz_Marian_PALIKOT",
            "Tanajno Paweł Jan": "Paweł_Jan_TANAJNO",
            "Wilk Jacek": "Jacek_WILK",
        }
        other_replacements = {
            "Liczba wyborców uprawnionych do głosowania": "eligible_voters",
            "Liczba wyborców, którym wydano karty do głosowania": "issued_ballots",
            "Liczba głosów nieważnych": "invalid_ballots",
        }
    elif standard_name == "poland__president_2015_b":
        candidates_replacements = {
            "Duda Andrzej Sebastian": "Andrzej_Sebastian_DUDA",
            "Komorowski Bronisław Maria": "Bronisław_Maria_KOMOROWSKI",
        }
        other_replacements = {
            "Liczba wyborców uprawnionych do głosowania": "eligible_voters",
            "Liczba wyborców, którym wydano karty do głosowania": "issued_ballots",
            "Liczba głosów nieważnych": "invalid_ballots",
        }
    elif standard_name == "poland__president_2020_a":
        candidates_replacements = {
            "Robert BIEDROŃ": "Robert_BIEDROŃ",
            "Krzysztof BOSAK": "Krzysztof_BOSAK",
            "Andrzej Sebastian DUDA": "Andrzej_Sebastian_DUDA",
            "Szymon Franciszek HOŁOWNIA": "Szymon_Franciszek_HOŁOWNIA",
            "Marek JAKUBIAK": "Marek_JAKUBIAK",
            "Władysław Marcin KOSINIAK-KAMYSZ": "Władysław_Marcin_KOSINIAK-KAMYSZ",
            "Mirosław Mariusz PIOTROWSKI": "Mirosław_Mariusz_PIOTROWSKI",
            "Paweł Jan TANAJNO": "Paweł_Jan_TANAJNO",
            "Rafał Kazimierz TRZASKOWSKI": "Rafał_Kazimierz_TRZASKOWSKI",
            "Waldemar Włodzimierz WITKOWSKI": "Waldemar_Włodzimierz_WITKOWSKI",
            "Stanisław Józef ŻÓŁTEK": "Stanisław_Józef_ŻÓŁTEK",
        }
        other_replacements = {
            "Liczba wyborców uprawnionych do głosowania": "eligible_voters",
            "Liczba wyborców, którym wydano karty do głosowania": "issued_ballots",
            "Liczba głosów nieważnych": "invalid_ballots",
        }
    elif standard_name == "poland__president_2020_b":
        candidates_replacements = {
            "Andrzej Sebastian DUDA": "Andrzej_Sebastian_DUDA",
            "Rafał Kazimierz TRZASKOWSKI": "Rafał_Kazimierz_TRZASKOWSKI",
        }
        other_replacements = {
            "Liczba wyborców uprawnionych do głosowania": "eligible_voters",
            "Liczba wyborców, którym wydano karty do głosowania": "issued_ballots",
            "Liczba głosów nieważnych": "invalid_ballots",
        }
    else:
        raise NotImplementedError("Unknown file")

    return candidates_replacements, other_replacements


# Function to process and clean election data
def process_election_data(file_path, regions_df, output_path, standard_name):
    delimiter = detect_delimiter(file_path)
    election_df = pd.read_csv(file_path, delimiter=delimiter)

    if standard_name == "poland__president_2000_a":
        election_df["teryt_code"] = "T_" + election_df["TERYT"].astype(str).str.zfill(4)
        renamed_powiats = {
            "T_1431": "T_1465",  # warszawski -> m. Warszawa
            "T_0263": "T_0265",  # Wałbrzych -> Wałbrzych
        }
        election_df["teryt_code"].replace(renamed_powiats, inplace=True)
    elif standard_name == "poland__president_2005_a":
        election_df["teryt_code"] = "T_" + election_df["TERYT"].astype(str).str[
            :-2
        ].str.zfill(4)
    elif standard_name == "poland__president_2005_b":
        election_df["teryt_code"] = "T_" + election_df["TERYT"].astype(str).str[
            :-2
        ].str.zfill(4)
    elif standard_name == "poland__president_2010_a":
        election_df["teryt_code"] = "T_" + election_df["TERYT"].astype(str).str[
            :-2
        ].str.zfill(4)
        election_df["Głosy nieważne"] = (
            election_df["Gł. odd."] - election_df["Gł. ważne"]
        )
    elif standard_name == "poland__president_2010_b":
        election_df["teryt_code"] = "T_" + election_df["TERYT"].astype(str).str[
            :-2
        ].str.zfill(4)
        election_df["Głosy nieważne"] = (
            election_df["Gł. odd."] - election_df["Gł. ważne"]
        )
    elif standard_name == "poland__president_2015_a":
        election_df["teryt_code"] = "T_" + election_df["TERYT"].astype(str).str.zfill(4)
    elif standard_name == "poland__president_2015_b":
        election_df["teryt_code"] = "T_" + election_df["TERYT"].astype(str).str.zfill(4)
    elif standard_name == "poland__president_2020_a":
        election_df["teryt_code"] = "T_" + election_df["Kod TERYT"].astype(str).str[
            :-2
        ].str.zfill(4)
    elif standard_name == "poland__president_2020_b":
        election_df["teryt_code"] = "T_" + election_df["Kod TERYT"].astype(str).str[
            :-2
        ].str.zfill(4)
    else:
        raise NotImplementedError

    candidates_replacements, other_replacements = get_replacements(standard_name)

    # Validate and merge with regions dataframe
    validate_merge(election_df, regions_df, "teryt_code")
    export_df = election_df.merge(regions_df, how="outer", on="teryt_code")

    # Rename columns and fill missing values
    export_df.rename(columns=candidates_replacements, inplace=True)
    export_df.rename(columns=other_replacements, inplace=True)
    export_df.fillna(-1, inplace=True)

    # Define the order of columns and export the cleaned data
    prefix_columns = [
        "nuts_3_code",
        "nuts_3_name",
        "powiat_name",
        "powiat_name_extra",
        "teryt_code",
        "eligible_voters",
        "issued_ballots",
        "invalid_ballots",
    ]
    suffix_columns = [
        "voivodship_name",
        "voivodship_name_extra",
        "level_5_name",
        "level_4_name",
        "level_3_name",
        "level_2_name",
        "level_1_name",
    ]
    columns_to_export = (
        prefix_columns + sorted(list(candidates_replacements.values())) + suffix_columns
    )
    export_df = export_df[columns_to_export]

    export_df.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)


# Main code execution
file_pattern = os.path.join(base_dir, "poland__president*.csv")
csv_files = glob(file_pattern)

regions_file = os.path.join(base_dir, "../intermediate_datasets/poland__region_id.csv")
regions_df = pd.read_csv(regions_file)

if not csv_files:
    raise ValueError("No files found")

for file_path in sorted(csv_files):
    print(f"Loading file: {os.path.basename(file_path)}")
    try:
        standard_name = os.path.basename(file_path)[: len("poland__president_2000_a")]
        output_path = os.path.join(intermediate_dir, f"{standard_name}.csv")

        process_election_data(file_path, regions_df, output_path, standard_name)

    except Exception as e:
        print(f"Failed processing {os.path.basename(file_path)}: {e}")
        raise e
