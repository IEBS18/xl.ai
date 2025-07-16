import { COLLAPSIBLE_MESSAGE_TYPES } from "./constants"

export const getTimeBasedGreeting = () => {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return "Good Morning"
  if (hour >= 12 && hour < 17) return "Good Afternoon" 
  if (hour >= 17 && hour < 22) return "Good Evening"
  return "Hi"
}

export const shouldCollapseByDefault = (type) => {
  return COLLAPSIBLE_MESSAGE_TYPES.includes(type)
}

export const copyToClipboard = (text) => {
  navigator.clipboard.writeText(text).then(() => {
    console.log("Copied to clipboard")
  })
}

export const renderMarkdown = (text) => {
  // Simple markdown renderer for basic formatting
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`(.*?)`/g, '<code class="bg-gray-800 text-green-400 px-2 py-1 rounded text-sm">$1</code>')
    .replace(/### (.*?)(\n|$)/g, '<h3 class="text-lg font-semibold mt-4 mb-2 text-white">$1</h3>')
    .replace(/## (.*?)(\n|$)/g, '<h2 class="text-xl font-semibold mt-6 mb-3 text-white">$1</h2>')
    .replace(/# (.*?)(\n|$)/g, '<h1 class="text-2xl font-bold mt-8 mb-4 text-white">$1</h1>')
    .replace(/\n\n/g, '</p><p class="mb-4">')
    .replace(/\n/g, "<br>")
}

export const getStepIcon = (type, isCompleted) => {
  // This will be used by components that import the icons
  return { type, isCompleted }
}

export const getStepColor = (type, isCompleted) => {
  if (type === "status") {
    return isCompleted ? "border-green-500 bg-green-500" : "border-blue-500 bg-blue-500"
  }

  switch (type) {
    case "success":
      return "border-green-500 bg-green-500"
    case "error":
      return "border-red-500 bg-red-500"
    case "code":
      return "border-purple-500 bg-purple-500"
    case "dataframe":
      return "border-cyan-500 bg-cyan-500"
    case "image":
      return "border-orange-500 bg-orange-500"
    case "report":
      return "border-indigo-500 bg-indigo-500"
    default:
      return "border-gray-500 bg-gray-500"
  }
}