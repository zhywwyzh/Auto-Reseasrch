import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def load_exclusion_data():
    """
    Load participant exclusion status data from the most recent file.
    
    Returns:
        pd.DataFrame: DataFrame with participantId and included columns
    """
    print("Loading participant exclusion data...")
    
    # Find the most recent exclusion file
    exclusion_files = glob.glob("outputs/participant_exclusion_status_*.csv")
    if not exclusion_files:
        print("ERROR: No participant exclusion status files found!")
        return None
    
    latest_file = max(exclusion_files, key=os.path.getctime)
    print(f"Using exclusion file: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file)
        print(f"Exclusion data columns: {list(df.columns)}")
        print(f"First 3 rows of exclusion data:")
        print(df.head(3))
        
        # Check required columns
        required_cols = ['participantId', 'included']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"ERROR: Missing required columns in exclusion file: {missing_cols}")
            return None
        
        print(f"Total participants in exclusion file: {len(df)}")
        print(f"Participants with included=True: {df['included'].sum()}")
        
        return df
    
    except Exception as e:
        print(f"ERROR loading exclusion file: {e}")
        return None

def load_participant_data():
    """
    Load individual participant CSV files for VWM and MRT tasks.
    
    Returns:
        pd.DataFrame: Combined DataFrame with all participant data
    """
    print("\nLoading individual participant data files...")
    
    # Find all participant data files
    data_files = glob.glob("../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv")
    print(f"Found {len(data_files)} participant data files")
    
    if not data_files:
        print("ERROR: No participant data files found!")
        return None
    
    all_data = []
    
    for file_path in data_files:
        print(f"Loading: {file_path}")
        try:
            df = pd.read_csv(file_path)
            
            # Extract participant ID from filename
            filename = os.path.basename(file_path)
            # Format: PARTICIPANT_<ID>_VWM_and_Rotation_Task_<timestamp>.csv
            participant_id = filename.split('_')[1]
            df['participantId'] = participant_id
            
            all_data.append(df)
            
        except Exception as e:
            print(f"ERROR loading {file_path}: {e}")
            continue
    
    if not all_data:
        print("ERROR: No valid participant data files loaded!")
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined data shape: {combined_df.shape}")
    print(f"Combined data columns: {list(combined_df.columns)}")
    print(f"First 3 rows of combined data:")
    print(combined_df.head(3))
    
    # Check required columns
    required_cols = [
        'participantId', 'isPractice', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
        'VWM_cueIndex', 'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees',
        'VWM_error_degrees', 'VWM_error_absolute_degrees', 'VWM_rt_ms',
        'VWM_timeout', 'VWM_isAttentionCheck', 'MRT_trial', 'MRT_angle_degrees',
        'MRT_isReflected', 'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms',
        'MRT_timeout', 'MRT_isAttentionCheck'
    ]
    
    missing_cols = [col for col in required_cols if col not in combined_df.columns]
    if missing_cols:
        print(f"WARNING: Missing columns in participant data: {missing_cols}")
    
    # Print unique values for key experimental design parameters
    print("\n=== EXPERIMENTAL DESIGN PARAMETERS ===")
    
    # VWM parameters
    vwm_data = combined_df[combined_df['VWM_trial'].notna()]
    if len(vwm_data) > 0:
        print(f"VWM set sizes: {sorted(vwm_data['VWM_setSize'].dropna().unique())}")
        print(f"VWM delay durations: {sorted(vwm_data['VWM_delay_s'].dropna().unique())}")
        print(f"VWM isPractice values: {sorted(vwm_data['isPractice'].dropna().unique())}")
    
    # MRT parameters  
    mrt_data = combined_df[combined_df['MRT_trial'].notna()]
    if len(mrt_data) > 0:
        print(f"MRT rotation angles: {sorted(mrt_data['MRT_angle_degrees'].dropna().unique())}")
        print(f"MRT isReflected values: {sorted(mrt_data['MRT_isReflected'].dropna().unique())}")
        print(f"MRT isPractice values: {sorted(mrt_data['isPractice'].dropna().unique())}")
    
    print(f"VWM reaction time data type: {type(vwm_data['VWM_rt_ms'].iloc[0] if len(vwm_data) > 0 else 'N/A')}")
    print(f"MRT reaction time data type: {type(mrt_data['MRT_rt_ms'].iloc[0] if len(mrt_data) > 0 else 'N/A')}")
    
    return combined_df

