#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import glob
import sys
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import R interface
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri, numpy2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter

def install_r_packages():
    """Install required R packages if not already installed."""
    print("Checking and installing required R packages...")
    try:
        utils = importr('utils')
        base = importr('base')
        
        # Check and install packages
        packages = ['circular', 'lme4', 'broom.mixed']
        for pkg in packages:
            try:
                importr(pkg)
                print(f"Package {pkg} already installed")
            except:
                print(f"Installing R package: {pkg}")
                utils.install_packages(pkg, repos='https://cloud.r-project.org/')
                print(f"Successfully installed {pkg}")
    except Exception as e:
        print(f"Warning: Could not install R packages: {e}")
        print("Please ensure R packages are installed manually if needed")

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
    return max(files, key=os.path.getctime)

def load_and_validate_data():
    """
    Load and validate all required input files.
    
    Returns:
        tuple: (main_data, mixture_params, vviq_data) DataFrames or (None, None, None) if error
    """
    print("Loading input files...")
    
    # Find latest files
    main_pattern = "outputs/VWM_MRT_cleaned_data_*.csv"
    mixture_pattern = "outputs/VWM_mixture_model_parameters_*.csv"
    vviq_pattern = "outputs/VVIQ2_cleaned_scores_*.csv"
    
    main_file = find_latest_file(main_pattern)
    mixture_file = find_latest_file(mixture_pattern)
    vviq_file = find_latest_file(vviq_pattern)
    
    if not main_file:
        print(f"Error: No file found matching pattern {main_pattern}")
        return None, None, None
    if not mixture_file:
        print(f"Error: No file found matching pattern {mixture_pattern}")
        return None, None, None
    if not vviq_file:
        print(f"Error: No file found matching pattern {vviq_pattern}")
        return None, None, None
        
    print(f"Found main data file: {main_file}")
    print(f"Found mixture parameters file: {mixture_file}")
    print(f"Found VVIQ data file: {vviq_file}")
    
    # Load main data
    try:
        main_data = pd.read_csv(main_file)
        print(f"Main data shape: {main_data.shape}")
        print("Main data columns:", list(main_data.columns))
        print("First 3 rows of main data:")
        print(main_data.head(3))
        
        # Validate required columns
        required_main_cols = ['participantId', 'isPractice', 'VWM_error_degrees', 'VWM_block', 
                             'MRT_trial', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms',
                             'MRT_block', 'excluded_from_VWM', 'excluded_from_MRT', 'trial_excluded']
        missing_cols = [col for col in required_main_cols if col not in main_data.columns]
        if missing_cols:
            print(f"Error: Missing required columns in main data: {missing_cols}")
            return None, None, None
            
        # Print unique values for key columns
        print("Unique isPractice values:", main_data['isPractice'].unique())
        print("Unique VWM_block values:", main_data['VWM_block'].unique())
        print("Unique MRT_block values:", main_data['MRT_block'].unique())
        print("Unique excluded_from_VWM values:", main_data['excluded_from_VWM'].unique())
        print("Unique excluded_from_MRT values:", main_data['excluded_from_MRT'].unique())
        print("Unique trial_excluded values:", main_data['trial_excluded'].unique())
        print("VWM_error_degrees data type:", main_data['VWM_error_degrees'].dtype)
        print("MRT_rt_ms data type:", main_data['MRT_rt_ms'].dtype)
        
    except Exception as e:
        print(f"Error loading main data: {e}")
        return None, None, None
    
    # Load mixture parameters
    try:
        mixture_params = pd.read_csv(mixture_file)
        print(f"Mixture parameters shape: {mixture_params.shape}")
        print("Mixture parameters columns:", list(mixture_params.columns))
        print("First 3 rows of mixture parameters:")
        print(mixture_params.head(3))
        
        required_mixture_cols = ['participantId', 'kappa_concentration', 'guess_rate', 'model_converged']
        missing_cols = [col for col in required_mixture_cols if col not in mixture_params.columns]
        if missing_cols:
            print(f"Error: Missing required columns in mixture parameters: {missing_cols}")
            return None, None, None
            
        print("Unique model_converged values:", mixture_params['model_converged'].unique())
        print("kappa_concentration data type:", mixture_params['kappa_concentration'].dtype)
        print("guess_rate data type:", mixture_params['guess_rate'].dtype)
        
    except Exception as e:
        print(f"Error loading mixture parameters: {e}")
        return None, None, None
    
    # Load VVIQ data
    try:
        vviq_data = pd.read_csv(vviq_file)
        print(f"VVIQ data shape: {vviq_data.shape}")
        print("VVIQ data columns:", list(vviq_data.columns))
        print("First 3 rows of VVIQ data:")
        print(vviq_data.head(3))
        
        required_vviq_cols = ['PROLIFIC_PID', 'total_score', 'familiar_person_score', 'sunrise_score',
                             'shop_front_score', 'countryside_score', 'driving_score', 'beach_score',
                             'railway_station_score', 'garden_score', 'excluded']
        missing_cols = [col for col in required_vviq_cols if col not in vviq_data.columns]
        if missing_cols:
            print(f"Error: Missing required columns in VVIQ data: {missing_cols}")
            return None, None, None
            
        print("Unique excluded values:", vviq_data['excluded'].unique())
        print("total_score data type:", vviq_data['total_score'].dtype)
        
    except Exception as e:
        print(f"Error loading VVIQ data: {e}")
        return None, None, None
    
    return main_data, mixture_params, vviq_data

