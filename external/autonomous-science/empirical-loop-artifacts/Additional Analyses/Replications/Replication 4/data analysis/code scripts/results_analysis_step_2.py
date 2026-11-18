#!/usr/bin/env python3
"""
Participant Exclusion Script for VWM and Rotation Task Data

This script processes participant data from multiple sources to apply exclusion criteria
and generate cleaned datasets for analysis.
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime

def get_most_recent_file(pattern):
    """
    Get the most recent file matching a pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_participant_data():
    """
    Load and consolidate participant data from all input sources.
    
    Returns:
    tuple: (main_data_df, vviq_df, prolific_df) containing the loaded dataframes
    """
    print("Loading participant data files...")
    
    # Load main task data files
    main_pattern = "../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv"
    main_files = glob.glob(main_pattern)
    print(f"Found {len(main_files)} main task data files")
    
    if not main_files:
        print("ERROR: No main task data files found!")
        return None, None, None
    
    # Load all main task files
    main_dfs = []
    for file in main_files:
        print(f"Loading: {file}")
        try:
            df = pd.read_csv(file)
            df.columns = df.columns.str.strip()
            print(f"Columns in {file}:")
            print(df.columns.tolist())
            print("First 3 rows:")
            print(df.head(3))
            main_dfs.append(df)
        except Exception as e:
            print(f"Error loading {file}: {e}")
            continue
    
    if not main_dfs:
        print("ERROR: Could not load any main task data files!")
        return None, None, None
    
    # Combine all main task data
    main_data = pd.concat(main_dfs, ignore_index=True)
    print(f"Combined main data shape: {main_data.shape}")

    # Fill NaN values in attention check columns with False (non-attention-check trials)
    main_data['VWM_isAttentionCheck'] = main_data['VWM_isAttentionCheck'].fillna(False)
    main_data['MRT_isAttentionCheck'] = main_data['MRT_isAttentionCheck'].fillna(False)
    
    # Load VVIQ data
    vviq_file = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
    vviq_df = None
    try:
        vviq_df = pd.read_csv(vviq_file)
        vviq_df.columns = vviq_df.columns.str.strip()
        print(f"VVIQ data loaded. Shape: {vviq_df.shape}")
        print("VVIQ columns:")
        print(vviq_df.columns.tolist())
        print("First 3 rows:")
        print(vviq_df.head(3))
    except Exception as e:
        print(f"Error loading VVIQ data: {e}")
    
    # Load Prolific export data
    prolific_pattern = "../C_results/data/prolific_export_*.csv"
    prolific_file = get_most_recent_file(prolific_pattern)
    prolific_df = None
    if prolific_file:
        try:
            prolific_df = pd.read_csv(prolific_file)
            prolific_df.columns = prolific_df.columns.str.strip()
            # Check if columns need renaming before attempting to rename
            rename_map = {}
            if 'Participant id' in prolific_df.columns:
                rename_map['Participant id'] = 'participant_id'
            if 'Time taken' in prolific_df.columns:
                rename_map['Time taken'] = 'time_taken'
            if rename_map:
                prolific_df.rename(columns=rename_map, inplace=True)
            print(f"Prolific data loaded from: {prolific_file}")
            print(f"Prolific data shape: {prolific_df.shape}")
            print("Prolific columns:")
            print(prolific_df.columns.tolist())
            print("First 3 rows:")
            print(prolific_df.head(3))
        except Exception as e:
            print(f"Error loading Prolific data: {e}")
    else:
        print("No Prolific export files found")
    
    return main_data, vviq_df, prolific_df

