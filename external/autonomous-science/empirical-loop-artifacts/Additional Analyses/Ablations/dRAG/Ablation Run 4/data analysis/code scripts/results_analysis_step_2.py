#!/usr/bin/env python3
"""
VWM Data Cleaning Script

This script processes Visual Working Memory (VWM) task data from CSV files,
applying comprehensive exclusion criteria and data quality checks.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys


def calculate_circular_error(response_angle, target_angle):
    """
    Calculate normalized circular error for orientation data.
    
    Parameters:
    -----------
    response_angle : float or array-like
        Response angle in degrees
    target_angle : float or array-like
        Target angle in degrees
    
    Returns:
    --------
    float or array-like
        Normalized circular error in degrees (±90°)
    """
    raw_error = response_angle - target_angle
    
    # Normalize to ±90° circular space
    normalized_error = np.where(raw_error > 90, raw_error - 180,
                               np.where(raw_error < -90, raw_error + 180, raw_error))
    
    return normalized_error


def calculate_circular_mean_error(errors):
    """
    Calculate absolute circular mean error.
    
    Parameters:
    -----------
    errors : array-like
        Array of circular errors in degrees
    
    Returns:
    --------
    float
        Absolute circular mean error in degrees
    """
    # Input validation: must be non-empty, numeric, and finite
    errors = np.asarray(errors)
    if len(errors) == 0 or not np.isfinite(errors).any():
        return 0.0

    # Convert to radians for circular statistics
    errors_rad = np.radians(errors)
    
    # Calculate circular mean
    sin_sum = np.sum(np.sin(errors_rad))
    cos_sum = np.sum(np.cos(errors_rad))
    
    circular_mean_rad = np.arctan2(sin_sum, cos_sum)
    circular_mean_deg = np.degrees(circular_mean_rad)
    
    return abs(circular_mean_deg)


def load_and_combine_data(file_pattern):
    """
    Load and combine all CSV files matching the pattern.
    
    Parameters:
    -----------
    file_pattern : str
        Glob pattern for input files
    
    Returns:
    --------
    pd.DataFrame
        Combined dataframe from all matching files
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} files.")
    
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {file_pattern}")
    
    combined_data = []
    show_details_for = 3  # Only show details for first N files

    for idx, file in enumerate(files):
        if idx < show_details_for:
            print(f"\nLoading file {idx+1}/{len(files)}: {file}")
        elif idx == show_details_for:
            print(f"... (suppressing detailed output for remaining {len(files) - show_details_for} files)")
        try:
            df = pd.read_csv(file)
            if idx < show_details_for:
                print(f"  File shape: {df.shape}")
                print(f"  Columns: {df.columns.tolist()}")
                print(f"  First 2 rows:\n{df.head(2)}")
            combined_data.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue

    if not combined_data:
        raise ValueError("No valid data files could be loaded")
    
    combined_df = pd.concat(combined_data, ignore_index=True)
    if combined_df.empty:
        raise ValueError("Combined DataFrame is empty")
    print(f"\nCombined data shape: {combined_df.shape}")
    print(f"Columns in combined data: {combined_df.columns.tolist()}")
    print(f"First 2 rows of combined data:\n{combined_df.head(2)}")
    print(f"Summary statistics for VWM_trial column (non-null count): {combined_df['VWM_trial'].notnull().sum()}")
    
    return combined_df


