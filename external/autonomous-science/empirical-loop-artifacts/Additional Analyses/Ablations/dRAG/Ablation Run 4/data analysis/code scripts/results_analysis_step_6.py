import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import R interface
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects import conversion

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
    
    # Get the most recent file based on creation time
    most_recent = max(files, key=os.path.getctime)
    return most_recent

def ensure_r_packages():
    """
    Ensure required R packages are installed.
    """
    print("Checking and installing required R packages...")
    try:
        utils = importr('utils')
        
        # Check and install lme4
        try:
            importr('lme4')
            print("lme4 package already available")
        except Exception as e:
            print(f"Installing lme4 package... (Error: {e})")
            utils.install_packages('lme4', repos='https://cloud.r-project.org/')
            print("lme4 package installed successfully")
        
        # Check and install lmerTest for p-values in linear models
        try:
            importr('lmerTest')
            print("lmerTest package already available")
        except Exception as e:
            print(f"Installing lmerTest package... (Error: {e})")
            utils.install_packages('lmerTest', repos='https://cloud.r-project.org/')
            print("lmerTest package installed successfully")
            
    except Exception as e:
        print(f"CRITICAL ERROR: Could not ensure R packages are installed: {e}")
        raise

def load_and_validate_data():
    """
    Load and validate input datasets.
    
    Returns:
    tuple: (mrt_data, vwm_data) DataFrames or (None, None) if validation fails
    """
    print("=== LOADING INPUT DATA ===")
    
    # Find MRT cleaned data file
    mrt_pattern = "outputs/MRT_cleaned_*.csv"
    mrt_file = find_most_recent_file(mrt_pattern)
    
    if mrt_file is None:
        print(f"ERROR: No MRT cleaned file found matching pattern: {mrt_pattern}")
        return None, None
    
    print(f"Found MRT file: {mrt_file}")
    
    # Find VWM parameters file
    vwm_pattern = "outputs/VWM_parameters_*.csv"
    vwm_file = find_most_recent_file(vwm_pattern)
    
    if vwm_file is None:
        print(f"ERROR: No VWM parameters file found matching pattern: {vwm_pattern}")
        return None, None
    
    print(f"Found VWM file: {vwm_file}")
    
    # Load MRT data
    try:
        mrt_data = pd.read_csv(mrt_file)
        print(f"\nMRT data loaded successfully. Shape: {mrt_data.shape}")
        print("MRT data columns:", list(mrt_data.columns))
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        # Validate required MRT columns
        required_mrt_cols = ['participantId', 'MRT_trial', 'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms', 'excluded']
        missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
        if missing_mrt_cols:
            print(f"ERROR: Missing required MRT columns: {missing_mrt_cols}")
            return None, None

        # Validate and standardize MRT_isCorrect data type
        print("Validating MRT_isCorrect data type...")
        if mrt_data['MRT_isCorrect'].dtype == 'object':
            # Handle string representations
            mrt_data['MRT_isCorrect'] = mrt_data['MRT_isCorrect'].map({
                'True': True, 'true': True, 'TRUE': True, '1': True, 1: True,
                'False': False, 'false': False, 'FALSE': False, '0': False, 0: False
            })
        elif mrt_data['MRT_isCorrect'].dtype in ['int64', 'int32']:
            # Convert 1/0 to True/False
            mrt_data['MRT_isCorrect'] = mrt_data['MRT_isCorrect'].astype(bool)

        print(f"MRT_isCorrect data type after validation: {mrt_data['MRT_isCorrect'].dtype}")
        
        # Print unique values for key experimental design columns
        print(f"\nUnique values in MRT_angle_degrees: {sorted(mrt_data['MRT_angle_degrees'].unique())}")
        print(f"Unique values in MRT_isCorrect: {sorted(mrt_data['MRT_isCorrect'].unique())}")
        print(f"Unique values in excluded: {sorted(mrt_data['excluded'].unique())}")
        print(f"Data type of MRT_rt_ms: {mrt_data['MRT_rt_ms'].dtype}")
        
    except Exception as e:
        print(f"ERROR loading MRT data: {e}")
        return None, None
    
    # Load VWM data
    try:
        vwm_data = pd.read_csv(vwm_file)
        print(f"\nVWM data loaded successfully. Shape: {vwm_data.shape}")
        print("VWM data columns:", list(vwm_data.columns))
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
        
        # Validate required VWM columns
        required_vwm_cols = ['participantId', 'kappa_concentration', 'excluded']
        missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
        if missing_vwm_cols:
            print(f"ERROR: Missing required VWM columns: {missing_vwm_cols}")
            return None, None
        
        # Print unique values for key experimental design columns
        print(f"\nUnique values in VWM excluded: {sorted(vwm_data['excluded'].unique())}")
        print(f"Data type of kappa_concentration: {vwm_data['kappa_concentration'].dtype}")
        
    except Exception as e:
        print(f"ERROR loading VWM data: {e}")
        return None, None
    
    return mrt_data, vwm_data

