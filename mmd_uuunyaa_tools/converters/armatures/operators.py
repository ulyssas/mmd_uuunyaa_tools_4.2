# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD UuuNyaa Tools.

from typing import Iterable, Optional, Tuple

import bpy

from mmd_uuunyaa_tools.converters.armatures import (
    AutoRigArmatureObject,
    MetarigArmatureObject,
    MMDArmatureObject,
    MMDRigifyArmatureObject,
    RigifyArmatureObject,
)
from mmd_uuunyaa_tools.m17n import _
from mmd_uuunyaa_tools.utilities import MessageException, import_mmd_tools


class MMDArmatureAddMetarig(bpy.types.Operator):
    bl_idname = "mmd_uuunyaa_tools.mmd_armature_add_metarig"
    bl_label = _("Add Human (metarig) from MMD Armature")
    bl_options = {"REGISTER", "UNDO"}

    is_clean_armature: bpy.props.BoolProperty(name=_("Clean Armature"), default=True)
    is_clean_koikatsu_armature: bpy.props.BoolProperty(name=_("Clean Koikatsu Armature"), default=False)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != "OBJECT":
            return False

        if len(context.selected_objects) != 1:
            return False

        return MMDArmatureObject.is_mmd_armature_object(context.active_object)

    def _create_metarig_object(self) -> bpy.types.Object:
        original_cursor_location = bpy.context.scene.cursor.location
        try:
            # Rigifyのメタリグはどこに置いたとしても、
            # 生成ボタンをおすと(0, 0, 0)にRigifyArmatureが生成される。
            # よってメタリグも(0, 0, 0)に生成するようにする。
            bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
            bpy.ops.object.armature_human_metarig_add()
            return bpy.context.object
        except AttributeError as ex:
            if str(ex) != 'Calling operator "bpy.ops.object.armature_human_metarig_add" error, could not be found':
                raise
            raise MessageException(_("Failed to invoke Rigify\nPlease enable Rigify add-on.")) from None
        finally:
            bpy.context.scene.cursor.location = original_cursor_location

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context: bpy.types.Context):
        mmd_object = context.active_object

        try:
            metarig_object = MetarigArmatureObject(self._create_metarig_object())
        except MessageException as ex:
            self.report(type={"ERROR"}, message=str(ex))
            return {"CANCELLED"}

        mmd_armature_object = MMDArmatureObject(mmd_object)
        metarig_object.fit_scale(mmd_armature_object)

        mmd_object.select = True
        metarig_object.select = True

        if self.is_clean_koikatsu_armature:
            mmd_armature_object.clean_koikatsu_armature_prepare()
            mmd_armature_object = MMDArmatureObject(mmd_object)

        bpy.ops.object.mode_set(mode="EDIT")

        if self.is_clean_koikatsu_armature:
            mmd_armature_object.clean_koikatsu_armature()

        if self.is_clean_armature:
            mmd_armature_object.clean_armature()

        if not mmd_armature_object.has_face_bones():
            metarig_object.remove_face_bones()

        metarig_object.fit_bones(mmd_armature_object)

        bpy.ops.object.mode_set(mode="POSE")
        metarig_object.set_rigify_parameters(mmd_armature_object)

        bpy.ops.object.mode_set(mode="OBJECT")

        return {"FINISHED"}


