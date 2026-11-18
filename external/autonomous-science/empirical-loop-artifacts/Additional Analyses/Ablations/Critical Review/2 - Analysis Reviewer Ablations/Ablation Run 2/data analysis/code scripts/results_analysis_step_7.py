#!/usr/bin/env python3
"""
VVIQ2 Regression Analysis Script

This script performs multiple linear regression analyses on VVIQ2 scores using kappa_vonmises
as the primary predictor with control covariates. It includes both total score and subscale
analyses with FDR correction for multiple comparisons.
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime
from scipy import stats
from statsmodels.stats.multitest import multipletests
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings
warnings.filterwarnings('ignore')

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to search for
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    return max(files, key=os.path.getmtime)

def load_and_validate_data():
    """
    Load and validate input data files.
    
    Returns:
    tuple: (mixture_df, measures_df) or (None, None) if files not found
    """
    print("Starting data loading and validation...")
    
    # Find most recent files
    mixture_pattern = "outputs/vwm_mixture_model_parameters_*.csv"
    measures_pattern = "outputs/individual_level_measures_*.csv"
    
    mixture_file = find_most_recent_file(mixture_pattern)
    measures_file = find_most_recent_file(measures_pattern)
    
    if not mixture_file:
        print(f"ERROR: No files found matching pattern: {mixture_pattern}")
        return None, None
    if not measures_file:
        print(f"ERROR: No files found matching pattern: {measures_pattern}")
        return None, None
    
    print(f"Found mixture model file: {mixture_file}")
    print(f"Found measures file: {measures_file}")
    
    # Load files
    try:
        mixture_df = pd.read_csv(mixture_file)
        measures_df = pd.read_csv(measures_file)
        print("Successfully loaded both files")
    except Exception as e:
        print(f"ERROR loading files: {e}")
        return None, None
    
    # Print file contents for debugging
    print("\n=== MIXTURE MODEL FILE ===")
    print("Columns:", list(mixture_df.columns))
    print("First 3 rows:")
    print(mixture_df.head(3))
    print(f"Shape: {mixture_df.shape}")
    
    print("\n=== MEASURES FILE ===")
    print("Columns:", list(measures_df.columns))
    print("First 3 rows:")
    print(measures_df.head(3))
    print(f"Shape: {measures_df.shape}")
    
    # Check for required columns
    required_mixture_cols = ['participantId', 'kappa_vonmises', 'vonmises_convergence']
    required_measures_cols = [
        'participantId', 'vwm_mean_accuracy_degrees', 'vwm_rt_cv', 'mrt_rt_cv',
        'vwm_timeout_rate', 'engagement_index', 'vviq2_total_score',
        'vviq2_face_person_score', 'vviq2_nature_score', 'vviq2_shop_score',
        'vviq2_natural_env_score', 'vviq2_car_road_score', 'vviq2_beach_score',
        'vviq2_station_score', 'vviq2_garden_score'
    ]
    
    missing_mixture = [col for col in required_mixture_cols if col not in mixture_df.columns]
    missing_measures = [col for col in required_measures_cols if col not in measures_df.columns]
    
    if missing_mixture:
        print(f"ERROR: Missing columns in mixture file: {missing_mixture}")
        return None, None
    if missing_measures:
        print(f"ERROR: Missing columns in measures file: {missing_measures}")
        return None, None
    
    print("All required columns found in both files")
    
    # Print unique values for key columns
    print(f"\nUnique vonmises_convergence values: {mixture_df['vonmises_convergence'].unique()}")
    
    return mixture_df, measures_df

def merge_and_filter_data(mixture_df, measures_df):
    """
    Merge datasets and filter for convergent models.
    
    Parameters:
    mixture_df (pd.DataFrame): Mixture model parameters
    measures_df (pd.DataFrame): Individual level measures
    
    Returns:
    pd.DataFrame: Merged and filtered dataset
    """
    print("\nMerging datasets...")
    
    # Merge on participantId
    merged_df = pd.merge(mixture_df, measures_df, on='participantId', how='inner')
    print(f"After merge: {merged_df.shape[0]} participants")
    
    print(f"Convergence status breakdown:")
    print(merged_df['vonmises_convergence'].value_counts())
    
    # Filter for convergent models
    filtered_df = merged_df[merged_df['vonmises_convergence'] == True].copy()
    print(f"After filtering for convergent models: {filtered_df.shape[0]} participants")
    
    if filtered_df.shape[0] == 0:
        print("ERROR: No participants with convergent models found")
        return None
    
    # Print first 2 rows of filtered data
    print("\nFiltered dataset - First 2 rows:")
    print(filtered_df.head(2))
    
    return filtered_df

def standardize_control_variables(df):
    """
    Z-standardize control variables for regression analysis.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Dataframe with standardized variables
    """
    print("\nStandardizing control variables...")
    
    control_vars = [
        'vwm_mean_accuracy_degrees', 'vwm_rt_cv', 'mrt_rt_cv',
        'vwm_timeout_rate', 'engagement_index'
    ]
    
    df_standardized = df.copy()
    
    for var in control_vars:
        if var in df.columns:
            # Check for missing values
            missing_count = df[var].isna().sum()
            print(f"{var}: {missing_count} missing values")
            
            if missing_count < len(df):
                scaler = StandardScaler()
                df_standardized[f'z_{var}'] = scaler.fit_transform(df[[var]]).flatten()
                print(f"Standardized {var} -> z_{var}")
                print(f"  Mean: {df_standardized[f'z_{var}'].mean():.6f}")
                print(f"  Std: {df_standardized[f'z_{var}'].std():.6f}")
            else:
                print(f"WARNING: {var} has all missing values, skipping standardization")
    
    return df_standardized


def run_regression_analysis(df, outcome_var, predictors):
    """
    Run multiple linear regression analysis.
    
    Parameters:
    df (pd.DataFrame): Input data
    outcome_var (str): Dependent variable name
    predictors (list): List of predictor variable names
    
    Returns:
    dict: Regression results including coefficients, p-values, etc.
    """
    # Remove rows with missing values
    analysis_vars = [outcome_var] + predictors
    analysis_df = df[analysis_vars].dropna()
    
    if analysis_df.shape[0] == 0:
        print(f"ERROR: No complete cases for {outcome_var}")
        return None
    
    print(f"\nRunning regression for {outcome_var}")
    print(f"Complete cases: {analysis_df.shape[0]}")
    
    # Prepare data
    y = analysis_df[outcome_var]
    X = analysis_df[predictors]
    X_with_const = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X_with_const)
    results = model.fit()
    
    # Calculate VIF using statsmodels
    vif_dict = {
        col: variance_inflation_factor(X.values, i)
        for i, col in enumerate(X.columns)
    }
    
    # Extract results
    regression_results = []
    
    for i, var in enumerate(['const'] + predictors):
        if var == 'const':
            predictor_name = 'intercept'
            vif_value = np.nan
        else:
            predictor_name = var
            vif_value = vif_dict.get(var, np.nan)
        
        coef = results.params[i]
        se = results.bse[i]
        p_val = results.pvalues[i]
        ci_lower, ci_upper = results.conf_int().iloc[i]
        
        regression_results.append({
            'predictor': predictor_name,
            'coefficient': coef,
            'standard_error': se,
            'p_value': p_val,
            'confidence_interval_lower': ci_lower,
            'confidence_interval_upper': ci_upper,
            'VIF': vif_value,
            'model_r_squared': results.rsquared,
            'n_participants': analysis_df.shape[0]
        })
    
    print(f"R-squared: {results.rsquared:.4f}")
    print(f"Kappa coefficient: {results.params['kappa_vonmises']:.4f}, p-value: {results.pvalues['kappa_vonmises']:.4f}")
    
    return regression_results

def main():
    """
    Main function to execute the VVIQ2 regression analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("=== VVIQ2 REGRESSION ANALYSIS ===")
        print(f"Start time: {datetime.now()}")
        
        # Create outputs directory
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Load and validate data
        mixture_df, measures_df = load_and_validate_data()
        if mixture_df is None or measures_df is None:
            return 1
        
        # Merge and filter data
        df = merge_and_filter_data(mixture_df, measures_df)
        if df is None:
            return 1
        
        # Standardize control variables
        df = standardize_control_variables(df)
        
        # Define predictors
        control_vars = [
            'z_vwm_mean_accuracy_degrees', 'z_vwm_rt_cv', 'z_mrt_rt_cv',
            'z_vwm_timeout_rate', 'z_engagement_index'
        ]
        
        # Filter to only include standardized variables that exist
        available_controls = [var for var in control_vars if var in df.columns]
        predictors = ['kappa_vonmises'] + available_controls
        
        print(f"\nUsing predictors: {predictors}")
        
        # Primary analysis: VVIQ2 total score
        print("\n=== PRIMARY ANALYSIS: VVIQ2 TOTAL SCORE ===")
        total_results = run_regression_analysis(df, 'vviq2_total_score', predictors)
        
        if total_results is None:
            print("ERROR: Primary analysis failed")
            return 1
        
        # Save primary results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        total_results_df = pd.DataFrame(total_results)
        total_output_file = f"outputs/vviq2_total_regression_results_{timestamp}.csv"
        total_results_df.to_csv(total_output_file, index=False)
        print(f"Saved primary results to: {total_output_file}")
        
        # Secondary analyses: VVIQ2 subscales
        print("\n=== SECONDARY ANALYSES: VVIQ2 SUBSCALES ===")
        subscale_vars = [
            'vviq2_face_person_score', 'vviq2_nature_score', 'vviq2_shop_score',
            'vviq2_natural_env_score', 'vviq2_car_road_score', 'vviq2_beach_score',
            'vviq2_station_score', 'vviq2_garden_score'
        ]
        
        all_subscale_results = []
        kappa_p_values = []
        
        for subscale in subscale_vars:
            if subscale in df.columns:
                print(f"\nAnalyzing {subscale}...")
                subscale_results = run_regression_analysis(df, subscale, predictors)
                
                if subscale_results is not None:
                    for result in subscale_results:
                        result['subscale'] = subscale
                        all_subscale_results.append(result)
                    
                    # Extract kappa p-value for FDR correction
                    kappa_result = next((r for r in subscale_results if r['predictor'] == 'kappa_vonmises'), None)
                    if kappa_result:
                        kappa_p_values.append(kappa_result['p_value'])
                    else:
                        kappa_p_values.append(np.nan)
                else:
                    print(f"WARNING: Analysis failed for {subscale}")
                    kappa_p_values.append(np.nan)
            else:
                print(f"WARNING: {subscale} not found in data")
                kappa_p_values.append(np.nan)
        
        # Apply FDR correction
        print(f"\n=== APPLYING FDR CORRECTION ===")
        valid_p_values = [p for p in kappa_p_values if not np.isnan(p)]
        print(f"Number of valid p-values for FDR correction: {len(valid_p_values)}")
        
        if len(valid_p_values) > 0:
            rejected, p_adjusted, alpha_sidak, alpha_bonf = multipletests(
                valid_p_values, alpha=0.05, method='fdr_bh'
            )
            print(f"FDR-adjusted p-values: {p_adjusted}")
            # Create a map from subscale to adjusted p-value
            analyzed_subscales = [s for s, p in zip(subscale_vars, kappa_p_values) if not np.isnan(p)]
            p_adj_map = dict(zip(analyzed_subscales, p_adjusted))
        else:
            p_adjusted = []
            p_adj_map = {}

        # Add FDR-adjusted p-values to results using the map
        for result in all_subscale_results:
            if result['predictor'] == 'kappa_vonmises':
                result['p_value_fdr_adjusted'] = p_adj_map.get(result['subscale'], np.nan)
            else:
                result['p_value_fdr_adjusted'] = np.nan

        # Save subscale results
        if all_subscale_results:
            subscale_results_df = pd.DataFrame(all_subscale_results)
            # Reorder columns for clarity
            output_cols = [
                'subscale', 'predictor', 'coefficient', 'standard_error', 'p_value',
                'p_value_fdr_adjusted', 'confidence_interval_lower',
                'confidence_interval_upper', 'VIF', 'model_r_squared', 'n_participants'
            ]
            subscale_results_df = subscale_results_df[output_cols]
            subscale_output_file = f"outputs/vviq2_subscale_regression_results_{timestamp}.csv"
            subscale_results_df.to_csv(subscale_output_file, index=False)
            print(f"Saved subscale results to: {subscale_output_file}")
            
            print("\nSubscale results summary:")
            print(subscale_results_df.head(2))
        else:
            print("WARNING: No subscale results to save")
        
        print(f"\nEnd time: {datetime.now()}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
