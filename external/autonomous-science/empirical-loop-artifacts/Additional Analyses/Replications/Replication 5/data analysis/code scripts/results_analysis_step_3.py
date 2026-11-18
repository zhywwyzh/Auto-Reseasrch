import pandas as pd
import numpy as np
import re
import os
from datetime import datetime
import sys

def extract_numeric_score(text_response):
    """
    Extract numeric score from text response using regex pattern.
    
    Parameters:
    text_response (str): Text response containing numeric score
    
    Returns:
    int or None: Extracted score (1-5) or None if invalid
    """
    if pd.isna(text_response):
        return None
    
    # Convert to string and find digits 1-5
    text_str = str(text_response)
    pattern = r'[1-5]'
    matches = re.findall(pattern, text_str)
    
    if matches:
        score = int(matches[0])  # Take first match
        if 1 <= score <= 5:
            return score
    
    return None

def count_missing_responses(row, vviq_columns):
    """
    Count missing responses across VVIQ columns for a participant.
    
    Parameters:
    row (pd.Series): Participant data row
    vviq_columns (list): List of VVIQ column names
    
    Returns:
    int: Count of missing responses
    """
    missing_count = 0
    for col in vviq_columns:
        if pd.isna(row[col]):
            missing_count += 1
    return missing_count

def calculate_invariant_response_percent(row, vviq_columns):
    """
    Calculate percentage of identical responses for a participant.
    
    Parameters:
    row (pd.Series): Participant data row
    vviq_columns (list): List of VVIQ column names
    
    Returns:
    float: Percentage of most common response
    """
    scores = []
    for col in vviq_columns:
        if not pd.isna(row[col]):
            scores.append(row[col])
    
    if len(scores) == 0:
        return 0
    
    # Count occurrences of each score
    score_counts = {}
    for score in scores:
        score_counts[score] = score_counts.get(score, 0) + 1
    
    max_count = max(score_counts.values())
    return (max_count / len(scores)) * 100

def detect_alternating_pattern(row, vviq_columns):
    """
    Detect alternating pattern responses (consecutive differences of ±1 for ≥16 items).
    
    Parameters:
    row (pd.Series): Participant data row
    vviq_columns (list): List of VVIQ column names
    
    Returns:
    bool: True if alternating pattern detected
    """
    scores = []
    for col in vviq_columns:
        if not pd.isna(row[col]):
            scores.append(row[col])
    
    if len(scores) < 16:
        return False
    
    consecutive_alternating = 0
    max_consecutive = 0
    
    for i in range(1, len(scores)):
        diff = abs(scores[i] - scores[i-1])
        if diff == 1:
            consecutive_alternating += 1
            max_consecutive = max(max_consecutive, consecutive_alternating)
        else:
            consecutive_alternating = 0
    
    return max_consecutive >= 15  # 15 differences means 16 consecutive items


