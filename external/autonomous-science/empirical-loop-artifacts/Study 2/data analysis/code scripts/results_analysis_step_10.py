#!/usr/bin/env python3
"""
Cross-task correlation analysis between VWM DoG parameters, MRT facilitation indices, and VVIQ2 scores.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import scipy.stats as stats
from scipy.stats import pearsonr
import warnings
warnings.filterwarnings('ignore')

# Import R interface
try:
    import rpy2.robjects as robjects
    from rpy2.robjects import pandas2ri, Formula
    from rpy2.robjects.packages import importr
    pandas2ri.activate()
    R_AVAILABLE = True
    print("R interface available via rpy2")
except ImportError:
    R_AVAILABLE = False
    print("Warning: R interface not available, will skip moderation analyses")

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern with <TIMESTAMP> placeholder
    
    Returns:
    str: Path to the most recent matching file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        print(f"No files found matching pattern: {search_pattern}")
        return None
    
    # Sort by modification time, most recent first
    matching_files.sort(key=os.path.getmtime, reverse=True)
    latest_file = matching_files[0]
    print(f"Found {len(matching_files)} files matching pattern, using latest: {latest_file}")
    return latest_file

def load_and_validate_data():
    """
    Load and validate all required input datasets.
    
    Returns:
    tuple: (vwm_data, mrt_data, vviq_data) or (None, None, None) if loading fails
    """
    print("=" * 60)
    print("LOADING AND VALIDATING INPUT DATA")
    print("=" * 60)
    
    # Load VWM DoG parameters
    vwm_file = find_latest_file('outputs/VWM_DoG_parameters_<TIMESTAMP>.csv')
    if not vwm_file:
        print("ERROR: VWM DoG parameters file not found")
        return None, None, None
    
    try:
        vwm_data = pd.read_csv(vwm_file)
        vwm_data.columns = [col.strip() for col in vwm_data.columns]
        print(f"\nVWM DoG parameters loaded from: {vwm_file}")
        print(f"VWM data shape: {vwm_data.shape}")
        print("VWM columns:", list(vwm_data.columns))
        print("First 3 rows of VWM data:")
        print(vwm_data.head(3))
        
        # Check required columns
        required_vwm_cols = ['participantId', 'VWM_setSize', 'VWM_delay_s', 'amplitude', 'width', 'zero_crossing', 'excluded_fitting']
        missing_vwm_cols = [col for col in required_vwm_cols if col not in vwm_data.columns]
        if missing_vwm_cols:
            print(f"ERROR: Missing VWM columns: {missing_vwm_cols}")
            return None, None, None
        
        # Print unique values for key experimental parameters
        print(f"Unique VWM_setSize values: {sorted(vwm_data['VWM_setSize'].unique())}")
        print(f"Unique VWM_delay_s values: {sorted(vwm_data['VWM_delay_s'].unique())}")
        print(f"Unique excluded_fitting values: {sorted(vwm_data['excluded_fitting'].unique())}")
        print(f"Variable types - amplitude: {type(vwm_data['amplitude'].iloc[0])}, width: {type(vwm_data['width'].iloc[0])}, zero_crossing: {type(vwm_data['zero_crossing'].iloc[0])}")
        
    except Exception as e:
        print(f"ERROR loading VWM data: {e}")
        return None, None, None
    
    # Load MRT facilitation indices
    mrt_file = find_latest_file('outputs/MRT_sequential_facilitation_indices_<TIMESTAMP>.csv')
    if not mrt_file:
        print("ERROR: MRT facilitation indices file not found")
        return None, None, None
    
    try:
        mrt_data = pd.read_csv(mrt_file)
        mrt_data.columns = [col.strip() for col in mrt_data.columns]
        print(f"\nMRT facilitation indices loaded from: {mrt_file}")
        print(f"MRT data shape: {mrt_data.shape}")
        print("MRT columns:", list(mrt_data.columns))
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        # Check required columns
        required_mrt_cols = ['participantId', 'rt_facilitation_slope', 'accuracy_facilitation_index', 'sufficient_data']
        missing_mrt_cols = [col for col in required_mrt_cols if col not in mrt_data.columns]
        if missing_mrt_cols:
            print(f"ERROR: Missing MRT columns: {missing_mrt_cols}")
            return None, None, None
        
        # Print unique values for key parameters
        print(f"Unique sufficient_data values: {sorted(mrt_data['sufficient_data'].unique())}")
        print(f"Variable types - rt_facilitation_slope: {type(mrt_data['rt_facilitation_slope'].iloc[0])}, accuracy_facilitation_index: {type(mrt_data['accuracy_facilitation_index'].iloc[0])}")
        print(f"RT facilitation slope range: {mrt_data['rt_facilitation_slope'].min():.6f} to {mrt_data['rt_facilitation_slope'].max():.6f}")
        print(f"Accuracy facilitation index range: {mrt_data['accuracy_facilitation_index'].min():.6f} to {mrt_data['accuracy_facilitation_index'].max():.6f}")
        
    except Exception as e:
        print(f"ERROR loading MRT data: {e}")
        return None, None, None
    
    # Load VVIQ2 scores
    vviq_file = find_latest_file('outputs/VVIQ2_cleaned_scores_<TIMESTAMP>.csv')
    if not vviq_file:
        print("ERROR: VVIQ2 scores file not found")
        return None, None, None
    
    try:
        vviq_data = pd.read_csv(vviq_file)
        vviq_data.columns = [col.strip() for col in vviq_data.columns]
        print(f"\nVVIQ2 scores loaded from: {vviq_file}")
        print(f"VVIQ2 data shape: {vviq_data.shape}")
        print("VVIQ2 columns:", list(vviq_data.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq_data.head(3))
        
        # Check required columns
        required_vviq_cols = ['PROLIFIC_PID', 'total_score_z', 'excluded_participant']
        missing_vviq_cols = [col for col in required_vviq_cols if col not in vviq_data.columns]
        if missing_vviq_cols:
            print(f"ERROR: Missing VVIQ2 columns: {missing_vviq_cols}")
            return None, None, None
        
        # Print unique values for key parameters
        print(f"Unique excluded_participant values: {sorted(vviq_data['excluded_participant'].unique())}")
        print(f"Variable type - total_score_z: {type(vviq_data['total_score_z'].iloc[0])}")
        print(f"Total score z range: {vviq_data['total_score_z'].min():.3f} to {vviq_data['total_score_z'].max():.3f}")
        
    except Exception as e:
        print(f"ERROR loading VVIQ2 data: {e}")
        return None, None, None
    
    return vwm_data, mrt_data, vviq_data

def merge_datasets(vwm_data, mrt_data, vviq_data):
    """
    Merge all datasets and apply exclusion criteria.
    
    Parameters:
    vwm_data (pd.DataFrame): VWM DoG parameters
    mrt_data (pd.DataFrame): MRT facilitation indices  
    vviq_data (pd.DataFrame): VVIQ2 scores
    
    Returns:
    pd.DataFrame: Merged dataset with exclusions applied
    """
    print("\n" + "=" * 60)
    print("MERGING DATASETS AND APPLYING EXCLUSIONS")
    print("=" * 60)
    
    print(f"Initial sample sizes:")
    print(f"  VWM data: {len(vwm_data['participantId'].unique())} unique participants")
    print(f"  MRT data: {len(mrt_data['participantId'].unique())} unique participants")
    print(f"  VVIQ2 data: {len(vviq_data['PROLIFIC_PID'].unique())} unique participants")
    
    # Apply exclusion criteria before merging
    print(f"\nApplying exclusion criteria...")
    
    # VWM exclusions
    vwm_before = len(vwm_data)
    vwm_included = vwm_data[vwm_data['excluded_fitting'] == False].copy()
    vwm_after = len(vwm_included)
    print(f"VWM exclusions: {vwm_before - vwm_after} rows excluded for excluded_fitting=True")
    print(f"VWM after exclusions: {len(vwm_included['participantId'].unique())} unique participants")
    
    # MRT exclusions
    mrt_before = len(mrt_data)
    mrt_included = mrt_data[mrt_data['sufficient_data'] == True].copy()
    mrt_after = len(mrt_included)
    print(f"MRT exclusions: {mrt_before - mrt_after} rows excluded for sufficient_data=False")
    print(f"MRT after exclusions: {len(mrt_included['participantId'].unique())} unique participants")
    
    # VVIQ2 exclusions
    vviq_before = len(vviq_data)
    vviq_included = vviq_data[vviq_data['excluded_participant'] == False].copy()
    vviq_after = len(vviq_included)
    print(f"VVIQ2 exclusions: {vviq_before - vviq_after} rows excluded for excluded_participant=True")
    print(f"VVIQ2 after exclusions: {len(vviq_included['PROLIFIC_PID'].unique())} unique participants")
    
    # Merge datasets
    print(f"\nMerging datasets...")
    
    # First merge VWM and MRT on participantId
    merged_vm = pd.merge(vwm_included, mrt_included, on='participantId', how='inner')
    print(f"After VWM-MRT merge: {len(merged_vm['participantId'].unique())} unique participants")
    
    # Then merge with VVIQ2 using participantId = PROLIFIC_PID
    merged_all = pd.merge(merged_vm, vviq_included, 
                         left_on='participantId', right_on='PROLIFIC_PID', how='inner')
    print(f"After full merge: {len(merged_all['participantId'].unique())} unique participants")
    
    print(f"Final merged dataset shape: {merged_all.shape}")
    print("Final merged dataset columns:", list(merged_all.columns))
    print("First 2 rows of merged dataset:")
    print(merged_all.head(2))
    
    return merged_all

def aggregate_vwm_parameters(merged_data):
    """
    Aggregate VWM DoG parameters across conditions per participant.
    
    Parameters:
    merged_data (pd.DataFrame): Merged dataset
    
    Returns:
    pd.DataFrame: Participant-level aggregated data
    """
    print("\n" + "=" * 60)
    print("AGGREGATING VWM DOG PARAMETERS")
    print("=" * 60)
    
    print("Aggregating VWM DoG parameters across conditions per participant...")
    
    # Check available conditions
    conditions = merged_data.groupby(['VWM_setSize', 'VWM_delay_s']).size()
    print("Available VWM conditions:")
    print(conditions)
    
    # Aggregate parameters by participant
    vwm_agg = merged_data.groupby('participantId').agg({
        'amplitude': 'mean',
        'width': 'mean', 
        'zero_crossing': 'mean',
        'rt_facilitation_slope': 'first',  # These should be the same across VWM conditions
        'accuracy_facilitation_index': 'first',
        'total_score_z': 'first'
    }).reset_index()
    
    # Rename columns for clarity
    vwm_agg = vwm_agg.rename(columns={
        'amplitude': 'vwm_mean_amplitude',
        'width': 'vwm_mean_width',
        'zero_crossing': 'vwm_mean_zero_crossing',
        'rt_facilitation_slope': 'mrt_rt_facilitation_slope',
        'accuracy_facilitation_index': 'mrt_accuracy_facilitation_index',
        'total_score_z': 'vviq2_total_score_z'
    })
    
    # Add inclusion flag
    vwm_agg['included_final_analysis'] = True
    
    print(f"Aggregated dataset shape: {vwm_agg.shape}")
    print("Aggregated dataset columns:", list(vwm_agg.columns))
    print("First 2 rows of aggregated dataset:")
    print(vwm_agg.head(2))
    
    # Summary statistics
    print("\nSummary statistics for aggregated VWM parameters:")
    for param in ['vwm_mean_amplitude', 'vwm_mean_width', 'vwm_mean_zero_crossing']:
        values = vwm_agg[param]
        print(f"{param}: Mean={values.mean():.4f}, SD={values.std():.4f}, Range=[{values.min():.4f}, {values.max():.4f}]")
    
    print("\nSummary statistics for MRT facilitation indices:")
    for param in ['mrt_rt_facilitation_slope', 'mrt_accuracy_facilitation_index']:
        values = vwm_agg[param]
        print(f"{param}: Mean={values.mean():.6f}, SD={values.std():.6f}, Range=[{values.min():.6f}, {values.max():.6f}]")
    
    print(f"\nVVIQ2 total score z: Mean={vwm_agg['vviq2_total_score_z'].mean():.3f}, SD={vwm_agg['vviq2_total_score_z'].std():.3f}")
    
    return vwm_agg

def compute_correlation_with_ci(x, y):
    """
    Compute Pearson correlation with 95% confidence interval.
    
    Parameters:
    x (array-like): First variable
    y (array-like): Second variable
    
    Returns:
    tuple: (correlation, ci_lower, ci_upper, p_value, n_pairs)
    """
    # Remove NaN pairs
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = np.array(x)[mask]
    y_clean = np.array(y)[mask]
    n_pairs = len(x_clean)
    
    if n_pairs < 3:
        return np.nan, np.nan, np.nan, np.nan, n_pairs
    
    # Compute correlation
    r, p_value = pearsonr(x_clean, y_clean)
    
    # Compute 95% CI using Fisher's z-transformation
    if abs(r) >= 0.999:  # Handle extreme correlations
        ci_lower, ci_upper = np.nan, np.nan
    else:
        z = np.arctanh(r)  # Fisher's z-transformation
        se_z = 1 / np.sqrt(n_pairs - 3)
        z_ci = 1.96 * se_z
        ci_lower = np.tanh(z - z_ci)
        ci_upper = np.tanh(z + z_ci)
    
    return r, ci_lower, ci_upper, p_value, n_pairs

def compute_cross_task_correlations(agg_data):
    """
    Compute correlations between VWM DoG parameters and MRT facilitation indices.
    
    Parameters:
    agg_data (pd.DataFrame): Aggregated participant-level data
    
    Returns:
    pd.DataFrame: Correlation results
    """
    print("\n" + "=" * 60)
    print("COMPUTING CROSS-TASK CORRELATIONS")
    print("=" * 60)
    
    vwm_params = ['vwm_mean_amplitude', 'vwm_mean_width', 'vwm_mean_zero_crossing']
    mrt_indices = ['mrt_rt_facilitation_slope', 'mrt_accuracy_facilitation_index']
    
    correlation_results = []
    
    print("Computing Pearson correlations between VWM DoG parameters and MRT facilitation indices...")
    
    for vwm_param in vwm_params:
        for mrt_index in mrt_indices:
            print(f"\nAnalyzing correlation: {vwm_param} vs {mrt_index}")
            
            x = agg_data[vwm_param]
            y = agg_data[mrt_index]
            
            r, ci_lower, ci_upper, p_value, n_pairs = compute_correlation_with_ci(x, y)
            
            print(f"  r = {r:.4f}, 95% CI = [{ci_lower:.4f}, {ci_upper:.4f}], p = {p_value:.4f}, n = {n_pairs}")
            
            correlation_results.append({
                'vwm_parameter': vwm_param,
                'mrt_index': mrt_index,
                'correlation_r': r,
                'ci_lower': ci_lower,
                'ci_upper': ci_upper,
                'p_value': p_value,
                'p_value_fdr_corrected': np.nan,  # Will be filled later
                'significant_fdr': False,  # Will be filled later
                'n_pairs': n_pairs
            })
    
    correlation_df = pd.DataFrame(correlation_results)
    
    print(f"\nCorrelation matrix computed with {len(correlation_df)} correlations")
    print("All correlations:")
    print(correlation_df[['vwm_parameter', 'mrt_index', 'correlation_r', 'p_value']])
    
    return correlation_df

def apply_fdr_correction(p_values):
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Parameters:
    p_values (array-like): Uncorrected p-values
    
    Returns:
    tuple: (corrected_p_values, significant_mask)
    """
    p_values = np.array(p_values)
    n = len(p_values)
    
    # Sort p-values and get original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Apply Benjamini-Hochberg procedure
    corrected_p = np.zeros(n)
    for i in range(n-1, -1, -1):
        if i == n-1:
            corrected_p[sorted_indices[i]] = sorted_p[i]
        else:
            corrected_p[sorted_indices[i]] = min(sorted_p[i] * n / (i + 1), 
                                               corrected_p[sorted_indices[i + 1]])
    
    # Determine significance at q = 0.05
    significant = corrected_p <= 0.05
    
    return corrected_p, significant

