import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import re

def parse_focus_loss_duration(duration_str):
    """
    Parse windowFocusLostDuringTasksDuration to seconds.
    
    Parameters:
    duration_str (str): Duration string in various formats
    
    Returns:
    float: Duration in seconds, or NaN if cannot parse
    """
    if pd.isna(duration_str):
        return np.nan
    
    duration_str = str(duration_str).strip()
    
    # Check if it's already numeric (seconds)
    try:
        return float(duration_str)
    except ValueError:
        pass
    
    # Check if it's HH:MM:SS format
    time_pattern = r'^(\d{1,2}):(\d{2}):(\d{2})$'
    match = re.match(time_pattern, duration_str)
    if match:
        hours, minutes, seconds = map(int, match.groups())
        return hours * 3600 + minutes * 60 + seconds
    
    # If cannot parse, return NaN
    return np.nan

def parse_timestamp(timestamp_str):
    """
    Parse timestamp string to datetime object using pandas.
    """
    if pd.isna(timestamp_str):
        return pd.NaT
    # Use pandas to_datetime which is more robust and handles various formats
    return pd.to_datetime(timestamp_str, errors='coerce')

def load_and_combine_data():
    """
    Load and combine all participant data files.
    
    Returns:
    pd.DataFrame: Combined dataframe with all participants
    """
    print("Loading participant data files...")
    
    # Find all matching files
    file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    files = glob.glob(file_pattern)
    
    print(f"Found {len(files)} participant files")
    
    if len(files) == 0:
        print("ERROR: No participant files found!")
        return None
    
    all_data = []
    
    for file in files:
        print(f"Loading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            print()
            
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not all_data:
        print("ERROR: No data files could be loaded!")
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined data shape: {combined_df.shape}")
    print(f"Combined columns: {list(combined_df.columns)}")
    print("First 2 rows of combined data:")
    print(combined_df.head(2))
    print()
    
    return combined_df

def validate_required_columns(df):
    """
    Validate that all required columns are present in the dataframe.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    bool: True if all required columns present, False otherwise
    """
    required_columns = [
        'participantId', 'table', 'isPractice', 'wasFullscreenExited',
        'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration',
        'VWM_trial', 'VWM_setSize', 'VWM_delay_s', 'VWM_responseAngle_degrees',
        'VWM_targetAngle_degrees', 'VWM_error_degrees', 'VWM_error_absolute_degrees',
        'VWM_rt_ms', 'VWM_timeout', 'VWM_pracAttempt', 'VWM_block',
        'MRT_trial', 'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response',
        'MRT_isCorrect', 'MRT_rt_ms', 'MRT_timeout', 'MRT_pracAttempt', 'MRT_block',
        'taskOrder', 'timestamp', 'windowWidthPixels', 'windowHeightPixels'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        return False
    
    print("All required columns present")
    return True

def print_unique_values(df):
    """
    Print unique values for key experimental design parameter columns.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    """
    print("=== UNIQUE VALUES FOR KEY EXPERIMENTAL DESIGN PARAMETERS ===")
    
    # VWM parameters
    print(f"VWM_setSize unique values: {sorted(df['VWM_setSize'].dropna().unique())}")
    print(f"VWM_delay_s unique values: {sorted(df['VWM_delay_s'].dropna().unique())}")
    print(f"VWM_block unique values: {sorted(df['VWM_block'].dropna().unique())}")
    print(f"VWM_pracAttempt unique values: {sorted(df['VWM_pracAttempt'].dropna().unique())}")
    
    # MRT parameters
    print(f"MRT_angle_degrees unique values: {sorted(df['MRT_angle_degrees'].dropna().unique())}")
    print(f"MRT_isReflected unique values: {sorted(df['MRT_isReflected'].dropna().unique())}")
    print(f"MRT_block unique values: {sorted(df['MRT_block'].dropna().unique())}")
    print(f"MRT_pracAttempt unique values: {sorted(df['MRT_pracAttempt'].dropna().unique())}")
    
    # General parameters
    print(f"table unique values: {sorted(df['table'].dropna().unique())}")
    print(f"isPractice unique values: {sorted(df['isPractice'].dropna().unique())}")
    print(f"taskOrder unique values: {sorted(df['taskOrder'].dropna().unique())}")
    print(f"wasFullscreenExited unique values: {sorted(df['wasFullscreenExited'].dropna().unique())}")
    
    # For measured variables, just print data types
    print(f"VWM_rt_ms data type: {df['VWM_rt_ms'].dtype}")
    print(f"VWM_error_degrees data type: {df['VWM_error_degrees'].dtype}")
    print(f"VWM_error_absolute_degrees data type: {df['VWM_error_absolute_degrees'].dtype}")
    print(f"MRT_rt_ms data type: {df['MRT_rt_ms'].dtype}")
    print(f"windowFocusLostDuringTasksNum data type: {df['windowFocusLostDuringTasksNum'].dtype}")
    print()

def apply_trial_exclusions(df):
    """
    Apply trial-level exclusions for VWM and MRT tasks.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Dataframe with trial exclusions applied
    """
    print("=== APPLYING TRIAL-LEVEL EXCLUSIONS ===")
    
    initial_rows = len(df)
    print(f"Initial number of rows: {initial_rows}")
    
    # Create a copy to work with
    df_clean = df.copy()
    
    # Track exclusions
    exclusions = []
    
    # VWM trial exclusions
    print("Applying VWM trial exclusions...")
    vwm_rows = df_clean['table'].isin(['vwm_practice', 'vwm_test'])
    vwm_data = df_clean[vwm_rows].copy()
    
    print(f"Total VWM rows before exclusions: {len(vwm_data)}")
    
    # VWM exclusion criteria
    vwm_rt_low = vwm_data['VWM_rt_ms'] < 200
    vwm_rt_high = vwm_data['VWM_rt_ms'] > 8000
    vwm_timeout = vwm_data['VWM_timeout'] == True
    vwm_no_response = pd.isna(vwm_data['VWM_responseAngle_degrees'])
    
    vwm_exclude = vwm_rt_low | vwm_rt_high | vwm_timeout | vwm_no_response
    
    print(f"VWM trials excluded for RT < 200ms: {vwm_rt_low.sum()}")
    print(f"VWM trials excluded for RT > 8000ms: {vwm_rt_high.sum()}")
    print(f"VWM trials excluded for timeout: {vwm_timeout.sum()}")
    print(f"VWM trials excluded for no response: {vwm_no_response.sum()}")
    print(f"Total VWM trials excluded: {vwm_exclude.sum()}")
    
    exclusions.append(['VWM_rt_low', vwm_rt_low.sum(), 'VWM trials with RT < 200ms'])
    exclusions.append(['VWM_rt_high', vwm_rt_high.sum(), 'VWM trials with RT > 8000ms'])
    exclusions.append(['VWM_timeout', vwm_timeout.sum(), 'VWM trials with timeout'])
    exclusions.append(['VWM_no_response', vwm_no_response.sum(), 'VWM trials with no response'])
    
    # Apply VWM exclusions
    vwm_data_clean = vwm_data[~vwm_exclude].copy()
    print(f"VWM rows after exclusions: {len(vwm_data_clean)}")
    
    # MRT trial exclusions
    print("\nApplying MRT trial exclusions...")
    mrt_rows = df_clean['table'].isin(['mrt_practice', 'mrt_test'])
    mrt_data = df_clean[mrt_rows].copy()
    
    print(f"Total MRT rows before exclusions: {len(mrt_data)}")
    
    # MRT exclusion criteria
    mrt_rt_low = mrt_data['MRT_rt_ms'] < 200
    mrt_rt_high = mrt_data['MRT_rt_ms'] > 8000
    mrt_timeout = mrt_data['MRT_timeout'] == True
    mrt_no_response = pd.isna(mrt_data['MRT_response'])
    
    mrt_exclude = mrt_rt_low | mrt_rt_high | mrt_timeout | mrt_no_response
    
    print(f"MRT trials excluded for RT < 200ms: {mrt_rt_low.sum()}")
    print(f"MRT trials excluded for RT > 8000ms: {mrt_rt_high.sum()}")
    print(f"MRT trials excluded for timeout: {mrt_timeout.sum()}")
    print(f"MRT trials excluded for no response: {mrt_no_response.sum()}")
    print(f"Total MRT trials excluded: {mrt_exclude.sum()}")
    
    exclusions.append(['MRT_rt_low', mrt_rt_low.sum(), 'MRT trials with RT < 200ms'])
    exclusions.append(['MRT_rt_high', mrt_rt_high.sum(), 'MRT trials with RT > 8000ms'])
    exclusions.append(['MRT_timeout', mrt_timeout.sum(), 'MRT trials with timeout'])
    exclusions.append(['MRT_no_response', mrt_no_response.sum(), 'MRT trials with no response'])
    
    # Apply MRT exclusions
    mrt_data_clean = mrt_data[~mrt_exclude].copy()
    print(f"MRT rows after exclusions: {len(mrt_data_clean)}")
    
    # Combine cleaned data with non-task rows
    other_rows = df_clean[~(vwm_rows | mrt_rows)]
    df_final = pd.concat([vwm_data_clean, mrt_data_clean, other_rows], ignore_index=True)
    
    print(f"Final number of rows after trial exclusions: {len(df_final)}")
    print()
    
    return df_final, exclusions

def calculate_practice_performance(df):
    """
    Calculate practice performance for each participant.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Participant-level practice performance metrics
    """
    print("=== CALCULATING PRACTICE PERFORMANCE ===")
    
    participants = df['participantId'].unique()
    practice_metrics = []
    
    for participant in participants:
        participant_data = df[df['participantId'] == participant]
        
        # VWM practice performance
        vwm_practice = participant_data[
            (participant_data['isPractice'] == True) & 
            (participant_data['table'] == 'vwm_practice')
        ]
        
        if len(vwm_practice) > 0:
            # Get final attempt (highest pracAttempt value)
            max_attempt = vwm_practice['VWM_pracAttempt'].max()
            final_attempt = vwm_practice[vwm_practice['VWM_pracAttempt'] == max_attempt]
            vwm_practice_error = final_attempt['VWM_error_absolute_degrees'].mean()
        else:
            vwm_practice_error = np.nan
        
        # MRT practice performance
        mrt_practice = participant_data[
            (participant_data['isPractice'] == True) & 
            (participant_data['table'] == 'mrt_practice')
        ]
        
        if len(mrt_practice) > 0:
            # Get final attempt (highest pracAttempt value)
            max_attempt = mrt_practice['MRT_pracAttempt'].max()
            final_attempt = mrt_practice[mrt_practice['MRT_pracAttempt'] == max_attempt]
            mrt_practice_correct = (final_attempt['MRT_isCorrect'] == True).mean()
        else:
            mrt_practice_correct = np.nan
        
        practice_metrics.append({
            'participantId': participant,
            'vwm_practice_error': vwm_practice_error,
            'mrt_practice_correct': mrt_practice_correct
        })
    
    practice_df = pd.DataFrame(practice_metrics)
    
    print("Practice performance summary:")
    print(f"VWM practice error - Mean: {practice_df['vwm_practice_error'].mean():.2f}, "
          f"Median: {practice_df['vwm_practice_error'].median():.2f}")
    print(f"MRT practice correct - Mean: {practice_df['mrt_practice_correct'].mean():.3f}, "
          f"Median: {practice_df['mrt_practice_correct'].median():.3f}")
    print()
    
    return practice_df

def calculate_trial_counts(df):
    """
    Calculate post-exclusion trial counts for each participant.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Participant-level trial counts
    """
    print("=== CALCULATING POST-EXCLUSION TRIAL COUNTS ===")
    
    participants = df['participantId'].unique()
    trial_counts = []
    
    for participant in participants:
        participant_data = df[df['participantId'] == participant]
        
        # VWM test trials
        vwm_test_count = len(participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['table'] == 'vwm_test')
        ])
        
        # MRT test trials
        mrt_test_count = len(participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['table'] == 'mrt_test')
        ])
        
        trial_counts.append({
            'participantId': participant,
            'vwm_test_trials': vwm_test_count,
            'mrt_test_trials': mrt_test_count
        })
    
    trial_counts_df = pd.DataFrame(trial_counts)
    
    print("Trial count summary:")
    print(f"VWM test trials - Mean: {trial_counts_df['vwm_test_trials'].mean():.1f}, "
          f"Min: {trial_counts_df['vwm_test_trials'].min()}, "
          f"Max: {trial_counts_df['vwm_test_trials'].max()}")
    print(f"MRT test trials - Mean: {trial_counts_df['mrt_test_trials'].mean():.1f}, "
          f"Min: {trial_counts_df['mrt_test_trials'].min()}, "
          f"Max: {trial_counts_df['mrt_test_trials'].max()}")
    print()
    
    return trial_counts_df

