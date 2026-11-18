import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy.optimize import minimize
from scipy.special import i0
import warnings
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match, with <TIMESTAMP> placeholder
        
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard pattern
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    
    # Find all matching files
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        return None
    
    # Get the most recent file based on modification time
    latest_file = max(matching_files, key=os.path.getmtime)
    return latest_file

def von_mises_pdf(theta, mu, kappa):
    """
    Calculate probability density function for von Mises distribution.
    
    Parameters:
    -----------
    theta : array-like
        Angle values in radians
    mu : float
        Mean direction parameter
    kappa : float
        Concentration parameter
        
    Returns:
    --------
    array-like
        PDF values
    """
    return np.exp(kappa * np.cos(theta - mu)) / (2 * np.pi * i0(kappa))


def mixture_pdf(theta, mu, kappa, p):
    """
    Calculate probability density function for von Mises-uniform mixture.
    
    Parameters:
    -----------
    theta : array-like
        Angle values in radians
    mu : float
        Mean direction of von Mises component
    kappa : float
        Concentration of von Mises component
    p : float
        Mixing proportion for von Mises component
        
    Returns:
    --------
    array-like
        Mixture PDF values
    """
    vm_pdf = von_mises_pdf(theta, mu, kappa)
    # The uniform component is defined over [-π/2, π/2], a range of width π.
    # The corresponding probability density is 1/π.
    uniform_density = 1 / np.pi
    return p * vm_pdf + (1 - p) * uniform_density

def negative_log_likelihood(params, theta):
    """
    Calculate negative log-likelihood for von Mises-uniform mixture model.
    
    Parameters:
    -----------
    params : array-like
        Parameters [mu, kappa, p]
    theta : array-like
        Observed angle data in radians
        
    Returns:
    --------
    float
        Negative log-likelihood value
    """
    mu, kappa, p = params
    
    # Ensure parameters are within bounds
    if kappa <= 0 or p <= 0 or p >= 1:
        return np.inf
    
    pdf_vals = mixture_pdf(theta, mu, kappa, p)
    
    # Avoid log(0) by adding small epsilon
    pdf_vals = np.maximum(pdf_vals, 1e-10)
    
    return -np.sum(np.log(pdf_vals))

def fit_von_mises_mixture(theta_data, n_starts=10):
    """
    Fit von Mises-uniform mixture model using maximum likelihood estimation.
    
    Parameters:
    -----------
    theta_data : array-like
        Error data in radians
    n_starts : int
        Number of random starting points for optimization
        
    Returns:
    --------
    dict
        Dictionary containing fitted parameters and fit statistics
    """
    print(f"  Fitting mixture model with {len(theta_data)} data points")
    
    best_result = None
    best_nll = np.inf
    
    # Parameter bounds
    bounds = [(-np.pi/2, np.pi/2),  # mu (bias)
              (0.1, 100),           # kappa (concentration)
              (0.01, 0.99)]         # p (mixing proportion)
    
    for start in range(n_starts):
        # Random initial values
        mu_init = np.random.uniform(-np.pi/4, np.pi/4)
        kappa_init = np.random.uniform(1, 10)
        p_init = np.random.uniform(0.3, 0.9)
        
        initial_params = [mu_init, kappa_init, p_init]
        
        try:
            result = minimize(negative_log_likelihood, 
                            initial_params,
                            args=(theta_data,),
                            bounds=bounds,
                            method='L-BFGS-B')
            
            if result.fun < best_nll:
                best_nll = result.fun
                best_result = result
                
        except Exception as e:
            print(f"    Optimization start {start+1} failed: {e}")
            continue
    
    if best_result is None:
        print("  All optimization attempts failed")
        return {
            'mu': np.nan,
            'kappa': np.nan,
            'p': np.nan,
            'neg_log_likelihood': np.nan,
            'convergence_success': False
        }
    
    mu_opt, kappa_opt, p_opt = best_result.x
    
    print(f"  Best fit: mu={mu_opt:.4f}, kappa={kappa_opt:.4f}, p={p_opt:.4f}")
    print(f"  Negative log-likelihood: {best_nll:.4f}")
    print(f"  Convergence success: {best_result.success}")
    
    return {
        'mu': mu_opt,
        'kappa': kappa_opt,
        'p': p_opt,
        'neg_log_likelihood': best_nll,
        'convergence_success': best_result.success
    }

