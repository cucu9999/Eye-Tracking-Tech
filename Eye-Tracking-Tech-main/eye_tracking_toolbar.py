
import tkinter as tk
from tkinter import ttk
from threading import Thread
import time

# 从你的实际控制文件导入
from Eye_Control import EyeCtrl

ctrl = EyeCtrl('COM5')  
#ctrl = EyeCtrl('/dev/ttyACM0')  # 替换为你的串口设备路径

# 初始值        创建字典
initial_value_dict = {
    'eyelid_upper_left': 0.30,
    'eyelid_upper_right': 0.30,
    'eyelid_lower_left': 0.63,
    'eyelid_lower_right': 0.63,
    'eyeball_horizontal': 0.50,
    'eyeball_vertical': 0.29
}

# 控制的参数及初始值
servo_values = {
    'eyelid_upper_left': initial_value_dict['eyelid_upper_left'],
    'eyelid_upper_right': initial_value_dict['eyelid_upper_right'],
    'eyelid_lower_left': initial_value_dict['eyelid_lower_left'],
    'eyelid_lower_right': initial_value_dict['eyelid_lower_right'],
    'eyeball_horizontal': initial_value_dict['eyeball_horizontal'],
    'eyeball_vertical': initial_value_dict['eyeball_vertical'],
}

# 实时同步线程
def update_ctrl_loop():
    while True:
        ctrl.eyelid_upper_left = servo_values['eyelid_upper_left']
        ctrl.eyelid_upper_right = servo_values['eyelid_upper_right']
        ctrl.eyelid_lower_left = servo_values['eyelid_lower_left']
        ctrl.eyelid_lower_right = servo_values['eyelid_lower_right']
        ctrl.eyeball_horizontal = servo_values['eyeball_horizontal']
        ctrl.eyeball_vertical = servo_values['eyeball_vertical']
        ctrl.send()
        time.sleep(0.03)

# GUI 界面
def create_gui():
    root = tk.Tk()
    root.title("表情机器人实时控制")

    sliders = [
        ('左上眼皮 (eyelid_upper_left)', 'eyelid_upper_left'),
        ('右上眼皮 (eyelid_upper_right)', 'eyelid_upper_right'),
        ('左下眼皮 (eyelid_lower_left)', 'eyelid_lower_left'),
        ('右下眼皮 (eyelid_lower_right)', 'eyelid_lower_right'),
        ('眼球平动 (eyeball_horizontal)', 'eyeball_horizontal'),
        ('眼球竖动 (eyeball_vertical)', 'eyeball_vertical'),
    ]

    slider_widgets = {}

    for i, (label, key) in enumerate(sliders):
        ttk.Label(root, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='w')

        # 当前值显示
        val_label = ttk.Label(root, text=f"{servo_values[key]:.2f}")
        val_label.grid(row=i, column=2, padx=5)

        # 滑动条
        scale = ttk.Scale(
            root, from_=0.0, to=1.0, orient='horizontal', length=300,
            command=lambda val, k=key, vlabel=val_label: on_scale_change(k, val, vlabel)
        )
        scale.set(servo_values[key])
        scale.grid(row=i, column=1, padx=5, pady=5)

        slider_widgets[key] = (scale, val_label)

    # 复位按钮
    def reset_all():
        for key, (scale, label) in slider_widgets.items():

            servo_values[key] = initial_value_dict[key]
            scale.set(initial_value_dict[key])
            label.config(text=f"{initial_value_dict[key]:.2f}")

    reset_btn = ttk.Button(root, text="复位所有", command=reset_all)
    reset_btn.grid(row=len(sliders), column=0, columnspan=3, pady=10)

    root.mainloop()

# 滑动条回调
def on_scale_change(key, val, label):
    val = float(val)
    servo_values[key] = val
    label.config(text=f"{val:.2f}")

# 启动控制线程
Thread(target=update_ctrl_loop, daemon=True).start()

# 启动 GUI
create_gui()
