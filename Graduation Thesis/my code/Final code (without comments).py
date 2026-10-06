import pyvista as pv
import csv
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import linear_sum_assignment

mesh = pv.read('freeform_test_17.stl')
mesh = mesh.subdivide(2)
points = mesh.points

pd.options.mode.copy_on_write = True

with open('dots.csv', 'w') as f:
    csv.writer(f).writerows(points)
df = pd.read_csv('dots.csv', header=None, names=['x', 'y', 'z']).dropna()

df = df[df['z'] > df['z'].min() + 0.1]

layer_spacing = 0.2 

def enforce_layer_spacing(df, layer_spacing):
    z_min = df['z'].min()
    layers = np.arange(z_min, df['z'].max() + layer_spacing, layer_spacing) 
    df['z'] = layers[np.argmin(np.abs(df['z'].values[:, None] - layers), axis=1)]
    return df

df = enforce_layer_spacing(df, layer_spacing)

def is_circular_shape(points, tolerance=0.1):
    center = points.mean(axis=0)
    distances = np.linalg.norm(points - center, axis=1)
    return np.abs(distances - distances.mean()).max() < tolerance

def solve_tsp(points):
    distance_matrix = squareform(pdist(points))
    _, col_ind = linear_sum_assignment(distance_matrix)
    return col_ind

def sort_clockwise(points):
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    return points[np.argsort(angles)]

def process_circular_layer(layer_points):
    return sort_clockwise(layer_points)

def process_non_circular_layer(layer_points):
    tsp_order = solve_tsp(layer_points)
    return sort_clockwise(layer_points[tsp_order])

ll = []
prev_exit_point = None

while len(df) > 0:
    current_layer_z = df['z'].max()
    current_layer = df[df['z'] == current_layer_z]

    if len(current_layer) < 3:
        df = df[df['z'] < current_layer_z]
        continue
    
    layer_points = current_layer[['x', 'y']].values
    hull = ConvexHull(layer_points)
    hull_coords = layer_points[hull.vertices]

    if is_circular_shape(hull_coords):
        sorted_points = process_circular_layer(hull_coords)
    else:
        sorted_points = process_non_circular_layer(hull_coords)

    if prev_exit_point is not None:
        dists = np.linalg.norm(sorted_points - prev_exit_point[:2], axis=1)
        start_idx = np.argmin(dists)
        sorted_points = np.roll(sorted_points, -start_idx, axis=0)
    
    sorted_layer = np.hstack([sorted_points, np.full((sorted_points.shape[0], 1), current_layer_z)])
    
    layer_path = list(sorted_layer)
    layer_path.append(layer_path[0]) 
    ll.extend(layer_path)

    prev_exit_point = layer_path[0]
  
    df = df[df['z'] < current_layer_z]

    unique_z = np.sort(df['z'].unique())
    print("Layer spacings:", np.diff(unique_z))

ll = np.round(ll, 3)
pd.DataFrame(ll, columns=['x', 'y', 'z']).to_csv('toolpath.csv', index=False)

df_ltp = pd.read_csv('toolpath.csv')
df_gchord = pd.DataFrame({
    'G': 'G01',
    'x': 'X' + df_ltp['x'].astype(str),
    'y': 'Y' + df_ltp['y'].astype(str),
    'z': 'Z' + df_ltp['z'].astype(str),
    'EOB': ';'
})

gcode_header = [
    "G90 ; (Absolute positioning)",
    "G21 ; (Set units to millimeters)",
    "G92 X0.0 Y0.0 Z0 ; (Set workplace origin)",
    "F1000 ; (Set feedrate)",
    "G01 X0.0 Y0.0 Z20 ; (Move to safe height)"
]

gcode_footer = [
    "G01 Z20 ; (Retract tool)",
    "M30 ; (End of program)"
]

with open('Gchord.txt', 'w') as f:
    for line in gcode_header:
        f.write(line + '\n')
    
    df_gchord.to_csv(f, index=False, sep=" ", header=False, mode='a')
    
    for line in gcode_footer:
        f.write(line + '\n')