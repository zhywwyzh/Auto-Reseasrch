import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

# Import R interface and statistical packages
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.robjects.conversion import localconverter

    # Import R packages
    base = importr('base')
    stats = importr('stats')
    utils = importr('utils')

    # Check and install required R packages
    try:
        lme4 = importr('lme4')
        print("lme4 package loaded successfully")
    except:
        print("Installing lme4 package...")
        utils.install_packages('lme4')
        lme4 = importr('lme4')

    try:
        lmerTest = importr('lmerTest')
        print("lmerTest package loaded successfully")
    except:
        print("Installing lmerTest package...")
        utils.install_packages('lmerTest')
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
    str: Path to the most recent file matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found latest file: {latest_file}")
    return latest_file

def load_and_validate_data():
    """
    Load and validate all required input files.
    
    Returns:
    tuple: (experimental_data, vwm_params, behavioral_controls) DataFrames
    """
    print("Loading input files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Load experimental data
    exp_pattern = "outputs/cleaned_experimental_data_*.csv"
    exp_file = find_latest_file(exp_pattern)
    experimental_data = pd.read_csv(exp_file)
    print(f"Loaded experimental data: {exp_file}")
    print(f"Experimental data columns: {list(experimental_data.columns)}")
    print("First 3 rows of experimental data:")
    print(experimental_data.head(3))
    
    # Validate required columns for experimental data
    exp_required_cols = ['participantId', 'table', 'isPractice', 'MRT_trial', 
                        'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms']
    missing_exp_cols = [col for col in exp_required_cols if col not in experimental_data.columns]
    if missing_exp_cols:
        print(f"Missing required columns in experimental data: {missing_exp_cols}")
        sys.exit(1)
    
    # Load VWM parameters
    vwm_pattern = "outputs/vwm_mixture_model_parameters_*.csv"
    vwm_file = find_latest_file(vwm_pattern)
    vwm_params = pd.read_csv(vwm_file)
    print(f"Loaded VWM parameters: {vwm_file}")
    print(f"VWM parameters columns: {list(vwm_params.columns)}")
    print("First 3 rows of VWM parameters:")
    print(vwm_params.head(3))
    
    # Validate required columns for VWM parameters
    vwm_required_cols = ['participantId', 'kappa_concentration', 'convergence_successful', 'fit_quality_flag']
    missing_vwm_cols = [col for col in vwm_required_cols if col not in vwm_params.columns]
    if missing_vwm_cols:
        print(f"Missing required columns in VWM parameters: {missing_vwm_cols}")
        sys.exit(1)
    
    # Load behavioral controls
    behav_pattern = "outputs/behavioral_control_metrics_*.csv"
    behav_file = find_latest_file(behav_pattern)
    behavioral_controls = pd.read_csv(behav_file)
    print(f"Loaded behavioral controls: {behav_file}")
    print(f"Behavioral controls columns: {list(behavioral_controls.columns)}")
    print("First 3 rows of behavioral controls:")
    print(behavioral_controls.head(3))
    
    # Validate required columns for behavioral controls
    behav_required_cols = ['participantId', 'mean_vwm_absolute_error', 'mrt_rt_coefficient_variation',
                          'focus_loss_instances_total', 'focus_loss_duration_seconds_total', 'task_order_condition']
    missing_behav_cols = [col for col in behav_required_cols if col not in behavioral_controls.columns]
    if missing_behav_cols:
        print(f"Missing required columns in behavioral controls: {missing_behav_cols}")
        sys.exit(1)
    
    return experimental_data, vwm_params, behavioral_controls

def prepare_mrt_data(experimental_data):
    """
    Prepare MRT performance data by filtering and processing.
    
    Parameters:
    experimental_data (DataFrame): Raw experimental data
    
    Returns:
    DataFrame: Processed MRT trial data
    """
    print("Preparing MRT performance data...")
    
    # Print unique values for key experimental design parameters
    print(f"Unique values in 'table' column: {experimental_data['table'].unique()}")
    print(f"Unique values in 'isPractice' column: {experimental_data['isPractice'].unique()}")
    
    # Filter for MRT test trials only
    mrt_data = experimental_data[
        (experimental_data['isPractice'] == False) & 
        (experimental_data['table'] == 'mrt_test')
    ].copy()
    
    print(f"Filtered MRT data shape: {mrt_data.shape}")
    print(f"Unique MRT angle degrees: {sorted(mrt_data['MRT_angle_degrees'].unique())}")
    print(f"Unique MRT trial numbers: {sorted(mrt_data['MRT_trial'].unique())}")
    print(f"MRT_isCorrect data type: {type(mrt_data['MRT_isCorrect'].iloc[0])}")
    print(f"MRT_rt_ms data type: {type(mrt_data['MRT_rt_ms'].iloc[0])}")
    
    # Select required columns
    mrt_trial_data = mrt_data[['participantId', 'MRT_trial', 'MRT_angle_degrees', 
                              'MRT_isCorrect', 'MRT_rt_ms']].copy()
    
    print("MRT trial data columns:")
    print(list(mrt_trial_data.columns))
    print("First 2 rows of MRT trial data:")
    print(mrt_trial_data.head(2))
    
    return mrt_trial_data

def merge_datasets(mrt_data, vwm_params, behavioral_controls):
    """
    Merge all datasets and apply exclusion criteria.
    
    Parameters:
    mrt_data (DataFrame): MRT trial data
    vwm_params (DataFrame): VWM parameters
    behavioral_controls (DataFrame): Behavioral control metrics
    
    Returns:
    DataFrame: Merged and filtered dataset
    """
    print("Merging datasets...")
    
    # Print VWM parameter exclusion criteria values
    print(f"Convergence successful values: {vwm_params['convergence_successful'].unique()}")
    print(f"Fit quality flag values: {vwm_params['fit_quality_flag'].unique()}")
    
    # Apply VWM parameter exclusions
    print(f"VWM params before exclusions: {len(vwm_params)}")
    vwm_filtered = vwm_params[
        (vwm_params['convergence_successful'] == True) & 
        (vwm_params['fit_quality_flag'] == True)
    ].copy()
    print(f"VWM params after exclusions: {len(vwm_filtered)}")
    print(f"Excluded {len(vwm_params) - len(vwm_filtered)} participants due to poor VWM fit")
    
    # Merge MRT data with filtered VWM parameters
    merged_data = mrt_data.merge(vwm_filtered, on='participantId', how='inner')
    print(f"After merging with VWM params: {merged_data.shape}")
    
    # Merge with behavioral controls
    final_data = merged_data.merge(behavioral_controls, on='participantId', how='inner')
    print(f"Final merged data shape: {final_data.shape}")
    
    print("Final merged data columns:")
    print(list(final_data.columns))
    print("First 2 rows of final merged data:")
    print(final_data.head(2))
    
    print(f"Unique participants in final dataset: {final_data['participantId'].nunique()}")
    print(f"Total trials in final dataset: {len(final_data)}")
    
    return final_data

def run_mixed_effects_models(data):
    """
    Run all four mixed-effects models using R.
    """
    print("Running mixed-effects models using R...")
    
    # Convert data to R using modern pandas2ri approach
    with localconverter(robjects.default_converter + pandas2ri.converter):
        r_data = robjects.conversion.py2rpy(data)
    robjects.globalenv['data'] = r_data

    # Calculate minimum angle for reference category
    min_angle = int(data['MRT_angle_degrees'].min())
    print(f"Using {min_angle} degrees as reference category for MRT_angle_degrees")
    # Explicitly relevel MRT_angle_degrees factor in R
    robjects.r(f'data$MRT_angle_degrees <- relevel(factor(data$MRT_angle_degrees), ref="{min_angle}")')
    
    model_results = []
    
    # Model 1: MRT Accuracy Analysis (Logistic)
    print("Running Model 1: MRT Accuracy Analysis...")
    model1_formula = f"""
    glmer(MRT_isCorrect ~ kappa_concentration * factor(MRT_angle_degrees) + 
          task_order_condition + 
          (1|participantId), data=data, family=binomial)
    """
    
    try:
        robjects.r(f"model1 <- {model1_formula}")
        print("Model 1 completed successfully")
        model1_results = extract_r_model_results("Model1_Accuracy", "model1")
        model_results.extend(model1_results)
    except Exception as e:
        print(f"Error in Model 1: {e}")
    
    # Model 2: MRT Accuracy with Controls (Logistic)
    print("Running Model 2: MRT Accuracy with Controls...")
    model2_formula = f"""
    glmer(MRT_isCorrect ~ kappa_concentration * factor(MRT_angle_degrees) + 
          task_order_condition +
          mean_vwm_absolute_error + mrt_rt_coefficient_variation + 
          focus_loss_instances_total + focus_loss_duration_seconds_total +
          (1|participantId), data=data, family=binomial)
    """
    
    try:
        robjects.r(f"model2 <- {model2_formula}")
        print("Model 2 completed successfully")
        model2_results = extract_r_model_results("Model2_Accuracy_Controls", "model2")
        model_results.extend(model2_results)
    except Exception as e:
        print(f"Error in Model 2: {e}")
    
    # Filter for correct trials and add log transformation
    print("Filtering data for correct trials only...")
    robjects.r("data_correct <- data[data$MRT_isCorrect == TRUE, ]")
    robjects.r("data_correct$log_rt <- log(data_correct$MRT_rt_ms)")
    robjects.r(f'data_correct$MRT_angle_degrees <- relevel(factor(data_correct$MRT_angle_degrees), ref="{min_angle}")')
    
    # Model 3: MRT Reaction Time Analysis (Linear)
    print("Running Model 3: MRT Reaction Time Analysis...")
    model3_formula = f"""
    lmer(log_rt ~ kappa_concentration * factor(MRT_angle_degrees) + 
         task_order_condition + 
         (1|participantId), data=data_correct, REML=FALSE)
    """
    
    try:
        robjects.r(f"model3 <- {model3_formula}")
        print("Model 3 completed successfully")
        model3_results = extract_r_model_results("Model3_RT", "model3")
        model_results.extend(model3_results)
    except Exception as e:
        print(f"Error in Model 3: {e}")
    
    # Model 4: MRT Reaction Time with Controls (Linear)
    print("Running Model 4: MRT Reaction Time with Controls...")
    model4_formula = f"""
    lmer(log_rt ~ kappa_concentration * factor(MRT_angle_degrees) + 
         task_order_condition +
         mean_vwm_absolute_error + mrt_rt_coefficient_variation + 
         focus_loss_instances_total + focus_loss_duration_seconds_total +
         (1|participantId), data=data_correct, REML=FALSE)
    """
    
    try:
        robjects.r(f"model4 <- {model4_formula}")
        print("Model 4 completed successfully")
        model4_results = extract_r_model_results("Model4_RT_Controls", "model4")
        model_results.extend(model4_results)
    except Exception as e:
        print(f"Error in Model 4: {e}")
    
    return model_results

def extract_r_model_results(model_name, r_model_name):
    """
    Extract results from an R mixed-effects model.
    """
    print(f"Extracting results for {model_name}...")
    
    results = []
    
    try:
        # Get model summary
        robjects.r(f"model_summary <- summary({r_model_name})")
        
        # Get model fit statistics
        robjects.r(f"model_aic <- AIC({r_model_name})")
        robjects.r(f"model_bic <- BIC({r_model_name})")
        robjects.r(f"log_lik <- logLik({r_model_name})")
        
        # Extract coefficient table - use $coefficients for fixed effects
        robjects.r(f"coef_table <- summary({r_model_name})$coefficients")
        
        # Convert to Python with proper pandas2ri
        with localconverter(robjects.default_converter + pandas2ri.converter):
            coef_table = robjects.conversion.rpy2py(robjects.r("as.data.frame(coef_table)"))
            model_aic = robjects.r("model_aic")[0]
            model_bic = robjects.r("model_bic")[0]
            log_likelihood = robjects.r("as.numeric(log_lik)")[0]
        
        print(f"Model fit statistics - AIC: {model_aic:.2f}, BIC: {model_bic:.2f}, LogLik: {log_likelihood:.2f}")
        
        # Extract random effect variances
        try:
            robjects.r(f"rand_effects <- VarCorr({r_model_name})")
            robjects.r(f"rand_var <- as.data.frame(rand_effects)")
            with localconverter(robjects.default_converter + pandas2ri.converter):
                rand_var_df = robjects.conversion.rpy2py(robjects.r("rand_var"))
            random_effect_variance = rand_var_df.iloc[0]['vcov'] if len(rand_var_df) > 0 else np.nan
        except:
            random_effect_variance = np.nan
        
        print(f"Extracted random effect variance: {random_effect_variance:.4f}")
        
        # Extract confidence intervals
        try:
            robjects.r(f"conf_int <- confint({r_model_name}, method='Wald')")
            with localconverter(robjects.default_converter + pandas2ri.converter):
                conf_intervals = robjects.conversion.rpy2py(robjects.r("as.data.frame(conf_int)"))
        except:
            conf_intervals = None
        
        # Process each fixed effect
        for i, effect_name in enumerate(coef_table.index):
            # Check model type based on coefficient table structure
            if coef_table.shape[1] == 4:  # glmer model (Estimate, Std.Error, z value, Pr(>|z|))
                z_value = coef_table.iloc[i, 2]  # z value
                p_value = coef_table.iloc[i, 3]  # Pr(>|z|)
            else:  # lmer model with lmerTest (Estimate, Std.Error, df, t value, Pr(>|t|))
                z_value = coef_table.iloc[i, 3]  # t value (stored as z_value for consistency)
                p_value = coef_table.iloc[i, 4]  # Pr(>|t|)
            result = {
                'model_name': model_name,
                'effect_name': effect_name,
                'coefficient': coef_table.iloc[i, 0],  # Estimate
                'standard_error': coef_table.iloc[i, 1],  # Std. Error
                'z_value': z_value,  # z-value for glmer, t-value for lmer
                'p_value': p_value,  # Pr(>|z|) or Pr(>|t|)
                'conf_int_lower': conf_intervals.iloc[i, 0] if conf_intervals is not None and i < len(conf_intervals) else np.nan,
                'conf_int_upper': conf_intervals.iloc[i, 1] if conf_intervals is not None and i < len(conf_intervals) else np.nan,
                'model_aic': model_aic,
                'model_bic': model_bic,
                'log_likelihood': log_likelihood,
                'random_effect_variance': random_effect_variance
            }
            
            results.append(result)
            print(f"Extracted effect: {effect_name}, coef: {result['coefficient']:.4f}, p: {result['p_value']:.4f}")
    
    except Exception as e:
        print(f"Error extracting results for {model_name}: {e}")
    
    return results

def save_results(model_results):
    """
    Save model results to CSV file.
    
    Parameters:
    model_results (list): List of model result dictionaries
    """
    print("Saving results...")
    
    # Create results DataFrame
    results_df = pd.DataFrame(model_results)
    
    print("Results DataFrame columns:")
    print(list(results_df.columns))
    print("First 2 rows of results:")
    print(results_df.head(2))
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"outputs/mrt_mixed_effects_results_{timestamp}.csv"
    
    # Save to CSV
    results_df.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")
    print(f"Total number of effects saved: {len(results_df)}")

def main():
    """
    Main function to execute the mixed-effects analysis pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT mixed-effects analysis...")
        print(f"Analysis started at: {datetime.now()}")
        
        # Load and validate data
        experimental_data, vwm_params, behavioral_controls = load_and_validate_data()
        
        # Prepare MRT data
        mrt_data = prepare_mrt_data(experimental_data)
        
        # Merge datasets
        merged_data = merge_datasets(mrt_data, vwm_params, behavioral_controls)
        
        # Run mixed-effects models
        model_results = run_mixed_effects_models(merged_data)
        
        # Save results
        save_results(model_results)
        
        print(f"Analysis completed at: {datetime.now()}")
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
