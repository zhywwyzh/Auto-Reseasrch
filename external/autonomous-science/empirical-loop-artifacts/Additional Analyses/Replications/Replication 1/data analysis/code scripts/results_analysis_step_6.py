#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import glob
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to search for
        
    Returns:
    --------
    str
        Path to the most recent file matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found latest file: {latest_file}")
    return latest_file

def load_and_validate_data(filepath):
    """
    Load and validate the input CSV file.
    
    Parameters:
    -----------
    filepath : str
        Path to the input CSV file
        
    Returns:
    --------
    pd.DataFrame
        Loaded and validated dataframe
    """
    print(f"Loading data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"Successfully loaded data with shape: {df.shape}")
    except Exception as e:
        print(f"Error loading file: {e}")
        return None
    
    print("All columns in dataset:")
    print(df.columns.tolist())
    
    print("\nFirst 3 rows of data:")
    print(df.head(3))
    
    # Check for required columns
    required_cols = ['participantId', 'trial_type', 'VWM_error_radians', 
                     'VWM_error_degrees_normalized', 'excluded_participant']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Warning: Missing required columns: {missing_cols}")
        return None
    
    print("Required columns found successfully")
    
    # Print unique values for key experimental design parameters
    print("\nUnique values for key experimental design parameters:")
    print(f"trial_type unique values: {df['trial_type'].unique()}")
    print(f"excluded_participant unique values: {df['excluded_participant'].unique()}")
    
    # Print data types for measured variables
    print(f"\nData types for measured variables:")
    print(f"VWM_error_radians type: {df['VWM_error_radians'].dtype}")
    print(f"VWM_error_degrees_normalized type: {df['VWM_error_degrees_normalized'].dtype}")
    
    return df

def filter_data(df):
    """
    Filter data for non-excluded participants and test trials only.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe
        
    Returns:
    --------
    pd.DataFrame
        Filtered dataframe
    """
    print("Filtering data...")
    
    initial_rows = len(df)
    print(f"Initial number of rows: {initial_rows}")
    
    # Filter for non-excluded participants
    df_filtered = df[df['excluded_participant'] == False].copy()
    after_exclusion = len(df_filtered)
    print(f"Rows after excluding participants: {after_exclusion}")
    print(f"Excluded {initial_rows - after_exclusion} rows due to participant exclusion")
    
    # Filter for test trials only
    df_filtered = df_filtered[df_filtered['trial_type'] == 'test'].copy()
    final_rows = len(df_filtered)
    print(f"Final rows after filtering for test trials: {final_rows}")
    print(f"Excluded {after_exclusion - final_rows} rows for non-test trials")
    
    print(f"\nFiltered data columns:")
    print(df_filtered.columns.tolist())
    print(f"\nFirst 2 rows of filtered data:")
    print(df_filtered.head(2))
    
    return df_filtered


def fit_von_mises_python(errors):
    """
    Fit von Mises distribution using Python implementation.
    
    Parameters:
    -----------
    errors : array-like
        Circular errors in radians
        
    Returns:
    --------
    dict
        Dictionary containing fitted parameters
    """
    from scipy.optimize import minimize
    from scipy.special import i0, i1
    
    def von_mises_loglik(params, data):
        """Negative log-likelihood for von Mises distribution"""
        mu, kappa = params
        if kappa <= 0:
            return 1e10
        
        n = len(data)
        loglik = -n * np.log(2 * np.pi) - n * np.log(i0(kappa)) + kappa * np.sum(np.cos(data - mu))
        return -loglik
    
    # Initial parameter estimates
    mu_init = np.arctan2(np.mean(np.sin(errors)), np.mean(np.cos(errors)))
    kappa_init = 1.0
    
    # Optimize
    try:
        result = minimize(von_mises_loglik, [mu_init, kappa_init], 
                         args=(errors,), method='L-BFGS-B',
                         bounds=[(0, 2*np.pi), (0.01, 100)])
        
        if result.success:
            mu, kappa = result.x
            loglik = -result.fun - len(errors) * np.log(2 * np.pi)  # Add missing constant
            n = len(errors)
            aic = 2 * 2 - 2 * loglik  # 2 parameters
            bic = np.log(n) * 2 - 2 * loglik
            
            return {
                'mu': mu,
                'kappa': kappa,
                'loglikelihood': loglik,
                'AIC': aic,
                'BIC': bic,
                'converged': True
            }
    except:
        pass
    
    return {
        'mu': np.nan,
        'kappa': np.nan,
        'loglikelihood': np.nan,
        'AIC': np.nan,
        'BIC': np.nan,
        'converged': False
    }

def fit_mixture_model_python(errors):
    """
    Fit two-component mixture model using Python implementation.
    
    Parameters:
    -----------
    errors : array-like
        Circular errors in radians
        
    Returns:
    --------
    dict
        Dictionary containing fitted parameters
    """
    from scipy.optimize import minimize
    
    def mixture_loglik(params, data):
        """Negative log-likelihood for mixture model"""
        p_guess, kappa, mu = params
        if p_guess < 0 or p_guess > 1 or kappa <= 0:
            return 1e10
        
        n = len(data)
        uniform_density = 1 / (2 * np.pi)
        
        # von Mises component (estimate mu)
        from scipy.special import i0
        vm_density = np.exp(kappa * np.cos(data - mu)) / (2 * np.pi * i0(kappa))
        
        mixture_density = p_guess * uniform_density + (1 - p_guess) * vm_density
        mixture_density = np.maximum(mixture_density, 1e-10)  # Avoid log(0)
        
        loglik = np.sum(np.log(mixture_density))
        return -loglik
    
    # Initial parameter estimates
    p_guess_init = 0.2
    kappa_init = 1.0
    mu_init = np.arctan2(np.mean(np.sin(errors)), np.mean(np.cos(errors)))
    
    try:
        result = minimize(mixture_loglik, [p_guess_init, kappa_init, mu_init],
                         args=(errors,), method='L-BFGS-B',
                         bounds=[(0, 1), (0.01, 100), (0, 2*np.pi)])
        
        if result.success:
            p_guess, kappa, mu = result.x
            loglik = -result.fun
            n = len(errors)
            aic = 2 * 3 - 2 * loglik  # 3 parameters
            bic = np.log(n) * 3 - 2 * loglik  # 3 parameters
            
            return {
                'guess_proportion': p_guess,
                'precision_nonguess': kappa,
                'mu': mu,
                'loglikelihood': loglik,
                'AIC': aic,
                'BIC': bic,
                'converged': True
            }
    except:
        pass
    
    return {
        'guess_proportion': np.nan,
        'precision_nonguess': np.nan,
        'mu': np.nan,
        'loglikelihood': np.nan,
        'AIC': np.nan,
        'BIC': np.nan,
        'converged': False
    }

def fit_wrapped_normal_python(errors):
    """
    Fit wrapped normal distribution using Python implementation.
    
    Parameters:
    -----------
    errors : array-like
        Circular errors in radians
        
    Returns:
    --------
    dict
        Dictionary containing fitted parameters
    """
    from scipy.optimize import minimize
    
    def wrapped_normal_loglik(params, data):
        """Negative log-likelihood for wrapped normal distribution"""
        mu, sigma = params
        if sigma <= 0:
            return 1e10
        
        # Approximate wrapped normal with truncated series
        loglik = 0
        for x in data:
            density = 0
            for k in range(-2, 3):  # Truncate series
                density += np.exp(-(x - mu + 2*np.pi*k)**2 / (2*sigma**2))
            density /= sigma * np.sqrt(2*np.pi)
            if density <= 0:
                density = 1e-10
            loglik += np.log(density)
        
        return -loglik
    
    # Initial parameter estimates
    mu_init = np.arctan2(np.mean(np.sin(errors)), np.mean(np.cos(errors)))
    sigma_init = 1.0
    
    try:
        result = minimize(wrapped_normal_loglik, [mu_init, sigma_init],
                         args=(errors,), method='L-BFGS-B',
                         bounds=[(0, 2*np.pi), (0.01, 10)])
        
        if result.success:
            loglik = -result.fun
            n = len(errors)
            aic = 2 * 2 - 2 * loglik  # 2 parameters
            mu, sigma = result.x
            return {'AIC': aic, 'converged': True, 'mu': mu, 'sigma': sigma}
    except:
        pass
    
    return {'AIC': np.nan, 'converged': False}

def fit_wrapped_cauchy_python(errors):
    """
    Fit wrapped Cauchy distribution using Python implementation.
    
    Parameters:
    -----------
    errors : array-like
        Circular errors in radians
        
    Returns:
    --------
    dict
        Dictionary containing fitted parameters
    """
    from scipy.optimize import minimize
    
    def wrapped_cauchy_loglik(params, data):
        """Negative log-likelihood for wrapped Cauchy distribution"""
        mu, rho = params
        if rho <= 0 or rho >= 1:
            return 1e10
        
        loglik = 0
        for x in data:
            density = (1 - rho**2) / (2*np.pi * (1 + rho**2 - 2*rho*np.cos(x - mu)))
            if density <= 0:
                density = 1e-10
            loglik += np.log(density)
        
        return -loglik
    
    # Initial parameter estimates
    mu_init = np.arctan2(np.mean(np.sin(errors)), np.mean(np.cos(errors)))
    rho_init = 0.5
    
    try:
        result = minimize(wrapped_cauchy_loglik, [mu_init, rho_init],
                         args=(errors,), method='L-BFGS-B',
                         bounds=[(0, 2*np.pi), (0.01, 0.99)])
        
        if result.success:
            loglik = -result.fun
            n = len(errors)
            aic = 2 * 2 - 2 * loglik  # 2 parameters
            mu, rho = result.x
            return {'AIC': aic, 'converged': True, 'mu': mu, 'rho': rho}
    except:
        pass
    
    return {'AIC': np.nan, 'converged': False}


def calculate_log_density(x, distribution, params):
    """Calculate log density for a single point under fitted distribution."""
    if not isinstance(params, dict) or not params:
        return -np.inf

    if distribution == 'von_mises':
        mu = params.get('mu')
        kappa = params.get('kappa')
        if mu is None or kappa is None or np.isnan(mu) or np.isnan(kappa) or kappa <= 0:
            return -np.inf
        from scipy.special import i0
        try:
            # von Mises density: f(x) = exp(kappa*cos(x-mu)) / (2*pi*i0(kappa))
            density = np.exp(kappa * np.cos(x - mu)) / (2 * np.pi * i0(kappa))
            if density <= 0 or np.isnan(density) or np.isinf(density):
                return -np.inf
            return np.log(density)
        except Exception:
            return -np.inf
    elif distribution == 'mixture':
        p_guess = params.get('guess_proportion')
        kappa = params.get('precision_nonguess') 
        mu = params.get('mu')
        if any(v is None or np.isnan(v) for v in [p_guess, kappa, mu]) or kappa <= 0:
            return -np.inf
        uniform_density = 1 / (2 * np.pi)
        from scipy.special import i0
        try:
            vm_density = np.exp(kappa * np.cos(x - mu)) / (2 * np.pi * i0(kappa))
            mixture_density = p_guess * uniform_density + (1 - p_guess) * vm_density
            if mixture_density <= 0 or np.isnan(mixture_density) or np.isinf(mixture_density):
                return -np.inf
            return np.log(mixture_density)
        except Exception:
            return -np.inf
    elif distribution == 'wrapped_normal':
        mu = params.get('mu', 0)
        sigma = params.get('sigma', 1)
        if sigma is None or sigma <= 0 or np.isnan(sigma):
            return -np.inf
        try:
            density = 0
            for k in range(-2, 3):  # Truncate series
                density += np.exp(-(x - mu + 2*np.pi*k)**2 / (2*sigma**2))
            density /= sigma * np.sqrt(2*np.pi)
            if density <= 0 or np.isnan(density) or np.isinf(density):
                return -np.inf
            return np.log(density)
        except Exception:
            return -np.inf
    elif distribution == 'wrapped_cauchy':
        mu = params.get('mu', 0)
        rho = params.get('rho', 0.5)
        if rho is None or rho <= 0 or rho >= 1 or np.isnan(rho):
            return -np.inf
        try:
            density = (1 - rho**2) / (2*np.pi * (1 + rho**2 - 2*rho*np.cos(x - mu)))
            if density <= 0 or np.isnan(density) or np.isinf(density):
                return -np.inf
            return np.log(density)
        except Exception:
            return -np.inf
    return -np.inf

def perform_loocv(errors):
    """Perform Leave-One-Out Cross-Validation for model comparison."""
    print(f"    Performing LOO-CV on {len(errors)} trials...")
    log_lik_sums = {'von_mises': 0, 'mixture': 0, 'wrapped_normal': 0, 'wrapped_cauchy': 0}
    valid_folds = {'von_mises': 0, 'mixture': 0, 'wrapped_normal': 0, 'wrapped_cauchy': 0}
    
    for i in range(len(errors)):
        train_data = np.delete(errors, i)
        test_point = errors[i]
        if len(train_data) < 5:
            continue
        vm_fit = fit_von_mises_python(train_data)
        mix_fit = fit_mixture_model_python(train_data)
        wn_fit = fit_wrapped_normal_python(train_data)
        wc_fit = fit_wrapped_cauchy_python(train_data)
        
        if vm_fit.get('converged', False):
            ll = calculate_log_density(test_point, 'von_mises', vm_fit)
            if not np.isinf(ll) and not np.isnan(ll):
                log_lik_sums['von_mises'] += ll
                valid_folds['von_mises'] += 1
        if mix_fit.get('converged', False):
            ll = calculate_log_density(test_point, 'mixture', mix_fit)
            if not np.isinf(ll) and not np.isnan(ll):
                log_lik_sums['mixture'] += ll
                valid_folds['mixture'] += 1
        if wn_fit.get('converged', False):
            ll = calculate_log_density(test_point, 'wrapped_normal', wn_fit)
            if not np.isinf(ll) and not np.isnan(ll):
                log_lik_sums['wrapped_normal'] += ll
                valid_folds['wrapped_normal'] += 1
        if wc_fit.get('converged', False):
            ll = calculate_log_density(test_point, 'wrapped_cauchy', wc_fit)
            if not np.isinf(ll) and not np.isnan(ll):
                log_lik_sums['wrapped_cauchy'] += ll
                valid_folds['wrapped_cauchy'] += 1
    
    # Set to -inf if no valid folds
    for dist in log_lik_sums:
        if valid_folds[dist] == 0:
            log_lik_sums[dist] = -np.inf
    
    return log_lik_sums

def process_participant(participant_id, participant_data):
    """
    Process a single participant's data to fit circular distributions.
    """
    print(f"Processing participant: {participant_id}")

    # Extract error data
    errors = participant_data['VWM_error_radians'].dropna().values
    valid_trials = len(errors)

    print(f"  Valid trials: {valid_trials}")
    if valid_trials > 0:
        print(f"  Error range: [{np.min(errors):.3f}, {np.max(errors):.3f}] radians")
        print(f"  Mean error magnitude: {np.mean(np.abs(errors)):.3f} radians")

    if valid_trials < 5:  # Minimum threshold
        print(f"  Insufficient data for participant {participant_id}")
        main_results = {
            'participantId': participant_id,
            'vonMises_kappa': np.nan,
            'vonMises_mu': np.nan,
            'vonMises_loglikelihood': np.nan,
            'vonMises_AIC': np.nan,
            'vonMises_BIC': np.nan,
            'mixture_guess_proportion': np.nan,
            'mixture_precision_nonguess': np.nan,
            'mixture_loglikelihood': np.nan,
            'mixture_AIC': np.nan,
            'mixture_BIC': np.nan,
            'wrapped_normal_AIC': np.nan,
            'wrapped_cauchy_AIC': np.nan,
            'best_fitting_distribution': 'insufficient_data',
            'valid_trials_count': valid_trials,
            'parameter_estimation_reliable': False
        }
        return main_results, {}

    # Fit von Mises distribution
    print(f"  Fitting von Mises distribution... (using Python)")
    vm_results = fit_von_mises_python(errors)
    if vm_results.get('converged', False):
        print(f"    Converged: kappa={vm_results.get('kappa', np.nan):.3f}, mu={vm_results.get('mu', np.nan):.3f}")
        print(f"    AIC={vm_results.get('AIC', np.nan):.2f}")
    else:
        print(f"    Failed to converge")

    # Fit mixture model
    print(f"  Fitting mixture model... (using Python)")
    mixture_results = fit_mixture_model_python(errors)
    if mixture_results.get('converged', False):
        print(f"    Converged: guess_prop={mixture_results.get('guess_proportion', np.nan):.3f}, kappa={mixture_results.get('precision_nonguess', np.nan):.3f}")
        print(f"    AIC={mixture_results.get('AIC', np.nan):.2f}")
    else:
        print(f"    Failed to converge")

    # Fit alternative distributions
    print(f"  Fitting wrapped normal...")
    wn_results = fit_wrapped_normal_python(errors)
    if wn_results.get('converged', False):
        print(f"    Converged: AIC={wn_results['AIC']:.2f}")
    else:
        print(f"    Failed to converge")

    print(f"  Fitting wrapped Cauchy...")
    wc_results = fit_wrapped_cauchy_python(errors)
    if wc_results.get('converged', False):
        print(f"    Converged: AIC={wc_results['AIC']:.2f}")
    else:
        print(f"    Failed to converge")

    # Perform LOO-CV for model comparison
    print(f"  Performing LOO-CV for model comparison...")
    loocv_scores = perform_loocv(errors)

    # Determine best fitting distribution based on LOO-CV
    best_dist = max(loocv_scores.keys(), key=lambda k: loocv_scores[k])
    if np.isnan(loocv_scores[best_dist]) or np.isinf(loocv_scores[best_dist]):
        best_dist = 'none_converged'

    # Check parameter reliability
    reliable = (valid_trials >= 20 and
                vm_results.get('converged', False) and
                mixture_results.get('converged', False))

    print(f"  Best fitting distribution: {best_dist}")
    print(f"  Parameter estimation reliable: {reliable}")

    main_results = {
        'participantId': participant_id,
        'vonMises_kappa': vm_results.get('kappa', np.nan),
        'vonMises_mu': vm_results.get('mu', np.nan),
        'vonMises_loglikelihood': vm_results.get('loglikelihood', np.nan),
        'vonMises_AIC': vm_results.get('AIC', np.nan),
        'vonMises_BIC': vm_results.get('BIC', np.nan),
        'mixture_guess_proportion': mixture_results.get('guess_proportion', np.nan),
        'mixture_precision_nonguess': mixture_results.get('precision_nonguess', np.nan),
        'mixture_loglikelihood': mixture_results.get('loglikelihood', np.nan),
        'mixture_AIC': mixture_results.get('AIC', np.nan),
        'mixture_BIC': mixture_results.get('BIC', np.nan),
        'wrapped_normal_AIC': wn_results.get('AIC', np.nan),
        'wrapped_cauchy_AIC': wc_results.get('AIC', np.nan),
        'best_fitting_distribution': best_dist,
        'valid_trials_count': valid_trials,
        'parameter_estimation_reliable': reliable
    }
    return main_results, loocv_scores

def validate_parameters(results_df):
    """
    Validate fitted parameters and flag any issues.
    
    Parameters:
    -----------
    results_df : pd.DataFrame
        DataFrame with fitted parameters
        
    Returns:
    --------
    pd.DataFrame
        Validated DataFrame with any corrections
    """
    print("Validating fitted parameters...")
    
    # Check kappa parameters are positive
    invalid_kappa = results_df['vonMises_kappa'] <= 0
    print(f"Participants with invalid kappa values: {invalid_kappa.sum()}")
    
    # Check mu parameters are within 0-2π range
    invalid_mu = ((results_df['vonMises_mu'] < 0) | 
                  (results_df['vonMises_mu'] > 2*np.pi))
    print(f"Participants with mu values outside [0, 2π]: {invalid_mu.sum()}")
    
    # Check mixture proportions are valid
    invalid_prop = ((results_df['mixture_guess_proportion'] < 0) | 
                    (results_df['mixture_guess_proportion'] > 1))
    print(f"Participants with invalid mixture proportions: {invalid_prop.sum()}")
    
    # Count convergence failures
    vm_failures = results_df['vonMises_AIC'].isna().sum()
    mixture_failures = results_df['mixture_AIC'].isna().sum()
    
    print(f"Von Mises convergence failures: {vm_failures}")
    print(f"Mixture model convergence failures: {mixture_failures}")
    
    return results_df

def create_model_validation_summary(results_df, loocv_df):
    """
    Create model validation summary statistics.
    
    Parameters:
    -----------
    results_df : pd.DataFrame
        DataFrame with fitted parameters
    loocv_df : pd.DataFrame
        DataFrame with LOO-CV scores
        
    Returns:
    --------
    pd.DataFrame
        Summary statistics for model validation
    """
    print("Creating model validation summary...")
    
    # Count best fitting distributions
    best_fits = results_df['best_fitting_distribution'].value_counts()
    total_participants = len(results_df)
    
    print("Best fitting distribution counts:")
    print(best_fits)
    
    # Calculate convergence rates
    distributions = ['von_mises', 'mixture', 'wrapped_normal', 'wrapped_cauchy']
    
    validation_data = []
    
    for dist in distributions:
        if dist == 'von_mises':
            converged = ~results_df['vonMises_AIC'].isna()
        elif dist == 'mixture':
            converged = ~results_df['mixture_AIC'].isna()
        elif dist == 'wrapped_normal':
            converged = ~results_df['wrapped_normal_AIC'].isna()
        elif dist == 'wrapped_cauchy':
            converged = ~results_df['wrapped_cauchy_AIC'].isna()
        
        convergence_rate = converged.mean()
        
        # Proportion of best fits
        prop_best = best_fits.get(dist, 0) / total_participants
        
        # Calculate mean and std of LOO-CV scores
        if not loocv_df.empty and dist in loocv_df.columns:
            mean_loocv = loocv_df[dist].mean()
            sd_loocv = loocv_df[dist].std()
        else:
            mean_loocv = np.nan
            sd_loocv = np.nan

        validation_data.append({
            'distribution_type': dist,
            'mean_LOO_CV_score': mean_loocv,
            'sd_LOO_CV_score': sd_loocv,
            'proportion_best_fits': prop_best,
            'convergence_rate': convergence_rate
        })
    
    validation_df = pd.DataFrame(validation_data)
    
    print("Model validation summary:")
    print(validation_df)
    
    return validation_df

def main():
    """
    Main function to execute the VWM parameter estimation task.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("Starting VWM parameter estimation analysis...")
        print(f"Analysis started at: {datetime.now()}")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Created/verified outputs directory")
        
        # Find the most recent input file
        input_pattern = 'outputs/VWM_cleaned_data_*.csv'
        try:
            input_file = find_latest_file(input_pattern)
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            print("Error: Failed to load or validate data")
            return 1
        
        # Filter data
        df_filtered = filter_data(df)
        if len(df_filtered) == 0:
            print("Error: No data remaining after filtering")
            return 1
        
        # Process each participant
        print("\nProcessing participants...")
        participants = df_filtered['participantId'].unique()
        print(f"Total participants to process: {len(participants)}")
        
        results = []
        all_loocv_scores = []
        for i, participant_id in enumerate(participants):
            print(f"\nProgress: {i+1}/{len(participants)}")
            
            participant_data = df_filtered[df_filtered['participantId'] == participant_id]
            result, loocv_scores = process_participant(participant_id, participant_data)
            results.append(result)
            if loocv_scores:
                loocv_scores['participantId'] = participant_id
                all_loocv_scores.append(loocv_scores)

        # Create results dataframes
        results_df = pd.DataFrame(results)
        loocv_df = pd.DataFrame(all_loocv_scores)
        print(f"\nCreated results dataframe with shape: {results_df.shape}")
        
        print("Results dataframe columns:")
        print(results_df.columns.tolist())
        print("\nFirst 2 rows of results:")
        print(results_df.head(2))
        
        # Validate parameters
        results_df = validate_parameters(results_df)
        
        # Create timestamp for output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save main results (only required columns)
        required_cols = [
            'participantId',
            'vonMises_kappa',
            'vonMises_mu',
            'vonMises_loglikelihood',
            'vonMises_AIC',
            'vonMises_BIC',
            'mixture_guess_proportion',
            'mixture_precision_nonguess',
            'mixture_loglikelihood',
            'mixture_AIC',
            'mixture_BIC',
            'wrapped_normal_AIC',
            'wrapped_cauchy_AIC',
            'best_fitting_distribution',
            'valid_trials_count',
            'parameter_estimation_reliable'
        ]
        results_df_out = results_df[required_cols].copy()
        output_file = f'outputs/VWM_parameters_{timestamp}.csv'
        results_df_out.to_csv(output_file, index=False)
        print(f"\nSaved main results to: {output_file}")
        
        # Create and save model validation summary
        validation_df = create_model_validation_summary(results_df, loocv_df)
        validation_file = f'outputs/model_validation_results_{timestamp}.csv'
        validation_df.to_csv(validation_file, index=False)
        print(f"Saved validation results to: {validation_file}")
        
        # Final summary statistics
        print(f"\nFinal Summary:")
        print(f"Total participants processed: {len(results_df)}")
        print(f"Participants with reliable parameter estimates: {results_df['parameter_estimation_reliable'].sum()}")
        print(f"Mean valid trials per participant: {results_df['valid_trials_count'].mean():.1f}")
        
        print(f"\nAnalysis completed at: {datetime.now()}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
