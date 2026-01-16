# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.


import bpy

from .checkers.operators import CheckEeveeRenderingPerformance
from .converters.armatures.operators import (
    MMDArmatureAddMetarig,
    MMDAutoRigApplyMMDRestPose,
    MMDAutoRigConvert,
    MMDRigifyApplyMMDRestPose,
    MMDRigifyConvert,
    MMDRigifyDerigger,
    MMDRigifyIntegrateFocusOnMMD,
    MMDRigifyIntegrateFocusOnRigify,
    MMDRigifyTranslator,
)
from .converters.physics.cloth import ConvertRigidBodyToClothOperator, RemoveMeshCloth, SelectClothMesh
from .converters.physics.cloth_bone import StretchBoneToVertexOperator
from .converters.physics.cloth_pyramid import (
    AddPyramidMeshByBreastBoneOperator,
    AssignPyramidWeightsOperator,
    ConvertPyramidMeshToClothOperator,
)
from .converters.physics.collision import RemoveMeshCollision, SelectCollisionMesh
from .editors.operators import (
    AutoSegmentationOperator,
    PaintSelectedFacesOperator,
    RestoreSegmentationColorPaletteOperator,
    SetupRenderEngineForEevee,
    SetupRenderEngineForToonEevee,
    SetupRenderEngineForWorkbench,
    SetupSegmentationColorPaletteOperator,
)
from .generators.physics import AddCenterOfGravityObject
from .utilities import import_mmd_tools, is_mmd_tools_installed


class InstallMMDTools(bpy.types.Operator):
    bl_idname = "mmd_tools_append.install_mmd_tools"
    bl_label = "Install MMD Tools"
    bl_options = {"REGISTER"}

    @classmethod
    def poll(cls, _context):
        return not is_mmd_tools_installed()

    def execute(self, context):
        bpy.ops.extensions.userpref_allow_online()
        bpy.ops.extensions.repo_sync(repo_index=0)
        bpy.ops.extensions.package_install(repo_index=0, pkg_id="mmd_tools")
        return {"FINISHED"}


class OperatorPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_operator_panel"
    bl_label = "MMD Append Operator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MMD"
    bl_context = ""

    def draw(self, _context):
        layout = self.layout

        if not is_mmd_tools_installed():
            layout.label(text="MMD Tools is not installed.", icon="ERROR")
            layout.operator(InstallMMDTools.bl_idname, icon="IMPORT")
            return

        col = layout.column(align=True)
        col.label(text="Render:", icon="SCENE_DATA")
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(SetupRenderEngineForEevee.bl_idname, icon="SCENE")
        grid.row(align=True).operator(SetupRenderEngineForWorkbench.bl_idname, icon="SCENE")
        grid.row(align=True).operator(SetupRenderEngineForToonEevee.bl_idname, icon="SCENE")
        grid.row(align=True).operator(CheckEeveeRenderingPerformance.bl_idname, icon="MOD_TIME")

        col = layout.column(align=True)
        col.label(text="MMD to Rigify:", icon="OUTLINER_OB_ARMATURE")
        grid = col.grid_flow(row_major=True, align=True)
        row = grid.row(align=True)
        row.operator_context = "EXEC_DEFAULT"
        row.operator(MMDArmatureAddMetarig.bl_idname, text="Add Metarig", icon="ADD").is_clean_armature = True
        row.operator_context = "INVOKE_DEFAULT"
        row.operator(MMDArmatureAddMetarig.bl_idname, text="", icon="WINDOW")

        row = grid.row(align=True)
        row.operator_context = "EXEC_DEFAULT"
        row.operator(MMDRigifyIntegrateFocusOnMMD.bl_idname, icon="GROUP_BONE").is_join_armatures = True
        row.operator_context = "INVOKE_DEFAULT"
        row.operator(MMDRigifyIntegrateFocusOnMMD.bl_idname, text="", icon="WINDOW")

        row = grid.row(align=True)
        row.operator_context = "EXEC_DEFAULT"
        row.operator(MMDRigifyIntegrateFocusOnRigify.bl_idname, icon="GROUP_BONE").is_join_armatures = True
        row.operator_context = "INVOKE_DEFAULT"
        row.operator(MMDRigifyIntegrateFocusOnRigify.bl_idname, text="", icon="WINDOW")

        col = layout.column(align=True)
        col.label(text="Rigify to MMD:", icon="OUTLINER_OB_ARMATURE")
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(MMDRigifyConvert.bl_idname, text="Convert to MMD compatible", icon="ARMATURE_DATA")
        grid.row(align=True).operator(MMDRigifyApplyMMDRestPose.bl_idname, text="Apply MMD Rest Pose")
        grid.row(align=True).operator(MMDRigifyDerigger.bl_idname, text="De-rig armature", icon="OUTLINER_OB_ARMATURE")
        grid.row(align=True).operator(MMDRigifyTranslator.bl_idname, text="Translate Rigify to MMD", icon="HELP")

        col.label(text="(Experimental) Auto-Rig to MMD:", icon="OUTLINER_OB_ARMATURE")
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(MMDAutoRigConvert.bl_idname, text="Convert to MMD compatible", icon="ARMATURE_DATA")
        grid.row(align=True).operator(MMDAutoRigApplyMMDRestPose.bl_idname, text="Apply MMD Rest Pose")


class MMDAppendPhysicsPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_physics"
    bl_label = "MMD Append Physics"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MMD"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_mmd_tools_installed()

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        col = layout.column(align=True)
        col.label(text="Relevant Selection:", icon="RESTRICT_SELECT_OFF")
        grid = col.grid_flow(row_major=True)
        row = grid.row(align=True)
        row.label(text="Collision Mesh", icon="MOD_PHYSICS")
        row.operator(SelectCollisionMesh.bl_idname, text="", icon="RESTRICT_SELECT_OFF")
        row.operator(RemoveMeshCollision.bl_idname, text="", icon="TRASH")

        mmd_root_object = import_mmd_tools().core.model.FnModel.find_root_object(context.active_object)
        if mmd_root_object is None:
            col = layout.column(align=True)
            col.label(text="MMD Model is not selected.", icon="ERROR")
        else:
            mmd_root = mmd_root_object.mmd_root

            row = grid.row(align=True)
            row.label(text="Rigid Body", icon="RIGID_BODY")
            row.operator_context = "EXEC_DEFAULT"
            operator = row.operator("mmd_tools.rigid_body_select", text="", icon="RESTRICT_SELECT_OFF")
            operator.properties = set(["collision_group_number", "shape"])
            row.operator_context = "INVOKE_DEFAULT"
            row.prop(
                mmd_root,
                "show_rigid_bodies",
                toggle=True,
                icon_only=True,
                icon="HIDE_OFF" if mmd_root.show_rigid_bodies else "HIDE_ON",
            )
            row.operator("rigidbody.objects_remove", text="", icon="TRASH")

            row = grid.row(align=True)
            row.label(text="Cloth Mesh", icon="MOD_CLOTH")
            row.operator(SelectClothMesh.bl_idname, text="", icon="RESTRICT_SELECT_OFF")
            row.prop(
                mmd_root_object,
                "mmd_tools_append_show_cloths",
                toggle=True,
                icon_only=True,
                icon="HIDE_OFF" if mmd_root_object.mmd_tools_append_show_cloths else "HIDE_ON",
            )
            row.operator(RemoveMeshCloth.bl_idname, text="", icon="TRASH")

            col = layout.column(align=True)
            col.label(text="Converter:", icon="SHADERFX")

            row = col.row(align=True)
            row.operator_context = "EXEC_DEFAULT"
            row.operator(ConvertRigidBodyToClothOperator.bl_idname, text="Rigid Body to Cloth", icon="MATCLOTH")
            row.operator_context = "INVOKE_DEFAULT"
            row.operator(ConvertRigidBodyToClothOperator.bl_idname, text="", icon="WINDOW")

        col = layout.column(align=True)
        col.label(text="Pyramid Cloth:", icon="MESH_CONE")
        grid = col.grid_flow(row_major=True, align=True)
        grid.row(align=True).operator(AddPyramidMeshByBreastBoneOperator.bl_idname, text="Add Pyramid", icon="CONE")
        grid.row(align=True).operator(ConvertPyramidMeshToClothOperator.bl_idname, text="Pyramid to Cloth", icon="MOD_CLOTH")
        grid.row(align=True).operator(AssignPyramidWeightsOperator.bl_idname, text="Repaint Weight", icon="WPAINT_HLT")

        col = layout.column(align=True)
        col.label(text="Misc:", icon="BLENDER")
        grid = col.grid_flow(row_major=True)
        grid.row(align=True).operator(StretchBoneToVertexOperator.bl_idname, text="Stretch Bone to Vertex", icon="CONSTRAINT_BONE")
        grid.row(align=True).operator(AddCenterOfGravityObject.bl_idname, text="Add Center of Gravity", icon="ORIENTATION_CURSOR")

    @staticmethod
    def _toggle_visibility_of_cloths(obj, context):
        mmd_tools = import_mmd_tools()

        mmd_root_object = mmd_tools.core.model.FnModel.find_root_object(obj)
        mmd_model = mmd_tools.core.model.Model(mmd_root_object)
        hide = not mmd_root_object.mmd_tools_append_show_cloths

        with mmd_tools.bpyutils.FnContext.temp_override_active_layer_collection(context, mmd_root_object):
            cloth_object: bpy.types.Object
            for cloth_object in mmd_model.cloths():
                cloth_object.hide = hide

            if hide and context.active_object is None:
                context.view_layer.objects.active = mmd_root_object

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Object.mmd_tools_append_show_cloths = bpy.props.BoolProperty(default=True, update=MMDAppendPhysicsPanel._toggle_visibility_of_cloths)

    @staticmethod
    def unregister():
        del bpy.types.Object.mmd_tools_append_show_cloths


