import React, { useState, useEffect } from 'react';
import axios from 'axios';
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
  Loader2
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const TemplateSettings = ({ isPro, sessionToken, onTemplateChange }) => {
  const [template, setTemplate] = useState(null);
  const [templateStyles, setTemplateStyles] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [logoFile, setLogoFile] = useState(null);
  const [logoPreview, setLogoPreview] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  // Form fields
  const [professorName, setProfessorName] = useState('');
  const [schoolName, setSchoolName] = useState('');
  const [schoolYear, setSchoolYear] = useState('');
  const [footerText, setFooterText] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('minimaliste');

  useEffect(() => {
    loadTemplateStyles();
    if (isPro) {
      loadUserTemplate();
    }
  }, [isPro]);

  const loadTemplateStyles = async () => {
    try {
      const response = await axios.get(`${API}/api/template/styles`);
      setTemplateStyles(response.data.styles);
    } catch (error) {
      console.error('Error loading template styles:', error);
    }
  };

  const loadUserTemplate = async () => {
    if (!sessionToken) return;
    
    setLoading(true);
    try {
      // Nouvelle route API pour la config Pro
      const response = await axios.get(`${API}/api/mathalea/pro/config`, {
        headers: { 'X-Session-Token': sessionToken }
      });
      
      const userTemplate = response.data;
      setTemplate(userTemplate);
      setProfessorName(userTemplate.professor_name || '');
      setSchoolName(userTemplate.school_name || '');
      setSchoolYear(userTemplate.school_year || '');
      setFooterText(userTemplate.footer_text || '');
      setSelectedStyle(userTemplate.template_style || userTemplate.template_choice || 'classique');
      
      if (userTemplate.logo_url) {
        // Construire l'URL complète du logo
        const logoUrl = userTemplate.logo_url.startsWith('http') 
          ? userTemplate.logo_url 
          : `${API}${userTemplate.logo_url}`;
        setLogoPreview(logoUrl);
        console.log('📸 Logo chargé:', logoUrl);
      }
      
      console.log('✅ Config Pro chargée:', userTemplate);
      
    } catch (error) {
      console.error('Error loading user template:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveTemplate = async () => {
    if (!sessionToken) return;
    
    setSaving(true);
    try {
      let uploadedLogoUrl = logoPreview; // Conserver le logo existant par défaut
      
      // 1. Si un nouveau fichier logo a été sélectionné, l'uploader d'abord
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
      
      // 2. Préparer les données de config Pro avec le logo
      const configData = {
        professor_name: professorName || '',
        school_name: schoolName || '',
        school_year: schoolYear || '2024-2025',
        footer_text: footerText || '',
        template_choice: selectedStyle,
        logo_url: uploadedLogoUrl || null  // Sauvegarder l'URL du logo
      };
      
      console.log('💾 Sauvegarde config Pro:', configData);

      // 3. Sauvegarder la configuration Pro complète
      const response = await axios.put(`${API}/api/mathalea/pro/config`, configData, {
        headers: { 
          'X-Session-Token': sessionToken,
          'Content-Type': 'application/json'
        }
      });

      console.log('✅ Config Pro sauvegardée avec succès');
      
      // 4. Recharger la config pour confirmer
      await loadUserTemplate();
      
      // 5. Notify parent component
      if (onTemplateChange) {
        onTemplateChange(configData);
      }
      
      alert('✅ Vos préférences Pro ont été sauvegardées !');
      
    } catch (error) {
      console.error('❌ Erreur sauvegarde config Pro:', error);
      alert('Erreur lors de la sauvegarde. Vérifiez votre connexion.');
    } finally {
      setSaving(false);
    }
  };

  const handleLogoUpload = (file) => {
    if (file && file.size <= 1024 * 1024) { // 1MB limit
      setLogoFile(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoPreview(e.target.result);
      };
      reader.readAsDataURL(file);
    } else {
      alert('Le logo doit faire moins de 1 Mo');
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

  if (!isPro) {
    // Free user - locked section
    return (
      <Card className="opacity-60 bg-gray-50 border-gray-200">
        <CardHeader className="relative">
          <div className="absolute top-4 right-4">
            <Lock className="h-5 w-5 text-gray-400" />
          </div>
          <CardTitle className="flex items-center text-gray-600">
            <Palette className="mr-2 h-5 w-5" />
            Personnalisation du document
          </CardTitle>
          <CardDescription className="text-gray-500">
            Personnalisez vos documents avec votre logo et informations
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Logo Upload - Locked */}
          <div className="space-y-2">
            <Label className="text-gray-500">Logo de l'établissement</Label>
            <div className="border-2 border-dashed border-gray-200 rounded-lg p-6 text-center bg-gray-100">
              <ImageIcon className="mx-auto h-8 w-8 text-gray-400 mb-2" />
              <p className="text-sm text-gray-500">Upload de logo (PNG/JPG)</p>
            </div>
          </div>

          {/* Form Fields - Locked */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-gray-500">Professeur</Label>
              <Input disabled placeholder="Nom du professeur" className="bg-gray-100" />
            </div>
            <div className="space-y-2">
              <Label className="text-gray-500">Établissement</Label>
              <Input disabled placeholder="Nom de l'établissement" className="bg-gray-100" />
            </div>
          </div>

          {/* Style Selector - Locked */}
          <div className="space-y-2">
            <Label className="text-gray-500">Style du document</Label>
            <Select disabled>
              <SelectTrigger className="bg-gray-100">
                <SelectValue placeholder="Sélectionner un style" />
              </SelectTrigger>
            </Select>
          </div>

          {/* CTA */}
          <Alert className="border-blue-200 bg-blue-50 mt-4">
            <Crown className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              <strong>Fonctionnalité Pro :</strong> Personnalisez vos documents avec votre logo, 
              informations d'établissement et différents styles de mise en page.
              <div className="mt-2">
                <Button size="sm" className="bg-blue-600 hover:bg-blue-700">
                  <Crown className="mr-1 h-3 w-3" />
                  Passer à Pro
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center p-8">
          <Loader2 className="h-6 w-6 animate-spin mr-2" />
          <span>Chargement des templates...</span>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center">
          <Palette className="mr-2 h-5 w-5 text-blue-600" />
          Personnalisation du document
          <Badge className="ml-2 bg-blue-100 text-blue-800">Pro</Badge>
        </CardTitle>
        <CardDescription>
          Personnalisez vos documents avec votre logo et informations
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Logo Upload */}
        <div className="space-y-2">
          {!logoPreview && <Label>Logo de l'établissement</Label>}
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
                  className="mx-auto h-16 w-auto object-contain"
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
                <p className="text-xs text-gray-500">PNG ou JPG, max 1 Mo</p>
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
          <Label>Style du document</Label>
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
                        style={{ backgroundColor: style.preview_colors.primary }}
                      />
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: style.preview_colors.accent }}
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
        <Button 
          onClick={handleSaveTemplate}
          disabled={saving}
          className="w-full"
        >
          {saving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Sauvegarde...
            </>
          ) : (
            'Sauvegarder les préférences'
          )}
        </Button>
      </CardContent>
    </Card>
  );
};

export default TemplateSettings;