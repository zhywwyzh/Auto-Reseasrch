#!/usr/bin/env python3
"""
Script to calculate cognitive performance metrics from VWM and MRT task data.

This script processes cleaned VWM and MRT data to calculate performance metrics
for each participant, including accuracy, reaction times, and control variables.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match (e.g., 'outputs/VWM_MRT_cleaned_data_*.csv')
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def load_and_validate_data(filepath):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    filepath (str): Path to the CSV file
    
    Returns:
    pd.DataFrame: Loaded dataframe, or None if validation fails
    """
    required_columns = [
        'participantId', 'isPractice', 'VWM_error_absolute_degrees', 'VWM_rt_ms',
        'VWM_block', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_block',
        'excluded_from_VWM', 'excluded_from_MRT', 'trial_excluded',
        'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration'
    ]
    
    try:
        df = pd.read_csv(filepath)
        print(f"Successfully loaded data from: {filepath}")
        print(f"Data shape: {df.shape}")
        
        # Print all columns
        print(f"All columns: {list(df.columns)}")
        
        # Print first 3 rows
        print("First 3 rows of data:")
        print(df.head(3))
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return None
        
        print("All required columns present.")
        
        # Print unique values for key experimental design columns
        print("\nUnique values for key experimental design columns:")
        print(f"isPractice unique values: {df['isPractice'].unique()}")
        print(f"VWM_block unique values: {df['VWM_block'].unique()}")
        print(f"MRT_block unique values: {df['MRT_block'].unique()}")
        print(f"MRT_angle_degrees unique values: {sorted(df['MRT_angle_degrees'].unique())}")
        print(f"excluded_from_VWM unique values: {df['excluded_from_VWM'].unique()}")
        print(f"excluded_from_MRT unique values: {df['excluded_from_MRT'].unique()}")
        print(f"trial_excluded unique values: {df['trial_excluded'].unique()}")
        print(f"MRT_isCorrect unique values: {df['MRT_isCorrect'].unique()}")
        
        # Print data types for measured variables (not unique values as they're too many)
        print(f"\nData types for measured variables:")
        print(f"VWM_error_absolute_degrees type: {df['VWM_error_absolute_degrees'].dtype}")
        print(f"VWM_rt_ms type: {df['VWM_rt_ms'].dtype}")
        print(f"MRT_rt_ms type: {df['MRT_rt_ms'].dtype}")
        print(f"windowFocusLostDuringTasksNum type: {df['windowFocusLostDuringTasksNum'].dtype}")
        print(f"windowFocusLostDuringTasksDuration type: {df['windowFocusLostDuringTasksDuration'].dtype}")
        
        return df
        
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return None

def filter_test_trials(df, task_type):
    """
    Filter for test trials based on task type.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    task_type (str): Either 'VWM' or 'MRT'
    
    Returns:
    pd.DataFrame: Filtered dataframe containing only test trials
    """
    print(f"\nFiltering {task_type} test trials...")
    
    # Start with all data
    filtered_df = df.copy()
    print(f"Starting with {len(filtered_df)} total trials")
    
    # Filter for non-practice trials
    filtered_df = filtered_df[filtered_df['isPractice'] == False]
    print(f"After isPractice=False filter: {len(filtered_df)} trials")
    
    # Filter for test blocks (not practice blocks)
    if task_type == 'VWM':
        filtered_df = filtered_df[filtered_df['VWM_block'] != 'practice']
        print(f"After VWM_block != 'practice' filter: {len(filtered_df)} trials")
        
        # Apply VWM-specific exclusions
        filtered_df = filtered_df[filtered_df['excluded_from_VWM'] == False]
        print(f"After excluded_from_VWM=False filter: {len(filtered_df)} trials")
        
    elif task_type == 'MRT':
        filtered_df = filtered_df[filtered_df['MRT_block'] != 'practice']
        print(f"After MRT_block != 'practice' filter: {len(filtered_df)} trials")
        
        # Apply MRT-specific exclusions
        filtered_df = filtered_df[filtered_df['excluded_from_MRT'] == False]
        print(f"After excluded_from_MRT=False filter: {len(filtered_df)} trials")
    
    # Apply trial-level exclusions
    filtered_df = filtered_df[filtered_df['trial_excluded'] == False]
    print(f"After trial_excluded=False filter: {len(filtered_df)} trials")
    
    return filtered_df

