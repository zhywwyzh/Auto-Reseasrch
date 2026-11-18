import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
from scipy import stats
from scipy.stats import pearsonr
from sklearn.linear_model import LinearRegression
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

def calculate_confidence_interval(r, n, confidence=0.95):
    """
    Calculate confidence interval for correlation coefficient using Fisher's z-transformation.
    
    Parameters:
    r (float): Correlation coefficient
    n (int): Sample size
    confidence (float): Confidence level (default 0.95)
    
    Returns:
    tuple: Lower and upper bounds of confidence interval
    """
    if abs(r) >= 1.0 or n <= 3:
        return np.nan, np.nan
    
    # Fisher's z-transformation
    z = 0.5 * np.log((1 + r) / (1 - r))
    
    # Standard error
    se = 1 / np.sqrt(n - 3)
    
    # Critical value for given confidence level
    alpha = 1 - confidence
    z_critical = stats.norm.ppf(1 - alpha / 2)
    
    # Confidence interval in z-space
    z_lower = z - z_critical * se
    z_upper = z + z_critical * se
    
    # Transform back to correlation space
    r_lower = (np.exp(2 * z_lower) - 1) / (np.exp(2 * z_lower) + 1)
    r_upper = (np.exp(2 * z_upper) - 1) / (np.exp(2 * z_upper) + 1)
    
    return r_lower, r_upper

def classify_reliability(reliability):
    """
    Classify reliability coefficient according to conventional thresholds.
    
    Parameters:
    reliability (float): Reliability coefficient
    
    Returns:
    str: Classification of reliability
    """
    if pd.isna(reliability):
        return "Unable to calculate"
    elif reliability >= 0.90:
        return "Excellent"
    elif reliability >= 0.80:
        return "Good"
    elif reliability >= 0.70:
        return "Acceptable"
    else:
        return "Poor"

def split_trials_randomly(df, participant_col, trial_col, condition_cols=None):
    """
    Split trials for each participant into two halves, ensuring balanced conditions.

    This function implements a random assignment approach within condition strata to ensure 
    that each half contains approximately equal representation of all experimental conditions. 
    For each participant, trials are randomly split within each unique combination of 
    condition values to maintain balance while introducing randomness.

    Parameters:
    df (DataFrame): Input dataframe containing trial data
    participant_col (str): Name of participant ID column
    trial_col (str): Name of trial column for identification
    condition_cols (list): List of condition columns to balance across halves (e.g., ['VWM_setSize', 'VWM_delay_s'])

    Returns:
    DataFrame: Dataframe with added 'half' column (values 1 or 2) indicating the split assignment

    Notes:
    - Uses random assignment within condition strata to ensure good balance of trials
    - Handles cases where a participant may have missing conditions or odd numbers of trials
    - Returns detailed statistics about the balance of conditions in each half
    """
    df_split = df.copy()
    df_split['half'] = np.nan
    
    # Track condition balance statistics
    balance_stats = {}
    
    for participant in df_split[participant_col].unique():
        participant_data = df_split[df_split[participant_col] == participant].copy()
        participant_stats = {'total_trials': len(participant_data), 'condition_balance': {}}
        
        if condition_cols and len(condition_cols) > 0:
            # Create condition combinations for stratified splitting
            participant_data['condition_combo'] = participant_data[condition_cols].apply(
                lambda x: '_'.join(x.astype(str)), axis=1)
            
            for condition in participant_data['condition_combo'].unique():
                # Get indices for this condition
                condition_mask = participant_data['condition_combo'] == condition
                condition_indices = participant_data.index[condition_mask]
                n_trials = len(condition_indices)
                
                if n_trials > 0:
                    # Randomly shuffle indices within this condition stratum
                    shuffled_condition_indices = condition_indices.to_numpy().copy()
                    np.random.shuffle(shuffled_condition_indices)
                    
                    half1_size = n_trials // 2
                    
                    # Assign first half1_size shuffled indices to half 1, rest to half 2
                    df_split.loc[shuffled_condition_indices[:half1_size], 'half'] = 1.0
                    df_split.loc[shuffled_condition_indices[half1_size:], 'half'] = 2.0
                    
                    # Record balance statistics
                    half1_count = half1_size
                    half2_count = n_trials - half1_size
                    participant_stats['condition_balance'][condition] = {
                        'total': n_trials,
                        'half1': half1_count,
                        'half2': half2_count,
                        'balance_ratio': min(half1_count, half2_count) / max(half1_count, half2_count) if max(half1_count, half2_count) > 0 else 1.0
                    }
        else:
            # Simple random assignment if no condition columns specified
            n_trials = len(participant_data)
            half1_size = n_trials // 2
            
            # Randomly shuffle participant indices
            shuffled_participant_indices = participant_data.index.to_numpy().copy()
            np.random.shuffle(shuffled_participant_indices)
            
            # Assign first half1_size shuffled indices to half 1, rest to half 2
            df_split.loc[shuffled_participant_indices[:half1_size], 'half'] = 1.0
            df_split.loc[shuffled_participant_indices[half1_size:], 'half'] = 2.0
            
            # Record basic balance statistics
            half1_count = half1_size
            half2_count = n_trials - half1_size
            participant_stats['condition_balance']['all_trials'] = {
                'total': n_trials,
                'half1': half1_count,
                'half2': half2_count,
                'balance_ratio': min(half1_count, half2_count) / max(half1_count, half2_count) if max(half1_count, half2_count) > 0 else 1.0
            }
        
        balance_stats[participant] = participant_stats
    
    # Calculate overall balance metrics
    overall_balance = calculate_overall_balance(balance_stats)
    df_split.attrs['balance_stats'] = balance_stats
    df_split.attrs['overall_balance'] = overall_balance
    
    return df_split

