from .mean_imputation import mean_imputation
from .median_imputation import median_imputation
from .mode_imputation import mode_imputation
from .knn_imputation import knn_imputation
#from .linear_regression_imputation import linear_regression_imputation

def evaluate_imputation(df_original, df_imputed):
    """
    A simple evaluation criterion:
    Measure the number of filled missing values and return a score.
    The more missing values filled, the better the score.
    """
    original_nulls = df_original.isnull().sum().sum()
    imputed_nulls = df_imputed.isnull().sum().sum()

    # The score is the reduction in missing values.
    score = original_nulls - imputed_nulls
    return score

def run_all_imputations(df):
    """
    Run all imputation techniques and return the best imputed DataFrame.
    """
    techniques = {
        "mean_imputation": mean_imputation,
        "median_imputation": median_imputation,
        "mode_imputation": mode_imputation,
        "knn_imputation": knn_imputation,
        #"linear_regression_imputation": linear_regression_imputation  # Add linear regression imputation
    }

    best_score = -float('inf')
    best_method = None
    best_imputed_df = None

    for name, technique in techniques.items():
        try:
            imputed_df = technique(df)
            score = evaluate_imputation(df, imputed_df)
            print(f"Technique: {name}, Score: {score}")
            
            if score > best_score:
                best_score = score
                best_method = name
                best_imputed_df = imputed_df
        except Exception as e:
            print(f"Error applying {name}: {e}")
    
    print(f"Best imputation method: {best_method} with score: {best_score}")
    return best_imputed_df, best_method
