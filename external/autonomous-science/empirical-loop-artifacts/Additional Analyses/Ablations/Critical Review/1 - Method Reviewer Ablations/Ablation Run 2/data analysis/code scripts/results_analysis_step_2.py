#!/usr/bin/env python3
"""
VWM and MRT Data Cleaning Script

This script processes Visual Working Memory (VWM) and Mental Rotation Task (MRT) data files,
applies participant-level and trial-level exclusions, and outputs cleaned data with exclusion logs.
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def load_and_merge_files(file_pattern):
    """
    Load and merge all participant files matching the pattern.
    
    Parameters:
    file_pattern (str): Glob pattern for input files
    
    Returns:
    pd.DataFrame: Merged dataframe from all participant files
    list: List of unique participant IDs
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} files: {files}")
    
    if not files:
        print("ERROR: No files found matching the pattern")
        return None, None
    
    all_data = []
    reference_columns = None

    # Track column inconsistencies
    missing_columns_files = []
    extra_columns_files = []

    for idx, file in enumerate(files):
        print(f"Loading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File {file} loaded with {len(df)} rows and {len(df.columns)} columns")
            print("Columns:", list(df.columns))
            print("First 3 rows:")
            print(df.head(3))
            if idx == 0:
                reference_columns = set(df.columns)
            else:
                current_columns = set(df.columns)
                missing_in_current = reference_columns - current_columns
                extra_in_current = current_columns - reference_columns
                if missing_in_current:
                    print(f"WARNING: File {file} is missing columns: {missing_in_current}")
                    missing_columns_files.append((file, missing_in_current))
                if extra_in_current:
                    print(f"WARNING: File {file} has extra columns: {extra_in_current}")
                    extra_columns_files.append((file, extra_in_current))
            all_data.append(df)
        except Exception as e:
            print(f"Error loading file {file}: {e}")
            continue

    # Print comprehensive summary of column inconsistencies
    if missing_columns_files or extra_columns_files:
        print("\n=== COLUMN INCONSISTENCY SUMMARY ===")
        if missing_columns_files:
            print(f"Files with missing columns: {len(missing_columns_files)}")
            for file, missing_cols in missing_columns_files:
                print(f"  {file}: missing {missing_cols}")
        if extra_columns_files:
            print(f"Files with extra columns: {len(extra_columns_files)}")
            for file, extra_cols in extra_columns_files:
                print(f"  {file}: extra {extra_cols}")
    else:
        print("\n=== COLUMN CONSISTENCY CHECK ===")
        print("All files have consistent column structure")
    
    if not all_data:
        print("ERROR: No valid data files loaded")
        return None, None
    
    print("Merging all data files...")
    merged_df = pd.concat(all_data, ignore_index=True, sort=False)
    print(f"Merged data has {len(merged_df)} rows and {len(merged_df.columns)} columns")
    
    unique_participants = merged_df['participantId'].unique()
    print(f"Found {len(unique_participants)} unique participants: {unique_participants}")
    
    return merged_df, unique_participants

def normalize_vwm_error(df):
    """
    Normalize VWM error data to ±90° range and recalculate absolute error.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Dataframe with normalized VWM error values
    """
    print("Normalizing VWM error data...")
    
    # Only process rows where VWM data exists (not NaN)
    vwm_mask = ~pd.isna(df['VWM_error_degrees'])
    print(f"Found {vwm_mask.sum()} VWM trials with error data")
    
    if vwm_mask.sum() == 0:
        print("No VWM error data to normalize")
        return df
    
    # Normalize error to ±90° range
    df.loc[vwm_mask & (df['VWM_error_degrees'] > 90), 'VWM_error_degrees'] -= 180
    df.loc[vwm_mask & (df['VWM_error_degrees'] < -90), 'VWM_error_degrees'] += 180
    
    # Recalculate absolute error
    df.loc[vwm_mask, 'VWM_error_absolute_degrees'] = df.loc[vwm_mask, 'VWM_error_degrees'].abs()
    
    print("VWM error normalization completed")
    print(f"VWM error range after normalization: {df['VWM_error_degrees'].min():.2f} to {df['VWM_error_degrees'].max():.2f}")
    
    return df

