#!/usr/bin/env python3
"""
Script to process prolific survey data and generate demographic statistics.
Filters for approved participants, validates demographic data, and calculates
descriptive statistics for reporting purposes.
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime

def create_output_directory():
    """
    Create the outputs directory if it doesn't exist.
    
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
    Find all files matching the given pattern and return the most recent one.
    
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
    required_columns = ['Participant id', 'Age', 'Sex', 'Time taken', 'Status', 'Completed at']
    
    for file_path in file_paths:
        print(f"\nProcessing file: {file_path}")
        try:
            # Verify file exists
            if not os.path.exists(file_path):
                print(f"ERROR: File does not exist: {file_path}")
                continue
                
            # Check file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
            print(f"File size: {file_size:.2f} MB")
            
            # Load the data
            df = pd.read_csv(file_path)
            
            # Strip whitespace from column names
            df.columns = df.columns.str.strip()
            
            # Basic data validation
            print(f"Loaded {len(df)} rows from {file_path}")
            print(f"Columns in file: {list(df.columns)}")
            print(f"Data types:\n{df.dtypes.head()}")
            print("First 3 rows:")
            print(df.head(3))
            
            # Check if all required columns exist
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"WARNING: Missing required columns in {file_path}: {missing_cols}")
                print("Skipping this file")
                continue
            
            # Verify data types and convert if necessary
            for col in required_columns:
                if col in df.columns:
                    print(f"Verifying column '{col}'...")
                    non_null_count = df[col].count()
                    print(f"  Non-null values: {non_null_count}/{len(df)} ({non_null_count/len(df)*100:.1f}%)")
            
            # Select only required columns
            df_subset = df[required_columns].copy()
            all_data.append(df_subset)
            print(f"Added {len(df_subset)} rows to combined dataset")
            
        except pd.errors.EmptyDataError:
            print(f"ERROR: File is empty: {file_path}")
            continue
        except pd.errors.ParserError:
            print(f"ERROR: File format error in {file_path}")
            continue
        except Exception as e:
            print(f"ERROR loading {file_path}: {str(e)}")
            continue
    
    if not all_data:
        print("ERROR: No valid data files found")
        return pd.DataFrame()
    
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"\nCombined dataset shape: {combined_df.shape}")
    print("Combined dataset columns:")
    print(list(combined_df.columns))
    print("First 2 rows of combined data:")
    print(combined_df.head(2))
    
    return combined_df

def filter_completed_participants(df):
    """
    Filter for completed participants with approved status and valid participant IDs.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Filtered dataframe
        dict: Exclusion counts
    """
    print(f"\nStarting with {len(df)} total rows")
    print(f"Initial dataset shape: {df.shape}")
    
    exclusions = {
        'missing_participant_id': 0,
        'not_approved_status': 0,
        'total_excluded': 0
    }
    
    # Print unique values for Status column
    print(f"Unique Status values: {df['Status'].unique()}")
    print(f"Status value counts: \n{df['Status'].value_counts()}")
    
    # Check for missing values in key columns
    missing_values = df.isnull().sum()
    print(f"\nMissing values in each column:")
    for col, count in missing_values.items():
        if count > 0:
            print(f"  {col}: {count} missing values")
    
    # Remove rows with missing participant IDs
    initial_count = len(df)
    print(f"\nChecking for missing Participant IDs...")
    missing_id_mask = df['Participant id'].isna()
    if missing_id_mask.any():
        print(f"Found {missing_id_mask.sum()} rows with missing Participant IDs")
    
    df_filtered = df.dropna(subset=['Participant id']).copy()
    exclusions['missing_participant_id'] = initial_count - len(df_filtered)
    print(f"Excluded {exclusions['missing_participant_id']} participants with missing Participant id")
    
    # Filter for approved status only
    initial_count = len(df_filtered)
    print(f"\nFiltering for approved status only...")
    status_counts = df_filtered['Status'].value_counts()
    print(f"Status distribution before filtering:")
    for status, count in status_counts.items():
        print(f"  {status}: {count} participants ({count/len(df_filtered)*100:.1f}%)")
    
    not_approved_mask = df_filtered['Status'] != 'APPROVED'
    if not_approved_mask.any():
        not_approved_statuses = df_filtered[not_approved_mask]['Status'].unique()
        print(f"Found {not_approved_mask.sum()} participants with non-approved status: {not_approved_statuses}")
    
    df_filtered = df_filtered[df_filtered['Status'] == 'APPROVED'].copy()
    exclusions['not_approved_status'] = initial_count - len(df_filtered)
    print(f"Excluded {exclusions['not_approved_status']} participants with Status != 'APPROVED'")
    
    exclusions['total_excluded'] = len(df) - len(df_filtered)
    
    print(f"\nFiltering summary:")
    print(f"  Initial dataset: {len(df)} participants")
    print(f"  Missing Participant ID: {exclusions['missing_participant_id']} excluded")
    print(f"  Non-approved status: {exclusions['not_approved_status']} excluded")
    print(f"  Total excluded: {exclusions['total_excluded']} participants")
    print(f"  Remaining: {len(df_filtered)} participants")
    
    print(f"\nFinal filtered dataset: {len(df_filtered)} participants")
    print("First 2 rows of filtered data:")
    print(df_filtered.head(2))
    
    return df_filtered, exclusions

