import functools
import bpy
import sys
import glob
import subprocess
from bpy_extras.io_utils import ImportHelper
from bpy.types import Panel, Operator
from bpy.app.handlers import persistent
import os
import threading
from queue import Queue

from . mix_ops import *
from . matgan_ops import *
from . neuralmat_ops import *


# Redraw all function
def redraw_all(context):
    for area in context.screen.areas:
        if area.type in ['NODE_EDITOR']:
            area.tag_redraw()

# Thread function for reading output
def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line.decode('utf-8').strip())
    out.close()

@persistent
def load_icons(dummy):
    MAT_OT_MATGAN_GetInterpolations._popen = None
    MAT_OT_MATGAN_Generator._popen = None
    MAT_OT_MATGAN_InputFromFlashImage._popen = None
    MAT_OT_MATGAN_SuperResolution._popen = None

def update_active_mat(self, context):
    ob = bpy.data.objects['Material Preview Plane']
    if context.scene.SelectWorkflow == 'MatGAN':
        ob.data.materials[0] = bpy.data.materials["matgan_mat"]
    elif context.scene.SelectWorkflow == 'NeuralMAT':
        ob.data.materials[0] = bpy.data.materials["neural_mat"]
    elif context.scene.SelectWorkflow == 'MixMAT':
        ob.data.materials[0] = bpy.data.materials['mix_mat']

def register():
    bpy.app.handlers.load_post.append(load_icons)

    bpy.types.Scene.SelectWorkflow = bpy.props.EnumProperty(
        name = 'Material System Select',
        description = 'Selected Material System for editing and generation.',
        items = { 
            ('MatGAN', 'MaterialGAN + LIIF', 'Using MaterialGAN for generation and LIIF model for upscaling. ' \
                + 'Editing implemented as vector space exploration.'), 
            ('NeuralMAT', 'Neural Material', 'Using Neural Material model for generatiog. ' \
                + 'Editing implemented as material interpolations.'), 
            ('MixMAT', 'Algorithmic generation', 'Using a Blender shader nodes approach for ' \
                + 'generating textures from albedo with mix blender shader nodes for editing.')
        },
        default='MatGAN',
        update=update_active_mat
    )

def unregister():
    bpy.app.handlers.load_post.remove(load_icons)


