# -*- coding: utf-8 -*-
"""
Created on Sat Mar 11 20:24:56 2017

@author: sebastian
"""
from twisted.internet import reactor, protocol
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.diag_message import *
from bk9050_defines import *
from kl3208_0010_defines import *
import logging
log = logging.getLogger("BK9050")

class BK9050:
    
    """Constructor"""
    def __init__(self,ip, port):
        self.ip = ip
        self.port = port
        self.connect()
        
        # if connection was established
        if self.client:
            log.info("Connection to bus coupler BK9050 {}:{} was successfully established.".format(self.ip, self.port))
            #self.set_modbus_tcp_mode(MODBUS_TCP_MODE_FAST)
            self.deactivate_watchdog()            
            self.initialize()
            
    def connect(self):
        self.client = ModbusClient(self.ip, self.port)
            
    def close(self):
        self.client.close()
        log.info("Connection closed.")
    
#---------------------------------------------------------------------------#
# INITIALIZATION
#---------------------------------------------------------------------------#
    
    def initialize(self):
        self.diag_check_bus_coupler_status()
        self.get_bus_coupler_id()
        self.initialize_process_image()
        self.initialize_analog_inputs()
        
    def num_analog_inputs(self):
        self.num_ai = self.client.read_input_registers(ADR_NUM_AI_R,1).registers[0] / 32
        log.info("Detected {} analog inputs.".format(self.num_ai))
        
    def num_analog_outputs(self):
        self.num_ao = self.client.read_input_registers(ADR_NUM_AO_R,1).registers[0] / 32
        log.info("Detected {} analog outputs.".format(self.num_ao))

    def num_digital_inputs(self):
        self.num_di = self.client.read_input_registers(ADR_NUM_DI_R,1).registers[0]
        log.info("Detected {} digital inputs.".format(self.num_di))

    def num_digital_outputs(self):
        self.num_do = self.client.read_input_registers(ADR_NUM_DO_R,1).registers[0]
        log.info("Detected {} digital outputs.".format(self.num_do)) 
    
    def initialize_process_image(self):
        log.info("Loading process image:")
        self.num_analog_inputs()
        self.num_analog_outputs()
        self.num_digital_inputs()
        self.num_digital_outputs()
    
    def initialize_analog_inputs(self):
        #assert(self.num_ai != 0)
        for input_num in range(1, self.num_ai+1):
            self.get_analog_input_status(input_num)
            self.get_bus_terminal_type(input_num)
            self.get_bus_terminal_firmware_version(input_num)
            self.get_bus_terminal_hardware_version(input_num)
            self.get_bus_terminal_manufacturer_adjustment_offset(input_num)
            self.get_bus_terminal_manufacturer_adjustment_gain(input_num)
            self.get_bus_terminal_manufacturer_scaling_offset(input_num)
            self.get_bus_terminal_manufacturer_scaling_gain(input_num)
            self.get_bus_terminal_manufacturer_calibration_offset(input_num)
            self.get_bus_terminal_manufacturer_calibration_gain(input_num)
            self.get_AD_raw_value(input_num)
            self.get_AD_line_res_raw_value(input_num)
            self.set_sensor_type(input_num, RTD_NTC5K)
    
    def get_bus_coupler_id(self):
        read_response = self.client.read_holding_registers(ADR_BUS_COUPLER_ID_R[0], 6)
        id = read_response.registers
        log.debug("Bus coupler ID: " + ":".join("{:02x}".format(x) for x in id))
        
    # set ModbusTCP mode to either fast mode (MODBUS_TCP_MODE_FAST) or  
    # normal/default mode (MODBUS_TCP_MODE_NORMAL). Fast mode should only be
    # used in small local networks. Use normal mode if experiencing problems.
    def set_modbus_tcp_mode(self, mode):
        #assert((mode != MODBUS_TCP_MODE_NORMAL) and (mode != MODBUS_TCP_MODE_FAST))
        self.write_register(ADR_MODBUS_TCP_MODE_RW, mode)
        
        # device needs to be reset here
        self.diag_reset_bus_coupler()
        
