import pandas as pd
import numpy as np
import os
import glob
import sys
from datetime import datetime
from scipy.optimize import minimize
from scipy.stats import vonmises, uniform
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
    return max(files, key=os.path.getctime)

def vonmises_mixture_likelihood(params, errors_rad):
    """
    Calculate negative log-likelihood for von Mises mixture model.
    
    Parameters:
    params (array): [kappa, mu, pU] parameters
    errors_rad (array): Error data in radians
    
    Returns:
    float: Negative log-likelihood
    """
    if len(errors_rad) == 0:
        return np.inf
    kappa, mu, pU = params
    
    # Ensure valid parameter ranges
    if kappa <= 0 or pU < 0 or pU > 1:
        return np.inf
    
    # von Mises component
    vm_component = vonmises.pdf(errors_rad, kappa, loc=mu)
    
    # Uniform component
    uniform_component = 1 / (2 * np.pi)
    
    # Mixture
    mixture_pdf = (1 - pU) * vm_component + pU * uniform_component
    
    # Avoid log(0)
    mixture_pdf = np.maximum(mixture_pdf, 1e-10)
    
    return -np.sum(np.log(mixture_pdf))

def fit_mixture_model(errors_rad, n_starts=10):
    """
    Fit von Mises mixture model with multiple starting values.
    
    Parameters:
    errors_rad (array): Error data in radians
    n_starts (int): Number of random starting values
    
    Returns:
    dict: Best fit parameters and success flag
    """
    best_result = None
    best_nll = np.inf

    for _ in range(n_starts):
        # Random starting values
        kappa_start = np.random.uniform(0.01, 10)
        mu_start = np.random.uniform(-np.pi, np.pi)
        pU_start = np.random.uniform(0.01, 0.5)

        try:
            result = minimize(
                vonmises_mixture_likelihood,
                [kappa_start, mu_start, pU_start],
                args=(errors_rad,),
                method='L-BFGS-B',
                bounds=[(0.01, 1000), (-np.pi, np.pi), (0, 1)]
            )

            if result.success and result.fun < best_nll:
                best_nll = result.fun
                best_result = result

        except:
            continue

    if best_result is not None and best_result.success:
        return {
            'success': True,
            'kappa': best_result.x[0],
            'mu': best_result.x[1],
            'pU': best_result.x[2],
            'nll': best_nll
        }
    else:
        return {'success': False}


