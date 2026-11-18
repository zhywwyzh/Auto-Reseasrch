import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy.optimize import minimize
from scipy.stats import vonmises, uniform
import warnings
import gc
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to search for
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def wrap_angle(angle):
    """
    Wrap angle to [-π, π] range.
    
    Parameters:
    angle (float): Angle in radians
    
    Returns:
    float: Wrapped angle in [-π, π] range
    """
    return np.arctan2(np.sin(angle), np.cos(angle))

def parse_orientations(orientation_string):
    """
    Parse comma-separated orientation string into list of floats.
    
    Parameters:
    orientation_string (str): String containing comma-separated angles
    
    Returns:
    list: List of orientation angles as floats
    """
    try:
        if pd.isna(orientation_string) or not isinstance(orientation_string, str):
            return []
        return [float(x.strip()) for x in orientation_string.split(',')]
    except:
        return []

def degrees_to_radians(degrees):
    """
    Convert degrees to radians.
    
    Parameters:
    degrees (float): Angle in degrees
    
    Returns:
    float: Angle in radians
    """
    return degrees * np.pi / 180

def calculate_angular_difference(angle1, angle2):
    """
    Calculate angular difference between two angles in degrees, convert to radians and wrap.
    
    Parameters:
    angle1 (float): First angle in degrees
    angle2 (float): Second angle in degrees
    
    Returns:
    float: Angular difference in radians, wrapped to [-π, π]
    """
    if pd.isna(angle1) or pd.isna(angle2):
        return np.nan
    diff = angle1 - angle2
    diff_rad = degrees_to_radians(diff)
    return wrap_angle(diff_rad)

def negative_log_likelihood_mixture(params, errors, non_target_errors):
    """
    Calculate negative log-likelihood for three-component mixture model.
    
    Parameters:
    params (list): Model parameters [kappa, mu, guess_rate, non_target_rate]
    errors (array): Target error data in radians
    non_target_errors (list): List of non-target error arrays for each trial
    
    Returns:
    float: Negative log-likelihood
    """
    kappa, mu, guess_rate, non_target_rate = params
    
    # Ensure parameters are valid
    if kappa <= 0 or guess_rate < 0 or non_target_rate < 0 or (guess_rate + non_target_rate) >= 1:
        return np.inf
    
    target_rate = 1 - guess_rate - non_target_rate
    if target_rate <= 0:
        return np.inf
    
    n_trials = len(errors)
    log_likelihood = 0
    
    for i in range(n_trials):
        error = errors[i]
        
        # Target component (von Mises)
        target_prob = vonmises.pdf(error, kappa, loc=mu)
        
        # Guess component (uniform)
        guess_prob = 1 / (2 * np.pi)
        
        # Non-target component (von Mises centered on non-target locations)
        if len(non_target_errors[i]) > 0:
            non_target_probs = [vonmises.pdf(nt_error, kappa, loc=0) for nt_error in non_target_errors[i]]
            non_target_prob = np.mean(non_target_probs)
        else:
            non_target_prob = 1 / (2 * np.pi)  # Fallback for set size 1
        
        # Mixture probability
        mixture_prob = (target_rate * target_prob + 
                       guess_rate * guess_prob + 
                       non_target_rate * non_target_prob)
        
        if mixture_prob <= 0:
            return np.inf
        
        log_likelihood += np.log(mixture_prob)
    
    return -log_likelihood