def calculate_session_metrics(df):
    """
    Calculate session-level metrics for each participant (excluding session duration).
    """
    print("=== CALCULATING SESSION METRICS ===")
    
    # Add debugging for timestamp and metadata structure
    print("Sample timestamp values:")
    print(df['timestamp'].head(10).tolist())
    print("Sample windowWidthPixels values:")
    print(df['windowWidthPixels'].head(10).tolist())
    print("Table types found:")
    print(df['table'].value_counts())
    print()
    
    participants = df['participantId'].unique()
    session_metrics = []
    
    for participant in participants:
        participant_data = df[df['participantId'] == participant]
        
        # Extract metadata from the dedicated metadata row
        metadata = participant_data[participant_data['table'] == 'metadata']
        
        if not metadata.empty:
            metadata_row = metadata.iloc[0]
            focus_loss_count = metadata_row['windowFocusLostDuringTasksNum']
            focus_loss_duration_raw = metadata_row['windowFocusLostDuringTasksDuration']
            screen_width = metadata_row['windowWidthPixels']
            screen_height = metadata_row['windowHeightPixels']
            fullscreen_exited = metadata_row['wasFullscreenExited']
        else:
            # Fallback if no metadata row found
            focus_loss_count = 0
            focus_loss_duration_raw = np.nan
            screen_width = np.nan
            screen_height = np.nan
            fullscreen_exited = False
        
        # Parse focus loss duration
        total_focus_loss_duration = parse_focus_loss_duration(focus_loss_duration_raw)
        if pd.isna(total_focus_loss_duration):
            total_focus_loss_duration = 0
        
        # Handle NaN values
        if pd.isna(focus_loss_count):
            focus_loss_count = 0
        if pd.isna(fullscreen_exited):
            fullscreen_exited = False
        
        session_metrics.append({
            'participantId': participant,
            'focus_loss_count': focus_loss_count,
            'focus_loss_duration_seconds': total_focus_loss_duration,
            'screen_width': screen_width,
            'screen_height': screen_height,
            'fullscreen_exited': fullscreen_exited
        })
    
    session_df = pd.DataFrame(session_metrics)
    
    print("Session metrics summary:")
    print(f"Focus loss count - Mean: {session_df['focus_loss_count'].mean():.1f}, "
          f"Max: {session_df['focus_loss_count'].max()}")
    print(f"Focus loss duration - Mean: {session_df['focus_loss_duration_seconds'].mean():.1f}s, "
          f"Max: {session_df['focus_loss_duration_seconds'].max():.1f}s")
    print(f"Screen width - Min: {session_df['screen_width'].min()}, Max: {session_df['screen_width'].max()}")
    print(f"Screen height - Min: {session_df['screen_height'].min()}, Max: {session_df['screen_height'].max()}")
    print(f"Fullscreen exited: {session_df['fullscreen_exited'].sum()} participants")
    print()
    
    return session_df

