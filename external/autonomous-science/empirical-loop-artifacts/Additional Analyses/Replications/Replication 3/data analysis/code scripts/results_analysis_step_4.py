import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

def get_most_recent_file(pattern):
    """
    Get the most recent file matching a pattern with <TIMESTAMP> placeholder.
    
    Parameters:
    pattern (str): File pattern with <TIMESTAMP> placeholder
    
    Returns:
    str: Path to most recent file matching pattern
    """
    # Replace <TIMESTAMP> with wildcard
    glob_pattern = pattern.replace('<TIMESTAMP>', '*')
    files = glob.glob(glob_pattern)
    
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {glob_pattern}")
    
    # Get most recent file by modification time
    most_recent = max(files, key=os.path.getmtime)
    print(f"Using most recent file: {most_recent}")
    return most_recent

def load_raw_data():
    """
    Load all raw participant data files and combine them.
    
    Returns:
    pd.DataFrame: Combined raw data from all participant files
    """
    print("Loading raw participant data files...")
    
    # Get all participant files
    raw_files = glob.glob("../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv")
    print(f"Found {len(raw_files)} raw data files")
    
    if not raw_files:
        raise FileNotFoundError("No participant data files found")
    
    all_data = []
    
    for file in raw_files:
        print(f"Loading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File columns: {list(df.columns)}")
            print(f"File shape: {df.shape}")
            print("First 3 rows:")
            print(df.head(3))
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No valid data files could be loaded")
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    print(f"Combined data shape: {combined_data.shape}")
    print(f"Combined data columns: {list(combined_data.columns)}")
    print("First 3 rows of combined data:")
    print(combined_data.head(3))
    
    return combined_data

def load_exclusion_data():
    """
    Load participant exclusion data.
    
    Returns:
    pd.DataFrame: Participant exclusion data
    """
    print("Loading participant exclusion data...")
    
    # Get most recent exclusion file
    exclusion_file = get_most_recent_file("outputs/participants_post_initial_exclusions_<TIMESTAMP>.csv")
    
    df = pd.read_csv(exclusion_file)
    print(f"Exclusion file columns: {list(df.columns)}")
    print(f"Exclusion file shape: {df.shape}")
    print("First 3 rows:")
    print(df.head(3))
    
    return df

