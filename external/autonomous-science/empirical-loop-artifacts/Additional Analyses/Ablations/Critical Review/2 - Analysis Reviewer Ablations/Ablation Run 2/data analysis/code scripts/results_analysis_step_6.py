#!/usr/bin/env python3
"""
MRT Accuracy and Reaction Time Regression Analysis Script

This script performs logistic regression analysis on MRT accuracy and linear regression 
analysis on MRT reaction times across different angular disparities, controlling for 
various cognitive and engagement measures.
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Import regression libraries
try:
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.stats.multitest import fdrcorrection
except ImportError:
    print("Error: statsmodels not available. Installing...")
    os.system("pip install statsmodels")
    import statsmodels.api as sm
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.stats.multitest import fdrcorrection

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    -----------
    pattern : str
        File pattern to match (with <TIMESTAMP> placeholder)
        
    Returns:
    --------
    str or None
        Path to most recent file, or None if no files found
    """
    # Convert pattern with <TIMESTAMP> to glob pattern
    glob_pattern = pattern.replace('<TIMESTAMP>', '*')
    
    files = glob.glob(glob_pattern)
    if not files:
        return None
    
    # Sort by modification time and return most recent
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files[0]

def load_and_validate_data():
    """
    Load and validate input data files.
    
    Returns:
    --------
    tuple
        (trial_data, mixture_params, individual_measures) DataFrames
    """
    print("=== LOADING AND VALIDATING INPUT DATA ===")
    
    # Find input files
    trial_file = find_most_recent_file('outputs/trial_level_cleaned_data_<TIMESTAMP>.csv')
    mixture_file = find_most_recent_file('outputs/vwm_mixture_model_parameters_<TIMESTAMP>.csv')
    individual_file = find_most_recent_file('outputs/individual_level_measures_<TIMESTAMP>.csv')
    
    if not trial_file:
        print("ERROR: No trial level data file found!")
        return None, None, None
    if not mixture_file:
        print("ERROR: No mixture model parameters file found!")
        return None, None, None
    if not individual_file:
        print("ERROR: No individual measures file found!")
        return None, None, None
        
    print(f"Loading trial data from: {trial_file}")
    print(f"Loading mixture parameters from: {mixture_file}")
    print(f"Loading individual measures from: {individual_file}")
    
    # Load data
    trial_data = pd.read_csv(trial_file)
    mixture_params = pd.read_csv(mixture_file)
    individual_measures = pd.read_csv(individual_file)
    
    print(f"\nTrial data shape: {trial_data.shape}")
    print("Trial data columns:", list(trial_data.columns))
    print("First 3 rows of trial data:")
    print(trial_data.head(3))
    
    print(f"\nMixture parameters shape: {mixture_params.shape}")
    print("Mixture parameters columns:", list(mixture_params.columns))
    print("First 3 rows of mixture parameters:")
    print(mixture_params.head(3))
    
    print(f"\nIndividual measures shape: {individual_measures.shape}")
    print("Individual measures columns:", list(individual_measures.columns))
    print("First 3 rows of individual measures:")
    print(individual_measures.head(3))
    
    # Validate required columns
    required_trial_cols = ['participantId', 'isPractice', 'MRT_trial', 'MRT_angle_degrees', 
                          'MRT_isCorrect', 'MRT_rt_ms', 'MRT_trial_excluded', 'participant_meets_minimum_trials']
    required_mixture_cols = ['participantId', 'kappa_vonmises', 'vonmises_convergence']
    required_individual_cols = ['participantId', 'vwm_mean_accuracy_degrees', 'vwm_rt_cv', 
                               'mrt_rt_cv', 'vwm_timeout_rate', 'engagement_index']
    
    missing_trial_cols = [col for col in required_trial_cols if col not in trial_data.columns]
    missing_mixture_cols = [col for col in required_mixture_cols if col not in mixture_params.columns]
    missing_individual_cols = [col for col in required_individual_cols if col not in individual_measures.columns]
    
    if missing_trial_cols:
        print(f"WARNING: Missing trial columns: {missing_trial_cols}")
    if missing_mixture_cols:
        print(f"WARNING: Missing mixture columns: {missing_mixture_cols}")
    if missing_individual_cols:
        print(f"WARNING: Missing individual columns: {missing_individual_cols}")
    
    # Print unique values for key experimental design parameters
    print("\n=== EXPERIMENTAL DESIGN PARAMETERS ===")
    
    if 'isPractice' in trial_data.columns:
        print("Unique isPractice values:", sorted(trial_data['isPractice'].dropna().unique()))
    
    if 'MRT_angle_degrees' in trial_data.columns:
        print("Unique MRT_angle_degrees values:", sorted(trial_data['MRT_angle_degrees'].dropna().unique()))
    
    if 'MRT_isCorrect' in trial_data.columns:
        print("Unique MRT_isCorrect values:", sorted(trial_data['MRT_isCorrect'].dropna().unique()))
    
    if 'MRT_trial_excluded' in trial_data.columns:
        print("Unique MRT_trial_excluded values:", sorted(trial_data['MRT_trial_excluded'].dropna().unique()))
    
    if 'participant_meets_minimum_trials' in trial_data.columns:
        print("Unique participant_meets_minimum_trials values:", sorted(trial_data['participant_meets_minimum_trials'].dropna().unique()))
    
    if 'vonmises_convergence' in mixture_params.columns:
        print("Unique vonmises_convergence values:", sorted(mixture_params['vonmises_convergence'].dropna().unique()))
    
    # Print variable types for measured variables
    print("\n=== MEASURED VARIABLE TYPES ===")
    if 'MRT_rt_ms' in trial_data.columns:
        print(f"MRT_rt_ms type: {trial_data['MRT_rt_ms'].dtype}")
    if 'kappa_vonmises' in mixture_params.columns:
        print(f"kappa_vonmises type: {mixture_params['kappa_vonmises'].dtype}")
    if 'vwm_mean_accuracy_degrees' in individual_measures.columns:
        print(f"vwm_mean_accuracy_degrees type: {individual_measures['vwm_mean_accuracy_degrees'].dtype}")
    
    return trial_data, mixture_params, individual_measures


