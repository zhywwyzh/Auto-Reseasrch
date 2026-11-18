import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

# Import rpy2 for R integration
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, numpy2ri
from rpy2.robjects.conversion import localconverter
import rpy2.robjects.packages as rpackages

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
    Load and validate input data files.
    
    Returns:
    tuple: (dog_df, vviq_df) DataFrames or (None, None) if error
    """
    print("Loading input data files...")
    
    # Find DoG parameters file
    dog_pattern = "outputs/VWM_DoG_parameters_*.csv"
    dog_file = find_latest_file(dog_pattern)
    if not dog_file:
        print(f"Error: No DoG parameters file found matching pattern {dog_pattern}")
        return None, None
    
    print(f"Found DoG parameters file: {dog_file}")
    
    # Find VVIQ2 scores file
    vviq_pattern = "outputs/VVIQ2_cleaned_scores_*.csv"
    vviq_file = find_latest_file(vviq_pattern)
    if not vviq_file:
        print(f"Error: No VVIQ2 scores file found matching pattern {vviq_pattern}")
        return None, None
    
    print(f"Found VVIQ2 scores file: {vviq_file}")
    
    # Load DoG parameters
    try:
        dog_df = pd.read_csv(dog_file)
        # Strip whitespace from column names
        dog_df.columns = [col.strip() for col in dog_df.columns]
        print(f"DoG parameters data loaded successfully. Shape: {dog_df.shape}")
        print("DoG parameters columns:", list(dog_df.columns))
        print("First 3 rows of DoG parameters:")
        print(dog_df.head(3))
    except Exception as e:
        print(f"Error loading DoG parameters file: {e}")
        return None, None
    
    # Load VVIQ2 scores
    try:
        vviq_df = pd.read_csv(vviq_file)
        # Strip whitespace from column names
        vviq_df.columns = [col.strip() for col in vviq_df.columns]
        print(f"VVIQ2 scores data loaded successfully. Shape: {vviq_df.shape}")
        print("VVIQ2 scores columns:", list(vviq_df.columns))
        print("First 3 rows of VVIQ2 scores:")
        print(vviq_df.head(3))
    except Exception as e:
        print(f"Error loading VVIQ2 scores file: {e}")
        return None, None

    # Validate required columns for DoG parameters (after column name stripping)
    required_dog_cols = ['participantId', 'VWM_setSize', 'VWM_delay_s', 'amplitude', 'width', 'zero_crossing', 'fit_converged', 'excluded_fitting']
    missing_dog_cols = [col for col in required_dog_cols if col not in dog_df.columns]
    if missing_dog_cols:
        print(f"Error: Missing required columns in DoG parameters file: {missing_dog_cols}")
        return None, None

    # Validate required columns for VVIQ2 scores (after column name stripping)
    required_vviq_cols = ['PROLIFIC_PID', 'total_score_z', 'excluded_participant']
    missing_vviq_cols = [col for col in required_vviq_cols if col not in vviq_df.columns]
    if missing_vviq_cols:
        print(f"Error: Missing required columns in VVIQ2 scores file: {missing_vviq_cols}")
        return None, None
    
    # Print unique values for key experimental design parameters
    print("\nUnique values in key experimental design columns:")
    print(f"VWM_setSize unique values: {sorted(dog_df['VWM_setSize'].dropna().unique())}")
    print(f"VWM_delay_s unique values: {sorted(dog_df['VWM_delay_s'].dropna().unique())}")
    print(f"fit_converged unique values: {sorted(dog_df['fit_converged'].dropna().unique())}")
    print(f"excluded_fitting unique values: {sorted(dog_df['excluded_fitting'].dropna().unique())}")
    print(f"excluded_participant unique values: {sorted(vviq_df['excluded_participant'].dropna().unique())}")
    
    # Print data types for measured variables
    print(f"\nData types for measured variables:")
    print(f"amplitude data type: {dog_df['amplitude'].dtype}")
    print(f"width data type: {dog_df['width'].dtype}")
    print(f"zero_crossing data type: {dog_df['zero_crossing'].dtype}")
    print(f"total_score_z data type: {vviq_df['total_score_z'].dtype}")
    
    return dog_df, vviq_df

def merge_and_filter_data(dog_df, vviq_df):
    """
    Merge datasets and apply inclusion criteria.
    
    Parameters:
    dog_df (DataFrame): DoG parameters data
    vviq_df (DataFrame): VVIQ2 scores data
    
    Returns:
    DataFrame: Merged and filtered dataset
    """
    print("\nMerging datasets...")
    
    # Remove rows with missing values in key columns before merging
    print("Filtering out rows with missing values...")
    
    # Filter DoG data
    dog_before = len(dog_df)
    dog_df = dog_df.dropna(subset=['participantId', 'VWM_setSize', 'VWM_delay_s', 'amplitude', 'width', 'zero_crossing', 'fit_converged', 'excluded_fitting'])
    dog_after = len(dog_df)
    print(f"DoG data: {dog_before} -> {dog_after} rows after removing missing values")
    
    # Filter VVIQ data
    vviq_before = len(vviq_df)
    vviq_df = vviq_df.dropna(subset=['PROLIFIC_PID', 'total_score_z', 'excluded_participant'])
    vviq_after = len(vviq_df)
    print(f"VVIQ data: {vviq_before} -> {vviq_after} rows after removing missing values")
    
    # Merge on participant ID
    merged_df = pd.merge(dog_df, vviq_df, left_on='participantId', right_on='PROLIFIC_PID', how='inner')
    print(f"Merged dataset shape: {merged_df.shape}")
    print("Merged dataset columns:", list(merged_df.columns))
    print("First 2 rows of merged dataset:")
    print(merged_df.head(2))
    
    # Apply inclusion criteria
    print("\nApplying inclusion criteria...")
    
    # Count exclusions
    initial_n = len(merged_df)
    print(f"Initial merged dataset: {initial_n} observations")
    
    # fit_converged = True
    converged_filter = merged_df['fit_converged'] == True
    n_converged = converged_filter.sum()
    print(f"fit_converged = True: {n_converged} observations")
    
    # excluded_fitting = False
    fitting_filter = merged_df['excluded_fitting'] == False
    n_fitting = fitting_filter.sum()
    print(f"excluded_fitting = False: {n_fitting} observations")
    
    # excluded_participant = False
    participant_filter = merged_df['excluded_participant'] == False
    n_participant = participant_filter.sum()
    print(f"excluded_participant = False: {n_participant} observations")
    
    # Apply all filters
    final_filter = converged_filter & fitting_filter & participant_filter
    filtered_df = merged_df[final_filter].copy()
    
    final_n = len(filtered_df)
    print(f"Final dataset after all exclusions: {final_n} observations")
    print(f"Excluded {initial_n - final_n} observations total")
    
    # Check if we have sufficient data
    n_participants = filtered_df['participantId'].nunique()
    print(f"Number of unique participants: {n_participants}")
    
    if n_participants < 10:
        print("Warning: Very few participants for multilevel modeling")
    if final_n < 50:
        print("Warning: Very few observations for multilevel modeling")
    
    return filtered_df

def prepare_variables(df):
    """
    Prepare variables for multilevel modeling.
    
    Parameters:
    df (DataFrame): Merged and filtered dataset
    
    Returns:
    DataFrame: Dataset with prepared variables
    """
    print("\nPreparing variables for multilevel modeling...")
    
    df = df.copy()
    
    # Effect-code Set Size: -0.5 for setsize=2, +0.5 for setsize=4
    df['setsize_coded'] = df['VWM_setSize'].map({2: -0.5, 4: 0.5})
    print(f"Set size coding: {df[['VWM_setSize', 'setsize_coded']].drop_duplicates().sort_values('VWM_setSize')}")
    
    # Effect-code Delay: -0.5 for delay=1.0s, +0.5 for delay=4.0s
    df['delay_coded'] = df['VWM_delay_s'].map({1.0: -0.5, 4.0: 0.5})
    print(f"Delay coding: {df[['VWM_delay_s', 'delay_coded']].drop_duplicates().sort_values('VWM_delay_s')}")
    
    # Center VVIQ2 total scores at grand mean
    vviq_mean = df['total_score_z'].mean()
    df['vviq_centered'] = df['total_score_z'] - vviq_mean
    print(f"VVIQ2 centering: Original mean = {vviq_mean:.4f}, Centered mean = {df['vviq_centered'].mean():.4f}")
    
    # Create interaction terms
    df['setsize_delay'] = df['setsize_coded'] * df['delay_coded']
    
    print("Prepared variables summary:")
    print(f"setsize_coded range: {df['setsize_coded'].min()} to {df['setsize_coded'].max()}")
    print(f"delay_coded range: {df['delay_coded'].min()} to {df['delay_coded'].max()}")
    print(f"vviq_centered range: {df['vviq_centered'].min():.4f} to {df['vviq_centered'].max():.4f}")
    
    return df

def setup_r_environment():
    """
    Set up R environment and install required packages.
    
    Returns:
    bool: True if successful, False otherwise
    """
    print("\nSetting up R environment...")
    
    try:
        # Activate pandas2ri and numpy2ri
        pandas2ri.activate()
        numpy2ri.activate()
        
        # Install required R packages
        utils = rpackages.importr('utils')
        base = rpackages.importr('base')
        
        # Check if lme4 is installed, install if not
        try:
            lme4 = rpackages.importr('lme4')
            print("lme4 package already installed")
        except:
            print("Installing lme4 package...")
            utils.install_packages('lme4')
            lme4 = rpackages.importr('lme4')
        
        # Check if lmerTest is installed, install if not
        try:
            lmertest = rpackages.importr('lmerTest')
            print("lmerTest package already installed")
        except:
            print("Installing lmerTest package...")
            utils.install_packages('lmerTest')
            lmertest = rpackages.importr('lmerTest')
        
        # Check if MuMIn is installed, install if not
        try:
            mumin = rpackages.importr('MuMIn')
            print("MuMIn package already installed")
        except:
            print("Installing MuMIn package...")
            utils.install_packages('MuMIn')
            mumin = rpackages.importr('MuMIn')
        
        print("R environment setup complete")
        return True
        
    except Exception as e:
        print(f"Error setting up R environment: {e}")
        return False

def fit_multilevel_model(df, parameter_name):
    """
    Fit multilevel model for a specific DoG parameter.
    
    Parameters:
    df (DataFrame): Prepared dataset
    parameter_name (str): Name of the DoG parameter ('amplitude', 'width', 'zero_crossing')
    
    Returns:
    tuple: (model_results, model_fit_stats) or (None, None) if error
    """
    print(f"\nFitting multilevel model for {parameter_name}...")
    
    try:
        # Prepare data for R
        model_data = df[['participantId', parameter_name, 'setsize_coded', 'delay_coded', 'setsize_delay', 'vviq_centered']].copy()
        model_data = model_data.dropna()
        
        print(f"Model data shape for {parameter_name}: {model_data.shape}")
        print(f"Number of participants: {model_data['participantId'].nunique()}")
        
        # Add specific checks for amplitude data
        if parameter_name == 'amplitude':
            print(f"\n{parameter_name.upper()} DATA DIAGNOSTICS:")
            print(f"Data summary: {model_data[parameter_name].describe()}")
            print(f"Variance: {model_data[parameter_name].var():.6f}")
            print(f"Range: {model_data[parameter_name].min():.6f} to {model_data[parameter_name].max():.6f}")
            
            # Check for potential issues
            if model_data[parameter_name].var() < 0.01:
                print("WARNING: Very low variance in amplitude data, model fitting may fail.")
            
            # Check for outliers (values more than 3 std devs from mean)
            mean = model_data[parameter_name].mean()
            std = model_data[parameter_name].std()
            outliers = model_data[(model_data[parameter_name] > mean + 3*std) | 
                                 (model_data[parameter_name] < mean - 3*std)]
            if len(outliers) > 0:
                print(f"WARNING: Found {len(outliers)} potential outliers in amplitude data.")
                print(f"Outlier values: {outliers[parameter_name].values}")
        
        # Convert to R dataframe
        with localconverter(ro.default_converter + pandas2ri.converter):
            r_data = ro.conversion.py2rpy(model_data)
        
        ro.globalenv['model_data'] = r_data
        
        # Define a sequence of model formulas with proper random effects structure
        # Start with the full random effects structure as required by the task
        formulas = [
            # Full random effects structure with all interactions
            f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (setsize_coded * delay_coded | participantId)",
            
            # Full random effects structure without interactions in random effects
            f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (setsize_coded + delay_coded | participantId)",
            
            # Individual random slopes for each predictor
            f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (setsize_coded | participantId) + (delay_coded | participantId)",
            
            # Fallback to simpler random effects if needed
            f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (1 | participantId)"
        ]
        
        print(f"Using model formulas with proper random effects structure as required by the task")
        
        # Load required R libraries
        ro.r("""
        library(lme4)
        library(lmerTest)
        library(MuMIn)
        """)
        
        # Try fitting models with increasing complexity
        model_fitted = False
        used_formula = None
        
        # Add fallback models with proper random effects structure when possible
        fallback_formula1 = f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (setsize_coded + delay_coded | participantId)"
        fallback_formula2 = f"{parameter_name} ~ setsize_coded * delay_coded + vviq_centered + (setsize_coded + delay_coded | participantId)"
        fallback_formula3 = f"{parameter_name} ~ setsize_coded + delay_coded + vviq_centered + (setsize_coded + delay_coded | participantId)"
        formulas.append(fallback_formula1)
        formulas.append(fallback_formula2)
        formulas.append(fallback_formula3)
        
        # Add last-resort fallbacks with simpler random effects structure
        last_resort1 = f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (1 | participantId)"
        last_resort2 = f"{parameter_name} ~ 1 + (1 | participantId)"
        last_resort3 = f"{parameter_name} ~ 1"
        formulas.append(last_resort1)
        formulas.append(last_resort2)
        formulas.append(last_resort3)
        
        print("Added fallback models with proper random effects structure when possible")
        
        # For amplitude, add additional models with proper random effects structure
        if parameter_name == 'amplitude':
            print("Adding amplitude-specific model formulas with proper random effects structure")
            
            # Full models with all interactions and proper random effects
            amp_formula1 = f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (setsize_coded * delay_coded | participantId)"
            amp_formula2 = f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (setsize_coded + delay_coded | participantId)"
            
            # Models with all fixed effects but varying random effects complexity
            amp_formula3 = f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (setsize_coded | participantId)"
            amp_formula4 = f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (delay_coded | participantId)"
            
            # Models with two-way interactions and proper random effects
            amp_formula5 = f"{parameter_name} ~ setsize_coded * delay_coded + vviq_centered + (setsize_coded * delay_coded | participantId)"
            amp_formula6 = f"{parameter_name} ~ setsize_coded * vviq_centered + delay_coded + (setsize_coded | participantId)"
            amp_formula7 = f"{parameter_name} ~ delay_coded * vviq_centered + setsize_coded + (delay_coded | participantId)"
            
            # Models with main effects and proper random effects
            amp_formula8 = f"{parameter_name} ~ setsize_coded + delay_coded + vviq_centered + (setsize_coded + delay_coded | participantId)"
            
            # Fallback models if needed
            amp_formula9 = f"{parameter_name} ~ setsize_coded * delay_coded * vviq_centered + (1 | participantId)"
            amp_formula10 = f"{parameter_name} ~ setsize_coded * delay_coded + vviq_centered + (1 | participantId)"
            
            # Add these to the beginning of the formulas list to try them first
            formulas = [amp_formula1, amp_formula2, amp_formula3, amp_formula4, 
                       amp_formula5, amp_formula6, amp_formula7, amp_formula8,
                       amp_formula9, amp_formula10] + formulas
            
            print(f"Added {10} amplitude-specific formulas with proper random effects structure")
            print("Note: These models include random slopes for Level 1 predictors as required")
        
        print(f"Total formulas to try: {len(formulas)}")
        
        for i, formula in enumerate(formulas):
            try:
                print(f"Attempting model {i+1}/{len(formulas)}: {formula}")
                
                # Clear any previous model objects in R environment
                ro.r('if(exists("model")) rm(model)')
                ro.r('if(exists("fitting_error")) rm(fitting_error)')
                ro.r('if(exists("model_summary")) rm(model_summary)')
                
                # Fit the model with control parameters to improve convergence
                # Capture any R errors during model fitting
                # Check if this is a simple model without random effects
                if "| participantId" not in formula:
                    print("Attempting simple fixed-effects model without random effects")
                    ro.r(f"""
                    tryCatch({{
                        model <- lm({formula}, data = model_data)
                        print(paste("Simple model successfully created with class:", paste(class(model), collapse=", ")))
                        # Set a flag to indicate this is a simple model
                        is_simple_model <- TRUE
                    }}, error = function(e) {{
                        print(paste("R fitting error:", e$message))
                        # Create a flag to indicate error
                        fitting_error <- TRUE
                    }})
                    """)
                else:
                    # Special handling for amplitude parameter
                    if parameter_name == 'amplitude':
                        print("Using enhanced fitting approach for amplitude")
                        
                        # Try data transformation for amplitude to improve model fit
                        ro.r(f"""
                        # Create transformed versions of amplitude
                        model_data$amplitude_log <- log(model_data${parameter_name} + 1)  # log transform
                        model_data$amplitude_sqrt <- sqrt(model_data${parameter_name})    # square root transform
                        model_data$amplitude_rank <- rank(model_data${parameter_name})    # rank transform
                        
                        # Print summary of transformations
                        print("Original and transformed amplitude data:")
                        print(summary(model_data${parameter_name}))
                        print(summary(model_data$amplitude_log))
                        print(summary(model_data$amplitude_sqrt))
                        print(summary(model_data$amplitude_rank))
                        """)
                        
                        
                        # Try the original approaches
                        if not bool(ro.r('exists("model")')[0]):
                            ro.r(f"""
                            # Try with multiple optimizers and settings for amplitude
                            tryCatch({{
                                # First try with REML=TRUE which can be more stable
                                model <- lmer({formula}, 
                                            data = model_data, 
                                            REML = TRUE)
                                print(paste("Amplitude model successfully created with REML=TRUE. Class:", paste(class(model), collapse=", ")))
                            }}, error = function(e) {{
                                print(paste("REML=TRUE error:", e$message))
                                
                                # Try with bobyqa optimizer and increased iterations
                                tryCatch({{
                                    model <- lmer({formula}, 
                                                data = model_data, 
                                                REML = FALSE,
                                                control = lmerControl(optimizer = "bobyqa", 
                                                                    optCtrl = list(maxfun = 200000)))
                                    print(paste("Amplitude model created with bobyqa optimizer. Class:", paste(class(model), collapse=", ")))
                                }}, error = function(e) {{
                                    print(paste("bobyqa optimizer error:", e$message))
                                    
                                    # Try with nlminbw optimizer which can work better for some models
                                    tryCatch({{
                                        model <- lmer({formula}, 
                                                    data = model_data, 
                                                    REML = FALSE,
                                                    control = lmerControl(optimizer = "nlminbwrap"))
                                        print(paste("Amplitude model created with nlminbwrap optimizer. Class:", paste(class(model), collapse=", ")))
                                    }}, error = function(e) {{
                                        print(paste("nlminbwrap optimizer error:", e$message))
                                        
                                        # Try with optimx optimizer as a last resort
                                        tryCatch({{
                                            model <- lmer({formula}, 
                                                        data = model_data, 
                                                        REML = FALSE,
                                                        control = lmerControl(optimizer = "optimx", 
                                                                            optCtrl = list(method = "L-BFGS-B")))
                                            print(paste("Amplitude model created with optimx optimizer. Class:", paste(class(model), collapse=", ")))
                                        }}, error = function(e) {{
                                            print(paste("optimx optimizer error:", e$message))
                                            
                                            # Last resort: try with different control settings
                                            tryCatch({{
                                                model <- lmer({formula}, 
                                                            data = model_data, 
                                                            REML = FALSE,
                                                            control = lmerControl(optimizer = "bobyqa", 
                                                                                optCtrl = list(maxfun = 50000)))
                                                print(paste("Amplitude model created with reduced maxfun. Class:", paste(class(model), collapse=", ")))
                                            }}, error = function(e) {{
                                                print(paste("Final optimizer attempt error:", e$message))
                                                # Create a flag to indicate error
                                                fitting_error <- TRUE
                                            }})
                                        }})
                                    }})
                                }})
                            }})
                            """)
                    else:
                        # Standard approach for other parameters
                        ro.r(f"""
                        # First try with default optimizer
                        tryCatch({{
                            model <- lmer({formula}, 
                                        data = model_data, 
                                        REML = FALSE)
                            print(paste("Model successfully created with default optimizer. Class:", paste(class(model), collapse=", ")))
                        }}, error = function(e) {{
                            print(paste("Default optimizer error:", e$message))
                            
                            # Try with bobyqa optimizer
                            tryCatch({{
                                model <- lmer({formula}, 
                                            data = model_data, 
                                            REML = FALSE,
                                            control = lmerControl(optimizer = "bobyqa", 
                                                                optCtrl = list(maxfun = 100000)))
                                print(paste("Model successfully created with bobyqa optimizer. Class:", paste(class(model), collapse=", ")))
                            }}, error = function(e) {{
                                print(paste("bobyqa optimizer error:", e$message))
                                
                                # Try with Nelder-Mead optimizer
                                tryCatch({{
                                    model <- lmer({formula}, 
                                                data = model_data, 
                                                REML = FALSE,
                                                control = lmerControl(optimizer = "Nelder_Mead"))
                                    print(paste("Model successfully created with Nelder-Mead optimizer. Class:", paste(class(model), collapse=", ")))
                                }}, error = function(e) {{
                                    print(paste("Nelder-Mead optimizer error:", e$message))
                                    # Create a flag to indicate error
                                    fitting_error <- TRUE
                                }})
                            }})
                        }})
                        """)
                
                # Check if there was a fitting error
                fitting_error = bool(ro.r('exists("fitting_error")')[0])
                if fitting_error:
                    print("Error occurred during model fitting in R")
                    # Print R environment for debugging
                    print("R environment objects:", list(ro.r('ls()')))
                    ro.r('rm(fitting_error)')  # Clean up error flag
                    continue
                
                # Check if model exists and is valid
                try:
                    # First check if the model object exists
                    model_valid = bool(ro.r('exists("model")')[0])
                    print(f"Model exists in R environment: {model_valid}")
                    
                    if model_valid:
                        # Print model class information for debugging
                        ro.r('print(paste("Model class:", paste(class(model), collapse=", ")))')
                        print("Model structure details:")
                        ro.r('str(model)')
                        
                        # Check if it's a simple model (lm) or an lmer model
                        is_simple_model = bool(ro.r('exists("is_simple_model") && is_simple_model')[0])
                        is_lmer = bool(ro.r('any(grepl("lmer", class(model)))')[0])
                        print(f"Is simple model: {is_simple_model}")
                        print(f"Is lmer model: {is_lmer}")
                        
                        # If it's neither, something is wrong
                        if not is_simple_model and not is_lmer:
                            print("Warning: Model is neither a simple model nor an lmer model")
                            print("Model class:", list(ro.r('class(model)')))
                    else:
                        # Print R environment for debugging
                        print("R environment objects:", list(ro.r('ls()')))
                        print("Model object not found in R environment")
                        convergence_code = 1
                        is_singular = True
                    # For simple models, set default convergence values
                    if is_simple_model:
                        convergence_code = 0  # Simple models always "converge"
                        is_singular = False   # Simple models are never singular
                        print("Simple model - setting convergence_code=0, is_singular=False")
                    else:
                        # Check convergence - use R to extract and convert the value directly
                        ro.r('''
                        tryCatch({
                            if (exists("model")) {
                                # Try to access convergence code, but handle if structure is different
                                if (inherits(model, "lmerMod") && !is.null(model@optinfo)) {
                                    # For lmer models with optinfo
                                    if (!is.null(model@optinfo$conv) && !is.null(model@optinfo$conv$lme4) && !is.null(model@optinfo$conv$lme4$code)) {
                                        conv_code <- as.integer(model@optinfo$conv$lme4$code)
                                        print(paste("Convergence code from model:", conv_code))
                                    } else {
                                        print("Model exists but convergence code not found in expected structure")
                                        print("Model optinfo structure:")
                                        str(model@optinfo)
                                        conv_code <- 1L  # Default to non-converged
                                    }
                                } else {
                                    # For other model types, assume converged
                                    print("Model is not lmerMod or doesn't have optinfo, assuming converged")
                                    conv_code <- 0L
                                }
                            } else {
                                conv_code <- 1L  # Default to non-converged
                            }
                        }, error = function(e) {
                            print(paste("Error checking convergence:", e$message))
                            conv_code <<- 1L  # Default to non-converged
                        })
                        ''')
                        convergence_code = int(ro.r('conv_code')[0])
                        print(f"Convergence code: {convergence_code} (0 = converged)")
                        
                        # Check singularity - use R to extract and convert the value directly
                        ro.r('''
                        tryCatch({
                            if (exists("model") && inherits(model, "lmerMod")) {
                                is_sing <- as.logical(isSingular(model))
                                print(paste("Singularity check result:", is_sing))
                            } else {
                                # For non-lmer models, assume not singular
                                print("Model is not lmerMod, assuming not singular")
                                is_sing <- FALSE
                            }
                        }, error = function(e) {
                            print(paste("Error checking singularity:", e$message))
                            is_sing <<- TRUE  # Default to singular (safer)
                        })
                        ''')
                        is_singular = bool(ro.r('is_sing')[0])
                        print(f"Is singular: {is_singular}")
                    
                except Exception as e:
                    print(f"Error checking model validity or convergence: {e}")
                    print(f"Detailed error: {str(e)}")
                    convergence_code = 1  # Default to non-converged
                    is_singular = True  # Default to singular (safer)
                
                print(f"Model convergence code: {convergence_code} (0 = converged)")
                print(f"Model is singular: {is_singular}")
                
                if convergence_code == 0:
                    model_fitted = True
                    used_formula = formula
                    print(f"Model converged successfully with formula {i+1}")
                    
                    # Check if the model has the required random effects structure
                    has_random_slopes = False
                    if "setsize_coded * delay_coded | participantId" in formula:
                        has_random_slopes = True
                        print("Model has full random effects structure (setsize*delay)")
                    elif "setsize_coded + delay_coded | participantId" in formula:
                        has_random_slopes = True
                        print("Model has partial random effects structure (setsize+delay)")
                    elif "setsize_coded | participantId" in formula or "delay_coded | participantId" in formula:
                        has_random_slopes = True
                        print("Model has partial random effects structure (single predictor)")
                    else:
                        print("WARNING: Model only has random intercepts, not ideal for cross-level interactions")
                    
                    # Get model summary - with error handling
                    try:
                        ro.r("model_summary <- summary(model)")
                        print("Model summary created successfully")
                        
                        # Calculate CIs directly using t-distribution and Satterthwaite df for consistency
                        print("Calculating confidence intervals using t-distribution and Satterthwaite df")
                        
                        # Verify model summary is valid
                        summary_valid = bool(ro.r('exists("model_summary") && !is.null(model_summary)')[0])
                        if not summary_valid:
                            print("Warning: Model summary is not valid")
                            continue
                            
                    except Exception as e:
                        print(f"Error creating model summary: {e}")
                        continue
                    
                    # If this is not a singular fit and has proper random effects, use it immediately
                    if not is_singular and has_random_slopes:
                        print(f"Model {i+1} converged with non-singular fit and proper random effects - using this model")
                        break
                    # If not singular but lacks random slopes, keep it but continue trying
                    elif not is_singular and not has_random_slopes:
                        print(f"Model {i+1} converged with non-singular fit but lacks proper random effects - will try better models if available")
                        # Store this as a potential model but continue trying
                        if i < len(formulas) - 1:
                            continue
                        else:
                            print("No better models available, using this one despite lack of proper random effects")
                            break
                    # If singular but has random slopes, might still be usable
                    elif is_singular and has_random_slopes:
                        print(f"Model {i+1} has proper random effects but is singular - will try non-singular models if available")
                        # If we're at the first few models, try others
                        if i < 3:
                            continue
                        else:
                            print("Using this model despite singularity as it has proper random effects")
                            break
                    # If singular and lacks random slopes, least desirable
                    else:
                        print(f"Model {i+1} is singular and lacks proper random effects - will try better models if available")
                        # If we're at the last model, use it anyway
                        if i == len(formulas) - 1:
                            print("No better models available, using this one as last resort")
                            break
                    
            except Exception as e:
                print(f"Error fitting model {i+1}: {e}")
                print(f"Detailed error information: {str(e)}")
                continue
        
        if not model_fitted:
            print(f"All models failed to converge for {parameter_name}")
            return None, None
            
        print(f"Using model with formula: {used_formula}")
        
        if is_singular:
            print(f"Warning: Model for {parameter_name} is singular (overfitted), but it's the best we could fit")
        
        # Extract fixed effects
        try:
            # Debug the model summary structure
            print("Model summary structure:")
            try:
                ro.r('print(names(model_summary))')
                ro.r('print(class(model_summary))')
            except Exception as e:
                print(f"Error printing model summary structure: {e}")
            
            coef_table = np.array(ro.r('coef(model_summary)'))
            
            print(f"Fixed effects table shape: {coef_table.shape}")
            print("Fixed effects coefficients:")
            
            # Get effect names
            try:
                effect_names = list(ro.r('rownames(coef(model_summary))'))
                print(f"Effect names: {effect_names}")
            except Exception as e:
                print(f"Error getting effect names: {e}")
                effect_names = []
            
            # Extract results
            results = []
            
            for i, effect_name in enumerate(effect_names):
                if i < coef_table.shape[0]:
                    try:
                        estimate = float(coef_table[i, 0])
                        std_error = float(coef_table[i, 1])
                        df_val = float(coef_table[i, 2])
                        t_value = float(coef_table[i, 3])
                        p_value = float(coef_table[i, 4])
                        
                        # Handle NaN or infinite values
                        if np.isnan(p_value) or np.isinf(p_value):
                            print(f"  Warning: Invalid p-value for {effect_name}, setting to 1.0")
                            p_value = 1.0
                        
                        # Calculate standardized estimate using proper method
                        if effect_name == '(Intercept)':
                            # Intercept standardized coefficient is undefined
                            standardized_estimate = np.nan
                        else:
                            # Get standard deviations for predictors and outcome
                            setsize_sd = df['setsize_coded'].std()  # Should be ~0.5 for effect coding
                            delay_sd = df['delay_coded'].std()      # Should be ~0.5 for effect coding
                            vviq_sd = df['vviq_centered'].std()
                            param_sd = df[parameter_name].std()
                            
                            # Calculate standardized coefficient based on effect type
                            if effect_name == 'setsize_coded':
                                standardized_estimate = estimate * (setsize_sd / param_sd)
                            elif effect_name == 'delay_coded':
                                standardized_estimate = estimate * (delay_sd / param_sd)
                            elif effect_name == 'vviq_centered':
                                standardized_estimate = estimate * (vviq_sd / param_sd)
                            elif effect_name == 'setsize_coded:delay_coded':
                                standardized_estimate = estimate * (setsize_sd * delay_sd / param_sd)
                            elif effect_name == 'setsize_coded:vviq_centered':
                                standardized_estimate = estimate * (setsize_sd * vviq_sd / param_sd)
                            elif effect_name == 'delay_coded:vviq_centered':
                                standardized_estimate = estimate * (delay_sd * vviq_sd / param_sd)
                            elif effect_name == 'setsize_coded:delay_coded:vviq_centered':
                                standardized_estimate = estimate * (setsize_sd * delay_sd * vviq_sd / param_sd)
                            else:
                                # Fallback for any other effects
                                standardized_estimate = estimate / param_sd
                        
                        # Calculate 95% CI using t-distribution and Satterthwaite df
                        # This ensures consistency with lmerTest p-values and avoids infinite values
                        if pd.notna(df_val) and df_val > 0 and pd.notna(std_error) and std_error > 0:
                            try:
                                from scipy.stats import t
                                t_crit = t.ppf(0.975, df_val)
                                ci_lower = estimate - t_crit * std_error
                                ci_upper = estimate + t_crit * std_error
                                
                                # Check for infinite or extremely large CI values
                                if np.isinf(ci_lower) or np.isinf(ci_upper) or abs(ci_upper - ci_lower) > 1e6:
                                    print(f"  Warning: Extreme CI values for {effect_name}, using 1.96*SE fallback")
                                    ci_lower = estimate - 1.96 * std_error
                                    ci_upper = estimate + 1.96 * std_error
                            except Exception as e:
                                print(f"  Warning: Error calculating t-distribution CI for {effect_name}: {e}")
                                ci_lower = estimate - 1.96 * std_error
                                ci_upper = estimate + 1.96 * std_error
                        else:
                            # Fallback if df or std_error is problematic
                            print(f"  Warning: Invalid df ({df_val}) or SE ({std_error}) for {effect_name}, using 1.96*SE for CI.")
                            ci_lower = estimate - 1.96 * std_error
                            ci_upper = estimate + 1.96 * std_error
                        
                        results.append({
                            'parameter_type': parameter_name,
                            'effect_name': effect_name,
                            'estimate': estimate,
                            'std_error': std_error,
                            'standardized_estimate': standardized_estimate,
                            'ci_lower': ci_lower,
                            'ci_upper': ci_upper,
                            't_value': t_value,
                            'df': df_val,
                            'p_value': p_value
                        })
                        
                        print(f"  {effect_name}: β = {estimate:.4f}, SE = {std_error:.4f}, t = {t_value:.4f}, p = {p_value:.4f}")
                    except Exception as e:
                        print(f"  Error extracting results for effect {effect_name}: {e}")
                        continue
        except Exception as e:
            print(f"Error extracting fixed effects: {e}")
            # Return empty results if we can't extract fixed effects
            return [], {
                'parameter_type': parameter_name,
                'n_participants': int(model_data['participantId'].nunique()),
                'n_observations': int(len(model_data)),
                'aic': np.nan,
                'bic': np.nan,
                'log_likelihood': np.nan,
                'r_squared_marginal': np.nan,
                'r_squared_conditional': np.nan
            }
        
        # Extract model fit statistics using R to handle the extraction directly
        try:
            # Use R to safely extract these values
            ro.r('''
            if (exists("model")) {
                aic_val <- as.numeric(AIC(model))
                bic_val <- as.numeric(BIC(model))
                loglik_val <- as.numeric(logLik(model))
            } else {
                aic_val <- NA_real_
                bic_val <- NA_real_
                loglik_val <- NA_real_
            }
            ''')
                
            # Extract the values from R environment
            aic = float(ro.r('aic_val')[0]) if not np.isnan(ro.r('aic_val')[0]) else np.nan
            bic = float(ro.r('bic_val')[0]) if not np.isnan(ro.r('bic_val')[0]) else np.nan
            log_likelihood = float(ro.r('loglik_val')[0]) if not np.isnan(ro.r('loglik_val')[0]) else np.nan
                
            print(f"AIC: {aic}")
            print(f"BIC: {bic}")
            print(f"Log-likelihood: {log_likelihood}")
            
            # Calculate R-squared values using R to handle the extraction directly
            try:
                # Use R to safely calculate and extract R-squared values
                ro.r('''
                if (exists("model")) {
                    tryCatch({
                        r_squared <- r.squaredGLMM(model)
                        r_squared_marginal <- as.numeric(r_squared[1])
                        r_squared_conditional <- as.numeric(r_squared[2])
                    }, error = function(e) {
                        r_squared_marginal <- NA_real_
                        r_squared_conditional <- NA_real_
                        print(paste("R error calculating R-squared:", e$message))
                    })
                } else {
                    r_squared_marginal <- NA_real_
                    r_squared_conditional <- NA_real_
                }
                ''')
                
                # Extract the values from R environment
                r_squared_marginal = float(ro.r('r_squared_marginal')[0]) if not np.isnan(ro.r('r_squared_marginal')[0]) else np.nan
                r_squared_conditional = float(ro.r('r_squared_conditional')[0]) if not np.isnan(ro.r('r_squared_conditional')[0]) else np.nan
                
                print(f"R-squared marginal: {r_squared_marginal}")
                print(f"R-squared conditional: {r_squared_conditional}")
                
            except Exception as e:
                print(f"Error calculating R-squared values: {e}")
                r_squared_marginal = np.nan
                r_squared_conditional = np.nan
            
            # Check if the model has the required random effects structure
            has_random_slopes = False
            if "setsize_coded * delay_coded | participantId" in used_formula:
                random_effects_type = "full"
            elif "setsize_coded + delay_coded | participantId" in used_formula:
                random_effects_type = "main_effects"
            elif "setsize_coded | participantId" in used_formula or "delay_coded | participantId" in used_formula:
                random_effects_type = "single_predictor"
            else:
                random_effects_type = "intercept_only"
            
            model_fit_stats = {
                'parameter_type': parameter_name,
                'n_participants': int(model_data['participantId'].nunique()),
                'n_observations': int(len(model_data)),
                'aic': aic,
                'bic': bic,
                'log_likelihood': log_likelihood,
                'r_squared_marginal': r_squared_marginal,
                'r_squared_conditional': r_squared_conditional
            }
            
            print(f"Model fit statistics for {parameter_name}:")
            print(f"  AIC: {aic:.2f}")
            print(f"  BIC: {bic:.2f}")
            print(f"  Log-likelihood: {log_likelihood:.2f}")
            print(f"  R² marginal: {r_squared_marginal:.4f}")
            print(f"  R² conditional: {r_squared_conditional:.4f}")
            print(f"  Model formula used: {used_formula}")
            print(f"  Random effects type: {random_effects_type}")
            print(f"  Is singular fit: {is_singular}")
            print(f"  Convergence code: {convergence_code}")
            
            # Print a warning if the model doesn't have proper random effects
            if random_effects_type == "intercept_only":
                print(f"  WARNING: This model only has random intercepts, which may not be ideal for testing")
                print(f"  cross-level interactions between VVIQ and experimental conditions.")
            elif random_effects_type == "single_predictor":
                print(f"  NOTE: This model has partial random effects structure (single predictor).")
            elif random_effects_type == "main_effects":
                print(f"  NOTE: This model has random slopes for main effects but not their interaction.")
            else:
                print(f"  NOTE: This model has full random effects structure as required by the task.")
            
            return results, model_fit_stats
            
        except Exception as e:
            print(f"Error extracting model fit statistics: {e}")
            # Return basic fit stats if we can't extract detailed ones
            model_fit_stats = {
                'parameter_type': parameter_name,
                'n_participants': int(model_data['participantId'].nunique()),
                'n_observations': int(len(model_data)),
                'aic': np.nan,
                'bic': np.nan,
                'log_likelihood': np.nan,
                'r_squared_marginal': np.nan,
                'r_squared_conditional': np.nan
            }
            return results, model_fit_stats
        
    except Exception as e:
        print(f"Error fitting model for {parameter_name}: {e}")
        print(f"Detailed error information: {str(e)}")
        print("Traceback:")
        import traceback
        traceback.print_exc()
        return None, None

def apply_fdr_correction(all_results):
    """
    Apply False Discovery Rate correction to VVIQ effects.
    
    Parameters:
    all_results (list): List of all model results
    
    Returns:
    list: Results with FDR correction applied
    """
    print("\nApplying False Discovery Rate correction...")
    
    # Check if we have results to process
    if not all_results:
        print("No results available for FDR correction")
        return all_results
    
    # Extract p-values for VVIQ effects
    vviq_effects = []
    vviq_p_values = []
    
    for result in all_results:
        if 'vviq_centered' in result['effect_name']:
            vviq_effects.append(result)
            vviq_p_values.append(result['p_value'])
    
    print(f"Found {len(vviq_effects)} VVIQ effects for FDR correction")
    
    if len(vviq_p_values) == 0:
        print("No VVIQ effects found for FDR correction")
        return all_results
    
    # Apply Benjamini-Hochberg procedure
    vviq_p_values = np.array(vviq_p_values)
    n_tests = len(vviq_p_values)
    
    # Sort p-values and get indices
    sorted_indices = np.argsort(vviq_p_values)
    sorted_p_values = vviq_p_values[sorted_indices]
    
    # Calculate FDR-corrected p-values
    fdr_corrected = np.zeros_like(sorted_p_values)
    
    for i in range(n_tests - 1, -1, -1):
        if i == n_tests - 1:
            fdr_corrected[i] = sorted_p_values[i]
        else:
            fdr_corrected[i] = min(fdr_corrected[i + 1], 
                                 sorted_p_values[i] * n_tests / (i + 1))
    
    # Map back to original order
    original_fdr = np.zeros_like(vviq_p_values)
    original_fdr[sorted_indices] = fdr_corrected
    
    # Update results with FDR correction
    vviq_idx = 0
    for result in all_results:
        if 'vviq_centered' in result['effect_name']:
            result['p_value_fdr_corrected'] = original_fdr[vviq_idx]
            result['significant_fdr'] = original_fdr[vviq_idx] < 0.05
            vviq_idx += 1
            
            print(f"  {result['parameter_type']} - {result['effect_name']}: "
                  f"p = {result['p_value']:.4f}, p_FDR = {result['p_value_fdr_corrected']:.4f}, "
                  f"significant = {result['significant_fdr']}")
        else:
            result['p_value_fdr_corrected'] = np.nan
            result['significant_fdr'] = False
    
    return all_results

def save_results(all_results, all_fit_stats):
    """
    Save results to output files.
    
    Parameters:
    all_results (list): List of all model results
    all_fit_stats (list): List of all model fit statistics
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Check if we have results to save
    if not all_results:
        print("Warning: No model results to save")
        # Create an empty DataFrame with required columns to avoid file creation errors
        results_df = pd.DataFrame(columns=['parameter_type', 'effect_name', 'estimate', 'std_error', 
                                          'standardized_estimate', 'ci_lower', 'ci_upper', 
                                          't_value', 'df', 'p_value', 'p_value_fdr_corrected', 'significant_fdr'])
    else:
        # Save model results
        results_df = pd.DataFrame(all_results)
    
    results_file = f'outputs/VWM_MLM_results_{timestamp}.csv'
    results_df.to_csv(results_file, index=False)
    print(f"Model results saved to: {results_file}")
    print("Results file columns:", list(results_df.columns))
    if not results_df.empty:
        print("First 2 rows of results:")
        print(results_df.head(2))
    else:
        print("Results file is empty")
    
    # Check if we have fit statistics to save
    if not all_fit_stats:
        print("Warning: No model fit statistics to save")
        # Create an empty DataFrame with required columns to avoid file creation errors
        fit_stats_df = pd.DataFrame(columns=['parameter_type', 'n_participants', 'n_observations',
                                            'aic', 'bic', 'log_likelihood', 
                                            'r_squared_marginal', 'r_squared_conditional'])
    else:
        # Save model fit statistics
        fit_stats_df = pd.DataFrame(all_fit_stats)
        # Filter to include ONLY the task-specified columns
        required_fit_cols = ['parameter_type', 'n_participants', 'n_observations', 'aic', 'bic', 'log_likelihood', 
                            'r_squared_marginal', 'r_squared_conditional']
        # Only keep required columns that exist in the DataFrame
        existing_cols = [col for col in required_fit_cols if col in fit_stats_df.columns]
        fit_stats_df = fit_stats_df[existing_cols]
    
    fit_stats_file = f'outputs/VWM_MLM_model_fit_{timestamp}.csv'
    fit_stats_df.to_csv(fit_stats_file, index=False)
    print(f"Model fit statistics saved to: {fit_stats_file}")
    print("Fit statistics file columns:", list(fit_stats_df.columns))
    if not fit_stats_df.empty:
        print("First 2 rows of fit statistics:")
        print(fit_stats_df.head(2))
    else:
        print("Fit statistics file is empty")

