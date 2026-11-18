#!/usr/bin/env python3
"""
Trial-level data cleaning script for VWM and MRT tasks.

This script applies trial-level exclusions and minimum trial requirements
to participant data, creating a cleaned dataset with exclusion flags.
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
    -----------
    pattern : str
        File pattern to match, with <TIMESTAMP> placeholder
        
    Returns:
    --------
    str or None
        Path to most recent matching file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard pattern
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    
    print(f"Searching for files matching pattern: {search_pattern}")
    
    # Find all matching files
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        print(f"No files found matching pattern: {search_pattern}")
        return None
    
    print(f"Found {len(matching_files)} matching files:")
    for file in matching_files:
        print(f"  - {file}")
    
    # Get the most recent file based on modification time
    most_recent_file = max(matching_files, key=os.path.getmtime)
    print(f"Using most recent file: {most_recent_file}")
    
    return most_recent_file


def load_and_validate_data(filepath):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    -----------
    filepath : str
        Path to the input CSV file
        
    Returns:
    --------
    pd.DataFrame or None
        Loaded dataframe if successful, None if failed
    """
    required_columns = [
        'participantId', 'isPractice', 'VWM_trial', 'VWM_rt_ms', 'VWM_timeout',
        'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees',
        'VWM_error_absolute_degrees', 'MRT_trial', 'MRT_rt_ms', 'MRT_timeout',
        'MRT_response', 'MRT_isCorrect', 'MRT_angle_degrees', 'MRT_isReflected',
        'MRT_stimulusId', 'included'
    ]
    
    try:
        print(f"Loading data from: {filepath}")
        df = pd.read_csv(filepath)
        
        print(f"Data loaded successfully. Shape: {df.shape}")
        print(f"Columns in dataset: {list(df.columns)}")
        print("First 3 rows of data:")
        print(df.head(3))
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return None
        
        print("All required columns present")
        return df
        
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return None


def apply_vwm_exclusions(df):
    """
    Apply trial-level exclusions for VWM data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with VWM data
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with VWM exclusion flags added
    """
    print("\n=== Applying VWM Trial-Level Exclusions ===")
    
    # Initialize exclusion columns
    df['VWM_trial_excluded'] = False
    df['VWM_exclusion_reason'] = ''
    
    # Only apply exclusions to rows with VWM data
    vwm_mask = df['VWM_trial'].notna()
    vwm_trials_initial = vwm_mask.sum()
    print(f"Total VWM trials before exclusions: {vwm_trials_initial}")
    
    exclusion_counts = {}
    
    # 1. Exclude trials with VWM_rt_ms < 200 (anticipatory responses)
    anticipatory_mask = vwm_mask & (df['VWM_rt_ms'] < 200)
    exclusion_counts['VWM_anticipatory'] = anticipatory_mask.sum()
    df.loc[anticipatory_mask, 'VWM_trial_excluded'] = True
    df.loc[anticipatory_mask, 'VWM_exclusion_reason'] = 'anticipatory_response'
    print(f"VWM trials excluded for anticipatory responses (RT < 200ms): {exclusion_counts['VWM_anticipatory']}")
    
    # 2. Exclude trials with VWM_rt_ms > 7000 (timeout trials)
    slow_rt_mask = vwm_mask & (~df['VWM_trial_excluded']) & (df['VWM_rt_ms'] > 7000)
    exclusion_counts['VWM_slow_rt'] = slow_rt_mask.sum()
    df.loc[slow_rt_mask, 'VWM_trial_excluded'] = True
    df.loc[slow_rt_mask, 'VWM_exclusion_reason'] = 'slow_response'
    print(f"VWM trials excluded for slow responses (RT > 7000ms): {exclusion_counts['VWM_slow_rt']}")
    
    # 3. Exclude trials where VWM_timeout = True
    timeout_mask = vwm_mask & (~df['VWM_trial_excluded']) & (df['VWM_timeout'] == True)
    exclusion_counts['VWM_timeout'] = timeout_mask.sum()
    df.loc[timeout_mask, 'VWM_trial_excluded'] = True
    df.loc[timeout_mask, 'VWM_exclusion_reason'] = 'timeout'
    print(f"VWM trials excluded for timeout: {exclusion_counts['VWM_timeout']}")
    
    # 4. Exclude trials with missing VWM_responseAngle_degrees or VWM_targetAngle_degrees
    missing_angles_mask = vwm_mask & (~df['VWM_trial_excluded']) & (
        df['VWM_responseAngle_degrees'].isna() | 
        df['VWM_targetAngle_degrees'].isna()
    )
    exclusion_counts['VWM_missing_angles'] = missing_angles_mask.sum()
    df.loc[missing_angles_mask, 'VWM_trial_excluded'] = True
    df.loc[missing_angles_mask, 'VWM_exclusion_reason'] = 'missing_angle_data'
    print(f"VWM trials excluded for missing angle data: {exclusion_counts['VWM_missing_angles']}")
    
    # 5. Exclude trials with VWM_responseAngle_degrees outside 0-360° range
    invalid_response_mask = vwm_mask & (~df['VWM_trial_excluded']) & (
        (df['VWM_responseAngle_degrees'] < 0) | 
        (df['VWM_responseAngle_degrees'] > 360)
    )
    exclusion_counts['VWM_invalid_response'] = invalid_response_mask.sum()
    df.loc[invalid_response_mask, 'VWM_trial_excluded'] = True
    df.loc[invalid_response_mask, 'VWM_exclusion_reason'] = 'invalid_response_angle'
    print(f"VWM trials excluded for invalid response angle: {exclusion_counts['VWM_invalid_response']}")
    
    # Count remaining valid VWM trials
    vwm_valid_mask = vwm_mask & (~df['VWM_trial_excluded'])
    vwm_trials_remaining = vwm_valid_mask.sum()
    print(f"VWM trials remaining after exclusions: {vwm_trials_remaining}")
    print(f"VWM exclusion rate: {((vwm_trials_initial - vwm_trials_remaining) / vwm_trials_initial * 100):.1f}%")
    
    return df, exclusion_counts


