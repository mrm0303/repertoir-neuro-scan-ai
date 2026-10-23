"""
Contact Sheet & Storyboard Generator for Video Clips
Extracts evenly-spaced keyframes from video files and compiles an elegant,
professional contact sheet with embedded timecodes, clip technical specifications,
camera metadata, and audio info.
"""
import os
import sys
import subprocess
import tempfile
import time
from datetime import timedelta
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageDraw, ImageFont, ImageTk

from catalogue_app.config import FFPROBE, FFPROBE_PATH, FFMPEG, FFMPEG_PATH
from catalogue_app.logger import log


def get_video_info(video_path):
    """Retrieves duration, resolution, fps, codecs and metadata via ffprobe."""
    ffprobe_cmd = FFPROBE_PATH if FFPROBE else "ffprobe"
    cmd = [
        ffprobe_cmd,
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-print_format", "json",
        video_path
    ]
    try:
        import json
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode != 0:
            return None
        data = json.loads(proc.stdout)
        fmt = data.get("format", {})
        streams = data.get("streams", [])
        
        vs = next((s for s in streams if s.get("codec_type") == "video"), None)
        as_ = next((s for s in streams if s.get("codec_type") == "audio"), None)

        dur_str = fmt.get("duration") or (vs.get("duration") if vs else "0")
        dur = float(dur_str) if dur_str else 0.0

        fps = 25.0
        if vs and "r_frame_rate" in vs:
            try:
                num, den = vs["r_frame_rate"].split('/')
                fps = float(num) / float(den)
            except:
                fps = 25.0

        tags = fmt.get("tags", {})
        creation_time = tags.get("creation_time", "")

        return {
            "duration": dur,
            "width": int(vs.get("width", 1920)) if vs else 1920,
            "height": int(vs.get("height", 1080)) if vs else 1080,
            "fps": fps,
            "video_codec": vs.get("codec_name", "inconnu") if vs else "aucun",
            "audio_codec": as_.get("codec_name", "aucun") if as_ else "aucun",
            "audio_channels": as_.get("channels", 0) if as_ else 0,
            "size": int(fmt.get("size", os.path.getsize(video_path))),
            "creation_time": creation_time,
        }
    except Exception as e:
        log.warning(f"ffprobe error for {video_path}: {e}")
        return None


def format_tc(seconds):
    """Format seconds into HH:MM:SS format."""
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def extract_keyframe(video_path, timestamp_sec, output_path, thumb_width=380):
    """Extracts a single frame from video at given timestamp using ffmpeg."""
    ffmpeg_cmd = FFMPEG_PATH if FFMPEG else "ffmpeg"
    cmd = [
        ffmpeg_cmd,
        "-ss", str(timestamp_sec),
        "-i", video_path,
        "-vframes", "1",
        "-vf", f"scale={thumb_width}:-1",
        "-q:v", "2",
        "-y",
        output_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=15)
        return res.returncode == 0 and os.path.exists(output_path)
    except Exception as e:
        log.warning(f"ffmpeg frame extraction error: {e}")
        return False


