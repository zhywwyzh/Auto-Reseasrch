import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
import sys

def extract_numeric_score(text_response):
    """
    Extract numeric score (1-5) from text response using pattern matching.
    
    Parameters:
    text_response (str): Text response containing numeric score
    
    Returns:
    int or None: Extracted numeric score between 1-5, or None if not found
    """
    if pd.isna(text_response) or text_response == '':
        return None
    
    try:
        # Convert to string if not already
        text_str = str(text_response).strip()
        
        # Look for patterns like "Rating: 3" or ending with digit
        match = re.search(r'(?:rating[:\s]*)?(\d)(?:\D*)?$', text_str, re.IGNORECASE)
        if match:
            score = int(match.group(1))
            if 1 <= score <= 5:
                return score
        
        # Additional fallback: look for any digit 1-5 in the string
        digits = re.findall(r'[1-5]', text_str)
        if digits:
            # Take the last valid digit found
            score = int(digits[-1])
            return score
            
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Warning: Error extracting score from '{text_response}': {e}")
        return None
    
    return None

def calculate_missing_items_count(row, score_columns):
    """
    Calculate the number of missing responses for a participant.
    
    Parameters:
    row (pd.Series): Participant data row
    score_columns (list): List of score column names
    
    Returns:
    int: Number of missing responses
    """
    missing_count = sum(1 for col in score_columns if pd.isna(row[col]))
    return missing_count

def check_response_patterns(row, score_columns):
    """
    Check for problematic response patterns in participant data.
    
    Parameters:
    row (pd.Series): Participant data row
    score_columns (list): List of score column names
    
    Returns:
    tuple: (has_identical_pattern, has_extreme_pattern)
    """
    # Safely collect valid scores, ensuring columns exist in the row
    valid_scores = []
    for col in score_columns:
        if col in row and not pd.isna(row[col]):
            valid_scores.append(row[col])
    
    if len(valid_scores) == 0:
        return False, False
    
    # Check for >80% identical ratings (>26 items)
    from collections import Counter
    score_counts = Counter(valid_scores)
    # Handle empty Counter case
    if not score_counts:
        return False, False
    
    max_count = max(score_counts.values()) if score_counts else 0
    has_identical_pattern = max_count > 26
    
    # Check for >90% extreme responses (ratings of 1 or 5)
    extreme_count = sum(1 for score in valid_scores if score in [1, 5])
    # Avoid division by zero
    extreme_percentage = extreme_count / len(valid_scores) if valid_scores else 0
    has_extreme_pattern = extreme_percentage > 0.9
    
    return has_identical_pattern, has_extreme_pattern

def calculate_adjusted_score(row, score_columns):
    """
    Calculate adjusted VVIQ2 score with proportional adjustment for missing items.
    
    Parameters:
    row (pd.Series): Participant data row
    score_columns (list): List of score column names
    
    Returns:
    tuple: (adjusted_score, num_completed_items)
    """
    # Safely collect valid scores, ensuring columns exist in the row
    valid_scores = []
    for col in score_columns:
        if col in row and not pd.isna(row[col]):
            # Ensure score is numeric
            try:
                score = float(row[col])
                valid_scores.append(score)
            except (ValueError, TypeError):
                # Skip non-numeric values
                pass
    
    num_completed = len(valid_scores)
    
    if num_completed < 27:
        return None, num_completed
    
    # Safely calculate sum and adjusted score
    try:
        sum_scores = sum(valid_scores)
        adjusted_score = sum_scores * (32 / num_completed) if num_completed > 0 else None
        return adjusted_score, num_completed
    except Exception as e:
        print(f"Error calculating adjusted score: {e}")
        return None, num_completed

