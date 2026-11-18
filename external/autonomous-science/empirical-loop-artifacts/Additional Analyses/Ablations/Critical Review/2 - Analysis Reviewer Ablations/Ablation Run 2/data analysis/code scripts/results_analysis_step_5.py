#!/usr/bin/env python3
"""
Script to calculate individual-level measures from VWM and MRT task data.
Processes trial-level data to create participant-level summary measures.
"""

import pandas as pd
import numpy as np
import os
import glob
import re
from datetime import datetime

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern with <TIMESTAMP> placeholder
    
    Returns:
    str: Path to the most recent matching file
    """
    # Replace <TIMESTAMP> with wildcard pattern
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        raise FileNotFoundError(f"No files found matching pattern: {search_pattern}")
    
    # Get the most recent file by modification time
    latest_file = max(matching_files, key=os.path.getmtime)
    print(f"Found latest file: {latest_file}")
    return latest_file

def parse_duration_to_ms(duration_str):
    """
    Convert duration string to milliseconds.
    
    Parameters:
    duration_str: Duration string in various formats
    
    Returns:
    float: Duration in milliseconds
    """
    if pd.isna(duration_str) or duration_str == '':
        return 0.0
    
    # If already numeric, assume milliseconds
    try:
        return float(duration_str)
    except:
        pass
    
    # Parse time format like "00:00:01.234"
    duration_str = str(duration_str).strip()
    
    # Handle format HH:MM:SS.mmm
    if ':' in duration_str:
        parts = duration_str.split(':')
        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000
            return total_ms
    
    # Default to 0 if can't parse
    return 0.0

def extract_vviq2_score(response_text):
    """
    Extract numeric score (1-5) from VVIQ2 response text.
    
    Parameters:
    response_text (str): VVIQ2 response text ending with numeric score
    
    Returns:
    int: Extracted score (1-5)
    """
    if pd.isna(response_text):
        return np.nan
    
    # Extract last digit from the string
    text = str(response_text).strip()
    
    # Look for number at the end
    match = re.search(r'(\d)$', text)
    if match:
        score = int(match.group(1))
        if 1 <= score <= 5:
            return score
    
    return np.nan

def calculate_vwm_accuracy(df, guess_rate_threshold=0.1):
    """
    Calculate VWM mean accuracy using mixture model classifications.
    
    Parameters:
    df (DataFrame): Trial-level data for one participant
    guess_rate_threshold (float): Threshold for classifying guess trials
    
    Returns:
    tuple: (mean_accuracy_degrees, total_trials_used)
    """
    # Filter to test trials only
    test_trials = df[
        (df['isPractice'] == False) & 
        (df['VWM_trial_excluded'] == False) &
        (df['VWM_trial'].notna())
    ].copy()
    
    if len(test_trials) == 0:
        return np.nan, 0
    
    # Get guess rate for this participant
    guess_rate = df['guess_rate_vonmises'].iloc[0]
    
    if pd.isna(guess_rate):
        # If no guess rate available, use all trials
        non_guess_trials = test_trials
    else:
        # Exclude a proportion of trials with the largest error, corresponding to the guess rate
        n_trials = len(test_trials)
        n_guess = int(round(n_trials * guess_rate))
        if n_guess > 0:
            non_guess_trials = test_trials.sort_values(by='VWM_error_absolute_degrees', ascending=True)[:-n_guess]
        else:
            non_guess_trials = test_trials
    
    if len(non_guess_trials) == 0:
        return np.nan, 0
    
    # Calculate mean absolute error for non-guess trials
    mean_accuracy = non_guess_trials['VWM_error_absolute_degrees'].mean()
    
    return mean_accuracy, len(non_guess_trials)

def calculate_rt_cv(rt_values):
    """
    Calculate coefficient of variation for reaction times.
    
    Parameters:
    rt_values (Series): Reaction time values
    
    Returns:
    float: Coefficient of variation (SD/mean)
    """
    if len(rt_values) == 0:
        return np.nan
    
    mean_rt = rt_values.mean()
    std_rt = rt_values.std()
    
    if mean_rt == 0:
        return np.nan
    
    return std_rt / mean_rt

def calculate_timeout_rate(df, task_prefix):
    """
    Calculate timeout rate for a given task.
    
    Parameters:
    df (DataFrame): Trial-level data for one participant
    task_prefix (str): Task prefix ('VWM' or 'MRT')
    
    Returns:
    float: Timeout rate (0-1)
    """
    # Filter to all test trials for the task, prior to other exclusions
    test_trials = df[
        (df['isPractice'] == False) & 
        (df[f'{task_prefix}_trial'].notna())
    ]
    
    if len(test_trials) == 0:
        return np.nan
    
    timeout_count = test_trials[f'{task_prefix}_timeout'].sum()
    total_trials = len(test_trials)
    
    return timeout_count / total_trials

def process_participant_data(participant_data, vviq2_data):
    """
    Process data for a single participant to calculate individual-level measures.
    
    Parameters:
    participant_data (DataFrame): Trial-level data for one participant
    vviq2_data (DataFrame): VVIQ2 questionnaire data
    
    Returns:
    dict: Individual-level measures for the participant
    """
    participant_id = participant_data['participantId'].iloc[0]
    
    print(f"Processing participant: {participant_id}")
    
    # Initialize results dictionary
    results = {'participantId': participant_id}
    
    # 1. Calculate VWM mean accuracy
    vwm_accuracy, vwm_trials_used = calculate_vwm_accuracy(participant_data)
    results['vwm_mean_accuracy_degrees'] = vwm_accuracy
    results['total_vwm_trials_used'] = vwm_trials_used
    
    # 2. Calculate RT coefficients of variation
    # VWM RT CV
    vwm_test_trials = participant_data[
        (participant_data['isPractice'] == False) & 
        (participant_data['VWM_trial_excluded'] == False) &
        (participant_data['VWM_trial'].notna())
    ]
    results['vwm_rt_cv'] = calculate_rt_cv(vwm_test_trials['VWM_rt_ms'])
    
    # MRT RT CV
    mrt_test_trials = participant_data[
        (participant_data['isPractice'] == False) & 
        (participant_data['MRT_trial_excluded'] == False) &
        (participant_data['MRT_trial'].notna())
    ]
    results['mrt_rt_cv'] = calculate_rt_cv(mrt_test_trials['MRT_rt_ms'])
    results['total_mrt_trials_used'] = len(mrt_test_trials)
    
    # 3. Extract focus loss metrics (handle missing columns gracefully)
    results['focus_loss_instances_instructions'] = (
        participant_data['windowFocusLostDuringInfoNum'].iloc[0] 
        if 'windowFocusLostDuringInfoNum' in participant_data.columns 
        else 0
    )
    results['focus_loss_instances_tasks'] = (
        participant_data['windowFocusLostDuringTasksNum'].iloc[0] 
        if 'windowFocusLostDuringTasksNum' in participant_data.columns 
        else 0
    )

    # Convert duration to milliseconds (handle missing columns)
    info_duration = (
        participant_data['windowFocusLostDuringInfoDuration'].iloc[0] 
        if 'windowFocusLostDuringInfoDuration' in participant_data.columns 
        else 0
    )
    tasks_duration = (
        participant_data['windowFocusLostDuringTasksDuration'].iloc[0] 
        if 'windowFocusLostDuringTasksDuration' in participant_data.columns 
        else 0
    )

    results['focus_loss_duration_instructions_ms'] = parse_duration_to_ms(info_duration)
    results['focus_loss_duration_tasks_ms'] = parse_duration_to_ms(tasks_duration)
    
    # 4. Calculate timeout rates
    results['vwm_timeout_rate'] = calculate_timeout_rate(participant_data, 'VWM')
    results['mrt_timeout_rate'] = calculate_timeout_rate(participant_data, 'MRT')
    
    # 5. Calculate VVIQ2 scores using the exact, specified column names
    vviq2_question_columns = [
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

    # Debug: print which VVIQ2 columns are found and used
    available_vviq2_columns = [col for col in vviq2_question_columns if col in participant_data.columns]
    print(f"VVIQ2 columns found for participant {participant_id}: {len(available_vviq2_columns)} out of {len(vviq2_question_columns)} expected")

    # Initialize VVIQ2 scores
    vviq2_scores = []
    for col in vviq2_question_columns:
        if col in participant_data.columns:
            response = participant_data[col].iloc[0]
            score = extract_vviq2_score(response)
            if pd.notna(score):
                vviq2_scores.append(score)

    # Calculate VVIQ2 total and subscale scores using correct question groupings
    if len(vviq2_scores) >= 32:
        results['vviq2_total_score'] = sum(vviq2_scores)
        # Map subscales to correct question groups (4 questions each)
        results['vviq2_face_person_score'] = sum(vviq2_scores[0:4])      # Questions 1-4: Face/Person
        results['vviq2_nature_score'] = sum(vviq2_scores[4:8])          # Questions 5-8: Nature scenes
        results['vviq2_shop_score'] = sum(vviq2_scores[8:12])           # Questions 9-12: Shop
        results['vviq2_natural_env_score'] = sum(vviq2_scores[12:16])   # Questions 13-16: Natural environment
        results['vviq2_car_road_score'] = sum(vviq2_scores[16:20])      # Questions 17-20: Car/Road
        results['vviq2_beach_score'] = sum(vviq2_scores[20:24])         # Questions 21-24: Beach
        results['vviq2_station_score'] = sum(vviq2_scores[24:28])       # Questions 25-28: Station
        results['vviq2_garden_score'] = sum(vviq2_scores[28:32])        # Questions 29-32: Garden
    else:
        # Set to NaN if insufficient VVIQ2 data
        results['vviq2_total_score'] = np.nan
        results['vviq2_face_person_score'] = np.nan
        results['vviq2_nature_score'] = np.nan
        results['vviq2_shop_score'] = np.nan
        results['vviq2_natural_env_score'] = np.nan
        results['vviq2_car_road_score'] = np.nan
        results['vviq2_beach_score'] = np.nan
        results['vviq2_station_score'] = np.nan
        results['vviq2_garden_score'] = np.nan

    return results

def z_score_safe(series):
    """Calculate z-score safely, handling zero standard deviation."""
    mean_val = series.mean()
    std_val = series.std()
    if std_val == 0 or pd.isna(std_val):
        return pd.Series(0.0, index=series.index)
    return (series - mean_val) / std_val

def calculate_engagement_index(df):
    """
    Calculate engagement index based on standardized focus loss and timeout metrics.
    """
    if df.empty:
        return pd.Series(dtype=float)
    
    # Check if required columns exist
    required_cols = ['focus_loss_instances_instructions', 'focus_loss_instances_tasks', 
                     'vwm_timeout_rate', 'mrt_timeout_rate']
    
    for col in required_cols:
        if col not in df.columns:
            print(f"Warning: Column {col} not found, setting to 0")
            df[col] = 0

    # Calculate total focus loss instances
    total_focus_loss = (
        df['focus_loss_instances_instructions'].fillna(0) + 
        df['focus_loss_instances_tasks'].fillna(0)
    )
    
    # Get individual timeout rates
    vwm_timeout_rate = df['vwm_timeout_rate'].fillna(0)
    mrt_timeout_rate = df['mrt_timeout_rate'].fillna(0)
    
    # Add debugging output
    print(f"Focus loss distribution: {total_focus_loss.value_counts().head()}")
    print(f"VWM timeout rate distribution: {vwm_timeout_rate.value_counts().head()}")
    print(f"MRT timeout rate distribution: {mrt_timeout_rate.value_counts().head()}")
    
    # Standardize using z-scores (specification-compliant method)
    z_focus_loss = z_score_safe(total_focus_loss)
    z_timeout_vwm = z_score_safe(vwm_timeout_rate)
    z_timeout_mrt = z_score_safe(mrt_timeout_rate)
    
    # Calculate engagement index (higher = better engagement, so negate disengagement indicators)
    engagement_index = -(z_focus_loss + z_timeout_vwm + z_timeout_mrt)
    
    return engagement_index

def main():
    """
    Main function to process individual-level measures from trial data.
    """
    try:
        print("Starting individual-level measures calculation...")
        print(f"Current working directory: {os.getcwd()}")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input files
        print("\nFinding input files...")
        
        # Trial-level cleaned data
        trial_data_file = find_latest_file('outputs/trial_level_cleaned_data_<TIMESTAMP>.csv')
        
        # VWM mixture model parameters
        mixture_params_file = find_latest_file('outputs/vwm_mixture_model_parameters_<TIMESTAMP>.csv')
        
        # VVIQ2 data
        vviq2_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        
        # Load data files
        print("\nLoading data files...")
        
        print(f"Loading trial data from: {trial_data_file}")
        trial_data = pd.read_csv(trial_data_file)
        print(f"Trial data shape: {trial_data.shape}")
        print("Trial data columns:")
        print(trial_data.columns.tolist())
        print("First 3 rows of trial data:")
        print(trial_data.head(3))
        
        print(f"\nLoading mixture model parameters from: {mixture_params_file}")
        mixture_params = pd.read_csv(mixture_params_file)
        print(f"Mixture params shape: {mixture_params.shape}")
        print("Mixture params columns:")
        print(mixture_params.columns.tolist())
        print("First 3 rows of mixture params:")
        print(mixture_params.head(3))
        
        # Load VVIQ2 data if available and merge with trial data
        vviq2_data = None
        if os.path.exists(vviq2_file):
            print(f"\nLoading VVIQ2 data from: {vviq2_file}")
            vviq2_data = pd.read_csv(vviq2_file)
            print(f"VVIQ2 data shape: {vviq2_data.shape}")
            
            # Clean column names and rename PROLIFIC_PID to participantId for merging
            vviq2_data.columns = [col.strip() for col in vviq2_data.columns]
            if 'PROLIFIC_PID' in vviq2_data.columns:
                vviq2_data.rename(columns={'PROLIFIC_PID': 'participantId'}, inplace=True)
                print("Renamed PROLIFIC_PID to participantId in VVIQ2 data")
            
            # Merge VVIQ2 data with trial data
            print("Merging VVIQ2 data with trial data...")
            trial_data = trial_data.merge(vviq2_data, on='participantId', how='left')
            print(f"Trial data shape after VVIQ2 merge: {trial_data.shape}")
        else:
            print(f"\nVVIQ2 file not found: {vviq2_file}")
        
        # Merge trial data with mixture model parameters
        print("\nMerging trial data with mixture model parameters...")
        combined_data = trial_data.merge(
            mixture_params[['participantId', 'kappa_vonmises', 'guess_rate_vonmises', 'vonmises_convergence']], 
            on='participantId', 
            how='left'
        )
        print(f"Combined data shape after merge: {combined_data.shape}")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        
        # Check for VWM trial types
        if 'VWM_trial' in combined_data.columns:
            print(f"VWM_trial unique values: {sorted(combined_data['VWM_trial'].dropna().unique())}")
        
        # Check for MRT trial types  
        if 'MRT_trial' in combined_data.columns:
            print(f"MRT_trial unique values: {sorted(combined_data['MRT_trial'].dropna().unique())}")
        
        # Check practice vs test trials
        if 'isPractice' in combined_data.columns:
            print(f"isPractice unique values: {combined_data['isPractice'].unique()}")
        
        # Check exclusion flags
        if 'VWM_trial_excluded' in combined_data.columns:
            print(f"VWM_trial_excluded unique values: {combined_data['VWM_trial_excluded'].unique()}")
        
        if 'MRT_trial_excluded' in combined_data.columns:
            print(f"MRT_trial_excluded unique values: {combined_data['MRT_trial_excluded'].unique()}")
        
        # Check timeout flags
        if 'VWM_timeout' in combined_data.columns:
            print(f"VWM_timeout unique values: {combined_data['VWM_timeout'].unique()}")
        
        if 'MRT_timeout' in combined_data.columns:
            print(f"MRT_timeout unique values: {combined_data['MRT_timeout'].unique()}")
        
        # Check convergence status
        if 'vonmises_convergence' in combined_data.columns:
            print(f"vonmises_convergence unique values: {combined_data['vonmises_convergence'].unique()}")
        
        # Check participant eligibility
        if 'participant_meets_minimum_trials' in combined_data.columns:
            print(f"participant_meets_minimum_trials unique values: {combined_data['participant_meets_minimum_trials'].unique()}")
        
        # Print data types for measured variables (not unique values)
        print("\nData types for measured variables:")
        if 'VWM_error_absolute_degrees' in combined_data.columns:
            print(f"VWM_error_absolute_degrees type: {combined_data['VWM_error_absolute_degrees'].dtype}")
        if 'VWM_rt_ms' in combined_data.columns:
            print(f"VWM_rt_ms type: {combined_data['VWM_rt_ms'].dtype}")
        if 'MRT_rt_ms' in combined_data.columns:
            print(f"MRT_rt_ms type: {combined_data['MRT_rt_ms'].dtype}")
        
        # Filter to participants with convergent mixture models and sufficient trials
        print("\nFiltering participants...")
        
        eligible_participants = combined_data[
            (combined_data['vonmises_convergence'] == True) &
            (combined_data['participant_meets_minimum_trials'] == True)
        ]['participantId'].unique()
        
        print(f"Total participants in data: {combined_data['participantId'].nunique()}")
        print(f"Participants with convergent models: {combined_data[combined_data['vonmises_convergence'] == True]['participantId'].nunique()}")
        print(f"Participants meeting minimum trials: {combined_data[combined_data['participant_meets_minimum_trials'] == True]['participantId'].nunique()}")
        print(f"Eligible participants (both criteria): {len(eligible_participants)}")
        
        # Filter data to eligible participants only
        filtered_data = combined_data[combined_data['participantId'].isin(eligible_participants)]
        print(f"Filtered data shape: {filtered_data.shape}")
        
        # Process each participant
        print("\nProcessing individual participants...")
        
        individual_measures = []
        
        for participant_id in eligible_participants:
            participant_data = filtered_data[filtered_data['participantId'] == participant_id]
            
            try:
                measures = process_participant_data(participant_data, vviq2_data)
                individual_measures.append(measures)
                print(f"Successfully processed participant {participant_id}")
            except Exception as e:
                print(f"Error processing participant {participant_id}: {str(e)}")
                continue
        
        # Create dataframe of individual measures
        print(f"\nCreating individual measures dataframe...")
        individual_df = pd.DataFrame(individual_measures)
        print(f"Individual measures shape: {individual_df.shape}")
        
        print("Individual measures columns:")
        print(individual_df.columns.tolist())
        print("First 2 rows of individual measures:")
        print(individual_df.head(2))
        
        # Calculate engagement index
        print("\nCalculating engagement index...")
        individual_df['engagement_index'] = calculate_engagement_index(individual_df)
        
        # Print summary statistics
        print("\nSummary statistics for key measures:")
        print(f"VWM mean accuracy (degrees): {individual_df['vwm_mean_accuracy_degrees'].describe()}")
        print(f"VWM RT CV: {individual_df['vwm_rt_cv'].describe()}")
        print(f"MRT RT CV: {individual_df['mrt_rt_cv'].describe()}")
        print(f"VWM timeout rate: {individual_df['vwm_timeout_rate'].describe()}")
        print(f"MRT timeout rate: {individual_df['mrt_timeout_rate'].describe()}")
        print(f"VVIQ2 total score: {individual_df['vviq2_total_score'].describe()}")
        print(f"Engagement index: {individual_df['engagement_index'].describe()}")
        
        # Save output file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'outputs/individual_level_measures_{timestamp}.csv'
        
        print(f"\nSaving individual measures to: {output_file}")
        individual_df.to_csv(output_file, index=False)
        
        print(f"Successfully saved {len(individual_df)} participant records")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
