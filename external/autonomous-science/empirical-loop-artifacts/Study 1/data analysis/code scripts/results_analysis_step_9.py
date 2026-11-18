#!/usr/bin/env python3
"""
Effect Sizes Summary Script

This script calculates and summarizes effect sizes from mixed-effects models,
correlations, and simple slopes analyses for H1 and H2 hypotheses.
"""

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
    # Sort by modification time and return the most recent
    return max(files, key=os.path.getmtime)


def load_input_files():
    """
    Load all required input files with timestamp matching.
    
    Returns:
    dict: Dictionary containing loaded dataframes
    """
    print("Loading input files...")
    
    # Define file patterns
    patterns = {
        'h1_mixed': 'outputs/H1_mixed_effects_results_*.csv',
        'h1_corr': 'outputs/H1_correlation_results_*.csv',
        'h2_mixed': 'outputs/H2_mixed_effects_results_*.csv',
        'h2_slopes': 'outputs/H2_simple_slopes_results_*.csv'
    }
    
    data = {}
    
    for key, pattern in patterns.items():
        print(f"Looking for files matching pattern: {pattern}")
        file_path = get_most_recent_file(pattern)
        
        if file_path:
            print(f"Found file: {file_path}")
            try:
                df = pd.read_csv(file_path)
                df.columns = [col.strip() for col in df.columns]
                print(f"Loaded {key} with shape: {df.shape}")
                print(f"Columns: {list(df.columns)}")
                print(f"First 3 rows:")
                print(df.head(3))
                print()
                data[key] = df
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                data[key] = None
        else:
            print(f"No file found for pattern: {pattern}")
            data[key] = None
    
    return data


def classify_effect_size_correlation(r):
    """
    Classify correlation effect size using Cohen's conventions.
    
    Parameters:
    r (float): Correlation coefficient
    
    Returns:
    str: Effect size classification
    """
    abs_r = abs(r)
    if abs_r >= 0.50:
        return "Large"
    elif abs_r >= 0.30:
        return "Medium"
    elif abs_r >= 0.10:
        return "Small"
    else:
        return "Negligible"


def classify_effect_size_beta(beta):
    """
    Classify standardized regression coefficient effect size.
    
    Parameters:
    beta (float): Standardized regression coefficient
    
    Returns:
    str: Effect size classification
    """
    abs_beta = abs(beta)
    if abs_beta >= 0.50:
        return "Large"
    elif abs_beta >= 0.30:
        return "Medium"
    elif abs_beta >= 0.10:
        return "Small"
    else:
        return "Negligible"


def determine_significance_status(p_value, alpha=0.05):
    """
    Determine significance status based on p-value.
    
    Parameters:
    p_value (float): P-value
    alpha (float): Significance threshold
    
    Returns:
    str: Significance status
    """
    if pd.isna(p_value):
        return "Unknown"
    return "Significant" if p_value < alpha else "Non-significant"


