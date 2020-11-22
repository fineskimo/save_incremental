import bpy
import os
from bpy.app.handlers import persistent

bl_info = {
    "name": "Save Incremental",
    "description": 'Save your file with an incremental suffix',
    "author": "Lapineige, Fin",
    "version": (1, 8, 3),
    "blender": (2, 80, 0),
    "location": "File > Save Incremental",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}


def replace_recent(find, replace):

    blender_config_path = bpy.utils.user_resource('CONFIG')
    blender_recents = os.path.join(blender_config_path, "recent-files.txt")

    with open(blender_recents, 'rt') as original:
        current = original.readline().strip()
        data = original.read()

    prepend = True
    if current == find:
        prepend = False

    if prepend is True:
        with open(blender_recents, 'w') as modified: modified.write(f"{replace}\n" + data)

    else:
        data = data.replace(replace, find)
        with open(blender_recents, 'w') as modified: modified.write(data)


def detect_number(name):
    last_nb_index = -1

    for i in range(1, len(name)):
        if name[-i].isnumeric():
            if last_nb_index == -1:
                last_nb_index = len(name) - i + 1  # +1 because last index in [:] need to be 1 more
        elif last_nb_index != -1:
            first_nb_index = len(name) - i + 1  # +1 to restore previous index
            return (first_nb_index, last_nb_index, name[first_nb_index:last_nb_index])   # first: index of the number / last: last number index +1
    return False


class FileIncrementalSave(bpy.types.Operator):
    bl_idname = "wm.save_incremental"
    bl_label = "Save Incremental"
    bl_description = "Save incremental file revision"

    def execute(self, context):
        if bpy.data.filepath:
            sep = os.path.sep
            f_path = bpy.data.filepath
            directory = os.path.dirname(f_path)

            increment_files = [file for file in os.listdir(os.path.dirname(f_path)) if os.path.basename(f_path).split('.blend')[0] in file.split('.blend')[0] and file.split('.blend')[0] != os.path.basename(f_path).split('.blend')[0] and file.endswith(".blend")]
            for file in increment_files:
                if not detect_number(file):
                    increment_files.remove(file)
            numbers_index = [(index, detect_number(file.split('.blend')[0])) for index, file in enumerate(increment_files)]
            numbers = [index_nb[1] for index_nb in numbers_index]  # [detect_number(file.split('.blend')[0]) for file in increment_files]
            if numbers:  # prevent from error with max()
                str_nb = str(max([int(n[2]) for n in numbers]) + 1)  # zfill to always have something like 001, 010, 100

            if increment_files:
                d_nb = detect_number(increment_files[-1].split('.blend')[0])
                str_nb = str_nb.zfill(len(d_nb[2]))
            else:
                d_nb = False
                d_nb_filepath = detect_number(os.path.basename(f_path).split('.blend')[0])
                # if numbers: ## USELESS ??
                #    str_nb.zfill(3)
                if d_nb_filepath:
                    str_nb = str(int(d_nb_filepath[2]) + 1).zfill(len(d_nb_filepath[2]))
            if d_nb:
                if len(increment_files[-1].split('.blend')[0]) < d_nb[1]:   # in case last_nb_index is just after filename's max index
                    output = directory + sep + increment_files[-1].split('.blend')[0][:d_nb[0]] + str_nb + '.blend'
                else:
                    output = directory + sep + increment_files[-1].split('.blend')[0][:d_nb[0]] + str_nb + increment_files[-1].split('.blend')[0][d_nb[1]:] + '.blend'
            else:
                if d_nb_filepath:
                    if len(os.path.basename(f_path).split('.blend')[0]) < d_nb_filepath[1]:   # in case last_nb_index is just after filename's max index
                        output = directory + sep + os.path.basename(f_path).split('.blend')[0][:d_nb_filepath[0]] + str_nb + '.blend'

                    else:
                        output = directory + sep + os.path.basename(f_path).split('.blend')[0][:d_nb_filepath[0]] + str_nb + os.path.basename(f_path).split('.blend')[0][d_nb_filepath[1]:] + '.blend'

                else:
                    output = f_path.split(".blend")[0] + '_' + '001' + '.blend'

            if os.path.isfile(output):
                self.report({'WARNING'}, "Internal Error: trying to save over an existing file. Cancelled")
                print('Tested Output: ', output)
                return {'CANCELLED'}

            bpy.ops.wm.save_as_mainfile(filepath=output, copy=True)  # save
            bpy.ops.wm.open_mainfile(filepath=output)  # open
            replace_recent(f'{bpy.data.filepath}', output)  # do recents
            bpy.ops.wm.read_history()

            self.report({'INFO'}, "File: {0} - Created at: {1}".format(output[len(bpy.path.abspath(sep)):], output[:len(bpy.path.abspath(sep))]))
        else:
            self.report({'WARNING'}, "Please save a main file")
        return {'FINISHED'}
        # ##### PENSER A TESTER AUTRES FICHIERS DU DOSSIER, VOIR SI TROU DANS NUMEROTATION==> WARNING


def draw_override(self, context):

    layout = self.layout

    layout.operator_context = 'INVOKE_AREA'
    layout.menu("TOPBAR_MT_file_new", text="New", icon='FILE_NEW')
    layout.operator("wm.open_mainfile", text="Open...", icon='FILE_FOLDER')
    layout.menu("TOPBAR_MT_file_open_recent")
    layout.operator("wm.revert_mainfile")
    layout.menu("TOPBAR_MT_file_recover")

    layout.separator()

    layout.operator_context = 'EXEC_AREA' if context.blend_data.is_saved else 'INVOKE_AREA'
    layout.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')

    layout.operator_context = 'INVOKE_AREA'
    layout.operator("wm.save_as_mainfile", text="Save...")
    layout.operator_context = 'INVOKE_AREA'
    layout.operator("wm.save_as_mainfile", text="Save Copy...").copy = True
    layout.operator('wm.save_incremental', icon='FILE_TICK')

    layout.separator()

    layout.operator_context = 'INVOKE_AREA'
    layout.operator("wm.link", text="Link...", icon='LINK_BLEND')
    layout.operator("wm.append", text="Append...", icon='APPEND_BLEND')
    layout.menu("TOPBAR_MT_file_previews")

    layout.separator()

    layout.menu("TOPBAR_MT_file_import", icon='IMPORT')
    layout.menu("TOPBAR_MT_file_export", icon='EXPORT')

    layout.separator()

    layout.menu("TOPBAR_MT_file_external_data")
    layout.menu("TOPBAR_MT_file_cleanup")

    layout.separator()

    layout.menu("TOPBAR_MT_file_defaults")

    layout.separator()

    layout.operator("wm.quit_blender", text="Quit", icon='QUIT')


def draw_into_file_menu(self,context):
    self.layout.operator('wm.save_incremental', icon='FILE_TICK')


@persistent
def override_on_load(dummy):
    bpy.types.TOPBAR_MT_file.draw = draw_override


def register():
    bpy.utils.register_class(FileIncrementalSave)
    bpy.types.TOPBAR_MT_file.prepend(draw_into_file_menu)
    #bpy.app.handlers.load_post.append(override_on_load)

def unregister():
    bpy.utils.unregister_class(FileIncrementalSave)
    bpy.types.TOPBAR_MT_file.remove(draw_into_file_menu)
    #bpy.app.handlers.load_post.remove(override_on_load)


if __name__ == "__main__":
    register()
