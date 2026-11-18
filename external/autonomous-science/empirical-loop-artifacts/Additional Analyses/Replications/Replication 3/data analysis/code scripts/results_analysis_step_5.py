#!/usr/bin/env python3
"""
VVIQ2 Data Processing Script

This script processes the Vividness of Visual Imagery Questionnaire-2 (VVIQ2) data,
applying exclusion criteria and calculating total and subscale scores.
"""

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import sys

def extract_numeric_score(response_text):
    """
    Extract the final numeric score (1-5) from a response text string.
    
    Parameters:
    -----------
    response_text : str or any
        The response text that should end with a numeric score
        
    Returns:
    --------
    int or None
        The extracted numeric score (1-5) or None if extraction fails
    """
    if pd.isna(response_text):
        return None
    
    # Convert to string if not already
    text = str(response_text).strip()
    
    # Extract the last digit from the string
    digits = re.findall(r'\d', text)
    if digits:
        last_digit = int(digits[-1])
        # Validate it's in the expected range
        if 1 <= last_digit <= 5:
            return last_digit
    
    return None

def identify_reverse_coded_items():
    """
    Identify items that require reverse coding based on VVIQ2 specification.
    
    Returns:
    --------
    list
        List of column indices (0-based) that require reverse coding
    """
    # Based on standard VVIQ2, typically no items are reverse coded
    # All items are scored in the same direction (higher = more vivid)
    return []

def reverse_code_score(score):
    """
    Apply reverse coding transformation to a score.
    
    Parameters:
    -----------
    score : int
        Original score (1-5)
        
    Returns:
    --------
    int
        Reverse coded score (6 - original_score)
    """
    if pd.isna(score):
        return score
    return 6 - score

def check_invariant_responses(scores):
    """
    Check if all responses are identical (invariant response pattern).
    
    Parameters:
    -----------
    scores : list or array
        List of numeric scores
        
    Returns:
    --------
    bool
        True if all non-missing scores are identical
    """
    valid_scores = [s for s in scores if not pd.isna(s)]
    if len(valid_scores) <= 1:
        return False
    return len(set(valid_scores)) == 1

def calculate_endpoint_percentage(scores):
    """
    Calculate percentage of responses using only scale endpoints (1 or 5).
    
    Parameters:
    -----------
    scores : list or array
        List of numeric scores
        
    Returns:
    --------
    float
        Percentage of responses using endpoints (0-100)
    """
    valid_scores = [s for s in scores if not pd.isna(s)]
    if len(valid_scores) == 0:
        return 0.0
    
    endpoint_count = sum(1 for s in valid_scores if s in [1, 5])
    return (endpoint_count / len(valid_scores)) * 100

