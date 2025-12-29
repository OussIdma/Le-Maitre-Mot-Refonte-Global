/**
 * PremiumEcoModal - Modal pour upsell Premium lors de l'accès au layout Éco
 * 
 * PR8: Layout Éco = Premium uniquement
 * - S'affiche quand un utilisateur Free tente d'utiliser le layout Éco
 * - Contenu spécifique selon les spécifications PR8
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Crown, CheckCircle, ArrowLeft } from "lucide-react";

const PremiumEcoModal = ({ 
  isOpen, 
  onClose,
  onStayClassic = null  // Callback pour rester en Classic
}) => {
  const navigate = useNavigate();

  const handleUpgrade = () => {
    onClose();
    navigate('/pricing');
  };

  const handleStayClassic = () => {
    if (onStayClassic) {
      onStayClassic();
    }
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <div className="flex items-center justify-center mb-4">
            <Crown className="h-12 w-12 text-yellow-500" />
          </div>
          <DialogTitle className="text-2xl text-center">
            Mode Éco — Premium
          </DialogTitle>
          <DialogDescription className="text-center text-base mt-2">
            Imprimez mieux, utilisez moins de papier.
          </DialogDescription>
        </DialogHeader>

        <div className="py-6 space-y-4">
          <ul className="space-y-3">
            <li className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-gray-700">
                Mise en page 2 colonnes (économie de pages)
              </span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-gray-700">
                Rendu professionnel (style manuel scolaire)
              </span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-gray-700">
                Personnalisation (logo, en-tête/pied de page)
              </span>
            </li>
            <li className="flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
              <span className="text-sm text-gray-700">
                Générations illimitées
              </span>
            </li>
          </ul>
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button
            onClick={handleUpgrade}
            className="w-full sm:w-auto bg-yellow-500 hover:bg-yellow-600 text-white"
          >
            <Crown className="h-4 w-4 mr-2" />
            Passer Premium
          </Button>
          <Button
            variant="outline"
            onClick={handleStayClassic}
            className="w-full sm:w-auto"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Rester en Classic
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default PremiumEcoModal;

