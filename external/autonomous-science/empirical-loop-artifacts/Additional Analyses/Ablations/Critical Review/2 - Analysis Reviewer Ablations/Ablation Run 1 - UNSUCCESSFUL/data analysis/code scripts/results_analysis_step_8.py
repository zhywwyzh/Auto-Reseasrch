import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def interpret_effect_size(beta_coef):
    """
    Interpret effect size magnitude based on Cohen's conventions.
    
    Parameters:
    beta_coef (float): Standardized beta coefficient
    
    Returns:
    str: Effect size interpretation (small/medium/large)
    """
    abs_beta = abs(beta_coef)
    if abs_beta >= 0.5:
        return "large"
    elif abs_beta >= 0.3:
        return "medium"
    elif abs_beta >= 0.1:
        return "small"
    else:
        return "negligible"

def assess_practical_significance(beta_coef, ci_lower, ci_upper):
    """
    Assess practical significance based on effect size and confidence intervals.
    
    Parameters:
    beta_coef (float): Standardized beta coefficient
    ci_lower (float): Lower bound of 95% CI
    ci_upper (float): Upper bound of 95% CI
    
    Returns:
    tuple: (bool, str) - practical significance flag and notes
    """
    abs_beta = abs(beta_coef)
    abs_ci_lower = abs(ci_lower)
    abs_ci_upper = abs(ci_upper)
    
    # Check if effect is practically meaningful (>= 0.1)
    practically_meaningful = abs_beta >= 0.1
    
    # Check if CI spans the practical significance threshold
    ci_spans_threshold = min(abs_ci_lower, abs_ci_upper) < 0.1 and max(abs_ci_lower, abs_ci_upper) > 0.1

    notes = []
    if practically_meaningful:
        notes.append(f"Effect size {interpret_effect_size(beta_coef)}")
    else:
        notes.append("Effect size negligible")

    if ci_spans_threshold and practically_meaningful:
        notes.append("CI spans negligible and meaningful effects")
    
    ci_width = ci_upper - ci_lower
    if ci_width > 0.4:
        notes.append("Wide CI indicates low precision")
    
    return practically_meaningful, "; ".join(notes)

