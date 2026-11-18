import os
import pandas as pd
import numpy as np
np.bool = np.bool_  # Handle numpy deprecation
import glob
from datetime import datetime
import sys
from scipy import stats as scipy_stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import OLSInfluence

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to search for
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def load_and_validate_data():
    """
    Load and validate all required input files.
    
    Returns:
    tuple: (vwm_params_df, vviq2_df, summary_metrics_df, task_data_df)
    """
    print("Starting data loading and validation...")
    
    # Create outputs directory if it doesn't exist
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")
    
    # Load VWM circular model parameters
    print("\n=== Loading VWM circular model parameters ===")
    vwm_pattern = "outputs/VWM_circular_model_parameters_*.csv"
    vwm_file = find_latest_file(vwm_pattern)
    if not vwm_file:
        print(f"ERROR: No VWM parameters file found matching pattern {vwm_pattern}")
        return None, None, None, None
    
    print(f"Loading VWM parameters from: {vwm_file}")
    vwm_params_df = pd.read_csv(vwm_file)
    print("VWM parameters - All columns:")
    print(vwm_params_df.columns.tolist())
    print("VWM parameters - First 3 rows:")
    print(vwm_params_df.head(3))
    
    # Check required columns for VWM parameters
    required_vwm_cols = ['participantId', 'kappa_vonmises', 'guess_rate_proportion', 'model_converged', 'excluded_from_modeling']
    missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_params_df.columns]
    if missing_vwm_cols:
        print(f"ERROR: Missing required VWM columns: {missing_vwm_cols}")
        return None, None, None, None
    
    print(f"VWM parameters shape before filtering: {vwm_params_df.shape}")
    print("VWM parameters - model_converged unique values:", vwm_params_df['model_converged'].unique())
    print("VWM parameters - excluded_from_modeling unique values:", vwm_params_df['excluded_from_modeling'].unique())
    
    # Filter VWM parameters
    vwm_filtered = vwm_params_df[
        (vwm_params_df['model_converged'] == True) & 
        (vwm_params_df['excluded_from_modeling'] == False)
    ]
    print(f"VWM parameters shape after filtering: {vwm_filtered.shape}")
    
    # Load VVIQ2 processed scores
    print("\n=== Loading VVIQ2 processed scores ===")
    vviq2_pattern = "outputs/VVIQ2_processed_scores_*.csv"
    vviq2_file = find_latest_file(vviq2_pattern)
    if not vviq2_file:
        print(f"ERROR: No VVIQ2 scores file found matching pattern {vviq2_pattern}")
        return None, None, None, None
    
    print(f"Loading VVIQ2 scores from: {vviq2_file}")
    vviq2_df = pd.read_csv(vviq2_file)
    print("VVIQ2 scores - All columns:")
    print(vviq2_df.columns.tolist())
    print("VVIQ2 scores - First 3 rows:")
    print(vviq2_df.head(3))
    
    # Check required columns for VVIQ2
    required_vviq2_cols = ['participantId', 'total_score_standardized', 'face_person_standardized', 
                          'sunrise_standardized', 'shop_standardized', 'countryside_standardized',
                          'car_road_standardized', 'beach_standardized', 'station_standardized', 
                          'garden_standardized']
    missing_vviq2_cols = [col for col in required_vviq2_cols if col not in vviq2_df.columns]
    if missing_vviq2_cols:
        print(f"ERROR: Missing required VVIQ2 columns: {missing_vviq2_cols}")
        return None, None, None, None
    
    # Load participant summary metrics
    print("\n=== Loading participant summary metrics ===")
    summary_pattern = "outputs/participant_summary_metrics_*.csv"
    summary_file = find_latest_file(summary_pattern)
    if not summary_file:
        print(f"ERROR: No summary metrics file found matching pattern {summary_pattern}")
        return None, None, None, None
    
    print(f"Loading summary metrics from: {summary_file}")
    summary_metrics_df = pd.read_csv(summary_file)
    print("Summary metrics - All columns:")
    print(summary_metrics_df.columns.tolist())
    print("Summary metrics - First 3 rows:")
    print(summary_metrics_df.head(3))
    
    # Check required columns for summary metrics
    required_summary_cols = ['participantId', 'mean_vwm_absolute_error']
    missing_summary_cols = [col for col in required_summary_cols if col not in summary_metrics_df.columns]
    if missing_summary_cols:
        print(f"ERROR: Missing required summary columns: {missing_summary_cols}")
        return None, None, None, None
    
    # Load task data for focus loss metrics
    print("\n=== Loading task data for focus loss metrics ===")
    task_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    task_files = glob.glob(task_pattern)
    if not task_files:
        print(f"ERROR: No task data files found matching pattern {task_pattern}")
        return None, None, None, None
    
    print(f"Found {len(task_files)} task data files")
    
    # Combine task data files to extract focus loss metrics
    task_data_list = []
    for file in task_files:
        try:
            df = pd.read_csv(file)
            # Convert duration from string to seconds
            if 'windowFocusLostDuringTasksDuration' in df.columns:
                df['windowFocusLostDuringTasksDuration'] = pd.to_timedelta(
                    df['windowFocusLostDuringTasksDuration'], errors='coerce'
                ).dt.total_seconds().fillna(0)
            task_data_list.append(df)
        except Exception as e:
            print(f"Warning: Could not read {file}: {e}")
            continue
    
    if not task_data_list:
        print("ERROR: No task data files could be loaded")
        return None, None, None, None
    
    task_data_df = pd.concat(task_data_list, ignore_index=True)
    print("Task data - All columns:")
    print(task_data_df.columns.tolist())
    print("Task data - First 3 rows:")
    print(task_data_df.head(3))
    
    # Check required columns for task data
    required_task_cols = ['participantId', 'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration']
    missing_task_cols = [col for col in required_task_cols if col not in task_data_df.columns]
    if missing_task_cols:
        print(f"ERROR: Missing required task data columns: {missing_task_cols}")
        return None, None, None, None
    
    # Aggregate focus loss metrics by participant
    focus_metrics = task_data_df.groupby('participantId').agg({
        'windowFocusLostDuringTasksNum': 'max',
        'windowFocusLostDuringTasksDuration': 'max'
    }).reset_index()
    
    print(f"Focus metrics aggregated for {len(focus_metrics)} participants")
    print("Focus metrics - First 2 rows:")
    print(focus_metrics.head(2))
    
    return vwm_filtered, vviq2_df, summary_metrics_df, focus_metrics