def prepare_data(mrt_data, vwm_data):
    """
    Prepare and merge datasets for analysis.
    
    Parameters:
    mrt_data (DataFrame): MRT cleaned data
    vwm_data (DataFrame): VWM parameters data
    
    Returns:
    tuple: (merged_data, correct_trials_data) or (None, None) if preparation fails
    """
    print("\n=== DATA PREPARATION ===")
    
    # Filter out excluded participants from both datasets
    print(f"Original MRT data shape: {mrt_data.shape}")
    mrt_included = mrt_data[mrt_data['excluded'] == False].copy()
    print(f"MRT data after exclusion filtering: {mrt_included.shape}")
    print(f"Excluded {mrt_data.shape[0] - mrt_included.shape[0]} MRT trials")
    
    print(f"Original VWM data shape: {vwm_data.shape}")
    vwm_included = vwm_data[vwm_data['excluded'] == False].copy()
    print(f"VWM data after exclusion filtering: {vwm_included.shape}")
    print(f"Excluded {vwm_data.shape[0] - vwm_included.shape[0]} VWM participants")
    
    # Merge datasets
    print("\nMerging datasets...")
    merged_data = pd.merge(mrt_included, vwm_included[['participantId', 'kappa_concentration']], 
                          on='participantId', how='inner')
    
    print(f"Merged data shape: {merged_data.shape}")
    print(f"Number of unique participants in merged data: {merged_data['participantId'].nunique()}")
    
    if merged_data.empty:
        print("ERROR: No participants found in both datasets after merging")
        return None, None
    
    # Print unique levels for MRT_angle_degrees
    print("\nChecking MRT_angle_degrees levels...")
    print(f"MRT_angle_degrees levels: {sorted(merged_data['MRT_angle_degrees'].unique())}")
    
    # Filter to correct trials only for RT analysis
    print("\nPreparing correct trials data for RT analysis...")
    correct_trials = merged_data[merged_data['MRT_isCorrect'] == True].copy()
    print(f"Correct trials shape: {correct_trials.shape}")
    print(f"Proportion of correct trials: {len(correct_trials) / len(merged_data):.3f}")
    
    # Log-transform reaction times for correct trials
    correct_trials['log_rt'] = np.log(correct_trials['MRT_rt_ms'])
    print(f"Log RT statistics:")
    print(f"  Mean: {correct_trials['log_rt'].mean():.3f}")
    print(f"  SD: {correct_trials['log_rt'].std():.3f}")
    print(f"  Range: {correct_trials['log_rt'].min():.3f} to {correct_trials['log_rt'].max():.3f}")
    
    print("\nFirst 2 rows of merged data:")
    print("Columns:", list(merged_data.columns))
    print(merged_data.head(2))
    
    print("\nFirst 2 rows of correct trials data:")
    print("Columns:", list(correct_trials.columns))
    print(correct_trials.head(2))
    
    return merged_data, correct_trials

