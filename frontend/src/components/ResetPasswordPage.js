import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Alert, AlertDescription } from './ui/alert';
import { Loader2, Lock, CheckCircle, AlertCircle, KeyRound } from 'lucide-react';
import { useToast } from '../hooks/use-toast';

const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const ResetPasswordPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const token = searchParams.get('token');
  
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState({
    length: false,
    uppercase: false,
    digit: false,
    match: false
  });

  useEffect(() => {
    if (!token) {
      toast({
        title: "Token manquant",
        description: "Le lien de réinitialisation est invalide.",
        variant: "destructive"
      });
      navigate('/');
    }
  }, [token, navigate, toast]);

  // P2: Live password validation
  useEffect(() => {
    if (newPassword) {
      setPasswordErrors({
        length: newPassword.length >= 8,
        uppercase: /[A-Z]/.test(newPassword),
        digit: /\d/.test(newPassword),
        match: newPassword === confirmPassword && confirmPassword.length > 0
      });
    } else {
      setPasswordErrors({
        length: false,
        uppercase: false,
        digit: false,
        match: false
      });
    }
  }, [newPassword, confirmPassword]);

  const handleResetPassword = async () => {
    if (!token) return;
    
    // Validate password strength
    if (newPassword.length < 8) {
      toast({
        title: "Mot de passe trop court",
        description: "Le mot de passe doit contenir au moins 8 caractères.",
        variant: "destructive"
      });
      return;
    }
    
    if (!/[A-Z]/.test(newPassword)) {
      toast({
        title: "Mot de passe invalide",
        description: "Le mot de passe doit contenir au moins une majuscule.",
        variant: "destructive"
      });
      return;
    }
    
    if (!/\d/.test(newPassword)) {
      toast({
        title: "Mot de passe invalide",
        description: "Le mot de passe doit contenir au moins un chiffre.",
        variant: "destructive"
      });
      return;
    }
    
    if (newPassword !== confirmPassword) {
      toast({
        title: "Mots de passe différents",
        description: "Les mots de passe ne correspondent pas.",
        variant: "destructive"
      });
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(`${API}/api/auth/reset-password-confirm`, {
        token: token,
        new_password: newPassword
      });
      
      setSuccess(true);
      toast({
        title: "Mot de passe mis à jour",
        description: "Votre mot de passe a été réinitialisé avec succès.",
      });
      
      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/');
      }, 2000);
      
    } catch (error) {
      console.error('Error resetting password:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la réinitialisation';
      toast({
        title: "Erreur",
        description: errorMsg,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return null; // Will redirect
  }

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <CardTitle>Mot de passe mis à jour</CardTitle>
            <CardDescription>
              Votre mot de passe a été réinitialisé avec succès.
            </CardDescription>
          </CardHeader>
          <CardContent className="text-center">
            <p className="text-sm text-gray-600 mb-4">
              Vous allez être redirigé vers la page de connexion...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <Lock className="h-8 w-8 text-blue-600" />
          </div>
          <CardTitle>Réinitialiser votre mot de passe</CardTitle>
          <CardDescription>
            Définissez un nouveau mot de passe pour votre compte Pro
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="new-password">Nouveau mot de passe</Label>
            <Input
              id="new-password"
              type="password"
              placeholder="••••••••"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && newPassword && confirmPassword && !loading) {
                  handleResetPassword();
                }
              }}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="confirm-password">Confirmer le mot de passe</Label>
            <Input
              id="confirm-password"
              type="password"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && newPassword && confirmPassword && !loading) {
                  handleResetPassword();
                }
              }}
            />
          </div>
          
          {/* Password validation indicators */}
          {newPassword && (
            <div className="space-y-2 text-sm">
              <div className={`flex items-center gap-2 ${passwordErrors.length ? 'text-green-600' : 'text-gray-500'}`}>
                {passwordErrors.length ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <span>Minimum 8 caractères</span>
              </div>
              <div className={`flex items-center gap-2 ${passwordErrors.uppercase ? 'text-green-600' : 'text-gray-500'}`}>
                {passwordErrors.uppercase ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <span>Au moins 1 majuscule</span>
              </div>
              <div className={`flex items-center gap-2 ${passwordErrors.digit ? 'text-green-600' : 'text-gray-500'}`}>
                {passwordErrors.digit ? (
                  <CheckCircle className="h-4 w-4" />
                ) : (
                  <AlertCircle className="h-4 w-4" />
                )}
                <span>Au moins 1 chiffre</span>
              </div>
              {confirmPassword && (
                <div className={`flex items-center gap-2 ${passwordErrors.match ? 'text-green-600' : 'text-red-600'}`}>
                  {passwordErrors.match ? (
                    <CheckCircle className="h-4 w-4" />
                  ) : (
                    <AlertCircle className="h-4 w-4" />
                  )}
                  <span>Les mots de passe correspondent</span>
                </div>
              )}
            </div>
          )}
          
          <Button 
            onClick={handleResetPassword}
            disabled={loading || !passwordErrors.length || !passwordErrors.uppercase || !passwordErrors.digit || !passwordErrors.match}
            className="w-full bg-blue-600 hover:bg-blue-700"
          >
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Réinitialisation en cours...
              </>
            ) : (
              <>
                <KeyRound className="mr-2 h-4 w-4" />
                Réinitialiser le mot de passe
              </>
            )}
          </Button>
          
          <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-700">
            💡 <strong>Conseil :</strong> Vous pouvez toujours utiliser le lien magique pour vous connecter.
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ResetPasswordPage;







