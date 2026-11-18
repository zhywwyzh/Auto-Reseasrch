#!/usr/bin/env python3
"""
VWM Circular Statistical Analysis Script

This script processes Visual Working Memory (VWM) data to fit circular statistical models
and perform model comparison for each participant.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
from scipy.optimize import minimize
from scipy.stats import vonmises, uniform
from sklearn.model_selection import KFold
import multiprocessing as mp
from functools import partial

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/VWM_cleaned_*.csv')
    
    Returns:
    --------
    str or None
        Path to the most recent file matching the pattern, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Sort by modification time and return the most recent
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def degrees_to_radians(degrees):
    """
    Convert degrees to radians.
    
    Parameters:
    -----------
    degrees : array-like
        Angles in degrees
    
    Returns:
    --------
    array-like
        Angles in radians
    """
    return np.deg2rad(degrees)

def radians_to_degrees(radians):
    """
    Convert radians to degrees.
    
    Parameters:
    -----------
    radians : array-like
        Angles in radians
    
    Returns:
    --------
    array-like
        Angles in degrees
    """
    return np.rad2deg(radians)

def wrapped_normal_pdf(x, mu, sigma):
    """
    Probability density function for wrapped normal distribution.
    
    Parameters:
    -----------
    x : array-like
        Values to evaluate PDF at (in radians)
    mu : float
        Mean parameter (in radians)
    sigma : float
        Standard deviation parameter
    
    Returns:
    --------
    array-like
        PDF values
    """
    # Approximate wrapped normal using sum of normal distributions
    pdf_sum = np.zeros_like(x)
    for k in range(-3, 4):  # Sum over several wrappings
        pdf_sum += np.exp(-0.5 * ((x - mu - 2*np.pi*k) / sigma)**2)
    return pdf_sum / (sigma * np.sqrt(2 * np.pi))

def wrapped_cauchy_pdf(x, mu, gamma):
    """
    Probability density function for wrapped Cauchy distribution.
    
    Parameters:
    -----------
    x : array-like
        Values to evaluate PDF at (in radians)
    mu : float
        Location parameter (in radians)
    gamma : float
        Scale parameter
    
    Returns:
    --------
    array-like
        PDF values
    """
    return (1 - gamma**2) / (2*np.pi * (1 + gamma**2 - 2*gamma*np.cos(x - mu)))

def von_mises_mixture_loglik(params, data):
    """
    Log-likelihood function for von Mises mixture model.
    
    Parameters:
    -----------
    params : array-like
        Parameters [kappa, mu, p] where:
        - kappa: concentration parameter
        - mu: mean direction parameter
        - p: guess rate (proportion of uniform responses)
    data : array-like
        Angular data in radians
    
    Returns:
    --------
    float
        Negative log-likelihood (for minimization)
    """
    kappa, mu, p = params
    
    # Ensure valid parameter ranges
    if kappa < 0 or p < 0 or p > 1:
        return np.inf
    
    # von Mises component
    vm_pdf = vonmises.pdf(data, kappa, loc=mu)
    
    # Uniform component
    uniform_pdf = 1 / (2 * np.pi)
    
    # Mixture likelihood
    likelihood = (1 - p) * vm_pdf + p * uniform_pdf
    
    # Avoid log(0)
    likelihood = np.maximum(likelihood, 1e-10)
    
    return -np.sum(np.log(likelihood))

def fit_von_mises_mixture(data, max_iter=1000, tol=1e-3):
    """
    Fit von Mises mixture model to circular data using maximum likelihood estimation.
    
    Parameters:
    -----------
    data : array-like
        Angular data in radians
    max_iter : int
        Maximum number of iterations
    tol : float
        Convergence tolerance
    
    Returns:
    --------
    dict
        Dictionary containing fitted parameters and convergence info
    """
    data = np.array(data)
    
    # Initial parameter guesses
    initial_guesses = [
        [1.0, 0.0, 0.2],  # moderate precision, no bias, low guess rate
        [0.5, 0.0, 0.5],  # low precision, no bias, high guess rate
        [2.0, np.pi/4, 0.1],  # high precision, some bias, very low guess rate
    ]
    
    best_result = None
    best_loglik = np.inf
    
    for initial_params in initial_guesses:
        try:
            result = minimize(
                von_mises_mixture_loglik,
                initial_params,
                args=(data,),
                method='L-BFGS-B',
                bounds=[(0.001, 50), (-np.pi, np.pi), (0, 0.999)],
                options={'maxiter': max_iter, 'ftol': tol}
            )
            
            if result.success and result.fun < best_loglik:
                best_result = result
                best_loglik = result.fun
                
        except Exception as e:
            print(f"Warning: Optimization failed with initial guess {initial_params}: {e}")
            continue
    
    if best_result is None:
        return {
            'kappa': np.nan,
            'mu': np.nan,
            'guess_rate': np.nan,
            'converged': False,
            'loglik': np.nan
        }
    
    kappa, mu, guess_rate = best_result.x
    
    return {
        'kappa': kappa,
        'mu': mu,
        'guess_rate': guess_rate,
        'converged': best_result.success,
        'loglik': -best_result.fun
    }

def bootstrap_parameters(data, n_bootstrap=1000):
    """
    Calculate bootstrap confidence intervals for model parameters.
    
    Parameters:
    -----------
    data : array-like
        Angular data in radians
    n_bootstrap : int
        Number of bootstrap samples
    
    Returns:
    --------
    dict
        Dictionary containing parameter estimates and confidence intervals
    """
    bootstrap_params = {'kappa': [], 'mu': [], 'guess_rate': []}
    
    for i in range(n_bootstrap):
        # Bootstrap sample
        boot_data = np.random.choice(data, size=len(data), replace=True)
        
        # Fit model
        result = fit_von_mises_mixture(boot_data)
        
        if result['converged']:
            bootstrap_params['kappa'].append(result['kappa'])
            bootstrap_params['mu'].append(result['mu'])
            bootstrap_params['guess_rate'].append(result['guess_rate'])
    
    # Calculate confidence intervals
    ci_results = {}
    for param in ['kappa', 'mu', 'guess_rate']:
        if len(bootstrap_params[param]) > 0:
            ci_results[f'{param}_se'] = np.std(bootstrap_params[param])
            ci_results[f'{param}_ci_lower'] = np.percentile(bootstrap_params[param], 2.5)
            ci_results[f'{param}_ci_upper'] = np.percentile(bootstrap_params[param], 97.5)
        else:
            ci_results[f'{param}_se'] = np.nan
            ci_results[f'{param}_ci_lower'] = np.nan
            ci_results[f'{param}_ci_upper'] = np.nan
    
    return ci_results

def fit_single_distribution(data, dist_type):
    """
    Fit a single circular distribution to data.
    
    Parameters:
    -----------
    data : array-like
        Angular data in radians
    dist_type : str
        Distribution type ('von_mises', 'wrapped_normal', 'wrapped_cauchy')
    
    Returns:
    --------
    float
        Log-likelihood of the fitted distribution
    """
    data = np.array(data)
    
    try:
        if dist_type == 'von_mises':
            # Fit von Mises distribution
            kappa_est = vonmises.fit(data, fscale=1)[0]
            mu_est = np.arctan2(np.mean(np.sin(data)), np.mean(np.cos(data)))
            loglik = np.sum(vonmises.logpdf(data, kappa_est, loc=mu_est))
            
        elif dist_type == 'wrapped_normal':
            # Fit wrapped normal (approximate using method of moments)
            mu_est = np.arctan2(np.mean(np.sin(data)), np.mean(np.cos(data)))
            R = np.sqrt(np.mean(np.cos(data))**2 + np.mean(np.sin(data))**2)
            if R > 0.53:
                sigma_est = np.sqrt(-2 * np.log(R))
            else:
                sigma_est = 1.0  # fallback
            
            pdf_vals = wrapped_normal_pdf(data, mu_est, sigma_est)
            pdf_vals = np.maximum(pdf_vals, 1e-10)
            loglik = np.sum(np.log(pdf_vals))
            
        elif dist_type == 'wrapped_cauchy':
            # Fit wrapped Cauchy
            mu_est = np.arctan2(np.mean(np.sin(data)), np.mean(np.cos(data)))
            R = np.sqrt(np.mean(np.cos(data))**2 + np.mean(np.sin(data))**2)
            gamma_est = R  # method of moments estimate
            
            pdf_vals = wrapped_cauchy_pdf(data, mu_est, gamma_est)
            pdf_vals = np.maximum(pdf_vals, 1e-10)
            loglik = np.sum(np.log(pdf_vals))
            
        else:
            loglik = np.nan
            
    except Exception as e:
        print(f"Warning: Failed to fit {dist_type} distribution: {e}")
        loglik = np.nan
    
    return loglik

def cross_validate_distributions(data, n_folds=10):
    """
    Perform cross-validation to compare different circular distributions.
    
    Parameters:
    -----------
    data : array-like
        Angular data in radians
    n_folds : int
        Number of cross-validation folds
    
    Returns:
    --------
    dict
        Dictionary containing average log-likelihoods for each distribution
    """
    data = np.array(data)
    kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)
    
    distributions = ['von_mises', 'wrapped_normal', 'wrapped_cauchy']
    cv_results = {dist: [] for dist in distributions}
    
    for train_idx, test_idx in kf.split(data):
        train_data = data[train_idx]
        test_data = data[test_idx]
        
        for dist_type in distributions:
            try:
                if dist_type == 'von_mises':
                    # Fit on training data
                    kappa_est = vonmises.fit(train_data, fscale=1)[0]
                    mu_est = np.arctan2(np.mean(np.sin(train_data)), np.mean(np.cos(train_data)))
                    # Evaluate on test data
                    loglik = np.sum(vonmises.logpdf(test_data, kappa_est, loc=mu_est))
                    
                elif dist_type == 'wrapped_normal':
                    # Fit on training data
                    mu_est = np.arctan2(np.mean(np.sin(train_data)), np.mean(np.cos(train_data)))
                    R = np.sqrt(np.mean(np.cos(train_data))**2 + np.mean(np.sin(train_data))**2)
                    if R > 0.53:
                        sigma_est = np.sqrt(-2 * np.log(R))
                    else:
                        sigma_est = 1.0
                    # Evaluate on test data
                    pdf_vals = wrapped_normal_pdf(test_data, mu_est, sigma_est)
                    pdf_vals = np.maximum(pdf_vals, 1e-10)
                    loglik = np.sum(np.log(pdf_vals))
                    
                elif dist_type == 'wrapped_cauchy':
                    # Fit on training data
                    mu_est = np.arctan2(np.mean(np.sin(train_data)), np.mean(np.cos(train_data)))
                    R = np.sqrt(np.mean(np.cos(train_data))**2 + np.mean(np.sin(train_data))**2)
                    gamma_est = R
                    # Evaluate on test data
                    pdf_vals = wrapped_cauchy_pdf(test_data, mu_est, gamma_est)
                    pdf_vals = np.maximum(pdf_vals, 1e-10)
                    loglik = np.sum(np.log(pdf_vals))
                
                cv_results[dist_type].append(loglik)
                
            except Exception as e:
                print(f"Warning: CV failed for {dist_type}: {e}")
                cv_results[dist_type].append(np.nan)
    
    # Calculate average log-likelihoods
    avg_logliks = {}
    for dist_type in distributions:
        valid_logliks = [x for x in cv_results[dist_type] if not np.isnan(x)]
        if valid_logliks:
            avg_logliks[dist_type] = np.mean(valid_logliks)
        else:
            avg_logliks[dist_type] = np.nan
    
    return avg_logliks

def process_participant(participant_data):
    """
    Process a single participant's data to fit models and perform analysis.
    
    Parameters:
    -----------
    participant_data : tuple
        Tuple containing (participant_id, error_data)
    
    Returns:
    --------
    dict
        Dictionary containing all analysis results for the participant
    """
    participant_id, error_degrees = participant_data
    
    print(f"Processing participant: {participant_id}")
    
    try:
        # Convert to radians
        error_radians = degrees_to_radians(error_degrees)
        
        # Check for degenerate cases
        if len(error_degrees) == 0:
            raise ValueError("No valid error data")
        
        if np.all(np.isnan(error_degrees)):
            raise ValueError("All error values are NaN")
        
        # Fit von Mises mixture model
        vm_result = fit_von_mises_mixture(error_radians)
        
        # Bootstrap confidence intervals
        ci_results = bootstrap_parameters(error_radians)
        
        # Cross-validation model comparison
        cv_results = cross_validate_distributions(error_radians)
        
        # Determine best fitting distribution
        valid_cv = {k: v for k, v in cv_results.items() if not np.isnan(v)}
        if valid_cv:
            best_dist = max(valid_cv.keys(), key=lambda k: valid_cv[k])
        else:
            best_dist = 'none'
        
        # Quality control checks
        excluded = False
        exclusion_reason = None
        
        if not vm_result['converged']:
            excluded = True
            exclusion_reason = 'model_convergence_failure'
        elif vm_result['kappa'] < 0:
            excluded = True
            exclusion_reason = 'negative_concentration'
        elif vm_result['guess_rate'] > 0.8:
            excluded = True
            exclusion_reason = 'high_guess_rate'
        
        # Compile results
        result = {
            'participantId': participant_id,
            'kappa_concentration': vm_result['kappa'],
            'mu_bias': radians_to_degrees(vm_result['mu']),
            'guess_rate': vm_result['guess_rate'],
            'kappa_se': ci_results.get('kappa_se', np.nan),
            'mu_se': radians_to_degrees(ci_results.get('mu_se', np.nan)),
            'guess_rate_se': ci_results.get('guess_rate_se', np.nan),
            'kappa_ci_lower': ci_results.get('kappa_ci_lower', np.nan),
            'kappa_ci_upper': ci_results.get('kappa_ci_upper', np.nan),
            'mu_ci_lower': radians_to_degrees(ci_results.get('mu_ci_lower', np.nan)),
            'mu_ci_upper': radians_to_degrees(ci_results.get('mu_ci_upper', np.nan)),
            'guess_rate_ci_lower': ci_results.get('guess_rate_ci_lower', np.nan),
            'guess_rate_ci_upper': ci_results.get('guess_rate_ci_upper', np.nan),
            'model_converged': bool(vm_result['converged']),
            'best_fit_distribution': best_dist,
            'von_mises_loglik': cv_results.get('von_mises', np.nan),
            'wrapped_normal_loglik': cv_results.get('wrapped_normal', np.nan),
            'wrapped_cauchy_loglik': cv_results.get('wrapped_cauchy', np.nan),
            'n_valid_trials': len(error_degrees),
            'excluded': bool(excluded),
            'exclusion_reason': exclusion_reason if excluded else ''
        }
        
        return result

    except Exception as e:
        print(f"Error processing participant {participant_id}: {e}")
        # Return a default result structure for failed participants
        return {
            'participantId': participant_id,
            'kappa_concentration': np.nan,
            'mu_bias': np.nan,
            'guess_rate': np.nan,
            'kappa_se': np.nan,
            'mu_se': np.nan,
            'guess_rate_se': np.nan,
            'kappa_ci_lower': np.nan,
            'kappa_ci_upper': np.nan,
            'mu_ci_lower': np.nan,
            'mu_ci_upper': np.nan,
            'guess_rate_ci_lower': np.nan,
            'guess_rate_ci_upper': np.nan,
            'model_converged': bool(False),
            'best_fit_distribution': 'none',
            'von_mises_loglik': np.nan,
            'wrapped_normal_loglik': np.nan,
            'wrapped_cauchy_loglik': np.nan,
            'n_valid_trials': len(error_degrees),
            'excluded': bool(True),
            'exclusion_reason': f'processing_error: {str(e)}'
        }

def main():
    """
    Main function to execute the VWM circular statistical analysis.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting VWM Circular Statistical Analysis")
        print("=" * 50)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input file
        print("Looking for input file...")
        input_pattern = 'outputs/VWM_cleaned_*.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"Error: No input file found matching pattern {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Load data
        print("Loading data...")
        try:
            data = pd.read_csv(input_file)
            print(f"Loaded data with shape: {data.shape}")
        except Exception as e:
            print(f"Error loading data: {e}")
            return 1
        
        # Print column information
        print(f"Columns in dataset: {list(data.columns)}")
        print("First 3 rows of data:")
        print(data.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'VWM_error_normalized_degrees', 'VWM_setSize', 'VWM_delay_s', 'excluded']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return 1
        
        # Print unique values for experimental design parameters
        print("\nExperimental design parameter values:")
        print(f"VWM_setSize unique values: {sorted(data['VWM_setSize'].unique())}")
        print(f"VWM_delay_s unique values: {sorted(data['VWM_delay_s'].unique())}")
        print(f"excluded unique values: {sorted(data['excluded'].unique())}")
        print(f"VWM_error_normalized_degrees data type: {data['VWM_error_normalized_degrees'].dtype}")
        
        # Filter valid participants
        print("\nFiltering valid participants...")
        print(f"Initial number of participants: {data['participantId'].nunique()}")
        
        # Filter out excluded participants
        valid_data = data[data['excluded'] == False].copy()
        print(f"Participants after excluding excluded==True: {valid_data['participantId'].nunique()}")
        
        # Check minimum trial count per participant
        trial_counts = valid_data.groupby('participantId').size()
        print(f"Trial count statistics:")
        print(f"  Mean: {trial_counts.mean():.1f}")
        print(f"  Median: {trial_counts.median():.1f}")
        print(f"  Min: {trial_counts.min()}")
        print(f"  Max: {trial_counts.max()}")
        
        # Filter participants with minimum 100 trials (changed from 150)
        valid_participants = trial_counts[trial_counts >= 100].index
        print(f"Participants with >=100 trials: {len(valid_participants)}")
        if len(valid_participants) < 10:
            print(f"Warning: Only {len(valid_participants)} participants remain after filtering. Results may not be reliable.")
            if len(valid_participants) == 0:
                print("Error: No participants remain after filtering. Cannot proceed with analysis.")
                return 1
        
        final_data = valid_data[valid_data['participantId'].isin(valid_participants)].copy()
        print(f"Final dataset shape: {final_data.shape}")
        
        # Prepare data for processing
        print("\nPreparing data for model fitting...")
        participant_data_list = []
        for participant_id in valid_participants:
            participant_subset = final_data[final_data['participantId'] == participant_id]
            error_data = participant_subset['VWM_error_normalized_degrees'].dropna().values
            participant_data_list.append((participant_id, error_data))
        
        print(f"Number of participants to process: {len(participant_data_list)}")
        
        # Process participants using multiprocessing for speed
        print("\nProcessing participants (using multiprocessing)...")
        n_cores = min(mp.cpu_count(), len(participant_data_list))
        print(f"Using {n_cores} CPU cores for processing")
        
        with mp.Pool(n_cores) as pool:
            results = pool.map(process_participant, participant_data_list)
        
        print("Participant processing complete!")
        
        # Convert results to DataFrame
        print("\nCompiling results...")
        results_df = pd.DataFrame(results)
        
        # Print processing summary
        print(f"Total participants processed: {len(results_df)}")
        print(f"Models converged: {results_df['model_converged'].sum()}")
        print(f"Participants excluded: {results_df['excluded'].sum()}")
        
        if results_df['excluded'].sum() > 0:
            print("Exclusion reasons:")
            exclusion_counts = results_df[results_df['excluded']]['exclusion_reason'].value_counts()
            for reason, count in exclusion_counts.items():
                print(f"  {reason}: {count}")
        
        # Model comparison summary
        print("\nModel comparison results:")
        best_fit_counts = results_df[~results_df['excluded']]['best_fit_distribution'].value_counts()
        total_valid = len(results_df[~results_df['excluded']])
        
        model_comparison_data = []
        for dist_type in ['von_mises', 'wrapped_normal', 'wrapped_cauchy']:
            n_best_fit = best_fit_counts.get(dist_type, 0)
            proportion = n_best_fit / total_valid if total_valid > 0 else 0
            
            # Calculate mean log-likelihood for this distribution
            loglik_col = f'{dist_type}_loglik'
            valid_logliks = results_df[~results_df['excluded']][loglik_col].dropna()
            mean_loglik = valid_logliks.mean() if len(valid_logliks) > 0 else np.nan
            if len(valid_logliks) <= 1:
                sd_loglik = np.nan
            else:
                sd_loglik = valid_logliks.std()
            
            model_comparison_data.append({
                'distribution_type': dist_type,
                'n_participants_best_fit': n_best_fit,
                'proportion_best_fit': proportion,
                'mean_loglik': mean_loglik,
                'sd_loglik': sd_loglik
            })
            
            print(f"  {dist_type}: {n_best_fit} participants ({proportion:.3f})")
        
        model_comparison_df = pd.DataFrame(model_comparison_data)
        
        # Save results
        print("\nSaving results...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save parameter results
        param_output_file = f'outputs/VWM_parameters_{timestamp}.csv'
        results_df.to_csv(param_output_file, index=False)
        print(f"Saved parameter results to: {param_output_file}")
        
        # Save model comparison results
        comparison_output_file = f'outputs/VWM_model_comparison_{timestamp}.csv'
        model_comparison_df.to_csv(comparison_output_file, index=False)
        print(f"Saved model comparison results to: {comparison_output_file}")
        
        # Print final summary
        print("\n" + "=" * 50)
        print("ANALYSIS SUMMARY")
        print("=" * 50)
        print(f"Total participants analyzed: {len(results_df)}")
        print(f"Successfully fitted models: {results_df['model_converged'].sum()}")
        print(f"Quality control exclusions: {results_df['excluded'].sum()}")
        print(f"Final valid participants: {len(results_df[~results_df['excluded']])}")
        
        print("\nParameter estimates (valid participants):")
        valid_results = results_df[~results_df['excluded']]
        if len(valid_results) > 0:
            print(f"  Kappa (concentration): {valid_results['kappa_concentration'].mean():.3f} ± {valid_results['kappa_concentration'].std():.3f}")
            print(f"  Mu (bias): {valid_results['mu_bias'].mean():.3f}° ± {valid_results['mu_bias'].std():.3f}°")
            print(f"  Guess rate: {valid_results['guess_rate'].mean():.3f} ± {valid_results['guess_rate'].std():.3f}")
        
        print("\nBest fitting distributions:")
        for _, row in model_comparison_df.iterrows():
            print(f"  {row['distribution_type']}: {row['proportion_best_fit']:.3f}")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
