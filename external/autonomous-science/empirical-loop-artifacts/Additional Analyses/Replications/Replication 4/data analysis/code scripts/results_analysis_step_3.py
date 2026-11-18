import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def load_participant_data():
    """
    Load the cleaned participant data file.
    
    Returns:
    pd.DataFrame: Participant data with inclusion flags
    """
    print("Loading participant data...")
    pattern = "outputs/cleaned_participant_data_*.csv"
    participant_file = find_latest_file(pattern)
    
    if participant_file is None:
        raise FileNotFoundError(f"No participant data file found matching pattern: {pattern}")
    
    print(f"Found participant data file: {participant_file}")
    
    df = pd.read_csv(participant_file)
    print(f"Participant data columns: {list(df.columns)}")
    print("First 3 rows of participant data:")
    print(df.head(3))
    
    # Verify required columns exist
    required_cols = ['participantId', 'included']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in participant data: {missing_cols}")
    
    print(f"Total participants: {len(df)}")
    print(f"Included participants: {df['included'].sum()}")
    print(f"Unique values in 'included' column: {df['included'].unique()}")
    
    return df

def load_experimental_data():
    """
    Load all experimental data files and combine them.
    
    Returns:
    pd.DataFrame: Combined experimental data from all participants
    """
    print("Loading experimental data files...")
    pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    data_files = glob.glob(pattern)
    
    if not data_files:
        raise FileNotFoundError(f"No experimental data files found matching pattern: {pattern}")
    
    print(f"Found {len(data_files)} experimental data files")
    
    all_data = []
    
    for file_path in data_files:
        print(f"Loading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No valid experimental data files could be loaded")
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    print(f"Combined experimental data columns: {list(combined_data.columns)}")
    print("First 3 rows of combined experimental data:")
    print(combined_data.head(3))
    
    # Verify required columns exist
    required_cols = [
        'participantId', 'isPractice', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
        'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees',
        'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_timeout', 'VWM_isAttentionCheck',
        'MRT_trial', 'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response',
        'MRT_isCorrect', 'MRT_rt_ms', 'MRT_timeout', 'MRT_isAttentionCheck'
    ]
    
    missing_cols = [col for col in required_cols if col not in combined_data.columns]
    if missing_cols:
        print(f"Warning: Missing columns in experimental data: {missing_cols}")
    
    print(f"Total experimental trials: {len(combined_data)}")
    print(f"Unique participants in experimental data: {combined_data['participantId'].nunique()}")
    
    # Print unique values for key experimental design parameters
    print(f"Unique VWM set sizes: {sorted(combined_data['VWM_setSize'].dropna().unique())}")
    print(f"Unique VWM delays: {sorted(combined_data['VWM_delay_s'].dropna().unique())}")
    print(f"Unique MRT angles: {sorted(combined_data['MRT_angle_degrees'].dropna().unique())}")
    print(f"Unique isPractice values: {combined_data['isPractice'].unique()}")
    print(f"Unique VWM_isAttentionCheck values: {combined_data['VWM_isAttentionCheck'].unique()}")
    print(f"Unique MRT_isAttentionCheck values: {combined_data['MRT_isAttentionCheck'].unique()}")
    print(f"Unique VWM_timeout values: {combined_data['VWM_timeout'].unique()}")
    print(f"Unique MRT_timeout values: {combined_data['MRT_timeout'].unique()}")
    print(f"Unique MRT_isReflected values: {combined_data['MRT_isReflected'].unique()}")
    print(f"Unique MRT_isCorrect values: {combined_data['MRT_isCorrect'].unique()}")
    
    # Debug: Check VWM condition distribution in raw data
    print("\nVWM condition distribution in raw data:")
    vwm_raw = combined_data[combined_data['VWM_trial'].notna()]
    if len(vwm_raw) > 0:
        vwm_raw_conditions = vwm_raw.groupby(['VWM_setSize', 'VWM_delay_s']).size()
        print(vwm_raw_conditions)
        
        # Specifically check for set size 1, delay 0.5
        setsize1_delay05_raw = vwm_raw[(vwm_raw['VWM_setSize'] == 1) & (vwm_raw['VWM_delay_s'] == 0.5)]
        print(f"Raw VWM trials with SetSize=1, Delay=0.5s: {len(setsize1_delay05_raw)}")
    
    return combined_data

