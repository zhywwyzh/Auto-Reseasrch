#!/usr/bin/env python3
"""
VVIQ2 Robust Regression Analysis Script

This script performs robust multiple regression analysis on VVIQ2 data using Huber M-estimation
to examine relationships between visual working memory concentration parameters and visual imagery scores.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

# Import R interface
import rpy2.robjects as ro
from rpy2.robjects import pandas2ri, numpy2ri, conversion
from rpy2.robjects.packages import importr

def setup_r_environment():
    """
    Set up R environment and import required packages.
    
    Returns:
        tuple: R base, stats, and MASS packages
    """
    print("Setting up R environment...")

    # Import R packages
    base = importr('base')
    stats = importr('stats')
    # Ensure MASS is installed
    utils = importr('utils')
    try:
        mass = importr('MASS')
    except Exception:
        print("MASS package not found. Attempting to install MASS...")
        utils.install_packages('MASS')
        mass = importr('MASS')

    print("R environment setup complete")
    return base, stats, mass

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Args:
        pattern (str): File pattern to match
        
    Returns:
        str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def load_input_data():
    """
    Load and validate input data files.
    
    Returns:
        tuple: (vwm_data, vviq_data) DataFrames
    """
    print("Loading input data...")
    
    # Find VWM parameters file
    vwm_pattern = "outputs/final_reliable_VWM_parameters_*.csv"
    vwm_file = find_latest_file(vwm_pattern)
    
    if vwm_file is None:
        print(f"Error: No VWM parameters file found matching pattern: {vwm_pattern}")
        return None, None
    
    print(f"Found VWM parameters file: {vwm_file}")
    
    # Find VVIQ2 scores file
    vviq_pattern = "outputs/VVIQ2_cleaned_scores_*.csv"
    vviq_file = find_latest_file(vviq_pattern)
    
    if vviq_file is None:
        print(f"Error: No VVIQ2 scores file found matching pattern: {vviq_pattern}")
        return None, None
    
    print(f"Found VVIQ2 scores file: {vviq_file}")
    
    # Load VWM data
    try:
        vwm_data = pd.read_csv(vwm_file)
        print(f"Loaded VWM data with shape: {vwm_data.shape}")
        print("VWM data columns:", list(vwm_data.columns))
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
    except Exception as e:
        print(f"Error loading VWM data: {e}")
        return None, None
    
    # Load VVIQ2 data
    try:
        vviq_data = pd.read_csv(vviq_file)
        print(f"Loaded VVIQ2 data with shape: {vviq_data.shape}")
        print("VVIQ2 data columns:", list(vviq_data.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq_data.head(3))
    except Exception as e:
        print(f"Error loading VVIQ2 data: {e}")
        return None, None
    
    return vwm_data, vviq_data

def validate_required_columns(vwm_data, vviq_data):
    """
    Validate that required columns exist in the input data.
    
    Args:
        vwm_data (pd.DataFrame): VWM parameters data
        vviq_data (pd.DataFrame): VVIQ2 scores data
        
    Returns:
        bool: True if all required columns exist, False otherwise
    """
    print("Validating required columns...")
    
    # Required VWM columns
    vwm_required = ['participantId', 'kappa_concentration', 'included_in_analysis']
    missing_vwm = [col for col in vwm_required if col not in vwm_data.columns]
    
    if missing_vwm:
        print(f"Missing required VWM columns: {missing_vwm}")
        return False
    
    # Required VVIQ2 columns
    vviq_required = ['PROLIFIC_PID', 'total_score', 'familiar_person_score', 
                     'sunrise_score', 'shop_front_score', 'countryside_score',
                     'driving_score', 'beach_score', 'railway_station_score',
                     'garden_scene_score', 'excluded']
    missing_vviq = [col for col in vviq_required if col not in vviq_data.columns]
    
    if missing_vviq:
        print(f"Missing required VVIQ2 columns: {missing_vviq}")
        return False
    
    print("All required columns found")
    
    # Print unique values for key experimental design parameters
    print("\nUnique values for key columns:")
    print(f"VWM included_in_analysis: {sorted(vwm_data['included_in_analysis'].unique())}")
    print(f"VVIQ2 excluded: {sorted(vviq_data['excluded'].unique())}")
    
    return True

def merge_and_filter_data(vwm_data, vviq_data):
    """
    Merge datasets and apply inclusion criteria.
    
    Args:
        vwm_data (pd.DataFrame): VWM parameters data
        vviq_data (pd.DataFrame): VVIQ2 scores data
        
    Returns:
        pd.DataFrame: Merged and filtered dataset
    """
    print("Merging and filtering data...")
    
    print(f"Initial VWM data: {len(vwm_data)} participants")
    print(f"Initial VVIQ2 data: {len(vviq_data)} participants")
    
    # Apply inclusion criteria to VWM data
    vwm_included = vwm_data[vwm_data['included_in_analysis'] == True].copy()
    print(f"VWM participants with included_in_analysis=True: {len(vwm_included)}")
    
    # Apply inclusion criteria to VVIQ2 data
    vviq_included = vviq_data[vviq_data['excluded'] == False].copy()
    print(f"VVIQ2 participants with excluded=False: {len(vviq_included)}")
    
    # Merge datasets
    merged_data = pd.merge(vwm_included, vviq_included, 
                          left_on='participantId', right_on='PROLIFIC_PID', 
                          how='inner')
    
    print(f"Merged dataset: {len(merged_data)} participants")
    print("Merged data columns:", list(merged_data.columns))
    print("First 2 rows of merged data:")
    print(merged_data.head(2))
    
    if len(merged_data) == 0:
        print("Error: No participants remain after merging and filtering")
        return None
    
    # Calculate sample mean of kappa_concentration
    kappa_mean = merged_data['kappa_concentration'].mean()
    print(f"Sample mean of kappa_concentration: {kappa_mean}")
    
    # Create kappa_centered
    merged_data['kappa_centered'] = merged_data['kappa_concentration'] - kappa_mean
    print(f"Created kappa_centered variable (mean = {merged_data['kappa_centered'].mean()})")
    
    return merged_data

def fit_robust_regression_model(y_data, x_data, model_name, base, stats, mass):
    """
    Fit a robust regression model using Huber M-estimation.
    """
    print(f"Fitting robust regression model: {model_name}")

    try:
        # Manual conversion without localconverter context
        r_y = ro.FloatVector(y_data)
        r_x = ro.FloatVector(x_data)
        r_data = ro.DataFrame({'y': r_y, 'x': r_x})

        # Fit model and extract summary as R object proxies
        rlm_model = mass.rlm(ro.Formula('y ~ x'), data=r_data, method='M')
        model_summary = base.summary(rlm_model)

        # Extract coefficients matrix using R-style indexing
        coef_matrix = model_summary.rx2('coefficients')
        slope = coef_matrix.rx(2, 1)[0]  # Row 2 (slope), Column 1 (estimate)
        std_error = coef_matrix.rx(2, 2)[0]  # Row 2, Column 2 (std error)
        t_value = coef_matrix.rx(2, 3)[0]  # Row 2, Column 3 (t value)

        # Get fitted values and residuals using correct R function access
        fitted_values_r = ro.r['fitted'](rlm_model)
        residuals_r = ro.r['residuals'](rlm_model)

        # Convert R objects to numpy arrays outside the context
        fitted_np = np.array(fitted_values_r)
        residuals_np = np.array(residuals_r)
        y_np = np.array(y_data)

        # Corrected p-value calculation
        n = len(y_data)
        df = n - 2
        try:
            p_r = stats.pt(abs(t_value), df=df)
            if hasattr(p_r, '__getitem__'):
                p_scalar = float(p_r[0])
            else:
                p_scalar = float(p_r)
            p_value = 2 * (1 - p_scalar)
        except Exception as e:
            print(f"Error calculating p-value: {e}")
            p_value = np.nan

        # Calculate standardized beta coefficient
        try:
            sd_x = np.std(x_data, ddof=1)
            sd_y = np.std(y_data, ddof=1)
            standardized_beta = slope * (sd_x / sd_y)
        except Exception as e:
            print(f"Error calculating standardized beta: {e}")
            standardized_beta = np.nan

        # Calculate robust R-squared
        try:
            ss_res = np.sum(residuals_np**2)
            ss_tot = np.sum((y_np - np.mean(y_np))**2)
            r_squared = 1 - (ss_res / ss_tot)
        except Exception as e:
            print(f"Error calculating R-squared: {e}")
            r_squared = np.nan

        # Calculate residual standard error
        try:
            residual_std_error = np.sqrt(ss_res / (n - 2))
        except Exception as e:
            print(f"Error calculating residual standard error: {e}")
            residual_std_error = np.nan

        # Bootstrap confidence intervals for standardized beta
        print(f"Calculating bootstrap confidence intervals for {model_name}...")
        n_bootstrap = 1000
        bootstrap_betas = []

        for i in range(n_bootstrap):
            try:
                indices = np.random.choice(len(x_data), size=len(x_data), replace=True)
                x_boot = x_data[indices]
                y_boot = y_data[indices]
            except Exception as e:
                continue

            try:
                # Manual conversion without localconverter context
                r_y_boot = ro.FloatVector(y_boot)
                r_x_boot = ro.FloatVector(x_boot)
                r_data_boot = ro.DataFrame({'y': r_y_boot, 'x': r_x_boot})
                rlm_boot = mass.rlm(ro.Formula('y ~ x'), data=r_data_boot, method='M')
                summary_boot = base.summary(rlm_boot)
                coef_matrix_boot = summary_boot.rx2('coefficients')
                slope_boot = coef_matrix_boot.rx(2, 1)[0]

                sd_x_boot = np.std(x_boot, ddof=1)
                sd_y_boot = np.std(y_boot, ddof=1)
                beta_boot = slope_boot * (sd_x_boot / sd_y_boot)
                bootstrap_betas.append(beta_boot)
            except Exception as e:
                if i < 5:
                    print(f"Bootstrap iteration {i} failed: {e}")
                continue

        if len(bootstrap_betas) > 0:
            ci_lower = np.percentile(bootstrap_betas, 2.5)
            ci_upper = np.percentile(bootstrap_betas, 97.5)
        else:
            ci_lower = np.nan
            ci_upper = np.nan

        results = {
            'coefficient': float(slope),
            'std_error': float(std_error),
            'standardized_beta': float(standardized_beta),
            't_value': float(t_value),
            'p_value': float(p_value),
            'confidence_interval_lower': float(ci_lower),
            'confidence_interval_upper': float(ci_upper),
            'r_squared': float(r_squared),
            'residual_std_error': float(residual_std_error)
        }

        print(f"Model {model_name} fitted successfully")
        print(f"Coefficient: {results['coefficient']:.4f}")
        print(f"Standardized beta: {results['standardized_beta']:.4f}")
        print(f"p-value: {results['p_value']:.4f}")

        return results

    except Exception as e:
        print(f"Error fitting model {model_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def run_regression_analysis(merged_data, base, stats, mass):
    """
    Run all robust regression analyses.
    
    Args:
        merged_data (pd.DataFrame): Merged and filtered dataset
        base, stats, mass: R packages
        
    Returns:
        list: List of model results dictionaries
    """
    print("Running robust regression analyses...")
    
    # Define dependent variables
    dependent_vars = {
        'total_score': 'total_score',
        'familiar_person_score': 'familiar_person_score',
        'sunrise_score': 'sunrise_score', 
        'shop_front_score': 'shop_front_score',
        'countryside_score': 'countryside_score',
        'driving_score': 'driving_score',
        'beach_score': 'beach_score',
        'railway_station_score': 'railway_station_score',
        'garden_scene_score': 'garden_scene_score'
    }
    
    results = []
    
    # Get predictor variable
    x_data = merged_data['kappa_centered'].values
    
    # Remove any rows with missing data in predictor
    valid_indices = ~np.isnan(x_data)
    x_clean = x_data[valid_indices]
    
    print(f"Predictor variable (kappa_centered) has {len(x_clean)} valid observations")
    
    # Fit models for each dependent variable
    for var_name, var_col in dependent_vars.items():
        print(f"\nAnalyzing {var_name}...")
        
        # Get dependent variable data
        y_data = merged_data[var_col].values[valid_indices]
        
        # Remove any rows with missing data in dependent variable
        valid_y_indices = ~pd.isna(y_data)
        x_final = x_clean[valid_y_indices]
        y_final = y_data[valid_y_indices]
        
        print(f"Final sample size for {var_name}: {len(y_final)}")
        
        if len(y_final) < 10:
            print(f"Warning: Sample size too small for {var_name}, skipping...")
            continue
        
        # Fit robust regression model
        model_results = fit_robust_regression_model(
            y_final, x_final, var_name, base, stats, mass
        )
        
        if model_results is not None:
            model_results['model_name'] = var_name
            model_results['dependent_variable'] = var_col
            model_results['predictor'] = 'kappa_centered'
            results.append(model_results)
    
    print(f"\nCompleted {len(results)} regression analyses")
    return results

def prepare_analysis_dataset(merged_data):
    """
    Prepare the analysis dataset for output.
    
    Args:
        merged_data (pd.DataFrame): Merged dataset
        
    Returns:
        pd.DataFrame: Analysis dataset with required columns
    """
    print("Preparing analysis dataset...")
    
    # Select required columns
    analysis_cols = [
        'participantId', 'kappa_concentration', 'kappa_centered',
        'total_score', 'familiar_person_score', 'sunrise_score',
        'shop_front_score', 'countryside_score', 'driving_score',
        'beach_score', 'railway_station_score', 'garden_scene_score'
    ]
    
    analysis_dataset = merged_data[analysis_cols].copy()
    
    print(f"Analysis dataset shape: {analysis_dataset.shape}")
    print("Analysis dataset columns:", list(analysis_dataset.columns))
    print("First 2 rows of analysis dataset:")
    print(analysis_dataset.head(2))
    
    return analysis_dataset

def save_results(results_list, analysis_dataset):
    """
    Save regression results and analysis dataset to CSV files.
    
    Args:
        results_list (list): List of regression results dictionaries
        analysis_dataset (pd.DataFrame): Analysis dataset
    """
    print("Saving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Prepare results dataframe
    if results_list:
        results_df = pd.DataFrame(results_list)
        
        # Reorder columns to match requirements
        results_cols = [
            'model_name', 'dependent_variable', 'predictor', 'coefficient',
            'std_error', 'standardized_beta', 't_value', 'p_value',
            'confidence_interval_lower', 'confidence_interval_upper',
            'r_squared', 'residual_std_error'
        ]
        results_df = results_df[results_cols]
        
        # Save results
        results_filename = f"outputs/VVIQ2_robust_regression_results_{timestamp}.csv"
        results_df.to_csv(results_filename, index=False)
        print(f"Saved regression results to: {results_filename}")
        
        print("Final results summary:")
        print(results_df)
    else:
        print("No regression results to save")
    
    # Save analysis dataset
    dataset_filename = f"outputs/VVIQ2_analysis_dataset_{timestamp}.csv"
    analysis_dataset.to_csv(dataset_filename, index=False)
    print(f"Saved analysis dataset to: {dataset_filename}")
    
    print("Results saved successfully")

def main():
    """
    Main function to execute the VVIQ2 robust regression analysis.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 Robust Regression Analysis")
        print("=" * 50)
        
        # Set up R environment
        base, stats, mass = setup_r_environment()
        
        # Load input data
        vwm_data, vviq_data = load_input_data()
        if vwm_data is None or vviq_data is None:
            print("Error: Failed to load input data")
            return 1
        
        # Validate required columns
        if not validate_required_columns(vwm_data, vviq_data):
            print("Error: Missing required columns")
            return 1
        
        # Merge and filter data
        merged_data = merge_and_filter_data(vwm_data, vviq_data)
        if merged_data is None:
            print("Error: Failed to merge and filter data")
            return 1
        
        # Run regression analyses
        results_list = run_regression_analysis(merged_data, base, stats, mass)
        
        # Prepare analysis dataset
        analysis_dataset = prepare_analysis_dataset(merged_data)
        
        # Save results
        save_results(results_list, analysis_dataset)
        
        print("=" * 50)
        print("VVIQ2 Robust Regression Analysis completed successfully")
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
