#!/usr/bin/env python3
"""
Audit du mapping chapitre → générateur
Identifie les chapitres du curriculum sans générateur
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from curriculum_data import CURRICULUM_DATA
import re

# Lire le mapping depuis math_generation_service.py
with open('/app/backend/services/math_generation_service.py', 'r') as f:
    content = f.read()

# Extraire les chapitres du mapping
mapping_pattern = r'"([^"]+)":\s*\[MathExerciseType\.'
mapped_chapters = set(re.findall(mapping_pattern, content))

# Récupérer tous les chapitres du curriculum
all_chapters = set()
chapters_by_level = {}

for matiere, data in CURRICULUM_DATA.items():
    if matiere == "Mathématiques" and "chapters" in data:
        for niveau, thematiques in data["chapters"].items():
            if niveau not in chapters_by_level:
                chapters_by_level[niveau] = []
            
            for thematique, chapitres in thematiques.items():
                for chapitre in chapitres:
                    all_chapters.add(chapitre)
                    chapters_by_level[niveau].append(chapitre)

# Identifier les manquants
missing_chapters = all_chapters - mapped_chapters

print("\n" + "="*80)
print("🔍 AUDIT MAPPING CHAPITRE → GÉNÉRATEUR")
print("="*80 + "\n")

print(f"📊 Statistiques :")
print(f"  - Chapitres dans curriculum : {len(all_chapters)}")
print(f"  - Chapitres mappés : {len(mapped_chapters)}")
print(f"  - Chapitres MANQUANTS : {len(missing_chapters)}")
print(f"  - Taux de couverture : {(len(all_chapters) - len(missing_chapters)) / len(all_chapters) * 100:.1f}%")

if missing_chapters:
    print("\n" + "="*80)
    print("❌ CHAPITRES SANS GÉNÉRATEUR (BUGS CRITIQUES)")
    print("="*80 + "\n")
    
    for niveau in ["6e", "5e", "4e", "3e"]:
        missing_in_level = [ch for ch in chapters_by_level.get(niveau, []) if ch in missing_chapters]
        
        if missing_in_level:
            print(f"\n📘 {niveau} :")
            for chapitre in missing_in_level:
                print(f"  ❌ {chapitre}")

    print("\n" + "="*80)
    print("⚠️  IMPACT : Utilisateurs obtiennent des exercices ALÉATOIRES")
    print("="*80 + "\n")

else:
    print("\n✅ Tous les chapitres sont mappés !\n")
