#!/usr/bin/env python3
"""
VVIQ-2 Data Processing Script

This script processes Vividness of Visual Imagery Questionnaire-2 (VVIQ-2) data by:
1. Extracting numeric scores from text responses
2. Applying data quality exclusion criteria
3. Calculating total and subscale scores
4. Generating cleaned dataset and exclusion log

Requirements:
- Input: VVIQ-2 CSV file with participant responses
- Output: Cleaned dataset and exclusion tracking files
"""

import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
import sys

def extract_numeric_score(text_response):
    """
    Extract numeric score from text response.
    
    Args:
        text_response (str or float): Text containing numeric response or NaN
        
    Returns:
        int or None: Extracted score between 1-5, or None if invalid
    """
    if pd.isna(text_response) or text_response == '':
        return None
    
    # Convert to string if not already
    text_str = str(text_response)
    
    # Look for numbers 1-5 in the text
    numbers = re.findall(r'\b[1-5]\b', text_str)
    
    if len(numbers) == 1:
        score = int(numbers[0])
        if 1 <= score <= 5:
            return score
    elif len(numbers) > 1:
        # If multiple numbers found, try to find the most likely score
        # Look for patterns like "rating: 3" or "score 4"
        for num in numbers:
            score = int(num)
            if 1 <= score <= 5:
                return score
    
    return None

def check_invariant_responding(scores, threshold=0.9):
    """
    Check for invariant responding pattern.
    
    Args:
        scores (list): List of numeric scores
        threshold (float): Threshold for percentage of identical responses
        
    Returns:
        bool: True if participant shows invariant responding above threshold
    """
    if not scores or len(scores) == 0:
        return False
    
    # Count frequency of each score
    score_counts = {}
    for score in scores:
        if score is not None:
            score_counts[score] = score_counts.get(score, 0) + 1
    
    if not score_counts:
        return False
    
    # Calculate percentage of most common response
    max_count = max(score_counts.values())
    total_responses = len([s for s in scores if s is not None])
    
    if total_responses == 0:
        return False
    
    percentage_same = max_count / total_responses
    return percentage_same > threshold

def check_acquiescence_bias(scores, threshold=0.8):
    """
    Check for acquiescence bias (extreme responding).
    
    Args:
        scores (list): List of numeric scores
        threshold (float): Threshold for percentage of extreme responses
        
    Returns:
        bool: True if participant shows acquiescence bias above threshold
    """
    if not scores or len(scores) == 0:
        return False
    
    valid_scores = [s for s in scores if s is not None]
    if len(valid_scores) == 0:
        return False
    
    # Count extreme responses (1 or 5)
    extreme_count = sum(1 for score in valid_scores if score in [1, 5])
    percentage_extreme = extreme_count / len(valid_scores)
    
    return percentage_extreme > threshold

