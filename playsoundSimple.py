import pyads
import winsound
import os
import time

# ── Config ────────────────────────────────────────────────────────────────────
AMS_NET_ID  = '199.4.42.250.1.1'
PLC_PORT    = 851
SOUND_DIR   = (r'C:\Users\YonatanA\Documents\Yonatan\Work\Technical'
               r'\TwinCAT projects\4026\PLC2Windowsapp'
               r'\PLC2Windowsapp\SoundPlayer')

SOUNDS = {
    1: os.path.join(SOUND_DIR, '1.wav'),
    2: os.path.join(SOUND_DIR, '2.wav'),
    3: os.path.join(SOUND_DIR, '3.wav'),
}
# ──────────────────────────────────────────────────────────────────────────────

current_sound = SOUNDS[1]  # default

plc = pyads.Connection(AMS_NET_ID, PLC_PORT)
plc.open()

@plc.notification(pyads.PLCTYPE_BOOL)
def on_sound_change(handle, name, timestamp, value):
    if value:
        winsound.PlaySound(current_sound, winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC)
    else:
        winsound.PlaySound(None, winsound.SND_PURGE)

@plc.notification(pyads.PLCTYPE_INT)
def on_select_change(handle, name, timestamp, value):
    global current_sound
    if value in SOUNDS:
        current_sound = SOUNDS[value]
        print(f'Sound selected: {value}.wav')
    else:
        print(f'Warning: sound {value} not found, keeping current.')

attr_bool = pyads.NotificationAttrib(1)   # BOOL = 1 byte
attr_int  = pyads.NotificationAttrib(2)   # INT  = 2 bytes

handles_sound  = plc.add_device_notification('MAIN.bSound',       attr_bool, on_sound_change)
handles_select = plc.add_device_notification('MAIN.nSoundSelect', attr_int,  on_select_change)

print('Listening — press Ctrl+C to stop.')
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print('Stopping.')
finally:
    plc.del_device_notification(*handles_sound)
    plc.del_device_notification(*handles_select)
    plc.close()