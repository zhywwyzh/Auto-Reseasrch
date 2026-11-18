import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
from statsmodels.stats.multitest import fdrcorrection
import warnings
warnings.filterwarnings('ignore')

def find_most_recent_file(pattern):
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
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def calculate_standardized_coefficient_logistic(raw_coef, predictor_sd):
    """
    Calculate standardized coefficient for logistic regression.

    Parameters:
    raw_coef (float): Raw coefficient from logistic regression
    predictor_sd (float): Standard deviation of predictor variable

    Returns:
    float: Standardized coefficient
    """
    # For logistic regression, standardization is more complex
    # Using approximation: β_std ≈ β * SD_X * sqrt(3)/π for logistic regression
    return raw_coef * predictor_sd * np.sqrt(3) / np.pi

def calculate_standardized_coefficient_linear(raw_coef, predictor_sd, outcome_sd):
    """
    Calculate standardized coefficient for linear regression.
    
    Parameters:
    raw_coef (float): Raw coefficient from linear regression
    predictor_sd (float): Standard deviation of predictor variable
    outcome_sd (float): Standard deviation of outcome variable
    
    Returns:
    float: Standardized coefficient (β = coefficient × SD_predictor / SD_outcome)
    """
    return raw_coef * predictor_sd / outcome_sd

def calculate_standardized_ci(raw_ci_lower, raw_ci_upper, predictor_sd, outcome_sd=None, is_logistic=False):
    """
    Calculate standardized confidence intervals.
    
    Parameters:
    raw_ci_lower (float): Lower bound of raw confidence interval
    raw_ci_upper (float): Upper bound of raw confidence interval
    predictor_sd (float): Standard deviation of predictor variable
    outcome_sd (float): Standard deviation of outcome variable (for linear regression)
    is_logistic (bool): Whether this is for logistic regression
    
    Returns:
    tuple: (standardized_ci_lower, standardized_ci_upper)
    """
    if is_logistic:
        # For logistic regression
        std_ci_lower = raw_ci_lower * predictor_sd * np.sqrt(3) / np.pi
        std_ci_upper = raw_ci_upper * predictor_sd * np.sqrt(3) / np.pi
    else:
        # For linear regression
        std_ci_lower = raw_ci_lower * predictor_sd / outcome_sd
        std_ci_upper = raw_ci_upper * predictor_sd / outcome_sd
    
    return std_ci_lower, std_ci_upper

def interpret_effect_size(beta):
    """
    Interpret effect size based on standardized coefficient magnitude.
    
    Parameters:
    beta (float): Standardized coefficient
    
    Returns:
    str: Effect size interpretation
    """
    abs_beta = abs(beta)
    if abs_beta < 0.1:
        return "Negligible"
    elif abs_beta < 0.3:
        return "Small"
    elif abs_beta < 0.5:
        return "Medium"
    else:
        return "Large"

def assess_practical_significance(beta, ci_lower, ci_upper, threshold=0.1):
    """
    Assess practical significance based on effect size and confidence interval.
    
    Parameters:
    beta (float): Standardized coefficient
    ci_lower (float): Lower bound of standardized confidence interval
    ci_upper (float): Upper bound of standardized confidence interval
    threshold (float): Minimum threshold for practical significance
    
    Returns:
    str: Practical significance assessment
    """
    abs_beta = abs(beta)
    ci_excludes_threshold = (abs(ci_lower) > threshold and abs(ci_upper) > threshold and 
                           np.sign(ci_lower) == np.sign(ci_upper))
    
    if abs_beta >= 0.3 and ci_excludes_threshold:
        return "High practical significance"
    elif abs_beta >= 0.1 and ci_excludes_threshold:
        return "Moderate practical significance"
    elif abs_beta >= 0.1:
        return "Low practical significance"
    else:
        return "Minimal practical significance"

