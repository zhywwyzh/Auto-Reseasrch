#!/usr/bin/env python3
"""
VVIQ2 Data Processing and Cleaning Script

This script processes Vividness of Visual Imagery Questionnaire-2 (VVIQ2) data by:
1. Extracting numeric scores from text responses
2. Filtering to included participants
3. Applying exclusion criteria (missing data, invariant responding, extreme patterns)
4. Imputing missing data within subscales
5. Calculating total and subscale scores
"""

import pandas as pd
import numpy as np
import os
import glob
import re
from datetime import datetime

def create_outputs_folder():
    """
    Create outputs folder if it doesn't exist.
    """
    if not os.path.exists('outputs'):
        os.makedirs('outputs')
        print("Created 'outputs' folder")

def find_latest_file(pattern):
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
    
    # Sort by modification time, most recent first
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]

def extract_numeric_score(response_text):
    """
    Extract numeric score (1-5) from response text string.
    
    Parameters:
    response_text (str or float): Response text containing numeric score
    
    Returns:
    int or None: Extracted score if valid (1-5), None otherwise
    """
    if pd.isna(response_text):
        return None
    
    # Convert to string if not already
    text = str(response_text)
    
    # Find all digits 1-5 in the text
    matches = re.findall(r'[1-5]', text)
    
    if matches:
        # Take the first valid digit found
        score = int(matches[0])
        if 1 <= score <= 5:
            return score
    
    return None

