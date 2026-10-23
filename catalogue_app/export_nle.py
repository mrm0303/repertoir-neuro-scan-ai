import os
import urllib.parse
from xml.sax.saxutils import escape


def _rate_block(fps, indent="            "):
    tb = int(round(fps)) if fps and fps > 0 else 25
    ntsc = "TRUE" if abs((fps or 25.0) - tb) > 0.01 else "FALSE"
    return (
        f"{indent}<rate>\n"
        f"{indent}  <timebase>{tb}</timebase>\n"
        f"{indent}  <ntsc>{ntsc}</ntsc>\n"
        f"{indent}</rate>"
    ), tb, ntsc


def generate_fcp_xml(clips, output_path, project_name="Export Catalogue", create_sequence=True):
    """
    Génère un fichier FCP 7 XML (xmeml version 4) 100% compatible avec Adobe Premiere Pro 2026,
    DaVinci Resolve et Final Cut Pro, avec liaison Audio/Vidéo (<link>) native.
    """
    default_timebase = 25
    default_width = 1920
    default_height = 1080

    clip_metadata = []
    for i, clip in enumerate(clips):
        name = clip.get("name", f"clip_{i}")
        path = clip.get("path", "")
        norm_p = os.path.abspath(path).replace("\\", "/") if path else ""
        if norm_p and not norm_p.startswith("/"):
            norm_p = "/" + norm_p
        file_url = escape("file://localhost" + urllib.parse.quote(norm_p, safe="/:"))

        fps = float(clip.get("fps") or default_timebase)
        rate_xml, timebase, ntsc = _rate_block(fps, "                ")
        duration_sec = float(clip.get("duration") or 5.0)
        if duration_sec <= 0:
            duration_sec = 5.0
        duration_frames = max(1, int(round(duration_sec * timebase)))
        width = int(clip.get("width") or default_width)
        height = int(clip.get("height") or default_height)

        clip_metadata.append({
            "id": i,
            "name": escape(name),
            "file_url": file_url,
            "fps": fps,
            "rate_xml": rate_xml,
            "timebase": timebase,
            "ntsc": ntsc,
            "duration_frames": duration_frames,
            "width": width,
            "height": height
        })

    if not clip_metadata:
        return False

    first_fps = clip_metadata[0]["fps"]
    seq_rate_xml, seq_timebase, seq_ntsc = _rate_block(first_fps, "      ")
    seq_width = clip_metadata[0]["width"]
    seq_height = clip_metadata[0]["height"]
    total_seq_duration = sum(c["duration_frames"] for c in clip_metadata)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE xmeml>',
        '<xmeml version="4">',
        '  <sequence id="sequence-1">',
        f'    <name>{escape(project_name)} - Timeline</name>',
        f'    <duration>{total_seq_duration}</duration>',
        seq_rate_xml,
        '    <timecode>',
        seq_rate_xml.replace("      <", "        <"),
        '      <string>00:00:00:00</string>',
        '      <frame>0</frame>',
        f'      <displayformat>{"DF" if seq_ntsc == "TRUE" and seq_timebase in (30, 60) else "NDF"}</displayformat>',
        '    </timecode>',
        '    <media>',
        '      <video>',
        '        <format>',
        '          <samplecharacteristics>',
        seq_rate_xml.replace("      <", "            <"),
        f'            <width>{seq_width}</width>',
        f'            <height>{seq_height}</height>',
        '            <anamorphic>FALSE</anamorphic>',
        '            <pixelaspectratio>square</pixelaspectratio>',
        '            <fielddominance>none</fielddominance>',
        '          </samplecharacteristics>',
        '        </format>',
        '        <track>'
    ]

    cur_start = 0
    for idx, c in enumerate(clip_metadata):
        dur = c["duration_frames"]
        cur_end = cur_start + dur
        i = c["id"]
        clip_idx = idx + 1
        lines.append(f'          <clipitem id="clipitem-v-{i}">')
        lines.append(f'            <name>{c["name"]}</name>')
        lines.append('            <enabled>TRUE</enabled>')
        lines.append(f'            <duration>{dur}</duration>')
        lines.append(c["rate_xml"].replace("                <", "            <"))
        lines.append(f'            <start>{cur_start}</start>')
        lines.append(f'            <end>{cur_end}</end>')
        lines.append('            <in>0</in>')
        lines.append(f'            <out>{dur}</out>')
        lines.append(f'            <file id="file-{i}">')
        lines.append(f'              <name>{c["name"]}</name>')
        lines.append(f'              <pathurl>{c["file_url"]}</pathurl>')
        lines.append(c["rate_xml"].replace("                <", "              <"))
        lines.append(f'              <duration>{dur}</duration>')
        lines.append('              <timecode>')
        lines.append(c["rate_xml"])
        lines.append('                <string>00:00:00:00</string>')
        lines.append('                <frame>0</frame>')
        lines.append('                <displayformat>NDF</displayformat>')
        lines.append('              </timecode>')
        lines.append('              <media>')
        lines.append('                <video>')
        lines.append('                  <samplecharacteristics>')
        lines.append(c["rate_xml"].replace("                <", "                    <"))
        lines.append(f'                    <width>{c["width"]}</width>')
        lines.append(f'                    <height>{c["height"]}</height>')
        lines.append('                  </samplecharacteristics>')
        lines.append('                </video>')
        lines.append('                <audio>')
        lines.append('                  <samplecharacteristics>')
        lines.append('                    <depth>16</depth>')
        lines.append('                    <samplerate>48000</samplerate>')
        lines.append('                  </samplecharacteristics>')
        lines.append('                  <channelcount>2</channelcount>')
        lines.append('                </audio>')
        lines.append('              </media>')
        lines.append('            </file>')
        lines.append('            <link>')
        lines.append(f'              <linkclipref>clipitem-v-{i}</linkclipref>')
        lines.append('              <mediatype>video</mediatype>')
        lines.append('              <trackindex>1</trackindex>')
        lines.append(f'              <clipindex>{clip_idx}</clipindex>')
        lines.append('            </link>')
        lines.append('            <link>')
        lines.append(f'              <linkclipref>clipitem-a-{i}</linkclipref>')
        lines.append('              <mediatype>audio</mediatype>')
        lines.append('              <trackindex>1</trackindex>')
        lines.append(f'              <clipindex>{clip_idx}</clipindex>')
        lines.append('            </link>')
        lines.append('          </clipitem>')
        cur_start = cur_end

    lines.append('        </track>')
    lines.append('      </video>')
    lines.append('      <audio>')
    lines.append('        <numOutputChannels>2</numOutputChannels>')
    lines.append('        <format>')
    lines.append('          <samplecharacteristics>')
    lines.append('            <depth>16</depth>')
    lines.append('            <samplerate>48000</samplerate>')
    lines.append('          </samplecharacteristics>')
    lines.append('        </format>')
    lines.append('        <track>')

    cur_start = 0
    for idx, c in enumerate(clip_metadata):
        dur = c["duration_frames"]
        cur_end = cur_start + dur
        i = c["id"]
        clip_idx = idx + 1
        lines.append(f'          <clipitem id="clipitem-a-{i}">')
        lines.append(f'            <name>{c["name"]}</name>')
        lines.append('            <enabled>TRUE</enabled>')
        lines.append(f'            <duration>{dur}</duration>')
        lines.append(c["rate_xml"].replace("                <", "            <"))
        lines.append(f'            <start>{cur_start}</start>')
        lines.append(f'            <end>{cur_end}</end>')
        lines.append('            <in>0</in>')
        lines.append(f'            <out>{dur}</out>')
        lines.append(f'            <file id="file-{i}"/>')
        lines.append('            <sourcetrack>')
        lines.append('              <mediatype>audio</mediatype>')
        lines.append('              <trackindex>1</trackindex>')
        lines.append('            </sourcetrack>')
        lines.append('            <link>')
        lines.append(f'              <linkclipref>clipitem-v-{i}</linkclipref>')
        lines.append('              <mediatype>video</mediatype>')
        lines.append('              <trackindex>1</trackindex>')
        lines.append(f'              <clipindex>{clip_idx}</clipindex>')
        lines.append('            </link>')
        lines.append('            <link>')
        lines.append(f'              <linkclipref>clipitem-a-{i}</linkclipref>')
        lines.append('              <mediatype>audio</mediatype>')
        lines.append('              <trackindex>1</trackindex>')
        lines.append(f'              <clipindex>{clip_idx}</clipindex>')
        lines.append('            </link>')
        lines.append('          </clipitem>')
        cur_start = cur_end

    lines.append('        </track>')
    lines.append('      </audio>')
    lines.append('    </media>')
    lines.append('  </sequence>')
    lines.append('</xmeml>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))
    return True
