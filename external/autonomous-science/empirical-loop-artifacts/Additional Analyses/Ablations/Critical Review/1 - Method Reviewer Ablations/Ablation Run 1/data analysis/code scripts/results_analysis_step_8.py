import os
import pandas as pd
import numpy as np
import glob
from datetime import datetime
from scipy import stats
from scipy.stats import f, t
from scipy.optimize import brentq
from scipy.stats import ncf
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
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def benjamini_hochberg_correction(p_values, alpha=0.05):
    """
    Apply Benjamini-Hochberg procedure for multiple comparison correction.
    
    Parameters:
    p_values (array-like): Original p-values
    alpha (float): False discovery rate level (default 0.05)
    
    Returns:
    tuple: (adjusted_p_values, significant_mask)
    """
    p_values = np.array(p_values)
    n = len(p_values)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate adjusted p-values using BH procedure
    adjusted_p = np.zeros(n)
    for i in range(n-1, -1, -1):
        if i == n-1:
            adjusted_p[sorted_indices[i]] = sorted_p[i]
        else:
            adjusted_p[sorted_indices[i]] = min(
                sorted_p[i] * n / (i + 1),
                adjusted_p[sorted_indices[i + 1]]
            )
    
    # Determine significance
    significant = adjusted_p < alpha
    
    return adjusted_p, significant

def calculate_cohens_f_squared_ci(f_squared, n, k, alpha=0.05):
    """Calculate confidence interval for Cohen's f-squared using non-central F distribution."""
    if f_squared <= 0 or n <= k + 1:
        return (0.0, 0.0)
    
    df1 = k
    df2 = n - k - 1
    F_stat = f_squared * df2 / df1
    
    def _find_ncp_bound(target_p, f_stat, df1, df2, is_lower=True):
        """Find non-centrality parameter for CI bound using root finding."""
        def objective(ncp):
            if ncp < 0:
                ncp = 0
            try:
                p_val = ncf.cdf(f_stat, df1, df2, ncp)
                return p_val - target_p
            except:
                return 1.0 if is_lower else -1.0
        
        try:
            if is_lower:
                ncp_bound = brentq(objective, 0, max(100, F_stat * 10), xtol=1e-6)
            else:
                ncp_bound = brentq(objective, 0, max(100, F_stat * 10), xtol=1e-6)
            return max(0, ncp_bound)
        except:
            return 0.0 if is_lower else F_stat * 2
    
    try:
        ncp_lower = _find_ncp_bound(1 - alpha/2, F_stat, df1, df2, is_lower=True)
        ncp_upper = _find_ncp_bound(alpha/2, F_stat, df1, df2, is_lower=False)
        
        f_sq_lower = ncp_lower / (df1 + df2 + 1)
        f_sq_upper = ncp_upper / (df1 + df2 + 1)
        
        return (f_sq_lower, f_sq_upper)
    except:
        return (0.0, f_squared * 2)

def calculate_partial_eta_squared_from_t(t_value, df):
    """
    Calculate partial eta-squared from t-value and degrees of freedom.
    
    Parameters:
    t_value (float): t-statistic
    df (int): Degrees of freedom
    
    Returns:
    float: Partial eta-squared
    """
    if pd.isna(t_value) or df <= 0:
        return np.nan
    
    eta_sq = (t_value ** 2) / (t_value ** 2 + df)
    return eta_sq

def interpret_effect_size(f_squared):
    """
    Interpret Cohen's f-squared effect size magnitude.
    
    Parameters:
    f_squared (float): Cohen's f-squared value
    
    Returns:
    str: Effect size interpretation
    """
    if pd.isna(f_squared) or f_squared < 0:
        return "Invalid"
    elif f_squared < 0.02:
        return "Negligible"
    elif f_squared < 0.15:
        return "Small"
    elif f_squared < 0.35:
        return "Medium"
    else:
        return "Large"

