#!/usr/bin/env python3
"""
Effect Size Calculation Script for MRT and VVIQ2 Analyses

This script calculates standardized effect sizes for:
1. Mixed-effects models (MRT accuracy GLMM, MRT RT LMM)
2. VVIQ2 regression analyses 
3. Bivariate correlations

The script processes input files with statistical results and raw data to compute
effect sizes with confidence intervals and interpretations.
"""

import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import scipy.stats as stats
from scipy.stats import pearsonr
import statsmodels.formula.api as smf
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern with <TIMESTAMP> placeholder
        
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    files = glob.glob(search_pattern)
    
    if not files:
        return None
    
    # Get the most recent file by modification time
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def interpret_eta_squared(eta_squared):
    """
    Interpret eta-squared effect size magnitude.
    
    Parameters:
    -----------
    eta_squared : float
        Eta-squared value
        
    Returns:
    --------
    str
        Interpretation of effect size magnitude
    """
    if eta_squared < 0.01:
        return "negligible"
    elif eta_squared < 0.06:
        return "small"
    elif eta_squared < 0.14:
        return "medium"
    else:
        return "large"

def interpret_correlation(r):
    """
    Interpret correlation coefficient magnitude.
    
    Parameters:
    -----------
    r : float
        Correlation coefficient
        
    Returns:
    --------
    str
        Interpretation of correlation magnitude
    """
    abs_r = abs(r)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "small"
    elif abs_r < 0.5:
        return "medium"
    else:
        return "large"

def interpret_standardized_beta(beta):
    """
    Interpret standardized beta coefficient magnitude.
    
    Parameters:
    -----------
    beta : float
        Standardized beta coefficient
        
    Returns:
    --------
    str
        Interpretation of beta magnitude
    """
    abs_beta = abs(beta)
    if abs_beta < 0.1:
        return "negligible"
    elif abs_beta < 0.3:
        return "small"
    elif abs_beta < 0.5:
        return "medium"
    else:
        return "large"

def interpret_odds_ratio(or_value):
    """
    Interpret odds ratio effect size magnitude.
    
    Parameters:
    -----------
    or_value : float
        Odds ratio value
        
    Returns:
    --------
    str
        Interpretation of odds ratio magnitude
    """
    if or_value < 1:
        val = 1 / or_value
    else:
        val = or_value
    
    if val < 1.2:
        return "negligible"
    elif val < 1.5:
        return "small"
    elif val < 3.0:
        return "medium"
    else:
        return "large"

def bootstrap_correlation_ci(x, y, n_bootstrap=1000, alpha=0.05):
    """
    Calculate bootstrap confidence intervals for correlation coefficient.
    
    Parameters:
    -----------
    x, y : array-like
        Variables to correlate
    n_bootstrap : int
        Number of bootstrap samples
    alpha : float
        Alpha level for confidence interval
        
    Returns:
    --------
    tuple
        (correlation, lower_ci, upper_ci)
    """
    # Remove missing values
    valid_mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[valid_mask]
    y_clean = y[valid_mask]
    
    if len(x_clean) < 3:
        return np.nan, np.nan, np.nan
    
    # Original correlation
    r_orig, _ = pearsonr(x_clean, y_clean)
    
    # Bootstrap correlations
    n = len(x_clean)
    bootstrap_rs = []
    
    for _ in range(n_bootstrap):
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = x_clean[indices]
        y_boot = y_clean[indices]
        
        try:
            r_boot, _ = pearsonr(x_boot, y_boot)
            if not np.isnan(r_boot):
                bootstrap_rs.append(r_boot)
        except:
            continue
    
    if len(bootstrap_rs) < 100:
        # Fall back to Fisher's z-transformation
        return fisher_z_ci(r_orig, n)
    
    # Calculate confidence intervals
    lower_percentile = 100 * (alpha / 2)
    upper_percentile = 100 * (1 - alpha / 2)
    
    ci_lower = np.percentile(bootstrap_rs, lower_percentile)
    ci_upper = np.percentile(bootstrap_rs, upper_percentile)
    
    return r_orig, ci_lower, ci_upper

def fisher_z_ci(r, n, alpha=0.05):
    """
    Calculate confidence interval for correlation using Fisher's z-transformation.
    
    Parameters:
    -----------
    r : float
        Correlation coefficient
    n : int
        Sample size
    alpha : float
        Alpha level for confidence interval
        
    Returns:
    --------
    tuple
        (correlation, lower_ci, upper_ci)
    """
    if n < 3 or abs(r) >= 1:
        return r, np.nan, np.nan
    
    # Fisher's z-transformation
    z = 0.5 * np.log((1 + r) / (1 - r))
    se_z = 1 / np.sqrt(n - 3)
    
    # Critical value
    z_crit = stats.norm.ppf(1 - alpha / 2)
    
    # Confidence interval in z-space
    z_lower = z - z_crit * se_z
    z_upper = z + z_crit * se_z
    
    # Transform back to correlation space
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return r, r_lower, r_upper