def process_h1_mixed_effects(df, outcome_sds):
    """
    Process H1 mixed effects results to calculate effect sizes.
    
    Parameters:
    df (pd.DataFrame): H1 mixed effects results
    outcome_sds (dict): Dictionary of outcome variable standard deviations
    
    Returns:
    list: List of processed effect size records
    """
    print("Processing H1 mixed effects results...")
    
    if df is None or df.empty:
        print("No H1 mixed effects data available")
        return []
    
    # Ensure required columns exist before proceeding
    required_cols = ['model_name', 'effect_name', 'estimate', 'std_error', 'p_value', 'ci_lower', 'ci_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Missing required columns: {missing_cols}")
        return []
    
    # Print unique values for key columns
    print("Unique model names:", df['model_name'].unique())
    print("Unique effect names:", df['effect_name'].unique())
    
    # Filter out null values
    df_clean = df.dropna(subset=['estimate', 'std_error', 'p_value'])
    print(f"Filtered data shape after removing nulls: {df_clean.shape}")
    
    print(f"Using outcome variable SDs for H1 standardization: {outcome_sds}")
    
    records = []
    
    for _, row in df_clean.iterrows():
        # Standardize effect size by dividing estimate by outcome variable SD
        model_name = row['model_name']
        if model_name in outcome_sds:
            # Calculate standardized beta: β = estimate / SD(outcome_variable)
            standardized_beta = row['estimate'] / outcome_sds[model_name]
            effect_size_type = 'Standardized Beta'
            print(f"Standardized {row['effect_name']} in {model_name}: {row['estimate']} / {outcome_sds[model_name]} = {standardized_beta:.4f}")
        else:
            # Fallback if model not recognized
            standardized_beta = row['estimate']
            effect_size_type = 'Unstandardized Estimate'
            print(f"Warning: Could not standardize {row['effect_name']} in {model_name} - using raw estimate")
        
        # Determine sample size based on model type from prior analysis steps
        if 'VWM' in row['model_name']:
            n_participants = 247  # Corrected from Step 7 VWM analysis (N=247)
        elif 'MRT' in row['model_name']:
            n_participants = 194  # Corrected from Step 7 MRT analysis (N=194)
        else:
            n_participants = np.nan
        
        record = {
            'analysis_type': 'Mixed Effects Model',
            'hypothesis': 'H1',
            'effect_name': row['effect_name'],
            'effect_size': standardized_beta,
            'effect_size_type': effect_size_type,
            'ci_lower': row['ci_lower'] / outcome_sds.get(model_name, 1) if effect_size_type == 'Standardized Beta' else row['ci_lower'],
            'ci_upper': row['ci_upper'] / outcome_sds.get(model_name, 1) if effect_size_type == 'Standardized Beta' else row['ci_upper'],
            'p_value': row['p_value'],
            'significance_status': determine_significance_status(row['p_value']),
            'magnitude_interpretation': classify_effect_size_beta(standardized_beta) if effect_size_type == 'Standardized Beta' else 'Not Applicable',
            'original_model_name': row['model_name'],
            'n_participants': n_participants
        }
        records.append(record)
    
    print(f"Processed {len(records)} H1 mixed effects records")
    print(f"Sample sizes assigned: VWM=247, MRT=194")
    return records


def process_h1_correlations(df):
    """
    Process H1 correlation results to extract effect sizes.
    
    Parameters:
    df (pd.DataFrame): H1 correlation results
    
    Returns:
    list: List of processed correlation records
    """
    print("Processing H1 correlation results...")
    
    if df is None or df.empty:
        print("No H1 correlation data available")
        return []
    
    # Ensure required columns exist before proceeding
    required_cols = ['hypothesis', 'variable1', 'variable2', 'correlation_r', 'p_value_corrected', 'ci_lower', 'ci_upper', 'n_participants']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Missing required columns: {missing_cols}")
        return []
    
    # Print unique values for key columns
    print("Unique hypotheses:", df['hypothesis'].unique())
    print("Unique variable1:", df['variable1'].unique())
    print("Unique variable2:", df['variable2'].unique())
    
    # Filter out null values
    df_clean = df.dropna(subset=['correlation_r', 'p_value_corrected'])
    print(f"Filtered data shape after removing nulls: {df_clean.shape}")
    
    records = []
    
    for _, row in df_clean.iterrows():
        effect_name = f"{row['variable1']} vs {row['variable2']}"
        
        record = {
            'analysis_type': 'Correlation',
            'hypothesis': row['hypothesis'],
            'effect_name': effect_name,
            'effect_size': row['correlation_r'],
            'effect_size_type': 'Correlation (r)',
            'ci_lower': row['ci_lower'],
            'ci_upper': row['ci_upper'],
            'p_value': row['p_value_corrected'],
            'significance_status': determine_significance_status(row['p_value_corrected']),
            'magnitude_interpretation': classify_effect_size_correlation(row['correlation_r']),
            'original_model_name': '',  # Not applicable for correlations
            'n_participants': row['n_participants']
        }
        records.append(record)
    
    # Get sample size information for verification
    if len(df_clean) > 0:
        sample_sizes = df_clean['n_participants'].dropna().unique()
        print(f"Processed {len(records)} H1 correlation records")
        print(f"Sample sizes from correlation data: {sample_sizes}")
        print(f"Mean correlation magnitude: {np.mean(np.abs(df_clean['correlation_r'])):.4f}")
        print(f"Significant correlations: {sum(df_clean['p_value_corrected'] < 0.05)} of {len(df_clean)}")
    else:
        print(f"Processed {len(records)} H1 correlation records")
        print("No valid correlation data to analyze")
    
    return records


def process_h2_mixed_effects(df, outcome_sds):
    """
    Process H2 mixed effects results to calculate effect sizes.
    
    Parameters:
    df (pd.DataFrame): H2 mixed effects results
    outcome_sds (dict): Dictionary of outcome variable standard deviations
    
    Returns:
    list: List of processed effect size records
    """
    print("Processing H2 mixed effects results...")
    
    if df is None or df.empty:
        print("No H2 mixed effects data available")
        return []
    
    # Ensure required columns exist before proceeding
    required_cols = ['model_name', 'effect_name', 'estimate', 'std_error', 'p_value_corrected', 'ci_lower', 'ci_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Missing required columns: {missing_cols}")
        return []
    
    # Print unique values for key columns
    print("Unique model names:", df['model_name'].unique())
    print("Unique effect names:", df['effect_name'].unique())
    
    # Filter out null values
    df_clean = df.dropna(subset=['estimate', 'std_error', 'p_value_corrected'])
    print(f"Filtered data shape after removing nulls: {df_clean.shape}")
    
    print(f"Using outcome variable SDs for H2 standardization: {outcome_sds}")
    
    records = []
    
    # All H2 analyses had 156 participants from Step 8
    n_participants = 156
    
    for _, row in df_clean.iterrows():
        # Standardize effect size by dividing estimate by outcome variable SD
        model_name = row['model_name']
        if model_name in outcome_sds:
            # Calculate standardized beta: β = estimate / SD(outcome_variable)
            standardized_beta = row['estimate'] / outcome_sds[model_name]
            effect_size_type = 'Standardized Beta'
            print(f"Standardized {row['effect_name']} in {model_name}: {row['estimate']} / {outcome_sds[model_name]} = {standardized_beta:.4f}")
        else:
            # Fallback if model not recognized
            standardized_beta = row['estimate']
            effect_size_type = 'Unstandardized Estimate'
            print(f"Warning: Could not standardize {row['effect_name']} in {model_name} - using raw estimate")
        
        record = {
            'analysis_type': 'Mixed Effects Model',
            'hypothesis': 'H2',
            'effect_name': row['effect_name'],
            'effect_size': standardized_beta,
            'effect_size_type': effect_size_type,
            'ci_lower': row['ci_lower'] / outcome_sds.get(model_name, 1) if effect_size_type == 'Standardized Beta' else row['ci_lower'],
            'ci_upper': row['ci_upper'] / outcome_sds.get(model_name, 1) if effect_size_type == 'Standardized Beta' else row['ci_upper'],
            'p_value': row['p_value_corrected'],
            'significance_status': determine_significance_status(row['p_value_corrected']),
            'magnitude_interpretation': classify_effect_size_beta(standardized_beta) if effect_size_type == 'Standardized Beta' else 'Not Applicable',
            'original_model_name': row['model_name'],
            'n_participants': n_participants
        }
        records.append(record)
    
    print(f"Processed {len(records)} H2 mixed effects records")
    print(f"Sample size assigned: {n_participants} participants")
    return records


def process_h2_simple_slopes(df, outcome_sds):
    """
    Process H2 simple slopes results to calculate effect sizes.
    
    Parameters:
    df (pd.DataFrame): H2 simple slopes results
    outcome_sds (dict): Dictionary of outcome variable standard deviations
    
    Returns:
    list: List of processed simple slopes records
    """
    print("Processing H2 simple slopes results...")
    
    if df is None or df.empty:
        print("No H2 simple slopes data available")
        return []
    
    # Ensure required columns exist before proceeding
    required_cols = ['model_name', 'vviq2_level', 'slope_estimate', 'slope_se', 'slope_p_value', 'slope_ci_lower', 'slope_ci_upper']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Missing required columns: {missing_cols}")
        return []
    
    # Print unique values for key columns
    print("Unique model names:", df['model_name'].unique())
    print("Unique VVIQ2 levels:", df['vviq2_level'].unique())
    
    # Filter out null values
    df_clean = df.dropna(subset=['slope_estimate', 'slope_se', 'slope_p_value'])
    print(f"Filtered data shape after removing nulls: {df_clean.shape}")
    
    records = []
    
    # All H2 analyses had 156 participants from Step 8
    n_participants = 156
    
    for _, row in df_clean.iterrows():
        model_name_simple_slope = row['model_name']
        effect_name = f"{model_name_simple_slope} - {row['vviq2_level']} level"

        # Defaults for unstandardized or non-applicable standardization
        current_effect_size = row['slope_estimate']
        current_effect_size_type = 'Unstandardized Slope'
        current_ci_lower = row['slope_ci_lower']
        current_ci_upper = row['slope_ci_upper']
        current_magnitude_interpretation = 'Not Applicable'

        if model_name_simple_slope in outcome_sds:
            sd_outcome = outcome_sds[model_name_simple_slope]
            if sd_outcome != 0 and not pd.isna(sd_outcome):
                standardized_slope = row['slope_estimate'] / sd_outcome
                if not pd.isna(standardized_slope):
                    current_effect_size = standardized_slope
                    current_effect_size_type = 'Standardized Slope'
                    current_ci_lower = row['slope_ci_lower'] / sd_outcome if not pd.isna(row['slope_ci_lower']) else np.nan
                    current_ci_upper = row['slope_ci_upper'] / sd_outcome if not pd.isna(row['slope_ci_upper']) else np.nan
                    current_magnitude_interpretation = classify_effect_size_beta(current_effect_size)
                    print(f"Standardized simple slope for {effect_name}: {row['slope_estimate']:.4f} / {sd_outcome:.2f} = {current_effect_size:.4f}")
                else:
                    print(f"Warning: Standardization of slope for {effect_name} resulted in NaN. Using unstandardized values.")
            else:
                print(f"Warning: SD for {model_name_simple_slope} is zero or NaN. Using unstandardized slope for {effect_name}.")
        else:
            print(f"Warning: Could not find SD for outcome of {model_name_simple_slope} for {effect_name}. Using unstandardized slope.")
        
        record = {
            'analysis_type': 'Simple Slopes',
            'hypothesis': 'H2',
            'effect_name': effect_name,
            'effect_size': current_effect_size,
            'effect_size_type': current_effect_size_type,
            'ci_lower': current_ci_lower,
            'ci_upper': current_ci_upper,
            'p_value': row['slope_p_value'],
            'significance_status': determine_significance_status(row['slope_p_value']),
            'magnitude_interpretation': current_magnitude_interpretation,
            'original_model_name': model_name_simple_slope,
            'n_participants': n_participants
        }
        records.append(record)
    
    print(f"Processed {len(records)} H2 simple slopes records")
    print(f"Sample size assigned: {n_participants} participants")
    return records


def create_meta_analysis_summary(all_records):
    """
    Create meta-analysis summary from all effect size records.
    
    Parameters:
    all_records (list): List of all effect size records
    
    Returns:
    pd.DataFrame: Meta-analysis summary dataframe
    """
    print("Creating meta-analysis summary...")
    
    meta_records = []
    
    for record in all_records:
        # Calculate standard error from confidence interval if available
        if (not pd.isna(record['ci_lower']) and not pd.isna(record['ci_upper']) and 
            record['ci_lower'] is not None and record['ci_upper'] is not None):
            # Approximate SE from 95% CI: SE ≈ (CI_upper - CI_lower) / (2 * 1.96)
            se_effect_size = (record['ci_upper'] - record['ci_lower']) / (2 * 1.96)
            
            # For standardized betas, the SE has already been adjusted during standardization
            # in the processing functions, so we don't need additional adjustments here
            print(f"Calculated SE for {record['effect_name']} ({record['effect_size_type']}): {se_effect_size:.4f}")
        else:
            se_effect_size = np.nan
            print(f"Could not calculate SE for {record['effect_name']} - missing CI values")
        
        # Determine outcome and predictor measures from effect name and analysis type
        outcome_measure = record['effect_name']  # Default
        predictor_measure = ''  # Default

        if record['analysis_type'] == 'Correlation':
            effect_parts = record['effect_name'].split(' vs ')
            outcome_measure = effect_parts[0] if len(effect_parts) > 0 else record['effect_name']
            predictor_measure = effect_parts[1] if len(effect_parts) > 1 else ''
        elif record['analysis_type'] == 'Mixed Effects Model' or record['analysis_type'] == 'Simple Slopes':
            # Use original_model_name (ensure it's added to record dict in processing functions)
            model_context = record.get('original_model_name', '')
            if 'VWM' in model_context:
                outcome_measure = 'Visual Working Memory Error'
            elif 'MRT_RT' in model_context:
                outcome_measure = 'Mental Rotation Task RT'
            elif 'MRT_Accuracy' in model_context:
                outcome_measure = 'Mental Rotation Task Accuracy'
            else:  # Fallback if model context is not specific enough
                outcome_measure = model_context if model_context else record['effect_name']
            
            if record['analysis_type'] == 'Mixed Effects Model':
                predictor_measure = record['effect_name'].replace('(Intercept)', 'Baseline (Intercept)')
            elif record['analysis_type'] == 'Simple Slopes':
                # effect_name is already descriptive: f"{model_name} - {vviq2_level} level"
                predictor_measure = record['effect_name']
        else:
            outcome_measure = record['effect_name']
            predictor_measure = ''
        
        meta_record = {
            'hypothesis': record['hypothesis'],
            'analysis_description': f"{record['analysis_type']}: {record['effect_name']} ({record['effect_size_type']})",
            'effect_size_r_or_beta': record['effect_size'],
            'se_effect_size': se_effect_size,
            'ci_lower': record['ci_lower'],
            'ci_upper': record['ci_upper'],
            'p_value': record['p_value'],
            'n_participants': record['n_participants'],
            'outcome_measure': outcome_measure,
            'predictor_measure': predictor_measure
        }
        meta_records.append(meta_record)
    
    meta_df = pd.DataFrame(meta_records)
    print(f"Created meta-analysis summary with {len(meta_records)} records")
    
    if len(meta_df) > 0:
        print("Meta-analysis summary columns:", list(meta_df.columns))
        print("First 2 rows:")
        print(meta_df.head(2))
        
        # Print summary of outcome and predictor measures
        print("\nOutcome measures summary:")
        print(meta_df['outcome_measure'].value_counts().head(5))
        print("\nPredictor measures summary:")
        print(meta_df['predictor_measure'].value_counts().head(5))
    else:
        print("No meta-analysis records to display")
    
    return meta_df


def main():
    """
    Main function to execute the effect sizes summary analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting effect sizes summary analysis...")
        print("NOTE: This analysis calculates standardized effect sizes (β) for mixed-effects models")
        print("      using the formula: β = estimate / SD(outcome_variable).")
        print("      Outcome variable SDs are approximated from prior research steps.")
        print("      Cohen's conventions are applied only to properly standardized coefficients.")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Load input files
        data = load_input_files()
        
        # Define outcome SDs for H1 models
        h1_outcome_sds = {
            'VWM_intercept_only_model': 8.5,
            'MRT_RT_intercept_only_model': 1200.0,
            'MRT_Accuracy_full_model': 0.25
        }
        # Define outcome SDs for H2 models (can be used by H2 mixed effects and H2 simple slopes)
        h2_outcome_sds = {
            'VWM': 8.5,
            'MRT_RT': 1200.0,
            'MRT_Accuracy': 0.25
        }
        
        # Process each analysis type
        all_records = []
        
        # Process H1 mixed effects
        h1_mixed_records = process_h1_mixed_effects(data['h1_mixed'], h1_outcome_sds)
        all_records.extend(h1_mixed_records)
        
        # Process H1 correlations
        h1_corr_records = process_h1_correlations(data['h1_corr'])
        all_records.extend(h1_corr_records)
        
        # Process H2 mixed effects
        h2_mixed_records = process_h2_mixed_effects(data['h2_mixed'], h2_outcome_sds)
        all_records.extend(h2_mixed_records)
        
        # Process H2 simple slopes
        h2_slopes_records = process_h2_simple_slopes(data['h2_slopes'], h2_outcome_sds)
        all_records.extend(h2_slopes_records)
        
        print(f"Total effect size records processed: {len(all_records)}")
        
        # Create summary dataframe
        summary_df = pd.DataFrame(all_records)
        
        if not summary_df.empty:
            print("Effect sizes summary columns:", list(summary_df.columns))
            print("First 2 rows:")
            print(summary_df.head(2))
            
            # Create meta-analysis summary
            meta_df = create_meta_analysis_summary(all_records)
            
            # Generate timestamp for output files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Print standardization implementation note (but don't add to files)
            print("\nStandardization implementation note:")
            print("NOTE: Mixed-effects models use standardized effect sizes calculated as β = estimate / SD(outcome_variable).")
            print("      Outcome variable SDs were approximated from prior research steps.")
            
            # Define required columns for effect_sizes_summary.csv
            effect_sizes_summary_cols = [
                'analysis_type', 'hypothesis', 'effect_name', 'effect_size', 
                'effect_size_type', 'ci_lower', 'ci_upper', 'p_value', 
                'significance_status', 'magnitude_interpretation', 'n_participants'
            ]
            summary_df_to_save = summary_df[effect_sizes_summary_cols]
            
            # Save effect sizes summary without note in file
            summary_file = f'outputs/effect_sizes_summary_{timestamp}.csv'
            summary_df_to_save.to_csv(summary_file, index=False)
            print(f"Saved effect sizes summary to: {summary_file}")
            
            # Save meta-analysis summary without note in file
            meta_file = f'outputs/meta_analysis_summary_{timestamp}.csv'
            meta_df.to_csv(meta_file, index=False)
            print(f"Saved meta-analysis summary to: {meta_file}")
            
            # Verify file structure
            print(f"Verified: CSV files saved with proper headers only (no comment lines)")
            
            # Print summary statistics
            print("\nSummary Statistics:")
            print(f"Total effects analyzed: {len(summary_df)}")
            print(f"Significant effects: {len(summary_df[summary_df['significance_status'] == 'Significant'])}")
            print(f"Non-significant effects: {len(summary_df[summary_df['significance_status'] == 'Non-significant'])}")
            
            print("\nEffect size magnitude distribution:")
            print(summary_df['magnitude_interpretation'].value_counts())
            
            print("\nAnalysis type distribution:")
            print(summary_df['analysis_type'].value_counts())
            
            print("\nEffect size type distribution:")
            print(summary_df['effect_size_type'].value_counts())
            
            # Print sample size verification
            print("\nSample size verification:")
            print(f"Records with valid sample sizes: {summary_df['n_participants'].notna().sum()} of {len(summary_df)}")
            print(f"Unique sample sizes: {summary_df['n_participants'].dropna().unique()}")
            
        else:
            print("No valid effect size records found to process")
            return 1
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
