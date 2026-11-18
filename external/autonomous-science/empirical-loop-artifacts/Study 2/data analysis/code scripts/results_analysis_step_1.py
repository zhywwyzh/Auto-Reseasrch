import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import sys

def load_prolific_data(file_pattern):
    """
    Load Prolific export CSV files matching the specified pattern.
    
    Parameters:
    file_pattern (str): File pattern to match Prolific export files
    
    Returns:
    pd.DataFrame: Combined dataframe from all matching files
    """
    print(f"Looking for files matching pattern: {file_pattern}")
    
    # Find all files matching the pattern
    matching_files = glob.glob(file_pattern)
    print(f"Found {len(matching_files)} matching files: {matching_files}")
    
    if not matching_files:
        print("ERROR: No files found matching the pattern")
        return None
    
    # Get the most recent file based on creation time
    most_recent_file = max(matching_files, key=os.path.getctime)
    print(f"Using most recent file: {most_recent_file}")
    
    try:
        df = pd.read_csv(most_recent_file)
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        print(f"Successfully loaded data from {most_recent_file}")
        print(f"Data shape: {df.shape}")
        
        # Print all columns
        print("All columns in the dataset:")
        print(list(df.columns))
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        return df
    
    except Exception as e:
        print(f"ERROR: Failed to load file {most_recent_file}: {str(e)}")
        return None

def validate_required_columns(df, required_columns):
    """
    Validate that all required columns exist in the dataframe.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    required_columns (list): List of required column names
    
    Returns:
    bool: True if all required columns exist, False otherwise
    """
    print("Validating required columns...")
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        return False
    
    print("All required columns are present")
    return True

def filter_participants(df):
    """
    Filter participants based on status and completion criteria.
    
    Parameters:
    df (pd.DataFrame): Input dataframe with participant data
    
    Returns:
    pd.DataFrame: Filtered dataframe with only approved and completed participants,
                 and a dictionary with exclusion counts
    """
    print("Starting participant filtering...")
    initial_count = len(df)
    print(f"Initial number of rows: {initial_count}")
    
    exclusion_counts = {
        'initial_count': initial_count,
        'status_excluded': 0,
        'completion_excluded': 0,
        'age_excluded': 0
    }
    
    # Print unique values for Status column
    print(f"Unique values in Status column: {df['Status'].unique()}")
    
    # Filter for APPROVED status
    print("Filtering for APPROVED status...")
    approved_df = df[df['Status'] == 'APPROVED'].copy()
    status_excluded = initial_count - len(approved_df)
    exclusion_counts['status_excluded'] = status_excluded
    print(f"Participants with APPROVED status: {len(approved_df)} (excluded: {status_excluded})")
    
    # Filter for non-null "Completed at" values
    print("Filtering for non-null 'Completed at' values...")
    completed_df = approved_df[approved_df['Completed at'].notna()].copy()
    completion_excluded = len(approved_df) - len(completed_df)
    exclusion_counts['completion_excluded'] = completion_excluded
    print(f"Participants with non-null 'Completed at': {len(completed_df)} (excluded: {completion_excluded})")
    
    # Filter for age range 18-35
    print("Filtering for age range 18-35...")
    age_filter_count = len(completed_df)
    completed_df = completed_df[completed_df['Age'].between(18, 35, inclusive='both')].copy()
    age_excluded = age_filter_count - len(completed_df)
    exclusion_counts['age_excluded'] = age_excluded
    print(f"Participants after age range (18-35) filter: {len(completed_df)} (excluded: {age_excluded})")
    
    # Calculate total exclusions
    total_excluded = status_excluded + completion_excluded + age_excluded
    exclusion_counts['total_excluded'] = total_excluded
    
    print(f"Final filtered dataset shape: {completed_df.shape}")
    print(f"Total participants excluded: {total_excluded} ({(total_excluded/initial_count)*100:.1f}% of initial dataset)")
    
    # Print intermediate dataframe info
    print("\nFiltered dataframe columns:")
    print(list(completed_df.columns))
    print("\nFirst 2 rows of filtered data:")
    print(completed_df.head(2))
    
    return completed_df, exclusion_counts