def calculate_overall_balance(balance_stats):
    """
    Calculate overall balance metrics from individual participant balance statistics.
    
    This function analyzes the balance statistics collected during trial splitting
    to determine how well the conditions were balanced across the two halves.
    A balance ratio of 1.0 indicates perfect balance, while lower values indicate
    increasingly unbalanced splits.
    
    Parameters:
    balance_stats (dict): Dictionary of balance statistics per participant
    
    Returns:
    dict: Overall balance metrics including:
        - total_conditions: Total number of condition combinations across all participants
        - balanced_conditions: Number of condition combinations with ratio >= 0.8
        - percent_balanced: Percentage of well-balanced conditions
        - mean_balance_ratio: Average balance ratio across all conditions
        - min_balance_ratio: Minimum balance ratio (worst case)
    """
    total_conditions = 0
    total_balanced_conditions = 0  # conditions with ratio >= 0.8
    balance_ratios = []
    
    for participant, stats in balance_stats.items():
        if not isinstance(stats, dict) or 'condition_balance' not in stats:
            continue
            
        for condition, condition_stats in stats['condition_balance'].items():
            if not isinstance(condition_stats, dict) or 'balance_ratio' not in condition_stats:
                continue
                
            total_conditions += 1
            ratio = condition_stats['balance_ratio']
            balance_ratios.append(ratio)
            if ratio >= 0.8:  # Consider a ratio of 0.8 or higher as well-balanced
                total_balanced_conditions += 1
    
    return {
        'total_conditions': total_conditions,
        'balanced_conditions': total_balanced_conditions,
        'percent_balanced': (total_balanced_conditions / total_conditions * 100) if total_conditions > 0 else 0,
        'mean_balance_ratio': np.mean(balance_ratios) if balance_ratios else 0,
        'min_balance_ratio': min(balance_ratios) if len(balance_ratios) > 0 else 0
    }

