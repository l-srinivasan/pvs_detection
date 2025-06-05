#!/bin/bash -i

#====================================================================================================================

# Name:         batch_process.sh
# Author:       Leela Srinivasan
# Date:         03/10/2025

# Syntax:       batch_process.sh

# Description:  Batch process PVS segmentation-based detection 
#               Output to volumetric mask and CSV
#               Compile stats and integrate to PVS and HV excel files in /Volumes/Shares/NEU/Projects/PVS/summary
    
# Dependencies: FreeSurfer (recon-all run), AFNI, Python


#====================================================================================================================

#Create subject list and HV list
scripts_dir="/Volumes/Shares/NEU/Scripts_and_Parameters/scripts/PVS_scripts"
python ${scripts_dir}/key_conversion.py


#Run all subjects through PVS processing
subject_list="/Volumes/Shares/NEU/Projects/PVS/summary/pnums.txt"
while IFS= read -r line; do
    bash $scripts_dir/find_PVS.sh \
       "$line"
done < "$subject_list"


#Run all HVs through PVS processing
hv_list="/Volumes/Shares/NEU/Projects/PVS/summary/hvs.txt"
while IFS= read -r line; do
    bash $scripts_dir/find_PVS_hv.sh \
       "$line"
done < "$hv_list"


#Compile and push summary stats
python ${scripts_dir}/compile_stats.py
