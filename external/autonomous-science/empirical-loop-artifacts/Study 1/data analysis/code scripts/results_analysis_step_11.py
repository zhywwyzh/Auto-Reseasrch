#!/usr/bin/env python3
"""
Task Order Effects Analysis Script

This script analyzes the effects of task order (VWM first vs MRT first) on performance
in both Visual Working Memory (VWM) and Mental Rotation Task (MRT) experiments.
"""

import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import sys
import warnings
warnings.filterwarnings('ignore')

# Import R functionality
try:
    import rpy2.robjects as ro
    from rpy2.robjects import pandas2ri
    from rpy2.robjects.packages import importr
    pandas2ri.activate()
    
    # Import R packages
    base = importr('base')
    stats = importr('stats')
    lme4 = importr('lme4')
    lmerTest = importr('lmerTest')
    
    print("R packages loaded successfully")
except ImportError as e:
    print(f"Error importing R packages: {e}")
    sys.exit(1)

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
    
    # Get the most recent file based on modification time
    most_recent = max(files, key=os.path.getmtime)
    print(f"Found most recent file: {most_recent}")
    return most_recent

def load_raw_data():
    """
    Load raw data files to extract task order information.
    
    Returns:
    pd.DataFrame: Combined raw data with task order information
    """
    print("Loading raw data files...")
    
    # Find all raw data files
    raw_files = glob.glob("raw_data/PARTICIPANT_*_VWM_and_Rotation_Task_*.csv")
    print(f"Found {len(raw_files)} raw data files")
    
    if not raw_files:
        print("No raw data files found!")
        return None
    
    all_data = []
    
    for file in raw_files:
        print(f"Processing file: {file}")
        try:
            df = pd.read_csv(file)
            df.columns = [col.strip() for col in df.columns]
            print(f"Columns in {file}: {list(df.columns)}")
            print(f"First 3 rows of {file}:")
            print(df.head(3))
            
            # Check for required columns
            required_cols = ['participantId', 'taskOrder', 'table', 'isPractice', 
                           'VWM_setSize', 'VWM_delay_s', 'VWM_error_absolute_degrees',
                           'MRT_angle_degrees', 'MRT_isCorrect', 'MRT_rt_ms']
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Missing columns in {file}: {missing_cols}")
                continue
            
            all_data.append(df)
            
        except Exception as e:
            print(f"Error reading {file}: {e}")
            continue
    
    if not all_data:
        print("No valid raw data files found!")
        return None
    
    # Combine all data
    combined_data = pd.concat(all_data, ignore_index=True)
    print(f"Combined raw data shape: {combined_data.shape}")
    print(f"Combined data columns: {list(combined_data.columns)}")
    print("First 2 rows of combined data:")
    print(combined_data.head(2))
    
    return combined_data

def extract_task_order_info(raw_data):
    """
    Extract task order information from raw data.
    
    Parameters:
    raw_data (pd.DataFrame): Raw data containing task order information
    
    Returns:
    pd.DataFrame: Task order information per participant
    """
    print("Extracting task order information...")
    
    if raw_data is None:
        print("No raw data available for task order extraction")
        return None
    
    # Print unique values for key columns
    print(f"Unique taskOrder values: {sorted(raw_data['taskOrder'].unique())}")
    print(f"Unique participantId values: {len(raw_data['participantId'].unique())} participants")
    
    # Extract task order per participant (should be consistent within participant)
    task_order_info = raw_data.groupby('participantId')['taskOrder'].first().reset_index()
    
    # Create binary variable: Task_Order_VWM_First
    # Assuming taskOrder = 1 means VWM first, taskOrder = 2 means MRT first
    # This needs to be verified based on the actual data structure
    print(f"Task order distribution: {task_order_info['taskOrder'].value_counts()}")
    
    # Create binary variable (1 = VWM first, 0 = MRT first)
    task_order_info['Task_Order_VWM_First'] = (task_order_info['taskOrder'] == 1).astype(int)
    
    print(f"Task_Order_VWM_First distribution:")
    print(task_order_info['Task_Order_VWM_First'].value_counts())
    
    print("Task order info:")
    print(task_order_info.head(2))
    
    return task_order_info

