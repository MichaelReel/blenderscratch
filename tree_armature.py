# <pep8-80 compliant>
bl_info = {
    "name": "Tree Shaped Armature Generator",
    "description": "Creates an armature object that vaguely resembles a tree.",
    "author": "Michael Reel",
    "version": (1, 0),
    "blender": (2, 91, 0),
    "location": "View3D > Add > Mesh > New Object",
    "warning": "",
    "doc_url": "https://github.com/MichaelReel/blenderscratch",
    "tracker_url": "https://github.com/MichaelReel/blenderscratch/issues",
    "support": "TESTING",
    "category": "Rigging",
}

import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, IntProperty, FloatProperty
from bpy_extras.object_utils import AddObjectHelper, object_data_add
from math import pi


class OBJECT_OT_add_object(Operator, AddObjectHelper):
    """Create a new Tree Mesh Object with Armature"""
    bl_idname = "mesh.add_object"
    bl_label = "Add Tree Mesh Object with Armature"
    bl_options = {'REGISTER', 'UNDO'}

    # Input variables
    start_bough_size: FloatProperty(
        name="Initial Branch Size",
        default=1.0,
        unit="LENGTH",
        subtype="DISTANCE",
        description="The starting size of the trunk from which subsequent branches are scaled.",
        soft_min=0.001,
        soft_max=100.0,
    )
    start_branch_tilt: FloatProperty(
        name="Initial Branch Tilt",
        default=1.053414,
        unit="ROTATION",
        subtype="ANGLE",
        description="The starting bend of each new branch from the parent branch from which subsequent bends are scaled.",
        min=-pi,
        max=2*pi,
        soft_min=0.0,
        soft_max=pi,
        step=360/pi,
    )
    branch_segments: IntProperty( 
        name="Branch Occurrences",
        default=3,
        description="The number of times a branch will be split into smaller branches.",
        min=0,
        max=10,
        soft_min=0,
        soft_max=5,
    )
    branch_per_segment: IntProperty(
        name="Sub Branches per Split",
        default=3,
        description="The number of new branches that are created at each split.",
        min=1,
        max=10,
        soft_min=0,
        soft_max=5,
    )
    bough_length_mod: FloatProperty(
        name="Branch Size Increment",
        default=-0.1,
        unit="LENGTH",
        subtype="DISTANCE",
        description="The incremental length change to each sub-branch in comparison to it's parent branch.",
        soft_min=-10.0,
        soft_max=100.0,
    )
    branch_tilt_mod: FloatProperty(
        name="Branch Tilt Increment",
        default=-0.157434,
        unit="ROTATION",
        subtype="ANGLE",
        description="The incremental change to the bend of each new branch in comparison to the bend between the parent and grandparent branch.",
        min=-pi,
        max=pi,
        soft_min=-pi,
        soft_max=pi,
    )
    show_data_debug: BoolProperty(
        name="Show Names and Axes",
        description="Primarily for debug this will have the axes and bones lables turned on. These can be disabled or enabled afterwards.",
    )


    @staticmethod
    def object_mode():
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')


    @staticmethod
    def edit_mode():
        if bpy.context.mode != 'EDIT':
            bpy.ops.object.mode_set(mode='EDIT')


    def add_bough(self, parent_bone, bough_size, tilt, rotation, depth=0):
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
        bough.roll = bough.parent.roll + rotation
        
        # Tilt the sub-branch by the given degrees, relative to what is now it's own orientation
        bpy.ops.transform.rotate(
            value=tilt,
            orient_matrix=bough.matrix.to_3x3(),
            orient_axis='X',
            orient_type='LOCAL',
            orient_matrix_type='LOCAL',
        )
        
        if depth > 0:
            # Create a set of sub branches
            degrees_per_segment = 2 * pi / self.branch_per_segment
            for branch in range(self.branch_per_segment):
                self.add_bough(
                    parent_bone=bough,
                    bough_size=bough_size + self.bough_length_mod,
                    tilt=tilt + self.branch_tilt_mod,
                    rotation=degrees_per_segment * branch,
                    depth=depth - 1
                )

        # Back 'up' (down? root-ward?) the tree
        for bone in main_object.data.edit_bones:
            bone.select = False
            bone.select_tail = False
            bone.select_head = False
        parent_bone.select_tail = True


    def create_armature(self, context):
        """
        Creates an armature object and data that creates a fractal-like tree structure.
        """
        # Create an armature object with the 'trunk' bone
        bpy.ops.object.armature_add(
            align='CURSOR',
        )
        
        self.edit_mode()
        
        # Get references and rename primary components
        object = bpy.context.object
        object.name = "Tree"
        armature = object.data
        armature.name = "TreeArmature"
        trunk = armature.edit_bones.active
        trunk.name = "Trunk"
        
        # Some debug settings (optional)
        if self.show_data_debug:
            object.show_axis = True
            object.data.show_axes = True
            object.data.show_names = True
        
        # Move the end of the first bone upwards
        bpy.ops.transform.translate(
            value=(0, 0, self.start_bough_size),
            orient_matrix_type='CURSOR',
        )
        
        if self.branch_segments > 0:
            # Create a set of branches
            degrees_per_segment = 2 * pi / self.branch_per_segment
            for branch in range(self.branch_per_segment):
                self.add_bough(
                    parent_bone=trunk,
                    bough_size=self.start_bough_size + self.bough_length_mod,
                    tilt=self.start_branch_tilt,
                    rotation=degrees_per_segment * branch,
                    depth=self.branch_segments - 1
                )



    def execute(self, context):
        self.object_mode()
        self.create_armature(context)
        self.object_mode()
        return {'FINISHED'}


# Registration

def add_object_button(self, context):
    self.layout.operator(
        OBJECT_OT_add_object.bl_idname,
        text="Add Object",
        icon='PLUGIN')


# This allows you to right click on a button and link to documentation
def add_object_manual_map():
    url_manual_prefix = "https://docs.blender.org/manual/en/latest/"
    url_manual_mapping = (
        ("bpy.ops.mesh.add_object", "scene_layout/object/types.html"),
    )
    return url_manual_prefix, url_manual_mapping


def register():
    bpy.utils.register_class(OBJECT_OT_add_object)
    bpy.utils.register_manual_map(add_object_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.append(add_object_button)


def unregister():
    bpy.utils.unregister_class(OBJECT_OT_add_object)
    bpy.utils.unregister_manual_map(add_object_manual_map)
    bpy.types.VIEW3D_MT_mesh_add.remove(add_object_button)


if __name__ == "__main__":
    register()