def main():
    """
    Main function to process VVIQ-2 data.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ-2 data processing...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Define input file path
        input_file = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
        
        print(f"Reading input file: {input_file}")
        
        # Read the CSV file
        try:
            df = pd.read_csv(input_file)
            print(f"Successfully loaded CSV with shape: {df.shape}")
        except FileNotFoundError:
            print(f"Error: Input file not found: {input_file}")
            return 1
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return 1

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        print("\nStripped whitespace from column names.")

        # Print actual column names for debugging, with lengths
        print("\nActual column names in the dataset (with lengths):")
        for i, col in enumerate(df.columns):
            print(f"{i+1}: '{col}' (len={len(col)})")
        print(f"\nFirst 3 rows of the dataset:")
        print(df.head(3))

        # Define the required questionnaire columns in order
        questionnaire_columns = [
            "The exact contour of face, head, shoulders and body.",
            "Characteristic poses of head, attitudes of body etc.",
            "The precise carriage, length of step, etc. in walking.",
            "The different colours worn in some familiar clothes.",
            "The sun is rising above the horizon into a hazy sky.",
            "The sky clears and surrounds the sun with blueness.",
            "Clouds. A storm blows up, with flashes of lightening.",
            "A rainbow appears.",
            "The overall appearance of the shop from the opposite side of the road.",
            "A window display including colours, shape and details of individual items for sale.",
            "You are near the entrance. The colour, shape and details of the door.",
            "You enter the shop and go to the counter. The counter assistant serves you. Money changes hands.",
            "The contours of the landscape.",
            "The colour and shape of the trees.",
            "The colour and shape of the lake.",
            "A strong wind blows on the tree and on the lake causing waves.",
            "You observe the heavy traffic travelling at maximum speed around your car. The overall appearance of vehicles, their colours, sizes and shapes.",
            "Your car accelerates to overtake the traffic directly in front of you. You see and urgent expression on the face of the driver and the people in the other vehicles as you pass.",
            "A large truck is flashing its headlight directly behind. Your car quickly moves over to let the truck pass. The driver signals with a friendly wave.",
            "You see a broken-down vehicle beside the road. Its lights are flashing. The driver is looking concerned and she is using a mobile phone.",
            "The overall appearance and colour of the water, surf, and sky.",
            "Bathers are swimming and splashing about in the water. Some are playing with a brightly coloured beach ball.",
            "An ocean liner crosses the horizon. It leaves a trail of smoke in the blue sky.",
            "A beautiful air balloon appears with four people aboard. The balloon drifts past you, almost directly overhead. The passengers wave and smile. You wave and smile back at them.",
            "The overall appearance of the station viewed from in front of the main entrance.",
            "You walk into the station. The colour, shape and details of the entrance hall.",
            "You approach the ticket office, go to a vacant counter and purchase your ticket.",
            "You walk to the platform and observe other passengers and the railway lines. A train arrives. You climb aboard.",
            "The overall appearance and design of the garden.",
            "The colour and shape of the bushes and shrubs.",
            "The colour and appearance of the flowers.",
            "Some birds fly down onto the lawn and start pecking for food."
        ]

        # Validate that all 32 questionnaire items are present (after stripping whitespace)
        missing_items = [col for col in questionnaire_columns if col not in df.columns]
        if missing_items:
            print(f"Error: Missing questionnaire columns: {missing_items}")
            print("Expected columns (with lengths):")
            for col in questionnaire_columns:
                print(f"  '{col}' (len={len(col)})")
            print("Actual columns (with lengths):")
            for col in df.columns:
                print(f"  '{col}' (len={len(col)})")
            return 1

        # Check if required columns exist
        required_columns = ['PROLIFIC_PID'] + questionnaire_columns
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return 1

        print(f"\nAll required columns found. Processing {len(questionnaire_columns)} VVIQ-2 items...")

        # Sample data inspection for first 5 participants and first 5 questionnaire columns
        print("\nSample data for first 5 participants and first 5 questionnaire items:")
        print(df.loc[:4, questionnaire_columns[:5]])

        # Initialize tracking variables
        initial_count = len(df)
        exclusion_log = []

        print(f"Initial participant count: {initial_count}")

        # Create working dataframe
        processed_df = df.copy()

        # Add exclusion tracking columns
        processed_df['excluded'] = False
        processed_df['exclusion_reason'] = ''

        # Exclude participants with missing PROLIFIC_PID FIRST
        missing_pid_mask = processed_df['PROLIFIC_PID'].isna() | (processed_df['PROLIFIC_PID'] == '')
        missing_pid_count = missing_pid_mask.sum()
        if missing_pid_count > 0:
            processed_df.loc[missing_pid_mask, 'excluded'] = True
            processed_df.loc[missing_pid_mask, 'exclusion_reason'] = 'Missing PROLIFIC_PID'
            exclusion_log.append(('Missing PROLIFIC_PID', missing_pid_count))
            print(f"Excluded {missing_pid_count} participants for missing PROLIFIC_PID")

        # Show sample data for first questionnaire column for debugging
        print("\nSample responses for first questionnaire item:")
        print(processed_df[questionnaire_columns[0]].head(5))

        # Extract numeric scores for each questionnaire item
        print("\nExtracting numeric scores from text responses...")

        # Vectorized extraction of numeric scores for each questionnaire item
        for i, col in enumerate(questionnaire_columns):
            item_num = f"item_{i+1:02d}"
            print(f"Processing {item_num}: {col[:50]}...")

            # Vectorized extraction
            processed_df[item_num] = processed_df[col].apply(extract_numeric_score)

            # Only flag as missing/invalid if not already excluded (e.g. for missing PID)
            missing_mask = processed_df[item_num].isna() & (~processed_df['excluded'])
            processed_df.loc[missing_mask, 'excluded'] = True
            processed_df.loc[missing_mask, 'exclusion_reason'] = 'Missing/invalid response'

            # Print some example extractions for validation
            valid_scores = processed_df[item_num].dropna().tolist()
            if valid_scores:
                print(f"  Extracted scores range: {min(valid_scores)} to {max(valid_scores)}")
                print(f"  Valid extractions: {len(valid_scores)}/{len(processed_df)}")
            else:
                print(f"  No valid scores extracted")

        # Count participants excluded for missing/invalid responses
        missing_response_count = (processed_df['exclusion_reason'] == 'Missing/invalid response').sum()
        if missing_response_count > 0:
            exclusion_log.append(('Missing/invalid responses', missing_response_count))
            print(f"Excluded {missing_response_count} participants for missing/invalid responses")

        # Check for invariant responding using vectorized apply
        print("\nChecking for invariant responding patterns...")
        def invariant_apply(row):
            if not row['excluded']:
                item_scores = [row[f"item_{i+1:02d}"] for i in range(32)]
                valid_scores = [s for s in item_scores if s is not None]
                if check_invariant_responding(valid_scores, threshold=0.9):
                    return True
            return False

        invariant_mask = processed_df.apply(invariant_apply, axis=1)
        invariant_count = invariant_mask.sum()
        processed_df.loc[invariant_mask, 'excluded'] = True
        processed_df.loc[invariant_mask, 'exclusion_reason'] = 'Invariant responding (>90% same rating)'
        if invariant_count > 0:
            exclusion_log.append(('Invariant responding', invariant_count))
            print(f"Excluded {invariant_count} participants for invariant responding")

        # Check for acquiescence bias using vectorized apply
        print("Checking for acquiescence bias (extreme responding)...")
        def acquiescence_apply(row):
            if not row['excluded']:
                item_scores = [row[f"item_{i+1:02d}"] for i in range(32)]
                valid_scores = [s for s in item_scores if s is not None]
                if check_acquiescence_bias(valid_scores, threshold=0.8):
                    return True
            return False

        acquiescence_mask = processed_df.apply(acquiescence_apply, axis=1)
        acquiescence_count = acquiescence_mask.sum()
        processed_df.loc[acquiescence_mask, 'excluded'] = True
        processed_df.loc[acquiescence_mask, 'exclusion_reason'] = 'Acquiescence bias (>80% extreme ratings)'
        if acquiescence_count > 0:
            exclusion_log.append(('Acquiescence bias', acquiescence_count))
            print(f"Excluded {acquiescence_count} participants for acquiescence bias")

        # Calculate scores for non-excluded participants
        print("\nCalculating VVIQ-2 scores...")

        # Prepare item columns
        item_cols = [f"item_{i+1:02d}" for i in range(32)]

        # Set scores to NaN for excluded participants
        processed_df.loc[processed_df['excluded'], 'total_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'face_person_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'sunrise_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'shop_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'countryside_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'driving_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'beach_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'railway_score'] = np.nan
        processed_df.loc[processed_df['excluded'], 'garden_score'] = np.nan

        # For non-excluded participants, calculate scores vectorized
        not_excluded_mask = ~processed_df['excluded']

        # Calculate total score
        processed_df.loc[not_excluded_mask, 'total_score'] = processed_df.loc[not_excluded_mask, item_cols].sum(axis=1)

        # Calculate subscale scores
        processed_df.loc[not_excluded_mask, 'face_person_score'] = processed_df.loc[not_excluded_mask, item_cols[0:4]].sum(axis=1)
        processed_df.loc[not_excluded_mask, 'sunrise_score'] = processed_df.loc[not_excluded_mask, item_cols[4:8]].sum(axis=1)
        processed_df.loc[not_excluded_mask, 'shop_score'] = processed_df.loc[not_excluded_mask, item_cols[8:12]].sum(axis=1)
        processed_df.loc[not_excluded_mask, 'countryside_score'] = processed_df.loc[not_excluded_mask, item_cols[12:16]].sum(axis=1)
        processed_df.loc[not_excluded_mask, 'driving_score'] = processed_df.loc[not_excluded_mask, item_cols[16:20]].sum(axis=1)
        processed_df.loc[not_excluded_mask, 'beach_score'] = processed_df.loc[not_excluded_mask, item_cols[20:24]].sum(axis=1)
        processed_df.loc[not_excluded_mask, 'railway_score'] = processed_df.loc[not_excluded_mask, item_cols[24:28]].sum(axis=1)
        processed_df.loc[not_excluded_mask, 'garden_score'] = processed_df.loc[not_excluded_mask, item_cols[28:32]].sum(axis=1)

        # Validate score ranges for non-excluded participants
        for idx, row in processed_df[not_excluded_mask].iterrows():
            total_score = row['total_score']
            if not (32 <= total_score <= 160):
                print(f"Warning: Total score out of range for participant {row['PROLIFIC_PID']}: {total_score}")

        # Create final output dataframe with required columns
        output_columns = [
            'PROLIFIC_PID',
            'item_01', 'item_02', 'item_03', 'item_04',
            'item_05', 'item_06', 'item_07', 'item_08',
            'item_09', 'item_10', 'item_11', 'item_12',
            'item_13', 'item_14', 'item_15', 'item_16',
            'item_17', 'item_18', 'item_19', 'item_20',
            'item_21', 'item_22', 'item_23', 'item_24',
            'item_25', 'item_26', 'item_27', 'item_28',
            'item_29', 'item_30', 'item_31', 'item_32',
            'total_score',
            'face_person_score', 'sunrise_score', 'shop_score', 'countryside_score',
            'driving_score', 'beach_score', 'railway_score', 'garden_score',
            'excluded', 'exclusion_reason'
        ]

        final_df = processed_df[output_columns].copy()

        # Print summary statistics
        total_excluded = final_df['excluded'].sum()
        remaining_participants = len(final_df) - total_excluded

        print(f"\nData processing summary:")
        print(f"Initial participants: {initial_count}")
        print(f"Total excluded: {total_excluded}")
        print(f"Remaining participants: {remaining_participants}")

        # Print score statistics for non-excluded participants
        valid_df = final_df[~final_df['excluded']]
        if len(valid_df) > 0:
            print(f"\nScore statistics for remaining participants:")
            print(f"Total score range: {valid_df['total_score'].min():.0f} - {valid_df['total_score'].max():.0f}")
            print(f"Total score mean: {valid_df['total_score'].mean():.2f}")

            # Check subscale ranges
            subscales = ['face_person_score', 'sunrise_score', 'shop_score', 'countryside_score',
                        'driving_score', 'beach_score', 'railway_score', 'garden_score']

            for subscale in subscales:
                min_score = valid_df[subscale].min()
                max_score = valid_df[subscale].max()
                if min_score < 4 or max_score > 20:
                    print(f"Warning: {subscale} out of expected range 4-20: {min_score} - {max_score}")

        # Print first 2 rows of final dataframe
        print(f"\nFinal dataframe columns:")
        print(list(final_df.columns))
        print(f"\nFirst 2 rows of final dataframe:")
        print(final_df.head(2))

        # Save output files with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save cleaned dataset
        output_file = f"outputs/VVIQ2_cleaned_{timestamp}.csv"
        final_df.to_csv(output_file, index=False)
        print(f"\nSaved cleaned dataset to: {output_file}")

        # Create and save exclusion log
        exclusion_df = pd.DataFrame(exclusion_log, columns=['exclusion_criterion', 'participants_excluded'])

        # Add remaining participants count
        remaining_counts = []
        cumulative_excluded = 0
        for _, row in exclusion_df.iterrows():
            cumulative_excluded += row['participants_excluded']
            remaining_counts.append(initial_count - cumulative_excluded)

        exclusion_df['remaining_participants'] = remaining_counts

        exclusion_log_file = f"outputs/VVIQ2_exclusion_log_{timestamp}.csv"
        exclusion_df.to_csv(exclusion_log_file, index=False)
        print(f"Saved exclusion log to: {exclusion_log_file}")

        print(f"\nExclusion log:")
        print(exclusion_df)

        print("\nFinished execution")
        return 0
        
    except Exception as e:
        print(f"Error during processing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
