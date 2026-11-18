#!/usr/bin/env python3
"""
MRT Data Cleaning Script

This script processes Mental Rotation Task (MRT) data from multiple participant files,
applies exclusion criteria, and outputs cleaned data with exclusion tracking.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def get_timestamp():
    """
    Generate timestamp string for output files.
    
    Returns:
        str: Timestamp in YYYYMMDD_HHMMSS format
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def load_mrt_data(file_pattern):
    """
    Load and combine MRT data from multiple participant files.
    
    Args:
        file_pattern (str): Glob pattern for input files
        
    Returns:
        pandas.DataFrame: Combined dataframe with all participant data
        list: List of successfully loaded files
    """
    print("Starting data loading process...")
    print(f"Searching for files matching pattern: {file_pattern}")
    
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} files matching pattern")
    
    if not files:
        print("ERROR: No files found matching the specified pattern")
        return None, []
    
    # Sort files to ensure consistent processing order
    files.sort()
    print("Files to process:")
    for f in files:
        print(f"  - {f}")
    
    combined_data = []
    loaded_files = []
    
    required_columns = [
        'participantId', 'table', 'isPractice', 'MRT_trial', 'MRT_stimulusId',
        'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response', 'MRT_isCorrect',
        'MRT_rt_ms', 'MRT_timeout', 'MRT_block', 'MRT_isAttentionCheck'
    ]
    
    for file in files:
        print(f"\nProcessing file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File loaded successfully. Shape: {df.shape}")
            print("All columns in file:")
            print(list(df.columns))
            print("First 3 rows:")
            print(df.head(3))
            
            # Check for required columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"WARNING: Missing required columns in {file}: {missing_cols}")
                print("Skipping this file...")
                continue
            
            # Identify MRT task rows (rows where MRT columns have data)
            # Use MRT_trial as indicator - if it's not null, this is an MRT row
            mrt_rows = df['MRT_trial'].notna()
            mrt_data = df[mrt_rows].copy()
            
            print(f"Found {len(mrt_data)} MRT task rows out of {len(df)} total rows")
            
            if len(mrt_data) > 0:
                combined_data.append(mrt_data)
                loaded_files.append(file)
                print("MRT data from this file added to combined dataset")
            else:
                print("No MRT data found in this file")
                
        except Exception as e:
            print(f"ERROR loading file {file}: {str(e)}")
            continue
    
    if not combined_data:
        print("ERROR: No valid MRT data found in any files")
        return None, []
    
    # Combine all data
    final_df = pd.concat(combined_data, ignore_index=True)
    print(f"\nCombined dataset created. Final shape: {final_df.shape}")
    print("Final combined data columns:")
    print(list(final_df.columns))
    print("First 2 rows of combined data:")
    print(final_df.head(2))
    
    return final_df, loaded_files

def print_data_overview(df):
    """
    Print overview of key experimental design parameters.
    
    Args:
        df (pandas.DataFrame): Input dataframe
    """
    print("\n=== DATA OVERVIEW ===")
    print(f"Total rows: {len(df)}")
    print(f"Total participants: {df['participantId'].nunique()}")
    
    print("\nKey experimental design parameters:")
    
    # isPractice values
    print("isPractice values:")
    print(df['isPractice'].value_counts(dropna=False))
    
    # MRT_angle_degrees values
    print("\nMRT_angle_degrees values:")
    print(df['MRT_angle_degrees'].value_counts(dropna=False))
    
    # MRT_isReflected values
    print("\nMRT_isReflected values:")
    print(df['MRT_isReflected'].value_counts(dropna=False))
    
    # MRT_response values
    print("\nMRT_response values:")
    print(df['MRT_response'].value_counts(dropna=False))
    
    # MRT_isCorrect values
    print("\nMRT_isCorrect values:")
    print(df['MRT_isCorrect'].value_counts(dropna=False))
    
    # MRT_timeout values
    print("\nMRT_timeout values:")
    print(df['MRT_timeout'].value_counts(dropna=False))
    
    # MRT_rt_ms type (not unique values as too many)
    print(f"\nMRT_rt_ms data type: {df['MRT_rt_ms'].dtype}")
    print(f"MRT_rt_ms non-null count: {df['MRT_rt_ms'].count()}")
    print(f"MRT_rt_ms range: {df['MRT_rt_ms'].min()} to {df['MRT_rt_ms'].max()}")

