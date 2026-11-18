import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
from statsmodels.stats.multitest import fdrcorrection
import warnings
warnings.filterwarnings('ignore')

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
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def calculate_partial_eta_squared(t_value, df_error):
    """
    Calculate partial eta-squared from t-statistic and degrees of freedom.
    
    Parameters:
    t_value (float): t-statistic
    df_error (float): degrees of freedom for error
    
    Returns:
    float: partial eta-squared value
    """
    if pd.isna(t_value) or pd.isna(df_error) or df_error <= 0:
        return np.nan

    try:
        t_squared = t_value ** 2
        eta_squared = t_squared / (t_squared + df_error)
        if np.isnan(eta_squared) or np.isinf(eta_squared):
            return np.nan
        return eta_squared
    except Exception as e:
        print(f"WARNING: Could not calculate partial eta-squared for t={t_value}, df={df_error}: {e}")
        return np.nan

def calculate_eta_squared_ci(t_value, df_error, alpha=0.05):
    """
    Calculate confidence interval for partial eta-squared using non-central F-distribution.
    
    Parameters:
    t_value (float): t-statistic
    df_error (float): degrees of freedom for error
    alpha (float): significance level (default 0.05 for 95% CI)
    
    Returns:
    tuple: (lower_ci, upper_ci)
    """
    if pd.isna(t_value) or pd.isna(df_error) or df_error <= 0:
        return np.nan, np.nan

    f_stat = t_value ** 2

    try:
        # For partial eta-squared CI using F-distribution
        # Lower bound: solve for lambda such that F(1, df_error, lambda) at (1-alpha/2) = f_stat
        # Upper bound: solve for lambda such that F(1, df_error, lambda) at (alpha/2) = f_stat

        # Approximate CI using non-central F-distribution
        from scipy.optimize import fsolve

        def find_ncp_lower(ncp):
            return stats.ncf.ppf(1 - alpha/2, 1, df_error, ncp) - f_stat

        def find_ncp_upper(ncp):
            return stats.ncf.ppf(alpha/2, 1, df_error, ncp) - f_stat

        # Find non-centrality parameters
        ncp_lower = max(0, fsolve(find_ncp_lower, 0)[0])
        ncp_upper = max(0, fsolve(find_ncp_upper, f_stat)[0])

        # Convert to partial eta-squared
        eta_lower = ncp_lower / (ncp_lower + df_error + 1)
        eta_upper = ncp_upper / (ncp_upper + df_error + 1)

        # Handle NaN or inf
        if np.isnan(eta_lower) or np.isnan(eta_upper) or np.isinf(eta_lower) or np.isinf(eta_upper):
            print(f"WARNING: Eta-squared CI calculation returned NaN/inf for t={t_value}, df={df_error}")
            return np.nan, np.nan

        return max(0.0, eta_lower), min(1.0, eta_upper)
    except Exception as e:
        # Fallback to simpler approximation
        try:
            se_eta = np.sqrt((4 * f_stat * (df_error + 1)**2) / ((f_stat + df_error)**3))
            eta_point = f_stat / (f_stat + df_error)
            t_crit = stats.t.ppf(1 - alpha/2, df_error)
            margin = t_crit * se_eta
            lower = max(0.0, eta_point - margin)
            upper = min(1.0, eta_point + margin)
            if np.isnan(lower) or np.isnan(upper) or np.isinf(lower) or np.isinf(upper):
                print(f"WARNING: Fallback eta-squared CI calculation returned NaN/inf for t={t_value}, df={df_error}")
                return np.nan, np.nan
            return lower, upper
        except Exception as e2:
            print(f"ERROR: Could not calculate eta-squared CI for t={t_value}, df={df_error}: {e2}")
            return np.nan, np.nan