def merge_datasets(vwm_df, vviq2_df, summary_df, focus_df):
    """
    Merge all datasets on participantId ensuring complete cases.
    
    Parameters:
    vwm_df (DataFrame): VWM parameters data
    vviq2_df (DataFrame): VVIQ2 scores data
    summary_df (DataFrame): Summary metrics data
    focus_df (DataFrame): Focus loss metrics data
    
    Returns:
    DataFrame: Merged dataset with complete cases
    """
    print("\n=== Merging datasets ===")
    
    print(f"VWM data participants: {len(vwm_df)}")
    print(f"VVIQ2 data participants: {len(vviq2_df)}")
    print(f"Summary data participants: {len(summary_df)}")
    print(f"Focus data participants: {len(focus_df)}")
    
    # Start with VWM data (already filtered)
    merged_df = vwm_df.copy()
    print(f"Starting with VWM data: {len(merged_df)} participants")
    
    # Merge with VVIQ2 data
    merged_df = merged_df.merge(vviq2_df, on='participantId', how='inner')
    print(f"After merging VVIQ2 data: {len(merged_df)} participants")
    
    # Merge with summary metrics
    merged_df = merged_df.merge(summary_df, on='participantId', how='inner')
    print(f"After merging summary metrics: {len(merged_df)} participants")
    
    # Merge with focus metrics
    merged_df = merged_df.merge(focus_df, on='participantId', how='inner')
    print(f"After merging focus metrics: {len(merged_df)} participants")
    
    # Check for complete cases
    print("\nChecking for missing values in key variables:")
    key_vars = ['kappa_vonmises', 'guess_rate_proportion', 'mean_vwm_absolute_error', 
               'windowFocusLostDuringTasksNum', 'total_score_standardized']
    
    for var in key_vars:
        missing = merged_df[var].isna().sum()
        print(f"{var}: {missing} missing values")
    
    # Remove rows with missing values in key variables
    before_dropna = len(merged_df)
    merged_df = merged_df.dropna(subset=key_vars)
    after_dropna = len(merged_df)
    print(f"Removed {before_dropna - after_dropna} participants with missing key variables")
    print(f"Final dataset: {after_dropna} participants")
    
    print("\nFinal merged dataset - All columns:")
    print(merged_df.columns.tolist())
    print("Final merged dataset - First 2 rows:")
    print(merged_df.head(2))
    
    return merged_df


