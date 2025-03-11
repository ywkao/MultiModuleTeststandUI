import asyncio
import serial
from PythonTools.MyLogging_BashJob1 import log as rs232log
from PythonTools.MyLogging_BashJob1 import log as bashlog

import pyvisa

class RS232Dev:
    def __init__(self, tag):
        self.rm = pyvisa.ResourceManager()
        self.tag = tag
    def __del__(self):
        self.rm.close()
    def SetTask(self, t):
        self.task = t
    async def Await(self):
        if not hasattr(self, 'task'): return # no task need to wait
        if self.task and not self.task.done():
            bashlog.debug(f'[{self.tag} - Await] waiting for mesg job finished')
            await self.task

async def set_status(instr, commands):
    ''' set the status. Such as no any read() required. '''
    try:
        for cmd in commands:
            instr.write(cmd)
        await asyncio.sleep(0.5)  # Wait 1 second before sending again
    except pyvisa.VisaIOError as e:
        print(f"VISA error: {e}")
    except Exception as e:
        print(f"Error: {e}")

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
        raise KeyError(f'[Invalid Key] input key "{ operation }" is not available in "{ commands.keys() }"') from e

    cmds = [cmd] if isinstance(cmd, str) else cmd

    rs232 = RS232Dev(tag)
    instr = rs232.rm.open_resource(resource)
    instr.baud_rate = 9600
    instr.timeout = 2000  # 2 seconds timeout
    await set_status(instr, cmds) # waiting for the end
    return rs232

def InitChecking(dev):
    failed_reason = ''
    try:
        rm = pyvisa.ResourceManager()
        instr = rm.open_resource(dev)
    except serial.serialutil.SerialException as e:
        failed_reason = f'Unable to find RS232 device from "{ dev }"'
    finally:
        rm.close()
        return failed_reason

if __name__ == "__main__":
    DEVICE_ADDRESS = "ASRL/dev/ttyUSB0::INSTR"

    init_error = InitChecking(DEVICE_ADDRESS)
    if init_error:
        print(f"Initialization check failed: {init_error}")
    else:
        print("[INFO] Device check passed.")
        asyncio.run( SetSwitchState('switch', DEVICE_ADDRESS, 'on') )
        asyncio.run( SetSwitchState('switch', DEVICE_ADDRESS, 'off') )
        print("[INFO] Test finished!")
