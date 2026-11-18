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
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    return max(files, key=os.path.getmtime)

def load_exclusion_data():
    """
    Load participant exclusion status data from the most recent file.
    
    Returns:
    pd.DataFrame: DataFrame containing exclusion status data
    """
    print("Loading participant exclusion status data...")
    
    # Find the most recent exclusion status file
    pattern = "outputs/participant_exclusion_status_*.csv"
    exclusion_file = find_most_recent_file(pattern)
    
    if not exclusion_file:
        print(f"ERROR: No exclusion status file found matching pattern: {pattern}")
        return None
        
    print(f"Found exclusion status file: {exclusion_file}")
    
    try:
        df = pd.read_csv(exclusion_file)
        df.columns = df.columns.str.strip()
        print(f"Loaded exclusion data with shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print("First 3 rows:")
        print(df.head(3))
        
        # Verify required columns exist
        required_cols = ['participantId', 'prolific_participant_id', 'included']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"ERROR: Missing required columns: {missing_cols}")
            return None
            
        return df
        
    except Exception as e:
        print(f"ERROR loading exclusion data: {e}")
        return None

def load_prolific_data():
    """
    Load Prolific export data from all matching files.
    
    Returns:
    pd.DataFrame: Combined DataFrame containing all Prolific export data
    """
    print("\nLoading Prolific export data...")
    
    # Find all Prolific export files
    pattern = "../C_results/data/prolific_export_*.csv"
    prolific_files = glob.glob(pattern)
    
    if not prolific_files:
        print(f"ERROR: No Prolific export files found matching pattern: {pattern}")
        return None
        
    print(f"Found {len(prolific_files)} Prolific export files:")
    for file in prolific_files:
        print(f"  - {file}")
    
    all_prolific_data = []
    
    for file in prolific_files:
        try:
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            print(f"\nLoaded {file} with shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            
            # Verify required columns exist
            required_cols = ['Participant id', 'Age', 'Sex', 'Time taken']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"WARNING: Missing required columns in {file}: {missing_cols}")
                continue
                
            all_prolific_data.append(df)
            
        except Exception as e:
            print(f"ERROR loading {file}: {e}")
            continue
    
    if not all_prolific_data:
        print("ERROR: No valid Prolific data files could be loaded")
        return None
        
    # Combine all Prolific data
    combined_df = pd.concat(all_prolific_data, ignore_index=True)
    print(f"\nCombined Prolific data shape: {combined_df.shape}")
    
    return combined_df

def filter_included_participants(exclusion_df):
    """
    Filter to only included participants.
    
    Parameters:
    exclusion_df (pd.DataFrame): DataFrame with exclusion status
    
    Returns:
    pd.DataFrame: DataFrame with only included participants
    """
    print("\nFiltering to included participants...")
    
    print(f"Unique values in 'included' column: {exclusion_df['included'].unique()}")
    
    # Filter to included participants only
    included_df = exclusion_df[exclusion_df['included'] == True].copy()
    
    print(f"Total participants: {len(exclusion_df)}")
    print(f"Included participants: {len(included_df)}")
    print(f"Excluded participants: {len(exclusion_df) - len(included_df)}")
    
    return included_df

def merge_demographic_data(included_df, prolific_df):
    """
    Merge included participants with their Prolific demographic data.
    
    Parameters:
    included_df (pd.DataFrame): DataFrame with included participants
    prolific_df (pd.DataFrame): DataFrame with Prolific demographic data
    
    Returns:
    pd.DataFrame: Merged DataFrame with demographic information
    """
    print("\nMerging demographic data...")
    
    # Merge on prolific participant ID
    merged_df = included_df.merge(
        prolific_df,
        left_on='prolific_participant_id',
        right_on='Participant id',
        how='left'
    )
    
    print(f"Participants with demographic data: {len(merged_df.dropna(subset=['Age']))}")
    print(f"Participants missing demographic data: {len(merged_df[merged_df['Age'].isna()])}")
    
    # Check for missing demographic data
    missing_demo = merged_df[merged_df['Age'].isna()]
    if len(missing_demo) > 0:
        print("Participants missing demographic data:")
        print(missing_demo[['participantId', 'prolific_participant_id']])
    
    # Remove participants without demographic data
    merged_df = merged_df.dropna(subset=['Age', 'Sex', 'Time taken'])
    
    print(f"Final sample size with complete demographic data: {len(merged_df)}")
    
    return merged_df

