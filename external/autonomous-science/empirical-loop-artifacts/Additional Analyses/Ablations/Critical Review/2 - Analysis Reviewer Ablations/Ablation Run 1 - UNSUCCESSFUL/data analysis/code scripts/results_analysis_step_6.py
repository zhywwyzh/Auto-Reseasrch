#!/usr/bin/env python3
"""
Mental Rotation Task (MRT) Performance Analysis Script

This script analyzes MRT performance by angular disparity and runs regression models
to examine relationships with visual working memory precision (kappa).
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Statistical modeling imports
from scipy import stats
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import fdrcorrection
import statsmodels.api as sm
import statsmodels.formula.api as smf

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match (e.g., 'outputs/mixture_model_parameters_*.csv')
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def load_input_files():
    """
    Load all required input files with error handling.
    
    Returns:
    tuple: (mixture_params_df, control_vars_df, trial_data_df) or (None, None, None) if error
    """
    print("Loading input files...")
    
    # Find latest files matching patterns
    mixture_file = find_latest_file('outputs/mixture_model_parameters_*.csv')
    control_file = find_latest_file('outputs/control_variables_*.csv')
    trial_file = find_latest_file('outputs/cleaned_trial_data_*.csv')
    
    if not mixture_file:
        print("ERROR: No mixture model parameters file found matching pattern")
        return None, None, None
    if not control_file:
        print("ERROR: No control variables file found matching pattern")
        return None, None, None
    if not trial_file:
        print("ERROR: No cleaned trial data file found matching pattern")
        return None, None, None
        
    print(f"Found mixture model file: {mixture_file}")
    print(f"Found control variables file: {control_file}")
    print(f"Found trial data file: {trial_file}")
    
    try:
        # Load mixture model parameters
        mixture_df = pd.read_csv(mixture_file)
        print(f"Loaded mixture model parameters: {mixture_df.shape[0]} rows, {mixture_df.shape[1]} columns")
        print("Mixture model columns:", list(mixture_df.columns))
        print("First 3 rows of mixture model data:")
        print(mixture_df.head(3))
        
        # Load control variables
        control_df = pd.read_csv(control_file)
        print(f"Loaded control variables: {control_df.shape[0]} rows, {control_df.shape[1]} columns")
        print("Control variables columns:", list(control_df.columns))
        print("First 3 rows of control variables data:")
        print(control_df.head(3))
        
        # Load trial data
        trial_df = pd.read_csv(trial_file)
        print(f"Loaded trial data: {trial_df.shape[0]} rows, {trial_df.shape[1]} columns")
        print("Trial data columns:", list(trial_df.columns))
        print("First 3 rows of trial data:")
        print(trial_df.head(3))
        
        return mixture_df, control_df, trial_df
        
    except Exception as e:
        print(f"ERROR loading input files: {e}")
        return None, None, None

def validate_required_columns(df, required_cols, df_name):
    """
    Validate that required columns exist in dataframe.
    
    Parameters:
    df (pd.DataFrame): DataFrame to validate
    required_cols (list): List of required column names
    df_name (str): Name of dataframe for error reporting
    
    Returns:
    bool: True if all required columns exist, False otherwise
    """
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns in {df_name}: {missing_cols}")
        return False
    return True

def calculate_mrt_accuracy_by_disparity(trial_df):
    """
    Calculate MRT accuracy for each angular disparity.
    
    Parameters:
    trial_df (pd.DataFrame): Trial data with MRT results
    
    Returns:
    pd.DataFrame: Accuracy by participant and angular disparity
    """
    print("Calculating MRT accuracy by angular disparity...")
    
    # Filter to MRT test trials
    mrt_trials = trial_df[
        (trial_df['isPractice'] == False) & 
        (trial_df['table'] == 'mrt_test')
    ].copy()
    
    print(f"Filtered to {len(mrt_trials)} MRT test trials")
    
    # Print unique angular disparities
    print("Unique angular disparities:", sorted(mrt_trials['MRT_angle_degrees'].unique()))
    
    # Calculate accuracy for each participant and angular disparity
    accuracy_results = []
    
    participants = mrt_trials['participantId'].unique()
    disparities = [0, 50, 100, 150]
    
    print(f"Processing {len(participants)} participants across {len(disparities)} angular disparities")
    
    for participant in participants:
        participant_data = mrt_trials[mrt_trials['participantId'] == participant]
        accuracy_row = {'participantId': participant}
        
        for disparity in disparities:
            disparity_trials = participant_data[participant_data['MRT_angle_degrees'] == disparity]
            
            if len(disparity_trials) > 0:
                correct_trials = disparity_trials['MRT_isCorrect'].sum()
                total_trials = len(disparity_trials)
                accuracy = correct_trials / total_trials
                accuracy_row[f'mrt_accuracy_{disparity}deg'] = accuracy
                accuracy_row[f'mrt_total_trials_{disparity}deg'] = total_trials
            else:
                accuracy_row[f'mrt_accuracy_{disparity}deg'] = np.nan
                accuracy_row[f'mrt_total_trials_{disparity}deg'] = 0

        accuracy_results.append(accuracy_row)
    
    accuracy_df = pd.DataFrame(accuracy_results)
    print(f"Calculated accuracy for {len(accuracy_df)} participants")
    print("Accuracy data columns:", list(accuracy_df.columns))
    print("First 2 rows of accuracy data:")
    print(accuracy_df.head(2))
    
    return accuracy_df

def calculate_mrt_rt_by_disparity(trial_df):
    """
    Calculate log-transformed median reaction times for each angular disparity.
    
    Parameters:
    trial_df (pd.DataFrame): Trial data with MRT results
    
    Returns:
    pd.DataFrame: Log RT by participant and angular disparity
    """
    print("Calculating MRT reaction times by angular disparity...")
    
    # Filter to correct MRT test trials with valid RTs
    mrt_trials = trial_df[
        (trial_df['isPractice'] == False) & 
        (trial_df['table'] == 'mrt_test') &
        (trial_df['MRT_isCorrect'] == True) &
        (trial_df['MRT_rt_ms'] >= 200) &
        (trial_df['MRT_rt_ms'] <= 7000)
    ].copy()
    
    print(f"Filtered to {len(mrt_trials)} valid correct MRT trials")
    
    # Calculate median RT for each participant and angular disparity
    rt_results = []
    
    participants = mrt_trials['participantId'].unique()
    disparities = [0, 50, 100, 150]
    
    print(f"Processing {len(participants)} participants across {len(disparities)} angular disparities")
    
    for participant in participants:
        participant_data = mrt_trials[mrt_trials['participantId'] == participant]
        rt_row = {'participantId': participant}
        
        for disparity in disparities:
            disparity_trials = participant_data[participant_data['MRT_angle_degrees'] == disparity]
            
            if len(disparity_trials) > 0:
                median_rt = disparity_trials['MRT_rt_ms'].median()
                log_rt = np.log(median_rt)
                rt_row[f'mrt_log_rt_{disparity}deg'] = log_rt
            else:
                rt_row[f'mrt_log_rt_{disparity}deg'] = np.nan

        rt_results.append(rt_row)
    
    rt_df = pd.DataFrame(rt_results)
    print(f"Calculated log RT for {len(rt_df)} participants")
    print("Log RT data columns:", list(rt_df.columns))
    print("First 2 rows of log RT data:")
    print(rt_df.head(2))
    
    return rt_df

def prepare_regression_dataset(mixture_df, control_df, performance_df):
    """
    Prepare dataset for regression analysis with standardized control variables.
    
    Parameters:
    mixture_df (pd.DataFrame): Mixture model parameters
    control_df (pd.DataFrame): Control variables
    performance_df (pd.DataFrame): MRT performance data
    
    Returns:
    pd.DataFrame: Merged and standardized dataset for regression
    """
    print("Preparing regression dataset...")
    
    # Merge datasets
    regression_df = mixture_df[['participantId', 'kappa_vonmises']].copy()
    
    # Merge control variables
    control_vars = ['participantId', 'vwm_mean_accuracy_nonguess', 'vwm_rt_cv', 
                   'mrt_rt_cv', 'engagement_index', 'vwm_timeout_rate']
    regression_df = regression_df.merge(control_df[control_vars], on='participantId', how='inner')
    
    # Merge performance data (include all columns, including trial counts)
    regression_df = regression_df.merge(performance_df, on='participantId', how='inner')
    
    print(f"Merged dataset has {len(regression_df)} participants")
    
    # Z-standardize control variables
    control_to_standardize = ['vwm_mean_accuracy_nonguess', 'vwm_rt_cv', 
                             'mrt_rt_cv', 'engagement_index', 'vwm_timeout_rate']
    
    scaler = StandardScaler()
    for var in control_to_standardize:
        if var in regression_df.columns:
            regression_df[f'z_{var}'] = scaler.fit_transform(regression_df[[var]])
            print(f"Standardized {var}: mean={regression_df[f'z_{var}'].mean():.3f}, std={regression_df[f'z_{var}'].std():.3f}")
    
    print("Regression dataset columns:", list(regression_df.columns))
    print("First 2 rows of regression dataset:")
    print(regression_df.head(2))
    
    return regression_df

def run_logistic_regression_models(regression_df):
    """
    Run logistic regression models for MRT accuracy at each angular disparity.
    
    Parameters:
    regression_df (pd.DataFrame): Prepared regression dataset
    
    Returns:
    list: List of regression results dictionaries
    """
    print("Running logistic regression models for MRT accuracy...")
    
    disparities = [0, 50, 100, 150]
    control_vars = ['z_vwm_mean_accuracy_nonguess', 'z_vwm_rt_cv', 
                   'z_mrt_rt_cv', 'z_engagement_index', 'z_vwm_timeout_rate']
    
    results = []
    
    for disparity in disparities:
        print(f"\nRunning logistic regression for {disparity}° angular disparity...")
        
        outcome_var = f'mrt_accuracy_{disparity}deg'
        weights_var = f'mrt_total_trials_{disparity}deg'
        
        # Check if outcome variable exists and has valid data
        if outcome_var not in regression_df.columns or weights_var not in regression_df.columns:
            print(f"Warning: {outcome_var} or {weights_var} not found in dataset")
            continue
            
        # Prepare data for this model
        model_data = regression_df[['participantId', outcome_var, weights_var, 'kappa_vonmises'] + control_vars].dropna()
        
        if len(model_data) < 10:
            print(f"Warning: Insufficient data for {disparity}° model (n={len(model_data)})")
            continue
            
        print(f"Model data: n={len(model_data)} participants")
        
        # Prepare predictors, excluding any that are constant (zero variance)
        predictors = ['kappa_vonmises'] + control_vars
        non_constant_predictors = [p for p in predictors if model_data[p].nunique(dropna=False) > 1]
        print(f"Using {len(non_constant_predictors)} non-constant predictors: {non_constant_predictors}")
        X = model_data[non_constant_predictors]
        y = model_data[outcome_var]
        weights = model_data[weights_var]
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        try:
            # Fit logistic regression (using GLM with binomial family and trial count weights)
            model = sm.GLM(y, X_with_const, family=sm.families.Binomial(), var_weights=weights).fit()
            
            # Calculate VIF on non-constant predictors only
            vif_data = pd.DataFrame()
            vif_data["Variable"] = X.columns
            vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
            
            max_vif = vif_data["VIF"].max()
            vif_flag = max_vif > 5
            
            print(f"Model fit successful. Max VIF: {max_vif:.2f}")
            if vif_flag:
                print(f"WARNING: High multicollinearity detected (VIF > 5)")
            
            # Extract results for each non-constant predictor
            for i, pred in enumerate(non_constant_predictors):
                coef = model.params[pred]
                se = model.bse[pred]
                p_val = model.pvalues[pred]
                ci_lower, ci_upper = model.conf_int().loc[pred]
                vif_val = vif_data[vif_data["Variable"] == pred]["VIF"].iloc[0]
                
                result = {
                    'model_type': 'logistic',
                    'angular_disparity': disparity,
                    'outcome_measure': 'accuracy',
                    'predictor': pred,
                    'coefficient': coef,
                    'standard_error': se,
                    'p_value': p_val,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'vif': vif_val,
                    'r_squared': model.pseudo_rsquared() if hasattr(model, "pseudo_rsquared") else np.nan,
                    'fdr_adjusted_p': np.nan  # Will be filled later
                }
                results.append(result)
                
                print(f"  {pred}: β={coef:.4f}, SE={se:.4f}, p={p_val:.4f}")
                
        except Exception as e:
            print(f"Error fitting logistic regression for {disparity}°: {e}")
            continue
    
    return results

def run_linear_regression_models(regression_df):
    """
    Run linear regression models for log-transformed MRT reaction times.
    
    Parameters:
    regression_df (pd.DataFrame): Prepared regression dataset
    
    Returns:
    list: List of regression results dictionaries
    """
    print("Running linear regression models for MRT reaction times...")
    
    disparities = [0, 50, 100, 150]
    control_vars = ['z_vwm_mean_accuracy_nonguess', 'z_vwm_rt_cv', 
                   'z_mrt_rt_cv', 'z_engagement_index', 'z_vwm_timeout_rate']
    
    results = []
    
    for disparity in disparities:
        print(f"\nRunning linear regression for {disparity}° angular disparity...")
        
        outcome_var = f'mrt_log_rt_{disparity}deg'
        
        # Check if outcome variable exists and has valid data
        if outcome_var not in regression_df.columns:
            print(f"Warning: {outcome_var} not found in dataset")
            continue
            
        # Prepare data for this model
        model_data = regression_df[['participantId', outcome_var, 'kappa_vonmises'] + control_vars].dropna()
        
        if len(model_data) < 10:
            print(f"Warning: Insufficient data for {disparity}° model (n={len(model_data)})")
            continue
            
        print(f"Model data: n={len(model_data)} participants")
        
        # Prepare predictors, excluding any that are constant (zero variance)
        predictors = ['kappa_vonmises'] + control_vars
        non_constant_predictors = [p for p in predictors if model_data[p].nunique(dropna=False) > 1]
        print(f"Using {len(non_constant_predictors)} non-constant predictors: {non_constant_predictors}")
        X = model_data[non_constant_predictors]
        y = model_data[outcome_var]
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        try:
            # Fit linear regression
            model = sm.OLS(y, X_with_const).fit()
            
            # Calculate VIF on non-constant predictors only
            vif_data = pd.DataFrame()
            vif_data["Variable"] = X.columns
            vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
            
            max_vif = vif_data["VIF"].max()
            vif_flag = max_vif > 5
            
            print(f"Model fit successful. R²={model.rsquared:.3f}, Max VIF: {max_vif:.2f}")
            if vif_flag:
                print(f"WARNING: High multicollinearity detected (VIF > 5)")
            
            # Extract results for each non-constant predictor
            for i, pred in enumerate(non_constant_predictors):
                coef = model.params[pred]
                se = model.bse[pred]
                p_val = model.pvalues[pred]
                ci_lower, ci_upper = model.conf_int().loc[pred]
                vif_val = vif_data[vif_data["Variable"] == pred]["VIF"].iloc[0]
                
                result = {
                    'model_type': 'linear',
                    'angular_disparity': disparity,
                    'outcome_measure': 'log_rt',
                    'predictor': pred,
                    'coefficient': coef,
                    'standard_error': se,
                    'p_value': p_val,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'vif': vif_val,
                    'r_squared': model.rsquared,
                    'fdr_adjusted_p': np.nan  # Will be filled later
                }
                results.append(result)
                
                print(f"  {pred}: β={coef:.4f}, SE={se:.4f}, p={p_val:.4f}")
                
        except Exception as e:
            print(f"Error fitting linear regression for {disparity}°: {e}")
            continue
    
    return results

def apply_fdr_correction(results):
    """
    Apply False Discovery Rate correction for multiple comparisons.
    
    Parameters:
    results (list): List of regression results dictionaries
    
    Returns:
    list: Updated results with FDR-adjusted p-values
    """
    print("Applying False Discovery Rate correction...")
    
    if not results:
        print("No results to apply FDR correction.")
        return []
    
    # Convert to DataFrame for easier handling
    results_df = pd.DataFrame(results)
    
    # Find rows with valid (non-NaN) p-values
    valid_mask = results_df['p_value'].notna()
    valid_p_values = results_df.loc[valid_mask, 'p_value']
    
    if len(valid_p_values) == 0:
        print("No valid p-values found for FDR correction")
        return results
    
    # Apply FDR correction to valid p-values
    rejected, p_adjusted = fdrcorrection(valid_p_values, alpha=0.05, method='indep')
    
    # Update results with adjusted p-values
    results_df.loc[valid_mask, 'fdr_adjusted_p'] = p_adjusted
    
    print(f"Applied FDR correction to {len(valid_p_values)} valid tests")
    print(f"Number of significant results after FDR correction: {sum(rejected)}")
    
    return results_df.to_dict('records')

def save_outputs(performance_df, results):
    """
    Save output files with timestamps.
    
    Parameters:
    performance_df (pd.DataFrame): MRT performance data by disparity
    results (list): Regression results
    """
    print("Saving output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save performance data with only required columns
    required_perf_cols = ['participantId', 'mrt_accuracy_0deg', 'mrt_accuracy_50deg', 'mrt_accuracy_100deg', 'mrt_accuracy_150deg', 'mrt_log_rt_0deg', 'mrt_log_rt_50deg', 'mrt_log_rt_100deg', 'mrt_log_rt_150deg']
    performance_file = f'outputs/mrt_performance_by_disparity_{timestamp}.csv'
    performance_df[required_perf_cols].to_csv(performance_file, index=False)
    print(f"Saved performance data to: {performance_file}")
    print(f"Performance data shape: {performance_df[required_perf_cols].shape}")
    
    # Save regression results
    results_df = pd.DataFrame(results)
    results_file = f'outputs/mrt_regression_results_{timestamp}.csv'
    results_df.to_csv(results_file, index=False)
    print(f"Saved regression results to: {results_file}")
    print(f"Regression results shape: {results_df.shape}")
    
    # Print summary of results
    if len(results_df) > 0:
        print("\nRegression results summary:")
        print("First 2 rows of regression results:")
        print(results_df.head(2))
        
        # Summary by model type
        summary = results_df.groupby(['model_type', 'predictor']).agg({
            'p_value': 'min',
            'fdr_adjusted_p': 'min'
        }).round(4)
        print("\nMinimum p-values by model type and predictor:")
        print(summary)

def main():
    """
    Main execution function for MRT performance analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT Performance Analysis Script")
        print("=" * 50)
        
        # Load input files
        mixture_df, control_df, trial_df = load_input_files()
        if mixture_df is None:
            return 1
        
        # Validate required columns
        mixture_required = ['participantId', 'kappa_vonmises']
        control_required = ['participantId', 'vwm_mean_accuracy_nonguess', 'vwm_rt_cv', 
                           'mrt_rt_cv', 'engagement_index', 'vwm_timeout_rate']
        trial_required = ['participantId', 'table', 'isPractice', 'MRT_trial', 
                         'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms']
        
        if not validate_required_columns(mixture_df, mixture_required, 'mixture_model_parameters'):
            return 1
        if not validate_required_columns(control_df, control_required, 'control_variables'):
            return 1
        if not validate_required_columns(trial_df, trial_required, 'cleaned_trial_data'):
            return 1
        
        print("All required columns validated successfully")
        
        # Print unique values for key experimental design parameters
        print("\nExperimental design parameters:")
        print("Unique values in 'table':", sorted(trial_df['table'].unique()))
        print("Unique values in 'isPractice':", sorted(trial_df['isPractice'].unique()))
        print("Unique values in 'MRT_angle_degrees':", sorted(trial_df['MRT_angle_degrees'].unique()))
        print("Unique values in 'MRT_isCorrect':", sorted(trial_df['MRT_isCorrect'].unique()))
        print("MRT_rt_ms data type:", trial_df['MRT_rt_ms'].dtype)
        
        # Calculate MRT accuracy by disparity
        accuracy_df = calculate_mrt_accuracy_by_disparity(trial_df)
        
        # Calculate MRT reaction times by disparity
        rt_df = calculate_mrt_rt_by_disparity(trial_df)
        
        # Merge performance data
        performance_df = accuracy_df.merge(rt_df, on='participantId', how='outer')
        print(f"Combined performance data: {len(performance_df)} participants")
        
        # Prepare regression dataset
        regression_df = prepare_regression_dataset(mixture_df, control_df, performance_df)
        
        # Run regression models
        logistic_results = run_logistic_regression_models(regression_df)
        linear_results = run_linear_regression_models(regression_df)
        
        # Combine all results
        all_results = logistic_results + linear_results
        
        # Apply FDR correction
        all_results = apply_fdr_correction(all_results)
        
        # Save outputs
        save_outputs(performance_df, all_results)
        
        print("\n" + "=" * 50)
        print("MRT Performance Analysis completed successfully")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