def identify_vwm_trials(df):
    """
    Identify which rows belong to VWM task.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Raw combined dataframe
    
    Returns:
    --------
    pd.DataFrame
        Dataframe containing only VWM trials
    """
    print("\nIdentifying VWM trials...")
    
    # VWM trials should have non-null VWM_trial values
    vwm_mask = pd.notna(df['VWM_trial'])
    vwm_df = df[vwm_mask].copy()
    
    print(f"Total rows in raw data: {len(df)}")
    print(f"VWM task rows identified: {len(vwm_df)}")
    
    # Print unique values for key experimental design parameters
    print("\nUnique values for key experimental design parameters:")
    
    if 'VWM_setSize' in vwm_df.columns:
        print(f"VWM_setSize unique values: {sorted(vwm_df['VWM_setSize'].dropna().unique())}")
    
    if 'VWM_delay_s' in vwm_df.columns:
        print(f"VWM_delay_s unique values: {sorted(vwm_df['VWM_delay_s'].dropna().unique())}")
    
    if 'VWM_block' in vwm_df.columns:
        print(f"VWM_block unique values: {sorted(vwm_df['VWM_block'].dropna().unique())}")
    
    if 'isPractice' in vwm_df.columns:
        print(f"isPractice unique values: {vwm_df['isPractice'].unique()}")
    
    if 'VWM_timeout' in vwm_df.columns:
        print(f"VWM_timeout unique values: {vwm_df['VWM_timeout'].unique()}")
    
    if 'VWM_isAttentionCheck' in vwm_df.columns:
        print(f"VWM_isAttentionCheck unique values: {vwm_df['VWM_isAttentionCheck'].unique()}")
    
    # Print data types for measured variables
    print("\nData types for measured variables:")
    if 'VWM_rt_ms' in vwm_df.columns:
        print(f"VWM_rt_ms data type: {vwm_df['VWM_rt_ms'].dtype}")
    
    if 'VWM_error_degrees' in vwm_df.columns:
        print(f"VWM_error_degrees data type: {vwm_df['VWM_error_degrees'].dtype}")
    
    return vwm_df


def remove_practice_trials(df):
    """
    Remove practice trials from the dataset.
    
    Parameters:
    -----------
    df : pd.DataFrame
        VWM dataframe
    
    Returns:
    --------
    pd.DataFrame
        Dataframe with practice trials removed
    """
    print("\nRemoving practice trials...")
    
    initial_count = len(df)
    
    # Remove practice trials
    non_practice_df = df[df['isPractice'] != True].copy()
    
    practice_removed = initial_count - len(non_practice_df)
    
    print(f"Practice trials removed: {practice_removed}")
    print(f"Remaining trials: {len(non_practice_df)}")
    
    return non_practice_df


