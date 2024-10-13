from fancyimpute import KNN
import pandas as pd
import numpy as np

def knn_imputation(df, k=5):
    """
    Perform KNN imputation on the DataFrame.
    Replace missing values using K-Nearest Neighbors algorithm.
    """
    df_imputed = df.copy()
    numeric_cols = df_imputed.select_dtypes(include='number').columns
    df_imputed[numeric_cols] = pd.DataFrame(KNN(k=k).fit_transform(df_imputed[numeric_cols]), columns=numeric_cols)
    return df_imputed
