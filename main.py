import os
import sys
import threading
import pandas as pd
from packages.plc_socket import kv_plc_tcp_socket
import math

# Constants
SAMPLE_SIZE = 100
FILENAME = 'Paladin_CT_sample.xlsx'
PLC_NAMES = ('M1 Gasket',
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
ct_values_list = [0.] * len(plc_list)

# The following list keep tracks of a PLC bit that presents a rising edge when the CT has been updated
# Each element is for each PLC
current_ct_bit_list = [False] * len(plc_list)
last_ct_bit_list = [False] * len(plc_list)

# Create temporary list of lists to be converted to Pandas dataframe after collecting sufficient data
ct_temp_lists = [[] for _ in range(len(plc_list))]

# Statistics
initial_stats_index = pd.Index(PLC_NAMES) 
sample_mean_series = pd.Series([0.] * len(plc_list), index=initial_stats_index)
sample_variance_series = pd.Series([0.] * len(plc_list), index=initial_stats_index)
sample_std_dev_series = pd.Series([0.] * len(plc_list), index=initial_stats_index)

# Thread functions
def t_get_ct(plc, index):
    try:
        ct_values_list[index] = float(plc.read('DM', 88)) / 10.
        current_ct_bit_list[index] = plc.read('MR', 5912)
    except Exception as e:
        print(f'Exception at t_get_ct(plc, index): {e} at {PLC_NAMES[index]}')

try:
    # Main loop
    while (True):

        threads = []

        # Fetch PLC's data
        for index, plc in enumerate(plc_list):
            t = threading.Thread(target=t_get_ct, args=(plc, index))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # Update cycle time temporary list of lists
        for index in range(len(ct_values_list)):
            # Look for a rising edge from the PLC's ct status updated bits
            if current_ct_bit_list[index] == True and last_ct_bit_list[index] == False:
                ct_temp_lists[index].append(ct_values_list[index])

            # Keep shifting each ct updated status bit value
            last_ct_bit_list[index] = current_ct_bit_list[index]

        # Convert temporary lists to Pandas dataframe
        if len(ct_temp_lists[-1]) >= SAMPLE_SIZE:
            df = pd.DataFrame(ct_temp_lists).T
            df.columns = PLC_NAMES

            # Calculate statistics
            sample_mean_series = df.mean()
            sample_variance_series = df.var()
            for index, variance in enumerate(sample_variance_series):
                sample_std_dev_series.iloc[index] = math.sqrt(variance)

            # Create data frame for statistics
            statistics_data = {
                'Mean': sample_mean_series,
                'Variance': sample_variance_series,
                'Std Dev': sample_std_dev_series
            }
            df_stats = pd.DataFrame(statistics_data)    

            # Export data to Excel file
            with pd.ExcelWriter(FILENAME) as writer:
                # Sheet 1: Cycle Time Samples
                df.to_excel(writer, sheet_name='CT_Samples', index=False)
                # Sheet 2: Statistics
                df_stats.to_excel(writer, sheet_name='Statistics', index=True)
            print(f'\n--- Successfully exported {SAMPLE_SIZE} samples to {FILENAME} ---')

            # Clean lists values to start a new sample
            ct_temp_lists = [[] for _ in range(len(plc_list))]

        # Print in terminal
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.write('\033[H')  # Move cursor to top left
        sys.stdout.write('\033[2K\r')  # Clear line and move to start
        sys.stdout.write(f'Calculating statistics for {SAMPLE_SIZE} samples')
        sys.stdout.write('\n')  # Move to next line
        for i in range(len(PLC_NAMES)):
            sys.stdout.write(f'{PLC_NAMES[i]}: {ct_values_list[i]} seconds')
            sys.stdout.write(f', {len(ct_temp_lists[i])} samples')
            sys.stdout.write(f', μ = {sample_mean_series.iloc[i]:.4f}')
            sys.stdout.write(f', σ² = {sample_variance_series.iloc[i]:.4f}')
            sys.stdout.write(f', σ = {sample_std_dev_series.iloc[i]:.4f}')
            sys.stdout.write('\n')  # Move to next line
        sys.stdout.flush()

except KeyboardInterrupt:
    print("\nProgram terminated by user (Ctrl+C). Exiting gracefully.")
    sys.exit(0)