def prepare_mrt_data(merged_data):
    """
    Prepare MRT performance measures by angular disparity.
    
    Parameters:
    -----------
    merged_data : pd.DataFrame
        Merged dataset
        
    Returns:
    --------
    pd.DataFrame
        Prepared MRT data for analysis
    """
    print("\n=== PREPARING MRT DATA ===")
    
    # Filter to test trials only
    print(f"Total trials before filtering: {len(merged_data)}")
    
    # Apply filters step by step
    mrt_data = merged_data.copy()
    
    # Filter practice trials
    if 'isPractice' in mrt_data.columns:
        initial_count = len(mrt_data)
        mrt_data = mrt_data[mrt_data['isPractice'] == False]
        print(f"After removing practice trials: {len(mrt_data)} (removed {initial_count - len(mrt_data)})")
    
    # Filter null MRT trials
    if 'MRT_trial' in mrt_data.columns:
        initial_count = len(mrt_data)
        mrt_data = mrt_data[mrt_data['MRT_trial'].notna()]
        print(f"After removing null MRT trials: {len(mrt_data)} (removed {initial_count - len(mrt_data)})")
    
    # Filter excluded trials
    if 'MRT_trial_excluded' in mrt_data.columns:
        initial_count = len(mrt_data)
        mrt_data = mrt_data[mrt_data['MRT_trial_excluded'] == False]
        print(f"After removing excluded trials: {len(mrt_data)} (removed {initial_count - len(mrt_data)})")
    
    print(f"Final valid MRT trials: {len(mrt_data)}")
    print(f"Unique participants in MRT data: {mrt_data['participantId'].nunique()}")
    
    # Check angular disparities
    if 'MRT_angle_degrees' in mrt_data.columns:
        angles = sorted(mrt_data['MRT_angle_degrees'].unique())
        print(f"Available angular disparities: {angles}")
        
        # Count trials per angle
        angle_counts = mrt_data['MRT_angle_degrees'].value_counts().sort_index()
        print("Trials per angular disparity:")
        for angle, count in angle_counts.items():
            print(f"  {angle}°: {count} trials")
    
    # Check correct/incorrect distribution
    if 'MRT_isCorrect' in mrt_data.columns:
        correct_counts = mrt_data['MRT_isCorrect'].value_counts()
        print(f"Correct responses: {correct_counts.get(True, 0)}")
        print(f"Incorrect responses: {correct_counts.get(False, 0)}")
    
    print("First 2 rows of prepared MRT data:")
    print(mrt_data.head(2))
    
    return mrt_data

