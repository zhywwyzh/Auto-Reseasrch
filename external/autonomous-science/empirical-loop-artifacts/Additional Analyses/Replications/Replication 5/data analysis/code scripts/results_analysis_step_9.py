import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import R interface
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, numpy2ri
from rpy2.robjects.conversion import localconverter
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
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def prepare_augmented_datasets():
    """
    Prepare augmented datasets with centered covariates for MRT and VVIQ2 analyses.
    
    Returns:
    tuple: (mrt_augmented_df, vviq2_augmented_df) DataFrames with centered covariates
    """
    print("=== PREPARING AUGMENTED DATASETS ===")
    
    # Find input files
    cognitive_file = find_latest_file("outputs/cognitive_summary_metrics_*.csv")
    mrt_file = find_latest_file("outputs/MRT_long_format_data_*.csv")
    vviq2_file = find_latest_file("outputs/VVIQ2_analysis_dataset_*.csv")
    
    print(f"Found cognitive metrics file: {cognitive_file}")
    print(f"Found MRT file: {mrt_file}")
    print(f"Found VVIQ2 file: {vviq2_file}")
    
    if not all([cognitive_file, mrt_file, vviq2_file]):
        raise FileNotFoundError("One or more required input files not found")
    
    # Load datasets
    cognitive_df = pd.read_csv(cognitive_file)
    mrt_df = pd.read_csv(mrt_file)
    vviq2_df = pd.read_csv(vviq2_file)
    
    print("\n=== COGNITIVE METRICS DATASET ===")
    print("Columns:", cognitive_df.columns.tolist())
    print("First 3 rows:")
    print(cognitive_df.head(3))
    print(f"Shape: {cognitive_df.shape}")
    
    print("\n=== MRT DATASET ===")
    print("Columns:", mrt_df.columns.tolist())
    print("First 3 rows:")
    print(mrt_df.head(3))
    print(f"Shape: {mrt_df.shape}")
    print("Unique rotation_angle_factor values:", mrt_df['rotation_angle_factor'].unique())
    
    print("\n=== VVIQ2 DATASET ===")
    print("Columns:", vviq2_df.columns.tolist())
    print("First 3 rows:")
    print(vviq2_df.head(3))
    print(f"Shape: {vviq2_df.shape}")
    
    # Define covariates to center
    covariates_to_center = [
        'VWM_mean_absolute_error',
        'VWM_error_SD', 
        'VWM_overall_accuracy',
        'VWM_RT_variability_CV',
        'MRT_RT_variability_CV',
        'focus_loss_instances',
        'focus_loss_duration_ms'
    ]
    
    print("\n=== CALCULATING SAMPLE MEANS AND STANDARDIZING COVARIATES ===")
    
    # Calculate sample means and mean-center covariates
    for covariate in covariates_to_center:
        if covariate in cognitive_df.columns:
            sample_mean = cognitive_df[covariate].mean()
            centered_name = f"{covariate}_centered"
            # Mean-center instead of z-score
            cognitive_df[centered_name] = cognitive_df[covariate] - sample_mean
            print(f"{covariate}: mean = {sample_mean:.4f}")
        else:
            print(f"Warning: {covariate} not found in cognitive metrics")
    
    print("\nCognitive dataset with centered variables:")
    print("Columns:", cognitive_df.columns.tolist())
    print("First 2 rows:")
    print(cognitive_df.head(2))
    
    # Merge MRT data with cognitive metrics
    print("\n=== MERGING MRT DATA WITH COGNITIVE METRICS ===")
    mrt_augmented = mrt_df.merge(cognitive_df, on='participantId', how='inner')
    print(f"MRT merged dataset shape: {mrt_augmented.shape}")
    print("Columns:", mrt_augmented.columns.tolist())
    print("First 2 rows:")
    print(mrt_augmented.head(2))
    
    # Merge VVIQ2 data with cognitive metrics  
    print("\n=== MERGING VVIQ2 DATA WITH COGNITIVE METRICS ===")
    vviq2_augmented = vviq2_df.merge(cognitive_df, on='participantId', how='inner')
    print(f"VVIQ2 merged dataset shape: {vviq2_augmented.shape}")
    print("Columns:", vviq2_augmented.columns.tolist())
    print("First 2 rows:")
    print(vviq2_augmented.head(2))
    
    return mrt_augmented, vviq2_augmented

