while len(df) > 0:
    # Find the current layer by selecting points in a small Z-tolerance range
    current_z = df['z'].max()  # Find the highest Z in the remaining points
    df_layer = df[(df['z'] >= current_z - tolerance) & (df['z'] <= current_z + tolerance)]
    
    # Convert points in the layer to a NumPy array
    l = df_layer[['x', 'y', 'z']].values
    n = len(l)  # Number of points in the current layer
    initial_point = l[0]  # Set the initial point for the layer
    pp = initial_point  # Start from the initial point of the layer

    # Tool path generation logic for the current layer
    visited = [False] * n  # Reset visited flags for the new layer
    visited[0] = True  # Mark initial point as visited

    # Inner loop for visiting points in the current layer
    while n > 0:
        # Same logic as before to find the next closest point
        ld = [np.sum(np.abs(pp - l[j])) if not visited[j] else float('inf') for j in range(len(l))]
        
        # Select the closest unvisited point
        k = np.argmin(ld)
        lk = l[k]
        ltp = np.vstack([ltp, lk])  # Add lk to toolpath
        visited[k] = True  # Mark this point as visited
        pp = lk  # Update current position
        n -= 1  # Decrement the number of unvisited points
    
    # Close the path by returning to the initial point
    ltp = np.vstack([ltp, initial_point])  # Complete the loop for this layer

    # Remove the points in the current layer from the DataFrame and move to the next layer
    df = df[df['z'] < current_z - tolerance]