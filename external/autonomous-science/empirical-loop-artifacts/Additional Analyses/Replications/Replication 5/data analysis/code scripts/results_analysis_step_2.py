#!/usr/bin/env python3
"""
Cognitive Data Cleaning Pipeline for VWM and MRT Tasks

This script processes interleaved data from Visual Working Memory (VWM) and Mental Rotation Task (MRT)
experiments, applying participant-level and trial-level exclusions according to specified criteria.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def create_output_directory():
    """Create outputs directory if it doesn't exist."""
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")

def load_and_combine_data():
    """
    Load all participant data files matching the pattern and combine into single DataFrame.
    Only the most recent file per participant is loaded (by timestamp in filename).
    Filters out non-trial summary rows (where both VWM_trial and MRT_trial are null).
    Also extracts and maps focus loss duration per participant before filtering.
    
    Returns:
        pd.DataFrame: Combined data from all participant files, with focus loss duration mapped
    """
    print("Loading participant data files...")

    # Helper to parse duration to ms
    def parse_duration_to_ms(duration_val):
        if pd.isna(duration_val):
            return 0.0
        if isinstance(duration_val, (int, float)):
            return float(duration_val)  # Ensure numeric return type
        if isinstance(duration_val, str) and ':' in str(duration_val):
            try:
                parts = str(duration_val).split(':')
                if len(parts) == 3:
                    h, m, s = map(float, parts)
                    return (h * 3600 + m * 60 + s) * 1000
            except (ValueError, TypeError):
                return 0.0
        return 0.0

    # Find all matching files
    file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    files = glob.glob(file_pattern)

    print(f"Found {len(files)} participant files")

    if len(files) == 0:
        print(f"ERROR: No files found matching pattern: {file_pattern}")
        return None

    # Required columns
    required_columns = [
        'participantId', 'isPractice', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
        'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees',
        'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_pracAttempt', 'VWM_timeout',
        'VWM_isAttentionCheck', 'MRT_trial', 'MRT_response', 'MRT_isCorrect',
        'MRT_rt_ms', 'MRT_pracAttempt', 'MRT_timeout', 'MRT_isAttentionCheck',
        'MRT_angle_degrees', 'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration'
    ]

    # Parse participantId and timestamp from filenames
    import re
    participant_file_map = {}
    participant_file_info = []
    unmatched_files = []

    for file_path in files:
        # Example: PARTICIPANT_12345_VWM_and_Rotation_Task_2025-05-22_153000.csv
        base = os.path.basename(file_path)
        
        # Try primary pattern with dashes in date
        match = re.match(r"PARTICIPANT_(.+?)_VWM_and_Rotation_Task_(\d{4}-\d{2}-\d{2}_\d{6})\.csv", base)
        if match:
            pid = match.group(1)
            timestamp_str = match.group(2)
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H%M%S")
                participant_file_info.append((pid, timestamp, file_path))
                continue
            except Exception as e:
                print(f"WARNING: Could not parse timestamp for file {file_path}: {e}")
        
        # Try secondary pattern without dashes in date
        match = re.match(r"PARTICIPANT_(.+?)_VWM_and_Rotation_Task_(\d{8}_\d{6})\.csv", base)
        if match:
            pid = match.group(1)
            timestamp_str = match.group(2)
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                participant_file_info.append((pid, timestamp, file_path))
                continue
            except Exception as e:
                print(f"WARNING: Could not parse timestamp for file {file_path}: {e}")
        
        # If no pattern matches, try to extract participant ID and use file modification time
        match = re.match(r"PARTICIPANT_(.+?)_VWM_and_Rotation_Task_.*\.csv", base)
        if match:
            pid = match.group(1)
            try:
                # Use file modification time as fallback
                timestamp = datetime.fromtimestamp(os.path.getmtime(file_path))
                participant_file_info.append((pid, timestamp, file_path))
                print(f"Using file modification time for {file_path}")
                continue
            except Exception as e:
                print(f"WARNING: Could not get modification time for file {file_path}: {e}")
        
        # If all else fails, record as unmatched
        unmatched_files.append(file_path)
        print(f"WARNING: Filename does not match any expected pattern: {file_path}")

    print(f"Successfully parsed {len(participant_file_info)} files")
    print(f"Unmatched files: {len(unmatched_files)}")
    if len(unmatched_files) > 0:
        print("First 5 unmatched files:")
        for i, f in enumerate(unmatched_files[:5]):
            print(f"  {os.path.basename(f)}")
        if len(unmatched_files) > 5:
            print(f"  ... and {len(unmatched_files) - 5} more")

    # Group by participantId, select latest timestamp
    from collections import defaultdict
    pid_to_files = defaultdict(list)
    for pid, timestamp, file_path in participant_file_info:
        pid_to_files[pid].append((timestamp, file_path))

    selected_files = []
    for pid, file_list in pid_to_files.items():
        # Only keep files with valid timestamp
        valid_files = [f for f in file_list if f[0] is not None]
        if not valid_files:
            print(f"WARNING: No valid timestamp files for participant {pid}, skipping.")
            continue
        # Select file with latest timestamp
        latest_file = max(valid_files, key=lambda x: x[0])
        selected_files.append((pid, latest_file[1], latest_file[0]))
        print(f"Selected file for participant {pid}: {latest_file[1]} (timestamp: {latest_file[0]})")

    print(f"Total unique participants with valid files: {len(selected_files)}")

    all_data = []

    for i, (pid, file_path, timestamp) in enumerate(selected_files):
        if i < 3 or i >= len(selected_files) - 2:  # Show first 3 and last 2
            print(f"Loading file: {file_path}")
        elif i == 3:
            print(f"... loading {len(selected_files) - 5} more files ...")
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()  # Strip whitespace from column names

            if i < 3 or i >= len(selected_files) - 2:
                print(f"File shape: {df.shape}")

            # Check for required columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"WARNING: Missing columns in {file_path}: {missing_cols}")
                continue

            if i < 3:  # Only show first 3 file previews
                print(f"First 3 rows of {file_path}:")
                print(df[required_columns].head(3))

            all_data.append(df[required_columns])

        except Exception as e:
            print(f"ERROR loading {file_path}: {e}")
            continue

    if not all_data:
        print("ERROR: No valid data files could be loaded")
        return None

    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined data shape before filtering: {combined_df.shape}")
    print(f"Total participants: {combined_df['participantId'].nunique()}")

    # Convert windowFocusLostDuringTasksDuration to ms for all rows
    print("Converting windowFocusLostDuringTasksDuration to numeric milliseconds...")
    combined_df['windowFocusLostDuringTasksDuration'] = combined_df['windowFocusLostDuringTasksDuration'].apply(parse_duration_to_ms)
    print(f"Conversion complete. Range: [{combined_df['windowFocusLostDuringTasksDuration'].min():.1f}, {combined_df['windowFocusLostDuringTasksDuration'].max():.1f}] ms")

    # Extract focus loss duration and number from summary rows (where both VWM_trial and MRT_trial are null)
    summary_rows = combined_df[(combined_df['VWM_trial'].isna()) & (combined_df['MRT_trial'].isna())]
    focus_loss_duration_map = summary_rows.groupby('participantId')['windowFocusLostDuringTasksDuration'].first().to_dict()
    focus_loss_num_map = summary_rows.groupby('participantId')['windowFocusLostDuringTasksNum'].first().to_dict()

    # Filter out non-trial summary rows (where both VWM_trial and MRT_trial are null)
    filtered_df = combined_df[combined_df['VWM_trial'].notna() | combined_df['MRT_trial'].notna()].copy()
    print(f"Filtered data shape (after removing non-trial summary rows): {filtered_df.shape}")

    # Map focus loss duration and number back to all trial rows
    filtered_df['windowFocusLostDuringTasksDuration'] = filtered_df['participantId'].map(focus_loss_duration_map).fillna(0)
    filtered_df['windowFocusLostDuringTasksNum'] = filtered_df['participantId'].map(focus_loss_num_map).fillna(0)

    return filtered_df

