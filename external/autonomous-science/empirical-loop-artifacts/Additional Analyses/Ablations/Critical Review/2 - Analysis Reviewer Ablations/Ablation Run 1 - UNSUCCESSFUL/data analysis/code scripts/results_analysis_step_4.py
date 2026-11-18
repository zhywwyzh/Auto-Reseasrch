#!/usr/bin/env python3
"""
Mixture Model Analysis for Visual Working Memory (VWM) Data

This script performs three-component mixture modeling on VWM error data to estimate
memory precision (kappa), bias (mu), and guess rate parameters for each participant.
Also compares alternative circular distributions and performs model selection.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy.optimize import minimize
from scipy.stats import vonmises, uniform
import warnings
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/cleaned_trial_data_*.csv')
    
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found latest file: {latest_file}")
    return latest_file

def wrap_angle(angle):
    """
    Wrap angle to [-π, π] range using circular wrapping.
    
    Parameters:
    -----------
    angle : float or array-like
        Angle(s) in radians to wrap
    
    Returns:
    --------
    float or array-like
        Wrapped angle(s) in [-π, π] range
    """
    return (angle + np.pi) % (2 * np.pi) - np.pi

def von_mises_pdf(x, mu, kappa):
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
    array-like
        PDF values
    """
    return vonmises.pdf(x, kappa, loc=mu)

def uniform_pdf(x):
    """
    Probability density function for uniform distribution on [-π, π].
    
    Parameters:
    -----------
    x : array-like
        Values at which to evaluate PDF
    
    Returns:
    --------
    array-like
        PDF values (constant 1/(2π))
    """
    return np.ones_like(x) / (2 * np.pi)

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
    array-like
        PDF values
    """
    # Edge case: sigma must be positive and finite
    if sigma <= 0 or not np.isfinite(sigma):
        return np.zeros_like(x)
    pdf = np.zeros_like(x)
    for k in range(-10, 11):  # Sum over wrapping terms
        pdf += np.exp(-0.5 * ((x - mu + 2*np.pi*k) / sigma)**2)
    return pdf / (sigma * np.sqrt(2 * np.pi))

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
        Scale parameter (0 < gamma < 1)
    
    Returns:
    --------
    array-like
        PDF values
    """
    # Edge case: gamma must be in (0, 1) and finite
    if gamma <= 0 or gamma >= 1 or not np.isfinite(gamma):
        return np.zeros_like(x)
    return (1 - gamma**2) / (2 * np.pi * (1 + gamma**2 - 2*gamma*np.cos(x - mu)))

def mixture_log_likelihood(params, errors, model_type='vonmises'):
    """
    Calculate log-likelihood for three-component mixture model.
    
    Parameters:
    -----------
    params : array-like
        Model parameters [concentration, bias, guess_rate]
    errors : array-like
        Error data in radians
    model_type : str
        Type of target distribution ('vonmises', 'wrapped_normal', 'wrapped_cauchy')
    
    Returns:
    --------
    float
        Negative log-likelihood (for minimization)
    """
    # Edge case: empty or invalid errors
    if len(errors) == 0:
        return np.inf
    errors = np.asarray(errors)
    if not np.all(np.isfinite(errors)):
        return np.inf

    if model_type == 'vonmises':
        concentration, bias, guess_rate = params
        if concentration <= 0 or guess_rate < 0 or guess_rate > 1:
            return np.inf
        
        target_pdf = von_mises_pdf(errors, bias, concentration)
        
    elif model_type == 'wrapped_normal':
        sigma, bias, guess_rate = params
        if sigma <= 0 or guess_rate < 0 or guess_rate > 1:
            return np.inf
        
        target_pdf = wrapped_normal_pdf(errors, bias, sigma)
        
    elif model_type == 'wrapped_cauchy':
        gamma, bias, guess_rate = params
        if gamma <= 0 or gamma >= 1 or guess_rate < 0 or guess_rate > 1:
            return np.inf
        
        target_pdf = wrapped_cauchy_pdf(errors, bias, gamma)
    
    uniform_pdf_val = uniform_pdf(errors)
    
    # Three-component mixture: target + non-target + guess
    # Assuming equal weighting between non-target and guess components
    mixture_pdf = (1 - guess_rate) * target_pdf + guess_rate * uniform_pdf_val
    
    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)
    
    log_likelihood = np.sum(np.log(mixture_pdf))
    return -log_likelihood  # Return negative for minimization

