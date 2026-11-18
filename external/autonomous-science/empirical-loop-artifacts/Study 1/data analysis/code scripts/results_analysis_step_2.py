#!/usr/bin/env python3
"""
VWM Data Cleaning Script

This script processes Visual Working Memory (VWM) task data from interleaved task CSV files.
It applies participant-level and trial-level exclusions according to specified criteria,
and outputs cleaned data with exclusion documentation.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def create_outputs_directory():
    """
    Create outputs directory if it doesn't exist.
    
    Returns:
        None
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")

def load_vwm_data():
    """
    Load and combine all VWM data files matching the specified pattern.
    
    Returns:
        pd.DataFrame: Combined dataframe with all VWM data
    """
    print("Loading VWM data files...")
    
    # Find all matching files
    file_pattern = "raw_data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    files = glob.glob(file_pattern)
    
    print(f"Found {len(files)} matching files:")
    for file in files:
        print(f"  - {file}")
    
    if not files:
        print("ERROR: No matching files found!")
        return None
    
    # Load and combine all files
    all_data = []
    
    incomplete_files = 0
    for i, file in enumerate(files):
        try:
            if i < 3:  # Show details for first 3 files only
                print(f"\nProcessing file: {file}")
            elif i == 3:
                print(f"\n... processing remaining {len(files) - 3} files (details suppressed for brevity) ...")
            
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            
            if i < 3:  # Show details for first 3 files only
                print(f"File shape: {df.shape}")
                print("All columns:")
                print(df.columns.tolist())
                print("\nFirst 3 rows:")
                print(df.head(3))
            
            # Check if file has minimum required structure
            if len(df) == 0 or 'table' not in df.columns:
                incomplete_files += 1
                if i < 3:
                    print(f"Warning: File appears incomplete or malformed")
                continue
            
            all_data.append(df)
            
        except Exception as e:
            incomplete_files += 1
            if i < 3:
                print(f"Error loading {file}: {e}")
            continue

    print(f"\nFile loading summary: {len(all_data)} files loaded successfully, {incomplete_files} files incomplete/failed")
    
    if not all_data:
        print("ERROR: No files could be loaded!")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined dataset shape: {combined_df.shape}")
    
    return combined_df

