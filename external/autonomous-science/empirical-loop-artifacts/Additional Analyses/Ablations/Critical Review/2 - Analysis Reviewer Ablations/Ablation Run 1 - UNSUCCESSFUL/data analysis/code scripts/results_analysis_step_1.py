#!/usr/bin/env python3
"""
Script to analyze participant demographics and session statistics from Prolific export data.
Filters for completed participants and calculates comprehensive demographic and duration statistics.
"""

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
    pattern (str): File pattern to match (e.g., '../C_results/data/prolific_export_*.csv')
    
    Returns:
    str: Path to the most recent file matching the pattern
    None: If no files found
    """
    files = glob.glob(pattern)
    if not files:
        print(f"No files found matching pattern: {pattern}")
        return None
    
    # Get the most recent file by modification time
    most_recent = max(files, key=os.path.getmtime)
    print(f"Found {len(files)} files matching pattern. Using most recent: {most_recent}")
    return most_recent


def load_and_validate_data(file_path):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    file_path (str): Path to the CSV file
    
    Returns:
    pd.DataFrame: Loaded dataframe if successful
    None: If file cannot be loaded or required columns missing
    """
    required_columns = ['Participant id', 'Status', 'Started at', 'Completed at', 'Time taken', 'Age', 'Sex']
    
    try:
        print(f"Loading data from: {file_path}")
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()  # Strip whitespace from column names
        print(f"Data loaded successfully. Shape: {df.shape}")
        
        # Print all columns
        print(f"All columns in dataset: {list(df.columns)}")
        
        # Print first 3 rows to show data structure
        print("First 3 rows of data:")
        print(df.head(3))
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            return None
        
        print(f"All required columns present: {required_columns}")
        return df
        
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None


def filter_completed_participants(df):
    """
    Filter dataframe to include only completed participants meeting inclusion criteria.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with participant data
    
    Returns:
    pd.DataFrame: Filtered dataframe with completed participants
    """
    print("\n=== FILTERING PARTICIPANTS ===")
    print(f"Initial dataset size: {len(df)} participants")
    
    # Print unique values for key experimental design columns
    print(f"Unique Status values: {df['Status'].unique()}")
    print(f"Unique Sex values: {df['Sex'].unique()}")
    
    # Track exclusions
    exclusions = {}
    
    # Filter 1: Status = "APPROVED"
    initial_count = len(df)
    df_filtered = df[df['Status'] == 'APPROVED'].copy()
    exclusions['Non-APPROVED status'] = initial_count - len(df_filtered)
    print(f"After Status='APPROVED' filter: {len(df_filtered)} participants (excluded {exclusions['Non-APPROVED status']})")
    
    # Filter 2: Non-null "Completed at" values
    before_count = len(df_filtered)
    df_filtered = df_filtered[df_filtered['Completed at'].notna()].copy()
    exclusions['Missing completion time'] = before_count - len(df_filtered)
    print(f"After non-null 'Completed at' filter: {len(df_filtered)} participants (excluded {exclusions['Missing completion time']})")
    
    # Filter 3: Non-missing Age
    before_count = len(df_filtered)
    df_filtered = df_filtered[df_filtered['Age'].notna()].copy()
    exclusions['Missing Age'] = before_count - len(df_filtered)
    print(f"After non-missing Age filter: {len(df_filtered)} participants (excluded {exclusions['Missing Age']})")
    
    # Filter 4: Non-missing Sex
    before_count = len(df_filtered)
    df_filtered = df_filtered[df_filtered['Sex'].notna()].copy()
    exclusions['Missing Sex'] = before_count - len(df_filtered)
    print(f"After non-missing Sex filter: {len(df_filtered)} participants (excluded {exclusions['Missing Sex']})")
    
    print(f"\nFinal sample size: {len(df_filtered)} participants")
    print("Exclusion summary:")
    for reason, count in exclusions.items():
        print(f"  - {reason}: {count} participants")
    
    # Print filtered data structure
    print("\nFiltered dataset columns:")
    print(list(df_filtered.columns))
    print("\nFirst 2 rows of filtered data:")
    print(df_filtered.head(2))
    
    return df_filtered


def calculate_age_statistics(df):
    """
    Calculate comprehensive age statistics.
    
    Parameters:
    df (pd.DataFrame): Filtered dataframe with participant data
    
    Returns:
    dict: Dictionary containing age statistics
    """
    print("\n=== CALCULATING AGE STATISTICS ===")
    
    ages = df['Age'].astype(float)
    
    age_stats = {
        'sample_size': len(df),
        'mean_age': np.mean(ages),
        'std_age': np.std(ages, ddof=1),
        'min_age': np.min(ages),
        'max_age': np.max(ages),
        'age_range': np.max(ages) - np.min(ages)
    }
    
    print(f"Age statistics calculated:")
    for stat, value in age_stats.items():
        print(f"  - {stat}: {value}")
    
    return age_stats


def calculate_sex_distribution(df):
    """
    Calculate sex distribution with counts and percentages.
    
    Parameters:
    df (pd.DataFrame): Filtered dataframe with participant data
    
    Returns:
    dict: Dictionary containing sex distribution statistics
    """
    print("\n=== CALCULATING SEX DISTRIBUTION ===")
    
    sex_counts = df['Sex'].value_counts()
    total_participants = len(df)
    
    sex_stats = {}
    
    print("Sex distribution:")
    for sex, count in sex_counts.items():
        percentage = (count / total_participants) * 100
        # Sanitize the sex category name to be used as a key
        sanitized_sex = sex.lower().replace(' ', '_')
        sex_stats[f'count_{sanitized_sex}'] = count
        sex_stats[f'percent_{sanitized_sex}'] = round(percentage, 1)
        print(f"  - {sex}: {count} ({percentage:.1f}%)")
    
    return sex_stats