def filter_included_participants(exp_data, participant_data):
    """
    Filter experimental data to only include participants marked as included.
    
    Parameters:
    exp_data (pd.DataFrame): Experimental data
    participant_data (pd.DataFrame): Participant data with inclusion flags
    
    Returns:
    pd.DataFrame: Filtered experimental data
    """
    print("Filtering to included participants only...")
    
    # Get list of included participants
    included_participants = participant_data[participant_data['included'] == True]['participantId'].tolist()
    print(f"Number of included participants: {len(included_participants)}")
    
    # Filter experimental data
    filtered_data = exp_data[exp_data['participantId'].isin(included_participants)].copy()
    
    print(f"Trials before participant filtering: {len(exp_data)}")
    print(f"Trials after participant filtering: {len(filtered_data)}")
    print(f"Participants in filtered data: {filtered_data['participantId'].nunique()}")
    
    return filtered_data

def apply_basic_filters(data):
    """
    Apply basic trial-level filters (practice trials, attention checks).
    """
    print("Applying basic trial-level filters...")
    
    exclusion_log = []
    initial_count = len(data)
    
    # Remove practice trials
    practice_mask = data['isPractice'] == True
    
    practice_excluded = practice_mask.sum()
    vwm_practice_excluded = data.loc[practice_mask, 'VWM_trial'].notna().sum()
    mrt_practice_excluded = data.loc[practice_mask, 'MRT_trial'].notna().sum()
    # Calculate BEFORE applying the mask
    practice_affected_participants = data.loc[practice_mask, 'participantId'].nunique() if practice_excluded > 0 else 0
    data = data[~practice_mask].copy()
    
    exclusion_log.append({
        'exclusion_criterion': 'Practice trials',
        'total_trials_excluded': practice_excluded,
        'vwm_trials_excluded': vwm_practice_excluded,
        'mrt_trials_excluded': mrt_practice_excluded,
        'participants_affected': practice_affected_participants  # Use the corrected calculation
    })
    
    print(f"Practice trials excluded: {practice_excluded}")
    print(f"Trials after practice filter: {len(data)}")
    
    # Remove attention check trials (no exceptions)
    attention_mask = (data['VWM_isAttentionCheck'] == True) | (data['MRT_isAttentionCheck'] == True)
    
    attention_excluded = attention_mask.sum()
    vwm_attention_excluded = data.loc[attention_mask, 'VWM_trial'].notna().sum()
    mrt_attention_excluded = data.loc[attention_mask, 'MRT_trial'].notna().sum()
    # Calculate BEFORE applying the mask
    attention_affected_participants = data.loc[attention_mask, 'participantId'].nunique() if attention_excluded > 0 else 0
    data = data[~attention_mask].copy()
    
    exclusion_log.append({
        'exclusion_criterion': 'Attention check trials',
        'total_trials_excluded': attention_excluded,
        'vwm_trials_excluded': vwm_attention_excluded,
        'mrt_trials_excluded': mrt_attention_excluded,
        'participants_affected': attention_affected_participants
    })
    
    print(f"Attention check trials excluded: {attention_excluded}")
    print(f"Trials after attention check filter: {len(data)}")
    
    return data, exclusion_log

def apply_anticipatory_response_filter(data, exclusion_log):
    """
    Flag trials with anticipatory responses (RT < 200ms for non-timeout trials).
    
    Parameters:
    data (pd.DataFrame): Experimental data
    exclusion_log (list): List to track exclusions
    """
    print("Applying anticipatory response filter...")
    
    # VWM anticipatory responses
    vwm_anticipatory_mask = (data['VWM_rt_ms'] < 200) & (data['VWM_timeout'] == False)
    vwm_anticipatory_excluded = vwm_anticipatory_mask.sum()
    vwm_affected_participants = data['participantId'][vwm_anticipatory_mask].nunique() if vwm_anticipatory_excluded > 0 else 0
    
    # MRT anticipatory responses
    mrt_anticipatory_mask = (data['MRT_rt_ms'] < 200) & (data['MRT_timeout'] == False)
    mrt_anticipatory_excluded = mrt_anticipatory_mask.sum()
    mrt_affected_participants = data['participantId'][mrt_anticipatory_mask].nunique() if mrt_anticipatory_excluded > 0 else 0
    
    # Combined mask
    anticipatory_mask = vwm_anticipatory_mask | mrt_anticipatory_mask
    total_anticipatory_excluded = anticipatory_mask.sum()
    total_affected_participants = data['participantId'][anticipatory_mask].nunique() if total_anticipatory_excluded > 0 else 0
    
    # Flag trials instead of removing them
    data.loc[anticipatory_mask, 'excluded_trial'] = True
    data.loc[anticipatory_mask, 'exclusion_reason'] += 'Anticipatory response; '
    
    exclusion_log.append({
        'exclusion_criterion': 'Anticipatory responses',
        'total_trials_excluded': total_anticipatory_excluded,
        'vwm_trials_excluded': vwm_anticipatory_excluded,
        'mrt_trials_excluded': mrt_anticipatory_excluded,
        'participants_affected': total_affected_participants
    })
    
    print(f"VWM anticipatory responses excluded: {vwm_anticipatory_excluded}")
    print(f"MRT anticipatory responses excluded: {mrt_anticipatory_excluded}")
    print(f"Total anticipatory responses excluded: {total_anticipatory_excluded}")
    print(f"Trials after anticipatory response filter: {len(data)}")
    

