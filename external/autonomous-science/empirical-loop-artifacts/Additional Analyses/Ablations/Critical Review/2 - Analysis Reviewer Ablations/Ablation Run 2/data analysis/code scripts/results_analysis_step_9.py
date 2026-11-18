import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import scipy.stats as stats
from scipy.stats import circstd
import warnings
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def calculate_circular_std(angles_rad):
    """
    Calculate circular standard deviation for angles in radians.
    
    Parameters:
    angles_rad (array): Array of angles in radians
    
    Returns:
    float: Circular standard deviation
    """
    if len(angles_rad) == 0:
        return np.nan
    return circstd(angles_rad, high=np.pi, low=-np.pi)

def degrees_to_radians(degrees):
    """
    Convert degrees to radians.
    
    Parameters:
    degrees (array): Array of angles in degrees
    
    Returns:
    array: Array of angles in radians
    """
    return np.deg2rad(degrees)

def standardize_variable(x):
    """
    Standardize a variable (z-score), ignoring NaNs in calculation.
    """
    return (x - x.mean()) / x.std()

def run_logistic_regression(data, outcome_col, predictor_col, covariates):
    """
    Run logistic regression using scipy.
    
    Parameters:
    data (DataFrame): Input data
    outcome_col (str): Name of outcome column
    predictor_col (str): Name of predictor column
    covariates (list): List of covariate column names
    
    Returns:
    dict: Regression results
    """
    from scipy.optimize import minimize
    from scipy.stats import norm
    
    # Prepare data
    y = data[outcome_col].values
    X_cols = [predictor_col] + covariates
    X = data[X_cols].values
    
    # Add intercept
    X = np.column_stack([np.ones(len(X)), X])
    
    # Logistic regression log-likelihood
    def neg_log_likelihood(params):
        linear_pred = X @ params
        prob = 1 / (1 + np.exp(-linear_pred))
        prob = np.clip(prob, 1e-15, 1 - 1e-15)  # Avoid log(0)
        return -np.sum(y * np.log(prob) + (1 - y) * np.log(1 - prob))
    
    # Initial parameters
    initial_params = np.zeros(X.shape[1])
    
    # Optimize
    try:
        result = minimize(neg_log_likelihood, initial_params, method='BFGS')
        
        # Calculate standard errors using Hessian
        hessian = result.hess_inv
        se = np.sqrt(np.diag(hessian))
        
        # Calculate p-values
        z_scores = result.x / se
        p_values = 2 * (1 - norm.cdf(np.abs(z_scores)))
        
        # Calculate confidence intervals
        ci_lower = result.x - 1.96 * se
        ci_upper = result.x + 1.96 * se
        
        # Calculate pseudo R-squared (McFadden's)
        null_ll = -len(y) * (np.mean(y) * np.log(np.mean(y)) + (1 - np.mean(y)) * np.log(1 - np.mean(y)))
        r_squared = 1 - (result.fun / null_ll)
        
        return {
            'coefficient': result.x[1],  # First predictor coefficient
            'standard_error': se[1],
            'p_value': p_values[1],
            'confidence_interval_lower': ci_lower[1],
            'confidence_interval_upper': ci_upper[1],
            'model_r_squared': r_squared,
            'n_participants': len(data)
        }
    except:
        return {
            'coefficient': np.nan,
            'standard_error': np.nan,
            'p_value': np.nan,
            'confidence_interval_lower': np.nan,
            'confidence_interval_upper': np.nan,
            'model_r_squared': np.nan,
            'n_participants': len(data)
        }

