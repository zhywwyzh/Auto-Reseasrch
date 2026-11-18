#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import R interface
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects.conversion import localconverter

def get_most_recent_file(pattern):
    """
    Get the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_input_data():
    """
    Load all required input CSV files with validation.
    
    Returns:
    tuple: (trial_data, precision_params, domain_metrics) DataFrames
    """
    print("Loading input data files...")
    
    # Find most recent files
    trial_pattern = "outputs/trial_level_cleaned_data_*.csv"
    precision_pattern = "outputs/final_precision_parameters_*.csv"
    metrics_pattern = "outputs/domain_general_metrics_*.csv"
    
    trial_file = get_most_recent_file(trial_pattern)
    precision_file = get_most_recent_file(precision_pattern)
    metrics_file = get_most_recent_file(metrics_pattern)
    
    if not trial_file:
        raise FileNotFoundError(f"No trial data file found matching pattern: {trial_pattern}")
    if not precision_file:
        raise FileNotFoundError(f"No precision parameters file found matching pattern: {precision_pattern}")
    if not metrics_file:
        raise FileNotFoundError(f"No domain metrics file found matching pattern: {metrics_pattern}")
    
    print(f"Loading trial data from: {trial_file}")
    print(f"Loading precision parameters from: {precision_file}")
    print(f"Loading domain metrics from: {metrics_file}")
    
    # Load trial data
    trial_data = pd.read_csv(trial_file)
    trial_data.columns = trial_data.columns.str.strip()
    print(f"\nTrial data columns: {list(trial_data.columns)}")
    print(f"Trial data shape: {trial_data.shape}")
    print("First 3 rows of trial data:")
    print(trial_data.head(3))

    # Validate required columns for trial data (after stripping)
    required_trial_cols = ['participantId', 'isPractice', 'trial_excluded_MRT', 'MRT_trial', 
                          'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_stimulusId']
    missing_trial_cols = [col for col in required_trial_cols if col not in trial_data.columns]
    if missing_trial_cols:
        raise ValueError(f"Missing required trial data columns: {missing_trial_cols}")

    # Load precision parameters
    precision_params = pd.read_csv(precision_file)
    precision_params.columns = precision_params.columns.str.strip()
    print(f"\nPrecision parameters columns: {list(precision_params.columns)}")
    print(f"Precision parameters shape: {precision_params.shape}")
    print("First 3 rows of precision parameters:")
    print(precision_params.head(3))

    # Validate required columns for precision parameters (after stripping)
    required_precision_cols = ['participantId', 'final_concentration_kappa', 'excluded_outlier']
    missing_precision_cols = [col for col in required_precision_cols if col not in precision_params.columns]
    if missing_precision_cols:
        raise ValueError(f"Missing required precision parameters columns: {missing_precision_cols}")

    # Load domain metrics
    domain_metrics = pd.read_csv(metrics_file)
    domain_metrics.columns = domain_metrics.columns.str.strip()
    print(f"\nDomain metrics columns: {list(domain_metrics.columns)}")
    print(f"Domain metrics shape: {domain_metrics.shape}")
    print("First 3 rows of domain metrics:")
    print(domain_metrics.head(3))

    # Validate required columns for domain metrics (after stripping)
    required_metrics_cols = ['participantId', 'VWM_median_rt_z', 'MRT_median_rt_z', 'VWM_accuracy_z', 
                            'MRT_accuracy_z', 'session_duration_z', 'focus_loss_duration_z', 'focus_loss_instances_z']
    missing_metrics_cols = [col for col in required_metrics_cols if col not in domain_metrics.columns]
    if missing_metrics_cols:
        raise ValueError(f"Missing required domain metrics columns: {missing_metrics_cols}")

    return trial_data, precision_params, domain_metrics

def prepare_analysis_dataset(trial_data, precision_params, domain_metrics):
    """
    Prepare the dataset for mixed-effects modeling by filtering and merging data.

    This function provides detailed logging and explanation of the data exclusion process,
    especially regarding the interleaved VWM and MRT trials. The high overall exclusion rate
    is expected and appropriate, as only MRT trials are relevant for this analysis.

    Parameters:
    trial_data (DataFrame): Trial-level data
    precision_params (DataFrame): Precision parameters
    domain_metrics (DataFrame): Domain-general metrics

    Returns:
    DataFrame: Prepared analysis dataset
    """
    print("\nPreparing analysis dataset...")

    # -------------------------------------------------------------------------
    # EXPLANATION OF DATA STRUCTURE AND EXCLUSION PROCESS
    # -------------------------------------------------------------------------
    print(f"\nData structure explanation:")
    print(f"The trial data contains interleaved VWM and MRT trials.")
    print(f"VWM trials will have NaN values for MRT columns and vice versa.")
    print(f"This analysis focuses on MRT trials only, so VWM trials will be excluded.")
    print(f"High overall exclusion rates are expected and appropriate, as all VWM trials are removed before MRT-specific exclusions are applied.")

    # Count VWM and MRT trials before any filtering
    vwm_trials = trial_data['VWM_trial'].notna().sum()
    mrt_trials = trial_data['MRT_trial'].notna().sum()
    print(f"VWM trials in dataset: {vwm_trials}")
    print(f"MRT trials in dataset: {mrt_trials}")
    print(f"Total trials in dataset: {trial_data.shape[0]}")

    # Print unique values for key experimental design parameters
    print(f"Unique values in isPractice: {trial_data['isPractice'].unique()}")
    print(f"Unique values in trial_excluded_MRT: {trial_data['trial_excluded_MRT'].unique()}")
    print(f"Unique values in MRT_angle_degrees: {sorted(trial_data['MRT_angle_degrees'].unique())}")
    print(f"Unique values in MRT_isCorrect: {trial_data['MRT_isCorrect'].unique()}")
    print(f"Unique values in excluded_outlier: {precision_params['excluded_outlier'].unique()}")

    # -------------------------------------------------------------------------
    # FILTER TO TEST TRIALS ONLY (exclude practice)
    # -------------------------------------------------------------------------
    print(f"\nFiltering to test trials (isPractice == False)...")
    print(f"Initial trial data shape: {trial_data.shape}")
    test_trials = trial_data[trial_data['isPractice'] == False].copy()
    print(f"After filtering to test trials: {test_trials.shape}")

    # Count VWM and MRT trials after filtering to test trials
    vwm_test_trials = test_trials['VWM_trial'].notna().sum()
    mrt_test_trials = test_trials['MRT_trial'].notna().sum()
    print(f"VWM test trials: {vwm_test_trials}")
    print(f"MRT test trials: {mrt_test_trials}")

    # -------------------------------------------------------------------------
    # EXCLUDE NON-MRT TRIALS (i.e., keep only MRT trials)
    # -------------------------------------------------------------------------
    print(f"\nExcluding non-MRT trials (keeping only MRT trials for analysis)...")
    mrt_test_trials_df = test_trials[test_trials['MRT_trial'].notna()].copy()
    print(f"Shape after keeping only MRT test trials: {mrt_test_trials_df.shape}")

    # -------------------------------------------------------------------------
    # EXCLUDE FLAGGED MRT TRIALS (MRT-specific exclusions)
    # -------------------------------------------------------------------------
    print(f"\nExcluding flagged MRT trials (trial_excluded_MRT == True)...")
    mrt_excluded_trials = mrt_test_trials_df[mrt_test_trials_df['trial_excluded_MRT'] == True].shape[0]
    mrt_total_trials = mrt_test_trials_df.shape[0]
    mrt_exclusion_rate = (mrt_excluded_trials / mrt_total_trials) * 100 if mrt_total_trials > 0 else 0
    print(f"MRT-specific exclusion rate: {mrt_exclusion_rate:.1f}% ({mrt_excluded_trials}/{mrt_total_trials} MRT test trials flagged for exclusion)")

    # Now keep only valid MRT trials
    valid_trials = mrt_test_trials_df[mrt_test_trials_df['trial_excluded_MRT'] == False].copy()
    print(f"After excluding flagged MRT trials: {valid_trials.shape}")

    # -------------------------------------------------------------------------
    # FILTER PRECISION PARAMETERS TO NON-OUTLIER PARTICIPANTS
    # -------------------------------------------------------------------------
    print(f"\nFiltering precision parameters to non-outlier participants...")
    print(f"Initial precision parameters shape: {precision_params.shape}")
    valid_participants = precision_params[precision_params['excluded_outlier'] == False].copy()
    print(f"After excluding outlier participants (excluded_outlier == False): {valid_participants.shape}")

    # -------------------------------------------------------------------------
    # MERGE WITH PRECISION PARAMETERS
    # -------------------------------------------------------------------------
    merged_data = valid_trials.merge(valid_participants[['participantId', 'final_concentration_kappa']],
                                    on='participantId', how='inner')
    print(f"After merging with precision parameters: {merged_data.shape}")

    # -------------------------------------------------------------------------
    # MERGE WITH DOMAIN METRICS
    # -------------------------------------------------------------------------
    final_data = merged_data.merge(domain_metrics, on='participantId', how='inner')
    print(f"After merging with domain metrics: {final_data.shape}")

    # -------------------------------------------------------------------------
    # CONVERT MRT_ANGLE_DEGREES TO CATEGORICAL
    # -------------------------------------------------------------------------
    angle_mapping = {0: "0°", 50: "50°", 100: "100°", 150: "150°"}
    final_data['MRT_angle_categorical'] = final_data['MRT_angle_degrees'].map(angle_mapping)

    # Safely convert to string and sort, handling edge cases
    unique_cats = final_data['MRT_angle_categorical'].dropna().unique()
    unique_cats_str = []
    for x in unique_cats:
        try:
            if pd.notna(x):
                unique_cats_str.append(str(x))
        except Exception:
            continue
    try:
        sorted_unique_cats = sorted(unique_cats_str)
    except Exception:
        sorted_unique_cats = unique_cats_str
    print(f"Unique values in MRT_angle_categorical: {sorted_unique_cats}")
    print(f"Final analysis dataset shape: {final_data.shape}")

    # -------------------------------------------------------------------------
    # CHECK FOR MISSING DATA
    # -------------------------------------------------------------------------
    print("\nMissing data summary:")
    missing_summary = final_data.isnull().sum()
    if hasattr(missing_summary, "items"):
        for col, missing_count in missing_summary.items():
            try:
                if missing_count > 0:
                    print(f"{col}: {missing_count} missing values")
            except Exception:
                continue
    else:
        print("No missing data summary available or unexpected data structure.")

    # -------------------------------------------------------------------------
    # REMOVE ROWS WITH ANY MISSING VALUES IN REQUIRED COLUMNS
    # -------------------------------------------------------------------------
    required_clean_cols = [
        'participantId', 'MRT_trial', 'MRT_angle_degrees', 'MRT_angle_categorical',
        'MRT_isCorrect', 'MRT_stimulusId', 'final_concentration_kappa',
        'VWM_median_rt_z', 'MRT_median_rt_z', 'VWM_accuracy_z', 'MRT_accuracy_z',
        'session_duration_z', 'focus_loss_duration_z', 'focus_loss_instances_z'
    ]
    before_dropna = final_data.shape[0]
    final_data = final_data.dropna(subset=required_clean_cols)
    after_dropna = final_data.shape[0]
    if before_dropna != after_dropna:
        print(f"Removed {before_dropna - after_dropna} rows with missing values in required columns.")

    # -------------------------------------------------------------------------
    # FINAL DATASET SUMMARY
    # -------------------------------------------------------------------------
    n_participants = final_data['participantId'].nunique()
    n_stimuli = final_data['MRT_stimulusId'].nunique()
    n_trials = len(final_data)

    print(f"\nFinal dataset summary:")
    print(f"Number of participants: {n_participants}")
    print(f"Number of unique stimuli: {n_stimuli}")
    print(f"Number of trials: {n_trials}")
    print(f"Trials per participant (mean): {n_trials / n_participants:.1f}")

    # -------------------------------------------------------------------------
    # INTERPRETIVE COMMENT ON EXCLUSION RATES
    # -------------------------------------------------------------------------
    print("\nInterpretation:")
    print("The high overall exclusion rate is expected and appropriate, as the majority of excluded trials are VWM trials that are not relevant for the MRT analysis.")
    print("The actual exclusion rate for MRT trials due to quality control is much lower and is reported above as the MRT-specific exclusion rate.")

    return final_data

def fit_mixed_effects_model(analysis_data):
    """
    Fit hierarchical logistic mixed-effects model using R's lme4 package.
    
    Parameters:
    analysis_data (DataFrame): Prepared analysis dataset
    
    Returns:
    dict: Model results including estimates, standard errors, p-values, etc.
    """
    print("\nFitting mixed-effects logistic regression model...")

    # Install and import required R packages
    required_r_packages = ['lme4', 'car', 'emmeans', 'ggplot2']
    utils = importr('utils')
    utils.chooseCRANmirror(ind=1)
    for pkg in required_r_packages:
        try:
            importr(pkg)
        except Exception:
            print(f"R package '{pkg}' not found. Attempting to install...")
            try:
                utils.install_packages(pkg)
                importr(pkg)
                print(f"Successfully installed and imported R package: {pkg}")
            except Exception as e:
                print(f"Failed to install R package '{pkg}': {e}")
                raise

    try:
        lme4 = importr('lme4')
        car = importr('car')
        base = importr('base')
        stats = importr('stats')
        print("Successfully imported R packages: lme4, car, emmeans, ggplot2")
    except Exception as e:
        print(f"Error importing R packages: {e}")
        raise

    # Convert pandas DataFrame to R DataFrame using localconverter
    try:
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_data = ro.conversion.py2rpy(analysis_data)
        ro.globalenv['analysis_data'] = r_data
    except Exception as e:
        print(f"Error converting pandas DataFrame to R DataFrame: {e}")
        raise

    # Set reference level for angle factor
    try:
        ro.r('''
        analysis_data$MRT_angle_categorical <- factor(analysis_data$MRT_angle_categorical, 
                                                      levels = c("0°", "50°", "100°", "150°"))
        ''')
    except Exception as e:
        print(f"Error setting reference level for MRT_angle_categorical: {e}")
        raise

    print("Fitting full model with all fixed and random effects...")

    # Fit the full mixed-effects model
    model_formula = '''
    glmer(MRT_isCorrect ~ final_concentration_kappa * MRT_angle_categorical + 
          VWM_median_rt_z + MRT_median_rt_z + VWM_accuracy_z + MRT_accuracy_z + 
          session_duration_z + focus_loss_duration_z + focus_loss_instances_z +
          (1 | participantId) + (1 | MRT_stimulusId),
          data = analysis_data, family = binomial(link = "logit"),
          control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000)))
    '''

    try:
        ro.r(f'full_model <- {model_formula}')
        print("Full model fitted successfully")
    except Exception as e:
        print(f"Error fitting full model: {e}")
        raise

    # Get model summary and extract fixed effects with parameter names
    try:
        ro.r('model_summary <- summary(full_model)')
        ro.r('coef_matrix <- coefficients(summary(full_model))')
        ro.r('param_names <- rownames(coef_matrix)')
        
        # Extract parameter names and coefficient matrix separately
        with localconverter(ro.default_converter + pandas2ri.converter):
            param_names = list(ro.conversion.rpy2py(ro.r('param_names')))
            fixed_effects_matrix = ro.conversion.rpy2py(ro.r('coef_matrix'))
        
        # Create proper DataFrame with parameter names as index
        fixed_effects_df = pd.DataFrame(fixed_effects_matrix, 
                                       index=param_names,
                                       columns=['Estimate', 'Std.Error', 'z.value', 'Pr(>|z|)'])
    except Exception as e:
        print(f"Error extracting fixed effects: {e}")
        raise

    print("\nFixed effects estimates:")
    print(fixed_effects_df)

    # Calculate odds ratios and confidence intervals
    try:
        ro.r('ci_results <- confint(full_model, method = "Wald")')
        ro.r('ci_param_names <- rownames(ci_results)')
        
        with localconverter(ro.default_converter + pandas2ri.converter):
            ci_matrix = ro.conversion.rpy2py(ro.r('ci_results'))
            ci_param_names = list(ro.conversion.rpy2py(ro.r('ci_param_names')))
        
        # Create CI DataFrame
        ci_df = pd.DataFrame(ci_matrix, 
                            index=ci_param_names,
                            columns=['2.5%', '97.5%'])
    except Exception as e:
        print(f"Error calculating confidence intervals: {e}")
        raise

    # Prepare results
    results = []

    for param in param_names:
        try:
            estimate = fixed_effects_df.loc[param, 'Estimate']
            std_error = fixed_effects_df.loc[param, 'Std.Error']
            z_value = fixed_effects_df.loc[param, 'z.value']
            p_value = fixed_effects_df.loc[param, 'Pr(>|z|)']

            odds_ratio = np.exp(estimate)
            
            # Handle CI extraction with error checking
            if param in ci_df.index:
                ci_lower = np.exp(ci_df.loc[param, '2.5%'])
                ci_upper = np.exp(ci_df.loc[param, '97.5%'])
            else:
                print(f"Warning: No CI found for parameter {param}")
                ci_lower = np.nan
                ci_upper = np.nan
                
            significance = p_value < 0.05  # Use uncorrected alpha as per instructions

            results.append({
                'parameter': param,
                'estimate': estimate,
                'std_error': std_error,
                'z_value': z_value,
                'p_value': p_value,
                'odds_ratio': odds_ratio,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'significance': significance
            })
        except Exception as e:
            print(f"Error processing parameter {param}: {e}")
            continue

    # Test main effect and interaction using likelihood ratio tests
    print("\nTesting main effect of concentration parameter...")

    # Model without concentration main effect
    model_no_main = '''
    glmer(MRT_isCorrect ~ MRT_angle_categorical + 
          VWM_median_rt_z + MRT_median_rt_z + VWM_accuracy_z + MRT_accuracy_z + 
          session_duration_z + focus_loss_duration_z + focus_loss_instances_z +
          (1 | participantId) + (1 | MRT_stimulusId),
          data = analysis_data, family = binomial(link = "logit"),
          control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000)))
    '''

    try:
        ro.r(f'model_no_main <- {model_no_main}')
        ro.r('lr_test_main <- anova(model_no_main, full_model)')
        with localconverter(ro.default_converter + pandas2ri.converter):
            lr_main = ro.conversion.rpy2py(ro.r('lr_test_main'))
        print("Main effect likelihood ratio test:")
        print(lr_main)
    except Exception as e:
        print(f"Error in main effect likelihood ratio test: {e}")
        raise

    # Model without interaction
    print("\nTesting interaction effect...")
    model_no_interaction = '''
    glmer(MRT_isCorrect ~ final_concentration_kappa + MRT_angle_categorical + 
          VWM_median_rt_z + MRT_median_rt_z + VWM_accuracy_z + MRT_accuracy_z + 
          session_duration_z + focus_loss_duration_z + focus_loss_instances_z +
          (1 | participantId) + (1 | MRT_stimulusId),
          data = analysis_data, family = binomial(link = "logit"),
          control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000)))
    '''

    try:
        ro.r(f'model_no_interaction <- {model_no_interaction}')
        ro.r('lr_test_interaction <- anova(model_no_interaction, full_model)')
        with localconverter(ro.default_converter + pandas2ri.converter):
            lr_interaction = ro.conversion.rpy2py(ro.r('lr_test_interaction'))
        print("Interaction effect likelihood ratio test:")
        print(lr_interaction)
    except Exception as e:
        print(f"Error in interaction effect likelihood ratio test: {e}")
        raise

    return {
        'results': results,
        'lr_main': lr_main,
        'lr_interaction': lr_interaction,
        'model_object': 'full_model'
    }

def calculate_model_diagnostics():
    """
    Calculate model diagnostics and fit statistics.
    
    Returns:
    list: List of diagnostic metrics
    """
    print("\nCalculating model diagnostics...")
    
    diagnostics = []

    # Calculate pseudo-R²
    try:
        ro.r('null_model <- glmer(MRT_isCorrect ~ 1 + (1 | participantId) + (1 | MRT_stimulusId), data = analysis_data, family = binomial)')
        ro.r('loglik_full <- logLik(full_model)')
        ro.r('loglik_null <- logLik(null_model)')
        ro.r('pseudo_r2 <- 1 - (as.numeric(loglik_full) / as.numeric(loglik_null))')
        pseudo_r2 = float(ro.r('pseudo_r2')[0])
        diagnostics.append({
            'metric': 'pseudo_r_squared',
            'value': pseudo_r2,
            'interpretation': 'Model explained variance (higher is better)'
        })
        print(f"Pseudo-R²: {pseudo_r2:.4f}")
    except Exception as e:
        print(f"Error calculating pseudo-R²: {e}")

    # Check convergence
    try:
        ro.r('convergence_code <- full_model@optinfo$conv$opt')
        conv_code = int(ro.r('convergence_code')[0])
        diagnostics.append({
            'metric': 'convergence_code',
            'value': conv_code,
            'interpretation': 'Convergence status (0 = converged)'
        })
        print(f"Convergence code: {conv_code}")
    except Exception as e:
        print(f"Error checking convergence: {e}")

    # Random effects variance
    try:
        ro.r('random_effects <- VarCorr(full_model)')
        ro.r('participant_var <- as.numeric(random_effects$participantId)')
        ro.r('stimulus_var <- as.numeric(random_effects$MRT_stimulusId)')
        participant_var = float(ro.r('participant_var')[0])
        stimulus_var = float(ro.r('stimulus_var')[0])

        participant_interpretation = 'Between-participant variance in intercept'
        if participant_var < 0.001:
            participant_interpretation += ' - indicates singular fit (variance near zero)'

        diagnostics.extend([
            {
                'metric': 'participant_random_intercept_variance',
                'value': participant_var,
                'interpretation': participant_interpretation
            },
            {
                'metric': 'stimulus_random_intercept_variance',
                'value': stimulus_var,
                'interpretation': 'Between-stimulus variance in intercept'
            }
        ])
        print(f"Participant random intercept variance: {participant_var:.4f}")
        print(f"Stimulus random intercept variance: {stimulus_var:.4f}")
    except Exception as e:
        print(f"Error extracting random effects variance: {e}")

    # Model AIC and BIC
    try:
        ro.r('model_aic <- AIC(full_model)')
        ro.r('model_bic <- BIC(full_model)')
        aic = float(ro.r('model_aic')[0])
        bic = float(ro.r('model_bic')[0])
        diagnostics.extend([
            {
                'metric': 'AIC',
                'value': aic,
                'interpretation': 'Akaike Information Criterion (lower is better)'
            },
            {
                'metric': 'BIC',
                'value': bic,
                'interpretation': 'Bayesian Information Criterion (lower is better)'
            }
        ])
        print(f"AIC: {aic:.2f}")
        print(f"BIC: {bic:.2f}")
    except Exception as e:
        print(f"Error calculating AIC/BIC: {e}")

    # Test for overdispersion
    try:
        ro.r('residual_deviance <- deviance(full_model)')
        ro.r('df_residual <- df.residual(full_model)')
        ro.r('dispersion_param <- residual_deviance / df_residual')
        residual_deviance = float(ro.r('residual_deviance')[0])
        df_residual = float(ro.r('df_residual')[0])
        dispersion_param = float(ro.r('dispersion_param')[0])
        
        overdispersion_interpretation = 'Dispersion parameter (>1 indicates overdispersion, <1 underdispersion)'
        if dispersion_param > 1.2:
            overdispersion_interpretation += ' - Model shows overdispersion'
        elif dispersion_param < 0.8:
            overdispersion_interpretation += ' - Model shows underdispersion'
        else:
            overdispersion_interpretation += ' - Dispersion appears adequate'
        
        diagnostics.extend([
            {
                'metric': 'residual_deviance',
                'value': residual_deviance,
                'interpretation': 'Residual deviance of the model'
            },
            {
                'metric': 'degrees_of_freedom_residual',
                'value': df_residual,
                'interpretation': 'Residual degrees of freedom'
            },
            {
                'metric': 'dispersion_parameter',
                'value': dispersion_param,
                'interpretation': overdispersion_interpretation
            }
        ])
        print(f"Residual deviance: {residual_deviance:.2f}")
        print(f"Residual degrees of freedom: {df_residual}")
        print(f"Dispersion parameter: {dispersion_param:.4f}")
    except Exception as e:
        print(f"Error calculating overdispersion test: {e}")

    return diagnostics

def perform_posthoc_analysis(lr_interaction):
    """
    Perform post-hoc analyses including simple slopes if interaction is significant
    according to the likelihood ratio test (LRT) for the interaction.
    
    Parameters:
    lr_interaction (DataFrame): LRT results for interaction effect
    
    Returns:
    dict: Post-hoc analysis results
    """
    print("\nPerforming post-hoc analyses...")

    # Use LRT p-value to determine if interaction is significant
    try:
        # The LRT result is a DataFrame with a 'Pr(>Chisq)' column
        # The second row (index 1) is the p-value for the interaction
        lrt_pval = None
        if hasattr(lr_interaction, "iloc") and lr_interaction.shape[0] > 1:
            # Try to get the p-value from the second row
            if "Pr(>Chisq)" in lr_interaction.columns:
                lrt_pval = lr_interaction.loc[lr_interaction.index[1], "Pr(>Chisq)"]
            elif "Pr(>Chi)" in lr_interaction.columns:
                lrt_pval = lr_interaction.loc[lr_interaction.index[1], "Pr(>Chi)"]
        significant_interaction = lrt_pval is not None and lrt_pval < 0.025

        print(f"LRT p-value for interaction: {lrt_pval}")
        print(f"Significant interaction by LRT (α = 0.025): {significant_interaction}")

        if significant_interaction:
            print("Conducting simple slopes analysis...")
            
            ro.r('''
            library(emmeans)
            slope_test <- emtrends(full_model, ~ MRT_angle_categorical, var = "final_concentration_kappa")
            slope_summary <- summary(slope_test)
            ''')
            
            try:
                with localconverter(ro.default_converter + pandas2ri.converter):
                    slope_results = ro.conversion.rpy2py(ro.r('slope_summary'))
                print("Simple slopes results:")
                print(slope_results)
            except Exception as e:
                print(f"Error in simple slopes analysis: {e}")

        # Calculate predicted probabilities across angles
        print("\nCalculating predicted probabilities...")
        ro.r('''
        library(ggplot2)
        # Create prediction grid
        pred_data <- expand.grid(
            final_concentration_kappa = seq(min(analysis_data$final_concentration_kappa, na.rm=TRUE),
                                           max(analysis_data$final_concentration_kappa, na.rm=TRUE),
                                           length.out = 50),
            MRT_angle_categorical = c("0°", "50°", "100°", "150°"),
            VWM_median_rt_z = 0,
            MRT_median_rt_z = 0,
            VWM_accuracy_z = 0,
            MRT_accuracy_z = 0,
            session_duration_z = 0,
            focus_loss_duration_z = 0,
            focus_loss_instances_z = 0
        )

        # Add dummy random effects (set to typical participant/stimulus)
        pred_data$participantId <- analysis_data$participantId[1]
        pred_data$MRT_stimulusId <- analysis_data$MRT_stimulusId[1]

        # Generate predictions
        pred_data$predicted_prob <- predict(full_model, newdata = pred_data, type = "response", re.form = NA)
        ''')

        with localconverter(ro.default_converter + pandas2ri.converter):
            predictions = ro.conversion.rpy2py(ro.r('pred_data'))
        print("Predicted probabilities calculated successfully")
        print(f"Prediction data shape: {predictions.shape}")

    except Exception as e:
        print(f"Error in post-hoc analysis: {e}")
        return {}

    return {'predictions_calculated': True}

def save_results(results, diagnostics, analysis_data):
    """
    Save all results to CSV files.
    
    Parameters:
    results (dict): Model results
    diagnostics (list): Model diagnostics
    analysis_data (DataFrame): Analysis dataset
    """
    print("\nSaving results to CSV files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save model results
    results_df = pd.DataFrame(results['results'])
    results_file = f"outputs/MRT_mixed_effects_results_{timestamp}.csv"
    results_df.to_csv(results_file, index=False)
    print(f"Model results saved to: {results_file}")
    print("Results summary:")
    print(results_df[['parameter', 'estimate', 'p_value', 'significance']])
    
    # Save model diagnostics
    diagnostics_df = pd.DataFrame(diagnostics)
    diagnostics_file = f"outputs/MRT_model_diagnostics_{timestamp}.csv"
    diagnostics_df.to_csv(diagnostics_file, index=False)
    print(f"Model diagnostics saved to: {diagnostics_file}")
    print("Diagnostics summary:")
    print(diagnostics_df)
    
    # Save analysis dataset
    # Select only required columns
    required_cols = ['participantId', 'MRT_trial', 'MRT_angle_degrees', 'MRT_angle_categorical',
                    'MRT_isCorrect', 'MRT_stimulusId', 'final_concentration_kappa',
                    'VWM_median_rt_z', 'MRT_median_rt_z', 'VWM_accuracy_z', 'MRT_accuracy_z',
                    'session_duration_z', 'focus_loss_duration_z', 'focus_loss_instances_z']
    
    dataset_output = analysis_data[required_cols].copy()
    dataset_file = f"outputs/MRT_analysis_dataset_{timestamp}.csv"
    dataset_output.to_csv(dataset_file, index=False)
    print(f"Analysis dataset saved to: {dataset_file}")
    print(f"Analysis dataset shape: {dataset_output.shape}")

def main():
    """
    Main function to execute the mixed-effects analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT mixed-effects analysis...")
        print("=" * 50)
        
        # Load input data
        trial_data, precision_params, domain_metrics = load_input_data()
        
        # Prepare analysis dataset
        analysis_data = prepare_analysis_dataset(trial_data, precision_params, domain_metrics)
        
        # Fit mixed-effects model
        model_results = fit_mixed_effects_model(analysis_data)
        
        # Calculate diagnostics
        diagnostics = calculate_model_diagnostics()
        
        # Perform post-hoc analyses
        posthoc_results = perform_posthoc_analysis(model_results['lr_interaction'])
        
        # Save results
        save_results(model_results, diagnostics, analysis_data)
        
        print("\n" + "=" * 50)
        print("Analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"\nError during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