def apply_vwm_outlier_filter(data, exclusion_log):
    """
    Flag VWM outlier trials (RT > mean + 3*SD within participant and condition).
    
    Parameters:
    data (pd.DataFrame): Experimental data
    exclusion_log (list): List to track exclusions
    """
    print("Applying VWM outlier filter...")
    
    # Debug: Check condition counts before filtering
    print("VWM condition counts before outlier filtering:")
    condition_counts = data[data['VWM_trial'].notna()].groupby(['VWM_setSize', 'VWM_delay_s']).size()
    print(condition_counts)
    
    outlier_mask = pd.Series(False, index=data.index)
    
    for participant in data['participantId'].unique():
        participant_data = data[data['participantId'] == participant]
        
        # Group by Set Size × Delay condition
        for (set_size, delay), group in participant_data.groupby(['VWM_setSize', 'VWM_delay_s']):
            # Skip if either set_size or delay is NaN
            if pd.isna(set_size) or pd.isna(delay):
                continue
                
            # Only consider non-timeout trials for statistics
            non_timeout_trials = group[group['VWM_timeout'] == False]
            
            if len(non_timeout_trials) < 2:  # Need at least 2 trials to calculate SD
                print(f"Participant {participant}, SetSize {set_size}, Delay {delay}: Only {len(non_timeout_trials)} non-timeout trials, skipping outlier detection")
                continue
            
            mean_rt = non_timeout_trials['VWM_rt_ms'].mean()
            std_rt = non_timeout_trials['VWM_rt_ms'].std()
            
            if pd.isna(std_rt) or std_rt == 0:
                print(f"Participant {participant}, SetSize {set_size}, Delay {delay}: Invalid std_rt ({std_rt}), skipping")
                continue
            
            threshold = mean_rt + 3 * std_rt
            
            # Mark outliers in non-timeout trials
            condition_outliers = (group['VWM_rt_ms'] > threshold) & (group['VWM_timeout'] == False)
            outlier_mask.loc[group.index[condition_outliers]] = True
    
    vwm_outliers_excluded = outlier_mask.sum()
    affected_participants = data['participantId'][outlier_mask].nunique() if vwm_outliers_excluded > 0 else 0
    
    # Flag trials instead of removing them
    data.loc[outlier_mask, 'excluded_trial'] = True
    data.loc[outlier_mask, 'exclusion_reason'] += 'VWM outlier; '
    
    # Debug: Check condition counts after filtering
    print("VWM condition counts after outlier filtering (non-excluded trials):")
    valid_data = data[(data['VWM_trial'].notna()) & (data['excluded_trial'] == False)]
    condition_counts_after = valid_data.groupby(['VWM_setSize', 'VWM_delay_s']).size()
    print(condition_counts_after)
    
    exclusion_log.append({
        'exclusion_criterion': 'VWM outlier trials',
        'total_trials_excluded': vwm_outliers_excluded,
        'vwm_trials_excluded': vwm_outliers_excluded,
        'mrt_trials_excluded': 0,
        'participants_affected': affected_participants
    })
    
    print(f"VWM outlier trials excluded: {vwm_outliers_excluded}")
    print(f"Trials after VWM outlier filter: {len(data)}")
    

