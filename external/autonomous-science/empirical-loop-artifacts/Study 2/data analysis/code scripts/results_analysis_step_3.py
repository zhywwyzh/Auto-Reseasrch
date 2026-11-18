#!/usr/bin/env python3
"""
MRT (Mental Rotation Task) Data Cleaning Script

This script processes Mental Rotation Task data from CSV files, applying various
exclusion criteria at participant and trial levels, and outputs cleaned data
with calculated variables.
"""

import pandas as pd
import numpy as np
import glob
import os
import re
from datetime import datetime
import sys

def parse_duration_to_seconds(duration_str):
    """
    Parse duration string to seconds.
    
    Parameters:
    duration_str (str): Duration string in various formats (e.g., "PT5.2S", "5.2s", "5200ms")
    
    Returns:
    float: Duration in seconds, or 0 if parsing fails
    """
    if pd.isna(duration_str) or duration_str == '' or duration_str is None:
        return 0.0
    
    duration_str = str(duration_str).strip()
    
    # Handle ISO 8601 duration format (PT5.2S)
    if duration_str.startswith('PT') and duration_str.endswith('S'):
        try:
            seconds_part = duration_str[2:-1]  # Remove 'PT' and 'S'
            return float(seconds_part)
        except ValueError:
            return 0.0
    
    # Handle simple seconds format (5.2s)
    if duration_str.endswith('s') and not duration_str.endswith('ms'):
        try:
            seconds_part = duration_str[:-1]  # Remove 's'
            return float(seconds_part)
        except ValueError:
            return 0.0
    
    # Handle milliseconds format (5200ms)
    if duration_str.endswith('ms'):
        try:
            ms_part = duration_str[:-2]  # Remove 'ms'
            return float(ms_part) / 1000.0
        except ValueError:
            return 0.0
    
    # Try to parse as plain number (assume seconds)
    try:
        return float(duration_str)
    except ValueError:
        return 0.0

def load_and_combine_data(file_pattern):
    """
    Load and combine all CSV files matching the pattern.
    
    Parameters:
    file_pattern (str): Glob pattern for input files
    
    Returns:
    pd.DataFrame: Combined dataframe from all matching files
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} files: {files}")
    
    if not files:
        print("No files found matching the pattern!")
        return pd.DataFrame()
    
    all_data = []
    
    for file in files:
        print(f"\nLoading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File shape: {df.shape}")
            print(f"Columns in file: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            all_data.append(df)
        except Exception as e:
            print(f"Error loading file {file}: {e}")
            continue
    
    if not all_data:
        print("No valid data files found!")
        return pd.DataFrame()
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined data shape: {combined_df.shape}")
    print(f"Combined data columns: {list(combined_df.columns)}")
    
    return combined_df

def check_incomplete_data(df, required_columns):
    """
    Check for participants with incomplete data in required columns.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    required_columns (list): List of required column names
    
    Returns:
    set: Set of participant IDs with incomplete data
    """
    print("\nChecking for incomplete datasets...")
    
    incomplete_participants = set()
    
    # Critical columns that must have data for valid trials
    critical_columns = ['MRT_trial', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms']
    
    # Check if dataframe is empty
    if df.empty:
        print("Dataframe is empty, cannot check for incomplete data")
        return incomplete_participants
    
    # Check each participant
    for participant_id in df['participantId'].unique():
        participant_data = df[df['participantId'] == participant_id]
        
        # Check for missing critical data in test trials
        if 'isPractice' in df.columns:
            test_trials = participant_data[participant_data['isPractice'] == False]
            if not test_trials.empty:
                for col in critical_columns:
                    if col in df.columns:
                        # Check if column exists and all values are NaN
                        if test_trials[col].isna().all():
                            print(f"Participant {participant_id} missing all data for {col}")
                            incomplete_participants.add(participant_id)
                            break
                    else:
                        # Column doesn't exist at all
                        print(f"Critical column {col} missing from dataset")
                        incomplete_participants.add(participant_id)
                        break
        else:
            print(f"isPractice column not found, cannot identify test trials for participant {participant_id}")
            incomplete_participants.add(participant_id)
    
    print(f"Found {len(incomplete_participants)} participants with incomplete data")
    
    return incomplete_participants

def filter_mrt_data(df):
    """
    Filter data to include only MRT-related rows.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Filtered dataframe containing only MRT rows
    """
    print("\nFiltering MRT-related rows...")
    
    # Check if 'table' column exists
    if 'table' not in df.columns:
        print("Warning: 'table' column not found. Cannot filter MRT data.")
        return pd.DataFrame()
    
    # Print unique values in table column
    print(f"Unique values in 'table' column: {df['table'].unique()}")
    
    # Filter for MRT-related rows (case-insensitive)
    mrt_mask = df['table'].str.contains('mrt|rotation', case=False, na=False)
    mrt_df = df[mrt_mask].copy()
    
    print(f"Original data shape: {df.shape}")
    print(f"MRT data shape: {mrt_df.shape}")
    print(f"Rows filtered out: {df.shape[0] - mrt_df.shape[0]}")
    
    if mrt_df.empty:
        print("No MRT data found!")
        return mrt_df
    
    # Print first 2 rows of filtered data
    print("First 2 rows of MRT data:")
    print(mrt_df.head(2))
    
    return mrt_df

def check_required_columns(df, required_columns):
    """
    Check if all required columns are present in the dataframe.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    required_columns (list): List of required column names
    
    Returns:
    bool: True if all required columns are present, False otherwise
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    return True