def identify_task_rows(df):
    """
    Identify which rows belong to VWM vs MRT tasks.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Dataframe with task identification masks
    """
    print("Identifying task rows...")
    
    # VWM rows are those with non-null VWM_trial
    vwm_rows = ~pd.isna(df['VWM_trial'])
    # MRT rows are those with non-null MRT_trial
    mrt_rows = ~pd.isna(df['MRT_trial'])
    
    print(f"VWM rows: {vwm_rows.sum()}")
    print(f"MRT rows: {mrt_rows.sum()}")
    print(f"Total rows: {len(df)}")
    
    return vwm_rows, mrt_rows

def check_practice_proficiency(df, vwm_rows, mrt_rows):
    """
    Check practice proficiency for both VWM and MRT tasks.
    """
    print("Checking practice proficiency...")
    print(f"Input dataframe shape: {df.shape}")
    print(f"VWM rows in input: {vwm_rows.sum()}")
    print(f"MRT rows in input: {mrt_rows.sum()}")

    # Create a copy to avoid modifying the original dataframe
    df_work = df.copy()
    
    # Ensure isPractice is boolean
    if 'isPractice' in df_work.columns:
        if df_work['isPractice'].dtype == 'object':
            df_work['isPractice'] = df_work['isPractice'].astype(str).str.lower().isin(['true', '1', 'yes'])
        elif df_work['isPractice'].dtype in ['int64', 'float64']:
            df_work['isPractice'] = df_work['isPractice'].astype(bool)

    exclude_participants = set()
    
    # Check VWM practice proficiency - use df_work instead of df
    print("Checking VWM practice proficiency...")
    vwm_practice = df_work[vwm_rows & (df_work['isPractice'] == True)]
    print(f"VWM practice trials: {len(vwm_practice)}")
    print(f"VWM practice participants: {vwm_practice['participantId'].nunique()}")

    if len(vwm_practice) > 0:
        print("Sample VWM practice data:")
        print(vwm_practice[['participantId', 'VWM_pracAttempt', 'VWM_error_absolute_degrees']].head())
        
        for participant in vwm_practice['participantId'].unique():
            participant_practice = vwm_practice[vwm_practice['participantId'] == participant]
            print(f"Participant {participant}: {len(participant_practice)} practice trials")

            if len(participant_practice) == 0:
                continue

            # Find final practice attempt
            if 'VWM_pracAttempt' in participant_practice.columns:
                max_attempt = participant_practice['VWM_pracAttempt'].max()
                print(f"  Max attempt: {max_attempt}")
            else:
                max_attempt = None

            if max_attempt is None or pd.isna(max_attempt):
                continue

            final_attempt = participant_practice[participant_practice['VWM_pracAttempt'] == max_attempt]

            if len(final_attempt) > 0:
                mean_error = final_attempt['VWM_error_absolute_degrees'].mean()
                print(f"  Final attempt mean error: {mean_error}")
                # Only exclude if failed after at least 3 attempts
                if max_attempt >= 3 and (pd.isna(mean_error) or mean_error > 45):
                    print(f"Excluding participant {participant} - VWM practice proficiency failure (mean error: {mean_error}, max attempt: {max_attempt})")
                    exclude_participants.add(participant)

    # Check MRT practice proficiency - use df_work instead of df
    print("Checking MRT practice proficiency...")
    mrt_practice = df_work[mrt_rows & (df_work['isPractice'] == True)]
    print(f"MRT practice trials: {len(mrt_practice)}")
    print(f"MRT practice participants: {mrt_practice['participantId'].nunique()}")

    if len(mrt_practice) > 0:
        print("Sample MRT practice data:")
        print(mrt_practice[['participantId', 'MRT_pracAttempt', 'MRT_isCorrect']].head())
        
        for participant in mrt_practice['participantId'].unique():
            participant_practice = mrt_practice[mrt_practice['participantId'] == participant]
            print(f"Participant {participant}: {len(participant_practice)} practice trials")

            if len(participant_practice) == 0:
                continue

            # Find final practice attempt
            if 'MRT_pracAttempt' in participant_practice.columns:
                max_attempt = participant_practice['MRT_pracAttempt'].max()
                print(f"  Max attempt: {max_attempt}")
            else:
                max_attempt = None

            if max_attempt is None or pd.isna(max_attempt):
                continue

            final_attempt = participant_practice[participant_practice['MRT_pracAttempt'] == max_attempt]

            if len(final_attempt) > 0:
                accuracy = final_attempt['MRT_isCorrect'].mean()
                print(f"  Final attempt accuracy: {accuracy}")
                # Only exclude if failed after at least 3 attempts
                if max_attempt >= 3 and (pd.isna(accuracy) or accuracy < (8/12)):
                    print(f"Excluding participant {participant} - MRT practice proficiency failure (accuracy: {accuracy}, max attempt: {max_attempt})")
                    exclude_participants.add(participant)

    print(f"Total participants excluded for practice proficiency: {len(exclude_participants)}")
    if exclude_participants:
        print(f"Excluded participants: {list(exclude_participants)}")
    return exclude_participants

