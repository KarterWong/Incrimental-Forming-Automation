# Initial setup
pp = [0, 0, 400]  # Initial tool position
initial_point = pp  # Keep track of the initial point to avoid revisiting it

# Toolpath logic
if n > 1:
    visited = []  # To track visited points
    while n > 0:
        j = 0
        ld = []  # List of distances to points from current position
        
        # Iterate over all points to calculate distances
        while j < n:
            # Skip the initial point if already visited
            if np.array_equal(l[j], initial_point) and c > 0:
                j += 1
                continue  # Skip this iteration if it's the initial point

            distance = np.linalg.norm(pp - l[j])  # Calculate distance to current point
            ld.append(distance)  # Append distance to list
            visited.append(False)  # Mark as unvisited initially
            j += 1

        # Find the nearest unvisited point
        k = ld.index(min(ld))  # Get index of the closest point
        lk = l[k]  # Get the coordinates of the closest point
        ltp = np.vstack([ltp, lk])  # Add to toolpath

        # Mark the point as visited
        visited[k] = True
        
        # Remove visited point from the list for next iteration
        ld.pop(k)
        l = np.delete(l, k, 0)  # Remove the visited point from the list
        n -= 1  # Decrease the number of unvisited points
        
        pp = lk  # Update current position to the new closest point
        c += 1  # Increment iteration count

    # After completing the layer, remove the initial point from toolpath if it's still there
    ltp = np.delete(ltp, 0, 0)  # Remove any unwanted initial point placeholder
    ll = np.vstack([ll, ltp])  # Append toolpath to the complete path

    # Remove processed points from the DataFrame based on tolerance
    df = df[df['z'] < s - tolerance]
