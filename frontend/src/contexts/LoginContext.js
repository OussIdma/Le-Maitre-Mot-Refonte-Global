/**
 * LoginContext - Contexte global pour gérer le modal de login
 * Permet d'ouvrir le modal de login depuis n'importe quelle page
 */

import React, { createContext, useContext, useState } from 'react';

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
  
  const openLogin = (returnTo = null) => {
    if (returnTo) {
      sessionStorage.setItem('postLoginRedirect', returnTo);
    }
    setShowLoginModal(true);
  };

  const closeLogin = () => {
    setShowLoginModal(false);
  };

  return (
    <LoginContext.Provider value={{ 
      showLoginModal, 
      setShowLoginModal, 
      openLogin,
      closeLogin
    }}>
      {children}
    </LoginContext.Provider>
  );
};



