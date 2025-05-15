import os
import cv2
import h5py
import time
import numpy as np
from datetime import datetime

class WriteManager_HDF5:
    def __init__(self, hdf5_path, chunk_size=60, compression_level=5):
        self.hdf5_path = os.path.abspath(hdf5_path)
        self.chunk_size = chunk_size
        self.compression_level = compression_level
        self.dataset = None
        self.total_written = 0
        self.hdf5_file = None

    def _initialize_if_needed(self, first_frame):
        if self.dataset is not None:
            return

        self.hdf5_file = h5py.File(self.hdf5_path, 'a')

        height, width, _ = first_frame.shape
        maxshape = (None, height, width, 3)
        chunks = (self.chunk_size, height, width, 3)

        obs_group = self.hdf5_file.require_group("observations")
        img_group = obs_group.require_group("images")
        if 'top' not in img_group:
            self.dataset = img_group.create_dataset(
                'top',
                shape=(0, height, width, 3),
                maxshape=maxshape,
                chunks=chunks,
                dtype='uint8',
                compression='gzip',
                compression_opts=self.compression_level
            )
        else:
            self.dataset = img_group['top']

        if 'top_timestamps' not in img_group:
            img_group.create_dataset(
                'top_timestamps',
                shape=(0,),
                maxshape=(None,),
                dtype='float64',
                chunks=True
            )

        if 'qpos' not in obs_group:
            obs_group.create_dataset('qpos', shape=(0,), maxshape=(None,), dtype='float32')
        if 'qvel' not in obs_group:
            obs_group.create_dataset('qvel', shape=(0,), maxshape=(None,), dtype='float32')

        if 'action' not in self.hdf5_file:
            self.hdf5_file.create_dataset(
                'action',
                shape=(0, 3),  # x, y, timestamp
                maxshape=(None, 3),
                dtype='float32',
                chunks=True
            )

        self.hdf5_file.attrs['created'] = datetime.now().isoformat()
        self.hdf5_file.attrs['color_space'] = 'BGR'
        self.hdf5_file.attrs['resolution'] = f"{width}x{height}"
        self.hdf5_file.attrs['fps'] = 30

        print("HDF5 数据集初始化完成")

    def write_top_image_with_timestamp(self, image):
        self._initialize_if_needed(image)

        obs_group = self.hdf5_file['observations']
        img_group = obs_group['images']
        ds = img_group['top']
        ts_ds = img_group['top_timestamps']

        idx = ds.shape[0]
        ds.resize((idx + 1, *ds.shape[1:]))
        ds[idx] = image

        ts = time.time()
        ts_ds.resize((idx + 1,))
        ts_ds[idx] = ts

        self.hdf5_file.flush()

    def write_eye_action(self, param_array):
        self._initialize_if_needed(np.zeros((10, 10, 3), dtype=np.uint8))  # dummy frame

        param_array = np.asarray(param_array, dtype='float32')
        if param_array.ndim == 1:
            param_array = param_array[np.newaxis, :]

        timestamp = np.full((param_array.shape[0], 1), time.time(), dtype='float32')
        combined = np.concatenate([param_array, timestamp], axis=1)

        ds = self.hdf5_file['action']
        idx = ds.shape[0]
        ds.resize((idx + combined.shape[0], 3))
        ds[idx:idx + combined.shape[0]] = combined
        self.hdf5_file.flush()

    def write_eye_action_with_timestamp(self, param_array):
        self.write_eye_action(param_array)

    def write_batch(self, frames):
        if not frames:
            print("没有帧可写入。")
            return

        frames = np.asarray(frames)
        if frames.ndim == 3:
            frames = frames[np.newaxis, ...]

        self._initialize_if_needed(frames[0])

        new_total = self.total_written + frames.shape[0]
        self.dataset.resize((new_total, *self.dataset.shape[1:]))
        self.dataset[self.total_written:new_total] = frames
        self.total_written = new_total

        print(f"已写入 {frames.shape[0]} 帧，当前总帧数: {self.total_written}")

    def __del__(self):
        if hasattr(self, 'hdf5_file') and self.hdf5_file:
            self.hdf5_file.flush()
            self.hdf5_file.close()
            self.hdf5_file = None


if __name__ == "__main__":
    print("测试 WriteManager_HDF5 写入功能")

    test_path = "test_data.h5"
    writer = WriteManager_HDF5(test_path)

    # 构造模拟数据
    dummy_images = [np.full((240, 320, 3), i * 50, dtype=np.uint8) for i in range(3)]
    dummy_actions = [[i * 0.1, i * 0.2] for i in range(3)]

    for img, action in zip(dummy_images, dummy_actions):
        writer.write_top_image_with_timestamp(img)
        writer.write_eye_action(action)

    if writer.hdf5_file is not None:
        writer.hdf5_file.flush()
        writer.hdf5_file.close()
        writer.hdf5_file = None

    print("\n📂 HDF5 文件结构：")
    def print_structure(name, obj):
        if isinstance(obj, h5py.Dataset):
            print(f"📄 {name} | shape={obj.shape}, dtype={obj.dtype}")
        elif isinstance(obj, h5py.Group):
            print(f"📁 {name}")

    with h5py.File(test_path, 'r') as f:
        f.visititems(print_structure)

    try:
        os.remove(test_path)
        print(f"\n测试完成，已自动删除文件：{test_path}")
    except Exception as e:
        print(f"无法删除测试文件：{e}")
