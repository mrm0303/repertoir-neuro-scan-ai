import sqlite3
import os
import json
from .utils import human_size

def generate_volume_html(con, volume_id, volume_name, out_path):
    # Fetch all files for this volume
    rows = con.execute(
        "SELECT rel_path, name, size, category FROM files WHERE volume_id = ? ORDER BY rel_path",
        (volume_id,)
    ).fetchall()

    if not rows:
        raise Exception("Aucun fichier trouvé pour ce volume.")

    # Build the tree structure
    # tree = {"/": {"_files": [], "sub": {}}}
    tree = {"_files": [], "sub": {}, "size": 0}
    
    total_size = 0
    for r in rows:
        path = r["rel_path"].strip("/")
        size = r["size"] or 0
        total_size += size
        
        parts = path.split("/") if path else []
        current = tree
        current["size"] += size
        
        for p in parts:
            if p not in current["sub"]:
                current["sub"][p] = {"_files": [], "sub": {}, "size": 0}
            current = current["sub"][p]
            current["size"] += size
            
        current["_files"].append({
            "name": r["name"],
            "size": size,
            "category": r["category"]
        })

    # 1. Recursive function to build Treemap data (Google Charts format)
    # Format: [ ['Name', 'Parent', 'Size', 'Color'], ... ]
    treemap_data = [["Dossier", "Parent", "Taille (Octets)", "Couleur"]]
    treemap_data.append(["Racine (Disque)", None, 0, 0])
    
    def build_treemap_data(node, node_path, parent_path):
        # Only add directories to the treemap to avoid overloading
        # Calculate size of this directory
        my_size = node["size"]
        
        # If it's too small compared to total, skip for the treemap (e.g., < 0.1% to avoid JS crash)
        if total_size > 0 and (my_size / total_size) < 0.001:
            return

        uid = node_path if node_path else "Racine (Disque)"
        p_uid = parent_path if parent_path else "Racine (Disque)"
        
        if uid != "Racine (Disque)":
            # Just use folder name, but append a unique ID to avoid collisions
            display_name = uid.split("/")[-1]
            if not display_name: display_name = "Racine"
            treemap_data.append([uid, p_uid, my_size, 0])
            
        for child_name, child_node in node["sub"].items():
            child_path = f"{node_path}/{child_name}" if node_path else child_name
            build_treemap_data(child_node, child_path, uid)

    build_treemap_data(tree, "", None)

    # 2. Recursive function to build the HTML Directory Tree
    def build_html_tree(node, name):
        html = f"<details><summary>📁 <b>{name}</b> <span class='size'>({human_size(node['size'])})</span></summary><ul>"
        
        for child_name, child_node in sorted(node["sub"].items(), key=lambda x: x[1]["size"], reverse=True):
            html += f"<li>{build_html_tree(child_node, child_name)}</li>"
            
        for f in sorted(node["_files"], key=lambda x: x["size"], reverse=True):
            icon = "📄"
            cat = f["category"]
            if cat == "video": icon = "🎥"
            elif cat == "image": icon = "📷"
            elif cat == "audio": icon = "🎵"
            html += f"<li>{icon} {f['name']} <span class='size'>({human_size(f['size'])})</span></li>"
            
        html += "</ul></details>"
        return html

    html_list = build_html_tree(tree, volume_name)

    # Template HTML
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Backup Visuel : {volume_name}</title>
    <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #1e1e2e; color: #cdd6f4; margin: 0; padding: 20px; }}
        h1 {{ color: #89b4fa; text-align: center; border-bottom: 2px solid #313244; padding-bottom: 10px; }}
        .container {{ display: flex; flex-direction: column; gap: 20px; max-width: 1200px; margin: 0 auto; }}
        .card {{ background: #313244; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        #chart_div {{ width: 100%; height: 600px; }}
        details {{ margin-left: 15px; margin-top: 5px; }}
        summary {{ cursor: pointer; padding: 4px; border-radius: 4px; }}
        summary:hover {{ background: #45475a; }}
        ul {{ list-style-type: none; border-left: 1px solid #585b70; margin: 0; padding-left: 15px; }}
        li {{ padding: 2px 0; }}
        .size {{ color: #a6adc8; font-size: 0.9em; }}
    </style>
    <script type="text/javascript">
      google.charts.load('current', {{'packages':['treemap']}});
      google.charts.setOnLoadCallback(drawChart);
      function drawChart() {{
        var data = google.visualization.arrayToDataTable({json.dumps(treemap_data)});
        var tree = new google.visualization.TreeMap(document.getElementById('chart_div'));
        tree.draw(data, {{
          minColor: '#f00',
          midColor: '#ddd',
          maxColor: '#0d0',
          headerHeight: 25,
          fontColor: 'black',
          showScale: true
        }});
      }}
    </script>
</head>
<body>
    <div class="container">
        <h1>Disque : {volume_name}</h1>
        <div style="text-align: center; color: #a6adc8; margin-bottom: 20px;">
            Taille totale : {human_size(total_size)}
        </div>
        
        <div class="card">
            <h2 style="color: #a6e3a1; margin-top: 0;">🗺️ Treemap Interactif (Dossiers)</h2>
            <div id="chart_div"></div>
        </div>

        <div class="card">
            <h2 style="color: #f9e2af; margin-top: 0;">🗂️ Arborescence complète (Screenshot visuel)</h2>
            <p style="color: #9399b2; font-size: 0.9em;">Cliquez sur les dossiers pour les dérouler.</p>
            {html_list}
        </div>
    </div>
</body>
</html>"""

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return True
