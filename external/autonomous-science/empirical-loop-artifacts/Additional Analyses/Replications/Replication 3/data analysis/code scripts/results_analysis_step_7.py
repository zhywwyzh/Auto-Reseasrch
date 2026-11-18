#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

# Import rpy2 for R integration
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    from rpy2.robjects import conversion

    # Import base R packages first
    base = importr('base')
    utils = importr('utils')

    # Function to install R package if not available
    def install_r_package(package_name):
        try:
            importr(package_name)
            print(f"R package '{package_name}' already installed")
        except:
            print(f"Installing R package '{package_name}'...")
            utils.install_packages(package_name, repos='https://cloud.r-project.org/')
            print(f"R package '{package_name}' installed successfully")

    # Install required R packages
    required_packages = ['lme4', 'MuMIn', 'lmerTest']
    for pkg in required_packages:
        install_r_package(pkg)

    # Import R packages
    stats = importr('stats')
    lme4 = importr('lme4')
    MuMIn = importr('MuMIn')
    lmerTest = importr('lmerTest')  # For p-values in lmer models

    print("Successfully imported R packages")
except Exception as e:
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
        return None
    # Sort by modification time, return most recent
    return max(files, key=os.path.getmtime)

def load_and_validate_data():
    """
    Load and validate all required input files.
    
    Returns:
    tuple: (mrt_data, vwm_data, participants_data) DataFrames
    """
    print("Loading input files...")
    
    # Find latest files
    mrt_pattern = "outputs/MRT_cleaned_data_*.csv"
    vwm_pattern = "outputs/VWM_model_parameters_*.csv"
    participants_pattern = "outputs/participants_post_initial_exclusions_*.csv"
    
    mrt_file = find_latest_file(mrt_pattern)
    vwm_file = find_latest_file(vwm_pattern)
    participants_file = find_latest_file(participants_pattern)
    
    if not mrt_file:
        print(f"No MRT data file found matching pattern: {mrt_pattern}")
        sys.exit(1)
    if not vwm_file:
        print(f"No VWM data file found matching pattern: {vwm_pattern}")
        sys.exit(1)
    if not participants_file:
        print(f"No participants data file found matching pattern: {participants_pattern}")
        sys.exit(1)
    
    print(f"Loading MRT data from: {mrt_file}")
    print(f"Loading VWM data from: {vwm_file}")
    print(f"Loading participants data from: {participants_file}")
    
    # Load MRT data
    try:
        mrt_data = pd.read_csv(mrt_file)
        print(f"MRT data loaded. Shape: {mrt_data.shape}")
        print("MRT data columns:", list(mrt_data.columns))
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        # Validate required columns
        required_mrt_cols = ['participantId', 'MRT_trial', 'MRT_rt_ms', 'MRT_angle_degrees', 
                           'MRT_isCorrect', 'ln_MRT_rt', 'excluded', 'exclusion_reason']
        missing_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
        if missing_cols:
            print(f"Missing required MRT columns: {missing_cols}")
            sys.exit(1)
            
        # Print unique values for key experimental design parameters
        print("Unique MRT_angle_degrees values:", sorted(mrt_data['MRT_angle_degrees'].unique()))
        print("MRT_isCorrect data type:", mrt_data['MRT_isCorrect'].dtype)
        print("ln_MRT_rt data type:", mrt_data['ln_MRT_rt'].dtype)
        
    except Exception as e:
        print(f"Error loading MRT data: {e}")
        sys.exit(1)
    
    # Load VWM data
    try:
        vwm_data = pd.read_csv(vwm_file)
        print(f"VWM data loaded. Shape: {vwm_data.shape}")
        print("VWM data columns:", list(vwm_data.columns))
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
        
        # Validate required columns
        required_vwm_cols = ['participantId', 'kappa', 'excluded']
        missing_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
        if missing_cols:
            print(f"Missing required VWM columns: {missing_cols}")
            sys.exit(1)
            
        print("kappa data type:", vwm_data['kappa'].dtype)
        
    except Exception as e:
        print(f"Error loading VWM data: {e}")
        sys.exit(1)
    
    # Load participants data
    try:
        participants_data = pd.read_csv(participants_file)
        print(f"Participants data loaded. Shape: {participants_data.shape}")
        print("Participants data columns:", list(participants_data.columns))
        print("First 3 rows of participants data:")
        print(participants_data.head(3))
        
        # Validate required columns
        required_part_cols = ['participantId', 'mean_vwm_accuracy_z', 'response_time_cv_z', 
                            'composite_engagement_score_z']
        missing_cols = [col for col in required_part_cols if col not in participants_data.columns]
        if missing_cols:
            print(f"Missing required participants columns: {missing_cols}")
            sys.exit(1)
            
        print("mean_vwm_accuracy_z data type:", participants_data['mean_vwm_accuracy_z'].dtype)
        print("response_time_cv_z data type:", participants_data['response_time_cv_z'].dtype)
        print("composite_engagement_score_z data type:", participants_data['composite_engagement_score_z'].dtype)
        
    except Exception as e:
        print(f"Error loading participants data: {e}")
        sys.exit(1)
    
    return mrt_data, vwm_data, participants_data

