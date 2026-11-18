#!/usr/bin/env python3
"""
Model Comparison Script for Visual Working Memory Data

This script compares three mixture models (von Mises, wrapped Normal, wrapped Cauchy)
using leave-one-out cross-validation and WAIC for model selection.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

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

def wrapped_normal_pdf(theta, mu, sigma):
    """
    Calculate probability density for wrapped normal distribution.
    
    Parameters:
    theta (array): Angles in radians
    mu (float): Mean parameter
    sigma (float): Standard deviation parameter
    
    Returns:
    array: Probability densities
    """
    # Use approximation with finite sum of normal distributions
    pdf_sum = np.zeros_like(theta)
    for k in range(-3, 4):  # Sum from k=-3 to k=3 for approximation
        pdf_sum += stats.norm.pdf(theta, mu + 2*np.pi*k, sigma)
    return pdf_sum

def wrapped_cauchy_pdf(theta, mu, rho):
    """
    Calculate probability density for wrapped Cauchy distribution.
    
    Parameters:
    theta (array): Angles in radians
    mu (float): Location parameter
    rho (float): Concentration parameter (0 <= rho < 1)
    
    Returns:
    array: Probability densities
    """
    return (1 - rho**2) / (2 * np.pi * (1 - 2*rho*np.cos(theta - mu) + rho**2))

def von_mises_mixture_loglik(params, theta):
    """
    Calculate log-likelihood for von Mises mixture model.
    
    Parameters:
    params (array): [kappa, mu, p] where p is mixture proportion
    theta (array): Observed angles in radians
    
    Returns:
    float: Negative log-likelihood
    """
    kappa, mu, p = params
    
    # Ensure parameters are in valid range
    if kappa <= 0 or p <= 0 or p >= 1:
        return 1e10
    
    # Von Mises component
    vm_pdf = stats.vonmises.pdf(theta, kappa, loc=mu)
    
    # Uniform component
    uniform_pdf = 1.0 / (2 * np.pi)
    
    # Mixture
    mixture_pdf = p * vm_pdf + (1 - p) * uniform_pdf
    
    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)
    
    return -np.sum(np.log(mixture_pdf))

def wrapped_normal_mixture_loglik(params, theta):
    """
    Calculate log-likelihood for wrapped normal mixture model.
    
    Parameters:
    params (array): [sigma, mu, p] where p is mixture proportion
    theta (array): Observed angles in radians
    
    Returns:
    float: Negative log-likelihood
    """
    sigma, mu, p = params
    
    # Ensure parameters are in valid range
    if sigma <= 0 or p <= 0 or p >= 1:
        return 1e10
    
    # Wrapped normal component
    wn_pdf = wrapped_normal_pdf(theta, mu, sigma)
    
    # Uniform component
    uniform_pdf = 1.0 / (2 * np.pi)
    
    # Mixture
    mixture_pdf = p * wn_pdf + (1 - p) * uniform_pdf
    
    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)
    
    return -np.sum(np.log(mixture_pdf))

def wrapped_cauchy_mixture_loglik(params, theta):
    """
    Calculate log-likelihood for wrapped Cauchy mixture model.
    
    Parameters:
    params (array): [rho, mu, p] where p is mixture proportion
    theta (array): Observed angles in radians
    
    Returns:
    float: Negative log-likelihood
    """
    rho, mu, p = params
    
    # Ensure parameters are in valid range
    if rho <= 0 or rho >= 1 or p <= 0 or p >= 1:
        return 1e10
    
    # Wrapped Cauchy component
    wc_pdf = wrapped_cauchy_pdf(theta, mu, rho)
    
    # Uniform component
    uniform_pdf = 1.0 / (2 * np.pi)
    
    # Mixture
    mixture_pdf = p * wc_pdf + (1 - p) * uniform_pdf
    
    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)
    
    return -np.sum(np.log(mixture_pdf))

def fit_von_mises_mixture(theta, initial_params=None):
    """
    Fit von Mises mixture model to data.
    
    Parameters:
    theta (array): Observed angles in radians
    initial_params (array): Initial parameter values [kappa, mu, p]
    
    Returns:
    dict: Fitted parameters and convergence info
    """
    if initial_params is None:
        # Initialize with more conservative values
        initial_params = [2.0, 0.0, 0.7]
    
    # Bounds: kappa > 0, mu unrestricted, 0 < p < 1
    bounds = [(0.1, 100), (-np.pi, np.pi), (0.01, 0.99)]
    
    try:
        result = minimize(von_mises_mixture_loglik, initial_params, 
                         args=(theta,), bounds=bounds, method='L-BFGS-B')
        
        return {
            'kappa': result.x[0],
            'mu': result.x[1],
            'p': result.x[2],
            'neg_log_lik': result.fun,
            'converged': result.success
        }
    except Exception as e:
        print(f"    Model fitting error: {e}")
        return {
            'kappa': np.nan,
            'mu': np.nan,
            'p': np.nan,
            'neg_log_lik': np.inf,
            'converged': False
        }

def fit_wrapped_normal_mixture(theta, initial_params=None):
    """
    Fit wrapped normal mixture model to data.
    
    Parameters:
    theta (array): Observed angles in radians
    initial_params (array): Initial parameter values [sigma, mu, p]
    
    Returns:
    dict: Fitted parameters and convergence info
    """
    if initial_params is None:
        # Initialize with more conservative values
        initial_params = [1.0, 0.0, 0.7]
    
    # Bounds: sigma > 0, mu unrestricted, 0 < p < 1
    bounds = [(0.01, 5.0), (-np.pi, np.pi), (0.01, 0.99)]
    
    try:
        result = minimize(wrapped_normal_mixture_loglik, initial_params, 
                         args=(theta,), bounds=bounds, method='L-BFGS-B')
        
        return {
            'sigma': result.x[0],
            'mu': result.x[1],
            'p': result.x[2],
            'neg_log_lik': result.fun,
            'converged': result.success,
            'kappa_equivalent': 1.0 / (result.x[0]**2)  # Convert to concentration
        }
    except Exception as e:
        print(f"    Model fitting error: {e}")
        return {
            'sigma': np.nan,
            'mu': np.nan,
            'p': np.nan,
            'neg_log_lik': np.inf,
            'converged': False,
            'kappa_equivalent': np.nan
        }

def fit_wrapped_cauchy_mixture(theta, initial_params=None):
    """
    Fit wrapped Cauchy mixture model to data.
    
    Parameters:
    theta (array): Observed angles in radians
    initial_params (array): Initial parameter values [rho, mu, p]
    
    Returns:
    dict: Fitted parameters and convergence info
    """
    if initial_params is None:
        # Initialize with more conservative values
        initial_params = [0.3, 0.0, 0.7]
    
    # Bounds: 0 < rho < 1, mu unrestricted, 0 < p < 1
    bounds = [(0.01, 0.99), (-np.pi, np.pi), (0.01, 0.99)]
    
    try:
        result = minimize(wrapped_cauchy_mixture_loglik, initial_params, 
                         args=(theta,), bounds=bounds, method='L-BFGS-B')
        
        return {
            'rho': result.x[0],
            'mu': result.x[1],
            'p': result.x[2],
            'neg_log_lik': result.fun,
            'converged': result.success,
            'kappa_equivalent': -2 * np.log(result.x[0])  # Convert to concentration
        }
    except Exception as e:
        print(f"    Model fitting error: {e}")
        return {
            'rho': np.nan,
            'mu': np.nan,
            'p': np.nan,
            'neg_log_lik': np.inf,
            'converged': False,
            'kappa_equivalent': np.nan
        }

def calculate_loo_cv(theta, model_type, n_starts=5):
    """
    Enhanced leave-one-out cross-validation score with robust fitting and error handling.
    
    Parameters:
    theta (array): Observed angles in radians
    model_type (str): 'vonmises', 'wrapped_normal', or 'wrapped_cauchy'
    n_starts (int): Number of random initializations for robust fitting
    
    Returns:
    float: LOO-CV score (higher is better)
    """
    n = len(theta)
    log_likelihoods = []
    penalty = -1e10  # Large negative penalty for failed fits

    def random_init(model_type):
        if model_type == 'vonmises':
            kappa = np.random.uniform(0.5, 10)
            mu = np.random.uniform(-np.pi, np.pi)
            p = np.random.uniform(0.1, 0.95)
            return [kappa, mu, p]
        elif model_type == 'wrapped_normal':
            sigma = np.random.uniform(0.1, 2.0)
            mu = np.random.uniform(-np.pi, np.pi)
            p = np.random.uniform(0.1, 0.95)
            return [sigma, mu, p]
        elif model_type == 'wrapped_cauchy':
            rho = np.random.uniform(0.05, 0.95)
            mu = np.random.uniform(-np.pi, np.pi)
            p = np.random.uniform(0.1, 0.95)
            return [rho, mu, p]
        else:
            raise ValueError("Unknown model_type")

    def fit_with_restarts(train_theta, model_type, n_starts):
        best_fit = None
        best_fun = np.inf
        for _ in range(n_starts):
            init = random_init(model_type)
            if model_type == 'vonmises':
                fit = fit_von_mises_mixture(train_theta, initial_params=init)
            elif model_type == 'wrapped_normal':
                fit = fit_wrapped_normal_mixture(train_theta, initial_params=init)
            elif model_type == 'wrapped_cauchy':
                fit = fit_wrapped_cauchy_mixture(train_theta, initial_params=init)
            else:
                continue
            # Validate fit
            if fit['converged'] and np.isfinite(fit['neg_log_lik']):
                if fit['neg_log_lik'] < best_fun:
                    best_fit = fit
                    best_fun = fit['neg_log_lik']
        return best_fit

    for i in range(n):
        train_theta = np.concatenate([theta[:i], theta[i+1:]])
        test_theta = theta[i]

        fit_result = fit_with_restarts(train_theta, model_type, n_starts)
        if fit_result is not None and fit_result['converged'] and np.isfinite(fit_result['neg_log_lik']):
            if model_type == 'vonmises':
                vm_pdf = stats.vonmises.pdf(test_theta, fit_result['kappa'], loc=fit_result['mu'])
                uniform_pdf = 1.0 / (2 * np.pi)
                mixture_pdf = fit_result['p'] * vm_pdf + (1 - fit_result['p']) * uniform_pdf
                log_likelihoods.append(np.log(max(mixture_pdf, 1e-10)))
            elif model_type == 'wrapped_normal':
                wn_pdf = wrapped_normal_pdf(np.array([test_theta]), fit_result['mu'], fit_result['sigma'])[0]
                uniform_pdf = 1.0 / (2 * np.pi)
                mixture_pdf = fit_result['p'] * wn_pdf + (1 - fit_result['p']) * uniform_pdf
                log_likelihoods.append(np.log(max(mixture_pdf, 1e-10)))
            elif model_type == 'wrapped_cauchy':
                wc_pdf = wrapped_cauchy_pdf(np.array([test_theta]), fit_result['mu'], fit_result['rho'])[0]
                uniform_pdf = 1.0 / (2 * np.pi)
                mixture_pdf = fit_result['p'] * wc_pdf + (1 - fit_result['p']) * uniform_pdf
                log_likelihoods.append(np.log(max(mixture_pdf, 1e-10)))
            else:
                log_likelihoods.append(penalty)
        else:
            log_likelihoods.append(penalty)

    return np.sum(log_likelihoods)

def calculate_aic(fit_result, n_params=3):
    """
    Calculate AIC (Akaike Information Criterion) for MLE fit.
    
    Parameters:
    fit_result (dict): Fitted model parameters (must include 'neg_log_lik' and 'converged')
    n_params (int): Number of free parameters (default 3)
    
    Returns:
    float: AIC score (lower is better)
    """
    if not fit_result['converged']:
        return np.inf
    return 2 * fit_result['neg_log_lik'] + 2 * n_params

def main():
    """
    Main function to execute model comparison analysis.
    """
    print("Starting model comparison analysis...")
    
    # Create outputs directory if it doesn't exist
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")
    
    # Find input files
    print("\nLooking for input files...")
    
    trial_pattern = 'outputs/trial_level_cleaned_data_*.csv'
    param_pattern = 'outputs/VWM_parameter_estimates_*.csv'
    
    trial_file = find_latest_file(trial_pattern)
    param_file = find_latest_file(param_pattern)
    
    if trial_file is None:
        print(f"ERROR: No trial data file found matching pattern {trial_pattern}")
        return 1
    
    if param_file is None:
        print(f"ERROR: No parameter file found matching pattern {param_pattern}")
        return 1
    
    print(f"Found trial data file: {trial_file}")
    print(f"Found parameter file: {param_file}")
    
    # Load data
    print("\nLoading data...")
    
    try:
        trial_data = pd.read_csv(trial_file)
        param_data = pd.read_csv(param_file)
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return 1
    
    print(f"Trial data shape: {trial_data.shape}")
    print("Trial data columns:", list(trial_data.columns))
    print("Trial data first 3 rows:")
    print(trial_data.head(3))
    
    print(f"\nParameter data shape: {param_data.shape}")
    print("Parameter data columns:", list(param_data.columns))
    print("Parameter data first 3 rows:")
    print(param_data.head(3))
    
    # Validate required columns
    required_trial_cols = ['participantId', 'isPractice', 'trial_excluded_VWM', 'VWM_error_normalized', 'VWM_trial']
    required_param_cols = ['participantId', 'concentration_kappa', 'bias_mu_degrees', 'guess_rate', 'neg_log_likelihood', 'n_valid_trials', 'convergence_success', 'excluded_insufficient_trials']
    
    missing_trial_cols = [col for col in required_trial_cols if col not in trial_data.columns]
    missing_param_cols = [col for col in required_param_cols if col not in param_data.columns]
    
    if missing_trial_cols:
        print(f"ERROR: Missing trial data columns: {missing_trial_cols}")
        return 1
    
    if missing_param_cols:
        print(f"ERROR: Missing parameter data columns: {missing_param_cols}")
        return 1
    
    print("All required columns found")
    
    # Print unique values for key experimental design parameters
    print("\nUnique values for key experimental design parameters:")
    print(f"isPractice: {sorted(trial_data['isPractice'].unique())}")
    print(f"trial_excluded_VWM: {sorted(trial_data['trial_excluded_VWM'].unique())}")
    
    # Filter trial data
    print("\nFiltering trial data...")
    print(f"Initial trial count: {len(trial_data)}")

    # Filter to VWM trials only first
    trial_data = trial_data[trial_data['VWM_trial'].notna()]
    print(f"After filtering to VWM trials only: {len(trial_data)}")

    # Filter to test trials only
    trial_data = trial_data[trial_data['isPractice'] == False]
    print(f"After filtering practice trials: {len(trial_data)}")

    # Filter out excluded trials
    trial_data = trial_data[trial_data['trial_excluded_VWM'] == False]
    print(f"After filtering excluded VWM trials: {len(trial_data)}")
    
    # Check parameter data
    print(f"\nParameter data participants: {len(param_data)}")
    print(f"Convergence success rate: {param_data['convergence_success'].mean():.3f}")
    
    # Get participants with both trial data and parameter estimates
    trial_participants = set(trial_data['participantId'].unique())
    param_participants = set(param_data['participantId'].unique())
    common_participants = trial_participants.intersection(param_participants)
    
    print(f"\nParticipants with trial data: {len(trial_participants)}")
    print(f"Participants with parameter estimates: {len(param_participants)}")
    print(f"Common participants: {len(common_participants)}")
    
    if len(common_participants) == 0:
        print("ERROR: No common participants found")
        return 1
    
    # Initialize results
    results = []
    summary_data = {'vonmises': [], 'wrapped_normal': [], 'wrapped_cauchy': []}
    
    print(f"\nStarting model comparison for {len(common_participants)} participants...")
    
    # Process each participant
    for i, participant_id in enumerate(sorted(common_participants)):
        print(f"\nProcessing participant {i+1}/{len(common_participants)}: {participant_id}")
        
        # Get participant trial data
        participant_trials = trial_data[trial_data['participantId'] == participant_id]
        
        if len(participant_trials) < 5:
            print(f"  Skipping - insufficient trials ({len(participant_trials)})")
            continue
        
        # Convert errors to radians
        errors_degrees = participant_trials['VWM_error_normalized'].values
        errors_radians = np.deg2rad(errors_degrees)

        # Validate data before fitting
        if np.any(np.isnan(errors_radians)) or np.any(np.isinf(errors_radians)):
            print(f"  Invalid data detected - skipping participant")
            continue
        
        print(f"  {len(errors_radians)} valid trials")
        
        # Get existing von Mises parameters
        param_row = param_data[param_data['participantId'] == participant_id].iloc[0]
        existing_kappa = param_row['concentration_kappa']
        existing_mu_deg = param_row['bias_mu_degrees']
        existing_guess_rate = param_row['guess_rate']
        existing_neg_loglik = param_row['neg_log_likelihood']
        
        print(f"  Existing von Mises: kappa={existing_kappa:.3f}, mu={existing_mu_deg:.1f}°, guess_rate={existing_guess_rate:.3f}")
        
        # Fit all three models
        print("  Fitting models...")
        
        # Von Mises (use existing parameters as starting point)
        vm_initial = [existing_kappa, np.deg2rad(existing_mu_deg), 1-existing_guess_rate]
        vm_fit = fit_von_mises_mixture(errors_radians, vm_initial)
        
        # Wrapped Normal
        wn_fit = fit_wrapped_normal_mixture(errors_radians)
        
        # Wrapped Cauchy  
        wc_fit = fit_wrapped_cauchy_mixture(errors_radians)
        
        print(f"    Von Mises converged: {vm_fit['converged']}")
        print(f"    Wrapped Normal converged: {wn_fit['converged']}")
        print(f"    Wrapped Cauchy converged: {wc_fit['converged']}")
        
        # Calculate LOO-CV scores
        print("  Calculating LOO-CV...")
        vm_loo = calculate_loo_cv(errors_radians, 'vonmises') if vm_fit['converged'] else -1e10
        wn_loo = calculate_loo_cv(errors_radians, 'wrapped_normal') if wn_fit['converged'] else -1e10
        wc_loo = calculate_loo_cv(errors_radians, 'wrapped_cauchy') if wc_fit['converged'] else -1e10

        print(f"    Von Mises LOO: {vm_loo:.2f}")
        print(f"    Wrapped Normal LOO: {wn_loo:.2f}")
        print(f"    Wrapped Cauchy LOO: {wc_loo:.2f}")

        # Calculate AIC scores
        print("  Calculating AIC...")
        vm_aic = calculate_aic(vm_fit)
        wn_aic = calculate_aic(wn_fit)
        wc_aic = calculate_aic(wc_fit)

        print(f"    Von Mises AIC: {vm_aic:.2f}")
        print(f"    Wrapped Normal AIC: {wn_aic:.2f}")
        print(f"    Wrapped Cauchy AIC: {wc_aic:.2f}")

        # Model selection based on LOO-CV (higher is better)
        loo_scores = {'vonmises': vm_loo, 'wrapped_normal': wn_loo, 'wrapped_cauchy': wc_loo}
        aic_scores = {'vonmises': vm_aic, 'wrapped_normal': wn_aic, 'wrapped_cauchy': wc_aic}

        # Remove models that didn't converge (penalized with -1e10)
        valid_models = {k: v for k, v in loo_scores.items() if v > -1e9}

        if not valid_models:
            print("  No models converged - skipping participant")
            continue

        # Tie-breaking logic for model selection
        sorted_models = sorted(valid_models.keys(), key=lambda k: valid_models[k], reverse=True)
        best_model = sorted_models[0]

        # Check for ties and apply AIC as a tie-breaker
        confident = True
        if len(sorted_models) > 1 and (valid_models[sorted_models[0]] - valid_models[sorted_models[1]]) < 2.0:
            print(f"  LOO-CV inconclusive. Applying AIC tie-breaker...")
            tied_models = [m for m in sorted_models if (valid_models[sorted_models[0]] - valid_models[m]) < 2.0]
            best_model = min(tied_models, key=lambda k: aic_scores[k])
            confident = False

        print(f"  Selected model: {best_model} (confident: {confident})")

        # Extract final parameters from selected model
        if best_model == 'vonmises':
            final_kappa = vm_fit['kappa']
            final_mu_deg = np.rad2deg(vm_fit['mu'])
            final_guess_rate = 1 - vm_fit['p']
        elif best_model == 'wrapped_normal':
            final_kappa = wn_fit['kappa_equivalent']
            final_mu_deg = np.rad2deg(wn_fit['mu'])
            final_guess_rate = 1 - wn_fit['p']
        else:  # wrapped_cauchy
            final_kappa = wc_fit['kappa_equivalent']
            final_mu_deg = np.rad2deg(wc_fit['mu'])
            final_guess_rate = 1 - wc_fit['p']

        # Store results
        results.append({
            'participantId': participant_id,
            'vonmises_loo_cv': vm_loo,
            'vonmises_aic': vm_aic,
            'wrapped_normal_loo_cv': wn_loo,
            'wrapped_normal_aic': wn_aic,
            'wrapped_cauchy_loo_cv': wc_loo,
            'wrapped_cauchy_aic': wc_aic,
            'selected_model': best_model,
            'final_concentration_kappa': final_kappa,
            'final_bias_mu_degrees': final_mu_deg,
            'final_guess_rate': final_guess_rate,
            'model_selection_confident': confident
        })

        # Store for summary
        if vm_fit['converged']:
            summary_data['vonmises'].append({'loo': vm_loo, 'aic': vm_aic})
        if wn_fit['converged']:
            summary_data['wrapped_normal'].append({'loo': wn_loo, 'aic': wn_aic})
        if wc_fit['converged']:
            summary_data['wrapped_cauchy'].append({'loo': wc_loo, 'aic': wc_aic})
    
    print(f"\nCompleted analysis for {len(results)} participants")
    
    if len(results) == 0:
        print("ERROR: No participants successfully analyzed")
        return 1
    
    # Create results dataframe
    results_df = pd.DataFrame(results)
    
    print("\nModel selection summary:")
    model_counts = results_df['selected_model'].value_counts()
    print(model_counts)
    
    # Create summary dataframe
    summary_results = []

    for model_type in ['vonmises', 'wrapped_normal', 'wrapped_cauchy']:
        selection_freq = len(results_df[results_df['selected_model'] == model_type])

        if model_type in summary_data and summary_data[model_type]:
            loo_vals = np.array([x['loo'] for x in summary_data[model_type]])
            aic_vals = np.array([x['aic'] for x in summary_data[model_type]])
            # Filter out non-finite values
            loo_vals = loo_vals[np.isfinite(loo_vals)]
            aic_vals = aic_vals[np.isfinite(aic_vals)]
            mean_loo = np.mean(loo_vals) if len(loo_vals) > 0 else np.nan
            mean_aic = np.mean(aic_vals) if len(aic_vals) > 0 else np.nan
            convergence_rate = len(summary_data[model_type]) / len(common_participants)
        else:
            mean_loo = np.nan
            mean_aic = np.nan
            convergence_rate = 0.0

        summary_results.append({
            'model_type': model_type,
            'selection_frequency': selection_freq,
            'mean_loo_cv': mean_loo,
            'mean_aic': mean_aic,
            'convergence_rate': convergence_rate
        })

    summary_df = pd.DataFrame(summary_results)

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    results_filename = f'outputs/model_comparison_results_{timestamp}.csv'
    summary_filename = f'outputs/model_comparison_summary_{timestamp}.csv'

    print(f"\nSaving results to {results_filename}")
    results_df.to_csv(results_filename, index=False)

    print(f"Saving summary to {summary_filename}")
    summary_df.to_csv(summary_filename, index=False)

    print("\nResults dataframe:")
    print("Columns:", list(results_df.columns))
    print("First 2 rows:")
    print(results_df.head(2))

    print("\nSummary dataframe:")
    print("Columns:", list(summary_df.columns))
    print("First 2 rows:")
    print(summary_df.head(2))

    print(f"\nFinal summary:")
    print(f"Total participants analyzed: {len(results)}")
    print(f"Model selection frequencies:")
    for _, row in summary_df.iterrows():
        print(f"  {row['model_type']}: {row['selection_frequency']} ({row['selection_frequency']/len(results)*100:.1f}%)")

    print("Finished execution")
    return 0

if __name__ == "__main__":
    exit(main())
