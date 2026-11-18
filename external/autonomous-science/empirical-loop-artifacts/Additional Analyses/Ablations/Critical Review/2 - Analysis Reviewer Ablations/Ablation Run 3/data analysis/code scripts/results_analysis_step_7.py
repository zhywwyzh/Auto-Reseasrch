import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.multitest import multipletests
import sys

def extract_numeric_score(response_text):
    """
    Robustly extract numeric score (1-5) from VVIQ2 response text.
    Returns np.nan if extraction fails.
    """
    if pd.isna(response_text):
        return np.nan
    try:
        response_str = str(response_text).strip()
        import re
        matches = re.findall(r'[1-5]', response_str)
        if matches:
            return int(matches[-1])  # Take last match
        return np.nan
    except:
        return np.nan

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
    # Sort by modification time and return the most recent
    return max(files, key=os.path.getmtime)

def standardize_variables(df, columns):
    """
    Z-standardize specified columns in dataframe.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    columns (list): List of column names to standardize
    
    Returns:
    pd.DataFrame: Dataframe with standardized columns
    """
    df_copy = df.copy()
    for col in columns:
        if col in df_copy.columns:
            df_copy[col] = stats.zscore(df_copy[col], nan_policy='omit')
    return df_copy

def calculate_vif(X):
    """
    Calculate Variance Inflation Factor for all predictors.
    
    Parameters:
    X (pd.DataFrame): Predictor variables dataframe
    
    Returns:
    dict: Dictionary with VIF values for each predictor
    """
    vif_data = {}
    for i, col in enumerate(X.columns):
        try:
            vif_data[col] = variance_inflation_factor(X.values, i)
        except:
            vif_data[col] = np.nan
    return vif_data

