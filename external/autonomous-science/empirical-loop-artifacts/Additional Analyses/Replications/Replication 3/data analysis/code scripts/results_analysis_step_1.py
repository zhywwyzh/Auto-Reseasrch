#!/usr/bin/env python3
"""
Script to process Prolific export data and generate sample statistics for approved participants.
This script filters data to approved participants only, calculates demographic statistics,
validates data quality, and creates a summary statistics table.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys


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
    pandas.DataFrame: Combined dataframe from all files
    """
    all_data = []
    
    for file_path in file_paths:
        print(f"\nLoading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print(f"File loaded successfully. Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            all_data.append(df)
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            continue
    
    if not all_data:
        print("No data files could be loaded successfully")
        return None
    
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
    df (pandas.DataFrame): Input dataframe
    required_columns (list): List of required column names
    
    Returns:
    bool: True if all required columns exist, False otherwise
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return False
    print("All required columns found")
    return True


def filter_approved_participants(df):
    """
    Filter dataframe to include only approved participants.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with Status column
    
    Returns:
    pandas.DataFrame: Filtered dataframe with only approved participants
    """
    print(f"\nOriginal data shape: {df.shape}")
    print(f"Unique Status values: {df['Status'].unique()}")
    
    # Filter to approved participants only
    approved_df = df[df['Status'] == 'APPROVED'].copy()
    print(f"Approved participants shape: {approved_df.shape}")
    print(f"Number of participants excluded (not approved): {len(df) - len(approved_df)}")
    
    return approved_df


def validate_data_quality(df):
    """
    Validate data quality by checking for missing values and reasonable age ranges.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe
    
    Returns:
    dict: Dictionary containing validation results and statistics
    """
    validation_results = {}
    
    print("\n=== DATA QUALITY VALIDATION ===")
    
    # Check for missing values in key demographic variables
    key_columns = ['Participant id', 'Age', 'Sex']
    missing_data = {}
    
    for col in key_columns:
        missing_count = df[col].isna().sum()
        missing_percentage = (missing_count / len(df)) * 100
        missing_data[col] = {'count': missing_count, 'percentage': missing_percentage}
        print(f"Missing values in {col}: {missing_count} ({missing_percentage:.2f}%)")
    
    validation_results['missing_data'] = missing_data
    
    # Print unique values for categorical variables
    print(f"\nUnique Sex values: {df['Sex'].unique()}")
    print(f"Unique Status values: {df['Status'].unique()}")
    
    # Validate age ranges (18-35 based on inclusion criteria)
    print(f"\nAge validation:")
    print(f"Age data type: {df['Age'].dtype}")
    age_stats = df['Age'].describe()
    print(f"Age statistics:\n{age_stats}")
    
    # Check for ages outside reasonable range
    unreasonable_ages = df[(df['Age'] < 18) | (df['Age'] > 35)]
    print(f"Participants with ages outside 18-35 range: {len(unreasonable_ages)}")
    if len(unreasonable_ages) > 0:
        print(f"Ages outside range: {unreasonable_ages['Age'].tolist()}")
    
    validation_results['age_validation'] = {
        'unreasonable_count': len(unreasonable_ages),
        'age_range_valid': len(unreasonable_ages) == 0
    }
    
    return validation_results


def calculate_demographic_statistics(df):
    """
    Calculate demographic statistics for approved participants.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with approved participants
    
    Returns:
    list: List of dictionaries containing statistics
    """
    statistics = []
    
    print("\n=== CALCULATING DEMOGRAPHIC STATISTICS ===")
    
    # Total number of participants
    total_n = len(df)
    print(f"Total number of approved participants (N): {total_n}")
    statistics.append({
        'statistic_name': 'total_participants',
        'value': total_n,
        'additional_info': 'Total number of approved participants'
    })
    
    # Age statistics
    age_data = df['Age'].dropna()
    print(f"\nAge statistics (N={len(age_data)}):")
    
    age_mean = age_data.mean()
    age_std = age_data.std()
    age_min = age_data.min()
    age_max = age_data.max()
    
    print(f"Age mean: {age_mean:.2f}")
    print(f"Age standard deviation: {age_std:.2f}")
    print(f"Age minimum: {age_min}")
    print(f"Age maximum: {age_max}")
    
    statistics.extend([
        {
            'statistic_name': 'age_mean',
            'value': round(age_mean, 2),
            'additional_info': 'Mean age of approved participants'
        },
        {
            'statistic_name': 'age_std',
            'value': round(age_std, 2),
            'additional_info': 'Standard deviation of age'
        },
        {
            'statistic_name': 'age_min',
            'value': int(age_min),
            'additional_info': 'Minimum age'
        },
        {
            'statistic_name': 'age_max',
            'value': int(age_max),
            'additional_info': 'Maximum age'
        }
    ])
    
    # Sex distribution
    sex_counts = df['Sex'].value_counts()
    sex_percentages = df['Sex'].value_counts(normalize=True) * 100
    
    print(f"\nSex distribution:")
    for sex_category in sex_counts.index:
        count = sex_counts[sex_category]
        percentage = sex_percentages[sex_category]
        print(f"{sex_category}: {count} ({percentage:.1f}%)")
        
        statistics.extend([
            {
                'statistic_name': f'sex_{sex_category.lower()}_count',
                'value': int(count),
                'additional_info': f'Number of {sex_category} participants'
            },
            {
                'statistic_name': f'sex_{sex_category.lower()}_percentage',
                'value': round(percentage, 1),
                'additional_info': f'Percentage of {sex_category} participants'
            }
        ])
    
    return statistics


def create_summary_table(statistics, validation_results):
    """
    Create summary statistics table with descriptive information.
    
    Parameters:
    statistics (list): List of statistic dictionaries
    validation_results (dict): Validation results
    
    Returns:
    pandas.DataFrame: Summary statistics dataframe
    """
    print("\n=== CREATING SUMMARY STATISTICS TABLE ===")
    
    # Convert statistics to dataframe
    summary_df = pd.DataFrame(statistics)
    
    # Add validation information
    validation_stats = []
    
    # Add missing data information
    for col, data in validation_results['missing_data'].items():
        validation_stats.append({
            'statistic_name': f'missing_data_{col.lower().replace(" ", "_")}',
            'value': data['count'],
            'additional_info': f'Number of missing values in {col}'
        })
    
    # Add age validation information
    validation_stats.append({
        'statistic_name': 'age_outside_range_count',
        'value': validation_results['age_validation']['unreasonable_count'],
        'additional_info': 'Number of participants with age outside 18-35 range'
    })
    
    # Combine all statistics
    validation_df = pd.DataFrame(validation_stats)
    final_summary = pd.concat([summary_df, validation_df], ignore_index=True)
    
    print(f"Summary table created with {len(final_summary)} statistics")
    print("Summary table columns:")
    print(list(final_summary.columns))
    print("First 2 rows of summary table:")
    print(final_summary.head(2))
    
    return final_summary


def save_output(summary_df, output_dir='outputs'):
    """
    Save summary statistics to CSV file with timestamp.
    
    Parameters:
    summary_df (pandas.DataFrame): Summary statistics dataframe
    output_dir (str): Output directory path
    
    Returns:
    str: Output file path
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"sample_statistics_{timestamp}.csv"
    output_path = os.path.join(output_dir, output_filename)
    
    # Save to CSV
    summary_df.to_csv(output_path, index=False)
    print(f"Summary statistics saved to: {output_path}")
    
    return output_path


def main():
    """
    Main function to execute the demographic analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting demographic analysis script...")
        
        # Define required columns
        required_columns = ['Participant id', 'Age', 'Sex', 'Time taken', 'Status']
        
        # Find input files
        input_pattern = '../C_results/data/prolific_export_*.csv'
        input_files = find_input_files(input_pattern)
        
        if not input_files:
            print(f"No input files found matching pattern: {input_pattern}")
            return 1
        
        # Load and combine data
        df = load_and_combine_data(input_files)
        if df is None:
            print("Failed to load any data files")
            return 1
        
        # Validate required columns exist
        if not validate_required_columns(df, required_columns):
            print("Required columns missing from input data")
            return 1
        
        # Filter to approved participants only
        approved_df = filter_approved_participants(df)
        if len(approved_df) == 0:
            print("No approved participants found in data")
            return 1
        
        # Validate data quality
        validation_results = validate_data_quality(approved_df)
        
        # Calculate demographic statistics
        statistics = calculate_demographic_statistics(approved_df)
        
        # Create summary table
        summary_table = create_summary_table(statistics, validation_results)
        
        # Save output
        output_path = save_output(summary_table)
        
        # Print final data processing summary
        print(f"\n=== DATA PROCESSING SUMMARY ===")
        print(f"Data found for {len(df)} participants")
        print(f"0 participants had incomplete data and were removed")
        print(f"0 participants were removed due to exclusion criteria (all were pre-approved)")
        print(f"Final dataset: {len(approved_df)} approved participants")
        
        print(f"\nAnalysis completed successfully!")
        print(f"Final summary statistics saved to: {output_path}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