class MMDRigifyOperatorABC:
    @classmethod
    def find_armature_objects(
        cls, objects: Iterable[bpy.types.Object]
    ) -> Tuple[Optional[bpy.types.Object], Optional[bpy.types.Object]]:
        mmd_tools = import_mmd_tools()

        rigify_object: Optional[bpy.types.Object] = None
        mmd_object: Optional[bpy.types.Object] = None

        for obj in objects:
            if obj.type != "ARMATURE":
                continue

            if "rig_id" in obj.data:
                rigify_object = obj
                continue

            mmd_root = mmd_tools.core.model.FnModel.find_root_object(obj)
            if mmd_root is not None:
                mmd_object = obj
                continue

        return (rigify_object, mmd_object)

    @classmethod
    def poll(cls, context: bpy.types.Context):
        if context.mode != "OBJECT":
            return False

        selected_objects = bpy.context.selected_objects
        if len(selected_objects) != 2:
            return False

        rigify_armature_object, mmd_armature_object = cls.find_armature_objects(selected_objects)

        return rigify_armature_object is not None and mmd_armature_object is not None

    @staticmethod
    def adjust_bone_groups(rigify_armature_object: RigifyArmatureObject, mmd_armature_object: MMDArmatureObject):
        # copy bone groups Rigify -> MMD
        rig_bone_collections = rigify_armature_object.bone_collections
        mmd_bone_collections = mmd_armature_object.bone_collections
        for rig_bone_collection_name in rig_bone_collections.keys():
            if rig_bone_collection_name in mmd_bone_collections:
                continue
            mmd_bone_collections.new(name=rig_bone_collection_name)

        # copy bone groups MMD -> Rigify
        diff_bone_group_names = set(mmd_bone_collections.keys()) - set(rig_bone_collections.keys())
        for mmd_bone_group_name in diff_bone_group_names:
            mmd_bone_collections[mmd_bone_group_name]
            rig_bone_collections.new(name=mmd_bone_group_name)
            

    @staticmethod
    def join_armatures(
        rigify_armature_object: RigifyArmatureObject,
        mmd_armature_object: MMDArmatureObject
    ):
        mmd_armature = mmd_armature_object.raw_armature
    #    mmd_armature.layers = [
    #        i in {0, 8, 9, 23, mmd_main_bone_layer, mmd_others_bone_layer, mmd_shadow_bone_layer, mmd_dummy_bone_layer}
    #        for i in range(32)
    #    ]

        mmd_bind_bones = mmd_armature_object.exist_actual_bone_names

        for bone in mmd_armature.bones:
            if "mmd_shadow" in bone.collections.keys():
                for coll in bone.collections:
                    if coll.name != "mmd_shadow":
                        coll.unassign(bone)

            elif "mmd_dummy" in bone.collections.keys():
                for coll in bone.collections:
                    if coll.name != "mmd_dummy":
                        coll.unassign(bone)
            #At this point, either a "Main" or "Other" bone. Only add to collection if "Other", since there is no "Main" collection.
            elif bone.name not in mmd_bind_bones:
                mmd_armature.collections["その他"].assign(bone)

        # join armatures
        rigify_armature: bpy.types.Armature = rigify_armature_object.raw_armature
        rig_collection_names = rigify_armature.collections.keys()
        rig_id = rigify_armature["rig_id"]

        bpy.context.view_layer.objects.active = mmd_armature_object.raw_object
        bpy.ops.object.join()
        #Verify collections in MMD_Armature and Rigify_Armature correspond...
        #for name in rig_collection_names not in mmd_armature.collections.keys():
        #    mmd_armature.collections.new(name)
        #mmd_armature["rig_id"] = rig_id
        mmd_armature_object.raw_object.display_type = "WIRE"

        #Hide all bones not in the MMD Other collection
        for collection in mmd_armature.collections:
            collection.is_visible = False
        mmd_armature.collections["その他"].is_visible = True

        mmd_armature_object.raw_object.show_in_front = True

    def invoke(self, context, _):
        return context.window_manager.invoke_props_dialog(self)


class MMDRigifyIntegrateFocusOnMMD(MMDRigifyOperatorABC, bpy.types.Operator):
    bl_idname = "mmd_uuunyaa_tools.mmd_rigify_mmd_focused_integrate"
    bl_label = _("MMD compatibility focused Integrate")
    bl_options = {"REGISTER", "UNDO"}

    is_join_armatures: bpy.props.BoolProperty(
        name=_("Join Armatures"), description=_("Join MMD and Rigify armatures"), default=True
    )
    mmd_main_bone_layer: bpy.props.IntProperty(name=_("MMD main bone layer"), default=24, min=0, max=31)
    mmd_others_bone_layer: bpy.props.IntProperty(name=_("MMD others bone layer"), default=25, min=0, max=31)
    mmd_shadow_bone_layer: bpy.props.IntProperty(name=_("MMD shadow bone layer"), default=26, min=0, max=31)
    mmd_dummy_bone_layer: bpy.props.IntProperty(name=_("MMD dummy bone layer"), default=27, min=0, max=31)

    @staticmethod
    def set_view_layers(rigify_armature_object: bpy.types.Object):
        rig_armature: bpy.types.Armature = rigify_armature_object.raw_armature
        #rig_armature.layers = [i in {0, 3, 4, 5, 8, 11, 13, 16, 28} for i in range(32)]
        for bone_col in rig_armature.collections:
            if bone_col.name not in {"mmd_shadow", "mmd_dummy"}:
                bone_col.is_visible = True
        

    def execute(self, context: bpy.types.Context):
        rigify_armature_raw_object, mmd_armature_raw_object = self.find_armature_objects(context.selected_objects)

        rigify_armature_object = MMDRigifyArmatureObject(rigify_armature_raw_object)
        mmd_armature_object = MMDArmatureObject(mmd_armature_raw_object)

        #self.change_mmd_bone_layer(mmd_armature_object)

        bpy.ops.object.mode_set(mode="EDIT")
        rigify_armature_object.remove_unused_face_bones()
        rigify_armature_object.fit_bone_rotations(mmd_armature_object)
        rigify_armature_object.imitate_mmd_bone_structure_focus_on_mmd(mmd_armature_object)

        bpy.ops.object.mode_set(mode="POSE")
        rigify_armature_object.imitate_mmd_pose_behavior_focus_on_mmd()
        rigify_armature_object.bind_bones(mmd_armature_object)

        bpy.ops.object.mode_set(mode="OBJECT")
        self.set_view_layers(rigify_armature_object)

        if self.is_join_armatures:
            self.adjust_bone_groups(rigify_armature_object, mmd_armature_object)
            self.join_armatures(
                rigify_armature_object,
                mmd_armature_object
            )
            rigify_armature_object = MMDRigifyArmatureObject(mmd_armature_raw_object)

        rigify_armature_object.assign_mmd_bone_names()

        return {"FINISHED"}