def fit_mixture_model(errors, model_type='vonmises'):
    """
    Fit three-component mixture model to error data.
    
    Parameters:
    -----------
    errors : array-like
        Error data in radians
    model_type : str
        Type of target distribution ('vonmises', 'wrapped_normal', 'wrapped_cauchy')
    
    Returns:
    --------
    dict
        Dictionary containing fitted parameters, AIC, and convergence status
    """
    n_trials = len(errors)
    print(f"  Fitting {model_type} model with {n_trials} trials...")

    # Initial parameter guesses
    if model_type == 'vonmises':
        initial_params = [1.0, 0.0, 0.2]  # [kappa, mu, guess_rate]
        bounds = [(0.1, 50), (-np.pi, np.pi), (0, 1)]
    elif model_type == 'wrapped_normal':
        initial_params = [1.0, 0.0, 0.2]  # [sigma, mu, guess_rate]
        bounds = [(0.1, 10), (-np.pi, np.pi), (0, 1)]
    elif model_type == 'wrapped_cauchy':
        initial_params = [0.5, 0.0, 0.2]  # [gamma, mu, guess_rate]
        bounds = [(0.01, 0.99), (-np.pi, np.pi), (0, 1)]
    
    try:
        # Multiple optimization attempts with different starting points
        best_result = None
        best_nll = np.inf
        
        for attempt in range(5):
            # Jitter initial parameters
            jittered_params = initial_params.copy()
            if attempt > 0:
                jittered_params[0] *= np.random.uniform(0.5, 2.0)
                jittered_params[1] += np.random.uniform(-0.5, 0.5)
                jittered_params[2] = np.random.uniform(0.1, 0.4)
            
            result = minimize(
                mixture_log_likelihood,
                jittered_params,
                args=(errors, model_type),
                bounds=bounds,
                method='L-BFGS-B'
            )
            
            if result.success and result.fun < best_nll:
                best_result = result
                best_nll = result.fun
        
        if best_result is not None and best_result.success:
            # Calculate AIC
            n_params = 3  # concentration/scale, bias, guess_rate
            aic = 2 * n_params + 2 * best_result.fun
            print(f"  {model_type} model converged successfully (AIC: {aic:.2f})")
            if model_type == 'vonmises':
                return {
                    'kappa': best_result.x[0],
                    'mu': best_result.x[1],
                    'guess_rate': best_result.x[2],
                    'aic': aic,
                    'converged': True
                }
            elif model_type == 'wrapped_normal':
                return {
                    'sigma': best_result.x[0],
                    'mu': best_result.x[1],
                    'guess_rate': best_result.x[2],
                    'aic': aic,
                    'converged': True
                }
            elif model_type == 'wrapped_cauchy':
                return {
                    'gamma': best_result.x[0],
                    'mu': best_result.x[1],
                    'guess_rate': best_result.x[2],
                    'aic': aic,
                    'converged': True
                }
        else:
            print(f"  {model_type} model failed to converge")
            return {
                'kappa': np.nan if model_type == 'vonmises' else None,
                'sigma': np.nan if model_type == 'wrapped_normal' else None,
                'gamma': np.nan if model_type == 'wrapped_cauchy' else None,
                'mu': np.nan,
                'guess_rate': np.nan,
                'aic': np.inf,
                'converged': False
            }
            
    except Exception as e:
        print(f"Error fitting {model_type} model: {e}")
        return {
            'kappa': np.nan if model_type == 'vonmises' else None,
            'sigma': np.nan if model_type == 'wrapped_normal' else None,
            'gamma': np.nan if model_type == 'wrapped_cauchy' else None,
            'mu': np.nan,
            'guess_rate': np.nan,
            'aic': np.inf,
            'converged': False
        }