def identify_task_rows(df):
    """
    Identify which task each row belongs to based on non-null values.
    
    Parameters:
    df (DataFrame): Main task dataframe
    
    Returns:
    DataFrame: Dataframe with task indicator columns added
    """
    print("Identifying task rows...")
    
    # Check for VWM task indicators
    vwm_indicators = ['VWM_trial', 'VWM_setSize', 'VWM_responseAngle_degrees']
    mrt_indicators = ['MRT_trial', 'MRT_isCorrect']
    
    # Create task indicator columns
    df['is_vwm_row'] = False
    df['is_mrt_row'] = False
    
    # VWM rows: have non-null VWM data
    for col in vwm_indicators:
        if col in df.columns:
            df['is_vwm_row'] = df['is_vwm_row'] | df[col].notna()
    
    # MRT rows: have non-null MRT data
    for col in mrt_indicators:
        if col in df.columns:
            df['is_mrt_row'] = df['is_mrt_row'] | df[col].notna()
    
    print(f"VWM rows identified: {df['is_vwm_row'].sum()}")
    print(f"MRT rows identified: {df['is_mrt_row'].sum()}")
    
    # Print unique values for key experimental parameters
    print("\nUnique values for key experimental parameters:")
    if 'VWM_setSize' in df.columns:
        print(f"VWM_setSize unique values: {sorted(df['VWM_setSize'].dropna().unique())}")
    if 'VWM_delay_s' in df.columns:
        print(f"VWM_delay_s unique values: {sorted(df['VWM_delay_s'].dropna().unique())}")
    if 'isPractice' in df.columns:
        print(f"isPractice unique values: {sorted(df['isPractice'].dropna().unique())}")
    if 'VWM_isAttentionCheck' in df.columns:
        print(f"VWM_isAttentionCheck unique values: {sorted(df['VWM_isAttentionCheck'].dropna().unique())}")
    if 'MRT_isAttentionCheck' in df.columns:
        print(f"MRT_isAttentionCheck unique values: {sorted(df['MRT_isAttentionCheck'].dropna().unique())}")
    
    return df

def parse_duration_value(val):
    """Parse duration value from string or numeric format to seconds."""
    if pd.isna(val):
        return 0
    if isinstance(val, str) and ':' in val:
        # Parse HH:MM:SS format to seconds
        parts = val.split(':')
        hours, minutes, seconds = int(parts[0]), int(parts[1]), int(parts[2])
        return float(hours * 3600 + minutes * 60 + seconds)
    else:
        # Assume numeric value is in MILLISECONDS, convert to seconds
        numeric_val = pd.to_numeric(val, errors='coerce')
        return (numeric_val / 1000.0) if pd.notna(numeric_val) else 0

