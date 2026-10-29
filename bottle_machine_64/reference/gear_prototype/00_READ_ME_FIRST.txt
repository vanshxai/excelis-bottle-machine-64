REFERENCE COPY - 150 RPM gear motor prototype (taken 2026-10-06). Do not edit.
Original (untouched): /Users/mac/Desktop/150rpm gear motor prototype/Vansh/150rpm gear system/

What worked end to end on the real rig: ESP32 + INA228 -> USB serial -> Flask app -> block average
-> "Part Interruption" detector (fixed measured current range per gear, 250 ms hold, sticky until
release) -> the touched gear highlights in the 3D view.
Key files:
  gearsystem/detection/live_state.py          the measured ranges + thresholds
  gearsystem/detection/signal_processing.py   process_block(), update_part_interruption()
  gearsystem/detection/acquisition.py         serial gateway, reconnect, DTR/RTS fix
  esp32_ina228_reader/src/main.cpp            working sensor firmware
  PROJECT_DOCUMENTATION.md                    full write-up (the README.md in here is stale)
Left out on purpose: dead ACS712/ESP-NOW firmware (esp32_gearbox_sender), .git, build caches.
