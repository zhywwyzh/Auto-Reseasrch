#!/usr/bin/env python3
"""
VWM Data Binning for DoG Function Fitting

This script prepares VWM (Visual Working Memory) data for DoG (Difference of Gaussians) 
function fitting by binning angular differences and calculating mean errors per bin.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/VWM_cleaned_data_*.csv')
    
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

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
        print(f"ERROR: Missing required columns: {missing_columns}")
        return False
    return True

def wrap_angular_difference(angle):
    """
    Wrap angular difference to [-90, 90] range for orientation data.
    
    Parameters:
    -----------
    angle : float or array-like
        Angular difference in degrees
    
    Returns:
    --------
    float or array-like
        Wrapped angular difference in [-90, 90] range
    
    Notes:
    ------
    Edge cases:
    - Exactly 90 degrees: Remains 90 degrees
    - Exactly -90 degrees: Remains -90 degrees
    - Exactly 180 degrees: Wrapped to 0 degrees (equivalent orientation)
    - Exactly 270 degrees: Wrapped to 90 degrees
    - NaN values: Preserved as NaN
    - Infinite values: Handled by modulo operation, resulting in NaN
    
    The function first wraps to [-180, 180] range, then to [-90, 90] range
    to account for the orientation symmetry (e.g., 100° is equivalent to -80°
    in orientation space).
    """
    # Convert to numpy array for vectorized operations
    angle = np.array(angle)
    
    # Wrap to [-180, 180] first
    wrapped = ((angle + 180) % 360) - 180
    
    # For orientation data, wrap to [-90, 90]
    wrapped = np.where(wrapped > 90, wrapped - 180, wrapped)
    wrapped = np.where(wrapped < -90, wrapped + 180, wrapped)
    
    return wrapped

def create_angular_bins():
    """
    Create 15-degree angular difference bins.
    
    Returns:
    --------
    list of tuples
        List of (lower_bound, upper_bound, center) for each bin
    """
    bins = []
    for i in range(6):  # 6 bins: 0-15, 15-30, 30-45, 45-60, 60-75, 75-90
        lower = i * 15
        upper = (i + 1) * 15
        center = lower + 7.5
        bins.append((lower, upper, center))
    
    return bins

def assign_bin(abs_angular_diff, bins):
    """
    Assign angular difference to appropriate bin.
    
    Parameters:
    -----------
    abs_angular_diff : float
        Absolute angular difference in degrees
    bins : list of tuples
        List of (lower_bound, upper_bound, center) for each bin
    
    Returns:
    --------
    int or None
        Bin index (0-5) or None if doesn't fit in any bin
    
    Notes:
    ------
    Edge cases:
    - Exactly at bin boundary: Assigned to the higher bin (e.g., 15° goes to bin 1, not bin 0)
    - Exactly 90 degrees: Assigned to the last bin (bin 5: 75-90°)
    - Negative values: Should not occur as we use absolute differences
    - Values > 90: Should not occur after proper wrapping
    - NaN values: Will not match any bin condition, returns None
    
    The function uses half-open intervals [lower, upper) for all bins except
    the last one, which includes the upper boundary [75, 90] to ensure all
    valid angular differences are assigned to a bin.
    """
    for i, (lower, upper, center) in enumerate(bins):
        if lower <= abs_angular_diff < upper:
            return i
    
    # Handle edge case where abs_angular_diff == 90
    if abs_angular_diff == 90:
        return 5  # Last bin
    
    return None

def filter_and_prepare_data(df):
    """
    Filter data for DoG fitting preparation.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Input dataframe with VWM data
    
    Returns:
    --------
    pandas.DataFrame
        Filtered dataframe ready for binning
    """
    print("Starting data filtering...")
    print(f"Initial data shape: {df.shape}")
    initial_count = len(df)
    
    # Remove rows with null values in critical columns
    critical_columns = ['participantId', 'trial_type', 'VWM_setSize', 'VWM_delay_s', 
                       'VWM_error_degrees', 'angular_difference_current_previous', 'excluded_trial']
    
    print("Checking for null values in critical columns...")
    total_null_rows = 0
    for col in critical_columns:
        null_count = df[col].isnull().sum()
        print(f"  {col}: {null_count} null values")
        total_null_rows += null_count
    
    # Filter out rows with null values in critical columns
    df_clean = df.dropna(subset=critical_columns)
    null_removed_count = initial_count - len(df_clean)
    print(f"After removing null values: {df_clean.shape}")
    print(f"  Removed {null_removed_count} rows with null values ({null_removed_count/initial_count:.1%} of original data)")
    
    # Filter for test trials only
    practice_count = len(df_clean[df_clean['trial_type'] == 'practice'])
    df_test = df_clean[df_clean['trial_type'] == 'test']
    print(f"After filtering for test trials: {df_test.shape}")
    print(f"  Removed {practice_count} practice trials ({practice_count/len(df_clean):.1%} of clean data)")
    
    # Exclude trials marked as excluded
    excluded_count = len(df_test[df_test['excluded_trial'] == True])
    df_valid = df_test[df_test['excluded_trial'] == False]
    print(f"After excluding marked trials: {df_valid.shape}")
    print(f"  Removed {excluded_count} excluded trials ({excluded_count/len(df_test):.1%} of test trials)")
    
    # Filter for valid set sizes (2 or 4) only
    invalid_set_size_count = len(df_valid[~df_valid['VWM_setSize'].isin([2, 4])])
    df_valid = df_valid[df_valid['VWM_setSize'].isin([2, 4])]
    print(f"After filtering for valid set sizes (2, 4): {df_valid.shape}")
    print(f"  Removed {invalid_set_size_count} trials with invalid set sizes ({invalid_set_size_count/len(df_test[df_test['excluded_trial'] == False]):.1%} of non-excluded test trials)")
    
    # Filter for valid delays (1.0 or 4.0) only
    invalid_delay_count = len(df_valid[~df_valid['VWM_delay_s'].isin([1.0, 4.0])])
    df_valid = df_valid[df_valid['VWM_delay_s'].isin([1.0, 4.0])]
    print(f"After filtering for valid delays (1.0, 4.0): {df_valid.shape}")
    print(f"  Removed {invalid_delay_count} trials with invalid delays ({invalid_delay_count/(len(df_test[df_test['excluded_trial'] == False]) - invalid_set_size_count):.1%} of remaining trials)")
    
    # Summary of filtering
    total_removed = initial_count - len(df_valid)
    print(f"\nFiltering summary:")
    print(f"  Initial trial count: {initial_count}")
    print(f"  Final trial count: {len(df_valid)}")
    print(f"  Total removed: {total_removed} ({total_removed/initial_count:.1%} of original data)")
    
    return df_valid

def bin_data_for_participant_condition(group_data, bins):
    """
    Bin data for a specific participant-condition combination.
    
    Parameters:
    -----------
    group_data : pandas.DataFrame
        Data for one participant-condition combination
    bins : list of tuples
        List of (lower_bound, upper_bound, center) for each bin
    
    Returns:
    --------
    tuple
        (list of dicts with bin results, original bin count, original adequate bin count)
    """
    results = []
    
    # Get absolute angular differences
    abs_angular_diffs = np.abs(group_data['angular_difference_current_previous'])
    
    # Assign each trial to a bin
    bin_assignments = []
    for diff in abs_angular_diffs:
        bin_idx = assign_bin(diff, bins)
        bin_assignments.append(bin_idx)
    
    group_data = group_data.copy()
    group_data['bin_idx'] = bin_assignments
    
    # Process each bin
    for bin_idx, (lower, upper, center) in enumerate(bins):
        bin_data = group_data[group_data['bin_idx'] == bin_idx]
        
        if len(bin_data) > 0:
            mean_error = bin_data['VWM_error_degrees'].mean()
            n_trials = len(bin_data)
            bin_adequate = n_trials >= 3
        else:
            mean_error = np.nan
            n_trials = 0
            bin_adequate = False
        
        result = {
            'bin_center_degrees': center,
            'bin_lower_bound': lower,
            'bin_upper_bound': upper,
            'mean_error_degrees': mean_error,
            'n_trials_in_bin': n_trials,
            'bin_adequate': bin_adequate
        }
        
        results.append(result)
    
    # Store original bin statistics before merging
    bins_before_merging = len(results)
    adequate_bins_before_merging = sum(1 for r in results if r['bin_adequate'])
    
    # Merge inadequate bins with adjacent bins
    print("  Checking for inadequate bins that need merging...")
    merged_results = []
    i = 0
    merge_count = 0
    inadequate_before = sum(1 for r in results if not r['bin_adequate'])
    empty_bins = sum(1 for r in results if r['n_trials_in_bin'] == 0)
    
    print(f"    Before merging: {inadequate_before} inadequate bins, {empty_bins} empty bins")
    
    while i < len(results):
        current_bin = results[i]
        
        # If bin is adequate or it's the last bin, add it to merged results
        if current_bin['bin_adequate'] or i == len(results) - 1:
            merged_results.append(current_bin)
            i += 1
            continue
        
        # If bin is inadequate and has trials, try to merge with next bin
        if not current_bin['bin_adequate'] and current_bin['n_trials_in_bin'] > 0 and i < len(results) - 1:
            next_bin = results[i + 1]
            
            # Calculate merged bin properties
            merged_n_trials = current_bin['n_trials_in_bin'] + next_bin['n_trials_in_bin']
            
            # Calculate weighted mean error
            if merged_n_trials > 0:
                # Handle potential NaN values in mean_error_degrees
                current_mean = current_bin['mean_error_degrees'] if not np.isnan(current_bin['mean_error_degrees']) else 0
                next_mean = next_bin['mean_error_degrees'] if not np.isnan(next_bin['mean_error_degrees']) else 0
                
                # Adjust trial counts for NaN means
                current_trials = current_bin['n_trials_in_bin'] if not np.isnan(current_bin['mean_error_degrees']) else 0
                next_trials = next_bin['n_trials_in_bin'] if not np.isnan(next_bin['mean_error_degrees']) else 0
                
                # Recalculate merged trials count for weighting
                effective_merged_trials = current_trials + next_trials
                
                if effective_merged_trials > 0:
                    merged_mean_error = (
                        (current_mean * current_trials) +
                        (next_mean * next_trials)
                    ) / effective_merged_trials
                else:
                    merged_mean_error = np.nan
            else:
                merged_mean_error = np.nan
            
            # Create merged bin
            merged_bin = {
                'bin_lower_bound': current_bin['bin_lower_bound'],
                'bin_upper_bound': next_bin['bin_upper_bound'],
                'bin_center_degrees': (current_bin['bin_lower_bound'] + next_bin['bin_upper_bound']) / 2,
                'mean_error_degrees': merged_mean_error,
                'n_trials_in_bin': merged_n_trials,
                'bin_adequate': merged_n_trials >= 3
            }
            
            merged_results.append(merged_bin)
            print(f"    Merged bin {i} [{current_bin['bin_lower_bound']}-{current_bin['bin_upper_bound']}°] "
                  f"({current_bin['n_trials_in_bin']} trials) with bin {i+1} "
                  f"[{next_bin['bin_lower_bound']}-{next_bin['bin_upper_bound']}°] "
                  f"({next_bin['n_trials_in_bin']} trials) → {merged_n_trials} total trials "
                  f"(adequate: {merged_bin['bin_adequate']})")
            merge_count += 1
            i += 2  # Skip the next bin since we merged it
        else:
            merged_results.append(current_bin)
            i += 1
    
    inadequate_after = sum(1 for r in merged_results if not r['bin_adequate'])
    print(f"    After merging: {merge_count} merges performed, {inadequate_after} bins still inadequate")
    print(f"    Bins reduced from {len(results)} to {len(merged_results)}")
    
    if inadequate_before > 0 and inadequate_after == 0:
        print(f"    All inadequate bins successfully merged")
    elif inadequate_after > 0:
        print(f"    Warning: {inadequate_after} bins remain inadequate after merging")
    
    return merged_results, bins_before_merging, adequate_bins_before_merging

def main():
    """
    Main function to execute the VWM data binning process.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("=" * 60)
        print("VWM DATA BINNING FOR DOG FUNCTION FITTING")
        print("=" * 60)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Created/verified outputs directory")
        
        # Find the most recent input file
        input_pattern = 'outputs/VWM_cleaned_data_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read the input data
        print("Reading input data...")
        df = pd.read_csv(input_file)
        print(f"Successfully read data with shape: {df.shape}")
        
        # Print all columns
        print("All columns in input data:")
        print(df.columns.tolist())
        
        # Print first 3 rows
        print("\nFirst 3 rows of input data:")
        print(df.head(3))
        
        # Validate required columns
        required_columns = ['participantId', 'trial_type', 'VWM_setSize', 'VWM_delay_s',
                           'VWM_error_degrees', 'angular_difference_current_previous', 'excluded_trial']
        
        if not validate_required_columns(df, required_columns):
            return 1
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"trial_type: {sorted(df['trial_type'].unique())}")
        print(f"VWM_setSize: {sorted(df['VWM_setSize'].unique())}")
        print(f"VWM_delay_s: {sorted(df['VWM_delay_s'].unique())}")
        print(f"excluded_trial: {sorted(df['excluded_trial'].unique())}")
        
        # Print data types for measured variables
        print("\nData types for measured variables:")
        print(f"VWM_error_degrees: {df['VWM_error_degrees'].dtype}")
        print(f"angular_difference_current_previous: {df['angular_difference_current_previous'].dtype}")
        
        # Filter and prepare data
        df_filtered = filter_and_prepare_data(df)
        
        if len(df_filtered) == 0:
            print("ERROR: No valid data remaining after filtering")
            return 1
        
        # Wrap angular differences to proper range
        print("Wrapping angular differences to [-90, 90] range...")
        df_filtered = df_filtered.copy()
        df_filtered['angular_difference_current_previous'] = wrap_angular_difference(
            df_filtered['angular_difference_current_previous']
        )
        
        # Create angular bins
        bins = create_angular_bins()
        print(f"Created {len(bins)} angular bins:")
        for i, (lower, upper, center) in enumerate(bins):
            print(f"  Bin {i}: [{lower}-{upper}°), center: {center}°")
        
        # Process data by participant and condition
        print("\nProcessing data by participant and condition...")
        
        # Group by participant, set size, and delay
        grouped = df_filtered.groupby(['participantId', 'VWM_setSize', 'VWM_delay_s'])
        
        all_results = []
        participant_summary = []
        
        for (participant_id, set_size, delay), group_data in grouped:
            print(f"Processing participant {participant_id}, set size {set_size}, delay {delay}s...")
            print(f"  Number of trials: {len(group_data)}")
            
            # Bin the data for this participant-condition
            bin_results = bin_data_for_participant_condition(group_data, bins)
            
            # Count adequate bins before and after merging
            # Note: bin_data_for_participant_condition now returns a tuple with before/after stats
            if isinstance(bin_results, tuple) and len(bin_results) == 3:
                bin_results, bins_before_merging, adequate_bins_before_merging = bin_results
                adequate_bins = sum(1 for result in bin_results if result['bin_adequate'])
                print(f"  Adequate bins before merging: {adequate_bins_before_merging}/{bins_before_merging}")
                print(f"  Adequate bins after merging: {adequate_bins}/{len(bin_results)}")
            else:
                adequate_bins = sum(1 for result in bin_results if result['bin_adequate'])
                adequate_bins_before_merging = adequate_bins  # If no merging stats available
                bins_before_merging = len(bin_results)
                print(f"  Adequate bins (≥3 trials): {adequate_bins}/{len(bin_results)}")
            
            # Add participant and condition info to each bin result
            for result in bin_results:
                result['participantId'] = participant_id
                result['VWM_setSize'] = set_size
                result['VWM_delay_s'] = delay
                result['condition_label'] = f"setSize{set_size}_delay{delay}s"
                all_results.append(result)
            
            # Track participant summary
            participant_summary.append({
                'participantId': participant_id,
                'VWM_setSize': set_size,
                'VWM_delay_s': delay,
                'total_trials': len(group_data),
                'adequate_bins': adequate_bins,
                'bins_before_merging': bins_before_merging,
                'adequate_bins_before_merging': adequate_bins_before_merging,
                'sufficient_for_fitting': adequate_bins >= 4,
                'sufficient_before_merging': adequate_bins_before_merging >= 4
            })
        
        # Create output dataframe
        print("\nCreating output dataframe...")
        output_df = pd.DataFrame(all_results)
        
        # Reorder columns as specified
        output_columns = ['participantId', 'VWM_setSize', 'VWM_delay_s', 'bin_center_degrees',
                         'bin_lower_bound', 'bin_upper_bound', 'mean_error_degrees',
                         'n_trials_in_bin', 'bin_adequate', 'condition_label']
        
        output_df = output_df[output_columns]
        
        print("Output dataframe created successfully!")
        print(f"Output shape: {output_df.shape}")
        
        # Print all columns
        print("\nAll columns in output data:")
        print(output_df.columns.tolist())
        
        # Print first 2 rows
        print("\nFirst 2 rows of output data:")
        print(output_df.head(2))
        
        # Print summary statistics
        print("\nSummary statistics:")
        print(f"Total bins: {len(output_df)}")
        print(f"Adequate bins: {output_df['bin_adequate'].sum()}")
        print(f"Percentage adequate: {output_df['bin_adequate'].mean()*100:.1f}%")
        
        # Print participant summary
        summary_df = pd.DataFrame(participant_summary)
        print(f"\nParticipant-condition summary:")
        print(f"Total participant-conditions: {len(summary_df)}")
        print(f"Sufficient for fitting (≥4 adequate bins): {summary_df['sufficient_for_fitting'].sum()} ({summary_df['sufficient_for_fitting'].mean():.1%})")
        
        # Summarize by set size and delay
        print("\nSummary by experimental condition:")
        for set_size in sorted(summary_df['VWM_setSize'].unique()):
            for delay in sorted(summary_df['VWM_delay_s'].unique()):
                condition_df = summary_df[(summary_df['VWM_setSize'] == set_size) & 
                                         (summary_df['VWM_delay_s'] == delay)]
                if len(condition_df) > 0:
                    sufficient = condition_df['sufficient_for_fitting'].sum()
                    total = len(condition_df)
                    print(f"  Set size {set_size}, delay {delay}s: {sufficient}/{total} sufficient ({sufficient/total:.1%})")
                    
                    # Bin adequacy distribution
                    bin_counts = condition_df['adequate_bins'].value_counts().sort_index()
                    print(f"    Adequate bin distribution: {dict(bin_counts.items())}")
        
        # List participants with insufficient data
        insufficient_conditions = summary_df[~summary_df['sufficient_for_fitting']]
        if len(insufficient_conditions) > 0:
            print(f"\nParticipant-conditions with insufficient data ({len(insufficient_conditions)}):")
            for _, row in insufficient_conditions.iterrows():
                print(f"  {row['participantId']}, set size {row['VWM_setSize']}, delay {row['VWM_delay_s']}s: {row['adequate_bins']} adequate bins")
        
        # Summarize effect of bin merging
        if 'bins_before_merging' in summary_df.columns and 'adequate_bins_before_merging' in summary_df.columns:
            total_before = summary_df['adequate_bins_before_merging'].sum()
            total_after = summary_df['adequate_bins'].sum()
            print(f"\nBin merging effect:")
            print(f"  Adequate bins before merging: {total_before}")
            print(f"  Adequate bins after merging: {total_after}")
            if total_before > 0:
                print(f"  Increase due to merging: {total_after - total_before} ({(total_after - total_before)/total_before:.1%})")
            else:
                print(f"  Increase due to merging: {total_after - total_before} (N/A%)")
            
            sufficient_before = (summary_df['adequate_bins_before_merging'] >= 4).sum()
            sufficient_after = summary_df['sufficient_for_fitting'].sum()
            print(f"  Sufficient participants before merging: {sufficient_before}/{len(summary_df)} ({sufficient_before/len(summary_df):.1%})")
            print(f"  Sufficient participants after merging: {sufficient_after}/{len(summary_df)} ({sufficient_after/len(summary_df):.1%})")
            print(f"  Additional participants eligible for fitting: {sufficient_after - sufficient_before}")
        
        # Save output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'outputs/VWM_binned_for_DoG_{timestamp}.csv'
        
        print(f"\nSaving output to: {output_filename}")
        output_df.to_csv(output_filename, index=False)
        print("Output file saved successfully!")
        
        # Final validation
        print("\nFinal validation:")
        print(f"Output file exists: {os.path.exists(output_filename)}")
        
        # Read back and verify
        verification_df = pd.read_csv(output_filename)
        print(f"Verification read shape: {verification_df.shape}")
        print(f"Columns match: {list(verification_df.columns) == output_columns}")
        
        # Double-check no extra columns
        if set(verification_df.columns) != set(output_columns):
            extra_cols = set(verification_df.columns) - set(output_columns)
            missing_cols = set(output_columns) - set(verification_df.columns)
            if extra_cols:
                print(f"Warning: Extra columns found in output file: {extra_cols}")
            if missing_cols:
                print(f"Warning: Missing columns in output file: {missing_cols}")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
