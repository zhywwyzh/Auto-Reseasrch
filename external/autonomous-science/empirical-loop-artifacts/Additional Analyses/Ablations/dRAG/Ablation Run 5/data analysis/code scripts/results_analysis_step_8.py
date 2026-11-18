import pandas as pd
import numpy as np
import os
import glob
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
    # Get the most recent file based on modification time
    return max(files, key=os.path.getmtime)

def identify_outliers(df):
    """
    Identify statistical outliers in precision parameters.
    
    Parameters:
    df (pandas.DataFrame): Input dataframe with precision parameters
    
    Returns:
    pandas.DataFrame: Dataframe with outlier flags and exclusion reasons
    """
    print("Starting outlier identification...")
    
    # Create a copy to work with
    df_work = df.copy()
    
    # Initialize exclusion columns
    df_work['excluded_outlier'] = False
    df_work['exclusion_reason_outlier'] = ''
    
    # Calculate log(kappa) values
    df_work['log_concentration_kappa'] = np.log(df_work['final_concentration_kappa'])
    print(f"Calculated log(kappa) values. Range: {df_work['log_concentration_kappa'].min():.3f} to {df_work['log_concentration_kappa'].max():.3f}")
    
    # Calculate group statistics for log(kappa)
    log_kappa_mean = df_work['log_concentration_kappa'].mean()
    log_kappa_sd = df_work['log_concentration_kappa'].std()
    print(f"Log(kappa) group mean: {log_kappa_mean:.3f}, SD: {log_kappa_sd:.3f}")
    
    # a. Extreme κ values (log(κ) outliers)
    log_kappa_threshold = 3 * log_kappa_sd
    log_kappa_outliers = np.abs(df_work['log_concentration_kappa'] - log_kappa_mean) > log_kappa_threshold
    
    print(f"Log(kappa) outliers identified: {log_kappa_outliers.sum()} participants")
    
    # b. Model convergence issues
    convergence_issues = df_work['model_selection_confident'] == False
    print(f"Model convergence issues: {convergence_issues.sum()} participants")
    
    # c. Implausible parameters
    too_low_kappa = df_work['final_concentration_kappa'] < 0.1
    too_high_kappa = df_work['final_concentration_kappa'] > 100
    implausible_kappa = too_low_kappa | too_high_kappa
    print(f"Implausible kappa values: {implausible_kappa.sum()} participants (too low: {too_low_kappa.sum()}, too high: {too_high_kappa.sum()})")
    
    # d. Guess rate outliers
    high_guess_rate = df_work['final_guess_rate'] > 0.8
    print(f"High guess rate outliers: {high_guess_rate.sum()} participants")
    
    # Apply exclusion criteria (prioritize log(κ) outlier criterion)
    exclusion_reasons = []
    
    # Log(kappa) outliers - primary criterion
    log_kappa_mask = log_kappa_outliers
    df_work.loc[log_kappa_mask, 'excluded_outlier'] = True
    df_work.loc[log_kappa_mask, 'exclusion_reason_outlier'] = 'log_kappa_outlier'
    
    # Model convergence issues - flag but don't exclude as standalone criterion
    # convergence_mask = convergence_issues & ~df_work['excluded_outlier']
    # df_work.loc[convergence_mask, 'excluded_outlier'] = True
    # df_work.loc[convergence_mask, 'exclusion_reason_outlier'] = 'model_convergence_issue'
    
    # Implausible parameters
    implausible_mask = implausible_kappa & ~df_work['excluded_outlier']
    df_work.loc[implausible_mask, 'excluded_outlier'] = True
    df_work.loc[implausible_mask, 'exclusion_reason_outlier'] = 'implausible_kappa'
    
    # High guess rate
    guess_rate_mask = high_guess_rate & ~df_work['excluded_outlier']
    df_work.loc[guess_rate_mask, 'excluded_outlier'] = True
    df_work.loc[guess_rate_mask, 'exclusion_reason_outlier'] = 'high_guess_rate'
    
    print(f"Total participants excluded: {df_work['excluded_outlier'].sum()}")
    
    return df_work

def calculate_exclusion_statistics(df):
    """
    Calculate exclusion statistics for each criterion.
    
    Parameters:
    df (pandas.DataFrame): Dataframe with exclusion flags
    
    Returns:
    pandas.DataFrame: Summary of exclusions by criterion
    """
    print("Calculating exclusion statistics...")
    
    total_participants = len(df)
    
    # Count exclusions by reason
    exclusion_counts = df['exclusion_reason_outlier'].value_counts()
    
    # Create summary dataframe
    exclusion_summary = []
    
    criteria = ['log_kappa_outlier', 'model_convergence_issue', 'implausible_kappa', 'high_guess_rate']
    
    for criterion in criteria:
        count = exclusion_counts.get(criterion, 0)
        percentage = (count / total_participants) * 100
        
        exclusion_summary.append({
            'exclusion_criterion': criterion,
            'excluded_count': count,
            'total_participants_screened': total_participants,
            'exclusion_percentage': percentage
        })
        
        print(f"{criterion}: {count} excluded ({percentage:.2f}%)")
    
    return pd.DataFrame(exclusion_summary)

