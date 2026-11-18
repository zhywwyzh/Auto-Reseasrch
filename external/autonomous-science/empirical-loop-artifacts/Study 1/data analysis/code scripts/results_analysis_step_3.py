#!/usr/bin/env python3
"""
MRT (Mental Rotation Task) Data Cleaning Script

This script processes MRT data from CSV files, applies participant and trial-level exclusions,
and outputs cleaned data with exclusion logs.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def load_mrt_data(file_pattern):
    """
    Load and combine MRT data from multiple CSV files.
    
    Parameters:
    file_pattern (str): Glob pattern for input CSV files
    
    Returns:
    tuple: (combined_dataframe, num_files_processed)
        - combined_dataframe (pd.DataFrame): Combined dataframe with MRT data
        - num_files_processed (int): Number of files successfully processed
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    # Find all matching files
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} matching files:")
    for file in files:
        print(f"  - {file}")
    
    if not files:
        print("No matching files found!")
        return pd.DataFrame(), 0
    
    # Load and combine all files
    all_data = []
    files_processed = 0
    for file in files:
        print(f"\nLoading file: {file}")
        try:
            df = pd.read_csv(file)
            # Strip whitespace from column names
            df.columns = [col.strip() for col in df.columns]
            print(f"File shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            all_data.append(df)
            files_processed += 1
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not all_data:
        print("No valid data files loaded!")
        return pd.DataFrame(), files_processed
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined data shape: {combined_df.shape}")
    print(f"Combined data columns: {list(combined_df.columns)}")
    print(f"Successfully processed {files_processed} files")
    
    return combined_df, files_processed

def filter_mrt_data(df):
    """
    Filter data to extract MRT-related rows.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Filtered dataframe containing only MRT data
    """
    print("\n=== FILTERING MRT DATA ===")
    
    # Check if required columns exist
    required_cols = ['participantId', 'table', 'isPractice', 'MRT_trial', 'MRT_angle_degrees', 
                     'MRT_isCorrect', 'MRT_rt_ms', 'MRT_timeout', 'MRT_isAttentionCheck']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Missing required columns: {missing_cols}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    print(f"All required columns present: {required_cols}")
    
    # Filter for MRT data (table contains "rotation" or "mrt", case-insensitive)
    # Check if table column exists and has string data
    if 'table' not in df.columns:
        print("Error: 'table' column not found in data")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Ensure table column is string type for string operations
    df['table'] = df['table'].astype(str)
    mrt_mask = df['table'].str.contains('rotation|mrt', case=False, na=False)
    mrt_data = df[mrt_mask].copy()
    
    print(f"Original data shape: {df.shape}")
    print(f"MRT data shape after filtering: {mrt_data.shape}")
    
    # Check if we have any MRT data
    if mrt_data.empty:
        print("No MRT data found after filtering!")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    # Handle NaN values in MRT_isAttentionCheck and convert to boolean
    # This step fills missing attention check flags with False (non-attention check trials)
    print("Converting MRT_isAttentionCheck to boolean...")
    print(f"MRT_isAttentionCheck NaN values before conversion: {mrt_data['MRT_isAttentionCheck'].isnull().sum()}")
    mrt_data.loc[:, 'MRT_isAttentionCheck'] = mrt_data['MRT_isAttentionCheck'].fillna(False)
    mrt_data.loc[:, 'MRT_isAttentionCheck'] = mrt_data['MRT_isAttentionCheck'].infer_objects(copy=False).astype(bool)
    print(f"MRT_isAttentionCheck NaN values after conversion: {mrt_data['MRT_isAttentionCheck'].isnull().sum()}")
    
    # Convert MRT_isCorrect to numeric type (0=incorrect, 1=correct)
    # This standardizes boolean responses to numeric format for statistical analysis
    print("Converting MRT_isCorrect to numeric for calculations (0/1)...")
    print(f"MRT_isCorrect unique values before conversion: {sorted(mrt_data['MRT_isCorrect'].dropna().unique())}")
    
    # Use supervisor's mapping approach with additional debugging
    map_to_int = {True: 1, False: 0, 'True': 1, 'False': 0, '1': 1, '0': 0, 1: 1, 0: 0, 1.0: 1, 0.0: 0}
    mapped_series = mrt_data['MRT_isCorrect'].map(map_to_int)
    print(f"DEBUG: mapped_series dtype: {mapped_series.dtype}")
    print(f"DEBUG: mapped_series unique values: {sorted(mapped_series.dropna().unique())}")
    
    numeric_series = pd.to_numeric(mapped_series, errors='coerce')
    print(f"DEBUG: numeric_series dtype after pd.to_numeric: {numeric_series.dtype}")
    
    # Direct assignment to ensure proper conversion
    mrt_data['MRT_isCorrect'] = numeric_series.astype('Int64')
    
    print(f"DEBUG: Dtype of MRT_isCorrect after .astype('Int64'): {mrt_data['MRT_isCorrect'].dtype}")
    print(f"MRT_isCorrect unique values after conversion: {sorted(mrt_data['MRT_isCorrect'].dropna().unique())}")
    print(f"NaN values in MRT_isCorrect after conversion: {mrt_data['MRT_isCorrect'].isnull().sum()}")
    
    # Verify the conversion worked correctly
    actual_dtype = str(mrt_data['MRT_isCorrect'].dtype)
    if actual_dtype not in ['int64', 'Int64']:
        print(f"WARNING: MRT_isCorrect conversion failed, got {actual_dtype} instead of int64/Int64")
        # Force conversion if it failed
        print("Attempting force conversion...")
        mrt_data['MRT_isCorrect'] = pd.to_numeric(mrt_data['MRT_isCorrect'], errors='coerce').astype('Int64')
        print(f"After force conversion: {mrt_data['MRT_isCorrect'].dtype}")
    else:
        print(f"SUCCESS: MRT_isCorrect conversion successful, dtype is {actual_dtype}")
    
    # Test that calculations work properly
    test_mean = mrt_data['MRT_isCorrect'].mean()
    print(f"Test calculation - MRT_isCorrect mean: {test_mean:.3f}")
    
    # Print unique values for key columns
    print("\nUnique values in key columns:")
    print(f"table: {sorted(mrt_data['table'].dropna().unique())}")
    print(f"isPractice: {sorted(mrt_data['isPractice'].dropna().unique())}")
    print(f"MRT_angle_degrees: {sorted(mrt_data['MRT_angle_degrees'].dropna().unique())}")
    print(f"MRT_timeout: {sorted(mrt_data['MRT_timeout'].dropna().unique())}")
    print(f"MRT_isAttentionCheck: {sorted(mrt_data['MRT_isAttentionCheck'].unique())}")
    print(f"MRT_rt_ms data type: {mrt_data['MRT_rt_ms'].dtype}")
    print(f"MRT_isCorrect data type: {mrt_data['MRT_isCorrect'].dtype}")
    
    # Separate practice and test trials
    practice_data = mrt_data[mrt_data['isPractice'] == True].copy()
    test_data = mrt_data[mrt_data['isPractice'] == False].copy()
    
    print(f"Practice trials: {len(practice_data)}")
    print(f"Test trials: {len(test_data)}")
    
    print("\nFirst 2 rows of filtered MRT data:")
    print(mrt_data.head(2))
    
    return mrt_data, test_data, practice_data

def apply_participant_exclusions(test_data):
    """
    Apply participant-level exclusions based on timeout rate and attention check performance.
    
    Exclusion criteria applied:
    1. Timeout rate >20%: Participants who timed out on more than 20% of test trials
    2. Attention check performance <60%: Participants with <60% accuracy on attention check trials
       (minimum 4 attention check trials required for this exclusion)
    
    Parameters:
    test_data (pd.DataFrame): Test trials data
    
    Returns:
    tuple: (excluded_participants set, exclusion_log dict)
    """
    print("\n=== APPLYING PARTICIPANT-LEVEL EXCLUSIONS ===")
    
    excluded_participants = set()
    exclusion_log = {}
    
    # Get unique participants
    if test_data.empty:
        print("No test data available for participant exclusions")
        return set(), {}
    
    participants = test_data['participantId'].unique()
    print(f"Total participants: {len(participants)}")
    
    # 1. Timeout rate exclusion (>20%)
    print("\n1. Checking timeout rates...")
    timeout_excluded = set()
    
    for participant in participants:
        p_data = test_data[test_data['participantId'] == participant]
        total_trials = len(p_data)
        timeout_trials = len(p_data[p_data['MRT_timeout'] == True])
        timeout_rate = timeout_trials / total_trials if total_trials > 0 else 0
        
        if timeout_rate > 0.20:
            timeout_excluded.add(participant)
            print(f"  Participant {participant}: {timeout_rate:.3f} timeout rate (>{timeout_trials}/{total_trials})")
    
    excluded_participants.update(timeout_excluded)
    exclusion_log['timeout_rate_>20%'] = len(timeout_excluded)
    print(f"Participants excluded for timeout rate >20%: {len(timeout_excluded)}")
    
    # 2. Attention check exclusion (<60% correct, minimum 4 trials)
    print("\n2. Checking attention check performance...")
    attention_excluded = set()
    
    for participant in participants:
        if participant in excluded_participants:
            continue
            
        p_data = test_data[test_data['participantId'] == participant]
        attention_data = p_data[p_data['MRT_isAttentionCheck'] == True]
        
        if len(attention_data) >= 4:
            # Use robust numeric conversion for accuracy calculation
            accuracy = pd.to_numeric(attention_data['MRT_isCorrect'], errors='coerce').mean()

            # Check for NaN accuracy (could happen if all values were non-convertible)
            if pd.isna(accuracy):
                print(f"  WARNING: Could not calculate accuracy for participant {participant} - all values non-numeric")
                continue
                
            if accuracy < 0.60:
                attention_excluded.add(participant)
                print(f"  Participant {participant}: {accuracy:.3f} accuracy on attention checks ({len(attention_data)} trials)")
        elif len(attention_data) > 0:
            print(f"  Participant {participant}: Only {len(attention_data)} attention check trials (minimum 4 required)")
    
    excluded_participants.update(attention_excluded)
    exclusion_log['attention_check_<60%'] = len(attention_excluded)
    print(f"Participants excluded for attention check performance <60%: {len(attention_excluded)}")
    
    print(f"\nTotal participants excluded at this stage: {len(excluded_participants)}")
    print(f"Remaining participants: {len(participants) - len(excluded_participants)}")
    
    return excluded_participants, exclusion_log

def apply_trial_exclusions(data, excluded_participants):
    """
    Apply trial-level exclusions for timeout, RT bounds, and practice trials.
    
    Parameters:
    data (pd.DataFrame): Full MRT data
    excluded_participants (set): Set of excluded participant IDs
    
    Returns:
    tuple: (filtered_data, trials_after_exclusions, timeout_trial_count, rt_outlier_trial_count)
        - filtered_data (pd.DataFrame): Data with trial exclusions applied
        - trials_after_exclusions (pd.DataFrame): Valid test trials after exclusions
        - timeout_trial_count (int): Number of timeout trials excluded
        - rt_outlier_trial_count (int): Number of RT outlier trials excluded
    """
    print("\n=== APPLYING TRIAL-LEVEL EXCLUSIONS ===")
    
    # Start with all MRT data
    filtered_data = data.copy()
    
    print(f"Starting with {len(filtered_data)} total MRT trials")
    
    # Mark excluded participants
    filtered_data['excluded_participant'] = filtered_data['participantId'].isin(excluded_participants)
    
    # Only work with test trials from non-excluded participants for further filtering
    test_trials = filtered_data[
        (filtered_data['isPractice'] == False) & 
        (~filtered_data['excluded_participant'])
    ].copy()
    
    print(f"Test trials from valid participants: {len(test_trials)}")
    
    # Apply trial-level exclusions to test trials from valid participants
    trials_after_exclusions = test_trials.copy()
    
    # 1. Exclude timeout trials (trials where participant failed to respond within time limit)
    timeout_exclusion_mask = trials_after_exclusions['MRT_timeout'] == True
    timeout_trial_count = timeout_exclusion_mask.sum()
    print(f"Timeout trials to exclude: {timeout_trial_count}")
    trials_after_exclusions = trials_after_exclusions[~timeout_exclusion_mask]
    
    # 2. Exclude RT outliers (responses <150ms likely anticipatory, >6000ms likely inattentive)
    rt_outlier_exclusion_mask = (trials_after_exclusions['MRT_rt_ms'] < 150) | (trials_after_exclusions['MRT_rt_ms'] > 6000)
    rt_outlier_trial_count = rt_outlier_exclusion_mask.sum()
    print(f"RT outlier trials to exclude: {rt_outlier_trial_count}")
    trials_after_exclusions = trials_after_exclusions[~rt_outlier_exclusion_mask]
    
    print(f"Valid test trials after exclusions: {len(trials_after_exclusions)}")
    
    # Mark valid trials in the full dataset (initialize all as invalid)
    filtered_data['valid_trial'] = False
    
    # Mark valid test trials (passed all exclusion criteria)
    valid_test_trial_indices = filtered_data[
        (filtered_data['isPractice'] == False) & 
        (~filtered_data['excluded_participant']) &
        (filtered_data['MRT_timeout'] != True) &
        (filtered_data['MRT_rt_ms'] >= 150) &
        (filtered_data['MRT_rt_ms'] <= 6000)
    ].index
    
    filtered_data.loc[valid_test_trial_indices, 'valid_trial'] = True
    
    # Practice trials are excluded from analysis dataset, so they remain valid_trial = False
    # Only test trials that pass all exclusion criteria are marked as valid_trial = True
    
    print(f"Total valid trials (test trials only): {filtered_data['valid_trial'].sum()}")
    
    return filtered_data, trials_after_exclusions, timeout_trial_count, rt_outlier_trial_count

def apply_outlier_identification(data, valid_trials):
    """
    Apply outlier identification based on RT and accuracy by rotation angle.
    
    Parameters:
    data (pd.DataFrame): Full filtered data
    valid_trials (pd.DataFrame): Valid test trials
    
    Returns:
    tuple: (updated_data, additional_exclusions, outlier_log)
    """
    print("\n=== APPLYING OUTLIER IDENTIFICATION ===")
    
    outlier_excluded = set()
    outlier_log = {}
    
    # Calculate condition means and SDs for each rotation angle
    angles = [0, 50, 100, 150]
    
    if valid_trials.empty:
        print("No valid trials available for outlier identification")
        return data, set(), {'statistical_outliers': 0, 'insufficient_trials_per_condition': 0}
    
    for angle in angles:
        print(f"\nProcessing {angle}° rotation condition...")
        
        angle_data = valid_trials[valid_trials['MRT_angle_degrees'] == angle]
        print(f"Total trials for {angle}°: {len(angle_data)}")
        
        if len(angle_data) == 0:
            continue
        
        # Calculate RT stats for correct trials only
        correct_trials = angle_data[angle_data['MRT_isCorrect'] == True]
        print(f"Correct trials for {angle}°: {len(correct_trials)}")
        
        if len(correct_trials) > 0:
            # Ensure RT column is numeric for calculations
            rt_values = pd.to_numeric(correct_trials['MRT_rt_ms'], errors='coerce')
            rt_mean = rt_values.mean()
            rt_sd = rt_values.std()
            print(f"RT mean: {rt_mean:.2f}ms, SD: {rt_sd:.2f}ms")
        else:
            rt_mean = np.nan
            rt_sd = np.nan
        
        # Calculate accuracy stats for all trials
        # Ensure MRT_isCorrect is numeric for calculations
        acc_values = pd.to_numeric(angle_data['MRT_isCorrect'], errors='coerce')
        acc_mean = acc_values.mean()
        acc_sd = acc_values.std()
        print(f"Accuracy mean: {acc_mean:.3f}, SD: {acc_sd:.3f}")
        
        # Check each participant's performance in this condition for statistical outliers
        participants_in_condition = angle_data['participantId'].unique()
        
        if len(participants_in_condition) == 0:
            continue
            
        for participant_id in participants_in_condition:
            participant_angle_data = angle_data[angle_data['participantId'] == participant_id]
            
            # Check RT outlier (using correct trials only, as RT analysis should focus on successful responses)
            participant_correct_trials = participant_angle_data[participant_angle_data['MRT_isCorrect'] == 1]
            if (len(participant_correct_trials) > 0 and len(correct_trials) > 0 and 
                rt_sd > 0 and not pd.isna(rt_mean) and not pd.isna(rt_sd)):
                participant_mean_rt = participant_correct_trials['MRT_rt_ms'].mean()
                if not pd.isna(participant_mean_rt):
                    rt_z_score = abs(participant_mean_rt - rt_mean) / rt_sd
                
                    # Exclude participants with RT >3 standard deviations from condition mean
                    if rt_z_score > 3.0:
                        outlier_excluded.add(participant_id)
                        print(f"  RT outlier - Participant {participant_id}: mean RT {participant_mean_rt:.2f}ms (z={rt_z_score:.2f})")
            
            # Check accuracy outlier (using all trials in condition)
            if (len(participant_angle_data) > 0 and acc_sd > 0 and 
                not pd.isna(acc_mean) and not pd.isna(acc_sd)):
                participant_mean_accuracy = pd.to_numeric(participant_angle_data['MRT_isCorrect'], errors='coerce').mean()
                if not pd.isna(participant_mean_accuracy):
                    accuracy_z_score = abs(participant_mean_accuracy - acc_mean) / acc_sd
                    
                    # Exclude participants with accuracy >3 standard deviations from condition mean
                    if accuracy_z_score > 3.0:
                        outlier_excluded.add(participant_id)
                        print(f"  Accuracy outlier - Participant {participant_id}: mean accuracy {participant_mean_accuracy:.3f} (z={accuracy_z_score:.2f})")
    
    outlier_log['statistical_outliers'] = len(outlier_excluded)
    print(f"\nTotal participants excluded as statistical outliers: {len(outlier_excluded)}")
    
    # Update exclusions in the data for statistical outliers
    updated_data = data.copy()
    outlier_mask = updated_data['participantId'].isin(outlier_excluded)
    updated_data.loc[outlier_mask, 'excluded_participant'] = True
    updated_data.loc[outlier_mask, 'valid_trial'] = False
    
    # Apply minimum trial count exclusion (10 per angle condition)
    print("\n=== APPLYING MINIMUM TRIAL COUNT EXCLUSION (10 per angle condition) ===")
    min_trials_excluded_set = set()
    
    # Get valid trials after statistical outlier exclusions
    valid_trials_after_stat_outliers = valid_trials[~valid_trials['participantId'].isin(outlier_excluded)]
    participants_to_check = valid_trials_after_stat_outliers['participantId'].unique()
    
    for p_id in participants_to_check:
        p_trials_for_min_check = valid_trials_after_stat_outliers[valid_trials_after_stat_outliers['participantId'] == p_id]
        for angle_val in angles:
            trials_in_condition = p_trials_for_min_check[p_trials_for_min_check['MRT_angle_degrees'] == angle_val]
            if len(trials_in_condition) < 10:
                min_trials_excluded_set.add(p_id)
                print(f"  Participant {p_id} will be excluded: {len(trials_in_condition)} trials in {angle_val}° condition.")
                break  # Participant excluded, no need to check other conditions
    
    outlier_log['insufficient_trials_per_condition'] = len(min_trials_excluded_set)
    print(f"Participants excluded for insufficient trials per condition: {len(min_trials_excluded_set)}")
    
    # Combine statistical outliers with minimum trials exclusions
    all_newly_excluded_this_step = outlier_excluded.union(min_trials_excluded_set)
    
    # Update exclusions in the data for all newly excluded participants
    newly_excluded_mask = updated_data['participantId'].isin(all_newly_excluded_this_step)
    updated_data.loc[newly_excluded_mask, 'excluded_participant'] = True
    updated_data.loc[newly_excluded_mask, 'valid_trial'] = False
    
    # Check minimum trial requirements
    print("\n=== CHECKING MINIMUM TRIAL REQUIREMENTS ===")
    final_valid = updated_data[
        (updated_data['isPractice'] == False) & 
        (updated_data['valid_trial'] == True)
    ]
    
    for angle in angles:
        angle_trials = final_valid[final_valid['MRT_angle_degrees'] == angle]
        participants_with_trials = angle_trials.groupby('participantId').size()
        sufficient_participants = (participants_with_trials >= 10).sum()
        
        print(f"{angle}° condition: {len(angle_trials)} total trials, "
              f"{len(participants_with_trials)} participants, "
              f"{sufficient_participants} with ≥10 trials")
    
    return updated_data, all_newly_excluded_this_step, outlier_log

def create_exclusion_log(exclusion_counts, total_participants):
    """
    Create exclusion log dataframe.
    
    Parameters:
    exclusion_counts (dict): Dictionary of exclusion criteria and counts
    total_participants (int): Total number of participants
    
    Returns:
    pd.DataFrame: Exclusion log dataframe
    """
    print("\n=== CREATING EXCLUSION LOG ===")
    
    exclusion_data = []
    for criterion, count in exclusion_counts.items():
        # Ensure count is numeric and handle potential None values
        count = int(count) if count is not None else 0
        percentage = (count / total_participants) * 100 if total_participants > 0 else 0
        exclusion_data.append({
            'exclusion_criterion': criterion,
            'total_excluded': count,
            'percentage_excluded': float(percentage)
        })
        print(f"{criterion}: {count} participants ({percentage:.1f}%)")
    
    return pd.DataFrame(exclusion_data)

def main():
    """
    Main function to execute the MRT data cleaning pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("=== MRT DATA CLEANING SCRIPT ===")
        print(f"Start time: {datetime.now()}")
        
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Load data
        file_pattern = "raw_data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        raw_data, num_files_processed = load_mrt_data(file_pattern)
        
        if raw_data.empty:
            print("No data loaded. Exiting.")
            return 1
        
        # Count initial participants before filtering
        initial_raw_participants = len(raw_data['participantId'].unique()) if 'participantId' in raw_data.columns else 0
        
        # Filter MRT data
        mrt_data_df, test_data_df, practice_data_df = filter_mrt_data(raw_data)
        
        if mrt_data_df.empty:
            print("No MRT data found or critical columns missing. Exiting.")
            return 1
        
        # Assign for consistency with rest of code
        mrt_data = mrt_data_df
        test_data = test_data_df
        practice_data = practice_data_df
        
        # Apply participant-level exclusions
        excluded_participants, exclusion_log = apply_participant_exclusions(test_data)
        
        # Apply trial-level exclusions
        filtered_data, valid_trials, timeout_trial_exclusions, rt_trial_exclusions = apply_trial_exclusions(mrt_data, excluded_participants)
        
        # Apply outlier identification
        final_data, new_exclusions_from_outlier_step, outlier_log = apply_outlier_identification(filtered_data, valid_trials)
        
        # Combine all exclusion logs
        total_participants = len(mrt_data['participantId'].unique())
        all_exclusions = {**exclusion_log, **outlier_log}
        
        # Add total exclusions
        all_excluded = excluded_participants.union(new_exclusions_from_outlier_step)
        all_exclusions['total_excluded_participants'] = len(all_excluded)
        
        exclusion_df = create_exclusion_log(all_exclusions, total_participants)
        
        # Prepare final output data with proper data types
        output_cols = ['participantId', 'table', 'MRT_trial', 'MRT_angle_degrees', 
                       'MRT_isCorrect', 'MRT_rt_ms', 'MRT_timeout', 'MRT_isAttentionCheck',
                       'isPractice', 'excluded_participant', 'valid_trial']
        
        final_output = final_data[output_cols].copy()
        
        # Ensure boolean columns maintain proper boolean data types for output
        boolean_columns_spec = {'MRT_timeout': bool, 'MRT_isAttentionCheck': bool, 'isPractice': bool, 'excluded_participant': bool, 'valid_trial': bool, 'MRT_isCorrect': 'boolean'}
        for col, target_dtype in boolean_columns_spec.items():
            if col in final_output.columns:
                if target_dtype == 'boolean':
                    # Handle MRT_isCorrect specially with nullable boolean
                    print(f"DEBUG: {col} dtype before conversion: {final_output[col].dtype}")
                    print(f"DEBUG: {col} unique values before conversion: {sorted(final_output[col].dropna().unique())}")
                    map_to_nullable_bool = {0: False, 1: True}
                    final_output[col] = final_output[col].map(map_to_nullable_bool).astype('boolean')
                    print(f"Ensured {col} is nullable boolean type: {final_output[col].dtype}")
                else:
                    # Convert to standard boolean directly, handling NaNs appropriately
                    final_output[col] = final_output[col].astype(bool)
                    print(f"Ensured {col} is boolean type: {final_output[col].dtype}")
                # Verify boolean values are actually True/False
                unique_vals = final_output[col].unique()
                print(f"  {col} unique values: {sorted(unique_vals)}")
        
        # Ensure MRT_angle_degrees is integer type for output
        if 'MRT_angle_degrees' in final_output.columns:
            # Convert to numeric first, then to proper integer type
            numeric_angles = pd.to_numeric(final_output['MRT_angle_degrees'], errors='coerce')
            # Always use Int64 to ensure integer type
            final_output['MRT_angle_degrees'] = numeric_angles.astype('Int64')
            print(f"Ensured MRT_angle_degrees is integer type: {final_output['MRT_angle_degrees'].dtype}")
            print(f"  MRT_angle_degrees unique values: {sorted(final_output['MRT_angle_degrees'].dropna().unique())}")
        
        # Debug check for MRT_isAttentionCheck NaNs before saving
        print(f"NaNs in final_output MRT_isAttentionCheck: {final_output['MRT_isAttentionCheck'].isnull().sum()}")
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save outputs
        data_filename = f"outputs/MRT_cleaned_data_{timestamp}.csv"
        log_filename = f"outputs/MRT_exclusion_log_{timestamp}.csv"
        
        print(f"\n=== SAVING OUTPUTS ===")
        print(f"Saving cleaned data to: {data_filename}")
        
        # Print final data types before saving
        print("Final data types before saving:")
        for col in final_output.columns:
            print(f"  {col}: {final_output[col].dtype}")
        
        # Save directly with proper data types, using na_rep for clarity of missing values
        final_output.to_csv(data_filename, index=False, na_rep='NA')
        print("Saved CSV with proper data types")
        
        print(f"Saving exclusion log to: {log_filename}")
        exclusion_df.to_csv(log_filename, index=False)
        
        # Final summary
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total participants: {total_participants}")
        print(f"Excluded participants: {len(all_excluded)}")
        print(f"Remaining participants: {total_participants - len(all_excluded)}")
        print(f"Total MRT trials: {len(final_output)}")
        print(f"Valid trials: {final_output['valid_trial'].sum()}")
        
        # Flag high attention check exclusion rate
        attention_exclusion_rate = (exclusion_log.get('attention_check_<60%', 0) / total_participants) * 100
        if attention_exclusion_rate > 25:
            print(f"\nWARNING: High attention check exclusion rate ({attention_exclusion_rate:.1f}%)")
            print("Consider reviewing the 60% accuracy threshold if this exclusion rate is excessive.")
        
        # Detailed final summary as required
        print(f"\n=== DETAILED DATA PROCESSING PIPELINE SUMMARY ===")
        print(f"Initial dataset: {num_files_processed} files processed, {initial_raw_participants} total participants")
        print(f"Participants with MRT data: {total_participants} (excluded {initial_raw_participants - total_participants} with no MRT task data)")
        print(f"Total MRT trials found: {len(final_output)}")
        print(f"Participant-level exclusions applied:")
        print(f"  - Timeout rate >20%: {exclusion_log.get('timeout_rate_>20%', 0)} participants")
        print(f"  - Attention check accuracy <60%: {exclusion_log.get('attention_check_<60%', 0)} participants")
        print(f"  - Statistical outliers (RT/accuracy): {outlier_log.get('statistical_outliers', 0)} participants")
        print(f"  - Insufficient trials per condition (<10): {outlier_log.get('insufficient_trials_per_condition', 0)} participants")
        print(f"Trial-level exclusions applied:")
        print(f"  - Timeout trials excluded: {timeout_trial_exclusions}")
        print(f"  - RT outlier trials excluded: {rt_trial_exclusions}")
        print(f"Total excluded: {len(all_excluded)} participants ({(len(all_excluded)/total_participants)*100:.1f}%)")
        print(f"Final clean dataset: {total_participants - len(all_excluded)} participants with {final_output['valid_trial'].sum()} valid trials")
        
        # Trial-level exclusion summary
        total_test_trials = len(final_output[(final_output['isPractice'] == False)])
        valid_test_trials = len(final_output[(final_output['isPractice'] == False) & (final_output['valid_trial'] == True)])
        print(f"Test trial retention rate: {valid_test_trials}/{total_test_trials} ({(valid_test_trials/total_test_trials)*100:.1f}%)")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