def merge_and_filter_data(mrt_data, vwm_data, participants_data):
    """
    Merge datasets and filter out excluded participants.
    
    Parameters:
    mrt_data (DataFrame): MRT cleaned data
    vwm_data (DataFrame): VWM model parameters
    participants_data (DataFrame): Participants data with control variables
    
    Returns:
    DataFrame: Merged and filtered dataset
    """
    print("\nMerging datasets...")
    
    # Filter out excluded participants from each dataset
    print(f"MRT data before exclusions: {len(mrt_data)} rows")
    mrt_filtered = mrt_data[mrt_data['excluded'] == False].copy()
    print(f"MRT data after exclusions: {len(mrt_filtered)} rows")
    
    print(f"VWM data before exclusions: {len(vwm_data)} participants")
    vwm_filtered = vwm_data[vwm_data['excluded'] == False].copy()
    print(f"VWM data after exclusions: {len(vwm_filtered)} participants")
    
    print(f"Participants data before exclusions: {len(participants_data)} participants")
    # Check if participants data has excluded column
    if 'excluded' in participants_data.columns:
        participants_filtered = participants_data[participants_data['excluded'] == False].copy()
    else:
        # Filter out participants with NaN control variables
        participants_filtered = participants_data.dropna(subset=['mean_vwm_accuracy_z', 'response_time_cv_z', 'composite_engagement_score_z']).copy()
    print(f"Participants data after exclusions: {len(participants_filtered)} participants")
    
    # Merge datasets
    print("Merging VWM and participants data...")
    vwm_participants = pd.merge(vwm_filtered, participants_filtered, on='participantId', how='inner')
    print(f"VWM-participants merged data: {len(vwm_participants)} participants")
    print("VWM-participants merged columns:", list(vwm_participants.columns))
    print("First 2 rows of merged VWM-participants data:")
    print(vwm_participants.head(2))
    
    print("Merging with MRT data...")
    merged_data = pd.merge(mrt_filtered, vwm_participants, on='participantId', how='inner')
    print(f"Final merged data: {len(merged_data)} rows from {len(merged_data['participantId'].unique())} participants")
    print("Final merged columns:", list(merged_data.columns))
    print("First 2 rows of final merged data:")
    print(merged_data.head(2))
    
    # Report final sample
    print(f"\nFinal sample: {len(merged_data['participantId'].unique())} participants")
    print(f"Total trials: {len(merged_data)}")
    print("Trials per angle:")
    print(merged_data.groupby('MRT_angle_degrees').size())
    
    return merged_data

