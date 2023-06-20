import tkinter as tk
import tkinter.filedialog as fd
import os

# temporarily add vendor to PATH, mpv requires it
vendor_path = os.path.abspath('vendor')
os.environ['PATH'] = os.pathsep.join([vendor_path, os.environ['PATH']])

from vendor import mpv

class ReactionSync:
    def __init__(self, master):
        self.master = master
        self.configure_master()
        self._initialize_widgets()
        self._initialize_video_player_variables()
        self.master.protocol("WM_DELETE_WINDOW", self.on_close_GUI)
        
    def configure_master(self):
        self.master.title("ReactionSync")
        self.master.resizable(False, False)
        self.master.geometry("300x150")

    def _initialize_widgets(self):
        self.file_label_A = self._create_file_label("No file selected")
        self.file_label_B = self._create_file_label("No file selected")
        self.browse_button_A = self._create_browse_button("Browse Reaction", self.file_label_A, "video_file_A")
        self.browse_button_B = self._create_browse_button("Browse Content", self.file_label_B, "video_file_B")
        self.play_button = self._create_play_button()
        self.sync_button = self._create_sync_button()
        self.reduce_delay_button = self._create_reduce_delay_button()
        self.increase_delay_button = self._create_increase_delay_button()
        self.status_label = self._create_status_label()

    def _initialize_video_player_variables(self):
        self.player_A = None
        self.player_B = None
        self.video_file_A = None
        self.video_file_B = None
        self.sync_point = None
        self.delay = 0
    
    def _create_file_label(self, text):
        label = tk.Label(self.master, text=text)
        label.pack()
        return label

    def _create_browse_button(self, text, file_label, video_file_var):
        button = tk.Button(self.master, text=text, command=lambda: self.browse_file(file_label, video_file_var))
        button.pack()
        return button

    def _create_play_button(self):
        button = tk.Button(self.master, text="Play", command=self.play_video)
        button.pack()
        return button

    def _create_sync_button(self):
        button = tk.Button(self.master, text="Sync", width=11, command=self.sync_videos)
        button.pack_forget()
        return button
    

    def _create_reduce_delay_button(self):
        button = tk.Button(self.master, text="<-", command=self.reduce_delay)
        button.place(x=-1000, y=-1000)
        return button

    def _create_increase_delay_button(self):
        button = tk.Button(self.master, text="->", command=self.increase_delay)
        button.place(x=-1000, y=-1000)
        return button

    def _create_status_label(self):
        label = tk.Label(self.master, text="")
        label.pack()
        return label

    def sync_videos(self):
        self.sync_point = self.player_A.time_pos
        self.player_B.pause = self.player_A.pause
        self.delay = 0
        self.status_label.config(text="Synced!")

    def browse_file(self, file_label, video_file_var):
        filetypes = (("Video files", "*.mp4 *.avi *.mkv"), ("All files", "*.*"))
        filepath = fd.askopenfilename(filetypes=filetypes)
        if filepath:
            setattr(self, video_file_var, filepath)
            filename = os.path.basename(filepath)
            file_label.config(text=filename)
            if self.video_file_A and self.video_file_B:
                self.status_label.config(text="Ready to play!")

    def play_video(self):
        if self.video_file_A and self.video_file_B:
            self.init_player_A()
            self.init_player_B()
            self.player_A.play(self.video_file_A)
            self.player_B.play(self.video_file_B)
            self._toggle_sync_controls()

    def _toggle_sync_controls(self):
        self.browse_button_A.pack_forget()
        self.browse_button_B.pack_forget()
        self.play_button.pack_forget()
        self.file_label_A.pack_forget()
        self.file_label_B.pack_forget()
        self.status_label.pack_forget()
        
        self.status_label.place(x=150, y=130, anchor="center")
        self.sync_button.place(x=150, y=48, anchor="center")
        
        self.reduce_delay_button.place(x=130, y=83, anchor="center")
        self.increase_delay_button.place(x=169, y=83, anchor="center")
        self.status_label.config(text="Ready to sync.")

    def init_player_A(self):
        self.player_A = mpv.MPV(input_default_bindings=True, input_vo_keyboard=True, osc=True, keep_open=True)
        self.player_A.autofit = '800'
        self._observe_player_A_properties()

    def _observe_player_A_properties(self):
        self.player_A.observe_property('pause', self.on_pause_A)
        self.player_A.observe_property('seeking', self.on_seek_A)
        self.player_A.observe_property('playback-time', self.while_playing)
        self.player_A.register_event_callback(self.handle_event)

    def init_player_B(self):
        self.player_B = mpv.MPV(ontop=True, osc=True, pause=True, border=False, input_default_bindings=True, keep_open=True)
        self.player_B.autofit = '500'

    def on_close_GUI(self):
        self.master.destroy()

    def on_quit_mpv_A(self, name, value):
        if not self.player_A.duration:
            if not self.ignore_first_eof_A:
                self.master.destroy()
            self.ignore_first_eof_A = False

    def on_pause_A(self, name, value):
        if self.player_B and self.sync_point:
            self.player_B.pause = self.player_A.pause

    def on_seek_A(self, name, value):
        if self.player_B and self.sync_point:
            if value == False:
                self._update_player_B_position()

    def _update_player_B_position(self):
        try:
            if self.player_A.time_pos <= self.sync_point:
                self.player_B.time_pos = 0
                self.player_B.pause = True
            elif self.player_A.time_pos >= self.sync_point + self.player_B.duration:
                self.player_B.time_pos = self.player_B.duration - 0.1
                self.player_B.pause = True
            else:
                self.player_B.time_pos = self.player_A.time_pos - self.sync_point
                self.player_B.pause = self.player_A.pause
        except:
            self.on_close_GUI()

    def increase_delay(self):
        if self.sync_point:
            self.sync_point += 0.1
            self.delay += 100
            self.status_label.config(text=f"Timing: {self.delay} ms")
            self._update_player_B_position()

    def reduce_delay(self):
        if self.sync_point:
            self.sync_point -= 0.1
            self.delay -= 100
            self.status_label.config(text=f"Timing: {self.delay} ms")
            self._update_player_B_position()

    def while_playing(self, name, value):
        try:
            if self.player_B and self.sync_point:
                if self.player_B.time_pos > self.player_B.duration - 0.1 and self.player_B.pause == False:
                    self.player_B.pause = True
                elif self.player_A.time_pos >= self.sync_point and self.player_B.time_pos < self.player_B.duration - 1 and self.player_B.pause != self.player_A.pause:
                    self.player_B.pause = self.player_A.pause
        except:
            self.on_close_GUI()
            
    def handle_event(self, event):
        if event.event_id.value == mpv.MpvEventID.SHUTDOWN:
            self.on_close_GUI()


if __name__ == "__main__":
    root = tk.Tk()
    app = ReactionSync(root)
    root.mainloop()
