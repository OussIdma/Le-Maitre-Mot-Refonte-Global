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
  CheckCircle
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

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
      const validationRes = await axios.get(`${API}/api/auth/session/validate`, {
        headers: { 'X-Session-Token': token }
      });
      
      setIsPro(true);
      
      // Load config
      await loadUserConfig(token);
      await loadTemplateStyles();
      
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
      const response = await axios.get(`${API}/api/mathalea/pro/config`, {
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
      const response = await axios.get(`${API}/api/template/styles`);
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
          `${API}/api/mathalea/pro/upload-logo`,
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

      await axios.put(`${API}/api/mathalea/pro/config`, configData, {
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
      </div>
    </div>
  );
};

export default ProSettingsPage;
