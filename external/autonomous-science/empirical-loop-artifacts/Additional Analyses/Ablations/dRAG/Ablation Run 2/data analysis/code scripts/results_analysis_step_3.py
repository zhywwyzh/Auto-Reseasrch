import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

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
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def calculate_vwm_mean_error(df):
    """
    Calculate mean absolute error on VWM task for each participant.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with trial-level data
    
    Returns:
    pandas.DataFrame: DataFrame with participantId and mean_vwm_absolute_error
    """
    print("Calculating VWM mean absolute error...")
    
    # Filter for VWM test trials (not practice)
    vwm_test_data = df[(df['isPractice'] == False) & (df['table'] == 'vwm_test')].copy()
    
    print(f"Found {len(vwm_test_data)} VWM test trials")
    print("VWM test data columns:", list(vwm_test_data.columns))
    if len(vwm_test_data) > 0:
        print("First 2 rows of VWM test data:")
        print(vwm_test_data.head(2))
    
    # Calculate mean absolute error per participant
    vwm_metrics = vwm_test_data.groupby('participantId')['VWM_error_absolute_degrees'].mean().reset_index()
    vwm_metrics.rename(columns={'VWM_error_absolute_degrees': 'mean_vwm_absolute_error'}, inplace=True)
    
    print(f"Calculated VWM metrics for {len(vwm_metrics)} participants")
    print("VWM metrics columns:", list(vwm_metrics.columns))
    print("First 2 rows of VWM metrics:")
    print(vwm_metrics.head(2))
    
    return vwm_metrics

def calculate_mrt_cv(df):
    """
    Calculate response time coefficient of variation for correct MRT trials.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with trial-level data
    
    Returns:
    pandas.DataFrame: DataFrame with participantId and mrt_rt_coefficient_variation
    """
    print("Calculating MRT coefficient of variation...")
    
    # Filter for correct MRT test trials (not practice)
    mrt_test_data = df[(df['isPractice'] == False) & 
                       (df['table'] == 'mrt_test') & 
                       (df['MRT_isCorrect'] == True)].copy()
    
    print(f"Found {len(mrt_test_data)} correct MRT test trials")
    print("MRT test data columns:", list(mrt_test_data.columns))
    if len(mrt_test_data) > 0:
        print("First 2 rows of MRT test data:")
        print(mrt_test_data.head(2))
    
    # Calculate CV per participant
    mrt_stats = mrt_test_data.groupby('participantId')['MRT_rt_ms'].agg(['mean', 'std']).reset_index()
    mrt_stats['mrt_rt_coefficient_variation'] = mrt_stats['std'] / mrt_stats['mean']
    # Preserve NaN values for cases where CV cannot be calculated (e.g., < 2 trials)
    print(f"Valid CV values: {mrt_stats['mrt_rt_coefficient_variation'].notna().sum()}, NaN CV values: {mrt_stats['mrt_rt_coefficient_variation'].isna().sum()}")
    mrt_cv = mrt_stats[['participantId', 'mrt_rt_coefficient_variation']]
    
    print(f"Calculated MRT CV for {len(mrt_cv)} participants")
    print("MRT CV columns:", list(mrt_cv.columns))
    print("First 2 rows of MRT CV:")
    print(mrt_cv.head(2))
    
    return mrt_cv

def extract_focus_metrics(df):
    """
    Extract focus loss metrics per participant.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with trial-level data
    
    Returns:
    pandas.DataFrame: DataFrame with participantId, focus_loss_instances_total, and focus_loss_duration_seconds_total
    """
    print("Extracting focus loss metrics...")
    
    # Get unique values per participant (should be consistent across trials)
    focus_metrics = df.groupby('participantId').agg({
        'windowFocusLostDuringTasksNum': 'first',
        'windowFocusLostDuringTasksDuration': 'first'
    }).reset_index()
    
    # Convert duration string to total seconds, handling NaNs
    focus_metrics['windowFocusLostDuringTasksDuration'] = pd.to_timedelta(
        focus_metrics['windowFocusLostDuringTasksDuration'], errors='coerce'
    ).dt.total_seconds().fillna(0)
    
    # Fill NaNs and cast count to integer
    focus_metrics['windowFocusLostDuringTasksNum'] = focus_metrics['windowFocusLostDuringTasksNum'].fillna(0).astype(int)
    
    focus_metrics.rename(columns={
        'windowFocusLostDuringTasksNum': 'focus_loss_instances_total',
        'windowFocusLostDuringTasksDuration': 'focus_loss_duration_seconds_total'
    }, inplace=True)
    
    print(f"Extracted focus metrics for {len(focus_metrics)} participants")
    print("Focus metrics columns:", list(focus_metrics.columns))
    print("First 2 rows of focus metrics:")
    print(focus_metrics.head(2))
    
    return focus_metrics