def prepare_model_data(merged_data):
    """
    Prepare data for mixed-effects modeling.
    
    Parameters:
    merged_data (DataFrame): Merged dataset
    
    Returns:
    tuple: (accuracy_data, rt_data) prepared for modeling
    """
    print("\nPreparing data for mixed-effects modeling...")
    
    # Ensure MRT_angle_degrees is treated as categorical (as string) with explicit ordering
    # Set '0.0' as the reference level and use ordered=False for treatment contrasts
    angle_strs = merged_data['MRT_angle_degrees'].astype(str)
    unique_angles = sorted(angle_strs.unique(), key=lambda x: float(x))
    if "0.0" in unique_angles:
        unique_angles = [lvl for lvl in unique_angles if lvl != "0.0"]
        unique_angles = ["0.0"] + unique_angles
    merged_data['rotation_angle'] = pd.Categorical(
        angle_strs,
        categories=unique_angles,
        ordered=False
    )
    
    print("Rotation angle categories:", merged_data['rotation_angle'].cat.categories.tolist())
    
    # For accuracy model - use all trials
    accuracy_data = merged_data.copy()
    print(f"Accuracy model data: {len(accuracy_data)} trials")
    
    # For RT model - use only correct responses
    rt_data = merged_data[merged_data['MRT_isCorrect'] == True].copy()
    print(f"RT model data (correct responses only): {len(rt_data)} trials")
    
    # Check for missing values in key variables
    print("\nMissing values check:")
    key_vars = ['kappa', 'MRT_isCorrect', 'ln_MRT_rt', 'mean_vwm_accuracy_z', 
                'response_time_cv_z', 'composite_engagement_score_z']
    for var in key_vars:
        if var in accuracy_data.columns:
            missing_acc = accuracy_data[var].isna().sum()
            print(f"{var} - Accuracy data missing: {missing_acc}")
        if var in rt_data.columns:
            missing_rt = rt_data[var].isna().sum()
            print(f"{var} - RT data missing: {missing_rt}")
    
    # Remove any rows with missing values in model variables
    print("\nRemoving rows with missing model variables...")
    model_vars_acc = ['kappa', 'MRT_isCorrect', 'rotation_angle', 'mean_vwm_accuracy_z', 
                     'response_time_cv_z', 'composite_engagement_score_z', 'participantId']
    accuracy_data = accuracy_data.dropna(subset=model_vars_acc)
    print(f"Accuracy data after removing missing: {len(accuracy_data)} trials")
    
    model_vars_rt = ['kappa', 'ln_MRT_rt', 'rotation_angle', 'mean_vwm_accuracy_z', 
                    'response_time_cv_z', 'composite_engagement_score_z', 'participantId']
    rt_data = rt_data.dropna(subset=model_vars_rt)
    print(f"RT data after removing missing: {len(rt_data)} trials")
    
    return accuracy_data, rt_data

