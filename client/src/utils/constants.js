export const BACKEND_URL = import.meta.env.VITE_API_BASE_URL || '';

export const SAMPLE_QUESTIONS = [
  "Add trend indicators to the data",
  "Calculate performance scores for each category",
  "Forecast next 12 months of sales",
  "Create risk categories based on volatility",
  "Generate comprehensive report on revenue trends",
  "Clean and standardize the data",
  "Analyze seasonal patterns in the data",
  "Identify top performing segments",
]

export const CONNECTORS = [
  { name: "Google Sheets", icon: "📊" },
  { name: "Excel Online", icon: "📈" },
  { name: "Airtable", icon: "🗃️" },
  { name: "Notion", icon: "📝" },
  { name: "MySQL", icon: "🗄️" },
  { name: "PostgreSQL", icon: "🐘" },
  { name: "MongoDB", icon: "🍃" },
  { name: "Salesforce", icon: "☁️" },
  { name: "HubSpot", icon: "🎯" },
  { name: "Zapier", icon: "⚡" },
  { name: "CSV/Excel", icon: "📄" },
  { name: "API", icon: "🔌" },
]

export const FILE_UPLOAD_CONFIG = {
  validTypes: [".csv", ".xlsx", ".xls"],
  maxSize: 128 * 1024 * 1024, // 50MB
  acceptedFormats: ".csv,.xlsx,.xls"
}

export const MESSAGE_TYPES = {
  USER: "user",
  SYSTEM: "system",
  STATUS: "status",
  CODE: "code",
  DATAFRAME: "dataframe",
  IMAGE: "image",
  REPORT: "report",
  SUCCESS: "success",
  ERROR: "error",
  OUTPUT: "output"
}

export const COLLAPSIBLE_MESSAGE_TYPES = ["code", "status", "dataframe"]