def calculate_exclusion_metrics(df, vviq_df, prolific_df):
    """
    Calculate exclusion metrics for each participant.
    
    Parameters:
    df (DataFrame): Main task data with task indicators
    vviq_df (DataFrame): VVIQ questionnaire data
    prolific_df (DataFrame): Prolific export data
    
    Returns:
    DataFrame: Participant-level metrics for exclusion decisions
    """
    print("Calculating exclusion metrics...")
    
    participants = df['participantId'].unique()
    
    results = []
    
    for participant in participants:
        # Get participant data
        p_data = df[df['participantId'] == participant].copy()
        
        # Initialize metrics
        metrics = {
            'participantId': participant,
            'vwm_practice_attempts': 0,
            'mrt_practice_attempts': 0,
            'vwm_timeout_rate': 0.0,
            'mrt_timeout_rate': 0.0,
            'focus_loss_instances': 0,
            'focus_loss_duration_pct': 0.0,
            'vwm_setsize2_error': np.nan,
            'mrt_overall_accuracy': 0.0,
            'vviq2_missing_pct': 0.0,
            'session_duration_minutes': np.nan,
            'vwm_practice_error': np.nan,
            'mrt_practice_accuracy': 0.0,
            'mrt_attention_accuracy': 0.0,
            'vviq2_identical_pct': np.nan
        }
        
        # Get VWM and MRT specific data
        vwm_data = p_data[p_data['is_vwm_row']].copy()
        mrt_data = p_data[p_data['is_mrt_row']].copy()
        
        # 1. Practice attempts
        if 'VWM_pracAttempt' in vwm_data.columns:
            metrics['vwm_practice_attempts'] = vwm_data['VWM_pracAttempt'].max() if not vwm_data['VWM_pracAttempt'].isna().all() else 0

        if 'MRT_pracAttempt' in mrt_data.columns:
            metrics['mrt_practice_attempts'] = mrt_data['MRT_pracAttempt'].max() if not mrt_data['MRT_pracAttempt'].isna().all() else 0
        
        # 2. VWM practice performance
        if 'VWM_pracAttempt' in vwm_data.columns and vwm_data['VWM_pracAttempt'].notna().any():
            max_attempt = vwm_data['VWM_pracAttempt'].max()
            vwm_practice = vwm_data[
                (vwm_data['isPractice'] == True) & 
                (vwm_data['VWM_isAttentionCheck'] == False) &
                (vwm_data['VWM_pracAttempt'] == max_attempt)
            ]
        else:
            vwm_practice = vwm_data[
                (vwm_data['isPractice'] == True) & 
                (vwm_data['VWM_isAttentionCheck'] == False)
            ]
        if len(vwm_practice) > 0 and 'VWM_error_absolute_degrees' in vwm_practice.columns:
            valid_errors = vwm_practice['VWM_error_absolute_degrees'].dropna()
            if len(valid_errors) > 0:
                metrics['vwm_practice_error'] = valid_errors.mean()
        
        # 3. MRT practice performance  
        if 'MRT_pracAttempt' in mrt_data.columns and mrt_data['MRT_pracAttempt'].notna().any():
            max_attempt = mrt_data['MRT_pracAttempt'].max()
            mrt_practice = mrt_data[
                (mrt_data['isPractice'] == True) & 
                (mrt_data['MRT_isAttentionCheck'] == False) &
                (mrt_data['MRT_pracAttempt'] == max_attempt)
            ]
        else:
            max_attempt = None
            mrt_practice = mrt_data[
                (mrt_data['isPractice'] == True) & 
                (mrt_data['MRT_isAttentionCheck'] == False)
            ]

        # Calculate accuracy for all participants
        if len(mrt_practice) > 0 and 'MRT_isCorrect' in mrt_practice.columns:
            valid_responses = mrt_practice['MRT_isCorrect'].dropna()
            if len(valid_responses) > 0:
                metrics['mrt_practice_accuracy'] = (valid_responses.sum() / len(valid_responses)) * 100

        # 4. Timeout rates
        vwm_test = vwm_data[
            (vwm_data['isPractice'] == False) & 
            (vwm_data['VWM_isAttentionCheck'] == False)
        ]
        if len(vwm_test) > 0 and 'VWM_timeout' in vwm_test.columns:
            valid_timeouts = vwm_test['VWM_timeout'].dropna()
            if len(valid_timeouts) > 0:
                metrics['vwm_timeout_rate'] = (valid_timeouts.sum() / len(valid_timeouts)) * 100
        
        mrt_test = mrt_data[
            (mrt_data['isPractice'] == False) & 
            (mrt_data['MRT_isAttentionCheck'] == False)
        ]
        if len(mrt_test) > 0 and 'MRT_timeout' in mrt_test.columns:
            valid_timeouts = mrt_test['MRT_timeout'].dropna()
            if len(valid_timeouts) > 0:
                metrics['mrt_timeout_rate'] = (valid_timeouts.sum() / len(valid_timeouts)) * 100
        
        # 5. MRT attention check accuracy
        mrt_attention = mrt_data[mrt_data['MRT_isAttentionCheck'] == True]
        if len(mrt_attention) > 0 and 'MRT_isCorrect' in mrt_attention.columns:
            valid_responses = mrt_attention['MRT_isCorrect'].dropna()
            if len(valid_responses) > 0:
                metrics['mrt_attention_accuracy'] = (valid_responses.sum() / len(valid_responses)) * 100
        
        # 6. Focus loss metrics
        focus_cols = ['windowFocusLostDuringTasksNum', 'windowFocusLostDuringInfoNum']
        duration_cols = ['windowFocusLostDuringTasksDuration', 'windowFocusLostDuringInfoDuration']
        
        total_instances = 0
        total_duration = 0
        
        for col in focus_cols:
            if col in p_data.columns:
                val = p_data[col].iloc[0] if len(p_data) > 0 and not p_data[col].isna().all() else 0
                total_instances += val if not pd.isna(val) else 0
        
        for col in duration_cols:
            if col in p_data.columns:
                val = p_data[col].iloc[0] if len(p_data) > 0 and not p_data[col].isna().all() else 0
                # Use helper to parse duration value
                numeric_val = parse_duration_value(val)
                total_duration += numeric_val if not pd.isna(numeric_val) else 0

        metrics['focus_loss_instances'] = total_instances

        
        # 7. VWM Set Size 2 performance
        vwm_setsize2 = vwm_data[
            (vwm_data['VWM_setSize'] == 2) & 
            (vwm_data['isPractice'] == False) & 
            (vwm_data['VWM_isAttentionCheck'] == False)
        ]
        if len(vwm_setsize2) > 0 and 'VWM_error_absolute_degrees' in vwm_setsize2.columns:
            valid_errors = vwm_setsize2['VWM_error_absolute_degrees'].dropna()
            if len(valid_errors) > 0:
                metrics['vwm_setsize2_error'] = valid_errors.mean()
        
        # 8. Overall MRT accuracy
        if len(mrt_test) > 0 and 'MRT_isCorrect' in mrt_test.columns:
            valid_responses = mrt_test['MRT_isCorrect'].dropna()
            if len(valid_responses) > 0:
                metrics['mrt_overall_accuracy'] = (valid_responses.sum() / len(valid_responses)) * 100
        
        # 9. Session duration and Focus Loss from Prolific data
        if prolific_df is not None:
            prolific_match = prolific_df[prolific_df['participant_id'] == participant]
            if len(prolific_match) > 0 and 'time_taken' in prolific_match.columns:
                time_taken = prolific_match['time_taken'].iloc[0]
                if not pd.isna(time_taken):
                    metrics['session_duration_minutes'] = time_taken / 60.0  # Convert seconds to minutes
                    # Calculate focus loss percentage
                    if total_duration > 0 and time_taken > 0:
                        session_duration_seconds = time_taken  # time_taken is already in seconds
                        focus_pct = (total_duration / session_duration_seconds) * 100
                        metrics['focus_loss_duration_pct'] = min(focus_pct, 100.0)  # Cap at 100%

        # 10. VVIQ metrics
        if vviq_df is not None:
            vviq_match = vviq_df[vviq_df['PROLIFIC_PID'] == participant]
            if len(vviq_match) > 0:
                # Find question columns (between 'Custom Data 1' and 'PROLIFIC_PID')
                all_cols = vviq_df.columns.tolist()
                try:
                    start_index = all_cols.index('Custom Data 1') + 1
                    end_index = all_cols.index('PROLIFIC_PID')
                    question_cols = all_cols[start_index:end_index]
                except ValueError:
                    question_cols = []
                
                if len(question_cols) == 32:
                    responses = []
                    for idx, col in enumerate(question_cols):
                        response = vviq_match[col].iloc[0]
                        try:
                            # Response is already numeric, use directly
                            if pd.notna(response):
                                numeric_val = int(response)
                                if 1 <= numeric_val <= 5:
                                    responses.append(numeric_val)
                                else:
                                    responses.append(np.nan)
                            else:
                                responses.append(np.nan)
                        except (ValueError, TypeError):
                            responses.append(np.nan)

                    # Calculate missing percentage
                    missing_count = sum(1 for r in responses if pd.isna(r))
                    metrics['vviq2_missing_pct'] = (missing_count / 32) * 100

                    # Calculate identical response percentage
                    valid_responses = [r for r in responses if not pd.isna(r)]
                    if len(valid_responses) > 0:
                        from collections import Counter
                        response_counts = Counter(valid_responses)
                        most_common_count = max(response_counts.values())
                        metrics['vviq2_identical_pct'] = (most_common_count / 32) * 100
                    else:
                        metrics['vviq2_identical_pct'] = np.nan  # No valid responses to check
        
        results.append(metrics)
    
    return pd.DataFrame(results)

