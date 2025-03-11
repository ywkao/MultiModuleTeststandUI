import jobfrag_base
import pyvisa
import time
import logging
from typing import Dict, Any

class Switch(jobfrag_base.JobFragBase):
    def __init__(self, hostNAME: str, timeOUT: float,
                 cmdTEMPLATEs: Dict[str, str], argCONFIGs: Dict[str, Any], argSETUPs: Dict[str, Any]):
        """
        Initialize the power switch control job.
        
        Args:
            hostNAME: RS232 port name (e.g., '/dev/ttyUSB0')
            timeOUT: Communication timeout in seconds
            cmdTEMPLATEs: Command templates for the switch
            argCONFIGs: Configuration parameters
            argSETUPs: Initial setup parameters
        """
        self.logger = logging.getLogger(__name__)

        self.port = hostNAME
        self.timeout = timeOUT
        self.cmd_templates = cmdTEMPLATEs
        self.configs = argCONFIGs
        self.setups = argSETUPs
        
        # RS232 connection objects
        self.rm = None
        self.device = None
        
        # State tracking
        self.is_initialized = False
        self.is_running = False

    def __del__(self):
        """Cleanup resources on object destruction"""
        self.Stop()
        if self.device:
            try:
                self.device.close()
            except:
                pass
        if self.rm:
            try:
                self.rm.close()
            except:
                pass

    def Initialize(self):
        """Initialize RS232 connection and configure device"""
        try:
            self.rm = pyvisa.ResourceManager()
            self.device = self.rm.open_resource(f'ASRL{self.port}::INSTR')
            
            # Configure RS232 parameters from setups
            self.device.baud_rate = self.setups.get('baud_rate', 9600)
            self.device.data_bits = self.setups.get('data_bits', 8)

            stop_bits_value = self.setups.get('stop_bits', 1)
            if stop_bits_value == 1:
                self.device.stop_bits = pyvisa.constants.StopBits.one
            elif stop_bits_value == 2:
                self.device.stop_bits = pyvisa.constants.StopBits.two
            elif stop_bits_value == 1.5:
                self.device.stop_bits = pyvisa.constants.StopBits.one_point_five
            else:
                raise ValueError(f"Invalid stop_bits value: {stop_bits_value}")

            # self.device.parity = self.setups.get('parity', pyvisa.constants.Parity.none)
            self.device.timeout = int(self.timeout * 1000)  # Convert to milliseconds
            
            # Send any initialization commands
            init_cmd = self.cmd_templates.get('init')
            if init_cmd:
                self.device.write(init_cmd)
            
            self.is_initialized = True
            self.logger.info("Power switch initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Initialization failed: {str(e)}")
            return False

    def Configure(self, updatedCONF: Dict[str, Any]) -> bool:
        """
        Update configuration parameters
        
        Args:
            updatedCONF: Dictionary containing updated parameters
        """
        try:
            self.configs.update(updatedCONF)
            self.logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration update failed: {str(e)}")
            return False

    def Run(self):
        """Execute the power switching operation"""
        if not self.is_initialized:
            self.logger.error("Device not initialized")
            return False
            
        try:
            self.is_running = True
            operation = self.configs.get('operation', 'on')
            cmd = self.cmd_templates.get(operation)
            if not cmd:
                raise ValueError(f"No command template for operation: {operation}")
            
            self.device.write(cmd)
            self.logger.info(f"Power status: {operation}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Run operation failed: {str(e)}")
            self.is_running = False
            return False

    def Stop(self):
        """Stop any ongoing operation"""
        if self.is_running:
            try:
                # Send stop command if defined
                stop_cmd = self.cmd_templates.get('stop')
                if stop_cmd:
                    self.device.write(stop_cmd)
                
                self.is_running = False
                self.logger.info("Operation stopped")
                return True
                
            except Exception as e:
                self.logger.error(f"Stop operation failed: {str(e)}")
                return False

if __name__ == "__main__":
    import sys, yaml
    with open('data_switch.yaml', 'r') as yaml_file:
        config_data = yaml.safe_load(yaml_file)

    # Create Switch instance
    job = Switch(
        hostNAME     = '/dev/ttyUSB0',  # Change to your port
        timeOUT      = 1.0,
        cmdTEMPLATEs = config_data['cmd_templates'],
        argCONFIGs   = config_data['arg_configs'],
        argSETUPs    = config_data['arg_setups']
    )

    # Test sequence
    print("Initializing...")
    if job.Initialize():
        print("Initialization successful")
        new_config = {'duration': 3.0}
        job.Configure(new_config)
        job.Run()
        job.Stop()
    else:
        print("Initialization failed")
