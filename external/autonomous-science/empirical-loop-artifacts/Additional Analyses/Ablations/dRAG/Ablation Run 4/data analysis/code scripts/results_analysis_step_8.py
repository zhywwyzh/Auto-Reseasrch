#!/usr/bin/env python3
"""
Domain-general covariates analysis and hierarchical regression for MRT accuracy and VVIQ2 scores.

This script performs:
1. Calculation of domain-general covariates for each participant
2. Hierarchical regression analysis for MRT accuracy and VVIQ2 total scores
3. Model comparison statistics including ΔR² and F-tests
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import re
import warnings
warnings.filterwarnings('ignore')

# Import R interface and statistical packages
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
import rpy2.robjects.numpy2ri as numpy2ri
from rpy2.robjects import conversion, default_converter
from rpy2.robjects.conversion import localconverter

# Activate pandas and numpy conversion
# pandas2ri.activate()
# numpy2ri.activate()

def get_latest_file(pattern):
    """
    Get the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/VWM_cleaned_*.csv')
        
    Returns:
    --------
    str or None
        Path to the most recent file matching the pattern, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, return most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def parse_duration_to_seconds(duration_str):
    """
    Convert duration string to seconds.
    
    Parameters:
    -----------
    duration_str : str or float
        Duration in HH:MM:SS format or numeric seconds
        
    Returns:
    --------
    float
        Duration in seconds
    """
    if pd.isna(duration_str):
        return 0.0
    
    # If already numeric, return as-is
    try:
        return float(duration_str)
    except (ValueError, TypeError):
        pass
    
    # Try to parse HH:MM:SS format
    try:
        duration_str = str(duration_str).strip()
        if ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = map(float, parts)
                return hours * 3600 + minutes * 60 + seconds
            elif len(parts) == 2:
                minutes, seconds = map(float, parts)
                return minutes * 60 + seconds
        return float(duration_str)
    except (ValueError, TypeError):
        return 0.0

