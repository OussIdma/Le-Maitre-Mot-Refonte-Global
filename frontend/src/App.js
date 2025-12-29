import React, { useState, useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import "./App.css";
import axios from "axios";
import { BrowserRouter, Routes, Route, useSearchParams, useNavigate, useLocation } from "react-router-dom";
import { Button } from "./components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Separator } from "./components/ui/separator";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./components/ui/dialog";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Alert, AlertDescription } from "./components/ui/alert";
import { BookOpen, FileText, Download, Shuffle, Loader2, GraduationCap, AlertCircle, CheckCircle, Crown, CreditCard, LogIn, LogOut, Mail, RefreshCw, Lock, KeyRound } from "lucide-react";
import { useToast } from "./hooks/use-toast";
import TemplateSettings from "./components/TemplateSettings";
import DocumentWizard from "./components/wizard/DocumentWizard";
import SheetBuilderPage from "./components/SheetBuilderPage";
import SheetBuilderPageV2 from "./components/SheetBuilderPageV2";
import MySheetsPage from "./components/MySheetsPage";
import MySheetsPageP31 from "./components/MySheetsPageP31";
import SheetEditPageP31 from "./components/SheetEditPageP31";
import MyExercisesPage from "./components/MyExercisesPage";
import ProSettingsPage from "./components/ProSettingsPage";
import ExerciseGeneratorPage from "./components/ExerciseGeneratorPage";
import CurriculumAdminSimplePage from "./components/admin/CurriculumAdminSimplePage";
import Curriculum6eAdminPage from "./components/admin/Curriculum6eAdminPage";
import ChapterExercisesAdminPage from "./components/admin/ChapterExercisesAdminPage";
import GeneratorTemplatesAdminPage from "./components/admin/GeneratorTemplatesAdminPage";
import LandingPage from "./components/LandingPage";
import NavBar from "./components/NavBar";
import CheckoutPage from "./components/CheckoutPage";
import ResetPasswordPage from "./components/ResetPasswordPage";
import PricingPage from "./components/PricingPage";
import UpgradeProModal, { trackPremiumEvent } from "./components/UpgradeProModal";
import { Toaster } from "./components/ui/toaster";
import { LoginProvider } from "./contexts/LoginContext";
import { SelectionProvider } from "./contexts/SelectionContext";
import GlobalLoginModal from "./components/GlobalLoginModal";
import SheetComposerPage from "./components/SheetComposerPage";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// P3.1: Redirection vers nouveau système "Mes fiches"
function RedirectToNewSheets() {
  const navigate = useNavigate();
  
  useEffect(() => {
    navigate('/mes-fiches', { replace: true });
  }, [navigate]);
  
  return (
    <div className="flex items-center justify-center min-h-screen">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  );
}

// Configure axios global timeout (15 seconds)
axios.defaults.timeout = 15000;

