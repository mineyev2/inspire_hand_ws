
from .inspire_hand_defaut import *
from .inspire_dds import inspire_hand_touch,inspire_hand_ctrl,inspire_hand_state
from unitree_sdk2py.core.channel import ChannelPublisher, ChannelFactoryInitialize
from unitree_sdk2py.core.channel import ChannelSubscriber, ChannelFactoryInitialize
from unitree_sdk2py.utils.thread import Thread

from pymodbus.client import ModbusTcpClient
from pymodbus.client import ModbusSerialClient

import numpy as np
import struct
import sys
import time
class ModbusDataHandler:
    def __init__(self, data=data_sheet, history_length=100, network=None, ip=None, port=6000, device_id=1, LR='r', use_serial=False, serial_port='/dev/ttyUSB0', baudrate=115200, states_structure=None, initDDS=True, max_retries=5, retry_delay=2):
        """_summary_
        Calling self.read() in a loop reads and returns the data, and publishes the DDS message at the same time        
        Args:
            data (dict, optional): Tactile sensor register definition. Defaults to data_sheet.
            history_length (int, optional): Hand state history_length. Defaults to 100.
            network (str, optional): Name of the DDS NIC. Defaults to None.
            ip (str, optional): ModbusTcp IP. Defaults to None will use 192.1686.11.210.
            port (int, optional): ModbusTcp IP port. Defaults to 6000.
            device_id (int, optional): Hand ID. Defaults to 1.
            LR (str, optional): Topic suffix l or r. Defaults to 'r'.
            use_serial (bool, optional): Whether to use serial mode. Defaults to False.
            serial_port (str, optional): Serial port name. Defaults to '/dev/ttyUSB0'.
            baudrate (int, optional): Serial baud rate. Defaults to 115200.
            states_structure (list, optional): List of tuples for state registers. Each tuple should contain (attribute_name, start_address, length, data_type). If None ,will publish All Data 
            initDDS (bool, optional): Run ChannelFactoryInitialize(0),only need run once in all program
            max_retries (int, optional): Number of retries for connecting to Modbus server. Defaults to 3.
            retry_delay (int, optional): Delay between retries in seconds. Defaults to 2.
        Raises:
            ConnectionError: raise when connection fails after max_retries
        """        
        self.data = data
        self.history_length = history_length
        self.history = {
            'POS_ACT': [np.zeros(history_length) for _ in range(6)],
            'ANGLE_ACT': [np.zeros(history_length) for _ in range(6)],
            'FORCE_ACT': [np.zeros(history_length) for _ in range(6)],
            'CURRENT': [np.zeros(history_length) for _ in range(6)],
            'ERROR': [np.zeros(history_length) for _ in range(6)],
            'STATUS': [np.zeros(history_length) for _ in range(6)],
            'TEMP': [np.zeros(history_length) for _ in range(6)]
        }
        self.use_serial = use_serial
        
        self.states_structure = states_structure or [
            ('pos_act', 1534, 6, 'short'),
            ('angle_act', 1546, 6, 'short'),
            ('force_act', 1582, 6, 'short'),
            ('current', 1594, 6, 'short'),
            ('err', 1606, 3, 'byte'),
            ('status', 1612, 3, 'byte'),
            ('temperature', 1618, 3, 'byte')
        ]
        if self.use_serial:
            self.client = ModbusSerialClient(method='rtu', port=serial_port, baudrate=baudrate, timeout=1)
            print("will use serial")
        else:
            if ip==None:
                self.client = ModbusTcpClient(defaut_ip, port=6000)
                print("will use defautl Tcp")
            else:
                self.client = ModbusTcpClient(ip, port=port)
                print("will use Tcp")

        # Try to connect to Modbus server with retry mechanism
        self.connect_to_modbus(max_retries, retry_delay)
        self.device_id = device_id

                
       # 初始化 ChannelFactory
        try:
            if initDDS:
                if network is None:
                    ChannelFactoryInitialize(0, network)
                else:
                    ChannelFactoryInitialize(0)
        except Exception as e:
            print(f"Error during ChannelFactory initialization: {e}")
            # Can add logging or other recovery mechanisms here
            return
        
        self.client.write_register(1004,1,self.device_id) #reser error
        if not self.use_serial:
            self.pub = ChannelPublisher("rt/inspire_hand/touch/"+LR, inspire_hand_touch)
            self.pub.Init()

        self.state_pub = ChannelPublisher("rt/inspire_hand/state/"+LR, inspire_hand_state)
        self.state_pub.Init()
            
        self.sub = ChannelSubscriber("rt/inspire_hand/ctrl/"+LR, inspire_hand_ctrl)
        self.sub.Init(self.write_registers_callback, 10)       
            
    def connect_to_modbus(self, max_retries, retry_delay):
        """Connect to Modbus server and retry on failure"""
        retries = 0
        while retries < max_retries:
            try:
                if not self.client.connect():
                    raise ConnectionError("Failed to connect to Modbus server.")
                print("Modbus client connected successfully.")
                return
            except ConnectionError as e:
                print(f"Connection attempt {retries + 1} failed: {e}")
                retries += 1
                if retries < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    print("Max retries reached. Could not connect.")
                    raise   
    def write_registers_callback(self,msg:inspire_hand_ctrl):
        with modbus_lock:
            if msg.mode & 0b0001:  # Mode 1 - Angle
                self.client.write_registers(1486, msg.angle_set, self.device_id)
                # print('angle_set')
            if msg.mode & 0b0010:  # Mode 2 - Position
                self.client.write_registers(1474, msg.pos_set, self.device_id)
                # print('pos_set')

            if msg.mode & 0b0100:  # Mode 4 - Force control
                self.client.write_registers(1498, msg.force_set, self.device_id)
                # print('force_set')

            if msg.mode & 0b1000:  # Mode 8 - Speed
                self.client.write_registers(1522, msg.speed_set, self.device_id)
                
    def read(self):
        if not self.use_serial:
            touch_msg = get_inspire_hand_touch()
            matrixs = {}
            for i, (name, addr, length, size, var) in enumerate(self.data):
                value = self.read_and_parse_registers(addr, length // 2,'short')
                if value is not None:
                    setattr(touch_msg, var, value)
                    matrix = np.array(value).reshape(size)
                    matrixs[var]=matrix
            self.pub.Write(touch_msg)
        else:
            matrixs = {}
        # Read the states for POS_ACT, ANGLE_ACT, etc.
        states_msg = get_inspire_hand_state()

        for attr_name, start_address, length, data_type in self.states_structure:
            setattr(states_msg, attr_name, self.read_and_parse_registers(start_address, length, data_type))
            
        self.state_pub.Write(states_msg)

        return {'states':{
            'POS_ACT': states_msg.pos_act,
            'ANGLE_ACT': states_msg.angle_act,
            'FORCE_ACT': states_msg.force_act,
            'CURRENT': states_msg.current,
            'ERROR': states_msg.err,
            'STATUS': states_msg.status,
            'TEMP': states_msg.temperature
        },'touch':matrixs
                }

    def read_and_parse_registers(self, start_address, num_registers, data_type='short'):
         with modbus_lock:
            # Read registers
            response = self.client.read_holding_registers(start_address, num_registers, self.device_id)

            if not response.isError():
                if data_type == 'short':
                    # Pack the read registers into binary data
                    packed_data = struct.pack('>' + 'H' * num_registers, *response.registers)
                    # Unpack registers into signed 16-bit integers (short)
                    angles = struct.unpack('>' + 'h' * num_registers, packed_data)
                    return angles
                elif data_type == 'byte':
                    # Split each 16-bit register into two 8-bit (uint8) data
                    byte_list = []
                    for reg in response.registers:
                        high_byte = (reg >> 8) & 0xFF  # High 8 bits
                        low_byte = reg & 0xFF          # Low 8 bits
                        byte_list.append(high_byte)
                        byte_list.append(low_byte)
                    return byte_list
            else:
                print("Error reading registers")
                return None
            

if __name__ == "__main__":
    import qt_tabs 
    app = qt_tabs.QApplication(sys.argv)
    handler=ModbusDataHandler(data_sheet)
    window = qt_tabs.MainWindow(handler,data_sheet)
    window.reflash()
    window.show()
    sys.exit(app.exec_())
