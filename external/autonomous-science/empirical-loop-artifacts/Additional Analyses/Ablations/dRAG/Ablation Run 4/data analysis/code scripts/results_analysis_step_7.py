import os
import pandas as pd
import numpy as np
import glob
from datetime import datetime
from scipy import stats
from scipy.stats import pearsonr
import statsmodels.api as sm
from statsmodels.robust.robust_linear_model import RLM
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

def load_and_validate_data(vviq2_file, vwm_file):
    """
    Load and validate input data files.
    
    Parameters:
    vviq2_file (str): Path to VVIQ2 cleaned data file
    vwm_file (str): Path to VWM parameters file
    
    Returns:
    tuple: (vviq2_df, vwm_df) - loaded and validated dataframes
    """
    print("Loading VVIQ2 data...")
    vviq2_df = pd.read_csv(vviq2_file)
    print(f"VVIQ2 data shape: {vviq2_df.shape}")
    print("VVIQ2 columns:", vviq2_df.columns.tolist())
    print("First 3 rows of VVIQ2 data:")
    print(vviq2_df.head(3))
    
    print("\nLoading VWM data...")
    vwm_df = pd.read_csv(vwm_file)
    print(f"VWM data shape: {vwm_df.shape}")
    print("VWM columns:", vwm_df.columns.tolist())
    print("First 3 rows of VWM data:")
    print(vwm_df.head(3))
    
    # Validate required columns
    vviq2_required = ['PROLIFIC_PID', 'total_score', 'face_person_score', 'sunrise_score', 
                      'shop_score', 'countryside_score', 'driving_score', 'beach_score', 
                      'railway_score', 'garden_score', 'excluded']
    vwm_required = ['participantId', 'kappa_concentration', 'excluded']
    
    missing_vviq2 = [col for col in vviq2_required if col not in vviq2_df.columns]
    missing_vwm = [col for col in vwm_required if col not in vwm_df.columns]
    
    if missing_vviq2:
        raise ValueError(f"Missing required VVIQ2 columns: {missing_vviq2}")
    if missing_vwm:
        raise ValueError(f"Missing required VWM columns: {missing_vwm}")
    
    print(f"All required columns present in both datasets")
    
    # Print unique values for exclusion columns
    print(f"VVIQ2 excluded unique values: {vviq2_df['excluded'].unique()}")
    print(f"VWM excluded unique values: {vwm_df['excluded'].unique()}")
    
    return vviq2_df, vwm_df

def merge_and_clean_data(vviq2_df, vwm_df):
    """
    Merge datasets and apply exclusion criteria.
    
    Parameters:
    vviq2_df (pd.DataFrame): VVIQ2 data
    vwm_df (pd.DataFrame): VWM data
    
    Returns:
    pd.DataFrame: Merged and cleaned dataset
    """
    print("\nApplying exclusion criteria...")
    
    # Filter out excluded participants
    vviq2_included = vviq2_df[vviq2_df['excluded'] == False].copy()
    vwm_included = vwm_df[vwm_df['excluded'] == False].copy()
    
    print(f"VVIQ2: {len(vviq2_df)} total, {len(vviq2_included)} included")
    print(f"VWM: {len(vwm_df)} total, {len(vwm_included)} included")
    
    # Merge datasets
    merged_df = pd.merge(vviq2_included, vwm_included, 
                        left_on='PROLIFIC_PID', right_on='participantId', 
                        how='inner')
    
    print(f"Merged dataset shape: {merged_df.shape}")
    print("Merged dataset columns:", merged_df.columns.tolist())
    print("First 2 rows of merged data:")
    print(merged_df.head(2))
    print("Note: After merge, exclusion columns are renamed to 'excluded_x' (VVIQ2) and 'excluded_y' (VWM)")
    
    # Check for complete cases
    required_vars = ['total_score', 'face_person_score', 'sunrise_score', 'shop_score',
                     'countryside_score', 'driving_score', 'beach_score', 'railway_score',
                     'garden_score', 'kappa_concentration']
    
    complete_cases = merged_df[required_vars].dropna()
    print(f"Complete cases: {len(complete_cases)} out of {len(merged_df)}")
    
    if len(complete_cases) < len(merged_df):
        print(f"Removing {len(merged_df) - len(complete_cases)} cases with missing data")
        merged_df = merged_df.loc[complete_cases.index]
    
    return merged_df




def run_robust_regression(data, outcome_var):
    """
    Run robust regression for a single outcome variable.
    
    Parameters:
    data (pd.DataFrame): Merged dataset
    outcome_var (str): Name of outcome variable
    
    Returns:
    dict: Robust regression results
    """
    print(f"\nRobust regression for {outcome_var}")
    
    # Prepare data
    X = data['kappa_concentration'].values
    y = data[outcome_var].values
    
    print(f"Sample size: {len(X)}")
    print(f"{outcome_var} range: {np.min(y)} - {np.max(y)}")
    
    # Add intercept
    X_with_intercept = sm.add_constant(X)
    
    # Fit robust model (M-estimation)
    robust_model = RLM(y, X_with_intercept, M=sm.robust.norms.HuberT()).fit()
    
    print(f"Robust regression summary for {outcome_var}:")
    print(robust_model.summary())
    
    # Extract results
    coef = robust_model.params[1]  # Slope coefficient
    se = robust_model.bse[1]
    t_val = robust_model.tvalues[1]
    p_val = robust_model.pvalues[1]
    conf_int = robust_model.conf_int()
    ci_lower, ci_upper = conf_int[1]
    
    results = {
        'outcome_variable': outcome_var,
        'predictor': 'kappa_concentration',
        'coefficient': coef,
        'standard_error': se,
        't_value': t_val,
        'p_value': p_val,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'model_type': 'robust_regression',
        'n_participants': len(X)
    }
    
    return results