def calculate_mrt_rt_outcome_sd(trial_data_file, angular_disparity=None):
    """
    Calculate outcome SD for MRT reaction time from trial-level data.
    
    Parameters:
    trial_data_file (str): Path to trial-level data file
    angular_disparity (float): Specific angular disparity to filter for, or None for all
    
    Returns:
    float: Standard deviation of participant-level median log reaction times
    """
    if trial_data_file is None:
        print("WARNING: No trial data file available for MRT RT outcome SD calculation")
        return 1.0
    
    try:
        trial_df = pd.read_csv(trial_data_file)
        
        # Filter for correct MRT responses and non-excluded trials
        mrt_correct = trial_df[
            (trial_df['MRT_isCorrect'] == True) & 
            (trial_df['MRT_trial_excluded'] == False)
        ].copy()
        
        # Filter by angular disparity if specified
        if angular_disparity is not None:
            mrt_correct = mrt_correct[mrt_correct['MRT_angle_degrees'] == angular_disparity]
        
        if len(mrt_correct) == 0:
            print(f"WARNING: No valid MRT trials found for angular disparity {angular_disparity}")
            return 1.0
        
        # Calculate log-transformed reaction times
        mrt_correct['log_rt'] = np.log(mrt_correct['MRT_rt_ms'])
        
        # Calculate median log RT by participant
        median_rt_by_participant = mrt_correct.groupby('participantId')['log_rt'].median()
        
        # Calculate standard deviation of these medians
        outcome_sd = median_rt_by_participant.std(ddof=1)
        
        print(f"Calculated MRT RT outcome SD for angular disparity {angular_disparity}: {outcome_sd}")
        return outcome_sd
        
    except Exception as e:
        print(f"ERROR calculating MRT RT outcome SD: {e}")
        return 1.0

