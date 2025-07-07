import os
import pandas as pd

class PromptHandler:
    def __init__(self, base_prompt, user_query):
        self.base_prompt = base_prompt.strip()
        self.user_query = user_query
        
    def _load(self, fname: str) -> str:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)
        path = os.path.join(base_dir, f"prompts\\{fname}")
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
        
    def _make(self, prompt, data: pd.DataFrame, task: str):
        # table_txt = data.to_string(index=False)
        system_prompt = f""" You are a Data Scientist AI Assistant working on forecasting pipelines.
        Tool description: {self.base_prompt}
        task: {task}
        Instriction: {self._load(prompt)}
        Data:
        ```
        {data}
        ```
        Output : dataframe using pandas library in python.
        """.strip()
        return system_prompt
    
    def Excel_formual(self, data: pd.DataFrame):
        # table_txt = data.to_string(index= False)
            
        system_prompt = f""" You are a Data Analyst AI Assistant skilled in advanced Excel formulas.
        Tool Description: {self.base_prompt}
        task: Apply advanced Excel formulas
        Instriction: {self._load("formula.txt")}
        Data:
        ```
        {data}
        ```
        Output : Output format: JSON with keys ['output(value)','formula','reason']
        """.strip()
        user_prompt = f"Step2: {self.user_query}  Use the advanced Excel toolkit."
        
        return system_prompt, user_prompt
        
    def clean_df(self, data: pd.DataFrame):
        # data_str = data.to_string(index=False)
        task = "Auto-clean dataset for forecasting"
        prompt_path = "autoclean.txt"    
        system_prompt = self._make(prompt_path, data, task)
        user_prompt = "Step 1: Clean the data for further preprocessing and forecasting.".strip()
        
        return system_prompt, user_prompt
    
    def preprocess_model(self, data: pd.DataFrame):
        task = "Preprocess cleaned data for time-series modeling"
        prompt_path = "autoclean.txt"    
        system_prompt = self._make(prompt_path, data, task)
        user_prompt = "Step 2: Clean the data for further preprocessing and forecasting.".strip()
        
        return system_prompt, user_prompt
    
    def fit_model(self, data: pd.DataFrame, model_choice: str="best"):
        if model_choice.lower() == "best":
            prompt_path = "model.txt"
            task  = "Automatically select and fit the best time-series model"
            system_prompt = self._make(prompt_path, data,task)
            user_prompt = "Step 3: Fit the best model automatically."
        else:
            prompt_path = "user_selected_model.txt"
            task  = f"Fit user-selected model: {model_choice}"
            system_prompt = self._make(prompt_path, data, task)
            user_prompt = f"Step 3: Fit the user-selected model ({model_choice})."
        return system_prompt, user_prompt
            
    def chart(self, data: pd.DataFrame):
        system_prompt = f"""You are a Data Scientist AI Assistant skilled in data visualization.\n"
            Tool description: {self.base_prompt}
            Task: Generate charts and dashboard
            Instructions: {self._load('chart.txt')}
            Forecast results: {data}
            Output: code snippets (e.g. matplotlib) and dashboard layout"""
        user_prompt = "Step 4: Generate charts and dashboard for visualization."
        
        return system_prompt, user_prompt
    
    
        
        
        
        
        
    