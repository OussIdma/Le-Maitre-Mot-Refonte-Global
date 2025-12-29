/**
 * NavBar - Navigation principale avec 3 liens max
 */

import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { GraduationCap, ShoppingCart, LogIn } from "lucide-react";
import { useSelection } from "../contexts/SelectionContext";
import { useLogin } from "../contexts/LoginContext";
import { useAuth } from "../hooks/useAuth";

function NavBar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { selectionCount } = useSelection();
  const { openLogin } = useLogin();
  const { userEmail } = useAuth();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  // Vérifier si on est sur une page admin
  const isAdminPage = location.pathname.startsWith('/admin');

  const handleLoginClick = () => {
    openLogin(location.pathname);
  };

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

            <Button
              variant={isActive('/mes-exercices') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/mes-exercices')}
            >
              {t('nav.myExercises')}
            </Button>

            <Button
              variant={isActive('/mes-fiches') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/mes-fiches')}
            >
              {t('nav.mySheets')}
            </Button>

            {/* Bouton Composer avec badge panier */}
            <Button
              variant={isActive('/fiches/nouvelle') ? 'default' : 'outline'}
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

            {/* Bouton Se connecter si déconnecté */}
            {!userEmail && (
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