def main():
    """
    Main function to process VVIQ2 data with exclusion criteria and score calculation.
    
    Returns:
    int: 0 for success, 1 for error
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
        
        if not os.path.exists(input_file):
            print(f"Error: Input file {input_file} not found")
            return 1
        
        df = pd.read_csv(input_file)
        print(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
        
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Calculate completion_time_seconds from Start Date and End Date
        if 'Start Date' in df.columns and 'End Date' in df.columns:
            print("Calculating completion_time_seconds from Start Date and End Date...")
            df['Start Date'] = pd.to_datetime(df['Start Date'])
            df['End Date'] = pd.to_datetime(df['End Date'])
            df['completion_time_seconds'] = (df['End Date'] - df['Start Date']).dt.total_seconds()
            print(f"Completion time calculated - range: {df['completion_time_seconds'].min()} to {df['completion_time_seconds'].max()}")
        else:
            print("Warning: Start Date or End Date columns not found, setting completion_time_seconds to None")
            df['completion_time_seconds'] = None

        # Map actual VVIQ columns to standardized format
        # The VVIQ items are in columns 9-40 (32 items total)
        vviq_actual_columns = df.columns[9:41].tolist()
        print(f"Found {len(vviq_actual_columns)} VVIQ columns")
        print("First 3 VVIQ columns:", vviq_actual_columns[:3])

        # Create mapping and rename columns
        vviq_column_mapping = {actual: f'VVIQ2_{i}' for i, actual in enumerate(vviq_actual_columns, 1)}
        df = df.rename(columns=vviq_column_mapping)
        print("Renamed VVIQ columns to standardized format")

        # Required columns (now using renamed columns)
        required_columns = ['PROLIFIC_PID'] + [f'VVIQ2_{i}' for i in range(1, 33)] + ['completion_time_seconds']
        vviq_columns = [f'VVIQ2_{i}' for i in range(1, 33)]

        # Check for required columns
        missing_columns = []
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            print(f"Error: Missing required columns: {missing_columns}")
            return 1

        print("All required columns found after mapping")

        # Print all columns
        print("All columns in dataset:")
        print(df.columns.tolist())
        
        # Print first 3 rows
        print("\nFirst 3 rows of data:")
        print(df.head(3))
        
        # Extract numeric scores from text responses
        print("\nExtracting numeric scores from text responses...")
        for col in vviq_columns:
            print(f"Processing column {col}")
            df[col] = df[col].apply(extract_numeric_score)
        
        print("Numeric score extraction completed")
        
        # Validate numeric extraction with sample raw data
        print("\nValidating numeric extraction with sample raw data:")
        sample_cols = vviq_columns[:3]
        for col in sample_cols:
            print(f"Extracted {col} sample values:")
            print(df[col].head(3).tolist())
            print()
        
        # Print unique values for VVIQ columns (sample a few)
        print("\nSample of extracted VVIQ scores:")
        for col in vviq_columns[:5]:  # Print first 5 columns
            unique_vals = df[col].dropna().unique()
            print(f"{col} unique values: {sorted(unique_vals)}")
        
        # Print completion time info
        print(f"\nCompletion time - type: {df['completion_time_seconds'].dtype}")
        print(f"Completion time - range: {df['completion_time_seconds'].min()} to {df['completion_time_seconds'].max()}")
        
        # Initialize exclusion tracking
        exclusion_log = []
        df['excluded'] = False
        df['exclusion_reason'] = ''
        
        initial_count = len(df)
        print(f"\nStarting with {initial_count} participants")
        
        # Exclusion criterion d: Missing PROLIFIC_PID or completion_time_seconds
        print("\nApplying exclusion criterion d: Incomplete questionnaire data...")
        missing_pid = df['PROLIFIC_PID'].isna()
        missing_time = df['completion_time_seconds'].isna()
        incomplete_data = missing_pid | missing_time
        
        excluded_incomplete = incomplete_data.sum()
        df.loc[incomplete_data, 'excluded'] = True
        df.loc[incomplete_data, 'exclusion_reason'] = 'Missing PROLIFIC_PID or completion_time'
        
        print(f"Excluded {excluded_incomplete} participants for incomplete questionnaire data")
        exclusion_log.append({
            'exclusion_criterion': 'Incomplete questionnaire data',
            'participants_excluded': excluded_incomplete,
            'description': 'Missing PROLIFIC_PID or completion_time_seconds'
        })
        
        # Calculate missing items count for all participants
        print("\nCalculating missing items count...")
        df['missing_items_count'] = df.apply(lambda row: count_missing_responses(row, vviq_columns), axis=1)
        
        # Exclusion criterion a: Incomplete submissions (>2 missing items)
        print("\nApplying exclusion criterion a: Incomplete submissions...")
        incomplete_submissions = (df['missing_items_count'] > 2) & (~df['excluded'])
        excluded_incomplete_sub = incomplete_submissions.sum()
        df.loc[incomplete_submissions, 'excluded'] = True
        df.loc[incomplete_submissions, 'exclusion_reason'] = 'Incomplete submissions (>2 missing items)'
        
        print(f"Excluded {excluded_incomplete_sub} participants for incomplete submissions")
        exclusion_log.append({
            'exclusion_criterion': 'Incomplete submissions',
            'participants_excluded': excluded_incomplete_sub,
            'description': 'Missing responses to >2 items (>6.25% missing data)'
        })
        
        # Calculate invariant response percentage
        print("\nCalculating invariant response percentages...")
        df['invariant_response_percent'] = df.apply(lambda row: calculate_invariant_response_percent(row, vviq_columns), axis=1)
        
        # Exclusion criterion b: Invariant responding
        print("\nApplying exclusion criterion b: Invariant responding...")
        invariant_responding = (df['invariant_response_percent'] >= 87.5) & (df['completion_time_seconds'].notna()) & (df['completion_time_seconds'] < 180) & (~df['excluded'])
        excluded_invariant = invariant_responding.sum()
        df.loc[invariant_responding, 'excluded'] = True
        df.loc[invariant_responding, 'exclusion_reason'] = 'Invariant responding (≥87.5% same rating, <180s)'
        
        print(f"Excluded {excluded_invariant} participants for invariant responding")
        exclusion_log.append({
            'exclusion_criterion': 'Invariant responding',
            'participants_excluded': excluded_invariant,
            'description': 'Same rating for ≥28/32 items (≥87.5%) AND completion_time_seconds <180'
        })
        
        # Exclusion criterion c: Careless responding (alternating patterns)
        print("\nApplying exclusion criterion c: Careless responding...")
        df['alternating_pattern'] = df.apply(lambda row: detect_alternating_pattern(row, vviq_columns), axis=1)
        careless_responding = df['alternating_pattern'] & (df['completion_time_seconds'].notna()) & (df['completion_time_seconds'] < 240) & (~df['excluded'])
        excluded_careless = careless_responding.sum()
        df.loc[careless_responding, 'excluded'] = True
        df.loc[careless_responding, 'exclusion_reason'] = 'Careless responding (alternating pattern, <240s)'
        
        print(f"Excluded {excluded_careless} participants for careless responding")
        exclusion_log.append({
            'exclusion_criterion': 'Careless responding',
            'participants_excluded': excluded_careless,
            'description': 'Alternating pattern responses (≥16 consecutive items) AND completion_time_seconds <240'
        })
        
        # Calculate total scores for remaining participants
        print("\nCalculating total VVIQ2 scores...")
        # For included participants with ≤2 missing items, calculate sum of available responses
        included_mask = ~df['excluded']
        df.loc[included_mask, 'total_score'] = df.loc[included_mask, vviq_columns].sum(axis=1, skipna=True)
        # Set to None only if all VVIQ responses are missing
        all_missing_mask = df[vviq_columns].isna().all(axis=1)
        df.loc[all_missing_mask, 'total_score'] = None

        # Calculate subscale scores using vectorized operations
        print("\nCalculating subscale scores...")
        subscales = {
            'familiar_person_score': [f'VVIQ2_{i}' for i in range(1, 5)],
            'sunrise_score': [f'VVIQ2_{i}' for i in range(5, 9)],
            'shop_front_score': [f'VVIQ2_{i}' for i in range(9, 13)],
            'countryside_score': [f'VVIQ2_{i}' for i in range(13, 17)],
            'driving_score': [f'VVIQ2_{i}' for i in range(17, 21)],
            'beach_score': [f'VVIQ2_{i}' for i in range(21, 25)],
            'railway_station_score': [f'VVIQ2_{i}' for i in range(25, 29)],
            'garden_scene_score': [f'VVIQ2_{i}' for i in range(29, 33)]
        }

        for subscale_name, columns in subscales.items():
            # Calculate sum for included participants using available items
            df.loc[included_mask, subscale_name] = df.loc[included_mask, columns].sum(axis=1, skipna=True)
            # Only set to None if ALL items in subscale are missing or participant is excluded
            all_missing_in_subscale = df[columns].isna().all(axis=1)
            df.loc[all_missing_in_subscale | df['excluded'], subscale_name] = None

        subscale_columns = list(subscales.keys())
        
        # Exclusion criterion: Extreme total scores (>2.5 SD from mean)
        print("\nApplying exclusion for extreme total scores...")
        valid_scores = df[~df['excluded'] & df['total_score'].notna()]['total_score']
        
        if len(valid_scores) > 0:
            mean_score = valid_scores.mean()
            std_score = valid_scores.std()
            print(f"Total score statistics - Mean: {mean_score:.2f}, SD: {std_score:.2f}")
            
            lower_bound = mean_score - 2.5 * std_score
            upper_bound = mean_score + 2.5 * std_score
            print(f"Extreme score bounds: {lower_bound:.2f} to {upper_bound:.2f}")
            
            extreme_scores = ((df['total_score'] < lower_bound) | (df['total_score'] > upper_bound)) & (~df['excluded']) & df['total_score'].notna()
            excluded_extreme = extreme_scores.sum()
            df.loc[extreme_scores, 'excluded'] = True
            df.loc[extreme_scores, 'exclusion_reason'] = 'Extreme total score (>2.5 SD from mean)'
            
            print(f"Excluded {excluded_extreme} participants for extreme total scores")
            exclusion_log.append({
                'exclusion_criterion': 'Extreme total scores',
                'participants_excluded': excluded_extreme,
                'description': 'Total scores >2.5 SD from group mean'
            })
        
        # Final participant count
        final_count = (~df['excluded']).sum()
        total_excluded = initial_count - final_count
        print(f"\nFinal results:")
        print(f"Initial participants: {initial_count}")
        print(f"Total excluded: {total_excluded}")
        print(f"Final participants: {final_count}")
        
        # Validate score ranges for included participants
        print("\nValidating score ranges for included participants...")
        included_df = df[~df['excluded']]
        
        if len(included_df) > 0:
            total_range = included_df['total_score'].dropna()
            if len(total_range) > 0:
                print(f"Total score range: {total_range.min()} to {total_range.max()} (expected: 32-160)")
            
            for subscale in subscale_columns:
                subscale_range = included_df[subscale].dropna()
                if len(subscale_range) > 0:
                    print(f"{subscale} range: {subscale_range.min()} to {subscale_range.max()} (expected: 4-20)")
        
        # Prepare output dataframes
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Main output file
        output_columns = ['PROLIFIC_PID', 'total_score', 'familiar_person_score', 'sunrise_score', 'shop_front_score',
                         'countryside_score', 'driving_score', 'beach_score', 'railway_station_score', 'garden_scene_score',
                         'excluded', 'exclusion_reason', 'completion_time_seconds', 'missing_items_count', 'invariant_response_percent']
        
        output_df = df[output_columns].copy()
        
        # Convert score columns to nullable integer type
        score_columns = ['total_score'] + subscale_columns
        for col in score_columns:
            if col in output_df.columns:
                output_df[col] = output_df[col].astype('Int64')
        
        output_file = f'outputs/VVIQ2_cleaned_scores_{timestamp}.csv'
        output_df.to_csv(output_file, index=False)
        print(f"\nSaved main output to: {output_file}")
        
        # Print sample of output
        print("\nSample of output data:")
        print("All output columns:")
        print(output_df.columns.tolist())
        print("\nFirst 2 rows:")
        print(output_df.head(2))
        
        # Exclusion log file
        exclusion_df = pd.DataFrame(exclusion_log)
        exclusion_file = f'outputs/VVIQ2_exclusion_log_{timestamp}.csv'
        exclusion_df.to_csv(exclusion_file, index=False)
        print(f"\nSaved exclusion log to: {exclusion_file}")
        
        print("\nExclusion log:")
        print("All exclusion log columns:")
        print(exclusion_df.columns.tolist())
        print("\nFirst 2 rows:")
        print(exclusion_df.head(2))
        
        # Print detailed exclusion summary
        print(f"\n{'='*50}")
        print("DETAILED EXCLUSION SUMMARY")
        print(f"{'='*50}")
        print(f"Data found for {initial_count} participants")
        for log_entry in exclusion_log:
            print(f"- {log_entry['exclusion_criterion']}: {log_entry['participants_excluded']} participants")
            print(f"  ({log_entry['description']})")
        print(f"Final dataset: {final_count} participants after exclusions")
        print(f"Total excluded: {total_excluded} participants ({(total_excluded/initial_count)*100:.1f}%)")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
