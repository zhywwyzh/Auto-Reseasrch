#!/usr/bin/env python3
"""
Standardized Effect Size Analysis and Sensitivity Testing Script

This script performs comprehensive effect size calculations and sensitivity analyses
for mixed-effects models and robust regression results from experimental data.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

import statsmodels.api as sm
import statsmodels.formula.api as smf

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern with <TIMESTAMP> placeholder
        
    Returns:
    --------
    str or None
        Path to the most recent file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    files = glob.glob(search_pattern)
    
    if not files:
        print(f"No files found matching pattern: {search_pattern}")
        return None
        
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Using latest file: {latest_file}")
    return latest_file

def load_input_data():
    """
    Load all required input CSV files.
    
    Returns:
    --------
    tuple
        Tuple containing all loaded dataframes
    """
    print("=== LOADING INPUT DATA ===")
    
    # Define file patterns
    file_patterns = {
        'mrt_results': 'outputs/mrt_mixed_effects_results_<TIMESTAMP>.csv',
        'vviq2_results': 'outputs/vviq2_robust_regression_results_<TIMESTAMP>.csv',
        'experimental_data': 'outputs/cleaned_experimental_data_<TIMESTAMP>.csv',
        'vwm_params': 'outputs/vwm_mixture_model_parameters_<TIMESTAMP>.csv',
        'behavioral_controls': 'outputs/behavioral_control_metrics_<TIMESTAMP>.csv',
        'vviq2_scores': 'outputs/vviq2_scores_processed_<TIMESTAMP>.csv'
    }
    
    dataframes = {}
    
    for name, pattern in file_patterns.items():
        print(f"\nLoading {name}...")
        filepath = find_latest_file(pattern)
        
        if filepath is None:
            print(f"ERROR: Could not find file for {name}")
            return None
            
        try:
            df = pd.read_csv(filepath)
            print(f"Loaded {name}: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            dataframes[name] = df
            
        except Exception as e:
            print(f"ERROR loading {name}: {e}")
            return None
    
    return (dataframes['mrt_results'], dataframes['vviq2_results'], 
            dataframes['experimental_data'], dataframes['vwm_params'],
            dataframes['behavioral_controls'], dataframes['vviq2_scores'])

def calculate_standardized_effects(mrt_results, vviq2_results, experimental_data, 
                                 vwm_params, behavioral_controls, vviq2_scores):
    """
    Calculate standardized effect sizes for mixed-effects models and regression analyses.
    
    Parameters:
    -----------
    mrt_results : pd.DataFrame
        Mixed-effects model results
    vviq2_results : pd.DataFrame
        VVIQ2 robust regression results
    experimental_data : pd.DataFrame
        Raw experimental data
    vwm_params : pd.DataFrame
        VWM mixture model parameters
    behavioral_controls : pd.DataFrame
        Behavioral control metrics
    vviq2_scores : pd.DataFrame
        VVIQ2 scores
        
    Returns:
    --------
    pd.DataFrame
        Standardized effect sizes
    """
    print("\n=== CALCULATING STANDARDIZED EFFECT SIZES ===")
    
    # Merge datasets to calculate standard deviations
    print("\nMerging datasets for SD calculations...")
    
    # Start with experimental data for MRT
    mrt_test_data = experimental_data[
        (experimental_data['table'] == 'mrt_test') & 
        (experimental_data['isPractice'] == False)
    ].copy()
    
    print(f"MRT test trials: {len(mrt_test_data)}")
    print(f"Unique participants in MRT data: {mrt_test_data['participantId'].nunique()}")
    
    # Merge with VWM parameters
    merged_data = mrt_test_data.merge(vwm_params, on='participantId', how='inner')
    print(f"After merging with VWM params: {len(merged_data)} trials, {merged_data['participantId'].nunique()} participants")
    
    # Merge with behavioral controls
    merged_data = merged_data.merge(behavioral_controls, on='participantId', how='inner')
    print(f"After merging with controls: {len(merged_data)} trials, {merged_data['participantId'].nunique()} participants")
    
    # Calculate standard deviations for predictors and outcomes
    print("\nCalculating standard deviations...")
    
    # For MRT accuracy (binary outcome, use theoretical SD)
    accuracy_sd = 0.5  # theoretical SD for binary outcome with balanced classes
    
    # For MRT reaction time
    rt_sd = merged_data['MRT_rt_ms'].std()
    print(f"MRT RT standard deviation: {rt_sd:.2f} ms")
    
    # For predictors
    kappa_sd = merged_data['kappa_concentration'].std()
    print(f"Kappa concentration standard deviation: {kappa_sd:.4f}")
    
    # Get unique angle values
    angle_values = merged_data['MRT_angle_degrees'].unique()
    print(f"MRT angle values: {sorted(angle_values)}")
    
    # Calculate CV and error SDs
    cv_sd = behavioral_controls['mrt_rt_coefficient_variation'].std()
    error_sd = behavioral_controls['mean_vwm_absolute_error'].std()
    
    print(f"CV standard deviation: {cv_sd:.4f}")
    print(f"VWM error standard deviation: {error_sd:.4f}")
    
    # For VVIQ2 analysis - merge VVIQ2 scores with VWM params and controls
    vviq2_merged = vviq2_scores.merge(vwm_params, on='participantId', how='inner')
    vviq2_merged = vviq2_merged.merge(behavioral_controls, on='participantId', how='inner')
    
    vviq2_sd = vviq2_merged['vviq2_total_score'].std()
    print(f"VVIQ2 total score standard deviation: {vviq2_sd:.2f}")
    
    # Initialize results list
    standardized_results = []
    
    # Process MRT mixed-effects results
    print("\nProcessing MRT mixed-effects results...")
    for _, row in mrt_results.iterrows():
        model_name = row['model_name']
        effect_name = row['effect_name']
        coefficient = row['coefficient']
        z_value = row['z_value']
        p_value = row['p_value']
        conf_lower = row['conf_int_lower']
        conf_upper = row['conf_int_upper']
        
        print(f"Processing {model_name} - {effect_name}")
        
        # Determine analysis type and outcome SD
        if 'Accuracy' in model_name:
            analysis_type = 'MRT_Accuracy'
            outcome_sd = accuracy_sd
        else:
            analysis_type = 'MRT_RT'
            outcome_sd = rt_sd
            
        # Determine predictor SD based on effect name
        predictor_sd = 1.0  # default for categorical variables
        
        if 'kappa_concentration' in effect_name:
            predictor_sd = kappa_sd
        elif 'mrt_rt_coefficient_variation' in effect_name:
            predictor_sd = cv_sd
        elif 'mean_vwm_absolute_error' in effect_name:
            predictor_sd = error_sd
            
        # Calculate standardized beta
        standardized_beta = coefficient * (predictor_sd / outcome_sd)
        
        # Calculate partial eta squared using z/t value
        # For mixed effects: η²p = t² / (t² + df)
        # Using conservative df estimate based on model type
        if 'Accuracy' in model_name:
            df_estimate = len(merged_data) - 10  # conservative estimate
        else:
            df_estimate = len(merged_data) - 10
            
        partial_eta_sq = (z_value ** 2) / ((z_value ** 2) + df_estimate)
        
        # Calculate standardized confidence intervals
        conf_range = conf_upper - conf_lower
        std_conf_range = conf_range * (predictor_sd / outcome_sd)
        conf_lower_std = standardized_beta - (std_conf_range / 2)
        conf_upper_std = standardized_beta + (std_conf_range / 2)
        
        # Cohen's interpretation
        abs_beta = abs(standardized_beta)
        if abs_beta < 0.1:
            cohen_interp = 'negligible'
        elif abs_beta < 0.3:
            cohen_interp = 'small'
        elif abs_beta < 0.5:
            cohen_interp = 'medium'
        else:
            cohen_interp = 'large'
            
        # Determine effect size magnitude category
        if abs_beta < 0.2:
            magnitude = 'small'
        elif abs_beta < 0.5:
            magnitude = 'medium'
        else:
            magnitude = 'large'
            
        standardized_results.append({
            'analysis_type': analysis_type,
            'model_name': model_name,
            'effect_name': effect_name,
            'raw_coefficient': coefficient,
            'standardized_beta': standardized_beta,
            'effect_size_magnitude': magnitude,
            'conf_int_lower_std': conf_lower_std,
            'conf_int_upper_std': conf_upper_std,
            'partial_eta_squared': partial_eta_sq,
            'cohen_interpretation': cohen_interp
        })
        
        print(f"  Raw coeff: {coefficient:.4f}, Std beta: {standardized_beta:.4f}, Magnitude: {magnitude}")
    
    # Process VVIQ2 robust regression results
    print("\nProcessing VVIQ2 robust regression results...")
    for _, row in vviq2_results.iterrows():
        model_name = row['model_name']
        variable_name = row['variable_name']
        coefficient = row['coefficient']
        t_statistic = row['t_statistic']
        p_value = row['p_value']
        conf_lower = row['conf_int_lower']
        conf_upper = row['conf_int_upper']
        n_obs = row['n_observations']
        
        print(f"Processing VVIQ2 - {variable_name}")
        
        # Determine predictor SD
        predictor_sd = 1.0  # default
        if 'kappa_concentration' in variable_name:
            predictor_sd = kappa_sd
        elif 'mrt_rt_coefficient_variation' in variable_name:
            predictor_sd = cv_sd
        elif 'mean_vwm_absolute_error' in variable_name:
            predictor_sd = error_sd
            
        # Calculate standardized beta
        standardized_beta = coefficient * (predictor_sd / vviq2_sd)
        
        # Calculate partial eta squared
        df_estimate = n_obs - 5  # conservative estimate
        partial_eta_sq = (t_statistic ** 2) / ((t_statistic ** 2) + df_estimate)
        
        # Calculate standardized confidence intervals
        conf_range = conf_upper - conf_lower
        std_conf_range = conf_range * (predictor_sd / vviq2_sd)
        conf_lower_std = standardized_beta - (std_conf_range / 2)
        conf_upper_std = standardized_beta + (std_conf_range / 2)
        
        # Cohen's interpretation
        abs_beta = abs(standardized_beta)
        if abs_beta < 0.1:
            cohen_interp = 'negligible'
        elif abs_beta < 0.3:
            cohen_interp = 'small'
        elif abs_beta < 0.5:
            cohen_interp = 'medium'
        else:
            cohen_interp = 'large'
            
        # Effect size magnitude
        if abs_beta < 0.2:
            magnitude = 'small'
        elif abs_beta < 0.5:
            magnitude = 'medium'
        else:
            magnitude = 'large'
            
        standardized_results.append({
            'analysis_type': 'VVIQ2_Regression',
            'model_name': model_name,
            'effect_name': variable_name,
            'raw_coefficient': coefficient,
            'standardized_beta': standardized_beta,
            'effect_size_magnitude': magnitude,
            'conf_int_lower_std': conf_lower_std,
            'conf_int_upper_std': conf_upper_std,
            'partial_eta_squared': partial_eta_sq,
            'cohen_interpretation': cohen_interp
        })
        
        print(f"  Raw coeff: {coefficient:.4f}, Std beta: {standardized_beta:.4f}, Magnitude: {magnitude}")
    
    results_df = pd.DataFrame(standardized_results)
    print(f"\nStandardized effects calculated: {len(results_df)} effects")
    
    return results_df

def calculate_cooks_distance(merged_data, model_type):
    """
    Calculate Cook's distance for outlier detection using statsmodels.
    
    Parameters:
    -----------
    merged_data : pd.DataFrame
        Merged analysis dataset
    model_type : str
        Type of model ('accuracy', 'rt', 'vviq2')
        
    Returns:
    --------
    pd.DataFrame
        Cook's distances by participant
    """
    print(f"\nCalculating Cook's distance for {model_type} model...")
    
    try:
        if model_type == 'accuracy':
            # Use a fixed-effects GLM as a proxy for the mixed-effects model
            formula = 'MRT_isCorrect ~ kappa_concentration * C(MRT_angle_degrees) + mean_vwm_absolute_error + mrt_rt_coefficient_variation'
            model = smf.glm(formula=formula, data=merged_data, family=sm.families.Binomial()).fit()
            influence = model.get_influence(observed=False)
            merged_data_copy = merged_data.copy()
            merged_data_copy['cooks_d'] = influence.cooks_distance[0]
            cooks_df = merged_data_copy.groupby('participantId')['cooks_d'].mean().reset_index()
        
        elif model_type == 'rt':
            # Use OLS as a proxy for the linear mixed-effects model
            rt_data = merged_data[merged_data['MRT_isCorrect'] == True].copy()
            if len(rt_data) == 0:
                print("WARNING: No correct trials found for RT analysis")
                return pd.DataFrame(columns=['participantId', 'cooks_distance', 'analysis_type'])
            
            formula = 'MRT_rt_ms ~ kappa_concentration * C(MRT_angle_degrees) + mean_vwm_absolute_error + mrt_rt_coefficient_variation'
            model = smf.ols(formula=formula, data=rt_data).fit()
            influence = model.get_influence()
            rt_data['cooks_d'] = influence.cooks_distance[0]
            cooks_df = rt_data.groupby('participantId')['cooks_d'].mean().reset_index()

        else:  # vviq2
            # Use OLS as proxy for RLM to get influence diagnostics
            formula = 'vviq2_total_score ~ kappa_concentration + mrt_rt_coefficient_variation + mean_vwm_absolute_error'
            model = smf.ols(formula=formula, data=merged_data).fit()
            influence = model.get_influence()
            merged_data_copy = merged_data.copy()
            merged_data_copy['cooks_d'] = influence.cooks_distance[0]
            # Data is already at participant level, so just format the output
            cooks_df = merged_data_copy[['participantId', 'cooks_d']].copy()

        cooks_df = cooks_df.rename(columns={'cooks_d': 'cooks_distance'})
        cooks_df['analysis_type'] = model_type
        
        print(f"Cook's distance calculated for {len(cooks_df)} participants")
        return cooks_df
        
    except Exception as e:
        print(f"ERROR calculating Cook's distance for {model_type}: {e}")
        # Return simplified calculation as fallback
        participants = merged_data['participantId'].unique()
        cooks_distances = []
        
        for participant in participants:
            participant_data = merged_data[merged_data['participantId'] == participant]
            
            if model_type == 'accuracy':
                mean_acc = participant_data['MRT_isCorrect'].mean()
                overall_mean = merged_data['MRT_isCorrect'].mean()
                leverage = abs(mean_acc - overall_mean)
            elif model_type == 'rt':
                mean_rt = participant_data['MRT_rt_ms'].mean()
                overall_mean = merged_data['MRT_rt_ms'].mean()
                leverage = abs(mean_rt - overall_mean) / merged_data['MRT_rt_ms'].std()
            else:  # vviq2
                kappa = participant_data['kappa_concentration'].iloc[0] if len(participant_data) > 0 else 0
                overall_mean = merged_data['kappa_concentration'].mean()
                leverage = abs(kappa - overall_mean) / merged_data['kappa_concentration'].std()
            
            cooks_distances.append({
                'participantId': participant,
                'cooks_distance': leverage,
                'analysis_type': model_type
            })
        
        return pd.DataFrame(cooks_distances)

def perform_sensitivity_analysis(experimental_data, vwm_params, behavioral_controls, vviq2_scores):
    """
    Perform sensitivity analysis using Cook's distance to identify outliers.
    
    Parameters:
    -----------
    experimental_data : pd.DataFrame
        Raw experimental data
    vwm_params : pd.DataFrame
        VWM mixture model parameters
    behavioral_controls : pd.DataFrame
        Behavioral control metrics
    vviq2_scores : pd.DataFrame
        VVIQ2 scores
        
    Returns:
    --------
    tuple
        (sensitivity_results_df, model_comparison_df)
    """
    print("\n=== PERFORMING SENSITIVITY ANALYSIS ===")
    
    # Merge datasets
    print("Merging datasets for sensitivity analysis...")
    
    # MRT test data
    mrt_test_data = experimental_data[
        (experimental_data['table'] == 'mrt_test') & 
        (experimental_data['isPractice'] == False)
    ].copy()
    
    # Merge all datasets
    merged_data = mrt_test_data.merge(vwm_params, on='participantId', how='inner')
    merged_data = merged_data.merge(behavioral_controls, on='participantId', how='inner')
    
    print(f"Final merged dataset: {len(merged_data)} trials, {merged_data['participantId'].nunique()} participants")
    
    # Calculate Cook's distance for each model type
    all_cooks_distances = []
    
    for model_type in ['accuracy', 'rt', 'vviq2']:
        print(f"\nCalculating Cook's distance for {model_type} model...")
        
        if model_type == 'vviq2':
            # For VVIQ2, use participant-level data
            vviq2_merged = vviq2_scores.merge(vwm_params, on='participantId', how='inner')
            vviq2_merged = vviq2_merged.merge(behavioral_controls, on='participantId', how='inner')
            cooks_df = calculate_cooks_distance(vviq2_merged, model_type)
        else:
            cooks_df = calculate_cooks_distance(merged_data, model_type)
            
        all_cooks_distances.append(cooks_df)
    
    # Combine all Cook's distances
    sensitivity_results = pd.concat(all_cooks_distances, ignore_index=True)
    
    # Calculate threshold: 4/n where n is number of participants
    n_participants = merged_data['participantId'].nunique()
    threshold = 4.0 / n_participants
    
    print(f"\nCook's distance threshold: {threshold:.4f} (4/{n_participants})")
    
    # Flag high leverage participants
    sensitivity_results['high_leverage_flag'] = sensitivity_results['cooks_distance'] > threshold
    sensitivity_results['excluded_from_sensitivity'] = sensitivity_results['high_leverage_flag']
    
    # Report outliers by model type
    for model_type in ['accuracy', 'rt', 'vviq2']:
        model_results = sensitivity_results[sensitivity_results['analysis_type'] == model_type]
        n_outliers = model_results['high_leverage_flag'].sum()
        print(f"{model_type} model outliers: {n_outliers}/{len(model_results)} participants")
        
        if n_outliers > 0:
            outlier_ids = model_results[model_results['high_leverage_flag']]['participantId'].tolist()
            print(f"  Outlier participants: {outlier_ids[:10]}{'...' if len(outlier_ids) > 10 else ''}")
    
    # Create model comparison - implement actual refitting
    print("\nImplementing model comparison with outlier removal...")

    # Define models for re-fitting
    vviq2_merged = vviq2_scores.merge(vwm_params, on='participantId', how='inner')
    vviq2_merged = vviq2_merged.merge(behavioral_controls, on='participantId', how='inner')

    model_definitions = {
        'accuracy': {
            'formula': 'MRT_isCorrect ~ kappa_concentration * C(MRT_angle_degrees) + mean_vwm_absolute_error + mrt_rt_coefficient_variation',
            'model_func': smf.glm,
            'data': merged_data,
            'family': sm.families.Binomial()
        },
        'rt': {
            'formula': 'MRT_rt_ms ~ kappa_concentration * C(MRT_angle_degrees) + mean_vwm_absolute_error + mrt_rt_coefficient_variation',
            'model_func': smf.ols,
            'data': merged_data[merged_data['MRT_isCorrect'] == True].copy()
        },
        'vviq2': {
            'formula': 'vviq2_total_score ~ kappa_concentration + mrt_rt_coefficient_variation + mean_vwm_absolute_error',
            'model_func': smf.rlm,
            'data': vviq2_merged,
            'M': sm.robust.norms.HuberT()
        }
    }

    model_comparison = []

    for model_type, definition in model_definitions.items():
        print(f"\nPerforming sensitivity model comparison for {model_type}...")

        # Fit original model
        try:
            if 'family' in definition:
                original_model = definition['model_func'](formula=definition['formula'],
                                                          data=definition['data'],
                                                          family=definition['family']).fit()
            elif 'M' in definition:
                original_model = definition['model_func'](formula=definition['formula'],
                                                          data=definition['data'],
                                                          M=definition['M']).fit()
            else:
                original_model = definition['model_func'](formula=definition['formula'],
                                                          data=definition['data']).fit()

            # Get outlier IDs for this model type
            outlier_ids = set(sensitivity_results[
                (sensitivity_results['analysis_type'] == model_type) &
                (sensitivity_results['high_leverage_flag'])
            ]['participantId'])

            if not outlier_ids:
                print(f"No outliers for {model_type}, skipping comparison.")
                continue

            print(f"Removing {len(outlier_ids)} outliers for {model_type} model")

            # Create sensitivity dataset without outliers
            sensitivity_data = definition['data'][~definition['data']['participantId'].isin(outlier_ids)]

            # Fit sensitivity model
            if 'family' in definition:
                sensitivity_model = definition['model_func'](formula=definition['formula'],
                                                             data=sensitivity_data,
                                                             family=definition['family']).fit()
            elif 'M' in definition:
                sensitivity_model = definition['model_func'](formula=definition['formula'],
                                                             data=sensitivity_data,
                                                             M=definition['M']).fit()
            else:
                sensitivity_model = definition['model_func'](formula=definition['formula'],
                                                             data=sensitivity_data).fit()

            # Compare coefficients
            original_params = pd.DataFrame({
                'coefficient_original': original_model.params,
                'p_value_original': original_model.pvalues
            })
            sensitivity_params = pd.DataFrame({
                'coefficient_sensitivity': sensitivity_model.params,
                'p_value_sensitivity': sensitivity_model.pvalues
            })

            comp_df = original_params.join(sensitivity_params, how='outer').fillna(np.nan)

            for effect, row in comp_df.iterrows():
                # Calculate percent change
                if pd.isna(row['coefficient_original']) or row['coefficient_original'] == 0:
                    percent_change = np.nan
                else:
                    percent_change = ((row['coefficient_sensitivity'] - row['coefficient_original']) /
                                      abs(row['coefficient_original'])) * 100

                # Determine significance change
                orig_sig = row['p_value_original'] < 0.05 if not pd.isna(row['p_value_original']) else False
                sens_sig = row['p_value_sensitivity'] < 0.05 if not pd.isna(row['p_value_sensitivity']) else False

                if orig_sig and sens_sig:
                    significance_change = 'maintained'
                elif orig_sig and not sens_sig:
                    significance_change = 'lost'
                elif not orig_sig and sens_sig:
                    significance_change = 'gained'
                else:
                    significance_change = 'maintained_non_sig'

                model_comparison.append({
                    'model_name': model_type,
                    'effect_name': effect,
                    'original_coefficient': row['coefficient_original'],
                    'sensitivity_coefficient': row['coefficient_sensitivity'],
                    'percent_change': percent_change,
                    'original_p_value': row['p_value_original'],
                    'sensitivity_p_value': row['p_value_sensitivity'],
                    'significance_change': significance_change
                })

                print(f"  {effect}: {percent_change:.1f}% change, significance {significance_change}")

        except Exception as e:
            print(f"ERROR in model comparison for {model_type}: {e}")
            continue

    model_comparison_df = pd.DataFrame(model_comparison)

    print(f"Sensitivity analysis completed")
    print(f"Sensitivity results: {len(sensitivity_results)} records")
    print(f"Model comparison: {len(model_comparison_df)} comparisons")

    return sensitivity_results, model_comparison_df

def save_results(standardized_effects, sensitivity_results, model_comparison):
    """
    Save all results to CSV files.
    
    Parameters:
    -----------
    standardized_effects : pd.DataFrame
        Standardized effect sizes
    sensitivity_results : pd.DataFrame
        Sensitivity analysis results
    model_comparison : pd.DataFrame
        Model comparison results
    """
    print("\n=== SAVING RESULTS ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save standardized effects
    effects_filename = f"outputs/standardized_effect_sizes_{timestamp}.csv"
    standardized_effects.to_csv(effects_filename, index=False)
    print(f"Saved standardized effects to: {effects_filename}")
    print("Standardized effects columns:", list(standardized_effects.columns))
    print("First 2 rows:")
    print(standardized_effects.head(2))
    
    # Save sensitivity results
    sensitivity_filename = f"outputs/sensitivity_analysis_results_{timestamp}.csv"
    sensitivity_results.to_csv(sensitivity_filename, index=False)
    print(f"Saved sensitivity results to: {sensitivity_filename}")
    print("Sensitivity results columns:", list(sensitivity_results.columns))
    print("First 2 rows:")
    print(sensitivity_results.head(2))
    
    # Save model comparison
    comparison_filename = f"outputs/sensitivity_model_comparison_{timestamp}.csv"
    model_comparison.to_csv(comparison_filename, index=False)
    print(f"Saved model comparison to: {comparison_filename}")
    print("Model comparison columns:", list(model_comparison.columns))
    print("First 2 rows:")
    print(model_comparison.head(2))

def main():
    """
    Main execution function.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("Starting standardized effect size analysis and sensitivity testing...")
        
        # Load input data
        data_tuple = load_input_data()
        if data_tuple is None:
            print("ERROR: Failed to load input data")
            return 1
            
        (mrt_results, vviq2_results, experimental_data, 
         vwm_params, behavioral_controls, vviq2_scores) = data_tuple
        
        # Print key experimental design parameters
        print("\n=== EXPERIMENTAL DESIGN PARAMETERS ===")
        
        # MRT angle values
        mrt_test = experimental_data[
            (experimental_data['table'] == 'mrt_test') & 
            (experimental_data['isPractice'] == False)
        ]
        print(f"MRT trial values (angles): {sorted(mrt_test['MRT_angle_degrees'].unique())}")
        
        # Table types
        print(f"Table types: {sorted(experimental_data['table'].unique())}")
        
        # Practice flags
        print(f"Practice flags: {sorted(experimental_data['isPractice'].unique())}")
        
        # VWM parameter ranges
        print(f"Kappa concentration range: {vwm_params['kappa_concentration'].min():.4f} to {vwm_params['kappa_concentration'].max():.4f}")
        
        # VVIQ2 score range
        print(f"VVIQ2 score range: {vviq2_scores['vviq2_total_score'].min()} to {vviq2_scores['vviq2_total_score'].max()}")
        
        # Calculate standardized effect sizes
        standardized_effects = calculate_standardized_effects(
            mrt_results, vviq2_results, experimental_data, 
            vwm_params, behavioral_controls, vviq2_scores
        )
        
        # Perform sensitivity analysis
        sensitivity_results, model_comparison = perform_sensitivity_analysis(
            experimental_data, vwm_params, behavioral_controls, vviq2_scores
        )
        
        # Save results
        save_results(standardized_effects, sensitivity_results, model_comparison)
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
