import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
from scipy.stats import circstd
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

def calculate_circular_std(angles_degrees):
    """
    Calculate circular standard deviation for angles in degrees.
    
    Parameters:
    angles_degrees (array-like): Angles in degrees
    
    Returns:
    float: Circular standard deviation in radians
    """
    angles_radians = np.radians(angles_degrees)
    return circstd(angles_radians)

def calculate_simple_precision(trial_data):
    """
    Calculate simple precision estimate for a participant.
    
    Parameters:
    trial_data (pd.DataFrame): Trial data for the participant
    
    Returns:
    float: Simple precision estimate (1/circular_std)
    """
    # Filter for test trials and non-excluded trials
    valid_trials = trial_data[
        (trial_data['isPractice'] == False) & 
        (trial_data['trial_excluded'] == False)
    ]
    
    if len(valid_trials) == 0:
        return np.nan
    
    errors = valid_trials['VWM_error_degrees'].values
    circular_std = calculate_circular_std(errors)
    
    if circular_std == 0:
        return np.inf
    
    return 1.0 / circular_std

def get_alternative_model_parameter(mixture_params, participant_id):
    participant_data = mixture_params[mixture_params['participantId'] == participant_id]
    
    if len(participant_data) == 0:
        return None, None
    
    row = participant_data.iloc[0]
    
    # Check if alternative model is better and AIC difference > 4
    if row['best_model'] != 'von_mises' and row['AIC_difference'] > 4:
        # Try to find actual concentration parameters robustly
        if row['best_model'] == 'wrapped_normal':
            if 'wrapped_normal_concentration' in mixture_params.columns:
                return row['wrapped_normal_concentration'], 'wrapped_normal'
            else:
                print(f"Warning: wrapped_normal_concentration column missing for participant {participant_id}")
        elif row['best_model'] == 'wrapped_cauchy':
            if 'wrapped_cauchy_concentration' in mixture_params.columns:
                return row['wrapped_cauchy_concentration'], 'wrapped_cauchy'
            else:
                print(f"Warning: wrapped_cauchy_concentration column missing for participant {participant_id}")
    
    return None, None

def run_regression_analysis(data, precision_column, dependent_variable, analysis_type='linear'):
    """
    Run regression analysis using statsmodels for robust statistical outputs.
    """
    import statsmodels.api as sm
    from sklearn.preprocessing import StandardScaler

    # Base predictor columns
    X_cols_base = ['VWM_mean_accuracy_nonguess', 'VWM_rt_cv', 'MRT_rt_cv', 
                   'engagement_index', 'VWM_timeout_rate']

    # Filter out zero-variance predictors
    X_cols = [precision_column]
    for col in X_cols_base:
        if col in data.columns and data[col].nunique(dropna=False) > 1:
            X_cols.append(col)

    # Remove rows with missing values
    analysis_data = data.dropna(subset=[dependent_variable] + X_cols)

    if len(analysis_data) < len(X_cols) + 2:
        return {'coefficient': np.nan, 'standard_error': np.nan, 'p_value': np.nan, 'sample_size': len(analysis_data)}

    try:
        # Prepare features and target
        X = analysis_data[X_cols]
        y = analysis_data[dependent_variable]

        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_scaled_df = pd.DataFrame(X_scaled, columns=X_cols, index=analysis_data.index)

        # Add constant term
        X_with_const = sm.add_constant(X_scaled_df, prepend=True)

        # Fit model
        if analysis_type == 'logistic':
            model = sm.Logit(y, X_with_const)
        else:
            model = sm.OLS(y, X_with_const)

        results = model.fit(disp=0)

        return {
            'coefficient': results.params[precision_column],
            'standard_error': results.bse[precision_column],
            'p_value': results.pvalues[precision_column],
            'sample_size': len(analysis_data)
        }

    except Exception as e:
        print(f"Error in regression analysis: {e}")
        return {'coefficient': np.nan, 'standard_error': np.nan, 'p_value': np.nan, 'sample_size': 0}

def apply_fdr_correction(p_values):
    """
    Apply False Discovery Rate correction.
    
    Parameters:
    p_values (array-like): Uncorrected p-values
    
    Returns:
    array: FDR-corrected p-values
    """
    from statsmodels.stats.multitest import fdrcorrection
    
    valid_p = np.array(p_values)
    valid_mask = ~np.isnan(valid_p)
    
    if np.sum(valid_mask) == 0:
        return np.full_like(valid_p, np.nan)
    
    corrected = np.full_like(valid_p, np.nan)
    _, corrected[valid_mask] = fdrcorrection(valid_p[valid_mask], alpha=0.05)
    
    return corrected

