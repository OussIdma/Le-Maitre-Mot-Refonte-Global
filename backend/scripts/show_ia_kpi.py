#!/usr/bin/env python3
"""
Script de visualisation des KPI IA
Usage : python scripts/show_ia_kpi.py [--last N]
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.ia_monitoring_service import ia_monitoring


def main():
    parser = argparse.ArgumentParser(description="Afficher les KPI du pipeline IA")
    parser.add_argument(
        "--last",
        type=int,
        default=None,
        help="Nombre de dernières générations à analyser (défaut : toutes)"
    )
    parser.add_argument(
        "--alerts",
        action="store_true",
        help="Vérifier uniquement les alertes"
    )
    
    args = parser.parse_args()
    
    if args.alerts:
        # Mode alertes uniquement
        alerts = ia_monitoring.check_alerts(last_n=args.last or 100)
        
        if alerts:
            print("\n🚨 ALERTES DÉTECTÉES :")
            for alert in alerts:
                print(f"  {alert}")
            print()
            sys.exit(1)  # Exit code 1 si alertes
        else:
            print("\n✅ Aucune alerte détectée\n")
            sys.exit(0)
    
    else:
        # Mode rapport complet
        ia_monitoring.print_kpi_report(last_n=args.last)


if __name__ == "__main__":
    main()
