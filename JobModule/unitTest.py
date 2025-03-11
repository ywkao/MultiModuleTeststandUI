import sys
import yaml
from switch_control import Switch  # Replace with your actual module name

def test_power_switch():

    with open('data_switch.yaml', 'r') as yaml_file:
        config_data = yaml.safe_load(yaml_file)

    cmd_templates = config_data['cmd_templates']
    arg_configs = config_data['arg_configs']
    arg_setups = config_data['arg_setups']

    # Create Switch instance
    job = Switch(
        hostNAME='/dev/ttyUSB0',  # Change to your port
        userNAME='',              # Not used for RS232
        privateKEYfile='',        # Not used for RS232
        timeOUT=1.0,
        cmdTEMPLATEs=cmd_templates,
        argCONFIGs=arg_configs,
        argSETUPs=arg_setups
    )

    # Test sequence
    print("Initializing...")
    if job.Initialize():
        print("Initialization successful")

        # Test configuration update
        new_config = {'duration': 3.0}
        if job.Configure(new_config):
            print("Configuration updated")

        # Run power cycle
        print("Running power cycle...")
        if job.Run():
            print("Power cycle completed")
        else:
            print("Power cycle failed")

        # Stop operation
        job.Stop()
    else:
        print("Initialization failed")

if __name__ == "__main__":
    test_power_switch()
