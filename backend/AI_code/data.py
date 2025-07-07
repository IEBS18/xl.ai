import pandas as pd
import json
import openpyxl
import re


def json_to_dataframe(j_data):
    
    # cell_data = {}
    
    # for cell, value in j_data.items():
    #     col = cell[0]
    #     row = cell[1:]
    #     val = value.get('value', '')
    #     cell_data.setdefault(row, {})[col] = val
        
    # # print(cell_data)
        
    # result = pd.DataFrame.from_dict(cell_data, orient='index')
    # header = result.loc["1"].tolist()
    # df = result.drop(index="1")
    # # 4) Assign the real column names
    # df.columns = header
    
    # # 5) Convert the remaining index labels to int, sort, reset
    # df.index = df.index.astype(int)
    # df = df.sort_index().reset_index(drop=True)
    # df= df.loc[:, ~df.columns.str.contains(r"Starting|Unnamed|Periods", regex=True)]
    # # df = df.loc[:, ~df.columns.str.contains(r"^Starting")]
    
    # return df
    if isinstance(j_data, str):
        with open(j_data, "r",encoding="utf-8") as f:
            json_data = json.load(f)
    else:
        json_data = j_data

    cell_data = json_data["spreadsheet"]["data"]["data"]
    if not cell_data:
        raise ValueError("No 'data' key or it's empty in the JSON input.")

    parsed_data = []
    for cell, info in cell_data.items():
        match = re.match(r"([A-Z]+)(\d+)", cell)
        if not match:
            continue
        col_letters, row_number = match.groups()
        col_index = sum([(ord(char) - 64) * (26 ** i) for i, char in enumerate(reversed(col_letters))]) - 1
        row_index = int(row_number) - 1
        value = info.get("value", "")
        parsed_data.append((row_index, col_index, value))

    if not parsed_data:
        raise ValueError("Parsed cell data is empty. Possibly invalid format.")

    # Build a nested dict with row numbers
    df_dict = {}
    for row, col, value in parsed_data:
        df_dict.setdefault(row, {})[col] = value

    df = pd.DataFrame.from_dict(df_dict, orient="index").sort_index().fillna("")

    if df.empty or df.shape[0] < 2:
        raise ValueError("DataFrame is empty or doesn't have enough rows to extract header.")

    # Assign header from first row
    df.columns = df.iloc[0]
    df = df.drop(index=0).reset_index(drop=True)
    print("DataFrame after header assignment:\n", df.head())
    # data=df.to_excel("output.excel", index=False)
    return df
    
    
def main():
    """
    Entry point for converting a spreadsheet-style JSON to a DataFrame.
    Modify the file path as needed.
    """
    input_file = r"C:\Users\nirmiti.deshmukh\xl.ai\backend\AI_code\spreadsheet.json" # 🔁 Change this to your actual path

    try:
        df = json_to_dataframe(input_file)
        print("[INFO] DataFrame successfully created:")
        print(df.head())
        
        # Optional: Export to CSV
        df.to_csv("output.csv", index=False)
    except Exception as e:
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    main()


        
        
        
        
        
        
        