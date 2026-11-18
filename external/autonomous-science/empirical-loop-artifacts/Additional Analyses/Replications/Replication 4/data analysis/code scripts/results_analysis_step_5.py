import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import R packages via rpy2
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, numpy2ri
from rpy2.robjects.packages import importr

def install_r_packages_if_needed():
    """Install required R packages if they are not already available."""
    print("Checking and installing required R packages...")
    try:
        utils = importr('utils')
        base = importr('base')
        
        required_packages = ['lme4', 'broom.mixed', 'car', 'performance']
        
        for package in required_packages:
            try:
                importr(package)
                print(f"Package {package} already installed")
            except:
                print(f"Installing R package: {package}")
                utils.install_packages(package, repos='https://cloud.r-project.org/')
                print(f"Successfully installed {package}")
    except Exception as e:
        print(f"Warning: Could not install R packages: {e}")
        print("Proceeding with available packages...")

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    # Get the most recent file based on modification time
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found latest file for pattern {pattern}: {latest_file}")
    return latest_file

def load_and_validate_data():
    """
    Load and validate all required input files.
    
    Returns:
    tuple: Four dataframes (vonmises_params, mrt_data, vwm_data, participant_data)
    """
    print("Loading input files...")
    
    # Find latest files for each input
    vonmises_file = find_latest_file("outputs/vonmises_parameters_overall_*.csv")
    mrt_file = find_latest_file("outputs/cleaned_mrt_data_*.csv")
    vwm_file = find_latest_file("outputs/cleaned_vwm_data_*.csv")
    participant_file = find_latest_file("outputs/cleaned_participant_data_*.csv")
    
    # Load von Mises parameters
    print(f"\nLoading von Mises parameters from: {vonmises_file}")
    vonmises_params = pd.read_csv(vonmises_file)
    vonmises_params.columns = vonmises_params.columns.str.strip()
    print("Von Mises parameters columns:", list(vonmises_params.columns))
    print("First 3 rows of von Mises parameters:")
    print(vonmises_params.head(3))
    
    required_vonmises_cols = ['participantId', 'kappa_overall', 'kappa_se_overall', 'poor_fit_flag']
    missing_vonmises_cols = [col for col in required_vonmises_cols if col not in vonmises_params.columns]
    if missing_vonmises_cols:
        raise ValueError(f"Missing required columns in von Mises file: {missing_vonmises_cols}")
    
    # Load MRT data
    print(f"\nLoading MRT data from: {mrt_file}")
    mrt_data = pd.read_csv(mrt_file)
    mrt_data.columns = mrt_data.columns.str.strip()
    print("MRT data columns:", list(mrt_data.columns))
    print("First 3 rows of MRT data:")
    print(mrt_data.head(3))
    
    required_mrt_cols = ['participantId', 'angle_degrees', 'isCorrect', 'excluded_trial']
    missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
    if missing_mrt_cols:
        raise ValueError(f"Missing required columns in MRT file: {missing_mrt_cols}")
    
    # Print unique values for key experimental design parameters
    print("Unique values in angle_degrees:", sorted(mrt_data['angle_degrees'].unique()))
    print("Unique values in isCorrect:", sorted(mrt_data['isCorrect'].unique()))
    print("Unique values in excluded_trial:", sorted(mrt_data['excluded_trial'].unique()))
    
    # Load VWM data
    print(f"\nLoading VWM data from: {vwm_file}")
    vwm_data = pd.read_csv(vwm_file)
    vwm_data.columns = vwm_data.columns.str.strip()
    print("VWM data columns:", list(vwm_data.columns))
    print("First 3 rows of VWM data:")
    print(vwm_data.head(3))
    
    required_vwm_cols = ['participantId', 'error_absolute_degrees', 'excluded_trial']
    missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
    if missing_vwm_cols:
        raise ValueError(f"Missing required columns in VWM file: {missing_vwm_cols}")
    
    print("Unique values in VWM excluded_trial:", sorted(vwm_data['excluded_trial'].unique()))
    print("VWM error_absolute_degrees data type:", vwm_data['error_absolute_degrees'].dtype)
    
    # Load participant data
    print(f"\nLoading participant data from: {participant_file}")
    participant_data = pd.read_csv(participant_file)
    participant_data.columns = participant_data.columns.str.strip()
    print("Participant data columns:", list(participant_data.columns))
    print("First 3 rows of participant data:")
    print(participant_data.head(3))
    
    required_participant_cols = ['participantId', 'focus_loss_duration_pct']
    missing_participant_cols = [col for col in required_participant_cols if col not in participant_data.columns]
    if missing_participant_cols:
        raise ValueError(f"Missing required columns in participant file: {missing_participant_cols}")
    
    print("Focus loss duration data type:", participant_data['focus_loss_duration_pct'].dtype)
    
    return vonmises_params, mrt_data, vwm_data, participant_data

