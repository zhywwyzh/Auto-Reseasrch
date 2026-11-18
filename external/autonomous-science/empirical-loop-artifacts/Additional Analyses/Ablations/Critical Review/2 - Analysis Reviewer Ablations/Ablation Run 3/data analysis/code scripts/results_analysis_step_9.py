#!/usr/bin/env python3
"""
Alternative Precision Measures Sensitivity Analysis Script

This script implements sensitivity analyses for visual working memory precision measures
by testing alternative precision calculations and assessing robustness of relationships
with mental rotation task performance and visual imagery measures.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Try to import rpy2 for R integration
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri, numpy2ri
    from rpy2.robjects.packages import importr
    R_AVAILABLE = True
    print("R integration available via rpy2")
except ImportError:
    R_AVAILABLE = False
    print("Warning: rpy2 not available, will use statsmodels for regression")

# Import statistical libraries
try:
    import scipy.stats as stats
    from scipy.stats import circstd, circmean
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    from statsmodels.stats.multitest import fdrcorrection
    print("Statistical libraries imported successfully")
except ImportError as e:
    print(f"Error importing statistical libraries: {e}")
    sys.exit(1)


def get_latest_file(pattern):
    """
    Get the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, return most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found latest file for pattern {pattern}: {latest_file}")
    return latest_file


