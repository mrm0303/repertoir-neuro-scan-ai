import os
import sqlite3
from datetime import datetime
from fpdf import FPDF
from .utils import human_size, human_count

class DeliveryReport(FPDF):
    def __init__(self, title, client_name=""):
        super().__init__()
        self.doc_title = title
        self.client_name = client_name
        
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, self.doc_title, border=False, align='L')
        if self.client_name:
            self.set_font('helvetica', 'I', 12)
            self.cell(0, 10, f"Pour : {self.client_name}", border=False, align='R')
        self.ln(15)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        date_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        self.cell(0, 10, f'Généré le {date_str} - Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(con: sqlite3.Connection, vol_id: int, vol_name: str, output_path: str):
    pdf = DeliveryReport(title=f"Rapport de Livraison : {vol_name}")
    pdf.add_page()
    
    # Statistiques globales
    stats = con.execute("SELECT COUNT(*) as n, SUM(size) as s FROM files WHERE volume_id=?", (vol_id,)).fetchone()
    total_files = stats["n"] or 0
    total_size = stats["s"] or 0
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "1. Résumé du Volume", ln=True)
    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 8, f"Nom du Disque : {vol_name}", ln=True)
    pdf.cell(0, 8, f"Nombre total de fichiers : {human_count(total_files)}", ln=True)
    pdf.cell(0, 8, f"Poids total : {human_size(total_size)}", ln=True)
    pdf.ln(5)
    
    # Caméras utilisées
    cameras = con.execute("SELECT camera, COUNT(*) as n FROM files WHERE volume_id=? AND camera IS NOT NULL AND camera != '' GROUP BY camera ORDER BY n DESC", (vol_id,)).fetchall()
    if cameras:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "2. Matériel & Caméras Détectés", ln=True)
        pdf.set_font("helvetica", "", 10)
        for c in cameras:
            pdf.cell(0, 8, f"- {c['camera']} : {human_count(c['n'])} fichier(s)", ln=True)
        pdf.ln(5)
        
    # Statistiques par catégorie
    categories = con.execute("SELECT category, COUNT(*) as n, SUM(size) as s FROM files WHERE volume_id=? GROUP BY category ORDER BY s DESC", (vol_id,)).fetchall()
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "3. Répartition par type de média", ln=True)
    pdf.set_font("helvetica", "", 10)
    
    # Table header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(60, 8, "Catégorie", border=1, fill=True)
    pdf.cell(40, 8, "Fichiers", border=1, fill=True)
    pdf.cell(50, 8, "Poids", border=1, fill=True, ln=True)
    
    for cat in categories:
        c_name = str(cat['category']).capitalize()
        pdf.cell(60, 8, c_name, border=1)
        pdf.cell(40, 8, str(human_count(cat['n'])), border=1)
        pdf.cell(50, 8, str(human_size(cat['s'])), border=1, ln=True)
    pdf.ln(10)
    
    # Arborescence (Top level folders)
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 10, "4. Arborescence principale (Dossiers racine)", ln=True)
    pdf.set_font("helvetica", "", 10)
    
    # Extraire les dossiers de premier niveau
    # On utilise SQLite substr/instr pour grouper par dossier racine
    folders = con.execute("""
        SELECT 
            CASE 
                WHEN instr(rel_path, '/') > 0 THEN substr(rel_path, 1, instr(rel_path, '/') - 1)
                ELSE 'Racine' 
            END as root_folder,
            COUNT(*) as n,
            SUM(size) as s
        FROM files 
        WHERE volume_id=?
        GROUP BY root_folder
        ORDER BY s DESC
        LIMIT 40
    """, (vol_id,)).fetchall()
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(90, 8, "Dossier", border=1, fill=True)
    pdf.cell(40, 8, "Fichiers", border=1, fill=True)
    pdf.cell(50, 8, "Poids", border=1, fill=True, ln=True)
    
    for f in folders:
        # Prevent very long folder names from breaking layout
        name_trunc = f['root_folder'][:40] + ('...' if len(f['root_folder'])>40 else '')
        pdf.cell(90, 8, name_trunc, border=1)
        pdf.cell(40, 8, str(human_count(f['n'])), border=1)
        pdf.cell(50, 8, str(human_size(f['s'])), border=1, ln=True)
        
    pdf.output(output_path)