def run_secondary_analyses(data):
    """
    Run robust regression analyses for all VVIQ2 subscale scores.
    
    Parameters:
    data (pd.DataFrame): Merged dataset
    
    Returns:
    list: List of regression results for each subscale
    """
    print("\n=== SECONDARY ANALYSES (ROBUST REGRESSION) ===")
    
    subscales = ['face_person_score', 'sunrise_score', 'shop_score', 'countryside_score',
                 'driving_score', 'beach_score', 'railway_score', 'garden_score']
    
    results = []
    
    for subscale in subscales:
        result = run_robust_regression(data, subscale)
        results.append(result)
    
    return results

def calculate_correlations(data):
    """
    Calculate correlations between kappa_concentration and VVIQ2 measures.
    
    Parameters:
    data (pd.DataFrame): Merged dataset
    
    Returns:
    list: List of correlation results
    """
    print("\n=== CORRELATION ANALYSES ===")
    
    vviq2_measures = ['total_score', 'face_person_score', 'sunrise_score', 'shop_score',
                      'countryside_score', 'driving_score', 'beach_score', 'railway_score',
                      'garden_score']
    
    correlation_results = []
    
    for measure in vviq2_measures:
        # Calculate Pearson correlation
        r, p = pearsonr(data['kappa_concentration'], data[measure])
        
        # Calculate confidence interval for correlation
        n = len(data)
        z = np.arctanh(r)
        se = 1 / np.sqrt(n - 3)
        z_ci_lower = z - 1.96 * se
        z_ci_upper = z + 1.96 * se
        ci_lower = np.tanh(z_ci_lower)
        ci_upper = np.tanh(z_ci_upper)
        
        print(f"{measure}: r = {r:.4f}, p = {p:.4f}, 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]")
        
        correlation_results.append({
            'vviq2_measure': measure,
            'correlation_with_kappa': r,
            'correlation_p_value': p,
            'correlation_ci_lower': ci_lower,
            'correlation_ci_upper': ci_upper,
            'n_participants': n
        })
    
    return correlation_results

def save_results(regression_results, correlation_results, timestamp):
    """
    Save analysis results to CSV files.
    
    Parameters:
    regression_results (list): List of regression results
    correlation_results (list): List of correlation results
    timestamp (str): Timestamp string for filenames
    """
    print("\n=== SAVING RESULTS ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Save regression results
    regression_df = pd.DataFrame(regression_results)
    regression_file = f'outputs/VVIQ2_VWM_regression_{timestamp}.csv'
    
    # Select only required columns for regression output
    regression_cols = ['outcome_variable', 'predictor', 'coefficient', 'standard_error',
                       't_value', 'p_value', 'ci_lower', 'ci_upper', 'model_type', 'n_participants']
    
    regression_df[regression_cols].to_csv(regression_file, index=False)
    print(f"Regression results saved to: {regression_file}")
    print("Regression results preview:")
    print(regression_df[regression_cols].head(2))
    
    # Save correlation results
    correlation_df = pd.DataFrame(correlation_results)
    correlation_file = f'outputs/VVIQ2_VWM_correlations_{timestamp}.csv'
    
    correlation_df.to_csv(correlation_file, index=False)
    print(f"Correlation results saved to: {correlation_file}")
    print("Correlation results preview:")
    print(correlation_df.head(2))

def main():
    """
    Main execution function for VVIQ2-VWM regression analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2-VWM regression analysis...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Find input files
        vviq2_pattern = "outputs/VVIQ2_cleaned_*.csv"
        vwm_pattern = "outputs/VWM_parameters_*.csv"
        
        vviq2_file = find_latest_file(vviq2_pattern)
        vwm_file = find_latest_file(vwm_pattern)
        
        # Load and validate data
        vviq2_df, vwm_df = load_and_validate_data(vviq2_file, vwm_file)
        
        # Merge and clean data
        merged_data = merge_and_clean_data(vviq2_df, vwm_df)
        
        if len(merged_data) < 10:
            raise ValueError(f"Insufficient data for analysis: only {len(merged_data)} participants")
        
        # Run primary robust regression analysis
        primary_results = run_robust_regression(merged_data, 'total_score')
        
        # Run secondary analyses (robust regression)
        secondary_results = run_secondary_analyses(merged_data)
        
        # Combine all regression results
        all_regression_results = [primary_results] + secondary_results
        
        # Calculate correlations
        correlation_results = calculate_correlations(merged_data)
        
        # Save results
        save_results(all_regression_results, correlation_results, timestamp)
        
        print("\nAnalysis completed successfully!")
        print(f"Total participants analyzed: {len(merged_data)}")
        print(f"Primary analysis p-value: {primary_results['p_value']:.4f}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
