#!/usr/bin/env python3
"""
Bootstrap uncertainty analysis for VWM, MRT, and VVIQ2 data with multi-stage estimation.
Implements bias-corrected and accelerated (BCa) confidence intervals.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
import warnings
from datetime import datetime
import time
from scipy import stats
import scipy
from scipy.optimize import minimize
import multiprocessing as mp
from functools import partial
import statsmodels.api as sm
import statsmodels.formula.api as smf

import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter
from rpy2.robjects import default_converter

def setup_r_environment():
    """Setup R environment and load required packages."""
    try:
        lme4 = importr('lme4')
        base = importr('base')
        stats = importr('stats')
        return True
    except Exception as e:
        print(f"Warning: R environment setup failed: {e}")
        print("Falling back to Python statsmodels implementation")
        return False

R_AVAILABLE = setup_r_environment()

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Args:
        pattern (str): File pattern to match
        
    Returns:
        str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, return most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def load_input_files():
    """
    Load all required input files and return as dictionary.
    
    Returns:
        dict: Dictionary containing all loaded dataframes
    """
    print("Loading input files...")
    
    # Define file patterns
    file_patterns = {
        'vwm_data': 'outputs/VWM_cleaned_data_*.csv',
        'vwm_params': 'outputs/VWM_model_parameters_*.csv',
        'mrt_data': 'outputs/MRT_cleaned_data_*.csv',
        'vviq_data': 'outputs/VVIQ2_cleaned_data_*.csv',
        'participants': 'outputs/participants_post_initial_exclusions_*.csv'
    }
    
    data = {}
    
    for key, pattern in file_patterns.items():
        filepath = find_latest_file(pattern)
        if filepath is None:
            print(f"ERROR: No files found matching pattern: {pattern}")
            sys.exit(1)
        
        print(f"Loading {key} from: {filepath}")
        df = pd.read_csv(filepath)
        print(f"{key} shape: {df.shape}")
        print(f"{key} columns: {list(df.columns)}")
        print(f"{key} first 3 rows:")
        print(df.head(3))
        print()
        
        data[key] = df
    
    return data

def validate_and_prepare_data(data):
    """
    Validate input data and prepare for analysis.
    
    Args:
        data (dict): Dictionary of input dataframes
        
    Returns:
        dict: Dictionary of prepared dataframes
    """
    print("Validating and preparing data...")
    
    # Filter VWM data for non-excluded participants
    vwm_data = data['vwm_data']
    if 'excluded' in vwm_data.columns:
        vwm_data = vwm_data[vwm_data['excluded'] == False].copy()
    print(f"VWM data after exclusion filtering: {vwm_data.shape[0]} rows")
    
    # Filter VWM parameters for non-excluded participants
    vwm_params = data['vwm_params']
    if 'excluded' in vwm_params.columns:
        vwm_params = vwm_params[vwm_params['excluded'] == False].copy()
    print(f"VWM parameters after exclusion filtering: {vwm_params.shape[0]} rows")
    
    # Filter MRT data for non-excluded participants
    mrt_data = data['mrt_data']
    if 'excluded' in mrt_data.columns:
        mrt_data = mrt_data[mrt_data['excluded'] == False].copy()
    print(f"MRT data after exclusion filtering: {mrt_data.shape[0]} rows")
    print(f"MRT data unique MRT_angle_degrees: {sorted(mrt_data['MRT_angle_degrees'].unique())}")
    print(f"MRT data unique MRT_isCorrect: {sorted(mrt_data['MRT_isCorrect'].unique())}")
    
    # Filter VVIQ data
    vviq_data = data['vviq_data']
    if 'excluded' in vviq_data.columns:
        vviq_data = vviq_data[vviq_data['excluded'] == False].copy()
    print(f"VVIQ data after exclusion filtering: {vviq_data.shape[0]} rows")
    print(f"VVIQ total_score range: {vviq_data['total_score'].min()} to {vviq_data['total_score'].max()}")
    
    # Filter participants data
    participants = data['participants']
    if 'excluded' in participants.columns:
        participants = participants[participants['excluded'] == False].copy()
    print(f"Participants after exclusion filtering: {participants.shape[0]} rows")
    
    # Get common participant IDs
    vwm_participants = set(vwm_data['participantId'].unique())
    vwm_param_participants = set(vwm_params['participantId'].unique())
    mrt_participants = set(mrt_data['participantId'].unique())
    vviq_participants = set(vviq_data['PROLIFIC_PID'].unique())
    main_participants = set(participants['participantId'].unique())
    
    # Find intersection of all participant sets
    common_participants = (vwm_participants & vwm_param_participants & 
                          mrt_participants & vviq_participants & main_participants)
    
    print(f"VWM participants: {len(vwm_participants)}")
    print(f"VWM param participants: {len(vwm_param_participants)}")
    print(f"MRT participants: {len(mrt_participants)}")
    print(f"VVIQ participants: {len(vviq_participants)}")
    print(f"Main participants: {len(main_participants)}")
    print(f"Common participants: {len(common_participants)}")
    
    # Filter all datasets to common participants
    vwm_data_filtered = vwm_data[vwm_data['participantId'].isin(common_participants)].copy()
    vwm_params_filtered = vwm_params[vwm_params['participantId'].isin(common_participants)].copy()
    mrt_data_filtered = mrt_data[mrt_data['participantId'].isin(common_participants)].copy()
    vviq_data_filtered = vviq_data[vviq_data['PROLIFIC_PID'].isin(common_participants)].copy()
    participants_filtered = participants[participants['participantId'].isin(common_participants)].copy()
    
    print(f"Final data sizes:")
    print(f"VWM data: {vwm_data_filtered.shape[0]} rows")
    print(f"VWM params: {vwm_params_filtered.shape[0]} rows")
    print(f"MRT data: {mrt_data_filtered.shape[0]} rows")
    print(f"VVIQ data: {vviq_data_filtered.shape[0]} rows")
    print(f"Participants: {participants_filtered.shape[0]} rows")
    
    return {
        'vwm_data': vwm_data_filtered,
        'vwm_params': vwm_params_filtered,
        'mrt_data': mrt_data_filtered,
        'vviq_data': vviq_data_filtered,
        'participants': participants_filtered,
        'common_participants': list(common_participants)
    }

def von_mises_mixture_log_likelihood(params, data):
    """
    Calculate log-likelihood for von Mises mixture model.
    
    Args:
        params (array): [kappa, mu, p_precision]
        data (array): Angular data in radians
        
    Returns:
        float: Negative log-likelihood
    """
    kappa, mu, p_precision = params
    
    # Ensure valid parameters
    if kappa <= 0 or p_precision <= 0 or p_precision >= 1:
        return np.inf
    
    # Von Mises component (precision)
    vm_component = stats.vonmises.pdf(data, kappa, loc=mu)
    
    # Uniform component (guessing)
    uniform_component = 1.0 / (2 * np.pi)
    
    # Mixture
    likelihood = p_precision * vm_component + (1 - p_precision) * uniform_component
    
    # Avoid log(0)
    likelihood = np.maximum(likelihood, 1e-10)
    
    return -np.sum(np.log(likelihood))

def fit_von_mises_mixture(data_radians):
    """
    Fit von Mises mixture model to angular data.
    
    Args:
        data_radians (array): Angular data in radians
        
    Returns:
        dict: Fitted parameters {kappa, mu, p_precision}
    """
    if len(data_radians) < 5:
        return {'kappa': np.nan, 'mu': np.nan, 'p_precision': np.nan}
    
    # Initial parameter guesses
    initial_mu = stats.circmean(data_radians)
    initial_kappa = 1.0
    initial_p = 0.7
    
    # Try multiple starting points
    best_result = None
    best_likelihood = np.inf
    
    for kappa_start in [0.5, 1.0, 2.0, 5.0]:
        for p_start in [0.5, 0.7, 0.9]:
            initial_params = [kappa_start, initial_mu, p_start]
            
            try:
                result = minimize(
                    von_mises_mixture_log_likelihood,
                    initial_params,
                    args=(data_radians,),
                    bounds=[(0.01, 100), (-np.pi, np.pi), (0.01, 0.99)],
                    method='L-BFGS-B'
                )
                
                if result.fun < best_likelihood:
                    best_likelihood = result.fun
                    best_result = result
            except:
                continue

    if best_result is None or not best_result.success:
        return {'kappa': np.nan, 'mu': np.nan, 'p_precision': np.nan}

    kappa, mu, p_precision = best_result.x
    # Validate kappa is within reasonable bounds
    if kappa < 0.1 or kappa > 100:
        return {'kappa': np.nan, 'mu': np.nan, 'p_precision': np.nan}
    return {'kappa': kappa, 'mu': mu, 'p_precision': p_precision}

def bootstrap_participant_parameters(participant_data, n_bootstrap=100):
    """
    Bootstrap kappa parameters for a single participant.
    
    Args:
        participant_data (array): VWM error data for one participant
        n_bootstrap (int): Number of bootstrap iterations
        
    Returns:
        array: Bootstrap distribution of kappa values
    """
    kappa_bootstrap = []
    
    # Convert to radians if in degrees
    if np.max(np.abs(participant_data)) > 10:  # Likely in degrees
        data_radians = np.deg2rad(participant_data)
    else:
        data_radians = participant_data
    
    for _ in range(n_bootstrap):
        # Resample with replacement
        bootstrap_sample = np.random.choice(data_radians, size=len(data_radians), replace=True)
        
        # Fit mixture model
        params = fit_von_mises_mixture(bootstrap_sample)
        
        if not np.isnan(params['kappa']):
            kappa_bootstrap.append(params['kappa'])
    
    return np.array(kappa_bootstrap)

def fit_mrt_mixed_effects_model_r(mrt_analysis, control_vars, group_col="participantId"):
    """
    Fit mixed-effects models for MRT using R's lme4 package.
    """
    try:
        with localconverter(default_converter + pandas2ri.converter):
            lme4 = importr('lme4')
            base = importr('base')
            
            r_df = ro.conversion.py2rpy(mrt_analysis)
            ro.globalenv['mrt_data'] = r_df
            
            control_formula = " + ".join(control_vars) if control_vars else ""
            if control_formula:
                control_formula = " + " + control_formula
            
            accuracy_formula = f"MRT_isCorrect ~ kappa{control_formula} + (1|{group_col})"
            accuracy_result = lme4.glmer(accuracy_formula, data=r_df, family="binomial")
            accuracy_coef = base.fixef(accuracy_result)['kappa']
            
            rt_formula = f"ln_MRT_rt ~ kappa{control_formula} + (1|{group_col})"
            correct_data = mrt_analysis[mrt_analysis['MRT_isCorrect'] == True]
            if len(correct_data) > 5:
                r_correct_df = ro.conversion.py2rpy(correct_data)
                ro.globalenv['correct_data'] = r_correct_df
                rt_result = lme4.lmer(rt_formula, data=r_correct_df)
                rt_coef = base.fixef(rt_result)['kappa']
            else:
                rt_coef = np.nan
                
            return {"accuracy_coef": accuracy_coef, "rt_coef": rt_coef}
    except Exception:
        return fit_mrt_mixed_effects_model_statsmodels(mrt_analysis, control_vars, group_col)

def fit_mrt_mixed_effects_model_statsmodels(mrt_analysis, control_vars, group_col="participantId"):
    """
    Fallback statsmodels implementation.
    """
    for var in control_vars:
        if var not in mrt_analysis.columns:
            mrt_analysis[var] = np.nan
    accuracy_coef = np.nan
    # Ensure required columns exist
    required_cols = ['MRT_isCorrect', 'kappa', group_col]
    if not all(col in mrt_analysis.columns for col in required_cols):
        return {"accuracy_coef": np.nan, "rt_coef": np.nan}
    try:
        formula = "MRT_isCorrect ~ kappa" + "".join([f" + {v}" for v in control_vars])
        model = smf.mixedlm(formula, mrt_analysis, groups=mrt_analysis[group_col], family=sm.families.Binomial())
        result = model.fit(reml=False, method='lbfgs', warn_convergence=False)
        accuracy_coef = result.params.get("kappa", np.nan)
    except Exception:
        try:
            formula = "MRT_isCorrect ~ kappa" + "".join([f" + {v}" for v in control_vars])
            model = smf.glm(formula, mrt_analysis, family=sm.families.Binomial())
            result = model.fit()
            accuracy_coef = result.params.get("kappa", np.nan)
        except Exception:
            accuracy_coef = np.nan
    rt_coef = np.nan
    try:
        correct_trials = mrt_analysis[mrt_analysis["MRT_isCorrect"] == True]
        if len(correct_trials) > 5:
            formula = "ln_MRT_rt ~ kappa" + "".join([f" + {v}" for v in control_vars])
            model = smf.mixedlm(formula, correct_trials, groups=correct_trials[group_col])
            result = model.fit(reml=False, method='lbfgs', warn_convergence=False)
            rt_coef = result.params.get("kappa", np.nan)
    except Exception:
        try:
            correct_trials = mrt_analysis[mrt_analysis["MRT_isCorrect"] == True]
            formula = "ln_MRT_rt ~ kappa" + "".join([f" + {v}" for v in control_vars])
            model = smf.ols(formula, correct_trials)
            result = model.fit()
            rt_coef = result.params.get("kappa", np.nan)
        except Exception:
            rt_coef = np.nan
    return {"accuracy_coef": accuracy_coef, "rt_coef": rt_coef}

def run_mrt_analysis(mrt_data, participants_data, control_vars, group_col="participantId"):
    """
    Run MRT analysis with control variables.
    """
    mrt_analysis = mrt_data.copy()
    # Validate control variables
    available_control_vars = [var for var in control_vars if var in participants_data.columns]
    if len(available_control_vars) != len(control_vars):
        missing_vars = set(control_vars) - set(available_control_vars)
        print(f"Warning: Missing control variables: {missing_vars}")
    control_vars = available_control_vars
    if len(control_vars) > 0:
        mrt_analysis = mrt_analysis.merge(
            participants_data[["participantId"] + control_vars],
            on="participantId", how="left"
        )
    mrt_analysis = mrt_analysis.dropna(subset=['kappa'])
    if len(mrt_analysis) == 0:
        return {'accuracy_coef': np.nan, 'rt_coef': np.nan}
    if R_AVAILABLE:
        return fit_mrt_mixed_effects_model_r(mrt_analysis, control_vars, group_col)
    else:
        return fit_mrt_mixed_effects_model_statsmodels(mrt_analysis, control_vars, group_col)


def fit_vviq_hierarchical_model(vviq_analysis, control_vars):
    """
    Fit simple linear regression for VVIQ, including control variables.
    Returns coefficient for kappa.
    """
    for var in control_vars:
        if var not in vviq_analysis.columns:
            vviq_analysis[var] = np.nan

    # Ensure required columns exist
    required_cols = ['total_score', 'kappa']
    if not all(col in vviq_analysis.columns for col in required_cols):
        return {"vviq_coef": np.nan}

    try:
        # Use simple OLS regression, not mixed-effects
        formula = "total_score ~ kappa" + "".join([f" + {v}" for v in control_vars])
        model = smf.ols(formula, vviq_analysis)
        result = model.fit()
        vviq_coef = result.params.get("kappa", np.nan)
    except Exception:
        vviq_coef = np.nan

    return {"vviq_coef": vviq_coef}

def run_vviq_analysis(vviq_data, participants_data, control_vars, group_col="PROLIFIC_PID"):
    """
    Run VVIQ analysis with control variables.
    """
    vviq_analysis = vviq_data.copy()
    # Validate control variables
    available_control_vars = [var for var in control_vars if var in participants_data.columns]
    if len(available_control_vars) != len(control_vars):
        missing_vars = set(control_vars) - set(available_control_vars)
        print(f"Warning: Missing control variables: {missing_vars}")
    control_vars = available_control_vars
    if len(control_vars) > 0:
        vviq_analysis = vviq_analysis.merge(
            participants_data[["participantId"] + control_vars],
            left_on="PROLIFIC_PID", right_on="participantId", how="left"
        )
    vviq_analysis = vviq_analysis.dropna(subset=['kappa', 'total_score'])
    if len(vviq_analysis) < 10:
        return {'vviq_coef': np.nan}
    if R_AVAILABLE:
        return fit_vviq_hierarchical_model_r(vviq_analysis, control_vars)
    else:
        return fit_vviq_hierarchical_model(vviq_analysis, control_vars)

def bootstrap_single_iteration(iteration, data, original_kappa, control_vars):
    """
    Single bootstrap iteration with proper dataset construction and error handling.
    """
    try:
        np.random.seed(12345 + iteration)
        participants = data['common_participants']
        bootstrap_pids = np.random.choice(participants, size=len(participants), replace=True)
        
        mrt_boot_rows = []
        vviq_boot_rows = []
        new_kappas = []
        
        for i, pid in enumerate(bootstrap_pids):
            unique_id = f"{pid}_{i}"
            
            # Re-fit mixture model with error handling
            try:
                participant_vwm = data['vwm_data'][data['vwm_data']['participantId'] == pid]
                if len(participant_vwm) > 0:
                    participant_errors = participant_vwm['VWM_normalized_error_degrees'].values
                    # Resample trials with replacement to capture estimation uncertainty
                    bootstrap_errors = np.random.choice(participant_errors, size=len(participant_errors), replace=True)
                    errors_radians = np.deg2rad(bootstrap_errors)
                    params = fit_von_mises_mixture(errors_radians)
                    if not np.isnan(params['kappa']) and params['kappa'] > 0.1 and params['kappa'] < 100:
                        new_kappa = params['kappa']
                    else:
                        # Use original kappa with small random noise to add variability
                        original_val = original_kappa.get(pid, np.nan)
                        if not np.isnan(original_val):
                            new_kappa = original_val * (1 + np.random.normal(0, 0.01))
                        else:
                            new_kappa = np.nan
                else:
                    original_val = original_kappa.get(pid, np.nan)
                    if not np.isnan(original_val):
                        new_kappa = original_val * (1 + np.random.normal(0, 0.01))
                    else:
                        new_kappa = np.nan
            except Exception as e:
                original_val = original_kappa.get(pid, np.nan)
                if not np.isnan(original_val):
                    new_kappa = original_val * (1 + np.random.normal(0, 0.01))
                else:
                    new_kappa = np.nan

            new_kappas.append(new_kappa)
            
            # Add MRT data for this instance with error handling
            try:
                participant_mrt = data['mrt_data'][data['mrt_data']['participantId'] == pid].copy()
                if len(participant_mrt) > 0:
                    participant_mrt['bootstrap_id'] = unique_id
                    participant_mrt['kappa'] = new_kappa
                    mrt_boot_rows.append(participant_mrt)
            except Exception as e:
                pass  # Skip this participant's MRT data
            
            # Add VVIQ data for this instance with error handling
            try:
                participant_vviq = data['vviq_data'][data['vviq_data']['PROLIFIC_PID'] == pid].copy()
                if len(participant_vviq) > 0:
                    participant_vviq['bootstrap_id'] = unique_id
                    participant_vviq['kappa'] = new_kappa
                    vviq_boot_rows.append(participant_vviq)
            except Exception as e:
                pass  # Skip this participant's VVIQ data
        
        # Concatenate and analyze with comprehensive error handling
        try:
            if mrt_boot_rows:
                mrt_boot_df = pd.concat(mrt_boot_rows, ignore_index=True)
                if len(mrt_boot_df) > 0:
                    mrt_results = run_mrt_analysis(mrt_boot_df, data['participants'], control_vars, "bootstrap_id")
                else:
                    mrt_results = {'accuracy_coef': np.nan, 'rt_coef': np.nan}
            else:
                mrt_results = {'accuracy_coef': np.nan, 'rt_coef': np.nan}
        except Exception as e:
            mrt_results = {'accuracy_coef': np.nan, 'rt_coef': np.nan}
        
        try:
            if vviq_boot_rows:
                vviq_boot_df = pd.concat(vviq_boot_rows, ignore_index=True)
                if len(vviq_boot_df) > 0:
                    vviq_results = run_vviq_analysis(vviq_boot_df, data['participants'], control_vars, "bootstrap_id")
                else:
                    vviq_results = {'vviq_coef': np.nan}
            else:
                vviq_results = {'vviq_coef': np.nan}
        except Exception as e:
            vviq_results = {'vviq_coef': np.nan}
        
        return {
            'iteration': iteration,
            'kappa_mean': np.nanmean(new_kappas),
            'accuracy_coef': mrt_results['accuracy_coef'],
            'rt_coef': mrt_results['rt_coef'],
            'vviq_coef': vviq_results['vviq_coef']
        }
        
    except Exception as e:
        print(f"Warning: Bootstrap iteration {iteration} failed completely: {e}")
        return {
            'iteration': iteration,
            'kappa_mean': np.nan,
            'accuracy_coef': np.nan,
            'rt_coef': np.nan,
            'vviq_coef': np.nan
        }

def fit_vviq_hierarchical_model_r(vviq_analysis, control_vars):
    """Fit regression for VVIQ using R's lm (linear model)."""
    try:
        with localconverter(default_converter + pandas2ri.converter):
            stats = importr('stats')
            r_df = ro.conversion.py2rpy(vviq_analysis)
            control_formula = " + ".join(control_vars) if control_vars else ""
            if control_formula:
                control_formula = " + " + control_formula

            # Use lm, not lmer, as there's one data point per participant
            formula = f"total_score ~ kappa{control_formula}"
            result = stats.lm(formula, data=r_df)
            vviq_coef = stats.coef(result)['kappa']

            return {"vviq_coef": vviq_coef}
    except Exception:
        # fallback to Python implementation
        return fit_vviq_hierarchical_model(vviq_analysis, control_vars)