def fit_mrt_mixed_effects_models(mrt_data):
    """
    Fit baseline and augmented mixed-effects models for MRT data using R lme4.
    
    Parameters:
    mrt_data (DataFrame): Augmented MRT dataset with centered covariates
    
    Returns:
    dict: Dictionary containing model results and comparison statistics
    """
    print("\n=== FITTING MRT MIXED-EFFECTS MODELS ===")
    
    # Import R packages
    lme4 = importr('lme4')
    lmerTest = importr('lmerTest')
    base = importr('base')
    stats = importr('stats')
    
    # Convert data to R
    with localconverter(ro.default_converter + pandas2ri.converter):
        r_data = ro.conversion.py2rpy(mrt_data)
    
    print("Data converted to R successfully")
    print(f"R data dimensions: {ro.r('dim')(r_data)}")
    
    # Define covariate terms
    covariate_terms = " + ".join([
        "VWM_mean_absolute_error_centered",
        "VWM_error_SD_centered", 
        "VWM_overall_accuracy_centered",
        "VWM_RT_variability_CV_centered",
        "MRT_RT_variability_CV_centered",
        "focus_loss_instances_centered",
        "focus_loss_duration_ms_centered"
    ])
    
    results = {}
    
    # Model 1: MRT Accuracy
    print("\n--- Fitting MRT Accuracy Models ---")
    
    # Baseline model 1a
    formula_1a = "MRT_accuracy ~ kappa_centered + rotation_angle_factor + kappa_centered:rotation_angle_factor + (1|participantId)"
    print(f"Model 1a formula: {formula_1a}")
    
    ro.globalenv['r_data'] = r_data
    model_1a = ro.r(f'lmer({formula_1a}, data = r_data, REML = FALSE)')
    ro.globalenv['model_1a'] = model_1a
    
    # Augmented model 1b
    formula_1b = f"MRT_accuracy ~ kappa_centered + rotation_angle_factor + kappa_centered:rotation_angle_factor + {covariate_terms} + (1|participantId)"
    print(f"Model 1b formula: {formula_1b}")
    
    model_1b = ro.r(f'lmer({formula_1b}, data = r_data, REML = FALSE)')
    ro.globalenv['model_1b'] = model_1b
    
    # Model comparison
    anova_result_1 = ro.r('anova')(model_1a, model_1b)
    print("Model 1 comparison results:")
    print(anova_result_1)
    
    # Extract comparison statistics
    with localconverter(ro.default_converter + numpy2ri.converter):
        anova_matrix_1 = np.array(anova_result_1)
    
    # Check model convergence
    is_singular_1a = bool(np.array(ro.r('isSingular(model_1a)'))[0])
    is_singular_1b = bool(np.array(ro.r('isSingular(model_1b)'))[0])
    
    if is_singular_1a or is_singular_1b:
        print(f"Warning: Model singularity detected - 1a: {is_singular_1a}, 1b: {is_singular_1b}")
    
    # Extract model statistics safely with proper R object handling
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_1a'] = model_1a
            ll_1a_array = np.array(ro.r('as.numeric(logLik(model_1a))'))
            ll_1a = float(ll_1a_array[0]) if ll_1a_array.size > 0 and not np.isnan(ll_1a_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract log-likelihood for model 1a: {e}")
        ll_1a = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_1b'] = model_1b
            ll_1b_array = np.array(ro.r('as.numeric(logLik(model_1b))'))
            ll_1b = float(ll_1b_array[0]) if ll_1b_array.size > 0 and not np.isnan(ll_1b_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract log-likelihood for model 1b: {e}")
        ll_1b = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_1a'] = model_1a
            aic_1a_array = np.array(ro.r('as.numeric(AIC(model_1a))'))
            aic_1a = float(aic_1a_array[0]) if aic_1a_array.size > 0 and not np.isnan(aic_1a_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract AIC for model 1a: {e}")
        aic_1a = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_1b'] = model_1b
            aic_1b_array = np.array(ro.r('as.numeric(AIC(model_1b))'))
            aic_1b = float(aic_1b_array[0]) if aic_1b_array.size > 0 and not np.isnan(aic_1b_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract AIC for model 1b: {e}")
        aic_1b = None
    
    # Extract fixed effects safely using proper numpy conversion
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_1a'] = model_1a
            fixed_effects_1a = np.array(ro.r('fixef(model_1a)'))
            kappa_coef_1a = float(fixed_effects_1a[1]) if (fixed_effects_1a.shape[0] > 1 and 
                                                          not np.isnan(fixed_effects_1a[1])) else None
    except Exception as e:
        print(f"Warning: Could not extract coefficients for model 1a: {e}")
        kappa_coef_1a = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_1b'] = model_1b
            fixed_effects_1b = np.array(ro.r('fixef(model_1b)'))
            kappa_coef_1b = float(fixed_effects_1b[1]) if (fixed_effects_1b.shape[0] > 1 and 
                                                          not np.isnan(fixed_effects_1b[1])) else None
    except Exception as e:
        print(f"Warning: Could not extract coefficients for model 1b: {e}")
        kappa_coef_1b = None
    
    # Extract coefficient table and p-values safely
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_1b'] = model_1b
            model_1b_summary = ro.r('summary(model_1b)')
            ro.globalenv['model_1b_summary'] = model_1b_summary
            coef_table_1b = np.array(ro.r('coef(model_1b_summary)'))
            kappa_p_1b = float(coef_table_1b[1, 4]) if (coef_table_1b.shape[0] > 1 and 
                                                        coef_table_1b.shape[1] > 4 and 
                                                        not np.isnan(coef_table_1b[1, 4])) else None
    except Exception as e:
        print(f"Warning: Could not extract p-values for model 1b: {e}")
        kappa_p_1b = None
    
    # Revert to named-column access for robustness
    try:
        lr_stat_1 = float(anova_result_1.rx2('Chisq')[1])
        df_diff_1 = int(anova_result_1.rx2('Df')[1])
        p_val_1 = float(anova_result_1.rx2('Pr(>Chisq)')[1])
    except Exception as e:
        print(f"Warning: Could not extract ANOVA statistics for model 1: {e}")
        lr_stat_1, df_diff_1, p_val_1 = None, None, None
    
    results['accuracy'] = {
        'model_comparison': 'MRT_Accuracy',
        'baseline_model_name': 'Model_1a',
        'augmented_model_name': 'Model_1b', 
        'log_likelihood_baseline': ll_1a,
        'log_likelihood_augmented': ll_1b,
        'likelihood_ratio_statistic': lr_stat_1,
        'df_difference': df_diff_1,
        'p_value_lr_test': p_val_1,
        'aic_baseline': aic_1a,
        'aic_augmented': aic_1b,
        'kappa_coefficient_baseline': kappa_coef_1a,
        'kappa_coefficient_augmented': kappa_coef_1b,
        'kappa_p_value_augmented': kappa_p_1b
    }
    
    print(f"Model 1 results: {results['accuracy']}")
    
    # Model 2: MRT Log RT
    print("\n--- Fitting MRT Log RT Models ---")
    
    # Baseline model 2a
    formula_2a = "MRT_log_RT ~ kappa_centered + rotation_angle_factor + kappa_centered:rotation_angle_factor + (1|participantId)"
    print(f"Model 2a formula: {formula_2a}")
    
    model_2a = ro.r(f'lmer({formula_2a}, data = r_data, REML = FALSE)')
    ro.globalenv['model_2a'] = model_2a
    
    # Augmented model 2b
    formula_2b = f"MRT_log_RT ~ kappa_centered + rotation_angle_factor + kappa_centered:rotation_angle_factor + {covariate_terms} + (1|participantId)"
    print(f"Model 2b formula: {formula_2b}")
    
    model_2b = ro.r(f'lmer({formula_2b}, data = r_data, REML = FALSE)')
    ro.globalenv['model_2b'] = model_2b
    
    # Model comparison
    anova_result_2 = ro.r('anova')(model_2a, model_2b)
    print("Model 2 comparison results:")
    print(anova_result_2)
    
    # Extract comparison statistics
    with localconverter(ro.default_converter + numpy2ri.converter):
        anova_matrix_2 = np.array(anova_result_2)
    
    # Check model convergence
    is_singular_2a = bool(np.array(ro.r('isSingular(model_2a)'))[0])
    is_singular_2b = bool(np.array(ro.r('isSingular(model_2b)'))[0])
    
    if is_singular_2a or is_singular_2b:
        print(f"Warning: Model singularity detected - 2a: {is_singular_2a}, 2b: {is_singular_2b}")
    
    # Extract model statistics safely with proper R object handling
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_2a'] = model_2a
            ll_2a_array = np.array(ro.r('as.numeric(logLik(model_2a))'))
            ll_2a = float(ll_2a_array[0]) if ll_2a_array.size > 0 and not np.isnan(ll_2a_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract log-likelihood for model 2a: {e}")
        ll_2a = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_2b'] = model_2b
            ll_2b_array = np.array(ro.r('as.numeric(logLik(model_2b))'))
            ll_2b = float(ll_2b_array[0]) if ll_2b_array.size > 0 and not np.isnan(ll_2b_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract log-likelihood for model 2b: {e}")
        ll_2b = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_2a'] = model_2a
            aic_2a_array = np.array(ro.r('as.numeric(AIC(model_2a))'))
            aic_2a = float(aic_2a_array[0]) if aic_2a_array.size > 0 and not np.isnan(aic_2a_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract AIC for model 2a: {e}")
        aic_2a = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_2b'] = model_2b
            aic_2b_array = np.array(ro.r('as.numeric(AIC(model_2b))'))
            aic_2b = float(aic_2b_array[0]) if aic_2b_array.size > 0 and not np.isnan(aic_2b_array[0]) else None
    except Exception as e:
        print(f"Warning: Could not extract AIC for model 2b: {e}")
        aic_2b = None
    
    # Extract fixed effects safely using proper numpy conversion
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_2a'] = model_2a
            fixed_effects_2a = np.array(ro.r('fixef(model_2a)'))
            kappa_coef_2a = float(fixed_effects_2a[1]) if (fixed_effects_2a.shape[0] > 1 and 
                                                          not np.isnan(fixed_effects_2a[1])) else None
    except Exception as e:
        print(f"Warning: Could not extract coefficients for model 2a: {e}")
        kappa_coef_2a = None
    
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_2b'] = model_2b
            fixed_effects_2b = np.array(ro.r('fixef(model_2b)'))
            kappa_coef_2b = float(fixed_effects_2b[1]) if (fixed_effects_2b.shape[0] > 1 and 
                                                          not np.isnan(fixed_effects_2b[1])) else None
    except Exception as e:
        print(f"Warning: Could not extract coefficients for model 2b: {e}")
        kappa_coef_2b = None
    
    # Extract coefficient table and p-values safely
    try:
        with localconverter(ro.default_converter + numpy2ri.converter):
            ro.globalenv['model_2b'] = model_2b
            model_2b_summary = ro.r('summary(model_2b)')
            ro.globalenv['model_2b_summary'] = model_2b_summary
            coef_table_2b = np.array(ro.r('coef(model_2b_summary)'))
            kappa_p_2b = float(coef_table_2b[1, 4]) if (coef_table_2b.shape[0] > 1 and 
                                                        coef_table_2b.shape[1] > 4 and 
                                                        not np.isnan(coef_table_2b[1, 4])) else None
    except Exception as e:
        print(f"Warning: Could not extract p-values for model 2b: {e}")
        kappa_p_2b = None
    
    # Revert to named-column access for robustness
    try:
        lr_stat_2 = float(anova_result_2.rx2('Chisq')[1])
        df_diff_2 = int(anova_result_2.rx2('Df')[1])
        p_val_2 = float(anova_result_2.rx2('Pr(>Chisq)')[1])
    except Exception as e:
        print(f"Warning: Could not extract ANOVA statistics for model 2: {e}")
        lr_stat_2, df_diff_2, p_val_2 = None, None, None
    
    results['log_rt'] = {
        'model_comparison': 'MRT_Log_RT',
        'baseline_model_name': 'Model_2a',
        'augmented_model_name': 'Model_2b',
        'log_likelihood_baseline': ll_2a,
        'log_likelihood_augmented': ll_2b,
        'likelihood_ratio_statistic': lr_stat_2,
        'df_difference': df_diff_2,
        'p_value_lr_test': p_val_2,
        'aic_baseline': aic_2a,
        'aic_augmented': aic_2b,
        'kappa_coefficient_baseline': kappa_coef_2a,
        'kappa_coefficient_augmented': kappa_coef_2b,
        'kappa_p_value_augmented': kappa_p_2b
    }
    
    print(f"Model 2 results: {results['log_rt']}")
    
    # Store models for covariate effects extraction
    results['models'] = {
        'model_1b': model_1b,
        'model_2b': model_2b
    }
    
    return results

def fit_vviq2_linear_regression_models(vviq2_data):
    """
    Fit hierarchical linear regression models for VVIQ2 data using R lm().
    Compares full (kappa + covariates) vs reduced (covariates only) models using ANOVA.
    
    Parameters:
    vviq2_data (DataFrame): Augmented VVIQ2 dataset with centered covariates
    
    Returns:
    dict: Dictionary containing model results for all VVIQ2 scores
    """
    print("\n=== FITTING VVIQ2 LINEAR REGRESSION MODELS ===")
    
    # Import R packages
    base = importr('base')
    stats = importr('stats')
    
    # Convert data to R
    with localconverter(ro.default_converter + pandas2ri.converter):
        r_data = ro.conversion.py2rpy(vviq2_data)
    
    print("VVIQ2 data converted to R successfully")
    print(f"R data dimensions: {ro.r('dim')(r_data)}")
    
    # Define dependent variables
    vviq2_scores = [
        'total_score',
        'familiar_person_score',
        'sunrise_score', 
        'shop_front_score',
        'countryside_score',
        'driving_score',
        'beach_score',
        'railway_station_score',
        'garden_scene_score'
    ]
    
    # Define covariate terms
    covariate_terms = " + ".join([
        "VWM_mean_absolute_error_centered",
        "VWM_error_SD_centered",
        "VWM_overall_accuracy_centered", 
        "VWM_RT_variability_CV_centered",
        "MRT_RT_variability_CV_centered",
        "focus_loss_instances_centered",
        "focus_loss_duration_ms_centered"
    ])
    
    results = {}
    ro.globalenv['r_data'] = r_data
    
    for score in vviq2_scores:
        print(f"\n--- Fitting models for {score} ---")
        
        # Full model: kappa + covariates
        formula_full = f"{score} ~ kappa_centered + {covariate_terms}"
        print(f"Full model formula: {formula_full}")
        full_model = ro.r(f'lm({formula_full}, data = r_data)')
        ro.globalenv['full_model'] = full_model

        # Reduced model: covariates only
        formula_reduced = f"{score} ~ {covariate_terms}"
        print(f"Reduced model formula: {formula_reduced}")
        reduced_model = ro.r(f'lm({formula_reduced}, data = r_data)')
        ro.globalenv['reduced_model'] = reduced_model

        # ANOVA comparison
        anova_result = ro.r('anova')(reduced_model, full_model)
        with localconverter(ro.default_converter + numpy2ri.converter):
            anova_matrix = np.array(anova_result)
        
        # Use named-column access for robustness
        try:
            f_stat_kappa = float(anova_result.rx2('F')[1])
            p_val_kappa_unique = float(anova_result.rx2('Pr(>F)')[1])
        except Exception as e:
            print(f"Warning: Could not extract F-statistic/p-value for {score}: {e}")
            f_stat_kappa, p_val_kappa_unique = None, None
        
        # Extract R-squared for full and reduced models
        try:
            with localconverter(ro.default_converter + numpy2ri.converter):
                full_summary = ro.r('summary')(full_model)
                reduced_summary = ro.r('summary')(reduced_model)
                r_squared_full = float(np.array(ro.r('as.numeric(summary(full_model)$r.squared)'))[0])
                r_squared_reduced = float(np.array(ro.r('as.numeric(summary(reduced_model)$r.squared)'))[0])
                partial_r_squared = r_squared_full - r_squared_reduced
        except Exception as e:
            print(f"Warning: Could not extract R-squared for {score}: {e}")
            r_squared_full = None
            r_squared_reduced = None
            partial_r_squared = None
        
        # Extract kappa coefficient and stats from full model
        try:
            with localconverter(ro.default_converter + numpy2ri.converter):
                coef_table = np.array(ro.r('coef(summary(full_model))'))
        except Exception as e:
            print(f"Warning: Could not extract coefficient table for {score}: {e}")
            coef_table = np.array([])
        
        kappa_coef = None
        kappa_se = None
        kappa_t = None
        kappa_p = None
        if coef_table.shape[0] > 1 and coef_table.shape[1] > 3:
            try:
                kappa_coef = float(coef_table[1, 0]) if not np.isnan(coef_table[1, 0]) else None
                kappa_se = float(coef_table[1, 1]) if not np.isnan(coef_table[1, 1]) else None
                kappa_t = float(coef_table[1, 2]) if not np.isnan(coef_table[1, 2]) else None  # Corrected index
                kappa_p = float(coef_table[1, 3]) if not np.isnan(coef_table[1, 3]) else None  # Corrected index
            except Exception as e:
                print(f"Warning: Could not extract kappa statistics for {score}: {e}")
        
        # Calculate standardized beta for kappa
        standardized_beta = None
        try:
            with localconverter(ro.default_converter + numpy2ri.converter):
                sd_kappa_array = np.array(ro.r('as.numeric(sd(r_data$kappa_centered, na.rm = TRUE))'))
                sd_y_array = np.array(ro.r(f'as.numeric(sd(r_data${score}, na.rm = TRUE))'))
                if sd_kappa_array.size > 0 and sd_y_array.size > 0:
                    sd_kappa = float(sd_kappa_array[0]) if not np.isnan(sd_kappa_array[0]) else 1.0
                    sd_y = float(sd_y_array[0]) if not np.isnan(sd_y_array[0]) else 1.0
                    if (kappa_coef is not None and sd_y != 0 and not np.isnan(sd_y) and 
                        sd_kappa != 0 and not np.isnan(sd_kappa)):
                        standardized_beta = kappa_coef * (sd_kappa / sd_y)
        except Exception as e:
            print(f"Warning: Error calculating standardized beta for {score}: {e}")
        
        results[score] = {
            'dependent_variable': score,
            'model_type': 'linear_regression_full',
            'kappa_coefficient': kappa_coef,
            'kappa_std_error': kappa_se,
            'kappa_standardized_beta': standardized_beta,
            'kappa_p_value': kappa_p,
            'model_r_squared': r_squared_full,
            'partial_r_squared_kappa': partial_r_squared,
            'f_statistic_kappa_unique': f_stat_kappa,
            'p_value_kappa_unique': p_val_kappa_unique,
            'full_model': full_model
        }
        
        # Conditional printing to avoid None formatting errors
        print(f"Results for {score}:")
        if kappa_coef is not None:
            print(f"  Kappa coefficient: {kappa_coef:.6f}")
        else:
            print(f"  Kappa coefficient: None")
        if kappa_p is not None:
            print(f"  Kappa p-value: {kappa_p:.6f}")
        else:
            print(f"  Kappa p-value: None")
        if r_squared_full is not None:
            print(f"  Model R-squared: {r_squared_full:.6f}")
        else:
            print(f"  Model R-squared: None")
        if partial_r_squared is not None:
            print(f"  Partial R-squared: {partial_r_squared:.6f}")
        else:
            print(f"  Partial R-squared: None")
    
    return results

def extract_covariate_effects(mrt_results, vviq2_results):
    """
    Extract covariate effects from all fitted models.
    
    Parameters:
    mrt_results (dict): Results from MRT mixed-effects models
    vviq2_results (dict): Results from VVIQ2 robust regression models
    
    Returns:
    list: List of dictionaries containing covariate effect information
    """
    print("\n=== EXTRACTING COVARIATE EFFECTS ===")
    
    covariate_effects = []
    
    # Extract from MRT models
    print("--- MRT Model Covariate Effects ---")
    
    mrt_models = {
        'MRT_Accuracy_Model_1b': mrt_results['models']['model_1b'],
        'MRT_Log_RT_Model_2b': mrt_results['models']['model_2b']
    }
    
    for model_name, model in mrt_models.items():
        print(f"\nExtracting effects for {model_name}")
        
        # Get coefficient table safely with proper error handling
        try:
            with localconverter(ro.default_converter + numpy2ri.converter):
                ro.globalenv['model'] = model
                ro.r('model_summary <- summary(model)')
                coef_table = np.array(ro.r('model_summary$coefficients'))
                r_rownames = ro.r('rownames(model_summary$coefficients)')
                coef_names = [str(name) for name in r_rownames]
                print(f"Coefficient names: {coef_names}")
                print(f"Coefficient table shape: {coef_table.shape}")
        except Exception as e:
            print(f"Warning: Could not extract coefficient table for {model_name}: {e}")
            continue
        
        # Extract covariate effects (skip intercept and main experimental factors)
        for i, coef_name in enumerate(coef_names):
            if '_centered' in coef_name and i < coef_table.shape[0]:
                try:
                    coefficient = float(coef_table[i, 0]) if (i < coef_table.shape[0] and 
                                                            coef_table.shape[1] > 0 and 
                                                            not np.isnan(coef_table[i, 0])) else None
                    std_error = float(coef_table[i, 1]) if (i < coef_table.shape[0] and 
                                                          coef_table.shape[1] > 1 and 
                                                          not np.isnan(coef_table[i, 1])) else None
                    # For MRT models - lmerTest has different indexing
                    t_value = float(coef_table[i, 3]) if (i < coef_table.shape[0] and 
                                                        coef_table.shape[1] > 3 and 
                                                        not np.isnan(coef_table[i, 3])) else None
                    p_value = float(coef_table[i, 4]) if (i < coef_table.shape[0] and 
                                                        coef_table.shape[1] > 4 and 
                                                        not np.isnan(coef_table[i, 4])) else None
                except (IndexError, ValueError) as e:
                    print(f"Warning: Could not extract statistics for {coef_name}: {e}")
                    continue
                
                # Calculate standardized beta (approximate)
                # For mixed-effects models, this is more complex, so we'll use a simple approximation
                standardized_beta = coefficient  # Placeholder - would need more complex calculation
                
                covariate_effects.append({
                    'analysis_type': 'MRT_Mixed_Effects',
                    'model_name': model_name,
                    'covariate_name': coef_name,
                    'coefficient': coefficient,
                    'std_error': std_error,
                    'standardized_beta': standardized_beta,
                    't_value': t_value,
                    'p_value': p_value,
                    'significant_at_05': p_value < 0.05 if p_value is not None else False
                })
                
                print(f"  {coef_name}: coef={coefficient:.6f}, p={p_value:.6f}")
    
    # Extract from VVIQ2 models
    print("\n--- VVIQ2 Model Covariate Effects ---")
    
    for score, result in vviq2_results.items():
        if 'full_model' in result:
            print(f"\nExtracting effects for {score}")
            
            model = result['full_model']
            
            try:
                with localconverter(ro.default_converter + numpy2ri.converter):
                    ro.globalenv['model'] = model
                    ro.r('model_summary <- summary(model)')
                    coef_table = np.array(ro.r('model_summary$coefficients'))
                    r_rownames = ro.r('rownames(model_summary$coefficients)')
                    coef_names = [str(name) for name in r_rownames]
                    print(f"Coefficient names: {coef_names}")
            except Exception as e:
                print(f"Warning: Could not extract coefficient table for {score}: {e}")
                continue
            
            # Extract covariate effects safely
            for i, coef_name in enumerate(coef_names):
                if '_centered' in coef_name and i < coef_table.shape[0]:
                    try:
                        coefficient = float(coef_table[i, 0]) if (i < coef_table.shape[0] and 
                                                                coef_table.shape[1] > 0 and 
                                                                not np.isnan(coef_table[i, 0])) else None
                        std_error = float(coef_table[i, 1]) if (i < coef_table.shape[0] and 
                                                              coef_table.shape[1] > 1 and 
                                                              not np.isnan(coef_table[i, 1])) else None
                        t_value = float(coef_table[i, 2]) if (i < coef_table.shape[0] and 
                                                            coef_table.shape[1] > 2 and 
                                                            not np.isnan(coef_table[i, 2])) else None
                        p_value = float(coef_table[i, 3]) if (i < coef_table.shape[0] and 
                                                            coef_table.shape[1] > 3 and 
                                                            not np.isnan(coef_table[i, 3])) else None
                    except (IndexError, ValueError) as e:
                        print(f"Warning: Could not extract statistics for {coef_name} in {score}: {e}")
                        continue
                    
                    # Calculate standardized beta safely with proper R object handling
                    standardized_beta = None
                    try:
                        with localconverter(ro.default_converter + numpy2ri.converter):
                            ro.globalenv['model'] = model
                            ro.globalenv['coef_name'] = coef_name
                            ro.r('model_frame <- model.frame(model)')
                            
                            # Check if covariate exists in model frame
                            coef_exists = bool(np.array(ro.r(f'"{coef_name}" %in% colnames(model_frame)'))[0])
                            if coef_exists:
                                ro.r('x_var <- model_frame[, coef_name]')
                                ro.r('y_var <- model_frame[, 1]')
                                
                                sd_x_array = np.array(ro.r('as.numeric(sd(x_var, na.rm = TRUE))'))
                                sd_y_array = np.array(ro.r('as.numeric(sd(y_var, na.rm = TRUE))'))
                                
                                if sd_x_array.shape[0] > 0 and sd_y_array.shape[0] > 0:
                                    sd_x = float(sd_x_array[0]) if not np.isnan(sd_x_array[0]) else 1.0
                                    sd_y = float(sd_y_array[0]) if not np.isnan(sd_y_array[0]) else 1.0
                                    
                                    if (coefficient is not None and sd_y != 0 and not np.isnan(sd_y) and 
                                        sd_x != 0 and not np.isnan(sd_x)):
                                        standardized_beta = coefficient * (sd_x / sd_y)
                    except Exception as e:
                        print(f"Warning: Error calculating standardized beta for {coef_name}: {e}")
                    
                    covariate_effects.append({
                        'analysis_type': 'VVIQ2_Linear_Regression',
                        'model_name': f'VVIQ2_{score}',
                        'covariate_name': coef_name,
                        'coefficient': coefficient,
                        'std_error': std_error,
                        'standardized_beta': standardized_beta,
                        't_value': t_value,
                        'p_value': p_value,
                        'significant_at_05': p_value < 0.05 if p_value is not None else False
                    })
                    
                    if coefficient is not None and p_value is not None:
                        print(f"  {coef_name}: coef={coefficient:.6f}, p={p_value:.6f}")
                    else:
                        print(f"  {coef_name}: coef={coefficient}, p={p_value}")
    
    print(f"\nTotal covariate effects extracted: {len(covariate_effects)}")
    return covariate_effects

def save_results(mrt_results, vviq2_results, covariate_effects):
    """
    Save all results to CSV files.
    
    Parameters:
    mrt_results (dict): MRT model comparison results
    vviq2_results (dict): VVIQ2 model results
    covariate_effects (list): Covariate effect results
    """
    print("\n=== SAVING RESULTS ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save MRT results
    mrt_output_data = []
    for model_type, results in mrt_results.items():
        if model_type != 'models':  # Skip stored model objects
            mrt_output_data.append(results)
    
    mrt_output_file = f"outputs/MRT_covariate_control_models_{timestamp}.csv"
    mrt_df = pd.DataFrame(mrt_output_data)
    mrt_df.to_csv(mrt_output_file, index=False)
    print(f"MRT results saved to: {mrt_output_file}")
    print("MRT results preview:")
    print(mrt_df.head(2))
    
    # Save VVIQ2 results
    vviq2_output_data = []
    for score, results in vviq2_results.items():
        if 'full_model' in results:
            # Remove the model object before saving
            output_row = {k: v for k, v in results.items() if k != 'full_model'}
            vviq2_output_data.append(output_row)
    
    vviq2_output_file = f"outputs/VVIQ2_covariate_control_models_{timestamp}.csv"
    vviq2_df = pd.DataFrame(vviq2_output_data)
    vviq2_df.to_csv(vviq2_output_file, index=False)
    print(f"VVIQ2 results saved to: {vviq2_output_file}")
    print("VVIQ2 results preview:")
    print(vviq2_df.head(2))
    
    # Save covariate effects
    covariate_output_file = f"outputs/covariate_effects_summary_{timestamp}.csv"
    covariate_df = pd.DataFrame(covariate_effects)
    covariate_df.to_csv(covariate_output_file, index=False)
    print(f"Covariate effects saved to: {covariate_output_file}")
    print("Covariate effects preview:")
    print(covariate_df.head(2))
    
    print(f"\nAll results saved with timestamp: {timestamp}")

def main():
    """
    Main function to execute the covariate control analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting covariate control analysis...")
        
        # Step 1: Prepare augmented datasets
        mrt_data, vviq2_data = prepare_augmented_datasets()
        
        # Step 2: Fit MRT mixed-effects models
        mrt_results = fit_mrt_mixed_effects_models(mrt_data)
        
        # Step 3: Fit VVIQ2 linear regression models
        vviq2_results = fit_vviq2_linear_regression_models(vviq2_data)
        
        # Step 4: Extract covariate effects
        covariate_effects = extract_covariate_effects(mrt_results, vviq2_results)
        
        # Step 5: Save results
        save_results(mrt_results, vviq2_results, covariate_effects)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
