import bpy
import bmesh
import math
from mathutils import Vector


# ------------------계산에 필요한 함수 정의-------------------------

# Aspect Ratios 계산 함수
def calculate_aspect_ratio(face):
    vertices = [v.co for v in face.verts]
    edge_lengths = [(vertices[i] - vertices[(i + 1) % 3]).length for i in range(3)]
    max_length = max(edge_lengths)
    min_length = min(edge_lengths)
    return max_length / min_length if min_length > 0 else float('inf')


# Skewness 계산 함수
def calculate_skewness(angles):
    theta_max = max(angles)
    theta_min = min(angles)
    skewness = max((theta_max - 60) / (180 - 60), (60 - theta_min) / 60)
    return skewness

# 폴리곤 각도 계산 함수
def calculate_polygon_angles(bm, face):
    angles = []
    vertices = [v.co for v in face.verts]

    num_vertices = len(vertices)
    for i in range(num_vertices):
        current_vertex = vertices[i]
        prev_vertex = vertices[i - 1]
        next_vertex = vertices[(i + 1) % num_vertices]

        vec1 = prev_vertex - current_vertex
        vec2 = next_vertex - current_vertex

        angle = vec1.angle(vec2)
        angles.append(math.degrees(angle))

    return angles


# 삼각형의 면적 계산 함수
def calculate_triangle_area(v1, v2, v3):
    a = (v2 - v1).length
    b = (v3 - v2).length
    c = (v1 - v3).length
    s = (a + b + c) / 2
    return math.sqrt(s * (s - a) * (s - b) * (s - c))

# 인접한 폴리곤들과의 size ratio계산
def calculate_size_ratio_for_polygon(bm, face):
    
    main_area = calculate_triangle_area(*[v.co for v in face.verts])
    max_area = main_area
    min_area = main_area

    # 인접한 폴리곤들의 면적 계산
    for edge in face.edges:
        for linked_face in edge.link_faces:
            if linked_face != face:
                area = calculate_triangle_area(*[v.co for v in linked_face.verts])
                max_area = max(max_area, area)
                min_area = min(min_area, area)

    size_ratio = max_area / min_area if min_area > 0 else float('inf')
    return size_ratio

# Shape factor 계산 함수
def calculate_shape_factor(face):
    # 삼각형의 면적 계산
    vertices = [v.co for v in face.verts]
    area = calculate_triangle_area(*vertices)

    # 외접원 반지름 계산
    a, b, c = (vertices[1] - vertices[0]).length, (vertices[2] - vertices[1]).length, (vertices[0] - vertices[2]).length
    s = (a + b + c) / 2
    radius = (a * b * c) / (4 * math.sqrt(s * (s - a) * (s - b) * (s - c)))

    # 이상적인 삼각형의 면적 (정삼각형)
    ideal_area = (math.sqrt(3) / 4) * radius ** 2

    # Shape Factor 계산
    shape_factor = area / ideal_area if ideal_area > 0 else float('inf')
    return shape_factor


# Max/Min Element 계산 함수
def calculate_max_min_element(bm):
    max_area = 0
    min_area = float('inf')
    max_face_index = -1
    min_face_index = -1

    for face in bm.faces:
        vertices = [v.co for v in face.verts]
        area = calculate_triangle_area(*vertices)

        if area > max_area:
            max_area = area
            max_face_index = face.index
        if area < min_area:
            min_area = area
            min_face_index = face.index

    return max_face_index, min_face_index, max_area, min_area



# 토폴로지 분석(점, 선, 면, 끊어진 선,끊어진 점)
def analyze_topology(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)

    vertices_count = len(bm.verts)
    edges_count = len(bm.edges)
    faces_count = len(bm.faces)
    non_manifold_edges = sum(1 for e in bm.edges if not e.is_manifold)
    loose_verts = sum(1 for v in bm.verts if len(v.link_edges) == 0)

    bm.free()

    return vertices_count, edges_count, faces_count, non_manifold_edges, loose_verts


# 정점 밀도 계산
def calculate_vertex_density(bm, verts, faces):
    total_area = sum(f.calc_area() for f in faces)
    vertex_density = len(verts) / total_area if total_area > 0 else 0
    return vertex_density



# ------------------연산 수행 부분-------------------------

