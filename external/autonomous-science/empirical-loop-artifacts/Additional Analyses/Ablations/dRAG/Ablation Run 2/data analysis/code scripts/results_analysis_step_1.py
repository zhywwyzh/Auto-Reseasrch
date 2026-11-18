#!/usr/bin/env python3
"""
Script to analyze participant data from Prolific export CSV files.
Calculates sample characteristics including demographics and session duration statistics.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def create_outputs_directory():
    """
    Create outputs directory if it doesn't exist.
    
    Returns:
        None
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created 'outputs' directory")
    else:
        print("'outputs' directory already exists")

def find_input_files(pattern):
    """
    Find input files matching the specified pattern.
    
    Parameters:
        pattern (str): File pattern to match
        
    Returns:
        list: List of matching file paths
    """
    print(f"Searching for files matching pattern: {pattern}")
    files = glob.glob(pattern)
    print(f"Found {len(files)} matching files: {files}")
    return files

def load_and_combine_data(file_paths):
    """
    Load and combine data from multiple CSV files.
    
    Parameters:
        file_paths (list): List of file paths to load
        
    Returns:
        pd.DataFrame: Combined dataframe from all files
    """
    all_data = []
    
    for file_path in file_paths:
        print(f"\nLoading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            df.columns = df.columns.str.strip()
            print(f"Successfully loaded {file_path} with shape: {df.shape}")
            print(f"Columns in {file_path}: {list(df.columns)}")
            print(f"First 3 rows of {file_path}:")
            print(df.head(3))
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if not all_data:
        print("No valid data files found!")
        return pd.DataFrame()
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined data shape: {combined_df.shape}")
    print(f"Combined data columns: {list(combined_df.columns)}")
    print("First 2 rows of combined data:")
    print(combined_df.head(2))
    
    return combined_df

def validate_required_columns(df, required_columns):
    """
    Validate that required columns exist in the dataframe.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        required_columns (list): List of required column names
        
    Returns:
        bool: True if all required columns exist, False otherwise
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    print("All required columns found in data")
    return True

def print_unique_values(df, categorical_columns):
    """
    Print unique values for categorical columns.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        categorical_columns (list): List of categorical column names
        
    Returns:
        None
    """
    print("\n=== UNIQUE VALUES FOR KEY COLUMNS ===")
    for col in categorical_columns:
        if col in df.columns:
            unique_vals = df[col].unique()
            print(f"{col} unique values: {unique_vals}")
            print(f"{col} value counts:")
            print(df[col].value_counts())
            print()

def filter_approved_participants(df):
    """
    Filter data to include only approved participants.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Filtered dataframe with only approved participants
    """
    print(f"\nInitial data shape: {df.shape}")
    print(f"Status value counts before filtering:")
    print(df['Status'].value_counts())
    
    # Filter for approved participants
    filtered_df = df[df['Status'] == 'APPROVED'].copy()
    
    print(f"Data shape after filtering for APPROVED status: {filtered_df.shape}")
    print(f"Number of participants excluded: {len(df) - len(filtered_df)}")
    
    return filtered_df

def calculate_session_duration(df):
    """
    Calculate session duration from start and completion timestamps.
    
    Parameters:
        df (pd.DataFrame): Input dataframe with timestamp columns
        
    Returns:
        pd.DataFrame: Dataframe with added session_duration_minutes column
    """
    print("\nCalculating session duration...")
    
    # Convert timestamp columns to datetime
    df['Started at'] = pd.to_datetime(df['Started at'], errors='coerce')
    df['Completed at'] = pd.to_datetime(df['Completed at'], errors='coerce')
    
    # Calculate session duration in minutes
    df['session_duration_minutes'] = (df['Completed at'] - df['Started at']).dt.total_seconds() / 60
    
    print(f"Session duration calculated for {df['session_duration_minutes'].notna().sum()} participants")
    print(f"Session duration missing for {df['session_duration_minutes'].isna().sum()} participants")
    
    return df

def convert_time_taken_to_minutes(df):
    """
    Convert time taken from seconds to minutes.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Dataframe with time_taken_minutes column
    """
    print("\nConverting time taken from seconds to minutes...")
    
    # Convert time taken to minutes
    df['time_taken_minutes'] = df['Time taken'] / 60
    
    print(f"Time taken converted to minutes for {df['time_taken_minutes'].notna().sum()} participants")
    
    return df

def calculate_sample_characteristics(df):
    """
    Calculate comprehensive sample characteristics.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        dict: Dictionary containing sample statistics
    """
    print("\nCalculating sample characteristics...")
    
    stats = {}
    
    # Final sample size
    stats['sample_size'] = len(df['Participant id'].unique())
    print(f"Final sample size: {stats['sample_size']}")
    
    # Age statistics
    age_data = df['Age'].dropna()
    stats['age_mean'] = age_data.mean()
    stats['age_std'] = age_data.std()
    stats['age_min'] = age_data.min()
    stats['age_max'] = age_data.max()
    
    print(f"Age statistics: Mean={stats['age_mean']:.2f}, SD={stats['age_std']:.2f}, Range={stats['age_min']}-{stats['age_max']}")
    
    # Sex distribution
    sex_counts = df['Sex'].value_counts()
    sex_percentages = df['Sex'].value_counts(normalize=True) * 100
    
    stats['sex_distribution'] = {}
    for sex, count in sex_counts.items():
        percentage = sex_percentages[sex]
        stats['sex_distribution'][sex] = {'count': count, 'percentage': percentage}
        print(f"Sex - {sex}: {count} ({percentage:.2f}%)")
    
    # Session duration statistics (using session_duration_minutes from timestamp difference)
    duration_data = df['session_duration_minutes'].dropna()
    stats['duration_mean'] = duration_data.mean()
    stats['duration_std'] = duration_data.std()
    stats['duration_min'] = duration_data.min()
    stats['duration_max'] = duration_data.max()
    
    print(f"Session duration statistics (from timestamps): Mean={stats['duration_mean']:.2f} min, SD={stats['duration_std']:.2f} min, Range={stats['duration_min']:.2f}-{stats['duration_max']:.2f} min")
    
    return stats

def create_summary_statistics_output(stats):
    """
    Create summary statistics output in required format.
    
    Parameters:
        stats (dict): Dictionary containing sample statistics
        
    Returns:
        pd.DataFrame: Summary statistics dataframe
    """
    print("\nCreating summary statistics output...")
    
    output_data = []
    
    # Sample size
    output_data.append({
        'metric': 'sample_size',
        'value': str(stats['sample_size']),
        'description': 'Total number of unique participants after filtering'
    })
    
    # Age statistics
    age_summary = f"{stats['age_mean']:.2f} ± {stats['age_std']:.2f}"
    age_range = f"{stats['age_min']}-{stats['age_max']}"
    
    output_data.append({
        'metric': 'age_mean_sd',
        'value': age_summary,
        'description': 'Age mean ± standard deviation'
    })
    
    output_data.append({
        'metric': 'age_range',
        'value': age_range,
        'description': 'Age range (minimum-maximum)'
    })
    
    # Sex distribution
    for sex, data in stats['sex_distribution'].items():
        metric_name = f"sex_{sex.lower().replace(' ', '_')}"
        output_data.append({
            'metric': metric_name,
            'value': f"{data['count']} ({data['percentage']:.2f}%)",
            'description': f'Number and percentage of {sex} participants'
        })
    
    # Session duration statistics
    duration_summary = f"{stats['duration_mean']:.2f} ± {stats['duration_std']:.2f}"
    duration_range = f"{stats['duration_min']:.2f}-{stats['duration_max']:.2f}"
    
    output_data.append({
        'metric': 'duration_mean_sd',
        'value': duration_summary,
        'description': 'Session duration mean ± standard deviation (minutes)'
    })
    
    output_data.append({
        'metric': 'duration_range',
        'value': duration_range,
        'description': 'Session duration range (minimum-maximum) in minutes'
    })
    
    output_df = pd.DataFrame(output_data)
    
    print("Summary statistics created:")
    print(output_df)
    
    return output_df

def save_output(df, filename):
    """
    Save output dataframe to CSV file.
    
    Parameters:
        df (pd.DataFrame): Dataframe to save
        filename (str): Output filename
        
    Returns:
        None
    """
    filepath = os.path.join('outputs', filename)
    df.to_csv(filepath, index=False)
    print(f"Output saved to: {filepath}")

def main():
    """
    Main function to execute the analysis pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting sample statistics analysis...")
        
        # Create outputs directory
        create_outputs_directory()
        
        # Define required columns
        required_columns = [
            'Participant id',
            'Status', 
            'Time taken',
            'Age',
            'Sex',
            'Started at',
            'Completed at'
        ]
        
        # Find input files
        input_pattern = '../C_results/data/prolific_export_*.csv'
        input_files = find_input_files(input_pattern)
        
        if not input_files:
            print(f"No input files found matching pattern: {input_pattern}")
            return 1
        
        # Load and combine data
        df = load_and_combine_data(input_files)

        if df.empty:
            print("No data loaded successfully")
            return 1

        # Track initial participant count
        initial_participant_count = len(df['Participant id'].unique())

        # Validate required columns
        if not validate_required_columns(df, required_columns):
            print("Required columns missing from data")
            return 1

        # Print unique values for key categorical columns
        categorical_columns = ['Status', 'Sex']
        print_unique_values(df, categorical_columns)

        # Print data types for measured variables
        print("\n=== DATA TYPES FOR MEASURED VARIABLES ===")
        measured_columns = ['Time taken', 'Age', 'Participant id']
        for col in measured_columns:
            if col in df.columns:
                print(f"{col} data type: {df[col].dtype}")

        # Filter for approved participants
        df_filtered = filter_approved_participants(df)

        if df_filtered.empty:
            print("No approved participants found")
            return 1

        # Calculate session duration
        df_filtered = calculate_session_duration(df_filtered)

        # Convert time taken to minutes
        df_filtered = convert_time_taken_to_minutes(df_filtered)

        print("\nFiltered data columns:")
        print(list(df_filtered.columns))
        print("First 2 rows of filtered data:")
        print(df_filtered.head(2))

        # Calculate sample characteristics
        stats = calculate_sample_characteristics(df_filtered)

        # Create summary statistics output
        summary_df = create_summary_statistics_output(stats)

        # Generate timestamp for output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'sample_statistics_{timestamp}.csv'

        # Save output
        save_output(summary_df, output_filename)

        # Track final participant count after all processing
        final_participant_count = len(df_filtered['Participant id'].unique())

        print("\n=== FINAL DATA CLEANING SUMMARY ===")
        print(f"Initial participants found: {initial_participant_count}")
        print(f"Participants excluded (non-APPROVED status): {initial_participant_count - final_participant_count}")
        print(f"Final participants included: {final_participant_count}")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