def calculate_demographics(merged_df):
    """
    Calculate demographic statistics and distributions.
    
    Parameters:
    merged_df (pd.DataFrame): DataFrame with merged demographic data
    
    Returns:
    dict: Dictionary containing demographic statistics
    """
    print("\nCalculating demographic statistics...")
    
    stats = {}
    
    # Sample size
    stats['sample_size'] = len(merged_df)
    print(f"Total sample size: {stats['sample_size']}")
    
    # Age statistics
    ages = merged_df['Age'].astype(float)
    stats['age_mean'] = ages.mean()
    stats['age_std'] = ages.std()
    stats['age_min'] = ages.min()
    stats['age_max'] = ages.max()
    
    print(f"Age - Mean: {stats['age_mean']:.2f}, SD: {stats['age_std']:.2f}")
    print(f"Age - Range: {stats['age_min']:.0f} to {stats['age_max']:.0f}")
    
    # Age distribution bins
    age_bins = [18, 26, 31, 36, np.inf]  # 18-25, 26-30, 31-35, 36+
    age_labels = ['18-25', '26-30', '31-35', '36+']
    age_groups = pd.cut(ages, bins=age_bins, labels=age_labels, right=False, include_lowest=True)
    merged_df['age_group'] = pd.Categorical(age_groups, categories=age_labels, ordered=True)
    
    age_dist = merged_df['age_group'].value_counts().sort_index()
    print("Age distribution:")
    for group, count in age_dist.items():
        pct = (count / len(merged_df)) * 100
        stats[f'age_group_{group}'] = count
        stats[f'age_group_{group}_pct'] = pct
        print(f"  {group}: {count} ({pct:.1f}%)")
    
    # Sex distribution
    print(f"Unique values in 'Sex' column: {merged_df['Sex'].unique()}")
    sex_dist = merged_df['Sex'].value_counts()
    print("Sex distribution:")
    for sex, count in sex_dist.items():
        pct = (count / len(merged_df)) * 100
        stats[f'sex_{sex}'] = count
        stats[f'sex_{sex}_pct'] = pct
        print(f"  {sex}: {count} ({pct:.1f}%)")
    
    # Session duration (convert from seconds to minutes)
    duration_seconds = merged_df['Time taken'].astype(float)
    duration_minutes = duration_seconds / 60
    
    stats['duration_mean_minutes'] = duration_minutes.mean()
    stats['duration_std_minutes'] = duration_minutes.std()
    stats['duration_min_minutes'] = duration_minutes.min()
    stats['duration_max_minutes'] = duration_minutes.max()
    
    print(f"Session duration - Mean: {stats['duration_mean_minutes']:.2f} min, SD: {stats['duration_std_minutes']:.2f} min")
    print(f"Session duration - Range: {stats['duration_min_minutes']:.2f} to {stats['duration_max_minutes']:.2f} min")
    
    # Add session duration in minutes to the dataframe
    merged_df['session_duration_minutes'] = duration_minutes
    
    # Verify recruitment targets (adults aged 18-35)
    target_age_participants = merged_df[(merged_df['Age'] >= 18) & (merged_df['Age'] <= 35)]
    stats['target_age_count'] = len(target_age_participants)
    stats['target_age_pct'] = (len(target_age_participants) / len(merged_df)) * 100
    
    print(f"Participants meeting recruitment target (18-35 years): {stats['target_age_count']} ({stats['target_age_pct']:.1f}%)")
    
    return stats, merged_df