def prepare_analysis_data(vonmises_params, mrt_data, vwm_data, participant_data):
    """
    Prepare data for GLMM analysis by filtering and merging datasets.
    
    Parameters:
    vonmises_params (DataFrame): Von Mises parameter estimates
    mrt_data (DataFrame): Mental rotation task data
    vwm_data (DataFrame): Visual working memory data
    participant_data (DataFrame): Participant-level data
    
    Returns:
    DataFrame: Prepared analysis dataset
    """
    print("\nPreparing analysis data...")
    
    # Filter participants without poor fit flag
    print(f"Von Mises participants before poor fit filtering: {len(vonmises_params)}")
    vonmises_filtered = vonmises_params[vonmises_params['poor_fit_flag'] != True].copy()
    print(f"Von Mises participants after poor fit filtering: {len(vonmises_filtered)}")
    print(f"Excluded {len(vonmises_params) - len(vonmises_filtered)} participants due to poor fit")
    
    # Filter MRT trials to valid ones only
    print(f"MRT trials before exclusion filtering: {len(mrt_data)}")
    mrt_filtered = mrt_data[mrt_data['excluded_trial'] == False].copy()
    print(f"MRT trials after exclusion filtering: {len(mrt_filtered)}")
    print(f"Excluded {len(mrt_data) - len(mrt_filtered)} MRT trials")
    
    # Calculate mean VWM accuracy per participant (using valid trials only)
    print(f"VWM trials before exclusion filtering: {len(vwm_data)}")
    vwm_filtered = vwm_data[vwm_data['excluded_trial'] == False].copy()
    print(f"VWM trials after exclusion filtering: {len(vwm_filtered)}")
    
    vwm_accuracy = vwm_filtered.groupby('participantId')['error_absolute_degrees'].mean().reset_index()
    vwm_accuracy.columns = ['participantId', 'mean_vwm_accuracy']
    print(f"Calculated VWM accuracy for {len(vwm_accuracy)} participants")
    print("VWM accuracy summary:")
    print(vwm_accuracy['mean_vwm_accuracy'].describe())
    
    # Calculate weights based on kappa uncertainty
    print("\nCalculating uncertainty weights...")
    vonmises_filtered['kappa_se_squared'] = vonmises_filtered['kappa_se_overall'] ** 2
    
    # Handle cases where kappa_se_overall = 0
    zero_se_mask = vonmises_filtered['kappa_se_overall'] == 0
    print(f"Participants with kappa_se_overall = 0: {zero_se_mask.sum()}")
    
    if zero_se_mask.any():
        # Set weight for zero SE cases to maximum weight
        non_zero_weights = 1 / vonmises_filtered.loc[~zero_se_mask, 'kappa_se_squared']
        max_weight = non_zero_weights.max() if len(non_zero_weights) > 0 else 1.0
        print(f"Setting max weight for zero SE cases: {max_weight}")
        
        vonmises_filtered['model_weight'] = np.where(
            zero_se_mask,
            max_weight,
            1 / vonmises_filtered['kappa_se_squared']
        )
    else:
        vonmises_filtered['model_weight'] = 1 / vonmises_filtered['kappa_se_squared']
    
    print("Weight summary:")
    print(vonmises_filtered['model_weight'].describe())
    
    # Merge all datasets
    print("\nMerging datasets...")
    
    # Start with MRT data and add von Mises parameters
    analysis_data = mrt_filtered.merge(
        vonmises_filtered[['participantId', 'kappa_overall', 'model_weight']],
        on='participantId',
        how='inner'
    )
    print(f"After merging MRT with von Mises: {len(analysis_data)} trials")
    
    # Add VWM accuracy
    analysis_data = analysis_data.merge(vwm_accuracy, on='participantId', how='inner')
    print(f"After adding VWM accuracy: {len(analysis_data)} trials")
    
    # Add participant data
    analysis_data = analysis_data.merge(
        participant_data[['participantId', 'focus_loss_duration_pct']],
        on='participantId',
        how='inner'
    )
    print(f"After adding participant data: {len(analysis_data)} trials")
    
    # Check for NaN values before centering
    print("\nChecking for missing values before centering...")

    # Comprehensive list of columns used in the R model
    model_columns = [
        'isCorrect',
        'kappa_overall',
        'angle_degrees',
        'mean_vwm_accuracy',
        'focus_loss_duration_pct',
        'participantId',
        'model_weight'
    ]
    missing_counts = analysis_data[model_columns].isnull().sum()
    print("Missing value counts (all model columns):")
    print(missing_counts)

    if missing_counts.sum() > 0:
        print("Warning: Found missing values in model variables")
        initial_rows = len(analysis_data)
        analysis_data = analysis_data.dropna(subset=model_columns)
        final_rows = len(analysis_data)
        print(f"Dropped {initial_rows - final_rows} rows with missing values in model columns")

    # Center continuous predictors
    print("\nCentering continuous predictors...")
    analysis_data['kappa_overall_centered'] = analysis_data['kappa_overall'] - analysis_data['kappa_overall'].mean()
    analysis_data['mean_vwm_accuracy_centered'] = analysis_data['mean_vwm_accuracy'] - analysis_data['mean_vwm_accuracy'].mean()
    analysis_data['focus_loss_duration_pct_centered'] = analysis_data['focus_loss_duration_pct'] - analysis_data['focus_loss_duration_pct'].mean()
    
    print(f"Kappa centered mean: {analysis_data['kappa_overall_centered'].mean():.6f}")
    print(f"VWM accuracy centered mean: {analysis_data['mean_vwm_accuracy_centered'].mean():.6f}")
    print(f"Focus loss centered mean: {analysis_data['focus_loss_duration_pct_centered'].mean():.6f}")
    
    # Add trial ID
    analysis_data['trial_id'] = range(1, len(analysis_data) + 1)
    
    print(f"\nFinal analysis dataset: {len(analysis_data)} trials from {analysis_data['participantId'].nunique()} participants")
    print("Analysis data columns:", list(analysis_data.columns))
    print("First 2 rows of analysis data:")
    print(analysis_data.head(2))
    
    return analysis_data

