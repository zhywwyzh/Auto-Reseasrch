import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

def get_most_recent_file(pattern):
    """
    Get the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def load_task_data_files(pattern):
    """
    Load all task data files matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    pd.DataFrame: Combined dataframe from all matching files
    """
    files = glob.glob(pattern)
    print(f"Found {len(files)} task data files matching pattern: {pattern}")
    
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    all_data = []
    for file in files:
        print(f"Loading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File {file} loaded with {len(df)} rows and {len(df.columns)} columns")
            all_data.append(df)
        except Exception as e:
            print(f"Error loading file {file}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No valid data files could be loaded")
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined dataframe has {len(combined_df)} rows and {len(combined_df.columns)} columns")
    
    return combined_df

def validate_required_columns(df, required_columns, file_type):
    """
    Validate that all required columns are present in the dataframe.
    
    Parameters:
    df (pd.DataFrame): Dataframe to validate
    required_columns (list): List of required column names
    file_type (str): Type of file being validated for error messages
    
    Returns:
    bool: True if all required columns are present
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"WARNING: Missing required columns in {file_type}: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    print(f"All required columns present in {file_type}")
    return True

def normalize_error_degrees(error_degrees):
    """
    Normalize error degrees to ±90° range to account for orientation equivalence.
    
    Parameters:
    error_degrees (float): Raw error in degrees
    
    Returns:
    float: Normalized error in ±90° range
    """
    if pd.isna(error_degrees):
        return np.nan
    
    # Normalize to ±90° range
    if error_degrees > 90:
        return error_degrees - 180
    elif error_degrees < -90:
        return error_degrees + 180
    else:
        return error_degrees

def apply_vwm_exclusions(df):
    """
    Apply VWM trial-level exclusions and calculate recall errors in a cascading manner.
    
    Parameters:
    df (pd.DataFrame): VWM trial data
    
    Returns:
    pd.DataFrame: Dataframe with exclusion flags and calculated errors
    """
    print("Applying VWM trial-level exclusions...")
    
    # Initialize exclusion flags
    df['excluded_timeout'] = False
    df['excluded_anticipatory_response'] = False
    df['excluded_extremely_slow_response'] = False
    df['excluded_invalid_response'] = False
    df['excluded_attention_check_failure'] = False
    
    # Initialize master exclusion tracker
    is_excluded = pd.Series(False, index=df.index)
    
    # a. Timeout exclusions
    timeout_mask = df['VWM_timeout'] == True
    df.loc[timeout_mask, 'excluded_timeout'] = True
    is_excluded |= timeout_mask
    print(f"Timeout exclusions: {timeout_mask.sum()} trials")
    
    # b. Anticipatory response exclusions (only on remaining trials)
    anticipatory_mask = (df['VWM_rt_ms'] < 200) & (~is_excluded)
    df.loc[anticipatory_mask, 'excluded_anticipatory_response'] = True
    is_excluded |= anticipatory_mask
    print(f"Anticipatory response exclusions: {anticipatory_mask.sum()} trials")
    
    # c. Extremely slow response exclusions (only on remaining trials)
    slow_mask = (df['VWM_rt_ms'] > 10000) & (~is_excluded)
    df.loc[slow_mask, 'excluded_extremely_slow_response'] = True
    is_excluded |= slow_mask
    print(f"Extremely slow response exclusions: {slow_mask.sum()} trials")
    
    # d. Invalid response exclusions (only on remaining trials)
    invalid_response_mask = (
        (df['VWM_responseAngle_degrees'].isna() |
         (df['VWM_responseAngle_degrees'] < 0) |
         (df['VWM_responseAngle_degrees'] > 360)) & (~is_excluded)
    )
    df.loc[invalid_response_mask, 'excluded_invalid_response'] = True
    is_excluded |= invalid_response_mask
    print(f"Invalid response exclusions: {invalid_response_mask.sum()} trials")
    
    # e. Attention check failure exclusions (only on remaining trials)
    attention_check_mask = (
        (df['VWM_isAttentionCheck'] == True) &
        (df['VWM_error_absolute_degrees'] > 15) & (~is_excluded)
    )
    df.loc[attention_check_mask, 'excluded_attention_check_failure'] = True
    is_excluded |= attention_check_mask
    print(f"Attention check failure exclusions: {attention_check_mask.sum()} trials")
    
    # Calculate trial validity based on master exclusion flag
    df['trial_valid'] = ~is_excluded
    
    print(f"Valid trials: {df['trial_valid'].sum()}/{len(df)} ({df['trial_valid'].mean()*100:.1f}%)")
    
    # Calculate signed recall error with normalization
    print("Calculating normalized signed recall errors...")
    df['signed_error_degrees'] = df['VWM_error_degrees'].apply(normalize_error_degrees)
    
    # Calculate absolute error
    df['absolute_error_degrees'] = df['signed_error_degrees'].abs()
    
    return df

