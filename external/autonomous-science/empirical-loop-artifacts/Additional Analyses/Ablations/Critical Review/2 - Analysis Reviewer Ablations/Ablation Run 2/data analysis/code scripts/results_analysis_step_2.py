#!/usr/bin/env python3
"""
Participant-level data cleaning script for VWM and MRT tasks with VVIQ2 questionnaire data.

This script processes multiple input files to create cleaned participant-level data
with comprehensive exclusion criteria applied.
"""

import pandas as pd
import numpy as np
import glob
import os
import re
from datetime import datetime
import sys

def create_outputs_directory():
    """
    Create outputs directory if it doesn't exist.
    
    Returns:
        None
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
        pattern (str): File pattern to match
        
    Returns:
        str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def load_participant_data():
    """
    Load all participant data files from the specified pattern.
    
    Returns:
        pd.DataFrame: Combined participant data from all files
    """
    print("Loading participant data files...")
    pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    files = glob.glob(pattern)
    
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return pd.DataFrame()
    
    print(f"Found {len(files)} participant data files:")
    for file in files:
        print(f"  - {file}")
    
    all_data = []
    for file in files:
        try:
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            print(f"\nLoaded {file}")
            print(f"Columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"First 3 rows:")
                print(df.head(3))
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
    
    if not all_data:
        print("No valid participant data files loaded")
        return pd.DataFrame()
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined participant data shape: {combined_df.shape}")
    print(f"Combined columns: {list(combined_df.columns)}")
    print(f"First 2 rows of combined data:")
    print(combined_df.head(2))
    
    return combined_df

def load_vviq2_data():
    """
    Load VVIQ2 questionnaire data.
    
    Returns:
        pd.DataFrame: VVIQ2 questionnaire data
    """
    print("\nLoading VVIQ2 data...")
    file_path = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
    
    try:
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()
        print(f"VVIQ2 data shape: {df.shape}")
        print(f"VVIQ2 columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"First 3 rows:")
            print(df.head(3))
        return df
    except Exception as e:
        print(f"Error loading VVIQ2 data: {e}")
        return pd.DataFrame()

def load_prolific_data():
    """
    Load Prolific export data, finding the most recent file.
    
    Returns:
        pd.DataFrame: Prolific export data
    """
    print("\nLoading Prolific data...")
    pattern = "../C_results/data/prolific_export_*.csv"
    latest_file = find_latest_file(pattern)
    
    if not latest_file:
        print(f"No files found matching pattern: {pattern}")
        return pd.DataFrame()
    
    print(f"Using most recent Prolific file: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file)
        df.columns = df.columns.str.strip()
        print(f"Prolific data shape: {df.shape}")
        print(f"Prolific columns: {list(df.columns)}")
        if len(df) > 0:
            print(f"First 3 rows:")
            print(df.head(3))
        return df
    except Exception as e:
        print(f"Error loading Prolific data: {e}")
        return pd.DataFrame()

def extract_vviq2_scores(vviq2_data):
    """
    Extract numeric scores from VVIQ2 response strings.
    
    Parameters:
        vviq2_data (pd.DataFrame): VVIQ2 questionnaire data
        
    Returns:
        dict: Mapping of participantId to VVIQ2 scores and completion metrics
    """
    print("\nExtracting VVIQ2 scores...")
    
    # Find VVIQ2 response columns (from "The exact contour..." to "Some birds fly down...")
    start_col = "The exact contour of face, head, shoulders and body."
    end_col = "Some birds fly down onto the lawn and start pecking for food."
    
    vviq2_cols = []
    found_start = False
    
    for col in vviq2_data.columns:
        if start_col in col:
            found_start = True
        if found_start:
            vviq2_cols.append(col)
        if end_col in col:
            break
    
    print(f"Found {len(vviq2_cols)} VVIQ2 response columns")
    print(f"VVIQ2 columns: {vviq2_cols}")
    
    participant_vviq2 = {}
    
    for _, row in vviq2_data.iterrows():
        participant_id = row.get('PROLIFIC_PID')
        if pd.isna(participant_id):
            participant_id = row.get('participantId') or row.get('Participant id')
        if pd.isna(participant_id):
            continue
            
        scores = []
        missing_count = 0
        
        for col in vviq2_cols:
            response = str(row.get(col, ''))
            if pd.isna(row.get(col)) or response == '' or response == 'nan':
                missing_count += 1
                scores.append(np.nan)
            else:
                # Extract numeric score from end of string
                match = re.search(r'(\d+)$', response.strip())
                if match:
                    score = int(match.group(1))
                    if 1 <= score <= 5:
                        scores.append(score)
                    else:
                        missing_count += 1
                        scores.append(np.nan)
                else:
                    missing_count += 1
                    scores.append(np.nan)
        
        # Calculate metrics
        total_items = len(vviq2_cols)
        missing_percentage = (missing_count / total_items) * 100 if total_items > 0 else 100
        
        # Calculate identical ratings percentage
        valid_scores = [s for s in scores if not pd.isna(s)]
        if len(valid_scores) > 0:
            most_common_score = max(set(valid_scores), key=valid_scores.count)
            identical_count = valid_scores.count(most_common_score)
            identical_percentage = (identical_count / len(valid_scores)) * 100
        else:
            identical_percentage = 0
        
        participant_vviq2[participant_id] = {
            'scores': scores,
            'missing_count': missing_count,
            'missing_percentage': missing_percentage,
            'identical_percentage': identical_percentage,
            'total_items': total_items,
            'has_data': len(valid_scores) > 0
        }
    
    print(f"Processed VVIQ2 data for {len(participant_vviq2)} participants")
    return participant_vviq2

def apply_exclusion_criteria(participant_data, vviq2_data, prolific_data):
    """
    Apply all exclusion criteria to the participant data.
    
    Parameters:
        participant_data (pd.DataFrame): Combined participant task data
        vviq2_data (pd.DataFrame): VVIQ2 questionnaire data
        prolific_data (pd.DataFrame): Prolific export data
        
    Returns:
        tuple: (cleaned_data, exclusion_log, all_participants, remaining_participants, final_data)
    """
    print("\nApplying exclusion criteria...")
    
    # Initialize exclusion tracking
    exclusion_log = []
    
    # Get all unique participants from main data
    all_participants = set(participant_data['participantId'].dropna().unique())
    print(f"Total participants in main data: {len(all_participants)}")
    print(f"Sample participant IDs in main data: {list(all_participants)[:5]}")
    print(f"Sample participant IDs in VVIQ2 data: {list(vviq2_data['PROLIFIC_PID'].dropna().unique())[:5] if 'PROLIFIC_PID' in vviq2_data.columns else 'N/A'}")
    print(f"Sample participant IDs in Prolific data: {list(prolific_data['PROLIFIC_PID'].dropna().unique())[:5] if 'PROLIFIC_PID' in prolific_data.columns else 'N/A'}")
    
    # 1. Filter Prolific data to approved participants only
    print("\n1. Applying Prolific approval filter...")
    approved_participants = set()
    if not prolific_data.empty and 'Status' in prolific_data.columns:
        approved_df = prolific_data[prolific_data['Status'] == 'APPROVED']
        prolific_id_col = None
        for col in ['PROLIFIC_PID', 'Participant id', 'participantId']:
            if col in approved_df.columns:
                prolific_id_col = col
                break
        if prolific_id_col is not None:
            approved_participants = set(approved_df[prolific_id_col].dropna().unique())
            print(f"Approved participants from Prolific: {len(approved_participants)}")
        else:
            print("Warning: No participant ID column found in Prolific data")
            approved_participants = all_participants  # Include all if no Prolific filter possible
    else:
        print("Warning: No Status column in Prolific data or empty data")
        approved_participants = all_participants  # Include all if no Prolific filter possible
    
    # Filter main data to approved participants
    if approved_participants:
        excluded_not_approved = all_participants - approved_participants
        remaining_participants = approved_participants & all_participants
        exclusion_log.append(['Prolific Status != APPROVED', len(excluded_not_approved), len(remaining_participants)])
    else:
        remaining_participants = all_participants
        exclusion_log.append(['Prolific Status != APPROVED', 0, len(remaining_participants)])
    
    print(f"Participants after Prolific filter: {len(remaining_participants)}")
    
    # 2. VWM Practice Performance exclusions
    print("\n2. Applying VWM practice performance exclusions...")
    vwm_practice_excluded = set()
    
    for participant in remaining_participants.copy():
        participant_df = participant_data[participant_data['participantId'] == participant]
        
        # Identify VWM practice trials
        vwm_practice = participant_df[
            (participant_df['isPractice'] == True) & 
            (participant_df['VWM_trial'].notna())
        ]
        
        if len(vwm_practice) == 0:
            print(f"  Participant {participant}: No VWM practice data found")
            vwm_practice_excluded.add(participant)
            continue
        
        # Group by practice attempt
        practice_attempts = vwm_practice['VWM_pracAttempt'].unique()
        practice_attempts = [x for x in practice_attempts if not pd.isna(x)]
        
        if len(practice_attempts) == 0:
            print(f"  Participant {participant}: No valid VWM practice attempts")
            vwm_practice_excluded.add(participant)
            continue
        
        passed_practice = False
        for attempt in sorted(practice_attempts):
            attempt_data = vwm_practice[vwm_practice['VWM_pracAttempt'] == attempt]
            valid_errors = attempt_data['VWM_error_absolute_degrees'].dropna()
            
            if len(valid_errors) > 0:
                mean_error = valid_errors.mean()
                if mean_error < 30:
                    passed_practice = True
                    break
        
        if not passed_practice and len(practice_attempts) >= 3:
            print(f"  Participant {participant}: Failed VWM practice after {len(practice_attempts)} attempts")
            vwm_practice_excluded.add(participant)
    
    remaining_participants -= vwm_practice_excluded
    exclusion_log.append(['VWM Practice Performance (<30° after 3 attempts)', len(vwm_practice_excluded), len(remaining_participants)])
    print(f"VWM practice excluded: {len(vwm_practice_excluded)}, remaining: {len(remaining_participants)}")
    
    # 3. MRT Practice Performance exclusions
    print("\n3. Applying MRT practice performance exclusions...")
    mrt_practice_excluded = set()
    
    for participant in remaining_participants.copy():
        participant_df = participant_data[participant_data['participantId'] == participant]
        
        # Identify MRT practice trials
        mrt_practice = participant_df[
            (participant_df['isPractice'] == True) & 
            (participant_df['MRT_trial'].notna())
        ]
        
        if len(mrt_practice) == 0:
            print(f"  Participant {participant}: No MRT practice data found")
            mrt_practice_excluded.add(participant)
            continue
        
        # Group by practice attempt
        practice_attempts = mrt_practice['MRT_pracAttempt'].unique()
        practice_attempts = [x for x in practice_attempts if not pd.isna(x)]
        
        if len(practice_attempts) == 0:
            print(f"  Participant {participant}: No valid MRT practice attempts")
            mrt_practice_excluded.add(participant)
            continue
        
        passed_practice = False
        for attempt in sorted(practice_attempts):
            attempt_data = mrt_practice[mrt_practice['MRT_pracAttempt'] == attempt]
            correct_responses = attempt_data['MRT_isCorrect'].sum()
            total_responses = len(attempt_data)
            
            if total_responses > 0:
                accuracy = correct_responses / total_responses
                if accuracy >= 8/12:  # 0.667
                    passed_practice = True
                    break
        
        if not passed_practice and len(practice_attempts) >= 3:
            print(f"  Participant {participant}: Failed MRT practice after {len(practice_attempts)} attempts")
            mrt_practice_excluded.add(participant)
    
    remaining_participants -= mrt_practice_excluded
    exclusion_log.append(['MRT Practice Performance (<8/12 correct after 3 attempts)', len(mrt_practice_excluded), len(remaining_participants)])
    print(f"MRT practice excluded: {len(mrt_practice_excluded)}, remaining: {len(remaining_participants)}")
    
    # 4. Main Task Timeout Rate exclusions
    print("\n4. Applying main task timeout rate exclusions...")
    timeout_excluded = set()
    
    for participant in remaining_participants.copy():
        participant_df = participant_data[participant_data['participantId'] == participant]
        
        # VWM timeout rate
        vwm_test = participant_df[
            (participant_df['isPractice'] == False) & 
            (participant_df['VWM_trial'].notna())
        ]
        
        if len(vwm_test) > 0:
            vwm_timeouts = vwm_test['VWM_timeout'].sum()
            vwm_timeout_rate = vwm_timeouts / len(vwm_test)
        else:
            vwm_timeout_rate = 0
        
        # MRT timeout rate
        mrt_test = participant_df[
            (participant_df['isPractice'] == False) & 
            (participant_df['MRT_trial'].notna())
        ]
        
        if len(mrt_test) > 0:
            mrt_timeouts = mrt_test['MRT_timeout'].sum()
            mrt_timeout_rate = mrt_timeouts / len(mrt_test)
        else:
            mrt_timeout_rate = 0
        
        if vwm_timeout_rate > 0.20 or mrt_timeout_rate > 0.20:
            print(f"  Participant {participant}: High timeout rate (VWM: {vwm_timeout_rate:.3f}, MRT: {mrt_timeout_rate:.3f})")
            timeout_excluded.add(participant)
    
    remaining_participants -= timeout_excluded
    exclusion_log.append(['Main Task Timeout Rate (>20%)', len(timeout_excluded), len(remaining_participants)])
    print(f"Timeout excluded: {len(timeout_excluded)}, remaining: {len(remaining_participants)}")
    
    # 5. MRT 0° Rotation Performance exclusions
    print("\n5. Applying MRT 0° rotation performance exclusions...")

    # Collect MRT 0° accuracy scores for analysis
    mrt_0deg_accuracies = []
    for participant in remaining_participants:
        participant_df = participant_data[participant_data['participantId'] == participant]
        mrt_0deg = participant_df[
            (participant_df['isPractice'] == False) & 
            (participant_df['MRT_trial'].notna()) &
            (participant_df['MRT_angle_degrees'] == 0)
        ]
        if len(mrt_0deg) >= 8:
            accuracy_0deg = mrt_0deg['MRT_isCorrect'].sum() / len(mrt_0deg)
            mrt_0deg_accuracies.append(accuracy_0deg)

    if mrt_0deg_accuracies:
        print(f"MRT 0° accuracy distribution (n={len(mrt_0deg_accuracies)}):")
        print(f"  Mean: {np.mean(mrt_0deg_accuracies):.3f}")
        print(f"  Median: {np.median(mrt_0deg_accuracies):.3f}")
        print(f"  Min: {np.min(mrt_0deg_accuracies):.3f}")
        print(f"  Max: {np.max(mrt_0deg_accuracies):.3f}")
        print(f"  Below 70%: {sum(1 for acc in mrt_0deg_accuracies if acc < 0.70)} ({sum(1 for acc in mrt_0deg_accuracies if acc < 0.70)/len(mrt_0deg_accuracies)*100:.1f}%)")

    mrt_0deg_excluded = set()
    
    for participant in remaining_participants.copy():
        participant_df = participant_data[participant_data['participantId'] == participant]
        
        # Identify 0° rotation test trials
        mrt_0deg = participant_df[
            (participant_df['isPractice'] == False) & 
            (participant_df['MRT_trial'].notna()) &
            (participant_df['MRT_angle_degrees'] == 0)
        ]
        
        if len(mrt_0deg) >= 8:  # Minimum 8 trials for reliable estimate
            correct_0deg = mrt_0deg['MRT_isCorrect'].sum()
            accuracy_0deg = correct_0deg / len(mrt_0deg)
            
            if accuracy_0deg < 0.70:
                print(f"  Participant {participant}: Low 0° accuracy ({accuracy_0deg:.3f}) on {len(mrt_0deg)} trials")
                mrt_0deg_excluded.add(participant)
        else:
            print(f"  Participant {participant}: Insufficient 0° trials ({len(mrt_0deg)} < 8)")
            mrt_0deg_excluded.add(participant)
    
    remaining_participants -= mrt_0deg_excluded
    exclusion_log.append(['MRT 0° Rotation Performance (<70% or <8 trials)', len(mrt_0deg_excluded), len(remaining_participants)])
    print(f"MRT 0° excluded: {len(mrt_0deg_excluded)}, remaining: {len(remaining_participants)}")
    
    # 6. VVIQ2 Questionnaire Completion exclusions
    print("\n6. Applying VVIQ2 completion exclusions...")
    vviq2_scores = extract_vviq2_scores(vviq2_data)
    vviq2_excluded = set()
    
    for participant in remaining_participants.copy():
        if participant not in vviq2_scores:
            print(f"  Participant {participant}: No VVIQ2 data")
            vviq2_excluded.add(participant)
            continue
        
        vviq2_info = vviq2_scores[participant]
        
        if not vviq2_info['has_data']:
            print(f"  Participant {participant}: No valid VVIQ2 responses")
            vviq2_excluded.add(participant)
            continue
        
        if vviq2_info['missing_percentage'] > 10:
            print(f"  Participant {participant}: Too many missing VVIQ2 items ({vviq2_info['missing_percentage']:.1f}%)")
            vviq2_excluded.add(participant)
            continue
        
        if vviq2_info['identical_percentage'] > 80:
            print(f"  Participant {participant}: Too many identical VVIQ2 ratings ({vviq2_info['identical_percentage']:.1f}%)")
            vviq2_excluded.add(participant)
            continue
    
    remaining_participants -= vviq2_excluded
    exclusion_log.append(['VVIQ2 Completion Issues (>10% missing or >80% identical)', len(vviq2_excluded), len(remaining_participants)])
    print(f"VVIQ2 excluded: {len(vviq2_excluded)}, remaining: {len(remaining_participants)}")
    
    # 7. Technical Issues exclusions
    print("\n7. Applying technical issues exclusions...")
    technical_excluded = set()
    
    for participant in remaining_participants.copy():
        participant_df = participant_data[participant_data['participantId'] == participant]
        
        # Check for VWM data
        has_vwm = len(participant_df[participant_df['VWM_trial'].notna()]) > 0
        
        # Check for MRT data
        has_mrt = len(participant_df[participant_df['MRT_trial'].notna()]) > 0
        
        # Check for VVIQ2 data (already checked above, but for completeness)
        has_vviq2 = participant in vviq2_scores and vviq2_scores[participant]['has_data']
        
        if not (has_vwm and has_mrt and has_vviq2):
            print(f"  Participant {participant}: Incomplete data (VWM: {has_vwm}, MRT: {has_mrt}, VVIQ2: {has_vviq2})")
            technical_excluded.add(participant)
    
    remaining_participants -= technical_excluded
    exclusion_log.append(['Technical Issues (incomplete data)', len(technical_excluded), len(remaining_participants)])
    print(f"Technical issues excluded: {len(technical_excluded)}, remaining: {len(remaining_participants)}")
    
    print(f"\nFinal remaining participants: {len(remaining_participants)}")

    # Verify exclusion cascading
    all_excluded = (vwm_practice_excluded | mrt_practice_excluded | timeout_excluded | 
                   mrt_0deg_excluded | vviq2_excluded | technical_excluded)
    print(f"\nExclusion verification:")
    print(f"  VWM practice: {len(vwm_practice_excluded)}")
    print(f"  MRT practice: {len(mrt_practice_excluded)}")
    print(f"  Timeout: {len(timeout_excluded)}")
    print(f"  MRT 0°: {len(mrt_0deg_excluded)}")
    print(f"  VVIQ2: {len(vviq2_excluded)}")
    print(f"  Technical: {len(technical_excluded)}")
    print(f"  Total unique excluded: {len(all_excluded)}")
    
    # Create cleaned dataset
    print("\nCreating cleaned dataset...")
    cleaned_data = participant_data[participant_data['participantId'].isin(remaining_participants)].copy()
    
    # Add inclusion/exclusion columns
    cleaned_data['included'] = True
    cleaned_data['exclusion_reason'] = ''
    
    # Also include excluded participants with their exclusion reasons
    excluded_data_list = []
    
    for participant in all_excluded:
        participant_df = participant_data[participant_data['participantId'] == participant].copy()
        participant_df['included'] = False
        
        # Determine exclusion reason
        if participant in vwm_practice_excluded:
            participant_df['exclusion_reason'] = 'VWM Practice Performance'
        elif participant in mrt_practice_excluded:
            participant_df['exclusion_reason'] = 'MRT Practice Performance'
        elif participant in timeout_excluded:
            participant_df['exclusion_reason'] = 'High Timeout Rate'
        elif participant in mrt_0deg_excluded:
            participant_df['exclusion_reason'] = 'MRT 0° Performance'
        elif participant in vviq2_excluded:
            participant_df['exclusion_reason'] = 'VVIQ2 Completion Issues'
        elif participant in technical_excluded:
            participant_df['exclusion_reason'] = 'Technical Issues'
        
        excluded_data_list.append(participant_df)
    
    if excluded_data_list:
        excluded_data = pd.concat(excluded_data_list, ignore_index=True)
        final_data = pd.concat([cleaned_data, excluded_data], ignore_index=True)
    else:
        final_data = cleaned_data
    
    print(f"Final dataset shape: {final_data.shape}")
    print(f"Included participants: {final_data['included'].sum()}")
    print(f"Excluded participants: {(~final_data['included']).sum()}")
    
    return final_data, exclusion_log, all_participants, remaining_participants, final_data

def print_experimental_parameters(data):
    """
    Print unique values for key experimental design parameters.
    
    Parameters:
        data (pd.DataFrame): Participant data
        
    Returns:
        None
    """
    print("\nExperimental Design Parameters:")
    
    # VWM parameters
    if 'VWM_setSize' in data.columns:
        unique_set_sizes = data['VWM_setSize'].dropna().unique()
        print(f"VWM Set Sizes: {sorted(unique_set_sizes)}")
    
    if 'VWM_delay_s' in data.columns:
        unique_delays = data['VWM_delay_s'].dropna().unique()
        print(f"VWM Delays (seconds): {sorted(unique_delays)}")
    
    # MRT parameters
    if 'MRT_angle_degrees' in data.columns:
        unique_angles = data['MRT_angle_degrees'].dropna().unique()
        print(f"MRT Rotation Angles: {sorted(unique_angles)}")
    
    # Practice attempt counts
    if 'VWM_pracAttempt' in data.columns:
        unique_vwm_attempts = data['VWM_pracAttempt'].dropna().unique()
        print(f"VWM Practice Attempts: {sorted(unique_vwm_attempts)}")
    
    if 'MRT_pracAttempt' in data.columns:
        unique_mrt_attempts = data['MRT_pracAttempt'].dropna().unique()
        print(f"MRT Practice Attempts: {sorted(unique_mrt_attempts)}")
    
    # Boolean parameters
    if 'isPractice' in data.columns:
        unique_practice = data['isPractice'].dropna().unique()
        print(f"Practice Trial Values: {unique_practice}")
    
    if 'VWM_timeout' in data.columns:
        print(f"VWM Timeout column type: {data['VWM_timeout'].dtype}")
    
    if 'MRT_timeout' in data.columns:
        print(f"MRT Timeout column type: {data['MRT_timeout'].dtype}")
    
    if 'MRT_isCorrect' in data.columns:
        print(f"MRT Correct column type: {data['MRT_isCorrect'].dtype}")
    
    # Measured variables (just show type, not unique values)
    if 'VWM_error_absolute_degrees' in data.columns:
        print(f"VWM Error column type: {data['VWM_error_absolute_degrees'].dtype}")
    
    if 'VWM_rt_ms' in data.columns:
        print(f"VWM RT column type: {data['VWM_rt_ms'].dtype}")
    
    if 'MRT_rt_ms' in data.columns:
        print(f"MRT RT column type: {data['MRT_rt_ms'].dtype}")

def save_outputs(cleaned_data, exclusion_log):
    """
    Save the cleaned data and exclusion log to CSV files.
    
    Parameters:
        cleaned_data (pd.DataFrame): Cleaned participant data
        exclusion_log (list): List of exclusion criteria and counts
        
    Returns:
        None
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Define required output columns
    required_columns = [
        'participantId', 'isPractice', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
        'VWM_cueIndex', 'VWM_orientations_degrees', 'VWM_responseAngle_degrees',
        'VWM_targetAngle_degrees', 'VWM_error_degrees', 'VWM_error_absolute_degrees',
        'VWM_rt_ms', 'VWM_pracAttempt', 'VWM_timeout', 'VWM_block', 'VWM_isAttentionCheck',
        'MRT_trial', 'MRT_stimulusId', 'MRT_angle_degrees', 'MRT_isReflected',
        'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_pracAttempt', 'MRT_timeout',
        'MRT_block', 'MRT_isAttentionCheck', 'included', 'exclusion_reason'
    ]
    
    # Select only available required columns
    available_columns = [col for col in required_columns if col in cleaned_data.columns]
    output_data = cleaned_data[available_columns].copy()
    
    print(f"\nSaving cleaned data with columns: {available_columns}")
    
    # Save cleaned data
    cleaned_filename = f"outputs/participant_level_cleaned_data_{timestamp}.csv"
    output_data.to_csv(cleaned_filename, index=False)
    print(f"Saved cleaned data to: {cleaned_filename}")
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusion_log, columns=['exclusion_criteria', 'number_excluded', 'remaining_participants'])
    exclusion_filename = f"outputs/participant_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(exclusion_filename, index=False)
    print(f"Saved exclusion log to: {exclusion_filename}")
    
    print(f"\nExclusion Summary:")
    print(exclusion_df)

def main():
    """
    Main execution function.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting participant-level data cleaning script...")
        
        # Create outputs directory
        create_outputs_directory()
        
        # Load all data files
        participant_data = load_participant_data()
        vviq2_data = load_vviq2_data()
        prolific_data = load_prolific_data()
        
        # Check if we have the minimum required data
        if participant_data.empty:
            print("Error: No participant data loaded")
            return 1

        # Move experimental parameters print here (after data load, before exclusions)
        print_experimental_parameters(participant_data)
        
        # Apply exclusion criteria
        cleaned_data, exclusion_log, all_participants, remaining_participants, final_data = apply_exclusion_criteria(participant_data, vviq2_data, prolific_data)
        
        # Save outputs
        save_outputs(cleaned_data, exclusion_log)

        # Print final summary statistics
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Data found for {len(all_participants)} participants")
        print(f"Final dataset: {final_data['included'].sum()} trials from {len(remaining_participants)} participants")
        print(f"Total exclusion rate: {((len(all_participants) - len(remaining_participants)) / len(all_participants) * 100):.1f}%")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
