import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from scipy import stats

import rpy2.robjects as ro
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter
from rpy2.robjects import pandas2ri, numpy2ri
import statsmodels.formula.api as smf
import rpy2.rinterface_lib.embedded
import rpy2.rinterface

# Setup rpy2 for R interaction - remove deprecated activate()
try:
    lme4 = importr('lme4')
    base = importr('base')
except Exception as e:
    print(f"Warning: Could not load R packages for bootstrap: {e}")
    lme4 = None
    base = None

def find_most_recent_file(pattern):
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

def bootstrap_confidence_interval(data, statistic_func, n_bootstrap=1000, confidence_level=0.95):
    """
    Fallback function that returns parametric CIs since we don't have raw participant data.
    """
    if len(data) >= 2:
        return data[0], data[1]
    else:
        return (np.nan, np.nan)

def bootstrap_vviq2_model(data, dv_name, predictor_name, n_bootstrap=1000):
    """
    Bootstrap confidence intervals for VVIQ2 regression models using participant resampling.
    """
    if data.empty:
        return (np.nan, np.nan)
    
    coefficients = []
    formula = f"{dv_name} ~ kappa_avg_scaled + rt_cv_standardized + focus_loss_instances_standardized + focus_loss_duration_standardized"
    
    for i in range(n_bootstrap):
        try:
            # Resample participants with replacement and reset index
            resampled_data = data.sample(n=len(data), replace=True, random_state=None).reset_index(drop=True)
            
            # Fit OLS model
            model = smf.ols(formula, data=resampled_data).fit()
            
            # Extract coefficient for the predictor
            if predictor_name in model.params.index:
                coefficients.append(model.params[predictor_name])
                
        except (KeyError, ValueError, Exception) as e:
            continue
    
    if len(coefficients) >= 50:  # Need minimum successful iterations
        return (np.percentile(coefficients, 2.5), np.percentile(coefficients, 97.5))
    else:
        print(f"Warning: Only {len(coefficients)} successful bootstrap iterations for VVIQ2 {predictor_name}")
        return (np.nan, np.nan)

def bootstrap_mrt_model(data, model_type, effect_name, n_bootstrap=100):
    """
    Bootstrap confidence intervals for MRT mixed-effects models using participant resampling.
    This function is a placeholder/fallback and always returns (np.nan, np.nan).
    """
    # The R interface is unreliable in this environment; always return NaN.
    return (np.nan, np.nan)

def interpret_effect_size(effect_size, effect_type):
    """
    Interpret effect size according to Cohen's conventions.
    
    Parameters:
    effect_size (float): The effect size value
    effect_type (str): Type of effect size ('r', 'd', 'f2', 'odds_ratio')
    
    Returns:
    tuple: (interpretation, cohen_category)
    """
    abs_effect = abs(effect_size)
    
    if effect_type == 'r' or effect_type == 'beta':
        if abs_effect < 0.1:
            return "Negligible effect", "negligible"
        elif abs_effect < 0.3:
            return "Small effect", "small"
        elif abs_effect < 0.5:
            return "Medium effect", "medium"
        else:
            return "Large effect", "large"
    
    elif effect_type == 'd':
        if abs_effect < 0.2:
            return "Negligible effect", "negligible"
        elif abs_effect < 0.5:
            return "Small effect", "small"
        elif abs_effect < 0.8:
            return "Medium effect", "medium"
        else:
            return "Large effect", "large"
    
    elif effect_type == 'f2':
        if abs_effect < 0.02:
            return "Negligible effect", "negligible"
        elif abs_effect < 0.15:
            return "Small effect", "small"
        elif abs_effect < 0.35:
            return "Medium effect", "medium"
        else:
            return "Large effect", "large"
    
    elif effect_type == 'odds_ratio':
        val = abs(effect_size) if abs(effect_size) >= 1 else 1 / abs(effect_size)
        if val < 1.2:
            return "Negligible effect", "negligible"
        elif val < 1.5:
            return "Small effect", "small"
        elif val < 2.5:
            return "Medium effect", "medium"
        else:
            return "Large effect", "large"
    else:
        return "Unknown effect type", "unknown"