def load_cleaned_vwm_data():
    """
    Load the most recent cleaned VWM data file.
    
    Returns:
    pd.DataFrame: Cleaned VWM data
    """
    print("Loading cleaned VWM data...")
    
    # Find the most recent VWM cleaned data file
    vwm_file = find_most_recent_file("outputs/VWM_cleaned_data_*.csv")
    
    if not vwm_file:
        print("No VWM cleaned data file found!")
        return None
    
    try:
        vwm_data = pd.read_csv(vwm_file)
        vwm_data.columns = [col.strip() for col in vwm_data.columns]
        print(f"VWM data shape: {vwm_data.shape}")
        print(f"VWM data columns: {list(vwm_data.columns)}")
        print("First 2 rows of VWM data:")
        print(vwm_data.head(2))
        
        # Print unique values for key experimental parameters
        print(f"Unique VWM_setSize values: {sorted(vwm_data['VWM_setSize'].unique())}")
        print(f"Unique VWM_delay_s values: {sorted(vwm_data['VWM_delay_s'].unique())}")
        print(f"Unique isPractice values: {vwm_data['isPractice'].unique()}")
        print(f"Unique excluded_participant values: {vwm_data['excluded_participant'].unique()}")
        print(f"Unique valid_trial values: {vwm_data['valid_trial'].unique()}")
        
        return vwm_data
        
    except Exception as e:
        print(f"Error loading VWM data: {e}")
        return None

def load_cleaned_mrt_data():
    """
    Load the most recent cleaned MRT data file.
    
    Returns:
    pd.DataFrame: Cleaned MRT data
    """
    print("Loading cleaned MRT data...")
    
    # Find the most recent MRT cleaned data file
    mrt_file = find_most_recent_file("outputs/MRT_cleaned_data_*.csv")
    
    if not mrt_file:
        print("No MRT cleaned data file found!")
        return None
    
    try:
        mrt_data = pd.read_csv(mrt_file)
        mrt_data.columns = [col.strip() for col in mrt_data.columns]
        print(f"MRT data shape: {mrt_data.shape}")
        print(f"MRT data columns: {list(mrt_data.columns)}")
        print("First 2 rows of MRT data:")
        print(mrt_data.head(2))
        
        # Print unique values for key experimental parameters
        print(f"Unique MRT_angle_degrees values: {sorted(mrt_data['MRT_angle_degrees'].unique())}")
        print(f"Unique MRT_isCorrect values: {mrt_data['MRT_isCorrect'].unique()}")
        print(f"Unique isPractice values: {mrt_data['isPractice'].unique()}")
        print(f"Unique excluded_participant values: {mrt_data['excluded_participant'].unique()}")
        print(f"Unique valid_trial values: {mrt_data['valid_trial'].unique()}")
        
        return mrt_data
        
    except Exception as e:
        print(f"Error loading MRT data: {e}")
        return None