def apply_participant_exclusions(df, exclusion_log):
    """
    Apply participant-level exclusions.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    exclusion_log (list): List to track exclusions
    
    Returns:
    tuple: (Dataframe with excluded participants flagged, Dictionary of exclusions by criterion)
    """
    print("\nApplying participant-level exclusions...")
    
    # Separate practice and test trials
    practice_df = df[df['isPractice'] == True].copy()
    test_df = df[df['isPractice'] == False].copy()
    
    print(f"Practice trials: {len(practice_df)}")
    print(f"Test trials: {len(test_df)}")
    
    # Print unique values for key columns
    print(f"Unique MRT_angle_degrees: {sorted(df['MRT_angle_degrees'].dropna().unique())}")
    print(f"Unique MRT_isReflected: {df['MRT_isReflected'].dropna().unique()}")
    print(f"Unique MRT_response: {df['MRT_response'].dropna().unique()}")
    print(f"Unique MRT_isCorrect: {df['MRT_isCorrect'].dropna().unique()}")
    print(f"Unique MRT_timeout: {df['MRT_timeout'].dropna().unique()}")
    print(f"Unique MRT_isAttentionCheck: {df['MRT_isAttentionCheck'].dropna().unique()}")
    print(f"Unique isPractice: {df['isPractice'].dropna().unique()}")
    print(f"MRT_rt_ms data type: {df['MRT_rt_ms'].dtype}")
    
    excluded_participants = set()
    initial_participants = set(df['participantId'].unique())
    
    print(f"Initial participants: {len(initial_participants)}")
    
    # Track exclusions by criterion
    exclusion_by_criterion = {}
    
    # 1. Failed >50% of attention check trials (>=3 incorrect out of 6, >50% failure rate)
    print("\n1. Checking attention check failures...")
    attention_check_df = test_df[test_df['MRT_isAttentionCheck'] == True].copy()
    
    if not attention_check_df.empty:
        attention_stats = attention_check_df.groupby('participantId').agg({
            'MRT_isCorrect': ['count', 'sum']
        }).round(3)
        attention_stats.columns = ['total_attention_checks', 'correct_attention_checks']
        attention_stats['incorrect_attention_checks'] = attention_stats['total_attention_checks'] - attention_stats['correct_attention_checks']
        
        # Changed threshold to >=3 (allowing up to 2 incorrect out of 6)
        failed_attention = attention_stats[attention_stats['incorrect_attention_checks'] >= 3]['incorrect_attention_checks']
        excluded_attention = set(failed_attention.index)
        excluded_participants.update(excluded_attention)
        exclusion_by_criterion['Failed >50% attention checks'] = excluded_attention
        
        print(f"Participants with >=3 incorrect attention checks: {len(excluded_attention)}")
        print(f"Attention check failure distribution (>=3 incorrect = excluded, >50% failure rate):")
        if not attention_stats.empty:
            for i in range(1, 7):
                count = len(attention_stats[attention_stats['incorrect_attention_checks'] == i])
                if count > 0:
                    if len(attention_stats) > 0:  # Avoid division by zero
                        percentage = count/len(attention_stats)*100
                    else:
                        percentage = 0
                    print(f"  {i} incorrect: {count} participants ({percentage:.1f}%)")
        else:
            print("  No attention check data available")
        
        # Avoid division by zero
        if len(initial_participants) > 0:
            exclusion_percentage = len(excluded_attention)/len(initial_participants)*100
        else:
            exclusion_percentage = 0
        exclusion_log.append(['Failed >50% attention checks', len(excluded_attention), len(initial_participants), exclusion_percentage])
    else:
        print("No attention check trials found")
        exclusion_log.append(['Failed >50% attention checks', 0, len(initial_participants), 0])
        exclusion_by_criterion['Failed >50% attention checks'] = set()
    
    # 2. >30% timeout trials
    print("\n2. Checking timeout rates...")
    timeout_stats = test_df.groupby('participantId').agg({
        'MRT_timeout': ['count', 'sum']
    }).round(3)
    timeout_stats.columns = ['total_trials', 'timeout_trials']
    timeout_stats['timeout_rate'] = timeout_stats['timeout_trials'] / timeout_stats['total_trials']
    
    high_timeout = timeout_stats[timeout_stats['timeout_rate'] > 0.30]['timeout_rate']
    excluded_timeout = set(high_timeout.index)
    excluded_participants.update(excluded_timeout)
    exclusion_by_criterion['Timeout rate >30%'] = excluded_timeout
    
    print(f"Participants with >30% timeout rate: {len(excluded_timeout)}")
    # Avoid division by zero
    if len(initial_participants) > 0:
        exclusion_percentage = len(excluded_timeout)/len(initial_participants)*100
    else:
        exclusion_percentage = 0
    exclusion_log.append(['Timeout rate >30%', len(excluded_timeout), len(initial_participants), exclusion_percentage])
    
    # 3. Required >8 practice attempts
    print("\n3. Checking practice attempts...")
    if not practice_df.empty and 'MRT_pracAttempt' in practice_df.columns:
        max_practice_attempts = practice_df.groupby('participantId')['MRT_pracAttempt'].max()
        high_practice = max_practice_attempts[max_practice_attempts > 8]
        excluded_practice = set(high_practice.index)
        excluded_participants.update(excluded_practice)
        exclusion_by_criterion['Practice attempts >8'] = excluded_practice
        
        print(f"Participants with >8 practice attempts: {len(excluded_practice)}")
        # Avoid division by zero
        if len(initial_participants) > 0:
            exclusion_percentage = len(excluded_practice)/len(initial_participants)*100
        else:
            exclusion_percentage = 0
        exclusion_log.append(['Practice attempts >8', len(excluded_practice), len(initial_participants), exclusion_percentage])
    else:
        print("No practice data or MRT_pracAttempt column found")
        exclusion_log.append(['Practice attempts >8', 0, len(initial_participants), 0])
        exclusion_by_criterion['Practice attempts >8'] = set()
    
    # 4. Mean response time >3 SD from sample mean (correct trials only)
    print("\n4. Checking mean response times...")
    correct_test_df = test_df[(test_df['MRT_isCorrect'] == True) & (pd.notna(test_df['MRT_rt_ms']))].copy()
    
    if not correct_test_df.empty:
        participant_mean_rt = correct_test_df.groupby('participantId')['MRT_rt_ms'].mean()
        sample_mean_rt = participant_mean_rt.mean()
        sample_std_rt = participant_mean_rt.std()
        rt_threshold = sample_mean_rt + 3 * sample_std_rt
        
        print(f"Sample mean RT: {sample_mean_rt:.2f}ms")
        print(f"Sample std RT: {sample_std_rt:.2f}ms")
        print(f"RT threshold (mean + 3*SD): {rt_threshold:.2f}ms")
        
        slow_rt = participant_mean_rt[participant_mean_rt > rt_threshold]
        excluded_rt = set(slow_rt.index)
        excluded_participants.update(excluded_rt)
        exclusion_by_criterion['Mean RT >3 SD'] = excluded_rt
        
        print(f"Participants with mean RT >3 SD: {len(excluded_rt)}")
        # Avoid division by zero
        if len(initial_participants) > 0:
            exclusion_percentage = len(excluded_rt)/len(initial_participants)*100
        else:
            exclusion_percentage = 0
        exclusion_log.append(['Mean RT >3 SD', len(excluded_rt), len(initial_participants), exclusion_percentage])
    else:
        print("No correct test trials found for RT analysis")
        exclusion_log.append(['Mean RT >3 SD', 0, len(initial_participants), 0])
        exclusion_by_criterion['Mean RT >3 SD'] = set()
    
    # 5. Overall accuracy >3 SD below sample mean
    print("\n5. Checking overall accuracy...")
    if not test_df.empty:
        participant_accuracy = test_df.groupby('participantId')['MRT_isCorrect'].mean()
        sample_mean_acc = participant_accuracy.mean()
        sample_std_acc = participant_accuracy.std()
        acc_threshold = sample_mean_acc - 3 * sample_std_acc
        
        print(f"Sample mean accuracy: {sample_mean_acc:.3f}")
        print(f"Sample std accuracy: {sample_std_acc:.3f}")
        print(f"Accuracy threshold (mean - 3*SD): {acc_threshold:.3f}")
        
        low_acc = participant_accuracy[participant_accuracy < acc_threshold]
        excluded_acc = set(low_acc.index)
        excluded_participants.update(excluded_acc)
        exclusion_by_criterion['Accuracy <3 SD below mean'] = excluded_acc
        
        print(f"Participants with accuracy <3 SD below mean: {len(excluded_acc)}")
        # Avoid division by zero
        if len(initial_participants) > 0:
            exclusion_percentage = len(excluded_acc)/len(initial_participants)*100
        else:
            exclusion_percentage = 0
        exclusion_log.append(['Accuracy <3 SD below mean', len(excluded_acc), len(initial_participants), exclusion_percentage])
    else:
        print("No test trials found for accuracy analysis")
        exclusion_log.append(['Accuracy <3 SD below mean', 0, len(initial_participants), 0])
        exclusion_by_criterion['Accuracy <3 SD below mean'] = set()
    
    # 6. Browser compatibility (webGLsupport = False AND frameRate < 15)
    print("\n6. Checking browser compatibility...")
    if 'webGLsupport' in df.columns and 'frameRate' in df.columns:
        participant_tech = df.groupby('participantId').agg({
            'webGLsupport': 'first',
            'frameRate': 'first'
        })
        
        tech_excluded = participant_tech[
            (participant_tech['webGLsupport'] == False) & 
            (participant_tech['frameRate'] < 15)
        ]
        excluded_tech = set(tech_excluded.index)
        excluded_participants.update(excluded_tech)
        exclusion_by_criterion['Poor browser compatibility'] = excluded_tech
        
        print(f"Participants with poor browser compatibility: {len(excluded_tech)}")
        # Avoid division by zero
        if len(initial_participants) > 0:
            exclusion_percentage = len(excluded_tech)/len(initial_participants)*100
        else:
            exclusion_percentage = 0
        exclusion_log.append(['Poor browser compatibility', len(excluded_tech), len(initial_participants), exclusion_percentage])
    else:
        print("Browser compatibility columns not found")
        exclusion_log.append(['Poor browser compatibility', 0, len(initial_participants), 0])
        exclusion_by_criterion['Poor browser compatibility'] = set()
    
    # Print summary of exclusions by criterion
    print("\nExclusion summary by criterion:")
    for criterion, excluded in exclusion_by_criterion.items():
        if excluded:
            print(f"  {criterion}: {len(excluded)} participants")
    
    # Mark trials of excluded participants instead of removing them
    print(f"\nTotal excluded participants: {len(excluded_participants)}")
    print(f"Remaining participants: {len(initial_participants) - len(excluded_participants)}")
    
    # Initialize exclusion tracking columns if they don't exist
    if 'excluded_trial' not in df.columns:
        df['excluded_trial'] = False
    if 'exclusion_reason_trial' not in df.columns:
        df['exclusion_reason_trial'] = ''
    
    # Mark all trials from excluded participants
    if excluded_participants:
        df.loc[df['participantId'].isin(excluded_participants), 'excluded_trial'] = True
        df.loc[df['participantId'].isin(excluded_participants), 'exclusion_reason_trial'] = 'Participant excluded'
    
    print(f"Data shape: {df.shape}")
    print(f"Trials marked as excluded due to participant exclusions: {df['excluded_trial'].sum()}")
    
    return df, exclusion_by_criterion

