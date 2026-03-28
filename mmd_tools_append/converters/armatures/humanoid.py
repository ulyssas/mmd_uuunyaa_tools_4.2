# Copyright 2026 MMD Tools Append authors
# This file is part of MMD Tools Append.

import math
import re
from collections.abc import Iterator

import bpy
from mathutils import Vector

from ...editors.armatures import ArmatureEditor
from ...utilities import import_mmd_tools

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
        "name_j": "体(上)",
        "icon": "OUTLINER_OB_ARMATURE",
        "category": "BODY",
        "display_type": "DEFAULT",
        "items": [
            {"name": "Hips", "mmd_j": "下半身", "frame_override": "体(下)"},
            {"name": "Spine", "mmd_j": "上半身"},
            {"name": "Chest", "mmd_j": "上半身2"},
            {"name": "UpperChest", "mmd_j": "上半身3"},
        ],
    },
    {
        "name": "Arm",
        "name_j": "腕",
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
        "name_j": "足",
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
        "name_j": "頭",
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
        "name_j": "指",
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
        "name_j": "指",
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

    def info(self):
        return f'HumanoidBoneSlot("{self.bone_name}")'


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

    def auto(self, editor, display_type):
        """Auto fills empty slots based on existing selection."""

        def flip_name(name: str) -> str:
            """Convert names like Arm.L, Arm_L, LeftArm, ArmLeft to right."""

            suffix_pattern = r"([._-])([LRlr])$"
            match = re.search(suffix_pattern, name)
            if match:
                delim = match.group(1)
                suffix = match.group(2)
                flipped = {"L": "R", "R": "L", "l": "r", "r": "l"}[suffix]
                return name[:-2] + delim + flipped
            else:
                mappings = {}
                LR = [("left", "right"), ("Left", "Right"), ("LEFT", "RIGHT"), ("J_Bip_L", "J_Bip_R")]
                for k, v in LR:
                    mappings[k] = v
                    mappings[v] = k
                pattern = re.compile("|".join(re.escape(k) for k in mappings.keys()))
                return pattern.sub(lambda m: mappings[m.group(0)], name)

        def get_lineal(name: str) -> tuple[str, str]:
            """Get parent and first child."""

            parent = ""
            child = ""
            if name in editor.bones:
                bone = editor.bones[name]
                parent = bone.parent.name if bone.parent else ""
                child = bone.children[0].name if bone.children else ""
            return parent, child

        match display_type:
            case "MIRRORED":
                for i in range(len(self.slots)):
                    if not self.slots[i].bone_name:
                        self.slots[i].bone_name = flip_name(self.slots[i - 1].bone_name)
            case "FINGER":
                for i in reversed(range(len(self.slots))):
                    if i < len(self.slots) - 1 and not self.slots[i].bone_name:
                        self.slots[i].bone_name = get_lineal(self.slots[i + 1].bone_name)[0]
                for i in range(len(self.slots)):
                    if i > 0 and not self.slots[i].bone_name:
                        self.slots[i].bone_name = get_lineal(self.slots[i - 1].bone_name)[1]

    name: bpy.props.StringProperty()
    mmd_j: bpy.props.StringProperty()
    mmd_e: bpy.props.StringProperty()
    frame_override: bpy.props.StringProperty()
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
    name_j: bpy.props.StringProperty()
    """actual name used for MMD DisplayFrame"""

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
            frame.name_j = frame_data["name_j"]
            frame.icon = frame_data["icon"]
            frame.category = frame_data["category"]
            frame.display_type = frame_data.get("display_type", "DEFAULT")

            for item_data in frame_data.get("items", []):
                item = frame.items.add()
                item.name = item_data["name"]
                item.mmd_j = item_data.get("mmd_j", "")
                item.mmd_e = item_data.get("mmd_e", "")
                item.frame_override = item_data.get("frame_override", "")

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

    def is_mmd_armature_object(self):
        if self.raw_object is None:
            return False

        if self.raw_object.type != "ARMATURE":
            return False

        if import_mmd_tools().core.model.FnModel.find_root_object(self.raw_object) is None:
            return False

        return True

    def create_bone_pos(self, name, collection, head, tail, parent=None, use_connect=False) -> bpy.types.EditBone:
        """Creates child bone based on head & tail position."""
        bone = self.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        if parent:
            bone.parent = parent
        bone.use_connect = use_connect
        if collection:
            collection.assign(bone)
        return bone

    def create_bone_vec(self, name, collection, length, parent) -> bpy.types.EditBone:
        """Creates child bone based on parent's orientation and length."""
        bone = self.edit_bones.new(name)
        bone.use_connect = True
        bone.parent = parent
        bone.align_orientation(parent)
        bone.length = length
        if collection:
            collection.assign(bone)
        return bone

    def to_mmd_pose(self, use_local=False, use_apose=False):
        """Convert bones to MMD. This function expects MMD naming convention."""

        def to_mmd_bone():
            """Locks positions of the bones and changes display connection to child bone."""
            for pbone in self.pose_bones:
                if pbone.name not in MMD_CONTROL:
                    pbone.lock_location = [True, True, True]
                    pbone.lock_rotation_w = False
                if len(pbone.children) == 1:
                    pbone.mmd_bone.display_connection_type = "BONE"
                    pbone.mmd_bone.display_connection_bone = pbone.children[0].name

        def is_tpose(tpose_angle: float = 5.0) -> bool:
            """Check if the model is in T-pose."""
            arm_vec = self.pose_bones["腕.L"].vector.normalized()
            angle = self.to_angle(arm_vec, "XZ")
            return math.degrees(abs(angle)) < tpose_angle

        def remove_deform():
            """Disables `use_deform` to exclude from Automatic Weights."""
            for bone in self.bones:
                if bone.name in MMD_CONTROL:
                    bone.use_deform = False

        def apply_local():
            """Adds local axis to arm bones."""
            bpy.ops.pose.select_all(action="DESELECT")
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

        def apply_fixed_axis():
            """Adds fixed axis to arm twist bones."""
            bpy.ops.pose.select_all(action="DESELECT")
            for bone in self.bone_collections["腕"].bones:
                if "捩" in bone.name:
                    pbone = self.pose_bones[bone.name]
                    pbone.select = True
                    pbone.mmd_bone.enabled_fixed_axis = True

            bpy.ops.mmd_tools.bone_fixed_axis_setup(type="LOAD")
            bpy.ops.mmd_tools.bone_fixed_axis_setup(type="APPLY")

        def create_root():
            """Create MMD center and root bone."""

            bpy.ops.object.mode_set(mode="EDIT")
            parent = self.edit_bones["下半身"].parent
            if parent is None or not math.isclose(parent.head.length, 0):
                parent = self.create_bone_pos("全ての親", None, (0.0, 0.0, 0.0), (0.0, 0.0, 0.7))
            else:
                parent.name = "全ての親"

            center = self.create_bone_pos("センター", None, (0.0, 0.0, 0.7), (0.0, 0.0, 0.0), parent)
            self.edit_bones["上半身"].use_connect = False
            self.edit_bones["下半身"].use_connect = False
            self.edit_bones["上半身"].parent = center
            self.edit_bones["下半身"].parent = center
            self.edit_bones["下半身"].tail = self.edit_bones["下半身"].head
            self.edit_bones["下半身"].head = self.edit_bones["上半身"].head

            bpy.ops.object.mode_set(mode="POSE")

        if not self.pose_bones.get("センター") or not self.pose_bones.get("全ての親"):
            create_root()

        if use_apose and is_tpose():
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
        apply_fixed_axis()
        if use_local:
            apply_local()

    def add_leg_ik(self):
        """Leg IK maker. Adapted from MMD Tools Helper"""

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

        # checks
        if self.pose_bones.get(LEG_IK_L) or self.pose_bones.get(LEG_IK_R):
            print("This armature already has Leg IK.")
            return
        if not self.pose_bones.get(ROOT) or not self.pose_bones.get(ANKLE_L) or not self.pose_bones.get(ANKLE_R):
            print("This armature does not have MMD bones.")
            return

        bpy.ops.object.mode_set(mode="POSE")

        add_ik_limit(self.pose_bones[KNEE_L])
        add_ik_limit(self.pose_bones[KNEE_R])

        # used for IK bone length
        FOOT_LENGTH = self.bones[ANKLE_L].length

        bpy.ops.object.mode_set(mode="EDIT")

        # move knees forward a little to prevent glitches
        if math.isclose(self.edit_bones["足.L"].vector.angle(self.edit_bones["ひざ.L"].vector), 0):
            self.edit_bones["足.L"].tail.y = -0.005
            self.edit_bones["足.R"].tail.y = -0.005

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
        self.get_or_create_bone_collection(self.bone_collections, "IK")
        self.bone_collections["IK"].assign(self.pose_bones[LEG_IK_L])
        self.bone_collections["IK"].assign(self.pose_bones[LEG_IK_R])
        self.bone_collections["IK"].assign(self.pose_bones[TOE_IK_L])
        self.bone_collections["IK"].assign(self.pose_bones[TOE_IK_R])

    def add_eyes_bone(self):
        """Adds 両目 bone to MMD rig."""

        HEAD = "頭"
        EYE_L = "目.L"
        EYE_R = "目.R"
        EYES = "両目"

        # checks
        if self.pose_bones.get(EYES):
            print("This armature already has eyes bone.")
            return
        if not self.pose_bones.get(EYE_L) or not self.pose_bones.get(EYE_R) or not self.pose_bones.get(HEAD):
            print("This armature does not have eye bones.")
            return

        bpy.ops.object.mode_set(mode="EDIT")
        bone = self.edit_bones.new(EYES)
        bone.head = self.edit_bones[HEAD].tail + Vector((0, 0, 0.2))
        bone.tail = bone.head + Vector((0, -0.05, 0))
        bone.parent = self.edit_bones[HEAD]

        bpy.ops.object.mode_set(mode="POSE")
        self.pose_bones[EYES].lock_location = [True, True, True]
        self.pose_bones[EYES].lock_rotation_w = False
        self.pose_bones[EYE_L].mmd_bone.additional_transform_bone = EYES
        self.pose_bones[EYE_R].mmd_bone.additional_transform_bone = EYES
        self.pose_bones[EYE_L].mmd_bone.has_additional_rotation = True
        self.pose_bones[EYE_R].mmd_bone.has_additional_rotation = True

        self.get_or_create_bone_collection(self.bone_collections, "体(上)")
        self.bone_collections["体(上)"].assign(self.pose_bones[EYES])

    def rename(self) -> int:
        count = 0

        LR_MAP_MMD = {0: "左", 1: "右"}
        LR_MAP_BLENDER = {0: ".L", 1: ".R"}
        HALF_FULL = str.maketrans("0123456789", "０１２３４５６７８９")

        for frame, item in self.tree.iter_items():
            col = self.get_or_create_bone_collection(self.bone_collections, frame.name_j)

            for idx, slot in enumerate(item.slots):
                if not slot.bone_name:
                    continue

                bone = self.edit_bones.get(slot.bone_name)
                if not bone:
                    continue

                pbone = self.pose_bones[slot.bone_name]
                original = bone.name
                target_j = item.mmd_j
                target_e = item.mmd_e

                match frame.display_type:
                    case "MIRRORED":
                        target_j = f"{LR_MAP_MMD.get(idx, '')}{target_j}"
                        if target_e:
                            target_e = f"{target_e}{LR_MAP_BLENDER.get(idx, '')}"
                    case "FINGER":
                        # 親指ならbaseから0, 1, 2 (全角)
                        init_n = 0 if item.name == "Thumb" else 1
                        target_j += str(idx + init_n).translate(HALF_FULL)
                        if target_e:
                            target_e += str(idx + init_n)

                # rename!
                bone.name = self.convert_mmd_prefix(target_j)
                pbone.mmd_bone.name_j = target_j
                if not pbone.mmd_bone.name_e:
                    pbone.mmd_bone.name_e = target_e or original

                if item.frame_override:
                    col = self.get_or_create_bone_collection(self.bone_collections, item.frame_override)
                    col.assign(bone)
                else:
                    col.assign(bone)

                # update
                slot.bone_name = bone.name
                count += 1

        return count

    def detect(self, finger_count: int = 5, precision: float = 0.0001):
        """
        Analyze the bone position, direction, structure and name to find Humanoid structure.
        Intended for non-MMD models, and the model must face Y- direction.
        """

        def isclose_abs(a: float, b: float, tol: float) -> bool:
            """Returns if the absolute values of a and b are close."""
            return math.isclose(abs(a), abs(b), abs_tol=tol)

        def isconnected(bone: bpy.types.EditBone, tol: float = precision) -> bool:
            """Check if bone.head is connected or in the same position as tail of the parent."""
            parent = bone.parent
            if parent:
                return bone.use_connect or (bone.head - parent.tail).length < tol
            return False

        def traverse_parent_chain(bone: bpy.types.EditBone, threshold: float = 0.6, chain: list[str] = None) -> list[str]:
            """
            Find connected parents that are pointing in a similar direction (bone chain).
            threshold = 1 means it will treat 90deg as part of the chain.
            """

            parent = bone.parent
            if not parent:
                return chain if chain else []

            if chain is None:
                chain = []

            angle = bone.vector.angle(parent.vector)
            if angle < math.pi * 0.5 * threshold:
                chain.append(parent.name)
                return traverse_parent_chain(parent, threshold=threshold, chain=chain)
            else:
                return chain

        # Gather bone data
        children_map = {b.name: [c.name for c in b.children] for b in self.bones if b.use_deform}
        bone_map: dict[str, dict[str, Vector]] = {
            b.name: {
                "head": b.head,
                "tail": b.tail,
                "vector": b.vector.normalized(),
                "connected": isconnected(b),
            }
            for b in self.edit_bones
            if b.use_deform
        }

        # find hand with finger count & furthest bone
        finger_parent = [k for k, v in children_map.items() if len(v) >= finger_count]
        if finger_parent:
            print(finger_parent)
            hand_pos = max(abs(bone_map[n]["head"].x) for n in finger_parent)
            hands = [n for n in finger_parent if isclose_abs(hand_pos, bone_map[n]["head"].x, precision)]
        print(hands)

        # find arm chains
        arm_l = []
        arm_r = []
        for h in hands:
            if bone_map[h]["head"].x > 0:
                arm_l = traverse_parent_chain(self.edit_bones[h], threshold=0.8)
            else:
                arm_r = traverse_parent_chain(self.edit_bones[h], threshold=0.8)
        print(arm_l, arm_r)

        # find toe by lowest & furthest bone
        min_z = min(v["head"].z for v in bone_map.values())
        bottom = [k for k, v in bone_map.items() if abs(v["head"].z - min_z) < precision]
        if bottom:
            toe_pos = max(abs(bone_map[n]["head"].y) for n in bottom)
            toes = [n for n in bottom if isclose_abs(toe_pos, bone_map[n]["head"].y, precision)]
        print(toes)

        # find leg chains (broken on MMD because EX and ToeIK)
        leg_l = []
        leg_r = []
        for t in toes:
            if bone_map[t]["head"].x > 0:
                leg_l = traverse_parent_chain(self.edit_bones[t], threshold=0.8)
            else:
                leg_r = traverse_parent_chain(self.edit_bones[t], threshold=0.8)
        print(leg_l, leg_r)

        # find head by top & upward bone (that is closer to root) わからん？？
        upward_bones = [v for v in bone_map.values() if v["vector"].z > 0.6]
        if upward_bones:
            max_z = max(v["tail"].z for v in upward_bones)
            head = [k for k, v in bone_map.items() if v["vector"].z > 0.6 and abs(v["tail"].z - max_z) < precision]
        print(head)

        print(traverse_parent_chain(self.edit_bones[head[0]]))
