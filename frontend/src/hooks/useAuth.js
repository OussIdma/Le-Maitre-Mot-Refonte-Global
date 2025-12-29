/**
 * useAuth - Hook réactif pour gérer l'authentification
 * 
 * Écoute les changements d'auth via:
 * - Événement custom "lmm:auth-changed"
 * - Événement "storage" (multi-tabs)
 * - Mise à jour automatique quand localStorage change
 * - Appel API /auth/me pour récupérer is_pro correctement
 */

import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Lit l'état d'authentification depuis localStorage
 */
const getAuthFromStorage = () => {
  const sessionToken = localStorage.getItem('lemaitremot_session_token');
  const userEmail = localStorage.getItem('lemaitremot_user_email');
  const loginMethod = localStorage.getItem('lemaitremot_login_method');
  
  return {
    sessionToken: sessionToken || null,
    userEmail: userEmail || null,
    loginMethod: loginMethod || null,
    isPro: false, // Sera mis à jour par l'appel API
    isLoading: true // Indique si on est en train de charger is_pro
  };
};

/**
 * Hook useAuth - État d'authentification réactif
 * 
 * @returns {{sessionToken: string|null, userEmail: string|null, isPro: boolean, isLoading: boolean}}
 */
export const useAuth = () => {
  const [authState, setAuthState] = useState(getAuthFromStorage);
  // P0: Ref pour éviter les boucles infinies lors du nettoyage
  const isClearingRef = useRef(false);
  
  // Fonction pour récupérer is_pro depuis l'API
  const fetchUserStatus = async (sessionToken) => {
    if (!sessionToken) {
      setAuthState(prev => ({ ...prev, isPro: false, isLoading: false, userEmail: null }));
      return;
    }
    
    try {
      const response = await axios.get(`${API}/auth/me`, {
        headers: {
          'X-Session-Token': sessionToken
        },
        withCredentials: true
      });
      
      // P0: Token valide - mettre à jour l'état avec les données de l'API
      const email = response.data.email || null;
      const isPro = response.data.is_pro === true;
      
      // Mettre à jour localStorage avec l'email de l'API (au cas où il aurait changé)
      if (email) {
        localStorage.setItem('lemaitremot_user_email', email);
      }
      
      setAuthState({
        sessionToken: sessionToken,
        userEmail: email,
        loginMethod: localStorage.getItem('lemaitremot_login_method') || null,
        isPro: isPro,
        isLoading: false
      });
      
      console.log('[useAuth] ✅ Token valide - utilisateur connecté:', email, 'isPro:', isPro);
    } catch (error) {
      // P0: Si 401, le token est invalide - nettoyer COMPLÈTEMENT le localStorage
      if (error.response?.status === 401) {
        console.log('[useAuth] ⚠️ Token invalide (401) - nettoyage COMPLET localStorage');
        
        // P0: Nettoyer TOUTES les clés auth du localStorage (y compris variantes possibles)
        localStorage.removeItem('lemaitremot_session_token');
        localStorage.removeItem('lemaitremot_user_email');
        localStorage.removeItem('lemaitremot_login_method');
        // Nettoyer aussi d'éventuelles variantes de clés
        localStorage.removeItem('userEmail');
        localStorage.removeItem('email');
        localStorage.removeItem('auth_email');
        localStorage.removeItem('session_token');
        
        // P0: Réinitialiser l'état AVANT de dispatcher l'événement
        // S'assurer que TOUT est à null/false
        const clearedState = {
          sessionToken: null,
          userEmail: null,
          loginMethod: null,
          isPro: false,
          isLoading: false
        };
        
        // P0: Marquer qu'on est en train de nettoyer
        isClearingRef.current = true;
        
        // P0: Forcer l'état immédiatement (synchronisation)
        setAuthState(clearedState);
        
        // P0: Dispatcher l'événement APRÈS avoir nettoyé l'état
        // Cela garantit que les autres composants verront l'état nettoyé
        setTimeout(() => {
          isClearingRef.current = false;
          window.dispatchEvent(new Event('lmm:auth-changed'));
        }, 50);
        
        console.log('[useAuth] ✅ État complètement réinitialisé après 401');
      } else {
        // En cas d'erreur réseau ou autre, considérer comme non authentifié
        console.error('[useAuth] Erreur lors de la récupération du statut:', error);
        setAuthState(prev => ({ ...prev, isPro: false, isLoading: false }));
      }
    }
  };
  
  useEffect(() => {
    // Fonction pour mettre à jour l'état
    const updateAuthState = async () => {
      // P0: Si on est en train de nettoyer, ne pas relire depuis localStorage
      if (isClearingRef.current) {
        console.log('[useAuth] Nettoyage en cours - skip updateAuthState');
        return;
      }
      
      const newState = getAuthFromStorage();
      
      // P0: Si on a un session token, toujours vérifier sa validité via l'API
      if (newState.sessionToken) {
        // Ne pas mettre à jour l'état avant la vérification API
        // On garde isLoading: true pour éviter d'afficher un état incohérent
        await fetchUserStatus(newState.sessionToken);
      } else {
        // Pas de token - utilisateur déconnecté
        // P0: S'assurer que l'état est complètement nettoyé
        setAuthState({
          sessionToken: null,
          userEmail: null,
          loginMethod: null,
          isPro: false,
          isLoading: false
        });
      }
    };
    
    // P0: Initialiser l'état au montage - toujours vérifier le token si présent
    updateAuthState();
    
    // Écouter l'événement custom "lmm:auth-changed"
    const handleAuthChanged = () => {
      console.log('[useAuth] Événement lmm:auth-changed détecté');
      // P0: Vérifier si le localStorage a été nettoyé
      const token = localStorage.getItem('lemaitremot_session_token');
      if (!token) {
        // P0: Si pas de token, forcer l'état à null (ne pas relire depuis localStorage)
        console.log('[useAuth] Pas de token après auth-changed - état forcé à null');
        isClearingRef.current = true;
        setAuthState({
          sessionToken: null,
          userEmail: null,
          loginMethod: null,
          isPro: false,
          isLoading: false
        });
        setTimeout(() => { isClearingRef.current = false; }, 100);
      } else {
        updateAuthState();
      }
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



