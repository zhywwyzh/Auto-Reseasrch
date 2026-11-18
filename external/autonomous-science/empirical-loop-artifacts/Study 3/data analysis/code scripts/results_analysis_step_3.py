import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import ast
import re

def parse_orientations_string(orientations_str):
    """
    Parse the VWM_orientations_degrees string to extract orientation values.
    
    Parameters:
    orientations_str (str): String containing orientation values, could be in various formats
    
    Returns:
    list: List of float values representing orientations
    """
    if pd.isna(orientations_str) or orientations_str == '':
        return []
    
    try:
        # Try to evaluate as a Python literal (list, tuple, etc.)
        orientations = ast.literal_eval(orientations_str)
        if isinstance(orientations, (list, tuple)):
            return [float(x) for x in orientations]
        else:
            return [float(orientations)]
    except (ValueError, SyntaxError):
        # If that fails, try to extract numbers using regex
        numbers = re.findall(r'-?\d+\.?\d*', orientations_str)
        return [float(x) for x in numbers]

def calculate_angular_difference(angle1, angle2):
    """
    Calculate the minimum angular difference between two angles in degrees.
    
    Parameters:
    angle1 (float): First angle in degrees
    angle2 (float): Second angle in degrees
    
    Returns:
    float: Minimum angular difference in degrees
    """
    diff = abs(angle1 - angle2)
    return min(diff, 180 - diff)

def find_minimum_orientation_difference(response_angle, orientations_list):
    """
    Find the minimum angular difference between response angle and any orientation in the list.
    
    Parameters:
    response_angle (float): Response angle in degrees
    orientations_list (list): List of orientation angles in degrees
    
    Returns:
    float: Minimum angular difference in degrees
    """
    if not orientations_list or pd.isna(response_angle):
        return np.inf
    
    min_diff = np.inf
    for orientation in orientations_list:
        diff = calculate_angular_difference(response_angle, orientation)
        min_diff = min(min_diff, diff)
    
    return min_diff

