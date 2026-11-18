import pandas as pd
import numpy as np
import os
import re
from datetime import datetime

def extract_numeric_score(response_text):
    """
    Extract numeric score from text response string.
    
    Parameters:
    response_text (str): Text response containing numeric score at end
    
    Returns:
    int or None: Extracted numeric score (1-5) or None if invalid
    """
    if pd.isna(response_text) or response_text == '':
        return None
    
    # Convert to string and extract last digit
    response_str = str(response_text).strip()
    
    # Find all digits in the string
    digits = re.findall(r'\d', response_str)
    
    if not digits:
        return None
    
    # Take the last digit as the score
    score = int(digits[-1])
    
    # Validate score is in range 1-5
    if 1 <= score <= 5:
        return score
    else:
        return None

def calculate_missing_percentage(scores):
    """
    Calculate percentage of missing items for a participant.
    
    Parameters:
    scores (list): List of extracted scores (may contain None values)
    
    Returns:
    float: Percentage of missing items (0-100)
    """
    total_items = len(scores)
    missing_items = sum(1 for score in scores if score is None)
    return (missing_items / total_items) * 100

def calculate_invariant_percentage(scores):
    """
    Calculate percentage of identical responses for a participant.
    
    Parameters:
    scores (list): List of extracted scores (excluding None values)
    
    Returns:
    float: Percentage of most frequent response (0-100)
    """
    valid_scores = [score for score in scores if score is not None]
    
    if len(valid_scores) == 0:
        return 0
    
    # Count frequency of each score
    from collections import Counter
    score_counts = Counter(valid_scores)
    
    # Find most frequent count
    max_count = max(score_counts.values())
    
    return (max_count / len(valid_scores)) * 100