def load_vviq2_data(filepath):
    """
    Load and process VVIQ2 data file.
    
    Parameters:
    filepath (str): Path to VVIQ2 CSV file
    
    Returns:
    pandas.DataFrame: Processed VVIQ2 data with numeric scores
    """
    print(f"Loading VVIQ2 data from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        # Strip whitespace from column names FIRST
        df.columns = df.columns.str.strip()
        print(f"VVIQ2 data loaded successfully. Shape: {df.shape}")
        
        # Print all columns
        print("VVIQ2 columns:")
        for i, col in enumerate(df.columns):
            print(f"  {i}: {col}")
        
        # Print first 3 rows
        print("\nFirst 3 rows of VVIQ2 data:")
        print(df.head(3))
        
        # Define metadata columns and get item columns (AFTER stripping whitespace)
        metadata_columns = ['Respondent ID', 'Collector ID', 'Start Date', 'End Date', 'IP Address', 
                            'Email Address', 'First Name', 'Last Name', 'Custom Data 1', 'PROLIFIC_PID']
        item_columns = [col for col in df.columns if col not in metadata_columns]
        
        if len(item_columns) != 32:
            raise ValueError(f"Expected exactly 32 VVIQ2 items, found {len(item_columns)}")
        
        print(f"Found {len(item_columns)} VVIQ2 item columns")
        
        # Extract numeric scores for each item
        for col in item_columns:
            print(f"Processing column: {col}")
            df[f"{col}_score"] = df[col].apply(extract_numeric_score)
        
        # Add debugging output: sample response text and extracted score for first participant
        print(f"\nDebugging score extraction for first participant:")
        for i, col in enumerate(item_columns[:3]):  # Show first 3 items
            sample_response = df.iloc[0][col]
            extracted_score = df.iloc[0][f"{col}_score"]
            print(f"Item {i+1}: '{sample_response}' -> Score: {extracted_score}")
        
        return df, item_columns
        
    except Exception as e:
        print(f"Error loading VVIQ2 data: {e}")
        raise

def load_included_participants(pattern):
    """
    Load included participants data.
    
    Parameters:
    pattern (str): File pattern for included participants
    
    Returns:
    pandas.DataFrame: Included participants data
    """
    filepath = find_latest_file(pattern)
    if filepath is None:
        raise FileNotFoundError(f"No files found matching pattern: {pattern}")
    
    print(f"Loading included participants from: {filepath}")
    
    try:
        df = pd.read_csv(filepath)
        print(f"Included participants data loaded successfully. Shape: {df.shape}")
        
        # Print all columns
        print("Included participants columns:")
        for col in df.columns:
            print(f"  {col}")
        
        # Print first 3 rows
        print("\nFirst 3 rows of included participants:")
        print(df.head(3))
        
        # Check required columns
        required_cols = ['participantId', 'included']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Required column '{col}' not found in included participants data")
        
        # Filter to included participants only
        included_df = df[df['included'] == True].copy()
        print(f"Number of included participants: {len(included_df)}")
        
        return included_df
        
    except Exception as e:
        print(f"Error loading included participants: {e}")
        raise

def apply_exclusion_criteria(df, item_columns, exclusions_log):
    """
    Apply VVIQ2-specific exclusion criteria.
    
    Parameters:
    df (pandas.DataFrame): VVIQ2 data with scores
    item_columns (list): List of VVIQ2 item column names
    exclusions_log (list): List to track exclusions
    
    Returns:
    pandas.DataFrame: Data after applying exclusions
    """
    print("\nApplying VVIQ2 exclusion criteria...")
    
    initial_count = len(df)
    print(f"Starting with {initial_count} participants")
    
    # Create score columns list
    score_columns = [f"{col}_score" for col in item_columns]
    
    # Initialize exclusion tracking columns
    df['excluded_VVIQ2'] = False
    df['exclusion_reason_VVIQ2'] = ''
    df['missing_items_count'] = 0
    df['max_response_frequency_percent'] = 0.0
    df['response_variance'] = 0.0
    
    # 1. Missing data criterion
    print("\n1. Checking missing data...")
    score_columns = [f"{col}_score" for col in item_columns]
    df['missing_items_count'] = df[score_columns].isnull().sum(axis=1)
    mask_missing = df['missing_items_count'] > 2
    df.loc[mask_missing, 'excluded_VVIQ2'] = True
    df.loc[mask_missing, 'exclusion_reason_VVIQ2'] = 'missing_data'
    
    missing_excluded = df[df['exclusion_reason_VVIQ2'] == 'missing_data']
    print(f"Participants excluded for missing data (>2 items): {len(missing_excluded)}")
    exclusions_log.append(['missing_data', len(missing_excluded), initial_count])
    
    # 2. Invalid responses criterion
    print("\n2. Checking invalid responses...")
    invalid_count = 0
    for idx, row in df.iterrows():
        if df.at[idx, 'excluded_VVIQ2']:
            continue
            
        scores = [row[col] for col in score_columns if not pd.isna(row[col])]
        invalid_scores = [score for score in scores if score < 1 or score > 5]
        
        if invalid_scores:
            df.at[idx, 'excluded_VVIQ2'] = True
            df.at[idx, 'exclusion_reason_VVIQ2'] = 'invalid_responses'
            invalid_count += 1
    
    print(f"Participants excluded for invalid responses: {invalid_count}")
    exclusions_log.append(['invalid_responses', invalid_count, initial_count])
    
    # 3. Invariant responding criterion
    print("\n3. Checking invariant responding...")
    invariant_count = 0
    for idx, row in df.iterrows():
        if df.at[idx, 'excluded_VVIQ2']:
            continue
            
        scores = [row[col] for col in score_columns if not pd.isna(row[col])]
        if len(scores) == 0:
            continue
            
        # Count frequency of each response
        unique_scores, counts = np.unique(scores, return_counts=True)
        max_frequency = max(counts)
        max_frequency_percent = (max_frequency / 32) * 100
        df.at[idx, 'max_response_frequency_percent'] = max_frequency_percent
        
        if max_frequency_percent > 90:
            df.at[idx, 'excluded_VVIQ2'] = True
            df.at[idx, 'exclusion_reason_VVIQ2'] = 'invariant_responding'
            invariant_count += 1
    
    print(f"Participants excluded for invariant responding (>90%): {invariant_count}")
    exclusions_log.append(['invariant_responding', invariant_count, initial_count])
    
    # 4. Extreme response patterns (low variance + high invariant responding)
    print("\n4. Checking extreme response patterns...")
    extreme_count = 0
    for idx, row in df.iterrows():
        if df.at[idx, 'excluded_VVIQ2']:
            continue
            
        scores = [row[col] for col in score_columns if not pd.isna(row[col])]
        if len(scores) < 2:
            continue
            
        variance = np.var(scores)
        df.at[idx, 'response_variance'] = variance
        
        # Exclude if variance < 0.5 AND invariant responding > 80%
        if variance < 0.5 and df.at[idx, 'max_response_frequency_percent'] > 80:
            df.at[idx, 'excluded_VVIQ2'] = True
            df.at[idx, 'exclusion_reason_VVIQ2'] = 'extreme_response_pattern'
            extreme_count += 1
    
    print(f"Participants excluded for extreme response patterns: {extreme_count}")
    exclusions_log.append(['extreme_response_pattern', extreme_count, initial_count])
    
    # Summary
    total_excluded = len(df[df['excluded_VVIQ2'] == True])
    remaining = len(df[df['excluded_VVIQ2'] == False])
    
    print(f"\nExclusion summary:")
    print(f"Total excluded: {total_excluded}")
    print(f"Remaining participants: {remaining}")

    # Print excluded participants details
    excluded_participants = df[df['excluded_VVIQ2'] == True]
    if len(excluded_participants) > 0:
        print(f"\nExcluded participants details:")
        for idx, row in excluded_participants.iterrows():
            print(f"  {row['PROLIFIC_PID']}: {row['exclusion_reason_VVIQ2']}")
    
    return df

def impute_missing_data(df, item_columns):
    """
    Apply missing data imputation using participant mean within subscale.
    
    Parameters:
    df (pandas.DataFrame): VVIQ2 data
    item_columns (list): List of VVIQ2 item column names
    
    Returns:
    pandas.DataFrame: Data with imputed values
    """
    print("\nApplying missing data imputation...")
    
    # Define subscales (4 items each, 8 subscales)
    subscales = {
        'familiar_person': item_columns[0:4],
        'sunrise': item_columns[4:8],
        'shop_front': item_columns[8:12],
        'countryside': item_columns[12:16],
        'driving': item_columns[16:20],
        'beach': item_columns[20:24],
        'railway_station': item_columns[24:28],
        'garden': item_columns[28:32]
    }
    
    score_columns = [f"{col}_score" for col in item_columns]
    subscale_scores = {name: [f"{col}_score" for col in cols] for name, cols in subscales.items()}
    
    imputation_count = 0
    
    for idx, row in df.iterrows():
        if df.at[idx, 'excluded_VVIQ2']:
            continue
            
        # Only impute for participants with ≤2 missing items
        if df.at[idx, 'missing_items_count'] <= 2:
            for subscale_name, subscale_score_cols in subscale_scores.items():
                # Get scores for this subscale
                subscale_values = [row[col] for col in subscale_score_cols]
                missing_indices = [i for i, val in enumerate(subscale_values) if pd.isna(val)]
                
                if missing_indices:
                    # Calculate mean of available items in this subscale
                    available_values = [val for val in subscale_values if not pd.isna(val)]
                    if available_values:
                        subscale_mean = np.mean(available_values)
                        imputed_value = round(subscale_mean)
                        
                        # Impute missing values
                        for missing_idx in missing_indices:
                            col_name = subscale_score_cols[missing_idx]
                            df.at[idx, col_name] = imputed_value
                            imputation_count += 1
                            print(f"Imputed {col_name} for participant {row['PROLIFIC_PID']}: {imputed_value}")
    
    print(f"Total imputations performed: {imputation_count}")
    return df

def calculate_vviq2_scores(df, item_columns):
    """
    Calculate VVIQ2 total and subscale scores.
    
    Parameters:
    df (pandas.DataFrame): VVIQ2 data with scores
    item_columns (list): List of VVIQ2 item column names
    
    Returns:
    pandas.DataFrame: Data with calculated scores
    """
    print("\nCalculating VVIQ2 scores...")
    
    score_columns = [f"{col}_score" for col in item_columns]
    
    # Define subscales
    subscales = {
        'familiar_person_score': score_columns[0:4],
        'sunrise_score': score_columns[4:8],
        'shop_front_score': score_columns[8:12],
        'countryside_score': score_columns[12:16],
        'driving_score': score_columns[16:20],
        'beach_score': score_columns[20:24],
        'railway_station_score': score_columns[24:28],
        'garden_score': score_columns[28:32]
    }
    
    for idx, row in df.iterrows():
        if df.at[idx, 'excluded_VVIQ2']:
            # Set scores to NaN for excluded participants
            df.at[idx, 'total_score'] = np.nan
            for subscale_name in subscales.keys():
                df.at[idx, subscale_name] = np.nan
        else:
            # Calculate total score
            total_scores = [row[col] for col in score_columns if not pd.isna(row[col])]
            if len(total_scores) == 32:  # All items present after imputation
                df.at[idx, 'total_score'] = sum(total_scores)
            else:
                df.at[idx, 'total_score'] = np.nan
            
            # Calculate subscale scores
            for subscale_name, subscale_cols in subscales.items():
                subscale_values = [row[col] for col in subscale_cols if not pd.isna(row[col])]
                if len(subscale_values) == 4:  # All 4 items present
                    df.at[idx, subscale_name] = sum(subscale_values)
                else:
                    df.at[idx, subscale_name] = np.nan
    
    # Validate score ranges for non-excluded participants
    valid_data = df[df['excluded_VVIQ2'] == False]
    
    if len(valid_data) > 0:
        # Check total score range (32-160)
        total_scores = valid_data['total_score'].dropna()
        if len(total_scores) > 0:
            print(f"Total score range: {total_scores.min()} - {total_scores.max()}")
            if total_scores.min() < 32 or total_scores.max() > 160:
                print("Warning: Total scores outside expected range (32-160)")
        
        # Check subscale score ranges (4-20)
        for subscale_name in subscales.keys():
            subscale_scores = valid_data[subscale_name].dropna()
            if len(subscale_scores) > 0:
                print(f"{subscale_name} range: {subscale_scores.min()} - {subscale_scores.max()}")
                if subscale_scores.min() < 4 or subscale_scores.max() > 20:
                    print(f"Warning: {subscale_name} outside expected range (4-20)")
    
    return df

def save_outputs(df, exclusions_log):
    """
    Save output files with timestamp.
    
    Parameters:
    df (pandas.DataFrame): Processed VVIQ2 data
    exclusions_log (list): List of exclusion criteria and counts
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save exclusion log
    exclusion_df = pd.DataFrame(exclusions_log, columns=['exclusion_criterion', 'excluded_count', 'total_participants_screened'])
    exclusion_file = f"outputs/VVIQ2_exclusion_log_{timestamp}.csv"
    exclusion_df.to_csv(exclusion_file, index=False)
    print(f"\nSaved exclusion log to: {exclusion_file}")
    print("Exclusion log contents:")
    print(exclusion_df)

    # Print summary of excluded participants
    excluded_df = df[df['excluded_VVIQ2'] == True]
    if len(excluded_df) > 0:
        print(f"\nExcluded participants summary:")
        exclusion_reasons = excluded_df['exclusion_reason_VVIQ2'].value_counts()
        for reason, count in exclusion_reasons.items():
            print(f"  {reason}: {count} participants")
    
    # Prepare cleaned scores output
    output_columns = [
        'participantId', 'total_score', 'familiar_person_score', 'sunrise_score',
        'shop_front_score', 'countryside_score', 'driving_score', 'beach_score',
        'railway_station_score', 'garden_score', 'excluded_VVIQ2', 'exclusion_reason_VVIQ2',
        'missing_items_count', 'max_response_frequency_percent', 'response_variance'
    ]
    
    # Create output dataframe
    output_df = pd.DataFrame()
    output_df['participantId'] = df['PROLIFIC_PID']
    
    # Copy score columns
    for col in output_columns[1:]:
        if col in df.columns:
            output_df[col] = df[col]
        else:
            output_df[col] = np.nan
    
    # Convert integer columns
    int_columns = ['total_score', 'familiar_person_score', 'sunrise_score', 'shop_front_score',
                   'countryside_score', 'driving_score', 'beach_score', 'railway_station_score',
                   'garden_score', 'missing_items_count']
    
    for col in int_columns:
        output_df[col] = pd.to_numeric(output_df[col], errors='coerce').astype('Int64')
    
    # Save cleaned scores
    scores_file = f"outputs/VVIQ2_cleaned_scores_{timestamp}.csv"
    output_df.to_csv(scores_file, index=False)
    print(f"\nSaved cleaned scores to: {scores_file}")
    
    # Print output summary
    print(f"\nOutput data shape: {output_df.shape}")
    print("Output columns:")
    for col in output_df.columns:
        print(f"  {col}")
    
    print("\nFirst 2 rows of output:")
    print(output_df.head(2))
    
    # Print final summary statistics
    excluded_count = len(output_df[output_df['excluded_VVIQ2'] == True])
    included_count = len(output_df[output_df['excluded_VVIQ2'] == False])
    
    print(f"\nFinal summary:")
    print(f"Total participants processed: {len(output_df)}")
    print(f"Excluded participants: {excluded_count}")
    print(f"Included participants: {included_count}")

def main():
    """
    Main function to execute VVIQ2 data processing pipeline.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting VVIQ2 data processing...")
        
        # Create outputs folder
        create_outputs_folder()
        
        # Load VVIQ2 data
        vviq2_file = "../C_results/data/Vividness of Visual Imagery Questionnaire-2.csv"
        vviq2_df, item_columns = load_vviq2_data(vviq2_file)
        
        # Load included participants
        included_pattern = "outputs/included_participants_*.csv"
        included_df = load_included_participants(included_pattern)
        
        # Merge datasets
        print(f"\nMerging datasets...")
        print(f"VVIQ2 participants: {len(vviq2_df)}")
        print(f"Included participants: {len(included_df)}")
        
        merged_df = pd.merge(vviq2_df, included_df[['participantId']], 
                           left_on='PROLIFIC_PID', right_on='participantId', how='inner')
        print(f"Merged participants: {len(merged_df)}")
        
        # Initialize exclusions log
        exclusions_log = []
        
        # Apply exclusion criteria
        processed_df = apply_exclusion_criteria(merged_df, item_columns, exclusions_log)
        
        # Apply missing data imputation
        imputed_df = impute_missing_data(processed_df, item_columns)
        
        # Calculate VVIQ2 scores
        final_df = calculate_vviq2_scores(imputed_df, item_columns)
        
        # Save outputs
        save_outputs(final_df, exclusions_log)

        # Print comprehensive final summary
        print(f"\n" + "="*60)
        print("FINAL PROCESSING SUMMARY")
        print("="*60)
        print(f"Initial VVIQ2 data loaded: {len(vviq2_df)} participants")
        print(f"Included participants from screening: {len(included_df)} participants")
        print(f"Participants after merging: {len(merged_df)} participants")
        print(f"\nExclusion criteria results:")
        for criterion, count, total in exclusions_log:
            print(f"  {criterion}: {count} excluded (from {total} screened)")
        print(f"\nFinal results:")
        print(f"  Total excluded: {len(final_df[final_df['excluded_VVIQ2'] == True])}")
        print(f"  Final included: {len(final_df[final_df['excluded_VVIQ2'] == False])}")
        print("="*60)

        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