def classify_guess_trials(main_data, mixture_params):
    """
    Classify VWM trials as memory vs guess based on error magnitude and guess rate.
    
    Args:
        main_data (pd.DataFrame): Main experimental data
        mixture_params (pd.DataFrame): Mixture model parameters
        
    Returns:
        pd.DataFrame: Main data with added 'is_guess_trial' column
    """
    print("Classifying guess trials...")
    
    # Calculate threshold as 90th percentile of uniform distribution over ±90° range
    # For uniform distribution from -90 to 90, the 90th percentile is at 90% of the range
    uniform_90th_percentile = -90 + 0.9 * (90 - (-90))  # = 72 degrees
    print(f"Uniform distribution 90th percentile threshold: {uniform_90th_percentile} degrees")
    
    # Merge mixture parameters
    main_with_params = main_data.merge(mixture_params[['participantId', 'guess_rate']], 
                                      on='participantId', how='left')
    
    # Filter for valid VWM trials
    vwm_trials = main_with_params[
        (main_with_params['isPractice'] == False) &
        (main_with_params['VWM_block'] != 'practice') &
        (main_with_params['excluded_from_VWM'] == False) &
        (main_with_params['trial_excluded'] == False) &
        (main_with_params['VWM_error_degrees'].notna())
    ].copy()
    
    print(f"Valid VWM trials for guess classification: {len(vwm_trials)}")
    
    # Classify trials as guesses based on error magnitude
    # Use absolute error > threshold as likely guess trials
    vwm_trials['abs_error'] = np.abs(vwm_trials['VWM_error_degrees'])
    vwm_trials['is_guess_trial'] = vwm_trials['abs_error'] > uniform_90th_percentile

    print(f"Trials classified as guesses: {vwm_trials['is_guess_trial'].sum()}")
    print(f"Proportion of guess trials: {vwm_trials['is_guess_trial'].mean():.3f}")

    # Add guess classification back to main data
    main_data_with_guess = main_data.copy()
    main_data_with_guess['is_guess_trial'] = False  # Default to False

    # Vectorized assignment for guess classification
    main_data_with_guess.loc[vwm_trials.index, 'is_guess_trial'] = vwm_trials['is_guess_trial']

    return main_data_with_guess