#---------------------------------------------------------------------------#
# WATCHDOG
#---------------------------------------------------------------------------#
    
    def deactivate_watchdog(self):
        self.set_watchdog_timeout(0)
        log.debug("Watchdog timer is now deactivated.")
    
    def set_watchdog_timeout(self,value):    
        self.write_register(ADR_WATCHDOG_TIMEOUT_RW, value)
    
    def get_watchdog_timeout(self):
        read_response = self.client.read_holding_registers(ADR_WATCHDOG_TIMEOUT_RW, 1)
        return read_response.registers[0]
        
    def get_watchdog_current_time(self):
        self.diag_check_bus_coupler_status()
        read_response    = self.client.read_holding_registers(ADR_WATCHDOG_CURRENT_TIME_R, 1)
        watchdog_time    = read_response.registers[0]
        watchdog_timeout = self.get_watchdog_timeout()
        if(self.watchdog_expired_err == False):
            if(watchdog_timeout == 0):
                log.debug("Watchdog is currently deactivated.")
            else:
                log.debug("Current watchdog time: {}/{} ms".format(watchdog_time, watchdog_timeout))
        else:
            log.error("Status Error: Watchdog timer expired.")
            
    def reset_watchdog(self):
        self.write_register(ADR_WATCHDOG_RESET_RW, WATCHDOG_RESET_SEQ[0])
        self.write_register(ADR_WATCHDOG_RESET_RW, WATCHDOG_RESET_SEQ[1])
    
    def set_watchdog_trigger_on_receive(self):
        self.write_register(ADR_WATCHDOG_TYPE_RW, WATCHDOG_TRIGGER_ON_RECEIVE)
        
    def set_watchdog_trigger_on_write(self):
        self.write_register(ADR_WATCHDOG_TYPE_RW, WATCHDOG_TRIGGER_ON_WRITE)
    
#---------------------------------------------------------------------------#
# DIAGNOSIS / STATUS
#---------------------------------------------------------------------------#
    
    def diag_check_bus_coupler_status(self):
        read_response = self.client.read_holding_registers(ADR_BUS_COUPLER_STATUS_R, 1)
        if(read_response.registers[0] == 0):
            self.watchdog_expired_err       = False
            self.bus_coupler_config_err     = False
            self.bus_terminal_err           = False
            log.debug("Bus coupler status is okay.")
        else:
            if(read_response.registers[0] & WATCHDOG_EXPIRED_ERR):
                self.watchdog_expired_err   = True
                log.error("Status Error: Watchdog timer expired.")
            if(read_response.registers[0] & BUS_COUPLER_CONFIG_ERR):
                self.bus_coupler_config_err = True
                log.error("Status Error: Bus coupler configuration error.")
            if(read_response.registers[0] & BUS_TERMINAL_ERR):
                self.bus_terminal_err       = True
                log.error("Status Error: Bus terminal error.")
    
    def diag_echo_request(self):
        request  = ReturnQueryDataRequest()
        response = self.client.execute(request)
        log.debug("Bus coupler echo message: {}".format(response.message))   
    
    def diag_reset_bus_coupler(self):
        request  = RestartCommunicationsOptionRequest()
        response = self.client.execute(request)
        log.debug("Bus coupler is going to reset now.")
    
    def diag_clear_counters(self):
        request  = ClearCountersRequest()
        response = self.client.execute(request)
        log.debug("Bus coupler counters cleared: {}".format(response.message))
    
    def diag_bus_message_counter(self):
        request  = ReturnBusMessageCountRequest()
        response = self.client.execute(request)
        log.debug("Bus message counter: {}".format(response.message))
        
    def diag_bus_error_counter(self):
        request  = ReturnBusExceptionErrorCountRequest()
        response = self.client.execute(request)
        log.debug("Bus exception error counter: {}".format(response.message))           
    
    def diag_response_counter(self):
        request  = ReturnSlaveMessageCountRequest()
        response = self.client.execute(request)
        log.debug("Bus coupler response counter: {}".format(response.message))         
        
    def diag_no_response_counter(self):
        request  = ReturnSlaveNoResponseCountRequest()
        response = self.client.execute(request)
        log.debug("Bus coupler no response counter: {}".format(response.message))
         
    def diag_response_error_counter(self):
        return # not working yet
        request  = ReturnBusCommunicationErrorCountRequest()
        response = self.client.execute(request)
        log.debug("Bus coupler response error counter: {}".format(response.message))         
         