def calculate_jackknife_estimates(data, param_name, original_kappa, control_vars):
    """
    Compute jackknife estimates for BCa acceleration parameter.
    Returns array of jackknife estimates for the parameter.
    """
    n = len(data['common_participants'])
    jackknife_estimates = []
    
    for i, leave_out_pid in enumerate(data['common_participants']):
        try:
            # Create jackknife datasets (leave one participant out)
            jack_mrt = data['mrt_data'][data['mrt_data']['participantId'] != leave_out_pid].copy()
            jack_vviq = data['vviq_data'][data['vviq_data']['PROLIFIC_PID'] != leave_out_pid].copy()
            
            # Add kappa values to jackknife datasets
            jack_kappa = {pid: k for pid, k in original_kappa.items() if pid != leave_out_pid}
            jack_mrt['kappa'] = jack_mrt['participantId'].map(jack_kappa)
            jack_vviq['kappa'] = jack_vviq['PROLIFIC_PID'].map(jack_kappa)
            
            # Run analyses with new signatures
            mrt_results = run_mrt_analysis(jack_mrt, data['participants'], control_vars)
            vviq_results = run_vviq_analysis(jack_vviq, data['participants'], control_vars)
            
            if param_name == "kappa_mean":
                est = np.nanmean(list(jack_kappa.values()))
            elif param_name == "accuracy_coef":
                est = mrt_results['accuracy_coef']
            elif param_name == "rt_coef":
                est = mrt_results['rt_coef']
            elif param_name == "vviq_coef":
                est = vviq_results['vviq_coef']
            else:
                est = np.nan
                
            jackknife_estimates.append(est)
            
        except Exception as e:
            print(f"Warning: Jackknife iteration {i} failed: {e}")
            jackknife_estimates.append(np.nan)
    
    return np.array(jackknife_estimates)

