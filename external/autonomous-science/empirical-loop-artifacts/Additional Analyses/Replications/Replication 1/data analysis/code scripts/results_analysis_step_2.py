import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def parse_duration_to_seconds(duration_str):
    """
    Parse duration string to total seconds.
    
    Parameters:
    duration_str: String in format HH:MM:SS or similar
    
    Returns:
    float: Total seconds
    """
    if pd.isna(duration_str) or duration_str == '':
        return 0.0
    
    try:
        # Handle different possible formats
        duration_str = str(duration_str).strip()
        
        # If it's already a number, return it
        try:
            return float(duration_str)
        except:
            pass
        
        # Parse HH:MM:SS format
        if ':' in duration_str:
            parts = duration_str.split(':')
            if len(parts) == 3:
                hours, minutes, seconds = parts
                return float(hours) * 3600 + float(minutes) * 60 + float(seconds)
            elif len(parts) == 2:
                minutes, seconds = parts
                return float(minutes) * 60 + float(seconds)
        
        # If no colons, assume it's seconds
        return float(duration_str)
    except:
        return 0.0

def normalize_circular_error(error_degrees):
    """
    Normalize circular error to -90 to +90 degree range.
    
    Parameters:
    error_degrees: float, error in degrees
    
    Returns:
    float: Normalized error in degrees
    """
    if pd.isna(error_degrees):
        return error_degrees
    
    # Wrap to -180 to 180 first
    error = error_degrees % 360
    if error > 180:
        error -= 360
    
    # Then constrain to -90 to +90
    if error > 90:
        error = 180 - error
    elif error < -90:
        error = -180 - error
    
    return error

