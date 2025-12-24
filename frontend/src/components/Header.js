import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";
import { useLogin } from "../contexts/LoginContext";
import { Badge } from "./ui/badge";
import { 
  GraduationCap, 
  FileText, 
  Sparkles, 
  FolderOpen, 
  LogIn, 
  LogOut,
  Crown,
  Home,
  Settings
} from "lucide-react";

function Header({ isPro, userEmail, onLogin, onLogout }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { openLogin } = useLogin();
  
  // Si onLogin n'est pas fourni, utiliser le contexte
  const handleLoginClick = () => {
    if (onLogin) {
      onLogin();
    } else {
      openLogin(location.pathname);
    }
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <div 
            className="flex items-center cursor-pointer"
            onClick={() => navigate('/')}
          >
            <GraduationCap className="h-8 w-8 text-blue-600 mr-2" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">{t('nav.appName')}</h1>
              <p className="text-xs text-gray-500">{t('nav.subtitle')}</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-2">
            <Button
              variant={isActive('/') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/')}
            >
              <Home className="h-4 w-4 mr-2" />
              {t('nav.home')}
            </Button>

            <Button
              variant={isActive('/builder') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/builder')}
            >
              <FileText className="h-4 w-4 mr-2" />
              {t('nav.createSheet')}
            </Button>

            <Button
              variant={isActive('/exercise-ia') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/')}
              className="relative"
            >
              <Sparkles className="h-4 w-4 mr-2" />
              {t('nav.exerciseIA')}
              {isPro && (
                <Badge className="ml-2 bg-purple-600 text-white text-xs">{t('pro.badge')}</Badge>
              )}
            </Button>

            <Button
              variant={isActive('/sheets') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/sheets')}
            >
              <FolderOpen className="h-4 w-4 mr-2" />
              {t('nav.mySheets')}
            </Button>

            {isPro && (
              <Button
                variant={isActive('/pro/settings') ? 'default' : 'ghost'}
                size="sm"
                onClick={() => {
                  // Détecter le sheetId depuis l'URL courante
                  const match = location.pathname.match(/\/builder\/([^/]+)/);
                  const sheetId = match ? match[1] : localStorage.getItem('current_sheet_id');
                  
                  if (sheetId) {
                    navigate('/pro/settings', { state: { from: 'builder', sheetId } });
                  } else {
                    navigate('/pro/settings');
                  }
                }}
                className="relative"
              >
                <Settings className="h-4 w-4 mr-2" />
                {t('nav.proSettings')}
                <Badge className="ml-2 bg-blue-600 text-white text-xs">{t('pro.badge')}</Badge>
              </Button>
            )}
          </nav>

          {/* User section */}
          <div className="flex items-center gap-2">
            {isPro && userEmail ? (
              <div className="flex items-center gap-2">
                <div className="hidden sm:flex items-center bg-blue-50 px-3 py-1.5 rounded-lg">
                  <Crown className="h-4 w-4 text-blue-600 mr-2" />
                  <div className="text-right">
                    <p className="text-xs font-semibold text-blue-900">{t('pro.status')}</p>
                    <p className="text-xs text-blue-700">{userEmail.split('@')[0]}</p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onLogout}
                >
                  <LogOut className="h-4 w-4 mr-2" />
                  {t('actions.disconnect')}
                </Button>
              </div>
            ) : (
              <Button
                variant="default"
                size="sm"
                onClick={handleLoginClick}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <LogIn className="h-4 w-4 mr-2" />
                {t('actions.login')}
              </Button>
            )}
          </div>
        </div>

        {/* Mobile navigation */}
        <nav className="md:hidden mt-4 flex gap-2 overflow-x-auto pb-2">
          <Button
            variant={isActive('/') ? 'default' : 'outline'}
            size="sm"
            onClick={() => navigate('/')}
          >
            <Home className="h-4 w-4 mr-1" />
            {t('nav.home')}
          </Button>

          <Button
            variant={isActive('/builder') ? 'default' : 'outline'}
            size="sm"
            onClick={() => navigate('/builder')}
          >
            <FileText className="h-4 w-4 mr-1" />
            {t('nav.sheetShort')}
          </Button>

          <Button
            variant={isActive('/exercise-ia') ? 'default' : 'outline'}
            size="sm"
            onClick={() => navigate('/')}
          >
            <Sparkles className="h-4 w-4 mr-1" />
            {t('nav.iaShort')}
          </Button>

          <Button
            variant={isActive('/sheets') ? 'default' : 'outline'}
            size="sm"
            onClick={() => navigate('/sheets')}
          >
            <FolderOpen className="h-4 w-4 mr-1" />
            {t('nav.mySheetsShort')}
          </Button>

          {isPro && (
            <Button
              variant={isActive('/pro/settings') ? 'default' : 'outline'}
              size="sm"
              onClick={() => {
                const match = location.pathname.match(/\/builder\/([^/]+)/);
                const sheetId = match ? match[1] : localStorage.getItem('current_sheet_id');
                
                if (sheetId) {
                  navigate('/pro/settings', { state: { from: 'builder', sheetId } });
                } else {
                  navigate('/pro/settings');
                }
              }}
            >
              <Settings className="h-4 w-4 mr-1" />
              {t('nav.proSettingsShort')}
            </Button>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;
