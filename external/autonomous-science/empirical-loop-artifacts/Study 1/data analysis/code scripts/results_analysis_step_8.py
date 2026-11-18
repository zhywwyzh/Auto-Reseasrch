#!/usr/bin/env python3
"""
H2 Mixed Effects Analysis with VVIQ2 Interactions
Analyzes VWM and MRT data with VVIQ2 interactions using mixed-effects models.
"""

import os
import sys
import pandas as pd
import numpy as np
import glob
from datetime import datetime
import warnings
import scipy.stats as scipy_stats
warnings.filterwarnings('ignore')

# Import R interface
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri, numpy2ri
    from rpy2.robjects.packages import importr
    pandas2ri.activate()
    numpy2ri.activate()
    
    # Import R packages
    base = importr('base')
    stats = importr('stats')
    lme4 = importr('lme4')
    lmerTest = importr('lmerTest')
    
    print("Successfully imported R packages")
except ImportError as e:
    print(f"Error importing R packages: {e}")
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
    
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def load_and_validate_data():
    """
    Load and validate all required input datasets.
    
    Returns:
    tuple: (vwm_df, mrt_df, vviq2_df) DataFrames or (None, None, None) if error
    """
    print("Loading input datasets...")
    
    # Find latest files
    vwm_pattern = "outputs/VWM_cleaned_data_*.csv"
    mrt_pattern = "outputs/MRT_cleaned_data_*.csv"
    vviq2_pattern = "outputs/VVIQ2_cleaned_data_*.csv"
    
    vwm_file = find_latest_file(vwm_pattern)
    mrt_file = find_latest_file(mrt_pattern)
    vviq2_file = find_latest_file(vviq2_pattern)
    
    if not vwm_file:
        print(f"No VWM file found matching pattern: {vwm_pattern}")
        return None, None, None
    if not mrt_file:
        print(f"No MRT file found matching pattern: {mrt_pattern}")
        return None, None, None
    if not vviq2_file:
        print(f"No VVIQ2 file found matching pattern: {vviq2_pattern}")
        return None, None, None
    
    print(f"Found VWM file: {vwm_file}")
    print(f"Found MRT file: {mrt_file}")
    print(f"Found VVIQ2 file: {vviq2_file}")
    
    # Load datasets
    try:
        vwm_df = pd.read_csv(vwm_file)
        print(f"VWM dataset loaded: {vwm_df.shape}")
        print("VWM columns:", list(vwm_df.columns))
        print("VWM first 3 rows:")
        print(vwm_df.head(3))
        
        mrt_df = pd.read_csv(mrt_file)
        print(f"MRT dataset loaded: {mrt_df.shape}")
        print("MRT columns:", list(mrt_df.columns))
        print("MRT first 3 rows:")
        print(mrt_df.head(3))
        
        vviq2_df = pd.read_csv(vviq2_file)
        print(f"VVIQ2 dataset loaded: {vviq2_df.shape}")
        print("VVIQ2 columns:", list(vviq2_df.columns))
        print("VVIQ2 first 3 rows:")
        print(vviq2_df.head(3))
        
    except Exception as e:
        print(f"Error loading datasets: {e}")
        return None, None, None
    
    # Validate required columns
    vwm_required = ['participantId', 'VWM_setSize', 'VWM_delay_s', 'VWM_error_absolute_degrees', 
                    'excluded_participant', 'valid_trial', 'isPractice']
    mrt_required = ['participantId', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms',
                    'excluded_participant', 'valid_trial', 'isPractice']
    vviq2_required = ['participantId', 'total_score', 'excluded_participant']
    
    missing_vwm = [col for col in vwm_required if col not in vwm_df.columns]
    missing_mrt = [col for col in mrt_required if col not in mrt_df.columns]
    missing_vviq2 = [col for col in vviq2_required if col not in vviq2_df.columns]
    
    if missing_vwm:
        print(f"Missing VWM columns: {missing_vwm}")
        return None, None, None
    if missing_mrt:
        print(f"Missing MRT columns: {missing_mrt}")
        return None, None, None
    if missing_vviq2:
        print(f"Missing VVIQ2 columns: {missing_vviq2}")
        return None, None, None
    
    print("All required columns present in datasets")
    
    # Print unique values for key experimental design parameters
    print("\nVWM experimental design parameters:")
    print(f"VWM_setSize unique values: {sorted(vwm_df['VWM_setSize'].dropna().unique())}")
    print(f"VWM_delay_s unique values: {sorted(vwm_df['VWM_delay_s'].dropna().unique())}")
    print(f"VWM excluded_participant unique values: {sorted(vwm_df['excluded_participant'].dropna().unique())}")
    print(f"VWM valid_trial unique values: {sorted(vwm_df['valid_trial'].dropna().unique())}")
    print(f"VWM isPractice unique values: {sorted(vwm_df['isPractice'].dropna().unique())}")
    
    print("\nMRT experimental design parameters:")
    print(f"MRT_angle_degrees unique values: {sorted(mrt_df['MRT_angle_degrees'].dropna().unique())}")
    print(f"MRT_isCorrect unique values: {sorted(mrt_df['MRT_isCorrect'].dropna().unique())}")
    print(f"MRT excluded_participant unique values: {sorted(mrt_df['excluded_participant'].dropna().unique())}")
    print(f"MRT valid_trial unique values: {sorted(mrt_df['valid_trial'].dropna().unique())}")
    print(f"MRT isPractice unique values: {sorted(mrt_df['isPractice'].dropna().unique())}")
    
    print("\nVVIQ2 parameters:")
    print(f"VVIQ2 excluded_participant unique values: {sorted(vviq2_df['excluded_participant'].dropna().unique())}")
    print(f"VVIQ2 total_score type: {type(vviq2_df['total_score'].iloc[0])}")
    
    return vwm_df, mrt_df, vviq2_df