def print_exclusion_summary(metrics_df, exclusion_log):
    """Print comprehensive exclusion summary."""
    print("\n" + "="*60)
    print("FINAL EXCLUSION SUMMARY")
    print("="*60)
    
    total_participants = len(metrics_df)
    included_count = metrics_df['included'].sum()
    excluded_count = total_participants - included_count
    
    print(f"Initial participant count: {total_participants}")
    print(f"Final included participants: {included_count}")
    print(f"Total excluded participants: {excluded_count}")
    if total_participants > 0:
        print(f"Inclusion rate: {(included_count/total_participants)*100:.1f}%")
    else:
        print("Inclusion rate: N/A (no participants found)")
    
    print("\nExclusion breakdown by criterion:")
    for log_entry in exclusion_log:
        print(f"  {log_entry['exclusion_criterion']}: {log_entry['total_excluded']} participants")
    
    print("\nKey metrics for included participants:")
    if included_count > 0:
        included_data = metrics_df[metrics_df['included'] == True]
        print(f"  Mean session duration: {included_data['session_duration_minutes'].mean():.1f} minutes")
        print(f"  Mean VWM Set Size 2 error: {included_data['vwm_setsize2_error'].mean():.1f}°")
        print(f"  Mean MRT accuracy: {included_data['mrt_overall_accuracy'].mean():.1f}%")
    else:
        print("  No participants included - check exclusion criteria!")

def apply_exclusion_criteria(metrics_df):
    """
    Apply exclusion criteria in a cascaded (sequential) manner and generate exclusion log.

    Parameters:
    metrics_df (DataFrame): Participant metrics

    Returns:
    tuple: (metrics_df_with_flags, exclusion_log)
    """
    print("\nApplying exclusion criteria (cascaded, vectorized)...")

    metrics_df['included'] = True
    metrics_df['exclusion_reason'] = ''

    # Define exclusion criteria as a list of dicts for clarity and log
    criteria = [
        {
            'name': 'VWM Practice Failure',
            'condition': (metrics_df['vwm_practice_error'] > 30) & (metrics_df['vwm_practice_attempts'] >= 3),
            'reason': 'VWM practice failure',
            'details': 'Mean absolute error >30° after >=3 attempts'
        },
        {
            'name': 'MRT Practice Failure',
            'condition': (metrics_df['mrt_practice_accuracy'] < 50) & (metrics_df['mrt_practice_attempts'] >= 3),
            'reason': 'MRT practice failure',
            'details': 'Accuracy <50% after >=3 attempts'
        },
        {
            'name': 'Poor Engagement',
            'condition': (metrics_df['vwm_timeout_rate'] > 20) | (metrics_df['mrt_timeout_rate'] > 20),
            'reason': 'Poor engagement',
            'details': 'Timeout rate >20% in either task'
        },
        {
            'name': 'Low Attention',
            'condition': (metrics_df['mrt_attention_accuracy'] < 40),
            'reason': 'Low attention',
            'details': 'MRT attention check accuracy <40%'
        },
        {
            'name': 'Excessive Distraction',
            'condition': (metrics_df['focus_loss_instances'] > 30) | (metrics_df['focus_loss_duration_pct'] > 10),
            'reason': 'Excessive distraction',
            'details': '>30 focus loss instances OR >10% session unfocused'
        },
        {
            'name': 'VWM Chance Performance',
            'condition': (metrics_df['vwm_setsize2_error'] > 45),
            'reason': 'VWM chance performance',
            'details': 'Set size 2 mean error >45°'
        },
        {
            'name': 'MRT Chance Performance',
            'condition': (metrics_df['mrt_overall_accuracy'] < 50),
            'reason': 'MRT chance performance',
            'details': 'Overall accuracy <50%'
        },
        {
            'name': 'Questionnaire Issues',
            'condition': (metrics_df['vviq2_missing_pct'] > 10) | (metrics_df['vviq2_identical_pct'] > 90),
            'reason': 'Questionnaire issues',
            'details': '>10% missing responses OR >90% identical responses'
        },
        {
            'name': 'Extreme Duration',
            'condition': (metrics_df['session_duration_minutes'] < 15) | (metrics_df['session_duration_minutes'] > 120),
            'reason': 'Extreme duration',
            'details': '<15 minutes OR >120 minutes'
        },
    ]

    exclusion_log = []

    # Apply cascaded exclusion vectorized
    for crit in criteria:
        # Apply cascaded exclusion only to still-included participants
        mask = metrics_df['included'] & crit['condition'].fillna(False)
        metrics_df.loc[mask, 'included'] = False
        metrics_df.loc[mask, 'exclusion_reason'] = crit['reason']
        
        # Log newly excluded participants at this step
        exclusion_log.append({
            'exclusion_criterion': crit['name'],
            'total_excluded': mask.sum(),
            'exclusion_details': crit['details']
        })

    print(f"\nTotal participants: {len(metrics_df)}")
    print(f"Included participants: {metrics_df['included'].sum()}")
    print(f"Excluded participants: {(~metrics_df['included']).sum()}")

    print_exclusion_summary(metrics_df, exclusion_log)
    return metrics_df, exclusion_log

