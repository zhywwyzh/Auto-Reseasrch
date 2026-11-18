#!/usr/bin/env python3
"""
Script to analyze participant demographics and session characteristics from Prolific export data.
Filters for approved participants and generates descriptive statistics.
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
        return None
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def load_and_validate_data(file_path):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    file_path (str): Path to the CSV file to load
    
    Returns:
    pandas.DataFrame: Loaded dataframe if successful
    None: If file cannot be loaded or required columns missing
    """
    required_columns = ['Participant id', 'Age', 'Sex', 'Time taken', 'Status']
    
    try:
        print(f"Loading data from: {file_path}")
        df = pd.read_csv(file_path)
        
        # Strip whitespace from column names to handle formatting inconsistencies
        df.columns = [col.strip() for col in df.columns]
        
        print(f"Data loaded successfully. Shape: {df.shape}")
        print(f"All columns in dataset: {list(df.columns)}")
        print("First three rows of data:")
        print(df.head(3))
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return None
        
        print(f"All required columns present: {required_columns}")
        return df
        
    except Exception as e:
        print(f"ERROR: Failed to load data from {file_path}: {str(e)}")
        return None

def print_unique_values(df):
    """
    Print unique values for key experimental design parameters.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    """
    print("\n=== UNIQUE VALUES FOR KEY COLUMNS ===")
    
    # Status column - experimental design parameter
    print(f"Status unique values: {sorted(df['Status'].unique().tolist())}")
    
    # Sex column - experimental design parameter  
    print(f"Sex unique values: {sorted(df['Sex'].unique().tolist())}")
    
    # For measured variables, just print data type
    print(f"Age column data type: {df['Age'].dtype}")
    print(f"Time taken column data type: {df['Time taken'].dtype}")
    print(f"Participant id column data type: {df['Participant id'].dtype}")

def validate_data_quality(df):
    """
    Validate data quality and check for issues.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    dict: Dictionary containing validation results and statistics
    """
    print("\n=== DATA QUALITY VALIDATION ===")
    validation_results = {}
    
    # Check for duplicate participant IDs
    duplicate_ids = df['Participant id'].duplicated().sum()
    validation_results['duplicate_participants'] = duplicate_ids
    print(f"Duplicate Participant IDs found: {duplicate_ids}")
    
    if duplicate_ids > 0:
        print("Duplicate participant IDs:")
        duplicates = df[df['Participant id'].duplicated(keep=False)]['Participant id'].unique()
        print(duplicates)
    
    # Check missing values in key variables
    key_columns = ['Participant id', 'Age', 'Sex', 'Time taken', 'Status']
    missing_counts = {}
    
    for col in key_columns:
        missing_count = df[col].isnull().sum()
        missing_counts[col] = missing_count
        print(f"Missing values in {col}: {missing_count}")
    
    validation_results['missing_values'] = missing_counts
    
    # Check age range (18-35 as per inclusion criteria)
    age_out_of_range = df[(df['Age'] < 18) | (df['Age'] > 35)].shape[0]
    validation_results['age_out_of_range'] = age_out_of_range
    print(f"Participants with age outside 18-35 range: {age_out_of_range}")
    
    if age_out_of_range > 0:
        print("Ages outside range:")
        out_of_range_ages = df[(df['Age'] < 18) | (df['Age'] > 35)]['Age'].unique()
        print(sorted(out_of_range_ages))
    
    return validation_results

def filter_approved_participants(df):
    """
    Filter dataframe to include only participants with Status = "APPROVED".
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    pandas.DataFrame: Filtered dataframe containing only approved participants
    """
    print("\n=== FILTERING FOR APPROVED PARTICIPANTS ===")
    
    initial_count = len(df)
    print(f"Initial participant count: {initial_count}")
    
    # Filter for approved status
    approved_df = df[df['Status'] == 'APPROVED'].copy()
    
    final_count = len(approved_df)
    excluded_count = initial_count - final_count
    
    print(f"Participants with APPROVED status: {final_count}")
    print(f"Participants excluded (non-APPROVED): {excluded_count}")
    
    print("First two rows of filtered data:")
    print(approved_df.head(2))
    print(f"Columns in filtered data: {list(approved_df.columns)}")
    
    return approved_df