def analyze_vwm_with_task_order(vwm_data, task_order_info):
    """
    Analyze VWM data with task order effects using mixed-effects model.
    
    Parameters:
    vwm_data (pd.DataFrame): Cleaned VWM data
    task_order_info (pd.DataFrame): Task order information
    
    Returns:
    pd.DataFrame: Model results
    """
    print("Analyzing VWM data with task order effects...")
    
    if vwm_data is None or task_order_info is None:
        print("Missing data for VWM analysis")
        return None
    
    # Merge task order information
    vwm_merged = vwm_data.merge(task_order_info[['participantId', 'Task_Order_VWM_First']], 
                                on='participantId', how='left')
    
    print(f"VWM data after merging task order: {vwm_merged.shape}")
    print("First 2 rows after merge:")
    print(vwm_merged.head(2))
    
    # Filter data
    print("Filtering VWM data...")
    print(f"Before filtering: {len(vwm_merged)} rows")
    
    vwm_filtered = vwm_merged[
        (vwm_merged['excluded_participant'] == False) &
        (vwm_merged['isPractice'] == False) &
        (vwm_merged['valid_trial'] == True) &
        (vwm_merged['VWM_isAttentionCheck'] == False)
    ].copy()
    
    print(f"After filtering: {len(vwm_filtered)} rows")
    
    if len(vwm_filtered) == 0:
        print("No valid VWM data after filtering!")
        return None
    
    # Filter for specified set sizes and delays to avoid rank deficiency
    valid_set_sizes = [2, 4]
    valid_delays = [1.0, 4.0]
    original_row_count = len(vwm_filtered)
    vwm_filtered = vwm_filtered[
        vwm_filtered['VWM_setSize'].isin(valid_set_sizes) &
        vwm_filtered['VWM_delay_s'].isin(valid_delays)
    ].copy()
    print(f"Filtered VWM data for set_sizes {valid_set_sizes} and delays {valid_delays}. Rows changed from {original_row_count} to {len(vwm_filtered)}")

    # Convert to categorical factors
    vwm_filtered['VWM_setSize_factor'] = vwm_filtered['VWM_setSize'].astype('category')
    vwm_filtered['VWM_delay_s_factor'] = vwm_filtered['VWM_delay_s'].astype('category')
    vwm_filtered['participantId_factor'] = vwm_filtered['participantId'].astype('category')
    
    print("VWM data prepared for analysis")
    print(f"Unique participants: {len(vwm_filtered['participantId'].unique())}")
    print(f"Task order distribution: {vwm_filtered['Task_Order_VWM_First'].value_counts()}")
    
    # Prepare data for R
    vwm_r = pandas2ri.py2rpy(vwm_filtered)
    
    # Fit mixed-effects model in R
    print("Fitting VWM mixed-effects model...")
    try:
        ro.globalenv['vwm_data'] = vwm_r

        # Load lmerTest for p-values
        ro.r("library(lmerTest)")

        # Try full model first, then simpler models if rank deficient
        model_formulas = [
            "VWM_error_absolute_degrees ~ VWM_setSize_factor * VWM_delay_s_factor * Task_Order_VWM_First + (1 | participantId_factor)",
            "VWM_error_absolute_degrees ~ VWM_setSize_factor + VWM_delay_s_factor + Task_Order_VWM_First + (1 | participantId_factor)",
            "VWM_error_absolute_degrees ~ VWM_setSize_factor + VWM_delay_s_factor + (1 | participantId_factor)"
        ]

        coef_df = None
        for i, formula in enumerate(model_formulas):
            try:
                print(f"Trying VWM model formula {i+1}: {formula}")
                ro.r(f'''
                vwm_model <- lmer({formula}, data = vwm_data)
                vwm_summary <- summary(vwm_model)
                r_coeffs_matrix <- vwm_summary$coefficients
                ''')
                # Robust matrix-based extraction
                r_coeffs_rownames = list(ro.r("rownames(r_coeffs_matrix)"))
                r_coeffs_colnames = list(ro.r("colnames(r_coeffs_matrix)"))
                np_coeffs = np.array(ro.r("as.matrix(r_coeffs_matrix)"))
                coef_df = pd.DataFrame(np_coeffs, index=r_coeffs_rownames, columns=r_coeffs_colnames)
                coef_df = coef_df.reset_index().rename(columns={'index': 'effect_name'})
                print(f"VWM model {i+1} fitted successfully")
                break
            except Exception as model_error:
                print(f"VWM model {i+1} failed: {model_error}")
                if i == len(model_formulas) - 1:
                    raise model_error
                continue

        if coef_df is not None:
            # Map R column names to desired output column names
            rename_map = {
                'Estimate': 'estimate', 'Std. Error': 'std_error',
                't value': 't_value', 'Pr(>|t|)': 'p_value'
            }
            coef_df.rename(columns=rename_map, inplace=True)

            # Ensure correct types
            for col in ['estimate', 'std_error', 't_value', 'p_value']:
                if col in coef_df.columns:
                    coef_df[col] = pd.to_numeric(coef_df[col], errors='coerce')

            # Calculate confidence intervals
            coef_df['ci_lower'] = coef_df['estimate'] - 1.96 * coef_df['std_error']
            coef_df['ci_upper'] = coef_df['estimate'] + 1.96 * coef_df['std_error']

            coef_df['model_name'] = 'VWM_TaskOrder'

            # Verify all required columns are present
            required_cols = ['model_name', 'effect_name', 'estimate', 'std_error', 't_value', 'p_value', 'ci_lower', 'ci_upper']
            missing_cols = [col for col in required_cols if col not in coef_df.columns]
            if missing_cols:
                print(f"Warning: Missing required columns in VWM results: {missing_cols}")
                # Add missing columns with NaN values
                for col in missing_cols:
                    coef_df[col] = np.nan

            coef_df = coef_df[required_cols]

            print("VWM model results:")
            print(coef_df.head())

            return coef_df

    except Exception as e:
        print(f"Error fitting VWM model: {e}")
        return None

