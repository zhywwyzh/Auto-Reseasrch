#!/usr/bin/env python3
"""
Mixed-Effects Modeling for Mental Rotation Task (MRT) Performance
================================================================

This script analyzes the relationship between Visual Working Memory (VWM) precision
and Mental Rotation Task performance using mixed-effects models.

The analysis includes:
1. Data merging and preprocessing
2. Variable preparation for mixed-effects modeling
3. Fitting mixed-effects models for accuracy and reaction time
4. Extracting and saving model results

Author: Analysis Pipeline
"""

import os
import sys
import pandas as pd
import numpy as np
import glob
from datetime import datetime
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (e.g., 'outputs/VWM_parameters_*.csv')
        
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Get the most recent file by modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def setup_r_environment():
    """
    Set up R environment for mixed-effects modeling.
    
    Returns:
    --------
    tuple
        (rpy2.robjects, rpy2.robjects.pandas2ri, rpy2.robjects.packages.importr)
    """
    try:
        import rpy2.robjects as ro
        import rpy2.robjects.pandas2ri as pandas2ri
        from rpy2.robjects.packages import importr
        
        # Import utils for package installation
        utils = importr('utils')
        
        # Check and install required R packages
        required_packages = ['lme4', 'car', 'performance', 'broom.mixed', 'lmerTest']
        print("Checking R package dependencies...")
        
        packages_to_install = []
        for pkg in required_packages:
            try:
                importr(pkg)
                print(f"✓ {pkg} is available")
            except:
                packages_to_install.append(pkg)
                print(f"✗ {pkg} needs to be installed")
        
        if packages_to_install:
            print(f"Installing missing R packages: {', '.join(packages_to_install)}")
            utils.install_packages(ro.StrVector(packages_to_install), 
                                 repos='https://cloud.r-project.org/')
            print("R package installation completed")
        
        print("R environment setup successful")
        return ro, pandas2ri, importr
        
    except ImportError as e:
        print(f"Error setting up R environment: {e}")
        print("Please install rpy2: pip install rpy2")
        sys.exit(1)

def load_and_validate_data():
    """
    Load and validate input data files.
    
    Returns:
    --------
    tuple
        (vwm_data, mrt_data) - DataFrames containing VWM parameters and MRT data
    """
    print("=" * 60)
    print("LOADING AND VALIDATING INPUT DATA")
    print("=" * 60)
    
    # Find VWM parameters file
    vwm_pattern = "outputs/VWM_parameters_*.csv"
    vwm_file = find_most_recent_file(vwm_pattern)
    
    if vwm_file is None:
        print(f"Error: No VWM parameters file found matching pattern: {vwm_pattern}")
        sys.exit(1)
    
    print(f"Found VWM parameters file: {vwm_file}")
    
    # Find MRT dependent variables file
    mrt_pattern = "outputs/MRT_dependent_variables_*.csv"
    mrt_file = find_most_recent_file(mrt_pattern)
    
    if mrt_file is None:
        print(f"Error: No MRT dependent variables file found matching pattern: {mrt_pattern}")
        sys.exit(1)
    
    print(f"Found MRT dependent variables file: {mrt_file}")
    
    # Load VWM data
    print("\nLoading VWM parameters data...")
    try:
        vwm_data = pd.read_csv(vwm_file)
        print(f"VWM data shape: {vwm_data.shape}")
        print(f"VWM columns: {list(vwm_data.columns)}")
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
        
        # Validate required columns
        required_vwm_cols = ['participantId', 'vonMises_kappa', 'parameter_estimation_reliable']
        missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
        if missing_vwm_cols:
            print(f"Error: Missing required VWM columns: {missing_vwm_cols}")
            sys.exit(1)
        
        # Print unique values for key columns
        print(f"\nUnique parameter_estimation_reliable values: {vwm_data['parameter_estimation_reliable'].unique()}")
        print(f"vonMises_kappa data type: {vwm_data['vonMises_kappa'].dtype}")
        
    except Exception as e:
        print(f"Error loading VWM data: {e}")
        sys.exit(1)
    
    # Load MRT data
    print("\nLoading MRT dependent variables data...")
    try:
        mrt_data = pd.read_csv(mrt_file)
        print(f"MRT data shape: {mrt_data.shape}")
        print(f"MRT columns: {list(mrt_data.columns)}")
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        # Validate required columns
        required_mrt_cols = ['participantId', 'rotation_angle_degrees', 'MRT_accuracy_proportion', 
                            'MRT_log_median_rt', 'mean_VWM_absolute_error', 
                            'VWM_rt_coefficient_variation', 'focus_loss_severity_index']
        missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
        if missing_mrt_cols:
            print(f"Error: Missing required MRT columns: {missing_mrt_cols}")
            sys.exit(1)
        
        # Print unique values for key experimental design columns
        print(f"\nUnique rotation_angle_degrees values: {sorted(mrt_data['rotation_angle_degrees'].unique())}")
        print(f"MRT_accuracy_proportion data type: {mrt_data['MRT_accuracy_proportion'].dtype}")
        print(f"MRT_log_median_rt data type: {mrt_data['MRT_log_median_rt'].dtype}")
        
    except Exception as e:
        print(f"Error loading MRT data: {e}")
        sys.exit(1)
    
    return vwm_data, mrt_data

