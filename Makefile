# Makefile pour Le Maître Mot

.PHONY: generators:check generators:update test:generators

# Vérifier que les générateurs sont à jour (mode check)
generators:check:
	@echo "🔍 Vérification des générateurs..."
	@python backend/scripts/run_generators_quality_gate.py --check

# Mettre à jour les générateurs désactivés
generators:update:
	@echo "🚀 Mise à jour des générateurs..."
	@python backend/scripts/run_generators_quality_gate.py

# Exécuter les tests des générateurs désactivés
test:generators:
	@echo "🧪 Tests des générateurs désactivés..."
	@pytest backend/tests/test_generator_factory_disabled.py -v




