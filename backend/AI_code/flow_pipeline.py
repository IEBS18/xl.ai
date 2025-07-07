from prompt_handler import PromptHandler
from data import json_to_dataframe
from openai import AzureOpenAI
import pandas as pd
import os
import openpyxl
import json
from python_exe import PythonCodeExecutor  # your Python executor function
from dotenv import load_dotenv

load_dotenv()
MODEL = "gpt-4o-mini"

openai_client = AzureOpenAI(
    api_key= os.getenv("AZUREAPI"),
    api_version= os.getenv("AZUREVERSION"),
    azure_endpoint= os.getenv("AZUREENDPOINT")
)

def response_openai(sys_prompt,user_prompt):
    # print("System prompt: ",sys_prompt)
    # print("User prompt: ", user_prompt)
    response = openai_client.chat.completions.create(
        model= MODEL,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user",   "content": user_prompt }
        ],
        temperature= 0.1,
        
        )
    
    return response.choices[0].message.content.strip()
        
        
        
def run_workflow(df, user_query:str, user_q_type: str, model_choice: str):
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
    execute = PythonCodeExecutor()

    # def exec_code(code: str, context_df: pd.DataFrame) :
    #     return execute.execute_code(
    #         code,
    #         {
    #             "df": context_df,
    #             "pd": pd,
    #             # "SimpleImputer": SimpleImputer,
    #             # "MinMaxScaler": MinMaxScaler,
    #             "openpyxl": openpyxl,
    #             "pd": pd,
    #             "response_openai": response_openai,
    #         }
    #     )

    ##base greeting message pending on user query

    if user_q_type.lower() == "excel":
        system_clean, user_clean = ph.clean_df(data)
        df_clean = response_openai(system_clean, user_clean)
        print("clean:\n",df_clean)
        
        system_p, user_p = ph.Excel_formual(df_clean)
        return response_openai(system_p, user_p)
    
    if user_q_type.lower() == "forecast":
        ##_______________auto-cleanup________________________
        sys1, user1 = ph.clean_df(data)
        code1 = response_openai(sys1, user1)
        print("clen df code", code1) #```python `
        out1 = execute.execute_code(code1, {"df": data})
        # out1 = exec_code(code1, {"df": data})
        print("out1", out1)
        df_clean = out1["variables"].get("df", out1["result"])
        
        ##______________preprocessing_________________________
        sys2, user2 = ph.preprocess_model(df_clean)
        code2 = response_openai(sys2, user2)
        out2 = execute.execute_code(code2, {"df": df_clean})
        df_prepped = out2["variables"].get("df", out2["result"])
        
        #_____________best model fit/user model fit___________
        sys3, user3 = ph.fit_model(df_prepped, model_choice)
        code3 = response_openai(sys3, user3)
        out3 = execute.execute_code(code3, {"df": df_prepped})
        per_model = out3["variables"].get("per_model", out3["result"])
        
        ### response should return 2 data frame
        
        # #____________chart/dashboard creation___________________
        best_name = max(per_model, key=lambda k: per_model[k]["accuracy"])
        best = per_model[best_name]

        # e) Charts & dashboard
        sys4, user4 = ph.chart(pd.DataFrame(best["preds"]))
        chart_code = response_openai(sys4, user4)
        out4 = execute.execute_code(chart_code, {
            "df": pd.DataFrame(best["preds"]),
            **({"metrics": best["metrics"]} if "metrics" in best else {})
        })

        return {
            "clean_step": out1,
            "preprocess_step": out2,
            "model_step": out3,
            "best_model": best_name,
            "metrics": best["metrics"],
            "predictions": best["preds"],
            "chart_step": out4
        }

    raise ValueError(f"Unknown user_q_type: {user_q_type}")

if __name__ == "__main__":
    # Example local run
    with open("spreadsheet.json", "r", encoding="utf-8") as f:
        json_data = json.load(f)
    df = json_to_dataframe(json_data)

    out = run_workflow(
        df=df,
        user_query="Forecast sales for next quarter",
        user_q_type="forecast",
        model_choice="best"
    )
    print(json.dumps(out, indent=2))