def fit_mixture_model(errors, non_target_errors):
    """
    Fit three-component mixture model using maximum likelihood estimation.
    """
    # Set random seed for reproducible results
    np.random.seed(42)

    # Estimate initial parameters from data
    # Estimate kappa from circular variance
    mean_cos = np.mean(np.cos(errors))
    mean_sin = np.mean(np.sin(errors))
    R = np.sqrt(mean_cos**2 + mean_sin**2)  # Resultant vector length
    if R > 0.53:  # Use approximation for high concentration
        kappa_init = 2*R + R**3 + 5*R**5/6
    elif R < 0.53:
        kappa_init = -0.4 + 1.39*R + 0.43/(1-R)
    else:
        kappa_init = 1.0
    kappa_init = max(0.1, min(kappa_init, 20))  # Reasonable bounds

    # Estimate mu from circular mean
    mu_init = np.arctan2(mean_sin, mean_cos)

    # Estimate guess rate from proportion of errors > 90 degrees
    large_errors = np.sum(np.abs(errors) > np.pi/2) / len(errors)
    guess_init = min(0.5, max(0.01, large_errors * 0.5))  # Conservative estimate

    # Initial parameter guesses based on data
    initial_params = [kappa_init, mu_init, guess_init, 0.05]

    # More permissive parameter bounds
    bounds = [(0.01, 200),      # kappa > 0, allow higher values
              (-np.pi, np.pi),   # mu in [-π, π]
              (0.0, 0.99),      # guess_rate, allow higher values
              (0.0, 0.99)]      # non_target_rate, allow higher values

    # Constraint: guess_rate + non_target_rate < 0.99 (more permissive)
    constraint = {'type': 'ineq', 'fun': lambda x: 0.99 - x[2] - x[3]}

    best_result = None
    best_nll = np.inf

    # Try multiple starting points with different strategies
    starting_points = []

    # Strategy 1: Data-driven initialization
    starting_points.append(initial_params)

    # Strategy 2: Conservative high-precision model
    starting_points.append([10.0, 0.0, 0.05, 0.05])

    # Strategy 3: High guess rate model
    starting_points.append([2.0, 0.0, 0.3, 0.1])

    # Strategy 4: Balanced model
    starting_points.append([5.0, mu_init, 0.15, 0.15])

    # Strategy 5-15: More diverse random variations
    for _ in range(11):
        starting_points.append([
            np.random.uniform(0.1, 50),  # Much wider kappa range
            np.random.uniform(-np.pi, np.pi),  # Full mu range
            np.random.uniform(0.0, 0.8),  # Wider guess rate range
            np.random.uniform(0.0, 0.5)   # Wider non-target rate range
        ])

    methods = ['SLSQP', 'L-BFGS-B']

    # Penalized NLL for L-BFGS-B (no constraints)
    def penalized_nll_mixture(params, errors, non_target_errors):
        nll = negative_log_likelihood_mixture(params, errors, non_target_errors)
        if params[2] + params[3] >= 0.99:
            nll += 1000 * (params[2] + params[3] - 0.98)**2
        return nll

    for method in methods:
        for start_params in starting_points:
            try:
                # Ensure starting parameters are within bounds
                start_params[0] = max(bounds[0][0], min(bounds[0][1], start_params[0]))
                start_params[1] = max(bounds[1][0], min(bounds[1][1], start_params[1]))
                start_params[2] = max(bounds[2][0], min(bounds[2][1], start_params[2]))
                start_params[3] = max(bounds[3][0], min(bounds[3][1], start_params[3]))

                # Ensure constraint is satisfied
                total_rate = start_params[2] + start_params[3]
                if total_rate >= 0.99:
                    # Rescale proportionally
                    if total_rate > 0:
                        start_params[2] = start_params[2] / total_rate * 0.8
                        start_params[3] = start_params[3] / total_rate * 0.8
                    else:
                        start_params[2] = 0.0
                        start_params[3] = 0.0

                if method == 'L-BFGS-B':
                    result = minimize(
                        penalized_nll_mixture,
                        start_params,
                        args=(errors, non_target_errors),
                        bounds=bounds,
                        method=method,
                        options={'maxiter': 2000, 'ftol': 1e-8}
                    )
                else:
                    result = minimize(
                        negative_log_likelihood_mixture,
                        start_params,
                        args=(errors, non_target_errors),
                        bounds=bounds,
                        constraints=constraint,
                        method=method,
                        options={'maxiter': 2000, 'ftol': 1e-8}
                    )

                if result.success and result.fun < best_nll:
                    kappa, mu, guess_rate, non_target_rate = result.x
                    if (kappa > 0.001 and kappa < 200 and 
                        guess_rate >= 0.0 and non_target_rate >= 0.0 and
                        guess_rate + non_target_rate <= 0.99):
                        best_result = result
                        best_nll = result.fun
            except:
                continue

    if best_result is None:
        return {
            'vonMises_kappa': np.nan,
            'vonMises_mu': np.nan,
            'guess_rate': np.nan,
            'non_target_rate': np.nan,
            'convergence_status': False,
            'log_likelihood': np.nan,
            'AIC': np.nan
        }

    kappa, mu, guess_rate, non_target_rate = best_result.x
    log_likelihood = -best_result.fun
    aic = 2 * 4 - 2 * log_likelihood  # 4 parameters

    return {
        'vonMises_kappa': kappa,
        'vonMises_mu': mu,
        'guess_rate': guess_rate,
        'non_target_rate': non_target_rate,
        'convergence_status': best_result.success,
        'log_likelihood': log_likelihood,
        'AIC': aic
    }