def test_moderation_effects(agg_data, correlation_df):
    """
    Test moderation effects of VVIQ2 scores on significant correlations using R.
    
    Parameters:
    agg_data (pd.DataFrame): Aggregated participant-level data
    correlation_df (pd.DataFrame): Correlation results with FDR correction
    
    Returns:
    pd.DataFrame: Moderation results
    """
    print("\n" + "=" * 60)
    print("TESTING MODERATION EFFECTS")
    print("=" * 60)
    
    if not R_AVAILABLE:
        print("R interface not available, skipping moderation analyses")
        return pd.DataFrame()
    
    # Get significant correlations
    significant_corrs = correlation_df[correlation_df['significant_fdr'] == True]
    print(f"Found {len(significant_corrs)} significant correlations for moderation testing")
    
    if len(significant_corrs) == 0:
        print("No significant correlations found, skipping moderation analyses")
        return pd.DataFrame()
    
    try:
        # Import R packages
        base = importr('base')
        stats = importr('stats')
        
        moderation_results = []
        
        for _, row in significant_corrs.iterrows():
            vwm_param = row['vwm_parameter']
            mrt_index = row['mrt_index']
            
            print(f"\nTesting moderation for: {vwm_param} ~ {mrt_index}")
            
            # Prepare data for R
            model_data = agg_data[[vwm_param, mrt_index, 'vviq2_total_score_z']].dropna()
            print(f"Sample size for moderation model: {len(model_data)}")
            
            if len(model_data) < 10:
                print("Insufficient sample size for moderation model")
                continue
            
            # Convert to R dataframe
            r_data = pandas2ri.py2rpy(model_data)
            
            # Fit moderation model
            formula_str = f"{mrt_index} ~ {vwm_param} + vviq2_total_score_z + {vwm_param}:vviq2_total_score_z"
            print(f"Model formula: {formula_str}")
            
            formula = Formula(formula_str)
            model = stats.lm(formula, data=r_data)
            summary_result = base.summary(model)
            
            # Extract coefficients
            coefficients = summary_result.rx2('coefficients')
            coef_names = list(coefficients.rownames)
            
            # Extract model R-squared
            r_squared = summary_result.rx2('r.squared')[0]
            
            # Process each coefficient
            for i, coef_name in enumerate(coef_names):
                estimate = coefficients[i, 0]
                std_error = coefficients[i, 1] 
                t_value = coefficients[i, 2]
                p_value = coefficients[i, 3]
                
                # Calculate 95% CI
                ci_lower = estimate - 1.96 * std_error
                ci_upper = estimate + 1.96 * std_error
                
                # Determine effect type
                if coef_name == '(Intercept)':
                    effect_type = 'intercept'
                elif ':' in coef_name:
                    effect_type = 'interaction'
                elif 'vviq2_total_score_z' in coef_name:
                    effect_type = 'vviq2_main'
                else:
                    effect_type = 'vwm_main'
                
                # Calculate standardized estimate (for non-intercept terms)
                if effect_type != 'intercept':
                    # Standardize by multiplying by SD of predictor and dividing by SD of outcome
                    if effect_type == 'interaction':
                        # For interaction, use product of SDs
                        sd_pred = model_data[vwm_param].std() * model_data['vviq2_total_score_z'].std()
                    elif effect_type == 'vviq2_main':
                        sd_pred = model_data['vviq2_total_score_z'].std()
                    else:  # vwm_main
                        sd_pred = model_data[vwm_param].std()
                    
                    sd_outcome = model_data[mrt_index].std()
                    standardized_estimate = estimate * sd_pred / sd_outcome
                else:
                    standardized_estimate = np.nan
                
                moderation_results.append({
                    'vwm_parameter': vwm_param,
                    'mrt_index': mrt_index,
                    'effect_type': effect_type,
                    'estimate': estimate,
                    'std_error': std_error,
                    'standardized_estimate': standardized_estimate,
                    'ci_lower': ci_lower,
                    'ci_upper': ci_upper,
                    't_value': t_value,
                    'p_value': p_value,
                    'p_value_fdr_corrected': np.nan,  # Will be filled later
                    'significant_fdr': False,  # Will be filled later
                    'model_r_squared': r_squared
                })
                
                print(f"  {effect_type}: β = {estimate:.6f}, SE = {std_error:.6f}, t = {t_value:.3f}, p = {p_value:.4f}")
        
        moderation_df = pd.DataFrame(moderation_results)
        
        if len(moderation_df) > 0:
            print(f"\nCompleted {len(moderation_df)} moderation tests")
            print("Moderation results summary:")
            print(moderation_df[['vwm_parameter', 'mrt_index', 'effect_type', 'estimate', 'p_value']])
        
        return moderation_df
        
    except Exception as e:
        print(f"Error in moderation analysis: {e}")
        return pd.DataFrame()

