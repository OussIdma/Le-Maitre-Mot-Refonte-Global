/**
 * UpgradeProModal - Modal réutilisable pour conversion Premium (P2.3)
 * 
 * Affiche la valeur Pro de manière contextuelle selon l'action déclencheuse.
 * Non-bloquant, fermable, pas redondant (1 affichage / session).
 */

import React, { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "./ui/dialog";
import { Button } from "./ui/button";
import { Check, Sparkles, FileDown, Palette, Layers, Zap, Crown } from "lucide-react";
import { useNavigate } from "react-router-dom";

// P2.3: Track modal opens per session (prevent redundancy)
const MODAL_SESSION_KEY = 'upgrade_pro_modal_shown';

const UpgradeProModal = ({ 
  isOpen, 
  onClose, 
  context = 'general' // 'export', 'variant', 'branding', 'generator', 'general'
}) => {
  const navigate = useNavigate();
  const [hasBeenShown, setHasBeenShown] = useState(false);

  // P2.3: Check if modal already shown this session
  useEffect(() => {
    if (isOpen && !hasBeenShown) {
      const shown = sessionStorage.getItem(MODAL_SESSION_KEY);
      if (shown) {
        setHasBeenShown(true);
        onClose(); // Auto-close if already shown
        return;
      }
      // Mark as shown
      sessionStorage.setItem(MODAL_SESSION_KEY, 'true');
      setHasBeenShown(true);
      
      // P2.3: Track event
      trackPremiumEvent('upgrade_modal_opened', { context });
    }
  }, [isOpen, hasBeenShown, context, onClose]);

  const handleStartTrial = () => {
    trackPremiumEvent('upgrade_converted', { context });
    onClose();
    navigate('/pricing');
  };

  // P2.3: Contextual benefits based on trigger
  const getContextualBenefits = () => {
    const allBenefits = [
      {
        icon: <FileDown className="h-5 w-5 text-blue-600" />,
        iconBg: "bg-blue-100",
        title: "Exports PDF illimités",
        description: "Créez et exportez autant de sujets que nécessaire sans limite"
      },
      {
        icon: <Layers className="h-5 w-5 text-purple-600" />,
        iconBg: "bg-purple-100",
        title: "Variantes A/B/C",
        description: "Générez plusieurs versions d'un même exercice pour vos évaluations"
      },
      {
        icon: <Palette className="h-5 w-5 text-green-600" />,
        iconBg: "bg-green-100",
        title: "Branding personnalisé",
        description: "Ajoutez votre logo et personnalisez vos documents avec vos templates"
      },
      {
        icon: <Zap className="h-5 w-5 text-orange-600" />,
        iconBg: "bg-orange-100",
        title: "Générateurs avancés",
        description: "Accédez à tous les générateurs premium et leurs variantes"
      },
      {
        icon: <Crown className="h-5 w-5 text-yellow-600" />,
        iconBg: "bg-yellow-100",
        title: "Bibliothèque & réutilisation",
        description: "Sauvegardez et réutilisez vos exercices et documents"
      }
    ];

    // Filter benefits based on context
    switch (context) {
      case 'export':
        return allBenefits.filter(b => 
          b.title.includes('Exports') || 
          b.title.includes('Branding') || 
          b.title.includes('Bibliothèque')
        );
      case 'variant':
        return allBenefits.filter(b => 
          b.title.includes('Variantes') || 
          b.title.includes('Générateurs')
        );
      case 'branding':
        return allBenefits.filter(b => 
          b.title.includes('Branding') || 
          b.title.includes('Exports')
        );
      case 'generator':
        return allBenefits.filter(b => 
          b.title.includes('Générateurs') || 
          b.title.includes('Variantes')
        );
      default:
        return allBenefits.slice(0, 4); // Show top 4 for general
    }
  };

  const benefits = getContextualBenefits();

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[550px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-2xl">
            <Sparkles className="h-6 w-6 text-purple-600" />
            Débloquez Le Maître Mot Pro
          </DialogTitle>
          <DialogDescription className="text-base">
            Accédez à toutes les fonctionnalités avancées pour un enseignement personnalisé
          </DialogDescription>
        </DialogHeader>

        <div className="py-6 space-y-4">
          {benefits.map((benefit, index) => (
            <div key={index} className="flex items-start gap-3">
              <div className={`mt-1 p-2 ${benefit.iconBg} rounded-lg`}>
                {benefit.icon}
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-1">
                  {benefit.title}
                </h4>
                <p className="text-sm text-gray-600">
                  {benefit.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        <DialogFooter className="flex flex-col sm:flex-row gap-2">
          <Button
            onClick={handleStartTrial}
            className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white"
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
            Plus tard
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

// P2.3: Track premium events (instrumentation)
export const trackPremiumEvent = (eventName, data = {}) => {
  const eventData = {
    event: eventName,
    timestamp: new Date().toISOString(),
    ...data
  };
  
  // Log to console (ready for analytics integration later)
  console.log('📊 Premium Event:', eventData);
  
  // Store in localStorage for debugging
  try {
    const events = JSON.parse(localStorage.getItem('premium_events') || '[]');
    events.push(eventData);
    // Keep only last 50 events
    if (events.length > 50) {
      events.shift();
    }
    localStorage.setItem('premium_events', JSON.stringify(events));
  } catch (e) {
    console.error('Error storing premium event:', e);
  }
};

export default UpgradeProModal;




