# Copyright 2026 MMD Tools Append authors
# This file is part of MMD Tools Append.

import math
from collections.abc import Iterator

import bpy

from ...editors.armatures import ArmatureEditor

# constants
MMD_CONTROL = ("センター", "全ての親", "足ＩＫ.L", "足ＩＫ.R", "つま先ＩＫ.L", "つま先ＩＫ.R")

HUMANOID_CATEGORY = [
    ("BODY", "Body", "Spine, arm and leg"),
    ("HEAD", "Head", "Neck, head and eyes"),
    ("HAND_L", "Left Hand", "Left hand fingers"),
    ("HAND_R", "Right Hand", "Right hand fingers"),
]

DISPLAY_TYPE_COLUMNS = {
    "DEFAULT": 1,
    "MIRRORED": 2,
    "FINGER": 3,
}

HUMANOID_DEFAULTS = [
    {
        "name": "Body",
        "icon": "OUTLINER_OB_ARMATURE",
        "category": "BODY",
        "display_type": "DEFAULT",
        "items": [
            {"name": "Hips", "mmd_j": "下半身"},
            {"name": "Spine", "mmd_j": "上半身"},
            {"name": "Chest", "mmd_j": "上半身2"},
            {"name": "UpperChest", "mmd_j": "上半身3"},
        ],
    },
    {
        "name": "Arm",
        "icon": "VIEW_PAN",
        "category": "BODY",
        "display_type": "MIRRORED",
        "items": [
            {"name": "Shoulder", "mmd_j": "肩"},
            {"name": "UpperArm", "mmd_j": "腕"},
            {"name": "LowerArm", "mmd_j": "ひじ"},
            {"name": "Hand", "mmd_j": "手首"},
        ],
    },
    {
        "name": "Leg",
        "icon": "MOD_DYNAMICPAINT",
        "category": "BODY",
        "display_type": "MIRRORED",
        "items": [
            {"name": "UpperLeg", "mmd_j": "足"},
            {"name": "LowerLeg", "mmd_j": "ひざ"},
            {"name": "Foot", "mmd_j": "足首"},
            {"name": "Toe", "mmd_j": "つま先"},
        ],
    },
    {
        "name": "Head",
        "icon": "USER",
        "category": "HEAD",
        "display_type": "DEFAULT",
        "items": [
            {"name": "Neck", "mmd_j": "首"},
            {"name": "Head", "mmd_j": "頭"},
            {"name": "LeftEye", "mmd_j": "左目"},
            {"name": "RightEye", "mmd_j": "右目"},
        ],
    },
    {
        "name": "Left Hand",
        "icon": "VIEW_PAN",
        "category": "HAND_L",
        "display_type": "FINGER",
        "items": [
            {"name": "Thumb", "mmd_j": "左親指"},
            {"name": "Index", "mmd_j": "左人指"},
            {"name": "Middle", "mmd_j": "左中指"},
            {"name": "Ring", "mmd_j": "左薬指"},
            {"name": "Little", "mmd_j": "左小指"},
        ],
    },
    {
        "name": "Right Hand",
        "icon": "VIEW_PAN",
        "category": "HAND_R",
        "display_type": "FINGER",
        "items": [
            {"name": "Thumb", "mmd_j": "右親指"},
            {"name": "Index", "mmd_j": "右人指"},
            {"name": "Middle", "mmd_j": "右中指"},
            {"name": "Ring", "mmd_j": "右薬指"},
            {"name": "Little", "mmd_j": "右小指"},
        ],
    },
]


# property groups
class HumanoidBoneSlot(bpy.types.PropertyGroup):
    bone_name: bpy.props.StringProperty(name="Bone")


class HumanoidItem(bpy.types.PropertyGroup):
    """
    Each element of humanoid bones.

    Mirrored element (.L/.R) and finger bones (1-3) will be processed together.
    """

    def _update_slot_size(self, _context):
        """keep slots at a fixed size"""

        while len(self.slots) > self.column_count:
            self.slots.remove(len(self.slots) - 1)

        while len(self.slots) < self.column_count:
            self.slots.add()

    name: bpy.props.StringProperty()
    mmd_j: bpy.props.StringProperty()
    column_count: bpy.props.IntProperty(default=1, update=_update_slot_size)
    slots: bpy.props.CollectionProperty(type=HumanoidBoneSlot)


class HumanoidDisplayFrame(bpy.types.PropertyGroup):
    def _check_category(self, _context):
        if self.category not in [item[0] for item in HUMANOID_CATEGORY]:
            print("Invalid DisplayFrame category")

    def sync_display_type(self, _context):
        column = DISPLAY_TYPE_COLUMNS.get(self.display_type, 1)
        for item in self.items:
            item.column_count = column

    name: bpy.props.StringProperty(translation_context="MMD_HUMANOID")
    icon: bpy.props.StringProperty()
    category: bpy.props.StringProperty(update=_check_category)
    """must be one of IDs in HUMANOID_CATEGORY"""

    display_type: bpy.props.EnumProperty(
        items=[
            ("DEFAULT", "Default", "1 slot (default)"),
            ("MIRRORED", "Mirrored", "2 slots for Left/Right"),
            ("FINGER", "Finger", "3 slots for finger"),
        ],
        update=sync_display_type,
    )
    split_factor: bpy.props.FloatProperty(default=0.2)
    items: bpy.props.CollectionProperty(type=HumanoidItem)