def fit_mixed_effects_models(merged_data, correct_trials):
    """
    Fit mixed-effects models using R through rpy2.
    
    Parameters:
    merged_data (DataFrame): Complete merged dataset
    correct_trials (DataFrame): Correct trials only with log RT
    
    Returns:
    tuple: (accuracy_results, rt_results, random_effects_results) or (None, None, None) if fitting fails
    """
    print("\n=== FITTING MIXED-EFFECTS MODELS ===")
    
    try:
        # Import required R packages
        print("Loading R packages...")
        try:
            lme4 = importr('lme4')
            lmertest = importr('lmerTest')  # For p-values in linear models
            base = importr('base')
            stats = importr('stats')
            print("All R packages loaded successfully")
        except Exception as e:
            print(f"CRITICAL ERROR loading R packages: {e}")
            print("Make sure lme4 and lmerTest are properly installed")
            raise
        
        # Convert data to R format and assign to R environment
        print("Converting data to R format and assigning to R environment...")
        try:
            with conversion.localconverter(ro.default_converter + pandas2ri.converter):
                ro.globalenv['merged_data'] = merged_data
                ro.globalenv['correct_data'] = correct_trials

                # Validate data transfer
                r_merged_dims = ro.r('dim(merged_data)')
                r_correct_dims = ro.r('dim(correct_data)')
                print(f"R merged data dimensions: {r_merged_dims}")
                print(f"R correct trials dimensions: {r_correct_dims}")

                if r_merged_dims[0] == 0 or r_correct_dims[0] == 0:
                    raise ValueError("Data transfer to R failed - empty datasets")

        except Exception as e:
            print(f"ERROR during data conversion to R: {e}")
            raise
        
        # Model 1: Logistic regression for accuracy
        print("\n--- Fitting Model 1: Logistic regression for MRT accuracy ---")
        
        accuracy_formula = "MRT_isCorrect ~ kappa_concentration * factor(MRT_angle_degrees) + (1 + factor(MRT_angle_degrees) | participantId)"
        print(f"Accuracy model formula: {accuracy_formula}")
        
        try:
            print("Starting accuracy model fitting...")
            ro.r(f'''
            accuracy_model <- glmer({accuracy_formula}, 
                                  data = merged_data,
                                  family = binomial(link = "logit"),
                                  control = glmerControl(optimizer = "bobyqa"))
            ''')
            
            print("Accuracy model fitted successfully!")
            
            # Check convergence
            convergence_check = ro.r('accuracy_model@optinfo$conv$lme4$messages')
            if convergence_check != ro.NULL:
                print(f"Accuracy model convergence warnings: {convergence_check}")
            else:
                print("Accuracy model converged without warnings")
            
            # Extract results
            accuracy_summary = ro.r('summary(accuracy_model)')
            print("Accuracy model summary extracted")
            
        except Exception as e:
            print(f"ERROR fitting accuracy model: {e}")
            return None, None, None
        
        # Model 2: Linear regression for log RT
        print("\n--- Fitting Model 2: Linear regression for log RT ---")
        
        rt_formula = "log_rt ~ kappa_concentration * factor(MRT_angle_degrees) + (1 + factor(MRT_angle_degrees) | participantId)"
        print(f"RT model formula: {rt_formula}")
        
        try:
            print("Starting RT model fitting...")
            ro.r(f'''
            rt_model <- lmer({rt_formula}, 
                            data = correct_data,
                            control = lmerControl(optimizer = "bobyqa"))
            ''')
            
            print("RT model fitted successfully!")
            
            # Check convergence
            convergence_check = ro.r('rt_model@optinfo$conv$lme4$messages')
            if convergence_check != ro.NULL:
                print(f"RT model convergence warnings: {convergence_check}")
            else:
                print("RT model converged without warnings")
            
            # Extract results
            rt_summary = ro.r('summary(rt_model)')
            print("RT model summary extracted")
            
        except Exception as e:
            print(f"ERROR fitting RT model: {e}")
            return None, None, None
        
        # Run model diagnostics
        run_model_diagnostics()
        
        # Extract and print random effects variance components
        random_effects_results = extract_random_effects()
        
        # Extract detailed results for both models
        print("\n--- Extracting model results ---")
        
        # Extract accuracy model results
        accuracy_results = extract_model_results(model_name='accuracy_model', model_type='logistic')
        
        # Extract RT model results
        rt_results = extract_model_results(model_name='rt_model', model_type='linear')
        
        return accuracy_results, rt_results, random_effects_results
        
    except Exception as e:
        print(f"ERROR in mixed-effects modeling: {e}")
        return None, None, None