def merge_and_prepare_data(vwm_data, mrt_data):
    """
    Merge datasets and prepare variables for mixed-effects modeling.
    
    Parameters:
    -----------
    vwm_data : pd.DataFrame
        VWM parameters data
    mrt_data : pd.DataFrame
        MRT dependent variables data
        
    Returns:
    --------
    pd.DataFrame
        Merged and prepared analysis dataset
    """
    print("\n" + "=" * 60)
    print("MERGING AND PREPARING DATA")
    print("=" * 60)
    
    # Filter reliable participants from VWM data
    print(f"Total VWM participants: {len(vwm_data)}")
    reliable_vwm = vwm_data[vwm_data['parameter_estimation_reliable'] == True].copy()
    print(f"Reliable VWM participants: {len(reliable_vwm)}")
    print(f"Excluded VWM participants: {len(vwm_data) - len(reliable_vwm)}")
    
    # Merge datasets
    print("\nMerging VWM and MRT data...")
    merged_data = pd.merge(mrt_data, reliable_vwm[['participantId', 'vonMises_kappa']], 
                          on='participantId', how='inner')
    
    print(f"Merged data shape: {merged_data.shape}")
    print(f"Participants in merged data: {merged_data['participantId'].nunique()}")
    print(f"Total observations: {len(merged_data)}")
    
    print("\nMerged data columns:")
    print(list(merged_data.columns))
    print("\nFirst 2 rows of merged data:")
    print(merged_data.head(2))
    
    # Prepare variables for modeling
    print("\nPreparing variables for mixed-effects modeling...")
    
    # Convert rotation angle to categorical factor
    merged_data['rotation_angle_factor'] = merged_data['rotation_angle_degrees'].astype('category')
    print(f"Rotation angle factor levels: {merged_data['rotation_angle_factor'].cat.categories.tolist()}")
    
    # Center and scale vonMises_kappa
    kappa_mean = merged_data['vonMises_kappa'].mean()
    kappa_std = merged_data['vonMises_kappa'].std()
    merged_data['vonMises_kappa_centered'] = (merged_data['vonMises_kappa'] - kappa_mean) / kappa_std
    
    print(f"vonMises_kappa: mean={kappa_mean:.4f}, std={kappa_std:.4f}")
    print(f"vonMises_kappa_centered: mean={merged_data['vonMises_kappa_centered'].mean():.4f}, std={merged_data['vonMises_kappa_centered'].std():.4f}")
    
    # Center domain-general covariates
    covariates = ['mean_VWM_absolute_error', 'VWM_rt_coefficient_variation', 'focus_loss_severity_index']
    
    for covar in covariates:
        covar_mean = merged_data[covar].mean()
        merged_data[f'{covar}_centered'] = merged_data[covar] - covar_mean
        print(f"{covar}: mean={covar_mean:.4f}")
    
    # Check for missing data
    print("\nMissing data summary:")
    missing_summary = merged_data.isnull().sum()
    print(missing_summary[missing_summary > 0])

    # Check for weights column needed for binomial model
    if 'valid_trials_count_angle' in merged_data.columns:
        print(f"Found valid_trials_count_angle column for binomial weights")
        print(f"valid_trials_count_angle range: {merged_data['valid_trials_count_angle'].min()} to {merged_data['valid_trials_count_angle'].max()}")
    else:
        print("Warning: valid_trials_count_angle column not found - binomial model will be fitted without proper weights")
    
    # Report data availability for each model
    accuracy_data = merged_data.dropna(subset=['MRT_accuracy_proportion'])
    rt_data = merged_data.dropna(subset=['MRT_log_median_rt'])
    
    print(f"\nData available for accuracy model: {len(accuracy_data)} observations from {accuracy_data['participantId'].nunique()} participants")
    print(f"Data available for RT model: {len(rt_data)} observations from {rt_data['participantId'].nunique()} participants")
    
    return merged_data

