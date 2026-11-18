import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

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
    # Sort by modification time and return the most recent
    return max(files, key=os.path.getmtime)

def calculate_effect_size_magnitude(beta):
    """
    Calculate effect size magnitude based on Cohen's conventions.
    
    Parameters:
    beta (float): Standardized regression coefficient
    
    Returns:
    str: Effect size magnitude category
    """
    abs_beta = abs(beta)
    if abs_beta >= 0.5:
        return "Large"
    elif abs_beta >= 0.3:
        return "Medium"
    elif abs_beta >= 0.1:
        return "Small"
    else:
        return "Negligible"

def determine_statistical_significance(p_value, alpha=0.05):
    """
    Determine statistical significance based on p-value.
    
    Parameters:
    p_value (float): P-value from statistical test
    alpha (float): Significance threshold (default 0.05)
    
    Returns:
    str: "Significant" or "Not Significant"
    """
    if pd.isna(p_value):
        return "Not Significant"
    return "Significant" if p_value < alpha else "Not Significant"

def assess_practical_significance(beta, ci_lower, ci_upper):
    """
    Assess practical significance based on effect size and confidence intervals.
    
    Parameters:
    beta (float): Standardized regression coefficient
    ci_lower (float): Lower bound of confidence interval
    ci_upper (float): Upper bound of confidence interval
    
    Returns:
    str: Practical significance assessment
    """
    abs_beta = abs(beta)
    
    # Check if confidence interval excludes zero
    excludes_zero = (ci_lower > 0 and ci_upper > 0) or (ci_lower < 0 and ci_upper < 0)
    
    if abs_beta >= 0.3 and excludes_zero:
        return "High"
    elif abs_beta >= 0.1 and excludes_zero:
        return "Moderate"
    elif abs_beta >= 0.1:
        return "Low"
    else:
        return "Negligible"

def calculate_or_magnitude(odds_ratio):
    """
    Calculate effect size magnitude for Odds Ratios based on log(OR).
    
    Parameters:
    odds_ratio (float): Odds ratio from logistic regression
    
    Returns:
    str: Effect size magnitude category
    """
    if pd.isna(odds_ratio) or odds_ratio <= 0:
        return "Negligible"
    
    log_or = abs(np.log(odds_ratio))
    if log_or >= 0.693:  # ln(2) ≈ 0.693, OR ≥ 2 or ≤ 0.5
        return "Large"
    elif log_or >= 0.405:  # ln(1.5) ≈ 0.405, OR ≥ 1.5 or ≤ 0.67
        return "Medium"
    elif log_or >= 0.182:  # ln(1.2) ≈ 0.182, OR ≥ 1.2 or ≤ 0.83
        return "Small"
    else:
        return "Negligible"

def assess_or_practical_significance(odds_ratio, ci_lower, ci_upper):
    """
    Assess practical significance for Odds Ratios.
    
    Parameters:
    odds_ratio (float): Odds ratio from logistic regression
    ci_lower (float): Lower bound of OR confidence interval
    ci_upper (float): Upper bound of OR confidence interval
    
    Returns:
    str: Practical significance assessment
    """
    if pd.isna(odds_ratio) or odds_ratio <= 0:
        return "Negligible"
    
    log_or = abs(np.log(odds_ratio))
    
    # Check if confidence interval excludes 1 (null value for OR)
    excludes_one = (ci_lower > 1 and ci_upper > 1) or (ci_lower < 1 and ci_upper < 1)
    
    if log_or >= 0.405 and excludes_one:  # Medium+ effect and excludes null
        return "High"
    elif log_or >= 0.182 and excludes_one:  # Small+ effect and excludes null
        return "Moderate"
    elif log_or >= 0.182:  # Small+ effect but CI includes null
        return "Low"
    else:
        return "Negligible"