def calculate_participant_measures(mrt_data):
    """
    Calculate participant-level measures for each angular disparity.
    
    Parameters:
    -----------
    mrt_data : pd.DataFrame
        Prepared MRT trial data
        
    Returns:
    --------
    pd.DataFrame
        Participant-level measures by angular disparity
    """
    print("\n=== CALCULATING PARTICIPANT MEASURES ===")
    
    participant_measures = []
    
    angles = sorted(mrt_data['MRT_angle_degrees'].unique())
    
    for angle in angles:
        print(f"\nProcessing {angle}° angular disparity...")
        
        angle_data = mrt_data[mrt_data['MRT_angle_degrees'] == angle].copy()
        print(f"  Trials at {angle}°: {len(angle_data)}")
        
        # Calculate accuracy per participant
        accuracy_stats = angle_data.groupby('participantId').agg({
            'MRT_isCorrect': ['count', 'sum']
        }).round(4)
        accuracy_stats.columns = ['total_trials', 'correct_trials']
        accuracy_stats['mrt_accuracy'] = accuracy_stats['correct_trials'] / accuracy_stats['total_trials']
        
        # Calculate median RT for correct responses only
        correct_trials = angle_data[angle_data['MRT_isCorrect'] == True]
        print(f"  Correct trials at {angle}°: {len(correct_trials)}")
        
        if len(correct_trials) > 0:
            rt_stats = correct_trials.groupby('participantId')['MRT_rt_ms'].median()
            rt_stats.name = 'mrt_rt_median'
        else:
            rt_stats = pd.Series(dtype=float, name='mrt_rt_median')
        
        # Combine measures
        participant_stats = accuracy_stats.join(rt_stats, how='left')
        participant_stats['angular_disparity'] = angle
        participant_stats = participant_stats.reset_index()
        
        print(f"  Participants with data at {angle}°: {len(participant_stats)}")
        print(f"  Mean accuracy at {angle}°: {participant_stats['mrt_accuracy'].mean():.3f}")
        if len(participant_stats.dropna(subset=['mrt_rt_median'])) > 0:
            print(f"  Mean RT at {angle}°: {participant_stats['mrt_rt_median'].mean():.1f} ms")
        
        participant_measures.append(participant_stats)
    
    # Combine all angular disparities
    all_measures = pd.concat(participant_measures, ignore_index=True)
    
    print(f"\nTotal participant-angle combinations: {len(all_measures)}")
    print("First 2 rows of participant measures:")
    print(all_measures.head(2))
    
    return all_measures

def add_covariates_and_transform(individual_measures, mixture_params):
    """
    Create participant-level covariates and apply z-score transformations.
    
    Parameters:
    -----------
    individual_measures : pd.DataFrame
        Individual-level measures
    mixture_params : pd.DataFrame
        Mixture model parameters (convergent only)
        
    Returns:
    --------
    pd.DataFrame
        Participant-level covariates with z-scored variables
    """
    print("\n=== CREATING PARTICIPANT-LEVEL COVARIATES AND TRANSFORMATIONS ===")
    
    # Merge participant-level data
    participant_covariates = individual_measures.merge(
        mixture_params[['participantId', 'kappa_vonmises']], 
        on='participantId', how='inner'
    )
    
    print(f"Participant covariates shape: {participant_covariates.shape}")
    print(f"Unique participants: {participant_covariates['participantId'].nunique()}")
    
    # Z-standardize continuous control variables on participant-level data
    control_vars = ['vwm_mean_accuracy_degrees', 'vwm_rt_cv', 'mrt_rt_cv', 'vwm_timeout_rate', 'engagement_index']
    
    for var in control_vars:
        if var in participant_covariates.columns:
            z_var = f'z_{var.replace("_degrees", "")}'
            participant_covariates[z_var] = stats.zscore(participant_covariates[var], nan_policy='omit')
            print(f"Z-standardized {var} -> {z_var}")
            print(f"  Mean: {participant_covariates[z_var].mean():.6f}, Std: {participant_covariates[z_var].std():.6f}")
    
    print("Participant covariates columns:", list(participant_covariates.columns))
    return participant_covariates

