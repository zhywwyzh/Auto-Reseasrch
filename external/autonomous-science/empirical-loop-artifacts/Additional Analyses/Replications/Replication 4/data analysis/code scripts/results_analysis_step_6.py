import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Import R packages via rpy2
import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
from rpy2.robjects.packages import importr
import rpy2.robjects.numpy2ri as numpy2ri

# Enable automatic conversion between pandas and R dataframes
from rpy2.robjects import conversion, default_converter
from rpy2.robjects.conversion import localconverter

def find_latest_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file matching the pattern
    """
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    # Sort by modification time and return the most recent
    latest_file = max(files, key=os.path.getmtime)
    print(f"Found latest file for pattern {pattern}: {latest_file}")
    return latest_file

def install_and_import_r_packages():
    """
    Install and import required R packages.
    
    Returns:
    dict: Dictionary of imported R packages
    """
    print("Installing and importing required R packages...")
    
    # Import base R functions for package installation
    utils = importr('utils')
    base = importr('base')
    
    # List of required packages
    required_packages = ['lme4', 'car', 'performance', 'lmerTest']
    
    # Check and install packages if needed
    for package in required_packages:
        try:
            importr(package)
            print(f"Package {package} already available")
        except:
            print(f"Installing package {package}...")
            utils.install_packages(package)
            print(f"Package {package} installed successfully")
    
    # Import all packages
    packages = {}
    packages['lme4'] = importr('lme4')
    packages['lmerTest'] = importr('lmerTest')  # This loads lme4 with p-values
    packages['base'] = importr('base')
    packages['stats'] = importr('stats')
    packages['car'] = importr('car')
    packages['performance'] = importr('performance')
    
    print("All R packages loaded successfully")
    return packages

def load_and_validate_data():
    """
    Load and validate all input datasets.
    
    Returns:
    tuple: (vonmises_df, mrt_df, vwm_df, participant_df)
    """
    print("Starting data loading and validation...")
    
    # Find latest files
    vonmises_file = find_latest_file("outputs/vonmises_parameters_overall_*.csv")
    mrt_file = find_latest_file("outputs/cleaned_mrt_data_*.csv")
    vwm_file = find_latest_file("outputs/cleaned_vwm_data_*.csv")
    participant_file = find_latest_file("outputs/cleaned_participant_data_*.csv")
    
    # Load datasets
    print("\nLoading von Mises parameters dataset...")
    vonmises_df = pd.read_csv(vonmises_file)
    print(f"Von Mises data shape: {vonmises_df.shape}")
    print(f"Von Mises columns: {list(vonmises_df.columns)}")
    print("First 3 rows:")
    print(vonmises_df.head(3))
    
    print("\nLoading MRT dataset...")
    mrt_df = pd.read_csv(mrt_file)
    print(f"MRT data shape: {mrt_df.shape}")
    print(f"MRT columns: {list(mrt_df.columns)}")
    print("First 3 rows:")
    print(mrt_df.head(3))
    print(f"Unique angle_degrees values: {sorted(mrt_df['angle_degrees'].unique())}")
    print(f"Unique isCorrect values: {sorted(mrt_df['isCorrect'].unique())}")
    print(f"Unique excluded_trial values: {sorted(mrt_df['excluded_trial'].unique())}")
    
    print("\nLoading VWM dataset...")
    vwm_df = pd.read_csv(vwm_file)
    print(f"VWM data shape: {vwm_df.shape}")
    print(f"VWM columns: {list(vwm_df.columns)}")
    print("First 3 rows:")
    print(vwm_df.head(3))
    print(f"Unique excluded_trial values: {sorted(vwm_df['excluded_trial'].unique())}")
    
    print("\nLoading participant dataset...")
    participant_df = pd.read_csv(participant_file)
    print(f"Participant data shape: {participant_df.shape}")
    print(f"Participant columns: {list(participant_df.columns)}")
    print("First 3 rows:")
    print(participant_df.head(3))
    
    # Validate required columns
    required_vonmises_cols = ['participantId', 'kappa_overall', 'kappa_se_overall', 'poor_fit_flag']
    required_mrt_cols = ['participantId', 'angle_degrees', 'isCorrect', 'rt_ms', 'excluded_trial']
    required_vwm_cols = ['participantId', 'error_absolute_degrees', 'excluded_trial']
    required_participant_cols = ['participantId', 'focus_loss_duration_pct']
    
    missing_cols = []
    for col in required_vonmises_cols:
        if col not in vonmises_df.columns:
            missing_cols.append(f"vonmises: {col}")
    
    for col in required_mrt_cols:
        if col not in mrt_df.columns:
            missing_cols.append(f"mrt: {col}")
    
    for col in required_vwm_cols:
        if col not in vwm_df.columns:
            missing_cols.append(f"vwm: {col}")
    
    for col in required_participant_cols:
        if col not in participant_df.columns:
            missing_cols.append(f"participant: {col}")
    
    if missing_cols:
        print(f"WARNING: Missing required columns: {missing_cols}")
        # Don't fail, just continue with available columns
    
    print("Data loading and validation completed successfully.")
    return vonmises_df, mrt_df, vwm_df, participant_df

def prepare_analysis_data(vonmises_df, mrt_df, vwm_df, participant_df):
    """
    Prepare data for LMM analysis by filtering and merging datasets.
    
    Parameters:
    vonmises_df (pd.DataFrame): Von Mises parameters data
    mrt_df (pd.DataFrame): MRT data
    vwm_df (pd.DataFrame): VWM data
    participant_df (pd.DataFrame): Participant data
    
    Returns:
    pd.DataFrame: Prepared analysis dataset
    """
    print("\nPreparing analysis data...")
    
    # Filter von Mises data to exclude poor fits
    print(f"Original von Mises participants: {len(vonmises_df)}")
    print(f"Poor fit flag values: {vonmises_df['poor_fit_flag'].value_counts()}")
    
    good_fit_participants = vonmises_df[vonmises_df['poor_fit_flag'] != True]['participantId'].unique()
    print(f"Participants with good von Mises fits: {len(good_fit_participants)}")
    
    # Filter MRT data to correct trials only
    print(f"\nOriginal MRT trials: {len(mrt_df)}")
    mrt_filtered = mrt_df[
        (mrt_df['excluded_trial'] == False) & 
        (mrt_df['isCorrect'] == True) &
        (mrt_df['participantId'].isin(good_fit_participants))
    ].copy()
    print(f"Filtered MRT trials (correct, non-excluded, good fit participants): {len(mrt_filtered)}")
    
    # Apply log transformation to RT
    mrt_filtered['log_rt'] = np.log(mrt_filtered['rt_ms'])
    print(f"Log RT range: {mrt_filtered['log_rt'].min():.3f} to {mrt_filtered['log_rt'].max():.3f}")
    
    # Convert angle to categorical
    mrt_filtered['angle_degrees'] = mrt_filtered['angle_degrees'].astype('category')
    print(f"Angle categories: {mrt_filtered['angle_degrees'].cat.categories}")
    
    # Calculate VWM accuracy per participant
    print(f"\nOriginal VWM trials: {len(vwm_df)}")
    vwm_filtered = vwm_df[
        (vwm_df['excluded_trial'] == False) &
        (vwm_df['participantId'].isin(good_fit_participants))
    ]
    print(f"Filtered VWM trials: {len(vwm_filtered)}")
    
    vwm_accuracy = vwm_filtered.groupby('participantId')['error_absolute_degrees'].mean().reset_index()
    vwm_accuracy.columns = ['participantId', 'mean_vwm_accuracy']
    print(f"VWM accuracy calculated for {len(vwm_accuracy)} participants")
    print(f"VWM accuracy range: {vwm_accuracy['mean_vwm_accuracy'].min():.3f} to {vwm_accuracy['mean_vwm_accuracy'].max():.3f}")
    
    # Filter participant data
    participant_filtered = participant_df[participant_df['participantId'].isin(good_fit_participants)].copy()
    print(f"Participant data for {len(participant_filtered)} participants")
    
    # Filter von Mises data
    vonmises_filtered = vonmises_df[vonmises_df['participantId'].isin(good_fit_participants)].copy()
    
    # Calculate weights for kappa uncertainty
    print("\nCalculating weights for kappa uncertainty...")
    vonmises_filtered['weight'] = 1 / (vonmises_filtered['kappa_se_overall'] ** 2)
    
    # Handle zero standard errors
    zero_se_count = (vonmises_filtered['kappa_se_overall'] == 0).sum()
    if zero_se_count > 0:
        print(f"Found {zero_se_count} participants with zero kappa SE")
        max_weight = vonmises_filtered[vonmises_filtered['kappa_se_overall'] > 0]['weight'].max()
        vonmises_filtered.loc[vonmises_filtered['kappa_se_overall'] == 0, 'weight'] = max_weight
        print(f"Set weight for zero SE participants to max weight: {max_weight:.3f}")
    
    print(f"Weight range: {vonmises_filtered['weight'].min():.3f} to {vonmises_filtered['weight'].max():.3f}")
    
    # Merge all datasets
    print("\nMerging datasets...")
    analysis_data = mrt_filtered.merge(vonmises_filtered[['participantId', 'kappa_overall', 'weight']], on='participantId')
    analysis_data = analysis_data.merge(vwm_accuracy, on='participantId')
    analysis_data = analysis_data.merge(participant_filtered[['participantId', 'focus_loss_duration_pct']], on='participantId')
    
    print(f"Final analysis dataset shape: {analysis_data.shape}")
    print(f"Participants in analysis: {analysis_data['participantId'].nunique()}")
    print(f"Trials per participant: {analysis_data.groupby('participantId').size().describe()}")
    
    # Center continuous predictors
    print("\nCentering continuous predictors...")
    analysis_data['kappa_overall_centered'] = analysis_data['kappa_overall'] - analysis_data['kappa_overall'].mean()
    analysis_data['mean_vwm_accuracy_centered'] = analysis_data['mean_vwm_accuracy'] - analysis_data['mean_vwm_accuracy'].mean()
    analysis_data['focus_loss_duration_pct_centered'] = analysis_data['focus_loss_duration_pct'] - analysis_data['focus_loss_duration_pct'].mean()
    
    print(f"Kappa centered range: {analysis_data['kappa_overall_centered'].min():.3f} to {analysis_data['kappa_overall_centered'].max():.3f}")
    print(f"VWM accuracy centered range: {analysis_data['mean_vwm_accuracy_centered'].min():.3f} to {analysis_data['mean_vwm_accuracy_centered'].max():.3f}")
    print(f"Focus loss centered range: {analysis_data['focus_loss_duration_pct_centered'].min():.3f} to {analysis_data['focus_loss_duration_pct_centered'].max():.3f}")
    
    # Add trial ID
    analysis_data['trial_id'] = range(1, len(analysis_data) + 1)
    
    # Add missing value handling before return statement
    model_cols = ['log_rt', 'kappa_overall_centered', 'angle_degrees', 
                  'mean_vwm_accuracy_centered', 'focus_loss_duration_pct_centered', 
                  'participantId', 'weight']
    initial_rows = len(analysis_data)
    analysis_data.dropna(subset=model_cols, inplace=True)
    final_rows = len(analysis_data)
    if initial_rows > final_rows:
        print(f"\nDropped {initial_rows - final_rows} rows with NA values in model columns.")
        print(f"Final analysis dataset shape after NA removal: {analysis_data.shape}")

    print("Analysis data preparation completed.")
    print("\nAnalysis data columns:")
    print(list(analysis_data.columns))
    print("\nFirst 2 rows of analysis data:")
    print(analysis_data.head(2))
    
    return analysis_data

def fit_lmm_model(analysis_data):
    """
    Fit linear mixed-effects model using R via rpy2.
    
    Parameters:
    analysis_data (pd.DataFrame): Prepared analysis dataset
    
    Returns:
    tuple: (model, model_summary, diagnostics)
    """
    print("\nFitting linear mixed-effects model using R...")
    
    # Install and import required R packages
    packages = install_and_import_r_packages()
    
    # Convert pandas DataFrame to R DataFrame using localconverter
    print("Converting data to R format...")
    with localconverter(default_converter + pandas2ri.converter):
        r_data = robjects.conversion.py2rpy(analysis_data)
    
    # Assign data to R global environment
    robjects.globalenv['data'] = r_data
    
    # Set reference level for angle_degrees to 0
    print("Setting reference level for angle_degrees...")
    robjects.r('''
    data$angle_degrees <- relevel(as.factor(data$angle_degrees), ref="0")
    ''')
    
    # Fit the model
    print("Fitting LMM model...")
    model_formula = '''
    log_rt ~ kappa_overall_centered * angle_degrees + 
             mean_vwm_accuracy_centered + 
             focus_loss_duration_pct_centered + 
             (1|participantId)
    '''
    
    print(f"Model formula: {model_formula}")
    
    try:
        # Fit model with weights
        model = robjects.r(f'''
        model <- lmer({model_formula}, 
                     data = data, 
                     weights = data$weight,
                     REML = FALSE)
        model
        ''')
        print("Model fitted successfully")
        
        # Check model convergence
        convergence_check = robjects.r('model@optinfo$conv$lme4$messages')
        if convergence_check != robjects.NULL:
            print(f"Model convergence warnings: {convergence_check}")
        else:
            print("Model converged successfully")
        
        # Get model summary
        model_summary = robjects.r('summary(model)')
        print("Model summary obtained")
        
        # Extract fixed effects
        print("Extracting fixed effects...")
        fixed_effects = robjects.r('fixef(model)')
        
        # Get confidence intervals
        print("Calculating confidence intervals...")
        conf_int = robjects.r('confint(model, method="Wald")')
        
        # Get model diagnostics
        print("Computing model diagnostics...")
        
        # VIF (excluding interactions initially)
        try:
            vif_model_formula = '''log_rt ~ kappa_overall_centered + angle_degrees + 
                          mean_vwm_accuracy_centered + focus_loss_duration_pct_centered + 
                          (1|participantId)'''
            robjects.r(f'vif_model <- lmer({vif_model_formula}, data=data, weights=data$weight, REML=FALSE)')
            vif_values = robjects.r('vif(vif_model)')
            print("VIF values computed")
        except Exception as e:
            print(f"Could not compute VIF values: {e}")
            vif_values = None
        
        # ICC
        try:
            icc_result = robjects.r('performance::icc(model)')
            print("ICC computed")
        except:
            print("Could not compute ICC")
            icc_result = None
        
        # Model fit statistics
        aic = robjects.r('AIC(model)')[0]
        bic = robjects.r('BIC(model)')[0]
        loglik = robjects.r('logLik(model)')[0]
        
        # R-squared
        try:
            r2_result = robjects.r('performance::r2(model)')
            r2_marginal = r2_result.rx2('R2_marginal')[0] if 'R2_marginal' in r2_result.names else None
            r2_conditional = r2_result.rx2('R2_conditional')[0] if 'R2_conditional' in r2_result.names else None
            print("R-squared values computed")
        except:
            print("Could not compute R-squared values")
            r2_marginal = None
            r2_conditional = None
        
        # Get residuals and fitted values for diagnostics
        residuals = robjects.r('residuals(model)')
        fitted_values = robjects.r('fitted(model)')
        
        diagnostics = {
            'aic': aic,
            'bic': bic,
            'loglik': loglik,
            'r2_marginal': r2_marginal,
            'r2_conditional': r2_conditional,
            'vif': vif_values,
            'icc': icc_result,
            'residuals': residuals,
            'fitted': fitted_values
        }
        
        print("Model fitting and diagnostics completed successfully")
        
        return model, model_summary, diagnostics
        
    except Exception as e:
        print(f"Error fitting model: {e}")
        raise

def extract_model_results(model, model_summary, diagnostics):
    """
    Extract model results and format for output.
    
    Parameters:
    model: R model object
    model_summary: R model summary object
    diagnostics (dict): Model diagnostic results
    
    Returns:
    tuple: (results_df, diagnostics_df)
    """
    print("\nExtracting model results...")

    # Extract coefficient table - get metadata first, then convert
    coef_table_r = robjects.r('summary(model)$coefficients')
    coef_row_names = list(coef_table_r.rownames)
    coef_col_names = list(coef_table_r.colnames)

    # Extract confidence intervals - get metadata first, then convert  
    conf_int_r = robjects.r('confint(model, method="Wald")')
    conf_int_row_names = list(conf_int_r.rownames)
    conf_int_col_names = list(conf_int_r.colnames)

    # Now convert to arrays using localconverter
    with localconverter(default_converter + pandas2ri.converter + numpy2ri.converter):
        coef_array = np.array(coef_table_r)
        conf_int_array = np.array(conf_int_r)

    # Create DataFrames using pre-extracted names
    coef_df = pd.DataFrame(coef_array, index=coef_row_names, columns=coef_col_names)
    conf_int_df = pd.DataFrame(conf_int_array, index=conf_int_row_names, columns=conf_int_col_names)

    # Filter confidence intervals to only include fixed effects
    conf_int_df = conf_int_df.loc[conf_int_df.index.isin(coef_row_names)]
    print(f"Filtered confidence interval shape: {conf_int_df.shape}")

    # Debug prints for verification
    print(f"Coefficient table shape: {coef_array.shape}")
    print(f"Row names length: {len(coef_row_names)}")
    print(f"Column names length: {len(coef_col_names)}")
    print(f"Confidence interval shape: {conf_int_array.shape}")
    print(f"CI row names length: {len(conf_int_row_names)}")
    print(f"CI column names length: {len(conf_int_col_names)}")
    
    # Get effect names
    effect_names = list(coef_df.index)
    print(f"Fixed effects: {effect_names}")
    
    # Create results dataframe
    results_data = []
    
    for effect_name in effect_names:
        # Determine effect type
        if effect_name == '(Intercept)':
            effect_type = 'intercept'
        elif 'kappa_overall_centered:' in effect_name:
            effect_type = 'interaction'
        elif 'angle_degrees' in effect_name:
            effect_type = 'main_effect'
        elif any(var in effect_name for var in ['kappa_overall_centered', 'mean_vwm_accuracy_centered', 'focus_loss_duration_pct_centered']):
            effect_type = 'main_effect'
        else:
            effect_type = 'other'
        
        # Extract values using column and index names for robustness
        coefficient = coef_df.loc[effect_name, 'Estimate']
        standard_error = coef_df.loc[effect_name, 'Std. Error']
        t_value = coef_df.loc[effect_name, 't value']
        p_value = coef_df.loc[effect_name, 'Pr(>|t|)']  # From lmerTest

        # Get confidence intervals
        ci_lower = conf_int_df.loc[effect_name, '2.5 %']
        ci_upper = conf_int_df.loc[effect_name, '97.5 %']
        
        results_data.append({
            'effect_name': effect_name,
            'coefficient': coefficient,
            'standard_error': standard_error,
            't_value': t_value,
            'p_value': p_value,
            'ci_lower': ci_lower,
            'ci_upper': ci_upper,
            'effect_type': effect_type
        })
    
    results_df = pd.DataFrame(results_data)
    
    print("Fixed effects results:")
    print(results_df)
    
    # Create diagnostics dataframe
    diagnostics_data = []
    
    # Model fit statistics
    diagnostics_data.append({
        'diagnostic_name': 'AIC',
        'diagnostic_value': diagnostics['aic'],
        'interpretation': 'Lower is better'
    })

    diagnostics_data.append({
        'diagnostic_name': 'BIC',
        'diagnostic_value': diagnostics['bic'],
        'interpretation': 'Lower is better'
    })

    diagnostics_data.append({
        'diagnostic_name': 'LogLikelihood',
        'diagnostic_value': diagnostics['loglik'],
        'interpretation': 'Higher is better'
    })

    if diagnostics['r2_marginal'] is not None:
        diagnostics_data.append({
            'diagnostic_name': 'R2_marginal',
            'diagnostic_value': diagnostics['r2_marginal'],
            'interpretation': 'Variance explained by fixed effects'
        })

    if diagnostics['r2_conditional'] is not None:
        diagnostics_data.append({
            'diagnostic_name': 'R2_conditional',
            'diagnostic_value': diagnostics['r2_conditional'],
            'interpretation': 'Variance explained by all effects'
        })

    if diagnostics['icc'] is not None:
        try:
            icc_value = diagnostics['icc'].rx2('ICC_adjusted')[0]
            diagnostics_data.append({
                'diagnostic_name': 'ICC',
                'diagnostic_value': icc_value,
                'interpretation': 'Proportion of variance due to clustering'
            })
        except:
            print("Could not extract ICC value")

    # VIF values
    if diagnostics['vif'] is not None:
        try:
            vif_r = diagnostics['vif']
            base = importr('base')
            
            with localconverter(default_converter + pandas2ri.converter + numpy2ri.converter):
                if base.is_matrix(vif_r)[0]:
                    # Handle matrix output from car::vif (e.g., with factors)
                    var_names = list(vif_r.rownames)
                    vif_df = pd.DataFrame(np.array(vif_r), index=var_names, columns=list(vif_r.colnames))
                    
                    vif_col = 'GVIF' if 'GVIF' in vif_df.columns else vif_df.columns[0]
                    for var_name in vif_df.index:
                        vif_val = vif_df.loc[var_name, vif_col]
                        interpretation = 'Good (VIF < 5)' if vif_val < 5 else 'Concerning (VIF >= 5)'
                        diagnostics_data.append({
                            'diagnostic_name': f'VIF_{var_name}',
                            'diagnostic_value': vif_val,
                            'interpretation': interpretation
                        })
                else:
                    # Handle vector output
                    var_names = list(vif_r.names)
                    vif_values = np.array(vif_r)
                    for i, var_name in enumerate(var_names):
                        vif_val = vif_values[i]
                        interpretation = 'Good (VIF < 5)' if vif_val < 5 else 'Concerning (VIF >= 5)'
                        diagnostics_data.append({
                            'diagnostic_name': f'VIF_{var_name}',
                            'diagnostic_value': vif_val,
                            'interpretation': interpretation
                        })
        except Exception as e:
            print(f"Could not extract VIF values: {e}")
    
    diagnostics_df = pd.DataFrame(diagnostics_data)
    
    print("Model diagnostics:")
    print(diagnostics_df)
    
    return results_df, diagnostics_df

def create_analysis_output(analysis_data, model, diagnostics):
    """
    Create analysis data output with predictions and residuals.
    
    Parameters:
    analysis_data (pd.DataFrame): Original analysis data
    model: R model object
    diagnostics (dict): Model diagnostic results
    
    Returns:
    pd.DataFrame: Analysis data with predictions and residuals
    """
    print("\nCreating analysis data output...")
    
    # Get predictions and residuals from R using localconverter
    with localconverter(default_converter + pandas2ri.converter):
        fitted_values = robjects.conversion.rpy2py(diagnostics['fitted'])
        residuals = robjects.conversion.rpy2py(diagnostics['residuals'])
    
    # Create output dataframe
    output_data = analysis_data[['participantId', 'trial_id', 'kappa_overall', 'angle_degrees', 
                               'log_rt', 'mean_vwm_accuracy', 'focus_loss_duration_pct']].copy()
    
    # Add model weight
    output_data['model_weight'] = analysis_data['weight']
    
    # Add predictions and residuals
    output_data['predicted_log_rt'] = fitted_values
    output_data['residual'] = residuals
    
    print(f"Analysis output data shape: {output_data.shape}")
    print("Analysis output columns:")
    print(list(output_data.columns))
    print("First 2 rows:")
    print(output_data.head(2))
    
    return output_data

def save_results(results_df, diagnostics_df, analysis_output_df):
    """
    Save all results to CSV files.
    
    Parameters:
    results_df (pd.DataFrame): Model results
    diagnostics_df (pd.DataFrame): Model diagnostics
    analysis_output_df (pd.DataFrame): Analysis data with predictions
    """
    print("\nSaving results to CSV files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save results
    results_file = f'outputs/mrt_rt_lmm_results_{timestamp}.csv'
    results_df.to_csv(results_file, index=False)
    print(f"Model results saved to: {results_file}")
    
    # Save diagnostics
    diagnostics_file = f'outputs/mrt_rt_model_diagnostics_{timestamp}.csv'
    diagnostics_df.to_csv(diagnostics_file, index=False)
    print(f"Model diagnostics saved to: {diagnostics_file}")
    
    # Save analysis data
    analysis_file = f'outputs/mrt_rt_analysis_data_{timestamp}.csv'
    analysis_output_df.to_csv(analysis_file, index=False)
    print(f"Analysis data saved to: {analysis_file}")
    
    print("All results saved successfully.")

def main():
    """
    Main function to execute the MRT reaction time LMM analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("=== MRT Reaction Time Linear Mixed-Effects Model Analysis ===")
        print(f"Analysis started at: {datetime.now()}")
        
        # Load and validate data
        vonmises_df, mrt_df, vwm_df, participant_df = load_and_validate_data()
        
        # Prepare analysis data
        analysis_data = prepare_analysis_data(vonmises_df, mrt_df, vwm_df, participant_df)
        
        # Fit LMM model
        model, model_summary, diagnostics = fit_lmm_model(analysis_data)
        
        # Extract results
        results_df, diagnostics_df = extract_model_results(model, model_summary, diagnostics)
        
        # Create analysis output
        analysis_output_df = create_analysis_output(analysis_data, model, diagnostics)
        
        # Save results
        save_results(results_df, diagnostics_df, analysis_output_df)
        
        print(f"\nAnalysis completed successfully at: {datetime.now()}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in analysis: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
