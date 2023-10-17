"""A quick-and-dirty wrapper (really, some of the code is garbage) for caracal to
perform imaging, selfcal and source-finding on a single target field using
pre-computed crosscal solutions. The code is *requested to be developed as it is*,
with no modulation, dedicated cleaning, logging or workflow management solutions,
only a standalone script. The script is designed for OTF snapshot imaging.

The code *should* be readable, but some comments are added nonetheless.

TO DO: add dedicated logging for execution and later debugging. In particular when the MS is flagged!

To DO: refactoring the code to make swapping logical components easy.

NOTE: the TO DO-s were expected to be TO DO-s during development due to the priorities
    of the management.

Author: K. Rozgonyi (rstofi@gmail.com)
License: GNU GPLv3
"""

import os
import configparser
import argparse
import copy
import numpy as np
from distutils.dir_util import copy_tree
import shutil
import fileinput
import subprocess
from katbeam import JimBeam
from astropy.io import fits
from astropy import wcs
import bdsf
from casacore import tables as casatables
import json
import psutil
import matplotlib.pyplot as plt

# === Functions ===
def get_args():
    """
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c',
        '--config_file',
        required=True,
        help='Configuration file',
        action='store',
        type=str)

    parser.add_argument(
        '-o',
        '--output_dir_path',
        required=False,
        default=None,
        help='Where the output goes',
        action='store',
        type=str)

    parser.add_argument(
        '-r',
        '--run_dir_path',
        required=False,
        default=None,
        help='Where caracal runs',
        action='store',
        type=str)

    parser.add_argument(
        '-t',
        '--target',
        required=False,
        default=None,
        help='Target field name',
        action='store',
        type=str)

    parser.add_argument(
        '-ssf',
        '--skip_source_finding',
        required=False,
        action='store_true',
        help='When enabled the worker skips the source finding part')

    parser.add_argument(
        '-osf',
        '--only_source_finding',
        required=False,
        action='store_true',
        help='When enabled the worker only executes source finding')

    parser.add_argument(
        '-g',
        '--generate_template',
        required=False,
        action='store_true',
        help='When enabled the worker only creates an empty template config file')


    args = parser.parse_args()

    return args.__dict__

def get_params(comment_char:str='#') -> dict:
    """
    """
    dict_args = get_args()

    #Generate template config file here if needed
    if dict_args['generate_template'] == True:
        generate_params_template(dict_args['config_file'])
        exit()

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(dict_args['config_file'])

    #Get rid of any comments at the end of lines as this is not supported by configparse
    config_params = dict(config.items('params'))

    for key, val in config_params.items():
        config_params[key] = val.split()[0].strip() #Remove end of line commands

    #Deal with optional parameters
    convert = lambda x, r: eval(x) if isinstance(r(x), bool) else r(x)

    #Hard-coded list of optional parameters
    _optional_params_list = ['obs_band', 'trim_box', 'box_size',
                        'create_sub_band_images', 'deep_clean', 'use_symlink']
    _optional_params_defaults_list = ['L', 'False', '0.5', 'False', 'False', 'True']
    _optional_param_types_list =  [str, bool, float, bool, bool, bool]

    for i in range(0,len(_optional_params_list)):
        if _optional_params_list[i] not in config_params.keys() or\
            not config_params[_optional_params_list[i]].strip():
            config_params[_optional_params_list[i]] = _optional_params_defaults_list[i]
        
        config_params[_optional_params_list[i]] = convert(config_params[_optional_params_list[i]], _optional_param_types_list[i])

    if config_params['obs_band'] not in ['L', 'UHF']:
        raise ValueError('Invalid observing band: {0:s}'.format(config_params['obs_band']))

    #Join parser args and config args
    del dict_args['config_file']

    for key, val in dict_args.items():
        if val is not None:
            config_params[key] = val

    return config_params

def generate_params_template(temaplate_name:str) -> int:
    """
    Hard-coded template config file
    """
    data = {"params" :{
            "output_dir_path" : " #Mandatory, absolute path",
            "ms_dir_path" : " #Mandatory, absolute path",
            "caltables_path" : " #Mandatory, absolute path",
            "template_cfg" : " #Mandatory, absolute path",
            "run_dir_path" : " #Mandatory, absolute path",
            "singularity_dir" : " #Mandatory, absolute path",
            "target" : " #Mandatory, string",
            "data_id" : " #Mandatory, string",
            "prefix" : " #Mandatory, string",
            "pybdsf_setup_path" : " #Mandatory, absolute path",
            "obs_band" : "L #Optional, string (valid: L, UHF)",
            "trim_box" : "False #Optional, bool",
            "box_size" : "0.5 #Optional, float",
            "create_sub_band_images" : "False #Optional, bool",
            "deep_clean" : "False #Optional, bool",
            "use_symlink" : "True #Optional, bool"
            }}

    config = configparser.ConfigParser()
    config.read_dict(data)
    with open(temaplate_name, 'w') as configfile:
        config.write(configfile)

    return 0

def prepare_dir(dir_path:str, remove_only:bool=False) -> int:
    """
    """
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

    if not remove_only:
        os.makedirs(dir_path)

    return 0

def prepare_output_tree(input_caltables_path:str,
                        output_dir_path:str,
                        data_id:str,
                        prefix:str,
                        label_cal:str='1gc1',
                        use_symlink:bool=True) -> None:
    """
    Set up the output directory tree for caracal run and copy the caltables from
    the crosscal solutions.

    OPTIONAL TO DO: ignore the first iterations of the Jones-terms (e.g G0, G1, K0...etc.)
        and only colpy the final solutions. (only relevant with `use_symlink`=False)
    """
    subdirs_list = ['caracal_MS', 'caracal_output']

    for subdir in subdirs_list:
        subdir_path = os.path.join(output_dir_path, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)

    # `subdir_path` is set to 'caracal_output' after the loop...

    #Use symlink
    if use_symlink:
        #Remove if exist to avoid data multiplication with different names
        prepare_dir(os.path.join(subdir_path,'caltables'), remove_only=False)

        #Handle the yml file
        cal_files_list = [f for f in os.listdir(input_caltables_path)
                            if os.path.isfile(os.path.join(input_caltables_path, f))]

        if len([i for i in cal_files_list if '.yml' in i])!= 1:
            raise ValueError("None or more than one .yaml file copied")
        else:
            os.symlink(os.path.join(input_caltables_path,cal_files_list[0]),
                        os.path.join(os.path.join(subdir_path,'caltables'),
                        'callib-{0:s}-{1:s}-{2:s}.yml'.format(prefix,data_id,label_cal)))

        #Handle the caltables
        cal_dir_list = [d for d in os.listdir(input_caltables_path)
                        if os.path.isdir(os.path.join(input_caltables_path, d))]

        for d in cal_dir_list:
            os.symlink(os.path.join(input_caltables_path,d), os.path.join(os.path.join(subdir_path,'caltables'),os.path.basename(d)),target_is_directory=True)

    else:
        #Remove if exist to avoid data multiplication with different names
        prepare_dir(os.path.join(subdir_path,'caltables'), remove_only=True)

        copy_tree(input_caltables_path, os.path.join(subdir_path,'caltables'))

        caltables_copied_objects_list = os.listdir(os.path.join(subdir_path,'caltables'))

        if len([i for i in caltables_copied_objects_list if '.yml' in i]) != 1:
            raise ValueError("None or more than one .yaml file copied")
        else:
            os.rename(os.path.join(os.path.join(subdir_path,'caltables'),[i for i in caltables_copied_objects_list if '.yml' in i][0]),
                os.path.join(os.path.join(subdir_path,'caltables'),'callib-{0:s}-{1:s}-{2:s}.yml'.format(prefix,data_id,label_cal)))
    return 0 

def deep_clean_output_dir(output_dir_path:str) -> int:
    """
    """
    subdirs_list = ['caracal_MS', 'caracal_output']
    for subdir in subdirs_list:
        subdir_path = os.path.join(output_dir_path, subdir)
        if os.path.exists(subdir_path):
            shutil.rmtree(subdir_path)

    return 0

def overwrite_line_in_yml(yml_path:str,
                        param_string:str,
                        new_param_string:str) -> int:
    """
    """
    for line in fileinput.input(yml_path, inplace = 1): 
        if param_string in line:
            line = line[0:line.rfind(param_string) + len(param_string)] + \
            ' ' + new_param_string + os.linesep
        print(line, end='')

    return 0

def populate_yml(yml_path:str,
                output_dir_path:str,
                MS_dir_path:str,
                data_id:str,
                prefix:str,
                target:str) -> int:
    """
    This function overwrites the *key* parameters in a caracal yaml file to enable
    'custom' imaging with unique input data.

    Notes:
    - fcal needs space to avoid conflict with other params
    """

    brckt = lambda x: '[' + x + ']'

    params_list = ['msdir:', 'rawdatadir:', 'output:', 'prefix:', 'dataid:', 'target:', 'gcal:', ' fcal:', 'bpcal:', 'xcal:']
    new_params_list = [os.path.join(output_dir_path,'caracal_MS'), MS_dir_path, os.path.join(output_dir_path,'caracal_output'),
                        prefix,  brckt(data_id)] + [brckt(target)] * 5

    for p, n_p in zip(params_list,new_params_list):
        overwrite_line_in_yml(yml_path,p,n_p)

    return 0

def get_field_id_based_on_name_from_MS(mspath:str,
                                        field_name:str) -> int:
    """
    """

    MS = casatables.table(mspath, ack=True, readonly=True)

    # === Get the FIELD sub-table
    # Select all sub strings containing `subtable_name` and select the first result
    # NOTE: only one table should exist named `/subtable_name`
    field_table_path = [subtables_path for subtables_path in MS.getsubtables(
    ) if '/' + 'FIELD' in subtables_path][0]

    # Get the index of the dash using reverse
    fieldtable_dash_index = field_table_path.rindex("/")

    field_table_path = field_table_path[:fieldtable_dash_index] + \
        "::" + field_table_path[fieldtable_dash_index + 1:]


    field_table = casatables.table(field_table_path, ack=True, readonly=True)

    MS.close()

    # The row number in the ANTENNA table corresponds to the field ID
    # See: https://casaguides.nrao.edu/index.php?title=Measurement_Set_Contents

    # I *assume* the same thing is true for the FIELD ID

    field_id = None
    for i in field_table.rownumbers():

        if field_name == field_table.getcol('NAME')[i]:
            field_id = i

    field_table.close()

    if field_id == None:
        raise ValueError('No field {0:s} found in target MS!'.format(field_name))
    else:
        #print(field_name,field_id)
        return field_id

def check_MS_flags(MS_dir_path:str,
                    data_id:str,
                    target:str,
                    flag_threshold=0.99,
                    speedup:bool=False) -> int:
    """
    Simple script to check if an input MS is flagged beyond a threshold. Needed to
    avoid imaging heavily-flagged data in which caracal would likely fail during
    selfcal.

    Note: enabling the `speedup` option makes use of the `FLAG_ROW` column instead
            of the `FLAG` column from the MS, but it does not always work if the
            flags are not set properly!
    """
    mspath = os.path.join(MS_dir_path,data_id + '.ms')
    
    MS = casatables.table(mspath, ack=True, readonly=True)

    field_id = get_field_id_based_on_name_from_MS(mspath, target)

    if speedup:
        flag_data = MS.query(query='FIELD_ID IN {0:d}'.format(field_id),
                        columns='FLAG_ROW')

        flags = flag_data.getcol('FLAG_ROW')
    else:

        flag_data = MS.query(query='FIELD_ID IN {0:d}'.format(field_id),
                        columns='FLAG')

        flags = flag_data.getcol('FLAG')

    if np.divide(np.sum(flags),np.size(flags)) >= flag_threshold:
        MS.close()
        raise ValueError('Over {0:.2f} of the visibilities are flagged, terminating!'.format(flag_threshold))
    else:
        MS.close()
        return 0

def get_subband_images_list(output_dir_path:str,
                            N_selfcal_cycles:int=2) -> list:
    """
    """
    images_path = os.path.join(output_dir_path, 'caracal_output/continuum/image_{0:s}'.format(str(int(N_selfcal_cycles))))
    subband_image_list = [os.path.join(images_path, f) for f in os.listdir(images_path) if f.endswith('image.fits') and not f.endswith('MFS-image.fits')]

    return subband_image_list

def get_MFS_image(output_dir_path:str,
                N_selfcal_cycles:int=2) -> str:
    """
    """
    images_path = os.path.join(output_dir_path, 'caracal_output/continuum/image_{0:s}'.format(str(int(N_selfcal_cycles))))
    return [os.path.join(images_path, f) for f in os.listdir(images_path) if f.endswith('MFS-image.fits')][0]

def get_PB_data(fimage_path:str,
                use_mask:bool=True,
                mask_below:float=0.1,
                obs_band='L') -> np.ndarray:
    """
    Generate the PB data based on a fits image.

    Note: the current code only supports L-band PB models!
    """
    hdu_header = fits.getheader(fimage_path)

    nu = int(hdu_header['CRVAL3'] * 1e-6)
    npx = hdu_header['NAXIS1']
    b_extent = npx * np.fabs(hdu_header['CDELT1'])

    margin=np.linspace(-b_extent/2.,b_extent/2.,npx)
    x,y=np.meshgrid(margin,margin)

    if obs_band == 'L':
        Mbeam=JimBeam('MKAT-AA-L-JIM-2020')
    elif obs_band == 'UHF':
        Mbeam=JimBeam('MKAT-AA-UHF-JIM-2020')

    beampixels=Mbeam.I(x,y,nu)

    if use_mask:
        beampixels[beampixels <= mask_below] = np.nan

    return beampixels

def get_freq(fimage_path:str) -> float:
    """
    """
    hdu_header = fits.getheader(fimage_path)
    freq = float(hdu_header['CRVAL3'])
    
    return freq

def get_PB_weight(fimage_path:str) -> float:
    """
    """
    hdu_header = fits.getheader(fimage_path)
    weight = hdu_header['WSCIMGWG']
    
    return weight

def get_fimage_xy_dat(fimage_path:str) -> np.ndarray:
    """
    """
    hdu_data = fits.getdata(fimage_path)

    return hdu_data[0,0,...]

def get_fimage_xy_shape(fimage_path:str) -> tuple:
    """
    """
    hdu_header = fits.getheader(fimage_path)
    xy_extent = int(hdu_header['NAXIS1'])

    if xy_extent != int(hdu_header['NAXIS2']):
        raise ValueError('Image {0:s} is not square!').format(fimage_path)

    return (xy_extent,xy_extent)

def get_fimage_cutout(fimage_path:str,cutout_extent:float=0.75) -> tuple:
    """Quick and dirty implementation... TO DO: speed it up
    """
    xy_extent = get_fimage_xy_shape(fimage_path)[0]


    if cutout_extent >= 1.:
        return tuple([0,int(xy_extent - 1),0,int(xy_extent - 1)])

    central_px_index = np.floor(xy_extent * 0.5) - 1
    half_cutout_extent_px = cutout_extent * xy_extent * 0.5

    cutout_corners = [int(np.ceil(central_px_index - half_cutout_extent_px)),
                    int(np.ceil(central_px_index + half_cutout_extent_px)),
                    int(np.ceil(central_px_index - half_cutout_extent_px)),
                    int(np.ceil(central_px_index + half_cutout_extent_px))] #(xmin, xmax, ymin, ymax)

    return tuple(cutout_corners)

def generate_PB_images(output_dir_path:str, use_mask:bool=True, obs_band:str='L') -> int:
    """
    This function is not used ???
    """
    subband_image_list = get_subband_images_list(output_dir_path)

    for sim in subband_image_list:
        b_sim = os.path.join(os.path.join(output_dir_path,'beams'),os.path.basename(sim).replace('image','pb'))
        shutil.copyfile(sim,b_sim)

        with fits.open(b_sim, mode='update') as ff: ff[0].data[0,0,...] = get_PB_data(sim,
                                                                            use_mask=use_mask,
                                                                            obs_band=obs_band)

    return 0

def get_PB_corrected_images(output_dir_path:str, create_sub_band_images:bool=True, obs_band:str='L') -> int:
    """
    NOTE: this is a quite important function and it is poorly written/designed

    TO DO: make this function more modular and readable

    TO DO: separate the cube generation to a distinct function and call it in a 
        linear fashion to ~third memory usage... (mostly useful for local testing)

    This function copies over the non-PB corrected MFS image to the results/ 
    directory, creates the PB-corrected MFS image, creates a PB-corrected cube from
    the sub-band images. In addition, it generates all-sub-band beam models under beams/

    The PB-corrected sub-band cube is ordered by increasing frequency and has the
    MFS synthesized beam added to the header. In addition, a secondary HDU (BinaryTable)
    is created with the sub-band synthesized beam information.

    NOTE: the code creates images with no masking is applied when PB correction.
        These images have `*pb_nonan_*` instead of `*pb_*` in their names

    NOTE: the code generates a cube with the PB models that is used to get the
        effective frequency maps. These maps should be generated separately, but
        the code is already so ugly that it is simpler to include it here...

        I am not sure if I use the `'right'` formulae for computing these maps.

        The original formula can be find in `Heywood et al., 2022, MNRAS 509, 2150-2168`

        i.e. the MIGHTEE early science fields paper.

        In eq 3. they use the 1 $\sigma$ RMS level for each sub-band, but I use
        the imaging weights in my code. These weights, however, should capture both
        the relative visibility sensitivity and imaging weights for each sub-band,
        and so, they should be used...

    """
    MFS_im = get_MFS_image(output_dir_path)

    PBc_im = os.path.join(os.path.join(output_dir_path,'results'),
        os.path.basename(MFS_im).replace('image','pb_corrected_image'))
    cube_im = os.path.join(os.path.join(output_dir_path,'results'),
        os.path.basename(MFS_im).replace('image','pb_nonan_corrected_cube'))
 
    non_masked_PBc_im = os.path.join(os.path.join(output_dir_path,'results'),
        os.path.basename(MFS_im).replace('image','pb_nonan_corrected_image'))

    ef_image = os.path.join(os.path.join(output_dir_path,'results'),
        os.path.basename(MFS_im).replace('image','effective_frequency_image'))

    shutil.copyfile(MFS_im,os.path.join(os.path.join(output_dir_path,'results'),os.path.basename(MFS_im)))
    shutil.copyfile(MFS_im,PBc_im)
    shutil.copyfile(MFS_im,non_masked_PBc_im)
    shutil.copyfile(MFS_im,ef_image)

    #PB correction
    subband_image_list = get_subband_images_list(output_dir_path)

    #Set up cube wcs
    MFS_HDU = fits.open(MFS_im)[0].header
    cube_wcs = copy.deepcopy(wcs.WCS(MFS_HDU))

    cube_wcs.wcs.cdelt[2] = wcs.WCS(fits.open(subband_image_list[0])[0].header).wcs.cdelt[2]
    cube_wcs._naxis[2] = len(subband_image_list)

    subband_beams = []
    freqs = []
    img_weights = []
    for sim in subband_image_list:
        sim_header = fits.getheader(sim)
        freqs.append(float(sim_header['CRVAL3']))
        subband_beams.append((sim_header['BMAJ'],sim_header['BMIN'],sim_header['BPA']))
        img_weights.append(float(sim_header['WSCIMGWG']))

    freqinds = np.array(freqs).argsort()
    sorted_freqs = np.array(freqs)[freqinds]
    sorted_subband_image_list = np.array(subband_image_list)[freqinds]
    sorted_subband_beams = np.array(subband_beams)[freqinds]
    sorted_subband_weights = np.array(img_weights)[freqinds]

    cube_wcs.wcs.crval[2] = wcs.WCS(fits.open(sorted_subband_image_list[0])[0].header).wcs.crval[2]

    cube_data = np.zeros(cube_wcs._naxis)

    PBc_dat = np.zeros(get_fimage_xy_shape(MFS_im))
    non_masked_PBc_dat = np.zeros(get_fimage_xy_shape(MFS_im))
    ef_dat = np.zeros(get_fimage_xy_shape(MFS_im))
    weighted_PB_dat = np.zeros(get_fimage_xy_shape(MFS_im))
    sumw = 0.

    if create_sub_band_images:
        os.makedirs(os.path.join(output_dir_path,'results/sub_band_images'))

    for sim, i in zip(sorted_subband_image_list,range(0,cube_wcs._naxis[2])):

        if create_sub_band_images:
            PBc_sim = os.path.join(os.path.join(output_dir_path,'results/sub_band_images'),
                            os.path.basename(sim).replace('image','pb_corrected_image'))
            shutil.copyfile(sim,PBc_sim)

            non_masked_PBc_sim = os.path.join(os.path.join(output_dir_path,'results/sub_band_images'),
                            os.path.basename(sim).replace('image','pb_nonan_corrected_image'))
            shutil.copyfile(sim,non_masked_PBc_sim)

        PB_weight = get_PB_weight(sim)

        #Ignore empty channels
        if int(PB_weight) != 0:
            sim_dat = get_fimage_xy_dat(sim)
            PB_dat = get_PB_data(sim,obs_band=obs_band)    
            sim_freq = get_freq(sim)

            non_masked_PB_dat = get_PB_data(sim, use_mask=False, obs_band=obs_band) 

            sim_corrected_dat = sim_dat / PB_dat
            non_masked_sim_corrected_dat = sim_dat / non_masked_PB_dat

            if create_sub_band_images:
                with fits.open(PBc_sim, mode='update') as ff: ff[0].data[0,0,...] = sim_corrected_dat
                with fits.open(non_masked_PBc_sim, mode='update') as ff: ff[0].data[0,0,...] = non_masked_sim_corrected_dat

            PBc_dat += PB_weight * sim_corrected_dat
            sumw += PB_weight

            non_masked_PBc_dat += PB_weight * non_masked_sim_corrected_dat

            ef_dat += PB_weight * non_masked_PB_dat * sim_freq
            weighted_PB_dat += PB_weight * non_masked_PB_dat

            #cube_data[...,i,0] = sim_corrected_dat #Use masking
            cube_data[...,i,0] = non_masked_sim_corrected_dat #Do not use masking


    #rearrange for fits standard
    cube_data = np.swapaxes(cube_data,0,3)
    cube_data = np.swapaxes(cube_data,1,2)
    cube_data = np.swapaxes(cube_data,2,3)

    PBc_dat /= sumw
    non_masked_PBc_dat /= sumw
    ef_dat /= weighted_PB_dat

    #Add header to cubes
    cube_header = cube_wcs.to_header()
    cube_hdu = fits.PrimaryHDU(cube_data, header=cube_header)
    cube_hdu.writeto(cube_im)
    
    with fits.open(cube_im, mode='update') as ff:
        ff[0].header['BSCALE'] = MFS_HDU['BSCALE']
        ff[0].header['BZERO'] = MFS_HDU['BZERO']
        ff[0].header['BUNIT'] = MFS_HDU['BUNIT']

        ff[0].header['BMAJ'] = MFS_HDU['BMAJ']
        ff[0].header['BMIN'] = MFS_HDU['BMIN']
        ff[0].header['BPA'] = MFS_HDU['BPA']

    #Create 'BEAMS' table HDU
    col1 = fits.Column(name='BMAJ', format='E', unit='arcsec', array=np.array([b[0] for b in sorted_subband_beams]))
    col2 = fits.Column(name='BMIN', format='E', unit='arcsec', array=np.array([b[1] for b in sorted_subband_beams]))
    col3 = fits.Column(name='BPA', format='E', unit='degree', array=np.array([b[2] for b in sorted_subband_beams]))
    col4 = fits.Column(name='FREQ', format='D', unit='Hz', array=sorted_freqs)
    col5 = fits.Column(name='STOKES', format='E', array=np.ones(np.size(sorted_freqs)))
    col6 = fits.Column(name='WSCIMGWG', format='D', array=sorted_subband_weights)

    beams_hdu = fits.BinTableHDU.from_columns([col1, col2, col3, col4, col5, col6])

    #Note: renaming this HDU to BEAMS is incompatible with some software... like pybdsf

    with fits.open(cube_im, mode='update') as ff: ff.append(beams_hdu)

    #Write PB corrected MFS images
    with fits.open(PBc_im, mode='update') as ff: ff[0].data[0,0,...] = PBc_dat
    with fits.open(non_masked_PBc_im, mode='update') as ff: ff[0].data[0,0,...] = non_masked_PBc_dat
    with fits.open(ef_image, mode='update') as ff: ff[0].data[0,0,...] = ef_dat

    #Adjust the header of the ef image
    with fits.open(ef_image, mode='update') as ff:
        ff[0].header['BUNIT'] = 'Hz'
        ff[0].header['BTYPE'] = 'FREQ'

    return 0

def get_beam_spectra_from_beams_table(fits_cube:str) -> list:
    """
    """

    beams_table = fits.open(fits_cube)[1]

    beam_spectrum = []
    for i in range(0,int(beams_table.header['NAXIS2'])):
        beam_spectrum.append((beams_table.data['BMAJ'][i],
                            beams_table.data['BMIN'][i],
                            beams_table.data['BPA'][i]))

    return beam_spectrum

def generate_effective_frequency_image_from_PB_cube(PB_cube_path:str,
                                                    output_dir_path:str) -> int:
    """
    See the NOTES in `get_PB_corrected_images` for more info
    """
    MFS_im = get_MFS_image(output_dir_path)

    ef_image = os.path.join(os.path.join(output_dir_path,'results'),
        os.path.basename(MFS_im).replace('image','effective_frequency_image'))

    shutil.copyfile(MFS_im,ef_image)

    #Get the effective frequency data
    pb_cube_data = fits.getdata(PB_cube_path)


def get_pybds_imag_params_from_json(json_path:str) -> dict:
    """
    Read in a the parameters for `bdsf.process_image` from a .json file and remove
    some custom paramters that are filled automatically.
    """
    with open(json_path) as j:
        img_process_params_dict = json.load(j)

    if 'rms_box' in img_process_params_dict.keys():
        img_process_params_dict['rms_box'] = tuple(img_process_params_dict['rms_box'])

    if 'rms_box_bright' in img_process_params_dict.keys():
        img_process_params_dict['rms_box_bright'] = tuple(img_process_params_dict['rms_box_bright'])

    custom_params = ['input', 'detection_image', 'collapse_av', 'beam_spectrum']

    for param in custom_params:
        if param in img_process_params_dict.keys():
            del img_process_params_dict[param]

    return img_process_params_dict

def do_source_finding(output_dir_path:str,
                    data_id:str,
                    json_path:str,
                    trim_box:bool=False,
                    box_size:float=0.75) -> str:
    """
    pybdsf source-finding and catalog generator function.
    """
    results_path = os.path.join(os.path.join(output_dir_path,'results'))

    sf_image = [os.path.join(results_path, f) for f in os.listdir(results_path) if f.endswith('pb_nonan_corrected_image.fits')][0]
    det_image = [os.path.join(results_path, f) for f in os.listdir(results_path) if f.endswith('MFS-image.fits')][0]

    img_process_params_dict = get_pybds_imag_params_from_json(json_path)

    img_process_params_dict['input'] = sf_image
    img_process_params_dict['detection_image'] = det_image
    img_process_params_dict['multichan_opts'] = False #Disable MFS imaging
    
    if trim_box:
        img_process_params_dict['trim_box'] = get_fimage_cutout(sf_image,box_size)

    img = bdsf.process_image(**img_process_params_dict)

    # Save catalog
    catalog_path = os.path.join(os.path.join(output_dir_path,'results'),
        os.path.basename(det_image).replace('MFS-image.fits','catalog.fits'))
    
    img.write_catalog(outfile=catalog_path,
                        catalog_type='gaul', #'gaul' for gaussian list
                        clobber=True,
                        format='fits',
                        incl_chan=True,
                        incl_empty=False,
                        srcroot=data_id)

    # Remove the pybdsf logfile and the folder created by bdsf
    # TO DO: add option to keep the detailed bdsf output folder not only the catalog

    logfiles = [ f for f in os.listdir(results_path) if f.endswith(".log") ]
    for f in logfiles:
        try: 
            os.remove(os.path.join(results_path, f))
        except:
            pass

    for im in [sf_image, det_image]:
        bdsf_output_folder_path = os.path.splitext(im)[0] + '_pybdsf'

        if os.path.exists(bdsf_output_folder_path):
            shutil.rmtree(bdsf_output_folder_path)

    return catalog_path

# ====================================
# === Pipeline execution functions ===
# ====================================

# === Handling flags
def flag_status_checkpointing(config_params:dict, flagged:bool) -> int:
    """
    """
    with open(os.path.join(config_params['output_dir_path'],'flag_status.json'), 'w') as outfile:
        json.dump({'flagged' : flagged}, outfile)

    return 0

def is_my_MS_flagged_questionmark(config_params:dict) -> bool:
    """
    Check the MS for excessive flagging
    """

    try:
        check_MS_flags(config_params['ms_dir_path'],
                        config_params['data_id'],
                        config_params['target'])
        flagged = False
    except Exception as e:
        print(e)
        flagged = True

    #This is for local testing => Uncomment this for running stuff
    flagged = False

    flag_status_checkpointing(config_params, flagged)

    return flagged

# === execution
def execute_worker(config_params:dict) -> int:
    """
    This function executes the pipeline if the MS has enough non-flagged visibilites
    """
    local_test = True

    if config_params['only_source_finding'] == True:
        if config_params['skip_source_finding'] == True:
            raise ValueError('Inconsistent worker configuration (source-finding conflict)!')

        #Here I expect that everything is done consistently, so no check are made!
        catalog_path = do_source_finding(config_params['output_dir_path'],
                                        config_params['data_id'],
                                        config_params['pybdsf_setup_path'],
                                        trim_box=config_params['trim_box'],
                                        box_size=config_params['box_size'])

    else:
        if not os.path.exists(config_params['output_dir_path']):
            os.mkdir(config_params['output_dir_path'])

        prepare_output_tree(input_caltables_path=config_params['caltables_path'],
                            output_dir_path=config_params['output_dir_path'],
                            data_id=config_params['data_id'],
                            prefix=config_params['prefix'],
                            use_symlink=config_params['use_symlink'])
        
        prepare_dir(config_params['run_dir_path'])

        shutil.copyfile(config_params['template_cfg'],
            os.path.join(config_params['run_dir_path'],'config.yml'))

        populate_yml(os.path.join(config_params['run_dir_path'],'config.yml'),
                    config_params['output_dir_path'],
                    config_params['ms_dir_path'],
                    config_params['data_id'],
                    config_params['prefix'],
                    config_params['target'])

        #Run caracal    
        #From this point can't check locally
        if local_test:
            crs = "echo 'caracal -c {0:s} -ct singularity -sid {1:s}'".format(
                os.path.join(config_params['run_dir_path'],'config.yml'),
                            config_params['singularity_dir'])
        else:
            crs = 'caracal -c {0:s} -ct singularity -sid {1:s}'.format(
                os.path.join(config_params['run_dir_path'],'config.yml'),
                            config_params['singularity_dir'])

        p = subprocess.run(crs, cwd=config_params['run_dir_path'], shell=True)

        #Simulate primary beams and apply correction

        #Help for local testing
        if local_test:
            #copy_tree('/home/krozgonyi/Desktop/playground/isaac_tests/blob/example_caracal_selfcal_output/caracal_output/continuum/image_2',
            #                    os.path.join(config_params['output_dir_path'],'caracal_output/continuum/image_2'))
            #copy_tree('/home/krozgonyi/test_demo_pipeline_crosscal/1631559762/example_selfcal/continuum/image_2',
            #                    os.path.join(config_params['output_dir_path'],'caracal_output/continuum/image_2'))

            copy_tree('/home/krozgonyi/test_demo_pipeline_crosscal/1631559762/high_res_imaging/continuum/image_2',
                                os.path.join(config_params['output_dir_path'],'caracal_output/continuum/image_2'))

        #Get PB corrected, non-PB corrected images and PB corrected cube
        prepare_dir(os.path.join(config_params['output_dir_path'],'results'))

        get_PB_corrected_images(config_params['output_dir_path'],
                                create_sub_band_images=config_params['create_sub_band_images'],
                                obs_band=config_params['obs_band'])

        #Source finding
        if config_params['skip_source_finding'] == False:
            do_source_finding(config_params['output_dir_path'],
                            config_params['data_id'],
                            config_params['pybdsf_setup_path'],
                            trim_box=config_params['trim_box'],
                            box_size=config_params['box_size'])

        #Clean up
        if config_params['deep_clean']:
            deep_clean_output_dir(config_params['output_dir_path'])

    return 0

# === MAIN ===
if __name__ == "__main__":
    config_params = get_params()

    flagged = is_my_MS_flagged_questionmark(config_params)

    if not flagged:
        execute_worker(config_params)

    #NOTE: don't forget to remove the local testing and MS return lines from the server version!