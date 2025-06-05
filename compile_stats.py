#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 14 13:03:39 2025
@author: Leela Srinivasan

Pull summary stats from each subject's PVS dir. Consolidate and push to original excel.
Dependencies: AFNI
"""

import os
import subprocess
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta


def main(): 
    integrate_pvs_excel()
    write_hv_excel()
    

def compute_binary_volume(eroded_mask_dir):
    """
    Compute the volume of binary eroded white matter volumetric masks.

    Returns
    -------
    None. Outputs volume to txtfile.

    """
    
    for hemi in ["left", "right"]:
        
        
        f="eroded_{}_cerebral_white_matter.nii".format(hemi)
        fp=os.path.join(eroded_mask_dir,f)
        o="{}_vol.txt".format(hemi)
        op=os.path.join(eroded_mask_dir,o)
        

        cmd="3dOverlap {} {} > {}"
        cmd=cmd.format(fp,fp,op)
        subprocess.run(cmd, shell=True)
            


def add_wm_volumes(ind, subj, df):
    """

    Add WM Volumes to summary PVS df
    
    
    Parameters
    ----------
    ind : int
        row number corresponding to subject.
    subj : str
        p***.
    df : df
        summary df.

    Returns
    -------
    df : df
        updated summary df.

    """
    
    #Run 3dOverlap to calculate binary volumes
    eroded_mask_dir="/Volumes/Shares/NEU/Projects/PVS/{}/eroded_masks".format(subj)
    if not os.path.exists(eroded_mask_dir):
        return df #Return unedited
    
    if not "left_vol.txt" in os.listdir(eroded_mask_dir):
        compute_binary_volume(eroded_mask_dir)
    
    
    #Read txtfile and add volume to summary df
    for hemi in ["Left", "Right"]:
        hemi_lower=hemi.lower()
        f="{}_vol.txt".format(hemi_lower)
        fp=os.path.join(eroded_mask_dir, f)
        
        
        with open(fp, "r") as file:
            content=file.read()
            vol=int(content.split("\n")[0])
            colname="{} WM Volume".format(hemi)
            df.loc[ind, colname] = vol   
            
            
    return df
        

def filter_df(df):
    """
    
    Remove subjects with inaccurately large PVS structures

    Parameters
    ----------
    df : df
        input df.

    Returns
    -------
    bool
        True/False to drop subject.
    df
        filtered df.

    """
    
    
    if df.loc[0, "#Volume"]>500:
        return True, df
    return False, df[df["#Volume"] <= 500 ]


def key_to_list():
    """

    Returns
    -------
    key_list : liet
        list of patient and name pairings.

    """
    
    fp='/Volumes/Shares/NEU/Scripts_and_Parameters/14N0061_key'
    try:
        with open(fp, "r") as file:
            key_list = file.read().splitlines()
    except Exception as e:
        print(f"An error occurred: {e}")
    return key_list

    
def subj_to_name(subj):
    """
    

    Parameters
    ----------
    subj : p***
        p-number.

    Returns
    -------
    name : str
        name as reflected by 14N key.

    """
    
    #Pull subject pairing
    key_list=key_to_list()
    pair=[x for x in key_list if subj+"=" in x]
    if len(pair)==1:
        name=pair[0].split("=")[1]
        return name
    return None


def name_to_subj(name_list):
    """
    

    Parameters
    ----------
    name_list : list
        list of lowercase names (all last and first).

    Returns
    -------
    subj : str
        p***.

    """
    
    key_list=key_to_list()
    for pairing in key_list:
        names=pairing.split("=")[1].split("_")
        if all(item in names for item in name_list):
            subj=pairing.split("=")[0]
            return subj
    return None


def convert_str_to_datetime(date):
    """
    
    Convert date from str acquired from README to datetime object

    Parameters
    ----------
    date : str
        MRI acq date.

    Returns
    -------
    date_obj : datetime obj
        MRI acq date in datetime format.

    """
    
    date_format="%Y%m%d"
    date_obj=datetime.strptime(date, date_format)
    return date_obj


def find_date_from_readme(mri_folder):
    """
    

    Parameters
    ----------
    mri_folder : str
        path to mri Raw_Data folder.

    Returns
    -------
    date : str
        date of MRI acq.

    """
    
    for f in os.listdir(mri_folder):
        if 'README' in f:
            with open(os.path.join(mri_folder, f), "r") as file:
                content = file.read()
                
                if "Study" in f:
                    content_list=content.split(", ")
                    date_entries=[x for x in content_list if "Study:" in x]
                    if len(date_entries)>0:
                        date=date_entries[0].split(":")[1].split("-")[0]
                        return date, convert_str_to_datetime(date)
                   
                elif "Series" in f:
                    content_list=content.split("\n    ")[1:]
                    date_entries=[x for x in content_list if "InstanceCreationDate:" in x]
                    if len(date_entries)>0:
                        date=date_entries[0].split(": ")[1]
                        return date, convert_str_to_datetime(date)
    return None, None
                       
                
    
def hyphenate_date(date):
    """
    

    Parameters
    ----------
    date : str
        20010504 format.

    Returns
    -------
    date
        2001-05-04 format.

    """
    
    if date:
        return "-".join([date[:4], date[4:6], date[6:8]])
    return None

    
def get_mri_acq_date(subj):
    """
    

    Parameters
    ----------
    subj : str
        p***.

    Returns
    -------
    date : str
        date of MRI acq
        
    With extract_date and subj_to_name, finds MRI acquisition date

    """
    
    
    mri_default_dir='/Volumes/Shares/NEU/Raw_Data/Multicontrast_MRI/Patients/'
    mri_alt_dir='/Volumes/Shares/NEU/Raw_Data/Other_MRI/Patients/'
    name=subj_to_name(subj)

    
    if name in os.listdir(mri_default_dir):
        dcm_folder=os.path.join(mri_default_dir, name)
        if "mri" in os.listdir(dcm_folder):
            mri_folder=os.path.join(dcm_folder, "mri")
            if "mprage" in os.listdir(mri_folder):
                date, dt_obj=find_date_from_readme(os.path.join(mri_folder, "mprage"))
                return hyphenate_date(date), dt_obj
        
        
    elif name in os.listdir(mri_alt_dir):
        dcm_folder=os.path.join(mri_alt_dir, name)
        if "mri" in os.listdir(dcm_folder):
            date, dt_obj = find_date_from_readme(os.path.join(dcm_folder, "mri"))
            return hyphenate_date(date), dt_obj
        
        
    return None, None
        
    
def read_subj_csvs(subj):
    """
    Read and compute summary stats for PVS data, if pipeline has been run on subj

    Parameters
    ----------
    subj : TYPE
        DESCRIPTION.

    Returns
    -------
    list
        statistics list with PVS count, volume, and average volume for each hemi.

    """
    pvs_root='/Volumes/Shares/NEU/Projects/PVS/'
    csv_dir=os.path.join(pvs_root,subj,'t1', 'csv')
    if os.path.exists(csv_dir):
        
        stats=[]
        for hemi in ['left', 'right']:
            
            
            csv_name="pvs_within_{}_cerebral_white_matter.csv".format(hemi)
            if not os.path.exists(os.path.join(csv_dir, csv_name)):
                stats.append(0)
                stats.append(0)
                stats.append(0)
                
            else:
                df=pd.read_csv(os.path.join(csv_dir, csv_name))
                if df.empty:
                    return None
                drop_subject,df=filter_df(df)
                if drop_subject:
                    return None
                
                
                stats.append(len(df))
                stats.append(df['#Volume'].values.sum() if len(df['#Volume'].values) > 0 else 0)
                stats.append(df['#Volume'].values.mean() if len(df['#Volume'].values) > 0 else 0)
            
            
        return stats
    return None
           

def read_pvs_excel():
    """
    Read raw excel, convert format and create new cols.

    Returns
    -------
    pvs_df : df
        pvs data from excel.

    """
    
    #Read raw excel
    f='/Users/srinivasanl2/Library/CloudStorage/OneDrive-NationalInstitutesofHealth/pvs_seizure_outcomes.xlsx'
    pvs_df=pd.read_excel(f)
    pvs_df=pvs_df.dropna(subset=['First Name'])
    
    
    #Initialize new columns
    pvs_df["pnum"]=""
    pvs_df["dob"]=pvs_df["Patient Profile ::DOB"].apply(lambda x: str(x).split(" ")[0])
    pvs_df["mri_date"]=""
    pvs_df["age_at_mri"]=""
    return pvs_df
    

def create_hv_df():

    
    cols=["Left WM Volume", "Right WM Volume", "Left PVS Count", "Left PVS Volume", "Left PVS Mean Volume", "Right PVS Count", "Right PVS Volume", "Right PVS Mean Volume"]
    hv_df=pd.DataFrame(columns=cols)
    pvs_root='/Volumes/Shares/NEU/Projects/PVS/'
    
    
    for hv in os.listdir(pvs_root):
        if 'hv' in hv:
            stats=read_subj_csvs(hv)
            if stats:
                ind=len(hv_df)
                for i in range(0,6):
                    hv_df.loc[ind, cols[i+2]]=stats[i]
                hv_df=add_wm_volumes(ind,hv,hv_df)
            
    return hv_df
        
        
def write_hv_excel():
    
    
    hv_df=create_hv_df()
    summary_dir='/Volumes/Shares/NEU/Projects/PVS/summary'
    hv_df.to_excel(os.path.join(summary_dir, 'hv_stats.xlsx'))
    
    
def age_at_mri(dob, mri_date):
    """

    Parameters
    ----------
    dob : datetime.datetime obj
        date of birth.
    mri_date : datetime.datetime obj
        date of mri acq.

    Returns
    -------
    age at MRI : int
        age in years at MRI.

    """
    
    return relativedelta(mri_date, dob).years

  
def update_date_info(ind, df, subj):
    """

    Parameters
    ----------
    ind : int
        df index.
    df : df
        pvs df.
    subj : str
        p***.

    Returns
    -------
    df : df
        pvs df, updated with date information.

    """
    
    #Get MRI info
    df.loc[ind, "pnum"]=subj
    mri_date, mri_datetime =get_mri_acq_date(subj)
    
    if mri_date:
        df.loc[ind, "mri_date"] = mri_date
        dob_datetime=df.loc[ind, 'Patient Profile ::DOB']
        df.loc[ind, "age_at_mri"] = age_at_mri(dob_datetime, mri_datetime)
        
    
    return df

        
def integrate_pvs_excel():
    """

    Reads and modifies PVS df, pushes back to excel sheet

    """
    pvs_df=read_pvs_excel()
    new_cols=["Left WM Volume", "Right WM Volume", "Left PVS Count", "Left PVS Volume", "Left PVS Mean Volume", "Right PVS Count", "Right PVS Volume", "Right PVS Mean Volume"]
    for new_col in new_cols:
        pvs_df[new_col]=""
        
    
    #Iterate through subjects, creating list of all possible lowercase names
    for ind, row in pvs_df.iterrows():
        all_names= row["First Name"].split(" ") + row["Last Name"].split(" ")
        lowercase_names=[x.lower() for x in all_names]
        subj=name_to_subj(lowercase_names)
        
        
        #If subj in key, update df with date and PVS stat info
        if subj: 
            pvs_df=update_date_info(ind, pvs_df, subj)
            pvs_df=add_wm_volumes(ind,subj,pvs_df)
            stat_list=read_subj_csvs(subj)
            if stat_list:
               for i in range(0,6):
                   pvs_df.loc[ind, new_cols[i+2]]=stat_list[i]
        
        
    #Push to excel sheets
    summary_dir='/Volumes/Shares/NEU/Projects/PVS/summary'
    pvs_df.to_excel(os.path.join(summary_dir, 'integrated_pvs_project.xlsx'))
    subset_df=pvs_df[pvs_df["Left PVS Count"] != ""]
    subset_df.to_excel(os.path.join(summary_dir, 'subset_pvs_project.xlsx'))

    
    
if __name__ == "__main__":
    main()