def calculate_vwm_slopes(df, error_col, condition_col, half_col, half_value):
    """
    Calculate VWM slope parameters for a specific half using specific condition differences.
    
    This function calculates slopes for VWM data by taking the difference between specific
    condition levels, following the methodology from Step 5:
    - For set size: difference between set size 4 and set size 2 (higher minus lower)
    - For delay: difference between 4s and 1s delay (longer minus shorter)
    
    Parameters:
    df (DataFrame): Input dataframe with VWM trial data
    error_col (str): Name of error column (e.g., 'VWM_error_absolute_degrees')
    condition_col (str): Name of condition column (e.g., 'VWM_setSize' or 'VWM_delay_s')
    half_col (str): Name of half column (typically 'half')
    half_value (int/float): Half value to filter for (1 or 2)
    
    Returns:
    dict: Dictionary with participant IDs as keys and calculated slopes as values
    """
    slopes = {}
    success_count = 0
    failure_count = 0
    half_data = df[df[half_col] == half_value]
    
    print(f"\nCalculating {condition_col} slopes for half {half_value}...")
    
    for participant in half_data['participantId'].unique():
        participant_data = half_data[half_data['participantId'] == participant]
        
        if len(participant_data) == 0:
            slopes[participant] = np.nan
            failure_count += 1
            continue
            
        # Calculate mean error for each condition
        condition_means = participant_data.groupby(condition_col)[error_col].mean()
        condition_counts = participant_data.groupby(condition_col)[error_col].count()
        
        if len(condition_means) < 2:
            slopes[participant] = np.nan
            failure_count += 1
            continue
        
        # Calculate slope based on specific condition differences
        if condition_col == 'VWM_setSize':
            # SetSize slope: difference between set size 4 and set size 2
            if 4.0 in condition_means and 2.0 in condition_means:
                slopes[participant] = condition_means[4.0] - condition_means[2.0]
                success_count += 1
            else:
                slopes[participant] = np.nan
                failure_count += 1
        elif condition_col == 'VWM_delay_s':
            # Delay slope: difference between 4s and 1s delay
            if 4.0 in condition_means and 1.0 in condition_means:
                slopes[participant] = condition_means[4.0] - condition_means[1.0]
                success_count += 1
            else:
                slopes[participant] = np.nan
                failure_count += 1
        else:
            # Fallback to max-min difference if condition column is unexpected
            conditions = sorted(condition_means.index)
            slopes[participant] = condition_means[conditions[-1]] - condition_means[conditions[0]]
            success_count += 1
    
    # Print summary statistics
    total = success_count + failure_count
    print(f"  Successfully calculated {condition_col} slopes for {success_count}/{total} participants ({success_count/total*100:.1f}%)")
    if failure_count > 0:
        print(f"  Failed to calculate slopes for {failure_count} participants due to missing conditions")
    
    return slopes

def calculate_mrt_slopes(df, rt_col, accuracy_col, angle_col, half_col, half_value):
    """
    Calculate MRT slope parameters for a specific half.
    
    This function calculates slopes for MRT data following the methodology from Step 6:
    - For RT: Uses only correct trials, applies log transformation, and calculates 
      unstandardized regression coefficient with angle as predictor
    - For Accuracy: Uses all trials and calculates unstandardized regression coefficient
      with angle as predictor
    
    Parameters:
    df (DataFrame): Input dataframe with MRT trial data
    rt_col (str): Name of reaction time column (e.g., 'MRT_rt_ms')
    accuracy_col (str): Name of accuracy column (e.g., 'MRT_isCorrect')
    angle_col (str): Name of angle column (e.g., 'MRT_angle_degrees')
    half_col (str): Name of half column (typically 'half')
    half_value (int/float): Half value to filter for (1 or 2)
    
    Returns:
    tuple: Dictionary with RT slopes, Dictionary with accuracy slopes
    """
    rt_slopes = {}
    accuracy_slopes = {}
    half_data = df[df[half_col] == half_value]
    
    success_rt_count = 0
    failure_rt_count = 0
    success_acc_count = 0
    failure_acc_count = 0
    
    print(f"\nCalculating MRT slopes for half {half_value}...")
    
    for participant in half_data['participantId'].unique():
        participant_data = half_data[half_data['participantId'] == participant]
        
        if len(participant_data) == 0:
            rt_slopes[participant] = np.nan
            accuracy_slopes[participant] = np.nan
            failure_rt_count += 1
            failure_acc_count += 1
            continue
        
        # For RT slope: Use only correct trials and apply log transformation
        correct_trials = participant_data[participant_data[accuracy_col] == True].copy()
        valid_rt_data = correct_trials[correct_trials[rt_col] > 0].copy()
        
        if len(valid_rt_data) < 2:
            rt_slopes[participant] = np.nan
            failure_rt_count += 1
        else:
            valid_rt_data['log_rt'] = np.log(valid_rt_data[rt_col])
            
            # Calculate RT slope
            try:
                X_rt = valid_rt_data[[angle_col]].values
                y_rt = valid_rt_data['log_rt'].values
                
                if len(np.unique(X_rt)) > 1:
                    reg_rt = LinearRegression().fit(X_rt, y_rt)
                    rt_slopes[participant] = reg_rt.coef_[0]
                    success_rt_count += 1
                else:
                    rt_slopes[participant] = np.nan
                    failure_rt_count += 1
            except Exception as e:
                rt_slopes[participant] = np.nan
                failure_rt_count += 1
        
        # Calculate accuracy slope (using all trials)
        try:
            X_acc = participant_data[[angle_col]].values
            y_acc = participant_data[accuracy_col].astype(float).values
            
            if len(np.unique(X_acc)) > 1:
                reg_acc = LinearRegression().fit(X_acc, y_acc)
                accuracy_slopes[participant] = reg_acc.coef_[0]
                success_acc_count += 1
            else:
                accuracy_slopes[participant] = np.nan
                failure_acc_count += 1
        except Exception as e:
            accuracy_slopes[participant] = np.nan
            failure_acc_count += 1
    
    # Print summary statistics
    total_rt = success_rt_count + failure_rt_count
    total_acc = success_acc_count + failure_acc_count
    
    print(f"  Successfully calculated RT slopes for {success_rt_count}/{total_rt} participants ({success_rt_count/total_rt*100:.1f}%)")
    if failure_rt_count > 0:
        print(f"  Failed to calculate RT slopes for {failure_rt_count} participants due to insufficient data or errors")
    
    print(f"  Successfully calculated Accuracy slopes for {success_acc_count}/{total_acc} participants ({success_acc_count/total_acc*100:.1f}%)")
    if failure_acc_count > 0:
        print(f"  Failed to calculate Accuracy slopes for {failure_acc_count} participants due to insufficient data or errors")
    
    return rt_slopes, accuracy_slopes

