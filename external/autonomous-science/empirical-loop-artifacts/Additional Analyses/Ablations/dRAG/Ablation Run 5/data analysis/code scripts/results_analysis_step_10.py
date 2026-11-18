#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

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
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def load_input_files():
    """
    Load all required input files with timestamp pattern matching.
    
    Returns:
    tuple: (precision_df, metrics_df, vviq_df) or (None, None, None) if files not found
    """
    print("=== LOADING INPUT FILES ===")
    
    # Find most recent files
    precision_pattern = "outputs/final_precision_parameters_*.csv"
    metrics_pattern = "outputs/domain_general_metrics_*.csv"
    vviq_pattern = "outputs/VVIQ2_cleaned_scores_*.csv"
    
    precision_file = find_most_recent_file(precision_pattern)
    metrics_file = find_most_recent_file(metrics_pattern)
    vviq_file = find_most_recent_file(vviq_pattern)
    
    print(f"Precision parameters file: {precision_file}")
    print(f"Domain general metrics file: {metrics_file}")
    print(f"VVIQ2 scores file: {vviq_file}")
    
    if not all([precision_file, metrics_file, vviq_file]):
        print("ERROR: One or more input files not found!")
        return None, None, None
    
    # Load precision parameters
    print("\n--- Loading precision parameters ---")
    precision_df = pd.read_csv(precision_file)
    precision_df.columns = precision_df.columns.str.strip()
    print(f"Precision parameters shape: {precision_df.shape}")
    print("Columns:", list(precision_df.columns))
    print("First 3 rows:")
    print(precision_df.head(3))
    
    # Check excluded_outlier unique values
    print("Unique values in excluded_outlier:", precision_df['excluded_outlier'].unique())
    
    # Load domain general metrics
    print("\n--- Loading domain general metrics ---")
    metrics_df = pd.read_csv(metrics_file)
    metrics_df.columns = metrics_df.columns.str.strip()
    print(f"Domain general metrics shape: {metrics_df.shape}")
    print("Columns:", list(metrics_df.columns))
    print("First 3 rows:")
    print(metrics_df.head(3))
    
    # Load VVIQ2 scores
    print("\n--- Loading VVIQ2 scores ---")
    vviq_df = pd.read_csv(vviq_file)
    vviq_df.columns = vviq_df.columns.str.strip()
    print(f"VVIQ2 scores shape: {vviq_df.shape}")
    print("Columns:", list(vviq_df.columns))
    print("First 3 rows:")
    print(vviq_df.head(3))
    
    # Check excluded_VVIQ2 unique values
    print("Unique values in excluded_VVIQ2:", vviq_df['excluded_VVIQ2'].unique())
    
    return precision_df, metrics_df, vviq_df

