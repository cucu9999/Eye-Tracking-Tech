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

    eyeball_horizontal_init = eye_ctrl.eyeball_horizontal
    eyeball_vertical_init = eye_ctrl.eyeball_vertical

    # 生成带时间戳的新文件名
    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    hdf5_path = f"output_record_{now_str}.h5"

    writer = None

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return
    
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 2560)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # 读取一帧以获取分辨率
    ret, frame = cap.read()
    if not ret or frame is None:
        print("无法读取摄像头帧")
        return
    # 只使用左边图像
    frame = frame[:, :1280]
    frame_height, frame_width = frame.shape[:2]

    # 图像中眼球注视点位置
    eyeball_px_x = int(eyeball_horizontal_init * frame_width)
    eyeball_px_y = int(eyeball_vertical_init * frame_height)

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("读取摄像头画面失败")
            break

         # 截取左边画面
        frame = frame[:, :1280]

        cv2.imshow("Left Camera", frame)
        
        # 转换BGR到RGB，给detector用
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        landmarks, blendshapes, rotation_matrix = face_mesh_detector.get_results(frame_rgb)

        if landmarks:
            try:
                # 初始化写入器
                if writer is None:
                    writer = WriteManager_HDF5(hdf5_path)

                # 计算人脸中心像素坐标
                face_center_x_norm = (landmarks[33].x + landmarks[263].x) / 2
                face_center_y_norm = (landmarks[33].y + landmarks[263].y) / 2
                face_center_x = int(face_center_x_norm * frame_width)
                face_center_y = int(face_center_y_norm * frame_height)

                # 差量计算：人脸位置与眼球初始点的偏移（像素）
                dx = face_center_x - eyeball_px_x
                dy = face_center_y - eyeball_px_y

                # 归一化差量
                dx_norm = -dx / (frame_width / 2)
                dy_norm = -dy / (frame_height / 2)

                # 灵敏度控制
                sensitivity = 0.8
                horizontal_offset = np.clip(eyeball_horizontal_init + dx_norm * sensitivity, 0.0, 1.0)
                vertical_offset = np.clip(eyeball_vertical_init + dy_norm * sensitivity, 0.0, 1.0)

                # 控制伺服
                eye_ctrl.eyeball_horizontal = horizontal_offset
                eye_ctrl.eyeball_vertical = vertical_offset
                eye_ctrl.send()

                print(f"👁️ 控制: 水平={horizontal_offset:.2f}, 竖直={vertical_offset:.2f}")

                # 写入图像帧与时间戳
                # writer.write_top_image_with_timestamp(frame)

                # 写入动作和动作时间戳
                action = np.array([horizontal_offset, vertical_offset], dtype=np.float32)
                # writer.write_eye_action_with_timestamp(action)

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