def apply_mrt_outlier_filter(data, exclusion_log):
    """
    Flag MRT outlier trials (RT > mean + 3*SD within participant and rotation angle, for correct trials).
    
    Parameters:
    data (pd.DataFrame): Experimental data
    exclusion_log (list): List to track exclusions
    """
    print("Applying MRT outlier filter...")
    
    outlier_mask = pd.Series(False, index=data.index)
    
    for participant in data['participantId'].unique():
        participant_data = data[data['participantId'] == participant]
        
        # Group by rotation angle
        for angle, group in participant_data.groupby('MRT_angle_degrees'):
            # Only consider correct, non-timeout trials for statistics
            correct_non_timeout = group[(group['MRT_isCorrect'] == True) & (group['MRT_timeout'] == False)]
            
            if len(correct_non_timeout) < 2:  # Need at least 2 trials to calculate SD
                continue
            
            mean_rt = correct_non_timeout['MRT_rt_ms'].mean()
            std_rt = correct_non_timeout['MRT_rt_ms'].std()
            
            if pd.isna(std_rt) or std_rt == 0:
                continue
            
            threshold = mean_rt + 3 * std_rt
            
            # Mark outliers in correct, non-timeout trials
            condition_outliers = (group['MRT_rt_ms'] > threshold) & (group['MRT_isCorrect'] == True) & (group['MRT_timeout'] == False)
            outlier_mask.loc[group.index[condition_outliers]] = True
    
    mrt_outliers_excluded = outlier_mask.sum()
    affected_participants = data['participantId'][outlier_mask].nunique() if mrt_outliers_excluded > 0 else 0

    # Flag trials instead of removing them
    data.loc[outlier_mask, 'excluded_trial'] = True
    data.loc[outlier_mask, 'exclusion_reason'] += 'MRT outlier; '
    
    exclusion_log.append({
        'exclusion_criterion': 'MRT outlier trials',
        'total_trials_excluded': mrt_outliers_excluded,
        'vwm_trials_excluded': 0,
        'mrt_trials_excluded': mrt_outliers_excluded,
        'participants_affected': affected_participants
    })
    
    print(f"MRT outlier trials excluded: {mrt_outliers_excluded}")
    print(f"Trials after MRT outlier filter: {len(data)}")
    

def apply_extreme_error_filter(data, exclusion_log):
    """
    Flag trials with extreme VWM errors (>90 degrees).
    
    Parameters:
    data (pd.DataFrame): Experimental data
    exclusion_log (list): List to track exclusions
    """
    print("Applying extreme VWM error filter...")
    
    extreme_error_mask = data['VWM_error_absolute_degrees'] > 90
    extreme_errors_excluded = extreme_error_mask.sum()
    affected_participants = data['participantId'][extreme_error_mask].nunique() if extreme_errors_excluded > 0 else 0

    # Flag trials instead of removing them
    data.loc[extreme_error_mask, 'excluded_trial'] = True
    data.loc[extreme_error_mask, 'exclusion_reason'] += 'Extreme VWM error; '
    
    exclusion_log.append({
        'exclusion_criterion': 'Extreme VWM errors',
        'total_trials_excluded': extreme_errors_excluded,
        'vwm_trials_excluded': extreme_errors_excluded,
        'mrt_trials_excluded': 0,
        'participants_affected': affected_participants
    })
    
    print(f"Extreme VWM error trials excluded: {extreme_errors_excluded}")
    print(f"Trials after extreme error filter: {len(data)}")
    

def apply_invalid_response_filter(data, exclusion_log):
    """
    Flag trials with invalid or missing response data.
    
    Parameters:
    data (pd.DataFrame): Experimental data
    exclusion_log (list): List to track exclusions
    """
    print("Applying invalid response filter...")
    
    # VWM invalid responses: missing response angle when not timeout
    vwm_invalid_mask = (pd.isna(data['VWM_responseAngle_degrees'])) & (data['VWM_timeout'] == False)
    vwm_invalid_excluded = vwm_invalid_mask.sum()
    
    # MRT invalid responses: missing response when not timeout
    mrt_invalid_mask = (pd.isna(data['MRT_response'])) & (data['MRT_timeout'] == False)
    mrt_invalid_excluded = mrt_invalid_mask.sum()
    
    # Combined mask
    invalid_mask = vwm_invalid_mask | mrt_invalid_mask
    total_invalid_excluded = invalid_mask.sum()
    affected_participants = data['participantId'][invalid_mask].nunique() if total_invalid_excluded > 0 else 0

    # Flag trials instead of removing them
    data.loc[invalid_mask, 'excluded_trial'] = True
    data.loc[invalid_mask, 'exclusion_reason'] += 'Invalid response; '
    
    exclusion_log.append({
        'exclusion_criterion': 'Invalid responses',
        'total_trials_excluded': total_invalid_excluded,
        'vwm_trials_excluded': vwm_invalid_excluded,
        'mrt_trials_excluded': mrt_invalid_excluded,
        'participants_affected': affected_participants
    })
    
    print(f"VWM invalid responses excluded: {vwm_invalid_excluded}")
    print(f"MRT invalid responses excluded: {mrt_invalid_excluded}")
    print(f"Total invalid responses excluded: {total_invalid_excluded}")
    print(f"Trials after invalid response filter: {len(data)}")
    

