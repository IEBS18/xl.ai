from prompt_handler import PromptHandler
from data import json_to_dataframe
from openai import AzureOpenAI
import pandas as pd
import os
import openpyxl
import json
from dotenv import load_dotenv

load_dotenv()
MODEL = "gpt-4o-mini"

openai_client = AzureOpenAI(
    api_key= os.getenv("AZUREAPI"),
    api_version= os.getenv("AZUREVERSION"),
    azure_endpoint= os.getenv("AZUREENDPOINT")
)

def response_openai(sys_prompt,user_prompt):
    print("System prompt: ",sys_prompt)
    print("User prompt: ", user_prompt)
    response = openai_client.chat.completions.create(
        model= MODEL,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": user_prompt }
        ],
        temperature= 0.1,
        
        )
    
    return response.choices[0].message.content.strip()
        
        
        
def run_workflow(df: pd.DataFrame, user_query:str, user_q_type: str, model_choice: str):
    """
    Orchestrate either:
      • an Excel‐formula workflow, or
      • a forecast pipeline (clean → preprocess → fit → chart → report)
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(script_dir)
    path = os.path.join(base_dir, "prompts", "base.txt")
    with open(path, 'r', encoding='utf-8') as fb:
        base_prompt = fb.read()
    data = df[1:]
    ph = PromptHandler(base_prompt, user_query)
    
    if user_q_type.lower() == "excel":
        system_clean, user_clean = ph.clean_df(data)
        df_clean = response_openai(system_clean, user_clean)
        
        system_p, user_p = ph.Excel_formual(df_clean)
        return response_openai(system_p, user_p)
    
    if user_q_type.lower() == "forecast":
        ##_______________auto-cleanup________________________
        s1, u1 = ph.clean_df(data)
        df_clean = response_openai(s1, u1)
        
        ##______________preprocessing_________________________
        s2,u2 = ph.preprocess_model(df_clean)
        df_preprocess = response_openai(s2,u2)
        
        #_____________best model fit/user model fit___________
        s3, u3 = ph.fit_model(df_preprocess, model_choice)
        fit_response = response_openai(s3, u3)
        
        ### response should return 2 data frame
        
        # #____________chart/dashboard creation___________________
        # s4, u4 = ph.chart(fit_response[0])
        
    return fit_response


if __name__ == "__main__":
    
    # script_dir = os.path.dirname(os.path.abspath(__file__))
    # base_dir = os.path.dirname(script_dir)
    # path = os.path.join(base_dir, 'sample.json')

    
    path = "../sample.json"
    
    with open(path, 'r', encoding='utf-8') as fp:
        full = json.load(fp)
        
    data_dict = full['data']
    
    df = json_to_dataframe(data_dict)
    # df_new = df.drop(df.index[0]).reset_index(drop=True)
    print(df.head())
    # df.to_excel("result_df.xlsx", index= False)
    
    user_query = "What is the total sales from customer stuff-mart for 2024 year?"
    
    query_type = "Forecast"
    
    model_type = "ARIMA"
    
    result = run_workflow(df,user_query, query_type, model_type)
    
    print(f"result is : {result}")

        
        
    
    
    
    

