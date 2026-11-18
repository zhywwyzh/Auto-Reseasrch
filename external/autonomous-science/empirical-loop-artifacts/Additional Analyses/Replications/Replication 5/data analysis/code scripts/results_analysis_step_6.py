import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime

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
    # Sort by modification time, return most recent
    return max(files, key=os.path.getmtime)

def load_and_validate_data():
    """
    Load and validate input data files.
    
    Returns:
    tuple: (cognitive_data_df, reliable_params_df) or (None, None) if error
    """
    print("Starting data loading and validation...")
    
    # Find input files
    cognitive_pattern = "outputs/cleaned_cognitive_data_*.csv"
    reliable_pattern = "outputs/final_reliable_VWM_parameters_*.csv"
    
    cognitive_file = find_latest_file(cognitive_pattern)
    reliable_file = find_latest_file(reliable_pattern)
    
    if not cognitive_file:
        print(f"ERROR: No files found matching pattern {cognitive_pattern}")
        return None, None
    
    if not reliable_file:
        print(f"ERROR: No files found matching pattern {reliable_pattern}")
        return None, None
    
    print(f"Found cognitive data file: {cognitive_file}")
    print(f"Found reliable parameters file: {reliable_file}")
    
    try:
        # Load cognitive data
        print("Loading cognitive data...")
        cognitive_df = pd.read_csv(cognitive_file)
        print(f"Loaded cognitive data with shape: {cognitive_df.shape}")
        print("Cognitive data columns:")
        print(cognitive_df.columns.tolist())
        print("First 3 rows of cognitive data:")
        print(cognitive_df.head(3))
        
        # Load reliable parameters
        print("\nLoading reliable parameters...")
        reliable_df = pd.read_csv(reliable_file)
        print(f"Loaded reliable parameters with shape: {reliable_df.shape}")
        print("Reliable parameters columns:")
        print(reliable_df.columns.tolist())
        print("First 3 rows of reliable parameters:")
        print(reliable_df.head(3))
        
        # Check required columns for cognitive data
        required_cognitive_cols = [
            'participantId', 'isPractice', 'trial_type', 'VWM_error_normalized_degrees',
            'VWM_error_absolute_degrees', 'VWM_rt_ms', 'MRT_angle_degrees',
            'MRT_isCorrect', 'MRT_rt_ms', 'excluded_trial',
            'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration'
        ]
        
        missing_cognitive_cols = [col for col in required_cognitive_cols if col not in cognitive_df.columns]
        if missing_cognitive_cols:
            print(f"ERROR: Missing required columns in cognitive data: {missing_cognitive_cols}")
            return None, None
        
        # Check required columns for reliable parameters
        required_reliable_cols = ['participantId', 'kappa_concentration', 'included_in_analysis']
        missing_reliable_cols = [col for col in required_reliable_cols if col not in reliable_df.columns]
        if missing_reliable_cols:
            print(f"ERROR: Missing required columns in reliable parameters: {missing_reliable_cols}")
            return None, None
        
        print("All required columns found in both files")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"trial_type unique values: {cognitive_df['trial_type'].unique()}")
        print(f"isPractice unique values: {cognitive_df['isPractice'].unique()}")
        print(f"excluded_trial unique values: {cognitive_df['excluded_trial'].unique()}")
        print(f"MRT_angle_degrees unique values: {sorted(cognitive_df['MRT_angle_degrees'].dropna().unique())}")
        print(f"MRT_isCorrect unique values: {cognitive_df['MRT_isCorrect'].unique()}")
        print(f"included_in_analysis unique values: {reliable_df['included_in_analysis'].unique()}")
        
        # Print data types for measured variables
        print("\nData types for measured variables:")
        print(f"VWM_error_normalized_degrees type: {cognitive_df['VWM_error_normalized_degrees'].dtype}")
        print(f"VWM_error_absolute_degrees type: {cognitive_df['VWM_error_absolute_degrees'].dtype}")
        print(f"VWM_rt_ms type: {cognitive_df['VWM_rt_ms'].dtype}")
        print(f"MRT_rt_ms type: {cognitive_df['MRT_rt_ms'].dtype}")
        print(f"kappa_concentration type: {reliable_df['kappa_concentration'].dtype}")
        
        return cognitive_df, reliable_df
        
    except Exception as e:
        print(f"ERROR loading data: {str(e)}")
        return None, None