def calculate_participant_exclusions(df, min_valid_trials=100):
    """
    Calculate which participants should be excluded based on various criteria.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Non-practice VWM dataframe
    min_valid_trials : int
        Minimum number of valid trials required to retain a participant
    
    Returns:
    --------
    dict
        Dictionary with exclusion information, including detailed mapping
    """
    print("\n=== Calculating participant-level exclusions ===")

    if len(df) == 0:
        return {'excluded_participants': set(), 'excluded_participants_map': {}, 'exclusion_log': []}
    
    exclusion_log = []
    excluded_participants = set()
    
    # Get unique participants
    participants = df['participantId'].unique()
    print(f"Total participants: {len(participants)}")
    
    # Data quality check: print trial counts per participant
    print("\nParticipant trial counts (first 10 shown):")
    trial_counts = df.groupby('participantId').size()
    print(trial_counts.head(10))
    print(f"Trial count stats: min={trial_counts.min()}, max={trial_counts.max()}, mean={trial_counts.mean():.1f}, median={trial_counts.median()}")
    
    # 1. Timeout rate calculation
    print("\n1. Checking timeout rates...")
    timeout_excluded = set()
    
    for participant in participants:
        participant_data = df[df['participantId'] == participant]
        total_trials = len(participant_data)
        timeout_trials = len(participant_data[participant_data['VWM_timeout'] == True])
        
        if total_trials > 0:
            timeout_rate = timeout_trials / total_trials
            if timeout_rate > 0.20:
                timeout_excluded.add(participant)
                print(f"  Participant {participant}: timeout rate {timeout_rate:.3f} > 0.20")
    
    excluded_participants.update(timeout_excluded)
    exclusion_log.append(('Timeout rate >20%', len(timeout_excluded), len(participants) - len(excluded_participants)))
    print(f"Participants excluded for high timeout rate: {len(timeout_excluded)}")
    
    # 2. Data completeness check
    print("\n2. Checking data completeness...")
    completeness_excluded = set()
    
    critical_columns = ['VWM_error_degrees', 'VWM_rt_ms', 'VWM_targetAngle_degrees']
    
    for participant in participants:
        if participant in excluded_participants:
            continue
            
        participant_data = df[df['participantId'] == participant]
        
        for col in critical_columns:
            if participant_data[col].isna().all():
                completeness_excluded.add(participant)
                print(f"  Participant {participant}: missing all data for {col}")
                break
    
    excluded_participants.update(completeness_excluded)
    exclusion_log.append(('Missing critical data', len(completeness_excluded), len(participants) - len(excluded_participants)))
    print(f"Participants excluded for missing critical data: {len(completeness_excluded)}")
    
    # Apply trial-level exclusions to calculate valid trial counts
    print("\n3. Applying trial-level exclusions and checking minimum trial count...")
    trial_count_excluded = set()
    valid_trial_counts = {}
    
    for participant in participants:
        if participant in excluded_participants:
            continue

        participant_data = df[df['participantId'] == participant]

        # Calculate valid trials based on actual trial-level exclusions
        valid_trials = participant_data[
            (participant_data['VWM_rt_ms'] >= 200) &
            (participant_data['VWM_timeout'] != True) &
            (pd.notna(participant_data['VWM_responseAngle_degrees']))
        ]
        valid_trial_counts[participant] = len(valid_trials)

        if len(valid_trials) < min_valid_trials:
            trial_count_excluded.add(participant)
            print(f"  Participant {participant}: only {len(valid_trials)} valid trials < {min_valid_trials}")
    
    # Show distribution of valid trial counts
    print("\nDistribution of valid trial counts (first 10 shown):")
    valid_trial_counts_series = pd.Series(valid_trial_counts)
    print(valid_trial_counts_series.head(10))
    print(f"Valid trial count stats: min={valid_trial_counts_series.min()}, max={valid_trial_counts_series.max()}, mean={valid_trial_counts_series.mean():.1f}, median={valid_trial_counts_series.median()}")
    print(f"Number of participants with <{min_valid_trials} valid trials: {(valid_trial_counts_series < min_valid_trials).sum()}")
    print(f"Number of participants with >= {min_valid_trials} valid trials: {(valid_trial_counts_series >= min_valid_trials).sum()}")
    print(f"Full distribution of valid trial counts (value counts):")
    print(valid_trial_counts_series.value_counts().sort_index())
    print(f"Histogram of valid trial counts (bins of 10):")
    print(valid_trial_counts_series.value_counts(bins=10, sort=False))
    
    excluded_participants.update(trial_count_excluded)
    exclusion_log.append((f'Insufficient valid trials (<{min_valid_trials})', len(trial_count_excluded), len(participants) - len(excluded_participants)))
    print(f"Participants excluded for insufficient valid trials: {len(trial_count_excluded)}")
    
    # 4. Response time coefficient of variation
    print("\n4. Checking response time coefficient of variation...")
    cv_excluded = set()
    
    for participant in participants:
        if participant in excluded_participants:
            continue

        participant_data = df[df['participantId'] == participant]

        # Use only valid trials for RT CV
        valid_trials = participant_data[
            (participant_data['VWM_rt_ms'] >= 200) &
            (participant_data['VWM_timeout'] != True) &
            (pd.notna(participant_data['VWM_responseAngle_degrees']))
        ]

        if len(valid_trials) > 0:
            rt_values = valid_trials['VWM_rt_ms'].dropna()
            if len(rt_values) > 1:
                cv = rt_values.std() / rt_values.mean()
                if cv > 3.0:
                    cv_excluded.add(participant)
                    print(f"  Participant {participant}: CV {cv:.3f} > 3.0")
    
    excluded_participants.update(cv_excluded)
    exclusion_log.append(('RT coefficient of variation >3.0', len(cv_excluded), len(participants) - len(excluded_participants)))
    print(f"Participants excluded for high RT CV: {len(cv_excluded)}")
    
    # 5. Systematic bias check
    print("\n5. Checking systematic bias...")
    bias_excluded = set()
    
    for participant in participants:
        if participant in excluded_participants:
            continue

        participant_data = df[df['participantId'] == participant]

        # Use only valid trials for systematic bias
        valid_trials = participant_data[
            (participant_data['VWM_rt_ms'] >= 200) &
            (participant_data['VWM_timeout'] != True) &
            (pd.notna(participant_data['VWM_responseAngle_degrees']))
        ]

        if len(valid_trials) > 0:
            errors = valid_trials['VWM_error_degrees'].dropna()
            if len(errors) > 0:
                abs_circular_mean_error = calculate_circular_mean_error(errors)
                if abs_circular_mean_error > 45:
                    bias_excluded.add(participant)
                    print(f"  Participant {participant}: systematic bias {abs_circular_mean_error:.1f}° > 45°")
    
    excluded_participants.update(bias_excluded)
    exclusion_log.append(('Systematic bias >45°', len(bias_excluded), len(participants) - len(excluded_participants)))
    print(f"Participants excluded for systematic bias: {len(bias_excluded)}")
    
    print(f"\nTotal participants excluded: {len(excluded_participants)}")
    print(f"Remaining participants: {len(participants) - len(excluded_participants)}")
    
    # Build exclusion details mapping for specific reasons
    exclusion_details = {
        'Timeout rate >20%': timeout_excluded,
        'Missing critical data': completeness_excluded,
        f'Insufficient valid trials (<{min_valid_trials})': trial_count_excluded,
        'RT coefficient of variation >3.0': cv_excluded,
        'Systematic bias >45°': bias_excluded
    }
    
    return {
        'excluded_participants': excluded_participants,
        'excluded_participants_map': exclusion_details,
        'exclusion_log': exclusion_log
    }


