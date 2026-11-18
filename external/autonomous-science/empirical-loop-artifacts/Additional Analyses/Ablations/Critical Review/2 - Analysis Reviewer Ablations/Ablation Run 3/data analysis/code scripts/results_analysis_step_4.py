#!/usr/bin/env python3
"""
Visual Working Memory Mixture Model Analysis Script

This script analyzes visual working memory data by fitting three-component mixture models
to orientation error data for each participant. It compares von Mises, wrapped normal,
and wrapped Cauchy distributions for the target component.
"""

import os
import sys
import glob
import numpy as np
import pandas as pd
from datetime import datetime
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., "outputs/vwm_cleaned_trials_*.csv")
    
    Returns:
    --------
    str or None
        Path to the most recent file matching pattern, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def wrap_to_pi(angles):
    """
    Wrap angles to [-π, π] range using circular arithmetic.
    
    Parameters:
    -----------
    angles : array-like
        Angles in radians
    
    Returns:
    --------
    numpy.ndarray
        Angles wrapped to [-π, π] range
    """
    return np.arctan2(np.sin(angles), np.cos(angles))

def von_mises_pdf(x, mu, kappa):
    """
    Probability density function for von Mises distribution.
    
    Parameters:
    -----------
    x : array-like
        Angles in radians
    mu : float
        Mean direction parameter
    kappa : float
        Concentration parameter
    
    Returns:
    --------
    numpy.ndarray
        PDF values
    """
    return stats.vonmises.pdf(x, kappa, loc=mu)

def wrapped_normal_pdf(x, mu, sigma):
    """
    Probability density function for wrapped normal distribution.
    
    Parameters:
    -----------
    x : array-like
        Angles in radians
    mu : float
        Mean parameter
    sigma : float
        Standard deviation parameter
    
    Returns:
    --------
    numpy.ndarray
        PDF values
    """
    # Wrapped normal approximation using series expansion
    pdf_vals = np.zeros_like(x)
    for k in range(-3, 4):  # Sum over several wrapping terms
        pdf_vals += stats.norm.pdf(x + 2*np.pi*k, loc=mu, scale=sigma)
    return pdf_vals

def wrapped_cauchy_pdf(x, mu, gamma):
    """
    Probability density function for wrapped Cauchy distribution.
    
    Parameters:
    -----------
    x : array-like
        Angles in radians
    mu : float
        Location parameter
    gamma : float
        Scale parameter
    
    Returns:
    --------
    numpy.ndarray
        PDF values
    """
    # Wrapped Cauchy formula
    sinh_gamma = np.sinh(gamma)
    cosh_gamma = np.cosh(gamma)
    return sinh_gamma / (2 * np.pi * (cosh_gamma - np.cos(x - mu)))

def three_component_mixture_loglik(params, errors, model_type='von_mises'):
    """
    Log-likelihood for three-component mixture model (target + guess + non-target).
    Parameters:
    -----------
    params : list or array
        [mu, concentration, guess_rate, non_target_rate]
    errors : array-like
        Error angles in radians
    model_type : str
        Type of target distribution ('von_mises', 'wrapped_normal', 'wrapped_cauchy')
    Returns:
    --------
    float
        Negative log-likelihood
    """
    if model_type == 'von_mises':
        mu, kappa, guess_rate, non_target_rate = params
        if kappa <= 0 or not (0 <= guess_rate < 1) or not (0 <= non_target_rate < 1) or (guess_rate + non_target_rate >= 1):
            return np.inf
        target_rate = 1 - guess_rate - non_target_rate
        target_pdf = von_mises_pdf(errors, mu, kappa)
    elif model_type == 'wrapped_normal':
        mu, sigma, guess_rate, non_target_rate = params
        if sigma <= 0 or not (0 <= guess_rate < 1) or not (0 <= non_target_rate < 1) or (guess_rate + non_target_rate >= 1):
            return np.inf
        target_rate = 1 - guess_rate - non_target_rate
        target_pdf = wrapped_normal_pdf(errors, mu, sigma)
    elif model_type == 'wrapped_cauchy':
        mu, gamma, guess_rate, non_target_rate = params
        if gamma <= 0 or not (0 <= guess_rate < 1) or not (0 <= non_target_rate < 1) or (guess_rate + non_target_rate >= 1):
            return np.inf
        target_rate = 1 - guess_rate - non_target_rate
        target_pdf = wrapped_cauchy_pdf(errors, mu, gamma)
    else:
        return np.inf

    uniform_pdf = 1 / (2 * np.pi)
    mixture_pdf = target_rate * target_pdf + guess_rate * uniform_pdf + non_target_rate * uniform_pdf
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)
    return -np.sum(np.log(mixture_pdf))

