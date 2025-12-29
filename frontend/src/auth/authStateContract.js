/**
 * Contrat d'état d'authentification
 * 
 * Définit les règles de validation pour l'état d'authentification
 * et évite la duplication de logique de vérification
 */

/**
 * Vérifie si un utilisateur est considéré comme connecté
 * 
 * @param {Object} state - État d'authentification
 * @param {string|null} state.sessionToken - Token de session
 * @param {string|null} state.userEmail - Email de l'utilisateur
 * @returns {boolean} true si l'utilisateur est connecté
 */
export function isLoggedIn({ sessionToken, userEmail }) {
  return Boolean(sessionToken && userEmail && String(userEmail).trim().length > 0);
}

/**
 * Normalise un email (trim + validation)
 * 
 * @param {string|null|undefined} email - Email à normaliser
 * @returns {string|null} Email normalisé ou null si invalide
 */
export function normalizeEmail(email) {
  return email?.trim() || null;
}


