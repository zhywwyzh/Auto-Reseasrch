#!/usr/bin/env python3
"""
Control Variables Calculation Script

This script calculates control variables from cleaned trial data and mixture model parameters,
including VWM accuracy, response time variability, focus loss metrics, timeout rates, and
an engagement index.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

def get_latest_file(pattern):
    """
    Get the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/cleaned_trial_data_*.csv')
    
    Returns:
    --------
    str or None
        Path to the most recent file matching pattern, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def standardize_values(values):
    """
    Calculate z-scores for a series of values.
    
    Parameters:
    -----------
    values : array-like
        Values to standardize
    
    Returns:
    --------
    numpy.ndarray
        Standardized (z-score) values
    """
    values = np.array(values)
    mean_val = np.mean(values)
    std_val = np.std(values, ddof=1)  # Sample standard deviation
    
    if std_val == 0:
        print("Warning: Standard deviation is 0, returning zeros for standardized values")
        return np.zeros_like(values)
    
    return (values - mean_val) / std_val

def calculate_control_variables(trial_data, mixture_params):
    """
    Calculate all control variables for each participant.
    
    Parameters:
    -----------
    trial_data : pandas.DataFrame
        Cleaned trial data with required columns
    mixture_params : pandas.DataFrame
        Mixture model parameters with guess rates
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with calculated control variables for each participant
    """
    print("Starting control variables calculation...")
    
    # Merge trial data with mixture model parameters
    print("Merging trial data with mixture model parameters...")
    merged_data = trial_data.merge(mixture_params, on='participantId', how='left')
    print(f"Merged data shape: {merged_data.shape}")
    print("Merged data columns:", merged_data.columns.tolist())
    print("First 2 rows of merged data:")
    print(merged_data.head(2))
    
    # Initialize results list
    results = []
    
    # Get unique participants
    participants = merged_data['participantId'].unique()
    print(f"Processing {len(participants)} participants...")
    
    for i, participant_id in enumerate(participants):
        print(f"\nProcessing participant {i+1}/{len(participants)}: {participant_id}")
        
        # Filter data for this participant
        participant_data = merged_data[merged_data['participantId'] == participant_id]
        
        # Initialize result dictionary
        result = {'participantId': participant_id}
        
        # Get VWM test trials (non-practice, vwm_main table per specification)
        vwm_trials = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['table'] == 'vwm_main')
        ].copy()

        # Fallback to actual data structure if no trials found
        if len(vwm_trials) == 0:
            vwm_trials = participant_data[
                (participant_data['isPractice'] == False) & 
                (participant_data['table'] == 'vwm_test')
            ].copy()
            if len(vwm_trials) > 0:
                print(f"  WARNING: Using fallback table name 'vwm_test' instead of specified 'vwm_main'")

        print(f"  VWM test trials: {len(vwm_trials)}")

        # Get MRT test trials (non-practice, mrt_main table per specification)
        mrt_trials = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['table'] == 'mrt_main')
        ].copy()

        # Fallback to actual data structure if no trials found
        if len(mrt_trials) == 0:
            mrt_trials = participant_data[
                (participant_data['isPractice'] == False) & 
                (participant_data['table'] == 'mrt_test')
            ].copy()
            if len(mrt_trials) > 0:
                print(f"  WARNING: Using fallback table name 'mrt_test' instead of specified 'mrt_main'")

        print(f"  MRT test trials: {len(mrt_trials)}")
        
        # 1. Calculate VWM mean accuracy for non-guess trials
        if len(vwm_trials) > 0:
            # Get guess rate for this participant
            guess_rate = participant_data['guess_rate_vonmises'].iloc[0] if not pd.isna(participant_data['guess_rate_vonmises'].iloc[0]) else 0
            print(f"  Guess rate: {guess_rate}")
            
            # Estimate number of non-guess trials
            n_total_vwm = len(vwm_trials)
            n_nonguess = int(n_total_vwm * (1 - guess_rate))
            
            if n_nonguess > 0:
                # Sort trials by error and take the n_nonguess best trials
                # This is a deterministic approach to identifying non-guess trials
                nonguess_trials = vwm_trials.sort_values(
                    by='VWM_error_absolute_degrees',
                    ascending=True
                ).head(n_nonguess)

                result['vwm_mean_accuracy_nonguess'] = nonguess_trials['VWM_error_absolute_degrees'].mean()
                print(f"  VWM mean accuracy (non-guess, deterministic): {result['vwm_mean_accuracy_nonguess']:.2f} degrees")
            else:
                result['vwm_mean_accuracy_nonguess'] = np.nan
                print("  No non-guess trials estimated")
            
            # 2. Calculate VWM response time coefficient of variation
            vwm_rt_mean = vwm_trials['VWM_rt_ms'].mean()
            vwm_rt_std = vwm_trials['VWM_rt_ms'].std()
            result['vwm_rt_cv'] = vwm_rt_std / vwm_rt_mean if vwm_rt_mean > 0 else np.nan
            print(f"  VWM RT CV: {result['vwm_rt_cv']:.3f}")
            
            # VWM timeout rate
            result['vwm_timeout_rate'] = vwm_trials['VWM_timeout'].mean()
            print(f"  VWM timeout rate: {result['vwm_timeout_rate']:.3f}")
            
            result['n_vwm_trials_used'] = len(vwm_trials)
        else:
            result['vwm_mean_accuracy_nonguess'] = np.nan
            result['vwm_rt_cv'] = np.nan
            result['vwm_timeout_rate'] = np.nan
            result['n_vwm_trials_used'] = 0
            print("  No VWM test trials found")
        
        # 3. Calculate MRT response time coefficient of variation
        if len(mrt_trials) > 0:
            mrt_rt_mean = mrt_trials['MRT_rt_ms'].mean()
            mrt_rt_std = mrt_trials['MRT_rt_ms'].std()
            result['mrt_rt_cv'] = mrt_rt_std / mrt_rt_mean if mrt_rt_mean > 0 else np.nan
            print(f"  MRT RT CV: {result['mrt_rt_cv']:.3f}")
            
            # MRT timeout rate
            result['mrt_timeout_rate'] = mrt_trials['MRT_timeout'].mean()
            print(f"  MRT timeout rate: {result['mrt_timeout_rate']:.3f}")
            
            result['n_mrt_trials_used'] = len(mrt_trials)
        else:
            result['mrt_rt_cv'] = np.nan
            result['mrt_timeout_rate'] = np.nan
            result['n_mrt_trials_used'] = 0
            print("  No MRT test trials found")
        
        # 4. Extract focus loss metrics (these should be consistent across all rows for a participant)
        result['focus_loss_instances_instructions'] = participant_data['windowFocusLostDuringInfoNum'].dropna().iloc[0] if not participant_data['windowFocusLostDuringInfoNum'].dropna().empty else 0
        result['focus_loss_instances_tasks'] = participant_data['windowFocusLostDuringTasksNum'].dropna().iloc[0] if not participant_data['windowFocusLostDuringTasksNum'].dropna().empty else 0
        result['focus_loss_duration_instructions_ms'] = participant_data['windowFocusLostDuringInfoDuration'].dropna().iloc[0] if not participant_data['windowFocusLostDuringInfoDuration'].dropna().empty else 0
        result['focus_loss_duration_tasks_ms'] = participant_data['windowFocusLostDuringTasksDuration'].dropna().iloc[0] if not participant_data['windowFocusLostDuringTasksDuration'].dropna().empty else 0
        
        print(f"  Focus loss instances (instructions): {result['focus_loss_instances_instructions']}")
        print(f"  Focus loss instances (tasks): {result['focus_loss_instances_tasks']}")
        print(f"  Focus loss duration (instructions): {result['focus_loss_duration_instructions_ms']} ms")
        print(f"  Focus loss duration (tasks): {result['focus_loss_duration_tasks_ms']} ms")
        
        results.append(result)
    
    # Convert to DataFrame
    results_df = pd.DataFrame(results)
    print(f"\nCalculated metrics for {len(results_df)} participants")
    
    # Validate focus loss and timeout data
    print("\nValidating focus loss and timeout data...")

    # Check if all focus loss values are zero
    all_focus_zero = (
        (results_df['focus_loss_instances_instructions'] == 0).all() and
        (results_df['focus_loss_instances_tasks'] == 0).all() and
        (results_df['focus_loss_duration_instructions_ms'] == 0).all() and
        (results_df['focus_loss_duration_tasks_ms'] == 0).all()
    )

    all_timeout_zero = (
        (results_df['vwm_timeout_rate'] == 0).all() and
        (results_df['mrt_timeout_rate'] == 0).all()
    )

    if all_focus_zero:
        print("WARNING: All focus loss metrics are zero across all participants")
        print("This may indicate data collection issues or that focus loss was not captured")

    if all_timeout_zero:
        print("WARNING: All timeout rates are zero across all participants")
        print("This may indicate data collection issues or very lenient timeout settings")

    # 6. Create engagement index
    print("\nCalculating engagement index...")

    # Calculate combined focus loss instances, handling missing data robustly
    combined_focus_loss = (
        results_df['focus_loss_instances_tasks'].fillna(0) +
        results_df['focus_loss_instances_instructions'].fillna(0)
    )

    # Calculate combined timeout rates, handling missing data robustly
    combined_timeout_rate = (
        results_df['vwm_timeout_rate'].fillna(0) +
        results_df['mrt_timeout_rate'].fillna(0)
    )

    # Check for zero variance before standardization
    focus_loss_std = combined_focus_loss.std()
    timeout_rate_std = combined_timeout_rate.std()

    if focus_loss_std == 0 and timeout_rate_std == 0:
        print("WARNING: Both focus loss and timeout measures have zero variance")
        print("Setting engagement index to 0 for all participants (no variation to measure)")
        results_df['engagement_index'] = 0.0
    elif focus_loss_std == 0:
        print("WARNING: Focus loss has zero variance, using only timeout rate for engagement index")
        results_df['engagement_index'] = standardize_values(combined_timeout_rate)
    elif timeout_rate_std == 0:
        print("WARNING: Timeout rate has zero variance, using only focus loss for engagement index")
        results_df['engagement_index'] = standardize_values(combined_focus_loss)
    else:
        # Standard calculation when both measures have variance
        z_focus_loss = standardize_values(combined_focus_loss)
        z_timeout_rate = standardize_values(combined_timeout_rate)
        results_df['engagement_index'] = z_focus_loss + z_timeout_rate

    print("Engagement index calculation completed")
    print(f"Engagement index range: {results_df['engagement_index'].min():.3f} to {results_df['engagement_index'].max():.3f}")

    return results_df

