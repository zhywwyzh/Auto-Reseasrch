import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import re

def read_participant_files():
    """
    Read all participant VWM and Rotation Task CSV files from the data directory.
    
    Returns:
        pandas.DataFrame: Combined dataframe with all participant data
    """
    print("Reading participant data files...")
    
    # Find all participant files
    file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    participant_files = glob.glob(file_pattern)
    
    print(f"Found {len(participant_files)} participant files")
    
    if len(participant_files) == 0:
        print("ERROR: No participant files found")
        return None
    
    # Required columns for participant files
    required_columns = [
        'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_error_absolute_degrees',
        'VWM_pracAttempt', 'VWM_timeout', 'VWM_block', 'MRT_trial', 'MRT_isCorrect',
        'MRT_angle_degrees', 'MRT_pracAttempt', 'MRT_timeout', 'MRT_block', 'wasFullscreenExited'
    ]
    
    all_data = []
    
    for file_path in participant_files:
        print(f"Reading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print(f"File columns: {list(df.columns)}")
            print(f"First 3 rows:\n{df.head(3)}")
            
            # Check if required columns exist
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"WARNING: Missing columns in {file_path}: {missing_cols}")
                continue
            
            all_data.append(df)
            print(f"Successfully read {len(df)} rows from {file_path}")
            
        except Exception as e:
            print(f"ERROR reading {file_path}: {e}")
            continue
    
    if not all_data:
        print("ERROR: No valid participant files could be read")
        return None
    
    # Combine all participant data
    combined_data = pd.concat(all_data, ignore_index=True)
    print(f"Combined participant data shape: {combined_data.shape}")
    print(f"Combined data columns: {list(combined_data.columns)}")
    print(f"First 2 rows of combined data:\n{combined_data.head(2)}")
    
    # Print unique values for key experimental design parameters
    print("\nUnique values for key experimental design parameters:")
    if 'table' in combined_data.columns:
        print(f"table unique values: {combined_data['table'].unique()}")
        # Debugging: print all unique table values for main task identification
        print(f"DEBUG: All unique table values: {combined_data['table'].unique()}")
    if 'isPractice' in combined_data.columns:
        print(f"isPractice unique values: {combined_data['isPractice'].unique()}")
    if 'VWM_block' in combined_data.columns:
        print(f"VWM_block unique values: {combined_data['VWM_block'].unique()}")
    if 'MRT_block' in combined_data.columns:
        print(f"MRT_block unique values: {combined_data['MRT_block'].unique()}")
    if 'MRT_angle_degrees' in combined_data.columns:
        print(f"MRT_angle_degrees unique values: {combined_data['MRT_angle_degrees'].unique()}")
    if 'VWM_pracAttempt' in combined_data.columns:
        print(f"VWM_pracAttempt unique values: {combined_data['VWM_pracAttempt'].unique()}")
    if 'MRT_pracAttempt' in combined_data.columns:
        print(f"MRT_pracAttempt unique values: {combined_data['MRT_pracAttempt'].unique()}")
    
    return combined_data

def read_vviq2_file():
    """
    Read the VVIQ2 questionnaire file, skipping the junk metadata row.
    
    Returns:
        pandas.DataFrame: VVIQ2 data
    """
    print("\nReading VVIQ2 file...")
    
    vviq_file = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
    
    try:
        # Skip the second row (index 1) which contains junk data/full question text
        vviq_data = pd.read_csv(vviq_file, skiprows=[1])
        print(f"VVIQ2 file columns: {list(vviq_data.columns)}")
        print(f"VVIQ2 data shape: {vviq_data.shape}")
        print(f"First 3 rows of VVIQ2 data:\n{vviq_data.head(3)}")
        
        if 'PROLIFIC_PID' not in vviq_data.columns:
            print("ERROR: PROLIFIC_PID column not found in VVIQ2 file")
            return None
        
        # Strip whitespace for robust matching
        vviq_data['PROLIFIC_PID'] = vviq_data['PROLIFIC_PID'].str.strip()
            
        return vviq_data
        
    except Exception as e:
        print(f"ERROR reading VVIQ2 file: {e}")
        return None