def compute_composite_scores(agg_data):
    """
    Compute composite scores for domain-general temporal integration.
    
    Parameters:
    agg_data (pd.DataFrame): Aggregated participant-level data
    
    Returns:
    tuple: (composite_vwm, composite_mrt, correlation_result, agg_data)
    """
    print("\n" + "=" * 60)
    print("COMPUTING COMPOSITE SCORES")
    print("=" * 60)
    
    print("Computing composite scores for domain-general temporal integration...")
    
    # VWM composite: weighted average of amplitude and width
    amplitude = agg_data['vwm_mean_amplitude'].values
    width = agg_data['vwm_mean_width'].values
    
    # Calculate weights as inverse variance
    var_amplitude = np.var(amplitude, ddof=1)
    var_width = np.var(width, ddof=1)
    
    weight_amplitude = 1 / var_amplitude if var_amplitude > 0 else 1
    weight_width = 1 / var_width if var_width > 0 else 1
    
    total_weight_vwm = weight_amplitude + weight_width
    
    composite_vwm = (weight_amplitude * amplitude + weight_width * width) / total_weight_vwm
    
    print(f"VWM composite weights: amplitude = {weight_amplitude:.4f}, width = {weight_width:.4f}")
    print(f"VWM composite score: Mean = {np.mean(composite_vwm):.4f}, SD = {np.std(composite_vwm):.4f}")
    
    # MRT composite: weighted average of RT and accuracy facilitation
    rt_facilitation = agg_data['mrt_rt_facilitation_slope'].values
    acc_facilitation = agg_data['mrt_accuracy_facilitation_index'].values
    
    # Calculate weights as inverse variance
    var_rt = np.var(rt_facilitation, ddof=1)
    var_acc = np.var(acc_facilitation, ddof=1)
    
    weight_rt = 1 / var_rt if var_rt > 0 else 1
    weight_acc = 1 / var_acc if var_acc > 0 else 1
    
    total_weight_mrt = weight_rt + weight_acc
    
    composite_mrt = (weight_rt * rt_facilitation + weight_acc * acc_facilitation) / total_weight_mrt
    
    print(f"MRT composite weights: rt_facilitation = {weight_rt:.4f}, accuracy_facilitation = {weight_acc:.4f}")
    print(f"MRT composite score: Mean = {np.mean(composite_mrt):.6f}, SD = {np.std(composite_mrt):.6f}")
    
    # Test correlation between composite scores
    r, ci_lower, ci_upper, p_value, n_pairs = compute_correlation_with_ci(composite_vwm, composite_mrt)
    
    print(f"\nComposite score correlation:")
    print(f"  r = {r:.4f}, 95% CI = [{ci_lower:.4f}, {ci_upper:.4f}], p = {p_value:.4f}, n = {n_pairs}")
    
    correlation_result = {
        'vwm_parameter': 'composite_vwm',
        'mrt_index': 'composite_mrt', 
        'correlation_r': r,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'p_value': p_value,
        'n_pairs': n_pairs
    }
    
    # Add composite scores to the aggregated data
    agg_data['composite_vwm'] = composite_vwm
    agg_data['composite_mrt'] = composite_mrt

    return composite_vwm, composite_mrt, correlation_result, agg_data