// Payment Success Component
function PaymentSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [checkingStatus, setCheckingStatus] = useState(true);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    if (!sessionId) {
      setError("Session ID manquant");
      setCheckingStatus(false);
      return;
    }

    pollPaymentStatus(sessionId);
  }, [searchParams]);

  const pollPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    const pollInterval = 2000; // 2 seconds

    if (attempts >= maxAttempts) {
      setError('Vérification du paiement expirée. Veuillez contacter le support.');
      setCheckingStatus(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/checkout/status/${sessionId}`);
      
      if (response.data.payment_status === 'paid') {
        setPaymentStatus('success');
        setCheckingStatus(false);
        
        // Redirect to main app after 3 seconds
        setTimeout(() => {
          navigate('/');
        }, 3000);
        return;
      } else if (response.data.status === 'expired') {
        setError('Session de paiement expirée. Veuillez réessayer.');
        setCheckingStatus(false);
        return;
      }

      // Continue polling if payment is still pending
      setTimeout(() => pollPaymentStatus(sessionId, attempts + 1), pollInterval);
    } catch (error) {
      console.error('Error checking payment status:', error);
      setError('Erreur lors de la vérification du paiement.');
      setCheckingStatus(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <GraduationCap className="mx-auto h-12 w-12 text-blue-600 mb-4" />
          <CardTitle>Le Maître Mot - Paiement</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          {checkingStatus ? (
            <div>
              <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600 mb-4" />
              <p>Vérification du paiement en cours...</p>
            </div>
          ) : error ? (
            <div>
              <AlertCircle className="mx-auto h-8 w-8 text-red-600 mb-4" />
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={() => navigate('/')} variant="outline">
                Retour à l'accueil
              </Button>
            </div>
          ) : paymentStatus === 'success' ? (
            <div>
              <CheckCircle className="mx-auto h-8 w-8 text-green-600 mb-4" />
              <h3 className="text-lg font-semibold mb-2">Paiement réussi !</h3>
              <p className="text-gray-600 mb-2">Votre abonnement Pro est maintenant actif</p>
              <p className="text-sm text-gray-500 mb-4">
                Vous avez accès aux exports illimités
              </p>
              <p className="text-sm text-gray-500">
                Redirection automatique vers l'accueil...
              </p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

// Payment Cancel Component
function PaymentCancel() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <GraduationCap className="mx-auto h-12 w-12 text-blue-600 mb-4" />
          <CardTitle>Le Maître Mot - Paiement Annulé</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          <AlertCircle className="mx-auto h-8 w-8 text-orange-600 mb-4" />
          <h3 className="text-lg font-semibold mb-2">Paiement annulé</h3>
          <p className="text-gray-600 mb-4">
            Votre paiement a été annulé. Vous pouvez réessayer à tout moment.
          </p>
          <Button onClick={() => navigate('/')} className="w-full">
            Retour à l'accueil
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

// Login Verification Component (for magic link)
function LoginVerify() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [verifying, setVerifying] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  // P0-A1: useRef guard prevents multiple calls (React StrictMode safe)
  const didCallRef = useRef(false);

  useEffect(() => {
    // P0-A1: Guard with useRef - prevents duplicate calls in StrictMode
    if (didCallRef.current) {
      console.log('[LoginVerify] Already called, skipping (StrictMode guard)');
      return;
    }

    const token = searchParams.get('token');
    if (!token) {
      setError("Token manquant");
      setVerifying(false);
      return;
    }

    // Mark as called BEFORE async call to prevent race conditions
    didCallRef.current = true;
    verifyLogin(token);
  }, [searchParams]); // P0-A1: Removed isVerifying from deps

  const verifyLogin = async (token) => {
    
    try {
      // Generate device ID
      const deviceId = localStorage.getItem('lemaitremot_device_id') || generateDeviceId();
      localStorage.setItem('lemaitremot_device_id', deviceId);

      console.log('🔐 Verifying login token...');
      const response = await axios.post(`${API}/auth/verify-login`, {
        token: token,
        device_id: deviceId
      }, {
        withCredentials: true // P0 UX: Inclure les cookies httpOnly
      });

      // Store session token and user info
      localStorage.setItem('lemaitremot_session_token', response.data.session_token);
      localStorage.setItem('lemaitremot_user_email', response.data.email);
      localStorage.setItem('lemaitremot_login_method', 'session');

      console.log('✅ Login verification successful');
      setSuccess(true);
      
      // P0 UX: Rediriger vers returnTo si présent
      const returnTo = sessionStorage.getItem('postLoginRedirect') || '/';
      sessionStorage.removeItem('postLoginRedirect'); // Nettoyer après utilisation
      
      setTimeout(() => {
        navigate(returnTo);
      }, 2000);

    } catch (error) {
      console.error('Error verifying login:', error);
      setError(error.response?.data?.detail || 'Erreur lors de la vérification');
    } finally {
      setVerifying(false);
    }
  };

  const generateDeviceId = () => {
    return 'device_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <GraduationCap className="h-8 w-8 text-blue-600 mr-2" />
            <h1 className="text-2xl font-bold text-gray-900">Le Maître Mot</h1>
          </div>
          <CardTitle>Connexion en cours</CardTitle>
        </CardHeader>
        <CardContent className="text-center">
          {verifying ? (
            <div className="space-y-4">
              <Loader2 className="h-8 w-8 text-blue-600 animate-spin mx-auto" />
              <p className="text-gray-600">Vérification de votre connexion...</p>
            </div>
          ) : error ? (
            <div className="space-y-4">
              <AlertCircle className="h-8 w-8 text-red-600 mx-auto" />
              <p className="text-red-600">{error}</p>
              <Button 
                onClick={() => navigate('/')}
                variant="outline"
                className="w-full"
              >
                Retour à l'accueil
              </Button>
            </div>
          ) : success ? (
            <div className="space-y-4">
              <CheckCircle className="h-8 w-8 text-green-600 mx-auto" />
              <p className="text-green-600">✅ Connexion réussie !</p>
              <p className="text-sm text-gray-500">Redirection en cours...</p>
            </div>
          ) : null}
        </CardContent>
      </Card>
    </div>
  );
}

function MainApp() {
  const { t } = useTranslation();
  const { openLogin, closeLogin } = useLogin();
  const [catalog, setCatalog] = useState([]);
  const [catalogStats, setCatalogStats] = useState(null); // Add catalog stats
  const [selectedMatiere, setSelectedMatiere] = useState("");
  const [selectedNiveau, setSelectedNiveau] = useState("");
  const [selectedChapitre, setSelectedChapitre] = useState("");
  const [typeDoc, setTypeDoc] = useState("exercices");
  const [difficulte, setDifficulte] = useState("moyen");
  const [nbExercices, setNbExercices] = useState(6);
  const [currentDocument, setCurrentDocument] = useState(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [openedDocument, setOpenedDocument] = useState(null);
  
  // API Error state management
  const [apiError, setApiError] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);
  
  // Guest and quota management (new logic)
  const [guestId, setGuestId] = useState("");
  const [quotaStatus, setQuotaStatus] = useState({ 
    exports_remaining: 3, 
    quota_exceeded: false,
    exports_used: 0,
    max_exports: 3
  });
  const [quotaLoaded, setQuotaLoaded] = useState(false);
  
  // Pro status management
  const [userEmail, setUserEmail] = useState("");
  const [isPro, setIsPro] = useState(false);
  const [proStatusChecked, setProStatusChecked] = useState(false);
  const [sessionToken, setSessionToken] = useState("");
  
  // Template states
  const [userTemplate, setUserTemplate] = useState(null);
  const [templateUpdated, setTemplateUpdated] = useState(false);
  
  // Payment modal
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [pricing, setPricing] = useState({});
  const [paymentEmail, setPaymentEmail] = useState("");
  const [paymentLoading, setPaymentLoading] = useState(false);
  // P0: État pour afficher le lien magique en mode dev
  const [devCheckoutLink, setDevCheckoutLink] = useState(null);
  
  // Login modal for existing Pro users
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginEmail, setLoginEmail] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginSuccess, setLoginSuccess] = useState(false);
  const [loginEmailSent, setLoginEmailSent] = useState(false);
  const [loginTab, setLoginTab] = useState("magic"); // "magic" or "password"
  
  // Reset password modal
  const [showResetModal, setShowResetModal] = useState(false);
  const [resetEmail, setResetEmail] = useState("");
  const [resetLoading, setResetLoading] = useState(false);
  
  const { toast } = useToast();
  
  // Export states
  const [exportingSubject, setExportingSubject] = useState(false);
  const [exportingSolution, setExportingSolution] = useState(false);
  
  // Export style selection
  const [exportStyles, setExportStyles] = useState({});
  const [selectedExportStyle, setSelectedExportStyle] = useState("classique");

  // Initialize guest ID and check Pro status
  useEffect(() => {
    let storedGuestId = localStorage.getItem('lemaitremot_guest_id');
    if (!storedGuestId) {
      storedGuestId = 'guest_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('lemaitremot_guest_id', storedGuestId);
    }
    setGuestId(storedGuestId);
    
    // Check if user has a stored email (Pro user)
    const storedEmail = localStorage.getItem('lemaitremot_user_email');
    if (storedEmail) {
      console.log('Found stored email, checking Pro status for:', storedEmail);
      setUserEmail(storedEmail);
      setPaymentEmail(storedEmail); // Pre-fill payment form
      checkProStatus(storedEmail);
    } else {
      setProStatusChecked(true);
    }
    
    console.log('Guest ID:', storedGuestId, 'Stored email:', storedEmail);
  }, []);

  const checkProStatus = async (email) => {
    try {
      const response = await axios.get(`${API}/user/status/${encodeURIComponent(email)}`);
      const isProUser = response.data.is_pro;
      
      setIsPro(isProUser);
      setProStatusChecked(true);
      
      console.log('Pro status check:', { email, isPro: isProUser });
      
      if (isProUser) {
        console.log('✅ User is Pro - unlimited exports');
      }
    } catch (error) {
      console.error('Error checking Pro status:', error);
      setIsPro(false);
      setProStatusChecked(true);
    }
  };

  const fetchCatalog = async () => {
    try {
      setApiError(null);
      const response = await axios.get(`${API}/catalog`);
      console.log('📚 Catalog received:', response.data.catalog?.length, 'matières');
      setCatalog(response.data.catalog);
      
      // Store catalog stats if available
      if (response.data.stats) {
        setCatalogStats(response.data.stats);
        console.log('📊 Curriculum stats loaded:', response.data.stats);
      }
      
      // Log roadmap info if available  
      if (response.data.roadmap) {
        console.log('🗺️ Roadmap info:', response.data.roadmap);
      }
    } catch (error) {
      console.error("Erreur lors du chargement du catalogue:", error);
      const errorMessage = error.code === 'ECONNABORTED' 
        ? "Le serveur met trop de temps à répondre. Veuillez réessayer."
        : "Impossible de charger les données. Vérifiez votre connexion internet.";
      setApiError(errorMessage);
    }
  };

  const fetchPricing = async () => {
    try {
      const response = await axios.get(`${API}/pricing`);
      setPricing(response.data.packages);
    } catch (error) {
      console.error("Erreur lors du chargement des prix:", error);
    }
  };

  const fetchQuotaStatus = async () => {
    // Pro users have unlimited exports
    if (isPro) {
      setQuotaStatus({
        exports_remaining: 999,
        quota_exceeded: false,
        exports_used: 0,
        max_exports: 999,
        is_pro: true
      });
      setQuotaLoaded(true);
      console.log('Pro user - unlimited quota set');
      return;
    }
    
    if (!guestId) return;
    try {
      const response = await axios.get(`${API}/quota/check?guest_id=${guestId}`);
      setQuotaStatus(response.data);
      setQuotaLoaded(true);
      console.log('Guest quota status:', response.data);
    } catch (error) {
      console.error("Erreur lors du chargement du quota:", error);
      // Set safe defaults on error
      setQuotaStatus({ 
        exports_remaining: 3, 
        quota_exceeded: false,
        exports_used: 0,
        max_exports: 3
      });
      setQuotaLoaded(true);
    }
  };

  const fetchDocuments = async () => {
    if (!guestId) return;
    try {
      const response = await axios.get(`${API}/documents?guest_id=${guestId}`);
      setDocuments(response.data.documents);
    } catch (error) {
      console.error("Erreur lors du chargement des documents:", error);
    }
  };

  const fetchExportStyles = async () => {
    try {
      const config = {};
      
      // Include session token if available
      if (sessionToken) {
        config.headers = {
          'X-Session-Token': sessionToken
        };
      }
      
      const response = await axios.get(`${API}/export/styles`, config);
      setExportStyles(response.data.styles || {});
      console.log('📊 Export styles loaded:', response.data);
      
      // If user is not Pro and current selection is Pro-only, reset to classique
      if (!response.data.user_is_pro && response.data.styles[selectedExportStyle]?.pro_only) {
        setSelectedExportStyle("classique");
      }
    } catch (error) {
      console.error("Erreur lors du chargement des styles d'export:", error);
      // Set safe default
      setExportStyles({
        "classique": {
          "name": "Classique",
          "description": "Style traditionnel élégant",
          "pro_only": false
        }
      });
    }
  };

  const generateDocument = async () => {
    if (!selectedMatiere || !selectedNiveau || !selectedChapitre) {
      alert("Veuillez sélectionner une matière, un niveau et un chapitre");
      return;
    }

    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/generate`, {
        matiere: selectedMatiere,
        niveau: selectedNiveau,
        chapitre: selectedChapitre,
        type_doc: typeDoc,
        difficulte: difficulte,
        nb_exercices: nbExercices,
        guest_id: guestId
      }, {
        timeout: 60000  // 60 seconds timeout (augmenté pour le nouveau système géométrique)
      });
      
      setCurrentDocument(response.data.document);
      await fetchDocuments();
    } catch (error) {
      console.error("Erreur lors de la génération:", error);
      if (error.code === 'ECONNABORTED') {
        alert("La génération prend trop de temps. Veuillez réessayer avec moins d'exercices.");
      } else {
        alert("Erreur lors de la génération du document");
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const exportPDF = async (exportType) => {
    if (!currentDocument) return;

    console.log('📄 Export PDF requested:', {
      exportType,
      isPro,
      hasSessionToken: !!sessionToken,
      userEmail,
      sessionTokenPreview: sessionToken ? sessionToken.substring(0, 20) + '...' : 'none'
    });

    const setLoading = exportType === 'sujet' ? setExportingSubject : setExportingSolution;
    setLoading(true);

    try {
      const requestData = {
        document_id: currentDocument.id,
        export_type: exportType,
        template_style: selectedExportStyle
      };
      
      // Pro users don't need guest_id, regular users do
      if (!isPro) {
        requestData.guest_id = guestId;
      }
      
      const requestConfig = {
        responseType: 'blob'
      };
      
      // Send session token if available (let backend determine Pro status)
      if (sessionToken) {
        requestConfig.headers = {
          'X-Session-Token': sessionToken
        };
        console.log('🔐 Sending session token with export request:', sessionToken.substring(0, 20) + '...');
      } else {
        console.log('⚠️ No session token available for export request');
      }

      console.log('📤 Making export request with config:', {
        url: `${API}/export`,
        hasHeaders: !!requestConfig.headers,
        requestData
      });

      const response = await axios.post(`${API}/export`, requestData, requestConfig);

      console.log('✅ Export response received:', {
        status: response.status,
        contentType: response.headers['content-type'],
        size: response.data.size
      });

      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `LeMaitremot_${currentDocument.type_doc}_${currentDocument.matiere}_${currentDocument.niveau}_${exportType}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      // Refresh quota
      await fetchQuotaStatus();
      
      // P2.3: Check if this was the 4th export (quota exhausted)
      const newQuota = await axios.get(`${API}/quota/check?guest_id=${guestId}`).catch(() => null);
      if (newQuota && newQuota.data.exports_remaining === 0 && !isPro) {
        trackPremiumEvent('premium_cta_clicked', { context: 'export', trigger: 'quota_exhausted' });
        setUpgradeContext('export');
        setShowUpgradeModal(true);
      }
      
    } catch (error) {
      console.error("Erreur lors de l'export:", error);
      
      // Handle session expiry/invalidity (someone else logged in)
      if (error.response?.status === 401 || error.response?.status === 402) {
        if (sessionToken && isPro) {
          console.log('Session invalidated - user may have been logged out by another device');
          // Clear ALL session data completely
          localStorage.removeItem('lemaitremot_session_token');
          localStorage.removeItem('lemaitremot_user_email');
          localStorage.removeItem('lemaitremot_login_method');
          
          setSessionToken("");
          setUserEmail("");
          setIsPro(false);
          setProStatusChecked(true);
          
          alert('Votre session a expiré ou a été fermée depuis un autre appareil. Veuillez vous reconnecter.');
          openLogin();
          return;
        } else if (error.response?.status === 402) {
          const errorData = error.response.data;
          if (errorData.action === "upgrade_required") {
            setShowPaymentModal(true);
          } else {
            alert("Quota d'exports dépassé");
          }
        }
      } else {
        alert("Erreur lors de l'export PDF");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleUpgradeClick = async (packageId) => {
    if (!paymentEmail || !paymentEmail.includes('@')) {
      alert('Veuillez saisir une adresse email valide');
      return;
    }
    
    setPaymentLoading(true);
    setDevCheckoutLink(null); // Reset
    
    try {
      // P0: Appeler pre-checkout pour obtenir le lien magique
      const preCheckoutResponse = await axios.post(`${API}/auth/pre-checkout`, {
        email: paymentEmail,
        package_id: packageId
      });
      
      // P0: Afficher le lien magique en mode dev
      if (preCheckoutResponse.data.dev_mode && preCheckoutResponse.data.checkout_link) {
        setDevCheckoutLink(preCheckoutResponse.data.checkout_link);
        toast({
          title: "🔗 Lien magique (mode dev)",
          description: "Le lien de confirmation est affiché ci-dessous pour copier.",
        });
        setPaymentLoading(false);
        return; // Ne pas continuer, l'utilisateur doit cliquer sur le lien
      }
      
      // En production, l'email est envoyé, on affiche un message
      toast({
        title: "Email envoyé",
        description: "Un lien de confirmation a été envoyé à votre adresse email.",
      });
      
    } catch (error) {
      console.error('Erreur lors du pre-checkout:', error);
      
      // Handle duplicate subscription error
      if (error.response?.status === 409) {
        const errorData = error.response.data;
        if (errorData.error === "already_subscribed") {
          alert(`⚠️ Abonnement existant détecté\n\n${errorData.message}\n\nSi vous souhaitez modifier votre abonnement, veuillez nous contacter.`);
        } else {
          alert('Cette adresse email dispose déjà d\'un abonnement actif.');
        }
      } else {
        // Toujours afficher un message neutre pour la sécurité
        toast({
          title: "Email envoyé",
          description: "Si un compte existe, un lien de confirmation a été envoyé.",
        });
      }
    } finally {
      setPaymentLoading(false);
    }
  };

  const varyExercise = async (exerciseIndex) => {
    if (!currentDocument) return;
    
    try {
      const response = await axios.post(`${API}/documents/${currentDocument.id}/vary/${exerciseIndex}`);
      const updatedDoc = { ...currentDocument };
      updatedDoc.exercises[exerciseIndex] = response.data.exercise;
      setCurrentDocument(updatedDoc);
    } catch (error) {
      console.error("Erreur lors de la variation:", error);
      alert("Erreur lors de la génération de la variation");
    }
  };

  const openRecentDocument = (doc) => {
    console.log('📂 Opening recent document:', doc);
    // Set the document as current
    setCurrentDocument(doc);
    // Flag it for the wizard to pre-fill and jump to step 3
    setOpenedDocument(doc);
  };

  const handleDocumentOpened = () => {
    // Clear the opened document flag after wizard processes it
    setOpenedDocument(null);
  };

  // Retry function for API errors
  const handleRetry = async () => {
    setIsRetrying(true);
    setApiError(null);
    try {
      await Promise.all([
        fetchCatalog(),
        fetchPricing(),
        fetchExportStyles(),
        guestId ? fetchQuotaStatus() : Promise.resolve()
      ]);
    } catch (error) {
      console.error("Retry failed:", error);
    } finally {
      setIsRetrying(false);
    }
  };

  // Initialize authentication on load and set up session monitoring
  useEffect(() => {
    initializeAuth();
    fetchCatalog();
    fetchPricing();
    fetchExportStyles();
    
    // Set up periodic session validation for Pro users
    const sessionCheckInterval = setInterval(() => {
      if (sessionToken) {
        validateSession(sessionToken, true); // silent validation
      }
    }, 60000); // Check every minute
    
    // Check if user just returned from payment
    const pendingPayment = localStorage.getItem('lemaitremot_pending_payment');
    if (pendingPayment && userEmail) {
      console.log('User returned from payment, checking Pro status...');
      localStorage.removeItem('lemaitremot_pending_payment');
      
      // Wait a bit for webhook processing, then check status
      setTimeout(() => {
        checkProStatus(userEmail);
      }, 3000);
    }
    
    // Cleanup interval on unmount
    return () => {
      clearInterval(sessionCheckInterval);
    };
  }, [sessionToken]);

  // P0 UX: Gérer returnTo depuis les query params
  useEffect(() => {
    const searchParams = new URLSearchParams(location.search);
    const returnTo = searchParams.get('returnTo');
    const shouldLogin = searchParams.get('login') === 'true';
    
    if (shouldLogin && returnTo) {
      sessionStorage.setItem('postLoginRedirect', returnTo);
      openLogin();
      // Nettoyer l'URL
      window.history.replaceState({}, '', location.pathname);
    }
  }, [location]);

  const initializeAuth = () => {
    // Check for session token (new method)
    const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
    const storedEmail = localStorage.getItem('lemaitremot_user_email');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    
    if (storedSessionToken && storedEmail && loginMethod === 'session') {
      setSessionToken(storedSessionToken);
      setUserEmail(storedEmail);
      validateSession(storedSessionToken);
    } else if (storedEmail && loginMethod !== 'session') {
      // Legacy method (email only)
      setUserEmail(storedEmail);
      checkProStatus(storedEmail);
    } else {
      setProStatusChecked(true);
    }
  };

  const validateSession = async (token, silent = false) => {
    try {
      const response = await axios.get(`${API}/auth/session/validate`, {
        headers: {
          'X-Session-Token': token
        }
      });
      
      setUserEmail(response.data.email);
      setIsPro(true);
      setProStatusChecked(true);
      
      // P0 UX: Si on vient d'une page protégée, rediriger vers returnTo
      if (!silent) {
        console.log('✅ Session valid - user is Pro:', response.data.email);
        
        // Vérifier si on doit rediriger après validation de session
        const returnTo = sessionStorage.getItem('postLoginRedirect');
        if (returnTo && window.location.pathname === '/') {
          sessionStorage.removeItem('postLoginRedirect');
          setTimeout(() => {
            navigate(returnTo);
          }, 100);
        }
      }
      
    } catch (error) {
      if (!silent) {
        console.error('Session validation failed:', error);
      }
      
      // Clear ALL invalid session data (complete cleanup)
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
      setSessionToken("");
      setUserEmail("");  // Added: Clear email state
      setIsPro(false);
      setProStatusChecked(true);
      
      // If it was session expired/invalid during active use (not silent check)
      if (error.response?.status === 401) {
        if (!silent) {
          console.log('Session expired - user needs to login again');
          alert('Votre session a expiré. Vous avez peut-être été déconnecté depuis un autre appareil.');
          openLogin();
        } else {
          console.log('Session invalidated silently (probably from another device)');
        }
      }
    }
  };

  const requestLogin = async (email) => {
    setLoginLoading(true);
    try {
      await axios.post(`${API}/auth/request-login`, {
        email: email
      });
      
      setLoginEmailSent(true);
      console.log('✅ Magic link sent to:', email);
      
      toast({
        title: "Email envoyé",
        description: "Si un compte existe, un email vous a été envoyé.",
      });
      
    } catch (error) {
      console.error('Error requesting login:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de l\'envoi du lien de connexion';
      toast({
        title: "Erreur",
        description: errorMsg,
        variant: "destructive"
      });
    } finally {
      setLoginLoading(false);
    }
  };

  // P2: Password login handler
  const handlePasswordLogin = async () => {
    if (!loginEmail || !loginPassword) return;
    
    setLoginLoading(true);
    try {
      // Generate device ID
      const deviceId = localStorage.getItem('lemaitremot_device_id') || generateDeviceId();
      localStorage.setItem('lemaitremot_device_id', deviceId);
      
      const response = await axios.post(`${API}/auth/login-password`, {
        email: loginEmail,
        password: loginPassword
      }, {
        headers: {
          'X-Device-ID': deviceId
        },
        withCredentials: true // P0 UX: Inclure les cookies httpOnly
      });
      
      // Store session token and user info
      const sessionToken = response.data.session_token;
      localStorage.setItem('lemaitremot_session_token', sessionToken);
      localStorage.setItem('lemaitremot_user_email', loginEmail);
      localStorage.setItem('lemaitremot_login_method', 'session');
      
      setSessionToken(sessionToken);
      setUserEmail(loginEmail);
      setIsPro(true);
      closeLogin();
      
      // P0 UX: Rediriger vers returnTo si présent
      const returnTo = sessionStorage.getItem('postLoginRedirect');
      if (returnTo) {
        sessionStorage.removeItem('postLoginRedirect'); // Nettoyer après utilisation
        setTimeout(() => {
          navigate(returnTo);
        }, 100);
      }
      
      toast({
        title: t('login.loginSuccess'),
        description: t('login.loginSuccessDesc'),
      });
      
      console.log('✅ Password login successful');
      
    } catch (error) {
      console.error('Error in password login:', error);
      const status = error.response?.status;
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la connexion';
      
      if (status === 400) {
        toast({
          title: t('login.passwordNotSet'),
          description: errorMsg,
          variant: "destructive"
        });
      } else if (status === 401) {
        toast({
          title: t('login.loginError'),
          description: t('login.incorrectCredentials'),
          variant: "destructive"
        });
      } else {
        toast({
          title: t('errors.generic'),
          description: errorMsg,
          variant: "destructive"
        });
      }
    } finally {
      setLoginLoading(false);
      setLoginPassword(""); // Clear password for security
    }
  };

  // P2: Reset password request handler
  const handleResetPasswordRequest = async () => {
    if (!resetEmail) return;
    
    setResetLoading(true);
    try {
      await axios.post(`${API}/auth/reset-password-request`, {
        email: resetEmail
      });
      
      toast({
        title: t('login.emailSent'),
        description: t('login.emailSentDesc'),
      });
      
      setShowResetModal(false);
      setResetEmail("");
      
    } catch (error) {
      console.error('Error requesting password reset:', error);
      // Always show success message (neutral response)
      toast({
        title: t('login.emailSent'),
        description: t('login.emailSentDesc'),
      });
      setShowResetModal(false);
      setResetEmail("");
    } finally {
      setResetLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (sessionToken) {
        await axios.post(`${API}/auth/logout`, {}, {
          headers: {
            'X-Session-Token': sessionToken
          }
        });
      }
      
      // Clear all auth data
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
      setSessionToken("");
      setUserEmail("");
      setIsPro(false);
      setProStatusChecked(true);
      
      console.log('✅ Logged out successfully');
      
    } catch (error) {
      console.error('Error during logout:', error);
      
      // Clear local data anyway
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
      setSessionToken("");
      setUserEmail("");
      setIsPro(false);
      setProStatusChecked(true);
    }
  };

  useEffect(() => {
    if (guestId && proStatusChecked) {
      fetchQuotaStatus();
      fetchDocuments();
      fetchExportStyles(); // Refresh styles when Pro status changes
    }
  }, [guestId, proStatusChecked, isPro]);

  const availableLevels = catalog.find(m => m.name === selectedMatiere)?.levels || [];
  const availableChapters = availableLevels.find(l => l.name === selectedNiveau)?.chapters || [];

  // Show error screen if API is unavailable
  if (apiError && catalog.length === 0) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <Card className="w-full max-w-md mx-4">
          <CardHeader className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <CardTitle className="text-xl text-gray-900">Service temporairement indisponible</CardTitle>
          </CardHeader>
          <CardContent className="text-center space-y-4">
            <p className="text-gray-600">{apiError}</p>
            <Button 
              onClick={handleRetry} 
              disabled={isRetrying}
              className="w-full"
            >
              {isRetrying ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Nouvelle tentative...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Réessayer
                </>
              )}
            </Button>
            <p className="text-xs text-gray-500">
              Si le problème persiste, veuillez réessayer dans quelques minutes.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-6">
            <GraduationCap className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">Le Maître Mot</h1>
          </div>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Générateur de documents pédagogiques personnalisés pour les enseignants français
          </p>
          
          {/* Link to Sheet Builder */}
          <div className="mt-4">
            <Button 
              variant="outline" 
              onClick={() => window.location.href = '/builder'}
              className="mx-auto"
            >
              <BookOpen className="h-4 w-4 mr-2" />
              Créer une fiche d'exercices
            </Button>
          </div>
          
          {/* Quota Status */}
          <div className="mt-4">
            {quotaLoaded ? (
              isPro ? (
                <div className="flex flex-col items-center space-y-3">
                  <Alert className="max-w-md mx-auto border-blue-200 bg-blue-50">
                    <Crown className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-800">
                      <strong>Le Maître Mot Pro :</strong> Exports illimités
                      {userEmail && <span className="block text-xs mt-1">({userEmail})</span>}
                    </AlertDescription>
                  </Alert>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={logout}
                    className="text-xs flex items-center"
                  >
                    <LogOut className="h-3 w-3 mr-1" />
                    Se déconnecter
                  </Button>
                </div>
              ) : quotaStatus.quota_exceeded ? (
                <div className="flex flex-col items-center space-y-3">
                  <Alert className="max-w-md mx-auto border-orange-200 bg-orange-50">
                    <AlertCircle className="h-4 w-4 text-orange-600" />
                    <AlertDescription className="text-orange-800">
                      <strong>Limite atteinte :</strong> 3 exports gratuits utilisés.
                      <div className="flex gap-2 mt-2">
                        <Button 
                          variant="link" 
                          className="p-0 h-auto text-orange-600 underline" 
                          onClick={() => setShowPaymentModal(true)}
                        >
                          Passer à Pro
                        </Button>
                        <span className="text-orange-600">ou</span>
                        <Button 
                          variant="link" 
                          className="p-0 h-auto text-orange-600 underline" 
                          onClick={() => openLogin()}
                        >
                          Se connecter
                        </Button>
                      </div>
                    </AlertDescription>
                  </Alert>
                </div>
              ) : (
                <div className="flex flex-col items-center space-y-3">
                  <Alert className="max-w-md mx-auto border-green-200 bg-green-50">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      <strong>Mode gratuit :</strong> {quotaStatus.exports_remaining} exports restants
                    </AlertDescription>
                  </Alert>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => openLogin()}
                    className="text-xs flex items-center"
                  >
                    <LogIn className="h-3 w-3 mr-1" />
                    Déjà Pro ? Se connecter
                  </Button>
                </div>
              )
            ) : (
              <Alert className="max-w-md mx-auto border-gray-200 bg-gray-50">
                <Loader2 className="h-4 w-4 text-gray-600 animate-spin" />
                <AlertDescription className="text-gray-700">
                  Chargement des quotas...
                </AlertDescription>
              </Alert>
            )}
          </div>
        </div>

        {/* Document Wizard */}
        <DocumentWizard 
          // Curriculum data
          matieres={catalog}  // Pass full catalog objects instead of just names
          niveaux={availableLevels.map(l => l.name)}
          chapitres={availableChapters}
          catalogStats={catalogStats?.roadmap}  // Pass catalog stats
          // Current selections
          selectedMatiere={selectedMatiere}
          selectedNiveau={selectedNiveau}
          selectedChapitre={selectedChapitre}
          typeDoc={typeDoc}
          difficulte={difficulte}
          nbExercices={nbExercices}
          // Handlers
          onMatiereChange={setSelectedMatiere}
          onNiveauChange={setSelectedNiveau}
          onChapitreChange={setSelectedChapitre}
          onTypeDocChange={setTypeDoc}
          onDifficulteChange={setDifficulte}
          onNbExercicesChange={setNbExercices}
          // Generation
          isGenerating={isGenerating}
          currentDocument={currentDocument}
          onGenerate={generateDocument}
          onVaryExercise={varyExercise}
          // Export
          exportStyles={exportStyles}
          selectedExportStyle={selectedExportStyle}
          onExportStyleChange={setSelectedExportStyle}
          exportingSubject={exportingSubject}
          exportingSolution={exportingSolution}
          onExportPDF={exportPDF}
          // Template settings
          isPro={isPro}
          sessionToken={sessionToken}
          onTemplateChange={(template) => {
            setUserTemplate(template);
            setTemplateUpdated(true);
          }}
          // Quota/Pro status
          quotaStatus={quotaStatus}
          quotaLoaded={quotaLoaded}
          userEmail={userEmail}
          onCheckProStatus={checkProStatus}
          onShowPaymentModal={() => setShowPaymentModal(true)}
          // Loading states
          isLoading={false}
          // Document loading
          openedDocument={openedDocument}
          onDocumentOpened={handleDocumentOpened}
        />

        {/* Recent Documents */}
        {documents.length > 0 && (
          <Card className="mt-8 shadow-lg border-0 bg-white/80 backdrop-blur-sm">
            <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-t-lg">
              <CardTitle>Documents récents</CardTitle>
              <CardDescription className="text-purple-50">
                Vos derniers documents générés
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {documents.slice(0, 6).map((doc) => (
                  <Card key={doc.id} className="cursor-pointer hover:shadow-md transition-shadow border border-gray-200">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900">{doc.type_doc}</h4>
                        <Badge variant="outline" className="text-xs">{doc.difficulte}</Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-1">{doc.matiere} - {doc.niveau}</p>
                      <p className="text-xs text-gray-500 mb-3">{doc.chapitre}</p>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-gray-400">
                          {doc.nb_exercices} exercices
                        </span>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => openRecentDocument(doc)}
                          className="text-blue-600 hover:text-blue-700"
                        >
                          Ouvrir
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Payment Modal */}
        <Dialog open={showPaymentModal} onOpenChange={(open) => {
          setShowPaymentModal(open);
          if (!open) {
            setDevCheckoutLink(null); // Reset quand le modal se ferme
          }
        }}>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle className="flex items-center text-center">
                <Crown className="mr-2 h-6 w-6 text-yellow-600" />
                Passez à Le Maître Mot Pro
              </DialogTitle>
              <DialogDescription className="text-center">
                Débloquez les exports illimités et accédez à toutes les fonctionnalités
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-6">
              {/* Email Input */}
              <div className="space-y-2">
                <Label htmlFor="payment-email">Adresse email *</Label>
                <Input
                  id="payment-email"
                  type="email"
                  placeholder="votre@email.fr"
                  value={paymentEmail}
                  onChange={(e) => setPaymentEmail(e.target.value)}
                  required
                />
                <p className="text-xs text-gray-500">
                  Cette adresse sera utilisée pour gérer votre abonnement
                </p>
              </div>
              
              {/* Monthly Plan */}
              {pricing.monthly && (
                <Card className="border-2 border-blue-200 hover:border-blue-400 transition-colors cursor-pointer">
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">Abonnement Mensuel</h3>
                        <p className="text-sm text-gray-600">Parfait pour essayer</p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-blue-600">{pricing.monthly.amount}€</div>
                        <div className="text-sm text-gray-500">par mois</div>
                      </div>
                    </div>
                    <ul className="space-y-2 mb-4 text-sm text-gray-700">
                      <li className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        Exports PDF illimités
                      </li>
                      <li className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        Génération d'exercices sans limite
                      </li>
                      <li className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        Toutes les matières et niveaux
                      </li>
                    </ul>
                    <Button 
                      onClick={() => handleUpgradeClick('monthly')}
                      disabled={!paymentEmail || paymentLoading}
                      className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
                    >
                      {paymentLoading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <CreditCard className="mr-2 h-4 w-4" />
                      )}
                      Choisir Mensuel
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* Yearly Plan */}
              {pricing.yearly && (
                <Card className="border-2 border-green-200 hover:border-green-400 transition-colors cursor-pointer relative">
                  <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                    <Badge className="bg-green-600 text-white px-3 py-1">Économisez 16%</Badge>
                  </div>
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-4">
                      <div>
                        <h3 className="text-lg font-bold text-gray-900">Abonnement Annuel</h3>
                        <p className="text-sm text-gray-600">Le meilleur rapport qualité/prix</p>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-green-600">{pricing.yearly.amount}€</div>
                        <div className="text-sm text-gray-500">par an</div>
                        <div className="text-xs text-green-600">Soit {(pricing.yearly.amount / 12).toFixed(2)}€/mois</div>
                      </div>
                    </div>
                    <ul className="space-y-2 mb-4 text-sm text-gray-700">
                      <li className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        Exports PDF illimités
                      </li>
                      <li className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        Génération d'exercices sans limite
                      </li>
                      <li className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        Toutes les matières et niveaux
                      </li>
                      <li className="flex items-center">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                        Économisez 20€ par rapport au mensuel
                      </li>
                    </ul>
                    <Button 
                      onClick={() => handleUpgradeClick('yearly')}
                      disabled={!paymentEmail || paymentLoading}
                      className="w-full bg-green-600 hover:bg-green-700 disabled:opacity-50"
                    >
                      {paymentLoading ? (
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      ) : (
                        <Crown className="mr-2 h-4 w-4" />
                      )}
                      Choisir Annuel
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* P0: Afficher le lien magique en mode dev */}
              {devCheckoutLink && (
                <div className="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded-md">
                  <p className="text-sm font-medium text-blue-900">
                    🔗 Lien magique (mode développement)
                  </p>
                  <div className="flex items-center gap-2">
                    <Input
                      value={devCheckoutLink}
                      readOnly
                      className="flex-1 font-mono text-xs bg-white"
                    />
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        navigator.clipboard.writeText(devCheckoutLink);
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
                    Cliquez sur le lien ou copiez-le pour continuer le checkout.
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      window.open(devCheckoutLink, '_blank');
                    }}
                    className="w-full"
                  >
                    Ouvrir le lien
                  </Button>
                </div>
              )}

              <div className="text-center text-xs text-gray-500 mt-4">
                Paiement sécurisé par Stripe • Annulation possible à tout moment
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Login Modal maintenant géré globalement via GlobalLoginModal */}
        
        {/* Reset Password Modal */}
        <Dialog open={showResetModal} onOpenChange={(open) => {
          setShowResetModal(open);
          if (!open) {
            setResetEmail("");
            setResetLoading(false);
          }
        }}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center text-center">
                <Lock className="mr-2 h-6 w-6 text-blue-600" />
                {t('login.forgotPassword')}
              </DialogTitle>
              <DialogDescription className="text-center">
                {t('login.resetPasswordDescription')}
              </DialogDescription>
            </DialogHeader>
            
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="reset-email">{t('login.emailAddress')}</Label>
                <Input
                  id="reset-email"
                  type="email"
                  placeholder={t('login.emailPlaceholder')}
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && resetEmail && !resetLoading) {
                      handleResetPasswordRequest();
                    }
                  }}
                />
              </div>
              
              <Button 
                onClick={handleResetPasswordRequest}
                disabled={!resetEmail || resetLoading}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                {resetLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {t('actions.sendingEmail')}
                  </>
                ) : (
                  <>
                    <Mail className="mr-2 h-4 w-4" />
                    {t('login.sendEmail')}
                  </>
                )}
              </Button>
              
              <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-700">
                {t('login.resetInfo')}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

// Component wrapper avec NavBar
function AppWithNav({ children, showNav = true }) {
  if (!showNav) {
    return <>{children}</>;
  }
  return (
    <>
      <NavBar />
      {children}
    </>
  );
}

// Redirect component pour normaliser les routes
function RedirectToGenerer() {
  const navigate = useNavigate();
  const location = useLocation();

  React.useEffect(() => {
    // Normaliser les variations de casse
    const normalizedPath = location.pathname.toLowerCase();
    if (normalizedPath === '/générer' || normalizedPath === '/generer' || normalizedPath === '/Générer') {
      navigate('/generer', { replace: true });
      return;
    }
    
    // Rediriger toute route inconnue vers /generer
    navigate('/generer', { replace: true });
  }, [location.pathname, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-600 mb-4">Redirection en cours...</p>
      </div>
    </div>
  );
}

// 404 Component
function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <GraduationCap className="mx-auto h-12 w-12 text-blue-600 mb-4" />
          <CardTitle>Page non trouvée</CardTitle>
          <CardDescription>
            La page que vous recherchez n'existe pas.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <Button
            onClick={() => navigate('/generer')}
            className="w-full"
          >
            Aller au générateur
          </Button>
          <Button
            variant="outline"
            onClick={() => navigate('/')}
            className="w-full"
          >
            Retour à l'accueil
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <SelectionProvider>
      <LoginProvider>
        <Toaster />
        <GlobalUpgradeModal />
        <GlobalLoginModal />
        <Routes>
        {/* Routes spéciales sans NavBar */}
        <Route path="/success" element={<PaymentSuccess />} />
        <Route path="/cancel" element={<PaymentCancel />} />
        <Route path="/login/verify" element={<LoginVerify />} />
        <Route path="/checkout" element={<CheckoutPage />} /> {/* P0: Secure checkout page */}
        <Route path="/reset-password" element={<ResetPasswordPage />} /> {/* P2: Reset password page */}
        <Route path="/pricing" element={<PricingPage />} /> {/* P2.3: Pricing page */}
        
        {/* Routes principales avec NavBar */}
        <Route path="/" element={
          <AppWithNav>
            <LandingPage />
          </AppWithNav>
        } />
        
        <Route path="/generer" element={
          <AppWithNav>
            <ExerciseGeneratorPage />
          </AppWithNav>
        } />
        
        {/* Normalisation des variations de casse */}
        <Route path="/générer" element={<RedirectToGenerer />} />
        <Route path="/Générer" element={<RedirectToGenerer />} />
        
        {/* Route legacy /generate redirige vers /generer */}
        <Route path="/generate" element={<RedirectToGenerer />} />
        
        {/* Routes existantes avec NavBar */}
        {/* P3.1: Redirection ancien builder vers nouveau système */}
        <Route path="/builder" element={
          <AppWithNav>
            <RedirectToNewSheets />
          </AppWithNav>
        } />
        <Route path="/builder/:sheetId" element={
          <AppWithNav>
            <RedirectToNewSheets />
          </AppWithNav>
        } />
        {/* PR7: Nouveau builder simplifié "3 clics" */}
        <Route path="/builder-v2" element={
          <AppWithNav>
            <SheetBuilderPageV2 />
          </AppWithNav>
        } />
        {/* Legacy route - redirige vers nouveau */}
        <Route path="/sheets" element={
          <AppWithNav>
            <RedirectToNewSheets />
          </AppWithNav>
        } />
        {/* P3.1: Nouveau système "Mes fiches" */}
        <Route path="/mes-fiches" element={
          <AppWithNav>
            <MySheetsPageP31 />
          </AppWithNav>
        } />
        <Route path="/mes-fiches/:sheet_uid" element={
          <AppWithNav>
            <SheetEditPageP31 />
          </AppWithNav>
        } />
        <Route path="/mes-exercices" element={
          <AppWithNav>
            <MyExercisesPage />
          </AppWithNav>
        } /> {/* P3.0: Bibliothèque d'exercices */}
        <Route path="/pro/settings" element={
          <AppWithNav>
            <ProSettingsPage />
          </AppWithNav>
        } />
        
        {/* Routes admin avec NavBar */}
        <Route path="/admin/curriculum" element={
          <AppWithNav>
            <Curriculum6eAdminPage />
          </AppWithNav>
        } />
        <Route path="/admin/curriculum/:chapterCode/exercises" element={
          <AppWithNav>
            <ChapterExercisesAdminPage />
          </AppWithNav>
        } />
        <Route path="/admin/templates" element={
          <AppWithNav>
            <GeneratorTemplatesAdminPage />
          </AppWithNav>
        } />
        
        {/* Route legacy MainApp (simplifiée) - redirige vers /generer */}
        <Route path="/legacy" element={
          <AppWithNav>
            <MainApp />
          </AppWithNav>
        } />
        
        {/* Route composer de fiche */}
        <Route path="/fiches/nouvelle" element={
          <AppWithNav>
            <SheetComposerPage />
          </AppWithNav>
        } />

        {/* Catch-all: rediriger vers /generer */}
        <Route path="/*" element={<RedirectToGenerer />} />
      </Routes>
      </LoginProvider>
      </SelectionProvider>
    </BrowserRouter>
  );
}

// P2.3: Global Upgrade Pro Modal (outside router for global access)
function GlobalUpgradeModal() {
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [upgradeContext, setUpgradeContext] = useState('general');

  // Listen for custom events to open modal
  useEffect(() => {
    const handleOpenModal = (event) => {
      setUpgradeContext(event.detail?.context || 'general');
      setShowUpgradeModal(true);
    };
    
    window.addEventListener('openUpgradeModal', handleOpenModal);
    return () => window.removeEventListener('openUpgradeModal', handleOpenModal);
  }, []);

  return (
    <UpgradeProModal
      isOpen={showUpgradeModal}
      onClose={() => setShowUpgradeModal(false)}
      context={upgradeContext}
    />
  );
}

export default App;