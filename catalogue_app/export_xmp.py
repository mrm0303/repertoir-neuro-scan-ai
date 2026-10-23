"""
Exporteur XMP Sidecar standard (Adobe / IPTC / Dublin Core).
Permet d'injecter automatiquement les métadonnées, tags IA, caméras et codecs
dans des fichiers sidecar .xmp lisibles directement par Adobe Premiere, DaVinci Resolve,
Lightroom et Final Cut Pro.
"""

import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from .utils import human_size

def generate_xmp_content(file_row, tags=None):
    """
    Génère le contenu XML conforme à la norme Adobe XMP Packet.
    """
    tags = tags or []
    name = file_row.get("name", "")
    camera = file_row.get("camera", "")
    lens = file_row.get("lens", "")
    codec = file_row.get("codec", "")
    shot_date = file_row.get("shot_date", "")
    
    tag_list_str = "".join([f"<rdf:li>{t}</rdf:li>" for t in tags])
    
    xmp_template = f"""<?xpacket begin="" id="W5M0MpCehiHzreSzNTczkc9d"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Catalogue de Disques XMP Exporter">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
    xmlns:tiff="http://ns.adobe.com/tiff/1.0/"
    xmlns:exif="http://ns.adobe.com/exif/1.0/">
   <dc:title>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">{name}</rdf:li>
    </rdf:Alt>
   </dc:title>
   <dc:subject>
    <rdf:Bag>
     {tag_list_str}
    </rdf:Bag>
   </dc:subject>
   <tiff:Make>{camera.split()[0] if camera else ""}</tiff:Make>
   <tiff:Model>{camera}</tiff:Model>
   <exif:LensModel>{lens}</exif:LensModel>
   <xmp:CreateDate>{shot_date}</xmp:CreateDate>
   <photoshop:Format>{codec}</photoshop:Format>
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
<?xpacket end="w"?>"""
    return xmp_template.strip()


def export_xmp_sidecars(con, file_rows, output_dir=None, progress_cb=None):
    """
    Génère des fichiers sidecar .xmp pour une liste de fichiers.
    Si output_dir est None, les crée à côté du fichier d'origine s'il est accessible.
    """
    from .db import tags_for_files
    file_ids = [r["id"] for r in file_rows]
    tag_map = tags_for_files(con, file_ids)
    
    created_count = 0
    total = len(file_rows)
    
    for idx, r in enumerate(file_rows):
        fid = r["id"]
        fname = r["name"]
        tags = tag_map.get(fid, [])
        content = generate_xmp_content(r, tags)
        
        base_name = os.path.splitext(fname)[0]
        xmp_name = f"{base_name}.xmp"
        
        if output_dir:
            out_path = os.path.join(output_dir, xmp_name)
        else:
            # Essayer d'écrire à côté du fichier original si le disque est monté
            last_path = r.get("volume_last_path") or ""
            rel = r.get("rel_path") or ""
            target_file = os.path.join(last_path, rel)
            if os.path.exists(target_file):
                out_path = os.path.splitext(target_file)[0] + ".xmp"
            else:
                continue
                
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            created_count += 1
        except Exception as e:
            print(f"Erreur export XMP {xmp_name}: {e}")
            
        if progress_cb and idx % 200 == 0:
            progress_cb(f"Export XMP : {idx}/{total}", idx, total)
            
    return created_count
