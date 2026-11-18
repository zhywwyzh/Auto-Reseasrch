import pandas as pd
import numpy as np
import os
import glob
import sys
from datetime import datetime
import statsmodels.api as sm
from scipy.stats import f
import pickle

def get_latest_file(pattern):
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

def load_and_validate_data():
    """
    Load and validate all required input files.
    
    Returns:
    tuple: (vwm_df, vviq_df, cog_df) or (None, None, None) if error
    """
    print("Loading and validating input files...")
    
    # Find VWM parameters file
    vwm_pattern = "outputs/VWM_parameters_*.csv"
    vwm_file = get_latest_file(vwm_pattern)
    if not vwm_file:
        print(f"Error: No file found matching pattern {vwm_pattern}")
        return None, None, None
    print(f"Found VWM parameters file: {vwm_file}")
    
    # Find VVIQ2 scores file
    vviq_pattern = "outputs/VVIQ2_cleaned_scores_*.csv"
    vviq_file = get_latest_file(vviq_pattern)
    if not vviq_file:
        print(f"Error: No file found matching pattern {vviq_pattern}")
        return None, None, None
    print(f"Found VVIQ2 scores file: {vviq_file}")
    
    # Find cognitive covariates file
    cog_pattern = "outputs/cognitive_covariates_*.csv"
    cog_file = get_latest_file(cog_pattern)
    if not cog_file:
        print(f"Error: No file found matching pattern {cog_pattern}")
        return None, None, None
    print(f"Found cognitive covariates file: {cog_file}")
    
    try:
        # Load VWM parameters
        print("\nLoading VWM parameters file...")
        vwm_df = pd.read_csv(vwm_file)
        print(f"VWM parameters columns: {list(vwm_df.columns)}")
        print(f"VWM parameters first 3 rows:\n{vwm_df.head(3)}")
        
        # Validate required columns
        vwm_required = ['participantId', 'vonMises_kappa', 'parameter_estimation_reliable']
        missing_vwm = [col for col in vwm_required if col not in vwm_df.columns]
        if missing_vwm:
            print(f"Error: Missing required columns in VWM file: {missing_vwm}")
            return None, None, None
        
        # Print unique values for key columns
        print(f"Unique parameter_estimation_reliable values: {vwm_df['parameter_estimation_reliable'].unique()}")
        print(f"vonMises_kappa data type: {vwm_df['vonMises_kappa'].dtype}")
        print(f"vonMises_kappa range: {vwm_df['vonMises_kappa'].min()} to {vwm_df['vonMises_kappa'].max()}")
        
        # Load VVIQ2 scores
        print("\nLoading VVIQ2 scores file...")
        vviq_df = pd.read_csv(vviq_file)
        print(f"VVIQ2 columns: {list(vviq_df.columns)}")
        print(f"VVIQ2 first 3 rows:\n{vviq_df.head(3)}")
        
        # Validate required columns
        vviq_required = ['participantId', 'total_VVIQ2_score', 'familiar_person_subscale',
                        'sunrise_subscale', 'shop_front_subscale', 'countryside_subscale',
                        'driving_subscale', 'beach_subscale', 'railway_station_subscale',
                        'garden_subscale', 'excluded_participant']
        missing_vviq = [col for col in vviq_required if col not in vviq_df.columns]
        if missing_vviq:
            print(f"Error: Missing required columns in VVIQ2 file: {missing_vviq}")
            return None, None, None
        
        # Print unique values for key columns
        print(f"Unique excluded_participant values: {vviq_df['excluded_participant'].unique()}")
        print(f"total_VVIQ2_score data type: {vviq_df['total_VVIQ2_score'].dtype}")
        print(f"total_VVIQ2_score range: {vviq_df['total_VVIQ2_score'].min()} to {vviq_df['total_VVIQ2_score'].max()}")
        
        # Load cognitive covariates
        print("\nLoading cognitive covariates file...")
        cog_df = pd.read_csv(cog_file)
        print(f"Cognitive covariates columns: {list(cog_df.columns)}")
        print(f"Cognitive covariates first 3 rows:\n{cog_df.head(3)}")
        
        # Validate required columns
        cog_required = ['participantId', 'mean_VWM_absolute_error', 
                       'VWM_rt_coefficient_variation', 'focus_loss_severity_index']
        missing_cog = [col for col in cog_required if col not in cog_df.columns]
        if missing_cog:
            print(f"Error: Missing required columns in cognitive covariates file: {missing_cog}")
            return None, None, None
        
        # Print data types for covariates
        for col in cog_required[1:]:  # Skip participantId
            print(f"{col} data type: {cog_df[col].dtype}")
            print(f"{col} range: {cog_df[col].min()} to {cog_df[col].max()}")
        
        return vwm_df, vviq_df, cog_df
        
    except Exception as e:
        print(f"Error loading data files: {e}")
        return None, None, None

