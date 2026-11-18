#!/usr/bin/env python3
"""
Prolific Data Analysis Script
Processes prolific export CSV files to generate sample statistics and demographic summaries.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match (e.g., '../C_results/data/prolific_export_*.csv')
    
    Returns:
    str or None: Path to the most recent file, or None if no files found
    """
    print(f"Searching for files matching pattern: {pattern}")
    files = glob.glob(pattern)
    print(f"Found {len(files)} files matching pattern")
    
    if not files:
        print("No files found matching the pattern")
        return None
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    print(f"Most recent file: {most_recent}")
    return most_recent

def load_and_validate_data(filepath):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    filepath (str): Path to the CSV file
    
    Returns:
    pandas.DataFrame or None: Loaded dataframe if successful, None if failed
    """
    print(f"Loading data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        df.columns = df.columns.str.strip()
        print(f"Successfully loaded data with shape: {df.shape}")
        
        # Print all columns
        print("All columns in the dataset:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}. {col}")
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Check for required columns
        required_columns = [
            'Participant id', 'Age', 'Sex', 'Time taken', 
            'Status', 'Started at', 'Completed at'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            print("Available columns that might match:")
            for col in df.columns:
                for req_col in missing_columns:
                    if req_col.lower() in col.lower() or col.lower() in req_col.lower():
                        print(f"  '{col}' might match '{req_col}'")
            return None
        
        print("All required columns found")
        return df
        
    except Exception as e:
        print(f"Error loading file {filepath}: {e}")
        return None

def filter_approved_participants(df):
    """
    Filter dataframe to include only approved participants.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    pandas.DataFrame: Filtered dataframe with only approved participants
    """
    print("Filtering to approved participants only...")
    
    # Print unique status values
    print("Unique Status values:")
    unique_statuses = df['Status'].unique()
    for status in unique_statuses:
        print(f"  {status}")
    
    initial_count = len(df)
    print(f"Initial participant count: {initial_count}")
    
    # Filter to approved only
    approved_df = df[df['Status'] == 'APPROVED'].copy()
    final_count = len(approved_df)
    excluded_count = initial_count - final_count
    
    print(f"Approved participants: {final_count}")
    print(f"Excluded participants: {excluded_count}")
    
    return approved_df

def validate_data_quality(df):
    """
    Perform data validation checks on the filtered dataset using cascaded filtering.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    pandas.DataFrame: Validated dataframe
    dict: Exclusion counts for each step
    """
    print("Performing data quality validation (cascaded filtering)...")

    exclusions = {}

    # Step 1: Age filter
    print("Validating age range (18-35)...")
    age_valid = (df['Age'] >= 18) & (df['Age'] <= 35)
    age_invalid_count = (~age_valid).sum()
    exclusions['age_excluded'] = int(age_invalid_count)
    if age_invalid_count > 0:
        print(f"Participants excluded for invalid age: {age_invalid_count}")
        print("Invalid age values:")
        invalid_ages = df.loc[~age_valid, 'Age'].unique()
        for age in invalid_ages:
            print(f"  {age}")
    df_age = df[age_valid].copy()

    # Step 2: Time taken filter
    print("Validating Time taken values (900-7200 seconds)...")
    time_valid = (df_age['Time taken'] >= 900) & (df_age['Time taken'] <= 7200)
    time_invalid_count = (~time_valid).sum()
    exclusions['time_excluded'] = int(time_invalid_count)
    if time_invalid_count > 0:
        print(f"Participants excluded for invalid time taken: {time_invalid_count}")
        print("Time taken statistics for invalid values:")
        invalid_times = df_age.loc[~time_valid, 'Time taken']
        print(f"  Min: {invalid_times.min()}")
        print(f"  Max: {invalid_times.max()}")
        print(f"  Mean: {invalid_times.mean():.2f}")
    df_time = df_age[time_valid].copy()

    # Step 3: Missing data filter
    print("Checking for missing values in critical variables...")
    critical_vars = ['Participant id', 'Age', 'Sex']
    n_before_missing = len(df_time)

    # Drop rows with any missing values in the critical columns
    df_final = df_time.dropna(subset=critical_vars).copy()

    exclusions['missing_excluded'] = n_before_missing - len(df_final)
    exclusions['missing_breakdown'] = df_time[critical_vars].isna().sum().to_dict()

    if exclusions['missing_excluded'] > 0:
        print(f"Participants excluded for missing critical data: {exclusions['missing_excluded']}")

    initial_count = len(df)
    after_age = len(df_age)
    after_time = len(df_time)
    after_missing = len(df_final)
    print(f"Initial count after approval filter: {initial_count}")
    print(f"Count after age filter: {after_age}")
    print(f"Count after time filter: {after_time}")
    print(f"Final count after missing data filter: {after_missing}")
    print(f"Total excluded in validation: {initial_count - after_missing}")

    exclusions['initial_approved'] = int(initial_count)
    exclusions['after_age'] = int(after_age)
    exclusions['after_time'] = int(after_time)
    exclusions['final_valid'] = int(after_missing)
    exclusions['total_excluded_validation'] = int(initial_count - after_missing)

    return df_final, exclusions

def calculate_session_duration(df):
    """
    Calculate session duration from start and completion times.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with datetime columns
    
    Returns:
    pandas.DataFrame: Dataframe with added session duration column
    """
    print("Calculating session duration...")
    
    df = df.copy()
    
    # Convert datetime columns
    print("Converting datetime columns...")
    df['started_at_dt'] = pd.to_datetime(df['Started at'])
    df['completed_at_dt'] = pd.to_datetime(df['Completed at'])
    
    # Calculate duration in minutes
    duration_seconds = (df['completed_at_dt'] - df['started_at_dt']).dt.total_seconds()
    df['session_duration_minutes'] = duration_seconds / 60
    
    print("Session duration statistics (minutes):")
    print(f"  Mean: {df['session_duration_minutes'].mean():.2f}")
    print(f"  SD: {df['session_duration_minutes'].std():.2f}")
    print(f"  Min: {df['session_duration_minutes'].min():.2f}")
    print(f"  Max: {df['session_duration_minutes'].max():.2f}")
    
    return df

def calculate_descriptive_statistics(df):
    """
    Calculate descriptive statistics for the final sample.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    dict: Dictionary containing all calculated statistics
    """
    print("Calculating descriptive statistics...")
    
    stats = {}
    
    # Total participant count
    unique_participants = df['Participant id'].nunique()
    stats['total_participants'] = unique_participants
    print(f"Total unique participants: {unique_participants}")
    
    # Age distribution
    print("Age distribution:")
    age_mean = df['Age'].mean()
    age_std = df['Age'].std()
    age_min = df['Age'].min()
    age_max = df['Age'].max()
    
    stats['age_mean'] = age_mean
    stats['age_std'] = age_std
    stats['age_min'] = age_min
    stats['age_max'] = age_max
    
    print(f"  Mean age: {age_mean:.2f}")
    print(f"  SD age: {age_std:.2f}")
    print(f"  Min age: {age_min}")
    print(f"  Max age: {age_max}")
    
    # Sex distribution
    print("Sex distribution:")
    sex_counts = df['Sex'].value_counts()
    sex_proportions = df['Sex'].value_counts(normalize=True)
    
    print("Unique Sex values:")
    for sex in df['Sex'].unique():
        print(f"  {sex}")
    
    for sex in sex_counts.index:
        count = sex_counts[sex]
        proportion = sex_proportions[sex]
        stats[f'sex_{sex}_count'] = count
        stats[f'sex_{sex}_proportion'] = proportion
        print(f"  {sex}: {count} ({proportion:.3f})")
    
    # Session duration statistics
    print("Session duration statistics:")
    duration_mean = df['session_duration_minutes'].mean()
    duration_std = df['session_duration_minutes'].std()
    duration_min = df['session_duration_minutes'].min()
    duration_max = df['session_duration_minutes'].max()
    
    stats['duration_mean'] = duration_mean
    stats['duration_std'] = duration_std
    stats['duration_min'] = duration_min
    stats['duration_max'] = duration_max
    
    print(f"  Mean duration: {duration_mean:.2f} minutes")
    print(f"  SD duration: {duration_std:.2f} minutes")
    print(f"  Min duration: {duration_min:.2f} minutes")
    print(f"  Max duration: {duration_max:.2f} minutes")
    
    return stats

def create_sample_statistics_output(stats, timestamp):
    """
    Create sample statistics output CSV.
    
    Parameters:
    stats (dict): Dictionary containing statistics
    timestamp (str): Timestamp string for filename
    
    Returns:
    str: Filepath of created file
    """
    print("Creating sample statistics output...")
    
    # Create output data
    output_data = []
    
    # Add all statistics with descriptions
    stat_descriptions = {
        'total_participants': 'Total number of unique participants',
        'age_mean': 'Mean age of participants',
        'age_std': 'Standard deviation of age',
        'age_min': 'Minimum age',
        'age_max': 'Maximum age',
        'duration_mean': 'Mean session duration in minutes',
        'duration_std': 'Standard deviation of session duration in minutes',
        'duration_min': 'Minimum session duration in minutes',
        'duration_max': 'Maximum session duration in minutes'
    }
    
    for metric, value in stats.items():
        if metric in stat_descriptions:
            output_data.append({
                'metric': metric,
                'value': float(value),
                'description': stat_descriptions[metric]
            })
        elif metric.startswith('sex_') and metric.endswith('_count'):
            sex_name = metric.replace('sex_', '').replace('_count', '')
            output_data.append({
                'metric': metric,
                'value': float(value),
                'description': f'Count of {sex_name} participants'
            })
        elif metric.startswith('sex_') and metric.endswith('_proportion'):
            sex_name = metric.replace('sex_', '').replace('_proportion', '')
            output_data.append({
                'metric': metric,
                'value': float(value),
                'description': f'Proportion of {sex_name} participants'
            })
    
    # Create dataframe and save
    output_df = pd.DataFrame(output_data)
    
    print("Sample statistics output:")
    print("All columns:")
    for col in output_df.columns:
        print(f"  {col}")
    print("First 2 rows:")
    print(output_df.head(2))
    
    filepath = f"outputs/sample_statistics_{timestamp}.csv"
    output_df.to_csv(filepath, index=False)
    print(f"Saved sample statistics to: {filepath}")
    
    return filepath

def create_demographic_summary_output(df, timestamp):
    """
    Create demographic summary output CSV.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    timestamp (str): Timestamp string for filename
    
    Returns:
    str: Filepath of created file
    """
    print("Creating demographic summary output...")
    
    # Select and rename columns
    output_df = df[[
        'Participant id', 'Age', 'Sex', 'session_duration_minutes', 
        'Time taken', 'Status'
    ]].copy()
    
    output_df.columns = [
        'participant_id', 'age', 'sex', 'session_duration_minutes',
        'time_taken_seconds', 'status'
    ]
    
    print("Demographic summary output:")
    print("All columns:")
    for col in output_df.columns:
        print(f"  {col}")
    print("First 2 rows:")
    print(output_df.head(2))
    
    filepath = f"outputs/demographic_summary_{timestamp}.csv"
    output_df.to_csv(filepath, index=False)
    print(f"Saved demographic summary to: {filepath}")
    
    return filepath

def create_session_data_output(df, timestamp):
    """
    Create prolific session data output CSV.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    timestamp (str): Timestamp string for filename
    
    Returns:
    str: Filepath of created file
    """
    print("Creating session data output...")
    
    # Select and rename columns
    output_df = df[[
        'Participant id', 'Started at', 'Completed at', 'session_duration_minutes'
    ]].copy()
    
    output_df.columns = [
        'participant_id', 'started_at', 'completed_at', 'session_duration_minutes'
    ]
    
    print("Session data output:")
    print("All columns:")
    for col in output_df.columns:
        print(f"  {col}")
    print("First 2 rows:")
    print(output_df.head(2))
    
    filepath = f"outputs/prolific_session_data_{timestamp}.csv"
    output_df.to_csv(filepath, index=False)
    print(f"Saved session data to: {filepath}")
    
    return filepath

def main():
    """
    Main function to execute the prolific data analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for failure
    """
    try:
        print("Starting Prolific Data Analysis Script")
        print("=" * 50)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Created/verified outputs directory")
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Using timestamp: {timestamp}")
        
        # Find input file
        input_pattern = "../C_results/data/prolific_export_*.csv"
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print("ERROR: No input files found matching the pattern")
            return 1
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            print("ERROR: Failed to load and validate data")
            return 1

        initial_participant_count = len(df)
        
        # Filter to approved participants
        approved_df = filter_approved_participants(df)
        if len(approved_df) == 0:
            print("ERROR: No approved participants found")
            return 1

        status_exclusions = initial_participant_count - len(approved_df)
        
        # Validate data quality (cascaded)
        validated_df, validation_exclusions = validate_data_quality(approved_df)
        if len(validated_df) == 0:
            print("ERROR: No participants passed validation criteria")
            return 1
        
        # Calculate session duration
        final_df = calculate_session_duration(validated_df)
        
        # Calculate descriptive statistics
        stats = calculate_descriptive_statistics(final_df)
        
        # Create output files
        print("\nCreating output files...")
        print("-" * 30)
        
        stats_file = create_sample_statistics_output(stats, timestamp)
        demo_file = create_demographic_summary_output(final_df, timestamp)
        session_file = create_session_data_output(final_df, timestamp)
        
        # Print analysis summary
        print("\nAnalysis Summary:")
        print("-" * 20)
        print(f"Input file processed: {input_file}")
        print(f"Final sample size: {len(final_df)} participants")
        print(f"Files created:")
        print(f"  - {stats_file}")
        print(f"  - {demo_file}")
        print(f"  - {session_file}")

        # Print final exclusion summary as per instructions
        print("\nExclusion Summary:")
        print("-" * 20)
        print(f"1) Initial participants loaded: {initial_participant_count}")
        print(f"2) Participants removed due to non-APPROVED status: {status_exclusions}")
        print(f"3) Participants removed for age outside 18-35: {validation_exclusions.get('age_excluded', 0)}")
        print(f"4) Participants removed for invalid time taken (<900s or >7200s): {validation_exclusions.get('time_excluded', 0)}")
        print(f"5) Participants removed due to missing critical data: {validation_exclusions.get('missing_excluded', 0)}")
        print(f"6) Final dataset: {len(final_df)} participants")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
