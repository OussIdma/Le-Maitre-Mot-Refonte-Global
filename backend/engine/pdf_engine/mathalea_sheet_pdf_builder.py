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


def build_sheet_student_pdf(sheet_preview: dict, layout: str = "eco") -> bytes:
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
        layout: "eco" (2 colonnes, compact) ou "classic" (1 colonne, standard)
        
    Returns:
        bytes: Contenu du PDF
    """
    html_content = _build_html_student(sheet_preview, layout=layout)
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    logger.info(f"✅ PDF Élève généré (layout={layout}): {len(pdf_bytes)} bytes")
    return pdf_bytes


def build_sheet_correction_pdf(sheet_preview: dict, layout: str = "eco") -> bytes:
    """
    Génère le PDF "corrigé" (avec toutes les solutions)
    
    Contient:
    - Titre de la fiche
    - Métadonnées (niveau, date)
    - Tous les exercices avec leurs énoncés
    - Toutes les solutions détaillées
    
    Args:
        sheet_preview: Dict contenant le preview complet de la fiche
        layout: "eco" (2 colonnes, compact) ou "classic" (1 colonne, standard)
        
    Returns:
        bytes: Contenu du PDF
    """
    html_content = _build_html_correction(sheet_preview, layout=layout)
    pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
    
    logger.info(f"✅ PDF Corrigé généré (layout={layout}): {len(pdf_bytes)} bytes")
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
        html += _render_exercise(item, ex_idx, include_solutions=False, is_student=False, layout="classic")
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def _build_html_student(sheet_preview: dict, layout: str = "eco") -> str:
    """Génère le HTML pour le PDF élève"""
    
    titre = sheet_preview.get("titre", "Feuille d'exercices")
    niveau = sheet_preview.get("niveau", "")
    items = sheet_preview.get("items", [])
    
    # Choisir le CSS selon le layout
    css = _get_eco_css() if layout == "eco" else _get_base_css()
    
    # Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {css}
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
    
    # PR6.3: Si layout=eco, créer eco-columns au niveau du contenu
    # (les blocs fullwidth seront gérés dans _render_exercise)
    if layout == "eco":
        html += '<div class="eco-columns">'
    
    # Exercises
    for ex_idx, item in enumerate(items, 1):
        exercise_html = _render_exercise(item, ex_idx, include_solutions=False, is_student=True, layout=layout)
        html += exercise_html
    
    # PR6.3: Fermer eco-columns si ouvert
    if layout == "eco":
        html += '</div>'
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def _build_html_correction(sheet_preview: dict, layout: str = "eco") -> str:
    """Génère le HTML pour le PDF corrigé
    
    PR6.1: Le corrigé est TOUJOURS en 1 colonne (classic) pour éviter les trous/espaces.
    Le paramètre layout=eco est ignoré pour le corrigé.
    """
    
    titre = sheet_preview.get("titre", "Feuille d'exercices")
    niveau = sheet_preview.get("niveau", "")
    items = sheet_preview.get("items", [])
    
    # PR6.1: Corrigé toujours en classic (1 colonne) pour éviter les trous
    # Ignorer layout=eco pour le corrigé
    css = _get_base_css()
    if layout == "eco":
        logger.info("[PDF_CORRECTION] layout=eco ignoré pour corrigé, utilisation de classic (1 colonne)")
    
    # Header
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            {css}
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
            <h1 class="sheet-title">{titre}</h1>
            <div class="sheet-meta">
                <span class="niveau">Niveau: {niveau}</span>
                <span class="date">Date: {datetime.now().strftime("%d/%m/%Y")}</span>
                <span class="type">Corrigé</span>
            </div>
        </div>
        
        <div class="content">
    """
    
    # Exercises
    for ex_idx, item in enumerate(items, 1):
        html += _render_exercise(item, ex_idx, include_solutions=True, is_student=False, layout="classic")
    
    html += """
        </div>
    </body>
    </html>
    """
    
    return html


