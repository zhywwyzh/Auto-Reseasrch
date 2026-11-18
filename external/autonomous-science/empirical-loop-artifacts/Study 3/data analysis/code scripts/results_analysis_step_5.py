import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
from scipy.stats import vonmises

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

def calculate_posterior_probabilities(error_degrees, guess_rate, vonmises_kappa, mu=0):
    """
    Calculate posterior probabilities for guess vs non-guess trials using mixture model.
    
    Parameters:
    error_degrees (array): Array of error values in degrees
    guess_rate (float): Fitted guess rate parameter
    vonmises_kappa (float): Fitted von Mises concentration parameter
    mu (float): Mean of von Mises distribution (default 0)
    
    Returns:
    array: Posterior probabilities of guess component for each trial
    """
    # Convert degrees to radians
    error_radians = np.deg2rad(error_degrees)
    
    # Calculate likelihood for uniform (guess) component
    uniform_likelihood = 1 / np.pi
    
    # Calculate likelihood for von Mises (non-guess) component
    vonmises_likelihood = vonmises.pdf(error_radians, kappa=vonmises_kappa, loc=mu)
    
    # Calculate posterior probabilities using Bayes' theorem
    numerator = guess_rate * uniform_likelihood
    denominator = guess_rate * uniform_likelihood + (1 - guess_rate) * vonmises_likelihood
    
    posterior_guess = numerator / denominator
    
    return posterior_guess

def calculate_z_scores(values):
    """
    Calculate z-scores for an array of values.
    
    Parameters:
    values (array): Array of numeric values
    
    Returns:
    array: Z-scores for the input values
    """
    mean_val = np.mean(values)
    std_val = np.std(values, ddof=1)
    if std_val == 0:
        return np.zeros_like(values)
    return (values - mean_val) / std_val

def time_to_milliseconds(time_str):
    """
    Convert time string to milliseconds.
    
    Parameters:
    time_str: Time string in HH:MM:SS format or numeric value
    
    Returns:
    float: Time in milliseconds, NaN for invalid/empty values
    """
    if pd.isna(time_str):
        return np.nan

    if isinstance(time_str, (int, float)):
        return float(time_str)

    if isinstance(time_str, str):
        if time_str == "00:00:00" or time_str.strip() == "":
            return 0.0

        try:
            # Parse HH:MM:SS format
            parts = time_str.split(':')
            if len(parts) == 3:
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2])
                total_seconds = hours * 3600 + minutes * 60 + seconds
                return total_seconds * 1000  # Convert to milliseconds
        except (ValueError, IndexError):
            pass

    return np.nan