def merge_and_prepare_data(vwm_df, mrt_df, vviq2_df):
    """
    Merge datasets and prepare VVIQ2 scores.
    
    Parameters:
    vwm_df (DataFrame): VWM dataset
    mrt_df (DataFrame): MRT dataset  
    vviq2_df (DataFrame): VVIQ2 dataset
    
    Returns:
    tuple: (merged_vwm, merged_mrt, vviq2_scores) or (None, None, None) if error
    """
    print("\nMerging datasets and preparing VVIQ2 scores...")
    
    # Filter out excluded participants from each dataset
    print("Filtering excluded participants...")
    vwm_included = vwm_df[vwm_df['excluded_participant'] == False].copy()
    mrt_included = mrt_df[mrt_df['excluded_participant'] == False].copy()
    vviq2_included = vviq2_df[vviq2_df['excluded_participant'] == False].copy()
    
    print(f"VWM after exclusions: {vwm_included.shape[0]} rows")
    print(f"MRT after exclusions: {mrt_included.shape[0]} rows")
    print(f"VVIQ2 after exclusions: {vviq2_included.shape[0]} rows")
    
    # Get participants present in all datasets
    vwm_participants = set(vwm_included['participantId'].unique())
    mrt_participants = set(mrt_included['participantId'].unique())
    vviq2_participants = set(vviq2_included['participantId'].unique())
    
    common_participants = vwm_participants & mrt_participants & vviq2_participants
    print(f"Participants in all datasets: {len(common_participants)}")
    
    if len(common_participants) == 0:
        print("No common participants found across all datasets")
        return None, None, None
    
    # Filter datasets to common participants
    vwm_common = vwm_included[vwm_included['participantId'].isin(common_participants)].copy()
    mrt_common = mrt_included[mrt_included['participantId'].isin(common_participants)].copy()
    vviq2_common = vviq2_included[vviq2_included['participantId'].isin(common_participants)].copy()
    
    print(f"VWM common participants: {vwm_common.shape[0]} rows")
    print(f"MRT common participants: {mrt_common.shape[0]} rows") 
    print(f"VVIQ2 common participants: {vviq2_common.shape[0]} rows")
    
    # Prepare VVIQ2 scores - mean center
    vviq2_scores = vviq2_common[['participantId', 'total_score']].copy()
    
    # Remove any null values in total_score
    vviq2_scores = vviq2_scores.dropna(subset=['total_score'])
    print(f"VVIQ2 scores after removing nulls: {vviq2_scores.shape[0]} rows")
    
    # Mean center VVIQ2 scores
    mean_vviq2 = vviq2_scores['total_score'].mean()
    vviq2_scores['vviq2_centered'] = vviq2_scores['total_score'] - mean_vviq2
    
    print(f"VVIQ2 mean: {mean_vviq2:.3f}")
    print(f"VVIQ2 SD: {vviq2_scores['total_score'].std():.3f}")
    print(f"VVIQ2 centered mean: {vviq2_scores['vviq2_centered'].mean():.6f}")
    
    print("VVIQ2 scores prepared:")
    print("Columns:", list(vviq2_scores.columns))
    print("First 2 rows:")
    print(vviq2_scores.head(2))
    
    # Merge VVIQ2 scores with VWM and MRT data
    merged_vwm = vwm_common.merge(vviq2_scores[['participantId', 'vviq2_centered']], 
                                  on='participantId', how='inner')
    merged_mrt = mrt_common.merge(vviq2_scores[['participantId', 'vviq2_centered']], 
                                  on='participantId', how='inner')
    
    print(f"Merged VWM: {merged_vwm.shape[0]} rows")
    print(f"Merged MRT: {merged_mrt.shape[0]} rows")
    
    print("Merged VWM columns:", list(merged_vwm.columns))
    print("Merged VWM first 2 rows:")
    print(merged_vwm.head(2))
    
    print("Merged MRT columns:", list(merged_mrt.columns))
    print("Merged MRT first 2 rows:")
    print(merged_mrt.head(2))
    
    return merged_vwm, merged_mrt, vviq2_scores

