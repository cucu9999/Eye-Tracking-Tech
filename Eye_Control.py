from serial import *
import time
import random
import math

# TODO: 从xml文件直接读取配置
class Servo:
    def __init__(self, id, jdStart, jdMax, jdMin, fScale, fOffSet, pos):
        self.id = id
        self.jdStart = jdStart
        self.jdMax = jdMax
        self.jdMin = jdMin
        self.fScale = fScale
        self.fOffSet = fOffSet
        self.pos = pos

eyelid_lower_left          = Servo(24, 90, 108, 59, 11.1, 0, 1)                     # 左下眨眼   + eyelid_lower_left
eyelid_upper_left      = Servo( 25, 90, 144, 67, 11.1, 0, 0)                        # 左上眨眼  + eyelid_upper_left
eyeball_horizontal      = Servo( 27, 90, 126, 54, 11.1, 0, 0)                       # 左右眼平  + eyeball_horizontal

eyelid_lower_right         = Servo( 22, 90, 108, 59, 11.1, 0, 1)                    # 右下眨眼  + eyelid_lower_right
eyelid_upper_right     = Servo( 23, 90, 144, 67, 11.1, 0, 0)                        # 右上眨眼  + eyelid_upper_right
eyeball_vertical     = Servo( 26, 90, 126, 75, 11.1, 0, 0)                          # 左右眼竖  + eyeball_vertical


servos = [eyelid_lower_left, eyelid_upper_left, eyeball_horizontal, 
          eyelid_lower_right, eyelid_upper_right, eyeball_vertical, 
]


class EyeCtrl(Serial):
    #*args, **kwargs 这种写法代表这个方法接受任意个数的参数
    def __init__(self, arg, *args, **kwargs):
        super().__init__(arg, *args, **kwargs)
        if self.is_open:
            print('Open Success')
        else:
            print('Open Error')

        self.eyelid_lower_left          = 0.5
        self.eyelid_upper_left      = 0.5
        self.eyeball_horizontal      = 0.5

        self.eyelid_lower_right         = 0.5
        self.eyelid_upper_right     = 0.5
        self.eyeball_vertical     = 0.5

    @property
    def msgs(self):
        return [
            self.eyelid_lower_left, self.eyelid_upper_left, self.eyeball_horizontal, 
            self.eyelid_lower_right, self.eyelid_upper_right, self.eyeball_vertical, 
        ]

    def send(self):
        # print(self.msgs)
        head = 0xaa
        num=0x00
        end=0x2f

        frameData = [head, num]

        servo_num = 0
        for node, servo in zip(self.msgs, servos):
            node = servo.jdMin+node*(servo.jdMax-servo.jdMin)
            if node and node != servo.pos:                                              # 目标位置改变
                if node != 0:                                                           # msg 没有值
                    if node > servo.jdMax:                                              # 限幅
                        node = servo.jdMax
                    if node < servo.jdMin:
                        node = servo.jdMin
                    servo.pos = node
                    node = int((node + servo.fOffSet) * servo.fScale) + 500
                    pos_l = node & 0xFF
                    pos_h = (node >> 8) & 0xFF
                    id = servo.id & 0xFF
                    frameData.extend([id, pos_h, pos_l])
                    servo_num += 1
        if servo_num == 0:
            return
        num=servo_num
        frameData[1] = num
        frameData.extend([end])

        if self.is_open:
            self.write(frameData)

#直接执行这个.py文件运行下边代码，import到其他脚本中下边代码不会执行
if __name__ == '__main__':

    # ctrl = HeadCtrl('COM6')                                                           # windows
    ctrl = EyeCtrl('/dev/ttyACM0')                                                     # ubuntu

    ctrl.eyelid_upper_right = 0.30                                                  # 右上眼皮      向下闭眼 [0, 0.30 , 1] 向上张开
    ctrl.eyelid_upper_left = 0.30                                                   # 左上眼皮      向上张开 [0, 0.30,  1] 向下闭眼

    ctrl.eyelid_lower_right = 0.63                                                  # 右下眼皮      向下张开 [0, 0.63, 1] 向上闭眼
    ctrl.eyelid_lower_left = 0.63                                                   # 左下眼皮      向上闭眼 [0, 0.63,  1] 向下张开

    ctrl.eyeball_horizontal = 0.50                                                  # 眼球平动      右[0, 0.50, 1] 左
    ctrl.eyeball_vertical = 0.29                                                    # 眼球竖动      下[0, 0.29, 1] 上
    print(ctrl.msgs)
    ctrl.send()


    direction = [1, 1]

    while True:
        ## -------------------------------保持初始-------------------------------
        # ctrl.eyelid_upper_right = 0.30                      # 右上眼皮      向下闭眼 [0, 0.30 , 1] 向上张开
        # ctrl.eyelid_upper_left = 0.30                       # 左上眼皮      向上张开 [0, 0.30,  1] 向下闭眼

        # ctrl.eyelid_lower_right = 0.63                      # 右下眼皮      向下张开 [0, 0.63, 1] 向上闭眼
        # ctrl.eyelid_lower_left = 0.63                       # 左下眼皮      向上闭眼 [0, 0.63,  1] 向下张开

        # ctrl.eyeball_horizontal = 0.50                      # 眼球平动      右[0, 0.50, 1] 左
        # ctrl.eyeball_vertical = 0.29                        # 眼球竖动      下[0, 0.29, 1] 上

        ## -------------------------------正弦运动-------------------------------
        ctrl.eyelid_upper_right -= 0.01 * direction[0]                                # 右上眼皮
        ctrl.eyelid_upper_left -= 0.01 * direction[0]                                 # 左上眼皮
        ctrl.eyelid_lower_right += 0.01 * direction[0]                                # 右下眼皮
        ctrl.eyelid_lower_left += 0.01 * direction[1]                                 # 左下眼皮

        if (ctrl.eyelid_upper_right  >= 1 or ctrl.eyelid_upper_right <= 0):
            direction[0] *= -1
        if (ctrl.eyelid_upper_left  >= 1 or ctrl.eyelid_upper_left <= 0):
            direction[0] *= -1
        if (ctrl.eyelid_lower_right  >= 1 or ctrl.eyelid_lower_right <= 0):
            direction[0] *= -1
        if (ctrl.eyelid_lower_left >= 1 or ctrl.eyelid_lower_left <= 0):
            direction[1] *= -1

        # print(ctrl.msgs)
        ctrl.send()
        time.sleep(0.01)