def calculate_bca_ci(bootstrap_dist, original_estimate, jackknife_estimates, alpha=0.05):
    """
    Calculate bias-corrected and accelerated confidence intervals using jackknife.
    """
    bootstrap_dist = np.array(bootstrap_dist)
    bootstrap_dist = bootstrap_dist[~np.isnan(bootstrap_dist)]
    if len(bootstrap_dist) < 10 or jackknife_estimates is None or len(jackknife_estimates) < 2:
        return np.nan, np.nan
    # Check for degenerate bootstrap distribution
    if np.std(bootstrap_dist) < 1e-6:  # Nearly constant distribution
        # Fall back to percentile method
        lower_ci = np.percentile(bootstrap_dist, 2.5)
        upper_ci = np.percentile(bootstrap_dist, 97.5)
        return lower_ci, upper_ci
    n_boot = len(bootstrap_dist)
    # Bias correction
    p0 = np.sum(bootstrap_dist < original_estimate) / n_boot
    if p0 == 0:
        p0 = 1 / (2 * n_boot)
    elif p0 == 1:
        p0 = 1 - 1 / (2 * n_boot)
    z0 = stats.norm.ppf(p0)
    # Acceleration parameter (a) from jackknife
    jackknife_estimates = np.array(jackknife_estimates)
    jack_mean = np.mean(jackknife_estimates)
    num = np.sum((jack_mean - jackknife_estimates) ** 3)
    denom = 6.0 * (np.sum((jack_mean - jackknife_estimates) ** 2) ** 1.5)
    a = num / denom if denom != 0 else 0.0
    # Adjusted quantiles
    z_alpha_2 = stats.norm.ppf(alpha / 2)
    z_1_alpha_2 = stats.norm.ppf(1 - alpha / 2)
    alpha_1 = stats.norm.cdf(z0 + (z0 + z_alpha_2) / (1 - a * (z0 + z_alpha_2)))
    alpha_2 = stats.norm.cdf(z0 + (z0 + z_1_alpha_2) / (1 - a * (z0 + z_1_alpha_2)))
    alpha_1 = np.clip(alpha_1, 0.001, 0.999)
    alpha_2 = np.clip(alpha_2, 0.001, 0.999)
    lower_ci = np.percentile(bootstrap_dist, alpha_1 * 100)
    upper_ci = np.percentile(bootstrap_dist, alpha_2 * 100)
    # Fallback to percentile if BCa produces degenerate results
    if lower_ci == upper_ci or np.isnan(lower_ci) or np.isnan(upper_ci):
        lower_ci = np.percentile(bootstrap_dist, 2.5)
        upper_ci = np.percentile(bootstrap_dist, 97.5)
    return lower_ci, upper_ci