def apply_technical_failure_filter(data, exclusion_log):
    """
    Flag trials with technical failures (impossible combinations).
    
    Parameters:
    data (pd.DataFrame): Experimental data
    exclusion_log (list): List to track exclusions
    """
    print("Applying technical failure filter...")
    
    # Check for impossible combinations: response time exists but timeout=true
    vwm_impossible_mask = (~pd.isna(data['VWM_rt_ms'])) & (data['VWM_timeout'] == True)
    mrt_impossible_mask = (~pd.isna(data['MRT_rt_ms'])) & (data['MRT_timeout'] == True)
    
    vwm_impossible_excluded = vwm_impossible_mask.sum()
    mrt_impossible_excluded = mrt_impossible_mask.sum()
    
    # Combined mask
    impossible_mask = vwm_impossible_mask | mrt_impossible_mask
    total_impossible_excluded = impossible_mask.sum()
    affected_participants = data['participantId'][impossible_mask].nunique() if total_impossible_excluded > 0 else 0

    # Flag trials instead of removing them
    data.loc[impossible_mask, 'excluded_trial'] = True
    data.loc[impossible_mask, 'exclusion_reason'] += 'Technical failure; '
    
    exclusion_log.append({
        'exclusion_criterion': 'Technical failures',
        'total_trials_excluded': total_impossible_excluded,
        'vwm_trials_excluded': vwm_impossible_excluded,
        'mrt_trials_excluded': mrt_impossible_excluded,
        'participants_affected': affected_participants
    })
    
    print(f"VWM impossible combinations excluded: {vwm_impossible_excluded}")
    print(f"MRT impossible combinations excluded: {mrt_impossible_excluded}")
    print(f"Total technical failures excluded: {total_impossible_excluded}")
    print(f"Trials after technical failure filter: {len(data)}")
    

def validate_data_integrity(data):
    """
    Validate data integrity after exclusions and check trial counts per condition.
    """
    print("Validating data integrity on non-excluded trials...")
    valid_data = data[data['excluded_trial'] == False]
    
    print(f"Final valid dataset size: {len(valid_data)} trials")
    print(f"Final participant count: {valid_data['participantId'].nunique()}")
    
    # Debug: Check for missing VWM conditions
    print("\nChecking for VWM experimental conditions:")
    vwm_valid = valid_data[valid_data['VWM_trial'].notna()]
    vwm_conditions = vwm_valid.groupby(['VWM_setSize', 'VWM_delay_s']).size()
    print("VWM conditions in final dataset:")
    print(vwm_conditions)
    
    # Specifically check for set size 1, delay 0.5
    setsize1_delay05 = vwm_valid[(vwm_valid['VWM_setSize'] == 1) & (vwm_valid['VWM_delay_s'] == 0.5)]
    print(f"VWM trials with SetSize=1, Delay=0.5s: {len(setsize1_delay05)}")
    
    # Check trial counts per participant per condition
    print("\nTrial counts per participant per VWM condition:")
    vwm_counts = valid_data.groupby(['participantId', 'VWM_setSize', 'VWM_delay_s']).size()
    print(f"VWM condition trial counts - Min: {vwm_counts.min()}, Max: {vwm_counts.max()}, Mean: {vwm_counts.mean():.1f}")
    
    print("\nTrial counts per participant per MRT condition:")
    mrt_counts = valid_data.groupby(['participantId', 'MRT_angle_degrees']).size()
    print(f"MRT condition trial counts - Min: {mrt_counts.min()}, Max: {mrt_counts.max()}, Mean: {mrt_counts.mean():.1f}")
    
    # Check for participants with very low trial counts
    min_trials_per_condition = 5  # Threshold for adequate trial count
    
    low_vwm_participants = vwm_counts[vwm_counts < min_trials_per_condition]
    if len(low_vwm_participants) > 0:
        print(f"Warning: {len(low_vwm_participants)} VWM participant-condition combinations have < {min_trials_per_condition} trials")
    
    low_mrt_participants = mrt_counts[mrt_counts < min_trials_per_condition]
    if len(low_mrt_participants) > 0:
        print(f"Warning: {len(low_mrt_participants)} MRT participant-condition combinations have < {min_trials_per_condition} trials")
    
    # Check data ranges
    print(f"\nVWM error range: {valid_data['VWM_error_degrees'].min():.1f} to {valid_data['VWM_error_degrees'].max():.1f} degrees")
    print(f"VWM absolute error range: {valid_data['VWM_error_absolute_degrees'].min():.1f} to {valid_data['VWM_error_absolute_degrees'].max():.1f} degrees")
    print(f"VWM RT range: {valid_data['VWM_rt_ms'].min():.1f} to {valid_data['VWM_rt_ms'].max():.1f} ms")
    print(f"MRT RT range: {valid_data['MRT_rt_ms'].min():.1f} to {valid_data['MRT_rt_ms'].max():.1f} ms")

