# CLASSIFICATION DES GÉNÉRATEURS DYNAMIQUES

**Date de génération :** 2025-12-24T18:56:26.332551
**Total tests :** 17
**✅ Pass :** 17
**❌ Fail :** 0

---

## 📊 RÉSUMÉ PAR CATÉGORIE

- 🟢 **GOLD :** 6 générateur(s)
- 🟠 **AMÉLIORABLE :** 0 générateur(s)
- 🔴 **DÉSACTIVÉ :** 0 générateur(s)

---

## 🟢 GOLD

Générateurs 100% fiables, utilisables en production immédiatement.

- **CALCUL_NOMBRES_V1** (v1.0.0)
- **RAISONNEMENT_MULTIPLICATIF_V1** (v1.0.0)
- **SIMPLIFICATION_FRACTIONS_V1** (v1.0.0)
- **SIMPLIFICATION_FRACTIONS_V2** (v2.0.0)
- **SYMETRIE_AXIALE_V2** (v2.0.0)
- **THALES_V2** (v2.0.0)

---

## 🟠 AMÉLIORABLE

Générateurs fonctionnels mais avec des problèmes localisés. Fix estimable.

*Aucun générateur AMÉLIORABLE pour le moment.*

---

## 🔴 DÉSACTIVÉ

Générateurs avec échecs récurrents, monkeypatch RNG, ou templates inline non maîtrisés.

⚠️ **Ces générateurs ne sont PAS visibles dans l'UI et ne peuvent PAS être utilisés.**

*Aucun générateur DÉSACTIVÉ pour le moment.*

---

## 📝 NOTES

Cette classification est générée automatiquement à partir des résultats de test.
Pour mettre à jour :

```bash
python backend/scripts/test_dynamic_generators.py --output test_results.json
python backend/scripts/classify_generators.py --input test_results.json --output docs/CLASSIFICATION_GENERATEURS.md
```
