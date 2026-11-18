#!/usr/bin/env python3
"""
Sensitivity Analysis and Model Validation Script for VWM Study

This script conducts sensitivity analysis by excluding guess trials and validates
statistical models through comprehensive diagnostic procedures.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
from scipy import stats
from scipy.optimize import minimize
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri, conversion
from rpy2.robjects.packages import importr

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

def load_input_data():
    """
    Load all required input data files.
    
    Returns:
    tuple: (trial_data, model_params, mrt_results, vviq_results, vviq_scores, mrt_trial_data)
    """
    print("Loading input data files...")
    
    # Find latest files
    trial_pattern = "outputs/VWM_cleaned_trial_data_*.csv"
    params_pattern = "outputs/VWM_circular_model_parameters_*.csv"
    mrt_pattern = "outputs/MRT_mixed_effects_results_*.csv"
    vviq_pattern = "outputs/VVIQ2_robust_regression_results_*.csv"
    vviq_scores_pattern = "outputs/VVIQ2_processed_scores_*.csv"
    mrt_trial_pattern = "outputs/MRT_cleaned_trial_data_*.csv"
    
    trial_file = find_latest_file(trial_pattern)
    params_file = find_latest_file(params_pattern)
    mrt_file = find_latest_file(mrt_pattern)
    vviq_file = find_latest_file(vviq_pattern)
    vviq_scores_file = find_latest_file(vviq_scores_pattern)
    mrt_trial_file = find_latest_file(mrt_trial_pattern)
    
    if not all([trial_file, params_file, mrt_file, vviq_file, vviq_scores_file, mrt_trial_file]):
        print("Error: Could not find all required input files")
        return None, None, None, None, None, None
    
    print(f"Loading trial data from: {trial_file}")
    trial_data = pd.read_csv(trial_file)
    print(f"Trial data columns: {list(trial_data.columns)}")
    print(f"First 3 rows of trial data:")
    print(trial_data.head(3))
    
    print(f"\nLoading model parameters from: {params_file}")
    model_params = pd.read_csv(params_file)
    print(f"Model parameters columns: {list(model_params.columns)}")
    print(f"First 3 rows of model parameters:")
    print(model_params.head(3))
    
    print(f"\nLoading MRT results from: {mrt_file}")
    mrt_results = pd.read_csv(mrt_file)
    print(f"MRT results columns: {list(mrt_results.columns)}")
    print(f"First 3 rows of MRT results:")
    print(mrt_results.head(3))
    
    print(f"\nLoading VVIQ results from: {vviq_file}")
    vviq_results = pd.read_csv(vviq_file)
    print(f"VVIQ results columns: {list(vviq_results.columns)}")
    print(f"First 3 rows of VVIQ results:")
    print(vviq_results.head(3))
    
    print(f"\nLoading VVIQ2 processed scores from: {vviq_scores_file}")
    vviq_scores = pd.read_csv(vviq_scores_file)
    print(f"VVIQ2 processed scores columns: {list(vviq_scores.columns)}")
    print(f"First 3 rows of VVIQ2 processed scores:")
    print(vviq_scores.head(3))
    print(f"VVIQ2 processed scores detailed columns: {list(vviq_scores.columns)}")
    if 'total_score_standardized' in vviq_scores.columns:
        print("Found 'total_score_standardized' column for VVIQ2 analysis")
    elif 'total_score_raw' in vviq_scores.columns:
        print("Found 'total_score_raw' column for VVIQ2 analysis")
    else:
        print("Warning: No standard VVIQ2 total score column found")
    
    print(f"\nLoading MRT cleaned trial data from: {mrt_trial_file}")
    mrt_trial_data = pd.read_csv(mrt_trial_file)
    print(f"MRT cleaned trial data columns: {list(mrt_trial_data.columns)}")
    print(f"First 3 rows of MRT cleaned trial data:")
    print(mrt_trial_data.head(3))
    
    return trial_data, model_params, mrt_results, vviq_results, vviq_scores, mrt_trial_data

def classify_guess_trials(trial_data, model_params):
    """
    Classify trials as memory-based vs guess responses using mixture model results.
    
    Parameters:
    trial_data (pd.DataFrame): Trial-level data
    model_params (pd.DataFrame): Circular model parameters
    
    Returns:
    pd.DataFrame: Trial data with guess classification
    """
    print("\nClassifying guess trials using mixture model results...")
    
    # Merge trial data with model parameters
    trial_data_classified = trial_data.merge(
        model_params[['participantId', 'kappa_vonmises', 'guess_rate_proportion', 'model_converged']], 
        on='participantId', 
        how='left'
    )
    
    print(f"Total trials before classification: {len(trial_data_classified)}")
    
    # Calculate von Mises probability for each trial
    def vonmises_probability(error_rad, kappa):
        """Calculate von Mises probability density"""
        from scipy.special import i0
        return np.exp(kappa * np.cos(error_rad)) / (2 * np.pi * i0(kappa))
    
    # Convert error to radians
    trial_data_classified['error_rad'] = np.deg2rad(trial_data_classified['normalized_error_degrees'])
    
    # Calculate probabilities
    vonmises_probs = []
    memory_based_flags = []
    
    for idx, row in trial_data_classified.iterrows():
        if pd.isna(row['kappa_vonmises']) or pd.isna(row['guess_rate_proportion']):
            vonmises_probs.append(np.nan)
            memory_based_flags.append(False)
            continue
            
        # Von Mises probability
        vm_prob = vonmises_probability(row['error_rad'], row['kappa_vonmises'])
        
        # Uniform (guess) probability
        uniform_prob = 1 / (2 * np.pi)
        
        # Mixture probabilities
        memory_weight = 1 - row['guess_rate_proportion']
        guess_weight = row['guess_rate_proportion']
        
        # Posterior probability of memory-based response
        posterior_memory = (memory_weight * vm_prob) / (memory_weight * vm_prob + guess_weight * uniform_prob)
        
        vonmises_probs.append(posterior_memory)
        memory_based_flags.append(posterior_memory > 0.5)
    
    trial_data_classified['vonmises_probability'] = vonmises_probs
    trial_data_classified['memory_based'] = memory_based_flags
    
    # Summary statistics
    total_trials = len(trial_data_classified)
    memory_trials = sum(trial_data_classified['memory_based'])
    guess_trials = total_trials - memory_trials
    
    print(f"Classification results:")
    print(f"  Total trials: {total_trials}")
    print(f"  Memory-based trials: {memory_trials} ({memory_trials/total_trials*100:.1f}%)")
    print(f"  Guess trials: {guess_trials} ({guess_trials/total_trials*100:.1f}%)")
    
    return trial_data_classified

def fit_vonmises_memory_only(trial_data_classified):
    """
    Re-fit von Mises models on memory-only trials for each participant.
    
    Parameters:
    trial_data_classified (pd.DataFrame): Trial data with guess classification
    
    Returns:
    pd.DataFrame: Sensitivity parameters for each participant
    """
    print("\nRe-fitting von Mises models on memory-only trials...")

    sensitivity_params = []

    # Filter to memory-based trials only
    memory_trials = trial_data_classified[
        (trial_data_classified['memory_based'] == True) &
        (~trial_data_classified['trial_excluded'])
    ]

    participants = memory_trials['participantId'].unique()
    print(f"Processing {len(participants)} participants for sensitivity analysis...")

    for participant in participants:
        participant_trials = memory_trials[memory_trials['participantId'] == participant]

        if len(participant_trials) < 15:
            print(f"  {participant}: Insufficient trials ({len(participant_trials)}), skipping")
            sensitivity_params.append({
                'participantId': participant,
                'kappa_sensitivity': np.nan,
                'sufficient_trials': False,
                'num_memory_trials': len(participant_trials)
            })
            continue

        # Get error values in radians
        errors_rad = participant_trials['error_rad'].values

        # Fit von Mises distribution using scipy.stats.vonmises.fit
        try:
            # scipy.stats.vonmises.fit returns (kappa, loc, scale) if floc=0, fscale=1
            # We want to estimate kappa only, so fix loc=0, scale=1
            # The fit method expects data in radians
            fit_kappa, fit_loc, fit_scale = stats.vonmises.fit(errors_rad, fscale=1, floc=0)
            kappa_sensitivity = fit_kappa
        except Exception as e:
            print(f"  {participant}: Fitting error - {e}")
            kappa_sensitivity = np.nan

        sensitivity_params.append({
            'participantId': participant,
            'kappa_sensitivity': kappa_sensitivity,
            'sufficient_trials': len(participant_trials) >= 15,
            'num_memory_trials': len(participant_trials)
        })

        if len(sensitivity_params) % 50 == 0:
            print(f"  Processed {len(sensitivity_params)} participants...")

    sensitivity_df = pd.DataFrame(sensitivity_params)

    # Summary statistics
    valid_params = sensitivity_df[~sensitivity_df['kappa_sensitivity'].isna()]
    print(f"\nSensitivity parameter fitting results:")
    print(f"  Participants processed: {len(sensitivity_df)}")
    print(f"  Valid parameters obtained: {len(valid_params)}")
    print(f"  Insufficient trials: {sum(~sensitivity_df['sufficient_trials'])}")
    print(f"  Mean kappa_sensitivity: {valid_params['kappa_sensitivity'].mean():.3f}")
    print(f"  Std kappa_sensitivity: {valid_params['kappa_sensitivity'].std():.3f}")

    return sensitivity_df

def install_r_packages():
    """Install required R packages if not already installed."""
    try:
        utils = importr('utils')
        pkgs = robjects.StrVector(['lme4', 'lmerTest', 'robust', 'MASS'])
        utils.install_packages(pkgs, repos='https://cloud.r-project.org')
    except Exception as e:
        print(f"Warning: Could not install R packages: {e}")

def rerun_statistical_models(model_params, sensitivity_params, mrt_results, vviq_results, vviq_scores, mrt_trial_data):
    """
    Re-run statistical models using sensitivity kappa parameters.
    
    Parameters:
    model_params (pd.DataFrame): Original model parameters
    sensitivity_params (pd.DataFrame): Sensitivity kappa parameters
    mrt_results (pd.DataFrame): Original MRT results
    vviq_results (pd.DataFrame): Original VVIQ results
    vviq_scores (pd.DataFrame): VVIQ2 processed scores
    mrt_trial_data (pd.DataFrame): MRT cleaned trial data
    
    Returns:
    tuple: (sensitivity_mrt_results, sensitivity_vviq_results, correlation_result)
    """
    print("\nRe-running statistical models with sensitivity parameters...")
    
    # Merge original parameters with sensitivity parameters
    combined_params = model_params.merge(sensitivity_params, on='participantId', how='left')
    
    # Calculate correlation between original and sensitivity kappa
    valid_both = combined_params[
        (~combined_params['kappa_vonmises'].isna()) & 
        (~combined_params['kappa_sensitivity'].isna())
    ]
    
    if len(valid_both) > 0:
        correlation = stats.pearsonr(valid_both['kappa_vonmises'], valid_both['kappa_sensitivity'])
        print(f"Correlation between original and sensitivity kappa: r = {correlation[0]:.3f}, p = {correlation[1]:.3f}")
        correlation_result = correlation[0]
    else:
        print("No valid data for correlation calculation")
        correlation_result = np.nan

    print("Installing and loading R packages for statistical modeling...")
    try:
        install_r_packages()
        base = importr('base')
        lme4 = importr('lme4')
        lmertest = importr('lmerTest')
        robust = importr('robust')
        mass = importr('MASS')
        print("R packages loaded successfully")
    except Exception as e:
        print(f"Error loading R packages: {e}")
        return None, None, correlation_result

    # Prepare data for MRT model: merge sensitivity kappa into MRT trial data
    mrt_trial_data = mrt_trial_data.copy()
    mrt_trial_data = mrt_trial_data.merge(
        sensitivity_params[['participantId', 'kappa_sensitivity']],
        on='participantId', how='left'
    )
    # Remove rows with missing kappa_sensitivity
    mrt_trial_data = mrt_trial_data[~mrt_trial_data['kappa_sensitivity'].isna()]

    # Create accuracy column from is_correct if not present
    if 'accuracy' not in mrt_trial_data.columns and 'is_correct' in mrt_trial_data.columns:
        mrt_trial_data['accuracy'] = mrt_trial_data['is_correct'].astype(int)

    # Prepare data for VVIQ model: merge sensitivity kappa into VVIQ scores
    vviq_scores = vviq_scores.copy()
    vviq_scores = vviq_scores.merge(
        sensitivity_params[['participantId', 'kappa_sensitivity']],
        on='participantId', how='left'
    )
    vviq_scores = vviq_scores[~vviq_scores['kappa_sensitivity'].isna()]

    # Fit MRT mixed-effects models in R using lmer/glmer
    print("Fitting MRT mixed-effects models in R using sensitivity kappa...")

    with conversion.localconverter(robjects.default_converter + pandas2ri.converter):
        r_mrt_data = robjects.conversion.py2rpy(mrt_trial_data)
    robjects.globalenv['mrt_data'] = r_mrt_data

    mrt_results_list = []

    # Reaction time model with interaction
    try:
        mrt_formula = robjects.Formula('reaction_time_ms ~ kappa_sensitivity * rotation_angle + (1|participantId)')
        mrt_model = lmertest.lmer(mrt_formula, data=robjects.globalenv['mrt_data'])
        mrt_summary = base.summary(mrt_model)
        coef_table = np.array(mrt_summary.rx2('coefficients'))
        coef_names = list(mrt_summary.rx2('coefficients').rownames)
        for idx, name in enumerate(coef_names):
            mrt_results_list.append({
                'model_type': 'reaction_time',
                'effect_name': name,
                'coefficient': coef_table[idx, 0],
                'standard_error': coef_table[idx, 1],
                'p_value': coef_table[idx, 4]
            })
    except Exception as e:
        print(f"Error fitting MRT RT model in R: {e}")

    # Accuracy model (if accuracy column exists)
    if 'accuracy' in mrt_trial_data.columns:
        try:
            acc_formula = robjects.Formula('accuracy ~ kappa_sensitivity * rotation_angle + (1|participantId)')
            acc_model = lme4.glmer(acc_formula, data=robjects.globalenv['mrt_data'], family=robjects.r('binomial'))
            acc_summary = base.summary(acc_model)
            coef_table = np.array(acc_summary.rx2('coefficients'))
            coef_names = list(acc_summary.rx2('coefficients').rownames)
            for idx, name in enumerate(coef_names):
                mrt_results_list.append({
                    'model_type': 'accuracy',
                    'effect_name': name,
                    'coefficient': coef_table[idx, 0],
                    'standard_error': coef_table[idx, 1],
                    'p_value': coef_table[idx, 3] if coef_table.shape[1] > 3 else np.nan
                })
        except Exception as e:
            print(f"Error fitting MRT accuracy model in R: {e}")

    sensitivity_mrt_results = pd.DataFrame(mrt_results_list)

    # Fit VVIQ robust regression in R using MASS::rlm for all standardized score columns
    print("Fitting VVIQ robust regression in R using sensitivity kappa for all standardized scores...")
    vviq_score_columns = [col for col in vviq_scores.columns if col.endswith('_standardized')]
    sensitivity_vviq_results_list = []

    with conversion.localconverter(robjects.default_converter + pandas2ri.converter):
        r_vviq_data = robjects.conversion.py2rpy(vviq_scores)
    robjects.globalenv['vviq_data'] = r_vviq_data

    for score_col in vviq_score_columns:
        try:
            vviq_formula = robjects.Formula(f'{score_col} ~ kappa_sensitivity')
            vviq_model = mass.rlm(vviq_formula, data=robjects.globalenv['vviq_data'])
            vviq_summary = base.summary(vviq_model)
            coef_table = np.array(vviq_summary.rx2('coefficients'))
            coef_names = list(vviq_summary.rx2('coefficients').rownames)
            idx = coef_names.index('kappa_sensitivity')
            vviq_coef = coef_table[idx, 0]
            vviq_se = coef_table[idx, 1]
            # Extract t-statistic from summary (column 3)
            t_stat = coef_table[idx, 2]
            # Use correct residual degrees of freedom: n - p
            df_residual = len(vviq_scores) - len(coef_names)
            vviq_p = 2 * (1 - stats.t.cdf(abs(t_stat), df_residual))
            sensitivity_vviq_results_list.append({
                'model_name': score_col,
                'predictor_name': 'kappa_sensitivity',
                'coefficient': vviq_coef,
                'robust_standard_error': vviq_se,
                'p_value': vviq_p
            })
        except Exception as e:
            print(f"Error fitting VVIQ model for {score_col}: {e}")

    sensitivity_vviq_results = pd.DataFrame(sensitivity_vviq_results_list)

    print(f"Created sensitivity results:")
    print(f"  MRT models: {len(sensitivity_mrt_results)} effects")
    print(f"  VVIQ models: {len(sensitivity_vviq_results)} effects")
    
    return sensitivity_mrt_results, sensitivity_vviq_results, correlation_result

def validate_statistical_models(mrt_results, vviq_results, mrt_trial_data, vviq_scores, model_params):
    """
    Conduct comprehensive model validation including residual analysis and influence diagnostics.
    
    Parameters:
    mrt_results (pd.DataFrame): MRT model results
    vviq_results (pd.DataFrame): VVIQ model results
    mrt_trial_data (pd.DataFrame): MRT cleaned trial data
    vviq_scores (pd.DataFrame): VVIQ2 processed scores
    model_params (pd.DataFrame): Original model parameters
    
    Returns:
    tuple: (validation_diagnostics, influential_observations)
    """
    print("\nConducting model validation and diagnostic procedures...")

    validation_diagnostics = []
    influential_observations = []

    # MRT model validation
    print("Validating MRT mixed-effects model residuals and influence...")
    # Merge kappa_vonmises into MRT trial data
    mrt_trial_data = mrt_trial_data.copy()
    mrt_trial_data = mrt_trial_data.merge(
        model_params[['participantId', 'kappa_vonmises']],
        on='participantId', how='left'
    )
    mrt_trial_data = mrt_trial_data[~mrt_trial_data['kappa_vonmises'].isna()]
    mrt_trial_data = mrt_trial_data.reset_index(drop=True)

    # Fit OLS for diagnostics (approximate, since lmer is in R)
    import statsmodels.api as sm
    import statsmodels.formula.api as smf

    # OLS: reaction_time_ms ~ kappa_vonmises
    ols_mrt = smf.ols('reaction_time_ms ~ kappa_vonmises', data=mrt_trial_data).fit()
    residuals = ols_mrt.resid
    fitted = ols_mrt.fittedvalues

    # Normality test: Use Kolmogorov-Smirnov for n >= 5000, else Shapiro-Wilk
    n_mrt = len(residuals)
    if n_mrt >= 5000:
        # Standardize residuals for KS test
        standardized_resid = (residuals - np.mean(residuals)) / np.std(residuals)
        ks_stat, ks_p = stats.kstest(standardized_resid, 'norm')
        normality_test_type = 'Normality_Kolmogorov_Smirnov'
        normality_stat = ks_stat
        normality_p = ks_p
        normality_violated = ks_p < 0.05
        remedial_action = 'Transform_or_robust_methods' if normality_violated else 'None'
    else:
        shapiro_stat, shapiro_p = stats.shapiro(residuals)
        normality_test_type = 'Normality_Shapiro_Wilk'
        normality_stat = shapiro_stat
        normality_p = shapiro_p
        normality_violated = shapiro_p < 0.05
        remedial_action = 'Transform_or_robust_methods' if normality_violated else 'None'

    # Homoscedasticity test
    from statsmodels.stats.diagnostic import het_breuschpagan
    bp_test = het_breuschpagan(residuals, ols_mrt.model.exog)
    bp_stat, bp_p = bp_test[0], bp_test[1]

    # Outlier/influence diagnostics
    infl = ols_mrt.get_influence()
    cooks = infl.cooks_distance[0]
    leverage = infl.hat_matrix_diag
    std_resid = infl.resid_studentized_internal
    dffits = infl.dffits[0]
    # DFBETAS calculation
    dfbetas = infl.dfbetas

    # Outlier/influence flags
    cooks_cutoff = 4 / len(mrt_trial_data)
    leverage_cutoff = 2 * (ols_mrt.df_model + 1) / len(mrt_trial_data)
    std_resid_cutoff = 3

    outlier_flags = np.abs(std_resid) > std_resid_cutoff
    high_leverage_flags = leverage > leverage_cutoff
    high_influence_flags = cooks > cooks_cutoff

    validation_diagnostics.append({
        'model_name': 'MRT_RT',
        'diagnostic_type': normality_test_type,
        'test_statistic': normality_stat,
        'p_value': normality_p,
        'assumption_violated': normality_violated,
        'remedial_action': remedial_action,
        'num_outliers_detected': int(np.sum(outlier_flags)),
        'num_high_leverage_points': int(np.sum(high_leverage_flags)),
        'num_influential_observations': int(np.sum(high_influence_flags))
    })
    validation_diagnostics.append({
        'model_name': 'MRT_RT',
        'diagnostic_type': 'Homoscedasticity_Breusch_Pagan',
        'test_statistic': bp_stat,
        'p_value': bp_p,
        'assumption_violated': bp_p < 0.05,
        'remedial_action': 'None' if bp_p >= 0.05 else 'Robust_standard_errors',
        'num_outliers_detected': int(np.sum(outlier_flags)),
        'num_high_leverage_points': int(np.sum(high_leverage_flags)),
        'num_influential_observations': int(np.sum(high_influence_flags))
    })

    max_idx = min(len(high_influence_flags), len(outlier_flags), len(high_leverage_flags), len(mrt_trial_data))
    for idx, (i, row) in enumerate(mrt_trial_data.iterrows()):
        if idx >= max_idx:
            break
        # DFBETAS for kappa_vonmises (assume it's the second predictor if present)
        dfbetas_kappa = dfbetas[idx, 1] if dfbetas.shape[1] > 1 else np.nan
        dfbetas_threshold = 2 / np.sqrt(len(mrt_trial_data))
        dfbetas_kappa_flag = abs(dfbetas_kappa) > dfbetas_threshold if not np.isnan(dfbetas_kappa) else False
        if high_influence_flags[idx] or outlier_flags[idx] or high_leverage_flags[idx] or dfbetas_kappa_flag:
            influential_observations.append({
                'participantId': row['participantId'],
                'model_name': 'MRT_RT',
                'cooks_distance': cooks[idx],
                'leverage_value': leverage[idx],
                'standardized_residual': std_resid[idx],
                'dffits': float(dffits[idx]) if np.ndim(dffits) > 0 else dffits,
                'dfbetas_kappa': dfbetas_kappa,
                'dfbetas_kappa_flag': dfbetas_kappa_flag,
                'high_influence_flag': bool(high_influence_flags[idx]),
                'outlier_flag': bool(outlier_flags[idx]),
                'exclusion_recommended': bool(high_influence_flags[idx] or outlier_flags[idx] or dfbetas_kappa_flag)
            })

    # VVIQ model validation
    print("Validating VVIQ robust regression residuals and influence...")
    vviq_scores = vviq_scores.copy()
    vviq_scores = vviq_scores.merge(
        model_params[['participantId', 'kappa_vonmises']],
        on='participantId', how='left'
    )
    vviq_scores = vviq_scores[~vviq_scores['kappa_vonmises'].isna()]
    vviq_scores = vviq_scores.reset_index(drop=True)

    # Validate all standardized score columns
    vviq_score_columns = [col for col in vviq_scores.columns if col.endswith('_standardized')]
    for score_col in vviq_score_columns:
        ols_vviq = smf.ols(f'{score_col} ~ kappa_vonmises', data=vviq_scores).fit()
        residuals_vviq = ols_vviq.resid
        fitted_vviq = ols_vviq.fittedvalues

        # Normality test: Use Kolmogorov-Smirnov for n >= 5000, else Shapiro-Wilk
        n_vviq = len(residuals_vviq)
        if n_vviq >= 5000:
            standardized_resid_vviq = (residuals_vviq - np.mean(residuals_vviq)) / np.std(residuals_vviq)
            ks_stat, ks_p = stats.kstest(standardized_resid_vviq, 'norm')
            normality_test_type_vviq = 'Normality_Kolmogorov_Smirnov'
            normality_stat_vviq = ks_stat
            normality_p_vviq = ks_p
            normality_violated_vviq = ks_p < 0.05
        else:
            shapiro_stat_vviq, shapiro_p_vviq = stats.shapiro(residuals_vviq)
            normality_test_type_vviq = 'Normality_Shapiro_Wilk'
            normality_stat_vviq = shapiro_stat_vviq
            normality_p_vviq = shapiro_p_vviq
            normality_violated_vviq = shapiro_p_vviq < 0.05

        infl_vviq = ols_vviq.get_influence()
        cooks_vviq = infl_vviq.cooks_distance[0]
        leverage_vviq = infl_vviq.hat_matrix_diag
        std_resid_vviq = infl_vviq.resid_studentized_internal
        dffits_vviq = infl_vviq.dffits[0]
        dfbetas_vviq = infl_vviq.dfbetas

        cooks_cutoff_vviq = 4 / len(vviq_scores)
        leverage_cutoff_vviq = 2 * (ols_vviq.df_model + 1) / len(vviq_scores)
        std_resid_cutoff_vviq = 3

        outlier_flags_vviq = np.abs(std_resid_vviq) > std_resid_cutoff_vviq
        high_leverage_flags_vviq = leverage_vviq > leverage_cutoff_vviq
        high_influence_flags_vviq = cooks_vviq > cooks_cutoff_vviq

        validation_diagnostics.append({
            'model_name': f'VVIQ2_robust_{score_col}',
            'diagnostic_type': normality_test_type_vviq,
            'test_statistic': normality_stat_vviq,
            'p_value': normality_p_vviq,
            'assumption_violated': normality_violated_vviq,
            'remedial_action': 'Robust_regression_already_applied',
            'num_outliers_detected': int(np.sum(outlier_flags_vviq)),
            'num_high_leverage_points': int(np.sum(high_leverage_flags_vviq)),
            'num_influential_observations': int(np.sum(high_influence_flags_vviq))
        })

        max_idx_vviq = min(len(high_influence_flags_vviq), len(outlier_flags_vviq), len(high_leverage_flags_vviq), len(vviq_scores))
        for idx, (i, row) in enumerate(vviq_scores.iterrows()):
            if idx >= max_idx_vviq:
                break
            # DFBETAS for kappa_vonmises (assume it's the second predictor if present)
            dfbetas_kappa_vviq = dfbetas_vviq[idx, 1] if dfbetas_vviq.shape[1] > 1 else np.nan
            dfbetas_threshold_vviq = 2 / np.sqrt(len(vviq_scores))
            dfbetas_kappa_flag_vviq = abs(dfbetas_kappa_vviq) > dfbetas_threshold_vviq if not np.isnan(dfbetas_kappa_vviq) else False
            if high_influence_flags_vviq[idx] or outlier_flags_vviq[idx] or high_leverage_flags_vviq[idx] or dfbetas_kappa_flag_vviq:
                influential_observations.append({
                    'participantId': row['participantId'],
                    'model_name': f'VVIQ2_robust_{score_col}',
                    'cooks_distance': cooks_vviq[idx],
                    'leverage_value': leverage_vviq[idx],
                    'standardized_residual': std_resid_vviq[idx],
                    'dffits': float(dffits_vviq[idx]) if np.ndim(dffits_vviq) > 0 else dffits_vviq,
                    'dfbetas_kappa': dfbetas_kappa_vviq,
                    'dfbetas_kappa_flag': dfbetas_kappa_flag_vviq,
                    'high_influence_flag': bool(high_influence_flags_vviq[idx]),
                    'outlier_flag': bool(outlier_flags_vviq[idx]),
                    'exclusion_recommended': bool(high_influence_flags_vviq[idx] or outlier_flags_vviq[idx] or dfbetas_kappa_flag_vviq)
                })

    validation_df = pd.DataFrame(validation_diagnostics)
    influential_df = pd.DataFrame(influential_observations)

    print(f"Model validation completed:")
    print(f"  Diagnostic tests conducted: {len(validation_df)}")
    print(f"  Influential observations identified: {len(influential_df)}")
    print(f"  Models with assumption violations: {sum(validation_df['assumption_violated'])}")

    return validation_df, influential_df

def create_sensitivity_analysis_results(mrt_results, vviq_results, sensitivity_mrt_results, 
                                       sensitivity_vviq_results, correlation_result):
    """
    Create comprehensive sensitivity analysis results comparing original vs sensitivity models.
    
    Parameters:
    mrt_results (pd.DataFrame): Original MRT results
    vviq_results (pd.DataFrame): Original VVIQ results
    sensitivity_mrt_results (pd.DataFrame): Sensitivity MRT results
    sensitivity_vviq_results (pd.DataFrame): Sensitivity VVIQ results
    correlation_result (float): Correlation between original and sensitivity kappa
    
    Returns:
    pd.DataFrame: Sensitivity analysis results
    """
    print("\nCreating sensitivity analysis comparison results...")

    # Debugging output for shapes and effect names
    print(f"Original MRT results shape: {mrt_results.shape}")
    print(f"Original MRT effect names: {mrt_results['effect_name'].unique()}")
    print(f"Sensitivity MRT results shape: {sensitivity_mrt_results.shape}")
    print(f"Sensitivity MRT effect names: {sensitivity_mrt_results['effect_name'].unique()}")
    print(f"Original VVIQ results shape: {vviq_results.shape}")
    print(f"Sensitivity VVIQ results shape: {sensitivity_vviq_results.shape}")

    sensitivity_analysis_results = []

    # --- Improved matching logic for main effects and interactions ---

    # Helper to extract effect type and variable(s)
    def parse_effect(effect_name):
        # e.g., 'kappa_vonmises', 'kappa_vonmises:rotation_angle', etc.
        if ':' in effect_name:
            parts = effect_name.split(':')
            return 'interaction', set(parts)
        else:
            return 'main', set([effect_name])

    # Compare MRT results
    original_mrt = mrt_results[mrt_results['effect_name'].str.contains('kappa_vonmises', na=False)]
    print(f"Original MRT rows with 'kappa_vonmises' in effect_name: {len(original_mrt)}")

    for _, orig_row in original_mrt.iterrows():
        orig_type, orig_vars = parse_effect(orig_row['effect_name'])
        print(f"Matching MRT model_type: {orig_row['model_type']}, effect_name: {orig_row['effect_name']} (type: {orig_type})")
        # Find corresponding sensitivity result with same effect type and variables (replace kappa_vonmises with kappa_sensitivity)
        def match_sens(row):
            sens_type, sens_vars = parse_effect(row['effect_name'])
            # Replace kappa_vonmises with kappa_sensitivity in orig_vars for matching
            mapped_vars = set([v.replace('kappa_vonmises', 'kappa_sensitivity') for v in orig_vars])
            return (row['model_type'] == orig_row['model_type']) and (sens_type == orig_type) and (sens_vars == mapped_vars)
        sens_matches = sensitivity_mrt_results[sensitivity_mrt_results.apply(match_sens, axis=1)]
        print(f"  Found {len(sens_matches)} sensitivity matches for MRT model_type {orig_row['model_type']} and effect {orig_row['effect_name']}")
        if len(sens_matches) > 0:
            sens_row = sens_matches.iloc[0]
            print(f"    Sensitivity effect_name: {sens_row['effect_name']}, coefficient: {sens_row['coefficient']}, p: {sens_row['p_value']}")
            coeff_diff = sens_row['coefficient'] - orig_row['coefficient']
            conclusion_changed = (orig_row['p_value'] < 0.05) != (sens_row['p_value'] < 0.05)
            sensitivity_analysis_results.append({
                'analysis_type': 'MRT',
                'model_name': f"MRT_{orig_row['model_type']}",
                'original_coefficient': orig_row['coefficient'],
                'original_p_value': orig_row['p_value'],
                'sensitivity_coefficient': sens_row['coefficient'],
                'sensitivity_p_value': sens_row['p_value'],
                'coefficient_difference': coeff_diff,
                'conclusion_changed': conclusion_changed,
                'correlation_original_sensitivity_kappa': correlation_result
            })
        else:
            print(f"    No sensitivity match found for MRT model_type {orig_row['model_type']} and effect {orig_row['effect_name']}")

    # Compare VVIQ results
    print(f"Original VVIQ results columns: {list(vviq_results.columns)}")
    print(f"Original VVIQ predictor names: {vviq_results['predictor_name'].unique() if 'predictor_name' in vviq_results.columns else 'No predictor_name column'}")
    # Use flexible matching for VVIQ
    original_vviq = vviq_results[vviq_results['predictor_name'].str.contains('kappa_vonmises', na=False)]
    print(f"Original VVIQ rows with 'kappa_vonmises' in predictor_name: {len(original_vviq)}")

    for _, orig_row in original_vviq.iterrows():
        # Use outcome_variable if present, else model_name
        outcome_var = orig_row['outcome_variable'] if 'outcome_variable' in orig_row else orig_row['model_name']
        print(f"Matching VVIQ model_name: {orig_row['model_name']}, predictor_name: {orig_row['predictor_name']}")
        # Find corresponding sensitivity result with same model_name and predictor_name replaced
        sens_matches = sensitivity_vviq_results[
            (sensitivity_vviq_results['model_name'] == outcome_var) &
            (sensitivity_vviq_results['predictor_name'] == orig_row['predictor_name'].replace('kappa_vonmises', 'kappa_sensitivity'))
        ]
        print(f"  Found {len(sens_matches)} sensitivity matches for VVIQ model_name {outcome_var}")
        if len(sens_matches) > 0:
            sens_row = sens_matches.iloc[0]
            print(f"    Sensitivity predictor_name: {sens_row['predictor_name'] if 'predictor_name' in sens_row else 'N/A'}, coefficient: {sens_row['coefficient']}, p: {sens_row['p_value']}")
            coeff_diff = sens_row['coefficient'] - orig_row['coefficient']
            conclusion_changed = (orig_row['p_value'] < 0.05) != (sens_row['p_value'] < 0.05)
            sensitivity_analysis_results.append({
                'analysis_type': 'VVIQ',
                'model_name': orig_row['model_name'],
                'original_coefficient': orig_row['coefficient'],
                'original_p_value': orig_row['p_value'],
                'sensitivity_coefficient': sens_row['coefficient'],
                'sensitivity_p_value': sens_row['p_value'],
                'coefficient_difference': coeff_diff,
                'conclusion_changed': conclusion_changed,
                'correlation_original_sensitivity_kappa': correlation_result
            })
        else:
            print(f"    No sensitivity match found for VVIQ model_name {outcome_var}")

    sensitivity_df = pd.DataFrame(sensitivity_analysis_results)

    # Only keep the required columns in the output
    required_columns = [
        'analysis_type',
        'model_name',
        'original_coefficient',
        'original_p_value',
        'sensitivity_coefficient',
        'sensitivity_p_value',
        'coefficient_difference',
        'conclusion_changed',
        'correlation_original_sensitivity_kappa'
    ]
    sensitivity_df = sensitivity_df[required_columns]

    print(f"Sensitivity analysis results:")
    print(f"  Total comparisons: {len(sensitivity_df)}")
    print(f"  Conclusions changed: {sum(sensitivity_df['conclusion_changed'])}")
    print(f"  Mean coefficient difference: {sensitivity_df['coefficient_difference'].mean():.4f}")
    print(f"  Correlation original-sensitivity kappa: {correlation_result:.3f}")

    return sensitivity_df

def save_output_files(sensitivity_results, validation_diagnostics, influential_observations, stability_results=None):
    """
    Save all output files with timestamp.
    
    Parameters:
    sensitivity_results (pd.DataFrame): Sensitivity analysis results
    validation_diagnostics (pd.DataFrame): Model validation diagnostics
    influential_observations (pd.DataFrame): Influential observations data
    stability_results (dict): Model stability results (optional)
    """
    print("\nSaving output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save sensitivity analysis results
    sensitivity_file = f"outputs/sensitivity_analysis_results_{timestamp}.csv"
    sensitivity_results.to_csv(sensitivity_file, index=False)
    print(f"Saved sensitivity analysis results to: {sensitivity_file}")
    
    # Save model validation diagnostics
    validation_file = f"outputs/model_validation_diagnostics_{timestamp}.csv"
    validation_diagnostics.to_csv(validation_file, index=False)
    print(f"Saved model validation diagnostics to: {validation_file}")
    
    # Save influential observations
    influential_file = f"outputs/influential_observations_{timestamp}.csv"
    influential_observations.to_csv(influential_file, index=False)
    print(f"Saved influential observations to: {influential_file}")

    print("\nOutput file contents preview:")
    print("\nSensitivity analysis results:")
    print(f"Columns: {list(sensitivity_results.columns)}")
    print(sensitivity_results.head(2))

    print("\nModel validation diagnostics:")
    print(f"Columns: {list(validation_diagnostics.columns)}")
    print(validation_diagnostics.head(2))

    print("\nInfluential observations:")
    print(f"Columns: {list(influential_observations.columns)}")
    print(influential_observations.head(2))

def create_validation_report(sensitivity_results, validation_diagnostics, influential_observations, stability_results):
    """
    Generate a comprehensive plain text model validation report.
    """
    from datetime import datetime
    import os

    os.makedirs('outputs', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"outputs/model_validation_report_{timestamp}.txt"

    with open(report_file, "w") as f:
        f.write("MODEL VALIDATION REPORT\n")
        f.write("="*80 + "\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        # Sensitivity analysis summary
        f.write("Sensitivity Analysis Results\n")
        f.write("-"*80 + "\n")
        if sensitivity_results is not None and not sensitivity_results.empty:
            f.write(f"Total comparisons: {len(sensitivity_results)}\n")
            f.write(f"Conclusions changed: {sum(sensitivity_results['conclusion_changed'])}\n")
            f.write(f"Mean coefficient difference: {sensitivity_results['coefficient_difference'].mean():.4f}\n")
            f.write(f"Correlation original-sensitivity kappa: {sensitivity_results['correlation_original_sensitivity_kappa'].iloc[0]:.3f}\n")
            f.write("\n")
        else:
            f.write("No sensitivity results available.\n\n")

        # Model validation diagnostics
        f.write("Model Validation Diagnostics\n")
        f.write("-"*80 + "\n")
        if validation_diagnostics is not None and not validation_diagnostics.empty:
            for _, row in validation_diagnostics.iterrows():
                f.write(f"Model: {row['model_name']}\n")
                f.write(f"  Diagnostic: {row['diagnostic_type']}\n")
                f.write(f"  Test statistic: {row['test_statistic']:.4f}\n")
                f.write(f"  p-value: {row['p_value']:.4g}\n")
                f.write(f"  Assumption violated: {row['assumption_violated']}\n")
                f.write(f"  Remedial action: {row['remedial_action']}\n")
                f.write(f"  Outliers detected: {row['num_outliers_detected']}\n")
                f.write(f"  High leverage points: {row['num_high_leverage_points']}\n")
                f.write(f"  Influential observations: {row['num_influential_observations']}\n")
                f.write("\n")
        else:
            f.write("No validation diagnostics available.\n\n")

        # Influential observations
        f.write("Influential Observations\n")
        f.write("-"*80 + "\n")
        if influential_observations is not None and not influential_observations.empty:
            f.write(f"Total influential observations: {len(influential_observations)}\n")
            f.write("Sample influential observations (first 5):\n")
            f.write(str(influential_observations.head(5)))
            f.write("\n\n")
        else:
            f.write("No influential observations detected.\n\n")

        # Model stability results
        f.write("Model Stability Results\n")
        f.write("-"*80 + "\n")
        if stability_results is not None:
            if 'mrt_comparison' in stability_results and stability_results['mrt_comparison'] is not None:
                f.write("MRT Model Stability Comparison:\n")
                f.write(str(stability_results['mrt_comparison'].head(5)))
                f.write("\n\n")
            if 'vviq_comparison' in stability_results and stability_results['vviq_comparison'] is not None:
                f.write("VVIQ Model Stability Comparison:\n")
                f.write(str(stability_results['vviq_comparison'].head(5)))
                f.write("\n\n")
        else:
            f.write("No model stability results available.\n\n")

        f.write("="*80 + "\n")
        f.write("END OF REPORT\n")

    print(f"Saved model validation report to: {report_file}")

def main():
    """
    Main execution function for sensitivity analysis and model validation.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting sensitivity analysis and model validation script...")
        print(f"Script started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load input data
        trial_data, model_params, mrt_results, vviq_results, vviq_scores, mrt_trial_data = load_input_data()
        if trial_data is None:
            print("Error: Failed to load input data")
            return 1
        
        # Print key experimental design parameters
        print("\nExperimental design parameters:")
        if 'set_size' in trial_data.columns:
            print(f"Set size values: {sorted(trial_data['set_size'].unique())}")
        if 'delay_duration' in trial_data.columns:
            print(f"Delay values: {sorted(trial_data['delay_duration'].unique())}")
        if 'rotation_angle' in trial_data.columns:
            print(f"Rotation angle values: {sorted(trial_data['rotation_angle'].unique())}")
        
        # Classify guess trials
        trial_data_classified = classify_guess_trials(trial_data, model_params)
        if trial_data_classified is None:
            print("Error: Failed to classify guess trials")
            return 1
        
        # Re-fit models on memory-only trials
        sensitivity_params = fit_vonmises_memory_only(trial_data_classified)
        if sensitivity_params is None or len(sensitivity_params) == 0:
            print("Error: Failed to fit sensitivity models")
            return 1
        
        # Re-run statistical models
        sensitivity_mrt_results, sensitivity_vviq_results, correlation_result = rerun_statistical_models(
            model_params, sensitivity_params, mrt_results, vviq_results, vviq_scores, mrt_trial_data
        )
        
        if sensitivity_mrt_results is None or sensitivity_vviq_results is None:
            print("Error: Failed to re-run statistical models")
            return 1
        
        # Validate statistical models
        validation_diagnostics, influential_observations = validate_statistical_models(
            mrt_results, vviq_results, mrt_trial_data, vviq_scores, model_params
        )
        
        if validation_diagnostics is None or influential_observations is None:
            print("Error: Failed to validate statistical models")
            return 1
        
        # Model stability analysis (Step 4)
        stability_results = assess_model_stability(
            mrt_results, vviq_results, mrt_trial_data, vviq_scores, model_params, influential_observations
        )
        
        # Create sensitivity analysis results
        sensitivity_results = create_sensitivity_analysis_results(
            mrt_results, vviq_results, sensitivity_mrt_results, 
            sensitivity_vviq_results, correlation_result
        )
        
        if sensitivity_results is None:
            print("Error: Failed to create sensitivity analysis results")
            return 1
        
        # Save output files
        save_output_files(sensitivity_results, validation_diagnostics, influential_observations, stability_results)

        # Create model validation report
        create_validation_report(sensitivity_results, validation_diagnostics, influential_observations, stability_results)
        
        print(f"\nScript completed successfully at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

def assess_model_stability(mrt_results, vviq_results, mrt_trial_data, vviq_scores, model_params, influential_observations):
    """
    Assess model stability by re-running original models after excluding influential participants.
    Returns a dictionary of DataFrames with stability results for MRT and VVIQ models,
    and includes coefficient comparison with original models.
    """
    print("\nAssessing model stability by excluding influential participants...")

    # Identify influential participants for each model
    mrt_influential = influential_observations[
        (influential_observations['model_name'] == 'MRT_RT') &
        (influential_observations['exclusion_recommended'])
    ]
    mrt_exclude_ids = set(mrt_influential['participantId'])

    vviq_influential = influential_observations[
        influential_observations['model_name'].str.startswith('VVIQ2_robust_') &
        (influential_observations['exclusion_recommended'])
    ]
    vviq_exclude_ids = set(vviq_influential['participantId'])

    # Exclude from MRT trial data
    mrt_trial_data_stable = mrt_trial_data[~mrt_trial_data['participantId'].isin(mrt_exclude_ids)].copy()
    # Exclude from VVIQ scores
    vviq_scores_stable = vviq_scores[~vviq_scores['participantId'].isin(vviq_exclude_ids)].copy()

    # Merge kappa_vonmises into both
    mrt_trial_data_stable = mrt_trial_data_stable.merge(
        model_params[['participantId', 'kappa_vonmises']],
        on='participantId', how='left'
    )
    mrt_trial_data_stable = mrt_trial_data_stable[~mrt_trial_data_stable['kappa_vonmises'].isna()]
    vviq_scores_stable = vviq_scores_stable.merge(
        model_params[['participantId', 'kappa_vonmises']],
        on='participantId', how='left'
    )
    vviq_scores_stable = vviq_scores_stable[~vviq_scores_stable['kappa_vonmises'].isna()]

    # Use rpy2 to refit original R models on filtered data
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri, conversion
    from rpy2.robjects.packages import importr
    import numpy as np

    base = importr('base')
    lme4 = importr('lme4')
    lmertest = importr('lmerTest')
    mass = importr('MASS')

    # MRT stability results (mixed-effects in R)
    mrt_stability_results = []
    if len(mrt_trial_data_stable) > 0:
        with conversion.localconverter(robjects.default_converter + pandas2ri.converter):
            r_mrt_data = robjects.conversion.py2rpy(mrt_trial_data_stable)
        robjects.globalenv['mrt_data_stable'] = r_mrt_data
        try:
            mrt_formula = robjects.Formula('reaction_time_ms ~ kappa_vonmises * rotation_angle + (1|participantId)')
            mrt_model = lmertest.lmer(mrt_formula, data=robjects.globalenv['mrt_data_stable'])
            mrt_summary = base.summary(mrt_model)
            coef_table = np.array(mrt_summary.rx2('coefficients'))
            coef_names = list(mrt_summary.rx2('coefficients').rownames)
            for idx, name in enumerate(coef_names):
                mrt_stability_results.append({
                    'model_type': 'reaction_time',
                    'effect_name': name,
                    'coefficient': coef_table[idx, 0],
                    'standard_error': coef_table[idx, 1],
                    'p_value': coef_table[idx, 4]
                })
        except Exception as e:
            print(f"Error fitting MRT RT model in R (stability): {e}")

    mrt_stability_df = pd.DataFrame(mrt_stability_results)

    # VVIQ stability results (robust regression in R)
    vviq_score_columns = [col for col in vviq_scores_stable.columns if col.endswith('_standardized')]
    vviq_stability_results = []
    if len(vviq_scores_stable) > 0:
        with conversion.localconverter(robjects.default_converter + pandas2ri.converter):
            r_vviq_data = robjects.conversion.py2rpy(vviq_scores_stable)
        robjects.globalenv['vviq_data_stable'] = r_vviq_data
        for score_col in vviq_score_columns:
            try:
                vviq_formula = robjects.Formula(f'{score_col} ~ kappa_vonmises')
                vviq_model = mass.rlm(vviq_formula, data=robjects.globalenv['vviq_data_stable'])
                vviq_summary = base.summary(vviq_model)
                coef_table = np.array(vviq_summary.rx2('coefficients'))
                coef_names = list(vviq_summary.rx2('coefficients').rownames)
                idx = coef_names.index('kappa_vonmises')
                vviq_coef = coef_table[idx, 0]
                vviq_se = coef_table[idx, 1]
                t_stat = coef_table[idx, 2]
                df_residual = len(vviq_scores_stable) - len(coef_names)
                vviq_p = 2 * (1 - stats.t.cdf(abs(t_stat), df_residual))
                vviq_stability_results.append({
                    'model_name': score_col,
                    'predictor_name': 'kappa_vonmises',
                    'coefficient': vviq_coef,
                    'standard_error': vviq_se,
                    'p_value': vviq_p
                })
            except Exception as e:
                print(f"Error fitting VVIQ model for {score_col} (stability): {e}")
    vviq_stability_df = pd.DataFrame(vviq_stability_results)

    # --- Coefficient comparison with original models ---
    print(f"\nModel stability analysis completed:")
    print(f"  MRT stability results: {len(mrt_stability_df)} effects")
    print(f"  VVIQ stability results: {len(vviq_stability_df)} effects")

    # Compare MRT coefficients
    print("\nMRT model coefficient stability comparison:")
    mrt_comparison = []
    mrt_comparison_df = None  # Ensure variable is always defined
    orig_effects = set(zip(mrt_results['effect_name'], mrt_results['model_type']))
    stable_effects = set(zip(mrt_stability_df['effect_name'], mrt_stability_df['model_type']))
    common_effects = orig_effects & stable_effects
    for effect, model_type in common_effects:
        orig_row = mrt_results[(mrt_results['effect_name'] == effect) & (mrt_results['model_type'] == model_type)].iloc[0]
        stable_row = mrt_stability_df[(mrt_stability_df['effect_name'] == effect) & (mrt_stability_df['model_type'] == model_type)].iloc[0]
        orig_coef = orig_row['coefficient']
        stable_coef = stable_row['coefficient']
        pct_change = 100 * (stable_coef - orig_coef) / orig_coef if orig_coef != 0 else np.nan
        print(f"  Effect: {effect} | Model type: {model_type} | Original: {orig_coef:.4f} | Stability: {stable_coef:.4f} | Δ: {stable_coef - orig_coef:+.4f} ({pct_change:+.2f}%)")
        mrt_comparison.append({
            'effect_name': effect,
            'model_type': model_type,
            'original_coefficient': orig_coef,
            'stability_coefficient': stable_coef,
            'coefficient_difference': stable_coef - orig_coef,
            'percent_change': pct_change,
            'original_p_value': orig_row['p_value'],
            'stability_p_value': stable_row['p_value']
        })
    if len(mrt_comparison) > 0:
        mrt_comparison_df = pd.DataFrame(mrt_comparison)
        print("\nMRT coefficient percent changes summary:")
        print(mrt_comparison_df[['effect_name', 'coefficient_difference', 'percent_change', 'original_p_value', 'stability_p_value']])
    else:
        print("  No matching effects found for MRT stability comparison.")

    # Compare VVIQ coefficients
    print("\nVVIQ model coefficient stability comparison:")
    vviq_comparison = []
    vviq_comparison_df = None  # Ensure variable is always defined
    for _, orig_row in vviq_results.iterrows():
        outcome_var = orig_row['outcome_variable'] if 'outcome_variable' in orig_row else orig_row['model_name']
        predictor = orig_row['predictor_name'] if 'predictor_name' in orig_row else None
        stable_match = vviq_stability_df[
            (vviq_stability_df['model_name'] == outcome_var) &
            (vviq_stability_df['predictor_name'] == predictor)
        ]
        if len(stable_match) > 0:
            stable_row = stable_match.iloc[0]
            orig_coef = orig_row['coefficient']
            stable_coef = stable_row['coefficient']
            pct_change = 100 * (stable_coef - orig_coef) / orig_coef if orig_coef != 0 else np.nan
            print(f"  Model: {outcome_var} | Predictor: {predictor} | Original: {orig_coef:.4f} | Stability: {stable_coef:.4f} | Δ: {stable_coef - orig_coef:+.4f} ({pct_change:+.2f}%)")
            vviq_comparison.append({
                'model_name': outcome_var,
                'predictor_name': predictor,
                'original_coefficient': orig_coef,
                'stability_coefficient': stable_coef,
                'coefficient_difference': stable_coef - orig_coef,
                'percent_change': pct_change,
                'original_p_value': orig_row['p_value'],
                'stability_p_value': stable_row['p_value']
            })
    if len(vviq_comparison) > 0:
        vviq_comparison_df = pd.DataFrame(vviq_comparison)
        print("\nVVIQ coefficient percent changes summary:")
        print(vviq_comparison_df[['model_name', 'predictor_name', 'coefficient_difference', 'percent_change', 'original_p_value', 'stability_p_value']])
    else:
        print("  No matching effects found for VVIQ stability comparison.")

    return {
        'mrt': mrt_stability_df,
        'vviq': vviq_stability_df,
        'mrt_comparison': mrt_comparison_df,
        'vviq_comparison': vviq_comparison_df
    }

if __name__ == "__main__":
    exit(main())