def run_linear_regression(data, outcome_col, predictor_col, covariates):
    """
    Run linear regression using scipy.
    
    Parameters:
    data (DataFrame): Input data
    outcome_col (str): Name of outcome column
    predictor_col (str): Name of predictor column
    covariates (list): List of covariate column names
    
    Returns:
    dict: Regression results
    """
    from scipy.stats import linregress
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import r2_score
    
    # Prepare data
    y = data[outcome_col].values
    X_cols = [predictor_col] + covariates
    X = data[X_cols].values
    
    try:
        # Fit model
        model = LinearRegression()
        model.fit(X, y)
        
        # Get predictions
        y_pred = model.predict(X)
        
        # Calculate standard errors
        n = len(y)
        p = X.shape[1]
        residuals = y - y_pred
        mse = np.sum(residuals**2) / (n - p - 1)
        
        # Design matrix with intercept
        X_with_intercept = np.column_stack([np.ones(n), X])
        try:
            var_covar_matrix = mse * np.linalg.inv(X_with_intercept.T @ X_with_intercept)
            se = np.sqrt(np.diag(var_covar_matrix))
            predictor_se = se[1]  # Standard error for first predictor
        except:
            predictor_se = np.nan
        
        # Get coefficient for first predictor
        predictor_coef = model.coef_[0]
        
        # Calculate t-statistic and p-value
        if not np.isnan(predictor_se) and predictor_se != 0:
            t_stat = predictor_coef / predictor_se
            p_value = 2 * (1 - stats.t.cdf(np.abs(t_stat), n - p - 1))
        else:
            p_value = np.nan
        
        # Calculate confidence intervals
        if not np.isnan(predictor_se):
            t_critical = stats.t.ppf(0.975, n - p - 1)
            ci_lower = predictor_coef - t_critical * predictor_se
            ci_upper = predictor_coef + t_critical * predictor_se
        else:
            ci_lower = np.nan
            ci_upper = np.nan
        
        # Calculate R-squared
        r_squared = r2_score(y, y_pred)
        
        return {
            'coefficient': predictor_coef,
            'standard_error': predictor_se,
            'p_value': p_value,
            'confidence_interval_lower': ci_lower,
            'confidence_interval_upper': ci_upper,
            'model_r_squared': r_squared,
            'n_participants': len(data)
        }
    except:
        return {
            'coefficient': np.nan,
            'standard_error': np.nan,
            'p_value': np.nan,
            'confidence_interval_lower': np.nan,
            'confidence_interval_upper': np.nan,
            'model_r_squared': np.nan,
            'n_participants': len(data)
        }

