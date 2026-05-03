import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { Trophy, Scale, TrendingUp, AlertTriangle, CheckCircle2 } from 'lucide-react';

function winnerText(winner, leftLabel, rightLabel) {
  if (winner === 'left') return leftLabel;
  if (winner === 'right') return rightLabel;
  return 'Tie';
}

function SentimentBadge({ sentiment }) {
  const value = String(sentiment || 'neutral').toLowerCase();
  if (value === 'positive') {
    return <span className="px-2 py-1 rounded-full text-xs bg-green-500 bg-opacity-20 text-green-200 border border-green-400 border-opacity-40">Positive</span>;
  }
  if (value === 'negative') {
    return <span className="px-2 py-1 rounded-full text-xs bg-red-500 bg-opacity-20 text-red-200 border border-red-400 border-opacity-40">Negative</span>;
  }
  return <span className="px-2 py-1 rounded-full text-xs bg-gray-500 bg-opacity-20 text-gray-200 border border-gray-400 border-opacity-40">Neutral</span>;
}

export default function ComparisonDashboard({
  data,
  leftLabel = 'Left',
  rightLabel = 'Right',
  accentClass = 'text-purple-200',
  borderClass = 'border-purple-400 border-opacity-20',
  leftColor = '#a855f7',
  rightColor = '#22d3ee',
}) {
  if (!data) {
    return null;
  }

  const comparison = data.comparison || {};
  const leftEntity = data.left_entity || {};
  const rightEntity = data.right_entity || {};

  const metricCards = comparison.metric_cards || [];
  const sentimentChart = comparison.sentiment_chart || [];
  const emotionRadar = comparison.emotion_radar || [];
  const aspectTable = comparison.aspect_table || [];
  const insights = comparison.ai_insights || [];
  const summaryCards = comparison.summary_cards || [];
  const uniqueAdvantages = comparison.unique_advantages || {};

  const leftName = leftEntity.label || leftLabel;
  const rightName = rightEntity.label || rightLabel;

  const metricBars = metricCards.map((item) => ({
    metric: item.label,
    left: item.left_score,
    right: item.right_score,
  }));

  return (
    <div className="space-y-8">
      <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
          <div>
            <p className={`text-sm ${accentClass}`}>Left Target</p>
            <h3 className="text-white text-xl font-semibold">{leftName}</h3>
          </div>
          <div className="text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-black bg-opacity-30 border border-white border-opacity-20">
              <Trophy className="w-4 h-4 text-yellow-300" />
              <span className="text-white text-sm font-semibold">
                Winner: {winnerText(comparison.overall_winner, leftName, rightName)}
              </span>
            </div>
            <p className={`text-sm mt-2 ${accentClass}`}>
              Score Delta: {comparison.score_delta || 0}
            </p>
          </div>
          <div className="text-right">
            <p className={`text-sm ${accentClass}`}>Right Target</p>
            <h3 className="text-white text-xl font-semibold">{rightName}</h3>
          </div>
        </div>
      </div>

      {summaryCards.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-5 gap-4">
          {summaryCards.map((card, index) => (
            <div key={`${card.title}-${index}`} className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-xl p-4 border ${borderClass}`}>
              <p className={`text-xs uppercase tracking-wide ${accentClass}`}>{card.title}</p>
              <p className="text-white text-xl font-bold mt-1">{card.value}</p>
              <p className="text-gray-200 text-sm mt-2">{card.description}</p>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
          <h3 className="text-white text-xl font-semibold mb-5 flex items-center gap-2">
            <Scale className="w-5 h-5" />
            Metric Score Comparison
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={metricBars}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.12)" />
              <XAxis dataKey="metric" stroke="rgba(255,255,255,0.7)" interval={0} angle={-15} textAnchor="end" height={70} />
              <YAxis stroke="rgba(255,255,255,0.7)" domain={[0, 100]} />
              <Tooltip
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.85)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Bar dataKey="left" name={leftName} fill={leftColor} radius={[6, 6, 0, 0]} />
              <Bar dataKey="right" name={rightName} fill={rightColor} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
          <h3 className="text-white text-xl font-semibold mb-5 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Sentiment Comparison
          </h3>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={sentimentChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.12)" />
              <XAxis dataKey="label" stroke="rgba(255,255,255,0.7)" />
              <YAxis stroke="rgba(255,255,255,0.7)" domain={[0, 100]} />
              <Tooltip
                formatter={(value) => `${value}%`}
                contentStyle={{
                  backgroundColor: 'rgba(0,0,0,0.85)',
                  border: '1px solid rgba(255,255,255,0.2)',
                  borderRadius: '8px',
                }}
              />
              <Legend />
              <Bar dataKey="left" name={leftName} fill={leftColor} radius={[6, 6, 0, 0]} />
              <Bar dataKey="right" name={rightName} fill={rightColor} radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
          <h3 className="text-white text-xl font-semibold mb-5">Emotion Radar</h3>
          <ResponsiveContainer width="100%" height={340}>
            <RadarChart data={emotionRadar}>
              <PolarGrid stroke="rgba(255,255,255,0.2)" />
              <PolarAngleAxis dataKey="emotion" tick={{ fill: 'rgba(255,255,255,0.8)', fontSize: 12 }} />
              <PolarRadiusAxis tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 10 }} />
              <Radar name={leftName} dataKey="left" stroke={leftColor} fill={leftColor} fillOpacity={0.35} />
              <Radar name={rightName} dataKey="right" stroke={rightColor} fill={rightColor} fillOpacity={0.3} />
              <Legend />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
          <h3 className="text-white text-xl font-semibold mb-5">Metric Verdicts</h3>
          <div className="space-y-3">
            {metricCards.map((card) => (
              <div key={card.key} className="rounded-xl p-4 bg-black bg-opacity-25 border border-white border-opacity-10">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="text-white font-medium">{card.label}</p>
                  <span className={`text-xs px-2 py-1 rounded-full border border-white border-opacity-20 ${accentClass}`}>
                    Winner: {winnerText(card.winner, leftName, rightName)}
                  </span>
                </div>
                <p className="text-sm text-gray-200 mb-2">
                  {leftName}: {card.left_value}{card.unit} | {rightName}: {card.right_value}{card.unit}
                </p>
                <p className="text-xs text-gray-300">{card.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
        <h3 className="text-white text-xl font-semibold mb-5">Aspect Comparison</h3>
        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
          {aspectTable.length === 0 ? (
            <p className={`text-sm ${accentClass}`}>No aspect-level overlap was detected.</p>
          ) : (
            aspectTable.map((row) => (
              <div key={row.aspect} className="rounded-xl p-4 bg-black bg-opacity-25 border border-white border-opacity-10">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <p className="text-white font-semibold">{row.aspect}</p>
                  <span className={`text-xs px-2 py-1 rounded-full border border-white border-opacity-20 ${accentClass}`}>
                    Winner: {winnerText(row.winner, leftName, rightName)}
                  </span>
                </div>
                <div className="flex flex-wrap gap-3 text-sm">
                  <div className="flex items-center gap-2 text-gray-200">
                    <span>{leftName}:</span>
                    <SentimentBadge sentiment={row.left_sentiment} />
                    <span className="text-xs opacity-80">({row.left_mentions} mentions)</span>
                  </div>
                  <div className="flex items-center gap-2 text-gray-200">
                    <span>{rightName}:</span>
                    <SentimentBadge sentiment={row.right_sentiment} />
                    <span className="text-xs opacity-80">({row.right_mentions} mentions)</span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
          <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-green-300" />
            Shared Strengths
          </h4>
          {(comparison.shared_strengths || []).length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {(comparison.shared_strengths || []).map((item) => (
                <span key={item} className="px-2 py-1 rounded-full text-xs bg-green-500 bg-opacity-20 text-green-200 border border-green-400 border-opacity-40">
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className={`text-sm ${accentClass}`}>No clear shared strengths.</p>
          )}
        </div>

        <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
          <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-300" />
            Shared Complaints
          </h4>
          {(comparison.shared_complaints || []).length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {(comparison.shared_complaints || []).map((item) => (
                <span key={item} className="px-2 py-1 rounded-full text-xs bg-red-500 bg-opacity-20 text-red-200 border border-red-400 border-opacity-40">
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className={`text-sm ${accentClass}`}>No major shared complaints.</p>
          )}
        </div>

        <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
          <h4 className="text-white font-semibold mb-3">Unique Advantages</h4>
          <p className={`text-xs ${accentClass} mb-2`}>{leftName}</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {(uniqueAdvantages.left || []).slice(0, 4).map((item) => (
              <span key={`l-${item}`} className="px-2 py-1 rounded-full text-xs bg-purple-500 bg-opacity-20 text-purple-100 border border-purple-300 border-opacity-40">
                {item}
              </span>
            ))}
          </div>
          <p className={`text-xs ${accentClass} mb-2`}>{rightName}</p>
          <div className="flex flex-wrap gap-2">
            {(uniqueAdvantages.right || []).slice(0, 4).map((item) => (
              <span key={`r-${item}`} className="px-2 py-1 rounded-full text-xs bg-cyan-500 bg-opacity-20 text-cyan-100 border border-cyan-300 border-opacity-40">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className={`bg-white bg-opacity-5 backdrop-blur-lg rounded-2xl p-6 border ${borderClass}`}>
        <h3 className="text-white text-xl font-semibold mb-4">AI Comparative Insights</h3>
        <div className="space-y-3">
          {insights.map((item, index) => (
            <div key={`${index}-${item.slice(0, 20)}`} className="rounded-xl p-4 bg-black bg-opacity-25 border border-white border-opacity-10">
              <p className="text-gray-100">{item}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
