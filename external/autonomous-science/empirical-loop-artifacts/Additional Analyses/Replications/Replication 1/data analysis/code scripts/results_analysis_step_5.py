import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to search for
    
    Returns:
    str: Path to the most recent file matching the pattern, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def calculate_focus_loss_severity_index(df):
    """
    Calculate focus loss severity index for each participant based on z-scores.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing participant data with focus loss metrics
    
    Returns:
    pd.DataFrame: DataFrame with focus loss severity metrics added
    """
    print("Calculating focus loss severity index...")
    
    # Get unique participant-level values for focus loss metrics
    participant_focus = df.groupby('participantId')[['windowFocusLostDuringTasksNum', 
                                                    'windowFocusLostDuringTasksDuration_seconds']].first().reset_index()
    
    print(f"Focus loss data for {len(participant_focus)} participants:")
    print("Columns:", list(participant_focus.columns))
    print("First 2 rows:")
    print(participant_focus.head(2))
    
    # Calculate z-scores for focus loss instances
    instances_mean = participant_focus['windowFocusLostDuringTasksNum'].mean()
    instances_std = participant_focus['windowFocusLostDuringTasksNum'].std()
    
    print(f"Focus loss instances - Mean: {instances_mean:.3f}, Std: {instances_std:.3f}")
    
    participant_focus['focus_loss_instances_zscore'] = (
        participant_focus['windowFocusLostDuringTasksNum'] - instances_mean
    ) / instances_std
    
    # Calculate z-scores for focus loss duration
    duration_mean = participant_focus['windowFocusLostDuringTasksDuration_seconds'].mean()
    duration_std = participant_focus['windowFocusLostDuringTasksDuration_seconds'].std()
    
    print(f"Focus loss duration - Mean: {duration_mean:.3f}, Std: {duration_std:.3f}")
    
    participant_focus['focus_loss_duration_zscore'] = (
        participant_focus['windowFocusLostDuringTasksDuration_seconds'] - duration_mean
    ) / duration_std
    
    # Calculate focus loss severity index
    participant_focus['focus_loss_severity_index'] = (
        participant_focus['focus_loss_instances_zscore'] + 
        participant_focus['focus_loss_duration_zscore']
    )
    
    print("Focus loss severity index calculated for all participants")
    print("Focus loss severity index range:", 
          f"{participant_focus['focus_loss_severity_index'].min():.3f} to {participant_focus['focus_loss_severity_index'].max():.3f}")
    
    return participant_focus

def calculate_vwm_rt_variability(vwm_df):
    """
    Calculate VWM response time variability metrics for each participant.
    
    Parameters:
    vwm_df (pd.DataFrame): VWM DataFrame containing trial-level data
    
    Returns:
    pd.DataFrame: DataFrame with VWM RT variability metrics
    """
    print("Calculating VWM response time variability...")
    
    # Filter for test trials only
    test_trials = vwm_df[vwm_df['trial_type'] == 'test'].copy()
    print(f"Found {len(test_trials)} test trials out of {len(vwm_df)} total trials")
    
    print("Trial type unique values:", vwm_df['trial_type'].unique())
    
    # Filter for valid RT range (200-7000ms)
    valid_trials = test_trials[
        (test_trials['VWM_rt_ms'] >= 200) & 
        (test_trials['VWM_rt_ms'] <= 7000)
    ].copy()
    
    print(f"Valid trials (200-7000ms RT): {len(valid_trials)} out of {len(test_trials)} test trials")
    
    # Calculate RT metrics using groupby for efficiency
    rt_metrics = valid_trials.groupby('participantId')['VWM_rt_ms'].agg(
        VWM_rt_mean_ms='mean',
        VWM_rt_sd_ms='std',
        valid_VWM_trials_count='count'
    ).reset_index()
    
    # Filter for minimum trial count
    rt_metrics = rt_metrics[rt_metrics['valid_VWM_trials_count'] >= 10].copy()
    
    # Calculate coefficient of variation
    rt_metrics['VWM_rt_coefficient_variation'] = rt_metrics['VWM_rt_sd_ms'] / rt_metrics['VWM_rt_mean_ms']
    
    print(f"VWM RT variability calculated for {len(rt_metrics)} participants")
    print("VWM RT variability data:")
    print("Columns:", list(rt_metrics.columns))
    print("First 2 rows:")
    print(rt_metrics.head(2))
    
    # Data validation
    cv_valid = rt_metrics[(rt_metrics['VWM_rt_coefficient_variation'] >= 0) & 
                          (rt_metrics['VWM_rt_coefficient_variation'] <= 2.0)]
    
    print(f"Participants with valid CV (0-2.0): {len(cv_valid)} out of {len(rt_metrics)}")
    
    if len(cv_valid) < len(rt_metrics):
        print("Participants with invalid CV values:")
        invalid_cv = rt_metrics[~rt_metrics['participantId'].isin(cv_valid['participantId'])]
        print(invalid_cv[['participantId', 'VWM_rt_coefficient_variation']])
    
    return rt_metrics