def main():
    """
    Main function to execute the effect size calculation pipeline.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("Starting effect size calculation script...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Find input files
        print("\nSearching for input files...")
        
        input_files = {
            'mrt_accuracy_glmm': find_latest_file('outputs/mrt_accuracy_glmm_results_<TIMESTAMP>.csv'),
            'mrt_rt_lmm': find_latest_file('outputs/mrt_rt_lmm_results_<TIMESTAMP>.csv'),
            'vviq2_regression': find_latest_file('outputs/vviq2_regression_results_<TIMESTAMP>.csv'),
            'mrt_accuracy_data': find_latest_file('outputs/mrt_accuracy_analysis_data_<TIMESTAMP>.csv'),
            'mrt_rt_data': find_latest_file('outputs/mrt_rt_analysis_data_<TIMESTAMP>.csv'),
            'vviq2_data': find_latest_file('outputs/vviq2_analysis_data_<TIMESTAMP>.csv'),
            'vonmises_params': find_latest_file('outputs/vonmises_parameters_overall_<TIMESTAMP>.csv')
        }
        
        # Check which files were found
        for file_type, file_path in input_files.items():
            if file_path:
                print(f"Found {file_type}: {file_path}")
            else:
                print(f"WARNING: Could not find {file_type}")
        
        # Load input files
        print("\nLoading input files...")
        
        data = {}
        for file_type, file_path in input_files.items():
            if file_path and os.path.exists(file_path):
                try:
                    df = pd.read_csv(file_path)
                    data[file_type] = df
                    print(f"Loaded {file_type}: {df.shape[0]} rows, {df.shape[1]} columns")
                    print(f"Columns: {list(df.columns)}")
                    print(f"First 3 rows:")
                    print(df.head(3))
                    print()
                except Exception as e:
                    print(f"Error loading {file_type}: {e}")
                    data[file_type] = None
            else:
                data[file_type] = None
        
        # Initialize output dataframes
        mixed_models_results = []
        vviq2_regression_results = []
        bivariate_correlations_results = []
        summary_results = []
        
        # Load von Mises parameters for uncertainty adjustment
        vonmises_df = data.get('vonmises_params')
        if vonmises_df is not None:
            print(f"Von Mises parameters unique values:")
            print(f"poor_fit_flag: {vonmises_df['poor_fit_flag'].unique() if 'poor_fit_flag' in vonmises_df.columns else 'Column not found'}")
            # Filter out poor fits if flag exists
            if 'poor_fit_flag' in vonmises_df.columns:
                # Ensure boolean type and handle potential NaN values
                vonmises_df = vonmises_df[vonmises_df['poor_fit_flag'].fillna(True) == False].copy()
                print(f"After filtering poor fits: {vonmises_df.shape[0]} participants")
        
        # Prepare base dataframe for bootstrap: merge kappa means and SEs with participant-level data
        print("\n" + "="*60)
        print("PREPARING DATA FOR BOOTSTRAP")
        print("="*60)

        # Prepare base dataframe with kappa means and SEs
        if vonmises_df is not None:
            kappa_base = vonmises_df[['participantId', 'kappa_overall', 'kappa_se_overall']].copy()
        else:
            raise RuntimeError("Von Mises parameter file with kappa means and SEs is required for bootstrap.")

        # Merge with VVIQ2 data for regression
        if data['vviq2_data'] is not None:
            vviq2_data_df = data['vviq2_data']
            # Rename kappa columns to avoid conflicts
            kappa_base_renamed = kappa_base.rename(columns={
                'kappa_overall': 'kappa_mean', 
                'kappa_se_overall': 'kappa_se'
            })
            vviq2_bootstrap_df = pd.merge(vviq2_data_df, kappa_base_renamed, on='participantId', how='inner')
            print(f"VVIQ2 bootstrap df columns after merge: {list(vviq2_bootstrap_df.columns)}")
            print(f"VVIQ2 bootstrap df shape: {vviq2_bootstrap_df.shape}")
            if len(vviq2_bootstrap_df) == 0:
                print("WARNING: No participants found after merging VVIQ2 data with kappa parameters")
                vviq2_bootstrap_df = None
        else:
            vviq2_bootstrap_df = None

        # Merge with MRT accuracy and RT data for mixed models
        if data['mrt_accuracy_data'] is not None:
            mrt_acc_df = data['mrt_accuracy_data']
            # Rename kappa columns to avoid conflicts
            kappa_base_renamed = kappa_base.rename(columns={
                'kappa_overall': 'kappa_mean', 
                'kappa_se_overall': 'kappa_se'
            })
            mrt_acc_bootstrap_df = pd.merge(mrt_acc_df, kappa_base_renamed, on='participantId', how='inner')
            print(f"MRT accuracy bootstrap df columns after merge: {list(mrt_acc_bootstrap_df.columns)}")
            print(f"MRT accuracy bootstrap df shape: {mrt_acc_bootstrap_df.shape}")
            if len(mrt_acc_bootstrap_df) == 0:
                print("WARNING: No participants found after merging MRT accuracy data with kappa parameters")
                mrt_acc_bootstrap_df = None
        else:
            mrt_acc_bootstrap_df = None

        if data['mrt_rt_data'] is not None:
            mrt_rt_df = data['mrt_rt_data']
            # Rename kappa columns to avoid conflicts
            kappa_base_renamed = kappa_base.rename(columns={
                'kappa_overall': 'kappa_mean', 
                'kappa_se_overall': 'kappa_se'
            })
            mrt_rt_bootstrap_df = pd.merge(mrt_rt_df, kappa_base_renamed, on='participantId', how='inner')
            print(f"MRT RT bootstrap df columns after merge: {list(mrt_rt_bootstrap_df.columns)}")
            print(f"MRT RT bootstrap df shape: {mrt_rt_bootstrap_df.shape}")
            if len(mrt_rt_bootstrap_df) == 0:
                print("WARNING: No participants found after merging MRT RT data with kappa parameters")
                mrt_rt_bootstrap_df = None
        else:
            mrt_rt_bootstrap_df = None

        # 1. Bootstrap effect sizes for mixed-effects models
        print("\n" + "="*60)
        print("BOOTSTRAP MIXED-EFFECTS MODEL EFFECT SIZES")
        print("="*60)

        n_bootstrap = 1000
        np.random.seed(42)

        # MRT Accuracy GLMM (logistic regression with random intercepts)
        if mrt_acc_bootstrap_df is not None:
            # Aggregate data for participant-level GLM as per new instructions
            print("\nAggregating MRT accuracy data to participant level for GLM...")
            agg_df = mrt_acc_bootstrap_df.groupby('participantId').agg({
                'isCorrect': ['sum', 'count'],
                'kappa_mean': 'first',
                'kappa_se': 'first'
            }).reset_index()
            # Flatten column names
            agg_df.columns = ['participantId', 'n_correct', 'n_trials', 'kappa_mean', 'kappa_se']
            agg_df['n_failures'] = agg_df['n_trials'] - agg_df['n_correct']
            agg_df['prop_correct'] = agg_df['n_correct'] / agg_df['n_trials']

            # Debugging: Validate aggregated data structure
            print(f"Aggregated data validation:")
            print(f"Shape: {agg_df.shape}")
            print(f"Columns: {list(agg_df.columns)}")
            print(f"Sample data:\n{agg_df.head(3)}")
            print(f"Trial count range: {agg_df['n_trials'].min()} - {agg_df['n_trials'].max()}")
            print(f"Correct count range: {agg_df['n_correct'].min()} - {agg_df['n_correct'].max()}")

            # Additional validation: ensure no zero trial counts
            if agg_df['n_trials'].min() == 0:
                print("ERROR: Some participants have zero trials")
                agg_df = None

        if mrt_acc_bootstrap_df is not None and agg_df is not None:
            # Calculate empirical logit for each participant
            agg_df['logit_p'] = np.log((agg_df['n_correct'] + 0.5) / (agg_df['n_failures'] + 0.5))

            # Validate required columns (after aggregation and renaming) after kappa info is present
            required_cols = ['participantId', 'kappa_mean', 'kappa_se']
            missing_cols = [col for col in required_cols if col not in agg_df.columns]
            if missing_cols:
                print(f"ERROR: Missing required columns in aggregated MRT accuracy data: {missing_cols}")
                agg_df = None

            # Validate kappa_se values are positive and non-zero
            invalid_se = (agg_df['kappa_se'] <= 0) | (agg_df['kappa_se'].isna())
            if invalid_se.any():
                print(f"WARNING: Found {invalid_se.sum()} participants with invalid kappa_se values. Removing them.")
                agg_df = agg_df[~invalid_se].copy()
                print(f"Remaining participants after SE validation: {len(agg_df)}")

            print("\nBootstrapping MRT Accuracy WLS (empirical logit regression)...")
            effect_dists = {}
            successful_iterations = 0

            # Use participant-level data for bootstrap
            participant_kappa_info = agg_df[['participantId', 'kappa_mean', 'kappa_se']]

            for i in tqdm(range(n_bootstrap), desc="Bootstrap MRT Accuracy WLS"):
                try:
                    # Generate one kappa sample per participant
                    kappa_sample = np.random.normal(participant_kappa_info['kappa_mean'], participant_kappa_info['kappa_se'])
                    sample_df = pd.DataFrame({
                        'participantId': participant_kappa_info['participantId'],
                        'kappa_overall_boot': kappa_sample
                    })
                    # Merge with aggregated data
                    df = pd.merge(agg_df, sample_df, on='participantId', how='left')
                    df['kappa_overall_boot_centered'] = df['kappa_overall_boot'] - df['kappa_overall_boot'].mean()

                    # Use empirical logit as dependent variable, weighted by n_trials
                    try:
                        model = smf.wls(
                            "logit_p ~ kappa_overall_boot_centered",
                            data=df,
                            weights=df['n_trials']
                        )
                        result = model.fit()

                        # Debug output for first few iterations
                        if i < 5:
                            print(f"Iteration {i}: WLS fitted successfully")
                            print(f"  Parameters: {list(result.params.index)}")

                    except Exception as e:
                        if i < 10:
                            print(f"Iteration {i}: WLS fitting failed: {e}")
                            print(f"  Data shape: {df.shape}")
                            print(f"  Kappa range: [{df['kappa_overall_boot_centered'].min():.3f}, {df['kappa_overall_boot_centered'].max():.3f}]")
                            print(f"  logit_p range: [{df['logit_p'].min():.3f}, {df['logit_p'].max():.3f}]")
                            print(f"  n_trials range: [{df['n_trials'].min()}, {df['n_trials'].max()}]")
                        continue

                    # Extract main effect only (no interactions)
                    effect_name = 'kappa_overall_boot_centered'
                    if effect_name in result.params.index:
                        coeff = result.params[effect_name]
                        odds_ratio = np.exp(coeff)

                        if not np.isnan(odds_ratio) and odds_ratio > 0 and not np.isinf(odds_ratio):
                            if effect_name not in effect_dists:
                                effect_dists[effect_name] = {'or': [], 'coeff': []}
                            effect_dists[effect_name]['or'].append(odds_ratio)
                            effect_dists[effect_name]['coeff'].append(coeff)

                    successful_iterations += 1
                    if (i+1) % 100 == 0:
                        print(f"Completed {i+1} bootstrap iterations, {successful_iterations} successful.")

                except Exception as e:
                    if i < 10:  # Print first 10 errors for debugging
                        print(f"Iteration {i}: WLS fitting failed: {e}")
                        print(f"Data shape: {df.shape}, kappa range: [{df['kappa_overall_boot_centered'].min():.3f}, {df['kappa_overall_boot_centered'].max():.3f}]")
                    continue

            print(f"Total successful bootstrap iterations: {successful_iterations}")

            # Add debugging after bootstrap loop to check effect_dists contents
            print(f"\nBootstrap completed. effect_dists contains {len(effect_dists)} effects:")
            for name, dists in effect_dists.items():
                print(f"  {name}: {len(dists.get('or', []))} OR samples, {len(dists.get('coeff', []))} coeff samples")

            # Add minimum threshold for successful iterations
            if successful_iterations < 500:
                print(f"WARNING: Only {successful_iterations} successful iterations. Minimum 500 required.")

            # Debugging: show final effect_dists keys and sample counts
            if len(effect_dists) == 0:
                print("ERROR: No effects were collected during bootstrap. Check model specification.")

            print(f"Final effect_dists keys: {list(effect_dists.keys())}")
            for name, dists in effect_dists.items():
                print(f"  {name}: {len(dists['or'])} samples")

            # Process results for each effect (outside try-catch)
            for effect_name, dists in effect_dists.items():
                or_dist = np.array(dists['or'])
                or_dist = or_dist[~np.isnan(or_dist)]
                coeff_dist = np.array(dists['coeff'])
                coeff_dist = coeff_dist[~np.isnan(coeff_dist)]

                if len(or_dist) > 0:
                    or_median = np.median(or_dist)
                    ci_lower = np.percentile(or_dist, 2.5)
                    ci_upper = np.percentile(or_dist, 97.5)
                    interpretation = interpret_odds_ratio(or_median)

                    # Clean effect name
                    clean_effect_name = 'kappa_overall'

                    # Coefficient CI for significance
                    if len(coeff_dist) > 0:
                        coeff_ci_lower = np.percentile(coeff_dist, 2.5)
                        coeff_ci_upper = np.percentile(coeff_dist, 97.5)
                    else:
                        coeff_ci_lower = np.nan
                        coeff_ci_upper = np.nan

                    mixed_models_results.append({
                        'model_name': 'MRT_Accuracy_WLS',
                        'effect_name': clean_effect_name,
                        'effect_size': or_median,
                        'effect_size_type': 'odds_ratio',
                        'ci_lower': ci_lower,
                        'ci_upper': ci_upper,
                        'interpretation': interpretation,
                        'uncertainty_adjusted': True,
                        'coeff_ci_lower': coeff_ci_lower,
                        'coeff_ci_upper': coeff_ci_upper
                    })

                    print(f"Bootstrap Odds Ratio for {clean_effect_name} = {or_median:.4f} [{ci_lower:.4f}, {ci_upper:.4f}] ({interpretation})")
                else:
                    print(f"No valid bootstrap samples for {effect_name}.")

            # Validation: ensure results were added
            if len(mixed_models_results) == 0:
                print("WARNING: No MRT Accuracy WLS results were added to mixed_models_results after processing bootstrap.")

        # MRT RT LMM (linear regression with random intercepts)
        if mrt_rt_bootstrap_df is not None:
            print("\nBootstrapping MRT RT LMM (linear regression with random intercepts)...")
            effect_dists = {}
            successful_iterations = 0

            # Optimization: extract unique participant kappa info once
            participant_kappa_info = mrt_rt_bootstrap_df[['participantId', 'kappa_mean', 'kappa_se']].drop_duplicates().reset_index(drop=True)
            print(f"Unique participants for bootstrap: {len(participant_kappa_info)}")

            for i in tqdm(range(n_bootstrap), desc="Bootstrap MRT RT LMM"):
                try:
                    # Generate one kappa sample per participant
                    kappa_sample = np.random.normal(participant_kappa_info['kappa_mean'], participant_kappa_info['kappa_se'])
                    sample_df = pd.DataFrame({
                        'participantId': participant_kappa_info['participantId'],
                        'kappa_overall_boot': kappa_sample
                    })
                    # Merge the small sample df into the main data
                    df = pd.merge(mrt_rt_bootstrap_df, sample_df, on='participantId', how='left')
                    df['kappa_overall_boot_centered'] = df['kappa_overall_boot'] - df['kappa_overall_boot'].mean()

                    # Try mixed-effects model first
                    try:
                        model = smf.mixedlm("log_rt ~ kappa_overall_boot_centered * C(angle_degrees)",
                                           df, groups=df["participantId"])
                        result = model.fit(reml=False)

                        # Extract effects for all kappa-related terms
                        for effect_name in result.tvalues.index:
                            if 'kappa_overall_boot_centered' in effect_name:
                                t_stat = result.tvalues[effect_name]
                                df_resid = result.df_resid
                                f_stat = t_stat ** 2
                                eta_sq = f_stat / (f_stat + df_resid) if (f_stat + df_resid) > 0 else np.nan

                                if effect_name not in effect_dists:
                                    effect_dists[effect_name] = {'eta_sq': [], 'coeff': []}
                                effect_dists[effect_name]['eta_sq'].append(eta_sq)
                                effect_dists[effect_name]['coeff'].append(result.params[effect_name])

                    except Exception as e:
                        if i < 10:
                            print(f"Iteration {i}: MixedLM failed: {e}. Falling back to OLS.")
                        # Fallback to OLS approximation
                        model = smf.ols("log_rt ~ kappa_overall_boot_centered * C(angle_degrees)", data=df)
                        result = model.fit()

                        # Extract effects for all kappa-related terms
                        for effect_name in result.tvalues.index:
                            if 'kappa_overall_boot_centered' in effect_name:
                                t_stat = result.tvalues[effect_name]
                                df_resid = result.df_resid
                                f_stat = t_stat ** 2
                                eta_sq = f_stat / (f_stat + df_resid) if (f_stat + df_resid) > 0 else np.nan

                                if effect_name not in effect_dists:
                                    effect_dists[effect_name] = {'eta_sq': [], 'coeff': []}
                                effect_dists[effect_name]['eta_sq'].append(eta_sq)
                                effect_dists[effect_name]['coeff'].append(result.params[effect_name])

                    successful_iterations += 1
                    if (i+1) % 100 == 0:
                        print(f"Completed {i+1} bootstrap iterations, {successful_iterations} successful.")

                except Exception as e:
                    if i < 10:
                        print(f"Iteration {i}: Exception during bootstrap: {e}")
                    continue

            print(f"Total successful bootstrap iterations: {successful_iterations}")

            # Process results for each effect
            for effect_name, dists in effect_dists.items():
                eta_sq_dist = np.array(dists['eta_sq'])
                eta_sq_dist = eta_sq_dist[~np.isnan(eta_sq_dist)]
                coeff_dist = np.array(dists['coeff'])
                coeff_dist = coeff_dist[~np.isnan(coeff_dist)]

                if len(eta_sq_dist) > 0:
                    eta_sq_median = np.median(eta_sq_dist)
                    ci_lower = np.percentile(eta_sq_dist, 2.5)
                    ci_upper = np.percentile(eta_sq_dist, 97.5)
                    interpretation = interpret_eta_squared(eta_sq_median)

                    # Clean effect name
                    clean_effect_name = effect_name.replace('kappa_overall_boot_centered', 'kappa_overall')

                    # Coefficient CI for significance
                    if len(coeff_dist) > 0:
                        coeff_ci_lower = np.percentile(coeff_dist, 2.5)
                        coeff_ci_upper = np.percentile(coeff_dist, 97.5)
                    else:
                        coeff_ci_lower = np.nan
                        coeff_ci_upper = np.nan

                    mixed_models_results.append({
                        'model_name': 'MRT_RT_LMM',
                        'effect_name': clean_effect_name,
                        'effect_size': eta_sq_median,
                        'effect_size_type': 'partial_eta_squared',
                        'ci_lower': ci_lower,
                        'ci_upper': ci_upper,
                        'interpretation': interpretation,
                        'uncertainty_adjusted': True,
                        'coeff_ci_lower': coeff_ci_lower,
                        'coeff_ci_upper': coeff_ci_upper
                    })

                    print(f"Bootstrap partial η² for {clean_effect_name} = {eta_sq_median:.4f} [{ci_lower:.4f}, {ci_upper:.4f}] ({interpretation})")
                else:
                    print(f"No valid bootstrap samples for {effect_name}.")

        # 2. Bootstrap standardized effect sizes for VVIQ2 regression
        print("\n" + "="*60)
        print("BOOTSTRAP VVIQ2 REGRESSION EFFECT SIZES")
        print("="*60)

        if vviq2_bootstrap_df is not None:
            # Outcome variables and their corresponding columns
            outcome_mapping = {
                'total_vviq2_score': 'total_vviq2_score',
                'familiar_person_score': 'familiar_person_score',
                'sunrise_score': 'sunrise_score',
                'shop_front_score': 'shop_front_score',
                'countryside_score': 'countryside_score',
                'driving_score': 'driving_score',
                'beach_score': 'beach_score',
                'railway_station_score': 'railway_station_score',
                'garden_score': 'garden_score'
            }

            required_cols = ['mean_vwm_accuracy', 'mrt_rt_variability', 'focus_loss_instances']
            available_cols = [col for col in required_cols if col in vviq2_bootstrap_df.columns]

            if len(available_cols) < len(required_cols):
                print(f"WARNING: Missing VVIQ2 covariates. Available: {available_cols}, Required: {required_cols}")

            # Optimization: extract unique participant kappa info once (not strictly necessary, but for consistency)
            participant_kappa_info = vviq2_bootstrap_df[['participantId', 'kappa_mean', 'kappa_se']].drop_duplicates().reset_index(drop=True)

            for outcome_var in outcome_mapping.values():
                if outcome_var not in vviq2_bootstrap_df.columns:
                    continue

                print(f"\nBootstrapping VVIQ2 regression for {outcome_var}...")
                beta_dist = []
                r2_dist = []

                for i in tqdm(range(n_bootstrap), desc=f"Bootstrap VVIQ2 {outcome_var}"):
                    try:
                        # Generate one kappa sample per participant
                        kappa_sample = np.random.normal(participant_kappa_info['kappa_mean'], participant_kappa_info['kappa_se'])
                        sample_df = pd.DataFrame({
                            'participantId': participant_kappa_info['participantId'],
                            'kappa_overall_boot': kappa_sample
                        })
                        # Merge the small sample df into the main data
                        df = pd.merge(vviq2_bootstrap_df, sample_df, on='participantId', how='left')
                        df['kappa_overall_boot_centered'] = df['kappa_overall_boot'] - df['kappa_overall_boot'].mean()

                        # Center all available covariates
                        formula_parts = ['kappa_overall_boot_centered']
                        for col in available_cols:
                            centered_col = f"{col}_centered"
                            df[centered_col] = df[col] - df[col].mean()
                            formula_parts.append(centered_col)

                        formula = f"{outcome_var} ~ " + " + ".join(formula_parts)

                        model = smf.ols(formula, data=df)
                        result = model.fit()

                        # Extract standardized beta for kappa effect
                        if 'kappa_overall_boot_centered' in result.params.index:
                            sd_x = df['kappa_overall_boot_centered'].std()
                            sd_y = df[outcome_var].std()
                            beta = result.params['kappa_overall_boot_centered']
                            beta_std = beta * (sd_x / sd_y) if sd_y > 0 else np.nan
                            beta_dist.append(beta_std)
                            r2_dist.append(result.rsquared)
                        else:
                            beta_dist.append(np.nan)
                            r2_dist.append(np.nan)

                    except Exception as e:
                        beta_dist.append(np.nan)
                        r2_dist.append(np.nan)

                # Process results
                beta_dist = np.array(beta_dist)
                beta_dist = beta_dist[~np.isnan(beta_dist)]
                r2_dist = np.array(r2_dist)
                r2_dist = r2_dist[~np.isnan(r2_dist)]

                if len(beta_dist) > 0:
                    beta_std = np.median(beta_dist)
                    ci_lower = np.percentile(beta_dist, 2.5)
                    ci_upper = np.percentile(beta_dist, 97.5)
                    interpretation = interpret_standardized_beta(beta_std)
                    r2_median = np.median(r2_dist) if len(r2_dist) > 0 else np.nan

                    vviq2_regression_results.append({
                        'outcome_variable': outcome_var,
                        'standardized_beta': beta_std,
                        'beta_ci_lower': ci_lower,
                        'beta_ci_upper': ci_upper,
                        'interpretation': interpretation,
                        'r_squared_model': r2_median
                    })

                    print(f"Bootstrap standardized β = {beta_std:.4f} [{ci_lower:.4f}, {ci_upper:.4f}] ({interpretation})")
                    print(f"Model R² (median): {r2_median:.4f}")
                    print(f"Covariates included: {', '.join(available_cols)}")
                else:
                    print(f"No valid bootstrap samples for {outcome_var}.")
        
        # 3. Calculate bivariate correlations
        print("\n" + "="*60)
        print("CALCULATING BIVARIATE CORRELATIONS")
        print("="*60)
        
        # Prepare participant-level data for correlations
        participant_data = {}
        
        # MRT accuracy data
        if data['mrt_accuracy_data'] is not None:
            mrt_acc_df = data['mrt_accuracy_data']
            print(f"MRT accuracy data: {mrt_acc_df.shape}")
            print(f"Unique values in key columns:")
            print(f"angle_degrees: {sorted(mrt_acc_df['angle_degrees'].unique())}")
            print(f"isCorrect: {mrt_acc_df['isCorrect'].unique()}")
            
            # Calculate mean accuracy per participant
            participant_accuracy = mrt_acc_df.groupby('participantId')['isCorrect'].mean().reset_index()
            participant_accuracy.columns = ['participantId', 'mean_accuracy']
            participant_data['mean_accuracy'] = participant_accuracy
            print(f"Calculated mean accuracy for {len(participant_accuracy)} participants")
        
        # MRT RT data
        if data['mrt_rt_data'] is not None:
            mrt_rt_df = data['mrt_rt_data']
            print(f"MRT RT data: {mrt_rt_df.shape}")
            print(f"Unique values in key columns:")
            print(f"angle_degrees: {sorted(mrt_rt_df['angle_degrees'].unique())}")
            print(f"log_rt data type: {mrt_rt_df['log_rt'].dtype}")
            
            # Calculate mean log RT per participant
            participant_rt = mrt_rt_df.groupby('participantId')['log_rt'].mean().reset_index()
            participant_rt.columns = ['participantId', 'mean_log_rt']
            participant_data['mean_log_rt'] = participant_rt
            print(f"Calculated mean log RT for {len(participant_rt)} participants")
        
        # VVIQ2 data
        if data['vviq2_data'] is not None:
            vviq2_df = data['vviq2_data']
            print(f"VVIQ2 data: {vviq2_df.shape}")
            print(f"VVIQ2 columns: {list(vviq2_df.columns)}")
            
            # VVIQ2 scores are already at participant level
            vviq2_scores = vviq2_df[[
                'participantId', 'total_vviq2_score', 'familiar_person_score',
                'sunrise_score', 'shop_front_score', 'countryside_score',
                'driving_score', 'beach_score', 'railway_station_score', 'garden_score'
            ]].copy()
            participant_data['vviq2_scores'] = vviq2_scores
            print(f"VVIQ2 scores for {len(vviq2_scores)} participants")
        
        # Merge all participant data with kappa values
        if vonmises_df is not None:
            print(f"\nMerging participant data with kappa values...")
            
            # Start with kappa values
            merged_data = vonmises_df[['participantId', 'kappa_overall']].copy()
            print(f"Starting with {len(merged_data)} participants with kappa values")
            
            # Merge each dataset
            for data_name, df in participant_data.items():
                if df is not None:
                    merged_data = merged_data.merge(df, on='participantId', how='inner')
                    print(f"After merging {data_name}: {len(merged_data)} participants")
            
            print(f"Final merged dataset: {merged_data.shape}")
            print("Columns:", list(merged_data.columns))
            print("First 2 rows:")
            print(merged_data.head(2))

            # Add validation for minimum sample size in correlations
            if len(merged_data) < 10:
                print(f"WARNING: Insufficient sample size ({len(merged_data)}) for reliable correlations")
            
            # Calculate correlations
            kappa_values = merged_data['kappa_overall'].values
            
            # Define outcome variables for correlation
            outcome_vars = {
                'MRT_Overall_Accuracy': 'mean_accuracy',
                'MRT_Mean_LogRT': 'mean_log_rt',
                'VVIQ2_Total_Score': 'total_vviq2_score',
                'VVIQ2_Familiar_Person': 'familiar_person_score',
                'VVIQ2_Sunrise': 'sunrise_score',
                'VVIQ2_Shop_Front': 'shop_front_score',
                'VVIQ2_Countryside': 'countryside_score',
                'VVIQ2_Driving': 'driving_score',
                'VVIQ2_Beach': 'beach_score',
                'VVIQ2_Railway_Station': 'railway_station_score',
                'VVIQ2_Garden': 'garden_score'
            }
            
            for outcome_name, column_name in outcome_vars.items():
                if column_name in merged_data.columns:
                    outcome_values = merged_data[column_name].values
                    
                    # Calculate correlation with bootstrap CI
                    r, ci_lower, ci_upper = bootstrap_correlation_ci(kappa_values, outcome_values)
                    
                    # Calculate p-value
                    try:
                        _, p_value = pearsonr(kappa_values, outcome_values)
                    except:
                        p_value = np.nan
                    
                    interpretation = interpret_correlation(r)
                    sample_size = len(merged_data)
                    
                    bivariate_correlations_results.append({
                        'variable_pair': f'kappa_overall - {outcome_name}',
                        'pearson_r': r,
                        'r_ci_lower': ci_lower,
                        'r_ci_upper': ci_upper,
                        'p_value': p_value,
                        'interpretation': interpretation,
                        'sample_size': sample_size
                    })
                    
                    print(f"\nCorrelation: kappa_overall - {outcome_name}")
                    print(f"r = {r:.4f} [{ci_lower:.4f}, {ci_upper:.4f}], p = {p_value:.4f} ({interpretation})")
                    print(f"Sample size: {sample_size}")
        
        # 4. Create comprehensive summary
        print("\n" + "="*60)
        print("CREATING COMPREHENSIVE SUMMARY")
        print("="*60)
        
        # Mixed models summary
        for result in mixed_models_results:
            # Use coefficient CI for significance testing
            significance = "significant" if (
                ('coeff_ci_lower' in result and 'coeff_ci_upper' in result) and
                (
                    (result['coeff_ci_lower'] > 0 and result['coeff_ci_upper'] > 0) or
                    (result['coeff_ci_lower'] < 0 and result['coeff_ci_upper'] < 0)
                )
            ) else "non-significant"
            summary_results.append({
                'analysis_type': 'Mixed_Effects_Model',
                'effect_description': f"{result['model_name']} - {result['effect_name']}",
                'effect_size_value': result['effect_size'],
                'effect_size_type': result['effect_size_type'],
                'ci_lower': result['ci_lower'],
                'ci_upper': result['ci_upper'],
                'magnitude_interpretation': result['interpretation'],
                'statistical_significance': significance
            })
        
        # VVIQ2 regression summary
        for result in vviq2_regression_results:
            significance = "significant" if (result['beta_ci_lower'] > 0 and result['beta_ci_upper'] > 0) or (result['beta_ci_lower'] < 0 and result['beta_ci_upper'] < 0) else "non-significant"
            summary_results.append({
                'analysis_type': 'VVIQ2_Regression',
                'effect_description': f"kappa_overall -> {result['outcome_variable']}",
                'effect_size_value': result['standardized_beta'],
                'effect_size_type': 'standardized_beta',
                'ci_lower': result['beta_ci_lower'],
                'ci_upper': result['beta_ci_upper'],
                'magnitude_interpretation': result['interpretation'],
                'statistical_significance': significance
            })
        
        # Bivariate correlations summary
        for result in bivariate_correlations_results:
            significance = "significant" if result['p_value'] < 0.05 else "non-significant"
            summary_results.append({
                'analysis_type': 'Bivariate_Correlation',
                'effect_description': result['variable_pair'],
                'effect_size_value': result['pearson_r'],
                'effect_size_type': 'pearson_r',
                'ci_lower': result['r_ci_lower'],
                'ci_upper': result['r_ci_upper'],
                'magnitude_interpretation': result['interpretation'],
                'statistical_significance': significance
            })
        
        # Save output files
        print("\n" + "="*60)
        print("SAVING OUTPUT FILES")
        print("="*60)
        
        # Mixed models effect sizes
        if mixed_models_results:
            mixed_models_df = pd.DataFrame(mixed_models_results)
            # Remove temporary columns before saving
            mixed_models_df = mixed_models_df.drop(columns=['coeff_ci_lower', 'coeff_ci_upper'], errors='ignore')
            mixed_models_file = f'outputs/effect_sizes_mixed_models_{timestamp}.csv'
            mixed_models_df.to_csv(mixed_models_file, index=False)
            print(f"Saved mixed models effect sizes: {mixed_models_file}")
            print(f"Shape: {mixed_models_df.shape}")
            print("Columns:", list(mixed_models_df.columns))
            print("First 2 rows:")
            print(mixed_models_df.head(2))
        
        # VVIQ2 regression effect sizes
        if vviq2_regression_results:
            vviq2_regression_df = pd.DataFrame(vviq2_regression_results)
            vviq2_regression_file = f'outputs/effect_sizes_vviq2_regression_{timestamp}.csv'
            vviq2_regression_df.to_csv(vviq2_regression_file, index=False)
            print(f"Saved VVIQ2 regression effect sizes: {vviq2_regression_file}")
            print(f"Shape: {vviq2_regression_df.shape}")
            print("Columns:", list(vviq2_regression_df.columns))
            print("First 2 rows:")
            print(vviq2_regression_df.head(2))
        
        # Bivariate correlations
        if bivariate_correlations_results:
            bivariate_correlations_df = pd.DataFrame(bivariate_correlations_results)
            bivariate_correlations_file = f'outputs/effect_sizes_bivariate_correlations_{timestamp}.csv'
            bivariate_correlations_df.to_csv(bivariate_correlations_file, index=False)
            print(f"Saved bivariate correlations: {bivariate_correlations_file}")
            print(f"Shape: {bivariate_correlations_df.shape}")
            print("Columns:", list(bivariate_correlations_df.columns))
            print("First 2 rows:")
            print(bivariate_correlations_df.head(2))
        
        # Summary
        if summary_results:
            summary_df = pd.DataFrame(summary_results)
            summary_file = f'outputs/effect_sizes_summary_{timestamp}.csv'
            summary_df.to_csv(summary_file, index=False)
            print(f"Saved effect sizes summary: {summary_file}")
            print(f"Shape: {summary_df.shape}")
            print("Columns:", list(summary_df.columns))
            print("First 2 rows:")
            print(summary_df.head(2))
        
        print(f"\nTotal effect sizes calculated:")
        print(f"- Mixed models: {len(mixed_models_results)}")
        print(f"- VVIQ2 regression: {len(vviq2_regression_results)}")
        print(f"- Bivariate correlations: {len(bivariate_correlations_results)}")
        print(f"- Summary entries: {len(summary_results)}")
        
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