def filter_reliable_participants(cognitive_df, reliable_df):
    """
    Filter to participants with reliable VWM parameters.
    
    Parameters:
    cognitive_df (pd.DataFrame): Cognitive data
    reliable_df (pd.DataFrame): Reliable parameters data
    
    Returns:
    tuple: (filtered_cognitive_df, reliable_participants_df)
    """
    print("\nFiltering to reliable participants...")
    
    # Filter reliable participants
    reliable_participants = reliable_df[reliable_df['included_in_analysis'] == True].copy()
    print(f"Number of reliable participants: {len(reliable_participants)}")
    
    # Filter cognitive data to reliable participants
    reliable_participant_ids = set(reliable_participants['participantId'])
    cognitive_filtered = cognitive_df[cognitive_df['participantId'].isin(reliable_participant_ids)].copy()
    
    print(f"Cognitive data filtered from {len(cognitive_df)} to {len(cognitive_filtered)} trials")
    print(f"Number of unique participants in filtered cognitive data: {cognitive_filtered['participantId'].nunique()}")
    
    return cognitive_filtered, reliable_participants

def calculate_mrt_metrics(cognitive_df):
    """
    Calculate MRT performance metrics by rotation angle for each participant.
    
    Parameters:
    cognitive_df (pd.DataFrame): Filtered cognitive data
    
    Returns:
    pd.DataFrame: MRT metrics per participant and angle
    """
    print("\nCalculating MRT metrics by rotation angle...")
    
    # Filter MRT trials
    mrt_trials = cognitive_df[
        (cognitive_df['trial_type'] == 'MRT') &
        (cognitive_df['isPractice'] == False) &
        (cognitive_df['excluded_trial'] == False)
    ].copy()
    
    print(f"MRT trials after filtering: {len(mrt_trials)}")
    print(f"Unique participants in MRT trials: {mrt_trials['participantId'].nunique()}")
    print(f"MRT angle distribution: {mrt_trials['MRT_angle_degrees'].value_counts().sort_index()}")
    
    # Calculate accuracy and trial counts
    accuracy = mrt_trials.groupby(['participantId', 'MRT_angle_degrees'])['MRT_isCorrect'].mean().rename('accuracy')
    trial_counts = mrt_trials.groupby(['participantId', 'MRT_angle_degrees'])['MRT_isCorrect'].count().rename('trial_count')
    
    # Calculate log RT for correct trials
    mrt_trials['log_MRT_rt_ms'] = np.where(
        (mrt_trials['MRT_isCorrect'] == True) & (mrt_trials['MRT_rt_ms'] > 0),
        np.log(mrt_trials['MRT_rt_ms']),
        np.nan
    )
    log_rt = mrt_trials[mrt_trials['MRT_isCorrect'] == True].groupby(['participantId', 'MRT_angle_degrees'])['log_MRT_rt_ms'].mean().rename('logRT')
    
    # Combine metrics into a single DataFrame
    metrics = pd.concat([accuracy, log_rt, trial_counts], axis=1).reset_index()
    
    # Pivot to wide format
    mrt_metrics_df = metrics.pivot(index='participantId', columns='MRT_angle_degrees')
    
    # Flatten MultiIndex columns
    mrt_metrics_df.columns = [
        f"MRT_accuracy_{int(angle)}deg" if metric == 'accuracy' else
        f"MRT_logRT_{int(angle)}deg" if metric == 'logRT' else
        f"trials_per_angle_{int(angle)}deg"
        for metric, angle in mrt_metrics_df.columns
    ]
    mrt_metrics_df = mrt_metrics_df.reset_index()
    
    print(f"MRT metrics calculated for {len(mrt_metrics_df)} participants")
    print("MRT metrics dataframe columns:")
    print(mrt_metrics_df.columns.tolist())
    print("First 2 rows of MRT metrics:")
    print(mrt_metrics_df.head(2))
    
    return mrt_metrics_df