def apply_trial_exclusions(df, exclusion_log):
    """
    Apply trial-level exclusions for test trials.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    exclusion_log (list): List to track exclusions
    
    Returns:
    pd.DataFrame: Dataframe with exclusion flags added
    """
    print("\nApplying trial-level exclusions...")
    
    # Exclusion tracking should already be initialized
    # We'll only apply exclusions to test trials
    
    # Only apply trial exclusions to test trials
    test_mask = df['isPractice'] == False
    test_df = df[test_mask].copy()
    
    print(f"Test trials to evaluate: {len(test_df)}")
    
    initial_test_trials = len(test_df)
    
    # 1. Response times <200ms
    print("\n1. Excluding trials with RT <200ms...")
    fast_rt_mask = (test_df['MRT_rt_ms'] < 200) & pd.notna(test_df['MRT_rt_ms'])
    fast_rt_count = fast_rt_mask.sum()
    
    df.loc[test_mask & fast_rt_mask, 'excluded_trial'] = True
    df.loc[test_mask & fast_rt_mask, 'exclusion_reason_trial'] = 'RT < 200ms'
    
    print(f"Trials with RT <200ms: {fast_rt_count}")
    exclusion_log.append(['RT < 200ms', fast_rt_count, initial_test_trials, fast_rt_count/initial_test_trials*100])
    
    # 2. Response times >7000ms or timeout
    print("\n2. Excluding trials with RT >7000ms or timeout...")
    slow_rt_mask = ((test_df['MRT_rt_ms'] > 7000) | (test_df['MRT_timeout'] == True)) & pd.notna(test_df['MRT_rt_ms'])
    slow_rt_count = slow_rt_mask.sum()
    
    df.loc[test_mask & slow_rt_mask, 'excluded_trial'] = True
    df.loc[test_mask & slow_rt_mask, 'exclusion_reason_trial'] = 'RT > 7000ms or timeout'
    
    print(f"Trials with RT >7000ms or timeout: {slow_rt_count}")
    exclusion_log.append(['RT > 7000ms or timeout', slow_rt_count, initial_test_trials, slow_rt_count/initial_test_trials*100])
    
    # 3. First trial of each block
    print("\n3. Excluding first trial of each block...")
    first_trial_mask = test_df['MRT_trial'] == 1
    first_trial_count = first_trial_mask.sum()
    
    df.loc[test_mask & first_trial_mask, 'excluded_trial'] = True
    df.loc[test_mask & first_trial_mask, 'exclusion_reason_trial'] = 'First trial of block'
    
    print(f"First trials of blocks: {first_trial_count}")
    exclusion_log.append(['First trial of block', first_trial_count, initial_test_trials, first_trial_count/initial_test_trials*100])
    
    # 4. All attention check trials
    print("\n4. Excluding attention check trials...")
    attention_mask = test_df['MRT_isAttentionCheck'] == True
    attention_count = attention_mask.sum()
    
    df.loc[test_mask & attention_mask, 'excluded_trial'] = True
    df.loc[test_mask & attention_mask, 'exclusion_reason_trial'] = 'Attention check trial'
    
    print(f"Attention check trials: {attention_count}")
    exclusion_log.append(['Attention check trial', attention_count, initial_test_trials, attention_count/initial_test_trials*100])
    
    # 5. Trials where participant exited fullscreen
    print("\n5. Excluding trials with fullscreen exit...")
    if 'wasFullscreenExited' in df.columns:
        fullscreen_mask = test_df['wasFullscreenExited'] == True
        fullscreen_count = fullscreen_mask.sum()
        
        df.loc[test_mask & fullscreen_mask, 'excluded_trial'] = True
        df.loc[test_mask & fullscreen_mask, 'exclusion_reason_trial'] = 'Fullscreen exited'
        
        print(f"Trials with fullscreen exit: {fullscreen_count}")
        exclusion_log.append(['Fullscreen exited', fullscreen_count, initial_test_trials, fullscreen_count/initial_test_trials*100])
    else:
        print("wasFullscreenExited column not found")
        exclusion_log.append(['Fullscreen exited', 0, initial_test_trials, 0])
    
    # 6. Window focus lost >5 seconds
    print("\n6. Excluding trials with window focus lost >5 seconds...")
    if 'windowFocusLostDuringTasksDuration' in df.columns:
        df['focus_lost_seconds'] = df['windowFocusLostDuringTasksDuration'].apply(parse_duration_to_seconds)
        # Fix: Use test_mask to properly filter the dataframe first
        focus_mask = test_mask & (df['focus_lost_seconds'] > 5)
        focus_count = focus_mask.sum()
        
        # Apply exclusion to the correct rows
        df.loc[focus_mask, 'excluded_trial'] = True
        df.loc[focus_mask, 'exclusion_reason_trial'] = 'Window focus lost >5s'
        
        print(f"Trials with focus lost >5s: {focus_count}")
        exclusion_log.append(['Window focus lost >5s', focus_count, initial_test_trials, focus_count/initial_test_trials*100])
    else:
        print("windowFocusLostDuringTasksDuration column not found")
        exclusion_log.append(['Window focus lost >5s', 0, initial_test_trials, 0])
    
    total_excluded = df[test_mask]['excluded_trial'].sum()
    print(f"\nTotal test trials excluded: {total_excluded}")
    print(f"Remaining valid test trials: {initial_test_trials - total_excluded}")
    
    return df