def fit_mixed_effects_models(accuracy_data, rt_data):
    """
    Fit linear mixed-effects models using R's lme4 package.
    
    Parameters:
    accuracy_data (DataFrame): Data for accuracy model
    rt_data (DataFrame): Data for RT model
    
    Returns:
    tuple: (acc_coefs, rt_coefs, acc_rsq, rt_rsq, acc_param_names, rt_param_names)
    """
    print("\nFitting mixed-effects models using R's lme4...")
    
    # Convert pandas DataFrames to R DataFrames using context manager
    with conversion.localconverter(robjects.default_converter + pandas2ri.converter) as cv:
        r_acc_data = cv.py2rpy(accuracy_data)
        r_rt_data = cv.py2rpy(rt_data)

    # Assign data to R environment
    robjects.globalenv['acc_data'] = r_acc_data
    robjects.globalenv['rt_data'] = r_rt_data
    
    print("Data transferred to R environment")
    
    # Fit accuracy model (logistic regression)
    print("Fitting accuracy model (logistic regression)...")
    acc_formula = "MRT_isCorrect ~ kappa * rotation_angle + mean_vwm_accuracy_z + response_time_cv_z + composite_engagement_score_z + (1|participantId)"
    
    try:
        robjects.r(f'''
        acc_model <- glmer({acc_formula}, 
                          data = acc_data, 
                          family = binomial,
                          control = glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000)))
        ''')
        print("Accuracy model fitted successfully")
    except Exception as e:
        print(f"Error fitting accuracy model: {e}")
        sys.exit(1)
    
    # Fit RT model (linear regression)
    print("Fitting RT model (linear regression)...")
    rt_formula = "ln_MRT_rt ~ kappa * rotation_angle + mean_vwm_accuracy_z + response_time_cv_z + composite_engagement_score_z + (1|participantId)"
    
    try:
        robjects.r(f'''
        rt_model <- lmer({rt_formula}, 
                        data = rt_data,
                        control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 100000)))
        ''')
        print("RT model fitted successfully")
    except Exception as e:
        print(f"Error fitting RT model: {e}")
        sys.exit(1)
    
    # Extract model results
    print("Extracting model results...")
    
    # Get accuracy model results
    try:
        robjects.r('''
        acc_summary <- summary(acc_model)
        acc_coefs <- acc_summary$coefficients
        acc_param_names <- rownames(acc_coefs)
        acc_rsq <- r.squaredGLMM(acc_model)
        ''')
        
        with conversion.localconverter(robjects.default_converter + pandas2ri.converter) as cv:
            acc_coefs = cv.rpy2py(robjects.r['acc_coefs'])
            acc_param_names = cv.rpy2py(robjects.r['acc_param_names'])
            acc_rsq = cv.rpy2py(robjects.r['acc_rsq'])

        print("Accuracy model R-squared:")
        # Handle potential numpy array structure
        try:
            if hasattr(acc_rsq, 'shape') and len(acc_rsq.shape) > 1:
                marginal_rsq = float(acc_rsq[0, 0])
                conditional_rsq = float(acc_rsq[0, 1])
            else:
                marginal_rsq = float(acc_rsq[0])
                conditional_rsq = float(acc_rsq[1])
            print(f"Marginal R²: {marginal_rsq:.4f}")
            print(f"Conditional R²: {conditional_rsq:.4f}")
        except Exception as e:
            print(f"Error formatting accuracy model R-squared values: {e}")
            print(f"acc_rsq raw value: {acc_rsq}")
            raise

    except Exception as e:
        print(f"Error extracting accuracy model results: {e}")
        sys.exit(1)

    # Get RT model results
    try:
        robjects.r('''
        rt_summary <- summary(rt_model)
        rt_coefs <- rt_summary$coefficients
        rt_param_names <- rownames(rt_coefs)
        rt_rsq <- r.squaredGLMM(rt_model)
        ''')

        with conversion.localconverter(robjects.default_converter + pandas2ri.converter) as cv:
            rt_coefs = cv.rpy2py(robjects.r['rt_coefs'])
            rt_param_names = cv.rpy2py(robjects.r['rt_param_names'])
            rt_rsq = cv.rpy2py(robjects.r['rt_rsq'])

        print("RT model R-squared:")
        # Handle potential numpy array structure
        try:
            if hasattr(rt_rsq, 'shape') and len(rt_rsq.shape) > 1:
                marginal_rsq_rt = float(rt_rsq[0, 0])
                conditional_rsq_rt = float(rt_rsq[0, 1])
            else:
                marginal_rsq_rt = float(rt_rsq[0])
                conditional_rsq_rt = float(rt_rsq[1])
            print(f"Marginal R²: {marginal_rsq_rt:.4f}")
            print(f"Conditional R²: {conditional_rsq_rt:.4f}")
        except Exception as e:
            print(f"Error formatting RT model R-squared values: {e}")
            print(f"rt_rsq raw value: {rt_rsq}")
            raise

    except Exception as e:
        print(f"Error extracting RT model results: {e}")
        sys.exit(1)

    return acc_coefs, rt_coefs, acc_rsq, rt_rsq, acc_param_names, rt_param_names

def extract_model_diagnostics():
    """
    Extract model diagnostics from fitted models.
    
    Returns:
    tuple: (acc_diagnostics, rt_diagnostics) DataFrames
    """
    print("\nExtracting model diagnostics...")
    
    try:
        # Get accuracy model diagnostics
        robjects.r('''
        acc_fitted <- fitted(acc_model)
        acc_resid <- residuals(acc_model)
        acc_std_resid <- residuals(acc_model, type = "pearson")
        acc_leverage <- hatvalues(acc_model)
        acc_participant_ids <- acc_data$participantId
        ''')
        
        with conversion.localconverter(robjects.default_converter + pandas2ri.converter) as cv:
            acc_fitted = cv.rpy2py(robjects.r['acc_fitted'])
            acc_resid = cv.rpy2py(robjects.r['acc_resid'])
            acc_std_resid = cv.rpy2py(robjects.r['acc_std_resid'])
            acc_leverage = cv.rpy2py(robjects.r['acc_leverage'])
            acc_participant_ids = cv.rpy2py(robjects.r['acc_participant_ids'])

        acc_diagnostics = pd.DataFrame({
            'participantId': acc_participant_ids,
            'model_type': 'accuracy',
            'fitted_values': acc_fitted,
            'residuals': acc_resid,
            'standardized_residuals': acc_std_resid,
            'leverage': acc_leverage
        })

        print(f"Accuracy model diagnostics extracted: {len(acc_diagnostics)} observations")

    except Exception as e:
        print(f"Error extracting accuracy model diagnostics: {e}")
        sys.exit(1)

    try:
        # Get RT model diagnostics
        robjects.r('''
        rt_fitted <- fitted(rt_model)
        rt_resid <- residuals(rt_model)
        rt_std_resid <- residuals(rt_model, type = "pearson")
        rt_leverage <- hatvalues(rt_model)
        rt_participant_ids <- rt_data$participantId
        ''')

        with conversion.localconverter(robjects.default_converter + pandas2ri.converter) as cv:
            rt_fitted = cv.rpy2py(robjects.r['rt_fitted'])
            rt_resid = cv.rpy2py(robjects.r['rt_resid'])
            rt_std_resid = cv.rpy2py(robjects.r['rt_std_resid'])
            rt_leverage = cv.rpy2py(robjects.r['rt_leverage'])
            rt_participant_ids = cv.rpy2py(robjects.r['rt_participant_ids'])

        rt_diagnostics = pd.DataFrame({
            'participantId': rt_participant_ids,
            'model_type': 'reaction_time',
            'fitted_values': rt_fitted,
            'residuals': rt_resid,
            'standardized_residuals': rt_std_resid,
            'leverage': rt_leverage
        })

        print(f"RT model diagnostics extracted: {len(rt_diagnostics)} observations")

    except Exception as e:
        print(f"Error extracting RT model diagnostics: {e}")
        sys.exit(1)

    # Combine diagnostics
    diagnostics = pd.concat([acc_diagnostics, rt_diagnostics], ignore_index=True)

    return diagnostics