def extract_model_results(model_name, model_type):
    """
    Extract detailed results from fitted R models using robust column-based indexing.
    
    Parameters:
    model_name (str): Name of the R model object
    model_type (str): Type of model ('logistic' or 'linear')
    
    Returns:
    tuple: (effects_df, fit_df) containing model results
    """
    print(f"\nExtracting results for {model_name} ({model_type} model)...")
    
    try:
        # Validate model exists in R environment
        model_exists = ro.r(f'exists("{model_name}")')
        if not model_exists[0]:
            print(f"ERROR: Model {model_name} does not exist in R environment")
            return None, None

        try:
            # Extract coefficient table as DataFrame for robust indexing
            print("Extracting coefficient table...")
            ro.r(f'''
coef_summary <- summary({model_name})$coefficients
coef_df <- as.data.frame(coef_summary)
coef_df$effect_name <- rownames(coef_df)
''')

            # Convert to pandas DataFrame
            with conversion.localconverter(ro.default_converter + pandas2ri.converter):
                coef_df = ro.r('coef_df')

            print(f"Coefficient table columns: {list(coef_df.columns)}")
            print(f"Coefficient table shape: {coef_df.shape}")

            # Create effects dataframe with robust column access
            effects_list = []

            for idx, row in coef_df.iterrows():
                effect_name = row['effect_name']
                coefficient = row['Estimate']
                std_error = row['Std. Error']

                if model_type == 'logistic':
                    t_z_value = row['z value']
                    p_value = row['Pr(>|z|)']
                    df_value = np.nan
                else:
                    # For linear with lmerTest: extract df when available
                    df_value = row['df'] if 'df' in row else np.nan
                    t_z_value = row['t value']
                    p_value = row['Pr(>|t|)']

                # Calculate confidence intervals
                ci_lower = coefficient - 1.96 * std_error
                ci_upper = coefficient + 1.96 * std_error

                effects_list.append({
                    'model_type': model_type,
                    'effect_name': str(effect_name),
                    'coefficient': float(coefficient),
                    'standard_error': float(std_error),
                    't_value': float(t_z_value),
                    'p_value': float(p_value) if not np.isnan(p_value) else np.nan,
                    'ci_lower': float(ci_lower),
                    'ci_upper': float(ci_upper),
                    'df': float(df_value) if not pd.isnull(df_value) else np.nan,
                    'significance': 'yes' if not np.isnan(p_value) and p_value < 0.05 else 'no'
                })

            effects_df = pd.DataFrame(effects_list)
            print(f"Successfully extracted {len(effects_df)} effects")

        except Exception as e:
            print(f"CRITICAL ERROR extracting fixed effects for {model_name}: {e}")
            print(f"Error details: {type(e).__name__}")
            return None, None
        
        try:
            # Extract model fit statistics with detailed error handling
            print("Extracting model fit statistics...")
            
            try:
                aic = float(ro.r(f'AIC({model_name})')[0])
            except Exception as e:
                print(f"Warning: Could not extract AIC: {e}")
                aic = np.nan
                
            try:
                bic = float(ro.r(f'BIC({model_name})')[0])
            except Exception as e:
                print(f"Warning: Could not extract BIC: {e}")
                bic = np.nan
                
            try:
                loglik = float(ro.r(f'logLik({model_name})')[0])
            except Exception as e:
                print(f"Warning: Could not extract log-likelihood: {e}")
                loglik = np.nan
            
            try:
                n_obs = int(ro.r(f'nobs({model_name})')[0])
            except Exception as e:
                print(f"Warning: Could not extract n_obs: {e}")
                n_obs = np.nan
                
            try:
                n_participants = int(ro.r(f'length(unique({model_name}@frame$participantId))')[0])
            except Exception as e:
                print(f"Warning: Could not extract n_participants: {e}")
                n_participants = np.nan
            
            # Check convergence with detailed error handling
            converged = True
            try:
                conv_check = ro.r(f'{model_name}@optinfo$conv$lme4$messages')
                if conv_check != ro.NULL:
                    converged = False
                    print(f"Model convergence issues detected: {conv_check}")
            except Exception as e:
                print(f"Warning: Could not check convergence for {model_name}: {e}")
            
            fit_df = pd.DataFrame([{
                'model_type': model_type,
                'aic': aic,
                'bic': bic,
                'log_likelihood': loglik,
                'n_participants': n_participants,
                'n_observations': n_obs,
                'converged': converged
            }])
            
        except Exception as e:
            print(f"CRITICAL ERROR extracting fit statistics for {model_name}: {e}")
            return None, None
        
        print(f"Results extracted successfully for {model_type} model")
        print(f"Number of effects: {len(effects_df)}")
        if not np.isnan(aic):
            print(f"Model fit - AIC: {aic:.2f}, BIC: {bic:.2f}")
        
        return effects_df, fit_df
        
    except Exception as e:
        print(f"CRITICAL ERROR extracting results for {model_name}: {e}")
        print(f"Error type: {type(e).__name__}")
        return None, None

