import pandas as pd

def mean_imputation(df):
    """
    Perform mean imputation on the DataFrame.
    Replace missing values with the mean of the respective columns.
    """
    df_imputed = df.copy()
    for col in df_imputed.select_dtypes(include='number'):
        df_imputed[col].fillna(df_imputed[col].mean(), inplace=True)
    return df_imputed