def process_regression_results():
    """
    Process regression results files to create effect sizes summary.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        print("Starting effect sizes analysis...")
        
        # Find most recent input files
        print("Searching for input files...")
        mrt_pattern = "outputs/MRT_regression_results_*.csv"
        vviq2_pattern = "outputs/VVIQ2_regression_results_*.csv"
        
        mrt_file = find_most_recent_file(mrt_pattern)
        vviq2_file = find_most_recent_file(vviq2_pattern)
        
        if not mrt_file:
            print(f"Error: No MRT regression results file found matching pattern: {mrt_pattern}")
            return 1
        if not vviq2_file:
            print(f"Error: No VVIQ2 regression results file found matching pattern: {vviq2_pattern}")
            return 1
            
        print(f"Found MRT file: {mrt_file}")
        print(f"Found VVIQ2 file: {vviq2_file}")
        
        # Read input files
        print("\nReading MRT regression results...")
        mrt_df = pd.read_csv(mrt_file)
        print(f"MRT file columns: {list(mrt_df.columns)}")
        print("First 3 rows of MRT data:")
        print(mrt_df.head(3))
        
        print("\nReading VVIQ2 regression results...")
        vviq2_df = pd.read_csv(vviq2_file)
        print(f"VVIQ2 file columns: {list(vviq2_df.columns)}")
        print("First 3 rows of VVIQ2 data:")
        print(vviq2_df.head(3))
        
        # Print unique values for key experimental design parameters
        print("\nUnique values in key columns:")
        if 'angular_disparity' in mrt_df.columns:
            print(f"MRT angular_disparity values: {sorted(mrt_df['angular_disparity'].dropna().unique())}")
        if 'analysis_type' in mrt_df.columns:
            print(f"MRT analysis_type values: {mrt_df['analysis_type'].unique()}")
        if 'dependent_variable' in mrt_df.columns:
            print(f"MRT dependent_variable values: {mrt_df['dependent_variable'].unique()}")
        if 'predictor_variable' in mrt_df.columns:
            print(f"MRT predictor_variable values: {mrt_df['predictor_variable'].unique()}")
            
        if 'analysis_type' in vviq2_df.columns:
            print(f"VVIQ2 analysis_type values: {vviq2_df['analysis_type'].unique()}")
        if 'dependent_variable' in vviq2_df.columns:
            print(f"VVIQ2 dependent_variable values: {vviq2_df['dependent_variable'].unique()}")
        if 'predictor_variable' in vviq2_df.columns:
            print(f"VVIQ2 predictor_variable values: {vviq2_df['predictor_variable'].unique()}")
        
        # Filter for vonMises_kappa predictor rows only
        print("\nFiltering for vonMises_kappa predictor rows...")
        mrt_filtered = mrt_df[mrt_df['predictor_variable'] == 'vonMises_kappa'].copy()
        vviq2_filtered = vviq2_df[vviq2_df['predictor_variable'] == 'vonMises_kappa'].copy()
        
        print(f"MRT filtered rows: {len(mrt_filtered)}")
        print(f"VVIQ2 filtered rows: {len(vviq2_filtered)}")
        
        if len(mrt_filtered) == 0:
            print("Warning: No vonMises_kappa predictor rows found in MRT data")
        if len(vviq2_filtered) == 0:
            print("Warning: No vonMises_kappa predictor rows found in VVIQ2 data")
        
        # Initialize results list
        results = []
        
        # Process MRT results
        print("\nProcessing MRT regression results...")
        for idx, row in mrt_filtered.iterrows():
            print(f"Processing MRT row {idx}: {row['dependent_variable']}, angular_disparity: {row.get('angular_disparity', 'N/A')}, analysis_type: {row['analysis_type']}")
            
            # Determine significance - use p_value_fdr_corrected if available, otherwise p_value
            if 'p_value_fdr_corrected' in row and pd.notna(row['p_value_fdr_corrected']):
                p_val = row['p_value_fdr_corrected']
            else:
                p_val = row['p_value']
            
            # Extract coefficient and confidence intervals
            coefficient = row['coefficient']
            ci_lower = row['confidence_interval_lower']
            ci_upper = row['confidence_interval_upper']
            
            # Handle different analysis types
            if row['analysis_type'] == 'logistic_regression':
                # Coefficient is an Odds Ratio
                effect_magnitude = calculate_or_magnitude(coefficient)
                practical_significance = assess_or_practical_significance(coefficient, ci_lower, ci_upper)
                interpretation = f"vonMises_kappa -> {row['dependent_variable']}: OR={coefficient:.3f}, {effect_magnitude} effect, {determine_statistical_significance(p_val)}"
            else:
                # Coefficient is a standardized beta (linear regression)
                effect_magnitude = calculate_effect_size_magnitude(coefficient)
                practical_significance = assess_practical_significance(coefficient, ci_lower, ci_upper)
                interpretation = f"vonMises_kappa -> {row['dependent_variable']}: β={coefficient:.3f}, {effect_magnitude} effect, {determine_statistical_significance(p_val)}"
            
            stat_significance = determine_statistical_significance(p_val)
            
            # Create result record
            result = {
                'relationship_type': 'MRT',
                'dependent_variable': row['dependent_variable'],
                'angular_disparity': row.get('angular_disparity', np.nan),
                'coefficient': coefficient,
                'confidence_interval_lower': ci_lower,
                'confidence_interval_upper': ci_upper,
                'p_value_fdr_corrected': p_val,
                'effect_size_magnitude': effect_magnitude,
                'statistical_significance': stat_significance,
                'practical_significance': practical_significance,
                'sample_size': row['sample_size'],
                'interpretation': interpretation
            }
            
            results.append(result)
            if row['analysis_type'] == 'logistic_regression':
                print(f"  OR={coefficient:.3f}, p={p_val:.4f}, {effect_magnitude} effect, {stat_significance}")
            else:
                print(f"  β={coefficient:.3f}, p={p_val:.4f}, {effect_magnitude} effect, {stat_significance}")
        
        # Process VVIQ2 results
        print("\nProcessing VVIQ2 regression results...")
        for idx, row in vviq2_filtered.iterrows():
            print(f"Processing VVIQ2 row {idx}: {row['dependent_variable']}")
            
            # Determine significance - use p_value_fdr_corrected if available, otherwise p_value
            if 'p_value_fdr_corrected' in row and pd.notna(row['p_value_fdr_corrected']):
                p_val = row['p_value_fdr_corrected']
            else:
                p_val = row['p_value']
            
            # Extract coefficient (standardized beta)
            beta = row['coefficient']
            ci_lower = row['confidence_interval_lower']
            ci_upper = row['confidence_interval_upper']
            
            # Calculate effect size metrics
            effect_magnitude = calculate_effect_size_magnitude(beta)
            stat_significance = determine_statistical_significance(p_val)
            practical_significance = assess_practical_significance(beta, ci_lower, ci_upper)
            
            # Create result record
            result = {
                'relationship_type': 'VVIQ2',
                'dependent_variable': row['dependent_variable'],
                'angular_disparity': np.nan,  # VVIQ2 doesn't have angular disparity
                'coefficient': beta,
                'confidence_interval_lower': ci_lower,
                'confidence_interval_upper': ci_upper,
                'p_value_fdr_corrected': p_val,
                'effect_size_magnitude': effect_magnitude,
                'statistical_significance': stat_significance,
                'practical_significance': practical_significance,
                'sample_size': row['sample_size'],
                'interpretation': f"vonMises_kappa -> {row['dependent_variable']}: β={beta:.3f}, {effect_magnitude} effect, {stat_significance}"
            }
            
            results.append(result)
            print(f"  β={beta:.3f}, p={p_val:.4f}, {effect_magnitude} effect, {stat_significance}")
        
        # Create results dataframe
        print(f"\nCreating results dataframe with {len(results)} records...")
        results_df = pd.DataFrame(results)
        
        # Print summary statistics
        print("\nEffect Size Summary:")
        print(f"Total relationships analyzed: {len(results_df)}")
        print(f"Significant relationships: {len(results_df[results_df['statistical_significance'] == 'Significant'])}")
        print(f"Large effects: {len(results_df[results_df['effect_size_magnitude'] == 'Large'])}")
        print(f"Medium effects: {len(results_df[results_df['effect_size_magnitude'] == 'Medium'])}")
        print(f"Small effects: {len(results_df[results_df['effect_size_magnitude'] == 'Small'])}")
        print(f"Negligible effects: {len(results_df[results_df['effect_size_magnitude'] == 'Negligible'])}")
        
        # Quality control checks
        print("\nQuality control checks:")
        
        # Check confidence intervals for significant effects
        significant_effects = results_df[results_df['statistical_significance'] == 'Significant']
        if len(significant_effects) > 0:
            print(f"Checking {len(significant_effects)} significant effects...")
            for idx, row in significant_effects.iterrows():
                if row['relationship_type'] == 'MRT' and row['dependent_variable'] == 'MRT_accuracy':
                    # For OR, check if CI excludes 1
                    ci_excludes_null = (row['confidence_interval_lower'] > 1 and row['confidence_interval_upper'] > 1) or \
                                       (row['confidence_interval_lower'] < 1 and row['confidence_interval_upper'] < 1)
                else:
                    # For beta, check if CI excludes 0
                    ci_excludes_null = (row['confidence_interval_lower'] > 0 and row['confidence_interval_upper'] > 0) or \
                                       (row['confidence_interval_lower'] < 0 and row['confidence_interval_upper'] < 0)
                if not ci_excludes_null:
                    print(f"  Warning: Significant effect has CI including null value: {row['dependent_variable']}")
                else:
                    print(f"  ✓ Significant effect CI excludes null value: {row['dependent_variable']}")
        else:
            print("No significant effects found to check.")
        
        # Print first few rows of results
        print("\nFirst 2 rows of results dataframe:")
        print("All columns:", list(results_df.columns))
        print(results_df.head(2))
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"outputs/effect_sizes_summary_{timestamp}.csv"
        
        print(f"\nSaving results to: {output_file}")
        results_df.to_csv(output_file, index=False)
        
        print(f"Effect sizes summary saved successfully with {len(results_df)} rows")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = process_regression_results()
    exit(exit_code)
