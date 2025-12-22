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

      // Parsing défensif : vérifier Content-Type avant JSON.parse
      const contentType = response.headers.get('content-type') || '';
      let data = null;
      
      if (contentType.includes('application/json')) {
        try {
          const text = await response.text();
          data = JSON.parse(text);
        } catch (jsonError) {
          // Si JSON.parse échoue malgré Content-Type JSON, traiter comme erreur
          lastError = {
            error_code: "non_json_response",
            message: `Réponse invalide du serveur (JSON attendu): ${jsonError.message}`,
            details: null
          };
          throw new Error(lastError.message);
        }
      } else {
        // Si ce n'est pas du JSON, lire le texte et construire une erreur structurée
        const text = await response.text();
        lastError = {
          error_code: "non_json_response",
          message: `Réponse non-JSON du serveur (Content-Type: ${contentType || 'non spécifié'}): ${text.slice(0, 200)}...`,
          details: text
        };
        throw new Error(lastError.message);
      }

      if (!response.ok) {
        // Construire une erreur structurée depuis la réponse
        const errorMessage = data.message || data.detail?.message || data.detail || `Erreur ${response.status}`;
        lastError = {
          error_code: data.error_code || data.error || "http_error",
          message: errorMessage,
          details: data
        };
        throw new Error(errorMessage);
      }

      return { success: true, data };
    } catch (error) {
      // Si lastError a déjà été défini (non-JSON ou erreur structurée), l'utiliser
      if (!lastError || (error.name !== 'AbortError' && !lastError.error_code)) {
        if (error.name === 'AbortError') {
          lastError = {
            error_code: "timeout",
            message: 'La requête a expiré. Vérifiez votre connexion et réessayez.',
            details: null
          };
        } else {
          lastError = {
            error_code: "network_error",
            message: error.message || 'Erreur inconnue lors de la requête.',
            details: null
          };
        }
      }
      
      // Si on a encore des retries, attendre un peu avant de réessayer
      if (attempt < retries) {
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  clearTimeout(timeoutId);
  
  // Retourner une erreur structurée
  return { 
    success: false, 
    error: lastError?.message || 'Erreur inconnue',
    error_details: lastError || { error_code: "unknown_error", message: 'Erreur inconnue' }
  };
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
 * Crée un exercice pour un chapitre donné (CRUD admin)
 */
export async function createChapterExercise(chapterCode, exercisePayload) {
  return apiCall(`/api/admin/chapters/${chapterCode}/exercises`, {
    method: 'POST',
    body: exercisePayload,
    timeout: DEFAULT_TIMEOUT,
  });
}

/**
 * Met à jour un exercice existant (CRUD admin)
 */
export async function updateChapterExercise(chapterCode, exerciseId, exercisePayload) {
  return apiCall(`/api/admin/chapters/${chapterCode}/exercises/${exerciseId}`, {
    method: 'PUT',
    body: exercisePayload,
    timeout: DEFAULT_TIMEOUT,
  });
}

/**
 * Supprime un exercice existant (CRUD admin)
 */
export async function deleteChapterExercise(chapterCode, exerciseId) {
  return apiCall(`/api/admin/chapters/${chapterCode}/exercises/${exerciseId}`, {
    method: 'DELETE',
    timeout: DEFAULT_TIMEOUT,
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
  validateTemplate,
  createChapterExercise,
  updateChapterExercise,
  deleteChapterExercise,
};