#---------------------------------------------------------------------------#
# single READ / WRITE operations
#---------------------------------------------------------------------------#   
    
    def write_register(self, addr, value):
        write_response = self.client.write_register(addr, value)
        #read_response  = self.client.read_holding_registers(addr, 1)       # enable for read validation
        assert(write_response.function_code < ERROR_RESPONSE)
        #assert(read_response.registers[0] == value)                        # enable for read validation
        
    def write_control_register(self, input_num, control_byte):
        self.write_register(control_byte_address(input_num), control_byte)
        
    def write_terminal_register_value(self, input_num, register, value):
        # switch from process data to register communication mode
        # disable write protection
        control_byte = REG_ACCESS | REG_ACCESS_WRITE | ADR_CODEWORD_REG_RW
        self.client.write_registers(control_byte_address(input_num), [control_byte, CODE_DISABLE_WRITE_PROTECTION])
        
        # write value to register
        control_byte = REG_ACCESS | REG_ACCESS_WRITE | register
        self.client.write_registers(control_byte_address(input_num), [control_byte, value])
        
        # re-enable write protection
        control_byte = REG_ACCESS | REG_ACCESS_WRITE | ADR_CODEWORD_REG_RW
        self.client.write_registers(control_byte_address(input_num), [control_byte, CODE_DISABLE_WRITE_PROTECTION])        # bug HIER?
        
        # switch from register communication to process data mode
        self.write_control_register(input_num, 0)
        
    def read_status_register(self, input_num):
        return self.client.read_holding_registers(status_register_address(input_num), 1)        
        
    def read_terminal_register(self, input_num, register):
        control_byte = REG_ACCESS | REG_ACCESS_READ | register
        self.write_control_register(input_num, control_byte)
        return self.client.read_holding_registers(input_data_address(input_num), 1)
        
    def set_digital_output(self, num, value):
        assert(num < self.num_digital_outputs)
        write_response = self.client.write_coil(num, value)
        #read_response  = self.client.read_coils(num, 1)                     # enable for read validation
        assert(write_response.function_code < ERROR_RESPONSE)     
        #assert(read_response.bits[0] == value)                              # enable for read validation
        log.debug("Digital output {} set to {}.".format(num, value))
        
    def get_analog_input_status(self, input_num):
        read_response = self.read_status_register(input_num)
        status_byte = read_response.registers[0]
        if(status_byte == 0):
            log.info("Analog input {}: \t Connected and in range.".format(input_num))
        else:
            if(status_byte & STATUS_BYTE_OVERRANGE):
                log.info("Analog input {}: \t Out of range (overrange).".format(input_num))
            elif (status_byte & STATUS_BYTE_UNDERRANGE):
                log.info("Analog input {}: \t Out of range (underrange).".format(input_num))
                
