// app/frontend/src/components/ProExportModal.js

import React, { useEffect, useState } from "react";
import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || "";

/**
 * ProExportModal
 *
 * Props attendues :
 * - isOpen        : bool        → la modale est-elle ouverte ?
 * - onClose       : () => void  → callback pour fermer la modale
 * - sheetId       : string      → ID de la fiche à exporter
 * - sessionToken  : string      → email / token de session (X-Session-Token)
 * - defaultDocType: string      → "exercices" | "controle" | "evaluation" | "dm" (optionnel)
 *
 * NOTE :
 * - Le backend retourne :
 *   {
 *     pro_subject_pdf: "<base64>",
 *     pro_correction_pdf: "<base64>",
 *     base_filename: "LeMaitreMot_<NomFiche>_Pro",
 *     template: "classique" | "academique",
 *     ...
 *   }
 */

function downloadPdfFromBase64(base64Data, filename) {
  try {
    const byteCharacters = atob(base64Data);
    const byteNumbers = new Array(byteCharacters.length);

    for (let i = 0; i < byteCharacters.length; i += 1) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }

    const byteArray = new Uint8Array(byteNumbers);
    const blob = new Blob([byteArray], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "document.pdf";

    // iOS / Safari friendly
    link.style.position = "fixed";
    link.style.top = "-1000px";
    link.style.left = "-1000px";
    link.style.zIndex = "-1";

    document.body.appendChild(link);

    const clickEvent = new MouseEvent("click", {
      bubbles: true,
      cancelable: true,
      view: window,
    });
    link.dispatchEvent(clickEvent);

    setTimeout(() => {
      if (link.parentNode) {
        document.body.removeChild(link);
      }
      URL.revokeObjectURL(url);
    }, 1000);
  } catch (err) {
    console.error("Erreur téléchargement PDF Pro :", err);
    alert("Impossible de télécharger le PDF Pro. Réessayez plus tard.");
  }
}

