#!/usr/bin/env python3
"""
Mixed-effects modeling script for Mental Rotation Task (MRT) data analysis.
This script processes cognitive summary metrics and fits linear mixed-effects models
using R's lme4 package via rpy2.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
from scipy.stats import t

# Import R interface
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter

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
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def create_output_directory():
    """
    Create outputs directory if it doesn't exist.
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")

def load_and_validate_data(filepath):
    """
    Load and validate the input CSV file.
    
    Parameters:
    filepath (str): Path to the input CSV file
    
    Returns:
    pd.DataFrame: Loaded and validated dataframe
    """
    print(f"Loading data from: {filepath}")
    
    # Required columns
    required_columns = [
        'participantId', 'kappa_concentration', 
        'MRT_accuracy_0deg', 'MRT_accuracy_50deg', 'MRT_accuracy_100deg', 'MRT_accuracy_150deg',
        'MRT_logRT_0deg', 'MRT_logRT_50deg', 'MRT_logRT_100deg', 'MRT_logRT_150deg',
        'sufficient_data_all_angles'
    ]
    
    try:
        df = pd.read_csv(filepath)
        print(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        
        # Print all columns
        print("All columns in dataset:")
        print(df.columns.tolist())
        
        # Print first 3 rows
        print("\nFirst 3 rows:")
        print(df.head(3))
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return None
            
        # Print unique values for key experimental design parameters
        print("\nUnique values for sufficient_data_all_angles:")
        print(df['sufficient_data_all_angles'].unique())
        
        # Print data types for measured variables
        print("\nData types for measured variables:")
        print(f"kappa_concentration: {df['kappa_concentration'].dtype}")
        for angle in ['0deg', '50deg', '100deg', '150deg']:
            print(f"MRT_accuracy_{angle}: {df[f'MRT_accuracy_{angle}'].dtype}")
            print(f"MRT_logRT_{angle}: {df[f'MRT_logRT_{angle}'].dtype}")
        
        return df
        
    except Exception as e:
        print(f"ERROR: Failed to load data: {e}")
        return None

def reshape_to_long_format(df):
    """
    Reshape data from wide to long format for mixed-effects modeling.
    
    Parameters:
    df (pd.DataFrame): Wide format dataframe
    
    Returns:
    pd.DataFrame: Long format dataframe
    """
    print("\nReshaping data to long format...")
    
    # Filter for participants with sufficient data
    df_filtered = df[df['sufficient_data_all_angles'] == True].copy()
    print(f"Participants with sufficient data: {len(df_filtered)}")
    
    if len(df_filtered) == 0:
        print("ERROR: No participants with sufficient data")
        return None
    
    # Calculate centered kappa concentration
    kappa_mean = df_filtered['kappa_concentration'].mean()
    print(f"Sample mean of kappa_concentration: {kappa_mean}")
    df_filtered['kappa_centered'] = df_filtered['kappa_concentration'] - kappa_mean
    
    # Create long format data
    long_data = []
    
    angles = [0, 50, 100, 150]
    
    for _, row in df_filtered.iterrows():
        participant_id = row['participantId']
        kappa_concentration = row['kappa_concentration']
        kappa_centered = row['kappa_centered']
        
        for angle in angles:
            angle_str = f"{angle}deg"
            accuracy = row[f'MRT_accuracy_{angle_str}']
            log_rt = row[f'MRT_logRT_{angle_str}']
            
            long_data.append({
                'participantId': participant_id,
                'rotation_angle_degrees': angle,
                'rotation_angle_factor': f"angle_{angle}",
                'MRT_accuracy': accuracy,
                'MRT_log_RT': log_rt,
                'kappa_concentration': kappa_concentration,
                'kappa_centered': kappa_centered
            })
    
    long_df = pd.DataFrame(long_data)

    print(f"rotation_angle_factor data type: {long_df['rotation_angle_factor'].dtype}")
    print(f"rotation_angle_factor sample values: {long_df['rotation_angle_factor'].head(2).tolist()}")

    print(f"Long format data shape: {long_df.shape}")
    print("\nLong format data columns:")
    print(long_df.columns.tolist())
    print("\nFirst 2 rows of long format data:")
    print(long_df.head(2))
    
    # Print unique values for rotation angles
    print("\nUnique rotation_angle_degrees values:")
    print(sorted(long_df['rotation_angle_degrees'].unique()))
    print("Unique rotation_angle_factor values:")
    print(sorted(long_df['rotation_angle_factor'].unique()))
    
    return long_df

def setup_r_environment():
    """
    Set up R environment and import required packages.
    
    Returns:
    tuple: R objects for lme4, car, stats, and base packages
    """
    print("\nSetting up R environment...")
    
    # DO NOT activate pandas2ri globally - use context managers instead
    
    try:
        # Import base R packages first
        utils = importr('utils')
        base = importr('base')
        
        # Check and install required packages
        print("Checking and installing required R packages...")
        ro.r('''
        required_packages <- c("lme4", "car", "lmerTest", "emmeans")
        for (pkg in required_packages) {
            if (!require(pkg, character.only = TRUE)) {
                install.packages(pkg, repos = "https://cloud.r-project.org/")
                library(pkg, character.only = TRUE)
            }
        }
        ''')
        
        # Import R packages
        lme4 = importr('lme4')
        car = importr('car')
        lmerTest = importr('lmerTest')
        stats = importr('stats')
        emmeans = importr('emmeans')
        
        print("Successfully imported R packages: lme4, car, lmerTest, emmeans, stats")
        return lme4, car, stats, base, lmerTest, emmeans
        
    except Exception as e:
        print(f"ERROR: Failed to import R packages: {e}")
        return None, None, None, None, None, None

def extract_simple_effects(model_name, model_num):
    """Extract simple effects (slopes) for significant interactions."""
    print(f"Extracting simple effects for {model_name}...")
    try:
        ro.r(f'simple_effects <- summary(emmeans::emtrends(model{model_num}, ~ rotation_angle_factor, var = "kappa_centered"), infer = c(TRUE, TRUE))')
        
        with localconverter(ro.default_converter + pandas2ri.converter):
            simple_table = ro.conversion.rpy2py(ro.r('as.data.frame(simple_effects)'))
        
        print("Simple effects table columns:")
        print(simple_table.columns.tolist())
        print("Simple effects table structure:")
        print(simple_table.head())
        
        results = []
        for idx, row in simple_table.iterrows():
            # Flexible column name matching for t-value
            t_col = 't.ratio' if 't.ratio' in simple_table.columns else ('z.ratio' if 'z.ratio' in simple_table.columns else None)
            # Flexible column name for trend
            trend_col = 'kappa_centered.trend' if 'kappa_centered.trend' in simple_table.columns else ('trend' if 'trend' in simple_table.columns else None)
            # SE column
            se_col = 'SE' if 'SE' in simple_table.columns else None
            # Flexible column name matching for p-value
            p_col = 'p.value' if 'p.value' in simple_table.columns else ('p.value.' if 'p.value.' in simple_table.columns else None)
            # Flexible column name matching for confidence intervals
            lower_col = 'lower.CL' if 'lower.CL' in simple_table.columns else ('asymp.LCL' if 'asymp.LCL' in simple_table.columns else None)
            upper_col = 'upper.CL' if 'upper.CL' in simple_table.columns else ('asymp.UCL' if 'asymp.UCL' in simple_table.columns else None)
            # rotation_angle_factor column
            angle_col = 'rotation_angle_factor' if 'rotation_angle_factor' in simple_table.columns else None

            # Extract values
            if trend_col is None:
                print(f"Warning: Could not find trend column in emmeans output")
                estimate = np.nan
            else:
                estimate = float(row[trend_col])
            if se_col is None:
                print(f"Warning: Could not find SE column in emmeans output")
                std_error = np.nan
            else:
                std_error = float(row[se_col])
            if t_col is None:
                print(f"Warning: Could not find t.ratio or z.ratio column in emmeans output")
                t_value = np.nan
            else:
                t_value = float(row[t_col])
            if p_col is None:
                print(f"Warning: Could not find p.value column in emmeans output")
                p_value = np.nan
            else:
                p_value = float(row[p_col])
            if lower_col is None or upper_col is None:
                print(f"Warning: Could not find lower.CL or upper.CL columns in emmeans output")
                ci_lower = np.nan
                ci_upper = np.nan
            else:
                ci_lower = float(row[lower_col])
                ci_upper = float(row[upper_col])
            if angle_col is None:
                print(f"Warning: Could not find rotation_angle_factor column in emmeans output")
                angle_val = "unknown"
            else:
                angle_val = row[angle_col]

            result = {
                'model_name': model_name,
                'effect_type': 'simple_effect',
                'parameter': f"kappa_centered_at_{angle_val}deg",
                'estimate': estimate,
                'std_error': std_error,
                't_value': t_value,
                'p_value': p_value,
                'confidence_interval_lower': ci_lower,
                'confidence_interval_upper': ci_upper
            }
            results.append(result)
        
        print(f"Extracted {len(results)} simple effects for {model_name}")
        return results
        
    except Exception as e:
        print(f"ERROR: Failed to extract simple effects for {model_name}: {e}")
        return []

def fit_mixed_effects_models(long_df, lme4, car, stats, lmerTest, emmeans):
    """
    Fit linear mixed-effects models for MRT accuracy and log reaction time.
    
    Parameters:
    long_df (pd.DataFrame): Long format data
    lme4: R lme4 package
    car: R car package  
    stats: R stats package
    lmerTest: R lmerTest package
    emmeans: R emmeans package
    
    Returns:
    tuple: (model1_results, model2_results, model1_anova, model2_anova, model_fit_stats, simple_effects_results)
    """
    print("\nFitting mixed-effects models...")
    
    # Convert dataframe to R
    with localconverter(ro.default_converter + pandas2ri.converter):
        r_df = ro.conversion.py2rpy(long_df)
    
    # Assign to R global environment
    ro.globalenv['data'] = r_df
    
    # Model 1: MRT Accuracy
    print("\nFitting Model 1: MRT Accuracy")
    try:
        ro.r('''
        model1 <- lmerTest::lmer(MRT_accuracy ~ kappa_centered * rotation_angle_factor + (1|participantId), 
                       data = data, REML = FALSE)
        ''')
        
        # Get model summary
        model1_summary = ro.r('summary(model1)')
        print("Model 1 fitted successfully")
        
    except Exception as e:
        print(f"ERROR: Failed to fit Model 1: {e}")
        return None, None, None, None, None, []
    
    # Model 2: MRT Log Reaction Time  
    print("\nFitting Model 2: MRT Log Reaction Time")
    try:
        ro.r('''
        model2 <- lmerTest::lmer(MRT_log_RT ~ kappa_centered * rotation_angle_factor + (1|participantId), 
                       data = data, REML = FALSE)
        ''')
        
        # Get model summary
        model2_summary = ro.r('summary(model2)')
        print("Model 2 fitted successfully")
        
    except Exception as e:
        print(f"ERROR: Failed to fit Model 2: {e}")
        return None, None, None, None, None, []
    
    # Test effects using lmerTest::anova (Type III)
    print("\nTesting effects using lmerTest::anova...")
    try:
        ro.r('anova1 <- anova(model1, type = 3)')
        ro.r('anova2 <- anova(model2, type = 3)')
        print("Type III ANOVA (lmerTest) completed successfully")
    except Exception as e:
        print(f"ERROR: Failed to compute ANOVA: {e}")
    
    # Extract model results
    model1_results = extract_model_results("MRT_Accuracy", 1)
    model2_results = extract_model_results("MRT_LogRT", 2)
    
    # Extract ANOVA results
    model1_anova = extract_anova_results("MRT_Accuracy", 1)
    model2_anova = extract_anova_results("MRT_LogRT", 2)
    
    # Extract model fit statistics
    model_fit_stats = extract_model_fit_statistics()
    
    # Check for significant interactions and perform simple effects if needed
    simple_effects_results = []
    for anova_results, model_name, model_num in [(model1_anova, "MRT_Accuracy", 1), (model2_anova, "MRT_LogRT", 2)]:
        for result in anova_results:
            if 'interaction' in result['parameter'].lower() or ':' in result['parameter']:
                if result['p_value'] < 0.05:
                    print(f"Significant interaction found in {model_name} (p = {result['p_value']:.6f})")
                    simple_effects = extract_simple_effects(model_name, model_num)
                    simple_effects_results.extend(simple_effects)

    return model1_results, model2_results, model1_anova, model2_anova, model_fit_stats, simple_effects_results

def extract_model_results(model_name, model_num):
    """
    Extract fixed effects results from fitted model.
    
    Parameters:
    model_name (str): Name of the model
    model_num (int): Model number (1 or 2)
    
    Returns:
    list: List of dictionaries containing model results
    """
    print(f"\nExtracting results for {model_name}...")
    
    try:
        # Get fixed effects coefficients and confidence intervals using proper R conversion
        with localconverter(ro.default_converter + pandas2ri.converter):
            coef_table = ro.conversion.rpy2py(ro.r(f'as.data.frame(summary(model{model_num})$coefficients)'))
            conf_int = ro.conversion.rpy2py(ro.r(f'as.data.frame(confint(model{model_num}, parm=\"beta_\"))'))
        
        print(f"Coefficient table shape: {coef_table.shape}")
        print("Coefficient table:")
        print(coef_table)
        
        results = []
        
        # Process each coefficient with robust parameter matching
        for param in coef_table.index:
            row = coef_table.loc[param]
            
            # Extract values with proper column names from lmerTest output
            estimate = float(row['Estimate'])
            std_error = float(row['Std. Error'])
            t_value = float(row['t value'])
            p_value = float(row['Pr(>|t|)'])  # lmerTest provides p-values directly
            
            # Get confidence intervals by matching parameter names
            try:
                ci_lower = float(conf_int.loc[param, '2.5 %'])
                ci_upper = float(conf_int.loc[param, '97.5 %'])
            except (KeyError, IndexError):
                print(f"Warning: Could not find confidence intervals for parameter {param}")
                ci_lower = np.nan
                ci_upper = np.nan
            
            result = {
                'model_name': model_name,
                'effect_type': 'fixed',
                'parameter': str(param),
                'estimate': estimate,
                'std_error': std_error,
                't_value': t_value,
                'p_value': p_value,
                'confidence_interval_lower': ci_lower,
                'confidence_interval_upper': ci_upper
            }
            results.append(result)
        
        print(f"Extracted {len(results)} fixed effects for {model_name}")
        return results
        
    except Exception as e:
        print(f"ERROR: Failed to extract results for {model_name}: {e}")
        return []

def extract_anova_results(model_name, model_num):
    """
    Extract Type III ANOVA results from fitted model.
    
    Parameters:
    model_name (str): Name of the model
    model_num (int): Model number (1 or 2)
    
    Returns:
    list: List of dictionaries containing ANOVA results
    """
    print(f"\nExtracting ANOVA results for {model_name}...")
    
    try:
        # Get Type III ANOVA results
        with localconverter(ro.default_converter + pandas2ri.converter):
            anova_table = ro.conversion.rpy2py(ro.r(f'as.data.frame(anova{model_num})'))
        
        print(f"ANOVA table shape: {anova_table.shape}")
        print("ANOVA table:")
        print(anova_table)
        
        results = []
        
        # Process each effect in the ANOVA table
        for effect in anova_table.index:
            row = anova_table.loc[effect]
            
            result = {
                'model_name': model_name,
                'parameter': str(effect),
                'sum_sq': float(row['Sum Sq']) if 'Sum Sq' in row and not pd.isna(row['Sum Sq']) else np.nan,
                'mean_sq': float(row['Mean Sq']) if 'Mean Sq' in row and not pd.isna(row['Mean Sq']) else np.nan,
                'df_num': int(row['NumDF']) if 'NumDF' in row and not pd.isna(row['NumDF']) else np.nan,
                'df_den': float(row['DenDF']) if 'DenDF' in row and not pd.isna(row['DenDF']) else np.nan,
                'f_value': float(row['F value']) if 'F value' in row and not pd.isna(row['F value']) else np.nan,
                'p_value': float(row['Pr(>F)']) if 'Pr(>F)' in row and not pd.isna(row['Pr(>F)']) else np.nan
            }
            results.append(result)
        
        print(f"Extracted {len(results)} ANOVA effects for {model_name}")
        return results
        
    except Exception as e:
        print(f"ERROR: Failed to extract ANOVA results for {model_name}: {e}")
        return []

def extract_model_fit_statistics():
    """
    Extract model fit statistics for both models.
    
    Returns:
    list: List of dictionaries containing fit statistics
    """
    print("\nExtracting model fit statistics...")
    
    fit_stats = []
    
    for model_num, model_name in [(1, "MRT_Accuracy"), (2, "MRT_LogRT")]:
        try:
            # Get AIC, BIC, log-likelihood
            ro.r(f'aic_val <- AIC(model{model_num})')
            ro.r(f'bic_val <- BIC(model{model_num})')
            ro.r(f'loglik_val <- logLik(model{model_num})')
            
            # Calculate proper residual degrees of freedom for mixed models
            # Calculate proper residual degrees of freedom: nobs - n_fixef
            ro.r(f'n_obs <- nobs(model{model_num})')
            ro.r(f'n_fixed <- length(fixef(model{model_num}))')
            ro.r(f'df_resid_calc <- n_obs - n_fixed')
            
            # Get variance components
            ro.r(f'var_comp <- as.data.frame(VarCorr(model{model_num}))')
            
            with localconverter(ro.default_converter + pandas2ri.converter):
                aic_val = ro.conversion.rpy2py(ro.r('aic_val'))[0]
                bic_val = ro.conversion.rpy2py(ro.r('bic_val'))[0]
                loglik_val = ro.conversion.rpy2py(ro.r('loglik_val'))[0]
                df_resid = ro.conversion.rpy2py(ro.r('df_resid_calc'))[0]
                var_comp = ro.conversion.rpy2py(ro.r('var_comp'))
            
            print(f"Variance components for {model_name}:")
            print(var_comp)
            
            # Extract variance components by group name (robust approach)
            random_intercept_var = np.nan
            residual_var = np.nan
            
            if len(var_comp) > 0:
                # Look for participantId group (random intercept)
                participant_rows = var_comp[var_comp['grp'] == 'participantId']
                if len(participant_rows) > 0:
                    random_intercept_var = float(participant_rows.iloc[0]['vcov'])
                
                # Look for Residual group
                residual_rows = var_comp[var_comp['grp'] == 'Residual']
                if len(residual_rows) > 0:
                    residual_var = float(residual_rows.iloc[0]['vcov'])
            
            stat = {
                'model_name': model_name,
                'AIC': float(aic_val),
                'BIC': float(bic_val), 
                'log_likelihood': float(loglik_val),
                'df_residual': int(df_resid),
                'random_intercept_variance': float(random_intercept_var),
                'residual_variance': float(residual_var)
            }
            fit_stats.append(stat)
            
            print(f"Extracted fit statistics for {model_name}")
            
        except Exception as e:
            print(f"ERROR: Failed to extract fit statistics for {model_name}: {e}")
    
    return fit_stats

def perform_model_diagnostics():
    """
    Perform model diagnostics including residual analysis.
    """
    print("\nPerforming model diagnostics...")
    
    try:
        # Residual analysis for both models
        for model_num, model_name in [(1, "MRT_Accuracy"), (2, "MRT_LogRT")]:
            print(f"\nDiagnostics for {model_name}:")
            
            # Get residuals
            ro.r(f'resid{model_num} <- residuals(model{model_num})')
            ro.r(f'fitted{model_num} <- fitted(model{model_num})')
            
            # Shapiro-Wilk test for normality (sample if too many observations)
            ro.r(f'''
            if(length(resid{model_num}) > 5000) {{
                resid_sample <- sample(resid{model_num}, 5000)
            }} else {{
                resid_sample <- resid{model_num}
            }}
            shapiro_test <- shapiro.test(resid_sample)
            ''')
            
            shapiro_result = ro.r('shapiro_test')
            print(f"Shapiro-Wilk test p-value: {shapiro_result.rx2('p.value')[0]}")
            
            # Get residual statistics
            ro.r(f'resid_summary <- summary(resid{model_num})')
            resid_summary = ro.r('resid_summary')
            print(f"Residual summary: {resid_summary}")
            
    except Exception as e:
        print(f"ERROR: Failed to perform diagnostics: {e}")

def save_results(model1_results, model2_results, model1_anova, model2_anova, model_fit_stats, simple_effects_results, long_df):
    """
    Save all results to CSV files.
    
    Parameters:
    model1_results (list): Model 1 fixed effects results
    model2_results (list): Model 2 fixed effects results
    model1_anova (list): Model 1 ANOVA results
    model2_anova (list): Model 2 ANOVA results
    model_fit_stats (list): Model fit statistics
    simple_effects_results (list): Simple effects results
    long_df (pd.DataFrame): Long format data
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save fixed effects and simple effects results
    all_fixed_results = model1_results + model2_results + simple_effects_results
    if all_fixed_results:
        results_df = pd.DataFrame(all_fixed_results)
        results_file = f"outputs/MRT_mixed_effects_results_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        print(f"\nSaved fixed effects results to: {results_file}")
        print("Fixed effects results columns:")
        print(results_df.columns.tolist())
        print("First 2 rows of fixed effects results:")
        print(results_df.head(2))
    
    # Save ANOVA results
    all_anova_results = model1_anova + model2_anova
    if all_anova_results:
        anova_df = pd.DataFrame(all_anova_results)
        anova_file = f"outputs/MRT_anova_results_{timestamp}.csv"
        anova_df.to_csv(anova_file, index=False)
        print(f"\nSaved ANOVA results to: {anova_file}")
        print("ANOVA results columns:")
        print(anova_df.columns.tolist())
        print("First 2 rows of ANOVA results:")
        print(anova_df.head(2))
    
    # Save model fit statistics
    if model_fit_stats:
        fit_stats_df = pd.DataFrame(model_fit_stats)
        fit_stats_file = f"outputs/MRT_model_fit_statistics_{timestamp}.csv"
        fit_stats_df.to_csv(fit_stats_file, index=False)
        print(f"\nSaved model fit statistics to: {fit_stats_file}")
        print("Fit statistics columns:")
        print(fit_stats_df.columns.tolist())
        print("First 2 rows of fit statistics:")
        print(fit_stats_df.head(2))
    
    # Save long format data
    long_df_to_save = long_df.copy()
    long_df_to_save['rotation_angle_factor'] = long_df_to_save['rotation_angle_factor'].astype(str)
    print(f"Final rotation_angle_factor data type before save: {long_df_to_save['rotation_angle_factor'].dtype}")
    print(f"Final rotation_angle_factor sample values before save: {long_df_to_save['rotation_angle_factor'].head(2).tolist()}")
    print(f"After explicit conversion - rotation_angle_factor data type: {long_df_to_save['rotation_angle_factor'].dtype}")
    print(f"After explicit conversion - rotation_angle_factor sample values: {long_df_to_save['rotation_angle_factor'].head(2).tolist()}")
    long_data_file = f"outputs/MRT_long_format_data_{timestamp}.csv"
    long_df_to_save.to_csv(long_data_file, index=False)
    print(f"\nSaved long format data to: {long_data_file}")
    print("Long format data columns:")
    print(long_df_to_save.columns.tolist())
    print("First 2 rows of long format data:")
    print(long_df_to_save.head(2))

def main():
    """
    Main function to execute the mixed-effects modeling analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT mixed-effects modeling analysis...")
        
        # Create output directory
        create_output_directory()
        
        # Find and load input file
        input_pattern = "outputs/cognitive_summary_metrics_*.csv"
        input_file = find_latest_file(input_pattern)
        
        if not input_file:
            print(f"ERROR: No input file found matching pattern: {input_pattern}")
            return 1
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            return 1
        
        # Reshape to long format
        long_df = reshape_to_long_format(df)
        if long_df is None:
            return 1
        
        # Set up R environment
        lme4, car, stats, base, lmerTest, emmeans = setup_r_environment()
        if lme4 is None:
            return 1
        
        # Fit mixed-effects models
        model1_results, model2_results, model1_anova, model2_anova, model_fit_stats, simple_effects_results = fit_mixed_effects_models(
            long_df, lme4, car, stats, lmerTest, emmeans)
        
        if model1_results is None:
            return 1
        
        # Perform model diagnostics
        perform_model_diagnostics()
        
        # Save results
        save_results(model1_results, model2_results, model1_anova, model2_anova, model_fit_stats, simple_effects_results, long_df)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Script failed with exception: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
