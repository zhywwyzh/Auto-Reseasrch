import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
import sys

def extract_numeric_score(text):
    """
    Extract numeric score (1-5) from response text using regex.
    
    Parameters:
    text (str): Response text containing numeric score
    
    Returns:
    int or None: Extracted numeric score between 1-5, or None if not found
    """
    if pd.isna(text) or text == '':
        return None
    
    # Convert to string if not already
    text_str = str(text)
    
    # Look for numbers 1-5 in the text
    matches = re.findall(r'\b[1-5]\b', text_str)
    
    if matches:
        # Return the first valid score found
        return int(matches[0])
    else:
        return None

def validate_score_range(score):
    """
    Validate that score is within 1-5 range.
    
    Parameters:
    score (int or None): Score to validate
    
    Returns:
    bool: True if score is valid (1-5), False otherwise
    """
    if score is None:
        return False
    return 1 <= score <= 5

def calculate_missing_percentage(row, total_items=32):
    """
    Calculate percentage of missing responses for a participant.
    
    Parameters:
    row (pd.Series): Row containing participant responses
    total_items (int): Total number of VVIQ2 items
    
    Returns:
    float: Percentage of missing responses (0-100)
    """
    missing_count = sum(1 for score in row if pd.isna(score) or score is None)
    return (missing_count / total_items) * 100

def has_identical_ratings(row):
    """
    Check if participant provided identical ratings across all items.
    
    Parameters:
    row (pd.Series): Row containing participant responses
    
    Returns:
    bool: True if all non-missing responses are identical
    """
    valid_scores = [score for score in row if not pd.isna(score) and score is not None]
    if len(valid_scores) <= 1:
        return False
    return len(set(valid_scores)) == 1

def calculate_extreme_response_percentage(row):
    """
    Calculate percentage of extreme responses (1s and 5s).
    
    Parameters:
    row (pd.Series): Row containing participant responses
    
    Returns:
    float: Percentage of extreme responses (0-100)
    """
    valid_scores = [score for score in row if not pd.isna(score) and score is not None]
    if len(valid_scores) == 0:
        return 0
    
    extreme_count = sum(1 for score in valid_scores if score in [1, 5])
    return (extreme_count / len(valid_scores)) * 100

def calculate_coefficient_of_variation(row):
    """
    Calculate coefficient of variation for participant responses.
    
    Parameters:
    row (pd.Series): Row containing participant responses
    
    Returns:
    float: Coefficient of variation (std/mean)
    """
    valid_scores = [score for score in row if not pd.isna(score) and score is not None]
    if len(valid_scores) <= 1:
        return 0
    
    mean_score = np.mean(valid_scores)
    std_score = np.std(valid_scores)
    
    if mean_score == 0:
        return 0
    
    return std_score / mean_score

