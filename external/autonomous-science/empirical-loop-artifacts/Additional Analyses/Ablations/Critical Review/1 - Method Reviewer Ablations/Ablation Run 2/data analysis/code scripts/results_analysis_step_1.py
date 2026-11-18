#!/usr/bin/env python3
"""
Prolific Sample Demographics Analysis Script

This script processes Prolific demographic data to calculate sample characteristics,
validate data completeness, and generate summary statistics for approved participants.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def load_prolific_data(file_pattern):
    """
    Load Prolific demographic data from CSV files matching the specified pattern.
    
    Parameters:
    -----------
    file_pattern : str
        File pattern to match Prolific export CSV files
        
    Returns:
    --------
    pd.DataFrame
        Combined dataframe with all Prolific data
    """
    print(f"Loading Prolific data from pattern: {file_pattern}")
    
    # Find all files matching the pattern
    file_list = glob.glob(file_pattern)
    print(f"Found {len(file_list)} files matching pattern")
    
    if not file_list:
        print("No files found matching the pattern!")
        return pd.DataFrame()
    
    # Sort files by creation time and use the most recent
    file_list.sort(key=os.path.getctime, reverse=True)
    latest_file = file_list[0]
    print(f"Using most recent file: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file)
        print(f"Successfully loaded data with shape: {df.shape}")
        
        # Print all columns
        print("All columns in dataset:")
        print(df.columns.tolist())
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        return df
        
    except Exception as e:
        print(f"Error loading file {latest_file}: {e}")
        return pd.DataFrame()

def validate_required_columns(df, required_columns):
    """
    Validate that all required columns are present in the dataframe.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe to validate
    required_columns : list
        List of required column names
        
    Returns:
    --------
    bool
        True if all required columns are present, False otherwise
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return False
    
    print("All required columns are present")
    return True

def filter_approved_participants(df):
    """
    Filter dataframe to include only approved participants.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe with participant data
        
    Returns:
    --------
    pd.DataFrame
        Filtered dataframe with only approved participants
    """
    print("Filtering for approved participants...")
    
    # Print unique Status values
    print("Unique Status values:")
    print(df['Status'].unique())
    
    # Filter for approved participants
    approved_df = df[df['Status'] == 'APPROVED'].copy()
    
    print(f"Total participants before filtering: {len(df)}")
    print(f"Approved participants after filtering: {len(approved_df)}")
    
    return approved_df

def calculate_age_statistics(df):
    """
    Calculate age statistics for the sample.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe with participant data
        
    Returns:
    --------
    dict
        Dictionary containing age statistics
    """
    print("Calculating age statistics...")
    
    # Check for missing age data
    missing_age = df['Age'].isna().sum()
    print(f"Missing age data: {missing_age} participants")
    
    # Calculate statistics on non-missing age data
    valid_ages = df['Age'].dropna()
    
    if len(valid_ages) == 0:
        print("No valid age data available")
        return {
            'age_mean': np.nan,
            'age_std': np.nan,
            'age_min': np.nan,
            'age_max': np.nan,
            'age_n': 0
        }
    
    age_stats = {
        'age_mean': valid_ages.mean(),
        'age_std': valid_ages.std(),
        'age_min': valid_ages.min(),
        'age_max': valid_ages.max(),
        'age_n': len(valid_ages)
    }
    
    print(f"Age statistics: Mean={age_stats['age_mean']:.2f}, SD={age_stats['age_std']:.2f}, Range={age_stats['age_min']}-{age_stats['age_max']}")
    
    return age_stats

def calculate_sex_distribution(df):
    """
    Calculate sex distribution for the sample.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe with participant data
        
    Returns:
    --------
    dict
        Dictionary containing sex distribution statistics
    """
    print("Calculating sex distribution...")
    
    # Print unique Sex values
    print("Unique Sex values:")
    print(df['Sex'].unique())
    
    # Check for missing sex data
    missing_sex = df['Sex'].isna().sum()
    print(f"Missing sex data: {missing_sex} participants")
    
    # Calculate distribution
    sex_counts = df['Sex'].value_counts(dropna=False)
    total_valid = df['Sex'].notna().sum()
    
    sex_stats = {}
    for sex, count in sex_counts.items():
        if pd.notna(sex):
            percentage = (count / len(df)) * 100 if len(df) > 0 else 0
            sex_stats[f'sex_{sex.lower()}_n'] = count
            sex_stats[f'sex_{sex.lower()}_pct'] = percentage
            print(f"{sex}: n={count}, {percentage:.1f}%")
    
    return sex_stats