def calculate_vwm_metrics(cognitive_df):
    """
    Calculate VWM domain-general control variables for each participant.
    
    Parameters:
    cognitive_df (pd.DataFrame): Filtered cognitive data
    
    Returns:
    pd.DataFrame: VWM metrics per participant
    """
    print("\nCalculating VWM metrics...")
    
    # Filter VWM trials
    vwm_trials = cognitive_df[
        (cognitive_df['trial_type'] == 'VWM') &
        (cognitive_df['isPractice'] == False) &
        (cognitive_df['excluded_trial'] == False)
    ].copy()
    
    print(f"VWM trials after filtering: {len(vwm_trials)}")
    print(f"Unique participants in VWM trials: {vwm_trials['participantId'].nunique()}")
    
    def cv(x):
        """Custom function for coefficient of variation, handles division by zero"""
        mean_val = np.mean(x)
        return np.std(x) / mean_val if mean_val > 0 else np.nan
    
    vwm_metrics_df = vwm_trials.groupby('participantId').agg(
        VWM_mean_absolute_error=('VWM_error_absolute_degrees', 'mean'),
        VWM_error_SD=('VWM_error_normalized_degrees', 'std'),
        VWM_overall_accuracy=('VWM_error_absolute_degrees', lambda x: (x <= 15).mean()),
        VWM_RT_variability_CV=('VWM_rt_ms', cv)
    ).reset_index()
    
    print(f"VWM metrics calculated for {len(vwm_metrics_df)} participants")
    print("VWM metrics dataframe columns:")
    print(vwm_metrics_df.columns.tolist())
    print("First 2 rows of VWM metrics:")
    print(vwm_metrics_df.head(2))
    
    return vwm_metrics_df

def calculate_mrt_rt_variability(cognitive_df):
    """
    Calculate MRT intra-individual RT variability for each participant.
    
    Parameters:
    cognitive_df (pd.DataFrame): Filtered cognitive data
    
    Returns:
    pd.DataFrame: MRT RT variability per participant
    """
    print("\nCalculating MRT RT variability...")
    
    # Filter MRT correct trials
    mrt_correct_trials = cognitive_df[
        (cognitive_df['trial_type'] == 'MRT') &
        (cognitive_df['isPractice'] == False) &
        (cognitive_df['excluded_trial'] == False) &
        (cognitive_df['MRT_isCorrect'] == True)
    ].copy()
    
    print(f"MRT correct trials after filtering: {len(mrt_correct_trials)}")
    
    def cv(x):
        """Custom function for coefficient of variation, handles division by zero"""
        if len(x) <= 1:
            return np.nan
        mean_val = np.mean(x)
        return np.std(x) / mean_val if mean_val > 0 else np.nan
    
    mrt_rt_var_df = mrt_correct_trials.groupby('participantId').agg(
        MRT_RT_variability_CV=('MRT_rt_ms', cv)
    ).reset_index()
    
    print(f"MRT RT variability calculated for {len(mrt_rt_var_df)} participants")
    print("MRT RT variability dataframe columns:")
    print(mrt_rt_var_df.columns.tolist())
    print("First 2 rows of MRT RT variability:")
    print(mrt_rt_var_df.head(2))
    
    return mrt_rt_var_df

def calculate_focus_metrics(cognitive_df):
    """
    Calculate focus loss engagement metrics for each participant.
    
    Parameters:
    cognitive_df (pd.DataFrame): Filtered cognitive data
    
    Returns:
    pd.DataFrame: Focus metrics per participant
    """
    print("\nCalculating focus loss metrics...")
    
    focus_metrics = cognitive_df.groupby('participantId').agg({
        'windowFocusLostDuringTasksNum': 'first',
        'windowFocusLostDuringTasksDuration': 'first'
    }).reset_index()
    
    focus_metrics.rename(columns={
        'windowFocusLostDuringTasksNum': 'focus_loss_instances',
        'windowFocusLostDuringTasksDuration': 'focus_loss_duration_ms'
    }, inplace=True)
    
    # Convert to integer type
    focus_metrics['focus_loss_instances'] = focus_metrics['focus_loss_instances'].astype(int)
    
    print(f"Focus metrics calculated for {len(focus_metrics)} participants")
    print("Focus metrics dataframe columns:")
    print(focus_metrics.columns.tolist())
    print("First 2 rows of focus metrics:")
    print(focus_metrics.head(2))
    
    return focus_metrics

