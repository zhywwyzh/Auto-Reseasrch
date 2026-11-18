import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
from scipy import stats
import sys

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.

    Parameters
    ----------
    pattern : str
        File pattern to match (e.g., 'outputs/mrt_accuracy_regression_results_*.csv').

    Returns
    -------
    str or None
        Path to the most recent file, or None if no files found.
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    return latest_file

def calculate_standardized_coefficient(raw_coef, sd_predictor, sd_outcome):
    """
    Calculate the standardized regression coefficient (beta).

    Parameters
    ----------
    raw_coef : float
        Raw regression coefficient from the model.
    sd_predictor : float
        Standard deviation of the predictor variable.
    sd_outcome : float
        Standard deviation of the outcome variable.

    Returns
    -------
    float
        Standardized coefficient (beta).
    """
    return raw_coef * (sd_predictor / sd_outcome)

def calculate_confidence_interval(beta, se_beta, n_participants, k_predictors=1, alpha=0.05):
    """
    Calculate the confidence interval for a standardized coefficient.

    Parameters
    ----------
    beta : float
        Standardized coefficient.
    se_beta : float
        Standard error of the standardized coefficient.
    n_participants : int
        Number of participants in the regression.
    k_predictors : int, optional
        Number of predictors in the model (default is 1).
    alpha : float, optional
        Significance level for the confidence interval (default is 0.05).

    Returns
    -------
    tuple of float
        (lower_bound, upper_bound) of the confidence interval.
    """
    df = n_participants - k_predictors - 1
    t_critical = stats.t.ppf(1 - alpha/2, df)
    margin_error = t_critical * se_beta
    return (beta - margin_error, beta + margin_error)

def categorize_effect_size(beta):
    """
    Categorize effect size according to Cohen's conventions.

    Parameters
    ----------
    beta : float
        Standardized coefficient.

    Returns
    -------
    str
        Effect size category: 'negligible', 'small', 'medium', or 'large'.
    """
    abs_beta = abs(beta)
    if abs_beta < 0.1:
        return "negligible"
    elif abs_beta < 0.3:
        return "small"
    elif abs_beta < 0.5:
        return "medium"
    else:
        return "large"

def calculate_variance_explained(beta):
    """
    Calculate the approximate percentage variance explained by the predictor.

    Parameters
    ----------
    beta : float
        Standardized coefficient.

    Returns
    -------
    float
        Percentage variance explained by the predictor.
    """
    return (beta ** 2) * 100

def validate_output_columns(df, required_columns, df_name="DataFrame"):
    """
    Validate that the DataFrame contains exactly the required columns (no extras) and that they are not entirely missing.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to validate.
    required_columns : list of str
        List of required column names.
    df_name : str, optional
        Name of the DataFrame for error messages.

    Returns
    -------
    bool
        True if all required columns are present, no extras, and not all values are missing, False otherwise.
    """
    missing_cols = [col for col in required_columns if col not in df.columns]
    extra_cols = [col for col in df.columns if col not in required_columns]
    if missing_cols:
        print(f"ERROR: {df_name} is missing required columns: {missing_cols}")
        return False
    if extra_cols:
        print(f"ERROR: {df_name} has extra columns not required: {extra_cols}")
        return False
    # Check for columns that are present but all values are missing
    all_missing_cols = [col for col in required_columns if df[col].isnull().all()]
    if all_missing_cols:
        print(f"WARNING: {df_name} columns with all missing values: {all_missing_cols}")
    return True