def create_exclusion_summary(df):
    """
    Create summary of trial exclusions.
    
    Parameters:
    df (pd.DataFrame): Dataframe with exclusion flags
    
    Returns:
    pd.DataFrame: Summary of exclusions
    """
    exclusion_criteria = [
        'excluded_timeout',
        'excluded_anticipatory_response',
        'excluded_extremely_slow_response',
        'excluded_invalid_response',
        'excluded_attention_check_failure'
    ]
    
    exclusion_summary = []
    total_trials = len(df)
    
    for criterion in exclusion_criteria:
        count_excluded = df[criterion].sum()
        exclusion_percentage = (count_excluded / total_trials) * 100
        
        exclusion_summary.append({
            'exclusion_criterion': criterion.replace('excluded_', ''),
            'count_excluded': count_excluded,
            'total_trials_assessed': total_trials,
            'exclusion_percentage': exclusion_percentage
        })
    
    return pd.DataFrame(exclusion_summary)

def main():
    """
    Main function to process VWM data and apply exclusions.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print("Starting VWM data cleaning and exclusion process...")
        
        # Load inclusion status file
        print("\n=== Loading participant inclusion status ===")
        inclusion_pattern = "outputs/participant_inclusion_status_*.csv"
        inclusion_file = get_most_recent_file(inclusion_pattern)
        print(f"Loading inclusion status from: {inclusion_file}")
        
        inclusion_df = pd.read_csv(inclusion_file)
        print(f"Inclusion status file loaded with {len(inclusion_df)} rows and {len(inclusion_df.columns)} columns")
        print("Columns:", list(inclusion_df.columns))
        print("First 3 rows:")
        print(inclusion_df.head(3))
        
        # Validate inclusion file columns
        required_inclusion_columns = ['participantId', 'included']
        if not validate_required_columns(inclusion_df, required_inclusion_columns, "inclusion status file"):
            return 1
        
        # Get list of included participants
        included_participants = inclusion_df[inclusion_df['included'] == True]['participantId'].tolist()
        print(f"\nIncluded participants: {len(included_participants)} out of {len(inclusion_df)}")
        print("Included participant IDs:", included_participants)
        
        # Load task data files
        print("\n=== Loading task data files ===")
        task_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        task_df = load_task_data_files(task_pattern)
        
        # Store counts for final summary
        initial_total_rows = len(task_df)
        initial_participants = task_df['participantId'].nunique()
        initial_vwm_trials = len(task_df[task_df['VWM_trial'].notna()])
        
        print("Task data columns:", list(task_df.columns))
        print("First 3 rows:")
        print(task_df.head(3))
        
        # Validate task data columns
        required_task_columns = [
            'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_setSize',
            'VWM_delay_s', 'VWM_cueIndex', 'VWM_orientations_degrees',
            'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees',
            'VWM_error_degrees', 'VWM_error_absolute_degrees', 'VWM_rt_ms',
            'VWM_timeout', 'VWM_block', 'VWM_isAttentionCheck'
        ]
        
        if not validate_required_columns(task_df, required_task_columns, "task data files"):
            return 1
        
        # Print unique values for key experimental design parameters
        print("\n=== Key experimental design parameters ===")
        print("Unique values in 'table':", sorted(task_df['table'].dropna().unique()))
        print("Unique values in 'isPractice':", sorted(task_df['isPractice'].dropna().unique()))
        print("Unique values in 'VWM_setSize':", sorted(task_df['VWM_setSize'].dropna().unique()))
        print("Unique values in 'VWM_delay_s':", sorted(task_df['VWM_delay_s'].dropna().unique()))
        print("Unique values in 'VWM_block':", sorted(task_df['VWM_block'].dropna().unique()))
        print("Unique values in 'VWM_isAttentionCheck':", sorted(task_df['VWM_isAttentionCheck'].dropna().unique()))
        
        # Print data types for measured variables
        print("\n=== Measured variable data types ===")
        print("VWM_responseAngle_degrees type:", task_df['VWM_responseAngle_degrees'].dtype)
        print("VWM_targetAngle_degrees type:", task_df['VWM_targetAngle_degrees'].dtype)
        print("VWM_rt_ms type:", task_df['VWM_rt_ms'].dtype)
        print("VWM_error_degrees type:", task_df['VWM_error_degrees'].dtype)
        
        # Filter to VWM trials only (identify VWM-specific rows)
        print("\n=== Identifying VWM trials ===")
        # VWM trials are those where VWM_trial is not null
        vwm_mask = task_df['VWM_trial'].notna()
        vwm_df = task_df[vwm_mask].copy()
        print(f"VWM trials identified: {len(vwm_df)} out of {len(task_df)} total rows")
        
        # Filter to included participants only
        print("\n=== Filtering to included participants ===")
        vwm_df = vwm_df[vwm_df['participantId'].isin(included_participants)].copy()
        print(f"VWM trials for included participants: {len(vwm_df)}")
        
        if len(vwm_df) == 0:
            print("ERROR: No VWM trials found for included participants")
            return 1
        
        # Apply exclusions and calculate errors
        print("\n=== Applying exclusions and calculating errors ===")
        vwm_df = apply_vwm_exclusions(vwm_df)
        
        # Separate practice and test trials
        print("\n=== Separating practice and test trials ===")
        practice_mask = (vwm_df['table'] == 'vwm_practice') | (vwm_df['isPractice'] == True)
        test_mask = (vwm_df['table'] == 'vwm_test') | (vwm_df['isPractice'] == False)
        
        print(f"Practice trials: {practice_mask.sum()}")
        print(f"Test trials: {test_mask.sum()}")
        
        # Determine trial type
        vwm_df['trial_type'] = 'unknown'
        vwm_df.loc[practice_mask, 'trial_type'] = 'practice'
        vwm_df.loc[test_mask, 'trial_type'] = 'test'
        
        print("Trial type distribution:")
        print(vwm_df['trial_type'].value_counts())
        
        # Create output dataframe with required columns
        print("\n=== Creating output dataframe ===")
        output_df = pd.DataFrame({
            'participantId': vwm_df['participantId'],
            'trial_number': vwm_df['VWM_trial'],
            'set_size': vwm_df['VWM_setSize'],
            'delay_seconds': vwm_df['VWM_delay_s'],
            'cue_index': vwm_df['VWM_cueIndex'],
            'target_angle_degrees': vwm_df['VWM_targetAngle_degrees'],
            'response_angle_degrees': vwm_df['VWM_responseAngle_degrees'],
            'signed_error_degrees': vwm_df['signed_error_degrees'],
            'absolute_error_degrees': vwm_df['absolute_error_degrees'],
            'response_time_ms': vwm_df['VWM_rt_ms'],
            'trial_type': vwm_df['trial_type'],
            'block_number': vwm_df['VWM_block'],
            'is_attention_check': vwm_df['VWM_isAttentionCheck'],
            'excluded_timeout': vwm_df['excluded_timeout'],
            'excluded_anticipatory_response': vwm_df['excluded_anticipatory_response'],
            'excluded_extremely_slow_response': vwm_df['excluded_extremely_slow_response'],
            'excluded_invalid_response': vwm_df['excluded_invalid_response'],
            'excluded_attention_check_failure': vwm_df['excluded_attention_check_failure'],
            'trial_valid': vwm_df['trial_valid']
        })
        
        print("Output dataframe created with columns:", list(output_df.columns))
        print("First 2 rows of output dataframe:")
        print(output_df.head(2))
        
        # Create exclusion summary
        print("\n=== Creating exclusion summary ===")
        exclusion_summary = create_exclusion_summary(vwm_df)
        print("Exclusion summary:")
        print(exclusion_summary)
        
        # Save output files
        print("\n=== Saving output files ===")
        
        # Save cleaned trial data
        output_file = f"outputs/VWM_cleaned_trial_data_{timestamp}.csv"
        output_df.to_csv(output_file, index=False)
        print(f"Cleaned trial data saved to: {output_file}")
        print(f"Output file contains {len(output_df)} rows and {len(output_df.columns)} columns")
        
        # Save exclusion log
        exclusion_file = f"outputs/VWM_trial_exclusion_log_{timestamp}.csv"
        exclusion_summary.to_csv(exclusion_file, index=False)
        print(f"Exclusion log saved to: {exclusion_file}")
        
        # Print final summary
        print("\n=== Final Summary ===")
        print(f"Total VWM trials processed: {len(vwm_df)}")
        print(f"Valid trials: {output_df['trial_valid'].sum()}")
        print(f"Invalid trials: {(~output_df['trial_valid']).sum()}")
        print(f"Overall validity rate: {output_df['trial_valid'].mean()*100:.1f}%")
        
        # Summary by participant
        participant_summary = output_df.groupby('participantId').agg({
            'trial_valid': ['count', 'sum', 'mean']
        }).round(3)
        participant_summary.columns = ['total_trials', 'valid_trials', 'validity_rate']
        print("\nParticipant-level summary:")
        print(participant_summary)
        
        # Add comprehensive data cleaning summary
        print("\n=== DATA CLEANING SUMMARY ===")
        print(f"1) Initial data loaded: {initial_total_rows} total rows from {initial_participants} participants")
        print(f"   - Identified {initial_vwm_trials} VWM trials across all participants")
        print(f"2) Participant-level filtering: Retained {len(included_participants)} participants for analysis")
        print(f"   - Processing {len(vwm_df)} VWM trials from included participants")
        print("3) Trial-level exclusions (cascading):")
        total_excluded_trials = 0
        for _, row in exclusion_summary.iterrows():
            count = int(row['count_excluded'])
            total_excluded_trials += count
            print(f"   - {count} trials removed for: {row['exclusion_criterion']}")
        print(f"   - Total trials excluded: {total_excluded_trials}")
        print(f"4) Final dataset: {output_df['trial_valid'].sum()} valid trials from {len(included_participants)} participants")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
