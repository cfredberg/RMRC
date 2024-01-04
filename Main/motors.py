import dynamixel_sdk


# ---------------------------------------------------------------------------- #
# https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/
# https://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/api_reference/python/python_porthandler/#python

DEVICE_NAME = "/dev/ttyUSB0"
PROTOCOL_VERSION = 2.0

# BAUDRATE = 57600
ADDR_BAUDRATE, BAUDRATE, BAUDRATE_VALUE = 8, 4_500_000, 7
ADDR_RETURN_DELAY_TIME, RETURN_DELAY_TIME_VALUE = 9, 0
ADDR_OPERATING_MODE, OPERATING_MODE_VALUE = 11, 1 # 1 = velocity control mode

# MAX_VELOCITY = 330
ADDR_VELOCITY_LIMIT, VELOCITY_LIMIT_START_VALUE, VELOCITY_LIMIT_UNITS = 44, 1023, 0.229 # rev/min

ADDR_TORQUE_ENABLE = 64 # 1 = enable, 0 = disable
ADDR_ERROR_CODE = 70
ADDR_GOAL_VELOCITY = 104

ADDR_PROFILE_ACCELERATION, PROFILE_ACCELERATION_UNITS = 108, 214.577 # rev/min^2
TIME_TO_MAX_VELOCITY = 0.4 / 60 # min
# (rev/min) / (min) = rev/min^2
PROFILE_ACCELERATION_MAX = 32737
PROFILE_ACCELERATION_START_VALUE = int((VELOCITY_LIMIT_START_VALUE * VELOCITY_LIMIT_UNITS) / TIME_TO_MAX_VELOCITY / PROFILE_ACCELERATION_UNITS)

ADDR_PRESENT_VELOCITY = 128
# ---------------------------------------------------------------------------- #


