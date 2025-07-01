import pandas as pd

FREQ_MAP={
    'daily':       'D',
    'weekly':      'W',
    'monthly':     'M',
    'quarterly':   'Q',
    'yearly':      'Y'
}


def grouping_data(df, cat_col= "total_products", frequency= 'monthly'):
    
    ## get the value and date columns 
    df = df.copy()
    
    df['Date']  = pd.to_datetime(df['Date'])
    
    freq_key = frequency.lower()
    freq_code = FREQ_MAP.get(freq_key, frequency)
    
    ## code handelling
    try:
        pd.tseries.frequencies.to_offset(freq_code)
    except(ValueError, KeyError):
        allowed = list(FREQ_MAP.keys()) + ['D','W','M','Q','Y']
        raise ValueError(
            f"Invalid frequency '{frequency}'. "
            f"Use one of {allowed} (e.g. 'daily'→'D', 'monthly'→'M')."
        )
    
    group_key = [pd.Grouper(key='Date', freq= freq_code)]
    if cat_col in df.columns:
        group_key.append(cat_col)
        
    
    result = (
        df
        .groupby(group_key, dropna = False)['Value']
        .sum()
        .reset_index()
    )
    
    return result
    
    