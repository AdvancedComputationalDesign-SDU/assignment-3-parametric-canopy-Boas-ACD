"""
Assignment 3: Parametric Structural Canopy

Author: Boas Olesen

Description:
This script generates a parametric structural canopy using depth maps and recursive geometry generation.
It explores different functions to control both the depth map and the fractal geometry to generate a
structural system composed of:
- A shell/gridshell
- A set of vertical supports

The script also combines different strategies for surface tessellation to achieve a non-uniform tessellation
of the input surface.

Note: This script is intended to be used within Grasshopper's Python scripting component.
"""

# Import necessary libraries
import Rhino
import Rhino.Geometry as rg
import math
import random

# Define input parameters (These should be connected to Grasshopper inputs)
# base_surface: The input surface for the canopy (Type: Surface)
# depth_map_control: A numerical value controlling the depth variation (Type: Number)
# recursion_params: A dictionary containing parameters for recursive geometry (Type: Dict)
# tessellation_strategy: The tessellation method ('quad', 'triangular', 'voronoi') (Type: String)
# support_points: Points where the vertical supports will be placed (Type: List of Points)

# Example default parameters (remove when using in Grasshopper)
# base_surface = rg.PlaneSurface(rg.Plane.WorldXY, rg.Interval(-10, 10), rg.Interval(-10, 10))
# depth_map_control = 5.0
# recursion_params = {
#     'max_depth': 3,
#     'angle': 30,
#     'length': 5,
#     'length_reduction': 0.7,
#     'branches': 2,
#     'angle_variation': 15
# }
# tessellation_strategy = 'quad'
# support_points = [rg.Point3d(0, 0, 0)]

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

def tessellate_surface(surface, strategy='quad'):
    """
    Tessellates the input surface using the specified strategy.

    Parameters:
    - surface: The surface to tessellate (rg.Surface)
    - strategy: The tessellation method ('quad', 'triangular', 'voronoi')

    Returns:
    - tessellated_mesh: A mesh representing the tessellated surface
    """
    # TODO: Implement tessellation logic based on the chosen strategy
    # Potential avenues:
    # - For 'quad', create a grid of points and connect them
    # - For 'triangular', subdivide quads into triangles
    # - For 'voronoi', generate seed points and create Voronoi cells
    pass

def generate_recursive_supports(start_point, params, depth=0):
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

    def generate_recursive_support(start_point, start_angle, angle_change, length, length_scale, height_step, surface, max_heigth):
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

"""
# Main execution (This code would be inside the GhPython component)
# Inputs from Grasshopper should be connected to the respective variables
# base_surface, depth_map_control, recursion_params, tessellation_strategy, support_points

"""

if base_surface and depth_map_control and recursion_params and tessellation_strategy and support_points:
    # Generate modified surface with depth map
    # TODO: Call generate_depth_map and assign the result to modified_surface
    # modified_surface = generate_depth_map(base_surface, depth_map_control)
    
    # Tessellate the modified surface
    # TODO: Call tessellate_surface and assign the result to canopy_mesh
    # canopy_mesh = tessellate_surface(modified_surface, tessellation_strategy)
    
    # Generate vertical supports
    supports = []
    for pt in support_points:
        # TODO: Call generate_recursive_supports and extend the supports list
        # curves = generate_recursive_supports(pt, recursion_params)
        # supports.extend(curves)
        pass
    
    # Assign outputs to Grasshopper components
    # Output variables (e.g., canopy_mesh, supports) should be connected to the component outputs

else:
    # Handle cases where inputs are not provided
    pass
