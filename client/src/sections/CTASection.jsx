import React from "react"
import { motion } from "framer-motion"
import { useTheme } from "../context/ThemeProvider"

const CTASection = () => {
  const { themeClasses } = useTheme()

  return (
    <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <h2 className={`text-4xl md:text-5xl font-bold ${themeClasses.text} mb-6 tracking-tight`}>
            Endless use cases
          </h2>
          <p className={`text-lg ${themeClasses.textSecondary} mb-12 max-w-2xl mx-auto leading-relaxed`}>
            DataScope AI has 1000+ use cases for any corporate role, helping you and your team take care of
            serious work
          </p>

          <motion.button
            className={`${themeClasses.button} px-12 py-4 rounded-xl font-semibold transition-all duration-300 text-lg`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            Sign up
          </motion.button>
        </motion.div>
      </div>
    </section>
  )
}

export default CTASection