def load_input_data():
    """
    Load all required input files.
    
    Returns:
    --------
    dict
        Dictionary containing loaded dataframes
    """
    print("=== LOADING INPUT DATA ===")
    
    data = {}
    
    # Load VWM cleaned data
    print("\n1. Loading VWM cleaned data...")
    vwm_pattern = "outputs/VWM_cleaned_*.csv"
    vwm_file = get_latest_file(vwm_pattern)
    if vwm_file:
        print(f"Found VWM file: {vwm_file}")
        data['vwm'] = pd.read_csv(vwm_file).rename(columns=str.strip)
        print(f"VWM data shape: {data['vwm'].shape}")
        print("VWM columns:", list(data['vwm'].columns))
        print("First 3 rows of VWM data:")
        print(data['vwm'].head(3))
        print(f"VWM excluded unique values: {data['vwm']['excluded'].unique()}")
        print(f"VWM timeout unique values: {data['vwm']['VWM_timeout'].unique()}")
    else:
        print(f"ERROR: No VWM cleaned file found matching pattern: {vwm_pattern}")
        return None
    
    # Load MRT cleaned data
    print("\n2. Loading MRT cleaned data...")
    mrt_pattern = "outputs/MRT_cleaned_*.csv"
    mrt_file = get_latest_file(mrt_pattern)
    if mrt_file:
        print(f"Found MRT file: {mrt_file}")
        data['mrt'] = pd.read_csv(mrt_file).rename(columns=str.strip)
        print(f"MRT data shape: {data['mrt'].shape}")
        print("MRT columns:", list(data['mrt'].columns))
        print("First 3 rows of MRT data:")
        print(data['mrt'].head(3))
        print(f"MRT excluded unique values: {data['mrt']['excluded'].unique()}")
        print(f"MRT timeout unique values: {data['mrt']['MRT_timeout'].unique()}")
        print(f"MRT isCorrect unique values: {data['mrt']['MRT_isCorrect'].unique()}")
    else:
        print(f"ERROR: No MRT cleaned file found matching pattern: {mrt_pattern}")
        return None
    
    # Load VVIQ2 cleaned data
    print("\n3. Loading VVIQ2 cleaned data...")
    vviq_pattern = "outputs/VVIQ2_cleaned_*.csv"
    vviq_file = get_latest_file(vviq_pattern)
    if vviq_file:
        print(f"Found VVIQ2 file: {vviq_file}")
        data['vviq'] = pd.read_csv(vviq_file).rename(columns=str.strip)
        print(f"VVIQ2 data shape: {data['vviq'].shape}")
        print("VVIQ2 columns:", list(data['vviq'].columns))
        print("First 3 rows of VVIQ2 data:")
        print(data['vviq'].head(3))
        print(f"VVIQ2 excluded unique values: {data['vviq']['excluded'].unique()}")
        print(f"VVIQ2 total_score type: {data['vviq']['total_score'].dtype}")
    else:
        print(f"ERROR: No VVIQ2 cleaned file found matching pattern: {vviq_pattern}")
        return None
    
    # Load VWM parameters data
    print("\n4. Loading VWM parameters data...")
    params_pattern = "outputs/VWM_parameters_*.csv"
    params_file = get_latest_file(params_pattern)
    if params_file:
        print(f"Found VWM parameters file: {params_file}")
        data['params'] = pd.read_csv(params_file).rename(columns=str.strip)
        print(f"VWM parameters data shape: {data['params'].shape}")
        print("VWM parameters columns:", list(data['params'].columns))
        print("First 3 rows of VWM parameters data:")
        print(data['params'].head(3))
        print(f"VWM parameters excluded unique values: {data['params']['excluded'].unique()}")
        print(f"VWM parameters kappa_concentration type: {data['params']['kappa_concentration'].dtype}")
    else:
        print(f"ERROR: No VWM parameters file found matching pattern: {params_pattern}")
        return None
    
    # Load metadata files
    print("\n5. Loading metadata files...")
    metadata_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    metadata_files = glob.glob(metadata_pattern)
    if metadata_files:
        print(f"Found {len(metadata_files)} metadata files")
        metadata_list = []
        for file in metadata_files:
            try:
                df = pd.read_csv(file).rename(columns=str.strip)
                print(f"Loaded metadata file: {file}")
                print("Metadata columns:", list(df.columns))
                print("First 3 rows of metadata:")
                print(df.head(3))
                metadata_list.append(df)
            except Exception as e:
                print(f"Error loading {file}: {e}")
        
        if metadata_list:
            data['metadata'] = pd.concat(metadata_list, ignore_index=True)
            # Ensure one summary row per participant by dropping duplicates
            data['metadata'].drop_duplicates(subset='participantId', keep='first', inplace=True)
            print(f"Combined metadata shape after deduplication: {data['metadata'].shape}")
            print(f"Metadata windowFocusLostDuringTasksNum type: {data['metadata']['windowFocusLostDuringTasksNum'].dtype}")
            print(f"Metadata windowFocusLostDuringInfoNum type: {data['metadata']['windowFocusLostDuringInfoNum'].dtype}")
        else:
            print("ERROR: No metadata files could be loaded")
            return None
    else:
        print(f"ERROR: No metadata files found matching pattern: {metadata_pattern}")
        return None
    
    print("\n=== INPUT DATA LOADING COMPLETE ===")
    return data

