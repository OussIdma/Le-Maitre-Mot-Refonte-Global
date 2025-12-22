import React from "react";
import { X, Download, FileText, Users, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent } from "./ui/card";

function PdfDownloadModal({ isOpen, onClose, pdfResult }) {
  if (!isOpen || !pdfResult) return null;

  const { student_pdf, correction_pdf, base_filename, sheetTitle } = pdfResult;

  /**
   * Fonction helper pour télécharger un PDF depuis base64
   * Compatible avec tous les navigateurs (desktop + mobile + iOS Safari)
   * 
   * STRATÉGIE iOS-FRIENDLY:
   * - Utilise un blob URL mais sans navigation
   * - Force le téléchargement via l'attribut download
   * - Empêche la navigation qui ferait fermer la modale
   */
  const downloadPdfFromBase64 = (base64Data, filename) => {
    if (!base64Data) {
      console.error('Pas de données base64 à télécharger');
      return;
    }
    
    try {
      // Décoder base64 en bytes
      const byteCharacters = window.atob(base64Data);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      
      // Créer blob avec le bon type MIME
      const blob = new Blob([byteArray], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      
      // Créer un lien de téléchargement
      const link = document.createElement('a');
      link.href = url;
      link.download = filename || 'document.pdf';
      
      // Style pour rendre le lien invisible
      link.style.display = 'none';
      link.style.position = 'fixed';
      link.style.zIndex = '-1';
      
      // Ajouter au DOM
      document.body.appendChild(link);
      
      // IMPORTANT: Ne PAS utiliser link.click() car cela peut causer une navigation
      // Sur iOS, utiliser une approche plus contrôlée
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true,
        view: window
      });
      
      link.dispatchEvent(clickEvent);
      
      // Nettoyage après un délai (important pour iOS)
      setTimeout(() => {
        if (link.parentNode) {
          document.body.removeChild(link);
        }
        URL.revokeObjectURL(url);
      }, 1000);
      
      console.log('📥 PDF téléchargé:', filename);
      
      // Afficher une confirmation visuelle (toast)
      // L'utilisateur peut maintenant télécharger le second PDF
      console.log('✅ Téléchargement lancé. La modale reste ouverte pour télécharger d\'autres PDFs.');
      
    } catch (error) {
      console.error('Erreur téléchargement PDF:', error);
      alert('Erreur lors du téléchargement du PDF. Veuillez réessayer.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <Card className="bg-white rounded-lg shadow-2xl w-full max-w-md">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center">
            <CheckCircle2 className="h-6 w-6 text-green-600 mr-3" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">
                Vos PDFs sont prêts
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Fiche : <span className="font-medium">{sheetTitle}</span>
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content */}
        <CardContent className="p-6">
          <p className="text-sm text-gray-700 mb-4">
            Choisissez les documents à télécharger :
          </p>

          <div className="space-y-3">
            {/* Bouton Version élève */}
            <Button
              onClick={() => downloadPdfFromBase64(student_pdf, `${base_filename || sheetTitle}_Eleve.pdf`)}
              className="w-full bg-green-600 hover:bg-green-700 flex items-center justify-center"
              size="lg"
            >
              <Users className="h-5 w-5 mr-2" />
              Télécharger la version élève
            </Button>

            {/* Bouton Corrigé */}
            <Button
              onClick={() => downloadPdfFromBase64(correction_pdf, `${base_filename || sheetTitle}_Corrige.pdf`)}
              className="w-full bg-red-600 hover:bg-red-700 flex items-center justify-center"
              size="lg"
            >
              <Download className="h-5 w-5 mr-2" />
              Télécharger la version corrigée
            </Button>
          </div>

          {/* Aide */}
          <p className="text-xs text-gray-500 mt-4 text-center">
            💡 Vous pouvez ouvrir ou enregistrer ces PDFs depuis votre navigateur.
          </p>
        </CardContent>

        {/* Footer */}
        <div className="border-t p-4 flex justify-end">
          <Button variant="outline" onClick={onClose}>
            Fermer
          </Button>
        </div>
      </Card>
    </div>
  );
}

export default PdfDownloadModal;
