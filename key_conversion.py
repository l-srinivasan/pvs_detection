#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 3 09:58:34 2025
@author: Leela Srinivasan

Convert patient and HV names to p-numbers/hv codes.
"""

import os
import pandas as pd


def main():
    
    df=read_raw_pvs()
    key_list=read_key()

    pnums=[]
    missing=[]
    odir='/Volumes/Shares/NEU/Projects/PVS/summary/'
    extract_hvs(key_list, odir)


    #Scan key for match and append to list if found/missing
    for ind, row in df.iterrows():
        all_names=row["First Name"].split(' ') + row["Last Name"].split(' ')
        lowercase_names=[x.lower() for x in all_names]
        found=0
        
        for pair in key_list:
            if all(x in pair for x in lowercase_names):
                pnum=pair.split("=")[0]
                pnums.append(pnum)
                found=1
        
        if found==0:
            missing.append(" ".join(all_names))


    #Save outputs to txt files 
    out_fp=os.path.join(odir, "pnums.txt")
    list_to_txtfile(pnums, out_fp)
    missing_fp=os.path.join(odir, "missing_names.txt")
    list_to_txtfile(missing, missing_fp)
    
    
    
def read_raw_pvs():
    """
    Read most recent version of PVS df and extract subject names.

    Returns
    -------
    df : df
        df containing solely subject names.

    """
    f='/Users/srinivasanl2/Library/CloudStorage/OneDrive-NationalInstitutesofHealth/pvs_seizure_outcomes.xlsx'
    pvs_df=pd.read_excel(f)
    pvs_df=pvs_df.dropna(subset=['First Name'])
    df=pvs_df[["First Name", "Last Name"]]
    return df

    
def read_key():
    """
    Read 14N executable.

    Returns
    -------
    key_list : list
        list of subject / code associations.

    """
    
    key_fp="/Volumes/Shares/NEU/Scripts_and_Parameters/14N0061_key"
    try:
        with open(key_fp, "r") as file:
            key_list = file.read().splitlines()
    except Exception as e:
        print(f"An error occurred: {e}")
    return key_list


def list_to_txtfile(lst, output_file):
    """
    

    Parameters
    ----------
    lst : list
    output_file : str
        path for desired newline separated output text file.

    Returns
    -------
    None.

    """
    with open(output_file, mode="w") as file:
        file.write("\n".join(lst) + "\n")


def extract_hvs(key_list, odir):
    """

    Parameters
    ----------
    key_list : list
        list of pairings in the 14N key.
    odir : str
        path to output dir.

    Returns
    -------
    None. Outputs newline separated file containing  HVs to run.

    """
    
    hv_list=[x.split("=")[0] for x in key_list if "hv" in x]
    hv_fp=os.path.join(odir, "hvs.txt")
    list_to_txtfile(hv_list, hv_fp)


if __name__ == "__main__":
    main()