def fit_mixture_model(errors, model_type='von_mises', n_starts=10):
    """
    Fit three-component mixture model to error data.

    Parameters:
    -----------
    errors : array-like
        Error angles in radians
    model_type : str
        Type of target distribution
    n_starts : int
        Number of random starting points for optimization

    Returns:
    --------
    dict
        Dictionary containing fitted parameters and model statistics
    """
    best_result = None
    best_loglik = np.inf

    for start in range(n_starts):
        # Generate valid random starting parameters
        while True:
            guess_rate = np.random.uniform(0.05, 0.3)
            non_target_rate = np.random.uniform(0.05, 0.3)
            if guess_rate + non_target_rate < 0.95:
                break

        if model_type == 'von_mises':
            initial_params = [
                np.random.uniform(-0.1, 0.1),  # mu (small bias)
                np.random.uniform(0.5, 5.0),   # kappa
                guess_rate,                    # guess_rate
                non_target_rate                # non_target_rate
            ]
            bounds = [(-np.pi, np.pi), (0.01, 50), (0, 0.99), (0, 0.99)]

        elif model_type == 'wrapped_normal':
            initial_params = [
                np.random.uniform(-0.1, 0.1),  # mu
                np.random.uniform(0.2, 1.0),   # sigma
                guess_rate,                    # guess_rate
                non_target_rate                # non_target_rate
            ]
            bounds = [(-np.pi, np.pi), (0.01, 2), (0, 0.99), (0, 0.99)]

        elif model_type == 'wrapped_cauchy':
            initial_params = [
                np.random.uniform(-0.1, 0.1),  # mu
                np.random.uniform(0.2, 1.0),   # gamma
                guess_rate,                    # guess_rate
                non_target_rate                # non_target_rate
            ]
            bounds = [(-np.pi, np.pi), (0.01, 2), (0, 0.99), (0, 0.99)]

        try:
            result = minimize(
                three_component_mixture_loglik,
                initial_params,
                args=(errors, model_type),
                bounds=bounds,
                method='L-BFGS-B'
            )

            if result.fun < best_loglik:
                best_loglik = result.fun
                best_result = result

        except Exception as e:
            continue

    if best_result is None:
        return {
            'converged': False,
            'params': [np.nan, np.nan, np.nan, np.nan],
            'loglik': np.nan,
            'aic': np.nan
        }

    # Calculate AIC
    n_params = len(best_result.x)
    aic = 2 * n_params + 2 * best_loglik

    return {
        'converged': best_result.success,
        'params': best_result.x,
        'loglik': -best_loglik,
        'aic': aic
    }

def convert_concentration_parameters(param, model_type):
    """
    Convert concentration parameters to equivalent kappa values for comparison.
    
    Parameters:
    -----------
    param : float
        Concentration parameter from fitted model
    model_type : str
        Type of model ('von_mises', 'wrapped_normal', 'wrapped_cauchy')
    
    Returns:
    --------
    float
        Equivalent kappa value
    """
    if model_type == 'von_mises':
        return param  # Already kappa
    elif model_type == 'wrapped_normal':
        # Convert sigma to equivalent kappa (approximate relationship)
        return 1 / (param ** 2)
    elif model_type == 'wrapped_cauchy':
        # Convert gamma to equivalent kappa (approximate relationship)
        return 1 / param
    else:
        return np.nan