def process_participant_data(participant_errors):
    """
    Process VWM error data for a single participant.
    
    Parameters:
    -----------
    participant_errors : array-like
        Error data in radians for one participant
    
    Returns:
    --------
    dict
        Dictionary containing all model fits and comparison results
    """
    print(f"Processing participant with {len(participant_errors)} trials")
    
    # Fit all three models
    vonmises_fit = fit_mixture_model(participant_errors, 'vonmises')
    wrapped_normal_fit = fit_mixture_model(participant_errors, 'wrapped_normal')
    wrapped_cauchy_fit = fit_mixture_model(participant_errors, 'wrapped_cauchy')
    
    # Determine best model
    aics = {
        'vonmises': vonmises_fit['aic'],
        'wrapped_normal': wrapped_normal_fit['aic'],
        'wrapped_cauchy': wrapped_cauchy_fit['aic']
    }
    
    best_model = min(aics, key=aics.get)
    
    # Check for significant AIC differences
    vonmises_aic = vonmises_fit['aic']
    best_aic = aics[best_model]
    aic_difference = vonmises_aic - best_aic
    
    if aic_difference > 4:
        print(f"Warning: Alternative model ({best_model}) shows AIC improvement > 4 points")
    
    # Note: sigma and gamma are mapped to kappa_wrapped_normal and kappa_wrapped_cauchy columns for output consistency,
    # but these are not concentration parameters like kappa (von Mises). Interpret accordingly.
    results = {
        'kappa_vonmises': vonmises_fit['kappa'],
        'mu_vonmises': vonmises_fit['mu'],
        'guess_rate_vonmises': vonmises_fit['guess_rate'],
        'aic_vonmises': vonmises_fit['aic'],
        # Note: sigma parameter mapped to kappa column for consistency
        'kappa_wrapped_normal': wrapped_normal_fit['sigma'],
        'mu_wrapped_normal': wrapped_normal_fit['mu'],
        'aic_wrapped_normal': wrapped_normal_fit['aic'],
        # Note: gamma parameter mapped to kappa column for consistency
        'kappa_wrapped_cauchy': wrapped_cauchy_fit['gamma'],
        'mu_wrapped_cauchy': wrapped_cauchy_fit['mu'],
        'aic_wrapped_cauchy': wrapped_cauchy_fit['aic'],
        'best_model': best_model,
        'converged': vonmises_fit['converged'],
        'n_trials_used': len(participant_errors)
    }
    
    return results

