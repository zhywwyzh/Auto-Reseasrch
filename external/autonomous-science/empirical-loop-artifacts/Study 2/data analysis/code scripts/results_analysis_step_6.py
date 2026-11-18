import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy.optimize import curve_fit
from scipy import stats
import multiprocessing
from functools import partial
import warnings
warnings.filterwarnings('ignore')

# Set up multiprocessing constants
NUM_CORES = min(10, multiprocessing.cpu_count())  # Use up to 10 cores (for M1 Mac)

def create_outputs_folder():
    """
    Create outputs folder if it doesn't exist.
    
    Returns:
        None
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs folder")

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
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found latest file: {latest_file}")
    return latest_file

def dog_function(x, a, w):
    """
    Basic Difference of Gaussians (DoG) function.
    
    Parameters:
        x (array): Angular differences in degrees
        a (float): Amplitude parameter
        w (float): Width parameter
        
    Returns:
        array: DoG function values
    """
    return a * x * np.exp(-(x**2) / (2 * w**2))

def expanded_dog_function(x, a, w, b1, b2, b3, prev_feedback, trial_num, focus_loss):
    """
    Expanded DoG function with covariates.
    
    Parameters:
        x (array): Angular differences in degrees
        a (float): Amplitude parameter
        w (float): Width parameter
        b1 (float): Previous feedback coefficient
        b2 (float): Trial number coefficient
        b3 (float): Focus loss coefficient
        prev_feedback (array): Previous trial feedback values
        trial_num (array): Trial numbers
        focus_loss (array): Focus loss durations
        
    Returns:
        array: Expanded DoG function values
    """
    # Calculate base DoG component
    base_dog = a * x * np.exp(-(x**2) / (2 * w**2))
    
    # Handle potential shape mismatches between x and covariates
    try:
        # First convert any scalar values to arrays
        if np.isscalar(prev_feedback):
            prev_feedback = np.array([prev_feedback])
        if np.isscalar(trial_num):
            trial_num = np.array([trial_num])
        if np.isscalar(focus_loss):
            focus_loss = np.array([focus_loss])
            
        # Check if shapes match
        if len(prev_feedback) != len(x) or len(trial_num) != len(x) or len(focus_loss) != len(x):
            # Broadcast covariates to match x shape if possible
            if len(prev_feedback) == 1:
                prev_feedback = np.repeat(prev_feedback, len(x))
            if len(trial_num) == 1:
                trial_num = np.repeat(trial_num, len(x))
            if len(focus_loss) == 1:
                focus_loss = np.repeat(focus_loss, len(x))
                
            # If still mismatched, truncate or pad arrays
            if len(prev_feedback) != len(x):
                if len(prev_feedback) > len(x):
                    prev_feedback = prev_feedback[:len(x)]
                else:
                    prev_feedback = np.pad(prev_feedback, (0, len(x) - len(prev_feedback)), 'constant', constant_values=np.mean(prev_feedback))
                    
            if len(trial_num) != len(x):
                if len(trial_num) > len(x):
                    trial_num = trial_num[:len(x)]
                else:
                    trial_num = np.pad(trial_num, (0, len(x) - len(trial_num)), 'constant', constant_values=np.mean(trial_num))
                    
            if len(focus_loss) != len(x):
                if len(focus_loss) > len(x):
                    focus_loss = focus_loss[:len(x)]
                else:
                    focus_loss = np.pad(focus_loss, (0, len(x) - len(focus_loss)), 'constant', constant_values=np.mean(focus_loss))
    except TypeError:
        # If arrays are not iterable (e.g., scalars), convert to arrays
        if np.isscalar(prev_feedback):
            prev_feedback = np.repeat(prev_feedback, len(x))
        if np.isscalar(trial_num):
            trial_num = np.repeat(trial_num, len(x))
        if np.isscalar(focus_loss):
            focus_loss = np.repeat(focus_loss, len(x))
    
    # Calculate covariate effects
    covariate_effects = b1 * prev_feedback + b2 * trial_num + b3 * focus_loss
    
    # Return combined effect
    return base_dog + covariate_effects

def _bootstrap_iteration(i, x_data, y_data, weights, covariate_data=None):
    """
    Single bootstrap iteration for parallel processing.
    
    Parameters:
        i (int): Iteration number
        x_data (array): Angular difference values
        y_data (array): Error values
        weights (array): Trial counts for weighting
        covariate_data (dict, optional): Dictionary of covariate arrays for expanded model
        
    Returns:
        tuple: (basic_params, expanded_params) or (None, None) if fitting fails
    """
    if i % 100 == 0:
        print(f"Bootstrap iteration {i}")
        
    # Resample with replacement
    indices = np.random.choice(len(x_data), size=len(x_data), replace=True)
    x_boot = x_data[indices]
    y_boot = y_data[indices]
    w_boot = weights[indices]
    
    basic_params = None
    expanded_params = None
    
    # Basic DoG model bootstrap
    try:
        popt, _ = curve_fit(dog_function, x_boot, y_boot, 
                          p0=[5, 15], sigma=1/np.sqrt(w_boot),
                          bounds=([0, 1], [50, 100]))
        basic_params = popt
        
        # Expanded DoG model bootstrap (if covariates provided)
        if covariate_data is not None:
            # Get covariates that are already aggregated to match x_data length
            feedback_values = covariate_data.get('feedback_values', None)
            trial_num_values = covariate_data.get('trial_num_values', None)
            focus_loss_values = covariate_data.get('focus_loss_values', None)
                
            # Resample covariates - ensure they match the resampled x_data length
            if feedback_values is not None and len(feedback_values) == len(x_data):
                feedback_boot = feedback_values[indices]
                trial_num_boot = trial_num_values[indices]
                focus_loss_boot = focus_loss_values[indices]
            else:
                # Fallback: use mean values if shapes don't match
                feedback_values_raw = covariate_data.get('feedback_values_raw', None)
                trial_num_values_raw = covariate_data.get('trial_num_values_raw', None)
                focus_loss_values_raw = covariate_data.get('focus_loss_values_raw', None)
                    
                # Check if raw values exist before using them
                if feedback_values_raw is not None and len(feedback_values_raw) > 0:
                    feedback_mean = np.mean(np.nan_to_num(feedback_values_raw))
                else:
                    feedback_mean = 0
                        
                if trial_num_values_raw is not None and len(trial_num_values_raw) > 0:
                    trial_num_mean = np.mean(np.nan_to_num(trial_num_values_raw))
                else:
                    trial_num_mean = 0
                        
                if focus_loss_values_raw is not None and len(focus_loss_values_raw) > 0:
                    focus_loss_mean = np.mean(np.nan_to_num(focus_loss_values_raw))
                else:
                    focus_loss_mean = 0
                    
                # Aggregate to match the resampled x_boot length
                feedback_boot = np.repeat(feedback_mean, len(x_boot))
                trial_num_boot = np.repeat(trial_num_mean, len(x_boot))
                focus_loss_boot = np.repeat(focus_loss_mean, len(x_boot))
                
            # Create lambda for expanded model
            expanded_fit_func = lambda x, a, w, b1, b2, b3: expanded_dog_function(
                x, a, w, b1, b2, b3, 
                feedback_boot, trial_num_boot, focus_loss_boot
            )
            
            # Fit expanded model
            popt_expanded, _ = curve_fit(
                expanded_fit_func, x_boot, y_boot, 
                p0=[popt[0], popt[1], 0, 0, 0], 
                sigma=1/np.sqrt(w_boot),
                bounds=([0, 1, -10, -10, -10], [50, 100, 10, 10, 10])
            )
            expanded_params = popt_expanded
    except Exception as e:
        pass
    
    return (basic_params, expanded_params)

def bootstrap_dog_fit(x_data, y_data, weights, covariate_data=None, n_bootstrap=1000):
    """
    Bootstrap DoG parameter estimation with confidence intervals using parallel processing.
    
    Parameters:
        x_data (array): Angular difference values
        y_data (array): Error values
        weights (array): Trial counts for weighting
        covariate_data (dict, optional): Dictionary of covariate arrays for expanded model
        n_bootstrap (int): Number of bootstrap samples
        
    Returns:
        dict: Bootstrap results with parameter estimates and confidence intervals
    """
    print(f"Starting bootstrap with {n_bootstrap} samples using {NUM_CORES} CPU cores...")
    
    use_expanded_model = covariate_data is not None
    if use_expanded_model:
        print("Bootstrapping both basic and expanded DoG models in parallel...")
    
    # Create a partial function with fixed parameters
    bootstrap_func = partial(_bootstrap_iteration, 
                            x_data=x_data, 
                            y_data=y_data, 
                            weights=weights, 
                            covariate_data=covariate_data)
    
    # Run bootstrap iterations in parallel
    try:
        with multiprocessing.Pool(processes=NUM_CORES) as pool:
            results = pool.map(bootstrap_func, range(n_bootstrap))
    except Exception as e:
        print(f"Parallel processing failed: {str(e)}. Falling back to sequential processing.")
        # Fall back to sequential processing if parallel fails
        results = [bootstrap_func(i) for i in range(n_bootstrap)]
    
    # Extract results
    bootstrap_params = []
    bootstrap_expanded_params = []
    
    for basic_params, expanded_params in results:
        if basic_params is not None:
            bootstrap_params.append(basic_params)
        if expanded_params is not None:
            bootstrap_expanded_params.append(expanded_params)
    
    if len(bootstrap_params) == 0:
        print("Warning: All bootstrap iterations failed for basic model")
        return None
    
    bootstrap_params = np.array(bootstrap_params)
    
    # Calculate confidence intervals for basic model
    amplitude_ci = np.percentile(bootstrap_params[:, 0], [2.5, 97.5])
    width_ci = np.percentile(bootstrap_params[:, 1], [2.5, 97.5])
    
    # Calculate zero crossing for each bootstrap sample
    zero_crossings = bootstrap_params[:, 1] * np.sqrt(2)
    zero_crossing_ci = np.percentile(zero_crossings, [2.5, 97.5])
    
    print(f"Completed {len(bootstrap_params)}/{n_bootstrap} valid basic model bootstrap samples")
    
    result = {
        'amplitude_ci': amplitude_ci,
        'width_ci': width_ci,
        'zero_crossing_ci': zero_crossing_ci,
        'bootstrap_samples_completed': len(bootstrap_params),
        'bootstrap_success_rate': (len(bootstrap_params) / n_bootstrap) * 100
    }
    
    # Add expanded model confidence intervals if available
    if use_expanded_model and len(bootstrap_expanded_params) > 0:
        bootstrap_expanded_params = np.array(bootstrap_expanded_params)
        
        expanded_amplitude_ci = np.percentile(bootstrap_expanded_params[:, 0], [2.5, 97.5])
        expanded_width_ci = np.percentile(bootstrap_expanded_params[:, 1], [2.5, 97.5])
        expanded_zero_crossings = bootstrap_expanded_params[:, 1] * np.sqrt(2)
        expanded_zero_crossing_ci = np.percentile(expanded_zero_crossings, [2.5, 97.5])
        
        # Covariate parameter CIs
        b1_ci = np.percentile(bootstrap_expanded_params[:, 2], [2.5, 97.5])
        b2_ci = np.percentile(bootstrap_expanded_params[:, 3], [2.5, 97.5])
        b3_ci = np.percentile(bootstrap_expanded_params[:, 4], [2.5, 97.5])
        
        result.update({
            'expanded_amplitude_ci': expanded_amplitude_ci,
            'expanded_width_ci': expanded_width_ci,
            'expanded_zero_crossing_ci': expanded_zero_crossing_ci,
            'b1_ci': b1_ci,
            'b2_ci': b2_ci,
            'b3_ci': b3_ci,
            'expanded_bootstrap_samples_completed': len(bootstrap_expanded_params),
            'expanded_bootstrap_success_rate': (len(bootstrap_expanded_params) / n_bootstrap) * 100
        })
        
        print(f"Completed {len(bootstrap_expanded_params)}/{n_bootstrap} valid expanded model bootstrap samples")
    elif use_expanded_model:
        print("Warning: All bootstrap iterations failed for expanded model")
    
    return result

def process_covariates(cleaned_data_subset):
    """
    Process covariate data for expanded DoG model fitting.
    
    Parameters:
        cleaned_data_subset (DataFrame): Cleaned trial data for covariates
        
    Returns:
        DataFrame: Processed data with numeric covariates
    """
    # Create a copy to avoid modifying the original
    processed_data = cleaned_data_subset.copy()
    
    # Convert feedback to numeric values
    feedback_map = {'Good': 1, 'Ok': 0, 'Poor': -1}
    processed_data['feedback_numeric'] = processed_data['previous_trial_feedback'].map(feedback_map).fillna(0)
    
    # Extract seconds from ISO 8601 duration format
    if 'windowFocusLostDuringTasksDuration' in processed_data.columns:
        processed_data['focus_loss_seconds'] = processed_data['windowFocusLostDuringTasksDuration'].astype(str).str.extract(r'PT([\d.]+)S')[0].astype(float).fillna(0)
    else:
        processed_data['focus_loss_seconds'] = 0
    
    print(f"Processed covariates: feedback_numeric range: {processed_data['feedback_numeric'].min()} to {processed_data['feedback_numeric'].max()}")
    print(f"Processed covariates: focus_loss_seconds range: {processed_data['focus_loss_seconds'].min()} to {processed_data['focus_loss_seconds'].max()}")
    
    return processed_data

def fit_dog_model(participant_data, cleaned_data_subset):
    """
    Fit DoG model to participant data for a specific condition.
    
    Parameters:
        participant_data (DataFrame): Binned data for participant-condition
        cleaned_data_subset (DataFrame): Cleaned trial data for covariates
        
    Returns:
        dict: Fitting results including parameters and statistics
    """
    # Filter for adequate bins
    adequate_data = participant_data[participant_data['bin_adequate'] == True].copy()
    
    if len(adequate_data) < 4:
        return {
            'fit_converged': False,
            'exclusion_reason': 'Insufficient adequate bins (< 4)'
        }
    
    x_data = adequate_data['bin_center_degrees'].values
    y_data = adequate_data['mean_error_degrees'].values
    weights = adequate_data['n_trials_in_bin'].values
    
    # Remove any NaN values
    valid_mask = ~(np.isnan(x_data) | np.isnan(y_data) | np.isnan(weights))
    x_data = x_data[valid_mask]
    y_data = y_data[valid_mask]
    weights = weights[valid_mask]
    
    if len(x_data) < 4:
        return {
            'fit_converged': False,
            'exclusion_reason': 'Insufficient valid data points after NaN removal'
        }
    
    try:
        # Basic DoG fit
        popt, pcov = curve_fit(dog_function, x_data, y_data, 
                              p0=[5, 15], sigma=1/np.sqrt(weights),
                              bounds=([0, 1], [50, 100]))
        
        amplitude, width = popt
        zero_crossing = width * np.sqrt(2)
        
        # Calculate R-squared
        y_pred = dog_function(x_data, amplitude, width)
        ss_res = np.sum((y_data - y_pred) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Process covariates for this participant-condition
        print(f"Filtering covariate data for participant {participant_data['participantId'].iloc[0]}, condition: {participant_data['condition_label'].iloc[0]}")
        
        condition_data = cleaned_data_subset[
            (cleaned_data_subset['VWM_setSize'] == participant_data['VWM_setSize'].iloc[0]) &
            (cleaned_data_subset['VWM_delay_s'] == participant_data['VWM_delay_s'].iloc[0])
        ]
        
        # Validate that we have sufficient covariate data
        if len(condition_data) < 5:  # Minimum threshold for meaningful covariate analysis
            print(f"WARNING: Insufficient covariate data for participant {participant_data['participantId'].iloc[0]}, condition: {participant_data['condition_label'].iloc[0]}")
            print(f"Found only {len(condition_data)} trials, minimum 5 required for expanded model")
            
            # Create empty covariate data with same length as x_data
            feedback_values = np.zeros(len(x_data))
            trial_num_values = np.zeros(len(x_data))
            focus_loss_values = np.zeros(len(x_data))
            
            covariate_data_valid = False
            print("Will attempt basic DoG model only")
        else:
            # Process covariates to numeric format
            processed_covariates = process_covariates(condition_data)
            
            # Check for required columns
            required_cols = ['feedback_numeric', 'VWM_trial', 'focus_loss_seconds']
            missing_cols = [col for col in required_cols if col not in processed_covariates.columns]
            
            if missing_cols:
                print(f"WARNING: Missing required covariate columns: {missing_cols}")
                # Create empty covariate data with same length as x_data
                feedback_values = np.zeros(len(x_data))
                trial_num_values = np.zeros(len(x_data))
                focus_loss_values = np.zeros(len(x_data))
                covariate_data_valid = False
            else:
                # Extract covariate data
                feedback_values_raw = processed_covariates['feedback_numeric'].values
                trial_num_values_raw = processed_covariates['VWM_trial'].fillna(0).values
                focus_loss_values_raw = processed_covariates['focus_loss_seconds'].values
                
                # Check for all zeros or NaNs which would make fitting unstable
                # First replace any NaNs with zeros to avoid comparison issues
                feedback_clean = np.nan_to_num(feedback_values_raw)
                trial_num_clean = np.nan_to_num(trial_num_values_raw)
                focus_loss_clean = np.nan_to_num(focus_loss_values_raw)
                
                if (np.all(feedback_clean == 0) and np.all(trial_num_clean == 0) and 
                    np.all(focus_loss_clean == 0)):
                    print("WARNING: All covariate values are zero, expanded model may be unstable")
                    covariate_data_valid = False
                else:
                    covariate_data_valid = True
                
                # Implement more sophisticated bin-level aggregation for covariates
                print(f"Implementing bin-level covariate aggregation (x_data length: {len(x_data)})")
                
                # First, check if we can link trials to bins using angular difference
                if 'angular_difference_current_previous' in processed_covariates.columns:
                    print("Using angular_difference_current_previous to map trials to bins")
                    
                    # Create bin mapping from adequate_data
                    bin_mapping = {}
                    for i, row in adequate_data.iterrows():
                        # Check if bin_lower_bound exists as a column and the value is not NaN
                        if 'bin_lower_bound' in adequate_data.columns and not pd.isna(row.get('bin_lower_bound')):
                            bin_lower = row['bin_lower_bound']
                        else:
                            bin_lower = row['bin_center_degrees'] - 5
                            
                        # Check if bin_upper_bound exists as a column and the value is not NaN
                        if 'bin_upper_bound' in adequate_data.columns and not pd.isna(row.get('bin_upper_bound')):
                            bin_upper = row['bin_upper_bound']
                        else:
                            bin_upper = row['bin_center_degrees'] + 5
                            
                        bin_mapping[row['bin_center_degrees']] = (bin_lower, bin_upper)
                    
                    # Initialize arrays for bin-level covariates
                    feedback_values = np.zeros(len(x_data))
                    trial_num_values = np.zeros(len(x_data))
                    focus_loss_values = np.zeros(len(x_data))
                    
                    # Map trials to bins and compute mean covariate values per bin
                    for i, bin_center in enumerate(x_data):
                        bin_lower, bin_upper = bin_mapping[bin_center]
                        
                        # Find trials that fall within this bin
                        bin_trials = processed_covariates[
                            (processed_covariates['angular_difference_current_previous'] >= bin_lower) & 
                            (processed_covariates['angular_difference_current_previous'] < bin_upper)
                        ]
                        
                        if len(bin_trials) > 0:
                            feedback_values[i] = bin_trials['feedback_numeric'].mean()
                            trial_num_values[i] = bin_trials['VWM_trial'].mean()
                            focus_loss_values[i] = bin_trials['focus_loss_seconds'].mean()
                            print(f"Bin {i+1}/{len(x_data)} (center={bin_center:.1f}°): {len(bin_trials)} trials mapped")
                        else:
                            # If no trials in this bin, use global means
                            feedback_values[i] = np.mean(feedback_clean)
                            trial_num_values[i] = np.mean(trial_num_clean)
                            focus_loss_values[i] = np.mean(focus_loss_clean)
                            print(f"Bin {i+1}/{len(x_data)} (center={bin_center:.1f}°): No trials mapped, using global means")
                else:
                    print("No angular_difference_current_previous column found, using global means for covariates")
                    # Fall back to simple approach: use mean values for each covariate
                    feedback_values = np.repeat(np.mean(feedback_clean), len(x_data))
                    trial_num_values = np.repeat(np.mean(trial_num_clean), len(x_data))
                    focus_loss_values = np.repeat(np.mean(focus_loss_clean), len(x_data))
                
                # Replace any NaNs that might have been introduced
                feedback_values = np.nan_to_num(feedback_values)
                trial_num_values = np.nan_to_num(trial_num_values)
                focus_loss_values = np.nan_to_num(focus_loss_values)
                
                print(f"Aggregated covariate shapes: feedback={feedback_values.shape}, trial_num={trial_num_values.shape}, focus_loss={focus_loss_values.shape}")
                print(f"Bin-level feedback range: {np.min(feedback_values):.2f} to {np.max(feedback_values):.2f}")
                print(f"Bin-level trial_num range: {np.min(trial_num_values):.2f} to {np.max(trial_num_values):.2f}")
                print(f"Bin-level focus_loss range: {np.min(focus_loss_values):.2f} to {np.max(focus_loss_values):.2f}")
                    
                # Verify no NaN values
                if (np.any(np.isnan(feedback_values)) or np.any(np.isnan(trial_num_values)) or 
                    np.any(np.isnan(focus_loss_values))):
                    print("WARNING: NaN values found in covariates, replacing with zeros")
                    feedback_values = np.nan_to_num(feedback_values)
                    trial_num_values = np.nan_to_num(trial_num_values)
                    focus_loss_values = np.nan_to_num(focus_loss_values)
        
        # Print covariate statistics
        print(f"Covariate data prepared: {len(condition_data)} trials for expanded model")
        print(f"Feedback values range: {np.min(feedback_values)} to {np.max(feedback_values)}")
        print(f"Trial numbers range: {np.min(trial_num_values)} to {np.max(trial_num_values)}")
        print(f"Focus loss range: {np.min(focus_loss_values)} to {np.max(focus_loss_values)}")
        print(f"Covariate data valid for expanded model: {covariate_data_valid}")
        
        # Prepare covariate data for bootstrap
        covariate_data = None
        if covariate_data_valid:
            # Store both raw and aggregated values
            covariate_data = {
                'feedback_values': feedback_values,  # Already aggregated to match x_data
                'trial_num_values': trial_num_values,
                'focus_loss_values': focus_loss_values,
                'feedback_values_raw': feedback_values_raw,  # Original trial-level data
                'trial_num_values_raw': trial_num_values_raw,
                'focus_loss_values_raw': focus_loss_values_raw
            }
            print(f"Prepared covariate data for bootstrap with shapes matching x_data ({len(x_data)})")
            
        # Bootstrap confidence intervals
        bootstrap_results = bootstrap_dog_fit(x_data, y_data, weights, covariate_data)
        
        # Fit expanded model with covariates
        try:
            # Verify shapes match before fitting
            if len(feedback_values) != len(x_data) or len(trial_num_values) != len(x_data) or len(focus_loss_values) != len(x_data):
                print(f"ERROR: Shape mismatch detected. x_data: {len(x_data)}, feedback: {len(feedback_values)}, trial_num: {len(trial_num_values)}, focus_loss: {len(focus_loss_values)}")
                # Re-aggregate to ensure shapes match
                feedback_values = np.repeat(np.mean(np.nan_to_num(feedback_values_raw)), len(x_data))
                trial_num_values = np.repeat(np.mean(np.nan_to_num(trial_num_values_raw)), len(x_data))
                focus_loss_values = np.repeat(np.mean(np.nan_to_num(focus_loss_values_raw)), len(x_data))
                print(f"Re-aggregated covariate shapes: feedback={feedback_values.shape}, trial_num={trial_num_values.shape}, focus_loss={focus_loss_values.shape}")
            
            # Verify no NaN or inf values in any arrays
            if (np.any(np.isnan(x_data)) or np.any(np.isnan(y_data)) or 
                np.any(np.isnan(feedback_values)) or np.any(np.isnan(trial_num_values)) or 
                np.any(np.isnan(focus_loss_values)) or
                np.any(np.isinf(x_data)) or np.any(np.isinf(y_data)) or 
                np.any(np.isinf(feedback_values)) or np.any(np.isinf(trial_num_values)) or 
                np.any(np.isinf(focus_loss_values))):
                
                print("WARNING: NaN or inf values detected in input arrays, replacing with zeros")
                x_data = np.nan_to_num(x_data)
                y_data = np.nan_to_num(y_data)
                feedback_values = np.nan_to_num(feedback_values)
                trial_num_values = np.nan_to_num(trial_num_values)
                focus_loss_values = np.nan_to_num(focus_loss_values)
            
            # Create a lambda function to handle the expanded model with covariates
            expanded_fit_func = lambda x, a, w, b1, b2, b3: expanded_dog_function(
                x, a, w, b1, b2, b3, 
                feedback_values, trial_num_values, focus_loss_values
            )
            
            # Initial parameters: start with basic DoG parameters plus zeros for covariates
            p0_expanded = [amplitude, width, 0, 0, 0]
            
            # Bounds for parameters
            bounds_expanded = ([0, 1, -10, -10, -10], [50, 100, 10, 10, 10])
            
            print(f"Fitting expanded DoG model with covariates...")
            print(f"Input shapes: x_data={x_data.shape}, y_data={y_data.shape}, feedback={feedback_values.shape}")
            
            # Test the expanded function with initial parameters before fitting
            try:
                test_output = expanded_fit_func(x_data, *p0_expanded)
                print(f"Expanded function test successful, output shape: {test_output.shape}")
            except Exception as test_e:
                print(f"WARNING: Expanded function test failed: {str(test_e)}")
                print("Attempting to fix function inputs...")
                
                # Last resort: ensure all arrays are exactly the same length and type
                min_len = min(len(x_data), len(y_data))
                x_data = x_data[:min_len].astype(np.float64)
                y_data = y_data[:min_len].astype(np.float64)
                feedback_values = np.repeat(np.mean(feedback_values), min_len).astype(np.float64)
                trial_num_values = np.repeat(np.mean(trial_num_values), min_len).astype(np.float64)
                focus_loss_values = np.repeat(np.mean(focus_loss_values), min_len).astype(np.float64)
                
                # Update the lambda function with fixed arrays
                expanded_fit_func = lambda x, a, w, b1, b2, b3: expanded_dog_function(
                    x, a, w, b1, b2, b3, 
                    feedback_values, trial_num_values, focus_loss_values
                )
                
                # Test again
                try:
                    test_output = expanded_fit_func(x_data, *p0_expanded)
                    print(f"Fixed expanded function test successful, output shape: {test_output.shape}")
                except Exception as retest_e:
                    raise Exception(f"Could not fix expanded function: {str(retest_e)}")
            
            popt_expanded, _ = curve_fit(
                expanded_fit_func, x_data, y_data, 
                p0=p0_expanded, sigma=1/np.sqrt(weights),
                bounds=bounds_expanded
            )
            
            expanded_amplitude, expanded_width, b1, b2, b3 = popt_expanded
            expanded_zero_crossing = expanded_width * np.sqrt(2)
            
            print(f"Expanded model fit successful: amplitude={expanded_amplitude:.2f}, width={expanded_width:.2f}")
            print(f"Covariate coefficients: b1={b1:.4f}, b2={b2:.4f}, b3={b3:.4f}")
            
            # Calculate R-squared for expanded model
            y_pred_expanded = expanded_fit_func(x_data, *popt_expanded)
            ss_res_expanded = np.sum((y_data - y_pred_expanded) ** 2)
            r_squared_expanded = 1 - (ss_res_expanded / ss_tot) if ss_tot > 0 else 0
            
            # Calculate improvement over basic model
            r_squared_improvement = r_squared_expanded - r_squared
            
            print(f"Expanded model R² = {r_squared_expanded:.4f} (improvement over basic model: {r_squared_improvement:.4f})")
            
            # Calculate AIC for model comparison
            n = len(x_data)
            k_basic = 2  # Number of parameters in basic model
            k_expanded = 5  # Number of parameters in expanded model
            
            # Ensure residual sum of squares is positive to avoid log of negative number
            ss_res_safe = max(ss_res, np.finfo(float).eps)
            ss_res_expanded_safe = max(ss_res_expanded, np.finfo(float).eps)
            
            aic_basic = n * np.log(ss_res_safe / n) + 2 * k_basic
            aic_expanded = n * np.log(ss_res_expanded_safe / n) + 2 * k_expanded
            
            # Calculate BIC
            bic_basic = n * np.log(ss_res_safe / n) + k_basic * np.log(n)
            bic_expanded = n * np.log(ss_res_expanded_safe / n) + k_expanded * np.log(n)
            
            print(f"Model comparison - Basic model: AIC={aic_basic:.2f}, BIC={bic_basic:.2f}")
            print(f"Model comparison - Expanded model: AIC={aic_expanded:.2f}, BIC={bic_expanded:.2f}")
            
            # Interpret covariate effects
            print("Covariate effect interpretation:")
            print(f"  Previous feedback (b1={b1:.4f}): {'Significant' if abs(b1) > 0.1 else 'Non-significant'}")
            print(f"  Trial number (b2={b2:.4f}): {'Significant' if abs(b2) > 0.1 else 'Non-significant'}")
            print(f"  Focus loss (b3={b3:.4f}): {'Significant' if abs(b3) > 0.1 else 'Non-significant'}")
            
            expanded_fit_converged = True
            expanded_fit_error = ""
            
            # Store additional metrics
            expanded_model_metrics = {
                'r_squared_improvement': r_squared_improvement,
                'aic_basic': aic_basic,
                'aic_expanded': aic_expanded,
                'bic_basic': bic_basic,
                'bic_expanded': bic_expanded
            }
            
        except Exception as e:
            print(f"Expanded model fitting failed: {str(e)}")
            # Fall back to basic model parameters if expanded model fails
            expanded_amplitude = amplitude
            expanded_width = width
            expanded_zero_crossing = zero_crossing
            b1, b2, b3 = 0, 0, 0
            r_squared_expanded = r_squared
            expanded_fit_converged = False
            expanded_fit_error = str(e)
        
        result = {
            'fit_converged': True,
            'amplitude': amplitude,
            'width': width,
            'zero_crossing': zero_crossing,
            'r_squared': r_squared,
            'expanded_model_amplitude': expanded_amplitude,
            'expanded_model_width': expanded_width,
            'expanded_model_zero_crossing': expanded_zero_crossing,
            'expanded_model_r_squared': r_squared_expanded,
            'expanded_model_converged': expanded_fit_converged,
            'expanded_model_b1': b1 if expanded_fit_converged else np.nan,
            'expanded_model_b2': b2 if expanded_fit_converged else np.nan,
            'expanded_model_b3': b3 if expanded_fit_converged else np.nan,
            'exclusion_reason': ''
        }
        
        if bootstrap_results:
            # Basic model confidence intervals
            result.update({
                'amplitude_ci_lower': bootstrap_results['amplitude_ci'][0],
                'amplitude_ci_upper': bootstrap_results['amplitude_ci'][1],
                'width_ci_lower': bootstrap_results['width_ci'][0],
                'width_ci_upper': bootstrap_results['width_ci'][1],
                'zero_crossing_ci_lower': bootstrap_results['zero_crossing_ci'][0],
                'zero_crossing_ci_upper': bootstrap_results['zero_crossing_ci'][1],
                'bootstrap_success_rate': bootstrap_results.get('bootstrap_success_rate', np.nan)
            })
            
            # Expanded model confidence intervals if available
            if 'expanded_amplitude_ci' in bootstrap_results:
                result.update({
                    'expanded_model_amplitude_ci_lower': bootstrap_results['expanded_amplitude_ci'][0],
                    'expanded_model_amplitude_ci_upper': bootstrap_results['expanded_amplitude_ci'][1],
                    'expanded_model_width_ci_lower': bootstrap_results['expanded_width_ci'][0],
                    'expanded_model_width_ci_upper': bootstrap_results['expanded_width_ci'][1],
                    'expanded_model_zero_crossing_ci_lower': bootstrap_results['expanded_zero_crossing_ci'][0],
                    'expanded_model_zero_crossing_ci_upper': bootstrap_results['expanded_zero_crossing_ci'][1],
                    'expanded_model_b1_ci_lower': bootstrap_results['b1_ci'][0],
                    'expanded_model_b1_ci_upper': bootstrap_results['b1_ci'][1],
                    'expanded_model_b2_ci_lower': bootstrap_results['b2_ci'][0],
                    'expanded_model_b2_ci_upper': bootstrap_results['b2_ci'][1],
                    'expanded_model_b3_ci_lower': bootstrap_results['b3_ci'][0],
                    'expanded_model_b3_ci_upper': bootstrap_results['b3_ci'][1],
                    'expanded_bootstrap_success_rate': bootstrap_results.get('expanded_bootstrap_success_rate', np.nan)
                })
            else:
                # Fill with NaN if expanded model bootstrap failed
                result.update({
                    'expanded_model_amplitude_ci_lower': np.nan,
                    'expanded_model_amplitude_ci_upper': np.nan,
                    'expanded_model_width_ci_lower': np.nan,
                    'expanded_model_width_ci_upper': np.nan,
                    'expanded_model_zero_crossing_ci_lower': np.nan,
                    'expanded_model_zero_crossing_ci_upper': np.nan,
                    'expanded_model_b1_ci_lower': np.nan,
                    'expanded_model_b1_ci_upper': np.nan,
                    'expanded_model_b2_ci_lower': np.nan,
                    'expanded_model_b2_ci_upper': np.nan,
                    'expanded_model_b3_ci_lower': np.nan,
                    'expanded_model_b3_ci_upper': np.nan,
                    'expanded_bootstrap_success_rate': 0.0
                })
        else:
            # Fill with NaN if all bootstrap failed
            result.update({
                'amplitude_ci_lower': np.nan,
                'amplitude_ci_upper': np.nan,
                'width_ci_lower': np.nan,
                'width_ci_upper': np.nan,
                'zero_crossing_ci_lower': np.nan,
                'zero_crossing_ci_upper': np.nan,
                'bootstrap_success_rate': 0.0,
                'expanded_model_amplitude_ci_lower': np.nan,
                'expanded_model_amplitude_ci_upper': np.nan,
                'expanded_model_width_ci_lower': np.nan,
                'expanded_model_width_ci_upper': np.nan,
                'expanded_model_zero_crossing_ci_lower': np.nan,
                'expanded_model_zero_crossing_ci_upper': np.nan,
                'expanded_model_b1_ci_lower': np.nan,
                'expanded_model_b1_ci_upper': np.nan,
                'expanded_model_b2_ci_lower': np.nan,
                'expanded_model_b2_ci_upper': np.nan,
                'expanded_model_b3_ci_lower': np.nan,
                'expanded_model_b3_ci_upper': np.nan,
                'expanded_bootstrap_success_rate': 0.0
            })
        
        return result
        
    except Exception as e:
        print(f"Fitting failed: {str(e)}")
        return {
            'fit_converged': False,
            'exclusion_reason': f'Fitting algorithm failed: {str(e)}'
        }

def check_extreme_parameters(df, param_cols):
    """
    Identify participants with extreme parameter estimates (>5 SD from mean).
    
    Parameters:
        df (DataFrame): Results dataframe
        param_cols (list): Parameter column names to check
        
    Returns:
        DataFrame: Updated dataframe with exclusion flags
    """
    print("Checking for extreme parameter estimates...")
    
    for col in param_cols:
        if col in df.columns:
            valid_data = df[df['fit_converged'] == True][col]
            if len(valid_data) > 0:
                mean_val = valid_data.mean()
                std_val = valid_data.std()
                
                if std_val > 0:
                    z_scores = np.abs((df[col] - mean_val) / std_val)
                    extreme_mask = (z_scores > 5) & (df['fit_converged'] == True)
                    
                    df.loc[extreme_mask, 'excluded_fitting'] = True
                    df.loc[extreme_mask, 'exclusion_reason_fitting'] = f'Extreme {col} parameter (>5 SD)'
                    
                    print(f"Found {extreme_mask.sum()} extreme values for {col}")
    
    return df

def main():
    """
    Main function to execute DoG parameter fitting analysis.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM DoG parameter fitting analysis...")
        
        # Create outputs folder
        create_outputs_folder()
        
        # Find input files
        print("Looking for input files...")
        
        binned_pattern = "outputs/VWM_binned_for_DoG_*.csv"
        binned_file = find_latest_file(binned_pattern)
        
        cleaned_pattern = "outputs/VWM_cleaned_data_*.csv"
        cleaned_file = find_latest_file(cleaned_pattern)
        
        if not binned_file:
            print(f"Error: No binned data file found matching pattern {binned_pattern}")
            return 1
            
        if not cleaned_file:
            print(f"Error: No cleaned data file found matching pattern {cleaned_pattern}")
            return 1
        
        # Load data
        print(f"Loading binned data from: {binned_file}")
        binned_df = pd.read_csv(binned_file)
        
        print(f"Loading cleaned data from: {cleaned_file}")
        cleaned_df = pd.read_csv(cleaned_file)
        
        # Print data structure
        print("\nBinned data columns:")
        print(binned_df.columns.tolist())
        print("\nFirst 3 rows of binned data:")
        print(binned_df.head(3))
        
        print("\nCleaned data columns:")
        print(cleaned_df.columns.tolist())
        print("\nFirst 3 rows of cleaned data:")
        print(cleaned_df.head(3))
        
        # Check required columns
        required_binned_cols = ['participantId', 'VWM_setSize', 'VWM_delay_s', 
                               'bin_center_degrees', 'mean_error_degrees', 
                               'n_trials_in_bin', 'bin_adequate', 'condition_label']
        
        required_cleaned_cols = ['participantId', 'trial_type', 'previous_trial_feedback',
                               'VWM_trial', 'windowFocusLostDuringTasksDuration']
        
        missing_binned = [col for col in required_binned_cols if col not in binned_df.columns]
        missing_cleaned = [col for col in required_cleaned_cols if col not in cleaned_df.columns]
        
        if missing_binned:
            print(f"Error: Missing required columns in binned data: {missing_binned}")
            return 1
            
        if missing_cleaned:
            print(f"Error: Missing required columns in cleaned data: {missing_cleaned}")
            return 1
        
        # Print unique values for key experimental parameters
        print("\nUnique values in key experimental parameters:")
        print(f"VWM_setSize: {sorted(binned_df['VWM_setSize'].unique())}")
        print(f"VWM_delay_s: {sorted(binned_df['VWM_delay_s'].unique())}")
        print(f"condition_label: {sorted(binned_df['condition_label'].unique())}")
        print(f"bin_adequate: {sorted(binned_df['bin_adequate'].unique())}")
        
        if 'previous_trial_feedback' in cleaned_df.columns:
            print(f"previous_trial_feedback: {sorted(cleaned_df['previous_trial_feedback'].dropna().unique())}")
        
        # Remove null values from key columns
        print("\nFiltering out null values...")
        
        # For binned data
        initial_binned_count = len(binned_df)
        binned_df = binned_df.dropna(subset=['participantId', 'VWM_setSize', 'VWM_delay_s', 
                                           'bin_center_degrees', 'mean_error_degrees', 
                                           'n_trials_in_bin', 'bin_adequate'])
        final_binned_count = len(binned_df)
        print(f"Binned data: {initial_binned_count} -> {final_binned_count} rows after removing nulls")
        
        # For cleaned data
        initial_cleaned_count = len(cleaned_df)
        cleaned_df = cleaned_df.dropna(subset=['participantId'])
        final_cleaned_count = len(cleaned_df)
        print(f"Cleaned data: {initial_cleaned_count} -> {final_cleaned_count} rows after removing nulls")
        
        # Initialize results list
        results = []
        exclusion_log = []
        
        # Get unique participant-condition combinations
        conditions = binned_df.groupby(['participantId', 'VWM_setSize', 'VWM_delay_s', 'condition_label'])
        
        print(f"\nProcessing {len(conditions)} participant-condition combinations...")
        
        total_assessed = 0
        fitting_failures = 0
        insufficient_bins = 0
        
        for (participant_id, set_size, delay, condition_label), group_data in conditions:
            total_assessed += 1
            
            if total_assessed % 10 == 0:
                print(f"Processing combination {total_assessed}/{len(conditions)}")
            
            # Get corresponding cleaned data for covariates
            participant_cleaned = cleaned_df[cleaned_df['participantId'] == participant_id]
            
            # Fit DoG model
            fit_result = fit_dog_model(group_data, participant_cleaned)
            
            # Create result row
            result_row = {
                'participantId': participant_id,
                'VWM_setSize': set_size,
                'VWM_delay_s': delay,
                'condition_label': condition_label,
                'fit_converged': fit_result['fit_converged'],
                'excluded_fitting': not fit_result['fit_converged'],
                'exclusion_reason_fitting': fit_result.get('exclusion_reason', '')
            }
            
            if fit_result['fit_converged']:
                result_row.update({
                    'amplitude': fit_result['amplitude'],
                    'amplitude_ci_lower': fit_result.get('amplitude_ci_lower', np.nan),
                    'amplitude_ci_upper': fit_result.get('amplitude_ci_upper', np.nan),
                    'width': fit_result['width'],
                    'width_ci_lower': fit_result.get('width_ci_lower', np.nan),
                    'width_ci_upper': fit_result.get('width_ci_upper', np.nan),
                    'zero_crossing': fit_result['zero_crossing'],
                    'zero_crossing_ci_lower': fit_result.get('zero_crossing_ci_lower', np.nan),
                    'zero_crossing_ci_upper': fit_result.get('zero_crossing_ci_upper', np.nan),
                    'r_squared': fit_result['r_squared'],
                    'expanded_model_amplitude': fit_result['expanded_model_amplitude'],
                    'expanded_model_width': fit_result['expanded_model_width'],
                    'expanded_model_zero_crossing': fit_result['expanded_model_zero_crossing']
                })
            else:
                # Fill with NaN for failed fits
                result_row.update({
                    'amplitude': np.nan,
                    'amplitude_ci_lower': np.nan,
                    'amplitude_ci_upper': np.nan,
                    'width': np.nan,
                    'width_ci_lower': np.nan,
                    'width_ci_upper': np.nan,
                    'zero_crossing': np.nan,
                    'zero_crossing_ci_lower': np.nan,
                    'zero_crossing_ci_upper': np.nan,
                    'r_squared': np.nan,
                    'expanded_model_amplitude': np.nan,
                    'expanded_model_width': np.nan,
                    'expanded_model_zero_crossing': np.nan
                })
                
                if 'Insufficient' in fit_result.get('exclusion_reason', ''):
                    insufficient_bins += 1
                else:
                    fitting_failures += 1
        
            # Add expanded model parameters if available
            if fit_result['fit_converged'] and 'expanded_model_r_squared' in fit_result:
                result_row.update({
                    'expanded_model_r_squared': fit_result['expanded_model_r_squared'],
                    'expanded_model_converged': fit_result.get('expanded_model_converged', False),
                    'expanded_model_b1': fit_result.get('expanded_model_b1', np.nan),
                    'expanded_model_b2': fit_result.get('expanded_model_b2', np.nan),
                    'expanded_model_b3': fit_result.get('expanded_model_b3', np.nan)
                })
                
                # Add confidence intervals if available
                for ci_param in ['expanded_model_amplitude_ci_lower', 'expanded_model_amplitude_ci_upper',
                                'expanded_model_width_ci_lower', 'expanded_model_width_ci_upper',
                                'expanded_model_zero_crossing_ci_lower', 'expanded_model_zero_crossing_ci_upper',
                                'expanded_model_b1_ci_lower', 'expanded_model_b1_ci_upper',
                                'expanded_model_b2_ci_lower', 'expanded_model_b2_ci_upper',
                                'expanded_model_b3_ci_lower', 'expanded_model_b3_ci_upper']:
                    if ci_param in fit_result:
                        result_row[ci_param] = fit_result[ci_param]
            
            results.append(result_row)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        
        print(f"\nInitial fitting results:")
        print(f"Total assessed: {total_assessed}")
        print(f"Successful fits: {results_df['fit_converged'].sum()}")
        print(f"Failed fits: {(~results_df['fit_converged']).sum()}")
        print(f"Insufficient bins: {insufficient_bins}")
        print(f"Algorithm failures: {fitting_failures}")
        
        # Check for extreme parameters
        param_cols = ['amplitude', 'width', 'zero_crossing']
        results_df = check_extreme_parameters(results_df, param_cols)
        
        # Count final exclusions
        extreme_exclusions = (results_df['excluded_fitting'] & 
                            results_df['exclusion_reason_fitting'].str.contains('Extreme', na=False)).sum()
        
        print(f"\nFinal exclusion counts:")
        print(f"Extreme parameter exclusions: {extreme_exclusions}")
        print(f"Total excluded: {results_df['excluded_fitting'].sum()}")
        print(f"Final valid fits: {(~results_df['excluded_fitting']).sum()}")
        
        # Create exclusion log
        exclusion_log = [
            {
                'exclusion_criteria': 'Insufficient adequate bins (< 4)',
                'count_excluded': insufficient_bins,
                'total_assessed': total_assessed,
                'exclusion_percentage': (insufficient_bins / total_assessed) * 100 if total_assessed > 0 else 0
            },
            {
                'exclusion_criteria': 'DoG fitting algorithm failure',
                'count_excluded': fitting_failures,
                'total_assessed': total_assessed,
                'exclusion_percentage': (fitting_failures / total_assessed) * 100 if total_assessed > 0 else 0
            },
            {
                'exclusion_criteria': 'Extreme parameter estimates (>5 SD)',
                'count_excluded': extreme_exclusions,
                'total_assessed': total_assessed,
                'exclusion_percentage': (extreme_exclusions / total_assessed) * 100 if total_assessed > 0 else 0
            }
        ]
        
        exclusion_log_df = pd.DataFrame(exclusion_log)
        
        # Save output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save parameters file
        params_filename = f"outputs/VWM_DoG_parameters_{timestamp}.csv"
        results_df.to_csv(params_filename, index=False)
        print(f"\nSaved DoG parameters to: {params_filename}")
        
        # Save exclusion log
        log_filename = f"outputs/VWM_DoG_fitting_log_{timestamp}.csv"
        exclusion_log_df.to_csv(log_filename, index=False)
        print(f"Saved fitting log to: {log_filename}")
        
        # Count expanded model failures
        if 'expanded_model_converged' in results_df.columns:
            expanded_failures = (~results_df['expanded_model_converged'] & results_df['fit_converged']).sum()
            print(f"Expanded model failures: {expanded_failures} (out of {results_df['fit_converged'].sum()} successful basic fits)")
            
            # Add to exclusion log
            expanded_failure_log = {
                'exclusion_criteria': 'Expanded model fitting failure',
                'count_excluded': expanded_failures,
                'total_assessed': results_df['fit_converged'].sum(),
                'exclusion_percentage': (expanded_failures / results_df['fit_converged'].sum()) * 100 if results_df['fit_converged'].sum() > 0 else 0
            }
            exclusion_log_df = pd.concat([exclusion_log_df, pd.DataFrame([expanded_failure_log])], ignore_index=True)
        
        # Print final summary
        print(f"\nFinal summary:")
        print(f"Parameters file columns: {results_df.columns.tolist()}")
        print(f"First 2 rows of parameters:")
        print(results_df.head(2))
        
        print(f"\nExclusion log:")
        print(exclusion_log_df)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
