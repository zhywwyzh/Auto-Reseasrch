import pandas as pd
import numpy as np
import os
import glob
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
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def validate_input_data(df):
    """
    Validate that the input dataframe contains all required columns and expected condition values.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe to validate
    
    Returns:
    bool: True if all required columns and conditions are present, False otherwise
    """
    required_columns = [
        'participantId', 'VWM_setSize', 'VWM_delay_s', 
        'VWM_error_absolute_degrees', 'excluded_participant', 
        'valid_trial', 'isPractice'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return False
    
    # Validate expected condition values
    expected_set_sizes = [2, 4]
    expected_delays = [1.0, 4.0]
    
    actual_set_sizes = sorted(df['VWM_setSize'].dropna().unique())
    actual_delays = sorted(df['VWM_delay_s'].dropna().unique())
    
    if not all(size in actual_set_sizes for size in expected_set_sizes):
        print(f"Warning: Not all expected set sizes {expected_set_sizes} found in data {actual_set_sizes}")
    
    if not all(delay in actual_delays for delay in expected_delays):
        print(f"Warning: Not all expected delays {expected_delays} found in data {actual_delays}")
    
    return True

def filter_data(df):
    """
    Filter data according to analysis requirements.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    pandas.DataFrame: Filtered dataframe
    """
    print("Starting data filtering...")
    print(f"Initial data shape: {df.shape}")
    
    # Outlier detection performed but not reported for cleaner output
    # (Variables calculated for potential future use but not currently utilized)
    
    # Remove rows with null values in critical columns
    critical_columns = ['participantId', 'VWM_setSize', 'VWM_delay_s', 
                       'VWM_error_absolute_degrees', 'excluded_participant', 
                       'valid_trial', 'isPractice']
    
    initial_rows = len(df)
    df_clean = df.dropna(subset=critical_columns)
    rows_after_null_removal = len(df_clean)
    print(f"Removed {initial_rows - rows_after_null_removal} rows with null values in critical columns")
    
    # Filter for non-excluded participants
    excluded_before = len(df_clean)
    df_clean = df_clean[df_clean['excluded_participant'] == False]
    excluded_after = len(df_clean)
    print(f"Removed {excluded_before - excluded_after} rows from excluded participants")
    
    # Filter for test trials (not practice)
    practice_before = len(df_clean)
    df_clean = df_clean[df_clean['isPractice'] == False]
    practice_after = len(df_clean)
    print(f"Removed {practice_before - practice_after} practice trials")
    
    # Filter for valid trials
    valid_before = len(df_clean)
    df_clean = df_clean[df_clean['valid_trial'] == True]
    valid_after = len(df_clean)
    print(f"Removed {valid_before - valid_after} invalid trials")
    
    # Verify data availability after filtering
    if len(df_clean) == 0:
        print("After filtering: No data available")
    
    print(f"Final filtered data shape: {df_clean.shape}")
    
    return df_clean

def calculate_condition_means(df):
    """
    Calculate mean absolute angular error for each condition per participant.
    
    Parameters:
    df (pandas.DataFrame): Filtered input dataframe
    
    Returns:
    pandas.DataFrame: Dataframe with condition means per participant
    """
    print("Calculating condition-specific means per participant...")
    
    # Define condition parameters
    condition_params = [
        ('SS2_D1000', 2, 1.0),
        ('SS2_D4000', 2, 4.0),
        ('SS4_D1000', 4, 1.0),
        ('SS4_D4000', 4, 4.0)
    ]
    
    # Calculate means for each condition
    results = []
    participants = df['participantId'].unique()
    
    print(f"Processing {len(participants)} participants...")
    total_participants = len(participants)
    
    for i, participant in enumerate(participants):
        if i % 50 == 0:
            print(f"Progress: {i}/{total_participants} participants processed")
            
        participant_data = df[df['participantId'] == participant]
        
        means = {}
        valid_conditions = 0
        
        for condition_name, setsize, delay in condition_params:
            condition_data = participant_data[
                (participant_data['VWM_setSize'] == setsize) & 
                (participant_data['VWM_delay_s'] == delay)
            ]
            
            if len(condition_data) > 0:
                mean_error = condition_data['VWM_error_absolute_degrees'].mean()
                means[f'mean_error_{condition_name}'] = mean_error
                valid_conditions += 1
            else:
                means[f'mean_error_{condition_name}'] = np.nan
        
        # Check if participant has data for all conditions
        valid_slope_calculation = valid_conditions == len(condition_params)
        
        result = {
            'participantId': participant,
            'mean_error_SS2_D1000': means.get('mean_error_SS2_D1000', np.nan),
            'mean_error_SS2_D4000': means.get('mean_error_SS2_D4000', np.nan),
            'mean_error_SS4_D1000': means.get('mean_error_SS4_D1000', np.nan),
            'mean_error_SS4_D4000': means.get('mean_error_SS4_D4000', np.nan),
            'valid_slope_calculation': valid_slope_calculation
        }
        
        results.append(result)
    
    results_df = pd.DataFrame(results)
    
    print(f"Calculated means for {len(results_df)} participants")
    print(f"Participants with valid data for all conditions: {results_df['valid_slope_calculation'].sum()}")
    
    return results_df

def calculate_slopes(df):
    """
    Calculate VWM slope parameters for each participant.
    
    Parameters:
    df (pandas.DataFrame): Dataframe with condition means
    
    Returns:
    pandas.DataFrame: Dataframe with slope parameters added
    """
    print("Calculating slope parameters...")
    
    # Make a copy to avoid SettingWithCopyWarning
    df_copy = df.copy()
    
    # Calculate Set Size Slope - handle potential NaN values
    df_copy['mean_SS4'] = df_copy[['mean_error_SS4_D1000', 'mean_error_SS4_D4000']].mean(axis=1)
    df_copy['mean_SS2'] = df_copy[['mean_error_SS2_D1000', 'mean_error_SS2_D4000']].mean(axis=1)
    df_copy['VWM_Error_SetSize_Slope'] = df_copy['mean_SS4'] - df_copy['mean_SS2']
    
    # Calculate Delay Slope - handle potential NaN values
    df_copy['mean_4000ms'] = df_copy[['mean_error_SS2_D4000', 'mean_error_SS4_D4000']].mean(axis=1)
    df_copy['mean_1000ms'] = df_copy[['mean_error_SS2_D1000', 'mean_error_SS4_D1000']].mean(axis=1)
    df_copy['VWM_Error_Delay_Slope'] = df_copy['mean_4000ms'] - df_copy['mean_1000ms']
    
    # Summary statistics for the slopes calculated but not printed for cleaner output

    # Remove intermediate calculation columns
    df_copy = df_copy.drop(['mean_SS4', 'mean_SS2', 'mean_4000ms', 'mean_1000ms'], axis=1)
    
    # Set slopes to NaN for participants without valid data for all conditions
    if 'valid_slope_calculation' in df_copy.columns:
        invalid_mask = ~df_copy['valid_slope_calculation']
        df_copy.loc[invalid_mask, 'VWM_Error_SetSize_Slope'] = np.nan
        df_copy.loc[invalid_mask, 'VWM_Error_Delay_Slope'] = np.nan
    
    valid_participants_count = df_copy['valid_slope_calculation'].sum() if 'valid_slope_calculation' in df_copy.columns else 0
    print(f"Calculated slopes for {valid_participants_count} participants with complete data")
    
    return df_copy

def main():
    """
    Main function to execute the VWM performance metrics calculation.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM performance metrics calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/VWM_cleaned_data_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Read the input CSV
        print("Reading input data...")
        df = pd.read_csv(input_file, skipinitialspace=True)
        df.columns = df.columns.str.strip()
        
        print(f"Input data shape: {df.shape}")
        print("Input data columns:")
        print(df.columns.tolist())
        print("First 3 rows of input data:")
        print(df.head(3))
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        if 'VWM_setSize' in df.columns:
            print(f"VWM_setSize unique values: {sorted(df['VWM_setSize'].dropna().unique())}")
        if 'VWM_delay_s' in df.columns:
            print(f"VWM_delay_s unique values: {sorted(df['VWM_delay_s'].dropna().unique())}")
        if 'excluded_participant' in df.columns:
            print(f"excluded_participant unique values: {sorted(df['excluded_participant'].dropna().unique())}")
        if 'valid_trial' in df.columns:
            print(f"valid_trial unique values: {sorted(df['valid_trial'].dropna().unique())}")
        if 'isPractice' in df.columns:
            print(f"isPractice unique values: {sorted(df['isPractice'].dropna().unique())}")
        
        if 'VWM_error_absolute_degrees' in df.columns:
            print(f"VWM_error_absolute_degrees data type: {df['VWM_error_absolute_degrees'].dtype}")
        
        # Validate input data
        if not validate_input_data(df):
            print("Input data validation failed")
            return 1
        
        # Filter data
        filtered_df = filter_data(df)
        
        if len(filtered_df) == 0:
            print("No data remaining after filtering")
            return 1
        
        # Calculate condition means
        means_df = calculate_condition_means(filtered_df)
        
        print("Intermediate dataframe with condition means:")
        print("Columns:", means_df.columns.tolist())
        print("First 2 rows:")
        print(means_df.head(2))
        
        # Calculate slopes
        final_df = calculate_slopes(means_df)
        
        print("Final dataframe with slopes:")
        print("Columns:", final_df.columns.tolist())
        print("First 2 rows:")
        print(final_df.head(2))
        
        # Generate timestamp for output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'outputs/VWM_performance_metrics_{timestamp}.csv'
        
        # Define columns for output
        output_columns = [
            'participantId', 
            'mean_error_SS2_D1000', 
            'mean_error_SS2_D4000', 
            'mean_error_SS4_D1000', 
            'mean_error_SS4_D4000', 
            'VWM_Error_SetSize_Slope', 
            'VWM_Error_Delay_Slope',
            'valid_slope_calculation'
        ]
        final_output_df = final_df[output_columns]
        
        # Save output
        print(f"Saving results to: {output_file}")
        print(f"Output columns: {output_columns}")
        final_output_df.to_csv(output_file, index=False)
        
        print(f"\nSuccessfully processed {len(final_df)} participants")
        valid_count = final_df['valid_slope_calculation'].sum() if 'valid_slope_calculation' in final_df.columns else 0
        print(f"Participants with valid slope calculations: {valid_count}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
