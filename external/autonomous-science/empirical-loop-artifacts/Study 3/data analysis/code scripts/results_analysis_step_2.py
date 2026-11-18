import pandas as pd
import numpy as np
import glob
import os
import re
from datetime import datetime

def load_task_data():
    """
    Load all task data files matching the pattern PARTICIPANT_*_VWM_and_Rotation_Task_*.csv
    
    Returns:
        pd.DataFrame: Combined task data from all participants
    """
    print("Loading task data files...")
    
    # Find all matching task data files
    task_files = glob.glob('raw_data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv')
    print(f"Found {len(task_files)} task data files")
    
    if not task_files:
        print("ERROR: No task data files found!")
        return None
    
    all_task_data = []
    
    for file in task_files:
        print(f"Loading: {file}")
        try:
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            print(f"  Columns: {list(df.columns)}")
            print(f"  Shape: {df.shape}")
            print(f"  First 3 rows:")
            print(df.head(3))
            all_task_data.append(df)
        except Exception as e:
            print(f"  ERROR loading {file}: {e}")
            continue
    
    if not all_task_data:
        print("ERROR: No task data files could be loaded!")
        return None
    
    # Combine all task data
    combined_task_data = pd.concat(all_task_data, ignore_index=True)
    print(f"\nCombined task data shape: {combined_task_data.shape}")
    print(f"Combined task data columns: {list(combined_task_data.columns)}")
    print(f"First 2 rows of combined data:")
    print(combined_task_data.head(2))
    
    return combined_task_data

def load_vviq_data():
    """
    Load VVIQ2 questionnaire data
    
    Returns:
        pd.DataFrame: VVIQ2 data
    """
    print("\nLoading VVIQ2 data...")
    
    vviq_file = 'raw_data/Vividness of Visual Imagery Questionnaire-2.csv'
    
    try:
        vviq_data = pd.read_csv(vviq_file)
        vviq_data.columns = vviq_data.columns.str.strip()
        vviq_data.rename(columns={'PROLIFIC_PID': 'participantId'}, inplace=True)
        print(f"VVIQ2 data shape: {vviq_data.shape}")
        print(f"VVIQ2 data columns: {list(vviq_data.columns)}")
        print(f"First 3 rows of VVIQ2 data:")
        print(vviq_data.head(3))
        return vviq_data
    except Exception as e:
        print(f"ERROR loading VVIQ2 data: {e}")
        return None

def load_prolific_data():
    """
    Load prolific export data
    
    Returns:
        pd.DataFrame: Prolific export data
    """
    print("\nLoading prolific export data...")
    
    # Find prolific export files
    prolific_files = glob.glob('raw_data/prolific_export_*.csv')
    print(f"Found {len(prolific_files)} prolific export files")
    
    if not prolific_files:
        print("ERROR: No prolific export files found!")
        return None
    
    # Use the most recent file if multiple exist
    if len(prolific_files) > 1:
        prolific_files.sort(key=os.path.getmtime, reverse=True)
        print(f"Using most recent file: {prolific_files[0]}")
    
    try:
        prolific_data = pd.read_csv(prolific_files[0])
        prolific_data.columns = prolific_data.columns.str.strip()
        prolific_data.rename(columns={'Participant id': 'participantId'}, inplace=True)
        print(f"Prolific data shape: {prolific_data.shape}")
        print(f"Prolific data columns: {list(prolific_data.columns)}")
        print(f"First 3 rows of prolific data:")
        print(prolific_data.head(3))
        return prolific_data
    except Exception as e:
        print(f"ERROR loading prolific data: {e}")
        return None