def main():
    """
    Main function to process regression results and calculate standardized effect sizes.
    """
    print("Starting standardized effect size calculation...")
    
    # Create outputs directory if it doesn't exist
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")
    
    # Find most recent input files
    print("\nSearching for input files...")
    
    mrt_accuracy_pattern = 'outputs/mrt_accuracy_regression_results_*.csv'
    mrt_rt_pattern = 'outputs/mrt_reaction_time_regression_results_*.csv'
    vviq2_total_pattern = 'outputs/vviq2_total_regression_results_*.csv'
    vviq2_subscale_pattern = 'outputs/vviq2_subscale_regression_results_*.csv'
    
    mrt_accuracy_file = find_most_recent_file(mrt_accuracy_pattern)
    mrt_rt_file = find_most_recent_file(mrt_rt_pattern)
    vviq2_total_file = find_most_recent_file(vviq2_total_pattern)
    vviq2_subscale_file = find_most_recent_file(vviq2_subscale_pattern)
    
    print(f"MRT accuracy file: {mrt_accuracy_file}")
    print(f"MRT reaction time file: {mrt_rt_file}")
    print(f"VVIQ2 total file: {vviq2_total_file}")
    print(f"VVIQ2 subscale file: {vviq2_subscale_file}")
    
    # Find and load source data files for SD calculation
    print("\nSearching for source data files for SD calculation...")
    vwm_params_pattern = 'outputs/vwm_mixture_model_parameters_*.csv'
    individual_measures_pattern = 'outputs/individual_level_measures_*.csv'
    vwm_params_file = find_most_recent_file(vwm_params_pattern)
    individual_measures_file = find_most_recent_file(individual_measures_pattern)
    print(f"VWM parameters file: {vwm_params_file}")
    print(f"Individual measures file: {individual_measures_file}")

    trial_data_pattern = 'outputs/trial_level_cleaned_data_*.csv'
    trial_data_file = find_most_recent_file(trial_data_pattern)
    print(f"Trial data file: {trial_data_file}")

    if vwm_params_file is None or individual_measures_file is None or trial_data_file is None:
        print("WARNING: Missing source data files for SD calculation")
        if trial_data_file is None:
            print("WARNING: Missing trial data file - cannot calculate MRT RT outcome SD")
        print("Will use default SD values (1.0) for standardization calculations")
        print("This may affect the accuracy of standardized coefficients")
        
        # Create empty dataframe with default values
        source_df = pd.DataFrame()
        use_default_sds = True
    else:
        vwm_params_df = pd.read_csv(vwm_params_file)
        individual_measures_df = pd.read_csv(individual_measures_file)
        
        # Merge on participantId (camelCase)
        merge_col = 'participantId' if 'participantId' in vwm_params_df.columns and 'participantId' in individual_measures_df.columns else None
        if merge_col is None:
            print("WARNING: Could not find participantId column in both source files")
            print("Will use default SD values (1.0) for standardization calculations")
            source_df = pd.DataFrame()
            use_default_sds = True
        else:
            source_df = pd.merge(vwm_params_df, individual_measures_df, on=merge_col, how='inner')
            print(f"Merged source data shape: {source_df.shape}")
            use_default_sds = False

    # Check if all files exist
    files_dict = {
        'mrt_accuracy': mrt_accuracy_file,
        'mrt_rt': mrt_rt_file,
        'vviq2_total': vviq2_total_file,
        'vviq2_subscale': vviq2_subscale_file
    }
    
    missing_files = [name for name, path in files_dict.items() if path is None]
    if missing_files:
        print(f"ERROR: Missing input files: {missing_files}")
        return 1
    
    # Initialize results list
    results = []
    
    # Process MRT accuracy results (logistic regression)
    print("\nProcessing MRT accuracy results...")
    try:
        mrt_acc_df = pd.read_csv(mrt_accuracy_file)
        print("MRT accuracy columns:", list(mrt_acc_df.columns))
        print("First 3 rows:")
        print(mrt_acc_df.head(3))
        
        # Print unique values for key columns
        if 'angular_disparity' in mrt_acc_df.columns:
            print("Unique angular_disparity values:", sorted(mrt_acc_df['angular_disparity'].unique()))
        if 'predictor' in mrt_acc_df.columns:
            print("Unique predictor values:", mrt_acc_df['predictor'].unique())
        
        # Filter for kappa_vonmises predictor
        kappa_data = mrt_acc_df[mrt_acc_df['predictor'] == 'kappa_vonmises'].copy()
        print(f"Found {len(kappa_data)} kappa_vonmises coefficients for MRT accuracy")
        
        if len(kappa_data) > 0:
            print("First 2 rows of kappa_vonmises data:")
            print(kappa_data.head(2))

            # Calculate actual SD of kappa_vonmises from source data
            if use_default_sds or 'kappa_vonmises' not in source_df.columns:
                predictor_sd = 1.0
                print("Using default predictor SD = 1.0")
            else:
                predictor_sd = source_df['kappa_vonmises'].std(ddof=1)
                print(f"Calculated predictor SD from data: {predictor_sd}")

            # Apply FDR correction to p-values across angular disparities
            kappa_data = kappa_data.copy()
            if 'p_value' in kappa_data.columns:
                _, fdr_corrected = fdrcorrection(kappa_data['p_value'].values)
                kappa_data['p_value_fdr'] = fdr_corrected
            else:
                kappa_data['p_value_fdr'] = kappa_data['p_value']

            for idx, row in kappa_data.iterrows():
                # Calculate standardized coefficient
                std_coef = calculate_standardized_coefficient_logistic(
                    row['coefficient'], predictor_sd
                )
                
                # Calculate standardized confidence intervals
                std_ci_lower, std_ci_upper = calculate_standardized_ci(
                    row['confidence_interval_lower'], 
                    row['confidence_interval_upper'],
                    predictor_sd, 
                    is_logistic=True
                )
                
                # Use FDR-corrected p-value for significance
                significance_status = "Significant" if row['p_value_fdr'] < 0.05 else "Not significant"
                
                # Interpret effect size and practical significance
                effect_interpretation = interpret_effect_size(std_coef)
                practical_sig = assess_practical_significance(std_coef, std_ci_lower, std_ci_upper)
                
                results.append({
                    'analysis_type': 'MRT_accuracy',
                    'outcome_measure': 'accuracy',
                    'angular_disparity': row['angular_disparity'],
                    'raw_coefficient': row['coefficient'],
                    'standardized_coefficient': std_coef,
                    'confidence_interval_lower_std': std_ci_lower,
                    'confidence_interval_upper_std': std_ci_upper,
                    'p_value': row['p_value_fdr'],
                    'significance_status': significance_status,
                    'effect_size_interpretation': effect_interpretation,
                    'practical_significance': practical_sig,
                    'n_participants': row['n_participants']
                })
        
    except Exception as e:
        print(f"Error processing MRT accuracy file: {e}")
    
    # Process MRT reaction time results (linear regression)
    print("\nProcessing MRT reaction time results...")
    try:
        mrt_rt_df = pd.read_csv(mrt_rt_file)
        print("MRT reaction time columns:", list(mrt_rt_df.columns))
        print("First 3 rows:")
        print(mrt_rt_df.head(3))
        
        # Print unique values for key columns
        if 'angular_disparity' in mrt_rt_df.columns:
            print("Unique angular_disparity values:", sorted(mrt_rt_df['angular_disparity'].unique()))
        if 'predictor' in mrt_rt_df.columns:
            print("Unique predictor values:", mrt_rt_df['predictor'].unique())
        
        # Filter for kappa_vonmises predictor
        kappa_data = mrt_rt_df[mrt_rt_df['predictor'] == 'kappa_vonmises'].copy()
        print(f"Found {len(kappa_data)} kappa_vonmises coefficients for MRT reaction time")
        
        if len(kappa_data) > 0:
            print("First 2 rows of kappa_vonmises data:")
            print(kappa_data.head(2))

            # Calculate actual SD of kappa_vonmises from source data
            if use_default_sds or 'kappa_vonmises' not in source_df.columns:
                predictor_sd = 1.0
                print("Using default predictor SD = 1.0")
            else:
                predictor_sd = source_df['kappa_vonmises'].std(ddof=1)
                print(f"Calculated predictor SD from data: {predictor_sd}")

            # Apply FDR correction to p-values across angular disparities
            kappa_data = kappa_data.copy()
            if 'p_value' in kappa_data.columns:
                _, fdr_corrected = fdrcorrection(kappa_data['p_value'].values)
                kappa_data['p_value_fdr'] = fdr_corrected
            else:
                kappa_data['p_value_fdr'] = kappa_data['p_value']

            for idx, row in kappa_data.iterrows():
                # Calculate actual SD of reaction_time from trial data for this specific angular disparity
                if use_default_sds or trial_data_file is None:
                    outcome_sd = 1.0
                    print(f"Using default outcome SD = 1.0 for reaction time at {row['angular_disparity']} degrees")
                else:
                    outcome_sd = calculate_mrt_rt_outcome_sd(trial_data_file, row['angular_disparity'])

                # Calculate standardized coefficient for linear regression
                std_coef = calculate_standardized_coefficient_linear(
                    row['coefficient'], predictor_sd, outcome_sd
                )
                
                # Calculate standardized confidence intervals
                std_ci_lower, std_ci_upper = calculate_standardized_ci(
                    row['confidence_interval_lower'], 
                    row['confidence_interval_upper'],
                    predictor_sd, 
                    outcome_sd,
                    is_logistic=False
                )
                
                # Use FDR-corrected p-value for significance
                significance_status = "Significant" if row['p_value_fdr'] < 0.05 else "Not significant"
                
                # Interpret effect size and practical significance
                effect_interpretation = interpret_effect_size(std_coef)
                practical_sig = assess_practical_significance(std_coef, std_ci_lower, std_ci_upper)
                
                results.append({
                    'analysis_type': 'MRT_reaction_time',
                    'outcome_measure': 'reaction_time',
                    'angular_disparity': row['angular_disparity'],
                    'raw_coefficient': row['coefficient'],
                    'standardized_coefficient': std_coef,
                    'confidence_interval_lower_std': std_ci_lower,
                    'confidence_interval_upper_std': std_ci_upper,
                    'p_value': row['p_value_fdr'],
                    'significance_status': significance_status,
                    'effect_size_interpretation': effect_interpretation,
                    'practical_significance': practical_sig,
                    'n_participants': row['n_participants']
                })
        
    except Exception as e:
        print(f"Error processing MRT reaction time file: {e}")
    
    # Process VVIQ2 total results
    print("\nProcessing VVIQ2 total results...")
    try:
        vviq2_total_df = pd.read_csv(vviq2_total_file)
        print("VVIQ2 total columns:", list(vviq2_total_df.columns))
        print("First 3 rows:")
        print(vviq2_total_df.head(3))
        
        # Print unique values for key columns
        if 'predictor' in vviq2_total_df.columns:
            print("Unique predictor values:", vviq2_total_df['predictor'].unique())
        
        # Filter for kappa_vonmises predictor
        kappa_data = vviq2_total_df[vviq2_total_df['predictor'] == 'kappa_vonmises'].copy()
        print(f"Found {len(kappa_data)} kappa_vonmises coefficients for VVIQ2 total")
        
        if len(kappa_data) > 0:
            print("First 2 rows of kappa_vonmises data:")
            print(kappa_data.head(2))

            # Calculate actual SD of kappa_vonmises from source data
            if use_default_sds or 'kappa_vonmises' not in source_df.columns:
                predictor_sd = 1.0
                print("Using default predictor SD = 1.0")
            else:
                predictor_sd = source_df['kappa_vonmises'].std(ddof=1)
                print(f"Calculated predictor SD from data: {predictor_sd}")

            # Calculate actual SD of VVIQ2 total from source data
            if use_default_sds:
                outcome_sd = 1.0
                print("Using default outcome SD = 1.0 for VVIQ2 total")
            else:
                vviq2_total_col_candidates = [col for col in source_df.columns if 'vviq2_total' in col]
                if len(vviq2_total_col_candidates) > 0:
                    outcome_sd = source_df[vviq2_total_col_candidates[0]].std(ddof=1)
                    print(f"Using {vviq2_total_col_candidates[0]} for VVIQ2 total SD: {outcome_sd}")
                else:
                    print("WARNING: No vviq2_total column found in source data, using SD=1.0")
                    outcome_sd = 1.0

            for _, row in kappa_data.iterrows():
                # Calculate standardized coefficient
                std_coef = calculate_standardized_coefficient_linear(
                    row['coefficient'], predictor_sd, outcome_sd
                )
                
                # Calculate standardized confidence intervals
                std_ci_lower, std_ci_upper = calculate_standardized_ci(
                    row['confidence_interval_lower'], 
                    row['confidence_interval_upper'],
                    predictor_sd, 
                    outcome_sd,
                    is_logistic=False
                )
                
                # Determine significance status
                significance_status = "Significant" if row['p_value'] < 0.05 else "Not significant"
                
                # Interpret effect size and practical significance
                effect_interpretation = interpret_effect_size(std_coef)
                practical_sig = assess_practical_significance(std_coef, std_ci_lower, std_ci_upper)
                
                results.append({
                    'analysis_type': 'VVIQ2_total',
                    'outcome_measure': 'vviq2_total',
                    'angular_disparity': 'NA',  # Not applicable for VVIQ2
                    'raw_coefficient': row['coefficient'],
                    'standardized_coefficient': std_coef,
                    'confidence_interval_lower_std': std_ci_lower,
                    'confidence_interval_upper_std': std_ci_upper,
                    'p_value': row['p_value'],
                    'significance_status': significance_status,
                    'effect_size_interpretation': effect_interpretation,
                    'practical_significance': practical_sig,
                    'n_participants': row['n_participants']
                })
        
    except Exception as e:
        print(f"Error processing VVIQ2 total file: {e}")
    
    # Process VVIQ2 subscale results
    print("\nProcessing VVIQ2 subscale results...")
    try:
        vviq2_subscale_df = pd.read_csv(vviq2_subscale_file)
        print("VVIQ2 subscale columns:", list(vviq2_subscale_df.columns))
        print("First 3 rows:")
        print(vviq2_subscale_df.head(3))
        
        # Print unique values for key columns
        if 'subscale' in vviq2_subscale_df.columns:
            print("Unique subscale values:", vviq2_subscale_df['subscale'].unique())
        if 'predictor' in vviq2_subscale_df.columns:
            print("Unique predictor values:", vviq2_subscale_df['predictor'].unique())
        
        # Filter for kappa_vonmises predictor
        kappa_data = vviq2_subscale_df[vviq2_subscale_df['predictor'] == 'kappa_vonmises'].copy()
        # Filter for significant results only (as per instructions)
        has_fdr = 'p_value_fdr_adjusted' in kappa_data.columns
        if has_fdr:
            kappa_data = kappa_data[kappa_data['p_value_fdr_adjusted'] < 0.05]
        print(f"Found {len(kappa_data)} significant kappa_vonmises coefficients for VVIQ2 subscales")
        
        if len(kappa_data) > 0:
            print("First 2 rows of kappa_vonmises data:")
            print(kappa_data.head(2))
            
            # Calculate actual SD of kappa_vonmises from source data
            if use_default_sds or 'kappa_vonmises' not in source_df.columns:
                predictor_sd = 1.0
                print("Using default predictor SD = 1.0")
            else:
                predictor_sd = source_df['kappa_vonmises'].std(ddof=1)
                print(f"Calculated predictor SD from data: {predictor_sd}")

            for _, row in kappa_data.iterrows():
                # Use FDR-adjusted p-value if available, otherwise regular p-value
                p_value_to_use = row['p_value_fdr_adjusted'] if has_fdr else row['p_value']

                # Calculate actual SD of the subscale from source data
                if use_default_sds:
                    outcome_sd = 1.0
                    print(f"Using default outcome SD = 1.0 for subscale {row['subscale']}")
                else:
                    subscale_col = None
                    if 'subscale' in row and row['subscale'] in source_df.columns:
                        subscale_col = row['subscale']
                    elif 'subscale' in row and any(row['subscale'].lower() in col.lower() for col in source_df.columns):
                        # Try to match ignoring case
                        for col in source_df.columns:
                            if row['subscale'].lower() in col.lower():
                                subscale_col = col
                                break
                    if subscale_col is not None:
                        outcome_sd = source_df[subscale_col].std(ddof=1)
                        print(f"Using {subscale_col} for subscale SD: {outcome_sd}")
                    else:
                        print(f"WARNING: Could not find subscale column for {row['subscale']}, using SD=1.0")
                        outcome_sd = 1.0

                # Calculate standardized coefficient
                std_coef = calculate_standardized_coefficient_linear(
                    row['coefficient'], predictor_sd, outcome_sd
                )
                
                # Calculate standardized confidence intervals
                std_ci_lower, std_ci_upper = calculate_standardized_ci(
                    row['confidence_interval_lower'], 
                    row['confidence_interval_upper'],
                    predictor_sd, 
                    outcome_sd,
                    is_logistic=False
                )
                
                # Determine significance status
                significance_status = "Significant" if p_value_to_use < 0.05 else "Not significant"
                
                # Interpret effect size and practical significance
                effect_interpretation = interpret_effect_size(std_coef)
                practical_sig = assess_practical_significance(std_coef, std_ci_lower, std_ci_upper)
                
                # Use subscale as outcome measure
                outcome_measure = row['subscale'] if 'subscale' in row else 'vviq2_subscale'
                
                results.append({
                    'analysis_type': 'VVIQ2_subscale',
                    'outcome_measure': outcome_measure,
                    'angular_disparity': 'NA',  # Not applicable for VVIQ2
                    'raw_coefficient': row['coefficient'],
                    'standardized_coefficient': std_coef,
                    'confidence_interval_lower_std': std_ci_lower,
                    'confidence_interval_upper_std': std_ci_upper,
                    'p_value': p_value_to_use,
                    'significance_status': significance_status,
                    'effect_size_interpretation': effect_interpretation,
                    'practical_significance': practical_sig,
                    'n_participants': row['n_participants']
                })
        
    except Exception as e:
        print(f"Error processing VVIQ2 subscale file: {e}")
    
    # Create results dataframe
    print(f"\nTotal results processed: {len(results)}")
    
    if len(results) == 0:
        print("ERROR: No results to process")
        return 1
    
    results_df = pd.DataFrame(results)
    
    print("\nResults summary:")
    print("Analysis types:", results_df['analysis_type'].unique())
    print("Outcome measures:", results_df['outcome_measure'].unique())
    print("Effect size interpretations:", results_df['effect_size_interpretation'].value_counts())
    print("Significance status:", results_df['significance_status'].value_counts())
    
    print("\nFirst 2 rows of results:")
    print(results_df.head(2))
    
    print("\nAll columns in results:")
    print(list(results_df.columns))
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f'outputs/standardized_effect_sizes_{timestamp}.csv'
    
    results_df.to_csv(output_filename, index=False)
    print(f"\nResults saved to: {output_filename}")
    
    # Print summary statistics
    print("\n=== EFFECT SIZE SUMMARY ===")
    print(f"Total analyses: {len(results_df)}")
    print(f"Significant results: {len(results_df[results_df['significance_status'] == 'Significant'])}")
    
    print("\nEffect sizes by analysis type:")
    for analysis_type in results_df['analysis_type'].unique():
        subset = results_df[results_df['analysis_type'] == analysis_type]
        print(f"\n{analysis_type}:")
        print(f"  Mean standardized coefficient: {subset['standardized_coefficient'].mean():.3f}")
        print(f"  Effect size distribution:")
        print(subset['effect_size_interpretation'].value_counts().to_dict())
        print(f"  Practical significance distribution:")
        print(subset['practical_significance'].value_counts().to_dict())
    
    print("\n=== CONFIDENCE INTERVAL INTERPRETATION ===")
    for _, row in results_df.iterrows():
        ci_width = row['confidence_interval_upper_std'] - row['confidence_interval_lower_std']
        ci_excludes_zero = (row['confidence_interval_lower_std'] > 0) or (row['confidence_interval_upper_std'] < 0)
        
        print(f"\n{row['analysis_type']} - {row['outcome_measure']}:")
        print(f"  Standardized β: {row['standardized_coefficient']:.3f}")
        print(f"  95% CI: [{row['confidence_interval_lower_std']:.3f}, {row['confidence_interval_upper_std']:.3f}]")
        print(f"  CI width: {ci_width:.3f}")
        print(f"  CI excludes zero: {ci_excludes_zero}")
        print(f"  Effect size: {row['effect_size_interpretation']}")
        print(f"  Practical significance: {row['practical_significance']}")
    
    print("Finished execution")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
