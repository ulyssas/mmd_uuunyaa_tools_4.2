# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

import os
import pathlib
import tempfile

import bpy
from bpy.app.translations import pgettext as _

from . import utilities
from .asset_search.assets import AssetUpdater
from .asset_search.operators import DeleteCachedFiles


class MMDToolsAppendAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    asset_search_results_max_display_count: bpy.props.IntProperty(
        name="Asset Search Results Max. Display Count",
        description="Larger value is slower",
        min=10,
        soft_max=200,
        default=50,
    )

    asset_jsons_folder: bpy.props.StringProperty(
        name="Asset JSONs Folder",
        description="Path to asset list JSON files",
        subtype="DIR_PATH",
        default=os.path.join(os.path.dirname(__file__), "asset_jsons"),
    )

    asset_json_update_repo: bpy.props.StringProperty(
        name="Asset JSON Update Repository",
        description="Specify the github repository which to retrieve the assets",
        default=AssetUpdater.default_repo,
    )

    asset_json_update_query: bpy.props.StringProperty(
        name="Asset JSON Update Query",
        description="Specify the filter conditions for retrieving assets",
        default=AssetUpdater.default_query,
    )

    asset_json_update_on_startup_enabled: bpy.props.BoolProperty(name="Asset JSON Auto Update on Startup", default=True)

    asset_cache_folder: bpy.props.StringProperty(
        name="Asset Cache Folder",
        description="Path to asset cache folder",
        subtype="DIR_PATH",
        default=os.path.join(tempfile.gettempdir(), "mmd_tools_append_cache"),
    )

    asset_max_cache_size: bpy.props.IntProperty(
        name="Asset Max. Cache Size (MB)",
        description="Maximum size (Mega bytes) of the asset cache folder",
        min=100,
        soft_max=1_000_000,
        default=10_000,
    )

    asset_extract_root_folder: bpy.props.StringProperty(
        name="Asset Extract Root Folder",
        description="Path to extract the cached assets",
        subtype="DIR_PATH",
        default=os.path.join(pathlib.Path.home(), "BlenderAssets"),
    )

    asset_extract_folder: bpy.props.StringProperty(
        name="Asset Extract Folder",
        description="Path to assets. Create it under the Asset Extract Root Folder.\nThe following variables are available: {id}, {type}, {name}, {aliases[en]}, {aliases[ja]}",
        default="{type}/{id}.{name}",
    )

    asset_extract_json: bpy.props.StringProperty(
        name="Asset Extract JSON",
        description="Name to assets marker JSON. Create it under the Asset Extract Folder.\nThe presence of this file is used to determine the existence of the asset.\nThe following variables are available: {id}, {type}, {name}, {aliases[en]}, {aliases[ja]}",
        default="{id}.json",
    )

    _translation_texts = [
        _("Check now for mmd_tools_append update"),
        _("Auto-check for Update"),
        _("Last check: Never"),
        _("Addon is up to date"),
        _("Checking..."),
        _("Choose 'Update Now' & press OK to install, "),
        _("or click outside window to defer"),
        _("No updates available"),
        _("Press okay to dismiss dialog"),
        _("Check for update now?"),
        _("Process update"),
        _("Decide to install, ignore, or defer new addon update"),
        _("Update Now"),
        _("Install update now"),
        _("Ignore"),
        _("Ignore this update to prevent future popups"),
        _("Defer"),
        _("Defer choice till next blender session"),
    ]

    def draw(self, context):
        layout: bpy.types.UILayout = self.layout  # pylint: disable=no-member

        col = layout.box().column()
        col.prop(self, "asset_search_results_max_display_count")

        col = layout.box().column()
        col.prop(self, "asset_jsons_folder")

        row = col.split(factor=0.95, align=True)
        row.prop(self, "asset_json_update_repo")
        row.operator("wm.url_open", text="Browse Assets", icon="URL").url = f"https://github.com/{self.asset_json_update_repo}/issues"

        row = col.split(factor=0.95, align=True)
        row.prop(self, "asset_json_update_query")
        row.operator("wm.url_open", text="Query Examples", icon="URL").url = "https://github.com/MMD-Blender/blender_mmd_tools_append/wiki/How-to-add-a-new-asset#query-examples"

        col.prop(self, "asset_json_update_on_startup_enabled")

        col = layout.box().column()
        col.prop(self, "asset_cache_folder")

        usage = col.split(align=True, factor=0.24)
        usage.label(text="Asset Cache Usage:")
        usage_row = usage.column(align=True)
        usage_row.alignment = "RIGHT"

        cache_folder_size = sum(f.stat().st_size for f in pathlib.Path(self.asset_cache_folder).glob("**/*") if f.is_file())
        usage_row.label(text=f"{utilities.to_human_friendly_text(cache_folder_size)}B")

        col.prop(self, "asset_max_cache_size")

        col.operator(DeleteCachedFiles.bl_idname)

        col = layout.box().column()
        col.prop(self, "asset_extract_root_folder")
        col.prop(self, "asset_extract_folder")
        col.prop(self, "asset_extract_json")

        layout.separator()
        col = layout.column()
        col.label(text="Credits:")

        credit = col.column(align=True)
        row = credit.split(factor=0.95)
        row.label(text="Rigid body Physics to Cloth Physics feature is the work of 小威廉伯爵.")
        row.operator("wm.url_open", text="", icon="URL").url = "https://github.com/958261649/Miku_Miku_Rig"
        credit.label(text="It was ported with his permission.")