def apply_mrt_exclusions(df):
    """
    Apply trial-level exclusions for MRT data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with MRT data
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with MRT exclusion flags added
    """
    print("\n=== Applying MRT Trial-Level Exclusions ===")
    
    # Initialize exclusion columns
    df['MRT_trial_excluded'] = False
    df['MRT_exclusion_reason'] = ''
    
    # Only apply exclusions to rows with MRT data
    mrt_mask = df['MRT_trial'].notna()
    mrt_trials_initial = mrt_mask.sum()
    print(f"Total MRT trials before exclusions: {mrt_trials_initial}")
    
    exclusion_counts = {}
    
    # 1. Exclude trials with MRT_rt_ms < 200 (anticipatory responses)
    anticipatory_mask = mrt_mask & (df['MRT_rt_ms'] < 200)
    exclusion_counts['MRT_anticipatory'] = anticipatory_mask.sum()
    df.loc[anticipatory_mask, 'MRT_trial_excluded'] = True
    df.loc[anticipatory_mask, 'MRT_exclusion_reason'] = 'anticipatory_response'
    print(f"MRT trials excluded for anticipatory responses (RT < 200ms): {exclusion_counts['MRT_anticipatory']}")
    
    # 2. Exclude trials with MRT_rt_ms > 7000 (timeout trials)
    slow_rt_mask = mrt_mask & (~df['MRT_trial_excluded']) & (df['MRT_rt_ms'] > 7000)
    exclusion_counts['MRT_slow_rt'] = slow_rt_mask.sum()
    df.loc[slow_rt_mask, 'MRT_trial_excluded'] = True
    df.loc[slow_rt_mask, 'MRT_exclusion_reason'] = 'slow_response'
    print(f"MRT trials excluded for slow responses (RT > 7000ms): {exclusion_counts['MRT_slow_rt']}")
    
    # 3. Exclude trials where MRT_timeout = True
    timeout_mask = mrt_mask & (~df['MRT_trial_excluded']) & (df['MRT_timeout'] == True)
    exclusion_counts['MRT_timeout'] = timeout_mask.sum()
    df.loc[timeout_mask, 'MRT_trial_excluded'] = True
    df.loc[timeout_mask, 'MRT_exclusion_reason'] = 'timeout'
    print(f"MRT trials excluded for timeout: {exclusion_counts['MRT_timeout']}")
    
    # 4. Exclude trials with missing MRT_response data
    missing_response_mask = mrt_mask & (~df['MRT_trial_excluded']) & df['MRT_response'].isna()
    exclusion_counts['MRT_missing_response'] = missing_response_mask.sum()
    df.loc[missing_response_mask, 'MRT_trial_excluded'] = True
    df.loc[missing_response_mask, 'MRT_exclusion_reason'] = 'missing_response'
    print(f"MRT trials excluded for missing response: {exclusion_counts['MRT_missing_response']}")
    
    # 5. Exclude trials with missing MRT_stimulusId or MRT_angle_degrees
    missing_stimulus_mask = mrt_mask & (~df['MRT_trial_excluded']) & (
        df['MRT_stimulusId'].isna() | 
        df['MRT_angle_degrees'].isna()
    )
    exclusion_counts['MRT_missing_stimulus'] = missing_stimulus_mask.sum()
    df.loc[missing_stimulus_mask, 'MRT_trial_excluded'] = True
    df.loc[missing_stimulus_mask, 'MRT_exclusion_reason'] = 'missing_stimulus_data'
    print(f"MRT trials excluded for missing stimulus data: {exclusion_counts['MRT_missing_stimulus']}")
    
    # Count remaining valid MRT trials
    mrt_valid_mask = mrt_mask & (~df['MRT_trial_excluded'])
    mrt_trials_remaining = mrt_valid_mask.sum()
    print(f"MRT trials remaining after exclusions: {mrt_trials_remaining}")
    print(f"MRT exclusion rate: {((mrt_trials_initial - mrt_trials_remaining) / mrt_trials_initial * 100):.1f}%")
    
    return df, exclusion_counts


