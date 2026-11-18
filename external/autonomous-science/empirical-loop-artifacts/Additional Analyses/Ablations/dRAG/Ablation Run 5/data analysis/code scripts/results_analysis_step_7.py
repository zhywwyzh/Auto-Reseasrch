import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

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
    return max(files, key=os.path.getctime)


def calculate_z_score(values):
    """
    Calculate z-scores for a series of values, handling NaN values properly.
    
    Parameters:
    values (pd.Series): Series of numeric values
    
    Returns:
    pd.Series: Z-scores
    """
    valid_values = values.dropna()
    if len(valid_values) == 0:
        return pd.Series([np.nan] * len(values), index=values.index)
    mean_val = valid_values.mean()
    std_val = valid_values.std()
    if std_val == 0:
        return pd.Series([0] * len(values), index=values.index)
    return (values - mean_val) / std_val

def main():
    """
    Main function to process trial data and calculate domain-general metrics.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting domain-general metrics calculation...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find input files
        print("\nSearching for input files...")
        trial_pattern = "outputs/trial_level_cleaned_data_*.csv"
        prolific_pattern = "outputs/prolific_session_data_*.csv"
        
        trial_file = find_latest_file(trial_pattern)
        prolific_file = find_latest_file(prolific_pattern)
        
        if trial_file is None:
            print(f"ERROR: No trial data file found matching pattern: {trial_pattern}")
            return 1
        if prolific_file is None:
            print(f"ERROR: No prolific session data file found matching pattern: {prolific_pattern}")
            return 1
            
        print(f"Found trial data file: {trial_file}")
        print(f"Found prolific session data file: {prolific_file}")
        
        # Load trial data
        print(f"\nLoading trial data from {trial_file}...")
        trial_data = pd.read_csv(trial_file)
        print(f"Loaded trial data with shape: {trial_data.shape}")
        
        print("Trial data columns:")
        print(trial_data.columns.tolist())
        print("\nFirst 3 rows of trial data:")
        print(trial_data.head(3))
        
        # Load prolific session data
        print(f"\nLoading prolific session data from {prolific_file}...")
        prolific_data = pd.read_csv(prolific_file)
        print(f"Loaded prolific session data with shape: {prolific_data.shape}")
        
        print("Prolific session data columns:")
        print(prolific_data.columns.tolist())
        print("\nFirst 3 rows of prolific session data:")
        print(prolific_data.head(3))
        
        # Verify required columns in trial data
        required_trial_cols = [
            'participantId', 'isPractice', 'trial_excluded_VWM', 'trial_excluded_MRT',
            'VWM_rt_ms', 'VWM_timeout', 'VWM_error_absolute_degrees',
            'MRT_rt_ms', 'MRT_timeout', 'MRT_isCorrect',
            'windowFocusLostDuringTasksDuration', 'windowFocusLostDuringTasksNum'
        ]
        
        missing_trial_cols = [col for col in required_trial_cols if col not in trial_data.columns]
        if missing_trial_cols:
            print(f"ERROR: Missing required columns in trial data: {missing_trial_cols}")
            return 1
        
        # Verify required columns in prolific data
        required_prolific_cols = ['participant_id', 'session_duration_minutes']
        missing_prolific_cols = [col for col in required_prolific_cols if col not in prolific_data.columns]
        if missing_prolific_cols:
            print(f"ERROR: Missing required columns in prolific data: {missing_prolific_cols}")
            return 1
        
        print("\nAll required columns found in both datasets")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"isPractice unique values: {sorted(trial_data['isPractice'].unique())}")
        print(f"trial_excluded_VWM unique values: {sorted(trial_data['trial_excluded_VWM'].unique())}")
        print(f"trial_excluded_MRT unique values: {sorted(trial_data['trial_excluded_MRT'].unique())}")
        print(f"VWM_timeout unique values: {sorted(trial_data['VWM_timeout'].unique())}")
        print(f"MRT_timeout unique values: {sorted(trial_data['MRT_timeout'].unique())}")
        print(f"MRT_isCorrect unique values: {sorted(trial_data['MRT_isCorrect'].unique())}")
        
        # Print data types for measured variables
        print("\nData types for measured variables:")
        print(f"VWM_rt_ms type: {trial_data['VWM_rt_ms'].dtype}")
        print(f"MRT_rt_ms type: {trial_data['MRT_rt_ms'].dtype}")
        print(f"VWM_error_absolute_degrees type: {trial_data['VWM_error_absolute_degrees'].dtype}")
        print(f"windowFocusLostDuringTasksDuration type: {trial_data['windowFocusLostDuringTasksDuration'].dtype}")
        print(f"windowFocusLostDuringTasksNum type: {trial_data['windowFocusLostDuringTasksNum'].dtype}")
        
        # Get unique participants
        participants = trial_data['participantId'].unique()
        print(f"\nFound {len(participants)} unique participants")
        
        # Initialize results dataframe
        results = pd.DataFrame({'participantId': participants})
        print(f"Initialized results dataframe with {len(results)} participants")
        
        # Calculate VWM median RT
        print("\nCalculating VWM median RT...")
        vwm_rt_data = trial_data[
            (trial_data['isPractice'] == False) & 
            (trial_data['trial_excluded_VWM'] == False) & 
            (trial_data['VWM_timeout'] == False)
        ].copy()
        print(f"VWM RT data after filtering: {len(vwm_rt_data)} trials")
        
        vwm_rt_medians = vwm_rt_data.groupby('participantId')['VWM_rt_ms'].agg(['median', 'count']).reset_index()
        vwm_rt_medians.columns = ['participantId', 'VWM_median_rt_raw', 'VWM_valid_trials_count']
        print("VWM RT medians calculated:")
        print(vwm_rt_medians.head(2))
        
        # Calculate MRT median RT
        print("\nCalculating MRT median RT...")
        mrt_rt_data = trial_data[
            (trial_data['isPractice'] == False) & 
            (trial_data['trial_excluded_MRT'] == False) & 
            (trial_data['MRT_timeout'] == False)
        ].copy()
        print(f"MRT RT data after filtering: {len(mrt_rt_data)} trials")
        
        mrt_rt_medians = mrt_rt_data.groupby('participantId')['MRT_rt_ms'].agg(['median', 'count']).reset_index()
        mrt_rt_medians.columns = ['participantId', 'MRT_median_rt_raw', 'MRT_valid_trials_count']
        print("MRT RT medians calculated:")
        print(mrt_rt_medians.head(2))
        
        # Calculate VWM accuracy
        print("\nCalculating VWM accuracy...")
        vwm_acc_data = trial_data[
            (trial_data['isPractice'] == False) & 
            (trial_data['trial_excluded_VWM'] == False) & 
            (trial_data['VWM_timeout'] == False)
        ].copy()
        
        vwm_acc_data['VWM_correct'] = vwm_acc_data['VWM_error_absolute_degrees'] <= 15
        vwm_accuracy = vwm_acc_data.groupby('participantId')['VWM_correct'].mean().reset_index()
        vwm_accuracy.columns = ['participantId', 'VWM_accuracy_raw']
        print("VWM accuracy calculated:")
        print(vwm_accuracy.head(2))
        
        # Calculate MRT accuracy
        print("\nCalculating MRT accuracy...")
        mrt_acc_data = trial_data[
            (trial_data['isPractice'] == False) & 
            (trial_data['trial_excluded_MRT'] == False) & 
            (trial_data['MRT_timeout'] == False)
        ].copy()
        
        mrt_accuracy = mrt_acc_data.groupby('participantId')['MRT_isCorrect'].mean().reset_index()
        mrt_accuracy.columns = ['participantId', 'MRT_accuracy_raw']
        print("MRT accuracy calculated:")
        print(mrt_accuracy.head(2))
        
        # Calculate focus loss metrics
        print("\nCalculating focus loss metrics...")
        focus_data = trial_data.groupby('participantId').agg({
            'windowFocusLostDuringTasksDuration': 'first',
            'windowFocusLostDuringTasksNum': 'first'
        }).reset_index()
        
        focus_data['focus_loss_duration_seconds_raw'] = pd.to_timedelta(focus_data['windowFocusLostDuringTasksDuration'], errors='coerce').dt.total_seconds().fillna(0.0)
        focus_data['focus_loss_instances_raw'] = focus_data['windowFocusLostDuringTasksNum'].fillna(0).astype(int)
        
        focus_metrics = focus_data[['participantId', 'focus_loss_duration_seconds_raw', 'focus_loss_instances_raw']]
        print("Focus loss metrics calculated:")
        print(focus_metrics.head(2))
        
        # Merge prolific session data
        print("\nMerging prolific session data...")
        session_data = prolific_data[['participant_id', 'session_duration_minutes']].copy()
        session_data.columns = ['participantId', 'session_duration_minutes_raw']
        print("Session data to merge:")
        print(session_data.head(2))
        
        # Merge all metrics
        print("\nMerging all metrics...")
        results = results.merge(vwm_rt_medians, on='participantId', how='left')
        results = results.merge(mrt_rt_medians, on='participantId', how='left')
        results = results.merge(vwm_accuracy, on='participantId', how='left')
        results = results.merge(mrt_accuracy, on='participantId', how='left')
        results = results.merge(session_data, on='participantId', how='left')
        results = results.merge(focus_metrics, on='participantId', how='left')
        
        print("Merged results:")
        print(results.columns.tolist())
        print(results.head(2))
        
        # Data validation
        print("\nData validation...")
        print(f"Participants with missing VWM RT: {results['VWM_median_rt_raw'].isna().sum()}")
        print(f"Participants with missing MRT RT: {results['MRT_median_rt_raw'].isna().sum()}")
        print(f"Participants with missing VWM accuracy: {results['VWM_accuracy_raw'].isna().sum()}")
        print(f"Participants with missing MRT accuracy: {results['MRT_accuracy_raw'].isna().sum()}")
        print(f"Participants with missing session duration: {results['session_duration_minutes_raw'].isna().sum()}")
        
        # Check for extreme outliers (>5 SD)
        print("\nChecking for extreme outliers (>5 SD)...")
        numeric_cols = ['VWM_median_rt_raw', 'MRT_median_rt_raw', 'VWM_accuracy_raw', 'MRT_accuracy_raw', 
                       'session_duration_minutes_raw', 'focus_loss_duration_seconds_raw', 'focus_loss_instances_raw']
        
        for col in numeric_cols:
            if col in results.columns:
                values = results[col].dropna()
                if len(values) > 0:
                    mean_val = values.mean()
                    std_val = values.std()
                    outliers = np.abs(values - mean_val) > 5 * std_val
                    print(f"{col}: {outliers.sum()} extreme outliers (>5 SD)")
        
        # Calculate z-scores with explicit column mapping
        print("\nCalculating z-scores...")
        z_score_map = {
            'VWM_median_rt_raw': 'VWM_median_rt_z',
            'MRT_median_rt_raw': 'MRT_median_rt_z', 
            'VWM_accuracy_raw': 'VWM_accuracy_z',
            'MRT_accuracy_raw': 'MRT_accuracy_z',
            'session_duration_minutes_raw': 'session_duration_z',
            'focus_loss_duration_seconds_raw': 'focus_loss_duration_z',
            'focus_loss_instances_raw': 'focus_loss_instances_z'
        }

        for raw_col, z_col in z_score_map.items():
            if raw_col in results.columns:
                results[z_col] = calculate_z_score(results[raw_col])
                print(f"Calculated z-scores for {raw_col} -> {z_col}")
        
        # Final results
        print("\nFinal results summary:")
        print(f"Total participants: {len(results)}")
        print("Results columns:")
        print(results.columns.tolist())
        print("\nFirst 2 rows of final results:")
        print(results.head(2))
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/domain_general_metrics_{timestamp}.csv"
        
        # Ensure correct column order
        output_cols = [
            'participantId', 'VWM_median_rt_raw', 'MRT_median_rt_raw', 'VWM_accuracy_raw', 'MRT_accuracy_raw',
            'session_duration_minutes_raw', 'focus_loss_duration_seconds_raw', 'focus_loss_instances_raw',
            'VWM_median_rt_z', 'MRT_median_rt_z', 'VWM_accuracy_z', 'MRT_accuracy_z',
            'session_duration_z', 'focus_loss_duration_z', 'focus_loss_instances_z',
            'VWM_valid_trials_count', 'MRT_valid_trials_count'
        ]
        
        # Ensure all required columns exist
        for col in output_cols:
            if col not in results.columns:
                results[col] = np.nan
        
        final_results = results[output_cols]
        
        print(f"\nSaving results to {output_file}...")
        final_results.to_csv(output_file, index=False)
        print(f"Results saved successfully to {output_file}")
        
        print(f"\nFinal output shape: {final_results.shape}")
        print("Final output columns:")
        print(final_results.columns.tolist())
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
