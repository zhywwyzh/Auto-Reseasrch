#!/usr/bin/env python3
"""
VVIQ2 Data Processing and Cleaning Script

This script processes the Vividness of Visual Imagery Questionnaire-2 (VVIQ2) data,
applies various exclusion criteria, and calculates final scores and subscales.
"""

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import sys

def extract_numeric_score(response_text):
    """
    Extract the numeric score (1-5) from the end of a response string.
    
    Parameters:
    -----------
    response_text : str or NaN
        The response text containing descriptive text ending with numeric score
        
    Returns:
    --------
    int or NaN
        The extracted numeric score (1-5) or NaN if extraction fails
    """
    if pd.isna(response_text):
        return np.nan
    
    # Convert to string if not already
    response_str = str(response_text)
    
    # Extract the last digit from the string
    digits = re.findall(r'\d', response_str)
    if digits:
        last_digit = int(digits[-1])
        # Validate score is between 1-5
        if 1 <= last_digit <= 5:
            return last_digit
    
    return np.nan

def calculate_completion_time(start_date, end_date):
    """
    Calculate completion time in minutes between start and end dates.
    
    Parameters:
    -----------
    start_date : str
        Start timestamp string
    end_date : str
        End timestamp string
        
    Returns:
    --------
    float
        Completion time in minutes, or NaN if calculation fails
    """
    try:
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)
        completion_time = (end_dt - start_dt).total_seconds() / 60
        return completion_time
    except Exception as e:
        print(f"Error converting dates {start_date} to {end_date}: {e}")
        return np.nan

def check_alternating_pattern(scores, pattern_type='1-2'):
    """
    Check if scores follow an alternating pattern (1-2-1-2 or 4-5-4-5).
    Only counts full consecutive pairs that match the pattern.
    
    Parameters:
    -----------
    scores : list
        List of numeric scores
    pattern_type : str
        Type of pattern to check ('1-2' or '4-5')
        
    Returns:
    --------
    float
        Proportion of items following the alternating pattern
    """
    if len(scores) < 4:
        return 0.0
    
    # Define the pattern pairs to look for
    if pattern_type == '1-2':
        pattern_pair = [1, 2]
    elif pattern_type == '4-5':
        pattern_pair = [4, 5]
    else:
        return 0.0
    
    # Count consecutive pairs that match the pattern
    consecutive_pair_matches = 0
    total_possible_pairs = 0
    
    # Check pairs of consecutive scores
    for i in range(0, len(scores)-1, 2):
        if i+1 < len(scores) and not pd.isna(scores[i]) and not pd.isna(scores[i+1]):
            total_possible_pairs += 1
            if scores[i] == pattern_pair[0] and scores[i+1] == pattern_pair[1]:
                consecutive_pair_matches += 1
    
    print(f"Alternating pattern {pattern_type}: {consecutive_pair_matches}/{total_possible_pairs} consecutive pairs match")
    return consecutive_pair_matches / len(scores) * 2 if len(scores) > 0 else 0.0

def check_ascending_descending_pattern(scores):
    """
    Check if scores follow ascending (1-2-3-4-5) or descending (5-4-3-2-1) patterns.
    Separately evaluates whether segments consistently match ascending or descending patterns.
    
    Parameters:
    -----------
    scores : list
        List of numeric scores
        
    Returns:
    --------
    float
        Proportion of items following consistent ascending or descending patterns
    """
    if len(scores) < 5:
        return 0.0
    
    ascending_pattern = [1, 2, 3, 4, 5]
    descending_pattern = [5, 4, 3, 2, 1]
    
    # Check for repeated patterns
    pattern_matches = 0
    total_positions = 0
    
    for i in range(0, len(scores), 5):
        segment = scores[i:i+5]
        if len(segment) == 5:
            total_positions += 5
            
            # Check if segment matches ascending pattern
            asc_matches = 0
            desc_matches = 0
            
            for j, score in enumerate(segment):
                if not pd.isna(score):
                    if score == ascending_pattern[j]:
                        asc_matches += 1
                    if score == descending_pattern[j]:
                        desc_matches += 1
            
            # Only count the better matching pattern (not both)
            pattern_matches += max(asc_matches, desc_matches)
            
            # Print detailed information about pattern matching
            if max(asc_matches, desc_matches) >= 3:
                pattern_type = "ascending" if asc_matches >= desc_matches else "descending"
                print(f"Segment {i//5+1} matches {pattern_type} pattern: {max(asc_matches, desc_matches)}/5 items")
    
    return pattern_matches / total_positions if total_positions > 0 else 0.0