def main():
    """
    Main function to process regression results and calculate standardized effect sizes.

    This function loads regression results and performance data, computes standardized effect sizes
    (beta coefficients), confidence intervals, effect size categories, and variance explained for all
    effects (not just significant ones). It outputs detailed CSV files with all effect sizes and a summary
    for reporting. The function also provides verbose progress reporting and error handling.

    Returns
    -------
    int
        0 if successful, 1 if an error occurred.
    """
    try:
        print("========== Starting standardized effect size calculation ==========")

        # Create outputs directory if it doesn't exist
        print("Checking/creating outputs directory...")
        os.makedirs('outputs', exist_ok=True)

        # Generate timestamp for output files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        print(f"Timestamp for output files: {timestamp}")

        # Find input files
        print("\n--- Searching for input files ---")

        mrt_accuracy_file = find_latest_file('outputs/mrt_accuracy_regression_results_*.csv')
        mrt_rt_file = find_latest_file('outputs/mrt_rt_regression_results_*.csv')
        vviq2_total_file = find_latest_file('outputs/vviq2_total_regression_results_*.csv')
        vviq2_subscale_file = find_latest_file('outputs/vviq2_subscale_regression_results_*.csv')
        mrt_performance_file = find_latest_file('outputs/mrt_performance_by_disparity_*.csv')
        vviq2_scores_file = find_latest_file('outputs/vviq2_scores_with_predictors_*.csv')

        print(f"  MRT accuracy file: {mrt_accuracy_file}")
        print(f"  MRT RT file: {mrt_rt_file}")
        print(f"  VVIQ2 total file: {vviq2_total_file}")
        print(f"  VVIQ2 subscale file: {vviq2_subscale_file}")
        print(f"  MRT performance file: {mrt_performance_file}")
        print(f"  VVIQ2 scores file: {vviq2_scores_file}")

        # Check if all required files exist
        required_files = [mrt_accuracy_file, mrt_rt_file, vviq2_total_file,
                          vviq2_subscale_file, mrt_performance_file, vviq2_scores_file]

        if any(f is None for f in required_files):
            print("ERROR: Some required input files not found! Aborting analysis.")
            return 1

        # Load regression results files
        print("\n--- Loading regression results files ---")

        try:
            mrt_accuracy_df = pd.read_csv(mrt_accuracy_file)
            print(f"  MRT accuracy columns: {list(mrt_accuracy_df.columns)}")
            print("  MRT accuracy first 3 rows:")
            print(mrt_accuracy_df.head(3))
            print(f"  Angular disparity values: {mrt_accuracy_df['angular_disparity'].unique()}")
        except Exception as e:
            print(f"Error loading MRT accuracy file: {e}")
            return 1

        try:
            mrt_rt_df = pd.read_csv(mrt_rt_file)
            print(f"\n  MRT RT columns: {list(mrt_rt_df.columns)}")
            print("  MRT RT first 3 rows:")
            print(mrt_rt_df.head(3))
            print(f"  Angular disparity values: {mrt_rt_df['angular_disparity'].unique()}")
        except Exception as e:
            print(f"Error loading MRT RT file: {e}")
            return 1

        try:
            vviq2_total_df = pd.read_csv(vviq2_total_file)
            print(f"\n  VVIQ2 total columns: {list(vviq2_total_df.columns)}")
            print("  VVIQ2 total first 3 rows:")
            print(vviq2_total_df.head(3))
        except Exception as e:
            print(f"Error loading VVIQ2 total file: {e}")
            return 1

        try:
            vviq2_subscale_df = pd.read_csv(vviq2_subscale_file)
            print(f"\n  VVIQ2 subscale columns: {list(vviq2_subscale_df.columns)}")
            print("  VVIQ2 subscale first 3 rows:")
            print(vviq2_subscale_df.head(3))
            print(f"  Subscale names: {vviq2_subscale_df['subscale_name'].unique()}")
        except Exception as e:
            print(f"Error loading VVIQ2 subscale file: {e}")
            return 1

        # Load performance data files for calculating standard deviations
        print("\n--- Loading performance data files ---")

        try:
            mrt_performance_df = pd.read_csv(mrt_performance_file)
            print(f"  MRT performance columns: {list(mrt_performance_df.columns)}")
            print("  MRT performance first 2 rows:")
            print(mrt_performance_df.head(2))
        except Exception as e:
            print(f"Error loading MRT performance file: {e}")
            return 1

        try:
            vviq2_scores_df = pd.read_csv(vviq2_scores_file)
            print(f"\n  VVIQ2 scores columns: {list(vviq2_scores_df.columns)}")
            print("  VVIQ2 scores first 2 rows:")
            print(vviq2_scores_df.head(2))
        except Exception as e:
            print(f"Error loading VVIQ2 scores file: {e}")
            return 1

        # Calculate standard deviations from performance data
        print("\n--- Calculating standard deviations ---")

        # SD of kappa (predictor variable)
        sd_kappa = mrt_performance_df['kappa'].std()
        print(f"  SD of kappa: {sd_kappa:.4f}")

        # SD of outcome variables
        accuracy_cols = ['accuracy_0deg', 'accuracy_50deg', 'accuracy_100deg', 'accuracy_150deg']
        rt_cols = ['median_rt_0deg', 'median_rt_50deg', 'median_rt_100deg', 'median_rt_150deg']

        sd_accuracies = {}
        sd_rts = {}

        for col in accuracy_cols:
            if col in mrt_performance_df.columns:
                sd_accuracies[col] = mrt_performance_df[col].std()
                print(f"  SD of {col}: {sd_accuracies[col]:.4f}")

        # For RT, use log-transformed RT columns if available, else apply log transformation on-the-fly
        for col in rt_cols:
            log_col = f'log_{col}'
            if log_col in mrt_performance_df.columns:
                sd_rts[col] = mrt_performance_df[log_col].std()
                print(f"  SD of {log_col} (log-transformed): {sd_rts[col]:.4f}")
            elif col in mrt_performance_df.columns:
                # Apply log transformation on-the-fly
                log_rt = np.log(mrt_performance_df[col].replace(0, np.nan).dropna())
                sd_rts[col] = log_rt.std()
                print(f"  SD of log-transformed {col}: {sd_rts[col]:.4f}")

        # SD of VVIQ2 variables
        vviq2_cols = ['vviq2_total_score', 'vviq2_familiar_person', 'vviq2_sunrise',
                      'vviq2_shop_front', 'vviq2_countryside', 'vviq2_driving',
                      'vviq2_beach', 'vviq2_railway_station', 'vviq2_garden']

        sd_vviq2 = {}
        for col in vviq2_cols:
            if col in vviq2_scores_df.columns:
                sd_vviq2[col] = vviq2_scores_df[col].std()
                print(f"  SD of {col}: {sd_vviq2[col]:.4f}")

        # Initialize list to store all effect size results
        all_effects = []

        print("\n--- Processing MRT accuracy results (significant effects only) ---")

        # Process MRT accuracy results (only significant effects)
        for idx, row in mrt_accuracy_df.iterrows():
            p_value = row['kappa_p_value_fdr']
            raw_coef = row['kappa_coefficient']
            raw_se = row['kappa_se']
            n_participants = row['n_participants']

            # Only process significant effects
            if p_value < 0.05:
                # Determine which accuracy column this corresponds to
                disparity = int(row['angular_disparity'])
                accuracy_col = f'accuracy_{disparity}deg'

                if accuracy_col in sd_accuracies:
                    sd_outcome = sd_accuracies[accuracy_col]

                    # Calculate standardized coefficient
                    beta = calculate_standardized_coefficient(raw_coef, sd_kappa, sd_outcome)

                    # Calculate standardized SE
                    scaling_factor = sd_kappa / sd_outcome
                    se_beta = raw_se * scaling_factor

                    # Calculate confidence interval (use 7 predictors: kappa + 6 controls)
                    ci_lower, ci_upper = calculate_confidence_interval(beta, se_beta, n_participants, k_predictors=7)

                    # Categorize effect size
                    effect_category = categorize_effect_size(beta)

                    # Calculate variance explained
                    var_explained = calculate_variance_explained(beta)

                    # Calculate CI width
                    ci_width = ci_upper - ci_lower

                    # Check practical significance
                    practical_significance_flag = abs(beta) >= 0.1

                    effect_data = {
                        'analysis_type': 'MRT_accuracy',
                        'outcome_variable': f'accuracy_{disparity}deg',
                        'kappa_coefficient_raw': raw_coef,
                        'kappa_coefficient_standardized': beta,
                        'standardized_se': se_beta,
                        'ci_lower_95': ci_lower,
                        'ci_upper_95': ci_upper,
                        'p_value_adjusted': p_value,
                        'effect_size_category': effect_category,
                        'variance_explained_percent': var_explained,
                        'ci_width': ci_width,
                        'practical_significance_flag': practical_significance_flag,
                        'n_participants': n_participants
                    }

                    all_effects.append(effect_data)
                    print(f"  {accuracy_col}: β = {beta:.4f}, p = {p_value:.4g}, Effect size: {effect_category}")

        print("\nProcessing MRT RT results (significant effects only)...")

        # Process MRT RT results (only significant effects)
        for idx, row in mrt_rt_df.iterrows():
            p_value = row['kappa_p_value_fdr']
            raw_coef = row['kappa_coefficient']
            raw_se = row['kappa_se']
            n_participants = row['n_participants']

            # Only process significant effects
            if p_value < 0.05:
                # Determine which RT column this corresponds to
                disparity = int(row['angular_disparity'])
                rt_col = f'median_rt_{disparity}deg'

                if rt_col in sd_rts:
                    sd_outcome = sd_rts[rt_col]

                    # Calculate standardized coefficient
                    beta = calculate_standardized_coefficient(raw_coef, sd_kappa, sd_outcome)

                    # Calculate standardized SE
                    scaling_factor = sd_kappa / sd_outcome
                    se_beta = raw_se * scaling_factor

                    # Calculate confidence interval (use 7 predictors: kappa + 6 controls)
                    ci_lower, ci_upper = calculate_confidence_interval(beta, se_beta, n_participants, k_predictors=7)

                    # Categorize effect size
                    effect_category = categorize_effect_size(beta)

                    # Calculate variance explained
                    var_explained = calculate_variance_explained(beta)

                    # Calculate CI width
                    ci_width = ci_upper - ci_lower

                    # Check practical significance
                    practical_significance_flag = abs(beta) >= 0.1

                    effect_data = {
                        'analysis_type': 'MRT_RT',
                        'outcome_variable': f'median_rt_{disparity}deg',
                        'kappa_coefficient_raw': raw_coef,
                        'kappa_coefficient_standardized': beta,
                        'standardized_se': se_beta,
                        'ci_lower_95': ci_lower,
                        'ci_upper_95': ci_upper,
                        'p_value_adjusted': p_value,
                        'effect_size_category': effect_category,
                        'variance_explained_percent': var_explained,
                        'ci_width': ci_width,
                        'practical_significance_flag': practical_significance_flag,
                        'n_participants': n_participants
                    }

                    all_effects.append(effect_data)
                    print(f"  {rt_col}: β = {beta:.4f}, p = {p_value:.4g}, Effect size: {effect_category}")

        print("\nProcessing VVIQ2 total results (significant effects only)...")

        # Process VVIQ2 total results (only significant effects)
        for idx, row in vviq2_total_df.iterrows():
            p_value = row['kappa_p_value']
            raw_coef = row['kappa_coefficient']
            raw_se = row['kappa_se']
            n_participants = row['n_participants']

            # Only process significant effects
            if p_value < 0.05:
                if 'vviq2_total_score' in sd_vviq2:
                    sd_outcome = sd_vviq2['vviq2_total_score']

                    # Calculate standardized coefficient
                    beta = calculate_standardized_coefficient(raw_coef, sd_kappa, sd_outcome)

                    # Calculate standardized SE
                    scaling_factor = sd_kappa / sd_outcome
                    se_beta = raw_se * scaling_factor

                    # Calculate confidence interval (use 7 predictors: kappa + 6 controls)
                    ci_lower, ci_upper = calculate_confidence_interval(beta, se_beta, n_participants, k_predictors=7)

                    # Categorize effect size
                    effect_category = categorize_effect_size(beta)

                    # Calculate variance explained
                    var_explained = calculate_variance_explained(beta)

                    # Calculate CI width
                    ci_width = ci_upper - ci_lower

                    # Check practical significance
                    practical_significance_flag = abs(beta) >= 0.1

                    effect_data = {
                        'analysis_type': 'VVIQ2_total',
                        'outcome_variable': 'vviq2_total_score',
                        'kappa_coefficient_raw': raw_coef,
                        'kappa_coefficient_standardized': beta,
                        'standardized_se': se_beta,
                        'ci_lower_95': ci_lower,
                        'ci_upper_95': ci_upper,
                        'p_value_adjusted': p_value,
                        'effect_size_category': effect_category,
                        'variance_explained_percent': var_explained,
                        'ci_width': ci_width,
                        'practical_significance_flag': practical_significance_flag,
                        'n_participants': n_participants
                    }

                    all_effects.append(effect_data)
                    print(f"  vviq2_total_score: β = {beta:.4f}, p = {p_value:.4g}, Effect size: {effect_category}")

        print("\nProcessing VVIQ2 subscale results (significant effects only)...")

        # Process VVIQ2 subscale results (only significant effects)
        for idx, row in vviq2_subscale_df.iterrows():
            p_value = row['kappa_p_value_fdr']
            subscale = row['subscale_name']
            raw_coef = row['kappa_coefficient']
            raw_se = row['kappa_se']
            n_participants = row['n_participants']

            # Only process significant effects
            if p_value < 0.05:
                outcome_col = subscale  # subscale_name is already the correct column name

                if outcome_col in sd_vviq2:
                    sd_outcome = sd_vviq2[outcome_col]

                    # Calculate standardized coefficient
                    beta = calculate_standardized_coefficient(raw_coef, sd_kappa, sd_outcome)

                    # Calculate standardized SE
                    scaling_factor = sd_kappa / sd_outcome
                    se_beta = raw_se * scaling_factor

                    # Calculate confidence interval (use 7 predictors: kappa + 6 controls)
                    ci_lower, ci_upper = calculate_confidence_interval(beta, se_beta, n_participants, k_predictors=7)

                    # Categorize effect size
                    effect_category = categorize_effect_size(beta)

                    # Calculate variance explained
                    var_explained = calculate_variance_explained(beta)

                    # Calculate CI width
                    ci_width = ci_upper - ci_lower

                    # Check practical significance
                    practical_significance_flag = abs(beta) >= 0.1

                    effect_data = {
                        'analysis_type': 'VVIQ2_subscale',
                        'outcome_variable': outcome_col,
                        'kappa_coefficient_raw': raw_coef,
                        'kappa_coefficient_standardized': beta,
                        'standardized_se': se_beta,
                        'ci_lower_95': ci_lower,
                        'ci_upper_95': ci_upper,
                        'p_value_adjusted': p_value,
                        'effect_size_category': effect_category,
                        'variance_explained_percent': var_explained,
                        'ci_width': ci_width,
                        'practical_significance_flag': practical_significance_flag,
                        'n_participants': n_participants
                    }

                    all_effects.append(effect_data)
                    print(f"  {outcome_col}: β = {beta:.4f}, p = {p_value:.4g}, Effect size: {effect_category}")
        
        print(f"\nTotal significant effects processed: {len(all_effects)}")

        if len(all_effects) == 0:
            print("No significant effects found to analyze!")
            # Still create empty output files
            empty_effects_df = pd.DataFrame(columns=[
                'analysis_type', 'outcome_variable', 'kappa_coefficient_raw',
                'kappa_coefficient_standardized', 'standardized_se', 'ci_lower_95',
                'ci_upper_95', 'p_value_adjusted', 'effect_size_category',
                'variance_explained_percent', 'ci_width', 'practical_significance_flag',
                'n_participants'
            ])

            empty_summary_df = pd.DataFrame(columns=[
                'relationship_description', 'standardized_beta', 'ci_lower_95',
                'ci_upper_95', 'p_value', 'effect_magnitude', 'interpretation',
                'statistical_power_note'
            ])

            # Save empty files
            effects_output_file = f'outputs/standardized_effect_sizes_{timestamp}.csv'
            summary_output_file = f'outputs/effect_size_summary_{timestamp}.csv'

            empty_effects_df.to_csv(effects_output_file, index=False)
            empty_summary_df.to_csv(summary_output_file, index=False)

            print(f"Empty effect sizes file saved: {effects_output_file}")
            print(f"Empty summary file saved: {summary_output_file}")
            print("Finished execution")
            return 0

        # Create DataFrame from all effects
        effects_df = pd.DataFrame(all_effects)

        print("\n--- Effect sizes DataFrame ---")
        print("  Columns:", list(effects_df.columns))
        print("  First 2 rows:")
        print(effects_df.head(2))

        # Sort by absolute standardized coefficient
        print("  Sorting effects by absolute standardized coefficient...")
        effects_df['abs_beta'] = effects_df['kappa_coefficient_standardized'].abs()
        effects_df = effects_df.sort_values('abs_beta', ascending=False)
        effects_df = effects_df.drop('abs_beta', axis=1)

        print("\n--- Effects sorted by magnitude (significant only) ---")
        for idx, row in effects_df.iterrows():
            print(f"  {row['analysis_type']} - {row['outcome_variable']}: β = {row['kappa_coefficient_standardized']:.4f} ({row['effect_size_category']})")

        # Create summary DataFrame
        print("\n--- Creating effect size summary ---")

        summary_data = []
        for idx, row in effects_df.iterrows():
            # Create relationship description
            if row['analysis_type'] == 'MRT_accuracy':
                relationship_desc = f"Kappa → MRT {row['outcome_variable']}"
            elif row['analysis_type'] == 'MRT_RT':
                relationship_desc = f"Kappa → MRT {row['outcome_variable']}"
            elif row['analysis_type'] == 'VVIQ2_total':
                relationship_desc = "Kappa → VVIQ2 total score"
            elif row['analysis_type'] == 'VVIQ2_subscale':
                subscale_name = row['outcome_variable'].replace('vviq2_', '').replace('_', ' ').title()
                relationship_desc = f"Kappa → VVIQ2 {subscale_name}"
            else:
                relationship_desc = f"Kappa → {row['outcome_variable']}"

            # Create interpretation
            beta = row['kappa_coefficient_standardized']
            effect_cat = row['effect_size_category']
            ci_lower = row['ci_lower_95']
            ci_upper = row['ci_upper_95']

            if beta > 0:
                direction = "positive"
            else:
                direction = "negative"

            interpretation = f"{effect_cat.capitalize()} {direction} association between kappa and {row['outcome_variable']}"

            # Statistical power note
            n = row['n_participants']
            if n < 30:
                power_note = "Small sample size may limit statistical power"
            elif n < 50:
                power_note = "Moderate sample size provides adequate power for medium effects"
            else:
                power_note = "Large sample size provides good statistical power"

            summary_data.append({
                'relationship_description': relationship_desc,
                'standardized_beta': beta,
                'ci_lower_95': ci_lower,
                'ci_upper_95': ci_upper,
                'p_value': row['p_value_adjusted'],
                'effect_magnitude': effect_cat,
                'interpretation': interpretation,
                'statistical_power_note': power_note
            })

        summary_df = pd.DataFrame(summary_data)

        print("\n--- Summary DataFrame ---")
        print("  Columns:", list(summary_df.columns))
        print("  First 2 rows:")
        print(summary_df.head(2))

        # Validate output columns before saving
        print("\n--- Validating output columns ---")
        required_effects_cols = [
            'analysis_type', 'outcome_variable', 'kappa_coefficient_raw',
            'kappa_coefficient_standardized', 'standardized_se', 'ci_lower_95',
            'ci_upper_95', 'p_value_adjusted', 'effect_size_category',
            'variance_explained_percent', 'ci_width', 'practical_significance_flag',
            'n_participants'
        ]
        required_summary_cols = [
            'relationship_description', 'standardized_beta', 'ci_lower_95',
            'ci_upper_95', 'p_value', 'effect_magnitude', 'interpretation',
            'statistical_power_note'
        ]
        effects_valid = validate_output_columns(effects_df, required_effects_cols, df_name="Effects DataFrame")
        summary_valid = validate_output_columns(summary_df, required_summary_cols, df_name="Summary DataFrame")
        if not effects_valid or not summary_valid:
            print("ERROR: Output validation failed. Aborting file save.")
            return 1

        # Explicitly select only required columns before saving
        effects_df = effects_df[required_effects_cols]
        summary_df = summary_df[required_summary_cols]

        # Save output files
        effects_output_file = f'outputs/standardized_effect_sizes_{timestamp}.csv'
        summary_output_file = f'outputs/effect_size_summary_{timestamp}.csv'

        print(f"\n--- Saving standardized effect sizes to: {effects_output_file} ---")
        effects_df.to_csv(effects_output_file, index=False)

        print(f"--- Saving effect size summary to: {summary_output_file} ---")
        summary_df.to_csv(summary_output_file, index=False)

        print("\n--- Final summary statistics (significant effects only) ---")
        print(f"  Total significant effects: {len(all_effects)}")
        print(f"  Large effects: {len(effects_df[effects_df['effect_size_category'] == 'large'])}")
        print(f"  Medium effects: {len(effects_df[effects_df['effect_size_category'] == 'medium'])}")
        print(f"  Small effects: {len(effects_df[effects_df['effect_size_category'] == 'small'])}")
        print(f"  Negligible effects: {len(effects_df[effects_df['effect_size_category'] == 'negligible'])}")
        print(f"  Not applicable effects: {len(effects_df[effects_df['effect_size_category'] == 'not_applicable'])}")

        if len(effects_df) > 0:
            strongest_effect = effects_df.iloc[0]
            print(f"  Strongest effect: {strongest_effect['analysis_type']} - {strongest_effect['outcome_variable']} (β = {strongest_effect['kappa_coefficient_standardized']:.4f})")

        print("\n========== Finished execution ==========")
        return 0

    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
