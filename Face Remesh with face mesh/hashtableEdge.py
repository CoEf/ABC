import cv2
import mediapipe as mp
import os

# MediaPipe Face Mesh의 연결 인덱스
FACE_MESH_CONNECTIONS = mp.solutions.face_mesh.FACEMESH_TESSELATION

class Vertex:
    def __init__(self, id, x, y, z):
        self.id = id
        self.x = x
        self.y = y
        self.z = z

class Face:
    def __init__(self, vertices):
        self.vertices = vertices

def create_edge_hash_table():
    edge_hash_table = {}
    for connection in FACE_MESH_CONNECTIONS:
        idx1, idx2 = connection

        if idx1 not in edge_hash_table:
            edge_hash_table[idx1] = []
        edge_hash_table[idx1].append(idx2)

        # 양방향 연결을 고려하고 싶다면 아래 코드를 활성화하세요.
        # if idx2 not in edge_hash_table:
        #     edge_hash_table[idx2] = []
        # edge_hash_table[idx2].append(idx1)

    return edge_hash_table

def vector_subtract(v1, v2):
    return (v1.x - v2.x, v1.y - v2.y, v1.z - v2.z)

def cross_product(v1, v2):
    x = v1[1] * v2[2] - v1[2] * v2[1]
    y = v1[2] * v2[0] - v1[0] * v2[2]
    z = v1[0] * v2[1] - v1[1] * v2[0]
    return (x, y, z)

def dot_product(v1, v2):
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]

def create_faces(vertices, edge_hash_table):
    faces = []
    used_edges = set()
    existing_faces = set()  # 이미 생성된 면을 추적하기 위한 집합

    for v in vertices:
        if v.id not in edge_hash_table:
            continue

        for next_vertex_id in edge_hash_table[v.id]:
            if (v.id, next_vertex_id) in used_edges:
                continue

            if next_vertex_id not in edge_hash_table:
                continue

            for third_vertex_id in edge_hash_table[next_vertex_id]:
                if third_vertex_id == v.id or (next_vertex_id, third_vertex_id) in used_edges:
                    continue

                next_vertex = vertices[next_vertex_id]
                third_vertex = vertices[third_vertex_id]

                # 정점 ID를 정렬하여 면의 중복을 확인합니다.
                sorted_vertex_ids = tuple(sorted([v.id, next_vertex_id, third_vertex_id]))

                if v.id in edge_hash_table[third_vertex_id]: # 면 완성 확인
                    if sorted_vertex_ids not in existing_faces: # 면 중복 확인
                        faces.append(Face([v, next_vertex, third_vertex]))
                        used_edges.add((v.id, next_vertex_id))
                        existing_faces.add(sorted_vertex_ids)
                        break

    return faces


def get_face_mesh_coordinates(image):
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)
    results = face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    if results.multi_face_landmarks:
        return results.multi_face_landmarks[0].landmark
    else:
        print("Face not detected.")
        return None

def export_landmarks_to_obj(landmarks, faces, filename):
    with open(filename, 'w') as file:
        # 정점 데이터 작성
        for landmark in landmarks:
            # 1920 x 1080, orthographic Scale = 1 일 때 블렌더 3d좌표계에 맞추기 위해 조정을 해줍니다.
            x = (landmark.x - 0.5) * 1
            y = (landmark.y - 0.5) * -0.5625
            z = -landmark.z
            file.write(f"v {x} {y} {z}\n")

        # 면 데이터 작성
        for face in faces:
            vertices = face.vertices
            # OBJ 파일의 인덱스는 1부터 시작하므로 1을 더합니다.
            file.write(f"f {vertices[0].id + 1} {vertices[1].id + 1} {vertices[2].id + 1}\n")


# 기존의 process_folder 함수에서 export_landmarks_to_obj 호출 부분을 수정합니다.
def process_folder(folder_path, output_folder):
    for filename in os.listdir(folder_path):
        if filename.endswith(".png"):
            image_path = os.path.join(folder_path, filename)
            image = cv2.imread(image_path)
            landmarks = get_face_mesh_coordinates(image)

            # 해시 테이블 생성 
            edge_hash_table = create_edge_hash_table()
            
            if landmarks:
                # Vertex 객체 리스트 생성
                vertices = [Vertex(i, lm.x, lm.y, lm.z) for i, lm in enumerate(landmarks)]
                # 면 생성
                faces = create_faces(vertices, edge_hash_table)

                output_filename = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.obj")
                export_landmarks_to_obj(landmarks, faces, output_filename)



# 렌더링된 이미지가 저장된 폴더 경로
folder_path = 'C:\\Project Result\\Render Result'
output_folder = 'C:\\Project Result\\Exported Landmarks'
process_folder(folder_path, output_folder)