def fit_glmm_model(analysis_data):
    """
    Fit generalized linear mixed-effects model using R's lme4 package.
    
    Parameters:
    analysis_data (DataFrame): Prepared analysis dataset
    
    Returns:
    tuple: R model object and fitted values
    """
    print("\nFitting GLMM model using R...")
    
    # Import R packages
    try:
        install_r_packages_if_needed()
        lme4 = importr('lme4')
        stats = importr('stats')
        base = importr('base')
        print("Successfully imported R packages")
    except Exception as e:
        print(f"Error importing R packages: {e}")
        raise

    # Convert data to R using modern conversion context
    from rpy2.robjects.conversion import localconverter
    with localconverter(ro.default_converter + pandas2ri.converter + numpy2ri.converter):
        r_data = ro.conversion.py2rpy(analysis_data)
    ro.globalenv['analysis_data'] = r_data

    # Set reference level for angle_degrees to 0 and ensure factors
    ro.r('''
    analysis_data$angle_degrees <- factor(analysis_data$angle_degrees, levels = c(0, 50, 100, 150))
    analysis_data$participantId <- factor(analysis_data$participantId)
    ''')

    print("Converted data to R format")
    print("R data dimensions:", ro.r('dim(analysis_data)'))

    # Check for complete cases in R for all model variables
    ro.r('''
    model_vars <- c("isCorrect", "kappa_overall_centered", "angle_degrees", 
                    "mean_vwm_accuracy_centered", "focus_loss_duration_pct_centered", 
                    "participantId", "model_weight")
    complete_cases_idx <- complete.cases(analysis_data[, model_vars])
    analysis_data_complete <- analysis_data[complete_cases_idx, ]
    n_total <- nrow(analysis_data)
    n_complete <- nrow(analysis_data_complete)
    n_missing <- n_total - n_complete
    print(paste0("Number of complete cases for model fitting: ", n_complete, " / ", n_total))
    if (n_missing > 0) {
        print(paste0("Number of rows dropped due to missing values: ", n_missing))
    }
    ''')

    n_total = int(ro.r('n_total')[0])
    n_complete = int(ro.r('n_complete')[0])
    n_missing = int(ro.r('n_missing')[0])
    print(f"Number of complete cases for model fitting: {n_complete} / {n_total}")
    if n_missing > 0:
        print(f"Number of rows dropped due to missing values: {n_missing}")

    # Define the model formula
    model_formula = '''
    isCorrect ~ kappa_overall_centered * angle_degrees + 
                mean_vwm_accuracy_centered + 
                focus_loss_duration_pct_centered + 
                (1 | participantId)
    '''

    print(f"Model formula: {model_formula}")

    # Fit the model using only complete cases
    print("Fitting GLMM model on complete cases...")
    try:
        ro.r(f'''
        model <- glmer({model_formula}, 
                      data = analysis_data_complete, 
                      family = binomial(link = "logit"),
                      weights = analysis_data_complete$model_weight,
                      control = glmerControl(optimizer = "bobyqa", 
                                           optCtrl = list(maxfun = 100000)))
        ''')
        print("Model fitted successfully")
    except Exception as e:
        print(f"Error fitting model: {e}")
        raise

    # Get fitted values and residuals
    ro.r('''
    fitted_values <- fitted(model)
    residuals_values <- residuals(model, type = "pearson")
    complete_cases_idx_py <- complete_cases_idx
    ''')
    
    return ro.r('model'), ro.r('fitted_values'), ro.r('residuals_values'), ro.r('complete_cases_idx_py')

