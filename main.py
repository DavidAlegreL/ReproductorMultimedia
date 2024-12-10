import vlc
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import os
import sys

from mutagen.easyid3 import EasyID3
from mutagen.mp3 import MP3
from pymediainfo import MediaInfo

def analyze_mp3(file_path):
    try:
        audio = EasyID3(file_path)
        metadata = {
            "Título": audio.get("title", ["Desconocido"])[0],
            "Artista": audio.get("artist", ["Desconocido"])[0],
            "Álbum": audio.get("album", ["Desconocido"])[0],
            "Género": audio.get("genre", ["Desconocido"])[0],
        }

        audio_file = MP3(file_path)
        duration = int(audio_file.info.length)
        metadata["Duración"] = f"{duration // 60}:{duration % 60:02d} min"

        return metadata

    except Exception as e:
        return {"Error": f"Error al analizar el MP3: {e}"}


def analyze_video(file_path):
    try:
        media_info = MediaInfo.parse(file_path)
        video_track = next(
            (track for track in media_info.tracks if track.track_type == "Video"), None
        )
        audio_track = next(
            (track for track in media_info.tracks if track.track_type == "Audio"), None
        )

        metadata = {
            "Formato": video_track.format if video_track else "Desconocido",
            "Resolución": (
                f"{video_track.width}x{video_track.height}" if video_track else "Desconocido"
            ),
            "Duración": (
                f"{int(video_track.duration / 1000) // 60}:{int(video_track.duration / 1000) % 60:02d} min"
                if video_track and video_track.duration
                else "Desconocido"
            ),
            "Codec de audio": audio_track.codec if audio_track else "Desconocido",
            "Canales de audio": audio_track.channel_s if audio_track else "Desconocido",
        }

        return metadata

    except Exception as e:
        return {"Error": f"Error al analizar el video: {e}"}