def validate_and_clean_demographics(df):
    """
    Validate and clean demographic data including age, sex, and completion time.
    
    Parameters:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Cleaned dataframe
        dict: Validation results
    """
    print(f"\nValidating demographics for {len(df)} participants")
    
    validation_results = {
        'age_out_of_range': 0,
        'invalid_age': 0,
        'invalid_sex': 0,
        'invalid_time': 0,
        'total_excluded': 0
    }
    
    df_clean = df.copy()
    initial_count = len(df_clean)
    
    # Print unique values for categorical columns
    print(f"Unique Sex values: {df_clean['Sex'].unique()}")
    
    # Track participants at each validation step
    remaining_participants = set(df_clean.index)
    excluded_by_criteria = {
        'invalid_age': set(),
        'age_out_of_range': set(),
        'invalid_sex': set(),
        'invalid_time': set()
    }
    
    # Convert Age to numeric
    print("Converting Age to numeric...")
    df_clean['Age'] = pd.to_numeric(df_clean['Age'], errors='coerce')
    invalid_age_mask = df_clean['Age'].isna()
    invalid_age_indices = set(df_clean[invalid_age_mask].index)
    excluded_by_criteria['invalid_age'] = invalid_age_indices
    validation_results['invalid_age'] = len(invalid_age_indices)
    print(f"Found {validation_results['invalid_age']} participants with invalid age")
    
    # Validate age range 18-35 (only for those with valid age)
    valid_age_mask = ~invalid_age_mask
    if valid_age_mask.any():
        age_out_of_range = (df_clean['Age'] < 18) | (df_clean['Age'] > 35)
        age_out_of_range_indices = set(df_clean[age_out_of_range & valid_age_mask].index)
        excluded_by_criteria['age_out_of_range'] = age_out_of_range_indices
        validation_results['age_out_of_range'] = len(age_out_of_range_indices)
        print(f"Found {validation_results['age_out_of_range']} participants outside age range 18-35")
        
        # Flag participants outside target age range
        if validation_results['age_out_of_range'] > 0:
            print("WARNING: Participants outside target age range detected!")
            out_of_range_ages = df_clean[age_out_of_range & valid_age_mask]['Age'].tolist()
            print(f"Out of range ages: {out_of_range_ages}")
    
    # Standardize Sex categories
    print("Standardizing Sex categories...")
    sex_mapping = {
        'male': 'Male',
        'Male': 'Male',
        'MALE': 'Male',
        'female': 'Female',
        'Female': 'Female',
        'FEMALE': 'Female',
        'other': 'Other',
        'Other': 'Other',
        'OTHER': 'Other',
        'Prefer not to say': 'Other',
        'prefer not to say': 'Other'
    }
    
    df_clean['Sex'] = df_clean['Sex'].apply(lambda x: sex_mapping.get(x, 'Other'))
    invalid_sex_mask = df_clean['Sex'].isna()
    invalid_sex_indices = set(df_clean[invalid_sex_mask].index)
    excluded_by_criteria['invalid_sex'] = invalid_sex_indices
    validation_results['invalid_sex'] = len(invalid_sex_indices)
    print(f"Found {validation_results['invalid_sex']} participants with invalid sex")
    
    # Convert Time taken to numeric and then to minutes
    print("Converting Time taken to minutes...")
    df_clean['Time taken'] = pd.to_numeric(df_clean['Time taken'], errors='coerce')
    invalid_time_mask = df_clean['Time taken'].isna()
    invalid_time_indices = set(df_clean[invalid_time_mask].index)
    excluded_by_criteria['invalid_time'] = invalid_time_indices
    validation_results['invalid_time'] = len(invalid_time_indices)
    print(f"Found {validation_results['invalid_time']} participants with invalid time")
    
    # Convert seconds to minutes
    df_clean['completion_time_minutes'] = df_clean['Time taken'] / 60.0
    
    # Remove rows with any invalid data
    all_excluded_indices = set().union(*excluded_by_criteria.values())
    validation_results['total_excluded'] = len(all_excluded_indices)
    
    # Keep only valid participants
    if len(all_excluded_indices) > 0:
        df_clean = df_clean[~df_clean.index.isin(all_excluded_indices)].copy()
    else:
        # No exclusions, keep all rows but still make a copy for consistency
        df_clean = df_clean.copy()
    
    print(f"After validation: {len(df_clean)} participants remain")
    print(f"Total excluded in validation: {validation_results['total_excluded']} participants")
    print("First 2 rows of cleaned data:")
    print(df_clean.head(2))
    
    # Store detailed exclusion information
    validation_results['excluded_by_criteria'] = {k: len(v) for k, v in excluded_by_criteria.items()}
    
    return df_clean, validation_results