def main():
    """
    Main function to process regression results and calculate effect sizes.
    """
    try:
        print("Starting effect size analysis...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find most recent input files
        print("Searching for input files...")
        mrt_pattern = "outputs/mrt_regression_results_*.csv"
        vviq2_pattern = "outputs/vviq2_regression_results_*.csv"
        
        mrt_file = find_most_recent_file(mrt_pattern)
        vviq2_file = find_most_recent_file(vviq2_pattern)
        
        if mrt_file is None:
            print(f"ERROR: No MRT regression results file found matching pattern: {mrt_pattern}")
            return 1
        if vviq2_file is None:
            print(f"ERROR: No VVIQ2 regression results file found matching pattern: {vviq2_pattern}")
            return 1
            
        print(f"Found MRT file: {mrt_file}")
        print(f"Found VVIQ2 file: {vviq2_file}")
        
        # Read input files
        print("\nReading MRT regression results...")
        mrt_df = pd.read_csv(mrt_file)
        print("MRT columns:", list(mrt_df.columns))
        print("First 3 rows of MRT data:")
        print(mrt_df.head(3))
        
        print("\nReading VVIQ2 regression results...")
        vviq2_df = pd.read_csv(vviq2_file)
        print("VVIQ2 columns:", list(vviq2_df.columns))
        print("First 3 rows of VVIQ2 data:")
        print(vviq2_df.head(3))
        
        # Validate required columns
        mrt_required_cols = ['model_type', 'angular_disparity', 'outcome_measure', 'predictor', 
                            'coefficient', 'standard_error', 'p_value', 'ci_lower', 'ci_upper', 
                            'r_squared', 'fdr_adjusted_p']
        vviq2_required_cols = ['model_type', 'outcome_measure', 'predictor', 'coefficient', 
                              'standard_error', 'p_value', 'ci_lower', 'ci_upper', 'r_squared', 
                              'fdr_adjusted_p']
        
        missing_mrt_cols = [col for col in mrt_required_cols if col not in mrt_df.columns]
        missing_vviq2_cols = [col for col in vviq2_required_cols if col not in vviq2_df.columns]
        
        if missing_mrt_cols:
            print(f"ERROR: Missing required columns in MRT data: {missing_mrt_cols}")
            return 1
        if missing_vviq2_cols:
            print(f"ERROR: Missing required columns in VVIQ2 data: {missing_vviq2_cols}")
            return 1
        
        print("\nAll required columns found in both datasets.")
        
        # Print unique values for key experimental design parameters
        print("\nUnique values in key columns:")
        print("MRT model_type:", mrt_df['model_type'].unique())
        print("MRT angular_disparity:", sorted(mrt_df['angular_disparity'].unique()))
        print("MRT outcome_measure:", mrt_df['outcome_measure'].unique())
        print("MRT predictor:", mrt_df['predictor'].unique())
        print("VVIQ2 model_type:", vviq2_df['model_type'].unique())
        print("VVIQ2 outcome_measure:", vviq2_df['outcome_measure'].unique())
        print("VVIQ2 predictor:", vviq2_df['predictor'].unique())
        
        # Filter to kappa_vonmises predictor only
        print("\nFiltering to kappa_vonmises predictor only...")
        mrt_kappa = mrt_df[mrt_df['predictor'] == 'kappa_vonmises'].copy()
        vviq2_kappa = vviq2_df[vviq2_df['predictor'] == 'kappa_vonmises'].copy()
        
        print(f"MRT data after filtering: {len(mrt_kappa)} rows")
        print(f"VVIQ2 data after filtering: {len(vviq2_kappa)} rows")
        
        if len(mrt_kappa) == 0:
            print("WARNING: No MRT data found for kappa_vonmises predictor")
        if len(vviq2_kappa) == 0:
            print("WARNING: No VVIQ2 data found for kappa_vonmises predictor")
        
        # Identify significant relationships
        print("\nIdentifying significant relationships...")
        
        # For MRT: use fdr_adjusted_p < 0.05
        mrt_significant = mrt_kappa[mrt_kappa['fdr_adjusted_p'] < 0.05].copy()
        print(f"Significant MRT relationships: {len(mrt_significant)}")
        
        # For VVIQ2: use p_value < 0.05 for total score, fdr_adjusted_p < 0.05 for subscales
        vviq2_total = vviq2_kappa[vviq2_kappa['outcome_measure'] == 'vviq2_total_score'].copy()
        vviq2_subscales = vviq2_kappa[vviq2_kappa['outcome_measure'] != 'vviq2_total_score'].copy()
        
        vviq2_total_sig = vviq2_total[vviq2_total['p_value'] < 0.05].copy()
        vviq2_subscales_sig = vviq2_subscales[vviq2_subscales['fdr_adjusted_p'] < 0.05].copy()
        
        vviq2_significant = pd.concat([vviq2_total_sig, vviq2_subscales_sig], ignore_index=True)
        print(f"Significant VVIQ2 relationships: {len(vviq2_significant)}")
        
        # Process all effects (both significant and non-significant) for comprehensive table
        print("\nProcessing all effects for comprehensive table...")
        all_effects = []
        
        # Process MRT data
        for _, row in mrt_kappa.iterrows():
            beta_coef = row['coefficient']
            ci_lower = row['ci_lower']
            ci_upper = row['ci_upper']
            p_val = row['p_value']
            fdr_p = row['fdr_adjusted_p']
            
            effect_magnitude = interpret_effect_size(beta_coef)
            is_stat_sig = fdr_p < 0.05
            is_pract_sig, pract_notes = assess_practical_significance(beta_coef, ci_lower, ci_upper)
            
            # Determine outcome domain
            outcome_measure = row['outcome_measure']
            if 'accuracy' in outcome_measure.lower():
                outcome_domain = 'MRT_accuracy'
            elif 'rt' in outcome_measure.lower() or 'time' in outcome_measure.lower():
                outcome_domain = 'MRT_RT'
            else:
                outcome_domain = 'MRT_other'
            
            all_effects.append({
                'outcome_domain': outcome_domain,
                'specific_outcome': outcome_measure,
                'angular_disparity': row['angular_disparity'],
                'beta_coefficient': beta_coef,
                'ci_lower_95': ci_lower,
                'ci_upper_95': ci_upper,
                'p_value': p_val,
                'fdr_adjusted_p': fdr_p,
                'effect_size_magnitude': effect_magnitude,
                'statistically_significant': is_stat_sig,
                'practically_significant': is_pract_sig,
                'r_squared': row['r_squared']
            })
        
        # Process VVIQ2 data
        for _, row in vviq2_kappa.iterrows():
            beta_coef = row['coefficient']
            ci_lower = row['ci_lower']
            ci_upper = row['ci_upper']
            p_val = row['p_value']
            fdr_p = row['fdr_adjusted_p']
            
            effect_magnitude = interpret_effect_size(beta_coef)
            
            # Determine significance based on outcome type
            if row['outcome_measure'] == 'vviq2_total_score':
                is_stat_sig = p_val < 0.05
            else:
                is_stat_sig = fdr_p < 0.05
            
            is_pract_sig, pract_notes = assess_practical_significance(beta_coef, ci_lower, ci_upper)
            
            all_effects.append({
                'outcome_domain': 'VVIQ2',
                'specific_outcome': row['outcome_measure'],
                'angular_disparity': np.nan,  # Not applicable for VVIQ2
                'beta_coefficient': beta_coef,
                'ci_lower_95': ci_lower,
                'ci_upper_95': ci_upper,
                'p_value': p_val,
                'fdr_adjusted_p': fdr_p,
                'effect_size_magnitude': effect_magnitude,
                'statistically_significant': is_stat_sig,
                'practically_significant': is_pract_sig,
                'r_squared': row['r_squared']
            })
        
        print(f"Total effects processed: {len(all_effects)}")
        
        # Create comprehensive effect size table
        effect_sizes_df = pd.DataFrame(all_effects)
        
        print("\nFirst 2 rows of effect sizes table:")
        print("Columns:", list(effect_sizes_df.columns))
        print(effect_sizes_df.head(2))
        
        # Create significant effects summary
        print("\nCreating significant effects summary...")
        significant_effects = []
        
        # Process significant MRT effects
        for _, row in mrt_significant.iterrows():
            beta_coef = row['coefficient']
            ci_lower = row['ci_lower']
            ci_upper = row['ci_upper']
            
            effect_magnitude = interpret_effect_size(beta_coef)
            is_pract_sig, pract_notes = assess_practical_significance(beta_coef, ci_lower, ci_upper)
            
            relationship_desc = f"MRT {row['outcome_measure']} (angular_disparity={row['angular_disparity']}) ~ kappa_vonmises"
            effect_interp = f"{effect_magnitude} effect (β={beta_coef:.3f})"
            
            significant_effects.append({
                'relationship_description': relationship_desc,
                'beta_coefficient': beta_coef,
                'ci_lower_95': ci_lower,
                'ci_upper_95': ci_upper,
                'effect_size_interpretation': effect_interp,
                'practical_significance_notes': pract_notes
            })
        
        # Process significant VVIQ2 effects
        for _, row in vviq2_significant.iterrows():
            beta_coef = row['coefficient']
            ci_lower = row['ci_lower']
            ci_upper = row['ci_upper']
            
            effect_magnitude = interpret_effect_size(beta_coef)
            is_pract_sig, pract_notes = assess_practical_significance(beta_coef, ci_lower, ci_upper)
            
            relationship_desc = f"VVIQ2 {row['outcome_measure']} ~ kappa_vonmises"
            effect_interp = f"{effect_magnitude} effect (β={beta_coef:.3f})"
            
            significant_effects.append({
                'relationship_description': relationship_desc,
                'beta_coefficient': beta_coef,
                'ci_lower_95': ci_lower,
                'ci_upper_95': ci_upper,
                'effect_size_interpretation': effect_interp,
                'practical_significance_notes': pract_notes
            })
        
        significant_effects_df = pd.DataFrame(significant_effects)
        
        print(f"Significant effects summary: {len(significant_effects)} relationships")
        if len(significant_effects) > 0:
            print("First 2 rows of significant effects summary:")
            print("Columns:", list(significant_effects_df.columns))
            print(significant_effects_df.head(2))
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save output files
        effect_sizes_file = f"outputs/effect_sizes_{timestamp}.csv"
        significant_effects_file = f"outputs/significant_effects_summary_{timestamp}.csv"
        
        print(f"\nSaving effect sizes table to: {effect_sizes_file}")
        effect_sizes_df.to_csv(effect_sizes_file, index=False)
        
        print(f"Saving significant effects summary to: {significant_effects_file}")
        significant_effects_df.to_csv(significant_effects_file, index=False)
        
        # Print summary statistics
        print("\n=== EFFECT SIZE ANALYSIS SUMMARY ===")
        print(f"Total relationships analyzed: {len(all_effects)}")
        print(f"Statistically significant relationships: {sum(effect_sizes_df['statistically_significant'])}")
        print(f"Practically significant relationships: {sum(effect_sizes_df['practically_significant'])}")
        print(f"Both statistically and practically significant: {sum(effect_sizes_df['statistically_significant'] & effect_sizes_df['practically_significant'])}")
        
        # Print effect size distribution
        print("\nEffect size magnitude distribution:")
        for magnitude in ['negligible', 'small', 'medium', 'large']:
            count = sum(effect_sizes_df['effect_size_magnitude'] == magnitude)
            print(f"  {magnitude}: {count}")
        
        # Print domain-specific summary
        print("\nDomain-specific summary:")
        for domain in effect_sizes_df['outcome_domain'].unique():
            domain_data = effect_sizes_df[effect_sizes_df['outcome_domain'] == domain]
            sig_count = sum(domain_data['statistically_significant'])
            print(f"  {domain}: {len(domain_data)} total, {sig_count} significant")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