def calculate_variables(df):
    """
    Calculate required variables for the analysis.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Dataframe with calculated variables added
    """
    print("\nCalculating required variables...")
    
    # Initialize new columns
    df['log_rt_ms'] = np.nan
    df['previous_angle_degrees'] = np.nan
    df['abs_angular_disparity_change'] = np.nan
    df['previous_trial_correct'] = pd.NA  # Use pandas NA for boolean values
    
    # 1. Log-transform reaction times (for correct trials only)
    print("1. Calculating log-transformed reaction times...")
    if not df.empty and 'MRT_isCorrect' in df.columns and 'MRT_rt_ms' in df.columns:
        correct_mask = (df['MRT_isCorrect'] == True) & pd.notna(df['MRT_rt_ms']) & (df['MRT_rt_ms'] > 0)
        if correct_mask.any():  # Check if any trials meet the criteria
            df.loc[correct_mask, 'log_rt_ms'] = np.log(df.loc[correct_mask, 'MRT_rt_ms'])
    else:
        print("Warning: Required columns for log RT calculation missing or dataframe is empty")
    
    log_rt_count = df['log_rt_ms'].notna().sum()
    print(f"Log RT calculated for {log_rt_count} correct trials")
    
    # 2. Calculate previous trial information and angular disparity change
    print("2. Calculating previous trial information and angular disparity...")
    
    # Sort by participant, block, and trial
    df_sorted = df.sort_values(['participantId', 'MRT_block', 'MRT_trial']).copy()
    
    for participant in df_sorted['participantId'].unique():
        participant_mask = df_sorted['participantId'] == participant
        participant_data = df_sorted[participant_mask].copy()
        
        for block in participant_data['MRT_block'].unique():
            block_mask = participant_data['MRT_block'] == block
            block_data = participant_data[block_mask].copy()
            
            if len(block_data) > 1:
                # Get indices for this participant and block
                block_indices = block_data.index
                
                # Calculate previous trial information (skip first trial of each block)
                for i in range(1, len(block_indices)):
                    current_idx = block_indices[i]
                    previous_idx = block_indices[i-1]
                    
                    # Previous angle
                    df_sorted.loc[current_idx, 'previous_angle_degrees'] = df_sorted.loc[previous_idx, 'MRT_angle_degrees']
                    
                    # Previous trial correct - keep as boolean
                    # Check for null values before assignment
                    if pd.notna(df_sorted.loc[previous_idx, 'MRT_isCorrect']):
                        df_sorted.loc[current_idx, 'previous_trial_correct'] = bool(df_sorted.loc[previous_idx, 'MRT_isCorrect'])
                    
                    # Absolute angular disparity change
                    if 'MRT_angle_degrees' in df_sorted.columns:
                        current_angle = df_sorted.loc[current_idx, 'MRT_angle_degrees']
                        previous_angle = df_sorted.loc[previous_idx, 'MRT_angle_degrees']
                        
                        if pd.notna(current_angle) and pd.notna(previous_angle):
                            df_sorted.loc[current_idx, 'abs_angular_disparity_change'] = abs(current_angle - previous_angle)
    
    # Update original dataframe with calculated values - handle each column separately to avoid dtype warnings
    df['log_rt_ms'] = df_sorted['log_rt_ms']
    df['previous_angle_degrees'] = df_sorted['previous_angle_degrees']
    df['abs_angular_disparity_change'] = df_sorted['abs_angular_disparity_change']
    
    # Ensure previous_trial_correct is stored as boolean
    if 'previous_trial_correct' in df_sorted.columns:
        # Convert to boolean explicitly to avoid dtype warnings
        df['previous_trial_correct'] = df_sorted['previous_trial_correct'].astype('boolean')
    
    # Print summary of calculated variables
    print(f"Previous angle calculated for {df['previous_angle_degrees'].notna().sum()} trials")
    print(f"Angular disparity change calculated for {df['abs_angular_disparity_change'].notna().sum()} trials")
    print(f"Previous trial correct calculated for {df['previous_trial_correct'].notna().sum()} trials")
    
    return df

