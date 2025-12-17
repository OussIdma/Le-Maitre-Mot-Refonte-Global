"""
PDF Builder pour les fiches MathALÉA
Sprint D - Génération PDF à partir du preview JSON

Architecture:
- Utilise WeasyPrint (comme le système existant)
- Génère 3 types de PDF: sujet, élève, corrigé
- Compatible avec les données du preview Sprint C
"""

import weasyprint
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


def build_sheet_subject_pdf(sheet_preview: dict) -> bytes:
    """
    Génère le PDF "sujet" (sans réponses, pour le professeur)
    
    Contient:
    - Titre de la fiche
    - Métadonnées (niveau, date)
    - Tous les exercices avec leurs énoncés
    - Pas de solutions
    
    Args:
        sheet_preview: Dict contenant le preview complet de la fiche
        
    Returns:
        bytes: Contenu du PDF
    """
    html_content = _build_html_subject(sheet_preview)
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    logger.info(f"✅ PDF Sujet généré: {len(pdf_bytes)} bytes")
    return pdf_bytes


def build_sheet_student_pdf(sheet_preview: dict) -> bytes:
    """
    Génère le PDF "élève" (pour distribution aux élèves)
    
    Contient:
    - Titre de la fiche
    - Métadonnées (niveau, date)
    - Tous les exercices avec leurs énoncés
    - Espace pour les réponses
    - Pas de solutions
    
    Args:
        sheet_preview: Dict contenant le preview complet de la fiche
        
    Returns:
        bytes: Contenu du PDF
    """
    html_content = _build_html_student(sheet_preview)
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    logger.info(f"✅ PDF Élève généré: {len(pdf_bytes)} bytes")
    return pdf_bytes


def build_sheet_correction_pdf(sheet_preview: dict) -> bytes:
    """
    Génère le PDF "corrigé" (avec toutes les solutions)
    
    Contient:
    - Titre de la fiche
    - Métadonnées (niveau, date)
    - Tous les exercices avec leurs énoncés
    - Toutes les solutions détaillées
    
    Args:
        sheet_preview: Dict contenant le preview complet de la fiche
        
    Returns:
        bytes: Contenu du PDF
    """
    html_content = _build_html_correction(sheet_preview)
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    logger.info(f"✅ PDF Corrigé généré: {len(pdf_bytes)} bytes")
    return pdf_bytes


# ============================================================================
# Fonctions internes de génération HTML
# ============================================================================

