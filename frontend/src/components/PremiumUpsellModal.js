/**
 * PremiumUpsellModal - Modal non-intrusive pour conversion Premium
 * 
 * Affiche la valeur Pro SANS frustration ni blocage.
 * Ouverture uniquement sur action utilisateur (clic CTA), jamais automatique.
 */

import React from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Check, Sparkles, FileDown, Palette } from "lucide-react";

const PremiumUpsellModal = ({ isOpen, onClose, onStartTrial }) => {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <Sparkles className="h-6 w-6 text-purple-600" />
            Aller plus loin avec Le Maître Mot Pro
          </DialogTitle>
          <DialogDescription className="text-base">
            Débloquez des fonctionnalités avancées pour un enseignement personnalisé
          </DialogDescription>
        </DialogHeader>

        <div className="py-6 space-y-4">
          {/* Variantes A/B/C */}
          <div className="flex items-start gap-3">
            <div className="mt-1 p-2 bg-purple-100 rounded-lg">
              <Check className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">
                Variantes A/B/C (anti-triche, différenciation)
              </h4>
              <p className="text-sm text-gray-600">
                Générez plusieurs versions d'un même exercice pour vos évaluations et adaptez à chaque niveau
              </p>
            </div>
          </div>

          {/* Exports PDF illimités */}
          <div className="flex items-start gap-3">
            <div className="mt-1 p-2 bg-blue-100 rounded-lg">
              <FileDown className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">
                Exports PDF illimités sans watermark
              </h4>
              <p className="text-sm text-gray-600">
                Créez et exportez autant de sujets que nécessaire avec vos propres paramètres
              </p>
            </div>
          </div>

          {/* Templates & branding */}
          <div className="flex items-start gap-3">
            <div className="mt-1 p-2 bg-green-100 rounded-lg">
              <Palette className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-1">
                Templates & branding professionnels
              </h4>
              <p className="text-sm text-gray-600">
                Personnalisez vos documents avec des modèles élégants et votre identité visuelle
              </p>
            </div>
          </div>
        </div>

        <DialogFooter className="flex flex-col sm:flex-row gap-2">
          <Button
            onClick={onStartTrial}
            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white"
            size="lg"
          >
            <Sparkles className="mr-2 h-4 w-4" />
            Essayer Pro (7 jours)
          </Button>
          <Button
            onClick={onClose}
            variant="ghost"
            className="flex-1"
            size="lg"
          >
            Continuer en version gratuite
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default PremiumUpsellModal;




