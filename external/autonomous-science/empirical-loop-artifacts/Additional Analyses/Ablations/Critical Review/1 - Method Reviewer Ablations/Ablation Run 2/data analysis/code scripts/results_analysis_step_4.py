import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

# Import R interface
try:
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr

    # Import R packages
    base = importr('base')
    stats = importr('stats')
    mixtools = importr('mixtools')
    circular = importr('circular')

    # Install required R packages if not already installed
    utils = importr('utils')
    try:
        utils.install_packages(robjects.StrVector(['mixtools', 'circular']), repos='https://cloud.r-project.org/')
        print("R packages installed successfully")
    except Exception as e:
        print(f"Note: R package installation attempt: {e}")

    print("Successfully imported R packages")
except ImportError as e:
    print(f"Error importing rpy2 or R packages: {e}")
    sys.exit(1)

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
    
    # Get the most recent file by modification time
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def convert_degrees_to_radians(degrees):
    """
    Convert degrees to radians for circular statistics.
    
    Parameters:
    degrees (float or array): Error values in degrees
    
    Returns:
    float or array: Error values in radians
    """
    return degrees * np.pi / 180

def define_r_fitting_function():
    """Defines the R mixture model fitting function in the R global environment."""
    r_fit_code = """
    fit_vm_uniform_mixture <- function(errors) {
        library(circular)
        n <- length(errors)
        # Negative log-likelihood for von Mises + uniform mixture
        negloglik <- function(par) {
            mu <- par[1]
            kappa <- par[2]
            p_guess <- par[3]
            # von Mises density with explicit circular conversion
            vm_density <- dvonmises(circular(errors), mu=circular(mu), kappa=kappa)
            # Uniform density over [-pi/2, pi/2]
            unif_density <- rep(1/(pi), n)
            # Mixture
            mix_density <- (1 - p_guess) * vm_density + p_guess * unif_density
            # Avoid log(0)
            mix_density[mix_density < 1e-10] <- 1e-10
            -sum(log(mix_density))
        }
        # Initial values: mu=mean, kappa=5, p_guess=0.2
        mu_init <- mean.circular(circular(errors))
        init <- c(mu_init, 5, 0.2)
        # Lower and upper bounds: mu in [-pi/2, pi/2], kappa>0, p_guess in [0,1]
        lower <- c(-pi/2, 0.01, 0.0)
        upper <- c(pi/2, 100, 1.0)
        fit <- optim(init, negloglik, method="L-BFGS-B", lower=lower, upper=upper)
        # Extract parameters
        mu_hat <- fit$par[1]
        kappa_hat <- fit$par[2]
        p_guess_hat <- fit$par[3]
        converged <- fit$convergence == 0
        loglik <- -fit$value
        list(
            kappa_concentration = kappa_hat,
            mu_bias = mu_hat,
            guess_rate = p_guess_hat,
            model_converged = converged,
            log_likelihood = loglik
        )
    }
    """
    robjects.r(r_fit_code)

def fit_mixture_model_r(error_radians):
    """
    Fit a von Mises + uniform mixture model using a pre-defined R function.

    Parameters:
    error_radians (array): Array of error values in radians

    Returns:
    dict: Dictionary containing fitted parameters and model diagnostics
    """
    try:
        # Convert to R vector
        r_errors = robjects.FloatVector(error_radians)
        n_trials = len(error_radians)
        print(f"Fitting von Mises + uniform mixture model for {n_trials} trials")

        # Call the pre-defined R function
        fit_func = robjects.globalenv['fit_vm_uniform_mixture']
        fit_result = fit_func(r_errors)

        # Extract results from R list
        kappa_concentration = float(fit_result.rx2('kappa_concentration')[0])
        mu_bias = float(fit_result.rx2('mu_bias')[0])
        guess_rate = float(fit_result.rx2('guess_rate')[0])
        model_converged = bool(fit_result.rx2('model_converged')[0])
        log_likelihood = float(fit_result.rx2('log_likelihood')[0])

        # Ensure parameters are in valid ranges
        kappa_concentration = max(0.01, min(kappa_concentration, 100))
        guess_rate = max(0.0, min(guess_rate, 1.0))
        mu_bias = max(-np.pi/2, min(mu_bias, np.pi/2))

        return {
            'kappa_concentration': kappa_concentration,
            'mu_bias': mu_bias,
            'guess_rate': guess_rate,
            'model_converged': model_converged,
            'log_likelihood': log_likelihood,
            'fit_quality_flag': 'good'
        }

    except Exception as e:
        print(f"Error in mixture model fitting: {e}")
        return {
            'kappa_concentration': np.nan,
            'mu_bias': np.nan,
            'guess_rate': np.nan,
            'model_converged': False,
            'log_likelihood': np.nan,
            'fit_quality_flag': 'error'
        }