def prepare_analysis_dataset(precision_df, metrics_df, vviq_df):
    """
    Merge datasets and apply exclusion criteria for regression analysis.
    
    Parameters:
    precision_df (pd.DataFrame): Precision parameters data
    metrics_df (pd.DataFrame): Domain general metrics data
    vviq_df (pd.DataFrame): VVIQ2 scores data
    
    Returns:
    pd.DataFrame: Merged and filtered dataset ready for analysis
    """
    print("\n=== PREPARING ANALYSIS DATASET ===")
    
    # Start with precision parameters and filter for included participants
    print(f"Initial precision parameters: {len(precision_df)} participants")
    precision_included = precision_df[precision_df['excluded_outlier'] == False].copy()
    print(f"After outlier exclusions: {len(precision_included)} participants")
    
    # Merge with domain general metrics
    merged_df = precision_included.merge(metrics_df, on='participantId', how='inner')
    print(f"After merging with domain general metrics: {len(merged_df)} participants")
    
    # Merge with VVIQ2 scores
    merged_df = merged_df.merge(vviq_df, on='participantId', how='inner')
    print(f"After merging with VVIQ2 scores: {len(merged_df)} participants")
    
    # Apply VVIQ2 exclusions
    analysis_df = merged_df[merged_df['excluded_VVIQ2'] == False].copy()
    print(f"After VVIQ2 exclusions: {len(analysis_df)} participants")
    
    # Check minimum sample size
    if len(analysis_df) < 200:
        print(f"WARNING: Sample size ({len(analysis_df)}) is below minimum requirement (n=200)")
    else:
        print(f"Sample size adequate: n={len(analysis_df)}")
    
    # Select required columns for analysis
    required_columns = [
        'participantId', 'final_concentration_kappa',
        'total_score', 'familiar_person_score', 'sunrise_score', 'shop_front_score',
        'countryside_score', 'driving_score', 'beach_score', 'railway_station_score',
        'garden_score', 'VWM_median_rt_z', 'MRT_median_rt_z', 'VWM_accuracy_z',
        'MRT_accuracy_z', 'session_duration_z', 'focus_loss_duration_z', 'focus_loss_instances_z'
    ]
    
    analysis_df = analysis_df[required_columns].copy()
    
    print("\nFinal analysis dataset:")
    print(f"Shape: {analysis_df.shape}")
    print("Columns:", list(analysis_df.columns))
    print("First 2 rows:")
    print(analysis_df.head(2))
    
    # Check for missing values
    missing_counts = analysis_df.isnull().sum()
    if missing_counts.sum() > 0:
        print("\nWARNING: Missing values detected. Dropping rows with missing data.")
        print(missing_counts[missing_counts > 0])
        original_rows = len(analysis_df)
        
        # Define predictor columns that cannot have missing values
        predictor_columns = [
            'final_concentration_kappa', 'VWM_median_rt_z', 'MRT_median_rt_z',
            'VWM_accuracy_z', 'MRT_accuracy_z', 'session_duration_z',
            'focus_loss_duration_z', 'focus_loss_instances_z'
        ]
        
        # Remove participants with missing values in predictor variables
        analysis_df = analysis_df.dropna(subset=predictor_columns)
        print(f"Dropped {original_rows - len(analysis_df)} rows due to missing predictor data")
        print(f"Final sample size after missing data removal: {len(analysis_df)}")
        
        # Verify no missing values remain in predictors
        remaining_missing = analysis_df[predictor_columns].isnull().sum().sum()
        if remaining_missing > 0:
            print(f"ERROR: {remaining_missing} missing values remain in predictors after cleaning")
            return None
        else:
            print("Confirmed: No missing values in predictor variables")
    else:
        print("\nNo missing values detected")
    
    return analysis_df

def fit_regression_model(df, outcome_var, predictors):
    """
    Fit multiple linear regression model and return comprehensive results.
    
    Parameters:
    df (pd.DataFrame): Analysis dataset
    outcome_var (str): Name of outcome variable
    predictors (list): List of predictor variable names
    
    Returns:
    dict: Dictionary containing model results and diagnostics
    """
    # Prepare data
    y = df[outcome_var]
    X = df[predictors]

    # Validate data before fitting
    if X.isnull().any().any() or np.isinf(X).any().any():
        raise ValueError("Predictor variables contain NaN or inf values")
    if y.isnull().any() or np.isinf(y).any():
        raise ValueError("Outcome variable contains NaN or inf values")

    X_with_intercept = sm.add_constant(X)
    
    # Fit model
    model = sm.OLS(y, X_with_intercept).fit()
    
    # Calculate standardized coefficients
    X_std = (X - X.mean()) / X.std()
    y_std = (y - y.mean()) / y.std()
    X_std_with_intercept = sm.add_constant(X_std)
    model_std = sm.OLS(y_std, X_std_with_intercept).fit()
    
    # Extract results
    results = {
        'model': model,
        'model_std': model_std,
        'outcome_var': outcome_var,
        'predictors': predictors,
        'n_participants': len(df),
        'r_squared': model.rsquared,
        'adjusted_r_squared': model.rsquared_adj,
        'f_statistic': model.fvalue,
        'f_p_value': model.f_pvalue,
        'coefficients': model.params,
        'std_errors': model.bse,
        'standardized_betas': model_std.params,
        't_values': model.tvalues,
        'p_values': model.pvalues,
        'conf_int': model.conf_int()
    }
    
    return results

def calculate_effect_size(standardized_beta):
    """
    Categorize effect size based on Cohen's conventions for standardized coefficients.
    
    Parameters:
    standardized_beta (float): Standardized regression coefficient
    
    Returns:
    str: Effect size category
    """
    abs_beta = abs(standardized_beta)
    if abs_beta < 0.1:
        return "negligible"
    elif abs_beta < 0.3:
        return "small"
    elif abs_beta < 0.5:
        return "medium"
    else:
        return "large"

