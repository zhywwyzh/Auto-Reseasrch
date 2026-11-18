import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime

def load_latest_inclusion_file():
    """
    Load the most recent participant inclusion status file.
    
    Returns:
        pd.DataFrame: DataFrame containing participant inclusion status
    """
    print("Loading participant inclusion status file...")
    
    # Find all matching inclusion files
    inclusion_pattern = "outputs/participant_inclusion_status_*.csv"
    inclusion_files = glob.glob(inclusion_pattern)
    
    if not inclusion_files:
        raise FileNotFoundError(f"No inclusion status files found matching pattern: {inclusion_pattern}")
    
    # Get the most recent file
    latest_inclusion_file = max(inclusion_files, key=os.path.getctime)
    print(f"Using inclusion file: {latest_inclusion_file}")
    
    # Load the inclusion status file
    inclusion_df = pd.read_csv(latest_inclusion_file)
    
    print("Inclusion file columns:", list(inclusion_df.columns))
    print("First 3 rows of inclusion file:")
    print(inclusion_df.head(3))
    
    # Verify required columns exist
    required_inclusion_cols = ['participantId', 'included']
    missing_cols = [col for col in required_inclusion_cols if col not in inclusion_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in inclusion file: {missing_cols}")
    
    print(f"Total participants in inclusion file: {len(inclusion_df)}")
    print(f"Included participants: {inclusion_df['included'].sum()}")
    print(f"Excluded participants: {(~inclusion_df['included']).sum()}")
    
    return inclusion_df

def load_task_data_files():
    """
    Load all participant task data files.
    
    Returns:
        pd.DataFrame: Combined DataFrame containing all task data
    """
    print("Loading task data files...")
    
    # Find all matching task data files
    data_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    data_files = glob.glob(data_pattern)
    
    if not data_files:
        raise FileNotFoundError(f"No task data files found matching pattern: {data_pattern}")
    
    print(f"Found {len(data_files)} task data files")
    
    all_data = []
    
    for file_path in data_files:
        print(f"Loading file: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print(f"File shape: {df.shape}")
            all_data.append(df)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No valid task data files could be loaded")
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined data shape: {combined_df.shape}")
    
    print("Combined data columns:", list(combined_df.columns))
    print("First 3 rows of combined data:")
    print(combined_df.head(3))
    
    return combined_df

def filter_mrt_data(df):
    """
    Filter the combined dataframe to only include MRT task data.
    
    Args:
        df (pd.DataFrame): Combined task data
        
    Returns:
        pd.DataFrame: Filtered MRT data
    """
    print("Filtering for MRT task data...")
    
    # Check required columns for MRT task
    required_mrt_cols = [
        'participantId', 'table', 'isPractice', 'MRT_trial', 'MRT_stimulusId',
        'MRT_angle_degrees', 'MRT_isReflected', 'MRT_response', 'MRT_isCorrect',
        'MRT_rt_ms', 'MRT_timeout', 'MRT_block', 'MRT_isAttentionCheck'
    ]
    
    missing_cols = [col for col in required_mrt_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required MRT columns: {missing_cols}")
    
    # Filter to rows where MRT task was active (non-null MRT_trial)
    mrt_data = df[df['MRT_trial'].notna()].copy()
    print(f"MRT task rows: {len(mrt_data)}")

    # Convert data types for key columns
    print("Converting data types...")
    mrt_data['MRT_isCorrect'] = pd.to_numeric(mrt_data['MRT_isCorrect'], errors='coerce').astype('boolean')
    mrt_data['MRT_timeout'] = pd.to_numeric(mrt_data['MRT_timeout'], errors='coerce').astype('boolean')
    mrt_data['MRT_isAttentionCheck'] = pd.to_numeric(mrt_data['MRT_isAttentionCheck'], errors='coerce').astype('boolean')
    mrt_data['MRT_rt_ms'] = pd.to_numeric(mrt_data['MRT_rt_ms'], errors='coerce')

    if len(mrt_data) == 0:
        raise ValueError("No MRT task data found")
    
    # Print unique values for key experimental design parameters
    print("Unique values for MRT experimental design parameters:")
    print(f"MRT_angle_degrees: {sorted(mrt_data['MRT_angle_degrees'].dropna().unique())}")
    print(f"MRT_isReflected: {sorted(mrt_data['MRT_isReflected'].dropna().unique())}")
    print(f"MRT_block: {sorted(mrt_data['MRT_block'].dropna().unique())}")
    print(f"MRT_isAttentionCheck: {sorted(mrt_data['MRT_isAttentionCheck'].dropna().unique())}")
    print(f"table values: {sorted(mrt_data['table'].dropna().unique())}")
    print(f"isPractice values: {sorted(mrt_data['isPractice'].dropna().unique())}")
    print(f"MRT_response values: {sorted(mrt_data['MRT_response'].dropna().unique())}")
    
    # Print data types for measured variables
    print("Data types for measured variables:")
    print(f"MRT_rt_ms type: {mrt_data['MRT_rt_ms'].dtype}")
    print(f"MRT_isCorrect type: {mrt_data['MRT_isCorrect'].dtype}")
    print(f"MRT_timeout type: {mrt_data['MRT_timeout'].dtype}")
    
    return mrt_data

def filter_to_included_participants(mrt_data, inclusion_df):
    """
    Filter MRT data to only included participants.
    
    Args:
        mrt_data (pd.DataFrame): MRT task data
        inclusion_df (pd.DataFrame): Participant inclusion status
        
    Returns:
        pd.DataFrame: Filtered MRT data for included participants
    """
    print("Filtering to included participants only...")
    
    # Get list of included participants
    included_participants = inclusion_df[inclusion_df['included'] == True]['participantId'].tolist()
    print(f"Number of included participants: {len(included_participants)}")
    
    # Filter MRT data to included participants
    filtered_data = mrt_data[mrt_data['participantId'].isin(included_participants)].copy()
    print(f"MRT data after filtering to included participants: {len(filtered_data)} rows")
    
    unique_participants = filtered_data['participantId'].nunique()
    print(f"Unique participants in filtered MRT data: {unique_participants}")
    
    return filtered_data

def apply_trial_exclusions(mrt_data):
    """
    Apply trial-level exclusions to MRT data using cascaded logic.
    
    Args:
        mrt_data (pd.DataFrame): MRT data for included participants
        
    Returns:
        pd.DataFrame: MRT data with exclusion flags
    """
    print("Applying trial-level exclusions (cascaded)...")
    
    # Initialize exclusion flags
    mrt_data['excluded_timeout'] = False
    mrt_data['excluded_anticipatory_response'] = False
    mrt_data['excluded_extremely_slow_response'] = False
    mrt_data['excluded_invalid_response'] = False
    mrt_data['excluded_attention_check_failure'] = False

    initial_trials = len(mrt_data)
    print(f"Initial number of trials: {initial_trials}")

    already_excluded = pd.Series(False, index=mrt_data.index)

    # a. Timeout exclusions
    timeout_mask = (mrt_data['MRT_timeout'] == True) & (~already_excluded)
    mrt_data.loc[timeout_mask, 'excluded_timeout'] = True
    timeout_count = timeout_mask.sum()
    already_excluded = already_excluded | timeout_mask
    print(f"Trials excluded for timeout: {timeout_count} ({timeout_count/initial_trials*100:.2f}%)")

    # b. Anticipatory response exclusions
    anticipatory_mask = (mrt_data['MRT_rt_ms'] < 200) & (~already_excluded)
    mrt_data.loc[anticipatory_mask, 'excluded_anticipatory_response'] = True
    anticipatory_count = anticipatory_mask.sum()
    already_excluded = already_excluded | anticipatory_mask
    print(f"Trials excluded for anticipatory response: {anticipatory_count} ({anticipatory_count/initial_trials*100:.2f}%)")

    # c. Extremely slow response exclusions
    slow_mask = (mrt_data['MRT_rt_ms'] > 10000) & (~already_excluded)
    mrt_data.loc[slow_mask, 'excluded_extremely_slow_response'] = True
    slow_count = slow_mask.sum()
    already_excluded = already_excluded | slow_mask
    print(f"Trials excluded for extremely slow response: {slow_count} ({slow_count/initial_trials*100:.2f}%)")

    # d. Invalid response exclusions (only 'b' and 'n' are valid)
    invalid_response_mask = (
        (mrt_data['MRT_response'].isna() | (~mrt_data['MRT_response'].isin(['b', 'n'])))
        & (~already_excluded)
    )
    mrt_data.loc[invalid_response_mask, 'excluded_invalid_response'] = True
    invalid_count = invalid_response_mask.sum()
    already_excluded = already_excluded | invalid_response_mask
    print(f"Trials excluded for invalid response: {invalid_count} ({invalid_count/initial_trials*100:.2f}%)")
    print(f"Response value distribution (after exclusions): {mrt_data.loc[~already_excluded, 'MRT_response'].value_counts().to_dict()}")

    # e. Attention check failure exclusions
    attention_check_mask = (
        (mrt_data['MRT_isAttentionCheck'] == True) &
        (mrt_data['MRT_isCorrect'] == False) &
        (~already_excluded)
    )
    mrt_data.loc[attention_check_mask, 'excluded_attention_check_failure'] = True
    attention_count = attention_check_mask.sum()
    already_excluded = already_excluded | attention_check_mask
    print(f"Trials excluded for attention check failure: {attention_count} ({attention_count/initial_trials*100:.2f}%)")

    print(f"Total trials remaining after all exclusions: {(~already_excluded).sum()}")

    return mrt_data

def process_reaction_times(mrt_data):
    """
    Process reaction times for correct trials and identify outliers.
    
    Args:
        mrt_data (pd.DataFrame): MRT data with exclusion flags
        
    Returns:
        pd.DataFrame: MRT data with log RT and outlier flags
    """
    print("Processing reaction times...")
    
    # Initialize columns
    mrt_data['log_response_time_ms'] = np.nan
    mrt_data['excluded_rt_outlier'] = False
    
    # Calculate any trial exclusion (for general validity)
    any_exclusion = (
        mrt_data['excluded_timeout'] |
        mrt_data['excluded_anticipatory_response'] |
        mrt_data['excluded_extremely_slow_response'] |
        mrt_data['excluded_invalid_response'] |
        mrt_data['excluded_attention_check_failure']
    )
    
    # Log-transform reaction times for correct trials that are not excluded
    correct_valid_mask = (
        (mrt_data['MRT_isCorrect'] == True) &
        (~any_exclusion)
    )
    
    print(f"Correct and valid trials for RT processing: {correct_valid_mask.sum()}")
    
    # Calculate log RT for valid correct trials
    valid_rt_data = mrt_data.loc[correct_valid_mask, 'MRT_rt_ms']
    mrt_data.loc[correct_valid_mask, 'log_response_time_ms'] = np.log(valid_rt_data)
    
    # Identify RT outliers by participant and angle
    print("Identifying RT outliers by participant and angle...")
    
    outlier_count = 0
    for participant in mrt_data['participantId'].unique():
        participant_mask = mrt_data['participantId'] == participant
        
        for angle in mrt_data['MRT_angle_degrees'].dropna().unique():
            angle_mask = mrt_data['MRT_angle_degrees'] == angle
            
            # Get correct, valid trials for this participant and angle
            condition_mask = participant_mask & angle_mask & correct_valid_mask
            condition_data = mrt_data.loc[condition_mask, 'log_response_time_ms'].dropna()
            
            if len(condition_data) > 0:
                mean_log_rt = condition_data.mean()
                std_log_rt = condition_data.std()
                
                if not np.isnan(std_log_rt) and std_log_rt > 0:
                    # Identify outliers (more than 3 SDs from mean)
                    outlier_mask = (
                        condition_mask &
                        (
                            (mrt_data['log_response_time_ms'] > (mean_log_rt + 3 * std_log_rt)) |
                            (mrt_data['log_response_time_ms'] < (mean_log_rt - 3 * std_log_rt))
                        )
                    )
                    
                    mrt_data.loc[outlier_mask, 'excluded_rt_outlier'] = True
                    outlier_count += outlier_mask.sum()
    
    print(f"Trials flagged as RT outliers: {outlier_count}")
    
    return mrt_data

def create_validity_flags(mrt_data):
    """
    Create trial validity flags for accuracy and RT analyses.
    
    Args:
        mrt_data (pd.DataFrame): MRT data with all exclusion flags
        
    Returns:
        pd.DataFrame: MRT data with validity flags
    """
    print("Creating trial validity flags...")
    
    # General exclusions that apply to both accuracy and RT analyses
    general_exclusions = (
        mrt_data['excluded_timeout'] |
        mrt_data['excluded_anticipatory_response'] |
        mrt_data['excluded_extremely_slow_response'] |
        mrt_data['excluded_invalid_response'] |
        mrt_data['excluded_attention_check_failure']
    )
    
    # Trial valid for accuracy analysis (no general exclusions)
    mrt_data['trial_valid_accuracy_analysis'] = ~general_exclusions
    
    # Trial valid for RT analysis (no general exclusions, no RT outliers, correct responses only)
    mrt_data['trial_valid_rt_analysis'] = (
        ~general_exclusions &
        ~mrt_data['excluded_rt_outlier'] &
        (mrt_data['MRT_isCorrect'] == True)
    )
    
    print(f"Trials valid for accuracy analysis: {mrt_data['trial_valid_accuracy_analysis'].sum()}")
    print(f"Trials valid for RT analysis: {mrt_data['trial_valid_rt_analysis'].sum()}")
    
    return mrt_data

def separate_practice_test_trials(mrt_data):
    """
    Separate practice and test trials and create trial type column.
    
    Args:
        mrt_data (pd.DataFrame): MRT data
        
    Returns:
        pd.DataFrame: MRT data with trial type column
    """
    print("Separating practice and test trials...")
    
    # Create trial type column
    practice_mask = (mrt_data['table'] == 'mrt_practice') | (mrt_data['isPractice'] == True)
    test_mask = (mrt_data['table'] == 'mrt_test') | (mrt_data['isPractice'] == False)
    
    mrt_data['trial_type'] = 'unknown'
    mrt_data.loc[practice_mask, 'trial_type'] = 'practice'
    mrt_data.loc[test_mask, 'trial_type'] = 'test'
    
    print(f"Practice trials: {(mrt_data['trial_type'] == 'practice').sum()}")
    print(f"Test trials: {(mrt_data['trial_type'] == 'test').sum()}")
    print(f"Unknown trial type: {(mrt_data['trial_type'] == 'unknown').sum()}")
    
    return mrt_data

def create_cleaned_output(mrt_data):
    """
    Create cleaned trial data output with required columns.
    
    Args:
        mrt_data (pd.DataFrame): Processed MRT data
        
    Returns:
        pd.DataFrame: Cleaned data with required output columns
    """
    print("Creating cleaned output data...")
    
    # Create output dataframe with required columns
    output_data = pd.DataFrame({
        'participantId': mrt_data['participantId'],
        'trial_number': mrt_data['MRT_trial'],
        'stimulus_id': mrt_data['MRT_stimulusId'],
        'rotation_angle_degrees': mrt_data['MRT_angle_degrees'],
        'is_reflected': mrt_data['MRT_isReflected'],
        'response': mrt_data['MRT_response'],
        'is_correct': mrt_data['MRT_isCorrect'],
        'response_time_ms': mrt_data['MRT_rt_ms'],
        'log_response_time_ms': mrt_data['log_response_time_ms'],
        'trial_type': mrt_data['trial_type'],
        'block_number': mrt_data['MRT_block'],
        'is_attention_check': mrt_data['MRT_isAttentionCheck'],
        'excluded_timeout': mrt_data['excluded_timeout'],
        'excluded_anticipatory_response': mrt_data['excluded_anticipatory_response'],
        'excluded_extremely_slow_response': mrt_data['excluded_extremely_slow_response'],
        'excluded_invalid_response': mrt_data['excluded_invalid_response'],
        'excluded_attention_check_failure': mrt_data['excluded_attention_check_failure'],
        'excluded_rt_outlier': mrt_data['excluded_rt_outlier'],
        'trial_valid_accuracy_analysis': mrt_data['trial_valid_accuracy_analysis'],
        'trial_valid_rt_analysis': mrt_data['trial_valid_rt_analysis']
    })

    # Map coded responses to readable format, keeping '0' as None for timeouts
    response_mapping = {'b': 'same', 'n': 'different', '0': None}
    output_data['response'] = output_data['response'].map(response_mapping)

    print(f"Output data shape: {output_data.shape}")
    print("Output data columns:", list(output_data.columns))
    print("First 2 rows of output data:")
    print(output_data.head(2))
    
    return output_data

def create_exclusion_log(mrt_data):
    """
    Create trial exclusion log summary using cascaded counts.
    
    Args:
        mrt_data (pd.DataFrame): MRT data with exclusion flags
        
    Returns:
        pd.DataFrame: Exclusion log summary
    """
    print("Creating exclusion log (cascaded counts)...")
    
    total_trials = len(mrt_data)
    exclusion_data = []

    # Cascaded logic: count only those excluded at each step, not previously excluded
    already_excluded = pd.Series(False, index=mrt_data.index)

    # a. Timeout
    timeout_mask = (mrt_data['excluded_timeout'] == True) & (~already_excluded)
    timeout_count = timeout_mask.sum()
    exclusion_data.append({
        'exclusion_criterion': 'timeout',
        'count_excluded': timeout_count,
        'total_trials_assessed': total_trials,
        'exclusion_percentage': (timeout_count / total_trials) * 100
    })
    already_excluded = already_excluded | timeout_mask

    # b. Anticipatory response
    anticipatory_mask = (mrt_data['excluded_anticipatory_response'] == True) & (~already_excluded)
    anticipatory_count = anticipatory_mask.sum()
    exclusion_data.append({
        'exclusion_criterion': 'anticipatory_response',
        'count_excluded': anticipatory_count,
        'total_trials_assessed': total_trials,
        'exclusion_percentage': (anticipatory_count / total_trials) * 100
    })
    already_excluded = already_excluded | anticipatory_mask

    # c. Extremely slow response
    slow_mask = (mrt_data['excluded_extremely_slow_response'] == True) & (~already_excluded)
    slow_count = slow_mask.sum()
    exclusion_data.append({
        'exclusion_criterion': 'extremely_slow_response',
        'count_excluded': slow_count,
        'total_trials_assessed': total_trials,
        'exclusion_percentage': (slow_count / total_trials) * 100
    })
    already_excluded = already_excluded | slow_mask

    # d. Invalid response
    invalid_mask = (mrt_data['excluded_invalid_response'] == True) & (~already_excluded)
    invalid_count = invalid_mask.sum()
    exclusion_data.append({
        'exclusion_criterion': 'invalid_response',
        'count_excluded': invalid_count,
        'total_trials_assessed': total_trials,
        'exclusion_percentage': (invalid_count / total_trials) * 100
    })
    already_excluded = already_excluded | invalid_mask

    # e. Attention check failure
    attention_mask = (mrt_data['excluded_attention_check_failure'] == True) & (~already_excluded)
    attention_count = attention_mask.sum()
    exclusion_data.append({
        'exclusion_criterion': 'attention_check_failure',
        'count_excluded': attention_count,
        'total_trials_assessed': total_trials,
        'exclusion_percentage': (attention_count / total_trials) * 100
    })
    already_excluded = already_excluded | attention_mask

    # f. RT outlier (applies only to trials valid for RT analysis up to this point)
    # RT outlier is only relevant for correct, valid trials (after all above exclusions)
    rt_outlier_mask = (mrt_data['excluded_rt_outlier'] == True) & (
        mrt_data['trial_valid_accuracy_analysis'] == True
    )
    rt_outlier_count = rt_outlier_mask.sum()
    exclusion_data.append({
        'exclusion_criterion': 'rt_outlier',
        'count_excluded': rt_outlier_count,
        'total_trials_assessed': total_trials,
        'exclusion_percentage': (rt_outlier_count / total_trials) * 100
    })

    exclusion_log = pd.DataFrame(exclusion_data)
    print("Exclusion log:")
    print(exclusion_log)
    return exclusion_log

def main():
    """
    Main function to execute MRT data cleaning pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting MRT data cleaning pipeline...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Load input files
        inclusion_df = load_latest_inclusion_file()
        combined_data = load_task_data_files()
        
        # Filter to MRT task data
        mrt_data = filter_mrt_data(combined_data)
        
        # Filter to included participants only
        mrt_data = filter_to_included_participants(mrt_data, inclusion_df)
        
        # Apply trial-level exclusions
        mrt_data = apply_trial_exclusions(mrt_data)
        
        # Process reaction times and identify outliers
        mrt_data = process_reaction_times(mrt_data)
        
        # Create trial validity flags
        mrt_data = create_validity_flags(mrt_data)
        
        # Separate practice and test trials
        mrt_data = separate_practice_test_trials(mrt_data)
        
        # Create cleaned output data
        cleaned_data = create_cleaned_output(mrt_data)
        
        # Create exclusion log
        exclusion_log = create_exclusion_log(mrt_data)
        
        # Save outputs with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save cleaned trial data
        cleaned_output_file = f"outputs/MRT_cleaned_trial_data_{timestamp}.csv"
        cleaned_data.to_csv(cleaned_output_file, index=False)
        print(f"Cleaned trial data saved to: {cleaned_output_file}")
        
        # Save exclusion log
        exclusion_output_file = f"outputs/MRT_trial_exclusion_log_{timestamp}.csv"
        exclusion_log.to_csv(exclusion_output_file, index=False)
        print(f"Exclusion log saved to: {exclusion_output_file}")
        
        # Final summary
        print("\nFinal summary:")

        # Initial counts
        initial_trials = len(combined_data)
        initial_participants = combined_data['participantId'].nunique()
        print(f"Initial participants loaded: {initial_participants}")
        print(f"Initial trials loaded: {initial_trials}")

        # After filtering to MRT
        mrt_trials = len(mrt_data)
        mrt_participants = mrt_data['participantId'].nunique()
        print(f"Trials after filtering to included participants and MRT task: {mrt_trials}")
        print(f"Participants after filtering: {mrt_participants}")

        # Exclusion breakdown (cascaded)
        # Recompute cascaded counts for reporting
        exclusion_steps = [
            ('excluded_timeout', 'Timeout'),
            ('excluded_anticipatory_response', 'Anticipatory response'),
            ('excluded_extremely_slow_response', 'Extremely slow response'),
            ('excluded_invalid_response', 'Invalid response'),
            ('excluded_attention_check_failure', 'Attention check failure'),
        ]
        already_excluded = pd.Series(False, index=mrt_data.index)
        for col, label in exclusion_steps:
            mask = (mrt_data[col] == True) & (~already_excluded)
            count = mask.sum()
            print(f"Trials removed for {label}: {count} ({count/mrt_trials*100:.2f}%)")
            already_excluded = already_excluded | mask

        print(f"Trials remaining after all exclusions: {(~already_excluded).sum()}")

        # RT outlier
        rt_outlier_mask = (mrt_data['excluded_rt_outlier'] == True) & (mrt_data['trial_valid_accuracy_analysis'] == True)
        rt_outlier_count = rt_outlier_mask.sum()
        print(f"Trials flagged as RT outliers (from valid, correct trials): {rt_outlier_count} ({rt_outlier_count/mrt_trials*100:.2f}%)")

        # Final cleaned data
        print(f"Total participants processed: {cleaned_data['participantId'].nunique()}")
        print(f"Total trials in cleaned dataset: {len(cleaned_data)}")
        print(f"Practice trials: {(cleaned_data['trial_type'] == 'practice').sum()}")
        print(f"Test trials: {(cleaned_data['trial_type'] == 'test').sum()}")
        print(f"Trials valid for accuracy analysis: {cleaned_data['trial_valid_accuracy_analysis'].sum()}")
        print(f"Trials valid for RT analysis: {cleaned_data['trial_valid_rt_analysis'].sum()}")

        # Participant-level summaries
        print(f"Participants with at least one valid accuracy trial: {cleaned_data.loc[cleaned_data['trial_valid_accuracy_analysis'], 'participantId'].nunique()}")
        print(f"Participants with at least one valid RT trial: {cleaned_data.loc[cleaned_data['trial_valid_rt_analysis'], 'participantId'].nunique()}")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in MRT data cleaning pipeline: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