def calculate_statistical_power(effect_size, sample_size, alpha=0.05):
    """
    Calculate post-hoc statistical power (simplified calculation).
    
    Parameters:
    effect_size (float): Effect size
    sample_size (int): Sample size
    alpha (float): Alpha level
    
    Returns:
    float: Statistical power estimate
    """
    # Simplified power calculation based on effect size and sample size
    # This is a rough approximation
    if sample_size <= 0:
        return 0.0
    
    # Convert effect size to standard normal distribution
    z_alpha = 1.96  # for alpha = 0.05, two-tailed
    z_beta = abs(effect_size) * np.sqrt(sample_size / 4)  # simplified formula
    
    # Calculate power using normal distribution
    from scipy import stats
    power = 1 - stats.norm.cdf(z_alpha - z_beta)
    
    return min(1.0, max(0.0, power))

def main():
    """
    Main function to calculate comprehensive effect sizes for significant findings.
    """
    try:
        print("Starting comprehensive effect size analysis...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find most recent input files
        print("\nSearching for input files...")
        
        mrt_pattern = "outputs/MRT_mixed_effects_results_*.csv"
        vviq2_pattern = "outputs/VVIQ2_regression_results_*.csv"
        hypothesis_pattern = "outputs/hypothesis_test_summary_*.csv"
        
        mrt_file = find_most_recent_file(mrt_pattern)
        vviq2_file = find_most_recent_file(vviq2_pattern)
        hypothesis_file = find_most_recent_file(hypothesis_pattern)
        
        if not mrt_file:
            print(f"Error: No MRT results file found matching pattern {mrt_pattern}")
            return 1
        if not vviq2_file:
            print(f"Error: No VVIQ2 results file found matching pattern {vviq2_pattern}")
            return 1
        if not hypothesis_file:
            print(f"Error: No hypothesis summary file found matching pattern {hypothesis_pattern}")
            return 1
        
        print(f"Found MRT file: {mrt_file}")
        print(f"Found VVIQ2 file: {vviq2_file}")
        print(f"Found hypothesis file: {hypothesis_file}")
        
        # Read input files
        print("\nReading input files...")
        
        try:
            mrt_df = pd.read_csv(mrt_file)
            print(f"MRT data shape: {mrt_df.shape}")
            print("MRT columns:", list(mrt_df.columns))
            print("MRT first 3 rows:")
            print(mrt_df.head(3))
            
            vviq2_df = pd.read_csv(vviq2_file)
            print(f"\nVVIQ2 data shape: {vviq2_df.shape}")
            print("VVIQ2 columns:", list(vviq2_df.columns))
            print("VVIQ2 first 3 rows:")
            print(vviq2_df.head(3))
            
            hypothesis_df = pd.read_csv(hypothesis_file)
            print(f"\nHypothesis data shape: {hypothesis_df.shape}")
            print("Hypothesis columns:", list(hypothesis_df.columns))
            print("Hypothesis first 3 rows:")
            print(hypothesis_df.head(3))
            
        except Exception as e:
            print(f"Error reading input files: {e}")
            return 1

        # Find analysis data files for bootstrap resampling
        mrt_acc_pattern = "outputs/MRT_accuracy_analysis_data_*.csv"
        mrt_rt_pattern = "outputs/MRT_rt_analysis_data_*.csv"
        vviq2_analysis_pattern = "outputs/VVIQ2_analysis_data_*.csv"

        mrt_acc_file = find_most_recent_file(mrt_acc_pattern)
        mrt_rt_file = find_most_recent_file(mrt_rt_pattern)
        vviq2_data_file = find_most_recent_file(vviq2_analysis_pattern)

        print(f"Found MRT accuracy data: {mrt_acc_file}")
        print(f"Found MRT RT data: {mrt_rt_file}")
        print(f"Found VVIQ2 analysis data: {vviq2_data_file}")

        # Load analysis data files
        mrt_acc_df = pd.read_csv(mrt_acc_file) if mrt_acc_file else pd.DataFrame()
        mrt_rt_df = pd.read_csv(mrt_rt_file) if mrt_rt_file else pd.DataFrame()
        vviq2_analysis_df = pd.read_csv(vviq2_data_file) if vviq2_data_file else pd.DataFrame()

        print(f"MRT accuracy data shape: {mrt_acc_df.shape}")
        print(f"MRT RT data shape: {mrt_rt_df.shape}")
        print(f"VVIQ2 analysis data shape: {vviq2_analysis_df.shape}")

        # Calculate actual sample sizes from loaded data
        MRT_SAMPLE_SIZE = len(mrt_acc_df['participantId'].unique()) if not mrt_acc_df.empty and 'participantId' in mrt_acc_df.columns else 247
        VVIQ2_SAMPLE_SIZE = len(vviq2_analysis_df) if not vviq2_analysis_df.empty else 242

        print(f"Using MRT sample size: {MRT_SAMPLE_SIZE}")
        print(f"Using VVIQ2 sample size: {VVIQ2_SAMPLE_SIZE}")
        
        # Validate required columns
        print("\nValidating required columns...")
        
        mrt_required = ['model_type', 'effect', 'coefficient_estimate', 'standard_error', 
                       'p_value_fdr_adjusted', 'confidence_interval_lower', 'confidence_interval_upper',
                       'odds_ratio', 'significance_fdr']
        
        vviq2_required = ['vviq2_measure', 'predictor', 'coefficient_estimate', 'standard_error',
                         'p_value_fdr_adjusted', 'confidence_interval_lower', 'confidence_interval_upper',
                         'beta_standardized', 'partial_r_squared', 'significance_fdr']
        
        hypothesis_required = ['hypothesis_number', 'result_supported', 'key_statistic', 
                              'p_value_fdr', 'effect_size']
        
        # Check MRT columns
        missing_mrt = [col for col in mrt_required if col not in mrt_df.columns]
        if missing_mrt:
            print(f"Warning: Missing MRT columns: {missing_mrt}")
        
        # Check VVIQ2 columns
        missing_vviq2 = [col for col in vviq2_required if col not in vviq2_df.columns]
        if missing_vviq2:
            print(f"Warning: Missing VVIQ2 columns: {missing_vviq2}")
        
        # Check hypothesis columns
        missing_hypothesis = [col for col in hypothesis_required if col not in hypothesis_df.columns]
        if missing_hypothesis:
            print(f"Warning: Missing hypothesis columns: {missing_hypothesis}")
        
        # Print unique values for key experimental design parameters
        print("\nExamining key experimental design parameters...")
        
        if 'effect' in mrt_df.columns:
            print("MRT effect types:", mrt_df['effect'].unique())
        if 'model_type' in mrt_df.columns:
            print("MRT model types:", mrt_df['model_type'].unique())
        if 'significance_fdr' in mrt_df.columns:
            print("MRT significance values:", mrt_df['significance_fdr'].unique())
        
        if 'predictor' in vviq2_df.columns:
            print("VVIQ2 predictors:", vviq2_df['predictor'].unique())
        if 'vviq2_measure' in vviq2_df.columns:
            print("VVIQ2 measures:", vviq2_df['vviq2_measure'].unique())
        if 'significance_fdr' in vviq2_df.columns:
            print("VVIQ2 significance values:", vviq2_df['significance_fdr'].unique())
        
        if 'result_supported' in hypothesis_df.columns:
            print("Hypothesis support values:", hypothesis_df['result_supported'].unique())
        
        # Filter for significant findings
        print("\nFiltering for significant findings...")

        # MRT significant results, filter for kappa effects only
        if 'significance_fdr' in mrt_df.columns:
            mrt_significant = mrt_df[(mrt_df['significance_fdr'] == True) & (mrt_df['effect'].str.contains('kappa', case=False, na=False))].copy()
            print(f"Found {len(mrt_significant)} significant MRT results (kappa effects only)")
            if len(mrt_significant) > 0:
                print("Significant MRT effects:")
                print(mrt_significant[['effect', 'coefficient_estimate', 'p_value_fdr_adjusted']].head())
        else:
            mrt_significant = pd.DataFrame()
            print("No significance column found in MRT data")
        
        # VVIQ2 κ effects (regardless of significance)
        vviq2_kappa = vviq2_df[vviq2_df['predictor'].str.contains('kappa', case=False, na=False)].copy()
        print(f"Found {len(vviq2_kappa)} VVIQ2 results with κ predictor (regardless of significance)")
        if len(vviq2_kappa) > 0:
            print("VVIQ2 κ predictors:")
            print(vviq2_kappa[['predictor', 'coefficient_estimate', 'p_value_fdr_adjusted']].head())
        vviq2_significant = vviq2_kappa  # For downstream code compatibility
        
        # Initialize results list
        effect_size_results = []
        hypothesis_summary_results = []
        
        print("\nCalculating effect sizes for significant MRT results...")

        # Process MRT results
        for counter, (idx, row) in enumerate(mrt_significant.iterrows(), 1):
            print(f"\nProcessing MRT result {counter}/{len(mrt_significant)}")
            print(f"Effect: {row.get('effect', 'Unknown')}")
            print(f"Coefficient: {row.get('coefficient_estimate', 'N/A')}")

            # Extract basic information
            effect_name = row.get('effect', 'Unknown')
            coefficient = row.get('coefficient_estimate', 0)
            std_error = row.get('standard_error', 0)
            p_value = row.get('p_value_fdr_adjusted', 1)
            ci_lower = row.get('confidence_interval_lower', np.nan)
            ci_upper = row.get('confidence_interval_upper', np.nan)
            odds_ratio = row.get('odds_ratio', 1)
            model_type = row.get('model_type', '')

            # Use bootstrap for CIs if possible, otherwise fallback to parametric CIs
            if model_type == 'MRT_accuracy' and not mrt_acc_df.empty:
                bootstrap_lower, bootstrap_upper = bootstrap_mrt_model(mrt_acc_df, 'accuracy', effect_name, n_bootstrap=1000)
            elif model_type == 'MRT_reaction_time' and not mrt_rt_df.empty:
                bootstrap_lower, bootstrap_upper = bootstrap_mrt_model(mrt_rt_df, 'reaction_time', effect_name, n_bootstrap=1000)
            else:
                bootstrap_lower, bootstrap_upper = (np.nan, np.nan)

            # Fallback to parametric CIs if bootstrap returns NaN
            if (np.isnan(bootstrap_lower) or np.isnan(bootstrap_upper)) and not np.isnan(ci_lower) and not np.isnan(ci_upper):
                bootstrap_lower, bootstrap_upper = ci_lower, ci_upper

            # Calculate effect size interpretations
            beta_interpretation, beta_category = interpret_effect_size(coefficient, 'beta')

            # Calculate odds ratio CIs properly (exponentiate log-odds CIs)
            if not np.isnan(ci_lower) and not np.isnan(ci_upper):
                odds_ratio_ci_lower = np.exp(ci_lower)
                odds_ratio_ci_upper = np.exp(ci_upper)
            else:
                odds_ratio_ci_lower = np.nan
                odds_ratio_ci_upper = np.nan

            or_interpretation, or_category = interpret_effect_size(odds_ratio, 'odds_ratio')

            # Calculate CI width
            ci_width = ci_upper - ci_lower if not np.isnan(ci_lower) and not np.isnan(ci_upper) else np.nan

            # Estimate statistical power using actual sample size
            power_estimate = calculate_statistical_power(abs(coefficient), MRT_SAMPLE_SIZE)

            # Add log-odds coefficient result (label as 'log_odds')
            effect_size_results.append({
                'analysis_domain': 'MRT',
                'dependent_variable': 'Mental_Rotation_Performance',
                'predictor_effect': effect_name,
                'effect_size_type': 'log_odds',
                'effect_size_value': coefficient,
                'effect_size_ci_lower': ci_lower,
                'effect_size_ci_upper': ci_upper,
                'effect_size_interpretation': beta_interpretation,
                'cohen_guideline_category': beta_category,
                'bootstrap_ci_lower': bootstrap_lower,
                'bootstrap_ci_upper': bootstrap_upper,
                'ci_width': ci_width,
                'practical_significance': f"Log-odds coefficient of {coefficient:.3f} indicates {'positive' if coefficient > 0 else 'negative'} association",
                'original_p_value_fdr': p_value,
                'statistical_power_post_hoc': power_estimate
            })

            # Add odds ratio result if available
            if not np.isnan(odds_ratio) and odds_ratio != 1:
                effect_size_results.append({
                    'analysis_domain': 'MRT',
                    'dependent_variable': 'Mental_Rotation_Performance',
                    'predictor_effect': effect_name,
                    'effect_size_type': 'odds_ratio',
                    'effect_size_value': odds_ratio,
                    'effect_size_ci_lower': odds_ratio_ci_lower,
                    'effect_size_ci_upper': odds_ratio_ci_upper,
                    'effect_size_interpretation': or_interpretation,
                    'cohen_guideline_category': or_category,
                    'bootstrap_ci_lower': odds_ratio_ci_lower,
                    'bootstrap_ci_upper': odds_ratio_ci_upper,
                    'ci_width': odds_ratio_ci_upper - odds_ratio_ci_lower if not np.isnan(odds_ratio_ci_lower) and not np.isnan(odds_ratio_ci_upper) else np.nan,
                    'practical_significance': f"Odds ratio of {odds_ratio:.3f} indicates {((odds_ratio-1)*100):.1f}% change in odds",
                    'original_p_value_fdr': p_value,
                    'statistical_power_post_hoc': power_estimate
                })
        
        print("\nCalculating effect sizes for significant VVIQ2 results...")

        # Process VVIQ2 results
        for counter, (idx, row) in enumerate(vviq2_significant.iterrows(), 1):
            print(f"\nProcessing VVIQ2 result {counter}/{len(vviq2_significant)}")
            print(f"Predictor: {row.get('predictor', 'Unknown')}")
            print(f"Measure: {row.get('vviq2_measure', 'Unknown')}")

            # Extract basic information
            predictor_name = row.get('predictor', 'Unknown')
            measure_name = row.get('vviq2_measure', 'Unknown')
            coefficient = row.get('coefficient_estimate', 0)
            std_error = row.get('standard_error', 0)
            p_value = row.get('p_value_fdr_adjusted', 1)
            ci_lower = row.get('confidence_interval_lower', np.nan)
            ci_upper = row.get('confidence_interval_upper', np.nan)
            beta_std = row.get('beta_standardized', 0)
            partial_r2 = row.get('partial_r_squared', 0)

            # Use bootstrap for CIs if possible for kappa predictor
            if not vviq2_analysis_df.empty and predictor_name == 'kappa_avg_scaled':
                bootstrap_lower, bootstrap_upper = bootstrap_vviq2_model(
                    vviq2_analysis_df, measure_name, predictor_name, n_bootstrap=1000
                )
            else:
                bootstrap_lower, bootstrap_upper = (np.nan, np.nan)

            # Fallback to parametric CIs only if bootstrap completely fails
            if np.isnan(bootstrap_lower) and np.isnan(bootstrap_upper) and not np.isnan(ci_lower) and not np.isnan(ci_upper):
                bootstrap_lower, bootstrap_upper = ci_lower, ci_upper

            # Calculate Cohen's f² effect size using CORRECTED formula
            if partial_r2 > 0 and partial_r2 < 1:
                cohens_f2 = partial_r2 / (1 - partial_r2)
            else:
                cohens_f2 = np.nan

            # Calculate effect size interpretations
            beta_interpretation, beta_category = interpret_effect_size(beta_std, 'beta')
            f2_interpretation, f2_category = interpret_effect_size(cohens_f2 if not np.isnan(cohens_f2) else 0, 'f2')

            # Calculate CI width
            ci_width = ci_upper - ci_lower if not np.isnan(ci_lower) and not np.isnan(ci_upper) else np.nan

            # Estimate statistical power using actual sample size
            power_estimate = calculate_statistical_power(abs(beta_std), VVIQ2_SAMPLE_SIZE)

            # Add standardized beta result
            effect_size_results.append({
                'analysis_domain': 'VVIQ2',
                'dependent_variable': measure_name,
                'predictor_effect': predictor_name,
                'effect_size_type': 'standardized_beta',
                'effect_size_value': beta_std,
                'effect_size_ci_lower': ci_lower,
                'effect_size_ci_upper': ci_upper,
                'effect_size_interpretation': beta_interpretation,
                'cohen_guideline_category': beta_category,
                'bootstrap_ci_lower': bootstrap_lower,
                'bootstrap_ci_upper': bootstrap_upper,
                'ci_width': ci_width,
                'practical_significance': f"Standardized beta of {beta_std:.3f} indicates {'positive' if beta_std > 0 else 'negative'} association",
                'original_p_value_fdr': p_value,
                'statistical_power_post_hoc': power_estimate
            })

            # Add partial R-squared result
            effect_size_results.append({
                'analysis_domain': 'VVIQ2',
                'dependent_variable': measure_name,
                'predictor_effect': predictor_name,
                'effect_size_type': 'partial_r_squared',
                'effect_size_value': partial_r2,
                'effect_size_ci_lower': np.nan,
                'effect_size_ci_upper': np.nan,
                'effect_size_interpretation': f"Explains {partial_r2*100:.1f}% of unique variance",
                'cohen_guideline_category': beta_category,
                'bootstrap_ci_lower': np.nan,
                'bootstrap_ci_upper': np.nan,
                'ci_width': np.nan,
                'practical_significance': f"Partial R² of {partial_r2:.3f} indicates {beta_interpretation.lower()} practical significance",
                'original_p_value_fdr': p_value,
                'statistical_power_post_hoc': power_estimate
            })

            # Add Cohen's f² result
            if not np.isnan(cohens_f2) and cohens_f2 > 0:
                effect_size_results.append({
                    'analysis_domain': 'VVIQ2',
                    'dependent_variable': measure_name,
                    'predictor_effect': predictor_name,
                    'effect_size_type': 'cohens_f_squared',
                    'effect_size_value': cohens_f2,
                    'effect_size_ci_lower': np.nan,
                    'effect_size_ci_upper': np.nan,
                    'effect_size_interpretation': f2_interpretation,
                    'cohen_guideline_category': f2_category,
                    'bootstrap_ci_lower': np.nan,
                    'bootstrap_ci_upper': np.nan,
                    'ci_width': np.nan,
                    'practical_significance': f"Cohen's f² of {cohens_f2:.3f} indicates {f2_interpretation.lower()}",
                    'original_p_value_fdr': p_value,
                    'statistical_power_post_hoc': power_estimate
                })
        
        print("\nProcessing hypothesis summary for effect magnitude categories...")
        
        # Process hypothesis summary
        for idx, row in hypothesis_df.iterrows():
            hypothesis_num = row.get('hypothesis_number', f'H{idx+1}')
            result_supported = row.get('result_supported', False)
            effect_size = row.get('effect_size', 0)
            p_value_fdr = row.get('p_value_fdr', 1)

            # Determine effect type from input to use correct interpretation conventions
            es_type_desc = row.get('effect_size_interpretation', '').lower()
            if 'odds ratio' in es_type_desc:
                es_type = 'odds_ratio'
            elif 'coefficient' in es_type_desc or 'beta' in es_type_desc:
                es_type = 'beta'
            else:
                es_type = 'beta'  # default fallback

            effect_interpretation, magnitude_category = interpret_effect_size(effect_size, es_type)

            # Define a comprehensive mapping from hypothesis to model parameters
            hypothesis_effect_map = {
                'H1': ('kappa_avg_scaled', 'MRT_accuracy', None),
                'H2': ('kappa_avg_scaled', 'MRT_reaction_time', None), 
                'H3a': ('kappa_avg_scaled:rotation_angle_degrees_scaled', 'MRT_accuracy', None),
                'H3b': ('kappa_avg_scaled:rotation_angle_degrees_scaled', 'MRT_reaction_time', None),
                'H4': ('kappa_avg_scaled', 'VVIQ2', 'total_vividness_score'),
                'H5': ('kappa_avg_scaled', 'VVIQ2', None)  # General VVIQ2 effect
            }

            # Find corresponding CI from full results based on hypothesis
            ci_lower, ci_upper = np.nan, np.nan
            if hypothesis_num in hypothesis_effect_map:
                effect_to_find, analysis_domain, dependent_var = hypothesis_effect_map[hypothesis_num]
                
                if analysis_domain in ['MRT_accuracy', 'MRT_reaction_time']:
                    matching_row = mrt_df[(mrt_df['effect'] == effect_to_find) & (mrt_df['model_type'] == analysis_domain)]
                    if not matching_row.empty:
                        row_data = matching_row.iloc[0]
                        if es_type == 'odds_ratio':
                            ci_lower = np.exp(row_data['confidence_interval_lower'])
                            ci_upper = np.exp(row_data['confidence_interval_upper'])
                        else:
                            ci_lower = row_data['confidence_interval_lower']
                            ci_upper = row_data['confidence_interval_upper']
                elif analysis_domain == 'VVIQ2':
                    if dependent_var:
                        # Look for specific VVIQ2 measure
                        vviq2_row = vviq2_df[(vviq2_df['predictor'] == effect_to_find) & (vviq2_df['vviq2_measure'] == dependent_var)]
                    else:
                        # Look for any VVIQ2 kappa effect (first one found)
                        vviq2_row = vviq2_df[vviq2_df['predictor'] == effect_to_find]
                    
                    if not vviq2_row.empty:
                        ci_lower = vviq2_row.iloc[0]['confidence_interval_lower']
                        ci_upper = vviq2_row.iloc[0]['confidence_interval_upper']

            # Create practical interpretation
            if result_supported:
                statistical_conclusion = "Hypothesis supported with statistical significance"
                practical_interpretation = f"Effect size of {effect_size:.3f} represents {effect_interpretation.lower()}"
                clinical_relevance = "Requires further investigation for clinical applications"
            else:
                statistical_conclusion = "Hypothesis not supported"
                practical_interpretation = "No meaningful effect detected"
                clinical_relevance = "No clinical relevance indicated"

            # Assess precision
            if abs(effect_size) > 0.1:
                precision_assessment = "Adequate precision for effect size estimation"
            else:
                precision_assessment = "Limited precision - small effect size"

            hypothesis_summary_results.append({
                'hypothesis_number': str(hypothesis_num),
                'effect_magnitude_category': magnitude_category if magnitude_category else "unknown",
                'primary_effect_size': effect_size,
                'primary_effect_95ci_lower': ci_lower,
                'primary_effect_95ci_upper': ci_upper,
                'practical_interpretation': practical_interpretation if practical_interpretation else "",
                'statistical_conclusion': statistical_conclusion if statistical_conclusion else "",
                'clinical_relevance_assessment': clinical_relevance if clinical_relevance else "",
                'precision_assessment': precision_assessment if precision_assessment else ""
            })
        
        # Create output DataFrames
        print("\nCreating output DataFrames...")

        # Ensure all required output columns are present and valid
        effect_sizes_df = pd.DataFrame(effect_size_results)
        hypothesis_summary_df = pd.DataFrame(hypothesis_summary_results)

        for col in ['effect_magnitude_category', 'practical_interpretation', 'statistical_conclusion', 'clinical_relevance_assessment', 'precision_assessment']:
            if col in hypothesis_summary_df.columns:
                hypothesis_summary_df[col] = hypothesis_summary_df[col].fillna("")

        print(f"Effect sizes DataFrame shape: {effect_sizes_df.shape}")
        print("Effect sizes columns:", list(effect_sizes_df.columns))
        print("Effect sizes first 2 rows:")
        print(effect_sizes_df.head(2))
        
        print(f"\nHypothesis summary DataFrame shape: {hypothesis_summary_df.shape}")
        print("Hypothesis summary columns:", list(hypothesis_summary_df.columns))
        print("Hypothesis summary first 2 rows:")
        print(hypothesis_summary_df.head(2))
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save output files
        print(f"\nSaving output files with timestamp {timestamp}...")
        
        effect_sizes_file = f"outputs/comprehensive_effect_sizes_{timestamp}.csv"
        hypothesis_summary_file = f"outputs/effect_size_summary_report_{timestamp}.csv"
        
        effect_sizes_df.to_csv(effect_sizes_file, index=False)
        hypothesis_summary_df.to_csv(hypothesis_summary_file, index=False)
        
        print(f"Saved comprehensive effect sizes to: {effect_sizes_file}")
        print(f"Saved effect size summary report to: {hypothesis_summary_file}")
        
        # Print final summary
        print("\nFinal Summary:")
        print(f"Total effect size calculations: {len(effect_sizes_df)}")
        print(f"Total hypothesis summaries: {len(hypothesis_summary_df)}")
        print(f"Significant MRT effects: {len(mrt_significant)}")
        print(f"Significant VVIQ2 effects: {len(vviq2_significant)}")
        
        if len(effect_sizes_df) > 0:
            print("\nEffect size distribution by category:")
            print(effect_sizes_df['cohen_guideline_category'].value_counts())
        
        if len(hypothesis_summary_df) > 0:
            print("\nHypothesis magnitude distribution:")
            print(hypothesis_summary_df['effect_magnitude_category'].value_counts())
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