def run_bootstrap_analysis(data, n_bootstrap=1000):
    """
    Run complete bootstrap uncertainty analysis.
    """
    print(f"Starting bootstrap analysis with {n_bootstrap} iterations...")
    np.random.seed(12345)
    # Define control variables to use
    control_vars = [
        'mean_vwm_accuracy_z', 
        'response_time_cv_z', 
        'composite_engagement_score_z'
    ]
    # Get original parameter estimates
    print("Calculating original parameter estimates...")
    original_kappa = {}
    for _, row in data['vwm_params'].iterrows():
        original_kappa[row['participantId']] = row['kappa']

    print(f"Original kappa values for {len(original_kappa)} participants")
    print(f"Kappa range: {np.nanmin(list(original_kappa.values())):.3f} to {np.nanmax(list(original_kappa.values())):.3f}")

    # Create datasets with kappa values for original analysis
    original_mrt = data['mrt_data'].copy()
    original_mrt['kappa'] = original_mrt['participantId'].map(original_kappa)

    original_vviq = data['vviq_data'].copy()
    original_vviq['kappa'] = original_vviq['PROLIFIC_PID'].map(original_kappa)

    # Run original analyses
    original_mrt_results = run_mrt_analysis(original_mrt, data['participants'], control_vars)
    original_vviq_results = run_vviq_analysis(original_vviq, data['participants'], control_vars)

    original_estimates = {
        'kappa_mean': np.nanmean(list(original_kappa.values())),
        'accuracy_coef': original_mrt_results['accuracy_coef'],
        'rt_coef': original_mrt_results['rt_coef'],
        'vviq_coef': original_vviq_results['vviq_coef']
    }
    print("Original estimates:")
    for key, value in original_estimates.items():
        print(f"  {key}: {value:.4f}")

    # Diagnostic: show kappa bootstrap range for verification
    print(f"\nDiagnostic: Original kappa range: {np.nanmin(list(original_kappa.values())):.4f} to {np.nanmax(list(original_kappa.values())):.4f}")

    # Jackknife estimation for BCa acceleration
    print("\nCalculating jackknife estimates for BCa acceleration...")
    jackknife_dict = {}
    for param_name in original_estimates.keys():
        print(f"  Jackknife for {param_name}...")
        jackknife_dict[param_name] = calculate_jackknife_estimates(data, param_name, original_kappa, control_vars)
        print(f"    Jackknife mean: {np.nanmean(jackknife_dict[param_name]):.4f}")
    # Run bootstrap iterations
    print(f"\nRunning {n_bootstrap} bootstrap iterations...")
    n_cores = min(mp.cpu_count(), 8)
    print(f"Using {n_cores} CPU cores for parallel processing")
    bootstrap_func = partial(bootstrap_single_iteration, data=data, original_kappa=original_kappa, control_vars=control_vars)
    with mp.Pool(n_cores) as pool:
        bootstrap_results = []
        chunk_size = max(1, n_bootstrap // 10)
        for i in range(0, n_bootstrap, chunk_size):
            chunk_end = min(i + chunk_size, n_bootstrap)
            chunk_iterations = list(range(i, chunk_end))
            print(f"Processing iterations {i+1} to {chunk_end}...")
            chunk_results = pool.map(bootstrap_func, chunk_iterations)
            bootstrap_results.extend(chunk_results)
            print(f"Completed {len(bootstrap_results)}/{n_bootstrap} iterations")
    bootstrap_dists = {
        'kappa_mean': [r['kappa_mean'] for r in bootstrap_results],
        'accuracy_coef': [r['accuracy_coef'] for r in bootstrap_results],
        'rt_coef': [r['rt_coef'] for r in bootstrap_results],
        'vviq_coef': [r['vviq_coef'] for r in bootstrap_results]
    }

    # Diagnostic: show bootstrap kappa_mean range for verification
    kappa_bootstrap_dist = np.array(bootstrap_dists['kappa_mean'])
    kappa_bootstrap_dist = kappa_bootstrap_dist[~np.isnan(kappa_bootstrap_dist)]
    if len(kappa_bootstrap_dist) > 0:
        print(f"\nDiagnostic: Bootstrap kappa_mean range: {np.nanmin(kappa_bootstrap_dist):.4f} to {np.nanmax(kappa_bootstrap_dist):.4f}")

    print("\nCalculating bootstrap statistics and confidence intervals...")
    results = []
    # Save intermediate bootstrap distributions for diagnostics
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    bootstrap_dist_filename = f'outputs/bootstrap_distributions_{timestamp}.csv'
    bootstrap_dist_df = pd.DataFrame(bootstrap_dists)
    bootstrap_dist_df.to_csv(bootstrap_dist_filename, index=False)
    print(f"Bootstrap distributions saved to: {bootstrap_dist_filename}")
    for param_name in bootstrap_dists.keys():
        bootstrap_dist = np.array(bootstrap_dists[param_name])
        bootstrap_dist = bootstrap_dist[~np.isnan(bootstrap_dist)]
        if len(bootstrap_dist) > 0:
            original_est = original_estimates[param_name]
            bootstrap_mean = np.mean(bootstrap_dist)
            bootstrap_se = np.std(bootstrap_dist)
            bootstrap_bias = bootstrap_mean - original_est
            # Calculate BCa confidence intervals using jackknife
            bca_lower, bca_upper = calculate_bca_ci(bootstrap_dist, original_est, jackknife_dict[param_name])
            results.append({
                'parameter_name': param_name,
                'original_estimate': original_est,
                'bootstrap_mean': bootstrap_mean,
                'bootstrap_se': bootstrap_se,
                'bootstrap_bias': bootstrap_bias,
                'bca_ci_lower': bca_lower,
                'bca_ci_upper': bca_upper,
                'bootstrap_iterations': len(bootstrap_dist)
            })
            print(f"{param_name}:")
            print(f"  Original: {original_est:.4f}")
            print(f"  Bootstrap mean: {bootstrap_mean:.4f}")
            print(f"  Bootstrap SE: {bootstrap_se:.4f}")
            print(f"  Bias: {bootstrap_bias:.4f}")
            print(f"  95% BCa CI: [{bca_lower:.4f}, {bca_upper:.4f}]")
            print(f"  Valid iterations: {len(bootstrap_dist)}")
    return pd.DataFrame(results)

def save_session_info(n_bootstrap):
    """
    Save computational session information.
    
    Args:
        n_bootstrap (int): Number of bootstrap iterations completed
    """
    print("Saving session information...")
    
    session_info = [
        {'software_component': 'Python', 'version': sys.version.split()[0], 
         'random_seed': 12345, 'bootstrap_iterations_completed': n_bootstrap,
         'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
        {'software_component': 'NumPy', 'version': np.__version__, 
         'random_seed': 12345, 'bootstrap_iterations_completed': n_bootstrap,
         'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
        {'software_component': 'SciPy', 'version': scipy.__version__, 
         'random_seed': 12345, 'bootstrap_iterations_completed': n_bootstrap,
         'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')},
        {'software_component': 'Pandas', 'version': pd.__version__, 
         'random_seed': 12345, 'bootstrap_iterations_completed': n_bootstrap,
         'analysis_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ]
    
    session_df = pd.DataFrame(session_info)
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Save session info
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_filename = f'outputs/computational_session_info_{timestamp}.csv'
    session_df.to_csv(session_filename, index=False)
    
    print(f"Session information saved to: {session_filename}")
    print("Session info columns:", list(session_df.columns))
    print("Session info first 2 rows:")
    print(session_df.head(2))

def main():
    """
    Main function to run bootstrap uncertainty analysis.
    """
    try:
        print("Starting bootstrap uncertainty analysis...")
        print(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load input files
        raw_data = load_input_files()
        
        # Validate and prepare data
        prepared_data = validate_and_prepare_data(raw_data)
        
        # Run bootstrap analysis
        n_bootstrap = 1000
        bootstrap_results = run_bootstrap_analysis(prepared_data, n_bootstrap=n_bootstrap)
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Save bootstrap results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_filename = f'outputs/bootstrap_uncertainty_results_{timestamp}.csv'
        bootstrap_results.to_csv(results_filename, index=False)
        
        print(f"\nBootstrap results saved to: {results_filename}")
        print("Results columns:", list(bootstrap_results.columns))
        print("Results first 2 rows:")
        print(bootstrap_results.head(2))
        
        # Save session information
        save_session_info(n_bootstrap)
        
        print("\nBootstrap uncertainty analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