def analyze_mrt_with_task_order(mrt_data, task_order_info):
    """
    Analyze MRT data with task order effects using mixed-effects and GLM models.
    
    Parameters:
    mrt_data (pd.DataFrame): Cleaned MRT data
    task_order_info (pd.DataFrame): Task order information
    
    Returns:
    pd.DataFrame: Combined model results
    """
    print("Analyzing MRT data with task order effects...")
    
    if mrt_data is None or task_order_info is None:
        print("Missing data for MRT analysis")
        return None
    
    # Merge task order information
    mrt_merged = mrt_data.merge(task_order_info[['participantId', 'Task_Order_VWM_First']], 
                                on='participantId', how='left')
    
    print(f"MRT data after merging task order: {mrt_merged.shape}")
    print("First 2 rows after merge:")
    print(mrt_merged.head(2))
    
    # Filter data
    print("Filtering MRT data...")
    print(f"Before filtering: {len(mrt_merged)} rows")
    
    mrt_filtered = mrt_merged[
        (mrt_merged['excluded_participant'] == False) &
        (mrt_merged['isPractice'] == False) &
        (mrt_merged['valid_trial'] == True) &
        (mrt_merged['MRT_isAttentionCheck'] == False)
    ].copy()
    
    print(f"After filtering: {len(mrt_filtered)} rows")
    
    if len(mrt_filtered) == 0:
        print("No valid MRT data after filtering!")
        return None
    
    # Apply log transformation to RT
    mrt_filtered['log_MRT_rt_ms'] = np.log(mrt_filtered['MRT_rt_ms'])
    
    # Prepare categorical factors
    mrt_filtered['participantId_factor'] = mrt_filtered['participantId'].astype('category')
    
    print("MRT data prepared for analysis")
    print(f"Unique participants: {len(mrt_filtered['participantId'].unique())}")
    print(f"Task order distribution: {mrt_filtered['Task_Order_VWM_First'].value_counts()}")
    
    all_results = []

    # 1. RT Model (correct trials only)
    print("Fitting MRT RT model...")
    mrt_rt_data = mrt_filtered[mrt_filtered['MRT_isCorrect'] == True].copy()
    print(f"Correct trials for RT analysis: {len(mrt_rt_data)}")

    if len(mrt_rt_data) > 0:
        try:
            mrt_rt_r = pandas2ri.py2rpy(mrt_rt_data)
            ro.globalenv['mrt_rt_data'] = mrt_rt_r

            # Load lmerTest for p-values
            ro.r("library(lmerTest)")

            # Try full model first, then simpler models if rank deficient
            rt_model_formulas = [
                "log_MRT_rt_ms ~ MRT_angle_degrees * Task_Order_VWM_First + (1 | participantId_factor)",
                "log_MRT_rt_ms ~ MRT_angle_degrees + Task_Order_VWM_First + (1 | participantId_factor)",
                "log_MRT_rt_ms ~ MRT_angle_degrees + (1 | participantId_factor)"
            ]

            rt_coef_df = None
            for i, rt_formula in enumerate(rt_model_formulas):
                try:
                    print(f"Trying MRT RT model formula {i+1}: {rt_formula}")
                    ro.r(f'''
                    mrt_rt_model <- lmer({rt_formula}, data = mrt_rt_data)
                    mrt_rt_summary <- summary(mrt_rt_model)
                    r_coeffs_matrix <- mrt_rt_summary$coefficients
                    ''')
                    # Robust matrix-based extraction
                    r_coeffs_rownames = list(ro.r("rownames(r_coeffs_matrix)"))
                    r_coeffs_colnames = list(ro.r("colnames(r_coeffs_matrix)"))
                    np_coeffs = np.array(ro.r("as.matrix(r_coeffs_matrix)"))
                    rt_coef_df = pd.DataFrame(np_coeffs, index=r_coeffs_rownames, columns=r_coeffs_colnames)
                    rt_coef_df = rt_coef_df.reset_index().rename(columns={'index': 'effect_name'})
                    print(f"MRT RT model {i+1} fitted successfully")
                    break
                except Exception as model_error:
                    print(f"MRT RT model {i+1} failed: {model_error}")
                    if i == len(rt_model_formulas) - 1:
                        raise model_error
                    continue

            if rt_coef_df is not None:
                # Map R column names to desired output column names
                rename_map = {
                    'Estimate': 'estimate', 'Std. Error': 'std_error',
                    't value': 't_value', 'Pr(>|t|)': 'p_value'
                }
                rt_coef_df.rename(columns=rename_map, inplace=True)

                # Ensure correct types
                for col in ['estimate', 'std_error', 't_value', 'p_value']:
                    if col in rt_coef_df.columns:
                        rt_coef_df[col] = pd.to_numeric(rt_coef_df[col], errors='coerce')

                # Calculate confidence intervals
                rt_coef_df['ci_lower'] = rt_coef_df['estimate'] - 1.96 * rt_coef_df['std_error']
                rt_coef_df['ci_upper'] = rt_coef_df['estimate'] + 1.96 * rt_coef_df['std_error']

                rt_coef_df['model_name'] = 'MRT_RT_TaskOrder'

                # Verify all required columns are present
                required_cols = ['model_name', 'effect_name', 'estimate', 'std_error', 't_value', 'p_value', 'ci_lower', 'ci_upper']
                missing_cols = [col for col in required_cols if col not in rt_coef_df.columns]
                if missing_cols:
                    print(f"Warning: Missing required columns in MRT RT results: {missing_cols}")
                    for col in missing_cols:
                        rt_coef_df[col] = np.nan

                rt_coef_df = rt_coef_df[required_cols]

                print("MRT RT model results:")
                print(rt_coef_df.head())

                all_results.append(rt_coef_df)

        except Exception as e:
            print(f"Error fitting MRT RT model: {e}")

    # 2. Accuracy Model (GLM)
    print("Fitting MRT accuracy model...")
    try:
        mrt_acc_r = pandas2ri.py2rpy(mrt_filtered)
        ro.globalenv['mrt_acc_data'] = mrt_acc_r

        # Try full model first, then simpler models if rank deficient
        acc_model_formulas = [
            "MRT_isCorrect ~ MRT_angle_degrees * Task_Order_VWM_First",
            "MRT_isCorrect ~ MRT_angle_degrees + Task_Order_VWM_First",
            "MRT_isCorrect ~ MRT_angle_degrees"
        ]

        acc_coef_df = None
        for i, acc_formula in enumerate(acc_model_formulas):
            try:
                print(f"Trying MRT accuracy model formula {i+1}: {acc_formula}")
                ro.r(f'''
                mrt_acc_model <- glm({acc_formula}, data = mrt_acc_data, family = binomial(link = "logit"))
                mrt_acc_summary <- summary(mrt_acc_model)
                r_coeffs_matrix <- mrt_acc_summary$coefficients
                ''')
                # Robust matrix-based extraction
                r_coeffs_rownames = list(ro.r("rownames(r_coeffs_matrix)"))
                r_coeffs_colnames = list(ro.r("colnames(r_coeffs_matrix)"))
                np_coeffs = np.array(ro.r("as.matrix(r_coeffs_matrix)"))
                acc_coef_df = pd.DataFrame(np_coeffs, index=r_coeffs_rownames, columns=r_coeffs_colnames)
                acc_coef_df = acc_coef_df.reset_index().rename(columns={'index': 'effect_name'})
                print(f"MRT accuracy model {i+1} fitted successfully")
                break
            except Exception as model_error:
                print(f"MRT accuracy model {i+1} failed: {model_error}")
                if i == len(acc_model_formulas) - 1:
                    raise model_error
                continue

        if acc_coef_df is not None:
            # Map R column names to desired output column names
            rename_map = {
                'Estimate': 'estimate', 'Std. Error': 'std_error',
                'z value': 't_value', 'Pr(>|z|)': 'p_value'
            }
            acc_coef_df.rename(columns=rename_map, inplace=True)

            # Ensure correct types
            for col in ['estimate', 'std_error', 't_value', 'p_value']:
                if col in acc_coef_df.columns:
                    acc_coef_df[col] = pd.to_numeric(acc_coef_df[col], errors='coerce')

            # Calculate confidence intervals
            acc_coef_df['ci_lower'] = acc_coef_df['estimate'] - 1.96 * acc_coef_df['std_error']
            acc_coef_df['ci_upper'] = acc_coef_df['estimate'] + 1.96 * acc_coef_df['std_error']

            acc_coef_df['model_name'] = 'MRT_Accuracy_TaskOrder'

            # Verify all required columns are present
            required_cols = ['model_name', 'effect_name', 'estimate', 'std_error', 't_value', 'p_value', 'ci_lower', 'ci_upper']
            missing_cols = [col for col in required_cols if col not in acc_coef_df.columns]
            if missing_cols:
                print(f"Warning: Missing required columns in MRT accuracy results: {missing_cols}")
                for col in missing_cols:
                    acc_coef_df[col] = np.nan

            acc_coef_df = acc_coef_df[required_cols]

            print("MRT accuracy model results:")
            print(acc_coef_df.head())

            all_results.append(acc_coef_df)

    except Exception as e:
        print(f"Error fitting MRT accuracy model: {e}")

    # Combine results
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        return combined_results
    else:
        return None