def validate_data(data, required_columns):
    """
    Validate that required columns exist in the data.
    
    Parameters:
    -----------
    data : pandas.DataFrame
        Data to validate
    required_columns : list
        List of required column names
    
    Returns:
    --------
    bool
        True if all required columns exist, False otherwise
    """
    missing_columns = [col for col in required_columns if col not in data.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        return False
    
    print("All required columns present")
    return True

def main():
    """
    Main function to execute the control variables calculation.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("=" * 60)
        print("CONTROL VARIABLES CALCULATION SCRIPT")
        print("=" * 60)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Outputs directory ready")
        
        # Find input files
        print("\nSearching for input files...")
        
        # Find cleaned trial data file
        trial_data_pattern = 'outputs/cleaned_trial_data_*.csv'
        trial_data_file = get_latest_file(trial_data_pattern)
        
        if trial_data_file is None:
            print(f"ERROR: No files found matching pattern: {trial_data_pattern}")
            return 1
        
        print(f"Found trial data file: {trial_data_file}")
        
        # Find mixture model parameters file
        mixture_params_pattern = 'outputs/mixture_model_parameters_*.csv'
        mixture_params_file = get_latest_file(mixture_params_pattern)
        
        if mixture_params_file is None:
            print(f"ERROR: No files found matching pattern: {mixture_params_pattern}")
            return 1
        
        print(f"Found mixture model parameters file: {mixture_params_file}")
        
        # Load data files
        print("\nLoading data files...")
        
        # Load trial data
        print(f"Reading trial data from: {trial_data_file}")
        trial_data = pd.read_csv(trial_data_file)
        trial_data.columns = trial_data.columns.str.strip()
        print(f"Trial data shape: {trial_data.shape}")
        print("Trial data columns:", trial_data.columns.tolist())
        print("First 3 rows of trial data:")
        print(trial_data.head(3))
        
        # Load mixture model parameters
        print(f"\nReading mixture model parameters from: {mixture_params_file}")
        mixture_params = pd.read_csv(mixture_params_file)
        mixture_params.columns = mixture_params.columns.str.strip()
        print(f"Mixture model parameters shape: {mixture_params.shape}")
        print("Mixture model parameters columns:", mixture_params.columns.tolist())
        print("First 3 rows of mixture model parameters:")
        print(mixture_params.head(3))
        
        # Validate required columns
        print("\nValidating required columns...")
        
        trial_required_columns = [
            'participantId', 'table', 'isPractice', 'VWM_error_absolute_degrees',
            'VWM_rt_ms', 'VWM_timeout', 'MRT_rt_ms', 'MRT_timeout',
            'windowFocusLostDuringTasksNum', 'windowFocusLostDuringInfoNum',
            'windowFocusLostDuringTasksDuration', 'windowFocusLostDuringInfoDuration'
        ]
        
        mixture_required_columns = ['participantId', 'guess_rate_vonmises']
        
        if not validate_data(trial_data, trial_required_columns):
            return 1
        
        if not validate_data(mixture_params, mixture_required_columns):
            return 1
        
        # Print unique values for key experimental design columns
        print("\nExperimental design parameter values:")
        print(f"table unique values: {sorted(trial_data['table'].unique())}")
        print(f"isPractice unique values: {sorted(trial_data['isPractice'].unique())}")
        
        # Print data types for measured variables
        print("\nMeasured variable data types:")
        print(f"VWM_error_absolute_degrees type: {trial_data['VWM_error_absolute_degrees'].dtype}")
        print(f"VWM_rt_ms type: {trial_data['VWM_rt_ms'].dtype}")
        print(f"MRT_rt_ms type: {trial_data['MRT_rt_ms'].dtype}")
        print(f"guess_rate_vonmises type: {mixture_params['guess_rate_vonmises'].dtype}")
        
        # Calculate control variables
        print("\n" + "="*50)
        print("CALCULATING CONTROL VARIABLES")
        print("="*50)
        
        results = calculate_control_variables(trial_data, mixture_params)
        
        # Quality control checks
        print("\n" + "="*50)
        print("QUALITY CONTROL CHECKS")
        print("="*50)
        
        print(f"Total participants processed: {len(results)}")
        
        # Check for missing data
        for col in results.columns:
            if col != 'participantId':
                missing_count = results[col].isna().sum()
                print(f"{col}: {missing_count} missing values ({missing_count/len(results)*100:.1f}%)")
        
        # Check ranges
        print("\nMetric ranges:")
        numeric_columns = ['vwm_mean_accuracy_nonguess', 'vwm_rt_cv', 'mrt_rt_cv', 
                          'vwm_timeout_rate', 'mrt_timeout_rate', 'engagement_index']
        
        for col in numeric_columns:
            if col in results.columns:
                valid_values = results[col].dropna()
                if len(valid_values) > 0:
                    print(f"{col}: {valid_values.min():.3f} to {valid_values.max():.3f}")
        
        # Display final results
        print("\n" + "="*50)
        print("FINAL RESULTS SUMMARY")
        print("="*50)
        
        print("Results columns:", results.columns.tolist())
        print("First 2 rows of results:")
        print(results.head(2))
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'outputs/control_variables_{timestamp}.csv'
        
        print(f"\nSaving results to: {output_file}")
        results.to_csv(output_file, index=False)
        
        print(f"Successfully saved {len(results)} participant records")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