def read_prolific_file():
    """
    Read the Prolific export file.
    
    Returns:
        pandas.DataFrame: Prolific data
    """
    print("\nReading Prolific export file...")
    
    # Find prolific export file
    prolific_pattern = "../C_results/data/prolific_export_*.csv"
    prolific_files = glob.glob(prolific_pattern)
    
    if len(prolific_files) == 0:
        print("ERROR: No Prolific export files found")
        return None
    
    # Use most recent file if multiple exist
    prolific_file = max(prolific_files, key=os.path.getctime)
    print(f"Using Prolific file: {prolific_file}")
    
    try:
        prolific_data = pd.read_csv(prolific_file)
        # Strip whitespace for robust matching
        if 'Participant id' in prolific_data.columns:
            prolific_data['Participant id'] = prolific_data['Participant id'].str.strip()
        print(f"Prolific file columns: {list(prolific_data.columns)}")
        print(f"Prolific data shape: {prolific_data.shape}")
        print(f"First 3 rows of Prolific data:\n{prolific_data.head(3)}")
        
        required_cols = ['Participant id', 'Status']
        missing_cols = [col for col in required_cols if col not in prolific_data.columns]
        if missing_cols:
            print(f"ERROR: Missing required columns in Prolific file: {missing_cols}")
            return None
            
        print(f"Prolific Status unique values: {prolific_data['Status'].unique()}")
        
        return prolific_data
        
    except Exception as e:
        print(f"ERROR reading Prolific file: {e}")
        return None

def apply_prolific_exclusions(participant_data, prolific_data):
    """
    Apply Prolific completion status exclusions.
    
    Args:
        participant_data (pandas.DataFrame): Combined participant data
        prolific_data (pandas.DataFrame): Prolific export data
        
    Returns:
        tuple: (filtered_data, exclusion_count)
    """
    print("\nApplying Prolific completion status exclusions...")
    
    initial_participants = participant_data['participantId'].nunique()
    print(f"Initial participants: {initial_participants}")
    
    # Merge with Prolific data
    merged_data = participant_data.merge(
        prolific_data[['Participant id', 'Status']], 
        left_on='participantId', 
        right_on='Participant id', 
        how='left'
    )
    
    print(f"Participants with Prolific data: {merged_data['Status'].notna().sum()}")
    print(f"Status distribution: {merged_data['Status'].value_counts()}")
    
    # Keep only APPROVED participants
    approved_data = merged_data[merged_data['Status'] == 'APPROVED']
    final_participants = approved_data['participantId'].nunique()
    
    exclusions = initial_participants - final_participants
    print(f"Excluded {exclusions} participants due to Prolific status")
    print(f"Remaining participants: {final_participants}")
    
    return approved_data, exclusions

def apply_vwm_practice_exclusions(data):
    """
    Apply VWM practice performance exclusions.
    
    Args:
        data (pandas.DataFrame): Participant data
        
    Returns:
        tuple: (filtered_data, exclusion_count)
    """
    print("\nApplying VWM practice performance exclusions...")
    
    initial_participants = data['participantId'].nunique()
    
    # Identify VWM practice trials
    vwm_practice = data[
        (data['isPractice'] == True) & 
        (data['table'] == 'vwm_practice')
    ].copy()
    
    print(f"VWM practice trials found: {len(vwm_practice)}")
    
    if len(vwm_practice) == 0:
        print("No VWM practice trials found - no exclusions applied")
        return data, 0
    
    excluded_participants = set()
    
    # For each participant, check final practice attempt performance
    for participant in vwm_practice['participantId'].unique():
        participant_practice = vwm_practice[vwm_practice['participantId'] == participant]
        
        # Get final attempt (highest VWM_pracAttempt value)
        max_attempt = participant_practice['VWM_pracAttempt'].max()
        final_attempt = participant_practice[participant_practice['VWM_pracAttempt'] == max_attempt]
        
        # Calculate mean absolute error for final attempt
        if len(final_attempt) > 0:
            mean_error = final_attempt['VWM_error_absolute_degrees'].mean()
            
            # Exclude if mean error >= 30 degrees after max 3 attempts
            if pd.notna(mean_error) and mean_error >= 30 and max_attempt >= 3:
                excluded_participants.add(participant)
                print(f"Excluding participant {participant}: VWM practice mean error {mean_error:.2f} degrees after {max_attempt} attempts")
    
    # Filter out excluded participants
    filtered_data = data[~data['participantId'].isin(excluded_participants)]
    
    exclusions = len(excluded_participants)
    final_participants = filtered_data['participantId'].nunique()
    
    print(f"Excluded {exclusions} participants due to VWM practice performance")
    print(f"Remaining participants: {final_participants}")
    
    return filtered_data, exclusions