def perform_model_diagnostics(model_results):
    """
    Perform model diagnostics including outlier detection and multicollinearity assessment.
    
    Parameters:
    model_results (dict): Results from fit_regression_model
    
    Returns:
    dict: Diagnostic results
    """
    model = model_results['model']
    
    # Calculate Cook's distance
    influence = model.get_influence()
    cooks_d = influence.cooks_distance[0]
    
    # Calculate VIF for multicollinearity
    X = model.model.exog[:, 1:]  # Exclude intercept
    vif_data = pd.DataFrame()
    vif_data["Variable"] = model_results['predictors']
    vif_data["VIF"] = [variance_inflation_factor(X, i) for i in range(X.shape[1])]
    
    diagnostics = {
        'cooks_distance_max': np.max(cooks_d),
        'cooks_distance_outliers': np.sum(cooks_d > 4/len(cooks_d)),
        'vif_data': vif_data,
        'vif_max': vif_data["VIF"].max(),
        'multicollinearity_concern': vif_data["VIF"].max() > 10
    }
    
    return diagnostics

def run_primary_analysis(df):
    """
    Run primary analysis: VVIQ2 total score regression.
    
    Parameters:
    df (pd.DataFrame): Analysis dataset
    
    Returns:
    dict: Primary analysis results
    """
    print("\n=== PRIMARY ANALYSIS: VVIQ2 TOTAL SCORE ===")
    
    predictors = [
        'final_concentration_kappa', 'VWM_median_rt_z', 'MRT_median_rt_z',
        'VWM_accuracy_z', 'MRT_accuracy_z', 'session_duration_z',
        'focus_loss_duration_z', 'focus_loss_instances_z'
    ]
    
    results = fit_regression_model(df, 'total_score', predictors)
    
    print(f"Model R² = {results['r_squared']:.4f}")
    print(f"Adjusted R² = {results['adjusted_r_squared']:.4f}")
    print(f"F-statistic = {results['f_statistic']:.4f}, p = {results['f_p_value']:.6f}")
    print(f"N participants = {results['n_participants']}")
    
    # Focus on concentration parameter
    conc_idx = predictors.index('final_concentration_kappa') + 1  # +1 for intercept
    conc_coef = results['coefficients'].iloc[conc_idx]
    conc_se = results['std_errors'].iloc[conc_idx]
    conc_std_beta = results['standardized_betas'].iloc[conc_idx]
    conc_t = results['t_values'].iloc[conc_idx]
    conc_p = results['p_values'].iloc[conc_idx]
    
    print(f"\nConcentration parameter results:")
    print(f"  Coefficient: {conc_coef:.4f} ± {conc_se:.4f}")
    print(f"  Standardized β: {conc_std_beta:.4f}")
    print(f"  t-value: {conc_t:.4f}")
    print(f"  p-value: {conc_p:.6f}")
    print(f"  Effect size: {calculate_effect_size(conc_std_beta)}")
    
    # Significance test (α = 0.025 for primary analysis)
    significant = conc_p < 0.025
    print(f"  Significant at α = 0.025: {significant}")
    
    # Model diagnostics
    diagnostics = perform_model_diagnostics(results)
    print(f"\nModel diagnostics:")
    print(f"  Max Cook's distance: {diagnostics['cooks_distance_max']:.4f}")
    print(f"  Cook's distance outliers: {diagnostics['cooks_distance_outliers']}")
    print(f"  Max VIF: {diagnostics['vif_max']:.2f}")
    print(f"  Multicollinearity concern: {diagnostics['multicollinearity_concern']}")
    
    return results

