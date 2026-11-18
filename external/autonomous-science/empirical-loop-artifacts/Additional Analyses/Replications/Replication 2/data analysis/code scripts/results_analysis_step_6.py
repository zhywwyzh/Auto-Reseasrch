import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def parse_duration_to_seconds(duration_str):
    """
    Convert duration from HH:MM:SS format to total seconds.
    
    Parameters:
    duration_str (str): Duration in HH:MM:SS format
    
    Returns:
    float: Total seconds, or 0 if parsing fails
    """
    if pd.isna(duration_str) or duration_str is None or duration_str == '':
        return 0.0
    
    try:
        parts = str(duration_str).split(':')
        if len(parts) == 3:
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        else:
            return 0.0
    except (ValueError, IndexError):
        return 0.0

def extract_focus_loss_data(raw_files):
    """
    Extract focus loss data from raw task files.
    
    Parameters:
    raw_files (list): List of raw CSV file paths
    
    Returns:
    dict: Dictionary with participantId as key and focus loss data as values
    """
    focus_loss_data = {}
    
    for file_path in raw_files:
        print(f"Processing raw file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print(f"Raw file columns: {list(df.columns)}")
            print(f"First 3 rows of raw file:")
            print(df.head(3))
            
            # Look for metadata rows
            if 'table' in df.columns:
                metadata_rows = df[df['table'] == 'metadata']
                print(f"Found {len(metadata_rows)} metadata rows")
                
                if len(metadata_rows) > 0:
                    participant_id = None
                    if 'participantId' in metadata_rows.columns:
                        participant_id = metadata_rows['participantId'].iloc[0]
                    
                    if participant_id:
                        focus_instances = 0
                        focus_duration = 0.0
                        missing_data = True
                        
                        if 'windowFocusLostDuringTasksNum' in metadata_rows.columns:
                            focus_instances_val = metadata_rows['windowFocusLostDuringTasksNum'].iloc[0]
                            if pd.notna(focus_instances_val):
                                focus_instances = int(focus_instances_val) if focus_instances_val != '' else 0
                                missing_data = False
                        
                        if 'windowFocusLostDuringTasksDuration' in metadata_rows.columns:
                            focus_duration_val = metadata_rows['windowFocusLostDuringTasksDuration'].iloc[0]
                            if pd.notna(focus_duration_val) and focus_duration_val != '':
                                focus_duration = parse_duration_to_seconds(focus_duration_val)
                                missing_data = False
                        
                        focus_loss_data[participant_id] = {
                            'focus_loss_instances_raw': focus_instances,
                            'focus_loss_duration_seconds_raw': focus_duration,
                            'missing_focus_loss_data': missing_data
                        }
                        print(f"Participant {participant_id}: instances={focus_instances}, duration={focus_duration}s, missing={missing_data}")
            else:
                print("No 'table' column found in raw file")
                
        except Exception as e:
            print(f"Error processing raw file {file_path}: {e}")
            continue
    
    print(f"Extracted focus loss data for {len(focus_loss_data)} participants")
    return focus_loss_data

def calculate_rt_coefficient_variation(vwm_data, mrt_data):
    """
    Calculate coefficient of variation of RT across both tasks for each participant.
    
    Parameters:
    vwm_data (DataFrame): VWM cleaned trial data
    mrt_data (DataFrame): MRT cleaned trial data
    
    Returns:
    dict: Dictionary with participantId as key and RT statistics as values
    """
    rt_stats = {}
    
    # Filter VWM data for valid test trials
    vwm_valid = vwm_data[
        (vwm_data['trial_valid'] == True) & 
        (vwm_data['trial_type'] == 'test')
    ].copy()
    print(f"VWM valid test trials: {len(vwm_valid)}")
    
    # Filter MRT data for valid correct test trials
    mrt_valid = mrt_data[
        (mrt_data['trial_valid_rt_analysis'] == True) & 
        (mrt_data['is_correct'] == True) & 
        (mrt_data['trial_type'] == 'test')
    ].copy()
    print(f"MRT valid correct test trials: {len(mrt_valid)}")
    
    # Combine RT data from both tasks
    vwm_rt = vwm_valid[['participantId', 'response_time_ms']].copy()
    mrt_rt = mrt_valid[['participantId', 'response_time_ms']].copy()
    
    combined_rt = pd.concat([vwm_rt, mrt_rt], ignore_index=True)
    print(f"Combined RT data shape: {combined_rt.shape}")
    
    # Calculate RT statistics for each participant
    unique_participants = combined_rt['participantId'].unique()
    for participant_id in unique_participants:
        participant_rts = combined_rt[combined_rt['participantId'] == participant_id]['response_time_ms']
        
        if len(participant_rts) > 1:  # Need at least 2 trials to calculate CV
            mean_rt = participant_rts.mean()
            sd_rt = participant_rts.std()
            cv_rt = (sd_rt / mean_rt) * 100 if mean_rt > 0 else 0
            
            rt_stats[participant_id] = {
                'rt_coefficient_variation': cv_rt,
                'total_valid_trials_combined': len(participant_rts),
                'mean_rt_combined_tasks': mean_rt,
                'sd_rt_combined_tasks': sd_rt
            }
        else:
            print(f"Warning: Participant {participant_id} has insufficient valid trials ({len(participant_rts)})")
    
    print(f"Calculated RT statistics for {len(rt_stats)} participants")
    return rt_stats

def standardize_variables(data_dict, variables):
    """
    Calculate z-scores for specified variables across all participants.
    
    Parameters:
    data_dict (dict): Dictionary with participant data
    variables (list): List of variable names to standardize
    
    Returns:
    dict: Updated dictionary with standardized variables
    """
    # Explicit mapping for standardized column names
    var_to_standardized_col = {
        'rt_coefficient_variation': 'rt_cv_standardized',
        'focus_loss_instances_raw': 'focus_loss_instances_standardized',
        'focus_loss_duration_seconds_raw': 'focus_loss_duration_standardized'
    }
    for var in variables:
        # Filter out NaN values
        values = [data_dict[pid][var] for pid in data_dict if var in data_dict[pid] and not pd.isna(data_dict[pid][var])]
        if len(values) > 1:
            mean_val = np.nanmean(values)
            sd_val = np.nanstd(values, ddof=1)
            print(f"Standardizing {var}: mean={mean_val:.3f}, sd={sd_val:.3f}")
            for participant_id in data_dict:
                if var in data_dict[participant_id]:
                    raw_val = data_dict[participant_id][var]
                    if pd.isna(raw_val) or sd_val == 0:
                        z_score = np.nan
                    else:
                        z_score = (raw_val - mean_val) / sd_val
                    standardized_col = var_to_standardized_col.get(var, f"{var}_standardized")
                    data_dict[participant_id][standardized_col] = z_score
    return data_dict

def check_extreme_outliers(data_dict, standardized_vars):
    """
    Check for extreme outliers (>3 SD from mean) in standardized variables.
    
    Parameters:
    data_dict (dict): Dictionary with participant data
    standardized_vars (list): List of standardized variable names
    
    Returns:
    None
    """
    print("\nChecking for extreme outliers (>3 SD):")
    for var in standardized_vars:
        extreme_participants = []
        for participant_id in data_dict:
            if var in data_dict[participant_id]:
                z_score = data_dict[participant_id][var]
                if pd.isna(z_score):
                    continue
                if abs(z_score) > 3:
                    extreme_participants.append((participant_id, z_score))
        if extreme_participants:
            print(f"{var}: {len(extreme_participants)} extreme outliers")
            for pid, z_score in extreme_participants:
                print(f"  Participant {pid}: z-score = {z_score:.3f}")
        else:
            print(f"{var}: No extreme outliers")

def main():
    """
    Main function to process cognitive covariates data.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting cognitive covariates processing...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input files
        print("\nFinding input files...")
        
        # Find VWM cleaned data
        vwm_pattern = "outputs/VWM_cleaned_trial_data_*.csv"
        vwm_file = find_latest_file(vwm_pattern)
        if not vwm_file:
            print(f"Error: No VWM cleaned data file found matching pattern: {vwm_pattern}")
            return 1
        print(f"Found VWM file: {vwm_file}")
        
        # Find MRT cleaned data
        mrt_pattern = "outputs/MRT_cleaned_trial_data_*.csv"
        mrt_file = find_latest_file(mrt_pattern)
        if not mrt_file:
            print(f"Error: No MRT cleaned data file found matching pattern: {mrt_pattern}")
            return 1
        print(f"Found MRT file: {mrt_file}")
        
        # Find raw task data files
        raw_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        raw_files = glob.glob(raw_pattern)
        if not raw_files:
            print(f"Error: No raw task data files found matching pattern: {raw_pattern}")
            return 1
        print(f"Found {len(raw_files)} raw task data files")
        
        # Load VWM data
        print(f"\nLoading VWM data from: {vwm_file}")
        vwm_data = pd.read_csv(vwm_file)
        print(f"VWM data columns: {list(vwm_data.columns)}")
        print(f"VWM data shape: {vwm_data.shape}")
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
        
        # Check required VWM columns
        required_vwm_cols = ['participantId', 'response_time_ms', 'trial_valid', 'trial_type']
        missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
        if missing_vwm_cols:
            print(f"Error: Missing required VWM columns: {missing_vwm_cols}")
            return 1
        
        # Print unique values for key columns
        print(f"VWM trial_type unique values: {vwm_data['trial_type'].unique()}")
        print(f"VWM trial_valid unique values: {vwm_data['trial_valid'].unique()}")
        print(f"VWM response_time_ms type: {vwm_data['response_time_ms'].dtype}")
        
        # Load MRT data
        print(f"\nLoading MRT data from: {mrt_file}")
        mrt_data = pd.read_csv(mrt_file)
        print(f"MRT data columns: {list(mrt_data.columns)}")
        print(f"MRT data shape: {mrt_data.shape}")
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        # Check required MRT columns
        required_mrt_cols = ['participantId', 'response_time_ms', 'is_correct', 'trial_valid_rt_analysis', 'trial_type']
        missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
        if missing_mrt_cols:
            print(f"Error: Missing required MRT columns: {missing_mrt_cols}")
            return 1
        
        # Print unique values for key columns
        print(f"MRT trial_type unique values: {mrt_data['trial_type'].unique()}")
        print(f"MRT trial_valid_rt_analysis unique values: {mrt_data['trial_valid_rt_analysis'].unique()}")
        print(f"MRT is_correct unique values: {mrt_data['is_correct'].unique()}")
        print(f"MRT response_time_ms type: {mrt_data['response_time_ms'].dtype}")
        
        # Extract focus loss data from raw files
        print("\nExtracting focus loss data...")
        focus_loss_data = extract_focus_loss_data(raw_files)
        
        # Calculate RT coefficient of variation
        print("\nCalculating RT coefficient of variation...")
        rt_stats = calculate_rt_coefficient_variation(vwm_data, mrt_data)
        
        # Combine all participant data
        print("\nCombining participant data...")
        all_participants = set(list(focus_loss_data.keys()) + list(rt_stats.keys()))
        print(f"Total unique participants: {len(all_participants)}")
        
        combined_data = {}
        for participant_id in all_participants:
            combined_data[participant_id] = {}
            
            # Add focus loss data
            if participant_id in focus_loss_data:
                combined_data[participant_id].update(focus_loss_data[participant_id])
            else:
                combined_data[participant_id].update({
                    'focus_loss_instances_raw': 0,
                    'focus_loss_duration_seconds_raw': 0.0,
                    'missing_focus_loss_data': True
                })
            
            # Add RT statistics
            if participant_id in rt_stats:
                combined_data[participant_id].update(rt_stats[participant_id])
            else:
                print(f"Warning: No RT statistics for participant {participant_id}")
        
        # Standardize variables
        print("\nStandardizing variables...")
        variables_to_standardize = [
            'rt_coefficient_variation',
            'focus_loss_instances_raw',
            'focus_loss_duration_seconds_raw'
        ]
        
        standardized_data = standardize_variables(combined_data, variables_to_standardize)
        print(f"Total participants for analysis: {len(combined_data)}")

        # Print counts of participants with and without RT data
        num_with_rt = sum(
            1 for pid, data in combined_data.items()
            if not pd.isna(data.get('rt_coefficient_variation', np.nan))
        )
        num_without_rt = len(combined_data) - num_with_rt
        print(f"Participants with RT data: {num_with_rt}")
        print(f"Participants without RT data: {num_without_rt}")
        
        # Check for extreme outliers
        standardized_vars = [
            'rt_cv_standardized',
            'focus_loss_instances_standardized',
            'focus_loss_duration_standardized'
        ]
        check_extreme_outliers(standardized_data, standardized_vars)
        
        # Create output dataframe
        print("\nCreating output dataframe...")
        output_rows = []
        
        for participant_id, data in standardized_data.items():
            row = {
                'participantId': participant_id,
                'rt_coefficient_variation': data.get('rt_coefficient_variation', np.nan),
                'focus_loss_instances_raw': data.get('focus_loss_instances_raw', 0),
                'focus_loss_duration_seconds_raw': data.get('focus_loss_duration_seconds_raw', 0.0),
                'rt_cv_standardized': data.get('rt_cv_standardized', np.nan),
                'focus_loss_instances_standardized': data.get('focus_loss_instances_standardized', np.nan),
                'focus_loss_duration_standardized': data.get('focus_loss_duration_standardized', np.nan),
                'missing_focus_loss_data': data.get('missing_focus_loss_data', True),
                'total_valid_trials_combined': data.get('total_valid_trials_combined', 0),
                'mean_rt_combined_tasks': data.get('mean_rt_combined_tasks', np.nan),
                'sd_rt_combined_tasks': data.get('sd_rt_combined_tasks', np.nan)
            }
            output_rows.append(row)
        
        output_df = pd.DataFrame(output_rows)
        
        print(f"Output dataframe shape: {output_df.shape}")
        print("Output dataframe columns:", list(output_df.columns))
        print("First 2 rows of output dataframe:")
        print(output_df.head(2))
        
        # Summary statistics
        print("\nSummary statistics:")
        print(f"Participants with missing focus loss data: {output_df['missing_focus_loss_data'].sum()}")
        print(f"Mean RT CV: {output_df['rt_coefficient_variation'].mean():.3f}")
        print(f"Mean focus loss instances: {output_df['focus_loss_instances_raw'].mean():.3f}")
        print(f"Mean focus loss duration: {output_df['focus_loss_duration_seconds_raw'].mean():.3f}")
        
        # Save output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"outputs/cognitive_covariates_{timestamp}.csv"
        output_df.to_csv(output_filename, index=False)
        print(f"\nSaved output to: {output_filename}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