def filter_included_participants(data_df, exclusion_df):
    """
    Filter data to only include participants marked as included=True.
    
    Args:
        data_df (pd.DataFrame): Combined participant data
        exclusion_df (pd.DataFrame): Exclusion status data
        
    Returns:
        pd.DataFrame: Filtered data for included participants only
    """
    print("\nFiltering to included participants...")
    
    # Get list of included participants
    included_participants = exclusion_df[exclusion_df['included'] == True]['participantId'].tolist()
    print(f"Number of included participants: {len(included_participants)}")
    
    # Filter data
    filtered_df = data_df[data_df['participantId'].isin(included_participants)].copy()
    print(f"Data shape after filtering: {filtered_df.shape}")
    
    return filtered_df

def identify_task_rows(df):
    """
    Identify which rows belong to VWM vs MRT tasks.
    
    Args:
        df (pd.DataFrame): Combined data
        
    Returns:
        tuple: (vwm_rows, mrt_rows) boolean masks
    """
    print("\nIdentifying task-specific rows...")
    
    # VWM rows have non-null VWM_trial values
    vwm_rows = df['VWM_trial'].notna()
    
    # MRT rows have non-null MRT_trial values
    mrt_rows = df['MRT_trial'].notna()
    
    print(f"VWM rows: {vwm_rows.sum()}")
    print(f"MRT rows: {mrt_rows.sum()}")
    print(f"Total rows: {len(df)}")
    
    return vwm_rows, mrt_rows