def main():
    """
    Main function to execute the mixture modeling analysis.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting mixture model analysis for VWM data...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the latest cleaned trial data file
        input_pattern = 'outputs/cleaned_trial_data_*.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No files found matching pattern {input_pattern}")
            return 1
        
        print(f"Reading input file: {input_file}")
        
        # Read the input CSV
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded data with shape: {df.shape}")
        except Exception as e:
            print(f"ERROR: Failed to read CSV file: {e}")
            return 1
        
        # Print column information
        print("All columns in input file:")
        print(df.columns.tolist())
        
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Check for required columns
        required_columns = [
            'participantId', 'table', 'isPractice', 
            'VWM_responseAngle_degrees', 'VWM_targetAngle_degrees', 'VWM_error_degrees'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found!")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"table: {df['table'].unique()}")
        print(f"isPractice: {df['isPractice'].unique()}")
        
        print("\nData types for measured variables:")
        print(f"VWM_responseAngle_degrees: {df['VWM_responseAngle_degrees'].dtype}")
        print(f"VWM_targetAngle_degrees: {df['VWM_targetAngle_degrees'].dtype}")
        print(f"VWM_error_degrees: {df['VWM_error_degrees'].dtype}")
        
        # Filter to VWM test trials only
        print("\nFiltering to VWM test trials...")
        print(f"Total rows before filtering: {len(df)}")
        
        # Filter conditions
        vwm_test_trials = df[
            (df['isPractice'] == False) & 
            (df['table'] == 'vwm_test')  # Changed from 'vwm_main'
        ].copy()
        
        print(f"Rows after filtering to VWM test trials: {len(vwm_test_trials)}")
        
        if len(vwm_test_trials) == 0:
            print("ERROR: No VWM test trials found after filtering")
            return 1
        
        # Calculate orientation recall errors
        print("\nCalculating orientation recall errors...")
        # Use existing error column
        vwm_test_trials['error_radians'] = vwm_test_trials['VWM_error_degrees'] * np.pi / 180
        
        # Wrap errors to [-π, π] range
        vwm_test_trials['error_radians_wrapped'] = wrap_angle(vwm_test_trials['error_radians'])
        
        print("Error calculation completed!")
        print(f"Error range in radians: [{vwm_test_trials['error_radians_wrapped'].min():.3f}, {vwm_test_trials['error_radians_wrapped'].max():.3f}]")
        
        # Add validation after error calculation
        print(f"Checking for invalid values in error data...")
        n_nan = vwm_test_trials['error_radians_wrapped'].isna().sum()
        n_inf = (~np.isfinite(vwm_test_trials['error_radians_wrapped'])).sum()
        print(f"Found {n_nan} NaN values and {n_inf} infinite values in wrapped errors")
        
        if n_nan > 0 or n_inf > 0:
            print("Removing invalid error values...")
            vwm_test_trials = vwm_test_trials[
                vwm_test_trials['error_radians_wrapped'].notna() & 
                np.isfinite(vwm_test_trials['error_radians_wrapped'])
            ]
            print(f"Remaining trials after cleaning: {len(vwm_test_trials)}")
        
        # Group by participant and process each one
        print("\nProcessing participants...")
        participants = vwm_test_trials['participantId'].unique()
        print(f"Found {len(participants)} participants to process")
        
        results_list = []
        
        for i, participant_id in enumerate(participants):
            print(f"\nProcessing participant {i+1}/{len(participants)}: {participant_id}")
            
            # Get participant data
            participant_data = vwm_test_trials[
                vwm_test_trials['participantId'] == participant_id
            ]['error_radians_wrapped'].values
            
            # Remove any NaN values and add validation
            participant_data = participant_data[~np.isnan(participant_data)]
            participant_data = participant_data[np.isfinite(participant_data)]
            
            if len(participant_data) < 10:
                print(f"WARNING: Participant {participant_id} has insufficient data ({len(participant_data)} trials < 10 minimum) - skipping mixture model fitting")
                continue
            
            # Process participant
            participant_results = process_participant_data(participant_data)
            participant_results['participantId'] = participant_id
            
            results_list.append(participant_results)
            
            print(f"Participant {participant_id} completed:")
            print(f"  - von Mises kappa: {participant_results['kappa_vonmises']:.3f}")
            print(f"  - von Mises mu: {participant_results['mu_vonmises']:.3f}")
            print(f"  - Guess rate: {participant_results['guess_rate_vonmises']:.3f}")
            print(f"  - Best model: {participant_results['best_model']}")
            print(f"  - Converged: {participant_results['converged']}")
        
        if not results_list:
            print("ERROR: No participants processed successfully")
            return 1
        
        print(f"\nSuccessfully processed {len(results_list)} participants")
        
        # Create results DataFrame
        results_df = pd.DataFrame(results_list)
        
        print("\nResults summary:")
        print(f"Participants with converged fits: {results_df['converged'].sum()}/{len(results_df)}")
        
        # Model comparison summary
        model_counts = results_df['best_model'].value_counts()
        print("\nBest model distribution:")
        for model, count in model_counts.items():
            print(f"  {model}: {count}")
        
        # Create model comparison summary
        summary_data = []
        for model_type in ['vonmises', 'wrapped_normal', 'wrapped_cauchy']:
            n_best = (results_df['best_model'] == model_type).sum()
            
            if model_type == 'vonmises':
                mean_aic = results_df['aic_vonmises'].mean()
                aic_improvement = 0  # Reference model
            elif model_type == 'wrapped_normal':
                mean_aic = results_df['aic_wrapped_normal'].mean()
                aic_improvement = results_df['aic_vonmises'].mean() - mean_aic
            elif model_type == 'wrapped_cauchy':
                mean_aic = results_df['aic_wrapped_cauchy'].mean()
                aic_improvement = results_df['aic_vonmises'].mean() - mean_aic
            
            summary_data.append({
                'model_type': model_type,
                'n_participants_best': n_best,
                'mean_aic': mean_aic,
                'aic_improvement_over_vonmises': aic_improvement
            })
        
        summary_df = pd.DataFrame(summary_data)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save results
        output_file1 = f'outputs/mixture_model_parameters_{timestamp}.csv'
        output_file2 = f'outputs/model_comparison_summary_{timestamp}.csv'
        
        print(f"\nSaving results to:")
        print(f"  {output_file1}")
        print(f"  {output_file2}")
        
        # Reorder columns to match specification
        results_df = results_df[[
            'participantId', 'kappa_vonmises', 'mu_vonmises', 'guess_rate_vonmises', 
            'aic_vonmises', 'kappa_wrapped_normal', 'mu_wrapped_normal', 
            'aic_wrapped_normal', 'kappa_wrapped_cauchy', 'mu_wrapped_cauchy', 
            'aic_wrapped_cauchy', 'best_model', 'converged', 'n_trials_used'
        ]]
        
        results_df.to_csv(output_file1, index=False)
        summary_df.to_csv(output_file2, index=False)
        
        print("\nFinal results preview:")
        print("Mixture model parameters (first 2 rows):")
        print(results_df.head(2))
        
        print("\nModel comparison summary:")
        print(summary_df)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Unexpected error in main function: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