class MMDRigifyIntegrateFocusOnRigify(bpy.types.Operator, MMDRigifyOperatorABC):
    bl_idname = "mmd_uuunyaa_tools.mmd_rigify_rigify_focused_integrate"
    bl_label = _("Rigify operability focused Integrate")
    bl_options = {"REGISTER", "UNDO"}

    is_join_armatures: bpy.props.BoolProperty(
        name=_("Join Armatures"), description=_("Join MMD and Rigify armatures"), default=True
    )
    mmd_main_bone_layer: bpy.props.IntProperty(name=_("MMD main bone layer"), default=24, min=0, max=31)
    mmd_others_bone_layer: bpy.props.IntProperty(name=_("MMD others bone layer"), default=25, min=0, max=31)
    mmd_shadow_bone_layer: bpy.props.IntProperty(name=_("MMD shadow bone layer"), default=26, min=0, max=31)
    mmd_dummy_bone_layer: bpy.props.IntProperty(name=_("MMD dummy bone layer"), default=27, min=0, max=31)
    rename_mmd_bones: bpy.props.BoolProperty(name=_("Rename MMD bones"), default=False)

    @staticmethod
    def set_view_layers(rigify_armature_object: bpy.types.Object):
        rig_armature: bpy.types.Armature = rigify_armature_object.raw_armature
        #rig_armature.layers = [i in {0, 3, 5, 7, 10, 13, 16, 28} for i in range(32)]
        for collection in rig_armature.collections:
            if collection.name in {"Face", "Torso", "Fingers", "Arm.L (IK)", "Arm.R (IK)", "Leg.L (IK)", "Leg.R (IK)", "Root"}:
                collection.is_visible = True
            else:
                collection.is_visible = False

    def execute(self, context: bpy.types.Context):
        rigify_armature_raw_object, mmd_armature_raw_object = self.find_armature_objects(context.selected_objects)

        rigify_armature_object = MMDRigifyArmatureObject(rigify_armature_raw_object)
        mmd_armature_object = MMDArmatureObject(mmd_armature_raw_object)

        #self.change_mmd_bone_layer(mmd_armature_object)

        bpy.ops.object.mode_set(mode="EDIT")
        rigify_armature_object.remove_unused_face_bones()
        rigify_armature_object.fit_bone_rotations(mmd_armature_object)
        rigify_armature_object.imitate_mmd_bone_structure_focus_on_rigify(mmd_armature_object)

        bpy.ops.object.mode_set(mode="POSE")
        rigify_armature_object.imitate_mmd_pose_behavior_focus_on_rigify()
        rigify_armature_object.bind_bones(mmd_armature_object)

        bpy.ops.object.mode_set(mode="OBJECT")
        self.set_view_layers(rigify_armature_object)

        if self.is_join_armatures:
            self.adjust_bone_groups(rigify_armature_object, mmd_armature_object)
            self.join_armatures(
                rigify_armature_object,
                mmd_armature_object,
            #    self.mmd_main_bone_layer,
            #    self.mmd_others_bone_layer,
            #    self.mmd_shadow_bone_layer,
            #    self.mmd_dummy_bone_layer,
            )
            rigify_armature_object = MMDRigifyArmatureObject(mmd_armature_raw_object)

        if self.rename_mmd_bones:
            rigify_armature_object.assign_mmd_bone_names()

        return {"FINISHED"}