def extract_model_results(model):
    """
    Extract model results including coefficients, confidence intervals, and diagnostics.
    
    Parameters:
    model: R model object
    
    Returns:
    tuple: Results dataframe and diagnostics dataframe
    """
    print("\nExtracting model results...")
    
    # Import additional R packages for results extraction
    try:
        broom_mixed = importr('broom.mixed')
        car = importr('car')
        performance = importr('performance')
        print("Successfully imported additional R packages")
    except Exception as e:
        print(f"Warning: Could not import all R packages for advanced diagnostics: {e}")
        # Use base R functions instead
        stats = importr('stats')
    
    # Extract fixed effects
    ro.r('''
    # Get model summary
    model_summary <- summary(model)

    # Extract fixed effects coefficients and their names
    fixed_effects <- model_summary$coefficients
    fixed_effects_rownames <- rownames(fixed_effects)

    # Calculate confidence intervals
    conf_int <- confint(model, parm = "beta_", method = "Wald")

    # Calculate VIF for multicollinearity assessment, ensuring a data.frame is returned
    vif_values <- tryCatch({
        vif_result <- car::vif(model)
        # Explicitly convert to a data.frame to ensure type consistency
        vif_df <- as.data.frame(vif_result)
        vif_df$predictor <- rownames(vif_df)
        vif_df
    }, error = function(e) { NULL })

    # Set flag for null check
    vif_is_null <- is.null(vif_values)

    # Get model fit statistics
    aic_value <- AIC(model)
    bic_value <- BIC(model)
    loglik_value <- logLik(model)[1]

    # Extract random effects variance
    var_comp <- as.data.frame(VarCorr(model))

    # Check convergence
    convergence_code <- model@optinfo$conv$opt
    convergence_msg <- model@optinfo$conv$lme4$messages
    ''')

    # Get fixed effects results
    from rpy2.robjects.conversion import localconverter
    with localconverter(ro.default_converter + pandas2ri.converter):
        fixed_effects_np = ro.conversion.rpy2py(ro.r('fixed_effects'))
        effect_names = list(ro.r('fixed_effects_rownames'))
        conf_int_np = ro.conversion.rpy2py(ro.r('conf_int'))

    # Create results dataframe
    results_df = pd.DataFrame({
        'effect_name': effect_names,
        'coefficient': fixed_effects_np[:, 0],
        'standard_error': fixed_effects_np[:, 1],
        'z_value': fixed_effects_np[:, 2],
        'p_value': fixed_effects_np[:, 3],
        'ci_lower': conf_int_np[:, 0],
        'ci_upper': conf_int_np[:, 1],
        'effect_type': ['fixed'] * len(effect_names)
    })

    print("Fixed effects results:")
    print(results_df)

    # Extract model diagnostics
    aic_val = float(ro.r('aic_value')[0])
    bic_val = float(ro.r('bic_value')[0])
    loglik_val = float(ro.r('loglik_value')[0])

    # Get random effects variance - more robust extraction
    from rpy2.robjects.conversion import localconverter
    with localconverter(ro.default_converter + pandas2ri.converter):
        var_comp = ro.conversion.rpy2py(ro.r('var_comp'))
    try:
        random_var = float(var_comp[var_comp['grp'] == 'participantId']['vcov'].iloc[0])
    except Exception:
        random_var = float(var_comp.iloc[0]['vcov']) if len(var_comp) > 0 else 0.0

    # Calculate ICC
    try:
        ro.r('icc_value <- performance::icc(model)$ICC_adjusted')
        icc_val = float(ro.r('icc_value')[0])
    except Exception:
        # Calculate ICC manually
        ro.r('icc_manual <- var_comp$vcov[1] / (var_comp$vcov[1] + pi^2/3)')
        icc_val = float(ro.r('icc_manual')[0])

    # Check convergence
    conv_code = int(ro.r('convergence_code')[0])

    # Process VIF values if available
    try:
        vif_is_null = bool(ro.r('vif_is_null')[0])
        if not vif_is_null:
            with localconverter(ro.default_converter + pandas2ri.converter):
                vif_df = ro.conversion.rpy2py(ro.r('vif_values'))
            
            print("\nVIF/GVIF values:")
            print(vif_df)
            
            # Handle different VIF output formats
            if "GVIF" in vif_df.columns and "Df" in vif_df.columns:
                # For models with factors, calculate adjusted VIF
                vif_to_check = (vif_df["GVIF"] ** (1/(2*vif_df["Df"])))**2
                vif_interpretation = 'Should be < 5 for no multicollinearity (from GVIF)'
            else:
                # For simple VIF
                vif_to_check = vif_df.iloc[:, 0]
                vif_interpretation = 'Should be < 5 for no multicollinearity'
            
            print("\nIndividual VIF values by predictor:")
            for i, (predictor, vif_val) in enumerate(zip(vif_df['predictor'], vif_to_check)):
                print(f"  {predictor}: {vif_val:.3f}")
            
            # Identify problematic predictors
            high_vif_threshold = 5.0
            high_vif_predictors = [vif_df['predictor'].iloc[i] for i, vif_val in enumerate(vif_to_check) if vif_val > high_vif_threshold]
            if high_vif_predictors:
                print(f"\nPredictors with VIF > {high_vif_threshold}: {high_vif_predictors}")
            
            vif_max = float(vif_to_check.max())
            vif_mean = float(vif_to_check.mean())
            vif_diagnostics = [
                ['VIF_Maximum', vif_max, vif_interpretation],
                ['VIF_Mean', vif_mean, 'Should be close to 1 for no multicollinearity']
            ]
        else:
            vif_diagnostics = [['VIF_Calculation', np.nan, 'Could not calculate VIF values']]
    except Exception as e:
        print(f"VIF processing error: {e}")
        vif_diagnostics = [['VIF_Calculation', np.nan, 'Could not calculate VIF values']]

    # Update diagnostics_df creation to include VIF
    base_diagnostics = [
        ['AIC', aic_val, 'Lower is better'],
        ['BIC', bic_val, 'Lower is better'], 
        ['LogLikelihood', loglik_val, 'Higher is better'],
        ['RandomIntercept_Variance', random_var, 'Between-participant variance'],
        ['ICC', icc_val, 'Proportion of variance due to participants'],
        ['Convergence_Code', conv_code, '0 = converged, non-zero = convergence issues']
    ]

    all_diagnostics = base_diagnostics + vif_diagnostics

    diagnostics_df = pd.DataFrame(all_diagnostics, columns=[
        'diagnostic_name', 'diagnostic_value', 'interpretation'
    ])

    # Ensure diagnostic_value column is numeric
    diagnostics_df['diagnostic_value'] = pd.to_numeric(diagnostics_df['diagnostic_value'], errors='coerce')

    print("\nModel diagnostics:")
    print(diagnostics_df)

    return results_df, diagnostics_df