class MAT_PT_GeneratorPanel(Panel):
    bl_space_type = "NODE_EDITOR"
    bl_region_type = "UI"
    bl_label = "Modifier operations"
    bl_category = "MaterialGenerator Util"

    thumb_scale = 8.0
    check_existing = False

    def draw_matgan(self, context):
        layout = self.layout
        matgan = bpy.context.scene.matgan_properties

        # ================================================
        # Draw MaterialGAN props and operators
        # ================================================
        
        row = layout.row()
        row.prop(matgan, "progress", emboss=False, text="Status")
        
        row = layout.row()
        col = row.column()
        col.prop(matgan, "num_rend", text="Num of images")
        col = row.column()
        col.prop(matgan, "epochs", text="Epochs")
        
        row = layout.row()
        row.prop(matgan, "directory", text="Directory")
        row.operator("matgan.file_browser", icon="FILE_FOLDER", text="")

        row = layout.row()
        col = row.column()
        col.operator("matgan.input_from_images", text="Format flash images") 
        
        row = layout.row()
        col = row.column()
        col.operator("matgan.mat_from_images", text="Generate Material") 
        col = row.column()
        col.operator("matgan.stop_generator", text="", icon="PAUSE")

        layout.separator()

        # ================================================
        # Draw Upscale LIIF
        # ================================================

        row = layout.row()
        col = row.column()
        col.prop(matgan, "h_res", text="Height resolution")
        col = row.column()
        col.prop(matgan, "w_res", text="Width resolution")
        row = layout.row()
        row.operator("matgan.super_res", text="Upscale material")

        layout.separator()

        row = layout.row()
        row.operator("matgan.get_interpolations", text="Get interpolations")

        layout.separator()

        
        # ================================================
        # Draw Gallery view
        # ================================================

        if MAT_OT_MATGAN_GetInterpolations._popen is None and MAT_OT_MATGAN_Generator._popen is None:
            self.draw_gallery(context, matgan, "matgan")
        
    def draw_gallery(self, context, gan, mode):
        interp_dir = os.path.join(gan.directory, 'interps')
        out_dir =  os.path.join(gan.directory, 'out')

        if '7_1_render.png' in bpy.data.images and f'{mode}-render.png' in bpy.data.images:
            layout = self.layout
            box = layout.box()
            cols = box.column_flow(columns=3)

            # Get images
            dir_list = sorted(glob.glob(interp_dir + '/*_1_render.png'))

            id = 0
            for dir in dir_list:
                if id == 4:
                    in_box = cols.box()
                    col = in_box.column()
                    col.template_icon(icon_value=bpy.data.images[f'{mode}-render.png'].preview.icon_id, scale=10)
                    col.label(text="Current material")
                name = os.path.split(dir)[1]
                img = bpy.data.images[name]
                in_box = cols.box()
                col = in_box.column()
                col.template_icon(icon_value=img.preview.icon_id, scale=10)
                operator = col.operator(f'{mode}.edit_move', text=f"Semantic {name[0]}")
                operator.direction = name[0]
                id += 1
            
    def draw_neuralmat(self, context):
        layout = self.layout
        neuralmat = bpy.context.scene.neuralmat_properties

        # ================================================
        # Draw NeuralMaterial props and operators
        # ================================================

        row = layout.row()
        row.prop(neuralmat, "progress", emboss=False, text="Status")
        
        row = layout.row()
        col = row.column()
        col.prop(neuralmat, "num_rend", text="Num of images")
        col = row.column()
        col.prop(neuralmat, "epochs", text="Epochs")
        
        row = layout.row()
        col = row.column()
        col.prop(neuralmat, "h_res", text="Height resolution")
        col = row.column()
        col.prop(neuralmat, "w_res", text="Width resolution")
        
        row = layout.row()
        row.prop(neuralmat, "directory", text="Directory")
        row.operator("neuralmat.file_browser", icon="FILE_FOLDER", text="")

        row = layout.row()
        col = row.column()
        col.operator("neuralmat.generator", text="Generate Material") 
        col = row.column()
        col.operator("neuralmat.stop_generator", text="", icon="PAUSE")

        layout.separator()

        # ================================================
        # Draw NeuralMaterial interpolations operator
        # ================================================

        row = layout.row()
        row.operator("neuralmat.get_interpolations", text="Get interpolations")

        layout.separator()

        # ================================================
        # Draw Gallery view
        # ================================================

        if MAT_OT_NEURAL_GetInterpolations._popen is None and MAT_OT_NEURAL_Generator._popen is None:
            self.draw_gallery(context, neuralmat, "neural")

    def draw_mixmat(self, context):
        layout = self.layout
        mix = bpy.context.scene.mixmat_properties

        # ================================================
        # Draw Mix Materials generator operator
        # ================================================

        row = layout.row()
        row.prop(mix, "progress", emboss=False, text="Status")

        row = layout.row()
        row.prop(mix, "directory", text="Directory")
        row.operator("mixmat.file_browser", icon="FILE_FOLDER", text="")

        row = layout.row()
        row.operator("mixmat.generator", text="Generate")

        layout.separator()

        # ================================================
        # Draw Mix material interpolations operator
        # ================================================

        row = layout.row()
        row.prop(mix, "material", text="Select")
        row.prop(mix, "value", text="Mix level")
        

        if 'generated' in mix.progress:
            layout.separator()
            row = layout.row()
            row.template_preview(bpy.data.materials["mix_mat"], show_buttons=False)

    def draw(self, context):
        self.layout.prop(context.scene, 'SelectWorkflow')
        if context.scene.SelectWorkflow == 'MatGAN':
            self.draw_matgan(context)
        elif context.scene.SelectWorkflow == 'NeuralMAT':
            self.draw_neuralmat(context)
        elif context.scene.SelectWorkflow == 'MixMAT':
            self.draw_mixmat(context)
        