def merge_and_filter_data(vwm_df, vviq_df, cog_df):
    """
    Merge datasets and apply inclusion criteria.
    
    Parameters:
    vwm_df (pd.DataFrame): VWM parameters data
    vviq_df (pd.DataFrame): VVIQ2 scores data  
    cog_df (pd.DataFrame): Cognitive covariates data
    
    Returns:
    pd.DataFrame: Merged and filtered dataset
    """
    print("\nMerging datasets and applying inclusion criteria...")
    
    print(f"Initial sample sizes:")
    print(f"VWM parameters: {len(vwm_df)} participants")
    print(f"VVIQ2 scores: {len(vviq_df)} participants")
    print(f"Cognitive covariates: {len(cog_df)} participants")
    
    # Filter VWM data for reliable parameter estimation
    print(f"\nFiltering VWM data for parameter_estimation_reliable = True...")
    reliable_vwm = vwm_df[vwm_df['parameter_estimation_reliable'] == True].copy()
    print(f"Participants with reliable VWM parameter estimation: {len(reliable_vwm)}")
    print(f"Excluded due to unreliable parameter estimation: {len(vwm_df) - len(reliable_vwm)}")
    
    # Filter VVIQ2 data for non-excluded participants
    print(f"\nFiltering VVIQ2 data for excluded_participant = False...")
    valid_vviq = vviq_df[vviq_df['excluded_participant'] == False].copy()
    print(f"Non-excluded VVIQ2 participants: {len(valid_vviq)}")
    print(f"Excluded VVIQ2 participants: {len(vviq_df) - len(valid_vviq)}")
    
    # Merge datasets
    print(f"\nMerging datasets...")
    # First merge VWM and VVIQ2
    merged_df = pd.merge(reliable_vwm, valid_vviq, on='participantId', how='inner')
    print(f"Participants after VWM-VVIQ2 merge: {len(merged_df)}")
    
    # Then merge with cognitive covariates
    final_df = pd.merge(merged_df, cog_df, on='participantId', how='inner')
    print(f"Final participants after all merges: {len(final_df)}")
    
    print(f"Final merged dataset columns: {list(final_df.columns)}")
    print(f"Final merged dataset first 2 rows:\n{final_df.head(2)}")
    
    return final_df