def generate_contact_sheet(video_path, output_path=None, grid=(4, 3), thumb_w=380,
                           extra_meta=None, progress_cb=None):
    """
    Generates a high-quality storyboard contact sheet image for a video.
    grid is (cols, rows). Default (4, 3) = 12 frames.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Fichier vidéo introuvable : {video_path}")

    info = get_video_info(video_path)
    if not info or info["duration"] <= 0:
        raise ValueError("Impossible d'extraire la durée et les flux vidéo.")

    cols, rows = grid
    total_frames = cols * rows
    dur = info["duration"]

    # Calculate spaced timestamps (from 5% to 95% of clip)
    start_offset = min(1.0, dur * 0.05)
    end_offset = max(dur - 1.0, dur * 0.95)
    step = (end_offset - start_offset) / max(1, total_frames - 1) if total_frames > 1 else 0
    timestamps = [start_offset + i * step for i in range(total_frames)]

    tmp_dir = tempfile.mkdtemp(prefix="cs_frames_")
    frame_files = []

    try:
        for idx, ts in enumerate(timestamps):
            f_path = os.path.join(tmp_dir, f"frame_{idx:02d}.jpg")
            ok = extract_keyframe(video_path, ts, f_path, thumb_width=thumb_w)
            if ok:
                frame_files.append((ts, f_path))
            else:
                log.warning(f"Échec extraction frame {idx} à {ts}s")
            
            if progress_cb:
                progress_cb(idx + 1, total_frames)

        if not frame_files:
            raise RuntimeError("Aucune vignette n'a pu être extraite.")

        # Determine thumbnail dimensions from first valid frame
        with Image.open(frame_files[0][1]) as first_img:
            actual_thumb_w, actual_thumb_h = first_img.size

        # Canvas Layout sizing
        padding = 16
        gap = 12
        header_h = 130
        footer_h = 40

        sheet_w = cols * actual_thumb_w + (cols + 1) * gap
        sheet_h = header_h + rows * actual_thumb_h + (rows + 1) * gap + footer_h

        # Base canvas (Cinematic dark theme)
        sheet = Image.new("RGB", (sheet_w, sheet_h), color="#11111b")
        draw = ImageDraw.Draw(sheet)

        # Fonts (fallback to default if system fonts not found)
        try:
            font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
            font_specs = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
            font_tc = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 12)
            font_footer = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 11)
        except:
            font_title = ImageFont.load_default()
            font_specs = ImageFont.load_default()
            font_tc = ImageFont.load_default()
            font_footer = ImageFont.load_default()

        # Draw Header
        fname = os.path.basename(video_path)
        draw.text((padding, 18), fname, fill="#89b4fa", font=font_title)

        sz_mb = info["size"] / (1024 * 1024)
        sz_str = f"{sz_mb / 1024:.2f} Go" if sz_mb >= 1024 else f"{sz_mb:.1f} Mo"
        dur_str = format_tc(info["duration"])

        meta_line1 = (f"Durée : {dur_str} ({info['duration']:.2f}s)   |   "
                      f"Définition : {info['width']}×{info['height']}   |   "
                      f"Cadence : {info['fps']:.2f} ips   |   "
                      f"Taille : {sz_str}")
        draw.text((padding, 56), meta_line1, fill="#cdd6f4", font=font_specs)

        cam_str = extra_meta.get("camera", "Inconnue") if extra_meta else "Inconnue"
        vol_str = extra_meta.get("volume_name", "") if extra_meta else ""
        vol_part = f"   |   Disque : {vol_str}" if vol_str else ""
        date_str = info.get("creation_time") or (extra_meta.get("date", "") if extra_meta else "")

        meta_line2 = (f"Codec : {info['video_codec'].upper()}   |   "
                      f"Audio : {info['audio_codec'].upper()} ({info['audio_channels']} ch)   |   "
                      f"Caméra : {cam_str}{vol_part}" +
                      (f"   |   Date : {date_str[:19]}" if date_str else ""))
        draw.text((padding, 80), meta_line2, fill="#a6adc8", font=font_specs)

        # Header separator line
        draw.line([(padding, header_h - 10), (sheet_w - padding, header_h - 10)], fill="#313244", width=1)

        # Draw Thumbnail Grid
        for i, (ts, img_path) in enumerate(frame_files):
            r = i // cols
            c = i % cols
            x = gap + c * (actual_thumb_w + gap)
            y = header_h + r * (actual_thumb_h + gap)

            with Image.open(img_path) as im:
                sheet.paste(im, (x, y))

            # Overlay Timecode Pill
            tc_str = format_tc(ts)
            pill_pad = 4
            pill_w = 70
            pill_h = 20
            px = x + actual_thumb_w - pill_w - 6
            py = y + actual_thumb_h - pill_h - 6

            # Semi-transparent dark background for timecode
            draw.rectangle([px, py, px + pill_w, py + pill_h], fill="#000000")
            draw.text((px + pill_pad + 2, py + 2), tc_str, fill="#f5e0dc", font=font_tc)

        # Draw Footer
        footer_text = f"Catalogue de Disques V6 — Planche Contact & Storyboard   •   Généré le {time.strftime('%d/%m/%Y à %H:%M')}"
        draw.text((padding, sheet_h - footer_h + 12), footer_text, fill="#585b70", font=font_footer)

        # Output save
        if not output_path:
            base, _ = os.path.splitext(video_path)
            output_path = f"{base}_PlancheContact.jpg"

        sheet.save(output_path, quality=92)
        log.info(f"Planche contact générée : {output_path}")
        return output_path

    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


class ContactSheetDialog(tk.Toplevel):
    """
    Dialog window offering customizable contact sheet generation,
    interactive preview, and instant export.
    """

    def __init__(self, master, video_path, metadata=None):
        super().__init__(master)
        self.video_path = video_path
        self.metadata = metadata or {}
        self.output_path = None
        self.preview_image = None

        self.title(f"Planche Contact : {os.path.basename(video_path)}")
        self.geometry("820x650")
        self.minsize(700, 500)
        self.transient(master)

        # Control panel top
        ctrl = ttk.LabelFrame(self, text=" Configuration de la Planche Contact ", padding=10)
        ctrl.pack(fill="x", padx=12, pady=10)

        ttk.Label(ctrl, text="Disposition de la Grille :").grid(row=0, column=0, sticky="w", pady=4)
        self.var_grid = tk.StringVar(value="4x3 (12 vignettes)")
        cmb_grid = ttk.Combobox(ctrl, textvariable=self.var_grid, state="readonly", width=20,
                                values=["3x3 (9 vignettes)", "4x3 (12 vignettes)", "4x4 (16 vignettes)", "5x4 (20 vignettes)"])
        cmb_grid.grid(row=0, column=1, sticky="w", padx=8, pady=4)

        ttk.Label(ctrl, text="Largeur vignettes :").grid(row=0, column=2, sticky="w", padx=(15, 0), pady=4)
        self.var_width = tk.StringVar(value="380 px (Haute Définition)")
        cmb_width = ttk.Combobox(ctrl, textvariable=self.var_width, state="readonly", width=22,
                                 values=["280 px (Standard)", "380 px (Haute Définition)", "480 px (Ultra-HD)"])
        cmb_width.grid(row=0, column=3, sticky="w", padx=8, pady=4)

        self.btn_gen = ttk.Button(ctrl, text="🎬 Générer la Planche Contact", command=self._start_generation)
        self.btn_gen.grid(row=0, column=4, sticky="e", padx=(15, 0), pady=4)

        # Progress bar
        self.prog_frame = ttk.Frame(ctrl)
        self.prog_frame.grid(row=1, column=0, columnspan=5, sticky="ew", pady=(8, 0))
        self.lbl_status = ttk.Label(self.prog_frame, text="Prêt à générer.")
        self.lbl_status.pack(side="left")
        self.pb = ttk.Progressbar(self.prog_frame, mode="determinate", length=300)
        self.pb.pack(side="right")

        # Preview area (Scrollable canvas)
        prev_frame = ttk.LabelFrame(self, text=" Aperçu ", padding=8)
        prev_frame.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        self.canvas = tk.Canvas(prev_frame, bg="#11111b", highlightthickness=0)
        vbar = ttk.Scrollbar(prev_frame, orient="vertical", command=self.canvas.yview)
        hbar = ttk.Scrollbar(prev_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        prev_frame.rowconfigure(0, weight=1)
        prev_frame.columnconfigure(0, weight=1)

        # Bottom Actions
        act = ttk.Frame(self, padding=(12, 0, 12, 12))
        act.pack(fill="x")

        self.btn_save_as = ttk.Button(act, text="💾 Enregistrer sous…", command=self._save_as, state="disabled")
        self.btn_save_as.pack(side="left", padx=(0, 8))

        self.btn_open = ttk.Button(act, text="👁️ Ouvrir dans Aperçu / Finder", command=self._open_in_finder, state="disabled")
        self.btn_open.pack(side="left", padx=8)

        ttk.Button(act, text="Fermer", command=self.destroy).pack(side="right")

        # Auto-start generation on dialog open
        self.after(200, self._start_generation)

    def _parse_grid(self):
        txt = self.var_grid.get().split()[0] # e.g. "4x3"
        c, r = txt.split('x')
        return int(c), int(r)

    def _parse_width(self):
        txt = self.var_width.get().split()[0]
        return int(txt)

    def _start_generation(self):
        self.btn_gen.config(state="disabled")
        self.btn_save_as.config(state="disabled")
        self.btn_open.config(state="disabled")
        self.lbl_status.config(text="Extraction des vignettes en cours...")
        self.pb["value"] = 0
        grid = self._parse_grid()
        thumb_w = self._parse_width()

        def worker():
            try:
                def prog(curr, tot):
                    pct = int(curr / tot * 100)
                    self.after(0, lambda: self.pb.configure(value=pct))
                    self.after(0, lambda: self.lbl_status.config(text=f"Extraction vignette {curr}/{tot} ({pct}%)"))

                out = generate_contact_sheet(
                    self.video_path,
                    grid=grid,
                    thumb_w=thumb_w,
                    extra_meta=self.metadata,
                    progress_cb=prog
                )
                self.output_path = out
                self.after(0, self._display_preview)
            except Exception as e:
                self.after(0, lambda err=e: messagebox.showerror("Erreur", f"Échec de la génération :\n{err}", parent=self))
            finally:
                self.after(0, lambda: self.btn_gen.config(state="normal"))

        import threading
        threading.Thread(target=worker, daemon=True).start()

    def _display_preview(self):
        if not self.output_path or not os.path.exists(self.output_path):
            return

        self.lbl_status.config(text=f"✅ Planche contact générée : {os.path.basename(self.output_path)}")
        self.btn_save_as.config(state="normal")
        self.btn_open.config(state="normal")

        # Load for display (scale down if canvas is smaller)
        img = Image.open(self.output_path)
        # Keep aspect ratio for preview display
        max_w = 780
        if img.width > max_w:
            scale = max_w / img.width
            disp_size = (int(img.width * scale), int(img.height * scale))
            disp_img = img.resize(disp_size, Image.Resampling.LANCZOS)
        else:
            disp_img = img

        self.preview_image = ImageTk.PhotoImage(disp_img)
        self.canvas.delete("all")
        self.canvas.create_image(10, 10, anchor="nw", image=self.preview_image)
        self.canvas.config(scrollregion=(0, 0, disp_img.width + 20, disp_img.height + 20))

    def _save_as(self):
        if not self.output_path or not os.path.exists(self.output_path):
            return
        dest = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer la Planche Contact",
            initialfile=os.path.basename(self.output_path),
            filetypes=[("Image JPEG", "*.jpg"), ("Image PNG", "*.png")]
        )
        if dest:
            import shutil
            shutil.copy2(self.output_path, dest)
            messagebox.showinfo("Export Réussi", f"Planche contact enregistrée dans :\n{dest}", parent=self)

    def _open_in_finder(self):
        if not self.output_path or not os.path.exists(self.output_path):
            return
        if sys.platform == "darwin":
            subprocess.Popen(["open", "-R", self.output_path])
        elif os.name == "nt":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(self.output_path)])
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(self.output_path)])
