# Copyright 2026 MMD Tools Append authors
# This file is part of MMD Tools Append.

import bpy

from ...utilities import MessageException

HUMANOID_CATEGORY = [
    ("BODY", "Body", "Spine, arm and leg bones"),
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
            {"name": "Hips"},
            {"name": "Spine"},
            {"name": "Chest"},
            {"name": "UpperChest"},
        ],
    },
    {
        "name": "Arm",
        "icon": "VIEW_PAN",
        "category": "BODY",
        "display_type": "MIRRORED",
        "items": [
            {"name": "Shoulder"},
            {"name": "UpperArm"},
            {"name": "LowerArm"},
            {"name": "Hand"},
        ],
    },
    {
        "name": "Leg",
        "icon": "MOD_DYNAMICPAINT",
        "category": "BODY",
        "display_type": "MIRRORED",
        "items": [
            {"name": "UpperLeg"},
            {"name": "LowerLeg"},
            {"name": "Foot"},
            {"name": "Toe"},
        ],
    },
    {
        "name": "Head",
        "icon": "USER",
        "category": "HEAD",
        "display_type": "DEFAULT",
        "items": [
            {"name": "Neck"},
            {"name": "Head"},
            {"name": "LeftEye"},
            {"name": "RightEye"},
        ],
    },
    {
        "name": "Left Hand",
        "icon": "MOD_DYNAMICPAINT",
        "category": "HAND_L",
        "display_type": "FINGER",
        "items": [
            {"name": "Thumb"},
            {"name": "Index"},
            {"name": "Middle"},
            {"name": "Ring"},
            {"name": "Little"},
        ],
    },
    {
        "name": "Right Hand",
        "icon": "MOD_DYNAMICPAINT",
        "category": "HAND_R",
        "display_type": "FINGER",
        "items": [
            {"name": "Thumb"},
            {"name": "Index"},
            {"name": "Middle"},
            {"name": "Ring"},
            {"name": "Little"},
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

    name: bpy.props.StringProperty()
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
    categories: bpy.props.EnumProperty(
        name="Category",
        items=HUMANOID_CATEGORY,
    )
    frames: bpy.props.CollectionProperty(type=HumanoidDisplayFrame)

    def initialize_humanoid(self, data: dict = HUMANOID_DEFAULTS):
        if self.frames:
            return

        for frame_data in data:
            frame = self.frames.add()
            frame.name = frame_data["name"]
            frame.icon = frame_data["icon"]
            frame.category = frame_data["category"]
            frame.display_type = frame_data.get("display_type", "DEFAULT")

            for item_data in frame_data.get("items", []):
                item = frame.items.add()
                item.name = item_data["name"]

            frame.sync_display_type(None)

    @staticmethod
    def register():
        bpy.types.Object.mmd_tools_append_humanoid_settings = bpy.props.PointerProperty(type=HumanoidTree)

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_tools_append_humanoid_settings


class HumanoidInitializeOperator(bpy.types.Operator):
    bl_idname = "mmd_tools_append.humanoid_initialize"
    bl_label = "Initialize Humanoid Renamer"
    bl_description = "Initialize Humanoid structure data."
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
            context.object.mmd_tools_append_humanoid_settings.initialize_humanoid()
        except MessageException as ex:
            self.report(type={"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        return {"FINISHED"}