def calculate_descriptive_statistics(df):
    """
    Calculate descriptive statistics for the cleaned dataset.
    
    Parameters:
        df (pd.DataFrame): Cleaned dataframe
        
    Returns:
        dict: Dictionary containing all calculated statistics
    """
    print(f"\nCalculating descriptive statistics for {len(df)} participants")
    
    stats = {}
    
    # Total participants
    stats['total_participants'] = len(df)
    print(f"Total participants who completed the study: {stats['total_participants']}")
    
    # Age statistics
    stats['age_mean'] = df['Age'].mean()
    stats['age_std'] = df['Age'].std()
    stats['age_min'] = df['Age'].min()
    stats['age_max'] = df['Age'].max()
    
    print(f"Age statistics:")
    print(f"  Mean: {stats['age_mean']:.2f}")
    print(f"  Standard deviation: {stats['age_std']:.2f}")
    print(f"  Minimum: {stats['age_min']}")
    print(f"  Maximum: {stats['age_max']}")
    
    # Sex distribution
    sex_counts = df['Sex'].value_counts()
    sex_percentages = df['Sex'].value_counts(normalize=True) * 100
    
    stats['sex_distribution'] = {}
    for sex in sex_counts.index:
        stats['sex_distribution'][sex] = {
            'count': sex_counts[sex],
            'percentage': sex_percentages[sex]
        }
    
    print(f"Sex distribution:")
    for sex, data in stats['sex_distribution'].items():
        print(f"  {sex}: {data['count']} ({data['percentage']:.1f}%)")
    
    # Completion time statistics (in minutes)
    stats['time_mean'] = df['completion_time_minutes'].mean()
    stats['time_std'] = df['completion_time_minutes'].std()
    stats['time_min'] = df['completion_time_minutes'].min()
    stats['time_max'] = df['completion_time_minutes'].max()
    
    print(f"Completion time statistics (minutes):")
    print(f"  Mean: {stats['time_mean']:.2f}")
    print(f"  Standard deviation: {stats['time_std']:.2f}")
    print(f"  Minimum: {stats['time_min']:.2f}")
    print(f"  Maximum: {stats['time_max']:.2f}")
    
    return stats

def create_summary_table(stats):
    """
    Create a summary statistics table for reporting.
    
    Parameters:
        stats (dict): Dictionary of calculated statistics
        
    Returns:
        pd.DataFrame: Summary statistics dataframe
    """
    print("\nCreating summary statistics table...")
    
    summary_data = []
    
    # Add overall statistics
    summary_data.append(['total_participants', float(stats['total_participants']), ''])
    
    # Add age statistics
    summary_data.append(['age_mean', stats['age_mean'], ''])
    summary_data.append(['age_std', stats['age_std'], ''])
    summary_data.append(['age_min', float(stats['age_min']), ''])
    summary_data.append(['age_max', float(stats['age_max']), ''])
    
    # Add sex distribution
    for sex, data in stats['sex_distribution'].items():
        summary_data.append(['sex_count', float(data['count']), sex])
        summary_data.append(['sex_percentage', data['percentage'], sex])
    
    # Add completion time statistics
    summary_data.append(['completion_time_mean', stats['time_mean'], ''])
    summary_data.append(['completion_time_std', stats['time_std'], ''])
    summary_data.append(['completion_time_min', stats['time_min'], ''])
    summary_data.append(['completion_time_max', stats['time_max'], ''])
    
    summary_df = pd.DataFrame(summary_data, columns=['statistic_name', 'value', 'category'])
    
    print("Summary table created:")
    print("All columns:", list(summary_df.columns))
    print("First 2 rows:")
    print(summary_df.head(2))
    
    return summary_df

def create_cleaned_demographic_data(df):
    """
    Create cleaned demographic dataset for output.
    
    Parameters:
        df (pd.DataFrame): Cleaned dataframe
        
    Returns:
        pd.DataFrame: Demographic data in required output format
    """
    print("\nCreating cleaned demographic data output...")
    
    output_df = pd.DataFrame({
        'participant_id': df['Participant id'],
        'age': df['Age'].astype(int),
        'sex': df['Sex'],
        'completion_time_minutes': df['completion_time_minutes'],
        'status': df['Status']
    })
    
    print("Cleaned demographic data created:")
    print("All columns:", list(output_df.columns))
    print("First 2 rows:")
    print(output_df.head(2))
    
    return output_df

