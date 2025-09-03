# -*- coding: utf-8 -*-
# Copyright 2021 UuuNyaa <UuuNyaa@gmail.com>
# This file is part of MMD Tools Append.

# MMD Tools Append is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# MMD Tools Append is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import importlib.util
import os
import sys
import traceback

from mmd_tools_append import auto_load
from mmd_tools_append.m17n import _

bl_info = {
    "name": "mmd_tools_append",
    "description": "Utility tools for MMD model & scene editing by Uuu(/>ω<)/Nyaa!.",
    "author": "UuuNyaa",
    "version": (4, 0, 0),
    "blender": (4, 1, 0),
    "warning": "",
    "location": "View3D > Sidebar > MMD Tools Panel",
    "wiki_url": "https://github.com/MMD-Blender/blender_mmd_tools_append/wiki",
    "tracker_url": "https://github.com/MMD-Blender/blender_mmd_tools_append/issues",
    "support": "COMMUNITY",
    "category": "Object",
}

_translation_texts = [
    _("Utility tools for MMD model & scene editing by Uuu(/>ω<)/Nyaa!."),
    _("View3D > Sidebar > MMD Tools Panel"),
]

PACKAGE_PATH = os.path.dirname(__file__)
PACKAGE_NAME = __package__

REGISTER_HOOKS = []
UNREGISTER_HOOKS = []

auto_load.init()


def register():
    auto_load.register()
    for hook in REGISTER_HOOKS:
        try:
            hook()
        except:  # pylint: disable=bare-except
            traceback.print_exc()


def unregister():
    for hook in UNREGISTER_HOOKS:
        try:
            hook()
        except:  # pylint: disable=bare-except
            traceback.print_exc()
    auto_load.unregister()