def apply_minimum_trial_requirements(df):
    """
    Apply minimum trial requirements and flag participants who don't meet criteria.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with exclusion flags
        
    Returns:
    --------
    pd.DataFrame
        Dataframe with participant retention flags
    """
    print("\n=== Applying Minimum Trial Requirements ===")
    
    # Initialize participant retention flag
    df['participant_meets_minimum_trials'] = True
    
    participants_excluded = []
    
    # Get unique participants
    participants = df['participantId'].unique()
    print(f"Total participants to check: {len(participants)}")
    
    for participant in participants:
        participant_data = df[df['participantId'] == participant]
        
        # Check VWM minimum trials (test trials only, not excluded)
        vwm_test_trials = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['VWM_trial'].notna()) &
            (~participant_data['VWM_trial_excluded'])
        ]
        vwm_valid_count = len(vwm_test_trials)
        
        # Check MRT minimum trials (test trials only, not excluded)
        mrt_test_trials = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['MRT_trial'].notna()) &
            (~participant_data['MRT_trial_excluded'])
        ]
        mrt_valid_count = len(mrt_test_trials)
        
        # Apply minimum requirements
        vwm_meets_minimum = vwm_valid_count >= 95  # 75% of 126 expected trials
        mrt_meets_minimum = mrt_valid_count >= 77  # 75% of 102 expected trials
        
        if not (vwm_meets_minimum and mrt_meets_minimum):
            df.loc[df['participantId'] == participant, 'participant_meets_minimum_trials'] = False
            participants_excluded.append(participant)
            print(f"Participant {participant} excluded: VWM={vwm_valid_count}/95, MRT={mrt_valid_count}/77")
        else:
            print(f"Participant {participant} retained: VWM={vwm_valid_count}/95, MRT={mrt_valid_count}/77")
    
    # Propagate exclusion to all trials for excluded participants
    if participants_excluded:
        print(f"\nFlagging all trials for {len(participants_excluded)} excluded participant(s)...")
        excluded_mask = df['participantId'].isin(participants_excluded)
        
        # Invalidate all trials (VWM and MRT) for these participants
        df.loc[excluded_mask, ['VWM_trial_excluded', 'MRT_trial_excluded']] = True
        df.loc[excluded_mask, ['VWM_exclusion_reason', 'MRT_exclusion_reason']] = 'participant_insufficient_trials'
    
    participants_retained = len(participants) - len(participants_excluded)
    print(f"\nParticipants excluded for insufficient trials: {len(participants_excluded)}")
    print(f"Participants retained: {participants_retained}")
    
    return df, len(participants_excluded), participants_retained


