import os
import re
import subprocess
import urllib.parse
import datetime
import numpy as np
from scipy import signal

VIDEO_EXTS = {".mov", ".mp4", ".mxf", ".braw", ".r3d", ".avi", ".mkv", ".crm"}
AUDIO_EXTS = {".wav", ".mp3", ".aac", ".aif", ".aiff", ".flac", ".m4a"}

_MEDIA_INFO_CACHE = {}


def get_media_info(file_path):
    """Récupère durée, fps, dimensions, canaux audio et timecode via ffprobe (avec cache)."""
    abs_p = os.path.abspath(file_path)
    if abs_p in _MEDIA_INFO_CACHE:
        return dict(_MEDIA_INFO_CACHE[abs_p])

    info = {
        "duration": 5.0,
        "fps": 25.0,
        "timecode": "",
        "width": 1920,
        "height": 1080,
        "has_audio": False,
        "channels": 2,
        "bits_per_sample": 16,
        "sample_rate": 48000
    }
    try:
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "stream=codec_type,width,height,r_frame_rate,duration,channels,bits_per_sample,sample_rate:format=duration:format_tags=timecode",
            "-of", "default=noprint_wrappers=1",
            file_path
        ]
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=10)
        for line in res.splitlines():
            line = line.strip()
            if not line:
                continue
            k, _, v = line.partition("=")
            if k == "codec_type" and v == "audio":
                info["has_audio"] = True
            elif k == "duration" and v and v != "N/A":
                try:
                    d_val = float(v)
                    if d_val > 0:
                        info["duration"] = d_val
                except Exception:
                    pass
            elif k == "r_frame_rate" and "/" in v:
                try:
                    num, den = v.split("/")
                    if float(den) > 0 and float(num) > 0:
                        fps_val = round(float(num) / float(den), 3)
                        if 1.0 <= fps_val <= 240.0:
                            info["fps"] = fps_val
                except Exception:
                    pass
            elif k == "width" and v and v != "N/A":
                try:
                    info["width"] = int(v)
                except Exception:
                    pass
            elif k == "height" and v and v != "N/A":
                try:
                    info["height"] = int(v)
                except Exception:
                    pass
            elif k == "channels" and v and v != "N/A":
                try:
                    ch = int(v)
                    if ch > 0:
                        info["channels"] = ch
                except Exception:
                    pass
            elif k == "bits_per_sample" and v and v != "N/A":
                try:
                    bps = int(v)
                    if bps in (16, 24, 32):
                        info["bits_per_sample"] = bps
                except Exception:
                    pass
            elif k == "sample_rate" and v and v != "N/A":
                try:
                    sr_val = int(v)
                    if sr_val > 0:
                        info["sample_rate"] = sr_val
                except Exception:
                    pass
            elif "timecode" in k.lower() and v:
                info["timecode"] = v
    except Exception:
        pass

    _MEDIA_INFO_CACHE[abs_p] = dict(info)
    return info


