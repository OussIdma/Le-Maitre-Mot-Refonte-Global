/**
 * ProFeaturePage - Page upsell pour fonctionnalités Pro
 * 
 * Affiche une page propre "Fonctionnalité Pro" avec CTA upgrade
 * Utilisée quand un Free user accède à /mes-exercices ou /mes-fiches
 */

import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { 
  Crown, 
  Lock, 
  BookOpen, 
  FileText, 
  CheckCircle,
  ArrowRight
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useLogin } from "../contexts/LoginContext";

function ProFeaturePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { userEmail, isPro, isLoading } = useAuth();
  const { openLogin } = useLogin();
  
  // Déterminer quelle fonctionnalité est demandée
  const isMyExercises = location.pathname === '/mes-exercices';
  const isMySheets = location.pathname === '/mes-fiches';
  
  const featureName = isMyExercises ? "Bibliothèque d'exercices" : "Historique des fiches";
  const featureDescription = isMyExercises 
    ? "Sauvegardez et réutilisez vos exercices favoris"
    : "Consultez et modifiez toutes vos fiches créées";
  
  const features = [
    {
      icon: <BookOpen className="h-5 w-5" />,
      title: "Bibliothèque d'exercices",
      description: "Sauvegardez vos exercices générés pour les réutiliser facilement",
      proOnly: true
    },
    {
      icon: <FileText className="h-5 w-5" />,
      title: "Historique des fiches",
      description: "Accédez à toutes vos fiches créées, modifiez-les et réexportez-les",
      proOnly: true
    },
    {
      icon: <Crown className="h-5 w-5" />,
      title: "Exports illimités",
      description: "Générez et exportez autant de PDFs que vous voulez",
      proOnly: true
    }
  ];
  
  const handleUpgrade = () => {
    if (userEmail) {
      // User connecté mais Free -> rediriger vers pricing
      navigate('/pricing');
    } else {
      // User non connecté -> ouvrir modal login avec returnTo
      sessionStorage.setItem('postLoginRedirect', location.pathname);
      openLogin();
    }
  };
  
  // Si on charge encore ou si l'utilisateur est Pro, ne rien afficher (sera géré par la route)
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }
  
  if (isPro) {
    // Si Pro, rediriger vers la page normale
    if (isMyExercises) {
      navigate('/mes-exercices', { replace: true });
    } else if (isMySheets) {
      navigate('/mes-fiches', { replace: true });
    }
    return null;
  }
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-16">
        <div className="max-w-3xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <div className="flex items-center justify-center mb-4">
              <Lock className="h-12 w-12 text-blue-600 mr-3" />
              <Crown className="h-12 w-12 text-yellow-500" />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Fonctionnalité Pro
            </h1>
            <p className="text-xl text-gray-600 mb-2">
              {featureName}
            </p>
            <p className="text-gray-500">
              {featureDescription}
            </p>
          </div>
          
          {/* Main Card */}
          <Card className="shadow-lg border-2 border-blue-200">
            <CardHeader className="text-center bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
              <CardTitle className="text-2xl flex items-center justify-center">
                <Crown className="h-6 w-6 mr-2" />
                Passez à Le Maître Mot Pro
              </CardTitle>
              <CardDescription className="text-blue-50 mt-2">
                Débloquez toutes les fonctionnalités avancées
              </CardDescription>
            </CardHeader>
            <CardContent className="p-8">
              {/* Features List */}
              <div className="space-y-4 mb-8">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-start gap-4">
                    <div className="flex-shrink-0 mt-1 text-blue-600">
                      {feature.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900">{feature.title}</h3>
                        {feature.proOnly && (
                          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
                            Pro
                          </Badge>
                        )}
                      </div>
                      <p className="text-gray-600 text-sm">{feature.description}</p>
                    </div>
                  </div>
                ))}
              </div>
              
              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <Button
                  onClick={handleUpgrade}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                  size="lg"
                >
                  {userEmail ? (
                    <>
                      Passer à Pro
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  ) : (
                    <>
                      Se connecter / S'inscrire
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
                <Button
                  onClick={() => navigate('/generer')}
                  variant="outline"
                  size="lg"
                >
                  Continuer en mode gratuit
                </Button>
              </div>
              
              {/* Info Box */}
              <div className="mt-8 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-800">
                  <strong>Mode gratuit disponible :</strong> Vous pouvez toujours générer des exercices 
                  et composer des fiches. La bibliothèque et l'historique sont des fonctionnalités Pro 
                  pour vous aider à organiser votre travail.
                </p>
              </div>
            </CardContent>
          </Card>
          
          {/* Free Features Reminder */}
          <Card className="mt-8 shadow-md">
            <CardHeader>
              <CardTitle className="text-lg">Ce que vous pouvez faire en mode gratuit</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Générer des exercices</h4>
                    <p className="text-sm text-gray-600">Créez des exercices personnalisés</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Composer des fiches</h4>
                    <p className="text-sm text-gray-600">Sélectionnez et exportez vos exercices</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Exports limités</h4>
                    <p className="text-sm text-gray-600">3 exports PDF par jour</p>
                  </div>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-gray-900">Toutes les matières</h4>
                    <p className="text-sm text-gray-600">Accès à tous les niveaux et chapitres</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default ProFeaturePage;