def fit_vwm_model(merged_vwm):
    """
    Fit VWM mixed-effects model with VVIQ2 interactions.
    
    Parameters:
    merged_vwm (DataFrame): Merged VWM dataset with VVIQ2 scores
    
    Returns:
    dict: Model results or None if error
    """
    print("\nFitting VWM mixed-effects model...")
    
    # Filter data
    vwm_data = merged_vwm[
        (merged_vwm['isPractice'] == False) & 
        (merged_vwm['valid_trial'] == True)
    ].copy()
    
    # Remove null values
    original_rows = vwm_data.shape[0]
    vwm_data = vwm_data.dropna(subset=['VWM_error_absolute_degrees', 'VWM_setSize', 
                                       'VWM_delay_s', 'vviq2_centered'])
    dropped_rows = original_rows - vwm_data.shape[0]
    
    print(f"VWM data after removing null values: {vwm_data.shape[0]} rows (dropped {dropped_rows} rows with null values)")
    
    # Filter for specific set sizes and delays as per instructions
    print(f"VWM data before specific level filtering: {vwm_data.shape[0]} rows")
    vwm_data = vwm_data[
        (vwm_data['VWM_setSize'].isin([2, 4])) &
        (vwm_data['VWM_delay_s'].isin([1.0, 4.0]))
    ].copy()
    print(f"VWM analysis data after filtering for setSize 2,4 and delay 1.0,4.0: {vwm_data.shape[0]} rows")
    print(f"VWM participants: {vwm_data['participantId'].nunique()}")
    
    if vwm_data.shape[0] == 0:
        print("No valid VWM data for analysis")
        return None
    
    # Convert to factors
    vwm_data['VWM_setSize_factor'] = vwm_data['VWM_setSize'].astype(str)
    vwm_data['VWM_delay_factor'] = vwm_data['VWM_delay_s'].astype(str)
    
    print(f"VWM setSize factor levels after filtering: {sorted(vwm_data['VWM_setSize_factor'].unique())}")
    print(f"VWM delay factor levels after filtering: {sorted(vwm_data['VWM_delay_factor'].unique())}")
    print(f"VWM setSize factor counts: {vwm_data['VWM_setSize_factor'].value_counts().to_dict()}")
    print(f"VWM delay factor counts: {vwm_data['VWM_delay_factor'].value_counts().to_dict()}")
    print(f"VVIQ2 centered mean: {vwm_data['vviq2_centered'].mean():.6f}, SD: {vwm_data['vviq2_centered'].std():.6f}")
    print(f"VWM 2x2 design verification - Expected 4 conditions, found: {len(vwm_data.groupby(['VWM_setSize_factor', 'VWM_delay_factor']))}")
    
    # Transfer data to R
    robjects.globalenv['vwm_data'] = vwm_data
    
    # Progressive model fitting with explicit contrasts
    model_formulas = [
        "VWM_error_absolute_degrees ~ VWM_setSize_factor * VWM_delay_factor * vviq2_centered + (1 + VWM_setSize_factor * VWM_delay_factor | participantId)",
        "VWM_error_absolute_degrees ~ VWM_setSize_factor * VWM_delay_factor * vviq2_centered + (1 + VWM_setSize_factor + VWM_delay_factor | participantId)",
        "VWM_error_absolute_degrees ~ VWM_setSize_factor * VWM_delay_factor * vviq2_centered + (1 | participantId)"
    ]
    
    model_fitted = False
    
    # Set up factors with explicit reference levels
    robjects.r('''
    vwm_data$VWM_setSize_factor <- relevel(as.factor(vwm_data$VWM_setSize_factor), ref = "2")
    vwm_data$VWM_delay_factor <- relevel(as.factor(vwm_data$VWM_delay_factor), ref = "1.0")
    vwm_data$participantId <- as.factor(vwm_data$participantId)
    is_linear_model <- FALSE

    # Verify factor levels and reference levels
    cat("VWM setSize factor levels:", levels(vwm_data$VWM_setSize_factor), "\\n")
    cat("VWM delay factor levels:", levels(vwm_data$VWM_delay_factor), "\\n")
    cat("VWM setSize reference level:", levels(vwm_data$VWM_setSize_factor)[1], "\\n")
    cat("VWM delay reference level:", levels(vwm_data$VWM_delay_factor)[1], "\\n")

    # Verify 2x2 design structure
    design_table <- table(vwm_data$VWM_setSize_factor, vwm_data$VWM_delay_factor)
    cat("VWM 2x2 design structure:\\n")
    print(design_table)
    ''')
    
    # Try each model formula progressively
    for i, formula in enumerate(model_formulas):
        try:
            print(f"Attempting VWM model {i+1}/3: {formula}")
            robjects.globalenv['vwm_formula'] = formula
            
            robjects.r('''
            vwm_model <- lmer(as.formula(vwm_formula), 
                             data = vwm_data, REML = TRUE,
                             control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 200000)))
            
            # Check for convergence warnings
            vwm_summary <- summary(vwm_model)
            warnings <- capture.output(vwm_summary)
            has_warnings <- any(grepl("singular|negative eigenvalue|convergence", warnings))
            
            # Print specific warnings if any
            if (has_warnings) {
                warning_lines <- warnings[grepl("singular|negative eigenvalue|convergence", warnings)]
                cat("VWM model convergence warnings:\\n")
                cat(paste(warning_lines, collapse="\\n"), "\\n")
            }
            ''')
            
            has_warnings = bool(robjects.r('has_warnings')[0])
            if not has_warnings:
                print(f"VWM model {i+1} fitted successfully without warnings")
                model_fitted = True
                break
            else:
                print(f"VWM model {i+1} has convergence warnings, trying next model...")
                
        except Exception as e:
            print(f"VWM model {i+1} failed: {e}")
            continue
    
    # If all mixed-effects models failed, try linear model
    if not model_fitted:
        print("All mixed-effects models failed, falling back to linear model...")
        try:
            robjects.r('''
            vwm_model <- lm(VWM_error_absolute_degrees ~ VWM_setSize_factor * VWM_delay_factor * vviq2_centered, 
                           data = vwm_data)
            is_linear_model <- TRUE
            ''')
            print("Linear model fitted successfully as fallback")
            model_fitted = True
            
        except Exception as e:
            print(f"Linear model also failed: {e}")
            return None
    
    # Check for convergence issues and model type
    robjects.r('''
    # Check for convergence warnings
    vwm_summary <- summary(vwm_model)
    warnings <- capture.output(vwm_summary)
    has_warnings <- any(grepl("singular|negative eigenvalue|convergence", warnings))
    
    # Print the actual warnings for debugging
    if (any(grepl("singular|negative eigenvalue|convergence", warnings))) {
        warning_lines <- warnings[grepl("singular|negative eigenvalue|convergence", warnings)]
        cat("VWM model convergence warnings detected:\\n")
        cat(paste(warning_lines, collapse="\\n"), "\\n")
    }
    
    # Store model type for later use
    is_linear_model <- inherits(vwm_model, "lm") && !inherits(vwm_model, "merMod")
    
    # Print model type and coefficient structure for debugging
    cat("Model type: ", ifelse(is_linear_model, "Linear model", "Mixed-effects model"), "\\n")
    cat("Number of coefficients: ", nrow(vwm_summary$coefficients), "\\n")
    cat("Coefficient column names: ", paste(colnames(vwm_summary$coefficients), collapse=", "), "\\n")
    ''')
    
    try:
        has_warnings = bool(robjects.r('has_warnings')[0])
        if has_warnings:
            print("WARNING: VWM model has convergence issues. Attempting to fit a simpler model...")
            
            # Try a simplified mixed-effects model
            robjects.r('''
            # Try with minimal random effects structure
            vwm_model <- lmer(VWM_error_absolute_degrees ~ VWM_setSize_factor * VWM_delay_factor * vviq2_centered + 
                             (1 | participantId), 
                             data = vwm_data, REML = TRUE,
                             control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 200000)))
            
            # Check if this improved convergence
            vwm_summary <- summary(vwm_model)
            warnings <- capture.output(vwm_summary)
            has_warnings <- any(grepl("singular|negative eigenvalue|convergence", warnings))
            
            # Store model type for later use
            is_linear_model <- inherits(vwm_model, "lm") && !inherits(vwm_model, "merMod")
            ''')
            
            has_warnings = bool(robjects.r('has_warnings')[0])
            if has_warnings:
                print("WARNING: VWM model still has convergence issues with simplified model.")
                print("Falling back to linear model without random effects...")
                
                # Use a linear model as final fallback
                robjects.r('''
                # Use a linear model without random effects as fallback
                vwm_model <- lm(VWM_error_absolute_degrees ~ VWM_setSize_factor * VWM_delay_factor * vviq2_centered, 
                               data = vwm_data)
                
                # Get model summary
                vwm_summary <- summary(vwm_model)
                
                # Store model type for later use
                is_linear_model <- TRUE
                
                cat("NOTICE: Using linear model without random effects\\n")
                ''')
                
                print("NOTICE: Using linear model without random effects")
                print("CAUTION: Results do not account for within-subject correlations")
            else:
                print("SUCCESS: VWM model convergence achieved with simplified model.")
        else:
            print("VWM model converged successfully without issues.")
            
        # Get model type
        is_linear_model = bool(robjects.r('is_linear_model')[0])
        print(f"VWM model type: {'Linear model' if is_linear_model else 'Mixed-effects model'}")
        
    except Exception as e:
        print(f"Note: Could not check for convergence warnings ({e}), continuing anyway.")
        is_linear_model = False
    
    # Extract results
    try:
        robjects.r('vwm_summary <- summary(vwm_model)')
        vwm_coef = robjects.r('vwm_summary$coefficients')
        
        # Print coefficient dimensions for debugging
        print(f"VWM coefficients dimensions: {robjects.r('dim(vwm_summary$coefficients)')}")
        
        # Handle different rpy2 versions with better error handling
        try:
            vwm_coef_df = pandas2ri.ri2py(vwm_coef)
            print(f"Successfully converted coefficients using ri2py: shape {np.array(vwm_coef_df).shape}")
        except Exception as e1:
            print(f"ri2py conversion failed: {e1}")
            try:
                vwm_coef_df = pandas2ri.rpy2py(vwm_coef)
                print(f"Successfully converted coefficients using rpy2py: shape {np.array(vwm_coef_df).shape}")
            except Exception as e2:
                print(f"rpy2py conversion failed: {e2}")
                try:
                    vwm_coef_df = np.array(vwm_coef)
                    print(f"Converted coefficients to numpy array: shape {vwm_coef_df.shape}")
                except Exception as e3:
                    print(f"Numpy conversion failed: {e3}")
                    # Last resort - try to extract manually
                    print("Attempting manual extraction of coefficients...")
                    robjects.r('''
                    # Extract coefficients manually as a data frame
                    vwm_coef_df <- as.data.frame(vwm_summary$coefficients)
                    ''')
                    vwm_coef_df = robjects.r('vwm_coef_df')
                    print(f"Manual extraction result: {type(vwm_coef_df)}")
        
        # Convert to DataFrame and dynamically assign columns based on model type
        vwm_results = pd.DataFrame(vwm_coef_df)
        
        # Check if we're dealing with a linear model (4 columns) or mixed-effects model (5 columns)
        if vwm_results.shape[1] == 4:  # Linear model output (no df column)
            print("Detected linear model output structure (4 columns)")
            vwm_results.columns = ['estimate', 'std_error', 't_value', 'p_value']
            vwm_results['df'] = np.nan  # Add placeholder df column for consistency
        else:  # Mixed-effects model output
            print("Detected mixed-effects model output structure (5 columns)")
            vwm_results.columns = ['estimate', 'std_error', 'df', 't_value', 'p_value']
        
        # Create meaningful effect names instead of numeric indices
        try:
            # Try to get effect names from R
            effect_names = robjects.r('rownames(vwm_summary$coefficients)')
            effect_names = [str(name) for name in effect_names]
            print(f"Successfully extracted {len(effect_names)} effect names from R")
        except Exception as e:
            print(f"Could not extract effect names from R: {e}")
            # Fallback to generic names based on model type and number of coefficients
            effect_names = []
            
            # Get the actual number of coefficients
            num_coeffs = vwm_results.shape[0]
            print(f"Number of coefficients: {num_coeffs}")
            
            # For 2x2 design, use appropriate names for 8-parameter structure
            base_names = [
                "(Intercept)", 
                "VWM_setSize_factor4",  # Assuming '2' is ref
                "VWM_delay_factor4.0", # Assuming '1.0' is ref
                "vviq2_centered",
                "VWM_setSize_factor4:VWM_delay_factor4.0",
                "VWM_setSize_factor4:vviq2_centered",
                "VWM_delay_factor4.0:vviq2_centered",
                "VWM_setSize_factor4:VWM_delay_factor4.0:vviq2_centered"
            ]
            
            # Only use as many names as we have coefficients
            if num_coeffs <= len(base_names):
                effect_names = base_names[:num_coeffs]
            else:
                # If we have more coefficients than names, use generic names
                effect_names = [f"VWM_effect_{i}" for i in range(num_coeffs)]
            
            print(f"Using fallback effect names: {effect_names}")
        
        # Assign meaningful effect names - ensure lengths match
        if len(effect_names) == vwm_results.shape[0]:
            vwm_results['effect_name'] = effect_names
            print(f"Assigned {len(effect_names)} effect names to VWM results")
        else:
            print(f"WARNING: Effect names length ({len(effect_names)}) doesn't match results shape ({vwm_results.shape[0]})")
            # Generate generic names with the correct length
            generic_names = [f"VWM_effect_{i}" for i in range(vwm_results.shape[0])]
            vwm_results['effect_name'] = generic_names
            print(f"Assigned {len(generic_names)} generic effect names to VWM results")
        
        vwm_results['model_name'] = 'VWM'
        
        # Print debug info about effect_name column
        print(f"VWM effect_name column type: {vwm_results['effect_name'].dtype}")
        print(f"VWM effect_name first few values: {vwm_results['effect_name'].head(3).tolist()}")
        print(f"VWM model fitted with {len(vwm_results)} parameters")
        
        # Calculate confidence intervals
        vwm_results['ci_lower'] = vwm_results['estimate'] - 1.96 * vwm_results['std_error']
        vwm_results['ci_upper'] = vwm_results['estimate'] + 1.96 * vwm_results['std_error']
        
        print("VWM model results:")
        print(vwm_results[['effect_name', 'estimate', 'std_error', 't_value', 'p_value']])
        
        # Print specific VVIQ2 interaction effects for verification
        vviq2_interactions = vwm_results[vwm_results['effect_name'].str.contains('vviq2_centered') & 
                                        vwm_results['effect_name'].str.contains(':')]
        if not vviq2_interactions.empty:
            print(f"VWM VVIQ2 interactions found: {len(vviq2_interactions)}")
            print("VWM VVIQ2 interaction effects:")
            print(vviq2_interactions[['effect_name', 'estimate', 'p_value']].to_string(index=False))
        else:
            print("No VWM VVIQ2 interactions found in results")
        
        return vwm_results
        
    except Exception as e:
        print(f"Error extracting VWM results: {e}")
        return None

