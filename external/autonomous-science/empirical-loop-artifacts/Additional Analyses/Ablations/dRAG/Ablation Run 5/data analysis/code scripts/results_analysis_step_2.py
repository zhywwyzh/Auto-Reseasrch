import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def convert_time_to_seconds(time_str):
    """
    Convert time string in HH:MM:SS format to total seconds.
    
    Parameters:
    time_str (str): Time string in HH:MM:SS format
    
    Returns:
    float: Total seconds
    """
    if pd.isna(time_str) or time_str == '':
        return 0
    try:
        parts = str(time_str).split(':')
        if len(parts) == 3:
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0
    except:
        return 0

def load_participant_data():
    """
    Load all participant data files and prolific session data.
    
    Returns:
    tuple: (combined_task_data, prolific_data)
    """
    print("Loading participant data files...")
    
    # Load task data files
    task_files = glob.glob('../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv')
    print(f"Found {len(task_files)} task data files")
    
    if len(task_files) == 0:
        print("ERROR: No task data files found!")
        return None, None
    
    all_task_data = []
    for file in task_files:
        print(f"Loading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            all_task_data.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if len(all_task_data) == 0:
        print("ERROR: No valid task data files loaded!")
        return None, None
    
    # Combine all task data
    combined_task_data = pd.concat(all_task_data, ignore_index=True)
    print(f"Combined task data shape: {combined_task_data.shape}")
    print(f"Combined task data columns: {list(combined_task_data.columns)}")
    print("First 2 rows of combined data:")
    print(combined_task_data.head(2))
    
    # Load prolific session data
    prolific_files = glob.glob('outputs/prolific_session_data_*.csv')
    print(f"Found {len(prolific_files)} prolific session files")
    
    if len(prolific_files) == 0:
        print("ERROR: No prolific session data files found!")
        return combined_task_data, None
    
    # Get most recent prolific file
    prolific_file = max(prolific_files, key=os.path.getctime)
    print(f"Using most recent prolific file: {prolific_file}")
    
    try:
        prolific_data = pd.read_csv(prolific_file)
        print(f"Prolific data shape: {prolific_data.shape}")
        print(f"Prolific data columns: {list(prolific_data.columns)}")
        print("First 3 rows of prolific data:")
        print(prolific_data.head(3))
    except Exception as e:
        print(f"Error loading prolific data: {e}")
        return combined_task_data, None
    
    return combined_task_data, prolific_data

def print_data_overview(df):
    """
    Print overview of key experimental design parameters.
    
    Parameters:
    df (pd.DataFrame): Task data
    """
    print("\n=== DATA OVERVIEW ===")
    
    # Print unique values for key experimental design columns
    design_columns = ['VWM_setSize', 'VWM_delay_s', 'VWM_block', 'MRT_angle_degrees', 'MRT_block', 'isPractice']
    for col in design_columns:
        if col in df.columns:
            unique_vals = df[col].dropna().unique()
            print(f"{col} unique values: {sorted(unique_vals) if len(unique_vals) < 50 else f'[{len(unique_vals)} unique values]'}")
    
    # Print data types for measured variables
    measured_columns = ['VWM_rt_ms', 'VWM_error_degrees', 'MRT_rt_ms', 'MRT_isCorrect']
    for col in measured_columns:
        if col in df.columns:
            print(f"{col} data type: {df[col].dtype}")
    
    print(f"Total participants: {df['participantId'].nunique()}")
    print(f"Total rows: {len(df)}")

def apply_exclusion_criteria(task_data, prolific_data):
    """
    Apply all exclusion criteria to participant data in a cascaded (sequential) fashion.
    
    Parameters:
    task_data (pd.DataFrame): Combined task data
    prolific_data (pd.DataFrame): Prolific session data
    
    Returns:
    tuple: (exclusions_dict, included_participants, excluded_participants, total_participants)
    """
    print("\n=== APPLYING EXCLUSION CRITERIA ===")
    
    exclusions = {
        'practice_block_failure': 0,
        'mrt_chance_performance': 0,
        'timeout_rate': 0,
        'focus_loss_duration': 0,
        'incomplete_data': 0,
        'session_duration': 0
    }
    
    # Efficient participant data access
    grouped_data = task_data.groupby('participantId')
    participant_data_dict = {participant: data for participant, data in grouped_data}
    
    excluded_participants = {}
    participants_remaining = task_data['participantId'].unique().tolist()
    total_participants = len(participants_remaining)
    print(f"Total participants to screen: {total_participants}")
    
    # 1. Practice block failure (cascaded)
    print(f"\n1. Checking practice block failure on {len(participants_remaining)} participants...")
    excluded_for_practice = []
    for participant in participants_remaining:
        participant_data = participant_data_dict[participant]
        vwm_prac_max = participant_data['VWM_pracAttempt'].max()
        mrt_prac_max = participant_data['MRT_pracAttempt'].max()
        
        reasons = []
        if pd.notna(vwm_prac_max) and vwm_prac_max > 5:
            reasons.append('VWM practice failure')
        if pd.notna(mrt_prac_max) and mrt_prac_max > 5:
            reasons.append('MRT practice failure')
        
        if reasons:
            excluded_for_practice.append(participant)
            excluded_participants[participant] = '; '.join(reasons)
    exclusions['practice_block_failure'] = len(excluded_for_practice)
    participants_remaining = [p for p in participants_remaining if p not in excluded_for_practice]
    print(f"Excluded {len(excluded_for_practice)} for practice failure. Remaining: {len(participants_remaining)}")
    
    # 2. MRT chance performance (cascaded)
    print(f"\n2. Checking MRT chance performance on {len(participants_remaining)} participants...")
    excluded_for_mrt = []
    for participant in participants_remaining:
        participant_data = participant_data_dict[participant]
        mrt_test_data = participant_data[
            (participant_data['isPractice'] == False)
        ]
        if mrt_test_data['MRT_isCorrect'].notna().any():
            mrt_accuracy = mrt_test_data['MRT_isCorrect'].astype('boolean').mean()
            if pd.notna(mrt_accuracy) and mrt_accuracy <= 0.50:
                excluded_for_mrt.append(participant)
                excluded_participants[participant] = 'MRT chance performance'
    exclusions['mrt_chance_performance'] = len(excluded_for_mrt)
    participants_remaining = [p for p in participants_remaining if p not in excluded_for_mrt]
    print(f"Excluded {len(excluded_for_mrt)} for MRT chance performance. Remaining: {len(participants_remaining)}")
    
    # 3. Timeout rate (cascaded)
    print(f"\n3. Checking timeout rate on {len(participants_remaining)} participants...")
    excluded_for_timeout = []
    for participant in participants_remaining:
        participant_data = participant_data_dict[participant]
        test_data = participant_data[participant_data['isPractice'] == False]
        vwm_timeouts = test_data['VWM_timeout'].astype('boolean').sum()
        mrt_timeouts = test_data['MRT_timeout'].astype('boolean').sum()
        total_timeouts = vwm_timeouts + mrt_timeouts
        vwm_valid_trials = test_data['VWM_timeout'].notna().sum()
        mrt_valid_trials = test_data['MRT_timeout'].notna().sum()
        total_valid_trials = vwm_valid_trials + mrt_valid_trials
        if total_valid_trials > 0:
            timeout_rate = total_timeouts / total_valid_trials
            if timeout_rate > 0.20:
                excluded_for_timeout.append(participant)
                excluded_participants[participant] = 'high timeout rate'
    exclusions['timeout_rate'] = len(excluded_for_timeout)
    participants_remaining = [p for p in participants_remaining if p not in excluded_for_timeout]
    print(f"Excluded {len(excluded_for_timeout)} for timeout rate. Remaining: {len(participants_remaining)}")
    
    # 4. Focus loss duration (cascaded)
    print(f"\n4. Checking focus loss duration on {len(participants_remaining)} participants...")
    excluded_for_focus = []
    for participant in participants_remaining:
        participant_data = participant_data_dict[participant]
        prolific_participant = prolific_data[prolific_data['participant_id'] == participant]
        if len(prolific_participant) > 0:
            focus_loss_str = participant_data['windowFocusLostDuringTasksDuration'].iloc[0]
            session_duration_min = prolific_participant['session_duration_minutes'].iloc[0]
            focus_loss_seconds = convert_time_to_seconds(focus_loss_str)
            session_duration_seconds = session_duration_min * 60
            if session_duration_seconds > 0:
                focus_loss_percentage = (focus_loss_seconds / session_duration_seconds) * 100
                if focus_loss_percentage > 15:
                    excluded_for_focus.append(participant)
                    excluded_participants[participant] = 'excessive focus loss'
    exclusions['focus_loss_duration'] = len(excluded_for_focus)
    participants_remaining = [p for p in participants_remaining if p not in excluded_for_focus]
    print(f"Excluded {len(excluded_for_focus)} for focus loss duration. Remaining: {len(participants_remaining)}")
    
    # 5. Incomplete data (cascaded)
    print(f"\n5. Checking incomplete data on {len(participants_remaining)} participants...")
    excluded_for_incomplete = []
    for participant in participants_remaining:
        participant_data = participant_data_dict[participant]
        vwm_test_trials = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['VWM_trial'].notna())
        ]['VWM_trial'].nunique()
        mrt_test_trials = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['MRT_trial'].notna())
        ]['MRT_trial'].nunique()
        vwm_missing_pct = (126 - vwm_test_trials) / 126
        mrt_missing_pct = (102 - mrt_test_trials) / 102
        if vwm_missing_pct > 0.25 or mrt_missing_pct > 0.25:
            excluded_for_incomplete.append(participant)
            excluded_participants[participant] = 'incomplete data'
    exclusions['incomplete_data'] = len(excluded_for_incomplete)
    participants_remaining = [p for p in participants_remaining if p not in excluded_for_incomplete]
    print(f"Excluded {len(excluded_for_incomplete)} for incomplete data. Remaining: {len(participants_remaining)}")
    
    # 6. Session duration (cascaded)
    print(f"\n6. Checking session duration on {len(participants_remaining)} participants...")
    excluded_for_session = []
    for participant in participants_remaining:
        prolific_participant = prolific_data[prolific_data['participant_id'] == participant]
        if len(prolific_participant) > 0:
            session_duration = prolific_participant['session_duration_minutes'].iloc[0]
            if session_duration < 15 or session_duration > 120:
                excluded_for_session.append(participant)
                excluded_participants[participant] = 'invalid session duration'
    exclusions['session_duration'] = len(excluded_for_session)
    participants_remaining = [p for p in participants_remaining if p not in excluded_for_session]
    print(f"Excluded {len(excluded_for_session)} for session duration. Remaining: {len(participants_remaining)}")
    
    included_participants = participants_remaining
    
    print(f"\n=== EXCLUSION SUMMARY ===")
    for criterion, count in exclusions.items():
        print(f"{criterion}: {count} participants excluded")
    print(f"Total included participants: {len(included_participants)}")
    print(f"Total excluded participants: {len(excluded_participants)}")
    
    return exclusions, included_participants, excluded_participants, total_participants

