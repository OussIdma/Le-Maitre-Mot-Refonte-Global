import React, { useState, useEffect } from "react";
import { Card, CardContent } from "../ui/card";
import { Stepper, StepperContent, StepperNavigation } from "../ui/stepper";
import { cn } from "../../lib/utils";

// Import step components
import Step1ProgrammeScolaire from "./Step1ProgrammeScolaire";
import Step2ParametresDocument from "./Step2ParametresDocument";
import Step3GenerationApercu from "./Step3GenerationApercu";
import Step4ExportTelechargement from "./Step4ExportTelechargement";

const DocumentWizard = ({ 
  // Curriculum data
  matieres,
  niveaux, 
  chapitres,
  catalogStats,  // Add catalogStats prop
  // Current selections
  selectedMatiere,
  selectedNiveau,
  selectedChapitre,
  typeDoc,
  difficulte,
  nbExercices,
  // Handlers
  onMatiereChange,
  onNiveauChange,
  onChapitreChange,
  onTypeDocChange,
  onDifficulteChange,
  onNbExercicesChange,
  // Document loading
  openedDocument,
  onDocumentOpened,
  // Generation
  isGenerating,
  currentDocument,
  onGenerate,
  onVaryExercise,
  // Export
  exportStyles,
  selectedExportStyle,
  onExportStyleChange,
  exportingSubject,
  exportingSolution,
  onExportPDF,
  // Template settings
  isPro,
  sessionToken,
  onTemplateChange,
  // Quota/Pro status
  quotaStatus,
  quotaLoaded,
  userEmail,
  onCheckProStatus,
  onShowPaymentModal,
  // Loading states
  isLoading = false
}) => {
  const [currentStep, setCurrentStep] = useState(1);

  // Handle opening a recent document
  useEffect(() => {
    if (openedDocument && onDocumentOpened) {
      // Pre-fill wizard data from the opened document
      onMatiereChange(openedDocument.matiere);
      onNiveauChange(openedDocument.niveau);
      onChapitreChange(openedDocument.chapitre);
      onTypeDocChange(openedDocument.type_doc);
      onDifficulteChange(openedDocument.difficulte);
      onNbExercicesChange(openedDocument.nb_exercices);
      
      // Jump to step 3 (Generation) since steps 1 & 2 are pre-filled
      setCurrentStep(3);
      
      // Clear the opened document flag
      onDocumentOpened();
    }
  }, [openedDocument, onDocumentOpened, onMatiereChange, onNiveauChange, onChapitreChange, onTypeDocChange, onDifficulteChange, onNbExercicesChange]);

  // Define wizard steps
  const steps = [
    {
      id: 'programme',
      title: 'Programme scolaire',
      description: 'Matière, niveau, chapitre',
      clickable: true
    },
    {
      id: 'parametres',
      title: 'Paramètres',
      description: 'Type, difficulté, options',
      clickable: true
    },
    {
      id: 'generation',
      title: 'Génération',
      description: 'Création du document',
      clickable: true
    },
    {
      id: 'export',
      title: 'Export',
      description: 'Téléchargement PDF',
      clickable: true
    }
  ];

  // Check if current step is valid/complete
  const isStepComplete = (stepNumber) => {
    switch (stepNumber) {
      case 1:
        return selectedMatiere && selectedNiveau && selectedChapitre;
      case 2:
        return typeDoc && difficulte && nbExercices;
      case 3:
        return currentDocument;
      case 4:
        return currentDocument;
      default:
        return false;
    }
  };

  // Check if we can proceed to next step
  const canProceedToNext = () => {
    return isStepComplete(currentStep);
  };

  // Navigation handlers
  const handleNext = () => {
    if (currentStep < steps.length && canProceedToNext()) {
      setCurrentStep(currentStep + 1);
    } else if (currentStep === steps.length) {
      // Handle "Terminé" button - reset wizard to step 1
      setCurrentStep(1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepClick = (stepNumber) => {
    // Allow clicking on completed steps or current step
    if (stepNumber <= currentStep || isStepComplete(stepNumber - 1)) {
      setCurrentStep(stepNumber);
    }
  };

  // Auto-advance to generation step after parameters are complete
  useEffect(() => {
    if (currentStep === 2 && isStepComplete(2) && !currentDocument) {
      // Don't auto-advance, let user click Next
    }
  }, [currentStep, typeDoc, difficulte, nbExercices, currentDocument]);

  // Auto-advance to export step after document is generated
  useEffect(() => {
    if (currentStep === 3 && currentDocument) {
      // Don't auto-advance, let user proceed manually
    }
  }, [currentStep, currentDocument]);

  // Render current step content
  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <Step1ProgrammeScolaire
            matieres={matieres}
            niveaux={niveaux}
            chapitres={chapitres}
            selectedMatiere={selectedMatiere}
            selectedNiveau={selectedNiveau}
            selectedChapitre={selectedChapitre}
            onMatiereChange={onMatiereChange}
            onNiveauChange={onNiveauChange}
            onChapitreChange={onChapitreChange}
            catalogStats={catalogStats}  // Pass catalog stats
            isLoading={isLoading}
          />
        );
      case 2:
        return (
          <Step2ParametresDocument
            typeDoc={typeDoc}
            difficulte={difficulte}
            nbExercices={nbExercices}
            onTypeDocChange={onTypeDocChange}
            onDifficulteChange={onDifficulteChange}
            onNbExercicesChange={onNbExercicesChange}
            isPro={isPro}
            sessionToken={sessionToken}
            onTemplateChange={onTemplateChange}
            isLoading={isLoading}
          />
        );
      case 3:
        return (
          <Step3GenerationApercu
            selectedMatiere={selectedMatiere}
            selectedNiveau={selectedNiveau}
            selectedChapitre={selectedChapitre}
            typeDoc={typeDoc}
            difficulte={difficulte}
            nbExercices={nbExercices}
            isGenerating={isGenerating}
            currentDocument={currentDocument}
            onGenerate={onGenerate}
            onVaryExercise={onVaryExercise}
            isLoading={isLoading}
          />
        );
      case 4:
        return (
          <Step4ExportTelechargement
            currentDocument={currentDocument}
            exportStyles={exportStyles}
            selectedExportStyle={selectedExportStyle}
            onExportStyleChange={onExportStyleChange}
            exportingSubject={exportingSubject}
            exportingSolution={exportingSolution}
            onExportPDF={onExportPDF}
            isPro={isPro}
            quotaStatus={quotaStatus}
            quotaLoaded={quotaLoaded}
            userEmail={userEmail}
            onCheckProStatus={onCheckProStatus}
            onShowPaymentModal={onShowPaymentModal}
            isLoading={isLoading}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Stepper Header - Always visible on desktop, hidden on mobile */}
      <Card className="shadow-lg border-0 bg-white/90 backdrop-blur-sm">
        <CardContent className="p-6">
          <div className="hidden md:block">
            <Stepper
              steps={steps}
              currentStep={currentStep}
              onStepClick={handleStepClick}
              className="mb-6"
            />
          </div>
          
          {/* Mobile step indicator */}
          <div className="md:hidden mb-6">
            <div className="text-center">
              <p className="text-sm text-gray-600 mb-2">
                Étape {currentStep} sur {steps.length}
              </p>
              <h2 className="text-lg font-semibold text-gray-900">
                {steps[currentStep - 1].title}
              </h2>
              <p className="text-sm text-gray-500">
                {steps[currentStep - 1].description}
              </p>
              
              {/* Progress bar for mobile */}
              <div className="w-full bg-gray-200 rounded-full h-2 mt-3">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(currentStep / steps.length) * 100}%` }}
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <StepperContent>
        {renderStepContent()}
      </StepperContent>

      {/* Navigation */}
      <Card className="shadow-lg border-0 bg-white/90 backdrop-blur-sm">
        <CardContent className="p-6">
          <StepperNavigation
            currentStep={currentStep}
            totalSteps={steps.length}
            onPrevious={handlePrevious}
            onNext={handleNext}
            isNextDisabled={!canProceedToNext() || isGenerating || isLoading}
            nextLabel={currentStep === steps.length ? "Terminé" : "Suivant"}
            previousLabel="Précédent"
          />
          
          {/* Step completion status */}
          <div className="mt-4 text-center text-xs text-gray-500">
            {!canProceedToNext() && currentStep < steps.length && (
              <p>
                {currentStep === 1 && "Sélectionnez une matière, un niveau et un chapitre pour continuer"}
                {currentStep === 2 && "Configurez le type de document, la difficulté et le nombre d'exercices"}
                {currentStep === 3 && "Générez votre document pour accéder aux options d'export"}
              </p>
            )}
            {canProceedToNext() && currentStep < steps.length && (
              <p className="text-green-600">
                ✓ Étape complète - Cliquez sur "Suivant" pour continuer
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocumentWizard;