#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

doc_dir = Path(__file__).parent.parent
table_dir = Path(__file__).parent

MULTILINE_DELIMITER = ";"
tables = {
    "Supported functions": {
        "target": doc_dir / "documentation_data_format.rst",
        "options": {
            "header-rows": "1",
            # "widths": "20 10 10 5",
        },
    },
}


def df_to_list_table(df, options, name):
    columns = df.columns
    table = f".. list-table:: {name}\n"
    for option_id, option_value in options.items():
        table += f"   :{option_id}: {option_value}\n"
    table += "\n"

    first = True
    for column in columns:
        if first:
            table += "   * "
            first = False
        else:
            table += "     "
        table += f"- | {column}\n"

    for _, row in df.iterrows():
        first = True
        for column in columns:
            cell = row[column]
            if first:
                table += "   * "
                first = False
            else:
                table += "     "
            table += "- "
            if MULTILINE_DELIMITER in cell:
                first_line = True
                for line in cell.split(MULTILINE_DELIMITER):
                    if first_line:
                        table += "| "
                        first_line = False
                    else:
                        table += "       | "
                    table += line
                    table += "\n"
            else:
                table += cell
                table += "\n"

    return table


def replace_text(filename, text, start, end):
    with open(filename, "r") as f:
        full_text0 = f.read()
    before_start = full_text0.split(start)[0]
    after_end = full_text0.split(end)[1]
    full_text = (
        before_start
        + start
        + text
        + end
        + after_end
    )
    with open(filename, "w") as f:
        f.write(full_text)


DISCLAIMER = "(GENERATED, DO NOT EDIT, INSTEAD EDIT IN PEtab/doc/src)"


for table_id, table_data in tables.items():
    target_file = table_data["target"]
    options = table_data["options"]
    df = pd.read_csv(table_dir/ f"{table_id}.tsv", sep="\t")
    table = df_to_list_table(df, options=options, name=table_id)
    replace_text(
        filename=target_file,
        text=table,
        start=f"\n..\n   START TABLE {table_id} {DISCLAIMER}\n",
        end=f"\n..\n   END TABLE {table_id}\n",
    )