def calculate_domain_general_covariates(data):
    """
    Calculate domain-general covariates for each participant.
    
    Parameters:
    -----------
    data : dict
        Dictionary containing loaded dataframes
        
    Returns:
    --------
    pd.DataFrame
        DataFrame with calculated covariates per participant
    """
    print("\n=== CALCULATING DOMAIN-GENERAL COVARIATES ===")
    
    # Filter to non-excluded data
    vwm_valid = data['vwm'][data['vwm']['excluded'] == False].copy()
    mrt_valid = data['mrt'][data['mrt']['excluded'] == False].copy()
    vviq_valid = data['vviq'][data['vviq']['excluded'] == False].copy()
    params_valid = data['params'][data['params']['excluded'] == False].copy()
    
    print(f"Valid VWM trials: {len(vwm_valid)}")
    print(f"Valid MRT trials: {len(mrt_valid)}")
    print(f"Valid VVIQ participants: {len(vviq_valid)}")
    print(f"Valid parameter participants: {len(params_valid)}")
    
    # Get unique participants from each dataset
    vwm_participants = set(vwm_valid['participantId'].unique())
    mrt_participants = set(mrt_valid['participantId'].unique())
    vviq_participants = set(vviq_valid['PROLIFIC_PID'].unique())
    params_participants = set(params_valid['participantId'].unique())
    
    print(f"Unique VWM participants: {len(vwm_participants)}")
    print(f"Unique MRT participants: {len(mrt_participants)}")
    print(f"Unique VVIQ participants: {len(vviq_participants)}")
    print(f"Unique parameter participants: {len(params_participants)}")
    
    # Find common participants
    common_participants = vwm_participants & mrt_participants & vviq_participants & params_participants
    print(f"Common participants across all datasets: {len(common_participants)}")
    
    results = []
    
    for participant in common_participants:
        print(f"\nProcessing participant: {participant}")
        
        # Get participant data
        vwm_p = vwm_valid[vwm_valid['participantId'] == participant]
        mrt_p = mrt_valid[mrt_valid['participantId'] == participant]
        vviq_p = vviq_valid[vviq_valid['PROLIFIC_PID'] == participant]
        params_p = params_valid[params_valid['participantId'] == participant]
        
        # Get metadata for this participant
        metadata_p = data['metadata'][data['metadata']['participantId'] == participant]
        
        if len(metadata_p) == 0:
            print(f"No metadata found for participant {participant}, skipping")
            continue
        
        # 1. Mean VWM accuracy
        total_vwm_trials = len(vwm_p)
        vwm_timeouts = len(vwm_p[vwm_p['VWM_timeout'] == True])
        mean_vwm_accuracy = (total_vwm_trials - vwm_timeouts) / total_vwm_trials if total_vwm_trials > 0 else 0
        
        # 2. Response time coefficient of variation
        # VWM CV (excluding timeouts)
        vwm_no_timeout = vwm_p[vwm_p['VWM_timeout'] == False]
        if len(vwm_no_timeout) > 1:
            vwm_cv = vwm_no_timeout['VWM_rt_ms'].std() / vwm_no_timeout['VWM_rt_ms'].mean()
        else:
            vwm_cv = 0
        
        # MRT CV (correct trials only, no timeouts)
        mrt_correct = mrt_p[(mrt_p['MRT_isCorrect'] == True) & (mrt_p['MRT_timeout'] == False)]
        if len(mrt_correct) > 1 and 'MRT_rt_ms' in mrt_correct.columns:
            mrt_cv = mrt_correct['MRT_rt_ms'].std() / mrt_correct['MRT_rt_ms'].mean()
        else:
            mrt_cv = 0
        
        combined_rt_cv = (vwm_cv + mrt_cv) / 2
        
        # 3. Total focus loss instances
        focus_tasks = metadata_p['windowFocusLostDuringTasksNum'].iloc[0] if len(metadata_p) > 0 else 0
        focus_info = metadata_p['windowFocusLostDuringInfoNum'].iloc[0] if len(metadata_p) > 0 else 0
        total_focus_loss_instances = focus_tasks + focus_info
        
        # 4. Total focus loss duration
        if len(metadata_p) > 0:
            duration_tasks = parse_duration_to_seconds(metadata_p['windowFocusLostDuringTasksDuration'].iloc[0])
            duration_info = parse_duration_to_seconds(metadata_p['windowFocusLostDuringInfoDuration'].iloc[0])
        else:
            duration_tasks = 0
            duration_info = 0
        total_focus_loss_duration = duration_tasks + duration_info
        
        # 5. Overall timeout rate
        total_mrt_trials = len(mrt_p)
        mrt_timeouts = len(mrt_p[mrt_p['MRT_timeout'] == True])
        total_trials = total_vwm_trials + total_mrt_trials
        total_timeouts = vwm_timeouts + mrt_timeouts
        overall_timeout_rate = total_timeouts / total_trials if total_trials > 0 else 0
        
        # 6. Overall MRT accuracy
        mrt_no_timeout = mrt_p[mrt_p['MRT_timeout'] == False]
        overall_mrt_accuracy = mrt_no_timeout['MRT_isCorrect'].mean() if len(mrt_no_timeout) > 0 else 0
        
        print(f"  Mean VWM accuracy: {mean_vwm_accuracy:.4f}")
        print(f"  Combined RT CV: {combined_rt_cv:.4f}")
        print(f"  Total focus loss instances: {total_focus_loss_instances}")
        print(f"  Total focus loss duration: {total_focus_loss_duration:.2f}")
        print(f"  Overall timeout rate: {overall_timeout_rate:.4f}")
        print(f"  Overall MRT accuracy: {overall_mrt_accuracy:.4f}")
        
        results.append({
            'participantId': participant,
            'mean_vwm_accuracy': mean_vwm_accuracy,
            'combined_rt_cv': combined_rt_cv,
            'total_focus_loss_instances': total_focus_loss_instances,
            'total_focus_loss_duration_seconds': total_focus_loss_duration,
            'overall_timeout_rate': overall_timeout_rate,
            'overall_mrt_accuracy': overall_mrt_accuracy,
            'excluded': False
        })
    
    covariates_df = pd.DataFrame(results)
    print(f"\nCalculated covariates for {len(covariates_df)} participants")
    print("Covariates dataframe columns:", list(covariates_df.columns))
    print("First 2 rows of covariates:")
    print(covariates_df.head(2))
    
    return covariates_df