def main():
    """
    Main function to execute the mixture model analysis.
    """
    try:
        print("Starting Visual Working Memory Mixture Model Analysis")
        print("=" * 60)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input file
        print("Looking for input file...")
        input_pattern = "outputs/vwm_cleaned_trials_*.csv"
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input file found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read input data
        print("Reading input data...")
        try:
            df = pd.read_csv(input_file)
        except Exception as e:
            print(f"ERROR: Failed to read input file: {e}")
            return 1
        
        print(f"Data shape: {df.shape}")
        print("Columns:", list(df.columns))
        print("First 3 rows:")
        print(df.head(3))
        
        # Check required columns
        required_columns = ['participant_id', 'error_degrees', 'response_angle_degrees', 
                          'target_angle_degrees', 'set_size', 'delay_seconds']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found!")
        
        # Print unique values for experimental design parameters
        print("\nExperimental design parameter values:")
        print(f"Set size unique values: {sorted(df['set_size'].unique())}")
        print(f"Delay seconds unique values: {sorted(df['delay_seconds'].unique())}")
        print(f"Participant IDs count: {df['participant_id'].nunique()}")
        print(f"Error degrees data type: {df['error_degrees'].dtype}")
        print(f"Response angle degrees data type: {df['response_angle_degrees'].dtype}")
        print(f"Target angle degrees data type: {df['target_angle_degrees'].dtype}")
        
        # Convert error degrees to radians
        print("\nConverting error degrees to radians...")
        df['error_radians'] = df['error_degrees'] * np.pi / 180
        
        # Wrap errors to [-π, π] range
        df['error_radians_wrapped'] = wrap_to_pi(df['error_radians'])
        
        # Verify error calculations
        print("Verifying error calculations...")
        calculated_errors = df['response_angle_degrees'] - df['target_angle_degrees']
        # Normalize to ±90 degrees
        calculated_errors = np.where(calculated_errors > 90, calculated_errors - 180, calculated_errors)
        calculated_errors = np.where(calculated_errors < -90, calculated_errors + 180, calculated_errors)
        
        error_diff = np.abs(df['error_degrees'] - calculated_errors)
        print(f"Maximum error calculation difference: {error_diff.max():.6f} degrees")
        
        # Get unique participants
        participants = df['participant_id'].unique()
        print(f"\nProcessing {len(participants)} participants...")
        
        # Initialize results storage
        results = []
        
        # Process each participant
        for i, participant in enumerate(participants):
            print(f"\nProcessing participant {i+1}/{len(participants)}: {participant}")
            
            # Get participant data
            participant_data = df[df['participant_id'] == participant].copy()
            errors = participant_data['error_radians_wrapped'].values
            
            print(f"  Trials: {len(errors)}")
            print(f"  Error range: [{np.min(errors):.3f}, {np.max(errors):.3f}] radians")
            
            # Fit von Mises model
            print("  Fitting von Mises model...")
            vm_result = fit_mixture_model(errors, 'von_mises')
            
            # Fit wrapped normal model
            print("  Fitting wrapped normal model...")
            wn_result = fit_mixture_model(errors, 'wrapped_normal')
            
            # Fit wrapped Cauchy model
            print("  Fitting wrapped Cauchy model...")
            wc_result = fit_mixture_model(errors, 'wrapped_cauchy')
            
            # Determine best model
            aics = {
                'von_mises': vm_result['aic'],
                'wrapped_normal': wn_result['aic'],
                'wrapped_cauchy': wc_result['aic']
            }
            
            best_model = min(aics.keys(), key=lambda k: aics[k] if not np.isnan(aics[k]) else np.inf)
            best_aic = aics[best_model]
            
            # Calculate AIC differences
            aic_differences = {k: v - best_aic for k, v in aics.items() if not np.isnan(v)}
            max_aic_diff = max(aic_differences.values()) if aic_differences else np.nan
            
            # Store results
            result_row = {
                'participant_id': participant,
                'von_mises_kappa': vm_result['params'][1] if vm_result['converged'] else np.nan,
                'von_mises_mu': vm_result['params'][0] if vm_result['converged'] else np.nan,
                'guess_rate': vm_result['params'][2] if vm_result['converged'] else np.nan,
                'non_target_rate': vm_result['params'][3] if vm_result['converged'] else np.nan,
                'von_mises_aic': vm_result['aic'],
                'wrapped_normal_kappa_equiv': convert_concentration_parameters(
                    wn_result['params'][1], 'wrapped_normal') if wn_result['converged'] else np.nan,
                'wrapped_normal_aic': wn_result['aic'],
                'wrapped_cauchy_kappa_equiv': convert_concentration_parameters(
                    wc_result['params'][1], 'wrapped_cauchy') if wc_result['converged'] else np.nan,
                'wrapped_cauchy_aic': wc_result['aic'],
                'best_model': best_model,
                'aic_difference': max_aic_diff,
                'model_converged': vm_result['converged'],
                'log_likelihood': vm_result['loglik'],
                'total_trials_fitted': len(errors)
            }

            results.append(result_row)

            print(f"  von Mises: κ={vm_result['params'][1]:.3f}, AIC={vm_result['aic']:.2f}")
            print(f"  Best model: {best_model}")
        
        # Create results dataframe
        print("\nCreating results dataframe...")
        results_df = pd.DataFrame(results)
        
        print("Results summary:")
        print(f"  Total participants: {len(results_df)}")
        print(f"  Converged fits: {results_df['model_converged'].sum()}")
        print(f"  Best model counts:")
        for model in results_df['best_model'].value_counts().items():
            print(f"    {model[0]}: {model[1]}")
        
        print("\nFirst 2 rows of results:")
        print("All columns:", list(results_df.columns))
        print(results_df.head(2))
        
        # Quality control checks
        print("\nQuality control checks:")
        
        # Check for non-convergent fits
        non_convergent = (~results_df['model_converged']).sum()
        print(f"  Non-convergent fits: {non_convergent}")
        
        # Check parameter bounds
        invalid_kappa = (results_df['von_mises_kappa'] <= 0).sum()
        invalid_guess = ((results_df['guess_rate'] < 0) | (results_df['guess_rate'] > 1)).sum()
        invalid_non_target = ((results_df['non_target_rate'] < 0) | (results_df['non_target_rate'] > 1)).sum()
        invalid_rate_sum = ((results_df['guess_rate'] + results_df['non_target_rate']) >= 1).sum()

        print(f"  Invalid kappa values (≤0): {invalid_kappa}")
        print(f"  Invalid guess rates (outside [0,1]): {invalid_guess}")
        print(f"  Invalid non-target rates (outside [0,1]): {invalid_non_target}")
        print(f"  Invalid rate parameter sums (≥1): {invalid_rate_sum}")
        
        # Check for outlying parameter estimates
        kappa_q95 = results_df['von_mises_kappa'].quantile(0.95)
        high_kappa = (results_df['von_mises_kappa'] > kappa_q95 * 3).sum()
        print(f"  Extremely high kappa values (>3*Q95): {high_kappa}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/vwm_mixture_parameters_{timestamp}.csv"
        
        print(f"\nSaving results to: {output_file}")
        results_df.to_csv(output_file, index=False)
        
        print(f"Results saved successfully!")
        print(f"Output file contains {len(results_df)} rows and {len(results_df.columns)} columns")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Script failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
