import TradingChart from "@/components/TradingChart";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">PROFIT Dashboard</h1>
          <p className="text-gray-600">Portfolio Reinforcement Optimization using Financial Intelligence Techniques</p>
        </header>

        <section className="grid grid-cols-1 gap-8">
          <TradingChart ticker="AAPL" />
        </section>
      </div>
    </main>
  );
}