def create_output_dataframe(df):
    """
    Create the final output dataframe with required columns.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Output dataframe with required columns only
    """
    print("\nCreating output dataframe...")
    
    # Add trial_type column
    df['trial_type'] = df['isPractice'].map({True: 'practice', False: 'test'})
    
    # Select required columns
    required_columns = [
        'participantId',
        'trial_type',
        'MRT_trial',
        'MRT_stimulusId',
        'MRT_angle_degrees',
        'MRT_isReflected',
        'MRT_response',
        'MRT_isCorrect',
        'MRT_rt_ms',
        'log_rt_ms',
        'MRT_block',
        'previous_angle_degrees',
        'abs_angular_disparity_change',
        'previous_trial_correct',
        'excluded_trial',
        'exclusion_reason_trial'
    ]
    
    # Check which columns exist
    available_columns = [col for col in required_columns if col in df.columns]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Warning: Missing columns in output: {missing_columns}")
    
    output_df = df[available_columns].copy()
    
    print(f"Output dataframe shape: {output_df.shape}")
    print(f"Output columns: {list(output_df.columns)}")
    print("First 2 rows of output:")
    print(output_df.head(2))
    
    return output_df

def save_exclusion_log(exclusion_log, timestamp):
    """
    Save the exclusion log to CSV.
    
    Parameters:
    exclusion_log (list): List of exclusion criteria and counts
    timestamp (str): Timestamp string for filename
    """
    print("\nSaving exclusion log...")
    
    if not exclusion_log:
        print("Warning: Exclusion log is empty")
        return
    
    exclusion_df = pd.DataFrame(exclusion_log, columns=[
        'exclusion_criteria',
        'count_excluded',
        'total_assessed',
        'exclusion_percentage'
    ])
    
    exclusion_filename = f"outputs/MRT_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(exclusion_filename, index=False)
    
    print(f"Exclusion log saved to: {exclusion_filename}")
    print("Exclusion summary:")
    print(exclusion_df)

