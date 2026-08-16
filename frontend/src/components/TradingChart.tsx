"use client";

import { useEffect, useRef, useState } from "react";
import { createChart, ColorType, CandlestickSeries, LineSeries } from "lightweight-charts";

export default function TradingChart({ ticker }: { ticker: string }) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 1. Initialize the chart instance
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "#ffffff" },
        textColor: "#333",
      },
      width: chartContainerRef.current.clientWidth,
      height: 600, // Increased height to fit both charts
      timeScale: {
        timeVisible: true,
        borderColor: "#D1D5DB",
      },
    });

    // 2. Configure the Price Scale (Top 70% of the chart)
    chart.priceScale("right").applyOptions({
      scaleMargins: {
        top: 0.05,
        bottom: 0.3, // Leave the bottom 30% empty for the RSI
      },
    });

    // 3. Add the Series First
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#26a69a",
      downColor: "#ef5350",
      borderVisible: false,
      wickUpColor: "#26a69a",
      wickDownColor: "#ef5350",
    });

    const smaSeries = chart.addSeries(LineSeries, {
      color: "#2962FF",
      lineWidth: 2,
      title: "SMA 20",
    });

    const rsiSeries = chart.addSeries(LineSeries, {
      color: "#9C27B0", 
      lineWidth: 2,
      title: "RSI 14",
      priceScaleId: "rsi", // <--- Introduces "rsi" ID
    });

    // 4. THEN Configure the RSI Scale (Bottom 20% of the chart)
    chart.priceScale("rsi").applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0.05,
      },
    });

    // 5. Fetch and Map Data
    const fetchData = async () => {
      try {
        const response = await fetch(`http://127.0.0.1:8000/api/v1/features/${ticker}`);
        if (!response.ok) throw new Error("Failed to fetch data.");
        
        const json = await response.json();
        
        const candleData = json.features.map((item: any) => ({
          time: item.trade_date,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }));

        const smaData = json.features
          .filter((item: any) => item.sma_20 !== null && !isNaN(item.sma_20))
          .map((item: any) => ({
            time: item.trade_date,
            value: item.sma_20,
          }));

        const rsiData = json.features
          .filter((item: any) => item.rsi_14 !== null && !isNaN(item.rsi_14))
          .map((item: any) => ({
            time: item.trade_date,
            value: item.rsi_14,
          }));

        // Apply data
        candlestickSeries.setData(candleData);
        smaSeries.setData(smaData);
        rsiSeries.setData(rsiData);
        
        chart.timeScale().fitContent();
        setLoading(false);
      } catch (err: any) {
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();

    // 6. Handle resizing
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
      <h2 className="text-xl font-bold mb-4 text-black">{ticker} Advanced Market Data</h2>
      {loading && <p className="text-gray-500">Loading historical data and indicators...</p>}
      {error && <p className="text-red-500 font-medium">Error: {error}</p>}
      <div ref={chartContainerRef} className="w-full" />
    </div>
  );
}