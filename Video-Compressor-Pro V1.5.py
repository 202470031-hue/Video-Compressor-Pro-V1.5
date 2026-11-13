import customtkinter as ctk
from tkinter import filedialog
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import threading
import os
import sys
import re
import psutil
import winsound
import ctypes

# إعداد المظهر
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# مسارات أدوات FFmpeg
FFMPEG_PATH = resource_path("ffmpeg.exe") if os.path.exists(resource_path("ffmpeg.exe")) else "ffmpeg"
FFPROBE_PATH = resource_path("ffprobe.exe") if os.path.exists(resource_path("ffprobe.exe")) else "ffprobe"

def fix_arabic(text):
    return text if text else ""

class ToolTip:
    def __init__(self, widget, text_dict, lang_var):
        self.widget = widget
        self.text_dict = text_dict
        self.lang_var = lang_var
        self.tooltip_window = None
        self.id = None
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        self.unschedule()
        self.id = self.widget.after(400, self.show_tooltip) 

    def leave(self, event=None):
        self.unschedule()
        self.hide_tooltip()

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show_tooltip(self, event=None):
        if self.tooltip_window: return
        lang = self.lang_var.get()
        text = self.text_dict.get(lang, self.text_dict.get("ar"))
        
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        self.tooltip_window = ctk.CTkToplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        self.tooltip_window.attributes("-topmost", True)
        
        label = ctk.CTkLabel(self.tooltip_window, text=text, fg_color="#333", text_color="white", corner_radius=6, padx=10, pady=5, font=("Arial", 12))
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class PremiumCompressorApp(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)
        self.title("Video Compressor Pro - By Eng. Fares Kuliab")
        
        try:
            myappid = 'eng.fares.videocompressor.pro.1.0'
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            icon_path = resource_path("app_icon.ico")
            self.iconbitmap(default=icon_path)
            self.after(200, lambda: self.iconbitmap(icon_path))
        except Exception:
            pass
            
        self.geometry("1050x800")
        self.minsize(900, 650)

        self.lang_var = ctk.StringVar(value="ar")
        
        self.selected_files = []
        self.file_durations = {} 
        self.file_settings = {}
        self.output_directory = ""
        self.current_process = None
        self.is_paused = False
        self.is_cancelled = False
        
        # القواميس والنصوص
        self.i18n = {
            "ar": {
                "title": "أداة ضغط المحاضرات الاحترافية",
                "settings": "⚙️ الإعدادات المتقدمة",
                "language": "🌐 لغة الواجهة (Language):",
                "theme": "🎨 مظهر التطبيق:",
                "theme_dark": "داكن", "theme_light": "فاتح",
                "hardware": "🖥️ مسرع المعالجة (Hardware):",
                "quality": "🎚️ جودة وترميز الفيديو:",
                "qualities": [
                    "4K (2160p) - H.265 (HEVC)", "1080p (FHD) - H.265 (HEVC)",
                    "1080p (FHD) - H.264 (الافتراضي)", "720p (HD) - H.264 (AVC)",
                    "480p (SD) - H.264 (AVC)", "360p (Low) - H.264 (AVC)"
                ],
                "post_action": "⚡ بعد الانتهاء من العمل:",
                "action_none": "لا تفعل شيئاً", "action_shutdown": "إيقاف تشغيل الكمبيوتر", "action_sleep": "وضع السكون",
                "author": "تطوير: المهندس فارس كليب © 2026\n📞 772626216 - 738689628",
                "btn_save": "💾 تحديد مجلد الحفظ",
                "btn_add": "📂 إضافة فيديوهات",
                "btn_merge": "🔗 دمج الفيديوهات",
                "mode": "اختر وضع المعالجة:",
                "mode_balance": "وضع التوازن (محاضرة عادية)", "mode_board": "وضع السبورة (حجم صغير ونصوص)", "mode_audio": "استخراج الصوت فقط (MP3)",
                "rotation_none": "بدون تدوير", "rotation_90_r": "90 درجة يمين", "rotation_90_l": "90 درجة يسار", "rotation_180": "180 درجة",
                "btn_start": "🚀 بدء الضغط والمعالجة",
                "btn_pause": "⏸ إيقاف مؤقت",
                "btn_resume": "▶ استئناف",
                "btn_cancel": "⏹ إلغاء",
                "log_empty": "لم يتم اختيار أي فيديوهات بعد...\n(يمكنك سحب وإفلات الفيديوهات هنا)",
                "tooltip_hw": {"ar": "استخدم كرت الشاشة لتسريع الضغط جداً", "en": "Use GPU for massive speed boost"},
                "tooltip_quality": {"ar": "اختر الدقة. ترميز H.265 يضغط الفيديو بحجم أصغر بكثير بنفس الجودة.", "en": "Select resolution. H.265 provides much smaller size."}
            },
            "en": {
                "title": "Pro Video Compressor",
                "settings": "⚙️ Advanced Settings",
                "language": "🌐 Language (لغة الواجهة):",
                "theme": "🎨 Application Theme:",
                "theme_dark": "Dark", "theme_light": "Light",
                "hardware": "🖥️ Hardware Accelerator:",
                "quality": "🎚️ Video Quality & Codec:",
                "qualities": [
                    "4K (2160p) - H.265 (HEVC)", "1080p (FHD) - H.265 (HEVC)",
                    "1080p (FHD) - H.264 (Default)", "720p (HD) - H.264 (AVC)",
                    "480p (SD) - H.264 (AVC)", "360p (Low) - H.264 (AVC)"
                ],
                "post_action": "⚡ After Completion:",
                "action_none": "Do Nothing", "action_shutdown": "Shutdown PC", "action_sleep": "Sleep Mode",
                "author": "Developed by: Eng. Fares Kuliab © 2026\n📞 772626216 - 738689628",
                "btn_save": "💾 Set Save Folder",
                "btn_add": "📂 Add Videos",
                "btn_merge": "🔗 Merge Videos",
                "mode": "Select Processing Mode:",
                "mode_balance": "Balanced (Standard)", "mode_board": "Board (Small Size, Clear Text)", "mode_audio": "Extract Audio Only (MP3)",
                "rotation_none": "No Rotation", "rotation_90_r": "90° Right", "rotation_90_l": "90° Left", "rotation_180": "180°",
                "btn_start": "🚀 Start Processing",
                "btn_pause": "⏸ Pause",
                "btn_resume": "▶ Resume",
                "btn_cancel": "⏹ Cancel",
                "log_empty": "No videos selected yet...\n(Drag & Drop videos here)"
            }
        }

        self.build_ui()
        self.update_texts()

    def build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # الشريط الجانبي
        self.sidebar_frame = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self.lbl_settings = ctk.CTkLabel(self.sidebar_frame, font=("Arial", 20, "bold"))
        self.lbl_settings.pack(pady=(20, 20))

        self.lbl_lang = ctk.CTkLabel(self.sidebar_frame, font=("Arial", 14))
        self.lbl_lang.pack(anchor="w", padx=20, pady=(5, 0))
        self.menu_lang = ctk.CTkOptionMenu(self.sidebar_frame, values=["العربية", "English"], command=self.change_language)
        self.menu_lang.pack(fill="x", padx=20, pady=5)
        self.menu_lang.set("العربية")

        self.lbl_theme = ctk.CTkLabel(self.sidebar_frame, font=("Arial", 14))
        self.lbl_theme.pack(anchor="w", padx=20, pady=(15, 0))
        self.menu_theme = ctk.CTkOptionMenu(self.sidebar_frame, command=self.change_theme)
        self.menu_theme.pack(fill="x", padx=20, pady=5)

        self.lbl_hw = ctk.CTkLabel(self.sidebar_frame, font=("Arial", 14))
        self.lbl_hw.pack(anchor="w", padx=20, pady=(15, 0))
        self.menu_hw = ctk.CTkOptionMenu(self.sidebar_frame, values=["CPU (Standard)", "NVIDIA (NVENC)", "AMD (AMF)"])
        self.menu_hw.pack(fill="x", padx=20, pady=5)
        ToolTip(self.menu_hw, self.i18n["ar"]["tooltip_hw"], self.lang_var)

        self.lbl_quality = ctk.CTkLabel(self.sidebar_frame, font=("Arial", 14))
        self.lbl_quality.pack(anchor="w", padx=20, pady=(15, 0))
        self.menu_quality = ctk.CTkOptionMenu(self.sidebar_frame, command=self.update_estimation)
        self.menu_quality.pack(fill="x", padx=20, pady=5)
        ToolTip(self.menu_quality, self.i18n["ar"]["tooltip_quality"], self.lang_var)

        self.lbl_post_action = ctk.CTkLabel(self.sidebar_frame, font=("Arial", 14))
        self.lbl_post_action.pack(anchor="w", padx=20, pady=(15, 0))
        self.menu_post_action = ctk.CTkOptionMenu(self.sidebar_frame)
        self.menu_post_action.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(self.sidebar_frame, text="").pack(expand=True)

        self.lbl_author = ctk.CTkLabel(self.sidebar_frame, font=("Arial", 13, "bold"), text_color="#1f538d", justify="center")
        self.lbl_author.pack(pady=(0, 20))

        # الواجهة الرئيسية
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)

        self.lbl_title = ctk.CTkLabel(self.main_frame, font=("Arial", 28, "bold"))
        self.lbl_title.pack(pady=(0, 15))

        self.top_buttons_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_buttons_frame.pack(pady=5)

        self.btn_save = ctk.CTkButton(self.top_buttons_frame, font=("Arial", 15), fg_color="#b8860b", hover_color="#8b6508", command=self.select_output_dir)
        self.btn_save.grid(row=0, column=0, padx=10)

        self.btn_add = ctk.CTkButton(self.top_buttons_frame, font=("Arial", 15), command=self.select_videos)
        self.btn_add.grid(row=0, column=1, padx=10)
        
        self.btn_merge = ctk.CTkButton(self.top_buttons_frame, font=("Arial", 15), fg_color="#4b0082", hover_color="#300052", command=self.open_merge_window)
        self.btn_merge.grid(row=0, column=2, padx=10)

        self.extra_settings_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.extra_settings_frame.pack(pady=5)
        
        self.format_menu = ctk.CTkOptionMenu(self.extra_settings_frame, values=[".mp4", ".mkv"], font=("Arial", 14), width=80)
        self.format_menu.grid(row=0, column=0, padx=10)
        
        self.name_entry = ctk.CTkEntry(self.extra_settings_frame, font=("Arial", 14), width=250, justify="right")
        self.name_entry.grid(row=0, column=1, padx=10)

        self.menu_rotation = ctk.CTkOptionMenu(self.extra_settings_frame, font=("Arial", 14), width=150)
        self.menu_rotation.grid(row=0, column=2, padx=10)

        self.lbl_save_dir = ctk.CTkLabel(self.main_frame, text="", font=("Arial", 14), text_color="#aaaaaa")
        self.lbl_save_dir.pack(pady=(5, 0))

        self.file_list_frame = ctk.CTkScrollableFrame(self.main_frame, height=200)
        self.file_list_frame.pack(fill="both", pady=5)
        self.file_list_frame.drop_target_register(DND_FILES)
        self.file_list_frame.dnd_bind('<<Drop>>', self.handle_drop)

        self.stats_frame = ctk.CTkFrame(self.main_frame, fg_color="#1a2b3c", corner_radius=8)
        self.stats_frame.pack(fill="x", pady=5)
        self.lbl_stats = ctk.CTkLabel(self.stats_frame, text="", font=("Arial", 14, "bold"), text_color="#f39c12")
        self.lbl_stats.pack(pady=5)

        self.lbl_mode = ctk.CTkLabel(self.main_frame, font=("Arial", 15, "bold"))
        self.lbl_mode.pack(pady=(10, 5))
        self.menu_mode = ctk.CTkOptionMenu(self.main_frame, font=("Arial", 14), width=350, command=self.update_estimation)
        self.menu_mode.pack(pady=5)

        self.btn_start = ctk.CTkButton(self.main_frame, font=("Arial", 18, "bold"), fg_color="green", hover_color="darkgreen", height=40, command=self.start_compression, state="disabled")
        self.btn_start.pack(pady=10)

        self.progress_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.lbl_progress = ctk.CTkLabel(self.progress_frame, font=("Arial", 14, "bold"), text="")
        self.lbl_progress.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=500, fg_color="#333", progress_color="green")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=5)

        self.controls_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.controls_frame.pack(pady=10)
        
        self.btn_pause = ctk.CTkButton(self.controls_frame, font=("Arial", 14), fg_color="#b8860b", hover_color="#8b6508", width=120, command=self.toggle_pause)
        self.btn_pause.grid(row=0, column=0, padx=10)
        
        self.btn_cancel = ctk.CTkButton(self.controls_frame, font=("Arial", 14), fg_color="#8b0000", hover_color="#600000", width=120, command=self.cancel_compression)
        self.btn_cancel.grid(row=0, column=1, padx=10)

    def change_language(self, choice):
        self.lang_var.set("en" if choice == "English" else "ar")
        self.update_texts()
        self.update_estimation()

    def update_texts(self):
        l = self.lang_var.get()
        d = self.i18n[l]
        
        self.lbl_settings.configure(text=d["settings"])
        self.lbl_lang.configure(text=d["language"])
        self.lbl_theme.configure(text=d["theme"])
        self.lbl_hw.configure(text=d["hardware"])
        self.lbl_quality.configure(text=d["quality"])
        self.lbl_post_action.configure(text=d["post_action"])
        
        theme_vals = [d["theme_dark"], d["theme_light"]]
        self.menu_theme.configure(values=theme_vals)
        self.menu_theme.set(theme_vals[0] if ctk.get_appearance_mode() == "Dark" else theme_vals[1])

        post_vals = [d["action_none"], d["action_shutdown"], d["action_sleep"]]
        self.menu_post_action.configure(values=post_vals)
        self.menu_post_action.set(post_vals[0])

        mode_vals = [d["mode_balance"], d["mode_board"], d["mode_audio"]]
        self.menu_mode.configure(values=mode_vals)
        self.menu_mode.set(mode_vals[0])

        rot_vals = [d["rotation_none"], d["rotation_90_r"], d["rotation_90_l"], d["rotation_180"]]
        self.menu_rotation.configure(values=rot_vals)
        self.menu_rotation.set(rot_vals[0])

        if l == "ar":
            self.name_entry.configure(placeholder_text="تسمية جديدة للملف (اختياري)", justify="right")
        else:
            self.name_entry.configure(placeholder_text="New filename (optional)", justify="left")
            
        self.current_qualities = d["qualities"]
        self.menu_quality.configure(values=self.current_qualities)
        if not self.menu_quality.get() or self.menu_quality.get() not in self.current_qualities:
            self.menu_quality.set(self.current_qualities[2]) 
            
        self.lbl_author.configure(text=d["author"])
        self.lbl_title.configure(text=d["title"])
        self.btn_save.configure(text=d["btn_save"])
        self.btn_add.configure(text=d["btn_add"])
        self.btn_merge.configure(text=d["btn_merge"])
        self.lbl_mode.configure(text=d["mode"])
        self.btn_start.configure(text=d["btn_start"])
        self.btn_pause.configure(text=d["btn_pause"])
        self.btn_cancel.configure(text=d["btn_cancel"])
        
        self.update_log()

    def change_theme(self, choice):
        if choice in [self.i18n["ar"]["theme_dark"], self.i18n["en"]["theme_dark"]]:
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

    def parse_time(self, time_str):
        try:
            parts = time_str.strip().split(':')
            if len(parts) == 3: return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
            if len(parts) == 2: return int(parts[0])*60 + float(parts[1])
            return float(parts[0])
        except: return 0.0

    def get_duration(self, file_path):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            cmd = [FFPROBE_PATH, "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, creationflags=creationflags)
            return float(res.stdout.strip())
        except: return 0.0

    def init_file_settings(self, file_path):
        return {
            "start": "", "end": "", 
            "cut_m_start": "", "cut_m_end": "",
            "text": "", "text_pos": "أسفل المنتصف", "watermark": "",
            "crop_t": "0", "crop_b": "0", "crop_l": "0", "crop_r": "0"
        }

    def handle_drop(self, event):
        files = self.tk.splitlist(event.data)
        valid = ('.mp4', '.mkv', '.avi', '.mov')
        for f in [f for f in files if f.lower().endswith(valid)]:
            if f not in self.selected_files:
                self.selected_files.append(f)
                self.file_durations[f] = self.get_duration(f)
                self.file_settings[f] = self.init_file_settings(f)
        self.update_log()
        self.update_estimation()

    def select_output_dir(self):
        title = "اختر المجلد" if self.lang_var.get() == "ar" else "Select Directory"
        dir_path = filedialog.askdirectory(title=title)
        if dir_path:
            self.output_directory = dir_path
            self.update_log()

    def select_videos(self):
        title = "اختر الفيديوهات" if self.lang_var.get() == "ar" else "Select Videos"
        files = filedialog.askopenfilenames(title=title, filetypes=[("Video", "*.mp4 *.mkv *.avi *.mov")])
        for f in files:
            if f not in self.selected_files:
                self.selected_files.append(f)
                self.file_durations[f] = self.get_duration(f)
                self.file_settings[f] = self.init_file_settings(f)
        self.update_log()
        self.update_estimation()

    def remove_file(self, file_path):
        if file_path in self.selected_files:
            self.selected_files.remove(file_path)
            self.file_settings.pop(file_path, None)
            self.update_log()
            self.update_estimation()

    def update_log(self):
        l = self.lang_var.get()
        dir_text = f"📁 مجلد الحفظ: {self.output_directory if self.output_directory else 'نفس مجلد المصدر'}" if l=="ar" else f"📁 Save Dir: {self.output_directory if self.output_directory else 'Same as original'}"
        self.lbl_save_dir.configure(text=dir_text)
        
        for widget in self.file_list_frame.winfo_children(): widget.destroy()

        if not self.selected_files:
            empty = self.i18n[l]["log_empty"]
            lbl = ctk.CTkLabel(self.file_list_frame, text=empty, font=("Arial", 15))
            lbl.pack(pady=40)
            self.btn_start.configure(state="disabled")
            self.btn_merge.configure(state="disabled")
            return
            
        self.btn_start.configure(state="normal")
        self.btn_merge.configure(state="normal")
        for idx, f in enumerate(self.selected_files):
            frame = ctk.CTkFrame(self.file_list_frame, fg_color="#2b2b2b", corner_radius=5)
            frame.pack(fill="x", pady=2, padx=5)
            
            name = os.path.basename(f)
            lbl = ctk.CTkLabel(frame, text=f"{idx+1}. {name}", font=("Arial", 14), anchor="w")
            lbl.pack(side="left", padx=10, pady=5)
            
            btn_del = ctk.CTkButton(frame, text="❌", width=40, fg_color="#8b0000", hover_color="#600000", command=lambda p=f: self.remove_file(p))
            btn_del.pack(side="right", padx=5, pady=5)
            
            edit_txt = "✂️ تعديل" if l=="ar" else "✂️ Edit"
            btn_edit = ctk.CTkButton(frame, text=edit_txt, width=80, fg_color="#1f538d", command=lambda p=f: self.open_editor(p))
            btn_edit.pack(side="right", padx=5, pady=5)

    # -----------------------------------------------------
    # ميزات نافذة الدمج (Merge Logic)
    # -----------------------------------------------------
    def open_merge_window(self):
        if len(self.selected_files) < 2:
            return
            
        l = self.lang_var.get()
        self.merge_window = ctk.CTkToplevel(self)
        self.merge_window.title(self.i18n[l]["btn_merge"])
        self.merge_window.geometry("600x550")
        self.merge_window.attributes("-topmost", True)
        
        lbl_hint = ctk.CTkLabel(self.merge_window, text="حدد الفيديوهات ورتبها بالأسهم (▲ ▼) للدمج:", font=("Arial", 16, "bold"))
        lbl_hint.pack(pady=10)
        
        # قائمة العناصر مع المتغيرات (محددة افتراضياً)
        self.merge_items = [{"path": f, "var": ctk.BooleanVar(value=True)} for f in self.selected_files]
        
        self.merge_list_frame = ctk.CTkScrollableFrame(self.merge_window)
        self.merge_list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.render_merge_list()
        
        self.merge_name_entry = ctk.CTkEntry(self.merge_window, font=("Arial", 14), width=300, justify="center", placeholder_text="اكتب اسم الملف المدمج (بدون صيغة)" if l=="ar" else "Merged File Name")
        self.merge_name_entry.pack(pady=10)
        
        btn_start_merge = ctk.CTkButton(self.merge_window, text="🚀 بدء الدمج الآن" if l=="ar" else "🚀 Start Merge", font=("Arial", 16, "bold"), fg_color="#4b0082", hover_color="#300052", height=40, command=self.start_merge_process)
        btn_start_merge.pack(pady=10)

    def render_merge_list(self):
        for w in self.merge_list_frame.winfo_children(): w.destroy()
        
        for idx, item in enumerate(self.merge_items):
            frame = ctk.CTkFrame(self.merge_list_frame, fg_color="#2b2b2b", corner_radius=5)
            frame.pack(fill="x", pady=2, padx=5)
            
            chk = ctk.CTkCheckBox(frame, text=os.path.basename(item["path"]), variable=item["var"], font=("Arial", 14))
            chk.pack(side="left", padx=10, pady=5)
            
            btn_down = ctk.CTkButton(frame, text="▼", width=40, fg_color="#555", command=lambda i=idx: self.move_merge_item(i, 1))
            btn_down.pack(side="right", padx=2, pady=5)
            
            btn_up = ctk.CTkButton(frame, text="▲", width=40, fg_color="#555", command=lambda i=idx: self.move_merge_item(i, -1))
            btn_up.pack(side="right", padx=2, pady=5)

    def move_merge_item(self, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(self.merge_items):
            self.merge_items[idx], self.merge_items[new_idx] = self.merge_items[new_idx], self.merge_items[idx]
            self.render_merge_list()

    def start_merge_process(self):
        selected_to_merge = [item["path"] for item in self.merge_items if item["var"].get()]
        if len(selected_to_merge) < 2:
            return
            
        output_name = self.merge_name_entry.get().strip()
        if not output_name: output_name = "Merged_Video"
        
        ext = self.format_menu.get()
        save_dir = self.output_directory if self.output_directory else os.path.dirname(selected_to_merge[0])
        out_path = os.path.join(save_dir, f"{output_name}{ext}")
        list_file_path = os.path.join(save_dir, "concat_list.txt")
        
        try:
            with open(list_file_path, "w", encoding="utf-8") as f:
                for path in selected_to_merge:
                    safe_path = path.replace('\\', '/')
                    f.write(f"file '{safe_path}'\n")
        except Exception as e:
            return

        cmd = [FFMPEG_PATH, "-f", "concat", "-safe", "0", "-i", list_file_path, "-c", "copy", out_path, "-y"]
        
        self.merge_window.destroy()
        self.progress_frame.pack(pady=10)
        l = self.lang_var.get()
        self.lbl_progress.configure(text="جاري الدمج السريع (يُرجى الانتظار)..." if l=="ar" else "Merging fast...")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        self.btn_start.configure(state="disabled")
        self.btn_merge.configure(state="disabled")
        
        threading.Thread(target=self.run_merge_thread, args=(cmd, list_file_path)).start()

    def run_merge_thread(self, cmd, list_file_path):
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            self.current_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, creationflags=flags)
            self.current_process.wait()
            
            self.progress_bar.stop()
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(1.0)
            
            l = self.lang_var.get()
            self.lbl_progress.configure(text="✅ تمت عملية الدمج بنجاح!" if l=="ar" else "✅ Merge Completed!")
            try: winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
            except: pass
            
        except Exception as e:
            pass
        finally:
            if os.path.exists(list_file_path):
                os.remove(list_file_path)
            self.btn_start.configure(state="normal")
            self.btn_merge.configure(state="normal")
            self.after(3000, self.progress_frame.pack_forget)

    # -----------------------------------------------------
    # بقية الدوال القديمة (فتح المحرر، حساب التقدير، الضغط العادي)
    # -----------------------------------------------------
    def open_editor(self, file_path):
        l = self.lang_var.get()
        editor = ctk.CTkToplevel(self)
        title = "محرر الفيديو الشامل" if l == "ar" else "Video Editor"
        editor.title(title)
        editor.geometry("550x750")
        editor.attributes("-topmost", True)
        
        settings = self.file_settings.get(file_path, self.init_file_settings(file_path))
        scroll_frame = ctk.CTkScrollableFrame(editor, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

        txt_cut = "القص الزمني (اقتطاع الأطراف)" if l=="ar" else "Time Trim (Cut Edges)"
        ctk.CTkLabel(scroll_frame, text=txt_cut, font=("Arial", 16, "bold")).pack(pady=(10, 5))
        ctk.CTkButton(scroll_frame, text="▶️ تشغيل لمعرفة الوقت" if l=="ar" else "▶️ Play to check time", fg_color="green", command=lambda: os.startfile(file_path)).pack(pady=5)
        
        time_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        time_frame.pack(pady=5)
        txt_from = "من (HH:MM:SS):" if l=="ar" else "From (HH:MM:SS):"
        txt_to = "إلى (HH:MM:SS):" if l=="ar" else "To (HH:MM:SS):"
        
        col_lbl, col_ent = (2, 1) if l=="ar" else (1, 2)
        ctk.CTkLabel(time_frame, text=txt_from).grid(row=0, column=col_lbl, padx=5)
        ent_start = ctk.CTkEntry(time_frame, width=100, justify="center")
        ent_start.insert(0, settings["start"])
        ent_start.grid(row=0, column=col_ent, padx=5)
        
        ctk.CTkLabel(time_frame, text=txt_to).grid(row=1, column=col_lbl, padx=5, pady=10)
        ent_end = ctk.CTkEntry(time_frame, width=100, justify="center")
        ent_end.insert(0, settings["end"])
        ent_end.grid(row=1, column=col_ent, padx=5, pady=10)
        
        ctk.CTkLabel(scroll_frame, text="-"*50).pack()

        txt_mid = "حذف جزء من المنتصف (Cut Out)" if l=="ar" else "Cut Out Middle Section"
        ctk.CTkLabel(scroll_frame, text=txt_mid, font=("Arial", 16, "bold"), text_color="#ff5555").pack(pady=5)
        
        cut_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        cut_frame.pack(pady=5)
        txt_del_from = "احذف من:" if l=="ar" else "Delete From:"
        txt_del_to = "إلى:" if l=="ar" else "To:"
        
        ctk.CTkLabel(cut_frame, text=txt_del_from).grid(row=0, column=col_lbl, padx=5)
        ent_cut_start = ctk.CTkEntry(cut_frame, width=100, justify="center", placeholder_text="HH:MM:SS")
        ent_cut_start.insert(0, settings["cut_m_start"])
        ent_cut_start.grid(row=0, column=col_ent, padx=5)
        
        ctk.CTkLabel(cut_frame, text=txt_del_to).grid(row=1, column=col_lbl, padx=5, pady=5)
        ent_cut_end = ctk.CTkEntry(cut_frame, width=100, justify="center", placeholder_text="HH:MM:SS")
        ent_cut_end.insert(0, settings["cut_m_end"])
        ent_cut_end.grid(row=1, column=col_ent, padx=5, pady=5)
        
        ctk.CTkLabel(scroll_frame, text="-"*50).pack()

        txt_crop = "اقتطاع أبعاد الشاشة (Crop)" if l=="ar" else "Crop Video Frame"
        ctk.CTkLabel(scroll_frame, text=txt_crop, font=("Arial", 16, "bold")).pack(pady=5)
        crop_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        crop_frame.pack(pady=5)
        
        t_lbl, b_lbl = ("أعلى:", "أسفل:") if l=="ar" else ("Top:", "Bottom:")
        l_lbl, r_lbl = ("يسار:", "يمين:") if l=="ar" else ("Left:", "Right:")
        
        ctk.CTkLabel(crop_frame, text=t_lbl).grid(row=0, column=2, padx=5)
        ent_crop_t = ctk.CTkEntry(crop_frame, width=60, justify="center")
        ent_crop_t.insert(0, settings["crop_t"])
        ent_crop_t.grid(row=0, column=1, padx=5)
        
        ctk.CTkLabel(crop_frame, text=b_lbl).grid(row=1, column=2, padx=5, pady=5)
        ent_crop_b = ctk.CTkEntry(crop_frame, width=60, justify="center")
        ent_crop_b.insert(0, settings["crop_b"])
        ent_crop_b.grid(row=1, column=1, padx=5, pady=5)
        
        ctk.CTkLabel(crop_frame, text=l_lbl).grid(row=0, column=4, padx=5)
        ent_crop_l = ctk.CTkEntry(crop_frame, width=60, justify="center")
        ent_crop_l.insert(0, settings["crop_l"])
        ent_crop_l.grid(row=0, column=3, padx=5)
        
        ctk.CTkLabel(crop_frame, text=r_lbl).grid(row=1, column=4, padx=5)
        ent_crop_r = ctk.CTkEntry(crop_frame, width=60, justify="center")
        ent_crop_r.insert(0, settings["crop_r"])
        ent_crop_r.grid(row=1, column=3, padx=5)

        ctk.CTkLabel(scroll_frame, text="-"*50).pack()

        txt_addtext = "إضافة نص على الفيديو" if l=="ar" else "Add Text to Video"
        ctk.CTkLabel(scroll_frame, text=txt_addtext, font=("Arial", 16, "bold")).pack(pady=5)
        ent_text = ctk.CTkEntry(scroll_frame, width=300, justify="center", placeholder_text="اكتب النص هنا..." if l=="ar" else "Write text here...")
        ent_text.insert(0, settings["text"])
        ent_text.pack(pady=5)

        pos_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        pos_frame.pack(pady=5)
        txt_pos = "موقع النص:" if l=="ar" else "Text Position:"
        ctk.CTkLabel(pos_frame, text=txt_pos).grid(row=0, column=col_lbl, padx=10)
        
        if l == "ar":
            pos_vals = ["أسفل المنتصف", "أعلى المنتصف", "وسط الشاشة", "أعلى اليمين", "أعلى اليسار", "أسفل اليمين", "أسفل اليسار"]
            default_pos = "أسفل المنتصف"
        else:
            pos_vals = ["Bottom Center", "Top Center", "Center", "Top Right", "Top Left", "Bottom Right", "Bottom Left"]
            default_pos = "Bottom Center"
            
        menu_text_pos = ctk.CTkOptionMenu(pos_frame, values=pos_vals, width=150)
        saved_pos = settings.get("text_pos")
        menu_text_pos.set(saved_pos if saved_pos in pos_vals else default_pos)
        menu_text_pos.grid(row=0, column=col_ent, padx=10)

        ctk.CTkLabel(scroll_frame, text="-"*50).pack()

        txt_wm = "إضافة علامة مائية (صورة)" if l=="ar" else "Add Watermark (Image)"
        ctk.CTkLabel(scroll_frame, text=txt_wm, font=("Arial", 16, "bold")).pack(pady=5)
        
        no_img = "لم يتم اختيار صورة" if l=="ar" else "No image selected"
        lbl_wm = ctk.CTkLabel(scroll_frame, text=os.path.basename(settings["watermark"]) if settings["watermark"] else no_img, text_color="yellow")
        lbl_wm.pack()
        
        def choose_wm():
            p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg")])
            if p:
                lbl_wm.configure(text=os.path.basename(p))
                editor.wm_path = p
                
        editor.wm_path = settings["watermark"]
        btn_wm = "اختيار صورة شعار" if l=="ar" else "Choose Logo Image"
        ctk.CTkButton(scroll_frame, text=btn_wm, command=choose_wm).pack(pady=5)

        def save_edits():
            self.file_settings[file_path] = {
                "start": ent_start.get().strip(),
                "end": ent_end.get().strip(),
                "cut_m_start": ent_cut_start.get().strip(),
                "cut_m_end": ent_cut_end.get().strip(),
                "text": ent_text.get().strip(),
                "text_pos": menu_text_pos.get(),
                "watermark": getattr(editor, 'wm_path', ""),
                "crop_t": ent_crop_t.get().strip() or "0",
                "crop_b": ent_crop_b.get().strip() or "0",
                "crop_l": ent_crop_l.get().strip() or "0",
                "crop_r": ent_crop_r.get().strip() or "0",
            }
            editor.destroy()

        save_txt = "💾 حفظ التعديلات" if l=="ar" else "💾 Save Edits"
        ctk.CTkButton(editor, text=save_txt, fg_color="#b8860b", font=("Arial", 16, "bold"), height=40, command=save_edits).pack(pady=10)

    def update_estimation(self, _=None):
        if not self.selected_files:
            self.lbl_stats.configure(text="")
            return
        total_orig_bytes = sum(os.path.getsize(f) for f in self.selected_files)
        orig_mb = total_orig_bytes / (1024 * 1024)
        mode = self.menu_mode.get()
        l = self.lang_var.get()
        
        if mode in [self.i18n["ar"]["mode_balance"], self.i18n["en"]["mode_balance"]]: mode_key = "balance"
        elif mode in [self.i18n["ar"]["mode_board"], self.i18n["en"]["mode_board"]]: mode_key = "board"
        else: mode_key = "audio"
        
        try: quality_idx = self.current_qualities.index(self.menu_quality.get())
        except ValueError: quality_idx = 2
            
        base_ratios = [0.85, 0.40, 0.60, 0.35, 0.20, 0.10]
        ratio = base_ratios[quality_idx]
        if mode_key == "audio": ratio = 0.05
        elif mode_key == "board": ratio *= 0.45 
            
        est_mb = orig_mb * ratio
        min_mb = est_mb * 0.8
        max_mb = est_mb * 1.2
        saved_mb = max(0, orig_mb - max_mb)
        
        if l == "ar": text = f"📊 الحجم الأصلي: {orig_mb:.1f} MB | المتوقع: من {min_mb:.1f} إلى {max_mb:.1f} MB (توفير ~{saved_mb:.1f} MB)"
        else: text = f"📊 Original: {orig_mb:.1f} MB | Estimated: {min_mb:.1f} to {max_mb:.1f} MB (Saved ~{saved_mb:.1f} MB)"
        self.lbl_stats.configure(text=text)

    def toggle_pause(self):
        if not self.current_process: return
        l = self.lang_var.get()
        try:
            p = psutil.Process(self.current_process.pid)
            if self.is_paused:
                p.resume()
                self.is_paused = False
                self.btn_pause.configure(text=self.i18n[l]["btn_pause"], fg_color="#b8860b")
            else:
                p.suspend()
                self.is_paused = True
                self.btn_pause.configure(text=self.i18n[l]["btn_resume"], fg_color="green")
        except: pass

    def cancel_compression(self):
        self.is_cancelled = True
        if self.current_process:
            try: self.current_process.kill()
            except: pass

    def start_compression(self):
        self.progress_frame.pack(pady=10)
        self.btn_start.configure(state="disabled")
        self.btn_merge.configure(state="disabled")
        self.is_cancelled = False
        self.is_paused = False
        threading.Thread(target=self.process_videos).start()

    def process_videos(self):
        l = self.lang_var.get()
        mode_val = self.menu_mode.get()
        if mode_val in [self.i18n["ar"]["mode_balance"], self.i18n["en"]["mode_balance"]]: mode = "balance"
        elif mode_val in [self.i18n["ar"]["mode_board"], self.i18n["en"]["mode_board"]]: mode = "board"
        else: mode = "audio"
        
        hw_val = self.menu_hw.get()
        ext = self.format_menu.get()
        custom_name = self.name_entry.get().strip()
        rotation_val = self.menu_rotation.get()
        total_files = len(self.selected_files)
        
        try: quality_idx = self.current_qualities.index(self.menu_quality.get())
        except ValueError: quality_idx = 2
        
        if quality_idx == 0: vcodec, crf_value, scale = "libx265", 24, "3840:2160"
        elif quality_idx == 1: vcodec, crf_value, scale = "libx265", 26, "1920:1080"
        elif quality_idx == 2: vcodec, crf_value, scale = "libx264", 23, "1920:1080"
        elif quality_idx == 3: vcodec, crf_value, scale = "libx264", 26, "1280:720"
        elif quality_idx == 4: vcodec, crf_value, scale = "libx264", 28, "854:480"
        elif quality_idx == 5: vcodec, crf_value, scale = "libx264", 30, "640:360"

        for idx, file_path in enumerate(self.selected_files):
            if self.is_cancelled: break
            
            settings = self.file_settings.get(file_path, {})
            orig_dir, filename = os.path.split(file_path)
            name_no_ext, _ = os.path.splitext(filename)
            save_dir = self.output_directory if self.output_directory else orig_dir
            base = f"{custom_name}_{idx+1}" if custom_name and total_files > 1 else custom_name if custom_name else f"{name_no_ext}_Pro"
            
            cmd = [FFMPEG_PATH]

            if settings.get("start"): cmd.extend(["-ss", settings.get("start")])
            if settings.get("end"): cmd.extend(["-to", settings.get("end")])
            cmd.extend(["-i", file_path])
            
            if mode == "audio":
                out_path = os.path.join(save_dir, f"{base}.mp3")
                cmd.extend(["-q:a", "0"])
                audio_filters = []
                c_start, c_end = settings.get("cut_m_start"), settings.get("cut_m_end")
                if c_start and c_end:
                    t1, t2 = self.parse_time(c_start), self.parse_time(c_end)
                    if t2 > t1:
                        audio_filters.append(f"aselect='not(between(t\\,{t1}\\,{t2}))'")
                        audio_filters.append("asetpts=N/SR/TB")
                
                if audio_filters: cmd.extend(["-af", ",".join(audio_filters)])
                cmd.extend(["-map", "a", out_path, "-y"])
            else:
                out_path = os.path.join(save_dir, f"{base}{ext}")
                has_wm = bool(settings.get("watermark"))
                if has_wm: cmd.extend(["-i", settings["watermark"]])

                current_vcodec = vcodec
                if "NVIDIA" in hw_val: current_vcodec = "hevc_nvenc" if "265" in current_vcodec else "h264_nvenc"
                elif "AMD" in hw_val: current_vcodec = "hevc_amf" if "265" in current_vcodec else "h264_amf"

                cmd.extend(["-vcodec", current_vcodec])
                if "nvenc" in current_vcodec: cmd.extend(["-cq", str(crf_value)])
                elif "amf" in current_vcodec: cmd.extend(["-rc", "cqp", "-qp_p", str(crf_value)])
                else: cmd.extend(["-crf", str(crf_value)])

                preset = "fast" if mode == "board" else "medium"
                cmd.extend(["-preset", preset, "-acodec", "aac", "-b:a", "128k"])
                
                vf_filters = []
                audio_filters = []
                
                if rotation_val in [self.i18n["ar"]["rotation_90_r"], self.i18n["en"]["rotation_90_r"]]: vf_filters.append("transpose=1")
                elif rotation_val in [self.i18n["ar"]["rotation_90_l"], self.i18n["en"]["rotation_90_l"]]: vf_filters.append("transpose=2")
                elif rotation_val in [self.i18n["ar"]["rotation_180"], self.i18n["en"]["rotation_180"]]: vf_filters.append("transpose=2,transpose=2")

                c_start, c_end = settings.get("cut_m_start"), settings.get("cut_m_end")
                if c_start and c_end:
                    t1, t2 = self.parse_time(c_start), self.parse_time(c_end)
                    if t2 > t1:
                        vf_filters.append(f"select='not(between(t\\,{t1}\\,{t2}))'")
                        vf_filters.append("setpts=N/FRAME_RATE/TB")
                        audio_filters.append(f"aselect='not(between(t\\,{t1}\\,{t2}))'")
                        audio_filters.append("asetpts=N/SR/TB")
                
                c_t, c_b = settings.get("crop_t", "0"), settings.get("crop_b", "0")
                c_l, c_r = settings.get("crop_l", "0"), settings.get("crop_r", "0")
                try:
                    if int(c_t) > 0 or int(c_b) > 0 or int(c_l) > 0 or int(c_r) > 0:
                        vf_filters.append(f"crop=iw-{c_l}-{c_r}:ih-{c_t}-{c_b}:{c_l}:{c_t}")
                except: pass

                vf_filters.append(f"scale='min({scale.split(':')[0]},iw)':'min({scale.split(':')[1]},ih)'")
                
                if settings.get("text"):
                    txt = settings.get("text").replace("'", "").replace(":", "")
                    pos = settings.get("text_pos", "أسفل المنتصف")
                    
                    if pos in ["أعلى المنتصف", "Top Center"]: pos_str = "x=(w-text_w)/2:y=20"
                    elif pos in ["وسط الشاشة", "Center"]: pos_str = "x=(w-text_w)/2:y=(h-th)/2"
                    elif pos in ["أعلى اليمين", "Top Right"]: pos_str = "x=w-text_w-20:y=20"
                    elif pos in ["أعلى اليسار", "Top Left"]: pos_str = "x=20:y=20"
                    elif pos in ["أسفل اليمين", "Bottom Right"]: pos_str = "x=w-text_w-20:y=h-th-20"
                    elif pos in ["أسفل اليسار", "Bottom Left"]: pos_str = "x=20:y=h-th-20"
                    else: pos_str = "x=(w-text_w)/2:y=h-th-20"
                    
                    vf_filters.append(f"drawtext=text='{txt}':fontcolor=white:fontsize=40:{pos_str}")

                f_str = ",".join(vf_filters)
                if has_wm:
                    complex_filter = f"[0:v]{f_str}[v1];[v1][1:v]overlay=main_w-overlay_w-20:20[outv]"
                    cmd.extend(["-filter_complex", complex_filter, "-map", "[outv]", "-map", "0:a?"])
                else:
                    if f_str: cmd.extend(["-vf", f_str])
                    
                if audio_filters: cmd.extend(["-af", ",".join(audio_filters)])
                cmd.extend([out_path, "-y"])

            total_dur = self.file_durations.get(file_path, self.get_duration(file_path))
            self.progress_bar.configure(mode="determinate")
            self.progress_bar.set(0)
            
            try:
                flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                self.current_process = subprocess.Popen(cmd, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8', errors='ignore', creationflags=flags)
                for line in self.current_process.stderr:
                    if self.is_cancelled: break
                    match = re.search(r"time=(\d{2}:\d{2}:\d{2}\.\d{2})", line)
                    if match and total_dur > 0:
                        h, m, s = match.group(1).split(':')
                        current_sec = int(h)*3600 + int(m)*60 + float(s)
                        prog = min(current_sec / total_dur, 1.0)
                        self.progress_bar.set(prog)
                        
                        prog_text = f"Processing {idx+1}/{total_files} - {int(prog*100)}%" if l=="en" else f"جاري المعالجة {idx+1}/{total_files} - {int(prog*100)}%"
                        self.lbl_progress.configure(text=prog_text)
                
                self.current_process.wait()
                if self.is_cancelled and os.path.exists(out_path): os.remove(out_path)
            except Exception as e:
                pass
        
        self.progress_frame.pack_forget()
        self.btn_start.configure(state="normal")
        self.btn_merge.configure(state="normal")
        
        try: winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
        except: pass

        if not self.is_cancelled:
            self.execute_post_action()

    def execute_post_action(self):
        action = self.menu_post_action.get()
        if action in [self.i18n["ar"]["action_shutdown"], self.i18n["en"]["action_shutdown"]]:
            os.system("shutdown /s /t 10")
        elif action in [self.i18n["ar"]["action_sleep"], self.i18n["en"]["action_sleep"]]:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

if __name__ == "__main__":
    app = PremiumCompressorApp()
    app.mainloop()