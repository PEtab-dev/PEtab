import pandas as pd


MULTILINE_DELIMITER = ";"
tables = {
    "functions": "../documentation_data_format.rst",
}


def df_to_list_table(df):
    columns = df.columns
    table = ".. list-table::\n\n"

    first = True
    for column in columns:
        if first:
            table += " * "
            first = False
        else:
            table += "   "
        table += f"- | **{column}**\n"

    for _, row in df.iterrows():
        first = True
        for column in columns:
            cell = row[column]
            if first:
                table += " * "
                first = False
            else:
                table += "   "
            table += "- "
            if MULTILINE_DELIMITER in cell:
                first_line = True
                for line in cell.split(MULTILINE_DELIMITER):
                    if first_line:
                        table += "| "
                        first_line = False
                    else:
                        table += "     | "
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


for table_id, target_file in tables.items():
    df = pd.read_csv(table_id+".tsv", sep="\t")
    table = df_to_list_table(df)
    replace_text(
        filename=target_file,
        text=table,
        start=f"\n..\n   START TABLE {table_id}\n",
        end=f"\n..\n   END TABLE {table_id}\n",
    )
