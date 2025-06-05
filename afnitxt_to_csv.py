#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 10 14:08:43 2025
@author: Leela Srinivasan

Convert 3dClusterize outputs to CSV format.
"""


import sys
import re
import pandas as pd


def main():
    
    f=sys.argv[1]
    outname=sys.argv[2]
    
    if verify_clusters(f):
        df,total_voxels=afnisummary_to_df(f)
        print("Total PVS voxels for {}: {}.".format(f, total_voxels))
        df_to_csv(df, outname)
        
    else:
        print("No clusters found in {}. Continuing...".format(f))
    

def split_row(input_string):
    """

    Parameters
    ----------
    input_string : str
        AFNI Column header string.

    Returns
    -------
    list
        AFNI Column names, split from original header.

    """
    return [x for x in re.split('  ', input_string) if x!='']


def verify_clusters(f):
    """

    Parameters
    ----------
    f : str
        Path to txt file output.

    Returns
    -------
    bool
        True if clusters exist, False if not.

    """
    
    with open(f, "r") as text_file:
        contents=text_file.readlines()
        if contents[0]=='#** NO CLUSTERS FOUND ***\n':
            return False
    return True
        
        
def afnisummary_to_df(f):
    """

    Parameters
    ----------
    f : str
        Path to txt file output.

    Returns
    -------
    df : df
        df containing table information from AFNI text report.
    total_voxels : str
        String integer value containing total PVS voxels in the nifti volume.

    """
    
    #Read table, skip opening lines and remove unwanted hashed lines, preserving summary footer
    table=pd.read_csv(f, delimiter='\t', skiprows=16)
    table=table.iloc[1:]
    summary=split_row(table.iloc[-1].values[0])
    total_voxels=summary[0]
    if total_voxels == '#':
       total_voxels=summary[1]
    table=table.iloc[:-2]
    
    #Append split strings to new df with corresponding columns
    df=pd.DataFrame(columns=split_row(table.columns[0]))
    for i in range(1, len(table)+1):
        df.loc[i-1] = split_row(table.loc[i, :].values[0])
        
    return df,total_voxels


def get_parent_dir(f):
    """

    Parameters
    ----------
    f : str
        orig path.

    Returns
    -------
    parent_dir : str
        directory containing f.

    """
    parent_dir='/'.join(f.split('/')[:-1])
    return parent_dir


def df_to_csv(df, outname):
    """

    Parameters
    ----------
    df : df
        df containing table information from AFNI text report.
    outname : str
        path to output file..

    Returns
    -------
    None.

    """
    df.to_csv(outname)


if __name__ == "__main__":
    main()