class MMDAppendSegmentationPanel(bpy.types.Panel):
    bl_idname = "MMD_APPEND_PT_segmentation"
    bl_label = "MMD Append Segmentation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Tool"

    @classmethod
    def poll(cls, context: bpy.types.Context):
        return is_mmd_tools_installed() and context.mode in {"PAINT_VERTEX", "EDIT_MESH"}

    def draw(self, context: bpy.types.Context):
        layout = self.layout

        mmd_tools_append_segmentation = context.scene.mmd_tools_append_segmentation

        col = layout.column()
        col.prop(mmd_tools_append_segmentation, "segmentation_vertex_color_attribute_name", text="Color Layer&AOV Name")
        if SetupSegmentationColorPaletteOperator.poll(context):
            col.operator(SetupSegmentationColorPaletteOperator.bl_idname, icon="RESTRICT_COLOR_ON")
        else:
            col.operator(RestoreSegmentationColorPaletteOperator.bl_idname, icon="MOD_TINT")
            col.template_palette(context.tool_settings.vertex_paint, "palette")
            row = col.row(align=True)
            op = row.operator(PaintSelectedFacesOperator.bl_idname, icon="BRUSH_DATA")
            op.segmentation_vertex_color_attribute_name = mmd_tools_append_segmentation.segmentation_vertex_color_attribute_name
            op.random_color = False
            op = row.operator(PaintSelectedFacesOperator.bl_idname, text="", icon="RESTRICT_COLOR_OFF")
            op.segmentation_vertex_color_attribute_name = mmd_tools_append_segmentation.segmentation_vertex_color_attribute_name
            op.random_color = True

        col.label(text="Auto Segmentation:", icon="MOD_EXPLODE")
        box = col.box().column(align=True)

        box.label(text="Thresholds:")
        flow = box.grid_flow()
        flow.row(align=True).prop(mmd_tools_append_segmentation, "cost_threshold", text="Cost")
        row = flow.row(align=True)
        row.prop(mmd_tools_append_segmentation, "maximum_area_threshold", text="Area Max")
        row.prop(mmd_tools_append_segmentation, "minimum_area_threshold", text="Min")

        box.label(text="Cost Factors:")
        flow = box.grid_flow()
        row = flow.row(align=True)
        row.row().prop(mmd_tools_append_segmentation, "face_angle_cost_factor", text="Face Angle")
        row.row().prop(mmd_tools_append_segmentation, "perimeter_cost_factor", text="Perimeter")
        row.row().prop(mmd_tools_append_segmentation, "material_change_cost_factor", text="Material Change")

        row = flow.row(align=True)
        row.alignment = "RIGHT"
        row.label(text="Edge ")
        row.prop(mmd_tools_append_segmentation, "edge_sharp_cost_factor", text="Sharp")
        row.prop(mmd_tools_append_segmentation, "edge_seam_cost_factor", text="Seam")

        row = flow.row(align=True)
        row.alignment = "RIGHT"
        row.label(text="Vertex Group ")
        row.prop(mmd_tools_append_segmentation, "vertex_group_weight_cost_factor", text="Weight")
        row.prop(mmd_tools_append_segmentation, "vertex_group_change_cost_factor", text="Change")

        box.label(text="Other Parameters:")
        flow = box.grid_flow()
        flow.row().prop(mmd_tools_append_segmentation, "edge_length_factor")
        flow.row().prop(mmd_tools_append_segmentation, "segmentation_vertex_color_random_seed", text="Color Random Seed")

        op = col.operator(AutoSegmentationOperator.bl_idname, text="Execute Auto Segmentation", icon="BRUSH_DATA")
        op.cost_threshold = mmd_tools_append_segmentation.cost_threshold
        op.maximum_area_threshold = mmd_tools_append_segmentation.maximum_area_threshold
        op.minimum_area_threshold = mmd_tools_append_segmentation.minimum_area_threshold
        op.face_angle_cost_factor = mmd_tools_append_segmentation.face_angle_cost_factor
        op.perimeter_cost_factor = mmd_tools_append_segmentation.perimeter_cost_factor
        op.material_change_cost_factor = mmd_tools_append_segmentation.material_change_cost_factor
        op.edge_sharp_cost_factor = mmd_tools_append_segmentation.edge_sharp_cost_factor
        op.edge_seam_cost_factor = mmd_tools_append_segmentation.edge_seam_cost_factor
        op.vertex_group_weight_cost_factor = mmd_tools_append_segmentation.vertex_group_weight_cost_factor
        op.vertex_group_change_cost_factor = mmd_tools_append_segmentation.vertex_group_change_cost_factor
        op.edge_length_factor = mmd_tools_append_segmentation.edge_length_factor
        op.segmentation_vertex_color_random_seed = mmd_tools_append_segmentation.segmentation_vertex_color_random_seed
        op.segmentation_vertex_color_attribute_name = mmd_tools_append_segmentation.segmentation_vertex_color_attribute_name

        # tool_settings.vertex_paint.brush.color