def load_and_filter_vwm_data():
    """
    Load all participant CSV files and filter for VWM-related rows.
    
    Returns:
    pd.DataFrame: Combined VWM data from all participants
    """
    print("Loading VWM data files...")
    
    # Find all matching files
    file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    files = glob.glob(file_pattern)
    
    print(f"Found {len(files)} files matching pattern")
    
    if len(files) == 0:
        print("No files found matching pattern!")
        return pd.DataFrame()
    
    all_data = []
    
    for file in files:
        print(f"Processing file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print(f"First 3 rows:")
            print(df.head(3))

            # Forward-fill participant-level data to all rows before filtering
            participant_level_cols = ['participantId', 'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration']
            for col in participant_level_cols:
                if col in df.columns:
                    df[col] = df[col].fillna(method='ffill')
            
            # Filter for VWM rows only
            if 'table' in df.columns:
                vwm_mask = df['table'].str.contains('vwm', case=False, na=False)
                vwm_data = df[vwm_mask].copy()
                print(f"VWM rows found: {len(vwm_data)}")
                all_data.append(vwm_data)
            else:
                print("Warning: 'table' column not found in file")
                
        except Exception as e:
            print(f"Error processing file {file}: {e}")
            continue
    
    if not all_data:
        print("No VWM data found in any files")
        return pd.DataFrame()
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    print(f"Combined VWM data shape: {combined_data.shape}")
    print(f"Combined data columns: {list(combined_data.columns)}")
    print(f"First 2 rows of combined data:")
    print(combined_data.head(2))
    
    return combined_data

def create_trial_type_column(df):
    """
    Create trial_type column based on isPractice.
    
    Parameters:
    df: pd.DataFrame with isPractice column
    
    Returns:
    pd.DataFrame: DataFrame with trial_type column added
    """
    print("Creating trial_type column...")
    
    df = df.copy()
    df['trial_type'] = df['isPractice'].apply(lambda x: 'practice' if x else 'test')
    
    print(f"Trial type distribution:")
    print(df['trial_type'].value_counts())
    
    return df

def calculate_practice_performance(df):
    """
    Calculate practice performance metrics for exclusion criteria.
    
    Parameters:
    df: pd.DataFrame with practice trial data
    
    Returns:
    pd.DataFrame: Participant-level practice metrics
    """
    print("Calculating practice performance...")
    
    # Filter for practice trials only
    practice_data = df[df['isPractice'] == True].copy()
    print(f"Practice trials: {len(practice_data)}")
    
    if len(practice_data) == 0:
        return pd.DataFrame()
    
    practice_metrics = []
    
    for participant in practice_data['participantId'].unique():
        print(f"Processing practice data for participant: {participant}")
        
        participant_practice = practice_data[practice_data['participantId'] == participant]
        
        # Find maximum practice attempt
        max_attempt = participant_practice['VWM_pracAttempt'].max()
        print(f"  Max practice attempt: {max_attempt}")
        
        # Get final practice attempt data
        final_attempt = participant_practice[participant_practice['VWM_pracAttempt'] == max_attempt]
        
        # Get last 8 trials of final attempt
        final_attempt_sorted = final_attempt.sort_values('VWM_trial')
        last_8_trials = final_attempt_sorted.tail(8)
        
        print(f"  Final attempt trials: {len(final_attempt)}, Last 8: {len(last_8_trials)}")
        
        # Calculate mean absolute error for last 8 trials
        if len(last_8_trials) > 0:
            mean_error = last_8_trials['VWM_error_absolute_degrees'].mean()
        else:
            mean_error = np.nan
        
        practice_metrics.append({
            'participantId': participant,
            'max_practice_attempts': max_attempt,
            'final_8_trials_mean_error': mean_error,
            'failed_practice_criterion': max_attempt > 3
        })
    
    practice_df = pd.DataFrame(practice_metrics)
    print(f"Practice performance calculated for {len(practice_df)} participants")
    print(f"First 2 rows of practice metrics:")
    print(practice_df.head(2))
    
    return practice_df

def calculate_test_metrics(df):
    """
    Calculate test trial metrics for exclusion criteria.
    
    Parameters:
    df: pd.DataFrame with test trial data
    
    Returns:
    pd.DataFrame: Participant-level test metrics
    """
    print("Calculating test trial metrics...")
    
    # Filter for test trials only
    test_data = df[df['isPractice'] == False].copy()
    print(f"Test trials: {len(test_data)}")
    
    if len(test_data) == 0:
        return pd.DataFrame()
    
    test_metrics = []
    
    # Calculate sample statistics for z-scores
    focus_num_mean = test_data.groupby('participantId')['windowFocusLostDuringTasksNum'].first().mean()
    focus_num_std = test_data.groupby('participantId')['windowFocusLostDuringTasksNum'].first().std()
    focus_duration_mean = test_data.groupby('participantId')['windowFocusLostDuringTasksDuration_seconds'].first().mean()
    focus_duration_std = test_data.groupby('participantId')['windowFocusLostDuringTasksDuration_seconds'].first().std()
    
    print(f"Focus loss stats - Num: mean={focus_num_mean:.2f}, std={focus_num_std:.2f}")
    print(f"Focus loss stats - Duration: mean={focus_duration_mean:.2f}, std={focus_duration_std:.2f}")

    # Add detailed validation reporting as requested
    print(f"Focus loss data validation:")
    print(f"  Participants with valid focus_num: {test_data['windowFocusLostDuringTasksNum'].notna().sum()}")
    print(f"  Participants with valid focus_duration: {test_data['windowFocusLostDuringTasksDuration'].notna().sum()}")

    for participant in test_data['participantId'].unique():
        participant_test = test_data[test_data['participantId'] == participant]
        
        # Timeout rate
        total_trials = len(participant_test)
        timeout_trials = len(participant_test[participant_test['VWM_timeout'] == True])
        timeout_rate = timeout_trials / total_trials if total_trials > 0 else 0
        
        # Focus loss metrics (use first row values since they should be constant per participant)
        focus_num = participant_test['windowFocusLostDuringTasksNum'].iloc[0]
        focus_duration = participant_test['windowFocusLostDuringTasksDuration_seconds'].iloc[0]
        
        # Check if focus loss data exists before calculating z-scores
        if focus_num_std > 0 and not pd.isna(focus_num_mean):
            focus_num_z = (focus_num - focus_num_mean) / focus_num_std
        else:
            focus_num_z = 0  # Default when no valid data
        
        if focus_duration_std > 0 and not pd.isna(focus_duration_mean):
            focus_duration_z = (focus_duration - focus_duration_mean) / focus_duration_std
        else:
            focus_duration_z = 0  # Default when no valid data

        focus_severity_index = focus_num_z + focus_duration_z
        
        # Completion rate
        completed_trials = len(participant_test[~pd.isna(participant_test['VWM_trial'])])
        completion_rate = completed_trials / total_trials if total_trials > 0 else 0
        
        test_metrics.append({
            'participantId': participant,
            'timeout_rate': timeout_rate,
            'focus_loss_num': focus_num,
            'focus_loss_duration_seconds': focus_duration,
            'focus_loss_num_z': focus_num_z,
            'focus_loss_duration_z': focus_duration_z,
            'focus_severity_index': focus_severity_index,
            'completion_rate': completion_rate,
            'total_test_trials': total_trials
        })
    
    test_df = pd.DataFrame(test_metrics)
    print(f"Test metrics calculated for {len(test_df)} participants")
    print(f"First 2 rows of test metrics:")
    print(test_df.head(2))
    
    return test_df

def apply_participant_exclusions(df, practice_metrics, test_metrics):
    """
    Apply participant-level exclusion criteria.
    
    Parameters:
    df: pd.DataFrame with all data
    practice_metrics: pd.DataFrame with practice performance
    test_metrics: pd.DataFrame with test metrics
    
    Returns:
    tuple: (cleaned_df, exclusion_log)
    """
    print("Applying participant-level exclusions...")
    
    exclusion_log = []
    excluded_participants = set()
    
    # Calculate focus severity threshold (2.5 SD from mean)
    if len(test_metrics) > 0:
        severity_mean = test_metrics['focus_severity_index'].mean()
        severity_std = test_metrics['focus_severity_index'].std()
        severity_threshold = severity_mean + 2.5 * severity_std
        print(f"Focus severity threshold: {severity_threshold:.2f}")
    else:
        severity_threshold = float('inf')
    
    initial_participants = df['participantId'].nunique()
    print(f"Initial participants: {initial_participants}")
    
    # Practice block failure
    if len(practice_metrics) > 0:
        practice_failed = practice_metrics[practice_metrics['failed_practice_criterion']]['participantId'].tolist()
        excluded_participants.update(practice_failed)
        exclusion_log.append({
            'exclusion_criteria': 'practice_block_failure',
            'number_excluded': len(practice_failed),
            'description': 'Failed to achieve criterion performance after 3 practice attempts'
        })
        print(f"Practice block failures: {len(practice_failed)}")
    
    # Timeout rate > 15%
    if len(test_metrics) > 0:
        timeout_excluded = test_metrics[test_metrics['timeout_rate'] > 0.15]['participantId'].tolist()
        excluded_participants.update(timeout_excluded)
        exclusion_log.append({
            'exclusion_criteria': 'high_timeout_rate',
            'number_excluded': len(timeout_excluded),
            'description': 'More than 15% timeout trials during main task blocks'
        })
        print(f"High timeout rate: {len(timeout_excluded)}")
    
    # Only apply focus severity exclusions if we have valid data
    if not pd.isna(severity_threshold) and severity_threshold != float('inf') and len(test_metrics) > 0:
        focus_excluded = test_metrics[test_metrics['focus_severity_index'] > severity_threshold]['participantId'].tolist()
    else:
        focus_excluded = []
        print("Skipping focus loss severity exclusions due to invalid data")
    excluded_participants.update(focus_excluded)
    exclusion_log.append({
        'exclusion_criteria': 'focus_loss_severity',
        'number_excluded': len(focus_excluded),
        'description': 'Focus loss severity index exceeds 2.5 standard deviations from sample mean'
    })
    print(f"Focus loss severity: {len(focus_excluded)}")
    
    # Incomplete data < 80%
    if len(test_metrics) > 0:
        incomplete_excluded = test_metrics[test_metrics['completion_rate'] < 0.8]['participantId'].tolist()
        excluded_participants.update(incomplete_excluded)
        exclusion_log.append({
            'exclusion_criteria': 'incomplete_data',
            'number_excluded': len(incomplete_excluded),
            'description': 'Less than 80% of expected main task trials completed'
        })
        print(f"Incomplete data: {len(incomplete_excluded)}")
    
    # Flag excluded participants instead of removing their data
    df['excluded_participant'] = df['participantId'].isin(excluded_participants)

    total_excluded = len(excluded_participants)
    remaining_participants = initial_participants - total_excluded
    print(f"Total participants flagged for exclusion: {total_excluded}")
    print(f"Participants remaining for analysis: {remaining_participants}")

    return df, exclusion_log

def apply_trial_exclusions(df):
    """
    Apply trial-level exclusions to remaining participants.
    
    Parameters:
    df: pd.DataFrame with participant-level exclusions applied
    
    Returns:
    pd.DataFrame: DataFrame with trial-level exclusions applied
    """
    print("Applying trial-level exclusions to non-excluded participants...")

    initial_trials = len(df)
    print(f"Initial trials: {initial_trials}")

    # Create masks for excluded participants and valid trials
    excluded_participant_mask = (df['excluded_participant'] == True)
    valid_trial_mask = (df['VWM_timeout'] != True) & \
                       (df['VWM_rt_ms'] >= 200) & \
                       (df['VWM_rt_ms'] <= 7000) & \
                       (~pd.isna(df['VWM_targetAngle_degrees']))

    # Keep all trials from excluded participants OR valid trials from included participants
    df_cleaned = df[excluded_participant_mask | valid_trial_mask].copy()

    final_trials = len(df_cleaned)
    total_removed = initial_trials - final_trials
    print(f"Total trials removed from included participants: {total_removed}")

    return df_cleaned

def normalize_orientation_errors(df):
    """
    Normalize orientation errors and convert to radians.
    
    Parameters:
    df: pd.DataFrame with VWM_error_degrees column
    
    Returns:
    pd.DataFrame: DataFrame with normalized errors and radians
    """
    print("Normalizing orientation errors...")
    
    # Normalize errors to -90 to +90 degrees
    df['VWM_error_degrees_normalized'] = df['VWM_error_degrees'].apply(normalize_circular_error)
    
    # Convert to radians
    df['VWM_error_radians'] = df['VWM_error_degrees_normalized'] * np.pi / 180
    
    print(f"Error normalization complete")
    print(f"Original error range: {df['VWM_error_degrees'].min():.2f} to {df['VWM_error_degrees'].max():.2f}")
    print(f"Normalized error range: {df['VWM_error_degrees_normalized'].min():.2f} to {df['VWM_error_degrees_normalized'].max():.2f}")
    print(f"Radians range: {df['VWM_error_radians'].min():.4f} to {df['VWM_error_radians'].max():.4f}")
    
    return df

def print_data_validation(df):
    """
    Print validation information about key experimental parameters.
    
    Parameters:
    df: pd.DataFrame to validate
    """
    print("=== DATA VALIDATION ===")
    
    # Print unique values for key experimental parameters, safely handling NaN
    if 'VWM_setSize' in df.columns:
        unique_vals = [x for x in df['VWM_setSize'].unique() if pd.notna(x)]
        print(f"VWM_setSize unique values: {sorted(unique_vals)}")
    
    if 'VWM_delay_s' in df.columns:
        unique_vals = [x for x in df['VWM_delay_s'].unique() if pd.notna(x)]
        print(f"VWM_delay_s unique values: {sorted(unique_vals)}")
    
    if 'VWM_block' in df.columns:
        unique_vals = [x for x in df['VWM_block'].unique() if pd.notna(x)]
        print(f"VWM_block unique values: {sorted(unique_vals)}")
    
    if 'trial_type' in df.columns:
        unique_vals = [x for x in df['trial_type'].unique() if pd.notna(x)]
        print(f"trial_type unique values: {sorted(unique_vals)}")
    
    if 'VWM_isAttentionCheck' in df.columns:
        unique_vals = [x for x in df['VWM_isAttentionCheck'].unique() if pd.notna(x)]
        print(f"VWM_isAttentionCheck unique values: {sorted(unique_vals)}")
    
    # Print data types for measured variables (don't print unique values)
    if 'VWM_rt_ms' in df.columns:
        print(f"VWM_rt_ms data type: {df['VWM_rt_ms'].dtype}")
    
    if 'VWM_error_degrees' in df.columns:
        print(f"VWM_error_degrees data type: {df['VWM_error_degrees'].dtype}")
    
    if 'windowFocusLostDuringTasksNum' in df.columns:
        print(f"windowFocusLostDuringTasksNum data type: {df['windowFocusLostDuringTasksNum'].dtype}")
    
    print("=== END VALIDATION ===")

def main():
    """
    Main execution function for VWM data cleaning pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM data cleaning pipeline...")
        
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Load and filter VWM data
        df = load_and_filter_vwm_data()
        if len(df) == 0:
            print("No VWM data found. Exiting.")
            return 1
        
        # Print data validation
        print_data_validation(df)
        
        # Create trial type column
        df = create_trial_type_column(df)
        
        # Convert duration to seconds on main dataframe
        df['windowFocusLostDuringTasksDuration_seconds'] = df['windowFocusLostDuringTasksDuration'].apply(parse_duration_to_seconds)
        
        # Calculate practice performance
        practice_metrics = calculate_practice_performance(df)
        
        # Calculate test metrics
        test_metrics = calculate_test_metrics(df)
        
        # Apply participant-level exclusions
        df_cleaned, exclusion_log = apply_participant_exclusions(df, practice_metrics, test_metrics)
        
        # Apply trial-level exclusions
        df_cleaned = apply_trial_exclusions(df_cleaned)
        
        # Normalize orientation errors
        df_cleaned = normalize_orientation_errors(df_cleaned)
        
        # Prepare final output columns
        output_columns = [
            'participantId', 'trial_type', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
            'VWM_cueIndex', 'VWM_targetAngle_degrees', 'VWM_responseAngle_degrees',
            'VWM_error_degrees_normalized', 'VWM_error_radians', 'VWM_error_absolute_degrees',
            'VWM_rt_ms', 'VWM_block', 'VWM_isAttentionCheck', 'excluded_participant',
            'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration_seconds'
        ]
        
        # Filter to only include specified columns that exist
        available_columns = [col for col in output_columns if col in df_cleaned.columns]
        df_output = df_cleaned[available_columns].copy()
        
        print(f"Final cleaned data shape: {df_output.shape}")
        print(f"Final data columns: {list(df_output.columns)}")
        print(f"First 2 rows of final data:")
        print(df_output.head(2))
        
        # Save cleaned data
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cleaned_filename = f"outputs/VWM_cleaned_data_{timestamp}.csv"
        df_output.to_csv(cleaned_filename, index=False)
        print(f"Cleaned data saved to: {cleaned_filename}")
        
        # Save exclusion log
        exclusion_df = pd.DataFrame(exclusion_log)
        exclusion_filename = f"outputs/VWM_exclusion_log_{timestamp}.csv"
        exclusion_df.to_csv(exclusion_filename, index=False)
        print(f"Exclusion log saved to: {exclusion_filename}")
        
        print("Exclusion summary:")
        for entry in exclusion_log:
            print(f"  {entry['exclusion_criteria']}: {entry['number_excluded']} participants - {entry['description']}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
