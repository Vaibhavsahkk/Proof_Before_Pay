import bpy
import math
from mathutils import Vector


FPS = 30
END = 450
OUT = "//media/blender_architecture.mp4"


def material(name, color, metallic=0.0, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = 0.32
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 2.2
    return mat


def add_cube(name, location, scale, mat, bevel=0.12):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bevel_mod = obj.modifiers.new("soft_edges", "BEVEL")
    bevel_mod.width = bevel
    bevel_mod.segments = 4
    obj.data.materials.append(mat)
    return obj


def add_text(body, location, size, mat, align="CENTER"):
    bpy.ops.object.text_add(location=location, rotation=(math.pi / 2, 0, 0))
    obj = bpy.context.object
    obj.data.body = body
    obj.data.align_x = align
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.012
    obj.data.bevel_depth = 0.004
    obj.data.materials.append(mat)
    return obj


def add_connector(start, end, mat):
    midpoint = (Vector(start) + Vector(end)) / 2
    length = (Vector(end) - Vector(start)).length
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.07, depth=length, location=midpoint)
    obj = bpy.context.object
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (Vector(end) - Vector(start)).to_track_quat("Z", "Y")
    obj.data.materials.append(mat)
    return obj


def point_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = END
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.render.ffmpeg.format = "MPEG4"
scene.render.ffmpeg.codec = "H264"
scene.render.ffmpeg.constant_rate_factor = "MEDIUM"
scene.render.filepath = OUT
scene.world.color = (0.008, 0.018, 0.035)

white = material("white", (0.8, 0.9, 0.95), metallic=0.1)
teal = material("evidence_teal", (0.04, 0.45, 0.5), metallic=0.15, emission=(0.05, 0.8, 0.75))
blue = material("extract_blue", (0.04, 0.24, 0.42), metallic=0.2, emission=(0.05, 0.4, 0.85))
green = material("verify_green", (0.04, 0.36, 0.25), metallic=0.1, emission=(0.1, 0.75, 0.4))
amber = material("rules_amber", (0.5, 0.26, 0.04), metallic=0.1, emission=(0.9, 0.4, 0.04))
rose = material("human_rose", (0.42, 0.08, 0.16), metallic=0.1, emission=(0.8, 0.12, 0.24))
glow = material("flow_glow", (0.1, 0.65, 0.8), emission=(0.1, 0.9, 1.0))
floor_mat = material("floor", (0.015, 0.04, 0.07), metallic=0.15)

add_cube("Floor", (0, 0, -0.35), (12, 5, 0.2), floor_mat, 0.04)
add_text("PROOF BEFORE PAY", (0, -0.55, 5.25), 0.62, white)
add_text("Evidence first. Payment second.", (0, -0.55, 4.6), 0.32, teal)

nodes = [
    (-8, "EVIDENCE\nINTAKE", "Invoice / PO / GRN", teal),
    (-4, "EXTRACT\nFACTS", "LLM reads documents", blue),
    (0, "VERIFY\nDETERMINISTICALLY", "Math / matches / bank", green),
    (4, "APPLY\nRULES", "HOLD > INVESTIGATE > PAY", amber),
    (8, "HUMAN\nDECISION", "No payment execution", rose),
]

for x, title, detail, mat in nodes:
    add_cube(title.replace("\n", "_"), (x, 0, 1.5), (1.55, 0.72, 1.05), mat)
    add_text(title, (x, -0.78, 1.78), 0.31, white)
    add_text(detail, (x, -0.78, 0.78), 0.16, white)

for left, right in zip(nodes[:-1], nodes[1:]):
    add_connector((left[0] + 1.65, 0, 1.5), (right[0] - 1.65, 0, 1.5), glow)

add_text("AI reads and explains", (-2, -0.75, 3.35), 0.22, blue)
add_text("Tools calculate", (2, -0.75, 3.35), 0.22, green)
add_text("Human approves consequences", (6, -0.75, 3.35), 0.22, rose)

bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.22, location=(-10, 0, 1.5))
flow = bpy.context.object
flow.name = "EvidenceFlow"
flow.data.materials.append(glow)
flow.keyframe_insert(data_path="location", frame=1)
flow.location.x = -8
flow.keyframe_insert(data_path="location", frame=75)
flow.location.x = -4
flow.keyframe_insert(data_path="location", frame=150)
flow.location.x = 0
flow.keyframe_insert(data_path="location", frame=225)
flow.location.x = 4
flow.keyframe_insert(data_path="location", frame=300)
flow.location.x = 8
flow.keyframe_insert(data_path="location", frame=375)
flow.location.x = 10
flow.keyframe_insert(data_path="location", frame=450)

for idx, x in enumerate((-8.8, -8.3, -7.8)):
    doc = add_cube(f"Document_{idx}", (x, 0.5, 4.0), (0.32, 0.08, 0.42), white, 0.03)
    doc.rotation_euler[1] = math.radians(8 * idx)
    doc.keyframe_insert(data_path="location", frame=1)
    doc.location = (x + 2.5, 0.1, 2.7)
    doc.keyframe_insert(data_path="location", frame=100 + idx * 12)
    doc.location = (x + 5.0, 0.0, 1.9)
    doc.keyframe_insert(data_path="location", frame=190 + idx * 12)

bpy.ops.object.camera_add(location=(0, -30, 10.5))
camera = bpy.context.object
camera.data.type = "PERSP"
camera.data.lens = 48
point_camera(camera, (0, 0, 1.8))
scene.camera = camera

bpy.ops.object.light_add(type="AREA", location=(0, -8, 10))
key = bpy.context.object
key.data.energy = 1500
key.data.shape = "RECTANGLE"
key.data.size = 12
point_camera(key, (0, 0, 1))

bpy.ops.object.light_add(type="AREA", location=(0, 4, 6))
fill = bpy.context.object
fill.data.energy = 800
fill.data.color = (0.15, 0.5, 0.8)
fill.data.size = 8
point_camera(fill, (0, 0, 1))

scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath="//media/blender_architecture.blend")
bpy.ops.render.render(animation=True)