def apply_participant_exclusions(practice_df, trial_counts_df, session_df, session_duration_df):
    """
    Apply participant-level exclusions.
    
    Parameters:
    practice_df (pd.DataFrame): Practice performance metrics
    trial_counts_df (pd.DataFrame): Trial counts
    session_df (pd.DataFrame): Session metrics
    session_duration_df (pd.DataFrame): Session durations from Prolific
    
    Returns:
    tuple: (included_participants, exclusion_log)
    """
    print("=== APPLYING PARTICIPANT-LEVEL EXCLUSIONS ===")
    
    # Merge all metrics
    participant_metrics = practice_df.merge(trial_counts_df, on='participantId')
    participant_metrics = participant_metrics.merge(session_df, on='participantId')
    participant_metrics = participant_metrics.merge(session_duration_df, on='participantId', how='left')
    
    print(f"Total participants: {len(participant_metrics)}")
    
    exclusions = []
    
    # Apply exclusion criteria
    vwm_practice_fail = participant_metrics['vwm_practice_error'] >= 30
    mrt_practice_fail = participant_metrics['mrt_practice_correct'] < (8/12)
    vwm_trials_low = participant_metrics['vwm_test_trials'] < 80
    fullscreen_exit = participant_metrics['fullscreen_exited'] == True
    focus_loss_high = (participant_metrics['focus_loss_count'] > 15) | (participant_metrics['focus_loss_duration_seconds'] > 120)
    screen_size_low = (participant_metrics['screen_width'] < 768) | (participant_metrics['screen_height'] < 768)
    session_duration_bad = (participant_metrics['session_duration_minutes'] < 15) | (participant_metrics['session_duration_minutes'] > 90)
    
    print(f"Excluded for VWM practice error >= 30°: {vwm_practice_fail.sum()}")
    print(f"Excluded for MRT practice correct < 8/12: {mrt_practice_fail.sum()}")
    print(f"Excluded for VWM test trials < 80: {vwm_trials_low.sum()}")
    print(f"Excluded for fullscreen exit: {fullscreen_exit.sum()}")
    print(f"Excluded for excessive focus loss: {focus_loss_high.sum()}")
    print(f"Excluded for screen size < 768px: {screen_size_low.sum()}")
    print(f"Excluded for session duration < 15min or > 90min: {session_duration_bad.sum()}")
    
    exclusions.extend([
        ['VWM_practice_fail', vwm_practice_fail.sum(), 'VWM practice error >= 30 degrees'],
        ['MRT_practice_fail', mrt_practice_fail.sum(), 'MRT practice correct < 8/12'],
        ['VWM_trials_low', vwm_trials_low.sum(), 'VWM test trials < 80'],
        ['fullscreen_exit', fullscreen_exit.sum(), 'Fullscreen exited'],
        ['focus_loss_high', focus_loss_high.sum(), 'Focus loss count > 15 or duration > 120s'],
        ['screen_size_low', screen_size_low.sum(), 'Screen width or height < 768px'],
        ['session_duration_bad', session_duration_bad.sum(), 'Session duration < 15min or > 90min']
    ])
    
    # Combine all exclusions
    any_exclusion = vwm_practice_fail | mrt_practice_fail | vwm_trials_low | fullscreen_exit | focus_loss_high | screen_size_low | session_duration_bad
    
    included_participants = participant_metrics[~any_exclusion]['participantId'].tolist()
    
    print(f"Total participants excluded: {any_exclusion.sum()}")
    print(f"Final included participants: {len(included_participants)}")
    print()
    
    return included_participants, exclusions

