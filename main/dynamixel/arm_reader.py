# Runs on the Laptop

import dynamixel.base_controller
import dynamixel.base_arm
import time

READER_JOINT_IDS = { # READER_JOINT_IDS[joint] = id
    "j1": 5,
    "j2": 6,
    "j3": 7,
}


class ArmReader(dynamixel.base_arm.BaseArm):
    def __init__(self):
        super().__init__(READER_JOINT_IDS)
        self.is_active = False

    def setup_arm(self):
        cycles = super().setup_arm()
        return cycles

    def maybe_update_torque(self, arm_active):
        # if active -> torque off
        if arm_active and not self.is_active:
            self.set_torque_status_all(False, self.joint_ids.values())
            self.is_active = True
        elif not arm_active and self.is_active:
            self.set_torque_status_all(True, self.joint_ids.values())
            self.is_active = False

    def update_arm_status(self):
        for joint, joint_id in self.joint_ids.items():
            pos, dxl_comm_result, dxl_error = self.packet_handler.read4ByteTxRx(
                self.port_handler,
                joint_id,
                dynamixel.base_controller.ADDR_PRESENT_POS
            )
            
            self.handle_possible_dxl_issues(joint_id, dxl_comm_result, dxl_error)
            self.check_error_and_maybe_reboot(joint_id)

            self.joint_statuses[joint] = pos