class HumanoidTree(bpy.types.PropertyGroup):
    frames: bpy.props.CollectionProperty(type=HumanoidDisplayFrame)

    def initialize_humanoid(self, data: dict = HUMANOID_DEFAULTS):
        if self.frames:
            return

        self.reset_humanoid(data)

    def reset_humanoid(self, data: dict = HUMANOID_DEFAULTS):
        self.frames.clear()

        for frame_data in data:
            frame = self.frames.add()
            frame.name = frame_data["name"]
            frame.icon = frame_data["icon"]
            frame.category = frame_data["category"]
            frame.display_type = frame_data.get("display_type", "DEFAULT")

            for item_data in frame_data.get("items", []):
                item = frame.items.add()
                item.name = item_data["name"]
                item.mmd_j = item_data.get("mmd_j", "")

            frame.sync_display_type(None)

    def iter_items(self) -> Iterator[tuple[HumanoidDisplayFrame, HumanoidItem]]:
        """access HumanoidItem as iterator"""

        for frame in self.frames:
            for item in frame.items:
                yield frame, item

    @staticmethod
    def register():
        bpy.types.Object.mmd_tools_append_humanoid_settings = bpy.props.PointerProperty(type=HumanoidTree)
        bpy.types.WindowManager.mmd_humanoid_category = bpy.props.EnumProperty(
            name="Append Humanoid Category",
            items=HUMANOID_CATEGORY,
            default="BODY",
            translation_context="MMD_HUMANOID",
        )

    @staticmethod
    def unregister():
        del bpy.types.WindowManager.mmd_humanoid_category
        del bpy.types.Object.mmd_tools_append_humanoid_settings


