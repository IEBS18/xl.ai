import React from "react"
import { SAMPLE_QUESTIONS } from "../utils/constants"

const SampleQuestions = ({ onSelectQuestion }) => {
  return (
    <div className="px-4 py-3 bg-gray-900 border-t border-gray-800">
      <div className="max-w-4xl mx-auto">
        <p className="text-xs font-semibold text-gray-300 mb-2">Try these sample questions:</p>
        <div className="flex flex-wrap gap-2">
          {SAMPLE_QUESTIONS.slice(0, 4).map((question, index) => (
            <button
              key={index}
              onClick={() => onSelectQuestion(question)}
              className="text-xs bg-gray-800 text-gray-300 px-3 py-2 rounded-full hover:bg-gray-700 transition-colors border border-gray-700 shadow-sm hover:shadow-md"
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

export default SampleQuestions