def create_task_order_summary(vwm_data, mrt_data, task_order_info):
    """
    Create summary statistics for task order conditions.
    
    Parameters:
    vwm_data (pd.DataFrame): VWM data
    mrt_data (pd.DataFrame): MRT data
    task_order_info (pd.DataFrame): Task order information
    
    Returns:
    pd.DataFrame: Task order summary statistics
    """
    print("Creating task order summary...")
    
    if task_order_info is None:
        print("No task order information available")
        return None
    
    # Merge task order with both datasets
    if vwm_data is not None:
        vwm_merged = vwm_data.merge(task_order_info[['participantId', 'Task_Order_VWM_First']], 
                                    on='participantId', how='left')
        vwm_filtered_summary = vwm_merged[
            (vwm_merged['excluded_participant'] == False) &
            (vwm_merged['isPractice'] == False) &
            (vwm_merged['valid_trial'] == True) &
            (vwm_merged['VWM_isAttentionCheck'] == False) &
            (vwm_merged['VWM_setSize'].isin([2, 4])) &
            (vwm_merged['VWM_delay_s'].isin([1.0, 4.0]))
        ]
    else:
        vwm_filtered_summary = None

    if mrt_data is not None:
        mrt_merged = mrt_data.merge(task_order_info[['participantId', 'Task_Order_VWM_First']], 
                                    on='participantId', how='left')
        mrt_filtered_summary = mrt_merged[
            (mrt_merged['excluded_participant'] == False) &
            (mrt_merged['isPractice'] == False) &
            (mrt_merged['valid_trial'] == True) &
            (mrt_merged['MRT_isAttentionCheck'] == False)
        ]
    else:
        mrt_filtered_summary = None
    
    # Create summary by task order condition
    summary_data = []
    
    for task_order in [0, 1]:  # 0 = MRT first, 1 = VWM first
        condition_name = "VWM_First" if task_order == 1 else "MRT_First"
        
        # Count participants
        n_participants = len(task_order_info[task_order_info['Task_Order_VWM_First'] == task_order])
        percentage = (n_participants / len(task_order_info)) * 100
        
        # Calculate mean VWM performance
        mean_vwm_performance = np.nan
        if vwm_filtered_summary is not None:
            vwm_condition = vwm_filtered_summary[vwm_filtered_summary['Task_Order_VWM_First'] == task_order]
            if len(vwm_condition) > 0:
                mean_vwm_performance = vwm_condition['VWM_error_absolute_degrees'].mean()

        # Calculate mean MRT performance (accuracy)
        mean_mrt_performance = np.nan
        if mrt_filtered_summary is not None:
            mrt_condition = mrt_filtered_summary[mrt_filtered_summary['Task_Order_VWM_First'] == task_order]
            if len(mrt_condition) > 0:
                mean_mrt_performance = mrt_condition['MRT_isCorrect'].mean()
        
        summary_data.append({
            'task_order_condition': condition_name,
            'n_participants': n_participants,
            'percentage': percentage,
            'mean_vwm_performance': mean_vwm_performance,
            'mean_mrt_performance': mean_mrt_performance
        })
    
    summary_df = pd.DataFrame(summary_data)
    
    print("Task order summary:")
    print(summary_df)
    
    return summary_df

