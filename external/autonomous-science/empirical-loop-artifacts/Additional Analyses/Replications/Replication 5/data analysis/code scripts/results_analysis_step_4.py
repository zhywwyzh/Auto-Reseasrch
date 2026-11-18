import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

try:
    from rpy2.robjects.packages import importr
    import rpy2.robjects as ro
    from rpy2.rinterface_lib.embedded import RRuntimeError
    RPY2_AVAILABLE = True
except ImportError:
    print("Warning: rpy2 not available, falling back to scipy")
    RPY2_AVAILABLE = False

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

def convert_degrees_to_radians(degrees):
    """
    Convert degrees to radians for circular data analysis.
    
    Parameters:
    degrees (array-like): Angle values in degrees
    
    Returns:
    numpy.ndarray: Angle values in radians
    """
    return np.array(degrees) * np.pi / 180

def wrap_to_pi(angles):
    """
    Wrap angles to [-π, π] range.
    
    Parameters:
    angles (array-like): Angle values in radians
    
    Returns:
    numpy.ndarray: Wrapped angle values
    """
    return np.arctan2(np.sin(angles), np.cos(angles))


def fit_mixture_model_r(data, n_starts=10, r_func=None):
    """
    Fit two-component mixture model using pre-defined R function.
    """
    if r_func is None:
        raise ValueError("R function not provided")
    
    try:
        result = r_func(ro.FloatVector(data), n_starts=n_starts)
        
        return {
            'mu': float(result.rx2('mu')[0]) if not ro.r('is.na')(result.rx2('mu'))[0] else np.nan,
            'kappa': float(result.rx2('kappa')[0]) if not ro.r('is.na')(result.rx2('kappa'))[0] else np.nan,
            'pU': float(result.rx2('pU')[0]) if not ro.r('is.na')(result.rx2('pU'))[0] else np.nan,
            'converged': bool(result.rx2('converged')[0]),
            'aic': float(result.rx2('aic')[0]) if not ro.r('is.na')(result.rx2('aic'))[0] else np.nan,
            'loglik': float(result.rx2('loglik')[0]) if not ro.r('is.na')(result.rx2('loglik'))[0] else np.nan
        }
    except Exception as e:
        print(f"    R fitting failed: {e}")
        return {
            'mu': np.nan,
            'kappa': np.nan,
            'pU': np.nan,
            'converged': False,
            'aic': np.nan,
            'loglik': np.nan
        }

def fit_single_vonmises_r(data, r_func=None):
    """
    Fit single von Mises model using pre-defined R function.
    """
    if r_func is None:
        raise ValueError("R function not provided")
    
    try:
        result = r_func(ro.FloatVector(data))
        
        return {
            'aic': float(result.rx2('aic')[0]) if not ro.r('is.na')(result.rx2('aic'))[0] else np.nan,
            'converged': bool(result.rx2('converged')[0])
        }
    except Exception as e:
        print(f"    R single model fitting failed: {e}")
        return {'aic': np.nan, 'converged': False}

