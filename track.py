import cv2
from det_face_mediapipe import FaceMeshDetector
from Eye_Control import EyeCtrl

def main():
    face_mesh_detector = FaceMeshDetector()
    eye_ctrl = EyeCtrl('COM5')  

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ 无法打开摄像头")
        return

    # 摄像头画面宽高
    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ 读取摄像头画面失败")
            break

        cv2.imshow("frame", frame)

        # 获取人脸关键点
        landmarks, blendshapes, rotation_matrix = face_mesh_detector.get_results(frame)

        if landmarks:
            try:
                # 计算人脸的水平和竖直位置，跟踪人脸移动
                face_center_x = (landmarks[33].x + landmarks[263].x) / 2  # 取左、右眼的水平中点
                face_center_y = (landmarks[33].y + landmarks[263].y) / 2  # 取左、右眼的竖直中点

                # 控制眼球水平和竖直位置
                horizontal_offset = max(0.0, min(1.0, (0.7 - face_center_x) * 2.5))
                vertical_offset = max(0.0, min(1.0, (0.7 - face_center_y) * 3.0))

                eye_ctrl.eyeball_horizontal = horizontal_offset
                eye_ctrl.eyeball_vertical = vertical_offset
                eye_ctrl.send()

                print(f"👁️ 控制:眼球水平:{horizontal_offset:.2f} 竖直:{vertical_offset:.2f}")

            except Exception as e:
                print(f"[控制伺服异常] {e}")
        else:
            print("😐 没检测到人脸")

        # 无论是否检测到人脸都显示画面
        # cv2.imshow("Face Tracking", cv2.flip(frame, 1))

        # 按 q 退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