def check_overall_performance(df, vwm_rows, mrt_rows):
    """
    Check overall task performance for both VWM and MRT tasks.
    """
    print("Checking overall task performance...")
    
    exclude_vwm = set()
    exclude_mrt = set()
    
    # Check VWM overall performance using groupby
    print("Checking VWM overall performance...")
    vwm_test = df[vwm_rows & (df['isPractice'] == False) & df['VWM_block'].notna()]
    print(f"VWM test trials: {len(vwm_test)}")
    
    if not vwm_test.empty and 'VWM_error_absolute_degrees' in vwm_test.columns:
        # Filter out null values before groupby
        vwm_valid = vwm_test[vwm_test['VWM_error_absolute_degrees'].notna()]
        if not vwm_valid.empty:
            vwm_perf = vwm_valid.groupby('participantId')['VWM_error_absolute_degrees'].mean()
            vwm_to_exclude = vwm_perf[vwm_perf > 75].index
            exclude_vwm.update(vwm_to_exclude)
            for participant in vwm_to_exclude:
                print(f"Excluding participant {participant} from VWM - poor performance (mean error: {vwm_perf[participant]})")
    
    # Check MRT overall performance using groupby
    print("Checking MRT overall performance...")
    mrt_test = df[mrt_rows & (df['isPractice'] == False) & df['MRT_block'].notna()]
    print(f"MRT test trials: {len(mrt_test)}")
    
    if not mrt_test.empty and 'MRT_isCorrect' in mrt_test.columns:
        # Filter out null values before groupby
        mrt_valid = mrt_test[mrt_test['MRT_isCorrect'].notna()]
        if not mrt_valid.empty:
            mrt_perf = mrt_valid.groupby('participantId')['MRT_isCorrect'].mean()
            mrt_to_exclude = mrt_perf[mrt_perf < 0.5].index
            exclude_mrt.update(mrt_to_exclude)
            for participant in mrt_to_exclude:
                print(f"Excluding participant {participant} from MRT - poor performance (accuracy: {mrt_perf[participant]})")
    
    print(f"Participants excluded from VWM for performance: {len(exclude_vwm)}")
    print(f"Participants excluded from MRT for performance: {len(exclude_mrt)}")
    
    return exclude_vwm, exclude_mrt

def check_attention_compliance(df, vwm_rows, mrt_rows):
    """
    Check attention check compliance for both tasks.
    """
    print("Checking attention check compliance...")
    
    exclude_vwm = set()
    exclude_mrt = set()
    
    # Check VWM attention checks using groupby
    print("Checking VWM attention checks...")
    vwm_attention = df[vwm_rows & (df['VWM_isAttentionCheck'] == True)]
    print(f"VWM attention check trials: {len(vwm_attention)}")
    
    if not vwm_attention.empty:
        vwm_fail_rates = vwm_attention.groupby('participantId').apply(
            lambda x: (x['VWM_error_absolute_degrees'] > 15).sum() / len(x) if len(x) > 0 else 0
        )
        vwm_to_exclude = vwm_fail_rates[vwm_fail_rates > 0.75].index
        exclude_vwm.update(vwm_to_exclude)
        for participant in vwm_to_exclude:
            print(f"Excluding participant {participant} from VWM - attention check failure rate: {vwm_fail_rates[participant]}")
    
    # Check MRT attention checks using groupby
    print("Checking MRT attention checks...")
    mrt_attention = df[mrt_rows & (df['MRT_isAttentionCheck'] == True)]
    print(f"MRT attention check trials: {len(mrt_attention)}")
    
    if not mrt_attention.empty:
        mrt_fail_rates = mrt_attention.groupby('participantId').apply(
            lambda x: (x['MRT_isCorrect'] == False).sum() / len(x) if len(x) > 0 else 0
        )
        mrt_to_exclude = mrt_fail_rates[mrt_fail_rates > 0.75].index
        exclude_mrt.update(mrt_to_exclude)
        for participant in mrt_to_exclude:
            print(f"Excluding participant {participant} from MRT - attention check failure rate: {mrt_fail_rates[participant]}")
    
    print(f"Participants excluded from VWM for attention: {len(exclude_vwm)}")
    print(f"Participants excluded from MRT for attention: {len(exclude_mrt)}")
    
    return exclude_vwm, exclude_mrt

