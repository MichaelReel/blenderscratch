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
branch_segments = 3  # Max ~4

bough_length_mod = -1
branch_tilt_mod = -10


def object_mode():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')


def edit_mode():
    if bpy.context.mode != 'EDIT':
        bpy.ops.object.mode_set(mode='EDIT')


def add_bough(parent_bone, bough_size, tilt, rotation, depth=0):
    # Need to access the collection of branches/bones
    main_object = bpy.context.object
    print(f"Extruding upon {parent_bone.name}")
    
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
    print(f"Bough created '{bough_name}' on parent {bough.parent.name}")
    
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
        for branch in [
            (bough, bough_size + bough_length_mod, tilt + branch_tilt_mod, 0, depth - 1),
            (bough, bough_size + bough_length_mod, tilt + branch_tilt_mod, 90, depth - 1),
            (bough, bough_size + bough_length_mod, tilt + branch_tilt_mod, 180, depth - 1),
            (bough, bough_size + bough_length_mod, tilt + branch_tilt_mod, 270, depth - 1)
        ]:
            print(f"Making bough: {branch} on {bough.name}")
            add_bough(*branch)

    # Back 'up' (down? root-ward?) the tree
    for bone in main_object.data.edit_bones:
        bone.select = False
        bone.select_tail = False
        bone.select_head = False
    parent_bone.select_tail = True


def create_armature():
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
#    object.show_axis = True
#    object.data.show_axes = True
#    object.data.show_names = True
    
    # Move the end of the first bone upwards
    bpy.ops.transform.translate(
        value=(0, 0, start_bough_size),
        orient_matrix_type='CURSOR',
    )
    
    print(f"Trunk created with name: {trunk.name}")
    if branch_segments > 0:
        # Create a set of branches
        for branch in [
            (trunk, start_bough_size + bough_length_mod, start_branch_tilt, 0, branch_segments - 1),
            (trunk, start_bough_size + bough_length_mod, start_branch_tilt, 90, branch_segments - 1),
            (trunk, start_bough_size + bough_length_mod, start_branch_tilt, 180, branch_segments - 1),
            (trunk, start_bough_size + bough_length_mod, start_branch_tilt, 270, branch_segments - 1)
        ]:
            print(f"Make bough: {branch} on {trunk.name}")
            add_bough(*branch)

print("\n-- SCRIPT START --")
object_mode()

create_armature()

print("-- SCRIPT COMPLETE --\n")
object_mode()