def print_data_structure(df):
    """
    Print detailed information about the data structure and experimental design parameters.
    
    Args:
        df (pd.DataFrame): Input dataframe
    """
    print("\n=== DATA STRUCTURE ANALYSIS ===")
    
    # Print all columns
    print(f"All columns ({len(df.columns)}): {list(df.columns)}")
    
    # Print first 2 rows (truncated)
    print("\nFirst 2 rows (truncated):")
    print(df.head(2).to_string(max_cols=10))
    
    # Print unique values for key experimental design parameters
    print("\n=== EXPERIMENTAL DESIGN PARAMETERS ===")
    
    print(f"Unique VWM_setSize values: {sorted(df['VWM_setSize'].dropna().unique())}")
    print(f"Unique VWM_delay_s values: {sorted(df['VWM_delay_s'].dropna().unique())}")
    print(f"Unique MRT_angle_degrees values: {sorted(df['MRT_angle_degrees'].dropna().unique())}")
    print(f"Unique isPractice values: {sorted(df['isPractice'].dropna().unique())}")
    
    # For measured variables, just print data types
    print(f"VWM_rt_ms data type: {df['VWM_rt_ms'].dtype}")
    print(f"MRT_rt_ms data type: {df['MRT_rt_ms'].dtype}")
    print(f"VWM_error_degrees data type: {df['VWM_error_degrees'].dtype}")
    print(f"VWM_error_absolute_degrees data type: {df['VWM_error_absolute_degrees'].dtype}")
    
    # Task structure analysis
    print("\n=== TASK STRUCTURE ===")
    vwm_rows = df['VWM_trial'].notna().sum()
    mrt_rows = df['MRT_trial'].notna().sum()
    print(f"Rows with VWM data: {vwm_rows}")
    print(f"Rows with MRT data: {mrt_rows}")
    print(f"Total rows: {len(df)}")

