import os, sys
import asyncio
import pyvisa
import serial

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PythonTools.MyLogging_BashJob1 import log as rs232log
from PythonTools.MyLogging_BashJob1 import log as bashlog

class RS232Dev:
    def __init__(self, tag):
        self.rm = pyvisa.ResourceManager()
        self.tag = tag
        self.task = None  # Initialize task attribute

    def __del__(self):
        self.rm.close()

    def SetTask(self, t):
        self.task = t

    async def Await(self):
        if not hasattr(self, 'task') or self.task is None: 
            return  # no task need to wait
        if not self.task.done():
            bashlog.debug(f'[{self.tag} - Await] waiting for mesg job finished')
            await self.task

async def set_status(instr, commands):
    """Send commands to the switch"""
    try:
        # Handle both string and list inputs
        cmds = [commands] if isinstance(commands, str) else commands
        for cmd in cmds: instr.write(cmd)
        await asyncio.sleep(0.5)  # Wait before returning
        return True
    except pyvisa.VisaIOError as e:
        print(f"VISA error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

async def SetSwitchState(tag, resource, operation):
    """Control switch state based on operation type"""
    commands = {
        'init' : '*RST', # Reset command
        'on'   : 'A',    # RELAY ON
        'off'  : 'a',    # RELAY OFF
        'stop' : 'ABORT' # Stop command
    }

    try:
        cmd = commands[operation]
    except KeyError as e:
        raise KeyError(f'[Invalid Key] input key "{operation}" is not available in "{list(commands.keys())}"') from e

    rs232 = RS232Dev(tag)
    try:
        instr = rs232.rm.open_resource(resource)
        instr.baud_rate = 9600
        instr.timeout = 2000  # 2 seconds timeout
        result = await set_status(instr, cmd)  # waiting for the end
        return rs232 if result else None
    except Exception as e:
        bashlog.error(f"Connection error: {e}")
        return None

def InitChecking(dev):
    failed_reason = ''
    rm = None
    try:
        rm = pyvisa.ResourceManager()
        instr = rm.open_resource(dev)
    except serial.serialutil.SerialException as e:
        failed_reason = f'Unable to find RS232 device from "{dev}"'
    except Exception as e:
        failed_reason = f'Error checking device: {e}'
    finally:
        if rm: rm.close()
        return failed_reason

if __name__ == "__main__":
    DEVICE_ADDRESS = "ASRL/dev/ttyUSB0::INSTR"

    # Define async test function
    async def test_switch():
        init_error = InitChecking(DEVICE_ADDRESS)
        if init_error:
            print(f"Initialization check failed: {init_error}")
        else:
            print("[INFO] Device check passed.")
            await SetSwitchState('switch', DEVICE_ADDRESS, 'on')
            await asyncio.sleep(2)  # Wait 2 seconds
            await SetSwitchState('switch', DEVICE_ADDRESS, 'off')
            print("[INFO] Test finished!")

    # Run the test function
    asyncio.run(test_switch())
