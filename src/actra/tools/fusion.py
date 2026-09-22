"""Autodesk Fusion 360 CAD automation tools."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from actra.mac import apple_events, input_control
from actra.models import SafetyLevel, ToolResult
from .registry import tool


def _get_fusion_scripts_dir() -> Path:
    base = Path.home() / "Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts"
    base.mkdir(parents=True, exist_ok=True)
    return base


@tool(
    name="fusion_create_script",
    description="Creates a Python script in Autodesk Fusion 360's API Scripts directory so it can be executed inside Fusion.",
    parameters={
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Name of the script (e.g. 'CreateCup')"},
            "python_code": {"type": "string", "description": "Python code utilizing adsk.core and adsk.fusion"},
            "description": {"type": "string", "description": "Brief description of the script"}
        },
        "required": ["name", "python_code"]
    },
    safety=SafetyLevel.SAFE
)
def fusion_create_script(name: str, python_code: str, description: str = "Created by Actra") -> ToolResult:
    try:
        clean_name = "".join(c for c in name if c.isalnum() or c in ("_", "-"))
        script_dir = _get_fusion_scripts_dir() / clean_name
        script_dir.mkdir(parents=True, exist_ok=True)

        script_file = script_dir / f"{clean_name}.py"
        script_file.write_text(python_code, encoding="utf-8")

        manifest_file = script_dir / f"{clean_name}.manifest"
        manifest_data = {
            "autodeskProduct": "Fusion",
            "type": "script",
            "author": "Actra",
            "description": {"": description},
            "supportedOS": "mac",
            "editEnabled": True
        }
        manifest_file.write_text(json.dumps(manifest_data, indent=4), encoding="utf-8")

        return ToolResult.ok(
            "fusion_create_script",
            name=clean_name,
            script_path=str(script_file),
            manifest_path=str(manifest_file),
            message=f"Script '{clean_name}' successfully installed in Fusion 360 scripts directory."
        )
    except Exception as e:
        return ToolResult.fail("fusion_create_script", "ERROR", str(e))


@tool(
    name="fusion_design_part",
    description="Generates and installs a 3D parametric CAD design script in Autodesk Fusion 360 for parts like 'cup', 'mug', 'cylinder', 'box', etc.",
    parameters={
        "type": "object",
        "properties": {
            "part_type": {"type": "string", "description": "Type of part to design: 'cup', 'mug', 'cylinder', 'box', 'vase'"},
            "radius": {"type": "number", "description": "Radius or width in cm (default 4.0)"},
            "height": {"type": "number", "description": "Height in cm (default 10.0)"},
            "wall_thickness": {"type": "number", "description": "Wall thickness in cm (default 0.3)"}
        },
        "required": ["part_type"]
    },
    safety=SafetyLevel.SAFE
)
def fusion_design_part(
    part_type: str,
    radius: float = 4.0,
    height: float = 10.0,
    wall_thickness: float = 0.3
) -> ToolResult:
    try:
        part_clean = part_type.lower().strip()
        script_name = f"Actra_{part_clean.capitalize()}"

        if part_clean in ("cup", "mug", "vase", "cylinder"):
            code = f"""# Author-Actra
# Description-Parametric {part_clean} generator for Autodesk Fusion

import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        # Ensure active design document
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)

        rootComp = design.rootComponent

        # Create sketch on XY plane
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        # Base circle
        circles = sketch.sketchCurves.sketchCircles
        center = adsk.core.Point3D.create(0, 0, 0)
        circle = circles.addByCenterRadius(center, {radius})

        # Extrude cylinder body
        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        distance = adsk.core.ValueInput.createByReal({height})
        extInput.setDistanceExtent(False, distance)
        extFeature = extrudes.add(extInput)

        body = extFeature.bodies.item(0)

        # Hollow out top to make a cup (Shell feature)
        if "{part_clean}" in ("cup", "mug", "vase"):
            topFace = None
            maxZ = -1e9
            for face in body.faces:
                if face.geometry.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType:
                    pt = face.pointOnFace
                    if pt.z > maxZ:
                        maxZ = pt.z
                        topFace = face

            if topFace:
                shells = rootComp.features.shellFeatures
                inputFaces = adsk.core.ObjectCollection.create()
                inputFaces.add(topFace)
                shellInput = shells.createInput(inputFaces, False)
                shellInput.insideThickness = adsk.core.ValueInput.createByReal({wall_thickness})
                shells.add(shellInput)

        ui.messageBox('✨ 3D {part_clean.capitalize()} created successfully by Actra!')

    except:
        if ui:
            ui.messageBox('Failed:
{{}}'.format(traceback.format_exc()))
"""
        elif part_clean == "box":
            code = f"""# Author-Actra
# Description-Parametric Box generator for Autodesk Fusion

import adsk.core, adsk.fusion, traceback

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface

        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        if not design:
            doc = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
            design = adsk.fusion.Design.cast(app.activeProduct)

        rootComp = design.rootComponent
        sketches = rootComp.sketches
        xyPlane = rootComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)

        lines = sketch.sketchCurves.sketchLines
        w = {radius * 2}
        h = {height}
        lines.addTwoPointRectangle(adsk.core.Point3D.create(-w/2, -w/2, 0), adsk.core.Point3D.create(w/2, w/2, 0))

        prof = sketch.profiles.item(0)
        extrudes = rootComp.features.extrudeFeatures
        extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(h))
        extrudes.add(extInput)

        ui.messageBox('✨ 3D Box created successfully by Actra!')
    except:
        if ui:
            ui.messageBox('Failed:
{{}}'.format(traceback.format_exc()))
"""
        else:
            return ToolResult.fail("fusion_design_part", "UNSUPPORTED_TYPE", f"Part type '{part_type}' not recognized. Supported: cup, mug, cylinder, box, vase.")

        # Install script into Fusion
        res = fusion_create_script(name=script_name, python_code=code, description=f"Parametric 3D {part_clean} generator")
        if not res.success:
            return res

        return ToolResult.ok(
            "fusion_design_part",
            part_type=part_clean,
            script_name=script_name,
            script_path=res.data.get("script_path"),
            message=f"Generated parametric 3D CAD design script for '{part_clean}' and installed into Fusion 360 Scripts directory ({res.data.get('script_path')})."
        )
    except Exception as e:
        return ToolResult.fail("fusion_design_part", "ERROR", str(e))
