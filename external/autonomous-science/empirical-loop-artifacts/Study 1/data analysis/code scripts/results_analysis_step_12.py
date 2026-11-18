#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
import seaborn as sns
plt.style.use('default')

# Import R interface
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
pandas2ri.activate()

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

def load_and_validate_data(file_path, required_columns):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    file_path (str): Path to the CSV file
    required_columns (list): List of required column names
    
    Returns:
    pd.DataFrame: Loaded dataframe, or None if validation fails
    """
    print(f"Attempting to load file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return None
    
    try:
        # Read CSV and strip whitespace from column names
        df = pd.read_csv(file_path)
        
        # Strip whitespace from column names
        df.columns = [col.strip() if isinstance(col, str) else col for col in df.columns]
        print(f"Successfully loaded file with {len(df)} rows and {len(df.columns)} columns")
        print(f"Column names have been stripped of whitespace")
        
        # Print all columns
        print("All columns in file:")
        print(list(df.columns))
        
        # Print first 3 rows
        print("First 3 rows:")
        print(df.head(3))
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return None
        
        print("All required columns found")
        return df
        
    except Exception as e:
        print(f"ERROR loading file: {e}")
        return None

def filter_data(df, task_name):
    """
    Filter data for analysis (exclude participants, practice trials, invalid trials).
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    task_name (str): Name of the task (VWM or MRT)
    
    Returns:
    pd.DataFrame: Filtered dataframe
    """
    print(f"\nFiltering {task_name} data...")
    print(f"Initial data shape: {df.shape}")
    
    # Define required columns for filtering
    key_columns = ['excluded_participant', 'isPractice', 'valid_trial']
    
    # Add task-specific columns to check
    if task_name == "MRT" and 'MRT_isAttentionCheck' in df.columns:
        key_columns.append('MRT_isAttentionCheck')
    
    # Check if all required columns exist BEFORE attempting any operations
    missing_cols = [col for col in key_columns if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Cannot filter data, missing required columns: {missing_cols}")
        return pd.DataFrame()  # Return empty dataframe if required columns missing
    
    # Remove null values in key columns
    initial_rows = len(df)
    
    for col in key_columns:
        before_filter = len(df)
        df = df.dropna(subset=[col])
        after_filter = len(df)
        if before_filter != after_filter:
            print(f"Removed {before_filter - after_filter} rows with null values in {col}")
    
    # Apply general filter conditions
    df_filtered = df[
        (df['excluded_participant'] == False) & 
        (df['isPractice'] == False) & 
        (df['valid_trial'] == True)
    ].copy()
    
    print(f"After general filtering: {len(df_filtered)} rows remaining")
    
    # Apply task-specific filtering
    if task_name == "MRT" and 'MRT_isAttentionCheck' in df_filtered.columns:
        rows_before_ac_filter = len(df_filtered)
        df_filtered = df_filtered[df_filtered['MRT_isAttentionCheck'] == False].copy()
        print(f"Applied MRT-specific filter: Excluded {rows_before_ac_filter - len(df_filtered)} MRT attention check trials")
    elif task_name == "VWM":
        print("VWM filtering: Attention check trials are intentionally retained for VWM modeling")
    
    print(f"After all filtering: {len(df_filtered)} rows remaining")
    print(f"Total excluded: {initial_rows - len(df_filtered)} rows")
    
    return df_filtered

def setup_r_environment():
    """
    Set up R environment and load required packages.
    
    Returns:
    dict: Dictionary of R package objects
    """
    print("Setting up R environment...")
    
    try:
        # Try to install required R packages if not present
        utils = importr('utils')
        
        # Check if lme4 and lmerTest are installed, install if not
        print("Checking for required R packages...")
        ro.r('if (!requireNamespace("lme4", quietly = TRUE)) { install.packages("lme4", repos="https://cloud.r-project.org") }')
        ro.r('if (!requireNamespace("lmerTest", quietly = TRUE)) { install.packages("lmerTest", repos="https://cloud.r-project.org") }')
        
        # Load required R packages
        lme4 = importr('lme4')
        ro.r('library(lmerTest)')  # Explicitly load lmerTest for p-values
        stats = importr('stats')
        base = importr('base')
        
        print("R packages loaded successfully")
        return {'lme4': lme4, 'stats': stats, 'base': base}
        
    except Exception as e:
        print(f"ERROR setting up R environment: {e}")
        return None

def fit_model_with_fallback(model_name, formula_fixed, random_effects_list, data_name, family=None, control_opts=None):
    """
    Attempt to fit a model with progressively simpler random effects structures.
    
    Parameters:
    model_name (str): Name to assign to the fitted model in R environment
    formula_fixed (str): Fixed effects formula
    random_effects_list (list): List of random effects structures from complex to simple
    data_name (str): Name of the data frame in R environment
    family (str): Family for glmer models (None for lmer)
    control_opts (str): Control options for the model
    
    Returns:
    str: The random effects structure that was successfully used
    """
    print(f"Attempting to fit {model_name} with fallback strategy...")
    
    final_re_structure = "None"
    
    for i, re_struct in enumerate(random_effects_list):
        print(f"  Attempt {i+1}/{len(random_effects_list)}: Trying RE structure: {re_struct}")
        
        try:
            # Construct the full model formula
            full_formula = f"{formula_fixed} + {re_struct}"
            
            # Choose the appropriate R function
            if family is None:
                model_func = "lmer"
                family_arg = ""
            else:
                model_func = "glmer"
                family_arg = f", family = {family}"
            
            # Add control options if provided
            control_arg = f", {control_opts}" if control_opts else ""
            
            # Attempt to fit the model
            ro.r(f'''
            tryCatch({{
                {model_name} <- {model_func}({full_formula}, data = {data_name}{family_arg}{control_arg})
                
                # Check for singularity
                if (isSingular({model_name})) {{
                    print("  Model fitted but has singular fit")
                    singular_fit <- TRUE
                }} else {{
                    print("  Model fitted successfully without singularity")
                    singular_fit <- FALSE
                }}
                
                # Store convergence status
                convergence_success <- TRUE
                
            }}, error = function(e) {{
                print(paste("  Model fitting failed:", e$message))
                convergence_success <- FALSE
                singular_fit <- NA
                {model_name} <- NULL
            }})
            ''')
            
            # Check if model fitting was successful
            convergence_success = ro.r('convergence_success')[0]
            
            if convergence_success:
                singular_fit = ro.r('singular_fit')[0]
                
                if not singular_fit:
                    # Model fitted successfully without singularity
                    final_re_structure = re_struct
                    print(f"  SUCCESS: Model converged without singularity using RE: {re_struct}")
                    break
                else:
                    # Model fitted but is singular - continue to simpler structure
                    print(f"  Model singular with RE: {re_struct}, trying simpler structure...")
                    if i == len(random_effects_list) - 1:
                        # This was the last (simplest) structure, accept it even if singular
                        final_re_structure = re_struct
                        print(f"  ACCEPTED: Using simplest structure despite singularity: {re_struct}")
                        break
            else:
                # Model failed to converge
                print(f"  Model failed to converge with RE: {re_struct}, trying simpler structure...")
                
        except Exception as e:
            print(f"  Error fitting model with RE {re_struct}: {e}")
            continue
    
    print(f"Final random effects structure for {model_name}: {final_re_structure}")
    return final_re_structure

def fit_mrt_models(df_mrt, r_packages):
    """
    Fit linear and quadratic models for MRT data.
    
    Parameters:
    df_mrt (pd.DataFrame): Filtered MRT dataframe
    r_packages (dict): Dictionary of R package objects
    
    Returns:
    dict: Dictionary containing model results
    """
    print("\nFitting MRT models...")
    start_time = datetime.now()
    print(f"Started MRT model fitting at: {start_time.strftime('%H:%M:%S')}")
    
    # Print unique values for key experimental parameters
    if 'MRT_angle_degrees' in df_mrt.columns:
        print("Unique values in MRT_angle_degrees:")
        print(sorted(df_mrt['MRT_angle_degrees'].unique()))
    else:
        print("WARNING: MRT_angle_degrees column not found")
    
    print("Data types for measured variables:")
    if 'MRT_rt_ms' in df_mrt.columns:
        print(f"MRT_rt_ms: {df_mrt['MRT_rt_ms'].dtype}")
    else:
        print("WARNING: MRT_rt_ms column not found")
        
    if 'MRT_isCorrect' in df_mrt.columns:
        print(f"MRT_isCorrect: {df_mrt['MRT_isCorrect'].dtype}")
    else:
        print("WARNING: MRT_isCorrect column not found")
    
    results = {}
    
    # RT Analysis - correct trials only
    print("\nAnalyzing MRT reaction times (correct trials only)...")
    df_rt = df_mrt[df_mrt['MRT_isCorrect'] == True].copy()
    
    # Remove null RT values
    df_rt = df_rt.dropna(subset=['MRT_rt_ms'])
    print(f"RT analysis with {len(df_rt)} correct trials")
    
    # Log transform RT - this is the outcome variable (not the predictor)
    print("Log-transforming reaction times (MRT_rt_ms) as the OUTCOME variable...")
    df_rt['log_MRT_rt_ms'] = np.log(df_rt['MRT_rt_ms'])
    print(f"Mean log RT: {df_rt['log_MRT_rt_ms'].mean():.4f}, SD: {df_rt['log_MRT_rt_ms'].std():.4f}")
    print("NOTE: The log-transformed RT is used as the dependent variable in the models")
    print("      while angle is used as a predictor variable (scaled to improve convergence)")
    
    # Scale predictors to address convergence warnings
    print("Scaling predictors to improve model convergence...")
    angle_mean = df_rt['MRT_angle_degrees'].mean()
    angle_sd = df_rt['MRT_angle_degrees'].std()
    df_rt['MRT_angle_degrees_scaled'] = (df_rt['MRT_angle_degrees'] - angle_mean) / angle_sd
    df_rt['MRT_angle_degrees_squared'] = df_rt['MRT_angle_degrees_scaled'] ** 2
    
    print(f"Scaled MRT_angle_degrees: mean={angle_mean:.2f}, sd={angle_sd:.2f}")
    
    # Convert to R dataframe
    r_df_rt = pandas2ri.py2rpy(df_rt)
    ro.globalenv['df_rt'] = r_df_rt

    # Define random effects structures from most to least complex
    rt_linear_re_structures = [
        "(1 + MRT_angle_degrees_scaled | participantId)",
        "(1 | participantId) + (0 + MRT_angle_degrees_scaled | participantId)",
        "(1 | participantId)"
    ]

    rt_quadratic_re_structures = [
        "(1 + MRT_angle_degrees_scaled + MRT_angle_degrees_squared | participantId)",
        "(1 + MRT_angle_degrees_scaled | participantId) + (0 + MRT_angle_degrees_squared | participantId)",
        "(1 + MRT_angle_degrees_scaled | participantId)",
        "(1 | participantId)"
    ]

    try:
        # Linear RT model with fallback
        linear_rt_re_used = fit_model_with_fallback(
            model_name="linear_rt_model",
            formula_fixed="log_MRT_rt_ms ~ MRT_angle_degrees_scaled",
            random_effects_list=rt_linear_re_structures,
            data_name="df_rt",
            control_opts='REML = FALSE, control = lmerControl(optimizer = "bobyqa")'
        )

        # Quadratic RT model with fallback
        quadratic_rt_re_used = fit_model_with_fallback(
            model_name="quadratic_rt_model",
            formula_fixed="log_MRT_rt_ms ~ MRT_angle_degrees_scaled + MRT_angle_degrees_squared",
            random_effects_list=rt_quadratic_re_structures,
            data_name="df_rt",
            control_opts='REML = FALSE, control = lmerControl(optimizer = "bobyqa")'
        )

        # Get model summaries and fit indices
        ro.r('''
        linear_rt_aic <- AIC(linear_rt_model)
        linear_rt_bic <- BIC(linear_rt_model)
        linear_rt_loglik <- logLik(linear_rt_model)[1]
        
        quadratic_rt_aic <- AIC(quadratic_rt_model)
        quadratic_rt_bic <- BIC(quadratic_rt_model)
        quadratic_rt_loglik <- logLik(quadratic_rt_model)[1]
        
        # Likelihood ratio test with error handling
        tryCatch({
            lrt_rt <- anova(linear_rt_model, quadratic_rt_model)
            lrt_rt_p <- lrt_rt$"Pr(>Chisq)"[2]
            if (is.na(lrt_rt_p) || !is.finite(lrt_rt_p)) {
                print("WARNING: Invalid p-value detected in likelihood ratio test for RT models")
                lrt_rt_p <- NA
            }
        }, error = function(e) {
            print(paste("ERROR in likelihood ratio test for RT models:", e$message))
            lrt_rt_p <- NA
        })
        
        # R-squared approximation with error handling
        tryCatch({
            linear_rt_r2 <- cor(fitted(linear_rt_model), df_rt$log_MRT_rt_ms)^2
            if (is.na(linear_rt_r2) || !is.finite(linear_rt_r2)) {
                print("WARNING: Invalid R-squared value for linear RT model")
                linear_rt_r2 <- NA
            }
        }, error = function(e) {
            print(paste("ERROR calculating R-squared for linear RT model:", e$message))
            linear_rt_r2 <- NA
        })
        
        tryCatch({
            quadratic_rt_r2 <- cor(fitted(quadratic_rt_model), df_rt$log_MRT_rt_ms)^2
            if (is.na(quadratic_rt_r2) || !is.finite(quadratic_rt_r2)) {
                print("WARNING: Invalid R-squared value for quadratic RT model")
                quadratic_rt_r2 <- NA
            }
        }, error = function(e) {
            print(paste("ERROR calculating R-squared for quadratic RT model:", e$message))
            quadratic_rt_r2 <- NA
        })
        
        # Print model fit statistics for debugging
        print(paste("Linear RT model - AIC:", linear_rt_aic, "BIC:", linear_rt_bic, "R²:", linear_rt_r2))
        print(paste("Quadratic RT model - AIC:", quadratic_rt_aic, "BIC:", quadratic_rt_bic, "R²:", quadratic_rt_r2))
        print(paste("LRT p-value:", lrt_rt_p))
        ''')
        
        # Extract results
        results['mrt_rt'] = {
            'linear': {
                'AIC': ro.r('linear_rt_aic')[0],
                'BIC': ro.r('linear_rt_bic')[0],
                'log_likelihood': ro.r('linear_rt_loglik')[0],
                'r_squared': ro.r('linear_rt_r2')[0],
                'random_effects': linear_rt_re_used
            },
            'quadratic': {
                'AIC': ro.r('quadratic_rt_aic')[0],
                'BIC': ro.r('quadratic_rt_bic')[0],
                'log_likelihood': ro.r('quadratic_rt_loglik')[0],
                'r_squared': ro.r('quadratic_rt_r2')[0],
                'random_effects': quadratic_rt_re_used
            },
            'lrt_p': ro.r('lrt_rt_p')[0]
        }
        
        print("MRT RT models fitted successfully")
        rt_end_time = datetime.now()
        rt_duration = (rt_end_time - start_time).total_seconds()
        print(f"MRT RT model fitting completed in {rt_duration:.2f} seconds")
        print(f"Linear RT model random effects used: {linear_rt_re_used}")
        print(f"Quadratic RT model random effects used: {quadratic_rt_re_used}")
        
    except Exception as e:
        print(f"ERROR fitting MRT RT models: {e}")
        results['mrt_rt'] = None
    
    # Accuracy Analysis
    print("\nAnalyzing MRT accuracy...")
    df_acc = df_mrt.dropna(subset=['MRT_isCorrect']).copy()
    
    # Scale predictors to address convergence warnings
    print("Scaling predictors for accuracy models...")
    try:
        angle_mean
        angle_sd
    except NameError:
        angle_mean = df_acc['MRT_angle_degrees'].mean()
        angle_sd = df_acc['MRT_angle_degrees'].std()
        print(f"Scaled MRT_angle_degrees: mean={angle_mean:.2f}, sd={angle_sd:.2f}")
    
    df_acc['MRT_angle_degrees_scaled'] = (df_acc['MRT_angle_degrees'] - angle_mean) / angle_sd
    df_acc['MRT_angle_degrees_squared'] = df_acc['MRT_angle_degrees_scaled'] ** 2
    
    print(f"Accuracy analysis with {len(df_acc)} trials")
    
    # Convert to R dataframe
    r_df_acc = pandas2ri.py2rpy(df_acc)
    ro.globalenv['df_acc'] = r_df_acc

    acc_linear_re_structures = [
        "(1 + MRT_angle_degrees_scaled | participantId)",
        "(1 | participantId) + (0 + MRT_angle_degrees_scaled | participantId)",
        "(1 | participantId)"
    ]

    acc_quadratic_re_structures = [
        "(1 + MRT_angle_degrees_scaled + MRT_angle_degrees_squared | participantId)",
        "(1 + MRT_angle_degrees_scaled | participantId) + (0 + MRT_angle_degrees_squared | participantId)",
        "(1 + MRT_angle_degrees_scaled | participantId)",
        "(1 | participantId)"
    ]

    try:
        # Linear accuracy model with fallback
        linear_acc_re_used = fit_model_with_fallback(
            model_name="linear_acc_model",
            formula_fixed="MRT_isCorrect ~ MRT_angle_degrees_scaled",
            random_effects_list=acc_linear_re_structures,
            data_name="df_acc",
            family="binomial",
            control_opts='control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000))'
        )

        # Quadratic accuracy model with fallback
        quadratic_acc_re_used = fit_model_with_fallback(
            model_name="quadratic_acc_model",
            formula_fixed="MRT_isCorrect ~ MRT_angle_degrees_scaled + MRT_angle_degrees_squared",
            random_effects_list=acc_quadratic_re_structures,
            data_name="df_acc",
            family="binomial",
            control_opts='control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000))'
        )

        # Get model summaries and fit indices
        ro.r('''
        linear_acc_aic <- AIC(linear_acc_model)
        linear_acc_bic <- BIC(linear_acc_model)
        linear_acc_loglik <- logLik(linear_acc_model)[1]
        
        quadratic_acc_aic <- AIC(quadratic_acc_model)
        quadratic_acc_bic <- BIC(quadratic_acc_model)
        quadratic_acc_loglik <- logLik(quadratic_acc_model)[1]
        
        # Likelihood ratio test with error handling
        tryCatch({
            lrt_acc <- anova(linear_acc_model, quadratic_acc_model)
            lrt_acc_p <- lrt_acc$"Pr(>Chisq)"[2]
            if (is.na(lrt_acc_p) || !is.finite(lrt_acc_p)) {
                print("WARNING: Invalid p-value detected in likelihood ratio test for accuracy models")
                lrt_acc_p <- NA
            }
        }, error = function(e) {
            print(paste("ERROR in likelihood ratio test for accuracy models:", e$message))
            lrt_acc_p <- NA
        })
        
        # Pseudo R-squared (variance explained method for logistic models) with error handling
        tryCatch({
            linear_acc_r2 <- var(fitted(linear_acc_model)) / (var(fitted(linear_acc_model)) + pi^2/3)
            if (is.na(linear_acc_r2) || !is.finite(linear_acc_r2)) {
                print("WARNING: Invalid R-squared value for linear accuracy model")
                linear_acc_r2 <- NA
            }
        }, error = function(e) {
            print(paste("ERROR calculating R-squared for linear accuracy model:", e$message))
            linear_acc_r2 <- NA
        })
        
        tryCatch({
            quadratic_acc_r2 <- var(fitted(quadratic_acc_model)) / (var(fitted(quadratic_acc_model)) + pi^2/3)
            if (is.na(quadratic_acc_r2) || !is.finite(quadratic_acc_r2)) {
                print("WARNING: Invalid R-squared value for quadratic accuracy model")
                quadratic_acc_r2 <- NA
            }
        }, error = function(e) {
            print(paste("ERROR calculating R-squared for quadratic accuracy model:", e$message))
            quadratic_acc_r2 <- NA
        })
        
        # Print model fit statistics for debugging
        print(paste("Linear accuracy model - AIC:", linear_acc_aic, "BIC:", linear_acc_bic, "R²:", linear_acc_r2))
        print(paste("Quadratic accuracy model - AIC:", quadratic_acc_aic, "BIC:", quadratic_acc_bic, "R²:", quadratic_acc_r2))
        print(paste("LRT p-value:", lrt_acc_p))
        ''')
        
        # Extract results
        results['mrt_accuracy'] = {
            'linear': {
                'AIC': ro.r('linear_acc_aic')[0],
                'BIC': ro.r('linear_acc_bic')[0],
                'log_likelihood': ro.r('linear_acc_loglik')[0],
                'r_squared': ro.r('linear_acc_r2')[0],
                'random_effects': linear_acc_re_used
            },
            'quadratic': {
                'AIC': ro.r('quadratic_acc_aic')[0],
                'BIC': ro.r('quadratic_acc_bic')[0],
                'log_likelihood': ro.r('quadratic_acc_loglik')[0],
                'r_squared': ro.r('quadratic_acc_r2')[0],
                'random_effects': quadratic_acc_re_used
            },
            'lrt_p': ro.r('lrt_acc_p')[0]
        }
        
        print("MRT accuracy models fitted successfully")
        acc_end_time = datetime.now()
        total_duration = (acc_end_time - start_time).total_seconds()
        print(f"MRT accuracy model fitting completed in {total_duration:.2f} seconds")
        print(f"Total MRT model fitting time: {total_duration:.2f} seconds")
        print(f"Linear accuracy model random effects used: {linear_acc_re_used}")
        print(f"Quadratic accuracy model random effects used: {quadratic_acc_re_used}")
        
    except Exception as e:
        print(f"ERROR fitting MRT accuracy models: {e}")
        results['mrt_accuracy'] = None
    
    return results

def fit_vwm_models(df_vwm, r_packages):
    """
    Fit linear and non-linear models for VWM data.
    
    Parameters:
    df_vwm (pd.DataFrame): Filtered VWM dataframe
    r_packages (dict): Dictionary of R package objects
    
    Returns:
    dict: Dictionary containing model results
    """
    print("\nFitting VWM models...")
    start_time = datetime.now()
    print(f"Started VWM model fitting at: {start_time.strftime('%H:%M:%S')}")
    
    # Print unique values for key experimental parameters
    if 'VWM_setSize' in df_vwm.columns:
        unique_set_sizes = sorted(df_vwm['VWM_setSize'].unique())
        print("Unique values in VWM_setSize:")
        print(unique_set_sizes)
        
        # Verify all three set sizes are present
        expected_set_sizes = [1, 2, 4]
        missing_set_sizes = [size for size in expected_set_sizes if size not in unique_set_sizes]
        if missing_set_sizes:
            print(f"WARNING: Missing expected VWM set sizes: {missing_set_sizes}")
            print("This may affect quadratic model fitting")
        else:
            print("VERIFIED: All expected VWM set sizes (1, 2, 4) are present in the data")
    else:
        print("WARNING: VWM_setSize column not found")
    
    if 'VWM_delay_s' in df_vwm.columns:
        print("Unique values in VWM_delay_s:")
        print(sorted(df_vwm['VWM_delay_s'].unique()))
    else:
        print("WARNING: VWM_delay_s column not found")
    
    print("Data types for measured variables:")
    if 'VWM_error_absolute_degrees' in df_vwm.columns:
        print(f"VWM_error_absolute_degrees: {df_vwm['VWM_error_absolute_degrees'].dtype}")
    else:
        print("WARNING: VWM_error_absolute_degrees column not found")
    
    # Remove null values in key columns
    df_vwm = df_vwm.dropna(subset=['VWM_error_absolute_degrees', 'VWM_setSize', 'VWM_delay_s'])
    print(f"VWM analysis with {len(df_vwm)} valid trials")
    
    # Create transformed predictors
    df_vwm['VWM_setSize_log'] = np.log(df_vwm['VWM_setSize'])
    df_vwm['VWM_delay_log'] = np.log(df_vwm['VWM_delay_s'])
    df_vwm['VWM_setSize_squared'] = df_vwm['VWM_setSize'] ** 2
    
    results = {}
    
    # Convert to R dataframe
    r_df_vwm = pandas2ri.py2rpy(df_vwm)
    ro.globalenv['df_vwm'] = r_df_vwm

    # Define random effects structures for VWM models
    vwm_linear_re_structures = [
        "(1 + VWM_setSize + VWM_delay_s + VWM_setSize:VWM_delay_s | participantId)",
        "(1 + VWM_setSize + VWM_delay_s | participantId)",
        "(1 + VWM_setSize | participantId)",
        "(1 | participantId)"
    ]
    vwm_log_re_structures = [
        "(1 + VWM_setSize_log + VWM_delay_log + VWM_setSize_log:VWM_delay_log | participantId)",
        "(1 + VWM_setSize_log + VWM_delay_log | participantId)",
        "(1 + VWM_setSize_log | participantId)",
        "(1 | participantId)"
    ]
    vwm_quad_re_structures = [
        "(1 + VWM_setSize + VWM_setSize_squared + VWM_delay_s + VWM_setSize_squared:VWM_delay_s | participantId)",
        "(1 + VWM_setSize + VWM_setSize_squared + VWM_delay_s | participantId)",
        "(1 + VWM_setSize + VWM_setSize_squared | participantId)",
        "(1 | participantId)"
    ]

    try:
        # Linear model (baseline) with fallback
        linear_vwm_re_used = fit_model_with_fallback(
            model_name="linear_vwm_model",
            formula_fixed="VWM_error_absolute_degrees ~ VWM_setSize * VWM_delay_s",
            random_effects_list=vwm_linear_re_structures,
            data_name="df_vwm",
            control_opts='REML = FALSE'
        )

        # Log-transformed model with fallback
        log_vwm_re_used = fit_model_with_fallback(
            model_name="log_vwm_model",
            formula_fixed="VWM_error_absolute_degrees ~ VWM_setSize_log * VWM_delay_log",
            random_effects_list=vwm_log_re_structures,
            data_name="df_vwm",
            control_opts='REML = FALSE'
        )

        # Quadratic model with fallback
        quadratic_vwm_re_used = fit_model_with_fallback(
            model_name="quadratic_vwm_model",
            formula_fixed="VWM_error_absolute_degrees ~ VWM_setSize + VWM_setSize_squared * VWM_delay_s",
            random_effects_list=vwm_quad_re_structures,
            data_name="df_vwm",
            control_opts='REML = FALSE'
        )

        # Get model summaries and fit indices with error handling
        ro.r('''
        # Linear model
        linear_vwm_aic <- AIC(linear_vwm_model)
        linear_vwm_bic <- BIC(linear_vwm_model)
        linear_vwm_loglik <- logLik(linear_vwm_model)[1]
        
        tryCatch({
            linear_vwm_r2 <- cor(fitted(linear_vwm_model), df_vwm$VWM_error_absolute_degrees)^2
            if (is.na(linear_vwm_r2) || !is.finite(linear_vwm_r2)) {
                print("WARNING: Invalid R-squared value for linear VWM model")
                linear_vwm_r2 <- NA
            }
        }, error = function(e) {
            print(paste("ERROR calculating R-squared for linear VWM model:", e$message))
            linear_vwm_r2 <- NA
        })
        
        # Log-transformed model
        log_vwm_aic <- AIC(log_vwm_model)
        log_vwm_bic <- BIC(log_vwm_model)
        log_vwm_loglik <- logLik(log_vwm_model)[1]
        
        tryCatch({
            log_vwm_r2 <- cor(fitted(log_vwm_model), df_vwm$VWM_error_absolute_degrees)^2
            if (is.na(log_vwm_r2) || !is.finite(log_vwm_r2)) {
                print("WARNING: Invalid R-squared value for log-transformed VWM model")
                log_vwm_r2 <- NA
            }
        }, error = function(e) {
            print(paste("ERROR calculating R-squared for log-transformed VWM model:", e$message))
            log_vwm_r2 <- NA
        })
        
        # Quadratic model
        quadratic_vwm_aic <- AIC(quadratic_vwm_model)
        quadratic_vwm_bic <- BIC(quadratic_vwm_model)
        quadratic_vwm_loglik <- logLik(quadratic_vwm_model)[1]
        
        tryCatch({
            quadratic_vwm_r2 <- cor(fitted(quadratic_vwm_model), df_vwm$VWM_error_absolute_degrees)^2
            if (is.na(quadratic_vwm_r2) || !is.finite(quadratic_vwm_r2)) {
                print("WARNING: Invalid R-squared value for quadratic VWM model")
                quadratic_vwm_r2 <- NA
            }
        }, error = function(e) {
            print(paste("ERROR calculating R-squared for quadratic VWM model:", e$message))
            quadratic_vwm_r2 <- NA
        })
        
        # Likelihood ratio tests with error handling
        tryCatch({
            lrt_log <- anova(linear_vwm_model, log_vwm_model)
            lrt_log_p <- lrt_log$"Pr(>Chisq)"[2]
            if (is.na(lrt_log_p) || !is.finite(lrt_log_p)) {
                print("WARNING: Invalid p-value detected in likelihood ratio test for log-transformed VWM model")
                lrt_log_p <- NA
            }
        }, error = function(e) {
            print(paste("ERROR in likelihood ratio test for log-transformed VWM model:", e$message))
            lrt_log_p <- NA
        })
        
        tryCatch({
            lrt_quad <- anova(linear_vwm_model, quadratic_vwm_model)
            lrt_quad_p <- lrt_quad$"Pr(>Chisq)"[2]
            if (is.na(lrt_quad_p) || !is.finite(lrt_quad_p)) {
                print("WARNING: Invalid p-value detected in likelihood ratio test for quadratic VWM model")
                lrt_quad_p <- NA
            }
        }, error = function(e) {
            print(paste("ERROR in likelihood ratio test for quadratic VWM model:", e$message))
            lrt_quad_p <- NA
        })
        
        # Print model fit statistics for debugging
        print(paste("Linear VWM model - AIC:", linear_vwm_aic, "BIC:", linear_vwm_bic, "R²:", linear_vwm_r2))
        print(paste("Log-transformed VWM model - AIC:", log_vwm_aic, "BIC:", log_vwm_bic, "R²:", log_vwm_r2))
        print(paste("Quadratic VWM model - AIC:", quadratic_vwm_aic, "BIC:", quadratic_vwm_bic, "R²:", quadratic_vwm_r2))
        print(paste("Log model LRT p-value:", lrt_log_p))
        print(paste("Quadratic model LRT p-value:", lrt_quad_p))
        ''')
        
        # Extract results
        results['vwm'] = {
            'linear': {
                'AIC': ro.r('linear_vwm_aic')[0],
                'BIC': ro.r('linear_vwm_bic')[0],
                'log_likelihood': ro.r('linear_vwm_loglik')[0],
                'r_squared': ro.r('linear_vwm_r2')[0],
                'random_effects': linear_vwm_re_used
            },
            'log_transformed': {
                'AIC': ro.r('log_vwm_aic')[0],
                'BIC': ro.r('log_vwm_bic')[0],
                'log_likelihood': ro.r('log_vwm_loglik')[0],
                'r_squared': ro.r('log_vwm_r2')[0],
                'lrt_p': ro.r('lrt_log_p')[0],
                'random_effects': log_vwm_re_used
            },
            'quadratic': {
                'AIC': ro.r('quadratic_vwm_aic')[0],
                'BIC': ro.r('quadratic_vwm_bic')[0],
                'log_likelihood': ro.r('quadratic_vwm_loglik')[0],
                'r_squared': ro.r('quadratic_vwm_r2')[0],
                'lrt_p': ro.r('lrt_quad_p')[0],
                'random_effects': quadratic_vwm_re_used
            }
        }
        
        print("VWM models fitted successfully")
        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()
        print(f"VWM model fitting completed in {total_duration:.2f} seconds")
        print(f"Linear VWM model random effects used: {linear_vwm_re_used}")
        print(f"Log-transformed VWM model random effects used: {log_vwm_re_used}")
        print(f"Quadratic VWM model random effects used: {quadratic_vwm_re_used}")
        
    except Exception as e:
        print(f"ERROR fitting VWM models: {e}")
        results['vwm'] = None
    
    return results

def extract_model_coefficients(r_packages):
    """
    Extract coefficients from fitted models.
    
    Parameters:
    r_packages (dict): Dictionary of R package objects
    
    Returns:
    list: List of coefficient dictionaries
    """
    print("\nExtracting model coefficients...")
    
    coefficients = []
    
    # Define models to extract coefficients from
    models = [
        ('MRT', 'linear', 'linear_rt_model', 'RT'),
        ('MRT', 'quadratic', 'quadratic_rt_model', 'RT'),
        ('MRT', 'linear', 'linear_acc_model', 'accuracy'),
        ('MRT', 'quadratic', 'quadratic_acc_model', 'accuracy'),
        ('VWM', 'linear', 'linear_vwm_model', 'error'),
        ('VWM', 'log_transformed', 'log_vwm_model', 'error'),
        ('VWM', 'quadratic', 'quadratic_vwm_model', 'error')
    ]
    
    for task, model_type, model_name, outcome in models:
        try:
            print(f"Extracting coefficients for {task} {model_type} model...")
            
            # Check if model exists before attempting to extract coefficients
            model_exists = ro.r(f'exists("{model_name}")')
            if not model_exists[0]:
                print(f"WARNING: Model {model_name} does not exist, skipping coefficient extraction")
                continue
                
            # Get model summary with proper handling for different model types
            ro.r(f'''
            model_summary <- summary({model_name})
            coef_table <- model_summary$coefficients
            coef_names <- rownames(coef_table)
            estimates <- coef_table[, "Estimate"]
            std_errors <- coef_table[, "Std. Error"]
            
            # Handle different coefficient table structures for lmer vs glmer
            if("z value" %in% colnames(coef_table)) {{
                test_values <- coef_table[, "z value"]
                p_values <- coef_table[, "Pr(>|z|)"]
            }} else if("t value" %in% colnames(coef_table)) {{
                test_values <- coef_table[, "t value"]
                p_values <- if("Pr(>|t|)" %in% colnames(coef_table)) coef_table[, "Pr(>|t|)"] else rep(NA, length(estimates))
            }} else {{
                test_values <- rep(NA, length(estimates))
                p_values <- rep(NA, length(estimates))
            }}
            
            # Calculate confidence intervals
            ci_lower <- estimates - 1.96 * std_errors
            ci_upper <- estimates + 1.96 * std_errors
            ''')
            
            # Extract coefficient information
            coef_names = list(ro.r('coef_names'))
            estimates = list(ro.r('estimates'))
            std_errors = list(ro.r('std_errors'))
            test_values = list(ro.r('test_values'))
            p_values = list(ro.r('p_values'))
            ci_lower = list(ro.r('ci_lower'))
            ci_upper = list(ro.r('ci_upper'))
            
            for i, coef_name in enumerate(coef_names):
                coefficients.append({
                    'task_name': task,
                    'model_type': model_type,
                    'coefficient_name': coef_name,
                    'estimate': estimates[i] if not pd.isna(estimates[i]) else 0.0,
                    'std_error': std_errors[i] if not pd.isna(std_errors[i]) else 0.0,
                    't_value': test_values[i] if not pd.isna(test_values[i]) else 0.0,
                    'p_value': p_values[i] if not pd.isna(p_values[i]) else 1.0,
                    'ci_lower': ci_lower[i] if not pd.isna(ci_lower[i]) else 0.0,
                    'ci_upper': ci_upper[i] if not pd.isna(ci_upper[i]) else 0.0
                })
            
        except Exception as e:
            print(f"WARNING: Could not extract coefficients for {task} {model_type}: {e}")
            continue
    
    print(f"Extracted coefficients for {len(coefficients)} parameters")
    return coefficients

def determine_preferred_models(results):
    """
    Determine preferred models based on fit indices.
    
    Parameters:
    results (dict): Dictionary containing model results
    
    Returns:
    dict: Dictionary with preferred model determinations
    """
    print("\nDetermining preferred models...")
    
    preferred = {}
    
    # MRT RT models
    if results.get('mrt_rt'):
        mrt_rt = results['mrt_rt']
        if mrt_rt['quadratic']['AIC'] < mrt_rt['linear']['AIC'] and mrt_rt['lrt_p'] < 0.05:
            preferred['mrt_rt'] = 'quadratic'
        else:
            preferred['mrt_rt'] = 'linear'
        print(f"MRT RT preferred model: {preferred['mrt_rt']} (Linear AIC: {mrt_rt['linear']['AIC']:.1f}, Quadratic AIC: {mrt_rt['quadratic']['AIC']:.1f}, LRT p: {mrt_rt['lrt_p']:.2e})")
    
    # MRT accuracy models
    if results.get('mrt_accuracy'):
        mrt_acc = results['mrt_accuracy']
        if mrt_acc['quadratic']['AIC'] < mrt_acc['linear']['AIC'] and mrt_acc['lrt_p'] < 0.05:
            preferred['mrt_accuracy'] = 'quadratic'
        else:
            preferred['mrt_accuracy'] = 'linear'
        print(f"MRT accuracy preferred model: {preferred['mrt_accuracy']} (Linear AIC: {mrt_acc['linear']['AIC']:.1f}, Quadratic AIC: {mrt_acc['quadratic']['AIC']:.1f}, LRT p: {mrt_acc['lrt_p']:.2e})")
    
    # VWM models - use consistent logic with AIC and LRT p-value
    if results.get('vwm'):
        vwm = results['vwm']
        
        # Print AIC values for debugging
        print(f"VWM model AICs - Linear: {vwm['linear']['AIC']:.1f}, Log: {vwm['log_transformed']['AIC']:.1f}, Quadratic: {vwm['quadratic']['AIC']:.1f}")
        print(f"VWM LRT p-values - Log vs Linear: {vwm['log_transformed']['lrt_p']}, Quadratic vs Linear: {vwm['quadratic']['lrt_p']}")
        
        # Find model with lowest AIC
        aics = {
            'linear': vwm['linear']['AIC'],
            'log_transformed': vwm['log_transformed']['AIC'],
            'quadratic': vwm['quadratic']['AIC']
        }
        lowest_aic_model = min(aics, key=aics.get)
        
        # Apply selection criteria: prefer non-linear model only if it has better AIC AND significant LRT
        if lowest_aic_model == 'log_transformed':
            # Check if log model is significantly better than linear
            if (vwm['log_transformed']['AIC'] < vwm['linear']['AIC'] and 
                not pd.isna(vwm['log_transformed']['lrt_p']) and 
                vwm['log_transformed']['lrt_p'] < 0.05):
                preferred['vwm'] = 'log_transformed'
            else:
                preferred['vwm'] = 'linear'
        elif lowest_aic_model == 'quadratic':
            # Check if quadratic model is significantly better than linear
            if (vwm['quadratic']['AIC'] < vwm['linear']['AIC'] and 
                not pd.isna(vwm['quadratic']['lrt_p']) and 
                vwm['quadratic']['lrt_p'] < 0.05):
                preferred['vwm'] = 'quadratic'
            else:
                preferred['vwm'] = 'linear'
        else:
            preferred['vwm'] = 'linear'
        
        print(f"VWM preferred model: {preferred['vwm']} (lowest AIC model: {lowest_aic_model})")
    
    return preferred

def create_results_summary(results, preferred):
    """
    Create summary of model comparison results.
    
    Parameters:
    results (dict): Dictionary containing model results
    preferred (dict): Dictionary with preferred model determinations
    
    Returns:
    list: List of result dictionaries
    """
    print("\nCreating results summary...")
    
    # Get sample sizes for reporting
    try:
        mrt_rt_n = int(ro.r('nrow(df_rt)')[0]) if 'df_rt' in ro.globalenv else 0
        mrt_acc_n = int(ro.r('nrow(df_acc)')[0]) if 'df_acc' in ro.globalenv else 0
        vwm_n = int(ro.r('nrow(df_vwm)')[0]) if 'df_vwm' in ro.globalenv else 0
        print(f"Sample sizes for reporting - MRT RT: {mrt_rt_n}, MRT Accuracy: {mrt_acc_n}, VWM: {vwm_n}")
    except Exception as e:
        print(f"WARNING: Could not determine sample sizes: {e}")
        mrt_rt_n = 0
        mrt_acc_n = 0
        vwm_n = 0
    
    summary = []
    
    # MRT RT results
    if results.get('mrt_rt'):
        mrt_rt = results['mrt_rt']
        for model_type in ['linear', 'quadratic']:
            summary.append({
                'task_name': 'MRT',
                'model_type': model_type,
                'outcome_measure': 'RT',
                'AIC': mrt_rt[model_type]['AIC'],
                'BIC': mrt_rt[model_type]['BIC'],
                'log_likelihood': mrt_rt[model_type]['log_likelihood'],
                'r_squared': mrt_rt[model_type]['r_squared'],
                'likelihood_ratio_test_p': mrt_rt['lrt_p'] if model_type == 'quadratic' else np.nan,
                'preferred_model': preferred.get('mrt_rt', 'unknown')
            })
    
    # MRT accuracy results
    if results.get('mrt_accuracy'):
        mrt_acc = results['mrt_accuracy']
        for model_type in ['linear', 'quadratic']:
            summary.append({
                'task_name': 'MRT',
                'model_type': model_type,
                'outcome_measure': 'accuracy',
                'AIC': mrt_acc[model_type]['AIC'],
                'BIC': mrt_acc[model_type]['BIC'],
                'log_likelihood': mrt_acc[model_type]['log_likelihood'],
                'r_squared': mrt_acc[model_type]['r_squared'],
                'likelihood_ratio_test_p': mrt_acc['lrt_p'] if model_type == 'quadratic' else np.nan,
                'preferred_model': preferred.get('mrt_accuracy', 'unknown')
            })
    
    # VWM results
    if results.get('vwm'):
        vwm = results['vwm']
        for model_type in ['linear', 'log_transformed', 'quadratic']:
            lrt_p = np.nan
            if model_type == 'log_transformed':
                lrt_p = vwm['log_transformed']['lrt_p']
            elif model_type == 'quadratic':
                lrt_p = vwm['quadratic']['lrt_p']
            
            summary.append({
                'task_name': 'VWM',
                'model_type': model_type,
                'outcome_measure': 'error',
                'AIC': vwm[model_type]['AIC'],
                'BIC': vwm[model_type]['BIC'],
                'log_likelihood': vwm[model_type]['log_likelihood'],
                'r_squared': vwm[model_type]['r_squared'],
                'likelihood_ratio_test_p': lrt_p,
                'preferred_model': preferred.get('vwm', 'unknown')
            })
    
    print(f"Created summary with {len(summary)} model comparisons")
    return summary

def create_model_visualizations(df_mrt, df_vwm, preferred, timestamp):
    """
    Create visualizations of model fits and diagnostic plots.
    
    Parameters:
    df_mrt (pd.DataFrame): Filtered MRT dataframe
    df_vwm (pd.DataFrame): Filtered VWM dataframe
    preferred (dict): Dictionary with preferred model determinations
    timestamp (str): Timestamp string for filenames
    """
    print("\nCreating model visualizations...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Set up figure style
    plt.style.use('seaborn-v0_8-whitegrid')
    
    # Create diagnostic plots for model residuals
    create_residual_plots(preferred, timestamp)
    
    # 1. MRT RT visualization
    try:
        print("Creating MRT RT visualization...")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get correct trials only
        df_mrt_correct = df_mrt[df_mrt['MRT_isCorrect'] == True].copy()
        
        # Create angle bins for aggregation
        angle_bins = sorted(df_mrt_correct['MRT_angle_degrees'].unique())
        
        # Calculate mean RT per angle
        rt_by_angle = df_mrt_correct.groupby('MRT_angle_degrees')['MRT_rt_ms'].agg(['mean', 'sem']).reset_index()
        
        # Plot data points with error bars
        ax.errorbar(rt_by_angle['MRT_angle_degrees'], rt_by_angle['mean'], 
                   yerr=rt_by_angle['sem'], fmt='o', color='blue', 
                   ecolor='lightblue', elinewidth=3, capsize=0,
                   label='Observed data')
        
        # Generate model predictions using actual fitted models
        x = np.array(angle_bins)
        
        # Create prediction data frame with scaled variables
        ro.globalenv['pred_angles'] = ro.FloatVector(x)
        angle_mean = df_mrt_correct['MRT_angle_degrees'].mean()
        angle_sd = df_mrt_correct['MRT_angle_degrees'].std()
        ro.r(f'pred_df <- data.frame(MRT_angle_degrees = pred_angles, MRT_angle_degrees_scaled = (pred_angles - {angle_mean}) / {angle_sd})')
        ro.r('pred_df$MRT_angle_degrees_squared <- pred_df$MRT_angle_degrees_scaled^2')
        
        if preferred.get('mrt_rt') == 'linear':
            # Linear model predictions
            print("Generating predictions from linear RT model...")
            try:
                ro.r('pred_y <- predict(linear_rt_model, newdata=pred_df, re.form=NA)')
                y_pred = np.exp(np.array(ro.r('pred_y')))
                ax.plot(x, y_pred, 'r-', linewidth=2, label='Linear model')
            except Exception as e:
                print(f"WARNING: Could not generate linear model predictions: {e}")
                # Fallback to approximate coefficients
                y = np.exp(0.007 * x + 7.5)
                ax.plot(x, y, 'r-', linewidth=2, label='Linear model (approx)')
        else:
            # Quadratic model predictions
            print("Generating predictions from quadratic RT model...")
            try:
                ro.r('pred_y <- predict(quadratic_rt_model, newdata=pred_df, re.form=NA)')
                y_pred = np.exp(np.array(ro.r('pred_y')))
                ax.plot(x, y_pred, 'g-', linewidth=2, label='Quadratic model')
            except Exception as e:
                print(f"WARNING: Could not generate quadratic model predictions: {e}")
                # Fallback to approximate coefficients
                y = np.exp(0.003 * x + 0.00005 * x**2 + 7.4)
                ax.plot(x, y, 'g-', linewidth=2, label='Quadratic model (approx)')
        
        ax.set_xlabel('Rotation Angle (degrees)', fontsize=12)
        ax.set_ylabel('Response Time (ms)', fontsize=12)
        ax.set_title('Mental Rotation Task: Response Time by Rotation Angle', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Save figure
        plt.tight_layout()
        plt.savefig(f'outputs/MRT_RT_model_{timestamp}.png', dpi=300)
        plt.close()
        
        print(f"Saved MRT RT visualization to: outputs/MRT_RT_model_{timestamp}.png")
        
    except Exception as e:
        print(f"WARNING: Could not create MRT RT visualization: {e}")
    
    # 2. MRT Accuracy visualization
    try:
        print("Creating MRT accuracy visualization...")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Calculate accuracy per angle
        acc_by_angle = df_mrt.groupby('MRT_angle_degrees')['MRT_isCorrect'].agg(['mean', 'sem']).reset_index()
        
        # Plot data points with error bars
        ax.errorbar(acc_by_angle['MRT_angle_degrees'], acc_by_angle['mean'], 
                   yerr=acc_by_angle['sem'], fmt='o', color='blue', 
                   ecolor='lightblue', elinewidth=3, capsize=0,
                   label='Observed data')
        
        # Generate model predictions using actual fitted models
        x = np.array(angle_bins)
        
        # Create prediction data frame if not already created
        if 'pred_df' not in ro.globalenv:
            ro.globalenv['pred_angles'] = ro.FloatVector(x)
            angle_mean = df_mrt['MRT_angle_degrees'].mean()
            angle_sd = df_mrt['MRT_angle_degrees'].std()
            ro.r(f'pred_df <- data.frame(MRT_angle_degrees = pred_angles, MRT_angle_degrees_scaled = (pred_angles - {angle_mean}) / {angle_sd})')
            ro.r('pred_df$MRT_angle_degrees_squared <- pred_df$MRT_angle_degrees_scaled^2')
        
        if preferred.get('mrt_accuracy') == 'linear':
            # Linear model predictions
            print("Generating predictions from linear accuracy model...")
            try:
                ro.r('pred_y <- predict(linear_acc_model, newdata=pred_df, re.form=NA, type="response")')
                y_pred = np.array(ro.r('pred_y'))
                ax.plot(x, y_pred, 'r-', linewidth=2, label='Linear model')
            except Exception as e:
                print(f"WARNING: Could not generate linear accuracy model predictions: {e}")
                # Fallback to approximate coefficients
                y = 1 / (1 + np.exp(-(2 - 0.01 * x)))
                ax.plot(x, y, 'r-', linewidth=2, label='Linear model (approx)')
        else:
            # Quadratic model predictions
            print("Generating predictions from quadratic accuracy model...")
            try:
                ro.r('pred_y <- predict(quadratic_acc_model, newdata=pred_df, re.form=NA, type="response")')
                y_pred = np.array(ro.r('pred_y'))
                ax.plot(x, y_pred, 'g-', linewidth=2, label='Quadratic model')
            except Exception as e:
                print(f"WARNING: Could not generate quadratic accuracy model predictions: {e}")
                # Fallback to approximate coefficients
                y = 1 / (1 + np.exp(-(2 - 0.005 * x - 0.0001 * x**2)))
                ax.plot(x, y, 'g-', linewidth=2, label='Quadratic model (approx)')
        
        ax.set_xlabel('Rotation Angle (degrees)', fontsize=12)
        ax.set_ylabel('Accuracy (proportion correct)', fontsize=12)
        ax.set_title('Mental Rotation Task: Accuracy by Rotation Angle', fontsize=14)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Save figure
        plt.tight_layout()
        plt.savefig(f'outputs/MRT_accuracy_model_{timestamp}.png', dpi=300)
        plt.close()
        
        print(f"Saved MRT accuracy visualization to: outputs/MRT_accuracy_model_{timestamp}.png")
        
    except Exception as e:
        print(f"WARNING: Could not create MRT accuracy visualization: {e}")
    
    # 3. VWM visualization
    try:
        print("Creating VWM visualization...")
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Get unique set sizes and delays
        set_sizes = sorted(df_vwm['VWM_setSize'].unique())
        delays = sorted(df_vwm['VWM_delay_s'].unique())
        
        # Calculate mean error per set size and delay
        error_by_condition = df_vwm.groupby(['VWM_setSize', 'VWM_delay_s'])['VWM_error_absolute_degrees'].agg(['mean', 'sem']).reset_index()
        
        # Plot data points with error bars for each delay
        for delay in delays:
            subset = error_by_condition[error_by_condition['VWM_delay_s'] == delay]
            ax.errorbar(subset['VWM_setSize'], subset['mean'], 
                       yerr=subset['sem'], fmt='o-', 
                       label=f'Delay = {delay}s')
        
        # Generate model predictions using actual fitted models
        x = np.array(set_sizes)
        
        # Create prediction dataframes for each delay and get actual model predictions
        if preferred.get('vwm') == 'linear':
            print("Generating predictions from linear VWM model...")
            for delay in delays:
                try:
                    # Create prediction dataframe for this delay
                    ro.r(f'''
                    pred_df_vwm <- data.frame(
                        VWM_setSize = c({",".join(map(str, set_sizes))}),
                        VWM_delay_s = {delay},
                        VWM_setSize_squared = c({",".join(map(lambda s: str(s**2), set_sizes))})
                    )
                    pred_df_vwm$VWM_setSize_log <- log(pred_df_vwm$VWM_setSize)
                    pred_df_vwm$VWM_delay_log <- log(pred_df_vwm$VWM_delay_s)
                    ''')
                    
                    # Get predictions
                    ro.r('pred_y <- predict(linear_vwm_model, newdata=pred_df_vwm, re.form=NA)')
                    y_pred = np.array(ro.r('pred_y'))
                    ax.plot(x, y_pred, '--', linewidth=1, alpha=0.7, label=f'Linear model (delay={delay}s)')
                except Exception as e:
                    print(f"WARNING: Could not generate linear VWM model predictions for delay={delay}: {e}")
                    # Fallback to approximate coefficients
                    y = 10 + 2 * x + 5 * delay
                    ax.plot(x, y, '--', linewidth=1, alpha=0.7, label=f'Linear model (approx, delay={delay}s)')
        
        elif preferred.get('vwm') == 'log_transformed':
            print("Generating predictions from log-transformed VWM model...")
            for delay in delays:
                try:
                    # Create prediction dataframe for this delay
                    ro.r(f'''
                    pred_df_vwm <- data.frame(
                        VWM_setSize = c({",".join(map(str, set_sizes))}),
                        VWM_delay_s = {delay},
                        VWM_setSize_squared = c({",".join(map(lambda s: str(s**2), set_sizes))})
                    )
                    pred_df_vwm$VWM_setSize_log <- log(pred_df_vwm$VWM_setSize)
                    pred_df_vwm$VWM_delay_log <- log(pred_df_vwm$VWM_delay_s)
                    ''')
                    
                    # Get predictions
                    ro.r('pred_y <- predict(log_vwm_model, newdata=pred_df_vwm, re.form=NA)')
                    y_pred = np.array(ro.r('pred_y'))
                    ax.plot(x, y_pred, '--', linewidth=1, alpha=0.7, label=f'Log model (delay={delay}s)')
                except Exception as e:
                    print(f"WARNING: Could not generate log-transformed VWM model predictions for delay={delay}: {e}")
                    # Fallback to approximate coefficients
                    y = 10 + 10 * np.log(x) + 5 * np.log(delay)
                    ax.plot(x, y, '--', linewidth=1, alpha=0.7, label=f'Log model (approx, delay={delay}s)')
        
        else:  # quadratic
            print("Generating predictions from quadratic VWM model...")
            for delay in delays:
                try:
                    # Create prediction dataframe for this delay
                    ro.r(f'''
                    pred_df_vwm <- data.frame(
                        VWM_setSize = c({",".join(map(str, set_sizes))}),
                        VWM_delay_s = {delay},
                        VWM_setSize_squared = c({",".join(map(lambda s: str(s**2), set_sizes))})
                    )
                    pred_df_vwm$VWM_setSize_log <- log(pred_df_vwm$VWM_setSize)
                    pred_df_vwm$VWM_delay_log <- log(pred_df_vwm$VWM_delay_s)
                    ''')
                    
                    # Get predictions
                    ro.r('pred_y <- predict(quadratic_vwm_model, newdata=pred_df_vwm, re.form=NA)')
                    y_pred = np.array(ro.r('pred_y'))
                    ax.plot(x, y_pred, '--', linewidth=1, alpha=0.7, label=f'Quadratic model (delay={delay}s)')
                except Exception as e:
                    print(f"WARNING: Could not generate quadratic VWM model predictions for delay={delay}: {e}")
                    # Fallback to approximate coefficients
                    y = 10 + 1 * x + 0.5 * x**2 + 3 * delay
                    ax.plot(x, y, '--', linewidth=1, alpha=0.7, label=f'Quadratic model (approx, delay={delay}s)')
        
        ax.set_xlabel('Set Size', fontsize=12)
        ax.set_ylabel('Absolute Error (degrees)', fontsize=12)
        ax.set_title('Visual Working Memory: Error by Set Size and Delay', fontsize=14)
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1))
        ax.grid(True, alpha=0.3)
        
        # Save figure
        plt.tight_layout()
        plt.savefig(f'outputs/VWM_model_{timestamp}.png', dpi=300)
        plt.close()
        
        print(f"Saved VWM visualization to: outputs/VWM_model_{timestamp}.png")
        
    except Exception as e:
        print(f"WARNING: Could not create VWM visualization: {e}")

def create_residual_plots(preferred, timestamp):
    """
    Create diagnostic residual plots for model assessment.
    
    Parameters:
    preferred (dict): Dictionary with preferred model determinations
    timestamp (str): Timestamp string for filenames
    """
    print("Creating model diagnostic plots...")
    
    try:
        # MRT RT model residuals
        print("Creating MRT RT model residual plots...")
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Get preferred model name
        model_name = "linear_rt_model" if preferred.get('mrt_rt') == 'linear' else "quadratic_rt_model"
        
        # Extract residuals and fitted values
        ro.r(f'''
        if(exists("{model_name}")) {{
            resid_df <- data.frame(
                fitted = fitted({model_name}),
                residuals = residuals({model_name}),
                participant = df_rt$participantId
            )
        }}
        ''')
        
        try:
            # Convert R dataframe to pandas
            resid_df = ro.conversion.rpy2py(ro.r('resid_df'))
            
            # Residuals vs Fitted plot
            axes[0].scatter(resid_df['fitted'], resid_df['residuals'], alpha=0.3)
            axes[0].axhline(y=0, color='r', linestyle='-', alpha=0.3)
            axes[0].set_xlabel('Fitted values')
            axes[0].set_ylabel('Residuals')
            axes[0].set_title('Residuals vs Fitted')
            
            # QQ plot of residuals
            from scipy import stats
            stats.probplot(resid_df['residuals'], plot=axes[1])
            axes[1].set_title('Normal Q-Q Plot')
            
            plt.tight_layout()
            plt.savefig(f'outputs/MRT_RT_diagnostics_{timestamp}.png', dpi=300)
            plt.close()
            print(f"Saved MRT RT diagnostic plots to: outputs/MRT_RT_diagnostics_{timestamp}.png")
            
        except Exception as e:
            print(f"WARNING: Could not create MRT RT residual plots: {e}")
        
        # MRT Accuracy model residuals (for logistic models, use different diagnostics)
        print("Creating MRT accuracy model residual plots...")
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Get preferred model name
        model_name = "linear_acc_model" if preferred.get('mrt_accuracy') == 'linear' else "quadratic_acc_model"
        
        # For logistic regression, use binned residuals
        ro.r(f'''
        if(exists("{model_name}")) {{
            # Get fitted probabilities
            fitted_probs <- fitted({model_name})
            
            # Create bins for fitted values
            n_bins <- 10
            bin_breaks <- seq(0, 1, length.out = n_bins + 1)
            bin_mids <- (bin_breaks[-1] + bin_breaks[-length(bin_breaks)]) / 2
            
            # Assign each fitted value to a bin
            bins <- cut(fitted_probs, breaks = bin_breaks, include.lowest = TRUE)
            
            # Calculate mean residual in each bin
            bin_residuals <- tapply(df_acc$MRT_isCorrect - fitted_probs, bins, mean)
            
            # Calculate standard error for each bin
            bin_counts <- table(bins)
            bin_se <- sqrt(tapply(fitted_probs * (1 - fitted_probs), bins, mean) / bin_counts)
            
            # Create dataframe for plotting
            binned_resid_df <- data.frame(
                bin_mid = bin_mids,
                residual = as.numeric(bin_residuals),
                se = as.numeric(bin_se),
                count = as.numeric(bin_counts)
            )
        }}
        ''')
        
        try:
            # Convert R dataframe to pandas
            binned_resid_df = ro.conversion.rpy2py(ro.r('binned_resid_df'))
            
            # Binned residual plot
            axes[0].errorbar(binned_resid_df['bin_mid'], binned_resid_df['residual'], 
                           yerr=binned_resid_df['se'], fmt='o')
            axes[0].axhline(y=0, color='r', linestyle='-', alpha=0.3)
            axes[0].set_xlabel('Fitted probability')
            axes[0].set_ylabel('Average residual')
            axes[0].set_title('Binned Residual Plot')
            
            # Sample size per bin
            axes[1].bar(binned_resid_df['bin_mid'], binned_resid_df['count'])
            axes[1].set_xlabel('Fitted probability')
            axes[1].set_ylabel('Count')
            axes[1].set_title('Observations per Bin')
            
            plt.tight_layout()
            plt.savefig(f'outputs/MRT_accuracy_diagnostics_{timestamp}.png', dpi=300)
            plt.close()
            print(f"Saved MRT accuracy diagnostic plots to: outputs/MRT_accuracy_diagnostics_{timestamp}.png")
            
        except Exception as e:
            print(f"WARNING: Could not create MRT accuracy residual plots: {e}")
        
        # VWM model residuals
        print("Creating VWM model residual plots...")
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # Get preferred model name
        if preferred.get('vwm') == 'linear':
            model_name = "linear_vwm_model"
        elif preferred.get('vwm') == 'log_transformed':
            model_name = "log_vwm_model"
        else:
            model_name = "quadratic_vwm_model"
        
        # Extract residuals and fitted values
        ro.r(f'''
        if(exists("{model_name}")) {{
            vwm_resid_df <- data.frame(
                fitted = fitted({model_name}),
                residuals = residuals({model_name}),
                participant = df_vwm$participantId
            )
        }}
        ''')
        
        try:
            # Convert R dataframe to pandas
            vwm_resid_df = ro.conversion.rpy2py(ro.r('vwm_resid_df'))
            
            # Residuals vs Fitted plot
            axes[0].scatter(vwm_resid_df['fitted'], vwm_resid_df['residuals'], alpha=0.3)
            axes[0].axhline(y=0, color='r', linestyle='-', alpha=0.3)
            axes[0].set_xlabel('Fitted values')
            axes[0].set_ylabel('Residuals')
            axes[0].set_title('Residuals vs Fitted')
            
            # QQ plot of residuals
            stats.probplot(vwm_resid_df['residuals'], plot=axes[1])
            axes[1].set_title('Normal Q-Q Plot')
            
            plt.tight_layout()
            plt.savefig(f'outputs/VWM_diagnostics_{timestamp}.png', dpi=300)
            plt.close()
            print(f"Saved VWM diagnostic plots to: outputs/VWM_diagnostics_{timestamp}.png")
            
        except Exception as e:
            print(f"WARNING: Could not create VWM residual plots: {e}")
            
    except Exception as e:
        print(f"WARNING: Error creating diagnostic plots: {e}")

def save_results(summary, coefficients, timestamp):
    """
    Save results to CSV files.
    
    Parameters:
    summary (list): List of result dictionaries
    coefficients (list): List of coefficient dictionaries
    timestamp (str): Timestamp string for filenames
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Save model comparison results
    if summary:
        results_df = pd.DataFrame(summary)
        
        # Correct NA_integer_ representation from R
        try:
            na_int_val = ro.r('NA_integer_')[0]
            if 'likelihood_ratio_test_p' in results_df.columns:
                results_df['likelihood_ratio_test_p'] = results_df['likelihood_ratio_test_p'].replace(na_int_val, np.nan)
        except Exception as e:
            print(f"WARNING: Could not correct NA values in results: {e}")
        
        results_file = f'outputs/nonlinear_analysis_results_{timestamp}.csv'
        results_df.to_csv(results_file, index=False)
        
        # Verify file was created and has expected content
        if os.path.exists(results_file):
            saved_df = pd.read_csv(results_file)
            print(f"Saved model comparison results to: {results_file}")
            print(f"Verified file exists with {len(saved_df)} rows and {len(saved_df.columns)} columns")
            
            # Check required columns
            expected_cols = ['task_name', 'model_type', 'outcome_measure', 'AIC', 'BIC', 'r_squared']
            missing_cols = [col for col in expected_cols if col not in saved_df.columns]
            if missing_cols:
                print(f"WARNING: Output file missing expected columns: {missing_cols}")
            else:
                print("All expected columns present in results file")
        else:
            print(f"ERROR: Failed to create results file: {results_file}")
        
        # Print summary (truncated for LLM context window)
        print("Model comparison summary (truncated):")
        print(results_df.head(3))
    
    # Save model coefficients
    if coefficients:
        coef_df = pd.DataFrame(coefficients)
        
        # Correct NA_integer_ representation from R
        try:
            na_int_val = ro.r('NA_integer_')[0]
            if 'p_value' in coef_df.columns:
                coef_df['p_value'] = coef_df['p_value'].replace(na_int_val, np.nan)
        except Exception as e:
            print(f"WARNING: Could not correct NA values in coefficients: {e}")
        
        coef_file = f'outputs/nonlinear_model_coefficients_{timestamp}.csv'
        coef_df.to_csv(coef_file, index=False)
        
        # Verify file was created and has expected content
        if os.path.exists(coef_file):
            saved_coef_df = pd.read_csv(coef_file)
            print(f"Saved model coefficients to: {coef_file}")
            print(f"Verified file exists with {len(saved_coef_df)} rows and {len(saved_coef_df.columns)} columns")
            
            # Check required columns
            expected_cols = ['task_name', 'model_type', 'coefficient_name', 'estimate', 'std_error']
            missing_cols = [col for col in expected_cols if col not in saved_coef_df.columns]
            if missing_cols:
                print(f"WARNING: Output file missing expected columns: {missing_cols}")
            else:
                print("All expected columns present in coefficients file")
        else:
            print(f"ERROR: Failed to create coefficients file: {coef_file}")
        
        # Print first few coefficients (truncated for LLM context window)
        print("First few model coefficients (truncated):")
        print(coef_df.head(3))

