#!/usr/bin/env python3
"""
VVIQ2 Analysis Script
Analyzes relationships between von Mises concentration parameters and VVIQ2 imagery scores
with control covariates from VWM and MRT tasks.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import re
from scipy import stats
from statsmodels.stats.multitest import fdrcorrection
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
import warnings

def get_timestamp():
    """Generate timestamp string for output files."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern with <TIMESTAMP> placeholder
    
    Returns:
    str: Path to the most recent matching file
    """
    # Replace <TIMESTAMP> with wildcard pattern
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    print(f"Searching for files matching pattern: {search_pattern}")
    
    matching_files = glob.glob(search_pattern)
    print(f"Found {len(matching_files)} matching files: {matching_files}")
    
    if not matching_files:
        raise FileNotFoundError(f"No files found matching pattern: {search_pattern}")
    
    # Sort by modification time and return the most recent
    latest_file = max(matching_files, key=os.path.getmtime)
    print(f"Using most recent file: {latest_file}")
    return latest_file

def extract_numeric_from_vviq2_response(response_text):
    """
    Extract numeric score from VVIQ2 response text.
    
    Parameters:
    response_text (str): Text response containing numeric rating at end
    
    Returns:
    int: Numeric score (1-5)
    """
    if pd.isna(response_text):
        return np.nan
    
    # Convert to string and extract last character
    response_str = str(response_text).strip()
    if response_str:
        try:
            # Get the last character and convert to int
            numeric_score = int(response_str[-1])
            # Validate range
            if 1 <= numeric_score <= 5:
                return numeric_score
            else:
                print(f"Warning: Score {numeric_score} outside expected range 1-5 for response: {response_text}")
                return np.nan
        except (ValueError, IndexError):
            print(f"Warning: Could not extract numeric score from response: {response_text}")
            return np.nan
    return np.nan

def load_and_process_vviq2_data(filepath):
    """
    Load and process VVIQ2 questionnaire data.
    
    Parameters:
    filepath (str): Path to VVIQ2 CSV file
    
    Returns:
    pd.DataFrame: Processed VVIQ2 data with scores
    """
    print(f"Loading VVIQ2 data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"VVIQ2 data loaded successfully. Shape: {df.shape}")
        
        # Print all columns
        print("VVIQ2 columns:", df.columns.tolist())
        
        # Print first 3 rows
        print("First 3 rows of VVIQ2 data:")
        print(df.head(3))
        
        # Check for required columns
        if 'PROLIFIC_PID' not in df.columns:
            raise ValueError("Required column 'PROLIFIC_PID' not found in VVIQ2 data")
        
        # Identify non-question columns to exclude
        non_question_cols = [
            'Respondent ID', 'Collector ID', 'Start Date', 'End Date', 
            'IP Address', 'Email Address', 'First Name', 'Last Name', 
            'Custom Data 1', 'PROLIFIC_PID'
        ]

        # Dynamically identify VVIQ2 question columns
        question_cols = [col for col in df.columns if col not in non_question_cols]

        # Validate that we have exactly 32 question columns
        if len(question_cols) != 32:
            print(f"Available columns: {df.columns.tolist()}")
            print(f"Non-question columns excluded: {non_question_cols}")
            print(f"Question columns found: {len(question_cols)}")
            raise ValueError(f"Expected exactly 32 VVIQ2 question columns, found {len(question_cols)}")

        print(f"Dynamically identified {len(question_cols)} VVIQ2 question columns")
        
        # Extract numeric scores from responses
        vviq2_scores = []
        for i, col in enumerate(question_cols):
            print(f"Processing question {i+1}: {col}")
            scores = df[col].apply(extract_numeric_from_vviq2_response)
            vviq2_scores.append(scores)
        
        # Create DataFrame with scores
        score_df = pd.DataFrame({
            'participantId': df['PROLIFIC_PID'],
            **{f'q{i+1}_score': vviq2_scores[i] for i in range(len(question_cols))}
        })
        
        print("VVIQ2 scores extracted. Sample scores:")
        print(score_df.head(3))
        
        # Calculate total and subscale scores
        print("Calculating VVIQ2 total and subscale scores...")
        
        # Total score (sum of all 32 items), require all items to be present (min_count=32)
        question_score_cols = [f'q{i+1}_score' for i in range(min(32, len(question_cols)))]
        score_df['total_vviq2_score'] = score_df[question_score_cols].sum(axis=1, min_count=len(question_score_cols))
        
        # Subscale scores (4 items each)
        subscales = [
            ('familiar_person_score', list(range(1, 5))),     # Items 1-4
            ('sunrise_score', list(range(5, 9))),             # Items 5-8
            ('shop_front_score', list(range(9, 13))),         # Items 9-12
            ('countryside_score', list(range(13, 17))),       # Items 13-16
            ('driving_score', list(range(17, 21))),           # Items 17-20
            ('beach_score', list(range(21, 25))),             # Items 21-24
            ('railway_station_score', list(range(25, 29))),   # Items 25-28
            ('garden_score', list(range(29, 33)))             # Items 29-32
        ]
        
        for subscale_name, item_indices in subscales:
            if max(item_indices) <= len(question_cols):
                subscale_cols = [f'q{i}_score' for i in item_indices]
                score_df[subscale_name] = score_df[subscale_cols].sum(axis=1, min_count=len(subscale_cols))
                print(f"{subscale_name}: items {min(item_indices)}-{max(item_indices)}")
            else:
                print(f"Warning: Not enough questions for {subscale_name}")
                score_df[subscale_name] = np.nan
        
        # Remove individual question scores, keep only totals and subscales
        final_cols = ['participantId', 'total_vviq2_score'] + [name for name, _ in subscales]
        score_df = score_df[final_cols]
        
        print("VVIQ2 processing complete. Final shape:", score_df.shape)
        print("VVIQ2 score summary:")
        print(score_df.describe())
        
        return score_df
        
    except Exception as e:
        print(f"Error loading VVIQ2 data: {e}")
        raise

def load_vonmises_data(filepath):
    """
    Load von Mises parameters data.
    
    Parameters:
    filepath (str): Path to von Mises CSV file
    
    Returns:
    pd.DataFrame: Filtered von Mises data
    """
    print(f"Loading von Mises data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"Von Mises data loaded. Shape: {df.shape}")
        
        # Print all columns
        print("Von Mises columns:", df.columns.tolist())
        
        # Print first 3 rows
        print("First 3 rows of von Mises data:")
        print(df.head(3))
        
        # Check required columns
        required_cols = ['participantId', 'kappa_overall', 'poor_fit_flag']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in von Mises data")
        
        # Filter out poor fits
        print(f"Total participants in von Mises data: {len(df)}")
        print(f"Poor fit flag values: {df['poor_fit_flag'].value_counts()}")
        
        # Filter to good fits only (poor_fit_flag != True)
        good_fits = df[df['poor_fit_flag'] != True].copy()
        print(f"Participants with good fits: {len(good_fits)}")
        
        print("Von Mises data summary (good fits only):")
        print(good_fits['kappa_overall'].describe())
        
        return good_fits[['participantId', 'kappa_overall']]
        
    except Exception as e:
        print(f"Error loading von Mises data: {e}")
        raise

def calculate_mrt_variability(filepath):
    """
    Calculate MRT reaction time variability per participant.
    
    Parameters:
    filepath (str): Path to MRT CSV file
    
    Returns:
    pd.DataFrame: MRT RT variability by participant
    """
    print(f"Loading MRT data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"MRT data loaded. Shape: {df.shape}")
        
        # Print all columns
        print("MRT columns:", df.columns.tolist())
        
        # Print first 3 rows
        print("First 3 rows of MRT data:")
        print(df.head(3))
        
        # Check required columns
        required_cols = ['participantId', 'isCorrect', 'rt_ms', 'excluded_trial']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in MRT data")
        
        # Print unique values for key design parameters
        if 'angle_degrees' in df.columns:
            print("Unique angle_degrees values:", sorted(df['angle_degrees'].unique()))
        
        print("Unique excluded_trial values:", df['excluded_trial'].unique())
        print("Unique isCorrect values:", df['isCorrect'].unique())
        
        # Filter to valid trials (excluded_trial=False) and correct responses (isCorrect=True)
        valid_trials = df[(df['excluded_trial'] == False) & (df['isCorrect'] == True)].copy()
        print(f"Valid correct trials: {len(valid_trials)} out of {len(df)} total trials")
        
        # Calculate RT variability (standard deviation) per participant
        rt_variability = valid_trials.groupby('participantId')['rt_ms'].std().reset_index()
        rt_variability.columns = ['participantId', 'mrt_rt_variability']
        
        print(f"RT variability calculated for {len(rt_variability)} participants")
        print("MRT RT variability summary:")
        print(rt_variability['mrt_rt_variability'].describe())
        
        return rt_variability
        
    except Exception as e:
        print(f"Error calculating MRT variability: {e}")
        raise

def calculate_vwm_accuracy(filepath):
    """
    Calculate VWM accuracy per participant.
    
    Parameters:
    filepath (str): Path to VWM CSV file
    
    Returns:
    pd.DataFrame: VWM accuracy by participant
    """
    print(f"Loading VWM data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"VWM data loaded. Shape: {df.shape}")
        
        # Print all columns
        print("VWM columns:", df.columns.tolist())
        
        # Print first 3 rows
        print("First 3 rows of VWM data:")
        print(df.head(3))
        
        # Check required columns
        required_cols = ['participantId', 'error_absolute_degrees', 'excluded_trial']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in VWM data")
        
        # Print unique values for key design parameters
        if 'setSize' in df.columns:
            print("Unique setSize values:", sorted(df['setSize'].unique()))
        if 'delay_s' in df.columns:
            print("Unique delay_s values:", sorted(df['delay_s'].unique()))
        
        print("Unique excluded_trial values:", df['excluded_trial'].unique())
        
        # Filter to valid trials (excluded_trial=False)
        valid_trials = df[df['excluded_trial'] == False].copy()
        print(f"Valid trials: {len(valid_trials)} out of {len(df)} total trials")
        
        # Calculate mean absolute error per participant (lower = better accuracy)
        vwm_accuracy = valid_trials.groupby('participantId')['error_absolute_degrees'].mean().reset_index()
        vwm_accuracy.columns = ['participantId', 'mean_vwm_accuracy']
        
        print(f"VWM accuracy calculated for {len(vwm_accuracy)} participants")
        print("VWM accuracy summary (mean absolute error in degrees):")
        print(vwm_accuracy['mean_vwm_accuracy'].describe())
        
        return vwm_accuracy
        
    except Exception as e:
        print(f"Error calculating VWM accuracy: {e}")
        raise

def load_participant_data(filepath):
    """
    Load participant-level data including focus loss instances.
    
    Parameters:
    filepath (str): Path to participant CSV file
    
    Returns:
    pd.DataFrame: Participant data with focus loss instances
    """
    print(f"Loading participant data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"Participant data loaded. Shape: {df.shape}")
        
        # Print all columns
        print("Participant columns:", df.columns.tolist())
        
        # Print first 3 rows
        print("First 3 rows of participant data:")
        print(df.head(3))
        
        # Check required columns
        required_cols = ['participantId', 'focus_loss_instances']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in participant data")
        
        # Filter to included participants if column exists
        if 'included' in df.columns:
            print("Unique included values:", df['included'].unique())
            included_participants = df[df['included'] == True].copy()
            print(f"Included participants: {len(included_participants)} out of {len(df)} total")
        else:
            print("No 'included' column found, using all participants")
            included_participants = df.copy()
        
        print("Focus loss instances summary:")
        print(included_participants['focus_loss_instances'].describe())
        
        return included_participants[['participantId', 'focus_loss_instances']]
        
    except Exception as e:
        print(f"Error loading participant data: {e}")
        raise

def merge_datasets(vviq2_df, vonmises_df, mrt_df, vwm_df, participant_df):
    """
    Merge all datasets on participant ID.
    
    Parameters:
    vviq2_df (pd.DataFrame): VVIQ2 scores
    vonmises_df (pd.DataFrame): Von Mises parameters
    mrt_df (pd.DataFrame): MRT variability
    vwm_df (pd.DataFrame): VWM accuracy
    participant_df (pd.DataFrame): Participant data
    
    Returns:
    pd.DataFrame: Merged dataset
    """
    print("Merging datasets...")
    
    # Start with von Mises data (already filtered for good fits)
    merged_df = vonmises_df.copy()
    print(f"Starting with {len(merged_df)} participants from von Mises data")
    
    # Merge VVIQ2 data
    merged_df = pd.merge(merged_df, vviq2_df, on='participantId', how='inner')
    print(f"After merging VVIQ2: {len(merged_df)} participants")
    
    # Merge MRT variability
    merged_df = pd.merge(merged_df, mrt_df, on='participantId', how='inner')
    print(f"After merging MRT: {len(merged_df)} participants")
    
    # Merge VWM accuracy
    merged_df = pd.merge(merged_df, vwm_df, on='participantId', how='inner')
    print(f"After merging VWM: {len(merged_df)} participants")
    
    # Merge participant data
    merged_df = pd.merge(merged_df, participant_df, on='participantId', how='inner')
    print(f"Final merged dataset: {len(merged_df)} participants")
    
    # Convert focus_loss_instances to numeric type
    if 'focus_loss_instances' in merged_df.columns:
        merged_df['focus_loss_instances'] = pd.to_numeric(merged_df['focus_loss_instances'], errors='coerce')
    
    # Convert all numeric columns to proper numeric types
    numeric_columns = ['kappa_overall', 'total_vviq2_score', 'familiar_person_score', 
                      'sunrise_score', 'shop_front_score', 'countryside_score', 
                      'driving_score', 'beach_score', 'railway_station_score', 
                      'garden_score', 'mrt_rt_variability', 'mean_vwm_accuracy']
    
    for col in numeric_columns:
        if col in merged_df.columns:
            merged_df[col] = pd.to_numeric(merged_df[col], errors='coerce')
            print(f"Converted {col} to numeric type: {merged_df[col].dtype}")
    
    print("Merged dataset columns:", merged_df.columns.tolist())
    print("Data types after conversion:")
    print(merged_df.dtypes)
    print("First 2 rows of merged data:")
    print(merged_df.head(2))
    
    # Check for missing data
    print("Missing data summary:")
    print(merged_df.isnull().sum())
    
    return merged_df

def center_variables(df, variables):
    """
    Center variables at their mean.
    
    Parameters:
    df (pd.DataFrame): Input dataframe
    variables (list): List of variable names to center
    
    Returns:
    pd.DataFrame: Dataframe with centered variables
    """
    print("Centering variables...")
    
    df_centered = df.copy()
    
    for var in variables:
        if var in df_centered.columns:
            mean_val = df_centered[var].mean()
            df_centered[f'{var}_centered'] = df_centered[var] - mean_val
            print(f"{var}: mean = {mean_val:.4f}, centered")
        else:
            print(f"Warning: Variable {var} not found in dataframe")
    
    return df_centered

def run_regression_analysis(df, dependent_var, predictors, model_name):
    """
    Run multiple linear regression analysis.
    """
    print(f"Running regression analysis for {model_name}...")
    
    # Prepare data
    y = df[dependent_var].dropna()
    X_data = df[predictors].loc[y.index].dropna()
    y = y.loc[X_data.index]
    
    print(f"Sample size for {model_name}: {len(y)} participants")
    
    # Print data types and sample values for debugging
    print(f"Dependent variable '{dependent_var}' data type: {y.dtype}")
    print(f"Dependent variable sample values: {y.head(3).tolist()}")
    
    for pred in predictors:
        print(f"Predictor '{pred}' data type: {X_data[pred].dtype}")
        print(f"Predictor '{pred}' sample values: {X_data[pred].head(3).tolist()}")
    
    
    # Add constant term
    X = sm.add_constant(X_data)
    
    # Final data type check
    print(f"Final y data type: {y.dtype}")
    print(f"Final X data types: {X.dtypes.to_dict()}")
    
    # Fit model
    model = sm.OLS(y, X).fit()
    
    # Extract results
    results = {
        'model_name': model_name,
        'n_observations': len(y),
        'predictors': [],
        'coefficients': [],
        'standard_errors': [],
        't_values': [],
        'p_values': [],
        'ci_lower': [],
        'ci_upper': [],
        'r_squared': model.rsquared,
        'adjusted_r_squared': model.rsquared_adj,
        'f_statistic': model.fvalue,
        'f_pvalue': model.f_pvalue,
        'aic': model.aic,
        'residuals': model.resid
    }
    
    # Extract coefficient information
    for i, param in enumerate(model.params.index):
        results['predictors'].append(param)
        results['coefficients'].append(model.params.iloc[i])
        results['standard_errors'].append(model.bse.iloc[i])
        results['t_values'].append(model.tvalues.iloc[i])
        results['p_values'].append(model.pvalues.iloc[i])
        
        # 95% confidence intervals
        ci = model.conf_int().iloc[i]
        results['ci_lower'].append(ci[0])
        results['ci_upper'].append(ci[1])
    
    print(f"Model {model_name} complete:")
    print(f"  R² = {results['r_squared']:.4f}")
    print(f"  Adjusted R² = {results['adjusted_r_squared']:.4f}")
    print(f"  F-statistic = {results['f_statistic']:.4f}, p = {results['f_pvalue']:.6f}")
    
    return results

def apply_fdr_correction(results_list):
    """
    Apply False Discovery Rate correction to p-values across multiple models.
    """
    print("Applying FDR correction to subscale analyses...")
    
    # Initialize p_values_fdr for all results with NaN
    for results in results_list:
        results['p_values_fdr'] = [np.nan] * len(results['p_values'])
    
    # Collect all p-values for kappa_overall_centered predictor
    kappa_pvalues = []
    kappa_indices = []
    
    for i, results in enumerate(results_list):
        for j, predictor in enumerate(results['predictors']):
            if predictor == 'kappa_overall_centered':
                kappa_pvalues.append(results['p_values'][j])
                kappa_indices.append((i, j))
                break
    
    if len(kappa_pvalues) > 0:
        # Apply FDR correction
        rejected, pvals_corrected = fdrcorrection(kappa_pvalues, alpha=0.05)
        
        print(f"FDR correction applied to {len(kappa_pvalues)} tests")
        print(f"Original p-values: {[f'{p:.6f}' for p in kappa_pvalues]}")
        print(f"FDR-corrected p-values: {[f'{p:.6f}' for p in pvals_corrected]}")
        print(f"Significant after FDR correction: {sum(rejected)}")
        
        # Update results with corrected p-values only for kappa_overall_centered
        for idx, (i, j) in enumerate(kappa_indices):
            results_list[i]['p_values_fdr'][j] = pvals_corrected[idx]
    
    return results_list

def save_regression_results(results_list, timestamp):
    """
    Save regression results to CSV file.
    """
    print("Saving regression results...")
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    
    # Prepare results for CSV
    output_rows = []
    
    for results in results_list:
        model_name = results['model_name']
        
        for i, predictor in enumerate(results['predictors']):
            # Get FDR-corrected p-value if available, otherwise NaN
            p_value_fdr = results.get('p_values_fdr', [np.nan] * len(results['p_values']))[i]
            
            row = {
                'model_name': model_name,
                'predictor_name': predictor,
                'coefficient': results['coefficients'][i],
                'standard_error': results['standard_errors'][i],
                't_value': results['t_values'][i],
                'p_value_raw': results['p_values'][i],
                'p_value_fdr': p_value_fdr,
                'ci_lower': results['ci_lower'][i],
                'ci_upper': results['ci_upper'][i],
                'r_squared': results['r_squared'],
                'adjusted_r_squared': results['adjusted_r_squared']
            }
            output_rows.append(row)
    
    # Create DataFrame and save
    results_df = pd.DataFrame(output_rows)
    
    output_file = f'outputs/vviq2_regression_results_{timestamp}.csv'
    results_df.to_csv(output_file, index=False)
    print(f"Regression results saved to: {output_file}")
    print(f"Results shape: {results_df.shape}")

def save_vviq2_scores(vviq2_df, timestamp):
    """
    Save VVIQ2 scores to CSV file.
    
    Parameters:
    vviq2_df (pd.DataFrame): VVIQ2 scores dataframe
    timestamp (str): Timestamp for filename
    """
    print("Saving VVIQ2 scores...")
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    
    output_file = f'outputs/vviq2_scores_{timestamp}.csv'
    vviq2_df.to_csv(output_file, index=False)
    print(f"VVIQ2 scores saved to: {output_file}")
    print(f"Scores shape: {vviq2_df.shape}")

def save_analysis_data(merged_df, timestamp):
    """
    Save complete analysis dataset to CSV file.
    
    Parameters:
    merged_df (pd.DataFrame): Merged analysis dataset
    timestamp (str): Timestamp for filename
    """
    print("Saving analysis dataset...")
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    
    # Select required columns for output
    output_cols = [
        'participantId', 'kappa_overall', 'total_vviq2_score',
        'familiar_person_score', 'sunrise_score', 'shop_front_score',
        'countryside_score', 'driving_score', 'beach_score',
        'railway_station_score', 'garden_score', 'mean_vwm_accuracy',
        'mrt_rt_variability', 'focus_loss_instances'
    ]
    
    # Check which columns exist
    available_cols = [col for col in output_cols if col in merged_df.columns]
    missing_cols = [col for col in output_cols if col not in merged_df.columns]
    
    if missing_cols:
        print(f"Warning: Missing columns in output: {missing_cols}")
    
    output_df = merged_df[available_cols].copy()
    
    output_file = f'outputs/vviq2_analysis_data_{timestamp}.csv'
    output_df.to_csv(output_file, index=False)
    print(f"Analysis dataset saved to: {output_file}")
    print(f"Dataset shape: {output_df.shape}")

def main():
    """Main analysis function."""
    try:
        print("=== VVIQ2 Analysis Script ===")
        print("Starting analysis...")
        
        timestamp = get_timestamp()
        print(f"Analysis timestamp: {timestamp}")
        
        # Load input files
        print("\n--- Loading Input Files ---")
        
        # 1. Load von Mises parameters
        vonmises_file = find_latest_file('outputs/vonmises_parameters_overall_<TIMESTAMP>.csv')
        vonmises_df = load_vonmises_data(vonmises_file)
        
        # 2. Load VVIQ2 data
        vviq2_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        vviq2_df = load_and_process_vviq2_data(vviq2_file)
        
        # 3. Calculate MRT variability
        mrt_file = find_latest_file('outputs/cleaned_mrt_data_<TIMESTAMP>.csv')
        mrt_df = calculate_mrt_variability(mrt_file)
        
        # 4. Calculate VWM accuracy
        vwm_file = find_latest_file('outputs/cleaned_vwm_data_<TIMESTAMP>.csv')
        vwm_df = calculate_vwm_accuracy(vwm_file)
        
        # 5. Load participant data
        participant_file = find_latest_file('outputs/cleaned_participant_data_<TIMESTAMP>.csv')
        participant_df = load_participant_data(participant_file)
        
        # Save VVIQ2 scores
        save_vviq2_scores(vviq2_df, timestamp)
        
        # Merge datasets
        print("\n--- Merging Datasets ---")
        merged_df = merge_datasets(vviq2_df, vonmises_df, mrt_df, vwm_df, participant_df)
        
        if len(merged_df) == 0:
            raise ValueError("No participants remaining after merging datasets")
        
        # Center predictor variables
        print("\n--- Centering Variables ---")
        variables_to_center = ['kappa_overall', 'mean_vwm_accuracy', 'mrt_rt_variability', 'focus_loss_instances']
        merged_df = center_variables(merged_df, variables_to_center)
        
        # Save analysis dataset
        save_analysis_data(merged_df, timestamp)
        
        # Run regression analyses
        print("\n--- Running Regression Analyses ---")
        
        # Define predictors (centered versions)
        predictors = ['kappa_overall_centered', 'mean_vwm_accuracy_centered', 
                     'mrt_rt_variability_centered', 'focus_loss_instances_centered']
        
        # Check if all predictors exist
        missing_predictors = [p for p in predictors if p not in merged_df.columns]
        if missing_predictors:
            print(f"Warning: Missing centered predictors: {missing_predictors}")
            # Use original variables if centered versions don't exist
            predictors = [p.replace('_centered', '') for p in predictors if p.replace('_centered', '') in merged_df.columns]
            print(f"Using original predictors: {predictors}")
        
        results_list = []
        
        # 1. Total VVIQ2 score model
        if 'total_vviq2_score' in merged_df.columns:
            total_results = run_regression_analysis(
                merged_df, 'total_vviq2_score', predictors, 'total_vviq2'
            )
            results_list.append(total_results)
        
        # 2. Subscale models
        subscales = [
            'familiar_person_score', 'sunrise_score', 'shop_front_score',
            'countryside_score', 'driving_score', 'beach_score',
            'railway_station_score', 'garden_score'
        ]
        
        subscale_results = []
        for subscale in subscales:
            if subscale in merged_df.columns:
                subscale_result = run_regression_analysis(
                    merged_df, subscale, predictors, subscale
                )
                subscale_results.append(subscale_result)
                results_list.append(subscale_result)
        
        # Apply FDR correction to subscale analyses only if kappa is significant in total model
        if len(subscale_results) > 0:
            print("\n--- Checking Total Model Significance ---")
            
            # Check if kappa_overall_centered is significant in total model
            total_kappa_pvalue = None
            for results in results_list:
                if results['model_name'] == 'total_vviq2':
                    for i, pred in enumerate(results['predictors']):
                        if pred == 'kappa_overall_centered':
                            total_kappa_pvalue = results['p_values'][i]
                            print(f"kappa_overall p-value in total model: {total_kappa_pvalue:.6f}")
                            break
                    break
            
            # Only apply FDR if kappa is significant in total model
            if total_kappa_pvalue is not None and total_kappa_pvalue < 0.05:
                print("kappa_overall is significant in total model - applying FDR correction to subscales")
                print("\n--- Applying FDR Correction ---")
                subscale_results = apply_fdr_correction(subscale_results)
                
                # Update results_list with corrected p-values
                for i, subscale_result in enumerate(subscale_results):
                    for j, result in enumerate(results_list):
                        if result['model_name'] == subscale_result['model_name']:
                            results_list[j] = subscale_result
                            break
            else:
                print("kappa_overall is not significant in total model - skipping FDR correction")
        
        # Save results
        print("\n--- Saving Results ---")
        save_regression_results(results_list, timestamp)
        
        print("\n=== Analysis Complete ===")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