def fit_robust_regression_models(merged_df):
    """
    Fit robust multiple regression models using statsmodels' RLM (Huber M-estimator).
    
    Parameters:
    merged_df (DataFrame): Merged dataset
    
    Returns:
    tuple: (results_list, diagnostics_list)
    """
    print("\n=== Fitting robust regression models (Python/statsmodels) ===")
    
    # Define outcome variables
    outcomes = [
        ('total_score_standardized', 'Total VVIQ2'),
        ('face_person_standardized', 'Face/Person'),
        ('sunrise_standardized', 'Sunrise'),
        ('shop_standardized', 'Shop'),
        ('countryside_standardized', 'Countryside'),
        ('car_road_standardized', 'Car/Road'),
        ('beach_standardized', 'Beach'),
        ('station_standardized', 'Station'),
        ('garden_standardized', 'Garden')
    ]
    
    # Prepare predictors
    predictors = ['kappa_vonmises', 'mean_vwm_absolute_error', 'guess_rate_proportion', 'windowFocusLostDuringTasksNum']
    
    results_list = []
    diagnostics_list = []
    
    for outcome_var, outcome_name in outcomes:
        print(f"\nFitting model for {outcome_name} ({outcome_var})")
        formula_str = f"{outcome_var} ~ {' + '.join(predictors)}"
        print(f"Formula: {formula_str}")
        try:
            model = smf.rlm(formula_str, data=merged_df, M=sm.robust.norms.TukeyBiweight())
            result = model.fit()
            
            # Extract coefficients and statistics
            coef_names = result.params.index.tolist()
            coefficients = result.params.values
            std_errors = result.bse.values
            t_values = result.tvalues.values
            # p-values are not provided by RLM; use normal approximation
            p_values = 2 * (1 - scipy_stats.norm.cdf(np.abs(t_values)))
            
            # Confidence intervals (normal approx)
            ci = result.conf_int()
            ci_lower = ci[0].values
            ci_upper = ci[1].values
            
            # Residuals and fitted values
            residuals = result.resid
            fitted_values = result.fittedvalues
            n_obs = len(fitted_values)
            
            # Robust weights
            weights = result.weights if hasattr(result, "weights") else np.ones(n_obs)
            
            # Standardized coefficients (excluding intercept)
            outcome_sd = merged_df[outcome_var].std()
            predictor_sds = {pred: merged_df[pred].std() for pred in predictors}
            
            # Pseudo R-squared (squared correlation between fitted and observed)
            try:
                r_squared = np.corrcoef(merged_df[outcome_var], fitted_values)[0, 1] ** 2
            except Exception:
                r_squared = np.nan
            
            # Cohen's f-squared for each predictor
            for i, coef_name in enumerate(coef_names):
                if coef_name != 'Intercept' and coef_name != '(Intercept)':
                    # Standardized coefficient
                    if coef_name in predictor_sds and outcome_sd > 0:
                        std_coef = coefficients[i] * (predictor_sds[coef_name] / outcome_sd)
                    else:
                        std_coef = np.nan
                    
                    # Cohen's f-squared: fit reduced model without this predictor
                    reduced_predictors = [p for p in predictors if p != coef_name]
                    if reduced_predictors:
                        reduced_formula = f"{outcome_var} ~ {' + '.join(reduced_predictors)}"
                        reduced_model = smf.rlm(reduced_formula, data=merged_df, M=sm.robust.norms.TukeyBiweight())
                        reduced_result = reduced_model.fit()
                        try:
                            reduced_r2 = np.corrcoef(merged_df[outcome_var], reduced_result.fittedvalues)[0, 1] ** 2
                        except Exception:
                            reduced_r2 = np.nan
                        if not np.isnan(r_squared) and not np.isnan(reduced_r2) and r_squared < 1:
                            cohens_f_squared = (r_squared - reduced_r2) / (1 - r_squared)
                        else:
                            cohens_f_squared = np.nan
                    else:
                        if not np.isnan(r_squared) and r_squared < 1:
                            cohens_f_squared = r_squared / (1 - r_squared)
                        else:
                            cohens_f_squared = np.nan
                    
                    results_list.append({
                        'model_name': f"Model_{outcome_name.replace('/', '_').replace(' ', '_')}",
                        'outcome_variable': outcome_var,
                        'predictor_name': coef_name,
                        'coefficient': coefficients[i],
                        'robust_standard_error': std_errors[i],
                        't_statistic': t_values[i],
                        'p_value': p_values[i],
                        'confidence_interval_lower': ci_lower[i],
                        'confidence_interval_upper': ci_upper[i],
                        'standardized_coefficient': std_coef,
                        'cohens_f_squared': cohens_f_squared
                    })
            
            # Leverage and influence
            try:
                ols_model = smf.ols(formula_str, data=merged_df).fit()
                influence = OLSInfluence(ols_model)
                hat_values = influence.hat_matrix_diag
                leverage_threshold = 2 * (len(predictors) + 1) / n_obs
                leverage_points = int(np.sum(hat_values > leverage_threshold))
            except Exception as e_hat:
                print(f"Warning: Could not compute leverage: {e_hat}")
                leverage_points = np.nan
            
            # Outliers and influential observations (using robust weights)
            outliers = np.sum(weights < 0.95)
            influential_obs = np.sum(weights < 0.5)
            
            # Normality test on residuals
            try:
                _, normality_p = scipy_stats.shapiro(residuals[:min(5000, len(residuals))])
            except Exception as e_shapiro:
                print(f"Warning: Shapiro-Wilk test failed: {e_shapiro}")
                normality_p = np.nan
            
            diagnostics_list.append({
                'model_name': f"Model_{outcome_name.replace('/', '_').replace(' ', '_')}",
                'outcome_variable': outcome_var,
                'robust_r_squared': r_squared,
                'adjusted_r_squared': 1 - (1 - r_squared) * (n_obs - 1) / (n_obs - len(predictors) - 1) if not np.isnan(r_squared) and n_obs > len(predictors) + 1 else np.nan,
                'residual_standard_error': np.std(residuals, ddof=1),
                'num_observations': n_obs,
                'num_outliers_detected': outliers,
                'leverage_points': leverage_points,
                'influential_observations': influential_obs,
                'normality_test_p_value': normality_p
            })
            
            print(f"Model fitted successfully. Pseudo R² = {r_squared:.4f}, n = {n_obs}")
            
            # Print key results for kappa_vonmises
            kappa_idx = None
            for i, name in enumerate(coef_names):
                if name == 'kappa_vonmises':
                    kappa_idx = i
                    break
            if kappa_idx is not None:
                print(f"κ coefficient: {coefficients[kappa_idx]:.4f} (SE: {std_errors[kappa_idx]:.4f}, p: {p_values[kappa_idx]:.4f})")
                if p_values[kappa_idx] < 0.05:
                    direction = "positive" if coefficients[kappa_idx] > 0 else "negative"
                    print(f"Significant {direction} association with imagery vividness!")
        except Exception as e:
            import traceback
            print(f"ERROR fitting model for {outcome_name}: {e}")
            traceback.print_exc()
            continue
    
    return results_list, diagnostics_list

