import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match, with <TIMESTAMP> placeholder
    
    Returns:
    str: Path to the most recent matching file, or None if no files found
    """
    # Convert pattern to glob pattern
    glob_pattern = pattern.replace('<TIMESTAMP>', '*')
    
    # Find all matching files
    matching_files = glob.glob(glob_pattern)
    
    if not matching_files:
        return None
    
    # Get the most recent file based on modification time
    most_recent = max(matching_files, key=os.path.getmtime)
    return most_recent

def normalize_vwm_error(error_degrees):
    """
    Normalize VWM error to ±90° range.
    
    Parameters:
    error_degrees (float): Original error in degrees
    
    Returns:
    float: Normalized error in ±90° range
    """
    if pd.isna(error_degrees):
        return error_degrees
    
    if error_degrees > 90:
        return error_degrees - 180
    elif error_degrees < -90:
        return error_degrees + 180
    else:
        return error_degrees

def apply_trial_exclusions(df):
    """
    Apply trial-level exclusions for both VWM and MRT tasks, using cascaded counting and vectorized operations.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with trial data
    
    Returns:
    tuple: (cleaned_df, exclusion_log)
        cleaned_df (pd.DataFrame): Dataframe with exclusion flags added
        exclusion_log (list): List of exclusion statistics
    """
    print("Applying trial-level exclusions...")

    # Convert boolean-like columns to pandas nullable boolean type
    bool_cols = [
        'isPractice', 'VWM_timeout', 'VWM_isAttentionCheck', 'MRT_timeout', 'MRT_isCorrect', 'MRT_isAttentionCheck'
    ]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype('boolean')

    # Initialize exclusion flags
    df['trial_excluded_VWM'] = False
    df['trial_excluded_MRT'] = False

    exclusion_log = []

    print("\n=== VWM TASK EXCLUSIONS ===")

    # Cascaded exclusion mask for VWM
    vwm_excluded_for_counting = pd.Series(False, index=df.index)

    # 1. VWM Practice trials exclusion
    print("1. VWM Practice trials exclusion...")
    vwm_practice_mask = (df['isPractice'] == True) & (~pd.isna(df['VWM_trial']))
    df.loc[vwm_practice_mask, 'trial_excluded_VWM'] = True
    practice_count = (vwm_practice_mask & ~vwm_excluded_for_counting).sum()
    vwm_excluded_for_counting |= vwm_practice_mask
    total_vwm_trials = (~pd.isna(df['VWM_trial'])).sum()
    print(f"   Excluded {practice_count} VWM practice trials out of {total_vwm_trials} total VWM trials")
    exclusion_log.append({
        'exclusion_criterion': 'Practice trials',
        'task': 'VWM',
        'excluded_count': practice_count,
        'total_trials_screened': total_vwm_trials
    })

    # 2. VWM Attention check exclusion
    print("2. VWM Attention check exclusion...")
    vwm_attention_mask = (df['VWM_isAttentionCheck'] == True) & (~pd.isna(df['VWM_trial']))
    df.loc[vwm_attention_mask, 'trial_excluded_VWM'] = True
    attention_count = (vwm_attention_mask & ~vwm_excluded_for_counting).sum()
    vwm_excluded_for_counting |= vwm_attention_mask
    print(f"   Excluded {attention_count} VWM attention check trials")
    exclusion_log.append({
        'exclusion_criterion': 'Attention checks',
        'task': 'VWM',
        'excluded_count': attention_count,
        'total_trials_screened': total_vwm_trials
    })

    # Calculate test_vwm_trials before missing error data exclusion
    test_vwm_trials = ((df['isPractice'] == False) & (~pd.isna(df['VWM_trial']))).sum()

    # 3. VWM Anticipatory responses exclusion
    print("3. VWM Anticipatory responses exclusion...")
    vwm_anticipatory_mask = (df['VWM_rt_ms'] < 200) & (df['isPractice'] == False) & (~pd.isna(df['VWM_trial']))
    df.loc[vwm_anticipatory_mask, 'trial_excluded_VWM'] = True
    anticipatory_count = (vwm_anticipatory_mask & ~vwm_excluded_for_counting).sum()
    vwm_excluded_for_counting |= vwm_anticipatory_mask
    print(f"   Excluded {anticipatory_count} VWM anticipatory responses out of {test_vwm_trials} test VWM trials")
    exclusion_log.append({
        'exclusion_criterion': 'Anticipatory responses',
        'task': 'VWM',
        'excluded_count': anticipatory_count,
        'total_trials_screened': test_vwm_trials
    })

    # 4. VWM Timeout exclusion
    print("4. VWM Timeout exclusion...")
    vwm_timeout_mask = (df['VWM_timeout'] == True) & (df['isPractice'] == False) & (~pd.isna(df['VWM_trial']))
    df.loc[vwm_timeout_mask, 'trial_excluded_VWM'] = True
    timeout_count = (vwm_timeout_mask & ~vwm_excluded_for_counting).sum()
    vwm_excluded_for_counting |= vwm_timeout_mask
    print(f"   Excluded {timeout_count} VWM timeout trials")
    exclusion_log.append({
        'exclusion_criterion': 'Timeouts',
        'task': 'VWM',
        'excluded_count': timeout_count,
        'total_trials_screened': test_vwm_trials
    })

    # 5. VWM Missing error data exclusion
    print("5. VWM Missing error data exclusion...")
    vwm_missing_error_mask = (pd.isna(df['VWM_error_degrees'])) & (df['isPractice'] == False) & (~pd.isna(df['VWM_trial']))
    df.loc[vwm_missing_error_mask, 'trial_excluded_VWM'] = True
    missing_error_count = (vwm_missing_error_mask & ~vwm_excluded_for_counting).sum()
    vwm_excluded_for_counting |= vwm_missing_error_mask
    print(f"   Excluded {missing_error_count} VWM trials with missing error data")
    exclusion_log.append({
        'exclusion_criterion': 'Missing error data',
        'task': 'VWM',
        'excluded_count': missing_error_count,
        'total_trials_screened': test_vwm_trials
    })

    # 6. VWM Extreme RT exclusion
    print("6. VWM Extreme RT exclusion...")
    vwm_extreme_mask = (df['VWM_rt_ms'] > 10000) & (df['isPractice'] == False) & (~pd.isna(df['VWM_trial']))
    df.loc[vwm_extreme_mask, 'trial_excluded_VWM'] = True
    extreme_count = (vwm_extreme_mask & ~vwm_excluded_for_counting).sum()
    vwm_excluded_for_counting |= vwm_extreme_mask
    print(f"   Excluded {extreme_count} VWM extreme RT trials")
    exclusion_log.append({
        'exclusion_criterion': 'Extreme RT values',
        'task': 'VWM',
        'excluded_count': extreme_count,
        'total_trials_screened': test_vwm_trials
    })

    # 7. VWM RT outliers exclusion (vectorized)
    print("7. VWM RT outliers exclusion (per participant, vectorized)...")
    # Only consider valid, test trials for stats (do NOT filter by vwm_excluded_for_counting)
    valid_vwm_mask = (
        (df['isPractice'] == False) &
        (df['VWM_timeout'] == False) &
        (df['VWM_rt_ms'] >= 200) &
        (df['VWM_rt_ms'] <= 10000) &
        (~pd.isna(df['VWM_trial']))
    )
    vwm_valid = df[valid_vwm_mask].copy()
    vwm_stats = vwm_valid.groupby('participantId')['VWM_rt_ms'].agg(['mean', 'std', 'count']).rename(
        columns={'mean': 'VWM_individual_mean_rt', 'std': 'VWM_individual_sd_rt', 'count': 'VWM_valid_trial_count'}
    )
    # Only keep participants with >=10 valid trials
    vwm_stats = vwm_stats[vwm_stats['VWM_valid_trial_count'] >= 10]
    # Merge stats back to main df, handle existing columns robustly
    df = df.merge(
        vwm_stats[['VWM_individual_mean_rt', 'VWM_individual_sd_rt']],
        left_on='participantId', right_index=True, how='left', suffixes=('_old', '')
    )

    # Compute outlier threshold and mask
    vwm_outlier_threshold = df['VWM_individual_mean_rt'] + 3 * df['VWM_individual_sd_rt']
    vwm_outlier_mask = (
        (df['VWM_rt_ms'] > vwm_outlier_threshold) &
        (~pd.isna(df['VWM_individual_mean_rt']))
    )
    df.loc[vwm_outlier_mask, 'trial_excluded_VWM'] = True
    vwm_outlier_count = (vwm_outlier_mask & ~vwm_excluded_for_counting).sum()
    vwm_excluded_for_counting |= vwm_outlier_mask

    # Print per-participant outlier info
    for pid, group in df[vwm_outlier_mask & ~vwm_excluded_for_counting].groupby('participantId'):
        threshold = (vwm_stats.loc[pid, 'VWM_individual_mean_rt'] + 3 * vwm_stats.loc[pid, 'VWM_individual_sd_rt']) if pid in vwm_stats.index else None
        print(f"   Participant {pid}: excluded {len(group)} outlier trials (threshold: {threshold:.2f}ms)" if threshold is not None else f"   Participant {pid}: excluded {len(group)} outlier trials")

    print(f"   Total VWM RT outliers excluded: {vwm_outlier_count} across {vwm_stats.shape[0]} participants")
    exclusion_log.append({
        'exclusion_criterion': 'RT outliers',
        'task': 'VWM',
        'excluded_count': vwm_outlier_count,
        'total_trials_screened': test_vwm_trials
    })

    print("\n=== MRT TASK EXCLUSIONS ===")

    # Cascaded exclusion mask for MRT
    mrt_excluded_for_counting = pd.Series(False, index=df.index)

    # 1. MRT Practice trials exclusion
    print("1. MRT Practice trials exclusion...")
    mrt_practice_mask = (df['isPractice'] == True) & (~pd.isna(df['MRT_trial']))
    df.loc[mrt_practice_mask, 'trial_excluded_MRT'] = True
    mrt_practice_count = (mrt_practice_mask & ~mrt_excluded_for_counting).sum()
    mrt_excluded_for_counting |= mrt_practice_mask
    total_mrt_trials = (~pd.isna(df['MRT_trial'])).sum()
    print(f"   Excluded {mrt_practice_count} MRT practice trials out of {total_mrt_trials} total MRT trials")
    exclusion_log.append({
        'exclusion_criterion': 'Practice trials',
        'task': 'MRT',
        'excluded_count': mrt_practice_count,
        'total_trials_screened': total_mrt_trials
    })

    # 2. MRT Attention check exclusion
    print("2. MRT Attention check exclusion...")
    mrt_attention_mask = (df['MRT_isAttentionCheck'] == True) & (~pd.isna(df['MRT_trial']))
    df.loc[mrt_attention_mask, 'trial_excluded_MRT'] = True
    mrt_attention_count = (mrt_attention_mask & ~mrt_excluded_for_counting).sum()
    mrt_excluded_for_counting |= mrt_attention_mask
    print(f"   Excluded {mrt_attention_count} MRT attention check trials")
    exclusion_log.append({
        'exclusion_criterion': 'Attention checks',
        'task': 'MRT',
        'excluded_count': mrt_attention_count,
        'total_trials_screened': total_mrt_trials
    })

    # 3. MRT Anticipatory responses exclusion
    print("3. MRT Anticipatory responses exclusion...")
    mrt_anticipatory_mask = (df['MRT_rt_ms'] < 200) & (df['isPractice'] == False) & (~pd.isna(df['MRT_trial']))
    df.loc[mrt_anticipatory_mask, 'trial_excluded_MRT'] = True
    mrt_anticipatory_count = (mrt_anticipatory_mask & ~mrt_excluded_for_counting).sum()
    mrt_excluded_for_counting |= mrt_anticipatory_mask
    test_mrt_trials = ((df['isPractice'] == False) & (~pd.isna(df['MRT_trial']))).sum()
    print(f"   Excluded {mrt_anticipatory_count} MRT anticipatory responses out of {test_mrt_trials} test MRT trials")
    exclusion_log.append({
        'exclusion_criterion': 'Anticipatory responses',
        'task': 'MRT',
        'excluded_count': mrt_anticipatory_count,
        'total_trials_screened': test_mrt_trials
    })

    # 4. MRT Timeout exclusion
    print("4. MRT Timeout exclusion...")
    mrt_timeout_mask = (df['MRT_timeout'] == True) & (df['isPractice'] == False) & (~pd.isna(df['MRT_trial']))
    df.loc[mrt_timeout_mask, 'trial_excluded_MRT'] = True
    mrt_timeout_count = (mrt_timeout_mask & ~mrt_excluded_for_counting).sum()
    mrt_excluded_for_counting |= mrt_timeout_mask
    print(f"   Excluded {mrt_timeout_count} MRT timeout trials")
    exclusion_log.append({
        'exclusion_criterion': 'Timeouts',
        'task': 'MRT',
        'excluded_count': mrt_timeout_count,
        'total_trials_screened': test_mrt_trials
    })

    # 5. MRT Extreme RT exclusion
    print("5. MRT Extreme RT exclusion...")
    mrt_extreme_mask = (df['MRT_rt_ms'] > 10000) & (df['isPractice'] == False) & (~pd.isna(df['MRT_trial']))
    df.loc[mrt_extreme_mask, 'trial_excluded_MRT'] = True
    mrt_extreme_count = (mrt_extreme_mask & ~mrt_excluded_for_counting).sum()
    mrt_excluded_for_counting |= mrt_extreme_mask
    print(f"   Excluded {mrt_extreme_count} MRT extreme RT trials")
    exclusion_log.append({
        'exclusion_criterion': 'Extreme RT values',
        'task': 'MRT',
        'excluded_count': mrt_extreme_count,
        'total_trials_screened': test_mrt_trials
    })

    # 6. MRT RT outliers exclusion (vectorized)
    print("6. MRT RT outliers exclusion (per participant, vectorized)...")
    valid_mrt_mask = (
        (df['isPractice'] == False) &
        (df['MRT_timeout'] == False) &
        (df['MRT_rt_ms'] >= 200) &
        (df['MRT_rt_ms'] <= 10000) &
        (~pd.isna(df['MRT_trial']))
    )
    mrt_valid = df[valid_mrt_mask].copy()
    mrt_stats = mrt_valid.groupby('participantId')['MRT_rt_ms'].agg(['mean', 'std', 'count']).rename(
        columns={'mean': 'MRT_individual_mean_rt', 'std': 'MRT_individual_sd_rt', 'count': 'MRT_valid_trial_count'}
    )
    mrt_stats = mrt_stats[mrt_stats['MRT_valid_trial_count'] >= 10]
    df = df.merge(
        mrt_stats[['MRT_individual_mean_rt', 'MRT_individual_sd_rt']],
        left_on='participantId', right_index=True, how='left', suffixes=('_old', '')
    )

    mrt_outlier_threshold = df['MRT_individual_mean_rt'] + 3 * df['MRT_individual_sd_rt']
    mrt_outlier_mask = (
        (df['MRT_rt_ms'] > mrt_outlier_threshold) &
        (~pd.isna(df['MRT_individual_mean_rt']))
    )
    df.loc[mrt_outlier_mask, 'trial_excluded_MRT'] = True
    mrt_outlier_count = (mrt_outlier_mask & ~mrt_excluded_for_counting).sum()
    mrt_excluded_for_counting |= mrt_outlier_mask

    for pid, group in df[mrt_outlier_mask & ~mrt_excluded_for_counting].groupby('participantId'):
        threshold = (mrt_stats.loc[pid, 'MRT_individual_mean_rt'] + 3 * mrt_stats.loc[pid, 'MRT_individual_sd_rt']) if pid in mrt_stats.index else None
        print(f"   Participant {pid}: excluded {len(group)} outlier trials (threshold: {threshold:.2f}ms)" if threshold is not None else f"   Participant {pid}: excluded {len(group)} outlier trials")

    print(f"   Total MRT RT outliers excluded: {mrt_outlier_count} across {mrt_stats.shape[0]} participants")
    exclusion_log.append({
        'exclusion_criterion': 'RT outliers',
        'task': 'MRT',
        'excluded_count': mrt_outlier_count,
        'total_trials_screened': test_mrt_trials
    })

    return df, exclusion_log

def main():
    """
    Main function to execute trial-level exclusions and data cleaning.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting trial-level exclusions script...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/participant_level_cleaned_data_<TIMESTAMP>.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input file found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read the input data
        print("Reading input data...")
        df = pd.read_csv(input_file)
        
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        print("\nAll columns in input data:")
        print(df.columns.tolist())
        
        print("\nFirst 3 rows of input data:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = [
            'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_rt_ms',
            'VWM_timeout', 'VWM_error_degrees', 'VWM_error_absolute_degrees',
            'VWM_isAttentionCheck', 'MRT_trial', 'MRT_rt_ms', 'MRT_timeout',
            'MRT_isCorrect', 'MRT_isAttentionCheck'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found.")
        
        # Print unique values for key experimental design parameters
        print("\n=== KEY EXPERIMENTAL DESIGN PARAMETERS ===")
        
        # Check if VWM_setSize exists
        if 'VWM_setSize' in df.columns:
            print(f"VWM_setSize unique values: {sorted(df['VWM_setSize'].dropna().unique())}")
        else:
            print("VWM_setSize column not found in data")
        
        # Check if VWM_delay_s exists
        if 'VWM_delay_s' in df.columns:
            print(f"VWM_delay_s unique values: {sorted(df['VWM_delay_s'].dropna().unique())}")
        else:
            print("VWM_delay_s column not found in data")
        
        # Check if MRT_angle_degrees exists
        if 'MRT_angle_degrees' in df.columns:
            print(f"MRT_angle_degrees unique values: {sorted(df['MRT_angle_degrees'].dropna().unique())}")
        else:
            print("MRT_angle_degrees column not found in data")
        
        # Check if MRT_isReflected exists
        if 'MRT_isReflected' in df.columns:
            print(f"MRT_isReflected unique values: {sorted(df['MRT_isReflected'].dropna().unique())}")
        else:
            print("MRT_isReflected column not found in data")
        
        print(f"isPractice unique values: {sorted(df['isPractice'].dropna().unique())}")
        print(f"VWM_isAttentionCheck unique values: {sorted(df['VWM_isAttentionCheck'].dropna().unique())}")
        print(f"MRT_isAttentionCheck unique values: {sorted(df['MRT_isAttentionCheck'].dropna().unique())}")
        
        # Print data types for measured variables
        print("\n=== MEASURED VARIABLE DATA TYPES ===")
        print(f"VWM_rt_ms data type: {df['VWM_rt_ms'].dtype}")
        print(f"VWM_error_degrees data type: {df['VWM_error_degrees'].dtype}")
        print(f"VWM_error_absolute_degrees data type: {df['VWM_error_absolute_degrees'].dtype}")
        print(f"MRT_rt_ms data type: {df['MRT_rt_ms'].dtype}")
        print(f"MRT_isCorrect data type: {df['MRT_isCorrect'].dtype}")
        
        # Calculate VWM normalized error
        print("\nCalculating VWM normalized error...")
        df['VWM_error_normalized'] = df['VWM_error_degrees'].apply(normalize_vwm_error)
        print(f"VWM_error_normalized calculated for {(~pd.isna(df['VWM_error_normalized'])).sum()} trials")
        
        # Apply trial-level exclusions
        df_cleaned, exclusion_log = apply_trial_exclusions(df)
        
        # Print summary statistics
        print("\n=== EXCLUSION SUMMARY ===")
        total_vwm_excluded = df_cleaned['trial_excluded_VWM'].sum()
        total_mrt_excluded = df_cleaned['trial_excluded_MRT'].sum()
        total_vwm_trials = (~pd.isna(df_cleaned['VWM_trial'])).sum()
        total_mrt_trials = (~pd.isna(df_cleaned['MRT_trial'])).sum()
        
        print(f"Total VWM trials excluded: {total_vwm_excluded} out of {total_vwm_trials} ({100*total_vwm_excluded/total_vwm_trials:.1f}%)")
        print(f"Total MRT trials excluded: {total_mrt_excluded} out of {total_mrt_trials} ({100*total_mrt_excluded/total_mrt_trials:.1f}%)")
        
        # Create timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save exclusion log
        exclusion_log_df = pd.DataFrame(exclusion_log)
        exclusion_log_file = f'outputs/trial_exclusion_log_{timestamp}.csv'
        exclusion_log_df.to_csv(exclusion_log_file, index=False)
        print(f"\nSaved exclusion log to: {exclusion_log_file}")
        print("Exclusion log contents:")
        print(exclusion_log_df)
        
        # Save cleaned data
        output_file = f'outputs/trial_level_cleaned_data_{timestamp}.csv'
        df_cleaned.to_csv(output_file, index=False)
        print(f"\nSaved cleaned data to: {output_file}")
        
        print(f"Output data shape: {df_cleaned.shape}")
        print("\nAll columns in output data:")
        print(df_cleaned.columns.tolist())
        
        print("\nFirst 2 rows of output data:")
        print(df_cleaned.head(2))

        # Add final exclusion report
        print("\n=== FINAL EXCLUSION REPORT (CASCADED) ===")
        print(f"Initial rows loaded: {len(df)}")
        for task in ['VWM', 'MRT']:
            print(f"\n--- {task} Task ---")
            task_log = exclusion_log_df[exclusion_log_df['task'] == task]
            for _, row in task_log.iterrows():
                print(f"Excluded for {row['exclusion_criterion']}: {row['excluded_count']} trials")
        print(f"\nFinal VWM trials excluded: {total_vwm_excluded} ({100*total_vwm_excluded/total_vwm_trials:.1f}%)")
        print(f"Final MRT trials excluded: {total_mrt_excluded} ({100*total_mrt_excluded/total_mrt_trials:.1f}%)")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
