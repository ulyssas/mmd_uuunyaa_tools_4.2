# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import math

import bpy
from mathutils import Vector

from ...editors.armatures import ArmatureEditor
from .mmd import MMDArmatureObject, MMDBoneType


class MetarigArmatureObject(ArmatureEditor):
    def fit_scale(self, mmd_armature_object: MMDArmatureObject):
        rigify_height = self.bones["spine.004"].head_local[2]
        mmd_height = mmd_armature_object.strict_bones["首"].head_local[2]

        scale = mmd_height / rigify_height
        self.raw_object.scale = (scale, scale, scale)
        bpy.ops.object.transform_apply(scale=True)

    def remove_face_bones(self):
        metarig_edit_bones = self.edit_bones
        metarig_face_bone = metarig_edit_bones["face"]
        for bone in metarig_face_bone.children_recursive:
            metarig_edit_bones.remove(bone)

        metarig_edit_bones.remove(metarig_face_bone)

    def fit_bones(self, mmd_armature_object: MMDArmatureObject, use_mmd_orientation: bool = True):
        # pylint: disable=too-many-statements
        metarig_edit_bones = self.edit_bones
        mmd_edit_bones = mmd_armature_object.strict_edit_bones
        metarig_edit_bones["spine.002"].head = mmd_edit_bones["上半身"].head

        if MMDBoneType.UPPER_BODY_2 in mmd_armature_object.exist_bone_types:
            metarig_edit_bones["spine.003"].head = mmd_edit_bones["上半身2"].head
            metarig_edit_bones["spine.003"].tail = mmd_edit_bones["上半身2"].tail
        else:
            metarig_edit_bones["spine.003"].head = self.to_bone_center(mmd_edit_bones["上半身"])
            metarig_edit_bones["spine.003"].tail = mmd_edit_bones["上半身"].tail

        metarig_edit_bones["spine.004"].head = mmd_edit_bones["首"].head
        metarig_edit_bones["spine.004"].tail = self.to_bone_center(mmd_edit_bones["首"])
        metarig_edit_bones["spine.005"].tail = mmd_edit_bones["首"].tail
        metarig_edit_bones["spine.006"].tail = mmd_edit_bones["頭"].tail

        if mmd_armature_object.has_face_bones():
            metarig_edit_bones["face"].head = mmd_edit_bones["頭"].head
            metarig_edit_bones["face"].tail = self.to_bone_center(mmd_edit_bones["頭"])

        metarig_edit_bones["shoulder.L"].head = mmd_edit_bones["左肩"].head
        metarig_edit_bones["shoulder.L"].tail = mmd_edit_bones["左肩"].tail
        metarig_edit_bones["shoulder.R"].head = mmd_edit_bones["右肩"].head
        metarig_edit_bones["shoulder.R"].tail = mmd_edit_bones["右肩"].tail
        metarig_edit_bones["upper_arm.L"].head = mmd_edit_bones["左腕"].head
        metarig_edit_bones["upper_arm.R"].head = mmd_edit_bones["右腕"].head
        metarig_edit_bones["forearm.L"].head = mmd_edit_bones["左ひじ"].head
        metarig_edit_bones["forearm.L"].tail = mmd_edit_bones["左ひじ"].tail
        metarig_edit_bones["forearm.R"].head = mmd_edit_bones["右ひじ"].head
        metarig_edit_bones["forearm.R"].tail = mmd_edit_bones["右ひじ"].tail
        metarig_edit_bones["hand.L"].tail = mmd_edit_bones["左手首"].tail
        metarig_edit_bones["hand.R"].tail = mmd_edit_bones["右手首"].tail

        if use_mmd_orientation:
            metarig_edit_bones["upper_arm.L"].roll = mmd_edit_bones["左腕"].roll + math.radians(+90)
            metarig_edit_bones["upper_arm.R"].roll = mmd_edit_bones["右腕"].roll + math.radians(+90)
            metarig_edit_bones["forearm.L"].roll = mmd_edit_bones["左ひじ"].roll + math.radians(+90)
            metarig_edit_bones["forearm.R"].roll = mmd_edit_bones["右ひじ"].roll + math.radians(+90)
            metarig_edit_bones["hand.L"].roll = mmd_edit_bones["左手首"].roll + math.radians(+90)
            metarig_edit_bones["hand.R"].roll = mmd_edit_bones["右手首"].roll + math.radians(+90)

        if MMDBoneType.THUMB_0 in mmd_armature_object.exist_bone_types:
            metarig_edit_bones["thumb.01.L"].head = mmd_edit_bones["左親指０"].head
            metarig_edit_bones["thumb.01.L"].tail = mmd_edit_bones["左親指０"].tail
            metarig_edit_bones["thumb.01.R"].head = mmd_edit_bones["右親指０"].head
            metarig_edit_bones["thumb.01.R"].tail = mmd_edit_bones["右親指０"].tail
        else:
            metarig_edit_bones["thumb.01.L"].head = mmd_edit_bones["左親指１"].head - mmd_edit_bones["左親指１"].vector
            metarig_edit_bones["thumb.01.L"].tail = mmd_edit_bones["左親指１"].head
            metarig_edit_bones["thumb.01.R"].head = mmd_edit_bones["右親指１"].head - mmd_edit_bones["右親指１"].vector
            metarig_edit_bones["thumb.01.R"].tail = mmd_edit_bones["右親指１"].head

        metarig_edit_bones["thumb.02.L"].tail = mmd_edit_bones["左親指１"].tail
        metarig_edit_bones["thumb.02.R"].tail = mmd_edit_bones["右親指１"].tail
        metarig_edit_bones["thumb.03.L"].tail = mmd_edit_bones["左親指２"].tail
        metarig_edit_bones["thumb.03.R"].tail = mmd_edit_bones["右親指２"].tail

        if "左人指０" in mmd_edit_bones:
            metarig_edit_bones["palm.01.L"].head = mmd_edit_bones["左人指０"].head
            metarig_edit_bones["palm.01.L"].tail = mmd_edit_bones["左人指０"].tail
        else:
            metarig_edit_bones["palm.01.L"].head = self.to_stretch(mmd_edit_bones["左ひじ"].tail, mmd_edit_bones["左人指１"].head, 0.99)
            metarig_edit_bones["palm.01.L"].tail = mmd_edit_bones["左人指１"].head

        if "右人指０" in mmd_edit_bones:
            metarig_edit_bones["palm.01.R"].head = mmd_edit_bones["右人指０"].head
            metarig_edit_bones["palm.01.R"].tail = mmd_edit_bones["右人指０"].tail
        else:
            metarig_edit_bones["palm.01.R"].head = self.to_stretch(mmd_edit_bones["右ひじ"].tail, mmd_edit_bones["右人指１"].head, 0.99)
            metarig_edit_bones["palm.01.R"].tail = mmd_edit_bones["右人指１"].head

        metarig_edit_bones["f_index.01.L"].head = mmd_edit_bones["左人指１"].head
        metarig_edit_bones["f_index.01.L"].tail = mmd_edit_bones["左人指１"].tail
        metarig_edit_bones["f_index.01.R"].head = mmd_edit_bones["右人指１"].head
        metarig_edit_bones["f_index.01.R"].tail = mmd_edit_bones["右人指１"].tail
        metarig_edit_bones["f_index.02.L"].tail = mmd_edit_bones["左人指２"].tail
        metarig_edit_bones["f_index.02.R"].tail = mmd_edit_bones["右人指２"].tail
        metarig_edit_bones["f_index.03.L"].tail = mmd_edit_bones["左人指３"].tail
        metarig_edit_bones["f_index.03.R"].tail = mmd_edit_bones["右人指３"].tail

        if "左中指０" in mmd_edit_bones:
            metarig_edit_bones["palm.02.L"].head = mmd_edit_bones["左中指０"].head
            metarig_edit_bones["palm.02.L"].tail = mmd_edit_bones["左中指０"].tail
        else:
            metarig_edit_bones["palm.02.L"].head = self.to_stretch(mmd_edit_bones["左ひじ"].tail, mmd_edit_bones["左中指１"].head, 0.99)
            metarig_edit_bones["palm.02.L"].tail = mmd_edit_bones["左中指１"].head

        if "右中指０" in mmd_edit_bones:
            metarig_edit_bones["palm.02.R"].head = mmd_edit_bones["右中指０"].head
            metarig_edit_bones["palm.02.R"].tail = mmd_edit_bones["右中指０"].tail
        else:
            metarig_edit_bones["palm.02.R"].head = self.to_stretch(mmd_edit_bones["右ひじ"].tail, mmd_edit_bones["右中指１"].head, 0.99)
            metarig_edit_bones["palm.02.R"].tail = mmd_edit_bones["右中指１"].head

        metarig_edit_bones["f_middle.01.L"].head = mmd_edit_bones["左中指１"].head
        metarig_edit_bones["f_middle.01.L"].tail = mmd_edit_bones["左中指１"].tail
        metarig_edit_bones["f_middle.01.R"].head = mmd_edit_bones["右中指１"].head
        metarig_edit_bones["f_middle.01.R"].tail = mmd_edit_bones["右中指１"].tail
        metarig_edit_bones["f_middle.02.L"].tail = mmd_edit_bones["左中指２"].tail
        metarig_edit_bones["f_middle.02.R"].tail = mmd_edit_bones["右中指２"].tail
        metarig_edit_bones["f_middle.03.L"].tail = mmd_edit_bones["左中指３"].tail
        metarig_edit_bones["f_middle.03.R"].tail = mmd_edit_bones["右中指３"].tail

        if "左薬指０" in mmd_edit_bones:
            metarig_edit_bones["palm.03.L"].head = mmd_edit_bones["左薬指０"].head
            metarig_edit_bones["palm.03.L"].tail = mmd_edit_bones["左薬指０"].tail
        else:
            metarig_edit_bones["palm.03.L"].head = self.to_stretch(mmd_edit_bones["左ひじ"].tail, mmd_edit_bones["左薬指１"].head, 0.99)
            metarig_edit_bones["palm.03.L"].tail = mmd_edit_bones["左薬指１"].head

        if "右薬指０" in mmd_edit_bones:
            metarig_edit_bones["palm.03.R"].head = mmd_edit_bones["右薬指０"].head
            metarig_edit_bones["palm.03.R"].tail = mmd_edit_bones["右薬指０"].tail
        else:
            metarig_edit_bones["palm.03.R"].head = self.to_stretch(mmd_edit_bones["右ひじ"].tail, mmd_edit_bones["右薬指１"].head, 0.99)
            metarig_edit_bones["palm.03.R"].tail = mmd_edit_bones["右薬指１"].head

        metarig_edit_bones["f_ring.01.L"].head = mmd_edit_bones["左薬指１"].head
        metarig_edit_bones["f_ring.01.L"].tail = mmd_edit_bones["左薬指１"].tail
        metarig_edit_bones["f_ring.01.R"].head = mmd_edit_bones["右薬指１"].head
        metarig_edit_bones["f_ring.01.R"].tail = mmd_edit_bones["右薬指１"].tail
        metarig_edit_bones["f_ring.02.L"].tail = mmd_edit_bones["左薬指２"].tail
        metarig_edit_bones["f_ring.02.R"].tail = mmd_edit_bones["右薬指２"].tail
        metarig_edit_bones["f_ring.03.L"].tail = mmd_edit_bones["左薬指３"].tail
        metarig_edit_bones["f_ring.03.R"].tail = mmd_edit_bones["右薬指３"].tail

        if "左小指０" in mmd_edit_bones:
            metarig_edit_bones["palm.04.L"].head = mmd_edit_bones["左小指０"].head
            metarig_edit_bones["palm.04.L"].tail = mmd_edit_bones["左小指０"].tail
        else:
            metarig_edit_bones["palm.04.L"].head = self.to_stretch(mmd_edit_bones["左ひじ"].tail, mmd_edit_bones["左小指１"].head, 0.99)
            metarig_edit_bones["palm.04.L"].tail = mmd_edit_bones["左小指１"].head

        if "右小指０" in mmd_edit_bones:
            metarig_edit_bones["palm.04.R"].head = mmd_edit_bones["右小指０"].head
            metarig_edit_bones["palm.04.R"].tail = mmd_edit_bones["右小指０"].tail
        else:
            metarig_edit_bones["palm.04.R"].head = self.to_stretch(mmd_edit_bones["右ひじ"].tail, mmd_edit_bones["右小指１"].head, 0.99)
            metarig_edit_bones["palm.04.R"].tail = mmd_edit_bones["右小指１"].head

        metarig_edit_bones["f_pinky.01.L"].head = mmd_edit_bones["左小指１"].head
        metarig_edit_bones["f_pinky.01.L"].tail = mmd_edit_bones["左小指１"].tail
        metarig_edit_bones["f_pinky.01.R"].head = mmd_edit_bones["右小指１"].head
        metarig_edit_bones["f_pinky.01.R"].tail = mmd_edit_bones["右小指１"].tail
        metarig_edit_bones["f_pinky.02.L"].tail = mmd_edit_bones["左小指２"].tail
        metarig_edit_bones["f_pinky.02.R"].tail = mmd_edit_bones["右小指２"].tail
        metarig_edit_bones["f_pinky.03.L"].tail = mmd_edit_bones["左小指３"].tail
        metarig_edit_bones["f_pinky.03.R"].tail = mmd_edit_bones["右小指３"].tail

        metarig_edit_bones["spine"].head = mmd_edit_bones["下半身"].tail
        metarig_edit_bones["spine.001"].head = self.to_bone_center(mmd_edit_bones["下半身"])
        metarig_edit_bones["spine.001"].tail = mmd_edit_bones["下半身"].head

        metarig_edit_bones["pelvis.L"].head = mmd_edit_bones["下半身"].tail
        metarig_edit_bones["pelvis.R"].head = mmd_edit_bones["下半身"].tail
        metarig_edit_bones["pelvis.L"].tail[1:3] = [
            mmd_edit_bones["下半身"].tail[1] - mmd_edit_bones["下半身"].length / 2,
            mmd_edit_bones["下半身"].head[2],
        ]
        metarig_edit_bones["pelvis.R"].tail[1:3] = [
            mmd_edit_bones["下半身"].tail[1] - mmd_edit_bones["下半身"].length / 2,
            mmd_edit_bones["下半身"].head[2],
        ]

        metarig_edit_bones["thigh.L"].head = mmd_edit_bones["左足"].head
        metarig_edit_bones["thigh.L"].tail = mmd_edit_bones["左足"].tail
        metarig_edit_bones["thigh.R"].head = mmd_edit_bones["右足"].head
        metarig_edit_bones["thigh.R"].tail = mmd_edit_bones["右足"].tail
        metarig_edit_bones["shin.L"].tail = mmd_edit_bones["左ひざ"].tail
        metarig_edit_bones["shin.R"].tail = mmd_edit_bones["右ひざ"].tail

        if MMDBoneType.TOE_EX in mmd_armature_object.exist_bone_types:
            toe_ex_l = mmd_edit_bones["左足先EX"]
            toe_ex_r = mmd_edit_bones["右足先EX"]

            # snap to the TOE_EX completely.
            metarig_edit_bones["foot.L"].tail = toe_ex_l.head
            metarig_edit_bones["foot.R"].tail = toe_ex_r.head

            # makes sure toe goes forward (-Y)
            toe_l_length = toe_ex_l.length if toe_ex_l.length else 0.07
            toe_r_length = toe_ex_r.length if toe_ex_r.length else 0.07
            metarig_edit_bones["toe.L"].tail = Vector(
                [
                    toe_ex_l.head.x,
                    toe_ex_l.head.y - toe_l_length,
                    toe_ex_l.head.z,
                ]
            )
            metarig_edit_bones["toe.R"].tail = Vector(
                [
                    toe_ex_r.head.x,
                    toe_ex_r.head.y - toe_r_length,
                    toe_ex_r.head.z,
                ]
            )

        else:
            metarig_edit_bones["foot.L"].tail = mmd_edit_bones["左足首"].tail
            metarig_edit_bones["foot.R"].tail = mmd_edit_bones["右足首"].tail
            metarig_edit_bones["toe.L"].tail = mmd_edit_bones["左足首"].tail + Vector([+0.0, -mmd_edit_bones["左足首"].length / 2, +0.0])
            metarig_edit_bones["toe.R"].tail = mmd_edit_bones["右足首"].tail + Vector([+0.0, -mmd_edit_bones["右足首"].length / 2, +0.0])

        metarig_edit_bones["heel.02.L"].tail = mmd_edit_bones["左ひざ"].tail.copy()
        metarig_edit_bones["heel.02.L"].tail[0] += +mmd_edit_bones["左ひざ"].length / 8
        metarig_edit_bones["heel.02.L"].tail[1] += +mmd_edit_bones["左ひざ"].length / 10
        metarig_edit_bones["heel.02.L"].tail[2] = 0
        metarig_edit_bones["heel.02.L"].head = mmd_edit_bones["左ひざ"].tail.copy()
        metarig_edit_bones["heel.02.L"].head[0] += -mmd_edit_bones["左ひざ"].length / 8
        metarig_edit_bones["heel.02.L"].head[1] += +mmd_edit_bones["左ひざ"].length / 10
        metarig_edit_bones["heel.02.L"].head[2] = 0
        metarig_edit_bones["heel.02.R"].tail = mmd_edit_bones["右ひざ"].tail.copy()
        metarig_edit_bones["heel.02.R"].tail[0] += -mmd_edit_bones["右ひざ"].length / 8
        metarig_edit_bones["heel.02.R"].tail[1] += +mmd_edit_bones["右ひざ"].length / 10
        metarig_edit_bones["heel.02.R"].tail[2] = 0
        metarig_edit_bones["heel.02.R"].head = mmd_edit_bones["右ひざ"].tail.copy()
        metarig_edit_bones["heel.02.R"].head[0] += +mmd_edit_bones["右ひざ"].length / 8
        metarig_edit_bones["heel.02.R"].head[1] += +mmd_edit_bones["右ひざ"].length / 10
        metarig_edit_bones["heel.02.R"].head[2] = 0

        # fix straight finger bend problem
        # https://blenderartists.org/t/rigify-fingers-issue/1218987
        # limbs.super_finger
        if use_mmd_orientation:

            def add_finger_zero_roll(metarig, mmd, amount):
                """Adds roll to finger 0 if it exists. Otherwise it adds roll to finger 1."""
                source_bone = mmd_edit_bones.get(f"{mmd}０") or mmd_edit_bones[f"{mmd}１"]
                metarig_edit_bones[metarig].roll = source_bone.roll + math.radians(amount)

            add_finger_zero_roll("thumb.01.L", "左親指", -90)
            add_finger_zero_roll("palm.01.L", "左人指", +180)
            add_finger_zero_roll("palm.02.L", "左中指", +180)
            add_finger_zero_roll("palm.03.L", "左薬指", +180)
            add_finger_zero_roll("palm.04.L", "左小指", +180)

            add_finger_zero_roll("thumb.01.R", "右親指", -90)
            add_finger_zero_roll("palm.01.R", "右人指", +0)
            add_finger_zero_roll("palm.02.R", "右中指", +0)
            add_finger_zero_roll("palm.03.R", "右薬指", +0)
            add_finger_zero_roll("palm.04.R", "右小指", +0)

            metarig_edit_bones["thumb.02.L"].roll = mmd_edit_bones["左親指１"].roll + math.radians(-90)
            metarig_edit_bones["thumb.03.L"].roll = mmd_edit_bones["左親指２"].roll + math.radians(-90)
            metarig_edit_bones["f_middle.01.L"].roll = mmd_edit_bones["左中指１"].roll + math.radians(+180)
            metarig_edit_bones["f_middle.02.L"].roll = mmd_edit_bones["左中指２"].roll + math.radians(+180)
            metarig_edit_bones["f_middle.03.L"].roll = mmd_edit_bones["左中指３"].roll + math.radians(+180)
            metarig_edit_bones["f_ring.01.L"].roll = mmd_edit_bones["左薬指１"].roll + math.radians(+180)
            metarig_edit_bones["f_ring.02.L"].roll = mmd_edit_bones["左薬指２"].roll + math.radians(+180)
            metarig_edit_bones["f_ring.03.L"].roll = mmd_edit_bones["左薬指３"].roll + math.radians(+180)
            metarig_edit_bones["f_ring.01.L"].roll = mmd_edit_bones["左薬指１"].roll + math.radians(+180)
            metarig_edit_bones["f_ring.02.L"].roll = mmd_edit_bones["左薬指２"].roll + math.radians(+180)
            metarig_edit_bones["f_ring.03.L"].roll = mmd_edit_bones["左薬指３"].roll + math.radians(+180)
            metarig_edit_bones["f_pinky.01.L"].roll = mmd_edit_bones["左小指１"].roll + math.radians(+180)
            metarig_edit_bones["f_pinky.02.L"].roll = mmd_edit_bones["左小指２"].roll + math.radians(+180)
            metarig_edit_bones["f_pinky.03.L"].roll = mmd_edit_bones["左小指３"].roll + math.radians(+180)

            metarig_edit_bones["thumb.02.R"].roll = mmd_edit_bones["右親指１"].roll + math.radians(-90)
            metarig_edit_bones["thumb.03.R"].roll = mmd_edit_bones["右親指２"].roll + math.radians(-90)
            metarig_edit_bones["f_middle.01.R"].roll = mmd_edit_bones["右中指１"].roll + math.radians(+0)
            metarig_edit_bones["f_middle.02.R"].roll = mmd_edit_bones["右中指２"].roll + math.radians(+0)
            metarig_edit_bones["f_middle.03.R"].roll = mmd_edit_bones["右中指３"].roll + math.radians(+0)
            metarig_edit_bones["f_ring.01.R"].roll = mmd_edit_bones["右薬指１"].roll + math.radians(+0)
            metarig_edit_bones["f_ring.02.R"].roll = mmd_edit_bones["右薬指２"].roll + math.radians(+0)
            metarig_edit_bones["f_ring.03.R"].roll = mmd_edit_bones["右薬指３"].roll + math.radians(+0)
            metarig_edit_bones["f_ring.01.R"].roll = mmd_edit_bones["右薬指１"].roll + math.radians(+0)
            metarig_edit_bones["f_ring.02.R"].roll = mmd_edit_bones["右薬指２"].roll + math.radians(+0)
            metarig_edit_bones["f_ring.03.R"].roll = mmd_edit_bones["右薬指３"].roll + math.radians(+0)
            metarig_edit_bones["f_pinky.01.R"].roll = mmd_edit_bones["右小指１"].roll + math.radians(+0)
            metarig_edit_bones["f_pinky.02.R"].roll = mmd_edit_bones["右小指２"].roll + math.radians(+0)
            metarig_edit_bones["f_pinky.03.R"].roll = mmd_edit_bones["右小指３"].roll + math.radians(+0)

        else:
            metarig_edit_bones["thumb.01.L"].roll += math.radians(-45)
            metarig_edit_bones["thumb.02.L"].roll += math.radians(-45)
            metarig_edit_bones["thumb.03.L"].roll += math.radians(-45)
            metarig_edit_bones["f_index.01.L"].roll += math.radians(-45)
            metarig_edit_bones["f_index.02.L"].roll += math.radians(-45)
            metarig_edit_bones["f_index.03.L"].roll += math.radians(-45)
            metarig_edit_bones["f_middle.01.L"].roll += math.radians(-45)
            metarig_edit_bones["f_middle.02.L"].roll += math.radians(-45)
            metarig_edit_bones["f_middle.03.L"].roll += math.radians(-45)
            metarig_edit_bones["f_ring.01.L"].roll += math.radians(-45)
            metarig_edit_bones["f_ring.02.L"].roll += math.radians(-45)
            metarig_edit_bones["f_ring.03.L"].roll += math.radians(-45)
            metarig_edit_bones["f_pinky.01.L"].roll += math.radians(-45)
            metarig_edit_bones["f_pinky.02.L"].roll += math.radians(-45)
            metarig_edit_bones["f_pinky.03.L"].roll += math.radians(-45)

            metarig_edit_bones["thumb.01.R"].roll += math.radians(+45)
            metarig_edit_bones["thumb.02.R"].roll += math.radians(+45)
            metarig_edit_bones["thumb.03.R"].roll += math.radians(+45)
            metarig_edit_bones["f_index.01.R"].roll += math.radians(+45)
            metarig_edit_bones["f_index.02.R"].roll += math.radians(+45)
            metarig_edit_bones["f_index.03.R"].roll += math.radians(+45)
            metarig_edit_bones["f_middle.01.R"].roll += math.radians(+45)
            metarig_edit_bones["f_middle.02.R"].roll += math.radians(+45)
            metarig_edit_bones["f_middle.03.R"].roll += math.radians(+45)
            metarig_edit_bones["f_ring.01.R"].roll += math.radians(+45)
            metarig_edit_bones["f_ring.02.R"].roll += math.radians(+45)
            metarig_edit_bones["f_ring.03.R"].roll += math.radians(+45)
            metarig_edit_bones["f_pinky.01.R"].roll += math.radians(+45)
            metarig_edit_bones["f_pinky.02.R"].roll += math.radians(+45)
            metarig_edit_bones["f_pinky.03.R"].roll += math.radians(+45)

        # fix elbow pole problem
        # https://blenderartists.org/t/rigify-elbow-problem/565285
        metarig_edit_bones["upper_arm.L"].tail += Vector([0, +0.001, 0])
        metarig_edit_bones["upper_arm.R"].tail += Vector([0, +0.001, 0])

        # remove unused mmd_edit_bones
        remove_metarig_edit_bones = [
            metarig_edit_bones["breast.L"],
            metarig_edit_bones["breast.R"],
        ]
        for metarig_bone in remove_metarig_edit_bones:
            metarig_edit_bones.remove(metarig_bone)

    def set_rigify_parameters(self, _mmd_armature_object: MMDArmatureObject):
        metarig_pose_bones = self.pose_bones

        # fix straight finger bend problem
        # https://blenderartists.org/t/rigify-fingers-issue/1218987
        # limbs.super_finger
        metarig_pose_bones["thumb.01.L"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["thumb.01.L"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["thumb.01.R"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["thumb.01.R"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_index.01.L"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_index.01.L"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_index.01.R"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_index.01.R"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_middle.01.L"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_middle.01.L"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_middle.01.R"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_middle.01.R"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_ring.01.L"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_ring.01.L"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_ring.01.R"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_ring.01.R"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_pinky.01.L"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_pinky.01.L"].rigify_parameters.make_extra_ik_control = True
        metarig_pose_bones["f_pinky.01.R"].rigify_parameters.primary_rotation_axis = "X"
        metarig_pose_bones["f_pinky.01.R"].rigify_parameters.make_extra_ik_control = True

        # fix straight arm IK problem
        # limbs.super_limb
        metarig_pose_bones["upper_arm.L"].rigify_parameters.rotation_axis = "x"
        metarig_pose_bones["upper_arm.R"].rigify_parameters.rotation_axis = "x"

        # fix straight leg IK problem
        # limbs.super_limb
        metarig_pose_bones["thigh.L"].rigify_parameters.rotation_axis = "x"
        metarig_pose_bones["thigh.R"].rigify_parameters.rotation_axis = "x"

        # fix toe problem
        # limbs.leg
        # TODO: Review when the Rigify bug is fixed
        #       https://developer.blender.org/T96748
        metarig_pose_bones["thigh.L"].rigify_parameters.extra_ik_toe = False
        metarig_pose_bones["thigh.R"].rigify_parameters.extra_ik_toe = False
