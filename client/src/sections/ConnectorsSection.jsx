import React from "react"
import { motion } from "framer-motion"
import { useTheme } from "../context/ThemeProvider"
import { CONNECTORS } from "../utils/constants"

const ConnectorsSection = () => {
  const { themeClasses } = useTheme()

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 1.0 }}
      className="text-center mt-20"
    >
      <p className={`text-xs ${themeClasses.textMuted} uppercase tracking-widest mb-12 font-medium`}>
        CONNECTS WITH YOUR FAVORITE TOOLS
      </p>

      <div className="grid grid-cols-3 md:grid-cols-6 lg:grid-cols-12 gap-4 max-w-6xl mx-auto">
        {CONNECTORS.map((connector, index) => (
          <motion.div
            key={connector.name}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{
              duration: 0.4,
              delay: index * 0.03,
              type: "spring",
              stiffness: 200,
            }}
            className={`p-4 rounded-xl text-center hover:scale-105 transition-all duration-300 cursor-pointer border ${themeClasses.border} ${themeClasses.glass}`}
            whileHover={{ y: -2 }}
          >
            <div className="text-2xl mb-2">{connector.icon}</div>
            <div className={`text-xs font-medium ${themeClasses.textMuted}`}>{connector.name}</div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  )
}

export default ConnectorsSection