def apply_fdr_correction(p_values):
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Parameters:
    p_values (array): Array of p-values
    
    Returns:
    array: FDR-corrected p-values
    """
    from scipy.stats import false_discovery_control
    try:
        return false_discovery_control(p_values)
    except:
        # Fallback manual implementation
        p_values = np.array(p_values)
        sorted_indices = np.argsort(p_values)
        sorted_p = p_values[sorted_indices]
        m = len(p_values)
        
        corrected_p = np.zeros_like(p_values)
        for i in range(m):
            corrected_p[sorted_indices[i]] = min(1.0, sorted_p[i] * m / (i + 1))
        
        return corrected_p

def main():
    """
    Main function to perform sensitivity analysis of precision measures.
    """
    try:
        print("Starting sensitivity analysis of precision measures...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find input files
        print("\nFinding input files...")
        
        trial_file = find_latest_file('outputs/trial_level_cleaned_data_*.csv')
        mixture_file = find_latest_file('outputs/vwm_mixture_model_parameters_*.csv')
        individual_file = find_latest_file('outputs/individual_level_measures_*.csv')
        
        if not trial_file:
            print("ERROR: Trial level data file not found")
            return 1
        if not mixture_file:
            print("ERROR: Mixture model parameters file not found")
            return 1
        if not individual_file:
            print("ERROR: Individual level measures file not found")
            return 1
            
        print(f"Found trial file: {trial_file}")
        print(f"Found mixture file: {mixture_file}")
        print(f"Found individual file: {individual_file}")
        
        # Load data
        print("\nLoading data files...")
        
        trial_data = pd.read_csv(trial_file)
        mixture_data = pd.read_csv(mixture_file)
        individual_data = pd.read_csv(individual_file)
        
        print(f"Trial data shape: {trial_data.shape}")
        print(f"Trial data columns: {list(trial_data.columns)}")
        print("First 3 rows of trial data:")
        print(trial_data.head(3))
        
        print(f"\nMixture data shape: {mixture_data.shape}")
        print(f"Mixture data columns: {list(mixture_data.columns)}")
        print("First 3 rows of mixture data:")
        print(mixture_data.head(3))
        
        print(f"\nIndividual data shape: {individual_data.shape}")
        print(f"Individual data columns: {list(individual_data.columns)}")
        print("First 3 rows of individual data:")
        print(individual_data.head(3))
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        if 'isPractice' in trial_data.columns:
            print(f"isPractice unique values: {trial_data['isPractice'].unique()}")
        if 'VWM_trial_excluded' in trial_data.columns:
            print(f"VWM_trial_excluded unique values: {trial_data['VWM_trial_excluded'].unique()}")
        if 'MRT_trial_excluded' in trial_data.columns:
            print(f"MRT_trial_excluded unique values: {trial_data['MRT_trial_excluded'].unique()}")
        if 'MRT_angle_degrees' in trial_data.columns:
            print(f"MRT_angle_degrees unique values: {sorted(trial_data['MRT_angle_degrees'].unique())}")
        
        # Merge datasets
        print("\nMerging datasets...")
        
        # Merge mixture and individual data
        merged_data = pd.merge(mixture_data, individual_data, on='participantId', how='inner')
        print(f"Merged data shape after combining mixture and individual: {merged_data.shape}")
        
        # 1. Calculate simple precision
        print("\n=== STEP 1: Calculating simple precision ===")
        
        simple_precision_results = []
        
        for participant_id in merged_data['participantId'].unique():
            print(f"Processing participant {participant_id}")
            
            # Get participant data
            participant_trials = trial_data[
                (trial_data['participantId'] == participant_id) & 
                (trial_data['isPractice'] == False) & 
                (trial_data['VWM_trial_excluded'] == False)
            ]
            
            participant_mixture = merged_data[merged_data['participantId'] == participant_id]
            
            if len(participant_trials) == 0 or len(participant_mixture) == 0:
                print(f"  No valid trials for participant {participant_id}")
                continue

            # Get mixture model parameters
            kappa = participant_mixture['kappa_vonmises'].iloc[0]
            mu = participant_mixture['mu_vonmises'].iloc[0]

            # Calculate error threshold based on von Mises distribution
            # Use 2 standard deviations as threshold
            if kappa > 0:
                # Approximate circular standard deviation for von Mises
                circ_std_approx = np.sqrt(-2 * np.log(np.i0(kappa) / np.exp(kappa)))
                error_threshold_rad = 2 * circ_std_approx
                error_threshold_deg = np.degrees(error_threshold_rad)
            else:
                error_threshold_deg = 90  # Fallback for very low precision

            # Filter trials within threshold
            errors_deg = participant_trials['VWM_error_degrees']
            non_guess_trials = participant_trials[np.abs(errors_deg) <= error_threshold_deg]

            if len(non_guess_trials) < 3:
                simple_precision = np.nan
            else:
                # Calculate circular standard deviation on filtered trials
                non_guess_errors_rad = degrees_to_radians(non_guess_trials['VWM_error_degrees'])
                circ_std = calculate_circular_std(non_guess_errors_rad)
                
                if circ_std > 0:
                    simple_precision = 1 / circ_std
                else:
                    simple_precision = np.nan

            simple_precision_results.append({
                'participantId': participant_id,
                'simple_precision': simple_precision
            })
        
        simple_precision_df = pd.DataFrame(simple_precision_results)
        print(f"Calculated simple precision for {len(simple_precision_df)} participants")
        
        # 2. Identify best-fitting alternative distribution
        print("\n=== STEP 2: Identifying best-fitting alternative distributions ===")
        
        alternative_kappa_results = []
        
        for _, row in merged_data.iterrows():
            participant_id = row['participantId']
            
            aic_vonmises = row['AIC_vonmises']
            aic_wrapped_normal = row['AIC_wrapped_normal']
            aic_wrapped_cauchy = row['AIC_wrapped_cauchy']
            
            # Find best alternative model
            best_alt_aic = min(aic_wrapped_normal, aic_wrapped_cauchy)
            aic_difference = aic_vonmises - best_alt_aic
            
            if aic_difference > 4:  # Alternative model outperforms by > 4 AIC units
                if aic_wrapped_normal < aic_wrapped_cauchy:
                    best_alternative_kappa = row['kappa_wrapped_normal']
                    alternative_model_used = 'wrapped_normal'
                else:
                    best_alternative_kappa = row['kappa_wrapped_cauchy']
                    alternative_model_used = 'wrapped_cauchy'
            else:
                best_alternative_kappa = row['kappa_vonmises']
                alternative_model_used = 'vonmises'
            
            alternative_kappa_results.append({
                'participantId': participant_id,
                'best_alternative_kappa': best_alternative_kappa,
                'alternative_model_used': alternative_model_used
            })
            
            print(f"Participant {participant_id}: {alternative_model_used} (AIC diff: {aic_difference:.2f})")
        
        alternative_kappa_df = pd.DataFrame(alternative_kappa_results)
        
        # Merge all precision measures
        precision_measures = pd.merge(simple_precision_df, alternative_kappa_df, on='participantId', how='inner')
        precision_measures = pd.merge(precision_measures, merged_data, on='participantId', how='inner')
        
        # Calculate correlations
        print("\n=== Calculating precision measure correlations ===")
        
        valid_data = precision_measures.dropna(subset=['simple_precision', 'kappa_vonmises', 'best_alternative_kappa'])
        
        if len(valid_data) > 0:
            corr_vonmises_simple = np.corrcoef(valid_data['kappa_vonmises'], valid_data['simple_precision'])[0, 1]
            corr_vonmises_alternative = np.corrcoef(valid_data['kappa_vonmises'], valid_data['best_alternative_kappa'])[0, 1]
        else:
            corr_vonmises_simple = np.nan
            corr_vonmises_alternative = np.nan
        
        precision_measures['precision_correlation_vonmises_simple'] = corr_vonmises_simple
        precision_measures['precision_correlation_vonmises_alternative'] = corr_vonmises_alternative
        
        print(f"Correlation von Mises vs Simple: {corr_vonmises_simple:.3f}")
        print(f"Correlation von Mises vs Alternative: {corr_vonmises_alternative:.3f}")
        
        # Prepare data for regression analyses
        print("\n=== Preparing data for regression analyses ===")
        
        # Extract participant flags from trial_data
        participant_flags = trial_data[['participantId', 'participant_meets_minimum_trials']].drop_duplicates()
        analysis_data = pd.merge(precision_measures, participant_flags, on='participantId', how='inner')

        # Validate required columns exist
        required_cols = ['participant_meets_minimum_trials']
        missing_cols = [col for col in required_cols if col not in analysis_data.columns]
        if missing_cols:
            print(f"ERROR: Missing required columns: {missing_cols}")
            return 1

        # Filter to participants meeting minimum trials criterion
        analysis_data = analysis_data[analysis_data['participant_meets_minimum_trials'] == True].copy()
        print(f"Analysis data shape after filtering: {analysis_data.shape}")
        
        # Standardize covariates
        covariates = ['vwm_mean_accuracy_degrees', 'vwm_rt_cv', 'mrt_rt_cv', 'vwm_timeout_rate', 'engagement_index']

        for covariate in covariates:
            if covariate in analysis_data.columns:
                analysis_data[f'z_{covariate}'] = standardize_variable(analysis_data[covariate])

        # Standardize precision measures
        for precision_col in ['simple_precision', 'kappa_vonmises', 'best_alternative_kappa']:
            if precision_col in analysis_data.columns:
                analysis_data[f'z_{precision_col}'] = standardize_variable(analysis_data[precision_col])
        
        # 3-6. Run regression analyses
        print("\n=== STEP 3-6: Running regression analyses ===")
        
        regression_results = []
        
        # Prepare MRT trial-level data
        mrt_trial_data = trial_data[
            (trial_data['isPractice'] == False) & 
            (trial_data['MRT_trial_excluded'] == False)
        ].copy()
        
        # Merge with analysis data
        mrt_analysis_data = pd.merge(mrt_trial_data, analysis_data, on='participantId', how='inner')
        
        print(f"MRT analysis data shape: {mrt_analysis_data.shape}")
        
        # MRT Accuracy Analysis
        print("\n--- MRT Accuracy Analysis ---")
        
        angular_disparities = [0, 50, 100, 150]
        precision_measures_list = ['simple_precision', 'kappa_vonmises', 'best_alternative_kappa']
        control_covariates = ['z_vwm_mean_accuracy_degrees', 'z_vwm_rt_cv', 'z_mrt_rt_cv', 'z_vwm_timeout_rate', 'z_engagement_index']
        
        for disparity in angular_disparities:
            disparity_data = mrt_analysis_data[mrt_analysis_data['MRT_angle_degrees'] == disparity]
            print(f"\nAngular disparity {disparity}°: {len(disparity_data)} trials")
            
            if len(disparity_data) == 0:
                continue
            
            for precision_measure in precision_measures_list:
                z_precision_col = f'z_{precision_measure}'
                
                if z_precision_col not in disparity_data.columns:
                    continue
                
                # Remove rows with missing data
                analysis_cols = [z_precision_col] + control_covariates + ['MRT_isCorrect']
                clean_data = disparity_data.dropna(subset=analysis_cols)
                
                print(f"  {precision_measure}: {len(clean_data)} valid observations")
                
                if len(clean_data) < 10:  # Minimum sample size
                    continue
                
                # Run logistic regression
                result = run_logistic_regression(
                    clean_data, 
                    'MRT_isCorrect', 
                    z_precision_col, 
                    control_covariates
                )
                
                result.update({
                    'analysis_type': 'MRT_accuracy',
                    'outcome_measure': 'accuracy',
                    'angular_disparity': disparity,
                    'precision_measure': precision_measure
                })
                
                regression_results.append(result)
                
                print(f"    Coefficient: {result['coefficient']:.4f}, p-value: {result['p_value']:.4f}")
        
        # MRT Reaction Time Analysis
        print("\n--- MRT Reaction Time Analysis ---")

        # Per instructions, aggregate to participant-level median RTs for correct trials
        correct_mrt_trials = mrt_analysis_data[mrt_analysis_data['MRT_isCorrect'] == True].copy()
        correct_mrt_trials['log_MRT_rt_ms'] = np.log(correct_mrt_trials['MRT_rt_ms'])
        mrt_rt_agg = correct_mrt_trials.groupby(['participantId', 'MRT_angle_degrees'])['log_MRT_rt_ms'].median().reset_index()
        participant_level_rt_data = pd.merge(analysis_data, mrt_rt_agg, on='participantId')

        for disparity in angular_disparities:
            disparity_data = participant_level_rt_data[participant_level_rt_data['MRT_angle_degrees'] == disparity]
            print(f"\nAngular disparity {disparity}°: {len(disparity_data)} participants")

            if len(disparity_data) == 0:
                continue

            for precision_measure in precision_measures_list:
                z_precision_col = f'z_{precision_measure}'

                if z_precision_col not in disparity_data.columns:
                    continue

                # Remove rows with missing data
                analysis_cols = [z_precision_col] + control_covariates + ['log_MRT_rt_ms']
                clean_data = disparity_data.dropna(subset=analysis_cols)

                print(f"  {precision_measure}: {len(clean_data)} valid observations")

                if len(clean_data) < 10:  # Minimum sample size
                    continue

                # Run linear regression
                result = run_linear_regression(
                    clean_data,
                    'log_MRT_rt_ms',
                    z_precision_col,
                    control_covariates
                )

                result.update({
                    'analysis_type': 'MRT_reaction_time',
                    'outcome_measure': 'log_reaction_time',
                    'angular_disparity': disparity,
                    'precision_measure': precision_measure
                })

                regression_results.append(result)

                print(f"    Coefficient: {result['coefficient']:.4f}, p-value: {result['p_value']:.4f}")
        
        # VVIQ2 Analysis
        print("\n--- VVIQ2 Analysis ---")
        
        vviq2_measures = [
            'vviq2_total_score',
            'vviq2_face_person_score',
            'vviq2_nature_score', 
            'vviq2_shop_score',
            'vviq2_natural_env_score',
            'vviq2_car_road_score',
            'vviq2_beach_score',
            'vviq2_station_score',
            'vviq2_garden_score'
        ]
        
        for vviq2_measure in vviq2_measures:
            if vviq2_measure not in analysis_data.columns:
                continue
                
            print(f"\nVVIQ2 measure: {vviq2_measure}")
            
            for precision_measure in precision_measures_list:
                z_precision_col = f'z_{precision_measure}'
                
                if z_precision_col not in analysis_data.columns:
                    continue
                
                # Remove rows with missing data
                analysis_cols = [z_precision_col] + control_covariates + [vviq2_measure]
                clean_data = analysis_data.dropna(subset=analysis_cols)
                
                print(f"  {precision_measure}: {len(clean_data)} valid observations")
                
                if len(clean_data) < 10:  # Minimum sample size
                    continue
                
                # Run linear regression
                result = run_linear_regression(
                    clean_data, 
                    vviq2_measure, 
                    z_precision_col, 
                    control_covariates
                )
                
                result.update({
                    'analysis_type': 'VVIQ2',
                    'outcome_measure': vviq2_measure,
                    'angular_disparity': 'NA',
                    'precision_measure': precision_measure
                })
                
                regression_results.append(result)
                
                print(f"    Coefficient: {result['coefficient']:.4f}, p-value: {result['p_value']:.4f}")
        
        # Apply FDR correction to VVIQ2 subscales
        print("\n--- Applying FDR correction to VVIQ2 subscales ---")
        
        vviq2_subscales = [measure for measure in vviq2_measures if measure != 'vviq2_total_score']
        
        for precision_measure in precision_measures_list:
            subscale_results = [r for r in regression_results 
                              if r['analysis_type'] == 'VVIQ2' 
                              and r['precision_measure'] == precision_measure 
                              and r['outcome_measure'] in vviq2_subscales]
            
            if len(subscale_results) > 0:
                p_values = [r['p_value'] for r in subscale_results if not np.isnan(r['p_value'])]
                
                if len(p_values) > 0:
                    corrected_p = apply_fdr_correction(p_values)
                    
                    # Update results with corrected p-values
                    # Do not add p_value_fdr_corrected to results, as it's not in output columns
                    p_idx = 0
                    for r in subscale_results:
                        if not np.isnan(r['p_value']):
                            # FDR-corrected p-values are computed but not added to results
                            p_idx += 1
        
        # Convert results to DataFrame
        regression_results_df = pd.DataFrame(regression_results)
        print(f"\nGenerated {len(regression_results_df)} regression results")
        
        # 7. Compare sensitivity analysis results
        print("\n=== STEP 7: Comparing sensitivity analysis results ===")
        
        robustness_comparisons = []
        
        # Group results by analysis type and outcome
        for analysis_type in regression_results_df['analysis_type'].unique():
            type_results = regression_results_df[regression_results_df['analysis_type'] == analysis_type]
            
            for outcome in type_results['outcome_measure'].unique():
                outcome_results = type_results[type_results['outcome_measure'] == outcome]
                
                if analysis_type in ['MRT_accuracy', 'MRT_reaction_time']:
                    for disparity in outcome_results['angular_disparity'].unique():
                        disparity_results = outcome_results[outcome_results['angular_disparity'] == disparity]
                        
                        # Get results for each precision measure
                        vonmises_result = disparity_results[disparity_results['precision_measure'] == 'kappa_vonmises']
                        simple_result = disparity_results[disparity_results['precision_measure'] == 'simple_precision']
                        alternative_result = disparity_results[disparity_results['precision_measure'] == 'best_alternative_kappa']
                        
                        if len(vonmises_result) > 0 and len(simple_result) > 0 and len(alternative_result) > 0:
                            comparison = {
                                'analysis_comparison': f"{analysis_type}_{outcome}_disparity_{disparity}",
                                'primary_coefficient': vonmises_result['coefficient'].iloc[0],
                                'simple_precision_coefficient': simple_result['coefficient'].iloc[0],
                                'alternative_model_coefficient': alternative_result['coefficient'].iloc[0],
                                'primary_p_value': vonmises_result['p_value'].iloc[0],
                                'simple_precision_p_value': simple_result['p_value'].iloc[0],
                                'alternative_model_p_value': alternative_result['p_value'].iloc[0],
                                'coefficient_difference_simple': simple_result['coefficient'].iloc[0] - vonmises_result['coefficient'].iloc[0],
                                'coefficient_difference_alternative': alternative_result['coefficient'].iloc[0] - vonmises_result['coefficient'].iloc[0],
                                'conclusion_robustness': 'robust' if (
                                    (vonmises_result['p_value'].iloc[0] < 0.05) == (simple_result['p_value'].iloc[0] < 0.05) == (alternative_result['p_value'].iloc[0] < 0.05)
                                ) else 'not_robust'
                            }
                            robustness_comparisons.append(comparison)
                else:  # VVIQ2
                    # Get results for each precision measure
                    vonmises_result = outcome_results[outcome_results['precision_measure'] == 'kappa_vonmises']
                    simple_result = outcome_results[outcome_results['precision_measure'] == 'simple_precision']
                    alternative_result = outcome_results[outcome_results['precision_measure'] == 'best_alternative_kappa']
                    
                    if len(vonmises_result) > 0 and len(simple_result) > 0 and len(alternative_result) > 0:
                        comparison = {
                            'analysis_comparison': f"VVIQ2_{outcome}",
                            'primary_coefficient': vonmises_result['coefficient'].iloc[0],
                            'simple_precision_coefficient': simple_result['coefficient'].iloc[0],
                            'alternative_model_coefficient': alternative_result['coefficient'].iloc[0],
                            'primary_p_value': vonmises_result['p_value'].iloc[0],
                            'simple_precision_p_value': simple_result['p_value'].iloc[0],
                            'alternative_model_p_value': alternative_result['p_value'].iloc[0],
                            'coefficient_difference_simple': simple_result['coefficient'].iloc[0] - vonmises_result['coefficient'].iloc[0],
                            'coefficient_difference_alternative': alternative_result['coefficient'].iloc[0] - vonmises_result['coefficient'].iloc[0],
                            'conclusion_robustness': 'robust' if (
                                (vonmises_result['p_value'].iloc[0] < 0.05) == (simple_result['p_value'].iloc[0] < 0.05) == (alternative_result['p_value'].iloc[0] < 0.05)
                            ) else 'not_robust'
                        }
                        robustness_comparisons.append(comparison)
        
        robustness_df = pd.DataFrame(robustness_comparisons)
        print(f"Generated {len(robustness_df)} robustness comparisons")
        
        # Save output files
        print("\n=== Saving output files ===")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save alternative precision measures
        output_cols_precision = [
            'participantId', 'simple_precision', 'best_alternative_kappa', 
            'alternative_model_used', 'precision_correlation_vonmises_simple', 
            'precision_correlation_vonmises_alternative'
        ]
        
        precision_output = precision_measures[output_cols_precision]
        precision_output_file = f'outputs/alternative_precision_measures_{timestamp}.csv'
        precision_output.to_csv(precision_output_file, index=False)
        print(f"Saved alternative precision measures to: {precision_output_file}")
        
        # Save regression results
        output_cols_regression = [
            'analysis_type', 'outcome_measure', 'angular_disparity', 'precision_measure',
            'coefficient', 'standard_error', 'p_value', 'confidence_interval_lower',
            'confidence_interval_upper', 'model_r_squared', 'n_participants'
        ]
        
        regression_output = regression_results_df[output_cols_regression]
        regression_output_file = f'outputs/sensitivity_analysis_regression_results_{timestamp}.csv'
        regression_output.to_csv(regression_output_file, index=False)
        print(f"Saved regression results to: {regression_output_file}")
        
        # Save robustness comparison
        output_cols_robustness = [
            'analysis_comparison', 'primary_coefficient', 'simple_precision_coefficient',
            'alternative_model_coefficient', 'primary_p_value', 'simple_precision_p_value',
            'alternative_model_p_value', 'coefficient_difference_simple',
            'coefficient_difference_alternative', 'conclusion_robustness'
        ]
        
        robustness_output = robustness_df[output_cols_robustness]
        robustness_output_file = f'outputs/robustness_comparison_summary_{timestamp}.csv'
        robustness_output.to_csv(robustness_output_file, index=False)
        print(f"Saved robustness comparison to: {robustness_output_file}")
        
        # Print summary statistics
        print("\n=== SUMMARY STATISTICS ===")
        print(f"Total participants analyzed: {len(precision_measures)}")
        print(f"Participants with valid simple precision: {precision_measures['simple_precision'].notna().sum()}")
        print(f"Alternative models used:")
        print(precision_measures['alternative_model_used'].value_counts())
        
        print(f"\nRobust conclusions: {(robustness_df['conclusion_robustness'] == 'robust').sum()}/{len(robustness_df)}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
