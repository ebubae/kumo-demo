"use client";
import { useState, useRef } from "react";
import Image from "next/image";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const chartOptions = {
  responsive: true,
  plugins: {
    legend: { display: false },
    title: { display: false },
  },
  scales: {
    x: { title: { display: true, text: "Month" } },
    y: {
      title: { display: true, text: "Sales (Thousands $)" },
      min: 0,
      // max: 6.7,
      ticks: {
        callback: function (tickValue: string | number) {
          // Chart.js expects tickValue to be string | number
          const num =
            typeof tickValue === "number" ? tickValue : parseFloat(tickValue);
          return num.toFixed(1);
        },
      },
    },
  },
};

export default function Home() {
  const [query, setQuery] = useState("");
  const [product, setProduct] = useState<any>(null);
  const [productError, setProductError] = useState<string | null>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [productLoading, setProductLoading] = useState(false);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);
  const evtSourceRef = useRef<EventSource | null>(null);

  function abbreviateNumber(num: number) {
    if (Math.abs(num) >= 1e6) return (num / 1e6).toFixed(1) + "M";
    if (Math.abs(num) >= 1e3) return (num / 1e3).toFixed(1) + "K";
    return num.toString();
  }

  const handleSearch = () => {
    if (!query) return;
    setProductLoading(true);
    setAnalyticsLoading(false);
    setProduct(null);
    setProductError(null);
    setAnalytics(null);
    if (evtSourceRef.current) {
      evtSourceRef.current.close();
    }
    const evtSource = new EventSource(
      `/api/analytics?query=${encodeURIComponent(query)}`
    );
    evtSourceRef.current = evtSource;
    let gotProduct = false;
    evtSource.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }
      if (!gotProduct) {
        // Expecting product chunk: { product_id, product_name, image_url }
        if (data.error) {
          setProductError(data.error);
          setProductLoading(false);
          setAnalyticsLoading(false);
          evtSource.close();
          return;
        } else if (data.product_id && data.product_name) {
          setProduct(data);
          setProductLoading(false);
          setAnalyticsLoading(true);
          gotProduct = true;
        }
      } else {
        setAnalytics(data);
        setAnalyticsLoading(false);
        evtSource.close();
      }
    };
    evtSource.onerror = () => {
      setProductError("Failed to fetch analytics.");
      setProductLoading(false);
      setAnalyticsLoading(false);
      evtSource.close();
    };
  };

  return (
    <div className="font-sans min-h-screen bg-gray-50 dark:bg-black flex flex-col items-center p-6 sm:p-12">
      <h1 className="text-3xl sm:text-4xl font-bold mb-8 mt-8 text-center">
        Kumo for ShopSight
      </h1>
      <div className="w-full max-w-xl mb-10">
        <input
          type="text"
          placeholder="Search for a product..."
          className="w-full px-5 py-3 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 text-lg bg-white dark:bg-gray-900 dark:text-white"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSearch();
          }}
        />
      </div>
      {productLoading && (
        <div className="flex flex-col items-center justify-center w-full max-w-3xl min-h-[120px] animate-fade-in">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-4"></div>
          <span className="text-lg text-gray-700 dark:text-gray-200 animate-pulse">
            Finding product...
          </span>
        </div>
      )}
      {(productError || product) && (
        <div className="w-full max-w-3xl flex flex-col gap-8 animate-fade-in">
          {/* Product Card */}
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow p-6 flex items-center gap-6">
            {product && product.image_url && (
              <div className="flex-shrink-0">
                <Image
                  src={product.image_url}
                  alt={product.product_name}
                  width={96}
                  height={96}
                  className="rounded-lg border object-cover"
                />
              </div>
            )}
            <div className="flex flex-col justify-center">
              <h2 className="text-xl font-semibold mb-2">Product</h2>
              {productError ? (
                <p className="text-lg text-red-600">{productError}</p>
              ) : product ? (
                <>
                  <p className="text-2xl font-bold mb-1">
                    {product.product_name}
                  </p>
                  <p className="text-gray-500 text-base">
                    ID: {product.product_id}
                  </p>
                </>
              ) : null}
            </div>
          </div>
          {/* Analytics Cards */}
          {product && analytics && (
            <div className="grid grid-cols-1 gap-8">
              {/* Sales Trends Card */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow p-6">
                <h2 className="text-xl font-semibold mb-4">
                  Past Sales Trends
                </h2>
                <div className="h-64 flex items-center justify-center">
                  <Line
                    data={{
                      labels: (() => {
                        // Generate month labels from Aug 2018 to Oct 2020
                        const start = new Date(2018, 7); // August 2018
                        const end = new Date(2020, 9); // October 2020
                        const labels = [];
                        let d = new Date(start);
                        while (d <= end) {
                          labels.push(
                            d.toLocaleString("default", { month: "short" }) +
                              " " +
                              d.getFullYear()
                          );
                          d.setMonth(d.getMonth() + 1);
                        }
                        return labels;
                      })(),
                      datasets: [
                        {
                          label: "Sales",
                          data: analytics.sales_trends,
                          borderColor: "#2563eb",
                          backgroundColor: "rgba(37,99,235,0.1)",
                          tension: 0.4,
                          fill: true,
                        },
                      ],
                    }}
                    options={chartOptions}
                  />
                </div>
              </div>
              {/* Forecasted Demand Card */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow p-6 flex flex-col items-start">
                <h2 className="text-xl font-semibold mb-2">
                  Forecasted Demand
                </h2>
                <span
                  className={`text-4xl font-bold mb-1 ${
                    analytics.forecasted_demand > 0
                      ? "text-green-600"
                      : "text-red-600"
                  }`}
                >
                  {analytics.forecasted_demand > 0 ? "+" : ""}
                  {abbreviateNumber(analytics.forecasted_demand)}
                </span>
                <span className="text-gray-600 dark:text-gray-300 text-base">
                  {analytics.forecast_text}
                </span>
              </div>
              {/* Customer Segments Card */}
              <div className="bg-white dark:bg-gray-900 rounded-xl shadow p-6">
                <h2 className="text-xl font-semibold mb-4">
                  Likely Customer Segments
                </h2>
                <ul className="space-y-4">
                  {analytics.customer_segments.map((seg: any, idx: number) => (
                    <li
                      key={seg.segment_name || idx}
                      className="flex flex-col gap-1 p-3 rounded-lg border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-950"
                    >
                      <span className="font-semibold text-lg text-blue-700 dark:text-blue-300">
                        {seg.segment_name}
                      </span>
                      <span className="text-gray-700 dark:text-gray-300 text-base">
                        <strong>Reasoning:</strong> {seg.reasoning}
                      </span>
                      <span className="text-gray-700 dark:text-gray-300 text-base">
                        <strong>Marketing Strategy:</strong>{" "}
                        {seg.marketing_strategy}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </div>
      )}
      <style jsx global>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
        .animate-spin {
          animation: spin 1s linear infinite;
        }
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(16px);
          }
          to {
            opacity: 1;
            transform: none;
          }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease;
        }
      `}</style>
    </div>
  );
}
