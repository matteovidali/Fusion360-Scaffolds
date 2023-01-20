#Author- Matteo Vidali
#Description- A Test script to add pipe scaffolding by simply selecting a sketch
from . import commands
from .lib import fusion360utils as futil
import adsk.core, adsk.fusion, adsk.cam, traceback

_app: adsk.core.Application = None
_ui: adsk.core.UserInterface = None
_scaffoldCustFeatureDef: adsk.fusion.CustomFeatureDefinition = None
_custFeatureBeingEdited: adsk.fusion.CustomFeature = None
_handlers = []

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
        body.name = "pipe_body"



def run(context):
    try:
        global _app, _ui, _scaffoldCustFeatureDef, _handlers
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface
        ShowMessage('This Script RUUNS!')

        # Create the command definition for create
        scaffoldCreateCmdDef = _ui.commandDefinitions.addButtonDefinition(  "adskScaffoldCreate", 
                                                                            "Pipe Scaffold", 
                                                                            "Creates a custom Pipe Scaffold around sketch lines", 
                                                                            "Resources/Scaffold"  )

        # Add create button to UI
        solidWS = _ui.workspaces.itemById('FusionSolidEnvironment')
        sCreatePanel = solidWS.toolbarPanels.itemById('SolidCreatePanel')
        cntrl = sCreatePanel.controls.addCommand(scaffoldCreateCmdDef)
        cntrl.isPromoted = True
        cntrl.isPromotedByDefault = True

        # Connect handler to command created event
        onCommandCreated = ScaffoldCreateCommandCreatedHandler()
        scaffoldCreateCmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # Create command definition for feature edit
        scaffoldEditCmdDef = _ui.commandDefinitions.addButtonDefinition("adskScaffoldsEdit",
                                                                        "Pipe Scaffold Edit",
                                                                        "Edits the Pipe Scaffold Feature", "")
        
        # Connect Edit command Handler to command created event for scaffold edit
        onCommandCreated = ScaffoldEditCommandCreatedHandler()
        scaffoldEditCmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)


        # Create the custom Feature:
        _scaffoldCustFeatureDef = adsk.fusion.CustomFeatureDefinition.create(   "adskScaffold",
                                                                                "Pipe Scaffold",
                                                                                "Resources/Scaffold" )
        _scaffoldCustFeatureDef.editCommandId = "adskScaffoldsEdit"


#        # This should probably get moved: TODO:
#        design = app.activeProduct
#        rootComp = design.rootComponent
#        planes = rootComp.constructionPlanes
#        extrudes = rootComp.features.extrudeFeatures
#        # Lets get a selected sketch
#        MySketch = ui.selectEntity("Select A sketch", "Sketches")
#        
#        if not MySketch.isValid:
#            ui.messageBox("Sketch is Invalid")
#            raise ValueError('Sketch does not have any iterable curves / No lines detected')
#        MySketch = MySketch.entity
#            
#        
#        lines = get_sketch_lines(MySketch)
#        
#        create_pipe(rootComp, lines, .05, .15)
        
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            ShowMessage('BUT ERROR OCCURS')
            
        else:
            ShowMessage('No UI')


def stop(context):
    try:
        # Remove all of the event handlers your app has created
        futil.clear_handlers()
        
        solidWS = _ui.workspaces.itemById("FusionSolidEnvironment")
        sCreatePanel = solidWS.toolbarPanels.itemById("SolidCreatePanel")
        
        cmdCntrl = sCreatePanel.controls.itemById('adskScaffoldCreate')
        if cmdCntrl:
            cmdCntrl.deleteMe()

        scaffoldCreate = _ui.commandDefinitions.itemById("adskScaffoldCreate")
        if scaffoldCreate:
            scaffoldCreate.deleteMe()


        scaffoldEditCmdDef = _ui.commandDefinitions.itemById("adskScaffoldsEdit")
        if scaffoldEditCmdDef:
            scaffoldEditCmdDef.deleteMe()

        # This will run the start function in each of your commands as defined in commands/__init__.py
        commands.stop()


    except:
        futil.handle_error('stop')



class ScaffoldCreateCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            global _app
            eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            sketchSelInput = inputs.addSelectionInput("sketch", "Sketch", "Select a Sketch to define the Pipe Scaffold")
            sketchSelInput.addSelectionFilter("Sketches")
            #TODO: Limited to 1 sketch at the moment: is this good Idea? who knows.
            sketchSelInput.setSelectionLimits(1,1)

            des: adsk.fusion.Design = _app.activeProduct
            inputs.addValueInput("id", "Pipe ID", des.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(2.54))
            inputs.addValueInput("od", "Pipe OD", des.unitsManager.defaultLengthUnits, adsk.core.ValueInput.createByReal(3))

            # Connect to outside handler TODO: FIND OUT WHY???
            onActivate = CreateActivateHandler()
            cmd.activate.add(onActivate)
            _handlers.append(onActivate)

            # UnComment these lines to enable preselect behaviour
            #onPreSelect = PreSelectHandler()
            #cmd.preSelect.add(onPreSelect)
            #_handlers.append(onPreSelect)

            # Handle Preview Behaviour
            onExecutePreview = CreateExecutePreviewHandler()
            cmd.executePreview.add(onExecutePreview)
            _handlers.append(onExecutePreview)

            # Handle the Execute
            onExecute = CreateExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)

        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CreateActivateHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)

            # Code to react to the event.
            ShowMessage('In MyActivateHandler event handler.')
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Uncomment this to enable preSelect handling
#class PreSelectHandler(adsk.core.CommandEventHandler):
#    def __init__(self):
#        super().__init__()
#
#    def notify(self, args):
#        try:
#            pass
#        except:
#            _ui.messageBox(f'Failed:\n{traceback.format_exec()}')

class CreateExecutePreviewHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Get the inputs.
            sketchSel: adsk.core.SelectionCommandInput = inputs.itemById('sketch')
            sketch = sketchSel.selection(0).entity
            idInput: adsk.core.ValueCommandInput = inputs.itemById('id')
            odInput: adsk.core.ValueCommandInput = inputs.itemById('od')

            #TODO: CREATE THE SCAFFOLD

            # Code to react to the event.
            ShowMessage('In MyExecutePreviewHandler event handler.')
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class CreateExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    
    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            ShowMessage('In MyExecuteHandler event handler.')
            cmd = eventArgs.command
            inputs = cmd.commandInputs

            # Get the inputs.
            sketchSel: adsk.core.SelectionCommandInput = inputs.itemById('sketch')
            sketch: adsk.fusion.Sketch = sketchSel.selection(0).entity
            idInput: adsk.core.ValueCommandInput = inputs.itemById('id')
            odInput: adsk.core.ValueCommandInput = inputs.itemById('od')

            # Create the emboss.
            # TODO: CREATE THE FEATURE

            # Create the custom feature.
            comp: adsk.fusion.Component = sketch.parentComponent
            des = comp.parentDesign
            custFeatureInput = comp.features.customFeatures.createInput(_scaffoldCustFeatureDef)
            custFeatureInput.addDependency('sketch', sketch)
            custFeatureInput.addCustomParameter('id', 'ID', adsk.core.ValueInput.createByString(idInput.expression), des.unitsManager.defaultLengthUnits, True)
            custFeatureInput.addCustomParameter('od', 'OD', adsk.core.ValueInput.createByString(odInput.expression), des.unitsManager.defaultLengthUnits, True)
            # TODO: DETERMINE THIS>>>
            #custFeatureInput.setStartAndEndFeatures(sk, fillet)
            custFeature = comp.features.customFeatures.add(custFeatureInput)

            # Set the sketch and feature parameters to use the custom parameters.
            idCustParam = custFeature.parameters.itemById('id')
            idParam.expression = idCustParam.name

            odCustParam = custFeature.parameters.itemById('od')
            odParam.expression = odCustParam.name
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

id

class ScaffoldEditCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            pass
        except:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def ShowMessage(message: str):
    textPalette: adsk.core.TextCommandPalette = _ui.palettes.itemById('TextCommands')
    if textPalette:
        textPalette.writeText(message)