class HumanoidEditor(ArmatureEditor):
    tree: HumanoidTree

    def __init__(self, armature_object: bpy.types.Object):
        super().__init__(armature_object)
        self.tree = armature_object.mmd_tools_append_humanoid_settings

    @staticmethod
    def convert_mmd_prefix(name: str) -> str:
        """左右 prefix to .LR suffix"""
        if name.startswith("左"):
            return name[1:] + ".L"
        if name.startswith("右"):
            return name[1:] + ".R"
        return name

    def to_mmd_pose(self, use_local=False):
        def to_mmd_bone():
            """Locks positions of the bones and changes display connection to child bone."""
            for pbone in self.pose_bones:
                if pbone.name not in MMD_CONTROL:
                    pbone.lock_location = [True, True, True]
                    pbone.lock_rotation_w = False
                if len(pbone.children) == 1:
                    pbone.mmd_bone.display_connection_type = "BONE"
                    pbone.mmd_bone.display_connection_bone = pbone.children[0].name

        def remove_deform():
            """Disables `use_deform` to exclude from Automatic Weights."""
            for bone in self.bones:
                if bone.name in MMD_CONTROL:
                    bone.use_deform = False

        def apply_local():
            for bone in self.bone_collections["指"].bones:
                pbone = self.pose_bones[bone.name]
                pbone.select = True
                pbone.mmd_bone.enabled_local_axes = True

            for bone in self.bone_collections["腕"].bones:
                if "肩" not in bone.name:
                    pbone = self.pose_bones[bone.name]
                    pbone.select = True
                    pbone.mmd_bone.enabled_local_axes = True

            bpy.ops.mmd_tools.bone_local_axes_setup(type="LOAD")
            bpy.ops.mmd_tools.bone_local_axes_setup(type="APPLY")

        angle = math.radians(45)

        pb = self.pose_bones["腕.L"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler[0] = -angle

        pb = self.pose_bones["腕.R"]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler[0] = -angle

        bpy.ops.pose.armature_apply()
        to_mmd_bone()
        remove_deform()
        if use_local:
            apply_local()

    def add_leg_ik(self):
        """Adapted from MMD Tools Helper"""

        def add_limit_rot(pbone: bpy.types.PoseBone):
            self.add_constraint(
                pbone,
                "LIMIT_ROTATION",
                "mmd_ik_limit_override",
                use_limit_x=True,
                use_limit_y=False,
                use_limit_z=False,
                min_x=math.pi / 360,  # radians=0.5 degrees
                max_x=math.pi,  # radians=180 degrees
                min_y=0,
                max_y=0,
                min_z=0,
                max_z=0,
                owner_space="LOCAL",
            )

        def add_ik_limit(pbone: bpy.types.PoseBone):
            pbone.use_ik_limit_x = True
            pbone.use_ik_limit_y = True
            pbone.use_ik_limit_z = True
            pbone.ik_min_x = 0
            pbone.ik_max_x = math.pi
            pbone.ik_min_y = 0
            pbone.ik_max_y = 0
            pbone.ik_min_z = 0
            pbone.ik_max_z = 0

        ROOT = "全ての親"
        LEG_IK_L = "足ＩＫ.L"
        LEG_IK_R = "足ＩＫ.R"
        TOE_IK_L = "つま先ＩＫ.L"
        TOE_IK_R = "つま先ＩＫ.R"

        KNEE_L = "ひざ.L"
        KNEE_R = "ひざ.R"
        ANKLE_L = "足首.L"
        ANKLE_R = "足首.R"
        TOE_L = "つま先.L"
        TOE_R = "つま先.R"

        bpy.ops.object.mode_set(mode="POSE")

        add_ik_limit(self.pose_bones[KNEE_L])
        add_ik_limit(self.pose_bones[KNEE_R])

        # used for IK bone length
        FOOT_LENGTH = self.bones[ANKLE_L].length

        bpy.ops.object.mode_set(mode="EDIT")

        # Add IK bones
        bone = self.edit_bones.new(LEG_IK_L)
        bone.head = self.edit_bones[ANKLE_L].head
        bone.tail = self.edit_bones[ANKLE_L].head
        bone.tail.y = self.edit_bones[ANKLE_L].head.y + FOOT_LENGTH
        bone.parent = self.edit_bones[ROOT]

        bone = self.edit_bones.new(LEG_IK_R)
        bone.head = self.edit_bones[ANKLE_R].head
        bone.tail = self.edit_bones[ANKLE_R].head
        bone.tail.y = self.edit_bones[ANKLE_R].head.y + FOOT_LENGTH
        bone.parent = self.edit_bones[ROOT]

        bone = self.edit_bones.new(TOE_IK_L)
        bone.head = self.edit_bones[TOE_L].head
        bone.tail = self.edit_bones[TOE_L].head
        bone.tail.z = self.edit_bones[TOE_L].head.z - FOOT_LENGTH / 2
        bone.parent = self.edit_bones[LEG_IK_L]

        bone = self.edit_bones.new(TOE_IK_R)
        bone.head = self.edit_bones[TOE_R].head
        bone.tail = self.edit_bones[TOE_R].head
        bone.tail.z = self.edit_bones[TOE_R].head.z - FOOT_LENGTH / 2
        bone.parent = self.edit_bones[LEG_IK_R]

        bpy.ops.object.mode_set(mode="POSE")

        # Add bone constraints
        self.add_ik_constraint(self.pose_bones[KNEE_L], self.raw_object, LEG_IK_L, 2, 200)
        self.add_ik_constraint(self.pose_bones[KNEE_R], self.raw_object, LEG_IK_R, 2, 200)
        self.add_ik_constraint(self.pose_bones[ANKLE_L], self.raw_object, TOE_IK_L, 1, 15)
        self.add_ik_constraint(self.pose_bones[ANKLE_R], self.raw_object, TOE_IK_R, 1, 15)

        self.pose_bones[KNEE_L].mmd_bone.ik_rotation_constraint = 2  # 180*2/math.pi
        self.pose_bones[KNEE_R].mmd_bone.ik_rotation_constraint = 2  # 180*2/math.pi
        self.pose_bones[ANKLE_L].mmd_bone.ik_rotation_constraint = 4  # 180*4/math.pi
        self.pose_bones[ANKLE_R].mmd_bone.ik_rotation_constraint = 4  # 180*4/math.pi

        add_limit_rot(self.pose_bones[KNEE_L])
        add_limit_rot(self.pose_bones[KNEE_R])

        # Add to Bone Collection
        self.bone_collections["IK"].assign(self.pose_bones[LEG_IK_L])
        self.bone_collections["IK"].assign(self.pose_bones[LEG_IK_R])
        self.bone_collections["IK"].assign(self.pose_bones[TOE_IK_L])
        self.bone_collections["IK"].assign(self.pose_bones[TOE_IK_R])

    def rename(self) -> int:
        count = 0

        LR_MAP_MMD = {0: "左", 1: "右"}
        HALF_FULL = str.maketrans("0123456789", "０１２３４５６７８９")

        for frame, item in self.tree.iter_items():
            for idx, slot in enumerate(item.slots):
                if not slot.bone_name:
                    continue

                bone = self.edit_bones.get(slot.bone_name)
                if not bone:
                    continue

                pbone = self.pose_bones[slot.bone_name]
                original = bone.name
                target = item.mmd_j

                match frame.display_type:
                    case "MIRRORED":
                        target = f"{LR_MAP_MMD.get(idx, '')}{target}"
                    case "FINGER":
                        # 親指ならbaseから0, 1, 2 (全角)
                        init_n = 0 if item.name == "Thumb" else 1
                        target += str(idx + init_n).translate(HALF_FULL)

                # rename!
                bone.name = self.convert_mmd_prefix(target)
                pbone.mmd_bone.name_j = target
                pbone.mmd_bone.name_e = original

                count += 1

        self.tree.reset_humanoid()

        return count

    def detect(self):
        pass
