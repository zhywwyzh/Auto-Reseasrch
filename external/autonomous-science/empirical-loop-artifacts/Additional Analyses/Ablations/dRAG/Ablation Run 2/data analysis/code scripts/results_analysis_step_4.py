#!/usr/bin/env python3
"""
VWM Mixture Model Parameter Estimation Script

This script processes visual working memory (VWM) experimental data and fits
two-component mixture models to estimate precision and guess rate parameters
for each participant.
"""

import os
import glob
import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import minimize
from scipy.special import i0  # Modified Bessel function of the first kind
import warnings
from datetime import datetime

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/cleaned_experimental_data_*.csv')
    
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, return most recent
    return max(files, key=os.path.getmtime)

def normalize_angles_to_pi(angles_rad):
    """
    Normalize angles to the range [-π, π].
    
    Parameters:
    -----------
    angles_rad : array-like
        Angles in radians
    
    Returns:
    --------
    numpy.ndarray
        Normalized angles in range [-π, π]
    """
    return np.arctan2(np.sin(angles_rad), np.cos(angles_rad))

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
        Probability density values
    """
    return np.exp(kappa * np.cos(x - mu)) / (2 * np.pi * i0(kappa))

def mixture_model_pdf(x, mu, kappa, p):
    """
    Probability density function for two-component mixture model.
    
    Parameters:
    -----------
    x : array-like
        Angles in radians
    mu : float
        Mean direction of von Mises component
    kappa : float
        Concentration parameter of von Mises component
    p : float
        Mixing proportion for von Mises component (1-p = uniform proportion)
    
    Returns:
    --------
    numpy.ndarray
        Mixture model probability density values
    """
    von_mises_component = von_mises_pdf(x, mu, kappa)
    uniform_component = 1.0 / (2 * np.pi)  # Uniform distribution on [-π, π]
    return p * von_mises_component + (1 - p) * uniform_component

def negative_log_likelihood(params, data):
    """
    Negative log-likelihood function for mixture model.
    
    Parameters:
    -----------
    params : array-like
        Model parameters [mu, kappa, p]
    data : array-like
        Observed angular errors in radians
    
    Returns:
    --------
    float
        Negative log-likelihood value
    """
    mu, kappa, p = params
    
    # Calculate mixture model PDF
    pdf_values = mixture_model_pdf(data, mu, kappa, p)
    
    # Avoid log(0) by adding small epsilon
    pdf_values = np.maximum(pdf_values, 1e-10)
    
    # Return negative log-likelihood
    return -np.sum(np.log(pdf_values))

def uniform_log_likelihood(data):
    """
    Log-likelihood for uniform-only model (null model).
    
    Parameters:
    -----------
    data : array-like
        Observed angular errors in radians
    
    Returns:
    --------
    float
        Log-likelihood value for uniform model
    """
    n = len(data)
    return n * np.log(1.0 / (2 * np.pi))

def fit_mixture_model(data):
    """
    Fit two-component mixture model to angular error data.
    
    Parameters:
    -----------
    data : array-like
        Angular errors in radians
    
    Returns:
    --------
    dict
        Dictionary containing fitted parameters and fit statistics:
        - mu_bias_radians: Mean direction bias
        - kappa_concentration: Concentration parameter
        - guess_rate_proportion: Proportion of random guesses (1-p)
        - model_aic: AIC for mixture model
        - null_model_aic: AIC for uniform model
        - delta_aic: Difference in AIC (null - mixture)
        - convergence_successful: Boolean indicating convergence
        - fit_quality_flag: Boolean indicating good fit quality
    """
    
    print(f"    Fitting mixture model to {len(data)} data points")
    
    # Initial parameter values
    initial_params = [0.0, 1.0, 0.8]  # [mu, kappa, p]
    
    # Parameter bounds
    bounds = [(-np.pi, np.pi),  # mu bounds
              (0.01, 50.0),     # kappa bounds  
              (0.01, 0.99)]     # p bounds
    
    try:
        # Minimize negative log-likelihood
        result = minimize(negative_log_likelihood, 
                         initial_params, 
                         args=(data,),
                         method='L-BFGS-B',
                         bounds=bounds)
        
        convergence_successful = result.success
        
        if convergence_successful:
            mu_fit, kappa_fit, p_fit = result.x
            
            # Calculate AIC for mixture model
            n_params_mixture = 3
            mixture_nll = result.fun
            model_aic = 2 * n_params_mixture + 2 * mixture_nll
            
            # Calculate AIC for uniform model
            uniform_ll = uniform_log_likelihood(data)
            n_params_uniform = 0
            null_model_aic = 2 * n_params_uniform - 2 * uniform_ll
            
            # Calculate delta AIC
            delta_aic = null_model_aic - model_aic
            
            # Check fit quality (mixture model should improve fit)
            fit_quality_flag = delta_aic >= 2.0
            
            # Check for boundary conditions
            if kappa_fit <= 0.02 or kappa_fit >= 49.9:
                fit_quality_flag = False
                print(f"    Warning: kappa at boundary condition ({kappa_fit:.3f})")
            
            print(f"    Fitted parameters: μ={mu_fit:.3f}, κ={kappa_fit:.3f}, p={p_fit:.3f}")
            print(f"    Model AIC: {model_aic:.2f}, Null AIC: {null_model_aic:.2f}, ΔAIC: {delta_aic:.2f}")
            
        else:
            print(f"    Optimization failed: {result.message}")
            mu_fit, kappa_fit, p_fit = np.nan, np.nan, np.nan
            model_aic, null_model_aic, delta_aic = np.nan, np.nan, np.nan
            fit_quality_flag = False
            
    except Exception as e:
        print(f"    Error during optimization: {str(e)}")
        convergence_successful = False
        mu_fit, kappa_fit, p_fit = np.nan, np.nan, np.nan
        model_aic, null_model_aic, delta_aic = np.nan, np.nan, np.nan
        fit_quality_flag = False
    
    return {
        'mu_bias_radians': mu_fit,
        'kappa_concentration': kappa_fit,
        'guess_rate_proportion': 1 - p_fit if not np.isnan(p_fit) else np.nan,
        'model_aic': model_aic,
        'null_model_aic': null_model_aic,
        'delta_aic': delta_aic,
        'convergence_successful': convergence_successful,
        'fit_quality_flag': fit_quality_flag
    }

def main():
    """
    Main function to process VWM data and fit mixture models.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    
    print("Starting VWM mixture model parameter estimation")
    print("=" * 60)
    
    try:
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        print("Created/verified outputs directory")
        
        # Find input file
        input_pattern = 'outputs/cleaned_experimental_data_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Load data
        print("\nLoading experimental data...")
        try:
            df = pd.read_csv(input_file)
            df.columns = df.columns.str.strip()
            print(f"Successfully loaded data with shape: {df.shape}")
        except Exception as e:
            print(f"ERROR: Failed to load input file: {str(e)}")
            return 1
        
        # Print all columns
        print("\nAll columns in input data:")
        print(list(df.columns))
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'table', 'isPractice', 'VWM_error_degrees']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"table values: {sorted(df['table'].unique())}")
        print(f"isPractice values: {sorted(df['isPractice'].unique())}")
        print(f"VWM_error_degrees data type: {df['VWM_error_degrees'].dtype}")
        
        # Filter data for VWM test trials
        print("\nFiltering data for VWM test trials...")
        print(f"Initial data shape: {df.shape}")
        
        # Filter for VWM test trials (isPractice = False AND table = "vwm_test")
        vwm_data = df[(df['isPractice'] == False) & (df['table'] == 'vwm_test')].copy()
        print(f"After filtering for VWM test trials: {vwm_data.shape}")
        
        if len(vwm_data) == 0:
            print("ERROR: No VWM test trials found after filtering")
            return 1
        
        # Check for missing VWM error values
        missing_errors = vwm_data['VWM_error_degrees'].isna().sum()
        print(f"Missing VWM_error_degrees values: {missing_errors}")
        
        if missing_errors > 0:
            vwm_data = vwm_data.dropna(subset=['VWM_error_degrees'])
            print(f"After removing missing error values: {vwm_data.shape}")
        
        # Convert errors to radians and normalize
        print("\nConverting errors to radians and normalizing...")
        vwm_data['VWM_error_radians'] = np.deg2rad(vwm_data['VWM_error_degrees'])
        vwm_data['VWM_error_radians_norm'] = normalize_angles_to_pi(vwm_data['VWM_error_radians'])
        
        print(f"Error range in degrees: [{vwm_data['VWM_error_degrees'].min():.1f}, {vwm_data['VWM_error_degrees'].max():.1f}]")
        print(f"Normalized error range in radians: [{vwm_data['VWM_error_radians_norm'].min():.3f}, {vwm_data['VWM_error_radians_norm'].max():.3f}]")
        
        # Group by participant and check trial counts
        print("\nGrouping data by participant...")
        participant_groups = vwm_data.groupby('participantId')
        participant_trial_counts = participant_groups.size()
        
        print(f"Number of unique participants: {len(participant_trial_counts)}")
        print(f"Trial count statistics:")
        print(f"  Mean: {participant_trial_counts.mean():.1f}")
        print(f"  Median: {participant_trial_counts.median():.1f}")
        print(f"  Min: {participant_trial_counts.min()}")
        print(f"  Max: {participant_trial_counts.max()}")
        
        # Apply minimum trial requirement (80 trials)
        min_trials = 80
        eligible_participants = participant_trial_counts[participant_trial_counts >= min_trials].index
        excluded_participants = participant_trial_counts[participant_trial_counts < min_trials]
        
        print(f"\nParticipants with >= {min_trials} trials: {len(eligible_participants)}")
        print(f"Participants excluded (< {min_trials} trials): {len(excluded_participants)}")
        
        if len(excluded_participants) > 0:
            print("Excluded participants and their trial counts:")
            for pid, count in excluded_participants.items():
                print(f"  {pid}: {count} trials")
        
        if len(eligible_participants) == 0:
            print("ERROR: No participants meet minimum trial requirement")
            return 1
        
        # Fit mixture models for each eligible participant
        print(f"\nFitting mixture models for {len(eligible_participants)} participants...")
        results_list = []
        
        for i, participant_id in enumerate(eligible_participants):
            print(f"\nProcessing participant {i+1}/{len(eligible_participants)}: {participant_id}")
            
            # Get participant's error data
            participant_data = vwm_data[vwm_data['participantId'] == participant_id]['VWM_error_radians_norm'].values
            n_trials = len(participant_data)
            
            print(f"  Processing {n_trials} trials")
            
            # Fit mixture model
            fit_results = fit_mixture_model(participant_data)
            
            # Compile results
            result_row = {
                'participantId': participant_id,
                'kappa_concentration': fit_results['kappa_concentration'],
                'mu_bias_radians': fit_results['mu_bias_radians'],
                'guess_rate_proportion': fit_results['guess_rate_proportion'],
                'model_aic': fit_results['model_aic'],
                'null_model_aic': fit_results['null_model_aic'],
                'delta_aic': fit_results['delta_aic'],
                'convergence_successful': fit_results['convergence_successful'],
                'fit_quality_flag': fit_results['fit_quality_flag'],
                'n_trials_used': n_trials
            }
            
            results_list.append(result_row)
        
        # Create results dataframe
        print("\nCompiling results...")
        results_df = pd.DataFrame(results_list)
        
        print(f"Results dataframe shape: {results_df.shape}")
        print("\nResults dataframe columns:")
        print(list(results_df.columns))
        print("\nFirst 2 rows of results:")
        print(results_df.head(2))
        
        # Print summary statistics
        print("\nSummary of fitting results:")
        successful_fits = results_df['convergence_successful'].sum()
        quality_fits = results_df['fit_quality_flag'].sum()
        
        print(f"Successful convergence: {successful_fits}/{len(results_df)} ({100*successful_fits/len(results_df):.1f}%)")
        print(f"Good quality fits (ΔAIC ≥ 2): {quality_fits}/{len(results_df)} ({100*quality_fits/len(results_df):.1f}%)")
        
        # Print parameter statistics for successful fits
        successful_results = results_df[results_df['convergence_successful']]
        if len(successful_results) > 0:
            print(f"\nParameter statistics for successful fits (n={len(successful_results)}):")
            print(f"Kappa (concentration):")
            print(f"  Mean: {successful_results['kappa_concentration'].mean():.3f}")
            print(f"  Median: {successful_results['kappa_concentration'].median():.3f}")
            print(f"  Range: [{successful_results['kappa_concentration'].min():.3f}, {successful_results['kappa_concentration'].max():.3f}]")
            
            print(f"Guess rate:")
            print(f"  Mean: {successful_results['guess_rate_proportion'].mean():.3f}")
            print(f"  Median: {successful_results['guess_rate_proportion'].median():.3f}")
            print(f"  Range: [{successful_results['guess_rate_proportion'].min():.3f}, {successful_results['guess_rate_proportion'].max():.3f}]")
            
            print(f"Bias (μ):")
            print(f"  Mean: {successful_results['mu_bias_radians'].mean():.3f}")
            print(f"  Median: {successful_results['mu_bias_radians'].median():.3f}")
            print(f"  Range: [{successful_results['mu_bias_radians'].min():.3f}, {successful_results['mu_bias_radians'].max():.3f}]")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'outputs/vwm_mixture_model_parameters_{timestamp}.csv'
        
        print(f"\nSaving results to: {output_filename}")
        results_df.to_csv(output_filename, index=False)
        print("Results saved successfully")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Unexpected error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