def main():
    """
    Main function to process VVIQ2 data with comprehensive cleaning and scoring.
    
    Returns:
    --------
    int
        0 for successful completion, 1 for errors
    """
    try:
        print("Starting VVIQ2 data processing...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Read input file
        input_file = 'raw_data/Vividness of Visual Imagery Questionnaire-2.csv'
        print(f"Reading input file: {input_file}")
        
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded data with shape: {df.shape}")
            # Strip whitespace from column names to handle discrepancies
            df.columns = df.columns.str.strip()
            print("Stripped whitespace from all column names")
        except FileNotFoundError:
            print(f"Error: Input file not found: {input_file}")
            return 1
        except Exception as e:
            print(f"Error reading input file: {e}")
            return 1
        
        # Print all columns
        print("\nAll columns in dataset:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}: {col}")
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Define required columns
        required_cols = [
            'PROLIFIC_PID',
            'Start Date',
            'End Date',
            'The exact contour of face, head, shoulders and body.',
            'Characteristic poses of head, attitudes of body etc.',
            'The precise carriage, length of step, etc. in walking.',
            'The different colours worn in some familiar clothes.',
            'The sun is rising above the horizon into a hazy sky.',
            'The sky clears and surrounds the sun with blueness.',
            'Clouds. A storm blows up, with flashes of lightening.',
            'A rainbow appears.',
            'The overall appearance of the shop from the opposite side of the road.',
            'A window display including colours, shape and details of individual items for sale.',
            'You are near the entrance. The colour, shape and details of the door.',
            'You enter the shop and go to the counter. The counter assistant serves you. Money changes hands.',
            'The contours of the landscape.',
            'The colour and shape of the trees.',
            'The colour and shape of the lake.',
            'A strong wind blows on the tree and on the lake causing waves.',
            'You observe the heavy traffic travelling at maximum speed around your car. The overall appearance of vehicles, their colours, sizes and shapes.',
            'Your car accelerates to overtake the traffic directly in front of you. You see and urgent expression on the face of the driver and the people in the other vehicles as you pass.',
            'A large truck is flashing its headlight directly behind. Your car quickly moves over to let the truck pass. The driver signals with a friendly wave.',
            'You see a broken-down vehicle beside the road. Its lights are flashing. The driver is looking concerned and she is using a mobile phone.',
            'The overall appearance and colour of the water, surf, and sky.',
            'Bathers are swimming and splashing about in the water. Some are playing with a brightly coloured beach ball.',
            'An ocean liner crosses the horizon. It leaves a trail of smoke in the blue sky.',
            'A beautiful air balloon appears with four people aboard. The balloon drifts past you, almost directly overhead. The passengers wave and smile. You wave and smile back at them.',
            'The overall appearance of the station viewed from in front of the main entrance.',
            'You walk into the station. The colour, shape and details of the entrance hall.',
            'You approach the ticket office, go to a vacant counter and purchase your ticket.',
            'You walk to the platform and observe other passengers and the railway lines. A train arrives. You climb aboard.',
            'The overall appearance and design of the garden.',
            'The colour and shape of the bushes and shrubs.',
            'The colour and appearance of the flowers.',
            'Some birds fly down onto the lawn and start pecking for food.'
        ]
        
        # Strip whitespace from required column names
        required_cols = [col.strip() for col in required_cols]
        
        # Check for required columns
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Error: Missing required columns: {missing_cols}")
            return 1
        
        print(f"All required columns found. Processing {len(df)} participants...")
        
        # Filter out rows with null PROLIFIC_PID
        initial_count = len(df)
        df = df.dropna(subset=['PROLIFIC_PID'])
        print(f"Removed {initial_count - len(df)} rows with missing PROLIFIC_PID")
        
        # Verify PROLIFIC_PID uniqueness
        unique_prolific_ids = df['PROLIFIC_PID'].nunique()
        print(f"Number of unique PROLIFIC_PIDs: {unique_prolific_ids}")
        if unique_prolific_ids < len(df):
            print(f"Warning: {len(df) - unique_prolific_ids} duplicate PROLIFIC_PIDs found")
        
        # Calculate completion time
        print("\nCalculating completion times...")
        df['completion_time_minutes'] = df.apply(
            lambda row: calculate_completion_time(row['Start Date'], row['End Date']), 
            axis=1
        )
        
        print(f"Completion time statistics:")
        print(f"Mean: {df['completion_time_minutes'].mean():.2f} minutes")
        print(f"Median: {df['completion_time_minutes'].median():.2f} minutes")
        print(f"Min: {df['completion_time_minutes'].min():.2f} minutes")
        print(f"Max: {df['completion_time_minutes'].max():.2f} minutes")
        
        # Extract VVIQ2 item columns (32 items)
        vviq_item_cols = required_cols[3:]  # Skip PROLIFIC_PID, Start Date, End Date
        print(f"\nExtracting scores from {len(vviq_item_cols)} VVIQ2 items...")
        
        # Extract numeric scores
        for col in vviq_item_cols:
            new_col_name = f"{col}_score"
            df[new_col_name] = df[col].apply(extract_numeric_score)
        
        # Get score column names
        score_cols = [f"{col}_score" for col in vviq_item_cols]
        
        # Count missing responses per participant
        df['missing_count'] = df[score_cols].isna().sum(axis=1)
        df['missing_percentage'] = (df['missing_count'] / len(score_cols)) * 100
        
        print(f"Missing data statistics:")
        print(f"Mean missing items per participant: {df['missing_count'].mean():.2f}")
        print(f"Participants with >10% missing: {(df['missing_percentage'] > 10).sum()}")
        
        # Initialize exclusion tracking
        exclusions = []
        df['excluded_participant'] = False
        df['exclusion_reason'] = ''
        
        total_participants = len(df)
        print(f"\nStarting exclusion process with {total_participants} participants...")
        
        # 1. >10% missing responses (>3.2 items, rounded to >3 items)
        missing_threshold = 3
        missing_mask = df['missing_count'] > missing_threshold
        excluded_missing = missing_mask.sum()
        df.loc[missing_mask, 'excluded_participant'] = True
        df.loc[missing_mask, 'exclusion_reason'] = '>10% missing responses'
        exclusions.append(['> 10% missing responses', excluded_missing, total_participants, (excluded_missing/total_participants)*100])
        print(f"Excluded {excluded_missing} participants for >10% missing responses")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Calculate scores for remaining analyses (only for non-excluded participants)
        valid_mask = ~df['excluded_participant']
        
        # Calculate total scores for outlier detection
        df['total_score'] = df[score_cols].sum(axis=1, skipna=True)
        
        # 2. Zero variance AND fast completion
        def has_zero_variance(row):
            scores = [row[col] for col in score_cols if not pd.isna(row[col])]
            return len(set(scores)) <= 1 if len(scores) > 1 else False
        
        zero_var_fast_mask = (
            valid_mask & 
            df.apply(has_zero_variance, axis=1) & 
            (df['completion_time_minutes'] < 3)
        )
        excluded_zero_var = zero_var_fast_mask.sum()
        df.loc[zero_var_fast_mask, 'excluded_participant'] = True
        df.loc[zero_var_fast_mask, 'exclusion_reason'] = 'Zero variance + fast completion'
        exclusions.append(['Zero variance + fast completion', excluded_zero_var, total_participants, (excluded_zero_var/total_participants)*100])
        print(f"Excluded {excluded_zero_var} participants for zero variance + fast completion")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 3. Total VVIQ2 score outliers (>3 SD from mean)
        if valid_mask.sum() > 0:
            valid_scores = df.loc[valid_mask, 'total_score'].dropna()
            if len(valid_scores) > 0:
                mean_score = valid_scores.mean()
                std_score = valid_scores.std()
                outlier_threshold_low = mean_score - 3 * std_score
                outlier_threshold_high = mean_score + 3 * std_score
                
                outlier_mask = (
                    valid_mask & 
                    ((df['total_score'] < outlier_threshold_low) | 
                     (df['total_score'] > outlier_threshold_high))
                )
                excluded_outliers = outlier_mask.sum()
                df.loc[outlier_mask, 'excluded_participant'] = True
                df.loc[outlier_mask, 'exclusion_reason'] = 'Total score outlier (>3 SD)'
                exclusions.append(['Total score outlier (>3 SD)', excluded_outliers, total_participants, (excluded_outliers/total_participants)*100])
                print(f"Excluded {excluded_outliers} participants for total score outliers")
                print(f"Score outlier thresholds: {outlier_threshold_low:.2f} - {outlier_threshold_high:.2f}")
                print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 4. >90% extreme responses AND fast completion
        def extreme_response_percentage(row):
            scores = [row[col] for col in score_cols if not pd.isna(row[col])]
            if len(scores) == 0:
                return 0
            extreme_count = sum(1 for score in scores if score in [1, 5])
            return (extreme_count / len(scores)) * 100
        
        df['extreme_percentage'] = df.apply(extreme_response_percentage, axis=1)
        extreme_fast_mask = (
            valid_mask & 
            (df['extreme_percentage'] > 90) & 
            (df['completion_time_minutes'] < 5)
        )
        excluded_extreme = extreme_fast_mask.sum()
        df.loc[extreme_fast_mask, 'excluded_participant'] = True
        df.loc[extreme_fast_mask, 'exclusion_reason'] = '>90% extreme responses + fast completion'
        exclusions.append(['>90% extreme responses + fast completion', excluded_extreme, total_participants, (excluded_extreme/total_participants)*100])
        print(f"Excluded {excluded_extreme} participants for >90% extreme responses + fast completion")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 5. Completion time <2 minutes
        fast_completion_mask = valid_mask & (df['completion_time_minutes'] < 2)
        excluded_fast = fast_completion_mask.sum()
        df.loc[fast_completion_mask, 'excluded_participant'] = True
        df.loc[fast_completion_mask, 'exclusion_reason'] = 'Completion time <2 minutes'
        exclusions.append(['Completion time <2 minutes', excluded_fast, total_participants, (excluded_fast/total_participants)*100])
        print(f"Excluded {excluded_fast} participants for completion time <2 minutes")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 6. Alternating patterns AND fast completion
        def check_alternating_patterns(row):
            scores = [row[col] for col in score_cols if not pd.isna(row[col])]
            if len(scores) < 4:
                return 0
            
            pattern_1_2 = check_alternating_pattern(scores, '1-2')
            pattern_4_5 = check_alternating_pattern(scores, '4-5')
            
            return max(pattern_1_2, pattern_4_5)
        
        df['alternating_percentage'] = df.apply(check_alternating_patterns, axis=1) * 100
        alternating_fast_mask = (
            valid_mask & 
            (df['alternating_percentage'] > 80) & 
            (df['completion_time_minutes'] < 4)
        )
        excluded_alternating = alternating_fast_mask.sum()
        df.loc[alternating_fast_mask, 'excluded_participant'] = True
        df.loc[alternating_fast_mask, 'exclusion_reason'] = 'Alternating patterns + fast completion'
        exclusions.append(['Alternating patterns + fast completion', excluded_alternating, total_participants, (excluded_alternating/total_participants)*100])
        print(f"Excluded {excluded_alternating} participants for alternating patterns + fast completion")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 7. Ascending/descending patterns
        def check_asc_desc_patterns(row):
            scores = [row[col] for col in score_cols if not pd.isna(row[col])]
            return check_ascending_descending_pattern(scores) * 100
        
        df['asc_desc_percentage'] = df.apply(check_asc_desc_patterns, axis=1)
        asc_desc_mask = valid_mask & (df['asc_desc_percentage'] > 70)
        excluded_asc_desc = asc_desc_mask.sum()
        df.loc[asc_desc_mask, 'excluded_participant'] = True
        df.loc[asc_desc_mask, 'exclusion_reason'] = 'Ascending/descending patterns >70%'
        exclusions.append(['Ascending/descending patterns >70%', excluded_asc_desc, total_participants, (excluded_asc_desc/total_participants)*100])
        print(f"Excluded {excluded_asc_desc} participants for ascending/descending patterns")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 8. Single response value AND fast completion (>87.5% = >28 out of 32 items)
        def single_value_percentage(row):
            scores = [row[col] for col in score_cols if not pd.isna(row[col])]
            if len(scores) == 0:
                return 0
            
            # Count most frequent value
            from collections import Counter
            counts = Counter(scores)
            max_count = max(counts.values()) if counts else 0
            return (max_count / len(scores)) * 100
        
        df['single_value_percentage'] = df.apply(single_value_percentage, axis=1)
        single_value_fast_mask = (
            valid_mask & 
            (df['single_value_percentage'] > 87.5) & 
            (df['completion_time_minutes'] < 4)
        )
        excluded_single_value = single_value_fast_mask.sum()
        df.loc[single_value_fast_mask, 'excluded_participant'] = True
        df.loc[single_value_fast_mask, 'exclusion_reason'] = 'Single response value >87.5% + fast completion'
        exclusions.append(['Single response value >87.5% + fast completion', excluded_single_value, total_participants, (excluded_single_value/total_participants)*100])
        print(f"Excluded {excluded_single_value} participants for single response value + fast completion")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 9. Failed to complete within reasonable timeframe (>45 minutes)
        long_completion_mask = valid_mask & (df['completion_time_minutes'] > 45)
        excluded_long = long_completion_mask.sum()
        df.loc[long_completion_mask, 'excluded_participant'] = True
        df.loc[long_completion_mask, 'exclusion_reason'] = 'Completion time >45 minutes'
        exclusions.append(['Completion time >45 minutes', excluded_long, total_participants, (excluded_long/total_participants)*100])
        print(f"Excluded {excluded_long} participants for completion time >45 minutes")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Update valid mask
        valid_mask = ~df['excluded_participant']
        
        # 10. Evidence of random responding (basic check - no coherent pattern within scenarios)
        def check_random_responding(row):
            # Check variance within each scenario (4 items each)
            scenario_variances = []
            for i in range(0, len(score_cols), 4):
                scenario_scores = [row[score_cols[j]] for j in range(i, min(i+4, len(score_cols))) if not pd.isna(row[score_cols[j]])]
                if len(scenario_scores) > 1:
                    scenario_variances.append(np.var(scenario_scores))
    
            # If all scenarios have very high variance (suggesting random responding)
            if len(scenario_variances) > 0:
                mean_variance = np.mean(scenario_variances)
                # NOTE: The threshold of 2.0 is empirical and may need adjustment based on
                # pilot data or statistical analysis of response patterns
                threshold = 2.0
                if mean_variance > threshold:
                    print(f"Detected high variance ({mean_variance:.2f}) across scenarios, suggesting random responding")
                return mean_variance > threshold
            return False
        
        random_responding_mask = valid_mask & df.apply(check_random_responding, axis=1)
        excluded_random = random_responding_mask.sum()
        df.loc[random_responding_mask, 'excluded_participant'] = True
        df.loc[random_responding_mask, 'exclusion_reason'] = 'Evidence of random responding'
        exclusions.append(['Evidence of random responding', excluded_random, total_participants, (excluded_random/total_participants)*100])
        print(f"Excluded {excluded_random} participants for evidence of random responding")
        print(f"Total excluded so far: {df['excluded_participant'].sum()} participants ({(df['excluded_participant'].sum()/total_participants)*100:.1f}%)")
        
        # Final valid participants
        final_valid_mask = ~df['excluded_participant']
        final_count = final_valid_mask.sum()
        print(f"\nFinal sample: {final_count} participants ({(final_count/total_participants)*100:.1f}% retained)")
        
        # Calculate subscale scores for valid participants
        print("\nCalculating VVIQ2 subscale scores...")
        
        # Define subscales (4 items each)
        subscales = {
            'face_person_subscale': score_cols[0:4],
            'sunrise_subscale': score_cols[4:8], 
            'shop_subscale': score_cols[8:12],
            'countryside_subscale': score_cols[12:16],
            'driving_subscale': score_cols[16:20],
            'beach_subscale': score_cols[20:24],
            'railway_subscale': score_cols[24:28],
            'garden_subscale': score_cols[28:32]
        }
        
        # Calculate subscale scores
        for subscale_name, subscale_cols in subscales.items():
            df[subscale_name] = df[subscale_cols].sum(axis=1, skipna=True)
            print(f"{subscale_name}: range {df.loc[final_valid_mask, subscale_name].min()}-{df.loc[final_valid_mask, subscale_name].max()}")
        
        # Recalculate total score (sum of all 32 items)
        df['total_score'] = df[score_cols].sum(axis=1, skipna=True)
        
        # Z-standardize total VVIQ2 scores (only for valid participants)
        if final_count > 0:
            valid_total_scores = df.loc[final_valid_mask, 'total_score']
            mean_total = valid_total_scores.mean()
            std_total = valid_total_scores.std()
            df['total_score_z'] = (df['total_score'] - mean_total) / std_total
            print(f"Total score statistics (valid participants): Mean={mean_total:.2f}, SD={std_total:.2f}")
        else:
            df['total_score_z'] = np.nan
        
        # Prepare output dataframe
        output_cols = [
            'PROLIFIC_PID',
            'completion_time_minutes', 
            'total_score',
            'total_score_z',
            'face_person_subscale',
            'sunrise_subscale',
            'shop_subscale', 
            'countryside_subscale',
            'driving_subscale',
            'beach_subscale',
            'railway_subscale',
            'garden_subscale',
            'excluded_participant',
            'exclusion_reason'
        ]
        
        output_df = df[output_cols].copy()
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save cleaned scores
        output_file = f'outputs/VVIQ2_cleaned_scores_{timestamp}.csv'
        output_df.to_csv(output_file, index=False)
        if os.path.exists(output_file):
            print(f"\nConfirmed file saved: {output_file}")
        else:
            print(f"\nWarning: File not found after saving attempt: {output_file}")
        
        # Print output data structure
        print("\nOutput dataframe columns:")
        for i, col in enumerate(output_df.columns):
            print(f"{i+1}: {col}")
        
        print("\nFirst 2 rows of output:")
        print(output_df.head(2))
        
        # Create exclusion log
        exclusion_df = pd.DataFrame(exclusions, columns=[
            'exclusion_criteria', 
            'count_excluded', 
            'total_assessed', 
            'exclusion_percentage'
        ])
        
        exclusion_file = f'outputs/VVIQ2_exclusion_log_{timestamp}.csv'
        exclusion_df.to_csv(exclusion_file, index=False)
        if os.path.exists(exclusion_file):
            print(f"\nConfirmed exclusion log saved: {exclusion_file}")
        else:
            print(f"\nWarning: Exclusion log file not found after saving attempt: {exclusion_file}")
        
        print("\nExclusion summary:")
        print(exclusion_df)
        
        # Print final summary
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Initial participants: {total_participants}")
        print(f"Final valid participants: {final_count}")
        print(f"Total excluded: {total_participants - final_count}")
        print(f"Retention rate: {(final_count/total_participants)*100:.1f}%")
        
        if final_count > 0:
            print(f"\nFinal sample statistics:")
            print(f"Total VVIQ2 score range: {df.loc[final_valid_mask, 'total_score'].min()}-{df.loc[final_valid_mask, 'total_score'].max()}")
            print(f"Mean completion time: {df.loc[final_valid_mask, 'completion_time_minutes'].mean():.2f} minutes")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