def fit_alternative_distributions(main_data, mixture_params):
    """
    Fit wrapped normal and wrapped Cauchy distributions to VWM error data.
    
    Args:
        main_data (pd.DataFrame): Main experimental data
        mixture_params (pd.DataFrame): Existing mixture model parameters
        
    Returns:
        pd.DataFrame: Parameters for all three distributions
    """
    print("Fitting alternative circular distributions...")
    
    # Setup R environment
    r = robjects.r
    r('library(circular)')
    r('library(stats)')
    
    # Filter for valid VWM trials
    vwm_data = main_data[
        (main_data['isPractice'] == False) &
        (main_data['VWM_block'] != 'practice') &
        (main_data['excluded_from_VWM'] == False) &
        (main_data['trial_excluded'] == False) &
        (main_data['VWM_error_degrees'].notna())
    ].copy()
    
    print(f"Valid VWM trials for distribution fitting: {len(vwm_data)}")
    
    # Get unique participants
    participants = vwm_data['participantId'].unique()
    print(f"Number of participants for distribution fitting: {len(participants)}")
    
    results = []
    
    for i, participant in enumerate(participants):
        if i % 10 == 0:
            print(f"Processing participant {i+1}/{len(participants)}")
            
        # Get participant's VWM errors
        participant_data = vwm_data[vwm_data['participantId'] == participant]
        errors_degrees = participant_data['VWM_error_degrees'].values
        
        if len(errors_degrees) < 5:  # Need minimum trials for fitting
            continue

        # Convert to radians
        errors_radians = np.deg2rad(errors_degrees)

        # Get existing von Mises parameters
        vm_params = mixture_params[mixture_params['participantId'] == participant]
        if len(vm_params) == 0:
            continue

        von_mises_kappa = float(vm_params['kappa_concentration'].iloc[0])

        try:
            # Fit wrapped normal distribution
            r.assign('errors_rad', robjects.FloatVector(errors_radians))
            r('circular_errors <- circular(errors_rad)')

            # Wrapped normal fitting
            r('''
            wn_fit <- tryCatch({
                mle.wrappednormal(circular_errors)
            }, error = function(e) NULL)
            ''')

            wn_fit = r('wn_fit')
            if wn_fit != robjects.NULL:
                wn_mu = float(r('wn_fit$mu')[0])
                wn_rho = float(r('wn_fit$rho')[0])
                # Convert rho to concentration-like parameter
                wn_concentration = -2 * np.log(wn_rho) if wn_rho > 0 else 0

                # Calculate AIC for wrapped normal
                r('''
                wn_aic <- tryCatch({
                    ll <- sum(log(dwrappednormal(circular_errors, mu=wn_fit$mu, rho=wn_fit$rho)))
                    -2 * ll + 2 * 2  # 2 parameters
                }, error = function(e) NA)
                ''')
                wn_aic = float(r('wn_aic')[0])
            else:
                wn_concentration = np.nan
                wn_aic = np.nan

            # Fit wrapped Cauchy distribution
            r('''
            wc_fit <- tryCatch({
                mle.wrappedcauchy(circular_errors)
            }, error = function(e) NULL)
            ''')

            wc_fit = r('wc_fit')
            if wc_fit != robjects.NULL:
                wc_mu = float(r('wc_fit$mu')[0])
                wc_rho = float(r('wc_fit$rho')[0])
                # For wrapped Cauchy, rho is already a concentration parameter
                wc_concentration = wc_rho

                # Calculate AIC for wrapped Cauchy
                r('''
                wc_aic <- tryCatch({
                    ll <- sum(log(dwrappedcauchy(circular_errors, mu=wc_fit$mu, rho=wc_fit$rho)))
                    -2 * ll + 2 * 2  # 2 parameters
                }, error = function(e) NA)
                ''')
                wc_aic = float(r('wc_aic')[0])
            else:
                wc_concentration = np.nan
                wc_aic = np.nan

            # Fit single von Mises distribution to full dataset for fair AIC comparison
            r('''
            vm_single_fit <- tryCatch({
                mle.vonmises(circular_errors)
            }, error = function(e) NULL)
            ''')

            vm_single_fit = r('vm_single_fit')
            if vm_single_fit != robjects.NULL:
                # Calculate AIC using the single-distribution fit
                r('''
                vm_aic <- tryCatch({
                    ll <- sum(log(dvonmises(circular_errors, mu=vm_single_fit$mu, kappa=vm_single_fit$kappa)))
                    -2 * ll + 2 * 2  # 2 parameters
                }, error = function(e) NA)
                ''')
                vm_aic = float(r('vm_aic')[0])
            else:
                vm_aic = np.nan

            # Determine best fitting distribution
            aics = {'von_mises': vm_aic, 'wrapped_normal': wn_aic, 'wrapped_cauchy': wc_aic}
            valid_aics = {k: v for k, v in aics.items() if not np.isnan(v)}
            if valid_aics:
                best_dist = min(valid_aics, key=valid_aics.get)
            else:
                best_dist = 'von_mises'  # Default

            results.append({
                'participantId': participant,
                'von_mises_kappa': von_mises_kappa,
                'wrapped_normal_concentration': wn_concentration,
                'wrapped_cauchy_concentration': wc_concentration,
                'von_mises_AIC': vm_aic,
                'wrapped_normal_AIC': wn_aic,
                'wrapped_cauchy_AIC': wc_aic,
                'best_fitting_distribution': best_dist
            })

        except Exception as e:
            print(f"Error fitting distributions for participant {participant}: {e}")
            results.append({
                'participantId': participant,
                'von_mises_kappa': von_mises_kappa,
                'wrapped_normal_concentration': np.nan,
                'wrapped_cauchy_concentration': np.nan,
                'von_mises_AIC': np.nan,
                'wrapped_normal_AIC': np.nan,
                'wrapped_cauchy_AIC': np.nan,
                'best_fitting_distribution': 'von_mises'
            })
    
    alt_params_df = pd.DataFrame(results)
    print(f"Successfully fit distributions for {len(alt_params_df)} participants")
    
    # Print summary statistics
    print("Alternative distribution parameters summary:")
    print("Wrapped normal concentration - mean:", alt_params_df['wrapped_normal_concentration'].mean())
    print("Wrapped Cauchy concentration - mean:", alt_params_df['wrapped_cauchy_concentration'].mean())
    print("Best fitting distribution counts:")
    print(alt_params_df['best_fitting_distribution'].value_counts())
    
    return alt_params_df