def _render_exercise(item: dict, ex_number: int, include_solutions: bool, is_student: bool, layout: str = "eco") -> str:
    """
    Rendu HTML d'un exercice complet
    
    Args:
        item: Item du preview contenant generated
        ex_number: Numéro de l'exercice
        include_solutions: Inclure les solutions
        is_student: Version élève (avec espace de réponse)
        layout: "eco" ou "classic" - PR6.2: pour wrapper les tableaux/figures en .fullwidth
    """
    exercise_type_summary = item.get("exercise_type_summary", {})
    generated = item.get("generated", {})
    questions = generated.get("questions", [])
    
    titre = exercise_type_summary.get("titre", f"Exercice {ex_number}")
    domaine = exercise_type_summary.get("domaine", "")
    
    # PR6.3: Rendre les questions et collecter les blocs fullwidth
    question_html_parts = []
    all_fullwidth_blocks = []
    
    for q_idx, question in enumerate(questions, 1):
        q_html, q_fullwidth_blocks = _render_question(question, q_idx, include_solutions, is_student, layout=layout)
        question_html_parts.append((q_html, q_fullwidth_blocks))
        all_fullwidth_blocks.extend(q_fullwidth_blocks)
    
    # PR6.3: Structure HTML selon layout
    # NOTE: eco-columns est créé au niveau parent (_build_html_student)
    # Ici on gère juste les blocs fullwidth qui doivent sortir
    html = f"""
    <div class="exercise">
        <div class="exercise-header">
            <h2><span class="exercise-number">{ex_number}</span>{titre}</h2>
            {f'<p class="exercise-domain">{domaine}</p>' if domaine else ''}
        </div>
        
        <div class="questions">
    """
    
    # PR6.3: Si layout=eco et qu'il y a des blocs fullwidth, les sortir
    # NOTE: eco-columns est déjà ouvert au niveau parent (_build_html_student)
    if layout == "eco" and all_fullwidth_blocks:
        placeholder_idx = 0
        for q_html, q_fullwidth_blocks in question_html_parts:
            # Remplacer les placeholders par rien (on sortira les blocs après)
            for _ in q_fullwidth_blocks:
                q_html = q_html.replace(f'<!--FULLWIDTH_{placeholder_idx}-->', '')
                placeholder_idx += 1
            
            html += q_html
            
            # Si cette question a des blocs fullwidth, sortir de colonnes et insérer
            if q_fullwidth_blocks:
                html += '</div></div>'  # Fermer questions + exercise
                html += '</div>'  # Fermer eco-columns (parent dans _build_html_student)
                for block in q_fullwidth_blocks:
                    html += f'<div class="fullwidth-block">{block}</div>'
                html += '<div class="eco-columns">'  # Rouvrir eco-columns
                html += f'<div class="exercise"><div class="exercise-header"><h2><span class="exercise-number">{ex_number}</span>{titre}</h2></div><div class="questions">'  # Rouvrir exercise + questions (sans domaine car déjà affiché)
    
    else:
        # Layout classic ou pas de fullwidth: rendu normal
        for q_html, _ in question_html_parts:
            # Nettoyer les placeholders s'il y en a
            import re
            q_html = re.sub(r'<!--FULLWIDTH_\d+-->', '', q_html)
            html += q_html
        html += '</div></div>'  # Fermer questions + exercise
    
    return html