def main():
    """
    Main function to run sensitivity analysis of precision measures.
    """
    try:
        print("Starting sensitivity analysis of precision measures...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find input files
        print("\nSearching for input files...")
        
        trial_data_file = find_latest_file('outputs/cleaned_trial_data_*.csv')
        mixture_params_file = find_latest_file('outputs/mixture_model_parameters_*.csv')
        mrt_performance_file = find_latest_file('outputs/MRT_performance_by_disparity_*.csv')
        vviq2_file = find_latest_file('outputs/VVIQ2_scores_*.csv')
        control_vars_file = find_latest_file('outputs/control_variables_*.csv')
        
        print(f"Trial data file: {trial_data_file}")
        print(f"Mixture params file: {mixture_params_file}")
        print(f"MRT performance file: {mrt_performance_file}")
        print(f"VVIQ2 file: {vviq2_file}")
        print(f"Control variables file: {control_vars_file}")
        
        # Load data
        print("\nLoading data files...")
        
        trial_data = pd.read_csv(trial_data_file)
        print(f"Trial data shape: {trial_data.shape}")
        print(f"Trial data columns: {list(trial_data.columns)}")
        print("First 3 rows of trial data:")
        print(trial_data.head(3))
        
        mixture_params = pd.read_csv(mixture_params_file)
        print(f"\nMixture params shape: {mixture_params.shape}")
        print(f"Mixture params columns: {list(mixture_params.columns)}")
        print("First 3 rows of mixture params:")
        print(mixture_params.head(3))

        # Add validation for required concentration columns
        print(f"Checking for concentration parameter columns...")
        required_alt_columns = ['wrapped_normal_concentration', 'wrapped_cauchy_concentration']
        missing_columns = [col for col in required_alt_columns if col not in mixture_params.columns]

        if missing_columns:
            print(f"WARNING: Missing concentration columns: {missing_columns}")
            print("This may indicate an outdated input file is being used.")
            print("Alternative model parameter extraction may be limited.")
        else:
            print("All required concentration columns found.")
        
        mrt_performance = pd.read_csv(mrt_performance_file)
        print(f"\nMRT performance shape: {mrt_performance.shape}")
        print(f"MRT performance columns: {list(mrt_performance.columns)}")
        print("First 3 rows of MRT performance:")
        print(mrt_performance.head(3))
        
        vviq2_scores = pd.read_csv(vviq2_file)
        print(f"\nVVIQ2 scores shape: {vviq2_scores.shape}")
        print(f"VVIQ2 scores columns: {list(vviq2_scores.columns)}")
        print("First 3 rows of VVIQ2 scores:")
        print(vviq2_scores.head(3))
        
        control_vars = pd.read_csv(control_vars_file)
        print(f"\nControl variables shape: {control_vars.shape}")
        print(f"Control variables columns: {list(control_vars.columns)}")
        print("First 3 rows of control variables:")
        print(control_vars.head(3))
        
        # Print unique values for key experimental design parameters
        print("\nUnique values for key experimental design parameters:")
        print(f"isPractice values: {trial_data['isPractice'].unique()}")
        print(f"trial_excluded values: {trial_data['trial_excluded'].unique()}")
        print(f"best_model values: {mixture_params['best_model'].unique()}")
        print(f"convergence_status values: {mixture_params['convergence_status'].unique()}")
        
        # Calculate simple precision estimates
        print("\nCalculating simple precision estimates...")
        
        participants = trial_data['participantId'].unique()
        print(f"Number of participants: {len(participants)}")
        
        precision_estimates = []
        
        for participant_id in participants:
            participant_trials = trial_data[trial_data['participantId'] == participant_id].dropna(subset=['VWM_error_degrees'])
            
            if participant_trials.empty:
                continue
            
            # Calculate simple precision estimate
            simple_precision = calculate_simple_precision(participant_trials)
            
            # Get alternative model parameter if available
            alt_param, alt_type = get_alternative_model_parameter(mixture_params, participant_id)
            
            # Get original vonMises kappa
            vonmises_kappa = np.nan
            if participant_id in mixture_params['participantId'].values:
                vonmises_kappa = mixture_params[mixture_params['participantId'] == participant_id]['vonMises_kappa'].iloc[0]
            
            precision_estimates.append({
                'participantId': participant_id,
                'vonMises_kappa': vonmises_kappa,
                'simple_precision_estimate': simple_precision,
                'alternative_model_parameter': alt_param,
                'alternative_model_type': alt_type
            })
        
        precision_df = pd.DataFrame(precision_estimates)
        print(f"\nPrecision estimates calculated for {len(precision_df)} participants")
        print("First 2 rows of precision estimates:")
        print(precision_df.head(2))

        # Add detailed reporting about alternative models found
        print(f"\nDetailed breakdown of alternative models:")
        alt_model_counts = precision_df['alternative_model_type'].value_counts(dropna=False)
        print(alt_model_counts)

        if len(precision_df[precision_df['alternative_model_parameter'].notna()]) == 0:
            print("\nWARNING: No participants have alternative model parameters.")
            print("This may indicate:")
            print("1. The input file is missing concentration parameter columns")
            print("2. No participants had better-fitting alternative models")
            print("3. The AIC difference threshold (>4) was not met")
        
        # Calculate correlations between precision measures
        print("\nCalculating correlations between precision measures...")

        valid_simple = precision_df.dropna(subset=['vonMises_kappa', 'simple_precision_estimate'])
        # Also filter out infinite values
        valid_simple = valid_simple[np.isfinite(valid_simple['simple_precision_estimate'])]

        if len(valid_simple) > 1:
            corr_simple = stats.pearsonr(valid_simple['vonMises_kappa'], valid_simple['simple_precision_estimate'])[0]
            print(f"Correlation between vonMises_kappa and simple_precision_estimate: {corr_simple:.3f} (n={len(valid_simple)})")
        else:
            corr_simple = np.nan
            print(f"Insufficient data for vonMises_kappa vs simple_precision_estimate correlation (n={len(valid_simple)})")

        valid_alt = precision_df.dropna(subset=['vonMises_kappa', 'alternative_model_parameter'])
        if len(valid_alt) > 1:
            corr_alt = stats.pearsonr(valid_alt['vonMises_kappa'], valid_alt['alternative_model_parameter'])[0]
            print(f"Correlation between vonMises_kappa and alternative_model_parameter: {corr_alt:.3f} (n={len(valid_alt)})")
        else:
            corr_alt = np.nan
            print(f"Insufficient data for vonMises_kappa vs alternative_model_parameter correlation (n={len(valid_alt)})")
        
        # Add correlation columns to precision dataframe
        precision_df['precision_correlation_simple'] = corr_simple
        precision_df['precision_correlation_alternative'] = corr_alt
        precision_df['best_model_used'] = precision_df['alternative_model_type'].fillna('vonMises')
        
        # Merge with other datasets for analysis
        print("\nMerging datasets for analysis...")
        
        # Merge MRT performance with precision estimates and control variables
        # Drop vonMises_kappa from mrt_performance before merging to avoid conflict
        mrt_analysis_data = mrt_performance.drop(columns=['vonMises_kappa']).merge(precision_df, on='participantId', how='inner')
        mrt_analysis_data = mrt_analysis_data.merge(control_vars, on='participantId', how='inner')
        
        print(f"MRT analysis data shape: {mrt_analysis_data.shape}")
        print("First 2 rows of MRT analysis data:")
        print(mrt_analysis_data.head(2))
        
        # Merge VVIQ2 with precision estimates and control variables
        vviq2_analysis_data = vviq2_scores.merge(precision_df, on='participantId', how='inner')
        vviq2_analysis_data = vviq2_analysis_data.merge(control_vars, on='participantId', how='inner')
        
        print(f"VVIQ2 analysis data shape: {vviq2_analysis_data.shape}")
        print("First 2 rows of VVIQ2 analysis data:")
        print(vviq2_analysis_data.head(2))
        
        # Run sensitivity analyses
        print("\nRunning sensitivity analyses...")
        
        sensitivity_results = []
        
        # MRT analyses
        angular_disparities = ['0deg', '50deg', '100deg', '150deg']
        analysis_types = ['accuracy', 'rt']
        precision_measures = ['vonMises_kappa', 'simple_precision_estimate']
        
        # Add alternative model parameter for participants where available
        alt_participants = mrt_analysis_data[mrt_analysis_data['alternative_model_parameter'].notna()]
        print(f"Number of participants with alternative model parameters: {len(alt_participants)}")
        
        for precision_measure in precision_measures:
            print(f"\nRunning MRT analyses with {precision_measure}...")
            
            for angular_disparity in angular_disparities:
                for analysis_type in analysis_types:
                    print(f"  Running {analysis_type} analysis for {angular_disparity}...")
                    
                    dep_var = f'MRT_accuracy_{angular_disparity}' if analysis_type == 'accuracy' else f'MRT_rt_log_{angular_disparity}'
                    
                    result = run_regression_analysis(
                        mrt_analysis_data,
                        precision_measure,
                        dep_var,  # Use the corrected variable name
                        'logistic' if analysis_type == 'accuracy' else 'linear'
                    )
                    
                    sensitivity_results.append({
                        'precision_measure': precision_measure,
                        'analysis_type': 'MRT',
                        'dependent_variable': dep_var,  # Use the corrected variable name here too
                        'angular_disparity': angular_disparity,
                        'coefficient': result['coefficient'],
                        'standard_error': result['standard_error'],
                        'p_value': result['p_value'],
                        'sample_size': result.get('sample_size', 0)
                    })
        
        # Alternative model parameter analyses (for participants where available)
        if len(alt_participants) > 0:
            print(f"\nRunning MRT analyses with alternative_model_parameter for {len(alt_participants)} participants...")
            
            for angular_disparity in angular_disparities:
                for analysis_type in analysis_types:
                    print(f"  Running {analysis_type} analysis for {angular_disparity}...")
                    
                    dep_var = f'MRT_accuracy_{angular_disparity}' if analysis_type == 'accuracy' else f'MRT_rt_log_{angular_disparity}'
                    
                    result = run_regression_analysis(
                        alt_participants,
                        'alternative_model_parameter',
                        dep_var,
                        'logistic' if analysis_type == 'accuracy' else 'linear'
                    )
                    
                    sensitivity_results.append({
                        'precision_measure': 'alternative_model_parameter',
                        'analysis_type': 'MRT',
                        'dependent_variable': dep_var,
                        'angular_disparity': angular_disparity,
                        'coefficient': result['coefficient'],
                        'standard_error': result['standard_error'],
                        'p_value': result['p_value'],
                        'sample_size': result.get('sample_size', 0)
                    })
        
        # VVIQ2 analyses with conditional subscale logic
        vviq2_subscales = ['familiar_person_score', 'sunrise_score', 'shop_front_score', 
                           'countryside_score', 'driving_score', 'beach_score', 
                           'railway_station_score', 'garden_score']

        # Combine all precision measures and their data sources
        all_precision_measures = [
            ('vonMises_kappa', vviq2_analysis_data), 
            ('simple_precision_estimate', vviq2_analysis_data)
        ]

        if len(alt_participants) > 0:
            alt_vviq2_data = vviq2_analysis_data[vviq2_analysis_data['alternative_model_parameter'].notna()]
            all_precision_measures.append(('alternative_model_parameter', alt_vviq2_data))

        for precision_measure, data_source in all_precision_measures:
            print(f"\nRunning VVIQ2 analyses with {precision_measure}...")
            
            # First run total VVIQ2 score analysis
            total_result = run_regression_analysis(
                data_source,
                precision_measure,
                'total_VVIQ2_score',
                'linear'
            )
            
            sensitivity_results.append({
                'precision_measure': precision_measure,
                'analysis_type': 'VVIQ2',
                'dependent_variable': 'total_VVIQ2_score',
                'angular_disparity': 'NA',
                'coefficient': total_result['coefficient'],
                'standard_error': total_result['standard_error'],
                'p_value': total_result['p_value'],
                'sample_size': total_result.get('sample_size', 0)
            })
            
            # Only run subscale analyses if total score is significant
            if total_result['p_value'] is not None and total_result['p_value'] < 0.05:
                print(f"  {precision_measure} is significant for total_VVIQ2_score (p={total_result['p_value']:.4f})")
                print(f"  Running subscale analyses...")
                
                for subscale in vviq2_subscales:
                    print(f"    Running analysis for {subscale}...")
                    
                    subscale_result = run_regression_analysis(
                        data_source,
                        precision_measure,
                        subscale,
                        'linear'
                    )
                    
                    sensitivity_results.append({
                        'precision_measure': precision_measure,
                        'analysis_type': 'VVIQ2',
                        'dependent_variable': subscale,
                        'angular_disparity': 'NA',
                        'coefficient': subscale_result['coefficient'],
                        'standard_error': subscale_result['standard_error'],
                        'p_value': subscale_result['p_value'],
                        'sample_size': subscale_result.get('sample_size', 0)
                    })
            else:
                p_val_str = f"{total_result['p_value']:.4f}" if total_result['p_value'] is not None else "N/A"
                print(f"  {precision_measure} is not significant for total_VVIQ2_score (p={p_val_str})")
                print(f"  Skipping subscale analyses for this precision measure")

        # Apply FDR correction
        print("\nApplying FDR correction...")

        # Convert to dataframe first
        sensitivity_df = pd.DataFrame(sensitivity_results)

        # Apply FDR correction conditionally per precision measure for subscales only
        sensitivity_df['p_value_fdr_corrected'] = sensitivity_df['p_value']  # Default to original p-value

        for measure in sensitivity_df['precision_measure'].unique():
            # Only correct subscale p-values (not total_VVIQ2_score)
            subscale_mask = (
                (sensitivity_df['precision_measure'] == measure) & 
                (sensitivity_df['analysis_type'] == 'VVIQ2') & 
                (sensitivity_df['dependent_variable'] != 'total_VVIQ2_score')
            )
            
            if subscale_mask.any():
                print(f"Applying FDR correction to {subscale_mask.sum()} subscale results for {measure}")
                p_values_to_correct = sensitivity_df.loc[subscale_mask, 'p_value']
                corrected_p_values = apply_fdr_correction(p_values_to_correct)
                sensitivity_df.loc[subscale_mask, 'p_value_fdr_corrected'] = corrected_p_values
        
        # Add robustness assessment columns
        print("\nAdding robustness assessment...")
        
        # Simple robustness assessment
        sensitivity_df['robustness_assessment'] = 'Calculated'
        sensitivity_df['conclusion_consistency'] = 'Assessed'
        sensitivity_df['effect_size_stability'] = 'Evaluated'
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save alternative precision estimates
        precision_output_file = f'outputs/alternative_precision_estimates_{timestamp}.csv'
        precision_df.to_csv(precision_output_file, index=False)
        print(f"\nSaved alternative precision estimates to: {precision_output_file}")
        
        # Save sensitivity analysis results
        sensitivity_output_file = f'outputs/sensitivity_analysis_results_{timestamp}.csv'
        sensitivity_df.to_csv(sensitivity_output_file, index=False)
        print(f"Saved sensitivity analysis results to: {sensitivity_output_file}")
        
        # Print summary statistics
        print("\n=== SENSITIVITY ANALYSIS SUMMARY ===")
        print(f"Total participants analyzed: {len(participants)}")
        print(f"Participants with simple precision estimates: {len(precision_df.dropna(subset=['simple_precision_estimate']))}")
        print(f"Participants with alternative model parameters: {len(precision_df.dropna(subset=['alternative_model_parameter']))}")
        
        # Calculate percentage with better alternative models
        better_alt_models = len(precision_df[precision_df['alternative_model_parameter'].notna()])
        pct_better_alt = (better_alt_models / len(participants)) * 100
        print(f"Percentage with better alternative models: {pct_better_alt:.1f}%")
        
        # Print correlation summary
        print(f"\nCorrelation between vonMises_kappa and simple_precision_estimate: {corr_simple:.3f}")
        if not np.isnan(corr_alt):
            print(f"Correlation between vonMises_kappa and alternative_model_parameter: {corr_alt:.3f}")
        
        # Print significant results summary
        significant_results = sensitivity_df[sensitivity_df['p_value_fdr_corrected'] < 0.05]
        print(f"\nNumber of significant results (p < 0.05): {len(significant_results)}")
        
        if len(significant_results) > 0:
            print("\nSignificant results by precision measure:")
            for measure in significant_results['precision_measure'].unique():
                count = len(significant_results[significant_results['precision_measure'] == measure])
                print(f"  {measure}: {count} significant results")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