class MESH_OT_calculate(bpy.types.Operator):
    bl_idname = "mesh.calculate_aspect_ratio"
    bl_label = "Calculate Aspect Ratio and Skewness"
    bl_options = {'REGISTER', 'UNDO'}

    # 실행 부분
    def execute(self, context):
        obj = context.active_object     
        
        # 활성 오브젝트인지 확인
        if obj.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a Mesh")
            return {'CANCELLED'}

        # bmesh 생성 및 바운딩
        bm = bmesh.new()
        bm.from_mesh(obj.data)
        bm.transform(obj.matrix_world)  # 월드 좌표계로 변환

        
        # 계산결과를 위한 리스트
        aspect_ratios = {}
        skewness_values = {}
        size_ratios = {}
        shape_factors = {} 
        
        # Edit mode에서의 개별 메쉬 선택시
        if bpy.context.mode == 'EDIT_MESH':
            selected_verts = [v for v in bm.verts if v.select]
            selected_faces = [f for f in bm.faces if f.select]
        else:
            selected_verts = bm.verts
            selected_faces = bm.faces
            
        bmesh.ops.triangulate(bm, faces=bm.faces[:]) # Triangulate
        
        # 계산
        for face in bm.faces:
            
            # Calculate aspect ratio
            aspect_ratio = calculate_aspect_ratio(face)
            aspect_ratios[face.index] = aspect_ratio
            
            # Calculate skewness
            angles = calculate_polygon_angles(bm, face)
            skewness = calculate_skewness(angles)
            skewness_values[face.index] = skewness           
            
            # Calculate size ratio
            size_ratio = calculate_size_ratio_for_polygon(bm, face)
            size_ratios[face.index] = size_ratio
            
            # Calculate shape factor
            shape_factor = calculate_shape_factor(face)
            shape_factors[face.index] = shape_factor
            
        # total value
        total_aspect_ratio = sum(aspect_ratios.values()) / len(aspect_ratios)
        total_skewness = sum(skewness_values.values()) / len(skewness_values)
        total_size_ratio = sum(size_ratios.values()) / len(size_ratios)
        total_shape_factor = sum(shape_factors.values()) / len(shape_factors)
        
        # Calculate max min element    
        max_face_index, min_face_index, max_area, min_area = calculate_max_min_element(bm) 
        
        # Analyze Topology
        topology_result = analyze_topology(obj)
        
        # Calculate Density
        density = calculate_vertex_density(bm, selected_verts, selected_faces) 
            
        bm.free()

        # 결과 저장
        context.scene.mesh_aspect_ratios = str(aspect_ratios)
        context.scene.mesh_skewness_values = str(skewness_values)
        context.scene.mesh_size_ratios = str(size_ratios)
        context.scene.mesh_shape_factors = str(shape_factors)
        
        context.scene.t_aspect_ratios = f'Total_aspect_ratio: {total_aspect_ratio}'
        context.scene.t_skewness_values =  f'Total_skewness: {total_skewness}'
        context.scene.t_size_ratios =  f'Total_size_ratio: {total_size_ratio}'
        context.scene.t_shape_factors =  f'Total_shape_factor: {total_shape_factor}'
        
        context.scene.mesh_max_element = f'Max Element: Face {max_face_index} (Area: {max_area:.2f})'
        context.scene.mesh_min_element = f'Min Element: Face {min_face_index} (Area: {min_area:.2f})'
        
        context.scene.vertices_count = f'Vertices Count: {topology_result[0]}'
        context.scene.edges_count = f'Edges Count: {topology_result[1]}'
        context.scene.faces_count = f'Faces Count: {topology_result[2]}'
        context.scene.non_manifold_edges = f'Non Manifold Edges: {topology_result[3]}'
        context.scene.loose_verts = f'Loose Verts: {topology_result[4]}'
        
        context.scene.vertex_density_report = f"Vertex Density: {density:.2f}"  


        return {'FINISHED'}








# ------------------UI 부분-------------------------

class MESH_PT_panel(bpy.types.Panel):
    bl_label = "Aspect Ratio and Skewness Panel"
    bl_idname = "MESH_PT_aspect_ratio"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tools'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.operator(MESH_OT_calculate.bl_idname, text="Calculate Aspect Ratios and Skewness")
    
        # Aspect Ratios 
        layout.prop(scene, "show_aspect_ratios", text="Show Aspect Ratios")
        if scene.show_aspect_ratios:
            if "mesh_aspect_ratios" in scene:
                aspect_ratios = eval(scene.mesh_aspect_ratios)
                for face_index, ratio in aspect_ratios.items():
                    layout.label(text=f"Face {face_index}: {ratio:.2f}")
            else:
                layout.label(text="No aspect ratios calculated.")

        # Skewness 
        layout.prop(scene, "show_skewness_values", text="Show Skewness Values")
        if scene.show_skewness_values:
            if "mesh_skewness_values" in scene:
                skewness_values = eval(scene.mesh_skewness_values)
                for face_index, skewness in skewness_values.items():
                    layout.label(text=f"Face {face_index} skewness: {skewness:.2f}")
            else:
                layout.label(text="No skewness values calculated.")
                
        # Size Ratios 
        layout.prop(scene, "show_size_ratios", text="Show Size Ratios")
        if scene.show_size_ratios:
            if "mesh_size_ratios" in scene:
                size_ratios = eval(scene.mesh_size_ratios)
                for face_index, size_ratio in size_ratios.items():
                    layout.label(text=f"Face {face_index} Size Ratio: {size_ratio:.2f}")
            else:
                layout.label(text="No size ratios calculated.")

        # Shape Factors 
        layout.prop(scene, "show_shape_factors", text="Show Shape Factors")
        if scene.show_shape_factors:
            if "mesh_shape_factors" in scene:
                shape_factors = eval(scene.mesh_shape_factors)
                for face_index, factor in shape_factors.items():
                    layout.label(text=f"Face {face_index} shape factor: {factor:.2f}")
            else:
                layout.label(text="No shape factors calculated.")
                
                
        # Total
        layout.label(text=context.scene.t_aspect_ratios)
        layout.label(text=context.scene.t_skewness_values)
        layout.label(text=context.scene.t_size_ratios)
        layout.label(text=context.scene.t_shape_factors)
        
        # Max Min Element
        layout.label(text=context.scene.mesh_max_element)
        layout.label(text=context.scene.mesh_min_element)

        # Topology
        layout.label(text=context.scene.vertices_count)
        layout.label(text=context.scene.edges_count)
        layout.label(text=context.scene.faces_count)
        layout.label(text=context.scene.non_manifold_edges)
        layout.label(text=context.scene.loose_verts)
        
        # Density
        layout.label(text=context.scene.vertex_density_report)






