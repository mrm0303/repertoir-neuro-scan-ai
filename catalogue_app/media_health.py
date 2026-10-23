"""
Media Health & Integrity Checker
Inspects video and audio files for corruption, truncated headers, missing moov atoms,
damaged streams, or audio/video decode errors using ffprobe and ffmpeg.
"""
import os
import json
import subprocess
import concurrent.futures
from catalogue_app.config import FFPROBE, FFPROBE_PATH
from catalogue_app.logger import log

def check_media_file_health(file_path, deep_check=False, timeout_sec=15):
    """
    Checks the health and integrity of a single media file.
    
    Returns a dict:
    {
        "path": str,
        "name": str,
        "status": "healthy" | "warning" | "corrupt" | "unknown",
        "issues": [str],
        "details": {
            "format_name": str,
            "duration": float,
            "video_codec": str,
            "resolution": str,
            "audio_codec": str,
            "channels": int,
        }
    }
    """
    result = {
        "path": file_path,
        "name": os.path.basename(file_path),
        "status": "healthy",
        "issues": [],
        "details": {}
    }

    if not os.path.exists(file_path):
        result["status"] = "corrupt"
        result["issues"].append("Fichier introuvable sur le disque.")
        return result

    if os.path.getsize(file_path) == 0:
        result["status"] = "corrupt"
        result["issues"].append("Fichier vide (0 octet).")
        return result

    ffprobe_cmd = FFPROBE_PATH if FFPROBE else "ffprobe"

    # 1. Container & Stream Inspection via ffprobe
    cmd = [
        ffprobe_cmd,
        "-v", "error",
        "-show_format",
        "-show_streams",
        "-print_format", "json",
        file_path
    ]

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
        if proc.returncode != 0:
            result["status"] = "corrupt"
            err_msg = proc.stderr.strip() or "Erreur inconnue ffprobe"
            result["issues"].append(f"Conteneur illisible / Corrompu: {err_msg}")
            return result

        data = json.loads(proc.stdout) if proc.stdout else {}
        fmt = data.get("format", {})
        streams = data.get("streams", [])

        if not streams:
            result["status"] = "corrupt"
            result["issues"].append("Aucun flux vidéo ou audio détecté dans le fichier.")
            return result

        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

        dur_str = fmt.get("duration")
        duration = float(dur_str) if dur_str else 0.0

        result["details"] = {
            "format_name": fmt.get("format_name", "inconnu"),
            "duration": duration,
            "size": int(fmt.get("size", 0) or os.path.getsize(file_path)),
            "video_codec": video_stream.get("codec_name") if video_stream else None,
            "resolution": f"{video_stream.get('width')}x{video_stream.get('height')}" if video_stream and video_stream.get('width') else None,
            "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
            "channels": audio_stream.get("channels") if audio_stream else None,
        }

        # Check for duration issues
        if duration <= 0:
            result["status"] = "warning"
            result["issues"].append("Durée indéterminée ou nulle (possible en-tête partiel/non finalisé).")

        # Check video stream validity
        if video_stream:
            if not video_stream.get("width") or not video_stream.get("height"):
                result["status"] = "corrupt"
                result["issues"].append("Flux vidéo sans dimensions valides.")

        # 2. Deep Decode Verification (Optional or if deep_check is True)
        if deep_check:
            ffmpeg_cmd = "ffmpeg"
            # Test decoding first 5 seconds or full file
            test_cmd = [
                ffmpeg_cmd,
                "-v", "error",
                "-xerror",
                "-i", file_path,
                "-t", "5",
                "-f", "null",
                "-"
            ]
            dec_proc = subprocess.run(test_cmd, capture_output=True, text=True, timeout=timeout_sec)
            if dec_proc.returncode != 0:
                result["status"] = "corrupt"
                dec_err = dec_proc.stderr.strip() or "Erreur de décodage des paquets"
                result["issues"].append(f"Erreur de décodage: {dec_err}")

    except subprocess.TimeoutExpired:
        result["status"] = "warning"
        result["issues"].append("Délai d'analyse dépassé (timeout) - possible blocage d'I/O.")
    except Exception as e:
        result["status"] = "unknown"
        result["issues"].append(f"Erreur d'analyse: {str(e)}")

    return result


def batch_check_media_health(file_paths, deep_check=False, max_workers=4, progress_cb=None):
    """
    Checks multiple files concurrently.
    Returns list of health report dicts.
    """
    results = []
    total = len(file_paths)
    if total == 0:
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_path = {executor.submit(check_media_file_health, p, deep_check): p for p in file_paths}
        
        for idx, future in enumerate(concurrent.futures.as_completed(future_to_path)):
            p = future_to_path[future]
            try:
                rep = future.result()
                results.append(rep)
            except Exception as e:
                results.append({
                    "path": p,
                    "name": os.path.basename(p),
                    "status": "corrupt",
                    "issues": [f"Exception non gérée: {e}"],
                    "details": {}
                })
            
            if progress_cb:
                progress_cb(idx + 1, total, p)

    return results
