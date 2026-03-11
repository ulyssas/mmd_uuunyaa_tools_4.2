# Copyright 2026 MMD Tools Append authors
# This file is part of MMD Tools Append.

import math
import re
import unicodedata

import bpy

from ..converters.armatures.humanoid import HumanoidEditor
from ..utilities import import_mmd_tools


def generate_mmd_humanoid(arm, use_eye=True):
    def create_bone_pos(name, collection, head, tail, parent=None, use_connect=False) -> bpy.types.EditBone:
        """Creates child bone based on head & tail position."""
        bone = editor.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        if parent:
            bone.parent = parent
        bone.use_connect = use_connect
        collection.assign(bone)
        return bone

    def create_bone_vec(name, collection, length, parent) -> bpy.types.EditBone:
        """Creates child bone based on parent's orientation and length."""
        bone = editor.edit_bones.new(name)
        bone.use_connect = True
        bone.parent = parent
        bone.align_orientation(parent)
        bone.length = length
        collection.assign(bone)
        return bone

    editor = HumanoidEditor(arm)

    root_coll = editor.bone_collections.new("Root")
    _ik_coll = editor.bone_collections.new("IK")
    center_coll = editor.bone_collections.new("センター")
    body_u_coll = editor.bone_collections.new("体(上)")
    body_l_coll = editor.bone_collections.new("体(下)")
    arm_coll = editor.bone_collections.new("腕")
    finger_coll = editor.bone_collections.new("指")
    leg_coll = editor.bone_collections.new("足")

    root = create_bone_pos("全ての親", root_coll, (0.0, 0.0, 0.0), (0.0, 0.0, 0.7))
    center = create_bone_pos("センター", center_coll, (0.0, 0.0, 0.7), (0.0, 0.0, 0.0), root)

    hips = create_bone_pos("下半身", body_l_coll, (0.0, 0.0, 1.0), (0.0, 0.0, 0.8), center)
    spine = create_bone_pos("上半身", body_u_coll, (0.0, 0.0, 1.0), (0.0, 0.0, 1.1), center)
    chest = create_bone_vec("上半身2", body_u_coll, 0.1, spine)
    upperchest = create_bone_vec("上半身3", body_u_coll, 0.1, chest)
    neck = create_bone_vec("首", body_u_coll, 0.05, upperchest)
    head = create_bone_vec("頭", body_u_coll, 0.2, neck)
    if use_eye:
        eye = create_bone_pos("目.L", body_u_coll, (0.04, -0.03, 1.43), (0.04, -0.08, 1.43), head)
        eye.roll = math.radians(45)

    upperleg = create_bone_pos("足.L", leg_coll, (0.1, 0.0, 0.9), (0.1, -0.005, 0.5), hips)
    lowerleg = create_bone_pos("ひざ.L", leg_coll, (0.1, 0.0, 0.5), (0.1, 0.0, 0.1), upperleg, True)
    foot = create_bone_pos("足首.L", leg_coll, (0.1, 0.0, 0.1), (0.1, -0.2, 0.0), lowerleg, True)
    _toe = create_bone_pos("つま先.L", leg_coll, (0.1, -0.2, 0.0), (0.1, -0.3, 0.0), foot, True)

    shoulder = create_bone_pos("肩.L", arm_coll, (0.02, 0.0, 1.28), (0.12, 0.0, 1.28), upperchest)
    upperarm = create_bone_vec("腕.L", arm_coll, 0.2, shoulder)
    lowerarm = create_bone_vec("ひじ.L", arm_coll, 0.15, upperarm)
    hand = create_bone_vec("手首.L", arm_coll, 0.05, lowerarm)

    little1 = create_bone_pos("小指１.L", finger_coll, (0.53, 0.02, 1.28), (0.545, 0.02, 1.28), hand)
    little2 = create_bone_vec("小指２.L", finger_coll, 0.015, little1)
    _little3 = create_bone_vec("小指３.L", finger_coll, 0.015, little2)
    ring1 = create_bone_pos("薬指１.L", finger_coll, (0.53, -0.01, 1.28), (0.549, -0.01, 1.28), hand)
    ring2 = create_bone_vec("薬指２.L", finger_coll, 0.019, ring1)
    _ring3 = create_bone_vec("薬指３.L", finger_coll, 0.019, ring2)
    middle1 = create_bone_pos("中指１.L", finger_coll, (0.53, 0.0, 1.28), (0.55, 0.0, 1.28), hand)
    middle2 = create_bone_vec("中指２.L", finger_coll, 0.02, middle1)
    _middle3 = create_bone_vec("中指３.L", finger_coll, 0.02, middle2)
    index1 = create_bone_pos("人指１.L", finger_coll, (0.53, 0.01, 1.28), (0.548, 0.01, 1.28), hand)
    index2 = create_bone_vec("人指２.L", finger_coll, 0.018, index1)
    _index3 = create_bone_vec("人指３.L", finger_coll, 0.018, index2)
    thumb1 = create_bone_pos("親指０.L", finger_coll, (0.505, -0.015, 1.28), (0.5198, -0.0211, 1.28), hand)
    thumb2 = create_bone_vec("親指１.L", finger_coll, 0.016, thumb1)
    _thumb3 = create_bone_vec("親指２.L", finger_coll, 0.016, thumb2)

    bpy.ops.armature.select_all(action="SELECT")
    bpy.ops.armature.symmetrize()
    bpy.ops.armature.select_all(action="DESELECT")


