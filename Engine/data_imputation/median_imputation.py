import pandas as pd

def median_imputation(df):
    """
    Perform median imputation on the DataFrame.
    Replace missing values with the median of the respective columns.
    """
    df_imputed = df.copy()
    for col in df_imputed.select_dtypes(include='number'):
        df_imputed[col].fillna(df_imputed[col].median(), inplace=True)
    return df_imputed
