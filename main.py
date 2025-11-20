import os
import sys
import time
import threading
import pandas
from packages.plc_socket import kv_plc_tcp_socket

# PLC names list
plc_names = ('M1 Gasket',
             'M2 PHD',
             'M3 Male IMLA assy',
             'M4 Female IMLA assy',
             'M5 Flatten and wleding',
             'M6 Female IMLA assy',
             'M7 Female IMLA assy',
             'M8 Short/Code',
             )

# Instance line 1 PLC's
plc_list = []

plc_list.append(kv_plc_tcp_socket('192.168.0.10', 8501, 3)) 
plc_list.append(kv_plc_tcp_socket('192.168.0.20', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.30', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.40', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.50', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.60', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.70', 8501, 3))
plc_list.append(kv_plc_tcp_socket('192.168.0.80', 8501, 3))


# Create CT list
ct_list = [0.] * len(plc_list)

# Thread functions
def t_get_ct(plc, index):
    try:
        ct_list[index] = float(plc.read('DM', 88)) / 10.
    except Exception as e:
        print(e)

try:
    # Main loop

    while (1):

        threads = []
        for idx, plc in enumerate(plc_list):
            t = threading.Thread(target=t_get_ct, args=(plc, idx))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write('\033[H')  # Move cursor to top left
        for name, ct in zip(plc_names, ct_list):
            sys.stdout.write('\033[2K\r')  # Clear line and move to start
            sys.stdout.write(
                f'{name}: {ct} seconds, '
            )
            sys.stdout.write('\n')  # Move to next line
        sys.stdout.flush()

        time.sleep(0.25)
        
except KeyboardInterrupt:
    print("\nProgram terminated by user (Ctrl+C). Exiting gracefully.")
    # Add any necessary cleanup code here, like closing PLC connections
    sys.exit(0) # Exit the program