def save_results(results_list, diagnostics_list):
    """
    Save regression results and diagnostics to CSV files.
    
    Parameters:
    results_list (list): List of regression results
    diagnostics_list (list): List of model diagnostics
    """
    print("\n=== Saving results ===")
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save regression results
    if results_list:
        results_df = pd.DataFrame(results_list)
        results_filename = f"outputs/VVIQ2_robust_regression_results_{timestamp}.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"Regression results saved to: {results_filename}")
        print(f"Results shape: {results_df.shape}")
        print("Results columns:")
        print(results_df.columns.tolist())
        print("First 2 rows of results:")
        print(results_df.head(2))
    else:
        print("No regression results to save")
    
    # Save model diagnostics
    if diagnostics_list:
        diagnostics_df = pd.DataFrame(diagnostics_list)
        diagnostics_filename = f"outputs/VVIQ2_model_diagnostics_{timestamp}.csv"
        diagnostics_df.to_csv(diagnostics_filename, index=False)
        print(f"Model diagnostics saved to: {diagnostics_filename}")
        print(f"Diagnostics shape: {diagnostics_df.shape}")
        print("Diagnostics columns:")
        print(diagnostics_df.columns.tolist())
        print("First 2 rows of diagnostics:")
        print(diagnostics_df.head(2))
    else:
        print("No model diagnostics to save")