def main():
    """
    Main function to perform multiple comparison corrections and effect size calculations.
    """
    try:
        print("Starting multiple comparison correction and effect size analysis...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input files
        print("\nSearching for input files...")
        mrt_pattern = "outputs/MRT_mixed_effects_results_*.csv"
        vviq_pattern = "outputs/VVIQ2_robust_regression_results_*.csv"
        
        mrt_file = find_latest_file(mrt_pattern)
        vviq_file = find_latest_file(vviq_pattern)
        
        if mrt_file is None:
            print(f"ERROR: No MRT mixed effects results file found matching pattern: {mrt_pattern}")
            return 1
        if vviq_file is None:
            print(f"ERROR: No VVIQ2 robust regression results file found matching pattern: {vviq_pattern}")
            return 1
            
        print(f"Found MRT file: {mrt_file}")
        print(f"Found VVIQ2 file: {vviq_file}")
        
        # Load data files
        print("\nLoading MRT mixed effects results...")
        mrt_df = pd.read_csv(mrt_file)
        print("MRT data columns:", list(mrt_df.columns))
        print("First 3 rows of MRT data:")
        print(mrt_df.head(3))
        
        print("\nLoading VVIQ2 robust regression results...")
        vviq_df = pd.read_csv(vviq_file)
        print("VVIQ2 data columns:", list(vviq_df.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq_df.head(3))
        
        # Validate required columns
        mrt_required_cols = ['model_type', 'effect_name', 'coefficient', 'standard_error', 
                           't_value', 'p_value', 'df', 'confidence_interval_lower', 'confidence_interval_upper']
        vviq_required_cols = ['model_name', 'outcome_variable', 'predictor_name', 'coefficient',
                            'robust_standard_error', 't_statistic', 'p_value', 
                            'confidence_interval_lower', 'confidence_interval_upper', 'cohens_f_squared']
        
        missing_mrt_cols = [col for col in mrt_required_cols if col not in mrt_df.columns]
        missing_vviq_cols = [col for col in vviq_required_cols if col not in vviq_df.columns]
        
        if missing_mrt_cols:
            print(f"ERROR: Missing required columns in MRT data: {missing_mrt_cols}")
            return 1
        if missing_vviq_cols:
            print(f"ERROR: Missing required columns in VVIQ2 data: {missing_vviq_cols}")
            return 1
        
        print("\nAll required columns found in both datasets.")
        
        # Print unique values for key design parameters
        print("\nUnique values in key columns:")
        print("MRT model_type values:", mrt_df['model_type'].unique())
        print("MRT effect_name values:", mrt_df['effect_name'].unique())
        print("VVIQ2 model_name values:", vviq_df['model_name'].unique())
        print("VVIQ2 outcome_variable values:", vviq_df['outcome_variable'].unique())
        print("VVIQ2 predictor_name values:", vviq_df['predictor_name'].unique())
        
        # Initialize results lists
        correction_results = []
        effect_size_results = []
        
        # VVIQ2 subscale analyses - BH correction
        print("\n=== VVIQ2 Subscale Analyses ===")
        # Use correct sample size and dynamic predictor count
        n_vviq = 194  # Correct sample size from prior steps
        k_vviq = vviq_df['predictor_name'].nunique()  # Calculate on full dataset
        print(f"Using correct VVIQ2 parameters: n={n_vviq}, k={k_vviq}")

        vviq_kappa_data = vviq_df[
            (vviq_df['predictor_name'] == 'kappa_vonmises') & 
            (vviq_df['outcome_variable'] != 'total_score_standardized')
        ].copy()
        
        print(f"Found {len(vviq_kappa_data)} VVIQ2 subscale analyses with kappa_vonmises predictor")
        print("VVIQ2 subscale data:")
        print(vviq_kappa_data[['model_name', 'outcome_variable', 'predictor_name', 'p_value']].head(10))
        
        if len(vviq_kappa_data) > 1:
            p_values = vviq_kappa_data['p_value'].values
            adjusted_p, significant = benjamini_hochberg_correction(p_values, alpha=0.05)
            
            print(f"\nApplying BH correction to {len(p_values)} VVIQ2 subscale p-values")
            print("Original p-values:", p_values)
            print("Adjusted p-values:", adjusted_p)
            print("Significant after correction:", significant)
            
            # Store correction results
            for i, (_, row) in enumerate(vviq_kappa_data.iterrows()):
                correction_results.append({
                    'analysis_type': 'VVIQ2_subscales',
                    'model_name': row['model_name'],
                    'effect_name': row['predictor_name'],
                    'original_p_value': p_values[i],
                    'adjusted_p_value': adjusted_p[i],
                    'fdr_significant': significant[i],
                    'correction_method': 'Benjamini-Hochberg',
                    'num_tests_corrected': len(p_values)
                })
                
                # Calculate effect sizes for VVIQ2
                f_squared_raw = row['cohens_f_squared']
                f_squared = max(0, f_squared_raw if not pd.isna(f_squared_raw) else 0.0)
                
                # Use correct parameters for CI calculation
                f_sq_ci_lower, f_sq_ci_upper = calculate_cohens_f_squared_ci(f_squared, n_vviq, k_vviq)
                
                # Convert to partial eta-squared
                eta_sq = f_squared / (1 + f_squared) if f_squared >= 0 else np.nan
                eta_sq_ci_lower = f_sq_ci_lower / (1 + f_sq_ci_lower) if f_sq_ci_lower >= 0 else 0.0
                eta_sq_ci_upper = f_sq_ci_upper / (1 + f_sq_ci_upper) if not np.isinf(f_sq_ci_upper) else 1.0
                
                effect_size_results.append({
                    'analysis_type': 'VVIQ2_subscales',
                    'model_name': row['model_name'],
                    'effect_name': row['predictor_name'],
                    'cohens_f_squared': f_squared,
                    'cohens_f_squared_CI_lower': f_sq_ci_lower,
                    'cohens_f_squared_CI_upper': f_sq_ci_upper,
                    'partial_eta_squared': eta_sq,
                    'partial_eta_squared_CI_lower': eta_sq_ci_lower,
                    'partial_eta_squared_CI_upper': eta_sq_ci_upper,
                    'effect_size_interpretation': interpret_effect_size(f_squared),
                    'practical_significance': f_squared >= 0.02 if not pd.isna(f_squared) else False
                })
        
        # MRT rotation angle analyses - BH correction
        print("\n=== MRT Rotation Angle Analyses ===")
        
        # Extract kappa_vonmises main effect and interaction
        mrt_kappa_main = mrt_df[mrt_df['effect_name'] == 'kappa_vonmises'].copy()
        mrt_kappa_interaction = mrt_df[mrt_df['effect_name'].str.contains('kappa_vonmises.*rotation_angle|rotation_angle.*kappa_vonmises', na=False)].copy()
        
        print(f"Found {len(mrt_kappa_main)} MRT main effects for kappa_vonmises")
        print(f"Found {len(mrt_kappa_interaction)} MRT interaction effects for kappa_vonmises × rotation_angle")
        
        mrt_effects = pd.concat([mrt_kappa_main, mrt_kappa_interaction], ignore_index=True)
        print("MRT effects data:")
        print(mrt_effects[['model_type', 'effect_name', 'p_value']].head(10))
        
        if len(mrt_effects) > 1:
            p_values = mrt_effects['p_value'].values
            adjusted_p, significant = benjamini_hochberg_correction(p_values, alpha=0.05)
            
            print(f"\nApplying BH correction to {len(p_values)} MRT p-values")
            print("Original p-values:", p_values)
            print("Adjusted p-values:", adjusted_p)
            print("Significant after correction:", significant)
            
            # Store correction results for MRT
            for i, (_, row) in enumerate(mrt_effects.iterrows()):
                correction_results.append({
                    'analysis_type': 'MRT_rotation_angle',
                    'model_name': row['model_type'],
                    'effect_name': row['effect_name'],
                    'original_p_value': p_values[i],
                    'adjusted_p_value': adjusted_p[i],
                    'fdr_significant': significant[i],
                    'correction_method': 'Benjamini-Hochberg',
                    'num_tests_corrected': len(p_values)
                })
                
                eta_sq = np.nan
                if row['model_type'] == 'reaction_time' and not pd.isna(row['df']):
                    eta_sq = calculate_partial_eta_squared_from_t(row['t_value'], row['df'])
                elif row['model_type'] == 'accuracy':
                    cohens_d = 2 * row['t_value'] / np.sqrt(194)  # N=194
                    eta_sq = cohens_d**2 / (cohens_d**2 + 4)

                f_squared = eta_sq / (1 - eta_sq) if pd.notna(eta_sq) and eta_sq < 1 else np.nan
                f_sq_ci_lower, f_sq_ci_upper = np.nan, np.nan
                eta_sq_ci_lower, eta_sq_ci_upper = np.nan, np.nan

                effect_size_results.append({
                    'analysis_type': 'MRT_rotation_angle',
                    'model_name': row['model_type'],
                    'effect_name': row['effect_name'],
                    'cohens_f_squared': f_squared,
                    'cohens_f_squared_CI_lower': f_sq_ci_lower,
                    'cohens_f_squared_CI_upper': f_sq_ci_upper,
                    'partial_eta_squared': eta_sq,
                    'partial_eta_squared_CI_lower': eta_sq_ci_lower,
                    'partial_eta_squared_CI_upper': eta_sq_ci_upper,
                    'effect_size_interpretation': interpret_effect_size(f_squared),
                    'practical_significance': f_squared >= 0.02 if not pd.isna(f_squared) else False
                })
        
        # Create output DataFrames
        print("\n=== Creating Output Files ===")
        
        correction_df = pd.DataFrame(correction_results)
        effect_size_df = pd.DataFrame(effect_size_results)
        
        print("Multiple comparison correction results:")
        print("Columns:", list(correction_df.columns))
        print("First 2 rows:")
        print(correction_df.head(2))
        
        print("\nEffect size results:")
        print("Columns:", list(effect_size_df.columns))
        print("First 2 rows:")
        print(effect_size_df.head(2))
        
        # Save output files
        correction_file = f'outputs/multiple_comparisons_corrected_{timestamp}.csv'
        effect_size_file = f'outputs/effect_sizes_with_CI_{timestamp}.csv'
        
        correction_df.to_csv(correction_file, index=False)
        effect_size_df.to_csv(effect_size_file, index=False)
        
        print(f"\nSaved multiple comparison corrections to: {correction_file}")
        print(f"Saved effect size calculations to: {effect_size_file}")
        
        # Summary statistics
        print("\n=== Summary ===")
        if len(correction_results) > 0:
            total_tests = len(correction_results)
            significant_before = sum(1 for r in correction_results if r['original_p_value'] < 0.05)
            significant_after = sum(1 for r in correction_results if r['fdr_significant'])
            
            print(f"Total tests corrected: {total_tests}")
            print(f"Significant before correction: {significant_before}")
            print(f"Significant after FDR correction: {significant_after}")
            
            # Effect size summary
            large_effects = sum(1 for r in effect_size_results if r['effect_size_interpretation'] == 'Large')
            medium_effects = sum(1 for r in effect_size_results if r['effect_size_interpretation'] == 'Medium')
            small_effects = sum(1 for r in effect_size_results if r['effect_size_interpretation'] == 'Small')
            
            print(f"\nEffect size distribution:")
            print(f"Large effects: {large_effects}")
            print(f"Medium effects: {medium_effects}")
            print(f"Small effects: {small_effects}")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
