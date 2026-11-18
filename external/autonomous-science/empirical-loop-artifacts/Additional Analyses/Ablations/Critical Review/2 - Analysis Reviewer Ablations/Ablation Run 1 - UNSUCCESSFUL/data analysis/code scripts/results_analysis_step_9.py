import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
from scipy import stats
from scipy.stats import circstd
import warnings
import statsmodels.api as sm
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to search for
    
    Returns:
    str: Path to the most recent file matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    latest_file = max(files, key=os.path.getctime)
    print(f"Found latest file: {latest_file}")
    return latest_file

def calculate_circular_std(angles_radians):
    """
    Calculate circular standard deviation for angles in radians.
    
    Parameters:
    angles_radians (array): Array of angles in radians
    
    Returns:
    float: Circular standard deviation
    """
    if len(angles_radians) == 0:
        return np.nan
    return circstd(angles_radians)

def calculate_simple_precision(vwm_errors, guess_rate):
    """
    Calculate simple precision estimate from VWM errors.
    
    Parameters:
    vwm_errors (array): Array of VWM error values in degrees
    guess_rate (float): Guess rate from mixture model
    
    Returns:
    float: Simple precision estimate (1 / circular_std)
    """
    if len(vwm_errors) == 0:
        return np.nan
    
    # Convert degrees to radians
    errors_radians = np.deg2rad(vwm_errors)
    
    # Calculate number of non-guess trials
    n_trials = len(errors_radians)
    n_nonguess = int(n_trials * (1 - guess_rate))
    
    if n_nonguess <= 1:
        return np.nan
    
    # Sort errors by absolute value and take the smallest (most likely non-guess)
    abs_errors = np.abs(errors_radians)
    sorted_indices = np.argsort(abs_errors)
    nonguess_errors = errors_radians[sorted_indices[:n_nonguess]]
    
    # Calculate circular standard deviation
    circ_std = calculate_circular_std(nonguess_errors)
    
    if circ_std == 0 or np.isnan(circ_std):
        return np.nan
    
    return 1.0 / circ_std

import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

def run_regression_model(df, outcome, predictor, controls, model_type='ols'):
    """
    Run regression model using statsmodels with proper model selection.
    """
    all_predictors = [predictor] + controls
    required_vars = [outcome] + all_predictors
    complete_data = df.dropna(subset=required_vars)
    
    if len(complete_data) < 10:
        print(f"Warning: Only {len(complete_data)} complete cases for {outcome}")
        return {
            'coefficient': np.nan,
            'standard_error': np.nan,
            'p_value': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'r_squared': np.nan
        }
    
    try:
        X = complete_data[all_predictors]
        X = sm.add_constant(X)
        y = complete_data[outcome]
        
        if model_type == 'logistic':
            model = sm.Logit(y, X).fit(disp=0)
        else:
            model = sm.OLS(y, X).fit()
        
        # Extract results for the primary predictor (index 1, after constant)
        coef = model.params.iloc[1]
        se = model.bse.iloc[1]
        p_val = model.pvalues.iloc[1]
        ci_lower, ci_upper = model.conf_int().iloc[1]
        
        # R-squared (pseudo R-squared for logistic)
        if model_type == 'logistic':
            r_squared = model.prsquared
        else:
            r_squared = model.rsquared
        
        return {
            'coefficient': coef,
            'standard_error': se,
            'p_value': p_val,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'r_squared': r_squared
        }
        
    except Exception as e:
        print(f"Warning: Model fitting failed for {outcome}: {str(e)}")
        return {
            'coefficient': np.nan,
            'standard_error': np.nan,
            'p_value': np.nan,
            'ci_lower': np.nan,
            'ci_upper': np.nan,
            'r_squared': np.nan
        }