def normalize_vwm_errors(df):
    """
    Apply circular normalization to VWM orientation errors to range ±90°.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Dataframe with normalized errors
    """
    print("\n=== NORMALIZING VWM ORIENTATION ERRORS ===")
    
    df = df.copy()
    
    # Initialize normalized error column
    df['VWM_error_normalized_degrees'] = df['VWM_error_degrees'].copy()
    
    # Apply normalization where VWM_error_degrees is not null
    mask = df['VWM_error_degrees'].notna()
    
    # Convert errors > 90° to error - 180°
    mask_high = mask & (df['VWM_error_degrees'] > 90)
    df.loc[mask_high, 'VWM_error_normalized_degrees'] = df.loc[mask_high, 'VWM_error_degrees'] - 180
    
    # Convert errors < -90° to error + 180°
    mask_low = mask & (df['VWM_error_degrees'] < -90)
    df.loc[mask_low, 'VWM_error_normalized_degrees'] = df.loc[mask_low, 'VWM_error_degrees'] + 180
    
    # Count normalizations
    n_high = mask_high.sum()
    n_low = mask_low.sum()
    n_total = mask.sum()
    
    print(f"Total VWM trials with error data: {n_total}")
    print(f"Errors normalized from >90°: {n_high}")
    print(f"Errors normalized from <-90°: {n_low}")
    print(f"Range of normalized errors: [{df['VWM_error_normalized_degrees'].min():.2f}, {df['VWM_error_normalized_degrees'].max():.2f}]")
    
    return df