def extract_random_effects():
    """
    Extract and print random effect variance components from fitted models as a combined DataFrame.
    Returns:
    DataFrame: Combined random effects variance components for both models.
    """
    print("\n=== EXTRACTING RANDOM EFFECTS VARIANCE COMPONENTS ===")
    try:
        # Extract random effects for accuracy model
        print("Extracting random effects for accuracy model...")
        accuracy_varcomp_df = None
        try:
            ro.r('''
            accuracy_varcomp <- VarCorr(accuracy_model)
            accuracy_varcomp_df <- as.data.frame(accuracy_varcomp)
            accuracy_varcomp_df$is_variance <- is.na(accuracy_varcomp_df$var2)
            ''')
            with conversion.localconverter(ro.default_converter + pandas2ri.converter):
                accuracy_varcomp_df = ro.r('accuracy_varcomp_df')
            print(f"Accuracy model VarCorr columns: {list(accuracy_varcomp_df.columns)}")
            print(f"Accuracy model VarCorr shape: {accuracy_varcomp_df.shape}")
            print("Accuracy model variance components:")
            print(accuracy_varcomp_df.to_string(index=False))
        except Exception as e:
            print(f"ERROR extracting accuracy model random effects: {e}")
            accuracy_varcomp_df = pd.DataFrame()

        # Extract random effects for RT model
        print("\nExtracting random effects for RT model...")
        rt_varcomp_df = None
        try:
            ro.r('''
            rt_varcomp <- VarCorr(rt_model)
            rt_varcomp_df <- as.data.frame(rt_varcomp)
            rt_varcomp_df$is_variance <- is.na(rt_varcomp_df$var2)
            ''')
            with conversion.localconverter(ro.default_converter + pandas2ri.converter):
                rt_varcomp_df = ro.r('rt_varcomp_df')
            print(f"RT model VarCorr columns: {list(rt_varcomp_df.columns)}")
            print(f"RT model VarCorr shape: {rt_varcomp_df.shape}")
            print("RT model variance components:")
            print(rt_varcomp_df.to_string(index=False))
        except Exception as e:
            print(f"ERROR extracting RT model random effects: {e}")
            rt_varcomp_df = pd.DataFrame()

        # Helper to process and filter variance components
        def process_varcomp(df, model_type):
            if df is None or df.empty:
                return pd.DataFrame()
            # Filter for variance components only using is_variance column
            filtered = df[df['is_variance'] == True].copy()
            # Handle 'Residual' effect name for residual variance rows
            filtered['effect_name'] = np.where(filtered['grp'] == 'Residual', 'Residual', filtered['var1'])
            filtered['group'] = filtered['grp']
            filtered['variance'] = filtered['vcov']
            filtered['std_dev'] = filtered['sdcor']
            filtered['model_type'] = model_type
            return filtered[['model_type', 'group', 'effect_name', 'variance', 'std_dev']]

        acc_df = process_varcomp(accuracy_varcomp_df, 'logistic')
        rt_df = process_varcomp(rt_varcomp_df, 'linear')

        combined = pd.concat([acc_df, rt_df], ignore_index=True)
        print("\nCombined random effects variance components:")
        print(combined.to_string(index=False))
        return combined

    except Exception as e:
        print(f"CRITICAL ERROR extracting random effects: {e}")
        return None

