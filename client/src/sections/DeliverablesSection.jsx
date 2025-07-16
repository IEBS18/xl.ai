import React, { useRef } from "react"
import { motion } from "framer-motion"
import { FileSpreadsheet, Presentation, FileText } from "lucide-react"
import { useTheme } from "../context/ThemeProvider"
import ParticleBackground from "../components/ParticleBackground"

const DeliverablesSection = () => {
  const { themeClasses } = useTheme()
  const particlesRef = useRef(null)

  return (
    <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
      {/* Particles Background */}
      <ParticleBackground ref={particlesRef} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <h2 className={`text-4xl md:text-6xl font-bold ${themeClasses.text} mb-4 leading-tight tracking-tight`}>
            Your deliverables,
            <br />
            powered by AI
          </h2>
        </motion.div>

        {/* AI Spreadsheets Feature */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-24">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <div className="flex items-center space-x-2 mb-6">
              <FileSpreadsheet className="w-5 h-5" />
              <span className="font-medium text-sm uppercase tracking-wider">AI Spreadsheets</span>
            </div>

            <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
              Insight-ready spreadsheets
            </h3>

            <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
              No broken formulas. No manual cleanup. DataScope AI helps you catch issues and surface insights in
              real time.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className={`${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
          >
            <motion.div
              className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl border ${themeClasses.border}`}
              whileHover={{ scale: 1.01 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <div className="flex items-center space-x-2 mb-6">
                <div className="flex space-x-1">
                  {["⟲", "↶", "↷", "$", "%", "⚡", "⌘", "✓", "⋮"].map((symbol, i) => (
                    <motion.div
                      key={i}
                      className={`w-8 h-8 ${themeClasses.surfaceSecondary} rounded flex items-center justify-center text-xs border ${themeClasses.border}`}
                      whileHover={{ scale: 1.1 }}
                      transition={{ type: "spring", stiffness: 400 }}
                    >
                      {symbol}
                    </motion.div>
                  ))}
                </div>
              </div>

              <div className={`text-sm ${themeClasses.textMuted} mb-6 font-mono`}>
                ∑ FORECAST (1, B2:B5, A2:A5)
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className={`border-b ${themeClasses.border}`}>
                      <th className={`text-left p-3 ${themeClasses.surfaceSecondary} rounded-tl`}>A</th>
                      <th className={`text-left p-3 ${themeClasses.text}`}>B</th>
                      <th className={`text-left p-3 ${themeClasses.surfaceSecondary}`}>C</th>
                      <th className={`text-left p-3 ${themeClasses.text}`}>D</th>
                      <th className={`text-left p-3 ${themeClasses.text} rounded-tr`}>E</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ["1", "Month", "Units Sold", "Revenue ($)", "COGS ($)"],
                      ["2", "Apr 2025", "5,083", "609,960", "355,810"],
                      ["3", "May 2025", "4,925", "591,000", "344,750"],
                      ["4", "Jun 2025", "4,741", "568,920", "331,870"],
                      ["5", "Jul 2025", "4,995", "599,400", "349,650"],
                    ].map((row, i) => (
                      <motion.tr
                        key={i}
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.3, delay: i * 0.1 }}
                        viewport={{ once: true }}
                        className={`border-b ${themeClasses.border} hover:${themeClasses.surfaceSecondary} transition-colors`}
                      >
                        {row.map((cell, j) => (
                          <td
                            key={j}
                            className={`p-3 ${i === 0 && (j === 0 || j === 2) ? themeClasses.surfaceSecondary : themeClasses.text}`}
                          >
                            {cell}
                          </td>
                        ))}
                      </motion.tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          </motion.div>
        </div>

        {/* AI Presentations Feature */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center mb-24">
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className={`order-2 lg:order-1 ${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
          >
            <motion.div
              className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl border ${themeClasses.border}`}
              whileHover={{ scale: 1.01 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h4 className={`font-semibold text-lg ${themeClasses.text}`}>Sales Report</h4>
                  <span className={`text-sm ${themeClasses.textMuted}`}>2024 Sales Progression</span>
                </div>

                <div className={`border-b ${themeClasses.border} pb-4`}>
                  <div className="flex items-center space-x-2">
                    <span className={`text-sm ${themeClasses.textSecondary}`}>FINANCIALS</span>
                    <div className={`${themeClasses.button} px-2 py-1 rounded text-xs`}>DataScope AI</div>
                  </div>
                </div>

                <div className={`${themeClasses.surfaceSecondary} p-4 rounded-xl border ${themeClasses.border}`}>
                  <p className={`text-sm ${themeClasses.textSecondary}`}>
                    Every insight, a step toward exponential growth.
                    <span className={`${themeClasses.button} px-1 rounded text-xs ml-1`}>DataScope AI</span> turns
                    intelligence into ROI.
                  </p>
                </div>
              </div>
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="order-1 lg:order-2"
          >
            <div className="flex items-center space-x-2 mb-6">
              <Presentation className="w-5 h-5" />
              <span className="font-medium text-sm uppercase tracking-wider">AI Presentations</span>
            </div>

            <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
              Polished, client-ready presentations
            </h3>

            <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
              Slides made easy. Any data, any topic, any input. DataScope AI turns it into a polished story fast.
            </p>
          </motion.div>
        </div>

        {/* AI Documents Feature */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <div className="flex items-center space-x-2 mb-6">
              <FileText className="w-5 h-5" />
              <span className="font-medium text-sm uppercase tracking-wider">AI Documents</span>
            </div>

            <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
              Documents, ready for hand off
            </h3>

            <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
              DataScope AI formats, edits, and checks your docs so that you don't have to.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className={`${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
          >
            <motion.div
              className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl transform rotate-2 hover:rotate-0 transition-all duration-500 border ${themeClasses.border}`}
              whileHover={{ scale: 1.02, rotate: 0 }}
            >
              <h4 className={`font-bold text-lg mb-6 ${themeClasses.text}`}>
                Top 5 Enterprise AI Startups to Watch in 2025
              </h4>

              <div className="space-y-4 text-sm">
                {[
                  { label: "Comprehensive Analysis" },
                  { label: "Market Trends" },
                  { label: "Investment Insights" },
                ].map((item, i) => (
                  <motion.div
                    key={item.label}
                    className="flex items-center space-x-3"
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <div className={`w-2 h-2 ${themeClasses.text === "text-white" ? "bg-white" : "bg-black"} rounded`}></div>
                    <span className={themeClasses.textSecondary}>{item.label}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            <motion.div
              className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl transform -rotate-1 hover:rotate-0 transition-all duration-500 mt-4 border ${themeClasses.border}`}
              whileHover={{ scale: 1.02, rotate: 0 }}
            >
              <h4 className={`font-bold text-lg mb-3 ${themeClasses.text}`}>
                Marketing Budget Proposal — Q2 2025
              </h4>
              <p className={`text-sm ${themeClasses.textSecondary}`}>
                Strategic rationale for budget allocation across digital channels...
              </p>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

export default DeliverablesSection