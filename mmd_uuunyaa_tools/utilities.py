# -*- coding: utf-8 -*-
# (C) 2021 UuuNyaa <UuuNyaa@gmail.com>

import os
import bpy

class ObjectAppender:
    def __init__(self, mark_id: str, blend_filename: str):
        self.mark_id = mark_id
        self.blend_filename = blend_filename

    def mark(self, obj):
        obj[self.mark_id] = True

    def unmark(self, obj):
        del obj[self.mark_id]

    def is_marked(self, obj) -> bool:
        return self.mark_id in obj

    def remove_objects(self):
        for collection in bpy.data.collections.values():
            if not self.is_marked(collection):
                continue
            for obj in collection.objects.values():
                if not self.is_marked(obj):
                    continue
                bpy.data.objects.remove(obj, do_unlink=True)
            self.unmark(collection)

    def append_collection(self, collection_name: str):
        if collection_name not in bpy.data.collections:
            path = os.path.join(self.blend_filename)
            with bpy.data.libraries.load(path, link=False) as (_, data_to):
                data_to.collections = [collection_name]

        return bpy.data.collections[collection_name]

    def append_objects_from_collection(self, collection_name: str):
        source = self.append_collection(collection_name)
        target = bpy.context.view_layer.active_layer_collection.collection
        self.mark(target)
        for obj in source.objects.values():
            self.mark(obj)
            source.objects.unlink(obj)
            target.objects.link(obj)
        bpy.data.collections.remove(source)