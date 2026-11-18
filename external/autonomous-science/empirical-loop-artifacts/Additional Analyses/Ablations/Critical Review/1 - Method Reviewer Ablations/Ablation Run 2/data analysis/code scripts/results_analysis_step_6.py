import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

# Import R interface
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr

    # Create converter for context manager usage
    converter = pandas2ri.converter

    # Import R packages with installation fallback
    base = importr('base')
    stats = importr('stats')
    utils = importr('utils')

    # Try to import required packages, install if missing
    try:
        lme4 = importr('lme4')
        lmerTest = importr('lmerTest')
        MuMIn = importr('MuMIn')
        print("Successfully imported R packages")
    except Exception as e:
        print(f"Installing missing R packages: {e}")
        utils.install_packages(['lme4', 'lmerTest', 'MuMIn'], repos='https://cloud.r-project.org/')
        lme4 = importr('lme4')
        lmerTest = importr('lmerTest')
        MuMIn = importr('MuMIn')
        print("Successfully installed and imported R packages")

except ImportError as e:
    print(f"Error importing rpy2 or R packages: {e}")
    sys.exit(1)

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
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    print(f"Found most recent file matching pattern '{pattern}': {most_recent}")
    return most_recent

def load_and_validate_data():
    """
    Load and validate input data files.
    
    Returns:
    tuple: (mrt_data, mixture_data) DataFrames or (None, None) if error
    """
    print("Starting data loading and validation...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Find MRT cleaned data file
    mrt_pattern = 'outputs/VWM_MRT_cleaned_data_*.csv'
    mrt_file = find_most_recent_file(mrt_pattern)
    if not mrt_file:
        print(f"Error: No MRT cleaned data file found matching pattern: {mrt_pattern}")
        return None, None
    
    # Find mixture model parameters file
    mixture_pattern = 'outputs/VWM_mixture_model_parameters_*.csv'
    mixture_file = find_most_recent_file(mixture_pattern)
    if not mixture_file:
        print(f"Error: No mixture model parameters file found matching pattern: {mixture_pattern}")
        return None, None
    
    # Load MRT data
    print(f"Loading MRT data from: {mrt_file}")
    try:
        mrt_data = pd.read_csv(mrt_file)
        print("MRT data loaded successfully")
        print("MRT data columns:", list(mrt_data.columns))
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        print(f"MRT data shape: {mrt_data.shape}")
    except Exception as e:
        print(f"Error loading MRT data: {e}")
        return None, None
    
    # Load mixture model data
    print(f"Loading mixture model data from: {mixture_file}")
    try:
        mixture_data = pd.read_csv(mixture_file)
        print("Mixture model data loaded successfully")
        print("Mixture model data columns:", list(mixture_data.columns))
        print("First 3 rows of mixture model data:")
        print(mixture_data.head(3))
        print(f"Mixture model data shape: {mixture_data.shape}")
    except Exception as e:
        print(f"Error loading mixture model data: {e}")
        return None, None
    
    # Validate required columns for MRT data
    required_mrt_cols = ['participantId', 'isPractice', 'MRT_trial', 'MRT_angle_degrees', 
                        'MRT_isCorrect', 'MRT_rt_ms', 'MRT_block', 'excluded_from_MRT', 'trial_excluded']
    missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
    if missing_mrt_cols:
        print(f"Error: Missing required MRT columns: {missing_mrt_cols}")
        return None, None
    
    # Validate required columns for mixture data
    required_mixture_cols = ['participantId', 'kappa_concentration', 'model_converged', 'fit_quality_flag']
    missing_mixture_cols = [col for col in required_mixture_cols if col not in mixture_data.columns]
    if missing_mixture_cols:
        print(f"Error: Missing required mixture model columns: {missing_mixture_cols}")
        return None, None
    
    print("All required columns present in both datasets")
    
    # Print unique values for key experimental design parameters
    print("\nUnique values in key experimental design columns:")
    print(f"isPractice unique values: {mrt_data['isPractice'].unique()}")
    print(f"MRT_block unique values: {mrt_data['MRT_block'].unique()}")
    print(f"MRT_angle_degrees unique values: {mrt_data['MRT_angle_degrees'].unique()}")
    print(f"excluded_from_MRT unique values: {mrt_data['excluded_from_MRT'].unique()}")
    print(f"trial_excluded unique values: {mrt_data['trial_excluded'].unique()}")
    print(f"model_converged unique values: {mixture_data['model_converged'].unique()}")
    
    # Print data types for measured variables
    print(f"\nData types for measured variables:")
    print(f"MRT_isCorrect type: {mrt_data['MRT_isCorrect'].dtype}")
    print(f"MRT_rt_ms type: {mrt_data['MRT_rt_ms'].dtype}")
    print(f"kappa_concentration type: {mixture_data['kappa_concentration'].dtype}")
    
    return mrt_data, mixture_data

def prepare_trial_level_dataset(mrt_data, mixture_data):
    """
    Prepare trial-level dataset for mixed-effects modeling.
    
    Parameters:
    mrt_data (pd.DataFrame): MRT cleaned data
    mixture_data (pd.DataFrame): Mixture model parameters
    
    Returns:
    pd.DataFrame: Prepared dataset for modeling
    """
    print("\nPreparing trial-level dataset for mixed-effects modeling...")
    
    # Filter for test trials
    print(f"Initial MRT data shape: {mrt_data.shape}")
    
    # Filter for non-practice trials and test blocks, handling potential NaNs
    test_data = mrt_data[
        (mrt_data['isPractice'].fillna(True) == False) & 
        (mrt_data['MRT_block'].notna()) &
        (mrt_data['MRT_block'] != 'practice')
    ].copy()
    print(f"After filtering for test trials (isPractice=False and MRT_block != 'practice'): {test_data.shape}")
    
    # Apply exclusion filters
    # First exclude participants with excluded_from_MRT=True
    test_data = test_data[test_data['excluded_from_MRT'] == False]
    print(f"After excluding participants with excluded_from_MRT=True: {test_data.shape}")
    
    # Then exclude trials with trial_excluded=True
    test_data = test_data[test_data['trial_excluded'] == False]
    print(f"After excluding trials with trial_excluded=True: {test_data.shape}")
    
    print(f"Remaining unique participants: {test_data['participantId'].nunique()}")
    
    # Filter mixture model data for converged models
    print(f"Initial mixture model data shape: {mixture_data.shape}")
    converged_mixture = mixture_data[
        (mixture_data['model_converged'] == True) & 
        (mixture_data['kappa_concentration'].notna())
    ].copy()
    print(f"After filtering for converged models with valid kappa: {converged_mixture.shape}")
    print(f"Converged participants: {converged_mixture['participantId'].nunique()}")
    
    # Merge datasets
    print("\nMerging MRT and mixture model data...")
    merged_data = test_data.merge(converged_mixture, on='participantId', how='inner')
    print(f"Merged dataset shape: {merged_data.shape}")
    print(f"Final unique participants: {merged_data['participantId'].nunique()}")
    
    # Create categorical rotation angle variable with string categories for rpy2 compatibility
    print("\nCreating categorical rotation angle variable...")
    merged_data['MRT_angle_factor'] = pd.Categorical(
        merged_data['MRT_angle_degrees'].astype(int).astype(str), 
        categories=['0', '50', '100', '150'], 
        ordered=False  # Change from True to False
    )

    # Ensure MRT_isCorrect is boolean type for proper operations
    merged_data['MRT_isCorrect'] = merged_data['MRT_isCorrect'].astype(bool)
    
    print("Unique values in MRT_angle_factor:", merged_data['MRT_angle_factor'].unique())
    print("MRT_angle_factor value counts:")
    print(merged_data['MRT_angle_factor'].value_counts())
    
    print("First 2 rows of prepared dataset:")
    print(merged_data[['participantId', 'MRT_angle_degrees', 'MRT_angle_factor', 
                      'MRT_isCorrect', 'MRT_rt_ms', 'kappa_concentration']].head(2))
    
    return merged_data

def run_accuracy_model(data):
    """
    Run generalized linear mixed-effects model for MRT accuracy.
    
    Parameters:
    data (pd.DataFrame): Prepared trial-level dataset
    
    Returns:
    dict: Model results and diagnostics
    """
    print("\nRunning Model 1: Generalized Linear Mixed-Effects Model for MRT Accuracy...")
    
    print(f"Model data shape: {data.shape}")
    true_count = data['MRT_isCorrect'].sum()
    false_count = len(data) - true_count
    print(f"Accuracy data - True: {true_count}, False: {false_count}")

    print("Setting up model formula and data preparation...")
    # Convert data to R format using context manager
    with converter.context():
        r_data = converter.py2rpy(data)
        robjects.globalenv['model_data'] = r_data

    # Set reference level for angle factor
    robjects.r('''
    model_data$MRT_angle_factor <- relevel(model_data$MRT_angle_factor, ref = "0")
    ''')

    print("Calling R model fitting function...")
    # Fit the model
    print("Fitting accuracy model...")
    try:
        robjects.r('''
        library(lme4)
        library(lmerTest)
        library(MuMIn)

        accuracy_model <- glmer(MRT_isCorrect ~ kappa_concentration * MRT_angle_factor + 
                               (1 | participantId), 
                               data = model_data, 
                               family = binomial(link = "logit"),
                               control = glmerControl(optimizer = "bobyqa"))
        ''')

        print("Accuracy model fitted successfully")

        print("Extracting model coefficients and summary statistics...")
        # Extract results with proper confidence interval handling
        robjects.r('''
        accuracy_summary <- summary(accuracy_model)
        accuracy_coefs <- accuracy_summary$coefficients
        accuracy_fixed_effects_names <- rownames(accuracy_coefs)

        # Model diagnostics
        accuracy_r2 <- r.squaredGLMM(accuracy_model)
        accuracy_aic <- AIC(accuracy_model)
        accuracy_bic <- BIC(accuracy_model)

        # Sample sizes
        accuracy_n_participants <- length(unique(model_data$participantId))
        accuracy_n_trials <- nrow(model_data)

        # Convergence status
        accuracy_convergence <- accuracy_model@optinfo$conv$opt
        ''')

        print("Computing model diagnostics (AIC, BIC, R²)...")
        # Try to get confidence intervals, with fallback
        try:
            robjects.r('''
            accuracy_confint <- confint(accuracy_model, parm = accuracy_fixed_effects_names, method = "Wald")
            ''')
            confint = np.array(robjects.r('accuracy_confint'))
            print("Confidence intervals calculated successfully")
        except Exception as ci_error:
            print(f"Warning: Confidence interval calculation failed: {ci_error}")
            print("Using fallback method: estimate ± 1.96*SE")
            coefs_temp = np.array(robjects.r('accuracy_coefs'))
            confint = np.column_stack([
                coefs_temp[:, 0] - 1.96 * coefs_temp[:, 1],
                coefs_temp[:, 0] + 1.96 * coefs_temp[:, 1]
            ])

        coefs = np.array(robjects.r('accuracy_coefs'))
        aic = float(robjects.r('accuracy_aic')[0])
        bic = float(robjects.r('accuracy_bic')[0])
        n_participants = int(robjects.r('accuracy_n_participants')[0])
        n_trials = int(robjects.r('accuracy_n_trials')[0])
        convergence = int(robjects.r('accuracy_convergence')[0])
        effect_names = list(robjects.r('accuracy_fixed_effects_names'))
        r2 = np.array(robjects.r('accuracy_r2'))
        r2_marginal = r2[0, 0]
        r2_conditional = r2[0, 1]

        # Check model convergence more thoroughly
        robjects.r('''
        accuracy_convergence_warnings <- accuracy_model@optinfo$conv$lme4$messages
        accuracy_singular <- isSingular(accuracy_model)
        ''')
        convergence_warnings = robjects.r('accuracy_convergence_warnings')
        is_singular = bool(robjects.r('accuracy_singular')[0])

        if convergence_warnings != robjects.NULL:
            print(f"Warning: Model convergence issues detected: {list(convergence_warnings)}")
        if is_singular:
            print("Warning: Model fit is singular (boundary/degenerate)")

        print(f"Accuracy model - AIC: {aic:.2f}, BIC: {bic:.2f}")
        print(f"Sample sizes - Participants: {n_participants}, Trials: {n_trials}")
        print(f"Convergence code: {convergence} (0 = converged)")
        print(f"R² marginal: {r2_marginal:.3f}, R² conditional: {r2_conditional:.3f}")

        print("Finalizing model results...")
        results = {
            'model_name': 'accuracy_model',
            'coefficients': coefs,
            'confint': confint,
            'effect_names': effect_names,
            'aic': aic,
            'bic': bic,
            'n_participants': n_participants,
            'n_trials': n_trials,
            'convergence': convergence,
            'r2_marginal': r2_marginal,
            'r2_conditional': r2_conditional
        }

        return results

    except Exception as e:
        print(f"Error fitting accuracy model: {e}")
        return None

def run_rt_model(data):
    """
    Run linear mixed-effects model for MRT reaction time.
    
    Parameters:
    data (pd.DataFrame): Prepared trial-level dataset
    
    Returns:
    dict: Model results and diagnostics
    """
    print("\nRunning Model 2: Linear Mixed-Effects Model for MRT Reaction Time...")
    
    # Filter for correct trials only
    correct_data = data[data['MRT_isCorrect'] == True].copy()
    print(f"Filtering for correct trials only: {correct_data.shape}")
    print(f"Participants in RT model: {correct_data['participantId'].nunique()}")

    print("Setting up model formula and data preparation...")
    # Log-transform reaction time
    correct_data['log_rt'] = np.log(correct_data['MRT_rt_ms'])
    print(f"Log RT - Mean: {correct_data['log_rt'].mean():.3f}, SD: {correct_data['log_rt'].std():.3f}")

    # Convert data to R format using context manager
    with converter.context():
        r_data = converter.py2rpy(correct_data)
        robjects.globalenv['rt_model_data'] = r_data

    # Set reference level for angle factor
    robjects.r('''
    rt_model_data$MRT_angle_factor <- relevel(rt_model_data$MRT_angle_factor, ref = "0")
    ''')

    print("Calling R model fitting function...")
    # Fit the model
    print("Fitting RT model...")
    try:
        robjects.r('''
        library(lme4)
        library(lmerTest)
        library(MuMIn)

        rt_model <- lmer(log_rt ~ kappa_concentration * MRT_angle_factor + 
                        (1 | participantId), 
                        data = rt_model_data,
                        control = lmerControl(optimizer = "bobyqa"))
        ''')

        print("RT model fitted successfully")

        print("Extracting model coefficients and summary statistics...")
        # Extract results with proper confidence interval handling
        robjects.r('''
        rt_summary <- summary(rt_model)
        rt_coefs <- rt_summary$coefficients
        rt_fixed_effects_names <- rownames(rt_coefs)

        # Model diagnostics
        rt_aic <- AIC(rt_model)
        rt_bic <- BIC(rt_model)
        rt_r2 <- r.squaredGLMM(rt_model)

        # Sample sizes
        rt_n_participants <- length(unique(rt_model_data$participantId))
        rt_n_trials <- nrow(rt_model_data)

        # Convergence status
        rt_convergence <- rt_model@optinfo$conv$lme4$code
        ''')

        print("Computing model diagnostics (AIC, BIC, R²)...")
        # Try to get confidence intervals, with fallback
        try:
            robjects.r('''
            rt_confint <- confint(rt_model, parm = rt_fixed_effects_names, method = "Wald")
            ''')
            confint = np.array(robjects.r('rt_confint'))
            print("Confidence intervals calculated successfully")
        except Exception as ci_error:
            print(f"Warning: Confidence interval calculation failed: {ci_error}")
            print("Using fallback method: estimate ± 1.96*SE")
            coefs_temp = np.array(robjects.r('rt_coefs'))
            confint = np.column_stack([
                coefs_temp[:, 0] - 1.96 * coefs_temp[:, 1],
                coefs_temp[:, 0] + 1.96 * coefs_temp[:, 1]
            ])

        coefs = np.array(robjects.r('rt_coefs'))
        aic = float(robjects.r('rt_aic')[0])
        bic = float(robjects.r('rt_bic')[0])
        r2 = np.array(robjects.r('rt_r2'))
        r2_marginal = r2[0, 0]
        r2_conditional = r2[0, 1]
        n_participants = int(robjects.r('rt_n_participants')[0])
        n_trials = int(robjects.r('rt_n_trials')[0])

        # Handle convergence status (might be NULL)
        try:
            convergence = int(robjects.r('rt_convergence')[0])
        except:
            convergence = 0  # Assume converged if no code

        # Check model convergence more thoroughly
        robjects.r('''
        rt_convergence_warnings <- rt_model@optinfo$conv$lme4$messages
        rt_singular <- isSingular(rt_model)
        ''')
        convergence_warnings = robjects.r('rt_convergence_warnings')
        is_singular = bool(robjects.r('rt_singular')[0])

        if convergence_warnings != robjects.NULL:
            print(f"Warning: RT model convergence issues detected: {list(convergence_warnings)}")
        if is_singular:
            print("Warning: RT model fit is singular (boundary/degenerate)")

        effect_names = list(robjects.r('rt_fixed_effects_names'))

        print(f"RT model - AIC: {aic:.2f}, BIC: {bic:.2f}")
        print(f"R² marginal: {r2_marginal:.3f}, R² conditional: {r2_conditional:.3f}")
        print(f"Sample sizes - Participants: {n_participants}, Trials: {n_trials}")
        print(f"Convergence code: {convergence} (0 = converged)")

        print("Finalizing model results...")
        results = {
            'model_name': 'rt_model',
            'coefficients': coefs,
            'confint': confint,
            'effect_names': effect_names,
            'aic': aic,
            'bic': bic,
            'r2_marginal': r2_marginal,
            'r2_conditional': r2_conditional,
            'n_participants': n_participants,
            'n_trials': n_trials,
            'convergence': convergence
        }

        return results

    except Exception as e:
        print(f"Error fitting RT model: {e}")
        return None

def format_and_save_results(accuracy_results, rt_results):
    """
    Format and save model results to CSV files.
    
    Parameters:
    accuracy_results (dict): Results from accuracy model
    rt_results (dict): Results from RT model
    """
    print("\nFormatting and saving results...")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare results dataframe
    results_data = []
    diagnostics_data = []
    
    # Process accuracy model results
    if accuracy_results:
        coefs = accuracy_results['coefficients']
        confint = accuracy_results['confint']
        effect_names = accuracy_results['effect_names']

        for i, effect in enumerate(effect_names):
            results_data.append({
                'model_name': 'accuracy_model',
                'effect_name': effect,
                'estimate': coefs[i, 0],
                'std_error': coefs[i, 1],
                'statistic': coefs[i, 2],  # z-value
                'p_value': coefs[i, 3],
                'ci_lower': confint[i, 0],
                'ci_upper': confint[i, 1],
                'df': np.nan  # Not applicable for GLMM
            })

        diagnostics_data.append({
            'model_name': 'accuracy_model',
            'n_participants': accuracy_results['n_participants'],
            'n_trials': accuracy_results['n_trials'],
            'AIC': accuracy_results['aic'],
            'BIC': accuracy_results['bic'],
            'R2_marginal': accuracy_results.get('r2_marginal', np.nan),
            'R2_conditional': accuracy_results.get('r2_conditional', np.nan),
            'convergence_status': 'converged' if accuracy_results['convergence'] == 0 else 'failed'
        })

    # Process RT model results
    if rt_results:
        coefs = rt_results['coefficients']
        confint = rt_results['confint']
        effect_names = rt_results['effect_names']

        for i, effect in enumerate(effect_names):
            results_data.append({
                'model_name': 'rt_model',
                'effect_name': effect,
                'estimate': coefs[i, 0],
                'std_error': coefs[i, 1],
                'statistic': coefs[i, 3],  # t-value is in the 4th column (index 3)
                'p_value': coefs[i, 4],    # p-value is in the 5th column (index 4)
                'ci_lower': confint[i, 0],
                'ci_upper': confint[i, 1],
                'df': coefs[i, 2]          # df is in the 3rd column (index 2)
            })

        diagnostics_data.append({
            'model_name': 'rt_model',
            'n_participants': rt_results['n_participants'],
            'n_trials': rt_results['n_trials'],
            'AIC': rt_results['aic'],
            'BIC': rt_results['bic'],
            'R2_marginal': rt_results['r2_marginal'],
            'R2_conditional': rt_results['r2_conditional'],
            'convergence_status': 'converged' if rt_results['convergence'] == 0 else 'failed'
        })
    
    # Save results
    results_df = pd.DataFrame(results_data)
    diagnostics_df = pd.DataFrame(diagnostics_data)
    
    results_file = f'outputs/MRT_mixed_effects_results_{timestamp}.csv'
    diagnostics_file = f'outputs/MRT_model_diagnostics_{timestamp}.csv'
    
    results_df.to_csv(results_file, index=False)
    diagnostics_df.to_csv(diagnostics_file, index=False)
    
    print(f"Results saved to: {results_file}")
    print(f"Diagnostics saved to: {diagnostics_file}")
    
    print("\nResults summary:")
    print(results_df)
    print("\nDiagnostics summary:")
    print(diagnostics_df)

def main():
    """
    Main function to execute the mixed-effects modeling analysis.
    """
    try:
        print("Starting MRT mixed-effects modeling analysis...")
        
        # Load and validate data
        mrt_data, mixture_data = load_and_validate_data()
        if mrt_data is None or mixture_data is None:
            print("Error: Failed to load required data files")
            return 1
        
        # Prepare trial-level dataset
        model_data = prepare_trial_level_dataset(mrt_data, mixture_data)
        if model_data.empty:
            print("Error: No data available for modeling after filtering")
            return 1
        
        # Run accuracy model
        accuracy_results = run_accuracy_model(model_data)
        if accuracy_results is None:
            print("Warning: Accuracy model failed to converge")
        
        # Run RT model
        rt_results = run_rt_model(model_data)
        if rt_results is None:
            print("Warning: RT model failed to converge")
        
        # Check if at least one model succeeded
        if accuracy_results is None and rt_results is None:
            print("Error: Both models failed to converge")
            return 1
        
        # Format and save results
        format_and_save_results(accuracy_results, rt_results)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Unexpected error in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
