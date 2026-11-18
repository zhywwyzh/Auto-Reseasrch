import pandas as pd
import numpy as np
import re
import os
import glob
from datetime import datetime
from scipy import stats
from scipy.stats import shapiro
import matplotlib.pyplot as plt
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

def create_timestamp():
    """Create timestamp string for output files"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def extract_vviq2_scores(response_text):
    """
    Extract numeric scores from VVIQ2 response text using regex.
    
    Parameters:
    response_text (str): Response text containing score at the end
    
    Returns:
    int: Extracted score (1-5) or None if not found
    """
    if pd.isna(response_text) or response_text == '':
        return None
    
    # Find trailing digits at the end of the string
    match = re.search(r'(\d+)$', str(response_text).strip())
    if match:
        score = int(match.group(1))
        # Validate score is in expected range
        if 1 <= score <= 5:
            return score
    return None

def calculate_vviq2_scores(df):
    """
    Calculate VVIQ2 total and subscale scores from response data.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing VVIQ2 responses
    
    Returns:
    pd.DataFrame: DataFrame with calculated scores
    """
    print("Calculating VVIQ2 scores...")
    
    # Define VVIQ2 item columns in order
    vviq2_items = [
        'The exact contour of face, head, shoulders and body.',
        'Characteristic poses of head, attitudes of body etc.',
        'The precise carriage, length of step, etc. in walking.',
        'The different colours worn in some familiar clothes.',
        'The sun is rising above the horizon into a hazy sky.',
        'The sky clears and surrounds the sun with blueness.',
        'Clouds. A storm blows up, with flashes of lightening.',
        'A rainbow appears.',
        'The overall appearance of the shop from the opposite side of the road.',
        'A window display including colours, shape and details of individual items for sale.',
        'You are near the entrance. The colour, shape and details of the door.',
        'You enter the shop and go to the counter. The counter assistant serves you. Money changes hands.',
        'The contours of the landscape.',
        'The colour and shape of the trees.',
        'The colour and shape of the lake.',
        'A strong wind blows on the tree and on the lake causing waves.',
        'You observe the heavy traffic travelling at maximum speed around your car. The overall appearance of vehicles, their colours, sizes and shapes.',
        'Your car accelerates to overtake the traffic directly in front of you. You see and urgent expression on the face of the driver and the people in the other vehicles as you pass.',
        'A large truck is flashing its headlight directly behind. Your car quickly moves over to let the truck pass. The driver signals with a friendly wave.',
        'You see a broken-down vehicle beside the road. Its lights are flashing. The driver is looking concerned and she is using a mobile phone.',
        'The overall appearance and colour of the water, surf, and sky.',
        'Bathers are swimming and splashing about in the water. Some are playing with a brightly coloured beach ball.',
        'An ocean liner crosses the horizon. It leaves a trail of smoke in the blue sky.',
        'A beautiful air balloon appears with four people aboard. The balloon drifts past you, almost directly overhead. The passengers wave and smile. You wave and smile back at them.',
        'The overall appearance of the station viewed from in front of the main entrance.',
        'You walk into the station. The colour, shape and details of the entrance hall.',
        'You approach the ticket office, go to a vacant counter and purchase your ticket.',
        'You walk to the platform and observe other passengers and the railway lines. A train arrives. You climb aboard.',
        'The overall appearance and design of the garden.',
        'The colour and shape of the bushes and shrubs.',
        'The colour and appearance of the flowers.',
        'Some birds fly down onto the lawn and start pecking for food.'
    ]
    
    print(f"Expected VVIQ2 items: {len(vviq2_items)}")
    print(f"Available columns in VVIQ2 data: {len(df.columns)}")
    
    # Extract scores for each item
    scores_df = df[['PROLIFIC_PID']].copy()
    
    item_scores = []
    for i, item in enumerate(vviq2_items):
        if item in df.columns:
            scores = df[item].apply(extract_vviq2_scores)
            item_scores.append(scores)
            print(f"Item {i+1}: {sum(scores.notna())} valid scores out of {len(scores)}")
        else:
            print(f"WARNING: Item '{item}' not found in columns")
            item_scores.append(pd.Series([None] * len(df)))
    
    # Calculate total VVIQ2 score
    total_scores = []
    for idx in range(len(df)):
        valid_scores = [score[idx] for score in item_scores if pd.notna(score[idx])]
        if len(valid_scores) >= 24:  # Require at least 75% of items (24 out of 32)
            total_scores.append(sum(valid_scores))
        else:
            total_scores.append(None)
    
    scores_df['total_VVIQ2_score'] = total_scores
    
    # Calculate subscale scores
    subscales = {
        'familiar_person_score': [0, 1, 2, 3],  # items 1-4
        'sunrise_score': [4, 5, 6, 7],  # items 5-8
        'shop_front_score': [8, 9, 10, 11],  # items 9-12
        'countryside_score': [12, 13, 14, 15],  # items 13-16
        'driving_score': [16, 17, 18, 19],  # items 17-20
        'beach_score': [20, 21, 22, 23],  # items 21-24
        'railway_station_score': [24, 25, 26, 27],  # items 25-28
        'garden_score': [28, 29, 30, 31]  # items 29-32
    }
    
    for subscale_name, item_indices in subscales.items():
        subscale_scores = []
        for idx in range(len(df)):
            valid_scores = [item_scores[i][idx] for i in item_indices if pd.notna(item_scores[i][idx])]
            if len(valid_scores) >= 3:  # Require at least 3 out of 4 items
                subscale_scores.append(sum(valid_scores))
            else:
                subscale_scores.append(None)
        scores_df[subscale_name] = subscale_scores
    
    # Rename PROLIFIC_PID to participantId for consistency
    scores_df = scores_df.rename(columns={'PROLIFIC_PID': 'participantId'})
    
    print(f"VVIQ2 scores calculated for {len(scores_df)} participants")
    print(f"Valid total scores: {sum(pd.notna(scores_df['total_VVIQ2_score']))}")
    
    return scores_df

def run_regression_analysis(df, dependent_var, predictors, control_vars):
    """
    Run multiple linear regression analysis with standardized control variables using statsmodels OLS and robust standard errors.
    
    Parameters:
    df (pd.DataFrame): Data for analysis
    dependent_var (str): Name of dependent variable
    predictors (list): List of predictor variable names
    control_vars (list): List of control variable names to standardize
    
    Returns:
    dict: Dictionary containing regression results
    """
    print(f"Running regression analysis for {dependent_var}...")

    # Prepare data
    analysis_df = df.copy()

    # Standardize control variables
    scaler = StandardScaler()
    for var in control_vars:
        if var in analysis_df.columns:
            analysis_df[f'{var}_standardized'] = scaler.fit_transform(analysis_df[[var]])

    # Create final predictor list
    final_predictors = []
    for pred in predictors:
        if pred in control_vars:
            final_predictors.append(f'{pred}_standardized')
        else:
            final_predictors.append(pred)

    # Remove rows with missing data
    analysis_vars = [dependent_var] + final_predictors
    analysis_df = analysis_df.dropna(subset=analysis_vars)

    if len(analysis_df) < 10:
        print(f"WARNING: Insufficient data for {dependent_var} analysis (n={len(analysis_df)})")
        return None

    print(f"Analysis sample size: {len(analysis_df)}")

    # Prepare X and y
    X = analysis_df[final_predictors]
    y = analysis_df[dependent_var]

    # Add intercept
    X_with_const = sm.add_constant(X)

    # Fit OLS model
    ols_model = sm.OLS(y, X_with_const)
    ols_results = ols_model.fit()
    robust_results = ols_results.get_robustcov_results(cov_type='HC3')

    # Extract statistics from robust results
    n = int(robust_results.nobs)
    p = len(final_predictors)
    r_squared = ols_results.rsquared
    f_statistic = ols_results.fvalue
    f_p_value = ols_results.f_pvalue

    # Exclude intercept for reporting
    params = robust_results.params
    bse = robust_results.bse
    tvalues = robust_results.tvalues
    pvalues = robust_results.pvalues
    conf_int = robust_results.conf_int(alpha=0.05)
    # Remove intercept (first entry)
    coefficients = params[1:]
    standard_errors = bse[1:]
    t_statistics = tvalues[1:]
    p_values = pvalues[1:]
    ci_lower = conf_int[1:, 0]
    ci_upper = conf_int[1:, 1]

    # VIF calculation (on non-intercept predictors)
    vif_values = []
    if len(final_predictors) > 1:
        for i in range(len(final_predictors)):
            vif = variance_inflation_factor(X.values, i)
            vif_values.append(vif)
    else:
        vif_values = [1.0]

    # Model diagnostics
    residuals = robust_results.resid
    # Shapiro-Wilk test for normality
    if len(residuals) <= 5000:  # Shapiro-Wilk has sample size limit
        shapiro_stat, shapiro_p = shapiro(residuals)
    else:
        shapiro_stat, shapiro_p = np.nan, np.nan

    # Breusch-Pagan test for homoscedasticity
    try:
        bp_stat, bp_p, _, _ = het_breuschpagan(residuals, X)
    except:
        bp_stat, bp_p = np.nan, np.nan

    # Cook's distance
    influence = ols_results.get_influence()
    cooks_d = influence.cooks_distance[0]
    influential_threshold = 4 / n
    n_influential = np.sum(cooks_d > influential_threshold)

    # Create results dictionary
    results = {
        'dependent_variable': dependent_var,
        'sample_size': n,
        'r_squared': r_squared,
        'f_statistic': f_statistic,
        'f_p_value': f_p_value,
        'shapiro_stat': shapiro_stat,
        'shapiro_p': shapiro_p,
        'bp_stat': bp_stat,
        'bp_p': bp_p,
        'n_influential': n_influential,
        'predictors': final_predictors,
        'coefficients': coefficients,
        'standard_errors': standard_errors,
        't_statistics': t_statistics,
        'p_values': p_values,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'vif_values': vif_values
    }

    print(f"Regression completed for {dependent_var}")
    print(f"R² = {r_squared:.4f}, F = {f_statistic:.4f}, p = {f_p_value:.4f}")

    return results

def main():
    """Main function to execute the VVIQ2 analysis pipeline"""
    try:
        print("Starting VVIQ2 analysis pipeline...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Load VVIQ2 data
        print("Loading VVIQ2 data...")
        vviq2_file = "raw_data/Vividness of Visual Imagery Questionnaire-2.csv"
        
        if not os.path.exists(vviq2_file):
            print(f"ERROR: VVIQ2 file not found: {vviq2_file}")
            return 1
        
        vviq2_df = pd.read_csv(vviq2_file)
        vviq2_df.columns = vviq2_df.columns.str.strip()  # Strip whitespace from column names
        print(f"VVIQ2 data loaded: {vviq2_df.shape}")
        print("VVIQ2 columns:", list(vviq2_df.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq2_df.head(3))
        
        # NOW verify required columns exist (after stripping)
        required_vviq2_cols = ['PROLIFIC_PID']
        missing_cols = [col for col in required_vviq2_cols if col not in vviq2_df.columns]
        if missing_cols:
            print(f"ERROR: Missing required VVIQ2 columns: {missing_cols}")
            return 1
        
        # Calculate VVIQ2 scores
        vviq2_scores = calculate_vviq2_scores(vviq2_df)
        # Validate that some VVIQ2 scores were calculated
        valid_total_scores = sum(pd.notna(vviq2_scores['total_VVIQ2_score']))
        if valid_total_scores == 0:
            print("ERROR: No valid VVIQ2 total scores calculated - check column name matching")
            return 1
        print("VVIQ2 scores calculated:")
        print("Columns:", list(vviq2_scores.columns))
        print("First 2 rows:")
        print(vviq2_scores.head(2))
        
        # Find and load mixture model parameters
        print("Loading mixture model parameters...")
        mixture_pattern = "outputs/mixture_model_parameters_*.csv"
        mixture_file = find_latest_file(mixture_pattern)
        
        if not mixture_file:
            print(f"ERROR: No mixture model parameters file found matching: {mixture_pattern}")
            return 1
        
        print(f"Using mixture model file: {mixture_file}")
        mixture_df = pd.read_csv(mixture_file)
        print(f"Mixture model data loaded: {mixture_df.shape}")
        print("Mixture model columns:", list(mixture_df.columns))
        print("First 3 rows of mixture model data:")
        print(mixture_df.head(3))
        
        # Print unique values for key columns
        if 'convergence_status' in mixture_df.columns:
            print("Unique convergence_status values:", mixture_df['convergence_status'].unique())
        if 'best_model' in mixture_df.columns:
            print("Unique best_model values:", mixture_df['best_model'].unique())
        
        # Find and load control variables
        print("Loading control variables...")
        control_pattern = "outputs/control_variables_*.csv"
        control_file = find_latest_file(control_pattern)
        
        if not control_file:
            print(f"ERROR: No control variables file found matching: {control_pattern}")
            return 1
        
        print(f"Using control variables file: {control_file}")
        control_df = pd.read_csv(control_file)
        print(f"Control variables data loaded: {control_df.shape}")
        print("Control variables columns:", list(control_df.columns))
        print("First 3 rows of control variables data:")
        print(control_df.head(3))
        
        # Print unique values for key columns
        if 'valid_for_analysis' in control_df.columns:
            print("Unique valid_for_analysis values:", control_df['valid_for_analysis'].unique())
        
        # Merge datasets
        print("Merging datasets...")
        
        # First merge VVIQ2 with mixture model data
        merged_df = pd.merge(vviq2_scores, mixture_df, on='participantId', how='inner')
        print(f"After merging VVIQ2 and mixture model data: {merged_df.shape}")
        
        # Then merge with control variables
        merged_df = pd.merge(merged_df, control_df, on='participantId', how='inner')
        print(f"After merging all datasets: {merged_df.shape}")
        
        print("Merged data columns:", list(merged_df.columns))
        print("First 2 rows of merged data:")
        print(merged_df.head(2))
        
        # Apply exclusion criteria
        print("Applying exclusion criteria...")
        
        initial_n = len(merged_df)
        print(f"Initial sample size: {initial_n}")
        
        # Exclude participants with convergence_status=False
        if 'convergence_status' in merged_df.columns:
            convergence_excluded = merged_df['convergence_status'] == False
            print(f"Participants excluded for convergence_status=False: {sum(convergence_excluded)}")
            merged_df = merged_df[merged_df['convergence_status'] == True]
        
        # Exclude participants with valid_for_analysis=False
        if 'valid_for_analysis' in merged_df.columns:
            validity_excluded = merged_df['valid_for_analysis'] == False
            print(f"Participants excluded for valid_for_analysis=False: {sum(validity_excluded)}")
            merged_df = merged_df[merged_df['valid_for_analysis'] == True]
        
        final_n = len(merged_df)
        print(f"Final sample size after exclusions: {final_n}")
        print(f"Total excluded: {initial_n - final_n}")
        
        # Save VVIQ2 scores
        timestamp = create_timestamp()
        vviq2_output_file = f"outputs/VVIQ2_scores_{timestamp}.csv"
        
        vviq2_output_cols = [
            'participantId', 'total_VVIQ2_score', 'familiar_person_score',
            'sunrise_score', 'shop_front_score', 'countryside_score',
            'driving_score', 'beach_score', 'railway_station_score', 'garden_score'
        ]
        
        vviq2_output = merged_df[vviq2_output_cols].copy()
        vviq2_output.to_csv(vviq2_output_file, index=False)
        print(f"VVIQ2 scores saved to: {vviq2_output_file}")
        
        # Define predictors and control variables
        primary_predictor = 'vonMises_kappa'
        control_vars_initial = [
            'VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 'MRT_rt_cv', 'engagement_index', 'VWM_timeout_rate'
        ]

        # Filter out control variables with zero variance
        control_vars = []
        for var in control_vars_initial:
            if var in merged_df.columns:
                valid_data = merged_df[var].dropna()
                if len(valid_data) > 0 and valid_data.std() > 0:
                    control_vars.append(var)
                else:
                    print(f"INFO: Excluding '{var}' from control variables due to zero variance or insufficient data.")
            else:
                print(f"INFO: Excluding '{var}' from control variables - column not found.")

        all_predictors = [primary_predictor] + control_vars
        
        # Check predictor availability
        available_predictors = [p for p in all_predictors if p in merged_df.columns]
        missing_predictors = [p for p in all_predictors if p not in merged_df.columns]
        
        print(f"Available predictors: {available_predictors}")
        if missing_predictors:
            print(f"WARNING: Missing predictors: {missing_predictors}")
        
        # Run primary regression analysis
        print("Running primary regression analysis...")
        primary_results = run_regression_analysis(
            merged_df, 'total_VVIQ2_score', available_predictors, control_vars
        )

        # Prepare regression results output and add primary results
        print("Preparing regression results output...")
        results_rows = []

        # Add primary analysis results first
        if primary_results:
            for i, predictor in enumerate(primary_results['predictors']):
                row = {
                    'analysis_type': 'primary',
                    'dependent_variable': primary_results['dependent_variable'],
                    'predictor_variable': predictor,
                    'coefficient': primary_results['coefficients'][i],
                    'standard_error': primary_results['standard_errors'][i],
                    't_statistic': primary_results['t_statistics'][i],
                    'p_value': primary_results['p_values'][i],
                    'p_value_fdr_corrected': np.nan,
                    'confidence_interval_lower': primary_results['ci_lower'][i],
                    'confidence_interval_upper': primary_results['ci_upper'][i],
                    'VIF': primary_results['vif_values'][i],
                    'model_r_squared': primary_results['r_squared'],
                    'model_f_statistic': primary_results['f_statistic'],
                    'model_p_value': primary_results['f_p_value'],
                    'sample_size': primary_results['sample_size']
                }
                results_rows.append(row)

            # Check significance of primary predictor
            if primary_predictor in primary_results['predictors']:
                primary_predictor_idx = primary_results['predictors'].index(primary_predictor)
                kappa_p_value = primary_results['p_values'][primary_predictor_idx]
                print(f"\nChecking significance of '{primary_predictor}': p-value = {kappa_p_value:.4f}")

                if kappa_p_value < 0.05:
                    print("Primary predictor is significant. Proceeding with secondary analyses.")

                    # Run secondary analyses on subscales
                    print("Running secondary analyses on VVIQ2 subscales...")
                    subscales = [
                        'familiar_person_score', 'sunrise_score', 'shop_front_score',
                        'countryside_score', 'driving_score', 'beach_score',
                        'railway_station_score', 'garden_score'
                    ]

                    subscale_results = []
                    for subscale in subscales:
                        if subscale in merged_df.columns:
                            result = run_regression_analysis(
                                merged_df, subscale, available_predictors, control_vars
                            )
                            if result:
                                subscale_results.append(result)

                    # Apply FDR correction to primary predictor only across subscales
                    print("Applying FDR correction to primary predictor across subscales...")
                    primary_predictor_p_values = []
                    for result in subscale_results:
                        # Find the index of the primary predictor
                        if primary_predictor in result['predictors']:
                            primary_idx = result['predictors'].index(primary_predictor)
                            primary_predictor_p_values.append(result['p_values'][primary_idx])

                    if primary_predictor_p_values:
                        fdr_rejected, fdr_corrected_p, _, _ = multipletests(primary_predictor_p_values, alpha=0.05, method='fdr_bh')
                        print(f"FDR correction applied to {len(primary_predictor_p_values)} primary predictor p-values")
                    else:
                        fdr_corrected_p = []

                    # Add subscale analysis results
                    fdr_p_index = 0
                    for result in subscale_results:
                        for i, predictor in enumerate(result['predictors']):
                            # Only apply FDR correction to primary predictor
                            if predictor == primary_predictor and fdr_p_index < len(fdr_corrected_p):
                                fdr_p = fdr_corrected_p[fdr_p_index]
                                fdr_p_index += 1
                            else:
                                fdr_p = np.nan

                            row = {
                                'analysis_type': 'subscale',
                                'dependent_variable': result['dependent_variable'],
                                'predictor_variable': predictor,
                                'coefficient': result['coefficients'][i],
                                'standard_error': result['standard_errors'][i],
                                't_statistic': result['t_statistics'][i],
                                'p_value': result['p_values'][i],
                                'p_value_fdr_corrected': fdr_p,
                                'confidence_interval_lower': result['ci_lower'][i],
                                'confidence_interval_upper': result['ci_upper'][i],
                                'VIF': result['vif_values'][i],
                                'model_r_squared': result['r_squared'],
                                'model_f_statistic': result['f_statistic'],
                                'model_p_value': result['f_p_value'],
                                'sample_size': result['sample_size']
                            }
                            results_rows.append(row)

                    # Save regression results
                    results_df = pd.DataFrame(results_rows)
                    results_output_file = f"outputs/VVIQ2_regression_results_{timestamp}.csv"
                    results_df.to_csv(results_output_file, index=False)
                    print(f"Regression results saved to: {results_output_file}")

                    print("Results summary:")
                    print(f"Total regression analyses: {len(subscale_results) + (1 if primary_results else 0)}")
                    print(f"Output files created: {vviq2_output_file}, {results_output_file}")

                else:
                    print("Primary predictor is not significant (p >= 0.05). Skipping secondary analyses.")
                    # Only save primary results
                    results_df = pd.DataFrame(results_rows)
                    results_output_file = f"outputs/VVIQ2_regression_results_{timestamp}.csv"
                    results_df.to_csv(results_output_file, index=False)
                    print(f"Regression results saved to: {results_output_file}")

                    print("Results summary:")
                    print(f"Total regression analyses: 1 (primary only, subscales skipped)")
                    print(f"Output files created: {vviq2_output_file}, {results_output_file}")

            else:
                print(f"Primary predictor '{primary_predictor}' not found in primary results. Skipping secondary analyses.")
                results_df = pd.DataFrame(results_rows)
                results_output_file = f"outputs/VVIQ2_regression_results_{timestamp}.csv"
                results_df.to_csv(results_output_file, index=False)
                print(f"Regression results saved to: {results_output_file}")

                print("Results summary:")
                print(f"Total regression analyses: 1 (primary only, subscales skipped)")
                print(f"Output files created: {vviq2_output_file}, {results_output_file}")

        # Print model diagnostics
        print("\nModel diagnostics summary:")
        if primary_results:
            print(f"Primary analysis (total VVIQ2 score):")
            print(f"  R² = {primary_results['r_squared']:.4f}")
            print(f"  F = {primary_results['f_statistic']:.4f}, p = {primary_results['f_p_value']:.4f}")
            print(f"  Normality test p = {primary_results['shapiro_p']:.4f}")
            print(f"  Homoscedasticity test p = {primary_results['bp_p']:.4f}")
            print(f"  Influential observations: {primary_results['n_influential']}")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