#---------------------------------------------------------------------------#
# Bus terminal register communication
#---------------------------------------------------------------------------#       
    
    def disable_register_write_protection(self, input_num):
        control_byte = REG_ACCESS | REG_ACCESS_WRITE | ADR_CODEWORD_REG_RW
        self.write_control_register(input_num, control_byte)
        self.write_register(output_data_address(input_num), CODE_DISABLE_WRITE_PROTECTION)
        self.write_control_register(input_num, 0)
        
    def enable_register_write_protection(self, input_num):
        control_byte = REG_ACCESS | REG_ACCESS_WRITE | ADR_CODEWORD_REG_RW
        self.write_control_register(input_num, control_byte)
        self.write_register(output_data_address(input_num), CODE_ENABLE_WRITE_PROTECTION)
        self.write_control_register(input_num, 0)

    def get_AD_raw_value(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_AD_RAW_VALUE_R)
        log.info("Analog input {}: \t Raw AD value {}".format(input_num, read_response.registers[0]))

    def get_AD_line_res_raw_value(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_AD_LINE_RES_RAW_VALUE_R)
        log.info("Analog input {}: \t Raw AD with line resistance value {}".format(input_num, read_response.registers[0]))

    def set_sensor_type(self, input_num, sensor_type):
        self.write_terminal_register_value(input_num, ADR_SENSOR_TYPE_RW, sensor_type)
        log.info("Analog input {}: \t Setting sensor type to {}".format(input_num, sensor_type_string(sensor_type)))
        self.get_sensor_type(input_num)
        
    def get_sensor_type(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_SENSOR_TYPE_RW)
        log.info("Analog input {}: \t Sensor type: {}".format(input_num, sensor_type_string(read_response.registers[0])))
        self.write_control_register(input_num, 0)

    def get_bus_terminal_firmware_version(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_FIRMWARE_VERSION_R)
        log.info("Analog input {}: \t Terminal firmware version: {}{}".format(input_num, unichr(read_response.registers[0] >> 8), unichr(read_response.registers[0] & 0x00FF)))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_hardware_version(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_HARDWARE_VERSION_R)
        log.info("Analog input {}: \t Terminal hardware version: {}".format(input_num, read_response.registers[0]))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_manufacturer_adjustment_offset(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_MANUFACTURER_ADJUSTMENT_OFFSET_RW)
        log.info("Analog input {}: \t Manufacturer adjustment offset: {}".format(input_num, read_response.registers[0]))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_manufacturer_adjustment_gain(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_MANUFACTURER_ADJUSTMENT_GAIN_RW)
        log.info("Analog input {}: \t Manufacturer adjustment gain: {}".format(input_num, read_response.registers[0]))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_manufacturer_scaling_offset(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_MANUFACTURER_SCALING_OFFSET_RW)
        log.info("Analog input {}: \t Manufacturer scaling offset: {}".format(input_num, read_response.registers[0]))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_manufacturer_scaling_gain(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_MANUFACTURER_SCALING_GAIN_RW)
        log.info("Analog input {}: \t Manufacturer scaling gain: {}".format(input_num, read_response.registers[0]))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_manufacturer_calibration_offset(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_MANUFACTURER_CALIB_OFFSET_RW)
        log.info("Analog input {}: \t Manufacturer calibration offset: {}".format(input_num, read_response.registers[0]))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_manufacturer_calibration_gain(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_MANUFACTURER_CALIB_GAIN_RW)
        log.info("Analog input {}: \t Manufacturer calibration gain: {}".format(input_num, read_response.registers[0]))
        self.write_control_register(input_num, 0)
        
    def get_bus_terminal_type(self, input_num):
        read_response = self.read_terminal_register(input_num, ADR_BUS_TERMINAL_TYPE_R)
        read_response_ext = self.read_terminal_register(input_num, ADR_BUS_TERMINAL_TYPE_EXTENSION_R)
        log.info("Analog input {}: \t Terminal type: {}-{:04d}".format(input_num, read_response.registers[0], read_response_ext.registers[0]))
        self.write_control_register(input_num, 0)        
        
#---------------------------------------------------------------------------#
# Multiple READ / WRITE operations
#---------------------------------------------------------------------------#

    