def main():
    """
    Main function to perform split-half reliability analysis.
    """
    try:
        # Set random seed for reproducibility
        np.random.seed(42)
        
        print("Starting split-half reliability analysis...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Find input files
        print("Looking for input files...")
        vwm_pattern = 'outputs/VWM_cleaned_data_*.csv'
        mrt_pattern = 'outputs/MRT_cleaned_data_*.csv'
        
        vwm_file = find_latest_file(vwm_pattern)
        mrt_file = find_latest_file(mrt_pattern)
        
        if vwm_file is None:
            print(f"Error: No VWM file found matching pattern {vwm_pattern}")
            return 1
        if mrt_file is None:
            print(f"Error: No MRT file found matching pattern {mrt_pattern}")
            return 1
            
        print(f"Found VWM file: {vwm_file}")
        print(f"Found MRT file: {mrt_file}")
        
        # Load data
        print("\nLoading VWM data...")
        vwm_df = pd.read_csv(vwm_file)
        vwm_df.columns = [col.strip() for col in vwm_df.columns]
        print(f"VWM data shape: {vwm_df.shape}")
        print("VWM columns:", list(vwm_df.columns))
        print("First 3 rows of VWM data:")
        print(vwm_df.head(3))
        
        print("\nLoading MRT data...")
        mrt_df = pd.read_csv(mrt_file)
        mrt_df.columns = [col.strip() for col in mrt_df.columns]
        print(f"MRT data shape: {mrt_df.shape}")
        print("MRT columns:", list(mrt_df.columns))
        print("First 3 rows of MRT data:")
        print(mrt_df.head(3))
        
        # Validate required columns (after column names have been stripped)
        vwm_required = ['participantId', 'VWM_trial', 'VWM_setSize', 'VWM_delay_s', 
                       'VWM_error_absolute_degrees', 'excluded_participant', 'valid_trial', 'isPractice', 'VWM_isAttentionCheck']
        mrt_required = ['participantId', 'MRT_trial', 'MRT_angle_degrees', 'MRT_isCorrect', 
                       'MRT_rt_ms', 'excluded_participant', 'valid_trial', 'isPractice', 'MRT_isAttentionCheck']
        
        missing_vwm = [col for col in vwm_required if col not in vwm_df.columns]
        missing_mrt = [col for col in mrt_required if col not in mrt_df.columns]
        
        if missing_vwm:
            print(f"Error: Missing VWM columns: {missing_vwm}")
            return 1
        if missing_mrt:
            print(f"Error: Missing MRT columns: {missing_mrt}")
            return 1
        
        print("All required columns found!")
        
        # Print unique values for key experimental design parameters
        print("\nVWM experimental design parameters:")
        print(f"VWM_setSize unique values: {sorted(vwm_df['VWM_setSize'].unique())}")
        print(f"VWM_delay_s unique values: {sorted(vwm_df['VWM_delay_s'].unique())}")
        print(f"excluded_participant unique values: {sorted(vwm_df['excluded_participant'].unique())}")
        print(f"valid_trial unique values: {sorted(vwm_df['valid_trial'].unique())}")
        print(f"isPractice unique values: {sorted(vwm_df['isPractice'].unique())}")
        print(f"VWM_isAttentionCheck unique values: {sorted(vwm_df['VWM_isAttentionCheck'].unique())}")
        
        print("\nMRT experimental design parameters:")
        print(f"MRT_angle_degrees unique values: {sorted(mrt_df['MRT_angle_degrees'].unique())}")
        print(f"excluded_participant unique values: {sorted(mrt_df['excluded_participant'].unique())}")
        print(f"valid_trial unique values: {sorted(mrt_df['valid_trial'].unique())}")
        print(f"isPractice unique values: {sorted(mrt_df['isPractice'].unique())}")
        print(f"MRT_isAttentionCheck unique values: {sorted(mrt_df['MRT_isAttentionCheck'].unique())}")
        
        # Filter data
        print("\nFiltering data...")
        print(f"VWM data before filtering: {len(vwm_df)} rows")
        vwm_filtered = vwm_df[
            (vwm_df['excluded_participant'] == False) & 
            (vwm_df['isPractice'] == False) & 
            (vwm_df['valid_trial'] == True) &
            (vwm_df['VWM_isAttentionCheck'] == False)
        ].copy()
        
        # Remove rows with null values in key columns
        vwm_filtered = vwm_filtered.dropna(subset=['VWM_error_absolute_degrees', 'VWM_setSize', 'VWM_delay_s'])
        print(f"VWM data after filtering: {len(vwm_filtered)} rows")
        
        print(f"MRT data before filtering: {len(mrt_df)} rows")
        mrt_filtered = mrt_df[
            (mrt_df['excluded_participant'] == False) & 
            (mrt_df['isPractice'] == False) & 
            (mrt_df['valid_trial'] == True) &
            (mrt_df['MRT_isAttentionCheck'] == False)
        ].copy()
        
        # Remove rows with null values in key columns
        mrt_filtered = mrt_filtered.dropna(subset=['MRT_rt_ms', 'MRT_isCorrect', 'MRT_angle_degrees'])
        print(f"MRT data after filtering: {len(mrt_filtered)} rows")
        
        # Get participant lists
        vwm_participants = set(vwm_filtered['participantId'].unique())
        mrt_participants = set(mrt_filtered['participantId'].unique())
        common_participants = vwm_participants.intersection(mrt_participants)
        
        print(f"\nVWM participants: {len(vwm_participants)}")
        print(f"MRT participants: {len(mrt_participants)}")
        print(f"Common participants: {len(common_participants)}")
        
        # Filter to common participants only
        vwm_filtered = vwm_filtered[vwm_filtered['participantId'].isin(common_participants)]
        mrt_filtered = mrt_filtered[mrt_filtered['participantId'].isin(common_participants)]
        
        print(f"VWM data with common participants: {len(vwm_filtered)} rows")
        print(f"MRT data with common participants: {len(mrt_filtered)} rows")
        
        # Split trials randomly with condition balancing
        print("\nSplitting trials randomly with condition balancing...")
        vwm_split = split_trials_randomly(vwm_filtered, 'participantId', 'VWM_trial', 
                                         condition_cols=['VWM_setSize', 'VWM_delay_s'])
        mrt_split = split_trials_randomly(mrt_filtered, 'participantId', 'MRT_trial',
                                         condition_cols=['MRT_angle_degrees'])
        
        # Print detailed condition balance information
        print("\nVWM condition balance after splitting:")
        vwm_condition_counts = vwm_split.groupby(['half', 'VWM_setSize', 'VWM_delay_s']).size().reset_index(name='count')
        print(vwm_condition_counts.to_string(index=False))
        
        # Print overall VWM balance metrics
        vwm_balance = vwm_split.attrs['overall_balance']
        print("\nVWM overall balance metrics:")
        print(f"Total condition combinations: {vwm_balance['total_conditions']}")
        print(f"Well-balanced conditions (ratio ≥ 0.8): {vwm_balance['balanced_conditions']} ({vwm_balance['percent_balanced']:.1f}%)")
        print(f"Mean balance ratio: {vwm_balance['mean_balance_ratio']:.3f}")
        print(f"Minimum balance ratio: {vwm_balance['min_balance_ratio']:.3f}")
        
        if vwm_balance['percent_balanced'] < 90:
            print("WARNING: Less than 90% of VWM conditions are well-balanced between halves.")
            print("RECOMMENDATION: This may affect reliability estimates. Consider using a more balanced design in future studies.")
        
        print("\nMRT condition balance after splitting:")
        mrt_condition_counts = mrt_split.groupby(['half', 'MRT_angle_degrees']).size().reset_index(name='count')
        print(mrt_condition_counts.to_string(index=False))
        
        # Print overall MRT balance metrics
        mrt_balance = mrt_split.attrs['overall_balance']
        print("\nMRT overall balance metrics:")
        print(f"Total condition combinations: {mrt_balance['total_conditions']}")
        print(f"Well-balanced conditions (ratio ≥ 0.8): {mrt_balance['balanced_conditions']} ({mrt_balance['percent_balanced']:.1f}%)")
        print(f"Mean balance ratio: {mrt_balance['mean_balance_ratio']:.3f}")
        print(f"Minimum balance ratio: {mrt_balance['min_balance_ratio']:.3f}")
        
        if mrt_balance['percent_balanced'] < 90:
            print("WARNING: Less than 90% of MRT conditions are well-balanced between halves.")
            print("RECOMMENDATION: This may affect reliability estimates. Consider using a more balanced design in future studies.")
        
        print("VWM split summary:")
        print(vwm_split['half'].value_counts())
        print("MRT split summary:")
        print(mrt_split['half'].value_counts())
        
        # Calculate slopes for each half
        print("\nCalculating VWM slopes...")
        
        # VWM SetSize slopes
        vwm_setsize_half1 = calculate_vwm_slopes(vwm_split, 'VWM_error_absolute_degrees', 'VWM_setSize', 'half', 1)
        vwm_setsize_half2 = calculate_vwm_slopes(vwm_split, 'VWM_error_absolute_degrees', 'VWM_setSize', 'half', 2)
        
        # VWM Delay slopes
        vwm_delay_half1 = calculate_vwm_slopes(vwm_split, 'VWM_error_absolute_degrees', 'VWM_delay_s', 'half', 1)
        vwm_delay_half2 = calculate_vwm_slopes(vwm_split, 'VWM_error_absolute_degrees', 'VWM_delay_s', 'half', 2)
        
        print("Calculating MRT slopes...")
        
        # MRT slopes
        mrt_rt_half1, mrt_acc_half1 = calculate_mrt_slopes(mrt_split, 'MRT_rt_ms', 'MRT_isCorrect', 'MRT_angle_degrees', 'half', 1)
        mrt_rt_half2, mrt_acc_half2 = calculate_mrt_slopes(mrt_split, 'MRT_rt_ms', 'MRT_isCorrect', 'MRT_angle_degrees', 'half', 2)
        
        # Create split-half slopes dataframe
        print("\nCreating split-half slopes dataframe...")
        participants = sorted(common_participants)
        
        split_half_data = {
            'participantId': participants,
            'VWM_Error_SetSize_Slope_Half1': [vwm_setsize_half1.get(p, np.nan) for p in participants],
            'VWM_Error_SetSize_Slope_Half2': [vwm_setsize_half2.get(p, np.nan) for p in participants],
            'VWM_Error_Delay_Slope_Half1': [vwm_delay_half1.get(p, np.nan) for p in participants],
            'VWM_Error_Delay_Slope_Half2': [vwm_delay_half2.get(p, np.nan) for p in participants],
            'MRT_RT_Angle_Slope_Half1': [mrt_rt_half1.get(p, np.nan) for p in participants],
            'MRT_RT_Angle_Slope_Half2': [mrt_rt_half2.get(p, np.nan) for p in participants],
            'MRT_Accuracy_Angle_Slope_Half1': [mrt_acc_half1.get(p, np.nan) for p in participants],
            'MRT_Accuracy_Angle_Slope_Half2': [mrt_acc_half2.get(p, np.nan) for p in participants]
        }
        
        split_half_df = pd.DataFrame(split_half_data)
        print("Split-half slopes dataframe shape:", split_half_df.shape)
        print("First 2 rows of split-half slopes:")
        print(split_half_df.head(2))
        
        # Calculate reliability coefficients
        print("\nCalculating reliability coefficients...")
        
        slope_pairs = [
            ('VWM_Error_SetSize_Slope', 'VWM_Error_SetSize_Slope_Half1', 'VWM_Error_SetSize_Slope_Half2'),
            ('VWM_Error_Delay_Slope', 'VWM_Error_Delay_Slope_Half1', 'VWM_Error_Delay_Slope_Half2'),
            ('MRT_RT_Angle_Slope', 'MRT_RT_Angle_Slope_Half1', 'MRT_RT_Angle_Slope_Half2'),
            ('MRT_Accuracy_Angle_Slope', 'MRT_Accuracy_Angle_Slope_Half1', 'MRT_Accuracy_Angle_Slope_Half2')
        ]
        
        reliability_results = []
        
        for slope_name, half1_col, half2_col in slope_pairs:
            print(f"\nProcessing {slope_name}...")
            
            # Get data for both halves
            half1_data = split_half_df[half1_col].dropna()
            half2_data = split_half_df[half2_col].dropna()
            
            # Find common participants with data in both halves
            half1_participants = split_half_df[split_half_df[half1_col].notna()]['participantId']
            half2_participants = split_half_df[split_half_df[half2_col].notna()]['participantId']
            common_slope_participants = set(half1_participants).intersection(set(half2_participants))
            
            if len(common_slope_participants) < 3:
                print(f"Warning: Insufficient data for {slope_name} (n={len(common_slope_participants)})")
                reliability_results.append({
                    'slope_parameter': slope_name,
                    'split_half_correlation': np.nan,
                    'spearman_brown_reliability': np.nan,
                    'reliability_ci_lower': np.nan,
                    'reliability_ci_upper': np.nan,
                    'reliability_classification': 'Insufficient data',
                    'n_participants': len(common_slope_participants)
                })
                continue
            
            # Get matched data
            matched_df = split_half_df[split_half_df['participantId'].isin(common_slope_participants)]
            
            # Ensure we have data before proceeding
            if len(matched_df) == 0:
                print(f"Warning: No matched data found for {slope_name}")
                reliability_results.append({
                    'slope_parameter': slope_name,
                    'split_half_correlation': np.nan,
                    'spearman_brown_reliability': np.nan,
                    'reliability_ci_lower': np.nan,
                    'reliability_ci_upper': np.nan,
                    'reliability_classification': 'Insufficient data',
                    'n_participants': 0
                })
                continue
                
            matched_half1 = matched_df[half1_col].values
            matched_half2 = matched_df[half2_col].values
            
            # Remove any remaining NaN values
            valid_indices = ~(np.isnan(matched_half1) | np.isnan(matched_half2))
            matched_half1 = matched_half1[valid_indices]
            matched_half2 = matched_half2[valid_indices]
            
            n_valid = len(matched_half1)
            print(f"Valid participants for {slope_name}: {n_valid}")
            
            if n_valid < 3:
                print(f"Warning: Insufficient valid data for {slope_name} (n={n_valid})")
                reliability_results.append({
                    'slope_parameter': slope_name,
                    'split_half_correlation': np.nan,
                    'spearman_brown_reliability': np.nan,
                    'reliability_ci_lower': np.nan,
                    'reliability_ci_upper': np.nan,
                    'reliability_classification': 'Insufficient data',
                    'n_participants': n_valid
                })
                continue
            
            # Calculate correlation
            try:
                correlation, p_value = pearsonr(matched_half1, matched_half2)
                print(f"Split-half correlation for {slope_name}: r = {correlation:.3f}, p = {p_value:.3f}")
                
                # Apply Spearman-Brown correction
                if pd.isna(correlation) or correlation <= -1.0:
                    reliability = np.nan
                else:
                    reliability = (2 * correlation) / (1 + correlation)
                
                print(f"Spearman-Brown reliability for {slope_name}: {reliability:.3f}")
                
                # Calculate confidence intervals on the raw correlation first
                try:
                    ci_lower_r, ci_upper_r = calculate_confidence_interval(correlation, n_valid)
                except Exception as e:
                    print(f"Warning: Could not calculate confidence intervals for {slope_name}: {e}")
                    ci_lower_r, ci_upper_r = np.nan, np.nan
                
                # Apply Spearman-Brown correction to CI bounds
                ci_lower = np.nan
                if not pd.isna(ci_lower_r):
                    # ci_lower_r is guaranteed to be > -1.0 if not NaN by calculate_confidence_interval
                    ci_lower = (2 * ci_lower_r) / (1 + ci_lower_r)

                ci_upper = np.nan
                if not pd.isna(ci_upper_r):
                    # ci_upper_r is guaranteed to be > -1.0 if not NaN by calculate_confidence_interval
                    ci_upper = (2 * ci_upper_r) / (1 + ci_upper_r)
                
                # Classify reliability
                classification = classify_reliability(reliability)
                
                reliability_results.append({
                    'slope_parameter': slope_name,
                    'split_half_correlation': correlation,
                    'spearman_brown_reliability': reliability,
                    'reliability_ci_lower': ci_lower,
                    'reliability_ci_upper': ci_upper,
                    'reliability_classification': classification,
                    'n_participants': n_valid
                })
                
            except Exception as e:
                print(f"Error calculating reliability for {slope_name}: {e}")
                reliability_results.append({
                    'slope_parameter': slope_name,
                    'split_half_correlation': np.nan,
                    'spearman_brown_reliability': np.nan,
                    'reliability_ci_lower': np.nan,
                    'reliability_ci_upper': np.nan,
                    'reliability_classification': 'Calculation error',
                    'n_participants': n_valid
                })
        
        # Create reliability results dataframe
        reliability_df = pd.DataFrame(reliability_results)
        print("\nReliability results:")
        print(reliability_df)
        
        # Save output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"\nSaving output files with timestamp {timestamp}...")
        
        # Save reliability analysis
        reliability_file = f'outputs/reliability_analysis_{timestamp}.csv'
        reliability_df.to_csv(reliability_file, index=False)
        print(f"Saved reliability analysis to: {reliability_file}")
        
        # Save split-half slopes
        slopes_file = f'outputs/split_half_slopes_{timestamp}.csv'
        split_half_df.to_csv(slopes_file, index=False)
        print(f"Saved split-half slopes to: {slopes_file}")
        
        # Print summary of reliability findings
        print("\n=== RELIABILITY ANALYSIS SUMMARY ===")
        print("Note: Reliability estimates may be affected by condition balance quality.")
        print(f"VWM condition balance: {vwm_balance['percent_balanced']:.1f}% well-balanced")
        print(f"MRT condition balance: {mrt_balance['percent_balanced']:.1f}% well-balanced")
        print("\nReliability coefficients:")
        
        for _, row in reliability_df.iterrows():
            slope = row['slope_parameter']
            reliability = row['spearman_brown_reliability']
            classification = row['reliability_classification']
            n = row['n_participants']
            correlation = row['split_half_correlation']
            
            print(f"{slope}:")
            print(f"  Split-half correlation: r = {correlation:.3f}")
            print(f"  Spearman-Brown reliability: {reliability:.3f} ({classification})")
            print(f"  Sample size: {n}")
            
            if classification == 'Poor':
                print(f"  WARNING: {slope} shows poor reliability - interpret correlations with caution")
            elif classification in ['Insufficient data', 'Calculation error']:
                print(f"  WARNING: {slope} reliability could not be calculated")
            
            # Add a blank line for readability
            print("")
        
        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
