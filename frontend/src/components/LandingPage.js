/**
 * LandingPage - Page d'accueil avec CTA vers /generer
 */

import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { GraduationCap, Sparkles, BookOpen, ArrowRight } from "lucide-react";

function LandingPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex items-center justify-center mb-6">
            <GraduationCap className="h-16 w-16 text-blue-600 mr-4" />
            <h1 className="text-5xl font-bold text-gray-900">{t('landing.title')}</h1>
          </div>
          <p className="text-2xl text-gray-600 max-w-3xl mx-auto mb-8">
            {t('landing.subtitle')}
          </p>
          
          {/* CTA Principal */}
          <Button
            size="lg"
            onClick={() => navigate('/generer')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg"
          >
            <Sparkles className="h-5 w-5 mr-2" />
            {t('landing.cta')}
            <ArrowRight className="h-5 w-5 ml-2" />
          </Button>
        </div>

        {/* Features Cards */}
        <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto mb-16">
          <Card className="border-2 hover:border-blue-300 transition-colors">
            <CardHeader>
              <Sparkles className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>{t('landing.feature1Title')}</CardTitle>
              <CardDescription>
                {t('landing.feature1Desc')}
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-blue-300 transition-colors">
            <CardHeader>
              <BookOpen className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>{t('landing.feature2Title')}</CardTitle>
              <CardDescription>
                {t('landing.feature2Desc')}
              </CardDescription>
            </CardHeader>
          </Card>

          <Card className="border-2 hover:border-blue-300 transition-colors">
            <CardHeader>
              <GraduationCap className="h-8 w-8 text-blue-600 mb-2" />
              <CardTitle>{t('landing.feature3Title')}</CardTitle>
              <CardDescription>
                {t('landing.feature3Desc')}
              </CardDescription>
            </CardHeader>
          </Card>
        </div>

        {/* Secondary CTA */}
        <div className="text-center">
          <p className="text-gray-600 mb-4">
            {t('landing.readyToStart')}
          </p>
          <Button
            variant="outline"
            size="lg"
            onClick={() => navigate('/generer')}
            className="border-2 border-blue-600 text-blue-600 hover:bg-blue-50"
          >
            {t('landing.accessGenerator')}
            <ArrowRight className="h-5 w-5 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default LandingPage;

