import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

def load_retained_participants(timestamp_pattern="outputs/retained_participants_*.csv"):
    """
    Load the most recent retained participants file.
    
    Parameters:
    timestamp_pattern (str): File pattern to match retained participants files
    
    Returns:
    pd.DataFrame: DataFrame containing participantId and included columns for retained participants
    """
    print("Loading retained participants...")
    
    # Find all matching files
    files = glob.glob(timestamp_pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {timestamp_pattern}")
    
    # Get the most recent file
    latest_file = max(files, key=os.path.getctime)
    print(f"Using retained participants file: {latest_file}")
    
    # Load the file
    df = pd.read_csv(latest_file)
    print(f"Loaded retained participants data with columns: {list(df.columns)}")
    print(f"First 3 rows:")
    print(df.head(3))
    
    # Filter to only included participants
    retained = df[df['included'] == True]['participantId'].tolist()
    print(f"Number of retained participants: {len(retained)}")
    print(f"Retained participant IDs: {retained}")
    
    return retained

def load_raw_trial_data(retained_participants):
    """
    Load and combine raw trial data for retained participants.
    
    Parameters:
    retained_participants (list): List of participant IDs to include
    
    Returns:
    pd.DataFrame: Combined trial data for all retained participants
    """
    print("Loading raw trial data...")
    
    # Find all participant data files
    data_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    all_files = glob.glob(data_pattern)
    print(f"Found {len(all_files)} total participant data files")
    
    combined_data = []
    
    for file_path in all_files:
        # Extract participant ID from filename
        filename = os.path.basename(file_path)
        # Look for PARTICIPANT_XXX pattern
        if "PARTICIPANT_" in filename:
            parts = filename.split("_")
            for i, part in enumerate(parts):
                if part == "PARTICIPANT" and i+1 < len(parts):
                    participant_id = parts[i+1]
                    break
            else:
                print(f"Could not extract participant ID from {filename}")
                continue
        else:
            print(f"Unexpected filename format: {filename}")
            continue
        
        # Only load data for retained participants
        if participant_id in retained_participants:
            print(f"Loading data for participant {participant_id} from {filename}")
            try:
                df = pd.read_csv(file_path)
                print(f"Columns in {filename}: {list(df.columns)}")
                print(f"First 3 rows:")
                print(df.head(3))
                
                # Add participant ID if not present
                if 'participantId' not in df.columns:
                    df['participantId'] = participant_id
                
                combined_data.append(df)
                print(f"Loaded {len(df)} rows for participant {participant_id}")
                
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                continue
    
    if not combined_data:
        raise ValueError("No valid data files loaded")
    
    # Combine all data
    all_data = pd.concat(combined_data, ignore_index=True)
    print(f"Combined data shape: {all_data.shape}")
    print(f"Combined data columns: {list(all_data.columns)}")
    print(f"First 2 rows of combined data:")
    print(all_data.head(2))
    
    return all_data

def identify_task_rows(df):
    """
    Identify which rows belong to VWM vs MRT tasks.
    
    Parameters:
    df (pd.DataFrame): Combined trial data
    
    Returns:
    tuple: (vwm_mask, mrt_mask) - boolean masks for VWM and MRT trials
    """
    print("Identifying task-specific rows...")
    
    # VWM rows have non-null VWM_trial
    vwm_mask = df['VWM_trial'].notna()
    # MRT rows have non-null MRT_trial  
    mrt_mask = df['MRT_trial'].notna()
    
    print(f"VWM trials: {vwm_mask.sum()}")
    print(f"MRT trials: {mrt_mask.sum()}")
    print(f"Total rows: {len(df)}")
    
    # Check for overlap (should be none in interleaved design)
    overlap = (vwm_mask & mrt_mask).sum()
    print(f"Overlapping trials (should be 0): {overlap}")
    
    return vwm_mask, mrt_mask

def apply_rt_exclusions(df, vwm_mask, mrt_mask):
    """
    Apply reaction time exclusions to both VWM and MRT data.
    
    Parameters:
    df (pd.DataFrame): Trial data
    vwm_mask (pd.Series): Boolean mask for VWM trials
    mrt_mask (pd.Series): Boolean mask for MRT trials
    
    Returns:
    tuple: (exclusion_counts, updated_masks)
    """
    print("Applying reaction time exclusions...")
    
    exclusion_counts = {
        'rt_under_200ms_vwm': 0,
        'rt_under_200ms_mrt': 0,
        'rt_outlier_vwm': 0,
        'rt_outlier_mrt': 0
    }
    
    # Create copies of masks to track exclusions
    vwm_valid = vwm_mask.copy()
    mrt_valid = mrt_mask.copy()
    
    # VWM RT exclusions - vectorized approach
    print("Processing VWM RT exclusions...")
    vwm_under_200 = (df['VWM_rt_ms'] < 200) & vwm_mask
    exclusion_counts['rt_under_200ms_vwm'] = vwm_under_200.sum()
    print(f"VWM trials with RT < 200ms: {exclusion_counts['rt_under_200ms_vwm']}")
    vwm_valid[vwm_under_200] = False

    # VWM outlier detection - vectorized
    vwm_for_outlier = vwm_valid & (df['VWM_rt_ms'] >= 200)
    if vwm_for_outlier.sum() > 0:
        rt_stats = df.loc[vwm_for_outlier].groupby('participantId')['VWM_rt_ms'].agg(['mean', 'std'])
        df_temp = df.join(rt_stats, on='participantId', rsuffix='_stats')
        outlier_threshold = df_temp['mean'] + 3 * df_temp['std']
        vwm_outlier_mask = (df['VWM_rt_ms'] > outlier_threshold) & vwm_valid & df_temp['std'].notna()
        exclusion_counts['rt_outlier_vwm'] = vwm_outlier_mask.sum()
        print(f"VWM RT outlier trials: {exclusion_counts['rt_outlier_vwm']}")
        vwm_valid[vwm_outlier_mask] = False
    else:
        print("No VWM trials eligible for outlier exclusion.")

    # MRT RT exclusions - vectorized approach
    print("Processing MRT RT exclusions...")
    mrt_under_200 = (df['MRT_rt_ms'] < 200) & mrt_mask
    exclusion_counts['rt_under_200ms_mrt'] = mrt_under_200.sum()
    print(f"MRT trials with RT < 200ms: {exclusion_counts['rt_under_200ms_mrt']}")
    mrt_valid[mrt_under_200] = False

    # MRT outlier detection - vectorized
    mrt_for_outlier = mrt_valid & (df['MRT_rt_ms'] >= 200)
    if mrt_for_outlier.sum() > 0:
        rt_stats = df.loc[mrt_for_outlier].groupby('participantId')['MRT_rt_ms'].agg(['mean', 'std'])
        df_temp = df.join(rt_stats, on='participantId', rsuffix='_stats')
        outlier_threshold = df_temp['mean'] + 3 * df_temp['std']
        mrt_outlier_mask = (df['MRT_rt_ms'] > outlier_threshold) & mrt_valid & df_temp['std'].notna()
        exclusion_counts['rt_outlier_mrt'] = mrt_outlier_mask.sum()
        print(f"MRT RT outlier trials: {exclusion_counts['rt_outlier_mrt']}")
        mrt_valid[mrt_outlier_mask] = False
    else:
        print("No MRT trials eligible for outlier exclusion.")

    return exclusion_counts, vwm_valid, mrt_valid

def apply_vwm_exclusions(df, vwm_mask):
    """
    Apply VWM-specific trial exclusions.
    
    Parameters:
    df (pd.DataFrame): Trial data
    vwm_mask (pd.Series): Boolean mask for VWM trials
    
    Returns:
    tuple: (exclusion_counts, updated_mask)
    """
    print("Applying VWM-specific exclusions...")
    
    exclusion_counts = {
        'vwm_timeout': 0,
        'vwm_missing_response': 0,
        'vwm_impossible_response': 0
    }
    
    vwm_valid = vwm_mask.copy()
    
    # Timeout exclusions first
    timeout_mask = (df['VWM_timeout'] == True) & vwm_valid
    exclusion_counts['vwm_timeout'] = timeout_mask.sum()
    print(f"VWM timeout trials: {exclusion_counts['vwm_timeout']}")
    vwm_valid[timeout_mask] = False
    
    # Missing response exclusions on remaining valid trials
    missing_response_mask = df['VWM_responseAngle_degrees'].isna() & vwm_valid
    exclusion_counts['vwm_missing_response'] = missing_response_mask.sum()
    print(f"VWM missing response trials: {exclusion_counts['vwm_missing_response']}")
    vwm_valid[missing_response_mask] = False
    
    # Impossible response exclusions on remaining valid trials
    impossible_response_mask = ((df['VWM_responseAngle_degrees'] < 0) | 
                               (df['VWM_responseAngle_degrees'] > 360)) & vwm_valid
    exclusion_counts['vwm_impossible_response'] = impossible_response_mask.sum()
    print(f"VWM impossible response trials: {exclusion_counts['vwm_impossible_response']}")
    vwm_valid[impossible_response_mask] = False
    
    return exclusion_counts, vwm_valid

def apply_mrt_exclusions(df, mrt_mask):
    """
    Apply MRT-specific trial exclusions.
    
    Parameters:
    df (pd.DataFrame): Trial data
    mrt_mask (pd.Series): Boolean mask for MRT trials
    
    Returns:
    tuple: (exclusion_counts, updated_mask)
    """
    print("Applying MRT-specific exclusions...")
    
    exclusion_counts = {
        'mrt_timeout': 0,
        'mrt_rt_over_7000ms': 0,
        'mrt_missing_response': 0
    }
    
    mrt_valid = mrt_mask.copy()
    
    # Timeout exclusions first
    timeout_mask = (df['MRT_timeout'] == True) & mrt_valid
    exclusion_counts['mrt_timeout'] = timeout_mask.sum()
    print(f"MRT timeout trials: {exclusion_counts['mrt_timeout']}")
    mrt_valid[timeout_mask] = False
    
    # RT > 7000ms exclusions on remaining valid trials
    rt_over_7000_mask = (df['MRT_rt_ms'] > 7000) & mrt_valid
    exclusion_counts['mrt_rt_over_7000ms'] = rt_over_7000_mask.sum()
    print(f"MRT RT > 7000ms trials: {exclusion_counts['mrt_rt_over_7000ms']}")
    mrt_valid[rt_over_7000_mask] = False
    
    # Missing response exclusions on remaining valid trials
    missing_response_mask = df['MRT_response'].isna() & mrt_valid
    exclusion_counts['mrt_missing_response'] = missing_response_mask.sum()
    print(f"MRT missing response trials: {exclusion_counts['mrt_missing_response']}")
    mrt_valid[missing_response_mask] = False
    
    return exclusion_counts, mrt_valid

def validate_cleaned_data(df, vwm_valid, mrt_valid):
    """
    Validate cleaned data and check for sufficient trials.
    
    Parameters:
    df (pd.DataFrame): Trial data
    vwm_valid (pd.Series): Valid VWM trials mask
    mrt_valid (pd.Series): Valid MRT trials mask
    
    Returns:
    dict: Validation results
    """
    print("Validating cleaned data...")
    
    validation_results = {}
    
    # Get valid data
    vwm_data = df[vwm_valid]
    mrt_data = df[mrt_valid]
    
    print(f"Valid VWM trials: {len(vwm_data)}")
    print(f"Valid MRT trials: {len(mrt_data)}")
    
    # Check practice vs test trials
    if 'isPractice' in vwm_data.columns:
        vwm_practice = vwm_data[vwm_data['isPractice'] == True]
        vwm_test = vwm_data[vwm_data['isPractice'] == False]
        print(f"VWM practice trials: {len(vwm_practice)}")
        print(f"VWM test trials: {len(vwm_test)}")
        
        print("VWM unique values for key design parameters:")
        if 'VWM_setSize' in vwm_data.columns:
            print(f"VWM_setSize: {sorted(vwm_data['VWM_setSize'].unique())}")
        if 'VWM_delay_s' in vwm_data.columns:
            print(f"VWM_delay_s: {sorted(vwm_data['VWM_delay_s'].unique())}")
        if 'VWM_block' in vwm_data.columns:
            print(f"VWM_block: {sorted(vwm_data['VWM_block'].dropna().unique())}")
    
    if 'isPractice' in mrt_data.columns:
        mrt_practice = mrt_data[mrt_data['isPractice'] == True]
        mrt_test = mrt_data[mrt_data['isPractice'] == False]
        print(f"MRT practice trials: {len(mrt_practice)}")
        print(f"MRT test trials: {len(mrt_test)}")
        
        print("MRT unique values for key design parameters:")
        if 'MRT_angle_degrees' in mrt_data.columns:
            print(f"MRT_angle_degrees: {sorted(mrt_data['MRT_angle_degrees'].unique())}")
        if 'MRT_isReflected' in mrt_data.columns:
            print(f"MRT_isReflected: {sorted(mrt_data['MRT_isReflected'].unique())}")
        if 'MRT_block' in mrt_data.columns:
            print(f"MRT_block: {sorted(mrt_data['MRT_block'].dropna().unique())}")
    
    # Check trial counts per participant
    participants = df['participantId'].unique()
    validation_results['participant_trial_counts'] = {}
    
    for participant in participants:
        p_vwm = vwm_data[vwm_data['participantId'] == participant]
        p_mrt = mrt_data[mrt_data['participantId'] == participant]
        
        validation_results['participant_trial_counts'][participant] = {
            'vwm_trials': len(p_vwm),
            'mrt_trials': len(p_mrt)
        }
        
        print(f"Participant {participant}: VWM={len(p_vwm)}, MRT={len(p_mrt)}")
    
    return validation_results

def create_exclusion_summary(rt_exclusions, vwm_exclusions, mrt_exclusions):
    """
    Create trial exclusion summary.
    
    Parameters:
    rt_exclusions (dict): RT exclusion counts
    vwm_exclusions (dict): VWM exclusion counts  
    mrt_exclusions (dict): MRT exclusion counts
    
    Returns:
    pd.DataFrame: Exclusion summary
    """
    print("Creating exclusion summary...")
    
    summary_data = []
    
    # RT exclusions
    summary_data.append({
        'exclusion_criterion': 'RT under 200ms',
        'vwm_excluded_trials': rt_exclusions['rt_under_200ms_vwm'],
        'mrt_excluded_trials': rt_exclusions['rt_under_200ms_mrt']
    })
    
    summary_data.append({
        'exclusion_criterion': 'RT outlier (>3SD)',
        'vwm_excluded_trials': rt_exclusions['rt_outlier_vwm'],
        'mrt_excluded_trials': rt_exclusions['rt_outlier_mrt']
    })
    
    # VWM-specific exclusions
    summary_data.append({
        'exclusion_criterion': 'Timeout',
        'vwm_excluded_trials': vwm_exclusions['vwm_timeout'],
        'mrt_excluded_trials': mrt_exclusions['mrt_timeout']
    })
    
    summary_data.append({
        'exclusion_criterion': 'Missing response',
        'vwm_excluded_trials': vwm_exclusions['vwm_missing_response'],
        'mrt_excluded_trials': mrt_exclusions['mrt_missing_response']
    })
    
    summary_data.append({
        'exclusion_criterion': 'Impossible response',
        'vwm_excluded_trials': vwm_exclusions['vwm_impossible_response'],
        'mrt_excluded_trials': 0  # No impossible response criterion for MRT
    })
    
    summary_data.append({
        'exclusion_criterion': 'RT over 7000ms',
        'vwm_excluded_trials': 0,  # No such criterion for VWM
        'mrt_excluded_trials': mrt_exclusions['mrt_rt_over_7000ms']
    })
    
    summary_df = pd.DataFrame(summary_data)
    print("Exclusion summary:")
    print(summary_df)
    
    return summary_df

def main():
    """
    Main function to execute the trial exclusion pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting trial exclusion pipeline...")
        
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Load retained participants
        retained_participants = load_retained_participants()
        
        # Load raw trial data
        all_data = load_raw_trial_data(retained_participants)
        
        # Identify task-specific rows
        vwm_mask, mrt_mask = identify_task_rows(all_data)
        
        # Apply RT exclusions
        rt_exclusions, vwm_valid, mrt_valid = apply_rt_exclusions(all_data, vwm_mask, mrt_mask)
        
        # Apply VWM-specific exclusions
        vwm_exclusions, vwm_valid = apply_vwm_exclusions(all_data, vwm_valid)
        
        # Apply MRT-specific exclusions
        mrt_exclusions, mrt_valid = apply_mrt_exclusions(all_data, mrt_valid)
        
        # Validate cleaned data
        validation_results = validate_cleaned_data(all_data, vwm_valid, mrt_valid)
        
        # Create final cleaned dataset
        final_valid = vwm_valid | mrt_valid
        cleaned_data = all_data[final_valid].copy()
        
        print(f"Final cleaned dataset shape: {cleaned_data.shape}")
        print(f"Final cleaned dataset columns: {list(cleaned_data.columns)}")
        print(f"First 2 rows of cleaned data:")
        print(cleaned_data.head(2))
        
        # Create exclusion summary
        exclusion_summary = create_exclusion_summary(rt_exclusions, vwm_exclusions, mrt_exclusions)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save outputs
        exclusion_file = f"outputs/trial_exclusion_log_{timestamp}.csv"
        cleaned_file = f"outputs/cleaned_trial_data_{timestamp}.csv"
        
        print(f"Saving exclusion summary to: {exclusion_file}")
        exclusion_summary.to_csv(exclusion_file, index=False)
        
        print(f"Saving cleaned trial data to: {cleaned_file}")
        cleaned_data.to_csv(cleaned_file, index=False)

        # Calculate and print final summary
        print("\n" + "="*60)
        print("FINAL DATA CLEANING SUMMARY")
        print("="*60)

        initial_vwm = vwm_mask.sum()
        initial_mrt = mrt_mask.sum()
        final_vwm = vwm_valid.sum()
        final_mrt = mrt_valid.sum()

        print(f"Initial VWM trials: {initial_vwm}")
        print(f"Initial MRT trials: {initial_mrt}")
        print(f"Total initial trials: {initial_vwm + initial_mrt}")
        print()

        # Print exclusion details
        total_vwm_excluded = initial_vwm - final_vwm
        total_mrt_excluded = initial_mrt - final_mrt

        print("Exclusions by criterion:")
        # RT exclusions
        print(f"  rt_under_200ms_vwm: {rt_exclusions['rt_under_200ms_vwm']} VWM trials")
        print(f"  rt_outlier_vwm: {rt_exclusions['rt_outlier_vwm']} VWM trials")
        print(f"  rt_under_200ms_mrt: {rt_exclusions['rt_under_200ms_mrt']} MRT trials")
        print(f"  rt_outlier_mrt: {rt_exclusions['rt_outlier_mrt']} MRT trials")
        # VWM-specific
        print(f"  vwm_timeout: {vwm_exclusions['vwm_timeout']} VWM trials")
        print(f"  vwm_missing_response: {vwm_exclusions['vwm_missing_response']} VWM trials")
        print(f"  vwm_impossible_response: {vwm_exclusions['vwm_impossible_response']} VWM trials")
        # MRT-specific
        print(f"  mrt_timeout: {mrt_exclusions['mrt_timeout']} MRT trials")
        print(f"  mrt_rt_over_7000ms: {mrt_exclusions['mrt_rt_over_7000ms']} MRT trials")
        print(f"  mrt_missing_response: {mrt_exclusions['mrt_missing_response']} MRT trials")

        print()
        print(f"Final VWM trials: {final_vwm}")
        print(f"Final MRT trials: {final_mrt}")
        print(f"Total final trials: {final_vwm + final_mrt}")

        print("Pipeline completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in trial exclusion pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
