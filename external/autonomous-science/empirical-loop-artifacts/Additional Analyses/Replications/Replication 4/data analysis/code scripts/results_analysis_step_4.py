#!/usr/bin/env python3
"""
Von Mises Distribution Parameter Estimation Script

This script fits von Mises distributions to visual working memory error data
using maximum likelihood estimation. It processes cleaned trial data and 
estimates concentration (kappa) and bias (mu) parameters both overall and
by experimental conditions.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats
from scipy.optimize import minimize
from scipy.stats import vonmises
import warnings
from scipy.special import iv

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/cleaned_vwm_data_*.csv')
    
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Sort by modification time and return the most recent
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def convert_degrees_to_radians(degrees):
    """
    Convert degrees to radians for circular statistics.
    
    Parameters:
    -----------
    degrees : array-like
        Error values in degrees (±90°)
    
    Returns:
    --------
    numpy.ndarray
        Error values in radians (±π/2)
    """
    return np.array(degrees) * np.pi / 180.0

def negative_log_likelihood_vonmises(params, data):
    """
    Negative log-likelihood function for von Mises distribution.
    
    Parameters:
    -----------
    params : array-like
        Parameters [mu, kappa] where mu is location and kappa is concentration
    data : array-like
        Circular data in radians
    
    Returns:
    --------
    float
        Negative log-likelihood value
    """
    mu, kappa = params
    
    # Ensure kappa is positive
    if kappa <= 0:
        return np.inf
    
    # Calculate negative log-likelihood
    n = len(data)
    log_likelihood = n * np.log(2 * np.pi * iv(0, kappa)) - kappa * np.sum(np.cos(data - mu))
    
    return log_likelihood

def _fit_vonmises_params_only(data):
    """
    Lightweight von Mises fitter for bootstrap that only returns parameters.
    
    Parameters:
    -----------
    data : array-like
        Circular data in radians
    
    Returns:
    --------
    tuple
        (mu, kappa, convergence_success)
    """
    data = np.array(data)
    n = len(data)
    
    if n < 3:
        return np.nan, np.nan, False
    
    # Initial parameter estimates (same as in fit_vonmises_mle)
    circular_mean = np.arctan2(np.mean(np.sin(data)), np.mean(np.cos(data)))
    r_bar = np.sqrt(np.mean(np.cos(data))**2 + np.mean(np.sin(data))**2)
    
    if r_bar < 0.53:
        kappa_init = 2 * r_bar + r_bar**3 + 5 * r_bar**5 / 6
    elif r_bar < 0.85:
        kappa_init = -0.4 + 1.39 * r_bar + 0.43 / (1 - r_bar)
    else:
        kappa_init = 1 / (3 * r_bar - 4 * r_bar**2 + r_bar**3)
    
    kappa_init = max(0.1, kappa_init)
    initial_params = [circular_mean, kappa_init]
    
    # Perform optimization (same as in fit_vonmises_mle but no Hessian calculation)
    try:
        result = minimize(
            negative_log_likelihood_vonmises,
            initial_params,
            args=(data,),
            method='L-BFGS-B',
            bounds=[(-np.pi, np.pi), (0.01, 100)],
            options={'maxiter': 1000}
        )
        
        mu_fit, kappa_fit = result.x
        convergence = result.success
        
        return mu_fit, kappa_fit, convergence
        
    except Exception:
        return np.nan, np.nan, False

def fit_vonmises_mle(data):
    """
    Fit von Mises distribution using maximum likelihood estimation.
    
    Parameters:
    -----------
    data : array-like
        Circular data in radians
    
    Returns:
    --------
    dict
        Dictionary containing fitted parameters and diagnostics:
        - mu: location parameter
        - kappa: concentration parameter
        - mu_se: standard error of mu
        - kappa_se: standard error of kappa
        - mu_ci_lower, mu_ci_upper: 95% CI for mu
        - kappa_ci_lower, kappa_ci_upper: 95% CI for kappa
        - aic: Akaike Information Criterion
        - bic: Bayesian Information Criterion
        - loglik: log-likelihood
        - convergence: whether optimization converged
    """
    data = np.array(data)
    n = len(data)
    
    if n < 3:
        # Not enough data for reliable fitting
        return {
            'mu': np.nan, 'kappa': np.nan,
            'mu_se': np.nan, 'kappa_se': np.nan,
            'mu_ci_lower': np.nan, 'mu_ci_upper': np.nan,
            'kappa_ci_lower': np.nan, 'kappa_ci_upper': np.nan,
            'aic': np.nan, 'bic': np.nan, 'loglik': np.nan,
            'convergence': False
        }
    
    # Initial parameter estimates
    # Use circular mean for mu and estimate kappa from concentration
    circular_mean = np.arctan2(np.mean(np.sin(data)), np.mean(np.cos(data)))
    r_bar = np.sqrt(np.mean(np.cos(data))**2 + np.mean(np.sin(data))**2)
    
    # Initial kappa estimate using approximation
    if r_bar < 0.53:
        kappa_init = 2 * r_bar + r_bar**3 + 5 * r_bar**5 / 6
    elif r_bar < 0.85:
        kappa_init = -0.4 + 1.39 * r_bar + 0.43 / (1 - r_bar)
    else:
        kappa_init = 1 / (3 * r_bar - 4 * r_bar**2 + r_bar**3)
    
    kappa_init = max(0.1, kappa_init)  # Ensure positive
    
    initial_params = [circular_mean, kappa_init]
    
    # Perform optimization
    try:
        result = minimize(
            negative_log_likelihood_vonmises,
            initial_params,
            args=(data,),
            method='L-BFGS-B',
            bounds=[(-np.pi, np.pi), (0.01, 100)],
            options={'maxiter': 1000}
        )
        
        mu_fit, kappa_fit = result.x
        convergence = result.success
        
        # Calculate Fisher Information Matrix for standard errors
        # Approximate using finite differences
        eps = 1e-6
        
        # Second derivatives for Fisher Information
        def hessian_element(i, j, params):
            params_plus_i = params.copy()
            params_plus_i[i] += eps
            params_minus_i = params.copy()
            params_minus_i[i] -= eps
            
            if i == j:
                # Second derivative with respect to same parameter
                f_plus = negative_log_likelihood_vonmises(params_plus_i, data)
                f_minus = negative_log_likelihood_vonmises(params_minus_i, data)
                f_center = negative_log_likelihood_vonmises(params, data)
                return (f_plus - 2*f_center + f_minus) / (eps**2)
            else:
                # Mixed partial derivative
                params_plus_ij = params.copy()
                params_plus_ij[i] += eps
                params_plus_ij[j] += eps
                
                params_plus_i_minus_j = params.copy()
                params_plus_i_minus_j[i] += eps
                params_plus_i_minus_j[j] -= eps
                
                params_minus_i_plus_j = params.copy()
                params_minus_i_plus_j[i] -= eps
                params_minus_i_plus_j[j] += eps
                
                params_minus_ij = params.copy()
                params_minus_ij[i] -= eps
                params_minus_ij[j] -= eps
                
                f_pp = negative_log_likelihood_vonmises(params_plus_ij, data)
                f_pm = negative_log_likelihood_vonmises(params_plus_i_minus_j, data)
                f_mp = negative_log_likelihood_vonmises(params_minus_i_plus_j, data)
                f_mm = negative_log_likelihood_vonmises(params_minus_ij, data)
                
                return (f_pp - f_pm - f_mp + f_mm) / (4 * eps**2)
        
        # Calculate Hessian matrix
        hessian = np.array([
            [hessian_element(0, 0, result.x), hessian_element(0, 1, result.x)],
            [hessian_element(1, 0, result.x), hessian_element(1, 1, result.x)]
        ])
        
        # Fisher Information is the Hessian of the negative log-likelihood
        fisher_info = hessian
        
        # Standard errors from inverse Fisher Information
        try:
            cov_matrix = np.linalg.inv(fisher_info)
            mu_se = np.sqrt(cov_matrix[0, 0])
            kappa_se = np.sqrt(cov_matrix[1, 1])
        except:
            # If Fisher Information is singular, use bootstrap
            mu_se = np.nan
            kappa_se = np.nan
        
        # Model fit statistics
        log_likelihood = -result.fun
        aic = 2 * 2 - 2 * log_likelihood  # 2 parameters
        bic = np.log(n) * 2 - 2 * log_likelihood
        
    except Exception as e:
        print(f"Optimization failed: {e}")
        convergence = False
        mu_fit = kappa_fit = np.nan
        mu_se = kappa_se = np.nan
        mu_ci_lower = mu_ci_upper = kappa_ci_lower = kappa_ci_upper = np.nan
        aic = bic = log_likelihood = np.nan
    
    return {
        'mu': mu_fit,
        'kappa': kappa_fit,
        'mu_se': mu_se,
        'kappa_se': kappa_se,
        'aic': aic,
        'bic': bic,
        'loglik': log_likelihood,
        'convergence': convergence
    }

def bootstrap_confidence_intervals(data, n_bootstrap=1000):
    """
    Calculate bootstrap confidence intervals for von Mises parameters.
    
    Parameters:
    -----------
    data : array-like
        Circular data in radians
    n_bootstrap : int
        Number of bootstrap iterations
    
    Returns:
    --------
    dict
        Bootstrap confidence intervals for mu and kappa
    """
    data = np.array(data)
    n = len(data)
    
    if n < 3:
        return {
            'mu_ci_lower': np.nan, 'mu_ci_upper': np.nan,
            'kappa_ci_lower': np.nan, 'kappa_ci_upper': np.nan
        }
    
    mu_bootstrap = []
    kappa_bootstrap = []
    
    for i in range(n_bootstrap):
        # Bootstrap sample
        bootstrap_indices = np.random.choice(n, size=n, replace=True)
        bootstrap_data = data[bootstrap_indices]
        
        # Fit von Mises to bootstrap sample using lightweight function
        mu_fit, kappa_fit, converged = _fit_vonmises_params_only(bootstrap_data)
        
        if converged and not np.isnan(mu_fit):
            mu_bootstrap.append(mu_fit)
            kappa_bootstrap.append(kappa_fit)
    
    if len(mu_bootstrap) > 0:
        mu_ci_lower = np.percentile(mu_bootstrap, 2.5)
        mu_ci_upper = np.percentile(mu_bootstrap, 97.5)
        kappa_ci_lower = np.percentile(kappa_bootstrap, 2.5)
        kappa_ci_upper = np.percentile(kappa_bootstrap, 97.5)
    else:
        mu_ci_lower = mu_ci_upper = kappa_ci_lower = kappa_ci_upper = np.nan
    
    return {
        'mu_ci_lower': mu_ci_lower,
        'mu_ci_upper': mu_ci_upper,
        'kappa_ci_lower': kappa_ci_lower,
        'kappa_ci_upper': kappa_ci_upper
    }

def main():
    """
    Main function to process visual working memory data and fit von Mises distributions.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting von Mises parameter estimation script...")
        print(f"Script started at: {datetime.now()}")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Created/verified outputs directory")
        
        # Find the most recent input file
        input_pattern = 'outputs/cleaned_vwm_data_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Load the data
        print("Loading data...")
        try:
            data = pd.read_csv(input_file)
            print(f"Successfully loaded data with shape: {data.shape}")
        except Exception as e:
            print(f"ERROR: Failed to load data from {input_file}: {e}")
            return 1
        
        # Print column information
        print("\nData columns:")
        print(data.columns.tolist())
        
        print("\nFirst 3 rows of data:")
        print(data.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'setSize', 'delay_s', 'error_degrees', 'excluded_trial']
        missing_columns = [col for col in required_columns if col not in data.columns]
        
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found")
        
        # Print unique values for experimental design parameters
        print("\nExperimental design parameter values:")
        print(f"Unique setSize values: {sorted(data['setSize'].unique())}")
        print(f"Unique delay_s values: {sorted(data['delay_s'].unique())}")
        print(f"Unique excluded_trial values: {sorted(data['excluded_trial'].unique())}")
        
        print(f"Error_degrees data type: {data['error_degrees'].dtype}")
        print(f"Error_degrees range: [{data['error_degrees'].min():.2f}, {data['error_degrees'].max():.2f}]")
        
        # Filter data for analysis
        print("\nFiltering data...")
        print(f"Total trials before filtering: {len(data)}")
        
        # Filter to valid trials only
        valid_data = data[data['excluded_trial'] == False].copy()
        print(f"Valid trials (excluded_trial=False): {len(valid_data)}")
        
        # Remove trials with missing error data
        valid_data = valid_data.dropna(subset=['error_degrees'])
        print(f"Trials after removing missing error_degrees: {len(valid_data)}")
        
        if len(valid_data) == 0:
            print("ERROR: No valid trials remaining after filtering")
            return 1
        
        # Convert error degrees to radians
        print("Converting degrees to radians...")
        valid_data['error_radians'] = convert_degrees_to_radians(valid_data['error_degrees'])
        
        print(f"Error range in radians: [{valid_data['error_radians'].min():.3f}, {valid_data['error_radians'].max():.3f}]")
        print(f"Expected range: [{-np.pi/2:.3f}, {np.pi/2:.3f}]")
        
        # Get unique participants
        participants = valid_data['participantId'].unique()
        print(f"\nFound {len(participants)} unique participants")
        
        # Initialize results lists
        overall_results = []
        condition_results = []
        
        # Define experimental conditions
        conditions = [
            (2, 1.0),  # Set Size 2, Delay 1000ms
            (2, 4.0),  # Set Size 2, Delay 4000ms
            (4, 1.0),  # Set Size 4, Delay 1000ms
            (4, 4.0)   # Set Size 4, Delay 4000ms
        ]
        
        print(f"Analyzing {len(conditions)} experimental conditions: {conditions}")
        
        # Process each participant
        for i, participant in enumerate(participants):
            print(f"\nProcessing participant {i+1}/{len(participants)}: {participant}")
            
            # Get participant data
            participant_data = valid_data[valid_data['participantId'] == participant]
            print(f"Participant has {len(participant_data)} valid trials")
            
            # Overall parameter estimation (collapsed across conditions)
            print("Fitting overall von Mises distribution...")
            overall_errors = participant_data['error_radians'].values
            
            if len(overall_errors) < 15:
                print(f"WARNING: Participant {participant} has only {len(overall_errors)} trials (< 15)")
            
            overall_fit = fit_vonmises_mle(overall_errors)
            
            # Add bootstrap confidence intervals for overall fit
            bootstrap_cis = bootstrap_confidence_intervals(overall_errors, n_bootstrap=1000)
            
            # Check for high uncertainty in overall fit
            if not np.isnan(overall_fit['kappa_se']) and not np.isnan(overall_fit['mu_se']):
                high_uncertainty_overall = (
                    (overall_fit['kappa_se'] > overall_fit['kappa']) or
                    (overall_fit['mu_se'] > np.abs(overall_fit['mu']))
                )
            else:
                high_uncertainty_overall = True

            # Check for poor fit using AIC/BIC outlier detection (will do this later across all participants)
            poor_fit_flag = False  # Will update this after processing all participants
            
            overall_result = {
                'participantId': participant,
                'kappa_overall': overall_fit['kappa'],
                'mu_overall': overall_fit['mu'],
                'kappa_se_overall': overall_fit['kappa_se'],
                'mu_se_overall': overall_fit['mu_se'],
                'kappa_ci_lower_overall': bootstrap_cis['kappa_ci_lower'],
                'kappa_ci_upper_overall': bootstrap_cis['kappa_ci_upper'],
                'mu_ci_lower_overall': bootstrap_cis['mu_ci_lower'],
                'mu_ci_upper_overall': bootstrap_cis['mu_ci_upper'],
                'aic_overall': overall_fit['aic'],
                'bic_overall': overall_fit['bic'],
                'loglik_overall': overall_fit['loglik'],
                'n_trials_overall': len(overall_errors),
                'poor_fit_flag': poor_fit_flag,
                'high_uncertainty_flag_overall': high_uncertainty_overall
            }
            
            overall_results.append(overall_result)
            
            print(f"Overall fit - kappa: {overall_fit['kappa']:.3f}, mu: {overall_fit['mu']:.3f}")
            print(f"Overall fit - AIC: {overall_fit['aic']:.2f}, BIC: {overall_fit['bic']:.2f}")
            
            # Condition-specific parameter estimation
            print("Fitting condition-specific von Mises distributions...")
            
            for setSize, delay_s in conditions:
                condition_data = participant_data[
                    (participant_data['setSize'] == setSize) & 
                    (participant_data['delay_s'] == delay_s)
                ]
                
                condition_errors = condition_data['error_radians'].values
                n_trials_condition = len(condition_errors)
                
                print(f"  Condition setSize={setSize}, delay_s={delay_s}: {n_trials_condition} trials")
                
                if n_trials_condition < 5:
                    print(f"    WARNING: Very few trials ({n_trials_condition}) for this condition")
                    # Still fit but flag convergence as poor
                    condition_fit = {
                        'mu': np.nan, 'kappa': np.nan,
                        'mu_se': np.nan, 'kappa_se': np.nan,
                        'mu_ci_lower': np.nan, 'mu_ci_upper': np.nan,
                        'kappa_ci_lower': np.nan, 'kappa_ci_upper': np.nan,
                        'aic': np.nan, 'bic': np.nan, 'loglik': np.nan,
                        'convergence': False
                    }
                    high_uncertainty_flag = True
                else:
                    condition_fit = fit_vonmises_mle(condition_errors)
                    
                    # Add bootstrap confidence intervals
                    condition_bootstrap_cis = bootstrap_confidence_intervals(condition_errors, n_bootstrap=1000)
                    condition_fit.update(condition_bootstrap_cis)
                    
                    # Check for high uncertainty in condition fit
                    if not np.isnan(condition_fit['kappa_se']) and not np.isnan(condition_fit['mu_se']):
                        high_uncertainty_flag = (
                            (condition_fit['kappa_se'] > condition_fit['kappa']) or
                            (condition_fit['mu_se'] > np.abs(condition_fit['mu']))
                        )
                    else:
                        high_uncertainty_flag = True
                
                condition_result = {
                    'participantId': participant,
                    'setSize': setSize,
                    'delay_s': delay_s,
                    'kappa': condition_fit['kappa'],
                    'mu': condition_fit['mu'],
                    'kappa_se': condition_fit['kappa_se'],
                    'mu_se': condition_fit['mu_se'],
                    'kappa_ci_lower': condition_fit.get('kappa_ci_lower', np.nan),
                    'kappa_ci_upper': condition_fit.get('kappa_ci_upper', np.nan),
                    'mu_ci_lower': condition_fit.get('mu_ci_lower', np.nan),
                    'mu_ci_upper': condition_fit.get('mu_ci_upper', np.nan),
                    'aic': condition_fit['aic'],
                    'bic': condition_fit['bic'],
                    'loglik': condition_fit['loglik'],
                    'n_trials': n_trials_condition,
                    'convergence_flag': condition_fit['convergence'],
                    'high_uncertainty_flag': high_uncertainty_flag
                }
                
                condition_results.append(condition_result)
                
                if condition_fit['convergence']:
                    print(f"    Fit - kappa: {condition_fit['kappa']:.3f}, mu: {condition_fit['mu']:.3f}")
                else:
                    print(f"    Fit failed to converge")
        
        print(f"\nCompleted fitting for all {len(participants)} participants")
        
        # Convert results to DataFrames
        overall_df = pd.DataFrame(overall_results)
        condition_df = pd.DataFrame(condition_results)
        
        print("\nOverall results DataFrame:")
        print("Columns:", overall_df.columns.tolist())
        print("First 2 rows:")
        print(overall_df.head(2))
        
        print("\nCondition results DataFrame:")
        print("Columns:", condition_df.columns.tolist())
        print("First 2 rows:")
        print(condition_df.head(2))
        
        # Quality control: Flag participants with poor model fits
        print("\nPerforming quality control...")
        
        # Calculate AIC/BIC outliers for overall fits
        valid_aic = overall_df['aic_overall'].dropna()
        valid_bic = overall_df['bic_overall'].dropna()
        
        if len(valid_aic) > 0:
            aic_mean = valid_aic.mean()
            aic_std = valid_aic.std()
            aic_outlier_threshold = aic_mean + 3 * aic_std
            
            bic_mean = valid_bic.mean()
            bic_std = valid_bic.std()
            bic_outlier_threshold = bic_mean + 3 * bic_std
            
            print(f"AIC outlier threshold (mean + 3*SD): {aic_outlier_threshold:.2f}")
            print(f"BIC outlier threshold (mean + 3*SD): {bic_outlier_threshold:.2f}")
            
            # Update poor fit flags
            poor_fit_mask = (
                (overall_df['aic_overall'] > aic_outlier_threshold) |
                (overall_df['bic_overall'] > bic_outlier_threshold) |
                (overall_df['n_trials_overall'] < 15)
            )
            
            overall_df['poor_fit_flag'] = poor_fit_mask
            
            n_poor_fits = poor_fit_mask.sum()
            print(f"Flagged {n_poor_fits} participants with poor fits")
        else:
            print("No valid AIC/BIC values found for quality control")
            overall_df['poor_fit_flag'] = True
        
        # Validation checks
        print("\nValidation checks:")
        
        # Check parameter ranges
        valid_kappa_mask = (overall_df['kappa_overall'] > 0) & (overall_df['kappa_overall'] < 100)
        valid_mu_mask = (overall_df['mu_overall'] >= -np.pi) & (overall_df['mu_overall'] <= np.pi)
        
        print(f"Participants with valid kappa (>0, <100): {valid_kappa_mask.sum()}/{len(overall_df)}")
        print(f"Participants with valid mu (-π to π): {valid_mu_mask.sum()}/{len(overall_df)}")
        
        # Check convergence for condition fits
        convergence_rates = condition_df.groupby(['setSize', 'delay_s'])['convergence_flag'].mean()
        print("\nConvergence rates by condition:")
        for (setSize, delay_s), rate in convergence_rates.items():
            print(f"  SetSize {setSize}, Delay {delay_s}s: {rate:.2%}")
        
        # Check trial counts
        insufficient_trials_overall = (overall_df['n_trials_overall'] < 15).sum()
        insufficient_trials_condition = (condition_df['n_trials'] < 15).sum()
        
        print(f"\nParticipants with <15 trials overall: {insufficient_trials_overall}")
        print(f"Condition fits with <15 trials: {insufficient_trials_condition}")
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        overall_output_file = f'outputs/vonmises_parameters_overall_{timestamp}.csv'
        condition_output_file = f'outputs/vonmises_parameters_conditions_{timestamp}.csv'
        
        print(f"\nSaving results...")
        print(f"Overall parameters: {overall_output_file}")
        print(f"Condition parameters: {condition_output_file}")
        
        # Save overall results
        overall_df.to_csv(overall_output_file, index=False)
        print(f"Saved overall results: {len(overall_df)} participants")
        
        # Save condition results
        condition_df.to_csv(condition_output_file, index=False)
        print(f"Saved condition results: {len(condition_df)} condition fits")
        
        # Final summary
        print("\nFinal Summary:")
        print(f"Total participants processed: {len(participants)}")
        print(f"Participants with poor overall fits: {overall_df['poor_fit_flag'].sum()}")
        print(f"Overall convergence rate: {(~overall_df['kappa_overall'].isna()).sum()}/{len(overall_df)}")
        print(f"Condition convergence rate: {condition_df['convergence_flag'].sum()}/{len(condition_df)}")
        
        print("\nParameter summary (overall fits):")
        print(f"Kappa (concentration) - Mean: {overall_df['kappa_overall'].mean():.3f}, SD: {overall_df['kappa_overall'].std():.3f}")
        print(f"Mu (bias) - Mean: {overall_df['mu_overall'].mean():.3f}, SD: {overall_df['mu_overall'].std():.3f}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Script failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