def fit_mixed_effects_models(data, ro, pandas2ri, importr):
    """
    Fit linear mixed-effects models for MRT accuracy and reaction time.
    
    Parameters:
    -----------
    data : pd.DataFrame
        Prepared analysis dataset
    ro : rpy2.robjects module
        R objects interface
    pandas2ri : rpy2.robjects.pandas2ri module
        Pandas to R conversion module
    importr : function
        R package import function
        
    Returns:
    --------
    tuple
        (accuracy_model, rt_model, accuracy_results, rt_results, fit_stats)
    """
    print("\n" + "=" * 60)
    print("FITTING MIXED-EFFECTS MODELS")
    print("=" * 60)
    
    # Import required R packages
    lme4 = importr('lme4')
    car = importr('car')
    performance = importr('performance')
    broom_mixed = importr('broom.mixed')
    lmerTest = importr('lmerTest')
    
    # Convert data to R dataframe using modern conversion context
    print("Converting data to R format...")
    with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
        r_data = ro.conversion.py2rpy(data)
    
    # Define model formulas
    fixed_effects = "vonMises_kappa_centered + rotation_angle_factor + vonMises_kappa_centered:rotation_angle_factor + mean_VWM_absolute_error_centered + VWM_rt_coefficient_variation_centered + focus_loss_severity_index_centered"
    random_effects = "(1 | participantId)"
    
    accuracy_formula = f"MRT_accuracy_proportion ~ {fixed_effects} + {random_effects}"
    rt_formula = f"MRT_log_median_rt ~ {fixed_effects} + {random_effects}"
    
    print(f"Accuracy model formula: {accuracy_formula}")
    print(f"RT model formula: {rt_formula}")
    
    # Fit accuracy model (binomial with logit link)
    print("\nFitting accuracy model (binomial GLMM)...")
    accuracy_model = None
    try:
        if 'valid_trials_count_angle' in data.columns:
            print("Using valid_trials_count_angle as weights for binomial model")
            accuracy_model = lme4.glmer(accuracy_formula, 
                                      data=r_data, 
                                      family=ro.r('binomial(link="logit")'),
                                      weights=r_data.rx2('valid_trials_count_angle'),
                                      control=lme4.glmerControl(optimizer="bobyqa"))
        else:
            print("Warning: valid_trials_count_angle not found, fitting without weights")
            accuracy_model = lme4.glmer(accuracy_formula, 
                                      data=r_data, 
                                      family=ro.r('binomial(link="logit")'),
                                      control=lme4.glmerControl(optimizer="bobyqa"))
        print("Accuracy model fitted successfully")
    except Exception as e:
        print(f"Error fitting accuracy model: {e}")
        accuracy_model = None

    if accuracy_model is not None:
        # Check for convergence warnings
        convergence_check = ro.r('isSingular')(accuracy_model)[0]
        if convergence_check:
            print("Warning: Accuracy model has singular fit (convergence issues)")

        # Get model summary
        accuracy_summary = ro.r('summary')(accuracy_model)
        print("Accuracy model summary:")
        print(accuracy_summary)
    else:
        print("Accuracy model was not fitted due to an error.")

    print("\nFitting RT model (linear LMM)...")
    # Filter data for RT model in pandas first
    rt_data_pd = data.dropna(subset=['MRT_log_median_rt'])
    print(f"RT model data: {len(rt_data_pd)} observations from {rt_data_pd['participantId'].nunique()} participants")

    # Convert filtered data to R
    with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
        rt_data_r = ro.conversion.py2rpy(rt_data_pd)

    rt_model = None
    try:
        rt_model = lmerTest.lmer(rt_formula, 
                           data=rt_data_r,
                           control=lme4.lmerControl(optimizer="bobyqa"))
        print("RT model fitted successfully")
    except Exception as e:
        print(f"Error fitting RT model: {e}")
        rt_model = None

    if rt_model is not None:
        # Check for convergence warnings
        convergence_check = ro.r('isSingular')(rt_model)[0]
        if convergence_check:
            print("Warning: RT model has singular fit (convergence issues)")

        # Get model summary
        rt_summary = ro.r('summary')(rt_model)
        print("RT model summary:")
        print(rt_summary)
    else:
        print("RT model was not fitted due to an error.")

    # Extract model results
    print("\nExtracting model results...")

    tidy_func = ro.r['tidy']

    accuracy_results = None
    rt_results = None
    fit_stats = []

    if accuracy_model is not None:
        try:
            # Extract fixed effects for accuracy model
            accuracy_fixed = tidy_func(accuracy_model, effects="fixed", **{"conf.int": True})
            with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
                accuracy_results = ro.conversion.rpy2py(accuracy_fixed)
            accuracy_results['effect_type'] = 'fixed'
            accuracy_results['model_type'] = 'accuracy'

            print("Accuracy model fixed effects:")
            print(accuracy_results)
            print("Available columns in accuracy results:", list(accuracy_results.columns))

            # Get fit statistics for accuracy model
            acc_aic = ro.r('AIC')(accuracy_model)[0]
            acc_bic = ro.r('BIC')(accuracy_model)[0]

            # Get R-squared values
            acc_r2 = performance.r2(accuracy_model)
            with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
                acc_conditional_r2 = ro.conversion.rpy2py(acc_r2.rx2('R2_conditional'))[0]
                acc_marginal_r2 = ro.conversion.rpy2py(acc_r2.rx2('R2_marginal'))[0]

            # Count observations and participants
            acc_n_obs = len(data.dropna(subset=['MRT_accuracy_proportion']))
            acc_n_participants = data.dropna(subset=['MRT_accuracy_proportion'])['participantId'].nunique()

            fit_stats.append({
                'model_type': 'accuracy',
                'AIC': acc_aic,
                'BIC': acc_bic,
                'conditional_r_squared': acc_conditional_r2,
                'marginal_r_squared': acc_marginal_r2,
                'num_observations': acc_n_obs,
                'num_participants': acc_n_participants
            })

        except Exception as e:
            print(f"Error extracting accuracy model results: {e}")
            import traceback
            traceback.print_exc()

    if rt_model is not None:
        try:
            # Extract fixed effects for RT model
            rt_fixed = tidy_func(rt_model, effects="fixed", **{"conf.int": True})
            with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
                rt_results = ro.conversion.rpy2py(rt_fixed)
            rt_results['effect_type'] = 'fixed'
            rt_results['model_type'] = 'reaction_time'

            print("RT model fixed effects:")
            print(rt_results)
            print("Available columns in RT results:", list(rt_results.columns))

            # Get fit statistics for RT model
            rt_aic = ro.r('AIC')(rt_model)[0]
            rt_bic = ro.r('BIC')(rt_model)[0]

            # Get R-squared values
            rt_r2 = performance.r2(rt_model)
            with ro.conversion.localconverter(ro.default_converter + pandas2ri.converter):
                rt_conditional_r2 = ro.conversion.rpy2py(rt_r2.rx2('R2_conditional'))[0]
                rt_marginal_r2 = ro.conversion.rpy2py(rt_r2.rx2('R2_marginal'))[0]

            # Count observations and participants
            rt_n_obs = len(data.dropna(subset=['MRT_log_median_rt']))
            rt_n_participants = data.dropna(subset=['MRT_log_median_rt'])['participantId'].nunique()

            fit_stats.append({
                'model_type': 'reaction_time',
                'AIC': rt_aic,
                'BIC': rt_bic,
                'conditional_r_squared': rt_conditional_r2,
                'marginal_r_squared': rt_marginal_r2,
                'num_observations': rt_n_obs,
                'num_participants': rt_n_participants
            })

        except Exception as e:
            print(f"Error extracting RT model results: {e}")
            import traceback
            traceback.print_exc()

    return accuracy_model, rt_model, accuracy_results, rt_results, fit_stats

