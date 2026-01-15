# from inspire_dds import inspire_hand_touch,inspire_hand_ctrl,inspire_hand_state
# from inspire_dds import inspire_hand_touch,inspire_hand_ctrl,inspire_hand_state
import sys
from inspire_sdkpy import inspire_sdk,inspire_hand_defaut
import time
# import inspire_sdkpy
if __name__ == "__main__":
    
    
    # handler=inspire_sdk.ModbusDataHandler(ip=inspire_hand_defaut.defaut_ip,LR='r',device_id=1)
    handler=inspire_sdk.ModbusDataHandler(ip='192.168.123.211',LR='l',device_id=1)
    time.sleep(0.5)

    call_count = 0  # Record call count
    start_time = time.perf_counter()  # Record start time

    try:
        while True:
            data_dict = handler.read()  # Read data

            call_count += 1  # Increment call count
            time.sleep(0.001)  # Pause 1 millisecond

            # Calculate and print call frequency
            if call_count % 10 == 0:  # Calculate frequency every 10 calls
                elapsed_time = time.perf_counter() - start_time  # Calculate total elapsed time
                frequency = call_count / elapsed_time  # Calculate frequency (Hz)
                print(f"Current frequency: {frequency:.2f} Hz, calls: {call_count}, elapsed time: {elapsed_time:.6f} seconds")
    except KeyboardInterrupt:
        elapsed_time = time.perf_counter() - start_time  # Calculate total elapsed time
        frequency = call_count / elapsed_time if elapsed_time > 0 else 0  # Calculate final frequency
        print(f"Program ended. Total calls: {call_count}, total time: {elapsed_time:.6f} seconds, final frequency: {frequency:.2f} Hz")
