# Importing libraries that will be used for the rest of the code
import pyvista as pv
import csv
import pandas as pd
import numpy as np
from scipy.spatial import ConvexHull
from scipy.spatial.distance import pdist, squareform
from scipy.optimize import linear_sum_assignment

mesh = pv.read('freeform_test_17.stl') # Load the STL to form the point cloud
mesh = mesh.subdivide(2)  # Increase this number (e.g., 3 or 4) for more points
points = mesh.points # Turing the point cloud to the mesh into points for processing

pd.options.mode.copy_on_write = True # Only copies the relevent points when needed for the entire program

with open('dots.csv', 'w') as f: #Saving the mesh points 
    csv.writer(f).writerows(points) # Sorts the points by Z coordinates 
df = pd.read_csv('dots.csv', header=None, names=['x', 'y', 'z']).dropna() # Puts the sorted points into dots.csv

df = df[df['z'] > df['z'].min() + 0.1] # This is removes the bottom layer of the shape to prevent the machine reprocessing points

layer_spacing = 0.2  # Set the distance between layers (in your desired units)

# Module for ensuring line spacing
def enforce_layer_spacing(df, layer_spacing):
    z_min = df['z'].min() 
    layers = np.arange(z_min, df['z'].max() + layer_spacing, layer_spacing) # Compute possible layer positions based on layer spacing
    df['z'] = layers[np.argmin(np.abs(df['z'].values[:, None] - layers), axis=1)] # Assign each point to the closest layer
    return df
df = enforce_layer_spacing(df, layer_spacing)

# Module for calculating the circular shapes
def is_circular_shape(points, tolerance=0.1): # The tolerance must be adjusted according to the dimensions of the model, the bigger the number the less amount of points are selected
    center = points.mean(axis=0)
    distances = np.linalg.norm(points - center, axis=1)
    return np.abs(distances - distances.mean()).max() < tolerance

# Module for calculating TSP (Traveling Sales Person)
def solve_tsp(points):
    distance_matrix = squareform(pdist(points))
    _, col_ind = linear_sum_assignment(distance_matrix)
    return col_ind


# Module for sorting the points in a clockwise direction
def sort_clockwise(points):
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    return points[np.argsort(angles)]


# Module for processing circular layers
def process_circular_layer(layer_points):
    return sort_clockwise(layer_points)


# Module for processing non-circular layers
def process_non_circular_layer(layer_points):
    tsp_order = solve_tsp(layer_points)
    return sort_clockwise(layer_points[tsp_order])

# Initialize toolpath
ll = []
prev_exit_point = None

while len(df) > 0:
    # This identifys the current layer and identifies the greatest Z coordinate or highest layer.
    current_layer_z = df['z'].max()
    current_layer = df[df['z'] == current_layer_z]

    # This layer skips any layers with fewer than 3 points because ConvexHull is unable to process layers with less than 3 points. This stops the program from breaking.
    if len(current_layer) < 3:
        df = df[df['z'] < current_layer_z]
        continue
    
    # Filter points to retain only boundary points using ConvexHull. This ensures that only the outermost points are processed and saved to the tool path.
    layer_points = current_layer[['x', 'y']].values
    hull = ConvexHull(layer_points)
    hull_coords = layer_points[hull.vertices]

    # Determine if the shape is circular or non-circular
    if is_circular_shape(hull_coords):
        sorted_points = process_circular_layer(hull_coords)
    else:
        sorted_points = process_non_circular_layer(hull_coords)

    # Closest point from previous layer to start
    if prev_exit_point is not None:
        dists = np.linalg.norm(sorted_points - prev_exit_point[:2], axis=1)
        start_idx = np.argmin(dists)
        sorted_points = np.roll(sorted_points, -start_idx, axis=0)
    
    # Add Z-coordinate to sorted points
    sorted_layer = np.hstack([sorted_points, np.full((sorted_points.shape[0], 1), current_layer_z)])
    
    # This part of the code makes the tool path return to the first point of the layer and then adds this movement to the end of the tool path.
    layer_path = list(sorted_layer)
    layer_path.append(layer_path[0])  # Return to the first point
    ll.extend(layer_path)

    prev_exit_point = layer_path[0]  # For continuous connection
    
    # Remove processed points from the main DataFrame then from here it repeats untill all of the layers are processed
    df = df[df['z'] < current_layer_z]

    #prints the layer spacings so that we can ensure that the layers are the same distance apart from each other
    unique_z = np.sort(df['z'].unique())
    print("Layer spacings:", np.diff(unique_z))

# Save toolpath to a CSV
ll = np.round(ll, 3)
pd.DataFrame(ll, columns=['x', 'y', 'z']).to_csv('toolpath.csv', index=False)

# Convert to G-code and save as a text file. (Can be changed to CSV or any file type.)
df_ltp = pd.read_csv('toolpath.csv')
df_gchord = pd.DataFrame({
    'G': 'G01',
    'x': 'X' + df_ltp['x'].astype(str),
    'y': 'Y' + df_ltp['y'].astype(str),
    'z': 'Z' + df_ltp['z'].astype(str),
    'EOB': ';'
})

# Define the starting and ending G-code lines.
# The coordinates for the following sections (gcode_header and gcode_footer) can be changed depending on the size of the work area for the CNC machine
gcode_header = [
    "G90 ; (Absolute positioning)",
    "G21 ; (Set units to millimeters)",
    "G92 X0.0 Y0.0 Z0 ; (Set workplace origin)",
    "F1000 ; (Set feedrate)",
    "G01 X0.0 Y0.0 Z20 ; (Move to safe height)"
]
# Note that for the line "G01 X0.0 Y0.0 Z20" and "G01 Z20" the Z coordinate MUST be changed depending on the work areas height.
# So that the tool goes down instead of going up from the work area origin

gcode_footer = [
    "G01 Z20 ; (Retract tool)",
    "M30 ; (End of program)"
]

# Add the header, G-code, and footer to the file
with open('Gchord.txt', 'w') as f:
    # Write the header
    for line in gcode_header:
        f.write(line + '\n')
    
    # Write the G-code toolpath
    df_gchord.to_csv(f, index=False, sep=" ", header=False, mode='a')
    
    # Write the footer
    for line in gcode_footer:
        f.write(line + '\n')