def save_results(accuracy_results, rt_results, fit_stats, timestamp):
    """
    Save model results to CSV files.
    
    Parameters:
    -----------
    accuracy_results : pd.DataFrame or None
        Accuracy model results
    rt_results : pd.DataFrame or None
        RT model results
    fit_stats : list
        Model fit statistics
    timestamp : str
        Timestamp for filenames
    """
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Save accuracy model results
    if accuracy_results is not None:
        accuracy_filename = f"outputs/MRT_accuracy_model_results_{timestamp}.csv"
        
        # Prepare accuracy results for output
        accuracy_output = accuracy_results.copy()
        
        # Debug: print available columns
        print("Available columns in accuracy results:", list(accuracy_output.columns))
        
        # Map column names to required output format
        column_mapping = {
            'term': 'term',
            'estimate': 'estimate',
            'std.error': 'std_error',
            'statistic': 'z_value',
            'p.value': 'p_value',
            'conf.low': 'conf_low_95',    # Fixed: was 'conf_low_95'
            'conf.high': 'conf_high_95',  # Fixed: was 'conf_high_95'
            'effect_type': 'effect_type'
        }
        
        # Only rename columns that actually exist
        for old_name, new_name in column_mapping.items():
            if old_name in accuracy_output.columns:
                accuracy_output = accuracy_output.rename(columns={old_name: new_name})
        
        # Only select columns that exist after renaming
        required_cols = ['term', 'estimate', 'std_error', 'z_value', 'p_value', 
                        'conf_low_95', 'conf_high_95', 'effect_type']
        available_cols = [col for col in required_cols if col in accuracy_output.columns]
        accuracy_output = accuracy_output[available_cols]
        
        accuracy_output.to_csv(accuracy_filename, index=False)
        print(f"Accuracy model results saved to: {accuracy_filename}")
        print("Accuracy results preview:")
        print(accuracy_output.head())
    
    # Save RT model results
    if rt_results is not None:
        rt_filename = f"outputs/MRT_reaction_time_model_results_{timestamp}.csv"
        
        # Prepare RT results for output
        rt_output = rt_results.copy()
        
        # Debug: print available columns
        print("Available columns in RT results:", list(rt_output.columns))
        
        # Map column names to required output format
        column_mapping = {
            'term': 'term',
            'estimate': 'estimate',
            'std.error': 'std_error',
            'statistic': 't_value',
            'p.value': 'p_value',
            'conf.low': 'conf_low_95',    # Fixed: was 'conf_low_95'
            'conf.high': 'conf_high_95',  # Fixed: was 'conf_high_95'
            'effect_type': 'effect_type'
        }
        
        # Only rename columns that actually exist
        for old_name, new_name in column_mapping.items():
            if old_name in rt_output.columns:
                rt_output = rt_output.rename(columns={old_name: new_name})
        
        # Only select columns that exist after renaming
        required_cols = ['term', 'estimate', 'std_error', 't_value', 'p_value', 
                        'conf_low_95', 'conf_high_95', 'effect_type']
        available_cols = [col for col in required_cols if col in rt_output.columns]
        rt_output = rt_output[available_cols]
        
        rt_output.to_csv(rt_filename, index=False)
        print(f"RT model results saved to: {rt_filename}")
        print("RT results preview:")
        print(rt_output.head())
    
    # Save fit statistics
    if fit_stats:
        fit_stats_filename = f"outputs/MRT_model_fit_statistics_{timestamp}.csv"
        fit_stats_df = pd.DataFrame(fit_stats)
        
        # Select only required columns
        required_cols = ['model_type', 'AIC', 'BIC', 'conditional_r_squared', 
                        'marginal_r_squared', 'num_observations', 'num_participants']
        fit_stats_df = fit_stats_df[required_cols]
        
        fit_stats_df.to_csv(fit_stats_filename, index=False)
        print(f"Model fit statistics saved to: {fit_stats_filename}")
        print("Fit statistics preview:")
        print(fit_stats_df)

