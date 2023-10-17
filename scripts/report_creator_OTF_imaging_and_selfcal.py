"""Quick and dirty (this is really an ugly code...) code to generate an automated
report from the `master_for_OTF_imaging_and_selfcal_workers.py` script output.

Super minimalist report of course in Jupyter notebook format.

Lots of copyed code... but ey, I *told* not to build anything complex, but only
standalone scripts...

Working on Python versions 3.5 - 3.9

Author: K. Rozgonyi (rstofi@gmail.com)
License: GNU GPLv3
"""

import os
import configparser
import argparse
import numpy as np
import nbformat as nbf
import copy
from astropy.io import fits
from astropy.wcs import WCS
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.axes as maxes
from mpl_toolkits.axes_grid1 import make_axes_locatable
import matplotlib.image as mpimg
import cv2
from IPython.display import Image, display
from typing import Union
import json

#=== Globals
#RCparams for plotting
matplotlib.rcParams['xtick.direction'] = 'in'
matplotlib.rcParams['ytick.direction'] = 'in'

matplotlib.rcParams['xtick.major.size'] = 3
matplotlib.rcParams['ytick.major.size'] = 3

matplotlib.rcParams['xtick.major.width'] = 2
matplotlib.rcParams['ytick.major.width'] = 2

matplotlib.rcParams['axes.linewidth'] = 1

plt.rcParams['xtick.labelsize']=12
plt.rcParams['ytick.labelsize']=12

#4 sampled colors from viridis
c0 = '#440154';#Purple
c1 = '#30678D';#Blue
c2 = '#35B778';#Greenish
c3 = '#FDE724';#Yellow

outlier_color = 'dimgrey'

#Select the colormap and set outliers
#_CMAP = matplotlib.cm.viridis
_CMAP = copy.copy(matplotlib.cm.get_cmap("viridis"))
_CMAP.set_bad(color=outlier_color)

