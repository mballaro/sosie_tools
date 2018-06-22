import numpy as np
import glob
import os
import fnmatch
from netCDF4 import Dataset
from sys import exit, argv
from yaml import load, dump

if len(argv) != 2:
    print(' \n')
    print('USAGE   : %s <file.YAML> \n' % path.basename(argv[0]))
    print('Purpose : Merge SOSIE weight decomposed on multiprocessor architecture \n')
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
merged_nc_file = YAML['merged_nc_file']

# final grid lon/lat
lon = np.arange(vector_lon[0]-resolution_lon, vector_lon[-1]+delta_lon+2*resolution_lon, resolution_lon)
lat = np.arange(vector_lat[0]-resolution_lat, vector_lat[-1]+delta_lat+resolution_lat, resolution_lat)

lon2D_merged = np.zeros((lat.size, lon.size))
lat2D_merged = np.zeros((lat.size, lon.size))
metrics_merged = np.zeros((3, lat.size, lon.size))
alphabeta_merged = np.zeros((2, lat.size, lon.size))
iproblem_merged = np.zeros((lat.size, lon.size))


def find_nearest_index(array, value):
    idx = (np.abs(array-value)).argmin()
    return idx


list_of_file = []
for root, dirnames, filenames in os.walk(output_dir):
    for filename in fnmatch.filter(filenames, 'sosie_mapping_*.nc'):
        list_of_file.append(os.path.join(root, filename))
        # Open netCDF file
        NC = Dataset(os.path.join(root, filename), 'r')
        lon2D_local = NC.variables["lon"][:, :]
        lat2D_local = NC.variables["lat"][:, :]
        metrics_local = NC.variables["metrics"][:, :, :]
        alphabeta_local = NC.variables["alphabeta"][:, :, :]
        iproblem_local = NC.variables["iproblem"][:, :]

        lon2D_local = np.where(lon2D_local >= 180, lon2D_local-360, lon2D_local)
        
        imin_lon = find_nearest_index(lon, lon2D_local[0, 0])
        imax_lon = find_nearest_index(lon, lon2D_local[0, -1]) + 1
        imin_lat = find_nearest_index(lat, lat2D_local[0, 0])
        imax_lat = find_nearest_index(lat, lat2D_local[-1, 0]) + 1

        if imax_lat > lat.size:
            imax_lat = lat.size 
        if imax_lon > lon.size:
            imax_lon = lon.size
        # print os.path.join(root, filename)
        
        lon2D_merged[imin_lat:imax_lat, imin_lon:imax_lon] = lon2D_local[:, :]
        lat2D_merged[imin_lat:imax_lat, imin_lon:imax_lon] = lat2D_local[:, :]
        metrics_merged[:, imin_lat:imax_lat, imin_lon:imax_lon] = metrics_local[:, :, :]
        alphabeta_merged[:, imin_lat:imax_lat, imin_lon:imax_lon] = alphabeta_local[:, :, :]
        iproblem_merged[imin_lat:imax_lat, imin_lon:imax_lon] = iproblem_local[:, :]

NC = Dataset(merged_nc_file, 'w', format='NETCDF4')
y = NC.createDimension('y', lat.size)
x = NC.createDimension('x', lon.size)
n2 = NC.createDimension('n2', 2)
n3 = NC.createDimension('n3', 3)
lat_out = NC.createVariable('lat', 'f8', ('y', 'x'))
lon_out = NC.createVariable('lon', 'f8', ('y', 'x'))
metrics_out = NC.createVariable('metrics', 'i4', ('n3', 'y', 'x'))
alphabeta_out = NC.createVariable('alphabeta', 'f8', ('n2', 'y', 'x'))
iproblem_out = NC.createVariable('iproblem', 'i4', ('y', 'x'))
lat_out[:, :] = lat2D_merged
lon_out[:, :] = lon2D_merged
metrics_out[:, :, :] = metrics_merged
alphabeta_out[:, :, :] = alphabeta_merged
iproblem_out[:, :] = iproblem_merged
NC.close()