def apply_participant_exclusions(df):
    """
    Apply participant-level exclusions in specified order.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        tuple: (cleaned_df, participant_status_df, exclusion_log)
    """
    print("\n=== APPLYING PARTICIPANT-LEVEL EXCLUSIONS ===")
    
    participants = df['participantId'].unique()
    initial_n = len(participants)
    print(f"Initial participants: {initial_n}")
    
    # Initialize tracking
    participant_status = []
    exclusion_log = []
    excluded_participants = set()
    
    # For each participant, calculate all metrics first
    for pid in participants:
        p_data = df[df['participantId'] == pid]
        
        status = {
            'participantId': pid,
            'included': True,
            'exclusion_reason': '',
            'VWM_practice_mean_error': np.nan,
            'MRT_practice_accuracy': np.nan,
            'VWM_timeout_percent': np.nan,
            'MRT_timeout_percent': np.nan,
            'VWM_attention_fail_percent': np.nan,
            'MRT_attention_fail_percent': np.nan,
            'MRT_overall_accuracy': np.nan,
            'focus_loss_duration_ms': np.nan
        }
        
        # a. VWM practice failure
        vwm_practice = p_data[(p_data['isPractice'] == True) & (p_data['VWM_trial'].notna())]
        if len(vwm_practice) > 0:
            max_attempt = vwm_practice['VWM_pracAttempt'].max()
            final_attempt = vwm_practice[vwm_practice['VWM_pracAttempt'] == max_attempt]
            if len(final_attempt) > 0:
                mean_error = final_attempt['VWM_error_absolute_degrees'].mean()
                status['VWM_practice_mean_error'] = mean_error
        
        # b. MRT practice failure
        mrt_practice = p_data[(p_data['isPractice'] == True) & (p_data['MRT_trial'].notna())]
        if len(mrt_practice) > 0:
            max_attempt = mrt_practice['MRT_pracAttempt'].max()
            final_attempt = mrt_practice[mrt_practice['MRT_pracAttempt'] == max_attempt]
            if len(final_attempt) > 0:
                accuracy = final_attempt['MRT_isCorrect'].mean()
                status['MRT_practice_accuracy'] = accuracy
        
        # c. Timeout trials
        vwm_test = p_data[(p_data['isPractice'] == False) & (p_data['VWM_trial'].notna())]
        if len(vwm_test) > 0:
            vwm_timeout_pct = (vwm_test['VWM_timeout'] == True).mean() * 100
            status['VWM_timeout_percent'] = vwm_timeout_pct
        
        mrt_test = p_data[(p_data['isPractice'] == False) & (p_data['MRT_trial'].notna())]
        if len(mrt_test) > 0:
            mrt_timeout_pct = (mrt_test['MRT_timeout'] == True).mean() * 100
            status['MRT_timeout_percent'] = mrt_timeout_pct
        
        # d. Attention check failures
        vwm_attn = p_data[(p_data['VWM_isAttentionCheck'] == True) & (p_data['isPractice'] == False) & (p_data['VWM_trial'].notna())]
        if len(vwm_attn) > 0:
            vwm_attn_acc = (vwm_attn['VWM_error_absolute_degrees'] <= 15).mean() * 100
            status['VWM_attention_fail_percent'] = 100 - vwm_attn_acc
        
        mrt_attn = p_data[(p_data['MRT_isAttentionCheck'] == True) & (p_data['isPractice'] == False) & (p_data['MRT_trial'].notna())]
        if len(mrt_attn) > 0:
            mrt_attn_acc = mrt_attn['MRT_isCorrect'].mean() * 100
            status['MRT_attention_fail_percent'] = 100 - mrt_attn_acc
        
        # e. Overall MRT accuracy
        mrt_main = p_data[(p_data['isPractice'] == False) & (p_data['MRT_trial'].notna()) & (p_data['MRT_timeout'] == False)]
        if len(mrt_main) > 0:
            mrt_overall_acc = mrt_main['MRT_isCorrect'].mean() * 100
            status['MRT_overall_accuracy'] = mrt_overall_acc
        
        # f. Focus loss duration
        # Use the mapped per-participant value (should be the same for all rows for this participant)
        if 'windowFocusLostDuringTasksDuration' in p_data.columns:
            focus_loss = p_data['windowFocusLostDuringTasksDuration'].iloc[0] if len(p_data) > 0 else 0
        else:
            focus_loss = 0
        status['focus_loss_duration_ms'] = focus_loss
        
        participant_status.append(status)

    # Now outside the loop: apply exclusions in order
    participant_status_df = pd.DataFrame(participant_status)

    print("\nApplying exclusions in order:")

    # a. VWM practice failure
    print(f"\nDiagnostic: VWM practice errors - Mean: {participant_status_df['VWM_practice_mean_error'].mean():.2f}, Range: [{participant_status_df['VWM_practice_mean_error'].min():.2f}, {participant_status_df['VWM_practice_mean_error'].max():.2f}]")
    print("VWM practice error value counts (binned):")
    print(pd.cut(participant_status_df['VWM_practice_mean_error'], bins=[-np.inf, 10, 15, 20, 25, 30, 40, np.inf]).value_counts().sort_index())
    vwm_practice_fails = participant_status_df[
        (participant_status_df['VWM_practice_mean_error'].notna()) & 
        (participant_status_df['VWM_practice_mean_error'] >= 35)  # Changed from 25
    ]['participantId'].tolist()

    new_vwm_practice_fails = [p for p in vwm_practice_fails if p not in excluded_participants]
    for pid in new_vwm_practice_fails:
        excluded_participants.add(pid)
        idx = participant_status_df[participant_status_df['participantId'] == pid].index[0]
        participant_status_df.loc[idx, 'included'] = False
        participant_status_df.loc[idx, 'exclusion_reason'] = 'VWM_practice_failure'

    print(f"a. VWM practice failure: {len(new_vwm_practice_fails)} participants excluded")

    # b. MRT practice failure
    print(f"\nDiagnostic: MRT practice accuracy - Mean: {participant_status_df['MRT_practice_accuracy'].mean():.3f}, Range: [{participant_status_df['MRT_practice_accuracy'].min():.3f}, {participant_status_df['MRT_practice_accuracy'].max():.3f}]")
    print("MRT practice accuracy value counts (binned):")
    print(pd.cut(participant_status_df['MRT_practice_accuracy'], bins=[-0.01, 0.3, 0.5, 0.583, 0.7, 0.8, 1.0]).value_counts().sort_index())
    mrt_practice_fails = participant_status_df[
        (participant_status_df['MRT_practice_accuracy'].notna()) & 
        (participant_status_df['MRT_practice_accuracy'] <= 7/12)
    ]['participantId'].tolist()

    new_mrt_practice_fails = [p for p in mrt_practice_fails if p not in excluded_participants]
    for pid in new_mrt_practice_fails:
        excluded_participants.add(pid)
        idx = participant_status_df[participant_status_df['participantId'] == pid].index[0]
        participant_status_df.loc[idx, 'included'] = False
        participant_status_df.loc[idx, 'exclusion_reason'] = 'MRT_practice_failure'

    print(f"b. MRT practice failure: {len(new_mrt_practice_fails)} participants excluded")

    # c. Timeout trials
    print(f"\nDiagnostic: VWM timeout percent - Mean: {participant_status_df['VWM_timeout_percent'].mean():.2f}, Range: [{participant_status_df['VWM_timeout_percent'].min():.2f}, {participant_status_df['VWM_timeout_percent'].max():.2f}]")
    print("VWM timeout percent value counts (binned):")
    print(pd.cut(participant_status_df['VWM_timeout_percent'], bins=[-0.01, 5, 10, 15, 20, 30, 100]).value_counts().sort_index())
    print(f"Diagnostic: MRT timeout percent - Mean: {participant_status_df['MRT_timeout_percent'].mean():.2f}, Range: [{participant_status_df['MRT_timeout_percent'].min():.2f}, {participant_status_df['MRT_timeout_percent'].max():.2f}]")
    print("MRT timeout percent value counts (binned):")
    print(pd.cut(participant_status_df['MRT_timeout_percent'], bins=[-0.01, 5, 10, 15, 20, 30, 100]).value_counts().sort_index())
    timeout_fails = participant_status_df[
        ((participant_status_df['VWM_timeout_percent'] > 15) | 
         (participant_status_df['MRT_timeout_percent'] > 15))
    ]['participantId'].tolist()

    new_timeout_fails = [p for p in timeout_fails if p not in excluded_participants]
    for pid in new_timeout_fails:
        excluded_participants.add(pid)
        idx = participant_status_df[participant_status_df['participantId'] == pid].index[0]
        participant_status_df.loc[idx, 'included'] = False
        participant_status_df.loc[idx, 'exclusion_reason'] = 'timeout_trials'

    print(f"c. Timeout trials: {len(new_timeout_fails)} participants excluded")

    # d. Attention check failures
    print(f"\nDiagnostic: VWM attention fail percent - Mean: {participant_status_df['VWM_attention_fail_percent'].mean():.2f}, Range: [{participant_status_df['VWM_attention_fail_percent'].min():.2f}, {participant_status_df['VWM_attention_fail_percent'].max():.2f}]")
    print("VWM attention fail percent value counts (binned):")
    print(pd.cut(participant_status_df['VWM_attention_fail_percent'], bins=[-0.01, 10, 20, 30, 40, 50, 60, 100]).value_counts().sort_index())
    print(f"Diagnostic: MRT attention fail percent - Mean: {participant_status_df['MRT_attention_fail_percent'].mean():.2f}, Range: [{participant_status_df['MRT_attention_fail_percent'].min():.2f}, {participant_status_df['MRT_attention_fail_percent'].max():.2f}]")
    print("MRT attention fail percent value counts (binned):")
    print(pd.cut(participant_status_df['MRT_attention_fail_percent'], bins=[-0.01, 10, 20, 30, 40, 50, 60, 100]).value_counts().sort_index())
    # Threshold: now >67% failure (i.e., <33% accuracy)
    attn_fails = participant_status_df[
        ((participant_status_df['VWM_attention_fail_percent'] > 67) | 
         (participant_status_df['MRT_attention_fail_percent'] > 67))
    ]['participantId'].tolist()

    new_attn_fails = [p for p in attn_fails if p not in excluded_participants]
    for pid in new_attn_fails:
        excluded_participants.add(pid)
        idx = participant_status_df[participant_status_df['participantId'] == pid].index[0]
        participant_status_df.loc[idx, 'included'] = False
        participant_status_df.loc[idx, 'exclusion_reason'] = 'attention_check_failure'

    print(f"d. Attention check failures: {len(new_attn_fails)} participants excluded")

    # e. Overall MRT accuracy
    mrt_acc_fails = participant_status_df[
        (participant_status_df['MRT_overall_accuracy'].notna()) & 
        (participant_status_df['MRT_overall_accuracy'] < 50)
    ]['participantId'].tolist()

    new_mrt_acc_fails = [p for p in mrt_acc_fails if p not in excluded_participants]
    for pid in new_mrt_acc_fails:
        excluded_participants.add(pid)
        idx = participant_status_df[participant_status_df['participantId'] == pid].index[0]
        participant_status_df.loc[idx, 'included'] = False
        participant_status_df.loc[idx, 'exclusion_reason'] = 'MRT_overall_accuracy'

    print(f"e. Overall MRT accuracy: {len(new_mrt_acc_fails)} participants excluded")


    # Correct focus loss exclusion statistics: only use participants not already excluded
    included_participants_df = participant_status_df[participant_status_df['included']]
    if len(included_participants_df) > 0:
        included_focus_values = included_participants_df['focus_loss_duration_ms'].dropna()
        new_focus_fails = []
        if len(included_focus_values) > 0:
            print(f"\nDiagnostic (corrected): Focus loss duration (ms) - Mean: {included_focus_values.mean():.1f}, Std: {included_focus_values.std():.1f}, Range: [{included_focus_values.min():.1f}, {included_focus_values.max():.1f}]")
            print("Focus loss duration value counts (binned):")
            print(pd.cut(included_focus_values, bins=[-0.01, 1000, 5000, 10000, 20000, 40000, 100000, np.inf]).value_counts().sort_index())
            focus_mean = included_focus_values.mean()
            focus_std = included_focus_values.std()
            if pd.notna(focus_std) and focus_std > 0:
                focus_cutoff = focus_mean + 2.5 * focus_std

                focus_fails = participant_status_df[
                    (participant_status_df['focus_loss_duration_ms'] > focus_cutoff) & (participant_status_df['included'])
                ]['participantId'].tolist()

                new_focus_fails = [p for p in focus_fails if p not in excluded_participants]
                for pid in new_focus_fails:
                    excluded_participants.add(pid)
                    idx = participant_status_df[participant_status_df['participantId'] == pid].index[0]
                    participant_status_df.loc[idx, 'included'] = False
                    participant_status_df.loc[idx, 'exclusion_reason'] = 'excessive_focus_loss'

                print(f"f. Excessive focus loss (cutoff: {focus_cutoff:.1f}ms): {len(new_focus_fails)} participants excluded")
            else:
                print("f. Excessive focus loss: Standard deviation is 0 or invalid, no exclusions applied")
        else:
            print("f. Excessive focus loss: No valid focus loss data available")
    else:
        print("f. Excessive focus loss: No included participants available for analysis")
        new_focus_fails = []

    # g. Incomplete task data - Fix the counting logic
    vwm_test_counts = df[(df['isPractice'] == False) & (df['VWM_trial'].notna())]['participantId'].value_counts()
    mrt_test_counts = df[(df['isPractice'] == False) & (df['MRT_trial'].notna())]['participantId'].value_counts()

    max_vwm = vwm_test_counts.max() if not vwm_test_counts.empty else 0
    max_mrt = mrt_test_counts.max() if not mrt_test_counts.empty else 0

    print(f"\nDiagnostic: VWM test trial counts - Max: {max_vwm}, Min: {vwm_test_counts.min() if not vwm_test_counts.empty else 0}")
    print("VWM test trial count value counts (binned):")
    if not vwm_test_counts.empty:
        print(pd.cut(vwm_test_counts, bins=[-0.01, max_vwm*0.5, max_vwm*0.7, max_vwm*0.9, max_vwm]).value_counts().sort_index())
    print(f"Diagnostic: MRT test trial counts - Max: {max_mrt}, Min: {mrt_test_counts.min() if not mrt_test_counts.empty else 0}")
    print("MRT test trial count value counts (binned):")
    if not mrt_test_counts.empty:
        print(pd.cut(mrt_test_counts, bins=[-0.01, max_mrt*0.5, max_mrt*0.7, max_mrt*0.9, max_mrt]).value_counts().sort_index())

    # Use the actual observed mode as expected (since all participants should have same number)
    expected_vwm_trials = vwm_test_counts.mode()[0] if not vwm_test_counts.empty else 126
    expected_mrt_trials = mrt_test_counts.mode()[0] if not mrt_test_counts.empty else 102

    incomplete_pids = []
    vwm_fails = vwm_test_counts[vwm_test_counts < (expected_vwm_trials * 0.9)].index
    mrt_fails = mrt_test_counts[mrt_test_counts < (expected_mrt_trials * 0.9)].index
    incomplete_pids.extend(vwm_fails)
    incomplete_pids.extend(mrt_fails)

    incomplete_fails = list(set(incomplete_pids))
    new_incomplete_fails = [p for p in incomplete_fails if p not in excluded_participants]
    for pid in new_incomplete_fails:
        excluded_participants.add(pid)
        idx = participant_status_df[participant_status_df['participantId'] == pid].index[0]
        participant_status_df.loc[idx, 'included'] = False
        participant_status_df.loc[idx, 'exclusion_reason'] = 'incomplete_task_data'

    print(f"g. Incomplete task data (expected VWM: {expected_vwm_trials}, expected MRT: {expected_mrt_trials}): {len(new_incomplete_fails)} participants excluded")
    
    # Create exclusion log
    exclusion_log = [
        {'exclusion_criterion': 'VWM_practice_failure', 'participants_excluded': len(new_vwm_practice_fails), 'trials_excluded': 0, 'description': 'VWM practice mean error ≥35°'},  # Updated description
        {'exclusion_criterion': 'MRT_practice_failure', 'participants_excluded': len(new_mrt_practice_fails), 'trials_excluded': 0, 'description': 'MRT practice accuracy ≤58.3%'},
        {'exclusion_criterion': 'timeout_trials', 'participants_excluded': len(new_timeout_fails), 'trials_excluded': 0, 'description': '>15% timeout trials in either task'},
        {'exclusion_criterion': 'attention_check_failure', 'participants_excluded': len(new_attn_fails), 'trials_excluded': 0, 'description': '<33% attention check accuracy'},
        {'exclusion_criterion': 'MRT_overall_accuracy', 'participants_excluded': len(new_mrt_acc_fails), 'trials_excluded': 0, 'description': '<50% overall MRT accuracy'},
        {'exclusion_criterion': 'excessive_focus_loss', 'participants_excluded': len(new_focus_fails), 'trials_excluded': 0, 'description': '>2.5 SD above mean focus loss duration'},
        {'exclusion_criterion': 'incomplete_task_data', 'participants_excluded': len(new_incomplete_fails), 'trials_excluded': 0, 'description': '>10% missing trials in either task'}
    ]
    
    # Mark excluded participants' trials directly
    df = df.copy()
    df['excluded_trial'] = df['participantId'].isin(excluded_participants)
    df['exclusion_reason_trial'] = np.where(df['excluded_trial'], 'excluded_participant', '')

    cleaned_df = df

    final_n = initial_n - len(excluded_participants)
    total_excluded = len(excluded_participants)

    print(f"\nParticipant exclusion summary:")
    print(f"Initial: {initial_n}")
    print(f"Final: {final_n}")
    print(f"Total excluded: {total_excluded}")

    return cleaned_df, participant_status_df, exclusion_log