def bootstrap_reliability_assessment(participant_id, errors_rad, original_params, n_bootstrap=1000):
    """
    Perform bootstrap reliability assessment for a participant.
    
    Parameters:
    participant_id (str): Participant identifier
    errors_rad (array): Error data in radians
    original_params (dict): Original model parameters
    n_bootstrap (int): Number of bootstrap samples
    
    Returns:
    dict: Bootstrap results
    """
    print(f"  Starting bootstrap for participant {participant_id} with {len(errors_rad)} trials")
    
    bootstrap_kappas = []
    successful_fits = 0
    boundary_hits = 0

    for i in range(n_bootstrap):
        if (i + 1) % 100 == 0:
            print(f"    Bootstrap iteration {i + 1}/{n_bootstrap}")

        # Bootstrap sample
        bootstrap_indices = np.random.choice(len(errors_rad), size=len(errors_rad), replace=True)
        bootstrap_errors = errors_rad[bootstrap_indices]

        # Fit model
        fit_result = fit_mixture_model(bootstrap_errors, n_starts=5)

        if fit_result['success']:
            if fit_result['kappa'] > 0.01:  # Not at boundary
                bootstrap_kappas.append(fit_result['kappa'])
                successful_fits += 1
            else:  # At boundary
                boundary_hits += 1

    convergence_rate = successful_fits / n_bootstrap
    print(f"    Bootstrap convergence rate (non-boundary): {convergence_rate:.3f} ({successful_fits}/{n_bootstrap})")
    print(f"    Bootstrap kappa boundary hits (kappa=0.01): {boundary_hits}/{n_bootstrap}")

    if len(bootstrap_kappas) == 0:
        return {
            'participantId': participant_id,
            'bootstrap_successful_fits': 0,
            'bootstrap_convergence_rate': 0.0,
            'bootstrap_kappa_boundary_hits': boundary_hits,
            'reliable': False,
            'reason': 'no_successful_fits'
        }

    if len(bootstrap_kappas) < 50:  # Need minimum samples for CI
        return {
            'participantId': participant_id,
            'bootstrap_successful_fits': successful_fits,
            'bootstrap_convergence_rate': convergence_rate,
            'bootstrap_kappa_boundary_hits': boundary_hits,
            'reliable': False,
            'reason': 'insufficient_bootstrap_samples'
        }

    bootstrap_kappas = np.array(bootstrap_kappas)

    # Calculate confidence intervals
    ci_lower = np.percentile(bootstrap_kappas, 2.5)
    ci_upper = np.percentile(bootstrap_kappas, 97.5)
    ci_span = ci_upper - ci_lower
    median_kappa = np.median(bootstrap_kappas)
    relative_span = ci_span / median_kappa if median_kappa > 0 else np.inf

    # Diagnostic: print if CI lower bound is at the optimization bound
    if np.isclose(ci_lower, 0.01, atol=1e-9):
        print(f"    WARNING: CI lower bound at optimization bound (0.01). Check if kappa estimates are hitting lower bound.")

    # Print min/max kappa for diagnostics
    print(f"    Bootstrap kappa min: {np.min(bootstrap_kappas):.4f}, max: {np.max(bootstrap_kappas):.4f}")

    # Apply exclusion criteria
    excluded_unreliable_kappa = relative_span > 20
    excluded_convergence_failure = convergence_rate < 0.90
    # Poor model fit criterion
    excluded_poor_model_fit = (original_params['aic_mixture'] - original_params['aic_single_vm']) > 2

    # Apply exclusion criteria in priority order
    if excluded_poor_model_fit:
        final_reason = 'poor_model_fit'
    elif excluded_convergence_failure:
        final_reason = 'convergence_failure'
    elif excluded_unreliable_kappa:
        final_reason = 'unreliable_kappa_estimation'
    else:
        final_reason = 'none'

    reliable = final_reason == 'none'

    print(f"    Median kappa: {median_kappa:.3f}, CI span: {ci_span:.3f}, Relative span: {relative_span:.3f}")
    print(f"    Reliable: {reliable}, Reason: {final_reason}")

    return {
        'participantId': participant_id,
        'original_kappa': original_params['kappa'],
        'bootstrap_kappa_median': median_kappa,
        'bootstrap_kappa_ci_lower': ci_lower,
        'bootstrap_kappa_ci_upper': ci_upper,
        'bootstrap_ci_span': ci_span,
        'bootstrap_relative_span': relative_span,
        'bootstrap_successful_fits': successful_fits,
        'bootstrap_convergence_rate': convergence_rate,
        'bootstrap_kappa_boundary_hits': boundary_hits,
        'reliable_parameter': reliable,
        'excluded_unreliable_kappa': excluded_unreliable_kappa,
        'excluded_convergence_failure': excluded_convergence_failure,
        'excluded_poor_model_fit': excluded_poor_model_fit,
        'final_exclusion_reason': final_reason
    }

