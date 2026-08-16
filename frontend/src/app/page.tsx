import TradingChart from "@/components/TradingChart";
import SentimentWidget from "@/components/SentimentWidget";

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-2 pb-4 border-b border-slate-200">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900">
              PROFIT Dashboard
            </h1>
            <p className="text-sm text-slate-500">
              Portfolio Reinforcement Optimization using Financial Intelligence Techniques
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-3 py-1 text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 rounded-full">
              Asset: AAPL
            </span>
          </div>
        </header>

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
          {/* Main Chart Area: spans 2 columns on desktop */}
          <div className="lg:col-span-2">
            <TradingChart ticker="AAPL" />
          </div>

          {/* Sentiment Stream: spans 1 column */}
          <div className="lg:col-span-1">
            <SentimentWidget ticker="AAPL" />
          </div>
        </section>
      </div>
    </main>
  );
}