def prepare_regression_data(covariates_df, data):
    """
    Prepare data for hierarchical regression analysis.
    
    Parameters:
    -----------
    covariates_df : pd.DataFrame
        DataFrame with calculated covariates
    data : dict
        Dictionary containing loaded dataframes
        
    Returns:
    --------
    tuple
        (mrt_data, vviq_data) - DataFrames ready for regression analysis
    """
    print("\n=== PREPARING REGRESSION DATA ===")
    
    # Filter valid data
    vviq_valid = data['vviq'][data['vviq']['excluded'] == False].copy()
    params_valid = data['params'][data['params']['excluded'] == False].copy()
    
    # Merge covariates with VVIQ data
    vviq_merged = pd.merge(
        covariates_df,
        vviq_valid[['PROLIFIC_PID', 'total_score']],
        left_on='participantId',
        right_on='PROLIFIC_PID',
        how='inner'
    )
    
    # Merge with VWM parameters
    vviq_data = pd.merge(
        vviq_merged,
        params_valid[['participantId', 'kappa_concentration']],
        on='participantId',
        how='inner'
    )
    
    # For MRT data, we already have overall_mrt_accuracy in covariates_df
    mrt_data = pd.merge(
        covariates_df,
        params_valid[['participantId', 'kappa_concentration']],
        on='participantId',
        how='inner'
    )
    
    print(f"MRT regression data shape: {mrt_data.shape}")
    print("MRT regression data columns:", list(mrt_data.columns))
    print("First 2 rows of MRT regression data:")
    print(mrt_data.head(2))
    
    print(f"VVIQ regression data shape: {vviq_data.shape}")
    print("VVIQ regression data columns:", list(vviq_data.columns))
    print("First 2 rows of VVIQ regression data:")
    print(vviq_data.head(2))
    
    return mrt_data, vviq_data

def standardize_data(df, outcome_col, predictor_cols):
    """Standardize (z-score) outcome and predictor variables."""
    df_std = df.copy()
    df_std[outcome_col] = (df[outcome_col] - df[outcome_col].mean()) / df[outcome_col].std()
    for col in predictor_cols:
        if col in df.columns and df[col].std() > 1e-9:
            df_std[col] = (df[col] - df[col].mean()) / df[col].std()
    return df_std

