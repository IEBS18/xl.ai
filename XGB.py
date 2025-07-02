import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, root_mean_squared_error, mean_absolute_percentage_error


class XGBoostTimeSeries:
    def __init__(self, data):
        """
        Initialize the class with data, process it and prepare for modeling
        """
        self.df = data
        self.model = XGBRegressor(objective='reg:squarederror', n_estimators=200, max_depth=5)
        self.features = None
        self.target = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        self.X = None
        self.y = None
    
    def preprocess_data(self):
        """
        Preprocesses the data to create time-related features and lag features.
        """
        self.df.index = pd.to_datetime(self.df.index)
        # self.df.set_index('Date', inplace=True)

        # Create relevant time features
        self.df['Month'] = self.df.index.month
        self.df['Year'] = self.df.index.year
        self.df['Day'] = self.df.index.day

        # Lag features (previous month's values)
        self.df['Lag_1'] = self.df['Value'].shift(1)
        self.df['Lag_2'] = self.df['Value'].shift(2)
        self.df['Lag_3'] = self.df['Value'].shift(3)
        self.df['Lag_6'] = self.df['Value'].shift(6)
        self.df['Lag_12'] = self.df['Value'].shift(12)
        
        self.df['rolling_mean_3'] = self.df['Value'].rolling(window=3).mean()
        self.df['rolling_std_6'] = self.df['Value'].rolling(window=6).std()

        # Drop rows with NaN values resulting from the lag features
        self.df.dropna(inplace=True)
        
        if self.df.empty:
            return False

        # Define features (X) and target (y)
        self.features = ['Month', 'Year', 'Day', 'Lag_1', 'Lag_2', 'Lag_3', 'Lag_6', 'Lag_12','rolling_mean_3', 'rolling_std_6']
        self.target = 'Value'
        
        # Split the data into features and target
        self.X = self.df[self.features]
        self.y = self.df[self.target]

        # Split data into training and testing sets
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.2, shuffle=False)
        
        return True
    
    def train_model(self):
        """
        Trains the XGBoost model using the training data.
        """
        self.model.fit(self.X_train, self.y_train)
    
    def evaluate_model(self):
        """
        Evaluates the model on the test data and prints the Mean Squared Error.
        """
        y_pred = self.model.predict(self.X_test)
        rmse = root_mean_squared_error(self.y_test, y_pred)
        mape = mean_absolute_percentage_error(self.y_test, y_pred)
        mad = np.mean(np.abs(self.y_test - y_pred))
        r2 = r2_score(self.y_test, y_pred)
        eval_df = pd.DataFrame({
                    'Metric': ['Root Mean Squared Error', 'Mean Absolute Percentage Error', 'Mean Absolute Deviation', 'R2 Score'],
                    'Value': [rmse, mape, mad, r2]
                })
        # print(f'Root Mean Squared Error on test data: {rmse}')
        
        return eval_df
    
    def predict_future(self, end_date):
        """
        Predict future values up until the given end_date, including lag and rolling features.
        """
        future_dates = pd.date_range(start=self.df.index[-1] + pd.Timedelta(days=1), end=end_date, freq='MS')
        predictions = []
        
        self.model.fit(self.X, self.y)
        # Copy historical values to update dynamically
        history = self.df['Value'].copy()

        for date in future_dates:
            # Create time-based features
            month = date.month
            year = date.year
            day = date.day

            # Get lag values from history
            lag_1 = history.iloc[-1]
            lag_2 = history.iloc[-2]
            lag_3 = history.iloc[-3]
            lag_6 = history.iloc[-6] if len(history) >= 6 else np.nan
            lag_12 = history.iloc[-12] if len(history) >= 12 else np.nan

            # Rolling features
            rolling_mean_3 = history.iloc[-3:].mean() if len(history) >= 3 else np.nan
            rolling_std_6 = history.iloc[-6:].std() if len(history) >= 6 else np.nan

            # Prepare input for prediction
            features = pd.DataFrame([{
                'Month': month,
                'Year': year,
                'Day': day,
                'Lag_1': lag_1,
                'Lag_2': lag_2,
                'Lag_3': lag_3,
                'Lag_6': lag_6,
                'Lag_12': lag_12,
                'rolling_mean_3': rolling_mean_3,
                'rolling_std_6': rolling_std_6
            }])

            # Predict and append result
            predicted_value = self.model.predict(features)[0]
            predictions.append(predicted_value)

            # Append to history for next iteration
            history = pd.concat([history, pd.Series([predicted_value], index=[date])])

        return predictions, future_dates
    
    def feature_importance_summary(self):
        """
        Returns a DataFrame summarizing feature importance by Gain, Coverage, and Frequency.
        """
        booster = self.model.get_booster()
        importance_types = ['gain', 'cover', 'weight']

        importance_dicts = {typ: booster.get_score(importance_type=typ) for typ in importance_types}

        all_features = set().union(*[set(d.keys()) for d in importance_dicts.values()])
        data = []

        for feature in all_features:
            gain = importance_dicts['gain'].get(feature, 0.0)
            cover = importance_dicts['cover'].get(feature, 0.0)
            freq = importance_dicts['weight'].get(feature, 0)

            data.append({
                'Feature': feature,
                'Gain': gain,
                'Coverage': cover,
                'Frequency': freq
            })

        df_imp = pd.DataFrame(data)

        # Normalize values to show percentages
        df_imp['Gain'] = 100 * df_imp['Gain'] / df_imp['Gain'].sum()
        df_imp['Coverage'] = 100 * df_imp['Coverage'] / df_imp['Coverage'].sum()
        df_imp['Frequency'] = 100 * df_imp['Frequency'] / df_imp['Frequency'].sum()

        df_imp = df_imp.sort_values('Gain', ascending=False)
        return df_imp.round(2)