def _render_question(question: dict, q_number: int, include_solution: bool, is_student: bool, layout: str = "eco") -> tuple[str, list[str]]:
    """
    PR6.3: Rendu HTML d'une question avec extraction des blocs fullwidth.
    
    Args:
        question: Question du preview
        q_number: Numéro de la question
        include_solution: Inclure la solution
        is_student: Version élève (avec espace de réponse)
        layout: "eco" ou "classic"
    
    Returns:
        tuple: (html_text_with_placeholders, fullwidth_blocks)
        - html_text_with_placeholders: HTML avec placeholders pour les blocs fullwidth
        - fullwidth_blocks: Liste des blocs extraits (tableaux, figures)
    """
    enonce = question.get("enonce_brut", "")
    solution = question.get("solution_brut", "")
    data = question.get("data", {})
    
    # Nettoyer et formater l'énoncé
    enonce_html = _format_text(enonce)
    
    # Récupérer la figure HTML si présente
    figure_html = question.get("figure_html", "")
    
    # PR6.3: Extraire les blocs fullwidth (tableaux, figures) du HTML
    fullwidth_blocks = []
    if layout == "eco":
        # Extraire les tableaux/figures de l'énoncé
        enonce_html, blocks_from_enonce = extract_fullwidth_blocks(enonce_html)
        fullwidth_blocks.extend(blocks_from_enonce)
        
        # Extraire la figure si présente
        if figure_html:
            _, blocks_from_figure = extract_fullwidth_blocks(figure_html)
            if blocks_from_figure:
                fullwidth_blocks.extend(blocks_from_figure)
            else:
                # Si pas de bloc extrait, c'est peut-être déjà du HTML simple
                fullwidth_blocks.append(f'<div class="figure">{figure_html}</div>')
    
    html = f"""
    <div class="question">
        <div class="question-header">
            <strong class="instruction">Question {q_number}:</strong>
        </div>
        <div class="question-enonce">
            {enonce_html}
        </div>
    """
    
    # PR6.3: Si layout != eco, on garde l'ancien comportement (figure inline)
    if figure_html and layout != "eco":
        html += f"""
        <div class="figure exercise-figure">
            {figure_html}
        </div>
        """
    
    # Espace de réponse pour version élève
    if is_student:
        html += """
        <div class="answer-space">
            <p><em>Réponse:</em></p>
            <div></div>
        </div>
        """
    
    # Solution (uniquement pour corrigé) - PR6.1: Design "manuel scolaire"
    if include_solution:
        solution_html = _format_text(solution)
        # PR6.3: Extraire aussi les blocs fullwidth de la solution si eco
        if layout == "eco":
            solution_html, blocks_from_solution = extract_fullwidth_blocks(solution_html)
            fullwidth_blocks.extend(blocks_from_solution)
        
        html += f"""
        <div class="solution correction-box">
            <div class="correction-title">Solution</div>
            <div class="correction">
                {solution_html}
            </div>
        </div>
        """
    
    html += """
    </div>
    """
    
    return html, fullwidth_blocks


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


def extract_fullwidth_blocks(html: str) -> tuple[str, list[str]]:
    """
    PR6.3: Extrait les blocs "wide" (tableaux, figures) du HTML pour les sortir des colonnes.
    
    Détecte:
    - <table>...</table> (tableaux)
    - <svg>...</svg> (figures SVG)
    - <div class="figure">...</div> (figures wrappées)
    
    Args:
        html: HTML contenant potentiellement des tableaux/figures
    
    Returns:
        tuple: (html_with_placeholders, list_of_fullwidth_blocks)
        - html_with_placeholders: HTML avec placeholders <!--FULLWIDTH_0-->, <!--FULLWIDTH_1-->, etc.
        - list_of_fullwidth_blocks: Liste des blocs extraits (dans l'ordre)
    """
    import re
    
    fullwidth_blocks = []
    placeholder_counter = 0
    
    # Pattern pour capturer un tableau complet (non-gourmand)
    table_pattern = r'<table[^>]*>.*?</table>'
    
    def extract_table(match):
        nonlocal placeholder_counter
        table_html = match.group(0)
        # Vérifier si déjà dans un wrapper fullwidth
        if 'class="fullwidth' in table_html or 'class="fullwidth-block' in table_html:
            return match.group(0)
        placeholder = f'<!--FULLWIDTH_{placeholder_counter}-->'
        fullwidth_blocks.append(f'<div class="table-wrapper">{table_html}</div>')
        placeholder_counter += 1
        return placeholder
    
    html = re.sub(table_pattern, extract_table, html, flags=re.DOTALL | re.IGNORECASE)
    
    # Pattern pour capturer les figures SVG (non-gourmand)
    svg_pattern = r'<svg[^>]*>.*?</svg>'
    
    def extract_svg(match):
        nonlocal placeholder_counter
        svg_html = match.group(0)
        # Vérifier si déjà dans un wrapper
        if 'class="figure' in html[max(0, match.start()-100):match.start()] or \
           'class="fullwidth' in html[max(0, match.start()-100):match.start()]:
            return match.group(0)
        placeholder = f'<!--FULLWIDTH_{placeholder_counter}-->'
        fullwidth_blocks.append(f'<div class="figure">{svg_html}</div>')
        placeholder_counter += 1
        return placeholder
    
    html = re.sub(svg_pattern, extract_svg, html, flags=re.DOTALL | re.IGNORECASE)
    
    # Pattern pour capturer les div.figure (déjà wrappées)
    figure_div_pattern = r'<div[^>]*class=["\']figure[^"\']*["\'][^>]*>.*?</div>'
    
    def extract_figure_div(match):
        nonlocal placeholder_counter
        figure_html = match.group(0)
        # Vérifier si déjà dans fullwidth-block
        if 'class="fullwidth-block' in figure_html:
            return match.group(0)
        placeholder = f'<!--FULLWIDTH_{placeholder_counter}-->'
        fullwidth_blocks.append(figure_html)
        placeholder_counter += 1
        return placeholder
    
    html = re.sub(figure_div_pattern, extract_figure_div, html, flags=re.DOTALL | re.IGNORECASE)
    
    return html, fullwidth_blocks