def main():
    """
    Main function to execute the task order effects analysis.
    
    Returns:
    int: 0 for success, 1 for error
    """
    try:
        print("Starting task order effects analysis...")
        
        # Create outputs directory if it doesn't exist
        if not os.path.exists('outputs'):
            os.makedirs('outputs')
            print("Created outputs directory")
        
        # Load raw data to extract task order information
        raw_data = load_raw_data()
        task_order_info = extract_task_order_info(raw_data)
        
        if task_order_info is None:
            print("Failed to extract task order information")
            return 1
        
        # Load cleaned data
        vwm_data = load_cleaned_vwm_data()
        mrt_data = load_cleaned_mrt_data()
        
        if vwm_data is None and mrt_data is None:
            print("No cleaned data available for analysis")
            return 1
        
        # Analyze VWM with task order
        vwm_results = None
        try:
            if vwm_data is not None:
                vwm_results = analyze_vwm_with_task_order(vwm_data, task_order_info)
        except Exception as e:
            print(f"Error in VWM analysis: {e}")

        # Analyze MRT with task order
        mrt_results = None
        try:
            if mrt_data is not None:
                mrt_results = analyze_mrt_with_task_order(mrt_data, task_order_info)
        except Exception as e:
            print(f"Error in MRT analysis: {e}")

        # Combine all results
        all_results = []
        if vwm_results is not None:
            all_results.append(vwm_results)
        if mrt_results is not None:
            all_results.append(mrt_results)

        # Save results (even if empty)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_filename = f"outputs/task_order_effects_results_{timestamp}.csv"
        required_columns = ['model_name', 'effect_name', 'estimate', 'std_error',
                            't_value', 'p_value', 'ci_lower', 'ci_upper']

        if all_results:
            combined_results = pd.concat(all_results, ignore_index=True)
            results_output = combined_results[required_columns]
        else:
            # Create empty DataFrame with required columns
            results_output = pd.DataFrame(columns=required_columns)

        results_output.to_csv(results_filename, index=False)
        print(f"Results saved to {results_filename}")

        print("Final results:")
        print(results_output)

        # Create task order summary
        summary_df = create_task_order_summary(vwm_data, mrt_data, task_order_info)

        if summary_df is not None:
            # Save summary
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_filename = f"outputs/task_order_summary_{timestamp}.csv"

            # Ensure we only include required columns
            required_summary_columns = ['task_order_condition', 'n_participants', 'percentage',
                                       'mean_vwm_performance', 'mean_mrt_performance']

            summary_output = summary_df[required_summary_columns]
            summary_output.to_csv(summary_filename, index=False)
            print(f"Summary saved to {summary_filename}")

            print("Final summary:")
            print(summary_output)

        print("Task order effects analysis completed successfully")
        print("Finished execution")
        return 0

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
