import os
import pandas as pd
import numpy as np
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
from statsmodels.stats.multitest import fdrcorrection

try:
    import rpy2.robjects as robjects
    from rpy2.robjects.packages import importr
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.conversion import localconverter
    R_AVAILABLE = True

    # Helper to install R packages if not present
    def ensure_r_package(pkg_name):
        try:
            return importr(pkg_name)
        except Exception as e:
            print(f"R package '{pkg_name}' not found. Attempting to install...")
            utils = importr('utils')
            try:
                utils.install_packages(pkg_name)
                return importr(pkg_name)
            except Exception as install_e:
                print(f"Failed to install R package '{pkg_name}': {install_e}")
                return None

    # Import or install R packages
    base = ensure_r_package('base')
    stats = ensure_r_package('stats')
    effectsize = ensure_r_package('effectsize')
    performance = ensure_r_package('performance')

    # Only check that packages are loaded
    if all([base, stats, effectsize, performance]):
        print("R integration successfully initialized")
    else:
        print("Warning: Some R packages could not be loaded. Some features may be unavailable.")
except ImportError:
    print("Warning: rpy2 not available, will use Python implementations where possible")
    R_AVAILABLE = False

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
    return max(files, key=os.path.getctime)

def calculate_cohens_f_squared(r_squared_conditional, r_squared_marginal):
    """
    Calculate Cohen's f² from conditional and marginal R-squared values.
    
    Parameters:
    r_squared_conditional (float): Conditional R-squared
    r_squared_marginal (float): Marginal R-squared
    
    Returns:
    float: Cohen's f² effect size
    """
    if r_squared_conditional >= 1.0:
        return np.inf
    return r_squared_conditional / (1 - r_squared_conditional)

def calculate_odds_ratio_ci(estimate, std_error, confidence_level=0.95):
    """
    Calculate odds ratio and confidence intervals from logistic regression coefficients.
    
    Parameters:
    estimate (float): Regression coefficient
    std_error (float): Standard error of coefficient
    confidence_level (float): Confidence level (default 0.95)
    
    Returns:
    tuple: (odds_ratio, ci_low, ci_high)
    """
    z_score = 1.96  # For 95% CI
    if confidence_level != 0.95:
        from scipy.stats import norm
        z_score = norm.ppf(1 - (1 - confidence_level) / 2)
    
    or_estimate = np.exp(estimate)
    ci_low = np.exp(estimate - z_score * std_error)
    ci_high = np.exp(estimate + z_score * std_error)
    
    return or_estimate, ci_low, ci_high