def create_exclusion_log(vwm_exclusions, mrt_exclusions, participants_excluded, final_participant_count):
    """
    Create a detailed exclusion log.
    
    Parameters:
    -----------
    vwm_exclusions : dict
        Dictionary of VWM exclusion counts by type
    mrt_exclusions : dict
        Dictionary of MRT exclusion counts by type
    participants_excluded : int
        Number of participants excluded for insufficient trials
    final_participant_count : int
        Final number of participants retained
        
    Returns:
    --------
    pd.DataFrame
        Exclusion log dataframe
    """
    print("\n=== Creating Exclusion Log ===")
    
    exclusion_data = []
    
    # VWM exclusions
    for reason, count in vwm_exclusions.items():
        exclusion_data.append({
            'exclusion_criteria': reason,
            'VWM_trials_excluded': count,
            'MRT_trials_excluded': 0,
            'participants_excluded_insufficient_trials': 0,
            'final_participant_count': 0
        })
    
    # MRT exclusions
    for reason, count in mrt_exclusions.items():
        exclusion_data.append({
            'exclusion_criteria': reason,
            'VWM_trials_excluded': 0,
            'MRT_trials_excluded': count,
            'participants_excluded_insufficient_trials': 0,
            'final_participant_count': 0
        })
    
    # Participant exclusions
    exclusion_data.append({
        'exclusion_criteria': 'insufficient_trials',
        'VWM_trials_excluded': 0,
        'MRT_trials_excluded': 0,
        'participants_excluded_insufficient_trials': participants_excluded,
        'final_participant_count': final_participant_count
    })
    
    log_df = pd.DataFrame(exclusion_data)
    
    print("Exclusion log created:")
    print(log_df)
    
    return log_df


def prepare_output_dataframe(df):
    """
    Prepare the final output dataframe with required columns.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with all processing applied
        
    Returns:
    --------
    pd.DataFrame
        Output dataframe with required columns only
    """
    print("\n=== Preparing Output Dataframe ===")
    
    # Define required output columns
    required_output_columns = [
        'participantId', 'isPractice', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
        'VWM_cueIndex', 'VWM_orientations_degrees', 'VWM_responseAngle_degrees',
        'VWM_targetAngle_degrees', 'VWM_error_degrees', 'VWM_error_absolute_degrees',
        'VWM_rt_ms', 'VWM_pracAttempt', 'VWM_timeout', 'VWM_block', 'VWM_isAttentionCheck',
        'MRT_trial', 'MRT_stimulusId', 'MRT_angle_degrees', 'MRT_isReflected',
        'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_pracAttempt', 'MRT_timeout',
        'MRT_block', 'MRT_isAttentionCheck', 'VWM_trial_excluded', 'MRT_trial_excluded',
        'VWM_exclusion_reason', 'MRT_exclusion_reason', 'participant_meets_minimum_trials'
    ]
    
    # Create output dataframe with only required columns
    # For missing columns, create them with NaN values
    output_df = pd.DataFrame()
    
    for col in required_output_columns:
        if col in df.columns:
            output_df[col] = df[col]
        else:
            # Create missing columns with appropriate default values
            if col in ['VWM_trial_excluded', 'MRT_trial_excluded', 'participant_meets_minimum_trials']:
                output_df[col] = False
            elif col in ['VWM_exclusion_reason', 'MRT_exclusion_reason']:
                output_df[col] = ''
            else:
                output_df[col] = np.nan
                print(f"Warning: Column '{col}' not found in input data, filling with NaN")
    
    print(f"Output dataframe prepared with shape: {output_df.shape}")
    print(f"Output columns: {list(output_df.columns)}")
    print("First 2 rows of output data:")
    print(output_df.head(2))
    
    return output_df