def main():
    """
    Main function to process VVIQ2 data and apply exclusion criteria.
    """
    try:
        print("Starting VVIQ2 data processing...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Load input file
        input_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        print(f"Loading input file: {input_file}")
        
        try:
            df = pd.read_csv(input_file)
        except FileNotFoundError:
            print(f"Error: Input file {input_file} not found")
            return 1
        except Exception as e:
            print(f"Error loading input file: {e}")
            return 1

        df.columns = [col.strip() for col in df.columns]  # Strip whitespace from column names

        # Add comprehensive debugging for PROLIFIC_PID column detection
        print(f"Looking for PROLIFIC_PID column...")
        if 'PROLIFIC_PID' in df.columns:
            print(f"Found PROLIFIC_PID column with {df['PROLIFIC_PID'].nunique()} unique values")
            print(f"Sample PROLIFIC_PID values: {df['PROLIFIC_PID'].head(3).tolist()}")
        else:
            print("PROLIFIC_PID column not found - checking end of column list")
            print(f"Last 5 columns: {list(df.columns)[-5:]}")
            print(f"All columns: {list(df.columns)}")
            # Check if it's named differently
            prolific_cols = [col for col in df.columns if 'PROLIFIC' in col.upper()]
            if prolific_cols:
                print(f"Found similar columns: {prolific_cols}")

        # Print all columns (truncated)
        print(f"Columns in dataset ({len(df.columns)} total): {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")
        
        # Print first 3 rows
        print("First 3 rows of data:")
        print(df.head(3))
        
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
            print(f"Warning: Missing required columns: {missing_columns}")
            # Check if critical PROLIFIC_PID column is missing
            if 'PROLIFIC_PID' in missing_columns:
                print("Error: Critical column 'PROLIFIC_PID' is missing from the data. Cannot proceed.")
                return 1
            # Continue with available columns only
            available_vviq_columns = [col for col in required_columns[1:] if col in df.columns]
        else:
            available_vviq_columns = required_columns[1:]

        print(f"Processing {len(available_vviq_columns)} VVIQ2 items")

        print(f"\nColumn matching results:")
        print(f"Total required VVIQ2 columns: {len(required_columns)-1}")  # Exclude PROLIFIC_PID
        print(f"Successfully matched columns: {len(available_vviq_columns)}")
        missing_vviq_count = (len(required_columns) - 1) - len(available_vviq_columns)
        print(f"Missing columns: {missing_vviq_count}")
        if missing_columns:
            vviq_missing = [col for col in missing_columns if col != 'PROLIFIC_PID']
            if vviq_missing:
                print(f"Missing VVIQ2 columns: {vviq_missing[:3]}{'...' if len(vviq_missing) > 3 else ''}")
            if 'PROLIFIC_PID' in missing_columns:
                print("  - Critical: PROLIFIC_PID column is missing.")

        # Add validation for exactly 32 VVIQ2 columns
        if len(available_vviq_columns) != 32:
            print(f"Error: Expected exactly 32 VVIQ2 columns, but found {len(available_vviq_columns)}")
            print("Cannot proceed with subscale calculations without all 32 items")
            return 1

        # Print sample responses to understand data format
        if len(available_vviq_columns) > 0:
            print(f"\nSample response data inspection:")
            print(f"Sample response from first participant for '{available_vviq_columns[0]}': {df.iloc[0][available_vviq_columns[0]]}")
            if len(available_vviq_columns) > 1:
                print(f"Sample response from first participant for '{available_vviq_columns[1]}': {df.iloc[0][available_vviq_columns[1]]}")

        # Extract numeric scores for all participants
        results = []
        exclusion_counts = {
            'missing_data': 0,
            'invariant_responding': 0,
            'extreme_response_time': 0,
            'invalid_responses': 0,
            'incomplete_questionnaire': 0
        }
        
        total_participants = len(df)
        print(f"Processing {total_participants} participants...")
        
        for idx, row in df.iterrows():
            # Always treat participant ID as string, avoid float conversion
            participant_id = str(row['PROLIFIC_PID']) if 'PROLIFIC_PID' in row else "MISSING_ID"

            # Truncate verbose output for better readability
            if idx < 10 or idx % 50 == 0 or idx >= total_participants - 5:
                print(f"Processing participant {idx+1}/{total_participants}: {participant_id}")
            elif idx == 10:
                print("... (processing continues, showing every 50th participant) ...")

            # Calculate completion time in minutes
            start_time = pd.to_datetime(row['Start Date'], errors='coerce')
            end_time = pd.to_datetime(row['End Date'], errors='coerce')
            if pd.notna(start_time) and pd.notna(end_time):
                completion_time_minutes = (end_time - start_time).total_seconds() / 60
            else:
                completion_time_minutes = np.nan

            # Extract scores from all VVIQ2 items
            extracted_scores = []
            for col in available_vviq_columns:
                score = extract_numeric_score(row[col])
                extracted_scores.append(score)

            # Add detailed debugging for first few participants
            if idx < 3:  # Show details for first 3 participants
                print(f"  Detailed score extraction:")
                for i, (col, score) in enumerate(zip(available_vviq_columns[:5], extracted_scores[:5])):
                    print(f"    Item {i+1}: '{row[col]}' -> {score}")
                
                # Validate extracted scores are integers 1-5
                invalid_scores = [score for score in extracted_scores if score is not None and (not isinstance(score, int) or score < 1 or score > 5)]
                if invalid_scores:
                    print(f"  Warning: Found invalid scores: {invalid_scores}")

            # Initialize exclusion flags
            excluded_missing_data = False
            excluded_invariant_responding = False
            excluded_extreme_response_time = False
            excluded_invalid_responses = False
            excluded_incomplete_questionnaire = False
            primary_exclusion_reason = "None"

            # Check for incomplete questionnaire (all None values)
            if all(score is None for score in extracted_scores):
                excluded_incomplete_questionnaire = True
                exclusion_counts['incomplete_questionnaire'] += 1
                primary_exclusion_reason = "Incomplete questionnaire"
                print(f"  Excluded: Incomplete questionnaire")

            # Check for invalid responses (scores outside 1-5 range)
            # Note: extract_numeric_score already filters to 1-5, so this checks for extraction failures
            valid_scores = [score for score in extracted_scores if score is not None]
            if any(score < 1 or score > 5 for score in valid_scores):
                excluded_invalid_responses = True
                exclusion_counts['invalid_responses'] += 1
                if primary_exclusion_reason == "None":
                    primary_exclusion_reason = "Invalid responses"
                print(f"  Excluded: Invalid responses")

            # Check for missing data (>10% missing items)
            missing_percentage = calculate_missing_percentage(extracted_scores)
            if missing_percentage > 10:
                excluded_missing_data = True
                exclusion_counts['missing_data'] += 1
                if primary_exclusion_reason == "None":
                    primary_exclusion_reason = "Missing data"
                print(f"  Excluded: Missing data ({missing_percentage:.1f}% missing)")

            # Check for extreme response time (< 1 minute)
            if pd.notna(completion_time_minutes) and completion_time_minutes < 1:
                excluded_extreme_response_time = True
                exclusion_counts['extreme_response_time'] += 1
                if primary_exclusion_reason == "None":
                    primary_exclusion_reason = "Extreme response time"
                print(f"  Excluded: Extreme response time ({completion_time_minutes:.2f} minutes)")

            # Check for invariant responding (>90% identical AND <3 minutes)
            if len(valid_scores) > 0:
                invariant_percentage = calculate_invariant_percentage(extracted_scores)
                # Apply exclusion ONLY if invariant AND fast completion time
                if invariant_percentage > 90 and pd.notna(completion_time_minutes) and completion_time_minutes < 3:
                    excluded_invariant_responding = True
                    exclusion_counts['invariant_responding'] += 1
                    if primary_exclusion_reason == "None":
                        primary_exclusion_reason = "Invariant responding"
                    print(f"  Excluded: Invariant responding ({invariant_percentage:.1f}% identical, {completion_time_minutes:.2f} minutes)")

            # Calculate scores for valid participants
            total_vividness_score = None
            subscale_scores = [None] * 8

            questionnaire_valid = not (excluded_missing_data or excluded_invariant_responding or
                                     excluded_extreme_response_time or excluded_invalid_responses or
                                     excluded_incomplete_questionnaire)

            if questionnaire_valid and len(available_vviq_columns) == 32:
                # Calculate total score
                valid_scores = [score for score in extracted_scores if score is not None]
                total_vividness_score = int(sum(valid_scores)) if len(valid_scores) > 0 else None

                # Calculate subscale scores with at least 1 valid item each
                for i in range(8):
                    start_idx = i * 4
                    end_idx = start_idx + 4
                    subscale_items = extracted_scores[start_idx:end_idx]
                    valid_subscale_items = [score for score in subscale_items if score is not None]
                    if len(valid_subscale_items) > 0:
                        subscale_scores[i] = int(sum(valid_subscale_items))
                    else:
                        subscale_scores[i] = None

                # Dynamic score validation - total score
                num_valid_items = len(valid_scores)
                if total_vividness_score is not None and (total_vividness_score < num_valid_items or total_vividness_score > num_valid_items * 5):
                    print(f"  Warning: Total score {total_vividness_score} outside expected range [{num_valid_items}, {num_valid_items * 5}]")

                # Dynamic score validation - subscale scores
                for i, score in enumerate(subscale_scores):
                    if score is not None:
                        start_idx = i * 4
                        end_idx = start_idx + 4
                        subscale_items = extracted_scores[start_idx:end_idx]
                        num_valid_subscale_items = len([s for s in subscale_items if s is not None])
                        if num_valid_subscale_items > 0 and (score < num_valid_subscale_items or score > num_valid_subscale_items * 5):
                            print(f"  Warning: Subscale {i+1} score {score} outside expected range [{num_valid_subscale_items}, {num_valid_subscale_items * 5}]")

                print(f"  Valid participant - Total score: {total_vividness_score}, Subscales: {subscale_scores}")
            else:
                print(f"  Invalid participant - excluded")
            
            # Store results
            result = {
                'participantId': participant_id,
                'total_vividness_score': total_vividness_score,
                'familiar_person_score': subscale_scores[0],
                'sunrise_score': subscale_scores[1],
                'shop_front_score': subscale_scores[2],
                'countryside_score': subscale_scores[3],
                'driving_scenario_score': subscale_scores[4],
                'beach_scene_score': subscale_scores[5],
                'railway_station_score': subscale_scores[6],
                'garden_scene_score': subscale_scores[7],
                'excluded_missing_data': excluded_missing_data,
                'excluded_invariant_responding': excluded_invariant_responding,
                'excluded_extreme_response_time': excluded_extreme_response_time,
                'excluded_invalid_responses': excluded_invalid_responses,
                'excluded_incomplete_questionnaire': excluded_incomplete_questionnaire,
                'questionnaire_valid': questionnaire_valid,
                'primary_exclusion_reason': primary_exclusion_reason
            }
            
            results.append(result)
        
        # Create results DataFrame
        results_df = pd.DataFrame(results)

        # Prepare score columns for CSV output: set excluded participants' scores to np.nan, keep integers for valid
        score_columns = [
            'total_vividness_score',
            'familiar_person_score',
            'sunrise_score',
            'shop_front_score',
            'countryside_score',
            'driving_scenario_score',
            'beach_scene_score',
            'railway_station_score',
            'garden_scene_score'
        ]
        for col in score_columns:
            if col in results_df.columns:
                # Convert None to np.nan for excluded participants, keep integers for valid participants
                results_df[col] = results_df[col].where(results_df['questionnaire_valid'], np.nan)

        print(f"\nData types after exclusion masking (should be float for NaN support):")
        for col in score_columns:
            if col in results_df.columns:
                print(f"  {col}: {results_df[col].dtype}")

        # Verification: valid participants should have integer scores, excluded should have NaN
        valid_mask = results_df['questionnaire_valid']
        excluded_mask = ~results_df['questionnaire_valid']
        for col in score_columns:
            if col in results_df.columns:
                valid_vals = results_df.loc[valid_mask, col]
                excluded_vals = results_df.loc[excluded_mask, col]
                if not valid_vals.dropna().apply(lambda x: float(x).is_integer()).all():
                    print(f"  Verification warning: Not all valid {col} values are integer!")
                if not excluded_vals.isna().all():
                    print(f"  Verification warning: Not all excluded {col} values are NaN!")

        print("\nResults summary:")
        print(f"Total participants processed: {len(results_df)}")
        print(f"Valid participants: {sum(results_df['questionnaire_valid'])}")
        print(f"Excluded participants: {sum(~results_df['questionnaire_valid'])}")
        
        print("\nFirst 2 rows of results:")
        print("Columns:", list(results_df.columns))
        print(results_df.head(2))
        
        # Save cleaned scores
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f'outputs/VVIQ2_cleaned_scores_{timestamp}.csv'

        results_df.to_csv(output_file, index=False)
        print(f"Saved cleaned scores to: {output_file}")
        
        # Create exclusion log
        exclusion_log = []
        for criterion, count in exclusion_counts.items():
            exclusion_log.append({
                'exclusion_criterion': criterion,
                'count_excluded': count,
                'total_participants_assessed': total_participants,
                'exclusion_percentage': (count / total_participants) * 100
            })
        
        exclusion_df = pd.DataFrame(exclusion_log)
        
        print("\nExclusion summary:")
        print("Columns:", list(exclusion_df.columns))
        print(exclusion_df.head(2))
        
        for _, row in exclusion_df.iterrows():
            print(f"{row['exclusion_criterion']}: {row['count_excluded']} participants ({row['exclusion_percentage']:.1f}%)")
        
        # Save exclusion log
        exclusion_file = f'outputs/VVIQ2_exclusion_log_{timestamp}.csv'
        exclusion_df.to_csv(exclusion_file, index=False)
        print(f"Saved exclusion log to: {exclusion_file}")
        
        # Final exclusion summary
        print(f"\n=== FINAL DATA PROCESSING SUMMARY ===")
        print(f"Initial participant count: {total_participants}")
        print(f"Final valid participant count: {sum(results_df['questionnaire_valid'])}")
        print(f"Total excluded: {sum(~results_df['questionnaire_valid'])}")
        print(f"Exclusion breakdown:")
        for criterion, count in exclusion_counts.items():
            if count > 0:
                print(f"  - {criterion.replace('_', ' ').title()}: {count} participants")
        print(f"Data retention rate: {(sum(results_df['questionnaire_valid']) / total_participants * 100):.1f}%")

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