class MAT_OT_StatusUpdater(Operator):
    """Operator which runs its self from a timer"""
    bl_idname = "wm.modal_status_updater"
    bl_label = "Modal Status Updater"

    _timer = None
    _thread = None
    _q = Queue()

    def modal(self, context, event):
        gan = bpy.context.scene.matgan_properties
        
        if event.type == 'TIMER':                
            if MAT_OT_MATGAN_Generator._popen:
                if MAT_OT_MATGAN_Generator._popen.poll() is None:
                    try:
                        line = self._q.get_nowait()
                        print(line)
                        update_matgan(os.path.join(gan.directory, 'out'))
                        gan.progress = line
                        redraw_all(context)
                    except:
                        pass
                else:
                    update_matgan(os.path.join(gan.directory, 'out'))
                    gan.progress = "Material generated."
                    redraw_all(context)
                    MAT_OT_MATGAN_Generator._popen = None
                    self.cancel(context)
                    return {'CANCELLED'}

            elif MAT_OT_MATGAN_InputFromFlashImage._popen:
                if MAT_OT_MATGAN_InputFromFlashImage._popen.poll() is None:
                    try:
                        line = self._q.get_nowait()
                        print(line)
                        gan.progress = line
                        redraw_all(context)
                    except:
                        pass
                else:
                    gan.progress = "Input ready."
                    redraw_all(context)
                    MAT_OT_MATGAN_InputFromFlashImage._popen = None
                    self.cancel(context)
                    return {'CANCELLED'}
            
            elif MAT_OT_MATGAN_SuperResolution._popen:
                if MAT_OT_MATGAN_SuperResolution._popen.poll() is not None:
                    gan.progress = "Material upscaled."
                    update_matgan(os.path.join(gan.directory, 'out'))
                    redraw_all(context)
                    MAT_OT_MATGAN_SuperResolution._popen = None
                    self._thread = None
                    self.cancel(context)
                    return {'CANCELLED'}
            
            elif MAT_OT_MATGAN_GetInterpolations._popen:
                if MAT_OT_MATGAN_GetInterpolations._popen.poll() is None:
                    try:
                        line = self._q.get_nowait()
                        print(line)
                        gan.progress = line
                        redraw_all(context)
                    except:
                        pass
                else:
                    check_remove_img('matgan-render.png')
                    img = bpy.data.images.load(os.path.join(gan.directory, 'out') + '/render.png')
                    img.name = 'matgan-render.png'

                    interp_path = os.path.join(gan.directory, 'interps')
                    dir_list = sorted(glob.glob(interp_path + '/*_1_render.png'))
                    for dir in dir_list:
                        check_remove_img(os.path.split(dir)[1])
                        img = bpy.data.images.load(dir)
                        img.name = os.path.split(dir)[1]
                    gan.progress = "Material interpolations generated."
                    redraw_all(context)
                    MAT_OT_MATGAN_GetInterpolations._popen = None
                    self.cancel(context)
                    return {'CANCELLED'}

            elif MAT_OT_NEURAL_Generator._popen:
                gan = bpy.context.scene.neuralmat_properties
                if MAT_OT_NEURAL_Generator._popen.poll() is None:
                    try:
                        line = self._q.get_nowait()
                        print(line)
                        update_neural(os.path.join(gan.directory, 'out'))
                        gan.progress = line
                        redraw_all(context)
                    except:
                        pass
                else:
                    update_neural(os.path.join(gan.directory, 'out'))
                    gan.progress = "Material generated."
                    redraw_all(context)
                    MAT_OT_NEURAL_Generator._popen = None
                    self.cancel(context)
                    return {'CANCELLED'}

            elif MAT_OT_NEURAL_GetInterpolations._popen:
                gan = bpy.context.scene.neuralmat_properties
                if MAT_OT_NEURAL_GetInterpolations._popen.poll() is None:
                    try:
                        line = self._q.get_nowait()
                        print(line)
                        gan.progress = line
                        redraw_all(context)
                    except:
                        pass
                else:
                    check_remove_img('neural-render.png')
                    img = bpy.data.images.load(os.path.join(gan.directory, 'out') + '/render.png')
                    img.name = 'neural-render.png'

                    interp_path = os.path.join(gan.directory, 'interps')
                    dir_list = sorted(glob.glob(interp_path + '/*_1_render.png'))
                    for dir in dir_list:
                        check_remove_img(os.path.split(dir)[1])
                        img = bpy.data.images.load(dir)
                        img.name = os.path.split(dir)[1]
                    gan.progress = "Material interpolations generated."
                    redraw_all(context)
                    MAT_OT_NEURAL_GetInterpolations._popen = None
                    self.cancel(context)
                    return {'CANCELLED'}

            else:
                self.cancel(context)
                return {'CANCELLED'}
        return {'PASS_THROUGH'}

    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        if MAT_OT_MATGAN_Generator._popen:
            self._thread = threading.Thread(target=enqueue_output, args=(MAT_OT_MATGAN_Generator._popen.stdout, self._q), daemon=True)
        elif MAT_OT_MATGAN_InputFromFlashImage._popen:
            self._thread = threading.Thread(target=enqueue_output, args=(MAT_OT_MATGAN_InputFromFlashImage._popen.stdout, self._q), daemon=True)
        elif MAT_OT_MATGAN_GetInterpolations._popen:
            self._thread = threading.Thread(target=enqueue_output, args=(MAT_OT_MATGAN_GetInterpolations._popen.stdout, self._q), daemon=True)
        elif MAT_OT_MATGAN_SuperResolution._popen:
            self._thread = threading.Thread(target=enqueue_output, args=(MAT_OT_MATGAN_SuperResolution._popen.stdout, self._q), daemon=True)
        elif MAT_OT_NEURAL_Generator._popen:
            self._thread = threading.Thread(target=enqueue_output, args=(MAT_OT_NEURAL_Generator._popen.stdout, self._q), daemon=True)
        elif MAT_OT_NEURAL_GetInterpolations._popen:
            self._thread = threading.Thread(target=enqueue_output, args=(MAT_OT_NEURAL_GetInterpolations._popen.stdout, self._q), daemon=True)
        self._thread.start()
        return {'RUNNING_MODAL'}

    def cancel(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
