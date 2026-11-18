#!/usr/bin/env python3
"""
MRT Data Cleaning Script
Processes Mental Rotation Task (MRT) data from multiple participant files,
applies exclusion criteria, and outputs cleaned data with exclusion log.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def load_and_combine_mrt_data(file_pattern):
    """
    Load and combine all participant MRT data files.
    
    Parameters:
    file_pattern (str): Glob pattern for input CSV files
    
    Returns:
    pd.DataFrame: Combined MRT data from all participants
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    # Find all matching files
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} files: {files}")
    
    if not files:
        print("ERROR: No files found matching the pattern")
        return None
    
    combined_data = []
    
    for file_path in files:
        print(f"\nProcessing file: {file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(file_path)
            print(f"File shape: {df.shape}")
            print(f"All columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            
            # Check for required columns
            required_columns = [
                'participantId', 'table', 'isPractice', 'MRT_trial', 
                'MRT_stimulusId', 'MRT_angle_degrees', 'MRT_isReflected',
                'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_pracAttempt',
                'MRT_timeout', 'MRT_block', 'MRT_isAttentionCheck'
            ]
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"WARNING: Missing columns in {file_path}: {missing_columns}")
                print("Skipping this file due to missing required columns")
                continue
            
            # Filter for MRT-related rows only
            mrt_mask = (df['table'].str.contains('mrt', case=False, na=False) | 
                       df['table'].str.contains('rotation', case=False, na=False))
            
            mrt_data = df[mrt_mask].copy()
            print(f"MRT rows found: {len(mrt_data)}")
            
            if len(mrt_data) > 0:
                combined_data.append(mrt_data)
                print(f"Added {len(mrt_data)} MRT rows from {file_path}")
            
        except Exception as e:
            print(f"ERROR reading {file_path}: {str(e)}")
            continue
    
    if not combined_data:
        print("ERROR: No valid MRT data found in any files")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(combined_data, ignore_index=True)
    print(f"\nCombined MRT data shape: {combined_df.shape}")
    print(f"Unique participants: {combined_df['participantId'].nunique()}")
    
    return combined_df

def create_trial_type_identifier(df):
    """
    Create trial_type column based on isPractice column.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with isPractice column
    
    Returns:
    pd.DataFrame: Dataframe with added trial_type column
    """
    print("\nCreating trial_type identifier...")
    
    df = df.copy()
    df['trial_type'] = df['isPractice'].apply(lambda x: 'practice' if x else 'test')
    
    print(f"Trial type distribution:")
    print(df['trial_type'].value_counts())
    
    return df

def calculate_practice_performance(df):
    """
    Calculate practice performance for exclusion criteria.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with practice trials
    
    Returns:
    dict: Dictionary with participant practice performance
    """
    print("\nCalculating practice performance...")
    
    practice_data = df[df['isPractice'] == True].copy()
    print(f"Total practice trials: {len(practice_data)}")
    
    practice_performance = {}
    
    for participant in practice_data['participantId'].unique():
        participant_practice = practice_data[practice_data['participantId'] == participant]
        
        # Find final practice attempt
        max_attempt = participant_practice['MRT_pracAttempt'].max()
        print(f"Participant {participant}: max practice attempt = {max_attempt}")
        
        final_attempt_data = participant_practice[
            participant_practice['MRT_pracAttempt'] == max_attempt
        ]
        
        # Get last 12 trials from final attempt
        final_attempt_sorted = final_attempt_data.sort_values('MRT_trial')
        last_12_trials = final_attempt_sorted.tail(12)
        
        print(f"Participant {participant}: final attempt has {len(final_attempt_data)} trials, using last {len(last_12_trials)} trials")
        
        # Count correct responses
        correct_count = last_12_trials['MRT_isCorrect'].sum()
        total_trials = len(last_12_trials)
        accuracy = correct_count / total_trials if total_trials > 0 else 0
        
        practice_performance[participant] = {
            'correct_count': correct_count,
            'total_trials': total_trials,
            'accuracy': accuracy,
            'max_attempts': max_attempt,
            'passes_practice': correct_count >= 8 and total_trials == 12
        }
        
        print(f"Participant {participant}: {correct_count}/{total_trials} correct ({accuracy:.3f}), passes: {practice_performance[participant]['passes_practice']}")
    
    return practice_performance

def calculate_test_trial_metrics(df):
    """
    Calculate test trial metrics for exclusion criteria.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with test trials
    
    Returns:
    dict: Dictionary with participant test performance metrics
    """
    print("\nCalculating test trial metrics...")
    
    test_data = df[df['isPractice'] == False].copy()
    print(f"Total test trials: {len(test_data)}")
    
    test_metrics = {}
    
    for participant in test_data['participantId'].unique():
        participant_test = test_data[test_data['participantId'] == participant]
        
        # Overall accuracy
        total_test_trials = len(participant_test)
        correct_trials = participant_test['MRT_isCorrect'].sum()
        overall_accuracy = correct_trials / total_test_trials if total_test_trials > 0 else 0
        
        # Timeout rate
        timeout_trials = participant_test['MRT_timeout'].sum()
        timeout_rate = timeout_trials / total_test_trials if total_test_trials > 0 else 0
        
        # Median reaction time for correct trials within valid range
        valid_rt_trials = participant_test[
            (participant_test['MRT_isCorrect'] == True) & 
            (participant_test['MRT_rt_ms'] >= 200) & 
            (participant_test['MRT_rt_ms'] <= 7000)
        ]
        
        if len(valid_rt_trials) > 0:
            median_rt = valid_rt_trials['MRT_rt_ms'].median()
            log_median_rt = np.log(median_rt)
        else:
            median_rt = np.nan
            log_median_rt = np.nan
        
        test_metrics[participant] = {
            'total_trials': total_test_trials,
            'correct_trials': correct_trials,
            'overall_accuracy': overall_accuracy,
            'timeout_trials': timeout_trials,
            'timeout_rate': timeout_rate,
            'median_rt': median_rt,
            'log_median_rt': log_median_rt,
            'valid_rt_trials': len(valid_rt_trials)
        }
        
        print(f"Participant {participant}: accuracy={overall_accuracy:.3f}, timeout_rate={timeout_rate:.3f}, median_rt={median_rt:.1f}, log_rt={log_median_rt:.3f}")
    
    return test_metrics

def apply_participant_exclusions(df, practice_performance, test_metrics):
    """
    Apply participant-level exclusion criteria.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    practice_performance (dict): Practice performance metrics
    test_metrics (dict): Test trial metrics
    
    Returns:
    tuple: (cleaned_df, exclusion_log)
    """
    print("\nApplying participant-level exclusions...")
    
    exclusion_log = []
    excluded_participants = set()
    
    # Get all participants
    all_participants = set(df['participantId'].unique())
    print(f"Total participants before exclusions: {len(all_participants)}")
    
    # 1. Practice block failure
    practice_failures = set()
    for participant, metrics in practice_performance.items():
        # Only exclude if participant had 3 or more attempts AND failed practice
        if metrics['max_attempts'] >= 3 and not metrics['passes_practice']:
            practice_failures.add(participant)

    newly_excluded_practice = practice_failures - excluded_participants
    excluded_participants.update(practice_failures)
    exclusion_log.append({
        'exclusion_criteria': 'Practice block failure',
        'number_excluded': len(newly_excluded_practice),
        'description': 'Participants with <8/12 correct responses after 3 practice attempts'
    })
    print(f"Practice failures: {len(newly_excluded_practice)} participants")
    
    # 2. Overall task accuracy <50%
    accuracy_failures = set()
    for participant, metrics in test_metrics.items():
        if metrics['overall_accuracy'] < 0.5:
            accuracy_failures.add(participant)

    newly_excluded_accuracy = accuracy_failures - excluded_participants
    excluded_participants.update(accuracy_failures)
    exclusion_log.append({
        'exclusion_criteria': 'Low task accuracy',
        'number_excluded': len(newly_excluded_accuracy),
        'description': 'Participants with main task accuracy <50%'
    })
    print(f"Low accuracy failures: {len(newly_excluded_accuracy)} participants")
    
    # 3. Timeout rate >15%
    timeout_failures = set()
    for participant, metrics in test_metrics.items():
        if metrics['timeout_rate'] > 0.15:
            timeout_failures.add(participant)

    newly_excluded_timeout = timeout_failures - excluded_participants
    excluded_participants.update(timeout_failures)
    exclusion_log.append({
        'exclusion_criteria': 'High timeout rate',
        'number_excluded': len(newly_excluded_timeout),
        'description': 'Participants with >15% timeout trials during main task'
    })
    print(f"High timeout failures: {len(newly_excluded_timeout)} participants")
    
    # 4. Extreme performance (>2.5 SD from mean)
    # Calculate means and SDs for accuracy and log RT
    valid_participants = [p for p in test_metrics.keys() if p not in excluded_participants]
    
    accuracies = [test_metrics[p]['overall_accuracy'] for p in valid_participants]
    log_rts = [test_metrics[p]['log_median_rt'] for p in valid_participants if not np.isnan(test_metrics[p]['log_median_rt'])]
    
    if len(accuracies) > 0:
        acc_mean = np.mean(accuracies)
        acc_std = np.std(accuracies)
        print(f"Accuracy: mean={acc_mean:.3f}, std={acc_std:.3f}")
    else:
        acc_mean = acc_std = 0
    
    if len(log_rts) > 0:
        rt_mean = np.mean(log_rts)
        rt_std = np.std(log_rts)
        print(f"Log RT: mean={rt_mean:.3f}, std={rt_std:.3f}")
    else:
        rt_mean = rt_std = 0
    
    extreme_performance = set()
    for participant in valid_participants:
        metrics = test_metrics[participant]

        # Check accuracy extreme
        if acc_std > 0:
            acc_z = abs(metrics['overall_accuracy'] - acc_mean) / acc_std
            if acc_z > 2.5:
                extreme_performance.add(participant)
                print(f"Participant {participant}: extreme accuracy z-score = {acc_z:.3f}")

        # Check RT extreme
        if not np.isnan(metrics['log_median_rt']) and rt_std > 0:
            rt_z = abs(metrics['log_median_rt'] - rt_mean) / rt_std
            if rt_z > 2.5:
                extreme_performance.add(participant)
                print(f"Participant {participant}: extreme RT z-score = {rt_z:.3f}")

    newly_excluded_extreme = extreme_performance - excluded_participants
    excluded_participants.update(extreme_performance)
    exclusion_log.append({
        'exclusion_criteria': 'Extreme performance',
        'number_excluded': len(newly_excluded_extreme),
        'description': 'Participants >2.5 SD from mean accuracy or log RT'
    })
    print(f"Extreme performance failures: {len(newly_excluded_extreme)} participants")
    
    # 5. Incomplete data (<80% of expected trials)
    # Estimate expected trials based on median trial count
    test_trial_counts = [test_metrics[p]['total_trials'] for p in test_metrics.keys()]
    expected_trials = np.median(test_trial_counts) if test_trial_counts else 0
    min_required_trials = int(0.8 * expected_trials)
    print(f"Expected trials: {expected_trials}, minimum required: {min_required_trials}")
    
    incomplete_data = set()
    for participant, metrics in test_metrics.items():
        if metrics['total_trials'] < min_required_trials:
            incomplete_data.add(participant)

    newly_excluded_incomplete = incomplete_data - excluded_participants
    excluded_participants.update(incomplete_data)
    exclusion_log.append({
        'exclusion_criteria': 'Incomplete data',
        'number_excluded': len(newly_excluded_incomplete),
        'description': 'Participants with <80% of expected main task trials'
    })
    print(f"Incomplete data failures: {len(newly_excluded_incomplete)} participants")
    
    # Create exclusion flag
    df_with_exclusions = df.copy()
    df_with_exclusions['excluded_participant'] = df_with_exclusions['participantId'].isin(excluded_participants)
    
    print(f"\nTotal participants excluded: {len(excluded_participants)}")
    print(f"Remaining participants: {len(all_participants) - len(excluded_participants)}")
    
    return df_with_exclusions, exclusion_log

def apply_trial_level_exclusions(df):
    """
    Apply trial-level exclusions to remaining participants.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with participant exclusions marked
    
    Returns:
    pd.DataFrame: Dataframe with trial-level exclusions applied
    """
    print("\nApplying trial-level exclusions...")
    
    # Work only with non-excluded participants
    included_data = df[df['excluded_participant'] == False].copy()
    excluded_data = df[df['excluded_participant'] == True].copy()
    
    print(f"Starting with {len(included_data)} trials from included participants")
    
    initial_count = len(included_data)
    
    # 1. Remove timeout trials
    timeout_mask = included_data['MRT_timeout'] == True
    timeout_count = timeout_mask.sum()
    included_data = included_data[~timeout_mask]
    print(f"Removed {timeout_count} timeout trials, remaining: {len(included_data)}")
    
    # 2. Remove RT < 200ms
    fast_rt_mask = included_data['MRT_rt_ms'] < 200
    fast_rt_count = fast_rt_mask.sum()
    included_data = included_data[~fast_rt_mask]
    print(f"Removed {fast_rt_count} trials with RT < 200ms, remaining: {len(included_data)}")
    
    # 3. Remove RT > 7000ms
    slow_rt_mask = included_data['MRT_rt_ms'] > 7000
    slow_rt_count = slow_rt_mask.sum()
    included_data = included_data[~slow_rt_mask]
    print(f"Removed {slow_rt_count} trials with RT > 7000ms, remaining: {len(included_data)}")
    
    # 4. Remove trials with missing stimulus ID
    missing_stimulus_mask = included_data['MRT_stimulusId'].isna()
    missing_stimulus_count = missing_stimulus_mask.sum()
    included_data = included_data[~missing_stimulus_mask]
    print(f"Removed {missing_stimulus_count} trials with missing stimulus ID, remaining: {len(included_data)}")

    # 5. Remove trials with invalid response values (not 'b' or 'n')
    invalid_response_mask = ~included_data['MRT_response'].isin(['b', 'n'])
    invalid_response_count = invalid_response_mask.sum()
    included_data = included_data[~invalid_response_mask]
    print(f"Removed {invalid_response_count} trials with invalid responses, remaining: {len(included_data)}")
    
    # Combine included and excluded data back together
    final_df = pd.concat([included_data, excluded_data], ignore_index=True)
    
    total_excluded_trials = initial_count - len(included_data)
    print(f"Total trial-level exclusions: {total_excluded_trials} trials")
    
    return final_df

def validate_data(df):
    """
    Validate data structure and values.
    
    Parameters:
    df (pd.DataFrame): Input dataframe to validate
    
    Returns:
    bool: True if validation passes
    """
    print("\nValidating data...")
    
    # Check angle degrees
    angle_values = df['MRT_angle_degrees'].dropna().unique()
    print(f"Unique MRT_angle_degrees values: {sorted(list(angle_values))}")
    expected_angles = [0, 50, 100, 150]
    invalid_angles = [a for a in angle_values if a not in expected_angles]
    if invalid_angles:
        print(f"WARNING: Invalid angle values found: {invalid_angles}")
    
    # Check response values
    response_values = df['MRT_response'].dropna().unique()
    print(f"Unique MRT_response values: {sorted(list(response_values))}")
    expected_responses = ['b', 'n']
    invalid_responses = [r for r in response_values if r not in expected_responses]
    if invalid_responses:
        print(f"WARNING: Invalid response values found: {invalid_responses}")
    
    # Check isCorrect values
    correct_values = df['MRT_isCorrect'].dropna().unique()
    print(f"Unique MRT_isCorrect values: {sorted(list(correct_values))}")
    
    # Check isReflected values
    reflected_values = df['MRT_isReflected'].dropna().unique()
    print(f"Unique MRT_isReflected values: {sorted(list(reflected_values))}")
    
    # Check trial type values
    if 'trial_type' in df.columns:
        trial_type_values = df['trial_type'].dropna().unique()
        print(f"Unique trial_type values: {sorted(list(trial_type_values))}")
    
    # Check timeout values
    timeout_values = df['MRT_timeout'].dropna().unique()
    print(f"Unique MRT_timeout values: {sorted(list(timeout_values))}")
    
    # Check block values
    block_values = df['MRT_block'].dropna().unique()
    print(f"Unique MRT_block values: {sorted(list(block_values))}")
    
    # Check attention check values
    attention_values = df['MRT_isAttentionCheck'].dropna().unique()
    print(f"Unique MRT_isAttentionCheck values: {sorted(list(attention_values))}")
    
    print("Data validation completed")
    return True

def save_outputs(df, exclusion_log):
    """
    Save cleaned data and exclusion log to output files.
    
    Parameters:
    df (pd.DataFrame): Cleaned dataframe
    exclusion_log (list): List of exclusion criteria and counts
    
    Returns:
    tuple: (data_filename, log_filename)
    """
    print("\nSaving outputs...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Prepare output columns for cleaned data
    output_columns = [
        'participantId', 'trial_type', 'MRT_trial', 'MRT_stimulusId',
        'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response', 
        'MRT_isCorrect', 'MRT_rt_ms', 'MRT_block', 'MRT_isAttentionCheck',
        'excluded_participant'
    ]
    
    # Select and reorder columns
    output_df = df[output_columns].copy()
    
    # Save cleaned data
    data_filename = f'outputs/MRT_cleaned_data_{timestamp}.csv'
    output_df.to_csv(data_filename, index=False)
    print(f"Saved cleaned data to: {data_filename}")
    print(f"Output data shape: {output_df.shape}")
    print("Output columns:", list(output_df.columns))
    print("First 2 rows of output:")
    print(output_df.head(2))
    
    # Save exclusion log
    log_df = pd.DataFrame(exclusion_log)
    log_filename = f'outputs/MRT_exclusion_log_{timestamp}.csv'
    log_df.to_csv(log_filename, index=False)
    print(f"Saved exclusion log to: {log_filename}")
    print("Exclusion log:")
    print(log_df)
    
    return data_filename, log_filename

def main():
    """
    Main function to execute the MRT data cleaning pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT Data Cleaning Script")
        print("=" * 50)
        
        # 1. Load and combine data
        file_pattern = '../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv'
        df = load_and_combine_mrt_data(file_pattern)
        
        if df is None or len(df) == 0:
            print("ERROR: No data loaded")
            return 1

        initial_participant_count = df['participantId'].nunique()
        
        print(f"\nLoaded data shape: {df.shape}")
        print("Loaded columns:", list(df.columns))
        print("First 2 rows:")
        print(df.head(2))
        
        # 2. Create trial type identifier
        df = create_trial_type_identifier(df)
        
        # 3. Calculate practice performance
        practice_performance = calculate_practice_performance(df)
        
        # 4. Calculate test trial metrics
        test_metrics = calculate_test_trial_metrics(df)
        
        # 5. Apply participant-level exclusions
        df, exclusion_log = apply_participant_exclusions(df, practice_performance, test_metrics)
        
        # 6. Apply trial-level exclusions
        df = apply_trial_level_exclusions(df)
        
        # 7. Validate data
        validate_data(df)
        
        # 8. Save outputs
        data_file, log_file = save_outputs(df, exclusion_log)

        # Final summary
        print("\n" + "=" * 50)
        print("FINAL DATA SUMMARY")
        print("=" * 50)
        # Initial participant and trial counts
        print(f"Initial number of participants: {initial_participant_count}")
        initial_trials = df.shape[0]
        print(f"Initial number of trials: {initial_trials}")

        # Exclusion summary by criteria
        print("\nExclusion summary by criteria:")
        for log in exclusion_log:
            print(f"- {log['exclusion_criteria']}: {log['number_excluded']} excluded ({log['description']})")

        # Final counts
        n_excluded = df[df['excluded_participant'] == True]['participantId'].nunique()
        n_included = df[df['excluded_participant'] == False]['participantId'].nunique()
        n_trials_included = df[df['excluded_participant'] == False].shape[0]
        print(f"\nTotal participants excluded: {n_excluded}")
        print(f"Total participants included: {n_included}")
        print(f"Final number of trials (included participants): {n_trials_included}")
        print(f"Final data shape (all rows): {df.shape}")

        print("\n" + "=" * 50)
        print("MRT Data Cleaning Completed Successfully")
        print(f"Final data shape: {df.shape}")
        print(f"Data saved to: {data_file}")
        print(f"Log saved to: {log_file}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
