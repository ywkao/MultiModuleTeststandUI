import pyvisa
import time

def main():
    # Create a connection
    rm = pyvisa.ResourceManager()
    
    # List all available ports (helpful for debugging)
    print("Available ports:", rm.list_resources())
    
    try:
        # Replace 'COM1' with your actual port
        # Windows example: 'COM1'
        # Linux/Mac example: '/dev/ttyUSB0' or '/dev/ttyS0'
        port = '/dev/ttyUSB0'  # Change this to match your setup
        device = rm.open_resource(f'ASRL{port}::INSTR')
        
        # Set basic parameters
        device.baud_rate = 9600
        device.data_bits = 8
        device.stop_bits = pyvisa.constants.StopBits.one
        device.parity = pyvisa.constants.Parity.none
        
        print(f"Connected to {port}")
        
        # Simple test: Send ON, wait, then OFF
        print("Sending ON command...")
        device.write('RELAY ON')
        time.sleep(2)  # Wait 2 seconds
        
        print("Sending OFF command...")
        device.write('a')
        
        # Close connection
        device.close()
        print("Test completed")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    finally:
        rm.close()

if __name__ == "__main__":
    main()
