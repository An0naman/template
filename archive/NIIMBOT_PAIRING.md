Manual Pairing Steps for Niimbot Printers
==========================================

1. Make sure printer is ON and in pairing mode (blue light flashing)

2. Open bluetoothctl:
   $ bluetoothctl

3. Start scanning:
   [bluetooth]# scan on
   
   Wait until you see your printer appear (e.g., "B1-H713123375" or "D110-...")

4. Stop scanning:
   [bluetooth]# scan off

5. Pair with the printer (use the MAC address that appeared):
   [bluetooth]# pair 13:07:12:A6:40:07
   
6. Trust the device:
   [bluetooth]# trust 13:07:12:A6:40:07

7. Connect (optional, for testing):
   [bluetooth]# connect 13:07:12:A6:40:07

8. Exit:
   [bluetooth]# exit

Now run the test script again:
  .venv/bin/python test_niimbot_rfcomm.py
