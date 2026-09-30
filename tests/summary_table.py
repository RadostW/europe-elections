import pathlib
import re
import pandas as pd

here = pathlib.Path(__file__).resolve().parent

with open(here / "test.log", "r", encoding="utf-8") as in_file:
    lines = in_file.readlines()
    test_lines = [
        line
        for line in lines
        if line.startswith("tests/test_election_winner.py::test_election")
    ]

records = []

# tests/test_election_winner.py::test_election_soft[HU_2024_eur] PASSED    [ 47%]
# tests/test_election_winner.py::test_election_hard[PL_2020_prb] PASSED    [ 87%]
for l in test_lines:
    m = re.match(r"tests/test_election_winner\.py::(.*)\[(.*)\] ([A-Z]*)", l)
    test_name = m[1]
    parameters_name = m[2]
    test_result = m[3]

    records.append(
        {
            "test_name": test_name,
            "parameters_name": parameters_name,
            "test_result": test_result,
        }
    )

df = pd.DataFrame.from_records(records)
df["test_result"] = df["test_result"].map(
    {
        "PASSED": "",
        "FAILED": "x",
    }
)
df_wide = pd.merge(
    df[df["test_name"] == "test_election_soft"],
    df[df["test_name"] == "test_election_hard"],
    on="parameters_name",
)
df_red = df_wide[["parameters_name", "test_result_x", "test_result_y"]].sort_values(by=["test_result_x","test_result_y"])
df_red.to_csv(here / "summary_table.csv")