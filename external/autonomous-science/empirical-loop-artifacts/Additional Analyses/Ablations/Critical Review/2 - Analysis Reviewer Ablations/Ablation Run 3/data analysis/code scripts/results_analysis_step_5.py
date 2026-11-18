#!/usr/bin/env python3
"""
Control Variables Calculation Script

This script calculates control variables for VWM and MRT tasks including:
- VWM mean accuracy for non-guess trials
- Response time coefficients of variation
- Focus loss measures
- Timeout rates
- Engagement index
"""

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
    pattern (str): File pattern to search for
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def parse_duration_to_ms(duration_str):
    """
    Parse duration string to milliseconds.
    Handles various time formats including HH:MM:SS.mmm
    
    Parameters:
    duration_str (str): Duration string to parse
    
    Returns:
    float: Duration in milliseconds, or 0 if parsing fails
    """
    if pd.isna(duration_str) or duration_str == '' or duration_str == '0':
        return 0.0
    
    try:
        # Handle string format
        duration_str = str(duration_str).strip()
        
        # If it's already a number, assume it's in milliseconds
        try:
            return float(duration_str)
        except ValueError:
            pass
        
        # Parse time format HH:MM:SS.mmm or MM:SS.mmm or SS.mmm
        parts = duration_str.split(':')
        total_ms = 0.0
        
        if len(parts) == 3:  # HH:MM:SS.mmm
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000
        elif len(parts) == 2:  # MM:SS.mmm
            minutes = float(parts[0])
            seconds = float(parts[1])
            total_ms = (minutes * 60 + seconds) * 1000
        elif len(parts) == 1:  # SS.mmm
            seconds = float(parts[0])
            total_ms = seconds * 1000
        
        return total_ms
    except Exception as e:
        print(f"Warning: Could not parse duration '{duration_str}': {e}")
        return 0.0

