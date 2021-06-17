import os, glob
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import nibabel as nb
import nibabel.freesurfer.mghformat as mgh
from nibabel.freesurfer.io import read_geometry
from nilearn.plotting.surf_plotting import load_surf_data
from brainstat.stats.terms import FixedEffect
from brainstat.stats.SLM import SLM
import myvis
import zipfile

datadir = '../data'

zipped_data = os.path.join(datadir, 'thickness.zip')
with zipfile.ZipFile(zipped_data, 'r') as zip_ref:
    zip_ref.extractall(datadir)

dfname = os.path.join(datadir, 'thickness.csv')
df = pd.read_csv(dfname)
idx = np.array(df["ID2"])
age = np.array(df["AGE"])

# 1. load thickness data 
j = 0
for Sidx in idx:
    
    # load mgh files for left hem 
    for file_L in glob.glob('../data/thickness/%s*_lh2fsaverage5_20.mgh' 
                            % (Sidx)):
        
        S_Lmgh = mgh.load(file_L).get_fdata()
        S_Larr = np.array(S_Lmgh)[:,:,0]
        
    # load mgh files for right hem        
    for file_R in glob.glob('../data/thickness/%s*_rh2fsaverage5_20.mgh' 
                            % (Sidx)):
        
        S_Rmgh = mgh.load(file_R).get_fdata()
        S_Rarr = np.array(S_Rmgh)[:,:,0]

    # concatenate left & right thickness for each subject    
    Sidx_thickness = np.concatenate((S_Larr, S_Rarr)).T

    if j == 0:
        thickness = Sidx_thickness
    else:
        thickness = np.concatenate((thickness, Sidx_thickness), axis=0)
    j += 1        

Mean_thickness = thickness.mean(axis=0)
print("all thicknes data loaded shape: ", thickness.shape)
print("Mean thickness shape: ", Mean_thickness.shape)

fig01 = plt.imshow(thickness, extent=[0,20484,0,259], aspect='auto')

# 2. read fsaverage5 surfaces & sulc & mask
Fs_Mesh_L = read_geometry(os.path.join(datadir, 'fsaverage5/lh.pial'))
Fs_Mesh_R = read_geometry(os.path.join(datadir, 'fsaverage5/rh.pial'))

Fs_Bg_Map_L  = load_surf_data(os.path.join(datadir, 'fsaverage5/lh.sulc'))
Fs_Bg_Map_R = load_surf_data(os.path.join(datadir, 'fsaverage5/rh.sulc'))

Mask_Left  = nb.freesurfer.io.read_label((os.path.join(
        datadir,'fsaverage5/lh.cortex.label')))
Mask_Right = nb.freesurfer.io.read_label((os.path.join(
        datadir,'fsaverage5/rh.cortex.label')))

surf_mesh = {}
surf_mesh['coords'] = np.concatenate((Fs_Mesh_L[0], Fs_Mesh_R[0]))
surf_mesh['tri']    = np.concatenate((Fs_Mesh_L[1], Fs_Mesh_R[1]))
bg_map = np.concatenate((Fs_Bg_Map_L, Fs_Bg_Map_R))
medial_wall = np.concatenate((Mask_Left,  10242 + Mask_Right))

# 3. plot mean thickness along the cortex
fig02 = myvis.plot_surfstat(surf_mesh, bg_map, Mean_thickness, 
                            mask = medial_wall,
                            cmap = 'viridis', vmin = 1.5, vmax = 4)

# 4. build the stats model
term_intercept = FixedEffect(1, names="intercept")
term_age = FixedEffect(age, "age")
model = term_intercept + term_age 

slm = SLM(model, -age, surf=surf_mesh)
slm.fit(thickness)
tvals = slm.t.flatten()
pvals = slm.fdr()

print("t-values: ", tvals)  # These are the t-values of the model.
print("p-values: ", pvals)  # These are the p-values of the model.

fig03 = myvis.plot_surfstat(surf_mesh, bg_map, tvals,
                            mask = medial_wall, cmap = 'gnuplot',
                            vmin = tvals.min(), vmax = tvals.max())

fig04 = myvis.plot_surfstat(surf_mesh, bg_map, pvals,
                            mask = medial_wall, cmap = 'YlOrRd',
                            vmin = 0, vmax = 0.05)
plt.show()