def run_secondary_analyses(df):
    """
    Run secondary analyses: VVIQ2 subscale regressions with FDR correction.
    
    Parameters:
    df (pd.DataFrame): Analysis dataset
    
    Returns:
    dict: Secondary analysis results with FDR correction
    """
    print("\n=== SECONDARY ANALYSES: VVIQ2 SUBSCALES ===")
    
    subscales = [
        'familiar_person_score', 'sunrise_score', 'shop_front_score',
        'countryside_score', 'driving_score', 'beach_score',
        'railway_station_score', 'garden_score'
    ]
    
    predictors = [
        'final_concentration_kappa', 'VWM_median_rt_z', 'MRT_median_rt_z',
        'VWM_accuracy_z', 'MRT_accuracy_z', 'session_duration_z',
        'focus_loss_duration_z', 'focus_loss_instances_z'
    ]
    
    subscale_results = {}
    concentration_p_values = []
    
    for subscale in subscales:
        print(f"\n--- {subscale} ---")
        results = fit_regression_model(df, subscale, predictors)
        subscale_results[subscale] = results
        
        # Extract concentration parameter results
        conc_idx = predictors.index('final_concentration_kappa') + 1
        conc_p = results['p_values'].iloc[conc_idx]
        concentration_p_values.append(conc_p)
        
        print(f"R² = {results['r_squared']:.4f}")
        print(f"Concentration p-value: {conc_p:.6f}")
    
    # Apply FDR correction
    print(f"\n--- FDR CORRECTION ---")
    print(f"Concentration p-values: {concentration_p_values}")
    
    rejected, p_corrected, alpha_sidak, alpha_bonf = multipletests(
        concentration_p_values, alpha=0.05, method='fdr_bh'
    )
    
    print(f"FDR corrected p-values: {p_corrected}")
    print(f"Significant after FDR: {rejected}")
    print(f"Number significant after FDR: {np.sum(rejected)}")
    
    # Add FDR results to subscale_results
    for i, subscale in enumerate(subscales):
        subscale_results[subscale]['fdr_p_value'] = p_corrected[i]
        subscale_results[subscale]['fdr_significant'] = rejected[i]
    
    return subscale_results

def create_results_dataframe(primary_results, subscale_results):
    """
    Create comprehensive results dataframe for all analyses.
    
    Parameters:
    primary_results (dict): Primary analysis results
    subscale_results (dict): Secondary analysis results
    
    Returns:
    pd.DataFrame: Results dataframe
    """
    print("\n=== CREATING RESULTS DATAFRAME ===")
    
    results_list = []
    
    # Process primary analysis
    predictors = [
        'final_concentration_kappa', 'VWM_median_rt_z', 'MRT_median_rt_z',
        'VWM_accuracy_z', 'MRT_accuracy_z', 'session_duration_z',
        'focus_loss_duration_z', 'focus_loss_instances_z'
    ]
    
    for i, predictor in enumerate(predictors):
        idx = i + 1  # +1 for intercept
        
        # For primary analysis, only concentration gets FDR correction (which is just the original p-value)
        if predictor == 'final_concentration_kappa':
            fdr_p = primary_results['p_values'].iloc[idx]
            fdr_sig = fdr_p < 0.025  # Primary analysis uses α = 0.025
        else:
            fdr_p = primary_results['p_values'].iloc[idx]
            fdr_sig = fdr_p < 0.05
        
        results_list.append({
            'outcome_variable': 'total_score',
            'parameter': predictor,
            'estimate': primary_results['coefficients'].iloc[idx],
            'std_error': primary_results['std_errors'].iloc[idx],
            'standardized_beta': primary_results['standardized_betas'].iloc[idx],
            't_value': primary_results['t_values'].iloc[idx],
            'p_value': primary_results['p_values'].iloc[idx],
            'p_value_fdr_corrected': fdr_p,
            'ci_lower': primary_results['conf_int'].iloc[idx, 0],
            'ci_upper': primary_results['conf_int'].iloc[idx, 1],
            'significance_uncorrected': primary_results['p_values'].iloc[idx] < 0.05,
            'significance_fdr_corrected': fdr_sig
        })
    
    # Process subscale analyses
    for subscale, results in subscale_results.items():
        for i, predictor in enumerate(predictors):
            idx = i + 1  # +1 for intercept
            
            # For concentration parameter, use FDR corrected p-value
            if predictor == 'final_concentration_kappa':
                fdr_p = results['fdr_p_value']
                fdr_sig = results['fdr_significant']
            else:
                fdr_p = results['p_values'].iloc[idx]
                fdr_sig = fdr_p < 0.05
            
            results_list.append({
                'outcome_variable': subscale,
                'parameter': predictor,
                'estimate': results['coefficients'].iloc[idx],
                'std_error': results['std_errors'].iloc[idx],
                'standardized_beta': results['standardized_betas'].iloc[idx],
                't_value': results['t_values'].iloc[idx],
                'p_value': results['p_values'].iloc[idx],
                'p_value_fdr_corrected': fdr_p,
                'ci_lower': results['conf_int'].iloc[idx, 0],
                'ci_upper': results['conf_int'].iloc[idx, 1],
                'significance_uncorrected': results['p_values'].iloc[idx] < 0.05,
                'significance_fdr_corrected': fdr_sig
            })
    
    results_df = pd.DataFrame(results_list)
    
    print(f"Results dataframe shape: {results_df.shape}")
    print("Columns:", list(results_df.columns))
    print("First 2 rows:")
    print(results_df.head(2))
    
    return results_df

