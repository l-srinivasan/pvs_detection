#!/bin/bash -i
set -e 

#====================================================================================================================

# Name:         find_PVS.sh
# Author:       Leela Srinivasan
# Date:         03/10/2025

# Syntax:       find_PVS.sh p***
# Arguments:    Patient identifier

# Description:  PVS T1w segmentation-based detection output to volumetric mask and CSV
# Dependencies: FreeSurfer (recon-all run), AFNI, Python


#====================================================================================================================

function display_usage {
	echo -e "\033[0;35m++ usage: $0 [-h|--help]  [-l|--list SUBJ_LIST] [SUBJ [SUBJ ...]] ++\033[0m"
	exit 1
}


subj_list=false
while [ -n "$1" ]; do
    case "$1" in
    	-h|--help) 		display_usage ;;	
        -l|--list)      subj_list=$2; shift ;; 
	    *) 				subj=$1; break ;;	
    esac
    shift 	
done


#Verify arg
if [[ ${subj_list} != "false" ]]; then
    if [ ! -f ${subj_list} ]; then
        echo -e "\033[0;35m++ subject_list doesn't exist. ++\033[0m"
        exit 1
    else
        subj_arr=($(cat ${subj_list}))
    fi
else
    subj_arr=("$@")
fi


#Prompt arg request
if [[ ! ${#subj_arr} -gt 0 ]]; then
	echo -e "\033[0;35m++ Subject list length is zero; please specify at least one subject to perform batch processing on ++\033[0m"
	display_usage
fi


#Check operating system
unameOut="$(uname -s)"
case "${unameOut}" in
    Linux*)     neu_dir="/shares/NEU";;
    Darwin*)    neu_dir="/Volumes/shares/NEU";;
    *)          echo -e "\033[0;35m++ Unrecognized OS. Must be either Linux or Mac OS in order to run script.\
						 Exiting... ++\033[0m"; exit 1
esac


scripts_dir=${neu_dir}/Scripts_and_Parameters/scripts/PVS_scripts
pvs_dir=${neu_dir}/Projects/PVS
deriv_dir="${neu_dir}/Data/derivatives/freesurfer-6.0.0"
bids_root=${neu_dir}/Data