def create_cleaned_dataset(df, included_participants):
    """
    Create cleaned dataset with only included participants and valid trials.
    
    Parameters:
    df (pd.DataFrame): Input dataframe after trial exclusions
    included_participants (list): List of included participant IDs
    
    Returns:
    pd.DataFrame: Cleaned dataset
    """
    print("=== CREATING CLEANED DATASET ===")
    
    # Filter to included participants only
    cleaned_df = df[df['participantId'].isin(included_participants)].copy()
    
    print(f"Cleaned dataset shape: {cleaned_df.shape}")
    print(f"Included participants: {len(included_participants)}")
    
    # Select only required output columns
    output_columns = [
        'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_setSize', 
        'VWM_delay_s', 'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 
        'VWM_error_degrees', 'VWM_error_absolute_degrees', 'VWM_rt_ms', 
        'VWM_block', 'MRT_trial', 'MRT_angle_degrees', 'MRT_isReflected', 
        'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_block', 
        'taskOrder', 'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration'
    ]
    
    cleaned_df = cleaned_df[output_columns].copy()
    
    print("Final cleaned dataset columns:")
    print(list(cleaned_df.columns))
    print("First 2 rows of cleaned dataset:")
    print(cleaned_df.head(2))
    print()
    
    return cleaned_df

def save_outputs(cleaned_df, all_exclusions):
    """
    Save cleaned dataset and exclusion log.
    
    Parameters:
    cleaned_df (pd.DataFrame): Cleaned dataset
    all_exclusions (list): List of exclusion criteria and counts
    """
    print("=== SAVING OUTPUTS ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save cleaned dataset
    cleaned_filename = f"outputs/cleaned_experimental_data_{timestamp}.csv"
    cleaned_df.to_csv(cleaned_filename, index=False)
    print(f"Saved cleaned dataset to: {cleaned_filename}")
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(all_exclusions, columns=['exclusion_criteria', 'n_excluded', 'description'])
    exclusion_filename = f"outputs/data_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(exclusion_filename, index=False)
    print(f"Saved exclusion log to: {exclusion_filename}")
    
    print("Exclusion summary:")
    print(exclusion_df)
    print()

def main():
    """
    Main function to execute the data cleaning pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting data cleaning pipeline...")
        
        # Load and combine data
        df = load_and_combine_data()
        if df is None:
            return 1
        
        # Validate required columns
        if not validate_required_columns(df):
            return 1
        
        # Print unique values for key columns
        print_unique_values(df)
        
        # Apply trial-level exclusions
        df_clean, trial_exclusions = apply_trial_exclusions(df)
        
        # Calculate practice performance
        practice_df = calculate_practice_performance(df_clean)
        
        # Calculate trial counts
        trial_counts_df = calculate_trial_counts(df_clean)
        
        # Get session durations from Prolific data
        session_duration_df = get_session_durations()
        
        # Calculate session metrics on original dataframe (before trial exclusions)
        session_df = calculate_session_metrics(df)
        
        # Apply participant-level exclusions
        included_participants, participant_exclusions = apply_participant_exclusions(
            practice_df, trial_counts_df, session_df, session_duration_df
        )
        
        # Create cleaned dataset
        cleaned_df = create_cleaned_dataset(df_clean, included_participants)
        
        # Combine all exclusions
        all_exclusions = trial_exclusions + participant_exclusions
        
        # Save outputs
        save_outputs(cleaned_df, all_exclusions)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

def get_session_durations():
    """
    Load Prolific export data and calculate session duration for each participant.
    
    Returns:
    pd.DataFrame: DataFrame with participantId and session_duration_minutes
    """
    print("=== LOADING SESSION DURATIONS FROM PROLIFIC DATA ===")
    
    prolific_files = glob.glob('../C_results/data/prolific_export_*.csv')
    if not prolific_files:
        print("WARNING: No Prolific export files found. Session duration cannot be calculated.")
        return pd.DataFrame(columns=['participantId', 'session_duration_minutes'])
    
    print(f"Found {len(prolific_files)} Prolific export files")
    
    all_prolific_data = []
    for file in prolific_files:
        try:
            df = pd.read_csv(file)
            all_prolific_data.append(df)
            print(f"Loaded Prolific file: {file} with {len(df)} rows")
        except Exception as e:
            print(f"Error loading Prolific file {file}: {e}")
    
    if not all_prolific_data:
        print("ERROR: No Prolific files could be loaded!")
        return pd.DataFrame(columns=['participantId', 'session_duration_minutes'])
    
    prolific_data = pd.concat(all_prolific_data, ignore_index=True)
    print(f"Combined Prolific data shape: {prolific_data.shape}")
    
    # Rename participant ID column for merging
    if 'Participant id' in prolific_data.columns:
        prolific_data.rename(columns={'Participant id': 'participantId'}, inplace=True)
    elif 'participant_id' in prolific_data.columns:
        prolific_data.rename(columns={'participant_id': 'participantId'}, inplace=True)
    
    # Convert timestamp columns to datetime
    prolific_data['Started at'] = pd.to_datetime(prolific_data['Started at'], errors='coerce')
    prolific_data['Completed at'] = pd.to_datetime(prolific_data['Completed at'], errors='coerce')
    
    # Calculate session duration in minutes
    prolific_data['session_duration_minutes'] = (prolific_data['Completed at'] - prolific_data['Started at']).dt.total_seconds() / 60
    
    session_duration_df = prolific_data[['participantId', 'session_duration_minutes']].copy()
    
    print(f"Session duration summary from Prolific data:")
    print(f"Mean: {session_duration_df['session_duration_minutes'].mean():.1f}min, "
          f"Min: {session_duration_df['session_duration_minutes'].min():.1f}min, "
          f"Max: {session_duration_df['session_duration_minutes'].max():.1f}min")
    print()
    
    return session_duration_df

if __name__ == "__main__":
    exit(main())
