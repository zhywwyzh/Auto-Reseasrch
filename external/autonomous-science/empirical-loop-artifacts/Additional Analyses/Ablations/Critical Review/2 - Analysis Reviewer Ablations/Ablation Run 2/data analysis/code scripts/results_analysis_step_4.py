#!/usr/bin/env python3
"""
Visual Working Memory (VWM) Mixture Model Analysis Script

This script processes VWM trial data and fits three-component mixture models
using von Mises, wrapped normal, and wrapped Cauchy distributions to estimate
memory precision, bias, and guess rates for each participant.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats, special
from scipy.optimize import minimize

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/trial_level_cleaned_data_*.csv')
        
    Returns:
    --------
    str or None
        Path to the most recent file matching pattern, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def wrap_circular_errors(errors_rad):
    """
    Wrap circular errors to [-π, π] range.
    
    Parameters:
    -----------
    errors_rad : array-like
        Errors in radians
        
    Returns:
    --------
    numpy.ndarray
        Wrapped errors in [-π, π] range
    """
    return ((errors_rad + np.pi) % (2 * np.pi)) - np.pi

def vonmises_pdf(x, mu, kappa):
    """
    Probability density function for von Mises distribution.
    
    Parameters:
    -----------
    x : array-like
        Values at which to evaluate PDF
    mu : float
        Mean direction parameter
    kappa : float
        Concentration parameter
        
    Returns:
    --------
    numpy.ndarray
        PDF values
    """
    return np.exp(kappa * np.cos(x - mu)) / (2 * np.pi * special.iv(0, kappa))

def wrapped_normal_pdf(x, mu, sigma):
    """
    Probability density function for wrapped normal distribution.
    
    Parameters:
    -----------
    x : array-like
        Values at which to evaluate PDF
    mu : float
        Mean parameter
    sigma : float
        Standard deviation parameter
        
    Returns:
    --------
    numpy.ndarray
        PDF values
    """
    # Sum over wrapping terms (truncated series)
    pdf_vals = np.zeros_like(x)
    for k in range(-5, 6):  # Truncate series for computational efficiency
        pdf_vals += np.exp(-((x - mu + 2*k*np.pi)**2) / (2*sigma**2))
    return pdf_vals / (sigma * np.sqrt(2*np.pi))

def wrapped_cauchy_pdf(x, mu, gamma):
    """
    Probability density function for wrapped Cauchy distribution.
    
    Parameters:
    -----------
    x : array-like
        Values at which to evaluate PDF
    mu : float
        Location parameter
    gamma : float
        Scale parameter
        
    Returns:
    --------
    numpy.ndarray
        PDF values
    """
    # Convert to complex representation for wrapped Cauchy
    rho = np.exp(-gamma)
    return (1 - rho**2) / (2*np.pi * (1 + rho**2 - 2*rho*np.cos(x - mu)))

def mixture_likelihood_vonmises(params, errors):
    """
    Calculate negative log-likelihood for three-component von Mises mixture model.

    Parameters:
    -----------
    params : array-like
        [kappa, mu, p_target, p_uniform] where:
        - kappa: concentration parameter
        - mu: bias parameter
        - p_target: proportion of target responses
        - p_uniform: proportion of uniform responses
        (guess rate = 1 - p_target - p_uniform)
    errors : array-like
        Circular error values in radians

    Returns:
    --------
    float
        Negative log-likelihood
    """
    kappa, mu, p_target, p_uniform = params

    # Ensure valid parameters and constraint
    if (
        kappa < 0
        or p_target < 0 or p_target > 1
        or p_uniform < 0 or p_uniform > 1
        or (p_target + p_uniform > 1)
    ):
        return np.inf

    p_guess = 1 - p_target - p_uniform

    # Component likelihoods
    target_pdf = vonmises_pdf(errors, mu, kappa)
    uniform_pdf = 1 / (2 * np.pi)  # Uniform on circle

    # Mixture likelihood (target + uniform + guess)
    mixture_pdf = p_target * target_pdf + p_uniform * uniform_pdf + p_guess * uniform_pdf

    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)

    return -np.sum(np.log(mixture_pdf))

def mixture_likelihood_wrapped_normal(params, errors):
    """
    Calculate negative log-likelihood for three-component wrapped normal mixture model.

    Parameters:
    -----------
    params : array-like
        [sigma, mu, p_target, p_uniform] where:
        - sigma: standard deviation parameter
        - mu: bias parameter
        - p_target: proportion of target responses
        - p_uniform: proportion of uniform responses
        (guess rate = 1 - p_target - p_uniform)
    errors : array-like
        Circular error values in radians

    Returns:
    --------
    float
        Negative log-likelihood
    """
    sigma, mu, p_target, p_uniform = params

    # Ensure valid parameters and constraint
    if (
        sigma <= 0
        or p_target < 0 or p_target > 1
        or p_uniform < 0 or p_uniform > 1
        or (p_target + p_uniform > 1)
    ):
        return np.inf

    p_guess = 1 - p_target - p_uniform

    # Component likelihoods
    target_pdf = wrapped_normal_pdf(errors, mu, sigma)
    uniform_pdf = 1 / (2 * np.pi)

    # Mixture likelihood (target + uniform + guess)
    mixture_pdf = p_target * target_pdf + p_uniform * uniform_pdf + p_guess * uniform_pdf

    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)

    return -np.sum(np.log(mixture_pdf))

def mixture_likelihood_wrapped_cauchy(params, errors):
    """
    Calculate negative log-likelihood for three-component wrapped Cauchy mixture model.

    Parameters:
    -----------
    params : array-like
        [gamma, mu, p_target, p_uniform] where:
        - gamma: scale parameter
        - mu: bias parameter
        - p_target: proportion of target responses
        - p_uniform: proportion of uniform responses
        (guess rate = 1 - p_target - p_uniform)
    errors : array-like
        Circular error values in radians

    Returns:
    --------
    float
        Negative log-likelihood
    """
    gamma, mu, p_target, p_uniform = params

    # Ensure valid parameters and constraint
    if (
        gamma <= 0
        or p_target < 0 or p_target > 1
        or p_uniform < 0 or p_uniform > 1
        or (p_target + p_uniform > 1)
    ):
        return np.inf

    p_guess = 1 - p_target - p_uniform

    # Component likelihoods
    target_pdf = wrapped_cauchy_pdf(errors, mu, gamma)
    uniform_pdf = 1 / (2 * np.pi)

    # Mixture likelihood (target + uniform + guess)
    mixture_pdf = p_target * target_pdf + p_uniform * uniform_pdf + p_guess * uniform_pdf

    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)

    return -np.sum(np.log(mixture_pdf))

def fit_mixture_model(errors, model_type='vonmises', n_starts=5):
    """
    Fit three-component mixture model using multiple random starts.

    Parameters:
    -----------
    errors : array-like
        Circular error values in radians
    model_type : str
        Type of model ('vonmises', 'wrapped_normal', 'wrapped_cauchy')
    n_starts : int
        Number of random starting points for optimization

    Returns:
    --------
    dict
        Dictionary containing fitted parameters, convergence status, and AIC
    """
    best_result = None
    best_nll = np.inf
    converged = False

    # Choose likelihood function and parameter bounds
    if model_type == 'vonmises':
        likelihood_func = mixture_likelihood_vonmises
        bounds = [(0.1, 50), (-np.pi, np.pi), (0.01, 0.98), (0.01, 0.98)]  # kappa, mu, p_target, p_uniform
    elif model_type == 'wrapped_normal':
        likelihood_func = mixture_likelihood_wrapped_normal
        bounds = [(0.1, 5), (-np.pi, np.pi), (0.01, 0.98), (0.01, 0.98)]  # sigma, mu, p_target, p_uniform
    elif model_type == 'wrapped_cauchy':
        likelihood_func = mixture_likelihood_wrapped_cauchy
        bounds = [(0.1, 5), (-np.pi, np.pi), (0.01, 0.98), (0.01, 0.98)]  # gamma, mu, p_target, p_uniform
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Try multiple random starts
    for start in range(n_starts):
        try:
            # Random initial parameters with sum constraint
            for _ in range(100):  # Try up to 100 times to get valid p_target, p_uniform
                if model_type == 'vonmises':
                    param1 = np.random.uniform(0.5, 10)  # kappa
                else:
                    param1 = np.random.uniform(0.5, 2)   # sigma/gamma
                mu = np.random.uniform(-np.pi/4, np.pi/4)
                p_target = np.random.uniform(0.2, 0.7)
                p_uniform = np.random.uniform(0.01, 0.98)
                if p_target + p_uniform < 0.98:
                    break
            else:
                # Fallback if not found
                p_target = 0.5
                p_uniform = 0.2
            init_params = [param1, mu, p_target, p_uniform]

            # Optimize
            result = minimize(
                likelihood_func,
                init_params,
                args=(errors,),
                bounds=bounds,
                method='L-BFGS-B'
            )

            if result.success and result.fun < best_nll:
                best_result = result
                best_nll = result.fun
                converged = True

        except Exception as e:
            print(f"Optimization attempt {start+1} failed: {e}")
            continue

    # Extract results
    if best_result is not None and converged:
        param1, mu, p_target, p_uniform = best_result.x
        guess_rate = 1 - p_target - p_uniform

        # Calculate AIC
        n_params = 4
        aic = 2 * best_nll + 2 * n_params

        return {
            'kappa': param1,
            'mu': mu,
            'guess_rate': guess_rate,
            'convergence': True,
            'aic': aic,
            'nll': best_nll
        }
    else:
        return {
            'kappa': np.nan,
            'mu': np.nan,
            'guess_rate': np.nan,
            'convergence': False,
            'aic': np.nan,
            'nll': np.nan
        }

def main():
    """
    Main function to process VWM data and fit mixture models.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting VWM Mixture Model Analysis")
        print("=" * 50)
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find input file
        input_pattern = 'outputs/trial_level_cleaned_data_*.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input file found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read input data
        print("Reading input data...")
        try:
            data = pd.read_csv(input_file)
            print(f"Successfully loaded data with shape: {data.shape}")
        except Exception as e:
            print(f"ERROR reading input file: {e}")
            return 1
        
        # Print column information
        print(f"Columns in dataset: {list(data.columns)}")
        print("First 3 rows of data:")
        print(data.head(3))
        
        # Check required columns
        required_columns = [
            'participantId', 'isPractice', 'VWM_trial', 'VWM_responseAngle_degrees',
            'VWM_targetAngle_degrees', 'VWM_error_degrees', 'VWM_trial_excluded',
            'participant_meets_minimum_trials'
        ]
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found")
        
        # Print unique values for key experimental design columns
        print("\nUnique values for key columns:")
        print(f"isPractice: {sorted(data['isPractice'].unique())}")
        print(f"participant_meets_minimum_trials: {sorted(data['participant_meets_minimum_trials'].unique())}")
        print(f"VWM_trial_excluded: {sorted(data['VWM_trial_excluded'].unique())}")
        
        # Check data types for measured variables
        print(f"VWM_error_degrees data type: {data['VWM_error_degrees'].dtype}")
        print(f"VWM_responseAngle_degrees data type: {data['VWM_responseAngle_degrees'].dtype}")
        print(f"VWM_targetAngle_degrees data type: {data['VWM_targetAngle_degrees'].dtype}")
        
        # Filter to participants meeting minimum trial requirements
        print(f"\nTotal participants before filtering: {data['participantId'].nunique()}")
        data_filtered = data[data['participant_meets_minimum_trials'] == True].copy()
        print(f"Participants meeting minimum trials: {data_filtered['participantId'].nunique()}")
        
        if len(data_filtered) == 0:
            print("ERROR: No participants meet minimum trial requirements")
            return 1
        
        # Filter to test trials only
        print(f"Total trials before practice filter: {len(data_filtered)}")
        data_filtered = data_filtered[data_filtered['isPractice'] == False].copy()
        print(f"Test trials only: {len(data_filtered)}")
        
        # Filter to valid VWM trials
        data_filtered = data_filtered[data_filtered['VWM_trial'].notna()].copy()
        print(f"Valid VWM trials: {len(data_filtered)}")
        
        # Exclude flagged trials
        data_filtered = data_filtered[data_filtered['VWM_trial_excluded'] == False].copy()
        print(f"Non-excluded trials: {len(data_filtered)}")
        
        if len(data_filtered) == 0:
            print("ERROR: No valid trials remaining after filtering")
            return 1
        
        # Convert errors to radians and wrap
        print("\nConverting errors to radians and wrapping...")
        data_filtered['VWM_error_radians'] = data_filtered['VWM_error_degrees'] * np.pi / 180
        data_filtered['VWM_error_wrapped'] = wrap_circular_errors(data_filtered['VWM_error_radians'])
        
        print(f"Error range in degrees: {data_filtered['VWM_error_degrees'].min():.2f} to {data_filtered['VWM_error_degrees'].max():.2f}")
        print(f"Error range in wrapped radians: {data_filtered['VWM_error_wrapped'].min():.2f} to {data_filtered['VWM_error_wrapped'].max():.2f}")
        
        # Group by participant
        participants = data_filtered['participantId'].unique()
        print(f"\nProcessing {len(participants)} participants...")
        
        # Initialize results storage
        results = []
        
        # Fit models for each participant
        for i, participant in enumerate(participants):
            print(f"\nProcessing participant {participant} ({i+1}/{len(participants)})...")
            
            # Get participant data
            participant_data = data_filtered[data_filtered['participantId'] == participant]
            errors = participant_data['VWM_error_wrapped'].values
            
            print(f"  Trials for this participant: {len(errors)}")
            
            if len(errors) < 10:  # Minimum trials for stable fitting
                print(f"  WARNING: Too few trials ({len(errors)}) for participant {participant}")
                continue
            
            # Initialize result dictionary
            result = {'participantId': participant, 'total_trials_used': len(errors)}
            
            # Fit von Mises model
            print("  Fitting von Mises model...")
            vm_result = fit_mixture_model(errors, 'vonmises')
            result.update({
                'kappa_vonmises': vm_result['kappa'],
                'mu_vonmises': vm_result['mu'],
                'guess_rate_vonmises': vm_result['guess_rate'],
                'AIC_vonmises': vm_result['aic'],
                'vonmises_convergence': vm_result['convergence']
            })

            # Fit wrapped normal model
            print("  Fitting wrapped normal model...")
            wn_result = fit_mixture_model(errors, 'wrapped_normal')
            result.update({
                'kappa_wrapped_normal': wn_result['kappa'],
                'mu_wrapped_normal': wn_result['mu'],
                'guess_rate_wrapped_normal': wn_result['guess_rate'],
                'AIC_wrapped_normal': wn_result['aic'],
                'wrapped_normal_convergence': wn_result['convergence']
            })

            # Fit wrapped Cauchy model
            print("  Fitting wrapped Cauchy model...")
            wc_result = fit_mixture_model(errors, 'wrapped_cauchy')
            result.update({
                'kappa_wrapped_cauchy': wc_result['kappa'],
                'mu_wrapped_cauchy': wc_result['mu'],
                'guess_rate_wrapped_cauchy': wc_result['guess_rate'],
                'AIC_wrapped_cauchy': wc_result['aic'],
                'wrapped_cauchy_convergence': wc_result['convergence']
            })
            
            # Determine best model
            aics = {
                'vonmises': vm_result['aic'],
                'wrapped_normal': wn_result['aic'],
                'wrapped_cauchy': wc_result['aic']
            }
            
            # Find best model (lowest AIC, excluding NaN)
            valid_aics = {k: v for k, v in aics.items() if not np.isnan(v)}
            if valid_aics:
                best_model = min(valid_aics, key=valid_aics.get)
            else:
                best_model = 'none_converged'
            
            result['best_model'] = best_model
            
            print(f"  Best model: {best_model}")
            if valid_aics:
                print(f"  AICs - von Mises: {aics['vonmises']:.2f}, Wrapped Normal: {aics['wrapped_normal']:.2f}, Wrapped Cauchy: {aics['wrapped_cauchy']:.2f}")

            results.append(result)
        
        # Convert results to DataFrame
        print(f"\nCreating results DataFrame with {len(results)} participants...")
        results_df = pd.DataFrame(results)
        
        print("Results summary:")
        print(f"Participants with results: {len(results_df)}")
        print(f"Von Mises convergence rate: {results_df['vonmises_convergence'].sum()}/{len(results_df)} ({100*results_df['vonmises_convergence'].mean():.1f}%)")
        print(f"Wrapped Normal convergence rate: {results_df['wrapped_normal_convergence'].sum()}/{len(results_df)} ({100*results_df['wrapped_normal_convergence'].mean():.1f}%)")
        print(f"Wrapped Cauchy convergence rate: {results_df['wrapped_cauchy_convergence'].sum()}/{len(results_df)} ({100*results_df['wrapped_cauchy_convergence'].mean():.1f}%)")
        
        # Print best model distribution
        print("\nBest model distribution:")
        print(results_df['best_model'].value_counts())
        
        # Print first two rows of results
        print("\nFirst 2 rows of results:")
        print("Columns:", list(results_df.columns))
        print(results_df.head(2))
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'outputs/vwm_mixture_model_parameters_{timestamp}.csv'
        
        print(f"\nSaving results to: {output_file}")
        results_df.to_csv(output_file, index=False)
        
        print(f"Successfully saved {len(results_df)} participant results")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