for subj in "${subj_arr[@]}"; do

    
    echo -e "\033[0;35m++ Working on $subj ++\033[0m"
    
    
    #Establish FreeSurfer recon-all directory
    subj_fs_dir=${deriv_dir}/sub-${subj}_ses-clinical
    ses='clinical'
    if [ ! -d $subj_fs_dir ]; then
        subj_fs_dir=${deriv_dir}/sub-${subj}_ses-altclinical
        ses='altclinical'
        if [ ! -d $subj_fs_dir ]; then
            echo -e "\033[0;35m++ Freesurfer directory not found. Run freesurfer_proc.sh. ++\033[0m"
            exit 1
        fi
    fi
    
    
    #Initialize working pvs directory
    subj_pvs_dir=${pvs_dir}/${subj}
    if [ ! -d $subj_pvs_dir ]; then
        mkdir -p $subj_pvs_dir
    fi
    
    
    #Initialize t1 directory
    subj_pvs_t1_dir=${pvs_dir}/${subj}/t1
    if [ ! -d $subj_pvs_t1_dir ]; then
        mkdir -p $subj_pvs_t1_dir
    fi
    
    
    #Check if process complete
    if [ -d ${subj_pvs_t1_dir}/csv ]; then
        echo -e "\033[0;35m++ PVS processing complete. Delete to rerun. Exiting... ++\033[0m"
        exit 1
    fi
    
    
    #Check if research t1 exists
    use_research=0
    research_dir=${bids_root}/sub-${subj}/ses-research/anat
    if [ -d ${research_dir} ]; then
        for filename in ${research_dir}/*T1w.nii*; do
            cp ${filename} ${subj_pvs_t1_dir}/$(basename "$filename")
            use_research=1
            research_t1=${subj_pvs_t1_dir}/$(basename "$filename")
        done
    fi
    
    
    #Copy in SurfVol from FreeSurfer recon-all directory
    if [ -f $subj_fs_dir/SUMA/sub-${subj}_ses-${ses}_SurfVol.nii ]; then
        cp $subj_fs_dir/SUMA/sub-${subj}_ses-${ses}_SurfVol.nii ${subj_pvs_t1_dir}/sub-${subj}_ses-${ses}_SurfVol.nii
    else
        echo -e "\033[0;35m++ SurfVol not found in FreeSurfer directory. Exiting... ++\033[0m"
        rm -rf $subj_pvs_dir
        exit 1
    fi
    
    
    #Designate t1; align to FS space if needed
    if [ "$use_research" -eq "1" ]; then
        echo -e "\033[0;35m++ Continuing with research t1. ++\033[0m"
        3dAllineate                                                                         \
             -base              ${subj_pvs_t1_dir}/sub-${subj}_ses-${ses}_SurfVol.nii       \
             -source            ${research_t1}                                                       \
             -prefix            ${subj_pvs_t1_dir}/aligned_t1.nii      
        t1=${subj_pvs_t1_dir}/aligned_t1.nii          
    else
        t1=${subj_pvs_t1_dir}/sub-${subj}_ses-${ses}_SurfVol.nii
    fi
    
    
    #Unifize the t1 to increase contrast and separation between GM/WM classification
    if [ ! -f ${subj_pvs_t1_dir}/unifized_t1.nii ]; then
        3dUnifize                                                               \
            -input       ${t1}                                             \
            -GM                                                                 \
            -prefix     ${subj_pvs_t1_dir}/unifized_t1.nii
    fi
    
    
    #Perform intensity based segmentation on the t1 image
    if [ ! -d ${subj_pvs_t1_dir}/classification ]; then
        echo -e "\033[0;35m++ Performing Image Segmentation (CSF/GM/WM) on t1. Check classification in ${subj_pvs_t1_dir}/classification ++\033[0m"
        3dSeg                                                                   \
            -anat       ${subj_pvs_t1_dir}/unifized_t1.nii                 \
            -mask       AUTO                                                    \
            -classes    'CSF ; GM ; WM'                                         \
            -prefix     ${subj_pvs_t1_dir}/classification                       
    fi
        
        
    #Create binary masks using FreeSurfer segmentation
    masks_dir=${subj_pvs_dir}/masks
    if [ ! -d $masks_dir ]; then
        mkdir -p $masks_dir
    fi
    if [ -z "$(find ${masks_dir} -mindepth 1 -maxdepth 1)" ]; then
        python $scripts_dir/create_fs_masks.py \
            "$subj" 
    fi
    
    
    #Initialize subdirectories
    eroded_masks_dir=${subj_pvs_dir}/eroded_masks
    if [ ! -d $eroded_masks_dir ]; then
        mkdir -p $eroded_masks_dir
    fi
    
    
    #Erode masks to remove edge cases
    if [ -z "$(find ${eroded_masks_dir} -mindepth 1 -maxdepth 1)" ]; then
        for nifti in "$masks_dir"/*.nii ;do
            nifti_basename=$(basename ${nifti})
            struct=${nifti_basename%.*}
            echo -e "\033[0;35m++ Eroding the ${struct} mask. ++\033[0m"
            3dmask_tool                                                     \
                -input   ${nifti}                                           \
                -prefix  ${eroded_masks_dir}/eroded_${nifti_basename}        \
                -dilate_input -2 
        done
    fi
                 
                 
    #Initialize overlap, cluster and csv directories             
    t1_overlap_masks_dir=${subj_pvs_t1_dir}/overlap_masks
    if [ ! -d $t1_overlap_masks_dir ]; then
        mkdir -p $t1_overlap_masks_dir
    fi
    
    t1_clusters_dir=${subj_pvs_t1_dir}/clusters
    if [ ! -d $t1_clusters_dir ]; then
        mkdir -p $t1_clusters_dir
    fi
    
    t1_csv_dir=${subj_pvs_t1_dir}/csv
    if [ ! -d $t1_csv_dir ]; then
        mkdir -p $t1_csv_dir
    fi
    
    
    #Create overlap masks, clusters and csv files from AFNI txt reports
    if [ -z "$( ls -A ${t1_overlap_masks_dir} )" ]; then
        for nifti in "$masks_dir"/*.nii ; do
            nifti_basename=$(basename ${nifti})
            struct=${nifti_basename%.*}
                
                
            echo -e "\033[0;35m++ Extracting WM from eroded ${struct} mask. ++\033[0m"
            3dcalc                                                                \
                -a ${eroded_masks_dir}/eroded_${nifti_basename}                   \
                -b ${subj_pvs_t1_dir}/classification/Classes+orig                 \
                -expr 'step(a)*b'                                                 \
                -prefix ${t1_overlap_masks_dir}/overlap_${nifti_basename}
                
                
            #Isolate gm within eroded mask
            3dcalc                                                                \
                -a ${t1_overlap_masks_dir}/overlap_${nifti_basename}              \
                -expr 'equals(a,2)'                                               \
                -prefix ${t1_overlap_masks_dir}/gm_within_${nifti_basename}
            
            
            #Cluster gm classification within eroded mask to volumetrically group PVS
            3dClusterize                                                          \
                -inset ${t1_overlap_masks_dir}/gm_within_${nifti_basename}        \
                -NN 1                                                             \
                -1sided RIGHT 0.5                                                 \
                -ithr 0                                                           \
                -idat 0                                                           \
                -clust_nvox 2                                                     \
                -pref_map ${t1_clusters_dir}/pvs_within_${nifti_basename}         \
                > ${t1_clusters_dir}/pvs_within_${struct}.txt
            
            
            #Convert AFNI text file report to CSV 
            python $scripts_dir/afnitxt_to_csv.py                           \
                ${t1_clusters_dir}/pvs_within_${struct}.txt                        \
                ${t1_csv_dir}/pvs_within_${struct}.csv                                 
        done
    fi
    
    
    #Copy t2 from bids data folder
    anat_dir=${bids_root}/sub-${subj}/ses-${ses}/anat
    if [ -f ${anat_dir}/sub-${subj}_ses-${ses}_rec-axialized_T2w.nii.gz ]; then
        cp ${anat_dir}/sub-${subj}_ses-${ses}_rec-axialized_T2w.nii.gz ${subj_pvs_t1_dir}/sub-${subj}_ses-${ses}_rec-axialized_T2w.nii.gz
    else
        echo -e "\033[0;35m++ T2w image not found in BIDS anat directory. Exiting... ++\033[0m"
        exit 1
    fi
    t2=${subj_pvs_t1_dir}/sub-${subj}_ses-${ses}_rec-axialized_T2w.nii.gz
    
    
    #Align the t2 to FS space for clinical validation
    if [ ! -f ${subj_pvs_t1_dir}/aligned_t2.nii ]; then
        3dAllineate                                                                         \
             -base              ${subj_pvs_t1_dir}/sub-${subj}_ses-${ses}_SurfVol.nii       \
             -source            ${t2}                                                       \
             -prefix            ${subj_pvs_t1_dir}/aligned_t2.nii                                         
    fi
    
    
    #Move exams for manual verification
    rm ${t2}
    find ${subj_pvs_t1_dir} -maxdepth 1 -type f -name '*.nii*' -exec mv {} ${subj_pvs_t1_dir}/clusters \;
    echo -e "\033[0;35m++ Launch output maps from ${t1_clusters_dir} and load csv data from ${t1_csv_dir}. ++\033[0m"
    
    
done