def calculate_mrt_metrics(df):
    """
    Calculate MRT performance metrics for each participant.
    
    Parameters:
    df (pd.DataFrame): Filtered MRT test trials
    
    Returns:
    pd.DataFrame: MRT metrics per participant
    """
    print("\nCalculating MRT metrics...")
    
    # Filter for MRT test trials
    mrt_df = filter_test_trials(df, 'MRT')
    
    if len(mrt_df) == 0:
        print("WARNING: No valid MRT trials found!")
        return pd.DataFrame()
    
    print(f"Processing {len(mrt_df)} valid MRT trials")
    
    # Initialize results list
    results = []
    
    # Get unique participants
    participants = mrt_df['participantId'].unique()
    print(f"Processing {len(participants)} participants for MRT metrics")
    
    # Define rotation angles
    angles = [0, 50, 100, 150]
    
    for participant in participants:
        print(f"Processing participant: {participant}")
        
        # Get participant data
        p_data = mrt_df[mrt_df['participantId'] == participant].copy()
        
        # Initialize participant metrics
        participant_metrics = {'participantId': participant}
        has_complete_data = True
        
        # Calculate metrics for each angle
        for angle in angles:
            angle_data = p_data[p_data['MRT_angle_degrees'] == angle]
            
            if len(angle_data) == 0:
                print(f"  No data for {angle}° angle")
                participant_metrics[f'MRT_accuracy_{angle}deg'] = np.nan
                participant_metrics[f'MRT_mean_RT_{angle}deg'] = np.nan
                participant_metrics[f'MRT_log_RT_{angle}deg'] = np.nan
                has_complete_data = False
                continue
            
            # Calculate accuracy
            accuracy = angle_data['MRT_isCorrect'].mean()
            participant_metrics[f'MRT_accuracy_{angle}deg'] = accuracy
            
            # Calculate mean RT for correct trials
            correct_trials = angle_data[angle_data['MRT_isCorrect'] == True]
            if len(correct_trials) > 0:
                mean_rt = correct_trials['MRT_rt_ms'].mean()
                log_rt = np.log(mean_rt) if mean_rt > 0 else np.nan
                participant_metrics[f'MRT_mean_RT_{angle}deg'] = mean_rt
                participant_metrics[f'MRT_log_RT_{angle}deg'] = log_rt
            else:
                participant_metrics[f'MRT_mean_RT_{angle}deg'] = np.nan
                participant_metrics[f'MRT_log_RT_{angle}deg'] = np.nan
                has_complete_data = False
            
            print(f"  {angle}°: accuracy={accuracy:.3f}, trials={len(angle_data)}, correct={len(correct_trials)}")
        
        # Calculate RT coefficient of variation across all correct trials
        all_correct = p_data[p_data['MRT_isCorrect'] == True]
        if len(all_correct) > 1:
            rt_mean = all_correct['MRT_rt_ms'].mean()
            rt_std = all_correct['MRT_rt_ms'].std()
            rt_cv = rt_std / rt_mean if rt_mean > 0 else np.nan
            participant_metrics['MRT_RT_coefficient_variation'] = rt_cv
        else:
            participant_metrics['MRT_RT_coefficient_variation'] = np.nan
            has_complete_data = False
        
        participant_metrics['has_complete_MRT_data'] = has_complete_data
        results.append(participant_metrics)
    
    return pd.DataFrame(results)

