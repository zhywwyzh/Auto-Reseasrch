import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from sklearn.linear_model import LinearRegression
import warnings
warnings.filterwarnings('ignore')

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
    
    # Get the most recent file by modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def validate_input_data(df):
    """
    Validate that the input dataframe contains all required columns.
    
    Parameters:
    df (pd.DataFrame): Input dataframe to validate
    
    Returns:
    bool: True if all required columns are present, False otherwise
    """
    required_columns = [
        'participantId', 'MRT_angle_degrees', 'MRT_isCorrect', 
        'MRT_rt_ms', 'excluded_participant', 'valid_trial', 'isPractice'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        return False
    
    print("All required columns are present in the input data.")
    return True

def filter_data(df):
    """
    Filter data according to task requirements.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Filtered dataframe
    """
    print("Starting data filtering...")
    
    initial_rows = len(df)
    print(f"Initial number of rows: {initial_rows}")
    
    # Remove rows with null values in critical columns
    critical_columns = ['participantId', 'MRT_angle_degrees', 'MRT_isCorrect', 
                       'MRT_rt_ms', 'excluded_participant', 'valid_trial', 'isPractice']
    
    df_clean = df.dropna(subset=critical_columns)
    print(f"Rows after removing null values in critical columns: {len(df_clean)}")
    
    # Filter for non-excluded participants
    df_filtered = df_clean[df_clean['excluded_participant'] == False].copy()
    print(f"Rows after excluding participants (excluded_participant = False): {len(df_filtered)}")
    
    # Filter for test trials only (not practice)
    df_filtered = df_filtered[df_filtered['isPractice'] == False].copy()
    print(f"Rows after excluding practice trials (isPractice = False): {len(df_filtered)}")
    
    # Filter for valid trials only
    df_filtered = df_filtered[df_filtered['valid_trial'] == True].copy()
    print(f"Rows after including only valid trials (valid_trial = True): {len(df_filtered)}")
    
    print(f"Total rows excluded: {initial_rows - len(df_filtered)}")
    
    return df_filtered

def calculate_participant_metrics(df):
    """
    Calculate condition-specific metrics per participant.
    
    Parameters:
    df (pd.DataFrame): Filtered input dataframe
    
    Returns:
    pd.DataFrame: Dataframe with participant metrics
    """
    print("Calculating participant metrics...")
    
    # Expected rotation angles
    expected_angles = [0, 50, 100, 150]
    
    # Initialize results list
    results = []
    
    # Get unique participants
    participants = df['participantId'].unique()
    print(f"Processing {len(participants)} participants...")
    
    for participant in participants:
        print(f"Processing participant: {participant}")
        
        participant_data = df[df['participantId'] == participant].copy()
        
        # Initialize participant result dictionary
        participant_result = {'participantId': participant}
        
        # Check if participant has data for all angles
        participant_angles = sorted(participant_data['MRT_angle_degrees'].unique())
        has_all_angles = set(participant_angles) == set(expected_angles)
        
        print(f"  Participant {participant} has angles: {participant_angles}")
        print(f"  Has all required angles: {has_all_angles}")
        
        # Calculate metrics for each angle
        angle_accuracies = []
        angle_log_rts = []
        angles_for_regression = []
        
        for angle in expected_angles:
            angle_data = participant_data[participant_data['MRT_angle_degrees'] == angle]
            
            if len(angle_data) == 0:
                # No data for this angle
                participant_result[f'mean_accuracy_{angle}deg'] = np.nan
                participant_result[f'mean_log_rt_{angle}deg'] = np.nan
                print(f"    No data for {angle}° angle")
            else:
                # Calculate accuracy (proportion of correct trials)
                accuracy = angle_data['MRT_isCorrect'].mean()
                participant_result[f'mean_accuracy_{angle}deg'] = accuracy
                angle_accuracies.append(accuracy)
                
                # Calculate mean log RT for correct trials only
                correct_trials = angle_data[angle_data['MRT_isCorrect'] == True]
                if len(correct_trials) > 0:
                    log_rts = np.log(correct_trials['MRT_rt_ms'])
                    mean_log_rt = log_rts.mean()
                    participant_result[f'mean_log_rt_{angle}deg'] = mean_log_rt
                    angle_log_rts.append(mean_log_rt)
                else:
                    participant_result[f'mean_log_rt_{angle}deg'] = np.nan
                    angle_log_rts.append(np.nan)
                    print(f"    No correct trials for {angle}° angle")
                
                angles_for_regression.append(angle)
                
                print(f"    {angle}°: accuracy={accuracy:.3f}, trials={len(angle_data)}, correct_trials={len(correct_trials) if len(correct_trials) > 0 else 0}")
        
        # Calculate slope parameters using linear regression
        valid_slope_calculation = True
        
        # RT slope calculation
        if len(angles_for_regression) >= 2 and not all(np.isnan(angle_log_rts)):
            # Remove NaN values for regression
            valid_indices = ~np.isnan(angle_log_rts)
            if sum(valid_indices) >= 2:
                X_rt = np.array(angles_for_regression)[valid_indices].reshape(-1, 1)
                y_rt = np.array(angle_log_rts)[valid_indices]
                
                rt_model = LinearRegression()
                rt_model.fit(X_rt, y_rt)
                participant_result['MRT_RT_Angle_Slope'] = rt_model.coef_[0]
                print(f"    RT slope: {rt_model.coef_[0]:.6f}")
            else:
                participant_result['MRT_RT_Angle_Slope'] = np.nan
                valid_slope_calculation = False
                print(f"    Insufficient valid RT data for slope calculation")
        else:
            participant_result['MRT_RT_Angle_Slope'] = np.nan
            valid_slope_calculation = False
            print(f"    Insufficient RT data for slope calculation")
        
        # Accuracy slope calculation
        if len(angles_for_regression) >= 2 and not all(np.isnan(angle_accuracies)):
            # Remove NaN values for regression
            valid_indices = ~np.isnan(angle_accuracies)
            if sum(valid_indices) >= 2:
                X_acc = np.array(angles_for_regression)[valid_indices].reshape(-1, 1)
                y_acc = np.array(angle_accuracies)[valid_indices]
                
                acc_model = LinearRegression()
                acc_model.fit(X_acc, y_acc)
                participant_result['MRT_Accuracy_Angle_Slope'] = acc_model.coef_[0]
                print(f"    Accuracy slope: {acc_model.coef_[0]:.6f}")
            else:
                participant_result['MRT_Accuracy_Angle_Slope'] = np.nan
                valid_slope_calculation = False
                print(f"    Insufficient valid accuracy data for slope calculation")
        else:
            participant_result['MRT_Accuracy_Angle_Slope'] = np.nan
            valid_slope_calculation = False
            print(f"    Insufficient accuracy data for slope calculation")
        
        participant_result['valid_slope_calculation'] = valid_slope_calculation
        
        results.append(participant_result)
    
    results_df = pd.DataFrame(results)
    print(f"Completed metrics calculation for {len(results_df)} participants")
    
    return results_df

def main():
    """
    Main function to execute the MRT performance metrics calculation.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT performance metrics calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/MRT_cleaned_data_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Read the input CSV file
        print("Reading input CSV file...")
        df = pd.read_csv(input_file)
        
        print(f"Input data shape: {df.shape}")
        print("Input data columns:")
        print(df.columns.tolist())
        print("\nFirst 3 rows of input data:")
        print(df.head(3))
        
        # Print unique values for key experimental design parameters
        print("\nUnique values in key experimental design columns:")
        if 'MRT_angle_degrees' in df.columns:
            print(f"MRT_angle_degrees: {sorted(df['MRT_angle_degrees'].unique())}")
        if 'excluded_participant' in df.columns:
            print(f"excluded_participant: {sorted(df['excluded_participant'].unique())}")
        if 'valid_trial' in df.columns:
            print(f"valid_trial: {sorted(df['valid_trial'].unique())}")
        if 'isPractice' in df.columns:
            print(f"isPractice: {sorted(df['isPractice'].unique())}")
        if 'MRT_isCorrect' in df.columns:
            print(f"MRT_isCorrect: {sorted(df['MRT_isCorrect'].unique())}")
        
        # Print data types for measured variables
        print("\nData types for measured variables:")
        if 'MRT_rt_ms' in df.columns:
            print(f"MRT_rt_ms: {df['MRT_rt_ms'].dtype}")
        if 'participantId' in df.columns:
            print(f"participantId: {df['participantId'].dtype}")
        
        # Validate input data
        if not validate_input_data(df):
            return 1
        
        # Filter data according to requirements
        df_filtered = filter_data(df)
        
        if len(df_filtered) == 0:
            print("ERROR: No data remaining after filtering")
            return 1
        
        print(f"Filtered data shape: {df_filtered.shape}")
        print("First 2 rows of filtered data:")
        print(df_filtered.head(2))
        
        # Calculate participant metrics
        results_df = calculate_participant_metrics(df_filtered)
        
        if len(results_df) == 0:
            print("ERROR: No participant metrics calculated")
            return 1
        
        print(f"Results data shape: {results_df.shape}")
        print("Results data columns:")
        print(results_df.columns.tolist())
        print("\nFirst 2 rows of results:")
        print(results_df.head(2))
        
        # Generate timestamp for output filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'outputs/MRT_performance_metrics_{timestamp}.csv'
        
        # Save results to CSV
        print(f"Saving results to: {output_file}")
        results_df.to_csv(output_file, index=False)
        
        # Print summary statistics
        print("\nSummary statistics:")
        print(f"Total participants processed: {len(results_df)}")
        print(f"Participants with valid slope calculations: {results_df['valid_slope_calculation'].sum()}")
        print(f"Participants with invalid slope calculations: {(~results_df['valid_slope_calculation']).sum()}")
        
        # Print some example slopes
        valid_slopes = results_df[results_df['valid_slope_calculation'] == True]
        if len(valid_slopes) > 0:
            print(f"\nExample RT slopes (first 5 valid participants):")
            print(valid_slopes[['participantId', 'MRT_RT_Angle_Slope']].head())
            print(f"\nExample Accuracy slopes (first 5 valid participants):")
            print(valid_slopes[['participantId', 'MRT_Accuracy_Angle_Slope']].head())
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)