def analyze_hypothesis(results_list):
    """
    Analyze the specific hypothesis about κ predicting imagery vividness.
    
    Parameters:
    results_list (list): List of regression results
    """
    print("\n=== Hypothesis Analysis: H2 - Higher κ predicts higher imagery vividness ===")
    
    # Filter results for kappa_vonmises predictor
    kappa_results = [r for r in results_list if r['predictor_name'] == 'kappa_vonmises']
    
    if not kappa_results:
        print("No results found for kappa_vonmises predictor")
        return
    
    print(f"Found {len(kappa_results)} models with kappa_vonmises predictor")
    
    # Analyze each outcome
    significant_positive = 0
    significant_negative = 0
    non_significant = 0
    
    for result in kappa_results:
        outcome = result['outcome_variable']
        coef = result['coefficient']
        p_val = result['p_value']
        ci_lower = result['confidence_interval_lower']
        ci_upper = result['confidence_interval_upper']
        
        print(f"\n{outcome}:")
        print(f"  Coefficient: {coef:.4f}")
        print(f"  95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"  p-value: {p_val:.4f}")
        
        if p_val < 0.05:
            if coef > 0:
                print(f"  Result: SIGNIFICANT POSITIVE association (supports H2)")
                significant_positive += 1
            else:
                print(f"  Result: SIGNIFICANT NEGATIVE association (contradicts H2)")
                significant_negative += 1
        else:
            print(f"  Result: Non-significant")
            non_significant += 1
    
    print(f"\n=== SUMMARY ===")
    print(f"Significant positive associations: {significant_positive}/{len(kappa_results)}")
    print(f"Significant negative associations: {significant_negative}/{len(kappa_results)}")
    print(f"Non-significant associations: {non_significant}/{len(kappa_results)}")
    
    if significant_positive > 0:
        print("H2 is SUPPORTED for at least some VVIQ2 subscales")
    elif significant_negative > 0:
        print("H2 is CONTRADICTED - found negative associations")
    else:
        print("H2 is NOT SUPPORTED - no significant associations found")

def main():
    """
    Main function to execute the robust regression analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 robust regression analysis...")
        
        # Load and validate data
        vwm_df, vviq2_df, summary_df, focus_df = load_and_validate_data()
        if vwm_df is None:
            print("ERROR: Failed to load required data files")
            return 1
        
        # Merge datasets
        merged_df = merge_datasets(vwm_df, vviq2_df, summary_df, focus_df)
        if len(merged_df) == 0:
            print("ERROR: No participants remaining after merging datasets")
            return 1
        
        # Fit robust regression models (Python/statsmodels)
        results_list, diagnostics_list = fit_robust_regression_models(
            merged_df
        )
        
        if not results_list:
            print("ERROR: No regression models were fitted successfully")
            return 1
        
        # Analyze hypothesis
        analyze_hypothesis(results_list)
        
        # Save results
        save_results(results_list, diagnostics_list)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
