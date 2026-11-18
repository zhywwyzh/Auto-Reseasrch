import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

def get_most_recent_file(pattern):
    """
    Get the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def normalize_error(response_angle, target_angle):
    """
    Normalize orientation errors to ±90° range.
    
    Parameters:
    response_angle (float): Response angle in degrees
    target_angle (float): Target angle in degrees
    
    Returns:
    float: Normalized error in degrees
    """
    return ((response_angle - target_angle + 90) % 180) - 90

def main():
    """
    Main function to process VWM data with exclusions and cleaning.
    """
    try:
        print("Starting VWM data processing...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Get timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load participant exclusion file
        print("Loading participant exclusion data...")
        exclusion_pattern = "outputs/participants_post_initial_exclusions_*.csv"
        exclusion_file = get_most_recent_file(exclusion_pattern)
        
        if exclusion_file is None:
            print(f"Error: No participant exclusion file found matching pattern: {exclusion_pattern}")
            return 1
        
        print(f"Found exclusion file: {exclusion_file}")
        exclusions_df = pd.read_csv(exclusion_file)
        
        print("Exclusion file columns:", list(exclusions_df.columns))
        print("First 3 rows of exclusion data:")
        print(exclusions_df.head(3))
        
        # Load VWM data files
        print("Loading VWM data files...")
        vwm_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        vwm_files = glob.glob(vwm_pattern)
        
        if not vwm_files:
            print(f"Error: No VWM data files found matching pattern: {vwm_pattern}")
            return 1
        
        print(f"Found {len(vwm_files)} VWM data files")
        
        # Combine all VWM data
        all_vwm_data = []
        
        for file in vwm_files:
            print(f"Processing file: {file}")
            df = pd.read_csv(file)
            
            # Check if required columns exist
            required_cols = ['participantId', 'isPractice', 'VWM_trial', 'VWM_timeout', 
                           'VWM_rt_ms', 'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees',
                           'VWM_error_degrees', 'VWM_error_absolute_degrees']
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Warning: Missing columns in {file}: {missing_cols}. Skipping file.")
                continue
            
            # Filter for VWM task rows only (rows where VWM_trial is not null)
            vwm_rows = df[df['VWM_trial'].notna()].copy()
            
            if len(vwm_rows) > 0:
                print(f"Found {len(vwm_rows)} VWM rows in {file}")
                all_vwm_data.append(vwm_rows)
        
        if not all_vwm_data:
            print("Error: No valid VWM data found in any files")
            return 1
        
        # Combine all VWM data
        vwm_df = pd.concat(all_vwm_data, ignore_index=True)
        print(f"Total VWM rows loaded: {len(vwm_df)}")
        
        print("VWM data columns:", list(vwm_df.columns))
        print("First 3 rows of VWM data:")
        print(vwm_df.head(3))
        
        # Print unique values for key experimental design columns
        print("Unique values in isPractice:", vwm_df['isPractice'].unique())
        print("Unique values in VWM_timeout:", vwm_df['VWM_timeout'].unique())
        print("Data type of VWM_rt_ms:", type(vwm_df['VWM_rt_ms'].iloc[0]) if len(vwm_df) > 0 else "No data")
        
        # Step 1: Include only non-excluded participants
        print("\nStep 1: Filtering participants...")
        valid_participants = exclusions_df[exclusions_df['excluded'] == False]['participantId'].tolist()
        print(f"Valid participants: {len(valid_participants)}")
        
        vwm_df = vwm_df[vwm_df['participantId'].isin(valid_participants)].copy()
        print(f"VWM data after participant filtering: {len(vwm_df)} rows")
        
        # Calculate total non-practice trials for valid participants BEFORE trial-level exclusions
        total_trials_map = vwm_df[vwm_df['isPractice'] == False].groupby('participantId').size().rename('total_original_trials')
        print(f"Calculated total trials map for {len(total_trials_map)} valid participants")
        # Initialize exclusion tracking
        exclusion_log = []
        
        # Step 2: Apply trial-level exclusions
        print("\nStep 2: Applying trial-level exclusions...")
        
        initial_count = len(vwm_df)
        print(f"Starting with {initial_count} VWM trials")
        
        # Remove practice trials
        practice_trials = vwm_df['isPractice'] == True
        practice_count = practice_trials.sum()
        vwm_df = vwm_df[~practice_trials].copy()
        exclusion_log.append(['Practice trials', practice_count])
        print(f"Removed {practice_count} practice trials, remaining: {len(vwm_df)}")
        
        # Remove timeout trials
        timeout_trials = vwm_df['VWM_timeout'] == True
        timeout_count = timeout_trials.sum()
        vwm_df = vwm_df[~timeout_trials].copy()
        exclusion_log.append(['Timeout trials', timeout_count])
        print(f"Removed {timeout_count} timeout trials, remaining: {len(vwm_df)}")
        
        # Remove trials with RT < 200ms
        rt_too_fast = vwm_df['VWM_rt_ms'] < 200
        rt_fast_count = rt_too_fast.sum()
        vwm_df = vwm_df[~rt_too_fast].copy()
        exclusion_log.append(['RT < 200ms', rt_fast_count])
        print(f"Removed {rt_fast_count} trials with RT < 200ms, remaining: {len(vwm_df)}")
        
        # Remove trials with RT > 15,000ms
        rt_too_slow = vwm_df['VWM_rt_ms'] > 15000
        rt_slow_count = rt_too_slow.sum()
        vwm_df = vwm_df[~rt_too_slow].copy()
        exclusion_log.append(['RT > 15000ms', rt_slow_count])
        print(f"Removed {rt_slow_count} trials with RT > 15000ms, remaining: {len(vwm_df)}")
        
        # Step 3: Normalize orientation errors
        print("\nStep 3: Normalizing orientation errors...")
        vwm_df['VWM_normalized_error_degrees'] = vwm_df.apply(
            lambda row: normalize_error(row['VWM_responseAngle_degrees'], row['VWM_targetAngle_degrees']), 
            axis=1
        )
        
        # Validate normalized errors are within ±90°
        normalized_errors = vwm_df['VWM_normalized_error_degrees']
        print(f"Normalized error range: {normalized_errors.min():.2f} to {normalized_errors.max():.2f}")
        
        if normalized_errors.min() < -90 or normalized_errors.max() > 90:
            print("Warning: Normalized errors outside ±90° range detected")
        else:
            print("Normalized errors are within ±90° range")
        
        # Step 4: Apply participant-level exclusions
        print("\nStep 4: Applying participant-level exclusions...")

        # Calculate valid trials per participant
        valid_trials_map = vwm_df.groupby('participantId').size().rename('valid_trials')

        # Combine stats into a single DataFrame using the pre-calculated total_trials_map
        stats_df = pd.DataFrame(total_trials_map).join(valid_trials_map, how='left').reset_index()
        stats_df['valid_trials'] = stats_df['valid_trials'].fillna(0).astype(int)
        stats_df['valid_percentage'] = stats_df['valid_trials'] / stats_df['total_original_trials']

        # Calculate mean error and RT for participants with valid trials
        means = vwm_df.groupby('participantId').agg(
            mean_abs_error=('VWM_error_absolute_degrees', 'mean'),
            mean_rt=('VWM_rt_ms', 'mean')
        )
        stats_df = stats_df.merge(means, on='participantId', how='left')

        print(f"Participant statistics calculated for {len(stats_df)} participants")

        # Track excluded participants without removing their data
        excluded_participants = {}
        current_stats = stats_df.copy()

        # Exclude participants with < 50% valid trials
        low_validity_pids = current_stats[current_stats['valid_percentage'] < 0.5]['participantId']
        for pid in low_validity_pids:
            excluded_participants[pid] = '< 50% valid trials'
        current_stats = current_stats[~current_stats['participantId'].isin(low_validity_pids)]
        exclusion_log.append(['< 50% valid trials', len(low_validity_pids)])
        print(f"Excluded {len(low_validity_pids)} participants with < 50% valid trials")
        print(f"Remaining participants: {len(current_stats)}")

        # Exclude participants with mean absolute error > 3 SD above mean
        mean_abs_errors = current_stats['mean_abs_error'].dropna()
        if len(mean_abs_errors) > 0:
            error_mean = mean_abs_errors.mean()
            error_sd = mean_abs_errors.std()
            error_threshold = error_mean + 3 * error_sd

            high_error_pids = current_stats[current_stats['mean_abs_error'] > error_threshold]['participantId']
            for pid in high_error_pids:
                excluded_participants[pid] = 'High error (>3SD above mean)'
            current_stats = current_stats[~current_stats['participantId'].isin(high_error_pids)]
            exclusion_log.append(['High error (>3SD above mean)', len(high_error_pids)])
            print(f"Error threshold: {error_threshold:.2f}")
            print(f"Excluded {len(high_error_pids)} participants with high error")

        # Exclude participants with mean RT > 3 SD from mean
        mean_rts = current_stats['mean_rt'].dropna()
        if len(mean_rts) > 0:
            rt_mean = mean_rts.mean()
            rt_sd = mean_rts.std()
            rt_threshold_low = rt_mean - 3 * rt_sd
            rt_threshold_high = rt_mean + 3 * rt_sd

            extreme_rt_pids = current_stats[(current_stats['mean_rt'] < rt_threshold_low) | (current_stats['mean_rt'] > rt_threshold_high)]['participantId']
            for pid in extreme_rt_pids:
                excluded_participants[pid] = 'Extreme RT (>3SD from mean)'
            current_stats = current_stats[~current_stats['participantId'].isin(extreme_rt_pids)]
            exclusion_log.append(['Extreme RT (>3SD from mean)', len(extreme_rt_pids)])
            print(f"RT thresholds: {rt_threshold_low:.2f} to {rt_threshold_high:.2f}")
            print(f"Excluded {len(extreme_rt_pids)} participants with extreme RT")
        
        # Step 5: Data validation
        print("\nStep 5: Data validation...")

        # Prepare final dataset with required columns and exclusion info
        final_df = vwm_df.copy()
        final_df['exclusion_reason'] = final_df['participantId'].map(excluded_participants).fillna('None')
        final_df['excluded'] = final_df['exclusion_reason'] != 'None'

        # For final reporting, filter to non-excluded data
        final_data_for_stats = final_df[final_df['excluded'] == False]
        print(f"Final dataset: {len(final_data_for_stats)} trials from {final_data_for_stats['participantId'].nunique()} participants")

        # Check normalized errors
        final_normalized_errors = final_data_for_stats['VWM_normalized_error_degrees']
        print(f"Final normalized error range: {final_normalized_errors.min():.2f} to {final_normalized_errors.max():.2f}")

        # Check response time distribution
        final_rts = final_data_for_stats['VWM_rt_ms']
        print(f"Final RT range: {final_rts.min():.2f} to {final_rts.max():.2f}")
        print(f"Final RT mean: {final_rts.mean():.2f}, SD: {final_rts.std():.2f}")

        # Check data points per participant
        trials_per_participant = final_data_for_stats.groupby('participantId').size()
        print(f"Trials per participant - Min: {trials_per_participant.min()}, Max: {trials_per_participant.max()}, Mean: {trials_per_participant.mean():.1f}")

        # Save exclusion log
        exclusion_log_df = pd.DataFrame(exclusion_log, columns=['exclusion_criteria', 'total_excluded'])
        exclusion_log_file = f"outputs/VWM_exclusion_log_{timestamp}.csv"
        exclusion_log_df.to_csv(exclusion_log_file, index=False)
        print(f"Saved exclusion log to: {exclusion_log_file}")

        print("Exclusion summary:")
        print(exclusion_log_df)

        # Save cleaned data with only required columns
        output_columns = [
            'participantId', 'VWM_trial', 'VWM_rt_ms', 'VWM_responseAngle_degrees',
            'VWM_targetAngle_degrees', 'VWM_error_degrees', 'VWM_error_absolute_degrees',
            'VWM_normalized_error_degrees', 'excluded', 'exclusion_reason'
        ]

        cleaned_data = final_df[output_columns].copy()
        cleaned_data_file = f"outputs/VWM_cleaned_data_{timestamp}.csv"
        cleaned_data.to_csv(cleaned_data_file, index=False)
        print(f"Saved cleaned data to: {cleaned_data_file}")

        print("Final cleaned data columns:", list(cleaned_data.columns))
        print("First 2 rows of cleaned data:")
        print(cleaned_data.head(2))

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