def print_data_summary(df):
    """
    Print summary statistics and unique values for key experimental parameters.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe to summarize
    """
    print("\n=== Data Summary ===")
    
    # Print basic info
    print(f"Total rows: {len(df)}")
    print(f"Total participants: {df['participantId'].nunique()}")
    print(f"Practice trials: {(df['isPractice'] == True).sum()}")
    print(f"Test trials: {(df['isPractice'] == False).sum()}")
    
    # Print unique values for key experimental design parameters
    if 'VWM_setSize' in df.columns:
        print(f"VWM set sizes: {sorted(df['VWM_setSize'].dropna().unique())}")
    
    if 'VWM_delay_s' in df.columns:
        print(f"VWM delays: {sorted(df['VWM_delay_s'].dropna().unique())}")
    
    if 'VWM_block' in df.columns:
        print(f"VWM blocks: {sorted(df['VWM_block'].dropna().unique())}")
    
    if 'VWM_isAttentionCheck' in df.columns:
        print(f"VWM attention check values: {sorted(df['VWM_isAttentionCheck'].dropna().unique())}")
    
    if 'MRT_angle_degrees' in df.columns:
        print(f"MRT angles: {sorted(df['MRT_angle_degrees'].dropna().unique())}")
    
    if 'MRT_isReflected' in df.columns:
        print(f"MRT reflection values: {sorted(df['MRT_isReflected'].dropna().unique())}")
    
    if 'MRT_block' in df.columns:
        print(f"MRT blocks: {sorted(df['MRT_block'].dropna().unique())}")
    
    if 'MRT_isAttentionCheck' in df.columns:
        print(f"MRT attention check values: {sorted(df['MRT_isAttentionCheck'].dropna().unique())}")
    
    # Print data types for measured variables
    print("\nData types for measured variables:")
    if 'VWM_rt_ms' in df.columns:
        print(f"VWM_rt_ms: {df['VWM_rt_ms'].dtype}")
    if 'VWM_error_degrees' in df.columns:
        print(f"VWM_error_degrees: {df['VWM_error_degrees'].dtype}")
    if 'MRT_rt_ms' in df.columns:
        print(f"MRT_rt_ms: {df['MRT_rt_ms'].dtype}")
    if 'MRT_isCorrect' in df.columns:
        print(f"MRT_isCorrect: {df['MRT_isCorrect'].dtype}")


def main():
    """
    Main execution function for trial-level data cleaning.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("=== Starting Trial-Level Data Cleaning ===")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find input file
        input_pattern = "outputs/participant_level_cleaned_data_<TIMESTAMP>.csv"
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print("ERROR: No input file found matching pattern")
            return 1
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            return 1
        
        # Filter to included participants only
        print(f"\nFiltering to included participants...")
        initial_rows = len(df)
        df = df[df['included'] == True].copy()
        print(f"Rows before filtering: {initial_rows}")
        print(f"Rows after filtering to included participants: {len(df)}")
        
        # Print data summary
        print_data_summary(df)
        
        # Apply VWM exclusions
        df, vwm_exclusions = apply_vwm_exclusions(df)
        
        # Apply MRT exclusions
        df, mrt_exclusions = apply_mrt_exclusions(df)
        
        # Apply minimum trial requirements
        df, participants_excluded, final_participant_count = apply_minimum_trial_requirements(df)
        
        # Create exclusion log
        exclusion_log = create_exclusion_log(
            vwm_exclusions, mrt_exclusions, participants_excluded, final_participant_count
        )
        
        # Prepare output dataframe
        output_df = prepare_output_dataframe(df)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main output file
        output_file = f"outputs/trial_level_cleaned_data_{timestamp}.csv"
        output_df.to_csv(output_file, index=False)
        print(f"\nSaved cleaned data to: {output_file}")
        
        # Save exclusion log
        log_file = f"outputs/trial_exclusion_log_{timestamp}.csv"
        exclusion_log.to_csv(log_file, index=False)
        print(f"Saved exclusion log to: {log_file}")
        
        # Print final summary
        print(f"\n=== Final Summary ===")
        print(f"Total trials in output: {len(output_df)}")
        print(f"VWM trials excluded: {output_df['VWM_trial_excluded'].sum()}")
        print(f"MRT trials excluded: {output_df['MRT_trial_excluded'].sum()}")
        print(f"Final participant count: {output_df.loc[output_df['participant_meets_minimum_trials'], 'participantId'].nunique()}")

        # Print comprehensive exclusion breakdown
        print(f"\n=== Comprehensive Exclusion Summary ===")
        print(f"Initial participants: 126")
        print(f"VWM trial exclusions by type:")
        for reason, count in vwm_exclusions.items():
            print(f"  - {reason}: {count}")
        print(f"MRT trial exclusions by type:")
        for reason, count in mrt_exclusions.items():
            print(f"  - {reason}: {count}")
        print(f"Participants excluded for insufficient trials: {participants_excluded}")
        print(f"Final dataset: {len(output_df)} trials from {final_participant_count} participants")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
