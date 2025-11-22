import os
import sys
import time
import threading
import pandas as pd
from packages.plc_socket import kv_plc_tcp_socket

# PLC names
plc_names = ('M1 Gasket',
             'M2 PHD',
             'M3 Male IMLA assy',
             'M4 Female IMLA assy',
             'M5 Flatten and welding',
             'M6 Female IMLA assy',
             'M7 Female IMLA assy',
             'M8 Short/Code',
             )

# Instance all PLC's
plc_list = []

plc_list.append(kv_plc_tcp_socket('192.168.0.10', 8501, 3)) 
plc_list.append(kv_plc_tcp_socket('192.168.0.20', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.30', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.40', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.50', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.60', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.70', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.80', 8501, 3))

# Create CT list, 
# The updated bit list stores the flag from the PLC program that will tell us if CT has been changed
ct_list = [0.] * len(plc_list)
updated_ct_bit_list = [[False, False] for _ in range(len(plc_list))] # <- [[New value, Last value]]

# Create Pandas series for statistics
ct_series_list = [pd.Series() for _ in range(len(plc_list))]

# Thread functions
def t_get_ct(plc, index):
    try:
        ct_list[index] = float(plc.read('DM', 88)) / 10.
    except Exception as e:
        print(f'Exception at t_get_ct(plc, index): {e} at {plc_names[index]}')

def t_get_updated_bit(plc, index):
    try:
        # Shift last value
        updated_ct_bit_list[index][1] = updated_ct_bit_list[index][0]
        # Updated new value
        updated_ct_bit_list[index][0] = plc.read('MR', 5912)
    except Exception as e:
        print(f'Exception at t_get_updated_bit(plc, index): {e} at {plc_names[index]}')

try:
    # Main loop
    while (True):

        threads = []

        # Fetch PLC's data
        for index, plc in enumerate(plc_list):
            t1 = threading.Thread(target=t_get_ct, args=(plc, index))
            t1.start()
            threads.append(t1)
            t2 = threading.Thread(target=t_get_updated_bit, args=(plc, index))
            t2.start()
            threads.append(t2)
        for t in threads:
            t.join()

        # Updated series if needed

        # Prompt values
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write('\033[H')  # Move cursor to top left
        for i in range(len(plc_names)):
            sys.stdout.write('\033[2K\r')  # Clear line and move to start
            sys.stdout.write(
                f'{plc_names[i]}: {ct_list[i]} seconds, [{updated_ct_bit_list[i][0]}, {updated_ct_bit_list[i][1]}]'
            )
            sys.stdout.write('\n')  # Move to next line
        sys.stdout.flush()

        time.sleep(0.25)

except KeyboardInterrupt:
    print("\nProgram terminated by user (Ctrl+C). Exiting gracefully.")
    # Add any necessary cleanup code here, like closing PLC connections
    sys.exit(0) # Exit the program