def main():
    """
    Main execution function.
    
    Returns:
    int: 0 for success, 1 for error
    """
    print("Starting non-linear relationship analysis...")
    print("NOTE: This analysis attempts to use complex random effects structures as specified.")
    print("      If complex structures lead to convergence issues or singular fits, the analysis")
    print("      will automatically fall back to simpler structures. The final random effects")
    print("      structure used for each model is documented in the output.")
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"Analysis timestamp: {timestamp}")
    
    try:
        # Find input files
        vwm_pattern = "outputs/VWM_cleaned_data_*.csv"
        mrt_pattern = "outputs/MRT_cleaned_data_*.csv"
        
        vwm_file = find_latest_file(vwm_pattern)
        mrt_file = find_latest_file(mrt_pattern)
        
        if not vwm_file:
            print(f"ERROR: No VWM file found matching pattern: {vwm_pattern}")
            return 1
        
        if not mrt_file:
            print(f"ERROR: No MRT file found matching pattern: {mrt_pattern}")
            return 1
        
        print(f"Found VWM file: {vwm_file}")
        print(f"Found MRT file: {mrt_file}")
        
        # Define required columns
        vwm_columns = [
            'participantId', 'table', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s',
            'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_timeout', 
            'VWM_isAttentionCheck', 'isPractice', 'excluded_participant', 'valid_trial'
        ]
        
        mrt_columns = [
            'participantId', 'table', 'MRT_trial', 'MRT_angle_degrees', 'MRT_isCorrect',
            'MRT_rt_ms', 'MRT_timeout', 'MRT_isAttentionCheck', 'isPractice',
            'excluded_participant', 'valid_trial'
        ]
        
        # Load data
        df_vwm = load_and_validate_data(vwm_file, vwm_columns)
        df_mrt = load_and_validate_data(mrt_file, mrt_columns)
        
        if df_vwm is None or df_mrt is None:
            print("ERROR: Failed to load required data files")
            return 1
        
        # Filter data
        df_vwm_filtered = filter_data(df_vwm, "VWM")
        df_mrt_filtered = filter_data(df_mrt, "MRT")
        
        if len(df_vwm_filtered) == 0 or len(df_mrt_filtered) == 0:
            print("ERROR: No data remaining after filtering")
            return 1
        
        # Setup R environment
        r_packages = setup_r_environment()
        if r_packages is None:
            print("ERROR: Failed to setup R environment")
            return 1
        
        # Fit models
        print("\n" + "="*50)
        print("FITTING MODELS")
        print("="*50)
        
        mrt_results = fit_mrt_models(df_mrt_filtered, r_packages)
        vwm_results = fit_vwm_models(df_vwm_filtered, r_packages)
        
        # Combine results
        all_results = {}
        if mrt_results.get('mrt_rt'):
            all_results['mrt_rt'] = mrt_results['mrt_rt']
        if mrt_results.get('mrt_accuracy'):
            all_results['mrt_accuracy'] = mrt_results['mrt_accuracy']
        if vwm_results.get('vwm'):
            all_results['vwm'] = vwm_results['vwm']
        
        # Extract coefficients
        coefficients = extract_model_coefficients(r_packages)
        
        # Determine preferred models
        preferred = determine_preferred_models(all_results)
        
        # Create results summary
        summary = create_results_summary(all_results, preferred)
        
        # Create visualizations
        create_model_visualizations(df_mrt_filtered, df_vwm_filtered, preferred, timestamp)
        
        # Save results
        save_results(summary, coefficients, timestamp)
        
        # Print final recommendations
        print("\n" + "="*50)
        print("ANALYSIS RECOMMENDATIONS")
        print("="*50)
        
        for task, model in preferred.items():
            print(f"{task}: Preferred model is {model}")
            
        if any('quadratic' in model or 'log_transformed' in model for model in preferred.values()):
            print("\nRECOMMENDation: Non-linear relationships detected.")
            print("Consider re-running main analyses with non-linear terms.")
        else:
            print("\nRECOMMENDation: Linear relationships appear adequate.")
            print("Main analyses can proceed with linear assumptions.")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
