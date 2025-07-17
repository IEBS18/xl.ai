import React from "react"
import { motion } from "framer-motion"
import { useTheme } from "../context/ThemeProvider"

const IntegrationsSection = () => {
  const { isDark, themeClasses } = useTheme()

  const integrations = [
    { name: "Gmail" },
    { name: "Salesforce" },
    { name: "Docs" },
    { name: "Slack" },
    { name: "Excel" },
    { name: "PowerPoint" },
  ]

  return (
    <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
          >
            <h2 className={`text-4xl md:text-5xl font-bold ${themeClasses.text} mb-8 tracking-tight`}>
              Integrations
            </h2>

            <p className={`text-lg ${themeClasses.textSecondary} mb-10 leading-relaxed`}>
              300+ integrations so you can research, analyze, and create without switching between platforms.
            </p>

            <p className={`${themeClasses.text} mb-8 font-medium`}>InsiPredict integrates with:</p>

            <div className="flex flex-wrap gap-3 mb-10">
              {integrations.map((integration, index) => (
                <motion.span
                  key={integration.name}
                  className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.border} ${themeClasses.textSecondary} hover:${themeClasses.text} cursor-pointer hover:scale-105 transition-all duration-300`}
                  initial={{ opacity: 0, scale: 0.8 }}
                  whileInView={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  whileHover={{ y: -2 }}
                >
                  {integration.name}
                </motion.span>
              ))}
            </div>

            <p className={`${themeClasses.textMuted} text-sm`}>+ many more</p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="relative"
          >
            <div className="grid grid-cols-3 gap-8 items-center">
              {[
                [{ delay: 0 }, { delay: 0.1 }],
                [{ delay: 0.2 }, { delay: 0.3 }, { delay: 0.4 }],
                [{ delay: 0.5 }, { delay: 0.6 }],
              ].map((column, colIndex) => (
                <div key={colIndex} className="space-y-8">
                  {column.map((item, itemIndex) => (
                    <motion.div
                      key={itemIndex}
                      className={`w-16 h-16 ${themeClasses.surfaceSecondary} rounded-2xl flex items-center justify-center shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group border ${themeClasses.border}`}
                      initial={{ opacity: 0, scale: 0, rotate: -90 }}
                      whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
                      transition={{
                        duration: 0.6,
                        delay: item.delay,
                        type: "spring",
                        stiffness: 200,
                      }}
                      viewport={{ once: true }}
                      whileHover={{ scale: 1.1, rotate: 3 }}
                    >
                      <div
                        className={`w-8 h-8 ${isDark ? "bg-white" : "bg-black"} rounded group-hover:rotate-12 transition-transform duration-300`}
                      />
                    </motion.div>
                  ))}
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}

export default IntegrationsSection