def create_quality_summary(df_included):
    """
    Create parameter quality summary for included participants.
    
    Parameters:
    df_included (pandas.DataFrame): Dataframe with included participants only
    
    Returns:
    pandas.DataFrame: Quality summary statistics
    """
    print("Creating parameter quality summary...")
    
    metrics = ['final_concentration_kappa', 'log_concentration_kappa', 'final_bias_mu_degrees', 'final_guess_rate']
    
    summary_data = []
    
    for metric in metrics:
        values = df_included[metric]
        
        summary_data.append({
            'metric': metric,
            'mean_value': values.mean(),
            'sd_value': values.std(),
            'min_value': values.min(),
            'max_value': values.max(),
            'n_participants': len(values)
        })
        
        print(f"{metric}: mean={values.mean():.3f}, sd={values.std():.3f}, range=[{values.min():.3f}, {values.max():.3f}]")
    
    return pd.DataFrame(summary_data)

def main():
    """
    Main function to execute parameter outlier exclusion analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting parameter outlier exclusion analysis...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Find the most recent input file
        input_pattern = 'outputs/model_comparison_results_*.csv'
        input_file = find_most_recent_file(input_pattern)
        
        if input_file is None:
            print(f"Error: No files found matching pattern {input_pattern}")
            return 1
        
        print(f"Using input file: {input_file}")
        
        # Read input data
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded data with {len(df)} participants")
        except Exception as e:
            print(f"Error reading input file: {e}")
            return 1
        
        # Print data structure for debugging
        print("Input data columns:", df.columns.tolist())
        print("First 3 rows of input data:")
        print(df.head(3))
        
        # Verify required columns exist
        required_columns = ['participantId', 'final_concentration_kappa', 'final_bias_mu_degrees', 
                          'final_guess_rate', 'selected_model', 'model_selection_confident']
        
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns present")
        
        # Print unique values for categorical columns
        print("Unique values in selected_model:", df['selected_model'].unique())
        print("Unique values in model_selection_confident:", df['model_selection_confident'].unique())
        
        # Print data types and ranges for numerical columns
        print("Data types and ranges for numerical columns:")
        for col in ['final_concentration_kappa', 'final_bias_mu_degrees', 'final_guess_rate']:
            print(f"{col}: type={df[col].dtype}, range=[{df[col].min():.3f}, {df[col].max():.3f}]")
        
        # Identify outliers and apply exclusion criteria
        df_with_exclusions = identify_outliers(df)
        
        # Calculate exclusion statistics
        exclusion_stats = calculate_exclusion_statistics(df_with_exclusions)
        
        # Create final analytical dataset (included participants only)
        df_included = df_with_exclusions[~df_with_exclusions['excluded_outlier']].copy()
        print(f"Final analytical dataset: {len(df_included)} participants included")
        
        # Validation checks
        print("Performing validation checks...")
        
        # Check minimum sample size
        min_sample_size = 200
        if len(df_included) < min_sample_size:
            print(f"Warning: Final sample size ({len(df_included)}) is below minimum recommended ({min_sample_size})")
        else:
            print(f"Sample size adequate: {len(df_included)} >= {min_sample_size}")
        
        # Check distribution of log(κ) values in cleaned sample
        log_kappa_clean = df_included['log_concentration_kappa']
        print(f"Cleaned log(kappa) distribution: mean={log_kappa_clean.mean():.3f}, sd={log_kappa_clean.std():.3f}")
        print(f"Cleaned log(kappa) range: [{log_kappa_clean.min():.3f}, {log_kappa_clean.max():.3f}]")
        
        # Create parameter quality summary
        quality_summary = create_quality_summary(df_included)
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save exclusion log
        exclusion_log_file = f'outputs/parameter_outlier_exclusion_log_{timestamp}.csv'
        exclusion_stats.to_csv(exclusion_log_file, index=False)
        print(f"Saved exclusion log to: {exclusion_log_file}")
        
        print("Exclusion log contents:")
        print(exclusion_stats)
        
        # Save final precision parameters
        output_columns = ['participantId', 'final_concentration_kappa', 'log_concentration_kappa', 
                         'final_bias_mu_degrees', 'final_guess_rate', 'selected_model', 
                         'excluded_outlier', 'exclusion_reason_outlier']
        
        final_params_file = f'outputs/final_precision_parameters_{timestamp}.csv'
        df_with_exclusions[output_columns].to_csv(final_params_file, index=False)
        print(f"Saved final precision parameters to: {final_params_file}")
        
        print("First 2 rows of final precision parameters:")
        print(df_with_exclusions[output_columns].head(2))
        
        # Save parameter quality summary
        quality_summary_file = f'outputs/parameter_quality_summary_{timestamp}.csv'
        quality_summary.to_csv(quality_summary_file, index=False)
        print(f"Saved parameter quality summary to: {quality_summary_file}")
        
        print("Parameter quality summary:")
        print(quality_summary)
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