class MediaPlayer:
    def __init__(self, master):
        self.master = master
        self.blue_color = "#2c3e50"
        self.orange_color = "#f39c12"
        self.master.title("Reproductor Multimedia")
        self.master.geometry("900x600")
        self.master.configure(bg=self.blue_color)

        # VLC config
        os.environ["VLC_VERBOSE"] = "-1"
        devnull = open(os.devnull, 'w')
        sys.stderr = devnull

        self.instance = vlc.Instance("--no-xlib","--avcodec-hw=none","--file-caching=3000","--quiet","--verbose=0")
        self.media_player = self.instance.media_player_new()
        self.media_player.video_set_adjust_int(vlc.VideoAdjustOption.Enable, 1)

        self.current_volume = 50
        self.media = None
        self.is_playing = False
        self.is_updating = False
        self.is_fullscreen = False
        self.is_orange = False  # Estado del fondo (False = Azul, True = Naranja)

        # Estilo de ttk para botones
        self.style = ttk.Style()
        self.style.theme_use("clam")
        # Fuente en botones
        self.style.configure("TButton", font=("Helvetica", 10, "bold"), foreground="white", background=self.blue_color)
        self.style.map("TButton", background=[("active", self.blue_color)])

        # Panel video
        self.video_panel = tk.Canvas(master, bg="black", bd=2, relief="ridge", highlightthickness=0)
        self.video_panel.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # Frames convertidos a tk.Frame para cambiar bg fácilmente
        self.metadata_frame = tk.Frame(master, bg=self.blue_color)
        self.metadata_frame.pack(fill="x", padx=10, pady=5)
        self.metadata_label = tk.Label(self.metadata_frame, text="Metadatos: No cargados", font=("Helvetica", 11, "bold"), bg=self.blue_color, fg="white")
        self.metadata_label.pack(fill="x")

        self.effects_frame = tk.Frame(master, bg=self.blue_color)
        self.effects_frame.pack(fill="x", padx=10, pady=5)
        self.effects_inner_frame = tk.Frame(self.effects_frame, bg=self.blue_color)
        self.effects_inner_frame.pack(anchor="center", expand=True)

        tk.Label(self.effects_inner_frame, text="Brillo:", bg=self.blue_color, fg="white", font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
        self.brightness_slider = ttk.Scale(self.effects_inner_frame, from_=0, to=2, orient="horizontal", command=self.set_brightness)
        self.brightness_slider.set(1)
        self.brightness_slider.pack(side="left", padx=5)

        tk.Label(self.effects_inner_frame, text="Contraste:", bg=self.blue_color, fg="white", font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
        self.contrast_slider = ttk.Scale(self.effects_inner_frame, from_=0, to=2, orient="horizontal", command=self.set_contrast)
        self.contrast_slider.set(1)
        self.contrast_slider.pack(side="left", padx=5)

        tk.Label(self.effects_inner_frame, text="Saturación:", bg=self.blue_color, fg="white", font=("Helvetica", 10, "bold")).pack(side="left", padx=5)
        self.saturation_slider = ttk.Scale(self.effects_inner_frame, from_=0, to=2, orient="horizontal", command=self.set_saturation)
        self.saturation_slider.set(1)
        self.saturation_slider.pack(side="left", padx=5)

        self.progress_bar_frame = tk.Frame(master, bg=self.blue_color)
        self.progress_bar_frame.pack(fill="x", pady=5)

        self.progress_bar = ttk.Scale(self.progress_bar_frame, from_=0, to=100, orient="horizontal", command=self.seek_video)
        self.progress_bar.pack(fill="x", padx=10)
        self.progress_tooltip = tk.Label(self.master, text="", bg="white", fg="black", font=("Helvetica", 9), bd=1, relief="solid")
        self.progress_bar.bind("<Motion>", self.update_progress_tooltip)
        self.progress_bar.bind("<Leave>", lambda e: self.progress_tooltip.place_forget())

        self.buttons_frame = tk.Frame(master, bg=self.blue_color)
        self.buttons_frame.pack(side="bottom", pady=10)

        # Cargar íconos
        self.play_icon = self.load_icon("assets/play_arrow.png")
        self.stop_icon = self.load_icon("assets/stop_button.png")
        self.quit_icon = self.load_icon("assets/quit_button.png")
        self.load_file_icon = self.load_icon("assets/load_file.png")
        self.forward_icon = self.load_icon("assets/forward_arrow.png")
        self.backward_icon = self.load_icon("assets/backward_arrow.png")
        self.volume_icon_low = self.load_icon("assets/volume_low.png")
        self.volume_icon_medium = self.load_icon("assets/volume_medium.png")
        self.volume_icon_high = self.load_icon("assets/volume_high.png")
        self.volume_icon_mute = self.load_icon("assets/volume_mute.png")
        self.mini_player_icon = self.load_icon("assets/mini_player.png")
        self.fullscreen_icon = self.load_icon("assets/fullscreen.jpeg")
        self.naranja_icon = self.load_icon("assets/naranja.png")
        self.azul_icon = self.load_icon("assets/azul.png")

        # Botones
        ttk.Button(self.buttons_frame, image=self.backward_icon, command=self.backward_5_seconds).pack(side="left", padx=5)
        ttk.Button(self.buttons_frame, image=self.play_icon, command=self.play_video).pack(side="left", padx=5)
        ttk.Button(self.buttons_frame, image=self.forward_icon, command=self.forward_5_seconds).pack(side="left", padx=5)
        ttk.Button(self.buttons_frame, image=self.stop_icon, command=self.pause_video).pack(side="left", padx=5)
        ttk.Button(self.buttons_frame, image=self.quit_icon, command=self.stop_video).pack(side="left", padx=5)
        ttk.Button(self.buttons_frame, image=self.load_file_icon, command=self.load_file).pack(side="left", padx=5)
        ttk.Button(self.buttons_frame, image=self.mini_player_icon, command=self.show_mini_player).pack(side="left", padx=5)

        self.fullscreen_button = ttk.Button(self.buttons_frame, image = self.fullscreen_icon, command=self.toggle_fullscreen)
        self.fullscreen_button.pack(side="left", padx=5)

        self.orange_button = ttk.Button(self.buttons_frame, image=self.naranja_icon, command=self.toggle_background_color)
        self.orange_button.pack(side="left", padx=5)

        self.volume_icon_label = tk.Label(self.buttons_frame, image=self.volume_icon_medium, bg=self.blue_color)
        self.volume_icon_label.pack(side="right", padx=5)
        self.volume_control = ttk.Scale(self.buttons_frame, from_=0, to=100, orient="horizontal", command=self.set_volume)
        self.volume_control.set(50)
        self.volume_control.pack(side="right", padx=10)

        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_icon(self, path):
        try:
            #Uso de rutas relativas para el correcto funcionamiento del ejecutable.
            base_path = os.path.dirname(os.path.abspath(__file__))  
            full_path = os.path.join(base_path, path)  
            icon = Image.open(full_path)
            icon = icon.resize((30, 30), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(icon)
        except Exception as e:
            print(f"No se pudo cargar el ícono {path}: {e}")
            return None


    def set_video_output(self, media_player, panel):
        video_window_id = panel.winfo_id()
        if sys.platform.startswith('win'):
            media_player.set_hwnd(video_window_id)
        elif sys.platform.startswith('darwin'):
            media_player.set_nsobject(video_window_id)
        else:
            self.media_player.set_xwindow(video_window_id)

    def load_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Archivos multimedia", "*.mp3 *.mp4 *.avi *.mkv"), ("Todos los archivos", "*.*")]
        )
        if file_path:
            self.media = self.instance.media_new(file_path)
            self.media_player.set_media(self.media)
            self.set_video_output(self.media_player, self.video_panel)

            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".mp3":
                metadata = analyze_mp3(file_path)
            else:
                metadata = analyze_video(file_path)

            metadata_str = "Metadatos:\n"
            for k, v in metadata.items():
                metadata_str += f"{k}: {v}\n"
            self.metadata_label.config(text=metadata_str)

            self.play_video()

    def play_video(self):
        if self.media:
            self.media_player.play()
            self.is_playing = True
            self.update_progress_bar()

    def pause_video(self):
        if self.media:
            self.media_player.pause()
            self.is_playing = False

    def stop_video(self):
        if self.media:
            self.media_player.stop()
            self.is_playing = False
            self.progress_bar.set(0)

    def forward_5_seconds(self):
        if self.media:
            current_time = self.media_player.get_time()
            self.media_player.set_time(current_time + 5000)

    def backward_5_seconds(self):
        if self.media:
            current_time = self.media_player.get_time()
            new_time = max(0, current_time - 5000)
            self.media_player.set_time(new_time)

    def set_volume(self, value):
        # Interpretar el valor directamente de la barra
        adjusted_value = int(float(value))  # El volumen ahora coincide con la barra (0 a 100)
        self.media_player.audio_set_volume(adjusted_value)  # Ajustar el volumen de VLC

        # Cambiar el ícono del volumen en función del nivel
        if adjusted_value == 0:
            self.volume_icon_label.config(image=self.volume_icon_mute)
        elif adjusted_value < 30:
            self.volume_icon_label.config(image=self.volume_icon_low)
        elif adjusted_value < 70:
            self.volume_icon_label.config(image=self.volume_icon_medium)
        else:
            self.volume_icon_label.config(image=self.volume_icon_high)


    def set_brightness(self, value):
        if self.media:
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Brightness, float(value))

    def set_contrast(self, value):
        if self.media:
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Contrast, float(value))

    def set_saturation(self, value):
        if self.media:
            self.media_player.video_set_adjust_float(vlc.VideoAdjustOption.Saturation, float(value))

    def seek_video(self, value):
        if not self.is_updating and self.media:
            total_time = self.media_player.get_length()
            if total_time > 0:
                new_time = int(float(value) / 100 * total_time)
                self.media_player.set_time(new_time)

    def update_progress_tooltip(self, event):
        if self.media:
            total_time = self.media_player.get_length()
            if total_time > 0:
                x = self.progress_bar.winfo_pointerx() - self.progress_bar.winfo_rootx()
                position = (x / self.progress_bar.winfo_width()) * total_time
                minutes, seconds = divmod(int(position // 1000), 60)
                self.progress_tooltip.config(text=f"{minutes}:{seconds:02}")
                self.progress_tooltip.place(x=event.x_root, y=event.y_root - 20)

    def update_progress_bar(self):
        if self.is_playing and self.media:
            try:
                total_time = self.media_player.get_length()
                current_time = self.media_player.get_time()

                if total_time > 0 and current_time >= 0:
                    progress = (current_time / total_time) * 100
                    self.is_updating = True
                    self.progress_bar.set(progress)
                    self.is_updating = False
            except Exception as e:
                print(f"Error al actualizar la barra de progreso: {e}")

            self.master.after(500, self.update_progress_bar)

    def show_mini_player(self):
        if not hasattr(self, 'mini_window') or self.mini_window is None:
            self.mini_window = tk.Toplevel(self.master)
            self.mini_window.title("Mini Player")
            self.mini_window.geometry("300x200")
            self.mini_window.attributes("-topmost", True)
            self.mini_window.protocol("WM_DELETE_WINDOW", self.hide_mini_player)

            self.mini_panel = tk.Canvas(self.mini_window, bg="black", bd=2, relief="ridge", highlightthickness=0)
            self.mini_panel.pack(fill="both", expand=True)

            ttk.Button(self.mini_window, text="Volver", command=self.hide_mini_player).pack(pady=5)

        self.master.withdraw()

        current_time = self.media_player.get_time() if self.media else 0
        is_playing = self.is_playing

        self.media_player.stop()
        self.media_player.release()

        self.media_player = self.instance.media_player_new()
        if self.media:
            self.media_player.set_media(self.media)
        self.set_video_output(self.media_player, self.mini_panel)
        self.media_player.play()
        self.media_player.set_time(current_time)
        self.media_player.audio_set_volume(100 - self.current_volume)

        if not is_playing:
            self.media_player.pause()

        self.is_playing = is_playing

    def hide_mini_player(self):
        if self.mini_window:
            self.mini_window.destroy()
            self.mini_window = None
            self.mini_panel = None

        current_time = self.media_player.get_time() if self.media else 0
        is_playing = self.is_playing

        self.media_player.stop()
        self.media_player.release()

        self.media_player = self.instance.media_player_new()
        if self.media:
            self.media_player.set_media(self.media)
        self.set_video_output(self.media_player, self.video_panel)
        self.media_player.play()
        self.media_player.set_time(current_time)
        self.media_player.audio_set_volume(100 - self.current_volume)

        if not is_playing:
            self.media_player.pause()

        self.is_playing = is_playing

        self.master.deiconify()

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        self.master.attributes("-fullscreen", self.is_fullscreen)
        if self.is_fullscreen:
            self.metadata_frame_pack_info = self.metadata_frame.pack_info()
            self.effects_frame_pack_info = self.effects_frame.pack_info()
            self.progress_bar_frame_pack_info = self.progress_bar_frame.pack_info()

            self.metadata_frame.pack_forget()
            self.effects_frame.pack_forget()
            self.progress_bar_frame.pack_forget()

            self.video_panel.config(bd=0, highlightthickness=0)
            self.video_panel.pack_configure(padx=0, pady=0)
        else:
            self.master.geometry("900x600")

            self.metadata_frame.pack(**self.metadata_frame_pack_info)
            self.effects_frame.pack(**self.effects_frame_pack_info)
            self.progress_bar_frame.pack(**self.progress_bar_frame_pack_info)

            self.video_panel.config(bd=2, highlightthickness=0)
            self.video_panel.pack_configure(padx=10, pady=10)

    def toggle_background_color(self):
        self.is_orange = not self.is_orange
        if self.is_orange:
            # Fondo naranja
            bg_color = self.orange_color
            self.orange_button.config(image=self.azul_icon)
        else:
            # Fondo azul
            bg_color = self.blue_color
            self.orange_button.config(image= self.naranja_icon)

        # Cambiar fondo de ventana
        self.master.configure(bg=bg_color)
        # Cambiar frames
        self.metadata_frame.config(bg=bg_color)
        self.effects_frame.config(bg=bg_color)
        self.effects_inner_frame.config(bg=bg_color)
        self.progress_bar_frame.config(bg=bg_color)
        self.buttons_frame.config(bg=bg_color)
        # Cambiar label metadatos
        self.metadata_label.config(bg=bg_color, fg="white")
        # Cambiar ícono de volumen
        self.volume_icon_label.config(bg=bg_color)
        
        # Cambiar estilo de TButton según fondo
        self.style.configure("TButton", background=bg_color, foreground="white")
        self.style.map("TButton", background=[("active", bg_color)])

        # Los labels dentro de effects_inner_frame también dependen del fondo
        for w in self.effects_inner_frame.winfo_children():
            if isinstance(w, tk.Label):
                w.config(bg=bg_color, fg="white")

    def on_close(self):
        self.media_player.stop()
        self.media_player.release()
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    player = MediaPlayer(root)
    root.mainloop()