def apply_exclusions_and_clean(df, excluded_participants_map):
    """
    Apply all exclusions and clean the data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Non-practice VWM dataframe
    excluded_participants_map : dict
        Mapping of exclusion reasons to sets of participant IDs
    
    Returns:
    --------
    pd.DataFrame
        Cleaned dataframe with exclusion tracking
    """
    print("\n=== Applying exclusions and cleaning data ===")

    # Validate required columns exist
    required_columns = ['VWM_responseAngle_degrees', 'VWM_rt_ms', 'VWM_timeout', 'participantId']
    for col in required_columns:
        if col not in df.columns:
            raise ValueError(f"Required column {col} not found in DataFrame")
    
    # Create copy of dataframe
    cleaned_df = df.copy()
    
    # Debugging: check missing response angles before exclusions
    print(f"Trials with missing response angles before exclusions: {pd.isna(cleaned_df['VWM_responseAngle_degrees']).sum()}")
    print(f"Trials with RT < 200ms before exclusions: {(cleaned_df['VWM_rt_ms'] < 200).sum()}")
    print(f"Trials with timeout before exclusions: {(cleaned_df['VWM_timeout'] == True).sum()}")
    
    # Initialize exclusion tracking columns
    cleaned_df['excluded'] = False
    cleaned_df['exclusion_reason'] = ''  # Initialize with empty string, not NaN
    
    # Mark excluded participants with specific reasons
    for reason, p_ids in excluded_participants_map.items():
        mask = cleaned_df['participantId'].isin(p_ids)
        cleaned_df.loc[mask, 'excluded'] = True
        cleaned_df.loc[mask, 'exclusion_reason'] = reason

    # Apply trial-level exclusions to remaining participants in correct hierarchy order
    all_excluded_ids = {p for p_set in excluded_participants_map.values() for p in p_set}
    remaining_participants_mask = ~cleaned_df['participantId'].isin(all_excluded_ids)

    # 1. Timeout trials - highest priority
    timeout_exclusion_mask = (cleaned_df['VWM_timeout'] == True) & remaining_participants_mask & (~cleaned_df['excluded'])
    cleaned_df.loc[timeout_exclusion_mask, 'excluded'] = True
    cleaned_df.loc[timeout_exclusion_mask, 'exclusion_reason'] = 'Timeout trial'

    # 2. RT < 200ms - only update if not already excluded
    rt_exclusion_mask = (cleaned_df['VWM_rt_ms'] < 200) & remaining_participants_mask & (~cleaned_df['excluded'])
    cleaned_df.loc[rt_exclusion_mask, 'excluded'] = True
    cleaned_df.loc[rt_exclusion_mask, 'exclusion_reason'] = 'RT < 200ms'

    # 3. Missing response angle - only update if not already excluded
    missing_response_mask = pd.isna(cleaned_df['VWM_responseAngle_degrees']) & remaining_participants_mask & (~cleaned_df['excluded'])
    cleaned_df.loc[missing_response_mask, 'excluded'] = True
    cleaned_df.loc[missing_response_mask, 'exclusion_reason'] = 'Missing response angle'
    
    # Recalculate normalized errors for all trials
    print("\nRecalculating normalized orientation recall errors...")
    
    valid_response_mask = pd.notna(cleaned_df['VWM_responseAngle_degrees']) & pd.notna(cleaned_df['VWM_targetAngle_degrees'])
    
    cleaned_df['VWM_error_normalized_degrees'] = np.nan
    cleaned_df.loc[valid_response_mask, 'VWM_error_normalized_degrees'] = calculate_circular_error(
        cleaned_df.loc[valid_response_mask, 'VWM_responseAngle_degrees'],
        cleaned_df.loc[valid_response_mask, 'VWM_targetAngle_degrees']
    )
    
    # Print exclusion summary
    total_trials = len(cleaned_df)
    excluded_trials = cleaned_df['excluded'].sum()
    valid_trials = total_trials - excluded_trials

    print(f"\nExclusion summary:")
    print(f"Total trials: {total_trials}")
    print(f"Excluded trials: {excluded_trials}")
    print(f"Valid trials: {valid_trials}")

    # Print exclusion reasons breakdown
    exclusion_counts = cleaned_df[cleaned_df['excluded']]['exclusion_reason'].value_counts()
    print(f"\nExclusion reasons breakdown:")
    for reason, count in exclusion_counts.items():
        print(f"{reason}: {count}")

    # Print valid trial counts per participant (first 10 shown)
    valid_trials_per_p = cleaned_df[~cleaned_df['excluded']].groupby('participantId').size()
    print("\nValid trial counts per participant (first 10 shown):")
    print(valid_trials_per_p.head(10))
    print(f"Valid trial count stats: min={valid_trials_per_p.min() if not valid_trials_per_p.empty else 'NA'}, max={valid_trials_per_p.max() if not valid_trials_per_p.empty else 'NA'}, mean={valid_trials_per_p.mean() if not valid_trials_per_p.empty else 'NA'}")

    # Ensure valid trials have empty string exclusion reasons (not NaN)
    cleaned_df.loc[~cleaned_df['excluded'], 'exclusion_reason'] = ''

    return cleaned_df


