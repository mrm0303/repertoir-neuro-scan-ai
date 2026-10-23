import sqlite3
import os
import json
import webbrowser
from .config import APP_DIR
from .utils import human_size

def build_tree(rows):
    root = {"name": "Disque", "value": 0, "children": {}}
    
    for row in rows:
        folder = row["folder"]
        size = row["total_size"] or 0
        if not folder or folder == ".":
            # Files at root
            root["value"] += size
            continue
            
        parts = folder.split('/')
        current = root
        current["value"] += size
        
        for part in parts:
            if part not in current["children"]:
                current["children"][part] = {"name": part, "value": 0, "children": {}}
            current = current["children"][part]
            current["value"] += size
            
    # Convert children dict to list recursively
    def format_node(node):
        if "children" in node:
            if node["children"]:
                node["children"] = [format_node(c) for c in node["children"].values()]
            else:
                del node["children"]
        return node
        
    return format_node(root)

def generate_sunburst(con, vol_id, vol_name):
    # Get aggregated sizes by folder
    cur = con.execute("SELECT folder, SUM(size) as total_size FROM files WHERE volume_id=? GROUP BY folder", (vol_id,))
    rows = cur.fetchall()
    
    tree_data = build_tree(rows)
    # Set the root name to volume name
    tree_data["name"] = vol_name
    
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Analyse - {vol_name}</title>
    <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background-color: #222428; color: white; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        #main {{ width: 100vw; height: 100vh; }}
        .header {{ position: absolute; top: 20px; left: 20px; z-index: 10; }}
        h1 {{ margin: 0; font-size: 24px; font-weight: 500; }}
        p {{ margin: 5px 0 0 0; color: #aaa; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{vol_name}</h1>
        <p>Cliquez sur un segment pour zoomer. Cliquez au centre pour dézoomer.</p>
    </div>
    <div id="main"></div>
    <script>
        var chartDom = document.getElementById('main');
        var myChart = echarts.init(chartDom, 'dark', {{ renderer: 'canvas' }});
        var option;

        const data = [{json.dumps(tree_data)}];

        option = {{
            backgroundColor: '#222428',
            tooltip: {{
                trigger: 'item',
                formatter: function (info) {{
                    var value = info.value;
                    var size = (value / (1024*1024*1024)).toFixed(2) + ' Go';
                    if (value < 1024*1024*1024) size = (value / (1024*1024)).toFixed(2) + ' Mo';
                    return info.name + '<br>Taille: ' + size;
                }}
            }},
            series: {{
                type: 'sunburst',
                data: data,
                radius: [0, '95%'],
                sort: 'desc',
                emphasis: {{
                    focus: 'ancestor'
                }},
                levels: [
                    {{}},
                    {{
                        r0: '15%',
                        r: '35%',
                        itemStyle: {{ borderWidth: 2 }},
                        label: {{ rotate: 'tangential' }}
                    }},
                    {{
                        r0: '35%',
                        r: '70%',
                        label: {{ align: 'right' }}
                    }},
                    {{
                        r0: '70%',
                        r: '72%',
                        label: {{ position: 'outside', padding: 3, silent: false }}
                    }}
                ]
            }}
        }};

        option && myChart.setOption(option);
        
        window.addEventListener('resize', function() {{
            myChart.resize();
        }});
    </script>
</body>
</html>
"""
    dash_dir = os.path.join(APP_DIR, "Dashboards")
    os.makedirs(dash_dir, exist_ok=True)
    out_path = os.path.join(dash_dir, f"dashboard_{vol_name}.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return out_path

