import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";
import { Download, Loader2, Crown, FileText } from "lucide-react";

const Step4ExportTelechargement = ({
  currentDocument,
  exportStyles,
  selectedExportStyle,
  onExportStyleChange,
  exportingSubject,
  exportingSolution,
  onExportPDF,
  // Quota/Pro status
  isPro,
  quotaStatus,
  quotaLoaded,
  userEmail,
  onCheckProStatus,
  onShowPaymentModal,
  isLoading = false
}) => {
  if (!currentDocument) {
    return (
      <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-t-lg">
          <CardTitle className="flex items-center">
            <Download className="mr-2 h-5 w-5" />
            Export et téléchargement
          </CardTitle>
          <CardDescription className="text-orange-50">
            Exportez votre document au format PDF
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div className="text-center py-12">
            <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun document généré</h3>
            <p className="text-gray-500">
              Générez d'abord un document pour accéder aux options d'export
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
      <CardHeader className="bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-t-lg">
        <CardTitle className="flex items-center">
          <Download className="mr-2 h-5 w-5" />
          Export et téléchargement
        </CardTitle>
        <CardDescription className="text-orange-50">
          Exportez votre document au format PDF avec le style souhaité
        </CardDescription>
      </CardHeader>
      <CardContent className="p-6 space-y-6">
        {/* Document Summary */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-2">Document prêt à exporter :</h4>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-600">Type :</span>
              <span className="ml-2 font-medium">{currentDocument.type_doc}</span>
            </div>
            <div>
              <span className="text-gray-600">Matière :</span>
              <span className="ml-2 font-medium">{currentDocument.matiere}</span>
            </div>
            <div>
              <span className="text-gray-600">Niveau :</span>
              <span className="ml-2 font-medium">{currentDocument.niveau}</span>
            </div>
            <div>
              <span className="text-gray-600">Exercices :</span>
              <span className="ml-2 font-medium">{currentDocument.nb_exercices}</span>
            </div>
            <div className="col-span-2">
              <span className="text-gray-600">Chapitre :</span>
              <span className="ml-2 font-medium">{currentDocument.chapitre}</span>
            </div>
          </div>
        </div>

        {/* Export Style Selection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Label htmlFor="export-style" className="text-sm font-medium text-gray-700 flex items-center">
              🎨 Style d'export
            </Label>
            {!isPro && (
              <Badge variant="outline" className="text-xs">
                Pro requis pour plus de styles
              </Badge>
            )}
          </div>
          <Select value={selectedExportStyle} onValueChange={onExportStyleChange} disabled={isLoading}>
            <SelectTrigger>
              <SelectValue placeholder="Choisir un style" />
            </SelectTrigger>
            <SelectContent>
              {Object.entries(exportStyles).map(([styleId, style]) => (
                <SelectItem 
                  key={styleId} 
                  value={styleId}
                  disabled={style.pro_only && !isPro}
                >
                  <div className="flex items-center justify-between w-full">
                    <div>
                      <div className="font-medium">{style.name}</div>
                      <div className="text-xs text-gray-500">{style.description}</div>
                    </div>
                    {style.pro_only && (
                      <Crown className="h-3 w-3 text-yellow-500 ml-2" />
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          
          {/* Style Preview */}
          {exportStyles[selectedExportStyle] && (
            <div className="text-xs text-gray-600">
              <p>📋 {exportStyles[selectedExportStyle].description}</p>
              {exportStyles[selectedExportStyle].pro_only && !isPro && (
                <p className="text-orange-600 mt-1">
                  ⚠️ Ce style nécessite un compte Pro
                </p>
              )}
            </div>
          )}
        </div>

        {/* Export Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <Button 
            onClick={() => onExportPDF('sujet')}
            disabled={!currentDocument || exportingSubject || isLoading}
            className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white disabled:opacity-50"
            size="lg"
          >
            {exportingSubject ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Export...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Export Sujet PDF
              </>
            )}
          </Button>
          
          <Button 
            onClick={() => onExportPDF('corrige')}
            disabled={!currentDocument || exportingSolution || isLoading}
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white disabled:opacity-50"
            size="lg"
          >
            {exportingSolution ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Export...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Export Corrigé PDF
              </>
            )}
          </Button>
        </div>

        {/* Export Status Info */}
        {quotaLoaded && (
          <div className="border-t pt-4">
            <div className="text-center text-sm">
              {isPro ? (
                <div className="text-blue-600 bg-blue-50 rounded-lg p-3">
                  <p className="font-medium flex items-center justify-center">
                    <Crown className="mr-2 h-4 w-4" />
                    Compte Pro - Exports illimités
                  </p>
                  <p className="text-xs text-blue-500 mt-1">
                    Profitez de tous les styles d'export disponibles
                  </p>
                </div>
              ) : quotaStatus.quota_exceeded ? (
                <div className="text-orange-600 bg-orange-50 rounded-lg p-3">
                  <p className="font-medium mb-2">
                    ⚠️ Quota d'export dépassé
                  </p>
                  <Button 
                    variant="outline" 
                    size="sm"
                    onClick={onShowPaymentModal}
                    className="text-orange-600 border-orange-300 hover:bg-orange-100"
                  >
                    Passer à Pro
                  </Button>
                  {userEmail && (
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={() => onCheckProStatus(userEmail)}
                      className="ml-2 text-xs text-orange-600"
                    >
                      Vérifier mon statut Pro
                    </Button>
                  )}
                </div>
              ) : (
                <div className="text-gray-600 bg-gray-50 rounded-lg p-3">
                  <p className="font-medium">
                    📄 Exports restants : {quotaStatus.exports_remaining}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Passez à Pro pour des exports illimités
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Success Message */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center text-green-800">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-2">
              <p className="text-sm font-medium">
                Document prêt à l'export !
              </p>
              <p className="text-xs text-green-600">
                Choisissez le type d'export souhaité ci-dessus
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default Step4ExportTelechargement;