def run_sensitivity_analyses(main_data, alt_params, vviq_data):
    """
    Run sensitivity analyses using alternative distribution parameters.
    
    Args:
        main_data (pd.DataFrame): Main experimental data
        alt_params (pd.DataFrame): Alternative distribution parameters
        vviq_data (pd.DataFrame): VVIQ data
        
    Returns:
        pd.DataFrame: Sensitivity analysis results
    """
    print("Running sensitivity analyses...")
    
    # Setup R environment for mixed effects models
    r = robjects.r
    r('library(lme4)')
    r('library(lmerTest)')
    r('library(broom.mixed)')
    
    results = []
    
    # Prepare data for MRT analyses
    mrt_data = main_data[
        (main_data['isPractice'] == False) &
        (main_data['MRT_block'] != 'practice') &
        (main_data['excluded_from_MRT'] == False) &
        (main_data['trial_excluded'] == False) &
        (main_data['MRT_rt_ms'].notna()) &
        (main_data['MRT_isCorrect'].notna())
    ].copy()
    
    print(f"Valid MRT trials: {len(mrt_data)}")
    
    # Merge with alternative parameters
    mrt_with_params = mrt_data.merge(alt_params, on='participantId', how='inner')
    print(f"MRT trials with alternative parameters: {len(mrt_with_params)}")
    
    # Test each concentration parameter type
    concentration_types = ['von_mises_kappa', 'wrapped_normal_concentration', 'wrapped_cauchy_concentration']
    
    for conc_type in concentration_types:
        print(f"Running MRT analysis with {conc_type}")
        
        # Filter out participants with missing concentration values
        valid_data = mrt_with_params[mrt_with_params[conc_type].notna()].copy()
        print(f"Participants with valid {conc_type}: {valid_data['participantId'].nunique()}")
        
        if len(valid_data) == 0:
            continue
            
        try:
            # Prepare data for R
            with localconverter(robjects.default_converter + pandas2ri.converter):
                r_data = robjects.conversion.py2rpy(valid_data[['participantId', 'MRT_rt_ms', 'MRT_isCorrect', 
                                                               'MRT_angle_degrees', conc_type]])
            r.assign('mrt_data', r_data)
            r(f'mrt_data${conc_type} <- scale(mrt_data${conc_type})[,1]')  # Standardize
            
            # MRT reaction time model
            r('''
            rt_model <- tryCatch({
                lmer(log(MRT_rt_ms) ~ MRT_angle_degrees * ''' + conc_type + ''' + 
                     (1|participantId), data=mrt_data)
            }, error = function(e) NULL)
            ''')

            rt_model = r('rt_model')
            if rt_model != robjects.NULL:
                r('rt_summary <- summary(rt_model)')
                r('rt_coefs <- fixef(rt_model)')
                r('rt_se <- sqrt(diag(vcov(rt_model)))')
                r('rt_aic <- AIC(rt_model)')
                r('rt_summary <- summary(rt_model)')
                r('rt_pvals <- coef(rt_summary)[,"Pr(>|t|)"]')

                # Extract interaction effect
                coef_names = list(r('names(rt_coefs)'))
                interaction_name = f'MRT_angle_degrees:{conc_type}'
                if interaction_name in coef_names:
                    idx = coef_names.index(interaction_name)
                    estimate = float(r('rt_coefs')[idx])
                    se = float(r('rt_se')[idx])
                    aic = float(r('rt_aic')[0])
                    p_val = float(r('rt_pvals')[idx])

                    results.append({
                        'analysis_type': 'MRT_reaction_time',
                        'distribution_type': conc_type,
                        'effect_name': 'angle_concentration_interaction',
                        'estimate': estimate,
                        'p_value': float(p_val),
                        'ci_lower': estimate - 1.96 * se,
                        'ci_upper': estimate + 1.96 * se,
                        'model_AIC': aic,
                        'significant_at_05': float(p_val) < 0.05
                    })

            # MRT accuracy model
            r('''
            acc_model <- tryCatch({
                glmer(MRT_isCorrect ~ MRT_angle_degrees * ''' + conc_type + ''' + 
                      (1|participantId), data=mrt_data, family=binomial)
            }, error = function(e) NULL)
            ''')

            acc_model = r('acc_model')
            if acc_model != robjects.NULL:
                r('acc_aic <- AIC(acc_model)')
                r('acc_coefs <- fixef(acc_model)')
                r('acc_se <- sqrt(diag(vcov(acc_model)))')
                r('acc_summary <- summary(acc_model)')
                r('acc_pvals <- coef(acc_summary)[,"Pr(>|z|)"]')

                # Extract interaction effect
                coef_names = list(r('names(acc_coefs)'))
                interaction_name = f'MRT_angle_degrees:{conc_type}'
                if interaction_name in coef_names:
                    idx = coef_names.index(interaction_name)
                    estimate = float(r('acc_coefs')[idx])
                    se = float(r('acc_se')[idx])
                    aic = float(r('acc_aic')[0])
                    p_val = float(r('acc_pvals')[idx])

                    results.append({
                        'analysis_type': 'MRT_accuracy',
                        'distribution_type': conc_type,
                        'effect_name': 'angle_concentration_interaction',
                        'estimate': estimate,
                        'p_value': float(p_val),
                        'ci_lower': estimate - 1.96 * se,
                        'ci_upper': estimate + 1.96 * se,
                        'model_AIC': aic,
                        'significant_at_05': float(p_val) < 0.05
                    })

        except Exception as e:
            print(f"Error in MRT analysis with {conc_type}: {e}")
    
    # VVIQ analyses
    print("Running VVIQ sensitivity analyses...")
    
    # Merge VVIQ data with alternative parameters
    vviq_valid = vviq_data[vviq_data['excluded'] == False].copy()
    vviq_valid = vviq_valid.rename(columns={'PROLIFIC_PID': 'participantId'})
    vviq_with_params = vviq_valid.merge(alt_params, on='participantId', how='inner')
    
    print(f"Participants with VVIQ and concentration data: {len(vviq_with_params)}")
    
    for conc_type in concentration_types:
        print(f"Running VVIQ analysis with {conc_type}")
        
        valid_vviq = vviq_with_params[vviq_with_params[conc_type].notna()].copy()
        
        if len(valid_vviq) == 0:
            continue
            
        try:
            # Prepare data for R
            with localconverter(robjects.default_converter + pandas2ri.converter):
                r_vviq = robjects.conversion.py2rpy(valid_vviq[['participantId', 'total_score', conc_type]])
            r.assign('vviq_data', r_vviq)
            r(f'vviq_data${conc_type} <- scale(vviq_data${conc_type})[,1]')  # Standardize
            
            # VVIQ regression
            r(f'vviq_model <- lm(total_score ~ {conc_type}, data=vviq_data)')
            r('vviq_summary <- summary(vviq_model)')
            r('vviq_coefs <- coef(vviq_model)')
            r('vviq_se <- sqrt(diag(vcov(vviq_model)))')
            r('vviq_aic <- AIC(vviq_model)')
            r('vviq_pvals <- coef(vviq_summary)[,"Pr(>|t|)"]')
            
            # Extract concentration effect
            coef_names = list(r('names(vviq_coefs)'))
            if conc_type in coef_names:
                idx = coef_names.index(conc_type)
                estimate = float(r('vviq_coefs')[idx])
                se = float(r('vviq_se')[idx])
                p_val = float(r('vviq_pvals')[idx])
                aic = float(r('vviq_aic')[0])
                
                results.append({
                    'analysis_type': 'VVIQ_total_score',
                    'distribution_type': conc_type,
                    'effect_name': 'concentration_main_effect',
                    'estimate': estimate,
                    'p_value': float(p_val),
                    'ci_lower': estimate - 1.96 * se,
                    'ci_upper': estimate + 1.96 * se,
                    'model_AIC': aic,
                    'significant_at_05': float(p_val) < 0.05
                })
                
        except Exception as e:
            print(f"Error in VVIQ analysis with {conc_type}: {e}")
    
    sensitivity_df = pd.DataFrame(results)
    print(f"Completed sensitivity analyses with {len(sensitivity_df)} results")
    
    return sensitivity_df