def run_logistic_regression(trial_analysis_data):
    """
    Run logistic regression models for MRT accuracy.
    
    Parameters:
    -----------
    trial_analysis_data : pd.DataFrame
        Trial-level MRT data with covariates already merged
        
    Returns:
    --------
    list
        List of regression results
    """
    print("\n=== RUNNING LOGISTIC REGRESSION FOR MRT ACCURACY ===")
    
    results = []
    angles = sorted(trial_analysis_data['MRT_angle_degrees'].unique())
    
    print(f"Available columns in trial data: {list(trial_analysis_data.columns)}")

    for angle in angles:
        print(f"\n--- Logistic regression for {angle}° ---")

        # Filter data for this angle
        angle_data = trial_analysis_data[
            trial_analysis_data['MRT_angle_degrees'] == angle
        ].copy()

        print(f"Trials at {angle}°: {len(angle_data)}")
        print(f"Participants at {angle}°: {angle_data['participantId'].nunique()}")

        # Remove rows with missing data
        analysis_cols = ['MRT_isCorrect', 'kappa_vonmises', 'z_vwm_mean_accuracy', 
                        'z_vwm_rt_cv', 'z_mrt_rt_cv', 'z_vwm_timeout_rate', 'z_engagement_index']

        # Check which columns exist
        missing_cols = [col for col in analysis_cols if col not in angle_data.columns]
        if missing_cols:
            print(f"Missing columns: {missing_cols}")
            continue

        complete_data = angle_data.dropna(subset=analysis_cols)
        print(f"Complete cases: {len(complete_data)}")

        if len(complete_data) < 10:
            print(f"Insufficient data for {angle}° - skipping")
            continue

        # Prepare variables
        y = complete_data['MRT_isCorrect'].astype(int)
        X_vars = ['kappa_vonmises', 'z_vwm_mean_accuracy', 'z_vwm_rt_cv', 
                  'z_mrt_rt_cv', 'z_vwm_timeout_rate', 'z_engagement_index']
        X = complete_data[X_vars]
        X = sm.add_constant(X)  # Add intercept

        print(f"Predictors: {X_vars}")
        print(f"Outcome distribution: {y.value_counts().to_dict()}")

        try:
            # Fit logistic regression
            model = sm.Logit(y, X)
            result = model.fit(disp=False)

            print(f"Model converged: {result.mle_retvals['converged']}")
            print(f"Pseudo R-squared: {result.prsquared:.4f}")

            # Calculate VIFs
            vifs = {}
            X_no_const = X.drop('const', axis=1)
            for i, var in enumerate(X_no_const.columns):
                try:
                    vif = variance_inflation_factor(X_no_const.values, i)
                    vifs[var] = vif if np.isfinite(vif) else np.nan
                except:
                    vifs[var] = np.nan

            # Extract results for each predictor
            for var in X_vars:
                coef = result.params[var]
                se = result.bse[var]
                p_val = result.pvalues[var]
                ci_lower, ci_upper = result.conf_int().loc[var]
                vif = vifs.get(var, np.nan)

                results.append({
                    'angular_disparity': angle,
                    'predictor': var,
                    'coefficient': coef,
                    'standard_error': se,
                    'p_value': p_val,
                    'confidence_interval_lower': ci_lower,
                    'confidence_interval_upper': ci_upper,
                    'VIF': vif,
                    'model_r_squared': result.prsquared,
                    'n_participants': complete_data['participantId'].nunique(),
                    'n_trials': len(complete_data)
                })

                print(f"  {var}: coef={coef:.4f}, se={se:.4f}, p={p_val:.4f}, VIF={vif:.2f}")

        except Exception as e:
            print(f"Error fitting model for {angle}°: {e}")
            continue
    
    print(f"\nCompleted logistic regression for {len(results)} predictor-angle combinations")
    return results