def fit_mrt_models(merged_mrt):
    """
    Fit MRT mixed-effects models with VVIQ2 interactions.
    
    Parameters:
    merged_mrt (DataFrame): Merged MRT dataset with VVIQ2 scores
    
    Returns:
    tuple: (rt_results, accuracy_results) or (None, None) if error
    """
    print("\nFitting MRT mixed-effects models...")
    
    # Filter data
    mrt_data = merged_mrt[
        (merged_mrt['isPractice'] == False) & 
        (merged_mrt['valid_trial'] == True)
    ].copy()
    
    # Remove null values
    original_rows = mrt_data.shape[0]
    mrt_data = mrt_data.dropna(subset=['MRT_angle_degrees', 'MRT_isCorrect', 
                                       'MRT_rt_ms', 'vviq2_centered'])
    dropped_rows = original_rows - mrt_data.shape[0]
    
    print(f"MRT analysis data: {mrt_data.shape[0]} rows (dropped {dropped_rows} rows with null values)")
    print(f"MRT participants: {mrt_data['participantId'].nunique()}")
    
    if mrt_data.shape[0] == 0:
        print("No valid MRT data for analysis")
        return None, None
    
    # Log transform RT and filter correct trials for RT analysis
    mrt_data['log_rt'] = np.log(mrt_data['MRT_rt_ms'])
    mrt_rt_data = mrt_data[mrt_data['MRT_isCorrect'] == True].copy()
    
    # Scale MRT angle degrees for numerical stability
    mrt_data['MRT_angle_degrees_scaled'] = (mrt_data['MRT_angle_degrees'] - mrt_data['MRT_angle_degrees'].mean()) / mrt_data['MRT_angle_degrees'].std()
    
    # Apply same scaling to RT data
    mrt_rt_data['MRT_angle_degrees_scaled'] = (mrt_rt_data['MRT_angle_degrees'] - mrt_rt_data['MRT_angle_degrees'].mean()) / mrt_rt_data['MRT_angle_degrees'].std()
    
    print(f"MRT RT analysis data (correct trials only): {mrt_rt_data.shape[0]} rows")
    print(f"MRT angle scaled mean: {mrt_data['MRT_angle_degrees_scaled'].mean():.6f}, SD: {mrt_data['MRT_angle_degrees_scaled'].std():.6f}")
    print(f"VVIQ2 centered mean: {mrt_data['vviq2_centered'].mean():.6f}, SD: {mrt_data['vviq2_centered'].std():.6f}")
    
    # Transfer data to R
    robjects.globalenv['mrt_data'] = mrt_data
    robjects.globalenv['mrt_rt_data'] = mrt_rt_data
    
    # Fit RT model with progressive simplification
    rt_results = None
    rt_model_formulas = [
        "log_rt ~ MRT_angle_degrees_scaled * vviq2_centered + (1 + MRT_angle_degrees_scaled | participantId)",
        "log_rt ~ MRT_angle_degrees_scaled * vviq2_centered + (1 | participantId)"
    ]
    
    rt_model_fitted = False
    
    # Set up factors
    robjects.r('''
    mrt_rt_data$participantId <- as.factor(mrt_rt_data$participantId)
    is_linear_rt_model <- FALSE
    ''')
    
    # Try each RT model formula progressively
    for i, formula in enumerate(rt_model_formulas):
        try:
            print(f"Attempting MRT RT model {i+1}/2: {formula}")
            robjects.globalenv['mrt_rt_formula'] = formula
            
            robjects.r('''
            mrt_rt_model <- lmer(as.formula(mrt_rt_formula), 
                                data = mrt_rt_data, REML = FALSE)
            
            # Check for convergence warnings
            mrt_rt_summary <- summary(mrt_rt_model)
            warnings <- capture.output(mrt_rt_summary)
            has_warnings <- any(grepl("singular|negative eigenvalue|convergence", warnings))
            ''')
            
            has_warnings = bool(robjects.r('has_warnings')[0])
            if not has_warnings:
                print(f"MRT RT model {i+1} fitted successfully without warnings")
                rt_model_fitted = True
                break
            else:
                print(f"MRT RT model {i+1} has convergence warnings, trying next model...")
                
        except Exception as e:
            print(f"MRT RT model {i+1} failed: {e}")
            continue
    
    # If all mixed-effects models failed, try linear model
    if not rt_model_fitted:
        print("All RT mixed-effects models failed, falling back to linear model...")
        try:
            robjects.r('''
            mrt_rt_model <- lm(log_rt ~ MRT_angle_degrees_scaled * vviq2_centered, 
                              data = mrt_rt_data)
            is_linear_rt_model <- TRUE
            ''')
            print("RT linear model fitted successfully as fallback")
            rt_model_fitted = True
            
        except Exception as e:
            print(f"RT linear model also failed: {e}")
            return None, None
    
    # Extract RT results
    if 'mrt_rt_model' in robjects.r('ls()'):
        try:
            # Simply extract results and note any warnings
            robjects.r('mrt_rt_summary <- summary(mrt_rt_model)')
            
            # Check for warnings but don't let them stop execution
            robjects.r('''
            warnings <- capture.output(mrt_rt_summary)
            has_warnings <- any(grepl("Model failed to converge|singular|convergence", warnings))
            ''')
            
            try:
                has_warnings = bool(robjects.r('has_warnings')[0])
                if has_warnings:
                    print("WARNING: MRT RT model has convergence issues. Results should be interpreted with caution.")
                    print("Proceeding with result extraction despite convergence warnings.")
            except Exception as e:
                print(f"Note: Could not check for convergence warnings ({e}), continuing anyway.")
            
            # Extract coefficients
            mrt_rt_coef = robjects.r('mrt_rt_summary$coefficients')
            
            # Handle different rpy2 versions
            try:
                mrt_rt_coef_df = pandas2ri.ri2py(mrt_rt_coef)
            except:
                try:
                    mrt_rt_coef_df = pandas2ri.rpy2py(mrt_rt_coef)
                except:
                    mrt_rt_coef_df = np.array(mrt_rt_coef)
            
            rt_results = pd.DataFrame(mrt_rt_coef_df)
            rt_results.columns = ['estimate', 'std_error', 'df', 't_value', 'p_value']
            
            # Create meaningful effect names
            try:
                effect_names = robjects.r('rownames(mrt_rt_summary$coefficients)')
                effect_names = [str(name) for name in effect_names]
            except:
                effect_names = [
                    "Intercept", 
                    "MRT_angle_degrees_scaled", 
                    "vviq2_centered", 
                    "MRT_angle_degrees_scaled:vviq2_centered"
                ][:len(rt_results)]
            
            rt_results['effect_name'] = effect_names if len(effect_names) == len(rt_results) else [f"MRT_RT_effect_{i}" for i in range(len(rt_results))]
            rt_results['model_name'] = 'MRT_RT'
            
            print(f"MRT_RT effect_name column type: {rt_results['effect_name'].dtype}")
            print(f"MRT_RT effect_name first few values: {rt_results['effect_name'].head(3).tolist()}")
            
            rt_results['ci_lower'] = rt_results['estimate'] - 1.96 * rt_results['std_error']
            rt_results['ci_upper'] = rt_results['estimate'] + 1.96 * rt_results['std_error']
            
            print("MRT RT model results:")
            print(rt_results[['effect_name', 'estimate', 'std_error', 't_value', 'p_value']])
            
        except Exception as e:
            print(f"Error extracting RT results: {e}")
            rt_results = None
    
    # Fit accuracy model with progressive simplification
    accuracy_results = None
    acc_model_formulas = [
        "MRT_isCorrect ~ MRT_angle_degrees_scaled * vviq2_centered + (1 + MRT_angle_degrees_scaled | participantId)",
        "MRT_isCorrect ~ MRT_angle_degrees_scaled * vviq2_centered + (1 | participantId)"
    ]
    
    acc_model_fitted = False
    
    # Set up factors
    robjects.r('''
    mrt_data$participantId <- as.factor(mrt_data$participantId)
    is_linear_acc_model <- FALSE
    ''')
    
    # Try each accuracy model formula progressively
    for i, formula in enumerate(acc_model_formulas):
        try:
            print(f"Attempting MRT accuracy model {i+1}/2: {formula}")
            robjects.globalenv['mrt_acc_formula'] = formula
            
            robjects.r('''
            mrt_acc_model <- glmer(as.formula(mrt_acc_formula), 
                                  data = mrt_data, family = binomial)
            
            # Check for convergence warnings
            mrt_acc_summary <- summary(mrt_acc_model)
            warnings <- capture.output(mrt_acc_summary)
            has_warnings <- any(grepl("singular|negative eigenvalue|convergence", warnings))
            ''')
            
            has_warnings = bool(robjects.r('has_warnings')[0])
            if not has_warnings:
                print(f"MRT accuracy model {i+1} fitted successfully without warnings")
                acc_model_fitted = True
                break
            else:
                print(f"MRT accuracy model {i+1} has convergence warnings, trying next model...")
                
        except Exception as e:
            print(f"MRT accuracy model {i+1} failed: {e}")
            continue
    
    # If all mixed-effects models failed, try linear model
    if not acc_model_fitted:
        print("All accuracy mixed-effects models failed, falling back to linear model...")
        try:
            robjects.r('''
            mrt_acc_model <- glm(MRT_isCorrect ~ MRT_angle_degrees_scaled * vviq2_centered, 
                                data = mrt_data, family = binomial)
            is_linear_acc_model <- TRUE
            ''')
            print("Accuracy linear model fitted successfully as fallback")
            acc_model_fitted = True
            
        except Exception as e:
            print(f"Accuracy linear model also failed: {e}")
            return rt_results, None
    
    # Extract accuracy results
    if 'mrt_acc_model' in robjects.r('ls()'):
        try:
            # Simply extract results and note any warnings
            robjects.r('mrt_acc_summary <- summary(mrt_acc_model)')
            
            # Check for warnings but don't let them stop execution
            robjects.r('''
            warnings <- capture.output(mrt_acc_summary)
            has_warnings <- any(grepl("Model failed to converge|singular|convergence", warnings))
            ''')
            
            try:
                has_warnings = bool(robjects.r('has_warnings')[0])
                if has_warnings:
                    print("WARNING: MRT accuracy model has convergence issues. Results should be interpreted with caution.")
                    print("Proceeding with result extraction despite convergence warnings.")
            except Exception as e:
                print(f"Note: Could not check for convergence warnings ({e}), continuing anyway.")
            
            # Extract coefficients
            mrt_acc_coef = robjects.r('mrt_acc_summary$coefficients')
            
            # Handle different rpy2 versions
            try:
                mrt_acc_coef_df = pandas2ri.ri2py(mrt_acc_coef)
            except:
                try:
                    mrt_acc_coef_df = pandas2ri.rpy2py(mrt_acc_coef)
                except:
                    mrt_acc_coef_df = np.array(mrt_acc_coef)
            
            accuracy_results = pd.DataFrame(mrt_acc_coef_df)
            accuracy_results.columns = ['estimate', 'std_error', 'z_value', 'p_value']
            
            # Create meaningful effect names instead of numeric indices
            try:
                # Try to get effect names from R
                effect_names = robjects.r('rownames(mrt_acc_summary$coefficients)')
                effect_names = [str(name) for name in effect_names]
            except:
                # Fallback to generic names
                effect_names = [
                    "Intercept", 
                    "MRT_angle_degrees_scaled", 
                    "vviq2_centered", 
                    "MRT_angle_degrees_scaled:vviq2_centered"
                ][:len(accuracy_results)]
            
            # Assign meaningful effect names
            accuracy_results['effect_name'] = effect_names if len(effect_names) == len(accuracy_results) else [f"MRT_Accuracy_effect_{i}" for i in range(len(accuracy_results))]
            accuracy_results['model_name'] = 'MRT_Accuracy'
            accuracy_results['t_value'] = accuracy_results['z_value']  # For consistency
            
            # Print debug info about effect_name column
            print(f"MRT_Accuracy effect_name column type: {accuracy_results['effect_name'].dtype}")
            print(f"MRT_Accuracy effect_name first few values: {accuracy_results['effect_name'].head(3).tolist()}")
            
            accuracy_results['ci_lower'] = accuracy_results['estimate'] - 1.96 * accuracy_results['std_error']
            accuracy_results['ci_upper'] = accuracy_results['estimate'] + 1.96 * accuracy_results['std_error']
            
            print("MRT accuracy model results:")
            print(accuracy_results[['effect_name', 'estimate', 'std_error', 'z_value', 'p_value']])
            
        except Exception as e:
            print(f"Error extracting accuracy results: {e}")
    
    return rt_results, accuracy_results

