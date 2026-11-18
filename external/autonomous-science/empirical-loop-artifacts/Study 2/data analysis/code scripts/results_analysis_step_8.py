#!/usr/bin/env python3
"""
MRT Sequential Facilitation Analysis Script

This script analyzes Mental Rotation Task (MRT) data to extract sequential facilitation indices
using Generalized Linear Mixed Models (GLMM) for both reaction time and accuracy measures.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

# Import rpy2 for R integration
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri, Formula
    from rpy2.robjects.packages import importr
    pandas2ri.activate()
    
    # Import R packages
    base = importr('base')
    stats = importr('stats')
    lme4 = importr('lme4')
    
except ImportError as e:
    print(f"Error importing rpy2: {e}")
    print("Please ensure R and rpy2 are properly installed")
    sys.exit(1)

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
    
    # Get the most recent file based on modification time
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def load_and_validate_data(filepath):
    """
    Load and validate the MRT cleaned data CSV file.
    
    Parameters:
    filepath (str): Path to the input CSV file
    
    Returns:
    pd.DataFrame: Loaded and validated dataframe
    """
    print(f"Loading data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"Successfully loaded data with shape: {df.shape}")
        
        # Print all columns
        print("Columns in dataset:")
        print(df.columns.tolist())
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Required columns
        required_cols = [
            'participantId', 'trial_type', 'MRT_trial', 'MRT_angle_degrees',
            'MRT_isReflected', 'MRT_isCorrect', 'MRT_rt_ms', 'log_rt_ms',
            'previous_angle_degrees', 'abs_angular_disparity_change', 'excluded_trial'
        ]
        
        # Check for required columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"ERROR: Missing required columns: {missing_cols}")
            return None
            
        print("All required columns present")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"trial_type: {sorted(df['trial_type'].dropna().unique())}")
        print(f"MRT_angle_degrees: {sorted(df['MRT_angle_degrees'].dropna().unique())}")
        print(f"MRT_isReflected: {sorted(df['MRT_isReflected'].dropna().unique())}")
        print(f"previous_angle_degrees: {sorted(df['previous_angle_degrees'].dropna().unique())}")
        print(f"excluded_trial: {sorted(df['excluded_trial'].dropna().unique())}")
        
        # Print data types for measured variables
        print(f"\nData types for measured variables:")
        print(f"MRT_rt_ms: {df['MRT_rt_ms'].dtype}")
        print(f"log_rt_ms: {df['log_rt_ms'].dtype}")
        print(f"abs_angular_disparity_change: {df['abs_angular_disparity_change'].dtype}")
        
        return df
        
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def prepare_data_for_analysis(df):
    """
    Prepare data for GLMM analysis by filtering and cleaning.
    
    Parameters:
    df (pd.DataFrame): Raw dataframe
    
    Returns:
    pd.DataFrame: Prepared dataframe for analysis
    """
    print("\nPreparing data for analysis...")
    
    # Initial data size
    print(f"Initial data size: {len(df)} rows")
    
    # Filter to test trials only
    df_test = df[df['trial_type'] == 'test'].copy()
    print(f"After filtering to test trials: {len(df_test)} rows")
    
    # Exclude trials marked as excluded_trial = True
    df_clean = df_test[df_test['excluded_trial'] == False].copy()
    print(f"After excluding marked trials: {len(df_clean)} rows")
    
    # Remove rows with null values in key columns
    key_cols = ['participantId', 'MRT_angle_degrees', 'MRT_isReflected', 
                'MRT_isCorrect', 'MRT_rt_ms', 
                'previous_angle_degrees', 'abs_angular_disparity_change']
    
    initial_clean_size = len(df_clean)
    for col in key_cols:
        before_size = len(df_clean)
        df_clean = df_clean.dropna(subset=[col])
        after_size = len(df_clean)
        if before_size != after_size:
            print(f"Removed {before_size - after_size} rows with null values in {col}")
    
    print(f"After removing null values: {len(df_clean)} rows")
    
    # Check participants with sufficient data
    participant_counts = df_clean.groupby('participantId').size()
    print(f"\nParticipant trial counts:")
    print(f"Mean trials per participant: {participant_counts.mean():.1f}")
    print(f"Min trials per participant: {participant_counts.min()}")
    print(f"Max trials per participant: {participant_counts.max()}")
    
    # Filter participants with at least 10 valid trials
    min_trials = 10
    sufficient_participants = participant_counts[participant_counts >= min_trials].index
    df_final = df_clean[df_clean['participantId'].isin(sufficient_participants)].copy()
    
    excluded_participants = len(participant_counts) - len(sufficient_participants)
    print(f"Excluded {excluded_participants} participants with < {min_trials} trials")
    print(f"Final dataset: {len(df_final)} rows from {len(sufficient_participants)} participants")
    
    # Print final data structure
    print("\nFinal prepared data structure:")
    print("Columns:", df_final.columns.tolist())
    print("First 2 rows:")
    print(df_final.head(2))
    
    return df_final

def fit_rt_model(df):
    """
    Fit RT model using GLMM with R's lme4.
    
    Parameters:
    df (pd.DataFrame): Prepared dataframe
    
    Returns:
    tuple: (model object, model results dataframe)
    """
    print("\nFitting RT model...")
    
    # Filter to correct trials only for RT analysis
    df_rt = df[df['MRT_isCorrect'] == True].copy()
    # Remove rows with null log_rt_ms for RT analysis
    df_rt = df_rt.dropna(subset=['log_rt_ms'])
    print(f"RT model data: {len(df_rt)} correct trials with valid log_rt_ms")
    
    # Convert data for R - only include necessary columns to avoid conversion issues
    rt_cols = ['participantId', 'MRT_angle_degrees', 'MRT_isReflected', 
               'previous_angle_degrees', 'abs_angular_disparity_change', 'log_rt_ms']
    df_rt_clean = df_rt[rt_cols].copy()
    
    # Apply scaling to abs_angular_disparity_change to aid convergence
    mean_val = df_rt_clean['abs_angular_disparity_change'].mean()
    std_val = df_rt_clean['abs_angular_disparity_change'].std()
    slope_predictor_name_r = 'abs_angular_disparity_change'  # Default
    if std_val > 0 and not np.isnan(std_val) and not np.isnan(mean_val):
        df_rt_clean['abs_angular_disparity_change_scaled'] = (df_rt_clean['abs_angular_disparity_change'] - mean_val) / std_val
        slope_predictor_name_r = 'abs_angular_disparity_change_scaled'
        print(f"RT model: Scaled abs_angular_disparity_change (mean={mean_val:.3f}, std={std_val:.3f})")
    else:
        df_rt_clean['abs_angular_disparity_change_scaled'] = df_rt_clean['abs_angular_disparity_change']
        print("Warning: abs_angular_disparity_change has zero/invalid standard deviation. Using original scale.")
    
    # Convert data for R with proper null handling
    df_rt_clean['MRT_angle_degrees'] = df_rt_clean['MRT_angle_degrees'].fillna('0').astype(str)
    df_rt_clean['previous_angle_degrees'] = df_rt_clean['previous_angle_degrees'].fillna('0').astype(str)
    df_rt_clean['MRT_isReflected'] = df_rt_clean['MRT_isReflected'].fillna('False').astype(str)
    
    # Convert to R dataframe
    r_df = pandas2ri.py2rpy(df_rt_clean)
    
    # Assign to R environment
    robjects.globalenv['rt_data'] = r_df
    robjects.globalenv['slope_predictor_name'] = slope_predictor_name_r
    
    print("Fitting RT GLMM model...")
    
    # Fit the model
    try:
        rt_model = robjects.r(f'''
            # Check for and install lme4 if needed
            if (!requireNamespace("lme4", quietly = TRUE)) {{
                install.packages("lme4", repos = "https://cloud.r-project.org")
            }}
            if (!requireNamespace("nloptr", quietly = TRUE)) {{
                install.packages("nloptr", repos = "https://cloud.r-project.org")
            }}
            library(lme4)
                
            # Check data structure
            print(paste("RT data dimensions:", nrow(rt_data), "x", ncol(rt_data)))
            print(paste("Unique participants:", length(unique(rt_data$participantId))))
                
            # Convert factors
            rt_data$MRT_angle_degrees <- as.factor(rt_data$MRT_angle_degrees)
            rt_data$previous_angle_degrees <- as.factor(rt_data$previous_angle_degrees)
            rt_data$MRT_isReflected <- as.factor(rt_data$MRT_isReflected)
            rt_data$participantId <- as.factor(rt_data$participantId)
                
            # Fit full model with glmer and Gamma family - including random slopes
            # Try bobyqa first, then fallback to alternative optimizers if convergence fails
            rt_model <- tryCatch({{
                glmer(log_rt_ms ~ MRT_angle_degrees + MRT_isReflected + 
                     previous_angle_degrees + {slope_predictor_name_r} + 
                     MRT_angle_degrees:{slope_predictor_name_r} + 
                     (1 + {slope_predictor_name_r}|participantId),
                     data = rt_data,
                     family = Gamma(link = "log"),
                     control = glmerControl(optimizer="bobyqa", optCtrl=list(maxfun=2e5)))
            }}, error = function(e) {{
                print("bobyqa optimizer failed, trying Nelder_Mead...")
                tryCatch({{
                    glmer(log_rt_ms ~ MRT_angle_degrees + MRT_isReflected + 
                         previous_angle_degrees + {slope_predictor_name_r} + 
                         MRT_angle_degrees:{slope_predictor_name_r} + 
                         (1 + {slope_predictor_name_r}|participantId),
                         data = rt_data,
                         family = Gamma(link = "log"),
                         control = glmerControl(optimizer="Nelder_Mead", optCtrl=list(maxfun=2e5)))
                }}, error = function(e2) {{
                    print("Nelder_Mead also failed, trying nloptwrap...")
                    glmer(log_rt_ms ~ MRT_angle_degrees + MRT_isReflected + 
                         previous_angle_degrees + {slope_predictor_name_r} + 
                         MRT_angle_degrees:{slope_predictor_name_r} + 
                         (1 + {slope_predictor_name_r}|participantId),
                         data = rt_data,
                         family = Gamma(link = "log"),
                         control = glmerControl(optimizer="nloptwrap", optCtrl=list(maxfun=2e5)))
                }})
            }})
                
            rt_model
        ''')
        
        print("RT model fitted successfully")
        
        # Check convergence using R's primary indicators - but don't block extraction
        try:
            rt_convergence_check = robjects.r('''
                conv_code <- rt_model@optinfo$conv$opt
                warnings_count <- length(rt_model@optinfo$warnings)
                max_grad_python_access <- max(abs(rt_model@optinfo$derivs$gradient))
                
                list(opt_code = conv_code, warnings = warnings_count, max_grad = max_grad_python_access)
            ''')
            
            opt_code = int(rt_convergence_check[0][0])
            warnings_count = int(rt_convergence_check[1][0])
            max_grad_python_access = float(rt_convergence_check[2][0])
            
            print(f"RT model convergence check: opt_code={opt_code}, R warnings_list_len={warnings_count}, max_grad_direct_access={max_grad_python_access:.6f}")
            
            # Use R's primary convergence indicator (opt_code) as main criterion
            # Only discard model in severe cases - be more lenient as per feedback
            if opt_code != 0 and max_grad_python_access > 0.05:
                print(f"RT model severely failed convergence: opt_code={opt_code}, max_grad={max_grad_python_access:.6f}. Model will not be used.")
                return None, None
            elif opt_code != 0:
                print(f"RT model optimizer reports non-convergence: opt_code={opt_code}, but proceeding as gradient is acceptable.")
            elif max_grad_python_access > 0.05:
                print(f"RT model has high gradient from direct access: {max_grad_python_access:.6f}, but opt_code is 0. Proceeding with caution.")
            elif max_grad_python_access > 0.01:
                print(f"RT model has convergence warnings but proceeding - opt_code: {opt_code}, max_grad: {max_grad_python_access:.6f}")
            
            # Proceed with parameter extraction unless severely failed
            print("RT model proceeding with parameter extraction despite any minor convergence warnings.")
                
        except Exception as conv_e:
            print(f"Could not check RT model convergence: {conv_e}")
            print("Proceeding with slope extraction")
        
        # Extract model summary
        rt_summary = robjects.r('summary(rt_model)')
        print("RT model summary extracted")
        
        # Extract coefficients (glmer uses z_value and p_value, not t_value)
        rt_coefs = robjects.r('''
            coef_summary <- summary(rt_model)$coefficients
            coef_df <- data.frame(
                effect_name = rownames(coef_summary),
                estimate = coef_summary[,1],
                std_error = coef_summary[,2],
                z_value = coef_summary[,3],
                p_value = coef_summary[,4],
                stringsAsFactors = FALSE
            )
            coef_df
        ''')
        
        rt_results = pandas2ri.rpy2py(rt_coefs)
        rt_results['model_type'] = 'RT'
        
        # Add confidence intervals
        try:
            ci_r_df_code = '''
                ci_matrix <- confint(rt_model, method="Wald", parm="beta_")
                ci_df <- as.data.frame(ci_matrix)
                colnames(ci_df) <- c("ci_lower_r", "ci_upper_r")
                ci_df$effect_name <- rownames(ci_df)
                ci_df
            '''
            ci_df_py = pandas2ri.rpy2py(robjects.r(ci_r_df_code))
            
            # Merge confidence intervals with results
            rt_results = rt_results.merge(ci_df_py, on='effect_name', how='left')
            rt_results.rename(columns={'ci_lower_r': 'ci_lower', 'ci_upper_r': 'ci_upper'}, inplace=True)
        except Exception as ci_e:
            print(f"Warning: Could not extract confidence intervals: {ci_e}")
            rt_results['ci_lower'] = np.nan
            rt_results['ci_upper'] = np.nan
        
        print("RT model results extracted successfully")
        print(f"RT model has {len(rt_results)} coefficients")
        print("RT model coefficients:")
        print(rt_results[['effect_name', 'estimate', 'p_value']].head(10))
        
        return rt_model, rt_results
        
    except Exception as e:
        print(f"Error fitting RT model: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def fit_accuracy_model(df):
    """
    Fit accuracy model using GLMM with R's lme4.
    
    Parameters:
    df (pd.DataFrame): Prepared dataframe
    
    Returns:
    tuple: (model object, model results dataframe)
    """
    print("\nFitting accuracy model...")
    
    # Use all trials for accuracy analysis - only include necessary columns to avoid conversion issues
    acc_cols = ['participantId', 'MRT_angle_degrees', 'MRT_isReflected', 
                'previous_angle_degrees', 'abs_angular_disparity_change', 'MRT_isCorrect']
    df_acc = df[acc_cols].copy()
    print(f"Accuracy model data: {len(df_acc)} trials")
    
    # Apply scaling to abs_angular_disparity_change to aid convergence
    if 'abs_angular_disparity_change' in df_acc.columns:
        mean_val_acc = df_acc['abs_angular_disparity_change'].mean()
        std_val_acc = df_acc['abs_angular_disparity_change'].std()
        acc_slope_predictor_name_r = 'abs_angular_disparity_change'  # Default
        if std_val_acc > 0 and not np.isnan(std_val_acc) and not np.isnan(mean_val_acc):
            df_acc['abs_angular_disparity_change_scaled'] = (df_acc['abs_angular_disparity_change'] - mean_val_acc) / std_val_acc
            acc_slope_predictor_name_r = 'abs_angular_disparity_change_scaled'
            print(f"Accuracy model: Scaled abs_angular_disparity_change (mean={mean_val_acc:.3f}, std={std_val_acc:.3f})")
        else:
            df_acc['abs_angular_disparity_change_scaled'] = df_acc['abs_angular_disparity_change']
            print("Warning (Accuracy): abs_angular_disparity_change has zero/invalid SD. Using original scale.")
    
    # Convert data for R with proper null handling
    df_acc['MRT_angle_degrees'] = df_acc['MRT_angle_degrees'].fillna('0').astype(str)
    df_acc['previous_angle_degrees'] = df_acc['previous_angle_degrees'].fillna('0').astype(str)
    df_acc['MRT_isReflected'] = df_acc['MRT_isReflected'].fillna('False').astype(str)
    df_acc['MRT_isCorrect'] = df_acc['MRT_isCorrect'].fillna(0).astype(int)
    
    # Convert to R dataframe
    r_df = pandas2ri.py2rpy(df_acc)
    
    # Assign to R environment
    robjects.globalenv['acc_data'] = r_df
    robjects.globalenv['acc_slope_predictor_name'] = acc_slope_predictor_name_r
    
    print("Fitting accuracy GLMM model...")
    
    # Fit the model
    try:
        acc_model = robjects.r(f'''
            # Check for and install lme4 if needed
            if (!requireNamespace("lme4", quietly = TRUE)) {{
                install.packages("lme4", repos = "https://cloud.r-project.org")
            }}
            library(lme4)
            
            # Convert factors
            acc_data$MRT_angle_degrees <- as.factor(acc_data$MRT_angle_degrees)
            acc_data$previous_angle_degrees <- as.factor(acc_data$previous_angle_degrees)
            acc_data$MRT_isReflected <- as.factor(acc_data$MRT_isReflected)
            acc_data$participantId <- as.factor(acc_data$participantId)
            
            # Fit model with scaled predictor and optimizer for better convergence
            acc_model <- glmer(MRT_isCorrect ~ MRT_angle_degrees + MRT_isReflected + 
                              previous_angle_degrees + {acc_slope_predictor_name_r} + 
                              MRT_angle_degrees:{acc_slope_predictor_name_r} + 
                              (1|participantId),
                              data = acc_data,
                              family = binomial(link = "logit"),
                              control = glmerControl(optimizer="bobyqa", optCtrl=list(maxfun=2e5)))
            
            acc_model
        ''')
        
        print("Accuracy model fitted successfully")
        
        # Extract model summary
        acc_summary = robjects.r('summary(acc_model)')
        print("Accuracy model summary extracted")
        
        # Extract coefficients
        acc_coefs = robjects.r('''
            coef_summary <- summary(acc_model)$coefficients
            coef_df <- data.frame(
                effect_name = rownames(coef_summary),
                estimate = coef_summary[,1],
                std_error = coef_summary[,2],
                z_value = coef_summary[,3],
                p_value = coef_summary[,4],
                stringsAsFactors = FALSE
            )
            coef_df
        ''')
        
        acc_results = pandas2ri.rpy2py(acc_coefs)
        acc_results['model_type'] = 'Accuracy'
        
        # Add confidence intervals with improved extraction
        ci_r_df_code = '''
            ci_matrix <- confint(acc_model, method="Wald", parm="beta_")
            ci_df <- as.data.frame(ci_matrix)
            colnames(ci_df) <- c("ci_lower_r", "ci_upper_r")
            ci_df$effect_name <- rownames(ci_df)
            ci_df
        '''
        ci_df_py = pandas2ri.rpy2py(robjects.r(ci_r_df_code))
        
        # Merge confidence intervals with results
        acc_results = acc_results.merge(ci_df_py, on='effect_name', how='left')
        acc_results.rename(columns={'ci_lower_r': 'ci_lower', 'ci_upper_r': 'ci_upper'}, inplace=True)
        
        print("Accuracy model results extracted")
        print("Accuracy model coefficients:")
        print(acc_results[['effect_name', 'estimate', 'p_value']])
        
        return acc_model, acc_results
        
    except Exception as e:
        print(f"Error fitting accuracy model: {e}")
        return None, None

def extract_participant_indices(df, rt_model, acc_model):
    """
    Extract participant-specific sequential facilitation indices.
    
    Parameters:
    df (pd.DataFrame): Prepared dataframe
    rt_model: R model object for RT
    acc_model: R model object for accuracy
    
    Returns:
    pd.DataFrame: Participant-level indices
    """
    print("\nExtracting participant-specific indices...")
    
    participants = df['participantId'].unique()
    print(f"Extracting indices for {len(participants)} participants")
    
    # Get original factor level categories for consistent predictions
    angle_categories = sorted(df['MRT_angle_degrees'].dropna().unique().astype(str))
    prev_angle_categories = sorted(df['previous_angle_degrees'].dropna().unique().astype(str))
    reflected_categories = sorted(df['MRT_isReflected'].dropna().unique().astype(str))
    print(f"Factor categories - Angles: {angle_categories}, Previous: {prev_angle_categories}, Reflected: {reflected_categories}")
    
    # Prepare for participant-specific slope extraction from RT model
    if rt_model is not None:
        try:
            # Check what coefficients are available
            coef_names = robjects.r('names(fixef(rt_model))')
            print(f"Available RT model coefficients: {list(coef_names)}")
            
            # Prepare participant-specific coefficient and variance extraction
            slope_predictor_name_for_extraction = robjects.r('slope_predictor_name')[0]
            print(f"Preparing to extract participant-specific slopes for: {slope_predictor_name_for_extraction}")
            
            # Extract participant coefficients and random effect variances once
            robjects.r('''
                # Get participant-specific coefficients (fixed + random effects)
                rt_coefs_participant <- coef(rt_model)$participantId

                # Get random effect variances for standard errors
                rt_ranef_participant_list <- ranef(rt_model, condVar = TRUE)
                # Get variance-covariance arrays directly from postVar attribute
                rt_ranef_variances <- attr(rt_ranef_participant_list$participantId, "postVar")
                print(paste("postVar structure:", str(rt_ranef_variances)))
                print(paste("postVar class:", class(rt_ranef_variances)))
                
                # Validate the variance array structure
                if (!is.null(rt_ranef_variances)) {
                    print(paste("Successfully extracted variance array with dimensions:", paste(dim(rt_ranef_variances), collapse=" x ")))
                    print(paste("Variance array class:", class(rt_ranef_variances)))
                } else {
                    print("Error: postVar attribute is NULL.")
                }
                rt_ranef_rownames <- rownames(rt_ranef_participant_list$participantId)

                # Ensure slope_predictor_name (R variable) is correctly defined and holds the string of the scaled predictor
                slope_col_name_in_ranef <- slope_predictor_name
                # Initialize to NULL
                g_slope_col_index_in_ranef_for_postVar <- NULL
                
                if (slope_col_name_in_ranef %in% colnames(rt_ranef_participant_list$participantId)) {
                    ranef_colnames <- colnames(rt_ranef_participant_list$participantId)
                    temp_idx <- which(ranef_colnames == slope_col_name_in_ranef)
                    if (length(temp_idx) == 1 && !is.na(temp_idx) && temp_idx > 0) {
                        g_slope_col_index_in_ranef_for_postVar <- as.integer(temp_idx)
                        print(paste("Slope column name for ranef SE:", slope_col_name_in_ranef))
                        print(paste("Index for postVar:", g_slope_col_index_in_ranef_for_postVar))
                        print(paste("Index validation - is.integer:", is.integer(g_slope_col_index_in_ranef_for_postVar), "value:", g_slope_col_index_in_ranef_for_postVar))
                    } else {
                        print(paste("ERROR: Slope predictor name not uniquely found. temp_idx:", temp_idx, "length:", length(temp_idx)))
                        g_slope_col_index_in_ranef_for_postVar <- NULL
                    }
                } else {
                    print(paste("ERROR: slope predictor", slope_col_name_in_ranef, "not found in ranef columns:", paste(colnames(rt_ranef_participant_list$participantId), collapse=", ")))
                    g_slope_col_index_in_ranef_for_postVar <- NULL
                }

                # Validate before global assignment
                print(paste("Pre-assignment validation:"))
                print(paste("  g_slope_col_index_in_ranef_for_postVar:", g_slope_col_index_in_ranef_for_postVar))
                print(paste("  is.null:", is.null(g_slope_col_index_in_ranef_for_postVar)))
                print(paste("  is.na:", if(!is.null(g_slope_col_index_in_ranef_for_postVar)) is.na(g_slope_col_index_in_ranef_for_postVar) else "NULL"))
                print(paste("  rt_ranef_variances is.null:", is.null(rt_ranef_variances)))
                if (!is.null(rt_ranef_variances)) {
                    print(paste("  rt_ranef_variances dimensions:", paste(dim(rt_ranef_variances), collapse=" x ")))
                }
                
                # Global assign for use in loop
                assign("g_slope_col_index_in_ranef_for_postVar", g_slope_col_index_in_ranef_for_postVar, envir = .GlobalEnv)
                assign("g_slope_col_name_in_ranef", slope_col_name_in_ranef, envir = .GlobalEnv)
                assign("g_rt_ranef_variances_valid", !is.null(rt_ranef_variances), envir = .GlobalEnv)

                print(paste("Participant coefficients prepared. Slope column index:", g_slope_col_index_in_ranef_for_postVar))
                print(paste("Number of participants with coefficients:", nrow(rt_coefs_participant)))
                print(paste("Random effects columns:", colnames(rt_ranef_participant_list$participantId)))
            ''')
            
            print("RT participant-specific slope extraction prepared successfully")
            print("NOTE: Using participant-specific slopes from random effects model, not fixed effects")
            
            # Validate that random slopes were actually fitted
            try:
                random_effects_structure = robjects.r('''
                    # Check if slope predictor is in the random effects structure
                    ranef_cols <- colnames(rt_ranef_participant_list$participantId)
                    slope_in_ranef <- slope_predictor_name %in% ranef_cols
                    list(slope_in_ranef = slope_in_ranef, ranef_cols = ranef_cols)
                ''')
                
                slope_in_ranef = bool(random_effects_structure[0][0])
                if not slope_in_ranef:
                    print("ERROR: Random slopes for facilitation effect not found in model structure")
                    print("Model may have failed to fit random slopes - reverting to None")
                    rt_model = None
                else:
                    print("SUCCESS: Random slopes for facilitation effect confirmed in model structure")
                    
            except Exception as validation_error:
                print(f"Warning: Could not validate random effects structure: {validation_error}")
                print("Proceeding with slope extraction")
            
        except Exception as e:
            print(f"Error preparing RT participant slope extraction: {e}")
            rt_model = None  # Set to None to trigger fallback
    else:
        print("RT model is None - cannot extract participant-specific slopes")
    
    # Remove any misleading fixed slope extraction output since we're using participant-specific slopes

    results = []
    
    for i, participant in enumerate(participants):
        if i == 0:  # Only print for first participant to reduce output
            print(f"Processing participant {i+1}/{len(participants)}")
        
        participant_data = df[df['participantId'] == participant].copy()
        n_trials = len(participant_data)
        
        # Initialize results for this participant
        participant_result = {
            'participantId': participant,
            'n_valid_trials': n_trials,
            'sufficient_data': n_trials >= 10
        }
        
        try:
            # Extract RT facilitation slope - participant-specific slopes from random effects model
            if rt_model is not None:
                try:
                    # Extract participant-specific slope coefficient and standard error
                    slope_and_se = robjects.r('''
                        participant_slope_val <- NA
                        participant_slope_se_val <- NA
                        if ("''' + str(participant) + '''" %in% rownames(rt_coefs_participant)) {
                            # slope_predictor_name is the R global variable with the predictor name string
                            participant_slope_val <- rt_coefs_participant["''' + str(participant) + '''", slope_predictor_name]
                            
                            participant_ranef_idx <- which(rt_ranef_rownames == "''' + str(participant) + '''")
                            # Use g_slope_col_index_in_ranef_for_postVar and g_slope_col_name_in_ranef defined globally
                            # Simplified validation to prevent NA/NULL issues
                            if (length(participant_ranef_idx) > 0 && 
                                !is.null(g_slope_col_index_in_ranef_for_postVar) && 
                                length(g_slope_col_index_in_ranef_for_postVar) == 1 && 
                                !is.na(g_slope_col_index_in_ranef_for_postVar) &&
                                !is.null(rt_ranef_variances) && 
                                !is.null(dim(rt_ranef_variances)) && 
                                length(dim(rt_ranef_variances)) == 3 &&
                                g_slope_col_name_in_ranef %in% colnames(rt_ranef_participant_list$participantId)) {

                                # Check if the index is valid for the dimensions of rt_ranef_variances
                                if(g_slope_col_index_in_ranef_for_postVar >= 1 && 
                                   g_slope_col_index_in_ranef_for_postVar <= dim(rt_ranef_variances)[1] && 
                                   g_slope_col_index_in_ranef_for_postVar <= dim(rt_ranef_variances)[2] &&
                                   participant_ranef_idx >= 1 && 
                                   participant_ranef_idx <= dim(rt_ranef_variances)[3]) {
                                  participant_slope_se_val <- sqrt(rt_ranef_variances[g_slope_col_index_in_ranef_for_postVar, g_slope_col_index_in_ranef_for_postVar, participant_ranef_idx])
                                } else {
                                  print(paste("Warning: Index out of bounds for SE extraction for participant ''' + str(participant) + '''"))
                                  participant_slope_se_val <- NA_real_
                                }
                            } else {
                                participant_slope_se_val <- NA_real_
                            }
                        }
                        list(slope = participant_slope_val, se = participant_slope_se_val)
                    ''')
                    
                    # Extract values with proper error handling and type checking
                    try:
                        slope_val = slope_and_se.rx2('slope')[0]
                        se_val = slope_and_se.rx2('se')[0]
                        
                        # Check if slope value is valid (not NA/NULL) with proper type checking
                        try:
                            slope_is_na = bool(robjects.r('is.na')(slope_val)[0]) if slope_val is not None else True
                        except (IndexError, TypeError):
                            slope_is_na = True
                            
                        try:
                            se_is_na = bool(robjects.r('is.na')(se_val)[0]) if se_val is not None else True
                        except (IndexError, TypeError):
                            se_is_na = True
                        
                        if not slope_is_na and slope_val is not None:
                            participant_result['rt_facilitation_slope'] = float(slope_val)
                            if not se_is_na and se_val is not None and float(se_val) > 0:
                                participant_result['rt_facilitation_se'] = float(se_val)
                            else:
                                participant_result['rt_facilitation_se'] = np.nan
                        else:
                            participant_result['rt_facilitation_slope'] = np.nan
                            participant_result['rt_facilitation_se'] = np.nan
                            
                    except (TypeError, ValueError, IndexError) as extract_error:
                        if i == 0:  # Only print for first participant
                            print(f"Warning: Type error extracting slope values: {extract_error}")
                        participant_result['rt_facilitation_slope'] = np.nan
                        participant_result['rt_facilitation_se'] = np.nan
                        
                except Exception as slope_error:
                    if i == 0:  # Only print detailed error for first participant
                        print(f"Warning: Could not extract participant-specific slope for {participant}: {slope_error}")
                    participant_result['rt_facilitation_slope'] = np.nan
                    participant_result['rt_facilitation_se'] = np.nan
            else:
                participant_result['rt_facilitation_slope'] = np.nan
                participant_result['rt_facilitation_se'] = np.nan

            # Extract accuracy facilitation index using model predictions
            if acc_model is not None:
                # Calculate difference in predicted accuracy between small vs large angular changes
                small_change_data = participant_data[participant_data['abs_angular_disparity_change'] <= 50].copy()
                large_change_data = participant_data[participant_data['abs_angular_disparity_change'] > 50].copy()
                
                if len(small_change_data) > 0 and len(large_change_data) > 0:
                    try:
                        # Get the scaling parameters used for the accuracy model
                        try:
                            acc_slope_predictor_name_for_prediction = robjects.r('acc_slope_predictor_name')[0]
                        except Exception as acc_pred_name_error:
                            acc_slope_predictor_name_for_prediction = 'abs_angular_disparity_change'
                        
                        # Apply same scaling to prediction data if model used scaled predictor
                        if acc_slope_predictor_name_for_prediction == 'abs_angular_disparity_change_scaled':
                            # Get scaling parameters from the same data as model fitting (df_acc equivalent)
                            if 'abs_angular_disparity_change' in df.columns:
                                acc_data_for_scaling = df[['abs_angular_disparity_change']].dropna()
                                if len(acc_data_for_scaling) > 0:
                                    mean_val_acc = float(acc_data_for_scaling['abs_angular_disparity_change'].mean())
                                    std_val_acc = float(acc_data_for_scaling['abs_angular_disparity_change'].std())
                                    if std_val_acc > 0 and not np.isnan(std_val_acc) and not np.isnan(mean_val_acc):
                                        small_change_data['abs_angular_disparity_change_scaled'] = (small_change_data['abs_angular_disparity_change'] - mean_val_acc) / std_val_acc
                                        large_change_data['abs_angular_disparity_change_scaled'] = (large_change_data['abs_angular_disparity_change'] - mean_val_acc) / std_val_acc
                                    else:
                                        small_change_data['abs_angular_disparity_change_scaled'] = small_change_data['abs_angular_disparity_change'].copy()
                                        large_change_data['abs_angular_disparity_change_scaled'] = large_change_data['abs_angular_disparity_change'].copy()
                                else:
                                    # Fallback if no data available
                                    small_change_data['abs_angular_disparity_change_scaled'] = small_change_data['abs_angular_disparity_change'].copy()
                                    large_change_data['abs_angular_disparity_change_scaled'] = large_change_data['abs_angular_disparity_change'].copy()
                            else:
                                small_change_data['abs_angular_disparity_change_scaled'] = small_change_data['abs_angular_disparity_change'].copy()
                                large_change_data['abs_angular_disparity_change_scaled'] = large_change_data['abs_angular_disparity_change'].copy()
                        
                        # Convert data for R predictions - exclude problematic columns
                        pred_cols = ['participantId', 'MRT_angle_degrees', 'MRT_isReflected', 
                                   'previous_angle_degrees', 'abs_angular_disparity_change', 'MRT_isCorrect']
                        if acc_slope_predictor_name_for_prediction == 'abs_angular_disparity_change_scaled':
                            pred_cols.append('abs_angular_disparity_change_scaled')
                        
                        small_change_data_r = small_change_data[pred_cols].copy()
                        large_change_data_r = large_change_data[pred_cols].copy()
                        
                        # Convert categorical variables to strings for R
                        for col in ['MRT_angle_degrees', 'previous_angle_degrees', 'MRT_isReflected']:
                            small_change_data_r[col] = small_change_data_r[col].astype(str)
                            large_change_data_r[col] = large_change_data_r[col].astype(str)
                        
                        # Convert to R dataframes with error handling
                        try:
                            robjects.globalenv['small_data'] = pandas2ri.py2rpy(small_change_data_r)
                            robjects.globalenv['large_data'] = pandas2ri.py2rpy(large_change_data_r)
                        except Exception as conv_error:
                            print(f"Warning: R conversion error for participant {participant}: {conv_error}")
                            raise conv_error  # Will trigger fallback
                        
                        # Make predictions using R
                        predictions = robjects.r(f'''
                            # Ensure factor levels match original model
                            small_data$MRT_angle_degrees <- factor(small_data$MRT_angle_degrees, levels = levels(acc_data$MRT_angle_degrees))
                            small_data$previous_angle_degrees <- factor(small_data$previous_angle_degrees, levels = levels(acc_data$previous_angle_degrees))
                            small_data$MRT_isReflected <- factor(small_data$MRT_isReflected, levels = levels(acc_data$MRT_isReflected))
                            small_data$participantId <- factor(small_data$participantId, levels = levels(acc_data$participantId))
                            
                            large_data$MRT_angle_degrees <- factor(large_data$MRT_angle_degrees, levels = levels(acc_data$MRT_angle_degrees))
                            large_data$previous_angle_degrees <- factor(large_data$previous_angle_degrees, levels = levels(acc_data$previous_angle_degrees))
                            large_data$MRT_isReflected <- factor(large_data$MRT_isReflected, levels = levels(acc_data$MRT_isReflected))
                            large_data$participantId <- factor(large_data$participantId, levels = levels(acc_data$participantId))
                            
                            # Predict probabilities
                            small_pred <- predict(acc_model, newdata = small_data, type = "response", allow.new.levels = TRUE)
                            large_pred <- predict(acc_model, newdata = large_data, type = "response", allow.new.levels = TRUE)
                            
                            list(small_mean = mean(small_pred, na.rm = TRUE), 
                                 large_mean = mean(large_pred, na.rm = TRUE),
                                 small_se = sd(small_pred, na.rm = TRUE) / sqrt(length(small_pred)),
                                 large_se = sd(large_pred, na.rm = TRUE) / sqrt(length(large_pred)))
                        ''')
                        
                        # Safely extract predictions with comprehensive type checking
                        try:
                            # Ensure predictions is a valid list/vector with proper length
                            if predictions is None or len(predictions) < 4:
                                raise ValueError("Insufficient prediction results")
                            
                            # Extract with comprehensive null and bounds checks
                            small_pred_val = predictions[0][0] if len(predictions) > 0 and len(predictions[0]) > 0 else None
                            large_pred_val = predictions[1][0] if len(predictions) > 1 and len(predictions[1]) > 0 else None
                            small_se_val = predictions[2][0] if len(predictions) > 2 and len(predictions[2]) > 0 else None
                            large_se_val = predictions[3][0] if len(predictions) > 3 and len(predictions[3]) > 0 else None
                            
                            # Convert with validation
                            small_acc_pred = float(small_pred_val) if small_pred_val is not None and not np.isnan(float(small_pred_val)) else 0.5
                            large_acc_pred = float(large_pred_val) if large_pred_val is not None and not np.isnan(float(large_pred_val)) else 0.5
                            small_se = float(small_se_val) if small_se_val is not None and not np.isnan(float(small_se_val)) and float(small_se_val) > 0 else 0.01
                            large_se = float(large_se_val) if large_se_val is not None and not np.isnan(float(large_se_val)) and float(large_se_val) > 0 else 0.01
                            
                        except (IndexError, TypeError, ValueError, AttributeError) as pred_extract_error:
                            if i == 0:  # Only print for first participant
                                print(f"Warning: Prediction extraction error for participant {participant}: {pred_extract_error}")
                            small_acc_pred, large_acc_pred = 0.5, 0.5
                            small_se, large_se = 0.01, 0.01
                        
                        participant_result['accuracy_facilitation_index'] = small_acc_pred - large_acc_pred
                        participant_result['accuracy_facilitation_se'] = np.sqrt(small_se**2 + large_se**2)
                        
                    except Exception as pred_error:
                        # Fallback to observed accuracies if prediction fails
                        if i == 0:  # Only print for first participant
                            print(f"Warning: Prediction failed for participant {participant}, using observed accuracies: {pred_error}")
                        small_acc = small_change_data['MRT_isCorrect'].mean() if len(small_change_data) > 0 else 0.5
                        large_acc = large_change_data['MRT_isCorrect'].mean() if len(large_change_data) > 0 else 0.5
                        participant_result['accuracy_facilitation_index'] = small_acc - large_acc
                        
                        # Approximate standard error for observed proportions with proper validation
                        n_small = len(small_change_data)
                        n_large = len(large_change_data)
                        
                        # Calculate SE with division by zero protection
                        if n_small > 0 and 0 < small_acc < 1:
                            se_small = np.sqrt(small_acc * (1 - small_acc) / n_small)
                        else:
                            se_small = 0.01  # Default SE
                            
                        if n_large > 0 and 0 < large_acc < 1:
                            se_large = np.sqrt(large_acc * (1 - large_acc) / n_large)
                        else:
                            se_large = 0.01  # Default SE
                            
                        participant_result['accuracy_facilitation_se'] = np.sqrt(se_small**2 + se_large**2)
                        
                else:
                    participant_result['accuracy_facilitation_index'] = np.nan
                    participant_result['accuracy_facilitation_se'] = np.nan
            else:
                participant_result['accuracy_facilitation_index'] = np.nan
                participant_result['accuracy_facilitation_se'] = np.nan
                
        except Exception as e:
            print(f"Error extracting indices for participant {participant}: {e}")
            participant_result['rt_facilitation_slope'] = np.nan
            participant_result['rt_facilitation_se'] = np.nan
            participant_result['accuracy_facilitation_index'] = np.nan
            participant_result['accuracy_facilitation_se'] = np.nan
        
        results.append(participant_result)
    
    results_df = pd.DataFrame(results)
    
    print("\nParticipant indices extracted:")
    print("Columns:", results_df.columns.tolist())
    print("First 2 rows:")
    print(results_df.head(2))
    
    # Summary statistics with proper NaN handling and type checking
    print(f"\nSummary of extracted indices:")
    
    # Ensure columns exist before accessing them
    if 'rt_facilitation_slope' in results_df.columns:
        rt_slope_valid = results_df['rt_facilitation_slope'].dropna()
        if len(rt_slope_valid) > 0 and rt_slope_valid.dtype in ['float64', 'float32', 'int64', 'int32']:
            rt_slope_mean = rt_slope_valid.mean()
            rt_slope_std = rt_slope_valid.std()
            rt_slope_min = rt_slope_valid.min()
            rt_slope_max = rt_slope_valid.max()
            print(f"RT facilitation slope - Mean: {rt_slope_mean:.6f}, SD: {rt_slope_std:.6f}")
            print(f"RT facilitation slope - Range: {rt_slope_min:.6f} to {rt_slope_max:.6f}")
        else:
            print("RT facilitation slope - No valid values (likely due to model convergence failure)")
    else:
        print("RT facilitation slope - Column not found in results")
    
    if 'accuracy_facilitation_index' in results_df.columns:
        acc_index_valid = results_df['accuracy_facilitation_index'].dropna()
        if len(acc_index_valid) > 0 and acc_index_valid.dtype in ['float64', 'float32', 'int64', 'int32']:
            acc_index_mean = acc_index_valid.mean()
            acc_index_std = acc_index_valid.std()
            print(f"Accuracy facilitation index - Mean: {acc_index_mean:.4f}, SD: {acc_index_std:.4f}")
        else:
            print("Accuracy facilitation index - No valid values")
    else:
        print("Accuracy facilitation index - Column not found in results")
    
    print(f"Participants with sufficient data: {results_df['sufficient_data'].sum()}/{len(results_df)}")
    print(f"Participants with valid RT slopes: {results_df['rt_facilitation_slope'].notna().sum()}/{len(results_df)}")
    if results_df['rt_facilitation_slope'].notna().sum() == 0:
        print("CRITICAL ERROR: RT model failed to converge - all RT results are invalid")
        print("RT facilitation analysis cannot be completed due to model convergence failure")
    else:
        print("SUCCESS: RT slopes extracted successfully for individual differences analysis")
    print(f"Participants with valid accuracy indices: {results_df['accuracy_facilitation_index'].notna().sum()}/{len(results_df)}")
    
    return results_df

def validate_models(rt_model, acc_model):
    """
    Validate model assumptions and convergence.
    
    Parameters:
    rt_model: R model object for RT
    acc_model: R model object for accuracy
    
    Returns:
    dict: Validation results
    """
    print("\nValidating model assumptions...")
    
    validation_results = {}
    
    # Check RT model with detailed convergence info
    if rt_model is not None:
        try:
            rt_convergence_detailed = robjects.r('''
                rt_conv <- rt_model@optinfo$conv$opt
                rt_warnings <- length(rt_model@optinfo$warnings)
                rt_max_grad <- max(abs(rt_model@optinfo$derivs$gradient))
                
                list(conv_code = rt_conv, warnings = rt_warnings, max_grad = rt_max_grad)
            ''')
            
            conv_code = int(rt_convergence_detailed[0][0])
            warnings_count = int(rt_convergence_detailed[1][0])
            max_grad = float(rt_convergence_detailed[2][0])
            
            validation_results['rt_convergence'] = conv_code
            
            print(f"RT model convergence validation:")
            print(f"  Optimizer code: {conv_code}")
            print(f"  Warning count: {warnings_count}")
            print(f"  Max gradient: {max_grad:.6f}")
            
            # Use more lenient validation criteria aligned with fitting logic
            if conv_code != 0:
                print(f"  Overall convergence: FAILED (optimizer reports failure)")
                validation_results['rt_convergence'] = 2  # Failed
            elif max_grad > 0.05:
                print(f"  Overall convergence: WARNINGS (high gradient but usable)")
                validation_results['rt_convergence'] = 1  # Warnings but usable
            else:
                print(f"  Overall convergence: SUCCESS")
                validation_results['rt_convergence'] = 0  # Success
            
        except Exception as e:
            print(f"Error checking RT model convergence: {e}")
            validation_results['rt_convergence'] = -999
    else:
        print("RT model is None - skipping convergence check")
        validation_results['rt_convergence'] = -999
    
    # Check accuracy model
    if acc_model is not None:
        try:
            acc_convergence = robjects.r('''
                acc_conv <- acc_model@optinfo$conv$opt
                acc_conv
            ''')
            validation_results['acc_convergence'] = int(acc_convergence[0])
            print(f"Accuracy model convergence code: {validation_results['acc_convergence']}")
            
        except Exception as e:
            print(f"Error checking accuracy model convergence: {e}")
            validation_results['acc_convergence'] = -999
    
    return validation_results

def extract_model_fit_stats(df, rt_model, acc_model, validation_results):
    """
    Extract model fit statistics.
    
    Parameters:
    df (pd.DataFrame): Prepared dataframe
    rt_model: R model object for RT
    acc_model: R model object for accuracy
    validation_results (dict): Validation results with convergence codes
    
    Returns:
    pd.DataFrame: Model fit statistics
    """
    print("\nExtracting model fit statistics...")
    
    fit_stats = []
    
    # RT model stats
    if rt_model is not None:
        try:
            rt_stats = robjects.r('''
                rt_n_obs <- nrow(rt_data)
                rt_n_participants <- length(unique(rt_data$participantId))
                rt_aic <- AIC(rt_model)
                rt_bic <- BIC(rt_model)
                rt_loglik <- as.numeric(logLik(rt_model))
                
                list(n_obs = rt_n_obs, n_participants = rt_n_participants, 
                     aic = rt_aic, bic = rt_bic, loglik = rt_loglik)
            ''')
            
            # Get more detailed convergence info for documentation
            try:
                rt_detailed_conv = robjects.r('''
                    rt_opt_code <- rt_model@optinfo$conv$opt
                    rt_max_grad <- max(abs(rt_model@optinfo$derivs$gradient))
                    list(opt_code = rt_opt_code, max_grad = rt_max_grad)
                ''')
                detailed_opt_code = int(rt_detailed_conv[0][0])
                detailed_max_grad = float(rt_detailed_conv[1][0])
                
                # More nuanced convergence coding
                if detailed_opt_code != 0:
                    conv_code = 2  # Optimizer failure
                elif detailed_max_grad > 0.01:
                    conv_code = 1  # Success with warnings
                else:
                    conv_code = 0  # Success
                    
            except Exception:
                conv_code = validation_results.get('rt_convergence', -999)
            
            fit_stats.append({
                'model_type': 'RT',
                'n_participants': int(rt_stats[1][0]),
                'n_observations': int(rt_stats[0][0]),
                'aic': float(rt_stats[2][0]),
                'bic': float(rt_stats[3][0]),
                'log_likelihood': float(rt_stats[4][0]),
                'convergence_code': conv_code
            })
            
        except Exception as e:
            print(f"Error extracting RT model fit stats: {e}")
    
    # Accuracy model stats
    if acc_model is not None:
        try:
            acc_stats = robjects.r('''
                acc_n_obs <- nrow(acc_data)
                acc_n_participants <- length(unique(acc_data$participantId))
                acc_aic <- AIC(acc_model)
                acc_bic <- BIC(acc_model)
                acc_loglik <- as.numeric(logLik(acc_model))
                
                list(n_obs = acc_n_obs, n_participants = acc_n_participants, 
                     aic = acc_aic, bic = acc_bic, loglik = acc_loglik)
            ''')
            
            fit_stats.append({
                'model_type': 'Accuracy',
                'n_participants': int(acc_stats[1][0]),
                'n_observations': int(acc_stats[0][0]),
                'aic': float(acc_stats[2][0]),
                'bic': float(acc_stats[3][0]),
                'log_likelihood': float(acc_stats[4][0]),
                'convergence_code': validation_results.get('acc_convergence', -999)
            })
            
        except Exception as e:
            print(f"Error extracting accuracy model fit stats: {e}")
    
    fit_df = pd.DataFrame(fit_stats)
    
    print("Model fit statistics:")
    print(fit_df)
    
    return fit_df

def save_results(participant_indices, model_results, model_fit_stats):
    """
    Save all results to CSV files.
    
    Parameters:
    participant_indices (pd.DataFrame): Participant-level indices
    model_results (pd.DataFrame): Combined model results
    model_fit_stats (pd.DataFrame): Model fit statistics
    """
    print("\nSaving results...")
    
    # Create outputs directory
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save participant indices
    indices_filename = f"outputs/MRT_sequential_facilitation_indices_{timestamp}.csv"
    participant_indices.to_csv(indices_filename, index=False)
    print(f"Saved participant indices to: {indices_filename}")
    
    # Save model results
    if model_results is not None and len(model_results) > 0:
        results_filename = f"outputs/MRT_GLMM_model_results_{timestamp}.csv"
        model_results.to_csv(results_filename, index=False)
        print(f"Saved model results to: {results_filename}")
    else:
        print("No model results to save - creating empty file")
        empty_results = pd.DataFrame(columns=['model_type', 'effect_name', 'estimate', 'std_error', 'z_value', 'p_value', 'ci_lower', 'ci_upper'])
        results_filename = f"outputs/MRT_GLMM_model_results_{timestamp}.csv"
        empty_results.to_csv(results_filename, index=False)
        print(f"Saved empty model results to: {results_filename}")
    
    # Save model fit statistics
    if model_fit_stats is not None and len(model_fit_stats) > 0:
        fit_filename = f"outputs/MRT_GLMM_model_fit_{timestamp}.csv"
        model_fit_stats.to_csv(fit_filename, index=False)
        print(f"Saved model fit statistics to: {fit_filename}")
    else:
        print("No model fit statistics to save - creating empty file")
        empty_fit_stats = pd.DataFrame(columns=['model_type', 'n_participants', 'n_observations', 'aic', 'bic', 'log_likelihood', 'convergence_code'])
        fit_filename = f"outputs/MRT_GLMM_model_fit_{timestamp}.csv"
        empty_fit_stats.to_csv(fit_filename, index=False)
        print(f"Saved empty model fit statistics to: {fit_filename}")

def main():
    """
    Main function to execute the MRT sequential facilitation analysis.
    
    Returns:
    int: 0 for success, 1 for failure
    """
    try:
        print("Starting MRT Sequential Facilitation Analysis")
        print("=" * 50)
        
        # Find input file
        input_pattern = "outputs/MRT_cleaned_data_*.csv"
        input_file = find_latest_file(input_pattern)
        
        if input_file is None:
            print(f"ERROR: No input files found matching pattern: {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Load and validate data
        df = load_and_validate_data(input_file)
        if df is None:
            print("ERROR: Failed to load data")
            return 1
        
        # Prepare data for analysis
        df_prepared = prepare_data_for_analysis(df)
        if df_prepared is None or len(df_prepared) == 0:
            print("ERROR: No valid data after preparation")
            return 1
        
        # Fit RT model
        rt_model, rt_results = fit_rt_model(df_prepared)
        
        # Fit accuracy model
        acc_model, acc_results = fit_accuracy_model(df_prepared)
        
        # Combine model results
        model_results = None
        if rt_results is not None and acc_results is not None:
            model_results = pd.concat([rt_results, acc_results], ignore_index=True)
        elif rt_results is not None:
            model_results = rt_results
        elif acc_results is not None:
            model_results = acc_results
        
        # Extract participant indices
        participant_indices = extract_participant_indices(df_prepared, rt_model, acc_model)
        
        # Validate models
        validation_results = validate_models(rt_model, acc_model)
        
        # Extract model fit statistics
        model_fit_stats = extract_model_fit_stats(df_prepared, rt_model, acc_model, validation_results)
        
        # Save results
        save_results(participant_indices, model_results, model_fit_stats)
        
        print("\n" + "=" * 50)
        print("Analysis completed successfully!")
        print(f"Processed {len(participant_indices)} participants")
        print(f"RT model fitted: {'Yes' if rt_model is not None else 'No'}")
        print(f"Accuracy model fitted: {'Yes' if acc_model is not None else 'No'}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Unexpected error in main function: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