def prepare_variables(df):
    """
    Prepare variables for regression modeling by centering and scaling.
    
    Parameters:
    df (pd.DataFrame): Merged dataset
    
    Returns:
    pd.DataFrame: Dataset with prepared variables
    """
    print("\nPreparing variables for regression modeling...")
    
    # Create a copy to avoid modifying original
    analysis_df = df.copy()
    
    # Center and scale vonMises_kappa
    print(f"vonMises_kappa before centering - Mean: {analysis_df['vonMises_kappa'].mean():.4f}, Std: {analysis_df['vonMises_kappa'].std():.4f}")
    analysis_df['vonMises_kappa_centered'] = (analysis_df['vonMises_kappa'] - analysis_df['vonMises_kappa'].mean()) / analysis_df['vonMises_kappa'].std()
    print(f"vonMises_kappa after centering - Mean: {analysis_df['vonMises_kappa_centered'].mean():.4f}, Std: {analysis_df['vonMises_kappa_centered'].std():.4f}")
    
    # Center domain-general covariates
    covariates = ['mean_VWM_absolute_error', 'VWM_rt_coefficient_variation', 'focus_loss_severity_index']
    
    for covar in covariates:
        print(f"{covar} before centering - Mean: {analysis_df[covar].mean():.4f}, Std: {analysis_df[covar].std():.4f}")
        analysis_df[f'{covar}_centered'] = analysis_df[covar] - analysis_df[covar].mean()
        print(f"{covar} after centering - Mean: {analysis_df[f'{covar}_centered'].mean():.4f}, Std: {analysis_df[f'{covar}_centered'].std():.4f}")
    
    # Check distributions of VVIQ2 scores
    print(f"\nVVIQ2 score distributions:")
    print(f"Total VVIQ2 score - Mean: {analysis_df['total_VVIQ2_score'].mean():.2f}, Std: {analysis_df['total_VVIQ2_score'].std():.2f}, Range: {analysis_df['total_VVIQ2_score'].min()}-{analysis_df['total_VVIQ2_score'].max()}")
    
    subscales = ['familiar_person_subscale', 'sunrise_subscale', 'shop_front_subscale', 
                'countryside_subscale', 'driving_subscale', 'beach_subscale', 
                'railway_station_subscale', 'garden_subscale']
    
    for subscale in subscales:
        mean_val = analysis_df[subscale].mean()
        std_val = analysis_df[subscale].std()
        min_val = analysis_df[subscale].min()
        max_val = analysis_df[subscale].max()
        print(f"{subscale} - Mean: {mean_val:.2f}, Std: {std_val:.2f}, Range: {min_val}-{max_val}")
    
    return analysis_df

def fit_primary_regression(df):
    print("\nFitting primary multiple regression model for total VVIQ2 score...")
    
    # Prepare data
    model_data = df[['total_VVIQ2_score', 'vonMises_kappa_centered', 
                     'mean_VWM_absolute_error_centered', 'VWM_rt_coefficient_variation_centered',
                     'focus_loss_severity_index_centered']].copy()
    
    model_data = model_data.dropna()
    print(f"Model data shape: {model_data.shape}")
    
    # Set up regression
    y = model_data['total_VVIQ2_score']
    X = model_data[['vonMises_kappa_centered', 'mean_VWM_absolute_error_centered', 
                    'VWM_rt_coefficient_variation_centered', 'focus_loss_severity_index_centered']]
    X = sm.add_constant(X)
    
    # Fit model
    model_fit = sm.OLS(y, X).fit()
    
    # Extract results
    coef_df = pd.DataFrame({
        'Estimate': model_fit.params,
        'Std. Error': model_fit.bse,
        't value': model_fit.tvalues,
        'Pr(>|t|)': model_fit.pvalues
    })
    
    confint_df = model_fit.conf_int()
    confint_df.columns = ['2.5 %', '97.5 %']
    
    print(f"Regression coefficients:\n{coef_df}")
    print(f"Adjusted R-squared: {model_fit.rsquared_adj:.4f}")
    print(f"F-statistic: {model_fit.fvalue:.4f}, p-value: {model_fit.f_pvalue:.6f}")

    results = {
        'coefficients': coef_df,
        'confidence_intervals': confint_df,
        'r_squared_adj': model_fit.rsquared_adj,
        'f_statistic': model_fit.fvalue,
        'f_p_value': model_fit.f_pvalue
    }

    return results, model_fit

