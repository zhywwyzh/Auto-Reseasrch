import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
from scipy.optimize import minimize
from scipy.special import i0e
from scipy.stats import circmean, circstd
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
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def von_mises_neg_log_likelihood(params, errors):
    """
    Calculate negative log-likelihood for von Mises distribution.
    
    Parameters:
    params (list): [mu, kappa] parameters for von Mises distribution
    errors (array): Error data in radians
    
    Returns:
    float: Negative log-likelihood value
    """
    mu, kappa = params
    if kappa <= 0:
        return np.inf

    try:
        n = len(errors)
        # log(pdf) = k*cos(x-u) - log(2*pi*i0(k))
        # With i0e(k) = i0(k)*exp(-k) => log(i0(k)) = log(i0e(k)) + k
        # log_likelihood = sum(k*cos(x-u)) - n*(log(2*pi) + log(i0e(k)) + k)
        log_likelihood = np.sum(kappa * np.cos(errors - mu)) - n * (kappa + np.log(2 * np.pi) + np.log(i0e(kappa)))
        return -log_likelihood
    except (ValueError, OverflowError):
        return np.inf

def fit_von_mises(errors):
    """
    Fit von Mises distribution to circular error data using maximum likelihood estimation.
    
    Parameters:
    errors (array): Error data in radians
    
    Returns:
    tuple: (mu, kappa) parameters, or (None, None) if fitting fails
    """
    if len(errors) < 5:
        return None, None
    
    # Initial parameter estimates
    # Use circular mean for mu
    mu_init = np.arctan2(np.mean(np.sin(errors)), np.mean(np.cos(errors)))
    
    # Initial kappa estimate using method of moments
    R = np.sqrt(np.mean(np.cos(errors))**2 + np.mean(np.sin(errors))**2)
    if R < 0.53:
        kappa_init = 2*R + R**3 + 5*R**5/6
    elif R < 0.85:
        kappa_init = -0.4 + 1.39*R + 0.43/(1-R)
    else:
        kappa_init = 1/(R**3 - 4*R**2 + 3*R)
    
    kappa_init = max(0.1, min(kappa_init, 10))  # Bound initial estimate
    
    try:
        # Optimize parameters
        result = minimize(von_mises_neg_log_likelihood, 
                         [mu_init, kappa_init], 
                         args=(errors,),
                         method='L-BFGS-B',
                         bounds=[(-np.pi, np.pi), (0.001, 100)])
        
        if result.success:
            return result.x[0], result.x[1]
        else:
            return None, None
    except:
        return None, None

def bootstrap_von_mises(errors, n_bootstrap=1000):
    """
    Perform bootstrap analysis of von Mises parameter estimation.
    
    Parameters:
    errors (array): Error data in radians
    n_bootstrap (int): Number of bootstrap samples
    
    Returns:
    dict: Bootstrap statistics including mean, CI, and CV for kappa
    """
    if len(errors) < 20:
        return {
            'bootstrap_kappa_mean': np.nan,
            'bootstrap_kappa_ci_lower': np.nan,
            'bootstrap_kappa_ci_upper': np.nan,
            'bootstrap_kappa_cv': np.nan
        }
    
    kappa_bootstrap = []
    
    for i in range(n_bootstrap):
        # Bootstrap sample
        boot_errors = np.random.choice(errors, size=len(errors), replace=True)
        mu_boot, kappa_boot = fit_von_mises(boot_errors)
        
        if kappa_boot is not None and not np.isnan(kappa_boot):
            kappa_bootstrap.append(kappa_boot)
    
    if len(kappa_bootstrap) < 100:  # Need sufficient successful fits
        return {
            'bootstrap_kappa_mean': np.nan,
            'bootstrap_kappa_ci_lower': np.nan,
            'bootstrap_kappa_ci_upper': np.nan,
            'bootstrap_kappa_cv': np.nan
        }
    
    kappa_bootstrap = np.array(kappa_bootstrap)
    
    return {
        'bootstrap_kappa_mean': np.mean(kappa_bootstrap),
        'bootstrap_kappa_ci_lower': np.percentile(kappa_bootstrap, 2.5),
        'bootstrap_kappa_ci_upper': np.percentile(kappa_bootstrap, 97.5),
        'bootstrap_kappa_cv': np.std(kappa_bootstrap) / np.mean(kappa_bootstrap)
    }