def apply_exclusions(df):
    """
    Apply all exclusion criteria and track reasons.
    
    Args:
        df (pandas.DataFrame): Input dataframe
        
    Returns:
        pandas.DataFrame: Dataframe with exclusion columns added
        dict: Exclusion summary statistics
    """
    print("\n=== APPLYING EXCLUSIONS ===")
    
    # Initialize exclusion tracking
    df = df.copy()
    df['excluded'] = False
    df['exclusion_reason'] = ''
    
    exclusion_stats = {
        'practice_trials': 0,
        'timeout_rate_high': set(),
        'accuracy_low': set(),
        'missing_data': set(),
        'rt_too_fast': 0,
        'timeout_trials': 0,
        'missing_response': 0,
        'cv_high': set(),
        'invalid_response': 0
    }
    
    print(f"Starting with {len(df)} total rows")
    
    # Step 1: Remove practice trials
    print("\nStep 1: Removing practice trials...")
    practice_mask = df['isPractice'] == True
    practice_count = practice_mask.sum()
    df.loc[practice_mask, 'excluded'] = True
    df.loc[practice_mask, 'exclusion_reason'] = 'practice_trial'
    exclusion_stats['practice_trials'] = practice_count
    print(f"Excluded {practice_count} practice trials")
    
    # Work with non-practice data for participant-level exclusions
    non_practice = df[~practice_mask].copy()
    print(f"Remaining non-practice rows: {len(non_practice)}")
    
    # Step 2: Participant-level exclusions
    print("\nStep 2: Participant-level exclusions...")
    
    participants = non_practice['participantId'].unique()
    print(f"Total participants to evaluate: {len(participants)}")
    
    for participant in participants:
        p_data = non_practice[non_practice['participantId'] == participant]
        exclude_participant = False
        reasons = []
        
        # 2a: Timeout rate check
        total_trials = len(p_data)
        timeout_trials = (p_data['MRT_timeout'] == True).sum() if 'MRT_timeout' in p_data.columns else 0
        timeout_rate = timeout_trials / total_trials if total_trials > 0 else 0

        if timeout_rate > 0.20:
            exclude_participant = True
            reasons.append('high_timeout_rate')
            exclusion_stats['timeout_rate_high'].add(participant)

        # 2b: Overall accuracy check (excluding timeouts)
        non_timeout_trials = p_data[p_data['MRT_timeout'] != True] if 'MRT_timeout' in p_data.columns else p_data
        if len(non_timeout_trials) > 0:
            correct_trials = non_timeout_trials['MRT_isCorrect'].sum()
            accuracy = correct_trials / len(non_timeout_trials)

            if accuracy < 0.50:
                exclude_participant = True
                reasons.append('low_accuracy')
                exclusion_stats['accuracy_low'].add(participant)
        
        # 2c: Data completeness check
        critical_cols = ['MRT_isCorrect', 'MRT_rt_ms', 'MRT_response']
        for col in critical_cols:
            if col in p_data.columns and p_data[col].isna().any():
                exclude_participant = True
                reasons.append('missing_critical_data')
                exclusion_stats['missing_data'].add(participant)
                break
        
        # Apply participant exclusion - fix concatenation
        if exclude_participant:
            participant_mask = (df['participantId'] == participant) & (~df['excluded'])
            df.loc[participant_mask, 'excluded'] = True
            # Handle existing exclusion reasons properly
            new_reason = '; '.join(reasons)
            df.loc[participant_mask, 'exclusion_reason'] = new_reason
    
    print(f"Participants excluded for high timeout rate: {len(exclusion_stats['timeout_rate_high'])}")
    print(f"Participants excluded for low accuracy: {len(exclusion_stats['accuracy_low'])}")
    print(f"Participants excluded for missing data: {len(exclusion_stats['missing_data'])}")
    
    # Step 3: Trial-level exclusions (for remaining participants)
    print("\nStep 3: Trial-level exclusions...")
    
    remaining_data = df[~df['excluded']].copy()
    print(f"Rows remaining after participant exclusions: {len(remaining_data)}")
    
    # 3a: RT too fast - fix to handle NaN values properly
    if 'MRT_rt_ms' in df.columns:
        rt_fast_mask = (df['MRT_rt_ms'].notna()) & (df['MRT_rt_ms'] < 200) & (~df['excluded'])
        rt_fast_count = rt_fast_mask.sum()
        df.loc[rt_fast_mask, 'excluded'] = True
        df.loc[rt_fast_mask, 'exclusion_reason'] = 'rt_too_fast'
        exclusion_stats['rt_too_fast'] = rt_fast_count
        print(f"Excluded {rt_fast_count} trials for RT < 200ms")
    
    # 3b: Timeout trials
    if 'MRT_timeout' in df.columns:
        timeout_mask = (df['MRT_timeout'] == True) & (~df['excluded'])
        timeout_count = timeout_mask.sum()
        df.loc[timeout_mask, 'excluded'] = True
        df.loc[timeout_mask, 'exclusion_reason'] = 'timeout_trial'
        exclusion_stats['timeout_trials'] = timeout_count
        print(f"Excluded {timeout_count} timeout trials")
    
    # 3c: Missing response or correct data - fix the logic
    if 'MRT_response' in df.columns:
        missing_response_mask = (df['MRT_response'].isna()) & (~df['excluded'])
    else:
        missing_response_mask = pd.Series([False] * len(df))

    if 'MRT_isCorrect' in df.columns:
        missing_correct_mask = (df['MRT_isCorrect'].isna()) & (~df['excluded'])
    else:
        missing_correct_mask = pd.Series([False] * len(df))

    missing_mask = missing_response_mask | missing_correct_mask
    missing_count = missing_mask.sum()
    df.loc[missing_mask, 'excluded'] = True
    df.loc[missing_mask, 'exclusion_reason'] = 'missing_response_or_correct'
    exclusion_stats['missing_response'] = missing_count
    print(f"Excluded {missing_count} trials for missing response or correct data")

    # 3d: Invalid response values (like "0")
    if 'MRT_response' in df.columns:
        valid_responses = ['b', 'n']
        invalid_response_mask = (~df['MRT_response'].isin(valid_responses)) & (df['MRT_response'].notna()) & (~df['excluded'])
        invalid_response_count = invalid_response_mask.sum()
        df.loc[invalid_response_mask, 'excluded'] = True
        df.loc[invalid_response_mask, 'exclusion_reason'] = 'invalid_response'
        exclusion_stats['invalid_response'] = invalid_response_count
        print(f"Excluded {invalid_response_count} trials for invalid response values")
    
    # Step 4: Data quality checks
    print("\nStep 4: Data quality checks...")
    
    # Update remaining data after trial exclusions
    remaining_data = df[~df['excluded']].copy()
    remaining_participants = remaining_data['participantId'].unique()
    print(f"Participants remaining for quality checks: {len(remaining_participants)}")
    
    for participant in remaining_participants:
        p_data = remaining_data[remaining_data['participantId'] == participant]
        exclude_participant = False
        reasons = []
        
        # 4a: CV check for correct trials
        correct_trials = p_data[p_data['MRT_isCorrect'] == True]
        if len(correct_trials) > 1 and 'MRT_rt_ms' in correct_trials.columns:
            rt_values = correct_trials['MRT_rt_ms'].dropna()
            if len(rt_values) > 1:
                cv = rt_values.std() / rt_values.mean() if rt_values.mean() > 0 else 0
                if cv > 3.0:
                    exclude_participant = True
                    reasons.append('high_cv')
                    exclusion_stats['cv_high'].add(participant)
        
        # Apply quality-based exclusions
        if exclude_participant:
            participant_mask = (df['participantId'] == participant) & (~df['excluded'])
            df.loc[participant_mask, 'excluded'] = True
            df.loc[participant_mask, 'exclusion_reason'] = '; '.join(reasons)
    
    print(f"Participants excluded for high CV: {len(exclusion_stats['cv_high'])}")
    
    # Final summary
    final_excluded = df['excluded'].sum()
    final_remaining = len(df) - final_excluded
    print(f"\nFinal exclusion summary:")
    print(f"Total rows excluded: {final_excluded}")
    print(f"Total rows remaining: {final_remaining}")
    
    remaining_participants = df[~df['excluded']]['participantId'].nunique()
    print(f"Final remaining participants: {remaining_participants}")
    
    return df, exclusion_stats

