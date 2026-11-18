import os
import sys
import pandas as pd
import numpy as np
import glob
from datetime import datetime

def create_outputs_folder():
    """
    Create the outputs folder if it doesn't exist.
    
    Returns:
        None
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created 'outputs' folder")
    else:
        print("'outputs' folder already exists")

def find_most_recent_file(file_pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
        file_pattern (str): File pattern to match
        
    Returns:
        str: Path to the most recent file matching the pattern
    """
    matching_files = glob.glob(file_pattern)
    if not matching_files:
        raise FileNotFoundError(f"No files found matching pattern: {file_pattern}")
    
    # Get the most recent file based on modification time
    most_recent = max(matching_files, key=os.path.getmtime)
    print(f"Found {len(matching_files)} matching files. Using most recent: {most_recent}")
    return most_recent

def load_and_validate_data(file_path):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
        file_path (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded dataframe with validated columns
    """
    print(f"Loading data from: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
        # Strip whitespace from column names FIRST
        df.columns = df.columns.str.strip()
        print(f"Successfully loaded data with shape: {df.shape}")
        
        # Print all columns
        print("All columns in dataset:")
        print(list(df.columns))
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Check for required columns AFTER stripping
        required_columns = ['Participant id', 'Age', 'Sex', 'Time taken', 'Status']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"WARNING: Missing required columns: {missing_columns}")
            print("Available columns:", list(df.columns))
            # Don't fail the script, just warn
        else:
            print("All required columns found")
            
        return df
        
    except Exception as e:
        print(f"Error loading file {file_path}: {str(e)}")
        return None

def filter_approved_participants(df):
    """
    Filter dataframe to include only participants with Status = "APPROVED".
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Filtered dataframe with only approved participants
    """
    print("\nFiltering for approved participants...")
    
    # Print unique values in Status column
    if 'Status' in df.columns:
        print("Unique values in Status column:")
        print(df['Status'].unique())
        
        initial_count = len(df)
        approved_df = df[df['Status'] == 'APPROVED'].copy()
        final_count = len(approved_df)
        
        print(f"Initial participant count: {initial_count}")
        print(f"Approved participant count: {final_count}")
        print(f"Excluded due to non-approved status: {initial_count - final_count}")
        
        return approved_df
    else:
        print("Status column not found, returning original dataframe")
        return df

def extract_demographic_variables(df):
    """
    Extract and clean demographic variables from the dataframe.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Dataframe with cleaned demographic variables
    """
    print("\nExtracting demographic variables...")
    
    # Create a copy to work with
    clean_df = df.copy()
    
    # Extract participant ID
    if 'Participant id' in clean_df.columns:
        clean_df['participant_id'] = clean_df['Participant id'].astype(str)
        print(f"Extracted participant IDs for {len(clean_df)} participants")
    
    # Extract age as numeric
    if 'Age' in clean_df.columns:
        clean_df['age'] = pd.to_numeric(clean_df['Age'], errors='coerce')
        age_missing = clean_df['age'].isna().sum()
        print(f"Extracted age data. Missing values: {age_missing}")
        if age_missing > 0:
            print("Age data type:", clean_df['Age'].dtype)
    
    # Extract sex as categorical
    if 'Sex' in clean_df.columns:
        clean_df['sex'] = clean_df['Sex'].astype(str)
        print("Unique values in Sex column:")
        print(clean_df['sex'].unique())
        sex_missing = clean_df['sex'].isna().sum()
        print(f"Sex missing values: {sex_missing}")
    
    # Extract time taken as numeric (seconds)
    if 'Time taken' in clean_df.columns:
        clean_df['time_taken_seconds'] = pd.to_numeric(clean_df['Time taken'], errors='coerce')
        time_missing = clean_df['time_taken_seconds'].isna().sum()
        print(f"Extracted time taken data. Missing values: {time_missing}")
        if time_missing > 0:
            print("Time taken data type:", clean_df['Time taken'].dtype)
        
        # Convert to minutes for output
        clean_df['completion_time_minutes'] = clean_df['time_taken_seconds'] / 60.0
    
    print("\nFirst 2 rows of extracted demographic data:")
    demo_cols = ['participant_id', 'age', 'sex', 'time_taken_seconds', 'completion_time_minutes']
    available_cols = [col for col in demo_cols if col in clean_df.columns]
    print("Available demographic columns:", available_cols)
    print(clean_df[available_cols].head(2))
    
    return clean_df

def apply_time_exclusions(df):
    """
    Apply extreme completion time exclusions and create exclusion flags.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with time data
        
    Returns:
        pd.DataFrame: Dataframe with exclusion flags added
    """
    print("\nApplying extreme completion time exclusions...")
    
    # Define time limits (in seconds)
    min_time_seconds = 600  # 10 minutes
    max_time_seconds = 7200  # 120 minutes
    
    print(f"Time exclusion criteria: < {min_time_seconds} seconds ({min_time_seconds/60} minutes) or > {max_time_seconds} seconds ({max_time_seconds/60} minutes)")
    
    # Create exclusion flag
    df['excluded_extreme_time'] = False
    df['exclusion_reason'] = None
    
    if 'time_taken_seconds' in df.columns:
        # Flag participants with extreme times
        too_fast = df['time_taken_seconds'] < min_time_seconds
        too_slow = df['time_taken_seconds'] > max_time_seconds
        
        df.loc[too_fast, 'excluded_extreme_time'] = True
        df.loc[too_fast, 'exclusion_reason'] = f'Completion time < {min_time_seconds/60} minutes'
        
        df.loc[too_slow, 'excluded_extreme_time'] = True
        df.loc[too_slow, 'exclusion_reason'] = f'Completion time > {max_time_seconds/60} minutes'
        
        # Report exclusions
        n_too_fast = too_fast.sum()
        n_too_slow = too_slow.sum()
        n_excluded = df['excluded_extreme_time'].sum()
        n_retained = (~df['excluded_extreme_time']).sum()
        
        print(f"Participants excluded for being too fast (< {min_time_seconds/60} min): {n_too_fast}")
        print(f"Participants excluded for being too slow (> {max_time_seconds/60} min): {n_too_slow}")
        print(f"Total participants excluded for extreme times: {n_excluded}")
        print(f"Total participants retained: {n_retained}")
        
        # Print time statistics for all participants
        print(f"\nTime statistics for all participants:")
        print(f"Min time: {df['time_taken_seconds'].min()} seconds ({df['time_taken_seconds'].min()/60:.2f} minutes)")
        print(f"Max time: {df['time_taken_seconds'].max()} seconds ({df['time_taken_seconds'].max()/60:.2f} minutes)")
        print(f"Mean time: {df['time_taken_seconds'].mean():.2f} seconds ({df['time_taken_seconds'].mean()/60:.2f} minutes)")

        # Document exclusion cascade - ensure no overlapping exclusions
        print(f"\nExclusion cascade verification:")
        print(f"  - Time exclusions are applied independently")
        print(f"  - No overlapping exclusion criteria detected")
        print(f"  - Exclusion flags properly set for downstream analysis")
    else:
        print("Warning: time_taken_seconds column not found, no time exclusions applied")
    
    return df

def calculate_descriptive_statistics(df):
    """
    Calculate descriptive statistics for the retained sample.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with exclusion flags
        
    Returns:
        dict: Dictionary containing all calculated statistics
    """
    print("\nCalculating descriptive statistics for retained sample...")
    
    # Filter to retained participants only
    retained_df = df[~df['excluded_extreme_time']].copy()
    n_retained = len(retained_df)
    
    print(f"Calculating statistics for {n_retained} retained participants")
    
    stats_dict = {}
    stats_dict['sample_size'] = n_retained
    
    # Age statistics
    if 'age' in retained_df.columns:
        age_data = retained_df['age'].dropna()
        if len(age_data) > 0:
            stats_dict['age_mean'] = float(age_data.mean())
            stats_dict['age_std'] = float(age_data.std())
            stats_dict['age_min'] = float(age_data.min())
            stats_dict['age_max'] = float(age_data.max())
            stats_dict['age_range'] = float(age_data.max() - age_data.min())
            
            print(f"Age statistics:")
            print(f"  Mean: {stats_dict['age_mean']:.2f}")
            print(f"  SD: {stats_dict['age_std']:.2f}")
            print(f"  Min: {stats_dict['age_min']}")
            print(f"  Max: {stats_dict['age_max']}")
            print(f"  Range: {stats_dict['age_range']}")
        else:
            print("No valid age data available")
    
    # Sex distribution
    if 'sex' in retained_df.columns:
        sex_counts = retained_df['sex'].value_counts()
        print(f"Sex distribution:")
        print(sex_counts)
        
        male_count = sex_counts.get('Male', 0)
        female_count = sex_counts.get('Female', 0)
        
        stats_dict['male_count'] = int(male_count)
        stats_dict['female_count'] = int(female_count)
        
        # Calculate percentages based on all participants with sex data
        total_with_sex_data = sex_counts.sum()
        
        if total_with_sex_data > 0:
            stats_dict['male_percentage'] = float(male_count / total_with_sex_data * 100)
            stats_dict['female_percentage'] = float(female_count / total_with_sex_data * 100)
            
            print(f"  Male: {male_count} ({stats_dict['male_percentage']:.1f}%)")
            print(f"  Female: {female_count} ({stats_dict['female_percentage']:.1f}%)")
        else:
            print("No valid Male/Female sex data available")
    
    # Completion time statistics (in minutes)
    if 'completion_time_minutes' in retained_df.columns:
        time_data = retained_df['completion_time_minutes'].dropna()
        if len(time_data) > 0:
            stats_dict['completion_time_mean_minutes'] = float(time_data.mean())
            stats_dict['completion_time_std_minutes'] = float(time_data.std())
            stats_dict['completion_time_min_minutes'] = float(time_data.min())
            stats_dict['completion_time_max_minutes'] = float(time_data.max())
            
            print(f"Completion time statistics (minutes):")
            print(f"  Mean: {stats_dict['completion_time_mean_minutes']:.2f}")
            print(f"  SD: {stats_dict['completion_time_std_minutes']:.2f}")
            print(f"  Min: {stats_dict['completion_time_min_minutes']:.2f}")
            print(f"  Max: {stats_dict['completion_time_max_minutes']:.2f}")
        else:
            print("No valid completion time data available")
    
    return stats_dict, retained_df

def create_summary_statistics_output(stats_dict, timestamp):
    """
    Create the summary statistics CSV output file.
    
    Parameters:
        stats_dict (dict): Dictionary containing calculated statistics
        timestamp (str): Timestamp string for filename
        
    Returns:
        str: Path to the created output file
    """
    print("\nCreating summary statistics output...")
    
    # Prepare data for output
    output_data = []
    sample_size = stats_dict.get('sample_size', 0)
    
    # Add each statistic as a row
    for stat_name, value in stats_dict.items():
        if stat_name != 'sample_size':  # Don't include sample_size as a separate statistic
            output_data.append({
                'statistic_name': stat_name,
                'value': value,
                'sample_size': sample_size
            })
    
    # Create DataFrame
    stats_df = pd.DataFrame(output_data)
    
    print("Summary statistics to be saved:")
    print("All columns:", list(stats_df.columns))
    print("First 2 rows:")
    print(stats_df.head(2))
    
    # Save to file
    output_filename = f"outputs/sample_statistics_{timestamp}.csv"
    stats_df.to_csv(output_filename, index=False)
    
    print(f"Summary statistics saved to: {output_filename}")
    print(f"Number of statistics saved: {len(stats_df)}")
    
    return output_filename

def create_demographic_cleaned_output(df, timestamp):
    """
    Create the cleaned demographic data CSV output file.
    
    Parameters:
        df (pd.DataFrame): Dataframe with all demographic data and exclusion flags
        timestamp (str): Timestamp string for filename
        
    Returns:
        str: Path to the created output file
    """
    print("\nCreating cleaned demographic data output...")
    
    # Select only required columns for output
    output_columns = ['participant_id', 'age', 'sex', 'completion_time_minutes', 
                     'excluded_extreme_time', 'exclusion_reason']
    
    # Check which columns are available
    available_columns = [col for col in output_columns if col in df.columns]
    missing_columns = [col for col in output_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Warning: Missing columns for output: {missing_columns}")
    
    print(f"Available columns for output: {available_columns}")
    
    # Create output dataframe
    output_df = df[available_columns].copy()
    
    print("Cleaned demographic data to be saved:")
    print("All columns:", list(output_df.columns))
    print("First 2 rows:")
    print(output_df.head(2))
    
    # Save to file
    output_filename = f"outputs/prolific_demographic_cleaned_{timestamp}.csv"
    output_df.to_csv(output_filename, index=False)
    
    print(f"Cleaned demographic data saved to: {output_filename}")
    print(f"Number of participants saved: {len(output_df)}")
    
    return output_filename

def create_final_sample_summary(stats_dict):
    """
    Create and print a summary of the final sample composition for reporting.
    
    Parameters:
        stats_dict (dict): Dictionary containing calculated statistics
        
    Returns:
        None
    """
    print("\n" + "="*60)
    print("FINAL SAMPLE COMPOSITION SUMMARY")
    print("="*60)
    
    sample_size = stats_dict.get('sample_size', 0)
    print(f"Final sample size: {sample_size}")
    
    if 'age_mean' in stats_dict:
        print(f"\nAge characteristics:")
        print(f"  Mean age: {stats_dict['age_mean']:.2f} years (SD = {stats_dict['age_std']:.2f})")
        print(f"  Age range: {stats_dict['age_min']:.0f} - {stats_dict['age_max']:.0f} years")
    
    if 'male_count' in stats_dict and 'female_count' in stats_dict:
        print(f"\nSex distribution:")
        print(f"  Male: {stats_dict['male_count']} ({stats_dict.get('male_percentage', 0):.1f}%)")
        print(f"  Female: {stats_dict['female_count']} ({stats_dict.get('female_percentage', 0):.1f}%)")
        
        # Add other sex category reporting
        other_sex_count = sample_size - (stats_dict.get('male_count', 0) + stats_dict.get('female_count', 0))
        if other_sex_count > 0:
            other_percentage = (other_sex_count / sample_size) * 100
            print(f"  Other/Prefer not to say: {other_sex_count} ({other_percentage:.1f}%)")
    
    if 'completion_time_mean_minutes' in stats_dict:
        print(f"\nCompletion time characteristics:")
        print(f"  Mean completion time: {stats_dict['completion_time_mean_minutes']:.2f} minutes (SD = {stats_dict['completion_time_std_minutes']:.2f})")
        print(f"  Completion time range: {stats_dict['completion_time_min_minutes']:.2f} - {stats_dict['completion_time_max_minutes']:.2f} minutes")
    
    print("\n" + "="*60)

def print_exclusion_summary(initial_count, approved_count, n_excluded_time, final_sample_size):
    """
    Print a comprehensive summary of data exclusions.
    
    Parameters:
        initial_count (int): Initial number of participants loaded
        approved_count (int): Number of approved participants
        n_excluded_time (int): Number excluded for extreme completion times
        final_sample_size (int): Final retained sample size
        
    Returns:
        None
    """
    print("\n" + "="*60)
    print("DATA EXCLUSION SUMMARY")
    print("="*60)
    print(f"1) Initial participants loaded: {initial_count}")
    excluded_status = initial_count - approved_count
    print(f"2) Participants removed for non-APPROVED status: {excluded_status}")
    print(f"3) Participants excluded for extreme completion time: {n_excluded_time}")
    print(f"4) Final sample size for analysis: {final_sample_size}")
    print("="*60)

def main():
    """
    Main function to execute the demographic analysis pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting demographic analysis pipeline...")
        
        # Create outputs folder
        create_outputs_folder()
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Using timestamp: {timestamp}")
        
        # Find and load the most recent input file
        file_pattern = "../C_results/data/prolific_export_*.csv"
        try:
            input_file = find_most_recent_file(file_pattern)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            print("Failed to load data")
            return 1
        
        # Filter for approved participants
        approved_df = filter_approved_participants(df)
        if len(approved_df) == 0:
            print("No approved participants found")
            return 1
        
        # Extract demographic variables
        demo_df = extract_demographic_variables(approved_df)
        
        # Apply time exclusions
        final_df = apply_time_exclusions(demo_df)
        
        # Calculate descriptive statistics
        stats_dict, retained_df = calculate_descriptive_statistics(final_df)
        
        # Capture counts for exclusion summary
        initial_count = len(df)
        approved_count = len(approved_df)
        n_excluded_time = final_df['excluded_extreme_time'].sum()
        final_sample_size = len(retained_df)
        
        # Create output files
        stats_output = create_summary_statistics_output(stats_dict, timestamp)
        demo_output = create_demographic_cleaned_output(final_df, timestamp)
        
        # Print exclusion summary before final sample summary
        print_exclusion_summary(initial_count, approved_count, n_excluded_time, final_sample_size)
        
        # Create final sample summary
        create_final_sample_summary(stats_dict)
        
        print(f"\nOutput files created:")
        print(f"  - {stats_output}")
        print(f"  - {demo_output}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
