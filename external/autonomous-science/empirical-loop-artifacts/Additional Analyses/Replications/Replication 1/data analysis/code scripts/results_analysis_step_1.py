#!/usr/bin/env python3
"""
Script to process Prolific participant data and generate demographic statistics.
Filters for approved participants, calculates demographic statistics, and outputs
cleaned data and summary statistics.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys


def load_prolific_data(file_pattern):
    """
    Load Prolific export data from CSV files matching the given pattern.
    
    Parameters:
    -----------
    file_pattern : str
        File pattern to match Prolific export CSV files
        
    Returns:
    --------
    pandas.DataFrame
        Combined dataframe from all matching CSV files
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    # Find all matching files
    matching_files = glob.glob(file_pattern)
    print(f"Found {len(matching_files)} matching files: {matching_files}")
    
    if not matching_files:
        print("No matching files found!")
        return None
    
    # Load and combine all files
    all_data = []
    for file_path in matching_files:
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
        print("No data files could be loaded!")
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
    Validate that all required columns exist in the dataframe.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe to validate
    required_columns : list
        List of required column names
        
    Returns:
    --------
    bool
        True if all required columns exist, False otherwise
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        print(f"Available columns: {list(df.columns)}")
        return False
    
    print("All required columns found!")
    return True


def clean_and_filter_data(df):
    """
    Clean and filter the participant data according to specified criteria.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Raw participant data
        
    Returns:
    --------
    pandas.DataFrame
        Cleaned and filtered participant data
    dict
        Dictionary tracking exclusions at each step
    """
    print(f"\nStarting data cleaning...")
    print(f"Initial sample size: {len(df)}")
    
    exclusions = {}
    exclusions['initial'] = len(df)
    
    # Print unique values for key columns
    print(f"\nUnique Status values: {df['Status'].unique()}")
    print(f"Unique Sex values: {df['Sex'].unique()}")
    
    # Filter for approved participants
    print(f"\nFiltering for approved participants...")
    approved_df = df[df['Status'] == 'APPROVED'].copy()
    exclusions['not_approved'] = len(df) - len(approved_df)
    print(f"Participants with APPROVED status: {len(approved_df)}")
    
    # Remove participants with missing Age or Sex data
    print(f"\nRemoving participants with missing Age or Sex data...")
    pre_demo_filter_count = len(approved_df)
    clean_df = approved_df.dropna(subset=['Age', 'Sex']).copy()
    exclusions['missing_demographics'] = pre_demo_filter_count - len(clean_df)
    print(f"After removing missing Age/Sex: {len(clean_df)}")
    
    # Validate age range (18-35)
    print(f"\nValidating age range (18-35)...")
    print(f"Age range in data: {clean_df['Age'].min()} - {clean_df['Age'].max()}")
    
    # Convert Age to numeric if it's not already
    clean_df['Age'] = pd.to_numeric(clean_df['Age'], errors='coerce')
    
    # Filter for valid age range
    valid_age_df = clean_df[(clean_df['Age'] >= 18) & (clean_df['Age'] <= 35)].copy()
    exclusions['invalid_age'] = len(clean_df) - len(valid_age_df)
    print(f"Participants with invalid age (outside 18-35): {exclusions['invalid_age']}")
    print(f"Final sample after age filtering: {len(valid_age_df)}")
    
    # Validate completion timestamps
    print(f"\nValidating completion timestamps...")
    print(f"Missing 'Completed at' timestamps: {valid_age_df['Completed at'].isna().sum()}")
    print(f"Missing 'Started at' timestamps: {valid_age_df['Started at'].isna().sum()}")

    # Remove participants with missing timestamps
    pre_ts_filter_count = len(valid_age_df)
    final_df = valid_age_df.dropna(subset=['Completed at', 'Started at']).copy()
    exclusions['missing_timestamps'] = pre_ts_filter_count - len(final_df)
    print(f"Final sample size after timestamp validation: {len(final_df)}")
    
    # Calculate session_duration_minutes once here
    final_df['session_duration_minutes'] = final_df['Time taken'] / 60
    
    print("\nFirst 2 rows of cleaned data:")
    print(final_df.head(2))
    
    return final_df, exclusions


def calculate_demographics(df):
    """
    Calculate demographic statistics for the cleaned dataset.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Cleaned participant data
        
    Returns:
    --------
    dict
        Dictionary containing demographic statistics
    """
    print(f"\nCalculating demographic statistics...")
    
    stats = {}
    
    # Sample size
    stats['sample_size'] = len(df)
    print(f"Final sample size (N): {stats['sample_size']}")
    
    # Age statistics
    stats['age_mean'] = df['Age'].mean()
    stats['age_std'] = df['Age'].std()
    stats['age_min'] = df['Age'].min()
    stats['age_max'] = df['Age'].max()
    
    print(f"\nAge statistics:")
    print(f"  Mean: {stats['age_mean']:.2f}")
    print(f"  Standard deviation: {stats['age_std']:.2f}")
    print(f"  Minimum: {stats['age_min']}")
    print(f"  Maximum: {stats['age_max']}")
    
    # Sex distribution
    sex_counts = df['Sex'].value_counts()
    sex_percentages = df['Sex'].value_counts(normalize=True) * 100
    
    print(f"\nSex distribution:")
    for sex in sex_counts.index:
        count = sex_counts[sex]
        percentage = sex_percentages[sex]
        stats[f'sex_{sex.lower()}_count'] = count
        stats[f'sex_{sex.lower()}_percentage'] = percentage
        print(f"  {sex}: {count} ({percentage:.1f}%)")
    
    # Session duration (already calculated in cleaning)
    stats['session_duration_mean'] = df['session_duration_minutes'].mean()
    stats['session_duration_std'] = df['session_duration_minutes'].std()
    
    print(f"\nSession duration statistics:")
    print(f"  Mean: {stats['session_duration_mean']:.2f} minutes")
    print(f"  Standard deviation: {stats['session_duration_std']:.2f} minutes")
    
    return stats


