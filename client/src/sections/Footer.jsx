import React from "react"
import { motion } from "framer-motion"
import { useTheme } from "../context/ThemeProvider"

const Footer = () => {
  const { isDark, themeClasses } = useTheme()

  const companyLinks = ["Home", "Blog", "Careers", "Brand Kit", "Affiliate"]
  const legalLinks = ["Security", "Privacy", "Terms of use"]

  return (
    <footer className={`${themeClasses.bg} py-20 border-t ${themeClasses.border} relative overflow-hidden`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="col-span-1 md:col-span-2">
            <motion.div
              className="flex items-center space-x-3 mb-8"
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 400 }}
            >
              <div className="flex items-center space-x-1">
                <image src='../../public/logo.svg' className="w-5 h-5" />
              </div>
            </motion.div>
            <p className={`${themeClasses.textSecondary} mb-8 max-w-md leading-relaxed text-lg`}>
              Work smarter, faster, and more efficiently with InsiPredict.
            </p>
            <div className="flex items-center space-x-6">
              <span className={`${themeClasses.textMuted} text-sm uppercase tracking-wider`}>Socials</span>
              <div className="flex space-x-4">
                {[0, 1].map((i) => (
                  <motion.div
                    key={i}
                    className={`w-10 h-10 ${themeClasses.surfaceSecondary} rounded-lg flex items-center justify-center cursor-pointer border ${themeClasses.border} hover:scale-110 transition-all duration-300`}
                    whileHover={{ y: -2 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <div className={`w-4 h-4 ${themeClasses.textMuted}`}></div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-6 ${themeClasses.text}`}>Company</h3>
            <ul className="space-y-4">
              {companyLinks.map((item, index) => (
                <motion.li
                  key={item}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <a
                    href="#"
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
                  >
                    {item}
                  </a>
                </motion.li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-6 ${themeClasses.text}`}>Legal</h3>
            <ul className="space-y-4">
              {legalLinks.map((item, index) => (
                <motion.li
                  key={item}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                  viewport={{ once: true }}
                >
                  <a
                    href="#"
                    className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
                  >
                    {item}
                  </a>
                </motion.li>
              ))}
            </ul>
          </div>
        </div>

        <motion.div
          className={`border-t ${themeClasses.border} mt-16 pt-8`}
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
        >
          <p className={`${themeClasses.textMuted} text-sm`}>© 2025 InsiPredict. All rights reserved.</p>
        </motion.div>
      </div>
    </footer>
  )
}

export default Footer