def main():
    """Main function to execute bootstrap reliability assessment."""
    try:
        print("Starting bootstrap reliability assessment...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
        
        # Find input files
        print("\nLooking for input files...")
        
        param_pattern = 'outputs/VWM_mixture_model_parameters_*.csv'
        param_file = find_latest_file(param_pattern)
        if param_file is None:
            print(f"Error: No parameter file found matching pattern {param_pattern}")
            return 1
        print(f"Found parameter file: {param_file}")
        
        data_pattern = 'outputs/cleaned_cognitive_data_*.csv'
        data_file = find_latest_file(data_pattern)
        if data_file is None:
            print(f"Error: No cognitive data file found matching pattern {data_pattern}")
            return 1
        print(f"Found cognitive data file: {data_file}")
        
        # Load parameter file
        print(f"\nLoading parameter file: {param_file}")
        param_df = pd.read_csv(param_file)
        print("Parameter file columns:", list(param_df.columns))
        print("First 3 rows of parameter data:")
        print(param_df.head(3))
        
        # Validate required columns in parameter file
        required_param_cols = [
            'participantId', 'kappa_concentration', 'mu_bias_radians', 
            'pU_uniform_proportion', 'model_converged', 'excluded_insufficient_data',
            'excluded_convergence_failure', 'excluded_extreme_parameters',
            'aic_mixture_model', 'aic_single_vonmises'
        ]
        missing_param_cols = [col for col in required_param_cols if col not in param_df.columns]
        if missing_param_cols:
            print(f"Error: Missing required columns in parameter file: {missing_param_cols}")
            return 1
        
        # Load cognitive data file
        print(f"\nLoading cognitive data file: {data_file}")
        data_df = pd.read_csv(data_file)
        print("Cognitive data file columns:", list(data_df.columns))
        print("First 3 rows of cognitive data:")
        print(data_df.head(3))
        
        # Validate required columns in cognitive data file
        required_data_cols = [
            'participantId', 'isPractice', 'trial_type', 
            'VWM_error_normalized_degrees', 'excluded_trial'
        ]
        missing_data_cols = [col for col in required_data_cols if col not in data_df.columns]
        if missing_data_cols:
            print(f"Error: Missing required columns in cognitive data file: {missing_data_cols}")
            return 1
        
        # Print unique values for key columns
        print("\nUnique values in key columns:")
        print("trial_type values:", sorted(list(data_df['trial_type'].unique())))
        print("isPractice values:", sorted(list(data_df['isPractice'].unique())))
        print("excluded_trial values:", sorted(list(data_df['excluded_trial'].unique())))
        print("model_converged values:", sorted(list(param_df['model_converged'].unique())))
        print("excluded_insufficient_data values:", sorted(list(param_df['excluded_insufficient_data'].unique())))
        print("excluded_convergence_failure values:", sorted(list(param_df['excluded_convergence_failure'].unique())))
        print("excluded_extreme_parameters values:", sorted(list(param_df['excluded_extreme_parameters'].unique())))
        
        # Select participants for analysis
        print("\nSelecting participants for bootstrap analysis...")
        
        # Filter parameter data
        valid_params = param_df[
            (param_df['model_converged'] == True) &
            (param_df['excluded_insufficient_data'] == False) &
            (param_df['excluded_convergence_failure'] == False) &
            (param_df['excluded_extreme_parameters'] == False)
        ].copy()
        # Ensure boolean columns are of bool dtype
        for col in ['model_converged', 'excluded_insufficient_data', 'excluded_convergence_failure', 'excluded_extreme_parameters']:
            if valid_params[col].dtype != bool:
                valid_params[col] = valid_params[col].astype(bool)
        
        print(f"Participants with valid parameters: {len(valid_params)}")
        print("Valid participants:", sorted(valid_params['participantId'].unique()))
        
        # Filter cognitive data for VWM trials
        vwm_data = data_df[
            (data_df['trial_type'] == 'VWM') &
            (data_df['isPractice'] == False) &
            (data_df['excluded_trial'] == False)
        ].copy()
        # Ensure boolean columns are of bool dtype
        for col in ['isPractice', 'excluded_trial']:
            if vwm_data[col].dtype != bool:
                vwm_data[col] = vwm_data[col].astype(bool)
        
        print(f"Valid VWM trials: {len(vwm_data)}")
        
        # Find participants with both parameter and trial data
        param_participants = set(valid_params['participantId'])
        data_participants = set(vwm_data['participantId'])
        common_participants = param_participants.intersection(data_participants)
        
        print(f"Participants with both parameter and trial data: {len(common_participants)}")
        print("Common participants:", sorted(common_participants))
        
        if len(common_participants) == 0:
            print("Error: No participants with both valid parameters and trial data")
            return 1
        
        # Perform bootstrap analysis for each participant
        print("\nPerforming bootstrap reliability assessment...")
        
        bootstrap_results = []
        
        if len(common_participants) == 0:
            print("No participants to analyze after filtering.")
        else:
            for i, participant_id in enumerate(sorted(common_participants)):
                print(f"\nProcessing participant {i+1}/{len(common_participants)}: {participant_id}")
                
                # Get participant's parameter data
                participant_params = valid_params[valid_params['participantId'] == participant_id].iloc[0]
                original_params = {
                    'kappa': participant_params['kappa_concentration'],
                    'mu': participant_params['mu_bias_radians'],
                    'pU': participant_params['pU_uniform_proportion'],
                    'aic_mixture': participant_params['aic_mixture_model'],
                    'aic_single_vm': participant_params['aic_single_vonmises']
                }
                
                # Get participant's trial data
                participant_trials = vwm_data[vwm_data['participantId'] == participant_id]
                errors_degrees = participant_trials['VWM_error_normalized_degrees'].values
                
                # Convert to radians
                errors_rad = np.deg2rad(errors_degrees)
                
                print(f"  Participant has {len(errors_rad)} valid trials")
                print(f"  Original kappa: {original_params['kappa']:.3f}")
                
                if len(errors_rad) < 20:  # Minimum trials needed
                    print(f"  Skipping participant {participant_id}: insufficient trials ({len(errors_rad)})")
                    continue
                
                # Perform bootstrap assessment
                result = bootstrap_reliability_assessment(participant_id, errors_rad, original_params)
                bootstrap_results.append(result)
        
        print(f"\nCompleted bootstrap analysis for {len(bootstrap_results)} participants")
        
        # Create output dataframes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Bootstrap reliability results
        bootstrap_df = pd.DataFrame(bootstrap_results)
        
        print("\nBootstrap results summary:")
        print("Bootstrap results columns:", list(bootstrap_df.columns))
        print("First 2 rows of bootstrap results:")
        print(bootstrap_df.head(2))
        
        # Count exclusions based on prioritized final_exclusion_reason
        exclusion_counts = bootstrap_df['final_exclusion_reason'].value_counts().to_dict()
        # Ensure all possible reasons are in the dictionary, even if count is 0
        for reason in ['unreliable_kappa_estimation', 'convergence_failure', 'poor_model_fit', 'none']:
            if reason not in exclusion_counts:
                exclusion_counts[reason] = 0

        print(f"\nExclusion counts:")
        for criterion, count in exclusion_counts.items():
            print(f"  {criterion}: {count}")

        reliable_participants = bootstrap_df[bootstrap_df['reliable_parameter'] == True]
        print(f"\nReliable participants: {len(reliable_participants)}")
        
        # Save bootstrap reliability assessment
        bootstrap_output_file = f'outputs/bootstrap_reliability_assessment_{timestamp}.csv'
        bootstrap_df.to_csv(bootstrap_output_file, index=False)
        print(f"Saved bootstrap reliability assessment: {bootstrap_output_file}")
        
        # Create exclusion log
        exclusion_log = []
        exclusion_log.append({
            'exclusion_criterion': 'unreliable_kappa',
            'participants_excluded': exclusion_counts.get('unreliable_kappa_estimation', 0),
            'description': 'Bootstrap 95% CI relative span is excessively large (span/median > 20)'
        })
        exclusion_log.append({
            'exclusion_criterion': 'convergence_failure',
            'participants_excluded': exclusion_counts.get('convergence_failure', 0),
            'description': 'Less than 900/1000 successful bootstrap convergences'
        })
        exclusion_log.append({
            'exclusion_criterion': 'poor_model_fit',
            'participants_excluded': exclusion_counts.get('poor_model_fit', 0),
            'description': 'Poor model fit (AIC difference > 2)'
        })
        
        exclusion_log_df = pd.DataFrame(exclusion_log)
        exclusion_log_file = f'outputs/parameter_reliability_exclusion_log_{timestamp}.csv'
        exclusion_log_df.to_csv(exclusion_log_file, index=False)
        print(f"Saved exclusion log: {exclusion_log_file}")
        
        # Create final reliable parameters file
        if len(reliable_participants) > 0:
            # Merge with original parameters
            final_params = reliable_participants.merge(
                valid_params[['participantId', 'kappa_concentration', 'mu_bias_radians', 'pU_uniform_proportion']],
                on='participantId'
            )
            
            final_reliable_df = pd.DataFrame({
                'participantId': final_params['participantId'],
                'kappa_concentration': final_params['kappa_concentration'],
                'mu_bias_radians': final_params['mu_bias_radians'],
                'pU_uniform_proportion': final_params['pU_uniform_proportion'],
                'bootstrap_kappa_ci_lower': final_params['bootstrap_kappa_ci_lower'],
                'bootstrap_kappa_ci_upper': final_params['bootstrap_kappa_ci_upper'],
                'included_in_analysis': True
            })
        else:
            # Create empty dataframe with correct columns
            final_reliable_df = pd.DataFrame(columns=[
                'participantId', 'kappa_concentration', 'mu_bias_radians', 
                'pU_uniform_proportion', 'bootstrap_kappa_ci_lower', 
                'bootstrap_kappa_ci_upper', 'included_in_analysis'
            ])
        
        final_params_file = f'outputs/final_reliable_VWM_parameters_{timestamp}.csv'
        final_reliable_df.to_csv(final_params_file, index=False)
        print(f"Saved final reliable parameters: {final_params_file}")
        
        print("\nFinal reliable parameters summary:")
        print("Final parameters columns:", list(final_reliable_df.columns))
        print("First 2 rows of final parameters:")
        print(final_reliable_df.head(2))
        
        print(f"\nBootstrap reliability assessment completed successfully!")
        print(f"Total participants analyzed: {len(bootstrap_results)}")
        print(f"Reliable participants: {len(reliable_participants)}")
        print(f"Reliability rate: {len(reliable_participants)/len(bootstrap_results)*100:.1f}%")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in bootstrap reliability assessment: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
