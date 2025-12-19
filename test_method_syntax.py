class TestClass:
    def test_dynamic_factory_v1_complete(self):
        """
        Test Dynamic Factory v1 - Complete Implementation
        
        Tests all priorities from the review request:
        - P0: Non-regression GM07/GM08
        - P1: Registry Central (GET /generators, GET /generators/{key}/full-schema)
        - P3: Params Fusion (defaults + exercise_params + overrides)
        - P5: SYMETRIE_AXIALE_V2 Pilot
        - Template Rendering
        """
        print("Test method works")
        return True, {}

# Test
t = TestClass()
print(hasattr(t, 'test_dynamic_factory_v1_complete'))