def apply_trial_exclusions(df, vwm_rows, mrt_rows):
    """
    Apply trial-level exclusion criteria for both VWM and MRT test trials.
    
    Args:
        df (pd.DataFrame): Combined data
        vwm_rows (pd.Series): Boolean mask for VWM rows
        mrt_rows (pd.Series): Boolean mask for MRT rows
        
    Returns:
        tuple: (df with exclusion info, exclusion_stats)
    """
    print("\nApplying trial-level exclusions...")
    
    # Initialize exclusion tracking
    df['trial_excluded'] = False
    df['exclusion_reason'] = ''
    exclusion_stats = {
        'VWM_anticipatory': 0,
        'VWM_slow': 0,
        'VWM_timeout': 0,
        'VWM_impossible_error': 0,
        'MRT_anticipatory': 0,
        'MRT_slow': 0,
        'MRT_timeout': 0
    }
    
    # Separate practice and test trials
    vwm_test = vwm_rows & (df['isPractice'] == False)
    mrt_test = mrt_rows & (df['isPractice'] == False)
    
    print(f"VWM test trials: {vwm_test.sum()}")
    print(f"MRT test trials: {mrt_test.sum()}")
    
    # 1. Anticipatory responses (<200ms)
    print("\nApplying anticipatory response exclusions...")
    
    # VWM anticipatory
    vwm_anticipatory = vwm_test & (df['VWM_rt_ms'] < 200) & ~df['trial_excluded']
    df.loc[vwm_anticipatory, 'trial_excluded'] = True
    df.loc[vwm_anticipatory, 'exclusion_reason'] = 'anticipatory_response'
    exclusion_stats['VWM_anticipatory'] = vwm_anticipatory.sum()
    print(f"VWM anticipatory exclusions: {exclusion_stats['VWM_anticipatory']}")
    
    # MRT anticipatory
    mrt_anticipatory = mrt_test & (df['MRT_rt_ms'] < 200) & ~df['trial_excluded']
    df.loc[mrt_anticipatory, 'trial_excluded'] = True
    df.loc[mrt_anticipatory, 'exclusion_reason'] = 'anticipatory_response'
    exclusion_stats['MRT_anticipatory'] = mrt_anticipatory.sum()
    print(f"MRT anticipatory exclusions: {exclusion_stats['MRT_anticipatory']}")
    
    # 2. Extremely slow responses (>3 SD above participant mean)
    print("\nApplying slow response exclusions...")
    
    for participant in df['participantId'].unique():
        if pd.isna(participant):
            continue

        participant_mask = df['participantId'] == participant

        # VWM slow responses
        vwm_participant_test_mask = vwm_test & participant_mask
        vwm_valid_for_stats_mask = vwm_participant_test_mask & ~df['trial_excluded']

        if vwm_valid_for_stats_mask.sum() > 1:
            vwm_rts = df.loc[vwm_valid_for_stats_mask, 'VWM_rt_ms']
            mean_rt, sd_rt = vwm_rts.mean(), vwm_rts.std()
            if pd.notna(sd_rt) and sd_rt > 0:
                threshold = mean_rt + 3 * sd_rt
                slow_trials_mask = vwm_participant_test_mask & (df['VWM_rt_ms'] > threshold) & ~df['trial_excluded']
                df.loc[slow_trials_mask, 'trial_excluded'] = True
                df.loc[slow_trials_mask, 'exclusion_reason'] = 'slow_response'
                exclusion_stats['VWM_slow'] += slow_trials_mask.sum()

        # MRT slow responses
        mrt_participant_test_mask = mrt_test & participant_mask
        mrt_valid_for_stats_mask = mrt_participant_test_mask & ~df['trial_excluded']

        if mrt_valid_for_stats_mask.sum() > 1:
            mrt_rts = df.loc[mrt_valid_for_stats_mask, 'MRT_rt_ms']
            mean_rt, sd_rt = mrt_rts.mean(), mrt_rts.std()
            if pd.notna(sd_rt) and sd_rt > 0:
                threshold = mean_rt + 3 * sd_rt
                slow_trials_mask = mrt_participant_test_mask & (df['MRT_rt_ms'] > threshold) & ~df['trial_excluded']
                df.loc[slow_trials_mask, 'trial_excluded'] = True
                df.loc[slow_trials_mask, 'exclusion_reason'] = 'slow_response'
                exclusion_stats['MRT_slow'] += slow_trials_mask.sum()
    
    print(f"VWM slow response exclusions: {exclusion_stats['VWM_slow']}")
    print(f"MRT slow response exclusions: {exclusion_stats['MRT_slow']}")
    
    # 3. Timeout exclusions
    print("\nApplying timeout exclusions...")
    
    # VWM timeouts
    vwm_timeout = vwm_test & (df['VWM_timeout'] == True) & ~df['trial_excluded']
    df.loc[vwm_timeout, 'trial_excluded'] = True
    df.loc[vwm_timeout, 'exclusion_reason'] = 'timeout'
    exclusion_stats['VWM_timeout'] = vwm_timeout.sum()
    print(f"VWM timeout exclusions: {exclusion_stats['VWM_timeout']}")
    
    # MRT timeouts
    mrt_timeout = mrt_test & (df['MRT_timeout'] == True) & ~df['trial_excluded']
    df.loc[mrt_timeout, 'trial_excluded'] = True
    df.loc[mrt_timeout, 'exclusion_reason'] = 'timeout'
    exclusion_stats['MRT_timeout'] = mrt_timeout.sum()
    print(f"MRT timeout exclusions: {exclusion_stats['MRT_timeout']}")
    
    # 4. VWM impossible errors (>180°)
    print("\nApplying VWM impossible error exclusions...")
    
    vwm_impossible = vwm_test & (np.abs(df['VWM_error_degrees']) > 180) & ~df['trial_excluded']
    df.loc[vwm_impossible, 'trial_excluded'] = True
    df.loc[vwm_impossible, 'exclusion_reason'] = 'impossible_error'
    exclusion_stats['VWM_impossible_error'] = vwm_impossible.sum()
    print(f"VWM impossible error exclusions: {exclusion_stats['VWM_impossible_error']}")
    
    return df, exclusion_stats

