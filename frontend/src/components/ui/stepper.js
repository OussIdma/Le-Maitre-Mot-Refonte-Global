import React from "react";
import { Check, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

const Stepper = ({ steps, currentStep, onStepClick, className }) => {
  return (
    <nav aria-label="Progression des étapes" className={cn("w-full", className)}>
      <ol className="flex items-center justify-between w-full">
        {steps.map((step, index) => {
          const stepNumber = index + 1;
          const isActive = stepNumber === currentStep;
          const isCompleted = stepNumber < currentStep;
          const isClickable = step.clickable !== false && stepNumber <= currentStep;

          return (
            <li key={step.id} className="flex items-center flex-1">
              <button
                type="button"
                onClick={() => isClickable && onStepClick?.(stepNumber)}
                disabled={!isClickable}
                className={cn(
                  "flex items-center p-2 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
                  isClickable ? "cursor-pointer hover:bg-gray-50" : "cursor-not-allowed",
                  "flex-1 text-left"
                )}
                aria-current={isActive ? "step" : undefined}
                aria-describedby={`step-${stepNumber}-description`}
              >
                <div className="flex items-center">
                  {/* Step Circle */}
                  <div
                    className={cn(
                      "flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold transition-all duration-200",
                      isCompleted
                        ? "bg-green-600 text-white"
                        : isActive
                        ? "bg-blue-600 text-white"
                        : "bg-gray-200 text-gray-600"
                    )}
                  >
                    {isCompleted ? (
                      <Check className="w-4 h-4" aria-hidden="true" />
                    ) : (
                      stepNumber
                    )}
                  </div>

                  {/* Step Content */}
                  <div className="ml-3 min-w-0 flex-1">
                    <p
                      className={cn(
                        "text-sm font-medium transition-colors duration-200",
                        isActive
                          ? "text-blue-600"
                          : isCompleted
                          ? "text-green-600"
                          : "text-gray-500"
                      )}
                    >
                      {step.title}
                    </p>
                    {step.description && (
                      <p
                        id={`step-${stepNumber}-description`}
                        className="text-xs text-gray-500 mt-1"
                      >
                        {step.description}
                      </p>
                    )}
                  </div>
                </div>
              </button>

              {/* Connector */}
              {index < steps.length - 1 && (
                <ChevronRight
                  className={cn(
                    "w-4 h-4 mx-2 transition-colors duration-200",
                    stepNumber < currentStep ? "text-green-600" : "text-gray-300"
                  )}
                  aria-hidden="true"
                />
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};

const StepperContent = ({ children, className }) => {
  return (
    <div className={cn("mt-6", className)} role="tabpanel">
      {children}
    </div>
  );
};

const StepperNavigation = ({ 
  currentStep, 
  totalSteps, 
  onPrevious, 
  onNext, 
  isNextDisabled = false,
  nextLabel = "Suivant",
  previousLabel = "Précédent",
  className 
}) => {
  const isFirstStep = currentStep === 1;
  const isLastStep = currentStep === totalSteps;

  return (
    <div className={cn("flex justify-between mt-6", className)}>
      <button
        type="button"
        onClick={onPrevious}
        disabled={isFirstStep}
        className={cn(
          "px-4 py-2 text-sm font-medium rounded-lg border transition-all duration-200",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
          isFirstStep
            ? "border-gray-200 bg-gray-50 text-gray-400 cursor-not-allowed"
            : "border-gray-300 bg-white text-gray-700 hover:bg-gray-50 hover:border-gray-400"
        )}
        aria-label={`${previousLabel} (étape ${currentStep - 1})`}
      >
        {previousLabel}
      </button>

      <button
        type="button"
        onClick={onNext}
        disabled={isNextDisabled}
        className={cn(
          "px-4 py-2 text-sm font-medium rounded-lg transition-all duration-200",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
          isNextDisabled
            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
            : "bg-blue-600 text-white hover:bg-blue-700"
        )}
        aria-label={`${nextLabel} ${!isLastStep ? `(étape ${currentStep + 1})` : ""}`}
      >
        {nextLabel}
      </button>
    </div>
  );
};

export { Stepper, StepperContent, StepperNavigation };