def save_outputs(metrics_df, exclusion_log):
    """
    Save output files with timestamp.
    
    Parameters:
    metrics_df (DataFrame): Final participant data with inclusion flags
    exclusion_log (list): List of exclusion criteria details
    """
    print("\nSaving output files...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusion_log)
    exclusion_file = f"outputs/participant_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(exclusion_file, index=False)
    print(f"Exclusion log saved to: {exclusion_file}")
    
    # Prepare final participant data
    output_cols = [
        'participantId', 'included', 'exclusion_reason', 'vwm_practice_attempts',
        'mrt_practice_attempts', 'vwm_timeout_rate', 'mrt_timeout_rate',
        'focus_loss_instances', 'focus_loss_duration_pct', 'vwm_setsize2_error',
        'mrt_overall_accuracy', 'vviq2_missing_pct', 'vviq2_identical_pct',
        'session_duration_minutes'
    ]
    
    final_df = metrics_df[output_cols].copy()
    
    # Save cleaned participant data
    participant_file = f"outputs/cleaned_participant_data_{timestamp}.csv"
    final_df.to_csv(participant_file, index=False)
    print(f"Cleaned participant data saved to: {participant_file}")
    
    print("\nFinal output summary:")
    print(f"Columns in final dataset: {final_df.columns.tolist()}")
    print("First 2 rows of final dataset:")
    print(final_df.head(2))

def main():
    """
    Main execution function.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting participant exclusion analysis...")
        
        # Load data
        main_data, vviq_df, prolific_df = load_participant_data()
        
        if main_data is None:
            print("ERROR: Could not load main task data")
            return 1
        
        # Identify task rows
        main_data = identify_task_rows(main_data)
        
        # Calculate exclusion metrics
        metrics_df = calculate_exclusion_metrics(main_data, vviq_df, prolific_df)
        
        print(f"\nMetrics calculated for {len(metrics_df)} participants")
        print("Metrics dataframe columns:")
        print(metrics_df.columns.tolist())
        print("First 2 rows of metrics:")
        print(metrics_df.head(2))
        
        # Apply exclusion criteria
        metrics_df, exclusion_log = apply_exclusion_criteria(metrics_df)
        
        # Save outputs
        save_outputs(metrics_df, exclusion_log)

        print(f"\nFinal data processing summary:")
        print(f"Total participants processed: {len(metrics_df)}")
        print(f"Participants included: {metrics_df['included'].sum()}")
        print(f"Participants excluded: {(~metrics_df['included']).sum()}")
        print(f"Inclusion rate: {(metrics_df['included'].sum()/len(metrics_df))*100:.1f}%")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