def check_timeout_behavior(df, vwm_rows, mrt_rows):
    """
    Check timeout behavior for both tasks.
    """
    print("Checking timeout behavior...")
    
    exclude_vwm = set()
    exclude_mrt = set()
    
    # Check VWM timeouts using groupby
    print("Checking VWM timeouts...")
    participant_vwm = df[vwm_rows]
    if not participant_vwm.empty:
        vwm_timeout_rates = participant_vwm.groupby('participantId')['VWM_timeout'].mean()
        vwm_to_exclude = vwm_timeout_rates[vwm_timeout_rates > 0.3].index
        exclude_vwm.update(vwm_to_exclude)
        for participant in vwm_to_exclude:
            print(f"Excluding participant {participant} from VWM - timeout rate: {vwm_timeout_rates[participant]}")
    
    # Check MRT timeouts using groupby
    print("Checking MRT timeouts...")
    participant_mrt = df[mrt_rows]
    if not participant_mrt.empty:
        mrt_timeout_rates = participant_mrt.groupby('participantId')['MRT_timeout'].mean()
        mrt_to_exclude = mrt_timeout_rates[mrt_timeout_rates > 0.3].index
        exclude_mrt.update(mrt_to_exclude)
        for participant in mrt_to_exclude:
            print(f"Excluding participant {participant} from MRT - timeout rate: {mrt_timeout_rates[participant]}")
    
    print(f"Participants excluded from VWM for timeouts: {len(exclude_vwm)}")
    print(f"Participants excluded from MRT for timeouts: {len(exclude_mrt)}")
    
    return exclude_vwm, exclude_mrt

def check_focus_loss(df):
    """
    Check window focus loss behavior.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    set: Set of participant IDs to exclude due to focus loss
    """
    print("Checking focus loss behavior...")
    
    exclude_participants = set()
    
    # Ensure timestamp column is datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    
    for participant in df['participantId'].unique():
        participant_data = df[df['participantId'] == participant]
        
        if len(participant_data) == 0:
            continue
        
        # Get focus loss duration (assuming it's in the first row for each participant)
        focus_loss_duration_str = participant_data['windowFocusLostDuringTasksDuration'].iloc[0]
        
        if pd.isna(focus_loss_duration_str):
            continue
        
        # Convert duration to seconds (assuming format like "00:01:30" for 1 min 30 sec)
        try:
            if ':' in str(focus_loss_duration_str):
                time_parts = str(focus_loss_duration_str).split(':')
                if len(time_parts) == 3:
                    hours, minutes, seconds = map(float, time_parts)
                    focus_loss_seconds = hours * 3600 + minutes * 60 + seconds
                elif len(time_parts) == 2:
                    minutes, seconds = map(float, time_parts)
                    focus_loss_seconds = minutes * 60 + seconds
                else:
                    focus_loss_seconds = float(focus_loss_duration_str)
            else:
                focus_loss_seconds = float(focus_loss_duration_str)
        except:
            print(f"Could not parse focus loss duration for participant {participant}: {focus_loss_duration_str}")
            continue
        
        # Calculate actual total task duration using timestamp column
        if 'timestamp' in participant_data.columns:
            task_times = participant_data['timestamp'].dropna()
            if len(task_times) > 1:
                total_task_duration_seconds = (task_times.max() - task_times.min()).total_seconds()
            else:
                total_task_duration_seconds = 0
        else:
            # Fallback to previous estimation if timestamp not available
            total_trials = len(participant_data)
            avg_rt = participant_data[['VWM_rt_ms', 'MRT_rt_ms']].mean().mean()
            if pd.isna(avg_rt):
                avg_rt = 2000  # Default assumption
            total_task_duration_seconds = total_trials * (avg_rt / 1000)
        
        if total_task_duration_seconds > 0:
            focus_loss_rate = focus_loss_seconds / total_task_duration_seconds
            
            if focus_loss_rate > 0.25:
                print(f"Excluding participant {participant} - focus loss rate: {focus_loss_rate}")
                exclude_participants.add(participant)
    
    print(f"Participants excluded for focus loss: {len(exclude_participants)}")
    return exclude_participants

