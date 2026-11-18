#!/usr/bin/env python3
"""
Control Analysis Script for VWM-MRT-VVIQ2 Study
Re-runs primary analyses with domain-general control variables.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
from scipy import stats
from statsmodels.stats.multitest import fdrcorrection

import statsmodels.api as sm
import statsmodels.formula.api as smf

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

def load_input_files():
    """
    Load all required input files and validate column presence.
    
    Returns:
    tuple: (mrt_data, mixture_data, vviq_data, cognitive_data) DataFrames
    """
    print("Loading input files...")
    
    # Find latest files
    mrt_file = find_latest_file("outputs/VWM_MRT_cleaned_data_*.csv")
    mixture_file = find_latest_file("outputs/VWM_mixture_model_parameters_*.csv")
    vviq_file = find_latest_file("outputs/VVIQ2_cleaned_scores_*.csv")
    cognitive_file = find_latest_file("outputs/cognitive_performance_metrics_*.csv")
    
    if not all([mrt_file, mixture_file, vviq_file, cognitive_file]):
        print("ERROR: Could not find all required input files")
        missing = []
        if not mrt_file: missing.append("VWM_MRT_cleaned_data")
        if not mixture_file: missing.append("VWM_mixture_model_parameters")
        if not vviq_file: missing.append("VVIQ2_cleaned_scores")
        if not cognitive_file: missing.append("cognitive_performance_metrics")
        print(f"Missing files: {missing}")
        return None, None, None, None
    
    print(f"Found files:")
    print(f"  MRT data: {mrt_file}")
    print(f"  Mixture model: {mixture_file}")
    print(f"  VVIQ data: {vviq_file}")
    print(f"  Cognitive metrics: {cognitive_file}")
    
    # Load MRT data
    print("\nLoading MRT data...")
    mrt_data = pd.read_csv(mrt_file)
    print(f"MRT data columns: {list(mrt_data.columns)}")
    print("First 3 rows of MRT data:")
    print(mrt_data.head(3))
    
    # Validate MRT columns
    required_mrt_cols = ['participantId', 'isPractice', 'MRT_trial', 'MRT_angle_degrees', 
                        'MRT_isCorrect', 'MRT_rt_ms', 'MRT_block', 'excluded_from_MRT', 'trial_excluded']
    missing_mrt = [col for col in required_mrt_cols if col not in mrt_data.columns]
    if missing_mrt:
        print(f"ERROR: Missing MRT columns: {missing_mrt}")
        return None, None, None, None
    
    # Load mixture model data
    print("\nLoading mixture model data...")
    mixture_data = pd.read_csv(mixture_file)
    print(f"Mixture model columns: {list(mixture_data.columns)}")
    print("First 3 rows of mixture model data:")
    print(mixture_data.head(3))
    
    # Validate mixture columns
    required_mixture_cols = ['participantId', 'kappa_concentration', 'model_converged', 'fit_quality_flag']
    missing_mixture = [col for col in required_mixture_cols if col not in mixture_data.columns]
    if missing_mixture:
        print(f"ERROR: Missing mixture model columns: {missing_mixture}")
        return None, None, None, None
    
    # Load VVIQ data
    print("\nLoading VVIQ data...")
    vviq_data = pd.read_csv(vviq_file)
    print(f"VVIQ data columns: {list(vviq_data.columns)}")
    print("First 3 rows of VVIQ data:")
    print(vviq_data.head(3))
    
    # Validate VVIQ columns
    required_vviq_cols = ['PROLIFIC_PID', 'total_score', 'familiar_person_score', 'sunrise_score',
                         'shop_front_score', 'countryside_score', 'driving_score', 'beach_score',
                         'railway_station_score', 'garden_score', 'excluded']
    missing_vviq = [col for col in required_vviq_cols if col not in vviq_data.columns]
    if missing_vviq:
        print(f"ERROR: Missing VVIQ columns: {missing_vviq}")
        return None, None, None, None
    
    # Load cognitive metrics data
    print("\nLoading cognitive metrics data...")
    cognitive_data = pd.read_csv(cognitive_file)
    print(f"Cognitive metrics columns: {list(cognitive_data.columns)}")
    print("First 3 rows of cognitive metrics data:")
    print(cognitive_data.head(3))
    
    # Validate cognitive columns
    required_cognitive_cols = ['participantId', 'VWM_mean_absolute_error', 
                              'MRT_RT_coefficient_variation', 'focus_loss_duration_trials_sec']
    missing_cognitive = [col for col in required_cognitive_cols if col not in cognitive_data.columns]
    if missing_cognitive:
        print(f"ERROR: Missing cognitive metrics columns: {missing_cognitive}")
        return None, None, None, None
    
    print("\nAll input files loaded successfully!")
    return mrt_data, mixture_data, vviq_data, cognitive_data

def prepare_merged_dataset(mrt_data, mixture_data, vviq_data, cognitive_data):
    """
    Merge all datasets and filter for complete data.
    
    Parameters:
    mrt_data (DataFrame): MRT trial-level data
    mixture_data (DataFrame): Mixture model parameters
    vviq_data (DataFrame): VVIQ scores
    cognitive_data (DataFrame): Cognitive performance metrics
    
    Returns:
    tuple: (participant_data, trial_data) merged DataFrames
    """
    print("\nPreparing merged dataset...")
    
    # Print unique values for key experimental design parameters
    print("\nKey experimental design parameters:")
    print(f"MRT angles: {sorted(mrt_data['MRT_angle_degrees'].unique())}")
    print(f"MRT blocks: {sorted(mrt_data['MRT_block'].unique())}")
    print(f"Practice values: {sorted(mrt_data['isPractice'].unique())}")
    
    # Filter datasets for valid participants
    print("\nFiltering datasets...")
    
    # Filter mixture model data for converged models
    print(f"Mixture model data before filtering: {len(mixture_data)} participants")
    mixture_filtered = mixture_data[
        (mixture_data['model_converged'] == True) & 
        (mixture_data['fit_quality_flag'] == 'good')
    ].copy()
    print(f"Mixture model data after filtering: {len(mixture_filtered)} participants")
    
    # Filter VVIQ data for non-excluded participants
    print(f"VVIQ data before filtering: {len(vviq_data)} participants")
    vviq_filtered = vviq_data[vviq_data['excluded'] == False].copy()
    print(f"VVIQ data after filtering: {len(vviq_filtered)} participants")
    
    # Rename PROLIFIC_PID to participantId for merging
    vviq_filtered = vviq_filtered.rename(columns={'PROLIFIC_PID': 'participantId'})
    
    # Filter cognitive data for complete cases
    print(f"Cognitive data before filtering: {len(cognitive_data)} participants")
    cognitive_filtered = cognitive_data.dropna(subset=[
        'VWM_mean_absolute_error', 'MRT_RT_coefficient_variation', 'focus_loss_duration_trials_sec'
    ]).copy()
    print(f"Cognitive data after filtering: {len(cognitive_filtered)} participants")
    
    # Merge participant-level data
    print("\nMerging participant-level data...")
    participant_data = mixture_filtered.merge(vviq_filtered, on='participantId', how='inner')
    print(f"After mixture-VVIQ merge: {len(participant_data)} participants")
    
    participant_data = participant_data.merge(cognitive_filtered, on='participantId', how='inner')
    print(f"After adding cognitive metrics: {len(participant_data)} participants")
    
    if len(participant_data) == 0:
        print("ERROR: No participants remain after merging datasets")
        print("This indicates a data compatibility issue between input files")
        return None, None

    print(f"Final participant dataset columns: {list(participant_data.columns)}")
    print("First 2 rows of participant data:")
    print(participant_data.head(2))
    
    # Filter MRT trial data for valid participants and trials
    print("\nFiltering MRT trial data...")
    valid_participants = set(participant_data['participantId'].unique())
    
    # Filter MRT data
    mrt_filtered = mrt_data[
        (mrt_data['participantId'].isin(valid_participants)) &
        (mrt_data['isPractice'] == False) &
        (mrt_data['MRT_block'] != 'practice') &
        (mrt_data['excluded_from_MRT'] == False) &
        (mrt_data['trial_excluded'] == False)
    ].copy()
    
    print(f"MRT trials after filtering: {len(mrt_filtered)} trials")
    print(f"MRT participants after filtering: {mrt_filtered['participantId'].nunique()} participants")
    
    # Merge trial data with participant data
    trial_data = mrt_filtered.merge(
        participant_data[['participantId', 'kappa_concentration', 
                         'VWM_mean_absolute_error', 'MRT_RT_coefficient_variation', 
                         'focus_loss_duration_trials_sec']], 
        on='participantId', how='inner'
    )

    if len(trial_data) == 0:
        print("ERROR: No MRT trials remain after filtering")
        print("This indicates a data compatibility issue between input files or filtering criteria")
        return None, None
    
    print(f"Final trial dataset: {len(trial_data)} trials from {trial_data['participantId'].nunique()} participants")
    print(f"Trial dataset columns: {list(trial_data.columns)}")
    print("First 2 rows of trial data:")
    print(trial_data.head(2))
    
    return participant_data, trial_data

def run_original_models(trial_data, participant_data):
    """
    Run original models without control variables for comparison.

    Parameters:
    trial_data (DataFrame): Trial-level data
    participant_data (DataFrame): Participant-level data

    Returns:
    dict: Original model results
    """
    print("\nRunning original models for comparison...")

    results = {}

    # Original MRT Accuracy Model (GEE with binomial family)
    print("Running original MRT accuracy model...")

    trial_data_r = trial_data.copy()
    acc_cols = ['MRT_isCorrect', 'kappa_concentration', 'MRT_angle_degrees', 'participantId']
    for col in ['MRT_isCorrect', 'kappa_concentration']:
        trial_data_r[col] = pd.to_numeric(trial_data_r[col], errors='coerce')
    acc_data = trial_data_r[acc_cols].replace([np.inf, -np.inf], np.nan).dropna()

    try:
        # Use GEE for binomial with participantId as group
        model = smf.gee(
            "MRT_isCorrect ~ kappa_concentration * C(MRT_angle_degrees)",
            groups="participantId",
            data=acc_data,
            family=sm.families.Binomial()
        )
        original_acc_model = model.fit()
        results['original_accuracy'] = {
            'model': original_acc_model,
            'nobs': len(acc_data)
        }
        print("Original accuracy model completed successfully")
    except Exception as e:
        print(f"Error in original accuracy model: {e}")
        results['original_accuracy'] = None

    # Original MRT RT Model (correct trials only, mixedlm)
    print("Running original MRT RT model...")

    correct_trials = trial_data_r[trial_data_r['MRT_isCorrect'] == True].copy()
    correct_trials['log_rt'] = np.log(correct_trials['MRT_rt_ms'])
    for col in ['log_rt', 'kappa_concentration']:
        correct_trials[col] = pd.to_numeric(correct_trials[col], errors='coerce')
    rt_cols = ['log_rt', 'kappa_concentration', 'MRT_angle_degrees', 'participantId']
    rt_data = correct_trials[rt_cols].replace([np.inf, -np.inf], np.nan).dropna()

    try:
        # Mixed effects model with random intercept for participantId
        original_rt_model = smf.mixedlm(
            "log_rt ~ kappa_concentration * C(MRT_angle_degrees)",
            data=rt_data,
            groups=rt_data["participantId"]
        ).fit()
        results['original_rt'] = {
            'model': original_rt_model,
            'nobs': len(rt_data)
        }
        print("Original RT model completed successfully")
    except Exception as e:
        print(f"Error in original RT model: {e}")
        results['original_rt'] = None

    # Original VVIQ regressions (robust linear model)
    print("Running original VVIQ regressions...")

    vviq_outcomes = ['total_score', 'familiar_person_score', 'sunrise_score', 'shop_front_score',
                     'countryside_score', 'driving_score', 'beach_score', 'railway_station_score', 'garden_score']

    vviq_results = {}

    for outcome in vviq_outcomes:
        print(f"Running original regression for {outcome}...")

        vviq_cols = [outcome, 'kappa_concentration']
        model_data = participant_data[vviq_cols].copy()
        for col in vviq_cols:
            model_data[col] = pd.to_numeric(model_data[col], errors='coerce')
        model_data = model_data.replace([np.inf, -np.inf], np.nan).dropna()
        for col in model_data.select_dtypes(include=[np.number]).columns:
            model_data[col] = model_data[col].astype(float)

        if len(model_data) < 10:
            print(f"Insufficient data for {outcome}: {len(model_data)} observations")
            vviq_results[outcome] = None
            continue

        try:
            model = smf.rlm(f"{outcome} ~ kappa_concentration", data=model_data, M=sm.robust.norms.HuberT())
            result = model.fit()
            vviq_results[outcome] = {
                'model': result,
                'nobs': len(model_data)
            }
            print(f"Original {outcome} regression completed successfully (n={len(model_data)})")
        except Exception as e:
            print(f"Error in original {outcome} regression: {e}")
            vviq_results[outcome] = None

    results['original_vviq'] = vviq_results

    return results

def run_control_models(trial_data, participant_data):
    """
    Run models with control variables.

    Parameters:
    trial_data (DataFrame): Trial-level data
    participant_data (DataFrame): Participant-level data

    Returns:
    dict: Control model results
    """
    print("\nRunning control models...")

    results = {}

    # Control MRT Accuracy Model (GEE with binomial family)
    print("Running control MRT accuracy model...")

    trial_data_r = trial_data.copy()
    acc_cols = ['MRT_isCorrect', 'kappa_concentration', 'MRT_angle_degrees', 'participantId',
                'VWM_mean_absolute_error', 'MRT_RT_coefficient_variation', 'focus_loss_duration_trials_sec']
    for col in ['MRT_isCorrect', 'kappa_concentration', 'VWM_mean_absolute_error', 'MRT_RT_coefficient_variation', 'focus_loss_duration_trials_sec']:
        trial_data_r[col] = pd.to_numeric(trial_data_r[col], errors='coerce')
    acc_data = trial_data_r[acc_cols].replace([np.inf, -np.inf], np.nan).dropna()

    try:
        model = smf.gee(
            "MRT_isCorrect ~ kappa_concentration * C(MRT_angle_degrees) + VWM_mean_absolute_error + MRT_RT_coefficient_variation + focus_loss_duration_trials_sec",
            groups="participantId",
            data=acc_data,
            family=sm.families.Binomial()
        )
        control_acc_model = model.fit()
        results['control_accuracy'] = {
            'model': control_acc_model,
            'nobs': len(acc_data)
        }
        print("Control accuracy model completed successfully")
    except Exception as e:
        print(f"Error in control accuracy model: {e}")
        results['control_accuracy'] = None

    # Control MRT RT Model (correct trials only, mixedlm)
    print("Running control MRT RT model...")

    correct_trials = trial_data_r[trial_data_r['MRT_isCorrect'] == True].copy()
    correct_trials['log_rt'] = np.log(correct_trials['MRT_rt_ms'])
    for col in ['log_rt', 'kappa_concentration', 'VWM_mean_absolute_error', 'MRT_RT_coefficient_variation', 'focus_loss_duration_trials_sec']:
        correct_trials[col] = pd.to_numeric(correct_trials[col], errors='coerce')
    rt_cols = ['log_rt', 'kappa_concentration', 'MRT_angle_degrees', 'participantId',
               'VWM_mean_absolute_error', 'MRT_RT_coefficient_variation', 'focus_loss_duration_trials_sec']
    rt_data = correct_trials[rt_cols].replace([np.inf, -np.inf], np.nan).dropna()

    try:
        control_rt_model = smf.mixedlm(
            "log_rt ~ kappa_concentration * C(MRT_angle_degrees) + VWM_mean_absolute_error + MRT_RT_coefficient_variation + focus_loss_duration_trials_sec",
            data=rt_data,
            groups=rt_data["participantId"]
        ).fit()
        results['control_rt'] = {
            'model': control_rt_model,
            'nobs': len(rt_data)
        }
        print("Control RT model completed successfully")
    except Exception as e:
        print(f"Error in control RT model: {e}")
        results['control_rt'] = None

    # Control VVIQ regressions (robust linear model)
    print("Running control VVIQ regressions...")

    vviq_outcomes = ['total_score', 'familiar_person_score', 'sunrise_score', 'shop_front_score',
                     'countryside_score', 'driving_score', 'beach_score', 'railway_station_score', 'garden_score']

    vviq_results = {}

    for outcome in vviq_outcomes:
        print(f"Running control regression for {outcome}...")

        vviq_cols = [outcome, 'kappa_concentration', 'VWM_mean_absolute_error',
                     'MRT_RT_coefficient_variation', 'focus_loss_duration_trials_sec']
        model_data = participant_data[vviq_cols].copy()
        for col in vviq_cols:
            model_data[col] = pd.to_numeric(model_data[col], errors='coerce')
        model_data = model_data.replace([np.inf, -np.inf], np.nan).dropna()
        for col in model_data.select_dtypes(include=[np.number]).columns:
            model_data[col] = model_data[col].astype(float)

        if len(model_data) < 10:
            print(f"Insufficient data for {outcome}: {len(model_data)} observations")
            vviq_results[outcome] = None
            continue

        try:
            model = smf.rlm(
                f"{outcome} ~ kappa_concentration + VWM_mean_absolute_error + MRT_RT_coefficient_variation + focus_loss_duration_trials_sec",
                data=model_data,
                M=sm.robust.norms.HuberT()
            )
            result = model.fit()
            vviq_results[outcome] = {
                'model': result,
                'nobs': len(model_data)
            }
            print(f"Control {outcome} regression completed successfully (n={len(model_data)})")
        except Exception as e:
            print(f"Error in control {outcome} regression: {e}")
            vviq_results[outcome] = None

    results['control_vviq'] = vviq_results

    return results

def extract_effect_info(model_result, effect_name):
    """
    Extract coefficient information from statsmodels output.
    """
    if model_result is None or not hasattr(model_result, 'params'):
        return None

    if effect_name in model_result.params.index:
        return {
            'estimate': float(model_result.params[effect_name]),
            'se': float(model_result.bse[effect_name]),
            'statistic': float(model_result.tvalues[effect_name]),
            'p_value': float(model_result.pvalues[effect_name])
        }
    return None


def compare_model_results(original_results, control_results, participant_data):
    """
    Compare original and control model results.

    Parameters:
    original_results (dict): Original model results
    control_results (dict): Control model results
    participant_data (DataFrame): Participant-level data

    Returns:
    tuple: (mrt_comparison, vviq_comparison) DataFrames
    """
    print("\nComparing model results...")

    # MRT model comparisons
    mrt_comparisons = []

    # Accuracy model
    orig_acc = original_results.get('original_accuracy')
    ctrl_acc = control_results.get('control_accuracy')
    if orig_acc and ctrl_acc:
        print("Comparing accuracy models...")

        orig_model = orig_acc.get('model')
        ctrl_model = ctrl_acc.get('model')

        orig_kappa = extract_effect_info(orig_model, 'kappa_concentration')
        ctrl_kappa = extract_effect_info(ctrl_model, 'kappa_concentration')

        if orig_kappa and ctrl_kappa:
            orig_ci = orig_model.conf_int().loc['kappa_concentration']
            ctrl_ci = ctrl_model.conf_int().loc['kappa_concentration']
            if abs(orig_kappa['estimate']) > 1e-10:
                effect_change = ((ctrl_kappa['estimate'] - orig_kappa['estimate']) / abs(orig_kappa['estimate'])) * 100
            else:
                effect_change = 0.0

            mrt_comparisons.append({
                'model_name': 'MRT_Accuracy',
                'effect_name': 'kappa_concentration',
                'original_estimate': orig_kappa['estimate'],
                'control_estimate': ctrl_kappa['estimate'],
                'original_p_value': orig_kappa['p_value'],
                'control_p_value': ctrl_kappa['p_value'],
                'original_ci_lower': orig_ci[0],
                'original_ci_upper': orig_ci[1],
                'control_ci_lower': ctrl_ci[0],
                'control_ci_upper': ctrl_ci[1],
                'effect_size_change_percent': effect_change
            })

    # RT model
    orig_rt = original_results.get('original_rt')
    ctrl_rt = control_results.get('control_rt')
    if orig_rt and ctrl_rt:
        print("Comparing RT models...")

        orig_model = orig_rt.get('model')
        ctrl_model = ctrl_rt.get('model')

        orig_kappa = extract_effect_info(orig_model, 'kappa_concentration')
        ctrl_kappa = extract_effect_info(ctrl_model, 'kappa_concentration')

        if orig_kappa and ctrl_kappa:
            orig_ci = orig_model.conf_int().loc['kappa_concentration']
            ctrl_ci = ctrl_model.conf_int().loc['kappa_concentration']
            if abs(orig_kappa['estimate']) > 1e-10:
                effect_change = ((ctrl_kappa['estimate'] - orig_kappa['estimate']) / abs(orig_kappa['estimate'])) * 100
            else:
                effect_change = 0.0

            mrt_comparisons.append({
                'model_name': 'MRT_RT',
                'effect_name': 'kappa_concentration',
                'original_estimate': orig_kappa['estimate'],
                'control_estimate': ctrl_kappa['estimate'],
                'original_p_value': orig_kappa['p_value'],
                'control_p_value': ctrl_kappa['p_value'],
                'original_ci_lower': orig_ci[0],
                'original_ci_upper': orig_ci[1],
                'control_ci_lower': ctrl_ci[0],
                'control_ci_upper': ctrl_ci[1],
                'effect_size_change_percent': effect_change
            })

    mrt_df = pd.DataFrame(mrt_comparisons)

    # VVIQ model comparisons
    vviq_comparisons = []

    if original_results.get('original_vviq') and control_results.get('control_vviq'):
        print("Comparing VVIQ models...")

        vviq_outcomes = ['total_score', 'familiar_person_score', 'sunrise_score', 'shop_front_score',
                         'countryside_score', 'driving_score', 'beach_score', 'railway_station_score', 'garden_score']

        # Collect kappa p-values for FDR correction
        orig_kappa_pvals = []
        ctrl_kappa_pvals = []

        for outcome in vviq_outcomes:
            orig_model = original_results['original_vviq'].get(outcome)
            ctrl_model = control_results['control_vviq'].get(outcome)

            orig_kappa = extract_effect_info(orig_model['model'], 'kappa_concentration') if orig_model is not None else None
            ctrl_kappa = extract_effect_info(ctrl_model['model'], 'kappa_concentration') if ctrl_model is not None else None

            orig_kappa_pvals.append(orig_kappa['p_value'] if orig_kappa else None)
            ctrl_kappa_pvals.append(ctrl_kappa['p_value'] if ctrl_kappa else None)

        # Apply FDR correction using scipy.stats.fdrcorrection (Benjamini-Hochberg)
        orig_pvals_array = np.array([p if p is not None else 1.0 for p in orig_kappa_pvals])
        if len(orig_pvals_array) > 0:
            _, orig_fdr = fdrcorrection(orig_pvals_array, alpha=0.05, method='indep')
            orig_fdr = orig_fdr.tolist()
        else:
            orig_fdr = [None] * len(orig_kappa_pvals)

        ctrl_pvals_array = np.array([p if p is not None else 1.0 for p in ctrl_kappa_pvals])
        if len(ctrl_pvals_array) > 0:
            _, ctrl_fdr = fdrcorrection(ctrl_pvals_array, alpha=0.05, method='indep')
            ctrl_fdr = ctrl_fdr.tolist()
        else:
            ctrl_fdr = [None] * len(ctrl_kappa_pvals)

        # Create comparison rows
        for i, outcome in enumerate(vviq_outcomes):
            orig_model = original_results['original_vviq'].get(outcome)
            ctrl_model = control_results['control_vviq'].get(outcome)

            orig_kappa = extract_effect_info(orig_model['model'], 'kappa_concentration') if orig_model is not None else None
            ctrl_kappa = extract_effect_info(ctrl_model['model'], 'kappa_concentration') if ctrl_model is not None else None

            if orig_kappa and ctrl_kappa:
                # Calculate pseudo-R-squared for robust regression using original data
                try:
                    # Original model R-squared - ensure we have valid fitted values
                    if hasattr(orig_model['model'], 'fittedvalues') and hasattr(orig_model['model'], 'model'):
                        fitted_orig = orig_model['model'].fittedvalues
                        observed_vals_orig = orig_model['model'].model.endog
                        if len(fitted_orig) > 0 and len(observed_vals_orig) > 0:
                            corr_matrix = np.corrcoef(fitted_orig, observed_vals_orig)
                            if not np.isnan(corr_matrix[0, 1]):
                                orig_r_squared = float(corr_matrix[0, 1]) ** 2
                            else:
                                orig_r_squared = 0.0
                        else:
                            orig_r_squared = 0.0
                    else:
                        orig_r_squared = 0.0

                    # Control model R-squared
                    if hasattr(ctrl_model['model'], 'fittedvalues') and hasattr(ctrl_model['model'], 'model'):
                        fitted_ctrl = ctrl_model['model'].fittedvalues
                        observed_vals_ctrl = ctrl_model['model'].model.endog
                        if len(fitted_ctrl) > 0 and len(observed_vals_ctrl) > 0:
                            corr_matrix = np.corrcoef(fitted_ctrl, observed_vals_ctrl)
                            if not np.isnan(corr_matrix[0, 1]):
                                ctrl_r_squared = float(corr_matrix[0, 1]) ** 2
                            else:
                                ctrl_r_squared = 0.0
                        else:
                            ctrl_r_squared = 0.0
                    else:
                        ctrl_r_squared = 0.0
                except Exception as e:
                    print(f"Error calculating R-squared for {outcome}: {e}")
                    orig_r_squared = 0.0
                    ctrl_r_squared = 0.0

                if abs(orig_kappa['estimate']) > 1e-10:
                    effect_change = ((ctrl_kappa['estimate'] - orig_kappa['estimate']) / abs(orig_kappa['estimate'])) * 100
                else:
                    effect_change = 0.0

                vviq_comparisons.append({
                    'outcome_variable': outcome,
                    'original_kappa_estimate': orig_kappa['estimate'],
                    'control_kappa_estimate': ctrl_kappa['estimate'],
                    'original_kappa_p_value': orig_kappa['p_value'],
                    'control_kappa_p_value': ctrl_kappa['p_value'],
                    'original_kappa_p_fdr': orig_fdr[i],
                    'control_kappa_p_fdr': ctrl_fdr[i],
                    'original_R_squared': orig_r_squared,
                    'control_R_squared': ctrl_r_squared,
                    'effect_size_change_percent': effect_change
                })

    vviq_df = pd.DataFrame(vviq_comparisons)

    return mrt_df, vviq_df

def save_results(mrt_comparison, vviq_comparison):
    """
    Save comparison results to CSV files.
    
    Parameters:
    mrt_comparison (DataFrame): MRT model comparison results
    vviq_comparison (DataFrame): VVIQ model comparison results
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save MRT results
    mrt_filename = f"outputs/control_analysis_MRT_results_{timestamp}.csv"
    mrt_comparison.to_csv(mrt_filename, index=False)
    print(f"MRT results saved to: {mrt_filename}")
    print(f"MRT results shape: {mrt_comparison.shape}")
    print("MRT results preview:")
    print(mrt_comparison.head(2))
    
    # Save VVIQ results
    vviq_filename = f"outputs/control_analysis_VVIQ2_results_{timestamp}.csv"
    vviq_comparison.to_csv(vviq_filename, index=False)
    print(f"VVIQ results saved to: {vviq_filename}")
    print(f"VVIQ results shape: {vviq_comparison.shape}")
    print("VVIQ results preview:")
    print(vviq_comparison.head(2))

def main():
    """Main execution function."""
    try:
        print("Starting control analysis...")
        
        # Load input files
        mrt_data, mixture_data, vviq_data, cognitive_data = load_input_files()
        if mrt_data is None:
            return 1
        
        # Prepare merged dataset
        participant_data, trial_data = prepare_merged_dataset(mrt_data, mixture_data, vviq_data, cognitive_data)
        if participant_data is None:
            return 1
        
        # Run original models
        original_results = run_original_models(trial_data, participant_data)
        
        # Run control models
        control_results = run_control_models(trial_data, participant_data)
        
        # Compare results
        mrt_comparison, vviq_comparison = compare_model_results(original_results, control_results, participant_data)
        
        # Save results
        save_results(mrt_comparison, vviq_comparison)
        
        print("\nControl analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
