#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed May 28 15:46:35 2025
@author: Leela Srinivasan

Compare t2/t1 voxel intensity ranges in detected PVS structures, clinician determined PVS structures, and eroded WM hemispheric masks.
Dependencies: AFNI, Matplotlib
"""

import os
import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import zscore
    

def main():
    subj=sys.argv[1]
    pvs_dir, t1, t2=init(subj)
    for hemi in ["left", "right"]:
        
        
        #Generate and read 1d files, check for clinician drawn ROI mask and read
        mask=generate_1d(pvs_dir, hemi, t1, t2)
        t1_pvs, t2_pvs, t1_wm, t2_wm=read_1d(pvs_dir, hemi)    
        manual_exists, t1_man, t2_man=manual_validation(pvs_dir, hemi, mask, t1, t2)
        
        
        #Plot with or without manual validation mask / clear 1D hemi files from dir
        if manual_exists:
            plot_intensities_with_validation(pvs_dir, t1_pvs, t2_pvs, t1_wm, t2_wm, t1_man, t2_man, hemi, subj)
        else:
            plot_intensities(pvs_dir, t1_pvs, t2_pvs, t1_wm, t2_wm, hemi, subj)   
        clear_1d(pvs_dir,hemi)
        
        
def init(subj):
    """

    Parameters
    ----------
    subj : str
        p***.

    Returns
    -------
    pvs_dir : str
        path to subject PVS dir.
    t1 : str
        path to t1 nifti.
    t2 : str
        path to t2 nifti.

    """
    pvs_base='/Volumes/Shares/NEU/Projects/PVS/'
    pvs_dir=os.path.join(pvs_base, subj)
    
    t1=os.path.join(pvs_dir, "t1", "clusters", "aligned_t1.nii")
    t2=os.path.join(pvs_dir, "t1", "clusters", "aligned_t2.nii")
    
    return pvs_dir, t1, t2
    

def run_3dcalc(a, b, o):
    """

    Parameters
    ----------
    a : str
        path to input dataset 1.
    b : str
        path to input dataset 2.
    o : str
        path to output dataset.

    Returns
    -------
    None.

    """
    
    cmd="3dcalc -a {} -b {} -expr 'a*step(b)' -prefix {}"
    cmd=cmd.format(a,b,o)
    subprocess.run(cmd, shell=True)
    
    
def read_1d(pvs_dir, hemi):
    """

    Parameters
    ----------
    pvs_dir : str
        path to subject PVS dir..
    hemi : str
        left/right.

    Returns
    -------
    t1_pvs : array
        intensity values for detected PVS areas from the t1.
    t2_pvs : array
        intensity values for detected PVS areas from the t2.
    t1_wm : array
        intensity values for the eroded mask from the t1.
    t2_wm : array
        intensity values for the eroded mask from the t2.

    """
    
    
    clust_dir=os.path.join(pvs_dir, "t1", "clusters")
    
    f1=os.path.join(clust_dir, "t1_{}_pvs.1D".format(hemi))
    t1_pvs = np.genfromtxt(f1)
    
    f2=os.path.join(clust_dir, "t2_{}_pvs.1D".format(hemi))
    t2_pvs = np.genfromtxt(f2)
    
    f3=os.path.join(clust_dir,"{}wm_t1_intensities.1D".format(hemi))
    t1_wm=np.genfromtxt(f3)
                        
    f4=os.path.join(clust_dir,"{}wm_t2_intensities.1D".format(hemi))
    t2_wm=np.genfromtxt(f4)
    
    return t1_pvs, t2_pvs, t1_wm, t2_wm


def calc_ratios(t1_wm, t2_wm):
    """

    Parameters
    ----------
    t1_wm : array
        intensity values for the eroded mask from the t1.
    t2_wm : array
        intensity values for the eroded mask from the t2.

    Returns
    -------
    None. Saves to txt file.

    """
    
    ratios=np.divide(t2_wm, t1_wm, out=np.zeros_like(t2_wm), where=t1_wm!=0)
    ratios[ratios==0]=np.nan
    z=zscore(ratios, nan_policy="omit")
    binary_1D=np.array(z>2, dtype=int)
    
    o='/Volumes/Shares/NEU/Projects/PVS/p38/t1/clusters/o.txt'
    np.savetxt(o, binary_1D, fmt='%d', newline='\n')

    

def clear_1d(pvs_dir, hemi):
    """

    Parameters
    ----------
    pvs_dir : str
        path to subject PVS dir.

    Returns
    -------
    None. Clears 1D files from dir.

    """
    
    print("Clearing temporary 1D files...")
    clust_dir=os.path.join(pvs_dir, "t1", "clusters")
    for res in ["t1", "t2"]:
        f_list=["{}_{}_pvs.1D".format(res, hemi),
                "{}wm_{}_intensities.1D".format(hemi, res),
                "{}_manual_{}.1D".format(res,hemi)]
        
        for f in f_list:
            if f in os.listdir(clust_dir):
                os.remove(os.path.join(clust_dir, f))
        
        
def create_verification_nii(clust_dir):
    """

    Parameters
    ----------
    clust_dir : str
        path to cluster PVS dir.

    Returns
    -------
    None. Generate merged_pvs.nii for visualization purposes.

    """
    
    os.chdir(clust_dir)
    cmd1='3dcalc -a pvs_within_left_cerebral_white_matter.nii -b pvs_within_right_cerebral_white_matter.nii -expr "step(a)+step(b)" -prefix pvs_both.nii'
    subprocess.run(cmd1, shell=True)
    cmd2='3dcalc -a pvs_both.nii -b manpvs.nii -expr "step(a)+2*(step(b))" -prefix merged_pvs.nii'
    subprocess.run(cmd2, shell=True)
    
    
def manual_validation(pvs_dir, hemi, mask, t1, t2):
    """

    Parameters
    ----------
    pvs_dir : str
        path to subject PVS dir.
    hemi : str
        left/right.
    mask : str
        path to eroded WM mask.
    t1 : str
        path to t1.
    t2 : str
        path to t2.

    Returns
    -------
    bool
        True/False to plot manual validation markers.
    TYPE
        Manual markers on t1 in 1d format or None if n/a.
    TYPE
        Manual markers on t2 in 1d format or None if n/a.

    """
    
    
    clust_dir=os.path.join(pvs_dir, "t1", "clusters")
    manual_mask=os.path.join(clust_dir, "manpvs.nii")
    if "manpvs.nii" in os.listdir(clust_dir):
        
        #Restrict to one hemi's eroded interior
        o1=os.path.join(pvs_dir, "t1", "clusters", "manual_{}.nii".format(hemi))
        run_3dcalc(manual_mask, mask, o1)
        
        o2=os.path.join(pvs_dir, "t1", "clusters", "t1_manual_{}.1D".format(hemi))
        run_3dcalc(t1, o1, o2)
        
        o3=os.path.join(pvs_dir, "t1", "clusters", "t2_manual_{}.1D".format(hemi))
        run_3dcalc(t2, o1, o3)
        
        t1_man_1d = np.genfromtxt(o2)
        t2_man_1d = np.genfromtxt(o3)
        
        create_verification_nii(clust_dir)
        return True, t1_man_1d, t2_man_1d
    return False, None, None
        
    
def plot_intensities(pvs_dir, t1_pvs, t2_pvs, t1_wm, t2_wm, hemi, subj):
    """

    Parameters
    ----------
    t1_pvs : array
        intensity values for detected PVS areas from the t1.
    t2_pvs : array
        intensity values for detected PVS areas from the t2.
    t1_wm : array
        intensity values for the eroded mask from the t1.
    t2_wm : array
        intensity values for the eroded mask from the t2.

    Returns
    -------
    None. Plots intensities.

    """
    
    plt.scatter(t1_wm, t2_wm, c='red', marker='o')
    plt.scatter(t1_pvs, t2_pvs, c='blue', marker='o')
    plt.xlabel('T1 voxel intensity')
    plt.ylabel('T2 voxel intensity')
    plt.legend(['Eroded {} WM'.format(hemi), 'Detected PVS']) 
    plt.title('T2 vs T1 voxel intensity; {}'.format(subj))
    
    o=os.path.join(pvs_dir, "t1", "clusters", "{}_intensities.png".format(hemi))
    plt.savefig(o,bbox_inches='tight')
    print("Saving plot to subject's PVS clusters directory.")
    
    
def plot_intensities_with_validation(pvs_dir, t1_pvs, t2_pvs, t1_wm, t2_wm, t1_man, t2_man, hemi, subj):
    """

    Parameters
    ----------
    t1_pvs : array
        intensity values for detected PVS areas from the t1.
    t2_pvs : array
        intensity values for detected PVS areas from the t2.
    t1_wm : array
        intensity values for the eroded mask from the t1.
    t2_wm : array
        intensity values for the eroded mask from the t2.

    Returns
    -------
    None. Plots intensities.

    """
    
    plt.scatter(t1_wm, t2_wm, c='red', marker='o')
    plt.scatter(t1_man, t2_man, c='yellow', marker='o')
    plt.scatter(t1_pvs, t2_pvs, c='blue', marker='o')
    plt.xlim(xmin=100)
    plt.ylim(ymin=100)
    plt.xlabel('T1 voxel intensity')
    plt.ylabel('T2 voxel intensity')
    plt.legend(['Eroded {} WM'.format(hemi), 'Clinician markers', 'Detected PVS']) 
    plt.title('T2 vs T1 voxel intensity; {}'.format(subj))
    
    o=os.path.join(pvs_dir, "t1", "clusters", "{}_intensities.png".format(hemi))
    plt.savefig(o,bbox_inches='tight')
    print("Saving plot to subject's PVS clusters directory.")
  
    
def generate_1d(pvs_dir, hemi, t1, t2):
    """

    Parameters
    ----------
    pvs_dir : str
        path to subject PVS dir.
    hemi : str
        left/right.
    t1 : str
        path to t1.
    t2 : str
        path to t2.

    Returns
    -------
    mask : str
        path to eroded wm hemispheric mask.

    """
    
    mask=os.path.join(pvs_dir, "eroded_masks", "eroded_{}_cerebral_white_matter.nii".format(hemi))
    o1=os.path.join(pvs_dir, "t1", "clusters", "{}wm_t1_intensities.1D".format(hemi))
    o2=os.path.join(pvs_dir, "t1", "clusters", "{}wm_t2_intensities.1D".format(hemi))
    
    run_3dcalc(t1, mask, o1)
    run_3dcalc(t2, mask, o2)
    
    pvs=os.path.join(pvs_dir, "t1", "clusters", "pvs_within_{}_cerebral_white_matter.nii".format(hemi))
    o3=os.path.join(pvs_dir, "t1", "clusters", "t1_{}_pvs.1D".format(hemi))
    o4=os.path.join(pvs_dir, "t1", "clusters", "t2_{}_pvs.1D".format(hemi))
    
    run_3dcalc(t1, pvs, o3)
    run_3dcalc(t2, pvs, o4)
    
    return mask
    
      
if __name__ == "__main__":
    main()
    
            
            
            
    
    
