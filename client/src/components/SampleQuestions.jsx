import React from "react"
import { Sparkles, ArrowRight } from "lucide-react"
import { SAMPLE_QUESTIONS } from "../utils/constants"
import { useTheme } from "@/context/ThemeProvider"
const SampleQuestions = ({ onSelectQuestion }) => {
  const { themeClasses } = useTheme()

  // Fallback questions if SAMPLE_QUESTIONS is not available
  const defaultQuestions = [
    "What is the average of sales?",
    "Show me a chart of revenue by month",
    "Generate a summary report",
    "Find the maximum value in price column",
    "Create a correlation analysis",
    "What are the top 10 customers by revenue?"
  ]

  const questions = SAMPLE_QUESTIONS || defaultQuestions

  return (
    <div className={`px-4 py-2 ${themeClasses.bg} ${themeClasses.border} border-t transition-colors`}>
      <div className="max-w-4xl mx-auto">
        <div className={`${themeClasses.glass} rounded-2xl p-2 shadow-sm`}>
          <div className="flex items-center space-x-2 mb-3">
            <div className={`p-1.5 ${themeClasses.surface} rounded-lg`}>
              <Sparkles size={14} className={themeClasses.textSecondary} />
            </div>
            <p className={`text-sm font-medium ${themeClasses.text}`}>
              Try these sample questions:
            </p>
          </div>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {questions.slice(0, 6).map((question, index) => (
              <button
                key={index}
                onClick={() => onSelectQuestion(question)}
                className={`group flex items-center justify-between text-xs ${themeClasses.surface} ${themeClasses.text} px-3 py-2.5 rounded-xl hover:${themeClasses.surfaceSecondary} transition-all duration-200 ${themeClasses.border} border shadow-sm hover:shadow-md hover:scale-[1.02] text-left`}
              >
                <span className="flex-1 line-clamp-2">{question}</span>
                <ArrowRight 
                  size={12} 
                  className={`${themeClasses.textSecondary} group-hover:${themeClasses.text} transition-colors ml-2 flex-shrink-0`} 
                />
              </button>
            ))}
          </div>
          
          <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <p className={`text-xs ${themeClasses.textMuted} text-center`}>
              Click any question to get started, or type your own analysis request
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SampleQuestions