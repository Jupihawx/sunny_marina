from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from pyvista.trame.ui import plotter_ui
from trame.widgets import html, vuetify

import pyvista as pv

import numpy as np
import os
import math


# Always set PyVista to plot off screen with Trame
pv.OFF_SCREEN = True

pv.global_theme.cmap = 'coolwarm' # Color map of the visualisation, change to liking

cropping_box = pv.Cube(center = (150, -100, 0), x_length=2000, y_length=1300, z_length=2000) # Defining box of interest for one street
cropping_box.rotate_z(50, inplace=True, point = (0, 0, 0))

server = get_server()
server.client_type = "vue2"                    # Choose between vue2 and vue3
state, ctrl = server.state, server.controller

state.trame__title = "Marina Temperature"

# Load the mesh file
wall = pv.read('./Model/buildings.vtu')
wall['Temperature'] = np.zeros((wall.n_points))
#buildings = pv.read('./Geometry/buildings.stl') # Building to display

# Textured ground
circle = pv.Circle(1200)
texture= pv.read_texture('./Geometry/satellite_image_2-modified.png')
circle.texture_map_to_plane(inplace=True)
circle.rotate_z(93,inplace = True)
circle.translate((40,210,0.1), inplace=True)



## Generate the plotter and adds the static elements
plotter = pv.Plotter()
#plotter.add_mesh(buildings)

## Information on the simulation used for the SVD
angles_simulated=[0,  0.3307,  0.6614,  0.9921,   1.3228,  1.6535,   1.9842,   2.3149,   2.6456,   2.9762,  3.3069,    3.6376,    3.9683,   4.2990,    4.6297,  4.9604,    5.2911,    5.6218,    5.9525, 2*np.pi ]
nb_angles_simulated=len(angles_simulated)
velocities=[5,10,15]
nb_velocities_simulated=len(velocities)
nb_bases_total=nb_angles_simulated*nb_velocities_simulated


## Load the pre-computed SVD model of T° over the wall
bases_wall_T = np.load('./Model/total/bases_T_buildings_total_reduced60.npy', allow_pickle=True)
mean_wall_T = np.load('./Model/total/T_buildings_total_mean.npy', allow_pickle=True)
interpolation_functions_wall_am_T = np.load('./Model/total/interpolation_functions_sun_-1_TOTAL_T_buildings.npy', allow_pickle=True)
interpolation_functions_wall_noon_T = np.load('./Model/total/interpolation_functions_sun_0_TOTAL_T_buildings.npy', allow_pickle=True)
interpolation_functions_wall_pm_T = np.load('./Model/total/interpolation_functions_sun_1_TOTAL_T_buildings.npy', allow_pickle=True)


## List of initial variables
global angle
angle=0
global velocity
velocity=10
global nb_bases
nb_bases=30
global current_interpolation_functions_wall
current_interpolation_functions_wall = interpolation_functions_wall_am_T

origin = (0, 0, 100)  # Origin of the clipping plane 
normal = (0, 0, 1)  # Normal vector of the clipping plane

actor_wall = plotter.add_mesh(wall,  cmap='coolwarm', scalars = 'Temperature', clim = [300,320])

@state.change("Angle")
def update_angle(Angle, **kwargs):
    global nb_bases
    global velocity
    global angle
    global current_interpolation_functions_wall
    global wall
    global actor_wall
    angle=math.radians(Angle)

    interpolated_coefficients_wall = []
    for base in range(nb_bases):
        interpolated_coefficients_wall.append(current_interpolation_functions_wall[base]((velocity,angle)))

    ## Reconstruct the field

    Result_wall = np.reshape(mean_wall_T,-1) + bases_wall_T[:, :nb_bases] @ interpolated_coefficients_wall
    wall['Temperature'] = Result_wall

    wall.active_scalars_name  = 'Temperature'
    actor_wall.mapper.array_name = 'Temperature'
    actor_wall.mapper.scalar_range = [300, 320]

    try:
        ctrl.view_update()
        plotter.scalar_bar.SetTitle('Temperature')
    except:
        pass