def check_technical_issues(df):
    """
    Check for technical issues (WebGL support and screen resolution).
    """
    print("Checking technical issues...")
    
    exclude_participants = set()
    
    # Get unique participant data using groupby
    participant_data = df.groupby('participantId').first()
    
    # Check WebGL support
    webgl_mask = participant_data['webGLsupport'] == False
    webgl_exclude = participant_data[webgl_mask].index
    for participant in webgl_exclude:
        print(f"Excluding participant {participant} - no WebGL support")
    exclude_participants.update(webgl_exclude)
    
    # Check screen resolution
    width_mask = (participant_data['screenWidthPixels'].notna()) & (participant_data['screenWidthPixels'] < 768)
    height_mask = (participant_data['screenHeightPixels'].notna()) & (participant_data['screenHeightPixels'] < 768)
    
    width_exclude = participant_data[width_mask].index
    height_exclude = participant_data[height_mask].index
    
    for participant in width_exclude:
        print(f"Excluding participant {participant} - screen width too small: {participant_data.loc[participant, 'screenWidthPixels']}")
    for participant in height_exclude:
        print(f"Excluding participant {participant} - screen height too small: {participant_data.loc[participant, 'screenHeightPixels']}")
    
    exclude_participants.update(width_exclude)
    exclude_participants.update(height_exclude)
    
    print(f"Participants excluded for technical issues: {len(exclude_participants)}")
    return exclude_participants

def apply_trial_exclusions(df, vwm_rows, mrt_rows, exclude_vwm_participants, exclude_mrt_participants):
    """
    Apply trial-level exclusions to remaining participants.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    vwm_rows (pd.Series): Boolean mask for VWM rows
    mrt_rows (pd.Series): Boolean mask for MRT rows
    exclude_vwm_participants (set): Participants excluded from VWM
    exclude_mrt_participants (set): Participants excluded from MRT
    
    Returns:
    pd.DataFrame: Dataframe with trial exclusion flags
    """
    print("Applying trial-level exclusions...")
    
    # Initialize trial_excluded column if it doesn't exist
    if 'trial_excluded' not in df.columns:
        df['trial_excluded'] = False

    # Flag trials based on task-specific participant exclusions
    vwm_excluded_mask = vwm_rows & df['participantId'].isin(exclude_vwm_participants)
    mrt_excluded_mask = mrt_rows & df['participantId'].isin(exclude_mrt_participants)
    df.loc[vwm_excluded_mask | mrt_excluded_mask, 'trial_excluded'] = True
    print(f"Flagged all trials for {vwm_excluded_mask.sum()} VWM-excluded and {mrt_excluded_mask.sum()} MRT-excluded trials")
    
    # Remove timeout trials - add null checks
    timeout_mask = ((df['VWM_timeout'] == True) | (df['MRT_timeout'] == True)).fillna(False)
    df.loc[timeout_mask, 'trial_excluded'] = True
    print(f"Excluded {timeout_mask.sum()} trials for timeouts")
    
    # Remove fast RT trials - add null checks
    fast_vwm = vwm_rows & (df['VWM_rt_ms'].notna()) & (df['VWM_rt_ms'] < 200)
    fast_mrt = mrt_rows & (df['MRT_rt_ms'].notna()) & (df['MRT_rt_ms'] < 200)
    df.loc[fast_vwm | fast_mrt, 'trial_excluded'] = True
    print(f"Excluded {(fast_vwm | fast_mrt).sum()} trials for fast RTs")
    
    # Remove VWM trials with impossible response angles - add null checks
    impossible_vwm = (vwm_rows & 
                     df['VWM_responseAngle_degrees'].notna() & 
                     ((df['VWM_responseAngle_degrees'] < 0) | (df['VWM_responseAngle_degrees'] >= 180)))
    df.loc[impossible_vwm, 'trial_excluded'] = True
    print(f"Excluded {impossible_vwm.sum()} VWM trials for impossible response angles")
    
    # Remove slow RT trials (>3SD from participant mean)
    print("Removing slow RT trials...")

    # Vectorized VWM slow RT exclusion with safety checks
    vwm_rt_valid = df.loc[vwm_rows & ~df['trial_excluded'] & ~df['participantId'].isin(exclude_vwm_participants) & df['VWM_rt_ms'].notna()]
    if not vwm_rt_valid.empty:
        try:
            vwm_grouped = vwm_rt_valid.groupby('participantId')['VWM_rt_ms']
            vwm_cutoff = vwm_grouped.transform('mean') + 3 * vwm_grouped.transform('std')
            slow_vwm_trials = vwm_rt_valid.index[vwm_rt_valid['VWM_rt_ms'] > vwm_cutoff]
            df.loc[slow_vwm_trials, 'trial_excluded'] = True
        except Exception as e:
            print(f"Warning: Could not apply VWM slow RT exclusion: {e}")

    # Vectorized MRT slow RT exclusion with safety checks
    mrt_rt_valid = df.loc[mrt_rows & (df['MRT_isCorrect'] == True) & ~df['trial_excluded'] & ~df['participantId'].isin(exclude_mrt_participants) & df['MRT_rt_ms'].notna()]
    if not mrt_rt_valid.empty:
        try:
            mrt_grouped = mrt_rt_valid.groupby(['participantId', 'MRT_angle_degrees'])['MRT_rt_ms']
            mrt_cutoff = mrt_grouped.transform('mean') + 3 * mrt_grouped.transform('std')
            slow_mrt_trials = mrt_rt_valid.index[mrt_rt_valid['MRT_rt_ms'] > mrt_cutoff]
            df.loc[slow_mrt_trials, 'trial_excluded'] = True
        except Exception as e:
            print(f"Warning: Could not apply MRT slow RT exclusion: {e}")

    print(f"Total trials excluded: {df['trial_excluded'].sum()}")
    return df

