import asyncio
import pyvisa
import yaml
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global configuration cache
_config_cache = {}

def load_config(config_file='data_switch.yaml'):
    """Load config from YAML file with caching"""
    if config_file in _config_cache:
        return _config_cache[config_file]
    
    with open(config_file, 'r') as yaml_file:
        config_data = yaml.safe_load(yaml_file)
    
    _config_cache[config_file] = config_data
    return config_data

class RS232Dev:
    def __init__(self, tag, config_data=None):
        self.rm = pyvisa.ResourceManager()
        self.tag = tag
        self.task = None
        self.config = config_data
        
    def __del__(self):
        if hasattr(self, 'rm'):
            self.rm.close()
            
    def SetTask(self, t):
        self.task = t
        
    async def Await(self):
        if not hasattr(self, 'task') or not self.task:
            return
        if not self.task.done():
            logger.debug(f'[{self.tag} - Await] waiting for job to finish')
            await self.task

async def set_switch_status(instr, commands):
    """Send commands to the switch without expecting responses"""
    try:
        for cmd in commands:
            instr.write(cmd)
            await asyncio.sleep(0.1)  # Small delay between commands
        
        await asyncio.sleep(0.5)  # Wait after all commands are sent
        return True
        
    except pyvisa.VisaIOError as e:
        logger.error(f"VISA error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

async def SetSwitchState(tag, resource, operation, config_data=None, config_file='data_switch.yaml'):
    """Control switch state based on operation type"""
    # Load configuration once or use provided config
    if config_data is None:
        config_data = load_config(config_file)
    
    cmd_templates = config_data['cmd_templates']
    arg_setups = config_data['arg_setups']
    
    # Determine which command to send
    if operation not in cmd_templates:
        raise KeyError(f'Invalid operation: "{operation}". Available operations: {list(cmd_templates.keys())}')
    
    # Only send the specific command for the requested operation
    command = cmd_templates[operation]
    commands = [command] if isinstance(command, str) else command
    
    # Initialize RS232 device
    rs232 = RS232Dev(tag, config_data)
    try:
        instr = rs232.rm.open_resource(resource)
        
        # Configure connection parameters
        instr.baud_rate = arg_setups.get('baud_rate', 9600)
        instr.data_bits = arg_setups.get('data_bits', 8)
        
        stop_bits_value = arg_setups.get('stop_bits', 1)
        if stop_bits_value == 1:
            instr.stop_bits = pyvisa.constants.StopBits.one
        elif stop_bits_value == 2:
            instr.stop_bits = pyvisa.constants.StopBits.two
        elif stop_bits_value == 1.5:
            instr.stop_bits = pyvisa.constants.StopBits.one_point_five
            
        instr.timeout = 2000  # 2 seconds timeout
        
        # Send commands to the device
        await set_switch_status(instr, commands)
        
        return rs232
    except Exception as e:
        logger.error(f"Failed to initialize or send commands: {e}")
        return None

class SwitchManager:
    """Helper class to manage switch operations with cached configuration"""
    def __init__(self, config_file='data_switch.yaml'):
        self.config_data = load_config(config_file)
        self.config_file = config_file
        
    async def turn_on(self, tag, resource):
        return await SetSwitchState(tag, resource, 'on', self.config_data)
        
    async def turn_off(self, tag, resource):
        return await SetSwitchState(tag, resource, 'off', self.config_data)
        
    async def reset(self, tag, resource):
        return await SetSwitchState(tag, resource, 'init', self.config_data)
        
def InitChecking(dev):
    """Check if the device is available"""
    failed_reason = ''
    try:
        rm = pyvisa.ResourceManager()
        instr = rm.open_resource(dev)
        rm.close()
    except Exception as e:
        failed_reason = f'Unable to find RS232 device "{dev}": {str(e)}'
    return failed_reason

if __name__ == "__main__":
    DEVICE_ADDRESS = "ASRL/dev/ttyUSB0::INSTR"
    
    # Test initialization
    init_error = InitChecking(DEVICE_ADDRESS)
    if init_error:
        print(f"Initialization check failed: {init_error}")
    else:
        print("Device check passed!")
        
        # Test operations with SwitchManager
        async def test_manager():
            manager = SwitchManager()
            
            print("Turning switch ON...")
            await manager.turn_on('switch', DEVICE_ADDRESS)
            await asyncio.sleep(2)  # Wait 2 seconds
            
            print("Turning switch OFF...")
            await manager.turn_off('switch', DEVICE_ADDRESS)
            print("Test sequence completed")
        
        asyncio.run(test_manager())