def validate_correlation_assumptions(agg_data, correlation_df):
    """
    Validate assumptions for correlation analyses.
    
    Parameters:
    agg_data (pd.DataFrame): Aggregated participant-level data
    correlation_df (pd.DataFrame): Correlation results
    
    Returns:
    dict: Validation results
    """
    print("\n" + "=" * 60)
    print("VALIDATING CORRELATION ASSUMPTIONS")
    print("=" * 60)
    
    validation_results = {}
    
    # Test normality for each variable
    print("Testing normality assumptions (Shapiro-Wilk test):")
    variables = ['vwm_mean_amplitude', 'vwm_mean_width', 'vwm_mean_zero_crossing',
                'mrt_rt_facilitation_slope', 'mrt_accuracy_facilitation_index', 'vviq2_total_score_z',
                'composite_vwm', 'composite_mrt']

    for var in variables:
        if var in agg_data.columns:  # Check if column exists
            data = agg_data[var].dropna()
            if len(data) >= 3:
                statistic, p_value = stats.shapiro(data)
                validation_results[f'{var}_normality_p'] = p_value
                print(f"  {var}: W = {statistic:.4f}, p = {p_value:.4f}")
            else:
                validation_results[f'{var}_normality_p'] = np.nan
                print(f"  {var}: Insufficient data for normality test")
        else:
            print(f"  {var}: Column not found in dataset")
    
    # Check for outliers using Cook's distance
    print("\nChecking for influential outliers using Cook's distance:")
    for _, row in correlation_df.iterrows():
        vwm_param = row['vwm_parameter']
        mrt_index = row['mrt_index']
        
        if vwm_param in agg_data.columns and mrt_index in agg_data.columns:
            x = agg_data[vwm_param].values
            y = agg_data[mrt_index].values
            
            # Remove NaN pairs
            mask = ~(np.isnan(x) | np.isnan(y))
            x_clean = x[mask]
            y_clean = y[mask]
            
            if len(x_clean) >= 10:
                try:
                    # Calculate Cook's distance using linear regression
                    X_matrix = np.column_stack([np.ones(len(x_clean)), x_clean])
                    
                    # Fit using normal equations
                    XtX_inv = np.linalg.inv(X_matrix.T @ X_matrix)
                    beta = XtX_inv @ X_matrix.T @ y_clean
                    y_pred = X_matrix @ beta
                    
                    # Calculate residuals and MSE
                    residuals = y_clean - y_pred
                    mse = np.sum(residuals**2) / (len(x_clean) - 2)
                    
                    # Calculate leverage (hat values)
                    H = X_matrix @ XtX_inv @ X_matrix.T
                    leverage = np.diag(H)
                    
                    # Calculate Cook's distance
                    p = 2  # number of parameters (intercept + slope)
                    cooks_d = (residuals**2 / (p * mse)) * (leverage / (1 - leverage)**2)
                    
                    # Count outliers (Cook's D > 4/n threshold)
                    threshold = 4 / len(x_clean)
                    outliers = np.sum(cooks_d > threshold)
                    
                    validation_results[f'{vwm_param}_{mrt_index}_cooks_outliers'] = outliers
                    print(f"  {vwm_param} vs {mrt_index}: {outliers} outliers (Cook's D > {threshold:.4f})")
                except np.linalg.LinAlgError:
                    print(f"  {vwm_param} vs {mrt_index}: Unable to compute Cook's distance (singular matrix)")
            else:
                print(f"  {vwm_param} vs {mrt_index}: Insufficient data for outlier detection")
        else:
            print(f"  {vwm_param} vs {mrt_index}: Variables not found in dataset")

    # Add notes about assumptions
    print("\nAssumption validation notes:")
    print("  Normality: Univariate Shapiro-Wilk tests performed. True bivariate normality")
    print("  would require specialized tests (e.g., Mardia's, Henze-Zirkler).")
    print("  Linearity: Visual inspection of scatterplots is recommended to verify")
    print("  linearity assumptions for each correlation pair.")
    print("  Outliers: Cook's distance used with threshold of 4/n per observation.")
    
    return validation_results