def create_exclusion_log():
    """
    Create exclusion log with counts for each criterion.
    
    Returns:
    pd.DataFrame: Exclusion log dataframe
    """
    # This would be populated during the actual exclusion process
    # For now, creating a template structure
    exclusions = [
        {"exclusion_criterion": "Practice proficiency failure", "count_excluded": 0, 
         "description": "Unable to achieve proficiency criteria after 3 practice attempts"},
        {"exclusion_criterion": "Poor overall performance", "count_excluded": 0,
         "description": "Overall task performance below threshold"},
        {"exclusion_criterion": "Attention check failures", "count_excluded": 0,
         "description": "Failed >75% of attention checks"},
        {"exclusion_criterion": "Excessive timeouts", "count_excluded": 0,
         "description": "Timeout rate >30%"},
        {"exclusion_criterion": "Focus loss", "count_excluded": 0,
         "description": "Focus loss >25% of total task duration"},
        {"exclusion_criterion": "Technical issues", "count_excluded": 0,
         "description": "No WebGL support or screen resolution <768px"}
    ]
    
    return pd.DataFrame(exclusions)

def main():
    """
    Main function to execute the data cleaning pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM and MRT data cleaning script...")
        
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Load and merge data files
        file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        df, unique_participants = load_and_merge_files(file_pattern)
        
        if df is None:
            print("ERROR: Failed to load data files")
            return 1
        
        print("\nOriginal data structure:")
        print("All columns:", list(df.columns))
        print("First 2 rows:")
        print(df.head(2))
        
        # Print unique values for key experimental design parameters
        print("\nExperimental design parameters:")
        if 'VWM_setSize' in df.columns:
            print("VWM set sizes:", df['VWM_setSize'].unique())
        if 'VWM_delay_s' in df.columns:
            print("VWM delays:", df['VWM_delay_s'].unique())
        if 'MRT_angle_degrees' in df.columns:
            print("MRT angles:", df['MRT_angle_degrees'].unique())
        if 'VWM_block' in df.columns:
            print("VWM blocks:", df['VWM_block'].unique())
        if 'MRT_block' in df.columns:
            print("MRT blocks:", df['MRT_block'].unique())
        
        # Print variable types for measured variables
        print("\nMeasured variable types:")
        if 'VWM_rt_ms' in df.columns:
            print(f"VWM_rt_ms type: {df['VWM_rt_ms'].dtype}")
        if 'MRT_rt_ms' in df.columns:
            print(f"MRT_rt_ms type: {df['MRT_rt_ms'].dtype}")
        if 'VWM_error_degrees' in df.columns:
            print(f"VWM_error_degrees type: {df['VWM_error_degrees'].dtype}")
        
        # Normalize VWM error data
        df = normalize_vwm_error(df)
        
        # Identify task rows
        vwm_rows, mrt_rows = identify_task_rows(df)
        
        # Apply participant-level exclusions CASCADED
        print("\n=== PARTICIPANT-LEVEL EXCLUSIONS (CASCADED) ===")
        remaining_participants = set(df['participantId'].unique())
        print(f"Starting with {len(remaining_participants)} participants")

        # Track exclusions for log
        exclude_practice = set()
        exclude_vwm_performance = set()
        exclude_mrt_performance = set()
        exclude_vwm_attention = set()
        exclude_mrt_attention = set()
        exclude_vwm_timeout = set()
        exclude_mrt_timeout = set()
        exclude_focus = set()
        exclude_technical = set()

        # Step 1: Practice proficiency
        print(f"\n--- Step 1: Practice Proficiency ---")
        df_practice = df[df['participantId'].isin(remaining_participants)].copy()
        vwm_rows_practice, mrt_rows_practice = identify_task_rows(df_practice)
        exclude_practice = check_practice_proficiency(df_practice, vwm_rows_practice, mrt_rows_practice)
        remaining_participants -= exclude_practice
        print(f"After practice exclusions: {len(remaining_participants)} participants remaining")

        # Step 2: Overall performance
        print(f"\n--- Step 2: Overall Performance ---")
        df_perf = df[df['participantId'].isin(remaining_participants)].copy()
        vwm_rows_perf, mrt_rows_perf = identify_task_rows(df_perf)
        exclude_vwm_performance, exclude_mrt_performance = check_overall_performance(df_perf, vwm_rows_perf, mrt_rows_perf)
        remaining_participants -= (exclude_vwm_performance | exclude_mrt_performance)
        print(f"After performance exclusions: {len(remaining_participants)} participants remaining")

        # Step 3: Attention compliance
        print(f"\n--- Step 3: Attention Compliance ---")
        df_attn = df[df['participantId'].isin(remaining_participants)].copy()
        vwm_rows_attn, mrt_rows_attn = identify_task_rows(df_attn)
        exclude_vwm_attention, exclude_mrt_attention = check_attention_compliance(df_attn, vwm_rows_attn, mrt_rows_attn)
        remaining_participants -= (exclude_vwm_attention | exclude_mrt_attention)
        print(f"After attention exclusions: {len(remaining_participants)} participants remaining")

        # Step 4: Timeout behavior
        print(f"\n--- Step 4: Timeout Behavior ---")
        df_timeout = df[df['participantId'].isin(remaining_participants)].copy()
        vwm_rows_timeout, mrt_rows_timeout = identify_task_rows(df_timeout)
        exclude_vwm_timeout, exclude_mrt_timeout = check_timeout_behavior(df_timeout, vwm_rows_timeout, mrt_rows_timeout)
        remaining_participants -= (exclude_vwm_timeout | exclude_mrt_timeout)
        print(f"After timeout exclusions: {len(remaining_participants)} participants remaining")

        # Step 5: Focus loss
        print(f"\n--- Step 5: Focus Loss ---")
        df_focus = df[df['participantId'].isin(remaining_participants)].copy()
        exclude_focus = check_focus_loss(df_focus)
        remaining_participants -= exclude_focus
        print(f"After focus loss exclusions: {len(remaining_participants)} participants remaining")

        # Step 6: Technical issues
        print(f"\n--- Step 6: Technical Issues ---")
        df_tech = df[df['participantId'].isin(remaining_participants)].copy()
        exclude_technical = check_technical_issues(df_tech)
        remaining_participants -= exclude_technical
        print(f"After technical exclusions: {len(remaining_participants)} participants remaining")

        # Combine exclusions for VWM and MRT
        exclude_vwm_total = (exclude_practice | exclude_vwm_performance | exclude_vwm_attention | exclude_vwm_timeout | exclude_focus | exclude_technical)
        exclude_mrt_total = (exclude_practice | exclude_mrt_performance | exclude_mrt_attention | exclude_mrt_timeout | exclude_focus | exclude_technical)

        print(f"\nTotal participants excluded from VWM: {len(exclude_vwm_total)}")
        print(f"Total participants excluded from MRT: {len(exclude_mrt_total)}")
        
        # Add exclusion flags to dataframe
        df['excluded_from_VWM'] = df['participantId'].isin(exclude_vwm_total)
        df['excluded_from_MRT'] = df['participantId'].isin(exclude_mrt_total)
        
        # Apply trial-level exclusions
        print("\n=== TRIAL-LEVEL EXCLUSIONS ===")
        df = apply_trial_exclusions(df, vwm_rows, mrt_rows, exclude_vwm_total, exclude_mrt_total)
        
        # Create output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare output dataframe with required columns
        output_columns = [
            'participantId', 'isPractice', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
            'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees',
            'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_timeout', 'VWM_isAttentionCheck',
            'VWM_block', 'MRT_trial', 'MRT_angle_degrees',
            'MRT_isReflected', 'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_timeout', 
            'MRT_isAttentionCheck', 'MRT_block', 'excluded_from_VWM', 
            'excluded_from_MRT', 'trial_excluded', 'windowFocusLostDuringTasksNum', 
            'windowFocusLostDuringTasksDuration'
        ]

        output_df = df[output_columns].copy()
        
        # Convert block columns to string type with clean labels
        for col in ['VWM_block', 'MRT_block']:
            output_df[col] = output_df[col].fillna(-1).astype(int).astype(str).replace('-1', 'practice')

        # Force string dtype to prevent CSV from converting back to numeric
        output_df['VWM_block'] = output_df['VWM_block'].astype('string')
        output_df['MRT_block'] = output_df['MRT_block'].astype('string')

        # Verify the conversion worked
        print(f"VWM_block dtype after conversion: {output_df['VWM_block'].dtype}")
        print(f"MRT_block dtype after conversion: {output_df['MRT_block'].dtype}")
        print(f"VWM_block sample values: {output_df['VWM_block'].unique()[:10]}")
        print(f"MRT_block sample values: {output_df['MRT_block'].unique()[:10]}")
        
        # Save cleaned data
        output_filename = f"outputs/VWM_MRT_cleaned_data_{timestamp}.csv"
        output_df.to_csv(output_filename, index=False)
        print(f"\nCleaned data saved to: {output_filename}")
        print(f"Output data shape: {output_df.shape}")
        
        # Create and save exclusion log
        exclusion_log = create_exclusion_log()
        
        # Update counts for exclusion log with actual values
        exclusion_log.loc[0, 'count_excluded'] = len(exclude_practice)
        exclusion_log.loc[1, 'count_excluded'] = len(exclude_vwm_performance | exclude_mrt_performance)
        exclusion_log.loc[2, 'count_excluded'] = len(exclude_vwm_attention | exclude_mrt_attention)
        exclusion_log.loc[3, 'count_excluded'] = len(exclude_vwm_timeout | exclude_mrt_timeout)
        exclusion_log.loc[4, 'count_excluded'] = len(exclude_focus)
        exclusion_log.loc[5, 'count_excluded'] = len(exclude_technical)
        
        log_filename = f"outputs/VWM_MRT_exclusion_log_{timestamp}.csv"
        exclusion_log.to_csv(log_filename, index=False)
        print(f"Exclusion log saved to: {log_filename}")

        # Verify CSV output by reading back and checking dtypes
        verification_df = pd.read_csv(output_filename)
        print(f"Verification - VWM_block dtype in saved CSV: {verification_df['VWM_block'].dtype}")
        print(f"Verification - MRT_block dtype in saved CSV: {verification_df['MRT_block'].dtype}")
        print(f"Verification - VWM_block sample values from CSV: {verification_df['VWM_block'].unique()[:10]}")
        print(f"Verification - MRT_block sample values from CSV: {verification_df['MRT_block'].unique()[:10]}")
        
        print("\nExclusion summary:")
        print(exclusion_log)
        
        print("\n=== FINAL DATA SUMMARY ===")
        print(f"Initial participants loaded: {len(unique_participants)}")
        print(f"Participants excluded for practice proficiency: {len(exclude_practice)}")
        print(f"Participants excluded for poor performance: {len(exclude_vwm_performance | exclude_mrt_performance)}")
        print(f"Participants excluded for attention failures: {len(exclude_vwm_attention | exclude_mrt_attention)}")
        print(f"Participants excluded for excessive timeouts: {len(exclude_vwm_timeout | exclude_mrt_timeout)}")
        print(f"Participants excluded for focus loss: {len(exclude_focus)}")
        print(f"Participants excluded for technical issues: {len(exclude_technical)}")
        print(f"Total unique participants excluded from VWM: {len(exclude_vwm_total)}")
        print(f"Total unique participants excluded from MRT: {len(exclude_mrt_total)}")
        print(f"Remaining participants for VWM: {len(unique_participants) - len(exclude_vwm_total)}")
        print(f"Remaining participants for MRT: {len(unique_participants) - len(exclude_mrt_total)}")
        print(f"Total trials flagged as excluded: {output_df['trial_excluded'].sum()}")
        print(f"Total rows in final dataset: {len(output_df)}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
