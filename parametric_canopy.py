"""
Assignment 3: Parametric Structural Canopy

Author: Boas Olesen

Description:
This script generates a parametric structural canopy using depth maps and recursive geometry generation.
It explores different functions to control both the depth map and the fractal geometry to generate a
structural system composed of:
- A shell/gridshell
- A set of vertical supports

The script also combines different strategies for surface tessellation
"""

# Import necessary libraries
import Rhino
import Rhino.Geometry as rg
import math
import random

"""
Create a parametric surface with random varying height as canopy
    Parametric Inputs
    length: Canopy length in x direction
    Width: Canopy width i y direction
    min_height: Minimumaximum Canopy height in z direction
    max_height: Maximum Canopy height in z direction
    n_cols: number of gridpoints in x direction
    n_rows: number of gridpoints in y direction
"""
def parametric_surface(length, width, min_height, max_height, n_cols, n_rows):
    # Spacing between gridpoints
    x_spacing = length / (n_cols - 1)
    y_spacing = width / (n_rows - 1)

    # Generate x and y values based on resolution (amount of rows/columns)
    x_vals = [i * x_spacing for i in range(n_cols)]
    y_vals = [i * y_spacing for i in range(n_rows)]

    n_points = len(x_vals) * len(y_vals) # total number of gridpoints
    z_vals = [max_height - (max_height - min_height) * random.random() for _ in range(n_points)] # randomizes height between min- & max_height

    # Generate flat list of 3D points
    pts_grid = [rg.Point3d(x, y, z_vals[i]) for i, (x, y) in enumerate((x, y) for y in y_vals for x in x_vals)]
    points = pts_grid

    # Surface degrees
    u_degree = min(3, n_rows - 1)
    v_degree = min(3, n_cols - 1)

    # Create the surface
    surface = rg.NurbsSurface.CreateFromPoints(pts_grid, n_rows, n_cols, u_degree, v_degree)
    return surface

"""
    Tessellates the input surface using the specified strategy.

    Parameters:
    - surface: The generated surface to tessellate
    - U: subdivision in the U direction
    - V: Subdivision in the V direction
    - strategy: The tessellation method is diagrid

    Returns:
    - tessellated_mesh: A mesh representing the tessellated surface
"""
import rhinoscriptsyntax as rs
import ghpythonlib.treehelpers as th

srf_u_domain = rs.SurfaceDomain(srf, 0)
srf_v_domain = rs.SurfaceDomain(srf, 1)

srf_pts = []
for i in range(U + 1):
    row = []
    for j in range(V + 1):
        srf_u = i / U * srf_u_domain[1]
        srf_v = j / V * srf_v_domain[1]
        row.append(rs.EvaluateSurface(srf, srf_u, srf_v))
    srf_pts.append(row)

diagrid = []

# Loop to create the Diagrid pattern
for i in range(len(srf_pts) - 2):       # Avoid accessing out-of-bound indices
    if i == 0 or i % 2 == 0:            # Create diagonal pattern only at certain rows
        for j in range(1, len(srf_pts[0]) - 1, 2):  # Avoid out-of-bound access in j-direction
            if i + 2 < len(srf_pts) and j + 1 < len(srf_pts[0]):
                cell_pts = [
                    srf_pts[i][j], 
                    srf_pts[i+1][j+1], 
                    srf_pts[i+2][j], 
                    srf_pts[i+1][j-1], 
                    srf_pts[i][j]
                ]
                diagrid.append(rs.AddPolyline(cell_pts))

srf_pts = th.list_to_tree(srf_pts)

def generate_recursive_support(start_point, start_angle, angle_change, length, length_scale, height_step, surface, max_heigth):
        
     """
    Generates recursive geometry (e.g., fractal patterns) for vertical supports.

    Parameters:
    - start_point: The starting point for recursion (rg.Point3d)
    - params: A dictionary containing parameters for recursion control
    - depth: The current recursion depth
    - start_point: Starting point for the support
    - start_angle: Initial angle for the support
    - angle_change: Incremnetal change to the angle in each recursion
    - length: length of each recursion
    - length_scale: scaling factor for the length in each recursion
    - height_step: incremental change for height in each recursion
    - surface: input surface that is gonna act as canopy
    - max_height: maximum height for the supports

    Returns:
    - points: a list if points to be used for curve generation
    - curves: A list of interpolated curves representing the supports
    """
    points = [start_point]  # Store the initial point
    current_angle = start_angle  # Initialize the angle
    
    while length > 0.001:  # Stop if length becomes less than 0.001
        # Calculate x, y, z offsets from length and angle
        x_change = length * math.sin(current_angle)
        y_change = length * math.cos(current_angle)
        z_change = height_step
            
        # Create point
        new_point = rg.Point3d.Add(points[-1], rg.Vector3d(x_change, y_change, z_change))

        # Check if supports missed canopy surface
        if new_point.Z > max_height + 0.01:
            break

        points.append(new_point)
            
        polyline = rg.Polyline()
        for pt in points:
            polyline.Add(pt)

        curve = polyline.ToNurbsCurve()

        # Check for intersection with the canopy surface
        intersections = rg.Intersect.Intersection.CurveSurface(curve, surface, 0.001, 0.001)
        if intersections:
            for event in intersections:
                if event.IsPoint:
                    intersect_point = event.PointA  # Get the intersection point
                    points.append(intersect_point)
                    return points
            
        # Update angle and length
        current_angle += math.radians(angle_change)
        length *= length_scale  # Scale the length for the next step
    
    return points

    # Generate points recursively, stopping at canopy intersection
    points = generate_recursive_support(start_point, start_angle, angle_change, length, length_scale, height_step, surface, max_height)

    # Remove point that goes through the canopy surface
    points.pop(-2)

    # Ensure points are all valid Point3d objects before output
    validated_points = [pt for pt in points if isinstance(pt, rg.Point3d)]

    # Interpolate curve through the points
    curve = rg.NurbsCurve.CreateInterpolatedCurve(validated_points, 3)