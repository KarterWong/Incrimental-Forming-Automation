import numpy as np

# Initialize the direction vector with None
previous_direction = None
ltp = []  # Initialize layer tool path as an empty list

while n > 0:
    ld = []  # List of (distance, angle, index) tuples
    
    for j in range(len(l)):
        if not visited[j]:  # Only consider unvisited points
            # Calculate the vector to the point
            next_vector = l[j] - pp
            distance = np.linalg.norm(next_vector)  # Euclidean distance

            # Calculate the angle with the previous direction vector
            if previous_direction is not None:
                angle = np.arccos(
                    np.dot(previous_direction, next_vector) /
                    (np.linalg.norm(previous_direction) * np.linalg.norm(next_vector))
                )
            else:
                angle = 0  # No previous direction, treat as zero angle

            # Store distance, angle, and index
            ld.append((distance, angle, j))

    if not ld:
        ltp.append(initial_point)  # Return to initial point to complete the layer
        break

    # Filter the list of points by a maximum angle threshold, e.g., within 45 degrees
    angle_threshold = np.pi / 4  # 45 degrees in radians
    ld_filtered = [(d, a, idx) for d, a, idx in ld if a <= angle_threshold]

    # If there are no points within the angle threshold, revert to closest point
    if ld_filtered:
        min_distance, min_angle, k = min(ld_filtered, key=lambda x: x[0])  # Choose closest within angle threshold
    else:
        min_distance, _, k = min(ld, key=lambda x: x[0])  # Choose closest point if no points within angle threshold

    # Update the path and tool state
    lk = l[k]  # Coordinates of the next point
    ltp.append(lk)  # Add lk to the layer tool path
    visited[k] = True  # Mark the point as visited
    previous_direction = lk - pp  # Update the direction vector
    pp = lk  # Set the next point as the current position
    n -= 1  # Decrement the count of unvisited points