# ---------------------------------------------------------------------------- #
DYNAMIXEL_IDS = { # DYNAMIXEL_IDS[side] = [id1, id2]
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
	def __init__(self, tx_rx):
		self.port_handler = dynamixel_sdk.PortHandler(DEVICE_NAME)
		self.packet_handler = dynamixel_sdk.PacketHandler(PROTOCOL_VERSION)
		
		self.tx_rx = tx_rx
		
		if self.port_handler.openPort():
			print("Succeeded to open the port")
		else:
			print("Failed to open the port.")

		self.profile_acceleration = PROFILE_ACCELERATION_START_VALUE
		self.velocity_limit = VELOCITY_LIMIT_START_VALUE

		self.speeds = { # speeds[side] = %
			"left": 0,
			"right": 0,
		}
		self.statuses = { # statuses[side] = %
			"left": 0,
			"right": 0,
		}

		self.acceleration_time = 0.4 # seconds: time to reach max velocity
		
		# used to have instant acceleration even for fixed acceleration (speed -> 0 -> instant acceleration)
		self.accelerations = { # accelerations[side] = value
			"left": self.profile_acceleration,
			"right": self.profile_acceleration
		}

	def setup(self):
		if self.port_handler.setBaudRate(BAUDRATE):
			print("Succeeded to change the baudrate")
		else:
			print("Failed to change the baudrate.")

		for side_ids in DYNAMIXEL_IDS.values():
			for id in side_ids:
				for addr, value in [
					(ADDR_BAUDRATE, BAUDRATE_VALUE),
					(ADDR_RETURN_DELAY_TIME, RETURN_DELAY_TIME_VALUE),
					(ADDR_OPERATING_MODE, OPERATING_MODE_VALUE),
					(ADDR_VELOCITY_LIMIT, self.velocity_limit),
					(ADDR_TORQUE_ENABLE, 1),
					(ADDR_PROFILE_ACCELERATION, self.profile_acceleration),
				]:
					self.command(id, addr, value)

	def close(self):
		for side_ids in DYNAMIXEL_IDS.values():
			for id in side_ids:
				for addr, value in [
					(ADDR_TORQUE_ENABLE, 0),
				]:
					self.command(id, addr, value)

		self.port_handler.closePort()

	def reset_motors(self):
		for side_ids in DYNAMIXEL_IDS.values():
			for id in side_ids:
				self.packet_handler.reboot(self.port_handler, id)

	def command(self, id, addr, value):
		if self.tx_rx:
			dxl_comm_result, dxl_error = self.packet_handler.write4ByteTxRx(self.port_handler, id, addr, value)
			if dxl_comm_result != dynamixel_sdk.COMM_SUCCESS:
				print(f"dxl_comm_result error {id} {addr} {value} {self.packet_handler.getTxRxResult(dxl_comm_result)}")
			elif dxl_error != 0:
				print(f"dxl_error error {id} {addr} {value} {self.packet_handler.getRxPacketError(dxl_error)}")
		else:
			self.packet_handler.write4ByteTxOnly(self.port_handler, id, addr, value)	

	def set_torque_status(self, status):
		status_code = 1 if status else 0
		for side_ids in DYNAMIXEL_IDS.values():
			for id in side_ids:
				self.command(id, ADDR_TORQUE_ENABLE, status_code)

	def update_acceleration(self):
		for side_ids in DYNAMIXEL_IDS.values():
			for id in side_ids:
				if self.acceleration_time > 0:
					value = int((self.velocity_limit * VELOCITY_LIMIT_UNITS) / self.acceleration_time / PROFILE_ACCELERATION_UNITS)
					self.profile_acceleration = min(value, PROFILE_ACCELERATION_MAX)
					self.command(id, ADDR_PROFILE_ACCELERATION, self.profile_acceleration)
				else:
					self.command(id, ADDR_PROFILE_ACCELERATION, 0)
				
	def update_speed(self):
		for side, side_ids in DYNAMIXEL_IDS.items():
			orientation = ORIENTATIONS[side]
			speed = self.speeds[side]
			power = int(speed * self.velocity_limit) * orientation

			if self.acceleration_time > 0:
				# instant acceleration when speed is 0 even for fixed acceleration
				last_acceleration = self.accelerations[side]
				if speed == 0:
					self.accelerations[side] = 0
				else:
					self.accelerations[side] = self.profile_acceleration
				update_acceleration = last_acceleration != self.accelerations[side]
			else:
				update_acceleration = False
				
			for id in side_ids:
				if update_acceleration:
					self.command(id, ADDR_PROFILE_ACCELERATION, self.accelerations[side])
				self.command(id, ADDR_GOAL_VELOCITY, power)

	def update_status(self):
		error_codes = {} # error_codes[id] = error_code
		any_errors = []

		for side, side_ids in DYNAMIXEL_IDS.items():
			orientation = ORIENTATIONS[side]
			self.statuses[side] = 0

			for id in side_ids:
				dxl_present_velocity = self.packet_handler.read4ByteTx(self.port_handler, id, ADDR_PRESENT_VELOCITY)
				error_code = self.packet_handler.read1ByteTx(self.port_handler, id, ADDR_ERROR_CODE)
				
				error_codes[id] = error_code
				any_errors.append(error_code > 0)
				
				self.statuses[side] += (dxl_present_velocity / VELOCITY_LIMIT_VALUE * orientation) / 2

		if any(any_errors):
			for id, error_code in error_codes.items():
				if error_code > 0:
					print(f"error_code {id} {error_code}")
					self.reset_motors()
# ---------------------------------------------------------------------------- #


"""
# Code used for the flipper arm, not currently implemented/recreated

import smbus

bus = smbus.SMBus(1)
bus2 = smbus.SMBus(8)


	if drive_4x.reset == 1:
		print("FLIPPER")
		if flipper == 0:
			pos = 0
			print("UP ", pos)
			bus.write_byte(37,1)
			print("a")
			bus.write_byte(37, pos)
			print("b")
			#bus2.write_byte(37,1)
			# print("c")
			#bus2.write_byte(37, pos)
			# print("d")
			flipper = 1
			print(flipper)
		else:
			pos = 100
			print("DOWN ", pos)
			bus.write_byte(37,1)
			bus.write_byte(37, pos)
			#bus2.write_byte(37,1)  
			#bus2.write_byte(37, pos)
			flipper = 0
"""