def filter_vwm_data(df):
    """
    Filter data to extract only VWM task rows.
    
    Args:
        df (pd.DataFrame): Combined raw data
        
    Returns:
        pd.DataFrame: Filtered VWM data
    """
    print("\nFiltering VWM data...")
    
    # Check if 'table' column exists
    if 'table' not in df.columns:
        print("ERROR: 'table' column not found in data!")
        return None
    
    print("Unique values in 'table' column:")
    print(df['table'].unique())
    
    # Filter for VWM rows (case-insensitive)
    vwm_mask = df['table'].str.contains('vwm', case=False, na=False)
    vwm_data = df[vwm_mask].copy()
    
    print(f"VWM data shape after filtering: {vwm_data.shape}")
    
    # Handle NaNs in VWM_isAttentionCheck and ensure boolean types
    if 'VWM_isAttentionCheck' in vwm_data.columns:
        nan_count = vwm_data['VWM_isAttentionCheck'].isna().sum()
        if nan_count > 0:
            print(f"Info: Found {nan_count} NaN values in 'VWM_isAttentionCheck' for VWM trials. Converting to False.")
            vwm_data['VWM_isAttentionCheck'] = vwm_data['VWM_isAttentionCheck'].fillna(False)
            vwm_data['VWM_isAttentionCheck'] = vwm_data['VWM_isAttentionCheck'].infer_objects(copy=False)
    
    # Ensure critical columns are boolean type for consistent processing
    for col_name in ['isPractice', 'VWM_timeout', 'VWM_isAttentionCheck']:
        if col_name in vwm_data.columns:
            vwm_data[col_name] = vwm_data[col_name].astype(bool)
    
    # Check required columns
    required_cols = [
        'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_setSize',
        'VWM_delay_s', 'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_timeout',
        'VWM_isAttentionCheck', 'taskOrder'
    ]
    
    missing_cols = [col for col in required_cols if col not in vwm_data.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        return None
    
    print("All required columns present")
    
    # Print unique values for key experimental design parameters
    print("\nUnique values for key experimental parameters:")
    print(f"VWM_setSize: {sorted(vwm_data['VWM_setSize'].dropna().unique())}")
    print(f"VWM_delay_s: {sorted(vwm_data['VWM_delay_s'].dropna().unique())}")
    print(f"isPractice: {sorted(vwm_data['isPractice'].dropna().unique())}")
    print(f"VWM_isAttentionCheck: {sorted(vwm_data['VWM_isAttentionCheck'].dropna().unique())}")
    print(f"taskOrder: {sorted(vwm_data['taskOrder'].dropna().unique())}")
    
    # Print data types for measured variables
    print(f"\nData types for measured variables:")
    print(f"VWM_error_absolute_degrees: {vwm_data['VWM_error_absolute_degrees'].dtype}")
    print(f"VWM_rt_ms: {vwm_data['VWM_rt_ms'].dtype}")
    
    return vwm_data

def separate_practice_test_trials(vwm_data):
    """
    Separate practice and test trials.
    
    Args:
        vwm_data (pd.DataFrame): VWM data
        
    Returns:
        tuple: (practice_data, test_data)
    """
    print("\nSeparating practice and test trials...")
    
    practice_data = vwm_data[vwm_data['isPractice'] == True].copy()
    test_data = vwm_data[vwm_data['isPractice'] == False].copy()
    
    print(f"Practice trials: {len(practice_data)}")
    print(f"Test trials: {len(test_data)}")
    
    return practice_data, test_data

def apply_participant_exclusions(test_data):
    """
    Apply participant-level exclusions based on timeout rate, easiest condition performance,
    and attention check accuracy.
    
    Args:
        test_data (pd.DataFrame): Test trial data
        
    Returns:
        tuple: (cleaned_test_data, exclusion_log)
    """
    print("\nApplying participant-level exclusions...")
    
    exclusion_log = []
    excluded_participants = set()
    
    # Get unique participants
    participants = test_data['participantId'].unique()
    print(f"Total participants: {len(participants)}")
    
    # 1. Timeout rate exclusion (>20%)
    print("\n1. Checking timeout rates...")
    timeout_excluded = []
    
    for participant in participants:
        p_data = test_data[test_data['participantId'] == participant]
        total_trials = len(p_data)
        timeout_trials = p_data['VWM_timeout'].sum()
        timeout_rate = timeout_trials / total_trials if total_trials > 0 else 0
        
        if timeout_rate > 0.20:
            timeout_excluded.append(participant)
            excluded_participants.add(participant)
            print(f"  Excluding {participant}: timeout rate = {timeout_rate:.3f} ({timeout_trials}/{total_trials})")
    
    exclusion_log.append({
        'exclusion_criterion': 'Timeout rate >20%',
        'total_excluded': len(timeout_excluded),
        'percentage_excluded': len(timeout_excluded) / len(participants) * 100
    })
    
    print(f"Excluded {len(timeout_excluded)} participants for high timeout rate")
    remaining_after_timeout = len(participants) - len(excluded_participants)
    print(f"Participants remaining after timeout exclusion: {remaining_after_timeout}")
    
    # 2. Easiest condition performance (SS2, D1000ms, >50° error)
    print("\n2. Checking performance in easiest condition (SS2, D1000ms)...")
    easiest_excluded = []
    
    for participant in participants:
        if participant in excluded_participants:
            continue
            
        p_data = test_data[test_data['participantId'] == participant]
        easiest_data = p_data[
            (p_data['VWM_setSize'] == 2) & 
            (p_data['VWM_delay_s'] == 1.0)
        ]
        
        if len(easiest_data) > 0:
            mean_error = easiest_data['VWM_error_absolute_degrees'].mean()
            if pd.notna(mean_error) and mean_error > 50:
                easiest_excluded.append(participant)
                excluded_participants.add(participant)
                print(f"  Excluding {participant}: mean error in easiest condition = {mean_error:.2f}°")
    
    exclusion_log.append({
        'exclusion_criterion': 'Mean error >50° in easiest condition',
        'total_excluded': len(easiest_excluded),
        'percentage_excluded': len(easiest_excluded) / len(participants) * 100
    })
    
    print(f"Excluded {len(easiest_excluded)} participants for poor performance in easiest condition")
    remaining_after_easiest = len(participants) - len(excluded_participants)
    print(f"Participants remaining after easiest condition exclusion: {remaining_after_easiest}")
    
    # 3. Attention check accuracy (<60% correct, minimum 4 trials)
    print("\n3. Checking attention check performance...")
    attention_excluded = []
    
    for participant in participants:
        if participant in excluded_participants:
            continue
            
        p_data = test_data[test_data['participantId'] == participant]
        attention_data = p_data[p_data['VWM_isAttentionCheck'] == True]
        
        if len(attention_data) >= 4:  # Minimum 4 attention check trials required
            correct_trials = (attention_data['VWM_error_absolute_degrees'] <= 30).sum()
            accuracy = correct_trials / len(attention_data)
            
            if accuracy < 0.60:
                attention_excluded.append(participant)
                excluded_participants.add(participant)
                print(f"  Excluding {participant}: attention check accuracy = {accuracy:.3f} ({correct_trials}/{len(attention_data)})")
        elif len(attention_data) > 0:
            print(f"  {participant}: Only {len(attention_data)} attention check trials (minimum 4 required)")
    
    exclusion_log.append({
        'exclusion_criterion': 'Attention check accuracy <60%',
        'total_excluded': len(attention_excluded),
        'percentage_excluded': len(attention_excluded) / len(participants) * 100
    })
    
    print(f"Excluded {len(attention_excluded)} participants for poor attention check performance")
    remaining_after_attention = len(participants) - len(excluded_participants)
    print(f"Participants remaining after attention check exclusion: {remaining_after_attention}")
    
    # Create cleaned dataset
    cleaned_test_data = test_data[~test_data['participantId'].isin(excluded_participants)].copy()
    
    print(f"\nRemaining participants after all participant-level exclusions: {len(cleaned_test_data['participantId'].unique())}")
    
    return cleaned_test_data, exclusion_log

def apply_trial_exclusions(test_data):
    """
    Apply trial-level exclusions for timeout and RT criteria.
    
    Args:
        test_data (pd.DataFrame): Test trial data
        
    Returns:
        tuple: (cleaned_data, additional_exclusion_log)
    """
    print("\nApplying trial-level exclusions...")
    
    initial_trials = len(test_data)
    exclusion_log = []
    
    # 1. Exclude timeout trials
    print("1. Excluding timeout trials...")
    timeout_trials = test_data['VWM_timeout'].sum()
    test_data_no_timeout = test_data[test_data['VWM_timeout'] == False].copy()
    
    exclusion_log.append({
        'exclusion_criterion': 'Timeout trials',
        'total_excluded': timeout_trials,
        'percentage_excluded': timeout_trials / initial_trials * 100
    })
    
    print(f"Excluded {timeout_trials} timeout trials")
    
    # 2. Exclude RT outliers (<150ms or >6000ms)
    print("2. Excluding RT outliers...")
    rt_valid = (test_data_no_timeout['VWM_rt_ms'] >= 150) & (test_data_no_timeout['VWM_rt_ms'] <= 6000)
    rt_excluded = (~rt_valid).sum()
    test_data_clean = test_data_no_timeout[rt_valid].copy()
    
    exclusion_log.append({
        'exclusion_criterion': 'RT <150ms or >6000ms',
        'total_excluded': rt_excluded,
        'percentage_excluded': rt_excluded / len(test_data_no_timeout) * 100
    })
    
    print(f"Excluded {rt_excluded} trials for RT criteria")
    
    print(f"Remaining trials after trial-level exclusions: {len(test_data_clean)}")
    
    return test_data_clean, exclusion_log

def apply_outlier_exclusions(test_data):
    """
    Apply outlier exclusions based on condition means and verify minimum trials per condition.
    
    Args:
        test_data (pd.DataFrame): Test trial data
        
    Returns:
        tuple: (final_cleaned_data, additional_exclusion_log)
    """
    print("\nApplying outlier exclusions...")
    
    exclusion_log = []
    
    # Define the four main conditions
    conditions = [
        {'setSize': 2, 'delay': 1.0, 'name': 'SS2/D1000'},
        {'setSize': 2, 'delay': 4.0, 'name': 'SS2/D4000'},
        {'setSize': 4, 'delay': 1.0, 'name': 'SS4/D1000'},
        {'setSize': 4, 'delay': 4.0, 'name': 'SS4/D4000'}
    ]
    
    # Calculate condition means and SDs
    print("Calculating condition means and standard deviations...")
    condition_stats = {}
    
    for condition in conditions:
        cond_data = test_data[
            (test_data['VWM_setSize'] == condition['setSize']) & 
            (test_data['VWM_delay_s'] == condition['delay'])
        ]
        
        if len(cond_data) > 0:
            mean_error = cond_data['VWM_error_absolute_degrees'].mean()
            std_error = cond_data['VWM_error_absolute_degrees'].std()
            
            condition_stats[condition['name']] = {
                'mean': mean_error,
                'std': std_error,
                'n_trials': len(cond_data)
            }
            
            print(f"  {condition['name']}: mean = {mean_error:.2f}°, SD = {std_error:.2f}°, n = {len(cond_data)}")
    
    # Identify outlier participants
    print("\nIdentifying outlier participants...")
    participants = test_data['participantId'].unique()
    outlier_participants = set()
    
    for participant in participants:
        p_data = test_data[test_data['participantId'] == participant]
        is_outlier = False
        
        for condition in conditions:
            cond_name = condition['name']
            if cond_name not in condition_stats:
                continue
                
            p_cond_data = p_data[
                (p_data['VWM_setSize'] == condition['setSize']) & 
                (p_data['VWM_delay_s'] == condition['delay'])
            ]
            
            if len(p_cond_data) > 0:
                p_mean_error = p_cond_data['VWM_error_absolute_degrees'].mean()
                
                if pd.notna(p_mean_error):
                    z_score = (p_mean_error - condition_stats[cond_name]['mean']) / condition_stats[cond_name]['std']
                    
                    if abs(z_score) > 3.0:
                        print(f"  Excluding {participant}: {cond_name} mean = {p_mean_error:.2f}° (z = {z_score:.2f})")
                        is_outlier = True
                        break
        
        if is_outlier:
            outlier_participants.add(participant)
    
    exclusion_log.append({
        'exclusion_criterion': 'Outlier performance (>3SD from condition mean)',
        'total_excluded': len(outlier_participants),
        'percentage_excluded': len(outlier_participants) / len(participants) * 100
    })
    
    print(f"Excluded {len(outlier_participants)} participants as outliers")
    
    # Remove outlier participants
    final_data = test_data[~test_data['participantId'].isin(outlier_participants)].copy()
    
    # Verify minimum trials per condition
    print("\nVerifying minimum trials per condition...")
    final_participants = final_data['participantId'].unique()
    insufficient_participants = set()
    
    for participant in final_participants:
        p_data = final_data[final_data['participantId'] == participant]
        
        for condition in conditions:
            p_cond_data = p_data[
                (p_data['VWM_setSize'] == condition['setSize']) & 
                (p_data['VWM_delay_s'] == condition['delay'])
            ]
            
            if len(p_cond_data) < 15:  # Minimum 15 valid trials per condition
                print(f"  {participant}: Only {len(p_cond_data)} trials in {condition['name']} (minimum 15 required)")
                insufficient_participants.add(participant)
                break
    
    if insufficient_participants:
        exclusion_log.append({
            'exclusion_criterion': 'Insufficient trials per condition (<15)',
            'total_excluded': len(insufficient_participants),
            'percentage_excluded': len(insufficient_participants) / len(final_participants) * 100
        })
        
        print(f"Excluded {len(insufficient_participants)} participants for insufficient trials")
        final_data = final_data[~final_data['participantId'].isin(insufficient_participants)].copy()
    
    print(f"\nFinal participants after all exclusions: {len(final_data['participantId'].unique())}")
    
    return final_data, exclusion_log

def create_final_dataset(practice_data, final_test_data, all_excluded_participants):
    """
    Create the final dataset with exclusion flags.
    
    Args:
        practice_data (pd.DataFrame): Practice trial data
        final_test_data (pd.DataFrame): Final cleaned test data
        all_excluded_participants (set): Set of all excluded participant IDs
        
    Returns:
        pd.DataFrame: Final dataset with exclusion flags
    """
    print("\nCreating final dataset...")
    
    # Combine practice and test data
    all_data = pd.concat([practice_data, final_test_data], ignore_index=True)
    
    # Add exclusion flags - create as boolean from start
    all_data['excluded_participant'] = all_data['participantId'].isin(all_excluded_participants).astype(bool)
    
    # Add valid trial flag (test trials from non-excluded participants, excluding timeouts and RT outliers)
    all_data['valid_trial'] = (
        (~all_data['excluded_participant']) &
        (all_data['isPractice'] == False) &
        (all_data['VWM_timeout'] == False) &
        (all_data['VWM_rt_ms'] >= 150) &
        (all_data['VWM_rt_ms'] <= 6000)
    ).astype(bool)
    
    # Ensure correct data types for the output CSV
    all_data['participantId'] = all_data['participantId'].astype(str)
    all_data['table'] = all_data['table'].astype(str)
    all_data['taskOrder'] = all_data['taskOrder'].astype(str)
    all_data['VWM_setSize'] = all_data['VWM_setSize'].astype(int)
    
    # Ensure boolean columns are properly typed - create as boolean from start
    bool_cols_to_convert = ['VWM_timeout', 'VWM_isAttentionCheck', 'isPractice', 'excluded_participant', 'valid_trial']
    for col_name in bool_cols_to_convert:
        if col_name in all_data.columns:
            all_data[col_name] = all_data[col_name].astype(bool)
    
    # Select required output columns
    output_cols = [
        'participantId', 'table', 'taskOrder', 'VWM_trial', 'VWM_setSize',
        'VWM_delay_s', 'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_timeout',
        'VWM_isAttentionCheck', 'isPractice', 'excluded_participant', 'valid_trial'
    ]
    
    final_dataset = all_data[output_cols].copy()
    
    # Final data type enforcement for CSV output
    final_dataset['participantId'] = final_dataset['participantId'].astype(str)
    final_dataset['table'] = final_dataset['table'].astype(str)
    final_dataset['taskOrder'] = final_dataset['taskOrder'].astype(str)
    final_dataset['VWM_setSize'] = final_dataset['VWM_setSize'].astype(int)
    
    # Ensure boolean columns are written as True/False in CSV
    bool_columns = ['VWM_timeout', 'VWM_isAttentionCheck', 'isPractice', 'excluded_participant', 'valid_trial']
    for col in bool_columns:
        if col in final_dataset.columns:
            final_dataset[col] = final_dataset[col].astype(bool)
    
    print(f"Final dataset shape: {final_dataset.shape}")
    print(f"Valid trials: {final_dataset['valid_trial'].sum()}")
    print(f"Excluded participants: {final_dataset['excluded_participant'].sum()}")
    
    return final_dataset

def save_outputs(final_dataset, all_exclusion_logs):
    """
    Save the cleaned dataset and exclusion log.
    
    Args:
        final_dataset (pd.DataFrame): Final cleaned dataset
        all_exclusion_logs (list): List of exclusion log entries
        
    Returns:
        None
    """
    print("\nSaving outputs...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save cleaned data with proper data types
    data_filename = f"outputs/VWM_cleaned_data_{timestamp}.csv"
    final_dataset.to_csv(data_filename, index=False)
    print(f"Saved cleaned data to: {data_filename}")
    
    # Print data type verification
    print(f"Data types in saved CSV:")
    for col in final_dataset.columns:
        print(f"  {col}: {final_dataset[col].dtype}")
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(all_exclusion_logs)
    log_filename = f"outputs/VWM_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(log_filename, index=False)
    print(f"Saved exclusion log to: {log_filename}")
    
    # Print exclusion summary
    print("\nExclusion Summary:")
    for log_entry in all_exclusion_logs:
        print(f"  {log_entry['exclusion_criterion']}: {log_entry['total_excluded']} ({log_entry['percentage_excluded']:.1f}%)")

def main():
    """
    Main function to execute the VWM data cleaning pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM data cleaning script...")
        
        # Create outputs directory
        create_outputs_directory()
        
        # Load data
        raw_data = load_vwm_data()
        if raw_data is None:
            return 1
        
        # Filter VWM data
        vwm_data = filter_vwm_data(raw_data)
        if vwm_data is None:
            return 1
        
        # Separate practice and test trials
        practice_data, test_data = separate_practice_test_trials(vwm_data)
        
        # Apply participant-level exclusions
        cleaned_test_data, participant_exclusions = apply_participant_exclusions(test_data)
        
        # Apply trial-level exclusions
        trial_cleaned_data, trial_exclusions = apply_trial_exclusions(cleaned_test_data)
        
        # Apply outlier exclusions
        final_test_data, outlier_exclusions = apply_outlier_exclusions(trial_cleaned_data)
        
        # Get all excluded participants
        all_excluded_participants = set(test_data['participantId'].unique()) - set(final_test_data['participantId'].unique())
        
        # Create final dataset
        final_dataset = create_final_dataset(practice_data, final_test_data, all_excluded_participants)
        
        # Combine all exclusion logs
        all_exclusion_logs = participant_exclusions + trial_exclusions + outlier_exclusions
        
        # Save outputs
        save_outputs(final_dataset, all_exclusion_logs)
        
        # Print comprehensive final summary
        print("\n--- FINAL DATA CLEANING SUMMARY ---")
        print(f"Initial total rows loaded from all files: {raw_data.shape[0]}")
        print(f"Total rows filtered for VWM task: {vwm_data.shape[0]}")
        initial_vwm_participants = len(vwm_data['participantId'].unique())
        print(f"Initial unique participants in VWM data (practice & test): {initial_vwm_participants}")
        initial_test_participants = len(test_data['participantId'].unique())
        print(f"Initial unique participants in VWM test trials: {initial_test_participants}")
        
        print("\nExclusion Details:")
        for log_entry in all_exclusion_logs:
            criterion = log_entry['exclusion_criterion']
            # More specific matching for trial-level exclusions
            is_trial_level = ("Timeout trials" in criterion) or ("RT <150ms or >6000ms" in criterion)
            is_participant_level = any(kw in criterion for kw in [">20%", ">50°", "<60%", ">3SD", "<15"])
            
            if is_trial_level:
                type_label = "Trials"
            elif is_participant_level:
                type_label = "Participants"
            else:
                type_label = "Unknown Type"
            
            print(f"  {type_label} excluded - {criterion}: {log_entry['total_excluded']} ({log_entry['percentage_excluded']:.2f}%)")
        
        final_retained_participants_count = len(final_test_data['participantId'].unique())
        total_unique_excluded_test_participants = initial_test_participants - final_retained_participants_count
        print(f"\nTotal unique participants excluded from test data analysis: {total_unique_excluded_test_participants}")
        print(f"Final VWM analysis dataset: {final_dataset['valid_trial'].sum()} valid test trials from {final_retained_participants_count} participants")
        print(f"The output VWM_cleaned_data.csv contains {len(final_dataset)} rows (includes practice trials and data from excluded participants marked invalid)")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
