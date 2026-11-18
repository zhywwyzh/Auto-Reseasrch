#!/usr/bin/env python3
"""
VVIQ2 Robust Regression Analysis Script

This script performs robust regression analysis between VWM kappa concentration
and VVIQ2 imagery scores, including primary analysis on total scores and 
secondary analyses on subscale scores with FDR correction.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
import statsmodels.api as sm
import statsmodels.robust.norms as norms
from scipy.stats import shapiro
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.diagnostic import het_breuschpagan


def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to search for, with <TIMESTAMP> placeholder
        
    Returns:
    --------
    str or None
        Path to the most recent matching file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard pattern
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    print(f"Searching for files matching pattern: {search_pattern}")
    
    matching_files = glob.glob(search_pattern)
    print(f"Found {len(matching_files)} matching files: {matching_files}")
    
    if not matching_files:
        return None
    
    # Sort by modification time and return the most recent
    latest_file = max(matching_files, key=os.path.getmtime)
    print(f"Selected most recent file: {latest_file}")
    return latest_file

def load_and_validate_data():
    """
    Load and validate input data files.
    
    Returns:
    --------
    tuple
        (vwm_df, vviq_df) - DataFrames for VWM and VVIQ2 data
    """
    print("=== Loading and validating input data ===")
    
    # Find VWM mixture model parameters file
    vwm_pattern = "outputs/VWM_mixture_model_parameters_<TIMESTAMP>.csv"
    vwm_file = find_latest_file(vwm_pattern)
    
    if vwm_file is None:
        print(f"ERROR: No VWM mixture model parameters file found matching pattern: {vwm_pattern}")
        return None, None
    
    # Find VVIQ2 cleaned scores file
    vviq_pattern = "outputs/VVIQ2_cleaned_scores_<TIMESTAMP>.csv"
    vviq_file = find_latest_file(vviq_pattern)
    
    if vviq_file is None:
        print(f"ERROR: No VVIQ2 cleaned scores file found matching pattern: {vviq_pattern}")
        return None, None
    
    # Load VWM data
    print(f"\nLoading VWM data from: {vwm_file}")
    try:
        vwm_df = pd.read_csv(vwm_file)
        print(f"VWM data loaded successfully. Shape: {vwm_df.shape}")
        print("VWM columns:", list(vwm_df.columns))
        print("First 3 rows of VWM data:")
        print(vwm_df.head(3))
        
        # Validate required columns
        required_vwm_cols = ['participantId', 'kappa_concentration', 'model_converged', 'fit_quality_flag']
        missing_cols = [col for col in required_vwm_cols if col not in vwm_df.columns]
        if missing_cols:
            print(f"ERROR: Missing required VWM columns: {missing_cols}")
            return None, None
        
        # Print unique values for key experimental parameters
        print(f"Unique model_converged values: {vwm_df['model_converged'].unique()}")
        print(f"Unique fit_quality_flag values: {vwm_df['fit_quality_flag'].unique()}")
        print(f"kappa_concentration data type: {vwm_df['kappa_concentration'].dtype}")
        print(f"participantId data type: {vwm_df['participantId'].dtype}")
        
    except Exception as e:
        print(f"ERROR loading VWM data: {e}")
        return None, None
    
    # Load VVIQ2 data
    print(f"\nLoading VVIQ2 data from: {vviq_file}")
    try:
        vviq_df = pd.read_csv(vviq_file)
        print(f"VVIQ2 data loaded successfully. Shape: {vviq_df.shape}")
        print("VVIQ2 columns:", list(vviq_df.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq_df.head(3))
        
        # Validate required columns
        required_vviq_cols = ['PROLIFIC_PID', 'total_score', 'familiar_person_score', 
                             'sunrise_score', 'shop_front_score', 'countryside_score',
                             'driving_score', 'beach_score', 'railway_station_score', 
                             'garden_score', 'excluded']
        missing_cols = [col for col in required_vviq_cols if col not in vviq_df.columns]
        if missing_cols:
            print(f"ERROR: Missing required VVIQ2 columns: {missing_cols}")
            return None, None
        
        # Print unique values for key experimental parameters
        print(f"Unique excluded values: {vviq_df['excluded'].unique()}")
        print(f"PROLIFIC_PID data type: {vviq_df['PROLIFIC_PID'].dtype}")
        print(f"total_score data type: {vviq_df['total_score'].dtype}")
        
    except Exception as e:
        print(f"ERROR loading VVIQ2 data: {e}")
        return None, None
    
    return vwm_df, vviq_df

def merge_and_filter_data(vwm_df, vviq_df):
    """
    Merge datasets and apply filtering criteria.
    
    Parameters:
    -----------
    vwm_df : pd.DataFrame
        VWM mixture model parameters data
    vviq_df : pd.DataFrame
        VVIQ2 cleaned scores data
        
    Returns:
    --------
    pd.DataFrame
        Merged and filtered dataset ready for analysis
    """
    print("\n=== Merging and filtering data ===")
    
    print(f"Initial VWM data shape: {vwm_df.shape}")
    print(f"Initial VVIQ2 data shape: {vviq_df.shape}")
    
    # Merge datasets
    print("\nMerging datasets on participantId (VWM) and PROLIFIC_PID (VVIQ2)...")
    merged_df = pd.merge(vwm_df, vviq_df, 
                        left_on='participantId', right_on='PROLIFIC_PID', 
                        how='inner')
    print(f"Merged data shape: {merged_df.shape}")
    print("Merged data columns:", list(merged_df.columns))
    print("First 2 rows of merged data:")
    print(merged_df.head(2))
    
    # Apply filtering criteria
    print(f"\nApplying filtering criteria...")
    
    # Filter for model_converged=True
    print(f"Before model_converged filter: {len(merged_df)} participants")
    converged_mask = merged_df['model_converged'] == True
    print(f"Participants with model_converged=True: {converged_mask.sum()}")
    merged_df = merged_df[converged_mask]
    print(f"After model_converged filter: {len(merged_df)} participants")
    
    # Filter for excluded=False
    print(f"Before excluded filter: {len(merged_df)} participants")
    not_excluded_mask = merged_df['excluded'] == False
    print(f"Participants with excluded=False: {not_excluded_mask.sum()}")
    merged_df = merged_df[not_excluded_mask]
    print(f"After excluded filter: {len(merged_df)} participants")
    
    # Remove participants with missing kappa_concentration
    print(f"Before kappa_concentration filter: {len(merged_df)} participants")
    kappa_missing = merged_df['kappa_concentration'].isna().sum()
    print(f"Participants with missing kappa_concentration: {kappa_missing}")
    merged_df = merged_df.dropna(subset=['kappa_concentration'])
    print(f"After kappa_concentration filter: {len(merged_df)} participants")
    
    # Remove participants with missing VVIQ2 scores
    vviq_score_cols = ['total_score', 'familiar_person_score', 'sunrise_score', 
                      'shop_front_score', 'countryside_score', 'driving_score',
                      'beach_score', 'railway_station_score', 'garden_score']
    
    print(f"Before VVIQ2 scores filter: {len(merged_df)} participants")
    for col in vviq_score_cols:
        missing_count = merged_df[col].isna().sum()
        print(f"Participants with missing {col}: {missing_count}")
    
    merged_df = merged_df.dropna(subset=vviq_score_cols)
    print(f"After VVIQ2 scores filter: {len(merged_df)} participants")
    
    print(f"\nFinal filtered dataset shape: {merged_df.shape}")
    print("Final dataset columns:", list(merged_df.columns))
    print("First 2 rows of final dataset:")
    print(merged_df.head(2))
    
    return merged_df


def run_robust_regression(data, outcome_var, predictor_var):
    """
    Run robust regression analysis using statsmodels' RLM (Robust Linear Model).

    Parameters:
    -----------
    data : pd.DataFrame
        Dataset containing outcome and predictor variables
    outcome_var : str
        Name of outcome variable column
    predictor_var : str
        Name of predictor variable column

    Returns:
    --------
    dict
        Dictionary containing regression results
    """
    print(f"\nRunning robust regression: {outcome_var} ~ {predictor_var}")

    # Prepare data for regression
    analysis_data = data[[outcome_var, predictor_var]].copy()
    analysis_data = analysis_data.dropna()
    n_participants = len(analysis_data)

    print(f"Analysis sample size: {n_participants}")
    print(f"{outcome_var} summary stats:")
    print(analysis_data[outcome_var].describe())
    print(f"{predictor_var} summary stats:")
    print(analysis_data[predictor_var].describe())

    # Prepare design matrix
    X = sm.add_constant(analysis_data[predictor_var])
    y = analysis_data[outcome_var]

    try:
        rlm_model = sm.RLM(y, X, M=norms.HuberT())
        rlm_results = rlm_model.fit()
        estimate = rlm_results.params[predictor_var]
        std_error = rlm_results.bse[predictor_var]
        t_value = rlm_results.tvalues[predictor_var]
        p_value = rlm_results.pvalues[predictor_var]
        conf_int = rlm_results.conf_int().loc[predictor_var]
        ci_lower = conf_int[0]
        ci_upper = conf_int[1]
        residuals = rlm_results.resid
        fitted_values = rlm_results.fittedvalues

        y_mean = np.mean(y)
        ss_res = np.sum(residuals ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r_squared = 1 - (ss_res / ss_tot)
        adjusted_r_squared = 1 - ((1 - r_squared) * (n_participants - 1) / (n_participants - 2)) if n_participants > 2 else np.nan

        results = {
            'outcome_variable': outcome_var,
            'predictor': predictor_var,
            'estimate': estimate,
            'std_error': std_error,
            't_value': t_value,
            'p_value': p_value,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'R_squared': r_squared,
            'adjusted_R_squared': adjusted_r_squared,
            'n_participants': n_participants,
            'residuals': residuals,
            'fitted_values': fitted_values,
            'rlm_result': rlm_results,
            'X': X,
            'y': y
        }

        print(f"Regression completed successfully:")
        print(f"  Estimate: {estimate:.4f}")
        print(f"  Std Error: {std_error:.4f}")
        print(f"  t-value: {t_value:.4f}")
        print(f"  p-value: {p_value:.4f}")
        print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"  R²: {r_squared:.4f}")
        print(f"  Adjusted R²: {adjusted_r_squared:.4f}")

        return results

    except Exception as e:
        print(f"ERROR in robust regression: {e}")
        return None

def calculate_fdr_correction(p_values):
    """
    Apply False Discovery Rate (FDR) correction using Benjamini-Hochberg procedure.

    Parameters:
    -----------
    p_values : list
        List of p-values to correct

    Returns:
    --------
    list
        List of FDR-adjusted p-values
    """
    print(f"\nApplying FDR correction to {len(p_values)} p-values")
    print(f"Original p-values: {p_values}")

    # Use statsmodels multipletests for FDR correction
    _, adjusted_p_values, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    adjusted_p_list = list(adjusted_p_values)

    print(f"FDR-adjusted p-values: {adjusted_p_list}")

    return adjusted_p_list

def perform_model_diagnostics(regression_results):
    """
    Perform model diagnostics for robust regression.

    Parameters:
    -----------
    regression_results : dict
        Results from robust regression

    Returns:
    --------
    dict
        Dictionary containing diagnostic results
    """
    print(f"\nPerforming model diagnostics for {regression_results['outcome_variable']}")

    residuals = regression_results['residuals']
    fitted_values = regression_results['fitted_values']
    rlm_result = regression_results['rlm_result']
    X = regression_results['X']
    y = regression_results['y']

    # Calculate standardized residuals
    residual_sd = np.std(residuals)
    standardized_residuals = residuals / residual_sd if residual_sd > 0 else residuals

    # Identify outliers (|standardized residual| > 2.5)
    outliers = np.abs(standardized_residuals) > 2.5
    n_outliers = np.sum(outliers)

    print(f"Number of outliers (|std residual| > 2.5): {n_outliers}")

    # Test residual normality (Shapiro-Wilk test)
    try:
        shapiro_stat, normality_p = shapiro(residuals)
        print(f"Shapiro-Wilk normality test p-value: {normality_p:.4f}")
    except Exception as e:
        print(f"ERROR in Shapiro-Wilk test: {e}")
        normality_p = np.nan

    # Test homoscedasticity (Breusch-Pagan test)
    try:
        # For Breusch-Pagan, need OLS fit
        ols_model = sm.OLS(y, X).fit()
        bp_test = het_breuschpagan(ols_model.resid, ols_model.model.exog)
        homoscedasticity_p = bp_test[1]  # p-value
        print(f"Homoscedasticity test (Breusch-Pagan) p-value: {homoscedasticity_p:.4f}")
    except Exception as e:
        print(f"ERROR in homoscedasticity test: {e}")
        homoscedasticity_p = np.nan

    # Get robust weights range
    try:
        weights = rlm_result.weights
        weights_range = f"[{np.min(weights):.3f}, {np.max(weights):.3f}]"
        print(f"Robust weights range: {weights_range}")
    except Exception as e:
        print(f"ERROR extracting weights: {e}")
        weights_range = "NA"

    diagnostics = {
        'outcome_variable': regression_results['outcome_variable'],
        'n_outliers': n_outliers,
        'residual_normality_p': normality_p,
        'homoscedasticity_p': homoscedasticity_p,
        'model_robust_weights_range': weights_range
    }

    return diagnostics

def main():
    """
    Main function to execute the VVIQ2 robust regression analysis.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting VVIQ2 Robust Regression Analysis")
        print("=" * 50)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Load and validate data
        vwm_df, vviq_df = load_and_validate_data()
        if vwm_df is None or vviq_df is None:
            print("ERROR: Failed to load input data")
            return 1
        
        # Merge and filter data
        analysis_data = merge_and_filter_data(vwm_df, vviq_df)
        if analysis_data is None or len(analysis_data) == 0:
            print("ERROR: No valid data remaining after filtering")
            return 1
        
        # Define outcome variables
        subscale_vars = [
            'familiar_person_score', 'sunrise_score', 'shop_front_score',
            'countryside_score', 'driving_score', 'beach_score',
            'railway_station_score', 'garden_score'
        ]

        all_outcome_vars = ['total_score'] + subscale_vars
        predictor_var = 'kappa_concentration'

        # Storage for results
        regression_results = []
        diagnostic_results = []

        print("\n=== Running regression analyses ===")

        # Run regressions for all outcome variables
        for outcome_var in all_outcome_vars:
            print(f"\n--- Analyzing {outcome_var} ---")

            result = run_robust_regression(analysis_data, outcome_var, predictor_var)
            if result is None:
                print(f"ERROR: Failed to run regression for {outcome_var}")
                continue

            regression_results.append(result)

            # Perform diagnostics
            diagnostics = perform_model_diagnostics(result)
            diagnostic_results.append(diagnostics)
        
        if len(regression_results) == 0:
            print("ERROR: No successful regressions completed")
            return 1
        
        # Apply conditional FDR correction based on primary analysis significance
        print("\n=== Applying conditional FDR correction ===")

        # Find primary analysis result
        total_result = next((r for r in regression_results if r['outcome_variable'] == 'total_score'), None)

        # Initialize p_value_fdr_adjusted for all results
        for r in regression_results:
            r['p_value_fdr_adjusted'] = np.nan

        if total_result and total_result['p_value'] < 0.05:
            print(f"Primary analysis is significant (p = {total_result['p_value']:.4f} < 0.05). Applying FDR correction to subscales.")

            # Extract subscale results and apply FDR correction
            subscale_results = [r for r in regression_results if r['outcome_variable'] in subscale_vars]
            if subscale_results:
                subscale_p_values = [r['p_value'] for r in subscale_results]
                fdr_adjusted_p_values = calculate_fdr_correction(subscale_p_values)

                # Update subscale results with FDR-adjusted p-values
                for i, result in enumerate(subscale_results):
                    result['p_value_fdr_adjusted'] = fdr_adjusted_p_values[i]

            # Set primary analysis adjusted p-value to original p-value
            total_result['p_value_fdr_adjusted'] = total_result['p_value']

        else:
            if total_result:
                print(f"Primary analysis not significant (p = {total_result['p_value']:.4f} >= 0.05). Skipping FDR correction for subscales.")
                total_result['p_value_fdr_adjusted'] = total_result['p_value']
            else:
                print("Primary analysis failed. Skipping FDR correction.")
        
        # Prepare output DataFrames
        print("\n=== Preparing output files ===")
        
        # Regression results DataFrame
        results_data = []
        for result in regression_results:
            results_data.append({
                'outcome_variable': result['outcome_variable'],
                'predictor': result['predictor'],
                'estimate': result['estimate'],
                'std_error': result['std_error'],
                't_value': result['t_value'],
                'p_value': result['p_value'],
                'p_value_fdr_adjusted': result['p_value_fdr_adjusted'],
                'ci_lower': result['ci_lower'],
                'ci_upper': result['ci_upper'],
                'R_squared': result['R_squared'],
                'adjusted_R_squared': result['adjusted_R_squared'],
                'n_participants': result['n_participants']
            })
        
        results_df = pd.DataFrame(results_data)
        
        # Model diagnostics DataFrame
        diagnostics_df = pd.DataFrame(diagnostic_results)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save regression results
        results_filename = f"outputs/VVIQ2_regression_results_{timestamp}.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"Regression results saved to: {results_filename}")
        
        print("Regression results summary:")
        print(results_df)
        
        # Save model diagnostics
        diagnostics_filename = f"outputs/VVIQ2_model_diagnostics_{timestamp}.csv"
        diagnostics_df.to_csv(diagnostics_filename, index=False)
        print(f"Model diagnostics saved to: {diagnostics_filename}")
        
        print("Model diagnostics summary:")
        print(diagnostics_df)
        
        # Print final summary
        print("\n=== Analysis Summary ===")
        print(f"Total participants included in analysis: {analysis_data.shape[0]}")
        print(f"Number of regression models fitted: {len(regression_results)}")
        if total_result:
            print(f"Primary analysis (total_score): p = {total_result['p_value']:.4f}")
        else:
            print("Primary analysis failed")
        
        # Only define subscale_results if FDR correction was applied
        significant_subscales = []
        if total_result and total_result['p_value'] < 0.05:
            subscale_results = [r for r in regression_results if r['outcome_variable'] in subscale_vars]
            for result in subscale_results:
                if result['p_value_fdr_adjusted'] < 0.05:
                    significant_subscales.append(result['outcome_variable'])
        
        print(f"Significant subscales after FDR correction (α = 0.05): {len(significant_subscales)}")
        if significant_subscales:
            print(f"Significant subscales: {significant_subscales}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"CRITICAL ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