def calculate_beta_ci(beta, std_error, df, alpha=0.05):
    """
    Calculate confidence interval for standardized beta coefficient.
    
    Parameters:
    beta (float): standardized beta coefficient
    std_error (float): standard error of beta
    df (float): degrees of freedom
    alpha (float): significance level (default 0.05 for 95% CI)
    
    Returns:
    tuple: (lower_ci, upper_ci)
    """
    if pd.isna(beta) or pd.isna(std_error) or pd.isna(df) or df <= 0:
        return np.nan, np.nan

    try:
        t_critical = stats.t.ppf(1 - alpha/2, df)
        margin = t_critical * std_error
        lower = beta - margin
        upper = beta + margin
        if np.isnan(lower) or np.isnan(upper) or np.isinf(lower) or np.isinf(upper):
            print(f"WARNING: Beta CI calculation returned NaN/inf for beta={beta}, se={std_error}, df={df}")
            return np.nan, np.nan
        return lower, upper
    except Exception as e:
        print(f"ERROR: Could not calculate beta CI for beta={beta}, se={std_error}, df={df}: {e}")
        return np.nan, np.nan


def classify_effect_size(effect_size, effect_type='beta'):
    """
    Classify effect size magnitude.
    
    Parameters:
    effect_size (float): Effect size value
    effect_type (str): Type of effect size ('beta' or 'eta_squared')
    
    Returns:
    str: Classification (small, medium, large)
    """
    if pd.isna(effect_size):
        return 'unknown'
    
    abs_effect = abs(effect_size)
    
    if effect_type == 'beta':
        if abs_effect < 0.3:
            return 'small'
        elif abs_effect < 0.5:
            return 'medium'
        else:
            return 'large'
    elif effect_type == 'eta_squared':
        if abs_effect < 0.01:
            return 'small'
        elif abs_effect < 0.06:
            return 'medium'
        else:
            return 'large'
    
    return 'unknown'

def normalize_model_name(model_name):
    """Normalize model names for consistent matching between datasets."""
    if model_name == 'MRT_LogRT':
        return 'MRT_Log_RT'
    return model_name