def main():
    """
    Main function to process VVIQ2 data with cleaning and exclusions.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 data processing...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Read input file
        input_file = "raw_data/Vividness of Visual Imagery Questionnaire-2.csv"
        print(f"Reading input file: {input_file}")
        
        df = pd.read_csv(input_file)
        print(f"Loaded data with shape: {df.shape}")
        print(f"Columns before stripping: {list(df.columns)}")
        
        # Strip whitespace from column names to ensure proper matching
        df.columns = df.columns.str.strip()
        print(f"Columns after stripping whitespace: {list(df.columns)}")
        print("First 3 rows:")
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
        
        # Strip whitespace from required columns to match CSV headers
        required_columns = [col.strip() for col in required_columns]
        
        # Check for required columns AFTER both CSV and required columns have been stripped
        print("Checking for required columns...")
        print(f"Required columns: {required_columns}")
        
        # Verify column matching with more detailed output
        found_columns = [col for col in required_columns if col in df.columns]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        print(f"Found {len(found_columns)} of {len(required_columns)} required columns")
        if missing_columns:
            print(f"Missing required columns: {missing_columns}")
            # Try to find similar columns that might be the same but with slight differences
            for missing_col in missing_columns:
                # Safely check for string containment
                similar_cols = [col for col in df.columns if (isinstance(col, str) and isinstance(missing_col, str)) and 
                               (missing_col in col or col in missing_col)]
                if similar_cols:
                    print(f"  Possible matches for '{missing_col}': {similar_cols}")
            return 1
        
        print("All required columns found")
        
        # Extract score columns (all except PROLIFIC_PID)
        score_columns = [col for col in required_columns if col != 'PROLIFIC_PID']
        print(f"Processing {len(score_columns)} VVIQ2 items")
        
        # Validate we have exactly 32 VVIQ2 items
        if len(score_columns) != 32:
            print(f"Warning: Expected 32 VVIQ2 items but found {len(score_columns)}")
            print(f"Score columns found: {score_columns}")
        else:
            print("Confirmed: All 32 VVIQ2 items found and will be processed")
        
        # Filter out rows with null PROLIFIC_PID
        df_clean = df[df['PROLIFIC_PID'].notna()].copy()
        total_participants = df_clean.shape[0]
        print(f"After filtering null PROLIFIC_PID: {total_participants} participants")
        
        # Extract numeric scores from text responses
        print("Extracting numeric scores from text responses...")
        for col in score_columns:
            df_clean[col + '_score'] = df_clean[col].apply(extract_numeric_score)
        
        # Debug score extraction for first few items
        print(f"Score extraction validation:")
        for i, col in enumerate(score_columns[:3]):
            print(f"  Original response example for '{col}': {df_clean[col].iloc[0]}")
            print(f"  Extracted score: {df_clean[col + '_score'].iloc[0]}")
        
        # Add more detailed score extraction debugging
        print(f"\nDetailed score extraction examples:")
        for i in range(min(3, len(df_clean))):
            print(f"Participant {i+1}:")
            for j, col in enumerate(score_columns[:2]):
                print(f"  Item: {col[:50]}...")
                print(f"  Response: '{df_clean[col].iloc[i]}'")
                print(f"  Extracted: {df_clean[col + '_score'].iloc[i]}")
        
        # Create list of score column names
        numeric_score_columns = [col + '_score' for col in score_columns]
        
        # Validate score distribution
        print(f"\nScore distribution validation:")
        for col in numeric_score_columns[:3]:
            scores = df_clean[col].dropna()
            if len(scores) > 0:
                print(f"  {col}: min={scores.min()}, max={scores.max()}, unique={len(scores.unique())}")
            else:
                print(f"  {col}: No valid scores found")
        
        # Check for potential extraction failures
        print(f"\nResponse format check:")
        # Safely extract sample responses with bounds checking
        num_samples = min(5, len(score_columns))
        sample_responses = []
        if len(df_clean) > 0 and num_samples > 0:
            for col in score_columns[:num_samples]:
                if col in df_clean.columns:
                    sample_responses.append(df_clean[col].iloc[0])
                else:
                    sample_responses.append("Column not found")
        print(f"Sample responses: {sample_responses}")
        
        # Validate scores are between 1-5
        print("\nValidating extracted scores...")
        for col in numeric_score_columns:
            valid_scores = df_clean[col].dropna()
            if len(valid_scores) > 0:
                invalid_scores = valid_scores[(valid_scores < 1) | (valid_scores > 5)]
                if len(invalid_scores) > 0:
                    print(f"Warning: Found {len(invalid_scores)} invalid scores in {col}")
        
        # Report missing data per VVIQ2 item
        print("\nMissing data report per VVIQ2 item:")
        for col in numeric_score_columns:
            missing_count = df_clean[col].isna().sum()
            missing_percent = (missing_count / len(df_clean)) * 100
            print(f"  {col}: {missing_count} missing values ({missing_percent:.1f}%)")
        
        # Additional verification of extraction success
        print(f"\nExtraction success verification:")
        total_possible_scores = len(df_clean) * len(numeric_score_columns)
        total_extracted_scores = sum(df_clean[col].notna().sum() for col in numeric_score_columns)
        extraction_rate = (total_extracted_scores / total_possible_scores) * 100 if total_possible_scores > 0 else 0
        print(f"Total possible scores: {total_possible_scores}")
        print(f"Total extracted scores: {total_extracted_scores}")
        print(f"Extraction success rate: {extraction_rate:.1f}%")
        
        # Initialize exclusion tracking
        exclusion_counts = {
            'missing_data': 0,
            'response_patterns': 0,
            'outliers': 0
        }
        
        # Apply participant-level exclusions
        print("Applying participant-level exclusions...")
        
        df_clean['num_missing_items'] = df_clean.apply(
            lambda row: calculate_missing_items_count(row, numeric_score_columns), axis=1
        )
        
        # Exclude participants with >5 missing items (i.e., 6 or more)
        missing_exclusions = df_clean['num_missing_items'] > 5
        exclusion_counts['missing_data'] = missing_exclusions.sum()
        print(f"Participants with >5 missing items (i.e., 6 or more): {exclusion_counts['missing_data']}")
        
        # Check response patterns
        print("Checking response patterns...")
        # Ensure numeric_score_columns exist before checking patterns
        if not numeric_score_columns:
            print("Warning: No numeric score columns found for pattern checking")
            df_clean['has_identical_pattern'] = False
            df_clean['has_extreme_pattern'] = False
        else:
            pattern_results = df_clean.apply(
                lambda row: check_response_patterns(row, numeric_score_columns), axis=1
            )
            # Safely unpack results, handling potential None values
            df_clean['has_identical_pattern'] = [result[0] if result is not None else False for result in pattern_results]
            df_clean['has_extreme_pattern'] = [result[1] if result is not None else False for result in pattern_results]
        
        pattern_exclusions = df_clean['has_identical_pattern'] | df_clean['has_extreme_pattern']
        exclusion_counts['response_patterns'] = pattern_exclusions.sum()
        print(f"Participants with problematic response patterns: {exclusion_counts['response_patterns']}")
        
        # Calculate adjusted VVIQ2 scores
        print("Calculating adjusted VVIQ2 scores...")
        score_results = df_clean.apply(
            lambda row: calculate_adjusted_score(row, numeric_score_columns), axis=1
        )
        df_clean['total_score'] = [result[0] for result in score_results]
        df_clean['num_completed_items'] = [result[1] for result in score_results]
        
        # Filter for participants with valid scores
        valid_scores_mask = df_clean['total_score'].notna()
        print(f"Participants with valid total scores: {valid_scores_mask.sum()}")
        
        # Initialize outlier thresholds with default values
        outlier_threshold_low = float('-inf')
        outlier_threshold_high = float('inf')
        
        # Apply outlier identification (3.0 SD from mean)
        valid_scores = df_clean[valid_scores_mask]['total_score']
        if len(valid_scores) > 0:
            mean_score = valid_scores.mean()
            std_score = valid_scores.std()
            print(f"Mean total score: {mean_score:.2f}, SD: {std_score:.2f}")
            
            outlier_threshold_low = mean_score - 3.0 * std_score
            outlier_threshold_high = mean_score + 3.0 * std_score
            print(f"Outlier thresholds: {outlier_threshold_low:.2f} to {outlier_threshold_high:.2f}")
            
            outlier_mask = (df_clean['total_score'] < outlier_threshold_low) | (df_clean['total_score'] > outlier_threshold_high)
            exclusion_counts['outliers'] = outlier_mask.sum()
            print(f"Participants identified as outliers: {exclusion_counts['outliers']}")
        else:
            outlier_mask = pd.Series([False] * len(df_clean), index=df_clean.index)
            exclusion_counts['outliers'] = 0
            print("No valid scores found for outlier detection")
        
        # Create final exclusion criteria with cascading logic
        print("\nApplying cascading exclusion criteria:")
        
        # Track participants at each exclusion stage
        remaining_after_missing = total_participants - exclusion_counts['missing_data']
        print(f"1. Missing data exclusion: {exclusion_counts['missing_data']} excluded, {remaining_after_missing} remaining")
        
        # For pattern exclusions, only consider those not already excluded by missing data
        pattern_exclusions_unique = pattern_exclusions & ~missing_exclusions
        unique_pattern_exclusions = pattern_exclusions_unique.sum()
        remaining_after_patterns = remaining_after_missing - unique_pattern_exclusions
        print(f"2. Response pattern exclusion: {unique_pattern_exclusions} additionally excluded, {remaining_after_patterns} remaining")
        
        # For outlier exclusions, only consider those not already excluded by previous criteria
        outlier_exclusions_unique = outlier_mask & ~(missing_exclusions | pattern_exclusions)
        unique_outlier_exclusions = outlier_exclusions_unique.sum()
        remaining_after_outliers = remaining_after_patterns - unique_outlier_exclusions
        print(f"3. Outlier exclusion: {unique_outlier_exclusions} additionally excluded, {remaining_after_outliers} remaining")
        
        # Create combined exclusion mask
        final_exclusions = missing_exclusions | pattern_exclusions | outlier_mask
        df_clean['excluded_participant'] = final_exclusions
        
        # Verify cascading exclusion logic consistency
        total_excluded_cascading = exclusion_counts['missing_data'] + unique_pattern_exclusions + unique_outlier_exclusions
        total_excluded_actual = final_exclusions.sum()
        print(f"Cascading exclusion verification:")
        print(f"  Sum of individual exclusions: {total_excluded_cascading}")
        print(f"  Actual total excluded: {total_excluded_actual}")
        if total_excluded_cascading != total_excluded_actual:
            print(f"  Warning: Exclusion count mismatch detected!")
        
        print(f"Total excluded: {final_exclusions.sum()} participants")
        print(f"Final dataset will contain: {total_participants - final_exclusions.sum()} participants")
        
        # Create exclusion reasons
        def get_exclusion_reason(row):
            reasons = []
            
            # Check for missing data exclusion
            if row['num_missing_items'] > 5:
                reasons.append('missing_data')
                
            # Check for response pattern exclusions
            if row['has_identical_pattern']:
                reasons.append('identical_pattern')
            if row['has_extreme_pattern']:
                reasons.append('extreme_pattern')
                
            # Check for outlier exclusion, handling NaN values
            if pd.notna(row['total_score']):
                if (row['total_score'] < outlier_threshold_low) or (row['total_score'] > outlier_threshold_high):
                    reasons.append('outlier')
            elif pd.isna(row['total_score']) and 'num_missing_items' in row and row['num_missing_items'] <= 5:
                # If total_score is NaN but missing item count is acceptable,
                # this indicates a calculation issue that should be noted
                reasons.append('invalid_score_calculation')
            
            # Return appropriate reason string
            if not reasons:
                return 'none'
            return '; '.join(reasons)
        
        df_clean['exclusion_reason'] = df_clean.apply(get_exclusion_reason, axis=1)
        
        # Prepare output data
        required_output_columns = ['PROLIFIC_PID', 'total_score', 'num_completed_items', 'excluded_participant', 'exclusion_reason']
        
        # Validate all required columns exist before creating output dataframe
        print("\nValidating output columns...")
        missing_output_cols = [col for col in required_output_columns if col not in df_clean.columns]
        if missing_output_cols:
            print(f"Warning: Missing required output columns: {missing_output_cols}")
            # Create any missing columns with default values
            for col in missing_output_cols:
                print(f"Creating missing column '{col}' with default values")
                if col == 'excluded_participant':
                    df_clean[col] = False
                elif col == 'exclusion_reason':
                    df_clean[col] = 'none'
                else:
                    df_clean[col] = None
        
        # Create output dataframe with required columns
        output_df = df_clean[required_output_columns].copy()
        output_df.rename(columns={'PROLIFIC_PID': 'participantId'}, inplace=True)
        
        # Verify output data integrity
        print("\nOutput data summary:")
        print(f"Columns: {list(output_df.columns)}")
        print(f"Total rows: {len(output_df)}")
        print(f"Excluded participants: {output_df['excluded_participant'].sum()}")
        print(f"Included participants: {(~output_df['excluded_participant']).sum()}")
        print("First 2 rows:")
        print(output_df.head(2))
        
        # Check for any NaN values in critical columns
        critical_cols = ['participantId', 'excluded_participant', 'exclusion_reason']
        for col in critical_cols:
            na_count = output_df[col].isna().sum()
            if na_count > 0:
                print(f"Warning: Found {na_count} NaN values in critical column '{col}'")
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save cleaned data
        output_file = f"outputs/VVIQ2_cleaned_data_{timestamp}.csv"
        output_df.to_csv(output_file, index=False)
        print(f"Saved cleaned data to: {output_file}")
        
        # Create exclusion log
        exclusion_log_data = []
        
        for criterion, count in exclusion_counts.items():
            percentage = (count / total_participants) * 100 if total_participants > 0 else 0
            exclusion_log_data.append({
                'exclusion_criterion': criterion,
                'total_excluded': count,
                'percentage_excluded': percentage
            })
        
        # Add total exclusions
        total_excluded = final_exclusions.sum()
        total_percentage = (total_excluded / total_participants) * 100 if total_participants > 0 else 0
        exclusion_log_data.append({
            'exclusion_criterion': 'total_excluded',
            'total_excluded': total_excluded,
            'percentage_excluded': total_percentage
        })
        
        exclusion_log_df = pd.DataFrame(exclusion_log_data)
        
        print("Exclusion log:")
        print(exclusion_log_df)
        
        # Save exclusion log
        exclusion_log_file = f"outputs/VVIQ2_exclusion_log_{timestamp}.csv"
        exclusion_log_df.to_csv(exclusion_log_file, index=False)
        print(f"Saved exclusion log to: {exclusion_log_file}")
        
        # Final summary
        print(f"\nFinal summary:")
        print(f"Data found for {total_participants} participants")
        print(f"Participants excluded due to >5 missing items: {exclusion_counts['missing_data']}")
        print(f"Participants excluded due to response patterns: {exclusion_counts['response_patterns']}")
        print(f"Participants excluded as outliers: {exclusion_counts['outliers']}")
        print(f"Total participants excluded: {total_excluded} ({total_percentage:.1f}%)")
        print(f"Final dataset: {total_participants - total_excluded} participants")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
