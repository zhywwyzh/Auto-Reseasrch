import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def create_timestamp():
    """
    Create a timestamp string for output filenames.
    
    Returns:
        str: Timestamp in format YYYYMMDD_HHMMSS
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def find_most_recent_file(pattern):
    """
    Find the most recent file matching a pattern with <TIMESTAMP> placeholder.
    
    Args:
        pattern (str): File pattern with <TIMESTAMP> placeholder
        
    Returns:
        str: Path to most recent file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    files = glob.glob(search_pattern)
    
    if not files:
        return None
    
    # Get the most recent file by modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def load_task_data_files():
    """
    Load all participant task data files matching the pattern.
    
    Returns:
        pd.DataFrame: Combined dataframe with all participant data
    """
    print("Loading task data files...")
    
    # Find all matching task data files
    task_files = glob.glob("../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv")
    print(f"Found {len(task_files)} task data files")
    
    if not task_files:
        print("ERROR: No task data files found!")
        return None
    
    all_data = []
    
    for file_path in task_files:
        print(f"Loading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()  # Add this line
            print(f"File shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            print()
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if not all_data:
        print("ERROR: No valid task data files loaded!")
        return None
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined data shape: {combined_df.shape}")
    print(f"Combined data columns: {list(combined_df.columns)}")
    print("First 2 rows of combined data:")
    print(combined_df.head(2))
    
    return combined_df

def load_included_participants():
    """
    Load the included participants file.
    
    Returns:
        pd.DataFrame: Dataframe with participant inclusion information
    """
    print("Loading included participants file...")
    
    # Find the most recent included participants file
    inclusion_file = find_most_recent_file("outputs/included_participants_<TIMESTAMP>.csv")
    
    if inclusion_file is None:
        print("ERROR: No included participants file found!")
        return None
    
    print(f"Loading inclusion file: {inclusion_file}")
    
    try:
        df = pd.read_csv(inclusion_file)
        print(f"Inclusion file shape: {df.shape}")
        print(f"Inclusion file columns: {list(df.columns)}")
        print("First 3 rows:")
        print(df.head(3))
        return df
    except Exception as e:
        print(f"Error loading inclusion file: {e}")
        return None

def filter_to_included_participants(task_df, inclusion_df):
    """
    Filter task data to only included participants.
    
    Args:
        task_df (pd.DataFrame): Task data
        inclusion_df (pd.DataFrame): Participant inclusion data
        
    Returns:
        pd.DataFrame: Filtered task data
    """
    print("Filtering to included participants...")
    
    # Get list of included participants
    included_participants = inclusion_df[inclusion_df['included_in_analysis'] == True]['participant_id'].tolist()
    print(f"Number of included participants: {len(included_participants)}")
    print(f"Included participants: {included_participants}")
    
    # Filter task data
    filtered_df = task_df[task_df['participantId'].isin(included_participants)].copy()
    print(f"Task data shape before filtering: {task_df.shape}")
    print(f"Task data shape after filtering: {filtered_df.shape}")
    
    # Check unique participants in filtered data
    unique_participants = filtered_df['participantId'].unique()
    print(f"Unique participants in filtered data: {len(unique_participants)}")
    print(f"Participants: {list(unique_participants)}")
    
    return filtered_df

def clean_vwm_trials(df):
    """
    Clean VWM trials according to specified criteria.
    
    Args:
        df (pd.DataFrame): Task data
        
    Returns:
        tuple: (cleaned_vwm_df, exclusion_summary_dict)
    """
    print("Cleaning VWM trials...")
    
    # First identify VWM trials - rows where table contains 'vwm'
    vwm_mask = df['table'].str.contains('vwm', case=False, na=False)
    vwm_data = df[vwm_mask].copy()
    
    print(f"Total VWM rows identified: {len(vwm_data)}")
    
    if len(vwm_data) == 0:
        print("No VWM data found!")
        return pd.DataFrame(), {}
    
    # Print unique values for key experimental design parameters
    print("VWM experimental design parameters:")
    print(f"Unique VWM_setSize values: {sorted(vwm_data['VWM_setSize'].dropna().unique())}")
    print(f"Unique VWM_delay_s values: {sorted(vwm_data['VWM_delay_s'].dropna().unique())}")
    print(f"VWM_rt_ms data type: {vwm_data['VWM_rt_ms'].dtype}")
    print(f"VWM_responseAngle_degrees data type: {vwm_data['VWM_responseAngle_degrees'].dtype}")
    
    # Initialize exclusion tracking
    exclusion_summary = {}
    participants = vwm_data['participantId'].unique()
    
    for participant in participants:
        exclusion_summary[participant] = {
            'vwm_original_trials': 0,
            'vwm_excluded_timeout': 0,
            'vwm_excluded_fast_rt': 0,
            'vwm_excluded_missing_data': 0,
            'vwm_retained_trials': 0
        }
    
    # Start with all VWM trials
    current_data = vwm_data.copy()
    
    print(f"Starting with {len(current_data)} VWM trials")
    
    # 1. Remove practice trials
    practice_mask = current_data['isPractice'] == True
    practice_trials = current_data[practice_mask]
    current_data = current_data[~practice_mask]
    print(f"Removed {len(practice_trials)} practice trials, {len(current_data)} remaining")
    
    # 2. Remove attention check trials
    attention_check_mask = current_data['VWM_isAttentionCheck'] == True
    attention_check_trials = current_data[attention_check_mask]
    current_data = current_data[~attention_check_mask]
    print(f"Removed {len(attention_check_trials)} attention check trials, {len(current_data)} remaining")
    
    # Count original trials per participant (after practice and attention check removal)
    for participant in participants:
        participant_trials = current_data[current_data['participantId'] == participant]
        exclusion_summary[participant]['vwm_original_trials'] = len(participant_trials)
    
    # 3. Remove timeout trials
    timeout_mask = current_data['VWM_timeout'] == True
    timeout_trials = current_data[timeout_mask]
    for participant in participants:
        participant_timeouts = timeout_trials[timeout_trials['participantId'] == participant]
        exclusion_summary[participant]['vwm_excluded_timeout'] = len(participant_timeouts)
    
    current_data = current_data[~timeout_mask]
    print(f"Removed {len(timeout_trials)} timeout trials, {len(current_data)} remaining")
    
    # 4. Remove trials with missing RT
    missing_rt_mask = current_data['VWM_rt_ms'].isna()
    missing_rt_trials = current_data[missing_rt_mask]
    for participant in participants:
        participant_missing = missing_rt_trials[missing_rt_trials['participantId'] == participant]
        exclusion_summary[participant]['vwm_excluded_missing_data'] += len(participant_missing)

    current_data = current_data[~missing_rt_mask]
    print(f"Removed {len(missing_rt_trials)} trials with missing RT, {len(current_data)} remaining")

    # 5. Remove trials with fast RT (< 200ms)
    fast_rt_mask = current_data['VWM_rt_ms'] < 200
    fast_rt_trials = current_data[fast_rt_mask]
    for participant in participants:
        participant_fast = fast_rt_trials[fast_rt_trials['participantId'] == participant]
        exclusion_summary[participant]['vwm_excluded_fast_rt'] = len(participant_fast)

    current_data = current_data[~fast_rt_mask]
    print(f"Removed {len(fast_rt_trials)} trials with fast RT, {len(current_data)} remaining")

    # 6. Remove trials with missing critical data
    critical_columns = ['VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees', 'VWM_error_absolute_degrees']
    missing_data_mask = current_data[critical_columns].isna().any(axis=1)
    missing_data_trials = current_data[missing_data_mask]
    for participant in participants:
        participant_missing_data = missing_data_trials[missing_data_trials['participantId'] == participant]
        exclusion_summary[participant]['vwm_excluded_missing_data'] += len(participant_missing_data)

    current_data = current_data[~missing_data_mask]
    print(f"Removed {len(missing_data_trials)} trials with missing critical data, {len(current_data)} remaining")
    
    # Count retained trials per participant
    for participant in participants:
        participant_retained = current_data[current_data['participantId'] == participant]
        exclusion_summary[participant]['vwm_retained_trials'] = len(participant_retained)
    
    print("VWM cleaning complete!")
    print(f"Final VWM data shape: {current_data.shape}")
    print("First 2 rows of cleaned VWM data:")
    print(current_data.head(2))
    
    return current_data, exclusion_summary

def clean_mrt_trials(df):
    """
    Clean MRT trials according to specified criteria.
    
    Args:
        df (pd.DataFrame): Task data
        
    Returns:
        tuple: (cleaned_mrt_df, exclusion_summary_dict)
    """
    print("Cleaning MRT trials...")
    
    # First identify MRT trials - rows where table contains 'mrt'
    mrt_mask = df['table'].str.contains('mrt', case=False, na=False)
    mrt_data = df[mrt_mask].copy()
    
    print(f"Total MRT rows identified: {len(mrt_data)}")
    
    if len(mrt_data) == 0:
        print("No MRT data found!")
        return pd.DataFrame(), {}
    
    # Print unique values for key experimental design parameters
    print("MRT experimental design parameters:")
    print(f"Unique MRT_angle_degrees values: {sorted(mrt_data['MRT_angle_degrees'].dropna().unique())}")
    print(f"Unique MRT_isReflected values: {sorted(mrt_data['MRT_isReflected'].dropna().unique())}")
    print(f"Unique MRT_response values: {sorted(mrt_data['MRT_response'].dropna().unique())}")
    print(f"MRT_rt_ms data type: {mrt_data['MRT_rt_ms'].dtype}")
    
    # Initialize exclusion tracking
    exclusion_summary = {}
    participants = mrt_data['participantId'].unique()
    
    for participant in participants:
        exclusion_summary[participant] = {
            'mrt_original_trials': 0,
            'mrt_excluded_timeout': 0,
            'mrt_excluded_fast_rt': 0,
            'mrt_excluded_slow_rt': 0,
            'mrt_excluded_missing_data': 0,
            'mrt_retained_trials': 0
        }
    
    # Start with all MRT trials
    current_data = mrt_data.copy()
    
    print(f"Starting with {len(current_data)} MRT trials")
    
    # 1. Remove practice trials
    practice_mask = current_data['isPractice'] == True
    practice_trials = current_data[practice_mask]
    current_data = current_data[~practice_mask]
    print(f"Removed {len(practice_trials)} practice trials, {len(current_data)} remaining")
    
    # 2. Remove attention check trials
    attention_check_mask = current_data['MRT_isAttentionCheck'] == True
    attention_check_trials = current_data[attention_check_mask]
    current_data = current_data[~attention_check_mask]
    print(f"Removed {len(attention_check_trials)} attention check trials, {len(current_data)} remaining")
    
    # Count original trials per participant (after practice and attention check removal)
    for participant in participants:
        participant_trials = current_data[current_data['participantId'] == participant]
        exclusion_summary[participant]['mrt_original_trials'] = len(participant_trials)
    
    # 3. Remove timeout trials
    timeout_mask = current_data['MRT_timeout'] == True
    timeout_trials = current_data[timeout_mask]
    for participant in participants:
        participant_timeouts = timeout_trials[timeout_trials['participantId'] == participant]
        exclusion_summary[participant]['mrt_excluded_timeout'] = len(participant_timeouts)
    
    current_data = current_data[~timeout_mask]
    print(f"Removed {len(timeout_trials)} timeout trials, {len(current_data)} remaining")
    
    # 4. Remove trials with fast RT (< 200ms)
    fast_rt_mask = current_data['MRT_rt_ms'] < 200
    fast_rt_trials = current_data[fast_rt_mask]
    for participant in participants:
        participant_fast = fast_rt_trials[fast_rt_trials['participantId'] == participant]
        exclusion_summary[participant]['mrt_excluded_fast_rt'] = len(participant_fast)
    
    current_data = current_data[~fast_rt_mask]
    print(f"Removed {len(fast_rt_trials)} fast RT trials, {len(current_data)} remaining")
    
    # 5. Remove trials with slow RT (> 7000ms)
    slow_rt_mask = current_data['MRT_rt_ms'] > 7000
    slow_rt_trials = current_data[slow_rt_mask]
    for participant in participants:
        participant_slow = slow_rt_trials[slow_rt_trials['participantId'] == participant]
        exclusion_summary[participant]['mrt_excluded_slow_rt'] = len(participant_slow)
    
    current_data = current_data[~slow_rt_mask]
    print(f"Removed {len(slow_rt_trials)} slow RT trials, {len(current_data)} remaining")
    
    # 6. Remove trials with missing RT
    missing_rt_mask = current_data['MRT_rt_ms'].isna()
    missing_rt_trials = current_data[missing_rt_mask]
    for participant in participants:
        participant_missing_rt = missing_rt_trials[missing_rt_trials['participantId'] == participant]
        exclusion_summary[participant]['mrt_excluded_missing_data'] += len(participant_missing_rt)
    
    current_data = current_data[~missing_rt_mask]
    print(f"Removed {len(missing_rt_trials)} trials with missing RT, {len(current_data)} remaining")
    
    # 7. Remove trials with missing critical data
    critical_columns = ['MRT_angle_degrees', 'MRT_isReflected', 'MRT_response', 'MRT_isCorrect']
    missing_data_mask = current_data[critical_columns].isna().any(axis=1)
    missing_data_trials = current_data[missing_data_mask]
    for participant in participants:
        participant_missing_data = missing_data_trials[missing_data_trials['participantId'] == participant]
        exclusion_summary[participant]['mrt_excluded_missing_data'] += len(participant_missing_data)
    
    current_data = current_data[~missing_data_mask]
    print(f"Removed {len(missing_data_trials)} trials with missing critical data, {len(current_data)} remaining")
    
    # Count retained trials per participant
    for participant in participants:
        participant_retained = current_data[current_data['participantId'] == participant]
        exclusion_summary[participant]['mrt_retained_trials'] = len(participant_retained)
    
    print("MRT cleaning complete!")
    print(f"Final MRT data shape: {current_data.shape}")
    print("First 2 rows of cleaned MRT data:")
    print(current_data.head(2))
    
    return current_data, exclusion_summary

def create_vwm_output(cleaned_vwm_df):
    """
    Create VWM output dataframe with required columns.
    
    Args:
        cleaned_vwm_df (pd.DataFrame): Cleaned VWM data
        
    Returns:
        pd.DataFrame: Output dataframe with required columns
    """
    print("Creating VWM output dataframe...")
    
    output_df = pd.DataFrame({
        'participant_id': cleaned_vwm_df['participantId'],
        'trial_number': cleaned_vwm_df['VWM_trial'],
        'set_size': cleaned_vwm_df['VWM_setSize'],
        'delay_seconds': cleaned_vwm_df['VWM_delay_s'],
        'response_angle_degrees': cleaned_vwm_df['VWM_responseAngle_degrees'],
        'target_angle_degrees': cleaned_vwm_df['VWM_targetAngle_degrees'],
        'error_degrees': cleaned_vwm_df['VWM_error_degrees'],
        'error_absolute_degrees': cleaned_vwm_df['VWM_error_absolute_degrees'],
        'response_time_ms': cleaned_vwm_df['VWM_rt_ms'],
        'trial_type': 'main_task'
    })
    
    print(f"VWM output dataframe shape: {output_df.shape}")
    print(f"VWM output columns: {list(output_df.columns)}")
    print("First 2 rows of VWM output:")
    print(output_df.head(2))
    
    return output_df

def create_mrt_output(cleaned_mrt_df):
    """
    Create MRT output dataframe with required columns.
    
    Args:
        cleaned_mrt_df (pd.DataFrame): Cleaned MRT data
        
    Returns:
        pd.DataFrame: Output dataframe with required columns
    """
    print("Creating MRT output dataframe...")
    
    output_df = pd.DataFrame({
        'participant_id': cleaned_mrt_df['participantId'],
        'trial_number': cleaned_mrt_df['MRT_trial'],
        'stimulus_id': cleaned_mrt_df['MRT_stimulusId'],
        'angle_degrees': cleaned_mrt_df['MRT_angle_degrees'],
        'is_reflected': cleaned_mrt_df['MRT_isReflected'],
        'response': cleaned_mrt_df['MRT_response'],
        'is_correct': cleaned_mrt_df['MRT_isCorrect'],
        'response_time_ms': cleaned_mrt_df['MRT_rt_ms'],
        'trial_type': 'main_task'
    })
    
    print(f"MRT output dataframe shape: {output_df.shape}")
    print(f"MRT output columns: {list(output_df.columns)}")
    print("First 2 rows of MRT output:")
    print(output_df.head(2))
    
    return output_df

def create_exclusion_summary(vwm_exclusions, mrt_exclusions):
    """
    Create exclusion summary dataframe.
    
    Args:
        vwm_exclusions (dict): VWM exclusion counts per participant
        mrt_exclusions (dict): MRT exclusion counts per participant
        
    Returns:
        pd.DataFrame: Exclusion summary dataframe
    """
    print("Creating exclusion summary...")
    
    # Get all participants
    all_participants = set(list(vwm_exclusions.keys()) + list(mrt_exclusions.keys()))
    
    summary_data = []
    
    for participant in all_participants:
        vwm_data = vwm_exclusions.get(participant, {})
        mrt_data = mrt_exclusions.get(participant, {})
        
        row = {
            'participant_id': participant,
            'vwm_original_trials': vwm_data.get('vwm_original_trials', 0),
            'vwm_excluded_timeout': vwm_data.get('vwm_excluded_timeout', 0),
            'vwm_excluded_fast_rt': vwm_data.get('vwm_excluded_fast_rt', 0),
            'vwm_excluded_missing_data': vwm_data.get('vwm_excluded_missing_data', 0),
            'vwm_retained_trials': vwm_data.get('vwm_retained_trials', 0),
            'mrt_original_trials': mrt_data.get('mrt_original_trials', 0),
            'mrt_excluded_timeout': mrt_data.get('mrt_excluded_timeout', 0),
            'mrt_excluded_fast_rt': mrt_data.get('mrt_excluded_fast_rt', 0),
            'mrt_excluded_slow_rt': mrt_data.get('mrt_excluded_slow_rt', 0),
            'mrt_excluded_missing_data': mrt_data.get('mrt_excluded_missing_data', 0),
            'mrt_retained_trials': mrt_data.get('mrt_retained_trials', 0)
        }
        
        summary_data.append(row)
    
    summary_df = pd.DataFrame(summary_data)
    
    print(f"Exclusion summary shape: {summary_df.shape}")
    print(f"Exclusion summary columns: {list(summary_df.columns)}")
    print("First 2 rows of exclusion summary:")
    print(summary_df.head(2))
    
    return summary_df

def main():
    """
    Main function to execute the trial-level data cleaning process.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting trial-level data cleaning process...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Create timestamp for output files
        timestamp = create_timestamp()
        print(f"Using timestamp: {timestamp}")
        
        # Load task data files
        task_df = load_task_data_files()
        if task_df is None:
            print("ERROR: Failed to load task data files")
            return 1
        
        # Load included participants
        inclusion_df = load_included_participants()
        if inclusion_df is None:
            print("ERROR: Failed to load included participants file")
            return 1
        
        # Filter to included participants
        filtered_df = filter_to_included_participants(task_df, inclusion_df)
        if len(filtered_df) == 0:
            print("ERROR: No data remaining after participant filtering")
            return 1
        
        # Clean VWM trials
        cleaned_vwm_df, vwm_exclusions = clean_vwm_trials(filtered_df)
        
        # Clean MRT trials
        cleaned_mrt_df, mrt_exclusions = clean_mrt_trials(filtered_df)
        
        # Create output dataframes
        if len(cleaned_vwm_df) > 0:
            vwm_output_df = create_vwm_output(cleaned_vwm_df)
            
            # Save VWM output
            vwm_output_file = f"outputs/vwm_cleaned_trials_{timestamp}.csv"
            vwm_output_df.to_csv(vwm_output_file, index=False)
            print(f"Saved VWM cleaned trials to: {vwm_output_file}")
        else:
            print("No VWM trials to output")
        
        if len(cleaned_mrt_df) > 0:
            mrt_output_df = create_mrt_output(cleaned_mrt_df)
            
            # Save MRT output
            mrt_output_file = f"outputs/mrt_cleaned_trials_{timestamp}.csv"
            mrt_output_df.to_csv(mrt_output_file, index=False)
            print(f"Saved MRT cleaned trials to: {mrt_output_file}")
        else:
            print("No MRT trials to output")
        
        # Create and save exclusion summary
        exclusion_summary_df = create_exclusion_summary(vwm_exclusions, mrt_exclusions)
        exclusion_output_file = f"outputs/trial_exclusion_summary_{timestamp}.csv"
        exclusion_summary_df.to_csv(exclusion_output_file, index=False)
        print(f"Saved exclusion summary to: {exclusion_output_file}")
        
        print("Trial-level data cleaning completed successfully!")
        # Print final summary statistics
        print("\n=== FINAL PROCESSING SUMMARY ===")
        print(f"Total participants with data: {len(exclusion_summary_df)}")
        print(f"Total VWM trials retained: {exclusion_summary_df['vwm_retained_trials'].sum()}")
        print(f"Total MRT trials retained: {exclusion_summary_df['mrt_retained_trials'].sum()}")
        print(f"VWM trials excluded - Timeout: {exclusion_summary_df['vwm_excluded_timeout'].sum()}")
        print(f"VWM trials excluded - Fast RT: {exclusion_summary_df['vwm_excluded_fast_rt'].sum()}")
        print(f"VWM trials excluded - Missing data: {exclusion_summary_df['vwm_excluded_missing_data'].sum()}")
        print(f"MRT trials excluded - Timeout: {exclusion_summary_df['mrt_excluded_timeout'].sum()}")
        print(f"MRT trials excluded - Fast RT: {exclusion_summary_df['mrt_excluded_fast_rt'].sum()}")
        print(f"MRT trials excluded - Slow RT: {exclusion_summary_df['mrt_excluded_slow_rt'].sum()}")
        print(f"MRT trials excluded - Missing data: {exclusion_summary_df['mrt_excluded_missing_data'].sum()}")
        print("=====================================\n")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
