#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import glob
import re
from datetime import datetime
import sys
import statsmodels.api as sm
from statsmodels.robust.robust_linear_model import RLM

def create_output_directory():
    """
    Create the outputs directory if it doesn't exist.
    
    Returns:
        None
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created 'outputs' directory")

def find_latest_file(pattern):
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
    
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def extract_numeric_score(response_text):
    """
    Extract numeric score from VVIQ2 response text by taking the last digit.
    
    Parameters:
        response_text (str): Text response containing numeric score
        
    Returns:
        int or None: Extracted score (1-5) or None if invalid
    """
    if pd.isna(response_text) or response_text == '':
        return None
    
    # Convert to string and find last digit
    text_str = str(response_text).strip()
    digits = re.findall(r'\d', text_str)
    
    if not digits:
        return None
    
    last_digit = int(digits[-1])
    
    # Validate score is between 1-5
    if 1 <= last_digit <= 5:
        return last_digit
    else:
        return None

def process_vviq2_data(vviq2_file):
    """
    Process VVIQ2 questionnaire data to extract numeric scores and calculate totals.
    
    Parameters:
        vviq2_file (str): Path to VVIQ2 CSV file
        
    Returns:
        pd.DataFrame: Processed VVIQ2 data with participant IDs, total scores, and exclusion flags
    """
    print(f"Reading VVIQ2 data from: {vviq2_file}")
    
    # Read the CSV file
    vviq2_df = pd.read_csv(vviq2_file)
    
    # Strip whitespace from column names to fix matching issues
    vviq2_df.columns = vviq2_df.columns.str.strip()
    
    print(f"VVIQ2 data shape: {vviq2_df.shape}")
    print("VVIQ2 columns:")
    print(list(vviq2_df.columns))
    print("\nFirst 3 rows of VVIQ2 data:")
    print(vviq2_df.head(3))
    
    # Define the VVIQ2 item columns
    vviq2_items = [
        'The exact contour of face, head, shoulders and body.',
        'Characteristic poses of head, attitudes of body etc.',
        'The precise carriage, length of step, etc. in walking.',
        'The different colours worn in some familiar clothes.',
        'The sun is rising above the horizon into a hazy sky.',
        'The sky clears and surrounds the sun with blueness.',
        'Clouds. A storm blows up, with flashes of lightening.',
        'A rainbow appears.',
        'The overall appearance of the shop from the opposite side of the road.',
        'A window display including colours, shape and details of individual items for sale.',
        'You are near the entrance. The colour, shape and details of the door.',
        'You enter the shop and go to the counter. The counter assistant serves you. Money changes hands.',
        'The contours of the landscape.',
        'The colour and shape of the trees.',
        'The colour and shape of the lake.',
        'A strong wind blows on the tree and on the lake causing waves.',
        'You observe the heavy traffic travelling at maximum speed around your car. The overall appearance of vehicles, their colours, sizes and shapes.',
        'Your car accelerates to overtake the traffic directly in front of you. You see and urgent expression on the face of the driver and the people in the other vehicles as you pass.',
        'A large truck is flashing its headlight directly behind. Your car quickly moves over to let the truck pass. The driver signals with a friendly wave.',
        'You see a broken-down vehicle beside the road. Its lights are flashing. The driver is looking concerned and she is using a mobile phone.',
        'The overall appearance and colour of the water, surf, and sky.',
        'Bathers are swimming and splashing about in the water. Some are playing with a brightly coloured beach ball.',
        'An ocean liner crosses the horizon. It leaves a trail of smoke in the blue sky.',
        'A beautiful air balloon appears with four people aboard. The balloon drifts past you, almost directly overhead. The passengers wave and smile. You wave and smile back at them.',
        'The overall appearance of the station viewed from in front of the main entrance.',
        'You walk into the station. The colour, shape and details of the entrance hall.',
        'You approach the ticket office, go to a vacant counter and purchase your ticket.',
        'You walk to the platform and observe other passengers and the railway lines. A train arrives. You climb aboard.',
        'The overall appearance and design of the garden.',
        'The colour and shape of the bushes and shrubs.',
        'The colour and appearance of the flowers.',
        'Some birds fly down onto the lawn and start pecking for food.'
    ]
    
    print(f"\nExpected 32 VVIQ2 items, found {len(vviq2_items)} in specification")
    
    # Check which columns are missing (AFTER stripping)
    missing_items = []
    for item in vviq2_items:
        if item not in vviq2_df.columns:
            missing_items.append(item)
    
    if missing_items:
        print(f"Warning: {len(missing_items)} VVIQ2 item columns are missing from the data")
        for item in missing_items[:5]:  # Show first 5 missing
            print(f"  - {item}")
        if len(missing_items) > 5:
            print(f"  ... and {len(missing_items) - 5} more")
    
    # Use only available items (AFTER stripping)
    available_items = [item for item in vviq2_items if item in vviq2_df.columns]
    print(f"Using {len(available_items)} available VVIQ2 items")
    
    # Validation: Ensure all 32 items are present
    if len(available_items) != 32:
        print(f"Error: Found {len(available_items)} out of 32 required VVIQ2 items. Cannot proceed with analysis.")
        print("This indicates data quality issues or column name mismatches.")
        return None
    
    # Process each participant
    processed_data = []
    
    for idx, row in vviq2_df.iterrows():
        participant_id = row['PROLIFIC_PID']
        
        # Extract scores for all available items
        scores = []
        missing_count = 0
        
        for item in available_items:
            score = extract_numeric_score(row[item])
            if score is not None:
                scores.append(score)
            else:
                missing_count += 1
        
        # Calculate total score (only if we have some valid scores)
        if scores:
            vviq2_total = sum(scores)
        else:
            vviq2_total = None
        
        # Determine if participant should be excluded (>3 missing responses = >9.375% missing)
        excluded_incomplete = missing_count > 3
        
        processed_data.append({
            'participantId': participant_id,
            'vviq2_total_score': vviq2_total,
            'n_missing_items': missing_count,
            'excluded_incomplete_vviq2': excluded_incomplete
        })
    
    processed_df = pd.DataFrame(processed_data)
    
    print(f"\nVVIQ2 processing summary:")
    print(f"Total participants: {len(processed_df)}")
    print(f"Participants with >3 missing responses: {processed_df['excluded_incomplete_vviq2'].sum()}")
    print(f"Valid VVIQ2 total scores: {processed_df['vviq2_total_score'].notna().sum()}")
    
    if processed_df['vviq2_total_score'].notna().sum() > 0:
        valid_scores = processed_df[processed_df['vviq2_total_score'].notna()]['vviq2_total_score']
        print(f"VVIQ2 total score range: {valid_scores.min()} - {valid_scores.max()}")
        print(f"VVIQ2 total score mean: {valid_scores.mean():.2f}")
    
    return processed_df

def load_vwm_data():
    """
    Load VWM mixture model parameters from the most recent file.
    
    Returns:
        pd.DataFrame: VWM data with participant IDs and model parameters
    """
    # Find the most recent VWM file
    vwm_pattern = 'outputs/vwm_mixture_model_parameters_*.csv'
    vwm_file = find_latest_file(vwm_pattern)
    
    if vwm_file is None:
        print(f"Error: No VWM mixture model parameter files found matching pattern: {vwm_pattern}")
        return None
    
    print(f"Reading VWM data from: {vwm_file}")
    
    vwm_df = pd.read_csv(vwm_file)
    
    print(f"VWM data shape: {vwm_df.shape}")
    print("VWM columns:")
    print(list(vwm_df.columns))
    print("\nFirst 3 rows of VWM data:")
    print(vwm_df.head(3))
    
    # Check for required columns
    required_cols = ['participantId', 'kappa_concentration', 'convergence_successful', 'fit_quality_flag']
    missing_cols = [col for col in required_cols if col not in vwm_df.columns]
    
    if missing_cols:
        print(f"Error: Missing required columns in VWM data: {missing_cols}")
        return None
    
    print(f"\nVWM data unique values for key columns:")
    print(f"convergence_successful: {sorted(vwm_df['convergence_successful'].unique())}")
    print(f"fit_quality_flag: {sorted(vwm_df['fit_quality_flag'].unique())}")
    print(f"kappa_concentration type: {vwm_df['kappa_concentration'].dtype}")
    
    return vwm_df

def load_behavioral_control_data():
    """
    Load behavioral control metrics from the most recent file.
    
    Returns:
        pd.DataFrame: Behavioral control data
    """
    # Find the most recent behavioral control file
    control_pattern = 'outputs/behavioral_control_metrics_*.csv'
    control_file = find_latest_file(control_pattern)
    
    if control_file is None:
        print(f"Error: No behavioral control files found matching pattern: {control_pattern}")
        return None
    
    print(f"Reading behavioral control data from: {control_file}")
    
    control_df = pd.read_csv(control_file)
    
    print(f"Behavioral control data shape: {control_df.shape}")
    print("Behavioral control columns:")
    print(list(control_df.columns))
    print("\nFirst 3 rows of behavioral control data:")
    print(control_df.head(3))
    
    # Check for required columns
    required_cols = ['participantId', 'mean_vwm_absolute_error', 'mrt_rt_coefficient_variation', 
                     'focus_loss_instances_total', 'focus_loss_duration_seconds_total', 'task_order_condition']
    missing_cols = [col for col in required_cols if col not in control_df.columns]
    
    if missing_cols:
        print(f"Error: Missing required columns in behavioral control data: {missing_cols}")
        return None
    
    print(f"\nBehavioral control data unique values for key columns:")
    print(f"task_order_condition: {sorted(control_df['task_order_condition'].unique())}")
    print(f"mean_vwm_absolute_error type: {control_df['mean_vwm_absolute_error'].dtype}")
    print(f"mrt_rt_coefficient_variation type: {control_df['mrt_rt_coefficient_variation'].dtype}")
    print(f"focus_loss_instances_total type: {control_df['focus_loss_instances_total'].dtype}")
    print(f"focus_loss_duration_seconds_total type: {control_df['focus_loss_duration_seconds_total'].dtype}")
    
    return control_df

def merge_datasets(vviq2_df, vwm_df, control_df):
    """
    Merge VVIQ2, VWM, and behavioral control datasets.
    
    Parameters:
        vviq2_df (pd.DataFrame): Processed VVIQ2 data
        vwm_df (pd.DataFrame): VWM mixture model parameters
        control_df (pd.DataFrame): Behavioral control metrics
        
    Returns:
        pd.DataFrame: Merged analysis dataset
    """
    print("\nMerging datasets...")
    
    # Filter VWM data for successful convergence and good fit quality
    print(f"VWM data before filtering: {len(vwm_df)} participants")
    vwm_filtered = vwm_df[
        (vwm_df['convergence_successful'] == True) & 
        (vwm_df['fit_quality_flag'] == True)
    ].copy()
    print(f"VWM data after filtering: {len(vwm_filtered)} participants")
    print(f"Excluded due to convergence_successful=False: {(vwm_df['convergence_successful'] == False).sum()}")
    print(f"Excluded due to fit_quality_flag=False: {(vwm_df['fit_quality_flag'] == False).sum()}")
    
    # Filter VVIQ2 data for complete responses
    print(f"VVIQ2 data before filtering: {len(vviq2_df)} participants")
    vviq2_filtered = vviq2_df[vviq2_df['excluded_incomplete_vviq2'] == False].copy()
    print(f"VVIQ2 data after filtering: {len(vviq2_filtered)} participants")
    print(f"Excluded due to incomplete VVIQ2: {(vviq2_df['excluded_incomplete_vviq2'] == True).sum()}")
    
    # Merge datasets
    # First merge VVIQ2 with VWM
    merged_df = pd.merge(vviq2_filtered, vwm_filtered, on='participantId', how='inner')
    print(f"After merging VVIQ2 and VWM: {len(merged_df)} participants")
    
    # Then merge with behavioral controls
    merged_df = pd.merge(merged_df, control_df, on='participantId', how='inner')
    print(f"After merging with behavioral controls: {len(merged_df)} participants")
    
    print("\nMerged dataset columns:")
    print(list(merged_df.columns))
    print("\nFirst 2 rows of merged dataset:")
    print(merged_df.head(2))
    
    # Check for missing values in key variables
    key_vars = ['vviq2_total_score', 'kappa_concentration', 'mean_vwm_absolute_error', 
                'mrt_rt_coefficient_variation', 'focus_loss_instances_total', 
                'focus_loss_duration_seconds_total', 'task_order_condition']
    
    print(f"\nMissing values in key variables:")
    for var in key_vars:
        if var in merged_df.columns:
            missing = merged_df[var].isna().sum()
            print(f"{var}: {missing} missing")
    
    return merged_df

def run_robust_regression(merged_df):
    """
    Run robust regression models to analyze the relationship between VVIQ2 and VWM concentration.
    
    Parameters:
        merged_df (pd.DataFrame): Merged analysis dataset
        
    Returns:
        list: List of model results dictionaries
    """
    print("\nRunning robust regression analyses...")
    
    # Remove any rows with missing values in key variables
    analysis_vars = ['vviq2_total_score', 'kappa_concentration', 'task_order_condition']
    analysis_df = merged_df[analysis_vars].dropna()
    
    print(f"Analysis dataset size: {len(analysis_df)} participants")
    
    if len(analysis_df) < 10:
        print("Error: Insufficient data for regression analysis")
        return []
    
    # Prepare results list
    results_list = []
    
    # Model 1: Primary model with task order control
    print("\nRunning primary robust regression model...")
    
    # Prepare data for primary model - fix data type issues
    y = analysis_df['vviq2_total_score']
    X_primary = analysis_df[['kappa_concentration']].copy()
    X_primary['task_order_VWM_first'] = (analysis_df['task_order_condition'] == 'VWM_first').astype(int)
    X_primary = sm.add_constant(X_primary).astype(float)
    
    print(f"Primary model predictors: {list(X_primary.columns)}")
    
    # Fit robust regression
    try:
        rlm_primary = RLM(y, X_primary, M=sm.robust.norms.HuberT())
        rlm_primary_fit = rlm_primary.fit()
        
        print("Primary model fitted successfully")
        print(f"Primary model scale: {rlm_primary_fit.scale}")
        print(f"Primary model observations: {rlm_primary_fit.nobs}")
        
        # Extract results
        for var_name in X_primary.columns:
            coef = rlm_primary_fit.params[var_name]
            se = rlm_primary_fit.bse[var_name]
            t_stat = rlm_primary_fit.tvalues[var_name]
            p_val = rlm_primary_fit.pvalues[var_name]
            conf_int = rlm_primary_fit.conf_int(alpha=0.05).loc[var_name]
            
            results_list.append({
                'model_name': 'primary_model',
                'variable_name': var_name,
                'coefficient': coef,
                'robust_standard_error': se,
                't_statistic': t_stat,
                'p_value': p_val,
                'conf_int_lower': conf_int[0],
                'conf_int_upper': conf_int[1],
                'model_scale': rlm_primary_fit.scale,
                'n_observations': int(rlm_primary_fit.nobs)
            })
        
    except Exception as e:
        print(f"Error fitting primary model: {e}")
    
    # Model 2: Full model with all controls
    print("\nRunning full robust regression model with controls...")
    
    # Prepare data for full model (mean_vwm_absolute_error removed to address multicollinearity)
    control_vars = ['kappa_concentration', 'mrt_rt_coefficient_variation',
                    'focus_loss_instances_total', 'task_order_condition']
    
    # Check which control variables are available
    available_controls = [var for var in control_vars if var in merged_df.columns]
    print(f"Available control variables: {available_controls}")
    
    if len(available_controls) >= 2:  # Need at least kappa_concentration and one other variable
        full_analysis_df = merged_df[['vviq2_total_score'] + available_controls].dropna()
        
        print(f"Full model dataset size: {len(full_analysis_df)} participants")
        
        if len(full_analysis_df) >= 10:
            y_full = full_analysis_df['vviq2_total_score']
            # All except task_order_condition
            X_full = full_analysis_df[available_controls[:-1]].copy()
            X_full['task_order_VWM_first'] = (full_analysis_df['task_order_condition'] == 'VWM_first').astype(int)
            X_full = sm.add_constant(X_full).astype(float)
            
            print(f"Full model predictors: {list(X_full.columns)}")
            
            try:
                # To address numerical instability, use a robust fit and check for warnings/errors
                rlm_full = RLM(y_full, X_full, M=sm.robust.norms.HuberT())
                rlm_full_fit = rlm_full.fit()
                
                print("Full model fitted successfully")
                print(f"Full model scale: {rlm_full_fit.scale}")
                print(f"Full model observations: {rlm_full_fit.nobs}")
                
                # Extract results
                for var_name in X_full.columns:
                    coef = rlm_full_fit.params[var_name]
                    se = rlm_full_fit.bse[var_name]
                    t_stat = rlm_full_fit.tvalues[var_name]
                    p_val = rlm_full_fit.pvalues[var_name]
                    conf_int = rlm_full_fit.conf_int(alpha=0.05).loc[var_name]
                    
                    results_list.append({
                        'model_name': 'full_model',
                        'variable_name': var_name,
                        'coefficient': coef,
                        'robust_standard_error': se,
                        't_statistic': t_stat,
                        'p_value': p_val,
                        'conf_int_lower': conf_int[0],
                        'conf_int_upper': conf_int[1],
                        'model_scale': rlm_full_fit.scale,
                        'n_observations': int(rlm_full_fit.nobs)
                    })
                
            except Exception as e:
                print(f"Error fitting full model: {e}")
    
    print(f"\nExtracted results for {len(results_list)} model coefficients")
    
    return results_list

def save_results(vviq2_processed_df, regression_results):
    """
    Save processed VVIQ2 data and regression results to CSV files.
    
    Parameters:
        vviq2_processed_df (pd.DataFrame): Processed VVIQ2 data
        regression_results (list): List of regression result dictionaries
        
    Returns:
        None
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save processed VVIQ2 scores
    vviq2_output_file = f'outputs/vviq2_scores_processed_{timestamp}.csv'
    vviq2_processed_df.to_csv(vviq2_output_file, index=False)
    print(f"Saved processed VVIQ2 data to: {vviq2_output_file}")
    
    # Save regression results
    if regression_results:
        regression_df = pd.DataFrame(regression_results)
        regression_output_file = f'outputs/vviq2_robust_regression_results_{timestamp}.csv'
        regression_df.to_csv(regression_output_file, index=False)
        print(f"Saved regression results to: {regression_output_file}")
        
        print("\nRegression results summary:")
        print(regression_df.head())
        
        # Print key findings
        kappa_results = regression_df[regression_df['variable_name'] == 'kappa_concentration']
        if len(kappa_results) > 0:
            print(f"\nKey findings for kappa_concentration:")
            for _, row in kappa_results.iterrows():
                print(f"  {row['model_name']}: coef={row['coefficient']:.4f}, p={row['p_value']:.4f}")
    else:
        print("No regression results to save")

def main():
    """
    Main function to execute the VVIQ2 analysis pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 analysis pipeline...")
        
        # Create output directory
        create_output_directory()
        
        # Load and process VVIQ2 data
        vviq2_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        if not os.path.exists(vviq2_file):
            print(f"Error: VVIQ2 file not found: {vviq2_file}")
            return 1
        
        vviq2_processed_df = process_vviq2_data(vviq2_file)
        if vviq2_processed_df is None or len(vviq2_processed_df) == 0:
            print("Error: Failed to process VVIQ2 data")
            return 1
        
        # Load VWM data
        vwm_df = load_vwm_data()
        if vwm_df is None:
            print("Error: Failed to load VWM data")
            return 1
        
        # Load behavioral control data
        control_df = load_behavioral_control_data()
        if control_df is None:
            print("Error: Failed to load behavioral control data")
            return 1
        
        # Merge datasets
        merged_df = merge_datasets(vviq2_processed_df, vwm_df, control_df)
        if len(merged_df) == 0:
            print("Error: No participants remaining after merging datasets")
            return 1
        
        # Run robust regression analyses
        regression_results = run_robust_regression(merged_df)
        
        # Save results
        save_results(vviq2_processed_df, regression_results)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
