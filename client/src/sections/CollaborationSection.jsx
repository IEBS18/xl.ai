import React from "react"
import { motion } from "framer-motion"
import { Users, Network, Eye, FileSpreadsheet, MessageSquare } from "lucide-react"
import { useTheme } from "../context/ThemeProvider"

const CollaborationSection = () => {
  const { isDark, themeClasses } = useTheme()

  const features = [
    {
      title: "Smart collaboration",
      description:
        "Built-in editors for spreadsheets, presentations and documents that run many iterations across multitudes of drafts",
      icon: Users,
    },
    {
      title: "Uses your tools like you do",
      description:
        "InsiPredict integrates with any spreadsheet, database, doc, chat, ticket, and data source that you have. From Slack to Salesforce.",
      icon: Network,
    },
    {
      title: "Shows its thinking",
      description:
        "Deep research capabilities that lead to all deliverables being grounded in data and tailored for your use case",
      icon: Eye,
    },
  ]

  return (
    <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <h2 className={`text-4xl md:text-6xl font-bold ${themeClasses.text} mb-4 leading-tight tracking-tight`}>
            One workspace to
            <br />
            move faster, together
          </h2>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Performance Report Mockup - Updated with gradient background */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="p-8 rounded-3xl"
            style={{
              background: 'linear-gradient(232.59deg, #011D89 22.28%, #00092B 92.41%)'
            }}
          >
            <motion.div
              className="bg-white p-8 rounded-2xl shadow-2xl"
              whileHover={{ scale: 1.01 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-semibold text-gray-900">Performance Report</h3>
                <span className="text-sm text-gray-500">Q2 2025</span>
              </div>

              <div className="space-y-8">
                <div>
                  <h4 className="font-medium mb-3 text-gray-900">Summary</h4>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    Performance metrics show significant improvement across key indicators with notable
                    enhancement in operational efficiency and customer satisfaction.
                  </p>
                </div>

                <div>
                  <h4 className="font-medium mb-6 text-gray-900">Monthly Active Users</h4>
                  <div className="flex items-end space-x-2 h-32">
                    {[...Array(12)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="rounded-sm flex-1"
                        style={{ 
                          height: `${Math.random() * 80 + 20}%`,
                          background: 'linear-gradient(90deg, #04165D 0%, #000723 100%)'
                        }}
                        initial={{ height: 0 }}
                        whileInView={{ height: `${Math.random() * 80 + 20}%` }}
                        transition={{ duration: 1, delay: i * 0.1 }}
                        viewport={{ once: true }}
                      />
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </motion.div>

          {/* Chat Interface Mockup - Updated with gradient background */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className={`${isDark ? "bg-gray-900" : "bg-gray-100"} p-8 rounded-3xl border ${themeClasses.border}`}
          >
            <div className="flex items-center space-x-3 mb-8">
              <div
                className={`w-10 h-10 ${isDark ? "bg-gray-800" : "bg-gray-200"} rounded-lg flex items-center justify-center`}
              >
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <div className={`font-medium ${themeClasses.text}`}>InsiPredict</div>
                <div className={`text-sm ${themeClasses.textMuted}`}>Market-team</div>
              </div>
            </div>

            <div className="space-y-6 mb-8">
              <motion.div
                className="flex items-start space-x-3"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.2 }}
                viewport={{ once: true }}
              >
                <div
                  className={`w-8 h-8 ${isDark ? "bg-gray-700" : "bg-gray-300"} rounded-full flex-shrink-0`}
                ></div>
                <div>
                  <div className={`font-medium text-sm ${themeClasses.text}`}>Tony</div>
                  <div className={`text-sm ${themeClasses.textSecondary}`}>
                    How's the progress on the report team?
                  </div>
                </div>
              </motion.div>

              <motion.div
                className="flex items-start space-x-3"
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.4 }}
                viewport={{ once: true }}
              >
                <div
                  className={`w-8 h-8 ${isDark ? "bg-gray-700" : "bg-gray-300"} rounded-full flex-shrink-0`}
                ></div>
                <div>
                  <div className={`font-medium text-sm ${themeClasses.text}`}>David</div>
                  <div className={`text-sm ${themeClasses.textSecondary}`}>
                    Just gave the task to InsiPredict, should have it soon
                  </div>
                </div>
              </motion.div>
            </div>

            <motion.div
              className={`${isDark ? "bg-gray-800" : "bg-gray-200"} rounded-xl p-6 border ${themeClasses.border}`}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.6 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.01 }}
            >
              <div className={`flex items-center space-x-2 text-sm ${themeClasses.textSecondary} mb-2`}>
                <FileSpreadsheet className="w-4 h-4" />
                <span>Q2_Performance_Report.xlsx</span>
              </div>
              <div className={`text-xs ${themeClasses.textMuted}`}>Generated by InsiPredict • 2 min ago</div>
            </motion.div>
          </motion.div>
        </div>

        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              viewport={{ once: true }}
              className={`text-center p-8 rounded-2xl border ${themeClasses.border} hover:scale-105 transition-all duration-300 group cursor-pointer`}
              whileHover={{ y: -5 }}
            >
              <motion.div
                className="w-12 h-12 rounded-xl flex items-center justify-center mb-6 mx-auto text-white"
                style={{
                  background: 'linear-gradient(232.59deg, #011D89 22.28%, #00092B 92.41%)'
                }}
                whileHover={{ scale: 1.1 }}
              >
                <feature.icon className="w-6 h-6" />
              </motion.div>
              <h3 className={`text-xl font-semibold mb-4 ${themeClasses.text}`}>{feature.title}</h3>
              <p className={`${themeClasses.textSecondary} leading-relaxed`}>{feature.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}

export default CollaborationSection