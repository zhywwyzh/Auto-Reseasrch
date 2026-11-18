import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def read_input_files(file_pattern):
    """
    Read and combine all CSV files matching the specified pattern.
    
    Parameters:
    file_pattern (str): Glob pattern to match input files
    
    Returns:
    pd.DataFrame: Combined dataframe from all matching files
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    # Find all files matching the pattern
    files = glob.glob(file_pattern)
    print(f"Found {len(files)} files: {files}")
    
    if not files:
        print("No files found matching the pattern")
        return None

    # Find the most recent file
    if len(files) == 1:
        latest_file = files[0]
    else:
        # Get the most recent file based on modification time
        latest_file = max(files, key=os.path.getmtime)

    print(f"Processing most recent file: {latest_file}")

    # Read only the most recent file
    try:
        df = pd.read_csv(latest_file)
        print(f"File {latest_file} shape: {df.shape}")
        print(f"Columns in {latest_file}: {list(df.columns)}")
        print(f"First 3 rows of {latest_file}:")
        print(df.head(3))
        return df
    except Exception as e:
        print(f"Error reading {latest_file}: {e}")
        return None

def validate_required_columns(df, required_columns):
    """
    Validate that all required columns exist in the dataframe.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    required_columns (list): List of required column names
    
    Returns:
    bool: True if all required columns exist, False otherwise
    """
    print(f"Validating required columns: {required_columns}")
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return False
    
    print("All required columns found")
    return True

def filter_completed_participants(df):
    """
    Filter dataframe to include only completed participants with Status = "APPROVED".
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Filtered dataframe with only approved participants
    """
    print("Filtering for completed participants...")
    
    # Print unique values for Status column
    print(f"Unique Status values: {df['Status'].unique()}")
    
    initial_count = len(df)
    print(f"Initial participant count: {initial_count}")
    
    # Filter for APPROVED status
    approved_df = df[df['Status'] == 'APPROVED'].copy()
    approved_count = len(approved_df)
    print(f"Participants with APPROVED status: {approved_count}")
    print(f"Excluded participants (not APPROVED): {initial_count - approved_count}")
    
    # Remove participants with missing completion data
    completion_columns = ['Completed at', 'Started at']
    before_completion_filter = len(approved_df)
    
    for col in completion_columns:
        missing_before = approved_df[col].isna().sum()
        approved_df = approved_df.dropna(subset=[col])
        missing_after = before_completion_filter - len(approved_df)
        print(f"Participants with missing {col}: {missing_before}")
        print(f"Participants remaining after removing missing {col}: {len(approved_df)}")
        before_completion_filter = len(approved_df)
    
    final_count = len(approved_df)
    print(f"Final participant count after filtering: {final_count}")
    print(f"Total excluded participants: {initial_count - final_count}")
    
    return approved_df

def validate_data_quality(df):
    """
    Perform data quality validation checks.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Validated dataframe with quality issues addressed
    """
    print("Performing data quality validation...")
    
    # Check for duplicate participant IDs
    print(f"Total participants: {len(df)}")
    unique_participants = df['Participant id'].nunique()
    print(f"Unique participant IDs: {unique_participants}")
    
    if len(df) > unique_participants:
        duplicates = df[df.duplicated(subset=['Participant id'], keep=False)]
        print(f"Found {len(duplicates)} duplicate participant entries")
        print("Duplicate participant IDs:")
        print(duplicates[['Participant id']].drop_duplicates())
        
        # Keep first occurrence of each participant
        df = df.drop_duplicates(subset=['Participant id'], keep='first')
        print(f"After removing duplicates: {len(df)} participants")
    else:
        print("No duplicate participant IDs found")
    
    # Validate age range (18-35 as specified)
    print("Validating age range...")
    age_stats_before = df['Age'].describe()
    print(f"Age statistics before filtering:\n{age_stats_before}")
    
    # Print unique age values to check data type
    print(f"Age data type: {df['Age'].dtype}")
    
    # Filter for age range 18-35
    valid_age_df = df[(df['Age'] >= 18) & (df['Age'] <= 35)].copy()
    excluded_age = len(df) - len(valid_age_df)
    print(f"Participants excluded due to age outside 18-35 range: {excluded_age}")
    print(f"Participants remaining after age filtering: {len(valid_age_df)}")
    
    # Check for complete demographic data
    print("Checking for complete demographic data...")
    demographic_columns = ['Age', 'Sex']
    
    for col in demographic_columns:
        missing_count = valid_age_df[col].isna().sum()
        print(f"Missing {col} data: {missing_count}")
        if missing_count > 0:
            valid_age_df = valid_age_df.dropna(subset=[col])
            print(f"Participants remaining after removing missing {col}: {len(valid_age_df)}")
    
    print(f"Final sample size after all validation: {len(valid_age_df)}")
    
    return valid_age_df

def calculate_sample_demographics(df):
    """
    Calculate comprehensive sample demographics and statistics.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with validated participants
    
    Returns:
    list: List of dictionaries containing demographic statistics
    """
    print("Calculating sample demographics...")
    
    statistics = []
    
    # Total number of participants
    total_participants = len(df)
    print(f"Total participants: {total_participants}")
    
    statistics.append({
        'statistic_name': 'Total Participants',
        'statistic_value': str(total_participants),
        'sample_size': total_participants,
        'percentage': 100.0
    })
    
    # Age statistics
    print("Calculating age statistics...")
    age_mean = df['Age'].mean()
    age_std = df['Age'].std()
    age_min = df['Age'].min()
    age_max = df['Age'].max()
    
    print(f"Age - Mean: {age_mean:.2f}, Std: {age_std:.2f}, Min: {age_min}, Max: {age_max}")
    
    statistics.extend([
        {
            'statistic_name': 'Age Mean',
            'statistic_value': f"{age_mean:.2f}",
            'sample_size': total_participants,
            'percentage': None
        },
        {
            'statistic_name': 'Age Standard Deviation',
            'statistic_value': f"{age_std:.2f}",
            'sample_size': total_participants,
            'percentage': None
        },
        {
            'statistic_name': 'Age Minimum',
            'statistic_value': str(int(age_min)),
            'sample_size': total_participants,
            'percentage': None
        },
        {
            'statistic_name': 'Age Maximum',
            'statistic_value': str(int(age_max)),
            'sample_size': total_participants,
            'percentage': None
        }
    ])
    
    # Sex distribution
    print("Calculating sex distribution...")
    sex_counts = df['Sex'].value_counts()
    print(f"Sex distribution:\n{sex_counts}")
    print(f"Unique Sex values: {df['Sex'].unique()}")
    
    for sex_category, count in sex_counts.items():
        percentage = (count / total_participants) * 100
        print(f"{sex_category}: {count} ({percentage:.1f}%)")
        
        statistics.extend([
            {
                'statistic_name': f'Sex {sex_category} Count',
                'statistic_value': str(count),
                'sample_size': total_participants,
                'percentage': None
            },
            {
                'statistic_name': f'Sex {sex_category} Percentage',
                'statistic_value': f"{percentage:.1f}%",
                'sample_size': total_participants,
                'percentage': round(percentage, 1)
            }
        ])
    
    # Session duration statistics (convert from seconds to minutes)
    print("Calculating session duration statistics...")
    print(f"Time taken data type: {df['Time taken'].dtype}")
    
    # Convert time from seconds to minutes
    duration_minutes = df['Time taken'] / 60
    duration_mean = duration_minutes.mean()
    duration_std = duration_minutes.std()
    duration_min = duration_minutes.min()
    duration_max = duration_minutes.max()
    
    print(f"Session Duration (minutes) - Mean: {duration_mean:.2f}, Std: {duration_std:.2f}, Min: {duration_min:.2f}, Max: {duration_max:.2f}")
    
    statistics.extend([
        {
            'statistic_name': 'Session Duration Mean (minutes)',
            'statistic_value': f"{duration_mean:.2f}",
            'sample_size': total_participants,
            'percentage': None
        },
        {
            'statistic_name': 'Session Duration Standard Deviation (minutes)',
            'statistic_value': f"{duration_std:.2f}",
            'sample_size': total_participants,
            'percentage': None
        },
        {
            'statistic_name': 'Session Duration Minimum (minutes)',
            'statistic_value': f"{duration_min:.2f}",
            'sample_size': total_participants,
            'percentage': None
        },
        {
            'statistic_name': 'Session Duration Maximum (minutes)',
            'statistic_value': f"{duration_max:.2f}",
            'sample_size': total_participants,
            'percentage': None
        }
    ])
    
    return statistics

def save_results(statistics, output_dir='outputs'):
    """
    Save the calculated statistics to a CSV file.
    
    Parameters:
    statistics (list): List of dictionaries containing statistics
    output_dir (str): Output directory path
    
    Returns:
    str: Path to the saved output file
    """
    print(f"Saving results to {output_dir} directory...")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"sample_statistics_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    # Convert statistics to DataFrame
    results_df = pd.DataFrame(statistics)
    
    print(f"Results dataframe shape: {results_df.shape}")
    print(f"Results dataframe columns: {list(results_df.columns)}")
    print(f"First 2 rows of results:")
    print(results_df.head(2))
    
    # Save to CSV
    results_df.to_csv(output_path, index=False)
    print(f"Results saved to: {output_path}")
    
    return output_path

def main():
    """
    Main function to execute the sample statistics calculation workflow.
    
    Returns:
    int: 0 for successful completion, 1 for errors
    """
    try:
        print("Starting sample statistics calculation...")
        
        # Define required columns
        required_columns = [
            'Participant id', 'Age', 'Sex', 'Time taken', 
            'Status', 'Completed at', 'Started at'
        ]
        
        # Read input files
        input_pattern = "raw_data/prolific_export_*.csv"
        df = read_input_files(input_pattern)

        if df is None:
            print("ERROR: Could not read input files")
            return 1

        # Strip whitespace from column names before validation
        df.columns = df.columns.str.strip()

        # Validate required columns
        if not validate_required_columns(df, required_columns):
            print("ERROR: Missing required columns")
            return 1
        
        # Filter for completed participants
        filtered_df = filter_completed_participants(df)
        
        if len(filtered_df) == 0:
            print("ERROR: No approved participants found")
            return 1
        
        # Validate data quality
        validated_df = validate_data_quality(filtered_df)
        
        if len(validated_df) == 0:
            print("ERROR: No participants remaining after validation")
            return 1
        
        # Calculate sample demographics
        statistics = calculate_sample_demographics(validated_df)
        
        # Save results
        output_path = save_results(statistics)
        
        print(f"Sample statistics calculation completed successfully")
        print(f"Output saved to: {output_path}")
        print("Finished execution")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
