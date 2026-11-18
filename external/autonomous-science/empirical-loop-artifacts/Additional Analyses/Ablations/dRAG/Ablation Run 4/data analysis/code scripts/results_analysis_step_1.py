#!/usr/bin/env python3
"""
Sample Statistics Calculation Script

This script calculates comprehensive sample characteristics and data quality indicators
from Prolific demographic data and cognitive task data files.
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
from datetime import datetime
import re


def convert_duration_to_seconds(duration_str):
    """
    Convert duration string to total seconds.
    
    Args:
        duration_str: Duration string in various formats (HH:MM:SS, MM:SS, or numeric)
    
    Returns:
        float: Duration in seconds, or original value if already numeric
    """
    if pd.isna(duration_str) or duration_str == '':
        return 0.0
    
    # If it's already a number, return as is
    try:
        return float(duration_str)
    except (ValueError, TypeError):
        pass
    
    # Try to parse as time format
    duration_str = str(duration_str).strip()
    
    # Handle HH:MM:SS format
    if ':' in duration_str:
        parts = duration_str.split(':')
        if len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = map(float, parts)
            return hours * 3600 + minutes * 60 + seconds
        elif len(parts) == 2:  # MM:SS
            minutes, seconds = map(float, parts)
            return minutes * 60 + seconds
    
    # If all else fails, try to convert to float
    try:
        return float(duration_str)
    except:
        return 0.0


def load_prolific_data():
    """
    Load and process Prolific demographic data.
    
    Returns:
        pd.DataFrame: Processed Prolific data with required columns
    """
    print("Loading Prolific demographic data...")
    
    # Find prolific export files
    prolific_files = glob.glob("../C_results/data/prolific_export_*.csv")
    print(f"Found {len(prolific_files)} prolific export files: {prolific_files}")
    
    if not prolific_files:
        raise FileNotFoundError("No prolific export files found matching pattern")
    
    # Use the most recent file if multiple exist
    prolific_file = max(prolific_files, key=os.path.getctime)
    print(f"Using prolific file: {prolific_file}")
    
    # Load the file
    prolific_df = pd.read_csv(prolific_file)
    prolific_df.columns = prolific_df.columns.str.strip()
    print(f"Loaded prolific data with shape: {prolific_df.shape}")
    print("Prolific data columns:")
    print(prolific_df.columns.tolist())
    print("First 3 rows of prolific data:")
    print(prolific_df.head(3))
    
    # Check required columns
    required_cols = ['Submission id', 'Participant id', 'Status', 'Started at', 
                    'Completed at', 'Time taken', 'Age', 'Sex', 'Total approvals']
    
    missing_cols = [col for col in required_cols if col not in prolific_df.columns]
    if missing_cols:
        print(f"Warning: Missing columns in prolific data: {missing_cols}")
    
    # Print unique values for key categorical columns
    if 'Status' in prolific_df.columns:
        print("Unique Status values:")
        print(prolific_df['Status'].unique())
    
    if 'Sex' in prolific_df.columns:
        print("Unique Sex values:")
        print(prolific_df['Sex'].unique())
    
    return prolific_df


def load_cognitive_task_data():
    """
    Load cognitive task data files and extract participant IDs and focus metrics.
    
    Returns:
        tuple: (participant_ids_set, focus_metrics_df)
    """
    print("Loading cognitive task data...")
    
    # Find cognitive task files
    task_files = glob.glob("../C_results/data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv")
    print(f"Found {len(task_files)} cognitive task files")
    
    if not task_files:
        raise FileNotFoundError("No cognitive task files found matching pattern")
    
    participant_ids = set()
    focus_metrics_list = []
    
    for file_path in task_files:
        print(f"Processing file: {file_path}")
        
        try:
            # Load the file
            df = pd.read_csv(file_path)
            # Strip whitespace from column headers BEFORE checking required columns
            df.columns = df.columns.str.strip()
            print(f"File shape: {df.shape}")
            print("File columns:")
            print(df.columns.tolist())
            print("First 3 rows:")
            print(df.head(3))

            # Check required columns
            required_cols = ['participantId', 'windowFocusLostDuringTasksNum', 
                           'windowFocusLostDuringInfoNum', 'windowFocusLostDuringTasksDuration',
                           'windowFocusLostDuringInfoDuration']

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Warning: Missing columns in file {file_path}: {missing_cols}")
                continue
            
            # Extract unique participant IDs
            if 'participantId' in df.columns:
                file_participant_ids = df['participantId'].dropna().unique()
                participant_ids.update(file_participant_ids)
                print(f"Found {len(file_participant_ids)} unique participant IDs in file")
            
            # Extract focus metrics from first row per participant
            if all(col in df.columns for col in required_cols):
                # Get first row for each participant
                first_rows = df.groupby('participantId').first().reset_index()
                
                for _, row in first_rows.iterrows():
                    participant_id = row['participantId']
                    
                    # Extract focus metrics
                    focus_data = {
                        'participantId': participant_id,
                        'windowFocusLostDuringTasksNum': row['windowFocusLostDuringTasksNum'],
                        'windowFocusLostDuringInfoNum': row['windowFocusLostDuringInfoNum'],
                        'windowFocusLostDuringTasksDuration': row['windowFocusLostDuringTasksDuration'],
                        'windowFocusLostDuringInfoDuration': row['windowFocusLostDuringInfoDuration']
                    }
                    focus_metrics_list.append(focus_data)
            
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
            continue
    
    print(f"Total unique participant IDs found: {len(participant_ids)}")
    print(f"Focus metrics extracted for {len(focus_metrics_list)} participants")
    
    # Create focus metrics dataframe
    focus_metrics_df = pd.DataFrame(focus_metrics_list)
    if not focus_metrics_df.empty:
        initial_count = len(focus_metrics_df)
        focus_metrics_df.drop_duplicates(subset=['participantId'], keep='first', inplace=True)
        print(f"Removed {initial_count - len(focus_metrics_df)} duplicate participant entries from focus metrics.")
        print("Focus metrics dataframe columns:")
        print(focus_metrics_df.columns.tolist())
        print("First 2 rows of focus metrics:")
        print(focus_metrics_df.head(2))
    
    return participant_ids, focus_metrics_df


def calculate_sample_characteristics(prolific_df):
    """
    Calculate sample characteristics from prolific data.
    
    Args:
        prolific_df (pd.DataFrame): Prolific demographic data
    
    Returns:
        list: List of dictionaries containing metric statistics
    """
    print("Calculating sample characteristics...")
    
    metrics = []
    
    # Total recruited participants (all statuses)
    total_recruited = prolific_df['Participant id'].nunique()
    metrics.append({
        'metric_name': 'total_recruited_participants',
        'metric_value': total_recruited,
        'additional_info': 'All participants regardless of status'
    })
    print(f"Total recruited participants: {total_recruited}")
    
    # Filter for approved participants only
    approved_df = prolific_df[prolific_df['Status'] == 'APPROVED'].copy()
    print(f"Approved participants: {len(approved_df)}")
    
    # Total approved participants
    total_approved = approved_df['Participant id'].nunique()
    metrics.append({
        'metric_name': 'total_approved_participants',
        'metric_value': total_approved,
        'additional_info': 'Participants with APPROVED status'
    })
    print(f"Total approved participants: {total_approved}")
    
    # Age statistics (for approved participants)
    if 'Age' in approved_df.columns and not approved_df['Age'].empty:
        age_data = approved_df['Age'].dropna()
        
        if len(age_data) > 0:
            mean_age = age_data.mean()
            std_age = age_data.std()
            min_age = age_data.min()
            max_age = age_data.max()
            
            metrics.extend([
                {
                    'metric_name': 'mean_age',
                    'metric_value': round(mean_age, 2),
                    'additional_info': 'Mean age of approved participants'
                },
                {
                    'metric_name': 'std_age',
                    'metric_value': round(std_age, 2),
                    'additional_info': 'Standard deviation of age'
                },
                {
                    'metric_name': 'min_age',
                    'metric_value': min_age,
                    'additional_info': 'Minimum age'
                },
                {
                    'metric_name': 'max_age',
                    'metric_value': max_age,
                    'additional_info': 'Maximum age'
                }
            ])
            
            print(f"Age statistics: Mean={mean_age:.2f}, SD={std_age:.2f}, Range={min_age}-{max_age}")
    
    # Sex distribution (for approved participants)
    if 'Sex' in approved_df.columns and not approved_df['Sex'].empty:
        sex_counts = approved_df['Sex'].value_counts()
        total_with_sex = sex_counts.sum()
        
        for sex, count in sex_counts.items():
            percentage = (count / total_with_sex) * 100
            clean_sex = sex.lower().replace(" ", "_")
            metrics.extend([
                {
                    'metric_name': f'sex_count_{clean_sex}',
                    'metric_value': count,
                    'additional_info': f'Count of {sex} participants'
                },
                {
                    'metric_name': f'sex_percentage_{clean_sex}',
                    'metric_value': round(percentage, 2),
                    'additional_info': f'Percentage of {sex} participants'
                }
            ])
            print(f"Sex distribution: {sex} = {count} ({percentage:.2f}%)")
    
    return metrics


def calculate_data_quality_indicators(prolific_df, participant_ids, focus_metrics_df):
    """
    Calculate data quality indicators.
    
    Args:
        prolific_df (pd.DataFrame): Prolific demographic data
        participant_ids (set): Set of participant IDs from cognitive task data
        focus_metrics_df (pd.DataFrame): Focus metrics data
    
    Returns:
        list: List of dictionaries containing quality metrics
    """
    print("Calculating data quality indicators...")
    
    metrics = []
    
    # Overall completion rate
    total_recruited = prolific_df['Participant id'].nunique()
    completed_with_data = len(participant_ids)
    completion_rate = (completed_with_data / total_recruited) * 100 if total_recruited > 0 else 0
    
    metrics.append({
        'metric_name': 'completion_rate',
        'metric_value': round(completion_rate, 2),
        'additional_info': 'Percentage of recruited participants with cognitive task data'
    })
    print(f"Completion rate: {completion_rate:.2f}% ({completed_with_data}/{total_recruited})")
    
    # Session duration statistics (for completed participants with both prolific and cognitive data)
    approved_df = prolific_df[prolific_df['Status'] == 'APPROVED'].copy()
    completed_df = approved_df[approved_df['Participant id'].isin(participant_ids)]
    print(f"Calculating session duration for {len(completed_df)} completed participants (with both prolific and cognitive data).")

    if 'Time taken' in completed_df.columns and not completed_df['Time taken'].empty:
        # Convert time taken from seconds to minutes
        time_data = completed_df['Time taken'].dropna()
        time_minutes = time_data / 60  # Convert to minutes

        if len(time_minutes) > 0:
            mean_duration = time_minutes.mean()
            std_duration = time_minutes.std()

            metrics.extend([
                {
                    'metric_name': 'mean_session_duration_minutes',
                    'metric_value': round(mean_duration, 2),
                    'additional_info': 'Mean session duration in minutes for completed participants with both prolific and cognitive data'
                },
                {
                    'metric_name': 'std_session_duration_minutes',
                    'metric_value': round(std_duration, 2),
                    'additional_info': 'Standard deviation of session duration in minutes for completed participants with both prolific and cognitive data'
                }
            ])

            print(f"Session duration (completed participants): Mean={mean_duration:.2f} min, SD={std_duration:.2f} min")
    
    # Focus loss metrics
    if not focus_metrics_df.empty:
        focus_cols = ['windowFocusLostDuringTasksNum', 'windowFocusLostDuringInfoNum',
                     'windowFocusLostDuringTasksDuration', 'windowFocusLostDuringInfoDuration']
        
        for col in focus_cols:
            if col in focus_metrics_df.columns:
                data = focus_metrics_df[col].dropna()
                
                # Convert duration columns to seconds if needed
                if 'Duration' in col:
                    data = data.apply(convert_duration_to_seconds)
                
                if len(data) > 0:
                    mean_val = data.mean()
                    std_val = data.std()
                    min_val = data.min()
                    max_val = data.max()
                    
                    metrics.extend([
                        {
                            'metric_name': f'mean_{col}',
                            'metric_value': round(mean_val, 2),
                            'additional_info': f'Mean {col}'
                        },
                        {
                            'metric_name': f'std_{col}',
                            'metric_value': round(std_val, 2),
                            'additional_info': f'Standard deviation {col}'
                        },
                        {
                            'metric_name': f'min_{col}',
                            'metric_value': round(min_val, 2),
                            'additional_info': f'Minimum {col}'
                        },
                        {
                            'metric_name': f'max_{col}',
                            'metric_value': round(max_val, 2),
                            'additional_info': f'Maximum {col}'
                        }
                    ])
                    
                    print(f"{col}: Mean={mean_val:.2f}, SD={std_val:.2f}, Range={min_val:.2f}-{max_val:.2f}")
    
    return metrics


def perform_validation_checks(prolific_df, participant_ids):
    """
    Perform validation checks on the data.
    
    Args:
        prolific_df (pd.DataFrame): Prolific demographic data
        participant_ids (set): Set of participant IDs from cognitive task data
    
    Returns:
        list: List of dictionaries containing validation metrics
    """
    print("Performing validation checks...")
    
    metrics = []
    
    # Check if cognitive task participant IDs match prolific data
    approved_df = prolific_df[prolific_df['Status'] == 'APPROVED'].copy()
    prolific_participant_ids = set(approved_df['Participant id'].dropna())
    
    # Find participants in cognitive data but not in approved prolific data
    cognitive_only = participant_ids - prolific_participant_ids
    prolific_only = prolific_participant_ids - participant_ids
    matched_participants = participant_ids & prolific_participant_ids
    
    metrics.extend([
        {
            'metric_name': 'participants_cognitive_only',
            'metric_value': len(cognitive_only),
            'additional_info': 'Participants in cognitive data but not in approved prolific data'
        },
        {
            'metric_name': 'participants_prolific_only',
            'metric_value': len(prolific_only),
            'additional_info': 'Approved participants without cognitive data'
        },
        {
            'metric_name': 'participants_matched',
            'metric_value': len(matched_participants),
            'additional_info': 'Participants with both prolific and cognitive data'
        }
    ])
    
    print(f"Validation results:")
    print(f"  Cognitive only: {len(cognitive_only)}")
    print(f"  Prolific only: {len(prolific_only)}")
    print(f"  Matched: {len(matched_participants)}")
    
    # Check for missing demographic data in approved participants
    if not approved_df.empty:
        missing_age = approved_df['Age'].isna().sum()
        missing_sex = approved_df['Sex'].isna().sum()
        
        metrics.extend([
            {
                'metric_name': 'missing_age_count',
                'metric_value': missing_age,
                'additional_info': 'Number of approved participants with missing age data'
            },
            {
                'metric_name': 'missing_sex_count',
                'metric_value': missing_sex,
                'additional_info': 'Number of approved participants with missing sex data'
            }
        ])
        
        print(f"Missing data in approved participants:")
        print(f"  Missing age: {missing_age}")
        print(f"  Missing sex: {missing_sex}")
    
    # Check age range (18-35 based on inclusion criteria)
    if 'Age' in approved_df.columns and not approved_df['Age'].empty:
        age_data = approved_df['Age'].dropna()
        outside_range = age_data[(age_data < 18) | (age_data > 35)]
        
        metrics.append({
            'metric_name': 'participants_outside_age_range',
            'metric_value': len(outside_range),
            'additional_info': 'Participants outside 18-35 age range'
        })
        
        print(f"Participants outside age range 18-35: {len(outside_range)}")
        if len(outside_range) > 0:
            print(f"Ages outside range: {outside_range.tolist()}")
    
    return metrics


def save_results(all_metrics):
    """
    Save results to CSV file.
    
    Args:
        all_metrics (list): List of all metric dictionaries
    """
    print("Saving results...")
    
    # Create outputs directory if it doesn't exist
    os.makedirs('outputs', exist_ok=True)
    
    # Generate timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'outputs/sample_statistics_{timestamp}.csv'
    
    # Create DataFrame
    results_df = pd.DataFrame(all_metrics)
    
    print("Final results dataframe:")
    print("Columns:")
    print(results_df.columns.tolist())
    print("First 2 rows:")
    print(results_df.head(2))
    print(f"Total metrics: {len(results_df)}")
    
    # Save to CSV
    results_df.to_csv(output_file, index=False)
    print(f"Results saved to: {output_file}")
    
    # Print summary of results
    print("\nSummary of calculated metrics:")
    for _, row in results_df.iterrows():
        print(f"  {row['metric_name']}: {row['metric_value']} ({row['additional_info']})")


def main():
    """
    Main function to execute the sample statistics calculation.
    
    Returns:
        int: 0 for success, 1 for error
    """
    try:
        print("Starting sample statistics calculation...")
        print(f"Current working directory: {os.getcwd()}")
        
        # Load data
        prolific_df = load_prolific_data()
        participant_ids, focus_metrics_df = load_cognitive_task_data()
        
        # Calculate metrics
        sample_metrics = calculate_sample_characteristics(prolific_df)
        quality_metrics = calculate_data_quality_indicators(prolific_df, participant_ids, focus_metrics_df)
        validation_metrics = perform_validation_checks(prolific_df, participant_ids)
        
        # Combine all metrics
        all_metrics = sample_metrics + quality_metrics + validation_metrics
        
        # Save results
        save_results(all_metrics)
        
        # Add exclusion summary as per requirements
        print("\n--- Data Loading and Exclusion Summary ---")
        total_recruited = prolific_df['Participant id'].nunique()
        matched_count = len(participant_ids.intersection(set(prolific_df[prolific_df['Status'] == 'APPROVED']['Participant id'])))
        print(f"Data found for {total_recruited} participants in Prolific export.")
        print("0 participants were removed (no exclusion criteria applied in this step).")
        print(f"Final dataset: {matched_count} participants with matched approved Prolific and cognitive data.")
        print("------------------------------------------")
        
        print("Finished execution")
        return 0
        
    except Exception as e:
        print(f"Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
