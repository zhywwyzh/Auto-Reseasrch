#!/usr/bin/env python3
"""
Mixed-effects analysis script for MRT and VVIQ2 relationships with VWM parameters.
Conducts hypothesis testing with FDR correction using R mixed-effects models via rpy2.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

# Import R interface
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri, Formula
    from rpy2.robjects.packages import importr
    from rpy2.robjects.conversion import localconverter
except ImportError:
    print("ERROR: rpy2 not available. Please install rpy2.")
    sys.exit(1)

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Args:
        pattern (str): File pattern to search for
        
    Returns:
        str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_input_data():
    """
    Load all required input CSV files with validation.
    
    Returns:
        tuple: (von_mises_df, mrt_df, vviq2_df, covariates_df) or None if error
    """
    print("Loading input data files...")
    
    # Find input files
    von_mises_file = find_latest_file("outputs/VWM_von_mises_parameters_*.csv")
    mrt_file = find_latest_file("outputs/MRT_cleaned_trial_data_*.csv")
    vviq2_file = find_latest_file("outputs/VVIQ2_cleaned_scores_*.csv")
    covariates_file = find_latest_file("outputs/cognitive_covariates_*.csv")
    
    if not all([von_mises_file, mrt_file, vviq2_file, covariates_file]):
        print("ERROR: Could not find all required input files")
        return None
    
    print(f"Found files:")
    print(f"  Von Mises: {von_mises_file}")
    print(f"  MRT: {mrt_file}")
    print(f"  VVIQ2: {vviq2_file}")
    print(f"  Covariates: {covariates_file}")
    
    try:
        # Load von Mises parameters
        print("\nLoading von Mises parameters...")
        von_mises_df = pd.read_csv(von_mises_file)
        print("Von Mises columns:", list(von_mises_df.columns))
        print("Von Mises first 3 rows:")
        print(von_mises_df.head(3))
        print(f"Von Mises shape: {von_mises_df.shape}")
        
        # Validate required columns
        required_vm_cols = ['participantId', 'set_size', 'delay_seconds', 'kappa_concentration', 'parameter_estimation_reliable']
        missing_vm_cols = [col for col in required_vm_cols if col not in von_mises_df.columns]
        if missing_vm_cols:
            print(f"ERROR: Missing von Mises columns: {missing_vm_cols}")
            return None
            
        # Print unique values for experimental design parameters
        print("Von Mises set_size unique values:", sorted(von_mises_df['set_size'].unique()))
        print("Von Mises delay_seconds unique values:", sorted(von_mises_df['delay_seconds'].unique()))
        print("Von Mises parameter_estimation_reliable unique values:", von_mises_df['parameter_estimation_reliable'].unique())
        print("Von Mises kappa_concentration data type:", von_mises_df['kappa_concentration'].dtype)
        
        # Load MRT data
        print("\nLoading MRT data...")
        mrt_df = pd.read_csv(mrt_file)
        print("MRT columns:", list(mrt_df.columns))
        print("MRT first 3 rows:")
        print(mrt_df.head(3))
        print(f"MRT shape: {mrt_df.shape}")
        
        # Validate required columns
        required_mrt_cols = ['participantId', 'rotation_angle_degrees', 'is_correct', 'log_response_time_ms', 
                            'trial_valid_accuracy_analysis', 'trial_valid_rt_analysis', 'trial_type']
        missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_df.columns]
        if missing_mrt_cols:
            print(f"ERROR: Missing MRT columns: {missing_mrt_cols}")
            return None
            
        # Print unique values for experimental design parameters
        print("MRT rotation_angle_degrees unique values:", sorted(mrt_df['rotation_angle_degrees'].unique()))
        print("MRT trial_type unique values:", mrt_df['trial_type'].unique())
        print("MRT is_correct unique values:", mrt_df['is_correct'].unique())
        print("MRT trial_valid_accuracy_analysis unique values:", mrt_df['trial_valid_accuracy_analysis'].unique())
        print("MRT trial_valid_rt_analysis unique values:", mrt_df['trial_valid_rt_analysis'].unique())
        print("MRT log_response_time_ms data type:", mrt_df['log_response_time_ms'].dtype)
        
        # Load VVIQ2 data
        print("\nLoading VVIQ2 data...")
        vviq2_df = pd.read_csv(vviq2_file)
        print("VVIQ2 columns:", list(vviq2_df.columns))
        print("VVIQ2 first 3 rows:")
        print(vviq2_df.head(3))
        print(f"VVIQ2 shape: {vviq2_df.shape}")
        
        # Validate required columns
        required_vviq2_cols = ['participantId', 'total_vividness_score', 'familiar_person_score', 'sunrise_score', 
                              'shop_front_score', 'countryside_score', 'driving_scenario_score', 'beach_scene_score', 
                              'railway_station_score', 'garden_scene_score', 'questionnaire_valid']
        missing_vviq2_cols = [col for col in required_vviq2_cols if col not in vviq2_df.columns]
        if missing_vviq2_cols:
            print(f"ERROR: Missing VVIQ2 columns: {missing_vviq2_cols}")
            return None
            
        # Print unique values for experimental design parameters
        print("VVIQ2 questionnaire_valid unique values:", vviq2_df['questionnaire_valid'].unique())
        print("VVIQ2 total_vividness_score data type:", vviq2_df['total_vividness_score'].dtype)
        
        # Load covariates data
        print("\nLoading covariates data...")
        covariates_df = pd.read_csv(covariates_file)
        print("Covariates columns:", list(covariates_df.columns))
        print("Covariates first 3 rows:")
        print(covariates_df.head(3))
        print(f"Covariates shape: {covariates_df.shape}")
        
        # Validate required columns
        required_cov_cols = ['participantId', 'rt_cv_standardized', 'focus_loss_instances_standardized', 'focus_loss_duration_standardized']
        missing_cov_cols = [col for col in required_cov_cols if col not in covariates_df.columns]
        if missing_cov_cols:
            print(f"ERROR: Missing covariates columns: {missing_cov_cols}")
            return None
            
        print("Covariates data types:")
        for col in required_cov_cols[1:]:  # Skip participantId
            print(f"  {col}: {covariates_df[col].dtype}")
        
        return von_mises_df, mrt_df, vviq2_df, covariates_df
        
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return None

def prepare_analysis_datasets(von_mises_df, mrt_df, vviq2_df, covariates_df):
    """
    Prepare and filter datasets for analysis.
    
    Args:
        von_mises_df (pd.DataFrame): Von Mises parameters data
        mrt_df (pd.DataFrame): MRT trial data
        vviq2_df (pd.DataFrame): VVIQ2 scores data
        covariates_df (pd.DataFrame): Cognitive covariates data
        
    Returns:
        tuple: (kappa_avg_df, mrt_test_df, vviq2_valid_df, covariates_df)
    """
    print("\nPreparing analysis datasets...")
    
    # Filter von Mises to reliable estimates and calculate average kappa
    print("Filtering von Mises parameters to reliable estimates...")
    vm_reliable = von_mises_df[von_mises_df['parameter_estimation_reliable'] == True].copy()
    print(f"Von Mises reliable estimates: {len(vm_reliable)} out of {len(von_mises_df)}")
    
    print("Calculating average kappa per participant...")
    kappa_avg_df = vm_reliable.groupby('participantId')['kappa_concentration'].mean().reset_index()
    kappa_avg_df.columns = ['participantId', 'kappa_avg']
    print(f"Average kappa calculated for {len(kappa_avg_df)} participants")
    print("Kappa average first 2 rows:")
    print(kappa_avg_df.head(2))
    
    # Filter MRT to test trials
    print("\nFiltering MRT data to test trials...")
    mrt_test_df = mrt_df[mrt_df['trial_type'] == 'test'].copy()
    print(f"MRT test trials: {len(mrt_test_df)} out of {len(mrt_df)}")
    print("MRT test data first 2 rows:")
    print(mrt_test_df.head(2))
    
    # Filter VVIQ2 to valid questionnaires
    print("\nFiltering VVIQ2 data to valid questionnaires...")
    vviq2_valid_df = vviq2_df[vviq2_df['questionnaire_valid'] == True].copy()
    print(f"VVIQ2 valid questionnaires: {len(vviq2_valid_df)} out of {len(vviq2_df)}")
    print("VVIQ2 valid data first 2 rows:")
    print(vviq2_valid_df.head(2))
    
    return kappa_avg_df, mrt_test_df, vviq2_valid_df, covariates_df

def setup_r_environment():
    """
    Set up R environment and install/load required packages.
    
    Returns:
        dict: Dictionary of R package objects
    """
    print("\nSetting up R environment...")
    
    try:
        # Import base packages
        base = importr('base')
        stats = importr('stats')
        utils = importr('utils')
        
        # Install required packages if not present
        packages = ['lme4', 'lm.beta']
        for package in packages:
            try:
                robjects.r(f'library({package})')
                print(f"R package {package} already available")
            except Exception as e:
                print(f"Installing R package: {package}...")
                try:
                    utils.install_packages(package, repos='https://cloud.r-project.org/')
                    robjects.r(f'library({package})')
                    print(f"Successfully installed and loaded {package}")
                except Exception as install_error:
                    print(f"ERROR: Failed to install R package {package}: {install_error}")
                    return None
        
        # Import packages
        try:
            lme4 = importr('lme4')
            lm_beta = importr('lm.beta')
        except Exception as e:
            print(f"ERROR: Failed to import R packages: {e}")
            return None
        
        print("R packages loaded successfully")
        return {'base': base, 'stats': stats, 'lme4': lme4, 'lm.beta': lm_beta}
        
    except Exception as e:
        print(f"ERROR setting up R environment: {e}")
        return None

def conduct_mrt_accuracy_analysis(mrt_data, kappa_data, covariates_data, r_packages):
    """
    Conduct MRT accuracy analysis using logistic mixed-effects model.
    
    Args:
        mrt_data (pd.DataFrame): MRT test trial data
        kappa_data (pd.DataFrame): Average kappa values per participant
        covariates_data (pd.DataFrame): Cognitive covariates
        r_packages (dict): R package objects
        
    Returns:
        tuple: (Results dataframe with model statistics, analysis-ready dataset)
    """
    print("\nConducting MRT accuracy analysis...")
    
    # Filter to valid accuracy trials
    acc_data = mrt_data[mrt_data['trial_valid_accuracy_analysis'] == True].copy()
    print(f"Valid accuracy trials: {len(acc_data)}")
    
    # Merge with kappa and covariates
    acc_data = acc_data.merge(kappa_data, on='participantId', how='inner')
    acc_data = acc_data.merge(covariates_data, on='participantId', how='inner')
    print(f"Merged accuracy data: {len(acc_data)} trials")
    print("Accuracy analysis data first 2 rows:")
    print(acc_data.head(2))

    # Standardize continuous predictors to improve model convergence
    acc_data['kappa_avg_scaled'] = (acc_data['kappa_avg'] - acc_data['kappa_avg'].mean()) / acc_data['kappa_avg'].std()
    acc_data['rotation_angle_degrees_scaled'] = (acc_data['rotation_angle_degrees'] - acc_data['rotation_angle_degrees'].mean()) / acc_data['rotation_angle_degrees'].std()

    # Convert boolean to numeric for R
    acc_data['is_correct_numeric'] = acc_data['is_correct'].astype(int)

    # Convert to R dataframe using new conversion context
    with localconverter(robjects.default_converter + pandas2ri.converter):
        r_acc_data = robjects.conversion.py2rpy(acc_data)

    print("Fitting logistic mixed-effects model for accuracy...")

    # Fit logistic mixed-effects model
    try:
        robjects.globalenv['acc_data'] = r_acc_data

        # Fit model with glmer and calculate confidence intervals
        model_formula = """
        is_correct_numeric ~ kappa_avg_scaled + rotation_angle_degrees_scaled + kappa_avg_scaled:rotation_angle_degrees_scaled + 
        rt_cv_standardized + focus_loss_instances_standardized + focus_loss_duration_standardized + 
        (1|participantId)
        """

        robjects.r(f"""
        library(lme4)
        acc_model <- glmer({model_formula}, data=acc_data, family=binomial)
        acc_summary <- summary(acc_model)
        acc_ci <- confint(acc_model, method="Wald")
        """)

        # Extract results robustly
        acc_summary = robjects.r('acc_summary')
        with localconverter(robjects.default_converter + pandas2ri.converter):
            coeffs_df = robjects.conversion.rpy2py(robjects.r('acc_summary$coefficients'))
            ci_df = robjects.conversion.rpy2py(robjects.r('acc_ci'))

        # Extract coefficient names from R
        coeff_names = list(robjects.r('rownames(acc_summary$coefficients)'))
        ci_names = list(robjects.r('rownames(acc_ci)'))

        print("Accuracy model fitted successfully")
        print("Accuracy model coefficients:")
        print(coeffs_df)

        # Create results dataframe using proper indexing
        results = []
        print(f"Extracting {len(coeff_names)} coefficients from model")
        print(f"Coefficient names: {coeff_names}")
        for i, coeff_name in enumerate(coeff_names):
            row = coeffs_df[i, :]  # numpy array row
            # Find corresponding CI by name for robustness
            try:
                ci_idx = ci_names.index(coeff_name)
                ci_lower = ci_df[ci_idx, 0]
                ci_upper = ci_df[ci_idx, 1]
            except (ValueError, IndexError):
                ci_lower, ci_upper = np.nan, np.nan

            results.append({
                'model_type': 'MRT_accuracy',
                'effect': coeff_name,
                'coefficient_estimate': float(row[0]) if len(row) > 0 else np.nan,
                'standard_error': float(row[1]) if len(row) > 1 else np.nan,
                't_value': float(row[2]) if len(row) > 2 else np.nan,
                'p_value': float(row[3]) if len(row) > 3 else np.nan,
                'p_value_fdr_adjusted': np.nan,
                'confidence_interval_lower': float(ci_lower),
                'confidence_interval_upper': float(ci_upper),
                'odds_ratio': np.exp(float(row[0])) if len(row) > 0 else np.nan,
                'significance_fdr': False
            })

        return pd.DataFrame(results), acc_data

    except Exception as e:
        print(f"ERROR in accuracy analysis: {e}")
        return pd.DataFrame(), acc_data

def conduct_mrt_rt_analysis(mrt_data, kappa_data, covariates_data, r_packages):
    """
    Conduct MRT reaction time analysis using linear mixed-effects model.
    
    Args:
        mrt_data (pd.DataFrame): MRT test trial data
        kappa_data (pd.DataFrame): Average kappa values per participant
        covariates_data (pd.DataFrame): Cognitive covariates
        r_packages (dict): R package objects
        
    Returns:
        tuple: (Results dataframe with model statistics, analysis-ready dataset)
    """
    print("\nConducting MRT reaction time analysis...")
    
    # Filter to valid RT trials (correct responses only)
    rt_data = mrt_data[(mrt_data['trial_valid_rt_analysis'] == True) & 
                       (mrt_data['is_correct'] == True)].copy()
    print(f"Valid RT trials: {len(rt_data)}")
    
    # Merge with kappa and covariates
    rt_data = rt_data.merge(kappa_data, on='participantId', how='inner')
    rt_data = rt_data.merge(covariates_data, on='participantId', how='inner')
    print(f"Merged RT data: {len(rt_data)} trials")
    print("RT analysis data first 2 rows:")
    print(rt_data.head(2))

    # Standardize continuous predictors to improve model convergence
    rt_data['kappa_avg_scaled'] = (rt_data['kappa_avg'] - rt_data['kappa_avg'].mean()) / rt_data['kappa_avg'].std()
    rt_data['rotation_angle_degrees_scaled'] = (rt_data['rotation_angle_degrees'] - rt_data['rotation_angle_degrees'].mean()) / rt_data['rotation_angle_degrees'].std()

    # Convert to R dataframe using new conversion context
    with localconverter(robjects.default_converter + pandas2ri.converter):
        r_rt_data = robjects.conversion.py2rpy(rt_data)

    print("Fitting linear mixed-effects model for reaction time...")

    # Fit linear mixed-effects model
    try:
        robjects.globalenv['rt_data'] = r_rt_data

        # Fit model with lmer and calculate confidence intervals
        model_formula = """
        log_response_time_ms ~ kappa_avg_scaled + rotation_angle_degrees_scaled + kappa_avg_scaled:rotation_angle_degrees_scaled + 
        rt_cv_standardized + focus_loss_instances_standardized + focus_loss_duration_standardized + 
        (1|participantId)
        """

        robjects.r(f"""
        library(lme4)
        rt_model <- lmer({model_formula}, data=rt_data)
        rt_summary <- summary(rt_model)
        rt_ci <- confint(rt_model, method="Wald")
        """)

        # Extract results robustly
        rt_summary = robjects.r('rt_summary')
        with localconverter(robjects.default_converter + pandas2ri.converter):
            coeffs_df = robjects.conversion.rpy2py(robjects.r('rt_summary$coefficients'))
            ci_df = robjects.conversion.rpy2py(robjects.r('rt_ci'))

        # Extract coefficient names from R
        coeff_names = list(robjects.r('rownames(rt_summary$coefficients)'))
        ci_names = list(robjects.r('rownames(rt_ci)'))

        print("RT model fitted successfully")
        print("RT model coefficients:")
        print(coeffs_df)

        # Create results dataframe using proper indexing
        results = []
        print(f"Extracting {len(coeff_names)} coefficients from model")
        print(f"Coefficient names: {coeff_names}")
        for i, coeff_name in enumerate(coeff_names):
            row = coeffs_df[i, :]  # numpy array row
            # Find corresponding CI by name for robustness
            try:
                ci_idx = ci_names.index(coeff_name)
                ci_lower = ci_df[ci_idx, 0]
                ci_upper = ci_df[ci_idx, 1]
            except (ValueError, IndexError):
                ci_lower, ci_upper = np.nan, np.nan

            results.append({
                'model_type': 'MRT_reaction_time',
                'effect': coeff_name,
                'coefficient_estimate': float(row[0]) if len(row) > 0 else np.nan,
                'standard_error': float(row[1]) if len(row) > 1 else np.nan,
                't_value': float(row[2]) if len(row) > 2 else np.nan,
                'p_value': float(row[3]) if len(row) > 3 else np.nan,
                'p_value_fdr_adjusted': np.nan,
                'confidence_interval_lower': float(ci_lower),
                'confidence_interval_upper': float(ci_upper),
                'odds_ratio': np.nan,
                'significance_fdr': False
            })

        return pd.DataFrame(results), rt_data

    except Exception as e:
        print(f"ERROR in RT analysis: {e}")
        return pd.DataFrame(), rt_data

def conduct_vviq2_analyses(vviq2_data, kappa_data, covariates_data):
    """
    Conduct VVIQ2 regression analyses for total score and subscales.
    
    Args:
        vviq2_data (pd.DataFrame): VVIQ2 scores data
        kappa_data (pd.DataFrame): Average kappa values per participant
        covariates_data (pd.DataFrame): Cognitive covariates
        
    Returns:
        tuple: (Results dataframe with regression statistics, analysis-ready dataset)
    """
    print("\nConducting VVIQ2 analyses...")
    
    # Merge datasets
    vviq2_merged = vviq2_data.merge(kappa_data, on='participantId', how='inner')
    vviq2_merged = vviq2_merged.merge(covariates_data, on='participantId', how='inner')
    # Add scaled kappa column for saving
    vviq2_merged['kappa_avg_scaled'] = (vviq2_merged['kappa_avg'] - vviq2_merged['kappa_avg'].mean()) / vviq2_merged['kappa_avg'].std()
    print(f"Merged VVIQ2 data: {len(vviq2_merged)} participants")
    print("VVIQ2 merged data first 2 rows:")
    print(vviq2_merged.head(2))
    
    # Define VVIQ2 measures
    vviq2_measures = ['total_vividness_score', 'familiar_person_score', 'sunrise_score', 
                     'shop_front_score', 'countryside_score', 'driving_scenario_score', 
                     'beach_scene_score', 'railway_station_score', 'garden_scene_score']
    
    results = []
    
    for measure in vviq2_measures:
        print(f"\nAnalyzing {measure}...")
        
        try:
            # Prepare data for regression
            reg_data = vviq2_merged[['participantId', measure, 'kappa_avg', 'rt_cv_standardized', 
                                   'focus_loss_instances_standardized', 'focus_loss_duration_standardized']].dropna()

            print(f"  Valid data for {measure}: {len(reg_data)} participants")

            if len(reg_data) < 10:  # Minimum sample size check
                print(f"  Insufficient data for {measure}, skipping...")
                continue

            # Scale kappa_avg for consistency
            reg_data['kappa_avg_scaled'] = (reg_data['kappa_avg'] - reg_data['kappa_avg'].mean()) / reg_data['kappa_avg'].std()

            # Convert to R dataframe using new conversion context
            with localconverter(robjects.default_converter + pandas2ri.converter):
                r_reg_data = robjects.conversion.py2rpy(reg_data)
            robjects.globalenv['reg_data'] = r_reg_data

            # Fit regression model with standardized coefficients
            try:
                robjects.r(f"""
                library(stats)
                library(lm.beta)
                reg_model <- lm({measure} ~ kappa_avg_scaled + rt_cv_standardized + focus_loss_instances_standardized + focus_loss_duration_standardized, data=reg_data)
                reg_summary <- summary(reg_model)
                reg_ci <- confint(reg_model)
                reg_beta <- lm.beta(reg_model)
                """)
            except Exception as model_fit_exc:
                print(f"  ERROR: Model fitting failed for {measure}: {model_fit_exc}")
                continue

            # Check if model converged properly
            try:
                model_converged = bool(robjects.r('!any(is.na(coef(reg_model)))')[0])
            except Exception as conv_exc:
                print(f"  ERROR: Could not check model convergence for {measure}: {conv_exc}")
                continue
            if not model_converged:
                print(f"  Warning: Model for {measure} may not have converged properly")
                continue

            # Extract results
            reg_summary = robjects.r('reg_summary')
            r_squared = float(robjects.r('reg_summary$r.squared')[0])
            with localconverter(robjects.default_converter + pandas2ri.converter):
                coeffs_df = robjects.conversion.rpy2py(robjects.r('reg_summary$coefficients'))
                ci_df = robjects.conversion.rpy2py(robjects.r('reg_ci'))
                beta_df = robjects.conversion.rpy2py(robjects.r('summary(reg_beta)$coefficients'))

            # Extract coefficient names from R
            coeff_names = list(robjects.r('rownames(reg_summary$coefficients)'))
            ci_names = list(robjects.r('rownames(reg_ci)'))
            beta_names = list(robjects.r('rownames(summary(reg_beta)$coefficients)'))

            print(f"  {measure} model fitted successfully")
            print(f"  R-squared: {r_squared:.4f}")
            print(f"  Extracting {len(coeff_names)} coefficients from model")
            print(f"  Coefficient names: {coeff_names}")

            # Extract coefficient results with robust indexing and partial R-squared calculation
            df_residual = float(robjects.r('reg_summary$df[2]')[0])
            for i, predictor in enumerate(coeff_names):
                row = coeffs_df[i, :]
                try:
                    ci_idx = ci_names.index(predictor)
                    ci_lower = ci_df[ci_idx, 0]
                    ci_upper = ci_df[ci_idx, 1]
                except (ValueError, IndexError):
                    ci_lower, ci_upper = np.nan, np.nan
                try:
                    beta_idx = beta_names.index(predictor)
                    beta_std = beta_df[beta_idx, 0]
                except (ValueError, IndexError):
                    beta_std = np.nan
                t_val = float(row[2]) if len(row) > 2 else np.nan
                # Calculate partial R-squared from t-statistic
                partial_r2 = (t_val**2) / (t_val**2 + df_residual) if not np.isnan(t_val) and predictor != '(Intercept)' else np.nan
                results.append({
                    'vviq2_measure': measure,
                    'predictor': predictor,
                    'coefficient_estimate': float(row[0]) if len(row) > 0 else np.nan,
                    'standard_error': float(row[1]) if len(row) > 1 else np.nan,
                    't_value': t_val,
                    'p_value': float(row[3]) if len(row) > 3 else np.nan,
                    'p_value_fdr_adjusted': np.nan,
                    'confidence_interval_lower': float(ci_lower),
                    'confidence_interval_upper': float(ci_upper),
                    'beta_standardized': float(beta_std),
                    'model_r_squared': r_squared,
                    'partial_r_squared': partial_r2,
                    'significance_fdr': False
                })

        except Exception as e:
            print(f"ERROR analyzing {measure}: {e}")
            continue
    
    return pd.DataFrame(results), vviq2_merged

def apply_fdr_correction(results_df, p_value_col='p_value', effects_to_correct=None):
    """
    Apply Benjamini-Hochberg FDR correction to p-values for specific effects.
    
    Args:
        results_df (pd.DataFrame): Results dataframe with p-values
        p_value_col (str): Name of p-value column
        effects_to_correct (list or None): List of effect names to apply FDR correction to
        
    Returns:
        pd.DataFrame: Results with FDR-corrected p-values
    """
    print(f"\nApplying FDR correction to {len(results_df)} tests...")

    if len(results_df) == 0 or p_value_col not in results_df.columns:
        print("No valid results for FDR correction")
        return results_df

    # Determine which rows to apply FDR correction to
    if effects_to_correct is not None:
        if 'effect' in results_df.columns:
            target_rows = results_df['effect'].isin(effects_to_correct)
        elif 'predictor' in results_df.columns:
            target_rows = results_df['predictor'].isin(effects_to_correct)
        else:
            # If neither column exists, apply to all rows as fallback
            target_rows = pd.Series(True, index=results_df.index)
    else:
        target_rows = pd.Series(True, index=results_df.index)

    # Get valid p-values for target rows
    valid_p = target_rows & ~results_df[p_value_col].isna()
    p_values = results_df.loc[valid_p, p_value_col].values

    if len(p_values) == 0:
        print("No valid p-values found for FDR correction")
        results_df['p_value_fdr_adjusted'] = np.nan
        results_df['significance_fdr'] = False
        return results_df

    # Apply Benjamini-Hochberg correction
    n_tests = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p_values = p_values[sorted_indices]

    # Calculate FDR-adjusted p-values
    fdr_p_values = np.zeros_like(sorted_p_values)
    for i in range(n_tests-1, -1, -1):
        if i == n_tests - 1:
            fdr_p_values[i] = sorted_p_values[i]
        else:
            fdr_p_values[i] = min(sorted_p_values[i] * n_tests / (i + 1), fdr_p_values[i + 1])

    # Map back to original order
    adjusted_p_values = np.zeros_like(p_values)
    adjusted_p_values[sorted_indices] = fdr_p_values

    # Update dataframe
    results_df_copy = results_df.copy()
    results_df_copy.loc[valid_p, 'p_value_fdr_adjusted'] = adjusted_p_values
    results_df_copy.loc[valid_p, 'significance_fdr'] = adjusted_p_values < 0.05

    # Set non-target rows to nan/False for FDR columns if not already set
    if effects_to_correct is not None:
        results_df_copy.loc[~target_rows, 'p_value_fdr_adjusted'] = np.nan
        results_df_copy.loc[~target_rows, 'significance_fdr'] = False

    print(f"FDR correction applied. Significant tests: {sum(adjusted_p_values < 0.05)}")

    return results_df_copy

def create_hypothesis_summary(mrt_results, vviq2_results):
    """
    Create hypothesis test summary based on results.
    
    Args:
        mrt_results (pd.DataFrame): MRT mixed-effects results
        vviq2_results (pd.DataFrame): VVIQ2 regression results
        
    Returns:
        pd.DataFrame: Hypothesis summary dataframe
    """
    print("\nCreating hypothesis test summary...")
    
    hypothesis_summary = []
    
    # H1: MRT accuracy main effect of kappa (scaled)
    h1_result = mrt_results[(mrt_results['model_type'] == 'MRT_accuracy') & 
                           (mrt_results['effect'] == 'kappa_avg_scaled')]
    if not h1_result.empty:
        row = h1_result.iloc[0]
        hypothesis_summary.append({
            'hypothesis_number': 'H1',
            'hypothesis_description': 'VWM precision predicts MRT accuracy performance',
            'test_conducted': 'Logistic mixed-effects model main effect of kappa',
            'result_supported': bool(row['significance_fdr']),
            'key_statistic': float(row['coefficient_estimate']),
            'p_value_fdr': float(row['p_value_fdr_adjusted']),
            'effect_size': float(row['odds_ratio']),
            'effect_size_interpretation': 'Odds ratio'
        })
    
    # H2: MRT reaction time main effect of kappa (scaled)
    h2_result = mrt_results[(mrt_results['model_type'] == 'MRT_reaction_time') & 
                           (mrt_results['effect'] == 'kappa_avg_scaled')]
    if not h2_result.empty:
        row = h2_result.iloc[0]
        hypothesis_summary.append({
            'hypothesis_number': 'H2',
            'hypothesis_description': 'VWM precision predicts MRT reaction time performance',
            'test_conducted': 'Linear mixed-effects model main effect of kappa',
            'result_supported': bool(row['significance_fdr']),
            'key_statistic': float(row['coefficient_estimate']),
            'p_value_fdr': float(row['p_value_fdr_adjusted']),
            'effect_size': float(row['coefficient_estimate']),
            'effect_size_interpretation': 'Unstandardized coefficient'
        })
    
    # H3: MRT kappa x rotation angle interaction (scaled)
    h3_acc_result = mrt_results[(mrt_results['model_type'] == 'MRT_accuracy') & 
                               (mrt_results['effect'] == 'kappa_avg_scaled:rotation_angle_degrees_scaled')]
    h3_rt_result = mrt_results[(mrt_results['model_type'] == 'MRT_reaction_time') & 
                              (mrt_results['effect'] == 'kappa_avg_scaled:rotation_angle_degrees_scaled')]
    
    if not h3_acc_result.empty:
        row = h3_acc_result.iloc[0]
        hypothesis_summary.append({
            'hypothesis_number': 'H3a',
            'hypothesis_description': 'VWM precision x rotation angle interaction for MRT accuracy',
            'test_conducted': 'Logistic mixed-effects model interaction effect',
            'result_supported': bool(row['significance_fdr']),
            'key_statistic': float(row['coefficient_estimate']),
            'p_value_fdr': float(row['p_value_fdr_adjusted']),
            'effect_size': float(row['odds_ratio']),
            'effect_size_interpretation': 'Odds ratio'
        })
    
    if not h3_rt_result.empty:
        row = h3_rt_result.iloc[0]
        hypothesis_summary.append({
            'hypothesis_number': 'H3b',
            'hypothesis_description': 'VWM precision x rotation angle interaction for MRT reaction time',
            'test_conducted': 'Linear mixed-effects model interaction effect',
            'result_supported': bool(row['significance_fdr']),
            'key_statistic': float(row['coefficient_estimate']),
            'p_value_fdr': float(row['p_value_fdr_adjusted']),
            'effect_size': float(row['coefficient_estimate']),
            'effect_size_interpretation': 'Unstandardized coefficient'
        })
    
    # H4: VVIQ2 total score relationship with kappa (scaled)
    h4_result = vviq2_results[(vviq2_results['vviq2_measure'] == 'total_vividness_score') & 
                             (vviq2_results['predictor'] == 'kappa_avg_scaled')]
    if not h4_result.empty:
        row = h4_result.iloc[0]
        hypothesis_summary.append({
            'hypothesis_number': 'H4',
            'hypothesis_description': 'VWM precision relates to VVIQ2 total vividness score',
            'test_conducted': 'Multiple regression of total VVIQ2 score',
            'result_supported': bool(row['significance_fdr']),
            'key_statistic': float(row['coefficient_estimate']),
            'p_value_fdr': float(row['p_value_fdr_adjusted']),
            'effect_size': float(row['beta_standardized']),
            'effect_size_interpretation': 'Standardized coefficient (beta)'
        })
    
    # H5: VVIQ2 subscale relationships with kappa (scaled)
    subscale_results = vviq2_results[(vviq2_results['vviq2_measure'] != 'total_vividness_score') & 
                                    (vviq2_results['predictor'] == 'kappa_avg_scaled')]
    if not subscale_results.empty:
        significant_subscales = subscale_results[subscale_results['significance_fdr'] == True]
        hypothesis_summary.append({
            'hypothesis_number': 'H5',
            'hypothesis_description': 'VWM precision relates to VVIQ2 subscale scores',
            'test_conducted': f'Multiple regressions of {len(subscale_results)} VVIQ2 subscales',
            'result_supported': len(significant_subscales) > 0,
            'key_statistic': float(len(significant_subscales)),
            'p_value_fdr': float(significant_subscales['p_value_fdr_adjusted'].min()) if len(significant_subscales) > 0 else 1.0,
            'effect_size': float(significant_subscales['beta_standardized'].abs().max()) if len(significant_subscales) > 0 else 0.0,
            'effect_size_interpretation': f'{len(significant_subscales)} significant subscales (max |beta|)'
        })
    
    return pd.DataFrame(hypothesis_summary)

def save_analysis_datasets(acc_data, rt_data, vviq2_merged):
    """
    Save analysis-ready datasets to CSV files with specified columns.
    """
    print("\nSaving analysis-ready datasets to CSV files...")

    os.makedirs('outputs', exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save MRT accuracy analysis dataset with exact required columns
    acc_cols = [
        'participantId', 'rotation_angle_degrees', 'is_correct', 'trial_valid_accuracy_analysis',
        'kappa_avg_scaled', 'rotation_angle_degrees_scaled', 'rt_cv_standardized', 
        'focus_loss_instances_standardized', 'focus_loss_duration_standardized'
    ]
    acc_filename = f"outputs/MRT_accuracy_analysis_data_{timestamp}.csv"
    acc_data[acc_cols].to_csv(acc_filename, index=False)
    print(f"Saved MRT accuracy analysis data to: {acc_filename}")

    # Save MRT RT analysis dataset with exact required columns
    rt_cols = [
        'participantId', 'rotation_angle_degrees', 'log_response_time_ms', 'is_correct',
        'trial_valid_rt_analysis', 'kappa_avg_scaled', 'rotation_angle_degrees_scaled',
        'rt_cv_standardized', 'focus_loss_instances_standardized', 'focus_loss_duration_standardized'
    ]
    rt_filename = f"outputs/MRT_rt_analysis_data_{timestamp}.csv"
    rt_data[rt_cols].to_csv(rt_filename, index=False)
    print(f"Saved MRT RT analysis data to: {rt_filename}")

    # Save VVIQ2 analysis dataset with exact required columns
    vviq2_cols = [
        'participantId', 'total_vividness_score', 'familiar_person_score', 'sunrise_score',
        'shop_front_score', 'countryside_score', 'driving_scenario_score', 'beach_scene_score',
        'railway_station_score', 'garden_scene_score', 'kappa_avg_scaled',
        'rt_cv_standardized', 'focus_loss_instances_standardized', 'focus_loss_duration_standardized'
    ]
    vviq2_filename = f"outputs/VVIQ2_analysis_data_{timestamp}.csv"
    vviq2_merged[vviq2_cols].to_csv(vviq2_filename, index=False)
    print(f"Saved VVIQ2 analysis data to: {vviq2_filename}")


def save_results(mrt_results, vviq2_results, hypothesis_summary, acc_data, rt_data, vviq2_merged):
    """
    Save all results to CSV files with timestamps, including analysis datasets.
    
    Args:
        mrt_results (pd.DataFrame): MRT mixed-effects results
        vviq2_results (pd.DataFrame): VVIQ2 regression results
        hypothesis_summary (pd.DataFrame): Hypothesis test summary
        acc_data (pd.DataFrame): MRT accuracy analysis-ready dataset
        rt_data (pd.DataFrame): MRT RT analysis-ready dataset
        vviq2_merged (pd.DataFrame): VVIQ2 analysis-ready dataset
    """
    print("\nSaving results to CSV files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save MRT results
    mrt_filename = f"outputs/MRT_mixed_effects_results_{timestamp}.csv"
    mrt_results.to_csv(mrt_filename, index=False)
    print(f"Saved MRT results to: {mrt_filename}")
    print("MRT results preview:")
    print(mrt_results.head(2))
    
    # Save VVIQ2 results
    vviq2_filename = f"outputs/VVIQ2_regression_results_{timestamp}.csv"
    vviq2_results.to_csv(vviq2_filename, index=False)
    print(f"Saved VVIQ2 results to: {vviq2_filename}")
    print("VVIQ2 results preview:")
    print(vviq2_results.head(2))
    
    # Save hypothesis summary
    hypothesis_filename = f"outputs/hypothesis_test_summary_{timestamp}.csv"
    hypothesis_summary.to_csv(hypothesis_filename, index=False)
    print(f"Saved hypothesis summary to: {hypothesis_filename}")
    print("Hypothesis summary preview:")
    print(hypothesis_summary.head(2))

    # Save analysis-ready datasets
    save_analysis_datasets(acc_data, rt_data, vviq2_merged)

def main():
    """
    Main function to execute the analysis pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting mixed-effects analysis for MRT and VVIQ2 relationships with VWM parameters")
        print("=" * 80)
        
        # Load input data
        data_tuple = load_input_data()
        if data_tuple is None:
            return 1
        
        von_mises_df, mrt_df, vviq2_df, covariates_df = data_tuple
        
        # Prepare analysis datasets
        kappa_avg_df, mrt_test_df, vviq2_valid_df, covariates_df = prepare_analysis_datasets(
            von_mises_df, mrt_df, vviq2_df, covariates_df
        )
        
        # Setup R environment
        r_packages = setup_r_environment()
        if r_packages is None:
            return 1
        
        # Conduct MRT analyses
        print("\n" + "="*50)
        print("CONDUCTING MRT ANALYSES")
        print("="*50)
        
        mrt_acc_results, acc_data = conduct_mrt_accuracy_analysis(mrt_test_df, kappa_avg_df, covariates_df, r_packages)
        mrt_rt_results, rt_data = conduct_mrt_rt_analysis(mrt_test_df, kappa_avg_df, covariates_df, r_packages)
        
        # Combine MRT results
        mrt_results = pd.concat([mrt_acc_results, mrt_rt_results], ignore_index=True)
        print(f"Combined MRT results: {len(mrt_results)} rows")
        
        # Apply FDR correction to MRT results
        mrt_results = apply_fdr_correction(
            mrt_results,
            effects_to_correct=['kappa_avg_scaled', 'kappa_avg_scaled:rotation_angle_degrees_scaled']
        )
        
        # Conduct VVIQ2 analyses
        print("\n" + "="*50)
        print("CONDUCTING VVIQ2 ANALYSES")
        print("="*50)
        
        vviq2_results, vviq2_merged = conduct_vviq2_analyses(vviq2_valid_df, kappa_avg_df, covariates_df)
        print(f"VVIQ2 results: {len(vviq2_results)} rows")
        
        # Apply FDR correction to VVIQ2 results
        vviq2_results = apply_fdr_correction(
            vviq2_results,
            effects_to_correct=['kappa_avg_scaled']
        )
        
        # Create hypothesis summary
        hypothesis_summary = create_hypothesis_summary(mrt_results, vviq2_results)
        
        # Save results and analysis datasets
        save_results(mrt_results, vviq2_results, hypothesis_summary, acc_data, rt_data, vviq2_merged)
        
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        print(f"MRT results: {len(mrt_results)} rows")
        print(f"VVIQ2 results: {len(vviq2_results)} rows")
        print(f"Hypothesis summary: {len(hypothesis_summary)} hypotheses")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