def main():
    """
    Main function to process VVIQ2 data and apply exclusion criteria.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 data processing...")
        
        # Define input file path
        input_file = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
        
        print(f"Reading input file: {input_file}")
        
        # Check if input file exists
        if not os.path.exists(input_file):
            print(f"ERROR: Input file not found: {input_file}")
            return 1
        
        # Read the CSV file
        df = pd.read_csv(input_file)
        df.columns = df.columns.str.strip()  # Strip whitespace from column names
        
        print(f"Successfully loaded data with {len(df)} rows and {len(df.columns)} columns")
        print("All columns:")
        print(list(df.columns))
        print("\nFirst 3 rows:")
        print(df.head(3))
        
        # Define VVIQ2 item columns in order
        vviq2_columns = [
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
        
        print(f"\nExpected {len(vviq2_columns)} VVIQ2 item columns")
        
        # Check if required columns exist
        missing_columns = []
        required_columns = ["PROLIFIC_PID", "Start Date", "End Date"] + vviq2_columns
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            return 1
        
        print("All required columns found in dataset")
        
        # Extract numeric scores from response text
        print("\nExtracting numeric scores from response text...")
        
        score_columns = []
        for i, col in enumerate(vviq2_columns):
            score_col = f"item_{i+1}_score"
            score_columns.append(score_col)
            df[score_col] = df[col].apply(extract_numeric_score)
            
            # Print sample of extracted scores for first few items
            if i < 3:
                print(f"\nItem {i+1} - Original responses (first 3):")
                print(df[col].head(3).tolist())
                print(f"Item {i+1} - Extracted scores (first 3):")
                print(df[score_col].head(3).tolist())
        
        print(f"\nExtracted scores for all {len(vviq2_columns)} items")
        
        # Calculate completion time in seconds
        print("Calculating completion times...")
        df['completion_seconds'] = (pd.to_datetime(df['End Date']) - pd.to_datetime(df['Start Date'])).dt.total_seconds()
        
        # Create dataframe with participant ID, scores, and completion time
        score_df = df[["PROLIFIC_PID"] + score_columns + ['completion_seconds']].copy()
        
        print(f"\nScore dataframe created with {len(score_df)} participants")
        print("Score dataframe columns:")
        print(list(score_df.columns))
        print("\nFirst 2 rows of score data:")
        print(score_df.head(2))
        
        # Initialize exclusion tracking
        exclusion_counts = {
            "missing_data": 0,
            "invalid_response_patterns": 0,
            "out_of_range_responses": 0,
            "extreme_responding": 0,
            "incomplete_data": 0
        }
        
        # Apply exclusion criteria in cascaded manner
        print("\nApplying exclusion criteria in cascaded manner...")
        
        # Start with all participants
        remaining_df = score_df.copy()
        all_excluded = []
        
        # Step 1: Exclude for missing data
        print("Step 1: Checking for missing data (>10% missing responses)...")
        step1_excluded = []
        for idx, row in remaining_df.iterrows():
            participant_id = row["PROLIFIC_PID"]
            scores = row[score_columns]
            missing_pct = calculate_missing_percentage(scores)
            if missing_pct > 10:
                step1_excluded.append({
                    "participant_id": participant_id,
                    "exclusion_reason": "missing_data"
                })
        
        exclusion_counts["missing_data"] = len(step1_excluded)
        all_excluded.extend(step1_excluded)
        excluded_ids = [p["participant_id"] for p in step1_excluded]
        remaining_df = remaining_df[~remaining_df["PROLIFIC_PID"].isin(excluded_ids)]
        print(f"Excluded {len(step1_excluded)} participants for missing data. Remaining: {len(remaining_df)}")
        
        # Step 2: Exclude for out-of-range responses
        print("Step 2: Checking for out-of-range responses...")
        step2_excluded = []
        for idx, row in remaining_df.iterrows():
            participant_id = row["PROLIFIC_PID"]
            scores = row[score_columns]
            has_invalid_range = False
            for score in scores:
                if score is not None and not pd.isna(score):
                    if not validate_score_range(score):
                        has_invalid_range = True
                        break
            if has_invalid_range:
                step2_excluded.append({
                    "participant_id": participant_id,
                    "exclusion_reason": "out_of_range_responses"
                })
        
        exclusion_counts["out_of_range_responses"] = len(step2_excluded)
        all_excluded.extend(step2_excluded)
        excluded_ids = [p["participant_id"] for p in step2_excluded]
        remaining_df = remaining_df[~remaining_df["PROLIFIC_PID"].isin(excluded_ids)]
        print(f"Excluded {len(step2_excluded)} participants for out-of-range responses. Remaining: {len(remaining_df)}")
        
        # Step 3: Exclude for incomplete data
        print("Step 3: Checking for incomplete data...")
        step3_excluded = []
        for idx, row in remaining_df.iterrows():
            participant_id = row["PROLIFIC_PID"]
            scores = row[score_columns]
            all_missing = all(pd.isna(score) or score is None for score in scores)
            if all_missing:
                step3_excluded.append({
                    "participant_id": participant_id,
                    "exclusion_reason": "incomplete_data"
                })
        
        exclusion_counts["incomplete_data"] = len(step3_excluded)
        all_excluded.extend(step3_excluded)
        excluded_ids = [p["participant_id"] for p in step3_excluded]
        remaining_df = remaining_df[~remaining_df["PROLIFIC_PID"].isin(excluded_ids)]
        print(f"Excluded {len(step3_excluded)} participants for incomplete data. Remaining: {len(remaining_df)}")
        
        # Step 4: Exclude for invalid response patterns (identical ratings AND fast completion)
        print("Step 4: Checking for invalid response patterns...")
        step4_excluded = []
        for idx, row in remaining_df.iterrows():
            participant_id = row["PROLIFIC_PID"]
            scores = row[score_columns]
            completion_time = row["completion_seconds"]
            if has_identical_ratings(scores) and completion_time < 120:
                step4_excluded.append({
                    "participant_id": participant_id,
                    "exclusion_reason": "invalid_response_patterns"
                })
        
        exclusion_counts["invalid_response_patterns"] = len(step4_excluded)
        all_excluded.extend(step4_excluded)
        excluded_ids = [p["participant_id"] for p in step4_excluded]
        remaining_df = remaining_df[~remaining_df["PROLIFIC_PID"].isin(excluded_ids)]
        print(f"Excluded {len(step4_excluded)} participants for invalid response patterns. Remaining: {len(remaining_df)}")
        
        # Step 5: Exclude for extreme responding
        print("Step 5: Checking for extreme responding...")
        step5_excluded = []
        for idx, row in remaining_df.iterrows():
            participant_id = row["PROLIFIC_PID"]
            scores = row[score_columns]
            extreme_pct = calculate_extreme_response_percentage(scores)
            cv = calculate_coefficient_of_variation(scores)
            if extreme_pct > 90 and cv < 0.3:
                step5_excluded.append({
                    "participant_id": participant_id,
                    "exclusion_reason": "extreme_responding"
                })
        
        exclusion_counts["extreme_responding"] = len(step5_excluded)
        all_excluded.extend(step5_excluded)
        excluded_ids = [p["participant_id"] for p in step5_excluded]
        remaining_df = remaining_df[~remaining_df["PROLIFIC_PID"].isin(excluded_ids)]
        print(f"Excluded {len(step5_excluded)} participants for extreme responding. Remaining: {len(remaining_df)}")
        
        excluded_participants = all_excluded
        clean_df = remaining_df
        
        print(f"\nCleaned dataset has {len(clean_df)} participants")
        
        # Calculate VVIQ2 scores for remaining participants
        print("\nCalculating VVIQ2 scores...")
        
        results = []
        
        for i, (idx, row) in enumerate(clean_df.iterrows()):
            participant_id = row["PROLIFIC_PID"]
            scores = [row[col] for col in score_columns]

            # Remove any None/NaN values for calculation
            valid_scores = [score for score in scores if not pd.isna(score) and score is not None]

            print(f"\nProcessing participant {i+1}/{len(clean_df)}: {participant_id}")
            print(f"Valid scores: {len(valid_scores)}/{len(scores)}")

            # Calculate total score using nansum (no imputation)
            total_score = np.nansum(scores)

            # Calculate subscale scores using nansum
            subscales = {
                "familiar_person_subscale": np.nansum(scores[0:4]),
                "sunrise_subscale": np.nansum(scores[4:8]),
                "shop_front_subscale": np.nansum(scores[8:12]),
                "countryside_subscale": np.nansum(scores[12:16]),
                "driving_subscale": np.nansum(scores[16:20]),
                "beach_subscale": np.nansum(scores[20:24]),
                "railway_station_subscale": np.nansum(scores[24:28]),
                "garden_subscale": np.nansum(scores[28:32])
            }

            result = {
                "participantId": participant_id,
                "total_VVIQ2_score": total_score,
                "excluded_participant": False,
                "exclusion_reason": ""
            }
            result.update(subscales)

            results.append(result)
        
        # Add excluded participants to results
        for excluded_p in excluded_participants:
            result = {
                "participantId": excluded_p["participant_id"],
                "total_VVIQ2_score": np.nan,
                "familiar_person_subscale": np.nan,
                "sunrise_subscale": np.nan,
                "shop_front_subscale": np.nan,
                "countryside_subscale": np.nan,
                "driving_subscale": np.nan,
                "beach_subscale": np.nan,
                "railway_station_subscale": np.nan,
                "garden_subscale": np.nan,
                "excluded_participant": True,
                "exclusion_reason": excluded_p["exclusion_reason"]
            }
            results.append(result)
        
        print(f"\nFinal results include {len(results)} participants")
        print(f"Valid scores calculated for {len([r for r in results if not r['excluded_participant']])} participants")
        
        # Print final summary
        print("\n" + "="*50)
        print("FINAL SUMMARY")
        print("="*50)
        print(f"Initial participants: {len(df)}")
        print(f"Total excluded: {sum(exclusion_counts.values())}")
        for criterion, count in exclusion_counts.items():
            print(f"  - {criterion}: {count}")
        print(f"Final valid participants: {len([r for r in results if not r['excluded_participant']])}")
        print("="*50)

        # Create output dataframe
        output_df = pd.DataFrame(results)
        
        print("\nOutput dataframe columns:")
        print(list(output_df.columns))
        print("\nFirst 2 rows of output data:")
        print(output_df.head(2))
        
        # Create outputs directory if it doesn't exist
        os.makedirs("outputs", exist_ok=True)
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save main output file
        output_filename = f"outputs/VVIQ2_cleaned_scores_{timestamp}.csv"
        output_df.to_csv(output_filename, index=False)
        print(f"\nSaved cleaned scores to: {output_filename}")
        
        # Create exclusion log
        exclusion_log = []
        exclusion_log.append({
            "exclusion_criteria": "missing_data",
            "number_excluded": exclusion_counts["missing_data"],
            "description": "Participants with >10% missing responses (>3.2 items out of 32)"
        })
        exclusion_log.append({
            "exclusion_criteria": "invalid_response_patterns",
            "number_excluded": exclusion_counts["invalid_response_patterns"],
            "description": "Participants who provide identical ratings across all 32 items AND complete the questionnaire in <120 seconds"
        })
        exclusion_log.append({
            "exclusion_criteria": "out_of_range_responses",
            "number_excluded": exclusion_counts["out_of_range_responses"],
            "description": "Participants with any responses outside the 1-5 scale range"
        })
        exclusion_log.append({
            "exclusion_criteria": "extreme_responding",
            "number_excluded": exclusion_counts["extreme_responding"],
            "description": "Participants with >90% extreme responses (1s and 5s) AND coefficient of variation <0.3"
        })
        exclusion_log.append({
            "exclusion_criteria": "incomplete_data",
            "number_excluded": exclusion_counts["incomplete_data"],
            "description": "Participants who did not complete the questionnaire or submitted blank responses"
        })
        
        exclusion_df = pd.DataFrame(exclusion_log)
        
        # Save exclusion log
        exclusion_filename = f"outputs/VVIQ2_exclusion_log_{timestamp}.csv"
        exclusion_df.to_csv(exclusion_filename, index=False)
        print(f"Saved exclusion log to: {exclusion_filename}")
        
        print("\nExclusion log:")
        print(exclusion_df)
        
        print("\nVVIQ2 data processing completed successfully!")
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"ERROR: An error occurred during processing: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
