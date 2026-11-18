#!/usr/bin/env python3
"""
MRT Regression Analysis Script

This script performs logistic and linear regression analyses on Mental Rotation Task (MRT) data
to examine the relationship between Visual Working Memory (VWM) precision (kappa) and MRT performance.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
from scipy import stats
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import warnings

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, return most recent
    return max(files, key=os.path.getmtime)

def load_input_data():
    """
    Load all required input CSV files.
    
    Returns:
    tuple: (mrt_data, vwm_params, control_vars) DataFrames
    """
    print("Loading input data files...")
    
    # Find latest files with timestamp patterns
    mrt_pattern = "outputs/mrt_cleaned_trials_*.csv"
    vwm_pattern = "outputs/vwm_mixture_parameters_*.csv"
    control_pattern = "outputs/control_variables_*.csv"
    
    mrt_file = find_latest_file(mrt_pattern)
    vwm_file = find_latest_file(vwm_pattern)
    control_file = find_latest_file(control_pattern)
    
    if not mrt_file:
        print(f"ERROR: No MRT file found matching pattern: {mrt_pattern}")
        return None, None, None
    if not vwm_file:
        print(f"ERROR: No VWM file found matching pattern: {vwm_pattern}")
        return None, None, None
    if not control_file:
        print(f"ERROR: No control file found matching pattern: {control_pattern}")
        return None, None, None
    
    print(f"Found MRT file: {mrt_file}")
    print(f"Found VWM file: {vwm_file}")
    print(f"Found control file: {control_file}")
    
    # Load MRT data
    print("\nLoading MRT cleaned trials data...")
    mrt_data = pd.read_csv(mrt_file)
    print(f"MRT data columns: {list(mrt_data.columns)}")
    print("First 3 rows of MRT data:")
    print(mrt_data.head(3))
    print(f"MRT data shape: {mrt_data.shape}")
    
    # Print unique values for key experimental design parameters
    print(f"Unique angle_degrees values: {sorted(mrt_data['angle_degrees'].unique())}")
    print(f"Unique is_correct values: {sorted(mrt_data['is_correct'].unique())}")
    print(f"Response time data type: {type(mrt_data['response_time_ms'].iloc[0])}")
    
    # Load VWM parameters
    print("\nLoading VWM mixture parameters data...")
    vwm_params = pd.read_csv(vwm_file)
    print(f"VWM parameters columns: {list(vwm_params.columns)}")
    print("First 3 rows of VWM parameters:")
    print(vwm_params.head(3))
    print(f"VWM parameters shape: {vwm_params.shape}")
    
    # Load control variables
    print("\nLoading control variables data...")
    control_vars = pd.read_csv(control_file)
    print(f"Control variables columns: {list(control_vars.columns)}")
    print("First 3 rows of control variables:")
    print(control_vars.head(3))
    print(f"Control variables shape: {control_vars.shape}")
    
    return mrt_data, vwm_params, control_vars

def prepare_mrt_data(mrt_data):
    """
    Prepare MRT data by calculating accuracy and median RT by angular disparity.
    
    Parameters:
    mrt_data (pd.DataFrame): Raw MRT trial data
    
    Returns:
    pd.DataFrame: Processed MRT performance data by participant and disparity
    """
    print("\nPreparing MRT data by angular disparity...")
    
    # Check for required columns
    required_cols = ['participant_id', 'angle_degrees', 'is_correct', 'response_time_ms']
    missing_cols = [col for col in required_cols if col not in mrt_data.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns in MRT data: {missing_cols}")
        return None
    
    # Group by participant and angle to calculate accuracy
    print("Calculating accuracy by participant and angular disparity...")
    accuracy_data = mrt_data.groupby(['participant_id', 'angle_degrees'])['is_correct'].agg(['mean', 'count']).reset_index()
    accuracy_data.columns = ['participant_id', 'angle_degrees', 'accuracy', 'trial_count']
    
    print("Accuracy data by disparity:")
    print(accuracy_data.head())
    
    # Filter to correct trials only for RT analysis
    correct_trials = mrt_data[mrt_data['is_correct'] == True].copy()
    print(f"Filtered to {len(correct_trials)} correct trials from {len(mrt_data)} total trials")
    
    # Calculate median RT for correct trials
    print("Calculating median RT for correct trials by participant and angular disparity...")
    rt_data = correct_trials.groupby(['participant_id', 'angle_degrees'])['response_time_ms'].median().reset_index()
    rt_data.columns = ['participant_id', 'angle_degrees', 'median_rt']
    
    # Apply log transformation
    rt_data['ln_rt'] = np.log(rt_data['median_rt'])
    
    print("RT data by disparity:")
    print(rt_data.head())
    
    # Merge accuracy and RT data
    performance_data = pd.merge(accuracy_data, rt_data, on=['participant_id', 'angle_degrees'], how='outer')
    
    print("Combined performance data:")
    print(performance_data.head())
    print(f"Performance data shape: {performance_data.shape}")
    
    # Pivot to wide format for easier analysis
    print("Reshaping to wide format...")
    
    # Pivot accuracy
    accuracy_wide = performance_data.pivot(index='participant_id', columns='angle_degrees', values='accuracy')
    accuracy_wide.columns = [f'accuracy_{int(col)}deg' for col in accuracy_wide.columns]
    
    # Pivot median RT
    rt_wide = performance_data.pivot(index='participant_id', columns='angle_degrees', values='median_rt')
    rt_wide.columns = [f'median_rt_{int(col)}deg' for col in rt_wide.columns]
    
    # Combine
    mrt_wide = pd.merge(accuracy_wide, rt_wide, left_index=True, right_index=True, how='outer')
    mrt_wide = mrt_wide.reset_index()
    
    print("Wide format MRT data:")
    print(f"Columns: {list(mrt_wide.columns)}")
    print("First 2 rows:")
    print(mrt_wide.head(2))
    
    return mrt_wide, performance_data

def merge_datasets(mrt_wide, vwm_params, control_vars):
    """
    Merge MRT performance data with VWM parameters and control variables.
    
    Parameters:
    mrt_wide (pd.DataFrame): Wide format MRT performance data
    vwm_params (pd.DataFrame): VWM mixture parameters
    control_vars (pd.DataFrame): Control variables
    
    Returns:
    pd.DataFrame: Merged dataset ready for analysis
    """
    print("\nMerging datasets...")
    
    # Check for required columns
    if 'von_mises_kappa' not in vwm_params.columns:
        print("ERROR: von_mises_kappa column not found in VWM parameters")
        return None
    
    required_control_cols = [
        'vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation', 
        'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate'
    ]
    missing_control_cols = [col for col in required_control_cols if col not in control_vars.columns]
    if missing_control_cols:
        print(f"ERROR: Missing required control columns: {missing_control_cols}")
        return None
    
    # Merge VWM parameters
    print("Merging with VWM parameters...")
    merged_data = pd.merge(mrt_wide, vwm_params[['participant_id', 'von_mises_kappa']], 
                          on='participant_id', how='inner')
    print(f"After VWM merge: {merged_data.shape}")
    
    # Merge control variables
    print("Merging with control variables...")
    control_cols = ['participant_id'] + required_control_cols
    merged_data = pd.merge(merged_data, control_vars[control_cols], 
                          on='participant_id', how='inner')
    print(f"After control merge: {merged_data.shape}")
    
    # Rename kappa column for clarity
    merged_data = merged_data.rename(columns={'von_mises_kappa': 'kappa'})
    
    print("Merged dataset:")
    print(f"Columns: {list(merged_data.columns)}")
    print("First 2 rows:")
    print(merged_data.head(2))
    
    # Z-standardize control variables
    print("\nZ-standardizing control variables...")
    scaler = StandardScaler()
    control_cols_to_standardize = required_control_cols
    
    for col in control_cols_to_standardize:
        if col in merged_data.columns:
            merged_data[f'{col}_z'] = scaler.fit_transform(merged_data[[col]])
            print(f"Standardized {col}: mean={merged_data[f'{col}_z'].mean():.3f}, std={merged_data[f'{col}_z'].std():.3f}")
    
    return merged_data

def calculate_vif(X):
    """
    Calculate Variance Inflation Factors for all predictors.
    
    Parameters:
    X (pd.DataFrame): Predictor variables
    
    Returns:
    pd.DataFrame: VIF values for each predictor
    """
    vif_data = pd.DataFrame()
    vif_data["Variable"] = X.columns
    vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
    return vif_data

def run_logistic_regression(data, performance_data, disparity, control_cols_z):
    """
    Run binomial GLM regression for MRT accuracy at a specific angular disparity.

    Parameters:
    data (pd.DataFrame): Merged dataset
    performance_data (pd.DataFrame): Long format performance data with accuracy and trial_count
    disparity (int): Angular disparity (0, 50, 100, 150)
    control_cols_z (list): Standardized control variable column names

    Returns:
    dict: Regression results
    """
    print(f"\nRunning binomial GLM regression for {disparity}° disparity...")

    # Filter performance data for this disparity
    disparity_perf = performance_data[performance_data['angle_degrees'] == disparity].copy()
    if len(disparity_perf) == 0:
        print(f"ERROR: No accuracy data found for {disparity}° disparity")
        return None

    # Merge with control variables and kappa
    merge_cols = ['participant_id', 'kappa'] + control_cols_z
    analysis_data = pd.merge(disparity_perf, data[merge_cols], on='participant_id', how='inner')

    # Filter out missing values
    analysis_data = analysis_data.dropna(subset=['accuracy', 'trial_count', 'kappa'] + control_cols_z)
    print(f"Analysis sample size: {len(analysis_data)}")

    if len(analysis_data) < 10:
        print(f"WARNING: Sample size too small for {disparity}° analysis")
        return None

    # Prepare predictors
    predictors = ['kappa'] + control_cols_z
    X = analysis_data[predictors]
    # Dependent variable: successes and failures
    n_success = (analysis_data['accuracy'] * analysis_data['trial_count']).round().astype(int)
    n_failures = analysis_data['trial_count'] - n_success
    y = np.column_stack([n_success, n_failures])

    # Add constant term
    X = sm.add_constant(X)

    # Calculate VIF
    vif_results = calculate_vif(X.iloc[:, 1:])  # Exclude constant
    max_vif = vif_results['VIF'].max()
    multicollinearity_flag = max_vif > 5

    print(f"VIF results for {disparity}°:")
    print(vif_results)
    print(f"Max VIF: {max_vif:.3f}, Multicollinearity flag: {multicollinearity_flag}")

    # Fit binomial GLM regression
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = sm.GLM(y, X, family=sm.families.Binomial()).fit(disp=0)

        # Extract results for kappa
        kappa_coef = model.params['kappa']
        kappa_se = model.bse['kappa']
        kappa_p = model.pvalues['kappa']

        # Model fit statistics
        # For binomial GLM, use pseudo R-squared (McFadden's)
        null_deviance = model.null_deviance
        resid_deviance = model.deviance
        r_squared = 1 - resid_deviance / null_deviance if null_deviance != 0 else np.nan

        print(f"Binomial GLM regression results for {disparity}°:")
        print(f"  Kappa coefficient: {kappa_coef:.4f}")
        print(f"  Kappa SE: {kappa_se:.4f}")
        print(f"  Kappa p-value: {kappa_p:.4f}")
        print(f"  Pseudo R-squared: {r_squared:.4f}")

        return {
            'angular_disparity': disparity,
            'kappa_coefficient': kappa_coef,
            'kappa_se': kappa_se,
            'kappa_p_value': kappa_p,
            'model_r_squared': r_squared,
            'n_participants': len(analysis_data),
            'vif_max': max_vif,
            'multicollinearity_flag': multicollinearity_flag
        }

    except Exception as e:
        print(f"ERROR in binomial GLM regression for {disparity}°: {e}")
        return None

def run_linear_regression(data, performance_data, disparity, control_cols_z):
    """
    Run linear regression for MRT reaction times at a specific angular disparity.
    
    Parameters:
    data (pd.DataFrame): Merged dataset
    performance_data (pd.DataFrame): Long format performance data with ln_rt
    disparity (int): Angular disparity (0, 50, 100, 150)
    control_cols_z (list): Standardized control variable column names
    
    Returns:
    dict: Regression results
    """
    print(f"\nRunning linear regression for {disparity}° disparity...")
    
    # Filter performance data for this disparity
    disparity_data = performance_data[performance_data['angle_degrees'] == disparity].copy()
    
    if len(disparity_data) == 0:
        print(f"ERROR: No RT data found for {disparity}° disparity")
        return None
    
    # Merge with control variables and kappa
    merge_cols = ['participant_id', 'kappa'] + control_cols_z
    rt_analysis_data = pd.merge(disparity_data, data[merge_cols], 
                               on='participant_id', how='inner')
    
    # Filter out missing values
    rt_analysis_data = rt_analysis_data.dropna(subset=['ln_rt', 'kappa'] + control_cols_z)
    print(f"RT analysis sample size: {len(rt_analysis_data)}")
    
    if len(rt_analysis_data) < 10:
        print(f"WARNING: Sample size too small for {disparity}° RT analysis")
        return None
    
    # Prepare predictors
    predictors = ['kappa'] + control_cols_z
    X = rt_analysis_data[predictors]
    y = rt_analysis_data['ln_rt']
    
    # Add constant term
    X = sm.add_constant(X)
    
    # Calculate VIF
    vif_results = calculate_vif(X.iloc[:, 1:])  # Exclude constant
    max_vif = vif_results['VIF'].max()
    multicollinearity_flag = max_vif > 5
    
    print(f"VIF results for {disparity}° RT:")
    print(vif_results)
    print(f"Max VIF: {max_vif:.3f}, Multicollinearity flag: {multicollinearity_flag}")
    
    # Fit linear regression
    try:
        model = sm.OLS(y, X).fit()
        
        # Extract results for kappa
        kappa_coef = model.params['kappa']
        kappa_se = model.bse['kappa']
        kappa_p = model.pvalues['kappa']
        r_squared = model.rsquared
        
        print(f"Linear regression results for {disparity}° RT:")
        print(f"  Kappa coefficient: {kappa_coef:.4f}")
        print(f"  Kappa SE: {kappa_se:.4f}")
        print(f"  Kappa p-value: {kappa_p:.4f}")
        print(f"  R-squared: {r_squared:.4f}")
        
        return {
            'angular_disparity': disparity,
            'kappa_coefficient': kappa_coef,
            'kappa_se': kappa_se,
            'kappa_p_value': kappa_p,
            'model_r_squared': r_squared,
            'n_participants': len(rt_analysis_data),
            'vif_max': max_vif,
            'multicollinearity_flag': multicollinearity_flag
        }
        
    except Exception as e:
        print(f"ERROR in linear regression for {disparity}° RT: {e}")
        return None

def apply_fdr_correction(accuracy_results, rt_results):
    """
    Apply False Discovery Rate correction across all model tests.
    
    Parameters:
    accuracy_results (list): List of accuracy regression results
    rt_results (list): List of RT regression results
    
    Returns:
    tuple: (accuracy_results_corrected, rt_results_corrected)
    """
    print("\nApplying FDR correction...")
    
    # Collect all p-values
    all_p_values = []
    for result in accuracy_results + rt_results:
        if result is not None:
            all_p_values.append(result['kappa_p_value'])
        else:
            all_p_values.append(np.nan)
    
    print(f"Original p-values: {all_p_values}")
    
    # Apply FDR correction
    valid_p_indices = [i for i, p in enumerate(all_p_values) if not np.isnan(p)]
    valid_p_values = [all_p_values[i] for i in valid_p_indices]
    
    if len(valid_p_values) > 0:
        _, corrected_p_values, _, _ = multipletests(valid_p_values, alpha=0.05, method='fdr_bh')
        
        # Map corrected p-values back
        corrected_all_p = [np.nan] * len(all_p_values)
        for i, idx in enumerate(valid_p_indices):
            corrected_all_p[idx] = corrected_p_values[i]
        
        print(f"FDR-corrected p-values: {corrected_all_p}")
        
        # Update results with corrected p-values
        n_accuracy = len(accuracy_results)
        
        for i, result in enumerate(accuracy_results):
            if result is not None:
                result['kappa_p_value_fdr'] = corrected_all_p[i]
        
        for i, result in enumerate(rt_results):
            if result is not None:
                result['kappa_p_value_fdr'] = corrected_all_p[n_accuracy + i]
    else:
        print("No valid p-values found for FDR correction")
        for result in accuracy_results + rt_results:
            if result is not None:
                result['kappa_p_value_fdr'] = np.nan
    
    return accuracy_results, rt_results

def save_results(accuracy_results, rt_results, merged_data, timestamp):
    """
    Save all results to CSV files.
    
    Parameters:
    accuracy_results (list): Accuracy regression results
    rt_results (list): RT regression results
    merged_data (pd.DataFrame): Merged dataset for performance summary
    timestamp (str): Timestamp for filename
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Save accuracy regression results
    if any(r is not None for r in accuracy_results):
        accuracy_df = pd.DataFrame([r for r in accuracy_results if r is not None])
        accuracy_file = f'outputs/mrt_accuracy_regression_results_{timestamp}.csv'
        accuracy_df.to_csv(accuracy_file, index=False)
        print(f"Saved accuracy regression results to: {accuracy_file}")
        print("Accuracy results:")
        print(accuracy_df)
    
    # Save RT regression results
    if any(r is not None for r in rt_results):
        rt_df = pd.DataFrame([r for r in rt_results if r is not None])
        rt_file = f'outputs/mrt_rt_regression_results_{timestamp}.csv'
        rt_df.to_csv(rt_file, index=False)
        print(f"Saved RT regression results to: {rt_file}")
        print("RT results:")
        print(rt_df)
    
    # Save performance summary
    performance_cols = [
        'participant_id', 'kappa',
        'accuracy_0deg', 'accuracy_50deg', 'accuracy_100deg', 'accuracy_150deg',
        'median_rt_0deg', 'median_rt_50deg', 'median_rt_100deg', 'median_rt_150deg',
        'vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation',
        'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate'
    ]
    
    # Select only columns that exist
    available_cols = [col for col in performance_cols if col in merged_data.columns]
    performance_summary = merged_data[available_cols].copy()
    
    performance_file = f'outputs/mrt_performance_by_disparity_{timestamp}.csv'
    performance_summary.to_csv(performance_file, index=False)
    print(f"Saved performance summary to: {performance_file}")
    print("Performance summary:")
    print(f"Columns: {list(performance_summary.columns)}")
    print("First 2 rows:")
    print(performance_summary.head(2))