def apply_mrt_practice_exclusions(data):
    """
    Apply MRT practice performance exclusions.
    
    Args:
        data (pandas.DataFrame): Participant data
        
    Returns:
        tuple: (filtered_data, exclusion_count)
    """
    print("\nApplying MRT practice performance exclusions...")
    
    initial_participants = data['participantId'].nunique()
    
    # Identify MRT practice trials
    mrt_practice = data[
        (data['isPractice'] == True) & 
        (data['table'] == 'mrt_practice')
    ].copy()
    
    print(f"MRT practice trials found: {len(mrt_practice)}")
    
    if len(mrt_practice) == 0:
        print("No MRT practice trials found - no exclusions applied")
        return data, 0
    
    excluded_participants = set()
    
    # For each participant, check final practice attempt performance
    for participant in mrt_practice['participantId'].unique():
        participant_practice = mrt_practice[mrt_practice['participantId'] == participant]
        
        # Get final attempt (highest MRT_pracAttempt value)
        max_attempt = participant_practice['MRT_pracAttempt'].max()
        final_attempt = participant_practice[participant_practice['MRT_pracAttempt'] == max_attempt]
        
        # Calculate accuracy for final attempt
        if len(final_attempt) > 0:
            accuracy = final_attempt['MRT_isCorrect'].mean()
            
            # Exclude if accuracy < 8/12 after max 3 attempts
            if pd.notna(accuracy) and accuracy < (8/12) and max_attempt >= 3:
                excluded_participants.add(participant)
                print(f"Excluding participant {participant}: MRT practice accuracy {accuracy:.3f} after {max_attempt} attempts")
    
    # Filter out excluded participants
    filtered_data = data[~data['participantId'].isin(excluded_participants)]
    
    exclusions = len(excluded_participants)
    final_participants = filtered_data['participantId'].nunique()
    
    print(f"Excluded {exclusions} participants due to MRT practice performance")
    print(f"Remaining participants: {final_participants}")
    
    return filtered_data, exclusions

def apply_timeout_exclusions(data):
    """
    Apply main task engagement exclusions based on timeout rates.
    
    Args:
        data (pandas.DataFrame): Participant data
        
    Returns:
        tuple: (filtered_data, exclusion_count)
    """
    print("\nApplying timeout rate exclusions...")
    
    initial_participants = data['participantId'].nunique()
    excluded_participants = set()
    
    # Check VWM timeout rates
    vwm_main = data[
        (data['isPractice'] == False) & 
        (data['table'] == 'vwm_test')
    ].copy()
    
    print(f"VWM main task trials found: {len(vwm_main)}")
    
    if len(vwm_main) > 0:
        for participant in vwm_main['participantId'].unique():
            participant_vwm = vwm_main[vwm_main['participantId'] == participant]
            timeout_rate = participant_vwm['VWM_timeout'].mean()
            
            if pd.notna(timeout_rate) and timeout_rate > 0.20:
                excluded_participants.add(participant)
                print(f"Excluding participant {participant}: VWM timeout rate {timeout_rate:.3f}")
    
    # Check MRT timeout rates
    mrt_main = data[
        (data['isPractice'] == False) & 
        (data['table'] == 'mrt_test')
    ].copy()
    
    print(f"MRT main task trials found: {len(mrt_main)}")
    
    if len(mrt_main) > 0:
        for participant in mrt_main['participantId'].unique():
            participant_mrt = mrt_main[mrt_main['participantId'] == participant]
            timeout_rate = participant_mrt['MRT_timeout'].mean()
            
            if pd.notna(timeout_rate) and timeout_rate > 0.20:
                excluded_participants.add(participant)
                print(f"Excluding participant {participant}: MRT timeout rate {timeout_rate:.3f}")
    
    # Filter out excluded participants
    filtered_data = data[~data['participantId'].isin(excluded_participants)]
    
    exclusions = len(excluded_participants)
    final_participants = filtered_data['participantId'].nunique()
    
    print(f"Excluded {exclusions} participants due to timeout rates")
    print(f"Remaining participants: {final_participants}")
    
    return filtered_data, exclusions