def create_output_datasets(data):
    """
    Create separate VWM and MRT output datasets.
    """
    print("Creating output datasets...")
    
    # Create VWM dataset - filter to VWM trials only
    vwm_df = data[data['VWM_trial'].notna()].copy()
    print(f"VWM trials found: {len(vwm_df)}")
    
    # Debug: Check VWM conditions before creating output dataset
    print("VWM conditions before output dataset creation:")
    vwm_conditions_pre = vwm_df.groupby(['VWM_setSize', 'VWM_delay_s']).size()
    print(vwm_conditions_pre)
    
    # Handle NaN values and type conversion safely
    vwm_data = pd.DataFrame({
        'participantId': vwm_df['participantId'].astype(str),
        'trial_number': pd.to_numeric(vwm_df['VWM_trial'], errors='coerce').fillna(0).astype(int),
        'setSize': pd.to_numeric(vwm_df['VWM_setSize'], errors='coerce').fillna(0).astype(int),
        'delay_s': pd.to_numeric(vwm_df['VWM_delay_s'], errors='coerce'),
        'responseAngle_degrees': pd.to_numeric(vwm_df['VWM_responseAngle_degrees'], errors='coerce'),
        'targetAngle_degrees': pd.to_numeric(vwm_df['VWM_targetAngle_degrees'], errors='coerce'),
        'error_degrees': pd.to_numeric(vwm_df['VWM_error_degrees'], errors='coerce'),
        'error_absolute_degrees': pd.to_numeric(vwm_df['VWM_error_absolute_degrees'], errors='coerce'),
        'rt_ms': pd.to_numeric(vwm_df['VWM_rt_ms'], errors='coerce'),
        'timeout': vwm_df['VWM_timeout'],
        'excluded_trial': vwm_df['excluded_trial'],
        'exclusion_reason': vwm_df['exclusion_reason'].fillna('').astype(str)
    })
    
    # Debug: Check VWM conditions after creating output dataset
    print("VWM conditions after output dataset creation:")
    vwm_conditions_post = vwm_data.groupby(['setSize', 'delay_s']).size()
    print(vwm_conditions_post)
    
    # Specifically check for set size 1, delay 0.5
    setsize1_delay05_output = vwm_data[(vwm_data['setSize'] == 1) & (vwm_data['delay_s'] == 0.5)]
    print(f"VWM trials with SetSize=1, Delay=0.5s in output dataset: {len(setsize1_delay05_output)}")
    
    # Create MRT dataset - filter to MRT trials only
    mrt_df = data[data['MRT_trial'].notna()].copy()
    print(f"MRT trials found: {len(mrt_df)}")
    
    # Handle NaN values and type conversion safely
    mrt_data = pd.DataFrame({
        'participantId': mrt_df['participantId'].astype(str),
        'trial_number': pd.to_numeric(mrt_df['MRT_trial'], errors='coerce').fillna(0).astype(int),
        'angle_degrees': pd.to_numeric(mrt_df['MRT_angle_degrees'], errors='coerce').fillna(0).astype(int),
        'isReflected': mrt_df['MRT_isReflected'],
        'response': mrt_df['MRT_response'].fillna('').astype(str),
        'isCorrect': mrt_df['MRT_isCorrect'],
        'rt_ms': pd.to_numeric(mrt_df['MRT_rt_ms'], errors='coerce'),
        'timeout': mrt_df['MRT_timeout'],
        'excluded_trial': mrt_df['excluded_trial'],
        'exclusion_reason': mrt_df['exclusion_reason'].fillna('').astype(str)
    })
    
    print(f"VWM dataset: {len(vwm_data)} trials")
    print("VWM data columns:", list(vwm_data.columns))
    print("First 2 rows of VWM data:")
    print(vwm_data.head(2))
    
    print(f"MRT dataset: {len(mrt_data)} trials")
    print("MRT data columns:", list(mrt_data.columns))
    print("First 2 rows of MRT data:")
    print(mrt_data.head(2))
    
    return vwm_data, mrt_data

