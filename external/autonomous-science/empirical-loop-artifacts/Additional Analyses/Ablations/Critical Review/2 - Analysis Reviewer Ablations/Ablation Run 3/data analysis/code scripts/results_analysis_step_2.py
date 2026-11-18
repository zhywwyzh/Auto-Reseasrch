import pandas as pd
import numpy as np
import glob
import os
from datetime import datetime
import re
from collections import Counter

def get_timestamp():
    """
    Generate timestamp string in YYYYMMDD_HHMMSS format.
    
    Returns:
        str: Timestamp string
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def find_most_recent_file(pattern):
    """
    Find the most recent file matching a pattern with <TIMESTAMP> placeholder.
    
    Args:
        pattern (str): File pattern with <TIMESTAMP> placeholder
        
    Returns:
        str: Path to most recent file, or None if no files found
    """
    # Replace <TIMESTAMP> with wildcard pattern
    search_pattern = pattern.replace('<TIMESTAMP>', '*')
    matching_files = glob.glob(search_pattern)
    
    if not matching_files:
        return None
        
    # Get most recent file by modification time
    most_recent = max(matching_files, key=os.path.getmtime)
    return most_recent

def extract_vviq2_score(response_str):
    """
    Extract numeric score from VVIQ2 response string.
    
    Args:
        response_str (str): Response string containing numeric score at end
        
    Returns:
        int or None: Extracted score (1-5) or None if extraction fails
    """
    if pd.isna(response_str) or response_str == '':
        return None
    
    # Extract last number from string
    numbers = re.findall(r'\d+', str(response_str))
    if numbers:
        score = int(numbers[-1])
        if 1 <= score <= 5:
            return score
    return None

def load_and_validate_task_data():
    """
    Load and validate all task data files.
    
    Returns:
        pd.DataFrame: Combined task data from all participant files
    """
    print("Loading task data files...")
    
    # Find all task data files
    task_files = glob.glob('../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv')
    print(f"Found {len(task_files)} task data files")
    
    if not task_files:
        print("ERROR: No task data files found!")
        return None
    
    required_columns = [
        'participantId', 'table', 'isPractice', 'VWM_trial', 'VWM_error_absolute_degrees',
        'VWM_pracAttempt', 'VWM_timeout', 'VWM_rt_ms', 'MRT_trial', 'MRT_isCorrect',
        'MRT_angle_degrees', 'MRT_pracAttempt', 'MRT_timeout', 'MRT_rt_ms'
    ]
    
    all_data = []
    
    for file_path in task_files:
        print(f"Loading: {file_path}")
        try:
            df = pd.read_csv(file_path)
            print(f"Columns in {file_path}: {list(df.columns)}")
            print(f"First 3 rows of {file_path}:")
            print(df.head(3))
            
            # Check for required columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                print(f"WARNING: Missing columns in {file_path}: {missing_cols}")
                continue
                
            all_data.append(df)
            
        except Exception as e:
            print(f"ERROR loading {file_path}: {e}")
            continue
    
    if not all_data:
        print("ERROR: No valid task data files loaded!")
        return None
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    print(f"Combined task data shape: {combined_data.shape}")
    print(f"Unique participants in task data: {combined_data['participantId'].nunique()}")
    
    # Print unique values for key experimental design columns
    print("\nUnique values in key columns:")
    print(f"table values: {sorted(combined_data['table'].unique())}")
    print(f"isPractice values: {sorted(combined_data['isPractice'].unique())}")
    print(f"MRT_angle_degrees values: {sorted(combined_data['MRT_angle_degrees'].dropna().unique())}")
    
    return combined_data

def load_and_validate_vviq2_data():
    """
    Load and validate VVIQ2 data.
    
    Returns:
        pd.DataFrame: VVIQ2 data
    """
    print("\nLoading VVIQ2 data...")
    
    vviq_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
    
    try:
        vviq_data = pd.read_csv(vviq_file)
        print(f"VVIQ2 data shape: {vviq_data.shape}")
        print(f"VVIQ2 columns: {list(vviq_data.columns)}")
        print("First 3 rows of VVIQ2 data:")
        print(vviq_data.head(3))
        
        if 'PROLIFIC_PID' not in vviq_data.columns:
            print("ERROR: PROLIFIC_PID column not found in VVIQ2 data!")
            return None
            
        print(f"Unique participants in VVIQ2: {vviq_data['PROLIFIC_PID'].nunique()}")
        return vviq_data
        
    except Exception as e:
        print(f"ERROR loading VVIQ2 data: {e}")
        return None

def load_and_validate_demographic_data():
    """
    Load and validate demographic data.
    
    Returns:
        pd.DataFrame: Demographic data
    """
    print("\nLoading demographic data...")
    
    # Find most recent demographic file
    demo_pattern = 'outputs/prolific_demographic_data_<TIMESTAMP>.csv'
    demo_file = find_most_recent_file(demo_pattern)
    
    if not demo_file:
        print("ERROR: No demographic data file found!")
        return None
    
    print(f"Using demographic file: {demo_file}")
    
    try:
        demo_data = pd.read_csv(demo_file)
        print(f"Demographic data shape: {demo_data.shape}")
        print(f"Demographic columns: {list(demo_data.columns)}")
        print("First 3 rows of demographic data:")
        print(demo_data.head(3))
        
        required_demo_cols = ['participant_id', 'status']
        missing_cols = [col for col in required_demo_cols if col not in demo_data.columns]
        if missing_cols:
            print(f"ERROR: Missing columns in demographic data: {missing_cols}")
            return None
            
        print(f"Unique participants in demographic: {demo_data['participant_id'].nunique()}")
        return demo_data
        
    except Exception as e:
        print(f"ERROR loading demographic data: {e}")
        return None

def analyze_vwm_practice_performance(task_data):
    """
    Analyze VWM practice performance for each participant.
    
    Args:
        task_data (pd.DataFrame): Combined task data
        
    Returns:
        dict: Dictionary with participant_id as key and final practice error as value
    """
    print("\nAnalyzing VWM practice performance...")
    
    # Filter VWM practice data
    vwm_practice = task_data[
        (task_data['isPractice'] == True) & 
        (task_data['table'] == 'vwm_practice')
    ].copy()
    
    print(f"VWM practice trials: {len(vwm_practice)}")
    print(f"Participants with VWM practice data: {vwm_practice['participantId'].nunique()}")
    
    vwm_results = {}
    
    for participant in vwm_practice['participantId'].unique():
        participant_data = vwm_practice[vwm_practice['participantId'] == participant]
        
        # Get final practice attempt
        max_attempt = participant_data['VWM_pracAttempt'].max()
        final_attempt_data = participant_data[participant_data['VWM_pracAttempt'] == max_attempt]
        
        # Calculate mean absolute error for final attempt
        mean_error = final_attempt_data['VWM_error_absolute_degrees'].mean()
        vwm_results[participant] = mean_error
        
        print(f"Participant {participant}: Final VWM practice error = {mean_error:.2f}°")
    
    return vwm_results

def analyze_mrt_practice_performance(task_data):
    """
    Analyze MRT practice performance for each participant.
    
    Args:
        task_data (pd.DataFrame): Combined task data
        
    Returns:
        dict: Dictionary with participant_id as key and final practice accuracy as value
    """
    print("\nAnalyzing MRT practice performance...")
    
    # Filter MRT practice data
    mrt_practice = task_data[
        (task_data['isPractice'] == True) & 
        (task_data['table'] == 'mrt_practice')
    ].copy()
    
    print(f"MRT practice trials: {len(mrt_practice)}")
    print(f"Participants with MRT practice data: {mrt_practice['participantId'].nunique()}")
    
    mrt_results = {}
    
    for participant in mrt_practice['participantId'].unique():
        participant_data = mrt_practice[mrt_practice['participantId'] == participant]
        
        # Get final practice attempt
        max_attempt = participant_data['MRT_pracAttempt'].max()
        final_attempt_data = participant_data[participant_data['MRT_pracAttempt'] == max_attempt]
        
        # Calculate accuracy for final attempt
        total_trials = len(final_attempt_data)
        correct_trials = final_attempt_data['MRT_isCorrect'].sum()
        accuracy = (correct_trials / total_trials) * 100 if total_trials > 0 else 0
        
        mrt_results[participant] = accuracy
        
        print(f"Participant {participant}: Final MRT practice accuracy = {accuracy:.1f}% ({correct_trials}/{total_trials})")
    
    return mrt_results

def analyze_main_task_engagement(task_data):
    """
    Analyze main task engagement metrics for each participant.
    
    Args:
        task_data (pd.DataFrame): Combined task data
        
    Returns:
        dict: Dictionary with engagement metrics for each participant
    """
    print("\nAnalyzing main task engagement...")
    print(f"Available table values: {sorted(task_data['table'].unique())}")
    print(f"Available isPractice values: {sorted(task_data['isPractice'].unique())}")
    
    engagement_results = {}
    
    # Get all participants
    all_participants = task_data['participantId'].unique()
    
    for participant in all_participants:
        participant_data = task_data[task_data['participantId'] == participant]
        results = {}
        
        # VWM timeout rate (main task: table == 'vwm_test')
        vwm_main = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['table'] == 'vwm_test')
        ]
        
        if len(vwm_main) > 0:
            vwm_timeout_rate = vwm_main['VWM_timeout'].mean()
            results['vwm_timeout_rate'] = vwm_timeout_rate
        else:
            results['vwm_timeout_rate'] = np.nan
        
        # MRT timeout rate (main task: table == 'mrt_test')
        mrt_main = participant_data[
            (participant_data['isPractice'] == False) & 
            (participant_data['table'] == 'mrt_test')
        ]
        
        if len(mrt_main) > 0:
            mrt_timeout_rate = mrt_main['MRT_timeout'].mean()
            results['mrt_timeout_rate'] = mrt_timeout_rate
            
            # MRT 0° accuracy
            mrt_0deg = mrt_main[mrt_main['MRT_angle_degrees'] == 0]
            if len(mrt_0deg) > 0:
                mrt_0deg_accuracy = mrt_0deg['MRT_isCorrect'].mean()
                results['mrt_0deg_accuracy'] = mrt_0deg_accuracy
            else:
                results['mrt_0deg_accuracy'] = np.nan
        else:
            results['mrt_timeout_rate'] = np.nan
            results['mrt_0deg_accuracy'] = np.nan
        
        engagement_results[participant] = results
        
        print(f"Participant {participant}: VWM timeout={results['vwm_timeout_rate']:.3f}, "
              f"MRT timeout={results['mrt_timeout_rate']:.3f}, "
              f"MRT 0° acc={results['mrt_0deg_accuracy']:.3f}")
    
    return engagement_results

def analyze_vviq2_responses(vviq_data):
    """
    Analyze VVIQ2 response patterns for each participant.
    
    Args:
        vviq_data (pd.DataFrame): VVIQ2 data
        
    Returns:
        dict: Dictionary with VVIQ2 metrics for each participant
    """
    print("\nAnalyzing VVIQ2 responses...")
    
    vviq_results = {}
    
    # Explicitly define non-question columns to avoid including metadata
    non_question_cols = ['Respondent ID', 'Collector ID', 'Start Date', 'End Date',
                         'IP Address', 'Email Address', 'First Name', 'Last Name',
                         'Custom Data 1', 'PROLIFIC_PID']
    question_cols = [col for col in vviq_data.columns if col not in non_question_cols]
    print(f"Found {len(question_cols)} question columns (expected 32)")

    print(f"Sample response formats from first participant:")
    if len(vviq_data) > 0:
        for col in question_cols[:3]:  # Show first 3 columns
            sample_val = vviq_data[col].iloc[0] if col in vviq_data.columns else "Column not found"
            print(f"  {col}: {sample_val}")

    for idx, row in vviq_data.iterrows():
        participant = row['PROLIFIC_PID']

        # Extract scores from all questions
        scores = []
        for col in question_cols:
            score = extract_vviq2_score(row[col])
            scores.append(score)

        # Calculate missing rate
        valid_scores = [s for s in scores if s is not None]
        missing_rate = (len(scores) - len(valid_scores)) / len(scores)

        # Calculate response pattern score (proportion of identical ratings)
        if valid_scores:
            score_counts = Counter(valid_scores)
            most_common_count = score_counts.most_common(1)[0][1]
            pattern_score = most_common_count / len(valid_scores)
        else:
            pattern_score = 1.0  # All missing = 100% identical

        vviq_results[participant] = {
            'missing_rate': missing_rate,
            'pattern_score': pattern_score
        }

        print(f"Participant {participant}: Missing rate={missing_rate:.3f}, "
              f"Pattern score={pattern_score:.3f}")

    return vviq_results

def apply_exclusion_criteria(vwm_practice, mrt_practice, engagement, vviq_results, demo_data):
    """
    Apply all exclusion criteria in cascaded fashion and generate results.
    """
    print("\nApplying exclusion criteria...")
    
    # Get all unique participants across data sources
    task_participants = set(list(vwm_practice.keys()) + list(mrt_practice.keys()) + list(engagement.keys()))
    vviq_participants = set(vviq_results.keys())
    demo_participants = set(demo_data['participant_id'].tolist())
    
    print(f"Task participants: {len(task_participants)}")
    print(f"VVIQ participants: {len(vviq_participants)}")  
    print(f"Demo participants: {len(demo_participants)}")
    
    # Find participants with complete data
    complete_participants = task_participants & vviq_participants & demo_participants
    print(f"Participants with complete data: {len(complete_participants)}")
    
    # Find all unique participants across all datasets (union)
    all_participants = task_participants | vviq_participants | demo_participants
    
    # Build complete metrics dataframe
    all_metrics = []
    for participant in complete_participants:
        metrics = {
            'participant_id': participant,
            'vwm_practice_final_error': vwm_practice.get(participant, np.nan),
            'mrt_practice_final_accuracy': mrt_practice.get(participant, np.nan),
            'vwm_timeout_rate': engagement.get(participant, {}).get('vwm_timeout_rate', np.nan),
            'mrt_timeout_rate': engagement.get(participant, {}).get('mrt_timeout_rate', np.nan),
            'mrt_0deg_accuracy': engagement.get(participant, {}).get('mrt_0deg_accuracy', np.nan),
            'vviq2_missing_rate': vviq_results.get(participant, {}).get('missing_rate', np.nan),
            'vviq2_response_pattern_score': vviq_results.get(participant, {}).get('pattern_score', np.nan),
            'included_in_analysis': True,
            'exclusion_reason': 'none'
        }
        all_metrics.append(metrics)
    
    results_df = pd.DataFrame(all_metrics)
    
    # Initialize exclusion counts
    exclusion_counts = {
        'technical_incomplete_data_exclusions': len(all_participants) - len(complete_participants),
        'vwm_practice_failures': 0,
        'mrt_practice_failures': 0,
        'vwm_timeout_exclusions': 0,
        'mrt_timeout_exclusions': 0,
        'mrt_0deg_engagement_failures': 0,
        'vviq2_missing_data_exclusions': 0,
        'vviq2_patterned_response_exclusions': 0
    }
    
    # Apply criteria sequentially (cascaded)
    remaining_count = len(complete_participants)
    print(f"Starting cascaded exclusions with {remaining_count} participants with complete data")
    
    # VWM practice exclusion (>30° error)
    vwm_prac_mask = (results_df['included_in_analysis']) & (~pd.isna(results_df['vwm_practice_final_error'])) & (results_df['vwm_practice_final_error'] > 30)
    excluded_count = vwm_prac_mask.sum()
    results_df.loc[vwm_prac_mask, ['included_in_analysis', 'exclusion_reason']] = [False, 'VWM_practice_error']
    exclusion_counts['vwm_practice_failures'] = excluded_count
    remaining_count -= excluded_count
    print(f"After VWM practice exclusion: {remaining_count} remaining ({excluded_count} excluded)")
    
    # MRT practice exclusion (<66.7% accuracy)
    mrt_prac_mask = (results_df['included_in_analysis']) & (~pd.isna(results_df['mrt_practice_final_accuracy'])) & (results_df['mrt_practice_final_accuracy'] < 66.7)
    excluded_count = mrt_prac_mask.sum()
    results_df.loc[mrt_prac_mask, ['included_in_analysis', 'exclusion_reason']] = [False, 'MRT_practice_accuracy']
    exclusion_counts['mrt_practice_failures'] = excluded_count
    remaining_count -= excluded_count
    print(f"After MRT practice exclusion: {remaining_count} remaining ({excluded_count} excluded)")
    
    # VWM timeout exclusion (>20%)
    vwm_timeout_mask = (results_df['included_in_analysis']) & (~pd.isna(results_df['vwm_timeout_rate'])) & (results_df['vwm_timeout_rate'] > 0.2)
    excluded_count = vwm_timeout_mask.sum()
    results_df.loc[vwm_timeout_mask, ['included_in_analysis', 'exclusion_reason']] = [False, 'VWM_timeout_rate']
    exclusion_counts['vwm_timeout_exclusions'] = excluded_count
    remaining_count -= excluded_count
    print(f"After VWM timeout exclusion: {remaining_count} remaining ({excluded_count} excluded)")
    
    # MRT timeout exclusion (>20%)
    mrt_timeout_mask = (results_df['included_in_analysis']) & (~pd.isna(results_df['mrt_timeout_rate'])) & (results_df['mrt_timeout_rate'] > 0.2)
    excluded_count = mrt_timeout_mask.sum()
    results_df.loc[mrt_timeout_mask, ['included_in_analysis', 'exclusion_reason']] = [False, 'MRT_timeout_rate']
    exclusion_counts['mrt_timeout_exclusions'] = excluded_count
    remaining_count -= excluded_count
    print(f"After MRT timeout exclusion: {remaining_count} remaining ({excluded_count} excluded)")
    
    # MRT 0° engagement exclusion (<70%)
    mrt_0deg_mask = (results_df['included_in_analysis']) & (~pd.isna(results_df['mrt_0deg_accuracy'])) & (results_df['mrt_0deg_accuracy'] < 0.7)
    excluded_count = mrt_0deg_mask.sum()
    results_df.loc[mrt_0deg_mask, ['included_in_analysis', 'exclusion_reason']] = [False, 'MRT_0deg_engagement']
    exclusion_counts['mrt_0deg_engagement_failures'] = excluded_count
    remaining_count -= excluded_count
    print(f"After MRT 0° engagement exclusion: {remaining_count} remaining ({excluded_count} excluded)")
    
    # VVIQ2 missing data exclusion (>10%)
    vviq_missing_mask = (results_df['included_in_analysis']) & (~pd.isna(results_df['vviq2_missing_rate'])) & (results_df['vviq2_missing_rate'] > 0.1)
    excluded_count = vviq_missing_mask.sum()
    results_df.loc[vviq_missing_mask, ['included_in_analysis', 'exclusion_reason']] = [False, 'VVIQ2_missing_data']
    exclusion_counts['vviq2_missing_data_exclusions'] = excluded_count
    remaining_count -= excluded_count
    print(f"After VVIQ2 missing data exclusion: {remaining_count} remaining ({excluded_count} excluded)")
    
    # VVIQ2 patterned response exclusion (>80% identical)
    vviq_pattern_mask = (results_df['included_in_analysis']) & (~pd.isna(results_df['vviq2_response_pattern_score'])) & (results_df['vviq2_response_pattern_score'] > 0.8)
    excluded_count = vviq_pattern_mask.sum()
    results_df.loc[vviq_pattern_mask, ['included_in_analysis', 'exclusion_reason']] = [False, 'VVIQ2_patterned_responses']
    exclusion_counts['vviq2_patterned_response_exclusions'] = excluded_count
    remaining_count -= excluded_count
    print(f"After VVIQ2 patterned response exclusion: {remaining_count} remaining ({excluded_count} excluded)")
    
    # Final retained count
    final_retained = results_df['included_in_analysis'].sum()
    
    # Create exclusion log
    exclusion_log = []
    descriptions = {
        'technical_incomplete_data_exclusions': 'Incomplete data across task/VVIQ2/demographic sources',
        'vwm_practice_failures': 'VWM practice final attempt error >30 degrees',
        'mrt_practice_failures': 'MRT practice final attempt accuracy <66.7%',
        'vwm_timeout_exclusions': 'VWM main task timeout rate >20%',
        'mrt_timeout_exclusions': 'MRT main task timeout rate >20%',
        'mrt_0deg_engagement_failures': 'MRT 0-degree rotation accuracy <70%',
        'vviq2_missing_data_exclusions': 'VVIQ2 missing response rate >10%',
        'vviq2_patterned_response_exclusions': 'VVIQ2 identical response rate >80%'
    }
    
    for criteria, count in exclusion_counts.items():
        exclusion_log.append({
            'exclusion_criteria': criteria,
            'exclusion_count': count,
            'exclusion_description': descriptions[criteria]
        })
    
    # Add total retained count
    exclusion_log.append({
        'exclusion_criteria': 'total_participants_retained',
        'exclusion_count': final_retained,
        'exclusion_description': 'Total participants retained for analysis'
    })
    
    return exclusion_log, results_df.to_dict('records')

def print_final_exclusion_summary(exclusion_log, all_participants_count):
    """Print cascaded exclusion summary with correct counts."""
    print(f"\n{'='*60}")
    print("FINAL EXCLUSION SUMMARY")
    print(f"{'='*60}")

    remaining = all_participants_count
    print(f"Initial participants: {remaining}")

    # Process exclusions in the order they were applied
    exclusion_order = [
        'technical_incomplete_data_exclusions',
        'vwm_practice_failures', 
        'mrt_practice_failures',
        'vwm_timeout_exclusions',
        'mrt_timeout_exclusions', 
        'mrt_0deg_engagement_failures',
        'vviq2_missing_data_exclusions',
        'vviq2_patterned_response_exclusions'
    ]
    
    for criteria in exclusion_order:
        entry = next(e for e in exclusion_log if e['exclusion_criteria'] == criteria)
        remaining -= entry['exclusion_count']
        print(f"After {criteria}: {remaining} remaining ({entry['exclusion_count']} excluded)")

    final_retained = next(e['exclusion_count'] for e in exclusion_log if e['exclusion_criteria'] == 'total_participants_retained')
    print(f"\nFinal participants retained for analysis: {final_retained}")
    print(f"{'='*60}")

def main():
    """
    Main execution function.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        # Create outputs directory
        os.makedirs('outputs', exist_ok=True)
        
        # Load all data sources
        task_data = load_and_validate_task_data()
        if task_data is None:
            return 1
        
        vviq_data = load_and_validate_vviq2_data()
        if vviq_data is None:
            return 1
        
        demo_data = load_and_validate_demographic_data()
        if demo_data is None:
            return 1
        
        # Analyze performance metrics
        vwm_practice = analyze_vwm_practice_performance(task_data)
        mrt_practice = analyze_mrt_practice_performance(task_data)
        engagement = analyze_main_task_engagement(task_data)
        vviq_results = analyze_vviq2_responses(vviq_data)
        
        # Apply exclusion criteria
        exclusion_log, included_participants = apply_exclusion_criteria(
            vwm_practice, mrt_practice, engagement, vviq_results, demo_data
        )
        
        # Save results
        timestamp = get_timestamp()
        
        # Save exclusion log
        exclusion_df = pd.DataFrame(exclusion_log)
        exclusion_file = f'outputs/participant_exclusion_log_{timestamp}.csv'
        exclusion_df.to_csv(exclusion_file, index=False)
        print(f"\nExclusion log saved to: {exclusion_file}")
        print("Exclusion log columns:", list(exclusion_df.columns))
        print("First 2 rows of exclusion log:")
        print(exclusion_df.head(2))
        
        # Save included participants
        included_df = pd.DataFrame(included_participants)
        included_file = f'outputs/included_participants_{timestamp}.csv'
        included_df.to_csv(included_file, index=False)
        print(f"\nIncluded participants saved to: {included_file}")
        print("Included participants columns:", list(included_df.columns))
        print("First 2 rows of included participants:")
        print(included_df.head(2))

        # Print final summary
        all_participants = set(list(vwm_practice.keys()) + list(mrt_practice.keys()) + list(engagement.keys())) | set(vviq_results.keys()) | set(demo_data['participant_id'].tolist())
        print_final_exclusion_summary(exclusion_log, len(all_participants))
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
