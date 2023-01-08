#Author- Matteo Vidali
#Description- A Test script to add pipe scaffolding by simply selecting a sketch

import adsk.core, adsk.fusion, adsk.cam, traceback

# Gets the sketch Lines object group from a selected sketch
def get_sketch_lines(sketch):
    return sketch.sketchCurves.sketchLines

def create_pipe(rootComp, sketch_lines, id, od):
    planes = rootComp.constructionPlanes
    sketches = rootComp.sketches
    extrudes = rootComp.features.extrudeFeatures

    for i in range(sketch_lines.count):
        if sketch_lines.item(i).isConstruction:
            continue
        # Create construction plane input
        planeInput = planes.createInput()

        # Add construction plane by distance on path (Centered)
        distance = adsk.core.ValueInput.createByReal(0.5)
        planeInput.setByDistanceOnPath(sketch_lines.item(i), distance)
        work_plane = planes.add(planeInput)

        # create circular profile and offset
        
        sketch = sketches.add(work_plane)
        sketchCircles = sketch.sketchCurves.sketchCircles
        centerPoint = adsk.core.Point3D.create(0, 0, 0)
        sketchCircles.addByCenterRadius(centerPoint, id)
        sketchCircles.addByCenterRadius(centerPoint, od)

        # Get extrude features
        

        prof = sketch.profiles.item(1)
        line_len = adsk.core.ValueInput.createByReal(sketch_lines.item(i).length+(2*od))
        extrudeInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extrudeInput.setSymmetricExtent(line_len, True)
        extrude0 = extrudes.add(extrudeInput)
        body = extrude0.bodies.item(0)
        body.name = "symmetric"



def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        design = app.activeProduct
        rootComp = design.rootComponent
        planes = rootComp.constructionPlanes
        extrudes = rootComp.features.extrudeFeatures
        # Currently just using the base component first sketch
        # to test
        lines = get_sketch_lines(rootComp.sketches[0])
        
        create_pipe(rootComp, lines, .05, .15)
        
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