def save_results(correlation_df, moderation_df, final_sample_df, timestamp):
    """
    Save all results to CSV files.
    
    Parameters:
    correlation_df (pd.DataFrame): Correlation results
    moderation_df (pd.DataFrame): Moderation results
    final_sample_df (pd.DataFrame): Final sample data
    timestamp (str): Timestamp for filenames
    """
    print("\n" + "=" * 60)
    print("SAVING RESULTS")
    print("=" * 60)
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Save correlation results
    corr_filename = f'outputs/cross_task_correlations_{timestamp}.csv'
    correlation_df.to_csv(corr_filename, index=False)
    print(f"Correlation results saved to: {corr_filename}")
    print(f"Correlation results shape: {correlation_df.shape}")
    
    # Save moderation results - always create file even if empty
    mod_filename = f'outputs/cross_task_moderation_results_{timestamp}.csv'
    if len(moderation_df) > 0:
        moderation_df.to_csv(mod_filename, index=False)
        print(f"Moderation results saved to: {mod_filename}")
        print(f"Moderation results shape: {moderation_df.shape}")
    else:
        # Create empty DataFrame with required columns
        empty_mod_df = pd.DataFrame(columns=['vwm_parameter', 'mrt_index', 'effect_type', 'estimate', 'std_error', 'standardized_estimate', 'ci_lower', 'ci_upper', 't_value', 'p_value', 'p_value_fdr_corrected', 'significant_fdr', 'model_r_squared'])
        empty_mod_df.to_csv(mod_filename, index=False)
        print(f"Empty moderation results file saved to: {mod_filename}")
        print(f"Moderation results shape: {empty_mod_df.shape}")
    
    # Save final sample with only required columns
    sample_filename = f'outputs/cross_task_final_sample_{timestamp}.csv'
    required_final_sample_cols = [
        'participantId', 'vwm_mean_amplitude', 'vwm_mean_width', 'vwm_mean_zero_crossing',
        'mrt_rt_facilitation_slope', 'mrt_accuracy_facilitation_index',
        'vviq2_total_score_z', 'included_final_analysis'
    ]
    # Select only required columns that exist
    final_sample_df_to_save = final_sample_df[[col for col in required_final_sample_cols if col in final_sample_df.columns]]
    final_sample_df_to_save.to_csv(sample_filename, index=False)
    print(f"Final sample saved to: {sample_filename}")
    print(f"Final sample shape: {final_sample_df_to_save.shape}")