class MMDRigifyConvert(bpy.types.Operator):
    bl_idname = "mmd_uuunyaa_tools.rigify_to_mmd_compatible"
    bl_label = _("Convert Rigify Armature to MMD compatible")
    bl_options = {"REGISTER", "UNDO"}

    upper_body2_bind_bone: bpy.props.EnumProperty(
        name=_("Upper Body2 as"),
        items=[
            ("spine_fk.002", "spine_fk.002", ""),
            ("spine_fk.003", "spine_fk.003", ""),
            ("chest", "chest", ""),
        ],
        default="spine_fk.002",
    )

    lower_body_bind_bone: bpy.props.EnumProperty(
        name=_("Lower Body as"),
        items=[
            ("spine_fk", "spine_fk", ""),
            ("hips", "hips", ""),
        ],
        default="spine_fk",
    )

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT":
            return False

        active_object = context.active_object

        return RigifyArmatureObject.is_rigify_armature_object(
            active_object
        ) and not MMDRigifyArmatureObject.is_mmd_integrated_object(active_object)

    def execute(self, context: bpy.types.Context):
        rigify_armature_object = RigifyArmatureObject(context.active_object)

        bpy.ops.object.mode_set(mode="EDIT")
        rigify_armature_object.imitate_mmd_bone_structure()

        bpy.ops.object.mode_set(mode="POSE")
        rigify_armature_object.imitate_mmd_pose_behavior()

        bpy.ops.object.mode_set(mode="OBJECT")
        rigify_armature_object.assign_mmd_bone_names(
            mmd2pose_bone_name_overrides={
                "上半身2": self.upper_body2_bind_bone,
                "下半身": self.lower_body_bind_bone,
            }
        )
        return {"FINISHED"}


class MMDRigifyApplyMMDRestPose(bpy.types.Operator):
    bl_idname = "mmd_uuunyaa_tools.rigify_apply_mmd_rest_pose"
    bl_label = _("Apply MMD Rest Pose")
    bl_options = {"REGISTER", "UNDO"}

    iterations: bpy.props.IntProperty(
        name=_("Iterations"), description=_("Number of solving iterations"), default=7, min=1, max=100
    )
    pose_arms: bpy.props.BoolProperty(name=_("Pose arms"), default=True)
    pose_legs: bpy.props.BoolProperty(name=_("Pose legs"), default=True)
    pose_fingers: bpy.props.BoolProperty(name=_("Pose fingers"), default=False)

    @classmethod
    def poll(cls, context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        return RigifyArmatureObject.is_rigify_armature_object(active_object)

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            rigify_armature_object = RigifyArmatureObject(context.active_object)
            dependency_graph = context.evaluated_depsgraph_get()

            bpy.ops.object.mode_set(mode="POSE")
            rigify_armature_object.pose_mmd_rest(
                dependency_graph,
                self.iterations,
                pose_arms=self.pose_arms,
                pose_legs=self.pose_legs,
                pose_fingers=self.pose_fingers,
            )

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}


class MMDAutoRigConvert(bpy.types.Operator):
    bl_idname = "mmd_uuunyaa_tools.autorig_to_mmd_compatible"
    bl_label = _("Convert AutoRig Armature to MMD compatible")
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        if context.mode != "OBJECT":
            return False

        active_object = context.active_object

        return AutoRigArmatureObject.is_autorig_armature_object(active_object)

    def execute(self, context: bpy.types.Context):
        autorig_armature_object = AutoRigArmatureObject(context.active_object)

        bpy.ops.object.mode_set(mode="EDIT")
        autorig_armature_object.imitate_mmd_bone_structure()

        bpy.ops.object.mode_set(mode="POSE")
        autorig_armature_object.imitate_mmd_pose_behavior()

        bpy.ops.object.mode_set(mode="OBJECT")
        autorig_armature_object.assign_mmd_bone_names()
        return {"FINISHED"}


class MMDAutoRigApplyMMDRestPose(bpy.types.Operator):
    bl_idname = "mmd_uuunyaa_tools.autorig_apply_mmd_rest_pose"
    bl_label = _("Apply MMD Rest Pose")
    bl_options = {"REGISTER", "UNDO"}

    iterations: bpy.props.IntProperty(
        name=_("Iterations"), description=_("Number of solving iterations"), default=7, min=1, max=100
    )
    pose_arms: bpy.props.BoolProperty(name=_("Pose arms"), default=True)
    pose_legs: bpy.props.BoolProperty(name=_("Pose legs"), default=True)
    pose_fingers: bpy.props.BoolProperty(name=_("Pose fingers"), default=False)

    @classmethod
    def poll(cls, context):
        if context.mode not in {"OBJECT", "POSE"}:
            return False

        active_object = context.active_object

        return AutoRigArmatureObject.is_autorig_armature_object(active_object)

    def execute(self, context: bpy.types.Context):
        previous_mode = context.mode

        try:
            rigify_armature_object = AutoRigArmatureObject(context.active_object)
            dependency_graph = context.evaluated_depsgraph_get()

            bpy.ops.object.mode_set(mode="POSE")
            rigify_armature_object.pose_mmd_rest(
                dependency_graph,
                self.iterations,
                pose_arms=self.pose_arms,
                pose_legs=self.pose_legs,
                pose_fingers=self.pose_fingers,
            )

        finally:
            bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}