def create_results_dataframe(acc_coefs, rt_coefs, acc_rsq, rt_rsq, acc_param_names, rt_param_names):
    """
    Create results DataFrame from model outputs.
    
    Parameters:
    acc_coefs: Accuracy model coefficients
    rt_coefs: RT model coefficients  
    acc_rsq: Accuracy model R-squared values
    rt_rsq: RT model R-squared values
    acc_param_names: List of parameter names for accuracy model
    rt_param_names: List of parameter names for RT model
    
    Returns:
    DataFrame: Formatted results
    """
    print("\nCreating results DataFrame...")
    
    results_list = []
    
    # Prepare R-squared values for accuracy model
    try:
        marginal_r2 = float(acc_rsq[0, 0]) if hasattr(acc_rsq, 'shape') and len(acc_rsq.shape) > 1 else float(acc_rsq[0])
        conditional_r2 = float(acc_rsq[0, 1]) if hasattr(acc_rsq, 'shape') and len(acc_rsq.shape) > 1 else float(acc_rsq[1])
    except Exception as e:
        print(f"Error extracting accuracy model R-squared for results dataframe: {e}")
        marginal_r2 = np.nan
        conditional_r2 = np.nan

    # Process accuracy model results
    acc_params = acc_param_names if acc_param_names is not None else (
        acc_coefs.index.tolist() if hasattr(acc_coefs, 'index') else [f"param_{i}" for i in range(len(acc_coefs))]
    )
    
    for i, param in enumerate(acc_params):
        if len(acc_coefs.shape) == 2:
            estimate = acc_coefs.iloc[i, 0] if hasattr(acc_coefs, 'iloc') else acc_coefs[i][0]
            std_error = acc_coefs.iloc[i, 1] if hasattr(acc_coefs, 'iloc') else acc_coefs[i][1]
            # For accuracy models (glmer), p-values are typically in column 3 (0-indexed)
            if hasattr(acc_coefs, 'iloc') and acc_coefs.shape[1] > 3:
                p_value = acc_coefs.iloc[i, 3]
            elif hasattr(acc_coefs, '__getitem__') and len(acc_coefs[i]) > 3:
                p_value = acc_coefs[i][3]
            else:
                p_value = np.nan
        else:
            estimate = acc_coefs[i] if hasattr(acc_coefs, '__getitem__') else float(acc_coefs)
            std_error = np.nan
            p_value = np.nan
            
        results_list.append({
            'model_type': 'accuracy',
            'parameter': param,
            'estimate': float(estimate),
            'standard_error': float(std_error) if not pd.isna(std_error) else np.nan,
            'p_value': float(p_value) if not pd.isna(p_value) else np.nan,
            'marginal_r_squared': marginal_r2,
            'conditional_r_squared': conditional_r2
        })
    
    # Prepare R-squared values for RT model
    try:
        marginal_r2_rt = float(rt_rsq[0, 0]) if hasattr(rt_rsq, 'shape') and len(rt_rsq.shape) > 1 else float(rt_rsq[0])
        conditional_r2_rt = float(rt_rsq[0, 1]) if hasattr(rt_rsq, 'shape') and len(rt_rsq.shape) > 1 else float(rt_rsq[1])
    except Exception as e:
        print(f"Error extracting RT model R-squared for results dataframe: {e}")
        marginal_r2_rt = np.nan
        conditional_r2_rt = np.nan

    # Process RT model results
    rt_params = rt_param_names if rt_param_names is not None else (
        rt_coefs.index.tolist() if hasattr(rt_coefs, 'index') else [f"param_{i}" for i in range(len(rt_coefs))]
    )
    
    for i, param in enumerate(rt_params):
        if len(rt_coefs.shape) == 2:
            estimate = rt_coefs.iloc[i, 0] if hasattr(rt_coefs, 'iloc') else rt_coefs[i][0]
            std_error = rt_coefs.iloc[i, 1] if hasattr(rt_coefs, 'iloc') else rt_coefs[i][1]
            # For RT models with lmerTest, p-values are typically in column 4 (0-indexed)
            # But we need to check if the column exists
            if hasattr(rt_coefs, 'iloc') and rt_coefs.shape[1] > 4:
                p_value = rt_coefs.iloc[i, 4]
            elif hasattr(rt_coefs, '__getitem__') and len(rt_coefs[i]) > 4:
                p_value = rt_coefs[i][4]
            else:
                p_value = np.nan
        else:
            estimate = rt_coefs[i] if hasattr(rt_coefs, '__getitem__') else float(rt_coefs)
            std_error = np.nan
            p_value = np.nan
            
        results_list.append({
            'model_type': 'reaction_time',
            'parameter': param,
            'estimate': float(estimate),
            'standard_error': float(std_error) if not pd.isna(std_error) else np.nan,
            'p_value': float(p_value) if not pd.isna(p_value) else np.nan,
            'marginal_r_squared': marginal_r2_rt,
            'conditional_r_squared': conditional_r2_rt
        })
    
    results_df = pd.DataFrame(results_list)
    
    print("Results DataFrame created:")
    print("Columns:", list(results_df.columns))
    print("First 2 rows:")
    print(results_df.head(2))
    print(f"Total parameters: {len(results_df)}")
    
    return results_df

