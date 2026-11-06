import React, { useState } from 'react';
import { AnalysisResponse, FEEDBACK_SOURCES, ANALYSIS_GOALS } from '../types';
import { SentimentChart } from './SentimentChart';
import { ThemeCard } from './ThemeCard';
import { RecommendationCard } from './RecommendationCard';
import { getExportJsonUrl, getExportCsvUrl } from '../api';
import { 
  Download, 
  FileJson, 
  FileSpreadsheet, 
  Printer, 
  PlusCircle, 
  CheckCircle2, 
  AlertTriangle, 
  HelpCircle, 
  Lightbulb, 
  Sparkles,
  Info,
  Calendar,
  Layers,
  Target,
  ExternalLink,
  Youtube,
  MessageSquare,
  Video
} from 'lucide-react';

interface DashboardProps {
  analysis: AnalysisResponse;
  onNewAnalysis: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({
  analysis,
  onNewAnalysis,
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'themes' | 'recommendations' | 'deepdive'>('overview');
  const result = analysis.result;

  const sourceObj = FEEDBACK_SOURCES.find(s => s.value === analysis.feedback_source);
  const goalObj = ANALYSIS_GOALS.find(g => g.value === analysis.analysis_goal);

  const formattedDate = analysis.created_at 
    ? new Date(analysis.created_at).toLocaleDateString(undefined, { 
        month: 'short', 
        day: 'numeric', 
        year: 'numeric', 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    : 'Just now';

  return (
    <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Simulation Banner */}
      {result.is_simulated && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 flex items-start justify-between gap-3 text-amber-900 text-xs sm:text-sm">
          <div className="flex items-start gap-2.5">
            <Info className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Smart Heuristic Simulation Active: </span>
              Analysis generated using built-in NLP heuristics. To activate real frontier LLM analysis, set your{' '}
              <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-bold">OPENAI_API_KEY</code>{' '}
              in <code className="bg-amber-100 px-1 py-0.5 rounded font-mono font-bold">backend/.env</code>.
            </div>
          </div>
        </div>
      )}

      {/* Social Media Content Card if available */}
      {analysis.social_metadata && (
        <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-5 animate-fadeIn">
          <div className="flex items-center gap-4">
            {analysis.social_metadata.thumbnail_url ? (
              <img
                src={analysis.social_metadata.thumbnail_url}
                alt="Thumbnail"
                className="w-24 h-16 object-cover rounded-2xl border border-slate-200 shadow-sm flex-shrink-0"
              />
            ) : (
              <div className="w-16 h-16 rounded-2xl bg-orange-100 text-orange-600 flex items-center justify-center flex-shrink-0">
                <MessageSquare className="w-8 h-8" />
              </div>
            )}
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-red-100 text-red-700 flex items-center gap-1">
                  {analysis.social_metadata.scope === 'short' ? (
                    <>
                      <Video className="w-3 h-3" /> YouTube Short
                    </>
                  ) : analysis.social_metadata.scope === 'channel' ? (
                    <>
                      <Layers className="w-3 h-3" /> YouTube Channel
                    </>
                  ) : analysis.social_metadata.platform === 'reddit' ? (
                    <>
                      <MessageSquare className="w-3 h-3" /> Reddit Thread
                    </>
                  ) : (
                    <>
                      <Youtube className="w-3 h-3" /> YouTube Video
                    </>
                  )}
                </span>
                <span className="text-xs text-slate-500 font-medium">
                  by <strong className="text-slate-800 font-bold">{analysis.social_metadata.author}</strong>
                </span>
              </div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 leading-snug">
                {analysis.social_metadata.title}
              </h2>
              {analysis.social_metadata.stats && (
                <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                  {analysis.social_metadata.stats.view_count && (
                    <span>{Number(analysis.social_metadata.stats.view_count).toLocaleString()} views</span>
                  )}
                  {analysis.social_metadata.stats.like_count && (
                    <>
                      <span>•</span>
                      <span>{Number(analysis.social_metadata.stats.like_count).toLocaleString()} likes</span>
                    </>
                  )}
                  <span>•</span>
                  <span>{analysis.item_count} comments analyzed</span>
                </div>
              )}
            </div>
          </div>

          {analysis.social_metadata.url && (
            <a
              href={analysis.social_metadata.url}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors whitespace-nowrap"
            >
              <span>View Source</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          )}
        </div>
      )}

      {/* Top Header Card */}
      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-slate-200/90 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div>
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="px-3 py-1 rounded-full bg-brand-50 text-brand-700 text-xs font-bold border border-brand-200 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              {sourceObj?.label || analysis.feedback_source}
            </span>
            <span className="px-3 py-1 rounded-full bg-slate-100 text-slate-700 text-xs font-bold border border-slate-200 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" />
              {goalObj?.label || analysis.analysis_goal}
            </span>
            <span className="text-xs text-slate-500 flex items-center gap-1 ml-1">
              <Calendar className="w-3.5 h-3.5" />
              {formattedDate}
            </span>
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Feedback Intelligence Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Synthesized from <strong className="text-slate-800 font-bold">{analysis.item_count}</strong> feedback items
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-2.5">
          <a
            href={getExportJsonUrl(analysis.id)}
            download
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
          >
            <FileJson className="w-4 h-4 text-slate-600" />
            <span>JSON</span>
          </a>

          <a
            href={getExportCsvUrl(analysis.id)}
            download
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            <span>CSV</span>
          </a>

          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
          >
            <Printer className="w-4 h-4 text-slate-600" />
            <span className="hidden sm:inline">Print</span>
          </button>

          <button
            onClick={onNewAnalysis}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-700 text-white font-bold text-xs shadow-sm transition-all"
          >
            <PlusCircle className="w-4 h-4" />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {/* Executive Summary Card */}
      <div className="bg-gradient-to-br from-brand-900 to-indigo-950 rounded-3xl p-6 sm:p-8 text-white shadow-xl">
        <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-brand-300 mb-3">
          <Sparkles className="w-4 h-4 text-brand-400" />
          <span>Executive Summary</span>
        </div>
        <p className="text-base sm:text-lg text-slate-100 font-medium leading-relaxed">
          {result.executive_summary}
        </p>

        <div className="mt-6 pt-6 border-t border-brand-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <div className="text-xs text-brand-300 font-medium">Primary Sentiment</div>
            <div className="text-xl font-bold capitalize text-white mt-0.5">{result.overall_sentiment}</div>
          </div>
          <div>
            <div className="text-xs text-brand-300 font-medium">Positive Ratio</div>
            <div className="text-xl font-bold text-emerald-400 mt-0.5">{result.sentiment_distribution.positive}%</div>
          </div>
          <div>
            <div className="text-xs text-brand-300 font-medium">Negative Ratio</div>
            <div className="text-xl font-bold text-rose-400 mt-0.5">{result.sentiment_distribution.negative}%</div>
          </div>
          <div>
            <div className="text-xs text-brand-300 font-medium">Identified Themes</div>
            <div className="text-xl font-bold text-indigo-300 mt-0.5">{result.key_themes.length}</div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
        <button
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'overview'
              ? 'bg-brand-50 text-brand-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          1. Sentiment & Emotions
        </button>
        <button
          onClick={() => setActiveTab('themes')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'themes'
              ? 'bg-brand-50 text-brand-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          2. Key Themes ({result.key_themes.length})
        </button>
        <button
          onClick={() => setActiveTab('recommendations')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'recommendations'
              ? 'bg-brand-50 text-brand-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          3. Prioritized Actions ({result.recommendations.length})
        </button>
        <button
          onClick={() => setActiveTab('deepdive')}
          className={`px-4 py-2 rounded-xl text-sm font-bold transition-all ${
            activeTab === 'deepdive'
              ? 'bg-brand-50 text-brand-700 shadow-sm'
              : 'text-slate-600 hover:text-slate-900'
          }`}
        >
          4. Voice-of-Customer Deep Dive
        </button>
      </div>

      {/* Tab 1: Sentiment & Emotions */}
      {activeTab === 'overview' && (
        <section className="space-y-6">
          <SentimentChart
            distribution={result.sentiment_distribution}
            emotions={result.emotion_breakdown}
            aspects={result.aspect_sentiments}
            overall={result.overall_sentiment}
          />
        </section>
      )}

      {/* Tab 2: Key Themes */}
      {activeTab === 'themes' && (
        <section className="space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Recurring Themes & Patterns
            </h2>
            <p className="text-sm text-slate-500">
              Clustered by topic with frequency weighting, urgency levels, and verbatim evidence.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {result.key_themes.map((theme, idx) => (
              <ThemeCard key={idx} theme={theme} />
            ))}
          </div>
        </section>
      )}

      {/* Tab 3: Actionable Recommendations */}
      {activeTab === 'recommendations' && (
        <section className="space-y-6">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              Prioritized Action Plan
            </h2>
            <p className="text-sm text-slate-500">
              Context-aware recommendations ranked by urgency and projected business impact.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {result.recommendations.map((rec, idx) => (
              <RecommendationCard key={idx} recommendation={rec} rank={idx + 1} />
            ))}
          </div>
        </section>
      )}

      {/* Tab 4: Voice-of-Customer Deep Dive */}
      {activeTab === 'deepdive' && (
        <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Complaints */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 text-rose-700 font-bold text-sm mb-4">
              <AlertTriangle className="w-4 h-4 text-rose-600" />
              <span>Common Complaints & Friction Points</span>
            </div>
            <ul className="space-y-2.5">
              {result.common_complaints.map((item, idx) => (
                <li key={idx} className="p-3 rounded-xl bg-rose-50/70 border border-rose-100 text-xs sm:text-sm text-rose-900 font-medium">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Recurring Questions */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 text-indigo-700 font-bold text-sm mb-4">
              <HelpCircle className="w-4 h-4 text-indigo-600" />
              <span>Recurring User Questions</span>
            </div>
            <ul className="space-y-2.5">
              {result.recurring_questions.map((item, idx) => (
                <li key={idx} className="p-3 rounded-xl bg-indigo-50/70 border border-indigo-100 text-xs sm:text-sm text-indigo-900 font-medium">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Suggestions */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 text-emerald-700 font-bold text-sm mb-4">
              <Lightbulb className="w-4 h-4 text-emerald-600" />
              <span>User Suggestions</span>
            </div>
            <ul className="space-y-2.5">
              {result.suggestions.map((item, idx) => (
                <li key={idx} className="p-3 rounded-xl bg-emerald-50/70 border border-emerald-100 text-xs sm:text-sm text-emerald-900 font-medium">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Feature Requests */}
          <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm">
            <div className="flex items-center gap-2 text-brand-700 font-bold text-sm mb-4">
              <Sparkles className="w-4 h-4 text-brand-600" />
              <span>Specific Feature / Content Requests</span>
            </div>
            <ul className="space-y-2.5">
              {result.feature_requests.map((item, idx) => (
                <li key={idx} className="p-3 rounded-xl bg-brand-50/70 border border-brand-100 text-xs sm:text-sm text-brand-900 font-medium">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </div>
  );
};