def apply_mrt_zero_degree_exclusions(data):
    """
    Apply MRT 0-degree performance exclusions.
    
    Args:
        data (pandas.DataFrame): Participant data
        
    Returns:
        tuple: (filtered_data, exclusion_count)
    """
    print("\nApplying MRT 0-degree performance exclusions...")
    
    initial_participants = data['participantId'].nunique()
    
    # Identify MRT main task 0-degree trials
    mrt_zero_degree = data[
        (data['isPractice'] == False) & 
        (data['table'] == 'mrt_test') &
        (data['MRT_angle_degrees'] == 0)
    ].copy()
    
    print(f"MRT 0-degree trials found: {len(mrt_zero_degree)}")
    
    if len(mrt_zero_degree) == 0:
        print("No MRT 0-degree trials found - no exclusions applied")
        return data, 0
    
    excluded_participants = set()
    
    # For each participant, check 0-degree performance
    for participant in mrt_zero_degree['participantId'].unique():
        participant_zero = mrt_zero_degree[mrt_zero_degree['participantId'] == participant]
        
        # Calculate accuracy on 0-degree trials
        accuracy = participant_zero['MRT_isCorrect'].mean()
        
        # Exclude if accuracy < 70%
        if pd.notna(accuracy) and accuracy < 0.70:
            excluded_participants.add(participant)
            print(f"Excluding participant {participant}: MRT 0-degree accuracy {accuracy:.3f}")
    
    # Filter out excluded participants
    filtered_data = data[~data['participantId'].isin(excluded_participants)]
    
    exclusions = len(excluded_participants)
    final_participants = filtered_data['participantId'].nunique()
    
    print(f"Excluded {exclusions} participants due to MRT 0-degree performance")
    print(f"Remaining participants: {final_participants}")
    
    return filtered_data, exclusions

def apply_technical_exclusions(data, vviq_data):
    """
    Apply technical and completion exclusions.
    
    Args:
        data (pandas.DataFrame): Participant data
        vviq_data (pandas.DataFrame): VVIQ2 data
        
    Returns:
        tuple: (filtered_data, exclusion_count)
    """
    print("\nApplying technical and completion exclusions...")
    
    initial_participants = data['participantId'].nunique()
    excluded_participants = set()
    
    # Check for missing task data
    participant_tasks = {}
    
    for participant in data['participantId'].unique():
        participant_data = data[data['participantId'] == participant]
        
        has_vwm = len(participant_data[participant_data['table'].str.contains('vwm', na=False)]) > 0
        has_mrt = len(participant_data[participant_data['table'].str.contains('mrt', na=False)]) > 0
        has_vviq = participant in vviq_data['PROLIFIC_PID'].values
        
        participant_tasks[participant] = {
            'vwm': has_vwm,
            'mrt': has_mrt, 
            'vviq': has_vviq
        }
        
        if not (has_vwm and has_mrt and has_vviq):
            excluded_participants.add(participant)
            missing = [task for task, present in participant_tasks[participant].items() if not present]
            print(f"Excluding participant {participant}: Missing data for {missing}")
    
    # Check fullscreen exits
    for participant in data['participantId'].unique():
        if participant in excluded_participants:
            continue
            
        participant_data = data[data['participantId'] == participant]
        fullscreen_exits = participant_data['wasFullscreenExited'].sum()
        
        if pd.notna(fullscreen_exits) and fullscreen_exits > 3:
            excluded_participants.add(participant)
            print(f"Excluding participant {participant}: {fullscreen_exits} fullscreen exits")
    
    # Filter out excluded participants
    filtered_data = data[~data['participantId'].isin(excluded_participants)]
    
    exclusions = len(excluded_participants)
    final_participants = filtered_data['participantId'].nunique()
    
    print(f"Excluded {exclusions} participants due to technical/completion issues")
    print(f"Remaining participants: {final_participants}")
    
    return filtered_data, exclusions