def validate_participant_data(df):
    """
    Perform data validation checks on participant data.
    
    Parameters:
    df (pd.DataFrame): Filtered participant dataframe
    
    Returns:
    dict: Dictionary containing validation results
    """
    print("Performing data validation checks...")
    validation_results = {}
    
    # Check for duplicate Participant id values
    duplicate_ids = df['Participant id'].duplicated().sum()
    validation_results['duplicate_ids'] = duplicate_ids
    print(f"Number of duplicate Participant IDs: {duplicate_ids}")
    
    if duplicate_ids > 0:
        print("WARNING: Duplicate participant IDs found!")
    
    # Check for missing values in demographic variables
    missing_age = df['Age'].isna().sum()
    missing_sex = df['Sex'].isna().sum()
    missing_participant_id = df['Participant id'].isna().sum()
    
    validation_results['missing_age'] = missing_age
    validation_results['missing_sex'] = missing_sex
    validation_results['missing_participant_id'] = missing_participant_id
    
    print(f"Missing Age values: {missing_age}")
    print(f"Missing Sex values: {missing_sex}")
    print(f"Missing Participant ID values: {missing_participant_id}")
    
    # Print unique values for Sex column
    print(f"Unique values in Sex column: {df['Sex'].unique()}")
    
    # Validate age range (18-35)
    valid_ages = df['Age'].between(18, 35, inclusive='both')
    invalid_age_count = (~valid_ages).sum()
    validation_results['invalid_age_count'] = invalid_age_count
    
    print(f"Participants with ages outside 18-35 range: {invalid_age_count}")
    
    if invalid_age_count > 0:
        print("WARNING: Some participants have ages outside the 18-35 inclusion criteria!")
        print(f"Age range in data: {df['Age'].min()} - {df['Age'].max()}")
    
    return validation_results

def calculate_demographics(df):
    """
    Calculate demographic summary statistics.
    
    Parameters:
    df (pd.DataFrame): Participant dataframe
    
    Returns:
    dict: Dictionary containing demographic statistics
    """
    print("Calculating demographic summary statistics...")
    
    # Remove any rows with missing demographic data for calculations
    clean_df = df.dropna(subset=['Participant id', 'Age', 'Sex']).copy()
    print(f"Participants with complete demographic data: {len(clean_df)}")
    
    demographics = {}
    
    # Total number of participants (unique Participant id values)
    total_n = clean_df['Participant id'].nunique()
    demographics['total_n'] = total_n
    print(f"Total unique participants: {total_n}")
    
    # Age statistics
    age_mean = clean_df['Age'].mean()
    age_std = clean_df['Age'].std()
    age_min = clean_df['Age'].min()
    age_max = clean_df['Age'].max()
    
    demographics['mean_age'] = age_mean
    demographics['sd_age'] = age_std
    demographics['min_age'] = age_min
    demographics['max_age'] = age_max
    
    print(f"Age statistics - Mean: {age_mean:.2f}, SD: {age_std:.2f}, Min: {age_min}, Max: {age_max}")
    
    # Sex distribution
    sex_counts = clean_df['Sex'].value_counts()
    print(f"Sex distribution counts: {sex_counts.to_dict()}")
    
    # Initialize counts (in case some categories are missing)
    n_male = sex_counts.get('Male', 0)
    n_female = sex_counts.get('Female', 0)
    # Map non-Male/Female responses to Other
    n_other = sum(count for category, count in sex_counts.items() if category not in ['Male', 'Female'])
    
    demographics['n_male'] = n_male
    demographics['n_female'] = n_female
    demographics['n_other'] = n_other
    
    # Calculate percentages
    percent_male = (n_male / total_n) * 100 if total_n > 0 else 0
    percent_female = (n_female / total_n) * 100 if total_n > 0 else 0
    percent_other = (n_other / total_n) * 100 if total_n > 0 else 0
    
    demographics['percent_male'] = percent_male
    demographics['percent_female'] = percent_female
    demographics['percent_other'] = percent_other
    
    # Print the actual counts and percentages for verification
    print(f"Sex distribution counts - Male: {n_male}, Female: {n_female}, Other: {n_other}")
    print(f"Sex distribution percentages - Male: {percent_male:.1f}%, Female: {percent_female:.1f}%, Other: {percent_other:.1f}%")
    
    return demographics

