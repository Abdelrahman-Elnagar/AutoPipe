import pandas as pd

def mode_imputation(df):
    """
    Perform mode imputation on the DataFrame.
    Replace missing values with the mode of the respective columns.
    """
    df_imputed = df.copy()
    for col in df_imputed.columns:
        df_imputed[col].fillna(df_imputed[col].mode()[0], inplace=True)
    return df_imputed