def calculate_session_duration_statistics(df):
    """
    Calculate session duration statistics (expects 'session_duration_minutes' column to exist).
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe with participant data
        
    Returns:
    --------
    dict
        Dictionary containing session duration statistics
    """
    print("Calculating session duration statistics...")
    
    # Check for missing duration data
    missing_duration = df['session_duration_minutes'].isna().sum()
    print(f"Missing session duration data: {missing_duration} participants")
    
    # Calculate statistics on non-missing duration data
    valid_durations = df['session_duration_minutes'].dropna()
    
    if len(valid_durations) == 0:
        print("No valid session duration data available")
        return {
            'duration_mean': np.nan,
            'duration_std': np.nan,
            'duration_min': np.nan,
            'duration_max': np.nan,
            'duration_n': 0
        }
    
    duration_stats = {
        'duration_mean': valid_durations.mean(),
        'duration_std': valid_durations.std(),
        'duration_min': valid_durations.min(),
        'duration_max': valid_durations.max(),
        'duration_n': len(valid_durations)
    }
    
    print(f"Session duration statistics: Mean={duration_stats['duration_mean']:.2f} min, SD={duration_stats['duration_std']:.2f} min, Range={duration_stats['duration_min']:.2f}-{duration_stats['duration_max']:.2f} min")
    
    return duration_stats

def validate_data_completeness(df):
    """
    Validate data completeness for demographic variables.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe with participant data
        
    Returns:
    --------
    tuple
        (dict of completeness statistics, pd.Series of completeness boolean)
    """
    print("Validating data completeness...")
    
    total_participants = len(df)
    
    # Check completeness for Age and Sex
    complete_age = df['Age'].notna().sum()
    complete_sex = df['Sex'].notna().sum()
    complete_both_series = (df['Age'].notna()) & (df['Sex'].notna())
    complete_both = complete_both_series.sum()
    
    completeness_stats = {
        'total_n': total_participants,
        'complete_age_n': complete_age,
        'complete_sex_n': complete_sex,
        'complete_demographics_n': complete_both,
        'complete_demographics_pct': (complete_both / total_participants) * 100 if total_participants > 0 else 0
    }
    
    print(f"Data completeness: {complete_both}/{total_participants} ({completeness_stats['complete_demographics_pct']:.1f}%) have complete demographic data")
    
    return completeness_stats, complete_both_series

def create_summary_statistics_table(df, age_stats, sex_stats, duration_stats, completeness_stats):
    """
    Create summary statistics table with all calculated metrics.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe with participant data
    age_stats : dict
        Age statistics
    sex_stats : dict
        Sex distribution statistics
    duration_stats : dict
        Session duration statistics
    completeness_stats : dict
        Data completeness statistics
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics table
    """
    print("Creating summary statistics table...")
    
    summary_data = []
    
    # Total N
    summary_data.append({
        'metric_name': 'total_n',
        'value': len(df),
        'description': 'Total number of approved participants'
    })
    
    # Age statistics
    summary_data.append({
        'metric_name': 'age_mean',
        'value': age_stats['age_mean'],
        'description': 'Mean age in years'
    })
    summary_data.append({
        'metric_name': 'age_std',
        'value': age_stats['age_std'],
        'description': 'Standard deviation of age in years'
    })
    summary_data.append({
        'metric_name': 'age_range',
        'value': f"{age_stats['age_min']}-{age_stats['age_max']}",
        'description': 'Age range (min-max)'
    })
    
    # Sex distribution
    for key, value in sex_stats.items():
        if '_n' in key:
            sex_type = key.replace('sex_', '').replace('_n', '')
            summary_data.append({
                'metric_name': key,
                'value': value,
                'description': f'Number of {sex_type} participants'
            })
        elif '_pct' in key:
            sex_type = key.replace('sex_', '').replace('_pct', '')
            summary_data.append({
                'metric_name': key,
                'value': value,
                'description': f'Percentage of {sex_type} participants'
            })
    
    # Session duration statistics
    summary_data.append({
        'metric_name': 'duration_mean',
        'value': duration_stats['duration_mean'],
        'description': 'Mean session duration in minutes'
    })
    summary_data.append({
        'metric_name': 'duration_std',
        'value': duration_stats['duration_std'],
        'description': 'Standard deviation of session duration in minutes'
    })
    summary_data.append({
        'metric_name': 'duration_range',
        'value': f"{duration_stats['duration_min']:.2f}-{duration_stats['duration_max']:.2f}",
        'description': 'Session duration range (min-max) in minutes'
    })
    
    # Data completeness
    summary_data.append({
        'metric_name': 'complete_demographics_pct',
        'value': completeness_stats['complete_demographics_pct'],
        'description': 'Percentage of participants with complete demographic data'
    })
    
    summary_df = pd.DataFrame(summary_data)
    
    print("Summary statistics table created:")
    print("All columns:")
    print(summary_df.columns.tolist())
    print("\nFirst 2 rows:")
    print(summary_df.head(2))
    
    return summary_df

