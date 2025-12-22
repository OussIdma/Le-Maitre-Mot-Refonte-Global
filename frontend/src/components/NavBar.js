/**
 * NavBar - Navigation principale avec 3 liens max
 */

import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { GraduationCap } from "lucide-react";

function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  // Vérifier si on est sur une page admin
  const isAdminPage = location.pathname.startsWith('/admin');

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
              <h1 className="text-xl font-bold text-gray-900">Le Maître Mot</h1>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="flex items-center gap-2">
            <Button
              variant={isActive('/') && !isAdminPage ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/')}
            >
              Accueil
            </Button>

            <Button
              variant={isActive('/generer') ? 'default' : 'ghost'}
              size="sm"
              onClick={() => navigate('/generer')}
            >
              Générer
            </Button>

            {/* Admin link - seulement si on est déjà sur une page admin ou si accessible */}
            {isAdminPage && (
              <Button
                variant={isActive('/admin') ? 'default' : 'ghost'}
                size="sm"
                onClick={() => navigate('/admin/curriculum')}
              >
                Admin
              </Button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export default NavBar;

