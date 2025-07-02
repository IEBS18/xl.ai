import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error, r2_score

class ExponentialSmoothingTimeSeries:
    def __init__(self, data, seasonal_periods=12, 
                 trend='add', seasonal='add', damped_trend=False,
                 use_boxcox=False, initialization_method='estimated'):
        """
        Initialize with time series data and model configuration.
        """
        self.df = data.copy()
        self.model = None
        self.fitted_model = None
        self.seasonal_periods = seasonal_periods
        self.trend = trend  # 'add', 'mul', or None
        self.seasonal = seasonal  # 'add', 'mul', or None
        self.damped_trend = damped_trend
        self.use_boxcox = use_boxcox
        self.initialization_method = initialization_method
        self.train = None
        self.test = None

    def preprocess_data(self, test_size=0.2):
        """
        Split the data into training and test sets, checking for minimum required data length.
        Returns False if data is too small for seasonal modeling.
        """
        self.df.index = pd.to_datetime(self.df.index)
        # self.df = self.df.asfreq('MS')  # MS = Month Start
        
        # Check if data has at least 2 full seasonal cycles
        if len(self.df) < 2 * self.seasonal_periods:
            return False

        n = int(len(self.df) * (1 - test_size))
        self.train = self.df.iloc[:n]
        self.test = self.df.iloc[n:]

        # Additional check after splitting
        if len(self.train) < 2 * self.seasonal_periods:
            return False

        return True

    def train_model(self):
        """
        Fit the exponential smoothing model.
        """
        self.model = ExponentialSmoothing(
            self.train['Value'],
            trend=self.trend,
            damped_trend=self.damped_trend,
            seasonal=self.seasonal,
            seasonal_periods=self.seasonal_periods,
            initialization_method=self.initialization_method,
            use_boxcox=self.use_boxcox
        )
        self.fitted_model = self.model.fit(optimized=True)

    def evaluate_model(self):
        """
        Evaluate the model performance on the test set.
        """
        preds = self.fitted_model.forecast(len(self.test))
        rmse = np.sqrt(mean_squared_error(self.test['Value'], preds))
        mae = mean_absolute_percentage_error(self.test['Value'], preds)
        mad = np.mean(np.abs(self.test['Value'] - preds))
        r2 = r2_score(self.test['Value'], preds)
        eval_df = pd.DataFrame({
            'Metric': ['Root Mean Squared Error', 'Mean Absolute Percentage Error', 'Mean Absolute Deviation','R2 Score'],
            'Value': [rmse, mae, mad, r2]
        })
        return eval_df

    def predict_future(self, steps=12):
        """
        Fit model on the entire dataset and forecast future values.
        """
        model = ExponentialSmoothing(
            self.df['Value'],
            trend=self.trend,
            damped_trend=self.damped_trend,
            seasonal=self.seasonal,
            seasonal_periods=self.seasonal_periods,
            initialization_method=self.initialization_method,
            use_boxcox=self.use_boxcox
        )
        fitted_model = model.fit(optimized=True)
        future_forecast = fitted_model.forecast(steps)
        return future_forecast


    def get_model_summary(self):
        """
        Return summary of the fitted model.
        """
        return self.fitted_model.summary()