def conduct_simple_slopes(vviq2_scores, model_results):
    """
    Conduct simple slopes analyses for significant interactions.
    
    Parameters:
    vviq2_scores (DataFrame): VVIQ2 scores data
    model_results (list): List of model result DataFrames
    
    Returns:
    DataFrame: Simple slopes results or None if no significant interactions
    """
    print("\nConducting simple slopes analyses...")
    
    if vviq2_scores is None or not isinstance(vviq2_scores, pd.DataFrame) or vviq2_scores.empty:
        print("Error: Invalid VVIQ2 scores data")
        return None
        
    if not model_results or all(result is None for result in model_results):
        print("Error: No valid model results for simple slopes analysis")
        return None
    
    # Validate VVIQ2 scores data
    if 'total_score' not in vviq2_scores.columns:
        print("Error: 'total_score' column not found in VVIQ2 scores")
        return None
        
    # Calculate VVIQ2 levels (±1 SD)
    vviq2_sd = vviq2_scores['total_score'].std()
    vviq2_mean = vviq2_scores['total_score'].mean()
    
    if pd.isna(vviq2_sd) or pd.isna(vviq2_mean):
        print("Error: Invalid VVIQ2 statistics (NaN values)")
        return None
    
    high_vviq2 = vviq2_sd  # +1 SD from centered mean (which is 0)
    low_vviq2 = -vviq2_sd  # -1 SD from centered mean
    
    print(f"VVIQ2 high level (+1 SD): {high_vviq2:.3f}")
    print(f"VVIQ2 low level (-1 SD): {low_vviq2:.3f}")
    
    simple_slopes_results = []
    
    # Check for significant interactions in each model
    for results in model_results:
        if results is None or results.empty:
            continue
            
        model_name = results['model_name'].iloc[0]
        
        # Debug print for effect_name column
        print(f"Simple slopes - {model_name} effect_name column type: {results['effect_name'].dtype}")
        print(f"Simple slopes - {model_name} effect_name first few values: {results['effect_name'].head(3).tolist()}")
        
        # Validate required columns exist
        if 'effect_name' not in results.columns or 'p_value' not in results.columns:
            print(f"Warning: Missing required columns in {model_name} results")
            continue
            
        # Look for VVIQ2 interaction terms - ensure effect_name is string type
        interaction_terms = results[results['effect_name'].astype(str).str.contains('vviq2_centered') & 
                                   results['effect_name'].astype(str).str.contains(':')]
        
        print(f"\n{model_name} interaction terms with VVIQ2:")
        print(interaction_terms[['effect_name', 'p_value']])
        
        # Only calculate simple slopes for significant interactions (p < 0.05)
        significant_interactions = interaction_terms[
            (interaction_terms['p_value'] < 0.05) | 
            (interaction_terms.get('p_value_corrected', interaction_terms['p_value']) < 0.05)
        ]
        
        if significant_interactions.empty:
            print(f"No significant VVIQ2 interactions found in {model_name}")
        else:
            print(f"Found {len(significant_interactions)} significant VVIQ2 interactions in {model_name}")
            
        for _, interaction in significant_interactions.iterrows():
            effect_name = interaction['effect_name']
            print(f"Calculating simple slopes for significant interaction: {effect_name} (p={interaction['p_value']:.4f})")
            
            # Extract the main effect being moderated - use more precise matching
            main_effect_term = None
            if 'VWM_setSize_factor' in effect_name and 'vviq2_centered' in effect_name:
                # Extract the specific VWM_setSize_factor term from the interaction
                interaction_parts = effect_name.split(':')
                if len(interaction_parts) >= 2:  # Ensure we have at least 2 parts
                    for part in interaction_parts:
                        if 'VWM_setSize_factor' in part and 'vviq2_centered' not in part:
                            main_effect_term = part
                            break
            elif 'VWM_delay_factor' in effect_name and 'vviq2_centered' in effect_name:
                # Extract the specific VWM_delay_factor term from the interaction
                interaction_parts = effect_name.split(':')
                if len(interaction_parts) >= 2:  # Ensure we have at least 2 parts
                    for part in interaction_parts:
                        if 'VWM_delay_factor' in part and 'vviq2_centered' not in part:
                            main_effect_term = part
                            break
            elif 'MRT_angle_degrees_scaled' in effect_name and 'vviq2_centered' in effect_name:
                main_effect_term = 'MRT_angle_degrees_scaled'
            else:
                continue
            
            if not main_effect_term:
                print(f"Warning: Could not extract main effect term from interaction: {effect_name}")
                continue
            
            # Find main effect using exact matching
            main_effect_candidates = results[results['effect_name'] == main_effect_term]
            
            if main_effect_candidates.empty:
                print(f"Warning: Main effect '{main_effect_term}' not found in model results")
                # Fallback to pattern matching if exact match fails
                if 'VWM_setSize' in main_effect_term:
                    fallback_pattern = 'VWM_setSize_factor'
                elif 'VWM_delay' in main_effect_term:
                    fallback_pattern = 'VWM_delay_factor'
                elif 'MRT_angle_degrees' in main_effect_term:
                    fallback_pattern = 'MRT_angle_degrees_scaled'
                else:
                    continue
                    
                main_effect_candidates = results[results['effect_name'].astype(str).str.contains(fallback_pattern) & 
                                               ~results['effect_name'].astype(str).str.contains(':')]
                
                if main_effect_candidates.empty:
                    print(f"Warning: Fallback pattern '{fallback_pattern}' also not found in model results")
                    continue
                else:
                    print(f"Using fallback pattern matching for '{fallback_pattern}'")
                
            # Use the first matching main effect
            main_effect_row = main_effect_candidates.iloc[0:1]
                
            # Safely access values with error handling
            try:
                main_effect = main_effect_row['estimate'].iloc[0]
                main_se = main_effect_row['std_error'].iloc[0]
                interaction_effect = interaction['estimate']
                interaction_se = interaction['std_error']
                
                # Validate numeric values
                if pd.isna(main_effect) or pd.isna(main_se) or pd.isna(interaction_effect) or pd.isna(interaction_se):
                    print(f"Error: NaN values found in effect data for {effect_name}")
                    continue
                    
                # Ensure all values are numeric
                main_effect = float(main_effect)
                main_se = float(main_se)
                interaction_effect = float(interaction_effect)
                interaction_se = float(interaction_se)
                
            except (IndexError, KeyError, ValueError, TypeError) as e:
                print(f"Error accessing or converting effect data: {e}")
                continue
            
            # Calculate simple slopes
            high_slope = main_effect + interaction_effect * high_vviq2
            low_slope = main_effect + interaction_effect * low_vviq2
            
            # Calculate standard errors (simplified - assumes no covariance)
            high_se = np.sqrt(main_se**2 + (high_vviq2 * interaction_se)**2)
            low_se = np.sqrt(main_se**2 + (low_vviq2 * interaction_se)**2)
            
            # Calculate confidence intervals and p-values
            high_ci_lower = high_slope - 1.96 * high_se
            high_ci_upper = high_slope + 1.96 * high_se
            high_p = 2 * (1 - scipy_stats.norm.cdf(abs(high_slope / high_se))) if high_se > 0 else 1.0
            
            low_ci_lower = low_slope - 1.96 * low_se
            low_ci_upper = low_slope + 1.96 * low_se
            low_p = 2 * (1 - scipy_stats.norm.cdf(abs(low_slope / low_se))) if low_se > 0 else 1.0
            
            # Add to results
            simple_slopes_results.extend([
                {
                    'model_name': model_name,
                    'vviq2_level': 'High (+1 SD)',
                    'slope_estimate': high_slope,
                    'slope_se': high_se,
                    'slope_ci_lower': high_ci_lower,
                    'slope_ci_upper': high_ci_upper,
                    'slope_p_value': high_p
                },
                {
                    'model_name': model_name,
                    'vviq2_level': 'Low (-1 SD)',
                    'slope_estimate': low_slope,
                    'slope_se': low_se,
                    'slope_ci_lower': low_ci_lower,
                    'slope_ci_upper': low_ci_upper,
                    'slope_p_value': low_p
                }
            ])
    
    if simple_slopes_results:
        simple_slopes_df = pd.DataFrame(simple_slopes_results)
        print("\nSimple slopes results:")
        print(simple_slopes_df)
        return simple_slopes_df
    else:
        print("No simple slopes calculated - no significant interactions found")
        # Return empty DataFrame instead of None to ensure file creation
        return pd.DataFrame(columns=['model_name', 'vviq2_level', 'slope_estimate', 
                                    'slope_se', 'slope_ci_lower', 'slope_ci_upper', 'slope_p_value'])