def create_analysis_output(analysis_data, fitted_values, residuals, complete_cases_idx):
    """
    Create the analysis data output file with predictions and residuals.
    
    Parameters:
    analysis_data (DataFrame): Original analysis dataset
    fitted_values: R vector of fitted values
    residuals: R vector of residuals
    complete_cases_idx: R logical vector indicating complete cases used in model fitting
    
    Returns:
    DataFrame: Analysis data with predictions and residuals
    """
    print("\nCreating analysis output data...")

    # Convert R vectors to numpy arrays
    fitted_py = np.array(fitted_values)
    residuals_py = np.array(residuals)

    # Convert R logical vector to numpy boolean array
    complete_cases_bool = np.array(complete_cases_idx, dtype=bool)
    print(f"Length of analysis_data: {len(analysis_data)}")
    print(f"Length of complete_cases_bool: {len(complete_cases_bool)}")
    print(f"Length of fitted_py: {len(fitted_py)}")

    # Filter analysis_data to only complete cases used in model fitting
    filtered_analysis_data = analysis_data.loc[complete_cases_bool].copy()
    print(f"Filtered analysis_data to {len(filtered_analysis_data)} rows (should match fitted values length: {len(fitted_py)})")

    if len(filtered_analysis_data) != len(fitted_py):
        raise ValueError(f"Length mismatch: filtered_analysis_data ({len(filtered_analysis_data)}) vs fitted_py ({len(fitted_py)})")

    # Create output dataframe with required columns only
    output_data = filtered_analysis_data[[
        'participantId', 'trial_id', 'kappa_overall', 'angle_degrees', 
        'isCorrect', 'mean_vwm_accuracy', 'focus_loss_duration_pct', 'model_weight'
    ]].copy()

    output_data['predicted_accuracy'] = fitted_py
    output_data['residual'] = residuals_py

    print("Analysis output data columns:", list(output_data.columns))
    print("First 2 rows of analysis output data:")
    print(output_data.head(2))

    return output_data