def _build_html_subject(sheet_preview: dict) -> str:
    """Génère le HTML pour le PDF sujet (prof)"""
    
    titre = sheet_preview.get("titre", "Feuille d'exercices")
    niveau = sheet_preview.get("niveau", "")
    items = sheet_preview.get("items", [])
    
    # Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {_get_base_css()}
            .answer-space {{
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{titre}</h1>
            <div class="metadata">
                <span class="niveau">Niveau: {niveau}</span>
                <span class="date">Date: {datetime.now().strftime("%d/%m/%Y")}</span>
                <span class="type">Sujet (Professeur)</span>
            </div>
        </div>
        
        <div class="content">
    """
    
    # Exercises
    for ex_idx, item in enumerate(items, 1):
        html += _render_exercise(item, ex_idx, include_solutions=False, is_student=False)
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def _build_html_student(sheet_preview: dict) -> str:
    """Génère le HTML pour le PDF élève"""
    
    titre = sheet_preview.get("titre", "Feuille d'exercices")
    niveau = sheet_preview.get("niveau", "")
    items = sheet_preview.get("items", [])
    
    # Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {_get_base_css()}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{titre}</h1>
            <div class="metadata">
                <span class="niveau">Niveau: {niveau}</span>
                <span class="date">Date: {datetime.now().strftime("%d/%m/%Y")}</span>
            </div>
            <div class="student-info">
                <p>Nom: ________________  Prénom: ________________  Classe: ________</p>
            </div>
        </div>
        
        <div class="content">
    """
    
    # Exercises
    for ex_idx, item in enumerate(items, 1):
        html += _render_exercise(item, ex_idx, include_solutions=False, is_student=True)
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def _build_html_correction(sheet_preview: dict) -> str:
    """Génère le HTML pour le PDF corrigé"""
    
    titre = sheet_preview.get("titre", "Feuille d'exercices")
    niveau = sheet_preview.get("niveau", "")
    items = sheet_preview.get("items", [])
    
    # Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {_get_base_css()}
            .solution {{
                background-color: #f0f8ff;
                border-left: 4px solid #4CAF50;
                padding: 10px;
                margin-top: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>{titre}</h1>
            <div class="metadata">
                <span class="niveau">Niveau: {niveau}</span>
                <span class="date">Date: {datetime.now().strftime("%d/%m/%Y")}</span>
                <span class="type">Corrigé</span>
            </div>
        </div>
        
        <div class="content">
    """
    
    # Exercises
    for ex_idx, item in enumerate(items, 1):
        html += _render_exercise(item, ex_idx, include_solutions=True, is_student=False)
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def _render_exercise(item: dict, ex_number: int, include_solutions: bool, is_student: bool) -> str:
    """
    Rendu HTML d'un exercice complet
    
    Args:
        item: Item du preview contenant generated
        ex_number: Numéro de l'exercice
        include_solutions: Inclure les solutions
        is_student: Version élève (avec espace de réponse)
    """
    exercise_type_summary = item.get("exercise_type_summary", {})
    generated = item.get("generated", {})
    questions = generated.get("questions", [])
    
    titre = exercise_type_summary.get("titre", f"Exercice {ex_number}")
    domaine = exercise_type_summary.get("domaine", "")
    
    html = f"""
    <div class="exercise">
        <div class="exercise-header">
            <h2>Exercice {ex_number}</h2>
            <p class="exercise-title">{titre}</p>
            {f'<p class="exercise-domain">{domaine}</p>' if domaine else ''}
        </div>
        
        <div class="questions">
    """
    
    # Questions
    for q_idx, question in enumerate(questions, 1):
        html += _render_question(question, q_idx, include_solutions, is_student)
    
    html += """
        </div>
    </div>
    """
    
    return html


def _render_question(question: dict, q_number: int, include_solution: bool, is_student: bool) -> str:
    """
    Rendu HTML d'une question
    
    Args:
        question: Question du preview
        q_number: Numéro de la question
        include_solution: Inclure la solution
        is_student: Version élève (avec espace de réponse)
    """
    enonce = question.get("enonce_brut", "")
    solution = question.get("solution_brut", "")
    data = question.get("data", {})
    
    # Nettoyer et formater l'énoncé
    enonce_html = _format_text(enonce)
    
    # Récupérer la figure HTML si présente
    figure_html = question.get("figure_html", "")
    
    html = f"""
    <div class="question">
        <div class="question-header">
            <strong>Question {q_number}:</strong>
        </div>
        <div class="question-enonce">
            {enonce_html}
        </div>
    """
    
    # Ajouter la figure géométrique si présente
    if figure_html:
        html += f"""
        <div class="exercise-figure">
            {figure_html}
        </div>
        """
    
    # Espace de réponse pour version élève
    if is_student:
        html += """
        <div class="answer-space">
            <p><em>Réponse:</em></p>
            <div style="height: 80px; border: 1px dashed #ccc; margin: 10px 0;"></div>
        </div>
        """
    
    # Solution (uniquement pour corrigé)
    if include_solution:
        solution_html = _format_text(solution)
        html += f"""
        <div class="solution">
            <strong>Solution:</strong><br>
            {solution_html}
        </div>
        """
    
    html += """
    </div>
    """
    
    return html


def _format_text(text: str) -> str:
    """Formate le texte brut en HTML (gestion des sauts de ligne, etc.)"""
    if not text:
        return ""
    
    # Remplacer les sauts de ligne par <br>
    text = text.replace("\n", "<br>")
    
    # Gérer les caractères spéciaux HTML
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    
    # Remettre les <br> après l'échappement
    text = text.replace("&lt;br&gt;", "<br>")
    
    return text


def _get_base_css() -> str:
    """CSS de base pour tous les PDFs"""
    return """
        @page {
            size: A4;
            margin: 2cm 1.5cm;
        }
        
        body {
            font-family: 'Arial', sans-serif;
            font-size: 11pt;
            line-height: 1.5;
            color: #333;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #2c3e50;
            padding-bottom: 15px;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 22pt;
            margin-bottom: 10px;
        }
        
        .metadata {
            font-size: 10pt;
            color: #666;
            margin-top: 10px;
        }
        
        .metadata span {
            margin: 0 15px;
        }
        
        .student-info {
            margin-top: 15px;
            font-size: 10pt;
            text-align: left;
        }
        
        .exercise {
            margin-bottom: 30px;
            page-break-inside: avoid;
        }
        
        .exercise-header {
            background-color: #f5f5f5;
            padding: 10px;
            border-left: 4px solid #3498db;
            margin-bottom: 15px;
        }
        
        .exercise-header h2 {
            color: #2c3e50;
            font-size: 14pt;
            margin: 0 0 5px 0;
        }
        
        .exercise-title {
            font-weight: bold;
            color: #34495e;
            margin: 5px 0;
        }
        
        .exercise-domain {
            font-size: 9pt;
            color: #7f8c8d;
            font-style: italic;
            margin: 0;
        }
        
        .questions {
            padding-left: 10px;
        }
        
        .question {
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        
        .question-header {
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .question-enonce {
            margin-left: 20px;
            line-height: 1.6;
        }
        
        .answer-space {
            margin: 15px 0 15px 20px;
        }
        
        .solution {
            margin: 15px 0 15px 20px;
            padding: 10px;
            background-color: #f0f8ff;
            border-left: 4px solid #4CAF50;
        }
        
        .solution strong {
            color: #27ae60;
        }
        
        /* Styles pour les figures géométriques */
        .exercise-figure {
            margin: 14px 0;
            text-align: center;
            width: 100%;
        }
        
        .exercise-figure svg {
            max-width: 100%;
            height: auto;
        }
    """


def build_sheet_pro_pdf(legacy_format: dict, template: str = "classique", user_config: dict = None) -> bytes:
    """
    Génère un PDF Pro personnalisé à partir du format legacy
    
    Ce PDF inclut:
    - Logo de l'établissement
    - Template personnalisé (classique ou académique)
    - Couleur primaire personnalisée
    - Énoncés et corrections
    
    Args:
        legacy_format: Dict au format legacy Pro generator
        template: "classique" ou "academique"
        user_config: Configuration utilisateur (optionnel)
    
    Returns:
        bytes: Contenu du PDF Pro personnalisé
    """
    # Choisir le template approprié
    if template == "academique":
        html_content = _build_html_pro_academique(legacy_format, user_config)
    else:  # "classique" par défaut
        html_content = _build_html_pro_classique(legacy_format, user_config)
    
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    logger.info(f"✅ PDF Pro généré ({template}): {len(pdf_bytes)} bytes")
    return pdf_bytes


def _build_html_pro_classique(legacy_format: dict, user_config: dict = None) -> str:
    """Génère le HTML pour le PDF Pro personnalisé"""
    
    titre = legacy_format.get("titre", "Feuille d'exercices")
    niveau = legacy_format.get("niveau", "")
    etablissement = legacy_format.get("etablissement", "")
    logo_url = legacy_format.get("logo_url")
    primary_color = legacy_format.get("primary_color", "#1a56db")
    exercices = legacy_format.get("exercices", [])
    
    # Header avec logo
    header_html = f"""
    <div class="header">
        <div class="header-content">
            {"<img src='" + logo_url + "' class='logo' />" if logo_url else ""}
            <div class="header-text">
                <h1>{titre}</h1>
                {"<p class='etablissement'>" + etablissement + "</p>" if etablissement else ""}
                <p class="niveau">{niveau}</p>
            </div>
        </div>
        <div class="date">{datetime.now().strftime("%d/%m/%Y")}</div>
    </div>
    """
    
    # Exercices
    exercices_html = ""
    for exercice in exercices:
        numero = exercice.get("numero", "")
        titre_ex = exercice.get("titre", "")
        enonce = exercice.get("enonce", "")
        correction = exercice.get("correction", "")
        metadata = exercice.get("metadata", {})
        domaine = metadata.get("domaine", "")
        
        exercices_html += f"""
        <div class="exercise">
            <div class="exercise-header">
                <h2 class="exercise-number">Exercice {numero}</h2>
                <p class="exercise-title">{titre_ex}</p>
                {"<p class='exercise-domain'>" + domaine + "</p>" if domaine else ""}
            </div>
            
            <div class="exercise-enonce">
                <h3>Énoncé</h3>
                <div class="content">
                    {enonce.replace(chr(10), '<br/>')}
                </div>
            </div>
            
            <div class="exercise-correction">
                <h3>Correction</h3>
                <div class="content">
                    {correction.replace(chr(10), '<br/>')}
                </div>
            </div>
        </div>
        """
    
    # CSS Pro personnalisé
    css = f"""
    <style>
        @page {{
            size: A4;
            margin: 20mm;
            @top-center {{
                content: "Le Maître Mot - {etablissement}";
                font-size: 9pt;
                color: #7f8c8d;
            }}
            @bottom-center {{
                content: "Page " counter(page);
                font-size: 9pt;
                color: #7f8c8d;
            }}
        }}
        
        body {{
            font-family: 'Arial', 'Helvetica', sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #2c3e50;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid {primary_color};
        }}
        
        .header-content {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 20px;
            margin-bottom: 10px;
        }}
        
        .logo {{
            max-height: 60px;
            max-width: 100px;
        }}
        
        .header-text h1 {{
            color: {primary_color};
            font-size: 20pt;
            margin: 0 0 5px 0;
            font-weight: bold;
        }}
        
        .etablissement {{
            font-size: 12pt;
            color: #34495e;
            margin: 0;
            font-weight: 500;
        }}
        
        .niveau {{
            font-size: 10pt;
            color: #7f8c8d;
            margin: 0;
        }}
        
        .date {{
            font-size: 9pt;
            color: #7f8c8d;
            font-style: italic;
        }}
        
        .exercise {{
            margin-bottom: 40px;
            page-break-inside: avoid;
        }}
        
        .exercise-header {{
            margin-bottom: 15px;
            padding: 10px;
            background-color: {primary_color}15;
            border-left: 4px solid {primary_color};
        }}
        
        .exercise-number {{
            color: {primary_color};
            font-size: 16pt;
            margin: 0 0 5px 0;
            font-weight: bold;
        }}
        
        .exercise-title {{
            color: #2c3e50;
            font-size: 12pt;
            margin: 0;
            font-weight: 500;
        }}
        
        .exercise-domain {{
            font-size: 9pt;
            color: #7f8c8d;
            font-style: italic;
            margin: 5px 0 0 0;
        }}
        
        .exercise-enonce, .exercise-correction {{
            margin-bottom: 20px;
        }}
        
        .exercise-enonce h3, .exercise-correction h3 {{
            color: {primary_color};
            font-size: 12pt;
            margin: 10px 0;
            font-weight: 600;
        }}
        
        .content {{
            padding-left: 20px;
            line-height: 1.8;
        }}
        
        .exercise-correction {{
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #27ae60;
        }}
        
        .exercise-correction h3 {{
            color: #27ae60;
        }}
        
        /* Styles pour les figures géométriques */
        .exercise-figure {{
            margin: 14px 0;
            text-align: center;
            width: 100%;
        }}
        
        .exercise-figure svg {{
            max-width: 100%;
            height: auto;
        }}
    </style>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{titre}</title>
        {css}
    </head>
    <body>
        {header_html}
        {exercices_html}
    </body>
    </html>
    """
    
    return html



def _build_html_pro_academique(legacy_format: dict, user_config: dict = None) -> str:
    """Génère le HTML pour le PDF Pro avec template académique (style formel)"""
    
    titre = legacy_format.get("titre", "Feuille d'exercices")
    niveau = legacy_format.get("niveau", "")
    etablissement = legacy_format.get("etablissement", "")
    logo_url = legacy_format.get("logo_url")
    primary_color = legacy_format.get("primary_color", "#2c5282")  # Bleu plus sombre pour style académique
    exercices = legacy_format.get("exercices", [])
    
    # Header formel avec cadre
    header_html = f"""
    <div class="header">
        <div class="header-top">
            {"<img src='" + logo_url + "' class='logo' />" if logo_url else ""}
            <div class="institution-info">
                {"<p class='etablissement'>" + etablissement + "</p>" if etablissement else ""}
                <p class="date">{datetime.now().strftime("%d/%m/%Y")}</p>
            </div>
        </div>
        <div class="header-center">
            <h1>{titre}</h1>
            <p class="niveau">{niveau}</p>
        </div>
    </div>
    """
    
    # Exercices avec style académique
    exercices_html = ""
    for exercice in exercices:
        numero = exercice.get("numero", "")
        titre_ex = exercice.get("titre", "")
        enonce = exercice.get("enonce", "")
        correction = exercice.get("correction", "")
        metadata = exercice.get("metadata", {})
        domaine = metadata.get("domaine", "")
        
        exercices_html += f"""
        <div class="exercise">
            <div class="exercise-header">
                <div class="exercise-number">EXERCICE {numero}</div>
                <div class="exercise-meta">
                    <span class="exercise-title">{titre_ex}</span>
                    {"<span class='exercise-domain'> — " + domaine + "</span>" if domaine else ""}
                </div>
            </div>
            
            <div class="exercise-section">
                <div class="section-label">ÉNONCÉ</div>
                <div class="section-content">
                    {enonce.replace(chr(10), '<br/>')}
                </div>
            </div>
            
            <div class="exercise-section correction-section">
                <div class="section-label">ÉLÉMENTS DE CORRECTION</div>
                <div class="section-content">
                    {correction.replace(chr(10), '<br/>')}
                </div>
            </div>
        </div>
        """
    
    # CSS Académique formel
    css = f"""
    <style>
        @page {{
            size: A4;
            margin: 25mm 20mm;
            @top-right {{
                content: "{etablissement}";
                font-size: 8pt;
                color: #666;
                font-style: italic;
            }}
            @bottom-center {{
                content: "Page " counter(page) " / " counter(pages);
                font-size: 8pt;
                color: #666;
            }}
        }}
        
        body {{
            font-family: 'Times New Roman', 'Georgia', serif;
            font-size: 11pt;
            line-height: 1.7;
            color: #1a1a1a;
        }}
        
        .header {{
            border: 2px solid {primary_color};
            padding: 15px;
            margin-bottom: 30px;
        }}
        
        .header-top {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 1px solid #ccc;
        }}
        
        .logo {{
            max-height: 50px;
            max-width: 80px;
        }}
        
        .institution-info {{
            text-align: right;
        }}
        
        .etablissement {{
            font-size: 11pt;
            font-weight: bold;
            color: {primary_color};
            margin: 0 0 5px 0;
        }}
        
        .date {{
            font-size: 9pt;
            color: #666;
            margin: 0;
        }}
        
        .header-center {{
            text-align: center;
        }}
        
        .header-center h1 {{
            color: {primary_color};
            font-size: 18pt;
            margin: 0 0 5px 0;
            font-weight: bold;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .niveau {{
            font-size: 11pt;
            color: #333;
            margin: 0;
            font-weight: 500;
        }}
        
        .exercise {{
            margin-bottom: 35px;
            page-break-inside: avoid;
        }}
        
        .exercise-header {{
            border-bottom: 2px solid {primary_color};
            margin-bottom: 15px;
            padding-bottom: 8px;
        }}
        
        .exercise-number {{
            color: {primary_color};
            font-size: 13pt;
            font-weight: bold;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }}
        
        .exercise-meta {{
            font-size: 10pt;
            color: #333;
        }}
        
        .exercise-title {{
            font-weight: 600;
        }}
        
        .exercise-domain {{
            font-style: italic;
            color: #666;
        }}
        
        .exercise-section {{
            margin-bottom: 20px;
            padding-left: 15px;
        }}
        
        .section-label {{
            font-size: 10pt;
            font-weight: bold;
            color: {primary_color};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            border-left: 3px solid {primary_color};
            padding-left: 8px;
        }}
        
        .section-content {{
            padding-left: 12px;
            line-height: 1.8;
            text-align: justify;
        }}
        
        .correction-section {{
            background-color: #f9f9f9;
            padding: 15px;
            border-left: 3px solid #5a7a3d;
            margin-left: 0;
        }}
        
        .correction-section .section-label {{
            color: #5a7a3d;
            border-left-color: #5a7a3d;
        }}
        
        /* Styles pour les figures géométriques */
        .exercise-figure {{
            margin: 14px 0;
            text-align: center;
            width: 100%;
        }}
        
        .exercise-figure svg {{
            max-width: 100%;
            height: auto;
        }}
    </style>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{titre}</title>
        {css}
    </head>
    <body>
        {header_html}
        {exercices_html}
    </body>
    </html>
    """
    
    return html


# Export des fonctions publiques
__all__ = [
    "build_sheet_subject_pdf",
    "build_sheet_student_pdf",
    "build_sheet_correction_pdf",
    "build_sheet_pro_pdf"
]