def create_output_files(merged_df, stats):
    """
    Create output CSV files with demographic data and statistics.
    
    Parameters:
    merged_df (pd.DataFrame): DataFrame with merged demographic data
    stats (dict): Dictionary containing demographic statistics
    """
    print("\nCreating output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create sample demographics file
    demographics_file = f"outputs/sample_demographics_{timestamp}.csv"
    demographics_output = merged_df[[
        'participantId',
        'prolific_participant_id', 
        'Age',
        'Sex',
        'session_duration_minutes'
    ]].copy()
    
    # Rename columns to match required output format
    demographics_output.columns = [
        'participantId',
        'prolific_participant_id',
        'age',
        'sex', 
        'session_duration_minutes'
    ]
    
    demographics_output.to_csv(demographics_file, index=False)
    print(f"Saved demographics data to: {demographics_file}")
    print(f"Demographics output shape: {demographics_output.shape}")
    print("Demographics output columns:", list(demographics_output.columns))
    print("First 2 rows of demographics output:")
    print(demographics_output.head(2))
    
    # Create sample statistics file
    statistics_file = f"outputs/sample_statistics_{timestamp}.csv"
    stats_data = []
    
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            stats_data.append({
                'statistic_name': key,
                'value': value,
                'additional_info': ''
            })
    
    stats_df = pd.DataFrame(stats_data)
    stats_df.to_csv(statistics_file, index=False)
    print(f"\nSaved statistics data to: {statistics_file}")
    print(f"Statistics output shape: {stats_df.shape}")
    print("Statistics output columns:", list(stats_df.columns))
    print("First 2 rows of statistics output:")
    print(stats_df.head(2))

def perform_data_validation(merged_df):
    """
    Perform data validation checks on the merged demographic data.
    
    Parameters:
    merged_df (pd.DataFrame): DataFrame with merged demographic data
    """
    print("\nPerforming data validation checks...")
    
    # Check for demographic outliers
    ages = merged_df['Age'].astype(float)
    duration_minutes = merged_df['session_duration_minutes']
    
    # Age outliers (outside reasonable range)
    age_outliers = merged_df[(ages < 18) | (ages > 80)]
    if len(age_outliers) > 0:
        print(f"WARNING: Found {len(age_outliers)} age outliers (< 18 or > 80 years)")
        print("Age outlier participant IDs:", age_outliers['participantId'].tolist())
    else:
        print("No age outliers detected")
    
    # Duration outliers (extremely short or long sessions)
    duration_outliers = merged_df[(duration_minutes < 1) | (duration_minutes > 120)]
    if len(duration_outliers) > 0:
        print(f"WARNING: Found {len(duration_outliers)} duration outliers (< 1 or > 120 minutes)")
        print("Duration outlier participant IDs:", duration_outliers['participantId'].tolist())
    else:
        print("No duration outliers detected")
    
    # Check for missing or unusual sex values
    sex_values = merged_df['Sex'].value_counts()
    print("Sex value distribution:")
    for sex, count in sex_values.items():
        print(f"  '{sex}': {count}")
    
    # Check for any completely missing demographic data
    missing_any = merged_df[merged_df[['Age', 'Sex', 'Time taken']].isnull().any(axis=1)]
    if len(missing_any) > 0:
        print(f"WARNING: Found {len(missing_any)} participants with some missing demographic data")
    else:
        print("No missing demographic data detected")

def main():
    """
    Main function to execute the demographic analysis workflow.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting demographic analysis...")
        
        # Load exclusion status data
        exclusion_df = load_exclusion_data()
        if exclusion_df is None:
            return 1
        n_total = len(exclusion_df)
        
        # Load Prolific demographic data
        prolific_df = load_prolific_data()
        if prolific_df is None:
            return 1
        n_prolific = len(prolific_df)
        
        # Filter to included participants only
        included_df = filter_included_participants(exclusion_df)
        n_included = len(included_df)
        n_excluded = n_total - n_included
        n_included_true = included_df['included'].sum()
        n_included_false = (exclusion_df['included'] == False).sum()
        n_included_na = exclusion_df['included'].isna().sum()
        if n_included == 0:
            print("ERROR: No included participants found")
            return 1
        
        # Merge with demographic data
        merged_df = merge_demographic_data(included_df, prolific_df)
        n_merged = len(merged_df)
        if n_merged == 0:
            print("ERROR: No participants with demographic data found")
            return 1
        
        # Calculate demographic statistics
        stats, merged_df = calculate_demographics(merged_df)
        
        # Perform data validation
        perform_data_validation(merged_df)
        
        # Create output files
        create_output_files(merged_df, stats)
        
        # Final summary printout as per project requirements
        print("\n--- Data Processing Summary ---")
        print(f"1) Data found for {n_total} participants in the exclusion status file.")
        print(f"2) {n_total - n_included} participants were removed based on pre-calculated exclusion criteria.")
        print(f"3) {n_included - n_merged} participants were removed due to missing demographic data.")
        print(f"4) Final dataset: {n_merged} participants with complete demographic data.")

        print("\nDemographic analysis completed successfully")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