def main():
    """
    Main function to process VWM data and fit von Mises mixture models.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting VWM parameter estimation script")
        print("=" * 50)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input file
        input_pattern = 'outputs/trial_level_cleaned_data_<TIMESTAMP>.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input file found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read input data
        print("\nReading input data...")
        try:
            df = pd.read_csv(input_file)
            print(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
        except Exception as e:
            print(f"ERROR: Failed to read input file: {e}")
            return 1
        
        # Print column information
        print("\nInput file columns:")
        print(df.columns.tolist())
        
        print("\nFirst 3 rows of input data:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'isPractice', 'trial_excluded_VWM', 
                          'VWM_error_normalized', 'VWM_trial']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("\nAll required columns found")
        
        # Print unique values for key columns
        print("\nUnique values in key columns:")
        print(f"isPractice: {sorted(df['isPractice'].dropna().unique())}")
        print(f"trial_excluded_VWM: {sorted(df['trial_excluded_VWM'].dropna().unique())}")
        print(f"VWM_error_normalized type: {df['VWM_error_normalized'].dtype}")
        print(f"VWM_trial type: {df['VWM_trial'].dtype}")
        
        # Filter data
        print("\nFiltering data...")
        print(f"Initial data shape: {df.shape}")
        
        # Filter to test trials only
        test_trials = df[df['isPractice'] == False].copy()
        print(f"After filtering to test trials (isPractice == False): {test_trials.shape}")
        
        # Exclude flagged trials
        valid_trials = test_trials[test_trials['trial_excluded_VWM'] == False].copy()
        print(f"After excluding flagged trials (trial_excluded_VWM == False): {valid_trials.shape}")
        
        # Remove rows with missing VWM_error_normalized
        valid_trials = valid_trials.dropna(subset=['VWM_error_normalized']).copy()
        print(f"After removing missing VWM_error_normalized: {valid_trials.shape}")
        
        # Convert error from degrees to radians
        print("\nConverting VWM_error_normalized from degrees to radians...")
        valid_trials['error_radians'] = valid_trials['VWM_error_normalized'] * (np.pi / 180)
        
        print(f"Error range in degrees: [{valid_trials['VWM_error_normalized'].min():.2f}, {valid_trials['VWM_error_normalized'].max():.2f}]")
        print(f"Error range in radians: [{valid_trials['error_radians'].min():.4f}, {valid_trials['error_radians'].max():.4f}]")
        
        # Group by participant
        print("\nGrouping data by participant...")
        participant_groups = valid_trials.groupby('participantId')
        print(f"Found {len(participant_groups)} unique participants")
        
        # Initialize output lists
        results_list = []
        log_list = []
        
        print("\nProcessing participants...")
        
        for i, (participant_id, participant_data) in enumerate(participant_groups):
            print(f"\nProcessing participant {i+1}/{len(participant_groups)}: {participant_id}")
            
            # Count trials for logging, focusing only on VWM trials
            participant_df_full = df[df['participantId'] == participant_id]
            initial_count = participant_df_full['VWM_trial'].notna().sum()
            final_count = len(participant_data)
            excluded_count = initial_count - final_count

            print(f"  Initial trials: {initial_count}")
            print(f"  Excluded trials: {excluded_count}")
            print(f"  Valid trials: {final_count}")

            # Log entry
            log_entry = {
                'participantId': participant_id,
                'initial_trial_count': initial_count,
                'excluded_trials_count': excluded_count,
                'final_valid_trials': final_count,
                'model_fit_attempted': False,
                'convergence_status': 'insufficient_trials'
            }
            
            # Check minimum trial requirement
            if final_count < 10:
                print(f"  Skipping participant {participant_id}: insufficient trials ({final_count} < 10)")
                
                results_list.append({
                    'participantId': participant_id,
                    'concentration_kappa': np.nan,
                    'bias_mu_degrees': np.nan,
                    'guess_rate': np.nan,
                    'neg_log_likelihood': np.nan,
                    'n_valid_trials': final_count,
                    'convergence_success': False,
                    'excluded_insufficient_trials': True
                })
                
                log_list.append(log_entry)
                continue
            
            # Fit mixture model
            print(f"  Fitting von Mises mixture model...")
            
            log_entry['model_fit_attempted'] = True
            
            try:
                theta_data = participant_data['error_radians'].values
                fit_result = fit_von_mises_mixture(theta_data)
                
                # Convert bias back to degrees
                bias_degrees = fit_result['mu'] * (180 / np.pi) if not np.isnan(fit_result['mu']) else np.nan
                guess_rate = 1 - fit_result['p'] if not np.isnan(fit_result['p']) else np.nan
                
                results_list.append({
                    'participantId': participant_id,
                    'concentration_kappa': fit_result['kappa'],
                    'bias_mu_degrees': bias_degrees,
                    'guess_rate': guess_rate,
                    'neg_log_likelihood': fit_result['neg_log_likelihood'],
                    'n_valid_trials': final_count,
                    'convergence_success': fit_result['convergence_success'],
                    'excluded_insufficient_trials': False
                })
                
                log_entry['convergence_status'] = 'success' if fit_result['convergence_success'] else 'failed'
                
            except Exception as e:
                print(f"  ERROR fitting model for participant {participant_id}: {e}")
                
                results_list.append({
                    'participantId': participant_id,
                    'concentration_kappa': np.nan,
                    'bias_mu_degrees': np.nan,
                    'guess_rate': np.nan,
                    'neg_log_likelihood': np.nan,
                    'n_valid_trials': final_count,
                    'convergence_success': False,
                    'excluded_insufficient_trials': False
                })
                
                log_entry['convergence_status'] = 'error'
            
            log_list.append(log_entry)
        
        # Create output dataframes
        print("\nCreating output dataframes...")
        
        results_df = pd.DataFrame(results_list)
        log_df = pd.DataFrame(log_list)
        
        print(f"Results dataframe shape: {results_df.shape}")
        print("Results dataframe columns:")
        print(results_df.columns.tolist())
        print("First 2 rows of results:")
        print(results_df.head(2))
        
        print(f"\nLog dataframe shape: {log_df.shape}")
        print("Log dataframe columns:")
        print(log_df.columns.tolist())
        print("First 2 rows of log:")
        print(log_df.head(2))
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save output files
        results_filename = f'outputs/VWM_parameter_estimates_{timestamp}.csv'
        log_filename = f'outputs/VWM_modeling_log_{timestamp}.csv'
        
        print(f"\nSaving results to: {results_filename}")
        results_df.to_csv(results_filename, index=False)
        
        print(f"Saving log to: {log_filename}")
        log_df.to_csv(log_filename, index=False)
        
        # Summary statistics
        print("\n" + "="*50)
        print("SUMMARY STATISTICS")
        print("="*50)
        
        total_participants = len(results_df)
        excluded_insufficient = results_df['excluded_insufficient_trials'].sum()
        successful_fits = results_df['convergence_success'].sum()
        
        print(f"Total participants: {total_participants}")
        print(f"Excluded (insufficient trials): {excluded_insufficient}")
        print(f"Successful model fits: {successful_fits}")
        print(f"Failed model fits: {total_participants - excluded_insufficient - successful_fits}")
        
        if successful_fits > 0:
            valid_results = results_df[results_df['convergence_success'] == True]
            print(f"\nParameter estimates for successful fits (n={len(valid_results)}):")
            print(f"Concentration (kappa): mean={valid_results['concentration_kappa'].mean():.3f}, std={valid_results['concentration_kappa'].std():.3f}")
            print(f"Bias (degrees): mean={valid_results['bias_mu_degrees'].mean():.3f}, std={valid_results['bias_mu_degrees'].std():.3f}")
            print(f"Guess rate: mean={valid_results['guess_rate'].mean():.3f}, std={valid_results['guess_rate'].std():.3f}")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