def main():
    """
    Main function to execute cross-task correlation analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("CROSS-TASK CORRELATION ANALYSIS")
        print("=" * 80)
        
        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"Analysis timestamp: {timestamp}")
        
        # Load and validate data
        vwm_data, mrt_data, vviq_data = load_and_validate_data()
        if vwm_data is None:
            print("ERROR: Failed to load input data")
            return 1
        
        # Merge datasets
        merged_data = merge_datasets(vwm_data, mrt_data, vviq_data)
        if len(merged_data) == 0:
            print("ERROR: No participants remaining after merge")
            return 1
        
        # Aggregate VWM parameters
        agg_data = aggregate_vwm_parameters(merged_data)
        
        print(f"\nFinal analyzable sample size: {len(agg_data)} participants")
        
        # Compute cross-task correlations
        correlation_df = compute_cross_task_correlations(agg_data)
        
        # Compute composite scores
        composite_vwm, composite_mrt, composite_corr, agg_data = compute_composite_scores(agg_data)
        
        # Add composite correlation to results
        composite_row = pd.DataFrame([composite_corr])
        correlation_df = pd.concat([correlation_df, composite_row], ignore_index=True)
        
        # Apply FDR correction to all correlations
        print("\n" + "=" * 60)
        print("APPLYING FDR CORRECTION")
        print("=" * 60)
        
        p_values = correlation_df['p_value'].values
        corrected_p, significant = apply_fdr_correction(p_values)
        
        correlation_df['p_value_fdr_corrected'] = corrected_p
        correlation_df['significant_fdr'] = significant
        
        print("FDR correction results:")
        for i, row in correlation_df.iterrows():
            print(f"  {row['vwm_parameter']} vs {row['mrt_index']}: p = {row['p_value']:.4f}, p_FDR = {row['p_value_fdr_corrected']:.4f}, significant = {row['significant_fdr']}")
        
        # Test moderation effects
        moderation_df = test_moderation_effects(agg_data, correlation_df)
        
        # Apply FDR correction to moderation results if any
        if len(moderation_df) > 0:
            print("\nApplying FDR correction to moderation results...")
            
            # Get only interaction p-values for FDR correction
            interaction_mask = moderation_df['effect_type'] == 'interaction'
            interaction_p_values = moderation_df[interaction_mask]['p_value'].values
            
            # Get raw correlation p-values
            raw_correlation_p_values = correlation_df['p_value'].values
            
            # Combine correlation and interaction p-values for FDR
            all_p_values_for_fdr = list(raw_correlation_p_values) + list(interaction_p_values)
            
            # Apply FDR correction to combined tests
            all_corrected_p, all_significant = apply_fdr_correction(all_p_values_for_fdr)
            
            # Update correlation results
            n_corr = len(raw_correlation_p_values)
            correlation_df['p_value_fdr_corrected'] = all_corrected_p[:n_corr]
            correlation_df['significant_fdr'] = all_significant[:n_corr]
            
            # Initialize moderation FDR columns
            moderation_df['p_value_fdr_corrected'] = np.nan
            moderation_df['significant_fdr'] = False
            
            # Update only interaction effects with FDR correction
            if len(interaction_p_values) > 0:
                interaction_indices = moderation_df[interaction_mask].index
                moderation_df.loc[interaction_indices, 'p_value_fdr_corrected'] = all_corrected_p[n_corr:]
                moderation_df.loc[interaction_indices, 'significant_fdr'] = all_significant[n_corr:]
            
            print("Updated FDR correction results including moderation tests:")
            significant_interactions = moderation_df[moderation_df['effect_type'] == 'interaction']
            for _, row in significant_interactions.iterrows():
                print(f"  {row['vwm_parameter']} x VVIQ2 -> {row['mrt_index']}: p = {row['p_value']:.4f}, p_FDR = {row['p_value_fdr_corrected']:.4f}, significant = {row['significant_fdr']}")
        
        # Validate correlation assumptions
        validation_results = validate_correlation_assumptions(agg_data, correlation_df)
        
        # Save results
        save_results(correlation_df, moderation_df, agg_data, timestamp)
        
        # Final summary
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)
        
        print(f"Final sample size: {len(agg_data)} participants")
        print(f"Number of correlations tested: {len(correlation_df)}")
        print(f"Number of significant correlations (FDR-corrected): {sum(correlation_df['significant_fdr'])}")
        
        if len(moderation_df) > 0:
            print(f"Number of moderation tests: {len(moderation_df)}")
            print(f"Number of significant interactions (FDR-corrected): {sum((moderation_df['effect_type'] == 'interaction') & moderation_df['significant_fdr'])}")
        
        print("\nSignificant correlations:")
        sig_corrs = correlation_df[correlation_df['significant_fdr'] == True]
        for _, row in sig_corrs.iterrows():
            print(f"  {row['vwm_parameter']} vs {row['mrt_index']}: r = {row['correlation_r']:.4f}, p_FDR = {row['p_value_fdr_corrected']:.4f}")
        
        if len(moderation_df) > 0:
            print("\nSignificant moderation effects:")
            sig_mods = moderation_df[(moderation_df['effect_type'] == 'interaction') & (moderation_df['significant_fdr'] == True)]
            for _, row in sig_mods.iterrows():
                print(f"  {row['vwm_parameter']} x VVIQ2 -> {row['mrt_index']}: β = {row['standardized_estimate']:.4f}, p_FDR = {row['p_value_fdr_corrected']:.4f}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
