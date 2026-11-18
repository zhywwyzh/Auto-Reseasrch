import pandas as pd
import numpy as np
from scipy import stats
import glob
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

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
    return max(files, key=os.path.getctime)

def benjamini_hochberg_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg FDR correction to p-values.
    
    Parameters:
    p_values (array): Array of p-values
    alpha (float): Significance level (default 0.05)
    
    Returns:
    tuple: (corrected_p_values, significant_mask)
    """
    p_values = np.array(p_values)
    n = len(p_values)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate corrected p-values
    corrected_p = np.zeros(n)
    for i in range(n):
        corrected_p[sorted_indices[i]] = min(1.0, sorted_p[i] * n / (i + 1))
    
    # Ensure monotonicity
    for i in range(n-2, -1, -1):
        if corrected_p[sorted_indices[i]] > corrected_p[sorted_indices[i+1]]:
            corrected_p[sorted_indices[i]] = corrected_p[sorted_indices[i+1]]
    
    significant = corrected_p <= alpha
    
    return corrected_p, significant

def calculate_cohens_f_squared(r_squared):
    """
    Calculate Cohen's f-squared from R-squared.
    
    Parameters:
    r_squared (float): R-squared value
    
    Returns:
    float: Cohen's f-squared
    """
    if r_squared >= 1.0:
        return np.inf
    return r_squared / (1 - r_squared)

def calculate_partial_eta_squared(coefficient, std_error, df_error):
    """
    Calculate partial eta-squared from coefficient and standard error.
    
    Parameters:
    coefficient (float): Model coefficient
    std_error (float): Standard error
    df_error (int): Error degrees of freedom
    
    Returns:
    float: Partial eta-squared
    """
    t_value = coefficient / std_error
    t_squared = t_value ** 2
    return t_squared / (t_squared + df_error)

def interpret_effect_size(effect_size, effect_type):
    """
    Interpret effect size magnitude according to Cohen's conventions.
    
    Parameters:
    effect_size (float): Effect size value
    effect_type (str): Type of effect size ('f_squared', 'eta_squared', 'delta_r_squared')
    
    Returns:
    str: Effect size interpretation
    """
    if pd.isna(effect_size):
        return "Unknown"
    
    if effect_type == 'f_squared':
        if effect_size < 0.02:
            return "Negligible"
        elif effect_size < 0.15:
            return "Small"
        elif effect_size < 0.35:
            return "Medium"
        else:
            return "Large"
    elif effect_type == 'eta_squared':
        if effect_size < 0.01:
            return "Negligible"
        elif effect_size < 0.06:
            return "Small"
        elif effect_size < 0.14:
            return "Medium"
        else:
            return "Large"
    elif effect_type == 'delta_r_squared':
        if effect_size < 0.02:
            return "Negligible"
        elif effect_size < 0.13:
            return "Small"
        elif effect_size < 0.26:
            return "Medium"
        else:
            return "Large"
    else:
        return "Unknown"

def main():
    """
    Main function to perform FDR correction and effect size calculations.
    """
    print("Starting FDR correction and effect size analysis...")
    
    # Create outputs directory if it doesn't exist
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created outputs directory")
    
    # Find input files
    print("\nSearching for input files...")
    
    mrt_file = find_latest_file('outputs/MRT_VWM_mixed_effects_*.csv')
    vviq2_file = find_latest_file('outputs/VVIQ2_VWM_regression_*.csv')
    hierarchical_file = find_latest_file('outputs/hierarchical_regression_results_*.csv')
    
    print(f"Found MRT mixed effects file: {mrt_file}")
    print(f"Found VVIQ2 regression file: {vviq2_file}")
    print(f"Found hierarchical regression file: {hierarchical_file}")
    
    if not all([mrt_file, vviq2_file, hierarchical_file]):
        print("ERROR: Not all required input files found!")
        return 1
    
    # Load data files
    print("\nLoading data files...")
    
    try:
        mrt_data = pd.read_csv(mrt_file)
        print(f"Loaded MRT data: {mrt_data.shape}")
        print("MRT columns:", list(mrt_data.columns))
        print("First 3 rows of MRT data:")
        print(mrt_data.head(3))
        
        vviq2_data = pd.read_csv(vviq2_file)
        print(f"\nLoaded VVIQ2 data: {vviq2_data.shape}")
        print("VVIQ2 columns:", list(vviq2_data.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq2_data.head(3))
        
        hierarchical_data = pd.read_csv(hierarchical_file)
        print(f"\nLoaded hierarchical data: {hierarchical_data.shape}")
        print("Hierarchical columns:", list(hierarchical_data.columns))
        print("First 3 rows of hierarchical data:")
        print(hierarchical_data.head(3))
        
    except Exception as e:
        print(f"ERROR loading data files: {e}")
        return 1
    
    # Compile all p-values for FDR correction
    print("\nCompiling p-values for FDR correction...")
    
    all_tests = []
    
    # Extract p-values from mixed-effects models
    print("Extracting mixed-effects p-values...")
    for idx, row in mrt_data.iterrows():
        if pd.notna(row['p_value']):
            all_tests.append({
                'analysis_type': f"Mixed_Effects_{row['model_type']}",
                'effect_name': row['effect_name'],
                'original_p_value': row['p_value'],
                'coefficient': row['coefficient'],
                'standard_error': row['standard_error'],
                't_value': row['t_value'],
                'ci_lower': row['ci_lower'],
                'ci_upper': row['ci_upper'],
                'df': row['df'],
                'source_data': 'mrt',
                'row_index': idx
            })
    
    print(f"Found {len([t for t in all_tests if t['source_data'] == 'mrt'])} mixed-effects tests")
    
    # Extract p-values from VVIQ2 regression analyses
    print("Extracting VVIQ2 regression p-values...")
    for idx, row in vviq2_data.iterrows():
        if pd.notna(row['p_value']):
            all_tests.append({
                'analysis_type': 'VVIQ2_Regression',
                'effect_name': f"VVIQ2_{row['outcome_variable']}_{row['predictor']}",
                'original_p_value': row['p_value'],
                'coefficient': row['coefficient'],
                'standard_error': row['standard_error'],
                't_value': row['t_value'],
                'ci_lower': row['ci_lower'],
                'ci_upper': row['ci_upper'],
                # 'r_squared': row['r_squared'],  # Removed as column does not exist
                'n_participants': row['n_participants'],
                'source_data': 'vviq2',
                'row_index': idx
            })
    
    print(f"Found {len([t for t in all_tests if t['source_data'] == 'vviq2'])} VVIQ2 regression tests")
    
    # Extract p-values from hierarchical regression analyses (delta R-squared tests)
    print("Extracting hierarchical regression p-values...")
    for idx, row in hierarchical_data.iterrows():
        if pd.notna(row['delta_r_squared_p_value']):
            all_tests.append({
                'analysis_type': 'Hierarchical_Regression',
                'effect_name': f"Delta_R2_{row['outcome_variable']}_{row['predictor_variable']}",
                'original_p_value': row['delta_r_squared_p_value'],
                'coefficient': row['coefficient'],
                'standard_error': row['standard_error'],
                't_value': row['t_value'],
                'delta_r_squared': row['delta_r_squared'],
                'n_participants': row['n_participants'],
                'r_squared': row.get('r_squared', np.nan),
                'standardized_coefficient': row.get('standardized_coefficient', np.nan),
                'source_data': 'hierarchical',
                'row_index': idx
            })
    
    print(f"Found {len([t for t in all_tests if t['source_data'] == 'hierarchical'])} hierarchical regression tests")
    print(f"Total tests for FDR correction: {len(all_tests)}")
    
    if len(all_tests) == 0:
        print("ERROR: No p-values found for FDR correction!")
        return 1
    
    # Apply FDR correction
    print("\nApplying Benjamini-Hochberg FDR correction...")
    
    p_values = [test['original_p_value'] for test in all_tests]
    corrected_p_values, significant_after_correction = benjamini_hochberg_correction(p_values)
    
    # Add corrected p-values back to test results
    for i, test in enumerate(all_tests):
        test['fdr_corrected_p_value'] = corrected_p_values[i]
        test['significant_after_correction'] = significant_after_correction[i]
    
    print(f"Tests significant before correction: {sum(p < 0.05 for p in p_values)}")
    print(f"Tests significant after FDR correction: {sum(significant_after_correction)}")
    
    # Calculate effect sizes for all tests
    print("\nCalculating effect sizes...")
    
    fdr_results = []
    effect_size_results = []
    
    for test in all_tests:
        print(f"Processing test: {test['effect_name']}")
        
        # Initialize all effect size variables
        effect_size_type = None
        effect_size_value = np.nan
        partial_eta_sq = np.nan
        cohens_f2 = np.nan
        cohens_f2_delta = np.nan
        correlation_r_val = np.nan
        r_squared_val = np.nan
        effect_interpretation = "Cannot calculate"
        
        # Calculate effect sizes based on analysis type
        if test['source_data'] == 'mrt':
            # Mixed-effects models: calculate partial eta-squared only if df is available
            if pd.notna(test.get('df')) and pd.notna(test.get('t_value')):
                df_val = test['df']
                t_val = test['t_value']
                partial_eta_sq = (t_val**2) / (t_val**2 + df_val)
                effect_size_type = 'partial_eta_squared'
                effect_size_value = partial_eta_sq
                effect_interpretation = interpret_effect_size(partial_eta_sq, 'eta_squared')
            else:
                effect_interpretation = "Cannot calculate (missing df)"
                
        elif test['source_data'] == 'vviq2':
            # Calculate R-squared from t-statistic since it's not provided
            if pd.notna(test.get('t_value')) and pd.notna(test.get('n_participants')) and test['n_participants'] > 2:
                t_val = test['t_value']
                n_val = test['n_participants']
                df = n_val - 2
                r_squared_val = (t_val**2) / (t_val**2 + df) if (t_val**2 + df) > 0 else 0
                correlation_r_val = np.sign(t_val) * np.sqrt(r_squared_val)
                cohens_f2 = calculate_cohens_f_squared(r_squared_val)
                effect_size_type = 'cohens_f_squared'
                effect_size_value = cohens_f2
                effect_interpretation = interpret_effect_size(cohens_f2, 'f_squared')
                # Confidence intervals for effect size are not calculated; set to NaN
                effect_size_ci_lower = np.nan
                effect_size_ci_upper = np.nan
            else:
                effect_interpretation = "Cannot calculate"
                
        elif test['source_data'] == 'hierarchical':
            # Hierarchical regression: use delta R-squared
            if pd.notna(test.get('delta_r_squared')):
                effect_size_type = 'delta_r_squared'
                effect_size_value = test['delta_r_squared']
                effect_interpretation = interpret_effect_size(test['delta_r_squared'], 'delta_r_squared')
                # Use correct formula: f² = ΔR² / (1 - R²_total)
                if pd.notna(test.get('r_squared')) and test['r_squared'] < 1.0:
                    cohens_f2_delta = test['delta_r_squared'] / (1 - test['r_squared'])
                else:
                    cohens_f2_delta = np.nan
            else:
                effect_interpretation = "Cannot calculate"
        
        # Get participant count
        n_participants = test.get('n_participants', np.nan)
        
        # Add to FDR results
        fdr_results.append({
            'analysis_type': test['analysis_type'],
            'effect_name': test['effect_name'],
            'original_p_value': test['original_p_value'],
            'fdr_corrected_p_value': test['fdr_corrected_p_value'],
            'significant_after_correction': test['significant_after_correction'],
            'effect_size_type': effect_size_type if effect_size_type else 'unknown',
            'effect_size_value': effect_size_value,
            'effect_size_interpretation': effect_interpretation,
            'n_participants': n_participants
        })
        
        # Add to comprehensive effect sizes
        effect_size_results.append({
            'analysis_category': test['analysis_type'],
            'specific_test': test['effect_name'],
            'coefficient': test.get('coefficient', np.nan),
            'standardized_coefficient': test.get('standardized_coefficient', np.nan) if test['source_data'] == 'hierarchical' else np.nan,
            'partial_eta_squared': partial_eta_sq if test['source_data'] == 'mrt' else np.nan,
            'cohens_f_squared': cohens_f2 if test['source_data'] == 'vviq2' else (cohens_f2_delta if test['source_data'] == 'hierarchical' else np.nan),
            'correlation_r': correlation_r_val,
            'delta_r_squared': test.get('delta_r_squared', np.nan) if test['source_data'] == 'hierarchical' else np.nan,
            'effect_interpretation': effect_interpretation,
            'significance_corrected': test['significant_after_correction']
        })
    
    print(f"Calculated effect sizes for {len(fdr_results)} tests")
    
    # Create final results summary
    print("\nCreating final results summary...")
    
    # Identify key hypotheses and their support
    final_summary = []
    
    # Group results by analysis type to summarize key findings
    significant_results = [r for r in fdr_results if r['significant_after_correction']]
    
    print(f"Found {len(significant_results)} significant results after FDR correction")
    
    # Summarize by hypothesis categories
    hypotheses = {
        'MRT_VWM_Accuracy': [r for r in significant_results if 'Mixed_Effects_logistic' in r['analysis_type']],
        'MRT_VWM_RT': [r for r in significant_results if 'Mixed_Effects_linear' in r['analysis_type']],
        'VVIQ2_VWM_Relationship': [r for r in significant_results if r['analysis_type'] == 'VVIQ2_Regression'],
        'Hierarchical_Incremental_Variance': [r for r in significant_results if r['analysis_type'] == 'Hierarchical_Regression']
    }
    
    for hypothesis, results in hypotheses.items():
        if results:
            # Prioritize results with a calculable effect size
            calculable_results = [r for r in results if pd.notna(r['effect_size_value'])]
            if calculable_results:
                # Take the strongest effect from those that are calculable
                strongest_result = max(calculable_results, key=lambda x: x['effect_size_value'])
            else:
                # Fallback to the first significant result if none have a calculable effect size
                strongest_result = results[0]
            
            final_summary.append({
                'hypothesis': hypothesis,
                'supported_after_correction': True,
                'key_effect_size': strongest_result['effect_size_value'],
                'effect_magnitude': strongest_result['effect_size_interpretation'],
                'corrected_p_value': strongest_result['fdr_corrected_p_value'],
                'interpretation': f"Significant {strongest_result['effect_size_interpretation'].lower()} effect"
            })
        else:
            final_summary.append({
                'hypothesis': hypothesis,
                'supported_after_correction': False,
                'key_effect_size': np.nan,
                'effect_magnitude': 'Not significant',
                'corrected_p_value': np.nan,
                'interpretation': 'No significant effects after FDR correction'
            })
    
    # Save results to CSV files
    print("\nSaving results to CSV files...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save FDR corrected results
    fdr_df = pd.DataFrame(fdr_results)
    fdr_filename = f'outputs/fdr_corrected_results_{timestamp}.csv'
    fdr_df.to_csv(fdr_filename, index=False)
    print(f"Saved FDR corrected results to: {fdr_filename}")
    print("FDR results columns:", list(fdr_df.columns))
    print("First 2 rows of FDR results:")
    print(fdr_df.head(2))
    
    # Save comprehensive effect sizes
    effect_df = pd.DataFrame(effect_size_results)
    effect_filename = f'outputs/comprehensive_effect_sizes_{timestamp}.csv'
    effect_df.to_csv(effect_filename, index=False)
    print(f"Saved comprehensive effect sizes to: {effect_filename}")
    print("Effect sizes columns:", list(effect_df.columns))
    print("First 2 rows of effect sizes:")
    print(effect_df.head(2))
    
    # Save final summary
    summary_df = pd.DataFrame(final_summary)
    summary_filename = f'outputs/final_results_summary_{timestamp}.csv'
    summary_df.to_csv(summary_filename, index=False)
    print(f"Saved final results summary to: {summary_filename}")
    print("Summary columns:", list(summary_df.columns))
    print("First 2 rows of summary:")
    print(summary_df.head(2))
    
    # Print final summary statistics
    print("\n" + "="*50)
    print("FINAL ANALYSIS SUMMARY")
    print("="*50)
    print(f"Total statistical tests conducted: {len(all_tests)}")
    print(f"Tests significant before correction (α = 0.05): {sum(p < 0.05 for p in p_values)}")
    print(f"Tests significant after FDR correction: {sum(significant_after_correction)}")
    print(f"FDR correction success rate: {sum(significant_after_correction)/sum(p < 0.05 for p in p_values)*100:.1f}%" if sum(p < 0.05 for p in p_values) > 0 else "N/A")
    
    print("\nHypothesis Support Summary:")
    for result in final_summary:
        status = "SUPPORTED" if result['supported_after_correction'] else "NOT SUPPORTED"
        print(f"- {result['hypothesis']}: {status}")
        if result['supported_after_correction']:
            print(f"  Effect magnitude: {result['effect_magnitude']}")
            print(f"  Corrected p-value: {result['corrected_p_value']:.4f}")
    
    print("Finished execution")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