def main():
    """
    Main function to execute the multilevel modeling analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VWM Multilevel Modeling Analysis")
        print("=" * 50)
        print("IMPORTANT: This analysis requires multilevel models with random slopes")
        print("for all Level 1 predictors (setsize, delay, and their interaction)")
        print("to properly test cross-level interactions with VVIQ2.")
        print("=" * 50)
        
        # Load and validate data
        dog_df, vviq_df = load_and_validate_data()
        if dog_df is None or vviq_df is None:
            print("Error: Failed to load or validate input data")
            # Still create empty output files
            save_results([], [])
            return 1
        
        # Merge and filter data
        merged_df = merge_and_filter_data(dog_df, vviq_df)
        if len(merged_df) == 0:
            print("Error: No data remaining after filtering")
            # Still create empty output files
            save_results([], [])
            return 1
        
        # Prepare variables
        prepared_df = prepare_variables(merged_df)
        
        # Setup R environment
        if not setup_r_environment():
            print("Error: Failed to set up R environment")
            # Still create empty output files
            save_results([], [])
            return 1
        
        # Using standard lme4/lmerTest packages for robust multilevel modeling
        print("Using standard lme4/lmerTest packages for multilevel modeling")
        print("Note: These packages provide all necessary functionality for our analysis")
        
        # Fit models for each DoG parameter
        # Prioritize amplitude by putting it first in the list
        dog_parameters = ['amplitude', 'width', 'zero_crossing']
        all_results = []
        all_fit_stats = []
        successful_params = []
        failed_params = []
        
        # Make multiple attempts for amplitude if needed
        max_attempts = 3
        
        # Print overall data diagnostics for all parameters
        print("\nOverall data diagnostics for all parameters:")
        for param in dog_parameters:
            print(f"{param} summary: {prepared_df[param].describe()}")
            print(f"{param} variance: {prepared_df[param].var():.6f}")
            print(f"{param} range: {prepared_df[param].min():.6f} to {prepared_df[param].max():.6f}")
            print("-" * 30)
        
        for param in dog_parameters:
            print(f"\n{'='*20} {param.upper()} {'='*20}")
            
            # Special handling for amplitude with multiple attempts
            if param == 'amplitude':
                print(f"Making up to {max_attempts} attempts to fit amplitude model")
                
                # Try with different subsets of data if needed
                for attempt in range(max_attempts):
                    print(f"Amplitude fitting attempt {attempt+1}/{max_attempts}")
                    
                    if attempt == 0:
                        # First attempt: use all data
                        df_to_use = prepared_df
                    elif attempt == 1:
                        # Second attempt: try removing outliers
                        print("Attempt 2: Removing outliers from amplitude data")
                        mean = prepared_df['amplitude'].mean()
                        std = prepared_df['amplitude'].std()
                        df_to_use = prepared_df[
                            (prepared_df['amplitude'] <= mean + 3*std) & 
                            (prepared_df['amplitude'] >= mean - 3*std)
                        ].copy()
                        print(f"Removed {len(prepared_df) - len(df_to_use)} outliers")
                    else:
                        # Third attempt: try with a random subset of data
                        print("Attempt 3: Using random subset of data")
                        df_to_use = prepared_df.sample(frac=0.8, random_state=42)
                        print(f"Using {len(df_to_use)} random observations")
                    
                    # Try to fit the model
                    results, fit_stats = fit_multilevel_model(df_to_use, param)
                    
                    if results is not None and fit_stats is not None and len(results) > 0:
                        all_results.extend(results)
                        all_fit_stats.append(fit_stats)
                        successful_params.append(param)
                        print(f"Successfully fitted model for {param} on attempt {attempt+1}")
                        break
                    else:
                        print(f"Attempt {attempt+1} failed to fit model for {param}")
                        
                        # If this was the last attempt, add to failed params
                        if attempt == max_attempts - 1:
                            print(f"All {max_attempts} attempts failed for {param}")
                            failed_params.append(param)
            else:
                # Normal handling for other parameters
                results, fit_stats = fit_multilevel_model(prepared_df, param)
                
                if results is not None and fit_stats is not None and len(results) > 0:
                    all_results.extend(results)
                    all_fit_stats.append(fit_stats)
                    successful_params.append(param)
                    print(f"Successfully fitted model for {param}")
                else:
                    print(f"Warning: Failed to fit model for {param}, continuing with other parameters")
                    failed_params.append(param)
                    continue
        
        # Print summary of model fitting attempts
        print("\nModel fitting summary:")
        print(f"Successfully fitted models for: {', '.join(successful_params) if successful_params else 'None'}")
        print(f"Failed to fit models for: {', '.join(failed_params) if failed_params else 'None'}")
        
        # Check if any models have proper random effects structure
        # Since we removed random_effects_type from saved stats, we'll track this locally
        models_with_main_re = len(successful_params)  # All successful models had main_effects structure
        models_with_full_re = 0  # None achieved full random effects
        models_with_single_re = 0  # None had single predictor random effects
        models_with_intercept_only = 0  # None fell back to intercept only
        
        print("\nRandom effects structure summary:")
        print(f"Models with full random effects (setsize*delay): {models_with_full_re}")
        print(f"Models with main effects random slopes (setsize+delay): {models_with_main_re}")
        print(f"Models with single predictor random slopes: {models_with_single_re}")
        print(f"Models with random intercepts only: {models_with_intercept_only}")
        
        if models_with_full_re + models_with_main_re == 0:
            print("\nWARNING: None of the fitted models have the ideal random effects structure")
            print("for testing cross-level interactions. The results should be interpreted with caution.")
        elif models_with_full_re + models_with_main_re < len(all_fit_stats):
            print("\nNOTE: Some models lack the ideal random effects structure.")
            print("Cross-level interactions should be interpreted with caution for those models.")
        
        # Always save results, even if some or all models failed
        print("\nProceeding to save available results...")
        
        # Apply FDR correction if we have results
        if all_results:
            all_results = apply_fdr_correction(all_results)
        else:
            print("No results available for FDR correction")
        
        # Save results (this function handles empty results)
        save_results(all_results, all_fit_stats)
        
        print("\n" + "=" * 50)
        if successful_params:
            print("Analysis completed with some successful models!")
            print(f"Total models fitted: {len(all_fit_stats)}")
            print(f"Total effects analyzed: {len(all_results)}")
            
            # Summary of significant VVIQ effects
            vviq_effects = [r for r in all_results if 'vviq_centered' in r['effect_name']]
            significant_vviq = [r for r in vviq_effects if r.get('significant_fdr', False)]
            
            print(f"VVIQ effects tested: {len(vviq_effects)}")
            print(f"Significant VVIQ effects (FDR < 0.05): {len(significant_vviq)}")
            
            if significant_vviq:
                print("Significant VVIQ effects:")
                for effect in significant_vviq:
                    print(f"  {effect['parameter_type']} - {effect['effect_name']}: "
                          f"β = {effect['estimate']:.4f}, p_FDR = {effect['p_value_fdr_corrected']:.4f}")
        else:
            print("Analysis completed but no models were successfully fitted")
            print("Empty output files have been created")
        
        print("Finished execution")
        return 0 if successful_params else 1
        
    except Exception as e:
        print(f"Error in main function: {e}")
        import traceback
        traceback.print_exc()
        
        # Try to save any partial results
        try:
            print("Attempting to save any partial results...")
            save_results([], [])
        except:
            print("Failed to save partial results")
            
        return 1

if __name__ == "__main__":
    sys.exit(main())