def fit_subscale_regressions(df):
    print("\nFitting exploratory regression models for VVIQ2 subscales...")
    
    subscales = ['familiar_person_subscale', 'sunrise_subscale', 'shop_front_subscale', 
                'countryside_subscale', 'driving_subscale', 'beach_subscale', 
                'railway_station_subscale', 'garden_subscale']
    
    predictor_cols = ['vonMises_kappa_centered', 'mean_VWM_absolute_error_centered', 
                     'VWM_rt_coefficient_variation_centered', 'focus_loss_severity_index_centered']
    
    subscale_results = {}
    kappa_p_values = []
    subscale_models = {}
    
    for subscale in subscales:
        print(f"\nFitting model for {subscale}...")
        
        model_data = df[[subscale] + predictor_cols].copy()
        model_data = model_data.dropna()
        
        y = model_data[subscale]
        X = model_data[predictor_cols]
        X = sm.add_constant(X)
        
        model_fit = sm.OLS(y, X).fit()
        subscale_models[subscale] = model_fit
        
        # Extract vonMises_kappa effect
        kappa_estimate = model_fit.params['vonMises_kappa_centered']
        kappa_std_error = model_fit.bse['vonMises_kappa_centered']
        kappa_t_value = model_fit.tvalues['vonMises_kappa_centered']
        kappa_p_value = model_fit.pvalues['vonMises_kappa_centered']
        
        kappa_p_values.append(kappa_p_value)
        
        print(f"{subscale} - vonMises_kappa effect: estimate={kappa_estimate:.4f}, p={kappa_p_value:.6f}")
        print(f"{subscale} - Model R²adj: {model_fit.rsquared_adj:.4f}, F={model_fit.fvalue:.4f}, p={model_fit.f_pvalue:.6f}")

        subscale_results[subscale] = {
            'kappa_estimate': kappa_estimate,
            'kappa_std_error': kappa_std_error,
            'kappa_t_value': kappa_t_value,
            'kappa_p_value': kappa_p_value,
            'r_squared_adj': model_fit.rsquared_adj,
            'f_statistic': model_fit.fvalue,
            'f_p_value': model_fit.f_pvalue
        }

    return subscale_results, kappa_p_values, subscale_models