def apply_trial_exclusions(df, exclusion_log, participant_status_df):
    """
    Apply trial-level exclusions to remaining participants.

    Args:
        df (pd.DataFrame): Input dataframe with included participants only
        exclusion_log (list): Existing exclusion log to append to
        participant_status_df (pd.DataFrame): DataFrame with participant inclusion status

    Returns:
        tuple: (cleaned_df, updated_exclusion_log)
    """
    print("\n=== APPLYING TRIAL-LEVEL EXCLUSIONS ===")

    df = df.copy()
    initial_trials = len(df)
    print(f"Initial trials: {initial_trials}")

    # Only process included participants for outlier detection
    included_pids = participant_status_df[participant_status_df['included']]['participantId'].tolist()

    # a. Remove timeout trials
    timeout_mask = ((df['VWM_timeout'] == True) | (df['MRT_timeout'] == True)).fillna(False)
    newly_excluded_timeout_mask = timeout_mask & ~df['excluded_trial']
    df.loc[newly_excluded_timeout_mask, 'excluded_trial'] = True
    df.loc[newly_excluded_timeout_mask, 'exclusion_reason_trial'] = 'timeout'
    timeout_excluded = newly_excluded_timeout_mask.sum()
    print(f"a. Timeout trials excluded: {timeout_excluded}")

    # b. Remove anticipatory responses
    anticipatory_mask = ((df['VWM_rt_ms'] < 200) | (df['MRT_rt_ms'] < 200)).fillna(False)
    newly_excluded_anticipatory_mask = anticipatory_mask & ~df['excluded_trial']
    df.loc[newly_excluded_anticipatory_mask, 'excluded_trial'] = True
    df.loc[newly_excluded_anticipatory_mask, 'exclusion_reason_trial'] = 'anticipatory_response'
    anticipatory_excluded = newly_excluded_anticipatory_mask.sum()
    print(f"b. Anticipatory responses excluded: {anticipatory_excluded}")

    # c. MRT outliers (>2.5 SD from individual participant mean within each angle condition)
    mrt_outlier_excluded = 0
    for pid in included_pids:
        p_data = df[(df['participantId'] == pid) & (df['isPractice'] == False) &
                   (df['MRT_trial'].notna()) & (df['MRT_isCorrect'] == True) & (~df['excluded_trial'])]

        for angle in p_data['MRT_angle_degrees'].dropna().unique():
            angle_mask = (df['participantId'] == pid) & (df['isPractice'] == False) & \
                        (df['MRT_trial'].notna()) & (df['MRT_isCorrect'] == True) & \
                        (df['MRT_angle_degrees'] == angle) & (~df['excluded_trial'])
            angle_data = df[angle_mask]

            if len(angle_data) > 0:
                mean_rt = angle_data['MRT_rt_ms'].mean()
                std_rt = angle_data['MRT_rt_ms'].std()

                if pd.notna(std_rt) and std_rt > 0:
                    cutoff = mean_rt + 2.5 * std_rt
                    outlier_mask = angle_mask & (df['MRT_rt_ms'] > cutoff)
                    newly_excluded_outlier_mask = outlier_mask & ~df['excluded_trial']
                    df.loc[newly_excluded_outlier_mask, 'excluded_trial'] = True
                    df.loc[newly_excluded_outlier_mask, 'exclusion_reason_trial'] = 'MRT_outlier'
                    mrt_outlier_excluded += newly_excluded_outlier_mask.sum()

    print(f"c. MRT outliers excluded: {mrt_outlier_excluded}")

    # d. Remove attention check trials from analysis
    attention_mask_base = ((df['VWM_isAttentionCheck'] == True) | (df['MRT_isAttentionCheck'] == True)).fillna(False)
    newly_excluded_attention_mask = attention_mask_base & ~df['excluded_trial']
    df.loc[newly_excluded_attention_mask, 'excluded_trial'] = True
    df.loc[newly_excluded_attention_mask, 'exclusion_reason_trial'] = 'attention_check'
    attention_excluded = newly_excluded_attention_mask.sum()
    print(f"d. Attention check trials excluded: {attention_excluded}")

    # Update exclusion log
    trial_exclusions = [
        {'exclusion_criterion': 'timeout_trials_trial_level', 'participants_excluded': 0, 'trials_excluded': timeout_excluded, 'description': 'Trial-level timeout exclusions'},
        {'exclusion_criterion': 'anticipatory_responses', 'participants_excluded': 0, 'trials_excluded': anticipatory_excluded, 'description': 'RT < 200ms'},
        {'exclusion_criterion': 'MRT_outliers', 'participants_excluded': 0, 'trials_excluded': mrt_outlier_excluded, 'description': 'MRT RT >2.5 SD from participant mean within angle'},
        {'exclusion_criterion': 'attention_check_trials', 'participants_excluded': 0, 'trials_excluded': attention_excluded, 'description': 'Attention check trials removed from analysis'}
    ]

    exclusion_log.extend(trial_exclusions)

    total_excluded_trials = df['excluded_trial'].sum()
    remaining_trials = len(df) - total_excluded_trials

    print(f"\nTrial exclusion summary:")
    print(f"Initial trials: {initial_trials}")
    print(f"Excluded trials: {total_excluded_trials}")
    print(f"Remaining trials: {remaining_trials}")

    return df, exclusion_log

