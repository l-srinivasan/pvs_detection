#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 3 16:11:24 2025
@author: Leela Srinivasan

Description: Pull desired segmentations from FreeSurfer, convert to nifti format and perform hemispheric merge.
Output to working PVS directory.

Dependencies: FreeSurfer (recon-all run), AFNI/SUMA

"""

import sys
import os
import shutil
import subprocess


def main():
    
    #Read args
    subj=sys.argv[1]
    
    
    #Set internal paths
    pvs_dir="/Volumes/Shares/NEU/Projects/PVS/{}".format(subj)
    pvs_masks_dir=os.path.join(pvs_dir, "masks")
    if not os.path.exists(pvs_masks_dir):
        raise Exception("PVS Project Masks Directory does not exist. Exiting...")
    session, fs_subj_dir, fs_mri_dir=set_freesurfer_paths(subj)
    
    
    """
    Input desired FreeSurferColorLUT numbers/label pairs.
    Refer to https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/AnatomicalROI/FreeSurferColorLUT
    """
    fs_colorlut=[(2, "left_cerebral_white_matter"),
                 (41, "right_cerebral_white_matter")]
    
    binarize_and_convert_masks(fs_mri_dir, pvs_masks_dir, fs_colorlut)
    
  
def set_freesurfer_paths(subj):
    """

    Parameters
    ----------
    subj : str
        pnum.

    Raises
    ------
    Exception
        FreeSurfer recon-all not run.

    Returns
    -------
    session : str
        clinical/altclinical.
    fs_subj_dir : str
        path to subject's FreeSurfer.
    fs_mri_dir : str
        path to subject's FreeSurfer mri subdir.

    """

    fs_dir="/Volumes/Shares/NEU/Data/derivatives/freesurfer-6.0.0/"
    if os.path.exists(os.path.join(fs_dir, "sub-{}_ses-clinical".format(subj))):
        session="ses-clinical"
    elif os.path.exists(os.path.join(fs_dir, "sub-{}_ses-altclinical".format(subj))):
        session="ses-altclinical"
    else:
        raise Exception("Subject Freesurfer directory not found. Exiting...")
    
    fs_subj_dir=os.path.join(fs_dir, "sub-{}_{}".format(subj, session))
    fs_mri_dir=os.path.join(fs_subj_dir, "mri")
    return session, fs_subj_dir, fs_mri_dir
    

def binarize_and_convert_masks(fs_mri_dir, wdir, matches):
    """

    Parameters
    ----------
    fs_mri_dir : str
        path to subject's FreeSurfer mri subdir.
    wdir : str
        working directory (in this case, pvs Project dir).
    matches : list
        list of ordered pairs.
        Refer to https://surfer.nmr.mgh.harvard.edu/fswiki/FsTutorial/AnatomicalROI/FreeSurferColorLUT

    Returns
    -------
    None.

    """
    
    os.chdir(fs_mri_dir)
    for match, label in matches:
        
        if not os.path.exists(os.path.join(wdir, "{}.nii".format(label))):
            #Binarize the segmented region
            cmd1 = "mri_binarize --i aseg.mgz --match {} --o {}.mgz"
            cmd1=cmd1.format(match, label)
            subprocess.run(cmd1, shell=True)
            
            #Convert the mask to nifti format
            cmd2 = "mri_convert {}.mgz {}.nii"
            cmd2=cmd2.format(label, label)
            subprocess.run(cmd2, shell=True)
            
            #Remove/move mask files
            os.remove(os.path.join(fs_mri_dir, "{}.mgz".format(label)))
            shutil.move(os.path.join(fs_mri_dir, "{}.nii".format(label)),os.path.join(wdir, "{}.nii".format(label)))
        
        
if __name__ == "__main__":
    main()
        

        