def create_exclusion_log(exclusion_stats, total_participants, final_df):
    """
    Create exclusion log dataframe with accurate remaining participant counts.
    """
    print("\nCreating exclusion log...")
    
    # Calculate final remaining participants after all exclusions
    final_remaining_participants = final_df[~final_df['excluded']]['participantId'].nunique()
    
    # For participant-level exclusions, show actual counts
    # For trial-level exclusions, show N/A as they don't affect participant count directly
    exclusion_data = [
        ['practice_trials', exclusion_stats['practice_trials'], 'N/A (trial-level)'],
        ['high_timeout_rate', len(exclusion_stats['timeout_rate_high']), f"After all exclusions: {final_remaining_participants}"],
        ['low_accuracy', len(exclusion_stats['accuracy_low']), f"After all exclusions: {final_remaining_participants}"],
        ['missing_critical_data', len(exclusion_stats['missing_data']), f"After all exclusions: {final_remaining_participants}"],
        ['rt_too_fast', exclusion_stats['rt_too_fast'], 'N/A (trial-level)'],
        ['timeout_trials', exclusion_stats['timeout_trials'], 'N/A (trial-level)'],
        ['missing_response_or_correct', exclusion_stats['missing_response'], 'N/A (trial-level)'],
        ['invalid_response', exclusion_stats['invalid_response'], 'N/A (trial-level)'],
        ['high_cv', len(exclusion_stats['cv_high']), f"After all exclusions: {final_remaining_participants}"]
    ]
    
    log_df = pd.DataFrame(exclusion_data, columns=['exclusion_criterion', 'participants_excluded', 'remaining_participants'])
    
    print("Exclusion log created:")
    print(log_df)
    
    return log_df