def calculate_vwm_metrics(df):
    """
    Calculate VWM performance metrics for each participant.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: VWM metrics per participant
    """
    print("\nCalculating VWM metrics...")
    
    # Filter for VWM test trials
    vwm_df = filter_test_trials(df, 'VWM')
    
    if len(vwm_df) == 0:
        print("WARNING: No valid VWM trials found!")
        return pd.DataFrame()
    
    print(f"Processing {len(vwm_df)} valid VWM trials")
    
    # Calculate mean absolute error per participant
    vwm_metrics = vwm_df.groupby('participantId').agg({
        'VWM_error_absolute_degrees': 'mean'
    }).reset_index()
    
    vwm_metrics.rename(columns={'VWM_error_absolute_degrees': 'VWM_mean_absolute_error'}, inplace=True)
    
    # Add completion flag
    vwm_metrics['has_complete_VWM_data'] = True
    
    print(f"Calculated VWM metrics for {len(vwm_metrics)} participants")
    print("VWM metrics preview:")
    print(vwm_metrics.head(2))
    
    return vwm_metrics

def calculate_control_variables(df):
    """
    Calculate domain-general control variables for each participant.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Control variables per participant
    """
    print("\nCalculating control variables...")
    
    results = []
    participants = df['participantId'].unique()
    
    for participant in participants:
        p_data = df[df['participantId'] == participant].copy()
        
        # Focus loss metrics (take from first row as these are participant-level)
        focus_instances = p_data['windowFocusLostDuringTasksNum'].iloc[0] if not p_data.empty else 0
        # Convert focus duration to seconds using pandas for robustness
        focus_duration_str = p_data['windowFocusLostDuringTasksDuration'].iloc[0] if not p_data.empty else "0"
        try:
            focus_duration_sec = pd.to_timedelta(focus_duration_str).total_seconds()
        except (ValueError, TypeError):
            focus_duration_sec = 0.0

        # Estimate session duration based on sum of valid RTs + assumed ITI (1s)
        # This is an approximation as no trial timestamps are available.
        valid_trials = p_data[(p_data['trial_excluded'] == False) & (p_data['isPractice'] == False)]
        if len(valid_trials) > 0:
            vwm_rt_sum = valid_trials['VWM_rt_ms'].fillna(0).sum()
            mrt_rt_sum = valid_trials['MRT_rt_ms'].fillna(0).sum()
            vwm_rt_count = valid_trials['VWM_rt_ms'].notna().sum()
            mrt_rt_count = valid_trials['MRT_rt_ms'].notna().sum()
            total_rt_ms = vwm_rt_sum + mrt_rt_sum
            num_valid_trials = vwm_rt_count + mrt_rt_count
            estimated_duration_min = (total_rt_ms + num_valid_trials * 1000) / 60000 if num_valid_trials > 0 else 0
        else:
            estimated_duration_min = 0
        
        control_vars = {
            'participantId': participant,
            'focus_loss_instances_trials': int(focus_instances) if pd.notna(focus_instances) and str(focus_instances).replace('.','').isdigit() else 0,
            'focus_loss_duration_trials_sec': focus_duration_sec,
            'total_session_duration_min': estimated_duration_min
        }
        
        results.append(control_vars)
        
        print(f"Participant {participant}: focus_instances={focus_instances}, "
              f"focus_duration={focus_duration_sec:.2f}s, session_duration={estimated_duration_min:.1f}min")
    
    return pd.DataFrame(results)

def validate_metrics(df):
    """
    Validate calculated metrics for data quality.
    
    Parameters:
    df (pd.DataFrame): Dataframe with calculated metrics
    
    Returns:
    pd.DataFrame: Validated dataframe
    """
    print("\nValidating metrics...")
    
    # Check accuracy values are between 0 and 1
    accuracy_cols = [col for col in df.columns if 'accuracy' in col]
    for col in accuracy_cols:
        invalid_acc = df[(df[col] < 0) | (df[col] > 1)][col]
        if len(invalid_acc) > 0:
            print(f"WARNING: Invalid accuracy values in {col}: {invalid_acc.tolist()}")
    
    # Check RT values are positive (but not log RTs, which can be negative)
    rt_cols = [col for col in df.columns if '_RT_' in col]
    for col in rt_cols:
        if 'log' not in col:  # Exclude log_RT columns from this check
            invalid_rt = df[df[col] <= 0].dropna(subset=[col])
            if not invalid_rt.empty:
                print(f"WARNING: Non-positive RT values in {col}: {invalid_rt[col].tolist()}")
    
    # Check for extreme outliers in control variables
    control_cols = ['focus_loss_instances_trials', 'focus_loss_duration_trials_sec', 'total_session_duration_min']
    for col in control_cols:
        if col in df.columns:
            q99 = df[col].quantile(0.99)
            outliers = df[df[col] > q99]
            if len(outliers) > 0:
                print(f"Potential outliers in {col} (>99th percentile): {len(outliers)} participants")
    
    # Report missing data
    missing_summary = df.isnull().sum()
    print("\nMissing data summary:")
    for col, missing_count in missing_summary.items():
        if missing_count > 0:
            print(f"  {col}: {missing_count} missing values")
    
    print("Validation complete.")
    return df

