# <pep8-80 compliant>
import bpy
from math import radians

'''
Create an armature and mesh/object at the cursor
'''

# Input variables: 
# TODO: get from dialog?
start_bough_size = 5
start_branch_tilt = 50
branch_segments = 4  # Max ~4
branch_per_segment = 3

bough_length_mod = -0.75
branch_tilt_mod = -10
show_data_debug = False


def object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def edit_mode():
    if bpy.context.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')


def add_bough(parent_bone, bough_size, tilt, rotation, depth=0):
    """
    Adds a branch along with recursive sub-branches.
    
    `parent_bone` is the bone to which the branch will be added
    and also to which context will be returned on completion.
    `bough_size` is the length of the current branch.
    N.B: sub branches will be modified by the global settings
    `tilt` is the angle in degrees from the parent orientation
    offsetting from what would be a direct extension.
    `rotation` is the roll angle around the parent branch at which 
    to tilt the new branch.
    `depth` is how maybe recursive layers of sub-branches to generate. 
    """
    # Need to access the collection of branches/bones
    main_object = bpy.context.object
    
    # Extrude off of the currently selected bone
    bpy.ops.armature.extrude_move(
        TRANSFORM_OT_translate={
            "value": (0, 0, bough_size),
            "orient_type": 'LOCAL',
            "orient_matrix_type": 'LOCAL',
        }
    )
    
    # Give this bough some kind of name (it might be renamed)
    bough = bpy.context.active_object.data.edit_bones.active
    bough.name = "Bough"
    bough_name = bough.name
    
    # Initially, line up this new branch to the parent branch
    bough.align_orientation(bough.parent)
    
    # Rotate relative to the parent by the given degrees
    bough.roll = bough.parent.roll + radians(rotation)
    
    # Tilt the sub-branch by the given degrees, relative to what is now it's own orientation
    bpy.ops.transform.rotate(
        value=radians(tilt),
        orient_matrix=bough.matrix.to_3x3(),
        orient_axis='X',
        orient_type='LOCAL',
        orient_matrix_type='LOCAL',
    )
    
    if depth > 0:
        # Create a set of sub branches
        degrees_per_segment = 360 / branch_per_segment
        for branch in range(branch_per_segment):
            add_bough(
                parent_bone=bough,
                bough_size=bough_size + bough_length_mod,
                tilt=tilt + branch_tilt_mod,
                rotation=degrees_per_segment * branch,
                depth=depth - 1
            )

    # Back 'up' (down? root-ward?) the tree
    for bone in main_object.data.edit_bones:
        bone.select = False
        bone.select_tail = False
        bone.select_head = False
    parent_bone.select_tail = True


def create_armature():
    """
    Creates an armature object and data that creates a fractal-like tree structure.
    """
    # Create an armature object with the 'trunk' bone
    bpy.ops.object.armature_add(
        align='CURSOR',
    )
    
    edit_mode()
    
    # Get references and rename primary components
    object = bpy.context.object
    object.name = "Tree"
    armature = object.data
    armature.name = "TreeArmature"
    trunk = armature.edit_bones.active
    trunk.name = "Trunk"
    
    # Some debug settings (optional)
    if show_data_debug:
        object.show_axis = True
        object.data.show_axes = True
        object.data.show_names = True
    
    # Move the end of the first bone upwards
    bpy.ops.transform.translate(
        value=(0, 0, start_bough_size),
        orient_matrix_type='CURSOR',
    )
    
    if branch_segments > 0:
        # Create a set of branches
        degrees_per_segment = 360 / branch_per_segment
        for branch in range(branch_per_segment):
            add_bough(
                parent_bone=trunk,
                bough_size=start_bough_size + bough_length_mod,
                tilt=start_branch_tilt,
                rotation=degrees_per_segment * branch,
                depth=branch_segments - 1
            )

print("\n-- SCRIPT START --")
object_mode()

create_armature()

print("-- SCRIPT COMPLETE --\n")
object_mode()