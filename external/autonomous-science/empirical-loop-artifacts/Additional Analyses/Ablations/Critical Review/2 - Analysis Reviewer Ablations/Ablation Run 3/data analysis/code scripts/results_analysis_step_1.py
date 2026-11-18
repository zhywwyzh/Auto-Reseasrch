import pandas as pd
import numpy as np
import glob
import os
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

def load_and_validate_data(file_path):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    file_path (str): Path to the CSV file
    
    Returns:
    pandas.DataFrame or None: Loaded dataframe if successful, None if failed
    """
    required_columns = ['Participant id', 'Age', 'Sex', 'Status', 'Started at', 'Completed at', 'Time taken']
    
    try:
        print(f"Loading data from: {file_path}")
        df = pd.read_csv(file_path)
        
        print(f"Data shape: {df.shape}")
        print("All columns in dataset:")
        print(list(df.columns))
        
        print("First 3 rows of data:")
        print(df.head(3))
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            return None
        
        print("All required columns found!")
        return df
        
    except Exception as e:
        print(f"Error loading file {file_path}: {str(e)}")
        return None

def filter_completed_participants(df):
    """
    Filter dataframe for completed participants only.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    pandas.DataFrame: Filtered dataframe with completed participants only
    """
    print("\nFiltering for completed participants...")
    
    initial_count = len(df)
    print(f"Initial participant count: {initial_count}")
    
    # Print unique values for Status column
    print("Unique values in Status column:")
    print(df['Status'].unique())
    
    # Filter for APPROVED status
    df_approved = df[df['Status'] == 'APPROVED'].copy()
    approved_count = len(df_approved)
    print(f"Participants with APPROVED status: {approved_count}")
    print(f"Excluded due to non-APPROVED status: {initial_count - approved_count}")
    
    # Filter for non-null Completed at values
    df_completed = df_approved[df_approved['Completed at'].notna()].copy()
    completed_count = len(df_completed)
    print(f"Participants with non-null Completed at: {completed_count}")
    print(f"Excluded due to null Completed at: {approved_count - completed_count}")
    
    print(f"Final completed participant count: {completed_count}")
    
    return df_completed

def validate_participant_data(df):
    """
    Validate participant data and flag any issues.
    
    Parameters:
    df (pandas.DataFrame): Filtered dataframe
    
    Returns:
    dict: Dictionary containing validation results and flags
    """
    print("\nValidating participant data...")
    
    validation_results = {
        'age_issues': [],
        'missing_demographic': [],
        'completion_time_issues': []
    }
    
    # Check age range (18-35)
    age_issues = df[(df['Age'] < 18) | (df['Age'] > 35)]
    if len(age_issues) > 0:
        print(f"Participants with age outside 18-35 range: {len(age_issues)}")
        validation_results['age_issues'] = age_issues['Participant id'].tolist()
    else:
        print("All participants have valid age range (18-35)")
    
    # Check for missing demographic data
    missing_age = df[df['Age'].isna()]
    missing_sex = df[df['Sex'].isna()]
    
    if len(missing_age) > 0:
        print(f"Participants with missing age data: {len(missing_age)}")
        validation_results['missing_demographic'].extend(missing_age['Participant id'].tolist())
    
    if len(missing_sex) > 0:
        print(f"Participants with missing sex data: {len(missing_sex)}")
        validation_results['missing_demographic'].extend(missing_sex['Participant id'].tolist())
    
    if len(missing_age) == 0 and len(missing_sex) == 0:
        print("No missing demographic data found")
    
    # Check completion times (convert to minutes)
    df['completion_time_minutes'] = df['Time taken'] / 60
    unusual_times = df[(df['completion_time_minutes'] < 10) | (df['completion_time_minutes'] > 120)]
    
    if len(unusual_times) > 0:
        print(f"Participants with unusual completion times (<10 min or >120 min): {len(unusual_times)}")
        validation_results['completion_time_issues'] = unusual_times['Participant id'].tolist()
    else:
        print("All participants have reasonable completion times (10-120 minutes)")
    
    return validation_results

def calculate_descriptive_statistics(df):
    """
    Calculate sample descriptive statistics.
    
    Parameters:
    df (pandas.DataFrame): Filtered dataframe
    
    Returns:
    pandas.DataFrame: Dataframe containing descriptive statistics
    """
    print("\nCalculating descriptive statistics...")
    
    statistics = []
    
    # Total participant count
    total_count = df['Participant id'].nunique()
    statistics.append({
        'statistic_name': 'total_participant_count',
        'statistic_value': total_count,
        'statistic_description': 'Count of unique participants'
    })
    print(f"Total participant count: {total_count}")
    
    # Age distribution
    mean_age = df['Age'].mean()
    std_age = df['Age'].std()
    min_age = df['Age'].min()
    max_age = df['Age'].max()
    
    statistics.extend([
        {
            'statistic_name': 'mean_age',
            'statistic_value': mean_age,
            'statistic_description': 'Mean age of participants'
        },
        {
            'statistic_name': 'std_age',
            'statistic_value': std_age,
            'statistic_description': 'Standard deviation of age'
        },
        {
            'statistic_name': 'min_age',
            'statistic_value': min_age,
            'statistic_description': 'Minimum age'
        },
        {
            'statistic_name': 'max_age',
            'statistic_value': max_age,
            'statistic_description': 'Maximum age'
        }
    ])
    
    print(f"Age statistics - Mean: {mean_age:.2f}, SD: {std_age:.2f}, Range: {min_age}-{max_age}")
    
    # Sex distribution
    sex_counts = df['Sex'].value_counts()
    sex_percentages = df['Sex'].value_counts(normalize=True) * 100
    
    print("Sex distribution:")
    for sex, count in sex_counts.items():
        percentage = sex_percentages[sex]
        print(f"  {sex}: {count} ({percentage:.1f}%)")
        
        statistics.extend([
            {
                'statistic_name': f'sex_count_{sex.lower()}',
                'statistic_value': count,
                'statistic_description': f'Count of {sex} participants'
            },
            {
                'statistic_name': f'sex_percentage_{sex.lower()}',
                'statistic_value': percentage,
                'statistic_description': f'Percentage of {sex} participants'
            }
        ])
    
    # Session completion time
    completion_time_minutes = df['Time taken'] / 60
    mean_completion = completion_time_minutes.mean()
    std_completion = completion_time_minutes.std()
    
    statistics.extend([
        {
            'statistic_name': 'mean_completion_time_minutes',
            'statistic_value': mean_completion,
            'statistic_description': 'Mean completion time in minutes'
        },
        {
            'statistic_name': 'std_completion_time_minutes',
            'statistic_value': std_completion,
            'statistic_description': 'Standard deviation of completion time in minutes'
        }
    ])
    
    print(f"Completion time - Mean: {mean_completion:.2f} minutes, SD: {std_completion:.2f} minutes")
    
    return pd.DataFrame(statistics)

def prepare_demographic_output(df):
    """
    Prepare demographic data for output.
    
    Parameters:
    df (pandas.DataFrame): Filtered dataframe
    
    Returns:
    pandas.DataFrame: Formatted demographic data
    """
    print("\nPreparing demographic output...")
    
    output_df = pd.DataFrame({
        'participant_id': df['Participant id'],
        'age': df['Age'],
        'sex': df['Sex'],
        'completion_time_minutes': df['Time taken'] / 60,
        'status': df['Status']
    })
    
    print("Demographic output columns:")
    print(list(output_df.columns))
    print("First 2 rows of demographic output:")
    print(output_df.head(2))
    
    return output_df

def main():
    """
    Main function to execute the data processing pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting Prolific data processing...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Created/verified outputs directory")
        
        # Find input file
        input_pattern = "../C_results/data/prolific_export_*.csv"
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            print("Failed to load or validate input data")
            return 1
        
        # Filter for completed participants
        df_filtered = filter_completed_participants(df)
        
        if len(df_filtered) == 0:
            print("No completed participants found after filtering")
            return 1
        
        # Validate participant data
        validation_results = validate_participant_data(df_filtered)
        
        # Calculate descriptive statistics
        stats_df = calculate_descriptive_statistics(df_filtered)
        
        # Prepare demographic output
        demo_df = prepare_demographic_output(df_filtered)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save statistics output
        stats_filename = f"outputs/sample_statistics_{timestamp}.csv"
        stats_df.to_csv(stats_filename, index=False)
        print(f"Saved statistics to: {stats_filename}")
        
        # Save demographic output
        demo_filename = f"outputs/prolific_demographic_data_{timestamp}.csv"
        demo_df.to_csv(demo_filename, index=False)
        print(f"Saved demographic data to: {demo_filename}")
        
        print("Data processing completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)