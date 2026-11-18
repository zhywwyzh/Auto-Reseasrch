import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
from scipy import stats

def read_and_combine_data():
    """
    Read and combine all participant data files matching the pattern.
    
    Returns:
        pd.DataFrame: Combined dataframe with all participant data
    """
    print("Starting data loading process...")
    
    # Find all matching files
    file_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    files = glob.glob(file_pattern)
    
    print(f"Found {len(files)} files matching pattern: {file_pattern}")
    
    if not files:
        print("ERROR: No files found matching the pattern!")
        return None
    
    combined_data = []
    
    for file in files:
        print(f"Reading file: {file}")
        try:
            df = pd.read_csv(file)
            print(f"File shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            print("First 3 rows:")
            print(df.head(3))
            print()
            
            combined_data.append(df)
        except Exception as e:
            print(f"Error reading file {file}: {e}")
            continue
    
    if not combined_data:
        print("ERROR: No valid data files found!")
        return None
    
    # Combine all dataframes
    full_data = pd.concat(combined_data, ignore_index=True)
    print(f"Combined data shape: {full_data.shape}")
    print(f"Combined data columns: {list(full_data.columns)}")
    print("First 2 rows of combined data:")
    print(full_data.head(2))
    print()
    
    return full_data

def validate_columns(df):
    """
    Validate that required columns exist in the dataframe.
    
    Args:
        df (pd.DataFrame): Input dataframe to validate
        
    Returns:
        bool: True if all required columns exist, False otherwise
    """
    required_columns = [
        'participantId', 'frameRate', 'windowWidthPixels', 'windowHeightPixels',
        'windowFocusLostDuringTasksNum', 'windowFocusLostDuringTasksDuration',
        'VWM_timeout', 'MRT_timeout', 'isPractice',
        'VWM_error_absolute_degrees', 'VWM_rt_ms', 'VWM_trial', 
        'MRT_trial', 'MRT_rt_ms'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"ERROR: Missing required columns: {missing_columns}")
        return False
    
    print("All required columns found!")
    return True

def print_unique_values(df):
    """
    Print unique values for key experimental design parameter columns.
    
    Args:
        df (pd.DataFrame): Input dataframe
    """
    print("\n=== UNIQUE VALUES FOR KEY COLUMNS ===")
    
    # Key experimental design parameters
    design_columns = ['isPractice', 'VWM_timeout', 'MRT_timeout']
    
    for col in design_columns:
        if col in df.columns:
            unique_vals = df[col].unique()
            print(f"{col}: {unique_vals}")
    
    # For measured variables, just print data types
    measured_columns = ['VWM_error_absolute_degrees', 'VWM_rt_ms', 'MRT_rt_ms', 
                       'frameRate']
    
    print("\n=== DATA TYPES FOR MEASURED VARIABLES ===")
    for col in measured_columns:
        if col in df.columns:
            print(f"{col}: {df[col].dtype}")
    
    print()

def read_prolific_data():
    """
    Read Prolific data to get session durations.
    """
    print("Reading Prolific data...")
    prolific_pattern = "../C_results/data/prolific_export_*.csv"
    prolific_files = glob.glob(prolific_pattern)
    
    if not prolific_files:
        print("ERROR: No Prolific export file found!")
        return None
    
    latest_file = max(prolific_files, key=os.path.getctime)
    print(f"Loading Prolific data from: {latest_file}")
    
    try:
        prolific_df = pd.read_csv(latest_file)
        print(f"Prolific file shape: {prolific_df.shape}")
        print(f"Prolific file columns: {list(prolific_df.columns)}")
    except Exception as e:
        print(f"ERROR reading Prolific file: {e}")
        return None
    
    required_cols = ['Participant id', 'Time taken']
    missing_cols = [col for col in required_cols if col not in prolific_df.columns]
    
    if missing_cols:
        print(f"ERROR: Prolific file missing required columns: {missing_cols}")
        return None
    
    print(f"Successfully loaded Prolific data for {len(prolific_df)} participants")
    print("First 5 rows of Prolific data:")
    print(prolific_df[required_cols].head())
    return prolific_df[required_cols]

def apply_exclusions(df, prolific_data):
    """
    Apply all exclusion criteria and track exclusions.
    
    Args:
        df (pd.DataFrame): Input dataframe
        prolific_data (pd.DataFrame): Prolific export dataframe
        
    Returns:
        tuple: (all_participants_summary, exclusion_log)
    """
    print("\n=== APPLYING EXCLUSIONS ===")
    
    exclusion_log = []
    
    # Get participant-level summary first
    participant_summary = get_participant_summary(df)
    print(f"Starting with {len(participant_summary)} participants")
    
    # Initialize exclusion tracking columns
    participant_summary['excluded'] = False
    participant_summary['exclusion_reason'] = ''
    
    # Calculate 95th percentile on the full sample BEFORE any exclusions
    focus_loss_95th = np.nanpercentile(participant_summary['windowFocusLostDuringTasksNum'], 95)
    
    initial_count = len(participant_summary)
    
    # 1. Session duration exclusions using Prolific data
    if prolific_data is None or prolific_data.empty:
        print("Skipping session duration exclusions due to missing Prolific data")
        exclusion_log.append({
            'exclusion_criteria': 'session_duration_over_3sd',
            'total_excluded': 0
        })
        participant_summary['session_duration_minutes'] = np.nan
    else:
        # Prepare Prolific data for merging
        prolific_data = prolific_data.copy()
        prolific_data = prolific_data.rename(columns={'Participant id': 'participantId'})
        prolific_data['session_duration_minutes'] = prolific_data['Time taken'] / 60.0
        session_durations = prolific_data[['participantId', 'session_duration_minutes']]
        participant_summary = participant_summary.merge(session_durations, on='participantId', how='left')
        print(f"Successfully merged session duration data. Number of participants with session duration: {participant_summary['session_duration_minutes'].notna().sum()}")
        all_durations = participant_summary['session_duration_minutes'].dropna()
        if len(all_durations) > 0:
            mean_duration = all_durations.mean()
            std_duration = all_durations.std()
            duration_threshold = mean_duration + 3 * std_duration
        else:
            duration_threshold = float('inf')

        print(f"Session duration statistics (all available durations):")
        if len(all_durations) > 0:
            print(f"Mean: {mean_duration:.2f} minutes")
            print(f"Std: {std_duration:.2f} minutes")
            print(f"Threshold (mean + 3*std): {duration_threshold:.2f} minutes")
            print(f"Min: {all_durations.min():.2f} minutes")
            print(f"Max: {all_durations.max():.2f} minutes")
        else:
            print("No session durations found.")

        duration_excluded = participant_summary['session_duration_minutes'] > duration_threshold
        newly_excluded_duration = (duration_excluded & ~participant_summary['excluded']).sum()

        print(f"Participants newly excluded for session duration > 3 SD: {newly_excluded_duration}")

        # Mark excluded participants
        participant_summary.loc[duration_excluded, 'excluded'] = True
        participant_summary.loc[duration_excluded, 'exclusion_reason'] += 'session_duration_over_3sd;'

        exclusion_log.append({
            'exclusion_criteria': 'session_duration_over_3sd',
            'total_excluded': int(newly_excluded_duration)
        })
    
    # 2. Technical quality exclusions - frameRate
    # Identify all who meet the criterion
    framerate_condition = participant_summary['frameRate'] < 15
    # Count how many are newly excluded by this criterion
    newly_excluded_framerate = (framerate_condition & ~participant_summary['excluded']).sum()

    print(f"Participants newly excluded for frameRate < 15: {newly_excluded_framerate}")

    # Mark ALL who meet the criterion, and add the reason
    participant_summary.loc[framerate_condition, 'excluded'] = True
    participant_summary.loc[framerate_condition, 'exclusion_reason'] += 'framerate_below_15;'

    exclusion_log.append({
        'exclusion_criteria': 'framerate_below_15',
        'total_excluded': int(newly_excluded_framerate)
    })

    # 3. Technical quality exclusions - window size
    window_condition = ((participant_summary['windowWidthPixels'] < 768) | 
                      (participant_summary['windowHeightPixels'] < 768))
    newly_excluded_window = (window_condition & ~participant_summary['excluded']).sum()

    print(f"Participants newly excluded for window size < 768x768: {newly_excluded_window}")

    # Mark ALL who meet the criterion, and add the reason
    participant_summary.loc[window_condition, 'excluded'] = True
    participant_summary.loc[window_condition, 'exclusion_reason'] += 'window_size_below_768;'

    exclusion_log.append({
        'exclusion_criteria': 'window_size_below_768',
        'total_excluded': int(newly_excluded_window)
    })

    # 4. Focus loss exclusions
    focus_condition = participant_summary['windowFocusLostDuringTasksNum'] > focus_loss_95th
    newly_excluded_focus = (focus_condition & ~participant_summary['excluded']).sum()

    print(f"95th percentile of focus loss events: {focus_loss_95th}")
    print(f"Participants newly excluded for focus loss > 95th percentile: {newly_excluded_focus}")

    # Mark ALL who meet the criterion, and add the reason
    participant_summary.loc[focus_condition, 'excluded'] = True
    participant_summary.loc[focus_condition, 'exclusion_reason'] += 'focus_loss_over_95th_percentile;'

    exclusion_log.append({
        'exclusion_criteria': 'focus_loss_over_95th_percentile',
        'total_excluded': int(newly_excluded_focus)
    })
    
    final_count = (~participant_summary['excluded']).sum()
    total_excluded = initial_count - final_count
    
    print(f"Final participant count after exclusions: {final_count}")
    print(f"Total participants excluded: {total_excluded}")
    
    return participant_summary, exclusion_log

def get_participant_summary(df):
    """
    Get participant-level summary with technical metrics.
    
    Args:
        df (pd.DataFrame): Input dataframe
        
    Returns:
        pd.DataFrame: Participant summary dataframe
    """
    print("Creating participant summary...")
    
    # Convert windowFocusLostDuringTasksDuration to minutes
    df['windowFocusLostDuringTasksDuration_minutes'] = pd.to_timedelta(
        df['windowFocusLostDuringTasksDuration']
    ).dt.total_seconds() / 60
    
    # Get first non-null value for each participant for technical metrics
    participant_summary = df.groupby('participantId').agg({
        'frameRate': 'first',
        'windowWidthPixels': 'first',
        'windowHeightPixels': 'first',
        'windowFocusLostDuringTasksNum': 'first',
        'windowFocusLostDuringTasksDuration_minutes': 'first'
    }).reset_index()
    
    print(f"Participant summary shape: {participant_summary.shape}")
    print("First 2 rows of participant summary:")
    print(participant_summary.head(2))
    
    return participant_summary

def calculate_control_variables(df, valid_participants):
    """
    Calculate control variables for remaining participants.
    
    Args:
        df (pd.DataFrame): Full dataframe
        valid_participants (pd.DataFrame): Valid participants after exclusions
        
    Returns:
        pd.DataFrame: Participants with control variables
    """
    print("\n=== CALCULATING CONTROL VARIABLES ===")
    
    # Filter to valid participants and test trials only
    valid_participant_ids = valid_participants['participantId'].tolist()
    test_data = df[(df['participantId'].isin(valid_participant_ids)) & 
                   (df['isPractice'] == False)].copy()
    
    print(f"Test data shape: {test_data.shape}")
    
    control_vars = []
    
    for participant_id in valid_participant_ids:
        participant_data = test_data[test_data['participantId'] == participant_id].copy()
        
        # Initialize control variables
        participant_controls = {'participantId': participant_id}
        
        # 1. Mean VWM accuracy
        vwm_data = participant_data[participant_data['VWM_trial'].notna()].copy()
        if len(vwm_data) > 0:
            vwm_accurate = (vwm_data['VWM_error_absolute_degrees'] <= 15).sum()
            vwm_total = len(vwm_data)
            participant_controls['mean_vwm_accuracy'] = vwm_accurate / vwm_total
        else:
            participant_controls['mean_vwm_accuracy'] = np.nan
        
        # 2. Response time coefficient of variation
        # VWM CV
        vwm_rt_data = vwm_data['VWM_rt_ms'].dropna()
        if len(vwm_rt_data) > 1:
            vwm_cv = vwm_rt_data.std() / vwm_rt_data.mean()
        else:
            vwm_cv = np.nan
        
        # MRT CV
        mrt_data = participant_data[participant_data['MRT_trial'].notna()].copy()
        mrt_rt_data = mrt_data['MRT_rt_ms'].dropna()
        if len(mrt_rt_data) > 1:
            mrt_cv = mrt_rt_data.std() / mrt_rt_data.mean()
        else:
            mrt_cv = np.nan
        
        # Average CV
        if not np.isnan(vwm_cv) and not np.isnan(mrt_cv):
            participant_controls['response_time_cv'] = (vwm_cv + mrt_cv) / 2
        elif not np.isnan(vwm_cv):
            participant_controls['response_time_cv'] = vwm_cv
        elif not np.isnan(mrt_cv):
            participant_controls['response_time_cv'] = mrt_cv
        else:
            participant_controls['response_time_cv'] = np.nan
        
        # 3. Composite engagement score
        # Timeout rate
        timeout_trials = ((participant_data['VWM_timeout'] == True) | 
                         (participant_data['MRT_timeout'] == True)).sum()
        total_trials = participant_data['VWM_trial'].notna().sum() + participant_data['MRT_trial'].notna().sum()
        timeout_rate = timeout_trials / total_trials if total_trials > 0 else 0
        
        # Focus loss duration (already in minutes)
        focus_duration = valid_participants[valid_participants['participantId'] == participant_id]['windowFocusLostDuringTasksDuration_minutes'].iloc[0]
        
        participant_controls['timeout_rate'] = timeout_rate
        participant_controls['focus_loss_duration'] = focus_duration
        
        control_vars.append(participant_controls)
    
    control_df = pd.DataFrame(control_vars)
    
    # Calculate composite engagement score with z-standardization
    control_df['timeout_rate_z'] = stats.zscore(control_df['timeout_rate'], nan_policy='omit')
    control_df['focus_loss_duration_z'] = stats.zscore(control_df['focus_loss_duration'], nan_policy='omit')
    
    # Average the two standardized components
    control_df['composite_engagement_score'] = (control_df['timeout_rate_z'] + control_df['focus_loss_duration_z']) / 2
    
    # Z-score standardize all control variables
    control_df['mean_vwm_accuracy_z'] = stats.zscore(control_df['mean_vwm_accuracy'], nan_policy='omit')
    control_df['response_time_cv_z'] = stats.zscore(control_df['response_time_cv'], nan_policy='omit')
    control_df['composite_engagement_score_z'] = stats.zscore(control_df['composite_engagement_score'], nan_policy='omit')
    
    print(f"Control variables calculated for {len(control_df)} participants")
    print("Control variables summary:")
    print(control_df[['mean_vwm_accuracy', 'response_time_cv', 'composite_engagement_score']].describe())
    
    return control_df

def create_final_output(all_participants_summary, control_vars):
    """
    Create the final output dataframe with all required columns.
    
    Args:
        all_participants_summary (pd.DataFrame): All participants with exclusion flags
        control_vars (pd.DataFrame): Control variables dataframe
        
    Returns:
        pd.DataFrame: Final output dataframe
    """
    print("\n=== CREATING FINAL OUTPUT ===")
    
    # Merge all participants with control variables (left join to keep all participants)
    final_df = all_participants_summary.merge(control_vars, on='participantId', how='left')
    
    # Clean up exclusion_reason column - remove trailing semicolons and ensure string type
    final_df['exclusion_reason'] = final_df['exclusion_reason'].astype(str).str.rstrip(';')
    
    # Select and order required columns
    required_columns = [
        'participantId', 'session_duration_minutes', 'frameRate',
        'windowWidthPixels', 'windowHeightPixels', 'windowFocusLostDuringTasksNum',
        'windowFocusLostDuringTasksDuration_minutes', 'mean_vwm_accuracy',
        'response_time_cv', 'composite_engagement_score', 'mean_vwm_accuracy_z',
        'response_time_cv_z', 'composite_engagement_score_z', 'excluded', 'exclusion_reason'
    ]
    
    final_df = final_df[required_columns]
    
    print(f"Final output shape: {final_df.shape}")
    print("Final output columns:")
    print(list(final_df.columns))
    print("First 2 rows of final output:")
    print(final_df.head(2))
    
    return final_df

def save_outputs(final_df, exclusion_log):
    """
    Save output files to the outputs directory.
    
    Args:
        final_df (pd.DataFrame): Final participant dataframe
        exclusion_log (list): List of exclusion criteria and counts
    """
    print("\n=== SAVING OUTPUTS ===")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusion_log)
    exclusion_filename = f'outputs/initial_exclusion_log_{timestamp}.csv'
    exclusion_df.to_csv(exclusion_filename, index=False)
    print(f"Saved exclusion log to: {exclusion_filename}")
    print("Exclusion log contents:")
    print(exclusion_df)
    
    # Save final participant data
    participant_filename = f'outputs/participants_post_initial_exclusions_{timestamp}.csv'
    final_df.to_csv(participant_filename, index=False)
    print(f"Saved participant data to: {participant_filename}")
    print(f"Saved {len(final_df)} participants to final output")