def wrapped_normal_pdf(x, mu, sigma):
    """
    Probability density function for wrapped normal distribution.
    
    Parameters:
    x (float): Value
    mu (float): Mean
    sigma (float): Standard deviation
    
    Returns:
    float: PDF value
    """
    if sigma <= 0:
        return 0
    # Approximate wrapped normal using sum of normal distributions
    pdf = 0
    for k in range(-3, 4):  # Sum over wrapping terms
        pdf += np.exp(-0.5 * ((x - mu + 2*np.pi*k) / sigma)**2)
    return pdf / (sigma * np.sqrt(2 * np.pi))

def wrapped_cauchy_pdf(x, mu, gamma):
    """
    Probability density function for wrapped Cauchy distribution.
    
    Parameters:
    x (float): Value
    mu (float): Location parameter
    gamma (float): Scale parameter
    
    Returns:
    float: PDF value
    """
    # Wrapped Cauchy PDF
    return (1 - gamma**2) / (2 * np.pi * (1 + gamma**2 - 2*gamma*np.cos(x - mu)))

def negative_log_likelihood_wrapped_normal(params, errors, non_target_errors):
    """
    Calculate negative log-likelihood for wrapped normal mixture model.
    
    Parameters:
    params (list): Model parameters [sigma, mu, guess_rate, non_target_rate]
    errors (array): Target error data in radians
    non_target_errors (list): List of non-target error arrays for each trial
    
    Returns:
    float: Negative log-likelihood
    """
    sigma, mu, guess_rate, non_target_rate = params
    
    if sigma <= 0 or guess_rate < 0 or non_target_rate < 0 or (guess_rate + non_target_rate) >= 1:
        return np.inf
    
    target_rate = 1 - guess_rate - non_target_rate
    if target_rate <= 0:
        return np.inf
    
    n_trials = len(errors)
    log_likelihood = 0
    
    for i in range(n_trials):
        error = errors[i]
        
        # Target component (wrapped normal)
        target_prob = wrapped_normal_pdf(error, mu, sigma)
        
        # Guess component (uniform)
        guess_prob = 1 / (2 * np.pi)
        
        # Non-target component (wrapped normal centered on non-target locations)
        if len(non_target_errors[i]) > 0:
            non_target_probs = [wrapped_normal_pdf(nt_error, 0, sigma) for nt_error in non_target_errors[i]]
            non_target_prob = np.mean(non_target_probs)
        else:
            non_target_prob = 1 / (2 * np.pi)  # Fallback for set size 1
        
        # Mixture probability
        mixture_prob = (target_rate * target_prob + 
                       guess_rate * guess_prob + 
                       non_target_rate * non_target_prob)
        
        if mixture_prob <= 0:
            return np.inf
        
        log_likelihood += np.log(mixture_prob)
    
    return -log_likelihood

def negative_log_likelihood_wrapped_cauchy(params, errors, non_target_errors):
    """
    Calculate negative log-likelihood for wrapped Cauchy mixture model.
    
    Parameters:
    params (list): Model parameters [gamma, mu, guess_rate, non_target_rate]
    errors (array): Target error data in radians
    non_target_errors (list): List of non-target error arrays for each trial
    
    Returns:
    float: Negative log-likelihood
    """
    gamma, mu, guess_rate, non_target_rate = params
    
    if gamma <= 0 or gamma >= 1 or guess_rate < 0 or non_target_rate < 0 or (guess_rate + non_target_rate) >= 1:
        return np.inf
    
    target_rate = 1 - guess_rate - non_target_rate
    if target_rate <= 0:
        return np.inf
    
    n_trials = len(errors)
    log_likelihood = 0
    
    for i in range(n_trials):
        error = errors[i]
        
        # Target component (wrapped Cauchy)
        target_prob = wrapped_cauchy_pdf(error, mu, gamma)
        
        # Guess component (uniform)
        guess_prob = 1 / (2 * np.pi)
        
        # Non-target component (wrapped Cauchy centered on non-target locations)
        if len(non_target_errors[i]) > 0:
            non_target_probs = [wrapped_cauchy_pdf(nt_error, 0, gamma) for nt_error in non_target_errors[i]]
            non_target_prob = np.mean(non_target_probs)
        else:
            non_target_prob = 1 / (2 * np.pi)  # Fallback for set size 1
        
        # Mixture probability
        mixture_prob = (target_rate * target_prob + 
                       guess_rate * guess_prob + 
                       non_target_rate * non_target_prob)
        
        if mixture_prob <= 0:
            return np.inf
        
        log_likelihood += np.log(mixture_prob)
    
    return -log_likelihood

