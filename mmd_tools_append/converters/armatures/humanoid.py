# Copyright 2026 MMD Tools Append authors
# This file is part of MMD Tools Append.

from collections.abc import Iterator

import bpy

from ...editors.armatures import ArmatureEditor
from ...utilities import MessageException

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


# Operators
class HumanoidInitializeOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_initialize"
    bl_label = "Initialize Humanoid Renamer"
    bl_description = "Initialize MMD compatible Humanoid structure data for renaming bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        try:
            context.active_object.mmd_tools_append_humanoid_settings.initialize_humanoid()
        except MessageException as ex:
            self.report({"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        return {"FINISHED"}


class HumanoidRenameOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_rename"
    bl_label = "Execute Rename"
    bl_description = "Rename selected bones to MMD compatible Japanese name"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        if active_object is None:
            return False

        return active_object.type == "ARMATURE"

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            bpy.ops.object.mode_set(mode="EDIT")
            tree: HumanoidTree = context.active_object.mmd_tools_append_humanoid_settings
            arm = ArmatureEditor(context.active_object)
            count = 0

            LR_MAP = {0: "左", 1: "右"}
            HALF_FULL = str.maketrans("0123456789", "０１２３４５６７８９")

            for frame, item in tree.iter_items():
                for idx, slot in enumerate(item.slots):
                    if not slot.bone_name:
                        continue

                    bone = arm.edit_bones.get(slot.bone_name)
                    if not bone:
                        continue

                    pbone = arm.pose_bones[slot.bone_name]
                    original = bone.name
                    target = item.mmd_j

                    match frame.display_type:
                        case "MIRRORED":
                            target = f"{LR_MAP.get(idx, '')}{target}"
                        case "FINGER":
                            # 親指ならbaseから0, 1, 2 (全角)
                            init_n = 0 if item.name == "Thumb" else 1
                            target += str(idx + init_n).translate(HALF_FULL)

                    # rename!
                    bone.name = target
                    pbone.mmd_bone.name_j = target
                    pbone.mmd_bone.name_e = original

                    count += 1

            tree.reset_humanoid()

        except MessageException as ex:
            self.report(type={"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        finally:
            self.report({"INFO"}, message=f"Renamed {count} bones.")
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}
