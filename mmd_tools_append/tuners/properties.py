# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import bpy
from bpy.types import GeometryNodeTree

from ..editors.nodes import MaterialEditor
from ..tuners import geometry_nodes_tuners, lighting_tuners, material_tuners


class LightingPropertyGroup(bpy.types.PropertyGroup):
    @staticmethod
    def update_lighting_thumbnails(prop: "LightingPropertyGroup", _):
        bpy.ops.mmd_tools_append.tune_lighting(lighting=prop.thumbnails)  # pylint: disable=no-member

    thumbnails: bpy.props.EnumProperty(
        items=lighting_tuners.TUNERS.to_enum_property_items(),
        description="Choose the lighting you want to use",
        update=update_lighting_thumbnails.__func__,
    )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Collection.mmd_tools_append_lighting = bpy.props.PointerProperty(type=LightingPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Collection.mmd_tools_append_lighting


class MaterialPropertyGroup(bpy.types.PropertyGroup):
    @staticmethod
    def update_material_thumbnails(prop: "MaterialPropertyGroup", _):
        if prop.update:
            bpy.ops.mmd_tools_append.tune_material(material=prop.thumbnails)  # pylint: disable=no-member

    update: bpy.props.BoolProperty(description="Whether or not to update active material", default=True)
    thumbnails: bpy.props.EnumProperty(
        items=material_tuners.TUNERS.to_enum_property_items(),
        description="Choose the material you want to use",
        update=update_material_thumbnails.__func__,
    )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Material.mmd_tools_append_material = bpy.props.PointerProperty(type=MaterialPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Material.mmd_tools_append_material


class GlobalToonSpherePropertyGroup(bpy.types.PropertyGroup):
    def _update_all_materials(self, attr_name, value):
        obj: bpy.types.Object = self.id_data
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.use_nodes:
                mat_editor = MaterialEditor(mat)
                method = getattr(mat_editor, attr_name, None)
                if method:
                    method(value)

    @staticmethod
    def adjust_toon(prop: "GlobalToonSpherePropertyGroup", _):
        prop._update_all_materials("set_mmd_toon_fac", prop.toon_fac)

    @staticmethod
    def adjust_sphere(prop: "GlobalToonSpherePropertyGroup", _):
        prop._update_all_materials("set_mmd_sphere_fac", prop.sphere_fac)

    toon_fac: bpy.props.FloatProperty(
        name="Toon Factor",
        description="Adjust the model's MMD toon texture factors globally",
        subtype="FACTOR",
        min=0.0,
        max=1.0,
        default=1,
        update=adjust_toon.__func__,
    )
    sphere_fac: bpy.props.FloatProperty(
        name="Sphere Factor",
        description="Adjust the model's MMD sphere texture factors globally",
        subtype="FACTOR",
        min=0.0,
        max=1.0,
        default=1,
        update=adjust_sphere.__func__,
    )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Object.mmd_tools_append_global_toon_sphere = bpy.props.PointerProperty(type=GlobalToonSpherePropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_tools_append_global_toon_sphere


class GeometryNodesPropertyGroup(bpy.types.PropertyGroup):
    @staticmethod
    def update_geometry_nodes_thumbnails(prop: "GeometryNodesPropertyGroup", _):
        bpy.ops.mmd_tools_append.tune_geometry_nodes(geometry_nodes=prop.thumbnails)  # pylint: disable=no-member

    thumbnails: bpy.props.EnumProperty(
        items=geometry_nodes_tuners.TUNERS.to_enum_property_items(),
        description="Choose the geometry nodes you want to use",
        update=update_geometry_nodes_thumbnails.__func__,
    )

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        GeometryNodeTree.mmd_tools_append_geometry_nodes = bpy.props.PointerProperty(type=GeometryNodesPropertyGroup)

    @staticmethod
    def unregister():
        del GeometryNodeTree.mmd_tools_append_geometry_nodes
