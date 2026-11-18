import pandas as pd
import numpy as np
import os
import glob
import re
from datetime import datetime
from scipy import stats
from sklearn.preprocessing import StandardScaler
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
import warnings
warnings.filterwarnings('ignore')

def find_latest_file(pattern):
    """
    Find the most recent file matching a pattern with timestamp.
    
    Parameters:
    pattern (str): File pattern with <TIMESTAMP> placeholder
    
    Returns:
    str: Path to the most recent matching file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard pattern
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        return None
    
    # Sort by modification time and return the most recent
    latest_file = max(matching_files, key=os.path.getmtime)
    return latest_file

def extract_vviq2_scores(response_text):
    """
    Extract numeric score from VVIQ2 response text.
    """
    if pd.isna(response_text):
        return None

    # Convert to string and strip whitespace
    response_str = str(response_text).strip()

    # Try to extract number from end of string
    match = re.search(r'(\d+)$', response_str)
    if match:
        score = int(match.group(1))
        if 1 <= score <= 5:
            return score

    # Try to extract any single digit 1-5
    match = re.search(r'\b([1-5])\b', response_str)
    if match:
        return int(match.group(1))

    return None

def calculate_vif(X):
    """
    Calculate Variance Inflation Factors for regression predictors.
    
    Parameters:
    X (pd.DataFrame): Predictor variables
    
    Returns:
    dict: VIF values for each predictor
    """
    vif_data = {}
    for i, col in enumerate(X.columns):
        if X[col].var() > 1e-9:
            vif_data[col] = variance_inflation_factor(X.values, i)
        else:
            vif_data[col] = np.nan
    return vif_data

def main():
    """
    Main function to process VVIQ2 data and run regression analyses.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 analysis script...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Find input files
        print("\nSearching for input files...")
        
        mixture_file = find_latest_file('outputs/mixture_model_parameters_<TIMESTAMP>.csv')
        control_file = find_latest_file('outputs/control_variables_<TIMESTAMP>.csv')
        vviq2_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        
        print(f"Mixture model file: {mixture_file}")
        print(f"Control variables file: {control_file}")
        print(f"VVIQ2 file: {vviq2_file}")
        
        # Check if files exist
        if not mixture_file or not os.path.exists(mixture_file):
            print("ERROR: Mixture model parameters file not found")
            return 1
        
        if not control_file or not os.path.exists(control_file):
            print("ERROR: Control variables file not found")
            return 1
            
        if not os.path.exists(vviq2_file):
            print("ERROR: VVIQ2 questionnaire file not found")
            return 1
        
        # Load data files
        print("\nLoading data files...")
        
        # Load mixture model parameters
        print("Loading mixture model parameters...")
        mixture_df = pd.read_csv(mixture_file)
        mixture_df.columns = mixture_df.columns.str.strip()
        print("Mixture model columns:", list(mixture_df.columns))
        print("First 3 rows of mixture model data:")
        print(mixture_df.head(3))
        
        # Load control variables
        print("\nLoading control variables...")
        control_df = pd.read_csv(control_file)
        control_df.columns = control_df.columns.str.strip()
        print("Control variables columns:", list(control_df.columns))
        print("First 3 rows of control variables data:")
        print(control_df.head(3))
        
        # Load VVIQ2 data
        print("\nLoading VVIQ2 questionnaire data...")
        vviq2_df = pd.read_csv(vviq2_file)
        vviq2_df.columns = vviq2_df.columns.str.strip()
        print("VVIQ2 columns:", list(vviq2_df.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq2_df.head(3))
        
        # Validate required columns
        print("\nValidating required columns...")
        
        required_mixture_cols = ['participantId', 'kappa_vonmises']
        required_control_cols = ['participantId', 'vwm_mean_accuracy_nonguess', 'vwm_rt_cv', 
                                'mrt_rt_cv', 'engagement_index', 'vwm_timeout_rate']
        
        missing_mixture = [col for col in required_mixture_cols if col not in mixture_df.columns]
        missing_control = [col for col in required_control_cols if col not in control_df.columns]
        
        if missing_mixture:
            print(f"ERROR: Missing columns in mixture model data: {missing_mixture}")
            return 1
        
        if missing_control:
            print(f"ERROR: Missing columns in control variables data: {missing_control}")
            return 1
        
        if 'PROLIFIC_PID' not in vviq2_df.columns:
            print("ERROR: Missing PROLIFIC_PID column in VVIQ2 data")
            return 1
        
        # Identify VVIQ2 item columns (should be 32 items)
        non_item_cols = ['Respondent ID', 'Collector ID', 'Start Date', 'End Date', 
                         'IP Address', 'Email Address', 'First Name', 'Last Name', 
                         'Custom Data 1', 'PROLIFIC_PID']
        item_columns = [col for col in vviq2_df.columns if col not in non_item_cols and not col.startswith('Unnamed')]
        print(f"\nFound {len(item_columns)} VVIQ2 item columns")
        print("Item columns:", item_columns[:5], "..." if len(item_columns) > 5 else "")
        print("Sample VVIQ2 responses from first participant:")
        for col in item_columns[:3]:  # Show first 3 items
            print(f"{col}: {vviq2_df.iloc[0][col]}")
        print("Detailed response analysis:")
        for i, col in enumerate(item_columns[:3]):
            response = vviq2_df.iloc[0][col]
            extracted_score = extract_vviq2_scores(response)
            print(f"Item {i+1}: '{response}' -> Score: {extracted_score}")

        if len(item_columns) != 32:
            print(f"WARNING: Expected 32 VVIQ2 items, found {len(item_columns)}")

        # Process VVIQ2 data
        print("\nProcessing VVIQ2 responses...")

        # Create results dataframe
        vviq2_results = []
        exclusions = {'missing_responses': 0, 'patterned_responses': 0, 'invalid_scores': 0}

        for idx, row in vviq2_df.iterrows():
            participant_id = str(row['PROLIFIC_PID'])

            # Extract scores once
            scores = []
            for col in item_columns:
                score = extract_vviq2_scores(row[col])
                if score is None:
                    exclusions['invalid_scores'] += 1
                    break
                scores.append(score)

            # Check if all scores were successfully extracted
            if len(scores) != len(item_columns):
                continue

            # Check for patterned responses (all same value)
            if len(set(scores)) == 1:
                exclusions['patterned_responses'] += 1
                continue

            # Calculate total score
            total_score = sum(scores)

            # Validate total score range
            if not (32 <= total_score <= 160):
                print(f"WARNING: Invalid total score {total_score} for participant {participant_id}")
                exclusions['invalid_scores'] += 1
                continue

            # Calculate subscale scores
            subscale_scores = {}
            scenario_names = ['person', 'sunrise', 'shop', 'countryside',
                            'driving', 'beach', 'station', 'garden']

            for i, scenario in enumerate(scenario_names):
                start_idx = i * 4
                end_idx = start_idx + 4
                subscale_score = sum(scores[start_idx:end_idx])

                # Validate subscale range
                if not (4 <= subscale_score <= 20):
                    print(f"WARNING: Invalid subscale score {subscale_score} for {scenario} in participant {participant_id}")
                    break

                subscale_scores[f'vviq2_{scenario}_score'] = subscale_score

            if len(subscale_scores) != 8:
                exclusions['invalid_scores'] += 1
                continue

            # Store results
            result = {
                'participantId': participant_id,
                'vviq2_total_score': total_score,
                **subscale_scores
            }
            vviq2_results.append(result)

        print(f"\nVVIQ2 processing complete:")
        print(f"Valid participants: {len(vviq2_results)}")
        for reason, count in exclusions.items():
            print(f"Excluded for {reason}: {count}")

        # Convert to dataframe
        vviq2_scores_df = pd.DataFrame(vviq2_results)
        print("\nVVIQ2 scores dataframe:")
        print("Columns:", list(vviq2_scores_df.columns))
        print("First 2 rows:")
        print(vviq2_scores_df.head(2))
        
        # Merge datasets
        print("\nMerging datasets...")

        if len(vviq2_scores_df) == 0:
            print("ERROR: No valid VVIQ2 participants found - cannot proceed with regression analysis")
            return 1
        
        # Start with mixture model data
        regression_df = mixture_df[['participantId', 'kappa_vonmises']].copy()
        print(f"Starting with {len(regression_df)} participants from mixture model")
        
        # Merge with control variables
        regression_df = regression_df.merge(
            control_df[required_control_cols], 
            on='participantId', 
            how='inner'
        )
        print(f"After merging control variables: {len(regression_df)} participants")
        
        # Merge with VVIQ2 scores
        regression_df = regression_df.merge(
            vviq2_scores_df, 
            on='participantId', 
            how='inner'
        )
        print(f"After merging VVIQ2 scores: {len(regression_df)} participants")
        
        print("\nFinal regression dataframe:")
        print("Columns:", list(regression_df.columns))
        print("First 2 rows:")
        print(regression_df.head(2))
        
        # Z-standardize control variables
        print("\nZ-standardizing control variables...")
        
        control_vars = ['vwm_mean_accuracy_nonguess', 'vwm_rt_cv', 'mrt_rt_cv', 
                       'engagement_index', 'vwm_timeout_rate']

        # Check variance and filter control variables
        control_vars_filtered = []
        for var in control_vars:
            var_variance = regression_df[var].var()
            if var_variance > 1e-9:
                control_vars_filtered.append(var)
            else:
                print(f"WARNING: Excluding '{var}' from analysis due to zero variance (variance={var_variance})")

        if len(control_vars_filtered) == 0:
            print("ERROR: All control variables have zero variance. Cannot proceed.")
            return 1

        scaler = StandardScaler()
        standardized_controls = scaler.fit_transform(regression_df[control_vars_filtered])
        
        for i, var in enumerate(control_vars_filtered):
            regression_df[f'z_{var}'] = standardized_controls[:, i]
        
        print("Standardized control variables added")
        
        # Prepare regression variables
        z_control_vars = [f'z_{var}' for var in control_vars_filtered]
        all_predictors = ['kappa_vonmises'] + z_control_vars
        
        print(f"\nRegression predictors: {all_predictors}")
        
        # Run primary regression for total VVIQ2 score
        print("\nRunning primary regression for total VVIQ2 score...")
        
        # Prepare data
        y_total = regression_df['vviq2_total_score']
        X_total = regression_df[all_predictors]
        X_total_with_const = sm.add_constant(X_total)
        
        # Fit model
        model_total = sm.OLS(y_total, X_total_with_const).fit()
        
        print("Total VVIQ2 score regression results:")
        print(model_total.summary())
        
        # Calculate VIF
        vif_values = calculate_vif(X_total)
        print("\nVariance Inflation Factors:")
        for var, vif in vif_values.items():
            print(f"{var}: {vif:.3f}")
            if vif > 5:
                print(f"WARNING: High VIF detected for {var} (VIF = {vif:.3f})")
        
        # Extract results for total score
        regression_results = []
        
        for i, predictor in enumerate(['const'] + all_predictors):
            if predictor == 'const':
                continue
                
            coef = model_total.params[predictor]
            se = model_total.bse[predictor]
            p_val = model_total.pvalues[predictor]
            ci_lower, ci_upper = model_total.conf_int().loc[predictor]
            vif_val = vif_values.get(predictor, np.nan)
            
            regression_results.append({
                'model_type': 'primary',
                'outcome_measure': 'vviq2_total_score',
                'predictor': predictor,
                'coefficient': coef,
                'standard_error': se,
                'p_value': p_val,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'vif': vif_val,
                'r_squared': model_total.rsquared,
                'fdr_adjusted_p': np.nan
            })
        
        # Run secondary analyses for subscales
        print("\nRunning secondary analyses for VVIQ2 subscales...")
        
        subscale_names = ['vviq2_person_score', 'vviq2_sunrise_score', 'vviq2_shop_score', 
                         'vviq2_countryside_score', 'vviq2_driving_score', 'vviq2_beach_score',
                         'vviq2_station_score', 'vviq2_garden_score']
        
        subscale_results = []
        kappa_p_values = []  # For FDR correction
        
        for subscale in subscale_names:
            print(f"\nRunning regression for {subscale}...")
            
            y_subscale = regression_df[subscale]
            X_subscale = regression_df[all_predictors]
            X_subscale_with_const = sm.add_constant(X_subscale)
            
            model_subscale = sm.OLS(y_subscale, X_subscale_with_const).fit()
            
            print(f"{subscale} regression R-squared: {model_subscale.rsquared:.4f}")
            
            # Store kappa p-value for FDR correction
            kappa_p_values.append(model_subscale.pvalues['kappa_vonmises'])
            
            # Store all results
            for predictor in all_predictors:
                coef = model_subscale.params[predictor]
                se = model_subscale.bse[predictor]
                p_val = model_subscale.pvalues[predictor]
                ci_lower, ci_upper = model_subscale.conf_int().loc[predictor]
                vif_val = vif_values.get(predictor, np.nan)
                
                subscale_results.append({
                    'model_type': 'secondary',
                    'outcome_measure': subscale,
                    'predictor': predictor,
                    'coefficient': coef,
                    'standard_error': se,
                    'p_value': p_val,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    'vif': vif_val,
                    'r_squared': model_subscale.rsquared,
                    'fdr_adjusted_p': np.nan
                })
        
        # Apply FDR correction for kappa coefficients across subscales
        print("\nApplying FDR correction for multiple comparisons...")
        
        rejected, fdr_p_values, _, _ = multipletests(kappa_p_values, alpha=0.05, method='fdr_bh')
        
        print("FDR correction results for kappa_vonmises across subscales:")
        for i, (subscale, orig_p, fdr_p, is_sig) in enumerate(zip(subscale_names, kappa_p_values, fdr_p_values, rejected)):
            print(f"{subscale}: p={orig_p:.4f}, FDR p={fdr_p:.4f}, Significant: {is_sig}")
        
        # Update FDR p-values in subscale results
        subscale_idx = 0
        for i, result in enumerate(subscale_results):
            if result['predictor'] == 'kappa_vonmises':
                subscale_results[i]['fdr_adjusted_p'] = fdr_p_values[subscale_idx]
                subscale_idx += 1
        
        # Combine all regression results
        all_regression_results = regression_results + subscale_results
        
        # Save VVIQ2 scores
        print("\nSaving VVIQ2 scores...")
        vviq2_output_file = f'outputs/vviq2_scores_{timestamp}.csv'
        vviq2_scores_df.to_csv(vviq2_output_file, index=False)
        print(f"VVIQ2 scores saved to: {vviq2_output_file}")
        
        # Save regression results
        print("\nSaving regression results...")
        regression_results_df = pd.DataFrame(all_regression_results)
        regression_output_file = f'outputs/vviq2_regression_results_{timestamp}.csv'
        regression_results_df.to_csv(regression_output_file, index=False)
        print(f"Regression results saved to: {regression_output_file}")
        
        print("\nFinal regression results dataframe:")
        print("Columns:", list(regression_results_df.columns))
        print("First 2 rows:")
        print(regression_results_df.head(2))
        
        print("\nSummary of significant results:")
        significant_results = regression_results_df[regression_results_df['p_value'] < 0.05]
        if len(significant_results) > 0:
            print(f"Found {len(significant_results)} significant associations (p < 0.05)")
            for _, row in significant_results.iterrows():
                print(f"{row['predictor']} -> {row['outcome_measure']}: β={row['coefficient']:.4f}, p={row['p_value']:.4f}")
        else:
            print("No significant associations found (p < 0.05)")
        
        # Check for FDR significant results
        fdr_significant = regression_results_df[
            (regression_results_df['predictor'] == 'kappa_vonmises') & 
            (regression_results_df['fdr_adjusted_p'] < 0.05)
        ]
        if len(fdr_significant) > 0:
            print(f"\nFound {len(fdr_significant)} FDR-significant kappa associations:")
            for _, row in fdr_significant.iterrows():
                print(f"kappa_vonmises -> {row['outcome_measure']}: β={row['coefficient']:.4f}, FDR p={row['fdr_adjusted_p']:.4f}")
        else:
            print("\nNo FDR-significant kappa associations found")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
