import time
import dynamixel_sdk
import motors.consts


# ---------------------------------------------------------------------------- #
# https://emanual.robotis.com/docs/en/dxl/x/xm430-w210/
# https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/api_reference/python/python_porthandler/#python

DEVICE_NAME = "/dev/ttyUSB0"
PROTOCOL_VERSION = 2.0

BAUDRATE = 57600

ARM_OPERATING_MODE = 4 # Extended Position Control Mode
MOTOR_OPERATING_MODE = 1 # Velocity Control Mode

ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_GOAL_VELOCITY = 104
ADDR_GOAL_POS = 116
ADDR_PRESENT_VELOCITY = 128
ADDR_PRESENT_POS = 132
ADDR_ERROR_CODE = 70
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
ARM_DYNAMIXEL_IDS = { # ARM_DYNAMIXEL_IDS[joint] = [controller_id, arm_id]
    "j1": [5, 8],
    "j2": [6, 9],
    "j3": [7, 10],	
}
ARM_REST_POSES = {
    "j1": 3072,
    "j2": 1024,
    "j3": 800,
}
# ---------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------- #
MOTOR_DYNAMIXEL_IDS = { # MOTOR_DYNAMIXEL_IDS[side] = [id1, id2]
    "left": [1, 3],
    "right": [2, 4],
}
ORIENTATIONS = { # ORIENTATIONS[side] = direction multiplier
    "left": 1,
    "right": -1,
}
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
class DynamixelController:
    # ------------------------------------------------------------------------ #
    def __init__(self):
        self.port_handler = dynamixel_sdk.PortHandler(DEVICE_NAME)
        self.packet_handler = dynamixel_sdk.PacketHandler(PROTOCOL_VERSION)

        if self.port_handler.openPort():
            print("Succeeded to open the port")
        else:
            print("Failed to open the port.")
        if self.port_handler.setBaudRate(BAUDRATE):
            print("Succeeded to change the baudrate")
        else:
            print("Failed to change the baudrate.")


        self.controller_statuses = { # controller_statuses[id] = #
            "j1": 0,
            "j2": 0,
            "j3": 0,
        }
        self.arm_statuses = { # arm_statuses[id] = #
            "j1": 0,
            "j2": 0,
            "j3": 0,
        }

        self.speeds = { # speeds[side] = %
            "left": 0,
            "right": 0,
        }
        self.motor_statuses = { # motor_statuses[side] = %
            "left": 0,
            "right": 0,
        }
        self.velocity_limit = motors.consts.STATE_FROM_SERVER["velocity_limit"]["value"]
        self.to_writes = { # to_writes[id] = #
            1: 0,
            2: 0,
            3: 0,
            4: 0,
        }
        self.has_wrote = { # has_wrote[id] = #
            1: 0,
            2: 0,
            3: 0,
            4: 0,
        }
        self.min_writes = motors.consts.STATE_FROM_SERVER["motor_writes"]

    def close(self):
        self.update_speeds({
            "left": 0,
            "right": 0,
        })
        for _ in range(motors.consts.MAX_WRITES):
            self.try_write_speeds()

        time.sleep(motors.consts.CLOSE_WAIT_TIME)
        self.set_torque_status(False)
        time.sleep(motors.consts.CLOSE_WAIT_TIME)
        
        self.port_handler.closePort()

    def set_torque_status(self, status, id):
        status_code = 1 if status else 0
        dxl_comm_result, dxl_error = self.packet_handler.write1ByteTxRx(self.port_handler, id, ADDR_TORQUE_ENABLE, status_code)
        if dxl_comm_result != dynamixel_sdk.COMM_SUCCESS:
            print(f"dxl_comm_result error {id} {self.packet_handler.getTxRxResult(dxl_comm_result)}")
        elif dxl_error != 0:
            print(f"dxl_error error {id} {self.packet_handler.getRxPacketError(dxl_error)}")

    def set_torque_status_all(self, status):
        ids = [id for id in ARM_DYNAMIXEL_IDS.values()] + [id for side_ids in MOTOR_DYNAMIXEL_IDS.values() for id in side_ids]
        for id in ids:
            self.set_torque_status(status, id)
    # ------------------------------------------------------------------------ #

    # ------------------------------------------------------------------------ #
    def set_up_arm(self):
        for joint, joint_ids in ARM_DYNAMIXEL_IDS.items():
            for joint_id in joint_ids:
                self.packet_handler.write1ByteTxRx(self.port_handler, joint_id, ADDR_OPERATING_MODE, ARM_OPERATING_MODE)
                self.set_torque_status(True, joint_id)

                rest_pos = ARM_REST_POSES[joint]
                self.packet_handler.write4ByteTxRx(self.port_handler, joint_id, ADDR_GOAL_POS, rest_pos)

            controller_id = joint_ids[0]
            self.set_torque_status(False, controller_id)

    def mirror_and_update_arm_status(self):
        for joint, joint_ids in ARM_DYNAMIXEL_IDS.items():
            controller_id, arm_id = joint_ids

            controller_pos, _dxl_comm_result, _dxl_error = self.packet_handler.read4ByteTxRx(self.port_handler, controller_id, ADDR_PRESENT_POS)
            self.packet_handler.write4ByteTxRx(self.port_handler, arm_id, ADDR_GOAL_POS, controller_pos)
            arm_pos,        _dxl_comm_result, _dxl_error = self.packet_handler.read4ByteTxRx(self.port_handler, arm_id,        ADDR_PRESENT_POS)

            self.arm_statuses[joint] = arm_pos
            self.controller_statuses[joint] = controller_pos
    # ------------------------------------------------------------------------ #

    # ------------------------------------------------------------------------ #
    def set_up_motors(self):
        for side_ids in MOTOR_DYNAMIXEL_IDS.values():
            for id in side_ids:
                self.packet_handler.write1ByteTxRx(self.port_handler, id, ADDR_OPERATING_MODE, MOTOR_OPERATING_MODE)
                self.set_torque_status(True, id)

    def update_speeds(self, speeds):
        self.speeds = speeds
        for id in self.to_writes:
            self.to_writes[id] = self.min_writes
            self.has_wrote[id] = 0

    def try_write_speeds(self):
        for side, side_ids in MOTOR_DYNAMIXEL_IDS.items():
            speed = self.speeds[side]
            orientation = ORIENTATIONS[side]
            power = int(speed * orientation * self.velocity_limit)

            for id in side_ids:
                if self.to_writes[id] > 0 and self.has_wrote[id] < motors.consts.MAX_WRITES:
                    dxl_comm_result, dxl_error = self.packet_handler.write4ByteTxRx(self.port_handler, id, ADDR_GOAL_VELOCITY, power)
                    if dxl_comm_result != dynamixel_sdk.COMM_SUCCESS:
                        print(f"dxl_comm_result error {id} {self.packet_handler.getTxRxResult(dxl_comm_result)}")
                    elif dxl_error != 0:
                        print(f"dxl_error error {id} {self.packet_handler.getRxPacketError(dxl_error)}")
                    else:
                        self.to_writes[id] -= 1
                    
                    self.has_wrote[id] += 1

    def update_motor_status_and_check_errors(self):
        for side, side_ids in MOTOR_DYNAMIXEL_IDS.items():
            orientation = ORIENTATIONS[side]
            self.motor_statuses[side] = 0

            for id in side_ids:
                dxl_present_velocity, _dxl_comm_result, _dxl_error = self.packet_handler.read4ByteTxRx(self.port_handler, id, ADDR_PRESENT_VELOCITY)
                error_code, _dxl_comm_result, _dxl_error = self.packet_handler.read1ByteTxRx(self.port_handler, id, ADDR_ERROR_CODE)
                
                # adjust for 2's complement
                if dxl_present_velocity > 0x7fffffff:
                    dxl_present_velocity = dxl_present_velocity - 4294967296
                # if dxl_present_current > 0x7fff:
                # 	dxl_present_current = dxl_present_current - 65536
                
                self.motor_statuses[side] += (dxl_present_velocity / self.velocity_limit * orientation) / 2
                    
                if error_code > 0:
                    print(f"error_code {id} {error_code} {self.packet_handler.getRxPacketError(error_code)}")
                    print(f"rebooting {id}")
                    self.packet_handler.reboot(self.port_handler, id)
    # ------------------------------------------------------------------------ #
# ---------------------------------------------------------------------------- #