def create_summary_table(demographics):
    """
    Create anonymized summary table in long format.
    
    Parameters:
    demographics (dict): Dictionary containing demographic statistics
    
    Returns:
    pd.DataFrame: Summary table with metric_name, value, and description columns
    """
    print("Creating summary statistics table...")
    
    # Define the summary statistics in the required format
    summary_data = [
        {'metric_name': 'total_n', 'value': demographics['total_n'], 'description': 'Total number of participants'},
        {'metric_name': 'mean_age', 'value': round(demographics['mean_age'], 2), 'description': 'Mean age of participants'},
        {'metric_name': 'sd_age', 'value': round(demographics['sd_age'], 2), 'description': 'Standard deviation of age'},
        {'metric_name': 'min_age', 'value': demographics['min_age'], 'description': 'Minimum age of participants'},
        {'metric_name': 'max_age', 'value': demographics['max_age'], 'description': 'Maximum age of participants'},
        {'metric_name': 'n_male', 'value': demographics['n_male'], 'description': 'Number of male participants'},
        {'metric_name': 'n_female', 'value': demographics['n_female'], 'description': 'Number of female participants'},
        {'metric_name': 'n_other', 'value': demographics['n_other'], 'description': 'Number of participants with other gender'},
        {'metric_name': 'percent_male', 'value': round(demographics['percent_male'], 1), 'description': 'Percentage of male participants'},
        {'metric_name': 'percent_female', 'value': round(demographics['percent_female'], 1), 'description': 'Percentage of female participants'},
        {'metric_name': 'percent_other', 'value': round(demographics['percent_other'], 1), 'description': 'Percentage of participants with other gender'}
    ]
    
    summary_df = pd.DataFrame(summary_data)
    
    print("Summary table created:")
    print("All columns in summary table:")
    print(list(summary_df.columns))
    print("\nFirst 2 rows of summary table:")
    print(summary_df.head(2))
    
    return summary_df

def save_output(summary_df, output_dir='outputs'):
    """
    Save the summary table to CSV file with timestamp.
    
    Parameters:
    summary_df (pd.DataFrame): Summary statistics dataframe
    output_dir (str): Output directory path
    
    Returns:
    str: Path to saved file
    """
    print(f"Saving output to {output_dir} directory...")
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created {output_dir} directory")
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
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
        required_columns = ['Participant id', 'Age', 'Sex', 'Status', 'Completed at']
        
        # Load data
        file_pattern = "raw_data/prolific_export_*.csv"
        df = load_prolific_data(file_pattern)
        
        if df is None:
            print("ERROR: Failed to load data")
            return 1
        
        # Validate required columns
        if not validate_required_columns(df, required_columns):
            print("ERROR: Required columns missing")
            return 1
        
        # Filter participants
        filtered_df, exclusion_counts = filter_participants(df)
        
        if len(filtered_df) == 0:
            print("ERROR: No participants remaining after filtering")
            return 1
        
        # Validate data
        validation_results = validate_participant_data(filtered_df)
        
        # Calculate demographics
        demographics = calculate_demographics(filtered_df)
        
        # Create summary table
        summary_df = create_summary_table(demographics)
        
        # Save output
        output_path = save_output(summary_df)
        
        print(f"\nFinal summary statistics:")
        print(summary_df.to_string(index=False))
        
        print("\nValidation summary:")
        for key, value in validation_results.items():
            print(f"{key}: {value}")
        
        print("\nExclusion Documentation:")
        print(f"Initial data loaded: {exclusion_counts['initial_count']} participants")
        print(f"Participants excluded due to status: {exclusion_counts['status_excluded']}")
        print(f"Participants excluded due to incomplete data: {exclusion_counts['completion_excluded']}")
        print(f"Participants excluded due to age criteria: {exclusion_counts['age_excluded']}")
        print(f"Total participants excluded: {exclusion_counts['total_excluded']}")
        print(f"Final dataset: {len(filtered_df)} participants after filtering")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