const ProExportModal = ({
  isOpen,
  onClose,
  sheetId,
  sessionToken,
  defaultDocType = "exercices",
}) => {
  const [proConfig, setProConfig] = useState(null);
  const [configError, setConfigError] = useState("");
  const [loadingConfig, setLoadingConfig] = useState(false);

  const [selectedTemplate, setSelectedTemplate] = useState("classique");

  const [isExportingSubject, setIsExportingSubject] = useState(false);
  const [isExportingCorrection, setIsExportingCorrection] = useState(false);
  const [exportError, setExportError] = useState("");

  // Charger la config Pro lorsque la modale s'ouvre
  useEffect(() => {
    if (!isOpen || !sessionToken) return;

    const fetchConfig = async () => {
      setLoadingConfig(true);
      setConfigError("");

      try {
        const res = await axios.get(
          `${API_BASE_URL}/api/mathalea/pro/config`,
          {
            headers: {
              "X-Session-Token": sessionToken,
            },
          }
        );

        const cfg = res.data || null;
        setProConfig(cfg);
        
        // Debug logo URL
        if (cfg && cfg.logo_url) {
          console.log('📸 Logo URL reçue:', cfg.logo_url);
          console.log('📸 Logo URL complète:', cfg.logo_url.startsWith('http') ? cfg.logo_url : `${API_BASE_URL}${cfg.logo_url}`);
        }

        // si l'utilisateur a déjà un template préféré → on le met par défaut
        if (cfg && cfg.template_choice) {
          setSelectedTemplate(cfg.template_choice);
        }
      } catch (err) {
        console.error("Erreur chargement config Pro :", err);
        setConfigError(
          "Impossible de charger votre configuration Pro. Les valeurs par défaut seront utilisées."
        );
      } finally {
        setLoadingConfig(false);
      }
    };

    fetchConfig();
  }, [isOpen, sessionToken]);

  const canClose = !isExportingSubject && !isExportingCorrection;

  const handleClose = () => {
    if (!canClose) return;
    setExportError("");
    onClose && onClose();
  };

  const callGenerateProPdf = async () => {
    if (!sheetId) {
      throw new Error("SheetId manquant pour l'export Pro.");
    }
    if (!sessionToken) {
      throw new Error("SessionToken manquant pour l'export Pro.");
    }

    const payload = {
      template: selectedTemplate || "classique",
      type_doc: defaultDocType || "exercices",
    };

    const res = await axios.post(
      `${API_BASE_URL}/api/mathalea/sheets/${sheetId}/generate-pdf-pro`,
      payload,
      {
        headers: {
          "Content-Type": "application/json",
          "X-Session-Token": sessionToken,
        },
      }
    );

    if (!res.data) {
      throw new Error("Réponse vide du serveur lors de l'export Pro.");
    }

    return res.data;
  };

  const handleExportSubject = async () => {
    setExportError("");
    setIsExportingSubject(true);
    try {
      const data = await callGenerateProPdf();
      if (!data.pro_subject_pdf) {
        throw new Error("PDF Sujet Pro manquant dans la réponse.");
      }

      const baseFilename =
        data.base_filename || "LeMaitreMot_Fiche_Pro_Sujet";
      const filename = `${baseFilename}_Sujet_${selectedTemplate}.pdf`;
      downloadPdfFromBase64(data.pro_subject_pdf, filename);
      // on NE ferme PAS la modale
      alert("Sujet Pro téléchargé avec succès ✅");
    } catch (err) {
      console.error("Erreur export Sujet Pro :", err);
      setExportError(
        err?.message ||
          "Une erreur est survenue lors de l'export du Sujet Pro."
      );
    } finally {
      setIsExportingSubject(false);
    }
  };

  const handleExportCorrection = async () => {
    setExportError("");
    setIsExportingCorrection(true);
    try {
      const data = await callGenerateProPdf();
      if (!data.pro_correction_pdf) {
        throw new Error("PDF Corrigé Pro manquant dans la réponse.");
      }

      const baseFilename =
        data.base_filename || "LeMaitreMot_Fiche_Pro_Corrige";
      const filename = `${baseFilename}_Corrige_${selectedTemplate}.pdf`;
      downloadPdfFromBase64(data.pro_correction_pdf, filename);
      // on NE ferme PAS la modale
      alert("Corrigé Pro téléchargé avec succès ✅");
    } catch (err) {
      console.error("Erreur export Corrigé Pro :", err);
      setExportError(
        err?.message ||
          "Une erreur est survenue lors de l'export du Corrigé Pro."
      );
    } finally {
      setIsExportingCorrection(false);
    }
  };

  if (!isOpen) return null;

  const schoolName =
    proConfig && proConfig.school_name
      ? proConfig.school_name
      : "Le Maître Mot";

  const professorName =
    proConfig && proConfig.professor_name ? proConfig.professor_name : "";

  const schoolYear =
    proConfig && proConfig.school_year
      ? proConfig.school_year
      : "2024-2025";

  const logoConfigured =
    proConfig && proConfig.logo_url && proConfig.logo_url.trim().length > 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* HEADER */}
        <div className="flex justify-between items-center p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-900">Export Pro personnalisé</h2>
          <button
            type="button"
            onClick={handleClose}
            disabled={!canClose}
            className="text-gray-400 hover:text-gray-600 disabled:opacity-50"
            aria-label="Fermer"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* BODY */}
        <div className="p-6 space-y-6">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="font-semibold text-blue-900 mb-2">Fonctionnalités Pro incluses</p>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>Logo et nom de votre établissement</li>
              <li>Template personnalisé avec vos couleurs</li>
              <li>PDF de qualité professionnelle</li>
            </ul>
          </div>

          {/* Choix du template */}
          <div className="space-y-2">
            <label htmlFor="template-select" className="block font-semibold text-gray-900">
              Choisissez votre template
            </label>
            <select
              id="template-select"
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              disabled={isExportingSubject || isExportingCorrection}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <option value="classique">Classique - Style moderne et coloré</option>
              <option value="academique">Académique - Style formel et structuré</option>
            </select>
          </div>

          {/* Config utilisateur - En lecture seule */}
          <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
            <div className="flex items-center justify-between mb-3">
              <p className="font-semibold text-gray-900">Votre configuration</p>
              <span className="text-xs text-gray-500 italic">Lecture seule</span>
            </div>
            {loadingConfig && (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
                <span className="ml-2 text-gray-600">Chargement de votre configuration…</span>
              </div>
            )}
            {configError && (
              <p className="text-red-600 text-sm">{configError}</p>
            )}
            {!loadingConfig && (
              <div className="space-y-3">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Établissement :</span>
                    <span className="font-medium text-gray-900">{schoolName}</span>
                  </div>
                  {professorName && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Professeur :</span>
                      <span className="font-medium text-gray-900">{professorName}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">Année scolaire :</span>
                    <span className="font-medium text-gray-900">{schoolYear}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Template préféré :</span>
                    <span className="font-medium text-gray-900">
                      {proConfig?.template_choice
                        ? proConfig.template_choice === "academique"
                          ? "Académique"
                          : "Classique"
                        : selectedTemplate === "academique"
                        ? "Académique"
                        : "Classique"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Logo :</span>
                    {logoConfigured && proConfig.logo_url ? (
                      <img 
                        src={proConfig.logo_url.startsWith('http') ? proConfig.logo_url : `${API_BASE_URL}${proConfig.logo_url}`}
                        alt="Logo" 
                        className="h-8 w-auto object-contain"
                        onError={(e) => {
                          console.error('Logo load error, URL:', e.target.src);
                          e.target.style.display = 'none';
                          e.target.nextSibling.style.display = 'inline';
                        }}
                      />
                    ) : null}
                    <span 
                      className="text-gray-500 text-xs italic"
                      style={{ display: logoConfigured && proConfig.logo_url ? 'none' : 'inline' }}
                    >
                      {logoConfigured ? "Erreur de chargement" : "Par défaut"}
                    </span>
                  </div>
                </div>
                
                {/* Lien vers la page de paramètres - Nouvel onglet avec contexte */}
                <div className="pt-3 border-t border-gray-200">
                  <button
                    onClick={() => {
                      // Construire l'URL avec le contexte de la fiche
                      const url = new URL('/pro/settings', window.location.origin);
                      url.searchParams.set('from', 'builder');
                      url.searchParams.set('sheetId', sheetId);
                      window.open(url.toString(), '_blank', 'noopener,noreferrer');
                    }}
                    className="flex items-center justify-center text-sm text-blue-600 hover:text-blue-700 hover:underline w-full"
                  >
                    <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                    </svg>
                    Modifier mes paramètres Pro
                    <svg className="w-3 h-3 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </button>
                  <p className="text-xs text-gray-500 text-center mt-1">
                    (Ouvre dans un nouvel onglet - vous reviendrez ici après)
                  </p>
                </div>
              </div>
            )}
          </div>

          {exportError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-800 text-sm">{exportError}</p>
            </div>
          )}
        </div>

        {/* FOOTER */}
        <div className="flex justify-end gap-3 p-6 border-t bg-gray-50">
          <button
            type="button"
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleClose}
            disabled={!canClose}
          >
            Fermer
          </button>

          <button
            type="button"
            className="px-4 py-2 text-white bg-green-600 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleExportSubject}
            disabled={isExportingSubject || isExportingCorrection}
          >
            {isExportingSubject ? (
              <span className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Export Sujet…
              </span>
            ) : (
              "Exporter Sujet Pro PDF"
            )}
          </button>

          <button
            type="button"
            className="px-4 py-2 text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
            onClick={handleExportCorrection}
            disabled={isExportingSubject || isExportingCorrection}
          >
            {isExportingCorrection ? (
              <span className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Export Corrigé…
              </span>
            ) : (
              "Exporter Corrigé Pro PDF"
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProExportModal;
