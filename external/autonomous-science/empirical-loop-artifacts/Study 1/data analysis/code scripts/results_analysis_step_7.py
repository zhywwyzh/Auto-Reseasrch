#!/usr/bin/env python3

import pandas as pd
import numpy as np
np.bool = np.bool_  # Handle numpy deprecation
import os
import glob
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

# Import R packages via rpy2
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri, Formula
from rpy2.robjects.packages import importr
import rpy2.robjects.numpy2ri as numpy2ri

# Activate automatic conversion between pandas and R
pandas2ri.activate()
numpy2ri.activate()

# Function to safely install and import R packages
def safe_import_r_package(package_name, repos='https://cloud.r-project.org/'):
    """Safely import an R package, installing it if necessary."""
    try:
        return importr(package_name)
    except:
        print(f"Installing R package: {package_name}")
        utils = importr('utils')
        utils.install_packages(package_name, repos=repos)
        return importr(package_name)

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
    # Sort by modification time and return the most recent
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def load_and_validate_data(file_path, required_columns):
    """
    Load CSV data and validate required columns exist.
    
    Parameters:
    file_path (str): Path to the CSV file
    required_columns (list): List of required column names
    
    Returns:
    pd.DataFrame: Loaded dataframe, or None if validation fails
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    try:
        df = pd.read_csv(file_path)
        print(f"Loaded file: {file_path}")
        print(f"Shape: {df.shape}")
        print(f"All columns: {list(df.columns)}")
        print("First 3 rows:")
        print(df.head(3))
        
        # Check for required columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            print(f"Missing required columns: {missing_cols}")
            return None
        
        return df
        
    except Exception as e:
        print(f"Error loading file {file_path}: {e}")
        return None

def filter_vwm_data(df):
    """
    Filter VWM data according to exclusion criteria.
    
    Parameters:
    df (pd.DataFrame): Raw VWM dataframe
    
    Returns:
    pd.DataFrame: Filtered VWM dataframe
    """
    print("Filtering VWM data...")
    print(f"Initial shape: {df.shape}")
    
    # Print unique values for key experimental design columns
    print(f"Unique VWM_setSize values: {sorted(df['VWM_setSize'].dropna().unique())}")
    print(f"Unique VWM_delay_s values: {sorted(df['VWM_delay_s'].dropna().unique())}")
    print(f"Unique excluded_participant values: {df['excluded_participant'].dropna().unique()}")
    print(f"Unique isPractice values: {df['isPractice'].dropna().unique()}")
    print(f"Unique valid_trial values: {df['valid_trial'].dropna().unique()}")
    print(f"VWM_error_absolute_degrees data type: {df['VWM_error_absolute_degrees'].dtype}")
    
    # Filter out null values in key columns
    df = df.dropna(subset=['excluded_participant', 'isPractice', 'valid_trial', 'VWM_error_absolute_degrees'])
    print(f"After removing null values in key columns: {df.shape}")
    
    # Apply filters
    df_filtered = df[
        (df['excluded_participant'] == False) &
        (df['isPractice'] == False) &
        (df['valid_trial'] == True)
    ].copy()
    
    print(f"After applying filters: {df_filtered.shape}")
    print(f"Participants remaining: {df_filtered['participantId'].nunique()}")
    
    return df_filtered

def filter_mrt_data(df):
    """
    Filter MRT data according to exclusion criteria.
    
    Parameters:
    df (pd.DataFrame): Raw MRT dataframe
    
    Returns:
    pd.DataFrame: Filtered MRT dataframe
    """
    print("Filtering MRT data...")
    print(f"Initial shape: {df.shape}")
    
    # Print unique values for key experimental design columns
    print(f"Unique MRT_angle_degrees values: {sorted(df['MRT_angle_degrees'].dropna().unique())}")
    print(f"Unique excluded_participant values: {df['excluded_participant'].dropna().unique()}")
    print(f"Unique isPractice values: {df['isPractice'].dropna().unique()}")
    print(f"Unique valid_trial values: {df['valid_trial'].dropna().unique()}")
    print(f"Unique MRT_isCorrect values: {df['MRT_isCorrect'].dropna().unique()}")
    print(f"MRT_rt_ms data type: {df['MRT_rt_ms'].dtype}")
    
    # Filter out null values in key columns
    df = df.dropna(subset=['excluded_participant', 'isPractice', 'valid_trial', 'MRT_rt_ms', 'MRT_isCorrect'])
    print(f"After removing null values in key columns: {df.shape}")
    
    # Apply filters
    df_filtered = df[
        (df['excluded_participant'] == False) &
        (df['isPractice'] == False) &
        (df['valid_trial'] == True)
    ].copy()
    
    print(f"After applying filters: {df_filtered.shape}")
    print(f"Participants remaining: {df_filtered['participantId'].nunique()}")
    
    return df_filtered

def fit_vwm_mixed_model(df, r_base, r_lme4):
    """
    Fit hierarchical linear mixed-effects model for VWM data.
    
    Parameters:
    df (pd.DataFrame): Filtered VWM dataframe
    r_base: R base package
    r_lme4: R lme4 package
    
    Returns:
    list: Model results as a list of dictionaries
    """
    print("Fitting VWM mixed-effects model...")
    
    # Check for required columns
    required_cols = ['participantId', 'VWM_setSize', 'VWM_delay_s', 'VWM_error_absolute_degrees']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns for VWM model: {missing_cols}")
        return []
    
    # Print descriptive statistics for key variables
    print("\nDescriptive statistics for VWM model variables:")
    for col in ['VWM_error_absolute_degrees']:
        stats = df[col].describe()
        print(f"{col}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}")
    
    # Print counts by condition
    print("\nTrials by condition:")
    if len(df) > 0 and 'VWM_setSize' in df.columns and 'VWM_delay_s' in df.columns:
        condition_counts = df.groupby(['VWM_setSize', 'VWM_delay_s']).size()
        print(condition_counts)
        
        # Additional verification requested by supervisor
        print(f"\nVWM factor level verification:")
        print(f"Number of unique VWM_setSize levels: {df['VWM_setSize'].nunique()}")
        print(f"Number of unique VWM_delay_s levels: {df['VWM_delay_s'].nunique()}")
        print(f"Expected 2x2 design: {df['VWM_setSize'].nunique() == 2 and df['VWM_delay_s'].nunique() == 2}")
    else:
        print("Error: Cannot compute condition counts - missing data or columns")
    
    # Additional diagnostics for factor level verification
    print(f"\nDetailed factor level analysis:")
    if 'VWM_setSize' in df.columns and len(df) > 0:
        print(f"VWM_setSize value counts: {df['VWM_setSize'].value_counts().sort_index()}")
    else:
        print("VWM_setSize value counts: No data available")
    
    if 'VWM_delay_s' in df.columns and len(df) > 0:
        print(f"VWM_delay_s value counts: {df['VWM_delay_s'].value_counts().sort_index()}")
    else:
        print("VWM_delay_s value counts: No data available")
    print(f"Total participants in VWM data: {df['participantId'].nunique()}")
    print(f"Total trials in VWM data: {len(df)}")
    
    # Import lmerTest for p-values
    try:
        r_lmerTest = safe_import_r_package('lmerTest')
        print("Successfully loaded lmerTest package")
    except Exception as e:
        print(f"Warning: Could not load lmerTest package: {e}")
        print("P-values will not be available")
    
    # Work on a copy and map delay values to match factor levels
    df_copy = df.copy()
    df_copy['VWM_delay_s'] = df_copy['VWM_delay_s'].replace({1.0: 1000, 4.0: 4000}).astype(int)
    
    # Validate that we only have expected values before factor conversion
    unique_setsize = sorted(df_copy['VWM_setSize'].unique())
    unique_delay = sorted(df_copy['VWM_delay_s'].unique())
    print(f"Unique VWM_setSize values before factor conversion: {unique_setsize}")
    print(f"Unique VWM_delay_s values before factor conversion: {unique_delay}")
    
    # Ensure we only have the expected 2x2 design values and filter out any unexpected values
    if set(unique_setsize) != {2, 4}:
        print(f"Warning: Unexpected VWM_setSize values: {unique_setsize}")
        print("Filtering to only include setSize 2 and 4...")
        df_copy = df_copy[df_copy['VWM_setSize'].isin([2, 4])]
        
    if set(unique_delay) != {1000, 4000}:
        print(f"Warning: Unexpected VWM_delay_s values: {unique_delay}")
        print("Filtering to only include delay 1000 and 4000...")
        df_copy = df_copy[df_copy['VWM_delay_s'].isin([1000, 4000])]
    
    print(f"After filtering for 2x2 design: {df_copy.shape}")
    print(f"Final unique VWM_setSize: {sorted(df_copy['VWM_setSize'].unique())}")
    print(f"Final unique VWM_delay_s: {sorted(df_copy['VWM_delay_s'].unique())}")
    
    # Convert factor variables to strings for proper R factor level specification
    df_copy['VWM_setSize'] = df_copy['VWM_setSize'].astype(str)
    df_copy['VWM_delay_s'] = df_copy['VWM_delay_s'].astype(str)
    
    # Convert to R dataframe
    r_df = pandas2ri.py2rpy(df_copy)
    
    # Convert variables to factors in R with explicit level specification
    robjects.r.assign("vwm_data", r_df)
    robjects.r("""
    # Ensure proper factor creation with explicit levels and contrasts
    vwm_data$VWM_setSize <- factor(vwm_data$VWM_setSize, levels = c("2", "4"))
    vwm_data$VWM_delay_s <- factor(vwm_data$VWM_delay_s, levels = c("1000", "4000"))
    vwm_data$participantId <- as.factor(vwm_data$participantId)
    
    # Verify factor structure before setting contrasts
    print("=== FACTOR VERIFICATION ===")
    print("VWM_setSize levels:"); print(levels(vwm_data$VWM_setSize))
    print("VWM_delay_s levels:"); print(levels(vwm_data$VWM_delay_s))
    print("VWM_setSize unique values:"); print(unique(vwm_data$VWM_setSize))
    print("VWM_delay_s unique values:"); print(unique(vwm_data$VWM_delay_s))
    
    # Set treatment contrasts explicitly with proper reference levels
    # This should create: setSize4 (4 vs 2) and delay_s4000 (4000 vs 1000)
    contrasts(vwm_data$VWM_setSize) <- contr.treatment(2, base=1)  # "2" is reference
    contrasts(vwm_data$VWM_delay_s) <- contr.treatment(2, base=1)  # "1000" is reference
    
    print("=== CONTRAST VERIFICATION ===")
    print("VWM_setSize contrasts:"); print(contrasts(vwm_data$VWM_setSize))
    print("VWM_delay_s contrasts:"); print(contrasts(vwm_data$VWM_delay_s))
    
    # Additional diagnostic: print unique values in R dataframe
    print("=== R DATAFRAME UNIQUE VALUES ===")
    print("Unique VWM_delay_s in R data:"); print(unique(vwm_data$VWM_delay_s))
    print("Unique VWM_setSize in R data:"); print(unique(vwm_data$VWM_setSize))
    """)
    
    print("Attempting to fit full random effects model...")
    print(f"Number of participants: {df['participantId'].nunique()}")
    print(f"Number of trials: {len(df)}")
    print(f"Model formula: VWM_error_absolute_degrees ~ VWM_setSize * VWM_delay_s + (1 + VWM_setSize * VWM_delay_s | participantId)")
    print("This may take several minutes for complex random effects structures...")
    
    # Try fitting the full model first
    model_converged = False
    try:
        robjects.r("""
        vwm_model <- lmerTest::lmer(VWM_error_absolute_degrees ~ VWM_setSize * VWM_delay_s + 
                         (1 + VWM_setSize * VWM_delay_s | participantId), 
                         data = vwm_data, REML = FALSE)
        """)
        
        # Check for convergence issues
        robjects.r("""
        conv_code <- vwm_model@optinfo$conv$opt
        is_singular <- lme4::isSingular(vwm_model)
        has_warnings <- length(vwm_model@optinfo$warnings) > 0
        """)
        
        try:
            conv_code_obj = robjects.r("conv_code")
            is_singular_obj = robjects.r("is_singular")
            has_warnings_obj = robjects.r("has_warnings")
            
            # More robust extraction with type checking
            conv_code = float(conv_code_obj[0]) if conv_code_obj and len(conv_code_obj) > 0 and conv_code_obj[0] is not None else 1
            is_singular = bool(is_singular_obj[0]) if is_singular_obj and len(is_singular_obj) > 0 and is_singular_obj[0] is not None else True
            has_warnings = bool(has_warnings_obj[0]) if has_warnings_obj and len(has_warnings_obj) > 0 and has_warnings_obj[0] is not None else True
        except (IndexError, TypeError, Exception) as e:
            print(f"Error accessing VWM convergence diagnostics: {e}")
            conv_code = 1
            is_singular = True
            has_warnings = True
        
        print(f"VWM full model diagnostics: conv_code={conv_code}, singular={is_singular}, warnings={has_warnings}")
        
        if conv_code == 0 and not is_singular and not has_warnings:
            print("Full model converged successfully")
            model_name = "VWM_full_model"
            model_converged = True
        else:
            print("Full model has convergence issues - will try simplified model")
            
    except Exception as e:
        print(f"Full model failed with error: {robjects.r.geterrmessage()}")
    
    # If full model didn't converge properly, try simplified model
    if not model_converged:
        try:
            robjects.r("""
            vwm_model <- lmerTest::lmer(VWM_error_absolute_degrees ~ VWM_setSize * VWM_delay_s + 
                             (1 + VWM_setSize + VWM_delay_s | participantId), 
                             data = vwm_data, REML = FALSE)
            """)
            
            # Check convergence for simplified model
            robjects.r("""
            conv_code <- vwm_model@optinfo$conv$opt
            is_singular <- lme4::isSingular(vwm_model)
            has_warnings <- length(vwm_model@optinfo$warnings) > 0
            """)
            
            try:
                conv_code_obj = robjects.r("conv_code")
                is_singular_obj = robjects.r("is_singular")
                has_warnings_obj = robjects.r("has_warnings")
                
                conv_code = float(conv_code_obj[0]) if conv_code_obj and len(conv_code_obj) > 0 and conv_code_obj[0] is not None else 1
                is_singular = bool(is_singular_obj[0]) if is_singular_obj and len(is_singular_obj) > 0 and is_singular_obj[0] is not None else True
                has_warnings = bool(has_warnings_obj[0]) if has_warnings_obj and len(has_warnings_obj) > 0 and has_warnings_obj[0] is not None else True
            except (IndexError, TypeError, Exception) as e:
                print(f"Error accessing simplified VWM convergence diagnostics: {e}")
                conv_code = 1
                is_singular = True
                has_warnings = True
            
            if conv_code == 0 and not is_singular and not has_warnings:
                print("Simplified model (additive random effects) converged")
                model_name = "VWM_simplified_model"
                model_converged = True
            else:
                print("Simplified model also has convergence issues - using intercept only")
                model_converged = False
                
        except Exception as e:
            print(f"Simplified model failed: {robjects.r.geterrmessage()}")
            model_converged = False
    
    # If simplified model also failed, use intercept only
    if not model_converged:
        robjects.r("""
        vwm_model <- lmerTest::lmer(VWM_error_absolute_degrees ~ VWM_setSize * VWM_delay_s + 
                         (1 | participantId), 
                         data = vwm_data, REML = FALSE)
        """)
        print("Random intercept only model fitted")
        model_name = "VWM_intercept_only_model"
    
    # Extract model summary
    robjects.r("vwm_summary <- summary(vwm_model)")
    
    # Print detailed model information for debugging
    robjects.r("""
    print("=== VWM MODEL SUMMARY ===")
    print("Fixed effects:")
    print(fixef(vwm_model))
    print("Fixed effects names:")
    print(names(fixef(vwm_model)))
    """)
    
    # Convert coefficients to data frame in R before extracting
    robjects.r("vwm_coef_df <- as.data.frame(coef(vwm_summary))")
    
    # Get confidence intervals
    try:
        robjects.r("vwm_confint <- as.data.frame(confint(vwm_model, method='Wald'))")
        # Print CI structure for debugging
        robjects.r("print('VWM CI row names:'); print(rownames(vwm_confint))")
        robjects.r("print('VWM CI column names:'); print(colnames(vwm_confint))")
        ci_available = True
    except Exception as e:
        print(f"Could not compute confidence intervals: {robjects.r.geterrmessage()}")
        ci_available = False
    
    # Extract results
    coef_df = pandas2ri.rpy2py(robjects.r("vwm_coef_df"))
    print(f"Coefficient dataframe shape: {coef_df.shape}")
    print(f"Coefficient dataframe columns: {list(coef_df.columns)}")
    
    # Extract p-values if available
    try:
        if coef_df.shape[1] > 4:
            p_values = coef_df.iloc[:, 4]
            p_values_available = True
        else:
            p_values = np.array([np.nan] * len(coef_df))
            p_values_available = False
    except Exception as e:
        print(f"Error extracting p-values: {e}")
        p_values = np.array([np.nan] * len(coef_df))
        p_values_available = False
    
    if ci_available:
        try:
            ci_df = pandas2ri.rpy2py(robjects.r("vwm_confint"))
            if ci_df is not None and not ci_df.empty:
                print(f"CI dataframe shape: {ci_df.shape}")
                print(f"CI dataframe columns: {list(ci_df.columns)}")
            else:
                print("Warning: CI dataframe is empty")
                ci_available = False
        except Exception as e:
            print(f"Error accessing CI dataframe: {e}")
            ci_available = False
    
    results = []
    
    # Verify we have the expected number of effects for 2x2 factorial design
    expected_effects = 4  # Intercept, main effect 1, main effect 2, interaction
    actual_effects = len(coef_df)
    if actual_effects != expected_effects:
        print(f"ERROR: Expected {expected_effects} fixed effects for 2x2 factorial design, but got {actual_effects}")
        print(f"Effect names: {list(coef_df.index)}")
        print("This indicates improper factor level specification in R.")
        print("Expected effects: (Intercept), VWM_setSize4, VWM_delay_s4000, VWM_setSize4:VWM_delay_s4000")
        
        # Continue processing but flag the issue
        if actual_effects > expected_effects:
            print("WARNING: Proceeding with analysis but results may not be interpretable.")
        elif actual_effects < expected_effects:
            print("ERROR: Too few effects detected. Model may have failed to fit properly.")
    else:
        print(f"SUCCESS: Found expected {expected_effects} fixed effects for 2x2 factorial design")
    
    # Iterate using R-generated effect names from coef_df.index
    for r_effect_name in coef_df.index:
        estimate = coef_df.loc[r_effect_name, coef_df.columns[0]]
        std_error = coef_df.loc[r_effect_name, coef_df.columns[1]]
        t_value = coef_df.loc[r_effect_name, coef_df.columns[3]] if coef_df.shape[1] > 3 else np.nan  # lmerTest: column 3 is t-value
        
        # Get p-value for this effect
        effect_idx = list(coef_df.index).index(r_effect_name)
        p_val = p_values[effect_idx] if p_values_available and effect_idx < len(p_values) else np.nan
        
        # Try to extract CI from R results first
        ci_lower = np.nan
        ci_upper = np.nan
        
        if ci_available and r_effect_name in ci_df.index:
            try:
                ci_lower = ci_df.loc[r_effect_name, ci_df.columns[0]]
                ci_upper = ci_df.loc[r_effect_name, ci_df.columns[1]]
                # Validate CI values are numeric
                if pd.isna(ci_lower) or pd.isna(ci_upper) or not np.isfinite(ci_lower) or not np.isfinite(ci_upper):
                    print(f"Warning: Invalid CI values for {r_effect_name}, using normal approximation")
                    ci_lower = np.nan
                    ci_upper = np.nan
                else:
                    print(f"Found CI for {r_effect_name} by name: [{ci_lower:.4f}, {ci_upper:.4f}]")
            except (KeyError, IndexError, TypeError, Exception) as e:
                print(f"Error extracting CI for {r_effect_name} by name: {e}")
                ci_lower = np.nan
                ci_upper = np.nan
        
        # If CI extraction failed, use normal approximation
        if np.isnan(ci_lower) or np.isnan(ci_upper):
            ci_lower = estimate - 1.96 * std_error
            ci_upper = estimate + 1.96 * std_error
            print(f"Using normal approximation CI for {r_effect_name}: [{ci_lower:.4f}, {ci_upper:.4f}]")
        
        result = {
            'model_name': model_name,
            'effect_name': r_effect_name,
            'estimate': estimate,
            'std_error': std_error,
            't_value': t_value,
            'p_value': p_val,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper
        }
        results.append(result)
    
    print(f"VWM model fitted with {len(results)} effects")
    return results

def fit_mrt_mixed_models(df, r_base, r_lme4):
    """
    Fit hierarchical linear mixed-effects models for MRT data.
    
    Parameters:
    df (pd.DataFrame): Filtered MRT dataframe
    r_base: R base package
    r_lme4: R lme4 package
    
    Returns:
    list: Model results for both RT and accuracy models
    """
    print("Fitting MRT mixed-effects models...")
    
    # Check for required columns
    required_cols = ['participantId', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns for MRT models: {missing_cols}")
        return []
    
    # Import lmerTest for p-values
    try:
        r_lmerTest = safe_import_r_package('lmerTest')
        print("Successfully loaded lmerTest package")
    except Exception as e:
        print(f"Warning: Could not load lmerTest package: {e}")
        print("P-values will not be available for RT model")
    
    # Apply log transformation to RT and filter for correct trials
    df_rt = df[df['MRT_isCorrect'] == True].copy()
    df_rt = df_rt.dropna(subset=['MRT_rt_ms'])
    df_rt['log_rt'] = np.log(df_rt['MRT_rt_ms'])
    
    # Print descriptive statistics for key variables
    print("\nDescriptive statistics for MRT model variables:")
    for col in ['MRT_rt_ms', 'log_rt']:
        if col in df_rt.columns:
            stats = df_rt[col].describe()
            print(f"{col}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}")
    
    # Print accuracy by angle
    print("\nAccuracy by angle:")
    accuracy_by_angle = df.groupby('MRT_angle_degrees')['MRT_isCorrect'].mean()
    print(accuracy_by_angle)
    
    # Print counts by angle
    print("\nTrials by angle:")
    angle_counts = df.groupby('MRT_angle_degrees').size()
    print(angle_counts)
    
    print(f"RT model data shape: {df_rt.shape}")
    print(f"RT model participants: {df_rt['participantId'].nunique()}")
    print(f"Accuracy model data shape: {df.shape}")
    print(f"Accuracy model participants: {df['participantId'].nunique()}")
    
    results = []
    
    # RT Model
    print("Fitting RT model...")
    r_df_rt = pandas2ri.py2rpy(df_rt)
    robjects.r.assign("mrt_rt_data", r_df_rt)
    robjects.r("""
    mrt_rt_data$participantId <- as.factor(mrt_rt_data$participantId)
    # Rescale MRT_angle_degrees to improve convergence (divide by 50)
    mrt_rt_data$MRT_angle_degrees_scaled <- mrt_rt_data$MRT_angle_degrees / 50
    """)
    
    # Try full model first
    model_converged = False
    try:
        robjects.r("""
        mrt_rt_model <- lmerTest::lmer(log_rt ~ MRT_angle_degrees_scaled + (1 + MRT_angle_degrees_scaled | participantId), 
                            data = mrt_rt_data, REML = FALSE)
        """)
        
        # Check for convergence issues more thoroughly
        robjects.r("""
        conv_code <- mrt_rt_model@optinfo$conv$opt
        is_singular <- lme4::isSingular(mrt_rt_model)
        has_warnings <- length(mrt_rt_model@optinfo$warnings) > 0
        max_grad <- max(abs(mrt_rt_model@optinfo$derivs$gradient))
        """)
        
        try:
            conv_code_obj = robjects.r("conv_code")
            is_singular_obj = robjects.r("is_singular")
            has_warnings_obj = robjects.r("has_warnings")
            max_grad_obj = robjects.r("max_grad")
            
            # More robust extraction with type checking and null checks
            conv_code = float(conv_code_obj[0]) if conv_code_obj and len(conv_code_obj) > 0 and conv_code_obj[0] is not None else 1.0
            is_singular = bool(is_singular_obj[0]) if is_singular_obj and len(is_singular_obj) > 0 and is_singular_obj[0] is not None else True
            has_warnings = bool(has_warnings_obj[0]) if has_warnings_obj and len(has_warnings_obj) > 0 and has_warnings_obj[0] is not None else True
            max_grad = float(max_grad_obj[0]) if max_grad_obj and len(max_grad_obj) > 0 and max_grad_obj[0] is not None else 999.0
        except (IndexError, TypeError, ValueError, Exception) as e:
            print(f"Error accessing RT convergence diagnostics: {e}")
            conv_code = 1.0  # Assume convergence failure
            is_singular = True
            has_warnings = True
            max_grad = 999.0
        
        print(f"RT model diagnostics: conv_code={conv_code}, singular={is_singular}, warnings={has_warnings}, max_grad={max_grad:.6f}")
        
        # Model is considered converged if basic criteria are met (relax max_grad threshold)
        if conv_code == 0 and not is_singular and max_grad < 1.0:  # More lenient gradient threshold
            print("Full RT model converged successfully")
            rt_model_name = "MRT_RT_full_model"
            model_converged = True
        else:
            print(f"Full RT model has convergence issues - will try simplified model")
            model_converged = False
            
    except Exception as e:
        print(f"Full RT model failed with error: {robjects.r.geterrmessage()}")
    
    # If full model didn't converge properly, try simplified model
    if not model_converged:
        try:
            robjects.r("""
            mrt_rt_model <- lmerTest::lmer(log_rt ~ MRT_angle_degrees_scaled + (1 | participantId), 
                                data = mrt_rt_data, REML = FALSE)
            """)
            print("RT random intercept model fitted")
            rt_model_name = "MRT_RT_intercept_only_model"
        except Exception as e:
            print(f"Simplified RT model also failed: {robjects.r.geterrmessage()}")
            # Try different optimizer
            robjects.r("""
            mrt_rt_model <- lmerTest::lmer(log_rt ~ MRT_angle_degrees_scaled + (1 | participantId), 
                                data = mrt_rt_data, REML = FALSE,
                                control = lmerControl(optimizer = "Nelder_Mead"))
            """)
            print("RT model fitted with Nelder_Mead optimizer")
            rt_model_name = "MRT_RT_nelder_mead_model"
    
    # Extract RT model results
    robjects.r("mrt_rt_summary <- summary(mrt_rt_model)")
    
    # Convert coefficients to data frame in R before extracting
    robjects.r("mrt_rt_coef_df <- as.data.frame(coef(mrt_rt_summary))")
    
    try:
        robjects.r("mrt_rt_confint <- as.data.frame(confint(mrt_rt_model, method='Wald'))")
        # Print CI structure for debugging
        robjects.r("print('RT CI row names:'); print(rownames(mrt_rt_confint))")
        robjects.r("print('RT CI column names:'); print(colnames(mrt_rt_confint))")
        rt_ci_available = True
    except Exception as e:
        print(f"Could not compute RT model confidence intervals: {robjects.r.geterrmessage()}")
        rt_ci_available = False
    
    coef_df = pandas2ri.rpy2py(robjects.r("mrt_rt_coef_df"))
    print(f"RT coefficient dataframe shape: {coef_df.shape}")
    print(f"RT coefficient dataframe columns: {list(coef_df.columns)}")
    
    # Extract p-values if available
    try:
        if coef_df.shape[1] > 4:
            p_values = coef_df.iloc[:, 4]
            rt_p_values_available = True
        else:
            p_values = np.array([np.nan] * len(coef_df))
            rt_p_values_available = False
    except Exception as e:
        print(f"Error extracting RT p-values: {e}")
        p_values = np.array([np.nan] * len(coef_df))
        rt_p_values_available = False
    
    if rt_ci_available:
        ci_df = pandas2ri.rpy2py(robjects.r("mrt_rt_confint"))
        print(f"RT CI dataframe shape: {ci_df.shape}")
        print(f"RT CI dataframe columns: {list(ci_df.columns)}")
    
    # Iterate using R-generated effect names from coef_df.index
    for r_effect_name in coef_df.index:
        estimate = coef_df.loc[r_effect_name, coef_df.columns[0]]
        std_error = coef_df.loc[r_effect_name, coef_df.columns[1]]
        t_value = coef_df.loc[r_effect_name, coef_df.columns[3]] if coef_df.shape[1] > 3 else np.nan  # lmerTest: column 3 is t-value

        # Get p-value for this effect
        effect_idx = list(coef_df.index).index(r_effect_name)
        p_val = p_values[effect_idx] if rt_p_values_available and effect_idx < len(p_values) else np.nan

        # Try to extract CI from R results first
        ci_lower = np.nan
        ci_upper = np.nan

        if rt_ci_available and r_effect_name in ci_df.index:
            try:
                ci_lower = ci_df.loc[r_effect_name, ci_df.columns[0]]
                ci_upper = ci_df.loc[r_effect_name, ci_df.columns[1]]
                print(f"Found CI for RT {r_effect_name} by name: [{ci_lower:.4f}, {ci_upper:.4f}]")
            except Exception as e:
                print(f"Error extracting CI for RT {r_effect_name} by name: {e}")
                ci_lower = np.nan
                ci_upper = np.nan

        # If CI extraction failed, use normal approximation
        if np.isnan(ci_lower) or np.isnan(ci_upper):
            ci_lower = estimate - 1.96 * std_error
            ci_upper = estimate + 1.96 * std_error
            print(f"Using normal approximation CI for RT {r_effect_name}: [{ci_lower:.4f}, {ci_upper:.4f}]")

        # Adjust effect name for output (remove _scaled suffix for clarity)
        output_effect_name = r_effect_name.replace('MRT_angle_degrees_scaled', 'MRT_angle_degrees')
        
        # Adjust estimate and CI for scaled variable (multiply by 50 to get per-degree effect)
        if 'MRT_angle_degrees_scaled' in r_effect_name:
            estimate_adjusted = estimate / 50  # Convert back to per-degree effect
            ci_lower_adjusted = ci_lower / 50
            ci_upper_adjusted = ci_upper / 50
            print(f"Adjusted {output_effect_name} estimate from {estimate:.6f} to {estimate_adjusted:.6f} (per degree)")
        else:
            estimate_adjusted = estimate
            ci_lower_adjusted = ci_lower
            ci_upper_adjusted = ci_upper
        
        result = {
            'model_name': rt_model_name,
            'effect_name': output_effect_name,
            'estimate': estimate_adjusted,
            'std_error': std_error / 50 if 'MRT_angle_degrees_scaled' in r_effect_name else std_error,
            't_value': t_value,  # t-value doesn't change with scaling
            'p_value': p_val,
            'ci_lower': ci_lower_adjusted,
            'ci_upper': ci_upper_adjusted
        }
        results.append(result)
    
    # Accuracy Model
    print("Fitting accuracy model...")
    r_df_acc = pandas2ri.py2rpy(df)
    robjects.r.assign("mrt_acc_data", r_df_acc)
    robjects.r("""
    mrt_acc_data$participantId <- as.factor(mrt_acc_data$participantId)
    # Rescale MRT_angle_degrees to improve convergence (divide by 50)
    mrt_acc_data$MRT_angle_degrees_scaled <- mrt_acc_data$MRT_angle_degrees / 50
    """)
    
    # Try full model first
    model_converged = False
    try:
        robjects.r("""
        mrt_acc_model <- glmer(MRT_isCorrect ~ MRT_angle_degrees_scaled + (1 + MRT_angle_degrees_scaled | participantId), 
                              data = mrt_acc_data, family = binomial, 
                              control = glmerControl(optimizer = "bobyqa"))
        """)
        
        # Check for convergence issues more thoroughly
        robjects.r("""
        conv_code <- mrt_acc_model@optinfo$conv$opt
        is_singular <- lme4::isSingular(mrt_acc_model)
        has_warnings <- length(mrt_acc_model@optinfo$warnings) > 0
        max_grad <- max(abs(mrt_acc_model@optinfo$derivs$gradient))
        """)
        
        try:
            conv_code_obj = robjects.r("conv_code")
            is_singular_obj = robjects.r("is_singular")
            has_warnings_obj = robjects.r("has_warnings")
            max_grad_obj = robjects.r("max_grad")
            
            # More robust extraction with type checking and null checks
            conv_code = int(conv_code_obj[0]) if conv_code_obj and len(conv_code_obj) > 0 and conv_code_obj[0] is not None else 1
            is_singular = bool(is_singular_obj[0]) if is_singular_obj and len(is_singular_obj) > 0 and is_singular_obj[0] is not None else True
            has_warnings = bool(has_warnings_obj[0]) if has_warnings_obj and len(has_warnings_obj) > 0 and has_warnings_obj[0] is not None else True
            max_grad = float(max_grad_obj[0]) if max_grad_obj and len(max_grad_obj) > 0 and max_grad_obj[0] is not None else 999.0
        except (IndexError, TypeError, ValueError, Exception) as e:
            print(f"Error accessing accuracy model convergence diagnostics: {e}")
            conv_code = 1  # Assume convergence failure
            is_singular = True
            has_warnings = True
            max_grad = 999.0
        
        print(f"Accuracy model diagnostics: conv_code={conv_code}, singular={is_singular}, warnings={has_warnings}, max_grad={max_grad:.6f}")
        
        # Model is considered converged if basic criteria are met (relax max_grad threshold for glmer)
        if conv_code == 0 and not is_singular and max_grad < 1.0:  # More lenient gradient threshold for glmer
            print("Full accuracy model converged successfully")
            acc_model_name = "MRT_Accuracy_full_model"
            model_converged = True
        else:
            print(f"Full accuracy model has convergence issues - will try simplified model")
            model_converged = False
            
    except Exception as e:
        print(f"Full accuracy model failed with error: {robjects.r.geterrmessage()}")
    
    # If full model didn't converge properly, try simplified model
    if not model_converged:
        try:
            robjects.r("""
            mrt_acc_model <- glmer(MRT_isCorrect ~ MRT_angle_degrees_scaled + (1 | participantId), 
                                  data = mrt_acc_data, family = binomial,
                                  control = glmerControl(optimizer = "bobyqa"))
            """)
            print("Accuracy random intercept model fitted")
            acc_model_name = "MRT_Accuracy_intercept_only_model"
        except Exception as e:
            print(f"Simplified accuracy model also failed: {robjects.r.geterrmessage()}")
            # Try different optimizer
            robjects.r("""
            mrt_acc_model <- glmer(MRT_isCorrect ~ MRT_angle_degrees_scaled + (1 | participantId), 
                                  data = mrt_acc_data, family = binomial,
                                  control = glmerControl(optimizer = "Nelder_Mead"))
            """)
            print("Accuracy model fitted with Nelder_Mead optimizer")
            acc_model_name = "MRT_Accuracy_nelder_mead_model"
    
    # Extract accuracy model results
    robjects.r("mrt_acc_summary <- summary(mrt_acc_model)")
    
    # Convert coefficients to data frame in R before extracting
    robjects.r("mrt_acc_coef_df <- as.data.frame(coef(mrt_acc_summary))")
    
    try:
        robjects.r("mrt_acc_confint <- as.data.frame(confint(mrt_acc_model, method='Wald'))")
        # Print CI structure for debugging
        robjects.r("print('Accuracy CI row names:'); print(rownames(mrt_acc_confint))")
        robjects.r("print('Accuracy CI column names:'); print(colnames(mrt_acc_confint))")
        acc_ci_available = True
    except Exception as e:
        print(f"Could not compute accuracy model confidence intervals: {robjects.r.geterrmessage()}")
        acc_ci_available = False
    
    coef_df = pandas2ri.rpy2py(robjects.r("mrt_acc_coef_df"))
    
    # Extract p-values from glmer summary (these are typically available)
    try:
        if coef_df.shape[1] > 3:
            p_values = coef_df.iloc[:, 3]
            acc_p_values_available = True
        else:
            p_values = np.array([np.nan] * len(coef_df))
            acc_p_values_available = False
    except Exception as e:
        print(f"Error extracting accuracy p-values: {e}")
        p_values = np.array([np.nan] * len(coef_df))
        acc_p_values_available = False
    
    if acc_ci_available:
        ci_df = pandas2ri.rpy2py(robjects.r("mrt_acc_confint"))
    
    # Iterate using R-generated effect names from coef_df.index
    for r_effect_name in coef_df.index:
        estimate = coef_df.loc[r_effect_name, coef_df.columns[0]]
        std_error = coef_df.loc[r_effect_name, coef_df.columns[1]]
        t_value = coef_df.loc[r_effect_name, coef_df.columns[2]] if coef_df.shape[1] > 2 else np.nan  # glmer: column 2 is z-value

        # Get p-value for this effect
        effect_idx = list(coef_df.index).index(r_effect_name)
        p_val = p_values[effect_idx] if acc_p_values_available and effect_idx < len(p_values) else np.nan

        # Try to extract CI from R results first
        ci_lower = np.nan
        ci_upper = np.nan

        if acc_ci_available and r_effect_name in ci_df.index:
            try:
                ci_lower = ci_df.loc[r_effect_name, ci_df.columns[0]]
                ci_upper = ci_df.loc[r_effect_name, ci_df.columns[1]]
                print(f"Found CI for {r_effect_name} by name: [{ci_lower:.4f}, {ci_upper:.4f}]")
            except Exception as e:
                print(f"Error extracting CI for {r_effect_name} by name: {e}")
                ci_lower = np.nan
                ci_upper = np.nan

        # If CI extraction failed, use normal approximation
        if np.isnan(ci_lower) or np.isnan(ci_upper):
            ci_lower = estimate - 1.96 * std_error
            ci_upper = estimate + 1.96 * std_error
            print(f"Using normal approximation CI for {r_effect_name}: [{ci_lower:.4f}, {ci_upper:.4f}]")

        # Adjust effect name for output (remove _scaled suffix for clarity)
        output_effect_name = r_effect_name.replace('MRT_angle_degrees_scaled', 'MRT_angle_degrees')
        
        # Adjust estimate and CI for scaled variable (multiply by 50 to get per-degree effect)
        if 'MRT_angle_degrees_scaled' in r_effect_name:
            estimate_adjusted = estimate / 50  # Convert back to per-degree effect
            ci_lower_adjusted = ci_lower / 50
            ci_upper_adjusted = ci_upper / 50
            print(f"Adjusted {output_effect_name} estimate from {estimate:.6f} to {estimate_adjusted:.6f} (per degree)")
        else:
            estimate_adjusted = estimate
            ci_lower_adjusted = ci_lower
            ci_upper_adjusted = ci_upper
        
        result = {
            'model_name': acc_model_name,
            'effect_name': output_effect_name,
            'estimate': estimate_adjusted,
            'std_error': std_error / 50 if 'MRT_angle_degrees_scaled' in r_effect_name else std_error,
            't_value': t_value,  # t-value doesn't change with scaling
            'p_value': p_val,
            'ci_lower': ci_lower_adjusted,
            'ci_upper': ci_upper_adjusted
        }
        results.append(result)
    
    print(f"MRT models fitted with {len(results)} total effects")
    return results

def compute_correlations(vwm_slopes, mrt_slopes):
    """
    Compute correlations between VWM and MRT slopes.
    
    Parameters:
    vwm_slopes (pd.DataFrame): VWM performance metrics
    mrt_slopes (pd.DataFrame): MRT performance metrics
    
    Returns:
    list: Correlation results
    """
    print("Computing correlations...")
    
    # Print input data information
    print(f"VWM slopes data shape: {vwm_slopes.shape}")
    print(f"VWM slopes participants: {vwm_slopes['participantId'].nunique()}")
    print(f"MRT slopes data shape: {mrt_slopes.shape}")
    print(f"MRT slopes participants: {mrt_slopes['participantId'].nunique()}")
    
    # Check for required columns
    vwm_required = ['participantId', 'VWM_Error_SetSize_Slope', 'VWM_Error_Delay_Slope', 'valid_slope_calculation']
    mrt_required = ['participantId', 'MRT_RT_Angle_Slope', 'MRT_Accuracy_Angle_Slope', 'valid_slope_calculation']
    
    missing_vwm = [col for col in vwm_required if col not in vwm_slopes.columns]
    missing_mrt = [col for col in mrt_required if col not in mrt_slopes.columns]
    
    if missing_vwm:
        print(f"Warning: Missing required VWM columns: {missing_vwm}")
    if missing_mrt:
        print(f"Warning: Missing required MRT columns: {missing_mrt}")
    
    # Merge datasets
    merged = pd.merge(vwm_slopes, mrt_slopes, on='participantId', how='inner')
    
    # Filter for valid slope calculations
    if 'valid_slope_calculation_x' in merged.columns and 'valid_slope_calculation_y' in merged.columns:
        merged = merged[
            (merged['valid_slope_calculation_x'] == True) &
            (merged['valid_slope_calculation_y'] == True)
        ]
    else:
        # Handle case where column names might be different
        valid_x_col = [col for col in merged.columns if 'valid_slope_calculation' in col and '_x' in col]
        valid_y_col = [col for col in merged.columns if 'valid_slope_calculation' in col and '_y' in col]
        
        if valid_x_col and valid_y_col:
            merged = merged[
                (merged[valid_x_col[0]] == True) &
                (merged[valid_y_col[0]] == True)
            ]
        else:
            print("Warning: Could not find valid slope calculation columns. Using all data.")
    
    print(f"Merged dataset shape: {merged.shape}")
    print(f"Participants with valid slopes for both tasks: {len(merged)}")
    
    # Remove null values
    merged = merged.dropna(subset=[
        'VWM_Error_SetSize_Slope', 'VWM_Error_Delay_Slope',
        'MRT_RT_Angle_Slope', 'MRT_Accuracy_Angle_Slope'
    ])
    
    print(f"After removing null values: {merged.shape}")
    
    # Print descriptive statistics for key variables
    print("\nDescriptive statistics for key variables:")
    for col in ['VWM_Error_SetSize_Slope', 'VWM_Error_Delay_Slope', 
                'MRT_RT_Angle_Slope', 'MRT_Accuracy_Angle_Slope']:
        if col in merged.columns:
            stats = merged[col].describe()
            print(f"{col}: mean={stats['mean']:.4f}, std={stats['std']:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}")
    
    results = []
    
    # Hypothesis 1a: VWM_Error_SetSize_Slope vs MRT_RT_Angle_Slope
    print("Computing H1a correlation...")
    h1a_data = merged[['VWM_Error_SetSize_Slope', 'MRT_RT_Angle_Slope']].dropna()
    
    if len(h1a_data) >= 3:
        from scipy.stats import pearsonr
        r_h1a, p_h1a = pearsonr(h1a_data['VWM_Error_SetSize_Slope'], h1a_data['MRT_RT_Angle_Slope'])
        
        # Compute confidence interval
        n = len(h1a_data)
        if n > 3:  # Ensure we have enough data for CI calculation
            z_r = np.arctanh(r_h1a)
            se = 1 / np.sqrt(n - 3)
            z_ci = 1.96 * se
            ci_lower = np.tanh(z_r - z_ci)
            ci_upper = np.tanh(z_r + z_ci)
        else:
            print("Warning: Not enough data for confidence interval calculation in H1a")
            ci_lower = np.nan
            ci_upper = np.nan
        
        results.append({
            'hypothesis': 'H1a',
            'variable1': 'VWM_Error_SetSize_Slope',
            'variable2': 'MRT_RT_Angle_Slope',
            'correlation_r': r_h1a,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'p_value': p_h1a,
            'n_participants': n
        })
        
        print(f"H1a: r = {r_h1a:.4f}, p = {p_h1a:.4f}, n = {n}")
    else:
        print("Insufficient data for H1a correlation")
    
    # Hypothesis 1b: VWM_Error_Delay_Slope vs MRT_Accuracy_Angle_Slope
    print("Computing H1b correlation...")
    h1b_data = merged[['VWM_Error_Delay_Slope', 'MRT_Accuracy_Angle_Slope']].dropna()
    
    if len(h1b_data) >= 3:
        r_h1b, p_h1b = pearsonr(h1b_data['VWM_Error_Delay_Slope'], h1b_data['MRT_Accuracy_Angle_Slope'])
        
        # Compute confidence interval
        n = len(h1b_data)
        if n > 3:  # Ensure we have enough data for CI calculation
            z_r = np.arctanh(r_h1b)
            se = 1 / np.sqrt(n - 3)
            z_ci = 1.96 * se
            ci_lower = np.tanh(z_r - z_ci)
            ci_upper = np.tanh(z_r + z_ci)
        else:
            print("Warning: Not enough data for confidence interval calculation in H1b")
            ci_lower = np.nan
            ci_upper = np.nan
        
        results.append({
            'hypothesis': 'H1b',
            'variable1': 'VWM_Error_Delay_Slope',
            'variable2': 'MRT_Accuracy_Angle_Slope',
            'correlation_r': r_h1b,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'p_value': p_h1b,
            'n_participants': n
        })
        
        print(f"H1b: r = {r_h1b:.4f}, p = {p_h1b:.4f}, n = {n}")
    else:
        print("Insufficient data for H1b correlation")
    
    # Apply conditional Benjamini-Hochberg correction
    if len(results) > 0:
        from statsmodels.stats.multitest import multipletests

        original_p_values = [r.get('p_value', np.nan) for r in results]

        # Check if at least one p-value is significant (< 0.05)
        valid_p_values = [p for p in original_p_values if not np.isnan(p)]
        any_significant = any(p < 0.05 for p in valid_p_values) if valid_p_values else False

        if any_significant and len(valid_p_values) > 1:
            print("At least one p-value < 0.05 detected. Applying Benjamini-Hochberg FDR correction.")
            print(f"Valid p-values to correct: {valid_p_values}")
            
            # Identify indices of valid (non-NaN) p-values
            valid_indices = [i for i, p in enumerate(original_p_values) if not np.isnan(p)]
            p_values_to_correct = [original_p_values[i] for i in valid_indices]

            rejected, p_corrected_values, _, _ = multipletests(
                p_values_to_correct, alpha=0.05, method='fdr_bh'
            )

            # Distribute corrected p-values back to results
            corrected_idx = 0
            for i, result_item in enumerate(results):
                if i in valid_indices:
                    result_item['p_value_corrected'] = p_corrected_values[corrected_idx]
                    corrected_idx += 1
                else:
                    result_item['p_value_corrected'] = np.nan  # Assign NaN if original was NaN
        else:
            # No correction needed - either no significant p-values or insufficient data
            if not any_significant:
                print("No p-values < 0.05 detected. Benjamini-Hochberg correction not applied.")
            else:
                print("Only one valid p-value. Benjamini-Hochberg correction not needed.")
            
            for result_item in results:
                result_item['p_value_corrected'] = result_item.get('p_value', np.nan)

        print("Correlation p-value summary:")
        for result in results:
            if not np.isnan(result['p_value_corrected']):
                print(f"{result['hypothesis']}: p_corrected = {result['p_value_corrected']:.4f}")
            else:
                print(f"{result['hypothesis']}: p_corrected = NaN (original p-value was NaN)")
    
    return results

def main():
    """Main execution function."""
    try:
        print("Starting H1 analysis...")
        
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Import R packages
        print("Loading R packages...")
        r_base = importr('base')
        r_lme4 = safe_import_r_package('lme4')
        r_stats = importr('stats')
        
        # Try to import lmerTest for p-values
        try:
            r_lmerTest = safe_import_r_package('lmerTest')
            print("Successfully loaded lmerTest package for p-values")
        except Exception as e:
            print(f"Warning: Could not load lmerTest package: {e}")
            print("Some p-values may not be available")
        
        # Find input files
        print("Finding input files...")
        
        vwm_data_file = find_most_recent_file('outputs/VWM_cleaned_data_*.csv')
        mrt_data_file = find_most_recent_file('outputs/MRT_cleaned_data_*.csv')
        vwm_metrics_file = find_most_recent_file('outputs/VWM_performance_metrics_*.csv')
        mrt_metrics_file = find_most_recent_file('outputs/MRT_performance_metrics_*.csv')
        
        if not all([vwm_data_file, mrt_data_file, vwm_metrics_file, mrt_metrics_file]):
            print("Error: Could not find all required input files")
            return 1
        
        print(f"Found VWM data file: {vwm_data_file}")
        print(f"Found MRT data file: {mrt_data_file}")
        print(f"Found VWM metrics file: {vwm_metrics_file}")
        print(f"Found MRT metrics file: {mrt_metrics_file}")
        
        # Load and validate data
        vwm_required_cols = ['participantId', 'VWM_setSize', 'VWM_delay_s', 'VWM_error_absolute_degrees', 
                            'excluded_participant', 'valid_trial', 'isPractice']
        mrt_required_cols = ['participantId', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms',
                            'excluded_participant', 'valid_trial', 'isPractice']
        vwm_metrics_cols = ['participantId', 'VWM_Error_SetSize_Slope', 'VWM_Error_Delay_Slope', 'valid_slope_calculation']
        mrt_metrics_cols = ['participantId', 'MRT_RT_Angle_Slope', 'MRT_Accuracy_Angle_Slope', 'valid_slope_calculation']
        
        vwm_data = load_and_validate_data(vwm_data_file, vwm_required_cols)
        mrt_data = load_and_validate_data(mrt_data_file, mrt_required_cols)
        vwm_metrics = load_and_validate_data(vwm_metrics_file, vwm_metrics_cols)
        mrt_metrics = load_and_validate_data(mrt_metrics_file, mrt_metrics_cols)
        
        if any(df is None for df in [vwm_data, mrt_data, vwm_metrics, mrt_metrics]):
            print("Error: Failed to load required data files")
            return 1
        
        # Filter data
        vwm_filtered = filter_vwm_data(vwm_data)
        mrt_filtered = filter_mrt_data(mrt_data)
        
        if vwm_filtered.empty or mrt_filtered.empty:
            print("Error: No data remaining after filtering")
            return 1
        
        # Fit mixed-effects models
        print("\n=== FITTING MIXED-EFFECTS MODELS ===")
        mixed_results = []
        
        vwm_results = fit_vwm_mixed_model(vwm_filtered, r_base, r_lme4)
        mixed_results.extend(vwm_results)
        
        mrt_results = fit_mrt_mixed_models(mrt_filtered, r_base, r_lme4)
        mixed_results.extend(mrt_results)
        
        # Compute correlations
        print("\n=== COMPUTING CORRELATIONS ===")
        correlation_results = compute_correlations(vwm_metrics, mrt_metrics)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save mixed-effects results
        if mixed_results:
            mixed_df = pd.DataFrame(mixed_results)
            
            # Verify all required columns are present
            required_mixed_cols = ['model_name', 'effect_name', 'estimate', 'std_error', 
                                  't_value', 'p_value', 'ci_lower', 'ci_upper']
            for col in required_mixed_cols:
                if col not in mixed_df.columns:
                    print(f"Warning: Missing required column '{col}' in mixed effects results. Adding empty column.")
                    mixed_df[col] = np.nan
            
            # Ensure all columns are in the right order
            mixed_df = mixed_df[required_mixed_cols]
            
            mixed_output_file = f'outputs/H1_mixed_effects_results_{timestamp}.csv'
            mixed_df.to_csv(mixed_output_file, index=False)
            print(f"Saved mixed-effects results to: {mixed_output_file}")
            print("Mixed-effects results columns:", list(mixed_df.columns))
            print("First 2 rows of mixed-effects results:")
            print(mixed_df.head(2).to_string())
        else:
            print("Warning: No mixed-effects results to save")
        
        # Save correlation results
        if correlation_results:
            corr_df = pd.DataFrame(correlation_results)
            
            # Verify all required columns are present in correct order
            required_corr_cols = ['hypothesis', 'variable1', 'variable2', 'correlation_r', 
                                 'ci_lower', 'ci_upper', 'p_value', 'p_value_corrected', 
                                 'n_participants']
            
            final_corr_cols = []
            for col in required_corr_cols:
                if col in corr_df.columns:
                    final_corr_cols.append(col)
                else:
                    print(f"Warning: Missing required column '{col}' in correlation results. Adding empty column.")
                    corr_df[col] = np.nan
                    final_corr_cols.append(col)
            
            # Add any extra columns at the end
            final_corr_cols.extend([col for col in corr_df.columns if col not in final_corr_cols])
            corr_df = corr_df[final_corr_cols]
            
            corr_output_file = f'outputs/H1_correlation_results_{timestamp}.csv'
            corr_df.to_csv(corr_output_file, index=False)
            print(f"Saved correlation results to: {corr_output_file}")
            print("Correlation results columns:", list(corr_df.columns))
            print("First 2 rows of correlation results:")
            print(corr_df.head(2).to_string())
        else:
            print("Warning: No correlation results to save")
        
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
