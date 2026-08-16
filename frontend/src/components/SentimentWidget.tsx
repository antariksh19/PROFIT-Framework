"use client";

import { useEffect, useState } from "react";

interface SentimentLog {
  published_at: string;
  headline: string;
  sentiment_score: number;
  label: "positive" | "negative" | "neutral";
}

interface SentimentData {
  ticker: string;
  average_sentiment_score: number;
  total_logs: number;
  logs: SentimentLog[];
}

export default function SentimentWidget({ ticker }: { ticker: string }) {
  const [data, setData] = useState<SentimentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSentiment = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/sentiment/${ticker}`);
        if (!response.ok) throw new Error("Failed to fetch sentiment logs");
        const json = await response.json();
        setData(json);
        setLoading(false);
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError("An unknown error occurred");
        }
        setLoading(false);
      }
    };

    fetchSentiment();
  }, [ticker]);

  const getBadgeStyle = (label: string) => {
    switch (label) {
      case "positive":
        return "bg-emerald-100 text-emerald-700 border-emerald-300";
      case "negative":
        return "bg-rose-100 text-rose-700 border-rose-300";
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
    }
  };

  const getAggregateBadge = (score: number) => {
    if (score > 0.15) {
      return { text: "Bullish", className: "bg-emerald-600 text-white" };
    }
    if (score < -0.15) {
      return { text: "Bearish", className: "bg-rose-600 text-white" };
    }
    return { text: "Neutral", className: "bg-amber-500 text-white" };
  };

  return (
    <div className="w-full h-full p-5 border border-slate-200 rounded-xl shadow-sm bg-white flex flex-col">
      <div className="flex items-center justify-between pb-4 mb-4 border-b border-slate-100">
        <div>
          <h3 className="text-lg font-bold text-slate-900">FinBERT Market Sentiment</h3>
          <p className="text-xs text-slate-500">Live NLP analysis from financial feeds</p>
        </div>
        {data && (
          <div className="text-right">
            <span
              className={`px-2.5 py-1 text-xs font-semibold rounded-md shadow-sm ${
                getAggregateBadge(data.average_sentiment_score).className
              }`}
            >
              {getAggregateBadge(data.average_sentiment_score).text}
            </span>
            <p className="text-xs font-mono text-slate-600 mt-1">
              Score: {data.average_sentiment_score > 0 ? `+` : ``}
              {data.average_sentiment_score.toFixed(4)}
            </p>
          </div>
        )}
      </div>

      {loading && <p className="text-sm text-slate-400">Loading sentiment stream...</p>}
      {error && <p className="text-sm text-rose-500 font-medium">{error}</p>}

      <div className="space-y-3 overflow-y-auto max-h-[480px] pr-1">
        {data?.logs.map((item, idx) => (
          <div
            key={idx}
            className="p-3 border border-slate-100 rounded-lg hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center justify-between gap-2 mb-1.5">
              <span
                className={`px-2 py-0.5 text-[11px] font-medium border rounded uppercase tracking-wider ${getBadgeStyle(
                  item.label
                )}`}
              >
                {item.label} ({item.sentiment_score > 0 ? `+` : ``}
                {item.sentiment_score.toFixed(2)})
              </span>
              <span className="text-[11px] text-slate-400">
                {new Date(item.published_at).toLocaleDateString([], {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <p className="text-sm text-slate-800 leading-snug font-normal">{item.headline}</p>
          </div>
        ))}
      </div>
    </div>
  );
}