def filter_mrt_data(raw_data):
    """
    Filter raw data to include only MRT (Mental Rotation Task) data.
    
    Parameters:
    raw_data (pd.DataFrame): Combined raw participant data
    
    Returns:
    pd.DataFrame: Filtered data containing only MRT trials
    """
    print("Filtering data for MRT task...")
    
    # Check required columns exist
    required_cols = ['participantId', 'isPractice', 'MRT_trial', 'MRT_timeout', 
                    'MRT_rt_ms', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_response']
    
    missing_cols = [col for col in required_cols if col not in raw_data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Filter for MRT data - use MRT_trial column as indicator (non-null values indicate MRT trials)
    mrt_data = raw_data[raw_data['MRT_trial'].notna()].copy()
    
    print(f"MRT data shape after filtering: {mrt_data.shape}")
    print("MRT data columns:")
    print(list(mrt_data.columns))
    print("First 2 rows of MRT data:")
    print(mrt_data.head(2))
    
    # Print unique values for key experimental design parameters
    print("\nUnique values for key experimental design parameters:")
    print(f"isPractice unique values: {sorted(mrt_data['isPractice'].dropna().unique())}")
    print(f"MRT_angle_degrees unique values: {sorted(mrt_data['MRT_angle_degrees'].dropna().unique())}")
    print(f"MRT_isCorrect unique values: {sorted(mrt_data['MRT_isCorrect'].dropna().unique())}")
    print(f"MRT_timeout unique values: {sorted(mrt_data['MRT_timeout'].dropna().unique())}")
    
    # Print data types for measured variables
    print(f"\nData types for measured variables:")
    print(f"MRT_rt_ms data type: {mrt_data['MRT_rt_ms'].dtype}")
    print(f"MRT_trial data type: {mrt_data['MRT_trial'].dtype}")
    
    return mrt_data[required_cols]

def apply_participant_filtering(mrt_data, exclusion_data):
    """
    Filter participants based on exclusion data.
    
    Parameters:
    mrt_data (pd.DataFrame): MRT trial data
    exclusion_data (pd.DataFrame): Participant exclusion data
    
    Returns:
    pd.DataFrame: Filtered MRT data with only non-excluded participants
    """
    print("Applying participant-level filtering...")
    
    # Get non-excluded participants
    valid_participants = exclusion_data[exclusion_data['excluded'] == False]['participantId'].tolist()
    print(f"Number of valid participants: {len(valid_participants)}")
    
    # Filter MRT data
    filtered_data = mrt_data[mrt_data['participantId'].isin(valid_participants)].copy()
    
    excluded_count = len(mrt_data['participantId'].unique()) - len(filtered_data['participantId'].unique())
    print(f"Excluded {excluded_count} participants from initial exclusions")
    print(f"Remaining participants: {len(filtered_data['participantId'].unique())}")
    print(f"Remaining trials: {len(filtered_data)}")
    
    return filtered_data

def apply_trial_exclusions(data):
    """
    Apply trial-level exclusions.
    
    Parameters:
    data (pd.DataFrame): MRT data
    
    Returns:
    tuple: (filtered_data, exclusion_log)
    """
    print("Applying trial-level exclusions...")
    
    exclusion_log = []
    original_count = len(data)
    
    # Remove practice trials
    practice_trials = data['isPractice'] == True
    practice_count = practice_trials.sum()
    data = data[~practice_trials].copy()
    exclusion_log.append({'exclusion_criteria': 'Practice trials', 'total_excluded': practice_count})
    print(f"Excluded {practice_count} practice trials")
    
    # Remove timeout trials
    timeout_trials = data['MRT_timeout'] == True
    timeout_count = timeout_trials.sum()
    data = data[~timeout_trials].copy()
    exclusion_log.append({'exclusion_criteria': 'Timeout trials', 'total_excluded': timeout_count})
    print(f"Excluded {timeout_count} timeout trials")
    
    # Remove trials with RT < 200ms
    fast_trials = data['MRT_rt_ms'] < 200
    fast_count = fast_trials.sum()
    data = data[~fast_trials].copy()
    exclusion_log.append({'exclusion_criteria': 'RT < 200ms', 'total_excluded': fast_count})
    print(f"Excluded {fast_count} trials with RT < 200ms")
    
    # Remove trials with RT > 15,000ms
    slow_trials = data['MRT_rt_ms'] > 15000
    slow_count = slow_trials.sum()
    data = data[~slow_trials].copy()
    exclusion_log.append({'exclusion_criteria': 'RT > 15,000ms', 'total_excluded': slow_count})
    print(f"Excluded {slow_count} trials with RT > 15,000ms")
    
    print(f"Remaining trials after basic exclusions: {len(data)} (from {original_count})")
    
    return data, exclusion_log

def apply_rt_outlier_exclusions(data, exclusion_log):
    """
    Apply RT outlier exclusions per participant per rotation angle.
    
    Parameters:
    data (pd.DataFrame): MRT data after basic exclusions
    exclusion_log (list): Existing exclusion log
    
    Returns:
    tuple: (filtered_data, updated_exclusion_log)
    """
    print("Applying RT outlier exclusions per participant per angle...")
    
    outlier_count = 0
    outlier_indices = []
    
    # Group by participant and angle
    for (participant, angle), group in data.groupby(['participantId', 'MRT_angle_degrees']):
        if len(group) < 3:  # Need at least 3 trials to calculate meaningful outliers
            continue
            
        mean_rt = group['MRT_rt_ms'].mean()
        std_rt = group['MRT_rt_ms'].std()
        
        if std_rt == 0:  # All RTs are identical
            continue
            
        # Find outliers (> mean + 3 SD, one-tailed)
        outliers = group[group['MRT_rt_ms'] > (mean_rt + 3 * std_rt)]
        outlier_indices.extend(outliers.index.tolist())
        outlier_count += len(outliers)
    
    # Remove outliers
    data_filtered = data.drop(outlier_indices).copy()
    exclusion_log.append({'exclusion_criteria': 'RT outliers (>3SD above mean per participant per angle)', 'total_excluded': outlier_count})
    print(f"Excluded {outlier_count} RT outlier trials")
    print(f"Remaining trials: {len(data_filtered)}")
    
    return data_filtered, exclusion_log

def apply_participant_level_exclusions(data, pre_exclusion_data, exclusion_log):
    """
    Apply participant-level exclusions based on accuracy and trial retention.

    Parameters:
    data (pd.DataFrame): MRT data after trial exclusions
    pre_exclusion_data (pd.DataFrame): MRT data before trial-level exclusions (for retention calculation)
    exclusion_log (list): Existing exclusion log

    Returns:
    tuple: (original_data, updated_exclusion_log, exclusion_mapping)
    """
    print("Applying participant-level exclusions...")

    # Calculate per-participant metrics after trial exclusions
    participant_stats = data.groupby('participantId').agg({
        'MRT_isCorrect': ['sum', 'count', 'mean'],
        'MRT_rt_ms': 'mean'
    }).round(4)
    participant_stats.columns = ['correct_count', 'total_trials', 'accuracy', 'mean_rt']
    participant_stats = participant_stats.reset_index()

    print("Participant statistics:")
    print(participant_stats.head(2))

    # Calculate original test trial counts per participant (before any exclusions, non-practice only)
    original_counts = pre_exclusion_data[pre_exclusion_data['isPractice'] == False].groupby('participantId').size().reset_index(name='original_trials')
    participant_stats = participant_stats.merge(original_counts, on='participantId', how='left')

    # Calculate retention rate
    participant_stats['retention_rate'] = participant_stats['total_trials'] / participant_stats['original_trials']

    print(f"Participant stats shape: {participant_stats.shape}")
    print("First 2 rows of participant stats:")
    print(participant_stats.head(2))

    # Exclusion 1: Overall accuracy < 25%
    low_accuracy = participant_stats['accuracy'] < 0.25
    low_accuracy_count = low_accuracy.sum()
    low_accuracy_participants = participant_stats[low_accuracy]['participantId'].tolist()

    # Exclusion 2: < 50% valid trials remaining (retention rate)
    low_retention = participant_stats['retention_rate'] < 0.5
    low_retention_count = low_retention.sum()
    low_retention_participants = participant_stats[low_retention]['participantId'].tolist()

    # Exclusion 3: Mean RT outliers (> mean + 3*SD, one-tailed)
    sample_mean_rt = participant_stats['mean_rt'].mean()
    sample_std_rt = participant_stats['mean_rt'].std()
    rt_outliers = participant_stats['mean_rt'] > (sample_mean_rt + 3 * sample_std_rt)
    rt_outlier_count = rt_outliers.sum()
    rt_outlier_participants = participant_stats[rt_outliers]['participantId'].tolist()

    # Build exclusion mapping instead of filtering data
    exclusion_map = {}
    for pid in low_accuracy_participants:
        exclusion_map.setdefault(pid, []).append("Low accuracy (<25%)")
    for pid in low_retention_participants:
        exclusion_map.setdefault(pid, []).append("Low trial retention (<50%)")
    for pid in rt_outlier_participants:
        exclusion_map.setdefault(pid, []).append("Mean RT outlier (>mean+3SD)")

    # Convert to final mapping with joined reasons
    final_exclusion_map = {pid: "; ".join(reasons) for pid, reasons in exclusion_map.items()}

    print(f"Excluding {low_accuracy_count} participants for low accuracy (<25%)")
    print(f"Excluding {low_retention_count} participants for low trial retention (<50%)")
    print(f"Excluding {rt_outlier_count} participants for RT outliers (>mean+3SD)")
    print(f"Total unique participants to exclude: {len(final_exclusion_map)}")

    # Update exclusion log
    exclusion_log.append({'exclusion_criteria': 'Low accuracy (<25%)', 'total_excluded': low_accuracy_count})
    exclusion_log.append({'exclusion_criteria': 'Low trial retention (<50%)', 'total_excluded': low_retention_count})
    exclusion_log.append({'exclusion_criteria': 'Mean RT outliers (>mean+3SD)', 'total_excluded': rt_outlier_count})

    print(f"Remaining participants: {len(data['participantId'].unique()) - len(final_exclusion_map)}")
    print(f"Remaining trials: {len(data[~data['participantId'].isin(final_exclusion_map.keys())])}")

    return data, exclusion_log, final_exclusion_map

def apply_log_transformation(data):
    """
    Apply log transformation to RT data for correct responses.
    
    Parameters:
    data (pd.DataFrame): Cleaned MRT data
    
    Returns:
    pd.DataFrame: Data with log-transformed RT values
    """
    print("Applying log transformation...")
    
    # Initialize ln_MRT_rt column
    data['ln_MRT_rt'] = np.nan
    
    # Apply log transformation only to correct responses
    correct_mask = data['MRT_isCorrect'] == True
    correct_count = correct_mask.sum()
    
    data.loc[correct_mask, 'ln_MRT_rt'] = np.log(data.loc[correct_mask, 'MRT_rt_ms'])
    
    print(f"Applied log transformation to {correct_count} correct responses")
    
    # Check for reasonable values
    ln_rt_values = data['ln_MRT_rt'].dropna()
    print(f"Log RT range: {ln_rt_values.min():.3f} to {ln_rt_values.max():.3f}")
    print(f"Log RT mean: {ln_rt_values.mean():.3f}")
    
    return data

def validate_data(data):
    """
    Validate the cleaned data.
    
    Parameters:
    data (pd.DataFrame): Cleaned MRT data
    """
    print("Validating cleaned data...")
    
    # Check rotation angles
    angles = sorted(data['MRT_angle_degrees'].unique())
    expected_angles = [0, 50, 100, 150]
    print(f"Rotation angles found: {angles}")
    print(f"Expected angles: {expected_angles}")
    
    if angles != expected_angles:
        print("WARNING: Unexpected rotation angles found!")
    
    # Check log-transformed values
    ln_rt_values = data['ln_MRT_rt'].dropna()
    if len(ln_rt_values) > 0:
        print(f"Log-transformed RT statistics:")
        print(f"  Count: {len(ln_rt_values)}")
        print(f"  Mean: {ln_rt_values.mean():.3f}")
        print(f"  Std: {ln_rt_values.std():.3f}")
        print(f"  Range: {ln_rt_values.min():.3f} to {ln_rt_values.max():.3f}")
    
    # Check trials per participant per angle
    trials_per_combo = data.groupby(['participantId', 'MRT_angle_degrees']).size()
    print(f"Trials per participant-angle combination:")
    print(f"  Mean: {trials_per_combo.mean():.1f}")
    print(f"  Min: {trials_per_combo.min()}")
    print(f"  Max: {trials_per_combo.max()}")
    
    if trials_per_combo.min() < 2:
        print("WARNING: Some participant-angle combinations have very few trials!")

def save_outputs(data, exclusion_log):
    """
    Save cleaned data and exclusion log to output files.
    
    Parameters:
    data (pd.DataFrame): Cleaned MRT data
    exclusion_log (list): List of exclusion criteria and counts
    """
    print("Saving output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare cleaned data for output
    output_data = data.copy()
    
    # Select required output columns
    output_columns = ['participantId', 'MRT_trial', 'MRT_rt_ms', 'MRT_angle_degrees', 
                     'MRT_isCorrect', 'MRT_response', 'ln_MRT_rt', 'excluded', 'exclusion_reason']
    
    output_data = output_data[output_columns]
    
    # Save cleaned data
    cleaned_file = f"outputs/MRT_cleaned_data_{timestamp}.csv"
    output_data.to_csv(cleaned_file, index=False)
    print(f"Saved cleaned data to: {cleaned_file}")
    print(f"Cleaned data shape: {output_data.shape}")
    print("Cleaned data columns:")
    print(list(output_data.columns))
    print("First 2 rows of cleaned data:")
    print(output_data.head(2))
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusion_log)
    exclusion_file = f"outputs/MRT_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(exclusion_file, index=False)
    print(f"Saved exclusion log to: {exclusion_file}")
    print("Exclusion log:")
    print(exclusion_df)

def main():
    """
    Main function to execute the MRT data cleaning pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT data cleaning pipeline...")
        
        # Load data
        raw_data = load_raw_data()
        exclusion_data = load_exclusion_data()
        
        # Filter for MRT data only
        mrt_data = filter_mrt_data(raw_data)
        
        # Apply participant filtering
        mrt_data = apply_participant_filtering(mrt_data, exclusion_data)

        # Save a copy of MRT data before trial-level exclusions for retention calculation
        mrt_data_pre_exclusions = mrt_data.copy()
        
        # Apply trial-level exclusions
        mrt_data, exclusion_log = apply_trial_exclusions(mrt_data)
        
        # Apply RT outlier exclusions
        mrt_data, exclusion_log = apply_rt_outlier_exclusions(mrt_data, exclusion_log)
        
        # Apply participant-level exclusions (pass pre-exclusion data for retention calculation)
        mrt_data, exclusion_log, participant_exclusion_map = apply_participant_level_exclusions(mrt_data, mrt_data_pre_exclusions, exclusion_log)

        # Populate excluded and exclusion_reason columns
        mrt_data['excluded'] = mrt_data['participantId'].isin(participant_exclusion_map.keys())
        mrt_data['exclusion_reason'] = mrt_data['participantId'].map(participant_exclusion_map).fillna('')

        # Apply log transformation
        mrt_data = apply_log_transformation(mrt_data)
        
        # Validate data
        validate_data(mrt_data)
        
        # Save outputs
        save_outputs(mrt_data, exclusion_log)

        # Final summary statistics
        print("\n" + "="*50)
        print("FINAL SUMMARY STATISTICS")
        print("="*50)
        print(f"Initial raw participant files: {len(glob.glob('../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv'))}")
        print(f"Initial total trials (all participants): {raw_data.shape[0]}")
        print(f"Initial MRT trials: {mrt_data_pre_exclusions.shape[0]}")
        print(f"Initial participants: {mrt_data_pre_exclusions['participantId'].nunique()}")
        print("\nExclusion log:")
        exclusion_df = pd.DataFrame(exclusion_log)
        print(exclusion_df)
        print(f"\nFinal number of non-excluded participants: {mrt_data[~mrt_data['excluded']]['participantId'].nunique()}")
        print(f"Final number of non-excluded trials: {(~mrt_data['excluded']).sum()}")
        print("="*50)
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