def create_model_summary_dataframe(primary_results, subscale_results):
    """
    Create model summary dataframe with key fit statistics.
    
    Parameters:
    primary_results (dict): Primary analysis results
    subscale_results (dict): Secondary analysis results
    
    Returns:
    pd.DataFrame: Model summary dataframe
    """
    print("\n=== CREATING MODEL SUMMARY DATAFRAME ===")
    
    summary_list = []
    
    # Primary analysis summary
    conc_std_beta = primary_results['standardized_betas'].iloc[1]  # concentration is first predictor
    effect_size = calculate_effect_size(conc_std_beta)
    
    summary_list.append({
        'outcome_variable': 'total_score',
        'r_squared': primary_results['r_squared'],
        'adjusted_r_squared': primary_results['adjusted_r_squared'],
        'f_statistic': primary_results['f_statistic'],
        'f_p_value': primary_results['f_p_value'],
        'n_participants': primary_results['n_participants'],
        'concentration_effect_size': effect_size
    })
    
    # Subscale summaries
    for subscale, results in subscale_results.items():
        conc_std_beta = results['standardized_betas'].iloc[1]
        effect_size = calculate_effect_size(conc_std_beta)
        
        summary_list.append({
            'outcome_variable': subscale,
            'r_squared': results['r_squared'],
            'adjusted_r_squared': results['adjusted_r_squared'],
            'f_statistic': results['f_statistic'],
            'f_p_value': results['f_p_value'],
            'n_participants': results['n_participants'],
            'concentration_effect_size': effect_size
        })
    
    summary_df = pd.DataFrame(summary_list)
    
    print(f"Model summary shape: {summary_df.shape}")
    print("Columns:", list(summary_df.columns))
    print("First 2 rows:")
    print(summary_df.head(2))
    
    return summary_df

def save_output_files(results_df, summary_df, analysis_df):
    """
    Save all output files with timestamp.
    
    Parameters:
    results_df (pd.DataFrame): Regression results
    summary_df (pd.DataFrame): Model summaries
    analysis_df (pd.DataFrame): Analysis dataset
    """
    print("\n=== SAVING OUTPUT FILES ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save files
    results_file = f"outputs/VVIQ2_regression_results_{timestamp}.csv"
    summary_file = f"outputs/VVIQ2_model_summary_{timestamp}.csv"
    dataset_file = f"outputs/VVIQ2_analysis_dataset_{timestamp}.csv"
    
    results_df.to_csv(results_file, index=False)
    print(f"Saved regression results: {results_file}")
    
    summary_df.to_csv(summary_file, index=False)
    print(f"Saved model summary: {summary_file}")
    
    analysis_df.to_csv(dataset_file, index=False)
    print(f"Saved analysis dataset: {dataset_file}")
    
    print(f"\nAll output files saved with timestamp: {timestamp}")

def main():
    """
    Main function to execute VVIQ2 regression analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 regression analysis...")
        
        # Load input files
        precision_df, metrics_df, vviq_df = load_input_files()
        if precision_df is None:
            print("ERROR: Failed to load input files")
            return 1
        
        # Prepare analysis dataset
        analysis_df = prepare_analysis_dataset(precision_df, metrics_df, vviq_df)
        if len(analysis_df) == 0:
            print("ERROR: No participants remaining after exclusions")
            return 1
        
        # Run primary analysis
        primary_results = run_primary_analysis(analysis_df)
        
        # Run secondary analyses
        subscale_results = run_secondary_analyses(analysis_df)
        
        # Create results dataframes
        results_df = create_results_dataframe(primary_results, subscale_results)
        summary_df = create_model_summary_dataframe(primary_results, subscale_results)
        
        # Save output files
        save_output_files(results_df, summary_df, analysis_df)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
