import pandas as pd
import json


def json_to_dataframe(j_data):
    
    cell_data = {}
    
    for cell, value in j_data.items():
        col = cell[0]
        row = cell[1:]
        val = value.get('value', '')
        cell_data.setdefault(row, {})[col] = val
        
    # print(cell_data)
        
    result = pd.DataFrame.from_dict(cell_data, orient='index')
    header = result.loc["1"].tolist()
    df = result.drop(index="1")
    # 4) Assign the real column names
    df.columns = header
    
    # 5) Convert the remaining index labels to int, sort, reset
    df.index = df.index.astype(int)
    df = df.sort_index().reset_index(drop=True)
    
    return df
    
    
if __name__ == "__main__":

    path = "sample.json"
    
    with open(path, 'r', encoding='utf-8') as fp:
        full = json.load(fp)
        
    data_dict = full['data']
    
    print(json_to_dataframe(data_dict))


        
        
        
        
        
        
        