def save_outputs(cleaned_df, exclusion_log):
    """
    Save cleaned data and exclusion log to output files.
    
    Parameters:
    -----------
    cleaned_df : pd.DataFrame
        Cleaned dataframe with exclusion tracking
    exclusion_log : list
        List of exclusion criteria and counts
    """
    print("\nSaving outputs...")
    
    # Create outputs directory if it doesn't exist
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define output columns for cleaned data
    output_columns = [
        'participantId',
        'VWM_trial',
        'VWM_setSize',
        'VWM_delay_s',
        'VWM_cueIndex',
        'VWM_orientations_degrees',
        'VWM_responseAngle_degrees',
        'VWM_targetAngle_degrees',
        'VWM_error_degrees',
        'VWM_error_normalized_degrees',
        'VWM_error_absolute_degrees',
        'VWM_rt_ms',
        'VWM_timeout',
        'VWM_block',
        'VWM_isAttentionCheck',
        'excluded',
        'exclusion_reason'
    ]
    
    # Save cleaned data (all trials, including excluded)
    cleaned_output_file = f'outputs/VWM_cleaned_{timestamp}.csv'
    cleaned_df[output_columns].to_csv(cleaned_output_file, index=False)
    print(f"Saved cleaned data to: {cleaned_output_file}")
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusion_log, columns=['exclusion_criterion', 'participants_excluded', 'remaining_participants'])
    exclusion_output_file = f'outputs/VWM_exclusion_log_{timestamp}.csv'
    exclusion_df.to_csv(exclusion_output_file, index=False)
    print(f"Saved exclusion log to: {exclusion_output_file}")
    
    # Print final summary
    print(f"\nFinal data summary:")
    print(f"Total trials in output: {len(cleaned_df)}")
    print(f"Valid trials: {(~cleaned_df['excluded']).sum()}")
    print(f"Excluded trials: {cleaned_df['excluded'].sum()}")
    print(f"Unique participants in output: {cleaned_df['participantId'].nunique()}")
    print(f"Valid participants: {cleaned_df[~cleaned_df['excluded']]['participantId'].nunique()}")