def _get_base_css() -> str:
    """CSS de base pour tous les PDFs (layout classic - 1 colonne) - PR6.1: Anti-débordement + Design manuel scolaire"""
    return """
        /* --- Variables design "manuel scolaire" --- */
        :root {
            --font: "Inter", "Helvetica", Arial, sans-serif;
            --text: #111;
            --muted: #555;
            --rule: #ddd;
            --accent: #0b57d0;
        }
        
        @page {
            size: A4;
            margin: 2cm 1.5cm;
        }
        
        * {
            box-sizing: border-box;  /* PR6.1: Anti-débordement */
        }
        
        body {
            font-family: var(--font);
            font-size: 11pt;
            line-height: 1.5;
            color: var(--text);
        }
        
        p {
            margin: 0 0 6px 0;
        }
        
        h1, h2, h3 {
            margin: 0 0 8px 0;
            line-height: 1.15;
        }
        
        hr {
            border: 0;
            border-top: 1px solid var(--rule);
            margin: 10px 0;
        }
        
        /* --- Header "manuel scolaire" --- */
        .header {
            text-align: center;
            border-bottom: 2px solid var(--rule);
            padding-bottom: 8px;
            margin-bottom: 12px;
        }
        
        .sheet-title {
            font-size: 18pt;
            font-weight: 800;
            letter-spacing: -0.2px;
            color: #2c3e50;
            margin-bottom: 4px;
        }
        
        .sheet-meta {
            font-size: 10pt;
            color: var(--muted);
            margin-top: 2px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
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
        
        .content {
            /* Pas de colonnes pour classic */
        }
        
        /* PR6.1: Anti-débordement même en classic */
        .content img,
        .content svg,
        .content canvas {
            max-width: 100% !important;
            height: auto !important;
            display: block;
        }
        
        .content table {
            width: 100% !important;
            max-width: 100% !important;
            table-layout: fixed;
            border-collapse: collapse;
            margin: 6px 0;
        }
        
        .content th,
        .content td {
            border: 1px solid var(--rule);
            padding: 4px 6px;
            vertical-align: top;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        
        .content pre,
        .content code {
            white-space: pre-wrap;
            word-break: break-word;
            max-width: 100%;
        }
        
        /* --- Exercice "manuel scolaire" --- */
        /* PR6.2: Supprimer page-break-inside: avoid pour éviter "1 exo = 1 page" */
        .exercise {
            margin-bottom: 15px;  /* PR6.2: Réduire marge (était 30px) */
            page-break-inside: auto;  /* PR6.2: auto au lieu de avoid */
            break-inside: auto;
        }
        
        .exercise-header {
            background-color: #f5f5f5;
            padding: 10px;
            border-left: 4px solid #3498db;
            margin-bottom: 15px;
        }
        
        .exercise-number {
            display: inline-block;
            min-width: 24px;
            text-align: center;
            font-weight: 800;
            font-size: 11pt;
            border: 1px solid var(--rule);
            border-radius: 6px;
            padding: 2px 8px;
            margin-right: 8px;
        }
        
        .exercise-header h2 {
            color: #2c3e50;
            font-size: 14pt;
            margin: 0 0 5px 0;
        }
        
        .exercise-title {
            font-weight: 750;
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
            margin-bottom: 12px;  /* PR6.2: Réduire marge (était 20px) */
            page-break-inside: auto;  /* PR6.2: auto au lieu de avoid */
            break-inside: auto;
        }
        
        .question-header {
            color: #2c3e50;
            margin-bottom: 5px;
        }
        
        .instruction {
            font-weight: 700;
        }
        
        .question-enonce {
            margin-left: 20px;
            line-height: 1.6;
        }
        
        .answer-space {
            margin: 15px 0 15px 20px;
        }
        
        .answer-space div {
            height: 80px;
            border: 1px dashed #ccc;
        }
        
        /* --- Solution "manuel scolaire" --- */
        .solution {
            margin: 15px 0 15px 20px;
            padding: 10px;
            background-color: #f0f8ff;
            border-left: 4px solid #4CAF50;
        }
        
        .solution strong {
            color: #27ae60;
        }
        
        .correction-title {
            font-size: 14pt;
            font-weight: 850;
            margin-bottom: 8px;
        }
        
        .correction ol {
            margin: 6px 0 0 18px;
        }
        
        .correction li {
            margin: 0 0 6px 0;
        }
        
        .conclusion {
            margin-top: 6px;
            padding: 6px 8px;
            border-left: 3px solid var(--accent);
            background: #f5f8ff;
        }
        
        /* --- Figures et tableaux (anti-débordement) --- */
        /* PR6.2: Garder avoid uniquement pour les figures/tableaux (pas pour les exercices) */
        .figure,
        .table-wrapper,
        .exercise-figure,
        .fullwidth {
            break-inside: avoid;
            page-break-inside: avoid;
            max-width: 100%;
            margin: 10px 0;  /* PR6.2: Réduire marge (était 14px) */
            text-align: center;
        }
        
        .figure svg,
        .exercise-figure svg {
            display: block;
            max-width: 100% !important;
            height: auto !important;
        }
    """


