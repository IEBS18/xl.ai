import React, { useState } from "react"
import { Copy, Check } from "lucide-react"
import { useTheme } from "../context/ThemeProvider"

const CodeBlock = ({ code, language = "python" }) => {
  const [copied, setCopied] = useState(false)
  const { themeClasses, isDark } = useTheme()

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  // Enhanced syntax highlighting for Python
  const highlightPython = (code) => {
    // Split by lines first to handle multi-line properly
    const lines = code.split('\n')
    
    return lines.map(line => {
      // Escape HTML entities first
      let highlightedLine = line
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')

      // Apply syntax highlighting
      highlightedLine = highlightedLine
        // Keywords
        .replace(/\b(import|from|as|def|class|if|elif|else|for|while|try|except|finally|with|return|yield|break|continue|pass|lambda|global|nonlocal|assert|del|raise|async|await)\b/g, 
          '<span class="text-purple-400 font-medium">$1</span>')
        
        // Built-in constants
        .replace(/\b(True|False|None|self|cls)\b/g, 
          '<span class="text-red-400 font-medium">$1</span>')
        
        // Common variables and modules
        .replace(/\b(pd|np|plt|sm|df|historical_df|t)\b/g, 
          '<span class="text-blue-400">$1</span>')
        
        // Strings (handle both single and double quotes)
        .replace(/(&#39;)(.*?)(&#39;)/g, 
          '<span class="text-green-400">$1$2$3</span>')
        .replace(/(&quot;)(.*?)(&quot;)/g, 
          '<span class="text-green-400">$1$2$3</span>')
        
        // Comments
        .replace(/(#.*$)/g, 
          '<span class="text-gray-500 italic">$1</span>')
        
        // Numbers
        .replace(/\b(\d+\.?\d*)\b/g, 
          '<span class="text-orange-400">$1</span>')
        
        // Operators
        .replace(/(\+|-|\*|\/|=|==|!=|&lt;=|&gt;=|&lt;|&gt;|\band\b|\bor\b|\bnot\b|\bin\b|\bis\b)/g, 
          '<span class="text-pink-400">$1</span>')
        
        // Brackets and parentheses
        .replace(/(\(|\)|\[|\]|\{|\})/g, 
          '<span class="text-yellow-400">$1</span>')

      return highlightedLine
    })
  }

  const lines = code.split('\n')
  const highlightedLines = highlightPython(code)

  return (
    <div className="bg-gray-900 rounded-lg border border-gray-700 overflow-hidden">
      {/* IDE-like header */}
      <div className="bg-gray-800 border-b border-gray-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
          </div>
          <span className="text-gray-300 text-sm font-medium ml-2">
            analysis.{language}
          </span>
        </div>
        <button
          onClick={copyToClipboard}
          className="flex items-center space-x-1 text-gray-400 hover:text-white p-1 rounded hover:bg-gray-700 transition-colors"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check size={14} />
              <span className="text-xs">Copied!</span>
            </>
          ) : (
            <>
              <Copy size={14} />
              <span className="text-xs">Copy</span>
            </>
          )}
        </button>
      </div>

      {/* Code content */}
      <div className="relative">
        <div className="flex">
          {/* Line numbers */}
          <div className="bg-gray-850 border-r border-gray-700 px-3 py-4 text-right select-none">
            {lines.map((_, index) => (
              <div
                key={index}
                className="text-gray-500 text-sm font-mono leading-6 min-h-[1.5rem]"
              >
                {index + 1}
              </div>
            ))}
          </div>

          {/* Code */}
          <div className="flex-1 overflow-x-auto">
            <div className="p-4">
              {highlightedLines.map((line, index) => (
                <div
                  key={index}
                  className="text-sm font-mono leading-6 min-h-[1.5rem] hover:bg-gray-800/50 transition-colors rounded px-2 -mx-2"
                  dangerouslySetInnerHTML={{ __html: line || '&nbsp;' }}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CodeBlock