def apply_fdr_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Parameters:
    p_values (list): List of p-values to correct
    alpha (float): FDR level (default 0.05)
    
    Returns:
    tuple: (corrected_p_values, significant_flags, threshold)
    """
    print(f"\nApplying Benjamini-Hochberg FDR correction with q = {alpha}...")
    
    # Convert to numpy array and sort
    p_array = np.array(p_values)
    n = len(p_array)
    
    # Get sorted indices
    sorted_indices = np.argsort(p_array)
    sorted_p = p_array[sorted_indices]
    
    print(f"Original p-values: {p_values}")
    print(f"Sorted p-values: {sorted_p}")
    
    # Calculate FDR-corrected p-values using Benjamini-Hochberg
    corrected_p = np.zeros(n)
    
    # Start from the largest p-value and work backwards
    for i in range(n-1, -1, -1):
        if i == n-1:
            corrected_p[sorted_indices[i]] = sorted_p[i]
        else:
            corrected_p[sorted_indices[i]] = min(corrected_p[sorted_indices[i+1]], 
                                               sorted_p[i] * n / (i + 1))
    
    # Determine significance after FDR correction
    significant = corrected_p <= alpha
    
    print(f"FDR-corrected p-values: {corrected_p}")
    print(f"Significant after FDR correction: {significant}")
    print(f"Number of significant effects: {np.sum(significant)}")
    
    return corrected_p, significant, alpha

def save_primary_results(primary_results, timestamp):
    print("\nSaving primary regression results...")
    
    coef_df = primary_results['coefficients']
    confint_df = primary_results['confidence_intervals']

    results_list = []

    for term in coef_df.index:
        result_row = {
            'term': term,
            'estimate': coef_df.loc[term, 'Estimate'],
            'std_error': coef_df.loc[term, 'Std. Error'],
            't_value': coef_df.loc[term, 't value'],
            'p_value': coef_df.loc[term, 'Pr(>|t|)'],
            'conf_low_95': confint_df.loc[term, '2.5 %'],
            'conf_high_95': confint_df.loc[term, '97.5 %'],
            'r_squared_adjusted': primary_results['r_squared_adj'],
            'f_statistic': primary_results['f_statistic'],
            'f_p_value': primary_results['f_p_value']
        }
        results_list.append(result_row)

    results_df = pd.DataFrame(results_list)

    output_file = f"outputs/VVIQ2_total_regression_results_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"Primary regression results saved to: {output_file}")

def save_subscale_results(subscale_results, kappa_p_values, corrected_p_values, significant_flags, timestamp):
    """
    Save subscale regression results to CSV.
    
    Parameters:
    subscale_results (dict): Results from subscale regressions
    kappa_p_values (list): Original p-values for kappa effects
    corrected_p_values (array): FDR-corrected p-values
    significant_flags (array): Significance flags after FDR correction
    timestamp (str): Timestamp for filename
    """
    print("\nSaving subscale regression results...")
    
    subscales = ['familiar_person_subscale', 'sunrise_subscale', 'shop_front_subscale', 
                'countryside_subscale', 'driving_subscale', 'beach_subscale', 
                'railway_station_subscale', 'garden_subscale']
    
    results_list = []
    
    for i, subscale in enumerate(subscales):
        result_row = {
            'subscale_name': subscale,
            'kappa_estimate': subscale_results[subscale]['kappa_estimate'],
            'kappa_std_error': subscale_results[subscale]['kappa_std_error'],
            'kappa_t_value': subscale_results[subscale]['kappa_t_value'],
            'kappa_p_value': subscale_results[subscale]['kappa_p_value'],
            'kappa_p_value_fdr_corrected': corrected_p_values[i],
            'kappa_significant_fdr': significant_flags[i],
            'r_squared_adjusted': subscale_results[subscale]['r_squared_adj'],
            'model_f_statistic': subscale_results[subscale]['f_statistic'],
            'model_f_p_value': subscale_results[subscale]['f_p_value']
        }
        results_list.append(result_row)

    results_df = pd.DataFrame(results_list)
    
    print(f"Subscale results dataframe columns: {list(results_df.columns)}")
    print(f"Subscale results dataframe first 2 rows:\n{results_df.head(2)}")
    
    # Save to CSV
    output_file = f"outputs/VVIQ2_subscale_regression_results_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"Subscale regression results saved to: {output_file}")

def save_fdr_summary(kappa_p_values, corrected_p_values, significant_flags, fdr_threshold, timestamp):
    """
    Save FDR correction summary to CSV.
    
    Parameters:
    kappa_p_values (list): Original p-values
    corrected_p_values (array): FDR-corrected p-values  
    significant_flags (array): Significance flags
    fdr_threshold (float): FDR threshold used
    timestamp (str): Timestamp for filename
    """
    print("\nSaving FDR correction summary...")
    
    subscales = ['familiar_person_subscale', 'sunrise_subscale', 'shop_front_subscale', 
                'countryside_subscale', 'driving_subscale', 'beach_subscale', 
                'railway_station_subscale', 'garden_subscale']
    
    results_list = []
    
    for i, subscale in enumerate(subscales):
        result_row = {
            'subscale_name': subscale,
            'original_p_value': kappa_p_values[i],
            'fdr_corrected_p_value': corrected_p_values[i],
            'significant_after_correction': significant_flags[i],
            'fdr_q_threshold': fdr_threshold
        }
        results_list.append(result_row)
    
    results_df = pd.DataFrame(results_list)
    
    print(f"FDR summary dataframe columns: {list(results_df.columns)}")
    print(f"FDR summary dataframe first 2 rows:\n{results_df.head(2)}")
    
    # Save to CSV
    output_file = f"outputs/VVIQ2_FDR_correction_summary_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    print(f"FDR correction summary saved to: {output_file}")

def create_empty_subscale_files(timestamp):
    """
    Create empty output files for subscale and FDR results when analysis is skipped.
    
    Parameters:
    timestamp (str): Timestamp for filename
    """
    print("Creating empty output files for skipped subscale analysis...")
    
    # Define column headers for subscale results
    subscale_cols = ['subscale_name', 'kappa_estimate', 'kappa_std_error', 'kappa_t_value',
                     'kappa_p_value', 'kappa_p_value_fdr_corrected', 'kappa_significant_fdr',
                     'r_squared_adjusted', 'model_f_statistic', 'model_f_p_value']

    # Define column headers for FDR results
    fdr_cols = ['subscale_name', 'original_p_value', 'fdr_corrected_p_value',
                'significant_after_correction', 'fdr_q_threshold']

    # Create empty dataframes and save to CSV
    subscale_file = f"outputs/VVIQ2_subscale_regression_results_{timestamp}.csv"
    fdr_file = f"outputs/VVIQ2_FDR_correction_summary_{timestamp}.csv"

    pd.DataFrame(columns=subscale_cols).to_csv(subscale_file, index=False)
    pd.DataFrame(columns=fdr_cols).to_csv(fdr_file, index=False)

    print(f"Empty subscale results file created: {subscale_file}")
    print(f"Empty FDR summary file created: {fdr_file}")
    
    # Create empty subscale models pickle file
    subscale_model_file = f"outputs/VVIQ2_subscale_models_{timestamp}.pkl"
    with open(subscale_model_file, "wb") as f:
        pickle.dump({}, f)
    print(f"Empty subscale models file created: {subscale_model_file}")

def main():
    """
    Main function to execute the VVIQ2 regression analysis.
    
    Returns:
    int: 0 for success, 1 for failure
    """
    try:
        print("Starting VVIQ2 regression analysis...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        print(f"Analysis timestamp: {timestamp}")
        
        # Load and validate data
        vwm_df, vviq_df, cog_df = load_and_validate_data()
        if vwm_df is None:
            print("Error: Failed to load required data files")
            return 1
        
        # Merge and filter data
        analysis_df = merge_and_filter_data(vwm_df, vviq_df, cog_df)
        if len(analysis_df) == 0:
            print("Error: No participants remaining after filtering and merging")
            return 1
        
        # Prepare variables for modeling
        analysis_df = prepare_variables(analysis_df)
        
        # Fit primary regression model
        primary_results, primary_model = fit_primary_regression(analysis_df)
        
        # Save primary results
        save_primary_results(primary_results, timestamp)
        
        # Save primary model object as .pkl
        primary_model_file = f"outputs/VVIQ2_total_model_{timestamp}.pkl"
        with open(primary_model_file, "wb") as f:
            pickle.dump(primary_model, f)
        print(f"Primary regression model object saved to: {primary_model_file}")
        
        # Check significance of kappa in primary model for conditional analysis
        kappa_p_value = primary_results['coefficients'].loc['vonMises_kappa_centered', 'Pr(>|t|)']
        print(f"\nPrimary model vonMises_kappa p-value: {kappa_p_value:.6f}")
        
        if kappa_p_value < 0.05:
            print(f"Kappa effect is significant (p={kappa_p_value:.4f}), proceeding with subscale analysis...")
            
            # Fit subscale regression models
            subscale_results, kappa_p_values, subscale_models = fit_subscale_regressions(analysis_df)
            
            # Apply FDR correction
            corrected_p_values, significant_flags, fdr_threshold = apply_fdr_correction(kappa_p_values)
            
            # Save subscale and FDR results
            save_subscale_results(subscale_results, kappa_p_values, corrected_p_values, significant_flags, timestamp)
            save_fdr_summary(kappa_p_values, corrected_p_values, significant_flags, fdr_threshold, timestamp)
            
            # Save subscale model objects as .pkl
            subscale_model_file = f"outputs/VVIQ2_subscale_models_{timestamp}.pkl"
            with open(subscale_model_file, "wb") as f:
                pickle.dump(subscale_models, f)
            print(f"Subscale regression model objects saved to: {subscale_model_file}")
        else:
            print(f"Kappa effect is not significant (p={kappa_p_value:.4f}), skipping subscale analysis...")
            # Create empty files to maintain consistent output structure
            create_empty_subscale_files(timestamp)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
