from netCDF4 import Dataset
import numpy as np
from os import system, path
from sys import exit, argv
from yaml import load, dump

if len(argv) != 2:
    print(' \n')
    print('USAGE   : %s <file.YAML> \n' % path.basename(argv[0]))
    print('Purpose : Compute SOSIE weight on multiprocessor architecture \n')
    exit(0)

# Load analysis information from YAML file
YAML = load(open(str(argv[1])))
output_dir = YAML['output_dir']
template_sosie = YAML['template_sosie']
sosie_exe_path = YAML['sosie_exe_path']
delta_lon = YAML['delta_lon']
delta_lat = YAML['delta_lat']
vector_lon = np.arange(YAML['llcrnrlon'], YAML['urcrnrlon'], delta_lon)
vector_lat = np.arange(YAML['llcrnrlat'], YAML['urcrnrlat'], delta_lat)
resolution_lon = YAML['resolution_lon']
resolution_lat = YAML['resolution_lat']

######################################################################################
# USER PARAMETERS
######################################################################################
# output_dir = "/home/mballarotta/sosie_tools/OUTPUTS"
# template_sosie = "/home/mballarotta/sosie_tools/template.namelist"
# sosie_exe_path = "/home/mballarotta/Public/git/sosie/bin/sosie.x"
#
# # Domain decomposition
# delta_lon = 1.
# delta_lat = 1.
# vector_lon = np.arange(-80., 8., delta_lon)
# vector_lat = np.arange(27., 67., delta_lat)
# # Output grid resolution
# resolution_lon = 1./60.
# resolution_lat = 1./60.
# NOTE: USER must adapt qsub bash job submission below
######################################################################################


# final grid lon/lat
lon = np.arange(vector_lon[0]-resolution_lon, vector_lon[-1]+delta_lon+2*resolution_lon, resolution_lon)
lat = np.arange(vector_lat[0]-resolution_lat, vector_lat[-1]+delta_lat+resolution_lat, resolution_lat)

cf_out = Dataset("natl60_lonlat_regulargrid_merged.nc", 'w', format='NETCDF4')
y = cf_out.createDimension('y', lat.size)
x = cf_out.createDimension('x', lon.size)
lat_out = cf_out.createVariable('lat', 'f8', 'y')
lon_out = cf_out.createVariable('lon', 'f8', 'x')
lat_out[:] = lat
lon_out[:] = lon
cf_out.close()

system("mkdir -p %s" % output_dir)

for lon_min in vector_lon:
    lon_max = lon_min + delta_lon
    for lat_min in vector_lat:
        lat_max = lat_min + delta_lat
        folder = "%s/domain_%s-%s_%s-%s" % (output_dir, str(lon_min), str(lon_max), str(lat_min), str(lat_max))
        system("mkdir -p %s" % folder)
        
        lon = np.arange(lon_min-resolution_lat, lon_max+resolution_lon, resolution_lon)
        lat = np.arange(lat_min-resolution_lat, lat_max+resolution_lat, resolution_lat)

        cf_out = Dataset("%s/natl60_lonlat_regulargrid_local.nc" % folder, 'w', format='NETCDF4')
        y = cf_out.createDimension('y', lat.size)
        x = cf_out.createDimension('x', lon.size)
        lat_out = cf_out.createVariable('lat', 'f8', 'y')
        lon_out = cf_out.createVariable('lon', 'f8', 'x')
        lat_out[:] = lat
        lon_out[:] = lon
        cf_out.close()

        # write bash file to submit
        bash_file = open("%s/submit.sh" % folder, 'w')
        bash_file.write('#!/bin/bash \n')
        # Go to directory
        bash_file.write('cd ' + folder + ' \n')
        # Copy sosie.template
        bash_file.write('cp ' + template_sosie + ' namelist \n')
        # Execute sosie
        bash_file.write('%s \n' % sosie_exe_path)
        bash_file.close()

        # QSUB Submit bash file (NEED TO BE ADAPTED BY USER)
        system("chmod +x %s/submit.sh" % folder)
        cmd = "BatchFerme --name=SOSIE --queue=short --no-confirm --notify=n --memory=8000m --cmd=%s/submit.sh" % folder
        system(cmd)
