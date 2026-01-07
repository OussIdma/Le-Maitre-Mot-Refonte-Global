/**
 * PricingPage - Page de tarification améliorée (P2.3)
 * 
 * Affiche clairement ce que l'utilisateur a déjà (Free) et ce qu'il débloque (Pro).
 * Conversion claire vers l'essai Pro.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';
import { Check, Crown, FileDown, Layers, Palette, Zap, BookOpen, Sparkles, Mail, Loader2, CheckCircle, Copy, UserPlus } from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { Separator } from './ui/separator';
import { useLogin } from '../contexts/LoginContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PricingPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { openRegister } = useLogin();
  const [isPro, setIsPro] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [checkoutEmail, setCheckoutEmail] = useState('');
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [checkoutError, setCheckoutError] = useState(null);
  const [checkoutSuccess, setCheckoutSuccess] = useState(false);
  const [checkoutLink, setCheckoutLink] = useState('');

  useEffect(() => {
    // Check if user is logged in and if Pro
    const sessionToken = localStorage.getItem('lemaitremot_session_token');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    const hasSession = !!(sessionToken && loginMethod === 'session');
    setIsLoggedIn(hasSession);
    // Note: Pour savoir si Pro, il faudrait appeler /auth/me, mais on simplifie ici
    // En prod, vérifier via /auth/me
    setIsPro(false); // Par défaut non-Pro, sera mis à jour si besoin
  }, []);

  // Handler pour le bouton "Commencer gratuitement"
  const handleStartFree = () => {
    if (isLoggedIn) {
      // Déjà connecté, rediriger vers le générateur
      navigate('/generer');
    } else {
      // Ouvrir le modal d'inscription
      openRegister();
    }
  };

  const handleStartTrial = () => {
    // Ouvrir le modal pour demander l'email
    setShowEmailModal(true);
    setCheckoutEmail('');
    setCheckoutError(null);
    setCheckoutSuccess(false);
  };

  const handlePreCheckout = async () => {
    if (!checkoutEmail || !checkoutEmail.includes('@')) {
      setCheckoutError('Veuillez saisir une adresse email valide');
      return;
    }

    setCheckoutLoading(true);
    setCheckoutError(null);
    setCheckoutLink(''); // Réinitialiser le lien

    try {
      const response = await axios.post(`${API}/auth/pre-checkout`, {
        email: checkoutEmail,
        package_id: 'monthly' // Par défaut mensuel
      });

      // Debug: afficher la réponse complète
      console.log('🔍 Pre-checkout response:', response.data);

      // Le backend retourne toujours 200 (réponse neutre)
      setCheckoutSuccess(true);
      
      // ✅ Stocker le lien séparément si disponible (mode dev)
      if (response.data.success && response.data.dev_mode && response.data.checkout_link) {
        console.log('✅ Lien de checkout détecté:', response.data.checkout_link);
        setCheckoutLink(response.data.checkout_link);
      } else {
        console.log('⚠️ Lien non disponible:', {
          success: response.data.success,
          dev_mode: response.data.dev_mode,
          checkout_link: response.data.checkout_link
        });
      }
    } catch (error) {
      console.error('Error in pre-checkout:', error);
      // Même en cas d'erreur, afficher le message de succès (sécurité)
      setCheckoutSuccess(true);
    } finally {
      setCheckoutLoading(false);
    }
  };

  const freeFeatures = [
    {
      icon: <BookOpen className="h-5 w-5 text-blue-600" />,
      title: "Génération & preview illimitées",
      description: "Créez autant d'exercices que vous voulez et prévisualisez-les"
    },
    {
      icon: <FileDown className="h-5 w-5 text-green-600" />,
      title: "3 exports PDF / jour",
      description: "Exportez vos documents en PDF (limite quotidienne)"
    },
    {
      icon: <Layers className="h-5 w-5 text-purple-600" />,
      title: "Composer des fiches",
      description: "Sélectionnez et organisez vos exercices en fiches personnalisées"
    },
    {
      icon: <Palette className="h-5 w-5 text-gray-600" />,
      title: "Mise en page standard",
      description: "Exports avec mise en page classique"
    }
  ];

  const proFeatures = [
    {
      icon: <FileDown className="h-5 w-5 text-blue-600" />,
      title: "Exports illimités",
      description: "Exportez autant de PDF que nécessaire, sans limite"
    },
    {
      icon: <Layers className="h-5 w-5 text-purple-600" />,
      title: "Variantes A/B/C",
      description: "Générez plusieurs versions d'un même exercice pour vos évaluations"
    },
    {
      icon: <Palette className="h-5 w-5 text-green-600" />,
      title: "Branding + templates",
      description: "Personnalisez vos documents avec votre logo et vos templates"
    },
    {
      icon: <BookOpen className="h-5 w-5 text-orange-600" />,
      title: "Bibliothèque & réutilisation",
      description: "Sauvegardez et réutilisez vos exercices et documents"
    },
    {
      icon: <Zap className="h-5 w-5 text-yellow-600" />,
      title: "Interactif illimité + stats",
      description: "Créez autant de devoirs interactifs que vous voulez avec statistiques détaillées"
    },
    {
      icon: <Crown className="h-5 w-5 text-purple-600" />,
      title: "Générateurs avancés",
      description: "Accédez à tous les générateurs premium et leurs variantes"
    }
  ];

  if (isPro) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-12 px-4">
        <div className="container mx-auto max-w-4xl">
          <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
            <CardHeader className="text-center">
              <div className="mx-auto w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mb-4">
                <Crown className="h-8 w-8 text-purple-600" />
              </div>
              <CardTitle className="text-3xl mb-2">Vous êtes déjà Pro !</CardTitle>
              <CardDescription className="text-lg">
                Profitez de toutes les fonctionnalités avancées
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Button onClick={() => navigate('/')} variant="outline">
                Retour à l'accueil
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 py-12 px-4">
      <div className="container mx-auto max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choisissez votre offre
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Découvrez ce que vous avez déjà et ce que vous pouvez débloquer avec Pro
          </p>
        </div>

        {/* Comparison Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Free Plan */}
          <Card className="border-2 border-gray-200">
            <CardHeader>
              <CardTitle className="text-2xl mb-2">Gratuit</CardTitle>
              <CardDescription className="text-lg">
                Parfait pour commencer
              </CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold text-gray-900">0€</span>
                <span className="text-gray-600">/mois</span>
              </div>
            </CardHeader>
            <CardContent>
              <Separator className="mb-6" />
              <div className="space-y-4">
                {freeFeatures.map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="mt-1">
                      <Check className="h-5 w-5 text-green-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {feature.title}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                onClick={handleStartFree}
                className="w-full mt-8 bg-green-600 hover:bg-green-700 text-white"
                size="lg"
              >
                <UserPlus className="mr-2 h-4 w-4" />
                {isLoggedIn ? "Accéder au générateur" : "Commencer gratuitement"}
              </Button>
            </CardContent>
          </Card>

          {/* Pro Plan */}
          <Card className="border-2 border-purple-500 bg-gradient-to-br from-purple-50 to-indigo-50 relative">
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
              <Badge className="bg-purple-600 text-white px-4 py-1">
                <Sparkles className="h-3 w-3 mr-1" />
                Recommandé
              </Badge>
            </div>
            <CardHeader>
              <CardTitle className="text-2xl mb-2 flex items-center gap-2">
                <Crown className="h-6 w-6 text-purple-600" />
                Pro
              </CardTitle>
              <CardDescription className="text-lg">
                Pour un enseignement personnalisé
              </CardDescription>
              <div className="mt-4">
                <span className="text-4xl font-bold text-purple-900">9,99€</span>
                <span className="text-gray-600">/mois</span>
              </div>
              <Badge className="mt-2 bg-green-100 text-green-800">
                Essai gratuit 7 jours
              </Badge>
            </CardHeader>
            <CardContent>
              <Separator className="mb-6" />
              <div className="space-y-4">
                {proFeatures.map((feature, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <div className="mt-1">
                      <Check className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900 mb-1">
                        {feature.title}
                      </h4>
                      <p className="text-sm text-gray-600">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
              <Button
                onClick={handleStartTrial}
                className="w-full mt-8 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white"
                size="lg"
              >
                <Sparkles className="mr-2 h-4 w-4" />
                Commencer l'essai Pro
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* FAQ Section */}
        <Card className="mt-12">
          <CardHeader>
            <CardTitle>Questions fréquentes</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                Puis-je annuler à tout moment ?
              </h4>
              <p className="text-sm text-gray-600">
                Oui, vous pouvez annuler votre abonnement Pro à tout moment depuis vos paramètres.
              </p>
            </div>
            <Separator />
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                L'essai gratuit est-il vraiment gratuit ?
              </h4>
              <p className="text-sm text-gray-600">
                Oui, l'essai de 7 jours est entièrement gratuit. Aucune carte bancaire n'est requise pour commencer.
              </p>
            </div>
            <Separator />
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">
                Que se passe-t-il après l'essai ?
              </h4>
              <p className="text-sm text-gray-600">
                Après 7 jours, votre abonnement Pro commence automatiquement. Vous pouvez annuler à tout moment avant la fin de l'essai.
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Modal pour demander l'email */}
      <Dialog open={showEmailModal} onOpenChange={setShowEmailModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Crown className="h-6 w-6 text-purple-600" />
              Créer votre compte Pro
            </DialogTitle>
            <DialogDescription>
              Entrez votre adresse email pour recevoir le lien de confirmation et créer votre compte
            </DialogDescription>
          </DialogHeader>
          
          {checkoutSuccess ? (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <p className="font-medium text-green-900">Email envoyé !</p>
                    <p className="text-sm text-green-700 mt-1">
                      Un lien de confirmation a été envoyé à <strong>{checkoutEmail}</strong>
                    </p>
                    
                    {/* ✅ Afficher le lien cliquable en mode dev */}
                    {checkoutLink && (
                      <div className="mt-3 p-3 bg-white border border-green-300 rounded-lg">
                        <p className="text-xs font-semibold text-gray-700 mb-2">
                          🔗 Lien de checkout (mode développement) :
                        </p>
                        <div className="flex items-center gap-2">
                          <a
                            href={checkoutLink}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex-1 text-xs text-blue-600 hover:text-blue-800 underline break-all"
                          >
                            {checkoutLink}
                          </a>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              navigator.clipboard.writeText(checkoutLink);
                              toast({
                                title: "Lien copié !",
                                description: "Le lien a été copié dans le presse-papiers",
                              });
                            }}
                            className="text-xs px-2"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    )}
                    
                    <p className="text-sm text-green-700 mt-2">
                      {checkoutLink 
                        ? "Cliquez sur le lien ci-dessus pour finaliser votre inscription et votre paiement."
                        : "Cliquez sur le lien dans votre email pour finaliser votre inscription et votre paiement."
                      }
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-700">
                💡 <strong>Conseil :</strong> Vérifiez vos spams si vous ne recevez pas l'email dans les 2 minutes.
              </div>
              
              <Button
                onClick={() => {
                  setShowEmailModal(false);
                  setCheckoutSuccess(false);
                  setCheckoutEmail('');
                  setCheckoutLink(''); // Réinitialiser le lien
                }}
                className="w-full"
                variant="outline"
              >
                Fermer
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="checkout-email">Adresse email</Label>
                <Input
                  id="checkout-email"
                  type="email"
                  placeholder="votre@email.fr"
                  value={checkoutEmail}
                  onChange={(e) => setCheckoutEmail(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && checkoutEmail && !checkoutLoading) {
                      handlePreCheckout();
                    }
                  }}
                  disabled={checkoutLoading}
                />
              </div>
              
              {checkoutError && (
                <Alert variant="destructive">
                  <AlertDescription>{checkoutError}</AlertDescription>
                </Alert>
              )}
              
              <Button
                onClick={handlePreCheckout}
                disabled={!checkoutEmail || checkoutLoading}
                className="w-full bg-purple-600 hover:bg-purple-700 text-white"
              >
                {checkoutLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Envoi en cours...
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    Recevoir le lien de confirmation
                  </>
                )}
              </Button>
              
              <p className="text-xs text-gray-500 text-center">
                En continuant, vous acceptez nos conditions d'utilisation
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PricingPage;

