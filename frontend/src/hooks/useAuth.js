/**
 * useAuth - Hook réactif pour gérer l'authentification
 * 
 * Écoute les changements d'auth via:
 * - Événement custom "lmm:auth-changed"
 * - Événement "storage" (multi-tabs)
 * - Mise à jour automatique quand localStorage change
 */

import { useState, useEffect } from 'react';

/**
 * Lit l'état d'authentification depuis localStorage
 */
const getAuthFromStorage = () => {
  const sessionToken = localStorage.getItem('lemaitremot_session_token');
  const userEmail = localStorage.getItem('lemaitremot_user_email');
  const loginMethod = localStorage.getItem('lemaitremot_login_method');
  
  const isPro = !!(sessionToken && userEmail && loginMethod === 'session');
  
  return {
    sessionToken: sessionToken || null,
    userEmail: userEmail || null,
    isPro
  };
};

/**
 * Hook useAuth - État d'authentification réactif
 * 
 * @returns {{sessionToken: string|null, userEmail: string|null, isPro: boolean}}
 */
export const useAuth = () => {
  const [authState, setAuthState] = useState(getAuthFromStorage);
  
  useEffect(() => {
    // Fonction pour mettre à jour l'état
    const updateAuthState = () => {
      const newState = getAuthFromStorage();
      setAuthState(newState);
    };
    
    // Écouter l'événement custom "lmm:auth-changed"
    const handleAuthChanged = () => {
      console.log('[useAuth] Événement lmm:auth-changed détecté');
      updateAuthState();
    };
    
    // Écouter l'événement "storage" (multi-tabs)
    const handleStorageChange = (e) => {
      // Vérifier que c'est bien un changement lié à l'auth
      if (
        e.key === 'lemaitremot_session_token' ||
        e.key === 'lemaitremot_user_email' ||
        e.key === 'lemaitremot_login_method' ||
        e.key === null // null = tous les keys ont changé (clear)
      ) {
        console.log('[useAuth] Changement localStorage détecté:', e.key);
        updateAuthState();
      }
    };
    
    // Ajouter les listeners
    window.addEventListener('lmm:auth-changed', handleAuthChanged);
    window.addEventListener('storage', handleStorageChange);
    
    // Nettoyage
    return () => {
      window.removeEventListener('lmm:auth-changed', handleAuthChanged);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, []);
  
  return authState;
};



