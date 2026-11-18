import pandas as pd
import numpy as np
import os
import re
import glob
from datetime import datetime

def find_most_recent_file(pattern):
    """
    Find the most recent file matching the given pattern.
    
    Parameters:
    pattern (str): File pattern to match
    
    Returns:
    str: Path to the most recent file, or None if no files found
    """
    files = glob.glob(pattern)
    if not files:
        return None
    # Get the most recent file based on creation time
    return max(files, key=os.path.getctime)

def extract_numeric_score(text_value):
    """
    Extract numeric score (1-5) from text string using regex.
    
    Parameters:
    text_value (str): Text containing numeric score
    
    Returns:
    int: Extracted numeric score, or None if not found/invalid
    """
    if pd.isna(text_value):
        return None
    
    # Convert to string if not already
    text_str = str(text_value)
    
    # Find all digits 1-5 in the text
    matches = re.findall(r'[1-5]', text_str)
    
    if matches:
        # Take the first valid digit found
        score = int(matches[0])
        if 1 <= score <= 5:
            return score
    
    return None

def load_and_process_exclusion_data(file_pattern):
    """
    Load participant exclusion status data and filter to included participants.
    
    Parameters:
    file_pattern (str): Pattern to match exclusion status files
    
    Returns:
    pd.DataFrame: Filtered dataframe with included participants only
    """
    print("Loading participant exclusion status data...")
    
    # Find most recent exclusion file
    exclusion_file = find_most_recent_file(file_pattern)
    
    if exclusion_file is None:
        raise FileNotFoundError(f"No exclusion status file found matching pattern: {file_pattern}")
    
    print(f"Using exclusion file: {exclusion_file}")
    
    # Load exclusion data
    exclusion_df = pd.read_csv(exclusion_file)
    
    print("Exclusion data columns:")
    print(exclusion_df.columns.tolist())
    print("\nFirst 3 rows of exclusion data:")
    print(exclusion_df.head(3))
    
    # Check required columns
    required_cols = ['participantId', 'prolific_participant_id', 'included']
    missing_cols = [col for col in required_cols if col not in exclusion_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in exclusion data: {missing_cols}")
    
    print(f"\nTotal participants in exclusion file: {len(exclusion_df)}")
    print(f"Unique values in 'included' column: {exclusion_df['included'].unique()}")
    
    # Filter to included participants only
    included_df = exclusion_df[exclusion_df['included'] == True].copy()
    
    print(f"Participants with included=True: {len(included_df)}")
    
    return included_df

def load_vviq2_data(file_path):
    """
    Load VVIQ2 questionnaire data.
    
    Parameters:
    file_path (str): Path to VVIQ2 CSV file
    
    Returns:
    pd.DataFrame: VVIQ2 dataframe
    """
    print("\nLoading VVIQ2 data...")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"VVIQ2 file not found: {file_path}")
    
    print(f"Using VVIQ2 file: {file_path}")
    
    # Load VVIQ2 data
    vviq2_df = pd.read_csv(file_path)
    
    # Strip whitespace from column names to ensure matching
    vviq2_df.columns = vviq2_df.columns.str.strip()
    
    print("VVIQ2 data columns:")
    print(vviq2_df.columns.tolist())
    print(f"\nFirst 3 rows of VVIQ2 data:")
    print(vviq2_df.head(3))
    
    # Check for PROLIFIC_PID column
    if 'PROLIFIC_PID' not in vviq2_df.columns:
        raise ValueError("Missing required column 'PROLIFIC_PID' in VVIQ2 data")
    
    print(f"\nTotal participants in VVIQ2 file: {len(vviq2_df)}")
    
    return vviq2_df

