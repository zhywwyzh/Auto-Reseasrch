import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

def von_mises_loglikelihood(params, data):
    """
    Calculate log-likelihood for von Mises distribution.
    
    Parameters:
    params (list): [mu, kappa] where mu is mean and kappa is concentration
    data (array): Angular data in radians
    
    Returns:
    float: Negative log-likelihood (for minimization)
    """
    mu, kappa = params
    if kappa <= 0:
        return np.inf
    
    # Von Mises log-likelihood
    loglik = np.sum(stats.vonmises.logpdf(data, kappa, loc=mu))
    return -loglik

def wrapped_normal_loglikelihood(params, data):
    """
    Calculate log-likelihood for wrapped normal distribution.
    
    Parameters:
    params (list): [mu, sigma] where mu is mean and sigma is standard deviation
    data (array): Angular data in radians
    
    Returns:
    float: Negative log-likelihood (for minimization)
    """
    mu, sigma = params
    if sigma <= 0:
        return np.inf
    
    # Vectorized calculation: sum PDFs across wraps before taking the log
    k = np.arange(-5, 6)
    wrapped_data = data[:, np.newaxis] + 2 * np.pi * k[np.newaxis, :]
    pdfs = stats.norm.pdf(wrapped_data, loc=mu, scale=sigma)
    summed_pdfs = np.sum(pdfs, axis=1)
    
    loglik = np.sum(np.log(summed_pdfs + 1e-10))  # Add epsilon to avoid log(0)
    return -loglik

def wrapped_cauchy_loglikelihood(params, data):
    """
    Calculate log-likelihood for wrapped Cauchy distribution.
    
    Parameters:
    params (list): [mu, rho] where mu is mean and rho is concentration (0 < rho < 1)
    data (array): Angular data in radians
    
    Returns:
    float: Negative log-likelihood (for minimization)
    """
    mu, rho = params
    if rho <= 0 or rho >= 1:
        return np.inf
    
    # Wrapped Cauchy log-likelihood
    # P(θ) = (1-ρ²)/(2π) * 1/(1 + ρ² - 2ρ*cos(θ-μ))
    cos_diff = np.cos(data - mu)
    denominator = 1 + rho**2 - 2*rho*cos_diff
    
    if np.any(denominator <= 0):
        return np.inf
    
    loglik = np.sum(np.log(1 - rho**2) - np.log(2*np.pi) - np.log(denominator))
    return -loglik

def fit_von_mises(data):
    """
    Fit von Mises distribution to circular data.
    
    Parameters:
    data (array): Angular data in radians
    
    Returns:
    dict: Dictionary containing fitted parameters, AIC, and log-likelihood
    """
    print(f"    Fitting von Mises distribution to {len(data)} data points")
    
    # Initial parameter estimates
    mu_init = stats.circmean(data)
    kappa_init = 1.0
    
    try:
        # Optimize parameters
        result = minimize(von_mises_loglikelihood, [mu_init, kappa_init], 
                         args=(data,), method='L-BFGS-B',
                         bounds=[(-np.pi, np.pi), (0.01, 100)])
        
        if result.success:
            mu_fit, kappa_fit = result.x
            loglik = -result.fun
            aic = 2 * 2 - 2 * loglik  # 2 parameters
            
            print(f"    Von Mises fit successful: μ={mu_fit:.4f}, κ={kappa_fit:.4f}, AIC={aic:.2f}")
            return {
                'mu': mu_fit,
                'kappa': kappa_fit,
                'loglikelihood': loglik,
                'aic': aic,
                'success': True
            }
        else:
            print("    Von Mises fit failed - optimization unsuccessful")
            return {'success': False}
    
    except Exception as e:
        print(f"    Von Mises fit failed with error: {e}")
        return {'success': False}