def extract_pcm(file_path, duration=120, sample_rate=8000):
    """
    Extrait un signal audio mono 8kHz 16-bit signé sous forme d'un tableau numpy.
    Mixe les canaux 1 et 2 (pan=mono|c0=0.5*c0+0.5*c1) pour supporter proprement
    les enregistreurs multipistes (Zoom F8 / Sound Devices 4-8 canaux).
    """
    cmd = [
        "ffmpeg", "-v", "error",
        "-ss", "0", "-t", str(duration),
        "-i", file_path,
        "-vn", "-af", "pan=mono|c0=0.5*c0+0.5*c1",
        "-ar", str(sample_rate),
        "-f", "s16le", "pipe:1"
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        raw, _ = proc.communicate(timeout=25)
        if not raw:
            return np.array([], dtype=np.float32)
        pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        max_val = np.max(np.abs(pcm)) if len(pcm) > 0 else 0
        if max_val > 0:
            pcm /= max_val
        return pcm
    except Exception:
        return np.array([], dtype=np.float32)


def _compute_envelope(sig, sr=8000):
    """
    Calcule l'enveloppe énergétique centrée (moyenne nulle) et normalisée (L2=1).
    La soustraction de la moyenne élimine totalement le biais triangulaire DC de fftconvolve.
    """
    if len(sig) < sr:
        return np.array([], dtype=np.float32)
    kernel_size = int(sr * 0.02)  # Fenêtre de lissage 20ms
    if kernel_size > 1:
        kernel = np.ones(kernel_size, dtype=np.float32) / kernel_size
        env = np.convolve(np.abs(sig), kernel, mode='same')
    else:
        env = np.abs(sig).astype(np.float32)

    env = env - np.mean(env)
    norm = float(np.linalg.norm(env))
    if norm > 1e-8:
        env = env / norm
    return env


def _correlate_envelopes(env_v, env_a, sr=8000):
    """
    Corrélation croisée FFT entre deux enveloppes centrées-normalisées.
    Retourne (offset_sec, confidence_pct, z_score).
    offset_sec > 0 signifie que l'audio externe a démarré avant la vidéo.
    """
    if len(env_v) < sr or len(env_a) < sr:
        return 0.0, 0, 0.0

    corr = signal.fftconvolve(env_a, env_v[::-1], mode='full')
    peak_idx = int(np.argmax(corr))
    peak_val = float(corr[peak_idx])

    offset_samples = peak_idx - len(env_v) + 1
    offset_sec = round(float(offset_samples) / sr, 3)

    mean_val = float(np.mean(corr))
    std_val = float(np.std(corr))
    z_score = (peak_val - mean_val) / (std_val + 1e-9) if std_val > 0 else 0.0

    if z_score >= 6.0:
        confidence = min(99, max(65, int(55 + (z_score - 6.0) * 4.5)))
    else:
        confidence = max(0, int((z_score / 6.0) * 55))

    return offset_sec, confidence, z_score


def sync_waveform(video_path, audio_path, max_dur=120, sr=8000):
    """Synchronisation par forme d'onde FFT."""
    sig_v = extract_pcm(video_path, duration=max_dur, sample_rate=sr)
    sig_a = extract_pcm(audio_path, duration=max_dur, sample_rate=sr)
    env_v = _compute_envelope(sig_v, sr=sr)
    env_a = _compute_envelope(sig_a, sr=sr)
    offset_sec, confidence, _ = _correlate_envelopes(env_v, env_a, sr=sr)
    return offset_sec, confidence


def sync_clap(video_path, audio_path, max_dur=30, sr=8000):
    """Détection de clap cinéma."""
    sig_v = extract_pcm(video_path, duration=max_dur, sample_rate=sr)
    sig_a = extract_pcm(audio_path, duration=max_dur, sample_rate=sr)

    if len(sig_v) < sr or len(sig_a) < sr:
        return 0.0, 0

    diff_v = np.diff(np.abs(sig_v))
    diff_a = np.diff(np.abs(sig_a))

    limit = min(20 * sr, len(diff_v), len(diff_a))
    clap_v = int(np.argmax(diff_v[:limit]))
    clap_a = int(np.argmax(diff_a[:limit]))

    t_v = clap_v / sr
    t_a = clap_a / sr
    offset_sec = round(t_a - t_v, 3)

    v_ratio = diff_v[clap_v] / (np.mean(np.abs(diff_v[:limit])) + 1e-6)
    a_ratio = diff_a[clap_a] / (np.mean(np.abs(diff_a[:limit])) + 1e-6)
    confidence = int(min(max((min(v_ratio, a_ratio) / 8.0) * 100, 0), 99))

    return offset_sec, confidence


def sync_timecode(video_path, audio_path):
    """Synchronisation par Timecode / BWF."""
    v_info = get_media_info(video_path)
    a_info = get_media_info(audio_path)

    tc_v = v_info.get("timecode")
    tc_a = a_info.get("timecode")

    def tc_to_sec(tc_str, fps=25.0):
        parts = re.split(r'[:;]', tc_str)
        if len(parts) == 4:
            h, m, s, f = [float(x) for x in parts]
            return h * 3600 + m * 60 + s + (f / fps)
        return None

    if tc_v and tc_a:
        sec_v = tc_to_sec(tc_v, v_info["fps"])
        sec_a = tc_to_sec(tc_a, v_info["fps"])
        if sec_v is not None and sec_a is not None:
            return round(sec_a - sec_v, 3), 100

    try:
        mtime_v = os.path.getmtime(video_path)
        mtime_a = os.path.getmtime(audio_path)
        return round(mtime_a - mtime_v, 3), 60
    except Exception:
        return 0.0, 0


def discover_camera_folders(video_dir):
    """Détecte les dossiers caméras frères si un sous-dossier comme Cam-A est sélectionné."""
    if not video_dir or not os.path.isdir(video_dir):
        return []
    abs_v = os.path.abspath(video_dir)
    base = os.path.basename(abs_v)
    parent = os.path.dirname(abs_v)

    target_dir = abs_v
    if base.upper() in ("CLIP", "CLIPS", "PRIVATE", "M4ROOT", "XDROOT", "BPAV", "CONTENTS", "VIDEO"):
        target_dir = parent
        base = os.path.basename(target_dir)
        parent = os.path.dirname(target_dir)

    cam_pattern = re.compile(r'^(cam(?:era)?[\s_\-]*[a-z0-9]+|[a-c][\s_\-]*cam)$', re.IGNORECASE)
    if cam_pattern.match(base) and os.path.isdir(parent):
        sibling_cams = []
        try:
            for entry in sorted(os.listdir(parent)):
                if entry.startswith('.'):
                    continue
                full_p = os.path.join(parent, entry)
                if os.path.isdir(full_p) and cam_pattern.match(entry):
                    sibling_cams.append(full_p)
        except OSError:
            pass
        if len(sibling_cams) > 1:
            return sibling_cams

    return [abs_v]


def scan_media_directory(folder_path, extensions, discover_siblings=False):
    """Scanne un dossier pour trouver les médias correspondants."""
    if not folder_path or not os.path.isdir(folder_path):
        return []

    folders = discover_camera_folders(folder_path) if discover_siblings else [os.path.abspath(folder_path)]
    seen_paths = set()
    items = []

    for f_dir in folders:
        for root, _, files in os.walk(f_dir):
            for f in sorted(files):
                if f.startswith('.'):
                    continue
                ext = os.path.splitext(f)[1].lower()
                if ext in extensions:
                    p = os.path.abspath(os.path.join(root, f))
                    if p in seen_paths:
                        continue
                    seen_paths.add(p)
                    try:
                        mtime = os.path.getmtime(p)
                        size = os.path.getsize(p)
                    except OSError:
                        mtime = 0
                        size = 0
                    items.append({
                        "name": f,
                        "path": p,
                        "ext": ext,
                        "mtime": mtime,
                        "size": size
                    })
    return items


def _extract_cam_label(file_path):
    """Extrait un identifiant de caméra ('Cam-A', 'Cam-B', etc.) depuis le nom ou le chemin."""
    m = re.search(r'(cam(?:era)?[\s_\-]*[a-z0-9]+)', file_path, re.IGNORECASE)
    if m:
        return m.group(1).upper().replace(" ", "-")
    return ""


def resolve_media_inputs(sources, valid_exts, default_label_prefix="Cam"):
    """
    Résout une liste de sources (dossiers OU fichiers individuels)
    en une liste uniforme d'éléments médias avec nom, chemin, taille, mtime et étiquette caméra/source.
    """
    if isinstance(sources, str):
        sources = [sources]
    elif not isinstance(sources, (list, tuple)):
        return []

    items = []
    seen_paths = set()
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    # Vérifier combien de sources non vides ont été fournies
    active_sources = [s for s in sources if s and (isinstance(s, dict) and s.get("path") or not isinstance(s, dict))]

    for idx_s, src in enumerate(sources):
        if not src:
            continue
        label = ""
        src_path = ""
        if isinstance(src, dict):
            src_path = src.get("path", "").strip()
            label = src.get("label", "").strip()
        else:
            src_path = str(src).strip()

        if not src_path:
            continue

        fallback_letter = letters[idx_s] if idx_s < len(letters) else str(idx_s + 1)
        fallback_label = f"{default_label_prefix}-{fallback_letter}"
        if not label:
            label = fallback_label

        abs_p = os.path.abspath(src_path)
        if os.path.isfile(abs_p):
            ext = os.path.splitext(abs_p)[1].lower()
            if ext in valid_exts and abs_p not in seen_paths:
                seen_paths.add(abs_p)
                try:
                    mtime = os.path.getmtime(abs_p)
                    size = os.path.getsize(abs_p)
                except OSError:
                    mtime = 0
                    size = 0
                items.append({
                    "name": os.path.basename(abs_p),
                    "path": abs_p,
                    "ext": ext,
                    "mtime": mtime,
                    "size": size,
                    "cam_label": label,
                    "source_index": idx_s + 1
                })
        elif os.path.isdir(abs_p):
            # Auto-détecter les caméras sœurs seulement si une seule source vidéo a été spécifiée
            discover = (len(active_sources) == 1 and default_label_prefix.lower() == "cam")
            scanned = scan_media_directory(abs_p, valid_exts, discover_siblings=discover)
            for sc in scanned:
                if sc["path"] not in seen_paths:
                    seen_paths.add(sc["path"])
                    cam_lbl = _extract_cam_label(sc["path"]) if discover else label
                    if not cam_lbl:
                        cam_lbl = label
                    items.append({
                        "name": sc["name"],
                        "path": sc["path"],
                        "ext": sc["ext"],
                        "mtime": sc["mtime"],
                        "size": sc["size"],
                        "cam_label": cam_lbl,
                        "source_index": idx_s + 1
                    })
    return items


def pair_and_sync(video_sources, audio_sources, method="waveform", progress_cb=None):
    """
    Associe automatiquement chaque vidéo à son audio externe correspondant (ou caméra maîtresse en Multi-Cam)
    et calcule le décalage de synchronisation exact à l'image près.
    - Accepte des dossiers OU des fichiers individuels (Caméra 1, Caméra 2, etc.)
    - Supporte les enregistreurs multipistes type Zoom F8 (4 à 8 canaux séparés)
    - Détecte automatiquement les prises et empile les caméras sur V1, V2, V3...
    """
    v_files = resolve_media_inputs(video_sources, VIDEO_EXTS, default_label_prefix="Cam")
    a_files = resolve_media_inputs(audio_sources, AUDIO_EXTS, default_label_prefix="Audio")

    video_only_multicam = False
    if not a_files and audio_sources:
        a_files = resolve_media_inputs(audio_sources, VIDEO_EXTS, default_label_prefix="CamRef")
        video_only_multicam = True
    elif not a_files and v_files:
        a_files = list(v_files)
        video_only_multicam = True

    if not v_files or not a_files:
        return []

    # Détection des prises multipistes mono Zoom F8 (fichiers _Tr1, _Tr2, _Tr3...)
    # On groupe les pistes supplémentaires sous la piste principale _Tr1
    mono_track_map = {}
    for a in a_files:
        m = re.search(r'^(.*?)_Tr(\d+)(\.[^.]+)$', a["name"], re.IGNORECASE)
        if m:
            base_take = m.group(1).lower()
            tr_num = int(m.group(2))
            if base_take not in mono_track_map:
                mono_track_map[base_take] = {}
            mono_track_map[base_take][tr_num] = a["path"]

    # Si des pistes _Tr1 existent avec des pistes compagnes _Tr2, _Tr3..., on annote l'élément principal
    for a in a_files:
        m = re.search(r'^(.*?)_Tr1(\.[^.]+)$', a["name"], re.IGNORECASE)
        if m:
            base_take = m.group(1).lower()
            if base_take in mono_track_map and len(mono_track_map[base_take]) > 1:
                tracks_dict = mono_track_map[base_take]
                sorted_trs = [tracks_dict[k] for k in sorted(tracks_dict.keys()) if k > 1]
                a["extra_mono_tracks"] = sorted_trs

    v_files = sorted(v_files, key=lambda x: (x.get("source_index", 1), x["name"], x["mtime"]))
    a_files = sorted(a_files, key=lambda x: (x["name"], x["mtime"]))

    sr = 8000
    max_dur = 120

    # 1. Pré-charger les métadonnées et enveloppes des fichiers Audio Maîtres (une seule fois par fichier)
    a_cache = {}
    for idx_a, a in enumerate(a_files):
        ap = a["path"]
        if progress_cb:
            progress_cb(0, len(v_files), f"Analyse Audio Master ({idx_a + 1}/{len(a_files)}) : {a['name']}")
        a_info = get_media_info(ap)
        a_env = np.array([], dtype=np.float32)
        if method in ("waveform", "auto"):
            a_sig = extract_pcm(ap, duration=max_dur, sample_rate=sr)
            a_env = _compute_envelope(a_sig, sr=sr)
        a_cache[ap] = {
            "item": a,
            "info": a_info,
            "env": a_env
        }

    # 2. Analyser chaque fichier Vidéo et trouver la meilleure correspondance Audio
    raw_matches = []
    total = len(v_files)

    for i, v in enumerate(v_files):
        vp = v["path"]
        if progress_cb:
            progress_cb(i, total, v["name"])

        v_info = get_media_info(vp)
        v_dur = v_info.get("duration", 5.0)

        # Ignorer les micro-coupures / faux départs caméra (< 4 secondes) s'il y a d'autres plans réels
        if v_dur < 4.0 and len(v_files) > 1:
            continue

        v_env = np.array([], dtype=np.float32)
        if method in ("waveform", "auto"):
            v_sig = extract_pcm(vp, duration=max_dur, sample_rate=sr)
            v_env = _compute_envelope(v_sig, sr=sr)

        best_a = a_files[0]
        best_offset = 0.0
        best_conf = 0
        best_score = -1e9

        for a in a_files:
            ap = a["path"]
            ac = a_cache[ap]
            a_info = ac["info"]
            a_dur = a_info.get("duration", 5.0)

            if os.path.abspath(vp) == os.path.abspath(ap):
                off, conf, z = 0.0, 100, 50.0
            elif method in ("waveform", "auto"):
                off, conf, z = _correlate_envelopes(v_env, ac["env"], sr=sr)
                if method == "auto" and conf < 55:
                    off_c, conf_c = sync_clap(vp, ap)
                    if conf_c > conf:
                        off, conf = off_c, conf_c
                        z = conf_c / 10.0
            elif method == "clap":
                off, conf = sync_clap(vp, ap)
                z = conf / 10.0
            elif method == "timecode":
                off, conf = sync_timecode(vp, ap)
                z = conf / 10.0
            else:
                off, conf, z = 0.0, 0, 0.0

            # Compatibilité de durée entre le rush caméra et la prise audio
            dur_ratio = min(v_dur, a_dur) / max(v_dur, a_dur, 0.1)
            if a_dur + 15.0 < v_dur * 0.7:
                score = z * 0.15
            else:
                score = z * (0.65 + 0.35 * dur_ratio)

            if score > best_score:
                best_score = score
                best_a = a
                best_offset = off
                best_conf = conf

        a_item = a_cache[best_a["path"]]["item"]
        a_info = a_cache[best_a["path"]]["info"]
        fps = v_info.get("fps", 25.0) or 25.0
        offset_frames = int(round(best_offset * fps))

        raw_matches.append({
            "video_name": v["name"],
            "video_path": vp,
            "cam_label": v.get("cam_label") or _extract_cam_label(vp) or "Cam-A",
            "source_index": v.get("source_index", 1),
            "audio_name": best_a["name"],
            "audio_path": best_a["path"],
            "extra_mono_tracks": a_item.get("extra_mono_tracks", []),
            "method": method.capitalize(),
            "offset_sec": best_offset,
            "offset_frames": offset_frames,
            "confidence": best_conf,
            "fps": fps,
            "duration": v_dur,
            "audio_duration": a_info.get("duration", v_dur),
            "audio_channels": a_info.get("channels", 2),
            "audio_bits": a_info.get("bits_per_sample", 16),
            "audio_sr": a_info.get("sample_rate", 48000),
            "has_cam_audio": v_info.get("has_audio", True),
            "cam_channels": v_info.get("channels", 2),
            "cam_bits": v_info.get("bits_per_sample", 16),
            "cam_sr": v_info.get("sample_rate", 48000),
            "width": v_info.get("width", 1920),
            "height": v_info.get("height", 1080),
        })

    # 3. Regrouper par prise Audio Master et ordonner les caméras
    groups_by_audio = {}
    audio_order = []
    for m in raw_matches:
        ak = os.path.abspath(m["audio_path"])
        if ak not in groups_by_audio:
            groups_by_audio[ak] = []
            audio_order.append(ak)
        groups_by_audio[ak].append(m)

    audio_order.sort(key=lambda ak: os.path.basename(ak).lower())

    results = []
    for ak in audio_order:
        cams = groups_by_audio[ak]
        # Ordonner par source_index puis par cam_label puis par nom
        cams.sort(key=lambda c: (c.get("source_index", 1), c.get("cam_label", ""), c["video_name"]))
        mc_count = len(cams)
        for idx_c, c in enumerate(cams):
            c["cam_track"] = idx_c + 1
            c["multicam_angles"] = mc_count
            results.append(c)

    if progress_cb:
        progress_cb(total, total, "Terminé")

    return results


def _rate_xml(fps, indent="            "):
    tb = int(round(fps)) if fps and fps > 0 else 25
    ntsc = "TRUE" if abs((fps or 25.0) - tb) > 0.01 else "FALSE"
    return (
        f"{indent}<rate>\n"
        f"{indent}  <timebase>{tb}</timebase>\n"
        f"{indent}  <ntsc>{ntsc}</ntsc>\n"
        f"{indent}</rate>"
    ), tb, ntsc


def _path_to_url(file_path):
    from xml.sax.saxutils import escape
    norm_p = os.path.abspath(file_path).replace("\\", "/")
    if not norm_p.startswith("/"):
        norm_p = "/" + norm_p
    return escape("file://localhost" + urllib.parse.quote(norm_p, safe="/:"))


def generate_synced_xml(sync_list, output_path, project_name="Synchronisation Rushes", multicam=True, split_audio_tracks=True):
    """
    Génère un fichier Final Cut Pro 7 XML (xmeml version 4) 100% compatible avec
    Adobe Premiere Pro 2026, DaVinci Resolve et Final Cut Pro.

    Architecture et Fonctionnalités Avancées :
    1. Multi-Caméras réelles : Caméra 1 (A) sur V1, Caméra 2 (B) sur V2, Caméra 3 (C) sur V3...
    2. Support Multipistes Zoom F8 / Sound Devices :
       - Si split_audio_tracks=True, chaque canal / micro du Zoom F8 est placé sur sa propre piste
         dédiée sur la timeline (A1 = Micro 1 / Perche, A2 = Micro 2 / HF1, A3 = Micro 3 / HF2...)
       - Tous les micros Zoom F8 sont liés (<link>) nativement à la vidéo principale V1 !
    3. Pistes témoins caméras mutées en fin de timeline pour référence.
    4. 100% compatible Premiere Pro 2026 sans dangling masterclipid.
    """
    from xml.sax.saxutils import escape

    if not sync_list:
        return False

    first_fps = sync_list[0].get("fps", 25.0) or 25.0
    seq_rate_xml, seq_tb, seq_ntsc = _rate_xml(first_fps, "      ")
    seq_w = sync_list[0].get("width") or 1920
    seq_h = sync_list[0].get("height") or 1080

    # Regrouper les éléments par prise Audio Master
    groups = []
    if multicam:
        group_map = {}
        for idx, item in enumerate(sync_list):
            a_key = os.path.abspath(item["audio_path"])
            if a_key not in group_map:
                grp = {
                    "audio_key": a_key,
                    "audio_path": item["audio_path"],
                    "audio_name": item["audio_name"],
                    "cams": []
                }
                group_map[a_key] = grp
                groups.append(grp)
            group_map[a_key]["cams"].append((idx, item))
    else:
        for idx, item in enumerate(sync_list):
            groups.append({
                "audio_key": os.path.abspath(item["audio_path"]),
                "audio_path": item["audio_path"],
                "audio_name": item["audio_name"],
                "cams": [(idx, item)]
            })

    # Déterminer le nombre maximum de canaux audio maître (Zoom F8)
    max_master_audio_channels = 1
    if split_audio_tracks:
        for item in sync_list:
            n_ch = int(item.get("audio_channels") or 2)
            extra_m = len(item.get("extra_mono_tracks", []))
            tot_ch = max(n_ch, 1 + extra_m)
            if tot_ch > max_master_audio_channels:
                max_master_audio_channels = tot_ch
    else:
        max_master_audio_channels = 1

    max_v_tracks = max(len(g["cams"]) for g in groups) if groups else 1
    video_tracks = [[] for _ in range(max_v_tracks)]

    # Pistes Audio Maître Zoom F8 (A1, A2, A3... jusqu'à max_master_audio_channels)
    audio_master_tracks = [[] for _ in range(max_master_audio_channels)]

    # Pistes Audio Témoins pour Caméras secondaires (V2, V3...)
    secondary_cam_audio_tracks = [[] for _ in range(max(0, max_v_tracks - 1))]
    # Piste Audio Témoin de V1 (Cam-A)
    v1_scratch_audio_track = []

    # Pré-calculer la durée et IDs constants des fichiers audio
    audio_file_ids = {}
    audio_file_durs = {}
    for item in sync_list:
        ak = os.path.abspath(item["audio_path"])
        tb_i = int(round(item.get("fps") or first_fps))
        a_dur_f = max(1, int(round((item.get("audio_duration") or item.get("duration") or 5.0) * tb_i)))
        v_dur_f = max(1, int(round((item.get("duration") or 5.0) * tb_i)))
        off_f = int(item.get("offset_frames", 0))
        needed_f = max(a_dur_f, off_f + v_dur_f, v_dur_f)
        if ak not in audio_file_ids:
            audio_file_ids[ak] = f"file-master-a-{len(audio_file_ids)}"
            audio_file_durs[ak] = needed_f
        else:
            audio_file_durs[ak] = max(audio_file_durs[ak], needed_f)

    defined_files = set()
    pos = 0
    gap_between_takes = int(seq_tb * 2)  # 2 secondes d'espace entre chaque prise

    for g_idx, grp in enumerate(groups):
        cams = grp["cams"]
        first_cam_item = cams[0][1]
        fps = first_cam_item.get("fps") or first_fps
        rate_xml, tb, ntsc = _rate_xml(fps, "                ")

        ak = grp["audio_key"]
        a_file_id = audio_file_ids[ak]
        a_file_dur = audio_file_durs[ak]

        cam_rel = []
        for global_idx, item in cams:
            v_dur = max(1, int(round((item.get("duration") or 5.0) * tb)))
            off_f = int(item.get("offset_frames", 0))
            cam_rel.append({
                "global_idx": global_idx,
                "item": item,
                "v_dur": v_dur,
                "off_f": off_f,
                "rel_start": off_f,
                "rel_end": off_f + v_dur
            })

        t_min = min(c["rel_start"] for c in cam_rel)
        t_max = max(c["rel_end"] for c in cam_rel)
        base_ref = min(0, t_min) if t_min < 0 else t_min

        # Nombre de canaux audio pour cette prise Zoom F8
        this_take_channels = max(1, int(first_cam_item.get("audio_channels") or 2))
        extra_mono = first_cam_item.get("extra_mono_tracks", [])
        if extra_mono:
            this_take_channels = max(this_take_channels, 1 + len(extra_mono))

        if not split_audio_tracks:
            this_take_channels = 1

        # Calculer les coordonnées de V1 et des pistes Master Audio associées
        c0 = cam_rel[0]
        v1_dur = c0["v_dur"]
        v1_off_f = c0["off_f"]
        v1_start = pos + (v1_off_f - base_ref)
        v1_end = v1_start + v1_dur
        v1_clip_id = f"clipitem-v1-{g_idx}"
        v1_clip_index = len(video_tracks[0]) + 1

        if v1_off_f >= 0:
            a_in = v1_off_f
            a_out = v1_off_f + v1_dur
            a_start = v1_start
            a_end = v1_end
        else:
            delay = -v1_off_f
            a_in = 0
            a_out = max(1, v1_dur - delay)
            a_start = v1_start + delay
            a_end = a_start + a_out

        # Liens entre V1 et toutes les pistes micros Zoom F8 (A1..A_n)
        v1_master_links = [
            {
                "ref": v1_clip_id,
                "mediatype": "video",
                "trackindex": 1,
                "clipindex": v1_clip_index
            }
        ]

        master_channel_clips = []
        for ch_idx in range(this_take_channels):
            ch_num = ch_idx + 1
            a_clip_id = f"clipitem-a-take{g_idx}-ch{ch_num}"
            a_clip_index = len(audio_master_tracks[ch_idx]) + 1
            v1_master_links.append({
                "ref": a_clip_id,
                "mediatype": "audio",
                "trackindex": ch_num,
                "clipindex": a_clip_index
            })

            # Si c'est du multi-mono Zoom F8
            ch_path = grp["audio_path"]
            ch_name = grp["audio_name"]
            ch_file_id = a_file_id
            if extra_mono and ch_idx > 0 and (ch_idx - 1) < len(extra_mono):
                ch_path = extra_mono[ch_idx - 1]
                ch_name = os.path.basename(ch_path)
                ch_file_id = f"file-mono-a-{g_idx}-ch{ch_num}"

            master_channel_clips.append({
                "ch_num": ch_num,
                "a_clip_id": a_clip_id,
                "audio_name": ch_name,
                "audio_path": ch_path,
                "a_file_id": ch_file_id,
                "a_file_dur": a_file_dur,
                "a_start": a_start,
                "a_end": a_end,
                "a_in": a_in,
                "a_out": a_out,
                "audio_channels": this_take_channels,
                "audio_bits": first_cam_item.get("audio_bits", 24),
                "audio_sr": first_cam_item.get("audio_sr", 48000),
                "rate_xml": rate_xml,
                "links": v1_master_links
            })

        # --- Placement de chaque caméra sur V1, V2, V3... ---
        for v_track_idx, c in enumerate(cam_rel):
            global_idx = c["global_idx"]
            item = c["item"]
            v_dur = c["v_dur"]
            off_f = c["off_f"]

            v_start = pos + (off_f - base_ref)
            v_end = v_start + v_dur
            v_clip_id = f"clipitem-v{v_track_idx + 1}-{g_idx}"
            v_clip_index = len(video_tracks[v_track_idx]) + 1

            if v_track_idx == 0:
                # Caméra 1 (V1)
                v_placement = {
                    "v_track_idx": 0,
                    "global_idx": global_idx,
                    "item": item,
                    "v_clip_id": v_clip_id,
                    "v_dur": v_dur,
                    "v_start": v_start,
                    "v_end": v_end,
                    "rate_xml": rate_xml,
                    "links": v1_master_links
                }
                video_tracks[0].append(v_placement)

                # Enregistrer chaque micro Zoom F8 dans sa piste A1, A2, A3...
                for ch_info in master_channel_clips:
                    audio_master_tracks[ch_info["ch_num"] - 1].append(ch_info)

                # Audio témoin de Caméra 1 en secours
                if item.get("has_cam_audio", True):
                    v1_scratch_audio_track.append({
                        "cp": v_placement,
                        "a_cam_clip_id": f"clipitem-acam1-{g_idx}",
                        "links": []
                    })
            else:
                # Caméras secondaires (V2, V3...) empilées au-dessus de V1
                sec_a_idx = v_track_idx - 1
                a_track_num = max_master_audio_channels + v_track_idx
                a_cam_clip_id = f"clipitem-acam{v_track_idx + 1}-{g_idx}"
                a_cam_clip_index = len(secondary_cam_audio_tracks[sec_a_idx]) + 1

                has_cam_a = item.get("has_cam_audio", True)
                vk_links = []
                if has_cam_a:
                    vk_links = [
                        {
                            "ref": v_clip_id,
                            "mediatype": "video",
                            "trackindex": v_track_idx + 1,
                            "clipindex": v_clip_index
                        },
                        {
                            "ref": a_cam_clip_id,
                            "mediatype": "audio",
                            "trackindex": a_track_num,
                            "clipindex": a_cam_clip_index
                        }
                    ]

                v_placement = {
                    "v_track_idx": v_track_idx,
                    "global_idx": global_idx,
                    "item": item,
                    "v_clip_id": v_clip_id,
                    "v_dur": v_dur,
                    "v_start": v_start,
                    "v_end": v_end,
                    "rate_xml": rate_xml,
                    "links": vk_links
                }
                video_tracks[v_track_idx].append(v_placement)

                if has_cam_a:
                    secondary_cam_audio_tracks[sec_a_idx].append({
                        "cp": v_placement,
                        "a_cam_clip_id": a_cam_clip_id,
                        "links": vk_links
                    })

        group_span = max(1, t_max - base_ref)
        pos += group_span + gap_between_takes

    tot_dur = max(1, pos)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE xmeml>',
        '<xmeml version="4">',
        '  <sequence id="sequence-sync-1">',
        f'    <name>{escape(project_name)} - Multi-Cam Sync</name>',
        f'    <duration>{tot_dur}</duration>',
        seq_rate_xml,
        '    <timecode>',
        seq_rate_xml.replace("      <", "        <"),
        '      <string>00:00:00:00</string>',
        '      <frame>0</frame>',
        f'      <displayformat>{"DF" if seq_ntsc == "TRUE" and seq_tb in (30, 60) else "NDF"}</displayformat>',
        '    </timecode>',
        '    <media>',
        '      <video>',
        '        <format>',
        '          <samplecharacteristics>',
        seq_rate_xml.replace("      <", "            <"),
        f'            <width>{seq_w}</width>',
        f'            <height>{seq_h}</height>',
        '            <anamorphic>FALSE</anamorphic>',
        '            <pixelaspectratio>square</pixelaspectratio>',
        '            <fielddominance>none</fielddominance>',
        '          </samplecharacteristics>',
        '        </format>'
    ]

    # --- Génération des Pistes Vidéo V1, V2, V3... ---
    for v_track_idx, track_clips in enumerate(video_tracks):
        lines.append('        <track>')
        for cp in track_clips:
            i = cp["global_idx"]
            item = cp["item"]
            v_name = escape(item["video_name"])
            v_url = _path_to_url(item["video_path"])
            w = item.get("width") or seq_w
            h = item.get("height") or seq_h
            has_cam_a = item.get("has_cam_audio", True)
            cam_bits = item.get("cam_bits", 16)
            cam_sr = item.get("cam_sr", 48000)
            file_id = f"file-v-{i}"

            lines.append(f'          <clipitem id="{cp["v_clip_id"]}">')
            lines.append(f'            <name>{v_name}</name>')
            lines.append('            <enabled>TRUE</enabled>')
            lines.append(f'            <duration>{cp["v_dur"]}</duration>')
            lines.append(cp["rate_xml"].replace("                <", "            <"))
            lines.append(f'            <start>{cp["v_start"]}</start>')
            lines.append(f'            <end>{cp["v_end"]}</end>')
            lines.append('            <in>0</in>')
            lines.append(f'            <out>{cp["v_dur"]}</out>')

            if file_id not in defined_files:
                defined_files.add(file_id)
                lines.append(f'            <file id="{file_id}">')
                lines.append(f'              <name>{v_name}</name>')
                lines.append(f'              <pathurl>{v_url}</pathurl>')
                lines.append(cp["rate_xml"].replace("                <", "              <"))
                lines.append(f'              <duration>{cp["v_dur"]}</duration>')
                lines.append('              <timecode>')
                lines.append(cp["rate_xml"])
                lines.append('                <string>00:00:00:00</string>')
                lines.append('                <frame>0</frame>')
                lines.append('                <displayformat>NDF</displayformat>')
                lines.append('              </timecode>')
                lines.append('              <media>')
                lines.append('                <video>')
                lines.append('                  <samplecharacteristics>')
                lines.append(cp["rate_xml"].replace("                <", "                    <"))
                lines.append(f'                    <width>{w}</width>')
                lines.append(f'                    <height>{h}</height>')
                lines.append('                  </samplecharacteristics>')
                lines.append('                </video>')
                if has_cam_a:
                    lines.append('                <audio>')
                    lines.append('                  <samplecharacteristics>')
                    lines.append(f'                    <depth>{cam_bits}</depth>')
                    lines.append(f'                    <samplerate>{cam_sr}</samplerate>')
                    lines.append('                  </samplecharacteristics>')
                    lines.append('                  <channelcount>2</channelcount>')
                    lines.append('                </audio>')
                lines.append('              </media>')
                lines.append('            </file>')
            else:
                lines.append(f'            <file id="{file_id}"/>')

            for lnk in cp["links"]:
                lines.append('            <link>')
                lines.append(f'              <linkclipref>{lnk["ref"]}</linkclipref>')
                lines.append(f'              <mediatype>{lnk["mediatype"]}</mediatype>')
                lines.append(f'              <trackindex>{lnk["trackindex"]}</trackindex>')
                lines.append(f'              <clipindex>{lnk["clipindex"]}</clipindex>')
                lines.append('            </link>')
            lines.append('          </clipitem>')
        lines.append('        </track>')

    lines.append('      </video>')

    # --- Génération des Pistes Audio ---
    lines.append('      <audio>')
    lines.append('        <numOutputChannels>2</numOutputChannels>')
    lines.append('        <format>')
    lines.append('          <samplecharacteristics>')
    lines.append('            <depth>24</depth>')
    lines.append('            <samplerate>48000</samplerate>')
    lines.append('          </samplecharacteristics>')
    lines.append('        </format>')

    # Pistes Audio A1..AK : Micros Séparés du Zoom F8 liés à V1
    for ch_idx, track_am in enumerate(audio_master_tracks):
        if not track_am:
            continue
        lines.append('        <track>')
        for am in track_am:
            ch_num = am["ch_num"]
            a_label = f"[Micro {ch_num}]" if max_master_audio_channels > 1 else ""
            a_name = escape(f"{am['audio_name']} {a_label}".strip())
            a_url = _path_to_url(am["audio_path"])
            file_id = am["a_file_id"]
            a_bits = am.get("audio_bits", 24)
            a_sr = am.get("audio_sr", 48000)
            a_channels = am.get("audio_channels", 2)

            lines.append(f'          <clipitem id="{am["a_clip_id"]}">')
            lines.append(f'            <name>{a_name}</name>')
            lines.append('            <enabled>TRUE</enabled>')
            lines.append(f'            <duration>{am["a_file_dur"]}</duration>')
            lines.append(am["rate_xml"].replace("                <", "            <"))
            lines.append(f'            <start>{am["a_start"]}</start>')
            lines.append(f'            <end>{am["a_end"]}</end>')
            lines.append(f'            <in>{am["a_in"]}</in>')
            lines.append(f'            <out>{am["a_out"]}</out>')

            if file_id not in defined_files:
                defined_files.add(file_id)
                lines.append(f'            <file id="{file_id}">')
                lines.append(f'              <name>{escape(am["audio_name"])}</name>')
                lines.append(f'              <pathurl>{a_url}</pathurl>')
                lines.append(am["rate_xml"].replace("                <", "              <"))
                lines.append(f'              <duration>{am["a_file_dur"]}</duration>')
                lines.append('              <timecode>')
                lines.append(am["rate_xml"])
                lines.append('                <string>00:00:00:00</string>')
                lines.append('                <frame>0</frame>')
                lines.append('                <displayformat>NDF</displayformat>')
                lines.append('              </timecode>')
                lines.append('              <media>')
                lines.append('                <audio>')
                lines.append('                  <samplecharacteristics>')
                lines.append(f'                    <depth>{a_bits}</depth>')
                lines.append(f'                    <samplerate>{a_sr}</samplerate>')
                lines.append('                  </samplecharacteristics>')
                lines.append(f'                  <channelcount>{a_channels}</channelcount>')
                lines.append('                </audio>')
                lines.append('              </media>')
                lines.append('            </file>')
            else:
                lines.append(f'            <file id="{file_id}"/>')

            lines.append('            <sourcetrack>')
            lines.append('              <mediatype>audio</mediatype>')
            lines.append(f'              <trackindex>{ch_num}</trackindex>')
            lines.append('            </sourcetrack>')
            for lnk in am["links"]:
                lines.append('            <link>')
                lines.append(f'              <linkclipref>{lnk["ref"]}</linkclipref>')
                lines.append(f'              <mediatype>{lnk["mediatype"]}</mediatype>')
                lines.append(f'              <trackindex>{lnk["trackindex"]}</trackindex>')
                lines.append(f'              <clipindex>{lnk["clipindex"]}</clipindex>')
                lines.append('            </link>')
            lines.append('          </clipitem>')
        lines.append('        </track>')

    # Pistes Audio Témoins pour Caméras secondaires (mutées, liées à V2, V3...)
    for sec_idx, cam_a_clips in enumerate(secondary_cam_audio_tracks):
        if not cam_a_clips:
            continue
        lines.append('        <track>')
        for cac in cam_a_clips:
            cp = cac["cp"]
            i = cp["global_idx"]
            item = cp["item"]
            v_name = escape(item["video_name"])
            lines.append(f'          <clipitem id="{cac["a_cam_clip_id"]}">')
            lines.append(f'            <name>{v_name} [Son Cam]</name>')
            lines.append('            <enabled>FALSE</enabled>')
            lines.append(f'            <duration>{cp["v_dur"]}</duration>')
            lines.append(cp["rate_xml"].replace("                <", "            <"))
            lines.append(f'            <start>{cp["v_start"]}</start>')
            lines.append(f'            <end>{cp["v_end"]}</end>')
            lines.append('            <in>0</in>')
            lines.append(f'            <out>{cp["v_dur"]}</out>')
            lines.append(f'            <file id="file-v-{i}"/>')
            lines.append('            <sourcetrack>')
            lines.append('              <mediatype>audio</mediatype>')
            lines.append('              <trackindex>1</trackindex>')
            lines.append('            </sourcetrack>')
            for lnk in cac["links"]:
                lines.append('            <link>')
                lines.append(f'              <linkclipref>{lnk["ref"]}</linkclipref>')
                lines.append(f'              <mediatype>{lnk["mediatype"]}</mediatype>')
                lines.append(f'              <trackindex>{lnk["trackindex"]}</trackindex>')
                lines.append(f'              <clipindex>{lnk["clipindex"]}</clipindex>')
                lines.append('            </link>')
            lines.append('          </clipitem>')
        lines.append('        </track>')

    # Piste Audio Témoin de V1 (Cam-A)
    if v1_scratch_audio_track:
        lines.append('        <track>')
        for cac in v1_scratch_audio_track:
            cp = cac["cp"]
            i = cp["global_idx"]
            item = cp["item"]
            v_name = escape(item["video_name"])
            lines.append(f'          <clipitem id="{cac["a_cam_clip_id"]}">')
            lines.append(f'            <name>{v_name} [Son Cam 1]</name>')
            lines.append('            <enabled>FALSE</enabled>')
            lines.append(f'            <duration>{cp["v_dur"]}</duration>')
            lines.append(cp["rate_xml"].replace("                <", "            <"))
            lines.append(f'            <start>{cp["v_start"]}</start>')
            lines.append(f'            <end>{cp["v_end"]}</end>')
            lines.append('            <in>0</in>')
            lines.append(f'            <out>{cp["v_dur"]}</out>')
            lines.append(f'            <file id="file-v-{i}"/>')
            lines.append('            <sourcetrack>')
            lines.append('              <mediatype>audio</mediatype>')
            lines.append('              <trackindex>1</trackindex>')
            lines.append('            </sourcetrack>')
            lines.append('          </clipitem>')
        lines.append('        </track>')

    lines.append('      </audio>')
    lines.append('    </media>')
    lines.append('  </sequence>')
    lines.append('</xmeml>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return True