def _get_eco_css() -> str:
    """CSS pour le layout eco (2 colonnes + compact) - PR6.1: Anti-débordement + Design manuel scolaire"""
    return """
        /* --- Variables design "manuel scolaire" --- */
        :root {
            --font: "Inter", "Helvetica", Arial, sans-serif;
            --text: #111;
            --muted: #555;
            --rule: #ddd;
            --accent: #0b57d0;
        }
        
        @page {
            size: A4;
            margin: 14mm 12mm;  /* Marges réduites mais raisonnables */
        }
        
        * {
            box-sizing: border-box;  /* PR6.1: Anti-débordement */
        }
        
        body {
            font-family: var(--font);
            font-size: 10pt;
            line-height: 1.35;
            color: var(--text);
        }
        
        p {
            margin: 0 0 6px 0;
        }
        
        h1, h2, h3 {
            margin: 0 0 8px 0;
            line-height: 1.15;
        }
        
        hr {
            border: 0;
            border-top: 1px solid var(--rule);
            margin: 10px 0;
        }
        
        /* --- Header "manuel scolaire" --- */
        .header {
            text-align: center;
            border-bottom: 2px solid var(--rule);
            padding-bottom: 8px;
            margin-bottom: 12px;
            /* PR6.3: Pas de column-span ici car header est avant eco-columns */
        }
        
        .sheet-title {
            font-size: 16pt;
            font-weight: 800;
            letter-spacing: -0.2px;
            color: #2c3e50;
            margin-bottom: 4px;
        }
        
        .sheet-meta {
            font-size: 9.5pt;
            color: var(--muted);
            margin-top: 2px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .metadata {
            font-size: 9pt;
            color: var(--muted);
            margin-top: 8px;
        }
        
        .metadata span {
            margin: 0 10px;
        }
        
        .student-info {
            margin-top: 10px;
            font-size: 9pt;
            text-align: left;
            /* PR6.3: Pas de column-span ici car student-info est avant eco-columns */
        }
        
        /* PR6.3: Layout 2 colonnes - structure refactorée pour éviter overlay */
        .content {
            /* Pas de column-count ici - on utilise .eco-columns pour les blocs texte */
        }
        
        /* PR6.3: Zone colonnes pour le texte (hors fullwidth) */
        .eco-columns {
            column-count: 2 !important;  /* PR6.3: Forcer 2 colonnes */
            column-gap: 10mm;
            column-fill: auto;
            width: 100%;
        }
        
        /* PR6.3: Bloc fullwidth HORS colonnes (évite overlay) */
        .fullwidth-block {
            width: 100%;
            margin: 8px 0 12px 0;
            break-inside: avoid;
            page-break-inside: avoid;
        }
        
        /* PR6.3: Tableaux lisibles dans fullwidth-block */
        .fullwidth-block table {
            width: 100% !important;
            border-collapse: collapse;
            table-layout: auto;  /* Pas fixed pour lisibilité */
            font-size: 11pt;     /* PR6.3: Taille lisible (>= 11pt) */
            margin: 0;
        }
        
        .fullwidth-block td,
        .fullwidth-block th {
            border: 1px solid #ddd;
            padding: 6px 8px;  /* PR6.3: Padding généreux */
            text-align: center;
            vertical-align: middle;
            white-space: nowrap;  /* PR6.3: Chiffres propres */
        }
        
        /* PR6.3: Figures dans fullwidth-block */
        .fullwidth-block .figure {
            width: 100%;
            text-align: center;
            margin: 0;
        }
        
        .fullwidth-block svg {
            max-width: 100% !important;
            height: auto !important;
            display: block;
            margin: 0 auto;
        }
        
        /* PR6.1: Anti-débordement général (safe) */
        .content img,
        .content svg,
        .content canvas,
        .eco-columns img,
        .eco-columns svg,
        .eco-columns canvas {
            max-width: 100% !important;
            height: auto !important;
            display: block;
        }
        
        /* PR6.3: Tableaux dans colonnes (petits tableaux qui restent) */
        .eco-columns table {
            width: 100% !important;
            max-width: 100% !important;
            table-layout: auto;
            border-collapse: collapse;
            margin: 6px 0;
            font-size: 10pt;
        }
        
        .eco-columns th,
        .eco-columns td {
            border: 1px solid var(--rule);
            padding: 3px 5px;
            vertical-align: top;
            overflow-wrap: anywhere;
            word-break: break-word;
        }
        
        .content pre,
        .content code,
        .eco-columns pre,
        .eco-columns code {
            white-space: pre-wrap;
            word-break: break-word;
            max-width: 100%;
        }
        
        /* --- Exercice "manuel scolaire" --- */
        .exercise {
            margin-bottom: 10px;
            page-break-inside: avoid;
            break-inside: avoid;
            display: inline-block;
            width: 100%;
        }
        
        .exercise-header {
            background-color: #f5f5f5;
            padding: 8px;
            border-left: 3px solid #3498db;
            margin-bottom: 12px;
        }
        
        .exercise-number {
            display: inline-block;
            min-width: 22px;
            text-align: center;
            font-weight: 800;
            font-size: 10pt;
            border: 1px solid var(--rule);
            border-radius: 6px;
            padding: 2px 6px;
            margin-right: 6px;
        }
        
        .exercise-header h2 {
            color: #2c3e50;
            font-size: 12pt;
            margin: 0 0 4px 0;
        }
        
        .exercise-title {
            font-weight: 750;
            color: #34495e;
            margin: 4px 0;
            font-size: 10pt;
        }
        
        .exercise-domain {
            font-size: 8pt;
            color: #7f8c8d;
            font-style: italic;
            margin: 0;
        }
        
        .questions {
            padding-left: 8px;
        }
        
        .question {
            margin-bottom: 15px;
            page-break-inside: avoid;
            break-inside: avoid;
        }
        
        .question-header {
            color: #2c3e50;
            margin-bottom: 4px;
            font-size: 10pt;
        }
        
        .instruction {
            font-weight: 700;
        }
        
        .question-enonce {
            margin-left: 15px;
            line-height: 1.5;
            font-size: 10pt;
        }
        
        .answer-space {
            margin: 10px 0 10px 15px;
        }
        
        .answer-space div {
            height: 60px;
            border: 1px dashed #ccc;
        }
        
        /* --- Figures et tableaux (anti-débordement) --- */
        .figure,
        .table-wrapper,
        .exercise-figure {
            break-inside: avoid;
            page-break-inside: avoid;
            max-width: 100%;
            margin: 10px 0;
            text-align: center;
        }
        
        .figure svg,
        .exercise-figure svg {
            display: block;
            max-width: 100% !important;
            height: auto !important;
        }
        
        /* --- Solution (éviter les trous - break-inside auto) --- */
        .solution,
        .correction-box {
            break-inside: auto !important;  /* PR6.2: Forcer auto pour éviter "1 exo = 1 page" */
            page-break-inside: auto !important;
            margin: 8px 0 8px 15px;  /* PR6.2: Réduire marge */
            padding: 8px;
            background-color: #f0f8ff;
            border-left: 3px solid #4CAF50;
            font-size: 10pt;  /* PR6.2: Taille minimale lisible (était 9pt) */
        }
        
        .solution strong {
            color: #27ae60;
        }
        
        /* --- Optimisations typographiques --- */
        .question-enonce {
            orphans: 3;
            widows: 3;
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