def add_mmd_names(arm):
    """Add name_j & name_e based on Blender name"""

    def to_english(name: str) -> str:
        name = unicodedata.normalize("NFKC", name)
        for key, value in JP_EN_MAP.items():
            name = name.replace(key, value)
        return name

    def to_mmd_prefix(name: str) -> str:
        match = re.search(r"\.(L|R)$", name)
        if not match:
            return name

        side = "左" if match.group(1) == "L" else "右"

        # remove prefix
        base = re.sub(r"\.(L|R)$", "", name)

        return side + base

    editor = HumanoidEditor(arm)

    # normalized by unicodedata
    JP_EN_MAP = {
        "全ての親": "Root",
        "センター": "Center",
        "上半身3": "UpperChest",
        "上半身2": "Chest",
        "上半身": "Spine",
        "下半身": "Hips",
        "つま先IK": "ToeIK",
        "足IK": "LegIK",
        "つま先": "Toe",
        "足首": "Foot",
        "ひざ": "LowerLeg",
        "足": "UpperLeg",
        "肩": "Shoulder",
        "腕": "UpperArm",
        "ひじ": "LowerArm",
        "手首": "Hand",
        "小指": "Little",
        "薬指": "Ring",
        "中指": "Middle",
        "人指": "Index",
        "親指": "Thumb",
        "首": "Neck",
        "頭": "Head",
        "目": "Eye",
    }

    for b in editor.pose_bones:
        b.mmd_bone.name_j = to_mmd_prefix(b.name)
        b.mmd_bone.name_e = to_english(b.name)


class AddMMDHumanoidRig(bpy.types.Operator):
    bl_idname = "mmd_tools_append.add_mmd_humanoid_rig"
    bl_label = "Add MMD Humanoid Rig"
    bl_description = "Generate armature with MMD compatible setup"
    bl_options = {"REGISTER", "UNDO"}

    name_j: bpy.props.StringProperty(
        name="Name",
        description="The name of the MMD model",
        default="New MMD Model",
    )
    name_e: bpy.props.StringProperty(
        name="Name(Eng)",
        description="The english name of the MMD model",
        default="New MMD Model",
    )
    scale: bpy.props.FloatProperty(
        name="Scale",
        description="Scale",
        default=0.08,
    )
    use_leg_ik: bpy.props.BoolProperty(
        name="Use Leg IK",
        description="Add Leg IK to MMD rig",
        default=True,
    )
    add_eye: bpy.props.BoolProperty(
        name="Add Eye bones",
        description="Add eye bones to MMD rig",
        default=True,
    )
    use_local_axis: bpy.props.BoolProperty(
        name="Use Local axis",
        description="Set up local axis for arms and fingers",
        default=False,
    )

    @classmethod
    def poll(cls, context):
        return context.mode == "OBJECT"

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            # from CreateMMDModelRoot
            rig = import_mmd_tools().core.model.Model.create(self.name_j, self.name_e, self.scale, add_root_bone=False)
            rig.initialDisplayFrames()

            bpy.context.view_layer.objects.active = rig.armature()
            bpy.ops.object.mode_set(mode="EDIT")
            generate_mmd_humanoid(rig.armature(), self.add_eye)
            bpy.ops.object.mode_set(mode="POSE")

            editor = HumanoidEditor(rig.armature())
            if self.use_leg_ik:
                editor.add_leg_ik()

            editor.to_mmd_pose(self.use_local_axis)
            add_mmd_names(rig.armature())

            bpy.ops.mmd_tools.display_item_quick_setup(type="GROUP_LOAD")
            bpy.ops.mmd_tools.fix_bone_order()

        except Exception as e:
            self.report({"ERROR"}, message=f"Failed to add MMD rig: {e}")
            return {"CANCELLED"}
        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class MMDAppendMMDRigMenu(bpy.types.Menu):
    bl_idname = "VIEW3D_MT_mmd_append_mmd_rig"
    bl_label = "MMD Append"

    def draw(self, _context):
        pass

    @staticmethod
    def draw_menu(this: bpy.types.Menu, _context):
        this.layout.operator(AddMMDHumanoidRig.bl_idname, text="Generate MMD humanoid", icon="OUTLINER_OB_ARMATURE")

    @staticmethod
    def register():
        bpy.types.VIEW3D_MT_armature_add.append(MMDAppendMMDRigMenu.draw_menu)

    @staticmethod
    def unregister():
        bpy.types.VIEW3D_MT_armature_add.remove(MMDAppendMMDRigMenu.draw_menu)
