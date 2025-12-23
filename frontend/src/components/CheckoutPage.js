/**
 * CheckoutPage - P0 Secure Checkout Flow
 * 
 * User arrives here via magic link from email (pre-checkout).
 * Flow:
 * 1. Verify token (creates session)
 * 2. Display package summary
 * 3. User confirms → Create Stripe checkout session
 * 4. Redirect to Stripe
 */

import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, CheckCircle, AlertCircle, Crown, Mail } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const API = `${BACKEND_URL}/api`;

const PRICING_PACKAGES = {
  monthly: {
    name: "Abonnement Mensuel",
    amount: 9.99,
    currency: "€",
    duration: "mois",
    description: "Accès illimité pendant 1 mois"
  },
  yearly: {
    name: "Abonnement Annuel",
    amount: 99.00,
    currency: "€",
    duration: "an",
    description: "Accès illimité pendant 1 an - Économisez 16%"
  }
};

function CheckoutPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(true);
  const [error, setError] = useState(null);
  const [tokenValid, setTokenValid] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [packageId, setPackageId] = useState('');
  const [creatingCheckout, setCreatingCheckout] = useState(false);
  
  useEffect(() => {
    const token = searchParams.get('token');
    if (!token) {
      setError('Lien invalide ou expiré');
      setVerifying(false);
      setLoading(false);
      return;
    }
    
    verifyToken(token);
  }, [searchParams]);
  
  const verifyToken = async (token) => {
    try {
      // Generate device ID
      const deviceId = localStorage.getItem('lemaitremot_device_id') || generateDeviceId();
      localStorage.setItem('lemaitremot_device_id', deviceId);
      
      // ✅ Utiliser le nouvel endpoint pour vérifier le token de checkout
      const response = await axios.post(`${API}/auth/verify-checkout-token`, {
        token: token,
        device_id: deviceId
      }, {
        withCredentials: true // Important pour recevoir le cookie httpOnly
      });
      
      // Store session token
      localStorage.setItem('lemaitremot_session_token', response.data.session_token);
      localStorage.setItem('lemaitremot_user_email', response.data.email);
      localStorage.setItem('lemaitremot_login_method', 'session');
      
      setUserEmail(response.data.email);
      setTokenValid(true);
      
      // ✅ Utiliser le package_id du token metadata
      const pkgId = response.data.package_id || searchParams.get('package') || 'monthly';
      setPackageId(pkgId);
      
      setVerifying(false);
      setLoading(false);
      
    } catch (error) {
      console.error('Error verifying checkout token:', error);
      
      if (error.response?.status === 400) {
        setError('Lien invalide ou expiré. Veuillez demander un nouveau lien.');
      } else if (error.response?.status === 403) {
        setError('Votre abonnement a expiré. Veuillez contacter le support.');
      } else {
        setError('Erreur lors de la vérification. Veuillez réessayer.');
      }
      
      setVerifying(false);
      setLoading(false);
    }
  };
  
  const generateDeviceId = () => {
    return 'dev-' + Math.random().toString(36).substr(2, 9) + '-' + Date.now();
  };
  
  const handleProceedToPayment = async () => {
    setCreatingCheckout(true);
    setError(null);
    
    try {
      const sessionToken = localStorage.getItem('lemaitremot_session_token');
      
      if (!sessionToken) {
        throw new Error('Session expirée. Veuillez recommencer.');
      }
      
      // Create Stripe checkout session (email from session, not body)
      const response = await axios.post(
        `${API}/checkout/session`,
        {
          package_id: packageId,
          origin_url: window.location.origin
        },
        {
          headers: {
            'X-Session-Token': sessionToken
          }
        }
      );
      
      // Redirect to Stripe Checkout
      window.location.href = response.data.url;
      
    } catch (error) {
      console.error('Error creating checkout session:', error);
      
      if (error.response?.status === 401) {
        setError('Session expirée. Veuillez demander un nouveau lien de confirmation.');
      } else if (error.response?.status === 409) {
        const detail = error.response.data.detail;
        setError(detail.message || 'Vous avez déjà un abonnement actif.');
      } else {
        setError('Erreur lors de la création de la session de paiement. Veuillez réessayer.');
      }
      
      setCreatingCheckout(false);
    }
  };
  
  const handleResendLink = () => {
    navigate('/pricing');
  };
  
  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <p className="text-gray-600">Vérification de votre email...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  // Error state
  if (!tokenValid) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center gap-2">
              <AlertCircle className="h-6 w-6 text-red-600" />
              <CardTitle>Lien invalide ou expiré</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
            
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Les liens de confirmation sont valides pendant 15 minutes pour des raisons de sécurité.
              </p>
              
              <Button onClick={handleResendLink} className="w-full">
                <Mail className="mr-2 h-4 w-4" />
                Demander un nouveau lien
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }
  
  // Success state - ready for payment
  const packageInfo = PRICING_PACKAGES[packageId];
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader>
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-6 w-6 text-green-600" />
            <span className="text-sm text-green-600 font-medium">Email vérifié</span>
          </div>
          <CardTitle className="flex items-center gap-2">
            <Crown className="h-6 w-6 text-purple-600" />
            Finalisez votre abonnement Pro
          </CardTitle>
          <CardDescription>
            Vous êtes à une étape de débloquer toutes les fonctionnalités premium
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* User email confirmed */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <Mail className="h-5 w-5 text-green-600 mt-0.5" />
              <div>
                <p className="font-medium text-green-900">Email confirmé</p>
                <p className="text-sm text-green-700">{userEmail}</p>
              </div>
            </div>
          </div>
          
          {/* Package summary */}
          <div className="border rounded-lg p-6">
            <h3 className="text-lg font-semibold mb-4">Récapitulatif</h3>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Formule</span>
                <span className="font-medium">{packageInfo.name}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Durée</span>
                <span className="font-medium">1 {packageInfo.duration}</span>
              </div>
              
              <div className="border-t pt-3 flex justify-between items-baseline">
                <span className="text-gray-900 font-medium">Total</span>
                <div className="text-right">
                  <span className="text-2xl font-bold text-gray-900">
                    {packageInfo.amount}{packageInfo.currency}
                  </span>
                  <span className="text-gray-600 text-sm ml-1">/ {packageInfo.duration}</span>
                </div>
              </div>
            </div>
          </div>
          
          {/* Features included */}
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h4 className="font-semibold text-purple-900 mb-3">Inclus dans votre abonnement :</h4>
            <ul className="space-y-2 text-sm text-purple-800">
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Générateurs premium illimités (variantes A/B/C)</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Exports PDF sans watermark</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Templates personnalisables</span>
              </li>
              <li className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>Support prioritaire</span>
              </li>
            </ul>
          </div>
          
          {/* Error display */}
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Payment button */}
          <div className="space-y-3">
            <Button 
              onClick={handleProceedToPayment}
              disabled={creatingCheckout}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white"
              size="lg"
            >
              {creatingCheckout ? (
                <>
                  <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  Redirection vers le paiement...
                </>
              ) : (
                <>
                  <Crown className="mr-2 h-5 w-5" />
                  Procéder au paiement sécurisé
                </>
              )}
            </Button>
            
            <p className="text-xs text-gray-500 text-center">
              🔒 Paiement sécurisé par Stripe • Annulation possible à tout moment
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default CheckoutPage;

