import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import Header from './Header';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Upload, 
  Crown, 
  Palette, 
  Image as ImageIcon, 
  User, 
  Building, 
  Calendar, 
  FileText,
  Lock,
  Loader2,
  ArrowLeft,
  Save,
  CheckCircle,
  Monitor,
  Smartphone,
  Tablet,
  LogOut,
  Shield,
  KeyRound
} from 'lucide-react';
import { useToast } from '../hooks/use-toast';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from './ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ProSettingsPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Récupérer le contexte de navigation (d'où vient l'utilisateur)
  // Priorité : query params (pour les nouveaux onglets) > state (pour navigation react-router)
  const queryParams = new URLSearchParams(location.search);
  const fromQuery = queryParams.get('from');
  const sheetIdQuery = queryParams.get('sheetId');
  
  const from = fromQuery || location.state?.from;
  const sheetId = sheetIdQuery || location.state?.sheetId;
  
  // Auth states
  const [sessionToken, setSessionToken] = useState('');
  const [userEmail, setUserEmail] = useState('');
  const [isPro, setIsPro] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  // Form states
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [professorName, setProfessorName] = useState('');
  const [schoolName, setSchoolName] = useState('');
  const [schoolYear, setSchoolYear] = useState('');
  const [footerText, setFooterText] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('classique');
  
  // P1.2: Sessions management states
  const [sessions, setSessions] = useState([]);
  const [sessionsLoading, setSessionsLoading] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  
  const { toast } = useToast();
  
  // Template styles
  const [templateStyles, setTemplateStyles] = useState({
    classique: { name: 'Classique', description: 'Style traditionnel élégant', preview_colors: { primary: '#2563eb', accent: '#7c3aed' } },
    academique: { name: 'Académique', description: 'Style professionnel et sobre', preview_colors: { primary: '#1e40af', accent: '#4b5563' } }
  });

  // Initialize auth
  useEffect(() => {
    const token = localStorage.getItem('lemaitremot_session_token');
    const email = localStorage.getItem('lemaitremot_user_email');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    
    setSessionToken(token || '');
    setUserEmail(email || '');
    
    if (!token || !email || loginMethod !== 'session') {
      setIsPro(false);
      setLoading(false);
      return;
    }
    
    // Validate session
    validateAndLoadConfig(token, email);
  }, []);

  const validateAndLoadConfig = async (token, email) => {
    try {
      // Validate session
      const validationRes = await axios.get(`${API}/auth/session/validate`, {
        headers: { 'X-Session-Token': token }
      });
      
      setIsPro(true);
      
      // Load config
      await loadUserConfig(token);
      await loadTemplateStyles();
      
      // P1.2: Load sessions
      await loadSessions(token);
      
    } catch (error) {
      console.error('Session validation failed:', error);
      setIsPro(false);
      
      // Clear invalid session
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
    } finally {
      setLoading(false);
    }
  };

  const loadUserConfig = async (token) => {
    try {
      const response = await axios.get(`${API}/mathalea/pro/config`, {
        headers: { 'X-Session-Token': token }
      });
      
      const config = response.data;
      setProfessorName(config.professor_name || '');
      setSchoolName(config.school_name || '');
      setSchoolYear(config.school_year || '2024-2025');
      setFooterText(config.footer_text || '');
      setSelectedStyle(config.template_style || config.template_choice || 'classique');
      
      if (config.logo_url) {
        const logoUrl = config.logo_url.startsWith('http') 
          ? config.logo_url 
          : `${API}${config.logo_url}`;
        setLogoPreview(logoUrl);
      }
      
      console.log('✅ Config Pro chargée:', config);
    } catch (error) {
      console.error('Error loading config:', error);
    }
  };

  const loadTemplateStyles = async () => {
    try {
      const response = await axios.get(`${API}/template/styles`);
      if (response.data.styles) {
        setTemplateStyles(response.data.styles);
      }
    } catch (error) {
      console.error('Error loading template styles:', error);
    }
  };

  const handleLogoUpload = (file) => {
    if (file && file.size <= 2 * 1024 * 1024) { // 2MB limit
      setLogoFile(file);
      
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    } else {
      alert('Le logo doit faire moins de 2 Mo');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        handleLogoUpload(file);
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleSave = async () => {
    if (!sessionToken) return;
    
    setSaving(true);
    setSaveSuccess(false);
    
    try {
      let uploadedLogoUrl = logoPreview;
      
      // Upload new logo if selected
      if (logoFile) {
        console.log('📤 Upload du nouveau logo...');
        const formData = new FormData();
        formData.append('file', logoFile);
        
        const uploadResponse = await axios.post(
          `${API}/mathalea/pro/upload-logo`,
          formData,
          {
            headers: {
              'X-Session-Token': sessionToken,
              'Content-Type': 'multipart/form-data'
            }
          }
        );
        
        uploadedLogoUrl = uploadResponse.data.logo_url;
        console.log('✅ Logo uploadé:', uploadedLogoUrl);
      }
      
      // Save config
      const configData = {
        professor_name: professorName || '',
        school_name: schoolName || '',
        school_year: schoolYear || '2024-2025',
        footer_text: footerText || '',
        template_choice: selectedStyle,
        logo_url: uploadedLogoUrl && !uploadedLogoUrl.startsWith('data:') ? uploadedLogoUrl : null
      };
      
      console.log('💾 Sauvegarde config Pro:', configData);

      await axios.put(`${API}/mathalea/pro/config`, configData, {
        headers: { 
          'X-Session-Token': sessionToken,
          'Content-Type': 'application/json'
        }
      });

      console.log('✅ Config Pro sauvegardée avec succès');
      setSaveSuccess(true);
      
      // Clear success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000);
      
    } catch (error) {
      console.error('❌ Erreur sauvegarde config Pro:', error);
      alert('Erreur lors de la sauvegarde. Vérifiez votre connexion.');
    } finally {
      setSaving(false);
    }
  };

  // P1.2: Load user sessions
  const loadSessions = async (token) => {
    if (!token) return;
    
    setSessionsLoading(true);
    try {
      const response = await axios.get(`${API}/auth/sessions`, {
        headers: { 'X-Session-Token': token }
      });
      
      setSessions(response.data.sessions || []);
      setCurrentSessionId(response.data.current_session_id || null);
      
      console.log('✅ Sessions chargées:', response.data);
    } catch (error) {
      console.error('Error loading sessions:', error);
      toast({
        title: "Erreur",
        description: "Impossible de charger les sessions",
        variant: "destructive"
      });
    } finally {
      setSessionsLoading(false);
    }
  };

  // P1.2: Delete a specific session
  const handleDeleteSession = async (sessionId) => {
    if (!sessionToken) return;
    
    // Prevent deleting current session (should be disabled in UI, but double-check)
    if (sessionId === currentSessionId) {
      toast({
        title: "Impossible",
        description: "Vous ne pouvez pas supprimer la session actuelle",
        variant: "destructive"
      });
      return;
    }
    
    const confirmed = window.confirm(
      "Êtes-vous sûr de vouloir déconnecter cet appareil ?"
    );
    
    if (!confirmed) return;
    
    try {
      await axios.delete(`${API}/auth/sessions/${sessionId}`, {
        headers: { 'X-Session-Token': sessionToken }
      });
      
      toast({
        title: "Appareil déconnecté",
        description: "Cet appareil a été déconnecté avec succès",
      });
      
      // Reload sessions
      await loadSessions(sessionToken);
    } catch (error) {
      console.error('Error deleting session:', error);
      
      let errorMessage = "Erreur lors de la déconnexion";
      if (error.response?.status === 403) {
        errorMessage = "Vous n'avez pas l'autorisation de supprimer cette session";
      } else if (error.response?.status === 400) {
        errorMessage = error.response.data.detail || errorMessage;
      }
      
      toast({
        title: "Erreur",
        description: errorMessage,
        variant: "destructive"
      });
    }
  };

  // P1.2: Delete all other sessions (keep current)
  const handleDeleteAllOtherSessions = async () => {
    if (!sessionToken || !currentSessionId) return;
    
    const otherSessions = sessions.filter(s => s.session_id !== currentSessionId);
    
    if (otherSessions.length === 0) {
      toast({
        title: "Aucune session",
        description: "Vous n'avez pas d'autres appareils connectés",
      });
      return;
    }
    
    const confirmed = window.confirm(
      `Êtes-vous sûr de vouloir déconnecter ${otherSessions.length} appareil(s) ?`
    );
    
    if (!confirmed) return;
    
    try {
      // Delete all other sessions
      const deletePromises = otherSessions.map(session =>
        axios.delete(`${API}/auth/sessions/${session.session_id}`, {
          headers: { 'X-Session-Token': sessionToken }
        })
      );
      
      await Promise.all(deletePromises);
      
      toast({
        title: "Appareils déconnectés",
        description: `${otherSessions.length} appareil(s) déconnecté(s) avec succès`,
      });
      
      // Reload sessions
      await loadSessions(sessionToken);
    } catch (error) {
      console.error('Error deleting sessions:', error);
      toast({
        title: "Erreur",
        description: "Erreur lors de la déconnexion des appareils",
        variant: "destructive"
      });
    }
  };

  // P1.2: Format relative time
  const formatRelativeTime = (dateString) => {
    if (!dateString) return "Inconnu";
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return "À l'instant";
    if (diffMins < 60) return `Il y a ${diffMins} minute${diffMins > 1 ? 's' : ''}`;
    if (diffHours < 24) return `Il y a ${diffHours} heure${diffHours > 1 ? 's' : ''}`;
    return `Il y a ${diffDays} jour${diffDays > 1 ? 's' : ''}`;
  };

  // P1.2: Get device icon
  const getDeviceIcon = (deviceType) => {
    switch (deviceType) {
      case 'desktop':
        return <Monitor className="h-5 w-5" />;
      case 'tablet':
        return <Tablet className="h-5 w-5" />;
      case 'mobile':
        return <Smartphone className="h-5 w-5" />;
      default:
        return <Monitor className="h-5 w-5" />;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('lemaitremot_session_token');
    localStorage.removeItem('lemaitremot_user_email');
    localStorage.removeItem('lemaitremot_login_method');
    navigate('/');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <Header 
          isPro={isPro}
          userEmail={userEmail}
          onLogin={() => navigate('/')}
          onLogout={handleLogout}
        />
        <div className="container mx-auto px-4 py-8">
          <Card>
            <CardContent className="flex items-center justify-center p-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span>Chargement...</span>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (!isPro) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <Header 
          isPro={isPro}
          userEmail={userEmail}
          onLogin={() => navigate('/')}
          onLogout={handleLogout}
        />
        <div className="container mx-auto px-4 py-8">
          <Card className="max-w-2xl mx-auto">
            <CardHeader>
              <div className="flex items-center justify-center mb-4">
                <Lock className="h-12 w-12 text-gray-400" />
              </div>
              <CardTitle className="text-center">Fonctionnalité Pro</CardTitle>
              <CardDescription className="text-center">
                Les paramètres de personnalisation sont réservés aux utilisateurs Pro
              </CardDescription>
            </CardHeader>
            <CardContent className="text-center space-y-4">
              <p className="text-gray-600">
                Passez à Le Maître Mot Pro pour personnaliser vos documents avec :
              </p>
              <ul className="text-left max-w-md mx-auto space-y-2 text-gray-700">
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  Logo de votre établissement
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  Informations personnalisées (professeur, école)
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  Pied de page personnalisé
                </li>
                <li className="flex items-center">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  Choix de styles de documents
                </li>
              </ul>
              <div className="flex gap-2 justify-center">
                <Button 
                  onClick={() => navigate('/')}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Crown className="mr-2 h-4 w-4" />
                  Passer à Pro
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => navigate('/')}
                >
                  <ArrowLeft className="mr-2 h-4 w-4" />
                  Retour à l'accueil
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header 
        isPro={isPro}
        userEmail={userEmail}
        onLogin={() => navigate('/')}
        onLogout={handleLogout}
      />
      
      <div className="container mx-auto px-4 py-8">
        {/* Page Header */}
        <div className="mb-6">
          {/* Bouton de retour intelligent */}
          {from === 'builder' && sheetId ? (
            <Button 
              variant="default"
              size="sm" 
              onClick={() => navigate(`/builder/${sheetId}`)}
              className="mb-4 bg-blue-600 hover:bg-blue-700"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour à ma fiche
            </Button>
          ) : (
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/builder')}
              className="mb-4"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
          )}
          
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 flex items-center">
                <Palette className="h-8 w-8 text-blue-600 mr-3" />
                Paramètres Pro
                <Badge className="ml-3 bg-blue-600">Pro</Badge>
              </h1>
              <p className="text-gray-600 mt-2">
                Personnalisez vos documents PDF avec votre logo et informations
              </p>
              {from === 'builder' && sheetId && (
                <p className="text-sm text-blue-600 mt-1">
                  ✨ Vous éditez vos paramètres depuis une fiche en cours
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Success Alert */}
        {saveSuccess && (
          <Alert className="mb-6 border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800">
              ✅ Vos préférences Pro ont été sauvegardées avec succès !
            </AlertDescription>
          </Alert>
        )}

        <Card className="max-w-4xl mx-auto">
          <CardHeader>
            <CardTitle className="flex items-center">
              Personnalisation des documents
            </CardTitle>
            <CardDescription>
              Ces paramètres seront automatiquement appliqués à tous vos exports Pro
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Logo Upload */}
            <div className="space-y-2">
              <Label>Logo de l'établissement</Label>
              <div
                className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                  dragOver ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
              >
                {logoPreview ? (
                  <div className="space-y-2">
                    <img 
                      src={logoPreview} 
                      alt="Logo de l'établissement" 
                      className="mx-auto h-20 w-auto object-contain"
                    />
                    <p className="text-sm text-gray-600">
                      Glissez une nouvelle image ou cliquez pour changer
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="mx-auto h-8 w-8 text-gray-400" />
                    <p className="text-sm text-gray-600">
                      Glissez votre logo ici ou cliquez pour sélectionner
                    </p>
                    <p className="text-xs text-gray-500">PNG ou JPG, max 2 Mo</p>
                  </div>
                )}
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/jpg"
                  onChange={(e) => e.target.files[0] && handleLogoUpload(e.target.files[0])}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
              </div>
            </div>

            {/* Information Fields */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="professor">
                  <User className="inline h-4 w-4 mr-1" />
                  Professeur
                </Label>
                <Input
                  id="professor"
                  value={professorName}
                  onChange={(e) => setProfessorName(e.target.value)}
                  placeholder="Nom du professeur"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="school">
                  <Building className="inline h-4 w-4 mr-1" />
                  Établissement
                </Label>
                <Input
                  id="school"
                  value={schoolName}
                  onChange={(e) => setSchoolName(e.target.value)}
                  placeholder="Nom de l'établissement"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="year">
                <Calendar className="inline h-4 w-4 mr-1" />
                Année scolaire
              </Label>
              <Input
                id="year"
                value={schoolYear}
                onChange={(e) => setSchoolYear(e.target.value)}
                placeholder="2024-2025"
              />
            </div>

            {/* Footer Text */}
            <div className="space-y-2">
              <Label htmlFor="footer">
                <FileText className="inline h-4 w-4 mr-1" />
                Pied de page personnalisé
              </Label>
              <Textarea
                id="footer"
                value={footerText}
                onChange={(e) => setFooterText(e.target.value)}
                placeholder="Texte qui apparaîtra en bas de chaque page..."
                rows={2}
              />
            </div>

            {/* Style Selector */}
            <div className="space-y-2">
              <Label>Style du document préféré</Label>
              <Select value={selectedStyle} onValueChange={setSelectedStyle}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(templateStyles).map(([styleId, style]) => (
                    <SelectItem key={styleId} value={styleId}>
                      <div className="flex items-center space-x-2">
                        <div className="flex space-x-1">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: style.preview_colors?.primary || '#2563eb' }}
                          />
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: style.preview_colors?.accent || '#7c3aed' }}
                          />
                        </div>
                        <span>{style.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {templateStyles[selectedStyle] && (
                <p className="text-sm text-gray-600">
                  {templateStyles[selectedStyle].description}
                </p>
              )}
            </div>

            {/* Save Button */}
            <div className="flex gap-2 pt-4">
              <Button 
                onClick={handleSave}
                disabled={saving}
                className="flex-1 bg-blue-600 hover:bg-blue-700"
              >
                {saving ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Sauvegarde...
                  </>
                ) : (
                  <>
                    <Save className="mr-2 h-4 w-4" />
                    Sauvegarder mes préférences Pro
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* P2: Sécurité du compte - Définir un mot de passe */}
        <Card className="max-w-4xl mx-auto mt-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Lock className="h-5 w-5 mr-2 text-blue-600" />
              Sécurité du compte
            </CardTitle>
            <CardDescription>
              Définissez un mot de passe optionnel pour votre compte Pro
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SetPasswordModal sessionToken={sessionToken} />
          </CardContent>
        </Card>

        {/* P1.2: Appareils connectés */}
        <Card className="max-w-4xl mx-auto mt-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2 text-blue-600" />
              Appareils connectés
            </CardTitle>
            <CardDescription>
              Gérez vos sessions actives sur différents appareils (maximum 3 simultanées)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {sessionsLoading ? (
              <div className="flex items-center justify-center p-8">
                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                <span className="text-gray-600">Chargement des sessions...</span>
              </div>
            ) : sessions.length === 0 ? (
              <div className="text-center p-8 text-gray-500">
                <Shield className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p>Aucune session active</p>
              </div>
            ) : (
              <div className="space-y-4">
                {sessions.map((session) => {
                  const isCurrent = session.session_id === currentSessionId;
                  
                  return (
                    <div
                      key={session.session_id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center gap-4 flex-1">
                        {/* Device Icon */}
                        <div className="text-gray-600">
                          {getDeviceIcon(session.device_type)}
                        </div>
                        
                        {/* Device Info */}
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-gray-900">
                              {session.browser} sur {session.os}
                            </span>
                            {isCurrent && (
                              <Badge className="bg-blue-600 text-white">
                                Cet appareil
                              </Badge>
                            )}
                          </div>
                          <div className="text-sm text-gray-600 space-y-1">
                            <p>
                              Connecté {formatRelativeTime(session.created_at)}
                            </p>
                            {session.last_used && session.last_used !== session.created_at && (
                              <p>
                                Dernière activité : {formatRelativeTime(session.last_used)}
                              </p>
                            )}
                            {session.ip_address && (
                              <p className="text-xs text-gray-500">
                                IP : {session.ip_address}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      
                      {/* Delete Button */}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeleteSession(session.session_id)}
                        disabled={isCurrent}
                        className={isCurrent ? "opacity-50 cursor-not-allowed" : ""}
                      >
                        <LogOut className="h-4 w-4 mr-2" />
                        {isCurrent ? "Session actuelle" : "Déconnecter"}
                      </Button>
                    </div>
                  );
                })}
                
                {/* Delete All Other Sessions Button */}
                {sessions.length > 1 && (
                  <div className="pt-4 border-t">
                    <Button
                      variant="outline"
                      onClick={handleDeleteAllOtherSessions}
                      className="w-full text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <LogOut className="h-4 w-4 mr-2" />
                      Déconnecter tous les autres appareils ({sessions.length - 1})
                    </Button>
                  </div>
                )}
                
                {/* Info */}
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-800">
                    <strong>ℹ️ Information :</strong> Vous pouvez être connecté sur jusqu'à 3 appareils simultanément.
                    Si vous vous connectez sur un 4ème appareil, la session la plus ancienne sera automatiquement déconnectée.
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* P2: Sécurité du compte - Définir un mot de passe */}
        <Card className="max-w-4xl mx-auto mt-6">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Lock className="h-5 w-5 mr-2 text-blue-600" />
              Sécurité du compte
            </CardTitle>
            <CardDescription>
              Définissez un mot de passe optionnel pour votre compte Pro
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SetPasswordModal sessionToken={sessionToken} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// P2: Set Password Modal Component
const SetPasswordModal = ({ sessionToken }) => {
  const { toast } = useToast();
  const [showModal, setShowModal] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [passwordErrors, setPasswordErrors] = useState({
    length: false,
    uppercase: false,
    digit: false,
    match: false
  });

  // P2: Live password validation
  useEffect(() => {
    if (password) {
      setPasswordErrors({
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        digit: /\d/.test(password),
        match: password === confirmPassword && confirmPassword.length > 0
      });
    } else {
      setPasswordErrors({
        length: false,
        uppercase: false,
        digit: false,
        match: false
      });
    }
  }, [password, confirmPassword]);

  const handleSetPassword = async () => {
    if (!sessionToken) {
      toast({
        title: "Erreur",
        description: "Session invalide. Veuillez vous reconnecter.",
        variant: "destructive"
      });
      return;
    }

    // Validate password strength
    if (password.length < 8) {
      toast({
        title: "Mot de passe trop court",
        description: "Le mot de passe doit contenir au moins 8 caractères.",
        variant: "destructive"
      });
      return;
    }
    
    if (!/[A-Z]/.test(password)) {
      toast({
        title: "Mot de passe invalide",
        description: "Le mot de passe doit contenir au moins une majuscule.",
        variant: "destructive"
      });
      return;
    }
    
    if (!/\d/.test(password)) {
      toast({
        title: "Mot de passe invalide",
        description: "Le mot de passe doit contenir au moins un chiffre.",
        variant: "destructive"
      });
      return;
    }
    
    if (password !== confirmPassword) {
      toast({
        title: "Mots de passe différents",
        description: "Les mots de passe ne correspondent pas.",
        variant: "destructive"
      });
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/set-password`, {
        password: password,
        password_confirm: confirmPassword
      }, {
        headers: {
          'X-Session-Token': sessionToken
        }
      });

      toast({
        title: "Mot de passe défini",
        description: "Votre mot de passe a été défini avec succès. Vous pouvez toujours utiliser le lien magique.",
      });

      setShowModal(false);
      setPassword('');
      setConfirmPassword('');
      
    } catch (error) {
      console.error('Error setting password:', error);
      const errorMsg = error.response?.data?.detail || 'Erreur lors de la définition du mot de passe';
      toast({
        title: "Erreur",
        description: errorMsg,
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Button
        onClick={() => setShowModal(true)}
        variant="outline"
        className="w-full"
      >
        <KeyRound className="h-4 w-4 mr-2" />
        Définir un mot de passe
      </Button>

      <Dialog open={showModal} onOpenChange={setShowModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center">
              <Lock className="mr-2 h-6 w-6 text-blue-600" />
              Définir un mot de passe
            </DialogTitle>
            <DialogDescription>
              Le mot de passe est optionnel. Vous pouvez toujours utiliser le lien magique pour vous connecter.
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="set-password">Mot de passe</Label>
              <Input
                id="set-password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && password && confirmPassword && !loading) {
                    handleSetPassword();
                  }
                }}
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="set-password-confirm">Confirmer le mot de passe</Label>
              <Input
                id="set-password-confirm"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && password && confirmPassword && !loading) {
                    handleSetPassword();
                  }
                }}
              />
            </div>
            
            {/* Password validation indicators */}
            {password && (
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
              onClick={handleSetPassword}
              disabled={loading || !passwordErrors.length || !passwordErrors.uppercase || !passwordErrors.digit || !passwordErrors.match}
              className="w-full bg-blue-600 hover:bg-blue-700"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Définition en cours...
                </>
              ) : (
                <>
                  <KeyRound className="mr-2 h-4 w-4" />
                  Définir le mot de passe
                </>
              )}
            </Button>
            
            <div className="bg-blue-50 p-3 rounded-lg text-xs text-blue-700">
              💡 <strong>Rappel :</strong> Vous pouvez toujours utiliser le lien magique pour vous connecter.
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default ProSettingsPage;
