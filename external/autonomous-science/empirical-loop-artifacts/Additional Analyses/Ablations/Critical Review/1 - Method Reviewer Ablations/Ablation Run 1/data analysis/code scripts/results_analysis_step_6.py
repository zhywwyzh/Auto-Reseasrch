import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
from rpy2.robjects import conversion
import warnings
warnings.filterwarnings('ignore')

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
    return max(files, key=os.path.getctime)

def load_vwm_parameters():
    """
    Load VWM circular model parameters and filter for valid participants.
    
    Returns:
    pd.DataFrame: Filtered VWM parameters dataframe
    """
    print("Loading VWM circular model parameters...")
    
    # Find the most recent VWM parameters file
    vwm_pattern = "outputs/VWM_circular_model_parameters_*.csv"
    vwm_file = find_latest_file(vwm_pattern)
    
    if vwm_file is None:
        raise FileNotFoundError(f"No VWM parameters file found matching pattern: {vwm_pattern}")
    
    print(f"Found VWM parameters file: {vwm_file}")
    
    # Load the file
    vwm_df = pd.read_csv(vwm_file)
    print(f"VWM parameters shape: {vwm_df.shape}")
    print("VWM parameters columns:", list(vwm_df.columns))
    print("First 3 rows of VWM parameters:")
    print(vwm_df.head(3))
    
    # Check for required columns
    required_cols = ['participantId', 'kappa_vonmises', 'guess_rate_proportion', 'model_converged', 'excluded_from_modeling']
    missing_cols = [col for col in required_cols if col not in vwm_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in VWM parameters: {missing_cols}")
    
    print("Unique values for key columns:")
    print(f"model_converged: {sorted(vwm_df['model_converged'].unique())}")
    print(f"excluded_from_modeling: {sorted(vwm_df['excluded_from_modeling'].unique())}")
    
    # Filter participants with converged models and not excluded
    print(f"Total participants before filtering: {len(vwm_df)}")
    filtered_vwm = vwm_df[(vwm_df['model_converged'] == True) & (vwm_df['excluded_from_modeling'] == False)]
    print(f"Participants after filtering (converged=True AND excluded=False): {len(filtered_vwm)}")
    
    return filtered_vwm

def load_participant_summary():
    """
    Load participant summary metrics for MRT performance data.
    
    Returns:
    pd.DataFrame: Participant summary metrics dataframe
    """
    print("\nLoading participant summary metrics...")
    
    # Find the most recent participant summary file
    summary_pattern = "outputs/participant_summary_metrics_*.csv"
    summary_file = find_latest_file(summary_pattern)
    
    if summary_file is None:
        raise FileNotFoundError(f"No participant summary file found matching pattern: {summary_pattern}")
    
    print(f"Found participant summary file: {summary_file}")
    
    # Load the file
    summary_df = pd.read_csv(summary_file)
    print(f"Participant summary shape: {summary_df.shape}")
    print("Participant summary columns:", list(summary_df.columns))
    print("First 3 rows of participant summary:")
    print(summary_df.head(3))
    
    # Check for required columns
    required_cols = ['participantId', 'mean_vwm_absolute_error', 'overall_mrt_accuracy', 
                     'mrt_accuracy_0deg', 'mrt_accuracy_50deg', 'mrt_accuracy_100deg', 'mrt_accuracy_150deg',
                     'mrt_median_rt_0deg', 'mrt_median_rt_50deg', 'mrt_median_rt_100deg', 'mrt_median_rt_150deg']
    missing_cols = [col for col in required_cols if col not in summary_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in participant summary: {missing_cols}")
    
    return summary_df

def load_focus_loss_data():
    """
    Load focus loss aggregate metrics from original task data.
    
    Returns:
    pd.DataFrame: Focus loss metrics dataframe
    """
    print("\nLoading focus loss data from original task files...")
    
    # Find all participant data files
    data_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    data_files = glob.glob(data_pattern)
    
    if not data_files:
        raise FileNotFoundError(f"No participant data files found matching pattern: {data_pattern}")
    
    print(f"Found {len(data_files)} participant data files")
    
    focus_loss_data = []
    
    for file_path in data_files:
        try:
            # Extract participant ID from filename
            filename = os.path.basename(file_path)
            participant_id = filename.split('_')[1]  # Extract from PARTICIPANT_XXX_...
            
            # Load the file
            df = pd.read_csv(file_path)
            
            # Check if required columns exist
            if 'windowFocusLostDuringTasksNum' in df.columns and 'windowFocusLostDuringTasksDuration' in df.columns:
                # Get focus loss metrics (assuming they're consistent across rows for each participant)
                focus_num = df['windowFocusLostDuringTasksNum'].iloc[0] if not df['windowFocusLostDuringTasksNum'].isna().all() else 0
                focus_duration = df['windowFocusLostDuringTasksDuration'].iloc[0] if not df['windowFocusLostDuringTasksDuration'].isna().all() else 0

                # Convert duration to seconds if it's a string in HH:MM:SS format
                if isinstance(focus_duration, str) and focus_duration.strip():
                    try:
                        focus_duration_sec = pd.to_timedelta(focus_duration).total_seconds()
                    except (ValueError, TypeError):
                        focus_duration_sec = 0
                else:
                    focus_duration_sec = 0 if pd.isna(focus_duration) else float(focus_duration)

                focus_loss_data.append({
                    'participantId': participant_id,
                    'windowFocusLostDuringTasksNum': focus_num,
                    'windowFocusLostDuringTasksDuration': focus_duration_sec
                })
            else:
                print(f"Warning: Focus loss columns not found in {filename}")
                
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if not focus_loss_data:
        raise ValueError("No focus loss data could be extracted from participant files")
    
    focus_df = pd.DataFrame(focus_loss_data)
    print(f"Focus loss data shape: {focus_df.shape}")
    print("Focus loss data columns:", list(focus_df.columns))
    print("First 3 rows of focus loss data:")
    print(focus_df.head(3))
    
    return focus_df

def calculate_mrt_trial_counts():
    """Calculate the number of valid MRT trials per participant per angle."""
    print("\nCalculating MRT trial counts from cleaned trial data...")
    mrt_pattern = "outputs/MRT_cleaned_trial_data_*.csv"
    mrt_file = find_latest_file(mrt_pattern)
    if mrt_file is None:
        raise FileNotFoundError(f"No MRT cleaned trial data found: {mrt_pattern}")
    
    print(f"Found MRT cleaned trial data file: {mrt_file}")
    mrt_trials_df = pd.read_csv(mrt_file)
    print(f"MRT trials data shape: {mrt_trials_df.shape}")
    print("MRT trials columns:", list(mrt_trials_df.columns))
    
    # Ensure 'rotation_angle' exists and handle potential naming variations FIRST
    if 'MRT_angle_degrees' in mrt_trials_df.columns:
        mrt_trials_df = mrt_trials_df.rename(columns={'MRT_angle_degrees': 'rotation_angle'})
    
    # Now check for required columns AFTER potential renaming
    if 'trial_excluded' not in mrt_trials_df.columns:
        raise ValueError("Missing 'trial_excluded' column in MRT trial data")
    
    if 'rotation_angle' not in mrt_trials_df.columns:
        raise ValueError("Missing 'rotation_angle' column in MRT trial data")
    
    valid_trials = mrt_trials_df[mrt_trials_df['trial_excluded'] == False]
    trial_counts = valid_trials.groupby(['participantId', 'rotation_angle']).size().reset_index(name='ntrials')
    print(f"Calculated trial counts for {len(trial_counts)} participant-angle combinations.")
    print("First 3 rows of trial counts:")
    print(trial_counts.head(3))
    return trial_counts

def reshape_mrt_data(summary_df):
    """
    Reshape MRT data from wide to long format.
    
    Parameters:
    summary_df (pd.DataFrame): Participant summary metrics dataframe
    
    Returns:
    pd.DataFrame: Reshaped MRT data in long format
    """
    print("\nReshaping MRT data to long format...")
    
    # Define rotation angles and corresponding columns
    angles = [0, 50, 100, 150]
    accuracy_cols = ['mrt_accuracy_0deg', 'mrt_accuracy_50deg', 'mrt_accuracy_100deg', 'mrt_accuracy_150deg']
    rt_cols = ['mrt_median_rt_0deg', 'mrt_median_rt_50deg', 'mrt_median_rt_100deg', 'mrt_median_rt_150deg']
    
    long_data = []
    
    for _, row in summary_df.iterrows():
        participant_id = row['participantId']
        
        for i, angle in enumerate(angles):
            accuracy = row[accuracy_cols[i]]
            median_rt = row[rt_cols[i]]
            
            long_data.append({
                'participantId': participant_id,
                'rotation_angle': angle,
                'accuracy': accuracy,
                'median_rt': median_rt
            })
    
    long_df = pd.DataFrame(long_data)
    print(f"Long format MRT data shape: {long_df.shape}")
    print("Long format columns:", list(long_df.columns))
    print("First 2 rows of long format data:")
    print(long_df.head(2))
    
    print("Unique rotation angles:", sorted(long_df['rotation_angle'].unique()))
    
    return long_df

def merge_datasets(vwm_df, summary_df, focus_df, long_mrt_df):
    """
    Merge all datasets for mixed-effects modeling.
    
    Parameters:
    vwm_df (pd.DataFrame): VWM parameters dataframe
    summary_df (pd.DataFrame): Participant summary metrics dataframe  
    focus_df (pd.DataFrame): Focus loss metrics dataframe
    long_mrt_df (pd.DataFrame): Long format MRT data
    
    Returns:
    pd.DataFrame: Merged dataset for analysis
    """
    print("\nMerging datasets...")
    
    # Start with long format MRT data
    merged_df = long_mrt_df.copy()
    print(f"Starting with long MRT data: {merged_df.shape}")
    
    # Merge with VWM parameters
    merged_df = merged_df.merge(vwm_df[['participantId', 'kappa_vonmises', 'guess_rate_proportion']], 
                               on='participantId', how='inner')
    print(f"After merging VWM parameters: {merged_df.shape}")
    
    # Merge with summary metrics for covariates
    merged_df = merged_df.merge(summary_df[['participantId', 'mean_vwm_absolute_error']], 
                               on='participantId', how='inner')
    print(f"After merging summary metrics: {merged_df.shape}")
    
    # Merge with focus loss data
    merged_df = merged_df.merge(focus_df, on='participantId', how='left')
    print(f"After merging focus loss data: {merged_df.shape}")
    
    # Fill missing focus loss data with 0
    merged_df['windowFocusLostDuringTasksNum'].fillna(0, inplace=True)
    merged_df['windowFocusLostDuringTasksDuration'].fillna(0, inplace=True)
    
    print("Final merged dataset columns:", list(merged_df.columns))
    print("First 2 rows of merged dataset:")
    print(merged_df.head(2))
    
    print(f"Final dataset has {len(merged_df['participantId'].unique())} unique participants")
    print(f"Total observations: {len(merged_df)}")
    
    return merged_df

def setup_r_environment():
    """
    Set up R environment and load required packages.
    """
    print("\nSetting up R environment...")

    # Import R utils for package installation
    utils = importr('utils')
    utils.chooseCRANmirror(ind=1)  # select the first mirror

    required_packages = ['lme4', 'lmerTest', 'performance']
    loaded_packages = {}
    for pkg in required_packages:
        try:
            loaded_packages[pkg] = importr(pkg)
            print(f"Successfully loaded R package: {pkg}")
        except Exception as e:
            print(f"R package '{pkg}' not found. Attempting to install...")
            try:
                utils.install_packages(pkg)
                loaded_packages[pkg] = importr(pkg)
                print(f"Successfully installed and loaded R package: {pkg}")
            except Exception as install_e:
                print(f"Failed to install R package '{pkg}': {install_e}")
                raise

    lme4 = loaded_packages['lme4']
    lmertest = loaded_packages['lmerTest']
    performance = loaded_packages['performance']
    return lme4, lmertest, performance

def fit_mixed_effects_models(merged_df, lme4, lmertest, performance):
    """
    Fit linear mixed-effects models using R lme4.
    
    Parameters:
    merged_df (pd.DataFrame): Merged dataset for analysis
    lme4: R lme4 package object
    lmertest: R lmerTest package object  
    performance: R performance package object
    
    Returns:
    tuple: (accuracy_model_results, rt_model_results)
    """
    print("\nFitting mixed-effects models...")

    # Convert dataframe to R using modern rpy2
    with conversion.localconverter(ro.default_converter + pandas2ri.converter):
        r_df = ro.conversion.py2rpy(merged_df)
    ro.globalenv['data'] = r_df

    # Scale continuous predictors for model stability
    print("Scaling continuous predictors...")
    ro.r("""
    predictors_to_scale <- c('kappa_vonmises', 'rotation_angle', 'mean_vwm_absolute_error', 
                               'guess_rate_proportion', 'windowFocusLostDuringTasksNum')
    data[, predictors_to_scale] <- scale(data[, predictors_to_scale])
    """)

    results = {}

    # Model 1: Accuracy (binomial)
    print("\nFitting Model 1: MRT Accuracy (binomial)")
    accuracy_formula = """
    glmer(accuracy ~ kappa_vonmises * rotation_angle + mean_vwm_absolute_error + 
          guess_rate_proportion + windowFocusLostDuringTasksNum + (1|participantId), 
          data=data, family=binomial, weights = ntrials)
    """

    try:
        ro.r(f'model1 <- {accuracy_formula}')
        print("Model 1 fitted successfully")

        # Extract results
        model1_summary = ro.r('summary(model1)')
        print("Model 1 Summary:")
        print(model1_summary)

        # Extract coefficients with proper row names
        coef_table = ro.r('summary(model1)$coefficients')
        row_names = ro.r('rownames(summary(model1)$coefficients)')
        with conversion.localconverter(ro.default_converter + pandas2ri.converter):
            coef_df = ro.conversion.rpy2py(coef_table)
            effect_names = ro.conversion.rpy2py(row_names)
        coef_df = pd.DataFrame(coef_df)
        coef_df.columns = ['Estimate', 'Std_Error', 'z_value', 'p_value']
        coef_df['effect_name'] = effect_names
        coef_df['model_type'] = 'accuracy'
        coef_df['df'] = np.nan  # Add df column with NaN for binomial model
        print("DEBUG: Model 1 effect names:", list(coef_df['effect_name']))

        # Calculate confidence intervals for fixed effects only, using Wald method for speed
        ci = ro.r('confint(model1, parm="beta_", method="Wald")')
        with conversion.localconverter(ro.default_converter + pandas2ri.converter):
            ci_df = ro.conversion.rpy2py(ci)
        ci_df = pd.DataFrame(ci_df, index=coef_df.index)
        coef_df['confidence_interval_lower'] = ci_df.iloc[:, 0]
        coef_df['confidence_interval_upper'] = ci_df.iloc[:, 1]

        # Add significance
        coef_df['significance'] = coef_df['p_value'] < 0.05

        # Rename columns to match output requirements
        coef_df = coef_df.rename(columns={
            'Estimate': 'coefficient',
            'Std_Error': 'standard_error',
            'z_value': 't_value'
        })

        results['accuracy'] = coef_df[['model_type', 'effect_name', 'coefficient', 'standard_error',
                                     't_value', 'p_value', 'df', 'confidence_interval_lower',
                                     'confidence_interval_upper', 'significance']]

        # Model diagnostics
        aic1 = ro.r('AIC(model1)')[0]
        bic1 = ro.r('BIC(model1)')[0]
        loglik1 = ro.r('logLik(model1)')[0]

        # R-squared values
        try:
            r2_result = ro.r('performance::r2(model1)')
            r2_marginal = float(r2_result.rx2('R2_marginal')[0])
            r2_conditional = float(r2_result.rx2('R2_conditional')[0])
        except Exception as r2_e:
            print(f"Could not calculate R-squared for accuracy model: {r2_e}")
            r2_marginal = np.nan
            r2_conditional = np.nan

        # Random effects variance
        ranef_var = ro.r('VarCorr(model1)$participantId[1]')[0]

        # Convergence status
        convergence = ro.r('model1@optinfo$conv$opt')[0] == 0

        # Check for singular fit
        singular_fit = 'TRUE' in str(ro.r('isSingular(model1)'))

        accuracy_diagnostics = {
            'model_type': 'accuracy',
            'AIC': aic1,
            'BIC': bic1,
            'log_likelihood': loglik1,
            'r_squared_marginal': r2_marginal,
            'r_squared_conditional': r2_conditional,
            'random_effects_variance': ranef_var,
            'convergence_status': convergence,
            'singular_fit_warning': singular_fit
        }

    except Exception as e:
        print(f"Error fitting accuracy model: {e}")
        results['accuracy'] = pd.DataFrame()
        accuracy_diagnostics = {}

    # Model 2: Reaction Time (gaussian)
    print("\nFitting Model 2: MRT Reaction Time (gaussian)")

    # Check if log transformation is needed
    rt_data = merged_df['median_rt'].dropna()
    if rt_data.skew() > 1:  # If highly skewed, apply log transformation
        print("Applying log transformation to reaction times due to skewness")
        ro.r('data$log_median_rt <- log(data$median_rt)')
        rt_dv = 'log_median_rt'
    else:
        rt_dv = 'median_rt'

    rt_formula = f"""
    lmer({rt_dv} ~ kappa_vonmises * rotation_angle + mean_vwm_absolute_error + 
         guess_rate_proportion + windowFocusLostDuringTasksNum + (1|participantId), 
         data=data)
    """

    try:
        ro.r(f'model2 <- {rt_formula}')
        print("Model 2 fitted successfully")

        # Extract results
        model2_summary = ro.r('summary(model2)')
        print("Model 2 Summary:")
        print(model2_summary)

        # Extract coefficients with proper row names
        coef_table = ro.r('summary(model2)$coefficients')
        row_names = ro.r('rownames(summary(model2)$coefficients)')
        with conversion.localconverter(ro.default_converter + pandas2ri.converter):
            coef_df = ro.conversion.rpy2py(coef_table)
            effect_names = ro.conversion.rpy2py(row_names)
        coef_df = pd.DataFrame(coef_df)
        coef_df.columns = ['Estimate', 'Std_Error', 'df', 't_value', 'p_value']
        coef_df['effect_name'] = effect_names
        coef_df['model_type'] = 'reaction_time'
        print("DEBUG: Model 2 effect names:", list(coef_df['effect_name']))

        # Calculate confidence intervals for fixed effects only
        ci = ro.r('confint(model2, parm="beta_")')
        with conversion.localconverter(ro.default_converter + pandas2ri.converter):
            ci_df = ro.conversion.rpy2py(ci)
        ci_df = pd.DataFrame(ci_df, index=coef_df.index)
        coef_df['confidence_interval_lower'] = ci_df.iloc[:, 0]
        coef_df['confidence_interval_upper'] = ci_df.iloc[:, 1]

        # Add significance
        coef_df['significance'] = coef_df['p_value'] < 0.05

        # Rename columns to match output requirements
        coef_df = coef_df.rename(columns={
            'Estimate': 'coefficient',
            'Std_Error': 'standard_error'
        })

        results['reaction_time'] = coef_df[['model_type', 'effect_name', 'coefficient', 'standard_error',
                                          't_value', 'p_value', 'df', 'confidence_interval_lower',
                                          'confidence_interval_upper', 'significance']]

        # Model diagnostics
        aic2 = ro.r('AIC(model2)')[0]
        bic2 = ro.r('BIC(model2)')[0]
        loglik2 = ro.r('logLik(model2)')[0]

        # R-squared values
        try:
            r2_result = ro.r('performance::r2(model2)')
            r2_marginal = float(r2_result.rx2('R2_marginal')[0])
            r2_conditional = float(r2_result.rx2('R2_conditional')[0])
        except Exception as r2_e:
            print(f"Could not calculate R-squared for RT model: {r2_e}")
            r2_marginal = np.nan
            r2_conditional = np.nan

        # Random effects variance
        ranef_var = ro.r('VarCorr(model2)$participantId[1]')[0]

        # Convergence status
        convergence = ro.r('model2@optinfo$conv$opt')[0] == 0

        # Check for singular fit
        singular_fit = 'TRUE' in str(ro.r('isSingular(model2)'))

        rt_diagnostics = {
            'model_type': 'reaction_time',
            'AIC': aic2,
            'BIC': bic2,
            'log_likelihood': loglik2,
            'r_squared_marginal': r2_marginal,
            'r_squared_conditional': r2_conditional,
            'random_effects_variance': ranef_var,
            'convergence_status': convergence,
            'singular_fit_warning': singular_fit
        }

    except Exception as e:
        print(f"Error fitting reaction time model: {e}")
        results['reaction_time'] = pd.DataFrame()
        rt_diagnostics = {}

    return results, [accuracy_diagnostics, rt_diagnostics]

def test_hypotheses(results):
    """
    Test specific hypotheses from model results.
    
    Parameters:
    results (dict): Dictionary containing model results
    """
    print("\nTesting specific hypotheses...")
    
    for model_type, model_results in results.items():
        if model_results.empty:
            continue
        
        print(f"\n{model_type.upper()} MODEL HYPOTHESES:")
        
        # H1: Higher κ predicts better performance (main effect of kappa_vonmises)
        kappa_main = model_results[model_results['effect_name'].str.contains('kappa_vonmises') & 
                                  ~model_results['effect_name'].str.contains(':')]
        if not kappa_main.empty:
            kappa_coef = kappa_main.iloc[0]['coefficient']
            kappa_p = kappa_main.iloc[0]['p_value']
            print(f"H1 - Main effect of kappa_vonmises: β = {kappa_coef:.4f}, p = {kappa_p:.4f}")
            if model_type == 'accuracy' and kappa_coef > 0 and kappa_p < 0.05:
                print("H1 SUPPORTED: Higher κ predicts better accuracy")
            elif model_type == 'reaction_time' and kappa_coef < 0 and kappa_p < 0.05:
                print("H1 SUPPORTED: Higher κ predicts faster reaction times")
            else:
                print("H1 NOT SUPPORTED")
        
        # H3: Relationship strongest for larger angular disparities (interaction)
        interaction_name = 'kappa_vonmises:rotation_angle'
        interaction = model_results[model_results['effect_name'] == interaction_name]
        if not interaction.empty:
            int_coef = interaction.iloc[0]['coefficient']
            int_p = interaction.iloc[0]['p_value']
            print(f"H3 - Kappa × Rotation interaction: β = {int_coef:.4f}, p = {int_p:.4f}")
            if int_p < 0.05:
                print("H3 SUPPORTED: Significant interaction between κ and rotation angle")
            else:
                print("H3 NOT SUPPORTED: No significant interaction")

def save_results(results, diagnostics):
    """
    Save model results and diagnostics to CSV files.
    
    Parameters:
    results (dict): Dictionary containing model results
    diagnostics (list): List of diagnostic dictionaries
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combine all model results
    all_results = []
    for model_type, model_df in results.items():
        if not model_df.empty:
            all_results.append(model_df)
    
    if all_results:
        results_df = pd.concat(all_results, ignore_index=True)
        results_file = f"outputs/MRT_mixed_effects_results_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        print(f"Saved model results to: {results_file}")
        print("Results columns:", list(results_df.columns))
        print("First 2 rows of results:")
        print(results_df.head(2))
    
    # Save diagnostics
    if diagnostics:
        diagnostics_df = pd.DataFrame([d for d in diagnostics if d])
        diagnostics_file = f"outputs/MRT_model_diagnostics_{timestamp}.csv"
        diagnostics_df.to_csv(diagnostics_file, index=False)
        print(f"Saved model diagnostics to: {diagnostics_file}")
        print("Diagnostics columns:", list(diagnostics_df.columns))
        print("First 2 rows of diagnostics:")
        print(diagnostics_df.head(2))

def main():
    """
    Main function to execute the mixed-effects modeling analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT mixed-effects modeling analysis...")
        print("=" * 60)
        
        # Load all datasets
        vwm_df = load_vwm_parameters()
        summary_df = load_participant_summary()
        focus_df = load_focus_loss_data()
        
        # Reshape MRT data to long format
        long_mrt_df = reshape_mrt_data(summary_df)
        
        # Calculate trial counts
        trial_counts_df = calculate_mrt_trial_counts()
        
        # Merge trial counts with long format data
        long_mrt_df = pd.merge(long_mrt_df, trial_counts_df, on=['participantId', 'rotation_angle'], how='left')
        long_mrt_df['ntrials'].fillna(0, inplace=True)  # Handle cases with no valid trials for an angle
        print(f"Long format data after merging trial counts: {long_mrt_df.shape}")
        print("Updated columns:", list(long_mrt_df.columns))
        
        # Merge all datasets
        merged_df = merge_datasets(vwm_df, summary_df, focus_df, long_mrt_df)
        
        # Set up R environment
        lme4, lmertest, performance = setup_r_environment()
        
        # Fit mixed-effects models
        results, diagnostics = fit_mixed_effects_models(merged_df, lme4, lmertest, performance)
        
        # Test hypotheses
        test_hypotheses(results)
        
        # Save results
        save_results(results, diagnostics)
        
        print("=" * 60)
        print("Analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