def save_results(results_df, diagnostics_df):
    """
    Save results and diagnostics to CSV files.
    
    Parameters:
    results_df (DataFrame): Model results
    diagnostics_df (DataFrame): Model diagnostics
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save results
    results_filename = f"outputs/MRT_mixed_effects_results_{timestamp}.csv"
    results_df.to_csv(results_filename, index=False)
    print(f"Results saved to: {results_filename}")
    
    # Save diagnostics
    diagnostics_filename = f"outputs/MRT_model_diagnostics_{timestamp}.csv"
    diagnostics_df.to_csv(diagnostics_filename, index=False)
    print(f"Diagnostics saved to: {diagnostics_filename}")
    
    # Print final summaries
    print(f"\nFinal results summary:")
    print(f"Results file contains {len(results_df)} parameter estimates")
    print(f"Diagnostics file contains {len(diagnostics_df)} observations")
    print(f"Models fitted: {results_df['model_type'].unique()}")

def main():
    """
    Main function to execute the MRT mixed-effects analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT mixed-effects analysis...")
        
        # Load and validate data
        mrt_data, vwm_data, participants_data = load_and_validate_data()
        
        # Merge and filter data
        merged_data = merge_and_filter_data(mrt_data, vwm_data, participants_data)
        
        # Prepare data for modeling
        accuracy_data, rt_data = prepare_model_data(merged_data)
        
        # Fit mixed-effects models
        acc_coefs, rt_coefs, acc_rsq, rt_rsq, acc_param_names, rt_param_names = fit_mixed_effects_models(accuracy_data, rt_data)
        
        # Extract diagnostics
        diagnostics_df = extract_model_diagnostics()
        
        # Create results DataFrame
        results_df = create_results_dataframe(acc_coefs, rt_coefs, acc_rsq, rt_rsq, acc_param_names, rt_param_names)
        
        # Save results
        save_results(results_df, diagnostics_df)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
