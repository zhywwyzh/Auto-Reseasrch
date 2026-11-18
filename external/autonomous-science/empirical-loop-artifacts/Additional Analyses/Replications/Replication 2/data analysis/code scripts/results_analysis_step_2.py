import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

def find_most_recent_file(pattern):
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
    return max(files, key=os.path.getctime)

def load_task_data_files(pattern):
    """
    Load all task data files matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match for task data files
    
    Returns:
    pd.DataFrame: Combined dataframe from all matching files
    """
    files = glob.glob(pattern)
    print(f"Found {len(files)} task data files matching pattern: {pattern}")
    
    all_data = []
    for file in files:
        print(f"Loading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File {file} loaded with shape: {df.shape}")
            all_data.append(df)
        except Exception as e:
            print(f"Error loading file {file}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No valid task data files found")
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined task data shape: {combined_df.shape}")
    return combined_df

def load_demographic_data():
    """
    Load the most recent demographic data file.
    
    Returns:
    pd.DataFrame: Demographic data
    """
    pattern = "outputs/prolific_demographic_cleaned_*.csv"
    demo_file = find_most_recent_file(pattern)
    
    if demo_file is None:
        raise ValueError(f"No demographic file found matching pattern: {pattern}")
    
    print(f"Loading demographic file: {demo_file}")
    demo_df = pd.read_csv(demo_file)
    print(f"Demographic data shape: {demo_df.shape}")
    return demo_df