def _run_regression_models(data_clean, outcome_var, block1_predictors, results_list):
    """Helper function to run hierarchical regression on both unscaled and scaled data."""
    base = importr('base')
    stats = importr('stats')

    if len(data_clean) == 0:
        print(f"ERROR: No data available for {outcome_var}")
        return

    # Check for and remove zero-variance predictors
    active_block1_preds = []
    for pred in block1_predictors:
        if pred in data_clean.columns and data_clean[pred].std() > 1e-9:
            active_block1_preds.append(pred)
        else:
            print(f"WARNING: Removing zero-variance predictor: {pred}")
    if len(active_block1_preds) == 0:
        print(f"ERROR: No valid predictors for {outcome_var}")
        return
    # Scale data for standardized coefficients
    all_predictors = active_block1_preds + ['kappa_concentration']
    data_scaled = standardize_data(data_clean, outcome_var, all_predictors)
    # Convert to R dataframes
    with localconverter(default_converter + pandas2ri.converter):
        r_data = robjects.conversion.py2rpy(data_clean)
        r_data_scaled = robjects.conversion.py2rpy(data_scaled)
    # Block 1: Domain-general covariates only
    formula1 = f"{outcome_var} ~ {' + '.join(active_block1_preds)}"
    print(f"Block 1 formula: {formula1}")
    model1 = stats.lm(formula1, data=r_data)
    model1_scaled = stats.lm(formula1, data=r_data_scaled)
    summary1 = base.summary(model1)
    summary1_scaled = base.summary(model1_scaled)
    # Block 2: Add kappa_concentration
    formula2 = f"{outcome_var} ~ {' + '.join(active_block1_preds)} + kappa_concentration"
    print(f"Block 2 formula: {formula2}")
    model2 = stats.lm(formula2, data=r_data)
    model2_scaled = stats.lm(formula2, data=r_data_scaled)
    summary2 = base.summary(model2)
    summary2_scaled = base.summary(model2_scaled)
    # Extract R-squared values
    r2_block1 = summary1.rx2('r.squared')[0]
    r2_block2 = summary2.rx2('r.squared')[0]
    adj_r2_block1 = summary1.rx2('adj.r.squared')[0]
    adj_r2_block2 = summary2.rx2('adj.r.squared')[0]
    delta_r2 = r2_block2 - r2_block1
    print(f"{outcome_var} Block 1 R²: {r2_block1:.4f}")
    print(f"{outcome_var} Block 2 R²: {r2_block2:.4f}")
    print(f"{outcome_var} ΔR²: {delta_r2:.4f}")
    # F-test for ΔR²
    anova_result = stats.anova(model1, model2)
    f_stat = anova_result.rx(2, 'F')[0]
    p_value_delta = anova_result.rx(2, 'Pr(>F)')[0]
    print(f"{outcome_var} ΔR² F-test: F = {f_stat:.4f}, p = {p_value_delta:.4f}")
    # Extract coefficients
    coef1 = summary1.rx2('coefficients')
    coef2 = summary2.rx2('coefficients')
    coef1_scaled = summary1_scaled.rx2('coefficients')
    coef2_scaled = summary2_scaled.rx2('coefficients')
    # Add Block 1 results
    for i, predictor in enumerate(['(Intercept)'] + active_block1_preds):
        if i < coef1.nrow:
            std_coef = coef1_scaled.rx(i+1, 1)[0] if predictor != '(Intercept)' else np.nan
            results_list.append({
                'outcome_variable': outcome_var,
                'block_number': 1,
                'predictor_variable': predictor,
                'coefficient': coef1.rx(i+1, 1)[0],
                'standard_error': coef1.rx(i+1, 2)[0],
                't_value': coef1.rx(i+1, 3)[0],
                'p_value': coef1.rx(i+1, 4)[0],
                'ci_lower': coef1.rx(i+1, 1)[0] - 1.96 * coef1.rx(i+1, 2)[0],
                'ci_upper': coef1.rx(i+1, 1)[0] + 1.96 * coef1.rx(i+1, 2)[0],
                'standardized_coefficient': std_coef,
                'r_squared': r2_block1,
                'adjusted_r_squared': adj_r2_block1,
                'delta_r_squared': np.nan,
                'delta_r_squared_p_value': np.nan,
                'n_participants': len(data_clean)
            })
    # Add Block 2 results
    for i, predictor in enumerate(['(Intercept)'] + active_block1_preds + ['kappa_concentration']):
        if i < coef2.nrow:
            std_coef = coef2_scaled.rx(i+1, 1)[0] if predictor != '(Intercept)' else np.nan
            delta_r2_val = delta_r2 if predictor == 'kappa_concentration' else np.nan
            delta_p_val = p_value_delta if predictor == 'kappa_concentration' else np.nan
            results_list.append({
                'outcome_variable': outcome_var,
                'block_number': 2,
                'predictor_variable': predictor,
                'coefficient': coef2.rx(i+1, 1)[0],
                'standard_error': coef2.rx(i+1, 2)[0],
                't_value': coef2.rx(i+1, 3)[0],
                'p_value': coef2.rx(i+1, 4)[0],
                'ci_lower': coef2.rx(i+1, 1)[0] - 1.96 * coef2.rx(i+1, 2)[0],
                'ci_upper': coef2.rx(i+1, 1)[0] + 1.96 * coef2.rx(i+1, 2)[0],
                'standardized_coefficient': std_coef,
                'r_squared': r2_block2,
                'adjusted_r_squared': adj_r2_block2,
                'delta_r_squared': delta_r2_val,
                'delta_r_squared_p_value': delta_p_val,
                'n_participants': len(data_clean)
            })