def apply_fdr_correction(model_results):
    """
    Apply Benjamini-Hochberg FDR correction to VVIQ2 interaction terms.
    
    Parameters:
    model_results (list): List of model result DataFrames
    
    Returns:
    list: Updated model results with corrected p-values
    """
    print("\nApplying FDR correction...")
    
    if not model_results or all(result is None for result in model_results):
        print("No valid model results for FDR correction")
        return model_results
    
    # Collect all VVIQ2 interaction p-values
    vviq2_interactions = []
    for results in model_results:
        if results is None or not isinstance(results, pd.DataFrame) or results.empty:
            continue
        
        if 'effect_name' not in results.columns or 'p_value' not in results.columns:
            print(f"Warning: Missing required columns in results dataframe")
            continue
            
        # Debug print for effect_name column
        print(f"FDR correction - {results['model_name'].iloc[0]} effect_name column type: {results['effect_name'].dtype}")
        print(f"FDR correction - {results['model_name'].iloc[0]} effect_name first few values: {results['effect_name'].head(3).tolist()}")
        
        # Ensure effect_name is string type before string operations
        interactions = results[results['effect_name'].astype(str).str.contains('vviq2_centered') & 
                              results['effect_name'].astype(str).str.contains(':')]
        
        if not interactions.empty:
            for _, row in interactions.iterrows():
                # Validate row data before adding
                if pd.notna(row['p_value']) and isinstance(row['p_value'], (int, float)):
                    vviq2_interactions.append({
                        'model_name': str(row['model_name']),
                        'effect_name': str(row['effect_name']),
                        'p_value': float(row['p_value']),
                        'index': len(vviq2_interactions)
                    })
    
    if not vviq2_interactions:
        print("No VVIQ2 interactions found for FDR correction")
        # Still need to add p_value_corrected column
        for results in model_results:
            if results is not None:
                results['p_value_corrected'] = results['p_value']
        return model_results
    
    print(f"Found {len(vviq2_interactions)} VVIQ2 interaction terms for FDR correction")
    
    # Extract p-values and apply FDR correction
    p_values = [item['p_value'] for item in vviq2_interactions]
    
    # Benjamini-Hochberg procedure
    n = len(p_values)
    if n == 0:
        print("No p-values to correct")
        # Add p_value_corrected column to results
        for results in model_results:
            if results is not None and isinstance(results, pd.DataFrame) and not results.empty:
                if 'p_value_corrected' not in results.columns:
                    results['p_value_corrected'] = results['p_value']
        return model_results
        
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate corrected p-values
    corrected_p = np.zeros(n)
    for i in range(n-1, -1, -1):
        if i == n-1:
            corrected_p[sorted_indices[i]] = sorted_p[i]
        else:
            corrected_p[sorted_indices[i]] = min(
                sorted_p[i] * n / (i + 1),
                corrected_p[sorted_indices[i + 1]]
            )
    
    # Cap at 1.0
    corrected_p = np.minimum(corrected_p, 1.0)
    
    # Map back to original interactions
    for i, item in enumerate(vviq2_interactions):
        item['p_value_corrected'] = corrected_p[i]
    
    print("FDR correction results:")
    for item in vviq2_interactions:
        print(f"{item['model_name']} - {item['effect_name']}: p={item['p_value']:.4f} -> p_corrected={item['p_value_corrected']:.4f}")
    
    # Update model results with corrected p-values
    corrected_results = []
    for results in model_results:
        if results is None:
            corrected_results.append(None)
            continue
            
        results_copy = results.copy()
        results_copy['p_value_corrected'] = results_copy['p_value']  # Default to uncorrected
        
        # Update VVIQ2 interactions with corrected p-values
        for item in vviq2_interactions:
            if item['model_name'] == results_copy['model_name'].iloc[0]:
                mask = results_copy['effect_name'] == item['effect_name']
                results_copy.loc[mask, 'p_value_corrected'] = item['p_value_corrected']
        
        corrected_results.append(results_copy)
    
    return corrected_results