class SegmentationPropertyGroup(bpy.types.PropertyGroup):
    cost_threshold: bpy.props.FloatProperty(name="Cost Threshold", default=2.5, min=0, soft_max=3.0, step=1)

    maximum_area_threshold: bpy.props.FloatProperty(name="Maximum Area Threshold", default=0.500, min=0, soft_max=1.0, precision=3, step=1)
    minimum_area_threshold: bpy.props.FloatProperty(name="Minimum Area Threshold", default=0.001, min=0, soft_max=1.0, precision=3, step=1)

    face_angle_cost_factor: bpy.props.FloatProperty(name="Face Angle Cost Factor", default=1.0, min=0, soft_max=2.0, step=1)
    perimeter_cost_factor: bpy.props.FloatProperty(name="Perimeter Cost Factor", default=0.0, min=0, soft_max=10.0, step=1)
    material_change_cost_factor: bpy.props.FloatProperty(name="Material Change Cost Factor", default=0.3, min=0, soft_max=1.0, step=1)
    edge_sharp_cost_factor: bpy.props.FloatProperty(name="Edge Sharp Cost Factor", default=0.0, min=0, soft_max=1.0, step=1)
    edge_seam_cost_factor: bpy.props.FloatProperty(name="Edge Seam Cost Factor", default=0.0, min=0, soft_max=1.0, step=1)
    vertex_group_weight_cost_factor: bpy.props.FloatProperty(name="Vertex Group Weight Cost Factor", default=0.1, min=0, soft_max=1.0, step=1)
    vertex_group_change_cost_factor: bpy.props.FloatProperty(name="Vertex Group Change Cost Factor", default=0.5, min=0, soft_max=1.0, step=1)

    edge_length_factor: bpy.props.FloatProperty(name="Edge Length Factor", default=1.0, min=0, soft_max=1.0, step=1)

    segmentation_vertex_color_random_seed: bpy.props.IntProperty(name="Segmentation Vertex Color Random Seed", default=0, min=0)
    segmentation_vertex_color_attribute_name: bpy.props.StringProperty(name="Segmentation Vertex Color Attribute Name", default="Segmentation")

    @staticmethod
    def register():
        # pylint: disable=assignment-from-no-return
        bpy.types.Scene.mmd_tools_append_segmentation = bpy.props.PointerProperty(type=SegmentationPropertyGroup)

    @staticmethod
    def unregister():
        del bpy.types.Scene.mmd_tools_append_segmentation
