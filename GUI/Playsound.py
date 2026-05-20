"""
TwinCAT ADS Sound Player
GUI application to configure and run an ADS-triggered sound player.
Requires: pyads  (pip install pyads)
"""

import os
import sys
import time
import queue
import threading
import winsound
import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import pyads
except ImportError:
    pyads = None

# ── Config file sits next to the exe (or script) ──────────────────────────────
BASE_DIR    = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config.ini')

DEFAULTS = {
    'ams_net_id': '199.4.42.250.1.1',
    'port':       '851',
    'var_sound':  'MAIN.bSound',
    'var_select': 'MAIN.nSoundSelect',
    'sound_1':    '',
    'sound_2':    '',
    'sound_3':    '',
    'sound_4':    '',
    'sound_5':    '',
}


class SoundPlayerApp:
    def __init__(self, root):
        self.root = root
        self.root.title('TwinCAT ADS Sound Player')
        self.root.resizable(False, False)

        self.log_queue      = queue.Queue()
        self.listener_thread = None
        self.running        = False

        self.cfg = configparser.ConfigParser()
        self._load_config()
        self._build_gui()
        self._poll_log()

    # ── Config ────────────────────────────────────────────────────────────────

    def _load_config(self):
        self.cfg.read(CONFIG_PATH)
        for section in ('ADS', 'PLC', 'Sounds'):
            if section not in self.cfg:
                self.cfg[section] = {}

    def _save_config(self):
        self.cfg['ADS']['ams_net_id'] = self.var_ams.get().strip()
        self.cfg['ADS']['port']       = self.var_port.get().strip()
        self.cfg['PLC']['var_sound']  = self.var_bsound.get().strip()
        self.cfg['PLC']['var_select'] = self.var_select.get().strip()
        self.cfg['Sounds']['sound_1'] = self.var_sound1.get().strip()
        self.cfg['Sounds']['sound_2'] = self.var_sound2.get().strip()
        self.cfg['Sounds']['sound_3'] = self.var_sound3.get().strip()
        self.cfg['Sounds']['sound_4'] = self.var_sound4.get().strip()
        self.cfg['Sounds']['sound_5'] = self.var_sound5.get().strip()
        with open(CONFIG_PATH, 'w') as f:
            self.cfg.write(f)
        self._log('Config saved.')

    # ── GUI ───────────────────────────────────────────────────────────────────

    def _build_gui(self):
        PAD = dict(padx=10, pady=6)

        # ── ADS Connection ────────────────────────────────────────────────────
        frm_ads = ttk.LabelFrame(self.root, text=' ADS Connection ')
        frm_ads.grid(row=0, column=0, sticky='ew', **PAD)

        ttk.Label(frm_ads, text='AMS Net ID:').grid(row=0, column=0, sticky='w', padx=6, pady=4)
        self.var_ams = tk.StringVar(value=self.cfg.get('ADS', 'ams_net_id', fallback=DEFAULTS['ams_net_id']))
        ttk.Entry(frm_ads, textvariable=self.var_ams, width=20).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(frm_ads, text='Port:').grid(row=0, column=2, sticky='w', padx=6)
        self.var_port = tk.StringVar(value=self.cfg.get('ADS', 'port', fallback=DEFAULTS['port']))
        ttk.Entry(frm_ads, textvariable=self.var_port, width=6).grid(row=0, column=3, padx=4, pady=4)

        ttk.Button(frm_ads, text='Test Connection', command=self._test_connection).grid(row=0, column=4, padx=10, pady=4)

        self.lbl_conn = ttk.Label(frm_ads, text='● Not tested', foreground='gray', width=16)
        self.lbl_conn.grid(row=0, column=5, padx=6)

        # ── PLC Variables ─────────────────────────────────────────────────────
        frm_plc = ttk.LabelFrame(self.root, text=' PLC Variables ')
        frm_plc.grid(row=1, column=0, sticky='ew', **PAD)

        ttk.Label(frm_plc, text='Sound trigger (BOOL):').grid(row=0, column=0, sticky='w', padx=6, pady=4)
        self.var_bsound = tk.StringVar(value=self.cfg.get('PLC', 'var_sound', fallback=DEFAULTS['var_sound']))
        ttk.Entry(frm_plc, textvariable=self.var_bsound, width=28).grid(row=0, column=1, padx=4, pady=4)

        ttk.Label(frm_plc, text='Sound select (INT):').grid(row=1, column=0, sticky='w', padx=6, pady=4)
        self.var_select = tk.StringVar(value=self.cfg.get('PLC', 'var_select', fallback=DEFAULTS['var_select']))
        ttk.Entry(frm_plc, textvariable=self.var_select, width=28).grid(row=1, column=1, padx=4, pady=4)

        # ── Sound Files ───────────────────────────────────────────────────────
        frm_snd = ttk.LabelFrame(self.root, text=' Sound Files (WAV only) ')
        frm_snd.grid(row=2, column=0, sticky='ew', **PAD)

        self.var_sound1 = tk.StringVar(value=self.cfg.get('Sounds', 'sound_1', fallback=''))
        self.var_sound2 = tk.StringVar(value=self.cfg.get('Sounds', 'sound_2', fallback=''))
        self.var_sound3 = tk.StringVar(value=self.cfg.get('Sounds', 'sound_3', fallback=''))
        self.var_sound4 = tk.StringVar(value=self.cfg.get('Sounds', 'sound_4', fallback=''))
        self.var_sound5 = tk.StringVar(value=self.cfg.get('Sounds', 'sound_5', fallback=''))

        for idx, (label, var) in enumerate([
            ('Sound 1:', self.var_sound1),
            ('Sound 2:', self.var_sound2),
            ('Sound 3:', self.var_sound3),
            ('Sound 4:', self.var_sound4),
            ('Sound 5:', self.var_sound5),
        ]):
            ttk.Label(frm_snd, text=label).grid(row=idx, column=0, sticky='w', padx=6, pady=4)
            ttk.Entry(frm_snd, textvariable=var, width=42).grid(row=idx, column=1, padx=4, pady=4)
            ttk.Button(frm_snd, text='Browse',
                       command=lambda v=var: self._browse(v)).grid(row=idx, column=2, padx=4, pady=4)
            ttk.Button(frm_snd, text='▶ Test',
                       command=lambda v=var: self._test_sound(v)).grid(row=idx, column=3, padx=4, pady=4)

        # ── Controls ──────────────────────────────────────────────────────────
        frm_ctrl = ttk.Frame(self.root)
        frm_ctrl.grid(row=3, column=0, sticky='ew', **PAD)

        ttk.Button(frm_ctrl, text='💾  Save Config', command=self._save_config).pack(side='left', padx=4)

        self.btn_stop  = ttk.Button(frm_ctrl, text='■  Stop',           command=self._stop,  state='disabled')
        self.btn_start = ttk.Button(frm_ctrl, text='▶  Start Listener', command=self._start)
        self.btn_stop.pack(side='right', padx=4)
        self.btn_start.pack(side='right', padx=4)

        # ── Log ───────────────────────────────────────────────────────────────
        frm_log = ttk.LabelFrame(self.root, text=' Log ')
        frm_log.grid(row=4, column=0, sticky='ew', **PAD)

        self.txt_log = tk.Text(
            frm_log, height=9, width=72, state='disabled',
            bg='#1e1e1e', fg='#cccccc', font=('Consolas', 9),
            relief='flat', borderwidth=0
        )
        scrollbar = ttk.Scrollbar(frm_log, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=scrollbar.set)
        self.txt_log.pack(side='left', padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _browse(self, var):
        path = filedialog.askopenfilename(
            title='Select WAV file',
            filetypes=[('WAV files', '*.wav'), ('All files', '*.*')]
        )
        if path:
            var.set(path)

    def _test_sound(self, var):
        path = var.get().strip()
        if not path:
            messagebox.showwarning('No file', 'No file path entered.')
            return
        if not os.path.exists(path):
            messagebox.showerror('Not found', f'File not found:\n{path}')
            return
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        self._log(f'Testing: {os.path.basename(path)}')

    def _test_connection(self):
        if pyads is None:
            messagebox.showerror('Missing library', 'pyads is not installed.\nRun: pip install pyads')
            return
        self.lbl_conn.config(text='● Testing...', foreground='orange')
        self.root.update()
        try:
            plc = pyads.Connection(self.var_ams.get().strip(), int(self.var_port.get().strip()))
            plc.open()
            plc.close()
            self.lbl_conn.config(text='● Connected', foreground='green')
            self._log(f'Connection OK — {self.var_ams.get()}:{self.var_port.get()}')
        except Exception as e:
            self.lbl_conn.config(text='✗ Failed', foreground='red')
            self._log(f'Connection failed: {e}')

    def _start(self):
        if pyads is None:
            messagebox.showerror('Missing library', 'pyads is not installed.\nRun: pip install pyads')
            return
        self._save_config()
        self.running = True
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self.listener_thread.start()

    def _stop(self):
        self.running = False
        winsound.PlaySound(None, winsound.SND_PURGE)
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        self._log('Listener stopped.')

    # ── ADS listener (runs in background thread) ──────────────────────────────

    def _listener_loop(self):
        sounds = {
            1: self.var_sound1.get().strip(),
            2: self.var_sound2.get().strip(),
            3: self.var_sound3.get().strip(),
            4: self.var_sound4.get().strip(),
            5: self.var_sound5.get().strip(),
        }
        # Use a list so the nested callback can mutate it
        current_sound = [sounds.get(1, '')]

        try:
            plc = pyads.Connection(self.var_ams.get().strip(), int(self.var_port.get().strip()))
            plc.open()
            self._log(f'Connected to {self.var_ams.get()}')

            @plc.notification(pyads.PLCTYPE_BOOL)
            def on_sound_change(handle, name, timestamp, value):
                if value:
                    path = current_sound[0]
                    if path and os.path.exists(path):
                        self._log(f'▶ Playing: {os.path.basename(path)}')
                        winsound.PlaySound(
                            path,
                            winsound.SND_FILENAME | winsound.SND_LOOP | winsound.SND_ASYNC
                        )
                    else:
                        self._log('⚠ Sound file not found — check config.')
                else:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                    self._log('■ Sound stopped.')

            @plc.notification(pyads.PLCTYPE_INT)
            def on_select_change(handle, name, timestamp, value):
                if value in sounds:
                    current_sound[0] = sounds[value]
                    self._log(f'Sound {value} selected: {os.path.basename(current_sound[0])}')
                else:
                    self._log(f'⚠ Sound index {value} not configured.')

            attr_bool = pyads.NotificationAttrib(1)   # BOOL = 1 byte
            attr_int  = pyads.NotificationAttrib(2)   # INT  = 2 bytes

            h1 = plc.add_device_notification(self.var_bsound.get().strip(), attr_bool, on_sound_change)
            h2 = plc.add_device_notification(self.var_select.get().strip(), attr_int,  on_select_change)

            self._log(f'Listening — trigger: {self.var_bsound.get()}  |  select: {self.var_select.get()}')

            while self.running:
                time.sleep(0.5)

            plc.del_device_notification(*h1)
            plc.del_device_notification(*h2)
            plc.close()
            self._log('ADS connection closed.')

        except Exception as e:
            self._log(f'Error: {e}')
            self.root.after(0, self._stop)

    # ── Log helpers ───────────────────────────────────────────────────────────

    def _log(self, message):
        self.log_queue.put(f'[{time.strftime("%H:%M:%S")}]  {message}')

    def _poll_log(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.txt_log.config(state='normal')
            self.txt_log.insert('end', msg + '\n')
            self.txt_log.see('end')
            self.txt_log.config(state='disabled')
        self.root.after(100, self._poll_log)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    root = tk.Tk()
    app = SoundPlayerApp(root)
    root.mainloop()