def create_trial_type_column(df):
    """
    Create trial_type column to identify which task each trial belongs to.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Dataframe with trial_type column added
    """
    print("\n=== CREATING TRIAL TYPE COLUMN ===")
    
    df = df.copy()

    # Initialize trial_type column as string
    df['trial_type'] = 'None'

    # VWM trials
    vwm_mask = df['VWM_trial'].notna()
    df.loc[vwm_mask, 'trial_type'] = 'VWM'

    # MRT trials
    mrt_mask = df['MRT_trial'].notna()
    df.loc[mrt_mask, 'trial_type'] = 'MRT'

    # Handle any overlaps (shouldn't happen but just in case)
    overlap_mask = vwm_mask & mrt_mask
    if overlap_mask.sum() > 0:
        print(f"WARNING: {overlap_mask.sum()} trials have both VWM and MRT data")

    print(f"Trial type distribution:")
    print(df['trial_type'].value_counts())

    return df

def save_outputs(cleaned_df, participant_status_df, exclusion_log):
    """
    Save all output files with timestamp.
    
    Args:
        cleaned_df (pd.DataFrame): Cleaned data
        participant_status_df (pd.DataFrame): Participant inclusion status
        exclusion_log (list): List of exclusion criteria and counts
    """
    print("\n=== SAVING OUTPUT FILES ===")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare cleaned data for output
    output_columns = [
        'participantId', 'isPractice', 'trial_type', 'VWM_trial', 'VWM_setSize',
        'VWM_delay_s', 'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees',
        'VWM_error_normalized_degrees', 'VWM_error_absolute_degrees', 'VWM_rt_ms',
        'VWM_isAttentionCheck', 'MRT_trial', 'MRT_angle_degrees', 'MRT_response',
        'MRT_isCorrect', 'MRT_rt_ms', 'MRT_isAttentionCheck',
        'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration',
        'excluded_trial', 'exclusion_reason_trial'
    ]
    
    # Include all data with proper exclusion flags
    output_df = cleaned_df[output_columns].copy()
    
    # Save cleaned data
    cleaned_filename = f"outputs/cleaned_cognitive_data_{timestamp}.csv"
    output_df.to_csv(cleaned_filename, index=False)
    print(f"Saved cleaned data: {cleaned_filename}")
    print(f"Cleaned data shape: {output_df.shape}")
    print("Cleaned data columns:", list(output_df.columns))
    print("First 2 rows of cleaned data:")
    print(output_df.head(2))
    
    # Save participant status
    status_filename = f"outputs/participant_inclusion_status_{timestamp}.csv"
    participant_status_df.to_csv(status_filename, index=False)
    print(f"Saved participant status: {status_filename}")
    print(f"Participant status shape: {participant_status_df.shape}")
    print("Participant status columns:", list(participant_status_df.columns))
    print("First 2 rows of participant status:")
    print(participant_status_df.head(2))
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusion_log)
    log_filename = f"outputs/data_cleaning_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(log_filename, index=False)
    print(f"Saved exclusion log: {log_filename}")
    print(f"Exclusion log shape: {exclusion_df.shape}")
    print("Exclusion log:")
    print(exclusion_df)