def main():
    """
    Main function to execute the VWM data cleaning pipeline.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("=== Starting VWM data cleaning pipeline ===")
        
        # Define input file pattern
        input_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        
        print("\n[Step 1] Loading and combining data...")
        raw_df = load_and_combine_data(input_pattern)
        
        print("\n[Step 2] Identifying VWM trials...")
        vwm_df = identify_vwm_trials(raw_df)
        
        print("\n[Step 3] Removing practice trials...")
        non_practice_df = remove_practice_trials(vwm_df)
        
        # Data quality check: print summary of key columns
        print("\nData quality check (first 5 rows):")
        print(non_practice_df[['participantId', 'VWM_trial', 'VWM_rt_ms', 'VWM_timeout', 'VWM_responseAngle_degrees', 'VWM_error_degrees']].head(5))
        print("Non-practice trial count:", len(non_practice_df))
        print("Unique participants (non-practice):", non_practice_df['participantId'].nunique())
        print("Trials with missing response angle:", pd.isna(non_practice_df['VWM_responseAngle_degrees']).sum())
        print("Trials with RT < 200ms:", (non_practice_df['VWM_rt_ms'] < 200).sum())
        print("Trials with timeout:", (non_practice_df['VWM_timeout'] == True).sum())
        
        print("\n[Step 4] Calculating participant exclusions (with configurable threshold)...")
        exclusion_results = calculate_participant_exclusions(non_practice_df, min_valid_trials=100)
        
        print("\n[Step 5] Applying exclusions and cleaning data...")
        cleaned_df = apply_exclusions_and_clean(non_practice_df, exclusion_results['excluded_participants_map'])
        
        print("\n[Step 6] Saving outputs...")
        save_outputs(cleaned_df, exclusion_results['exclusion_log'])
        
        # Final summary as per requirements
        print("\n--- Data Cleaning Summary ---")
        initial_participants = vwm_df['participantId'].nunique()
        print(f"1) VWM data found for {initial_participants} participants.")

        missing_data_p_count = len(exclusion_results['excluded_participants_map']['Missing critical data'])
        print(f"2) {missing_data_p_count} participants had incomplete data and were removed.")

        print("3) Data removal details:")
        for reason, p_ids in exclusion_results['excluded_participants_map'].items():
            if len(p_ids) > 0:
                # Dynamically replace threshold in reason string
                if 'Insufficient valid trials' in reason:
                    threshold = 100
                    display_reason = reason.replace('(<150)', f'(<{threshold})').replace('(<100)', f'(<{threshold})')
                else:
                    display_reason = reason
                print(f"   - {len(p_ids)} participants removed for: {display_reason}")

        trial_reasons = ['RT < 200ms', 'Timeout trial', 'Missing response angle']
        trial_exclusion_counts = cleaned_df['exclusion_reason'].value_counts()
        for reason in trial_reasons:
            count = trial_exclusion_counts.get(reason, 0)
            print(f"   - {count} trials removed for: {reason}")

        final_valid_participants = cleaned_df[~cleaned_df['excluded']]['participantId'].nunique()
        final_valid_trials = len(cleaned_df[~cleaned_df['excluded']])
        print(f"4) Final dataset: {final_valid_trials} trials from {final_valid_participants} participants.")

        print("=== Finished execution ===")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
