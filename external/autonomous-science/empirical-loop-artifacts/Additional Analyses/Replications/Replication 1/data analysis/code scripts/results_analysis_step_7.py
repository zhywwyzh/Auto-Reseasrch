#!/usr/bin/env python3
"""
Script to calculate MRT dependent variables and cognitive covariates from cleaned data files.
This script processes MRT, VWM, and cognitive control data to create variables for mixed-effects modeling.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to search for, including wildcards
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def load_and_validate_data():
    """
    Load and validate all required input data files.
    
    Returns:
    tuple: (mrt_data, vwm_data, cognitive_data) DataFrames or None if error
    """
    print("Starting data loading and validation...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Find latest input files
    print("Searching for input files...")
    mrt_file = find_latest_file('outputs/MRT_cleaned_data_*.csv')
    vwm_file = find_latest_file('outputs/VWM_cleaned_data_*.csv')
    cognitive_file = find_latest_file('outputs/cognitive_control_metrics_*.csv')
    
    print(f"Found MRT file: {mrt_file}")
    print(f"Found VWM file: {vwm_file}")
    print(f"Found cognitive file: {cognitive_file}")
    
    if not all([mrt_file, vwm_file, cognitive_file]):
        print("ERROR: Could not find all required input files")
        return None, None, None
    
    # Load MRT data
    print("\nLoading MRT data...")
    try:
        mrt_data = pd.read_csv(mrt_file)
        print(f"MRT data shape: {mrt_data.shape}")
        print("MRT columns:", list(mrt_data.columns))
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        # Check required columns
        required_mrt_cols = ['participantId', 'trial_type', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms', 'excluded_participant']
        missing_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
        if missing_cols:
            print(f"ERROR: Missing MRT columns: {missing_cols}")
            return None, None, None
            
        # Print unique values for key experimental design parameters
        print("Unique values in MRT_angle_degrees:", sorted(mrt_data['MRT_angle_degrees'].unique()))
        print("Unique values in trial_type:", mrt_data['trial_type'].unique())
        print("Unique values in excluded_participant:", mrt_data['excluded_participant'].unique())
        print("MRT_isCorrect data type:", type(mrt_data['MRT_isCorrect'].iloc[0]))
        print("MRT_rt_ms data type:", type(mrt_data['MRT_rt_ms'].iloc[0]))
        
    except Exception as e:
        print(f"ERROR loading MRT data: {e}")
        return None, None, None
    
    # Load VWM data
    print("\nLoading VWM data...")
    try:
        vwm_data = pd.read_csv(vwm_file)
        print(f"VWM data shape: {vwm_data.shape}")
        print("VWM columns:", list(vwm_data.columns))
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
        
        # Check required columns
        required_vwm_cols = ['participantId', 'trial_type', 'VWM_error_absolute_degrees', 'excluded_participant']
        missing_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
        if missing_cols:
            print(f"ERROR: Missing VWM columns: {missing_cols}")
            return None, None, None
            
        # Print unique values for key experimental design parameters
        print("Unique values in trial_type:", vwm_data['trial_type'].unique())
        print("Unique values in excluded_participant:", vwm_data['excluded_participant'].unique())
        print("VWM_error_absolute_degrees data type:", type(vwm_data['VWM_error_absolute_degrees'].iloc[0]))
        
    except Exception as e:
        print(f"ERROR loading VWM data: {e}")
        return None, None, None
    
    # Load cognitive control data
    print("\nLoading cognitive control data...")
    try:
        cognitive_data = pd.read_csv(cognitive_file)
        print(f"Cognitive data shape: {cognitive_data.shape}")
        print("Cognitive columns:", list(cognitive_data.columns))
        print("First 3 rows of cognitive data:")
        print(cognitive_data.head(3))
        
        # Check required columns
        required_cog_cols = ['participantId', 'focus_loss_severity_index', 'VWM_rt_coefficient_variation']
        missing_cols = [col for col in required_cog_cols if col not in cognitive_data.columns]
        if missing_cols:
            print(f"ERROR: Missing cognitive columns: {missing_cols}")
            return None, None, None
            
        print("focus_loss_severity_index data type:", type(cognitive_data['focus_loss_severity_index'].iloc[0]))
        print("VWM_rt_coefficient_variation data type:", type(cognitive_data['VWM_rt_coefficient_variation'].iloc[0]))
        
    except Exception as e:
        print(f"ERROR loading cognitive data: {e}")
        return None, None, None
    
    return mrt_data, vwm_data, cognitive_data

def filter_participants(mrt_data, vwm_data, cognitive_data):
    """
    Filter for non-excluded participants across all datasets.
    
    Parameters:
    mrt_data (DataFrame): MRT dataset
    vwm_data (DataFrame): VWM dataset  
    cognitive_data (DataFrame): Cognitive control dataset
    
    Returns:
    tuple: Filtered datasets (mrt_filtered, vwm_filtered, cognitive_filtered)
    """
    print("\nFiltering for non-excluded participants...")
    
    # Filter MRT data
    print(f"MRT data before filtering: {len(mrt_data)} rows")
    mrt_filtered = mrt_data[
        (mrt_data['excluded_participant'] == False) & 
        (mrt_data['trial_type'] == 'test')
    ].copy()
    print(f"MRT data after filtering: {len(mrt_filtered)} rows")
    
    # Filter VWM data
    print(f"VWM data before filtering: {len(vwm_data)} rows")
    vwm_filtered = vwm_data[
        (vwm_data['excluded_participant'] == False) & 
        (vwm_data['trial_type'] == 'test')
    ].copy()
    print(f"VWM data after filtering: {len(vwm_filtered)} rows")
    
    # Get unique participants from each dataset
    mrt_participants = set(mrt_filtered['participantId'].unique())
    vwm_participants = set(vwm_filtered['participantId'].unique())
    cognitive_participants = set(cognitive_data['participantId'].unique())
    
    print(f"Unique participants in MRT: {len(mrt_participants)}")
    print(f"Unique participants in VWM: {len(vwm_participants)}")
    print(f"Unique participants in cognitive: {len(cognitive_participants)}")
    
    # Find common participants across all datasets
    common_participants = mrt_participants & vwm_participants & cognitive_participants
    print(f"Common participants across all datasets: {len(common_participants)}")
    
    # Filter all datasets to common participants
    mrt_filtered = mrt_filtered[mrt_filtered['participantId'].isin(common_participants)].copy()
    vwm_filtered = vwm_filtered[vwm_filtered['participantId'].isin(common_participants)].copy()
    cognitive_filtered = cognitive_data[cognitive_data['participantId'].isin(common_participants)].copy()
    
    print(f"Final MRT data: {len(mrt_filtered)} rows, {len(mrt_filtered['participantId'].unique())} participants")
    print(f"Final VWM data: {len(vwm_filtered)} rows, {len(vwm_filtered['participantId'].unique())} participants")
    print(f"Final cognitive data: {len(cognitive_filtered)} rows, {len(cognitive_filtered['participantId'].unique())} participants")
    
    return mrt_filtered, vwm_filtered, cognitive_filtered

def calculate_mrt_variables(mrt_data):
    """
    Calculate MRT dependent variables by rotation angle for each participant.
    
    Parameters:
    mrt_data (DataFrame): Filtered MRT dataset
    
    Returns:
    DataFrame: MRT variables by participant and angle
    """
    print("\nCalculating MRT dependent variables...")
    
    # Apply RT filtering (200-7000ms)
    print(f"MRT trials before RT filtering: {len(mrt_data)}")
    mrt_valid = mrt_data[
        (mrt_data['MRT_rt_ms'] >= 200) & 
        (mrt_data['MRT_rt_ms'] <= 7000)
    ].copy()
    print(f"MRT trials after RT filtering: {len(mrt_valid)}")
    
    # Get all unique participants and angles for reporting
    participants = mrt_valid['participantId'].unique()
    angles = sorted(mrt_valid['MRT_angle_degrees'].unique())
    print(f"Processing {len(participants)} participants across {len(angles)} angles: {angles}")
    
    # 1. Calculate trial counts to identify groups with insufficient data
    trial_counts = mrt_valid.groupby(['participantId', 'MRT_angle_degrees']).size().reset_index(name='valid_trials_count_angle')
    
    # Identify participant-angle combinations to keep (>= 8 trials)
    valid_groups = trial_counts[trial_counts['valid_trials_count_angle'] >= 8]
    
    num_excluded = len(trial_counts) - len(valid_groups)
    print(f"Excluded {num_excluded} participant-angle combinations due to insufficient trials (<8)")
    
    # Filter original data to only include valid groups
    mrt_filtered = pd.merge(mrt_valid, valid_groups[['participantId', 'MRT_angle_degrees']], on=['participantId', 'MRT_angle_degrees'])
    
    # 2. Calculate DVs using groupby().agg() for efficiency
    # Create a column for correct RTs to easily calculate median
    mrt_filtered['correct_rt_ms'] = mrt_filtered['MRT_rt_ms'].where(mrt_filtered['MRT_isCorrect'])

    mrt_results = mrt_filtered.groupby(['participantId', 'MRT_angle_degrees']).agg(
        MRT_accuracy_proportion=('MRT_isCorrect', 'mean'),
        MRT_median_rt_ms=('correct_rt_ms', 'median'),
        valid_trials_count_angle=('MRT_rt_ms', 'size')
    ).reset_index()

    # Rename the angle column to match expected output
    mrt_results = mrt_results.rename(columns={'MRT_angle_degrees': 'rotation_angle_degrees'})

    # 3. Calculate log-transformed median RT
    mrt_results['MRT_log_median_rt'] = np.log(mrt_results['MRT_median_rt_ms'])

    print(f"MRT results shape: {mrt_results.shape}")
    print("First 2 rows of MRT results:")
    print(mrt_results.head(2))

    return mrt_results

def calculate_cognitive_covariates(vwm_data, cognitive_data):
    """
    Calculate domain-general cognitive covariates.
    
    Parameters:
    vwm_data (DataFrame): Filtered VWM dataset
    cognitive_data (DataFrame): Cognitive control dataset
    
    Returns:
    DataFrame: Cognitive covariates by participant
    """
    print("\nCalculating cognitive covariates...")
    
    # Calculate VWM performance (mean absolute error)
    vwm_performance = vwm_data.groupby('participantId')['VWM_error_absolute_degrees'].mean().reset_index()
    vwm_performance.columns = ['participantId', 'mean_VWM_absolute_error']
    
    print(f"VWM performance calculated for {len(vwm_performance)} participants")
    print("VWM performance stats:")
    print(vwm_performance['mean_VWM_absolute_error'].describe())
    
    # Extract cognitive control metrics
    cognitive_metrics = cognitive_data[['participantId', 'focus_loss_severity_index', 'VWM_rt_coefficient_variation']].copy()
    
    print(f"Cognitive metrics for {len(cognitive_metrics)} participants")
    print("Focus loss severity stats:")
    print(cognitive_metrics['focus_loss_severity_index'].describe())
    print("VWM RT coefficient variation stats:")
    print(cognitive_metrics['VWM_rt_coefficient_variation'].describe())
    
    # Merge covariates
    covariates = pd.merge(vwm_performance, cognitive_metrics, on='participantId', how='inner')
    
    print(f"Final covariates shape: {covariates.shape}")
    print("Covariates columns:", list(covariates.columns))
    print("First 2 rows of covariates:")
    print(covariates.head(2))
    
    return covariates

def validate_data_quality(mrt_results, covariates):
    """
    Perform data validation checks.
    
    Parameters:
    mrt_results (DataFrame): MRT results dataset
    covariates (DataFrame): Cognitive covariates dataset
    
    Returns:
    tuple: (mrt_clean, covariates_clean) after validation
    """
    print("\nPerforming data validation...")
    
    initial_mrt_rows = len(mrt_results)
    initial_cov_rows = len(covariates)
    
    # Check accuracy values (0-1 range)
    invalid_accuracy = mrt_results[
        (mrt_results['MRT_accuracy_proportion'] < 0) | 
        (mrt_results['MRT_accuracy_proportion'] > 1)
    ]
    print(f"Invalid accuracy values: {len(invalid_accuracy)}")
    
    # Check for outliers in log-transformed RTs (>3 SD from mean)
    valid_rt_data = mrt_results.dropna(subset=['MRT_log_median_rt'])
    if len(valid_rt_data) > 0:
        rt_mean = valid_rt_data['MRT_log_median_rt'].mean()
        rt_std = valid_rt_data['MRT_log_median_rt'].std()
        rt_outliers = valid_rt_data[
            np.abs(valid_rt_data['MRT_log_median_rt'] - rt_mean) > 3 * rt_std
        ]
        print(f"RT outliers (>3 SD): {len(rt_outliers)}")
        
        # Replace outlier RTs with NaN instead of dropping rows
        if not rt_outliers.empty:
            outlier_indices = rt_outliers.index
            print(f"Setting RT for {len(outlier_indices)} outlier rows to NaN.")
            mrt_results.loc[outlier_indices, ['MRT_median_rt_ms', 'MRT_log_median_rt']] = np.nan
    
    # Verify covariate ranges
    print("Covariate validation:")
    print(f"VWM error range: {covariates['mean_VWM_absolute_error'].min():.3f} - {covariates['mean_VWM_absolute_error'].max():.3f}")
    print(f"RT CV range: {covariates['VWM_rt_coefficient_variation'].min():.3f} - {covariates['VWM_rt_coefficient_variation'].max():.3f}")
    print(f"Focus loss range: {covariates['focus_loss_severity_index'].min():.3f} - {covariates['focus_loss_severity_index'].max():.3f}")
    
    print(f"MRT data: {initial_mrt_rows} -> {len(mrt_results)} rows after validation (outliers nullified, not removed)")
    print(f"Covariates: {initial_cov_rows} -> {len(covariates)} rows after validation")
    
    return mrt_results, covariates

def create_final_datasets(mrt_results, covariates):
    """
    Create final datasets for output, ensuring participant consistency.
    
    Parameters:
    mrt_results (DataFrame): MRT results dataset
    covariates (DataFrame): Cognitive covariates dataset
    
    Returns:
    tuple: (dependent_vars, cognitive_covs) final datasets
    """
    print("\nCreating final datasets...")
    
    # Merge MRT results with covariates
    dependent_vars = pd.merge(mrt_results, covariates, on='participantId', how='inner')
    
    # Get the final list of participants who have valid MRT data
    final_participant_ids = dependent_vars['participantId'].unique()
    
    # Filter the cognitive covariates to ensure consistency
    cognitive_covs = covariates[covariates['participantId'].isin(final_participant_ids)].copy()
    
    # Reorder columns to match the specified output format for clarity
    output_columns_order = [
        'participantId', 'rotation_angle_degrees', 'MRT_accuracy_proportion',
        'MRT_median_rt_ms', 'MRT_log_median_rt', 'valid_trials_count_angle',
        'mean_VWM_absolute_error', 'VWM_rt_coefficient_variation', 'focus_loss_severity_index'
    ]
    dependent_vars = dependent_vars[output_columns_order]
    
    print(f"Dependent variables dataset shape: {dependent_vars.shape}")
    print("Dependent variables columns:", list(dependent_vars.columns))
    print("First 2 rows of dependent variables:")
    print(dependent_vars.head(2))
    
    print(f"Cognitive covariates dataset shape: {cognitive_covs.shape}")
    print("Cognitive covariates columns:", list(cognitive_covs.columns))
    print("First 2 rows of cognitive covariates:")
    print(cognitive_covs.head(2))
    
    return dependent_vars, cognitive_covs

def save_outputs(dependent_vars, cognitive_covs):
    """
    Save output datasets to CSV files.
    
    Parameters:
    dependent_vars (DataFrame): MRT dependent variables dataset
    cognitive_covs (DataFrame): Cognitive covariates dataset
    """
    print("\nSaving output files...")
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save dependent variables
    dep_vars_file = f"outputs/MRT_dependent_variables_{timestamp}.csv"
    dependent_vars.to_csv(dep_vars_file, index=False)
    print(f"Saved dependent variables to: {dep_vars_file}")
    
    # Save cognitive covariates
    cog_covs_file = f"outputs/cognitive_covariates_{timestamp}.csv"
    cognitive_covs.to_csv(cog_covs_file, index=False)
    print(f"Saved cognitive covariates to: {cog_covs_file}")
    
    # Print final summary
    print(f"\nFinal summary:")
    print(f"Dependent variables: {len(dependent_vars)} rows, {len(dependent_vars['participantId'].unique())} participants")
    print(f"Cognitive covariates: {len(cognitive_covs)} rows, {len(cognitive_covs['participantId'].unique())} participants")
    
    # Print sample of final data
    print("\nSample of final dependent variables data:")
    print(dependent_vars.head(5))
    
    print("\nSample of final cognitive covariates data:")
    print(cognitive_covs.head(5))

def main():
    """
    Main function to execute the MRT dependent variables calculation pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT dependent variables calculation pipeline...")
        
        # Load and validate input data
        mrt_data, vwm_data, cognitive_data = load_and_validate_data()
        if mrt_data is None:
            print("ERROR: Failed to load input data")
            return 1
        
        # Filter participants
        mrt_filtered, vwm_filtered, cognitive_filtered = filter_participants(
            mrt_data, vwm_data, cognitive_data
        )
        
        # Calculate MRT variables
        mrt_results = calculate_mrt_variables(mrt_filtered)
        if len(mrt_results) == 0:
            print("ERROR: No valid MRT results calculated")
            return 1
        
        # Calculate cognitive covariates
        covariates = calculate_cognitive_covariates(vwm_filtered, cognitive_filtered)
        if len(covariates) == 0:
            print("ERROR: No cognitive covariates calculated")
            return 1
        
        # Validate data quality
        mrt_results, covariates = validate_data_quality(mrt_results, covariates)
        
        # Create final datasets
        dependent_vars, cognitive_covs = create_final_datasets(mrt_results, covariates)
        
        # Save outputs
        save_outputs(dependent_vars, cognitive_covs)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