def save_results(model_results, simple_slopes_results):
    """
    Save analysis results to output files.
    
    Parameters:
    model_results (list): List of model result DataFrames
    simple_slopes_results (DataFrame): Simple slopes results
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combine all model results
    all_results = []
    for results in model_results:
        if results is not None and isinstance(results, pd.DataFrame) and not results.empty:
            all_results.append(results)
    
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        
        # Required columns for mixed effects results
        required_columns = ['model_name', 'effect_name', 'estimate', 'std_error', 
                           't_value', 'p_value', 'p_value_corrected', 'ci_lower', 'ci_upper']
        
        # Check if all required columns exist
        missing_columns = [col for col in required_columns if col not in combined_results.columns]
        
        # Add any missing columns with default values
        for col in missing_columns:
            print(f"Warning: Adding missing column '{col}' with default values")
            if col == 'p_value_corrected':
                combined_results[col] = combined_results.get('p_value', 1.0)
            else:
                combined_results[col] = None
        
        # Select and order required columns
        results_output = combined_results[required_columns].copy()
        
        # Save main results
        results_file = f"outputs/H2_mixed_effects_results_{timestamp}.csv"
        results_output.to_csv(results_file, index=False)
        print(f"Mixed effects results saved to: {results_file}")
        print(f"Results shape: {results_output.shape}")
        print("Results columns:", list(results_output.columns))
        print("Results first 2 rows:")
        print(results_output.head(2))
    
    # Save simple slopes results - always create a file even if no significant interactions found
    required_slope_columns = ['model_name', 'vviq2_level', 'slope_estimate', 
                             'slope_se', 'slope_ci_lower', 'slope_ci_upper', 'slope_p_value']
    
    if simple_slopes_results is None or not isinstance(simple_slopes_results, pd.DataFrame) or simple_slopes_results.empty:
        # Create empty DataFrame with required columns
        simple_slopes_results = pd.DataFrame(columns=required_slope_columns)
        print("Note: Creating empty simple slopes results file as no significant interactions were found.")
    
    # Check if all required columns exist
    missing_columns = [col for col in required_slope_columns if col not in simple_slopes_results.columns]
    
    # Add any missing columns with default values
    for col in missing_columns:
        print(f"Warning: Adding missing column '{col}' with default values")
        simple_slopes_results[col] = None
        
    # Select and order required columns
    slopes_output = simple_slopes_results[required_slope_columns].copy()
    
    slopes_file = f"outputs/H2_simple_slopes_results_{timestamp}.csv"
    slopes_output.to_csv(slopes_file, index=False)
    print(f"Simple slopes results saved to: {slopes_file}")
    print(f"Simple slopes shape: {slopes_output.shape}")
    print("Simple slopes columns:", list(slopes_output.columns))
    if not slopes_output.empty:
        print("Simple slopes first 2 rows:")
        print(slopes_output.head(2))
    else:
        print("Simple slopes file is empty (no significant interactions found)")

def main():
    """
    Main analysis function.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting H2 Mixed Effects Analysis with VVIQ2 Interactions")
        print("=" * 60)
        
        # Load and validate data
        vwm_df, mrt_df, vviq2_df = load_and_validate_data()
        if vwm_df is None or mrt_df is None or vviq2_df is None:
            print("Error: Failed to load required datasets")
            return 1
        
        # Merge and prepare data
        merged_vwm, merged_mrt, vviq2_scores = merge_and_prepare_data(vwm_df, mrt_df, vviq2_df)
        if merged_vwm is None or merged_mrt is None or vviq2_scores is None:
            print("Error: Failed to merge datasets")
            return 1
        
        # Fit models
        print("\n" + "=" * 60)
        print("FITTING MIXED-EFFECTS MODELS")
        print("=" * 60)
        
        # Try to fit all models, but continue even if some fail
        try:
            vwm_results = fit_vwm_model(merged_vwm)
            print(f"VWM model success: {vwm_results is not None}")
        except Exception as e:
            print(f"VWM model fitting failed with error: {e}")
            vwm_results = None
            
        try:
            mrt_rt_results, mrt_acc_results = fit_mrt_models(merged_mrt)
            print(f"MRT RT model success: {mrt_rt_results is not None}")
            print(f"MRT Accuracy model success: {mrt_acc_results is not None}")
        except Exception as e:
            print(f"MRT model fitting failed with error: {e}")
            mrt_rt_results, mrt_acc_results = None, None
        
        # Collect all model results
        model_results = [vwm_results, mrt_rt_results, mrt_acc_results]
        
        # Check if at least one model fitted successfully
        successful_models = [r for r in model_results if r is not None]
        if not successful_models:
            print("Error: No models fitted successfully")
            return 1
        
        print(f"\nSuccessfully fitted {len(successful_models)} out of 3 models")
        
        # Apply FDR correction
        corrected_results = apply_fdr_correction(model_results)
        
        # Conduct simple slopes analyses
        simple_slopes_results = conduct_simple_slopes(vviq2_scores, corrected_results)
        
        # Save results
        save_results(corrected_results, simple_slopes_results)
        
        print("\n" + "=" * 60)
        print("ANALYSIS COMPLETE")
        print("=" * 60)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