# ------------------등록 해제 부분-------------------------
# 등록 및 해제 함수
def register():
    bpy.utils.register_class(MESH_OT_calculate)
    bpy.utils.register_class(MESH_PT_panel)
    
    # 프로퍼티 추가 (계산 + 토클)
    # Aspect_ratios 
    bpy.types.Scene.mesh_aspect_ratios = bpy.props.StringProperty() # aspect ratios 프로퍼티 추가
    bpy.types.Scene.show_aspect_ratios = bpy.props.BoolProperty(name="Show Aspect Ratios", default=True) # 토글 프로퍼티 추가
    
    # Skewness
    bpy.types.Scene.mesh_skewness_values = bpy.props.StringProperty()
    bpy.types.Scene.show_skewness_values = bpy.props.BoolProperty(name="Show Skewness Values", default=True)
    
    # Size Ratios
    bpy.types.Scene.mesh_size_ratios = bpy.props.StringProperty()  
    bpy.types.Scene.show_size_ratios = bpy.props.BoolProperty(name="Show Size Ratios", default=True)  
    
    # Shape Factors
    bpy.types.Scene.mesh_shape_factors = bpy.props.StringProperty()
    bpy.types.Scene.show_shape_factors = bpy.props.BoolProperty(name="Show Shape Factors", default=True)
    
    # total
    bpy.types.Scene.t_aspect_ratios = bpy.props.StringProperty()
    bpy.types.Scene.t_skewness_values = bpy.props.StringProperty()
    bpy.types.Scene.t_size_ratios = bpy.props.StringProperty()
    bpy.types.Scene.t_shape_factors = bpy.props.StringProperty()
    
    # max min element
    bpy.types.Scene.mesh_max_element = bpy.props.StringProperty()
    bpy.types.Scene.mesh_min_element = bpy.props.StringProperty()
    
    # Topology
    bpy.types.Scene.vertices_count = bpy.props.StringProperty()
    bpy.types.Scene.edges_count = bpy.props.StringProperty()
    bpy.types.Scene.faces_count = bpy.props.StringProperty()
    bpy.types.Scene.non_manifold_edges = bpy.props.StringProperty()
    bpy.types.Scene.loose_verts = bpy.props.StringProperty()
    
    # Density
    bpy.types.Scene.vertex_density_report = bpy.props.StringProperty()




def unregister():
    bpy.utils.unregister_class(MESH_OT_calculate)
    bpy.utils.unregister_class(MESH_PT_panel)
    
    # Aspect_ratios
    del bpy.types.Scene.mesh_aspect_ratios
    del bpy.types.Scene.show_aspect_ratios
    
    # Skewness
    del bpy.types.Scene.mesh_skewness_values
    del bpy.types.Scene.show_skewness_values
    
    # Size Ratios
    del bpy.types.Scene.mesh_size_ratios
    del bpy.types.Scene.show_size_ratios
    
    # Shape Factors
    del bpy.types.Scene.mesh_shape_factors
    del bpy.types.Scene.show_shape_factors
    
    # total
    del bpy.types.Scene.t_aspect_ratios 
    del bpy.types.Scene.t_skewness_values 
    del bpy.types.Scene.t_size_ratios 
    del bpy.types.Scene.t_shape_factors 
    
    # max min element
    del bpy.types.Scene.mesh_max_element
    del bpy.types.Scene.mesh_min_element
    
    # Topology
    del bpy.types.Scene.vertices_count
    del bpy.types.Scene.edges_count
    del bpy.types.Scene.faces_count
    del bpy.types.Scene.non_manifold_edges
    del bpy.types.Scene.loose_verts
    
    # Density
    del bpy.types.Scene.vertex_density_report
    


if __name__ == "__main__":
    register()