def main():
    """
    Main function to process cognitive performance metrics.
    
    Returns:
    int: 0 for success, 1 for failure
    """
    try:
        print("Starting cognitive performance metrics calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/VWM_MRT_cleaned_data_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            return 1
        
        # Calculate MRT metrics
        mrt_metrics = calculate_mrt_metrics(df)
        if mrt_metrics.empty:
            print("ERROR: Failed to calculate MRT metrics")
            return 1
        
        print("\nMRT metrics preview:")
        print("Columns:", list(mrt_metrics.columns))
        print("First 2 rows:")
        print(mrt_metrics.head(2))
        
        # Calculate VWM metrics
        vwm_metrics = calculate_vwm_metrics(df)
        if vwm_metrics.empty:
            print("ERROR: Failed to calculate VWM metrics")
            return 1
        
        # Calculate control variables
        control_vars = calculate_control_variables(df)
        
        print("\nControl variables preview:")
        print("Columns:", list(control_vars.columns))
        print("First 2 rows:")
        print(control_vars.head(2))
        
        # Merge all metrics
        print("\nMerging all metrics...")
        final_df = mrt_metrics.merge(vwm_metrics, on='participantId', how='outer')
        final_df = final_df.merge(control_vars, on='participantId', how='outer')
        
        # Fill missing completion flags
        final_df['has_complete_MRT_data'] = final_df['has_complete_MRT_data'].fillna(False)
        final_df['has_complete_VWM_data'] = final_df['has_complete_VWM_data'].fillna(False)
        
        print(f"Final dataframe shape: {final_df.shape}")
        print("Final dataframe columns:", list(final_df.columns))
        print("First 2 rows of final dataframe:")
        print(final_df.head(2))
        
        # Validate metrics
        final_df = validate_metrics(final_df)
        
        # Reorder columns to match required output format
        required_columns = [
            'participantId',
            'MRT_accuracy_0deg', 'MRT_accuracy_50deg', 'MRT_accuracy_100deg', 'MRT_accuracy_150deg',
            'MRT_mean_RT_0deg', 'MRT_mean_RT_50deg', 'MRT_mean_RT_100deg', 'MRT_mean_RT_150deg',
            'MRT_log_RT_0deg', 'MRT_log_RT_50deg', 'MRT_log_RT_100deg', 'MRT_log_RT_150deg',
            'VWM_mean_absolute_error',
            'MRT_RT_coefficient_variation',
            'focus_loss_instances_trials',
            'focus_loss_duration_trials_sec',
            'total_session_duration_min',
            'has_complete_MRT_data',
            'has_complete_VWM_data'
        ]
        
        # Ensure all required columns exist
        for col in required_columns:
            if col not in final_df.columns:
                print(f"Adding missing column: {col}")
                final_df[col] = np.nan
        
        # Select and reorder columns
        final_df = final_df[required_columns]
        
        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'outputs/cognitive_performance_metrics_{timestamp}.csv'
        
        # Save results
        final_df.to_csv(output_file, index=False)
        print(f"\nResults saved to: {output_file}")
        
        # Print summary statistics
        print(f"\nSummary:")
        print(f"Total participants: {len(final_df)}")
        print(f"Participants with complete MRT data: {final_df['has_complete_MRT_data'].sum()}")
        print(f"Participants with complete VWM data: {final_df['has_complete_VWM_data'].sum()}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
