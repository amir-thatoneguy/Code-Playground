import bpy
import bpy_extras
import math
import mathutils
from itertools import product

def print(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")

# Point class with x, y as point
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def Left_index(points):
    minn = 0
    for i in range(1, len(points)):
        if points[i].x < points[minn].x:
            minn = i
        elif points[i].x == points[minn].x:
            if points[i].y > points[minn].y:
                minn = i
    return minn

def orientation(p, q, r):
    val = (q.y - p.y) * (r.x - q.x) - (q.x - p.x) * (r.y - q.y)
    if val == 0:
        return 0
    elif val > 0:
        return 1
    else:
        return 2

def convexHull(points, n, result):
    if n < 3:
        return
    l = Left_index(points)
    hull = []
    p = l
    q = 0
    while True:
        hull.append(p)
        q = (p + 1) % n
        for i in range(n):
            if orientation(points[p], points[i], points[q]) == 2:
                q = i
        p = q
        if p == l:
            break
    for each in hull:
        result.append(points[each])

def polygon_area(vertices):
    psum = 0
    nsum = 0
    for i in range(len(vertices)):
        sindex = (i + 1) % len(vertices)
        prod = vertices[i].x * vertices[sindex].y
        psum += prod
    for i in range(len(vertices)):
        sindex = (i + 1) % len(vertices)
        prod = vertices[sindex].x * vertices[i].y
        nsum += prod
    return abs(1 / 2 * (psum - nsum))

def CreateSphere(s):
    bpy.ops.mesh.primitive_uv_sphere_add(scale=(s, s, s))
    sphere = bpy.context.object
    sphere.name = 'target'
    bpy.ops.object.shade_smooth()
    sphere.location = [0, 0, sphere.dimensions.z / 2]

def Generate(dataset):
    light = bpy.context.scene.objects["Light"]
    light.data.energy = 3000
    for data in dataset:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.data.objects['target'].select_set(True)
        bpy.ops.object.delete()
        type = 'Sphere'  # Fixed type
        CreateSphere(data[0])  # Fixed sphere type
        target = bpy.data.objects['target']
        target.data.materials.append(bpy.data.materials['Target_Material'])
        bpy.data.materials['Target_Material'].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (1, 0, 0, 1)  # Fixed red color
        bpy.data.materials['Light_Material'].node_tree.nodes['Emission'].inputs['Color'].default_value = data[1][1]
        light.data.color.r = data[1][1][0]
        light.data.color.g = data[1][1][1]
        light.data.color.b = data[1][1][2]
        step = 1  # step <= 8
        for k in range(int(8 / step + 1)):
            light.location = [-4 + k * step, -4 + k * step, 8]
            brightest_point_global = [-4 + k * step, -4 + k * step, 0]
            brightest_point_camera = bpy_extras.object_utils.world_to_camera_view(bpy.data.scenes['Scene'], bpy.data.objects['Camera'], mathutils.Vector((brightest_point_global[0], brightest_point_global[1], 0.0)))
            points = []
            delete_points = []
            for j in range(len(target.data.vertices)):
                v_local = target.data.vertices[j].co
                v_global = target.matrix_world @ v_local
                if v_global.z <= 0.0001:
                    delete_point_camera = bpy_extras.object_utils.world_to_camera_view(bpy.data.scenes['Scene'], bpy.data.objects['Camera'], mathutils.Vector((v_global.x, v_global.y, 0.0)))
                    delete_points.append(Point(delete_point_camera.x * 15, delete_point_camera.y * 15))
                x = light.location.z * (v_global.x - light.location.x) / (light.location.z - v_global.z) + light.location.x
                y = light.location.z * (v_global.y - light.location.y) / (light.location.z - v_global.z) + light.location.y
                point_camera = bpy_extras.object_utils.world_to_camera_view(bpy.data.scenes['Scene'], bpy.data.objects['Camera'], mathutils.Vector((x, y, 0.0)))
                points.append(Point(point_camera.x * 15, point_camera.y * 15))
            shadow = []
            delete = []
            convexHull(points, len(points), shadow)
            convexHull(delete_points, len(delete_points), delete)
            scene = bpy.context.scene
            scene.render.image_settings.file_format = 'PNG'
            scene.render.filepath = '/Users/jiagengz/Documents/blender_scripts/sun-light-samples/datasets/' + type + '_Red_Size_' + str(data[0]) + '_LightPosition_' + str(k * step) + '_LightColor_' + data[1][0] + '_ShadowArea_' + str(format(polygon_area(shadow) - polygon_area(delete), '.3f')) + '_FloorColor_' + data[1][0] + '_Brightest_X_' + str(format(brightest_point_camera.x * 15, '.3f')) + '_Y_' + str(format(brightest_point_camera.y * 15, '.3f')) + '_RGB_' + str(data[1][2]) + '.png'
            bpy.ops.render.render(write_still=True)

# Set resolution
bpy.context.scene.render.resolution_x = 256
bpy.context.scene.render.resolution_y = 256

# Fixed parameters
fixed_type = 2  # Sphere
fixed_color = ('Red', (1, 0, 0, 1))  # Red color

# Variable parameters
scales = [0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6]  # Continuous scale values
light_colors = [('SkyBlue', (0.5, 1, 1, 1), (190, 215, 215)), ('Plum', (1, 0.5, 1, 1), (215, 190, 215)), ('Khaki', (1, 1, 0.5, 1), (215, 215, 190)), ('Lavender', (0.5, 0.5, 1, 1), (190, 190, 215)), ('LightGreen', (0.5, 1, 0.5, 1), (190, 215, 190)), ('Coral', (1, 0.5, 0.5, 1), (215, 190, 190))]

# Generate dataset
dataset = list(product(scales, light_colors))
Generate(dataset)