def create_participant_demographics_table(df):
    """
    Create participant demographics table with required columns.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataframe with participant data
        
    Returns:
    --------
    pd.DataFrame
        Participant demographics table
    """
    print("Creating participant demographics table...")
    
    # Create the output dataframe with required columns
    demographics_df = pd.DataFrame({
        'participant_id': df['Participant id'],
        'age': df['Age'],
        'sex': df['Sex'],
        'session_duration_minutes': df['session_duration_minutes'],
        'status': df['Status'],
        'complete_demographics': df['complete_demographics']
    })
    
    print("Participant demographics table created:")
    print("All columns:")
    print(demographics_df.columns.tolist())
    print("\nFirst 2 rows:")
    print(demographics_df.head(2))
    
    return demographics_df

def save_output_files(summary_df, demographics_df):
    """
    Save output files to the outputs directory.
    
    Parameters:
    -----------
    summary_df : pd.DataFrame
        Summary statistics dataframe
    demographics_df : pd.DataFrame
        Participant demographics dataframe
    """
    print("Saving output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save summary statistics
    summary_filename = f'outputs/sample_statistics_{timestamp}.csv'
    summary_df.to_csv(summary_filename, index=False)
    print(f"Saved summary statistics to: {summary_filename}")
    
    # Save participant demographics
    demographics_filename = f'outputs/participant_demographics_{timestamp}.csv'
    demographics_df.to_csv(demographics_filename, index=False)
    print(f"Saved participant demographics to: {demographics_filename}")

def main():
    """
    Main function to execute the Prolific sample demographics analysis.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting Prolific Sample Demographics Analysis")
        print("=" * 50)
        
        # Define required columns
        required_columns = ['Participant id', 'Age', 'Sex', 'Time taken', 'Status']
        
        # Load Prolific data
        file_pattern = '../C_results/data/prolific_export_*.csv'
        df = load_prolific_data(file_pattern)
        
        # Track initial participant count
        initial_total_n = len(df)
        
        if df.empty:
            print("No data loaded. Exiting.")
            return 1
        
        # Validate required columns
        if not validate_required_columns(df, required_columns):
            print("Required columns missing. Exiting.")
            return 1
        
        # Filter for approved participants
        approved_df = filter_approved_participants(df)
        approved_n = len(approved_df)
        
        if approved_df.empty:
            print("No approved participants found. Exiting.")
            return 1
        
        # Centralize creation of session_duration_minutes column
        approved_df['session_duration_minutes'] = approved_df['Time taken'] / 60.0
        
        # Calculate statistics
        age_stats = calculate_age_statistics(approved_df)
        sex_stats = calculate_sex_distribution(approved_df)
        duration_stats = calculate_session_duration_statistics(approved_df)
        
        # Centralize creation of complete_demographics column
        completeness_stats, complete_both_series = validate_data_completeness(approved_df)
        approved_df['complete_demographics'] = complete_both_series
        
        # Final sample size after all exclusions (e.g., complete demographics)
        final_sample_n = len(approved_df)
        exclusions_n = initial_total_n - approved_n
        
        # Create output tables
        summary_df = create_summary_statistics_table(
            approved_df, age_stats, sex_stats, duration_stats, completeness_stats
        )
        demographics_df = create_participant_demographics_table(approved_df)
        
        # Save output files
        save_output_files(summary_df, demographics_df)
        
        # Print final summary
        print("=" * 50)
        print("FINAL SUMMARY")
        print(f"Initial total participants: {initial_total_n}")
        print(f"Number of approved participants: {approved_n}")
        print(f"Number of exclusions (not approved): {exclusions_n}")
        print(f"Final sample size (approved): {final_sample_n}")
        print("=" * 50)
        print("Analysis completed successfully")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
