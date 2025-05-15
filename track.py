import cv2
import time
import datetime
import numpy as np
from det_face_mediapipe import FaceMeshDetector
from Eye_Control import EyeCtrl
from writer_hdf5 import WriteManager_HDF5

def main():
    face_mesh_detector = FaceMeshDetector()
    eye_ctrl = EyeCtrl('COM5') 

    # 生成带时间戳的新文件名
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    hdf5_path = f"output_record_{now_str}.h5"

    writer = None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    while True:
        ret, frame = cap.read()
        if not ret:
            print("读取摄像头画面失败")
            break

        cv2.imshow("frame", frame)

        # 获取人脸关键点
        landmarks, blendshapes, rotation_matrix = face_mesh_detector.get_results(frame)

        if landmarks:
            try:
                # 初始化写入器
                if writer is None:
                    writer = WriteManager_HDF5(hdf5_path)

                # 计算人脸位置
                face_center_x = (landmarks[33].x + landmarks[263].x) / 2
                face_center_y = (landmarks[33].y + landmarks[263].y) / 2

                # 控制眼球偏移
                horizontal_offset = max(0.0, min(1.0, (0.7 - face_center_x) * 2.5))
                vertical_offset = max(0.0, min(1.0, (0.7 - face_center_y) * 3.0))

                eye_ctrl.eyeball_horizontal = horizontal_offset
                eye_ctrl.eyeball_vertical = vertical_offset
                eye_ctrl.send()

                print(f"👁️ 控制: 水平={horizontal_offset:.2f}, 竖直={vertical_offset:.2f}")

                # 写入图像帧与时间戳
                writer.write_top_image_with_timestamp(frame)

                # 写入动作和动作时间戳
                action = np.array([horizontal_offset, vertical_offset], dtype=np.float32)
                writer.write_eye_action_with_timestamp(action)

            except Exception as e:
                print(f"[控制伺服异常] {e}")
        else:
            print("😐 没检测到人脸 → 不写入数据")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if writer is not None:
        del writer  

if __name__ == "__main__":
    main()
