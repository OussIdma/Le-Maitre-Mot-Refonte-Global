/**
 * API Admin avec gestion robuste des erreurs (P0.1)
 * - Timeouts configurables
 * - Retry automatique
 * - Gestion des erreurs avec messages explicites
 */

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const DEFAULT_TIMEOUT = 15000; // 15 secondes

/**
 * Effectue un appel API avec timeout et gestion d'erreurs
 */
export async function apiCall(endpoint, options = {}) {
  const {
    method = 'GET',
    body = null,
    timeout = DEFAULT_TIMEOUT,
    retries = 1
  } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  const fetchOptions = {
    method,
    headers: { 'Content-Type': 'application/json' },
    signal: controller.signal
  };

  if (body && method !== 'GET') {
    fetchOptions.body = JSON.stringify(body);
  }

  let lastError = null;
  
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const response = await fetch(`${BACKEND_URL}${endpoint}`, fetchOptions);
      clearTimeout(timeoutId);

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail?.message || data.detail || `Erreur ${response.status}`);
      }

      return { success: true, data };
    } catch (error) {
      lastError = error;
      
      if (error.name === 'AbortError') {
        lastError = new Error('La requête a expiré. Vérifiez votre connexion et réessayez.');
      }
      
      // Si on a encore des retries, attendre un peu avant de réessayer
      if (attempt < retries) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  clearTimeout(timeoutId);
  return { success: false, error: lastError?.message || 'Erreur inconnue' };
}

/**
 * Récupère le schéma d'un générateur (essaie le nouveau endpoint Factory, puis legacy)
 */
export async function fetchGeneratorSchema(generatorKey) {
  // Essayer d'abord le nouveau endpoint Factory
  const factoryResult = await apiCall(`/api/v1/exercises/generators/${generatorKey}/full-schema`);
  if (factoryResult.success) {
    // Adapter la réponse Factory au format legacy pour compatibilité
    const data = factoryResult.data;
    return {
      success: true,
      data: {
        generator_key: data.generator_key,
        label: data.meta?.label || data.generator_key,
        description: data.meta?.description || '',
        niveau: data.meta?.niveaux?.[0] || '6e',
        variables: data.schema || [],
        svg_modes: data.meta?.svg_mode ? [data.meta.svg_mode] : ['AUTO', 'CUSTOM'],
        supports_double_svg: data.meta?.supports_double_svg ?? true,
        pedagogical_tips: data.meta?.pedagogical_tips,
        template_example_enonce: data.presets?.[0]?.params?.enonce_template || '',
        template_example_solution: data.presets?.[0]?.params?.solution_template || '',
        presets: data.presets || [],
        defaults: data.defaults || {}
      }
    };
  }
  
  // Fallback sur l'ancien endpoint
  return apiCall(`/api/v1/exercises/generators/${generatorKey}/schema`);
}

/**
 * Liste tous les générateurs
 */
export async function fetchGeneratorsList() {
  return apiCall('/api/v1/exercises/generators/list');
}

/**
 * Preview d'un exercice dynamique
 */
export async function previewDynamicExercise(data) {
  return apiCall('/api/admin/exercises/preview-dynamic', {
    method: 'POST',
    body: data,
    timeout: 20000 // Preview peut être plus long
  });
}

/**
 * Valide un template
 */
export async function validateTemplate(template, generatorKey) {
  return apiCall(`/api/admin/exercises/validate-template?template=${encodeURIComponent(template)}&generator_key=${generatorKey}`, {
    method: 'POST'
  });
}

export default {
  apiCall,
  fetchGeneratorSchema,
  fetchGeneratorsList,
  previewDynamicExercise,
  validateTemplate
};