def save_model_objects(accuracy_model, rt_model, ro, timestamp):
    """
    Save fitted model objects to .rds files.
    
    Parameters:
    -----------
    accuracy_model : R model object or None
        Fitted accuracy model
    rt_model : R model object or None  
        Fitted RT model
    ro : rpy2.robjects module
        R objects interface
    timestamp : str
        Timestamp for filenames
    """
    print("\n" + "=" * 60)
    print("SAVING FITTED MODEL OBJECTS (.rds)")
    print("=" * 60)
    
    if accuracy_model is not None:
        accuracy_rds_filename = f"outputs/MRT_accuracy_model_{timestamp}.rds"
        try:
            ro.r('saveRDS')(accuracy_model, accuracy_rds_filename)
            print(f"Accuracy model object saved to: {accuracy_rds_filename}")
        except Exception as e:
            print(f"Error saving accuracy model object: {e}")

    if rt_model is not None:
        rt_rds_filename = f"outputs/MRT_reaction_time_model_{timestamp}.rds"
        try:
            ro.r('saveRDS')(rt_model, rt_rds_filename)
            print(f"RT model object saved to: {rt_rds_filename}")
        except Exception as e:
            print(f"Error saving RT model object: {e}")

def main():
    """
    Main function to execute the mixed-effects modeling analysis.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting Mixed-Effects Modeling for MRT Performance Analysis")
        print("=" * 80)
        
        # Set up R environment
        ro, pandas2ri, importr = setup_r_environment()
        
        # Load and validate data
        vwm_data, mrt_data = load_and_validate_data()
        
        # Merge and prepare data
        analysis_data = merge_and_prepare_data(vwm_data, mrt_data)
        
        # Fit mixed-effects models
        accuracy_model, rt_model, accuracy_results, rt_results, fit_stats = fit_mixed_effects_models(
            analysis_data, ro, pandas2ri, importr)
        
        # Generate timestamp once for all output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save results
        save_results(accuracy_results, rt_results, fit_stats, timestamp)
        
        # Save model objects to RDS
        save_model_objects(accuracy_model, rt_model, ro, timestamp)
        
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
