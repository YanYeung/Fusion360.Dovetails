#Author-Michael Logutov
#Description-在指定边缘创建燕尾榫的"榫头"部分

handlers = []

ADDIN_NAME = "燕尾榫"
COMMAND_ID = ADDIN_NAME + "Addin"

import adsk.core, adsk.fusion, adsk.cam, traceback, math
from enum import Enum

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        command_definition = ui.commandDefinitions.itemById(COMMAND_ID)
        if not command_definition:
            command_definition = ui.commandDefinitions.addButtonDefinition(COMMAND_ID, ADDIN_NAME, "在指定边缘创建燕尾榫的\"榫头\"部分", "Resources/Dovetails")
            
        on_command_created = DovetailsCommandCreatedHandler()
        command_definition.commandCreated.add(on_command_created)
        handlers.append(on_command_created)
        
        addins_panel = ui.allToolbarPanels.itemById("SolidCreatePanel")
        addins_panel.controls.addCommand(command_definition)
    except:
        if ui:
            ui.messageBox("失败：\n{}".format(traceback.format_exc()))
            

def stop(context):
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        
        addins_panel = ui.allToolbarPanels.itemById("SolidCreatePanel")
        
        for ctrl in addins_panel.controls:
            if ctrl.id == COMMAND_ID:
                ctrl.deleteMe()
        
        command_definition = ui.commandDefinitions.itemById(COMMAND_ID)
        if command_definition:
            command_definition.deleteMe()
    except:
        if ui:
            ui.messageBox("失败：\n{}".format(traceback.format_exc()))	
        
         
class DovetailStartType(Enum):
    FullPin = "完整榫肩"
    HalfPin = "半榫肩"
    HalfTail = "半榫头"

class DovetailsCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            command = adsk.core.Command.cast(args.command)
            inputs = command.commandInputs
            
            design = adsk.fusion.Design.cast(app.activeProduct)
            if not design:
                ui.messageBox("使用此命令时，必须有一个处于活动状态的 Fusion 设计文档。")
                return False

            command.setDialogMinimumSize(550, 600)

            inputs.addImageCommandInput("help_image", "", "./Resources/Dialog help.png")
                
            face_input = inputs.addSelectionInput("face", "面", "选择要放置燕尾榫的面")
            face_input.setSelectionLimits(1, 1)
            face_input.addSelectionFilter("SolidFaces")
            
            edge_input = inputs.addSelectionInput("edge", "边", "在选定面上选择要放置燕尾榫的边")
            edge_input.setSelectionLimits(1, 1)
            edge_input.addSelectionFilter("LinearEdges")
            
            edge_length = inputs.addValueInput("edge_length", "边长", "mm", adsk.core.ValueInput.createByString("100 mm"))
            edge_length.tooltip = "通常设置为板材宽度参数，例如 \"drawer_height\"。"
            
            angle = inputs.addValueInput("angle", "角度", "deg", adsk.core.ValueInput.createByString("7 deg"))
            angle.tooltip = "燕尾榫侧边的角度。1:8 比例对应 7°，1:6 比例对应 9.5°。"

            height = inputs.addValueInput("height", "高度", "mm", adsk.core.ValueInput.createByString("10 mm"))
            height.tooltip = "燕尾榫从板边起始的高度。" \
                "通常设置为另一块板的厚度参数，例如 \"drawer_side_thickness\"。"

            thickness = inputs.addValueInput("thickness", "厚度", "mm", adsk.core.ValueInput.createByString("10 mm"))
            thickness.tooltip = "燕尾榫的厚度。通常设置为板材厚度参数，例如 \"drawer_front_thickness\"。"

            ratio = inputs.addValueInput("ratio", "榫头与榫肩比例", "", adsk.core.ValueInput.createByString("2"))
            ratio.tooltip = "榫头最大宽度与榫肩最大宽度的比值。"

            pin = inputs.addValueInput("pin", "最大榫肩宽度", "mm", adsk.core.ValueInput.createByString("11 mm"))
            pin.tooltip = "燕尾榫之间完整榫肩的最大宽度。增大此值可生成更大的燕尾榫，减小则反之。"

            start_type_input = inputs.addDropDownCommandInput("start_type", "起始类型", adsk.core.DropDownStyles.TextListDropDownStyle)
            for st in DovetailStartType:
                start_type_input.listItems.add(st.value, False, '')
            start_type_input.listItems[0].isSelected = True
            start_type_input.tooltip = "指定以完整榫肩还是半榫肩开始。"

            params_prefix = inputs.addStringValueInput("params_prefix", "参数名称前缀", "dovetails_")
            params_prefix.tooltip = "所有生成的燕尾榫参数将作为用户参数添加，其名称以此文本为前缀。" \
                "通常设置为零件名称，例如 \"drawer_front_dovetails_\""
            
            on_select = DovetailsCommandSelectionEventHandler()
            command.selectionEvent.add(on_select)
            handlers.append(on_select)
            
            on_input_changed = DovetailsCommandInputChangedEventHandler()
            command.inputChanged.add(on_input_changed)
            handlers.append(on_input_changed)
            
            on_execute = DovetailsCommandExecuteEventHandler()
            command.execute.add(on_execute)
            handlers.append(on_execute)
        except:
            if ui:
                ui.messageBox("失败：\n{}".format(traceback.format_exc()))
               

