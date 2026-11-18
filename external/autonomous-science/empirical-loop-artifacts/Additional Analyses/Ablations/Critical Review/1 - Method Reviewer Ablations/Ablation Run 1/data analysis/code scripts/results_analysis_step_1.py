import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import re
import sys

def load_participant_data():
    """
    Load all participant VWM and MRT task data files.
    
    Returns:
        pd.DataFrame: Combined dataframe with all participant task data
    """
    print("Loading participant VWM and MRT task data...")
    
    # Find all participant data files
    file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    participant_files = glob.glob(file_pattern)
    
    print(f"Found {len(participant_files)} participant data files")
    
    if not participant_files:
        print("ERROR: No participant data files found!")
        return None
    
    combined_data = []
    
    for file_path in participant_files:
        print(f"Loading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()
            print(f"File columns: {list(df.columns)}")
            print(f"First 3 rows:")
            print(df.head(3))
            print(f"File shape: {df.shape}")
            combined_data.append(df)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if not combined_data:
        print("ERROR: No valid participant data files loaded!")
        return None
    
    # Combine all participant data
    all_data = pd.concat(combined_data, ignore_index=True)
    print(f"Combined data shape: {all_data.shape}")
    print(f"Combined data columns: {list(all_data.columns)}")
    print("First 2 rows of combined data:")
    print(all_data.head(2))
    
    return all_data

def load_vviq2_data():
    """
    Load VVIQ2 questionnaire data.
    
    Returns:
        pd.DataFrame: VVIQ2 questionnaire responses
    """
    print("\nLoading VVIQ2 questionnaire data...")
    
    vviq2_file = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
    
    try:
        vviq2_df = pd.read_csv(vviq2_file)
        vviq2_df.columns = vviq2_df.columns.str.strip()
        print(f"VVIQ2 file columns: {list(vviq2_df.columns)}")
        print("First 3 rows of VVIQ2 data:")
        print(vviq2_df.head(3))
        print(f"VVIQ2 data shape: {vviq2_df.shape}")
        return vviq2_df
    except Exception as e:
        print(f"Error loading VVIQ2 data: {e}")
        return None

def load_prolific_data():
    """
    Load Prolific export data.
    
    Returns:
        pd.DataFrame: Prolific participant session data
    """
    print("\nLoading Prolific export data...")
    
    # Find prolific export files
    prolific_pattern = "../C_results/data/prolific_export_*.csv"
    prolific_files = glob.glob(prolific_pattern)
    
    print(f"Found {len(prolific_files)} prolific export files")
    
    if not prolific_files:
        print("ERROR: No prolific export files found!")
        return None
    
    # Use the most recent file if multiple exist
    prolific_files.sort(key=os.path.getmtime, reverse=True)
    prolific_file = prolific_files[0]
    print(f"Using prolific file: {prolific_file}")
    
    try:
        prolific_df = pd.read_csv(prolific_file)
        prolific_df.columns = prolific_df.columns.str.strip()
        print(f"Prolific file columns: {list(prolific_df.columns)}")
        print("First 3 rows of Prolific data:")
        print(prolific_df.head(3))
        print(f"Prolific data shape: {prolific_df.shape}")
        return prolific_df
    except Exception as e:
        print(f"Error loading Prolific data: {e}")
        return None

def extract_vviq2_scores(vviq2_text):
    """
    Extract numeric scores from VVIQ2 text responses.
    
    Args:
        vviq2_text (str): Text containing VVIQ2 responses
        
    Returns:
        list: List of numeric scores (1-5)
    """
    if pd.isna(vviq2_text) or not isinstance(vviq2_text, str):
        return []
    
    # Find all digits 1-5 in the text
    scores = re.findall(r'[1-5]', vviq2_text)
    return [int(score) for score in scores]

def check_incomplete_data(participant_data, vviq2_data, prolific_data):
    """
    Check for participants with incomplete data across the three main components.
    
    Args:
        participant_data (pd.DataFrame): Combined participant task data
        vviq2_data (pd.DataFrame): VVIQ2 questionnaire data
        prolific_data (pd.DataFrame): Prolific session data
        
    Returns:
        set: Set of participantIds with incomplete data
    """
    print("\nChecking for incomplete data...")
    
    incomplete_participants = set()
    
    # Get unique participant IDs from each dataset
    task_participants = set(participant_data['participantId'].unique()) if participant_data is not None else set()
    vviq2_participants = set(vviq2_data['PROLIFIC_PID'].unique()) if vviq2_data is not None else set()
    prolific_participants = set(prolific_data['Participant id'].unique()) if prolific_data is not None else set()
    
    print(f"Task participants: {len(task_participants)}")
    print(f"VVIQ2 participants: {len(vviq2_participants)}")
    print(f"Prolific participants: {len(prolific_participants)}")
    
    # Find participants missing from any dataset
    all_participants = task_participants.union(vviq2_participants).union(prolific_participants)
    
    for participant in all_participants:
        if (participant not in task_participants or 
            participant not in vviq2_participants or 
            participant not in prolific_participants):
            incomplete_participants.add(participant)
    
    # Check for missing VWM/MRT trial data
    if participant_data is not None:
        for participant in task_participants:
            participant_subset = participant_data[participant_data['participantId'] == participant]
            
            # Check for VWM trials
            vwm_trials = participant_subset[pd.notna(participant_subset['VWM_trial'])]
            if len(vwm_trials) == 0:
                incomplete_participants.add(participant)
                continue
                
            # Check for MRT trials
            mrt_trials = participant_subset[pd.notna(participant_subset['MRT_trial'])]
            if len(mrt_trials) == 0:
                incomplete_participants.add(participant)
    
    print(f"Participants with incomplete data: {len(incomplete_participants)}")
    return incomplete_participants

def check_technical_issues(participant_data):
    """
    Check for participants with technical issues (low frame rate or screen resolution).
    
    Args:
        participant_data (pd.DataFrame): Combined participant task data
        
    Returns:
        set: Set of participantIds with technical issues
    """
    print("\nChecking for technical issues...")
    
    technical_issue_participants = set()
    
    if participant_data is None:
        return technical_issue_participants

    # Ensure numeric columns are properly typed
    for col in ['frameRate', 'screenWidthPixels', 'screenHeightPixels']:
        if col in participant_data.columns:
            participant_data[col] = pd.to_numeric(participant_data[col], errors='coerce')
    
    # Get participant-level technical metrics (use first row per participant)
    participant_tech = participant_data.groupby('participantId').first()
    
    for participant_id, row in participant_tech.iterrows():
        # Check frame rate
        if pd.notna(row['frameRate']) and row['frameRate'] < 10:
            technical_issue_participants.add(participant_id)
            continue
            
        # Check screen resolution
        if (pd.notna(row['screenWidthPixels']) and pd.notna(row['screenHeightPixels']) and
            (row['screenWidthPixels'] < 600 or row['screenHeightPixels'] < 600)):
            technical_issue_participants.add(participant_id)
    
    print(f"Participants with technical issues: {len(technical_issue_participants)}")
    return technical_issue_participants

def check_excessive_focus_loss(participant_data):
    """
    Check for participants with excessive focus loss during tasks.
    
    Args:
        participant_data (pd.DataFrame): Combined participant task data
        
    Returns:
        set: Set of participantIds with excessive focus loss
    """
    print("\nChecking for excessive focus loss...")
    
    focus_loss_participants = set()
    
    if participant_data is None:
        return focus_loss_participants
    
    # Get participant-level focus loss metrics (use first row per participant)
    participant_focus = participant_data.groupby('participantId').first()
    
    for participant_id, row in participant_focus.iterrows():
        # Check number of focus loss events
        if pd.notna(row['windowFocusLostDuringTasksNum']) and row['windowFocusLostDuringTasksNum'] > 15:
            focus_loss_participants.add(participant_id)
            continue

        # Check total unfocused time (convert to minutes)
        duration_val = row['windowFocusLostDuringTasksDuration']
        if pd.notna(duration_val):
            try:
                duration_val = float(duration_val)
                unfocused_minutes = duration_val / 60
                if unfocused_minutes > 5:
                    focus_loss_participants.add(participant_id)
            except (ValueError, TypeError):
                continue
    
    print(f"Participants with excessive focus loss: {len(focus_loss_participants)}")
    return focus_loss_participants

def check_timeout_rates(participant_data):
    """
    Check for participants with high timeout rates on VWM or MRT tasks.
    
    Args:
        participant_data (pd.DataFrame): Combined participant task data
        
    Returns:
        tuple: (set of VWM timeout participants, set of MRT timeout participants)
    """
    print("\nChecking timeout rates...")
    
    vwm_timeout_participants = set()
    mrt_timeout_participants = set()
    
    if participant_data is None:
        return vwm_timeout_participants, mrt_timeout_participants
    
    # Print unique values for key experimental parameters
    print("Unique VWM_setSize values:", participant_data['VWM_setSize'].dropna().unique())
    print("Unique MRT_angle_degrees values:", participant_data['MRT_angle_degrees'].dropna().unique())
    print("Unique isPractice values:", participant_data['isPractice'].unique())
    
    for participant_id in participant_data['participantId'].unique():
        participant_subset = participant_data[participant_data['participantId'] == participant_id]
        
        # Check VWM timeout rate
        vwm_trials = participant_subset[
            (pd.notna(participant_subset['VWM_trial'])) & 
            (participant_subset['isPractice'] == False)
        ]
        
        if len(vwm_trials) > 0:
            vwm_timeouts = vwm_trials['VWM_timeout'].sum()
            vwm_timeout_rate = vwm_timeouts / len(vwm_trials)
            if vwm_timeout_rate > 0.20:
                vwm_timeout_participants.add(participant_id)
        
        # Check MRT timeout rate
        mrt_trials = participant_subset[
            (pd.notna(participant_subset['MRT_trial'])) & 
            (participant_subset['isPractice'] == False)
        ]
        
        if len(mrt_trials) > 0:
            mrt_timeouts = mrt_trials['MRT_timeout'].sum()
            mrt_timeout_rate = mrt_timeouts / len(mrt_trials)
            if mrt_timeout_rate > 0.20:
                mrt_timeout_participants.add(participant_id)
    
    print(f"VWM timeout participants: {len(vwm_timeout_participants)}")
    print(f"MRT timeout participants: {len(mrt_timeout_participants)}")
    return vwm_timeout_participants, mrt_timeout_participants

def check_attention_check_performance(participant_data):
    """
    Check attention check performance for VWM and MRT tasks.
    
    Args:
        participant_data (pd.DataFrame): Combined participant task data
        
    Returns:
        tuple: (set of VWM attention check failures, set of MRT attention check failures)
    """
    print("\nChecking attention check performance...")
    
    vwm_attention_failures = set()
    mrt_attention_failures = set()
    
    if participant_data is None:
        return vwm_attention_failures, mrt_attention_failures
    
    print("Unique VWM_isAttentionCheck values:", participant_data['VWM_isAttentionCheck'].unique())
    print("Unique MRT_isAttentionCheck values:", participant_data['MRT_isAttentionCheck'].unique())
    
    for participant_id in participant_data['participantId'].unique():
        participant_subset = participant_data[participant_data['participantId'] == participant_id]
        
        # Check VWM attention check performance
        vwm_attention_trials = participant_subset[
            (participant_subset['isPractice'] == False) & 
            (participant_subset['VWM_isAttentionCheck'] == True) &
            (pd.notna(participant_subset['VWM_trial']))
        ]
        
        if len(vwm_attention_trials) > 0:
            vwm_correct = (vwm_attention_trials['VWM_error_absolute_degrees'] <= 30).sum()
            vwm_accuracy = vwm_correct / len(vwm_attention_trials)
            if vwm_accuracy < 0.60:
                vwm_attention_failures.add(participant_id)
        
        # Check MRT attention check performance
        mrt_attention_trials = participant_subset[
            (participant_subset['isPractice'] == False) & 
            (participant_subset['MRT_isAttentionCheck'] == True) &
            (pd.notna(participant_subset['MRT_trial']))
        ]
        
        if len(mrt_attention_trials) > 0:
            mrt_correct = mrt_attention_trials['MRT_isCorrect'].sum()
            mrt_accuracy = mrt_correct / len(mrt_attention_trials)
            if mrt_accuracy < 0.40:
                mrt_attention_failures.add(participant_id)
    
    print(f"VWM attention check failures: {len(vwm_attention_failures)}")
    print(f"MRT attention check failures: {len(mrt_attention_failures)}")
    return vwm_attention_failures, mrt_attention_failures

def check_vviq2_response_validity(vviq2_data, prolific_data):
    """
    Check VVIQ2 response validity (identical responses and completion time).
    
    Args:
        vviq2_data (pd.DataFrame): VVIQ2 questionnaire data
        prolific_data (pd.DataFrame): Prolific session data
        
    Returns:
        set: Set of participantIds with invalid VVIQ2 responses
    """
    print("\nChecking VVIQ2 response validity...")
    
    vviq2_invalid_participants = set()
    
    if vviq2_data is None or prolific_data is None:
        return vviq2_invalid_participants
    
    # Map prolific completion times
    prolific_times = {}
    for _, row in prolific_data.iterrows():
        participant_id = row['Participant id']
        time_taken_numeric = pd.to_numeric(row['Time taken'], errors='coerce')
        if pd.notna(time_taken_numeric):
            time_taken_minutes = time_taken_numeric / 60
        else:
            time_taken_minutes = float('inf')
        prolific_times[participant_id] = time_taken_minutes

    vviq2_item_columns = [
        'The exact contour of face, head, shoulders and body.',
        'Characteristic poses of head, attitudes of body etc.',
        'The precise carriage, length of step, etc. in walking.',
        'The different colours worn in some familiar clothes.',
        'The sun is rising above the horizon into a hazy sky.',
        'The sky clears and surrounds the sun with blueness.',
        'Clouds. A storm blows up, with flashes of lightening.',
        'A rainbow appears.',
        'The overall appearance of the shop from the opposite side of the road.',
        'A window display including colours, shape and details of individual items for sale.',
        'You are near the entrance. The colour, shape and details of the door.',
        'You enter the shop and go to the counter. The counter assistant serves you. Money changes hands.',
        'The contours of the landscape.',
        'The colour and shape of the trees.',
        'The colour and shape of the lake.',
        'A strong wind blows on the tree and on the lake causing waves.',
        'You observe the heavy traffic travelling at maximum speed around your car. The overall appearance of vehicles, their colours, sizes and shapes.',
        'Your car accelerates to overtake the traffic directly in front of you. You see and urgent expression on the face of the driver and the people in the other vehicles as you pass.',
        'A large truck is flashing its headlight directly behind. Your car quickly moves over to let the truck pass. The driver signals with a friendly wave.',
        'You see a broken-down vehicle beside the road. Its lights are flashing. The driver is looking concerned and she is using a mobile phone.',
        'The overall appearance and colour of the water, surf, and sky.',
        'Bathers are swimming and splashing about in the water. Some are playing with a brightly coloured beach ball.',
        'An ocean liner crosses the horizon. It leaves a trail of smoke in the blue sky.',
        'A beautiful air balloon appears with four people aboard. The balloon drifts past you, almost directly overhead. The passengers wave and smile. You wave and smile back at them.',
        'The overall appearance of the station viewed from in front of the main entrance.',
        'You walk into the station. The colour, shape and details of the entrance hall.',
        'You approach the ticket office, go to a vacant counter and purchase your ticket.',
        'You walk to the platform and observe other passengers and the railway lines. A train arrives. You climb aboard.',
        'The overall appearance and design of the garden.',
        'The colour and shape of the bushes and shrubs.',
        'The colour and appearance of the flowers.',
        'Some birds fly down onto the lawn and start pecking for food.'
    ]
    print(f"VVIQ2 item columns: {len(vviq2_item_columns)}")

    # Verify VVIQ2 columns exist
    available_vviq2_cols = [col for col in vviq2_item_columns if col in vviq2_data.columns]
    if len(available_vviq2_cols) < 32:
        print(f"Warning: Only {len(available_vviq2_cols)} of 32 VVIQ2 columns found")
        return vviq2_invalid_participants

    for _, row in vviq2_data.iterrows():
        participant_id = row['PROLIFIC_PID']
        
        # Extract all VVIQ2 scores for this participant
        all_scores = []
        for col in available_vviq2_cols:
            scores = extract_vviq2_scores(str(row[col]))
            all_scores.extend(scores)
        
        if len(all_scores) >= 32:  # Should have 32 VVIQ2 items
            # Calculate mode percentage
            from collections import Counter
            score_counts = Counter(all_scores)
            if len(all_scores) > 0:  # Safety check
                most_common_count = score_counts.most_common(1)[0][1]
                mode_percentage = most_common_count / len(all_scores)
                
                # Check completion time
                completion_time_minutes = prolific_times.get(participant_id, float('inf'))
                
                # Apply conjunction: both criteria must be met
                if mode_percentage > 0.85 and completion_time_minutes < 8:
                    vviq2_invalid_participants.add(participant_id)
    
    print(f"VVIQ2 invalid participants: {len(vviq2_invalid_participants)}")
    return vviq2_invalid_participants

def check_session_duration_outliers(prolific_data):
    """
    Check for session duration outliers (>3 SD from mean).
    
    Args:
        prolific_data (pd.DataFrame): Prolific session data
        
    Returns:
        set: Set of participantIds with outlier session durations
    """
    print("\nChecking session duration outliers...")
    
    duration_outliers = set()
    
    if prolific_data is None:
        return duration_outliers
    
    # Convert time taken to numeric and then to minutes
    time_taken_numeric = pd.to_numeric(prolific_data['Time taken'], errors='coerce')
    durations_minutes = time_taken_numeric / 60
    
    # Calculate mean and standard deviation
    mean_duration = durations_minutes.mean()
    std_duration = durations_minutes.std()
    
    print(f"Mean session duration: {mean_duration:.2f} minutes")
    print(f"SD session duration: {std_duration:.2f} minutes")
    
    # Find outliers
    lower_bound = mean_duration - 3 * std_duration
    upper_bound = mean_duration + 3 * std_duration
    
    print(f"Duration bounds: {lower_bound:.2f} - {upper_bound:.2f} minutes")
    
    for idx, row in prolific_data.iterrows():
        participant_id = row['Participant id']
        duration_minutes = pd.to_numeric(row['Time taken'], errors='coerce') / 60
        
        if pd.notna(duration_minutes) and (duration_minutes < lower_bound or duration_minutes > upper_bound):
            duration_outliers.add(participant_id)
    
    print(f"Session duration outliers: {len(duration_outliers)}")
    return duration_outliers

def create_participant_mapping(participant_data, prolific_data):
    """
    Create mapping between participantId and Prolific Participant id.
    
    Args:
        participant_data (pd.DataFrame): Combined participant task data
        prolific_data (pd.DataFrame): Prolific session data
        
    Returns:
        dict: Mapping from participantId to prolific_participant_id
    """
    print("\nCreating participant ID mapping...")
    
    mapping = {}
    
    if participant_data is not None:
        task_participants = set(participant_data['participantId'].unique())
    else:
        task_participants = set()
    
    if prolific_data is not None:
        prolific_participants = set(prolific_data['Participant id'].unique())
    else:
        prolific_participants = set()
    
    # Create mapping (assuming participantId matches Participant id)
    for participant in task_participants:
        if participant in prolific_participants:
            mapping[participant] = participant
        else:
            mapping[participant] = None
    
    # Add any prolific participants not in task data
    for participant in prolific_participants:
        if participant not in mapping:
            mapping[participant] = participant
    
    print(f"Created mapping for {len(mapping)} participants")
    return mapping

def main():
    """
    Main function to execute participant exclusion analysis.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting participant exclusion analysis...")
        
        # Create outputs directory
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Load all data
        participant_data = load_participant_data()
        vviq2_data = load_vviq2_data()
        prolific_data = load_prolific_data()

        # Convert numeric columns to proper types
        if participant_data is not None:
            numeric_cols = ['frameRate', 'screenWidthPixels', 'screenHeightPixels', 
                            'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration']
            for col in numeric_cols:
                if col in participant_data.columns:
                    participant_data[col] = pd.to_numeric(participant_data[col], errors='coerce')

        # Convert prolific numeric columns
        if prolific_data is not None:
            prolific_numeric_cols = ['Time taken']
            for col in prolific_numeric_cols:
                if col in prolific_data.columns:
                    prolific_data[col] = pd.to_numeric(prolific_data[col], errors='coerce')
        
        if participant_data is None and vviq2_data is None and prolific_data is None:
            print("ERROR: No data could be loaded!")
            return 1
        
        # Create participant mapping
        participant_mapping = create_participant_mapping(participant_data, prolific_data)
        all_participants = set(participant_mapping.keys())

        print(f"\nTotal participants found: {len(all_participants)}")

        # === Calculate all exclusion criteria independently (for boolean flags) ===
        exclusion_criteria_sets = {}
        exclusion_criteria_sets['incomplete_data'] = check_incomplete_data(participant_data, vviq2_data, prolific_data)
        exclusion_criteria_sets['technical_issues'] = check_technical_issues(participant_data)
        exclusion_criteria_sets['excessive_focus_loss'] = check_excessive_focus_loss(participant_data)
        vwm_timeout_set, mrt_timeout_set = check_timeout_rates(participant_data)
        exclusion_criteria_sets['vwm_timeout_rate'] = vwm_timeout_set
        exclusion_criteria_sets['mrt_timeout_rate'] = mrt_timeout_set
        vwm_attention_set, mrt_attention_set = check_attention_check_performance(participant_data)
        exclusion_criteria_sets['vwm_attention_check_accuracy'] = vwm_attention_set
        exclusion_criteria_sets['mrt_attention_check_accuracy'] = mrt_attention_set
        exclusion_criteria_sets['vviq2_response_validity'] = check_vviq2_response_validity(vviq2_data, prolific_data)
        exclusion_criteria_sets['session_duration_outlier'] = check_session_duration_outliers(prolific_data)

        # === Cascaded exclusion for final inclusion/exclusion ===
        remaining_participants = all_participants.copy()
        participant_exclusion_reasons = {}
        exclusion_results = {}

        # 1. Incomplete data
        incomplete_data = exclusion_criteria_sets['incomplete_data'].intersection(remaining_participants)
        exclusion_results['incomplete_data'] = incomplete_data
        for p in incomplete_data:
            participant_exclusion_reasons[p] = 'incomplete_data'
        remaining_participants -= incomplete_data
        print(f"After incomplete_data exclusion: {len(remaining_participants)} participants remain")

        # 2. Technical issues
        technical_issues = exclusion_criteria_sets['technical_issues'].intersection(remaining_participants)
        exclusion_results['technical_issues'] = technical_issues
        for p in technical_issues:
            participant_exclusion_reasons[p] = 'technical_issues'
        remaining_participants -= technical_issues
        print(f"After technical_issues exclusion: {len(remaining_participants)} participants remain")

        # 3. Excessive focus loss
        excessive_focus_loss = exclusion_criteria_sets['excessive_focus_loss'].intersection(remaining_participants)
        exclusion_results['excessive_focus_loss'] = excessive_focus_loss
        for p in excessive_focus_loss:
            participant_exclusion_reasons[p] = 'excessive_focus_loss'
        remaining_participants -= excessive_focus_loss
        print(f"After excessive_focus_loss exclusion: {len(remaining_participants)} participants remain")

        # 4. Timeout rates
        vwm_timeout = exclusion_criteria_sets['vwm_timeout_rate'].intersection(remaining_participants)
        exclusion_results['vwm_timeout_rate'] = vwm_timeout
        for p in vwm_timeout:
            participant_exclusion_reasons[p] = 'vwm_timeout_rate'
        remaining_participants -= vwm_timeout
        print(f"After vwm_timeout_rate exclusion: {len(remaining_participants)} participants remain")

        mrt_timeout = exclusion_criteria_sets['mrt_timeout_rate'].intersection(remaining_participants)
        exclusion_results['mrt_timeout_rate'] = mrt_timeout
        for p in mrt_timeout:
            participant_exclusion_reasons[p] = 'mrt_timeout_rate'
        remaining_participants -= mrt_timeout
        print(f"After mrt_timeout_rate exclusion: {len(remaining_participants)} participants remain")

        # 5. Attention check performance
        vwm_attention = exclusion_criteria_sets['vwm_attention_check_accuracy'].intersection(remaining_participants)
        exclusion_results['vwm_attention_check_accuracy'] = vwm_attention
        for p in vwm_attention:
            participant_exclusion_reasons[p] = 'vwm_attention_check_accuracy'
        remaining_participants -= vwm_attention
        print(f"After vwm_attention_check_accuracy exclusion: {len(remaining_participants)} participants remain")

        mrt_attention = exclusion_criteria_sets['mrt_attention_check_accuracy'].intersection(remaining_participants)
        exclusion_results['mrt_attention_check_accuracy'] = mrt_attention
        for p in mrt_attention:
            participant_exclusion_reasons[p] = 'mrt_attention_check_accuracy'
        remaining_participants -= mrt_attention
        print(f"After mrt_attention_check_accuracy exclusion: {len(remaining_participants)} participants remain")

        # 6. VVIQ2 response validity
        vviq2_invalid = exclusion_criteria_sets['vviq2_response_validity'].intersection(remaining_participants)
        exclusion_results['vviq2_response_validity'] = vviq2_invalid
        for p in vviq2_invalid:
            participant_exclusion_reasons[p] = 'vviq2_response_validity'
        remaining_participants -= vviq2_invalid
        print(f"After vviq2_response_validity exclusion: {len(remaining_participants)} participants remain")

        # 7. Session duration outliers
        duration_outliers = exclusion_criteria_sets['session_duration_outlier'].intersection(remaining_participants)
        exclusion_results['session_duration_outlier'] = duration_outliers
        for p in duration_outliers:
            participant_exclusion_reasons[p] = 'session_duration_outlier'
        remaining_participants -= duration_outliers
        print(f"After session_duration_outlier exclusion: {len(remaining_participants)} participants remain")

        # Create exclusion status for each participant (boolean flags are based on independent sets)
        participant_status = []
        for participant in all_participants:
            exclusion_reason = participant_exclusion_reasons.get(participant, None)
            included = exclusion_reason is None

            participant_status.append({
                'participantId': participant,
                'prolific_participant_id': participant_mapping.get(participant),
                'included': included,
                'exclusion_reason': exclusion_reason,
                'incomplete_data': participant in exclusion_criteria_sets['incomplete_data'],
                'technical_issues': participant in exclusion_criteria_sets['technical_issues'],
                'excessive_focus_loss': participant in exclusion_criteria_sets['excessive_focus_loss'],
                'vwm_timeout_rate': participant in exclusion_criteria_sets['vwm_timeout_rate'],
                'mrt_timeout_rate': participant in exclusion_criteria_sets['mrt_timeout_rate'],
                'vwm_attention_check_accuracy': participant in exclusion_criteria_sets['vwm_attention_check_accuracy'],
                'mrt_attention_check_accuracy': participant in exclusion_criteria_sets['mrt_attention_check_accuracy'],
                'vviq2_response_validity': participant in exclusion_criteria_sets['vviq2_response_validity'],
                'session_duration_outlier': participant in exclusion_criteria_sets['session_duration_outlier']
            })

        # Create exclusion log
        exclusion_log = []
        total_participants = len(all_participants)

        for criterion, excluded_set in exclusion_results.items():
            count_excluded = len(excluded_set)
            percentage_excluded = (count_excluded / total_participants) * 100 if total_participants > 0 else 0

            exclusion_log.append({
                'exclusion_criteria': criterion,
                'count_excluded': count_excluded,
                'percentage_excluded': percentage_excluded
            })

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save participant exclusion status
        status_df = pd.DataFrame(participant_status)
        status_filename = f"outputs/participant_exclusion_status_{timestamp}.csv"
        status_df.to_csv(status_filename, index=False)
        print(f"\nSaved participant exclusion status to: {status_filename}")
        print("Status file columns:", list(status_df.columns))
        print("First 2 rows of status file:")
        print(status_df.head(2))

        # Save exclusion log
        log_df = pd.DataFrame(exclusion_log)
        log_filename = f"outputs/participant_exclusion_log_{timestamp}.csv"
        log_df.to_csv(log_filename, index=False)
        print(f"\nSaved exclusion log to: {log_filename}")
        print("Log file columns:", list(log_df.columns))
        print("First 2 rows of log file:")
        print(log_df.head(2))

        # Print summary
        included_count = sum(1 for p in participant_status if p['included'])
        excluded_count = total_participants - included_count

        print(f"\n=== FINAL DATA EXCLUSION SUMMARY ===")
        print(f"Data found for {total_participants} participants")
        for _, row in log_df.iterrows():
            print(f"  {row['exclusion_criteria']}: {row['count_excluded']} participants removed")
        print(f"Final dataset: {included_count} participants included")
        print(f"Total excluded: {excluded_count} participants")
        print(f"Final inclusion rate: {(included_count/total_participants)*100:.1f}%")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
