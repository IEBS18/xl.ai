import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from dateutil.parser import parse
import matplotlib.pyplot as plt

# Upload dataset manually
def upload_dataset(file_path):
    # file_path = "Auto Parts - Historic Data.xls"
    if file_path.endswith(".csv"):
        return pd.read_csv(file_path)
    elif file_path.endswith((".xls", ".xlsx")):
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format. Use CSV or XLSX.")

# Preview top 15 rows
def preview_dataset(df):
    print("[INFO] Previewing top 10 rows:")
    return df.head(10)

# Identify datetime-like column headers using dateutil
def extract_datetime_columns(df):
    date_cols = []
    for col in df.columns:
        try:
            parse(str(col))
            date_cols.append(col)
        except Exception:
            continue
    return date_cols

def long_with_id(df: pd.DataFrame, date_cols: list[str]) -> pd.DataFrame:
    """
    Melt wide date-columns into 'Date' + 'Value', then compute
    cumulative sum per group of the remaining ID columns.
    """
    df = df.copy()

    # 1) Identify your ID columns by excluding date_cols
    id_cols = [c for c in df.columns if c not in date_cols]

    # 2) Melt from wide → long
    df_long = df.melt(
        id_vars    = id_cols,
        value_vars = date_cols,
        var_name   = "Date",
        value_name = "Value"
    )

    # 3) Parse Date and sort
    df_long["Date"] = pd.to_datetime(df_long["Date"], errors="coerce", format=r'%y-%m-%d')
    df_long["Value"] = pd.to_numeric(df_long["Value"], errors="coerce").fillna(0)
    df_long = df_long.sort_values(id_cols + ["Date"])
    
    # 4) Group by IDs + Date, summing Value, and return that result
    result = (
        df_long
        .groupby(id_cols + ["Date"], dropna=False)["Value"]
        .sum()
        .reset_index()
    )

    return result

    

# Clean and normalize numeric data (handles missing values and outliers)
def auto_clean_data(df):
    df = df.copy()
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    for col in numeric_cols:
        mean = df[col].mean()
        std = df[col].std()
        df[col] = df[col].fillna(mean)
        df[col] = np.where((df[col] > mean + 3 * std) | (df[col] < mean - 3 * std), mean, df[col])

    # Normalize all numeric columns
    scaler = MinMaxScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df

# Detect frequency from datetime-like column headers using pandas + dateutil
def detect_frequency_from_columns(date_cols):
    try:
        dates = pd.to_datetime(date_cols)
        dates = dates.sort_values()
        deltas = dates.to_series().diff().dropna()
        mode_delta = deltas.mode()[0]
        seconds = mode_delta.total_seconds()

        if seconds < 60:
            return "sub-minute"
        elif seconds < 3600:
            return "minute"
        elif seconds < 86400:
            return "hourly"
        elif seconds < 604800:
            return "daily"
        elif seconds < 2628000:
            return "weekly"
        elif seconds < 31536000:
            return "monthly"
        else:
            return "yearly"
    except Exception as e:
        print(f"[WARNING] Could not detect frequency: {e}")
        return "unknown"

# Validate time series: reindex for continuity, detect missing, fill with 0
def validate_time_series(df, date_cols):
    try:
        dates = pd.to_datetime(date_cols)
        inferred_freq = pd.infer_freq(dates.sort_values()) or 'MS'
        full_range = pd.date_range(start=min(dates), end=max(dates), freq=inferred_freq)

        df = df.copy()
        df.columns = pd.to_datetime(df.columns, errors='coerce')
        df = df.reindex(columns=full_range, fill_value=0)
        return df, full_range.strftime("%Y-%m-%d").tolist()
    except Exception as e:
        print(f"[ERROR] Failed to validate time series: {e}")
        return df, date_cols

# def get_cumulative_sum(df, date_cols):
#     try:
#         df_sum = df[date_cols].copy()
#         df_sum.columns = pd.to_datetime(df_sum.columns).date
#         cumulative = df_sum.sum(axis=0).cumsum()
#         result_df = pd.DataFrame({"Date": cumulative.index, "Cumulative Value": cumulative.values})
#         return result_df
#     except Exception as e:
#         print(f"[ERROR] Could not compute cumulative sum: {e}")
#         return pd.DataFrame()

# ================= MAIN =================
# def main():
#     print("[INFO] Starting Data Preprocessing Pipeline...")
#     df = upload_dataset()
#     print(preview_dataset(df))

#     date_cols = extract_datetime_columns(df)
#     if not date_cols:
#         print("[ERROR] No datetime-like columns found.")
#         return

#     df_date_only = df[date_cols].copy()
#     df_validated, validated_date_cols = validate_time_series(df_date_only, date_cols)
#     df_cleaned = auto_clean_data(df_validated)
#     frequency = detect_frequency_from_columns(validated_date_cols)

#     print(f"\n[INFO] Detected Frequency: {frequency}")
#     print("\n[INFO] Processed Data Sample:")
#     print(preview_dataset(df_cleaned))

#     print("\n[INFO] Generating cumulative sum table...")
#     cumulative_df = get_cumulative_sum(df_cleaned, validated_date_cols)
#     print(cumulative_df)

# if __name__ == "__main__":
#     main()