def validate_parameters(params):
    """
    Validate fitted parameters and assign quality flags.
    
    Parameters:
    params (dict): Dictionary of fitted parameters
    
    Returns:
    dict: Updated parameters with quality flags
    """
    kappa = params['kappa_concentration']
    mu = params['mu_bias']
    guess_rate = params['guess_rate']
    
    # Check for valid ranges
    flags = []
    
    if not params['model_converged']:
        flags.append('no_convergence')
    
    if np.isnan(kappa) or kappa <= 0:
        flags.append('invalid_kappa')
    elif kappa > 50:  # Very high precision, might be unrealistic
        flags.append('extreme_kappa')
    
    if np.isnan(mu) or abs(mu) > np.pi:
        flags.append('invalid_bias')
    elif abs(mu) > np.pi/2:  # Large bias
        flags.append('large_bias')
    
    if np.isnan(guess_rate) or guess_rate < 0 or guess_rate > 1:
        flags.append('invalid_guess_rate')
    elif guess_rate > 0.8:  # Very high guessing
        flags.append('high_guessing')
    
    if not flags:
        params['fit_quality_flag'] = 'good'
    else:
        params['fit_quality_flag'] = ';'.join(flags)
    
    return params

def main():
    """
    Main function to process VWM data and fit mixture models.
    """
    try:
        print("Starting VWM mixture model analysis")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/VWM_MRT_cleaned_data_*.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read the input data
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded data with {len(df)} rows and {len(df.columns)} columns")
        except Exception as e:
            print(f"Error reading input file: {e}")
            return 1
        
        # Print all columns
        print("All columns in dataset:")
        print(list(df.columns))
        
        # Print first three rows
        print("\nFirst three rows of data:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'isPractice', 'VWM_error_degrees', 'VWM_block', 'excluded_from_VWM', 'trial_excluded']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key columns:")
        print(f"isPractice: {sorted(df['isPractice'].unique())}")
        print(f"VWM_block: {sorted(df['VWM_block'].unique())}")
        print(f"excluded_from_VWM: {sorted(df['excluded_from_VWM'].unique())}")
        print(f"trial_excluded: {sorted(df['trial_excluded'].unique())}")
        print(f"VWM_error_degrees type: {df['VWM_error_degrees'].dtype}")
        
        # Filter data for VWM analysis
        print("\nFiltering data for VWM analysis...")
        
        # Initial data count
        print(f"Initial data: {len(df)} rows")
        
        # Filter for test blocks (not practice)
        df_filtered = df[df['isPractice'] == False].copy()
        print(f"After removing practice trials: {len(df_filtered)} rows")
        
        # Filter for test-related VWM blocks (assuming any non-null VWM_block is test-related)
        df_filtered = df_filtered[df_filtered['VWM_block'].notna()].copy()
        print(f"After filtering for test blocks: {len(df_filtered)} rows")
        
        # Exclude participants marked for exclusion
        participants_before = df_filtered['participantId'].nunique()
        df_filtered = df_filtered[df_filtered['excluded_from_VWM'] != True].copy()
        participants_after = df_filtered['participantId'].nunique()
        print(f"After excluding participants (excluded_from_VWM=True): {len(df_filtered)} rows, {participants_after} participants (was {participants_before})")
        
        # Exclude individual trials marked for exclusion
        df_filtered = df_filtered[df_filtered['trial_excluded'] != True].copy()
        print(f"After excluding trials (trial_excluded=True): {len(df_filtered)} rows")
        
        # Remove rows with missing VWM_error_degrees
        df_filtered = df_filtered[df_filtered['VWM_error_degrees'].notna()].copy()
        print(f"After removing missing VWM_error_degrees: {len(df_filtered)} rows")
        
        if len(df_filtered) == 0:
            print("No data remaining after filtering")
            return 1
        
        # Convert error data to radians
        print("\nConverting error degrees to radians...")
        df_filtered['error_radians'] = convert_degrees_to_radians(df_filtered['VWM_error_degrees'])
        
        # Ensure errors are within ±π/2 range
        df_filtered['error_radians'] = np.clip(df_filtered['error_radians'], -np.pi/2, np.pi/2)
        
        print(f"Error range in radians: {df_filtered['error_radians'].min():.3f} to {df_filtered['error_radians'].max():.3f}")
        
        # Print intermediate dataframe info
        print("\nFiltered dataframe columns:")
        print(list(df_filtered.columns))
        print("\nFirst two rows of filtered data:")
        print(df_filtered.head(2))
        
        # Define the R fitting function once before the loop
        print("\nDefining R mixture model fitting function...")
        define_r_fitting_function()
        print("R fitting function defined successfully")
        
        # Get list of participants
        participants = df_filtered['participantId'].unique()
        print(f"\nFitting mixture models for {len(participants)} participants...")
        
        # Initialize results list
        results = []
        
        # Fit mixture model for each participant
        for i, participant in enumerate(participants):
            print(f"\nProcessing participant {i+1}/{len(participants)}: {participant}")
            
            # Get participant data
            participant_data = df_filtered[df_filtered['participantId'] == participant]
            error_data = participant_data['error_radians'].values
            
            print(f"Participant {participant} has {len(error_data)} trials")
            
            # Check minimum number of trials
            if len(error_data) < 10:
                print(f"Insufficient trials ({len(error_data)}) for participant {participant}")
                result = {
                    'participantId': participant,
                    'kappa_concentration': np.nan,
                    'mu_bias': np.nan,
                    'guess_rate': np.nan,
                    'model_converged': False,
                    'log_likelihood': np.nan,
                    'n_trials_used': len(error_data),
                    'fit_quality_flag': 'insufficient_trials'
                }
            else:
                # Fit mixture model
                fit_params = fit_mixture_model_r(error_data)
                
                # Validate parameters
                fit_params = validate_parameters(fit_params)
                
                # Create result dictionary
                result = {
                    'participantId': participant,
                    'kappa_concentration': fit_params['kappa_concentration'],
                    'mu_bias': fit_params['mu_bias'],
                    'guess_rate': fit_params['guess_rate'],
                    'model_converged': fit_params['model_converged'],
                    'log_likelihood': fit_params['log_likelihood'],
                    'n_trials_used': len(error_data),
                    'fit_quality_flag': fit_params['fit_quality_flag']
                }
                
                print(f"Fitted parameters: kappa={result['kappa_concentration']:.3f}, mu={result['mu_bias']:.3f}, guess_rate={result['guess_rate']:.3f}")
            
            results.append(result)
        
        # Convert results to DataFrame
        results_df = pd.DataFrame(results)
        
        print(f"\nFitting completed for all participants")
        print(f"Results shape: {results_df.shape}")
        
        # Print results summary
        print("\nResults summary:")
        print(f"Participants with converged models: {results_df['model_converged'].sum()}")
        print(f"Participants with good fits: {(results_df['fit_quality_flag'] == 'good').sum()}")
        
        # Print results dataframe info
        print("\nResults dataframe columns:")
        print(list(results_df.columns))
        print("\nFirst two rows of results:")
        print(results_df.head(2))
        
        # Quality control summary
        print("\nQuality control summary:")
        flag_counts = results_df['fit_quality_flag'].value_counts()
        print(flag_counts)
        
        # Parameter summary statistics
        print("\nParameter summary statistics:")
        print(f"Kappa (concentration) - Mean: {results_df['kappa_concentration'].mean():.3f}, Std: {results_df['kappa_concentration'].std():.3f}")
        print(f"Mu (bias) - Mean: {results_df['mu_bias'].mean():.3f}, Std: {results_df['mu_bias'].std():.3f}")
        print(f"Guess rate - Mean: {results_df['guess_rate'].mean():.3f}, Std: {results_df['guess_rate'].std():.3f}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f'outputs/VWM_mixture_model_parameters_{timestamp}.csv'
        
        # Ensure only required columns are included
        output_columns = ['participantId', 'kappa_concentration', 'mu_bias', 'guess_rate', 'model_converged', 'log_likelihood', 'n_trials_used', 'fit_quality_flag']
        results_output = results_df[output_columns].copy()
        
        results_output.to_csv(output_filename, index=False)
        print(f"\nResults saved to: {output_filename}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