def validate_metrics(summary_df):
    """
    Validate calculated metrics.
    
    Parameters:
    summary_df (pd.DataFrame): Summary metrics dataframe
    
    Returns:
    pd.DataFrame: Validated summary dataframe with additional validation columns
    """
    print("\nValidating metrics...")
    
    # Check accuracy values are between 0 and 1
    accuracy_cols = [col for col in summary_df.columns if 'accuracy' in col]
    for col in accuracy_cols:
        invalid_accuracy = summary_df[(summary_df[col] < 0) | (summary_df[col] > 1)].shape[0]
        if invalid_accuracy > 0:
            print(f"WARNING: {invalid_accuracy} participants have invalid {col} values")
    
    # Check for sufficient trial counts per angle (minimum 8 trials)
    trial_cols = [col for col in summary_df.columns if 'trials_per_angle' in col]
    summary_df['sufficient_data_all_angles'] = True
    
    for col in trial_cols:
        insufficient = summary_df[col] < 8
        summary_df.loc[insufficient, 'sufficient_data_all_angles'] = False
        print(f"{col}: {insufficient.sum()} participants have < 8 trials")
    
    sufficient_count = summary_df['sufficient_data_all_angles'].sum()
    print(f"Participants with sufficient data for all angles: {sufficient_count}/{len(summary_df)}")
    
    # Verify RT distributions after log transformation
    log_rt_cols = [col for col in summary_df.columns if 'logRT' in col]
    for col in log_rt_cols:
        valid_values = summary_df[col].dropna()
        if len(valid_values) > 0:
            print(f"{col}: mean={valid_values.mean():.3f}, std={valid_values.std():.3f}, range=[{valid_values.min():.3f}, {valid_values.max():.3f}]")
    
    print("Metrics validation completed")
    return summary_df

def main():
    """
    Main function to execute the cognitive summary metrics calculation.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting cognitive summary metrics calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Load and validate data
        cognitive_df, reliable_df = load_and_validate_data()
        if cognitive_df is None or reliable_df is None:
            return 1
        
        # Filter to reliable participants
        cognitive_filtered, reliable_participants = filter_reliable_participants(cognitive_df, reliable_df)
        
        # Calculate MRT metrics
        mrt_metrics = calculate_mrt_metrics(cognitive_filtered)
        
        # Calculate VWM metrics
        vwm_metrics = calculate_vwm_metrics(cognitive_filtered)
        
        # Calculate MRT RT variability
        mrt_rt_var = calculate_mrt_rt_variability(cognitive_filtered)
        
        # Calculate focus metrics
        focus_metrics = calculate_focus_metrics(cognitive_filtered)
        
        # Merge all metrics
        print("\nMerging all metrics...")
        summary_df = reliable_participants[['participantId', 'kappa_concentration']].copy()
        
        summary_df = summary_df.merge(mrt_metrics, on='participantId', how='left')
        summary_df = summary_df.merge(vwm_metrics, on='participantId', how='left')
        summary_df = summary_df.merge(mrt_rt_var, on='participantId', how='left')
        summary_df = summary_df.merge(focus_metrics, on='participantId', how='left')
        
        print(f"Summary dataframe shape: {summary_df.shape}")
        print("Summary dataframe columns:")
        print(summary_df.columns.tolist())
        print("First 2 rows of summary dataframe:")
        print(summary_df.head(2))
        
        # Validate metrics
        summary_df = validate_metrics(summary_df)
        
        # Ensure all required columns are present
        required_output_cols = [
            'participantId', 'kappa_concentration',
            'MRT_accuracy_0deg', 'MRT_accuracy_50deg', 'MRT_accuracy_100deg', 'MRT_accuracy_150deg',
            'MRT_logRT_0deg', 'MRT_logRT_50deg', 'MRT_logRT_100deg', 'MRT_logRT_150deg',
            'VWM_mean_absolute_error', 'VWM_error_SD', 'VWM_overall_accuracy', 'VWM_RT_variability_CV',
            'MRT_RT_variability_CV', 'focus_loss_instances', 'focus_loss_duration_ms',
            'trials_per_angle_0deg', 'trials_per_angle_50deg', 'trials_per_angle_100deg', 'trials_per_angle_150deg',
            'sufficient_data_all_angles'
        ]
        
        # Reorder columns to match required output
        summary_df = summary_df[required_output_cols]
        
        # Save output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/cognitive_summary_metrics_{timestamp}.csv"
        
        print(f"\nSaving output to: {output_file}")
        summary_df.to_csv(output_file, index=False)
        
        print(f"Successfully saved {len(summary_df)} participants to output file")
        print(f"Output file shape: {summary_df.shape}")
        print("Final output columns:")
        print(summary_df.columns.tolist())
        
        # Print summary statistics
        print("\nSummary statistics:")
        print(f"Total participants: {len(summary_df)}")
        print(f"Participants with sufficient data for all angles: {summary_df['sufficient_data_all_angles'].sum()}")
        print(f"Mean kappa concentration: {summary_df['kappa_concentration'].mean():.3f}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