def main():
    """
    Main function to execute VWM mixture model fitting analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM mixture model fitting analysis...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Setup R environment if available
        if RPY2_AVAILABLE:
            print("Setting up R environment and circular package...")
            try:
                utils = importr('utils')
                try:
                    circular = importr('circular')
                    print("R circular package loaded successfully")
                except RRuntimeError:
                    print("Installing R circular package...")
                    utils.install_packages('circular', repos='https://cloud.r-project.org/')
                    circular = importr('circular')
                    print("R circular package installed and loaded")
            except Exception as e:
                print(f"R setup failed: {e}, will use scipy fallback")
        # Define R model fitting functions once
        if RPY2_AVAILABLE:
            print("Defining R model fitting functions...")
            ro.r('''
            fit_mixture <- function(data, n_starts) {
                library(circular)
                
                mixture_loglik <- function(params, data) {
                    mu <- params[1]
                    kappa <- params[2] 
                    pU <- params[3]

                    if(kappa <= 0 || pU < 0 || pU > 1) return(1e10)

                    vonmises_density <- (1-pU) * dvonmises(data, mu=mu, kappa=kappa)
                    uniform_density <- pU / (2*pi)
                    mixture_density <- vonmises_density + uniform_density

                    -sum(log(pmax(mixture_density, 1e-10)))
                }

                best_loglik <- Inf
                best_params <- NULL
                converged <- FALSE

                for(i in 1:n_starts) {
                    start_mu <- runif(1, -pi, pi)
                    start_kappa <- runif(1, 0.1, 10)
                    start_pU <- runif(1, 0.1, 0.9)

                    tryCatch({
                        result <- optim(c(start_mu, start_kappa, start_pU), 
                                      mixture_loglik, data=data,
                                      method="L-BFGS-B",
                                      lower=c(-pi, 0.01, 0),
                                      upper=c(pi, 100, 1))

                        if(result$value < best_loglik) {
                            best_loglik <- result$value
                            best_params <- result$par
                            converged <- result$convergence == 0
                        }
                    }, error=function(e) NULL)
                }

                if(is.null(best_params)) {
                    return(list(mu=NA, kappa=NA, pU=NA, converged=FALSE, aic=NA, loglik=NA))
                }

                aic <- 2*3 + 2*best_loglik
                list(mu=best_params[1], kappa=best_params[2], pU=best_params[3], 
                     converged=converged, aic=aic, loglik=-best_loglik)
            }
            
            fit_single <- function(data) {
                library(circular)

                single_loglik <- function(params, data) {
                    mu <- params[1]
                    kappa <- params[2]

                    if(kappa <= 0) return(1e10)

                    density <- dvonmises(data, mu=mu, kappa=kappa)
                    -sum(log(pmax(density, 1e-10)))
                }

                best_loglik <- Inf
                best_params <- NULL
                converged <- FALSE

                for(i in 1:5) {
                    start_mu <- runif(1, -pi, pi)
                    start_kappa <- runif(1, 0.1, 10)

                    tryCatch({
                        result <- optim(c(start_mu, start_kappa), 
                                      single_loglik, data=data,
                                      method="L-BFGS-B",
                                      lower=c(-pi, 0.01),
                                      upper=c(pi, 100))

                        if(result$value < best_loglik) {
                            best_loglik <- result$value
                            best_params <- result$par
                            converged <- result$convergence == 0
                        }
                    }, error=function(e) NULL)
                }

                if(is.null(best_params)) {
                    return(list(aic=NA, converged=FALSE))
                }

                aic <- 2*2 + 2*best_loglik
                list(aic=aic, converged=converged)
            }
            ''')
            r_fit_mixture = ro.globalenv['fit_mixture']
            r_fit_single = ro.globalenv['fit_single']
        else:
            r_fit_mixture = None
            r_fit_single = None
        
        # Find the most recent input file
        input_pattern = 'outputs/cleaned_cognitive_data_*.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"Error: No input file found matching pattern {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read the input data
        print("Reading input data...")
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded data with shape: {df.shape}")
        except Exception as e:
            print(f"Error reading input file: {e}")
            return 1
        
        # Print column information
        print(f"Columns in input file: {list(df.columns)}")
        print("First 3 rows of input data:")
        print(df.head(3))
        
        # Check for required columns
        required_columns = ['participantId', 'isPractice', 'trial_type', 
                          'VWM_error_normalized_degrees', 'excluded_trial', 'exclusion_reason_trial']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns present")
        
        # Print unique values for key experimental design parameters
        print(f"Unique values in trial_type: {df['trial_type'].unique()}")
        print(f"Unique values in isPractice: {df['isPractice'].unique()}")
        print(f"Unique values in excluded_trial: {df['excluded_trial'].unique()}")
        print(f"VWM_error_normalized_degrees data type: {df['VWM_error_normalized_degrees'].dtype}")
        
        # Filter data for VWM analysis
        print("\nFiltering data for VWM analysis...")

        # Step 1: Identify and remove excluded participants first
        print("Step 1: Removing excluded participants...")
        if 'exclusion_reason_trial' in df.columns:
            excluded_participants = df[df['exclusion_reason_trial'] == 'excluded_participant']['participantId'].unique()
        else:
            excluded_participants = np.array([])  # No excluded participants if column doesn't exist
        print(f"Found {len(excluded_participants)} excluded participants")

        # Remove all data from excluded participants
        included_data = df[~df['participantId'].isin(excluded_participants)].copy()
        print(f"After removing excluded participants: {len(included_data)} rows from {included_data['participantId'].nunique()} participants")

        # Step 2: Select VWM trials from included participants only
        vwm_data = included_data[included_data['trial_type'] == 'VWM'].copy()
        print(f"After filtering for VWM trials: {len(vwm_data)} rows")

        # Step 3: Select test trials (not practice)
        vwm_data = vwm_data[vwm_data['isPractice'] == False].copy()
        print(f"After filtering for test trials (isPractice=False): {len(vwm_data)} rows")

        # Step 4: Exclude trials marked for exclusion (trial-level exclusions)
        vwm_data = vwm_data[vwm_data['excluded_trial'] == False].copy()
        print(f"After excluding marked trials (excluded_trial=False): {len(vwm_data)} rows")

        # Count valid trials per participant
        participant_counts = vwm_data.groupby('participantId').size()
        print(f"\nParticipant trial counts:")
        print(f"Mean trials per participant: {participant_counts.mean():.1f}")
        print(f"Min trials: {participant_counts.min()}")
        print(f"Max trials: {participant_counts.max()}")
        print(f"Participants with <80 trials: {(participant_counts < 80).sum()}")

        # Step 5: Remove participants with <80 valid trials
        valid_participants = participant_counts[participant_counts >= 80].index
        vwm_data = vwm_data[vwm_data['participantId'].isin(valid_participants)].copy()
        print(f"After removing participants with <80 trials: {len(vwm_data)} rows from {len(valid_participants)} participants")

        if len(vwm_data) == 0:
            print("Error: No data remaining after filtering")
            return 1
        
        # Convert error data to radians
        print("\nConverting error data to radians...")
        vwm_data['error_radians'] = convert_degrees_to_radians(vwm_data['VWM_error_normalized_degrees'])
        vwm_data['error_radians'] = wrap_to_pi(vwm_data['error_radians'])
        
        print(f"Error range in radians: [{vwm_data['error_radians'].min():.3f}, {vwm_data['error_radians'].max():.3f}]")
        
        # Initialize results storage
        results = []
        
        # Fit mixture models for each participant
        print(f"\nFitting mixture models for {len(valid_participants)} participants...")
        
        successful_fits = 0
        convergence_failures = 0
        insufficient_data_exclusions = 0
        extreme_parameter_exclusions = 0
        
        for i, participant_id in enumerate(valid_participants):
            print(f"Processing participant {i+1}/{len(valid_participants)}: {participant_id}")
            
            # Get participant data
            participant_data = vwm_data[vwm_data['participantId'] == participant_id]['error_radians'].values
            n_trials = len(participant_data)
            
            print(f"  Participant {participant_id} has {n_trials} valid trials")
            
            # Initialize result dictionary
            result = {
                'participantId': participant_id,
                'kappa_concentration': np.nan,
                'mu_bias_radians': np.nan,
                'pU_uniform_proportion': np.nan,
                'model_converged': False,
                'aic_mixture_model': np.nan,
                'aic_single_vonmises': np.nan,
                'valid_trials_used': n_trials,
                'excluded_insufficient_data': False,
                'excluded_convergence_failure': False,
                'excluded_extreme_parameters': False,
                'exclusion_reason': np.nan  # Changed from ''
            }
            
            # Check for sufficient data
            if n_trials < 20:  # Minimum for stable estimation
                print(f"  Excluding participant {participant_id}: insufficient data ({n_trials} trials)")
                result['excluded_insufficient_data'] = True
                result['exclusion_reason'] = 'insufficient_data'
                insufficient_data_exclusions += 1
                results.append(result)
                continue
            
            # Fit mixture model
            print(f"  Fitting mixture model...")
            mixture_fit = fit_mixture_model_r(participant_data, n_starts=10, r_func=r_fit_mixture)
            
            # Fit single von Mises model for comparison
            print(f"  Fitting single von Mises model...")
            single_fit = fit_single_vonmises_r(participant_data, r_func=r_fit_single)
            
            # Check convergence
            if not mixture_fit['converged']:
                print(f"  Excluding participant {participant_id}: mixture model convergence failure")
                result['excluded_convergence_failure'] = True
                result['exclusion_reason'] = 'convergence_failure'
                convergence_failures += 1
                results.append(result)
                continue
            
            # Check for extreme parameters
            kappa = mixture_fit['kappa']
            if kappa > 100 or kappa < 0.1:
                print(f"  Excluding participant {participant_id}: extreme kappa parameter ({kappa:.3f})")
                result['excluded_extreme_parameters'] = True
                result['exclusion_reason'] = 'extreme_parameters'
                extreme_parameter_exclusions += 1
                results.append(result)
                continue
            
            # Store successful fit
            result['kappa_concentration'] = mixture_fit['kappa']
            result['mu_bias_radians'] = mixture_fit['mu']
            result['pU_uniform_proportion'] = mixture_fit['pU']
            result['model_converged'] = True
            result['aic_mixture_model'] = mixture_fit['aic']
            result['aic_single_vonmises'] = single_fit['aic']
            
            # Check for minimal AIC improvement
            aic_diff = single_fit['aic'] - mixture_fit['aic']
            if pd.notna(aic_diff) and aic_diff < 2:
                result['exclusion_reason'] = 'minimal_aic_improvement'
                print(f"  Warning: Minimal model improvement (AIC diff: {aic_diff:.3f})")
            
            # Set exclusion_reason to 'none' for successful fits if not already set
            if pd.isna(result['exclusion_reason']):
                result['exclusion_reason'] = 'none'
            
            print(f"  Success: κ={mixture_fit['kappa']:.3f}, μ={mixture_fit['mu']:.3f}, pU={mixture_fit['pU']:.3f}, AIC_diff={aic_diff:.3f}")
            successful_fits += 1
            results.append(result)
        
        print(f"\nModel fitting completed:")
        print(f"Successful fits: {successful_fits}")
        print(f"Convergence failures: {convergence_failures}")
        print(f"Insufficient data exclusions: {insufficient_data_exclusions}")
        print(f"Extreme parameter exclusions: {extreme_parameter_exclusions}")
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)
        
        print("\nResults DataFrame columns:")
        print(list(results_df.columns))
        print("First 2 rows of results:")
        print(results_df.head(2))
        
        # Calculate summary statistics
        successful_results = results_df[results_df['model_converged'] == True]
        
        if len(successful_results) > 0:
            mean_kappa = successful_results['kappa_concentration'].mean()
            sd_kappa = successful_results['kappa_concentration'].std()
            mean_trials = successful_results['valid_trials_used'].mean()
        else:
            mean_kappa = np.nan
            sd_kappa = np.nan
            mean_trials = np.nan
        
        # Create summary DataFrame
        summary_data = {
            'total_participants_attempted': len(valid_participants),
            'successful_fits': successful_fits,
            'convergence_failures': convergence_failures,
            'insufficient_data_exclusions': insufficient_data_exclusions,
            'extreme_parameter_exclusions': extreme_parameter_exclusions,
            'mean_kappa_fitted': mean_kappa,
            'sd_kappa_fitted': sd_kappa,
            'mean_valid_trials_per_participant': mean_trials
        }
        
        summary_df = pd.DataFrame([summary_data])
        
        print("\nSummary DataFrame:")
        print(summary_df)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save results
        results_filename = f'outputs/VWM_mixture_model_parameters_{timestamp}.csv'
        summary_filename = f'outputs/model_fitting_summary_{timestamp}.csv'
        
        print(f"\nSaving results to {results_filename}")
        results_df.to_csv(results_filename, index=False)
        
        print(f"Saving summary to {summary_filename}")
        summary_df.to_csv(summary_filename, index=False)
        
        print("Analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