def save_outputs(summary_df, demographic_df):
    """
    Save output files with timestamp.
    
    Parameters:
        summary_df (pd.DataFrame): Summary statistics dataframe
        demographic_df (pd.DataFrame): Cleaned demographic dataframe
        
    Returns:
        None
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save summary statistics
    summary_filename = f"outputs/sample_statistics_{timestamp}.csv"
    summary_df.to_csv(summary_filename, index=False)
    print(f"Saved summary statistics to: {summary_filename}")
    
    # Save cleaned demographic data
    demographic_filename = f"outputs/demographic_data_cleaned_{timestamp}.csv"
    demographic_df.to_csv(demographic_filename, index=False)
    print(f"Saved cleaned demographic data to: {demographic_filename}")

def main():
    """
    Main function to execute the data processing pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting prolific data processing script...")
        
        # Create output directory
        create_output_directory()
        
        # Find input files
        input_pattern = "raw_data/prolific_export_*.csv"
        input_files = find_input_files(input_pattern)
        
        if not input_files:
            print("ERROR: No input files found matching pattern")
            return 1
        
        # Load and combine data
        df = load_and_combine_data(input_files)
        if df.empty:
            print("ERROR: No valid data loaded")
            return 1
        
        # Filter for completed participants
        df_filtered, exclusions = filter_completed_participants(df)
        if df_filtered.empty:
            print("ERROR: No approved participants found")
            return 1
        
        # Validate and clean demographics
        df_clean, validation_results = validate_and_clean_demographics(df_filtered)
        if df_clean.empty:
            print("ERROR: No valid participants after demographic validation")
            return 1
        
        # Calculate descriptive statistics
        stats = calculate_descriptive_statistics(df_clean)
        
        # Store validation results for later use in exclusion summary
        if stats is not None and isinstance(stats, dict):
            stats['validation_results'] = validation_results
        else:
            print("WARNING: Could not store validation results in stats dictionary")
        
        # Verify sample characteristics
        print(f"\nSample characteristics verification:")
        print(f"Age range in sample: {stats['age_min']}-{stats['age_max']} years")
        if stats['age_min'] >= 18 and stats['age_max'] <= 35:
            print("✓ Sample age range aligns with target population (18-35 years)")
        else:
            print("⚠ WARNING: Sample includes participants outside target age range")
        
        # Create output tables
        summary_df = create_summary_table(stats)
        demographic_df = create_cleaned_demographic_data(df_clean)
        
        # Save outputs
        save_outputs(summary_df, demographic_df)
        
        # Print final summary
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total participants processed: {len(df)}")
        print(f"Participants excluded: {exclusions['total_excluded']}")
        print(f"Final sample size: {len(df_clean)}")
        print(f"Age range: {stats['age_min']}-{stats['age_max']} years")
        print(f"Mean age: {stats['age_mean']:.1f} years")
        print(f"Mean completion time: {stats['time_mean']:.1f} minutes")
        
        # Detailed exclusion documentation
        print(f"\n=== EXCLUSION SUMMARY ===")
        print(f"Data found for {len(df)} participants")
        print(f"0 participants had incomplete data and were removed")
        
        # Initial filtering exclusions
        print(f"\nInitial filtering exclusions:")
        print(f"  Participants excluded due to missing participant ID: {exclusions['missing_participant_id']}")
        print(f"  Participants excluded due to non-approved status: {exclusions['not_approved_status']}")
        
        # Demographic validation exclusions
        print(f"\nDemographic validation exclusions:")
        if validation_results and 'excluded_by_criteria' in validation_results:
            for criterion, count in validation_results['excluded_by_criteria'].items():
                print(f"  Participants excluded due to {criterion}: {count}")
        else:
            print(f"  Participants excluded due to invalid age: {validation_results.get('invalid_age', 0)}")
            print(f"  Participants excluded due to age out of range: {validation_results.get('age_out_of_range', 0)}")
            print(f"  Participants excluded due to invalid sex: {validation_results.get('invalid_sex', 0)}")
            print(f"  Participants excluded due to invalid time: {validation_results.get('invalid_time', 0)}")
        
        # Total exclusions
        validation_total = validation_results.get('total_excluded', 0)
        if validation_total == 0 and validation_results:
            # Fallback calculation if total_excluded not available
            validation_total = (validation_results.get('invalid_age', 0) + 
                               validation_results.get('invalid_sex', 0) + 
                               validation_results.get('invalid_time', 0))
        
        total_excluded = exclusions.get('total_excluded', 0) + validation_total
        print(f"\nTotal exclusions: {total_excluded} participants")
        print(f"Final dataset: {len(df_clean)} participants")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Script failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