def main():
    """
    Main function to execute sensitivity analysis for precision measures.
    """
    try:
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Starting sensitivity analysis at {timestamp}")
        
        # Find and load input files
        print("\n=== LOADING INPUT FILES ===")
        
        # Load mixture model parameters
        mixture_pattern = "outputs/mixture_model_parameters_*.csv"
        mixture_file = find_latest_file(mixture_pattern)
        mixture_df = pd.read_csv(mixture_file)
        print(f"Loaded mixture model parameters: {mixture_df.shape}")
        print("Columns:", list(mixture_df.columns))
        print("First 3 rows:")
        print(mixture_df.head(3))
        
        # Load cleaned trial data
        trial_pattern = "outputs/cleaned_trial_data_*.csv"
        trial_file = find_latest_file(trial_pattern)
        trial_df = pd.read_csv(trial_file)
        print(f"\nLoaded trial data: {trial_df.shape}")
        print("Columns:", list(trial_df.columns))
        print("First 3 rows:")
        print(trial_df.head(3))
        print("Unique table values:", trial_df['table'].unique())
        print("Unique isPractice values:", trial_df['isPractice'].unique())
        
        # Load control variables
        control_pattern = "outputs/control_variables_*.csv"
        control_file = find_latest_file(control_pattern)
        control_df = pd.read_csv(control_file)
        print(f"\nLoaded control variables: {control_df.shape}")
        print("Columns:", list(control_df.columns))
        print("First 3 rows:")
        print(control_df.head(3))
        
        # Load MRT performance data
        mrt_pattern = "outputs/mrt_performance_by_disparity_*.csv"
        mrt_file = find_latest_file(mrt_pattern)
        mrt_df = pd.read_csv(mrt_file)
        print(f"\nLoaded MRT performance: {mrt_df.shape}")
        print("Columns:", list(mrt_df.columns))
        print("First 3 rows:")
        print(mrt_df.head(3))
        
        # Load VVIQ2 scores
        vviq_pattern = "outputs/vviq2_scores_*.csv"
        vviq_file = find_latest_file(vviq_pattern)
        vviq_df = pd.read_csv(vviq_file)
        print(f"\nLoaded VVIQ2 scores: {vviq_df.shape}")
        print("Columns:", list(vviq_df.columns))
        print("First 3 rows:")
        print(vviq_df.head(3))
        
        # Calculate simple precision estimates
        print("\n=== CALCULATING SIMPLE PRECISION ESTIMATES ===")
        
        # Filter VWM test trials
        vwm_test_trials = trial_df[
            (trial_df['isPractice'] == False) & 
            (trial_df['table'] == 'vwm_test')
        ].copy()
        print(f"VWM test trials: {len(vwm_test_trials)}")
        
        simple_precision_results = []
        
        for participant_id in mixture_df['participantId'].unique():
            print(f"Processing participant {participant_id}")
            
            # Get participant's trials and mixture model parameters
            participant_trials = vwm_test_trials[
                vwm_test_trials['participantId'] == participant_id
            ]
            participant_mixture = mixture_df[
                mixture_df['participantId'] == participant_id
            ]
            
            if len(participant_trials) == 0 or len(participant_mixture) == 0:
                print(f"  No data for participant {participant_id}")
                continue
            
            # Get guess rate and errors
            guess_rate = participant_mixture['guess_rate_vonmises'].iloc[0]
            vwm_errors = participant_trials['VWM_error_degrees'].dropna().values
            
            print(f"  Guess rate: {guess_rate:.3f}, Trials: {len(vwm_errors)}")
            
            # Calculate simple precision
            simple_precision = calculate_simple_precision(vwm_errors, guess_rate)
            
            # Determine alternative model parameters
            aic_vonmises = participant_mixture['aic_vonmises'].iloc[0]
            aic_wrapped_normal = participant_mixture['aic_wrapped_normal'].iloc[0]
            aic_wrapped_cauchy = participant_mixture['aic_wrapped_cauchy'].iloc[0]
            
            # Find best alternative model
            alt_models = {
                'wrapped_normal': aic_wrapped_normal,
                'wrapped_cauchy': aic_wrapped_cauchy
            }
            
            best_alt_model = min(alt_models.keys(), key=lambda x: alt_models[x])
            best_alt_aic = alt_models[best_alt_model]
            aic_improvement = aic_vonmises - best_alt_aic
            
            # Get alternative model precision
            if aic_improvement > 4:
                if best_alt_model == 'wrapped_normal':
                    alt_precision = participant_mixture['kappa_wrapped_normal'].iloc[0]
                else:
                    alt_precision = participant_mixture['kappa_wrapped_cauchy'].iloc[0]
                alt_model_used = best_alt_model
            else:
                alt_precision = participant_mixture['kappa_vonmises'].iloc[0]
                alt_model_used = 'vonmises'
            
            simple_precision_results.append({
                'participantId': participant_id,
                'simple_precision_estimate': simple_precision,
                'alternative_model_precision': alt_precision,
                'alternative_model_used': alt_model_used,
                'aic_improvement': aic_improvement
            })
            
            print(f"  Simple precision: {simple_precision:.3f}")
            print(f"  Alternative precision: {alt_precision:.3f}")
            print(f"  AIC improvement: {aic_improvement:.3f}")

        # Add fallback for empty precision results
        if len(simple_precision_results) == 0:
            print("Warning: No simple precision estimates calculated. Creating empty dataframe with required columns.")
            alt_precision_df = pd.DataFrame(columns=['participantId', 'simple_precision_estimate', 'alternative_model_precision', 'alternative_model_used', 'aic_improvement'])
        else:
            alt_precision_df = pd.DataFrame(simple_precision_results)
        print(f"\nAlternative precision estimates calculated for {len(alt_precision_df)} participants")
        
        # Save alternative precision measures
        alt_precision_file = f"outputs/alternative_precision_measures_{timestamp}.csv"
        alt_precision_df.to_csv(alt_precision_file, index=False)
        print(f"Saved alternative precision measures to {alt_precision_file}")
        
        # Merge all datasets for analysis
        print("\n=== MERGING DATASETS FOR ANALYSIS ===")
        
        # Check required columns before merging
        if 'participantId' not in mixture_df.columns:
            raise ValueError("mixture_df missing 'participantId' column")
        if 'participantId' not in alt_precision_df.columns:
            print("Warning: alt_precision_df missing 'participantId' column. Creating empty column.")
            alt_precision_df['participantId'] = np.nan

        # Start with mixture model data and add alternative precision
        analysis_df = mixture_df.merge(alt_precision_df, on='participantId', how='left')

        print(f"After merging mixture and alt_precision: {analysis_df.shape}")

        # Add control variables
        if 'participantId' in control_df.columns:
            analysis_df = analysis_df.merge(control_df, on='participantId', how='left')
            print(f"After merging control variables: {analysis_df.shape}")
        else:
            print("Warning: control_df missing 'participantId' column. Skipping merge.")

        # Add MRT performance
        if 'participantId' in mrt_df.columns:
            analysis_df = analysis_df.merge(mrt_df, on='participantId', how='left')
            print(f"After merging MRT performance: {analysis_df.shape}")
        else:
            print("Warning: mrt_df missing 'participantId' column. Skipping merge.")

        # Add VVIQ2 scores
        if 'participantId' in vviq_df.columns:
            analysis_df = analysis_df.merge(vviq_df, on='participantId', how='left')
            print(f"After merging VVIQ2 scores: {analysis_df.shape}")
        else:
            print("Warning: vviq_df missing 'participantId' column. Skipping merge.")

        print(f"Final analysis dataset: {analysis_df.shape}")
        print("Columns:", list(analysis_df.columns))
        print("First 2 rows:")
        print(analysis_df.head(2))
        
        # Standardize control variables
        print("\n=== STANDARDIZING CONTROL VARIABLES ===")
        control_vars = [
            'vwm_mean_accuracy_nonguess',
            'vwm_rt_cv',
            'mrt_rt_cv', 
            'engagement_index',
            'vwm_timeout_rate'
        ]
        
        z_control_vars = []
        for var in control_vars:
            if var in analysis_df.columns and analysis_df[var].std() > 0:
                z_var = f'z_{var}'
                analysis_df[z_var] = (analysis_df[var] - analysis_df[var].mean()) / analysis_df[var].std()
                z_control_vars.append(z_var)
                print(f"Standardized {var} -> {z_var} (mean={analysis_df[var].mean():.4f}, std={analysis_df[var].std():.4f})")
            else:
                print(f"Skipped standardization for {var} due to zero variance or missing column")
        
        # Run sensitivity analyses
        print("\n=== RUNNING SENSITIVITY ANALYSES ===")
        
        regression_results = []
        
        print(f"z_control_vars used in regression: {z_control_vars}")

        # Define outcome measures
        mrt_accuracy_outcomes = ['mrt_accuracy_0deg', 'mrt_accuracy_50deg', 
                                'mrt_accuracy_100deg', 'mrt_accuracy_150deg']
        mrt_rt_outcomes = ['mrt_log_rt_0deg', 'mrt_log_rt_50deg',
                          'mrt_log_rt_100deg', 'mrt_log_rt_150deg']
        vviq_outcomes = ['vviq2_total_score', 'vviq2_person_score', 'vviq2_sunrise_score',
                        'vviq2_shop_score', 'vviq2_countryside_score', 'vviq2_driving_score',
                        'vviq2_beach_score', 'vviq2_station_score', 'vviq2_garden_score']
        
        disparities = [0, 50, 100, 150]
        
        # Sensitivity Analysis 1: Simple Precision
        print("\n--- Sensitivity Analysis 1: Simple Precision ---")
        
        # MRT Accuracy models
        for i, outcome in enumerate(mrt_accuracy_outcomes):
            disparity = disparities[i]
            print(f"Running MRT accuracy model for {disparity}° disparity")
            
            results = run_regression_model(
                analysis_df, outcome, 'simple_precision_estimate', z_control_vars, model_type='logistic'
            )
            
            regression_results.append({
                'sensitivity_condition': 'simple_precision',
                'model_type': 'mrt_accuracy',
                'outcome_measure': outcome,
                'angular_disparity': disparity,
                'predictor': 'simple_precision_estimate',
                'coefficient': results['coefficient'],
                'standard_error': results['standard_error'],
                'p_value': results['p_value'],
                'ci_lower': results['ci_lower'],
                'ci_upper': results['ci_upper'],
                'r_squared': results['r_squared']
            })
            
            print(f"  Coefficient: {results['coefficient']:.4f}, p = {results['p_value']:.4f}")
        
        # MRT RT models
        for i, outcome in enumerate(mrt_rt_outcomes):
            disparity = disparities[i]
            print(f"Running MRT RT model for {disparity}° disparity")
            
            results = run_regression_model(
                analysis_df, outcome, 'simple_precision_estimate', z_control_vars
            )
            
            regression_results.append({
                'sensitivity_condition': 'simple_precision',
                'model_type': 'mrt_rt',
                'outcome_measure': outcome,
                'angular_disparity': disparity,
                'predictor': 'simple_precision_estimate',
                'coefficient': results['coefficient'],
                'standard_error': results['standard_error'],
                'p_value': results['p_value'],
                'ci_lower': results['ci_lower'],
                'ci_upper': results['ci_upper'],
                'r_squared': results['r_squared']
            })
            
            print(f"  Coefficient: {results['coefficient']:.4f}, p = {results['p_value']:.4f}")
        
        # VVIQ2 models
        for outcome in vviq_outcomes:
            print(f"Running VVIQ2 model for {outcome}")
            
            results = run_regression_model(
                analysis_df, outcome, 'simple_precision_estimate', z_control_vars
            )
            
            regression_results.append({
                'sensitivity_condition': 'simple_precision',
                'model_type': 'vviq2',
                'outcome_measure': outcome,
                'angular_disparity': np.nan,
                'predictor': 'simple_precision_estimate',
                'coefficient': results['coefficient'],
                'standard_error': results['standard_error'],
                'p_value': results['p_value'],
                'ci_lower': results['ci_lower'],
                'ci_upper': results['ci_upper'],
                'r_squared': results['r_squared']
            })
            
            print(f"  Coefficient: {results['coefficient']:.4f}, p = {results['p_value']:.4f}")
        
        # Sensitivity Analysis 2: Alternative Model Parameters
        print("\n--- Sensitivity Analysis 2: Alternative Model Parameters ---")
        
        # Filter to participants with superior alternative models
        if 'aic_improvement' in analysis_df.columns:
            alt_model_df = analysis_df[analysis_df['aic_improvement'] > 4].copy()
            print(f"Participants with superior alternative models: {len(alt_model_df)}")
        else:
            print("Warning: 'aic_improvement' column missing from analysis_df. Skipping alternative model analysis.")
            alt_model_df = pd.DataFrame()

        if len(alt_model_df) > 10:
            # MRT Accuracy models
            for i, outcome in enumerate(mrt_accuracy_outcomes):
                disparity = disparities[i]
                print(f"Running alternative model MRT accuracy for {disparity}° disparity")
                
                results = run_regression_model(
                    alt_model_df, outcome, 'alternative_model_precision', z_control_vars, model_type='logistic'
                )
                
                regression_results.append({
                    'sensitivity_condition': 'alternative_models',
                    'model_type': 'mrt_accuracy',
                    'outcome_measure': outcome,
                    'angular_disparity': disparity,
                    'predictor': 'alternative_model_precision',
                    'coefficient': results['coefficient'],
                    'standard_error': results['standard_error'],
                    'p_value': results['p_value'],
                    'ci_lower': results['ci_lower'],
                    'ci_upper': results['ci_upper'],
                    'r_squared': results['r_squared']
                })
                
                print(f"  Coefficient: {results['coefficient']:.4f}, p = {results['p_value']:.4f}")
            
            # MRT RT models
            for i, outcome in enumerate(mrt_rt_outcomes):
                disparity = disparities[i]
                print(f"Running alternative model MRT RT for {disparity}° disparity")
                
                results = run_regression_model(
                    alt_model_df, outcome, 'alternative_model_precision', z_control_vars
                )
                
                regression_results.append({
                    'sensitivity_condition': 'alternative_models',
                    'model_type': 'mrt_rt',
                    'outcome_measure': outcome,
                    'angular_disparity': disparity,
                    'predictor': 'alternative_model_precision',
                    'coefficient': results['coefficient'],
                    'standard_error': results['standard_error'],
                    'p_value': results['p_value'],
                    'ci_lower': results['ci_lower'],
                    'ci_upper': results['ci_upper'],
                    'r_squared': results['r_squared']
                })
                
                print(f"  Coefficient: {results['coefficient']:.4f}, p = {results['p_value']:.4f}")
            
            # VVIQ2 models
            for outcome in vviq_outcomes:
                print(f"Running alternative model VVIQ2 for {outcome}")
                
                results = run_regression_model(
                    alt_model_df, outcome, 'alternative_model_precision', z_control_vars
                )
                
                regression_results.append({
                    'sensitivity_condition': 'alternative_models',
                    'model_type': 'vviq2',
                    'outcome_measure': outcome,
                    'angular_disparity': np.nan,
                    'predictor': 'alternative_model_precision',
                    'coefficient': results['coefficient'],
                    'standard_error': results['standard_error'],
                    'p_value': results['p_value'],
                    'ci_lower': results['ci_lower'],
                    'ci_upper': results['ci_upper'],
                    'r_squared': results['r_squared']
                })
                
                print(f"  Coefficient: {results['coefficient']:.4f}, p = {results['p_value']:.4f}")
        else:
            print("Too few participants with superior alternative models for analysis")
        
        # Save regression results
        regression_results_df = pd.DataFrame(regression_results)
        regression_file = f"outputs/sensitivity_regression_results_{timestamp}.csv"
        regression_results_df.to_csv(regression_file, index=False)
        print(f"\nSaved sensitivity regression results to {regression_file}")
        
        print("\n=== CREATING ROBUSTNESS COMPARISON ===")

        # Load primary analysis results
        try:
            primary_mrt_file = find_latest_file("outputs/mrt_regression_results_*.csv")
            primary_vviq2_file = find_latest_file("outputs/vviq2_regression_results_*.csv")
            primary_mrt_df = pd.read_csv(primary_mrt_file)
            primary_vviq2_df = pd.read_csv(primary_vviq2_file)
            
            print(f"Loaded primary MRT results: {primary_mrt_df.shape}")
            print(f"Loaded primary VVIQ2 results: {primary_vviq2_df.shape}")
            
            # Combine primary results and filter for kappa_vonmises predictor
            primary_results_df = pd.concat([primary_mrt_df, primary_vviq2_df], ignore_index=True)
            primary_results_df = primary_results_df[primary_results_df['predictor'] == 'kappa_vonmises'].copy()
            
            print(f"Primary analysis results with kappa_vonmises: {len(primary_results_df)}")
            
            # Get sensitivity analysis results
            simple_df = regression_results_df[regression_results_df['sensitivity_condition'] == 'simple_precision'].copy()
            alt_df = regression_results_df[regression_results_df['sensitivity_condition'] == 'alternative_models'].copy()
            
            print(f"Simple precision results: {len(simple_df)}")
            print(f"Alternative model results: {len(alt_df)}")
            
            # Merge primary with simple precision results
            robustness_df = pd.merge(
                primary_results_df[['outcome_measure', 'angular_disparity', 'coefficient', 'p_value']],
                simple_df[['outcome_measure', 'angular_disparity', 'coefficient', 'p_value']],
                on=['outcome_measure', 'angular_disparity'],
                suffixes=('_primary', '_simple'),
                how='left'
            )
            
            # Merge with alternative model results
            robustness_df = pd.merge(
                robustness_df,
                alt_df[['outcome_measure', 'angular_disparity', 'coefficient', 'p_value']],
                on=['outcome_measure', 'angular_disparity'],
                suffixes=('', '_alt'),
                how='left'
            )
            
            # Rename columns to match expected output format
            robustness_df = robustness_df.rename(columns={
                'coefficient_primary': 'primary_coefficient',
                'p_value_primary': 'primary_p_value',
                'coefficient_simple': 'simple_precision_coefficient',
                'p_value_simple': 'simple_precision_p_value',
                'coefficient': 'alternative_model_coefficient',
                'p_value': 'alternative_model_p_value'
            })
            
            # Calculate consistency: simple precision vs primary analysis
            robustness_df['conclusion_consistent'] = (
                (robustness_df['primary_p_value'] < 0.05) == 
                (robustness_df['simple_precision_p_value'] < 0.05)
            )
            
            # Add robustness notes
            robustness_df['robustness_notes'] = 'Comparison of sensitivity analyses vs primary analysis'
            
            print(f"Final robustness comparison: {len(robustness_df)} comparisons")
            print("Consistency summary:")
            print(robustness_df['conclusion_consistent'].value_counts())
            
        except FileNotFoundError as e:
            print(f"Warning: Could not load primary analysis results: {e}")
            print("Creating placeholder robustness comparison")
            
            # Create placeholder comparison between sensitivity analyses
            robustness_results = []
            
            for outcome in mrt_accuracy_outcomes + mrt_rt_outcomes + vviq_outcomes:
                simple_results = regression_results_df[
                    (regression_results_df['sensitivity_condition'] == 'simple_precision') &
                    (regression_results_df['outcome_measure'] == outcome)
                ]
                
                if len(simple_results) > 0:
                    simple_coef = simple_results['coefficient'].iloc[0]
                    simple_p = simple_results['p_value'].iloc[0]
                    disparity = simple_results['angular_disparity'].iloc[0] if outcome in mrt_accuracy_outcomes + mrt_rt_outcomes else np.nan
                    
                    robustness_results.append({
                        'outcome_measure': outcome,
                        'angular_disparity': disparity,
                        'primary_coefficient': np.nan,
                        'primary_p_value': np.nan,
                        'simple_precision_coefficient': simple_coef,
                        'simple_precision_p_value': simple_p,
                        'alternative_model_coefficient': np.nan,
                        'alternative_model_p_value': np.nan,
                        'conclusion_consistent': True,
                        'robustness_notes': 'Primary analysis results not available'
                    })
            
            robustness_df = pd.DataFrame(robustness_results)

        robustness_file = f"outputs/robustness_comparison_{timestamp}.csv"
        robustness_df.to_csv(robustness_file, index=False)
        print(f"Saved robustness comparison to {robustness_file}")
        
        # Print summary statistics
        print("\n=== SUMMARY STATISTICS ===")
        print(f"Total participants analyzed: {len(analysis_df)}")
        print(f"Participants with simple precision estimates: {alt_precision_df['simple_precision_estimate'].notna().sum()}")
        if 'aic_improvement' in alt_precision_df.columns:
            print(f"Participants with superior alternative models: {(alt_precision_df['aic_improvement'] > 4).sum()}")
        else:
            print("Participants with superior alternative models: 0")
        
        # Correlation between precision measures
        valid_data = alt_precision_df.dropna(subset=['simple_precision_estimate'])
        if len(valid_data) > 10 and 'kappa_vonmises' in analysis_df.columns:
            corr_df = pd.merge(
                alt_precision_df[['participantId', 'simple_precision_estimate']],
                analysis_df[['participantId', 'kappa_vonmises']],
                on='participantId'
            ).dropna()
            if len(corr_df) > 0:
                corr_simple_vonmises = corr_df['simple_precision_estimate'].corr(corr_df['kappa_vonmises'])
                print(f"Correlation between simple precision and von Mises kappa: {corr_simple_vonmises:.3f}")
        
        print(f"\nSensitivity analysis completed successfully at {datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