def calculate_session_duration_statistics(df):
    """
    Calculate session duration statistics in minutes.
    
    Parameters:
    df (pd.DataFrame): Filtered dataframe with participant data
    
    Returns:
    dict: Dictionary containing session duration statistics
    """
    print("\n=== CALCULATING SESSION DURATION STATISTICS ===")
    
    # Convert seconds to minutes
    duration_seconds = df['Time taken'].astype(float)
    duration_minutes = duration_seconds / 60.0
    
    duration_stats = {
        'mean_duration_minutes': np.mean(duration_minutes),
        'std_duration_minutes': np.std(duration_minutes, ddof=1),
        'median_duration_minutes': np.median(duration_minutes)
    }
    
    print(f"Session duration statistics (in minutes):")
    for stat, value in duration_stats.items():
        print(f"  - {stat}: {value}")
    
    return duration_stats


def create_output_dataframe(age_stats, sex_stats, duration_stats):
    """
    Create output dataframe with all statistics in required format.
    
    Parameters:
    age_stats (dict): Age statistics
    sex_stats (dict): Sex distribution statistics
    duration_stats (dict): Session duration statistics
    
    Returns:
    pd.DataFrame: Output dataframe with metric_name, value, and unit columns
    """
    print("\n=== CREATING OUTPUT DATAFRAME ===")
    
    output_data = []
    
    # Add sample size
    output_data.append({
        'metric_name': 'sample_size',
        'value': age_stats['sample_size'],
        'unit': 'count'
    })
    
    # Add age statistics
    output_data.append({
        'metric_name': 'mean_age',
        'value': age_stats['mean_age'],
        'unit': 'years'
    })
    
    output_data.append({
        'metric_name': 'std_age',
        'value': age_stats['std_age'],
        'unit': 'years'
    })
    
    output_data.append({
        'metric_name': 'min_age',
        'value': age_stats['min_age'],
        'unit': 'years'
    })
    
    output_data.append({
        'metric_name': 'max_age',
        'value': age_stats['max_age'],
        'unit': 'years'
    })
    
    output_data.append({
        'metric_name': 'age_range',
        'value': age_stats['age_range'],
        'unit': 'years'
    })
    
    # Add sex distribution statistics
    for metric, value in sex_stats.items():
        if 'count_' in metric:
            unit = 'count'
        elif 'percent_' in metric:
            unit = 'percent'
        else:
            unit = 'unknown'
        
        output_data.append({
            'metric_name': metric,
            'value': value,
            'unit': unit
        })
    
    # Add session duration statistics
    output_data.append({
        'metric_name': 'mean_duration',
        'value': duration_stats['mean_duration_minutes'],
        'unit': 'minutes'
    })
    
    output_data.append({
        'metric_name': 'std_duration',
        'value': duration_stats['std_duration_minutes'],
        'unit': 'minutes'
    })
    
    output_data.append({
        'metric_name': 'median_duration',
        'value': duration_stats['median_duration_minutes'],
        'unit': 'minutes'
    })
    
    output_df = pd.DataFrame(output_data)
    
    print("Output dataframe created:")
    print("All columns:", list(output_df.columns))
    print("First 2 rows:")
    print(output_df.head(2))
    print(f"Total rows: {len(output_df)}")
    
    return output_df


def save_output_file(output_df, output_dir='outputs'):
    """
    Save output dataframe to CSV file with timestamp.
    
    Parameters:
    output_df (pd.DataFrame): Output dataframe to save
    output_dir (str): Output directory path
    
    Returns:
    str: Path to saved file
    """
    print(f"\n=== SAVING OUTPUT FILE ===")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"sample_statistics_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save to CSV
    output_df.to_csv(output_path, index=False)
    print(f"Output saved to: {output_path}")
    
    # Verify file was saved correctly
    if os.path.exists(output_path):
        print(f"File successfully saved. Size: {os.path.getsize(output_path)} bytes")
    else:
        print("ERROR: File was not saved successfully")
    
    return output_path


def main():
    """
    Main function to execute the complete analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting participant demographics and session statistics analysis...")
        
        # Step 1: Find and load input file
        input_pattern = "../C_results/data/prolific_export_*.csv"
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print("ERROR: No input files found")
            return 1
        
        # Step 2: Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            print("ERROR: Failed to load or validate input data")
            return 1
        
        # Step 3: Filter for completed participants
        df_filtered = filter_completed_participants(df)
        if len(df_filtered) == 0:
            print("ERROR: No participants meet inclusion criteria")
            return 1
        
        # Step 4: Calculate age statistics
        age_stats = calculate_age_statistics(df_filtered)
        
        # Step 5: Calculate sex distribution
        sex_stats = calculate_sex_distribution(df_filtered)
        
        # Step 6: Calculate session duration statistics
        duration_stats = calculate_session_duration_statistics(df_filtered)
        
        # Step 7: Create output dataframe
        output_df = create_output_dataframe(age_stats, sex_stats, duration_stats)
        
        # Step 8: Save output file
        output_path = save_output_file(output_df)
        
        print(f"\nAnalysis completed successfully!")
        print(f"Final sample size: {age_stats['sample_size']} participants")
        print(f"Output saved to: {output_path}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
