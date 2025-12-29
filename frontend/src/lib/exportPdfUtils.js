/**
 * Utilitaires pour gérer les exports PDF avec gating d'authentification
 * 
 * PR7.1: Gating export PDF = compte requis
 * - Vérifie si l'utilisateur est connecté avant d'appeler l'API
 * - Intercepte les erreurs 401 avec code AUTH_REQUIRED_EXPORT
 * - Ouvre la modal de login/signup si nécessaire
 * 
 * PR8: Layout Éco = Premium uniquement
 * - Intercepte les erreurs 403 avec code PREMIUM_REQUIRED_ECO
 * - Ouvre la modal premium si nécessaire
 */

import { useAuth } from '../hooks/useAuth';
import { useLogin } from '../contexts/LoginContext';

/**
 * Vérifie si l'utilisateur peut exporter en PDF
 * 
 * @param {Object} authState - État d'authentification depuis useAuth()
 * @returns {boolean} true si l'utilisateur peut exporter
 */
export function canExportPdf(authState) {
  if (!authState) return false;
  return authState.userEmail !== null && authState.userEmail !== undefined && authState.userEmail !== '';
}

/**
 * Gère les erreurs d'export PDF et ouvre la modal appropriée
 * 
 * @param {Error} error - Erreur axios
 * @param {Function} openLogin - Fonction pour ouvrir la modal de login
 * @param {Function} openRegister - Fonction pour ouvrir la modal d'inscription
 * @param {Object} pendingAction - Action à relancer après login (optionnel)
 * @returns {boolean} true si l'erreur a été gérée (modal ouverte)
 */
export function handleExportPdfError(error, openLogin, openRegister, openPremium = null, pendingAction = null) {
  // Vérifier si c'est une erreur 401 avec code AUTH_REQUIRED_EXPORT
  const errorDetail = error.response?.data?.detail;
  
  if (error.response?.status === 401) {
    // Vérifier le format de l'erreur (peut être un objet ou une string)
    const errorCode = typeof errorDetail === 'object' ? errorDetail.code || errorDetail.error : null;
    
    if (errorCode === 'AUTH_REQUIRED_EXPORT' || errorDetail === 'AUTH_REQUIRED_EXPORT') {
      // PR7.1: Ouvrir modal "Créer un compte" pour export PDF
      openRegister({
        returnTo: window.location.pathname,
        pendingAction: pendingAction || { type: 'export_pdf' },
        mode: 'register'
      });
      return true;
    }
    
    // Autre erreur 401 (session expirée, etc.) - ouvrir modal login
    openLogin({
      returnTo: window.location.pathname,
      pendingAction: pendingAction || { type: 'export_pdf' }
    });
    return true;
  }
  
  // PR8: Vérifier si c'est une erreur 403 avec code PREMIUM_REQUIRED_ECO
  if (error.response?.status === 403) {
    const errorCode = typeof errorDetail === 'object' ? errorDetail.code || errorDetail.error : null;
    
    if (errorCode === 'PREMIUM_REQUIRED_ECO' || errorDetail?.error === 'premium_required') {
      // PR8: Ouvrir modal premium pour layout Éco
      if (openPremium) {
        openPremium({
          returnTo: window.location.pathname,
          pendingAction: pendingAction || { type: 'export_pdf' }
        });
        return true;
      }
      // Fallback: rediriger vers pricing si openPremium n'est pas disponible
      if (window.location.pathname !== '/pricing') {
        window.location.href = '/pricing?upgrade=eco';
        return true;
      }
    }
  }
  
  return false;
}

/**
 * Hook personnalisé pour gérer les exports PDF avec gating
 * 
 * @returns {Object} { canExport, handleExportError, checkBeforeExport }
 */
export function useExportPdfGate() {
  const { userEmail, isLoading, isPro } = useAuth();
  const { openLogin, openRegister } = useLogin();
  
  const canExport = !isLoading && userEmail !== null && userEmail !== undefined && userEmail !== '';
  
  const checkBeforeExport = (onExport) => {
    if (!canExport) {
      // PR7.1: Ouvrir modal "Créer un compte" avant d'appeler l'API
      openRegister({
        returnTo: window.location.pathname,
        pendingAction: { type: 'export_pdf', callback: onExport },
        mode: 'register'
      });
      return false;
    }
    return true;
  };
  
  const handleExportError = (error, openPremium = null, pendingAction = null) => {
    return handleExportPdfError(error, openLogin, openRegister, openPremium, pendingAction);
  };
  
  return {
    canExport,
    checkBeforeExport,
    handleExportError,
    isPro: isPro || false
  };
}