class DovetailsCommandSelectionEventHandler(adsk.core.SelectionEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            event_args = adsk.core.SelectionEventArgs.cast(args)
            inputs = event_args.firingEvent.sender.commandInputs
            
            if event_args.activeInput.id == "edge":
                face = adsk.fusion.BRepFace.cast(inputs.itemById("face").selection(0).entity)
                edge = adsk.fusion.BRepEdge.cast(event_args.selection.entity)
                event_args.isSelectable = any([x for x in face.edges if x == edge])
        except:
            if ui:
                ui.messageBox("失败：\n{}".format(traceback.format_exc()))

                
class DovetailsCommandInputChangedEventHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui  = app.userInterface
            event_args = adsk.core.InputChangedEventArgs.cast(args)
            inputs = event_args.firingEvent.sender.commandInputs
            current_input = event_args.input
            
            if not current_input.isValid:
                return
                
            prev = None
            for cur in inputs:
                if prev and prev == current_input:
                    cur.hasFocus = True
                    break
                prev = cur
        except:
            if ui:
                ui.messageBox("失败：\n{}".format(traceback.format_exc()))
        
        
def add_parameter_if_not_exists(design, prefix, name, value, units = "", comment = ""):
    param_name = prefix + name
    param = design.userParameters.itemByName(param_name)
    if not param:
        param = design.userParameters.add(param_name, adsk.core.ValueInput.createByString(value), units, comment)
        if not param:
            raise ValueError("无法创建用户参数：{}".format(param_name))
    return param
    
   
def new_point(x, y, origin, xAxis, yAxis):
    x_axis = xAxis.copy()
    x_axis.normalize()
    x_axis.scaleBy(x)
    
    y_axis = yAxis.copy()
    y_axis.normalize()
    y_axis.scaleBy(y)
    
    v = origin.asVector()
    v.add(x_axis)
    v.add(y_axis)
    
    return v.asPoint()

    
def debug_draw_line(sketch, origin, vector, add = True):

    point1 = origin
    if isinstance(origin, adsk.core.Vector3D):
        point1 = origin.asPoint()
        
    if (isinstance(vector, adsk.core.Vector3D)):
        if add:
            v = vector.copy()
            v.add(point1.asVector())
            point2 = v.asPoint()
        else:
            point2 = vector.asPoint()
    else:
        point2 = vector
        
    line = sketch.sketchCurves.sketchLines.addByTwoPoints(point1, point2)
    line.isConstruction = True
    return line

    
def new_rotation_matrix(angle, axis, origin = adsk.core.Point3D.create(0, 0, 0)):
    m = adsk.core.Matrix3D.create()
    m.setToRotation(angle, axis, origin)
    return m
    
    
def find_profile_for_line(curve):
    curve = adsk.fusion.SketchCurve.cast(curve)
    for profile in curve.parentSketch.profiles:
        for profile_loop in profile.profileLoops:
            for profile_loop_curve in profile_loop.profileCurves:
                if profile_loop_curve.sketchEntity == curve:
                    return profile
    return None
 
   
class DovetailsCommandExecuteEventHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
        
    def notify(self, args):
        ui = None
        try:
            app = adsk.core.Application.get()
            ui = app.userInterface
            design = adsk.fusion.Design.cast(app.activeProduct)
            command = adsk.core.Command.cast(args.command)
            inputs = command.commandInputs
    
            face = adsk.fusion.BRepFace.cast(inputs.itemById("face").selection(0).entity)
            edge = adsk.fusion.BRepEdge.cast(inputs.itemById("edge").selection(0).entity)
            edge_length_input = adsk.core.ValueCommandInput.cast(inputs.itemById("edge_length"))
            angle_input = adsk.core.ValueCommandInput.cast(inputs.itemById("angle"))
            height_input = adsk.core.ValueCommandInput.cast(inputs.itemById("height"))
            thickness_input = adsk.core.ValueCommandInput.cast(inputs.itemById("thickness"))
            ratio_input = adsk.core.ValueCommandInput.cast(inputs.itemById("ratio"))
            pin_input = adsk.core.ValueCommandInput.cast(inputs.itemById("pin"))
            start_type = DovetailStartType(adsk.core.DropDownCommandInput.cast(inputs.itemById("start_type")).selectedItem.name)
            params_prefix = adsk.core.StringValueCommandInput.cast(inputs.itemById("params_prefix")).value
            
            angle_param = add_parameter_if_not_exists(design, params_prefix, "angle",
                                                      angle_input.expression,
                                                      angle_input.unitType,
                                                      "燕尾榫角度")
            height_param = add_parameter_if_not_exists(design, params_prefix, "height",
                                                       height_input.expression,
                                                       height_input.unitType,
                                                       "燕尾榫高度")
            thickness_param = add_parameter_if_not_exists(design, params_prefix, "thickness",
                                                          thickness_input.expression,
                                                          thickness_input.unitType,
                                                          "燕尾榫厚度")
            edge_length_param = add_parameter_if_not_exists(design, params_prefix, "edge_length",
                                                            edge_length_input.expression,
                                                            edge_length_input.unitType,
                                                            "燕尾榫边长")
            pin_param = add_parameter_if_not_exists(design, params_prefix, "pin",
                                                    pin_input.expression,
                                                    pin_input.unitType,
                                                    "燕尾榫最大榫肩宽度")
            ratio_param = add_parameter_if_not_exists(design, params_prefix, "ratio",
                                                      ratio_input.expression,
                                                      ratio_input.unitType,
                                                      "燕尾榫榫头与榫肩近似比例")
                                                    
            if start_type == DovetailStartType.FullPin:
                count_param_expression = "round (({} - {}) / ({} * (1 + {})))".format(edge_length_param.name, pin_param.name, pin_param.name, ratio_param.name)
            elif start_type == DovetailStartType.HalfPin:
                count_param_expression = "round ({} / ({} * (1 + {})))".format(edge_length_param.name, pin_param.name, ratio_param.name)
            elif start_type == DovetailStartType.HalfTail:
                count_param_expression = "round ({} / ({} * (1 + {})) - 1)".format(edge_length_param.name, pin_param.name, ratio_param.name)
            else:
                raise ValueError("不支持的起始类型：{}".format(start_type))
                
            count_param = add_parameter_if_not_exists(design, params_prefix, "count",
                                                      count_param_expression,
                                                      "",
                                                      "燕尾榫数量")
                                                      
            if count_param.value <= 0:
                raise ValueError("参数不适用 - 燕尾榫数量表达式计算得到无效数值 {}".format(count_param.value))
                
            # calculate resulted tails width after number of tails has been calculated
            if start_type == DovetailStartType.FullPin:
                tail_param_expression = "({} - {} * ({} + 1)) / {}".format(edge_length_param.name, pin_param.name, count_param.name, count_param.name)
            elif start_type == DovetailStartType.HalfPin:
                tail_param_expression = "({} - {} * {}) / {}".format(edge_length_param.name, pin_param.name, count_param.name, count_param.name)
            elif start_type == DovetailStartType.HalfTail:
                tail_param_expression = "{} / ({} + 1) - {}".format(edge_length_param.name, count_param.name, pin_param.name)
            else:
                raise ValueError("不支持的起始类型：{}".format(start_type))
                
            tail_param = add_parameter_if_not_exists(design, params_prefix, "tail",
                                                     tail_param_expression,
                                                     pin_input.unitType,
                                                     "燕尾榫榫头最小宽度")
                                                  
            component = face.body.parentComponent
            sketch = adsk.fusion.Sketch.cast(component.sketches.add(face))
            sketch.name = params_prefix + "sketch"
            projected_edge = adsk.fusion.SketchLine.cast(sketch.project(edge)[0])

            v_start = projected_edge.startSketchPoint.geometry.asVector()
            v_end = projected_edge.endSketchPoint.geometry.asVector()
            
            v_edge = v_end.copy()
            v_edge.subtract(v_start)

            face_center_in_sketch = sketch.modelToSketchSpace(face.centroid)
            
            (res, face_normal) = face.evaluator.getNormalAtPoint(face.centroid)
            if not res:
                raise ValueError("无法获取面法线")
                
            face_normal.add(face.centroid.asVector())
            face_normal = sketch.modelToSketchSpace(face_normal.asPoint()).asVector()
            face_normal.subtract(face_center_in_sketch.asVector())
            
            v_to_face_center = face_center_in_sketch.asVector()
            v_to_face_center.subtract(v_start)
            
            origin = v_start.asPoint()
                        
            v_outside = v_edge.crossProduct(face_normal)
            if v_outside.angleTo(v_to_face_center) < math.pi / 2:
                v_outside.transformBy(new_rotation_matrix(math.pi, v_edge, origin))

            # debug_draw_line(sketch, origin, face_center_in_sketch)
            # debug_draw_line(sketch, origin, v_edge)
            # debug_draw_line(sketch, origin, v_outside)
            # debug_draw_line(sketch, origin, face_normal)

            transform = adsk.core.Matrix3D.create()
            transform.transformBy(new_rotation_matrix(adsk.core.Vector3D.create(0, 1, 0).angleTo(v_outside), adsk.core.Vector3D.create(0, 0, 1)))
            transform.transformBy(new_rotation_matrix(adsk.core.Vector3D.create(1, 0, 0).angleTo(v_edge), adsk.core.Vector3D.create(0, 0, 1)))
            
            x_axis = v_edge
            y_axis = v_outside
            #sketch.sketchCurves.sketchLines.addByTwoPoints(new_point(0, 0, origin, x_axis, y_axis), new_point(1, 0, origin, x_axis, y_axis))
            #sketch.sketchCurves.sketchLines.addByTwoPoints(new_point(0, 0, origin, x_axis, y_axis), new_point(0, 2, origin, x_axis, y_axis))
            
            # draw one dovetail sketch
            lines = sketch.sketchCurves.sketchLines
            half_tails_profiles = None
            
            if start_type == DovetailStartType.HalfTail:
                # starting half tail
                line1 = lines.addByTwoPoints(new_point(0, 0, origin, x_axis, y_axis), new_point(1, 0, origin, x_axis, y_axis))
                sketch.geometricConstraints.addCoincident(line1.startSketchPoint, projected_edge.startSketchPoint)
                sketch.geometricConstraints.addCoincident(line1.endSketchPoint, projected_edge)
                d = sketch.sketchDimensions.addDistanceDimension(line1.startSketchPoint, line1.endSketchPoint,
                                                                 adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                                                 new_point(0.5, -0.5, origin, x_axis, y_axis))
                d.parameter.expression = "{} / 2".format(tail_param.name)
                
                line2 = lines.addByTwoPoints(line1.endSketchPoint, new_point(1.5, 1, origin, x_axis, y_axis))
                d = sketch.sketchDimensions.addAngularDimension(projected_edge, line2, new_point(1.5, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = "90 deg - {}".format(angle_param.name)
                
                line3 = lines.addByTwoPoints(line2.endSketchPoint, new_point(0, 1, origin, x_axis, y_axis))
                d = sketch.sketchDimensions.addOffsetDimension(line3, projected_edge, new_point(0.5, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = height_param.name
                starting_half_tail_profile_line = line3
                
                line4 = lines.addByTwoPoints(line3.endSketchPoint, line1.startSketchPoint)
                sketch.geometricConstraints.addPerpendicular(line4, projected_edge)
                
                # ending half tail
                line1 = lines.addByTwoPoints(new_point(5, 0, origin, x_axis, y_axis), new_point(4, 0, origin, x_axis, y_axis))
                sketch.geometricConstraints.addCoincident(line1.startSketchPoint, projected_edge.endSketchPoint)
                sketch.geometricConstraints.addCoincident(line1.endSketchPoint, projected_edge)
                d = sketch.sketchDimensions.addDistanceDimension(line1.startSketchPoint, line1.endSketchPoint,
                                                                 adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                                                 new_point(4.5, -0.5, origin, x_axis, y_axis))
                d.parameter.expression = "{} / 2".format(tail_param.name)
                
                line2 = lines.addByTwoPoints(line1.endSketchPoint, new_point(3.5, 1, origin, x_axis, y_axis))
                d = sketch.sketchDimensions.addAngularDimension(projected_edge, line2, new_point(3, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = "90 deg - {}".format(angle_param.name)
                
                line3 = lines.addByTwoPoints(line2.endSketchPoint, new_point(5, 1, origin, x_axis, y_axis))
                d = sketch.sketchDimensions.addOffsetDimension(line3, projected_edge, new_point(4.5, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = height_param.name
                ending_half_tail_profile_line = line3
                
                line4 = lines.addByTwoPoints(line3.endSketchPoint, line1.startSketchPoint)
                sketch.geometricConstraints.addPerpendicular(line4, projected_edge)
                
                # full tail
                line1 = lines.addByTwoPoints(new_point(2.5, 0, origin, x_axis, y_axis), new_point(2, 1, origin, x_axis, y_axis))
                sketch.geometricConstraints.addCoincident(line1.startSketchPoint, projected_edge)
                d = sketch.sketchDimensions.addDistanceDimension(projected_edge.startSketchPoint, line1.startSketchPoint,
                                                                 adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                                                 new_point(1.5, -1, origin, x_axis, y_axis))
                d.parameter.expression = "{} / 2 + {}".format(tail_param.name, pin_param.name)
                d = sketch.sketchDimensions.addAngularDimension(projected_edge, line1, new_point(1.5, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = "90 deg - {}".format(angle_param.name)
                
                line2 = lines.addByTwoPoints(line1.endSketchPoint, new_point(3.5, 1, origin, x_axis, y_axis))
                d = sketch.sketchDimensions.addOffsetDimension(line2, projected_edge, new_point(3, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = height_param.name
                full_tail_profile_line = line2
                
                line3 = lines.addByTwoPoints(line2.endSketchPoint, new_point(3, 0, origin, x_axis, y_axis))
                sketch.geometricConstraints.addCoincident(line3.endSketchPoint, projected_edge)
                d = sketch.sketchDimensions.addAngularDimension(line3, projected_edge, new_point(4, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = "90 deg - {}".format(angle_param.name)
                
                line4 = lines.addByTwoPoints(line3.endSketchPoint, line1.startSketchPoint)
                d = sketch.sketchDimensions.addDistanceDimension(line4.startSketchPoint, line4.endSketchPoint,
                                                                 adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                                                 new_point(3, -0.5, origin, x_axis, y_axis))
                d.parameter.expression = tail_param.name
                
                half_tails_profiles = adsk.core.ObjectCollection.create()
                half_tails_profiles.add(find_profile_for_line(starting_half_tail_profile_line))
                half_tails_profiles.add(find_profile_for_line(ending_half_tail_profile_line))
            else:
                line1 = lines.addByTwoPoints(new_point(1, 0, origin, x_axis, y_axis), new_point(0.5, 1, origin, x_axis, y_axis))
                sketch.geometricConstraints.addCoincident(line1.startSketchPoint, projected_edge)
                d = sketch.sketchDimensions.addDistanceDimension(projected_edge.startSketchPoint, line1.startSketchPoint,
                                                                 adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                                                 new_point(0.5, -0.5, origin, x_axis, y_axis))

                if start_type == DovetailStartType.HalfPin:
                    d.parameter.expression = "{} / 2".format(pin_param.name)
                elif start_type == DovetailStartType.FullPin:
                    d.parameter.expression = pin_param.name
                else:
                    raise ValueError("不支持的起始类型：{}".format(start_type))
                
                d = sketch.sketchDimensions.addAngularDimension(projected_edge, line1, new_point(0, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = "90 deg - {}".format(angle_param.name)
                
                line2 = lines.addByTwoPoints(line1.endSketchPoint, new_point(2.5, 1, origin, x_axis, y_axis))
                d = sketch.sketchDimensions.addOffsetDimension(line2, projected_edge, new_point(1.5, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = height_param.name
                full_tail_profile_line = line2
                
                line3 = lines.addByTwoPoints(line2.endSketchPoint, new_point(2, 0, origin, x_axis, y_axis))
                sketch.geometricConstraints.addCoincident(line3.endSketchPoint, projected_edge)
                d = sketch.sketchDimensions.addAngularDimension(line3, projected_edge, new_point(3, 0.5, origin, x_axis, y_axis))
                d.parameter.expression = "90 deg - {}".format(angle_param.name)
                
                line4 = lines.addByTwoPoints(line3.endSketchPoint, line1.startSketchPoint)
                d = sketch.sketchDimensions.addDistanceDimension(line4.startSketchPoint, line4.endSketchPoint,
                                                                 adsk.fusion.DimensionOrientations.AlignedDimensionOrientation,
                                                                 new_point(1.5, -0.5, origin, x_axis, y_axis))
                d.parameter.expression = tail_param.name

            # extrude dovetail
            extruded_dovetail = component.features.extrudeFeatures.addSimple(
                find_profile_for_line(full_tail_profile_line),
                adsk.core.ValueInput.createByString("-1 * {}".format(thickness_param.name)),
                adsk.fusion.FeatureOperations.JoinFeatureOperation)
            
            # multiply dovetails with rectangular pattern
            objects = adsk.core.ObjectCollection.create()
            objects.add(extruded_dovetail)
            
            pattern_spacing_expression = "{} + {}".format(tail_param.name, pin_param.name)
            
            pattern_input = component.features.rectangularPatternFeatures.createInput(
                objects,
                projected_edge,
                adsk.core.ValueInput.createByString(count_param.name),
                adsk.core.ValueInput.createByString(pattern_spacing_expression),
                adsk.fusion.PatternDistanceType.SpacingPatternDistanceType)

            pattern_input.setDirectionTwo(None, adsk.core.ValueInput.createByString("1"), adsk.core.ValueInput.createByString("0"))
            pattern_feature = component.features.rectangularPatternFeatures.add(pattern_input)
            
            # extrude half tails
            if half_tails_profiles:
                component.features.extrudeFeatures.addSimple(
                    half_tails_profiles,
                    adsk.core.ValueInput.createByString("-1 * {}".format(thickness_param.name)),
                    adsk.fusion.FeatureOperations.JoinFeatureOperation)
            
#            if pattern_feature.patternElements.count > 1:
#                face1 = adsk.fusion.BRepFace.cast(pattern_feature.patternElements[0].faces[0])
#                face2 = adsk.fusion.BRepFace.cast(pattern_feature.patternElements[1].faces[0])
#                
#                v = edge.endVertex.geometry.asVector()
#                v.subtract(edge.startVertex.geometry.asVector())
#                
#                v2 = face2.centroid.asVector()
#                v2.subtract(face1.centroid.asVector())
#                
#                #ui.messageBox(str(math.degrees(v.angleTo(v2))))
#                
#                ui.selectEntity(face2)
            
        except:
            if ui:
                ui.messageBox("失败：\n{}".format(traceback.format_exc()))
        
        
        