def fit_alternative_models(errors, non_target_errors):
    """
    Fit wrapped normal and wrapped Cauchy mixture models.
    """
    # Set random seed for reproducibility
    np.random.seed(42)

    results = {}

    # Estimate initial parameters from data (same as von Mises)
    mean_cos = np.mean(np.cos(errors))
    mean_sin = np.mean(np.sin(errors))
    mu_init = np.arctan2(mean_sin, mean_cos)
    large_errors = np.sum(np.abs(errors) > np.pi/2) / len(errors)
    guess_init = min(0.5, max(0.01, large_errors * 0.5))

    # Wrapped Normal Model
    best_result_normal = None
    best_nll_normal = np.inf
    bounds_normal = [(0.01, 20), (-np.pi, np.pi), (0.0, 0.99), (0.0, 0.99)]
    constraint_normal = {'type': 'ineq', 'fun': lambda x: 0.99 - x[2] - x[3]}

    starting_points_normal = [
        [1.0, mu_init, guess_init, 0.05],  # Data-driven
        [0.5, 0.0, 0.1, 0.1],             # Conservative
        [2.0, 0.0, 0.3, 0.1],             # High guess rate
        [5.0, mu_init, 0.15, 0.15],       # Balanced
    ]

    # More diverse random variations
    for _ in range(11):
        starting_points_normal.append([
            np.random.uniform(0.1, 10),
            np.random.uniform(-np.pi, np.pi),
            np.random.uniform(0.0, 0.8),
            np.random.uniform(0.0, 0.5)
        ])

    methods = ['SLSQP', 'L-BFGS-B']

    # Define penalized NLL functions outside the loop to avoid memory leaks
    def penalized_nll_normal(params, errors, non_target_errors):
        nll = negative_log_likelihood_wrapped_normal(params, errors, non_target_errors)
        if params[2] + params[3] >= 0.99:
            nll += 1000 * (params[2] + params[3] - 0.98)**2
        return nll

    for method in methods:
        for start_params in starting_points_normal:
            try:
                # Ensure parameters are within bounds and satisfy constraints
                start_params[0] = max(bounds_normal[0][0], min(bounds_normal[0][1], start_params[0]))
                start_params[1] = max(bounds_normal[1][0], min(bounds_normal[1][1], start_params[1]))
                start_params[2] = max(bounds_normal[2][0], min(bounds_normal[2][1], start_params[2]))
                start_params[3] = max(bounds_normal[3][0], min(bounds_normal[3][1], start_params[3]))

                total_rate = start_params[2] + start_params[3]
                if total_rate >= 0.99:
                    if total_rate > 0:
                        start_params[2] = start_params[2] / total_rate * 0.8
                        start_params[3] = start_params[3] / total_rate * 0.8
                    else:
                        start_params[2] = 0.0
                        start_params[3] = 0.0

                if method == 'L-BFGS-B':
                    result = minimize(
                        penalized_nll_normal,
                        start_params,
                        args=(errors, non_target_errors),
                        bounds=bounds_normal,
                        method=method,
                        options={'maxiter': 2000, 'ftol': 1e-8}
                    )
                else:
                    result = minimize(
                        negative_log_likelihood_wrapped_normal,
                        start_params,
                        args=(errors, non_target_errors),
                        bounds=bounds_normal,
                        constraints=constraint_normal,
                        method=method,
                        options={'maxiter': 2000, 'ftol': 1e-8}
                    )

                if result.success and result.fun < best_nll_normal:
                    sigma, mu, guess_rate, non_target_rate = result.x
                    if (sigma > 0.001 and guess_rate >= 0.0 and non_target_rate >= 0.0 and
                        guess_rate + non_target_rate <= 0.99):
                        best_result_normal = result
                        best_nll_normal = result.fun
            except:
                continue

    if best_result_normal is not None:
        log_likelihood = -best_result_normal.fun
        aic = 2 * 4 - 2 * log_likelihood
        results['wrapped_normal_AIC'] = aic
        results['wrapped_normal_concentration'] = best_result_normal.x[0]  # sigma
    else:
        results['wrapped_normal_AIC'] = np.nan
        results['wrapped_normal_concentration'] = np.nan

    # Wrapped Cauchy Model (similar improvements)
    best_result_cauchy = None
    best_nll_cauchy = np.inf
    bounds_cauchy = [(0.001, 0.999), (-np.pi, np.pi), (0.0, 0.99), (0.0, 0.99)]
    constraint_cauchy = {'type': 'ineq', 'fun': lambda x: 0.99 - x[2] - x[3]}

    starting_points_cauchy = [
        [0.3, mu_init, guess_init, 0.05],  # Data-driven
        [0.1, 0.0, 0.1, 0.1],             # Conservative
        [0.5, 0.0, 0.3, 0.1],             # High guess rate
        [0.7, mu_init, 0.15, 0.15],       # Balanced
    ]

    for _ in range(11):
        starting_points_cauchy.append([
            np.random.uniform(0.01, 0.8),
            np.random.uniform(-np.pi, np.pi),
            np.random.uniform(0.0, 0.8),
            np.random.uniform(0.0, 0.5)
        ])

    def penalized_nll_cauchy(params, errors, non_target_errors):
        nll = negative_log_likelihood_wrapped_cauchy(params, errors, non_target_errors)
        if params[2] + params[3] >= 0.99:
            nll += 1000 * (params[2] + params[3] - 0.98)**2
        return nll

    for method in methods:
        for start_params in starting_points_cauchy:
            try:
                # Ensure parameters are within bounds and satisfy constraints
                start_params[0] = max(bounds_cauchy[0][0], min(bounds_cauchy[0][1], start_params[0]))
                start_params[1] = max(bounds_cauchy[1][0], min(bounds_cauchy[1][1], start_params[1]))
                start_params[2] = max(bounds_cauchy[2][0], min(bounds_cauchy[2][1], start_params[2]))
                start_params[3] = max(bounds_cauchy[3][0], min(bounds_cauchy[3][1], start_params[3]))

                total_rate = start_params[2] + start_params[3]
                if total_rate >= 0.99:
                    if total_rate > 0:
                        start_params[2] = start_params[2] / total_rate * 0.8
                        start_params[3] = start_params[3] / total_rate * 0.8
                    else:
                        start_params[2] = 0.0
                        start_params[3] = 0.0

                if method == 'L-BFGS-B':
                    result = minimize(
                        penalized_nll_cauchy,
                        start_params,
                        args=(errors, non_target_errors),
                        bounds=bounds_cauchy,
                        method=method,
                        options={'maxiter': 2000, 'ftol': 1e-8}
                    )
                else:
                    result = minimize(
                        negative_log_likelihood_wrapped_cauchy,
                        start_params,
                        args=(errors, non_target_errors),
                        bounds=bounds_cauchy,
                        constraints=constraint_cauchy,
                        method=method,
                        options={'maxiter': 2000, 'ftol': 1e-8}
                    )

                if result.success and result.fun < best_nll_cauchy:
                    gamma, mu, guess_rate, non_target_rate = result.x
                    if (gamma > 0.001 and gamma < 0.999 and guess_rate >= 0.0 and 
                        non_target_rate >= 0.0 and guess_rate + non_target_rate <= 0.99):
                        best_result_cauchy = result
                        best_nll_cauchy = result.fun
            except:
                continue

    if best_result_cauchy is not None:
        log_likelihood = -best_result_cauchy.fun
        aic = 2 * 4 - 2 * log_likelihood
        results['wrapped_cauchy_AIC'] = aic
        results['wrapped_cauchy_concentration'] = best_result_cauchy.x[0]  # gamma
    else:
        results['wrapped_cauchy_AIC'] = np.nan
        results['wrapped_cauchy_concentration'] = np.nan

    return results

