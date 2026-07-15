// Interface demonstration only. Replace with real API data in later phases.
export const kpis = [
  {
    label: "Forecast Revenue",
    value: "$428.6K",
    detail: "Demo 30-day horizon",
  },
  { label: "Expected ROAS", value: "4.32×", detail: "Interface preview" },
  { label: "Target Achievement", value: "76%", detail: "Demo probability" },
  { label: "Forecast Confidence", value: "High", detail: "Demo indicator" },
];
export const forecastData = [
  { period: "W1", historical: 72, forecast: null, low: null, high: null },
  { period: "W2", historical: 78, forecast: null, low: null, high: null },
  { period: "W3", historical: 75, forecast: null, low: null, high: null },
  { period: "W4", historical: 86, forecast: 86, low: 86, high: 86 },
  { period: "W5", historical: null, forecast: 91, low: 82, high: 101 },
  { period: "W6", historical: null, forecast: 98, low: 86, high: 111 },
  { period: "W7", historical: null, forecast: 104, low: 89, high: 120 },
];
export const channels = [
  {
    name: "Google Ads",
    spend: "$38.2K",
    revenue: "$171.8K",
    roas: "4.50×",
    status: "On track",
  },
  {
    name: "Meta Ads",
    spend: "$31.4K",
    revenue: "$125.6K",
    roas: "4.00×",
    status: "Monitor",
  },
  {
    name: "Email",
    spend: "$8.9K",
    revenue: "$61.4K",
    roas: "6.90×",
    status: "On track",
  },
  {
    name: "Organic",
    spend: "$12.1K",
    revenue: "$69.8K",
    roas: "5.77×",
    status: "On track",
  },
];
export const phases = [
  "Foundation",
  "Data Intelligence",
  "Forecasting",
  "Trust and Uncertainty",
  "Causal Intelligence",
  "Scenario Simulation",
  "Optimization",
  "RAG and Agents",
];