def process_vwm_data(df, vwm_rows):
    """
    Process VWM test trial data including error normalization.
    
    Args:
        df (pd.DataFrame): Data with exclusion info
        vwm_rows (pd.Series): Boolean mask for VWM rows
        
    Returns:
        pd.DataFrame: Processed VWM data (ALL test trials, with exclusion status marked)
    """
    print("\nProcessing VWM data (ALL test trials, with exclusion status marked)...")
    
    # Filter to ALL VWM test trials (regardless of exclusion)
    vwm_test_all = vwm_rows & (df['isPractice'] == False)
    vwm_data = df[vwm_test_all].copy()
    
    print(f"Total VWM test trials (including excluded): {len(vwm_data)}")
    
    if len(vwm_data) == 0:
        print("WARNING: No VWM test trials found!")
        return pd.DataFrame()
    
    # Calculate normalized errors
    print("Calculating normalized errors...")
    vwm_data['normalized_error_degrees'] = vwm_data['VWM_error_degrees'].copy()
    
    # Normalize to +/- 90° range
    mask = np.abs(vwm_data['normalized_error_degrees']) > 90
    vwm_data.loc[mask, 'normalized_error_degrees'] = (
        vwm_data.loc[mask, 'normalized_error_degrees'] - 
        180 * np.sign(vwm_data.loc[mask, 'normalized_error_degrees'])
    )
    
    # Create output DataFrame
    vwm_output = pd.DataFrame({
        'participantId': vwm_data['participantId'],
        'trial_number': vwm_data['VWM_trial'],
        'set_size': vwm_data['VWM_setSize'],
        'delay_duration': vwm_data['VWM_delay_s'],
        'target_angle_degrees': vwm_data['VWM_targetAngle_degrees'],
        'response_angle_degrees': vwm_data['VWM_responseAngle_degrees'],
        'signed_error_degrees': vwm_data['VWM_error_degrees'],
        'absolute_error_degrees': vwm_data['VWM_error_absolute_degrees'],
        'normalized_error_degrees': vwm_data['normalized_error_degrees'],
        'reaction_time_ms': vwm_data['VWM_rt_ms'],
        'is_attention_check': vwm_data['VWM_isAttentionCheck'],
        'trial_excluded': vwm_data['trial_excluded'],
        'exclusion_reason': vwm_data['exclusion_reason']
    })
    
    print(f"VWM output columns: {list(vwm_output.columns)}")
    print(f"First 2 rows of VWM output:")
    print(vwm_output.head(2))
    
    return vwm_output

def process_mrt_data(df, mrt_rows):
    """
    Process MRT test trial data.
    
    Args:
        df (pd.DataFrame): Data with exclusion info
        mrt_rows (pd.Series): Boolean mask for MRT rows
        
    Returns:
        pd.DataFrame: Processed MRT data (ALL test trials, with exclusion status marked)
    """
    print("\nProcessing MRT data (ALL test trials, with exclusion status marked)...")
    
    # Filter to ALL MRT test trials (regardless of exclusion)
    mrt_test_all = mrt_rows & (df['isPractice'] == False)
    mrt_data = df[mrt_test_all].copy()
    
    print(f"Total MRT test trials (including excluded): {len(mrt_data)}")
    
    if len(mrt_data) == 0:
        print("WARNING: No MRT test trials found!")
        return pd.DataFrame()
    
    # Create output DataFrame
    mrt_output = pd.DataFrame({
        'participantId': mrt_data['participantId'],
        'trial_number': mrt_data['MRT_trial'],
        'rotation_angle': mrt_data['MRT_angle_degrees'],
        'is_reflected': mrt_data['MRT_isReflected'],
        'response': mrt_data['MRT_response'],
        'is_correct': mrt_data['MRT_isCorrect'],
        'reaction_time_ms': mrt_data['MRT_rt_ms'],
        'is_attention_check': mrt_data['MRT_isAttentionCheck'],
        'trial_excluded': mrt_data['trial_excluded'],
        'exclusion_reason': mrt_data['exclusion_reason']
    })
    
    print(f"MRT output columns: {list(mrt_output.columns)}")
    print(f"First 2 rows of MRT output:")
    print(mrt_output.head(2))
    
    return mrt_output