def main():
    """
    Main function to execute the MRT data cleaning pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT data cleaning script...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Define required columns
        required_columns = [
            'participantId', 'table', 'isPractice', 'MRT_trial', 'MRT_stimulusId',
            'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response', 'MRT_isCorrect',
            'MRT_rt_ms', 'MRT_pracAttempt', 'MRT_timeout', 'MRT_block',
            'MRT_isAttentionCheck', 'windowFocusLostDuringTasksDuration',
            'frameRate', 'webGLsupport', 'wasFullscreenExited'
        ]
        
        # Load and combine data
        file_pattern = 'raw_data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv'
        df = load_and_combine_data(file_pattern)
        
        if df.empty:
            print("No data loaded. Exiting.")
            return 1
        
        # Filter MRT data
        mrt_df = filter_mrt_data(df)
        
        if mrt_df.empty:
            print("No MRT data found. Exiting.")
            return 1
        
        # Check required columns (only check for existence, not data types)
        available_columns = [col for col in required_columns if col in mrt_df.columns]
        print(f"Available required columns: {len(available_columns)}/{len(required_columns)}")
        
        # Initialize exclusion log
        exclusion_log = []
        
        # Check for incomplete data
        incomplete_participants = check_incomplete_data(mrt_df, required_columns)
        if incomplete_participants:
            print(f"Removing {len(incomplete_participants)} participants with incomplete data")
            mrt_df = mrt_df[~mrt_df['participantId'].isin(incomplete_participants)].copy()
            exclusion_log.append(['Incomplete data', len(incomplete_participants), 
                                 len(mrt_df['participantId'].unique()) + len(incomplete_participants), 
                                 len(incomplete_participants)/(len(mrt_df['participantId'].unique()) + len(incomplete_participants))*100])
        
        # Initialize exclusion tracking columns
        mrt_df['excluded_trial'] = False
        mrt_df['exclusion_reason_trial'] = ''
        
        # Apply participant-level exclusions (marks trials but keeps all participants)
        cleaned_df, exclusion_by_criterion = apply_participant_exclusions(mrt_df, exclusion_log)
        
        # Apply trial-level exclusions
        cleaned_df = apply_trial_exclusions(cleaned_df, exclusion_log)
        
        # Calculate required variables
        cleaned_df = calculate_variables(cleaned_df)
        
        # Create output dataframe
        output_df = create_output_dataframe(cleaned_df)
        
        # Save cleaned data
        try:
            output_filename = f"outputs/MRT_cleaned_data_{timestamp}.csv"
            output_df.to_csv(output_filename, index=False)
            print(f"\nCleaned data saved to: {output_filename}")
            print(f"Final data shape: {output_df.shape}")
        except Exception as e:
            print(f"Error saving cleaned data: {e}")
        
        # Save exclusion log
        try:
            save_exclusion_log(exclusion_log, timestamp)
        except Exception as e:
            print(f"Error saving exclusion log: {e}")
        
        # Print final summary
        print("\n===== FINAL SUMMARY =====")
        initial_participant_count = len(mrt_df['participantId'].unique())
        final_valid_participants = len(output_df[~output_df['excluded_trial']]['participantId'].unique())
        initial_trials = mrt_df.shape[0]
        final_valid_trials = output_df[~output_df['excluded_trial']].shape[0]
    
        print(f"Initial data: {initial_trials} trials from {initial_participant_count} participants")
        print(f"Attention check threshold: >=3 incorrect out of 6 (>50% failure rate)")
        print(f"Trial-level exclusion criteria:")
        print(f"  - RT < 200ms")
        print(f"  - RT > 7000ms or timeout")
        print(f"  - First trial of each block")
        print(f"  - Attention check trials")
        print(f"  - Fullscreen exit")
        print(f"  - Window focus lost > 5 seconds")
    
        # Summarize incomplete datasets
        incomplete_count = len(incomplete_participants) if 'incomplete_participants' in locals() else 0
        if incomplete_count > 0:
            print(f"Incomplete datasets removed: {incomplete_count} participants")
    
        # Summarize participant exclusions
        excluded_participant_count = initial_participant_count - final_valid_participants - incomplete_count
        if excluded_participant_count > 0:
            print(f"Participants excluded: {excluded_participant_count} ({excluded_participant_count/initial_participant_count*100:.1f}%)")
            # Access exclusion_by_criterion from the apply_participant_exclusions function
            if 'exclusion_by_criterion' in locals():
                print(f"  - Failed >50% attention checks: {len(exclusion_by_criterion.get('Failed >50% attention checks', set()))}")
                print(f"  - Timeout rate >30%: {len(exclusion_by_criterion.get('Timeout rate >30%', set()))}")
                print(f"  - Practice attempts >8: {len(exclusion_by_criterion.get('Practice attempts >8', set()))}")
                print(f"  - Mean RT >3 SD: {len(exclusion_by_criterion.get('Mean RT >3 SD', set()))}")
                print(f"  - Accuracy <3 SD below mean: {len(exclusion_by_criterion.get('Accuracy <3 SD below mean', set()))}")
                print(f"  - Poor browser compatibility: {len(exclusion_by_criterion.get('Poor browser compatibility', set()))}")
            else:
                print("  (Detailed exclusion breakdown not available)")
        
        # Summarize trial exclusions
        excluded_trial_count = output_df['excluded_trial'].sum()
        print(f"Trials excluded: {excluded_trial_count} ({excluded_trial_count/initial_trials*100:.1f}%)")
        print(f"  - Participant exclusions: {output_df[output_df['exclusion_reason_trial'] == 'Participant excluded'].shape[0]}")
        print(f"  - RT < 200ms: {output_df[output_df['exclusion_reason_trial'] == 'RT < 200ms'].shape[0]}")
        print(f"  - First trial of block: {output_df[output_df['exclusion_reason_trial'] == 'First trial of block'].shape[0]}")
        print(f"  - Attention check trials: {output_df[output_df['exclusion_reason_trial'] == 'Attention check trial'].shape[0]}")
    
        # Final dataset
        print(f"Final valid dataset: {final_valid_trials} trials from {final_valid_participants} participants ({final_valid_participants/initial_participant_count*100:.1f}% of participants)")
        
        # Add note about exclusion rate
        if excluded_participant_count/initial_participant_count > 0.3:
            print(f"NOTE: The participant exclusion rate ({excluded_participant_count/initial_participant_count*100:.1f}%) is higher than typical online experiments (~30%).")
            print(f"      Consider reviewing exclusion criteria if further data retention is needed.")
        print("========================")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