def calculate_descriptive_statistics(df):
    """
    Calculate descriptive statistics for the approved participant sample.
    
    Parameters:
    df (pandas.DataFrame): Filtered dataframe with approved participants
    
    Returns:
    list: List of dictionaries containing statistics for output
    """
    print("\n=== CALCULATING DESCRIPTIVE STATISTICS ===")
    
    statistics = []
    
    # Total number of participants (unique participant IDs)
    unique_participants = df['Participant id'].nunique()
    statistics.append({
        'statistic': 'total_participants',
        'value': unique_participants,
        'category': None
    })
    print(f"Total unique participants: {unique_participants}")
    
    # Age distribution statistics
    age_mean = df['Age'].mean()
    age_std = df['Age'].std()
    age_min = df['Age'].min()
    age_max = df['Age'].max()
    
    statistics.extend([
        {'statistic': 'age_mean', 'value': age_mean, 'category': None},
        {'statistic': 'age_std', 'value': age_std, 'category': None},
        {'statistic': 'age_min', 'value': age_min, 'category': None},
        {'statistic': 'age_max', 'value': age_max, 'category': None}
    ])
    
    print(f"Age statistics - Mean: {age_mean:.2f}, SD: {age_std:.2f}, Min: {age_min}, Max: {age_max}")
    
    # Sex distribution
    sex_counts = df['Sex'].value_counts()
    total_participants = len(df)
    
    print(f"Sex distribution:")
    for sex_category in sex_counts.index:
        count = sex_counts[sex_category]
        percentage = (count / total_participants) * 100
        
        statistics.extend([
            {'statistic': 'sex_count', 'value': count, 'category': sex_category},
            {'statistic': 'sex_percentage', 'value': percentage, 'category': sex_category}
        ])
        
        print(f"  {sex_category}: {count} ({percentage:.1f}%)")
    
    # Session duration (convert from seconds to minutes)
    time_minutes = df['Time taken'] / 60  # Convert seconds to minutes
    session_mean = time_minutes.mean()
    session_std = time_minutes.std()
    
    statistics.extend([
        {'statistic': 'session_duration_mean_minutes', 'value': session_mean, 'category': None},
        {'statistic': 'session_duration_std_minutes', 'value': session_std, 'category': None}
    ])
    
    print(f"Session duration - Mean: {session_mean:.2f} minutes, SD: {session_std:.2f} minutes")
    
    return statistics

def create_output_dataframe(statistics):
    """
    Create output dataframe from statistics list.
    
    Parameters:
    statistics (list): List of dictionaries containing statistics
    
    Returns:
    pandas.DataFrame: Formatted dataframe for output
    """
    print("\n=== CREATING OUTPUT DATAFRAME ===")
    
    output_df = pd.DataFrame(statistics)
    
    print("Output dataframe structure:")
    print(f"Columns: {list(output_df.columns)}")
    print("First two rows:")
    print(output_df.head(2))
    print(f"Total rows: {len(output_df)}")
    
    return output_df

def save_output_file(df, base_filename):
    """
    Save dataframe to CSV file with timestamp.
    
    Parameters:
    df (pandas.DataFrame): Dataframe to save
    base_filename (str): Base filename without extension
    
    Returns:
    str: Path to saved file
    """
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create filename with timestamp
    filename = f"outputs/{base_filename}_{timestamp}.csv"
    
    print(f"\nSaving output to: {filename}")
    
    # Save to CSV
    df.to_csv(filename, index=False)
    
    print(f"Output file saved successfully: {filename}")
    print(f"File contains {len(df)} rows and {len(df.columns)} columns")
    
    return filename

def main():
    """
    Main function to execute the participant statistics analysis.
    
    Returns:
    int: 0 for successful completion, 1 for errors
    """
    try:
        print("=== STARTING PARTICIPANT STATISTICS ANALYSIS ===")
        
        # Find input file
        input_pattern = '../C_results/data/prolific_export_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            print("ERROR: Failed to load or validate input data")
            return 1
        
        # Print unique values for key columns
        print_unique_values(df)
        
        # Validate data quality
        validation_results = validate_data_quality(df)
        
        # Filter for approved participants
        approved_df = filter_approved_participants(df)
        
        if len(approved_df) == 0:
            print("ERROR: No approved participants found in dataset")
            return 1
        
        # Calculate descriptive statistics
        statistics = calculate_descriptive_statistics(approved_df)
        
        # Create output dataframe
        output_df = create_output_dataframe(statistics)
        
        # Save output file
        output_filename = save_output_file(output_df, 'sample_statistics')
        
        print("\n=== ANALYSIS COMPLETED SUCCESSFULLY ===")
        print(f"Final output saved to: {output_filename}")
        print("Finished execution")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