def fit_wrapped_normal(data):
    """
    Fit wrapped normal distribution to circular data.
    
    Parameters:
    data (array): Angular data in radians
    
    Returns:
    dict: Dictionary containing fitted parameters, AIC, and log-likelihood
    """
    print(f"    Fitting wrapped normal distribution to {len(data)} data points")
    
    # Initial parameter estimates
    mu_init = stats.circmean(data)
    sigma_init = 1.0
    
    try:
        # Optimize parameters
        result = minimize(wrapped_normal_loglikelihood, [mu_init, sigma_init], 
                         args=(data,), method='L-BFGS-B',
                         bounds=[(-np.pi, np.pi), (0.01, 5.0)])
        
        if result.success:
            mu_fit, sigma_fit = result.x
            loglik = -result.fun
            aic = 2 * 2 - 2 * loglik  # 2 parameters
            
            print(f"    Wrapped normal fit successful: μ={mu_fit:.4f}, σ={sigma_fit:.4f}, AIC={aic:.2f}")
            return {
                'mu': mu_fit,
                'sigma': sigma_fit,
                'loglikelihood': loglik,
                'aic': aic,
                'success': True
            }
        else:
            print("    Wrapped normal fit failed - optimization unsuccessful")
            return {'success': False}
    
    except Exception as e:
        print(f"    Wrapped normal fit failed with error: {e}")
        return {'success': False}

def fit_wrapped_cauchy(data):
    """
    Fit wrapped Cauchy distribution to circular data.
    
    Parameters:
    data (array): Angular data in radians
    
    Returns:
    dict: Dictionary containing fitted parameters, AIC, and log-likelihood
    """
    print(f"    Fitting wrapped Cauchy distribution to {len(data)} data points")
    
    # Initial parameter estimates
    mu_init = stats.circmean(data)
    rho_init = 0.5
    
    try:
        # Optimize parameters
        result = minimize(wrapped_cauchy_loglikelihood, [mu_init, rho_init], 
                         args=(data,), method='L-BFGS-B',
                         bounds=[(-np.pi, np.pi), (0.01, 0.99)])
        
        if result.success:
            mu_fit, rho_fit = result.x
            loglik = -result.fun
            aic = 2 * 2 - 2 * loglik  # 2 parameters
            
            print(f"    Wrapped Cauchy fit successful: μ={mu_fit:.4f}, ρ={rho_fit:.4f}, AIC={aic:.2f}")
            return {
                'mu': mu_fit,
                'rho': rho_fit,
                'loglikelihood': loglik,
                'aic': aic,
                'success': True
            }
        else:
            print("    Wrapped Cauchy fit failed - optimization unsuccessful")
            return {'success': False}
    
    except Exception as e:
        print(f"    Wrapped Cauchy fit failed with error: {e}")
        return {'success': False}

