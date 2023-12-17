import bpy
import bmesh
from mathutils import Vector

# 선택된 오브젝트를 가져옵니다
obj = bpy.context.active_object

# 카메라 위치를 가져옵니다
camera = bpy.context.scene.camera
camera_location = camera.location

# 오브젝트를 카메라 위치로 이동
obj.location = camera_location

# 각 정점에서 카메라 방향으로 레이를 발사
mesh = obj.data
bm = bmesh.new()
bm.from_mesh(mesh)
bm.verts.ensure_lookup_table()

depsgraph = bpy.context.evaluated_depsgraph_get()
ray_direction = camera.matrix_world.to_3x3() @ Vector((0, 0, -1))

# 닿지 않은 정점들을 저장할 리스트
unhit_verts = []

for v in bm.verts:
    ray_origin = obj.matrix_world @ v.co  # 오브젝트의 월드 좌표로 변환
    hit, location, normal, index, hit_obj, matrix = bpy.context.scene.ray_cast(
        depsgraph, ray_origin, ray_direction)

    # 자신의 오브젝트에 닿으면 추가 레이캐스팅 수행
    while hit and hit_obj == obj:
        ray_origin = location + ray_direction * 0.0001  # 약간 이동하여 다시 레이캐스팅
        hit, location, normal, index, hit_obj, matrix = bpy.context.scene.ray_cast(
            depsgraph, ray_origin, ray_direction)

    if hit and hit_obj.type == 'MESH':
        # 레이가 메쉬 오브젝트에 닿으면 정점 위치 업데이트
        v.co = obj.matrix_world.inverted() @ location  # 월드 좌표를 로컬 좌표로 변환
    else:
        # 닿지 않은 정점 또는 메쉬 오브젝트가 아닌 경우에 대한 처리
        unhit_verts.append(v)
        
# 닿지 않은 정점들을 같은 면을 공유하는 정점들의 중간 위치로 이동
for v in unhit_verts:
    linked_verts = [edge.other_vert(v) for edge in v.link_edges]
    if linked_verts:
        avg_pos = sum((vert.co for vert in linked_verts), Vector()) / len(linked_verts)
        v.co = avg_pos
        
# 변경 사항을 메쉬에 적용
bm.to_mesh(mesh)
bm.free()

# Shrinkwrap 모디파이어를 추가합니다
shrinkwrap_modifier = obj.modifiers.new(name="Shrinkwrap", type='SHRINKWRAP')

# 타겟 오브젝트 설정 (이 예제에서는 타겟 오브젝트를 수동으로 설정해야 합니다)
# 예를 들어, 타겟 오브젝트의 이름이 "TargetObject"라고 가정합니다
target_object_name = "Object_13"
shrinkwrap_modifier.target = bpy.data.objects[target_object_name]

# Shrinkwrap 모디파이어 적용
# 주의: 실제 모델링 작업에서는 모디파이어를 적용하기 전에 필요한 경우 백업을 해야 합니다
bpy.ops.object.modifier_apply(modifier=shrinkwrap_modifier.name)