def main():
    """
    Main function to execute the mixture modeling analysis.
    """
    try:
        print("Starting mixture modeling analysis...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent cleaned trial data file
        print("Searching for input file...")
        input_pattern = 'outputs/cleaned_trial_data_*.csv'
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input file found matching pattern: {input_pattern}")
            return 1
        
        print(f"Found input file: {input_file}")
        
        # Read the input data
        print("Reading input data...")
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded data with shape: {df.shape}")
        except Exception as e:
            print(f"ERROR: Failed to read input file: {e}")
            return 1
        
        # Print column information
        print("\nColumn names in input file:")
        print(df.columns.tolist())
        
        print("\nFirst 3 rows of input data:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = [
            'participantId', 'isPractice', 'VWM_error_degrees', 
            'VWM_targetAngle_degrees', 'VWM_responseAngle_degrees',
            'VWM_orientations_degrees', 'VWM_cueIndex', 'VWM_setSize',
            'VWM_delay_s', 'trial_excluded'
        ]
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found.")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"VWM_setSize unique values: {sorted(df['VWM_setSize'].unique())}")
        print(f"VWM_delay_s unique values: {sorted(df['VWM_delay_s'].unique())}")
        print(f"isPractice unique values: {sorted(df['isPractice'].unique())}")
        print(f"trial_excluded unique values: {sorted(df['trial_excluded'].unique())}")
        
        # Data types for measured variables
        print(f"\nData types for measured variables:")
        print(f"VWM_error_degrees type: {df['VWM_error_degrees'].dtype}")
        print(f"VWM_targetAngle_degrees type: {df['VWM_targetAngle_degrees'].dtype}")
        print(f"VWM_responseAngle_degrees type: {df['VWM_responseAngle_degrees'].dtype}")
        
        # Filter for test trials only and non-excluded trials
        print("\nFiltering data...")
        print(f"Total trials before filtering: {len(df)}")
        
        # Filter for test trials (isPractice=False)
        test_trials = df[df['isPractice'] == False]
        print(f"Test trials (isPractice=False): {len(test_trials)}")
        
        # Filter for non-excluded trials
        valid_trials = test_trials[test_trials['trial_excluded'] == False]
        print(f"Valid trials (trial_excluded=False): {len(valid_trials)}")

        # Explicitly filter for VWM trials with valid error data for modeling
        valid_trials = valid_trials[valid_trials['VWM_error_degrees'].notna()].copy()
        print(f"Valid VWM trials for modeling: {len(valid_trials)}")
        
        if len(valid_trials) == 0:
            print("ERROR: No valid trials found after filtering")
            return 1
        
        print(f"Participants with valid trials: {valid_trials['participantId'].nunique()}")
        
        # Prepare results list
        results = []
        
        # Process each participant
        participants = valid_trials['participantId'].unique()
        print(f"\nProcessing {len(participants)} participants...")
        
        for i, participant_id in enumerate(participants):
            print(f"\nProcessing participant {i+1}/{len(participants)}: {participant_id}")
            
            # Get participant data
            participant_data = valid_trials[valid_trials['participantId'] == participant_id].copy()
            print(f"  Trials for this participant: {len(participant_data)}")
            
            if len(participant_data) < 10:  # Minimum trials for reliable fitting
                print(f"  Skipping participant {participant_id}: insufficient trials ({len(participant_data)})")
                continue
            
            # Convert errors to radians and wrap
            errors_rad = []
            non_target_errors_list = []
            
            for idx, row in participant_data.iterrows():
                # Convert target error to radians and wrap
                error_deg = row['VWM_error_degrees']
                if pd.isna(error_deg):
                    continue
                    
                error_rad = degrees_to_radians(error_deg)
                error_wrapped = wrap_angle(error_rad)
                errors_rad.append(error_wrapped)
                
                # Parse orientations and identify non-target orientations
                orientations_str = row['VWM_orientations_degrees']
                if pd.isna(orientations_str):
                    non_target_errors_list.append([])
                    continue
                
                orientations = parse_orientations(orientations_str)
                cue_index = row['VWM_cueIndex']
                response_angle = row['VWM_responseAngle_degrees']
                
                if len(orientations) == 0 or pd.isna(cue_index) or pd.isna(response_angle):
                    non_target_errors_list.append([])
                    continue
                
                # Remove target orientation (cue_index is 0-based)
                if not pd.isna(cue_index) and 0 <= int(cue_index) < len(orientations):
                    cue_idx = int(cue_index)
                    non_target_orientations = orientations[:cue_idx] + orientations[cue_idx+1:]
                else:
                    non_target_orientations = orientations
                
                # Calculate angular differences to non-target orientations
                non_target_errors = []
                for nt_orientation in non_target_orientations:
                    diff = calculate_angular_difference(response_angle, nt_orientation)
                    non_target_errors.append(diff)
                
                non_target_errors_list.append(non_target_errors)
            
            errors_rad = np.array(errors_rad)
            
            if len(errors_rad) < 10:
                print(f"  Skipping participant {participant_id}: insufficient valid errors ({len(errors_rad)})")
                continue
            
            print(f"  Fitting models with {len(errors_rad)} valid trials...")
            
            # Fit von Mises mixture model
            vonmises_results = fit_mixture_model(errors_rad, non_target_errors_list)
            
            # Fit alternative models
            alternative_results = fit_alternative_models(errors_rad, non_target_errors_list)
            
            # Determine best model based on AIC
            aic_values = {
                'von_mises': vonmises_results['AIC'],
                'wrapped_normal': alternative_results.get('wrapped_normal_AIC', np.nan),
                'wrapped_cauchy': alternative_results.get('wrapped_cauchy_AIC', np.nan)
            }
            
            # Find best model (lowest AIC)
            valid_aics = {k: v for k, v in aic_values.items() if not pd.isna(v)}
            if valid_aics:
                best_model = min(valid_aics, key=valid_aics.get)
                best_aic = valid_aics[best_model]
                vonmises_aic = aic_values['von_mises']
                if not pd.isna(vonmises_aic):
                    aic_difference = best_aic - vonmises_aic
                else:
                    aic_difference = np.nan
            else:
                best_model = 'none'
                aic_difference = np.nan
            
            # Create result row with only the required 15 columns
            result_row = {
                'participantId': participant_id,
                'vonMises_kappa': vonmises_results['vonMises_kappa'],
                'vonMises_mu': vonmises_results['vonMises_mu'],
                'guess_rate': vonmises_results['guess_rate'],
                'non_target_rate': vonmises_results['non_target_rate'],
                'vonMises_AIC': vonmises_results['AIC'],
                'wrapped_normal_AIC': alternative_results.get('wrapped_normal_AIC', np.nan),
                'wrapped_normal_concentration': alternative_results.get('wrapped_normal_concentration', np.nan),
                'wrapped_cauchy_AIC': alternative_results.get('wrapped_cauchy_AIC', np.nan),
                'wrapped_cauchy_concentration': alternative_results.get('wrapped_cauchy_concentration', np.nan),
                'best_model': best_model,
                'AIC_difference': aic_difference,
                'convergence_status': vonmises_results['convergence_status'],
                'log_likelihood': vonmises_results['log_likelihood'],
                'num_trials_fitted': len(errors_rad)
            }

            results.append(result_row)

            print(f"  Results: kappa={vonmises_results['vonMises_kappa']:.3f}, "
                  f"mu={vonmises_results['vonMises_mu']:.3f}, "
                  f"guess_rate={vonmises_results['guess_rate']:.3f}, "
                  f"converged={vonmises_results['convergence_status']}")


        # Create results DataFrame
        if not results:
            print("ERROR: No participants successfully processed")
            return 1

        results_df = pd.DataFrame(results)

        print(f"\nProcessing complete. Results for {len(results_df)} participants.")
        print("\nResults summary:")
        print(f"Converged models: {results_df['convergence_status'].sum()}")
        print(f"Mean kappa: {results_df['vonMises_kappa'].mean():.3f}")
        print(f"Mean guess rate: {results_df['guess_rate'].mean():.3f}")

        print("\nFirst 2 rows of results:")
        print(results_df.head(2))

        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'outputs/mixture_model_parameters_{timestamp}.csv'
        results_df.to_csv(output_file, index=False)

        print(f"\nResults saved to: {output_file}")
        print("Finished execution")
        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