def main():
    """
    Main function to execute the data processing pipeline.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("=== STARTING DATA PROCESSING PIPELINE ===")
        
        # 1. Read and combine data
        df = read_and_combine_data()
        if df is None:
            return 1
        
        # 2. Validate columns
        if not validate_columns(df):
            return 1
        
        # 3. Print unique values
        print_unique_values(df)
        
        # 4. Read Prolific data for session durations
        prolific_df = read_prolific_data()
        if prolific_df is None:
            print("WARNING: Proceeding without Prolific session duration data.")
        
        # 5. Apply exclusions and get the full summary with flags
        all_participants_summary, exclusion_log = apply_exclusions(df, prolific_df)
        valid_participants = all_participants_summary[all_participants_summary['excluded'] == False]
        
        # 6. Calculate control variables for valid participants only
        control_vars = calculate_control_variables(df, valid_participants)
        
        # 7. Create final output with ALL participants
        final_df = create_final_output(all_participants_summary, control_vars)
        
        # 8. Save outputs
        save_outputs(final_df, exclusion_log)
        
        print("\n=== FINAL SUMMARY ===")
        initial_n = len(df['participantId'].unique())
        final_n = (~final_df['excluded']).sum()
        print(f"Initial participants: {initial_n}")
        print(f"Final participants after exclusions: {final_n}")
        print(f"Total excluded: {initial_n - final_n}")
        print("Exclusion breakdown (participants may be excluded for multiple reasons):")
        for item in exclusion_log:
            print(f"  - {item['exclusion_criteria']}: {item['total_excluded']}")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