def merge_datasets(task_data, vviq_data, prolific_data):
    """
    Merge task, VVIQ, and prolific datasets

    Args:
        task_data (pd.DataFrame): Task performance data
        vviq_data (pd.DataFrame): VVIQ2 questionnaire data
        prolific_data (pd.DataFrame): Prolific export data

    Returns:
        pd.DataFrame: Merged dataset
    """
    print("\nMerging datasets...")

    # Start with task data
    merged_data = task_data.copy()
    print(f"Starting with task data: {merged_data.shape}")

    # Merge with VVIQ data
    if vviq_data is not None:
        merged_data = merged_data.merge(vviq_data, on='participantId', how='left', suffixes=('', '_vviq'))
        print(f"After merging VVIQ data: {merged_data.shape}")

    # Merge with prolific data
    if prolific_data is not None:
        merged_data = merged_data.merge(prolific_data, on='participantId', how='left', suffixes=('', '_prolific'))
        print(f"After merging prolific data: {merged_data.shape}")

    # Remove duplicate columns if any (from merge suffixes)
    merged_data = merged_data.loc[:, ~merged_data.columns.duplicated()]

    print(f"Final merged data columns: {list(merged_data.columns)}")
    print(f"First 2 rows of merged data:")
    print(merged_data.head(2))

    return merged_data

def print_experimental_design_parameters(data):
    """
    Print unique values for key experimental design parameters
    
    Args:
        data (pd.DataFrame): Dataset to analyze
    """
    print("\n=== EXPERIMENTAL DESIGN PARAMETERS ===")
    
    # VWM parameters
    if 'VWM_setSize' in data.columns:
        print(f"VWM_setSize unique values: {sorted(data['VWM_setSize'].dropna().unique())}")
    
    if 'VWM_delay_s' in data.columns:
        print(f"VWM_delay_s unique values: {sorted(data['VWM_delay_s'].dropna().unique())}")
    
    if 'VWM_block' in data.columns:
        print(f"VWM_block unique values: {sorted(data['VWM_block'].dropna().unique())}")
    
    if 'VWM_isAttentionCheck' in data.columns:
        print(f"VWM_isAttentionCheck unique values: {sorted(data['VWM_isAttentionCheck'].dropna().unique())}")
    
    # MRT parameters
    if 'MRT_angle_degrees' in data.columns:
        print(f"MRT_angle_degrees unique values: {sorted(data['MRT_angle_degrees'].dropna().unique())}")
    
    if 'MRT_isReflected' in data.columns:
        print(f"MRT_isReflected unique values: {sorted(data['MRT_isReflected'].dropna().unique())}")
    
    if 'MRT_block' in data.columns:
        print(f"MRT_block unique values: {sorted(data['MRT_block'].dropna().unique())}")
    
    if 'MRT_isAttentionCheck' in data.columns:
        print(f"MRT_isAttentionCheck unique values: {sorted(data['MRT_isAttentionCheck'].dropna().unique())}")
    
    # General parameters
    if 'isPractice' in data.columns:
        print(f"isPractice unique values: {sorted(data['isPractice'].dropna().unique())}")
    
    if 'taskOrder' in data.columns:
        print(f"taskOrder unique values: {sorted(data['taskOrder'].dropna().unique())}")
    
    # Print data types for measured variables
    print("\n=== MEASURED VARIABLE TYPES ===")
    measured_vars = ['VWM_rt_ms', 'VWM_error_degrees', 'VWM_error_absolute_degrees', 
                    'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees',
                    'MRT_rt_ms', 'Time taken']
    
    for var in measured_vars:
        if var in data.columns:
            print(f"{var}: {data[var].dtype}")