def run_linear_regression(analysis_data):
    """
    Run linear regression models for MRT reaction times.
    
    Parameters:
    -----------
    analysis_data : pd.DataFrame
        Analysis data with log-transformed RTs
        
    Returns:
    --------
    list
        List of regression results
    """
    print("\n=== RUNNING LINEAR REGRESSION FOR MRT REACTION TIMES ===")
    
    results = []
    angles = sorted(analysis_data['angular_disparity'].unique())

    for angle in angles:
        print(f"\n--- Linear regression for {angle}° ---")

        # Filter data for this angle
        angle_data = analysis_data[
            analysis_data['angular_disparity'] == angle
        ].copy()

        print(f"Participants at {angle}°: {len(angle_data)}")

        # Remove rows with missing data
        analysis_cols = ['log_mrt_rt', 'kappa_vonmises', 'z_vwm_mean_accuracy', 
                        'z_vwm_rt_cv', 'z_mrt_rt_cv', 'z_vwm_timeout_rate', 'z_engagement_index']

        complete_data = angle_data.dropna(subset=analysis_cols)
        print(f"Complete cases: {len(complete_data)}")

        if len(complete_data) < 10:
            print(f"Insufficient data for {angle}° - skipping")
            continue

        # Prepare variables
        y = complete_data['log_mrt_rt']
        X_vars = ['kappa_vonmises', 'z_vwm_mean_accuracy', 'z_vwm_rt_cv', 
                  'z_mrt_rt_cv', 'z_vwm_timeout_rate', 'z_engagement_index']
        X = complete_data[X_vars]
        X = sm.add_constant(X)  # Add intercept

        print(f"Predictors: {X_vars}")
        print(f"Outcome mean: {y.mean():.4f}, std: {y.std():.4f}")

        try:
            # Fit linear regression
            model = sm.OLS(y, X)
            result = model.fit()

            print(f"R-squared: {result.rsquared:.4f}")
            print(f"Adj R-squared: {result.rsquared_adj:.4f}")

            # Calculate VIFs
            vifs = {}
            X_no_const = X.drop('const', axis=1)
            for i, var in enumerate(X_no_const.columns):
                try:
                    vif = variance_inflation_factor(X_no_const.values, i)
                    vifs[var] = vif if np.isfinite(vif) else np.nan
                except:
                    vifs[var] = np.nan

            # Extract results for each predictor
            for var in X_vars:
                coef = result.params[var]
                se = result.bse[var]
                p_val = result.pvalues[var]
                ci_lower, ci_upper = result.conf_int().loc[var]
                vif = vifs.get(var, np.nan)

                results.append({
                    'angular_disparity': angle,
                    'predictor': var,
                    'coefficient': coef,
                    'standard_error': se,
                    'p_value': p_val,
                    'confidence_interval_lower': ci_lower,
                    'confidence_interval_upper': ci_upper,
                    'VIF': vif,
                    'model_r_squared': result.rsquared,
                    'n_participants': len(complete_data),
                    'n_trials': int(complete_data['total_trials'].sum())  # Corrected n_trials calculation
                })

                print(f"  {var}: coef={coef:.4f}, se={se:.4f}, p={p_val:.4f}, VIF={vif:.2f}")

        except Exception as e:
            print(f"Error fitting model for {angle}°: {e}")
            continue
    
    print(f"\nCompleted linear regression for {len(results)} predictor-angle combinations")
    return results

def apply_fdr_correction(results):
    """
    Apply False Discovery Rate correction for multiple comparisons.
    
    Parameters:
    -----------
    results : list
        List of regression results
        
    Returns:
    --------
    list
        Results with FDR-corrected p-values
    """
    print("\n=== APPLYING FDR CORRECTION ===")
    
    if not results:
        print("No results to correct")
        return results
    
    # Extract p-values
    p_values = [r['p_value'] for r in results]
    print(f"Correcting {len(p_values)} p-values")
    
    # Apply FDR correction
    rejected, p_corrected = fdrcorrection(p_values, alpha=0.05, method='indep')
    
    # Update results
    for i, result in enumerate(results):
        # Overwrite p_value with corrected value, do not add new columns
        result['p_value'] = p_corrected[i]

    print(f"FDR-significant results: {sum(rejected)}/{len(rejected)}")

    return results