def main():
    """
    Main function to process control variables from trial data and mixture model parameters.
    """
    try:
        print("Starting control variables calculation...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input files
        print("Looking for input files...")
        trial_data_pattern = 'outputs/cleaned_trial_data_*.csv'
        mixture_model_pattern = 'outputs/mixture_model_parameters_*.csv'
        
        trial_data_file = find_latest_file(trial_data_pattern)
        mixture_model_file = find_latest_file(mixture_model_pattern)
        
        if trial_data_file is None:
            print(f"ERROR: No trial data file found matching pattern: {trial_data_pattern}")
            return 1
        
        if mixture_model_file is None:
            print(f"ERROR: No mixture model file found matching pattern: {mixture_model_pattern}")
            return 1
        
        print(f"Found trial data file: {trial_data_file}")
        print(f"Found mixture model file: {mixture_model_file}")
        
        # Read input files
        print("Reading trial data file...")
        trial_data = pd.read_csv(trial_data_file)
        print(f"Trial data shape: {trial_data.shape}")
        print("Trial data columns:", list(trial_data.columns))
        print("First 3 rows of trial data:")
        print(trial_data.head(3))

        # Skip duration columns conversion to preserve time string format
        print("Converting duration columns to numeric format...")
        # duration_cols = ['windowFocusLostDuringTasksDuration', 'windowFocusLostDuringInfoDuration']
        # for col in duration_cols:
        #     trial_data[col] = pd.to_numeric(trial_data[col], errors='coerce')
        print("Duration columns conversion skipped to preserve time string format")
        
        print("\nReading mixture model file...")
        mixture_params = pd.read_csv(mixture_model_file)
        print(f"Mixture model shape: {mixture_params.shape}")
        print("Mixture model columns:", list(mixture_params.columns))
        print("First 3 rows of mixture model:")
        print(mixture_params.head(3))
        
        # Validate required columns
        required_trial_cols = [
            'participantId', 'isPractice', 'VWM_error_absolute_degrees', 
            'VWM_rt_ms', 'VWM_timeout', 'MRT_rt_ms', 'MRT_timeout',
            'windowFocusLostDuringTasksNum', 'windowFocusLostDuringInfoNum',
            'windowFocusLostDuringTasksDuration', 'windowFocusLostDuringInfoDuration',
            'trial_excluded', 'table'
        ]
        
        required_mixture_cols = ['participantId', 'guess_rate', 'convergence_status']
        
        missing_trial_cols = [col for col in required_trial_cols if col not in trial_data.columns]
        missing_mixture_cols = [col for col in required_mixture_cols if col not in mixture_params.columns]
        
        if missing_trial_cols:
            print(f"ERROR: Missing required columns in trial data: {missing_trial_cols}")
            return 1
        
        if missing_mixture_cols:
            print(f"ERROR: Missing required columns in mixture model: {missing_mixture_cols}")
            return 1
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"isPractice: {sorted(trial_data['isPractice'].unique())}")
        print(f"trial_excluded: {sorted(trial_data['trial_excluded'].unique())}")
        print(f"VWM_timeout: {sorted(trial_data['VWM_timeout'].unique())}")
        print(f"MRT_timeout: {sorted(trial_data['MRT_timeout'].unique())}")
        print(f"table: {sorted(trial_data['table'].unique())}")
        print(f"convergence_status: {sorted(mixture_params['convergence_status'].unique())}")
        
        # Print data types for measured variables
        print("\nData types for measured variables:")
        print(f"VWM_error_absolute_degrees: {trial_data['VWM_error_absolute_degrees'].dtype}")
        print(f"VWM_rt_ms: {trial_data['VWM_rt_ms'].dtype}")
        print(f"MRT_rt_ms: {trial_data['MRT_rt_ms'].dtype}")
        print(f"guess_rate: {mixture_params['guess_rate'].dtype}")
        
        # Filter for valid test trials
        print("\nFiltering for valid test trials...")
        test_trials = trial_data[
            (trial_data['isPractice'] == False) & 
            (trial_data['trial_excluded'] == False)
        ].copy()
        
        print(f"Total trials: {len(trial_data)}")
        print(f"Valid test trials: {len(test_trials)}")
        
        # Get participants with valid convergence
        print("\nFiltering participants with valid convergence...")
        valid_participants = mixture_params[
            mixture_params['convergence_status'] == True
        ]['participantId'].unique()
        
        print(f"Total participants in mixture model: {len(mixture_params)}")
        print(f"Participants with valid convergence: {len(valid_participants)}")
        
        # Initialize results dataframe
        all_participants = trial_data['participantId'].unique()
        results = pd.DataFrame({
            'participantId': all_participants
        })
        
        print(f"Total unique participants in trial data: {len(all_participants)}")
        
        # Merge with mixture model parameters
        results = results.merge(mixture_params[['participantId', 'guess_rate', 'convergence_status']], 
                               on='participantId', how='left')
        
        # Initialize result columns
        results['VWM_mean_accuracy_nonguess'] = np.nan
        results['VWM_rt_cv'] = np.nan
        results['MRT_rt_cv'] = np.nan
        results['focus_loss_instances_tasks'] = np.nan
        results['focus_loss_instances_instructions'] = np.nan
        results['focus_loss_duration_tasks_ms'] = np.nan
        results['focus_loss_duration_instructions_ms'] = np.nan
        results['VWM_timeout_rate'] = np.nan
        results['MRT_timeout_rate'] = np.nan
        results['engagement_index'] = np.nan
        results['valid_for_analysis'] = False
        
        print("\nProcessing each participant...")
        
        for idx, participant_id in enumerate(all_participants):
            print(f"Processing participant {idx+1}/{len(all_participants)}: {participant_id}")
            
            # Get participant data
            participant_trials = test_trials[test_trials['participantId'] == participant_id].copy()
            participant_mixture = mixture_params[mixture_params['participantId'] == participant_id]
            
            if len(participant_trials) == 0:
                print(f"  No valid test trials for participant {participant_id}")
                continue
            
            if len(participant_mixture) == 0:
                print(f"  No mixture model data for participant {participant_id}")
                continue
            
            convergence_status = participant_mixture['convergence_status'].iloc[0]
            if not convergence_status:
                print(f"  Participant {participant_id} has convergence_status=False, skipping")
                continue
            
            guess_rate = participant_mixture['guess_rate'].iloc[0]
            
            # Check if we have vonMises_kappa in mixture model data
            if 'vonMises_kappa' in mixture_params.columns:
                vonmises_kappa = participant_mixture['vonMises_kappa'].iloc[0]
            else:
                # Use a default value if not available
                vonmises_kappa = 1.0
                print(f"  Warning: vonMises_kappa not found, using default value of 1.0")
            
            # 1. Calculate VWM mean accuracy for non-guess trials
            vwm_trials = participant_trials[participant_trials['table'] == 'vwm_test'].copy()
            vwm_trial_count = len(vwm_trials)
            mrt_trial_count = len(participant_trials[participant_trials['table'] == 'mrt_test'])

            if vwm_trial_count == 0:
                print(f"  Warning: No VWM test trials found for participant {participant_id}")
            if mrt_trial_count == 0:
                print(f"  Warning: No MRT test trials found for participant {participant_id}")

            if vwm_trial_count > 0:
                # Calculate posterior probabilities
                # Use signed error for posterior calculation, but store mean absolute error
                vwm_error_col = 'VWM_error_degrees'
                if vwm_error_col not in vwm_trials.columns:
                    print(f"  Warning: VWM_error_degrees column not found for participant {participant_id}")
                else:
                    valid_vwm_errors = vwm_trials[vwm_error_col].dropna()
                    if len(valid_vwm_errors) > 0:
                        posterior_guess = calculate_posterior_probabilities(
                            valid_vwm_errors.values, guess_rate, vonmises_kappa
                        )
                        # Classify trials as non-guess (posterior probability < 0.5)
                        non_guess_mask = posterior_guess < 0.5
                        non_guess_indices = valid_vwm_errors.index[non_guess_mask]
                        
                        if len(non_guess_indices) > 0:
                            # Calculate mean from the absolute error column for the identified trials
                            mean_abs_error = vwm_trials.loc[non_guess_indices, 'VWM_error_absolute_degrees'].mean()
                            results.loc[results['participantId'] == participant_id, 'VWM_mean_accuracy_nonguess'] = mean_abs_error
                            print(f"  VWM non-guess trials: {len(non_guess_indices)}/{len(valid_vwm_errors)}")
            
            # 2. Calculate response time coefficients of variation
            # VWM RT CV
            vwm_rt_trials = participant_trials[
                (participant_trials['table'] == 'vwm_test') & 
                (participant_trials['VWM_timeout'] == False) &
                (participant_trials['VWM_rt_ms'].notna())
            ]
            
            if len(vwm_rt_trials) > 0:
                vwm_rts = vwm_rt_trials['VWM_rt_ms'].values
                if len(vwm_rts) > 1:
                    vwm_rt_mean = np.mean(vwm_rts)
                    vwm_rt_std = np.std(vwm_rts, ddof=1)
                    if vwm_rt_mean > 0:
                        results.loc[results['participantId'] == participant_id, 'VWM_rt_cv'] = vwm_rt_std / vwm_rt_mean
            
            # MRT RT CV
            mrt_rt_trials = participant_trials[
                (participant_trials['table'] == 'mrt_test') & 
                (participant_trials['MRT_timeout'] == False) &
                (participant_trials['MRT_rt_ms'].notna())
            ]
            
            if len(mrt_rt_trials) > 0:
                mrt_rts = mrt_rt_trials['MRT_rt_ms'].values
                if len(mrt_rts) > 1:
                    mrt_rt_mean = np.mean(mrt_rts)
                    mrt_rt_std = np.std(mrt_rts, ddof=1)
                    if mrt_rt_mean > 0:
                        results.loc[results['participantId'] == participant_id, 'MRT_rt_cv'] = mrt_rt_std / mrt_rt_mean
            
            # 3. Extract focus loss metrics from metadata row in original trial_data
            meta_row = trial_data[(trial_data['participantId'] == participant_id) & (trial_data['table'] == 'metadata')]
            if not meta_row.empty:
                print(f"  Focus loss values for participant {participant_id}:")
                print(f"    windowFocusLostDuringTasksNum: {meta_row.iloc[0]['windowFocusLostDuringTasksNum']}")
                print(f"    windowFocusLostDuringInfoNum: {meta_row.iloc[0]['windowFocusLostDuringInfoNum']}")
                print(f"    windowFocusLostDuringTasksDuration: {meta_row.iloc[0]['windowFocusLostDuringTasksDuration']}")
                print(f"    windowFocusLostDuringInfoDuration: {meta_row.iloc[0]['windowFocusLostDuringInfoDuration']}")
                results.loc[results['participantId'] == participant_id, 'focus_loss_instances_tasks'] = meta_row.iloc[0]['windowFocusLostDuringTasksNum']
                results.loc[results['participantId'] == participant_id, 'focus_loss_instances_instructions'] = meta_row.iloc[0]['windowFocusLostDuringInfoNum']
                # Assign duration using time_to_milliseconds directly on the original string
                results.loc[results['participantId'] == participant_id, 'focus_loss_duration_tasks_ms'] = time_to_milliseconds(meta_row.iloc[0]['windowFocusLostDuringTasksDuration'])
                results.loc[results['participantId'] == participant_id, 'focus_loss_duration_instructions_ms'] = time_to_milliseconds(meta_row.iloc[0]['windowFocusLostDuringInfoDuration'])
            else:
                print(f"  Warning: No metadata row found for participant {participant_id}")
            
            # 4. Calculate timeout rates
            # VWM timeout rate
            vwm_all_trials = participant_trials[participant_trials['table'] == 'vwm_test']
            if len(vwm_all_trials) > 0:
                vwm_timeout_count = (vwm_all_trials['VWM_timeout'] == True).sum()
                vwm_timeout_rate = vwm_timeout_count / len(vwm_all_trials)
                results.loc[results['participantId'] == participant_id, 'VWM_timeout_rate'] = vwm_timeout_rate
            
            # MRT timeout rate
            mrt_all_trials = participant_trials[participant_trials['table'] == 'mrt_test']
            if len(mrt_all_trials) > 0:
                mrt_timeout_count = (mrt_all_trials['MRT_timeout'] == True).sum()
                mrt_timeout_rate = mrt_timeout_count / len(mrt_all_trials)
                results.loc[results['participantId'] == participant_id, 'MRT_timeout_rate'] = mrt_timeout_rate
        
        print("\nCalculating engagement index...")
        
        # 5. Create engagement index
        # Calculate total focus loss instances
        results['total_focus_loss'] = (
            results['focus_loss_instances_tasks'].fillna(0) + 
            results['focus_loss_instances_instructions'].fillna(0)
        )
        
        # Calculate total timeout rate
        results['total_timeout_rate'] = (
            results['VWM_timeout_rate'].fillna(0) + 
            results['MRT_timeout_rate'].fillna(0)
        )
        
        # Calculate z-scores for engagement components
        valid_focus_loss = results['total_focus_loss'].dropna()
        valid_timeout_rate = results['total_timeout_rate'].dropna()
        
        if len(valid_focus_loss) > 1:
            focus_loss_z = calculate_z_scores(valid_focus_loss)
            results.loc[results['total_focus_loss'].notna(), 'focus_loss_z'] = focus_loss_z
        else:
            results['focus_loss_z'] = 0
        
        if len(valid_timeout_rate) > 1:
            timeout_z = calculate_z_scores(valid_timeout_rate)
            results.loc[results['total_timeout_rate'].notna(), 'timeout_z'] = timeout_z
        else:
            results['timeout_z'] = 0
        
        # Sum standardized components
        results['engagement_raw'] = results['focus_loss_z'].fillna(0) + results['timeout_z'].fillna(0)
        
        # Final z-score standardization
        valid_engagement_raw = results['engagement_raw'].dropna()
        if len(valid_engagement_raw) > 1:
            engagement_z = calculate_z_scores(valid_engagement_raw)
            results.loc[results['engagement_raw'].notna(), 'engagement_index'] = engagement_z
        else:
            results['engagement_index'] = 0
        
        print("\nPerforming data validation...")
        
        # 6. Data validation and set valid_for_analysis flag
        for idx, row in results.iterrows():
            participant_id = row['participantId']

            # Check convergence status
            if pd.isna(row['convergence_status']) or row['convergence_status'] != True:
                continue

            # Check for critical missing data (but allow zeros)
            critical_missing = (
                pd.isna(row['VWM_mean_accuracy_nonguess']) or
                pd.isna(row['VWM_rt_cv']) or pd.isna(row['MRT_rt_cv']) or
                pd.isna(row['focus_loss_instances_tasks']) or pd.isna(row['focus_loss_instances_instructions']) or
                pd.isna(row['engagement_index'])
            )

            if critical_missing:
                continue

            # Validate CV values are positive and finite
            if row['VWM_rt_cv'] < 0 or not np.isfinite(row['VWM_rt_cv']):
                continue
            if row['MRT_rt_cv'] < 0 or not np.isfinite(row['MRT_rt_cv']):
                continue

            # Validate timeout rates are between 0 and 1
            if not (0 <= row['VWM_timeout_rate'] <= 1):
                continue
            if not (0 <= row['MRT_timeout_rate'] <= 1):
                continue

            # Validate focus loss metrics are non-negative (allow NaN)
            if row['focus_loss_instances_tasks'] < 0 or row['focus_loss_instances_instructions'] < 0:
                continue
            if (pd.notna(row['focus_loss_duration_tasks_ms']) and row['focus_loss_duration_tasks_ms'] < 0) or \
               (pd.notna(row['focus_loss_duration_instructions_ms']) and row['focus_loss_duration_instructions_ms'] < 0):
                continue

            # If all checks pass, mark as valid
            results.loc[idx, 'valid_for_analysis'] = True
        
        # Clean up temporary columns
        results = results.drop(columns=['convergence_status', 'guess_rate', 'total_focus_loss', 
                                       'total_timeout_rate', 'focus_loss_z', 'timeout_z', 'engagement_raw'])
        
        print("\nFinal results summary:")
        print(f"Total participants: {len(results)}")
        print(f"Valid for analysis: {results['valid_for_analysis'].sum()}")
        print(f"Invalid for analysis: {(~results['valid_for_analysis']).sum()}")
        
        # Print summary statistics
        print("\nSummary statistics for valid participants:")
        valid_results = results[results['valid_for_analysis'] == True]
        if len(valid_results) > 0:
            numeric_cols = ['VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 'MRT_rt_cv', 
                           'VWM_timeout_rate', 'MRT_timeout_rate', 'engagement_index']
            for col in numeric_cols:
                values = valid_results[col].dropna()
                if len(values) > 0:
                    print(f"  {col}: mean={values.mean():.3f}, std={values.std():.3f}, n={len(values)}")
        
        print("\nFirst 2 rows of results:")
        print(results.head(2))
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'outputs/control_variables_{timestamp}.csv'
        
        print(f"\nSaving results to: {output_file}")
        results.to_csv(output_file, index=False)
        
        print("Control variables calculation completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