def main():
    """
    Main function to execute VVIQ2 analysis with VWM mixture parameters.
    """
    try:
        print("Starting VVIQ2 analysis script...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Read VVIQ2 data
        print("\n=== Reading VVIQ2 data ===")
        vviq2_file = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
        if not os.path.exists(vviq2_file):
            print(f"Error: VVIQ2 file not found: {vviq2_file}")
            return 1
            
        vviq2_df = pd.read_csv(vviq2_file)
        vviq2_df.columns = vviq2_df.columns.str.strip()
        print(f"VVIQ2 data shape: {vviq2_df.shape}")
        print("VVIQ2 columns:")
        print(vviq2_df.columns.tolist())
        print("First 3 rows of VVIQ2 data:")
        print(vviq2_df.head(3))
        
        # Check for PROLIFIC_PID column
        if 'PROLIFIC_PID' not in vviq2_df.columns:
            print("Error: PROLIFIC_PID column not found in VVIQ2 data")
            return 1
        
        # Find VWM mixture parameters file
        print("\n=== Reading VWM mixture parameters ===")
        vwm_pattern = "outputs/vwm_mixture_parameters_*.csv"
        vwm_file = find_latest_file(vwm_pattern)
        if not vwm_file:
            print(f"Error: No VWM mixture parameters file found matching pattern: {vwm_pattern}")
            return 1
            
        print(f"Using VWM file: {vwm_file}")
        vwm_df = pd.read_csv(vwm_file)
        vwm_df.columns = vwm_df.columns.str.strip()
        print(f"VWM data shape: {vwm_df.shape}")
        print("VWM columns:")
        print(vwm_df.columns.tolist())
        print("First 3 rows of VWM data:")
        print(vwm_df.head(3))
        
        # Check required columns
        if 'participant_id' not in vwm_df.columns or 'von_mises_kappa' not in vwm_df.columns:
            print("Error: Required columns not found in VWM data")
            return 1
            
        # Find control variables file
        print("\n=== Reading control variables ===")
        control_pattern = "outputs/control_variables_*.csv"
        control_file = find_latest_file(control_pattern)
        if not control_file:
            print(f"Error: No control variables file found matching pattern: {control_pattern}")
            return 1
            
        print(f"Using control file: {control_file}")
        control_df = pd.read_csv(control_file)
        control_df.columns = control_df.columns.str.strip()
        print(f"Control data shape: {control_df.shape}")
        print("Control columns:")
        print(control_df.columns.tolist())
        print("First 3 rows of control data:")
        print(control_df.head(3))
        
        # Check required control columns
        required_control_cols = ['participant_id', 'vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation', 
                               'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate']
        missing_control_cols = [col for col in required_control_cols if col not in control_df.columns]
        if missing_control_cols:
            print(f"Error: Missing control columns: {missing_control_cols}")
            return 1
        
        # Find included participants file
        print("\n=== Reading included participants ===")
        included_pattern = "outputs/included_participants_*.csv"
        included_file = find_latest_file(included_pattern)
        if not included_file:
            print(f"Error: No included participants file found matching pattern: {included_pattern}")
            return 1
            
        print(f"Using included file: {included_file}")
        included_df = pd.read_csv(included_file)
        included_df.columns = included_df.columns.str.strip()
        print(f"Included data shape: {included_df.shape}")
        print("Included columns:")
        print(included_df.columns.tolist())
        print("First 3 rows of included data:")
        print(included_df.head(3))
        
        # Check required included columns
        if 'participant_id' not in included_df.columns or 'included_in_analysis' not in included_df.columns:
            print("Error: Required columns not found in included participants data")
            return 1
            
        # Print unique values for inclusion column
        print("Unique values in included_in_analysis column:")
        print(included_df['included_in_analysis'].unique())
        
        # Filter to included participants only
        included_participants = included_df[included_df['included_in_analysis'] == True]['participant_id'].tolist()
        print(f"Number of included participants: {len(included_participants)}")
        
        # Process VVIQ2 responses
        print("\n=== Processing VVIQ2 responses ===")
        
        # Identify VVIQ2 item columns (should be 32 items)
        # Exclude metadata columns (first 9 columns), PROLIFIC_PID is assumed to be present
        metadata_cols = vviq2_df.columns[:9].tolist()
        vviq2_item_cols = [col for col in vviq2_df.columns if col not in metadata_cols and col != 'PROLIFIC_PID']
        print(f"Found {len(vviq2_item_cols)} VVIQ2 item columns (excluding metadata columns)")
        print("VVIQ2 item columns:", vviq2_item_cols)
        
        # Extract numeric scores from VVIQ2 responses
        vviq2_scores = vviq2_df.copy()
        
        # Process each item column to extract numeric scores
        for col in vviq2_item_cols:
            vviq2_scores[f"{col}_score"] = vviq2_scores[col].apply(extract_numeric_score)
        
        # Create list of score columns (should be 32)
        score_cols = [f"{col}_score" for col in vviq2_item_cols]
        
        # Filter to first 32 score columns if more than 32 exist
        if len(score_cols) > 32:
            score_cols = score_cols[:32]
            print(f"Using first 32 score columns out of {len(score_cols)} available")
        elif len(score_cols) < 32:
            print(f"Warning: Only found {len(score_cols)} score columns, expected 32")
        
        print(f"Using {len(score_cols)} score columns for analysis")
        
        # Calculate total VVIQ2 score
        vviq2_scores['vviq2_total_score'] = vviq2_scores[score_cols].sum(axis=1)
        
        # Calculate subscale scores (4 items each)
        subscales = {
            'vviq2_familiar_person': score_cols[0:4],
            'vviq2_sunrise': score_cols[4:8],
            'vviq2_shop_front': score_cols[8:12],
            'vviq2_countryside': score_cols[12:16],
            'vviq2_driving': score_cols[16:20],
            'vviq2_beach': score_cols[20:24],
            'vviq2_railway_station': score_cols[24:28],
            'vviq2_garden': score_cols[28:32]
        }
        
        for subscale_name, item_cols in subscales.items():
            # Only use available columns
            available_cols = [col for col in item_cols if col in vviq2_scores.columns]
            if available_cols:
                vviq2_scores[subscale_name] = vviq2_scores[available_cols].sum(axis=1)
            else:
                vviq2_scores[subscale_name] = np.nan

        # Convert to numeric after calculation
        vviq2_scores['vviq2_total_score'] = pd.to_numeric(vviq2_scores['vviq2_total_score'], errors='coerce')
        for subscale_name in subscales.keys():
            vviq2_scores[subscale_name] = pd.to_numeric(vviq2_scores[subscale_name], errors='coerce')

        # Validation prints for extraction
        print("Validation: vviq2_total_score dtype:", vviq2_scores['vviq2_total_score'].dtype)
        print("Validation: vviq2_total_score min/max:", vviq2_scores['vviq2_total_score'].min(), vviq2_scores['vviq2_total_score'].max())
        for subscale_name in subscales.keys():
            print(f"Validation: {subscale_name} dtype:", vviq2_scores[subscale_name].dtype)
            print(f"Validation: {subscale_name} min/max:", vviq2_scores[subscale_name].min(), vviq2_scores[subscale_name].max())
        
        # Rename PROLIFIC_PID to participant_id for merging
        vviq2_scores['participant_id'] = vviq2_scores['PROLIFIC_PID']
        
        # Filter to included participants
        vviq2_included = vviq2_scores[vviq2_scores['participant_id'].isin(included_participants)]
        print(f"VVIQ2 data for included participants: {vviq2_included.shape}")
        
        # Check for missing VVIQ2 data
        missing_vviq2 = vviq2_included['vviq2_total_score'].isna().sum()
        print(f"Participants with missing VVIQ2 total scores: {missing_vviq2}")
        
        # Merge datasets
        print("\n=== Merging datasets ===")
        
        # Start with VVIQ2 data
        merged_df = vviq2_included[['participant_id', 'vviq2_total_score'] + list(subscales.keys())].copy()
        
        # Merge with VWM mixture parameters
        merged_df = merged_df.merge(vwm_df[['participant_id', 'von_mises_kappa']], 
                                  on='participant_id', how='left')
        print(f"After merging VWM data: {merged_df.shape}")
        
        # Rename kappa column
        merged_df['kappa'] = merged_df['von_mises_kappa']
        
        # Merge with control variables
        merged_df = merged_df.merge(control_df[required_control_cols], 
                                  on='participant_id', how='left')
        print(f"After merging control data: {merged_df.shape}")
        
        # Remove participants with missing data
        print("\n=== Data cleaning ===")
        print("Missing data summary before cleaning:")
        print(merged_df.isnull().sum())
        
        # Remove participants with missing key variables
        complete_cases = merged_df.dropna(subset=['vviq2_total_score', 'kappa'] + 
                                        ['vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation',
                                         'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate'])
        
        print(f"Complete cases after removing missing data: {complete_cases.shape}")
        print(f"Participants excluded due to missing data: {merged_df.shape[0] - complete_cases.shape[0]}")
        
        # Standardize control variables
        print("\n=== Standardizing control variables ===")
        control_vars = ['vwm_mean_accuracy_degrees', 'vwm_rt_coefficient_variation',
                       'mrt_rt_coefficient_variation', 'engagement_index', 'vwm_timeout_rate']
        
        analysis_df = standardize_variables(complete_cases, control_vars)
        
        print("Descriptive statistics for key variables:")
        print(analysis_df[['vviq2_total_score', 'kappa'] + control_vars].describe())
        
        # Print variable types for measured variables
        print("\nVariable types for measured variables:")
        print(f"vviq2_total_score: {analysis_df['vviq2_total_score'].dtype}")
        print(f"kappa: {analysis_df['kappa'].dtype}")
        for var in control_vars:
            print(f"{var}: {analysis_df[var].dtype}")
        
        # Multiple linear regression for total VVIQ2 score
        print("\n=== Multiple linear regression for total VVIQ2 score ===")
        
        # Prepare predictor variables
        X = analysis_df[['kappa'] + control_vars].copy()
        X = sm.add_constant(X)  # Add intercept
        y = analysis_df['vviq2_total_score']
        
        print(f"Regression data shape - X: {X.shape}, y: {y.shape}")
        print("Predictor variables:")
        print(X.columns.tolist())
        
        # Fit regression model
        model = sm.OLS(y, X).fit()
        print("\nRegression results summary:")
        print(model.summary())
        
        # Extract results for kappa
        kappa_coef = model.params['kappa']
        kappa_se = model.bse['kappa']
        kappa_p = model.pvalues['kappa']
        r_squared = model.rsquared
        n_participants = len(analysis_df)
        
        print(f"Kappa coefficient: {kappa_coef}")
        print(f"Kappa standard error: {kappa_se}")
        print(f"Kappa p-value: {kappa_p}")
        print(f"Model R-squared: {r_squared}")
        print(f"Number of participants: {n_participants}")
        
        # Calculate VIF for multicollinearity
        print("\n=== Multicollinearity diagnostics ===")
        X_no_const = X.drop('const', axis=1)
        vif_dict = calculate_vif(X_no_const)
        print("VIF values:")
        for var, vif in vif_dict.items():
            print(f"{var}: {vif:.3f}")
        
        max_vif = max([v for v in vif_dict.values() if not np.isnan(v)])
        multicollinearity_flag = max_vif > 5
        
        print(f"Maximum VIF: {max_vif:.3f}")
        print(f"Multicollinearity flag (VIF > 5): {multicollinearity_flag}")
        
        # Save total regression results
        total_results = pd.DataFrame({
            'kappa_coefficient': [kappa_coef],
            'kappa_se': [kappa_se],
            'kappa_p_value': [kappa_p],
            'model_r_squared': [r_squared],
            'n_participants': [n_participants],
            'vif_max': [max_vif],
            'multicollinearity_flag': [multicollinearity_flag]
        })
        
        total_results_file = f"outputs/vviq2_total_regression_results_{timestamp}.csv"
        total_results.to_csv(total_results_file, index=False)
        print(f"\nTotal regression results saved to: {total_results_file}")
        
        # Secondary analyses on subscale scores
        print("\n=== Secondary analyses on subscale scores ===")
        
        subscale_results = []
        subscale_names = list(subscales.keys())
        
        for subscale in subscale_names:
            print(f"\nAnalyzing subscale: {subscale}")
            
            # Check for missing data in this subscale
            y_sub = analysis_df[subscale]
            valid_data = ~y_sub.isna()
            
            if valid_data.sum() == 0:
                print(f"No valid data for {subscale}, skipping...")
                continue
            
            # Fit regression for this subscale
            X_sub = X[valid_data]
            y_sub_clean = y_sub[valid_data]
            
            try:
                model_sub = sm.OLS(y_sub_clean, X_sub).fit()
                
                coef = model_sub.params['kappa']
                se = model_sub.bse['kappa']
                p_val = model_sub.pvalues['kappa']
                r_sq = model_sub.rsquared
                n_sub = len(y_sub_clean)
                
                subscale_results.append({
                    'subscale_name': subscale,
                    'kappa_coefficient': coef,
                    'kappa_se': se,
                    'kappa_p_value': p_val,
                    'model_r_squared': r_sq,
                    'n_participants': n_sub
                })
                
                print(f"Coefficient: {coef:.4f}, SE: {se:.4f}, p: {p_val:.4f}, R²: {r_sq:.4f}, n: {n_sub}")
                
            except Exception as e:
                print(f"Error fitting model for {subscale}: {e}")
                continue
        
        # Apply FDR correction
        if subscale_results:
            p_values = [result['kappa_p_value'] for result in subscale_results]
            rejected, p_corrected, alpha_sidak, alpha_bonf = multipletests(p_values, alpha=0.05, method='fdr_bh')
            
            print("\n=== FDR correction results ===")
            for i, result in enumerate(subscale_results):
                result['kappa_p_value_fdr'] = p_corrected[i]
                print(f"{result['subscale_name']}: Original p = {result['kappa_p_value']:.4f}, FDR p = {p_corrected[i]:.4f}")
        
        # Save subscale results
        if subscale_results:
            subscale_df = pd.DataFrame(subscale_results)
            subscale_results_file = f"outputs/vviq2_subscale_regression_results_{timestamp}.csv"
            subscale_df.to_csv(subscale_results_file, index=False)
            print(f"\nSubscale regression results saved to: {subscale_results_file}")
        
        # Save merged dataset with scores and predictors
        print("\n=== Saving final dataset ===")
        
        # Prepare final dataset with required columns
        final_columns = ['participant_id', 'kappa', 'vviq2_total_score'] + subscale_names + control_vars
        final_df = analysis_df[final_columns].copy()
        
        print("Final dataset columns:")
        print(final_df.columns.tolist())
        print("First 2 rows of final dataset:")
        print(final_df.head(2))
        
        final_file = f"outputs/vviq2_scores_with_predictors_{timestamp}.csv"
        final_df.to_csv(final_file, index=False)
        print(f"\nFinal dataset saved to: {final_file}")
        
        print("\n=== Analysis Summary ===")
        print(f"Total participants analyzed: {n_participants}")
        print(f"VVIQ2 total score range: {analysis_df['vviq2_total_score'].min():.0f} - {analysis_df['vviq2_total_score'].max():.0f}")
        print(f"Kappa range: {analysis_df['kappa'].min():.3f} - {analysis_df['kappa'].max():.3f}")
        print(f"Main effect of kappa on total VVIQ2: β = {kappa_coef:.4f}, p = {kappa_p:.4f}")
        print(f"Model explained variance: R² = {r_squared:.4f}")
        
        if subscale_results:
            significant_subscales = [r['subscale_name'] for r in subscale_results if r['kappa_p_value_fdr'] < 0.05]
            print(f"Significant subscales after FDR correction: {len(significant_subscales)}")
            if significant_subscales:
                print("Significant subscales:", significant_subscales)
        
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