def get_vviq2_question_columns():
    """
    Get the exact VVIQ2 question column names in order.
    
    Returns:
    list: List of 32 VVIQ2 question column names
    """
    # These names should match the actual column names in the CSV after stripping whitespace
    return [
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

def match_and_process_participants(included_df, vviq2_df):
    """
    Match participants between exclusion and VVIQ2 data and process responses.
    
    Parameters:
    included_df (pd.DataFrame): Filtered exclusion data with included participants
    vviq2_df (pd.DataFrame): VVIQ2 questionnaire data
    
    Returns:
    pd.DataFrame: Merged and processed participant data
    """
    print("\nMatching participants between exclusion and VVIQ2 data...")
    
    # Merge on prolific IDs
    merged_df = included_df.merge(
        vviq2_df, 
        left_on='prolific_participant_id', 
        right_on='PROLIFIC_PID', 
        how='inner'
    )
    
    print(f"Participants with matching prolific IDs: {len(merged_df)}")
    
    if len(merged_df) == 0:
        raise ValueError("No participants found with matching prolific IDs between exclusion and VVIQ2 data")
    
    # Get VVIQ2 question columns
    vviq2_questions = get_vviq2_question_columns()
    
    print(f"\nExpected {len(vviq2_questions)} VVIQ2 question columns")
    
    # Check which VVIQ2 columns exist in the data
    available_questions = [q for q in vviq2_questions if q in merged_df.columns]
    missing_questions = [q for q in vviq2_questions if q not in merged_df.columns]
    
    print(f"Available VVIQ2 question columns: {len(available_questions)}")
    if missing_questions:
        print(f"Missing VVIQ2 question columns: {len(missing_questions)}")
        print("First few missing columns:")
        for i, q in enumerate(missing_questions[:5]):
            print(f"  {i+1}: {q!r}")
        if len(missing_questions) > 5:
            print(f"  ... and {len(missing_questions)-5} more")
    else:
        print("All expected VVIQ2 question columns are present.")
    
    # Debug: Show which columns are being matched
    print("\nColumn matching debug:")
    print("Columns in merged_df:")
    print(list(merged_df.columns))
    print("Columns expected (after stripping):")
    print(vviq2_questions)
    print("Columns matched:")
    print(available_questions)
    print("Columns missing:")
    print(missing_questions)
    
    if len(available_questions) == 0:
        raise ValueError("No VVIQ2 question columns found in merged data")
    
    return merged_df, available_questions

def extract_and_validate_scores(merged_df, available_questions):
    """
    Extract numeric scores from VVIQ2 responses and validate them.
    
    Parameters:
    merged_df (pd.DataFrame): Merged participant data
    available_questions (list): List of available VVIQ2 question columns
    
    Returns:
    pd.DataFrame: Dataframe with extracted numeric scores
    """
    print("\nExtracting and validating VVIQ2 scores...")
    
    # Create new dataframe for processed scores
    processed_df = merged_df[['participantId', 'prolific_participant_id']].copy()
    
    # Extract numeric scores for each question
    score_columns = []
    for i, question in enumerate(available_questions):
        score_col = f'vviq2_item_{i+1}'
        score_columns.append(score_col)
        
        print(f"Processing question {i+1}: {question[:50]}...")
        
        # Extract scores
        processed_df[score_col] = merged_df[question].apply(extract_numeric_score)
        
        # Check for missing/invalid scores
        missing_count = processed_df[score_col].isna().sum()
        if missing_count > 0:
            print(f"  Warning: {missing_count} participants have missing/invalid scores for item {i+1}")
        
        # Validate score range
        valid_scores = processed_df[score_col].dropna()
        if len(valid_scores) > 0:
            min_score = valid_scores.min()
            max_score = valid_scores.max()
            print(f"  Score range: {min_score} to {max_score}")
            
            if min_score < 1 or max_score > 5:
                print(f"  Warning: Scores outside valid range (1-5) found for item {i+1}")
    
    # Check completeness
    processed_df['response_complete'] = True
    for score_col in score_columns:
        processed_df.loc[processed_df[score_col].isna(), 'response_complete'] = False
    
    complete_count = processed_df['response_complete'].sum()
    incomplete_count = len(processed_df) - complete_count
    
    print(f"\nResponse completeness:")
    print(f"  Complete responses: {complete_count}")
    print(f"  Incomplete responses: {incomplete_count}")
    
    return processed_df, score_columns

def calculate_scores_and_subscales(processed_df, score_columns):
    """
    Calculate total scores and subscale scores for VVIQ2.
    
    Parameters:
    processed_df (pd.DataFrame): Dataframe with extracted scores
    score_columns (list): List of score column names
    
    Returns:
    pd.DataFrame: Dataframe with calculated scores and subscales
    """
    print("\nCalculating total and subscale scores...")
    
    # Only calculate scores for participants with complete responses
    complete_mask = processed_df['response_complete'] == True
    complete_df = processed_df[complete_mask].copy()
    
    print(f"Calculating scores for {len(complete_df)} participants with complete responses")
    
    if len(complete_df) == 0:
        print("Warning: No participants with complete responses found")
        return processed_df
    
    # Calculate total score
    score_cols_available = [col for col in score_columns if col in complete_df.columns]
    
    if len(score_cols_available) > 0:
        complete_df['total_score_raw'] = complete_df[score_cols_available].sum(axis=1)
        
        print(f"Total score statistics:")
        print(f"  Mean: {complete_df['total_score_raw'].mean():.2f}")
        print(f"  Std: {complete_df['total_score_raw'].std():.2f}")
        print(f"  Range: {complete_df['total_score_raw'].min()} to {complete_df['total_score_raw'].max()}")
        
        # Validate total score range
        expected_min = len(score_cols_available)
        expected_max = len(score_cols_available) * 5
        print(f"  Expected range: {expected_min} to {expected_max}")
        
        # Standardize total score
        complete_df['total_score_standardized'] = (
            complete_df['total_score_raw'] - complete_df['total_score_raw'].mean()
        ) / complete_df['total_score_raw'].std()
    
    # Define subscales (4 items each)
    subscale_definitions = {
        'face_person': list(range(0, 4)),
        'sunrise': list(range(4, 8)),
        'shop': list(range(8, 12)),
        'countryside': list(range(12, 16)),
        'car_road': list(range(16, 20)),
        'beach': list(range(20, 24)),
        'station': list(range(24, 28)),
        'garden': list(range(28, 32))
    }
    
    # Calculate subscale scores
    for subscale_name, item_indices in subscale_definitions.items():
        print(f"Calculating {subscale_name} subscale...")
        
        # Get available columns for this subscale
        subscale_cols = []
        for idx in item_indices:
            if idx < len(score_cols_available):
                subscale_cols.append(score_cols_available[idx])
        
        if len(subscale_cols) > 0:
            # Raw subscale score
            raw_col = f'{subscale_name}_raw'
            complete_df[raw_col] = complete_df[subscale_cols].sum(axis=1)
            
            print(f"  {subscale_name} raw score range: {complete_df[raw_col].min()} to {complete_df[raw_col].max()}")
            
            # Standardized subscale score
            std_col = f'{subscale_name}_standardized'
            complete_df[std_col] = (
                complete_df[raw_col] - complete_df[raw_col].mean()
            ) / complete_df[raw_col].std()
        else:
            print(f"  Warning: No items available for {subscale_name} subscale")
    
    # Merge back with original dataframe
    result_df = processed_df.copy()
    
    # Initialize score columns with NaN for all participants
    score_cols_to_add = [col for col in complete_df.columns if col not in result_df.columns]
    for col in score_cols_to_add:
        result_df[col] = np.nan
    
    # Update scores for participants with complete responses
    for col in score_cols_to_add:
        result_df.loc[complete_mask, col] = complete_df[col].values
    
    return result_df

def perform_data_quality_checks(final_df):
    """
    Perform comprehensive data quality checks and generate descriptive statistics.
    
    Parameters:
    final_df (pd.DataFrame): Final processed dataframe
    
    Returns:
    None
    """
    print("\n" + "="*50)
    print("DATA QUALITY CHECKS AND DESCRIPTIVE STATISTICS")
    print("="*50)
    
    print(f"\nFinal dataset shape: {final_df.shape}")
    
    # Check response completeness
    complete_responses = final_df['response_complete'].sum()
    total_responses = len(final_df)
    print(f"\nResponse completeness:")
    print(f"  Complete responses: {complete_responses}")
    print(f"  Incomplete responses: {total_responses - complete_responses}")
    print(f"  Completion rate: {complete_responses/total_responses*100:.1f}%")
    
    # Check for impossible values
    score_columns = [col for col in final_df.columns if 'raw' in col and col != 'response_complete']
    
    print(f"\nScore validation for {len(score_columns)} score columns:")
    for col in score_columns:
        valid_data = final_df[col].dropna()
        if len(valid_data) > 0:
            min_val = valid_data.min()
            max_val = valid_data.max()
            print(f"  {col}: range {min_val} to {max_val}")
            
            # Check for impossible values based on column type
            if 'total_score' in col:
                # Total score should be reasonable
                if min_val < 10 or max_val > 200:
                    print(f"    WARNING: Unusual total score range")
            elif any(subscale in col for subscale in ['face_person', 'sunrise', 'shop', 'countryside', 'car_road', 'beach', 'station', 'garden']):
                # Subscale scores should be 4-20
                if min_val < 4 or max_val > 20:
                    print(f"    WARNING: Unusual subscale score range")
    
    # Descriptive statistics for complete responses only
    complete_df = final_df[final_df['response_complete'] == True]
    
    if len(complete_df) > 0:
        print(f"\nDescriptive statistics for {len(complete_df)} participants with complete responses:")
        
        # Total score statistics
        if 'total_score_raw' in complete_df.columns:
            total_scores = complete_df['total_score_raw'].dropna()
            if len(total_scores) > 0:
                print(f"\nTotal VVIQ2 Score:")
                print(f"  N: {len(total_scores)}")
                print(f"  Mean: {total_scores.mean():.2f}")
                print(f"  SD: {total_scores.std():.2f}")
                print(f"  Median: {total_scores.median():.2f}")
                print(f"  Range: {total_scores.min()} to {total_scores.max()}")
        
        # Subscale statistics
        subscales = ['face_person', 'sunrise', 'shop', 'countryside', 'car_road', 'beach', 'station', 'garden']
        print(f"\nSubscale Scores:")
        for subscale in subscales:
            col_name = f'{subscale}_raw'
            if col_name in complete_df.columns:
                scores = complete_df[col_name].dropna()
                if len(scores) > 0:
                    print(f"  {subscale}: Mean={scores.mean():.2f}, SD={scores.std():.2f}, Range={scores.min()}-{scores.max()}")
    
    print("\nData quality checks completed.")

def save_output_file(final_df):
    """
    Save the processed VVIQ2 scores to output CSV file.
    
    Parameters:
    final_df (pd.DataFrame): Final processed dataframe
    
    Returns:
    str: Path to saved output file
    """
    print("\nPreparing output file...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f'outputs/VVIQ2_processed_scores_{timestamp}.csv'
    
    # Select only required output columns
    required_output_cols = [
        'participantId',
        'prolific_participant_id',
        'total_score_raw',
        'total_score_standardized',
        'face_person_raw',
        'face_person_standardized',
        'sunrise_raw',
        'sunrise_standardized',
        'shop_raw',
        'shop_standardized',
        'countryside_raw',
        'countryside_standardized',
        'car_road_raw',
        'car_road_standardized',
        'beach_raw',
        'beach_standardized',
        'station_raw',
        'station_standardized',
        'garden_raw',
        'garden_standardized',
        'response_complete'
    ]
    
    # Check which columns exist in the final dataframe
    available_cols = [col for col in required_output_cols if col in final_df.columns]
    missing_cols = [col for col in required_output_cols if col not in final_df.columns]
    
    print(f"Available output columns: {len(available_cols)}")
    if missing_cols:
        print(f"Missing output columns: {missing_cols}")
        # Add missing columns with NaN values
        for col in missing_cols:
            final_df[col] = np.nan
        available_cols = required_output_cols
    
    # Create output dataframe with only required columns
    output_df = final_df[available_cols].copy()
    
    print(f"Output dataframe shape: {output_df.shape}")
    print("Output columns:")
    print(output_df.columns.tolist())
    print("\nFirst 2 rows of output data:")
    print(output_df.head(2))
    
    # Save to CSV
    output_df.to_csv(output_filename, index=False)
    
    print(f"\nOutput saved to: {output_filename}")
    
    return output_filename

def main():
    """
    Main function to execute the VVIQ2 data processing pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 data processing pipeline...")
        print("="*50)
        
        # Step 1: Load and filter exclusion data
        exclusion_pattern = 'outputs/participant_exclusion_status_*.csv'
        included_df = load_and_process_exclusion_data(exclusion_pattern)
        
        # Step 2: Load VVIQ2 data
        vviq2_file = '../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv'
        vviq2_df = load_vviq2_data(vviq2_file)
        
        # Step 3: Match participants and verify data
        merged_df, available_questions = match_and_process_participants(included_df, vviq2_df)
        
        # Step 4: Extract and validate VVIQ2 scores
        processed_df, score_columns = extract_and_validate_scores(merged_df, available_questions)
        
        # Step 5: Calculate total and subscale scores
        final_df = calculate_scores_and_subscales(processed_df, score_columns)
        
        # Step 6: Perform data quality checks
        perform_data_quality_checks(final_df)
        
        # Step 7: Save output file
        output_file = save_output_file(final_df)
        
        print("\n" + "="*50)
        print("VVIQ2 PROCESSING COMPLETED SUCCESSFULLY")
        print("="*50)
        print(f"Output file: {output_file}")
        print("Finished execution")
        
        return 0
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        print("Script failed to complete successfully")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
