import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import scipy.stats as stats
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.metrics import r2_score
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
import warnings
warnings.filterwarnings('ignore')

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
    tuple: (trial_data, mixture_params, control_vars) DataFrames
    """
    print("Loading input files...")
    
    # Find latest files
    trial_data_file = find_latest_file("outputs/cleaned_trial_data_*.csv")
    mixture_params_file = find_latest_file("outputs/mixture_model_parameters_*.csv")
    control_vars_file = find_latest_file("outputs/control_variables_*.csv")
    
    # Load trial data
    print(f"Loading trial data from: {trial_data_file}")
    trial_data = pd.read_csv(trial_data_file)
    print(f"Trial data shape: {trial_data.shape}")
    print("Trial data columns:", list(trial_data.columns))
    print("First 3 rows of trial data:")
    print(trial_data.head(3))
    
    # Validate required columns for trial data
    required_trial_cols = ['participantId', 'isPractice', 'MRT_trial', 'MRT_angle_degrees', 
                          'MRT_isCorrect', 'MRT_rt_ms', 'MRT_timeout', 'trial_excluded']
    missing_cols = [col for col in required_trial_cols if col not in trial_data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in trial data: {missing_cols}")
    
    # Print unique values for key experimental design parameters
    print("Unique values in isPractice:", trial_data['isPractice'].unique())
    print("Unique values in MRT_angle_degrees:", sorted(trial_data['MRT_angle_degrees'].unique()))
    print("Unique values in MRT_isCorrect:", trial_data['MRT_isCorrect'].unique())
    print("Unique values in MRT_timeout:", trial_data['MRT_timeout'].unique())
    print("Unique values in trial_excluded:", trial_data['trial_excluded'].unique())
    
    # Load mixture model parameters
    print(f"Loading mixture model parameters from: {mixture_params_file}")
    mixture_params = pd.read_csv(mixture_params_file)
    print(f"Mixture params shape: {mixture_params.shape}")
    print("Mixture params columns:", list(mixture_params.columns))
    print("First 3 rows of mixture params:")
    print(mixture_params.head(3))
    
    # Validate required columns for mixture params
    required_mixture_cols = ['participantId', 'vonMises_kappa', 'convergence_status', 'best_model']
    missing_cols = [col for col in required_mixture_cols if col not in mixture_params.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in mixture params: {missing_cols}")
    
    print("Unique values in convergence_status:", mixture_params['convergence_status'].unique())
    print("Unique values in best_model:", mixture_params['best_model'].unique())
    
    # Load control variables
    print(f"Loading control variables from: {control_vars_file}")
    control_vars = pd.read_csv(control_vars_file)
    print(f"Control vars shape: {control_vars.shape}")
    print("Control vars columns:", list(control_vars.columns))
    print("First 3 rows of control vars:")
    print(control_vars.head(3))
    
    # Validate required columns for control vars
    required_control_cols = ['participantId', 'VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 
                            'MRT_rt_cv', 'focus_loss_instances_tasks', 'focus_loss_instances_instructions',
                            'focus_loss_duration_tasks_ms', 'focus_loss_duration_instructions_ms',
                            'VWM_timeout_rate', 'MRT_timeout_rate', 'engagement_index', 'valid_for_analysis']
    missing_cols = [col for col in required_control_cols if col not in control_vars.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in control vars: {missing_cols}")
    
    print("Unique values in valid_for_analysis:", control_vars['valid_for_analysis'].unique())
    
    return trial_data, mixture_params, control_vars

def prepare_mrt_performance_data(trial_data, mixture_params, control_vars):
    """
    Prepare MRT performance data by filtering and calculating metrics.
    
    Parameters:
    trial_data (DataFrame): Raw trial data
    mixture_params (DataFrame): Mixture model parameters
    control_vars (DataFrame): Control variables
    
    Returns:
    DataFrame: Prepared performance data
    """
    print("\nPreparing MRT performance data...")
    
    # Filter for valid participants
    print("Filtering participants...")
    valid_mixture = mixture_params[mixture_params['convergence_status'] == True]
    valid_control = control_vars[control_vars['valid_for_analysis'] == True]
    
    print(f"Participants with convergence_status=True: {len(valid_mixture)}")
    print(f"Participants with valid_for_analysis=True: {len(valid_control)}")
    
    # Get intersection of valid participants
    valid_participants = set(valid_mixture['participantId']) & set(valid_control['participantId'])
    print(f"Participants valid for both criteria: {len(valid_participants)}")
    
    # Filter trial data for test trials and valid participants
    test_trials = trial_data[
        (trial_data['isPractice'] == False) & 
        (trial_data['trial_excluded'] == False) &
        (trial_data['participantId'].isin(valid_participants))
    ].copy()
    
    print(f"Test trials after filtering: {len(test_trials)}")
    
    # Remove timeout trials
    non_timeout_trials = test_trials[test_trials['MRT_timeout'] == False].copy()
    print(f"Non-timeout trials: {len(non_timeout_trials)}")
    
    # Calculate performance metrics by participant and angular disparity
    angular_disparities = [0, 50, 100, 150]
    performance_data = []
    
    for participant in valid_participants:
        participant_data = {'participantId': participant}
        
        # Get participant trials
        p_trials = non_timeout_trials[non_timeout_trials['participantId'] == participant]
        
        # Calculate accuracy and RT for each angular disparity
        for angle in angular_disparities:
            angle_trials = p_trials[p_trials['MRT_angle_degrees'] == angle]
            
            if len(angle_trials) > 0:
                # Calculate accuracy
                accuracy = angle_trials['MRT_isCorrect'].mean()
                participant_data[f'MRT_accuracy_{angle}deg'] = accuracy
                
                # Calculate RT for correct responses only
                correct_trials = angle_trials[angle_trials['MRT_isCorrect'] == True]
                if len(correct_trials) > 0:
                    rt_log = np.log(correct_trials['MRT_rt_ms']).mean()
                    participant_data[f'MRT_rt_log_{angle}deg'] = rt_log
                else:
                    participant_data[f'MRT_rt_log_{angle}deg'] = np.nan
            else:
                participant_data[f'MRT_accuracy_{angle}deg'] = np.nan
                participant_data[f'MRT_rt_log_{angle}deg'] = np.nan
        
        performance_data.append(participant_data)
    
    performance_df = pd.DataFrame(performance_data)
    
    # Merge with mixture model parameters and control variables
    print("Merging with mixture model parameters and control variables...")
    
    # Merge with mixture params
    performance_df = performance_df.merge(
        valid_mixture[['participantId', 'vonMises_kappa']], 
        on='participantId', 
        how='inner'
    )
    
    # Merge with control variables
    control_cols_to_merge = ['participantId', 'VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 
                            'MRT_rt_cv', 'engagement_index', 'VWM_timeout_rate']
    performance_df = performance_df.merge(
        valid_control[control_cols_to_merge], 
        on='participantId', 
        how='inner'
    )
    
    print(f"Final performance data shape: {performance_df.shape}")
    print("Performance data columns:", list(performance_df.columns))
    print("First 2 rows of performance data:")
    print(performance_df.head(2))
    
    return performance_df, non_timeout_trials

def standardize_control_variables(performance_df):
    """
    Apply z-score standardization to control variables.
    
    Parameters:
    performance_df (DataFrame): Performance data
    
    Returns:
    DataFrame: Data with standardized control variables
    """
    print("\nStandardizing control variables...")
    
    control_vars_to_standardize = ['VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 
                                  'MRT_rt_cv', 'engagement_index', 'VWM_timeout_rate']
    
    standardized_df = performance_df.copy()
    
    for var in control_vars_to_standardize:
        if var in standardized_df.columns:
            mean_val = standardized_df[var].mean()
            std_val = standardized_df[var].std()
            if std_val == 0 or np.isnan(std_val):
                print(f"Warning: {var} has zero or undefined variance, skipping standardization.")
                continue
            standardized_df[var] = (standardized_df[var] - mean_val) / std_val
            print(f"Standardized {var}: mean={mean_val:.4f}, std={std_val:.4f}")
    
    return standardized_df

def calculate_vif(X):
    """
    Calculate variance inflation factors for predictors.
    
    Parameters:
    X (DataFrame): Predictor variables
    
    Returns:
    dict: VIF values for each predictor
    """
    vif_data = {}
    for i, col in enumerate(X.columns):
        try:
            vif_data[col] = variance_inflation_factor(X.values, i)
        except:
            vif_data[col] = np.nan
    return vif_data

def run_logistic_regression_analysis(performance_df, trial_data):
    """
    Run logistic regression analyses for MRT accuracy at each angular disparity.
    
    Parameters:
    performance_df (DataFrame): Performance data
    trial_data (DataFrame): Filtered non-timeout trial-level data
    
    Returns:
    list: Results from logistic regression analyses
    """
    print("\nRunning logistic regression analyses for MRT accuracy...")
    
    angular_disparities = [0, 50, 100, 150]
    results = []
    
    # Get valid participants
    valid_participants = set(performance_df['participantId'])
    
    # Filter trial data for analysis: only MRT trials, valid participants, and non-timeout
    analysis_trials = trial_data[
        (trial_data['participantId'].isin(valid_participants)) &
        (trial_data['MRT_trial'].notna())
    ].copy()
    
    # Merge standardized predictors onto trial data
    predictor_cols = ['participantId', 'vonMises_kappa', 'VWM_mean_accuracy_nonguess', 
                     'VWM_rt_cv', 'MRT_rt_cv', 'engagement_index', 'VWM_timeout_rate']
    analysis_trials = analysis_trials.merge(
        performance_df[predictor_cols], 
        on='participantId', 
        how='inner'
    )
    
    predictor_vars = ['vonMises_kappa', 'VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 
                     'MRT_rt_cv', 'engagement_index', 'VWM_timeout_rate']

    # Filter out zero variance predictors
    zero_var_predictors = [var for var in predictor_vars if performance_df[var].std() == 0 or np.isnan(performance_df[var].std())]
    if zero_var_predictors:
        print(f"Excluding zero-variance predictors from logistic regression: {zero_var_predictors}")
    predictor_vars = [var for var in predictor_vars if performance_df[var].std() > 0 and not np.isnan(performance_df[var].std())]

    for angle in angular_disparities:
        print(f"\nAnalyzing accuracy at {angle} degrees...")
        
        # Filter for specific angular disparity
        angle_trials = analysis_trials[analysis_trials['MRT_angle_degrees'] == angle].copy()
        
        if len(angle_trials) < 10:
            print(f"Insufficient data for {angle} degrees (n={len(angle_trials)})")
            continue
        
        # Prepare data
        X = angle_trials[predictor_vars].dropna()
        y = angle_trials.loc[X.index, 'MRT_isCorrect'].astype(int)
        
        print(f"Sample size for {angle} degrees: {len(X)}")
        print(f"Predictors used for {angle} degrees: {predictor_vars}")
        
        # Calculate VIF
        vif_values = calculate_vif(X)
        
        # Run logistic regression using statsmodels
        try:
            X_sm = sm.add_constant(X)
            model = sm.Logit(y, X_sm)
            result = model.fit(disp=0)
            
            # McFadden's pseudo R-squared
            llf = result.llf
            llnull = result.llnull
            pseudo_r2 = 1 - (llf / llnull) if llnull != 0 else np.nan
            
            # Model p-value (Likelihood Ratio Test)
            model_p_value = result.llr_pvalue if hasattr(result, "llr_pvalue") else np.nan
            
            # Store results for each predictor (excluding intercept)
            for i, var in enumerate(['const'] + predictor_vars):
                if var == 'const':
                    continue
                coef = result.params[var]
                se = result.bse[var]
                z_stat = result.tvalues[var]
                p_value = result.pvalues[var]
                ci_lower, ci_upper = result.conf_int().loc[var]
                or_coef = np.exp(coef)
                or_lower = np.exp(ci_lower)
                or_upper = np.exp(ci_upper)
                vif = vif_values.get(var, np.nan)
                
                results.append({
                    'analysis_type': 'logistic_regression',
                    'angular_disparity': angle,
                    'dependent_variable': 'MRT_accuracy',
                    'predictor_variable': var,
                    'coefficient': or_coef,  # Odds ratio
                    'standard_error': se,
                    't_statistic': z_stat,
                    'p_value': p_value,
                    'p_value_fdr_corrected': np.nan,  # Will be filled later
                    'confidence_interval_lower': or_lower,
                    'confidence_interval_upper': or_upper,
                    'VIF': vif,
                    'model_r_squared': pseudo_r2,
                    'model_f_statistic': np.nan,  # Not applicable for logistic regression
                    'model_p_value': model_p_value,
                    'sample_size': len(X)
                })
                
        except Exception as e:
            print(f"Error in logistic regression for {angle} degrees: {e}")
            continue
    
    return results

def run_linear_regression_analysis(performance_df, trial_data):
    """
    Run linear regression analyses for MRT reaction times at each angular disparity.
    
    Parameters:
    performance_df (DataFrame): Performance data
    trial_data (DataFrame): Filtered non-timeout trial-level data
    
    Returns:
    list: Results from linear regression analyses
    """
    print("\nRunning linear regression analyses for MRT reaction times...")
    
    angular_disparities = [0, 50, 100, 150]
    results = []
    
    # Get valid participants
    valid_participants = set(performance_df['participantId'])
    
    # Filter trial data for analysis: only MRT trials, valid participants, correct responses
    analysis_trials = trial_data[
        (trial_data['participantId'].isin(valid_participants)) &
        (trial_data['MRT_trial'].notna()) &
        (trial_data['MRT_isCorrect'] == True)
    ].copy()
    
    # Add log-transformed RT
    analysis_trials['MRT_rt_log'] = np.log(analysis_trials['MRT_rt_ms'])
    
    # Merge standardized predictors onto trial data
    predictor_cols = ['participantId', 'vonMises_kappa', 'VWM_mean_accuracy_nonguess', 
                     'VWM_rt_cv', 'MRT_rt_cv', 'engagement_index', 'VWM_timeout_rate']
    analysis_trials = analysis_trials.merge(
        performance_df[predictor_cols], 
        on='participantId', 
        how='inner'
    )
    
    predictor_vars = ['vonMises_kappa', 'VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 
                     'MRT_rt_cv', 'engagement_index', 'VWM_timeout_rate']

    # Filter out zero variance predictors
    zero_var_predictors = [var for var in predictor_vars if performance_df[var].std() == 0 or np.isnan(performance_df[var].std())]
    if zero_var_predictors:
        print(f"Excluding zero-variance predictors from linear regression: {zero_var_predictors}")
    predictor_vars = [var for var in predictor_vars if performance_df[var].std() > 0 and not np.isnan(performance_df[var].std())]

    for angle in angular_disparities:
        print(f"\nAnalyzing reaction times at {angle} degrees...")
        
        # Filter for specific angular disparity
        angle_trials = analysis_trials[analysis_trials['MRT_angle_degrees'] == angle].copy()
        
        if len(angle_trials) < 10:
            print(f"Insufficient data for {angle} degrees (n={len(angle_trials)})")
            continue
        
        # Prepare data
        X = angle_trials[predictor_vars].dropna()
        y = angle_trials.loc[X.index, 'MRT_rt_log']

        # Standardize the dependent variable for beta weights
        y_mean = y.mean()
        y_std = y.std()
        y_standardized = (y - y_mean) / y_std
        
        print(f"Sample size for {angle} degrees: {len(X)}")
        print(f"Predictors used for {angle} degrees: {predictor_vars}")
        
        # Calculate VIF
        vif_values = calculate_vif(X)
        
        # Run linear regression using statsmodels
        try:
            X_sm = sm.add_constant(X)
            model = sm.OLS(y_standardized, X_sm)
            result = model.fit()
            
            r2 = result.rsquared
            f_stat = result.fvalue
            f_p_value = result.f_pvalue
            n = int(result.nobs)
            p = int(result.df_model)
            
            # Store results for each predictor (excluding intercept)
            for i, var in enumerate(['const'] + predictor_vars):
                if var == 'const':
                    continue
                coef = result.params[var]
                se = result.bse[var]
                t_stat = result.tvalues[var]
                p_value = result.pvalues[var]
                ci_lower, ci_upper = result.conf_int().loc[var]
                vif = vif_values.get(var, np.nan)
                
                results.append({
                    'analysis_type': 'linear_regression',
                    'angular_disparity': angle,
                    'dependent_variable': 'MRT_rt_log',
                    'predictor_variable': var,
                    'coefficient': coef,
                    'standard_error': se,
                    't_statistic': t_stat,
                    'p_value': p_value,
                    'p_value_fdr_corrected': np.nan,  # Will be filled later
                    'confidence_interval_lower': ci_lower,
                    'confidence_interval_upper': ci_upper,
                    'VIF': vif,
                    'model_r_squared': r2,
                    'model_f_statistic': f_stat,
                    'model_p_value': f_p_value,
                    'sample_size': len(X)
                })
                
        except Exception as e:
            print(f"Error in linear regression for {angle} degrees: {e}")
            continue
    
    return results

def apply_fdr_correction(results):
    """
    Apply False Discovery Rate correction to p-values.
    """
    print("\nApplying FDR correction...")
    
    # Separate results by analysis type
    logistic_results = [r for r in results if r['analysis_type'] == 'logistic_regression']
    linear_results = [r for r in results if r['analysis_type'] == 'linear_regression']
    
    # Apply FDR correction separately for each analysis type
    for result_set in [logistic_results, linear_results]:
        if len(result_set) > 0:
            p_values = [r['p_value'] for r in result_set]
            _, p_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
            
            for i, result in enumerate(result_set):
                result['p_value_fdr_corrected'] = p_corrected[i]
    
    # For results without FDR correction (empty result sets), ensure the field exists
    for result in results:
        if 'p_value_fdr_corrected' not in result or np.isnan(result['p_value_fdr_corrected']):
            result['p_value_fdr_corrected'] = np.nan
    
    return results

def save_results(results, performance_df):
    """
    Save results to output files.
    
    Parameters:
    results (list): Analysis results
    performance_df (DataFrame): Performance data
    """
    print("\nSaving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save regression results
    results_df = pd.DataFrame(results)
    results_filename = f"outputs/MRT_regression_results_{timestamp}.csv"
    results_df.to_csv(results_filename, index=False)
    print(f"Saved regression results to: {results_filename}")
    print(f"Results shape: {results_df.shape}")
    
    # Save performance data
    performance_filename = f"outputs/MRT_performance_by_disparity_{timestamp}.csv"
    performance_df.to_csv(performance_filename, index=False)
    print(f"Saved performance data to: {performance_filename}")
    print(f"Performance data shape: {performance_df.shape}")
    
    # Print summary statistics
    print("\nSummary of results:")
    print(f"Total regression analyses: {len(results)}")
    print(f"Logistic regression analyses: {len([r for r in results if r['analysis_type'] == 'logistic_regression'])}")
    print(f"Linear regression analyses: {len([r for r in results if r['analysis_type'] == 'linear_regression'])}")
    
    # Check for high VIF values
    high_vif_results = [r for r in results if r['VIF'] > 5]
    if high_vif_results:
        print(f"\nWarning: {len(high_vif_results)} results have VIF > 5, indicating potential multicollinearity:")
        for result in high_vif_results:
            print(f"  {result['predictor_variable']} at {result['angular_disparity']}°: VIF = {result['VIF']:.2f}")
    
    # Print significant results after FDR correction
    significant_results = [r for r in results if r['p_value_fdr_corrected'] < 0.05]
    print(f"\nSignificant results after FDR correction (p < 0.05): {len(significant_results)}")
    for result in significant_results:
        print(f"  {result['analysis_type']}: {result['predictor_variable']} at {result['angular_disparity']}°, p_FDR = {result['p_value_fdr_corrected']:.4f}")

def main():
    """
    Main function to execute the MRT regression analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT regression analysis...")
        
        # Load and validate data
        trial_data, mixture_params, control_vars = load_and_validate_data()
        
        # Prepare MRT performance data
        performance_df, filtered_trial_data = prepare_mrt_performance_data(trial_data, mixture_params, control_vars)
        
        # Standardize control variables
        performance_df = standardize_control_variables(performance_df)
        
        # Run analyses
        logistic_results = run_logistic_regression_analysis(performance_df, filtered_trial_data)
        linear_results = run_linear_regression_analysis(performance_df, filtered_trial_data)
        
        # Combine results
        all_results = logistic_results + linear_results
        
        # Apply FDR correction
        all_results = apply_fdr_correction(all_results)
        
        # Save results
        save_results(all_results, performance_df)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