def save_results(accuracy_results, rt_results):
    """
    Save regression results to CSV files.
    
    Parameters:
    -----------
    accuracy_results : list
        Logistic regression results
    rt_results : list
        Linear regression results
    """
    print("\n=== SAVING RESULTS ===")
    
    # Create outputs directory
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save accuracy results
    if accuracy_results:
        accuracy_df = pd.DataFrame(accuracy_results)
        accuracy_file = f'outputs/mrt_accuracy_regression_results_{timestamp}.csv'
        accuracy_df.to_csv(accuracy_file, index=False)
        print(f"Saved accuracy results to: {accuracy_file}")
        print(f"Accuracy results shape: {accuracy_df.shape}")
        print("Accuracy results columns:", list(accuracy_df.columns))
        print("First 2 rows of accuracy results:")
        print(accuracy_df.head(2))
    else:
        print("No accuracy results to save")
    
    # Save RT results
    if rt_results:
        rt_df = pd.DataFrame(rt_results)
        rt_file = f'outputs/mrt_reaction_time_regression_results_{timestamp}.csv'
        rt_df.to_csv(rt_file, index=False)
        print(f"Saved RT results to: {rt_file}")
        print(f"RT results shape: {rt_df.shape}")
        print("RT results columns:", list(rt_df.columns))
        print("First 2 rows of RT results:")
        print(rt_df.head(2))
    else:
        print("No RT results to save")

def main():
    """
    Main function to execute the MRT regression analysis.
    
    Returns:
    --------
    int
        0 for success, 1 for error
    """
    try:
        print("Starting MRT Accuracy and Reaction Time Regression Analysis")
        print("=" * 60)
        
        # Load and validate data
        trial_data, mixture_params, individual_measures = load_and_validate_data()
        if trial_data is None:
            print("ERROR: Failed to load required data files")
            return 1
        
        # Filter to convergent mixture models only
        print(f"\n=== FILTERING TO CONVERGENT MIXTURE MODELS ===")
        print(f"Total participants in mixture parameters: {len(mixture_params)}")
        convergent_mixture = mixture_params[mixture_params['vonmises_convergence'] == True].copy()
        print(f"Participants with convergent mixture models: {len(convergent_mixture)}")
        
        # Create participant-level covariates with correct z-scoring
        participant_covariates = add_covariates_and_transform(individual_measures, convergent_mixture)
        
        # Create fully merged dataset early in pipeline
        print(f"\n=== MERGING TRIAL DATA WITH COVARIATES ===")
        merged_data = trial_data.merge(participant_covariates, on='participantId', how='inner')
        print(f"Merged data shape: {merged_data.shape}")
        print(f"Participants in merged data: {merged_data['participantId'].nunique()}")
        
        if len(merged_data) == 0:
            print("ERROR: No data after merging")
            return 1
        
        # Prepare trial-level MRT data for logistic regression
        mrt_trial_data = prepare_mrt_data(merged_data)
        if len(mrt_trial_data) == 0:
            print("ERROR: No valid MRT trial data")
            return 1
        
        # Calculate participant measures for linear regression
        participant_measures = calculate_participant_measures(mrt_trial_data)
        if len(participant_measures) == 0:
            print("ERROR: No participant measures calculated")
            return 1
        
        # Prepare data for linear regression
        rt_analysis_data = participant_measures.merge(participant_covariates, on='participantId', how='left')
        rt_analysis_data['log_mrt_rt'] = np.log(rt_analysis_data['mrt_rt_median'])
        
        print(f"RT analysis data shape: {rt_analysis_data.shape}")
        print("RT analysis data columns:", list(rt_analysis_data.columns))
        
        # Run logistic regression for accuracy (simplified call)
        accuracy_results = run_logistic_regression(mrt_trial_data)
        
        # Run linear regression for reaction times (simplified call)
        rt_results = run_linear_regression(rt_analysis_data)
        
        # Apply FDR correction
        if accuracy_results:
            accuracy_results = apply_fdr_correction(accuracy_results)
        if rt_results:
            rt_results = apply_fdr_correction(rt_results)
        
        # Save results
        save_results(accuracy_results, rt_results)
        
        print("\n" + "=" * 60)
        print("Analysis completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: Analysis failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
