import os
import json
import uuid
from datetime import datetime, timedelta
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Try to import sklearn components
try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import PolynomialFeatures
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
    from scipy.optimize import curve_fit
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# Try to import additional forecasting libraries
try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

def analyze_spreadsheet_structure(sheet_data):
    """Analyzes the spreadsheet structure to understand data patterns and relationships."""
    analysis = {
        "columns": {},
        "data_types": {},
        "metrics": {}
    }
    
    # Extract column headers
    headers = {}
    for cell, data in sheet_data.items():
        if cell.endswith('1'):  # Header row
            col = cell[:-1]
            headers[col] = data.get('value', '')
            analysis["columns"][col] = data.get('value', '')
    
    # Analyze data types
    for col, header in headers.items():
        col_values = []
        for row in range(2, 50):  # Check up to 50 rows
            cell_key = f"{col}{row}"
            if cell_key in sheet_data:
                val = sheet_data[cell_key].get('value')
                if val is not None:
                    col_values.append(val)
        
        if col_values:
            # Check if numeric
            numeric_count = 0
            for v in col_values:
                try:
                    float(v)
                    numeric_count += 1
                except (ValueError, TypeError):
                    pass
            
            if numeric_count > len(col_values) * 0.7:  # 70% threshold
                analysis["data_types"][col] = "numeric"
            else:
                analysis["data_types"][col] = "text"
    
    return analysis

def create_dataframe_from_sheet(sheet_data):
    """Convert sheet data to pandas DataFrame."""
    # Get headers
    headers = {}
    for cell, data in sheet_data.items():
        if cell.endswith('1'):
            col = cell[:-1]
            headers[col] = data.get('value', '')
    
    # Find max row
    max_row = 0
    for cell in sheet_data.keys():
        if any(c.isdigit() for c in cell):
            row_num = int(''.join(filter(str.isdigit, cell)))
            max_row = max(max_row, row_num)
    
    # Build DataFrame
    rows = []
    for row_num in range(2, max_row + 1):
        row_data = {}
        for col in headers.keys():
            cell_key = f"{col}{row_num}"
            if cell_key in sheet_data:
                row_data[col] = sheet_data[cell_key].get('value')
        if row_data:
            rows.append(row_data)
    
    df = pd.DataFrame(rows)
    return df, headers

def calculate_forecast_metrics(actual, predicted):
    """Calculate various forecast accuracy metrics."""
    try:
        mae = mean_absolute_error(actual, predicted)
        mse = mean_squared_error(actual, predicted)
        rmse = np.sqrt(mse)
        mape = np.mean(np.abs((actual - predicted) / actual)) * 100
        
        return {
            'MAE': float(mae),
            'MSE': float(mse),
            'RMSE': float(rmse),
            'MAPE': float(mape)
        }
    except:
        return {'MAE': 0, 'MSE': 0, 'RMSE': 0, 'MAPE': 0}