def main():
    """
    Main function to execute the MRT accuracy GLMM analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT accuracy GLMM analysis...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Load and validate data
        vonmises_params, mrt_data, vwm_data, participant_data = load_and_validate_data()
        
        # Prepare analysis dataset
        analysis_data = prepare_analysis_data(vonmises_params, mrt_data, vwm_data, participant_data)
        
        # Fit GLMM model
        model, fitted_values, residuals, complete_cases_idx = fit_glmm_model(analysis_data)
        
        # Extract results
        results_df, diagnostics_df = extract_model_results(model)
        
        # Create analysis output
        analysis_output = create_analysis_output(analysis_data, fitted_values, residuals, complete_cases_idx)
        
        # Save results to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        results_file = f"outputs/mrt_accuracy_glmm_results_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        print(f"\nSaved model results to: {results_file}")
        
        diagnostics_file = f"outputs/mrt_accuracy_model_diagnostics_{timestamp}.csv"
        diagnostics_df.to_csv(diagnostics_file, index=False)
        print(f"Saved model diagnostics to: {diagnostics_file}")
        
        analysis_file = f"outputs/mrt_accuracy_analysis_data_{timestamp}.csv"
        analysis_output.to_csv(analysis_file, index=False)
        print(f"Saved analysis data to: {analysis_file}")
        
        print("\nAnalysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