def run_non_guess_analysis(main_data_with_guess, mixture_params, vviq_data):
    """
    Run analyses excluding likely guess trials.
    
    Args:
        main_data_with_guess (pd.DataFrame): Main data with guess trial classification
        mixture_params (pd.DataFrame): Mixture model parameters
        vviq_data (pd.DataFrame): VVIQ data
        
    Returns:
        pd.DataFrame: Comparison of original vs non-guess analyses
    """
    print("Running non-guess trial analyses...")
    
    # Setup R environment
    r = robjects.r
    r('library(lme4)')
    r('library(lmerTest)')
    
    results = []
    
    # Recalculate mixture model parameters using only non-guess trials
    print("Recalculating mixture model parameters excluding guess trials...")
    
    non_guess_vwm = main_data_with_guess[
        (main_data_with_guess['isPractice'] == False) &
        (main_data_with_guess['VWM_block'] != 'practice') &
        (main_data_with_guess['excluded_from_VWM'] == False) &
        (main_data_with_guess['trial_excluded'] == False) &
        (main_data_with_guess['is_guess_trial'] == False) &
        (main_data_with_guess['VWM_error_degrees'].notna())
    ].copy()
    
    print(f"Non-guess VWM trials: {len(non_guess_vwm)}")
    
    # Calculate new kappa values for each participant using non-guess trials
    r('library(circular)')
    
    participants = non_guess_vwm['participantId'].unique()
    non_guess_kappas = {}
    
    for participant in participants:
        participant_data = non_guess_vwm[non_guess_vwm['participantId'] == participant]

        if len(participant_data) < 5:  # Need minimum trials
            continue

        errors_radians = np.deg2rad(participant_data['VWM_error_degrees'].values)

        try:
            r.assign('errors_rad', robjects.FloatVector(errors_radians))
            r('circular_errors <- circular(errors_rad)')
            r('''
            vm_fit <- tryCatch({
                mle.vonmises(circular_errors)
            }, error = function(e) list(kappa=0))
            ''')

            kappa = float(r('vm_fit$kappa')[0])
            non_guess_kappas[participant] = kappa

        except Exception as e:
            print(f"Error fitting von Mises for participant {participant}: {e}")
            non_guess_kappas[participant] = 0
    
    print(f"Calculated non-guess kappa for {len(non_guess_kappas)} participants")
    
    # Create non-guess parameters dataframe
    non_guess_params = pd.DataFrame([
        {'participantId': pid, 'non_guess_kappa': kappa} 
        for pid, kappa in non_guess_kappas.items()
    ])
    # Edge case: ensure at least one participant
    if non_guess_params.empty:
        print("Warning: No participants with sufficient non-guess trials for kappa estimation.")
        return pd.DataFrame(columns=[
            'analysis_type', 'original_estimate', 'non_guess_estimate',
            'original_p_value', 'non_guess_p_value',
            'original_n_participants', 'non_guess_n_participants',
            'effect_robust_to_guessing'
        ])
    
    # Compare original vs non-guess MRT analyses
    print("Comparing original vs non-guess MRT analyses...")
    
    # Prepare MRT data
    mrt_data = main_data_with_guess[
        (main_data_with_guess['isPractice'] == False) &
        (main_data_with_guess['MRT_block'] != 'practice') &
        (main_data_with_guess['excluded_from_MRT'] == False) &
        (main_data_with_guess['trial_excluded'] == False) &
        (main_data_with_guess['MRT_rt_ms'].notna()) &
        (main_data_with_guess['MRT_isCorrect'].notna())
    ].copy()
    
    # Merge with both original and non-guess parameters
    mrt_with_orig = mrt_data.merge(mixture_params[['participantId', 'kappa_concentration']], 
                                  on='participantId', how='inner')
    mrt_with_non_guess = mrt_data.merge(non_guess_params, on='participantId', how='inner')

    # Edge case: ensure at least one participant
    if mrt_with_orig.empty or mrt_with_non_guess.empty:
        print("Warning: No MRT trials with original or non-guess kappa available.")
        return pd.DataFrame(columns=[
            'analysis_type', 'original_estimate', 'non_guess_estimate',
            'original_p_value', 'non_guess_p_value',
            'original_n_participants', 'non_guess_n_participants',
            'effect_robust_to_guessing'
        ])

    print(f"MRT trials with original kappa: {mrt_with_orig['participantId'].nunique()} participants")
    print(f"MRT trials with non-guess kappa: {mrt_with_non_guess['participantId'].nunique()} participants")
    
    # Run original MRT reaction time analysis
    try:
        with localconverter(robjects.default_converter + pandas2ri.converter):
            r_orig = robjects.conversion.py2rpy(mrt_with_orig[['participantId', 'MRT_rt_ms', 'MRT_angle_degrees', 'kappa_concentration']])
        r.assign('mrt_orig', r_orig)
        r('mrt_orig$kappa_concentration <- scale(mrt_orig$kappa_concentration)[,1]')

        r('''
        orig_rt_model <- tryCatch({
            lmer(log(MRT_rt_ms) ~ MRT_angle_degrees * kappa_concentration + (1|participantId), data=mrt_orig)
        }, error = function(e) NULL)
        ''')

        orig_rt_model = r('orig_rt_model')
        if orig_rt_model != robjects.NULL:
            r('orig_coefs <- fixef(orig_rt_model)')
            r('orig_se <- sqrt(diag(vcov(orig_rt_model)))')
            r('orig_summary <- summary(orig_rt_model)')
            r('orig_pvals <- coef(orig_summary)[,"Pr(>|t|)"]')

            coef_names = list(r('names(orig_coefs)'))
            interaction_name = 'MRT_angle_degrees:kappa_concentration'
            if interaction_name in coef_names:
                idx = coef_names.index(interaction_name)
                orig_estimate = float(r('orig_coefs')[idx])
                orig_se = float(r('orig_se')[idx])
                orig_p = float(r('orig_pvals')[idx])
            else:
                orig_estimate = orig_p = np.nan
        else:
            orig_estimate = orig_p = np.nan

    except Exception as e:
        print(f"Error in original MRT RT analysis: {e}")
        orig_estimate = orig_p = np.nan

    # Run non-guess MRT reaction time analysis
    try:
        with localconverter(robjects.default_converter + pandas2ri.converter):
            r_ng = robjects.conversion.py2rpy(mrt_with_non_guess[['participantId', 'MRT_rt_ms', 'MRT_angle_degrees', 'non_guess_kappa']])
        r.assign('mrt_ng', r_ng)
        r('mrt_ng$non_guess_kappa <- scale(mrt_ng$non_guess_kappa)[,1]')

        r('''
        ng_rt_model <- tryCatch({
            lmer(log(MRT_rt_ms) ~ MRT_angle_degrees * non_guess_kappa + (1|participantId), data=mrt_ng)
        }, error = function(e) NULL)
        ''')

        ng_rt_model = r('ng_rt_model')
        if ng_rt_model != robjects.NULL:
            r('ng_coefs <- fixef(ng_rt_model)')
            r('ng_se <- sqrt(diag(vcov(ng_rt_model)))')
            r('ng_summary <- summary(ng_rt_model)')
            r('ng_pvals <- coef(ng_summary)[,"Pr(>|t|)"]')

            coef_names = list(r('names(ng_coefs)'))
            interaction_name = 'MRT_angle_degrees:non_guess_kappa'
            if interaction_name in coef_names:
                idx = coef_names.index(interaction_name)
                ng_estimate = float(r('ng_coefs')[idx])
                ng_se = float(r('ng_se')[idx])
                ng_p = float(r('ng_pvals')[idx])
            else:
                ng_estimate = ng_p = np.nan
        else:
            ng_estimate = ng_p = np.nan

    except Exception as e:
        print(f"Error in non-guess MRT RT analysis: {e}")
        ng_estimate = ng_p = np.nan
    
    # Add MRT RT results
    results.append({
        'analysis_type': 'MRT_reaction_time_interaction',
        'original_estimate': orig_estimate,
        'non_guess_estimate': ng_estimate,
        'original_p_value': orig_p,
        'non_guess_p_value': ng_p,
        'original_n_participants': mrt_with_orig['participantId'].nunique(),
        'non_guess_n_participants': mrt_with_non_guess['participantId'].nunique(),
        'effect_robust_to_guessing': (orig_p < 0.05) == (ng_p < 0.05) if not (np.isnan(orig_p) or np.isnan(ng_p)) else False
    })
    
    # Compare VVIQ analyses
    print("Comparing original vs non-guess VVIQ analyses...")
    
    vviq_valid = vviq_data[vviq_data['excluded'] == False].copy()
    vviq_valid = vviq_valid.rename(columns={'PROLIFIC_PID': 'participantId'})
    
    vviq_with_orig = vviq_valid.merge(mixture_params[['participantId', 'kappa_concentration']], 
                                     on='participantId', how='inner')
    vviq_with_ng = vviq_valid.merge(non_guess_params, on='participantId', how='inner')

    # Edge case: ensure at least one participant
    if vviq_with_orig.empty or vviq_with_ng.empty:
        print("Warning: No VVIQ participants with original or non-guess kappa available.")
        # Add empty VVIQ results instead of returning early
        results.append({
            'analysis_type': 'VVIQ_kappa_correlation',
            'original_estimate': np.nan,
            'non_guess_estimate': np.nan,
            'original_p_value': np.nan,
            'non_guess_p_value': np.nan,
            'original_n_participants': 0,
            'non_guess_n_participants': 0,
            'effect_robust_to_guessing': False
        })
    else:
        print(f"VVIQ with original kappa: {len(vviq_with_orig)} participants")
        print(f"VVIQ with non-guess kappa: {len(vviq_with_ng)} participants")
        
        # Original VVIQ analysis
        try:
            with localconverter(robjects.default_converter + pandas2ri.converter):
                r_vviq_orig = robjects.conversion.py2rpy(vviq_with_orig[['participantId', 'total_score', 'kappa_concentration']])
            r.assign('vviq_orig', r_vviq_orig)
            r('vviq_orig$kappa_concentration <- scale(vviq_orig$kappa_concentration)[,1]')

            r('orig_vviq_model <- lm(total_score ~ kappa_concentration, data=vviq_orig)')
            r('orig_vviq_coefs <- coef(orig_vviq_model)')
            r('orig_vviq_summary <- summary(orig_vviq_model)')
            r('orig_vviq_pvals <- coef(orig_vviq_summary)[,"Pr(>|t|)"]')

            orig_vviq_estimate = float(r('orig_vviq_coefs')[1])  # Slope coefficient
            orig_vviq_p = float(r('orig_vviq_pvals')[1])  # p-value

        except Exception as e:
            print(f"Error in original VVIQ analysis: {e}")
            orig_vviq_estimate = orig_vviq_p = np.nan

        # Non-guess VVIQ analysis
        try:
            with localconverter(robjects.default_converter + pandas2ri.converter):
                r_vviq_ng = robjects.conversion.py2rpy(vviq_with_ng[['participantId', 'total_score', 'non_guess_kappa']])
            r.assign('vviq_ng', r_vviq_ng)
            r('vviq_ng$non_guess_kappa <- scale(vviq_ng$non_guess_kappa)[,1]')

            r('ng_vviq_model <- lm(total_score ~ non_guess_kappa, data=vviq_ng)')
            r('ng_vviq_coefs <- coef(ng_vviq_model)')
            r('ng_vviq_summary <- summary(ng_vviq_model)')
            r('ng_vviq_pvals <- coef(ng_vviq_summary)[,"Pr(>|t|)"]')

            ng_vviq_estimate = float(r('ng_vviq_coefs')[1])  # Slope coefficient
            ng_vviq_p = float(r('ng_vviq_pvals')[1])  # p-value

        except Exception as e:
            print(f"Error in non-guess VVIQ analysis: {e}")
            ng_vviq_estimate = ng_vviq_p = np.nan
        
        # Add VVIQ results
        results.append({
            'analysis_type': 'VVIQ_kappa_correlation',
            'original_estimate': orig_vviq_estimate,
            'non_guess_estimate': ng_vviq_estimate,
            'original_p_value': orig_vviq_p,
            'non_guess_p_value': ng_vviq_p,
            'original_n_participants': len(vviq_with_orig),
            'non_guess_n_participants': len(vviq_with_ng),
            'effect_robust_to_guessing': (orig_vviq_p < 0.05) == (ng_vviq_p < 0.05) if not (np.isnan(orig_vviq_p) or np.isnan(ng_vviq_p)) else False
        })
    
    non_guess_df = pd.DataFrame(results)
    print(f"Completed non-guess analyses with {len(non_guess_df)} comparisons")
    
    return non_guess_df