def apply_trial_exclusions(df):
    """
    Apply trial-level exclusion criteria and create exclusion tracking columns.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with trial data
    
    Returns:
    pd.DataFrame: Dataframe with trial_excluded and exclusion_reason columns added
    """
    print("Applying trial-level exclusion criteria...")
    
    # Initialize exclusion tracking columns
    df['trial_excluded'] = False
    df['exclusion_reason'] = ''
    
    exclusion_counts = {}
    
    # a. Anticipatory Responses: Remove trials with VWM_rt_ms <200ms OR MRT_rt_ms <200ms
    print("Checking for anticipatory responses...")
    vwm_anticipatory = (
        df['table'].str.contains('vwm', na=False) & 
        (df['VWM_rt_ms'] < 200) & 
        (~pd.isna(df['VWM_rt_ms']))
    )
    mrt_anticipatory = (
        df['table'].str.contains('mrt', na=False) & 
        (df['MRT_rt_ms'] < 200) & 
        (~pd.isna(df['MRT_rt_ms']))
    )
    anticipatory_mask = vwm_anticipatory | mrt_anticipatory

    df.loc[anticipatory_mask, 'trial_excluded'] = True
    df.loc[anticipatory_mask, 'exclusion_reason'] = 'Anticipatory_Response'
    exclusion_counts['Anticipatory_Response'] = anticipatory_mask.sum()
    print(f"Excluded {anticipatory_mask.sum()} trials for anticipatory responses")
    
    # b. MRT Extreme RTs: Remove trials with MRT_rt_ms >7000ms AND MRT_timeout=False
    print("Checking for MRT extreme RTs...")
    mrt_extreme_mask = (df['MRT_rt_ms'] > 7000) & (df['MRT_timeout'] == False) & (~df['trial_excluded'])
    df.loc[mrt_extreme_mask, 'trial_excluded'] = True
    df.loc[mrt_extreme_mask, 'exclusion_reason'] = 'MRT_Extreme_RT'
    exclusion_counts['MRT_Extreme_RT'] = mrt_extreme_mask.sum()
    print(f"Excluded {mrt_extreme_mask.sum()} trials for MRT extreme RTs")
    
    # c. VWM Extreme Responses: Parse VWM_orientations_degrees and check minimum difference
    print("Checking for VWM extreme responses...")

    # Initialize the count variable
    vwm_extreme_count = 0

    # Filter to VWM trials that haven't been excluded yet and have required data
    vwm_mask = (
        df['table'].str.contains('vwm', na=False) & 
        (~df['trial_excluded']) & 
        (~pd.isna(df['VWM_responseAngle_degrees'])) & 
        (~pd.isna(df['VWM_orientations_degrees']))
    )

    vwm_trials = df[vwm_mask].copy()

    def check_extreme_response(row):
        orientations = parse_orientations_string(row['VWM_orientations_degrees'])
        if not orientations:
            return False
        min_diff = find_minimum_orientation_difference(row['VWM_responseAngle_degrees'], orientations)
        return min_diff >= 90

    if len(vwm_trials) > 0:
        extreme_mask = vwm_trials.apply(check_extreme_response, axis=1)
        extreme_indices = vwm_trials[extreme_mask].index

        df.loc[extreme_indices, 'trial_excluded'] = True
        df.loc[extreme_indices, 'exclusion_reason'] = 'VWM_Extreme_Response'
        vwm_extreme_count = len(extreme_indices)

    exclusion_counts['VWM_Extreme_Response'] = vwm_extreme_count
    print(f"Excluded {vwm_extreme_count} trials for VWM extreme responses")
    
    # d. Technical Failures: Remove trials with missing critical response data
    print("Checking for technical failures...")
    vwm_failure_mask = df['table'].str.contains('vwm', na=False) & pd.isna(df['VWM_responseAngle_degrees'])
    mrt_failure_mask = df['table'].str.contains('mrt', na=False) & (pd.isna(df['MRT_response']) | (~df['MRT_response'].isin(['b', 'n']) & ~pd.isna(df['MRT_response'])))
    timestamp_failure_mask = (df['table'] != 'metadata') & pd.isna(df['timestamp'])
    tech_failure_mask = (vwm_failure_mask | mrt_failure_mask | timestamp_failure_mask) & (~df['trial_excluded'])

    # Debugging output for technical failures
    print("Technical failure details:")
    if vwm_failure_mask.any():
        print(f"  VWM trials with missing response angle: {vwm_failure_mask.sum()}")
        print(f"    Indices: {df[vwm_failure_mask].index.tolist()}")
    if mrt_failure_mask.any():
        print(f"  MRT trials with invalid response values: {mrt_failure_mask.sum()}")
        invalid_mrt_values = df.loc[mrt_failure_mask, 'MRT_response'].unique()
        print(f"    Invalid MRT_response values: {invalid_mrt_values}")
        print(f"    Indices: {df[mrt_failure_mask].index.tolist()}")
    if timestamp_failure_mask.any():
        print(f"  Trials with missing timestamp: {timestamp_failure_mask.sum()}")
        print(f"    Indices: {df[timestamp_failure_mask].index.tolist()}")

    df.loc[tech_failure_mask, 'trial_excluded'] = True
    df.loc[tech_failure_mask, 'exclusion_reason'] = 'Technical_Failure'
    exclusion_counts['Technical_Failure'] = tech_failure_mask.sum()
    print(f"Excluded {tech_failure_mask.sum()} trials for technical failures")
    
    # Print exclusion summary
    print("\nTrial Exclusion Summary:")
    total_excluded = 0
    for reason, count in exclusion_counts.items():
        print(f"{reason}: {count} trials")
        total_excluded += count
    print(f"Total excluded trials: {total_excluded}")
    print(f"Total retained trials: {len(df) - total_excluded}")
    
    return df

