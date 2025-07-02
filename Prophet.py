import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_squared_error, mean_absolute_error, mean_absolute_percentage_error, r2_score
import numpy as np

class ProphetTimeSeriesModel:
    
    """
    Initializing the class with timeseries data, date column is already reindexed and Values could be renamed to target
    spliting data for Train and split
    model trianing using train data
    evaluating model performance using evaluation metrices 
    predict the values using the test dates 
    Plot the components and plot the forcast
    """
    def __init__(self, data, freq):
        self.df = data.reset_index().rename(columns ={
            'Date': 'ds',
            'Value': 'y'
        })
        self.model = Prophet()
        self.train = None
        self.test = None
        self.forecast = None
        
    def preprocess_data(self, split_ratio=0.8):
        """
        Preprocesses the data for Prophet and splits into train and test sets.
        """
        total_len = len(self.df)
        split_point = int(split_ratio * total_len)
        self.train = self.df.iloc[:split_point]
        self.test = self.df.iloc[split_point:]
        return True if not self.df.empty else False
    
    def train_model(self):
        self.model.fit(self.train)
        
    def evaluate_model(self):
        
        future = self.model.make_future_dataframe(periods=len(self.test), freq='M')
        self.forecast = self.model.predict(future)
        
        y_true = self.test['y'].values
        y_pred = self.forecast.iloc[-len(self.test):]['yhat'].values
        
        mse = mean_squared_error(y_true=y_true, y_pred=y_pred)
        rmse = np.sqrt(mse)
        # mae = mean_absolute_error(y_true=y_true, y_pred=y_pred)
        mape = mean_absolute_percentage_error(y_true=y_true, y_pred=y_pred)
        mad = np.mean(np.abs(y_true-y_pred))
        r2 = r2_score(y_true=y_true, y_pred=y_pred)
        
        eval_df = pd.DataFrame({
            'Metrices': ['Root Mean Squared Error', 'Mean Absolute Percentage Error', 'Mean Absolute Deviation', 'R2 Score'],
            'Value' : [rmse, mape, mad, r2]
        })
        
        return eval_df
    
    def predict_future(self, periods):
        
        self.model = Prophet()
        self.model.fit(self.df)
        future = self.model.make_future_dataframe(periods=periods, freq='M')
        forecast = self.model.predict(future)
        return forecast[['ds','yhat', 'yhat_lower', 'yhat_upper']].iloc[-periods:]
    

        
        