def calculate_summary_metrics(df, vwm_rows, mrt_rows):
    """
    Calculate summary metrics for each participant.
    
    Args:
        df (pd.DataFrame): Data with exclusion info
        vwm_rows (pd.Series): Boolean mask for VWM rows
        mrt_rows (pd.Series): Boolean mask for MRT rows
        
    Returns:
        pd.DataFrame: Summary metrics per participant
    """
    print("\nCalculating summary metrics...")
    
    participants = df['participantId'].unique()
    participants = participants[~pd.isna(participants)]
    
    summary_data = []
    
    for participant in participants:
        print(f"Processing participant: {participant}")
        
        participant_data = df[df['participantId'] == participant]
        metrics = {'participantId': participant}
        
        # VWM metrics
        vwm_participant_rows = participant_data['VWM_trial'].notna()
        vwm_participant = participant_data[vwm_participant_rows]
        vwm_test_valid = vwm_participant[
            (vwm_participant['isPractice'] == False) & 
            (vwm_participant['trial_excluded'] == False)
        ]
        
        if len(vwm_test_valid) > 0:
            metrics['mean_vwm_absolute_error'] = vwm_test_valid['VWM_error_absolute_degrees'].mean()
            
            # VWM RT variability (coefficient of variation)
            vwm_rt_mean = vwm_test_valid['VWM_rt_ms'].mean()
            vwm_rt_std = vwm_test_valid['VWM_rt_ms'].std()
            metrics['vwm_rt_variability'] = vwm_rt_std / vwm_rt_mean if vwm_rt_mean > 0 else np.nan
        else:
            metrics['mean_vwm_absolute_error'] = np.nan
            metrics['vwm_rt_variability'] = np.nan
        
        # MRT metrics
        mrt_participant_rows = participant_data['MRT_trial'].notna()
        mrt_participant = participant_data[mrt_participant_rows]
        mrt_test_valid = mrt_participant[
            (mrt_participant['isPractice'] == False) & 
            (mrt_participant['trial_excluded'] == False)
        ]
        
        if len(mrt_test_valid) > 0:
            # Overall accuracy
            metrics['overall_mrt_accuracy'] = mrt_test_valid['MRT_isCorrect'].mean()
            
            # Accuracy by angle
            angles = [0, 50, 100, 150]
            for angle in angles:
                angle_data = mrt_test_valid[mrt_test_valid['MRT_angle_degrees'] == angle]
                if len(angle_data) > 0:
                    metrics[f'mrt_accuracy_{angle}deg'] = angle_data['MRT_isCorrect'].mean()
                else:
                    metrics[f'mrt_accuracy_{angle}deg'] = np.nan
            
            # Median RT by angle for correct trials
            mrt_correct = mrt_test_valid[mrt_test_valid['MRT_isCorrect'] == True]
            for angle in angles:
                angle_correct = mrt_correct[mrt_correct['MRT_angle_degrees'] == angle]
                if len(angle_correct) > 0:
                    metrics[f'mrt_median_rt_{angle}deg'] = angle_correct['MRT_rt_ms'].median()
                else:
                    metrics[f'mrt_median_rt_{angle}deg'] = np.nan
            
            # MRT RT variability
            mrt_rt_mean = mrt_test_valid['MRT_rt_ms'].mean()
            mrt_rt_std = mrt_test_valid['MRT_rt_ms'].std()
            metrics['mrt_rt_variability'] = mrt_rt_std / mrt_rt_mean if mrt_rt_mean > 0 else np.nan
        else:
            metrics['overall_mrt_accuracy'] = np.nan
            for angle in [0, 50, 100, 150]:
                metrics[f'mrt_accuracy_{angle}deg'] = np.nan
                metrics[f'mrt_median_rt_{angle}deg'] = np.nan
            metrics['mrt_rt_variability'] = np.nan
        
        summary_data.append(metrics)
    
    summary_df = pd.DataFrame(summary_data)
    
    print(f"Summary metrics columns: {list(summary_df.columns)}")
    print(f"First 2 rows of summary metrics:")
    print(summary_df.head(2))
    
    return summary_df