def apply_vviq2_exclusions(data, vviq_data, prolific_data):
    """
    Apply VVIQ2 quality exclusions.

    Args:
        data (pandas.DataFrame): Participant data
        vviq_data (pandas.DataFrame): VVIQ2 data
        prolific_data (pandas.DataFrame): Prolific export data

    Returns:
        tuple: (filtered_data, exclusion_count, excluded_participants_set)
    """
    print("\nApplying VVIQ2 quality exclusions...")

    initial_participants = data['participantId'].nunique()
    excluded_participants = set()

    # Define metadata columns to exclude from response columns
    vviq_metadata_cols = [
        'Respondent ID', 'Collector ID', 'Start Date', 'End Date', 'IP Address',
        'Email Address', 'First Name', 'Last Name', 'Custom Data 1', 'PROLIFIC_PID'
    ]
    response_columns = [col for col in vviq_data.columns if col not in vviq_metadata_cols]
    print(f"VVIQ2 response columns found: {len(response_columns)}")
    print(f"VVIQ2 response columns: {response_columns}")

    # Add this debugging after response_columns are defined
    print(f"DEBUG: Sample VVIQ2 data for first participant:")
    first_participant = list(data['participantId'].unique())[0]
    if first_participant in vviq_data['PROLIFIC_PID'].values:
        sample_vviq = vviq_data[vviq_data['PROLIFIC_PID'] == first_participant]
        for i, col in enumerate(response_columns[:5]):  # Show first 5 columns
            response = sample_vviq[col].iloc[0]
            print(f"  {col}: '{response}' (type: {type(response)})")

    # Merge VVIQ2 with prolific data to get completion times
    vviq_merged = vviq_data.merge(prolific_data, left_on='PROLIFIC_PID', right_on='Participant id', how='left')
    if 'Duration (in seconds)' in vviq_merged.columns:
        vviq_merged['duration_minutes'] = vviq_merged['Duration (in seconds)'] / 60.0
    else:
        vviq_merged['duration_minutes'] = np.nan

    for participant in data['participantId'].unique():
        if participant not in vviq_data['PROLIFIC_PID'].values:
            continue

        participant_vviq = vviq_data[vviq_data['PROLIFIC_PID'] == participant]
        participant_vviq_merged = vviq_merged[vviq_merged['PROLIFIC_PID'] == participant]

        if len(participant_vviq) == 0:
            continue

        # Extract numeric scores from response strings
        numeric_scores = []
        missing_count = 0

        for col in response_columns:
            response = participant_vviq[col].iloc[0]

            if pd.isna(response) or str(response).strip() == '':
                missing_count += 1
                continue

            # Convert to string and try multiple extraction methods
            response_str = str(response).strip()
            
            # Try direct numeric conversion first
            try:
                if response_str.isdigit() and 1 <= int(response_str) <= 5:
                    numeric_scores.append(int(response_str))
                    continue
            except (ValueError, TypeError):
                pass
            
            # Try regex pattern matching for single digits
            if re.match(r'^[1-5]$', response_str):
                numeric_scores.append(int(response_str))
                continue
            
            # Try extracting number from end of string (original logic)
            try:
                if isinstance(response, (int, float)) and 1 <= response <= 5:
                    numeric_scores.append(int(response))
                elif isinstance(response, str):
                    match = re.search(r'(\d+)$', response.strip())
                    if match and 1 <= int(match.group(1)) <= 5:
                        numeric_scores.append(int(match.group(1)))
                    else:
                        missing_count += 1
                else:
                    missing_count += 1
            except (ValueError, TypeError):
                missing_count += 1

        # Check missing responses (>10% = >3.2 items)
        missing_percentage = missing_count / len(response_columns)
        if missing_percentage > 0.10:
            excluded_participants.add(participant)
            print(f"Excluding participant {participant}: {missing_percentage:.1%} missing VVIQ2 responses")
            continue

        # Check identical ratings (>80% identical AND completion time <5 minutes)
        identical_percentage = 0
        if len(numeric_scores) > 0:
            most_common_score = max(set(numeric_scores), key=numeric_scores.count)
            identical_percentage = numeric_scores.count(most_common_score) / len(numeric_scores)

        # Get completion time in minutes using 'Time taken' column from Prolific
        time_taken_sec = participant_vviq_merged['Time taken'].iloc[0] if 'Time taken' in participant_vviq_merged.columns else None
        completion_time_min = time_taken_sec / 60 if pd.notna(time_taken_sec) else None

        if identical_percentage > 0.80 and (completion_time_min is not None and completion_time_min < 5):
            excluded_participants.add(participant)
            print(f"Excluding participant {participant}: {identical_percentage:.1%} identical VVIQ2 ratings and completion time {completion_time_min:.2f} min")

    # Filter out excluded participants
    filtered_data = data[~data['participantId'].isin(excluded_participants)]

    exclusions = len(excluded_participants)
    final_participants = filtered_data['participantId'].nunique()

    print(f"Excluded {exclusions} participants due to VVIQ2 quality issues")
    print(f"Remaining participants: {final_participants}")

    return filtered_data, exclusions, excluded_participants

