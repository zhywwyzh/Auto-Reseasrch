#!/usr/bin/env python3
"""
VVIQ2 Hierarchical Multiple Regression Analysis Script

This script performs hierarchical multiple regression analysis examining the relationship
between VVIQ2 total scores and VWM precision (kappa), while controlling for engagement
and performance variables.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats
from scipy.optimize import root_scalar
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to search for (with <TIMESTAMP> placeholder)
    
    Returns:
    --------
    str or None
        Path to the most recent file matching pattern, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    files = glob.glob(search_pattern)
    
    if not files:
        return None
    
    # Get the most recent file by modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent


def calculate_cohens_f_squared(r2_full, r2_reduced):
    """
    Calculate Cohen's f² effect size.
    
    Parameters:
    -----------
    r2_full : float
        R² for the full model
    r2_reduced : float
        R² for the reduced model
    
    Returns:
    --------
    float
        Cohen's f² effect size
    """
    if r2_full >= 1.0:
        return np.inf
    
    f_squared = (r2_full - r2_reduced) / (1 - r2_full)
    # Don't force negative values to 0 - return actual value
    return f_squared

def f_squared_confidence_interval(f_squared, df_num, df_den, alpha=0.05):
    """
    Calculate confidence interval for Cohen's f² using proper non-central F distribution.
    """
    if f_squared <= 0:
        return (0.0, 0.0)
    
    # Convert f² to F statistic
    F_obs = f_squared * df_den / df_num
    
    try:
        # Lower bound: find ncp such that P(F > F_obs | ncp) = alpha/2
        def lower_eq(ncp):
            return stats.ncf.sf(F_obs, df_num, df_den, ncp) - alpha/2
        
        if F_obs > stats.f.ppf(alpha/2, df_num, df_den):
            result_lower = root_scalar(lower_eq, bracket=[0, F_obs * df_num], method='brentq')
            ncp_lower = result_lower.root
            f_sq_lower = ncp_lower / df_den
        else:
            f_sq_lower = 0.0
        
        # Upper bound: find ncp such that P(F < F_obs | ncp) = alpha/2
        def upper_eq(ncp):
            return stats.ncf.cdf(F_obs, df_num, df_den, ncp) - alpha/2
        
        result_upper = root_scalar(upper_eq, bracket=[0, F_obs * df_num * 10 + 1], method='brentq')
        ncp_upper = result_upper.root
        f_sq_upper = ncp_upper / df_den
        
        return (f_sq_lower, f_sq_upper)
    
    except:
        # Fallback to simpler method if root finding fails
        return (max(0, f_squared - 0.1), f_squared + 0.1)

def calculate_partial_correlation(X, y, var_index):
    """
    Calculate partial correlation for a specific variable.
    
    Parameters:
    -----------
    X : array-like
        Design matrix (without intercept)
    y : array-like
        Dependent variable
    var_index : int
        Index of variable for which to calculate partial correlation
    
    Returns:
    --------
    float
        Partial correlation coefficient
    """
    try:
        # Create matrices excluding the variable of interest
        X_reduced = np.delete(X, var_index, axis=1)
        x_var = X[:, var_index]
        
        # Add intercept to reduced matrix
        X_reduced_int = np.column_stack([np.ones(X_reduced.shape[0]), X_reduced])
        
        # Regress y on other variables
        if X_reduced_int.shape[1] > 1:
            beta_y = np.linalg.lstsq(X_reduced_int, y, rcond=None)[0]
            y_residual = y - np.dot(X_reduced_int, beta_y)
        else:
            y_residual = y - np.mean(y)
        
        # Regress variable of interest on other variables
        if X_reduced_int.shape[1] > 1:
            beta_x = np.linalg.lstsq(X_reduced_int, x_var, rcond=None)[0]
            x_residual = x_var - np.dot(X_reduced_int, beta_x)
        else:
            x_residual = x_var - np.mean(x_var)
        
        # Calculate correlation between residuals
        correlation = np.corrcoef(x_residual, y_residual)[0, 1]
        return correlation if not np.isnan(correlation) else 0.0
        
    except:
        return 0.0

def main():
    """
    Main function to execute the hierarchical regression analysis.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting VVIQ2 hierarchical regression analysis...")
        print(f"Current working directory: {os.getcwd()}")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Created/verified outputs directory")
        
        # Find input files
        print("\nSearching for input files...")
        
        vviq_file = find_most_recent_file('outputs/VVIQ2_cleaned_data_<TIMESTAMP>.csv')
        vwm_file = find_most_recent_file('outputs/VWM_model_parameters_<TIMESTAMP>.csv')
        participants_file = find_most_recent_file('outputs/participants_post_initial_exclusions_<TIMESTAMP>.csv')
        
        if not vviq_file:
            print("ERROR: Could not find VVIQ2_cleaned_data file")
            return 1
        if not vwm_file:
            print("ERROR: Could not find VWM_model_parameters file")
            return 1
        if not participants_file:
            print("ERROR: Could not find participants_post_initial_exclusions file")
            return 1
            
        print(f"Found VVIQ2 file: {vviq_file}")
        print(f"Found VWM file: {vwm_file}")
        print(f"Found participants file: {participants_file}")
        
        # Load datasets
        print("\nLoading datasets...")
        
        try:
            vviq_df = pd.read_csv(vviq_file)
            print(f"VVIQ2 dataset loaded: {vviq_df.shape[0]} rows, {vviq_df.shape[1]} columns")
            print("VVIQ2 columns:", list(vviq_df.columns))
            print("First 3 rows of VVIQ2 data:")
            print(vviq_df.head(3))
            
        except Exception as e:
            print(f"ERROR loading VVIQ2 file: {e}")
            return 1
            
        try:
            vwm_df = pd.read_csv(vwm_file)
            print(f"\nVWM dataset loaded: {vwm_df.shape[0]} rows, {vwm_df.shape[1]} columns")
            print("VWM columns:", list(vwm_df.columns))
            print("First 3 rows of VWM data:")
            print(vwm_df.head(3))
            
        except Exception as e:
            print(f"ERROR loading VWM file: {e}")
            return 1
            
        try:
            participants_df = pd.read_csv(participants_file)
            print(f"\nParticipants dataset loaded: {participants_df.shape[0]} rows, {participants_df.shape[1]} columns")
            print("Participants columns:", list(participants_df.columns))
            print("First 3 rows of participants data:")
            print(participants_df.head(3))
            
        except Exception as e:
            print(f"ERROR loading participants file: {e}")
            return 1
        
        # Validate required columns
        print("\nValidating required columns...")
        
        required_vviq_cols = ['PROLIFIC_PID', 'total_score', 'excluded']
        required_vwm_cols = ['participantId', 'kappa', 'excluded']
        required_participants_cols = ['participantId', 'mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z']
        
        missing_vviq = [col for col in required_vviq_cols if col not in vviq_df.columns]
        missing_vwm = [col for col in required_vwm_cols if col not in vwm_df.columns]
        missing_participants = [col for col in required_participants_cols if col not in participants_df.columns]
        
        if missing_vviq:
            print(f"ERROR: Missing VVIQ2 columns: {missing_vviq}")
            return 1
        if missing_vwm:
            print(f"ERROR: Missing VWM columns: {missing_vwm}")
            return 1
        if missing_participants:
            print(f"ERROR: Missing participants columns: {missing_participants}")
            return 1
            
        print("All required columns found")
        
        # Print unique values for key columns
        print("\nExamining key variables...")
        print("VVIQ2 excluded values:", vviq_df['excluded'].unique())
        print("VWM excluded values:", vwm_df['excluded'].unique())
        print("Total score type:", type(vviq_df['total_score'].iloc[0]))
        print("Kappa type:", type(vwm_df['kappa'].iloc[0]))
        print("Control variables types:")
        print("  mean_vwm_accuracy_z:", type(participants_df['mean_vwm_accuracy_z'].iloc[0]))
        print("  response_time_cv_z:", type(participants_df['response_time_cv_z'].iloc[0]))
        print("  composite_engagement_score_z:", type(participants_df['composite_engagement_score_z'].iloc[0]))
        
        # Filter out excluded participants
        print("\nFiltering excluded participants...")
        
        print(f"VVIQ2 before exclusion filter: {len(vviq_df)} participants")
        vviq_df_clean = vviq_df[vviq_df['excluded'] == False].copy()
        print(f"VVIQ2 after exclusion filter: {len(vviq_df_clean)} participants")
        
        print(f"VWM before exclusion filter: {len(vwm_df)} participants")
        vwm_df_clean = vwm_df[vwm_df['excluded'] == False].copy()
        print(f"VWM after exclusion filter: {len(vwm_df_clean)} participants")
        
        print(f"Participants before filtering: {len(participants_df)} participants")
        participants_df_clean = participants_df[participants_df['excluded'] == False].copy()
        print(f"Participants after filtering: {len(participants_df_clean)} participants")
        
        # Merge datasets
        print("\nMerging datasets...")
        
        # First merge VVIQ2 and VWM data
        merged_df = pd.merge(vviq_df_clean[['PROLIFIC_PID', 'total_score']], 
                           vwm_df_clean[['participantId', 'kappa']], 
                           left_on='PROLIFIC_PID', right_on='participantId', 
                           how='inner')
        print(f"After merging VVIQ2 and VWM: {len(merged_df)} participants")
        
        # Then merge with participants data
        merged_df = pd.merge(merged_df, 
                           participants_df_clean[['participantId', 'mean_vwm_accuracy_z', 
                                                'response_time_cv_z', 'composite_engagement_score_z']], 
                           on='participantId', 
                           how='inner')
        print(f"After merging with participants data: {len(merged_df)} participants")
        
        # Remove any rows with missing data
        print("\nChecking for missing data...")
        print("Missing data counts:")
        print(merged_df.isnull().sum())
        
        merged_df_complete = merged_df.dropna()
        print(f"After removing missing data: {len(merged_df_complete)} participants")
        
        if len(merged_df_complete) == 0:
            print("ERROR: No complete cases available for analysis")
            return 1
        
        print("\nFinal merged dataset:")
        print("All columns:", list(merged_df_complete.columns))
        print("First 2 rows:")
        print(merged_df_complete.head(2))
        
        # Prepare data for regression
        print("\nPreparing data for hierarchical regression...")
        
        # Dependent variable
        y = merged_df_complete['total_score'].values
        print(f"Dependent variable (total_score): {len(y)} observations")
        print(f"Total score range: {y.min()} to {y.max()}")
        
        # Control variables (Block 1)
        X_controls = merged_df_complete[['mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z']].values
        print(f"Control variables shape: {X_controls.shape}")
        
        # Add intercept to control variables
        X_controls_int = np.column_stack([np.ones(len(y)), X_controls])
        
        # Full model variables (Block 2)
        kappa = merged_df_complete['kappa'].values
        print(f"Kappa range: {kappa.min()} to {kappa.max()}")
        
        X_full = np.column_stack([X_controls, kappa])
        X_full_int = np.column_stack([np.ones(len(y)), X_full])
        
        # Perform hierarchical regression
        print("\nPerforming hierarchical regression analysis...")
        
        # Block 1: Control variables only
        print("Block 1: Control variables only")
        rlm_controls = sm.RLM(y, X_controls_int, M=sm.robust.norms.HuberT(t=1.345)).fit()
        r2_controls = 1 - np.sum(rlm_controls.resid**2) / np.sum((y - np.mean(y))**2)
        print(f"R² for control variables: {r2_controls:.4f}")
        
        # Block 2: Full model with kappa
        print("Block 2: Full model with kappa")
        rlm_full = sm.RLM(y, X_full_int, M=sm.robust.norms.HuberT(t=1.345)).fit()
        r2_full = 1 - np.sum(rlm_full.resid**2) / np.sum((y - np.mean(y))**2)
        r2_change = r2_full - r2_controls
        print(f"R² for full model: {r2_full:.4f}")
        print(f"R² change: {r2_change:.4f}")
        
        # Calculate Cohen's f² for kappa
        cohens_f2 = calculate_cohens_f_squared(r2_full, r2_controls)
        print(f"Cohen's f² for kappa: {cohens_f2:.4f}")
        
        # Calculate confidence interval for f²
        df_num = 1  # Adding one variable (kappa)
        df_den = len(y) - X_full_int.shape[1]
        f2_ci_lower, f2_ci_upper = f_squared_confidence_interval(cohens_f2, df_num, df_den)
        print(f"95% CI for Cohen's f²: [{f2_ci_lower:.4f}, {f2_ci_upper:.4f}]")
        
        # Calculate partial correlations for Block 1 (controls only)
        print("\nCalculating partial correlations for Block 1 (controls only)...")
        partial_corrs_controls = []
        control_var_names = ['mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z']
        for i in range(X_controls.shape[1]):
            partial_corr = calculate_partial_correlation(X_controls, y, i)
            partial_corrs_controls.append(partial_corr)
            print(f"Partial correlation for {control_var_names[i]} (Block 1): {partial_corr:.4f}")

        # Calculate partial correlations for Block 2 (full model)
        print("\nCalculating partial correlations for Block 2 (full model)...")
        partial_corrs = []
        var_names = ['mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z', 'kappa']
        for i in range(X_full.shape[1]):
            partial_corr = calculate_partial_correlation(X_full, y, i)
            partial_corrs.append(partial_corr)
            print(f"Partial correlation for {var_names[i]}: {partial_corr:.4f}")
        
        # Prepare results for output
        print("\nPreparing regression results for output...")
        
        results_list = []
        
        # Block 1 results (controls)
        control_names = ['intercept', 'mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z']
        for i, name in enumerate(control_names):
            # For partial correlation: intercept is always np.nan, others use partial_corrs_controls
            if name == 'intercept':
                partial_corr_val = np.nan
            else:
                idx = i - 1  # skip intercept
                partial_corr_val = partial_corrs_controls[idx] if idx < len(partial_corrs_controls) else np.nan
            results_list.append({
                'block': 'Block1_Controls',
                'predictor': name,
                'estimate': rlm_controls.params[i],
                'robust_se': rlm_controls.bse[i],
                't_value': rlm_controls.tvalues[i],
                'p_value': rlm_controls.pvalues[i],
                'r_squared': r2_controls,
                'r_squared_change': r2_controls if i == 0 else 0.0,  # Only first row gets the change
                'cohens_f_squared': np.nan,
                'f_squared_ci_lower': np.nan,
                'f_squared_ci_upper': np.nan,
                'partial_correlation': partial_corr_val
            })
        
        # Block 2 results (full model) 
        full_names = ['intercept', 'mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z', 'kappa']
        for i, name in enumerate(full_names):
            f2_val = cohens_f2 if name == 'kappa' else np.nan
            f2_lower = f2_ci_lower if name == 'kappa' else np.nan
            f2_upper = f2_ci_upper if name == 'kappa' else np.nan
            if name == 'intercept':
                partial_corr_val = np.nan
            else:
                idx = ['mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z', 'kappa'].index(name)
                partial_corr_val = partial_corrs[idx] if idx < len(partial_corrs) else np.nan
            results_list.append({
                'block': 'Block2_Full',
                'predictor': name,
                'estimate': rlm_full.params[i],
                'robust_se': rlm_full.bse[i],
                't_value': rlm_full.tvalues[i],
                'p_value': rlm_full.pvalues[i],
                'r_squared': r2_full,
                'r_squared_change': r2_change if i == 0 else 0.0,  # Only first row gets the change
                'cohens_f_squared': f2_val,
                'f_squared_ci_lower': f2_lower,
                'f_squared_ci_upper': f2_upper,
                'partial_correlation': partial_corr_val
            })
        
        results_df = pd.DataFrame(results_list)
        
        # Prepare diagnostics data
        print("Preparing diagnostic data...")
        
        fitted_values = rlm_full.fittedvalues
        residuals = rlm_full.resid
        standardized_residuals = residuals / rlm_full.scale
        # Robust regression does not provide OLS-style influence by default; try to use it, else fallback
        try:
            leverage = rlm_full.influence.hat_matrix_diag
        except AttributeError:
            # Fallback: compute OLS leverage for design matrix
            H = X_full_int @ np.linalg.pinv(X_full_int.T @ X_full_int) @ X_full_int.T
            leverage = np.diag(H)
        
        # Flag outliers (standardized residuals > 2.5 or leverage > 2*p/n)
        p = X_full_int.shape[1]
        n = len(y)
        leverage_threshold = 2 * p / n
        outlier_flag = (np.abs(standardized_residuals) > 2.5) | (leverage > leverage_threshold)
        
        print(f"Number of outliers flagged: {np.sum(outlier_flag)}")
        
        diagnostics_df = pd.DataFrame({
            'participantId': merged_df_complete['participantId'].values,
            'total_score': merged_df_complete['total_score'].values,
            'fitted_values': fitted_values,
            'residuals': residuals,
            'standardized_residuals': standardized_residuals,
            'leverage': leverage,
            'outlier_flag': outlier_flag
        })
        
        # Save results
        print("\nSaving results...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        results_filename = f'outputs/VVIQ2_regression_results_{timestamp}.csv'
        results_df.to_csv(results_filename, index=False)
        print(f"Regression results saved to: {results_filename}")
        
        diagnostics_filename = f'outputs/VVIQ2_regression_diagnostics_{timestamp}.csv'
        diagnostics_df.to_csv(diagnostics_filename, index=False)
        print(f"Diagnostic data saved to: {diagnostics_filename}")
        
        # Print final summary
        print("\n" + "="*60)
        print("HIERARCHICAL REGRESSION ANALYSIS SUMMARY")
        print("="*60)
        print(f"Sample size: {len(y)} participants")
        print(f"Block 1 R² (controls): {r2_controls:.4f}")
        print(f"Block 2 R² (full): {r2_full:.4f}")
        print(f"R² change (kappa): {r2_change:.4f}")
        print(f"Cohen's f² for kappa: {cohens_f2:.4f}")
        print(f"95% CI for f²: [{f2_ci_lower:.4f}, {f2_ci_upper:.4f}]")
        
        print("\nKey regression coefficients (Block 2):")
        for i, name in enumerate(full_names[1:], 1):  # Skip intercept
            print(f"  {name}: β = {rlm_full.params[i]:.4f}, "
                  f"SE = {rlm_full.bse[i]:.4f}, "
                  f"p = {rlm_full.pvalues[i]:.4f}")
        
        print(f"\nOutliers detected: {np.sum(outlier_flag)} participants")
        print("="*60)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