def apply_exclusion_criteria(data):
    """
    Apply all exclusion criteria in sequence

    Args:
        data (pd.DataFrame): Merged dataset

    Returns:
        tuple: (retained_data, exclusion_log)
    """
    print("\n=== APPLYING EXCLUSION CRITERIA ===")

    # Sanitize column names
    data.columns = data.columns.str.strip()

    exclusion_log = []
    initial_participants = data['participantId'].nunique()
    print(f"Initial number of participants: {initial_participants}")

    # Get all unique participants
    all_participants = set(data['participantId'].unique())
    excluded_participants = set()

    # a. VWM Practice Performance
    print("\n1. VWM Practice Performance...")
    vwm_practice = data[(data['isPractice'] == True) & (data['VWM_trial'].notna())]
    print(f"  VWM practice trials: {len(vwm_practice)}")
    vwm_practice_excluded = set()
    for participant in all_participants:
        if participant in excluded_participants:
            continue
            
        p_data = vwm_practice[vwm_practice['participantId'] == participant]
        if len(p_data) == 0:
            continue
            
        max_attempt = p_data['VWM_pracAttempt'].max()
        if pd.isna(max_attempt):
            continue
            
        final_attempt_data = p_data[p_data['VWM_pracAttempt'] == max_attempt]
        if len(final_attempt_data) == 0:
            continue
            
        mean_error = final_attempt_data['VWM_error_absolute_degrees'].mean()
        if pd.isna(mean_error):
            continue
            
        if mean_error > 30 and max_attempt >= 3:
            print(f"    Participant {participant}: mean error = {mean_error:.2f} (excluded)")
            vwm_practice_excluded.add(participant)
        else:
            print(f"    Participant {participant}: mean error = {mean_error:.2f} (retained)")
    excluded_participants.update(vwm_practice_excluded)
    exclusion_log.append(('VWM Practice Performance', len(vwm_practice_excluded), initial_participants - len(excluded_participants)))
    print(f"  Excluded {len(vwm_practice_excluded)} participants for VWM practice performance")
    print(f"  Remaining participants: {initial_participants - len(excluded_participants)}")
    
    # b. MRT Practice Performance
    print("\n2. MRT Practice Performance...")
    mrt_practice = data[(data['isPractice'] == True) & (data['MRT_trial'].notna())]
    print(f"  MRT practice trials: {len(mrt_practice)}")
    mrt_practice_excluded = set()
    for participant in all_participants:
        if participant in excluded_participants:
            continue
            
        p_data = mrt_practice[mrt_practice['participantId'] == participant]
        if len(p_data) == 0:
            continue
            
        max_attempt = p_data['MRT_pracAttempt'].max()
        if pd.isna(max_attempt):
            continue
            
        final_attempt_data = p_data[p_data['MRT_pracAttempt'] == max_attempt]
        if len(final_attempt_data) == 0:
            continue
            
        accuracy = final_attempt_data['MRT_isCorrect'].mean()
        if pd.isna(accuracy):
            continue
            
        if accuracy < (8/12) and max_attempt >= 3:
            print(f"    Participant {participant}: accuracy = {accuracy:.2f} (excluded)")
            mrt_practice_excluded.add(participant)
        else:
            print(f"    Participant {participant}: accuracy = {accuracy:.2f} (retained)")
    excluded_participants.update(mrt_practice_excluded)
    exclusion_log.append(('MRT Practice Performance', len(mrt_practice_excluded), initial_participants - len(excluded_participants)))
    print(f"  Excluded {len(mrt_practice_excluded)} participants for MRT practice performance")
    print(f"  Remaining participants: {initial_participants - len(excluded_participants)}")
    
    # c. Timeout Rate
    print("\n3. Timeout Rate...")
    main_task_data = data[data['isPractice'] == False]
    timeout_excluded = set()
    for participant in all_participants:
        if participant in excluded_participants:
            continue
            
        p_data = main_task_data[main_task_data['participantId'] == participant]
        if len(p_data) == 0:
            continue
            
        # VWM timeout rate
        vwm_data = p_data[p_data['VWM_trial'].notna()]
        if len(vwm_data) > 0:
            vwm_timeout_rate = vwm_data['VWM_timeout'].mean()
            if pd.notna(vwm_timeout_rate) and vwm_timeout_rate > 0.2:
                print(f"    Participant {participant}: VWM timeout rate = {vwm_timeout_rate:.2f} (excluded)")
                timeout_excluded.add(participant)
                continue
        
        # MRT timeout rate
        mrt_data = p_data[p_data['MRT_trial'].notna()]
        if len(mrt_data) > 0:
            mrt_timeout_rate = mrt_data['MRT_timeout'].mean()
            if pd.notna(mrt_timeout_rate) and mrt_timeout_rate > 0.2:
                print(f"    Participant {participant}: MRT timeout rate = {mrt_timeout_rate:.2f} (excluded)")
                timeout_excluded.add(participant)
    excluded_participants.update(timeout_excluded)
    exclusion_log.append(('Timeout Rate', len(timeout_excluded), initial_participants - len(excluded_participants)))
    print(f"  Excluded {len(timeout_excluded)} participants for timeout rate")
    print(f"  Remaining participants: {initial_participants - len(excluded_participants)}")
    
    # d. MRT Engagement
    print("\n4. MRT Engagement...")
    mrt_zero_rotation = data[(data['isPractice'] == False) & (data['MRT_angle_degrees'] == 0)]
    print(f"MRT 0° rotation trials: {len(mrt_zero_rotation)}")
    
    mrt_engagement_excluded = set()
    print("  Checking MRT engagement for each participant...")
    for participant in all_participants:
        if participant in excluded_participants:
            continue
            
        p_data = mrt_zero_rotation[mrt_zero_rotation['participantId'] == participant]
        if len(p_data) == 0:
            print(f"    Participant {participant}: no 0° MRT trials found")
            continue
            
        accuracy = p_data['MRT_isCorrect'].mean()
        if pd.isna(accuracy):
            print(f"    Participant {participant}: accuracy is NaN")
            continue
            
        if accuracy < 0.65:
            print(f"  Participant {participant}: accuracy = {accuracy:.3f} (excluded)")
            mrt_engagement_excluded.add(participant)
        else:
            print(f"  Participant {participant}: accuracy = {accuracy:.3f} (retained)")
    
    excluded_participants.update(mrt_engagement_excluded)
    exclusion_log.append(('MRT Engagement', len(mrt_engagement_excluded), initial_participants - len(excluded_participants)))
    print(f"Excluded {len(mrt_engagement_excluded)} participants for MRT engagement")
    
    # e. VVIQ2 Completion
    print("\n5. VVIQ2 Completion...")

    vviq_columns = [
        "The exact contour of face, head, shoulders and body.",
        "Characteristic poses of head, attitudes of body etc.",
        "The precise carriage, length of step, etc. in walking.",
        "The different colours worn in some familiar clothes.",
        "The sun is rising above the horizon into a hazy sky.",
        "The sky clears and surrounds the sun with blueness.",
        "Clouds. A storm blows up, with flashes of lightening.",
        "A rainbow appears.",
        "The overall appearance of the shop from the opposite side of the road.",
        "A window display including colours, shape and details of individual items for sale.",
        "You are near the entrance. The colour, shape and details of the door.",
        "You enter the shop and go to the counter. The counter assistant serves you. Money changes hands.",
        "The contours of the landscape.",
        "The colour and shape of the trees.",
        "The colour and shape of the lake.",
        "A strong wind blows on the tree and on the lake causing waves.",
        "You observe the heavy traffic travelling at maximum speed around your car. The overall appearance of vehicles, their colours, sizes and shapes.",
        "Your car accelerates to overtake the traffic directly in front of you. You see and urgent expression on the face of the driver and the people in the other vehicles as you pass.",
        "A large truck is flashing its headlight directly behind. Your car quickly moves over to let the truck pass. The driver signals with a friendly wave.",
        "You see a broken-down vehicle beside the road. Its lights are flashing. The driver is looking concerned and she is using a mobile phone.",
        "The overall appearance and colour of the water, surf, and sky.",
        "Bathers are swimming and splashing about in the water. Some are playing with a brightly coloured beach ball.",
        "An ocean liner crosses the horizon. It leaves a trail of smoke in the blue sky.",
        "A beautiful air balloon appears with four people aboard. The balloon drifts past you, almost directly overhead. The passengers wave and smile. You wave and smile back at them.",
        "The overall appearance of the station viewed from in front of the main entrance.",
        "You walk into the station. The colour, shape and details of the entrance hall.",
        "You approach the ticket office, go to a vacant counter and purchase your ticket.",
        "You walk to the platform and observe other passengers and the railway lines. A train arrives. You climb aboard.",
        "The overall appearance and design of the garden.",
        "The colour and shape of the bushes and shrubs.",
        "The colour and appearance of the flowers.",
        "Some birds fly down onto the lawn and start pecking for food."
    ]
    print(f"  VVIQ2 columns identified: {len(vviq_columns)}")

    vviq_completion_excluded = set()
    for participant in all_participants:
        if participant in excluded_participants:
            continue

        p_data = data[data['participantId'] == participant]
        if len(p_data) == 0:
            continue

        # Get first row for this participant (VVIQ data should be same across rows)
        first_row = p_data.iloc[0]

        missing_count = 0
        for col in vviq_columns:
            if col in first_row and pd.isna(first_row[col]):
                missing_count += 1

        missing_percentage = missing_count / len(vviq_columns)
        if missing_percentage > 0.1:  # >10% missing
            print(f"    Participant {participant}: {missing_count}/{len(vviq_columns)} missing ({missing_percentage:.2%}) (excluded)")
            vviq_completion_excluded.add(participant)
        else:
            print(f"    Participant {participant}: {missing_count}/{len(vviq_columns)} missing ({missing_percentage:.2%}) (retained)")

    excluded_participants.update(vviq_completion_excluded)
    exclusion_log.append(('VVIQ2 Completion', len(vviq_completion_excluded), initial_participants - len(excluded_participants)))
    print(f"  Excluded {len(vviq_completion_excluded)} participants for VVIQ2 completion")
    print(f"  Remaining participants: {initial_participants - len(excluded_participants)}")

    # f. VVIQ2 Response Patterns
    print("\n6. VVIQ2 Response Patterns...")
    vviq_pattern_excluded = set()

    for participant in all_participants:
        if participant in excluded_participants:
            continue

        p_data = data[data['participantId'] == participant]
        if len(p_data) == 0:
            continue

        first_row = p_data.iloc[0]

        # Extract numeric scores from VVIQ responses
        scores = []
        for col in vviq_columns:
            if col in first_row and pd.notna(first_row[col]):
                response = str(first_row[col])
                # Find a digit 1-5 anywhere in the response
                match = re.search(r'([1-5])', response)
                if match:
                    scores.append(int(match.group(1)))

        if len(scores) > 1:  # Check for more than one score to have a meaningful comparison
            # Calculate percentage of identical ratings
            most_common_score = max(set(scores), key=scores.count)
            identical_percentage = scores.count(most_common_score) / len(scores)
        else:
            identical_percentage = 0  # Handle case with 0 or 1 scores

        # Check time taken
        time_taken = first_row.get('Time taken', np.nan)
        if pd.notna(time_taken) and identical_percentage > 0.8 and time_taken < 180:
            print(f"    Participant {participant}: {identical_percentage:.2%} identical ratings, time taken = {time_taken:.1f}s (excluded)")
            vviq_pattern_excluded.add(participant)
        else:
            print(f"    Participant {participant}: {identical_percentage:.2%} identical ratings, time taken = {time_taken if pd.notna(time_taken) else 'NA'} (retained)")

    excluded_participants.update(vviq_pattern_excluded)
    exclusion_log.append(('VVIQ2 Response Patterns', len(vviq_pattern_excluded), initial_participants - len(excluded_participants)))
    print(f"  Excluded {len(vviq_pattern_excluded)} participants for VVIQ2 response patterns")
    print(f"  Remaining participants: {initial_participants - len(excluded_participants)}")
    
    # g. Technical Issues (incomplete data)
    print("\n7. Technical Issues...")
    technical_excluded = set()
    
    for participant in all_participants:
        if participant in excluded_participants:
            continue
            
        p_data = data[data['participantId'] == participant]
        
        # Check if participant has VWM data
        has_vwm = len(p_data[p_data['VWM_trial'].notna()]) > 0
        
        # Check if participant has MRT data
        has_mrt = len(p_data[p_data['MRT_trial'].notna()]) > 0
        
        # Check if participant has VVIQ data
        has_vviq = any(col in p_data.columns and p_data[col].notna().any() for col in vviq_columns)
        
        if not (has_vwm and has_mrt and has_vviq):
            print(f"    Participant {participant}: has_vwm={has_vwm}, has_mrt={has_mrt}, has_vviq={has_vviq} (excluded)")
            technical_excluded.add(participant)
        else:
            print(f"    Participant {participant}: has_vwm={has_vwm}, has_mrt={has_mrt}, has_vviq={has_vviq} (retained)")
    
    excluded_participants.update(technical_excluded)
    exclusion_log.append(('Technical Issues', len(technical_excluded), initial_participants - len(excluded_participants)))
    print(f"  Excluded {len(technical_excluded)} participants for technical issues")
    print(f"  Remaining participants: {initial_participants - len(excluded_participants)}")
    
    # h. Extreme Session Duration
    print("\n8. Extreme Session Duration...")
    duration_excluded = set()
    
    for participant in all_participants:
        if participant in excluded_participants:
            continue
            
        p_data = data[data['participantId'] == participant]
        if len(p_data) == 0:
            continue
            
        first_row = p_data.iloc[0]
        time_taken = first_row.get('Time taken', np.nan)
        
        if pd.notna(time_taken):
            # Convert to minutes (assuming time_taken is in seconds)
            time_minutes = time_taken / 60
            if time_minutes < 15 or time_minutes > 120:
                print(f"    Participant {participant}: session duration = {time_minutes:.1f} min (excluded)")
                duration_excluded.add(participant)
            else:
                print(f"    Participant {participant}: session duration = {time_minutes:.1f} min (retained)")
        else:
            print(f"    Participant {participant}: session duration = NA (retained)")
    
    excluded_participants.update(duration_excluded)
    exclusion_log.append(('Extreme Session Duration', len(duration_excluded), initial_participants - len(excluded_participants)))
    print(f"  Excluded {len(duration_excluded)} participants for extreme session duration")
    print(f"  Remaining participants: {initial_participants - len(excluded_participants)}")
    
    # Create final retained dataset
    retained_participants = all_participants - excluded_participants
    retained_data = data[data['participantId'].isin(retained_participants)]
    
    print(f"\nFinal sample size: {len(retained_participants)}")
    print(f"Total exclusions: {len(excluded_participants)}")
    
    return retained_data, exclusion_log