def save_results(alt_params, sensitivity_results, non_guess_results):
    """
    Save all analysis results to output files.
    
    Args:
        alt_params (pd.DataFrame): Alternative distribution parameters
        sensitivity_results (pd.DataFrame): Sensitivity analysis results
        non_guess_results (pd.DataFrame): Non-guess analysis results
    """
    print("Saving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save alternative distribution parameters
    alt_params_file = f"outputs/alternative_distributions_parameters_{timestamp}.csv"
    alt_params.to_csv(alt_params_file, index=False)
    print(f"Saved alternative distribution parameters to {alt_params_file}")
    print("Alternative parameters columns:", list(alt_params.columns))
    print("First 2 rows of alternative parameters:")
    print(alt_params.head(2))
    
    # Save sensitivity analysis results
    sensitivity_file = f"outputs/sensitivity_analysis_results_{timestamp}.csv"
    sensitivity_results.to_csv(sensitivity_file, index=False)
    print(f"Saved sensitivity analysis results to {sensitivity_file}")
    print("Sensitivity results columns:", list(sensitivity_results.columns))
    print("First 2 rows of sensitivity results:")
    print(sensitivity_results.head(2))
    
    # Save non-guess analysis results
    non_guess_file = f"outputs/non_guess_analysis_results_{timestamp}.csv"
    non_guess_results.to_csv(non_guess_file, index=False)
    print(f"Saved non-guess analysis results to {non_guess_file}")
    print("Non-guess results columns:", list(non_guess_results.columns))
    print("First 2 rows of non-guess results:")
    print(non_guess_results.head(2))

def main():
    """
    Main function to run the sensitivity analysis pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting sensitivity analysis pipeline...")
        
        # Load and validate data
        main_data, mixture_params, vviq_data = load_and_validate_data()
        if main_data is None:
            print("Error: Failed to load required input data")
            return 1

        # Install required R packages
        install_r_packages()
        
        # Classify guess trials
        main_data_with_guess = classify_guess_trials(main_data, mixture_params)
        
        # Fit alternative distributions
        alt_params = fit_alternative_distributions(main_data, mixture_params)
        
        # Run sensitivity analyses
        sensitivity_results = run_sensitivity_analyses(main_data, alt_params, vviq_data)
        
        # Run non-guess analyses
        non_guess_results = run_non_guess_analysis(main_data_with_guess, mixture_params, vviq_data)
        
        # Save results
        save_results(alt_params, sensitivity_results, non_guess_results)
        
        print("Sensitivity analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