def save_outputs(vwm_data, mrt_data, summary_data, exclusion_stats):
    """
    Save all output files with timestamp.
    
    Args:
        vwm_data (pd.DataFrame): Processed VWM data
        mrt_data (pd.DataFrame): Processed MRT data
        summary_data (pd.DataFrame): Summary metrics
        exclusion_stats (dict): Exclusion statistics
    """
    print("\nSaving output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save VWM data
    if len(vwm_data) > 0:
        vwm_filename = f"outputs/VWM_cleaned_trial_data_{timestamp}.csv"
        vwm_data.to_csv(vwm_filename, index=False)
        print(f"Saved VWM data: {vwm_filename}")
    else:
        print("WARNING: No VWM data to save!")
    
    # Save MRT data
    if len(mrt_data) > 0:
        mrt_filename = f"outputs/MRT_cleaned_trial_data_{timestamp}.csv"
        mrt_data.to_csv(mrt_filename, index=False)
        print(f"Saved MRT data: {mrt_filename}")
    else:
        print("WARNING: No MRT data to save!")
    
    # Save summary metrics
    if len(summary_data) > 0:
        summary_filename = f"outputs/participant_summary_metrics_{timestamp}.csv"
        summary_data.to_csv(summary_filename, index=False)
        print(f"Saved summary metrics: {summary_filename}")
    else:
        print("WARNING: No summary data to save!")
    
    # Save exclusion statistics
    exclusion_filename = f"outputs/exclusion_statistics_{timestamp}.txt"
    with open(exclusion_filename, 'w') as f:
        f.write("TRIAL EXCLUSION STATISTICS\n")
        f.write("==========================\n\n")
        for key, value in exclusion_stats.items():
            f.write(f"{key}: {value}\n")
    
    print(f"Saved exclusion statistics: {exclusion_filename}")
    
    # Print exclusion statistics
    print("\n=== EXCLUSION STATISTICS ===")
    for key, value in exclusion_stats.items():
        print(f"{key}: {value}")

def main():
    """
    Main function to execute the data cleaning and processing pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("=== VWM and MRT Data Cleaning Pipeline ===")
        
        # 1. Load exclusion data
        exclusion_df = load_exclusion_data()
        if exclusion_df is None:
            return 1
        
        # 2. Load participant data
        data_df = load_participant_data()
        if data_df is None:
            return 1
        
        # 3. Filter to included participants
        filtered_df = filter_included_participants(data_df, exclusion_df)
        if len(filtered_df) == 0:
            print("ERROR: No data for included participants!")
            return 1
        
        # 4. Identify task rows
        vwm_rows, mrt_rows = identify_task_rows(filtered_df)
        
        # 5. Apply exclusions
        processed_df, exclusion_stats = apply_trial_exclusions(filtered_df, vwm_rows, mrt_rows)
        
        # 6. Process VWM data (ALL test trials, with exclusion status marked)
        vwm_output = process_vwm_data(processed_df, vwm_rows)
        
        # 7. Process MRT data (ALL test trials, with exclusion status marked)
        mrt_output = process_mrt_data(processed_df, mrt_rows)
        
        # 8. Calculate summary metrics (only valid trials)
        summary_output = calculate_summary_metrics(processed_df, vwm_rows, mrt_rows)
        
        # 9. Save outputs
        save_outputs(vwm_output, mrt_output, summary_output, exclusion_stats)
        
        # === FINAL SUMMARY PRINTOUT ===
        print("\n=== FINAL SUMMARY ===")
        # Initial participant counts
        total_participants = len(exclusion_df)
        included_participants = exclusion_df['included'].sum()
        print(f"Total participants in exclusion file: {total_participants}")
        print(f"Included participants: {included_participants}")
        
        # Total trials loaded and processed
        total_trials_loaded = len(filtered_df)
        print(f"Total trials loaded for included participants: {total_trials_loaded}")
        
        # VWM and MRT test trial counts (before exclusions)
        vwm_test_trials = (vwm_rows & (filtered_df['isPractice'] == False)).sum()
        mrt_test_trials = (mrt_rows & (filtered_df['isPractice'] == False)).sum()
        print(f"Total VWM test trials (before exclusions): {vwm_test_trials}")
        print(f"Total MRT test trials (before exclusions): {mrt_test_trials}")
        
        # Breakdown of trial exclusions by type
        print("\nTrial exclusions by type:")
        for key, value in exclusion_stats.items():
            print(f"  {key}: {value}")
        
        # Final valid trial counts for both tasks
        vwm_valid_trials = (vwm_rows & (filtered_df['isPractice'] == False) & (processed_df['trial_excluded'] == False)).sum()
        mrt_valid_trials = (mrt_rows & (filtered_df['isPractice'] == False) & (processed_df['trial_excluded'] == False)).sum()
        print(f"\nFinal valid VWM test trials: {vwm_valid_trials}")
        print(f"Final valid MRT test trials: {mrt_valid_trials}")
        
        # Final participant counts in output files
        vwm_participants_final = processed_df.loc[
            (vwm_rows) & (processed_df['isPractice'] == False) & (processed_df['trial_excluded'] == False),
            'participantId'
        ].nunique()
        mrt_participants_final = processed_df.loc[
            (mrt_rows) & (processed_df['isPractice'] == False) & (processed_df['trial_excluded'] == False),
            'participantId'
        ].nunique()
        print(f"Participants with valid VWM test trials: {vwm_participants_final}")
        print(f"Participants with valid MRT test trials: {mrt_participants_final}")
        print(f"Participants in summary metrics: {summary_output['participantId'].nunique()}")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
