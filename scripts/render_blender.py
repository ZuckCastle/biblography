"""Render five short procedural 3D scene loops with Blender Workbench on CPU."""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy


def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    parser.add_argument("--fps", type=int, default=6)
    parser.add_argument("--frames-per-scene", type=int, default=12)
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    return mat


def cube(name, position, scale, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=position)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def setup():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 360
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.background_type = "WORLD"
    bpy.ops.object.camera_add(location=(0, -12, 5.2))
    camera = bpy.context.object
    camera.rotation_euler = (math.radians(72), 0, 0)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 7.7
    scene.camera = camera
    dark = material("deep blue", (0.025, 0.07, 0.18))
    blue = material("sea blue", (0.05, 0.2, 0.42))
    teal = material("sea teal", (0.07, 0.37, 0.54))
    gold = material("warm light", (1, 0.68, 0.22))
    pale = material("bright center", (1, 0.94, 0.65))
    cube("horizon", (0, 3.2, 0), (30, 0.1, 8), dark)
    waves = []
    for row in range(11):
        for col in range(9):
            x = (col - 4) * 0.9
            y = (row - 5) * 0.9
            obj = cube(f"wave_{row}_{col}", (x, y, -0.5), (0.88, 0.86, 0.14), blue if (row + col) % 2 else teal)
            waves.append((obj, x, y))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1, location=(0, 1.8, 1.3))
    orb = bpy.context.object
    orb.name = "light sphere"
    orb.data.materials.append(gold)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.72, location=(0, 1.7, 1.35))
    core = bpy.context.object
    core.name = "light center"
    core.data.materials.append(pale)
    return scene, waves, orb, core


def main():
    options = args()
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / "build" / "ingested.json").read_text(encoding="utf-8"))["plan"]
    scene, waves, orb, core = setup()
    output = Path(options.out).resolve()
    for scene_info in plan["scenes"]:
        verse = scene_info["verse"]
        folder = output / f"scene_{verse}"
        folder.mkdir(parents=True, exist_ok=True)
        for frame in range(options.frames_per_scene):
            phase = 2 * math.pi * frame / options.frames_per_scene
            for obj, x, y in waves:
                obj.location.z = -0.48 + 0.10 * math.sin(phase + x * 0.8 + y * 0.55)
            brightness = {1: 0.07, 2: 0.025, 3: 0.75, 4: 0.95, 5: 0.62}[verse]
            orb.scale = (brightness, brightness, brightness)
            core.scale = (brightness, brightness, brightness)
            orb.location = (0.2 * math.sin(phase), 1.8, 0.5 + brightness + (0.22 * math.sin(phase) if verse == 5 else 0))
            core.location = (orb.location.x, 1.68, orb.location.z + 0.04)
            scene.world.color = (0.012 + brightness * 0.14, 0.02 + brightness * 0.12, 0.07 + brightness * 0.12)
            scene.render.filepath = str(folder / f"{frame:03d}.png")
            bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene_info['id']} ({verse})")


if __name__ == "__main__":
    main()