def find_most_recent_file(pattern):
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
    
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def main():
    """
    Main function to perform circular distribution comparison analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting circular distribution comparison analysis...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find the most recent input file
        input_pattern = "outputs/VWM_cleaned_trial_data_*.csv"
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Read the input data
        print("Reading input data...")
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully read {len(df)} rows from input file")
        except Exception as e:
            print(f"ERROR: Failed to read input file: {e}")
            return 1
        
        # Print column information
        print(f"Columns in dataset: {list(df.columns)}")
        print("First 3 rows of data:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'set_size', 'delay_seconds', 
                          'signed_error_degrees', 'trial_valid', 'trial_type']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns present")
        
        # Print unique values for key experimental design parameters
        print("\nExperimental design parameter values:")
        print(f"set_size unique values: {sorted(df['set_size'].unique())}")
        print(f"delay_seconds unique values: {sorted(df['delay_seconds'].unique())}")
        print(f"trial_valid unique values: {sorted(df['trial_valid'].unique())}")
        print(f"trial_type unique values: {sorted(df['trial_type'].unique())}")
        print(f"signed_error_degrees data type: {df['signed_error_degrees'].dtype}")
        print(f"participantId data type: {df['participantId'].dtype}")
        
        # Filter to expected VWM conditions only (set_size 2,4 with delay 1.0s,4.0s)
        print("\nFiltering to expected VWM experimental conditions...")
        initial_condition_count = len(df)
        expected_conditions = [(2.0, 1.0), (2.0, 4.0), (4.0, 1.0), (4.0, 4.0)]
        condition_mask = df[['set_size', 'delay_seconds']].apply(tuple, axis=1).isin(expected_conditions)
        df = df[condition_mask].copy()
        final_condition_count = len(df)
        
        print(f"Filtered from {initial_condition_count} to {final_condition_count} trials based on expected conditions")
        print(f"Excluded {initial_condition_count - final_condition_count} trials from unexpected conditions")
        
        # Filter to test trials only
        print("\nFiltering to valid test trials...")
        initial_count = len(df)
        df_filtered = df[(df['trial_valid'] == True) & (df['trial_type'] == 'test')].copy()
        final_count = len(df_filtered)
        
        print(f"Filtered from {initial_count} to {final_count} trials")
        print(f"Excluded {initial_count - final_count} trials")
        
        if final_count == 0:
            print("ERROR: No valid test trials found after filtering")
            return 1
        
        # Convert degrees to radians
        print("Converting signed error from degrees to radians...")
        df_filtered['error_radians'] = df_filtered['signed_error_degrees'] * (np.pi / 180)
        
        print(f"Error range in degrees: {df_filtered['signed_error_degrees'].min():.2f} to {df_filtered['signed_error_degrees'].max():.2f}")
        print(f"Error range in radians: {df_filtered['error_radians'].min():.4f} to {df_filtered['error_radians'].max():.4f}")
        
        # Get unique participants and conditions
        participants = df_filtered['participantId'].unique()
        conditions = df_filtered[['set_size', 'delay_seconds']].drop_duplicates()
        
        print(f"\nFound {len(participants)} participants")
        print(f"Found {len(conditions)} conditions:")
        for _, row in conditions.iterrows():
            print(f"  Set size {row['set_size']}, delay {row['delay_seconds']}s")
        
        # Initialize results list
        results = []
        
        # Fit distributions for each participant and condition
        print("\nFitting circular distributions...")
        total_combinations = len(participants) * len(conditions)
        current_combination = 0
        
        for participant in participants:
            print(f"\nProcessing participant: {participant}")
            
            for _, condition in conditions.iterrows():
                current_combination += 1
                set_size = condition['set_size']
                delay_seconds = condition['delay_seconds']
                
                print(f"  Condition {current_combination}/{total_combinations}: set_size={set_size}, delay={delay_seconds}s")
                
                # Get data for this participant and condition
                mask = ((df_filtered['participantId'] == participant) & 
                       (df_filtered['set_size'] == set_size) & 
                       (df_filtered['delay_seconds'] == delay_seconds))
                
                condition_data = df_filtered[mask]['error_radians'].values
                trial_count = len(condition_data)
                
                print(f"    Found {trial_count} trials for this condition")
                
                if trial_count < 5:  # Need minimum trials for fitting
                    print(f"    Skipping - insufficient trials (need at least 5)")
                    continue
                
                # Initialize result row
                result_row = {
                    'participantId': participant,
                    'set_size': int(set_size),
                    'delay_seconds': float(delay_seconds),
                    'trial_count': trial_count
                }
                
                # Fit von Mises distribution
                vm_result = fit_von_mises(condition_data)
                if vm_result['success']:
                    result_row['von_mises_aic'] = vm_result['aic']
                    result_row['von_mises_kappa'] = vm_result['kappa']
                    result_row['von_mises_mu'] = vm_result['mu']
                else:
                    result_row['von_mises_aic'] = np.nan
                    result_row['von_mises_kappa'] = np.nan
                    result_row['von_mises_mu'] = np.nan
                
                # Fit wrapped normal distribution
                wn_result = fit_wrapped_normal(condition_data)
                if wn_result['success']:
                    result_row['wrapped_normal_aic'] = wn_result['aic']
                    result_row['wrapped_normal_sigma'] = wn_result['sigma']
                    result_row['wrapped_normal_mu'] = wn_result['mu']
                else:
                    result_row['wrapped_normal_aic'] = np.nan
                    result_row['wrapped_normal_sigma'] = np.nan
                    result_row['wrapped_normal_mu'] = np.nan
                
                # Fit wrapped Cauchy distribution
                wc_result = fit_wrapped_cauchy(condition_data)
                if wc_result['success']:
                    result_row['wrapped_cauchy_aic'] = wc_result['aic']
                    result_row['wrapped_cauchy_rho'] = wc_result['rho']
                    result_row['wrapped_cauchy_mu'] = wc_result['mu']
                else:
                    result_row['wrapped_cauchy_aic'] = np.nan
                    result_row['wrapped_cauchy_rho'] = np.nan
                    result_row['wrapped_cauchy_mu'] = np.nan
                
                # Determine best fitting distribution
                aic_values = {
                    'von_mises': result_row['von_mises_aic'],
                    'wrapped_normal': result_row['wrapped_normal_aic'],
                    'wrapped_cauchy': result_row['wrapped_cauchy_aic']
                }
                
                # Remove NaN values
                valid_aic = {k: v for k, v in aic_values.items() if not np.isnan(v)}
                
                if valid_aic:
                    best_distribution = min(valid_aic, key=valid_aic.get)
                    best_aic = valid_aic[best_distribution]
                    
                    result_row['best_fitting_distribution'] = best_distribution
                    
                    # Calculate delta AIC values
                    result_row['von_mises_delta_aic'] = result_row['von_mises_aic'] - best_aic if not np.isnan(result_row['von_mises_aic']) else np.nan
                    result_row['wrapped_normal_delta_aic'] = result_row['wrapped_normal_aic'] - best_aic if not np.isnan(result_row['wrapped_normal_aic']) else np.nan
                    result_row['wrapped_cauchy_delta_aic'] = result_row['wrapped_cauchy_aic'] - best_aic if not np.isnan(result_row['wrapped_cauchy_aic']) else np.nan
                    
                    # Correctly determine if an alternative is substantially better than von Mises
                    vm_aic = result_row.get('von_mises_aic', np.nan)
                    wn_aic = result_row.get('wrapped_normal_aic', np.nan)
                    wc_aic = result_row.get('wrapped_cauchy_aic', np.nan)

                    wn_is_better = (not np.isnan(vm_aic) and not np.isnan(wn_aic)) and (vm_aic - wn_aic > 4)
                    wc_is_better = (not np.isnan(vm_aic) and not np.isnan(wc_aic)) and (vm_aic - wc_aic > 4)
                    result_row['alternative_substantially_better'] = wn_is_better or wc_is_better

                    print(f"    Best fitting distribution: {best_distribution} (AIC={best_aic:.2f})")
                    if result_row['alternative_substantially_better']:
                        print(f"    Alternative distribution substantially better than von Mises (ΔAIC > 4)")
                
                else:
                    print("    No valid fits obtained for any distribution")
                    result_row['best_fitting_distribution'] = 'none'
                    result_row['von_mises_delta_aic'] = np.nan
                    result_row['wrapped_normal_delta_aic'] = np.nan
                    result_row['wrapped_cauchy_delta_aic'] = np.nan
                    result_row['alternative_substantially_better'] = False
                
                results.append(result_row)
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        print(f"\nCompleted fitting for {len(results_df)} participant-condition combinations")
        
        # Print results summary
        print("\nResults summary:")
        print("Columns:", list(results_df.columns))
        print("First 2 rows:")
        print(results_df.head(2))
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        detailed_output_file = f"outputs/circular_distribution_comparison_{timestamp}.csv"
        results_df.to_csv(detailed_output_file, index=False)
        print(f"Saved detailed results to: {detailed_output_file}")
        
        # Calculate summary statistics
        print("\nCalculating summary statistics...")
        
        # Filter out cases with no valid fits
        valid_results = results_df[results_df['best_fitting_distribution'] != 'none'].copy()
        print(f"Valid results: {len(valid_results)} out of {len(results_df)}")
        
        if len(valid_results) == 0:
            print("ERROR: No valid distribution fits found")
            return 1
        
        # Count best fits by distribution
        distribution_counts = valid_results['best_fitting_distribution'].value_counts()
        print(f"Distribution fit counts: {dict(distribution_counts)}")
        
        # Calculate summary statistics for each distribution
        summary_data = []
        
        for dist_type in ['von_mises', 'wrapped_normal', 'wrapped_cauchy']:
            aic_col = f'{dist_type}_aic'
            
            # Count best fits
            count_best = distribution_counts.get(dist_type, 0)
            percentage_best = (count_best / len(valid_results)) * 100
            
            # Calculate AIC statistics
            valid_aic = valid_results[aic_col].dropna()
            mean_aic = valid_aic.mean() if len(valid_aic) > 0 else np.nan
            sd_aic = valid_aic.std() if len(valid_aic) > 0 else np.nan
            
            # Correctly count substantially better cases (ΔAIC > 4)
            if dist_type == 'von_mises':
                # For von Mises, count cases where it was substantially WORSE than an alternative
                count_substantially_better = valid_results['alternative_substantially_better'].sum()
            else:
                # For alternatives, count cases where they were substantially BETTER than von Mises
                substantially_better_mask = (valid_results['von_mises_aic'] - valid_results[aic_col]) > 4
                count_substantially_better = substantially_better_mask.sum()
            
            percentage_substantially_better = (count_substantially_better / len(valid_results)) * 100
            
            # Validation conclusion
            if percentage_best > 50:
                validation_conclusion = "Best fitting distribution"
            elif percentage_best > 25:
                validation_conclusion = "Competitive alternative"
            elif percentage_substantially_better > 10:
                validation_conclusion = "Occasional substantial improvement"
            else:
                validation_conclusion = "Poor fit overall"
            
            summary_row = {
                'distribution_type': dist_type,
                'count_best_fit': int(count_best),
                'percentage_best_fit': round(percentage_best, 2),
                'mean_aic': round(mean_aic, 2) if not np.isnan(mean_aic) else np.nan,
                'sd_aic': round(sd_aic, 2) if not np.isnan(sd_aic) else np.nan,
                'count_substantially_better': int(count_substantially_better),
                'percentage_substantially_better': round(percentage_substantially_better, 2),
                'validation_conclusion': validation_conclusion
            }
            
            summary_data.append(summary_row)
            
            print(f"\n{dist_type} summary:")
            print(f"  Best fit: {count_best} cases ({percentage_best:.1f}%)")
            print(f"  Mean AIC: {mean_aic:.2f}" if not np.isnan(mean_aic) else "  Mean AIC: N/A")
            print(f"  Substantially better: {count_substantially_better} cases ({percentage_substantially_better:.1f}%)")
            print(f"  Conclusion: {validation_conclusion}")
        
        # Create summary DataFrame
        summary_df = pd.DataFrame(summary_data)
        
        print("\nSummary DataFrame:")
        print("Columns:", list(summary_df.columns))
        print("All rows:")
        print(summary_df)
        
        # Save summary results
        summary_output_file = f"outputs/distribution_validation_summary_{timestamp}.csv"
        summary_df.to_csv(summary_output_file, index=False)
        print(f"Saved summary results to: {summary_output_file}")
        
        # Final validation assessment
        von_mises_percentage = summary_df[summary_df['distribution_type'] == 'von_mises']['percentage_best_fit'].iloc[0]
        alternative_substantially_better_count = valid_results['alternative_substantially_better'].sum()
        alternative_substantially_better_percentage = (alternative_substantially_better_count / len(valid_results)) * 100
        
        print(f"\nFinal validation assessment:")
        print(f"Von Mises best fit in {von_mises_percentage:.1f}% of cases")
        print(f"Alternative distributions substantially better in {alternative_substantially_better_count} cases ({alternative_substantially_better_percentage:.1f}%)")
        
        if von_mises_percentage > 70:
            print("CONCLUSION: Von Mises assumption is well-supported")
        elif von_mises_percentage > 50:
            print("CONCLUSION: Von Mises assumption is moderately supported")
        elif alternative_substantially_better_percentage > 20:
            print("CONCLUSION: Von Mises assumption should be questioned - alternative distributions frequently provide better fits")
        else:
            print("CONCLUSION: Mixed evidence for von Mises assumption - consider model comparison in analyses")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