def main():
    """
    Main execution function.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT regression analysis...")
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Analysis timestamp: {timestamp}")
        
        # Load input data
        mrt_data, vwm_params, control_vars = load_input_data()
        if mrt_data is None or vwm_params is None or control_vars is None:
            print("ERROR: Failed to load input data")
            return 1
        
        # Prepare MRT data
        mrt_wide, performance_data = prepare_mrt_data(mrt_data)
        if mrt_wide is None:
            print("ERROR: Failed to prepare MRT data")
            return 1
        
        # Merge datasets
        merged_data = merge_datasets(mrt_wide, vwm_params, control_vars)
        if merged_data is None:
            print("ERROR: Failed to merge datasets")
            return 1
        
        # Define standardized control variable columns
        control_cols_z = [
            'vwm_mean_accuracy_degrees_z', 'vwm_rt_coefficient_variation_z',
            'mrt_rt_coefficient_variation_z', 'engagement_index_z', 'vwm_timeout_rate_z'
        ]
        
        # Run regression analyses for each angular disparity
        disparities = [0, 50, 100, 150]
        accuracy_results = []
        rt_results = []
        
        print("\n" + "="*50)
        print("RUNNING REGRESSION ANALYSES")
        print("="*50)
        
        for disparity in disparities:
            # Logistic regression for accuracy
            acc_result = run_logistic_regression(merged_data, performance_data, disparity, control_cols_z)
            accuracy_results.append(acc_result)
            
            # Linear regression for RT
            rt_result = run_linear_regression(merged_data, performance_data, disparity, control_cols_z)
            rt_results.append(rt_result)
        
        # Apply FDR correction
        accuracy_results, rt_results = apply_fdr_correction(accuracy_results, rt_results)
        
        # Save results
        save_results(accuracy_results, rt_results, merged_data, timestamp)
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