def run_model_diagnostics():
    """
    Run model diagnostics including residual plots and random effects testing.
    """
    print("\n=== RUNNING MODEL DIAGNOSTICS ===")
    
    try:
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate residual plots for RT model
        print("Generating residual plots for RT model...")
        try:
            ro.r(f'''
            png("outputs/rt_model_residuals_{timestamp}.png", width=800, height=600)
            par(mfrow=c(2,2))
            plot(rt_model)
            dev.off()
            cat("Residual plots saved to outputs/rt_model_residuals_{timestamp}.png\\n")
            ''')
            print(f"Residual plots saved successfully to outputs/rt_model_residuals_{timestamp}.png")
        except Exception as e:
            print(f"Warning: Could not generate residual plots: {e}")
        
        # Test random effects significance using likelihood ratio tests
        print("\nTesting random effects significance...")
        try:
            print("Fitting reduced models and performing likelihood ratio tests...")
            ro.r('''
            # Fit reduced accuracy model (intercept-only random effects)
            accuracy_reduced <- glmer(MRT_isCorrect ~ kappa_concentration * factor(MRT_angle_degrees) + (1 | participantId), 
                                     data = merged_data, 
                                     family = binomial(link = "logit"),
                                     control = glmerControl(optimizer = "bobyqa"))
            
            # Fit reduced RT model (intercept-only random effects)
            rt_reduced <- lmer(log_rt ~ kappa_concentration * factor(MRT_angle_degrees) + (1 | participantId), 
                              data = correct_data,
                              control = lmerControl(optimizer = "bobyqa"))
            
            # Perform likelihood ratio tests
            cat("\\n=== ACCURACY MODEL RANDOM SLOPES TEST ===\\n")
            accuracy_lrt <- anova(accuracy_reduced, accuracy_model)
            print(accuracy_lrt)
            
            cat("\\n=== RT MODEL RANDOM SLOPES TEST ===\\n")
            rt_lrt <- anova(rt_reduced, rt_model)
            print(rt_lrt)
            ''')
            print("Random effects significance testing completed successfully")
        except Exception as e:
            print(f"Warning: Could not complete random effects testing: {e}")
            
    except Exception as e:
        print(f"ERROR in model diagnostics: {e}")

def save_results(accuracy_results, rt_results, random_effects_results):
    """
    Save model results to CSV files.
    
    Parameters:
    accuracy_results (tuple): (effects_df, fit_df) for accuracy model
    rt_results (tuple): (effects_df, fit_df) for RT model
    random_effects_results (DataFrame): Random effects variance components
    
    Returns:
    bool: True if successful, False otherwise
    """
    print("\n=== SAVING RESULTS ===")
    
    try:
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Combine effects results
        if accuracy_results[0] is not None and rt_results[0] is not None:
            all_effects = pd.concat([accuracy_results[0], rt_results[0]], ignore_index=True)
            
            effects_filename = f"outputs/MRT_VWM_mixed_effects_{timestamp}.csv"
            all_effects.to_csv(effects_filename, index=False)
            print(f"Mixed effects results saved to: {effects_filename}")
            print("Effects results columns:", list(all_effects.columns))
            print("First 2 rows of effects results:")
            print(all_effects.head(2))
        
        # Combine fit results
        if accuracy_results[1] is not None and rt_results[1] is not None:
            all_fit = pd.concat([accuracy_results[1], rt_results[1]], ignore_index=True)
            
            fit_filename = f"outputs/MRT_VWM_model_fit_{timestamp}.csv"
            all_fit.to_csv(fit_filename, index=False)
            print(f"Model fit results saved to: {fit_filename}")
            print("Fit results columns:", list(all_fit.columns))
            print("First 2 rows of fit results:")
            print(all_fit.head(2))
        
        # Save random effects variance components
        if random_effects_results is not None and not random_effects_results.empty:
            random_effects_filename = f"outputs/MRT_VWM_random_effects_{timestamp}.csv"
            random_effects_results.to_csv(random_effects_filename, index=False)
            print(f"Random effects variance components saved to: {random_effects_filename}")
            print("Random effects columns:", list(random_effects_results.columns))
            print("First 2 rows of random effects results:")
            print(random_effects_results.head(2))
        
        return True
        
    except Exception as e:
        print(f"ERROR saving results: {e}")
        return False

def main():
    """
    Main function to execute the mixed-effects analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for failure
    """
    try:
        print("Starting MRT-VWM mixed-effects analysis...")
        
        # Ensure R packages are available
        ensure_r_packages()
        
        # Load and validate data
        mrt_data, vwm_data = load_and_validate_data()
        if mrt_data is None or vwm_data is None:
            return 1
        
        # Prepare data for analysis
        merged_data, correct_trials = prepare_data(mrt_data, vwm_data)
        if merged_data is None or correct_trials is None:
            return 1
        
        # Fit mixed-effects models
        accuracy_results, rt_results, random_effects_results = fit_mixed_effects_models(merged_data, correct_trials)
        if accuracy_results is None or rt_results is None or random_effects_results is None:
            return 1
        
        # Save results
        if not save_results(accuracy_results, rt_results, random_effects_results):
            return 1
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"CRITICAL ERROR in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