def save_outputs(exclusions, included_participants, excluded_participants, total_participants, clean_data):
    """
    Save all output files.
    
    Parameters:
    exclusions (dict): Exclusion counts
    included_participants (list): List of included participant IDs
    excluded_participants (dict): Dictionary of excluded participants and reasons
    total_participants (int): Total participants screened
    clean_data (pd.DataFrame): Cleaned participant data
    """
    print("\n=== SAVING OUTPUTS ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 1. Save exclusion log
    exclusion_log = []
    for criterion, count in exclusions.items():
        exclusion_log.append({
            'exclusion_criterion': criterion,
            'excluded_count': count,
            'total_participants_screened': total_participants
        })
    
    exclusion_df = pd.DataFrame(exclusion_log)
    exclusion_file = f'outputs/participant_exclusion_log_{timestamp}.csv'
    exclusion_df.to_csv(exclusion_file, index=False)
    print(f"Saved exclusion log to: {exclusion_file}")
    print("Exclusion log contents:")
    print(exclusion_df)
    
    # 2. Save included participants
    participant_status = []
    
    # Add included participants
    for participant in included_participants:
        participant_status.append({
            'participantId': participant,
            'included': True,
            'exclusion_reason': ''
        })
    
    # Add excluded participants
    for participant, reason in excluded_participants.items():
        participant_status.append({
            'participantId': participant,
            'included': False,
            'exclusion_reason': reason
        })
    
    participants_df = pd.DataFrame(participant_status)
    participants_file = f'outputs/included_participants_{timestamp}.csv'
    participants_df.to_csv(participants_file, index=False)
    print(f"Saved participant list to: {participants_file}")
    print("First 2 rows of participant list:")
    print(participants_df.head(2))
    
    # 3. Save cleaned data
    clean_file = f'outputs/participant_level_cleaned_data_{timestamp}.csv'
    clean_data.to_csv(clean_file, index=False)
    print(f"Saved cleaned data to: {clean_file}")
    print(f"Cleaned data shape: {clean_data.shape}")
    print("Cleaned data columns:")
    print(list(clean_data.columns))
    print("First 2 rows of cleaned data:")
    print(clean_data.head(2))

def main():
    """
    Main function to execute the participant exclusion and data cleaning process.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("=== PARTICIPANT EXCLUSION AND DATA CLEANING ===")
        
        # Load data
        task_data, prolific_data = load_participant_data()
        if task_data is None:
            print("ERROR: Failed to load task data")
            return 1
        if prolific_data is None:
            print("ERROR: Failed to load prolific data")
            return 1
        
        # Print data overview
        print_data_overview(task_data)
        
        # Apply exclusion criteria
        exclusions, included_participants, excluded_participants, total_participants = apply_exclusion_criteria(task_data, prolific_data)
        
        # Create cleaned dataset with only included participants
        print("\nCreating cleaned dataset...")
        clean_data = task_data[task_data['participantId'].isin(included_participants)].copy()
        
        # Ensure boolean columns are properly formatted
        boolean_columns = ['isPractice', 'VWM_timeout', 'MRT_timeout', 'MRT_isCorrect', 'MRT_isReflected', 'VWM_isAttentionCheck', 'MRT_isAttentionCheck']
        for col in boolean_columns:
            if col in clean_data.columns:
                clean_data[col] = clean_data[col].astype('boolean')
        
        # Filter to required columns
        required_columns = [
            'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_setSize',
            'VWM_delay_s', 'VWM_cueIndex', 'VWM_orientations_degrees',
            'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees',
            'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_pracAttempt', 'VWM_timeout',
            'VWM_block', 'VWM_isAttentionCheck', 'MRT_trial', 'MRT_stimulusId',
            'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response', 'MRT_isCorrect',
            'MRT_rt_ms', 'MRT_pracAttempt', 'MRT_timeout', 'MRT_block',
            'MRT_isAttentionCheck', 'windowFocusLostDuringTasksDuration',
            'windowFocusLostDuringTasksNum', 'timestamp'
        ]
        clean_data = clean_data[required_columns]
        
        print(f"Clean data contains {len(included_participants)} participants")
        print(f"Clean data shape: {clean_data.shape}")
        
        # Save outputs
        save_outputs(exclusions, included_participants, excluded_participants, total_participants, clean_data)
        
        # Final summary printout
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Initial participants: {total_participants}")
        for criterion, count in exclusions.items():
            print(f"Excluded for {criterion}: {count}")
        print(f"Final included participants: {len(included_participants)}")
        print(f"Data retention rate: {len(included_participants)/total_participants*100:.1f}%")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
