/**
 * NavBar - Navigation principale avec 3 liens max
 */

import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { GraduationCap, ShoppingCart, LogIn, LogOut, Loader2 } from "lucide-react";
import { useSelection } from "../contexts/SelectionContext";
import { useLogin } from "../contexts/LoginContext";
import { useAuth } from "../hooks/useAuth";
import { isLoggedIn, normalizeEmail } from "../auth/authStateContract";

function NavBar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { selectionCount } = useSelection();
  const { openLogin } = useLogin();
  const { userEmail, isPro, isLoading, sessionToken } = useAuth();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  // Vérifier si on est sur une page admin
  const isAdminPage = location.pathname.startsWith('/admin');

  const handleLoginClick = () => {
    openLogin(location.pathname);
  };

  // P0: Fonction de déconnexion
  const handleLogout = async () => {
    try {
      if (sessionToken) {
        const axios = (await import('axios')).default;
        const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
        const API = `${BACKEND_URL}/api`;
        
        try {
          await axios.post(`${API}/auth/logout`, {}, {
            headers: {
              'X-Session-Token': sessionToken
            }
          });
        } catch (error) {
          // Ignorer les erreurs de logout API - on nettoie quand même le localStorage
          console.log('[NavBar] Erreur logout API (ignorée):', error);
        }
      }
    } catch (error) {
      console.error('[NavBar] Erreur lors de la déconnexion:', error);
    } finally {
      // P0: Toujours nettoyer le localStorage
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
      // Dispatcher l'événement pour notifier useAuth()
      window.dispatchEvent(new Event('lmm:auth-changed'));
      
      console.log('[NavBar] ✅ Déconnexion réussie');
    }
  };

  // P0: Déterminer quels liens afficher selon le statut utilisateur
  // P0: Utiliser le contrat authStateContract pour vérifier l'état de connexion
  const authState = {
    sessionToken,
    userEmail,
    isPro,
    isLoading
  };
  const isLoggedInState = !isLoading && isLoggedIn(authState);
  const showMyExercises = isPro; // Bibliothèque = Pro uniquement
  const showMySheets = isPro; // Historique = Pro uniquement
  const showComposer = true; // Composer accessible à tous (Free + Pro)

  return (
    <nav className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div 
            className="flex items-center cursor-pointer"
            onClick={() => navigate('/')}
          >
            <GraduationCap className="h-8 w-8 text-blue-600 mr-2" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">{t('nav.appName')}</h1>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-2">
            <Button
              variant={isActive('/') && !isAdminPage ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/')}
            >
              {t('nav.home')}
            </Button>

            <Button
              variant={isActive('/generer') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/generer')}
            >
              {t('nav.generate')}
            </Button>

            {/* P0: Mes exercices - Pro uniquement */}
            {showMyExercises && (
              <Button
                variant={isActive('/mes-exercices') ? 'default' : 'ghost'}
                size="sm"
                onClick={() => navigate('/mes-exercices')}
              >
                {t('nav.myExercises')}
              </Button>
            )}

            {/* P0: Mes fiches - Pro uniquement (ou Composer pour Free) */}
            {showMySheets ? (
              <Button
                variant={isActive('/mes-fiches') ? 'default' : 'ghost'}
                size="sm"
                onClick={() => navigate('/mes-fiches')}
              >
                {t('nav.mySheets')}
              </Button>
            ) : isLoggedInState ? (
              // Free user: afficher "Composer" au lieu de "Mes fiches"
              <Button
                variant={isActive('/fiches/nouvelle') ? 'default' : 'ghost'}
                size="sm"
                onClick={() => navigate('/fiches/nouvelle')}
              >
                Composer
              </Button>
            ) : null}

            {/* Bouton Composer avec badge panier - accessible à tous */}
            {showComposer && (
              <Button
                variant={isActive('/fiches/nouvelle') && !showMySheets ? 'default' : 'outline'}
                size="sm"
                onClick={() => navigate('/fiches/nouvelle')}
                className="relative"
              >
                <ShoppingCart className="h-4 w-4 mr-2" />
                {selectionCount > 0 ? `Composer (${selectionCount})` : 'Composer'}
                {selectionCount > 0 && (
                  <Badge className="ml-2 bg-green-600 text-white text-xs px-1.5 py-0.5">
                    {selectionCount}
                  </Badge>
                )}
              </Button>
            )}

            {/* Admin link - seulement si on est déjà sur une page admin ou si accessible */}
            {isAdminPage && (
              <Button
                variant={isActive('/admin') ? 'default' : 'ghost'}
                size="sm"
                onClick={() => navigate('/admin/curriculum')}
              >
                {t('nav.admin')}
              </Button>
            )}

            {/* P0: Afficher l'état de chargement ou le bouton de connexion */}
            {isLoading ? (
              <Button
                variant="ghost"
                size="sm"
                disabled
                className="opacity-50"
              >
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Chargement...
              </Button>
            ) : !isLoggedInState ? (
              <Button
                variant="default"
                size="sm"
                onClick={handleLoginClick}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <LogIn className="h-4 w-4 mr-2" />
                Se connecter
              </Button>
            ) : isLoggedInState && normalizeEmail(userEmail) ? (
              // P0: Afficher l'email de l'utilisateur connecté (Free ou Pro) + bouton déconnexion
              // P0: Utiliser normalizeEmail pour valider l'email
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="hidden sm:inline">{normalizeEmail(userEmail)}</span>
                  {isPro && (
                    <Badge variant="default" className="bg-yellow-500 text-white">
                      Pro
                    </Badge>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleLogout}
                  className="text-gray-600 hover:text-gray-900"
                  title="Se déconnecter"
                >
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              // P0: Fallback - si userEmail est null/undefined/vide, afficher "Se connecter"
              <Button
                variant="default"
                size="sm"
                onClick={handleLoginClick}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <LogIn className="h-4 w-4 mr-2" />
                Se connecter
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export default NavBar;