def apply_fdr_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to p-values using statsmodels.
    
    Parameters:
    p_values (array-like): P-values to correct
    alpha (float): FDR threshold (default 0.05)
    
    Returns:
    tuple: (corrected_p_values, significant_flags)
    """
    if p_values is None or len(p_values) == 0:
        return np.array([]), np.array([])
    significant_flags, corrected_p_values = fdrcorrection(p_values, alpha=alpha, method='indep', is_sorted=False)
    return corrected_p_values, significant_flags

def categorize_effect_size(effect_size, effect_type='cohens_f'):
    """
    Categorize effect size magnitude according to Cohen's conventions.
    
    Parameters:
    effect_size (float): Effect size value
    effect_type (str): Type of effect size ('cohens_f', 'cohens_d', 'eta_squared', 'correlation')
    
    Returns:
    str: Effect size magnitude category
    """
    if pd.isna(effect_size):
        return 'unknown'
    
    effect_size = abs(effect_size)
    
    if effect_type == 'cohens_f':
        if effect_size < 0.10:
            return 'negligible'
        elif effect_size < 0.25:
            return 'small'
        elif effect_size < 0.40:
            return 'medium'
        else:
            return 'large'
    elif effect_type == 'cohens_d':
        if effect_size < 0.20:
            return 'negligible'
        elif effect_size < 0.50:
            return 'small'
        elif effect_size < 0.80:
            return 'medium'
        else:
            return 'large'
    elif effect_type == 'eta_squared':
        if effect_size < 0.01:
            return 'negligible'
        elif effect_size < 0.06:
            return 'small'
        elif effect_size < 0.14:
            return 'medium'
        else:
            return 'large'
    elif effect_type == 'correlation':
        if effect_size < 0.10:
            return 'negligible'
        elif effect_size < 0.30:
            return 'small'
        elif effect_size < 0.50:
            return 'medium'
        else:
            return 'large'
    else:
        return 'unknown'

def categorize_effect_size_odds_ratio(odds_ratio):
    """
    Categorize effect size magnitude for odds ratios.
    """
    if pd.isna(odds_ratio):
        return 'unknown'
    effect_magnitude = abs(np.log(odds_ratio))
    if effect_magnitude < np.log(1.5):
        return 'negligible'
    elif effect_magnitude < np.log(2.5):
        return 'small'
    elif effect_magnitude < np.log(4.0):
        return 'medium'
    else:
        return 'large'

def categorize_effect_size_partial_eta_squared(eta2):
    """
    Categorize effect size magnitude for partial eta squared.
    """
    if pd.isna(eta2):
        return 'unknown'
    if eta2 < 0.01:
        return 'negligible'
    elif eta2 < 0.06:
        return 'small'
    elif eta2 < 0.14:
        return 'medium'
    else:
        return 'large'

def calculate_partial_eta_squared(f_statistic, df_effect, df_error):
    """
    Calculate partial eta squared from F-statistic.
    
    Parameters:
    f_statistic (float): F-statistic value
    df_effect (int): Degrees of freedom for effect
    df_error (int): Degrees of freedom for error
    
    Returns:
    float: Partial eta squared
    """
    if pd.isna(f_statistic) or f_statistic <= 0:
        return np.nan
    
    return (f_statistic * df_effect) / (f_statistic * df_effect + df_error)

def process_mrt_models():
    """
    Process MRT mixed-effects models and calculate effect sizes.
    
    Returns:
    pd.DataFrame: Processed MRT effect sizes
    """
    print("\n=== Processing MRT Models ===")
    
    # Find input files
    accuracy_pattern = "outputs/MRT_accuracy_model_results_*.csv"
    rt_pattern = "outputs/MRT_reaction_time_model_results_*.csv"
    fit_pattern = "outputs/MRT_model_fit_statistics_*.csv"

    # Add after the existing pattern definitions
    accuracy_model_pattern = "outputs/MRT_accuracy_model_*.rds"
    rt_model_pattern = "outputs/MRT_reaction_time_model_*.rds"

    accuracy_file = get_latest_file(accuracy_pattern)
    rt_file = get_latest_file(rt_pattern)
    fit_file = get_latest_file(fit_pattern)

    accuracy_model_file = get_latest_file(accuracy_model_pattern)
    rt_model_file = get_latest_file(rt_model_pattern)

    print(f"Found accuracy file: {accuracy_file}")
    print(f"Found RT file: {rt_file}")
    print(f"Found fit file: {fit_file}")
    print(f"Found accuracy model file: {accuracy_model_file}")
    print(f"Found RT model file: {rt_model_file}")
    
    if not all([accuracy_file, rt_file, fit_file]):
        print("Warning: Some MRT input files not found")
        return pd.DataFrame()
    
    # Load data
    accuracy_df = pd.read_csv(accuracy_file)
    rt_df = pd.read_csv(rt_file)
    fit_df = pd.read_csv(fit_file)
    
    print("\nAccuracy model results:")
    print("Columns:", list(accuracy_df.columns))
    print("First 3 rows:")
    print(accuracy_df.head(3))
    
    print("\nRT model results:")
    print("Columns:", list(rt_df.columns))
    print("First 3 rows:")
    print(rt_df.head(3))
    
    print("\nModel fit statistics:")
    print("Columns:", list(fit_df.columns))
    print("First 3 rows:")
    print(fit_df.head(3))
    
    # Check for unique values in key columns
    if 'term' in accuracy_df.columns:
        print("\nUnique terms in accuracy model:", accuracy_df['term'].unique())
    if 'term' in rt_df.columns:
        print("Unique terms in RT model:", rt_df['term'].unique())
    if 'model_type' in fit_df.columns:
        print("Unique model types in fit statistics:", fit_df['model_type'].unique())
    
    # Helper function for standardized coefficients using R
    def get_standardized_params(model_file, model_name):
        """Get standardized parameters from R model using effectsize package."""
        # Check R availability and file existence
        if not R_AVAILABLE or not model_file or not os.path.exists(model_file):
            print(f"Skipping R-based standardization for {model_name} model (R not available or file missing).")
            return pd.DataFrame()
        # Check effectsize package availability
        if 'effectsize' not in globals() or effectsize is None:
            print(f"effectsize package not available for {model_name} model.")
            return pd.DataFrame()
        try:
            # Load the R model
            model = robjects.r['readRDS'](model_file)
            # Calculate standardized parameters using correct R function call
            try:
                std_params = robjects.r['standardize_parameters'](model, method="refit")
            except Exception as r_call_e:
                print(f"Error calling R's standardize_parameters for {model_name} model: {r_call_e}")
                return pd.DataFrame()
            # Convert to pandas DataFrame using modern rpy2 syntax
            with localconverter(robjects.default_converter + pandas2ri.converter):
                df = robjects.conversion.rpy2py(std_params)
            # Only proceed if df is not empty
            if df is None or len(df) == 0:
                print(f"No standardized parameters returned for {model_name} model.")
                return pd.DataFrame()
            # Rename columns to match expected format
            column_mapping = {
                'Parameter': 'term',
                'Std_Coefficient': 'std_coef',
                'CI_low': 'std_coef_ci_low', 
                'CI_high': 'std_coef_ci_high'
            }
            # Only rename columns that exist
            existing_columns = {k: v for k, v in column_mapping.items() if k in df.columns}
            if existing_columns:
                df = df.rename(columns=existing_columns)
            print(f"Successfully calculated standardized coefficients for {model_name} model.")
            return df
        except Exception as e:
            print(f"Could not compute standardized coefficients in R for {model_name} model: {e}")
            return pd.DataFrame()

    # Get standardized coefficients
    std_coefs_acc_df = get_standardized_params(accuracy_model_file, "accuracy")
    std_coefs_rt_df = get_standardized_params(rt_model_file, "reaction_time")
    
    results = []
    
    # Process accuracy model
    print("\n--- Processing Accuracy Model ---")
    accuracy_kappa_effects = accuracy_df[accuracy_df['term'].str.contains('vonMises_kappa', na=False)]
    
    # Get model fit statistics for accuracy model
    accuracy_fit = fit_df[fit_df['model_type'].str.contains('accuracy', case=False, na=False)]
    if not accuracy_fit.empty:
        cond_r2 = accuracy_fit['conditional_r_squared'].iloc[0] if 'conditional_r_squared' in accuracy_fit.columns else np.nan
        marg_r2 = accuracy_fit['marginal_r_squared'].iloc[0] if 'marginal_r_squared' in accuracy_fit.columns else np.nan
        cohens_f2 = calculate_cohens_f_squared(cond_r2, marg_r2)
        print(f"Accuracy model - Conditional R²: {cond_r2:.4f}, Marginal R²: {marg_r2:.4f}, Cohen's f²: {cohens_f2:.4f}")
    else:
        cohens_f2 = np.nan

    for _, row in accuracy_kappa_effects.iterrows():
        # Calculate odds ratios for logistic regression
        or_value, or_ci_low, or_ci_high = calculate_odds_ratio_ci(row['estimate'], row['std_error'])

        # Get standardized coefficient from R calculation
        term = row['term']
        std_coef_row = std_coefs_acc_df[std_coefs_acc_df['term'] == term] if not std_coefs_acc_df.empty else pd.DataFrame()
        
        if not std_coef_row.empty:
            std_coef = std_coef_row['std_coef'].iloc[0]
            std_ci_low = std_coef_row['std_coef_ci_low'].iloc[0] if 'std_coef_ci_low' in std_coef_row.columns else np.nan
            std_ci_high = std_coef_row['std_coef_ci_high'].iloc[0] if 'std_coef_ci_high' in std_coef_row.columns else np.nan
            print(f"Using R-calculated standardized coefficient for {term}: {std_coef:.4f}")
        else:
            # Fallback to estimate if R calculation failed
            std_coef = row['estimate']
            std_ci_low = row['conf_low_95'] if 'conf_low_95' in row else np.nan
            std_ci_high = row['conf_high_95'] if 'conf_high_95' in row else np.nan
            print(f"Using fallback coefficient for {term}: {std_coef:.4f}")

        effect_magnitude = categorize_effect_size_odds_ratio(or_value)

        results.append({
            'effect_name': row['term'],
            'model_type': 'accuracy',
            'standardized_coefficient': std_coef,
            'standardized_coefficient_CI_low': std_ci_low,
            'standardized_coefficient_CI_high': std_ci_high,
            'cohens_f_squared': cohens_f2,
            'odds_ratio': or_value,
            'odds_ratio_CI_low': or_ci_low,
            'odds_ratio_CI_high': or_ci_high,
            'effect_size_magnitude': effect_magnitude,
            'p_value_original': row['p_value'],
            'p_value_fdr_corrected': np.nan,  # Will be calculated later
            'significant_after_fdr': False
        })

    # Process reaction time model
    print("\n--- Processing Reaction Time Model ---")
    rt_kappa_effects = rt_df[rt_df['term'].str.contains('vonMises_kappa', na=False)]

    # Get model fit statistics for RT model - use actual data
    rt_fit = fit_df[fit_df['model_type'].str.contains('reaction_time|rt', case=False, na=False)]
    if not rt_fit.empty:
        try:
            num_obs = int(float(rt_fit['num_observations'].iloc[0]))
            num_participants = int(float(rt_fit['num_participants'].iloc[0]))
            num_fixed_effects = len(rt_df)  # Number of fixed effects from results
            df_error_rt = num_obs - num_participants - num_fixed_effects
        except (ValueError, TypeError):
            df_error_rt = 178  # Fallback if conversion fails
    else:
        df_error_rt = 178  # Fallback based on output
    print(f"RT model degrees of freedom for error (estimated): {df_error_rt}")

    if not rt_fit.empty:
        cond_r2 = rt_fit['conditional_r_squared'].iloc[0] if 'conditional_r_squared' in rt_fit.columns else np.nan
        marg_r2 = rt_fit['marginal_r_squared'].iloc[0] if 'marginal_r_squared' in rt_fit.columns else np.nan
        cohens_f2 = calculate_cohens_f_squared(cond_r2, marg_r2)
        print(f"RT model - Conditional R²: {cond_r2:.4f}, Marginal R²: {marg_r2:.4f}, Cohen's f²: {cohens_f2:.4f}")
    else:
        cohens_f2 = np.nan

    for _, row in rt_kappa_effects.iterrows():
        # Get standardized coefficient from R calculation
        term = row['term']
        std_coef_row = std_coefs_rt_df[std_coefs_rt_df['term'] == term] if not std_coefs_rt_df.empty else pd.DataFrame()
        
        if not std_coef_row.empty:
            std_coef = std_coef_row['std_coef'].iloc[0]
            std_ci_low = std_coef_row['std_coef_ci_low'].iloc[0] if 'std_coef_ci_low' in std_coef_row.columns else np.nan
            std_ci_high = std_coef_row['std_coef_ci_high'].iloc[0] if 'std_coef_ci_high' in std_coef_row.columns else np.nan
            print(f"Using R-calculated standardized coefficient for {term}: {std_coef:.4f}")
        else:
            # Fallback to estimate if R calculation failed
            std_coef = row['estimate']
            std_ci_low = row['conf_low_95'] if 'conf_low_95' in row else np.nan
            std_ci_high = row['conf_high_95'] if 'conf_high_95' in row else np.nan
            print(f"Using fallback coefficient for {term}: {std_coef:.4f}")

        # Calculate partial eta squared from t-value (not f-statistic)
        if 't_value' in row and not pd.isna(row['t_value']):
            t_val = row['t_value']
            partial_eta2 = (t_val**2) / (t_val**2 + df_error_rt)
        else:
            partial_eta2 = np.nan

        effect_magnitude = categorize_effect_size(partial_eta2, 'eta_squared')

        results.append({
            'effect_name': row['term'],
            'model_type': 'reaction_time',
            'standardized_coefficient': std_coef,
            'standardized_coefficient_CI_low': std_ci_low,
            'standardized_coefficient_CI_high': std_ci_high,
            'cohens_f_squared': cohens_f2,
            'partial_eta_squared': partial_eta2,
            'odds_ratio': np.nan,  # Not applicable for linear models
            'odds_ratio_CI_low': np.nan,
            'odds_ratio_CI_high': np.nan,
            'effect_size_magnitude': effect_magnitude,
            'p_value_original': row['p_value'],
            'p_value_fdr_corrected': np.nan,  # Will be calculated later
            'significant_after_fdr': False
        })
    
    # Apply FDR correction for vonMises_kappa rotation angle effects (main + 3 interactions) separately for each model
    print("\n--- Applying FDR Correction ---")
    results_df = pd.DataFrame(results)

    # FDR correction for accuracy model
    acc_mask = results_df['model_type'] == 'accuracy'
    acc_main_kappa = results_df[acc_mask & (results_df['effect_name'] == 'vonMises_kappa_centered')]
    acc_interaction_effects = results_df[acc_mask & results_df['effect_name'].str.contains(r'vonMises_kappa_centered:rotation_angle_factor(?:50|100|150)\.0$', na=False, regex=True)]
    acc_fdr_effects = pd.concat([acc_main_kappa, acc_interaction_effects])

    if not acc_fdr_effects.empty:
        print(f"Found {len(acc_fdr_effects)} vonMises_kappa rotation angle effects for FDR correction in accuracy model")
        print("Effects included:", acc_fdr_effects['effect_name'].tolist())
        p_values = acc_fdr_effects['p_value_original'].values
        corrected_p, significant_flags = apply_fdr_correction(p_values)
        for i, idx in enumerate(acc_fdr_effects.index):
            results_df.loc[idx, 'p_value_fdr_corrected'] = corrected_p[i]
            results_df.loc[idx, 'significant_after_fdr'] = significant_flags[i]
        print(f"After FDR correction (accuracy): {sum(significant_flags)} significant effects")
    else:
        print("No vonMises_kappa rotation angle effects found for FDR correction in accuracy model")

    # FDR correction for reaction_time model
    rt_mask = results_df['model_type'] == 'reaction_time'
    rt_main_kappa = results_df[rt_mask & (results_df['effect_name'] == 'vonMises_kappa_centered')]
    rt_interaction_effects = results_df[rt_mask & results_df['effect_name'].str.contains(r'vonMises_kappa_centered:rotation_angle_factor(?:50|100|150)\.0$', na=False, regex=True)]
    rt_fdr_effects = pd.concat([rt_main_kappa, rt_interaction_effects])

    if not rt_fdr_effects.empty:
        print(f"Found {len(rt_fdr_effects)} vonMises_kappa rotation angle effects for FDR correction in reaction_time model")
        print("Effects included:", rt_fdr_effects['effect_name'].tolist())
        p_values = rt_fdr_effects['p_value_original'].values
        corrected_p, significant_flags = apply_fdr_correction(p_values)
        for i, idx in enumerate(rt_fdr_effects.index):
            results_df.loc[idx, 'p_value_fdr_corrected'] = corrected_p[i]
            results_df.loc[idx, 'significant_after_fdr'] = significant_flags[i]
        print(f"After FDR correction (reaction_time): {sum(significant_flags)} significant effects")
    else:
        print("No vonMises_kappa rotation angle effects found for FDR correction in reaction_time model")

    print(f"\nProcessed {len(results_df)} MRT effects")
    return results_df

def process_vviq2_models():
    """
    Process VVIQ2 regression models and calculate effect sizes.
    
    Returns:
    pd.DataFrame: Processed VVIQ2 effect sizes
    """
    print("\n=== Processing VVIQ2 Models ===")
    
    # Find input files
    total_pattern = "outputs/VVIQ2_total_regression_results_*.csv"
    subscale_pattern = "outputs/VVIQ2_subscale_regression_results_*.csv"

    # Add model file loading
    vviq2_model_pattern = "outputs/VVIQ2_total_model_*.pkl"
    vviq2_model_file = get_latest_file(vviq2_model_pattern)

    print(f"Found VVIQ2 model file: {vviq2_model_file}")

    # Load VVIQ2 model if available
    vviq2_model = None
    if vviq2_model_file and os.path.exists(vviq2_model_file):
        try:
            import pickle
            with open(vviq2_model_file, 'rb') as f:
                vviq2_model = pickle.load(f)
            print("Successfully loaded VVIQ2 model object")
        except Exception as e:
            print(f"Could not load VVIQ2 model: {e}")
            vviq2_model = None

    total_file = get_latest_file(total_pattern)
    subscale_file = get_latest_file(subscale_pattern)
    
    print(f"Found total VVIQ2 file: {total_file}")
    print(f"Found subscale VVIQ2 file: {subscale_file}")
    
    if not all([total_file, subscale_file]):
        print("Warning: Some VVIQ2 input files not found")
        return pd.DataFrame()
    
    # Load data
    total_df = pd.read_csv(total_file)
    subscale_df = pd.read_csv(subscale_file)
    
    print("\nTotal VVIQ2 regression results:")
    print("Columns:", list(total_df.columns))
    print("First 3 rows:")
    print(total_df.head(3))
    
    print("\nSubscale VVIQ2 regression results:")
    print("Columns:", list(subscale_df.columns))
    print("First 3 rows:")
    print(subscale_df.head(3))
    if subscale_df.empty:
        print("Subscale analysis was skipped due to non-significant primary effect in total VVIQ2 model")
    
    # Check for unique values in key columns
    if 'term' in total_df.columns:
        print("\nUnique terms in total model:", total_df['term'].unique())
    if 'subscale_name' in subscale_df.columns:
        print("Unique subscale names:", subscale_df['subscale_name'].unique())
    
    results = []
    
    # Process total VVIQ2 model
    print("\n--- Processing Total VVIQ2 Model ---")
    kappa_effects_total = total_df[total_df['term'].str.contains('vonMises_kappa', na=False)]

    # Calculate degrees of freedom for VVIQ2 model
    # Assume: N = 190, predictors = 4, intercept = 1, so df_error = 190 - 4 - 1 = 185
    df_error_vviq2 = 190 - 4 - 1
    print(f"VVIQ2 model degrees of freedom for error: {df_error_vviq2}")

    if not kappa_effects_total.empty:
        for _, row in kappa_effects_total.iterrows():
            # Calculate Cohen's f² from R-squared
            r_squared = row['r_squared_adjusted'] if 'r_squared_adjusted' in row else np.nan
            cohens_f2 = r_squared / (1 - r_squared) if not pd.isna(r_squared) and r_squared < 1 else np.nan

            # Calculate partial eta squared from the t-statistic for the specific predictor
            if 't_value' in row and not pd.isna(row['t_value']):
                t_val = row['t_value']
                partial_eta2 = (t_val**2) / (t_val**2 + df_error_vviq2)
            else:
                partial_eta2 = np.nan

            # Standardized coefficient (assume estimate is standardized for regression)
            std_coef = row['estimate']
            std_ci_low = row['conf_low_95'] if 'conf_low_95' in row else np.nan
            std_ci_high = row['conf_high_95'] if 'conf_high_95' in row else np.nan

            # Partial correlation (approximation from t-value)
            if 't_value' in row:
                t_val = row['t_value']
                partial_r = t_val / np.sqrt(t_val**2 + df_error_vviq2) if not pd.isna(t_val) else np.nan
            else:
                partial_r = np.nan

            effect_magnitude = categorize_effect_size(cohens_f2, 'cohens_f')
            practical_significance = 'meaningful' if effect_magnitude in ['medium', 'large'] else 'limited'

            # Add p-value if available
            p_value = row['p_value'] if 'p_value' in row else np.nan

            results.append({
                'analysis_type': 'total_vviq2',
                'subscale_name': 'total',
                'cohens_f_squared': cohens_f2,
                'partial_eta_squared': partial_eta2,
                'partial_correlation': partial_r,
                'standardized_coefficient': std_coef,
                'standardized_coefficient_CI_low': std_ci_low,
                'standardized_coefficient_CI_high': std_ci_high,
                'effect_size_magnitude': effect_magnitude,
                'practical_significance': practical_significance,
                'p_value_original': p_value,
                'p_value_fdr_corrected': np.nan,  # Not used for total
                'significant_after_fdr': False    # Not used for total
            })
    
    # Process subscale models
    print("\n--- Processing VVIQ2 Subscale Models ---")
    
    for _, row in subscale_df.iterrows():
        # Calculate Cohen's f² from R-squared
        r_squared = row['r_squared_adjusted'] if 'r_squared_adjusted' in row else np.nan
        cohens_f2 = r_squared / (1 - r_squared) if not pd.isna(r_squared) and r_squared < 1 else np.nan

        # Partial correlation (approximation from t-value)
        if 'kappa_t_value' in row:
            t_val = row['kappa_t_value']
            # Use same df_error as above for subscales
            partial_r = t_val / np.sqrt(t_val**2 + df_error_vviq2) if not pd.isna(t_val) else np.nan
        else:
            partial_r = np.nan

        # Standardized coefficient
        std_coef = row['kappa_estimate'] if 'kappa_estimate' in row else np.nan

        # Calculate CI for standardized coefficient
        if 'kappa_std_error' in row:
            std_error = row['kappa_std_error']
            std_ci_low = std_coef - 1.96 * std_error
            std_ci_high = std_coef + 1.96 * std_error
        else:
            std_ci_low = np.nan
            std_ci_high = np.nan

        effect_magnitude = categorize_effect_size(cohens_f2, 'cohens_f')

        # Check if significant after FDR correction
        is_significant = row.get('kappa_significant_fdr', False)
        practical_significance = 'meaningful' if is_significant and effect_magnitude in ['medium', 'large'] else 'limited'

        # Add p-value if available
        p_value = row['kappa_p_value'] if 'kappa_p_value' in row else np.nan
        p_value_fdr = row['kappa_p_value_fdr'] if 'kappa_p_value_fdr' in row else np.nan

        results.append({
            'analysis_type': 'subscale_vviq2',
            'subscale_name': row['subscale_name'],
            'cohens_f_squared': cohens_f2,
            'partial_eta_squared': np.nan,  # Not calculated for individual subscales
            'partial_correlation': partial_r,
            'standardized_coefficient': std_coef,
            'standardized_coefficient_CI_low': std_ci_low,
            'standardized_coefficient_CI_high': std_ci_high,
            'effect_size_magnitude': effect_magnitude,
            'practical_significance': practical_significance,
            'p_value_original': p_value,
            'p_value_fdr_corrected': p_value_fdr,
            'significant_after_fdr': is_significant
        })
    
    results_df = pd.DataFrame(results)
    print(f"\nProcessed {len(results_df)} VVIQ2 effects")
    return results_df

def create_comprehensive_summary(mrt_results, vviq2_results):
    """
    Create comprehensive results summary integrating all analyses.
    
    Parameters:
    mrt_results (pd.DataFrame): MRT effect size results
    vviq2_results (pd.DataFrame): VVIQ2 effect size results
    
    Returns:
    pd.DataFrame: Comprehensive summary
    """
    print("\n=== Creating Comprehensive Summary ===")
    
    summary_results = []
    
    # Process MRT results
    for _, row in mrt_results.iterrows():
        # Determine statistical significance
        p_corrected = row['p_value_fdr_corrected']
        if pd.isna(p_corrected):
            p_val = row['p_value_original']
            sig_status = 'significant' if p_val < 0.05 else 'not_significant'
            multiple_corrected = False
        else:
            sig_status = 'significant' if row['significant_after_fdr'] else 'not_significant'
            multiple_corrected = True
        
        # Effect size value and CI
        if row['model_type'] == 'accuracy':
            effect_value = row['odds_ratio']
            ci_low = row['odds_ratio_CI_low']
            ci_high = row['odds_ratio_CI_high']
            effect_interpretation = f"Odds ratio: {effect_value:.3f}, {row['effect_size_magnitude']} effect"
        else:  # reaction_time model
            effect_value = row['partial_eta_squared'] if 'partial_eta_squared' in row else np.nan
            ci_low = np.nan  # CI for eta-squared is not calculated
            ci_high = np.nan
            effect_interpretation = f"Partial Eta Squared: {effect_value:.3f}, {row['effect_size_magnitude']} effect"
        
        # Practical significance
        practical_rating = 'high' if row['effect_size_magnitude'] in ['large'] else \
                          'moderate' if row['effect_size_magnitude'] in ['medium'] else 'low'
        
        # Hypothesis support
        hypothesis_support = 'supported' if sig_status == 'significant' and practical_rating in ['moderate', 'high'] else 'limited_support'
        
        summary_results.append({
            'analysis_domain': 'MRT',
            'effect_description': f"{row['model_type']} model - {row['effect_name']}",
            'statistical_significance': sig_status,
            'effect_size_value': effect_value,
            'effect_size_CI_low': ci_low,
            'effect_size_CI_high': ci_high,
            'effect_size_interpretation': effect_interpretation,
            'practical_significance_rating': practical_rating,
            'multiple_comparisons_corrected': multiple_corrected,
            'hypothesis_support': hypothesis_support
        })
    
    # Process VVIQ2 results
    subscale_results_exist = not vviq2_results[vviq2_results['analysis_type'] == 'subscale_vviq2'].empty
    for _, row in vviq2_results.iterrows():
        # Statistical significance: use actual p-values if available
        if not pd.isna(row.get('p_value_fdr_corrected', np.nan)):
            # Use FDR-corrected significance for subscales
            sig_status = 'significant' if row.get('significant_after_fdr', False) else 'not_significant'
            multiple_corrected = True
        elif not pd.isna(row.get('p_value_original', np.nan)):
            # Use original p-value for total
            sig_status = 'significant' if row.get('p_value_original', 1.0) < 0.05 else 'not_significant'
            multiple_corrected = False
        else:
            # Fallback to practical_significance if no p-value
            sig_status = 'significant' if row['practical_significance'] == 'meaningful' else 'not_significant'
            multiple_corrected = False

        # Effect size value and CI
        effect_value = row['cohens_f_squared']
        ci_low = np.nan  # Not calculated for Cohen's f²
        ci_high = np.nan

        if row['analysis_type'] == 'total_vviq2':
            effect_interpretation = f"Cohen's f²: {effect_value:.3f}, {row['effect_size_magnitude']} effect (total VVIQ2)"
        else:
            effect_interpretation = f"Cohen's f²: {effect_value:.3f}, {row['effect_size_magnitude']} effect ({row['subscale_name']} subscale)"

        # Practical significance
        practical_rating = 'high' if row['effect_size_magnitude'] in ['large'] else \
                          'moderate' if row['effect_size_magnitude'] in ['medium'] else 'low'

        # Hypothesis support
        hypothesis_support = 'supported' if sig_status == 'significant' and practical_rating in ['moderate', 'high'] else 'limited_support'

        summary_results.append({
            'analysis_domain': 'VVIQ2',
            'effect_description': f"{row['analysis_type']} - {row['subscale_name']}",
            'statistical_significance': sig_status,
            'effect_size_value': effect_value,
            'effect_size_CI_low': ci_low,
            'effect_size_CI_high': ci_high,
            'effect_size_interpretation': effect_interpretation,
            'practical_significance_rating': practical_rating,
            'multiple_comparisons_corrected': multiple_corrected,
            'hypothesis_support': hypothesis_support
        })

    # Add explanatory entry if no subscale analysis was performed
    if not subscale_results_exist:
        summary_results.append({
            'analysis_domain': 'VVIQ2',
            'effect_description': 'Subscale Analysis',
            'statistical_significance': 'not_applicable',
            'effect_size_value': np.nan,
            'effect_size_CI_low': np.nan,
            'effect_size_CI_high': np.nan,
            'effect_size_interpretation': 'Analysis not performed due to non-significant primary effect in total VVIQ2 model.',
            'practical_significance_rating': 'not_applicable',
            'multiple_comparisons_corrected': False,
            'hypothesis_support': 'not_applicable'
        })
    
    summary_df = pd.DataFrame(summary_results)
    print(f"\nCreated comprehensive summary with {len(summary_df)} effects")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("Statistical significance counts:")
    print(summary_df['statistical_significance'].value_counts())
    print("\nPractical significance ratings:")
    print(summary_df['practical_significance_rating'].value_counts())
    print("\nHypothesis support:")
    print(summary_df['hypothesis_support'].value_counts())
    
    return summary_df

def main():
    """
    Main function to execute the effect size analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting effect size analysis pipeline...")
        print(f"Current working directory: {os.getcwd()}")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Process MRT models
        mrt_results = process_mrt_models()
        
        # Process VVIQ2 models
        vviq2_results = process_vviq2_models()
        
        # Create comprehensive summary
        comprehensive_summary = create_comprehensive_summary(mrt_results, vviq2_results)
        
        # Save results
        print("\n=== Saving Results ===")
        
        # Save MRT effect sizes
        if not mrt_results.empty:
            mrt_output_file = f"outputs/MRT_effect_sizes_{timestamp}.csv"
            if 'partial_eta_squared' in mrt_results.columns:
                mrt_results_clean = mrt_results.drop('partial_eta_squared', axis=1)
            else:
                mrt_results_clean = mrt_results
            mrt_results_clean.to_csv(mrt_output_file, index=False)
            print(f"Saved MRT effect sizes to: {mrt_output_file}")
            print("MRT results preview:")
            print(mrt_results_clean.head(2))
        
        # Save VVIQ2 effect sizes
        if not vviq2_results.empty:
            vviq2_output_file = f"outputs/VVIQ2_effect_sizes_{timestamp}.csv"
            # Only include required columns, exclude p-value columns
            required_columns = [
                'analysis_type', 'subscale_name', 'cohens_f_squared', 'partial_eta_squared',
                'partial_correlation', 'standardized_coefficient', 'standardized_coefficient_CI_low',
                'standardized_coefficient_CI_high', 'effect_size_magnitude', 'practical_significance'
            ]
            # Only keep columns that exist in the DataFrame
            filtered_columns = [col for col in required_columns if col in vviq2_results.columns]
            vviq2_results_filtered = vviq2_results[filtered_columns]
            vviq2_results_filtered.to_csv(vviq2_output_file, index=False)
            print(f"Saved VVIQ2 effect sizes to: {vviq2_output_file}")
            print("VVIQ2 results preview:")
            print(vviq2_results_filtered.head(2))
        
        # Save comprehensive summary
        if not comprehensive_summary.empty:
            summary_output_file = f"outputs/comprehensive_results_summary_{timestamp}.csv"
            comprehensive_summary.to_csv(summary_output_file, index=False)
            print(f"Saved comprehensive summary to: {summary_output_file}")
            print("Comprehensive summary preview:")
            print(comprehensive_summary.head(2))
        
        print("\nEffect size analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in effect size analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