def main():
    """
    Main function to execute the effect size analysis with confidence intervals.
    """
    try:
        print("Starting effect size analysis with confidence intervals...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find input files
        print("\nSearching for input files...")
        
        mrt_mixed_file = find_most_recent_file('outputs/MRT_mixed_effects_results_*.csv')
        vviq2_robust_file = find_most_recent_file('outputs/VVIQ2_robust_regression_results_*.csv')
        mrt_covariate_file = find_most_recent_file('outputs/MRT_covariate_control_models_*.csv')
        vviq2_covariate_file = find_most_recent_file('outputs/VVIQ2_covariate_control_models_*.csv')
        
        print(f"MRT mixed effects file: {mrt_mixed_file}")
        print(f"VVIQ2 robust regression file: {vviq2_robust_file}")
        print(f"MRT covariate control file: {mrt_covariate_file}")
        print(f"VVIQ2 covariate control file: {vviq2_covariate_file}")
        
        if not all([mrt_mixed_file, vviq2_robust_file, mrt_covariate_file, vviq2_covariate_file]):
            print("ERROR: One or more required input files not found")
            return 1
        
        # Load input files
        print("\nLoading input files...")
        
        try:
            mrt_mixed_df = pd.read_csv(mrt_mixed_file)
            print(f"Loaded MRT mixed effects data: {mrt_mixed_df.shape}")
            print("Columns:", list(mrt_mixed_df.columns))
            print("First 3 rows:")
            print(mrt_mixed_df.head(3))
            
            vviq2_robust_df = pd.read_csv(vviq2_robust_file)
            print(f"\nLoaded VVIQ2 robust regression data: {vviq2_robust_df.shape}")
            print("Columns:", list(vviq2_robust_df.columns))
            print("First 3 rows:")
            print(vviq2_robust_df.head(3))
            
            mrt_covariate_df = pd.read_csv(mrt_covariate_file)
            # Strip whitespace to ensure consistent matching
            if 'model_comparison' in mrt_covariate_df.columns:
                mrt_covariate_df['model_comparison'] = mrt_covariate_df['model_comparison'].str.strip()
            print(f"\nLoaded MRT covariate control data: {mrt_covariate_df.shape}")
            print("Columns:", list(mrt_covariate_df.columns))
            print("First 3 rows:")
            print(mrt_covariate_df.head(3))
            
            vviq2_covariate_df = pd.read_csv(vviq2_covariate_file)
            print(f"\nLoaded VVIQ2 covariate control data: {vviq2_covariate_df.shape}")
            print("Columns:", list(vviq2_covariate_df.columns))
            print("First 3 rows:")
            print(vviq2_covariate_df.head(3))
            
        except Exception as e:
            print(f"ERROR loading input files: {e}")
            return 1
        
        # Validate required columns
        required_mrt_mixed_cols = ['model_name', 'effect_type', 'parameter', 'estimate', 'std_error', 't_value', 'p_value']
        required_vviq2_robust_cols = ['model_name', 'dependent_variable', 'standardized_beta', 't_value', 'p_value', 'r_squared']
        required_mrt_covariate_cols = ['model_comparison', 'kappa_coefficient_augmented', 'kappa_p_value_augmented', 'likelihood_ratio_statistic', 'p_value_lr_test']
        required_vviq2_covariate_cols = ['dependent_variable', 'kappa_standardized_beta', 'kappa_p_value', 'p_value_kappa_unique']

        # Add degrees of freedom columns to required columns if present in any input
        possible_df_cols = ['df', 'degrees_freedom', 'df_error', 'df_resid', 'df_denom', 'n_obs']
        for col in possible_df_cols:
            if col in mrt_mixed_df.columns and col not in required_mrt_mixed_cols:
                required_mrt_mixed_cols.append(col)
            if col in vviq2_robust_df.columns and col not in required_vviq2_robust_cols:
                required_vviq2_robust_cols.append(col)
            if col in vviq2_covariate_df.columns and col not in required_vviq2_covariate_cols:
                required_vviq2_covariate_cols.append(col)

        print("\nValidating required columns...")

        missing_cols = []
        for col in required_mrt_mixed_cols:
            if col not in mrt_mixed_df.columns:
                missing_cols.append(f"MRT mixed: {col}")

        for col in required_vviq2_robust_cols:
            if col not in vviq2_robust_df.columns:
                missing_cols.append(f"VVIQ2 robust: {col}")

        for col in required_mrt_covariate_cols:
            if col not in mrt_covariate_df.columns:
                missing_cols.append(f"MRT covariate: {col}")

        for col in required_vviq2_covariate_cols:
            if col not in vviq2_covariate_df.columns:
                missing_cols.append(f"VVIQ2 covariate: {col}")

        if missing_cols:
            print(f"ERROR: Missing required columns: {missing_cols}")
            return 1

        print("All required columns present")
        
        # Print unique values for key design parameters
        print("\nUnique values for key experimental design parameters:")
        
        if 'model_name' in mrt_mixed_df.columns:
            print("MRT mixed model_name values:", mrt_mixed_df['model_name'].unique())
        if 'parameter' in mrt_mixed_df.columns:
            print("MRT mixed parameter values:", mrt_mixed_df['parameter'].unique())
        if 'effect_type' in mrt_mixed_df.columns:
            print("MRT mixed effect_type values:", mrt_mixed_df['effect_type'].unique())
        
        if 'model_name' in vviq2_robust_df.columns:
            print("VVIQ2 robust model_name values:", vviq2_robust_df['model_name'].unique())
        if 'dependent_variable' in vviq2_robust_df.columns:
            print("VVIQ2 robust dependent_variable values:", vviq2_robust_df['dependent_variable'].unique())
        
        if 'model_comparison' in mrt_covariate_df.columns:
            print("MRT covariate model_comparison values:", mrt_covariate_df['model_comparison'].unique())
        
        if 'dependent_variable' in vviq2_covariate_df.columns:
            print("VVIQ2 covariate dependent_variable values:", vviq2_covariate_df['dependent_variable'].unique())
        
        # Initialize output dataframes
        effect_sizes_data = []
        multiple_comparisons_data = []
        final_results_data = []
        
        print("\n=== TASK 1: Calculate effect sizes for mixed-effects models ===")
        
        # Extract fixed effects from MRT models
        print("\nExtracting fixed effects from MRT mixed-effects models...")
        
        # Main effect of kappa_centered
        kappa_main_effects = mrt_mixed_df[mrt_mixed_df['parameter'] == 'kappa_centered'].copy()
        print(f"Found {len(kappa_main_effects)} kappa_centered main effects")
        print("Kappa main effects:")
        print(kappa_main_effects[['model_name', 'parameter', 'estimate', 't_value', 'p_value']])
        
        # Main effect of rotation_angle_factor
        rotation_main_effects = mrt_mixed_df[mrt_mixed_df['parameter'].str.contains('rotation_angle_factor', na=False) & 
                                           ~mrt_mixed_df['parameter'].str.contains(':', na=False)].copy()
        print(f"\nFound {len(rotation_main_effects)} rotation_angle_factor main effects")
        print("Rotation main effects:")
        print(rotation_main_effects[['model_name', 'parameter', 'estimate', 't_value', 'p_value']])
        
        # Interaction effects
        interaction_effects = mrt_mixed_df[mrt_mixed_df['parameter'].str.contains('kappa_centered.*rotation_angle_factor|rotation_angle_factor.*kappa_centered', na=False)].copy()
        print(f"\nFound {len(interaction_effects)} interaction effects")
        print("Interaction effects:")
        print(interaction_effects[['model_name', 'parameter', 'estimate', 't_value', 'p_value']])
        
        # Calculate partial eta-squared for fixed effects
        print("\nCalculating partial eta-squared for fixed effects...")

        # Try to extract degrees of freedom from the data, else fallback to estimate
        def extract_df(effect_row):
            # Try common column names for degrees of freedom
            for col in ['df', 'degrees_freedom', 'df_error', 'df_resid', 'df_denom']:
                if col in effect_row.index and not pd.isna(effect_row[col]):
                    return effect_row[col]
            # Try to infer from other columns if possible
            if 'n_obs' in effect_row.index and not pd.isna(effect_row['n_obs']):
                return effect_row['n_obs'] - 1
            return 147  # fallback

        for _, effect in kappa_main_effects.iterrows():
            df_estimate = extract_df(effect)
            eta_squared = calculate_partial_eta_squared(effect['t_value'], df_estimate)
            eta_ci_lower, eta_ci_upper = calculate_eta_squared_ci(effect['t_value'], df_estimate)

            effect_sizes_data.append({
                'analysis_type': 'MRT_mixed_effects',
                'model_name': effect['model_name'],
                'effect_name': 'kappa_centered_main',
                'effect_size_type': 'partial_eta_squared',
                'effect_size': eta_squared,
                'confidence_interval_lower': eta_ci_lower,
                'confidence_interval_upper': eta_ci_upper,
                'degrees_freedom': df_estimate,
                'original_p_value': effect['p_value'],
                'fdr_adjusted_p_value': np.nan,
                'significant_fdr_corrected': False
            })

        for _, effect in rotation_main_effects.iterrows():
            df_estimate = extract_df(effect)
            eta_squared = calculate_partial_eta_squared(effect['t_value'], df_estimate)
            eta_ci_lower, eta_ci_upper = calculate_eta_squared_ci(effect['t_value'], df_estimate)

            effect_sizes_data.append({
                'analysis_type': 'MRT_mixed_effects',
                'model_name': effect['model_name'],
                'effect_name': f"rotation_main_{effect['parameter']}",
                'effect_size_type': 'partial_eta_squared',
                'effect_size': eta_squared,
                'confidence_interval_lower': eta_ci_lower,
                'confidence_interval_upper': eta_ci_upper,
                'degrees_freedom': df_estimate,
                'original_p_value': effect['p_value'],
                'fdr_adjusted_p_value': np.nan,
                'significant_fdr_corrected': False
            })

        for _, effect in interaction_effects.iterrows():
            df_estimate = extract_df(effect)
            eta_squared = calculate_partial_eta_squared(effect['t_value'], df_estimate)
            eta_ci_lower, eta_ci_upper = calculate_eta_squared_ci(effect['t_value'], df_estimate)

            effect_sizes_data.append({
                'analysis_type': 'MRT_mixed_effects',
                'model_name': effect['model_name'],
                'effect_name': f"kappa_rotation_interaction_{effect['parameter']}",
                'effect_size_type': 'partial_eta_squared',
                'effect_size': eta_squared,
                'confidence_interval_lower': eta_ci_lower,
                'confidence_interval_upper': eta_ci_upper,
                'degrees_freedom': df_estimate,
                'original_p_value': effect['p_value'],
                'fdr_adjusted_p_value': np.nan,
                'significant_fdr_corrected': False
            })

        print(f"Added {len(kappa_main_effects) + len(rotation_main_effects) + len(interaction_effects)} MRT effect sizes")
        
        print("\n=== TASK 2: Compile standardized effect sizes for regression models ===")
        
        # Extract standardized beta coefficients for VVIQ2 models
        print("\nExtracting standardized beta coefficients from VVIQ2 models...")
        
        # Baseline models
        print("Processing baseline VVIQ2 models...")
        for _, model in vviq2_robust_df.iterrows():
            # Estimate degrees of freedom for regression (n - k - 1, using conservative estimate)
            df_estimate_reg = 144

            # Use actual std_error from the data if available
            actual_std_error = model['std_error'] if 'std_error' in model.index else np.nan

            beta_ci_lower, beta_ci_upper = calculate_beta_ci(
                model['standardized_beta'],
                actual_std_error,
                df_estimate_reg
            )

            effect_sizes_data.append({
                'analysis_type': 'VVIQ2_robust_regression',
                'model_name': model['model_name'],
                'effect_name': 'kappa_centered_baseline',
                'effect_size_type': 'standardized_beta',
                'effect_size': model['standardized_beta'],
                'confidence_interval_lower': beta_ci_lower,
                'confidence_interval_upper': beta_ci_upper,
                'degrees_freedom': df_estimate_reg,
                'original_p_value': model['p_value'],
                'fdr_adjusted_p_value': np.nan,
                'significant_fdr_corrected': False
            })

        print(f"Added {len(vviq2_robust_df)} baseline VVIQ2 effect sizes")
        
        # Covariate-controlled models
        print("\nProcessing covariate-controlled VVIQ2 models...")
        for _, model in vviq2_covariate_df.iterrows():
            df_estimate_reg = 144

            # Use actual std_error from the data if available (try multiple column names)
            actual_std_error = model.get('kappa_std_error', model.get('std_error', np.nan))

            beta_ci_lower, beta_ci_upper = calculate_beta_ci(
                model['kappa_standardized_beta'],
                actual_std_error,
                df_estimate_reg
            )

            effect_sizes_data.append({
                'analysis_type': 'VVIQ2_covariate_controlled',
                'model_name': model['dependent_variable'],
                'effect_name': 'kappa_centered_controlled',
                'effect_size_type': 'standardized_beta',
                'effect_size': model['kappa_standardized_beta'],
                'confidence_interval_lower': beta_ci_lower,
                'confidence_interval_upper': beta_ci_upper,
                'degrees_freedom': df_estimate_reg,
                'original_p_value': model['kappa_p_value'],
                'fdr_adjusted_p_value': np.nan,
                'significant_fdr_corrected': False
            })

        print(f"Added {len(vviq2_covariate_df)} covariate-controlled VVIQ2 effect sizes")
        
        print("\n=== TASK 3: Apply multiple comparison corrections ===")
        
        # MRT angle comparisons
        print("\nApplying multiple comparison corrections for MRT angle effects...")

        # For each MRT model, check if there is a significant interaction.
        # If so, apply FDR correction to interaction terms (simple slopes).
        # If not, do not apply FDR correction.

        unique_models = mrt_mixed_df['model_name'].unique()
        for model_name in unique_models:
            model_df = mrt_mixed_df[mrt_mixed_df['model_name'] == model_name]
            # Find interaction effects for this model
            interaction_mask = model_df['parameter'].str.contains('kappa_centered.*rotation_angle_factor|rotation_angle_factor.*kappa_centered', na=False)
            interaction_effects = model_df[interaction_mask]
            has_significant_interaction = (interaction_effects['p_value'] < 0.05).any()
            if has_significant_interaction:
                # Use interaction terms as simple effects for FDR correction
                simple_effects = model_df[interaction_mask].copy()
                if len(simple_effects) > 1:
                    print(f"Applying FDR correction to {len(simple_effects)} interaction (simple slope) effects for model {model_name} (significant interaction present)")
                    angle_p_values = []
                    angle_effect_names = []
                    angle_effect_sizes = []
                    angle_t_values = []
                    angle_df_estimates = []
                    angle_parameters = []
                    for _, effect in simple_effects.iterrows():
                        angle_p_values.append(effect['p_value'])
                        angle_effect_names.append(f"{effect['model_name']}_{effect['parameter']}")
                        angle_t_values.append(effect['t_value'])
                        angle_parameters.append(effect['parameter'])
                        # Calculate effect size robustly
                        df_estimate = None
                        for col in ['df', 'degrees_freedom', 'df_error', 'df_resid', 'df_denom']:
                            if col in effect.index and not pd.isna(effect[col]):
                                df_estimate = effect[col]
                                break
                        if df_estimate is None and 'n_obs' in effect.index and not pd.isna(effect['n_obs']):
                            df_estimate = effect['n_obs'] - 1
                        if df_estimate is None:
                            df_estimate = 147
                        angle_df_estimates.append(df_estimate)
                        eta_squared = calculate_partial_eta_squared(effect['t_value'], df_estimate)
                        angle_effect_sizes.append(eta_squared)
                    # Use statsmodels FDR correction
                    significant_mask, adjusted_p = fdrcorrection(angle_p_values, alpha=0.05)
                    # For reporting, compute critical values and ranks as in the custom function
                    n_tests = len(angle_p_values)
                    ranks = stats.rankdata(angle_p_values, method='ordinal')
                    critical_values = (ranks / n_tests) * 0.05
                    for i, (p_val, adj_p, sig, crit, rank, name, effect_size) in enumerate(zip(
                        angle_p_values, adjusted_p, significant_mask, critical_values, ranks, angle_effect_names, angle_effect_sizes
                    )):
                        multiple_comparisons_data.append({
                            'comparison_family': f'MRT_angle_comparisons_{model_name}',
                            'test_name': name,
                            'original_p_value': p_val,
                            'fdr_rank': rank,
                            'fdr_critical_value': crit,
                            'fdr_adjusted_p_value': adj_p,
                            'significant_after_correction': sig,
                            'effect_size': effect_size,
                            'practical_significance': classify_effect_size(effect_size, 'eta_squared')
                        })
                    # Update effect sizes data with FDR corrections
                    for i, effect_data in enumerate(effect_sizes_data):
                        if effect_data['analysis_type'] == 'MRT_mixed_effects' and effect_data['model_name'] == model_name:
                            for j, param in enumerate(angle_parameters):
                                if effect_data['effect_name'].endswith(param):
                                    effect_sizes_data[i]['fdr_adjusted_p_value'] = adjusted_p[j]
                                    effect_sizes_data[i]['significant_fdr_corrected'] = significant_mask[j]
                                    break
                else:
                    print(f"Not enough interaction (simple slope) effects for FDR correction in model {model_name} (need at least 2). Skipping FDR correction for this model.")
            else:
                print(f"No significant interaction in model {model_name}. Skipping FDR correction for simple effects.")
        
        # VVIQ2 subscale comparisons
        print("\nApplying multiple comparison corrections for VVIQ2 subscale effects...")

        vviq2_p_values = vviq2_robust_df['p_value'].tolist()
        vviq2_effect_names = [f"{row['model_name']}_{row['dependent_variable']}" for _, row in vviq2_robust_df.iterrows()]
        vviq2_effect_sizes = vviq2_robust_df['standardized_beta'].tolist()

        if len(vviq2_p_values) > 1:
            print(f"Applying FDR correction to {len(vviq2_p_values)} VVIQ2 subscale comparisons")
            # Use statsmodels FDR correction
            significant_mask_vviq2, adjusted_p_vviq2 = fdrcorrection(vviq2_p_values, alpha=0.05)
            n_tests = len(vviq2_p_values)
            ranks_vviq2 = stats.rankdata(vviq2_p_values, method='ordinal')
            critical_values_vviq2 = (ranks_vviq2 / n_tests) * 0.05

            for i, (p_val, adj_p, sig, crit, rank, name, effect_size) in enumerate(zip(
                vviq2_p_values, adjusted_p_vviq2, significant_mask_vviq2, critical_values_vviq2, ranks_vviq2, vviq2_effect_names, vviq2_effect_sizes
            )):
                multiple_comparisons_data.append({
                    'comparison_family': 'VVIQ2_subscale_comparisons',
                    'test_name': name,
                    'original_p_value': p_val,
                    'fdr_rank': rank,
                    'fdr_critical_value': crit,
                    'fdr_adjusted_p_value': adj_p,
                    'significant_after_correction': sig,
                    'effect_size': effect_size,
                    'practical_significance': classify_effect_size(effect_size, 'beta')
                })

            # Update effect sizes data with FDR corrections for VVIQ2
            for i, effect_data in enumerate(effect_sizes_data):
                if effect_data['analysis_type'] == 'VVIQ2_robust_regression':
                    for j, (_, row) in enumerate(vviq2_robust_df.iterrows()):
                        if effect_data['model_name'] == row['model_name']:
                            effect_sizes_data[i]['fdr_adjusted_p_value'] = adjusted_p_vviq2[j]
                            effect_sizes_data[i]['significant_fdr_corrected'] = significant_mask_vviq2[j]
                            break
        else:
            print("Not enough VVIQ2 subscale effects for FDR correction (need at least 2). Skipping FDR correction for this family.")
        
        print("\n=== TASK 4: Summarize significant effects ===")
        
        print("\nSummarizing primary analyses (without covariates)...")
        
        # Primary analyses
        primary_significant = []
        for effect in effect_sizes_data:
            if effect['analysis_type'] in ['MRT_mixed_effects', 'VVIQ2_robust_regression']:
                if effect['original_p_value'] < 0.05:
                    primary_significant.append(effect)
        
        print(f"Found {len(primary_significant)} significant primary effects")
        for effect in primary_significant:
            print(f"  {effect['model_name']}: {effect['effect_name']} = {effect['effect_size']:.4f}, p = {effect['original_p_value']:.4f}")
        
        # Control analyses
        print("\nSummarizing control analyses (with covariates)...")
        
        control_significant = []
        for effect in effect_sizes_data:
            if effect['analysis_type'] == 'VVIQ2_covariate_controlled':
                if effect['original_p_value'] < 0.05:
                    control_significant.append(effect)
        
        print(f"Found {len(control_significant)} significant control effects")
        for effect in control_significant:
            print(f"  {effect['model_name']}: {effect['effect_name']} = {effect['effect_size']:.4f}, p = {effect['original_p_value']:.4f}")
        
        print("\n=== TASK 5: Create comprehensive results summary ===")
        
        # Create final results summary
        print("\nCreating comprehensive results summary...")
        
        # Combine results by hypothesis/analysis type
        analysis_summary = {}
        
        # Process MRT results
        # Only one row per unique model_name
        for model_name in mrt_mixed_df['model_name'].unique():
            # Find the main kappa_centered effect for this model
            main_row = mrt_mixed_df[(mrt_mixed_df['model_name'] == model_name) & (mrt_mixed_df['parameter'] == 'kappa_centered')]
            if len(main_row) == 0:
                continue
            row = main_row.iloc[0]
            # Find corresponding effect size
            effect_size_info = None
            for effect in effect_sizes_data:
                if effect['model_name'] == model_name and effect['effect_name'] == 'kappa_centered_main':
                    effect_size_info = effect
                    break
            # Find covariate control info using normalized model names
            normalized_model_name = normalize_model_name(model_name)
            covariate_info = mrt_covariate_df[mrt_covariate_df['model_comparison'] == normalized_model_name]
            survives_covariate = False
            unique_variance = np.nan
            if len(covariate_info) > 0:
                covariate_row = covariate_info.iloc[0]
                survives_covariate = covariate_row['kappa_p_value_augmented'] < 0.05
                # Calculate unique variance using likelihood ratio statistic
                unique_variance = covariate_row['likelihood_ratio_statistic'] / 100
            final_results_data.append({
                'hypothesis': 'MRT_spatial_ability',
                'analysis_type': 'mixed_effects',
                'dependent_variable': model_name,
                'kappa_effect_significant': row['p_value'] < 0.05,
                'standardized_effect_size': effect_size_info['effect_size'] if effect_size_info else np.nan,
                'effect_size_ci_lower': effect_size_info['confidence_interval_lower'] if effect_size_info else np.nan,
                'effect_size_ci_upper': effect_size_info['confidence_interval_upper'] if effect_size_info else np.nan,
                'original_p_value': row['p_value'],
                'fdr_corrected_p_value': effect_size_info['fdr_adjusted_p_value'] if effect_size_info else np.nan,
                'survives_covariate_control': survives_covariate,
                'unique_variance_explained': unique_variance,
                'interpretation': classify_effect_size(
                    effect_size_info['effect_size'] if effect_size_info else np.nan, 'eta_squared'
                )
            })
        
        # Process VVIQ2 results
        for _, row in vviq2_robust_df.iterrows():
            # Find corresponding effect size
            effect_size_info = None
            for effect in effect_sizes_data:
                if effect['model_name'] == row['model_name'] and effect['analysis_type'] == 'VVIQ2_robust_regression':
                    effect_size_info = effect
                    break
            
            # Find covariate control info
            covariate_info = vviq2_covariate_df[vviq2_covariate_df['dependent_variable'] == row['dependent_variable']]
            survives_covariate = False
            unique_variance = np.nan

            if len(covariate_info) > 0:
                covariate_row = covariate_info.iloc[0]
                survives_covariate = covariate_row['p_value_kappa_unique'] < 0.05
                # Use partial_r_squared_kappa for unique variance if available and column exists
                if 'partial_r_squared_kappa' in covariate_row.index and not pd.isna(covariate_row['partial_r_squared_kappa']):
                    unique_variance = covariate_row['partial_r_squared_kappa']

            final_results_data.append({
                'hypothesis': 'VVIQ2_imagery_ability',
                'analysis_type': 'robust_regression',
                'dependent_variable': row['dependent_variable'],
                'kappa_effect_significant': row['p_value'] < 0.05,
                'standardized_effect_size': row['standardized_beta'],
                'effect_size_ci_lower': effect_size_info['confidence_interval_lower'] if effect_size_info else np.nan,
                'effect_size_ci_upper': effect_size_info['confidence_interval_upper'] if effect_size_info else np.nan,
                'original_p_value': row['p_value'],
                'fdr_corrected_p_value': effect_size_info['fdr_adjusted_p_value'] if effect_size_info else np.nan,
                'survives_covariate_control': survives_covariate,
                'unique_variance_explained': unique_variance,
                'interpretation': classify_effect_size(row['standardized_beta'], 'beta')
            })
        
        print(f"Created {len(final_results_data)} final result summaries")
        
        # Save output files
        print("\nSaving output files...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Effect sizes with confidence intervals
        effect_sizes_df = pd.DataFrame(effect_sizes_data)
        effect_sizes_file = f'outputs/effect_sizes_with_confidence_intervals_{timestamp}.csv'
        effect_sizes_df.to_csv(effect_sizes_file, index=False)
        print(f"Saved effect sizes to: {effect_sizes_file}")
        print("Effect sizes data:")
        print("Columns:", list(effect_sizes_df.columns))
        print("First 2 rows:")
        print(effect_sizes_df.head(2))
        
        # Multiple comparison corrections
        multiple_comparisons_df = pd.DataFrame(multiple_comparisons_data)
        multiple_comparisons_file = f'outputs/multiple_comparison_corrections_{timestamp}.csv'
        multiple_comparisons_df.to_csv(multiple_comparisons_file, index=False)
        print(f"\nSaved multiple comparisons to: {multiple_comparisons_file}")
        print("Multiple comparisons data:")
        print("Columns:", list(multiple_comparisons_df.columns))
        print("First 2 rows:")
        print(multiple_comparisons_df.head(2))
        
        # Final results summary
        final_results_df = pd.DataFrame(final_results_data)
        final_results_file = f'outputs/final_results_summary_{timestamp}.csv'
        final_results_df.to_csv(final_results_file, index=False)
        print(f"\nSaved final results to: {final_results_file}")
        print("Final results data:")
        print("Columns:", list(final_results_df.columns))
        print("First 2 rows:")
        print(final_results_df.head(2))
        
        # Print summary statistics
        print("\n=== FINAL SUMMARY ===")
        print(f"Total effect sizes calculated: {len(effect_sizes_data)}")
        print(f"Total multiple comparison corrections: {len(multiple_comparisons_data)}")
        print(f"Total final results: {len(final_results_data)}")
        
        # Count significant effects
        primary_sig_count = sum(1 for result in final_results_data if result['kappa_effect_significant'])
        fdr_sig_count = sum(1 for effect in effect_sizes_data if effect['significant_fdr_corrected'])
        covariate_sig_count = sum(1 for result in final_results_data if result['survives_covariate_control'])
        
        print(f"Significant primary effects: {primary_sig_count}")
        print(f"Effects surviving FDR correction: {fdr_sig_count}")
        print(f"Effects surviving covariate control: {covariate_sig_count}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