def create_output_files(retained_data, exclusion_log):
    """
    Create output files for retained participants and exclusion log
    
    Args:
        retained_data (pd.DataFrame): Data for retained participants
        exclusion_log (list): List of exclusion criteria and counts
    """
    print("\n=== CREATING OUTPUT FILES ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Create timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Prepare retained participants data
    output_columns = [
        'participantId', 'table', 'browserName', 'browserVersion', 'browserLanguage',
        'webGLsupport', 'OS', 'frameRate', 'screenWidthPixels', 'screenHeightPixels',
        'windowWidthPixels', 'windowHeightPixels', 'wasFullscreenExited',
        'windowFocusLostDuringTasksNum', 'windowFocusLostDuringInfoNum',
        'windowFocusLostDuringTasksDuration', 'windowFocusLostDuringInfoDuration',
        'taskOrder', 'timestamp', 'isPractice', 'VWM_trial', 'VWM_setSize',
        'VWM_delay_s', 'VWM_cueIndex', 'VWM_orientations_degrees',
        'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees',
        'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_pracAttempt', 'VWM_timeout',
        'VWM_block', 'VWM_isAttentionCheck', 'MRT_trial', 'MRT_stimulusId',
        'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response', 'MRT_isCorrect',
        'MRT_rt_ms', 'MRT_pracAttempt', 'MRT_timeout', 'MRT_block',
        'MRT_isAttentionCheck', 'Age', 'Sex', 'Time_taken_minutes'
    ]

    # Map possible alternative column names for demographic/technical fields
    alt_column_map = {
        'Age': ['Age', 'age'],
        'Sex': ['Sex', 'sex', 'Gender'],
        'table': ['table'],
        'browserName': ['browserName'],
        'browserVersion': ['browserVersion'],
        'browserLanguage': ['browserLanguage'],
        'webGLsupport': ['webGLsupport'],
        'OS': ['OS', 'os'],
        'frameRate': ['frameRate'],
        'screenWidthPixels': ['screenWidthPixels'],
        'screenHeightPixels': ['screenHeightPixels'],
        'windowWidthPixels': ['windowWidthPixels'],
        'windowHeightPixels': ['windowHeightPixels'],
        'wasFullscreenExited': ['wasFullscreenExited'],
        'windowFocusLostDuringTasksNum': ['windowFocusLostDuringTasksNum'],
        'windowFocusLostDuringInfoNum': ['windowFocusLostDuringInfoNum'],
        'windowFocusLostDuringTasksDuration': ['windowFocusLostDuringTasksDuration'],
        'windowFocusLostDuringInfoDuration': ['windowFocusLostDuringInfoDuration'],
        'timestamp': ['timestamp'],
    }

    # Create output dataframe with available columns, using alternative names if needed
    output_data = pd.DataFrame()
    for col in output_columns:
        if col == 'Time_taken_minutes' and 'Time taken' in retained_data.columns:
            output_data[col] = retained_data['Time taken'] / 60
        elif col in retained_data.columns:
            output_data[col] = retained_data[col]
        elif col in alt_column_map:
            found = False
            for alt in alt_column_map[col]:
                if alt in retained_data.columns:
                    output_data[col] = retained_data[alt]
                    found = True
                    break
            if not found:
                output_data[col] = np.nan
        else:
            output_data[col] = np.nan

    # Save retained participants data
    retained_filename = f'outputs/retained_participants_{timestamp}.csv'
    output_data.to_csv(retained_filename, index=False)
    print(f"Saved retained participants data to: {retained_filename}")
    print(f"Retained data shape: {output_data.shape}")

    # Create exclusion log
    exclusion_df = pd.DataFrame(exclusion_log, columns=['exclusion_criteria', 'total_exclusions', 'remaining_participants'])

    # Save exclusion log
    exclusion_filename = f'outputs/exclusion_log_{timestamp}.csv'
    exclusion_df.to_csv(exclusion_filename, index=False)
    print(f"Saved exclusion log to: {exclusion_filename}")
    print(f"Exclusion log:")
    print(exclusion_df)

def main():
    """
    Main execution function
    """
    try:
        print("=== Starting data processing and exclusion pipeline... ===")
        
        # Load all datasets
        print("\n--- Loading Task Data ---")
        task_data = load_task_data()
        if task_data is None:
            print("ERROR: Failed to load task data")
            return 1
        
        print("\n--- Loading VVIQ2 Data ---")
        vviq_data = load_vviq_data()
        print("\n--- Loading Prolific Export Data ---")
        prolific_data = load_prolific_data()
        
        # Merge datasets
        print("\n--- Merging Datasets ---")
        merged_data = merge_datasets(task_data, vviq_data, prolific_data)
        
        # Print experimental design parameters
        print("\n--- Experimental Design Parameters ---")
        print_experimental_design_parameters(merged_data)
        
        # Apply exclusion criteria
        print("\n--- Applying Exclusion Criteria ---")
        retained_data, exclusion_log = apply_exclusion_criteria(merged_data)
        
        # Create output files
        print("\n--- Creating Output Files ---")
        create_output_files(retained_data, exclusion_log)
        
        # Final summary
        print("\n=== DATA CLEANING SUMMARY ===")
        initial_n = merged_data['participantId'].nunique()
        print(f"Data found for {initial_n} participants")
        exclusion_df = pd.DataFrame(exclusion_log, columns=['exclusion_criteria', 'total_exclusions', 'remaining_participants'])
        for _, row in exclusion_df.iterrows():
            if row['total_exclusions'] > 0:
                print(f"{row['total_exclusions']} participants were removed due to: {row['exclusion_criteria']}")
        final_n = retained_data['participantId'].nunique()
        total_rows = len(retained_data)
        print(f"Final dataset: {total_rows} trials from {final_n} participants")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
