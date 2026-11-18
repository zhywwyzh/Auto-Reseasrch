import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

from scipy.stats import vonmises
from scipy.optimize import minimize

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to most recent file matching pattern, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def load_input_data():
    """
    Load the most recent VWM cleaned data file.
    
    Returns:
    pd.DataFrame: Loaded data with required columns
    """
    print("=" * 50)
    print("LOADING INPUT DATA")
    print("=" * 50)
    
    # Find the most recent VWM cleaned data file
    pattern = "outputs/VWM_cleaned_data_*.csv"
    input_file = find_most_recent_file(pattern)
    
    if input_file is None:
        print(f"No files found matching pattern: {pattern}")
        sys.exit(1)
    
    print(f"Loading input file: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"Successfully loaded data with shape: {df.shape}")
        
        # Print all columns
        print(f"All columns: {list(df.columns)}")
        
        # Print first 3 rows
        print("First 3 rows:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'VWM_normalized_error_degrees', 'excluded', 'exclusion_reason']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            sys.exit(1)
        
        print(f"All required columns present: {required_columns}")
        
        # Print unique values for key columns
        print(f"Unique values in 'excluded' column: {df['excluded'].unique()}")
        print(f"Unique values in 'exclusion_reason' column: {df['exclusion_reason'].unique()}")
        print(f"VWM_normalized_error_degrees data type: {df['VWM_normalized_error_degrees'].dtype}")
        
        return df
        
    except Exception as e:
        print(f"Error loading input file: {e}")
        sys.exit(1)

def filter_non_excluded_participants(df):
    """
    Filter to include only participants not excluded in previous steps.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    pd.DataFrame: Filtered dataframe with only non-excluded participants
    """
    print("=" * 50)
    print("FILTERING NON-EXCLUDED PARTICIPANTS")
    print("=" * 50)
    
    print(f"Initial data shape: {df.shape}")
    print(f"Total participants before filtering: {df['participantId'].nunique()}")
    
    # Filter for non-excluded participants (excluded == False)
    df_filtered = df[df['excluded'] == False].copy()
    
    print(f"Data shape after filtering excluded participants: {df_filtered.shape}")
    print(f"Total participants after filtering: {df_filtered['participantId'].nunique()}")
    
    # Print first 2 rows of filtered data
    print("First 2 rows after filtering:")
    print(df_filtered.head(2))
    
    return df_filtered

def apply_technical_exclusions(df):
    """
    Apply technical exclusions based on valid trial count.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    
    Returns:
    tuple: (filtered_df, exclusion_log)
    """
    print("=" * 50)
    print("APPLYING TECHNICAL EXCLUSIONS")
    print("=" * 50)
    
    exclusion_log = []
    
    # Count valid trials per participant
    print("Counting valid trials per participant...")
    trial_counts = df.groupby('participantId').size()
    print(f"Trial counts calculated for {len(trial_counts)} participants")
    print(f"Trial count statistics:")
    print(f"  Mean: {trial_counts.mean():.2f}")
    print(f"  Median: {trial_counts.median():.2f}")
    print(f"  Min: {trial_counts.min()}")
    print(f"  Max: {trial_counts.max()}")
    
    # Identify participants with < 20 valid trials
    insufficient_data_participants = trial_counts[trial_counts < 20].index.tolist()
    print(f"Participants with < 20 valid trials: {len(insufficient_data_participants)}")
    
    # Exclude participants with insufficient data
    df_filtered = df[~df['participantId'].isin(insufficient_data_participants)].copy()
    
    print(f"Data shape after technical exclusions: {df_filtered.shape}")
    print(f"Remaining participants: {df_filtered['participantId'].nunique()}")
    
    # Log exclusion
    exclusion_log.append({
        'exclusion_criteria': 'Insufficient valid trials (< 20)',
        'total_excluded': len(insufficient_data_participants)
    })
    
    return df_filtered, exclusion_log

def neg_log_likelihood(params, data):
    """Negative log-likelihood for von Mises + uniform mixture model"""
    mu, kappa, p_vm = params

    # Parameter bounds checking
    if kappa <= 0 or p_vm <= 0 or p_vm >= 1:
        return np.inf

    # von Mises component
    vm_pdf = vonmises.pdf(data, kappa, loc=mu)

    # Uniform component (on circle: 1/(2π))
    uniform_pdf = 1.0 / (2 * np.pi)

    # Mixture likelihood
    mixture_pdf = p_vm * vm_pdf + (1 - p_vm) * uniform_pdf

    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)

    return -np.sum(np.log(mixture_pdf))

def circular_mean(angles):
    """Calculate circular mean of angles in radians"""
    return np.arctan2(np.mean(np.sin(angles)), np.mean(np.cos(angles)))

def fit_mixture_models(df):
    """
    Fit von Mises + uniform mixture models for each participant using scipy.
    """
    print("=" * 50)
    print("FITTING MIXTURE MODELS (Python/scipy implementation)")
    print("=" * 50)

    participants = df['participantId'].unique()
    print(f"Fitting circular mixture models for {len(participants)} participants")

    results = []
    convergence_failures = []
    low_kappa_exclusions = []
    low_precision_exclusions = []

    for i, participant in enumerate(participants):
        if (i + 1) % 10 == 0:
            print(f"Processing participant {i + 1}/{len(participants)}")

        # Get participant data and convert to radians
        participant_data = df[df['participantId'] == participant]['VWM_normalized_error_degrees'].values
        participant_data_rad = np.deg2rad(participant_data)

        # Initial parameter guesses
        mu_init = circular_mean(participant_data_rad)
        kappa_init = 2.0
        p_vm_init = 0.7

        best_fit = None
        best_log_lik = -np.inf

        # Try multiple starting points for robustness
        for attempt in range(5):
            if attempt == 0:
                start_params = [mu_init, kappa_init, p_vm_init]
            else:
                start_params = [
                    np.random.uniform(-np.pi, np.pi),  # mu
                    np.random.uniform(1, 10),          # kappa
                    np.random.uniform(0.5, 0.9)        # p_vm
                ]

            bounds = [(-np.inf, np.inf), (1e-6, 100), (1e-6, 1-1e-6)]

            try:
                res = minimize(
                    neg_log_likelihood,
                    start_params,
                    args=(participant_data_rad,),
                    method='L-BFGS-B',
                    bounds=bounds
                )
                if res.success:
                    log_lik = -res.fun
                    if log_lik > best_log_lik:
                        best_log_lik = log_lik
                        best_fit = res
            except Exception as e:
                continue

        if best_fit is None or not best_fit.success:
            print(f"Modeling error for participant {participant}: Optimization failed")
            convergence_failures.append(participant)
            results.append({
                'participantId': participant,
                'kappa': np.nan,
                'mu': np.nan,
                'mixture_precision_proportion': np.nan,
                'mixture_guess_proportion': np.nan,
                'model_convergence_status': 'FAILED',
                'aic_value': np.nan,
                'bic_value': np.nan,
                'excluded': True,
                'exclusion_reason': 'Mixture model convergence failure'
            })
            continue

        params = best_fit.x
        mu_rad_unwrapped = float(params[0])
        mu_rad = np.arctan2(np.sin(mu_rad_unwrapped), np.cos(mu_rad_unwrapped))
        kappa = float(params[1])
        precision_prop = float(params[2])
        guess_prop = 1.0 - precision_prop

        mu_degrees = np.rad2deg(mu_rad)

        n_params = 3
        n_trials = len(participant_data)
        aic_val = 2 * n_params - 2 * best_log_lik
        bic_val = n_params * np.log(n_trials) - 2 * best_log_lik

        # Apply model quality exclusions
        excluded = False
        exclusion_reason = 'OK'

        if kappa < 0.1:
            low_kappa_exclusions.append(participant)
            excluded = True
            exclusion_reason = 'Low kappa (< 0.1)'
        elif precision_prop < 0.2:
            low_precision_exclusions.append(participant)
            excluded = True
            exclusion_reason = 'Low precision component proportion (< 20%)'

        results.append({
            'participantId': participant,
            'kappa': kappa,
            'mu': mu_rad,
            'mixture_precision_proportion': precision_prop,
            'mixture_guess_proportion': guess_prop,
            'model_convergence_status': 'SUCCESS',
            'aic_value': aic_val,
            'bic_value': bic_val,
            'excluded': excluded,
            'exclusion_reason': exclusion_reason
        })

    print("=" * 30)
    print("MIXTURE MODEL FITTING SUMMARY")
    print("=" * 30)
    print(f"Total participants processed: {len(participants)}")
    print(f"Convergence failures: {len(convergence_failures)}")
    print(f"Low kappa exclusions: {len(low_kappa_exclusions)}")
    print(f"Low precision component exclusions: {len(low_precision_exclusions)}")

    results_df = pd.DataFrame(results)

    print("First 2 rows of modeling results:")
    print(results_df.head(2))

    print("=" * 30)
    print("DATA VALIDATION")
    print("=" * 30)
    valid_data = results_df[~results_df['excluded']]
    if len(valid_data) > 0:
        # Check kappa parameters are positive
        negative_kappa = (valid_data['kappa'] <= 0).sum()
        print(f"Participants with non-positive kappa: {negative_kappa}")
        
        # Check mu parameters are within -π to +π radians
        mu_out_of_range = ((valid_data['mu'] < -np.pi) | (valid_data['mu'] > np.pi)).sum()
        print(f"Participants with mu outside [-π, π]: {mu_out_of_range}")
        
        # Check mixture proportions sum to 1
        prop_sum_check = np.abs(valid_data['mixture_precision_proportion'] + valid_data['mixture_guess_proportion'] - 1.0) > 1e-6
        prop_sum_errors = prop_sum_check.sum()
        print(f"Participants with mixture proportions not summing to 1: {prop_sum_errors}")

    additional_exclusions = [
        {'exclusion_criteria': 'Mixture model convergence failure', 'total_excluded': len(convergence_failures)},
        {'exclusion_criteria': 'Von Mises fitting failure', 'total_excluded': 0},
        {'exclusion_criteria': 'Low kappa (< 0.1)', 'total_excluded': len(low_kappa_exclusions)},
        {'exclusion_criteria': 'Low precision component proportion (< 20%)', 'total_excluded': len(low_precision_exclusions)}
    ]

    return results_df, additional_exclusions

def save_outputs(results_df, exclusion_log):
    """
    Save the output files with timestamp.
    
    Parameters:
    results_df (pd.DataFrame): Model parameters results
    exclusion_log (list): List of exclusion criteria and counts
    """
    print("=" * 50)
    print("SAVING OUTPUT FILES")
    print("=" * 50)
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save exclusion log
    exclusion_log_file = f"outputs/VWM_modeling_exclusion_log_{timestamp}.csv"
    exclusion_df = pd.DataFrame(exclusion_log)
    exclusion_df.to_csv(exclusion_log_file, index=False)
    print(f"Saved exclusion log to: {exclusion_log_file}")
    print("Exclusion log contents:")
    print(exclusion_df)
    
    # Save model parameters
    model_params_file = f"outputs/VWM_model_parameters_{timestamp}.csv"
    results_df.to_csv(model_params_file, index=False)
    print(f"Saved model parameters to: {model_params_file}")
    print(f"Model parameters shape: {results_df.shape}")
    print("First 2 rows of saved model parameters:")
    print(results_df.head(2))
    
    # Summary statistics
    total_participants = len(results_df)
    excluded_participants = results_df['excluded'].sum()
    valid_participants = total_participants - excluded_participants
    
    print("=" * 30)
    print("FINAL SUMMARY")
    print("=" * 30)
    print(f"Total participants processed: {total_participants}")
    print(f"Excluded participants: {excluded_participants}")
    print(f"Valid participants for analysis: {valid_participants}")
    
    if valid_participants > 0:
        valid_results = results_df[~results_df['excluded']]
        print(f"Kappa statistics for valid participants:")
        print(f"  Mean: {valid_results['kappa'].mean():.4f}")
        print(f"  Median: {valid_results['kappa'].median():.4f}")
        print(f"  Min: {valid_results['kappa'].min():.4f}")
        print(f"  Max: {valid_results['kappa'].max():.4f}")

def main():
    """
    Main execution function for VWM mixture modeling analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM mixture modeling analysis...")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load input data
        df = load_input_data()
        
        # Filter non-excluded participants
        df_filtered = filter_non_excluded_participants(df)
        
        # Apply technical exclusions
        df_technical, exclusion_log = apply_technical_exclusions(df_filtered)
        
        # Fit mixture models
        results_df, additional_exclusions = fit_mixture_models(df_technical)
        
        # Combine all exclusions
        all_exclusions = exclusion_log + additional_exclusions
        
        # Save outputs
        save_outputs(results_df, all_exclusions)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
