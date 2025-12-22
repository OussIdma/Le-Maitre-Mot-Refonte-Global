import React from 'react';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

const MathRenderer = ({ content, className = "" }) => {
  // Protection critique : afficher un message d'erreur visible si pas de contenu
  if (!content) {
    console.error("⚠️ MathRenderer: Contenu vide ou undefined reçu");
    return (
      <div className={`math-renderer-error ${className}`} style={{
        padding: '12px',
        backgroundColor: '#fff3cd',
        border: '1px solid #ffc107',
        borderRadius: '4px',
        color: '#856404',
        fontSize: '14px'
      }}>
        ⚠️ Erreur : Énoncé manquant ou vide. Veuillez regénérer l'exercice.
      </div>
    );
  }

  // Regular expressions for LaTeX patterns
  const LATEX_PATTERNS = {
    // Inline math: \frac{a}{b}, \sqrt{x}, x^{2}
    inline: /\\(?:frac\{[^}]+\}\{[^}]+\}|sqrt\{[^}]+\}|[a-zA-Z0-9]+\^\{[^}]+\})/g,
    // Display math (optional for future): $$...$$
    display: /\$\$([^$]+)\$\$/g
  };

  const renderMathContent = (text) => {
    if (!text || typeof text !== 'string') return text;

    // Check if the text contains LaTeX expressions
    const hasInlineMath = LATEX_PATTERNS.inline.test(text);
    const hasDisplayMath = LATEX_PATTERNS.display.test(text);

    if (!hasInlineMath && !hasDisplayMath) {
      // No math expressions found, return as plain text
      return <span dangerouslySetInnerHTML={{ __html: text }} />;
    }

    try {
      // Split text by math expressions and render each part
      const parts = [];
      let lastIndex = 0;
      let match;

      // Reset regex lastIndex
      LATEX_PATTERNS.inline.lastIndex = 0;

      // Process inline math expressions
      while ((match = LATEX_PATTERNS.inline.exec(text)) !== null) {
        const beforeMath = text.slice(lastIndex, match.index);
        if (beforeMath) {
          parts.push(
            <span 
              key={`text-${parts.length}`} 
              dangerouslySetInnerHTML={{ __html: beforeMath }} 
            />
          );
        }

        // Add the math expression
        const mathExpression = match[0];
        try {
          parts.push(
            <InlineMath 
              key={`math-${parts.length}`} 
              math={mathExpression}
            />
          );
        } catch (mathError) {
          console.warn(`Failed to render math expression: ${mathExpression}`, mathError);
          // Fallback to formatted text
          const fallback = formatMathFallback(mathExpression);
          parts.push(
            <span 
              key={`fallback-${parts.length}`}
              className="math-fallback"
              dangerouslySetInnerHTML={{ __html: fallback }}
            />
          );
        }

        lastIndex = match.index + match[0].length;
      }

      // Add any remaining text
      const remainingText = text.slice(lastIndex);
      if (remainingText) {
        parts.push(
          <span 
            key={`text-${parts.length}`} 
            dangerouslySetInnerHTML={{ __html: remainingText }} 
          />
        );
      }

      return <span className={className}>{parts}</span>;

    } catch (error) {
      console.error('Error rendering math content:', error);
      // Fallback to original content
      return <span dangerouslySetInnerHTML={{ __html: text }} />;
    }
  };

  const formatMathFallback = (mathExpression) => {
    try {
      // Convert common LaTeX expressions to HTML for fallback
      let formatted = mathExpression;

      // Convert fractions \frac{a}{b} to a/b with better styling
      formatted = formatted.replace(
        /\\frac\{([^}]+)\}\{([^}]+)\}/g,
        '<sup>$1</sup>/<sub>$2</sub>'
      );

      // Convert square roots \sqrt{x} to √(x)
      formatted = formatted.replace(
        /\\sqrt\{([^}]+)\}/g,
        '√($1)'
      );

      // Convert powers x^{n} to x^n with superscript
      formatted = formatted.replace(
        /([a-zA-Z0-9]+)\^\{([^}]+)\}/g,
        '$1<sup>$2</sup>'
      );

      return formatted;
    } catch (error) {
      console.warn('Error formatting math fallback:', error);
      return mathExpression; // Return original if formatting fails
    }
  };

  return (
    <div className={`math-renderer ${className}`}>
      {renderMathContent(content)}
    </div>
  );
};

export default MathRenderer;