@state.change("Velocity")
def update_velocity(Velocity, **kwargs):
    global nb_bases
    global velocity
    global angle
    global current_interpolation_functions_wall
    global wall
    global actor_wall

    velocity=Velocity

    interpolated_coefficients_wall = []
    for base in range(nb_bases):
        interpolated_coefficients_wall.append(current_interpolation_functions_wall[base]((velocity,angle)))

    ## Reconstruct the field

    Result_wall = np.reshape(mean_wall_T,-1) + bases_wall_T[:, :nb_bases] @ interpolated_coefficients_wall
    wall['Temperature'] = Result_wall

    wall.active_scalars_name  = 'Temperature'
    actor_wall.mapper.array_name = 'Temperature'
    actor_wall.mapper.scalar_range = [300, 320]

    try:
        ctrl.view_update()
    except:
        pass

@state.change("Bases")
def update_bases(Bases, **kwargs):
    global nb_bases
    global velocity
    global angle
    global current_interpolation_functions_wall
    global wall
    global actor_wall

    nb_bases=int(Bases)

    interpolated_coefficients_wall = []
    for base in range(nb_bases):
        interpolated_coefficients_wall.append(current_interpolation_functions_wall[base]((velocity,angle)))

    ## Reconstruct the field

    Result_wall = np.reshape(mean_wall_T,-1) + bases_wall_T[:, :nb_bases] @ interpolated_coefficients_wall
    wall['Temperature'] = Result_wall

    wall.active_scalars_name  = 'Temperature'
    actor_wall.mapper.array_name = 'Temperature'
    actor_wall.mapper.scalar_range = [300, 320]

    try:
        ctrl.view_update()
    except:
        pass

@state.change("timeofday")
def change_time(timeofday, **kwargs):
    global velocity
    global current_interpolation_functions_wall

    if  timeofday == 'morning':
        current_interpolation_functions_wall = interpolation_functions_wall_am_T

    if  timeofday == 'noon':
        current_interpolation_functions_wall = interpolation_functions_wall_noon_T

    if  timeofday == 'afternoon':
        current_interpolation_functions_wall = interpolation_functions_wall_pm_T


    update_velocity(velocity)



# Initialize


cropped_ground = circle.clip_box(cropping_box, invert= False)   
ground_actor = plotter.add_mesh(cropped_ground, texture=texture, opacity= 0.3)



with SinglePageLayout(server) as layout:

    with layout.toolbar:
        vuetify.VSpacer()
        vuetify.VSlider(
            v_model=("Velocity", 10),
            min=5,
            max=15,
            step=0.1,
            label="Velocity",
            classes="mt-1",
            hide_details=False,
            dense=True,
            thumb_size=16,
            thumb_label=True,
        )

        vuetify.VSlider(
            v_model=("Angle", 0),
            min=0,
            max=360,
            step=0.1,
            label="Angle",
            classes="mt-1",
            hide_details=False,
            dense=True,
            thumb_size=16,
            thumb_label=True,
        )

        vuetify.VSlider(
            v_model=("Bases", 20),
            min=20,
            max=57,
            step=1,
            label="Bases",
            classes="mt-1",
            hide_details=False,
            dense=True,
            thumb_size=16,
            thumb_label=True,
        )

        vuetify.VProgressLinear(
            indeterminate=True,
            absolute=True,
            bottom=True,
            active=("trame__busy",),
        )

        vuetify.VSelect(
            label="TimeOfDay",
            v_model=("timeofday","morning"),
            items=("array_list", ["morning","noon","afternoon"]),
            hide_details=True,
            dense=True,
            outlined=True,
            classes="pt-1 ml-2",
            style="max-width: 250px",
        )


    with layout.content:
        '''
        with html.Div(classes="ma-8"):

            vuetify.VBtn(
            "Update analytics",
            click = hide_field
                 )
            
        '''

        with vuetify.VContainer(
            fluid=True,
            classes="pa-0 fill-height",
        ):
            
            # Use PyVista UI template for Plotters
            view = plotter_ui(plotter)
            ctrl.view_update = view.update
    layout.title.set_text("Marina Temperature")

if __name__ == "__main__":
    server.start()