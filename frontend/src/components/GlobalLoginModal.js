/**
 * GlobalLoginModal - Modal de login global accessible depuis toutes les pages
 * Utilise le LoginContext pour gérer l'état d'ouverture
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { useToast } from "../hooks/use-toast";
import { useLogin } from "../contexts/LoginContext";
import { LogIn, Mail, KeyRound, Loader2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function GlobalLoginModal() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { showLoginModal, setShowLoginModal, closeLogin } = useLogin();
  
  // États du formulaire
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginTab, setLoginTab] = useState("magic");
  const [loginEmailSent, setLoginEmailSent] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);
  
  // Reset form when modal closes
  useEffect(() => {
    if (!showLoginModal) {
      setLoginEmail("");
      setLoginPassword("");
      setLoginEmailSent(false);
      setLoginLoading(false);
      setLoginTab("magic");
    }
  }, [showLoginModal]);

  const generateDeviceId = () => {
    return 'device_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  };

  // Magic link request
  const requestLogin = async (email) => {
    if (!email) return;
    
    setLoginLoading(true);
    try {
      await axios.post(`${API}/auth/request-login`, {
        email: email
      });
      
      setLoginEmailSent(true);
      toast({
        title: "Email envoyé",
        description: "Si un compte existe, un email vous a été envoyé.",
      });
      
    } catch (error) {
      console.error('Error requesting login:', error);
      // Always show success message (neutral response)
      setLoginEmailSent(true);
      toast({
        title: "Email envoyé",
        description: "Si un compte existe, un email vous a été envoyé.",
      });
    } finally {
      setLoginLoading(false);
    }
  };

  // Password login handler
  const handlePasswordLogin = async () => {
    if (!loginEmail || !loginPassword) return;
    
    setLoginLoading(true);
    try {
      const deviceId = localStorage.getItem('lemaitremot_device_id') || generateDeviceId();
      localStorage.setItem('lemaitremot_device_id', deviceId);
      
      const response = await axios.post(`${API}/auth/login-password`, {
        email: loginEmail,
        password: loginPassword
      }, {
        headers: {
          'X-Device-ID': deviceId
        },
        withCredentials: true
      });
      
      // Store session token and user info
      const sessionToken = response.data.session_token;
      localStorage.setItem('lemaitremot_session_token', sessionToken);
      localStorage.setItem('lemaitremot_user_email', loginEmail);
      localStorage.setItem('lemaitremot_login_method', 'session');
      
      closeLogin();
      
      // P0 UX: Rediriger vers returnTo si présent
      const returnTo = sessionStorage.getItem('postLoginRedirect');
      if (returnTo) {
        sessionStorage.removeItem('postLoginRedirect');
        setTimeout(() => {
          navigate(returnTo);
        }, 100);
      }
      
      toast({
        title: "Connexion réussie",
        description: "Vous êtes maintenant connecté.",
      });
      
      // Ne pas reload - React Router gère la navigation
      // L'état auth sera mis à jour via LoginContext
      
    } catch (error) {
      console.error('Error in password login:', error);
      const status = error.response?.status;
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la connexion';
      
      if (status === 400) {
        toast({
          title: "Mot de passe non défini",
          description: errorMsg,
          variant: "destructive"
        });
      } else if (status === 401) {
        toast({
          title: "Erreur de connexion",
          description: "Email ou mot de passe incorrect",
          variant: "destructive"
        });
      } else {
        toast({
          title: "Erreur",
          description: errorMsg,
          variant: "destructive"
        });
      }
    } finally {
      setLoginLoading(false);
      setLoginPassword("");
    }
  };

  return (
    <Dialog open={showLoginModal} onOpenChange={setShowLoginModal}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center text-center">
            <LogIn className="mr-2 h-6 w-6 text-blue-600" />
            Connexion Pro
          </DialogTitle>
        </DialogHeader>
        
        <Tabs value={loginTab} onValueChange={setLoginTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="magic" className="flex items-center gap-2">
              <Mail className="h-4 w-4" />
              Lien magique
            </TabsTrigger>
            <TabsTrigger value="password" className="flex items-center gap-2">
              <KeyRound className="h-4 w-4" />
              Mot de passe
            </TabsTrigger>
          </TabsList>
          
          {/* Magic Link Tab (default) */}
          <TabsContent value="magic" className="space-y-4 mt-4">
            {!loginEmailSent ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="login-email-magic">Adresse email de votre compte Pro</Label>
                  <Input
                    id="login-email-magic"
                    type="email"
                    placeholder="votre@email.fr"
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && loginEmail && !loginLoading) {
                        requestLogin(loginEmail);
                      }
                    }}
                  />
                </div>
                
                <Button 
                  onClick={() => requestLogin(loginEmail)}
                  disabled={!loginEmail || loginLoading}
                  className="w-full bg-blue-600 hover:bg-blue-700"
                >
                  {loginLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Envoi en cours...
                    </>
                  ) : (
                    <>
                      <Mail className="mr-2 h-4 w-4" />
                      Recevoir un lien de connexion
                    </>
                  )}
                </Button>
                
                <div className="text-center">
                  <p className="text-xs text-gray-500 mb-2">
                    Pas encore Pro ?
                  </p>
                  <Button 
                    variant="link" 
                    onClick={() => {
                      closeLogin();
                      navigate('/pricing');
                    }}
                    className="text-blue-600 p-0 h-auto"
                  >
                    Créer un compte Pro
                  </Button>
                </div>
              </>
            ) : (
              <div className="space-y-4 text-center">
                <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <Mail className="h-8 w-8 text-blue-600" />
                </div>
                
                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Email envoyé !</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Si un compte existe, un email vous a été envoyé.
                  </p>
                  <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-700">
                    💡 <strong>Conseil :</strong> Vérifiez vos spams si vous ne recevez pas l'email dans les 2 minutes.
                  </div>
                </div>
                
                <Button 
                  variant="outline" 
                  onClick={() => {
                    setLoginEmailSent(false);
                    setLoginEmail("");
                  }}
                  className="w-full"
                >
                  Changer d'email
                </Button>
              </div>
            )}
          </TabsContent>
          
          {/* Password Tab */}
          <TabsContent value="password" className="space-y-4 mt-4">
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email-password">Adresse email</Label>
                <Input
                  id="login-email-password"
                  type="email"
                  placeholder="votre@email.fr"
                  value={loginEmail}
                  onChange={(e) => setLoginEmail(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && loginEmail && loginPassword && !loginLoading) {
                      handlePasswordLogin();
                    }
                  }}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="login-password">Mot de passe</Label>
                <Input
                  id="login-password"
                  type="password"
                  placeholder="••••••••"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && loginEmail && loginPassword && !loginLoading) {
                      handlePasswordLogin();
                    }
                  }}
                />
              </div>
              
              <Button 
                onClick={handlePasswordLogin}
                disabled={!loginEmail || !loginPassword || loginLoading}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {loginLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Connexion en cours...
                  </>
                ) : (
                  <>
                    <LogIn className="mr-2 h-4 w-4" />
                    Se connecter
                  </>
                )}
              </Button>
              
              <div className="text-center">
                <Button 
                  variant="link" 
                  onClick={() => {
                    closeLogin();
                    navigate('/reset-password');
                  }}
                  className="text-sm text-gray-600 p-0 h-auto"
                >
                  Mot de passe oublié ?
                </Button>
              </div>
              
              <div className="text-center">
                <p className="text-xs text-gray-500 mb-2">
                  Pas encore Pro ?
                </p>
                <Button 
                  variant="link" 
                  onClick={() => {
                    closeLogin();
                    navigate('/pricing');
                  }}
                  className="text-blue-600 p-0 h-auto"
                >
                  Créer un compte Pro
                </Button>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

export default GlobalLoginModal;