def main():
    """
    Main function to process VWM data and extract von Mises parameters.
    """
    try:
        print("Starting VWM von Mises parameter extraction...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find input file
        input_pattern = 'outputs/VWM_cleaned_trial_data_*.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"Error: No input file found matching pattern {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read input data
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded data with shape: {df.shape}")
        except Exception as e:
            print(f"Error reading input file: {e}")
            return 1
        
        # Print all columns
        print("All columns in dataset:")
        print(df.columns.tolist())
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Check required columns
        required_columns = ['participantId', 'set_size', 'delay_seconds', 'signed_error_degrees', 'trial_valid', 'trial_type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns present")
        
        # Print unique values for experimental design parameters
        print(f"\nUnique values in set_size: {sorted(df['set_size'].unique())}")
        print(f"Unique values in delay_seconds: {sorted(df['delay_seconds'].unique())}")
        print(f"Unique values in trial_valid: {sorted(df['trial_valid'].unique())}")
        print(f"Unique values in trial_type: {sorted(df['trial_type'].unique())}")
        print(f"Type of signed_error_degrees: {df['signed_error_degrees'].dtype}")
        
        # Filter to test trials only
        print(f"\nOriginal data shape: {df.shape}")
        df_filtered = df[(df['trial_valid'] == True) & (df['trial_type'] == 'test')].copy()
        print(f"After filtering to valid test trials: {df_filtered.shape}")
        
        if df_filtered.empty:
            print("Error: No valid test trials found after filtering")
            return 1
        
        # Convert signed errors to radians
        df_filtered['error_radians'] = df_filtered['signed_error_degrees'] * (np.pi / 180)
        print("Converted signed errors to radians")
        
        # Remove rows with NaN errors
        df_filtered = df_filtered.dropna(subset=['error_radians'])
        print(f"After removing NaN errors: {df_filtered.shape}")
        
        # Use specified experimental conditions as per instructions
        valid_conditions = [(2, 1.0), (2, 4.0), (4, 1.0), (4, 4.0)]
        print(f"\nProcessing specified experimental conditions: {valid_conditions}")

        # Check if these conditions exist in the data
        print("\nChecking condition availability in data:")
        for set_size, delay in valid_conditions:
            count = len(df_filtered[(df_filtered['set_size'] == set_size) & (df_filtered['delay_seconds'] == delay)])
            print(f"SetSize{set_size}_Delay{delay}s: {count} trials")

        # Initialize results list
        results = []
        
        # Get unique participants
        participants = df_filtered['participantId'].unique()
        print(f"\nProcessing {len(participants)} participants...")
        print(f"Will process {len(valid_conditions)} conditions per participant: {valid_conditions}")
        
        # Process each participant and condition
        for i, participant in enumerate(participants):
            if i % 10 == 0:
                print(f"Processing participant {i+1}/{len(participants)}: {participant}")

            participant_data = df_filtered[df_filtered['participantId'] == participant]

            # Process each specified condition combination
            for set_size in [2, 4]:
                for delay in [1.0, 4.0]:
                    condition_data = participant_data[
                        (participant_data['set_size'] == set_size) &
                        (participant_data['delay_seconds'] == delay)
                    ]

                    trial_count = len(condition_data)
                    errors = condition_data['error_radians'].values

                    # Initialize result row
                    result_row = {
                        'participantId': participant,
                        'set_size': set_size,
                        'delay_seconds': delay,
                        'trial_count': trial_count,
                        'parameter_estimation_reliable': False,
                        'insufficient_trials': trial_count < 15
                    }

                    if trial_count >= 15:
                        # Fit von Mises distribution
                        mu, kappa = fit_von_mises(errors)

                        if mu is not None and kappa is not None:
                            result_row.update({
                                'kappa_concentration': kappa,
                                'mu_bias_radians': mu,
                                'mu_bias_degrees': mu * (180 / np.pi),
                                'kappa_log_transformed': np.log(kappa),
                                'parameter_estimation_reliable': True
                            })

                            # Bootstrap analysis
                            bootstrap_stats = bootstrap_von_mises(errors)
                            result_row.update(bootstrap_stats)
                        else:
                            # Fitting failed
                            result_row.update({
                                'kappa_concentration': np.nan,
                                'mu_bias_radians': np.nan,
                                'mu_bias_degrees': np.nan,
                                'kappa_log_transformed': np.nan,
                                'bootstrap_kappa_mean': np.nan,
                                'bootstrap_kappa_ci_lower': np.nan,
                                'bootstrap_kappa_ci_upper': np.nan,
                                'bootstrap_kappa_cv': np.nan
                            })
                    else:
                        # Insufficient trials
                        result_row.update({
                            'kappa_concentration': np.nan,
                            'mu_bias_radians': np.nan,
                            'mu_bias_degrees': np.nan,
                            'kappa_log_transformed': np.nan,
                            'bootstrap_kappa_mean': np.nan,
                            'bootstrap_kappa_ci_lower': np.nan,
                            'bootstrap_kappa_ci_upper': np.nan,
                            'bootstrap_kappa_cv': np.nan
                        })

                    results.append(result_row)
        
        # Create results dataframe
        results_df = pd.DataFrame(results)
        print(f"\nCreated results dataframe with shape: {results_df.shape}")
        
        # Print first 2 rows of results
        print("First 2 rows of results:")
        print(results_df.head(2))
        
        # Calculate summary statistics
        print("\nCalculating summary statistics...")
        
        # Filter to reliable estimates only
        reliable_data = results_df[results_df['parameter_estimation_reliable'] == True].copy()
        print(f"Number of reliable parameter estimates: {len(reliable_data)}")
        
        if len(reliable_data) == 0:
            print("Warning: No reliable parameter estimates found")
        
        # Create summary statistics
        summary_results = []
        
        if len(reliable_data) > 0:
            # Check skewness of kappa distribution
            kappa_values = reliable_data['kappa_concentration'].dropna()
            if len(kappa_values) > 0:
                kappa_skewness = stats.skew(kappa_values)
                print(f"Kappa distribution skewness: {kappa_skewness:.3f}")
                
                if kappa_skewness > 2:
                    print("Kappa distribution is highly skewed - log transformation was applied")
            
            # Summary by condition
            for set_size in [2, 4]:
                for delay in [1.0, 4.0]:
                    condition = f"SetSize{int(set_size)}_Delay{delay}s"
                    condition_data = reliable_data[
                        (reliable_data['set_size'] == set_size) &
                        (reliable_data['delay_seconds'] == delay)
                    ]

                    if len(condition_data) > 0:
                        # Kappa concentration parameter
                        kappa_vals = condition_data['kappa_concentration'].dropna()
                        if len(kappa_vals) > 0:
                            summary_results.append({
                                'condition': condition,
                                'parameter': 'kappa_concentration',
                                'mean_value': np.mean(kappa_vals),
                                'sd_value': np.std(kappa_vals),
                                'min_value': np.min(kappa_vals),
                                'max_value': np.max(kappa_vals),
                                'n_participants': len(kappa_vals),
                                'skewness': stats.skew(kappa_vals),
                                'kurtosis': stats.kurtosis(kappa_vals)
                            })

                        # Mu bias parameter
                        mu_vals = condition_data['mu_bias_radians'].dropna()
                        if len(mu_vals) > 0:
                            summary_results.append({
                                'condition': condition,
                                'parameter': 'mu_bias_radians',
                                'mean_value': circmean(mu_vals),
                                'sd_value': circstd(mu_vals),
                                'min_value': np.min(mu_vals),
                                'max_value': np.max(mu_vals),
                                'n_participants': len(mu_vals),
                                'skewness': stats.skew(mu_vals),  # Fixed: use stats.skew instead of circskew
                                'kurtosis': stats.kurtosis(mu_vals)
                            })

                        # Log-transformed kappa
                        kappa_log_vals = condition_data['kappa_log_transformed'].dropna()
                        if len(kappa_log_vals) > 0:
                            summary_results.append({
                                'condition': condition,
                                'parameter': 'kappa_log_transformed',
                                'mean_value': np.mean(kappa_log_vals),
                                'sd_value': np.std(kappa_log_vals),
                                'min_value': np.min(kappa_log_vals),
                                'max_value': np.max(kappa_log_vals),
                                'n_participants': len(kappa_log_vals),
                                'skewness': stats.skew(kappa_log_vals),
                                'kurtosis': stats.kurtosis(kappa_log_vals)
                            })
        
        summary_df = pd.DataFrame(summary_results)
        print(f"Created summary dataframe with shape: {summary_df.shape}")
        
        # Print summary statistics
        if len(summary_df) > 0:
            print("\nSummary statistics:")
            print(summary_df)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main results
        output_file1 = f'outputs/VWM_von_mises_parameters_{timestamp}.csv'
        results_df.to_csv(output_file1, index=False)
        print(f"\nSaved von Mises parameters to: {output_file1}")
        
        # Save summary statistics
        output_file2 = f'outputs/von_mises_parameter_summary_{timestamp}.csv'
        summary_df.to_csv(output_file2, index=False)
        print(f"Saved parameter summary to: {output_file2}")
        
        # Print final statistics
        total_participants = len(results_df['participantId'].unique())
        reliable_participants = len(reliable_data['participantId'].unique()) if len(reliable_data) > 0 else 0
        insufficient_trials_count = results_df['insufficient_trials'].sum()
        
        print(f"\nFinal Statistics:")
        print(f"Total participants processed: {total_participants}")
        print(f"Participants with reliable estimates: {reliable_participants}")
        print(f"Conditions with insufficient trials: {insufficient_trials_count}")
        print(f"Total parameter estimates: {len(results_df)}")
        print(f"Reliable parameter estimates: {len(reliable_data)}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