def save_outputs(exclusion_log, vwm_data, mrt_data):
    """
    Save all output files with timestamp.
    
    Parameters:
    exclusion_log (list): List of exclusion criteria and counts
    vwm_data (pd.DataFrame): Cleaned VWM data
    mrt_data (pd.DataFrame): Cleaned MRT data
    """
    print("Saving output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusion_log)
    exclusion_file = f'outputs/trial_exclusion_log_{timestamp}.csv'
    exclusion_df.to_csv(exclusion_file, index=False)
    print(f"Saved exclusion log to: {exclusion_file}")
    print("Exclusion log contents:")
    print(exclusion_df)
    
    # Save VWM data
    vwm_file = f'outputs/cleaned_vwm_data_{timestamp}.csv'
    vwm_data.to_csv(vwm_file, index=False)
    print(f"Saved VWM data to: {vwm_file}")
    
    # Save MRT data
    mrt_file = f'outputs/cleaned_mrt_data_{timestamp}.csv'
    mrt_data.to_csv(mrt_file, index=False)
    print(f"Saved MRT data to: {mrt_file}")

def filter_missing_trial_numbers(data, exclusion_log):
    """
    Remove rows with missing trial numbers.
    """
    print("Filtering out rows with missing trial numbers...")
    
    # Identify rows with missing trial numbers
    missing_trial_mask = pd.isna(data['VWM_trial']) & pd.isna(data['MRT_trial'])
    missing_trials_excluded = missing_trial_mask.sum()
    affected_participants = data['participantId'][missing_trial_mask].nunique() if missing_trials_excluded > 0 else 0
    
    data = data[~missing_trial_mask].copy()
    
    exclusion_log.append({
        'exclusion_criterion': 'Missing trial numbers',
        'total_trials_excluded': missing_trials_excluded,
        'vwm_trials_excluded': 0,
        'mrt_trials_excluded': 0,
        'participants_affected': affected_participants
    })
    
    print(f"Rows with missing trial numbers excluded: {missing_trials_excluded}")
    print(f"Trials after missing trial number filter: {len(data)}")
    
    return data

def main():
    """
    Main function to execute the trial exclusion pipeline.
    """
    try:
        print("Starting trial exclusion pipeline...")
        
        # Load data
        participant_data = load_participant_data()
        experimental_data = load_experimental_data()
        
        # Filter to included participants
        data = filter_included_participants(experimental_data, participant_data)
        
        # Initialize exclusion log BEFORE filtering missing trial numbers
        exclusion_log = []
        
        # Filter out rows with missing trial numbers
        data = filter_missing_trial_numbers(data, exclusion_log)
        
        # Initialize columns for flagging excluded trials
        print("Initializing exclusion columns for flagging...")
        data['excluded_trial'] = False
        data['exclusion_reason'] = ''
        
        # Apply basic filters
        data, basic_exclusions = apply_basic_filters(data)
        exclusion_log.extend(basic_exclusions)
        
        # Apply trial-level exclusion criteria
        apply_anticipatory_response_filter(data, exclusion_log)
        apply_vwm_outlier_filter(data, exclusion_log)
        apply_mrt_outlier_filter(data, exclusion_log)
        apply_extreme_error_filter(data, exclusion_log)
        apply_invalid_response_filter(data, exclusion_log)
        apply_technical_failure_filter(data, exclusion_log)
        
        # Validate data integrity
        validate_data_integrity(data)
        
        # Create output datasets
        vwm_data, mrt_data = create_output_datasets(data)
        
        # Save outputs
        save_outputs(exclusion_log, vwm_data, mrt_data)
        
        print("Trial exclusion pipeline completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in trial exclusion pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