def create_exclusion_summary(exclusion_counts, final_count):
    """
    Create exclusion summary log.
    
    Args:
        exclusion_counts (dict): Dictionary of exclusion criteria and counts
        final_count (int): Final sample size
        
    Returns:
        pandas.DataFrame: Exclusion summary
    """
    print("\nCreating exclusion summary...")
    
    summary_data = []
    running_count = exclusion_counts.get('initial', 0)
    
    for criterion, excluded in exclusion_counts.items():
        if criterion == 'initial':
            continue
            
        summary_data.append({
            'exclusion_criterion': criterion,
            'excluded_count': excluded,
            'remaining_count': running_count - excluded
        })
        running_count -= excluded
    
    summary_df = pd.DataFrame(summary_data)
    
    print("Exclusion Summary:")
    print(summary_df)
    
    return summary_df

def create_participant_summary(data, excluded_participants_by_reason, all_participants):
    """
    Create retained participants summary.
    
    Args:
        data (pandas.DataFrame): Final filtered data
        excluded_participants_by_reason (dict): Dictionary mapping participants to exclusion reasons
        all_participants (set): Set of all initial participant IDs
        
    Returns:
        pandas.DataFrame: Participant summary
    """
    print("\nCreating participant summary...")
    
    retained_ids = set(data['participantId'].unique())
    participant_summary = []
    
    for participant in all_participants:
        included = participant in retained_ids
        
        if included:
            exclusion_reason = None
        else:
            # Find exclusion reason
            exclusion_reason = None
            for reason, excluded_list in excluded_participants_by_reason.items():
                if participant in excluded_list:
                    exclusion_reason = reason
                    break
            if exclusion_reason is None:
                exclusion_reason = "unknown"
        
        participant_summary.append({
            'participantId': participant,
            'included': included,
            'exclusion_reason': exclusion_reason
        })
    
    summary_df = pd.DataFrame(participant_summary)
    
    print(f"Total participants processed: {len(summary_df)}")
    print(f"Included participants: {summary_df['included'].sum()}")
    print(f"Excluded participants: {(~summary_df['included']).sum()}")
    
    return summary_df

