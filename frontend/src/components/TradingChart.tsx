"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, CandlestickSeries } from "lightweight-charts";

export default function TradingChart({ ticker }: { ticker: string }) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#333",
      },
      width: chartContainerRef.current.clientWidth,
      height: 400,
      timeScale: {
        timeVisible: true,
        borderColor: "#D1D5DB",
      },
    });

    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    const fetchData = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/features/${ticker}`);
        if (!response.ok) throw new Error("Failed to fetch data. Is the FastAPI server running?");
        
        const json = await response.json();
        
        const formattedData = json.features.map((item: any) => ({
          time: item.trade_date,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }));

        candlestickSeries.setData(formattedData);
        chart.timeScale().fitContent();
        setLoading(false);
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [ticker]);

  return (
    <div className="w-full max-w-5xl mx-auto p-4 border rounded-lg shadow-sm bg-white">
      <h2 className="text-xl font-bold mb-4 text-black">{ticker} Market Data</h2>
      {loading && <p className="text-gray-500">Loading historical data...</p>}
      {error && <p className="text-red-500 font-medium">Error: {error}</p>}
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}