def calculate_control_variables():
    """
    Main function to calculate control variables from VWM and MRT data.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting control variables calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input files
        print("\nSearching for input files...")
        
        # VWM cleaned trials
        vwm_pattern = "outputs/vwm_cleaned_trials_*.csv"
        vwm_file = find_latest_file(vwm_pattern)
        if not vwm_file:
            print(f"Error: No VWM cleaned trials file found matching pattern: {vwm_pattern}")
            return 1
        print(f"Found VWM cleaned trials file: {vwm_file}")
        
        # MRT cleaned trials
        mrt_pattern = "outputs/mrt_cleaned_trials_*.csv"
        mrt_file = find_latest_file(mrt_pattern)
        if not mrt_file:
            print(f"Error: No MRT cleaned trials file found matching pattern: {mrt_pattern}")
            return 1
        print(f"Found MRT cleaned trials file: {mrt_file}")
        
        # VWM mixture parameters
        mixture_pattern = "outputs/vwm_mixture_parameters_*.csv"
        mixture_file = find_latest_file(mixture_pattern)
        if not mixture_file:
            print(f"Error: No VWM mixture parameters file found matching pattern: {mixture_pattern}")
            return 1
        print(f"Found VWM mixture parameters file: {mixture_file}")
        
        # Original task files
        original_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
        original_files = glob.glob(original_pattern)
        if not original_files:
            print(f"Error: No original task files found matching pattern: {original_pattern}")
            return 1
        print(f"Found {len(original_files)} original task files")
        
        # Load VWM cleaned trials
        print(f"\nLoading VWM cleaned trials from: {vwm_file}")
        vwm_data = pd.read_csv(vwm_file)
        print(f"VWM data columns: {list(vwm_data.columns)}")
        print(f"VWM data shape: {vwm_data.shape}")
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
        
        # Check required VWM columns
        required_vwm_cols = ['participant_id', 'error_absolute_degrees', 'response_time_ms']
        missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
        if missing_vwm_cols:
            print(f"Error: Missing required VWM columns: {missing_vwm_cols}")
            return 1
        
        # Load MRT cleaned trials
        print(f"\nLoading MRT cleaned trials from: {mrt_file}")
        mrt_data = pd.read_csv(mrt_file)
        print(f"MRT data columns: {list(mrt_data.columns)}")
        print(f"MRT data shape: {mrt_data.shape}")
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        # Check required MRT columns
        required_mrt_cols = ['participant_id', 'response_time_ms']
        missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
        if missing_mrt_cols:
            print(f"Error: Missing required MRT columns: {missing_mrt_cols}")
            return 1
        
        # Load mixture parameters
        print(f"\nLoading mixture parameters from: {mixture_file}")
        mixture_data = pd.read_csv(mixture_file)
        print(f"Mixture data columns: {list(mixture_data.columns)}")
        print(f"Mixture data shape: {mixture_data.shape}")
        print("First 3 rows of mixture data:")
        print(mixture_data.head(3))
        
        # Check required mixture columns
        required_mixture_cols = ['participant_id', 'guess_rate', 'non_target_rate']
        missing_mixture_cols = [col for col in required_mixture_cols if col not in mixture_data.columns]
        if missing_mixture_cols:
            print(f"Error: Missing required mixture columns: {missing_mixture_cols}")
            return 1
        
        # Load and combine original task files
        print(f"\nLoading original task files...")
        original_data_list = []
        
        for file_path in original_files:
            try:
                print(f"Loading: {file_path}")
                df = pd.read_csv(file_path)
                original_data_list.append(df)
            except Exception as e:
                print(f"Warning: Could not load {file_path}: {e}")
                continue
        
        if not original_data_list:
            print("Error: No original task files could be loaded")
            return 1
        
        original_data = pd.concat(original_data_list, ignore_index=True)
        print(f"Combined original data columns: {list(original_data.columns)}")
        print(f"Combined original data shape: {original_data.shape}")
        print("First 3 rows of original data:")
        print(original_data.head(3))
        
        # Check required original data columns
        required_original_cols = ['participantId', 'windowFocusLostDuringTasksNum', 
                                'windowFocusLostDuringInfoNum', 'windowFocusLostDuringTasksDuration',
                                'windowFocusLostDuringInfoDuration', 'VWM_timeout', 'MRT_timeout']
        missing_original_cols = [col for col in required_original_cols if col not in original_data.columns]
        if missing_original_cols:
            print(f"Error: Missing required original data columns: {missing_original_cols}")
            return 1
        
        # Print unique values for key columns
        print("\nUnique values in key experimental design columns:")
        if 'table' in original_data.columns:
            print(f"table unique values: {sorted(original_data['table'].unique())}")
        
        # Get unique participants
        vwm_participants = set(vwm_data['participant_id'].unique())
        mrt_participants = set(mrt_data['participant_id'].unique())
        mixture_participants = set(mixture_data['participant_id'].unique())
        original_participants = set(original_data['participantId'].unique())
        
        print(f"\nParticipant counts:")
        print(f"VWM participants: {len(vwm_participants)}")
        print(f"MRT participants: {len(mrt_participants)}")
        print(f"Mixture participants: {len(mixture_participants)}")
        print(f"Original data participants: {len(original_participants)}")
        
        # Find common participants
        all_participants = vwm_participants & mrt_participants & mixture_participants & original_participants
        print(f"Common participants across all datasets: {len(all_participants)}")
        
        if len(all_participants) == 0:
            print("Error: No participants found across all datasets")
            return 1
        
        # Initialize results dataframe
        results = []
        
        print(f"\nProcessing {len(all_participants)} participants...")
        
        for participant in sorted(all_participants):
            print(f"\nProcessing participant: {participant}")
            
            # Get participant data
            vwm_participant = vwm_data[vwm_data['participant_id'] == participant].copy()
            mrt_participant = mrt_data[mrt_data['participant_id'] == participant].copy()
            mixture_participant = mixture_data[mixture_data['participant_id'] == participant]
            original_participant = original_data[original_data['participantId'] == participant]
            
            print(f"  VWM trials: {len(vwm_participant)}")
            print(f"  MRT trials: {len(mrt_participant)}")
            print(f"  Mixture parameters: {len(mixture_participant)}")
            print(f"  Original data rows: {len(original_participant)}")
            
            # Initialize participant results
            participant_results = {'participant_id': participant}
            
            # Calculate VWM mean accuracy for non-guess trials
            if len(mixture_participant) > 0 and len(vwm_participant) > 0:
                guess_rate = mixture_participant['guess_rate'].iloc[0]
                non_target_rate = mixture_participant['non_target_rate'].iloc[0]
                
                # Check if mixture parameters are valid (not NaN)
                if pd.isna(guess_rate) or pd.isna(non_target_rate):
                    print(f"  Warning: Invalid mixture parameters (NaN values) for participant {participant}")
                    vwm_mean_accuracy = np.nan
                    vwm_trials_for_accuracy = 0
                else:
                    print(f"  Guess rate: {guess_rate}")
                    print(f"  Non-target rate: {non_target_rate}")
                    
                    # Calculate proportion of non-guess trials (target + non-target components)
                    non_guess_proportion = 1 - guess_rate
                    
                    # Sort VWM trials by error and take the proportion with lowest errors as non-guess trials
                    vwm_participant_sorted = vwm_participant.sort_values('error_absolute_degrees')
                    n_non_guess_trials = int(len(vwm_participant_sorted) * non_guess_proportion)
                    
                    if n_non_guess_trials > 0:
                        non_guess_trials = vwm_participant_sorted.head(n_non_guess_trials)
                        vwm_mean_accuracy = non_guess_trials['error_absolute_degrees'].mean()
                        vwm_trials_for_accuracy = len(non_guess_trials)
                    else:
                        vwm_mean_accuracy = np.nan
                        vwm_trials_for_accuracy = 0
                    
                    print(f"  Non-guess trials for accuracy: {vwm_trials_for_accuracy}")
                    print(f"  VWM mean accuracy: {vwm_mean_accuracy}")
            else:
                vwm_mean_accuracy = np.nan
                vwm_trials_for_accuracy = 0
            
            participant_results['vwm_mean_accuracy_degrees'] = vwm_mean_accuracy
            participant_results['vwm_trials_for_accuracy'] = vwm_trials_for_accuracy
            
            # Calculate VWM RT coefficient of variation
            if len(vwm_participant) > 0:
                vwm_rt_mean = vwm_participant['response_time_ms'].mean()
                vwm_rt_std = vwm_participant['response_time_ms'].std()
                vwm_rt_cv = vwm_rt_std / vwm_rt_mean if vwm_rt_mean > 0 else np.nan
                print(f"  VWM RT CV: {vwm_rt_cv}")
            else:
                vwm_rt_cv = np.nan
            
            participant_results['vwm_rt_coefficient_variation'] = vwm_rt_cv
            
            # Calculate MRT RT coefficient of variation
            if len(mrt_participant) > 0:
                mrt_rt_mean = mrt_participant['response_time_ms'].mean()
                mrt_rt_std = mrt_participant['response_time_ms'].std()
                mrt_rt_cv = mrt_rt_std / mrt_rt_mean if mrt_rt_mean > 0 else np.nan
                mrt_trials_for_rt_cv = len(mrt_participant)
                print(f"  MRT RT CV: {mrt_rt_cv}")
                print(f"  MRT trials for RT CV: {mrt_trials_for_rt_cv}")
            else:
                mrt_rt_cv = np.nan
                mrt_trials_for_rt_cv = 0
            
            participant_results['mrt_rt_coefficient_variation'] = mrt_rt_cv
            participant_results['mrt_trials_for_rt_cv'] = mrt_trials_for_rt_cv
            
            # Extract focus loss measures from original data
            metadata_rows = original_participant[original_participant['table'] == 'metadata']
            if len(metadata_rows) > 0:
                orig_row = metadata_rows.iloc[0]
                
                focus_loss_instructions = orig_row.get('windowFocusLostDuringInfoNum', 0)
                focus_loss_tasks = orig_row.get('windowFocusLostDuringTasksNum', 0)
                
                # Convert durations to milliseconds
                focus_duration_instructions = parse_duration_to_ms(orig_row.get('windowFocusLostDuringInfoDuration', 0))
                focus_duration_tasks = parse_duration_to_ms(orig_row.get('windowFocusLostDuringTasksDuration', 0))
                
                print(f"  Focus loss instances (instructions): {focus_loss_instructions}")
                print(f"  Focus loss instances (tasks): {focus_loss_tasks}")
                print(f"  Focus loss duration (instructions): {focus_duration_instructions} ms")
                print(f"  Focus loss duration (tasks): {focus_duration_tasks} ms")
            else:
                focus_loss_instructions = 0
                focus_loss_tasks = 0
                focus_duration_instructions = 0.0
                focus_duration_tasks = 0.0
            
            participant_results['focus_loss_instances_instructions'] = focus_loss_instructions
            participant_results['focus_loss_instances_tasks'] = focus_loss_tasks
            participant_results['focus_loss_duration_instructions_ms'] = focus_duration_instructions
            participant_results['focus_loss_duration_tasks_ms'] = focus_duration_tasks
            
            # Calculate timeout rates
            if len(original_participant) > 0:
                # Filter for main task trials only
                main_task_data = original_participant[original_participant['isPractice'] == False]
                
                # Calculate timeouts from main task data only
                vwm_trials_main = main_task_data[main_task_data['VWM_timeout'].notna()]
                mrt_trials_main = main_task_data[main_task_data['MRT_timeout'].notna()]
                
                total_vwm_trials = len(vwm_trials_main)
                total_mrt_trials = len(mrt_trials_main)
                
                vwm_timeouts = vwm_trials_main['VWM_timeout'].sum() if total_vwm_trials > 0 else 0
                mrt_timeouts = mrt_trials_main['MRT_timeout'].sum() if total_mrt_trials > 0 else 0
                
                vwm_timeout_rate = vwm_timeouts / total_vwm_trials if total_vwm_trials > 0 else 0.0
                mrt_timeout_rate = mrt_timeouts / total_mrt_trials if total_mrt_trials > 0 else 0.0
                
                print(f"  VWM timeouts: {vwm_timeouts}/{total_vwm_trials} = {vwm_timeout_rate}")
                print(f"  MRT timeouts: {mrt_timeouts}/{total_mrt_trials} = {mrt_timeout_rate}")
            else:
                vwm_timeout_rate = 0.0
                mrt_timeout_rate = 0.0
            
            participant_results['vwm_timeout_rate'] = vwm_timeout_rate
            participant_results['mrt_timeout_rate'] = mrt_timeout_rate
            
            # Set data quality flag (enhanced validation)
            data_quality_flag = True
            if (pd.isna(vwm_mean_accuracy) or pd.isna(vwm_rt_cv) or pd.isna(mrt_rt_cv) or
                vwm_trials_for_accuracy == 0 or mrt_trials_for_rt_cv == 0):
                data_quality_flag = False

            # Also check mixture parameter validity if they were loaded
            if len(mixture_participant) > 0:
                guess_rate_check = mixture_participant['guess_rate'].iloc[0]
                non_target_rate_check = mixture_participant['non_target_rate'].iloc[0]
                if pd.isna(guess_rate_check) or pd.isna(non_target_rate_check):
                    data_quality_flag = False

            participant_results['data_quality_flag'] = data_quality_flag
            
            results.append(participant_results)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        print(f"\nResults dataframe shape: {results_df.shape}")
        print("Results dataframe columns:", list(results_df.columns))
        print("First 2 rows of results:")
        print(results_df.head(2))
        
        # Calculate engagement index (standardized measures)
        print("\nCalculating engagement index...")
        
        # Standardize focus loss instances during tasks
        focus_tasks_z = (results_df['focus_loss_instances_tasks'] - results_df['focus_loss_instances_tasks'].mean()) / results_df['focus_loss_instances_tasks'].std()
        
        # Standardize VWM timeout rate
        vwm_timeout_z = (results_df['vwm_timeout_rate'] - results_df['vwm_timeout_rate'].mean()) / results_df['vwm_timeout_rate'].std()
        
        # Standardize MRT timeout rate
        mrt_timeout_z = (results_df['mrt_timeout_rate'] - results_df['mrt_timeout_rate'].mean()) / results_df['mrt_timeout_rate'].std()
        
        # Handle cases where std is 0 (all values are the same)
        focus_tasks_z = focus_tasks_z.fillna(0)
        vwm_timeout_z = vwm_timeout_z.fillna(0)
        mrt_timeout_z = mrt_timeout_z.fillna(0)
        
        # Sum standardized measures (higher values = lower engagement)
        engagement_index = focus_tasks_z + vwm_timeout_z + mrt_timeout_z
        results_df['engagement_index'] = engagement_index
        
        print("Engagement index statistics:")
        print(f"  Mean: {engagement_index.mean()}")
        print(f"  Std: {engagement_index.std()}")
        print(f"  Min: {engagement_index.min()}")
        print(f"  Max: {engagement_index.max()}")
        
        # Data validation
        print("\nData validation summary:")
        print(f"Total participants: {len(results_df)}")
        print(f"Participants with good data quality: {results_df['data_quality_flag'].sum()}")
        print(f"VWM accuracy range: {results_df['vwm_mean_accuracy_degrees'].min():.2f} - {results_df['vwm_mean_accuracy_degrees'].max():.2f} degrees")
        print(f"VWM RT CV range: {results_df['vwm_rt_coefficient_variation'].min():.3f} - {results_df['vwm_rt_coefficient_variation'].max():.3f}")
        print(f"MRT RT CV range: {results_df['mrt_rt_coefficient_variation'].min():.3f} - {results_df['mrt_rt_coefficient_variation'].max():.3f}")
        
        # Reorder columns to match required output
        output_columns = [
            'participant_id',
            'vwm_mean_accuracy_degrees',
            'vwm_rt_coefficient_variation',
            'mrt_rt_coefficient_variation',
            'focus_loss_instances_instructions',
            'focus_loss_instances_tasks',
            'focus_loss_duration_instructions_ms',
            'focus_loss_duration_tasks_ms',
            'vwm_timeout_rate',
            'mrt_timeout_rate',
            'engagement_index',
            'vwm_trials_for_accuracy',
            'mrt_trials_for_rt_cv',
            'data_quality_flag'
        ]
        
        results_df = results_df[output_columns]
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/control_variables_{timestamp}.csv"
        
        print(f"\nSaving results to: {output_file}")
        results_df.to_csv(output_file, index=False)
        
        print(f"Successfully saved {len(results_df)} participants to {output_file}")
        print("Final results summary:")
        print(results_df.describe())
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in calculate_control_variables: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(calculate_control_variables())
