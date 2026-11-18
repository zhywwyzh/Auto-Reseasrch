#!/usr/bin/env python3

import pandas as pd
import numpy as np
import os
import re
from datetime import datetime
import sys

def extract_numeric_score(text_value):
    """
    Extract numeric score (1-5) from text string containing response and score.
    
    Parameters:
    text_value (str): Text string containing response with numeric score at end
    
    Returns:
    int or None: Extracted numeric score (1-5) or None if extraction fails
    """
    if pd.isna(text_value) or text_value == '':
        return None
    
    # Convert to string if not already
    text_str = str(text_value)
    
    # Extract final digit from text
    digits = re.findall(r'\d', text_str)
    if digits:
        final_digit = int(digits[-1])
        # Validate score is within range 1-5
        if 1 <= final_digit <= 5:
            return final_digit
    
    return None

def calculate_missing_percentage(row, score_columns):
    """
    Calculate percentage of missing responses for a participant.
    
    Parameters:
    row (pd.Series): Participant data row
    score_columns (list): List of score column names
    
    Returns:
    float: Percentage of missing responses (0-100)
    """
    missing_count = sum(1 for col in score_columns if pd.isna(row[col]))
    return (missing_count / len(score_columns)) * 100

def calculate_variance(row, score_columns):
    """
    Calculate variance across all items for a participant.
    
    Parameters:
    row (pd.Series): Participant data row
    score_columns (list): List of score column names
    
    Returns:
    float: Variance across items, or None if insufficient data
    """
    scores = [row[col] for col in score_columns if not pd.isna(row[col])]
    if len(scores) < 2:
        return None
    return np.var(scores, ddof=1)

def calculate_response_set_bias(row, score_columns):
    """
    Calculate percentage of responses that are the same value.
    
    Parameters:
    row (pd.Series): Participant data row
    score_columns (list): List of score column names
    
    Returns:
    float: Maximum percentage of identical responses
    """
    scores = [row[col] for col in score_columns if not pd.isna(row[col])]
    if not scores:
        return 0
    
    # Count frequency of each response value
    value_counts = {}
    for score in scores:
        value_counts[score] = value_counts.get(score, 0) + 1
    
    # Return maximum percentage
    max_count = max(value_counts.values())
    return (max_count / len(scores)) * 100