def create_summary_statistics_table(stats):
    """
    Create a summary statistics table for output.
    
    Parameters:
    -----------
    stats : dict
        Dictionary containing demographic statistics
        
    Returns:
    --------
    pandas.DataFrame
        Summary statistics table
    """
    print(f"\nCreating summary statistics table...")
    
    summary_data = []
    
    # Sample size
    summary_data.append({
        'statistic_name': 'sample_size',
        'value': stats['sample_size'],
        'description': 'Total number of approved participants'
    })
    
    # Age statistics
    summary_data.append({
        'statistic_name': 'age_mean',
        'value': f"{stats['age_mean']:.2f}",
        'description': 'Mean age of participants'
    })
    
    summary_data.append({
        'statistic_name': 'age_std',
        'value': f"{stats['age_std']:.2f}",
        'description': 'Standard deviation of age'
    })
    
    summary_data.append({
        'statistic_name': 'age_min',
        'value': stats['age_min'],
        'description': 'Minimum age of participants'
    })
    
    summary_data.append({
        'statistic_name': 'age_max',
        'value': stats['age_max'],
        'description': 'Maximum age of participants'
    })
    
    # Sex distribution
    for key, value in stats.items():
        if key.startswith('sex_') and key.endswith('_count'):
            sex_type = key.replace('sex_', '').replace('_count', '')
            summary_data.append({
                'statistic_name': f'sex_{sex_type}_count',
                'value': value,
                'description': f'Number of {sex_type} participants'
            })
            
            # Add percentage
            percentage_key = f'sex_{sex_type}_percentage'
            if percentage_key in stats:
                summary_data.append({
                    'statistic_name': percentage_key,
                    'value': f"{stats[percentage_key]:.1f}",
                    'description': f'Percentage of {sex_type} participants'
                })
    
    # Session duration
    summary_data.append({
        'statistic_name': 'session_duration_mean',
        'value': f"{stats['session_duration_mean']:.2f}",
        'description': 'Mean session duration in minutes'
    })
    
    summary_data.append({
        'statistic_name': 'session_duration_std',
        'value': f"{stats['session_duration_std']:.2f}",
        'description': 'Standard deviation of session duration in minutes'
    })
    
    summary_df = pd.DataFrame(summary_data)
    print(f"Summary statistics table created with {len(summary_df)} rows")
    print("First 2 rows of summary table:")
    print(summary_df.head(2))
    
    return summary_df


def create_demographic_data_cleaned(df):
    """
    Create cleaned demographic data output table.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Cleaned participant data
        
    Returns:
    --------
    pandas.DataFrame
        Cleaned demographic data table
    """
    print(f"\nCreating cleaned demographic data table...")
    
    # Create output dataframe with required columns
    output_df = pd.DataFrame({
        'participant_id': df['Participant id'],
        'age': df['Age'],
        'sex': df['Sex'],
        'session_duration_minutes': df['session_duration_minutes'],
        'completion_date': pd.to_datetime(df['Completed at']).dt.date
    })
    
    print(f"Cleaned demographic data table created with {len(output_df)} rows")
    print("All columns:")
    print(list(output_df.columns))
    print("First 2 rows:")
    print(output_df.head(2))
    
    return output_df


def main():
    """
    Main function to execute the demographic analysis pipeline.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting demographic analysis pipeline...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Outputs directory ready")
        
        # Define required columns
        required_columns = [
            'Participant id', 'Status', 'Age', 'Sex', 
            'Completed at', 'Started at', 'Time taken'
        ]
        
        # Load data
        file_pattern = '../C_results/data/prolific_export_*.csv'
        df = load_prolific_data(file_pattern)
        
        if df is None:
            print("Failed to load data!")
            return 1
        
        initial_participant_count = len(df)
        
        # Validate required columns
        if not validate_required_columns(df, required_columns):
            print("Required columns missing!")
            return 1
        
        # Clean and filter data
        clean_df, exclusion_counts = clean_and_filter_data(df)
        
        if len(clean_df) == 0:
            print("No participants remaining after cleaning!")
            return 1
        
        # Calculate demographics
        stats = calculate_demographics(clean_df)
        
        # Create output tables
        summary_stats_df = create_summary_statistics_table(stats)
        demographic_data_df = create_demographic_data_cleaned(clean_df)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save output files
        summary_output_path = f'outputs/sample_statistics_{timestamp}.csv'
        demographic_output_path = f'outputs/demographic_data_cleaned_{timestamp}.csv'
        
        print(f"\nSaving output files...")
        summary_stats_df.to_csv(summary_output_path, index=False)
        print(f"Summary statistics saved to: {summary_output_path}")
        
        demographic_data_df.to_csv(demographic_output_path, index=False)
        print(f"Cleaned demographic data saved to: {demographic_output_path}")
        
        # Print exclusion summary
        print("\n--- Data Cleaning Summary ---")
        print(f"Data found for {initial_participant_count} participants")
        print(f"{exclusion_counts.get('not_approved', 0)} participants removed due to status not being 'APPROVED'.")
        print(f"{exclusion_counts.get('missing_demographics', 0)} participants removed due to missing Age or Sex.")
        print(f"{exclusion_counts.get('invalid_age', 0)} participants removed due to age outside the 18-35 range.")
        print(f"{exclusion_counts.get('missing_timestamps', 0)} participants removed due to missing completion/start timestamps.")
        print(f"Final dataset: {len(clean_df)} participants")
        print("---------------------------")
        
        print("\nAnalysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