def validate_cleaned_data(df):
    """
    Validate the cleaned trial data to ensure data quality.
    
    Parameters:
    df (pd.DataFrame): Cleaned dataframe
    
    Returns:
    None
    """
    print("\nValidating cleaned data...")
    
    # Check retained trials have complete response data
    retained_df = df[~df['trial_excluded']]
    print(f"Total retained trials: {len(retained_df)}")
    
    # Check VWM response angles are within 0-180° range
    vwm_angles = retained_df['VWM_responseAngle_degrees'].dropna()
    invalid_vwm_angles = ((vwm_angles < 0) | (vwm_angles > 180)).sum()
    print(f"VWM response angles outside 0-180° range: {invalid_vwm_angles}")
    
    # Check MRT responses are 'b' or 'n' only
    mrt_responses = retained_df['MRT_response'].dropna()
    invalid_mrt_responses = mrt_responses[~mrt_responses.isin(['b', 'n'])]
    if not invalid_mrt_responses.empty:
        print(f"ERROR: Invalid MRT responses found in retained data: {invalid_mrt_responses.unique().tolist()}")
        print(f"Count of invalid MRT responses: {len(invalid_mrt_responses)}")
        print(f"Invalid MRT responses details:")
        print(invalid_mrt_responses.value_counts())
    else:
        print(f"All {len(mrt_responses)} MRT responses in retained trials are valid ('b' or 'n').")
    
    # Check response times are within expected ranges
    vwm_rts = retained_df['VWM_rt_ms'].dropna()
    mrt_rts = retained_df['MRT_rt_ms'].dropna()
    
    print(f"VWM RT range: {vwm_rts.min():.2f} - {vwm_rts.max():.2f} ms")
    print(f"MRT RT range: {mrt_rts.min():.2f} - {mrt_rts.max():.2f} ms")
    
    # Check for missing data in key columns
    print("\nChecking for missing data in key columns of retained trials...")

    # VWM-specific columns
    vwm_retained = retained_df[retained_df['table'].str.contains('vwm', na=False)]
    print(f"Missing VWM_trial in retained VWM trials: {vwm_retained['VWM_trial'].isna().sum()}")

    # MRT-specific columns  
    mrt_retained = retained_df[retained_df['table'].str.contains('mrt', na=False)]
    print(f"Missing MRT_trial in retained MRT trials: {mrt_retained['MRT_trial'].isna().sum()}")

    # isPractice check on non-metadata rows
    non_metadata_retained = retained_df[retained_df['table'] != 'metadata']
    print(f"Missing isPractice in retained non-metadata trials: {non_metadata_retained['isPractice'].isna().sum()}")

    # participantId check on all retained trials
    print(f"Missing participantId in retained trials: {retained_df['participantId'].isna().sum()}")