def run_hierarchical_regression():
    """
    Run hierarchical regression analysis using R through rpy2.
    
    Returns:
    --------
    list
        List of regression results
    """
    print("\n=== RUNNING HIERARCHICAL REGRESSION ANALYSIS ===")
    
    # Import R base and stats
    base = importr('base')
    stats = importr('stats')

    # Load input data
    data = load_input_data()
    if data is None:
        print("ERROR: Failed to load input data")
        return None
    
    # Calculate covariates
    covariates_df = calculate_domain_general_covariates(data)
    
    # Prepare regression data
    mrt_data, vviq_data = prepare_regression_data(covariates_df, data)
    
    # Remove rows with missing values
    mrt_data_clean = mrt_data.dropna()
    vviq_data_clean = vviq_data.dropna()
    
    print(f"Clean MRT data for regression: {len(mrt_data_clean)} participants")
    print(f"Clean VVIQ data for regression: {len(vviq_data_clean)} participants")
    
    # Define predictor variables for Block 1 (domain-general covariates)
    block1_predictors = [
        'mean_vwm_accuracy',
        'combined_rt_cv', 
        'total_focus_loss_instances',
        'total_focus_loss_duration_seconds',
        'overall_timeout_rate'
    ]
    
    results = []
    
    # Run regression for MRT accuracy
    print("\n--- HIERARCHICAL REGRESSION FOR MRT ACCURACY ---")
    if len(mrt_data_clean) > 10:
        _run_regression_models(mrt_data_clean, 'overall_mrt_accuracy', block1_predictors, results)

    # Run regression for VVIQ total score  
    print("\n--- HIERARCHICAL REGRESSION FOR VVIQ TOTAL SCORE ---")
    if len(vviq_data_clean) > 10:
        _run_regression_models(vviq_data_clean, 'total_score', block1_predictors, results)

    return results, covariates_df

def save_results(results, covariates_df):
    """
    Save results to output CSV files.
    
    Parameters:
    -----------
    results : list
        List of regression results
    covariates_df : pd.DataFrame
        DataFrame with calculated covariates
    """
    print("\n=== SAVING RESULTS ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save covariates
    covariates_file = f"outputs/domain_general_covariates_{timestamp}.csv"
    covariates_df.to_csv(covariates_file, index=False)
    print(f"Saved covariates to: {covariates_file}")
    print(f"Covariates file shape: {covariates_df.shape}")
    
    # Save regression results
    if results:
        results_df = pd.DataFrame(results)
        results_file = f"outputs/hierarchical_regression_results_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        print(f"Saved regression results to: {results_file}")
        print(f"Regression results file shape: {results_df.shape}")
        print("Regression results columns:", list(results_df.columns))
        print("First 2 rows of regression results:")
        print(results_df.head(2))
    else:
        print("No regression results to save")

def main():
    """
    Main execution function.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("Starting domain-general covariates analysis...")
        
        # Run hierarchical regression analysis
        results, covariates_df = run_hierarchical_regression()
        
        # Save results
        save_results(results, covariates_df)
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