# === Functions ===
def get_args() -> dict:
    """Config file for `master_for_OTF_imaging_and_selfcal_workers.py`
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
        '-r',
        '--report_output_dir',
        required=False,
        help='Absolute path where to generate the notebook (default: `master_output_dir`)',
        action='store',
        type=str)

    parser.add_argument(
        '-n',
        '--notebook_only',
        required=False,
        action='store_true',
        help='If set only the notebook is created, no analysis is done')

    args = parser.parse_args()

    args.config_file = os.path.abspath(args.config_file)

    return args.__dict__

def get_master_params() -> dict:
    """
    """
    dict_args = get_args()

    config = configparser.ConfigParser(allow_no_value=True)
    config.read(dict_args['config_file'])

    config_params = dict(config.items('setup'))
    config_params['master_cfg_path'] = dict_args['config_file']

    for key, val in dict_args.items():
        if val is not None:
            config_params[key] = val

    return config_params

def get_targets_from_config(config_file:str) -> np.ndarray:
    """
    """
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(config_file)

    targets = []

    path_items = config.items('targets')
    
    for key, target in path_items:
        targets.append(target)

    return np.array(targets)

def md_linebreak() -> str:
    """Markdown linebreak: 2 spaces + linebreak
    """
    return "  " + os.linesep

def fancy_print_notebook_cells(notebbok_node:nbf.notebooknode.NotebookNode) -> int:
    """
    Helper for development.
    """

    print('Notebokk node cells:' + os.linesep +\
        '--------------------' + os.linesep)

    for cell in notebbok_node['cells']:
        print('Cell ID: {0:s}'.format(cell.id))
        print('Cell type: {0:s}'.format(cell.cell_type))

        print('Cell content')
        for line in cell.source.split(os.linesep):

            print('    ' + line)

        #print('Cell content:\n {0:s}'.format())
        print('')

    return 0

def init_report_notebook(config_file:str,
                        output_dir_path:str) -> nbf.notebooknode.NotebookNode:
    """
    """

    nb = nbf.v4.new_notebook()

    #Header
    report_header = 'OTF imaging and selfcal report' + md_linebreak() + '===='

    nb['cells'].append(nbf.v4.new_markdown_cell(report_header))

    #Import required libraries and This script
    current_script_path = os.path.realpath(__file__)

    init_libs = ''

    libs_required = ['sys', 'os']

    for lib in libs_required:
        init_libs += "import {0:s}".format(lib) + md_linebreak()

    init_libs += md_linebreak() + '#Import functions from the report script:' + md_linebreak() +\
            "sys.path.append('{0:s}')".format(os.path.dirname(current_script_path)) + md_linebreak() +\
            "from {0:s} import *".format(os.path.splitext(os.path.basename(current_script_path))[0])

    nb['cells'].append(nbf.v4.new_code_cell(init_libs))    

    #Init some enviromental variables
    env_vars = "#Env variables used in this report" + md_linebreak() +\
                "config_file_path = '{0:s}'".format(config_file) + md_linebreak() +\
                "output_dir_path = '{0:s}'".format(output_dir_path)
    
    nb['cells'].append(nbf.v4.new_code_cell(env_vars))

    #Add metadata to kernel
    metadata = {"kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
            },
            "language_info": {
            "codemirror_mode": {
            "name": "ipython",
            "version": 3
            },
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.8.12"}
            }

    nb['metadata'] = metadata

    nb = nbf.convert(nb,to_version=4)

    return nb

def get_flag_status(target_dir_path:str):
    """
    """
    #Flag status json should exist
    flag_status_json = os.path.join(target_dir_path,'flag_status.json')

    return json.load(open(flag_status_json))['flagged']

def get_completion_statistics(config_file:str,
                            output_dir_path:str) -> str:
    """
    """

    completion_summary = 'Completion summary:' + os.linesep +\
                        '===================' + os.linesep

    targets = get_targets_from_config(config_file)

    completion_summary += "Found {0:d} targets in config".format(np.size(targets)) + os.linesep

    #Look for target dirs
    target_dirs_found = 0
    result_dirs_found = 0
    image_cubes_found = 0
    cataloges_found = 0
    fully_flagged_MS_found = 0

    for target in targets:
        target_dir = os.path.join(output_dir_path,target)
        if os.path.exists(target_dir):
            target_dirs_found += 1
            
            #Flag status json should exist
            try:
                target_is_flagged = get_flag_status(os.path.join(output_dir_path, target))
            except FileNotFoundError:
                #The process is not even started...
                continue

            if target_is_flagged:
                fully_flagged_MS_found += 1

            #Do not even check the rest
            else:
                #Look for results dir
                results_dir = os.path.join(os.path.join(output_dir_path,target), 'results')
                if os.path.exists(results_dir):
                    result_dirs_found += 1

                    try:
                        image_cube = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.endswith('pb_nonan_corrected_cube.fits')][0]
                        if target.replace('-','_') in os.path.basename(image_cube):
                            image_cubes_found += 1
                    except IndexError:
                        #No image cube is created
                        pass

                    try:
                        catalog = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.endswith('catalog.fits')][0]
                        if target.replace('-','_') in os.path.basename(catalog):
                            cataloges_found += 1
                    except IndexError:
                        #No catalog is created
                        pass

    completion_summary += "Found {0:d} target directory ({1:.2f} target process has started)".format(
                        target_dirs_found, np.divide(target_dirs_found,np.size(targets))) + os.linesep

    completion_summary += "Found {0:d} fully flagged MS based on the flag status ({1:.2f} targets)".format(
                        fully_flagged_MS_found, np.divide(fully_flagged_MS_found,np.size(targets))) + os.linesep

    completion_summary += "Found {0:d} target/results directory ({1:.2f} targets got results)".format(
                        result_dirs_found, np.divide(result_dirs_found,np.size(targets))) + os.linesep

    completion_summary += "Found {0:d} image cubes ({1:.2f} targets got correct MSF image cubes)".format(
                        image_cubes_found, np.divide(image_cubes_found,np.size(targets))) + os.linesep

    completion_summary += "Found {0:d} catalogs ({1:.2f} targets got correct MSF image cubes)".format(
                        cataloges_found, np.divide(cataloges_found,np.size(targets))) + os.linesep

    return completion_summary

def get_target_status_list(config_file:str,
                            output_dir_path:str) -> list:
    """
    """

    completed_targets = []
    flagged_targets = []
    failed_targets = []

    targets = get_targets_from_config(config_file)

    for target in targets:

        target_dir = os.path.join(output_dir_path,target)
        if os.path.exists(target_dir):
            
            #Look at the flag status
            try:
                target_is_flagged = get_flag_status(target_dir)
            except FileNotFoundError:
                #Now this indicates that the worker is failed spectacularly
                failed_targets.append(target)

            if target_is_flagged:
                flagged_targets.append(target)

            else:
                #Look for results dir
                results_dir = os.path.join(os.path.join(output_dir_path,target), 'results')
                if os.path.exists(results_dir):

                    try:
                        image_cube = [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.endswith('pb_nonan_corrected_cube.fits')][0]

                        #The replacement is needed if the field names have a '-' (old otfms pipeline ?)
                        #as caracal converts this to '_'
                        if target.replace('-','_') in os.path.basename(image_cube):
                            completed_targets.append(target)

                    except IndexError:
                        failed_targets.append(target)

        else:
            failed_targets.append(target)

    return completed_targets, flagged_targets, failed_targets

def get_target_images_full_paths(target_list:list,
                        output_dir_path:str) -> Union[list, list, list]:
    """
    The targets *should* exist on disc. This function simply collects the full paths
    though, no checks is done.
    """
    mfs_image_paths = []
    pb_corrected_image_paths = []
    pb_corrected_cube_paths = []

    for target_name in target_list:
        images_path = os.path.join(os.path.join(output_dir_path,target_name),'results/')
    
        mfs_image_paths.append([os.path.join(images_path, f) for f in os.listdir(images_path) if f.endswith('MFS-image.fits')][0])
        pb_corrected_image_paths.append([os.path.join(images_path, f) for f in os.listdir(images_path) if f.endswith('pb_corrected_image.fits')][0])
        pb_corrected_cube_paths.append([os.path.join(images_path, f) for f in os.listdir(images_path) if f.endswith('pb_nonan_corrected_cube.fits')][0])

    return mfs_image_paths, pb_corrected_image_paths, pb_corrected_cube_paths

def generate_postage_stamp_from_fits(fitspath:str,
                                    outpath:str,
                                    cut_percentile=99.5) -> int:
    """
    """

    hdul = fits.open(fitspath, memmap=True)

    wcs = WCS(hdul[0].header)

    fits_data = hdul[0].data[0,0,...]

    #Convert Jy to mJy
    fits_data *= 1e3

    plot_data = copy.deepcopy(fits_data)
    plot_data[np.isnan(plot_data)] = 0

    percentiles = np.percentile(plot_data, np.array([100 - cut_percentile, cut_percentile]))

    fig, ax = plt.subplots(figsize=(7,7),
                    subplot_kw={'projection':wcs, 'slices':('x', 'y',0,0)})

    image_plot = plt.imshow(fits_data, vmin=percentiles[1], vmax=percentiles[0],
                            cmap=_CMAP, origin='lower')
    
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="3%", axes_class=maxes.Axes, pad=0.0)
    cbar = fig.colorbar(image_plot, cax=cax, orientation='vertical')
    cax.set_ylabel('S [mJy/beam]', fontsize=18)

    ax.coords[0].set_axislabel('RA -- SIN', fontsize=14)
    ax.coords[1].set_axislabel('Dec -- SIN', fontsize=14)

    plt.savefig(outpath, bbox_inches='tight')

    plt.close()

    return 0

def generate_postage_stamps(config_file:str,
                            output_dir_path:str,
                            target_list:list, 
                            cut_percentile=99.9,
                            check_existing=True,
                            list_only=False) -> list:
    """
    The target list is a name of the targets the user is interested in.
    In practice the pre-computed completed targets should be passed.
    NOTE: the pb corrected MFS images for all targets must exist!
    """
    postage_stamp_list = []

    for target in target_list:

        results_dir = os.path.join(os.path.join(output_dir_path,target), 'results')

        pb_corrected_MFS_fits_path = \
        [os.path.join(results_dir, f) for f in os.listdir(results_dir) if f.endswith('pb_corrected_image.fits')][0]

        postage_stamp_image = os.path.dirname(pb_corrected_MFS_fits_path) + "/postage_stamp_" +\
                        os.path.basename(pb_corrected_MFS_fits_path)[:-5] + '.png' #Unix path syntax and remove .fits extension

        #Generate postage stamp .png image
        postage_stamp_list.append(postage_stamp_image)

        if not list_only:
            if check_existing:
                if os.path.exists(postage_stamp_image) and os.path.isfile(postage_stamp_image):
                    pass
                else:
                    generate_postage_stamp_from_fits(pb_corrected_MFS_fits_path,postage_stamp_image,cut_percentile)
            else:
                generate_postage_stamp_from_fits(pb_corrected_MFS_fits_path,postage_stamp_image,cut_percentile)

    return postage_stamp_list

def display_postage_stamps(postage_stamp_path_list:list,
                            display_backend='jupyter',
                            get_image_name=True) -> int:
    """
    """

    for postage_stamp_path in postage_stamp_path_list:
        if get_image_name:
            image_name = os.path.basename(postage_stamp_path)

            print('Image displayed: {0:s}'.format(image_name))

        if display_backend == 'python':
            image = cv2.imread(postage_stamp_path)
            cv2.imshow('Postage stamp image', image)
            cv2.waitKey(0) #Waits unter user presses a key (code breaks if image is closed by clicking)
            cv2.destroyAllWindows()

        elif display_backend == 'jupyter':
            display(Image(filename=postage_stamp_path))

        else:
            raise ValueError("Nor supported backend '{0:s}'!".format(display_backend))

    return 0

#TO DO: add a function that ONLY displays the created images from a file list

# === Code to generate the report

def add_report_code_cells(notebook_node:nbf.notebooknode.NotebookNode) -> nbf.notebooknode.NotebookNode:
    """
    """

    # === Completion stats
    completion_stats_header = "Completion statistics" + md_linebreak() +\
                        "----" + md_linebreak() +\
                        "Find available output and generate lists of completed and non-completed targets/workers"

    notebook_node['cells'].append(nbf.v4.new_markdown_cell(completion_stats_header))

    completion_statistics = '#Get completion statistics based on the output folders/files found on disc' +\
                            md_linebreak() +\
                            "completion_stats = get_completion_statistics(config_file_path, output_dir_path)" +\
                             md_linebreak() + "print(completion_stats)"

    notebook_node['cells'].append(nbf.v4.new_code_cell(completion_statistics))
   
    #Get the list of completed and failed runs
    target_status_list_code = "#Get the list of completed target fields" + md_linebreak() +\
                        "completed_targets, flagged_targets, failed_targets = "\
                        "get_target_status_list(config_file_path, output_dir_path)" +\
                        md_linebreak() + "print('Completed targets:' + os.linesep + '---------')" + md_linebreak() +\
                        "print(*completed_targets, sep=os.linesep)" + md_linebreak() +\
                        md_linebreak() + "print(os.linesep + 'Flagged targets:' + os.linesep + '---------')" + md_linebreak() +\
                        "print(*flagged_targets, sep=os.linesep)" + md_linebreak() +\
                        md_linebreak() + "print(os.linesep + 'Failed targets:' + os.linesep + '---------')" + md_linebreak() +\
                        "print(*failed_targets, sep=os.linesep)"

    notebook_node['cells'].append(nbf.v4.new_code_cell(target_status_list_code))

    # === Time-space plots

    #TO DO: add time-space plots

    #Plot completed vs not as a function of time (need to read input MS)

    #Plot RA-Dec of completed and non-completed targets (need to read input MS)

    # === Postage stamps

    #TO DO: add postage stamp generation to the worker script, so it is generated during runtime

    postage_stamps_header = "Postage stamp images" + md_linebreak() +\
                        "----" + md_linebreak() +\
                        "Generate and display postage stamp images for all completed targets/workers"

    notebook_node['cells'].append(nbf.v4.new_markdown_cell(postage_stamps_header))

    generate_postage_stamps_code = "#Generate the postage stamp images" + md_linebreak() +\
                                "postage_stamp_images = generate_postage_stamps("+\
                                "config_file_path, output_dir_path, completed_targets,"+\
                                " check_existing=True)"

    notebook_node['cells'].append(nbf.v4.new_code_cell(generate_postage_stamps_code))

    display_postage_stamps_code = "#Display all postage stamps generated" + md_linebreak() +\
                                "display_postage_stamps(postage_stamp_images)"

    notebook_node['cells'].append(nbf.v4.new_code_cell(display_postage_stamps_code))

    return notebook_node

def save_report_notebook(notebook_node:nbf.notebooknode.NotebookNode,
                        notebook_out_path:str,
                        notebook_name='otf_imaging_and_selfcal_report') -> int:
    """
    """

    if not notebook_name.endswith('.ipynb'):
        notebook_name += '.ipynb'

    notebook_save_path = os.path.join(notebook_out_path,notebook_name)

    nbf.validate(notebook_node)

    nbf.write(notebook_node, open(notebook_save_path, 'w'), version=4)

    return 0

# === Code to run the report creator

def report_creator(config_params:dict) -> int:
    """
    """
    if not config_params['notebook_only']:
        # === i.e. for local testing
        completion_stats = get_completion_statistics(config_params['master_cfg_path'],
                                            config_params['master_output_dir_path']) 

        print(completion_stats)

        completed_targets = get_target_status_list(config_params['master_cfg_path'],
                                            config_params['master_output_dir_path'],
                                            completed=True)

        failed_targets = get_target_status_list(config_params['master_cfg_path'],
                                            config_params['master_output_dir_path'],
                                            completed=False)

        postage_stamp_images = generate_postage_stamps(config_params['master_cfg_path'],
                                            config_params['master_output_dir_path'],
                                            completed_targets)

        display_postage_stamps(postage_stamp_images, display_backend='python')

    # === Generate report notebook

    report_notebook_node = init_report_notebook(config_params['master_cfg_path'],
                                        config_params['master_output_dir_path'])

    report_notebook_node = add_report_code_cells(report_notebook_node)

    if config_params['report_output_dir'] == None:
        save_report_notebook(report_notebook_node,
                            config_params['master_output_dir_path'])
    else:
        save_report_notebook(report_notebook_node,
                            config_params['report_output_dir'])

    return 0

# === MAIN ===
if __name__ == "__main__":
    config_params = get_master_params()

    report_creator(config_params)