def main():
    """
    Main function to execute the trial-level data cleaning process.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting trial-level data cleaning process...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/retained_participants_*.csv'
        input_files = glob.glob(input_pattern)
        
        if not input_files:
            print(f"No input files found matching pattern: {input_pattern}")
            return 1
        
        # Sort by modification time and get the most recent
        input_files.sort(key=os.path.getmtime, reverse=True)
        input_file = input_files[0]
        print(f"Using input file: {input_file}")
        
        # Read the input data
        print("Reading input data...")
        df = pd.read_csv(input_file)
        
        print(f"Input data shape: {df.shape}")
        print("Input columns:")
        print(df.columns.tolist())
        
        print("\nFirst 3 rows of input data:")
        print(df.head(3))
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        design_columns = ['VWM_setSize', 'VWM_delay_s', 'VWM_cueIndex', 'VWM_block', 
                         'MRT_angle_degrees', 'MRT_isReflected', 'MRT_block', 'isPractice']
        
        for col in design_columns:
            if col in df.columns:
                unique_vals = df[col].unique()
                print(f"{col}: {unique_vals}")

        # Analyze data structure
        print(f"\nData structure analysis:")
        table_counts = df['table'].value_counts()
        print("Row counts by table type:")
        for table_type, count in table_counts.items():
            print(f"  {table_type}: {count}")

        # Check for actual trial data availability
        vwm_trials = df[df['table'].str.contains('vwm', na=False)]
        mrt_trials = df[df['table'].str.contains('mrt', na=False)]
        print(f"\nVWM trials with response data: {(~pd.isna(vwm_trials['VWM_responseAngle_degrees'])).sum()}")
        print(f"MRT trials with response data: {(~pd.isna(mrt_trials['MRT_response'])).sum()}")

        # Print data types for measured variables
        print("\nData types for measured variables:")
        measured_columns = ['VWM_rt_ms', 'VWM_responseAngle_degrees', 'VWM_error_degrees',
                          'MRT_rt_ms', 'Age', 'Time_taken_minutes']
        
        for col in measured_columns:
            if col in df.columns:
                print(f"{col}: {df[col].dtype}")
        
        # Apply trial exclusion criteria
        df_cleaned = apply_trial_exclusions(df)
        
        # Validate cleaned data
        validate_cleaned_data(df_cleaned)
        
        # Prepare output columns in the required order
        output_columns = [
            'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_setSize',
            'VWM_delay_s', 'VWM_cueIndex', 'VWM_orientations_degrees',
            'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees',
            'VWM_error_degrees', 'VWM_error_absolute_degrees', 'VWM_rt_ms',
            'VWM_timeout', 'VWM_block', 'VWM_isAttentionCheck', 'MRT_trial',
            'MRT_stimulusId', 'MRT_angle_degrees', 'MRT_isReflected',
            'MRT_response', 'MRT_isCorrect', 'MRT_rt_ms', 'MRT_timeout',
            'MRT_block', 'MRT_isAttentionCheck', 'windowFocusLostDuringTasksNum',
            'windowFocusLostDuringInfoNum', 'windowFocusLostDuringTasksDuration',
            'windowFocusLostDuringInfoDuration', 'Age', 'Sex', 'Time_taken_minutes',
            'trial_excluded', 'exclusion_reason'
        ]
        
        # Select only the required columns
        df_output = df_cleaned[output_columns].copy()
        
        print(f"\nOutput data shape: {df_output.shape}")
        print("Output columns:")
        print(df_output.columns.tolist())
        
        print("\nFirst 2 rows of output data:")
        print(df_output.head(2))
        
        # Generate timestamp for output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'outputs/cleaned_trial_data_{timestamp}.csv'
        
        # Save the cleaned data
        print(f"Saving cleaned data to: {output_file}")
        df_output.to_csv(output_file, index=False)
        
        # Save exclusion summary
        exclusion_summary_file = f'outputs/exclusion_summary_{timestamp}.txt'
        with open(exclusion_summary_file, 'w') as f:
            f.write("Trial Exclusion Summary\n")
            f.write("======================\n\n")
            
            excluded_df = df_cleaned[df_cleaned['trial_excluded']]
            exclusion_counts = excluded_df['exclusion_reason'].value_counts()
            
            for reason, count in exclusion_counts.items():
                f.write(f"{reason}: {count} trials\n")
            
            f.write(f"\nTotal excluded trials: {len(excluded_df)}\n")
            f.write(f"Total retained trials: {len(df_cleaned) - len(excluded_df)}\n")
            f.write(f"Total trials: {len(df_cleaned)}\n")
            f.write(f"Exclusion rate: {len(excluded_df)/len(df_cleaned)*100:.2f}%\n")
        
        print(f"Exclusion summary saved to: {exclusion_summary_file}")
        
        # Print final exclusion summary
        print("\n" + "="*50)
        print("FINAL EXCLUSION SUMMARY")
        print("="*50)
        print(f"Data found for {len(df['participantId'].unique())} participants ({len(df)} total rows)")
        print("0 participants had incomplete data and were removed (trial-level exclusions only)")

        excluded_df = df_cleaned[df_cleaned['trial_excluded']]
        exclusion_counts = excluded_df['exclusion_reason'].value_counts()

        print("\nTrial exclusions applied:")
        for reason, count in exclusion_counts.items():
            print(f"  {count} trials were removed due to {reason}")

        total_excluded = len(excluded_df)
        total_retained = len(df_cleaned) - total_excluded
        print(f"\nFinal dataset: {total_retained} trials from {len(df_cleaned['participantId'].unique())} participants")
        print(f"Total trials excluded: {total_excluded}")
        print(f"Exclusion rate: {total_excluded/len(df_cleaned)*100:.2f}%")
        
        print("Trial-level data cleaning completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
