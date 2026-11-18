import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

def get_most_recent_file(pattern):
    """
    Get the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_and_validate_data():
    """
    Load and validate all required input files.
    
    Returns:
    tuple: (facilitation_df, vviq_df, mrt_data_df) or (None, None, None) if error
    """
    print("Loading input files...")
    
    # Load MRT sequential facilitation indices
    facilitation_pattern = "outputs/MRT_sequential_facilitation_indices_*.csv"
    facilitation_file = get_most_recent_file(facilitation_pattern)
    if not facilitation_file:
        print(f"Error: No file found matching pattern {facilitation_pattern}")
        return None, None, None
    
    print(f"Loading facilitation file: {facilitation_file}")
    facilitation_df = pd.read_csv(facilitation_file)
    print("Facilitation data columns:", facilitation_df.columns.tolist())
    print("First 3 rows of facilitation data:")
    print(facilitation_df.head(3))
    
    # Validate required columns
    required_facilitation_cols = ['participantId', 'rt_facilitation_slope', 'accuracy_facilitation_index', 'sufficient_data']
    missing_cols = [col for col in required_facilitation_cols if col not in facilitation_df.columns]
    if missing_cols:
        print(f"Error: Missing columns in facilitation file: {missing_cols}")
        return None, None, None
    
    # Load VVIQ2 cleaned scores
    vviq_pattern = "outputs/VVIQ2_cleaned_scores_*.csv"
    vviq_file = get_most_recent_file(vviq_pattern)
    if not vviq_file:
        print(f"Error: No file found matching pattern {vviq_pattern}")
        return None, None, None
    
    print(f"Loading VVIQ file: {vviq_file}")
    vviq_df = pd.read_csv(vviq_file)
    print("VVIQ data columns:", vviq_df.columns.tolist())
    print("First 3 rows of VVIQ data:")
    print(vviq_df.head(3))
    
    # Validate required columns
    required_vviq_cols = ['PROLIFIC_PID', 'total_score_z', 'excluded_participant']
    missing_cols = [col for col in required_vviq_cols if col not in vviq_df.columns]
    if missing_cols:
        print(f"Error: Missing columns in VVIQ file: {missing_cols}")
        return None, None, None
    
    # Load MRT cleaned data
    mrt_pattern = "outputs/MRT_cleaned_data_*.csv"
    mrt_file = get_most_recent_file(mrt_pattern)
    if not mrt_file:
        print(f"Error: No file found matching pattern {mrt_pattern}")
        return None, None, None
    
    print(f"Loading MRT data file: {mrt_file}")
    mrt_data_df = pd.read_csv(mrt_file)
    print("MRT data columns:", mrt_data_df.columns.tolist())
    print("First 3 rows of MRT data:")
    print(mrt_data_df.head(3))
    
    # Validate required columns
    required_mrt_cols = ['participantId', 'trial_type', 'MRT_rt_ms', 'MRT_isCorrect', 'excluded_trial']
    missing_cols = [col for col in required_mrt_cols if col not in mrt_data_df.columns]
    if missing_cols:
        print(f"Error: Missing columns in MRT data file: {missing_cols}")
        return None, None, None
    
    # Print unique values for key experimental design columns
    print("\nUnique values in key columns:")
    print("trial_type values:", mrt_data_df['trial_type'].unique())
    print("sufficient_data values:", facilitation_df['sufficient_data'].unique())
    print("excluded_participant values:", vviq_df['excluded_participant'].unique())
    print("excluded_trial values:", mrt_data_df['excluded_trial'].unique())
    
    return facilitation_df, vviq_df, mrt_data_df

def merge_datasets(facilitation_df, vviq_df):
    """
    Merge facilitation and VVIQ datasets, applying inclusion criteria.
    
    Parameters:
    facilitation_df (pd.DataFrame): MRT facilitation indices
    vviq_df (pd.DataFrame): VVIQ2 scores
    
    Returns:
    pd.DataFrame: Merged dataset with valid participants only
    """
    print("\nMerging datasets...")
    
    # Filter for valid participants
    print("Applying inclusion criteria...")
    valid_facilitation = facilitation_df[facilitation_df['sufficient_data'] == True].copy()
    valid_vviq = vviq_df[vviq_df['excluded_participant'] == False].copy()
    
    print(f"Participants with sufficient MRT data: {len(valid_facilitation)}")
    print(f"Non-excluded VVIQ participants: {len(valid_vviq)}")
    
    # Merge datasets
    merged_df = pd.merge(
        valid_facilitation,
        valid_vviq,
        left_on='participantId',
        right_on='PROLIFIC_PID',
        how='inner'
    )
    
    print(f"Final merged dataset: {len(merged_df)} participants")
    print("Merged data columns:", merged_df.columns.tolist())
    print("First 2 rows of merged data:")
    print(merged_df.head(2))
    
    if len(merged_df) < 20:
        print("Warning: Small sample size for regression analyses")
    
    return merged_df

def calculate_baseline_performance(mrt_data_df, participant_ids):
    """
    Calculate baseline task performance measures for each participant.
    
    Parameters:
    mrt_data_df (pd.DataFrame): MRT trial-level data
    participant_ids (list): List of participant IDs to calculate for
    
    Returns:
    pd.DataFrame: Baseline performance measures per participant
    """
    print("\nCalculating baseline task performance...")
    
    # Filter for test trials and valid data
    test_trials = mrt_data_df[
        (mrt_data_df['trial_type'] == 'test') & 
        (mrt_data_df['excluded_trial'] == False) &
        (mrt_data_df['participantId'].isin(participant_ids))
    ].copy()
    
    print(f"Valid test trials for analysis: {len(test_trials)}")
    
    # Calculate baseline measures per participant
    baseline_stats = []
    
    for participant in participant_ids:
        p_data = test_trials[test_trials['participantId'] == participant]
        
        if len(p_data) > 0:
            mean_rt = p_data['MRT_rt_ms'].mean()
            accuracy = p_data['MRT_isCorrect'].mean()
            
            baseline_stats.append({
                'participantId': participant,
                'mean_rt_ms': mean_rt,
                'overall_accuracy': accuracy,
                'n_trials': len(p_data)
            })
    
    baseline_df = pd.DataFrame(baseline_stats)
    print(f"Baseline performance calculated for {len(baseline_df)} participants")
    print("Baseline performance columns:", baseline_df.columns.tolist())
    print("First 2 rows of baseline performance:")
    print(baseline_df.head(2))
    
    return baseline_df

def setup_r_environment():
    """
    Setup R environment for regression analyses.
    
    Returns:
    tuple: (rpy2.robjects, rpy2.robjects.pandas2ri) or (None, None) if error
    """
    try:
        import rpy2.robjects as ro
        from rpy2.robjects import pandas2ri
        from rpy2.robjects.packages import importr
        
        # Activate pandas conversion
        pandas2ri.activate()
        
        # Import required R packages
        base = importr('base')
        stats = importr('stats')
        
        print("R environment setup successful")
        return ro, pandas2ri
        
    except Exception as e:
        print(f"Error setting up R environment: {e}")
        return None, None

def fit_regression_models(analysis_df, ro):
    """
    Fit multiple regression models using R.
    
    Parameters:
    analysis_df (pd.DataFrame): Analysis dataset
    ro: rpy2.robjects module
    
    Returns:
    list: List of regression results
    """
    print("\nFitting regression models...")
    
    # Convert to R dataframe
    r_df = ro.conversion.py2rpy(analysis_df)
    ro.globalenv['analysis_data'] = r_df

    # Install and load required R packages
    ro.r('''
    if (!requireNamespace("lm.beta", quietly = TRUE)) {
      install.packages("lm.beta", repos = "https://cloud.r-project.org")
    }
    library(lm.beta)
    ''')

    results = []
    
    # Model 1: RT Facilitation Slope ~ VVIQ2_z
    print("Fitting Model 1: RT Facilitation Slope ~ VVIQ2_z")
    ro.r('''
    model1 <- lm(rt_facilitation_slope ~ total_score_z, data = analysis_data)
    model1_summary <- summary(model1)
    model1_confint <- confint(model1)
    model1_beta <- lm.beta(model1)
    model1_beta_summary <- summary(model1_beta)
    ''')
    
    # Extract results for Model 1
    model1_coef = ro.r('model1_summary$coefficients')
    model1_ci = ro.r('model1_confint')
    model1_beta_coef_r_matrix = ro.r('model1_beta_summary$coefficients')
    model1_r2 = ro.r('model1_summary$r.squared')[0]
    model1_adj_r2 = ro.r('model1_summary$adj.r.squared')[0]
    
    # Extract standardized coefficients directly from lm.beta object
    model1_beta_coef = ro.r('coef(model1_beta)')
    
    # Process Model 1 results
    coef_names = ['(Intercept)', 'total_score_z']
    for i, coef_name in enumerate(coef_names):
        # Get standardized estimate (NaN for intercept)
        if coef_name == '(Intercept)':
            std_estimate = np.nan
        else:
            try:
                # For non-intercept predictors, extract from beta coefficients (skip intercept index)
                std_estimate = model1_beta_coef[i-1]
            except (IndexError, TypeError) as e:
                print(f"Warning: Could not extract standardized coefficient for '{coef_name}' in Model 1: {e}")
                std_estimate = np.nan

        results.append({
            'model_name': 'RT_Facilitation_Main',
            'predictor': coef_name,
            'estimate': model1_coef[i][0],
            'std_error': model1_coef[i][1],
            'standardized_estimate': std_estimate,
            'ci_lower': model1_ci[i][0],
            'ci_upper': model1_ci[i][1],
            't_value': model1_coef[i][2],
            'p_value': model1_coef[i][3],
            'r_squared': model1_r2,
            'adjusted_r_squared': model1_adj_r2
        })
    
    # Model 2: Accuracy Facilitation Index ~ VVIQ2_z
    print("Fitting Model 2: Accuracy Facilitation Index ~ VVIQ2_z")
    ro.r('''
    model2 <- lm(accuracy_facilitation_index ~ total_score_z, data = analysis_data)
    model2_summary <- summary(model2)
    model2_confint <- confint(model2)
    model2_beta <- lm.beta(model2)
    model2_beta_summary <- summary(model2_beta)
    ''')
    
    # Extract results for Model 2
    model2_coef = ro.r('model2_summary$coefficients')
    model2_ci = ro.r('model2_confint')
    model2_beta_coef_r_matrix = ro.r('model2_beta_summary$coefficients')
    model2_r2 = ro.r('model2_summary$r.squared')[0]
    model2_adj_r2 = ro.r('model2_summary$adj.r.squared')[0]
    
    # Extract standardized coefficients directly from lm.beta object
    model2_beta_coef = ro.r('coef(model2_beta)')
    
    # Process Model 2 results
    for i, coef_name in enumerate(coef_names):
        # Get standardized estimate (NaN for intercept)
        if coef_name == '(Intercept)':
            std_estimate = np.nan
        else:
            try:
                # For non-intercept predictors, extract from beta coefficients (skip intercept index)
                std_estimate = model2_beta_coef[i-1]
            except (IndexError, TypeError) as e:
                print(f"Warning: Could not extract standardized coefficient for '{coef_name}' in Model 2: {e}")
                std_estimate = np.nan
        
        results.append({
            'model_name': 'Accuracy_Facilitation_Main',
            'predictor': coef_name,
            'estimate': model2_coef[i][0],
            'std_error': model2_coef[i][1],
            'standardized_estimate': std_estimate,
            'ci_lower': model2_ci[i][0],
            'ci_upper': model2_ci[i][1],
            't_value': model2_coef[i][2],
            'p_value': model2_coef[i][3],
            'r_squared': model2_r2,
            'adjusted_r_squared': model2_adj_r2
        })
    
    # Model 3: RT Facilitation with interactions
    print("Fitting Model 3: RT Facilitation with baseline performance interactions")
    ro.r('''
    model3 <- lm(rt_facilitation_slope ~ total_score_z + mean_rt_ms + overall_accuracy + 
                 total_score_z:mean_rt_ms + total_score_z:overall_accuracy, data = analysis_data)
    model3_summary <- summary(model3)
    model3_confint <- confint(model3)
    model3_beta <- lm.beta(model3)
    model3_beta_summary <- summary(model3_beta)
    ''')
    
    # Extract results for Model 3
    model3_coef = ro.r('model3_summary$coefficients')
    model3_ci = ro.r('model3_confint')
    model3_beta_coef_r_matrix = ro.r('model3_beta_summary$coefficients')
    model3_r2 = ro.r('model3_summary$r.squared')[0]
    model3_adj_r2 = ro.r('model3_summary$adj.r.squared')[0]
    
    # Extract standardized coefficients directly from lm.beta object
    model3_beta_coef = ro.r('coef(model3_beta)')
    
    # Process Model 3 results
    model3_coef_names = ['(Intercept)', 'total_score_z', 'mean_rt_ms', 'overall_accuracy', 
                         'total_score_z:mean_rt_ms', 'total_score_z:overall_accuracy']
    for i, coef_name in enumerate(model3_coef_names):
        # Get standardized estimate (NaN for intercept)
        if coef_name == '(Intercept)':
            std_estimate = np.nan
        else:
            try:
                # For non-intercept predictors, extract from beta coefficients (skip intercept index)
                std_estimate = model3_beta_coef[i-1]
            except (IndexError, TypeError) as e:
                print(f"Warning: Could not extract standardized coefficient for '{coef_name}' in Model 3: {e}")
                std_estimate = np.nan
        
        results.append({
            'model_name': 'RT_Facilitation_Interaction',
            'predictor': coef_name,
            'estimate': model3_coef[i][0],
            'std_error': model3_coef[i][1],
            'standardized_estimate': std_estimate,
            'ci_lower': model3_ci[i][0],
            'ci_upper': model3_ci[i][1],
            't_value': model3_coef[i][2],
            'p_value': model3_coef[i][3],
            'r_squared': model3_r2,
            'adjusted_r_squared': model3_adj_r2
        })
    
    # Model 4: Accuracy Facilitation with interactions
    print("Fitting Model 4: Accuracy Facilitation with baseline performance interactions")
    ro.r('''
    model4 <- lm(accuracy_facilitation_index ~ total_score_z + mean_rt_ms + overall_accuracy + 
                 total_score_z:mean_rt_ms + total_score_z:overall_accuracy, data = analysis_data)
    model4_summary <- summary(model4)
    model4_confint <- confint(model4)
    model4_beta <- lm.beta(model4)
    model4_beta_summary <- summary(model4_beta)
    ''')
    
    # Extract results for Model 4
    model4_coef = ro.r('model4_summary$coefficients')
    model4_ci = ro.r('model4_confint')
    model4_beta_coef_r_matrix = ro.r('model4_beta_summary$coefficients')
    model4_r2 = ro.r('model4_summary$r.squared')[0]
    model4_adj_r2 = ro.r('model4_summary$adj.r.squared')[0]
    
    # Extract standardized coefficients directly from lm.beta object
    model4_beta_coef = ro.r('coef(model4_beta)')
    
    # Process Model 4 results
    for i, coef_name in enumerate(model3_coef_names):
        # Get standardized estimate (NaN for intercept)
        if coef_name == '(Intercept)':
            std_estimate = np.nan
        else:
            try:
                # For non-intercept predictors, extract from beta coefficients (skip intercept index)
                std_estimate = model4_beta_coef[i-1]
            except (IndexError, TypeError) as e:
                print(f"Warning: Could not extract standardized coefficient for '{coef_name}' in Model 4: {e}")
                std_estimate = np.nan
        
        results.append({
            'model_name': 'Accuracy_Facilitation_Interaction',
            'predictor': coef_name,
            'estimate': model4_coef[i][0],
            'std_error': model4_coef[i][1],
            'standardized_estimate': std_estimate,
            'ci_lower': model4_ci[i][0],
            'ci_upper': model4_ci[i][1],
            't_value': model4_coef[i][2],
            'p_value': model4_coef[i][3],
            'r_squared': model4_r2,
            'adjusted_r_squared': model4_adj_r2
        })
    
    print(f"Fitted {len(set([r['model_name'] for r in results]))} regression models")
    
    # Print model structure summary for verification
    print("\nModel structure summary:")
    for model_name in ['RT_Facilitation_Main', 'Accuracy_Facilitation_Main', 'RT_Facilitation_Interaction', 'Accuracy_Facilitation_Interaction']:
        model_results = [r for r in results if r['model_name'] == model_name]
        predictors = [r['predictor'] for r in model_results]
        print(f"  {model_name}: {len(predictors)} predictors - {predictors}")
    
    return results

def check_regression_assumptions(analysis_df, ro):
    """
    Check regression assumptions and calculate diagnostics.
    
    Parameters:
    analysis_df (pd.DataFrame): Analysis dataset
    ro: rpy2.robjects module
    
    Returns:
    list: List of diagnostic results
    """
    print("\nChecking regression assumptions...")
    
    diagnostics = []
    
    # Convert to R dataframe
    r_df = ro.conversion.py2rpy(analysis_df)
    ro.globalenv['analysis_data'] = r_df
    
    models = [
        ('RT_Facilitation_Main', 'lm(rt_facilitation_slope ~ total_score_z, data = analysis_data)'),
        ('Accuracy_Facilitation_Main', 'lm(accuracy_facilitation_index ~ total_score_z, data = analysis_data)'),
        ('RT_Facilitation_Interaction', 'lm(rt_facilitation_slope ~ total_score_z + mean_rt_ms + overall_accuracy + total_score_z:mean_rt_ms + total_score_z:overall_accuracy, data = analysis_data)'),
        ('Accuracy_Facilitation_Interaction', 'lm(accuracy_facilitation_index ~ total_score_z + mean_rt_ms + overall_accuracy + total_score_z:mean_rt_ms + total_score_z:overall_accuracy, data = analysis_data)')
    ]
    
    for model_name, model_formula in models:
        print(f"Checking assumptions for {model_name}")
        
        ro.r(f'model <- {model_formula}')
        
        # Normality test (Shapiro-Wilk on residuals)
        ro.r('residuals <- residuals(model)')
        normality_p = ro.r('shapiro.test(residuals)$p.value')[0]
        
        # Homoscedasticity test (Breusch-Pagan)
        try:
            ro.r('''
            if (!requireNamespace("lmtest", quietly = TRUE)) {
              install.packages("lmtest", repos = "https://cloud.r-project.org")
            }
            library(lmtest)
            ''')
            homoscedasticity_p = ro.r('bptest(model)$p.value')[0]
        except Exception as e:
            print(f"Warning: Could not perform homoscedasticity test for {model_name}: {e}")
            homoscedasticity_p = None
        
        # Cook's distance for outliers
        ro.r('cooks_d <- cooks.distance(model)')
        max_cooks = ro.r('max(cooks_d, na.rm = TRUE)')[0]
        
        # Robust handling of n_influential calculation
        r_command_influential = 'sum(cooks_d > 4/length(cooks_d), na.rm = TRUE)'
        n_influential_r = ro.r(r_command_influential)
        print(f"Raw n_influential for {model_name}: {n_influential_r}")
        
        # Check for R NA or NULL values
        try:
            if str(n_influential_r) == 'NA' or n_influential_r is None:
                n_influential = 0
                print(f"Warning: n_influential was NA for {model_name}, setting to 0")
            else:
                n_influential = int(n_influential_r[0])
        except (ValueError, TypeError, IndexError) as e:
            print(f"Warning: Could not convert n_influential for {model_name}: {e}, setting to 0")
            n_influential = 0
        
        diagnostics.append({
            'model_name': model_name,
            'n_participants': len(analysis_df),
            'normality_test_p': normality_p,
            'homoscedasticity_test_p': homoscedasticity_p,
            'n_influential_outliers': n_influential,
            'max_cooks_distance': max_cooks
        })
    
    print("Regression diagnostics completed")
    return diagnostics

def apply_fdr_correction(results):
    """
    Apply False Discovery Rate correction using Benjamini-Hochberg procedure.
    Applies to all non-intercept predictors across all models.
    
    Parameters:
    results (list): List of regression results
    
    Returns:
    list: Results with FDR-corrected p-values
    """
    print("\nApplying False Discovery Rate correction...")
    
    # Initialize FDR columns for all results
    for result in results:
        result['p_value_fdr_corrected'] = np.nan
        result['significant_fdr'] = False
    
    # Extract p-values for VVIQ2-related predictors only
    p_values_to_correct = []
    indices_to_correct = []
    
    for i, result in enumerate(results):
        # Include only predictors that contain 'total_score_z' (main effects and interactions)
        if 'total_score_z' in result['predictor']:
            p_values_to_correct.append(result['p_value'])
            indices_to_correct.append(i)
        # All other predictors will remain with p_value_fdr_corrected = np.nan and significant_fdr = False

    # Validate expected number of VVIQ2-related predictors (should be 8: 1+1+3+3 from 4 models)
    expected_predictors = 8  # Model1(1) + Model2(1) + Model3(3) + Model4(3)
    if len(p_values_to_correct) != expected_predictors:
        print(f"Warning: Expected {expected_predictors} VVIQ2-related predictors, found {len(p_values_to_correct)}")
    
    print(f"Correcting {len(p_values_to_correct)} p-values (VVIQ2-related predictors only)")
    if len(p_values_to_correct) > 0:
        print("VVIQ2-related predictors included in FDR correction:")
        for i, idx in enumerate(indices_to_correct):
            print(f"  {i+1}. {results[idx]['model_name']}: {results[idx]['predictor']} (p={results[idx]['p_value']:.6f})")
    
    if len(p_values_to_correct) > 0:
        # Apply Benjamini-Hochberg correction
        p_array = np.array(p_values_to_correct)
        n = len(p_array)
        
        # Sort p-values and get indices
        sorted_indices = np.argsort(p_array)
        sorted_p = p_array[sorted_indices]
        
        # Calculate corrected p-values with proper B-H procedure
        corrected_ranks = np.arange(1, n + 1)
        bh_corrected = (sorted_p * n) / corrected_ranks
        
        # Ensure monotonicity (take cumulative minimum from the end)
        bh_corrected_monotonic = np.minimum.accumulate(bh_corrected[::-1])[::-1]
        
        # Ensure values are capped at 1.0
        bh_corrected_monotonic = np.clip(bh_corrected_monotonic, None, 1.0)
        
        # Map back to original order
        corrected_p_final = np.empty_like(p_array)
        corrected_p_final[sorted_indices] = bh_corrected_monotonic
        
        # Update results with corrected p-values
        for j, original_result_idx in enumerate(indices_to_correct):
            results[original_result_idx]['p_value_fdr_corrected'] = corrected_p_final[j]
            results[original_result_idx]['significant_fdr'] = corrected_p_final[j] < 0.05
    
    # Count significant results after FDR correction
    n_significant = sum(1 for r in results if r['significant_fdr'] and 'total_score_z' in r['predictor'])
    print(f"Significant VVIQ2-related results after FDR correction: {n_significant}")
    
    return results

def main():
    """
    Main function to execute the individual differences analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT individual differences analysis...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
        
        # Load and validate data
        facilitation_df, vviq_df, mrt_data_df = load_and_validate_data()
        if facilitation_df is None:
            return 1
        
        # Merge datasets
        merged_df = merge_datasets(facilitation_df, vviq_df)
        if len(merged_df) == 0:
            print("Error: No participants in merged dataset")
            return 1
        
        # Calculate baseline performance
        baseline_df = calculate_baseline_performance(mrt_data_df, merged_df['participantId'].tolist())
        
        # Merge with baseline performance
        analysis_df = pd.merge(merged_df, baseline_df, on='participantId', how='inner')
        print(f"Final analysis dataset: {len(analysis_df)} participants")
        print("Analysis dataset columns:", analysis_df.columns.tolist())
        print("First 2 rows of analysis dataset:")
        print(analysis_df.head(2))
        
        # Remove rows with NaN values in model variables
        model_vars = ['rt_facilitation_slope', 'accuracy_facilitation_index', 'total_score_z', 'mean_rt_ms', 'overall_accuracy']
        initial_rows = len(analysis_df)
        analysis_df = analysis_df.dropna(subset=model_vars)
        if len(analysis_df) < initial_rows:
            print(f"Dropped {initial_rows - len(analysis_df)} rows with NA in model variables from analysis_df.")
        print(f"Analysis dataset after NaN removal: {len(analysis_df)} participants")
        
        # Setup R environment
        ro, pandas2ri = setup_r_environment()
        if ro is None:
            print("Error: Could not setup R environment")
            return 1
        
        # Fit regression models
        results = fit_regression_models(analysis_df, ro)
        
        # Check regression assumptions
        diagnostics = check_regression_assumptions(analysis_df, ro)
        
        # Apply FDR correction
        results = apply_fdr_correction(results)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save regression results
        results_df = pd.DataFrame(results)
        results_file = f"outputs/MRT_individual_differences_results_{timestamp}.csv"
        results_df.to_csv(results_file, index=False)
        print(f"Regression results saved to {results_file}")
        print("Results summary:")
        print(f"Total models fitted: {len(results_df['model_name'].unique())}")
        print(f"Significant effects (FDR corrected): {sum(results_df['significant_fdr'])}")
        
        # Save diagnostics
        diagnostics_df = pd.DataFrame(diagnostics)
        diagnostics_file = f"outputs/MRT_regression_diagnostics_{timestamp}.csv"
        diagnostics_df.to_csv(diagnostics_file, index=False)
        print(f"Regression diagnostics saved to {diagnostics_file}")
        
        # Print final summary
        print("\nFinal Analysis Summary:")
        print(f"Sample size: {len(analysis_df)} participants")
        print(f"Models fitted: {len(diagnostics)} regression models")
        print(f"Significant VVIQ2-related predictors (FDR corrected): {sum(r['significant_fdr'] for r in results if 'total_score_z' in r['predictor'])}")
        
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
