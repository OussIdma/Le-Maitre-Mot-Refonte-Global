/**
 * GlobalLoginModal - Modal de login/inscription global accessible depuis toutes les pages
 * Utilise le LoginContext pour gérer l'état d'ouverture
 *
 * Modes:
 * - "login": Connexion avec lien magique ou mot de passe
 * - "register": Inscription gratuite avec email + password + password_confirm
 *
 * Après succès: exécute pendingAction si présent (ex: relancer export PDF)
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Button } from "./ui/button";
import { Alert, AlertDescription } from "./ui/alert";
import { useToast } from "../hooks/use-toast";
import { useLogin } from "../contexts/LoginContext";
import { LogIn, Mail, KeyRound, Loader2, UserPlus, Crown, ArrowLeft, CheckCircle } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function GlobalLoginModal() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const {
    showLoginModal,
    setShowLoginModal,
    closeLogin,
    initialMode,
    setInitialMode,
    executePendingAction
  } = useLogin();

  // Mode principal: "login" ou "register"
  const [mode, setMode] = useState(initialMode);

  // États du formulaire login
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginTab, setLoginTab] = useState("password"); // "magic" ou "password"
  const [loginEmailSent, setLoginEmailSent] = useState(false);
  const [loginLoading, setLoginLoading] = useState(false);

  // États du formulaire register
  const [registerEmail, setRegisterEmail] = useState("");
  const [registerPassword, setRegisterPassword] = useState("");
  const [registerPasswordConfirm, setRegisterPasswordConfirm] = useState("");
  const [registerLoading, setRegisterLoading] = useState(false);
  const [registerError, setRegisterError] = useState(null);

  // P0: État pour afficher le lien magique en mode dev
  const [devMagicLink, setDevMagicLink] = useState(null);

  // Sync mode with initialMode when modal opens
  useEffect(() => {
    if (showLoginModal) {
      setMode(initialMode);
    }
  }, [showLoginModal, initialMode]);

  // Reset form when modal closes
  useEffect(() => {
    if (!showLoginModal) {
      setLoginEmail("");
      setLoginPassword("");
      setLoginEmailSent(false);
      setLoginLoading(false);
      setLoginTab("password");
      setDevMagicLink(null);
      setRegisterEmail("");
      setRegisterPassword("");
      setRegisterPasswordConfirm("");
      setRegisterLoading(false);
      setRegisterError(null);
    }
  }, [showLoginModal]);

  const generateDeviceId = () => {
    return 'device_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  };

  /**
   * Callback après login/register réussi
   * - Stocke le session token
   * - Dispatch event auth-changed
   * - Ferme le modal
   * - Exécute pendingAction si présent
   */
  const onAuthSuccess = (sessionToken, email, isPro = false) => {
    // Store session token and user info
    localStorage.setItem('lemaitremot_session_token', sessionToken);
    localStorage.setItem('lemaitremot_user_email', email);
    localStorage.setItem('lemaitremot_login_method', 'session');

    // Dispatcher l'événement pour notifier les composants utilisant useAuth()
    window.dispatchEvent(new Event('lmm:auth-changed'));

    closeLogin();

    toast({
      title: isPro ? "Connexion Pro réussie" : "Compte créé !",
      description: isPro
        ? "Vous êtes connecté à votre compte Pro."
        : "Votre compte gratuit est prêt. Vous pouvez maintenant exporter vos fiches.",
    });

    // Exécuter l'action pending si présente
    const pending = executePendingAction();
    if (pending) {
      console.log('🔄 Exécution de l\'action pending:', pending);
      // L'action sera exécutée par le composant qui l'a définie
      // via un event custom ou un callback
      window.dispatchEvent(new CustomEvent('lmm:execute-pending-action', { detail: pending }));
    }

    // Rediriger vers returnTo si présent (et pas de pending action)
    if (!pending) {
      const returnTo = sessionStorage.getItem('postLoginRedirect');
      if (returnTo) {
        sessionStorage.removeItem('postLoginRedirect');
        setTimeout(() => {
          navigate(returnTo);
        }, 100);
      }
    }
  };

  // =====================================================
  // REGISTER FREE
  // =====================================================
  const handleRegisterFree = async () => {
    if (!registerEmail || !registerPassword || !registerPasswordConfirm) {
      setRegisterError("Veuillez remplir tous les champs");
      return;
    }

    if (registerPassword !== registerPasswordConfirm) {
      setRegisterError("Les mots de passe ne correspondent pas");
      return;
    }

    if (registerPassword.length < 6) {
      setRegisterError("Le mot de passe doit contenir au moins 6 caractères");
      return;
    }

    setRegisterLoading(true);
    setRegisterError(null);

    try {
      const deviceId = localStorage.getItem('lemaitremot_device_id') || generateDeviceId();
      localStorage.setItem('lemaitremot_device_id', deviceId);

      const response = await axios.post(`${API}/auth/register-free`, {
        email: registerEmail,
        password: registerPassword,
        password_confirm: registerPasswordConfirm
      }, {
        headers: {
          'X-Device-ID': deviceId
        },
        withCredentials: true
      });

      onAuthSuccess(response.data.session_token, registerEmail, false);

    } catch (error) {
      console.error('Error in register-free:', error);
      const status = error.response?.status;
      const errorMsg = error.response?.data?.detail || 'Erreur lors de l\'inscription';

      if (status === 409) {
        setRegisterError("Un compte existe déjà avec cet email. Connectez-vous plutôt.");
      } else if (status === 400) {
        setRegisterError(errorMsg);
      } else {
        setRegisterError("Erreur lors de l'inscription. Veuillez réessayer.");
      }
    } finally {
      setRegisterLoading(false);
    }
  };

  // =====================================================
  // LOGIN PASSWORD
  // =====================================================
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

      const isPro = response.data.is_pro === true;
      onAuthSuccess(response.data.session_token, loginEmail, isPro);

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

  // =====================================================
  // LOGIN MAGIC LINK
  // =====================================================
  const requestLogin = async (email) => {
    if (!email) return;

    setLoginLoading(true);
    setDevMagicLink(null);
    try {
      const response = await axios.post(`${API}/auth/request-login`, {
        email: email
      });

      setLoginEmailSent(true);

      // P0: Afficher le lien magique en mode dev
      if (response.data.dev_mode && response.data.magic_link) {
        setDevMagicLink(response.data.magic_link);
        toast({
          title: "Lien magique (mode dev)",
          description: "Le lien est affiché ci-dessous pour copier.",
        });
      } else {
        toast({
          title: "Email envoyé",
          description: "Si un compte existe, un email vous a été envoyé.",
        });
      }

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

  // =====================================================
  // RENDER: MODE REGISTER
  // =====================================================
  const renderRegisterMode = () => (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="register-email">Adresse email</Label>
        <Input
          id="register-email"
          type="email"
          placeholder="votre@email.fr"
          value={registerEmail}
          onChange={(e) => setRegisterEmail(e.target.value)}
          disabled={registerLoading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="register-password">Mot de passe</Label>
        <Input
          id="register-password"
          type="password"
          placeholder="6 caractères minimum"
          value={registerPassword}
          onChange={(e) => setRegisterPassword(e.target.value)}
          disabled={registerLoading}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="register-password-confirm">Confirmer le mot de passe</Label>
        <Input
          id="register-password-confirm"
          type="password"
          placeholder="Répétez le mot de passe"
          value={registerPasswordConfirm}
          onChange={(e) => setRegisterPasswordConfirm(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && registerEmail && registerPassword && registerPasswordConfirm && !registerLoading) {
              handleRegisterFree();
            }
          }}
          disabled={registerLoading}
        />
      </div>

      {registerError && (
        <Alert variant="destructive">
          <AlertDescription>{registerError}</AlertDescription>
        </Alert>
      )}

      <Button
        onClick={handleRegisterFree}
        disabled={!registerEmail || !registerPassword || !registerPasswordConfirm || registerLoading}
        className="w-full bg-green-600 hover:bg-green-700"
      >
        {registerLoading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Création en cours...
          </>
        ) : (
          <>
            <UserPlus className="mr-2 h-4 w-4" />
            Créer mon compte gratuit
          </>
        )}
      </Button>

      <div className="bg-green-50 p-3 rounded-lg text-xs text-green-700">
        <CheckCircle className="h-4 w-4 inline mr-1" />
        <strong>Compte gratuit :</strong> 10 exports PDF/jour, preview illimitée
      </div>

      <div className="text-center pt-2 border-t">
        <p className="text-xs text-gray-500 mb-2">
          Déjà un compte ?
        </p>
        <Button
          variant="link"
          onClick={() => setMode("login")}
          className="text-blue-600 p-0 h-auto"
        >
          Se connecter
        </Button>
      </div>

      <div className="text-center">
        <Button
          variant="link"
          onClick={() => {
            closeLogin();
            navigate('/pricing');
          }}
          className="text-purple-600 p-0 h-auto text-xs"
        >
          <Crown className="h-3 w-3 mr-1" />
          Découvrir l'offre Pro
        </Button>
      </div>
    </div>
  );

  // =====================================================
  // RENDER: MODE LOGIN
  // =====================================================
  const renderLoginMode = () => (
    <Tabs value={loginTab} onValueChange={setLoginTab} className="w-full">
      <TabsList className="grid w-full grid-cols-2">
        <TabsTrigger value="password" className="flex items-center gap-2">
          <KeyRound className="h-4 w-4" />
          Mot de passe
        </TabsTrigger>
        <TabsTrigger value="magic" className="flex items-center gap-2">
          <Mail className="h-4 w-4" />
          Lien magique
        </TabsTrigger>
      </TabsList>

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
        </div>
      </TabsContent>

      {/* Magic Link Tab */}
      <TabsContent value="magic" className="space-y-4 mt-4">
        {!loginEmailSent ? (
          <>
            <div className="space-y-2">
              <Label htmlFor="login-email-magic">Adresse email</Label>
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
          </>
        ) : (
          <div className="space-y-4 text-center">
            {/* P0: Afficher le lien magique en mode dev */}
            {devMagicLink ? (
              <div className="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm font-medium text-blue-900">
                  Lien magique (mode développement)
                </p>
                <div className="flex items-center gap-2">
                  <Input
                    value={devMagicLink}
                    readOnly
                    className="flex-1 font-mono text-xs bg-white"
                  />
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      navigator.clipboard.writeText(devMagicLink);
                      toast({
                        title: "Lien copié",
                        description: "Le lien magique a été copié dans le presse-papier.",
                      });
                    }}
                  >
                    Copier
                  </Button>
                </div>
                <p className="text-xs text-blue-700">
                  Cliquez sur le lien ou copiez-le pour vous connecter.
                </p>
                <Button
                  variant="outline"
                  onClick={() => {
                    setLoginEmailSent(false);
                    setDevMagicLink(null);
                    setLoginEmail("");
                  }}
                  className="w-full"
                >
                  Réessayer
                </Button>
              </div>
            ) : (
              <>
                <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center">
                  <Mail className="h-8 w-8 text-blue-600" />
                </div>

                <div>
                  <h3 className="font-semibold text-gray-900 mb-2">Email envoyé !</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Si un compte existe, un email vous a été envoyé.
                  </p>
                  <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-700">
                    <strong>Conseil :</strong> Vérifiez vos spams si vous ne recevez pas l'email dans les 2 minutes.
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
              </>
            )}
          </div>
        )}
      </TabsContent>

      {/* Footer commun pour login */}
      <div className="text-center pt-4 mt-4 border-t">
        <p className="text-xs text-gray-500 mb-2">
          Pas encore de compte ?
        </p>
        <Button
          variant="link"
          onClick={() => setMode("register")}
          className="text-green-600 p-0 h-auto font-medium"
        >
          <UserPlus className="h-4 w-4 mr-1" />
          Créer un compte gratuit
        </Button>
      </div>
    </Tabs>
  );

  return (
    <Dialog open={showLoginModal} onOpenChange={setShowLoginModal}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          {mode === "register" ? (
            <>
              <DialogTitle className="flex items-center">
                <UserPlus className="mr-2 h-6 w-6 text-green-600" />
                Créer un compte gratuit
              </DialogTitle>
              <DialogDescription>
                La preview est gratuite. Créez un compte pour exporter vos fiches en PDF.
              </DialogDescription>
            </>
          ) : (
            <>
              <DialogTitle className="flex items-center">
                <LogIn className="mr-2 h-6 w-6 text-blue-600" />
                Connexion
              </DialogTitle>
              <DialogDescription>
                Connectez-vous à votre compte pour accéder à vos fonctionnalités.
              </DialogDescription>
            </>
          )}
        </DialogHeader>

        {mode === "register" ? renderRegisterMode() : renderLoginMode()}
      </DialogContent>
    </Dialog>
  );
}

export default GlobalLoginModal;