def validate_required_columns(df, required_columns, file_type):
    """
    Validate that required columns exist in the dataframe.
    
    Parameters:
    df (pd.DataFrame): Dataframe to validate
    required_columns (list): List of required column names
    file_type (str): Type of file being validated for error messages
    
    Returns:
    bool: True if all required columns exist
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Missing required columns in {file_type}: {missing_columns}")
        return False
    return True

def calculate_participant_exclusions(task_df, demo_df):
    """
    Calculate exclusion criteria for each participant.

    Parameters:
    task_df (pd.DataFrame): Task data
    demo_df (pd.DataFrame): Demographic data

    Returns:
    pd.DataFrame: Participant exclusion status
    """
    # Process ALL participants from demographic file
    all_participants = demo_df['participant_id'].tolist()
    print(f"Total participants from demographic file: {len(all_participants)}")

    results = []

    for participant in all_participants:
        print(f"\nProcessing participant: {participant}")

        # Get demographic info for this participant
        demo_row = demo_df[demo_df['participant_id'] == participant].iloc[0]

        # Get participant data
        participant_data = task_df[task_df['participantId'] == participant].copy()

        # Initialize exclusion flags
        exclusions = {
            'participantId': participant,
            'included': True,
            'excluded_extreme_completion_time': demo_row['excluded_extreme_time'],
            'excluded_vwm_practice_attempts': False,
            'excluded_mrt_practice_attempts': False,
            'excluded_vwm_timeout_rate': False,
            'excluded_mrt_timeout_rate': False,
            'excluded_vwm_performance_outlier': False,
            'excluded_mrt_performance_outlier': False,
            'excluded_insufficient_vwm_trials': False,
            'excluded_incomplete_vwm_data': False,
            'excluded_incomplete_mrt_data': False,
            'vwm_timeout_rate': np.nan,
            'mrt_timeout_rate': np.nan,
            'vwm_mean_absolute_error': np.nan,
            'mrt_mean_accuracy': np.nan,
            'valid_vwm_trial_count': 0,
            'primary_exclusion_reason': 'None'
        }

        # Check if already excluded for extreme time
        if demo_row['excluded_extreme_time']:
            exclusions['included'] = False
            exclusions['primary_exclusion_reason'] = 'Extreme completion time'
            results.append(exclusions)
            print(f"  Excluded (demographics): Extreme completion time")
            continue

        if participant_data.empty:
            exclusions['excluded_incomplete_vwm_data'] = True
            exclusions['excluded_incomplete_mrt_data'] = True
            exclusions['included'] = False
            exclusions['primary_exclusion_reason'] = 'No task data found'
            results.append(exclusions)
            print(f"  Excluded: No task data found")
            continue

        # Check for incomplete task data
        vwm_test_data = participant_data[participant_data['table'] == 'vwm_test']
        mrt_test_data = participant_data[participant_data['table'] == 'mrt_test']

        if vwm_test_data.empty:
            exclusions['excluded_incomplete_vwm_data'] = True
            exclusions['included'] = False
            exclusions['primary_exclusion_reason'] = 'Incomplete VWM data'
            print(f"  Excluded: No VWM test data")

        if mrt_test_data.empty:
            exclusions['excluded_incomplete_mrt_data'] = True
            exclusions['included'] = False
            if exclusions['primary_exclusion_reason'] == 'None':
                exclusions['primary_exclusion_reason'] = 'Incomplete MRT data'
            print(f"  Excluded: No MRT test data")

        # Calculate all metrics regardless of previous exclusions
        # Check practice attempts
        vwm_practice_data = participant_data[participant_data['table'] == 'vwm_practice']
        mrt_practice_data = participant_data[participant_data['table'] == 'mrt_practice']

        if not vwm_practice_data.empty and 'VWM_pracAttempt' in vwm_practice_data.columns:
            max_vwm_attempts = vwm_practice_data['VWM_pracAttempt'].max()
            if pd.notna(max_vwm_attempts) and max_vwm_attempts > 10:
                exclusions['excluded_vwm_practice_attempts'] = True
                exclusions['included'] = False
                if exclusions['primary_exclusion_reason'] == 'None':
                    exclusions['primary_exclusion_reason'] = 'VWM practice attempts exceeded'
                print(f"  Excluded: VWM practice attempts = {max_vwm_attempts}")

        if not mrt_practice_data.empty and 'MRT_pracAttempt' in mrt_practice_data.columns:
            max_mrt_attempts = mrt_practice_data['MRT_pracAttempt'].max()
            if pd.notna(max_mrt_attempts) and max_mrt_attempts > 10:
                exclusions['excluded_mrt_practice_attempts'] = True
                exclusions['included'] = False
                if exclusions['primary_exclusion_reason'] == 'None':
                    exclusions['primary_exclusion_reason'] = 'MRT practice attempts exceeded'
                print(f"  Excluded: MRT practice attempts = {max_mrt_attempts}")

        # Calculate timeout rates
        if not vwm_test_data.empty and 'VWM_timeout' in vwm_test_data.columns:
            vwm_timeouts = vwm_test_data['VWM_timeout'].sum()
            vwm_total_trials = len(vwm_test_data)
            vwm_timeout_rate = vwm_timeouts / vwm_total_trials if vwm_total_trials > 0 else 0
            exclusions['vwm_timeout_rate'] = vwm_timeout_rate

            if vwm_timeout_rate > 0.25:
                exclusions['excluded_vwm_timeout_rate'] = True
                exclusions['included'] = False
                if exclusions['primary_exclusion_reason'] == 'None':
                    exclusions['primary_exclusion_reason'] = 'VWM timeout rate exceeded'
                print(f"  Excluded: VWM timeout rate = {vwm_timeout_rate:.3f}")

        if not mrt_test_data.empty and 'MRT_timeout' in mrt_test_data.columns:
            mrt_timeouts = mrt_test_data['MRT_timeout'].sum()
            mrt_total_trials = len(mrt_test_data)
            mrt_timeout_rate = mrt_timeouts / mrt_total_trials if mrt_total_trials > 0 else 0
            exclusions['mrt_timeout_rate'] = mrt_timeout_rate

            if mrt_timeout_rate > 0.25:
                exclusions['excluded_mrt_timeout_rate'] = True
                exclusions['included'] = False
                if exclusions['primary_exclusion_reason'] == 'None':
                    exclusions['primary_exclusion_reason'] = 'MRT timeout rate exceeded'
                print(f"  Excluded: MRT timeout rate = {mrt_timeout_rate:.3f}")

        # Calculate performance metrics
        if not vwm_test_data.empty and 'VWM_error_absolute_degrees' in vwm_test_data.columns:
            vwm_errors = vwm_test_data['VWM_error_absolute_degrees'].dropna()
            if not vwm_errors.empty:
                vwm_mean_error = vwm_errors.mean()
                exclusions['vwm_mean_absolute_error'] = vwm_mean_error
                print(f"  VWM mean error = {vwm_mean_error:.3f}")

        if not mrt_test_data.empty and 'MRT_isCorrect' in mrt_test_data.columns:
            mrt_correct = mrt_test_data['MRT_isCorrect'].dropna()
            if not mrt_correct.empty:
                mrt_accuracy = mrt_correct.mean()
                exclusions['mrt_mean_accuracy'] = mrt_accuracy
                print(f"  MRT accuracy = {mrt_accuracy:.3f}")

        # Count valid VWM trials
        if not vwm_test_data.empty and 'VWM_timeout' in vwm_test_data.columns and 'VWM_rt_ms' in vwm_test_data.columns:
            valid_vwm = vwm_test_data[
                (vwm_test_data['VWM_timeout'] == False) &
                (pd.notna(vwm_test_data['VWM_rt_ms']))
            ]
            valid_vwm_count = len(valid_vwm)
            exclusions['valid_vwm_trial_count'] = valid_vwm_count

            if valid_vwm_count < 60:
                exclusions['excluded_insufficient_vwm_trials'] = True
                exclusions['included'] = False
                if exclusions['primary_exclusion_reason'] == 'None':
                    exclusions['primary_exclusion_reason'] = 'Insufficient VWM trials'
                print(f"  Excluded: Valid VWM trials = {valid_vwm_count}")

        results.append(exclusions)

    results_df = pd.DataFrame(results)
    print(f"\nTotal participants processed: {len(results_df)}")

    # Ensure 'primary_exclusion_reason' is 'None' for included participants
    results_df.loc[results_df['included'] & (results_df['primary_exclusion_reason'].isna()), 'primary_exclusion_reason'] = 'None'
    results_df['primary_exclusion_reason'] = results_df['primary_exclusion_reason'].fillna('None')

    return results_df

def apply_performance_outlier_exclusions(results_df):
    """
    Apply performance outlier exclusions based on group statistics.
    
    Parameters:
    results_df (pd.DataFrame): Results dataframe with performance metrics
    
    Returns:
    pd.DataFrame: Updated results dataframe
    """
    print("\nApplying performance outlier exclusions...")
    
    # Calculate group statistics for VWM error
    vwm_errors = results_df['vwm_mean_absolute_error'].dropna()
    if not vwm_errors.empty:
        vwm_mean = vwm_errors.mean()
        vwm_std = vwm_errors.std()
        vwm_threshold_upper = vwm_mean + 3 * vwm_std
        vwm_threshold_lower = vwm_mean - 3 * vwm_std
        
        print(f"VWM error group stats: mean={vwm_mean:.3f}, std={vwm_std:.3f}")
        print(f"VWM error thresholds: [{vwm_threshold_lower:.3f}, {vwm_threshold_upper:.3f}]")
        
        # Apply VWM outlier exclusions (only exclude high error, not low error)
        vwm_outliers = results_df['vwm_mean_absolute_error'] > vwm_threshold_upper
        
        results_df.loc[vwm_outliers, 'excluded_vwm_performance_outlier'] = True
        results_df.loc[vwm_outliers & (results_df['primary_exclusion_reason'] == 'None'), 'primary_exclusion_reason'] = 'VWM performance outlier'
        results_df.loc[vwm_outliers, 'included'] = False
        
        print(f"VWM performance outliers excluded: {vwm_outliers.sum()}")
    
    # Calculate group statistics for MRT accuracy
    mrt_accuracies = results_df['mrt_mean_accuracy'].dropna()
    if not mrt_accuracies.empty:
        mrt_mean = mrt_accuracies.mean()
        mrt_std = mrt_accuracies.std()
        mrt_threshold_upper = mrt_mean + 3 * mrt_std
        mrt_threshold_lower = mrt_mean - 3 * mrt_std
        
        print(f"MRT accuracy group stats: mean={mrt_mean:.3f}, std={mrt_std:.3f}")
        print(f"MRT accuracy thresholds: [{mrt_threshold_lower:.3f}, {mrt_threshold_upper:.3f}]")
        
        # Apply MRT outlier exclusions (only exclude low accuracy, not high accuracy)
        mrt_outliers = results_df['mrt_mean_accuracy'] < mrt_threshold_lower
        
        results_df.loc[mrt_outliers, 'excluded_mrt_performance_outlier'] = True
        results_df.loc[mrt_outliers & (results_df['primary_exclusion_reason'] == 'None'), 'primary_exclusion_reason'] = 'MRT performance outlier'
        results_df.loc[mrt_outliers, 'included'] = False
        
        print(f"MRT performance outliers excluded: {mrt_outliers.sum()}")
    
    return results_df

def create_exclusion_summary(results_df, demo_df):
    """
    Create summary of exclusions by criterion.
    
    Parameters:
    results_df (pd.DataFrame): Results dataframe
    demo_df (pd.DataFrame): Demographic dataframe
    
    Returns:
    pd.DataFrame: Exclusion summary
    """
    total_original = len(demo_df)
    total_assessed = len(results_df)
    
    exclusion_criteria = [
        ('Extreme completion time', demo_df['excluded_extreme_time'].sum(), total_original),
        ('VWM practice attempts', results_df['excluded_vwm_practice_attempts'].sum(), total_assessed),
        ('MRT practice attempts', results_df['excluded_mrt_practice_attempts'].sum(), total_assessed),
        ('VWM timeout rate', results_df['excluded_vwm_timeout_rate'].sum(), total_assessed),
        ('MRT timeout rate', results_df['excluded_mrt_timeout_rate'].sum(), total_assessed),
        ('VWM performance outlier', results_df['excluded_vwm_performance_outlier'].sum(), total_assessed),
        ('MRT performance outlier', results_df['excluded_mrt_performance_outlier'].sum(), total_assessed),
        ('Insufficient VWM trials', results_df['excluded_insufficient_vwm_trials'].sum(), total_assessed),
        ('Incomplete VWM data', results_df['excluded_incomplete_vwm_data'].sum(), total_assessed),
        ('Incomplete MRT data', results_df['excluded_incomplete_mrt_data'].sum(), total_assessed)
    ]
    
    summary_data = []
    for criterion, count, total in exclusion_criteria:
        percentage = (count / total * 100) if total > 0 else 0
        summary_data.append({
            'exclusion_criterion': criterion,
            'count_excluded': count,
            'total_participants_assessed': total,
            'exclusion_percentage': percentage
        })
    
    return pd.DataFrame(summary_data)

def main():
    """
    Main function to execute participant exclusion analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting participant exclusion analysis...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Load data files
        print("\n=== LOADING DATA FILES ===")
        task_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        task_df = load_task_data_files(task_pattern)
        
        demo_df = load_demographic_data()
        
        # Validate required columns
        print("\n=== VALIDATING COLUMNS ===")
        task_required_columns = [
            'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_timeout',
            'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_pracAttempt',
            'MRT_trial', 'MRT_timeout', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_pracAttempt'
        ]
        
        demo_required_columns = ['participant_id', 'excluded_extreme_time']
        
        if not validate_required_columns(task_df, task_required_columns, "task data"):
            print("Available task columns:", list(task_df.columns))
            return 1
        
        if not validate_required_columns(demo_df, demo_required_columns, "demographic data"):
            print("Available demographic columns:", list(demo_df.columns))
            return 1
        
        # Print data structure information
        print("\n=== TASK DATA STRUCTURE ===")
        print("All columns:", list(task_df.columns))
        print("First 2 rows:")
        print(task_df.head(2))
        print("\nUnique values in 'table' column:", task_df['table'].unique())
        print("Unique values in 'isPractice' column:", task_df['isPractice'].unique())
        
        print("\n=== DEMOGRAPHIC DATA STRUCTURE ===")
        print("All columns:", list(demo_df.columns))
        print("First 2 rows:")
        print(demo_df.head(2))
        print("Unique values in 'excluded_extreme_time' column:", demo_df['excluded_extreme_time'].unique())
        
        # Calculate participant exclusions
        print("\n=== CALCULATING PARTICIPANT EXCLUSIONS ===")
        results_df = calculate_participant_exclusions(task_df, demo_df)
        
        # Apply performance outlier exclusions
        results_df = apply_performance_outlier_exclusions(results_df)
        
        # Create exclusion summary
        print("\n=== CREATING EXCLUSION SUMMARY ===")
        summary_df = create_exclusion_summary(results_df, demo_df)
        
        # Print summary statistics
        print("\nFinal inclusion statistics:")
        print(f"Total included participants: {results_df['included'].sum()}")
        print(f"Total excluded participants: {(~results_df['included']).sum()}")
        print(f"Total participants processed: {len(results_df)}")
        
        print("\nExclusion summary:")
        for _, row in summary_df.iterrows():
            print(f"  {row['exclusion_criterion']}: {row['count_excluded']} ({row['exclusion_percentage']:.1f}%)")

        # Print comprehensive final summary
        print("\n=== FINAL DATA PROCESSING SUMMARY ===")
        print(f"Initial participants loaded: {len(demo_df)}")
        print(f"Participants excluded for extreme completion time: {demo_df['excluded_extreme_time'].sum()}")
        print(f"Participants with no task data: {(results_df['primary_exclusion_reason'] == 'No task data found').sum()}")
        print(f"Participants excluded for VWM practice attempts: {results_df['excluded_vwm_practice_attempts'].sum()}")
        print(f"Participants excluded for MRT practice attempts: {results_df['excluded_mrt_practice_attempts'].sum()}")
        print(f"Participants excluded for VWM timeout rate: {results_df['excluded_vwm_timeout_rate'].sum()}")
        print(f"Participants excluded for MRT timeout rate: {results_df['excluded_mrt_timeout_rate'].sum()}")
        print(f"Participants excluded for VWM performance outlier: {results_df['excluded_vwm_performance_outlier'].sum()}")
        print(f"Participants excluded for MRT performance outlier: {results_df['excluded_mrt_performance_outlier'].sum()}")
        print(f"Participants excluded for insufficient VWM trials: {results_df['excluded_insufficient_vwm_trials'].sum()}")
        print(f"Final dataset: {results_df['included'].sum()} participants included")
        
        # Save output files
        print("\n=== SAVING OUTPUT FILES ===")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save participant inclusion status
        inclusion_file = f"outputs/participant_inclusion_status_{timestamp}.csv"
        results_df.to_csv(inclusion_file, index=False)
        print(f"Saved participant inclusion status to: {inclusion_file}")
        
        # Save exclusion log
        exclusion_file = f"outputs/participant_exclusion_log_{timestamp}.csv"
        summary_df.to_csv(exclusion_file, index=False)
        print(f"Saved exclusion log to: {exclusion_file}")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