def main():
    """
    Main function to process VVIQ2 data with cleaning and scoring.
    """
    try:
        print("Starting VVIQ2 data processing...")
        
        # Create outputs directory if it doesn't exist
        os.makedirs('outputs', exist_ok=True)
        
        # Load input data
        input_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        print(f"Loading data from: {input_file}")
        
        if not os.path.exists(input_file):
            print(f"ERROR: Input file not found: {input_file}")
            return 1
        
        df = pd.read_csv(input_file)
        # Strip whitespace from all column names to handle trailing spaces
        df.columns = df.columns.str.strip()
        print(f"Loaded data with shape: {df.shape}")
        
        # Print all columns
        print("All columns in dataset:")
        for i, col in enumerate(df.columns):
            print(f"  {i+1}: {col}")
        print(f"Data found for {len(df)} participants")
        
        # Calculate completion time if Start Date and End Date columns exist
        if 'Start Date' in df.columns and 'End Date' in df.columns:
            print("Calculating completion times...")
            df['Start Date'] = pd.to_datetime(df['Start Date'], errors='coerce')
            df['End Date'] = pd.to_datetime(df['End Date'], errors='coerce')
            df['completion_time_minutes'] = (df['End Date'] - df['Start Date']).dt.total_seconds() / 60.0
            print(f"Completion time calculated. Range: {df['completion_time_minutes'].min():.2f} - {df['completion_time_minutes'].max():.2f} minutes")
        else:
            print("Warning: Start Date and/or End Date columns not found. Time-based exclusions will be skipped.")
            df['completion_time_minutes'] = None

        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3).to_string())
        
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
        
        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        # Extract response columns (all except PROLIFIC_PID)
        response_columns = [col for col in required_columns if col != 'PROLIFIC_PID']
        print(f"Found {len(response_columns)} response columns")
        
        # Extract numeric scores from response text
        print("Extracting numeric scores from response text...")
        score_columns = []
        
        for col in response_columns:
            score_col = f"{col}_score"
            score_columns.append(score_col)
            df[score_col] = df[col].apply(extract_numeric_score)
        
        print(f"Extracted scores for {len(score_columns)} items")
        
        # Print sample of extracted scores
        print("\nSample of extracted scores (first 2 rows):")
        sample_scores = df[['PROLIFIC_PID'] + score_columns[:5]].head(2)
        print(sample_scores.to_string())
        
        # Initialize exclusion tracking
        exclusion_log = []
        df['excluded'] = False
        df['exclusion_reason'] = ''
        
        print(f"\nStarting with {len(df)} participants")
        
        # 1. Incomplete data exclusion
        print("Applying incomplete data exclusion criteria...")
        df['missing_percentage'] = df.apply(lambda row: calculate_missing_percentage(row, score_columns), axis=1)
        incomplete_mask = df['missing_percentage'] > 10  # >10% missing (>3.2 items, round up to >3 items)

        newly_excluded = incomplete_mask & ~df['excluded']
        incomplete_count = newly_excluded.sum()
        print(f"Participants with >10% missing data: {incomplete_count}")

        df.loc[newly_excluded, 'excluded'] = True
        df.loc[newly_excluded, 'exclusion_reason'] = 'incomplete_data'

        exclusion_log.append({
            'exclusion_criterion': 'incomplete_data',
            'count_excluded': incomplete_count,
            'description': 'More than 10% missing responses (>3 items out of 32)'
        })
        
        # 2. Low engagement patterns (variance=0 AND completion time <2 minutes)
        print("Applying low engagement exclusion criteria...")
        df['score_variance'] = df.apply(lambda row: calculate_variance(row, score_columns), axis=1)

        zero_variance_mask = df['score_variance'] == 0
        zero_variance_count = zero_variance_mask.sum()
        print(f"Participants with zero variance: {zero_variance_count}")

        if df['completion_time_minutes'].notna().any():
            short_time_mask_2min = df['completion_time_minutes'] < 2
            short_time_count = short_time_mask_2min.sum()
            print(f"Participants with completion time < 2 minutes: {short_time_count}")
            low_engagement_mask = zero_variance_mask & short_time_mask_2min
        else:
            print("No completion time data available - using only zero variance criterion")
            low_engagement_mask = zero_variance_mask

        newly_excluded = low_engagement_mask & ~df['excluded']
        low_engagement_count = newly_excluded.sum()
        print(f"Participants meeting low engagement criteria: {low_engagement_count}")
        df.loc[newly_excluded, 'excluded'] = True
        df.loc[newly_excluded, 'exclusion_reason'] = 'low_engagement'

        exclusion_log.append({
            'exclusion_criterion': 'low_engagement',
            'count_excluded': low_engagement_count,
            'description': 'Zero variance across all items AND completion time <2 minutes'
        })
        
        # 3. Calculate total scores for extreme score exclusion
        print("Calculating total VVIQ2 scores...")
        df['total_score_raw'] = df[score_columns].sum(axis=1, skipna=True)
        
        # Calculate sample statistics for extreme score exclusion
        valid_totals = df.loc[~df['excluded'], 'total_score_raw'].dropna()
        sample_mean = valid_totals.mean()
        sample_std = valid_totals.std()
        
        print(f"Sample mean total score: {sample_mean:.2f}")
        print(f"Sample std total score: {sample_std:.2f}")
        
        # Extreme total scores (>3SD from mean)
        extreme_threshold_upper = sample_mean + 3 * sample_std
        extreme_threshold_lower = sample_mean - 3 * sample_std
        
        extreme_mask = (df['total_score_raw'] > extreme_threshold_upper) | (df['total_score_raw'] < extreme_threshold_lower)
        newly_excluded = extreme_mask & ~df['excluded']
        extreme_count = newly_excluded.sum()
        print(f"Participants with extreme total scores: {extreme_count}")

        df.loc[newly_excluded, 'excluded'] = True
        df.loc[newly_excluded, 'exclusion_reason'] = 'extreme_scores'

        exclusion_log.append({
            'exclusion_criterion': 'extreme_scores',
            'count_excluded': extreme_count,
            'description': 'Total score >3SD from sample mean'
        })
        
        # 4. Response set bias (>90% identical responses AND completion time <3 minutes)
        print("Applying response set bias exclusion criteria...")
        df['response_set_bias'] = df.apply(lambda row: calculate_response_set_bias(row, score_columns), axis=1)

        high_bias_mask = df['response_set_bias'] > 90
        high_bias_count = high_bias_mask.sum()
        print(f"Participants with >90% identical responses: {high_bias_count}")

        if df['completion_time_minutes'].notna().any():
            short_time_mask_3min = df['completion_time_minutes'] < 3
            short_time_3min_count = short_time_mask_3min.sum()
            print(f"Participants with completion time < 3 minutes: {short_time_3min_count}")
            response_bias_mask = high_bias_mask & short_time_mask_3min
        else:
            print("No completion time data available - using only response bias criterion")
            response_bias_mask = high_bias_mask

        newly_excluded = response_bias_mask & ~df['excluded']
        response_bias_count = newly_excluded.sum()
        print(f"Participants meeting response set bias criteria: {response_bias_count}")

        df.loc[newly_excluded, 'excluded'] = True
        df.loc[newly_excluded, 'exclusion_reason'] = 'response_set_bias'

        exclusion_log.append({
            'exclusion_criterion': 'response_set_bias',
            'count_excluded': response_bias_count,
            'description': 'More than 90% responses are identical value AND completion time <3 minutes'
        })
        
        # 5. Impossible completion time (<1 minute)
        print("Applying impossible completion time exclusion criteria...")
        if df['completion_time_minutes'].notna().any():
            impossible_time_mask = df['completion_time_minutes'] < 1
            newly_excluded = impossible_time_mask & ~df['excluded']
            impossible_time_count = newly_excluded.sum()
            print(f"Participants with completion time < 1 minute: {impossible_time_count}")

            df.loc[newly_excluded, 'excluded'] = True
            df.loc[newly_excluded, 'exclusion_reason'] = 'impossible_completion_time'

            exclusion_log.append({
                'exclusion_criterion': 'impossible_completion_time',
                'count_excluded': impossible_time_count,
                'description': 'Completion time less than 1 minute'
            })
        else:
            print("No completion time data available - skipping impossible completion time exclusion")

        # 6. Technical issues (missing participant IDs)
        print("Checking for technical issues...")
        technical_mask = df['PROLIFIC_PID'].isna() | (df['PROLIFIC_PID'] == '')
        newly_excluded = technical_mask & ~df['excluded']
        technical_count = newly_excluded.sum()
        print(f"Participants with missing IDs: {technical_count}")

        df.loc[newly_excluded, 'excluded'] = True
        df.loc[newly_excluded, 'exclusion_reason'] = 'technical_issues'

        exclusion_log.append({
            'exclusion_criterion': 'technical_issues',
            'count_excluded': technical_count,
            'description': 'Missing or corrupted participant ID'
        })
        
        # Calculate final scores for non-excluded participants
        print("Calculating final VVIQ2 scores...")
        
        # Total score (sum of all 32 items)
        df['total_score'] = df[score_columns].sum(axis=1, skipna=False)
        
        # Subscale scores (4 items each)
        # Familiar person (items 1-4)
        familiar_person_cols = score_columns[0:4]
        df['familiar_person_score'] = df[familiar_person_cols].sum(axis=1, skipna=False)
        
        # Sunrise (items 5-8)
        sunrise_cols = score_columns[4:8]
        df['sunrise_score'] = df[sunrise_cols].sum(axis=1, skipna=False)
        
        # Shop front (items 9-12)
        shop_front_cols = score_columns[8:12]
        df['shop_front_score'] = df[shop_front_cols].sum(axis=1, skipna=False)
        
        # Countryside scene (items 13-16)
        countryside_cols = score_columns[12:16]
        df['countryside_score'] = df[countryside_cols].sum(axis=1, skipna=False)
        
        # Driving scenario (items 17-20)
        driving_cols = score_columns[16:20]
        df['driving_score'] = df[driving_cols].sum(axis=1, skipna=False)
        
        # Beach scene (items 21-24)
        beach_cols = score_columns[20:24]
        df['beach_score'] = df[beach_cols].sum(axis=1, skipna=False)
        
        # Railway station (items 25-28)
        railway_station_cols = score_columns[24:28]
        df['railway_station_score'] = df[railway_station_cols].sum(axis=1, skipna=False)
        
        # Garden scene (items 29-32)
        garden_cols = score_columns[28:32]
        df['garden_score'] = df[garden_cols].sum(axis=1, skipna=False)
        
        print("Subscale score ranges:")
        print(f"  Familiar person: {familiar_person_cols}")
        print(f"  Sunrise: {sunrise_cols}")
        print(f"  Shop front: {shop_front_cols}")
        print(f"  Countryside: {countryside_cols}")
        print(f"  Driving: {driving_cols}")
        print(f"  Beach: {beach_cols}")
        print(f"  Railway station: {railway_station_cols}")
        print(f"  Garden: {garden_cols}")
        
        # Validate score ranges
        print("Validating score ranges...")
        valid_participants = df[~df['excluded']].copy()
        
        print(f"Valid participants after exclusions: {len(valid_participants)}")
        print(f"Total excluded: {df['excluded'].sum()}")
        
        # Print exclusion summary
        print("\nExclusion summary:")
        for criterion in exclusion_log:
            print(f"  {criterion['exclusion_criterion']}: {criterion['count_excluded']} participants")
        
        # Print score statistics for valid participants
        if len(valid_participants) > 0:
            print("\nScore statistics for valid participants:")
            print(f"Total score range: {valid_participants['total_score'].min():.0f} - {valid_participants['total_score'].max():.0f}")
            print(f"Total score mean: {valid_participants['total_score'].mean():.2f}")
            
            subscale_cols = ['familiar_person_score', 'sunrise_score', 'shop_front_score', 
                           'countryside_score', 'driving_score', 'beach_score', 
                           'railway_station_score', 'garden_score']
            
            for subscale in subscale_cols:
                scores = valid_participants[subscale]
                print(f"{subscale}: {scores.min():.0f} - {scores.max():.0f} (mean: {scores.mean():.2f})")
        
        # Prepare output data
        output_columns = [
            'PROLIFIC_PID', 'total_score', 'familiar_person_score', 'sunrise_score',
            'shop_front_score', 'countryside_score', 'driving_score', 'beach_score',
            'railway_station_score', 'garden_score', 'excluded', 'exclusion_reason'
        ]
        
        output_df = df[output_columns].copy()
        
        # Convert boolean to proper format
        output_df['excluded'] = output_df['excluded'].astype(bool)
        
        # Convert scores to integers for non-excluded participants
        score_cols = ['total_score', 'familiar_person_score', 'sunrise_score', 'shop_front_score',
                     'countryside_score', 'driving_score', 'beach_score', 'railway_station_score', 'garden_score']
        
        for col in score_cols:
            output_df.loc[~output_df['excluded'], col] = output_df.loc[~output_df['excluded'], col].astype('Int64')
        
        # Print final output sample
        print("\nFinal output data (first 2 rows):")
        print(output_df.head(2).to_string())
        
        # Save cleaned scores
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'outputs/VVIQ2_cleaned_scores_{timestamp}.csv'
        output_df.to_csv(output_file, index=False)
        print(f"Saved cleaned scores to: {output_file}")
        
        # Save exclusion log
        exclusion_df = pd.DataFrame(exclusion_log)
        exclusion_file = f'outputs/VVIQ2_exclusion_log_{timestamp}.csv'
        exclusion_df.to_csv(exclusion_file, index=False)
        print(f"Saved exclusion log to: {exclusion_file}")
        
        # Print exclusion log
        print("\nExclusion log:")
        print(exclusion_df.to_string(index=False))
        
        print(f"\n--- Data Cleaning Summary ---")
        print(f"Data found for {len(df)} participants")
        for item in exclusion_log:
            if item['count_excluded'] > 0:
                print(f"{item['count_excluded']} participants were removed due to: {item['description']}")
        print(f"Final dataset: {len(df) - df['excluded'].sum()} participants")
        print("---------------------------")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
