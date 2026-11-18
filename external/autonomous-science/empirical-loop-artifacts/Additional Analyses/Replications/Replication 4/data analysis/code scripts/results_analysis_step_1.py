#!/usr/bin/env python3

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def load_prolific_data(file_pattern):
    """
    Load and combine Prolific export CSV files matching the specified pattern.
    
    Parameters:
    -----------
    file_pattern : str
        File pattern to match Prolific export CSV files
        
    Returns:
    --------
    pd.DataFrame
        Combined dataframe from all matching CSV files
    """
    print(f"Searching for files matching pattern: {file_pattern}")
    
    # Find all matching files
    matching_files = glob.glob(file_pattern)
    print(f"Found {len(matching_files)} matching files: {matching_files}")
    
    if not matching_files:
        print("ERROR: No files found matching the pattern")
        return None
    
    # Load and combine all files
    combined_data = []
    for file_path in matching_files:
        print(f"Loading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print(f"File shape: {df.shape}")
            print(f"Columns in file: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            combined_data.append(df)
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            continue
    
    if not combined_data:
        print("ERROR: No files could be loaded successfully")
        return None
    
    # Combine all dataframes
    final_df = pd.concat(combined_data, ignore_index=True)
    print(f"Combined dataset shape: {final_df.shape}")
    print(f"Combined dataset columns: {list(final_df.columns)}")
    print("First 2 rows of combined data:")
    print(final_df.head(2))
    
    return final_df

def validate_required_columns(df, required_columns):
    """
    Validate that required columns exist in the dataframe.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe to validate
    required_columns : list
        List of required column names
        
    Returns:
    --------
    bool
        True if all required columns exist, False otherwise
    """
    print(f"Checking for required columns: {required_columns}")
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    print("All required columns found")
    return True

def filter_completed_participants(df):
    """
    Filter dataframe to include only completed participants with valid demographic data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with participant data
        
    Returns:
    --------
    tuple
        (Filtered dataframe with only completed participants,
         exclusions_non_approved,
         exclusions_missing_demo)
    """
    print("Starting participant filtering...")
    print(f"Initial dataset shape: {df.shape}")
    
    # Print unique status values
    print(f"Unique status values: {df['status'].unique()}")
    
    # Filter for completed participants (APPROVED status)
    print("Filtering for APPROVED status participants...")
    initial_count = len(df)
    completed_df = df[df['status'] == 'APPROVED'].copy()
    after_status_count = len(completed_df)
    exclusions_non_approved = initial_count - after_status_count
    print(f"After status filtering: {completed_df.shape[0]} participants")
    
    # Check for missing demographic data
    print("Checking for missing demographic data...")
    print(f"Missing participant_id: {completed_df['participant_id'].isnull().sum()}")
    print(f"Missing age: {completed_df['age'].isnull().sum()}")
    print(f"Missing sex: {completed_df['sex'].isnull().sum()}")
    
    # Remove participants with missing demographic data
    before_demo_count = len(completed_df)
    completed_df = completed_df.dropna(subset=['participant_id', 'age', 'sex'])
    after_demo_count = len(completed_df)
    exclusions_missing_demo = before_demo_count - after_demo_count
    print(f"Excluded {exclusions_missing_demo} participants due to missing demographic data")
    print(f"Final sample after demographic filtering: {after_demo_count} participants")
    
    return completed_df, exclusions_non_approved, exclusions_missing_demo

def validate_participant_data(df):
    """
    Perform validation checks on participant data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe with participant data
        
    Returns:
    --------
    tuple
        (Validated dataframe with exclusions applied,
         exclusions_duplicate_ids,
         exclusions_age)
    """
    print("Performing validation checks...")
    
    # Check for unique participant IDs
    print("Checking participant ID uniqueness...")
    duplicate_ids = df['participant_id'].duplicated().sum()
    exclusions_duplicate_ids = 0
    if duplicate_ids > 0:
        print(f"WARNING: Found {duplicate_ids} duplicate participant IDs")
        print("Removing duplicate entries (keeping first occurrence)...")
        exclusions_duplicate_ids = duplicate_ids
        df = df.drop_duplicates(subset=['participant_id'], keep='first')
        print(f"After removing duplicates: {len(df)} participants")
    else:
        print("All participant IDs are unique")
    
    # Check age range (18-35 based on screening criteria)
    print("Checking age range (expected: 18-35)...")
    print(f"Age range in data: {df['age'].min()} - {df['age'].max()}")
    
    initial_count = len(df)
    valid_age_df = df[(df['age'] >= 18) & (df['age'] <= 35)].copy()
    final_count = len(valid_age_df)
    exclusions_age = initial_count - final_count
    
    print(f"Excluded {exclusions_age} participants due to age outside 18-35 range")
    print(f"Final sample after age validation: {final_count} participants")
    
    # Print unique sex values
    print(f"Unique sex values: {valid_age_df['sex'].unique()}")
    
    return valid_age_df, exclusions_duplicate_ids, exclusions_age

def calculate_descriptive_statistics(df):
    """
    Calculate descriptive statistics for the final sample.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Validated dataframe with participant data
        
    Returns:
    --------
    list
        List of dictionaries containing statistics
    """
    print("Calculating descriptive statistics...")
    
    statistics = []
    
    # Total number of participants
    total_participants = len(df['participant_id'].unique())
    statistics.append({
        'statistic_name': 'total_participants',
        'statistic_value': total_participants,
        'additional_info': 'count'
    })
    print(f"Total participants: {total_participants}")
    
    # Age statistics
    mean_age = df['age'].mean()
    std_age = df['age'].std()
    min_age = df['age'].min()
    max_age = df['age'].max()
    
    statistics.extend([
        {
            'statistic_name': 'mean_age',
            'statistic_value': round(mean_age, 2),
            'additional_info': 'years'
        },
        {
            'statistic_name': 'std_age',
            'statistic_value': round(std_age, 2),
            'additional_info': 'years'
        },
        {
            'statistic_name': 'min_age',
            'statistic_value': min_age,
            'additional_info': 'years'
        },
        {
            'statistic_name': 'max_age',
            'statistic_value': max_age,
            'additional_info': 'years'
        }
    ])
    
    print(f"Mean age: {mean_age:.2f} years")
    print(f"Age SD: {std_age:.2f} years")
    print(f"Age range: {min_age} - {max_age} years")
    
    # Sex distribution
    sex_counts = df['sex'].value_counts()
    print("Sex distribution:")
    for sex_category, count in sex_counts.items():
        percentage = (count / total_participants) * 100
        print(f"  {sex_category}: {count} ({percentage:.1f}%)")
        
        # Add count statistic
        statistics.append({
            'statistic_name': f'sex_{sex_category}_count',
            'statistic_value': count,
            'additional_info': 'count'
        })
        
        # Add percentage statistic
        statistics.append({
            'statistic_name': f'sex_{sex_category}_percent',
            'statistic_value': round(percentage, 1),
            'additional_info': 'percent'
        })
    
    return statistics

def save_statistics_table(statistics, output_dir):
    """
    Save statistics to CSV file with timestamp.
    
    Parameters:
    -----------
    statistics : list
        List of dictionaries containing statistics
    output_dir : str
        Output directory path
        
    Returns:
    --------
    str
        Path to saved file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sample_statistics_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Convert to DataFrame and save
    stats_df = pd.DataFrame(statistics)
    print("Statistics table:")
    print(stats_df)
    
    stats_df.to_csv(filepath, index=False)
    print(f"Statistics saved to: {filepath}")
    
    return filepath

def main():
    """
    Main function to execute the sample statistics calculation task.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("=== PROLIFIC DATA SAMPLE STATISTICS CALCULATION ===")
        print(f"Script started at: {datetime.now()}")
        
        # Define required columns
        required_columns = ['participant_id', 'age', 'sex', 'time_taken', 'status']
        
        # Load data
        file_pattern = "../C_results/data/prolific_export_*.csv"
        df = load_prolific_data(file_pattern)
        
        if df is None:
            print("ERROR: Could not load data")
            return 1

        # Clean column names and map to expected format
        print("Cleaning and mapping column names...")
        df.columns = df.columns.str.strip()
        print(f"Columns after stripping whitespace: {list(df.columns)}")

        # Validate original CSV columns exist before mapping
        original_required_columns = ['Participant id', 'Age', 'Sex', 'Time taken', 'Status']
        if not validate_required_columns(df, original_required_columns):
            print("ERROR: Missing required columns in original CSV format")
            return 1

        # Map actual CSV column names to expected names
        column_mapping = {
            'Participant id': 'participant_id',
            'Age': 'age',
            'Sex': 'sex',
            'Time taken': 'time_taken',
            'Status': 'status'
        }

        # Apply column mapping
        df = df.rename(columns=column_mapping)
        print(f"Columns after mapping: {list(df.columns)}")
        print("Column mapping completed successfully")
        
        # Validate required columns
        if not validate_required_columns(df, required_columns):
            print("ERROR: Missing required columns")
            return 1

        # Exclusion tracking variables
        initial_count = len(df)
        print(f"Initial participant count: {initial_count}")

        # Filter for completed participants
        completed_df, exclusions_non_approved, exclusions_missing_demo = filter_completed_participants(df)
        
        if len(completed_df) == 0:
            print("ERROR: No completed participants found")
            return 1
        
        # Validate participant data
        validated_df, exclusions_duplicate_ids, exclusions_age = validate_participant_data(completed_df)
        
        if len(validated_df) == 0:
            print("ERROR: No valid participants after validation")
            return 1

        # Calculate descriptive statistics
        statistics = calculate_descriptive_statistics(validated_df)
        
        # Save statistics table
        output_filepath = save_statistics_table(statistics, 'outputs')

        # Print required exclusion documentation format
        print(f"Data found for {initial_count} participants")
        if exclusions_missing_demo > 0:
            print(f"{exclusions_missing_demo} participants had incomplete data and were removed")
        if exclusions_non_approved > 0:
            print(f"{exclusions_non_approved} participants were removed due to non-APPROVED status")
        if exclusions_duplicate_ids > 0:
            print(f"{exclusions_duplicate_ids} participants were removed due to duplicate participant IDs")
        if exclusions_age > 0:
            print(f"{exclusions_age} participants were removed due to age outside 18-35 range")
        print(f"Final dataset: {len(validated_df)} participants")

        print(f"=== TASK COMPLETED SUCCESSFULLY ===")
        print(f"Final sample size: {len(validated_df)} participants")
        print(f"Statistics saved to: {output_filepath}")
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