def main():
    """
    Main function to process VVIQ2 data.
    """
    try:
        print("Starting VVIQ2 data processing...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Define input file path
        input_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        
        print(f"Reading input file: {input_file}")
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"ERROR: Input file not found: {input_file}")
            return 1
        
        # Read the CSV file
        try:
            df = pd.read_csv(input_file)
            df.columns = df.columns.str.strip()  # Clean column names first
            print(f"Successfully loaded data with {len(df)} rows and {len(df.columns)} columns")
        except Exception as e:
            print(f"ERROR: Failed to read CSV file: {e}")
            return 1

        # Define required columns
        required_columns = [
            'PROLIFIC_PID',
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

        # Print all columns
        print("\nAll columns in the dataset:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")

        # Print sample PROLIFIC_PID values for verification
        print(f"Sample PROLIFIC_PID values: {df['PROLIFIC_PID'].head(3).tolist()}")
        print(f"PROLIFIC_PID - Non-null count: {df['PROLIFIC_PID'].notna().sum()}/{len(df)}")
        print(f"PROLIFIC_PID - Unique values: {df['PROLIFIC_PID'].nunique()}")

        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3).to_string())

        # Check for missing required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1

        print(f"\nAll {len(required_columns)} required columns found in dataset")

        # Extract VVIQ2 question columns (exclude PROLIFIC_PID)
        vviq_columns = required_columns[1:]  # Skip PROLIFIC_PID

        print(f"\nProcessing {len(vviq_columns)} VVIQ2 items...")

        # Extract numeric scores from response text
        print("Extracting numeric scores from response text...")
        score_data = {}

        for col in vviq_columns:
            print(f"Processing column: {col}")
            scores = []
            for idx, response in enumerate(df[col]):
                score = extract_numeric_score(response)
                scores.append(score)
                if idx < 3:  # Print first few extractions for verification
                    print(f"  Row {idx}: '{response}' -> {score}")
            score_data[col] = scores

        # Create a new dataframe with extracted scores
        scores_df = pd.DataFrame(score_data)
        # Add type safety for participant ID conversion
        scores_df['PROLIFIC_PID'] = df['PROLIFIC_PID'].fillna('').astype(str)

        # Calculate completion time
        print("Calculating completion time...")
        df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
        df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')
        completion_time_seconds = (df['End Date'] - df['Start Date']).dt.total_seconds()
        scores_df['completion_time_seconds'] = completion_time_seconds
        print(f"Completion time calculated. Range: {completion_time_seconds.min():.1f} - {completion_time_seconds.max():.1f} seconds")
        
        print(f"\nExtracted scores dataframe shape: {scores_df.shape}")
        print("First 2 rows of extracted scores:")
        print(scores_df.head(2).to_string())
        
        # Validate extracted scores
        print("\nValidating extracted scores...")
        invalid_scores = 0
        for col in vviq_columns:
            col_invalid = scores_df[col].apply(lambda x: not pd.isna(x) and (x < 1 or x > 5)).sum()
            invalid_scores += col_invalid
            if col_invalid > 0:
                print(f"  {col}: {col_invalid} invalid scores")
        
        print(f"Total invalid scores found: {invalid_scores}")
        
        # Apply completeness exclusions
        print("\nApplying completeness exclusions...")
        
        # Count missing responses per participant
        missing_counts = scores_df[vviq_columns].isnull().sum(axis=1)
        complete_data = missing_counts == 0
        
        print(f"Participants with complete data: {complete_data.sum()}/{len(scores_df)}")
        print(f"Participants with missing data: {(~complete_data).sum()}")
        
        # Initialize exclusion tracking
        exclusions = []
        scores_df['excluded'] = False
        scores_df['exclusion_reason'] = ''
        
        # Exclude participants with missing responses
        missing_mask = ~complete_data
        scores_df.loc[missing_mask, 'excluded'] = True
        scores_df.loc[missing_mask, 'exclusion_reason'] = 'Missing responses'
        
        exclusions.append({
            'exclusion_criteria': 'Missing responses',
            'total_excluded': missing_mask.sum()
        })
        
        print(f"Excluded {missing_mask.sum()} participants for missing responses")
        
        # Apply response quality exclusions using vectorized operations
        print("\nApplying response quality exclusions...")
        remaining_mask = ~scores_df['excluded']
        print(f"Participants remaining for quality checks: {remaining_mask.sum()}")

        # Criterion 1: Invariant responses AND completion time < 90s
        print("Checking for invariant responses with completion time < 90s...")
        is_invariant = scores_df.loc[remaining_mask, vviq_columns].nunique(axis=1, dropna=True) == 1
        fast_completion = scores_df.loc[remaining_mask, 'completion_time_seconds'] < 90
        invariant_fast_mask = is_invariant & fast_completion

        # Apply criterion 1 exclusions
        invariant_indices = scores_df[remaining_mask][invariant_fast_mask].index
        scores_df.loc[invariant_indices, 'excluded'] = True
        scores_df.loc[invariant_indices, 'exclusion_reason'] = 'Invariant responses and completion time < 90s'
        print(f"Excluded {len(invariant_indices)} participants for invariant responses with fast completion")

        exclusions.append({
            'exclusion_criteria': 'Invariant responses and completion time < 90s',
            'total_excluded': len(invariant_indices)
        })

        # Criterion 2: >90% endpoint usage AND completion time < 60s
        print("Checking for >90% endpoint usage with completion time < 60s...")
        remaining_mask = ~scores_df['excluded']  # Update mask after first exclusion
        endpoint_counts = scores_df.loc[remaining_mask, vviq_columns].isin([1, 5]).sum(axis=1)
        valid_counts = scores_df.loc[remaining_mask, vviq_columns].notna().sum(axis=1)
        endpoint_pct = np.where(valid_counts > 0, (endpoint_counts / valid_counts) * 100, 0)
        very_fast_completion = scores_df.loc[remaining_mask, 'completion_time_seconds'] < 60
        endpoint_fast_mask = (endpoint_pct > 90) & very_fast_completion

        # Apply criterion 2 exclusions
        endpoint_indices = scores_df[remaining_mask][endpoint_fast_mask].index
        scores_df.loc[endpoint_indices, 'excluded'] = True
        scores_df.loc[endpoint_indices, 'exclusion_reason'] = '>90% endpoint responses and completion time < 60s'
        print(f"Excluded {len(endpoint_indices)} participants for >90% endpoint usage with very fast completion")

        exclusions.append({
            'exclusion_criteria': '>90% endpoint responses and completion time < 60s',
            'total_excluded': len(endpoint_indices)
        })
        
        # Apply reverse-coding transformations
        print("\nApplying reverse-coding transformations...")
        reverse_coded_items = identify_reverse_coded_items()
        
        if reverse_coded_items:
            print(f"Reverse coding {len(reverse_coded_items)} items...")
            for item_idx in reverse_coded_items:
                col = vviq_columns[item_idx]
                scores_df[col] = scores_df[col].apply(reverse_code_score)
                print(f"  Reverse coded: {col}")
        else:
            print("No items require reverse coding for VVIQ2")
        
        # Calculate VVIQ2 scores for non-excluded participants
        print("\nCalculating VVIQ2 scores...")
        
        final_data = []
        
        for idx, row in scores_df.iterrows():
            if row['excluded']:
                # Add excluded participant with null scores
                final_data.append({
                    'PROLIFIC_PID': row['PROLIFIC_PID'],
                    'total_score': None,
                    'familiar_person_score': None,
                    'sunrise_score': None,
                    'shop_front_score': None,
                    'countryside_scene_score': None,
                    'driving_scenario_score': None,
                    'beach_scene_score': None,
                    'railway_station_score': None,
                    'garden_scene_score': None,
                    'excluded': True,
                    'exclusion_reason': row['exclusion_reason']
                })
            else:
                # Calculate scores for included participants
                item_scores = [row[col] for col in vviq_columns]
                
                # Check if all scores are valid
                if all(not pd.isna(score) for score in item_scores):
                    # Calculate total score (sum of all 32 items)
                    total_score = sum(item_scores)
                    
                    # Calculate subscale scores (4 items each)
                    familiar_person_score = sum(item_scores[0:4])    # items 1-4
                    sunrise_score = sum(item_scores[4:8])            # items 5-8
                    shop_front_score = sum(item_scores[8:12])        # items 9-12
                    countryside_scene_score = sum(item_scores[12:16]) # items 13-16
                    driving_scenario_score = sum(item_scores[16:20])  # items 17-20
                    beach_scene_score = sum(item_scores[20:24])      # items 21-24
                    railway_station_score = sum(item_scores[24:28])  # items 25-28
                    garden_scene_score = sum(item_scores[28:32])     # items 29-32
                    
                    final_data.append({
                        'PROLIFIC_PID': row['PROLIFIC_PID'],
                        'total_score': total_score,
                        'familiar_person_score': familiar_person_score,
                        'sunrise_score': sunrise_score,
                        'shop_front_score': shop_front_score,
                        'countryside_scene_score': countryside_scene_score,
                        'driving_scenario_score': driving_scenario_score,
                        'beach_scene_score': beach_scene_score,
                        'railway_station_score': railway_station_score,
                        'garden_scene_score': garden_scene_score,
                        'excluded': False,
                        'exclusion_reason': ''
                    })
                else:
                    # Should not happen if exclusions worked correctly
                    final_data.append({
                        'PROLIFIC_PID': row['PROLIFIC_PID'],
                        'total_score': None,
                        'familiar_person_score': None,
                        'sunrise_score': None,
                        'shop_front_score': None,
                        'countryside_scene_score': None,
                        'driving_scenario_score': None,
                        'beach_scene_score': None,
                        'railway_station_score': None,
                        'garden_scene_score': None,
                        'excluded': True,
                        'exclusion_reason': 'Invalid scores detected'
                    })
        
        # Create final dataframe
        final_df = pd.DataFrame(final_data)
        
        print(f"Final dataset shape: {final_df.shape}")
        print("First 2 rows of final data:")
        print(final_df.head(2).to_string())
        print(f"Unique PROLIFIC_PIDs: {final_df['PROLIFIC_PID'].nunique()}")
        print(f"Sample PROLIFIC_PIDs: {final_df['PROLIFIC_PID'].head(3).tolist()}")

        # Additional validation for participant IDs
        print(f"Validating unique participant IDs in final data...")
        unique_ids = final_df['PROLIFIC_PID'].nunique()
        total_rows = len(final_df)
        print(f"Number of unique PROLIFIC_PIDs: {unique_ids} (out of {total_rows} rows)")
        if unique_ids != total_rows:
            print(f"WARNING: Number of unique participant IDs ({unique_ids}) does not match number of rows ({total_rows})")

        # Data validation
        print("\nPerforming data validation...")
        
        included_data = final_df[~final_df['excluded']]
        print(f"Included participants: {len(included_data)}")
        print(f"Excluded participants: {len(final_df) - len(included_data)}")
        
        if len(included_data) > 0:
            # Validate total scores
            total_scores = included_data['total_score'].dropna()
            if len(total_scores) > 0:
                print(f"Total score range: {total_scores.min()} - {total_scores.max()} (expected: 32-160)")
                print(f"Mean total score: {total_scores.mean():.2f}")
                
                # Check if scores are in valid range
                invalid_total = total_scores[(total_scores < 32) | (total_scores > 160)]
                if len(invalid_total) > 0:
                    print(f"WARNING: {len(invalid_total)} total scores outside valid range")
            
            # Validate subscale scores
            subscale_cols = ['familiar_person_score', 'sunrise_score', 'shop_front_score', 
                           'countryside_scene_score', 'driving_scenario_score', 'beach_scene_score',
                           'railway_station_score', 'garden_scene_score']
            
            for col in subscale_cols:
                subscale_scores = included_data[col].dropna()
                if len(subscale_scores) > 0:
                    print(f"{col} range: {subscale_scores.min()} - {subscale_scores.max()} (expected: 4-20)")
                    invalid_subscale = subscale_scores[(subscale_scores < 4) | (subscale_scores > 20)]
                    if len(invalid_subscale) > 0:
                        print(f"WARNING: {len(invalid_subscale)} {col} scores outside valid range")
        
        # Generate timestamp for output files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save exclusion log
        exclusion_log_file = f'outputs/VVIQ2_exclusion_log_{timestamp}.csv'
        exclusions_df = pd.DataFrame(exclusions)
        exclusions_df.to_csv(exclusion_log_file, index=False)
        print(f"\nSaved exclusion log to: {exclusion_log_file}")
        print("Exclusion summary:")
        print(exclusions_df.to_string(index=False))
        
        # Save cleaned data
        cleaned_data_file = f'outputs/VVIQ2_cleaned_data_{timestamp}.csv'
        final_df.to_csv(cleaned_data_file, index=False)
        print(f"\nSaved cleaned data to: {cleaned_data_file}")
        
        print(f"\nFinal summary:")
        print(f"Total participants processed: {len(final_df)}")
        print(f"Participants included: {len(included_data)}")
        print(f"Participants excluded: {len(final_df) - len(included_data)}")
        print(f"Exclusion rate: {((len(final_df) - len(included_data)) / len(final_df) * 100):.1f}%")
        print(f"Data found for {len(df)} participants")
        print(f"Final dataset: {len(included_data)} participants included")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