def load_input_files():
    """
    Load all required input files with timestamp matching.
    
    Returns:
    tuple: DataFrames for (vwm_trials, vwm_params, mrt_perf, vviq2_scores, control_vars)
    """
    print("Loading input files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Define file patterns
    patterns = {
        'vwm_trials': 'outputs/vwm_cleaned_trials_*.csv',
        'vwm_params': 'outputs/vwm_mixture_parameters_*.csv', 
        'mrt_perf': 'outputs/mrt_performance_by_disparity_*.csv',
        'vviq2_scores': 'outputs/vviq2_scores_with_predictors_*.csv',
        'control_vars': 'outputs/control_variables_*.csv'
    }
    
    # Load each file
    dataframes = {}
    for name, pattern in patterns.items():
        file_path = get_latest_file(pattern)
        if file_path is None:
            print(f"Error: No files found for pattern {pattern}")
            sys.exit(1)
            
        try:
            df = pd.read_csv(file_path)
            print(f"\nLoaded {name} from {file_path}")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print(f"First 3 rows:")
            print(df.head(3))
            dataframes[name] = df
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            sys.exit(1)
    
    return (dataframes['vwm_trials'], dataframes['vwm_params'], 
            dataframes['mrt_perf'], dataframes['vviq2_scores'], 
            dataframes['control_vars'])


def calculate_circular_std(errors_radians):
    """
    Calculate circular standard deviation for error values in radians.
    
    Parameters:
    errors_radians (array): Error values in radians
    
    Returns:
    float: Circular standard deviation
    """
    if len(errors_radians) == 0:
        return np.nan
    
    # Calculate mean resultant length
    mean_cos = np.mean(np.cos(errors_radians))
    mean_sin = np.mean(np.sin(errors_radians))
    R = np.sqrt(mean_cos**2 + mean_sin**2)
    
    # Use the standard, more accurate formula for circular standard deviation
    if R > 0 and R < 1:
        circular_std = np.sqrt(-2 * np.log(R))
    elif R == 1:
        circular_std = 0.0
    else:
        circular_std = np.nan
    
    return circular_std


def calculate_simple_precision(vwm_trials, vwm_params):
    """
    Calculate simple precision estimate (1/circular standard deviation) for each participant,
    excluding a proportion of trials equal to the guess_rate.
    
    Parameters:
    vwm_trials (DataFrame): VWM cleaned trials data
    vwm_params (DataFrame): VWM mixture parameters data
    
    Returns:
    DataFrame: Participant-level simple precision estimates
    """
    print("\nCalculating simple precision estimates...")
    
    # Merge trials with parameters to get guess rates
    merged = vwm_trials.merge(vwm_params[['participant_id', 'guess_rate']], 
                             on='participant_id', how='left')
    
    print(f"Merged data shape: {merged.shape}")
    print(f"Participants with guess rate data: {merged['guess_rate'].notna().sum()}")
    
    simple_precision_data = []
    
    rng = np.random.default_rng(seed=42)
    
    for participant_id in merged['participant_id'].unique():
        if pd.isna(participant_id):
            continue
            
        participant_data = merged[merged['participant_id'] == participant_id]
        guess_rate = participant_data['guess_rate'].iloc[0]
        
        if pd.isna(guess_rate):
            print(f"Warning: No guess rate for participant {participant_id}")
            continue
        
        # Get error values in degrees
        errors_degrees = participant_data['error_degrees'].dropna()
        
        if len(errors_degrees) == 0:
            print(f"Warning: No error data for participant {participant_id}")
            continue
        
        # Exclude a proportion of trials equal to guess_rate
        n_trials = len(errors_degrees)
        n_keep = int(round(n_trials * (1 - guess_rate)))
        if n_keep < 1:
            print(f"Warning: Too few non-guess trials for participant {participant_id}")
            continue
        # Randomly select n_keep trials to keep
        errors_degrees_kept = errors_degrees.sample(n=n_keep, random_state=42)
        
        # Convert to radians
        errors_radians = np.deg2rad(errors_degrees_kept)
        
        circular_std = calculate_circular_std(errors_radians)
        
        if pd.isna(circular_std) or circular_std <= 0:
            simple_precision = np.nan
        else:
            simple_precision = 1.0 / circular_std
        
        simple_precision_data.append({
            'participant_id': participant_id,
            'simple_precision': simple_precision,
            'n_trials': n_keep,
            'circular_std': circular_std
        })
    
    simple_precision_df = pd.DataFrame(simple_precision_data)
    print(f"Calculated simple precision for {len(simple_precision_df)} participants")
    print(f"Simple precision summary:")
    print(simple_precision_df['simple_precision'].describe())
    
    return simple_precision_df


def calculate_alternative_kappa(vwm_params):
    """
    Calculate best-fitting alternative model parameters.
    
    Parameters:
    vwm_params (DataFrame): VWM mixture parameters data
    
    Returns:
    DataFrame: Alternative kappa values and model information
    """
    print("\nCalculating alternative kappa values...")
    
    alternative_data = []
    
    for _, row in vwm_params.iterrows():
        participant_id = row['participant_id']
        best_model = row.get('best_model', 'von_mises')
        aic_difference = row.get('aic_difference', 0)
        von_mises_kappa = row.get('von_mises_kappa', np.nan)
        wrapped_normal_kappa = row.get('wrapped_normal_kappa_equiv', np.nan)
        wrapped_cauchy_kappa = row.get('wrapped_cauchy_kappa_equiv', np.nan)
        
        # Determine best alternative kappa
        if pd.notna(aic_difference) and aic_difference > 4 and best_model != 'von_mises':
            if best_model == 'wrapped_normal' and pd.notna(wrapped_normal_kappa):
                best_alternative_kappa = wrapped_normal_kappa
                best_alternative_model = 'wrapped_normal'
            elif best_model == 'wrapped_cauchy' and pd.notna(wrapped_cauchy_kappa):
                best_alternative_kappa = wrapped_cauchy_kappa
                best_alternative_model = 'wrapped_cauchy'
            else:
                best_alternative_kappa = von_mises_kappa
                best_alternative_model = 'von_mises'
        else:
            best_alternative_kappa = von_mises_kappa
            best_alternative_model = 'von_mises'
        
        alternative_data.append({
            'participant_id': participant_id,
            'von_mises_kappa': von_mises_kappa,
            'best_alternative_kappa': best_alternative_kappa,
            'best_alternative_model': best_alternative_model,
            'aic_difference': aic_difference
        })
    
    alternative_df = pd.DataFrame(alternative_data)
    print(f"Alternative kappa calculated for {len(alternative_df)} participants")
    print(f"Best alternative models:")
    print(alternative_df['best_alternative_model'].value_counts())
    
    return alternative_df


def run_regression(formula, data, model_type='ols'):
    """
    Run regression using statsmodels.
    
    Parameters:
    formula (str): Formula string (converted from R format)
    data (DataFrame): Data for regression
    model_type (str): 'ols' or 'glm_binomial'
    
    Returns:
    dict: Regression results
    """
    try:
        # Convert R formula to statsmodels format if needed
        if '~' in formula:
            if model_type == 'glm_binomial':
                model = smf.glm(formula, data=data, family=sm.families.Binomial())
                result = model.fit()
                return {
                    'coefficients': result.params.values,
                    'std_errors': result.bse.values,
                    'p_values': result.pvalues.values,
                    'r_squared': result.prsquared if hasattr(result, 'prsquared') else np.nan
                }
            else:
                model = smf.ols(formula, data=data)
                result = model.fit()
                return {
                    'coefficients': result.params.values,
                    'std_errors': result.bse.values,
                    'p_values': result.pvalues.values,
                    'r_squared': result.rsquared
                }
    except Exception as e:
        print(f"Statsmodels regression failed: {e}")
        return None


def run_mrt_accuracy_models(precision_data, mrt_data, control_data, precision_method):
    """
    Run MRT accuracy regression models with specified precision measure.
    
    Parameters:
    precision_data (DataFrame): Precision measures data
    mrt_data (DataFrame): MRT performance data
    control_data (DataFrame): Control variables data
    precision_method (str): Type of precision measure to use
    
    Returns:
    list: Results for each angular disparity
    """
    print(f"\nRunning MRT accuracy models with {precision_method} precision...")
    
    # Merge all data (do NOT merge control_data again, as mrt_data already contains these variables)
    merged_data = mrt_data.merge(precision_data, on='participant_id', how='inner')
    
    print(f"Merged data shape: {merged_data.shape}")
    
    # Define precision variable name
    if precision_method == 'simple':
        precision_var = 'simple_precision'
    elif precision_method == 'alternative':
        precision_var = 'best_alternative_kappa'
    else:
        precision_var = 'von_mises_kappa'
    
    results = []
    disparities = [0, 50, 100, 150]
    
    for disparity in disparities:
        accuracy_col = f'accuracy_{disparity}deg'
        
        if accuracy_col not in merged_data.columns:
            print(f"Warning: {accuracy_col} not found in data")
            continue
        
        # Prepare regression data
        reg_data = merged_data[[
            'participant_id', accuracy_col, precision_var,
            'vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation',
            'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate'
        ]].dropna()
        
        if len(reg_data) < 10:
            print(f"Warning: Insufficient data for {disparity}° model")
            continue
        
        # Run regression using GLM binomial for accuracy
        formula = f"{accuracy_col} ~ {precision_var} + vwm_mean_accuracy_degrees + vwm_rt_coefficient_variation + mrt_rt_coefficient_variation + engagement_index + vwm_timeout_rate"
        
        reg_result = run_regression(formula, reg_data, model_type='glm_binomial')
        
        if reg_result is not None:
            # Find precision coefficient (should be second coefficient after intercept)
            coef_names = [precision_var]  # We know the order from formula
            precision_idx = 1  # Index after intercept
            
            if len(reg_result['coefficients']) > precision_idx:
                kappa_coef = reg_result['coefficients'][precision_idx]
                kappa_se = reg_result['std_errors'][precision_idx]
                kappa_p = reg_result['p_values'][precision_idx]
                
                results.append({
                    'angular_disparity': disparity,
                    'precision_method': precision_method,
                    'kappa_coefficient': kappa_coef,
                    'kappa_se': kappa_se,
                    'kappa_p_value': kappa_p,
                    'n_participants': len(reg_data)
                })
                
                print(f"  {disparity}°: coef={kappa_coef:.4f}, se={kappa_se:.4f}, p={kappa_p:.4f}")
    
    return results


def run_mrt_rt_models(precision_data, mrt_data, control_data, precision_method):
    """
    Run MRT reaction time regression models with specified precision measure.
    
    Parameters:
    precision_data (DataFrame): Precision measures data
    mrt_data (DataFrame): MRT performance data
    control_data (DataFrame): Control variables data
    precision_method (str): Type of precision measure to use
    
    Returns:
    list: Results for each angular disparity
    """
    print(f"\nRunning MRT RT models with {precision_method} precision...")
    
    # Merge all data (do NOT merge control_data again, as mrt_data already contains these variables)
    merged_data = mrt_data.merge(precision_data, on='participant_id', how='inner')
    
    # Define precision variable name
    if precision_method == 'simple':
        precision_var = 'simple_precision'
    elif precision_method == 'alternative':
        precision_var = 'best_alternative_kappa'
    else:
        precision_var = 'von_mises_kappa'
    
    results = []
    disparities = [0, 50, 100, 150]
    
    for disparity in disparities:
        rt_col = f'median_rt_{disparity}deg'
        
        if rt_col not in merged_data.columns:
            print(f"Warning: {rt_col} not found in data")
            continue
        
        # Prepare regression data with log transformation
        reg_data = merged_data[[
            'participant_id', rt_col, precision_var,
            'vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation',
            'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate'
        ]].dropna()
        
        # Log transform RT
        reg_data[f'log_{rt_col}'] = np.log(reg_data[rt_col])
        
        if len(reg_data) < 10:
            print(f"Warning: Insufficient data for {disparity}° RT model")
            continue
        
        # Run regression
        formula = f"log_{rt_col} ~ {precision_var} + vwm_mean_accuracy_degrees + vwm_rt_coefficient_variation + mrt_rt_coefficient_variation + engagement_index + vwm_timeout_rate"
        
        reg_result = run_regression(formula, reg_data)
        
        if reg_result is not None:
            precision_idx = 1  # Index after intercept
            
            if len(reg_result['coefficients']) > precision_idx:
                kappa_coef = reg_result['coefficients'][precision_idx]
                kappa_se = reg_result['std_errors'][precision_idx]
                kappa_p = reg_result['p_values'][precision_idx]
                
                results.append({
                    'angular_disparity': disparity,
                    'precision_method': precision_method,
                    'kappa_coefficient': kappa_coef,
                    'kappa_se': kappa_se,
                    'kappa_p_value': kappa_p,
                    'n_participants': len(reg_data)
                })
                
                print(f"  {disparity}°: coef={kappa_coef:.4f}, se={kappa_se:.4f}, p={kappa_p:.4f}")
    
    return results


def run_vviq2_models(precision_data, vviq2_data, control_data, precision_method):
    """
    Run VVIQ2 regression models with specified precision measure.
    
    Parameters:
    precision_data (DataFrame): Precision measures data
    vviq2_data (DataFrame): VVIQ2 scores data
    control_data (DataFrame): Control variables data
    precision_method (str): Type of precision measure to use
    
    Returns:
    list: Results for total score and subscales
    """
    print(f"\nRunning VVIQ2 models with {precision_method} precision...")
    
    # Merge all data (do NOT merge control_data again, as vviq2_data already contains these variables)
    merged_data = vviq2_data.merge(precision_data, on='participant_id', how='inner')
    
    print(f"Merged data shape: {merged_data.shape}")
    
    # Define precision variable name
    if precision_method == 'simple':
        precision_var = 'simple_precision'
    elif precision_method == 'alternative':
        precision_var = 'best_alternative_kappa'
    else:
        precision_var = 'von_mises_kappa'
    
    results = []
    
    # VVIQ2 outcome variables
    vviq2_outcomes = [
        'vviq2_total_score',
        'vviq2_familiar_person',
        'vviq2_sunrise', 
        'vviq2_shop_front',
        'vviq2_countryside',
        'vviq2_driving',
        'vviq2_beach',
        'vviq2_railway_station',
        'vviq2_garden'
    ]
    
    for outcome in vviq2_outcomes:
        if outcome not in merged_data.columns:
            print(f"Warning: {outcome} not found in data")
            continue
        
        # Prepare regression data
        reg_data = merged_data[[
            'participant_id', outcome, precision_var,
            'vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation',
            'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate'
        ]].dropna()
        
        if len(reg_data) < 10:
            print(f"Warning: Insufficient data for {outcome} model")
            continue
        
        # Run regression
        formula = f"{outcome} ~ {precision_var} + vwm_mean_accuracy_degrees + vwm_rt_coefficient_variation + mrt_rt_coefficient_variation + engagement_index + vwm_timeout_rate"
        
        reg_result = run_regression(formula, reg_data)
        
        if reg_result is not None:
            precision_idx = 1  # Index after intercept
            
            if len(reg_result['coefficients']) > precision_idx:
                kappa_coef = reg_result['coefficients'][precision_idx]
                kappa_se = reg_result['std_errors'][precision_idx]
                kappa_p = reg_result['p_values'][precision_idx]
                
                results.append({
                    'outcome_variable': outcome,
                    'precision_method': precision_method,
                    'kappa_coefficient': kappa_coef,
                    'kappa_se': kappa_se,
                    'kappa_p_value': kappa_p,
                    'n_participants': len(reg_data)
                })
                
                print(f"  {outcome}: coef={kappa_coef:.4f}, se={kappa_se:.4f}, p={kappa_p:.4f}")
    
    return results


def apply_fdr_correction(results_list):
    """
    Apply FDR correction to VVIQ2 subscale analyses.
    
    Parameters:
    results_list (list): List of result dictionaries
    
    Returns:
    list: Results with FDR-corrected p-values
    """
    # Separate total score from subscales
    subscale_results = [r for r in results_list if 'vviq2_total_score' not in r['outcome_variable']]
    total_results = [r for r in results_list if 'vviq2_total_score' in r['outcome_variable']]
    
    if len(subscale_results) > 0:
        # Apply FDR correction to subscales
        p_values = [r['kappa_p_value'] for r in subscale_results]
        rejected, p_corrected = fdrcorrection(p_values, alpha=0.05)
        
        for i, result in enumerate(subscale_results):
            result['kappa_p_value_fdr'] = p_corrected[i]
            result['kappa_p_value'] = p_corrected[i]  # Replace with corrected value
    
    return total_results + subscale_results

def apply_mrt_fdr_correction(mrt_results):
    """Apply FDR correction to MRT results for each precision method separately."""
    corrected_results = []
    
    # Group by precision method
    for method in ['von_mises', 'simple', 'alternative']:
        method_results = [r for r in mrt_results if r['precision_method'] == method]
        
        if len(method_results) > 0:
            p_values = [r['kappa_p_value'] for r in method_results]
            rejected, p_corrected = fdrcorrection(p_values, alpha=0.05)
            
            for i, result in enumerate(method_results):
                result['kappa_p_value_fdr'] = p_corrected[i]
                result['kappa_p_value'] = p_corrected[i]  # Replace with corrected
                
        corrected_results.extend(method_results)
    
    return corrected_results


def calculate_correlations(precision_data):
    """
    Calculate correlations between precision measures.
    
    Parameters:
    precision_data (DataFrame): Combined precision measures
    
    Returns:
    dict: Correlation coefficients
    """
    print("\nCalculating precision measure correlations...")
    
    # Pairwise dropna for each pair
    simple_vm = precision_data[['simple_precision', 'von_mises_kappa']].dropna()
    alt_vm = precision_data[['best_alternative_kappa', 'von_mises_kappa']].dropna()
    
    corr_simple_vm = np.corrcoef(
        simple_vm['simple_precision'], simple_vm['von_mises_kappa']
    )[0, 1] if len(simple_vm) > 1 else np.nan
    
    corr_alt_vm = np.corrcoef(
        alt_vm['best_alternative_kappa'], alt_vm['von_mises_kappa']
    )[0, 1] if len(alt_vm) > 1 else np.nan
    
    print(f"Correlation simple precision vs von Mises kappa: {corr_simple_vm:.3f}")
    print(f"Correlation alternative kappa vs von Mises kappa: {corr_alt_vm:.3f}")
    
    return {
        'precision_correlation_simple_vm': corr_simple_vm,
        'precision_correlation_alt_vm': corr_alt_vm
    }


def compare_robustness(original_results, alternative_results):
    """
    Compare robustness across precision measurement methods.
    
    Parameters:
    original_results (list): Results from original von Mises analysis
    alternative_results (list): Results from alternative precision analysis
    
    Returns:
    dict: Robustness comparison metrics
    """
    print("\nComparing robustness across methods...")
    
    if len(original_results) == 0 or len(alternative_results) == 0:
        return {
            'coefficient_changes': [],
            'significance_maintained': [],
            'robustness_metrics': {},
            'n_total': 0,
            'n_originally_significant': 0,
            'n_robust': 0
        }
    
    coefficient_changes = []
    significance_maintained = []
    n_total = 0
    n_originally_significant = 0
    n_robust = 0
    
    # Match results by key (angular_disparity for MRT or outcome_variable for VVIQ2)
    for alt_result in alternative_results:
        # Find matching original result
        matching_original = None
        
        for orig_result in original_results:
            # Check if this is MRT data (has angular_disparity) or VVIQ2 data (has outcome_variable)
            if 'angular_disparity' in alt_result and 'angular_disparity' in orig_result:
                if alt_result['angular_disparity'] == orig_result['angular_disparity']:
                    matching_original = orig_result
                    break
            elif 'outcome_variable' in alt_result and 'outcome_variable' in orig_result:
                if alt_result['outcome_variable'] == orig_result['outcome_variable']:
                    matching_original = orig_result
                    break
        
        if matching_original is not None:
            n_total += 1
            # Calculate coefficient change
            orig_coef = matching_original['kappa_coefficient']
            alt_coef = alt_result['kappa_coefficient']
            
            if pd.notna(orig_coef) and pd.notna(alt_coef):
                coef_change = abs(alt_coef - orig_coef)
                coefficient_changes.append(coef_change)
                
                # Check significance maintenance (use FDR-corrected p-values if available)
                orig_p = matching_original.get('kappa_p_value_fdr', matching_original.get('kappa_p_value', np.nan))
                alt_p = alt_result.get('kappa_p_value_fdr', alt_result.get('kappa_p_value', np.nan))
                orig_sig = pd.notna(orig_p) and orig_p < 0.05
                alt_sig = pd.notna(alt_p) and alt_p < 0.05
                if orig_sig:
                    n_originally_significant += 1
                sig_maintained = orig_sig == alt_sig
                if sig_maintained and orig_sig:
                    n_robust += 1
                significance_maintained.append(sig_maintained)
                
                alt_result['coefficient_change_from_original'] = coef_change
                alt_result['significance_maintained'] = sig_maintained
    
    # Calculate robustness metrics
    if len(coefficient_changes) > 0:
        mean_coef_change = np.mean(coefficient_changes)
        prop_sig_maintained = np.mean(significance_maintained) if len(significance_maintained) > 0 else 0
    else:
        mean_coef_change = np.nan
        prop_sig_maintained = 0
    
    robustness_metrics = {
        'mean_coefficient_change': mean_coef_change,
        'proportion_significance_maintained': prop_sig_maintained,
        'n_comparisons': len(coefficient_changes)
    }
    
    print(f"Mean coefficient change: {mean_coef_change:.4f}")
    print(f"Proportion significance maintained: {prop_sig_maintained:.3f}")
    
    return {
        'coefficient_changes': coefficient_changes,
        'significance_maintained': significance_maintained,
        'robustness_metrics': robustness_metrics,
        'n_total': n_total,
        'n_originally_significant': n_originally_significant,
        'n_robust': n_robust
    }


def create_robustness_summary(mrt_acc_robust, mrt_rt_robust, vviq2_robust):
    """
    Create overall robustness summary across all analyses.
    
    Parameters:
    mrt_acc_robust (dict): MRT accuracy robustness metrics
    mrt_rt_robust (dict): MRT RT robustness metrics  
    vviq2_robust (dict): VVIQ2 robustness metrics
    
    Returns:
    list: Summary statistics for each analysis domain
    """
    print("\nCreating robustness summary...")
    
    summary_data = []
    
    domains = [
        ('MRT_Accuracy', mrt_acc_robust),
        ('MRT_ReactionTime', mrt_rt_robust),
        ('VVIQ2', vviq2_robust)
    ]
    
    for domain_name, robust_metrics in domains:
        if robust_metrics and 'robustness_metrics' in robust_metrics:
            metrics = robust_metrics['robustness_metrics']
            n_total = robust_metrics.get('n_total', 0)
            n_originally_significant = robust_metrics.get('n_originally_significant', 0)
            n_robust = robust_metrics.get('n_robust', 0)
            mean_coef_change = metrics.get('mean_coefficient_change', np.nan)
            prop_maintained = metrics.get('proportion_significance_maintained', 0)
            
            # Determine robustness rating
            if prop_maintained >= 0.8 and pd.notna(mean_coef_change) and mean_coef_change < 0.1:
                rating = 'High'
            elif prop_maintained >= 0.6:
                rating = 'Moderate' 
            else:
                rating = 'Low'
            
            summary_data.append({
                'analysis_domain': domain_name,
                'total_tests': n_total,
                'originally_significant': n_originally_significant,
                'robust_across_methods': n_robust,
                'robustness_percentage': prop_maintained * 100,
                'mean_coefficient_change': mean_coef_change,
                'overall_robustness_rating': rating
            })
        else:
            summary_data.append({
                'analysis_domain': domain_name,
                'total_tests': 0,
                'originally_significant': 0,
                'robust_across_methods': 0,
                'robustness_percentage': 0,
                'mean_coefficient_change': np.nan,
                'overall_robustness_rating': 'Unknown'
            })
    
    return summary_data


def main():
    """
    Main execution function for alternative precision measures sensitivity analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    print("Starting Alternative Precision Measures Sensitivity Analysis")
    print("=" * 60)
    
    try:
        # Load input files
        vwm_trials, vwm_params, mrt_perf, vviq2_scores, control_vars = load_input_files()
        
        print(f"\nData loaded successfully:")
        print(f"VWM trials: {vwm_trials.shape[0]} rows")
        print(f"VWM parameters: {vwm_params.shape[0]} participants")
        print(f"MRT performance: {mrt_perf.shape[0]} participants") 
        print(f"VVIQ2 scores: {vviq2_scores.shape[0]} participants")
        print(f"Control variables: {control_vars.shape[0]} participants")
        
        # Print unique values for key experimental design parameters
        print("\nKey experimental design parameters:")
        if 'participant_id' in vwm_trials.columns:
            print(f"Unique participants in VWM trials: {vwm_trials['participant_id'].nunique()}")
        
        # Calculate alternative precision measures
        print("\n" + "="*50)
        print("CALCULATING ALTERNATIVE PRECISION MEASURES")
        print("="*50)
        
        # 1. Simple precision estimate
        simple_precision_df = calculate_simple_precision(vwm_trials, vwm_params)
        
        # 2. Best-fitting alternative model parameters
        alternative_kappa_df = calculate_alternative_kappa(vwm_params)
        
        # Merge all precision measures
        precision_data = vwm_params[['participant_id', 'von_mises_kappa']].merge(
            simple_precision_df[['participant_id', 'simple_precision']], 
            on='participant_id', how='outer'
        ).merge(
            alternative_kappa_df[['participant_id', 'best_alternative_kappa', 'best_alternative_model']], 
            on='participant_id', how='outer'
        )
        
        print(f"\nCombined precision data shape: {precision_data.shape}")
        print("First 2 rows of precision data:")
        print(precision_data.head(2))
        
        # Calculate correlations
        correlations = calculate_correlations(precision_data)
        
        # Add correlations to precision data
        precision_data['precision_correlation_simple_vm'] = correlations['precision_correlation_simple_vm']
        precision_data['precision_correlation_alt_vm'] = correlations['precision_correlation_alt_vm']
        
        # Re-run regression models
        print("\n" + "="*50)
        print("RE-RUNNING REGRESSION MODELS")
        print("="*50)
        
        # Run models with different precision measures
        all_mrt_acc_results = []
        all_mrt_rt_results = []
        all_vviq2_results = []
        
        precision_methods = ['von_mises', 'simple', 'alternative']
        
        for method in precision_methods:
            print(f"\n--- Running models with {method} precision ---")
            
            # MRT accuracy models
            mrt_acc_results = run_mrt_accuracy_models(precision_data, mrt_perf, control_vars, method)
            all_mrt_acc_results.extend(mrt_acc_results)
            
            # MRT reaction time models  
            mrt_rt_results = run_mrt_rt_models(precision_data, mrt_perf, control_vars, method)
            all_mrt_rt_results.extend(mrt_rt_results)
            
            # VVIQ2 models
            vviq2_results = run_vviq2_models(precision_data, vviq2_scores, control_vars, method)
            
            # Apply FDR correction to VVIQ2 subscales
            vviq2_results_corrected = apply_fdr_correction(vviq2_results)
            all_vviq2_results.extend(vviq2_results_corrected)
        
        # Apply FDR correction to MRT results
        all_mrt_acc_results = apply_mrt_fdr_correction(all_mrt_acc_results)
        all_mrt_rt_results = apply_mrt_fdr_correction(all_mrt_rt_results)

        # Compare robustness
        print("\n" + "="*50)
        print("ROBUSTNESS ANALYSIS")
        print("="*50)
        
        # Separate original vs alternative results
        original_mrt_acc = [r for r in all_mrt_acc_results if r['precision_method'] == 'von_mises']
        alternative_mrt_acc_simple = [r for r in all_mrt_acc_results if r['precision_method'] == 'simple']
        alternative_mrt_acc_alt = [r for r in all_mrt_acc_results if r['precision_method'] == 'alternative']
        
        original_mrt_rt = [r for r in all_mrt_rt_results if r['precision_method'] == 'von_mises']
        alternative_mrt_rt_simple = [r for r in all_mrt_rt_results if r['precision_method'] == 'simple']
        alternative_mrt_rt_alt = [r for r in all_mrt_rt_results if r['precision_method'] == 'alternative']
        
        original_vviq2 = [r for r in all_vviq2_results if r['precision_method'] == 'von_mises']
        alternative_vviq2_simple = [r for r in all_vviq2_results if r['precision_method'] == 'simple']
        alternative_vviq2_alt = [r for r in all_vviq2_results if r['precision_method'] == 'alternative']
        
        # Calculate robustness metrics (using simple precision as primary alternative)
        mrt_acc_robustness = compare_robustness(original_mrt_acc, alternative_mrt_acc_simple)
        mrt_rt_robustness = compare_robustness(original_mrt_rt, alternative_mrt_rt_simple)
        vviq2_robustness = compare_robustness(original_vviq2, alternative_vviq2_simple)
        
        # Create robustness summary
        robustness_summary = create_robustness_summary(
            mrt_acc_robustness, mrt_rt_robustness, vviq2_robustness
        )
        
        # Save output files
        print("\n" + "="*50)
        print("SAVING OUTPUT FILES")
        print("="*50)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 1. Alternative precision measures
        precision_output = precision_data[['participant_id', 'von_mises_kappa', 'simple_precision', 
                                         'best_alternative_kappa', 'best_alternative_model',
                                         'precision_correlation_simple_vm', 'precision_correlation_alt_vm']]
        
        precision_file = f'outputs/alternative_precision_measures_{timestamp}.csv'
        precision_output.to_csv(precision_file, index=False)
        print(f"Saved alternative precision measures: {precision_file}")
        
        # 2. MRT accuracy sensitivity results
        mrt_acc_df = pd.DataFrame(all_mrt_acc_results)
        if len(mrt_acc_df) > 0:
            # Add missing columns
            if 'coefficient_change_from_original' not in mrt_acc_df.columns:
                mrt_acc_df['coefficient_change_from_original'] = np.nan
            if 'significance_maintained' not in mrt_acc_df.columns:
                mrt_acc_df['significance_maintained'] = False
            
            mrt_acc_file = f'outputs/sensitivity_mrt_accuracy_{timestamp}.csv'
            mrt_acc_df.to_csv(mrt_acc_file, index=False)
            print(f"Saved MRT accuracy sensitivity: {mrt_acc_file}")
        
        # 3. MRT reaction time sensitivity results
        mrt_rt_df = pd.DataFrame(all_mrt_rt_results)
        if len(mrt_rt_df) > 0:
            # Add missing columns
            if 'coefficient_change_from_original' not in mrt_rt_df.columns:
                mrt_rt_df['coefficient_change_from_original'] = np.nan
            if 'significance_maintained' not in mrt_rt_df.columns:
                mrt_rt_df['significance_maintained'] = False
            
            mrt_rt_file = f'outputs/sensitivity_mrt_rt_{timestamp}.csv'
            mrt_rt_df.to_csv(mrt_rt_file, index=False)
            print(f"Saved MRT RT sensitivity: {mrt_rt_file}")
        
        # 4. VVIQ2 sensitivity results
        vviq2_df = pd.DataFrame(all_vviq2_results)
        if len(vviq2_df) > 0:
            # Add missing columns
            if 'coefficient_change_from_original' not in vviq2_df.columns:
                vviq2_df['coefficient_change_from_original'] = np.nan
            if 'significance_maintained' not in vviq2_df.columns:
                vviq2_df['significance_maintained'] = False
            
            vviq2_file = f'outputs/sensitivity_vviq2_{timestamp}.csv'
            vviq2_df.to_csv(vviq2_file, index=False)
            print(f"Saved VVIQ2 sensitivity: {vviq2_file}")
        
        # 5. Robustness summary
        summary_df = pd.DataFrame(robustness_summary)
        summary_file = f'outputs/robustness_summary_{timestamp}.csv'
        summary_df.to_csv(summary_file, index=False)
        print(f"Saved robustness summary: {summary_file}")
        
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        print(f"Total participants analyzed: {len(precision_data)}")
        print(f"MRT accuracy models run: {len(all_mrt_acc_results)}")
        print(f"MRT RT models run: {len(all_mrt_rt_results)}")
        print(f"VVIQ2 models run: {len(all_vviq2_results)}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
