#!/usr/bin/env python3
"""
Visual Working Memory Circular Statistical Modeling Script

This script processes VWM trial data to fit circular statistical models
to orientation recall errors for each participant.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

# Import R interface
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri, numpy2ri
    from rpy2.robjects.conversion import localconverter
    from rpy2.robjects.packages import importr
    
    # Import basic R packages first
    base = importr('base')
    utils = importr('utils')
    stats = importr('stats')
    
    print("Successfully imported basic R packages")
    
    # Function to install R packages if needed
    def install_r_package(package_name):
        try:
            importr(package_name)
            print(f"R package '{package_name}' already installed")
            return True
        except:
            print(f"Installing R package '{package_name}'...")
            try:
                utils.install_packages(package_name, repos='https://cloud.r-project.org/')
                importr(package_name)
                print(f"Successfully installed R package '{package_name}'")
                return True
            except Exception as e:
                print(f"Failed to install R package '{package_name}': {e}")
                return False
    
    # Install and import required R packages
    required_packages = ['mixtools', 'circular']
    for pkg in required_packages:
        if not install_r_package(pkg):
            print(f"Critical error: Could not install required R package '{pkg}'")
            sys.exit(1)
    
    # Import the packages after installation
    mixtools = importr('mixtools')
    circular = importr('circular')
    
    print("Successfully imported all required R packages: base, utils, stats, mixtools, circular")
    
except ImportError as e:
    print(f"Error importing rpy2: {e}")
    print("Please install rpy2: pip install rpy2")
    sys.exit(1)
except Exception as e:
    print(f"Error setting up R interface: {e}")
    sys.exit(1)

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (with wildcards)
        
    Returns:
    --------
    str or None
        Path to most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Get the most recent file by modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def load_vwm_data():
    """
    Load VWM trial data from the most recent CSV file.
    
    Returns:
    --------
    pd.DataFrame
        Loaded VWM trial data
    """
    print("Looking for VWM trial data files...")
    
    # Find the most recent VWM cleaned trial data file
    pattern = "outputs/VWM_cleaned_trial_data_*.csv"
    input_file = find_most_recent_file(pattern)
    
    if input_file is None:
        print(f"No files found matching pattern: {pattern}")
        sys.exit(1)
    
    print(f"Loading VWM data from: {input_file}")
    
    try:
        df = pd.read_csv(input_file)
        print(f"Successfully loaded {len(df)} rows of data")
        
        # Print column information
        print(f"Columns in dataset: {list(df.columns)}")
        
        # Print first 3 rows
        print("First 3 rows of data:")
        print(df.head(3))
        
        return df
    
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def validate_required_columns(df):
    """
    Validate that required columns are present in the dataframe.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input dataframe to validate
        
    Returns:
    --------
    bool
        True if all required columns present, False otherwise
    """
    required_cols = ['participantId', 'normalized_error_degrees', 'trial_excluded']
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        print(f"Missing required columns: {missing_cols}")
        return False
    
    print("All required columns present")
    
    # Print unique values for key columns
    print(f"Unique values in trial_excluded: {df['trial_excluded'].unique()}")
    print(f"Type of normalized_error_degrees: {df['normalized_error_degrees'].dtype}")
    print(f"Number of unique participants: {df['participantId'].nunique()}")
    
    return True

def filter_and_prepare_data(df):
    """
    Filter data to included trials only and prepare for circular analysis.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Raw VWM trial data
        
    Returns:
    --------
    pd.DataFrame
        Filtered and prepared data
    """
    print("Filtering data to included trials only...")
    
    # Filter to non-excluded trials
    initial_count = len(df)
    df_filtered = df[df['trial_excluded'] == False].copy()
    final_count = len(df_filtered)
    
    print(f"Filtered from {initial_count} to {final_count} trials ({initial_count - final_count} excluded)")
    
    # Convert degrees to radians
    df_filtered['error_radians'] = df_filtered['normalized_error_degrees'] * np.pi / 180
    
    print("Converted error degrees to radians")
    print(f"Error degrees range: [{df_filtered['normalized_error_degrees'].min():.2f}, {df_filtered['normalized_error_degrees'].max():.2f}]")
    print(f"Error radians range: [{df_filtered['error_radians'].min():.2f}, {df_filtered['error_radians'].max():.2f}]")
    
    return df_filtered

def check_participant_trial_counts(df):
    """
    Check trial counts per participant and identify those with sufficient data.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Filtered trial data
        
    Returns:
    --------
    tuple
        (participant_counts, valid_participants)
    """
    print("Checking trial counts per participant...")
    
    participant_counts = df.groupby('participantId').size()
    print(f"Trial counts per participant:")
    print(f"Mean: {participant_counts.mean():.1f}")
    print(f"Median: {participant_counts.median():.1f}")
    print(f"Min: {participant_counts.min()}")
    print(f"Max: {participant_counts.max()}")
    
    # Identify participants with sufficient trials (minimum 20)
    min_trials = 20
    valid_participants = participant_counts[participant_counts >= min_trials].index.tolist()
    insufficient_participants = participant_counts[participant_counts < min_trials].index.tolist()
    
    print(f"Participants with >= {min_trials} trials: {len(valid_participants)}")
    print(f"Participants with < {min_trials} trials: {len(insufficient_participants)}")
    
    if insufficient_participants:
        print(f"Participants with insufficient data: {insufficient_participants}")
    
    return participant_counts, valid_participants

def validate_error_data(error_radians, participant_id):
    """Validate error data before R processing"""
    if len(error_radians) == 0:
        return False, "No data"
    if not np.all(np.isfinite(error_radians)):
        return False, "Contains non-finite values"
    if not np.all(np.abs(error_radians) <= np.pi):
        return False, "Values outside [-π, π] range"
    return True, "Valid"

def fit_circular_models_for_participant(participant_id, error_radians):
    """
    Fit circular statistical models for a single participant.

    Parameters:
    -----------
    participant_id : str
        Participant identifier
    error_radians : array-like
        Error values in radians

    Returns:
    --------
    tuple
        (Model fitting results dict, wrapped_normal_loglik value)
    """
    print(f"Fitting models for participant {participant_id} with {len(error_radians)} trials")

    results = {
        'participantId': participant_id,
        'kappa_vonmises': np.nan,
        'mu_bias_vonmises': np.nan,
        'guess_rate_proportion': np.nan,
        'vonmises_AIC': np.nan,
        'wrapped_normal_AIC': np.nan,
        'best_model': 'none',
        'model_converged': False,
        'num_trials_fitted': len(error_radians),
        'log_likelihood': np.nan,
        'model_fit_quality': 'poor',
        'excluded_from_modeling': False,
        'exclusion_reason': 'none'
    }

    # Add data validation before R processing
    is_valid, validation_msg = validate_error_data(error_radians, participant_id)
    if not is_valid:
        print(f"  Data validation failed: {validation_msg}")
        results['excluded_from_modeling'] = True
        results['exclusion_reason'] = f'invalid_data_{validation_msg}'
        return results, np.nan

    print(f"  Data validation passed: {len(error_radians)} valid trials")
    print(f"  Error range: [{np.min(error_radians):.3f}, {np.max(error_radians):.3f}] radians")

    wrapped_normal_loglik = np.nan

    try:
        # Use conversion context for all R operations
        with localconverter(robjects.default_converter + pandas2ri.converter + numpy2ri.converter):
            # Convert to R vector
            r_errors = robjects.FloatVector(error_radians)

            # Fit two-component mixture model using mixtools
            print(f"  Fitting von Mises mixture model...")

            # Define custom R function for proper circular models
            r_code = """
            options(warn=-1)  # Suppress warnings
            # Load required libraries
            library(circular)
            library(stats)

            # Custom von Mises + Uniform mixture model using MLE
            fit_vonmises_mixture <- function(errors) {
                tryCatch({
                    # Convert to circular object
                    circ_errors <- circular(errors, units="radians", template="none")
                    n <- length(errors)

                    # Define log-likelihood function for von Mises + Uniform mixture
                    loglik_vm_uniform <- function(params) {
                        mu <- params[1]
                        kappa <- exp(params[2])  # Ensure kappa > 0
                        p <- plogis(params[3])   # Ensure 0 < p < 1

                        # von Mises density
                        vm_density <- dvonmises(circ_errors, mu=mu, kappa=kappa)
                        # Uniform density on circle
                        uniform_density <- rep(1/(2*pi), n)

                        # Mixture density
                        mixture_density <- p * vm_density + (1-p) * uniform_density

                        # Return negative log-likelihood for minimization
                        -sum(log(mixture_density + 1e-10))  # Add small constant to avoid log(0)
                    }

                    # Initial parameter estimates
                    mu_init <- as.numeric(mean(circ_errors))
                    kappa_init <- log(max(0.1, rho.circular(circ_errors) * 2))  # Rough estimate
                    p_init <- qlogis(0.7)  # Start with 70% memory component

                    # Optimize
                    result <- optim(c(mu_init, kappa_init, p_init), 
                                   loglik_vm_uniform, 
                                   method="BFGS",
                                   control=list(maxit=1000))

                    if (result$convergence == 0) {
                        mu_est <- result$par[1]
                        kappa_est <- exp(result$par[2])
                        p_est <- plogis(result$par[3])
                        guess_rate <- 1 - p_est

                        loglik <- -result$value
                        aic <- 2 * 3 - 2 * loglik  # 3 parameters

                        list(
                            kappa = kappa_est,
                            mu = mu_est,
                            guess_rate = guess_rate,
                            loglik = loglik,
                            aic = aic,
                            converged = TRUE
                        )
                    } else {
                        list(
                            kappa = NA,
                            mu = NA,
                            guess_rate = NA,
                            loglik = NA,
                            aic = NA,
                            converged = FALSE
                        )
                    }
                }, error = function(e) {
                    error_msg <- paste0("R error in fit_vonmises_mixture: ", e$message)
                    print(error_msg)
                    list(
                        kappa = NA,
                        mu = NA,
                        guess_rate = NA,
                        loglik = NA,
                        aic = NA,
                        converged = FALSE,
                        error_message = error_msg
                    )
                })
            }

            # Wrapped normal model using MLE
            fit_wrapped_normal <- function(errors) {
                tryCatch({
                    circ_errors <- circular(errors, units="radians", template="none")

                    # Use circular package's MLE function
                    fit <- mle.wrappednormal(circ_errors)

                    # Extract parameters
                    mu_est <- fit$mu
                    rho_est <- fit$rho

                    # Calculate log-likelihood
                    loglik <- sum(log(dwrappednormal(circ_errors, mu=mu_est, rho=rho_est)))

                    # Calculate AIC
                    aic <- 2 * 2 - 2 * loglik  # 2 parameters

                    list(
                        aic = aic,
                        loglik = loglik,
                        converged = TRUE
                    )
                }, error = function(e) {
                    error_msg <- paste0("R error in fit_wrapped_normal: ", e$message)
                    print(error_msg)
                    list(
                        aic = NA,
                        loglik = NA,
                        converged = FALSE,
                        error_message = error_msg
                    )
                })
            }
            """

            # Execute R code
            robjects.r(r_code)
            fit_vonmises_mixture = robjects.globalenv['fit_vonmises_mixture']
            fit_wrapped_normal = robjects.globalenv['fit_wrapped_normal']

            # Fit von Mises mixture model
            vm_result = fit_vonmises_mixture(r_errors)
            vm_dict = dict(zip(list(vm_result.names()), list(vm_result)))
            # Each value is an R vector, so access [0] for scalar

            if bool(vm_dict['converged'][0]):
                results['kappa_vonmises'] = float(vm_dict['kappa'][0])
                results['mu_bias_vonmises'] = float(vm_dict['mu'][0])
                results['guess_rate_proportion'] = float(vm_dict['guess_rate'][0])
                results['vonmises_AIC'] = float(vm_dict['aic'][0])
                results['log_likelihood'] = float(vm_dict['loglik'][0])
                results['model_converged'] = True
                results['model_fit_quality'] = 'good'

                print(f"  von Mises model converged: kappa={results['kappa_vonmises']:.3f}, guess_rate={results['guess_rate_proportion']:.3f}")
            else:
                print(f"  von Mises model failed to converge")
                results['model_fit_quality'] = 'poor'

            # Fit wrapped normal model for comparison
            wn_result = fit_wrapped_normal(r_errors)
            wn_dict = dict(zip(list(wn_result.names()), list(wn_result)))

            if bool(wn_dict['converged'][0]):
                results['wrapped_normal_AIC'] = float(wn_dict['aic'][0])
                wrapped_normal_loglik = float(wn_dict['loglik'][0])
                print(f"  Wrapped normal model converged: AIC={results['wrapped_normal_AIC']:.3f}")
            else:
                wrapped_normal_loglik = np.nan
                print(f"  Wrapped normal model failed to converge")

            # Determine best model based on AIC
            if not np.isnan(results['vonmises_AIC']) and not np.isnan(results['wrapped_normal_AIC']):
                if results['vonmises_AIC'] < results['wrapped_normal_AIC']:
                    results['best_model'] = 'vonmises'
                else:
                    results['best_model'] = 'wrapped_normal'
            elif not np.isnan(results['vonmises_AIC']):
                results['best_model'] = 'vonmises'
            elif not np.isnan(results['wrapped_normal_AIC']):
                results['best_model'] = 'wrapped_normal'

            # Quality control checks
            if results['model_converged']:
                if (results['kappa_vonmises'] > 0 and
                    0 <= results['guess_rate_proportion'] <= 1):
                    results['model_fit_quality'] = 'good'
                else:
                    results['model_fit_quality'] = 'poor'
                    print(f"  Parameter estimates out of bounds")

    except Exception as e:
        print(f"  Error fitting models: {e}")
        print(f"  Error type: {type(e).__name__}")
        if hasattr(e, 'args') and e.args:
            print(f"  Error details: {e.args}")
        results['excluded_from_modeling'] = True
        results['exclusion_reason'] = f'model_fitting_error_{type(e).__name__}'

    return results, wrapped_normal_loglik

def process_all_participants(df, valid_participants):
    """
    Process all participants with sufficient data.

    Parameters:
    -----------
    df : pd.DataFrame
        Filtered trial data
    valid_participants : list
        List of participant IDs with sufficient data

    Returns:
    --------
    tuple
        (main_results, validation_results)
    """
    print(f"Processing {len(valid_participants)} participants...")

    main_results = []
    validation_results = []

    for i, participant_id in enumerate(valid_participants):
        print(f"Processing participant {i+1}/{len(valid_participants)}: {participant_id}")

        # Get participant data
        participant_data = df[df['participantId'] == participant_id]
        error_radians = participant_data['error_radians'].values

        # Fit models
        result, wrapped_normal_loglik = fit_circular_models_for_participant(participant_id, error_radians)
        main_results.append(result)

        # Add validation results
        if result['model_converged']:
            # von Mises validation entry
            validation_results.append({
                'participantId': participant_id,
                'model_type': 'vonmises',
                'AIC_value': result['vonmises_AIC'],
                'log_likelihood_value': result['log_likelihood'],
                'kappa_estimate': result['kappa_vonmises'],
                'convergence_status': result['model_converged']
            })

            # Wrapped normal validation entry
            if not np.isnan(result['wrapped_normal_AIC']):
                validation_results.append({
                    'participantId': participant_id,
                    'model_type': 'wrapped_normal',
                    'AIC_value': result['wrapped_normal_AIC'],
                    'log_likelihood_value': wrapped_normal_loglik,
                    'kappa_estimate': np.nan,  # Not applicable for wrapped normal
                    'convergence_status': True
                })

    return main_results, validation_results

def handle_insufficient_participants(participant_counts, valid_participants):
    """
    Create results entries for participants with insufficient data.
    
    Parameters:
    -----------
    participant_counts : pd.Series
        Trial counts per participant
    valid_participants : list
        List of valid participant IDs
        
    Returns:
    --------
    list
        Results for insufficient participants
    """
    insufficient_results = []
    min_trials = 20
    
    for participant_id, count in participant_counts.items():
        if participant_id not in valid_participants:
            result = {
                'participantId': participant_id,
                'kappa_vonmises': np.nan,
                'mu_bias_vonmises': np.nan,
                'guess_rate_proportion': np.nan,
                'vonmises_AIC': np.nan,
                'wrapped_normal_AIC': np.nan,
                'best_model': 'none',
                'model_converged': False,
                'num_trials_fitted': count,
                'log_likelihood': np.nan,
                'model_fit_quality': 'insufficient_data',
                'excluded_from_modeling': True,
                'exclusion_reason': f'insufficient_trials_{count}_min_{min_trials}'
            }
            insufficient_results.append(result)
    
    print(f"Created {len(insufficient_results)} entries for participants with insufficient data")
    return insufficient_results

def save_results(main_results, validation_results):
    """
    Save modeling results to CSV files.
    
    Parameters:
    -----------
    main_results : list
        Main modeling results
    validation_results : list
        Model validation results
    """
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save main results
    main_df = pd.DataFrame(main_results)
    main_filename = f'outputs/VWM_circular_model_parameters_{timestamp}.csv'
    main_df.to_csv(main_filename, index=False)
    
    print(f"Saved main results to: {main_filename}")
    print(f"Main results shape: {main_df.shape}")
    print("Main results columns:", list(main_df.columns))
    print("First 2 rows of main results:")
    print(main_df.head(2))
    
    # Save validation results
    if validation_results:
        validation_df = pd.DataFrame(validation_results)
        validation_filename = f'outputs/circular_model_validation_{timestamp}.csv'
        validation_df.to_csv(validation_filename, index=False)
        
        print(f"Saved validation results to: {validation_filename}")
        print(f"Validation results shape: {validation_df.shape}")
        print("Validation results columns:", list(validation_df.columns))
        print("First 2 rows of validation results:")
        print(validation_df.head(2))
    else:
        print("No validation results to save")

def print_summary_statistics(main_results):
    """
    Print summary statistics of modeling results.
    
    Parameters:
    -----------
    main_results : list
        Main modeling results
    """
    print("\n=== MODELING SUMMARY STATISTICS ===")
    
    main_df = pd.DataFrame(main_results)
    
    # Overall statistics
    total_participants = len(main_df)
    converged_participants = main_df['model_converged'].sum()
    excluded_participants = main_df['excluded_from_modeling'].sum()
    
    print(f"Total participants: {total_participants}")
    print(f"Successfully modeled: {converged_participants}")
    print(f"Excluded from modeling: {excluded_participants}")
    
    # Exclusion reasons
    exclusion_counts = main_df['exclusion_reason'].value_counts()
    print(f"Exclusion reasons:")
    for reason, count in exclusion_counts.items():
        if reason != 'none':
            print(f"  {reason}: {count}")
    
    # Model parameter statistics (for converged models only)
    converged_df = main_df[main_df['model_converged'] == True]
    
    if len(converged_df) > 0:
        print(f"\nParameter statistics for {len(converged_df)} converged models:")
        print(f"Kappa (concentration):")
        print(f"  Mean: {converged_df['kappa_vonmises'].mean():.3f}")
        print(f"  Median: {converged_df['kappa_vonmises'].median():.3f}")
        print(f"  Range: [{converged_df['kappa_vonmises'].min():.3f}, {converged_df['kappa_vonmises'].max():.3f}]")
        
        print(f"Guess rate:")
        print(f"  Mean: {converged_df['guess_rate_proportion'].mean():.3f}")
        print(f"  Median: {converged_df['guess_rate_proportion'].median():.3f}")
        print(f"  Range: [{converged_df['guess_rate_proportion'].min():.3f}, {converged_df['guess_rate_proportion'].max():.3f}]")
        
        # Best model counts
        best_model_counts = converged_df['best_model'].value_counts()
        print(f"Best fitting models:")
        for model, count in best_model_counts.items():
            print(f"  {model}: {count}")

def main():
    """
    Main execution function for VWM circular statistical modeling.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("Starting VWM Circular Statistical Modeling Script")
        print("=" * 50)
        
        # Load data
        df = load_vwm_data()
        
        # Validate required columns
        if not validate_required_columns(df):
            print("Required columns missing. Exiting.")
            return 1
        
        # Filter and prepare data
        df_filtered = filter_and_prepare_data(df)
        
        # Check participant trial counts
        participant_counts, valid_participants = check_participant_trial_counts(df_filtered)
        
        if len(valid_participants) == 0:
            print("No participants with sufficient data for modeling. Exiting.")
            return 1

        # Add option to test with subset first
        TEST_SUBSET = False  # Set to False for full processing
        original_valid_participants = valid_participants.copy()  # Keep original list
        if TEST_SUBSET and len(valid_participants) > 5:
            print("Testing with subset of 5 participants first...")
            valid_participants = valid_participants[:5]
        
        # Process participants with sufficient data
        main_results, validation_results = process_all_participants(df_filtered, valid_participants)
        
        # Handle participants with insufficient data
        insufficient_results = handle_insufficient_participants(
            participant_counts,
            valid_participants
        )
        
        # Combine all results
        all_main_results = main_results + insufficient_results
        
        # Save results
        save_results(all_main_results, validation_results)
        
        # Print summary statistics
        print_summary_statistics(all_main_results)
        
        print("\n" + "=" * 50)
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
