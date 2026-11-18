import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def load_and_validate_data(file_pattern):
    """
    Load CSV files matching the pattern and validate required columns.
    
    Parameters:
    file_pattern (str): Pattern to match input CSV files
    
    Returns:
    pd.DataFrame: Combined dataframe from all matching files
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    # Find all files matching the pattern
    matching_files = glob.glob(file_pattern)
    print(f"Found {len(matching_files)} matching files: {matching_files}")
    
    if not matching_files:
        print("No matching files found!")
        return None
    
    # If pattern contains timestamp placeholder, get the most recent file
    if '<TIMESTAMP>' in file_pattern:
        # Sort by modification time and get the most recent
        matching_files.sort(key=os.path.getmtime, reverse=True)
        files_to_process = [matching_files[0]]
        print(f"Using most recent file: {files_to_process[0]}")
    else:
        # Use all matching files
        files_to_process = matching_files
        print(f"Processing all {len(files_to_process)} files")
    
    combined_data = []
    
    for file_path in files_to_process:
        print(f"\nProcessing file: {file_path}")
        
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded {len(df)} rows from {file_path}")
            
            # Print all columns
            print("All columns in file:")
            print(df.columns.tolist())
            
            # Print first 3 rows
            print("First 3 rows:")
            print(df.head(3))
            
            combined_data.append(df)
            
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            continue
    
    if not combined_data:
        print("No valid data files could be loaded!")
        return None
    
    # Combine all dataframes
    final_df = pd.concat(combined_data, ignore_index=True)
    print(f"\nCombined dataset has {len(final_df)} total rows")
    
    return final_df

def standardize_column_names(df):
    """
    Standardize column names to match expected format.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Dataframe with standardized column names
    """
    print("\nStandardizing column names...")
    
    # Create mapping for common variations
    column_mapping = {}
    
    for col in df.columns:
        col_stripped = col.strip()
        col_lower = col_stripped.lower()
        
        if col_stripped == 'Participant id':
            column_mapping[col] = 'participant_id'
        elif col_stripped == 'Time taken':
            column_mapping[col] = 'time_taken'
        elif col_lower == 'status':
            column_mapping[col] = 'status'
        elif col_lower == 'age':
            column_mapping[col] = 'age'
        elif col_lower == 'sex' or col_lower == 'gender':
            column_mapping[col] = 'sex'
    
    print(f"Column mapping: {column_mapping}")
    
    # Rename columns
    df_renamed = df.rename(columns=column_mapping)
    
    return df_renamed

def validate_required_columns(df):
    """
    Validate that all required columns are present.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    bool: True if all required columns present, False otherwise
    """
    required_columns = ['participant_id', 'age', 'sex', 'time_taken', 'status']
    
    print(f"\nValidating required columns: {required_columns}")
    print(f"Available columns: {df.columns.tolist()}")
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Missing required columns: {missing_columns}")
        return False
    
    print("All required columns are present!")
    return True

def print_unique_values(df):
    """
    Print unique values for key experimental design parameters.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    """
    print("\n=== UNIQUE VALUES FOR KEY COLUMNS ===")
    
    # Status column
    if 'status' in df.columns:
        print(f"Unique values in 'status' column: {df['status'].unique()}")
    
    # Sex column
    if 'sex' in df.columns:
        print(f"Unique values in 'sex' column: {df['sex'].unique()}")
    
    # For measured variables, just print data type
    if 'age' in df.columns:
        print(f"'age' column data type: {df['age'].dtype}")
    
    if 'time_taken' in df.columns:
        print(f"'time_taken' column data type: {df['time_taken'].dtype}")

def filter_completed_participants(df):
    """
    Filter for completed participants with valid data.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Filtered dataframe
    dict: Exclusion counts
    """
    print("\n=== FILTERING COMPLETED PARTICIPANTS ===")
    
    initial_count = len(df)
    print(f"Initial participant count: {initial_count}")
    
    exclusion_counts = {
        'initial_count': initial_count,
        'non_approved_status': 0,
        'missing_age': 0,
        'missing_sex': 0,
        'final_count': 0
    }
    
    # Filter for approved status
    print(f"\nFiltering for approved status...")
    approved_statuses = ['APPROVED', 'approved', 'COMPLETED', 'completed', 'FINISHED', 'finished']
    
    # Check which approved statuses exist in the data
    existing_approved = [status for status in approved_statuses if status in df['status'].unique()]
    print(f"Found these approved statuses in data: {existing_approved}")
    
    if existing_approved:
        df_approved = df[df['status'].isin(existing_approved)]
    else:
        # If no standard approved status found, assume all are approved for now
        print("No standard approved status found - including all participants")
        df_approved = df.copy()
    
    exclusion_counts['non_approved_status'] = initial_count - len(df_approved)
    print(f"Excluded {exclusion_counts['non_approved_status']} participants for non-approved status")
    print(f"Remaining participants: {len(df_approved)}")
    
    # Remove participants with missing age data
    print(f"\nFiltering for valid age data...")
    before_age_filter = len(df_approved)
    df_age_valid = df_approved.dropna(subset=['age'])
    exclusion_counts['missing_age'] = before_age_filter - len(df_age_valid)
    print(f"Excluded {exclusion_counts['missing_age']} participants for missing age")
    print(f"Remaining participants: {len(df_age_valid)}")
    
    # Remove participants with missing sex data
    print(f"\nFiltering for valid sex data...")
    before_sex_filter = len(df_age_valid)
    df_sex_valid = df_age_valid.dropna(subset=['sex'])
    exclusion_counts['missing_sex'] = before_sex_filter - len(df_sex_valid)
    print(f"Excluded {exclusion_counts['missing_sex']} participants for missing sex")
    print(f"Remaining participants: {len(df_sex_valid)}")
    
    exclusion_counts['final_count'] = len(df_sex_valid)
    
    print(f"\n=== EXCLUSION SUMMARY ===")
    for key, value in exclusion_counts.items():
        print(f"{key}: {value}")
    
    return df_sex_valid, exclusion_counts

def calculate_sample_characteristics(df):
    """
    Calculate sample characteristics including demographics and session duration.
    
    Parameters:
    df (pd.DataFrame): Filtered dataframe
    
    Returns:
    dict: Dictionary containing all calculated statistics
    """
    print("\n=== CALCULATING SAMPLE CHARACTERISTICS ===")
    
    statistics = {}
    
    # Total sample size
    statistics['total_sample_size'] = len(df)
    print(f"Total sample size: {statistics['total_sample_size']}")
    
    # Age distribution
    print(f"\nCalculating age distribution...")
    statistics['age_mean'] = df['age'].mean()
    statistics['age_std'] = df['age'].std()
    statistics['age_min'] = df['age'].min()
    statistics['age_max'] = df['age'].max()
    
    print(f"Age - Mean: {statistics['age_mean']:.2f}")
    print(f"Age - SD: {statistics['age_std']:.2f}")
    print(f"Age - Range: {statistics['age_min']} to {statistics['age_max']}")
    
    # Sex distribution
    print(f"\nCalculating sex distribution...")
    sex_counts = df['sex'].value_counts()
    total_participants = len(df)
    
    for sex_category in sex_counts.index:
        count = sex_counts[sex_category]
        percentage = (count / total_participants) * 100
        statistics[f'sex_{sex_category.lower()}_count'] = count
        statistics[f'sex_{sex_category.lower()}_percentage'] = percentage
        print(f"Sex - {sex_category}: {count} ({percentage:.1f}%)")
    
    # Session duration statistics
    print(f"\nCalculating session duration statistics...")
    
    # Convert time_taken to minutes if needed (assuming it might be in seconds)
    time_taken = df['time_taken'].copy()
    
    # Check if time values seem to be in seconds (if mean > 300, likely seconds)
    if time_taken.mean() > 300:
        print("Time values appear to be in seconds, converting to minutes")
        time_taken_minutes = time_taken / 60
    else:
        print("Time values appear to be in minutes")
        time_taken_minutes = time_taken
    
    statistics['time_mean_minutes'] = time_taken_minutes.mean()
    statistics['time_std_minutes'] = time_taken_minutes.std()
    statistics['time_min_minutes'] = time_taken_minutes.min()
    statistics['time_max_minutes'] = time_taken_minutes.max()
    
    print(f"Completion time - Mean: {statistics['time_mean_minutes']:.2f} minutes")
    print(f"Completion time - SD: {statistics['time_std_minutes']:.2f} minutes")
    print(f"Completion time - Range: {statistics['time_min_minutes']:.2f} to {statistics['time_max_minutes']:.2f} minutes")
    
    return statistics, time_taken_minutes

def validate_demographic_data(df, time_taken_minutes):
    """
    Validate demographic data for unrealistic values.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    time_taken_minutes (pd.Series): Time taken in minutes
    
    Returns:
    dict: Data quality issues
    """
    print("\n=== VALIDATING DEMOGRAPHIC DATA ===")
    
    quality_issues = {}
    
    # Check for unrealistic age values
    unrealistic_ages = df[(df['age'] < 18) | (df['age'] > 80)]
    quality_issues['unrealistic_ages_count'] = len(unrealistic_ages)
    quality_issues['unrealistic_ages_ids'] = unrealistic_ages['participant_id'].tolist()
    
    print(f"Participants with unrealistic ages (<18 or >80): {quality_issues['unrealistic_ages_count']}")
    if quality_issues['unrealistic_ages_count'] > 0:
        print(f"Unrealistic age participant IDs: {quality_issues['unrealistic_ages_ids']}")
    
    # Check for unusual completion times
    unusual_times = df[(time_taken_minutes < 20) | (time_taken_minutes > 120)]
    quality_issues['unusual_times_count'] = len(unusual_times)
    quality_issues['unusual_times_ids'] = unusual_times['participant_id'].tolist()
    
    print(f"Participants with unusual completion times (<20 or >120 minutes): {quality_issues['unusual_times_count']}")
    if quality_issues['unusual_times_count'] > 0:
        print(f"Unusual completion time participant IDs: {quality_issues['unusual_times_ids']}")
    
    return quality_issues

def create_demographic_summary(df, time_taken_minutes, quality_issues):
    """
    Create demographic summary dataframe.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    time_taken_minutes (pd.Series): Time taken in minutes
    quality_issues (dict): Data quality issues
    
    Returns:
    pd.DataFrame: Demographic summary dataframe
    """
    print("\n=== CREATING DEMOGRAPHIC SUMMARY ===")
    
    summary_df = df[['participant_id', 'age', 'sex']].copy()
    summary_df['time_taken_minutes'] = time_taken_minutes
    summary_df['included_in_analysis'] = True

    # Mark participants with quality issues
    unrealistic_age_mask = (df['age'] < 18) | (df['age'] > 80)
    unusual_time_mask = (time_taken_minutes < 20) | (time_taken_minutes > 120)

    # Initialize exclusion_reason as empty string
    summary_df['exclusion_reason'] = ''

    # Append reasons to avoid overwriting
    summary_df.loc[unrealistic_age_mask, 'exclusion_reason'] += 'unrealistic_age;'
    summary_df.loc[unusual_time_mask, 'exclusion_reason'] += 'unusual_completion_time;'

    # Clean up exclusion_reason column
    summary_df['exclusion_reason'] = summary_df['exclusion_reason'].str.rstrip(';').replace('', None)

    # Mark participants with quality issues as excluded from analysis
    summary_df.loc[unrealistic_age_mask | unusual_time_mask, 'included_in_analysis'] = False

    print(f"Created demographic summary with {len(summary_df)} participants")
    print("Demographic summary columns:")
    print(summary_df.columns.tolist())
    print("First 2 rows of demographic summary:")
    print(summary_df.head(2))
    
    return summary_df

def create_statistics_summary(statistics, exclusion_counts, quality_issues):
    """
    Create statistics summary dataframe.
    
    Parameters:
    statistics (dict): Calculated statistics
    exclusion_counts (dict): Exclusion counts
    quality_issues (dict): Data quality issues
    
    Returns:
    pd.DataFrame: Statistics summary dataframe
    """
    print("\n=== CREATING STATISTICS SUMMARY ===")
    
    stats_data = []
    
    # Sample size statistics
    stats_data.append({
        'statistic_name': 'total_sample_size',
        'value': statistics['total_sample_size'],
        'description': 'Total number of completed participants'
    })
    
    # Age statistics
    stats_data.append({
        'statistic_name': 'age_mean',
        'value': round(statistics['age_mean'], 2),
        'description': 'Mean age of participants'
    })
    
    stats_data.append({
        'statistic_name': 'age_std',
        'value': round(statistics['age_std'], 2),
        'description': 'Standard deviation of age'
    })
    
    stats_data.append({
        'statistic_name': 'age_range_min',
        'value': statistics['age_min'],
        'description': 'Minimum age in sample'
    })
    
    stats_data.append({
        'statistic_name': 'age_range_max',
        'value': statistics['age_max'],
        'description': 'Maximum age in sample'
    })
    
    # Sex distribution statistics
    for key, value in statistics.items():
        if key.startswith('sex_') and key.endswith('_count'):
            sex_category = key.replace('sex_', '').replace('_count', '')
            stats_data.append({
                'statistic_name': f'sex_{sex_category}_count',
                'value': value,
                'description': f'Count of {sex_category} participants'
            })
            
            # Add percentage
            percentage_key = f'sex_{sex_category}_percentage'
            if percentage_key in statistics:
                stats_data.append({
                    'statistic_name': percentage_key,
                    'value': round(statistics[percentage_key], 1),
                    'description': f'Percentage of {sex_category} participants'
                })
    
    # Time statistics
    stats_data.append({
        'statistic_name': 'completion_time_mean_minutes',
        'value': round(statistics['time_mean_minutes'], 2),
        'description': 'Mean completion time in minutes'
    })
    
    stats_data.append({
        'statistic_name': 'completion_time_std_minutes',
        'value': round(statistics['time_std_minutes'], 2),
        'description': 'Standard deviation of completion time in minutes'
    })
    
    stats_data.append({
        'statistic_name': 'completion_time_range_min_minutes',
        'value': round(statistics['time_min_minutes'], 2),
        'description': 'Minimum completion time in minutes'
    })
    
    stats_data.append({
        'statistic_name': 'completion_time_range_max_minutes',
        'value': round(statistics['time_max_minutes'], 2),
        'description': 'Maximum completion time in minutes'
    })
    
    # Exclusion statistics
    for key, value in exclusion_counts.items():
        stats_data.append({
            'statistic_name': f'exclusion_{key}',
            'value': value,
            'description': f'Exclusion count: {key}'
        })
    
    # Quality issue statistics
    for key, value in quality_issues.items():
        if key.endswith('_count'):
            stats_data.append({
                'statistic_name': f'quality_issue_{key}',
                'value': value,
                'description': f'Quality issue count: {key}'
            })
    
    stats_df = pd.DataFrame(stats_data)
    
    print(f"Created statistics summary with {len(stats_df)} statistics")
    print("Statistics summary columns:")
    print(stats_df.columns.tolist())
    print("First 2 rows of statistics summary:")
    print(stats_df.head(2))
    
    return stats_df

def save_outputs(stats_df, demographic_df):
    """
    Save output files with timestamps.
    
    Parameters:
    stats_df (pd.DataFrame): Statistics summary dataframe
    demographic_df (pd.DataFrame): Demographic summary dataframe
    """
    print("\n=== SAVING OUTPUT FILES ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save statistics summary
    stats_filename = f'outputs/sample_statistics_{timestamp}.csv'
    stats_df.to_csv(stats_filename, index=False)
    print(f"Saved statistics summary to: {stats_filename}")
    
    # Save demographic summary
    demographic_filename = f'outputs/demographic_summary_{timestamp}.csv'
    demographic_df.to_csv(demographic_filename, index=False)
    print(f"Saved demographic summary to: {demographic_filename}")

def main():
    """
    Main function to execute the demographic analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("=== STARTING DEMOGRAPHIC ANALYSIS ===")
        
        # Define input file pattern
        input_pattern = "../C_results/data/prolific_export_*.csv"
        
        # Load and validate data
        df = load_and_validate_data(input_pattern)
        if df is None:
            print("ERROR: No valid data could be loaded")
            return 1
        
        # Standardize column names
        df = standardize_column_names(df)

        # Validate required columns (AFTER standardization)
        if not validate_required_columns(df):
            print("ERROR: Missing required columns")
            return 1
        
        # Print unique values for key columns
        print_unique_values(df)
        
        # Filter completed participants
        df_filtered, exclusion_counts = filter_completed_participants(df)
        
        if len(df_filtered) == 0:
            print("ERROR: No participants remaining after filtering")
            return 1
        
        # Calculate sample characteristics
        statistics, time_taken_minutes = calculate_sample_characteristics(df_filtered)
        
        # Validate demographic data
        quality_issues = validate_demographic_data(df_filtered, time_taken_minutes)
        
        # Create output dataframes
        demographic_summary = create_demographic_summary(df_filtered, time_taken_minutes, quality_issues)
        statistics_summary = create_statistics_summary(statistics, exclusion_counts, quality_issues)
        
        # Save outputs
        save_outputs(statistics_summary, demographic_summary)

        # Print final exclusion summary
        print("\n=== FINAL EXCLUSION REPORT ===")
        initial_n = exclusion_counts['initial_count']
        final_n = exclusion_counts['final_count']
        removed_status = exclusion_counts['non_approved_status']
        removed_missing = exclusion_counts['missing_age'] + exclusion_counts['missing_sex']
        print(f"Data found for {initial_n} participants")
        print(f"{removed_status} participants were removed due to non-approved status.")
        print(f"{removed_missing} participants had incomplete data and were removed.")
        print(f"Final dataset: {final_n} participants")
        
        print("\n=== ANALYSIS COMPLETE ===")
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