def main():
    """Main execution function."""
    try:
        print("=== COGNITIVE DATA CLEANING PIPELINE ===")
        
        # Create output directory
        create_output_directory()
        
        # Load and combine data
        df = load_and_combine_data()
        if df is None:
            print("ERROR: Failed to load data")
            return 1

        # Ensure boolean columns are properly handled with robust conversion
        boolean_columns = ['isPractice', 'VWM_timeout', 'VWM_isAttentionCheck', 'MRT_isCorrect', 'MRT_timeout', 'MRT_isAttentionCheck']
        for col in boolean_columns:
            if col in df.columns:
                # First convert string representations with proper type checking
                df[col] = df[col].replace({
                    'true': True, 'false': False, 'True': True, 'False': False,
                    'TRUE': True, 'FALSE': False, '1': True, '0': False,
                    1: True, 0: False, 'yes': True, 'no': False,
                    'Yes': True, 'No': False, 'YES': True, 'NO': False
                })
                # Convert to boolean and fill NaN values appropriately
                try:
                    if col == 'isPractice':
                        # Fill NaN values with False (assuming non-practice trials)
                        df[col] = df[col].astype('boolean').fillna(False)
                    else:
                        # For other boolean columns, fill NaN with False as default
                        df[col] = df[col].astype('boolean').fillna(False)
                except Exception as e:
                    print(f"Warning: Could not convert {col} to boolean: {e}")
                    df[col] = False

        print("Boolean column conversion complete.")

        # Create trial type column early
        df = create_trial_type_column(df)

        # Print data structure
        print_data_structure(df)
        
        # Normalize VWM errors
        df = normalize_vwm_errors(df)
        
        # Apply participant exclusions
        cleaned_df, participant_status_df, exclusion_log = apply_participant_exclusions(df)
        
        # Apply trial exclusions
        cleaned_df, exclusion_log = apply_trial_exclusions(cleaned_df, exclusion_log, participant_status_df)

        # Save outputs
        save_outputs(cleaned_df, participant_status_df, exclusion_log)

        # Print comprehensive final summary
        print("\n=== FINAL DATA CLEANING SUMMARY ===")
        total_participants = len(participant_status_df)
        included_participants = participant_status_df['included'].sum()
        excluded_participants = total_participants - included_participants

        total_trials = len(cleaned_df)
        excluded_trials = cleaned_df['excluded_trial'].sum()
        included_trials = total_trials - excluded_trials

        print(f"PARTICIPANTS:")
        print(f"  Total: {total_participants}")
        print(f"  Included: {included_participants}")
        print(f"  Excluded: {excluded_participants}")
        print(f"TRIALS:")
        print(f"  Total: {total_trials}")
        print(f"  Included: {included_trials}")
        print(f"  Excluded: {excluded_trials}")

        print(f"\nEXCLUSION BREAKDOWN:")
        for entry in exclusion_log:
            if entry['participants_excluded'] > 0:
                print(f"  {entry['exclusion_criterion']}: {entry['participants_excluded']} participants")
            if entry['trials_excluded'] > 0:
                print(f"  {entry['exclusion_criterion']}: {entry['trials_excluded']} trials")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
