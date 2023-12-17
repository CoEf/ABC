<<<<<<< HEAD
<<Face Remesh with face mesh>>

MediaPipe의 FaceMesh를 사용하여 얼굴메쉬를 remesh하는 것을 목표로 합니다.


=======
MediaPipe의 FaceMesh를 사용하여 얼굴메쉬를 remesh하는 것을 목표로 합니다.

>>>>>>> 991936b94e417b82adf93a8ebbca4b982ac8c206
<환경 설정>
evaluate.py 와 attachMesh.py는 블렌더 api를 사용하기에 블렌더 스크립트 환경에서 작동합니다.

faceConstruction.py에서는 MediaPipe를 사용하여 블렌더 스크립트 환경에서 지원하지 않습니다.
블렌더 환경에서 동작하는 것이 불가능한 것은 아니나 그 작업이 복잡하여 따로 파이썬 구동환경을 준비해줍니다.



<실행 방법>
evaluate.py는 여러 지표들로 선택된 오브젝트 메쉬의 완전성을 평가합니다. 해당 지표들은 블렌더 코너에서 확인가능합니다.

우선 준비한 오브젝트에 카메라를 얼굴에 놓아 주시고 렌더링을 진행해 주시기 바랍니다.
(카메라 환경은 Orthographic, Orthofraphic scale = 1, 1920x1080 으로 맞춰주세요)

faceConstruction.py의 마지막 줄의 folder_path를 렌더링 된 사진이 있는 폴더위치로 설정한 후 실행하면 설정한 output_folder위치에 얼굴메쉬.obj 이 나타납니다.

준비된 얼굴메쉬.obj 파일을 렌더링시 사용했던 오브젝트가 있는 블렌더환경에서 import해줍니다.
얼굴메쉬.obj 가 선택된 상태에서 attachMesh.py를 실행하면 카메라 위치값에 대응하여 얼굴위치에 메쉬를 부착해 줍니다.