def analyze_data_patterns(df, target_col):
    """Analyze data patterns and provide insights."""
    values = df[target_col].values
    
    # Basic statistics
    stats = {
        'count': len(values),
        'mean': float(np.mean(values)),
        'std': float(np.std(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'median': float(np.median(values))
    }
    
    # Trend analysis
    x = np.arange(len(values))
    slope, intercept = np.polyfit(x, values, 1)
    trend = 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
    
    # Volatility
    volatility = np.std(np.diff(values)) if len(values) > 1 else 0
    
    # Seasonality detection (simple)
    seasonality = 'unknown'
    if len(values) >= 12:
        # Check for potential monthly seasonality
        monthly_means = []
        for i in range(min(12, len(values))):
            idx = list(range(i, len(values), 12))
            if idx:
                monthly_means.append(np.mean([values[j] for j in idx]))
        
        if len(monthly_means) > 1:
            seasonal_variance = np.var(monthly_means)
            overall_variance = np.var(values)
            if seasonal_variance > overall_variance * 0.1:
                seasonality = 'possible'
    
    return {
        'statistics': stats,
        'trend': trend,
        'trend_slope': float(slope),
        'volatility': float(volatility),
        'seasonality': seasonality
    }

def linear_regression_forecast(df, target_col, periods=6):
    """Linear regression forecasting."""
    values = df[target_col].values
    x = np.arange(len(values))
    
    # Calculate linear regression manually
    n = len(values)
    sum_x = np.sum(x)
    sum_y = np.sum(values)
    sum_xy = np.sum(x * values)
    sum_x2 = np.sum(x * x)
    
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n
    
    # Make predictions
    future_x = np.arange(len(values), len(values) + periods)
    predictions = slope * future_x + intercept
    
    # Calculate confidence intervals (simple approach)
    residuals = values - (slope * x + intercept)
    std_error = np.std(residuals)
    confidence_interval = 1.96 * std_error  # 95% CI
    
    return {
        'predictions': predictions.tolist(),
        'model_name': 'Linear Regression',
        'slope': float(slope),
        'intercept': float(intercept),
        'confidence_interval': float(confidence_interval),
        'std_error': float(std_error)
    }

def moving_average_forecast(df, target_col, periods=6, window=3):
    """Moving average forecasting."""
    values = df[target_col].values
    
    if len(values) < window:
        window = len(values)
    
    # Calculate moving average
    if window == 1:
        ma = values
    else:
        ma = np.convolve(values, np.ones(window)/window, mode='valid')
    
    if len(ma) == 0:
        last_ma = np.mean(values)
        trend = 0
    else:
        last_ma = ma[-1]
        trend = (ma[-1] - ma[-2]) if len(ma) > 1 else 0
    
    # Generate predictions
    predictions = [last_ma + trend * i for i in range(1, periods + 1)]
    
    return {
        'predictions': predictions,
        'model_name': f'Moving Average (window={window})',
        'last_ma': float(last_ma),
        'trend': float(trend)
    }

def ema_forecast(df, target_col, periods=6, alpha=0.3):
    """Exponential Moving Average forecasting."""
    values = df[target_col].values
    
    if len(values) == 0:
        return {'predictions': [0] * periods, 'model_name': 'EMA', 'alpha': alpha}
    
    # Calculate EMA
    ema = [values[0]]
    for i in range(1, len(values)):
        ema.append(alpha * values[i] + (1 - alpha) * ema[-1])
    
    # Calculate trend
    if len(ema) > 1:
        trend = ema[-1] - ema[-2]
    else:
        trend = 0
    
    # Generate predictions
    last_ema = ema[-1]
    predictions = [last_ema + trend * i for i in range(1, periods + 1)]
    
    return {
        'predictions': predictions,
        'model_name': f'Exponential Moving Average (α={alpha})',
        'alpha': alpha,
        'last_ema': float(last_ema),
        'trend': float(trend)
    }

def box_jenkins_forecast(df, target_col, periods=6):
    """Box-Jenkins (ARIMA) forecasting."""
    if not STATSMODELS_AVAILABLE:
        return moving_average_forecast(df, target_col, periods)
    
    try:
        values = df[target_col].values
        
        if len(values) < 10:
            return moving_average_forecast(df, target_col, periods)
        
        # Check for stationarity
        adf_result = adfuller(values)
        is_stationary = adf_result[1] < 0.05
        
        # Simple ARIMA model selection
        if is_stationary:
            order = (1, 0, 1)  # AR(1), I(0), MA(1)
        else:
            order = (1, 1, 1)  # AR(1), I(1), MA(1)
        
        # Fit ARIMA model
        model = ARIMA(values, order=order)
        fitted_model = model.fit()
        
        # Make predictions
        forecast = fitted_model.forecast(steps=periods)
        
        return {
            'predictions': forecast.tolist(),
            'model_name': f'Box-Jenkins ARIMA{order}',
            'order': order,
            'is_stationary': is_stationary,
            'adf_pvalue': float(adf_result[1])
        }
    
    except Exception as e:
        print(f"Box-Jenkins failed: {e}")
        return moving_average_forecast(df, target_col, periods)

def xgb_forecast(df, target_col, periods=6):
    """XGBoost forecasting."""
    if not XGB_AVAILABLE:
        return moving_average_forecast(df, target_col, periods)
    
    try:
        values = df[target_col].values
        
        if len(values) < 5:
            return moving_average_forecast(df, target_col, periods)
        
        # Create features (lag features and trend)
        X = []
        y = []
        
        # Use last 3 values as features
        window = min(3, len(values) - 1)
        
        for i in range(window, len(values)):
            features = list(values[i-window:i]) + [i]  # Add time trend
            X.append(features)
            y.append(values[i])
        
        if len(X) == 0:
            return moving_average_forecast(df, target_col, periods)
        
        X = np.array(X)
        y = np.array(y)
        
        # Train XGBoost model
        model = xgb.XGBRegressor(n_estimators=100, max_depth=3, random_state=42)
        model.fit(X, y)
        
        # Make predictions
        predictions = []
        current_window = list(values[-window:])
        
        for i in range(periods):
            features = current_window + [len(values) + i]
            pred = model.predict([features])[0]
            predictions.append(pred)
            current_window = current_window[1:] + [pred]
        
        return {
            'predictions': predictions,
            'model_name': f'XGBoost (window={window})',
            'window_size': window,
            'feature_importance': model.feature_importances_.tolist() if hasattr(model, 'feature_importances_') else []
        }
    
    except Exception as e:
        print(f"XGBoost failed: {e}")
        return moving_average_forecast(df, target_col, periods)

def fbprophet_forecast(df, target_col, periods=6):
    """Facebook Prophet forecasting."""
    if not PROPHET_AVAILABLE:
        return moving_average_forecast(df, target_col, periods)
    
    try:
        values = df[target_col].values
        
        if len(values) < 10:
            return moving_average_forecast(df, target_col, periods)
        
        # Prepare data for Prophet
        dates = pd.date_range(start='2020-01-01', periods=len(values), freq='M')
        prophet_df = pd.DataFrame({
            'ds': dates,
            'y': values
        })
        
        # Fit Prophet model
        model = Prophet(yearly_seasonality=False, weekly_seasonality=False, daily_seasonality=False)
        model.fit(prophet_df)
        
        # Make future predictions
        future = model.make_future_dataframe(periods=periods, freq='M')
        forecast = model.predict(future)
        
        # Extract predictions
        predictions = forecast['yhat'].tail(periods).tolist()
        
        return {
            'predictions': predictions,
            'model_name': 'Facebook Prophet',
            'trend': forecast['trend'].iloc[-1],
            'seasonal': forecast.get('seasonal', [0])[-1] if 'seasonal' in forecast.columns else 0
        }
    
    except Exception as e:
        print(f"Facebook Prophet failed: {e}")
        return moving_average_forecast(df, target_col, periods)

def polynomial_forecast(df, target_col, degree=2, periods=6):
    """Polynomial regression forecasting (requires sklearn)."""
    if not SKLEARN_AVAILABLE:
        return moving_average_forecast(df, target_col, periods)
    
    X = np.arange(len(df)).reshape(-1, 1)
    y = df[target_col].values
    
    poly_features = PolynomialFeatures(degree=degree)
    X_poly = poly_features.fit_transform(X)
    
    model = LinearRegression()
    model.fit(X_poly, y)
    
    future_X = np.arange(len(df), len(df) + periods).reshape(-1, 1)
    future_X_poly = poly_features.transform(future_X)
    predictions = model.predict(future_X_poly)
    
    return {
        'predictions': predictions.tolist(),
        'model_name': f'Polynomial Regression (degree={degree})',
        'degree': degree,
        'r2_score': float(r2_score(y, model.predict(X_poly)))
    }

def create_forecast_chart(df, results, target_col, data_insights):
    """Create comprehensive forecast visualization."""
    try:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Main forecast plot
        historical_x = range(len(df))
        ax1.plot(historical_x, df[target_col].values, 'o-', 
                label='Historical Data', linewidth=2, markersize=6, color='black')
        
        # Plot forecasts
        colors = ['red', 'green', 'blue', 'orange', 'purple', 'brown', 'pink']
        
        for i, (model_name, result) in enumerate(results.items()):
            if 'predictions' in result:
                forecast_x = range(len(df), len(df) + len(result['predictions']))
                ax1.plot(forecast_x, result['predictions'], 's--', 
                        label=model_name, linewidth=2, markersize=6, 
                        color=colors[i % len(colors)])
        
        ax1.set_title(f'Forecast Analysis: {target_col}', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Time Period')
        ax1.set_ylabel('Value')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Data distribution
        ax2.hist(df[target_col].values, bins=min(20, len(df)//2), alpha=0.7, color='skyblue')
        ax2.set_title('Data Distribution', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Value')
        ax2.set_ylabel('Frequency')
        ax2.grid(True, alpha=0.3)
        
        # Trend analysis
        x = np.arange(len(df))
        slope, intercept = np.polyfit(x, df[target_col].values, 1)
        ax3.plot(x, df[target_col].values, 'o-', label='Data', color='blue')
        ax3.plot(x, slope * x + intercept, '--', label='Trend Line', color='red')
        ax3.set_title('Trend Analysis', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Time Period')
        ax3.set_ylabel('Value')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # Model comparison (if multiple models)
        if len(results) > 1:
            model_names = list(results.keys())
            last_predictions = [results[name]['predictions'][-1] if 'predictions' in results[name] else 0 
                              for name in model_names]
            
            ax4.bar(range(len(model_names)), last_predictions, color=colors[:len(model_names)])
            ax4.set_title('Final Period Predictions by Model', fontsize=14, fontweight='bold')
            ax4.set_xlabel('Model')
            ax4.set_ylabel('Predicted Value')
            ax4.set_xticks(range(len(model_names)))
            ax4.set_xticklabels(model_names, rotation=45, ha='right')
            ax4.grid(True, alpha=0.3)
        else:
            ax4.text(0.5, 0.5, 'Multiple models needed\nfor comparison', 
                    ha='center', va='center', transform=ax4.transAxes, fontsize=12)
            ax4.set_title('Model Comparison', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save chart
        chart_id = f"forecast_{uuid.uuid4().hex[:8]}"
        
        # Create static directory if it doesn't exist
        if not os.path.exists('static'):
            os.makedirs('static')
        
        image_path = f"static/{chart_id}.png"
        plt.savefig(image_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return chart_id
        
    except Exception as e:
        print(f"Chart creation failed: {e}")
        return ""

def generate_forecast_report(df, results, target_col, data_insights):
    """Generate comprehensive forecast report with insights."""
    
    report = {
        "executive_summary": "",
        "data_analysis": {},
        "model_performance": {},
        "forecasts": {},
        "insights": [],
        "recommendations": []
    }
    
    # Executive Summary
    total_models = len(results)
    data_points = len(df)
    trend = data_insights.get('trend', 'unknown')
    
    report["executive_summary"] = f"""
    Forecast Analysis Report for {target_col}
    
    This analysis examined {data_points} historical data points using {total_models} different forecasting models.
    The data shows a {trend} trend with notable patterns that inform future predictions.
    
    Key findings indicate potential future values ranging from {min([min(r.get('predictions', [0])) for r in results.values()]): .2f} 
    to {max([max(r.get('predictions', [0])) for r in results.values()]): .2f} across different forecasting approaches.
    """
    
    # Data Analysis
    stats = data_insights.get('statistics', {})
    report["data_analysis"] = {
        "historical_summary": {
            "data_points": stats.get('count', 0),
            "average_value": stats.get('mean', 0),
            "volatility": stats.get('std', 0),
            "range": {
                "min": stats.get('min', 0),
                "max": stats.get('max', 0)
            }
        },
        "trend_analysis": {
            "direction": trend,
            "strength": abs(data_insights.get('trend_slope', 0)),
            "volatility": data_insights.get('volatility', 0)
        },
        "seasonality": data_insights.get('seasonality', 'unknown')
    }
    
    # Model Performance and Forecasts
    for model_name, result in results.items():
        if 'predictions' in result:
            predictions = result['predictions']
            
            report["forecasts"][model_name] = {
                "predictions": predictions,
                "average_prediction": np.mean(predictions),
                "prediction_range": {
                    "min": min(predictions),
                    "max": max(predictions)
                }
            }
            
            # Model-specific metrics
            model_info = {
                "model_type": model_name,
                "prediction_count": len(predictions),
                "confidence": "medium"  # Default confidence
            }
            
            # Add model-specific details
            if "Linear Regression" in model_name:
                model_info["slope"] = result.get('slope', 0)
                model_info["trend_strength"] = "high" if abs(result.get('slope', 0)) > stats.get('std', 0) else "moderate"
            
            elif "ARIMA" in model_name:
                model_info["stationarity"] = "stationary" if result.get('is_stationary', False) else "non-stationary"
                model_info["model_order"] = result.get('order', (0,0,0))
            
            elif "XGBoost" in model_name:
                model_info["feature_importance"] = result.get('feature_importance', [])
                model_info["window_size"] = result.get('window_size', 0)
            
            report["model_performance"][model_name] = model_info
    
    # Generate Insights
    insights = []
    
    # Trend insights
    if trend == 'increasing':
        insights.append(f"The data shows a consistent upward trend, suggesting continued growth in {target_col}.")
    elif trend == 'decreasing':
        insights.append(f"The data indicates a declining trend in {target_col}, which may require attention.")
    else:
        insights.append(f"The {target_col} data shows relatively stable patterns with no strong directional trend.")
    
    # Volatility insights
    volatility = data_insights.get('volatility', 0)
    avg_value = stats.get('mean', 0)
    if avg_value > 0:
        volatility_ratio = volatility / avg_value
        if volatility_ratio > 0.2:
            insights.append("High volatility detected - forecasts should be interpreted with caution.")
        elif volatility_ratio > 0.1:
            insights.append("Moderate volatility present - consider confidence intervals in planning.")
        else:
            insights.append("Low volatility suggests stable, predictable patterns.")
    
    # Model consensus
    if len(results) > 1:
        predictions_lists = [r['predictions'] for r in results.values() if 'predictions' in r]
        if predictions_lists:
            final_predictions = [preds[-1] for preds in predictions_lists]
            prediction_std = np.std(final_predictions)
            prediction_mean = np.mean(final_predictions)
            
            if prediction_mean > 0:
                consensus_ratio = prediction_std / prediction_mean
                if consensus_ratio < 0.1:
                    insights.append("Strong consensus among models - high confidence in forecasts.")
                elif consensus_ratio < 0.3:
                    insights.append("Moderate consensus among models - reasonable confidence in forecasts.")
                else:
                    insights.append("Significant disagreement among models - consider ensemble approach.")
    
    # Seasonality insights
    seasonality = data_insights.get('seasonality', 'unknown')
    if seasonality == 'possible':
        insights.append("Potential seasonal patterns detected - consider longer-term cyclical factors.")
    
    report["insights"] = insights
    
    # Generate Recommendations
    recommendations = []
    
    # Based on trend
    if trend == 'increasing':
        recommendations.append("Consider capacity planning for continued growth.")
        recommendations.append("Monitor for potential acceleration or deceleration in growth rate.")
    elif trend == 'decreasing':
        recommendations.append("Investigate underlying causes of decline.")
        recommendations.append("Develop intervention strategies to address negative trends.")
    
    # Based on volatility
    if volatility_ratio > 0.2:
        recommendations.append("Implement risk management strategies due to high volatility.")
        recommendations.append("Consider shorter forecast horizons for better accuracy.")
    
    # Based on model performance
    if len(results) > 2:
        recommendations.append("Use ensemble forecasting combining multiple models for better accuracy.")
        recommendations.append("Regularly update models with new data for improved performance.")
    
    # Data quality
    if data_points < 12:
        recommendations.append("Collect more historical data to improve forecast reliability.")
    
    recommendations.append("Monitor actual vs. predicted values to validate model performance.")
    recommendations.append("Consider external factors that might impact future values.")
    
    report["recommendations"] = recommendations
    
    return report

def run_forecast_analysis(sheet_data, user_query):
    """Main forecast analysis function with enhanced algorithms."""
    try:
        # Analyze data structure
        analysis = analyze_spreadsheet_structure(sheet_data)
        
        # Create DataFrame
        df, headers = create_dataframe_from_sheet(sheet_data)
        
        if df.empty:
            return {"success": False, "error": "No data found"}
        
        # Find numeric columns
        numeric_cols = [col for col, dtype in analysis["data_types"].items() if dtype == "numeric"]
        
        if not numeric_cols:
            return {"success": False, "error": "No numeric columns found"}
        
        # Select target column (first numeric column)
        target_col = numeric_cols[0]
        
        # Convert to numeric
        df[target_col] = pd.to_numeric(df[target_col], errors='coerce')
        df = df.dropna(subset=[target_col])
        
        if len(df) < 3:
            return {"success": False, "error": "Not enough data points for forecasting"}
        
        # Analyze data patterns
        data_insights = analyze_data_patterns(df, target_col)
        
        # Run forecasting models
        results = {}
        
        # 1. Linear Regression
        try:
            results['Linear Regression'] = linear_regression_forecast(df, target_col)
        except Exception as e:
            print(f"Linear regression failed: {e}")
        
        # 2. Moving Average
        try:
            results['Moving Average'] = moving_average_forecast(df, target_col)
        except Exception as e:
            print(f"Moving average failed: {e}")
        
        # 3. EMA (Exponential Moving Average)
        try:
            results['EMA'] = ema_forecast(df, target_col)
        except Exception as e:
            print(f"EMA failed: {e}")
        
        # 4. Box-Jenkins (ARIMA)
        try:
            results['Box-Jenkins'] = box_jenkins_forecast(df, target_col)
        except Exception as e:
            print(f"Box-Jenkins failed: {e}")
        
        # 5. XGBoost
        try:
            results['XGBoost'] = xgb_forecast(df, target_col)
        except Exception as e:
            print(f"XGBoost failed: {e}")
        
        # 6. Facebook Prophet
        try:
            results['Facebook Prophet'] = fbprophet_forecast(df, target_col)
        except Exception as e:
            print(f"Facebook Prophet failed: {e}")
        
        # 7. Polynomial (if sklearn available)
        if SKLEARN_AVAILABLE:
            try:
                results['Polynomial'] = polynomial_forecast(df, target_col)
            except Exception as e:
                print(f"Polynomial failed: {e}")
        
        # Create chart
        chart_id = create_forecast_chart(df, results, target_col, data_insights)
        
        # Generate comprehensive report
        forecast_report = generate_forecast_report(df, results, target_col, data_insights)
        
        return {
            "success": True,
            "forecast_results": results,
            "chart_id": chart_id,
            "target_column": target_col,
            "data_shape": list(df.shape),
            "models_used": list(results.keys()),
            "data_insights": data_insights,
            "forecast_report": forecast_report,
            "library_availability": {
                "sklearn": SKLEARN_AVAILABLE,
                "xgboost": XGB_AVAILABLE,
                "prophet": PROPHET_AVAILABLE,
                "statsmodels": STATSMODELS_AVAILABLE
            }
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "traceback": traceback.format_exc()
        }

def get_cell_value_from_query(spreadsheet_json: dict, user_query: str, sheet_name: str = "Sheet1") -> dict:
    """Main handler for forecast requests."""
    
    sheet_data = spreadsheet_json.get("data", {}).get("data", {})
    
    if not sheet_data:
        return {"success": False, "error": "No sheet data found"}
    
    # Check if this is a forecast request
    query_lower = user_query.lower()
    is_forecast_request = any(word in query_lower for word in [
        'forecast', 'predict', 'future', 'projection', 'trend', 'model', 'regression'
    ])
    
    if is_forecast_request:
        # Run forecast analysis
        result = run_forecast_analysis(sheet_data, user_query)
        
        # Create response
        response = {
            "success": result.get("success", False),
            "forecast_results": result.get("forecast_results", {}),
            "chart": {
                "id": result.get("chart_id", ""),
                "label": "Forecast Analysis",
                "imageUrl": f"/static/{result.get('chart_id', '')}.png" if result.get('chart_id') else "",
                "type": "forecast",
                "description": f"Forecast analysis for query: {user_query}"
            },
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "forecast",
                "target_column": result.get("target_column", ""),
                "models_used": result.get("models_used", []),
                "data_shape": result.get("data_shape", []),
                "sklearn_available": result.get("sklearn_available", False)
            },
            "raw_results": result
        }
        
        if not result.get("success"):
            response["error"] = result.get("error", "Unknown error")
        
        return response
    
    # For non-forecast requests
    return {
        "success": True,
        "message": "Non-forecast analysis - implement additional logic as needed"
    }

def _np_converter(o):
    """
    JSON serializer for NumPy data types.
    Converts numpy.generic to Python scalar and numpy.ndarray to list.
    """
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(f"Type {type(o)} not serializable")

# Example usage
if __name__ == "__main__":
    # Sample data for testing
    sample_data = {
        "data": {
            "data": {
                "A1": {"value": "Month"},
                "B1": {"value": "Sales"},
                "A2": {"value": "Jan"},
                "B2": {"value": 1000},
                "A3": {"value": "Feb"},
                "B3": {"value": 1200},
                "A4": {"value": "Mar"},
                "B4": {"value": 1100},
                "A5": {"value": "Apr"},
                "B5": {"value": 1300},
                "A6": {"value": "May"},
                "B6": {"value": 1250},
                "A7": {"value": "Jun"},
                "B7": {"value": 1400}
            }
        }
    }
    
    query = "forecast sales for next 6 months using xgboost"
    result = get_cell_value_from_query(sample_data, query)
    print(json.dumps(result, indent=2, default=_np_converter))