def extract_task_order(df):
    """
    Extract task order assignment per participant.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with trial-level data
    
    Returns:
    pandas.DataFrame: DataFrame with participantId and task_order_condition
    """
    print("Extracting task order...")
    
    # Get unique task order per participant
    task_order = df.groupby('participantId')['taskOrder'].first().reset_index()
    
    # Convert to condition labels
    task_order['task_order_condition'] = task_order['taskOrder'].map({
        1: 'VWM_first',
        2: 'MRT_first'
    })
    
    task_order_final = task_order[['participantId', 'task_order_condition']]
    
    print(f"Extracted task order for {len(task_order_final)} participants")
    print("Task order columns:", list(task_order_final.columns))
    print("First 2 rows of task order:")
    print(task_order_final.head(2))
    print("Unique task order values:", task_order['taskOrder'].unique())
    print("Unique task order condition values:", task_order_final['task_order_condition'].unique())
    
    return task_order_final

def main():
    """
    Main function to process behavioral control metrics.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting behavioral control metrics calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/cleaned_experimental_data_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"Error: No files found matching pattern {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Read the input file
        print("Reading input file...")
        df = pd.read_csv(input_file, low_memory=False)
        
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        print("All columns in input file:", list(df.columns))
        print("First 3 rows of input data:")
        print(df.head(3))
        
        # Validate required columns
        required_columns = [
            'participantId', 'table', 'isPractice', 'VWM_error_absolute_degrees',
            'MRT_rt_ms', 'MRT_isCorrect', 'windowFocusLostDuringTasksNum',
            'windowFocusLostDuringTasksDuration', 'taskOrder'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found")
        
        # Print unique values for key experimental design parameters
        print("Unique values for key experimental design parameters:")
        print("table values:", sorted(df['table'].unique()))
        print("isPractice values:", sorted(df['isPractice'].unique()))
        print("taskOrder values:", sorted(df['taskOrder'].unique()))
        print("MRT_isCorrect values:", sorted(df['MRT_isCorrect'].unique()))
        
        # Print data types for measured variables
        print("Data types for measured variables:")
        print("VWM_error_absolute_degrees type:", df['VWM_error_absolute_degrees'].dtype)
        print("MRT_rt_ms type:", df['MRT_rt_ms'].dtype)
        print("windowFocusLostDuringTasksNum type:", df['windowFocusLostDuringTasksNum'].dtype)
        print("windowFocusLostDuringTasksDuration type:", df['windowFocusLostDuringTasksDuration'].dtype)
        
        # Calculate VWM mean absolute error
        vwm_metrics = calculate_vwm_mean_error(df)
        
        # Calculate MRT coefficient of variation
        mrt_cv = calculate_mrt_cv(df)
        
        # Extract focus loss metrics
        focus_metrics = extract_focus_metrics(df)
        
        # Extract task order
        task_order = extract_task_order(df)
        
        # Merge all metrics
        print("Merging all metrics...")
        control_metrics = vwm_metrics.copy()
        
        # Merge MRT CV
        control_metrics = control_metrics.merge(mrt_cv, on='participantId', how='outer')
        print(f"After merging MRT CV: {len(control_metrics)} participants")
        
        # Merge focus metrics
        control_metrics = control_metrics.merge(focus_metrics, on='participantId', how='outer')
        print(f"After merging focus metrics: {len(control_metrics)} participants")
        
        # Merge task order
        control_metrics = control_metrics.merge(task_order, on='participantId', how='outer')
        print(f"After merging task order: {len(control_metrics)} participants")
        
        print("Final control metrics columns:", list(control_metrics.columns))
        print("First 2 rows of final control metrics:")
        print(control_metrics.head(2))
        
        # Check for missing data
        print("Missing data summary:")
        print(control_metrics.isnull().sum())
        
        # Create output filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'outputs/behavioral_control_metrics_{timestamp}.csv'
        
        # Save the output
        print(f"Saving output to: {output_file}")
        control_metrics.to_csv(output_file, index=False)
        
        print(f"Successfully saved {len(control_metrics)} participant records to {output_file}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