def main():
    """
    Main function to execute participant exclusion analysis.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting participant exclusion analysis...")
        
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Read input files
        participant_data = read_participant_files()
        if participant_data is None:
            print("ERROR: Failed to read participant data")
            return 1
        
        vviq_data = read_vviq2_file()
        if vviq_data is None:
            print("ERROR: Failed to read VVIQ2 data")
            return 1
        
        prolific_data = read_prolific_file()
        if prolific_data is None:
            print("ERROR: Failed to read Prolific data")
            return 1

        # Print unique table values for debugging main task identification
        if 'table' in participant_data.columns:
            print(f"DEBUG: All unique table values in participant_data: {participant_data['table'].unique()}")

        # Track exclusions
        exclusion_counts = {'initial': participant_data['participantId'].nunique()}
        excluded_by_reason = {}

        # Capture all initial participants
        all_initial_participants = set(participant_data['participantId'].unique())

        # Apply exclusions sequentially
        print(f"\nStarting with {exclusion_counts['initial']} participants")

        # 1. Prolific status exclusions
        current_data, excluded = apply_prolific_exclusions(participant_data, prolific_data)
        exclusion_counts['prolific_status'] = excluded
        excluded_by_reason['prolific_status'] = set(participant_data['participantId'].unique()) - set(current_data['participantId'].unique())

        # 2. VWM practice exclusions
        prev_ids = set(current_data['participantId'].unique())
        current_data, excluded = apply_vwm_practice_exclusions(current_data)
        exclusion_counts['vwm_practice'] = excluded
        excluded_by_reason['vwm_practice'] = prev_ids - set(current_data['participantId'].unique())

        # 3. MRT practice exclusions
        prev_ids = set(current_data['participantId'].unique())
        current_data, excluded = apply_mrt_practice_exclusions(current_data)
        exclusion_counts['mrt_practice'] = excluded
        excluded_by_reason['mrt_practice'] = prev_ids - set(current_data['participantId'].unique())

        # 4. Timeout exclusions
        prev_ids = set(current_data['participantId'].unique())
        current_data, excluded = apply_timeout_exclusions(current_data)
        exclusion_counts['timeout_rates'] = excluded
        excluded_by_reason['timeout_rates'] = prev_ids - set(current_data['participantId'].unique())

        # 5. MRT 0-degree exclusions
        prev_ids = set(current_data['participantId'].unique())
        current_data, excluded = apply_mrt_zero_degree_exclusions(current_data)
        exclusion_counts['mrt_zero_degree'] = excluded
        excluded_by_reason['mrt_zero_degree'] = prev_ids - set(current_data['participantId'].unique())

        # 6. Technical exclusions
        prev_ids = set(current_data['participantId'].unique())
        current_data, excluded = apply_technical_exclusions(current_data, vviq_data)
        exclusion_counts['technical_completion'] = excluded
        excluded_by_reason['technical_completion'] = prev_ids - set(current_data['participantId'].unique())

        # 7. VVIQ2 exclusions
        prev_ids = set(current_data['participantId'].unique())
        current_data, excluded, vviq2_excluded_set = apply_vviq2_exclusions(current_data, vviq_data, prolific_data)
        exclusion_counts['vviq2_quality'] = excluded
        excluded_by_reason['vviq2_quality'] = vviq2_excluded_set

        final_count = current_data['participantId'].nunique()
        print(f"\nFinal sample size: {final_count} participants")

        # Create output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Exclusion summary
        exclusion_summary = create_exclusion_summary(exclusion_counts, final_count)
        exclusion_file = f"outputs/participant_exclusion_log_{timestamp}.csv"
        exclusion_summary.to_csv(exclusion_file, index=False)
        print(f"Exclusion summary saved to: {exclusion_file}")

        # Participant summary
        participant_summary = create_participant_summary(current_data, excluded_by_reason, all_initial_participants)
        participant_file = f"outputs/retained_participants_{timestamp}.csv"
        participant_summary.to_csv(participant_file, index=False)
        print(f"Participant summary saved to: {participant_file}")

        print(f"\n=== FINAL EXCLUSION SUMMARY ===")
        print(f"Initial participants: {exclusion_counts['initial']}")
        for criterion, count in exclusion_counts.items():
            if criterion != 'initial':
                print(f"Excluded for {criterion}: {count}")
        print(f"Final retained participants: {final_count}")
        print(f"Total exclusion rate: {((exclusion_counts['initial'] - final_count) / exclusion_counts['initial'] * 100):.1f}%")

        print("Finished execution")
        return 0

    except Exception as e:
        print(f"ERROR in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