def main():
    """
    Main function to process VWM and MRT data and create cognitive control metrics dataset.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting cognitive control metrics calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find most recent input files
        vwm_pattern = 'outputs/VWM_cleaned_data_*.csv'
        mrt_pattern = 'outputs/MRT_cleaned_data_*.csv'
        
        vwm_file = find_most_recent_file(vwm_pattern)
        mrt_file = find_most_recent_file(mrt_pattern)
        
        if not vwm_file:
            print(f"Error: No VWM files found matching pattern {vwm_pattern}")
            return 1
        
        if not mrt_file:
            print(f"Error: No MRT files found matching pattern {mrt_pattern}")
            return 1
        
        print(f"Using VWM file: {vwm_file}")
        print(f"Using MRT file: {mrt_file}")
        
        # Load VWM data
        print("\nLoading VWM data...")
        vwm_df = pd.read_csv(vwm_file)
        vwm_df.columns = [col.strip() for col in vwm_df.columns]
        print(f"VWM data loaded: {len(vwm_df)} rows")
        print("VWM columns:", list(vwm_df.columns))
        print("First 3 rows:")
        print(vwm_df.head(3))
        
        # Verify required VWM columns
        required_vwm_cols = ['participantId', 'trial_type', 'VWM_rt_ms', 'excluded_participant',
                            'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration_seconds']
        
        missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_df.columns]
        if missing_vwm_cols:
            print(f"Error: Missing required VWM columns: {missing_vwm_cols}")
            return 1
        
        # Load MRT data
        print("\nLoading MRT data...")
        mrt_df = pd.read_csv(mrt_file)
        mrt_df.columns = [col.strip() for col in mrt_df.columns]
        print(f"MRT data loaded: {len(mrt_df)} rows")
        print("MRT columns:", list(mrt_df.columns))
        print("First 3 rows:")
        print(mrt_df.head(3))
        
        # Verify required MRT columns
        required_mrt_cols = ['participantId', 'excluded_participant']
        
        missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_df.columns]
        if missing_mrt_cols:
            print(f"Error: Missing required MRT columns: {missing_mrt_cols}")
            return 1
        
        # Filter for non-excluded participants in both datasets
        print("\nFiltering for non-excluded participants...")
        vwm_valid = vwm_df[vwm_df['excluded_participant'] == False].copy()
        mrt_valid = mrt_df[mrt_df['excluded_participant'] == False].copy()
        
        print(f"VWM valid participants: {len(vwm_valid)} rows from {vwm_valid['participantId'].nunique()} unique participants")
        print(f"MRT valid participants: {len(mrt_valid)} rows from {mrt_valid['participantId'].nunique()} unique participants")
        
        # Get participants who are valid in both datasets
        vwm_participants = set(vwm_valid['participantId'].unique())
        mrt_participants = set(mrt_valid['participantId'].unique())
        
        valid_participants = vwm_participants.intersection(mrt_participants)
        print(f"Participants valid in both datasets: {len(valid_participants)}")
        
        if len(valid_participants) == 0:
            print("Error: No participants found who are valid in both VWM and MRT datasets")
            return 1
        
        # Calculate focus loss based on ALL valid VWM participants (N=243)
        focus_metrics = calculate_focus_loss_severity_index(vwm_valid)
        
        # Filter VWM data to the final intersection for RT variability calculation
        vwm_final = vwm_valid[vwm_valid['participantId'].isin(valid_participants)].copy()
        
        print(f"Final VWM data: {len(vwm_final)} rows from {len(valid_participants)} participants")
        
        # Calculate VWM RT variability
        rt_metrics = calculate_vwm_rt_variability(vwm_final)
        
        # Merge focus loss and RT variability metrics
        print("\nMerging focus loss and RT variability metrics...")
        cognitive_metrics = pd.merge(focus_metrics, rt_metrics, on='participantId', how='inner')
        
        print(f"Final cognitive control metrics: {len(cognitive_metrics)} participants")
        print("Final dataset columns:", list(cognitive_metrics.columns))
        print("First 2 rows:")
        print(cognitive_metrics.head(2))
        
        # Select only required output columns
        output_cols = ['participantId', 'focus_loss_severity_index', 'focus_loss_instances_zscore',
                      'focus_loss_duration_zscore', 'VWM_rt_coefficient_variation', 
                      'VWM_rt_mean_ms', 'VWM_rt_sd_ms', 'valid_VWM_trials_count']
        
        final_output = cognitive_metrics[output_cols].copy()
        
        # Data validation summary
        print("\nData validation summary:")
        print(f"Total participants: {len(final_output)}")
        print(f"Focus loss severity index range: {final_output['focus_loss_severity_index'].min():.3f} to {final_output['focus_loss_severity_index'].max():.3f}")
        print(f"VWM RT CV range: {final_output['VWM_rt_coefficient_variation'].min():.3f} to {final_output['VWM_rt_coefficient_variation'].max():.3f}")
        print(f"Valid VWM trials range: {final_output['valid_VWM_trials_count'].min()} to {final_output['valid_VWM_trials_count'].max()}")
        
        # Check for outliers in focus loss metrics
        focus_outliers = final_output[
            (np.abs(final_output['focus_loss_severity_index']) > 3)
        ]
        print(f"Focus loss severity outliers (|z| > 3): {len(focus_outliers)}")
        
        # Check CV ranges
        cv_out_of_range = final_output[
            (final_output['VWM_rt_coefficient_variation'] < 0) | 
            (final_output['VWM_rt_coefficient_variation'] > 2.0)
        ]
        print(f"CV values out of range (0-2.0): {len(cv_out_of_range)}")
        
        # Save output file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'outputs/cognitive_control_metrics_{timestamp}.csv'
        
        final_output.to_csv(output_file, index=False)
        print(f"\nOutput saved to: {output_file}")
        print(f"Output file contains {len(final_output)} rows and {len(final_output.columns)} columns")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