def main():
    """
    Main execution function.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("=== MRT DATA CLEANING SCRIPT ===")
        print(f"Script started at: {datetime.now()}")
        
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        print("Outputs directory created/verified")
        
        # Load data
        file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        df, loaded_files = load_mrt_data(file_pattern)
        
        if df is None:
            print("ERROR: Failed to load data")
            return 1
        
        print(f"\nSuccessfully loaded data from {len(loaded_files)} files")
        
        # Print data overview
        print_data_overview(df)
        
        # Store initial participant count
        total_participants = df['participantId'].nunique()
        print(f"\nInitial total participants: {total_participants}")
        
        # Apply exclusions
        df_with_exclusions, exclusion_stats = apply_exclusions(df)
        
        # Create output columns in correct order
        output_columns = [
            'participantId', 'MRT_trial', 'MRT_stimulusId', 'MRT_angle_degrees',
            'MRT_isReflected', 'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms',
            'MRT_timeout', 'MRT_block', 'MRT_isAttentionCheck', 'excluded', 'exclusion_reason'
        ]
        
        # Create full output with exclusion tracking
        full_output_df = df_with_exclusions[output_columns].copy()

        print(f"\nFinal output dataset shape (with exclusion tracking): {full_output_df.shape}")
        print("Final output data columns:")
        print(list(full_output_df.columns))
        print("First 2 rows of output data:")
        print(full_output_df.head(2))

        # Save full dataset with exclusion tracking
        timestamp = get_timestamp()
        output_filename = f"outputs/MRT_cleaned_{timestamp}.csv"
        full_output_df.to_csv(output_filename, index=False)
        print(f"\nCleaned data with exclusion tracking saved to: {output_filename}")

        # Create and save exclusion log
        exclusion_log = create_exclusion_log(exclusion_stats, total_participants, df_with_exclusions)
        log_filename = f"outputs/MRT_exclusion_log_{timestamp}.csv"
        exclusion_log.to_csv(log_filename, index=False)
        print(f"Exclusion log saved to: {log_filename}")

        # Final summary
        final_participants = full_output_df[~full_output_df['excluded']]['participantId'].nunique()
        final_trials = len(full_output_df[~full_output_df['excluded']])

        print(f"\n=== FINAL SUMMARY ===")
        print(f"Original participants: {total_participants}")
        print(f"Final participants: {final_participants}")
        print(f"Final trials: {final_trials}")
        print(f"Participant retention rate: {final_participants/total_participants*100:.1f}%")

        # Add comprehensive final documentation
        print(f"\n=== FINAL EXCLUSION DOCUMENTATION ===")
        print(f"Data found for {total_participants} participants")
        print(f"{len(exclusion_stats['missing_data'])} participants had incomplete data and were removed")
        print(f"{exclusion_stats['practice_trials']} practice trials were removed")
        print(f"{len(exclusion_stats['timeout_rate_high'])} participants removed for high timeout rate")
        print(f"{len(exclusion_stats['accuracy_low'])} participants removed for low accuracy")
        print(f"{exclusion_stats['rt_too_fast']} trials were removed due to RT <200ms")
        print(f"{exclusion_stats['timeout_trials']} timeout trials were removed")
        print(f"{exclusion_stats['missing_response']} trials removed for missing response/correct data")
        print(f"{exclusion_stats['invalid_response']} trials removed for invalid response values")
        print(f"{len(exclusion_stats['cv_high'])} participants removed for high CV")
        print(f"Final dataset: {final_trials} trials from {final_participants} participants")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Script failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
