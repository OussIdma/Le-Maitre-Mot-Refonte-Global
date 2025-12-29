/**
 * LoginContext - Contexte global pour gérer le modal de login
 * Permet d'ouvrir le modal de login depuis n'importe quelle page
 *
 * Supporte:
 * - pendingAction: action à relancer après login/signup réussi
 * - initialMode: "login" | "register" pour ouvrir directement en mode inscription
 */

import React, { createContext, useContext, useState, useCallback } from 'react';

const LoginContext = createContext();

export const useLogin = () => {
  const context = useContext(LoginContext);
  if (!context) {
    throw new Error('useLogin must be used within LoginProvider');
  }
  return context;
};

export const LoginProvider = ({ children }) => {
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [pendingAction, setPendingAction] = useState(null);
  const [initialMode, setInitialMode] = useState("login"); // "login" | "register"

  /**
   * Ouvre le modal de login
   * @param {string|object} options - soit returnTo (string), soit {returnTo, pendingAction, mode}
   */
  const openLogin = useCallback((options = null) => {
    if (typeof options === 'string') {
      // Ancien format: openLogin('/path')
      sessionStorage.setItem('postLoginRedirect', options);
      setInitialMode("login");
      setPendingAction(null);
    } else if (options && typeof options === 'object') {
      // Nouveau format: openLogin({returnTo, pendingAction, mode})
      if (options.returnTo) {
        sessionStorage.setItem('postLoginRedirect', options.returnTo);
      }
      if (options.pendingAction) {
        setPendingAction(options.pendingAction);
      }
      if (options.mode) {
        setInitialMode(options.mode);
      } else {
        setInitialMode("login");
      }
    } else {
      setInitialMode("login");
      setPendingAction(null);
    }
    setShowLoginModal(true);
  }, []);

  /**
   * Ouvre directement en mode inscription gratuite
   * @param {object} pendingActionParam - action à relancer après inscription
   */
  const openRegister = useCallback((pendingActionParam = null) => {
    if (pendingActionParam) {
      setPendingAction(pendingActionParam);
    }
    setInitialMode("register");
    setShowLoginModal(true);
  }, []);

  const closeLogin = useCallback(() => {
    setShowLoginModal(false);
    // Ne pas effacer pendingAction ici - sera effacé après exécution
  }, []);

  /**
   * Exécute et efface l'action pending
   * Appelé par GlobalLoginModal après login/signup réussi
   */
  const executePendingAction = useCallback(() => {
    const action = pendingAction;
    setPendingAction(null);
    return action;
  }, [pendingAction]);

  /**
   * Efface l'action pending sans l'exécuter
   */
  const clearPendingAction = useCallback(() => {
    setPendingAction(null);
  }, []);

  return (
    <LoginContext.Provider value={{
      showLoginModal,
      setShowLoginModal,
      openLogin,
      openRegister,
      closeLogin,
      pendingAction,
      setPendingAction,
      executePendingAction,
      clearPendingAction,
      initialMode,
      setInitialMode
    }}>
      {children}
    </LoginContext.Provider>
  );
};







