# Initialize tool position and tracking
pp = [0, 0, 400]  # Initial tool position
initial_point = pp  # Keep track of the initial point
visited = [False] * len(l)  # List of visited flags for each point
visited_count = 0  # Number of visited points

# Toolpath generation logic
if n > 1:
    visited[0] = True  # Mark the initial point as visited initially
    visited_count = 0  # Reset visited count

    while n > 0:
        j = 0
        ld = []  # List to store distances to points from the current tool position
        
        # Iterate over all points to calculate distances
        while j < n:
            # Skip the initial point until we've visited at least a few points
            if np.array_equal(l[j], initial_point) and visited_count > 0:
                j += 1
                continue  # Skip the initial point

            # Calculate distance from current position (pp) to the point (l[j])
            distance = np.linalg.norm(pp - l[j])
            ld.append(distance)  # Append distance to the list
            j += 1

        # Find the nearest unvisited point
        k = ld.index(min(ld))  # Get index of the closest point
        lk = l[k]  # Get the coordinates of the closest point
        ltp = np.vstack([ltp, lk])  # Add to toolpath

        # Mark the point as visited
        visited[k] = True
        visited_count += 1  # Increment visited points counter
        
        # After visiting a few points, allow revisiting the initial point
        if visited_count == n - 1:  # All points visited except the initial point
            visited[0] = False  # Unmark the initial point as visited to allow revisiting

        # Remove visited point from the list for the next iteration
        ld.pop(k)
        l = np.delete(l, k, 0)  # Remove the visited point from the list
        n -= 1  # Decrease the number of unvisited points

        pp = lk  # Update current position to the new closest point

    # After completing the layer, check if initial point is visited and revisit it
    if not visited[0]:  # If initial point was not visited during the iteration
        ltp = np.vstack([ltp, initial_point])  # Add initial point to complete the loop

    # Proceed to the next layer after the tool reaches the initial point
    ll = np.vstack([ll, ltp])

    # Remove processed points from the DataFrame based on tolerance
    df = df[df['z'] < s - tolerance]
