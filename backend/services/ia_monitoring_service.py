"""
Service de Monitoring IA
Suivi des métriques de qualité du pipeline IA

KPI suivis :
- Taux d'acceptation IA (IA validée / Total)
- Taux de rejet IA (IA rejetée → fallback / Total)
- Causes principales de rejet
- Temps de génération
- Coût estimé API
"""

import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class IAGenerationStats:
    """Statistiques d'une génération IA"""
    timestamp: str
    type_exercice: str
    niveau: str
    chapitre: str
    ia_utilisee: bool  # True si IA appelée (pas bypass)
    ia_acceptee: bool  # True si validation IA réussie
    fallback_utilise: bool  # True si fallback utilisé
    cause_rejet: Optional[str]  # Cause du rejet si applicable
    temps_generation_ms: Optional[float]  # Temps en millisecondes


class IAMonitoringService:
    """Service de monitoring du pipeline IA"""
    
    def __init__(self, log_file: str = "/app/backend/logs/ia_monitoring.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Stats en mémoire (session)
        self.session_stats: List[IAGenerationStats] = []
    
    def log_generation(
        self,
        type_exercice: str,
        niveau: str,
        chapitre: str,
        ia_utilisee: bool,
        ia_acceptee: bool,
        fallback_utilise: bool,
        cause_rejet: Optional[str] = None,
        temps_generation_ms: Optional[float] = None
    ):
        """Enregistrer une génération"""
        
        stats = IAGenerationStats(
            timestamp=datetime.now().isoformat(),
            type_exercice=type_exercice,
            niveau=niveau,
            chapitre=chapitre,
            ia_utilisee=ia_utilisee,
            ia_acceptee=ia_acceptee,
            fallback_utilise=fallback_utilise,
            cause_rejet=cause_rejet,
            temps_generation_ms=temps_generation_ms
        )
        
        # Ajouter aux stats session
        self.session_stats.append(stats)
        
        # Écrire dans le fichier de log
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(asdict(stats)) + "\n")
        except Exception as e:
            logger.error(f"Erreur écriture log monitoring : {e}")
    
    def get_kpi_summary(self, last_n: Optional[int] = None) -> Dict:
        """
        Calculer les KPI depuis les logs
        
        Args:
            last_n: Nombre de dernières entrées à considérer (None = toutes)
        
        Returns:
            Dict avec les KPI
        """
        
        # Lire les logs
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()
            
            if last_n:
                lines = lines[-last_n:]
            
            stats = [json.loads(line) for line in lines]
        except Exception as e:
            logger.error(f"Erreur lecture logs : {e}")
            stats = []
        
        if not stats:
            return {
                "total": 0,
                "message": "Aucune donnée disponible"
            }
        
        # Calculer KPI
        total = len(stats)
        ia_utilisee = sum(1 for s in stats if s["ia_utilisee"])
        ia_acceptee = sum(1 for s in stats if s["ia_acceptee"])
        ia_rejetee = sum(1 for s in stats if s["ia_utilisee"] and not s["ia_acceptee"])
        fallback_utilise = sum(1 for s in stats if s["fallback_utilise"])
        
        # Causes de rejet
        causes_rejet = {}
        for s in stats:
            if s["cause_rejet"]:
                cause = s["cause_rejet"]
                causes_rejet[cause] = causes_rejet.get(cause, 0) + 1
        
        # Répartition par type
        types_stats = {}
        for s in stats:
            type_ex = s["type_exercice"]
            if type_ex not in types_stats:
                types_stats[type_ex] = {
                    "total": 0,
                    "ia_acceptee": 0,
                    "ia_rejetee": 0,
                    "fallback": 0
                }
            
            types_stats[type_ex]["total"] += 1
            if s["ia_acceptee"]:
                types_stats[type_ex]["ia_acceptee"] += 1
            elif s["ia_utilisee"] and not s["ia_acceptee"]:
                types_stats[type_ex]["ia_rejetee"] += 1
            if s["fallback_utilise"]:
                types_stats[type_ex]["fallback"] += 1
        
        # Temps moyen
        temps_list = [s["temps_generation_ms"] for s in stats if s["temps_generation_ms"]]
        temps_moyen = sum(temps_list) / len(temps_list) if temps_list else None
        
        return {
            "periode": {
                "debut": stats[0]["timestamp"] if stats else None,
                "fin": stats[-1]["timestamp"] if stats else None,
                "nb_generations": total
            },
            "kpi_globaux": {
                "total_generations": total,
                "ia_utilisee": ia_utilisee,
                "ia_acceptee": ia_acceptee,
                "ia_rejetee": ia_rejetee,
                "fallback_utilise": fallback_utilise,
                "taux_acceptation_ia": round(ia_acceptee / ia_utilisee * 100, 1) if ia_utilisee > 0 else 0,
                "taux_rejet_ia": round(ia_rejetee / ia_utilisee * 100, 1) if ia_utilisee > 0 else 0,
                "taux_fallback": round(fallback_utilise / total * 100, 1)
            },
            "causes_rejet": causes_rejet,
            "par_type_exercice": types_stats,
            "performance": {
                "temps_moyen_ms": round(temps_moyen, 2) if temps_moyen else None
            }
        }
    
    def print_kpi_report(self, last_n: Optional[int] = None):
        """Afficher un rapport KPI lisible"""
        
        kpi = self.get_kpi_summary(last_n)
        
        print("\n" + "="*80)
        print("📊 RAPPORT KPI - PIPELINE IA")
        print("="*80)
        
        if kpi.get("total") == 0:
            print("Aucune donnée disponible")
            return
        
        # Période
        print(f"\n🕒 Période :")
        print(f"  - Début : {kpi['periode']['debut']}")
        print(f"  - Fin : {kpi['periode']['fin']}")
        print(f"  - Nb générations : {kpi['periode']['nb_generations']}")
        
        # KPI globaux
        print(f"\n📈 KPI Globaux :")
        kpi_glob = kpi['kpi_globaux']
        print(f"  - Total générations : {kpi_glob['total_generations']}")
        print(f"  - IA utilisée : {kpi_glob['ia_utilisee']} ({kpi_glob['ia_utilisee']/kpi_glob['total_generations']*100:.1f}%)")
        print(f"  - IA acceptée : {kpi_glob['ia_acceptee']} (taux : {kpi_glob['taux_acceptation_ia']}%)")
        print(f"  - IA rejetée : {kpi_glob['ia_rejetee']} (taux : {kpi_glob['taux_rejet_ia']}%)")
        print(f"  - Fallback utilisé : {kpi_glob['fallback_utilise']} (taux : {kpi_glob['taux_fallback']}%)")
        
        # Causes de rejet
        if kpi['causes_rejet']:
            print(f"\n⚠️ Causes de rejet IA :")
            for cause, count in sorted(kpi['causes_rejet'].items(), key=lambda x: x[1], reverse=True):
                print(f"  - {cause} : {count}")
        
        # Par type
        print(f"\n📚 Par type d'exercice :")
        for type_ex, stats in kpi['par_type_exercice'].items():
            taux_accept = (stats['ia_acceptee'] / stats['total'] * 100) if stats['total'] > 0 else 0
            print(f"  - {type_ex} : {stats['total']} générations, {taux_accept:.1f}% acceptées")
        
        # Performance
        if kpi['performance']['temps_moyen_ms']:
            print(f"\n⏱️ Performance :")
            print(f"  - Temps moyen génération : {kpi['performance']['temps_moyen_ms']:.0f} ms")
        
        print("\n" + "="*80 + "\n")
    
    def get_alert_thresholds(self) -> Dict:
        """Définir les seuils d'alerte"""
        return {
            "taux_rejet_ia_max": 20,  # Alerte si > 20% de rejet
            "taux_fallback_max": 30,  # Alerte si > 30% de fallback
            "temps_generation_max_ms": 5000  # Alerte si > 5s
        }
    
    def check_alerts(self, last_n: int = 100) -> List[str]:
        """Vérifier si des seuils d'alerte sont dépassés"""
        
        kpi = self.get_kpi_summary(last_n)
        thresholds = self.get_alert_thresholds()
        alerts = []
        
        if kpi.get("total") == 0:
            return alerts
        
        kpi_glob = kpi['kpi_globaux']
        
        # Alerte taux rejet IA
        if kpi_glob['taux_rejet_ia'] > thresholds['taux_rejet_ia_max']:
            alerts.append(
                f"🚨 Taux de rejet IA élevé : {kpi_glob['taux_rejet_ia']}% "
                f"(seuil : {thresholds['taux_rejet_ia_max']}%)"
            )
        
        # Alerte taux fallback
        if kpi_glob['taux_fallback'] > thresholds['taux_fallback_max']:
            alerts.append(
                f"⚠️ Taux de fallback élevé : {kpi_glob['taux_fallback']}% "
                f"(seuil : {thresholds['taux_fallback_max']}%)"
            )
        
        # Alerte temps génération
        temps_moyen = kpi['performance']['temps_moyen_ms']
        if temps_moyen and temps_moyen > thresholds['temps_generation_max_ms']:
            alerts.append(
                f"⏱️ Temps de génération élevé : {temps_moyen:.0f} ms "
                f"(seuil : {thresholds['temps_generation_max_ms']} ms)"
            )
        
        return alerts


# Instance globale
ia_monitoring = IAMonitoringService()
