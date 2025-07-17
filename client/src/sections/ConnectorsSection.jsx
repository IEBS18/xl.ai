// import React from "react"
// import { motion } from "framer-motion"
// import { useTheme } from "../context/ThemeProvider"
// import { CONNECTORS } from "../utils/constants"

// const ConnectorsSection = () => {
//   const { themeClasses } = useTheme()

//   return (
//     <motion.div
//       initial={{ opacity: 0, y: 20 }}
//       animate={{ opacity: 1, y: 0 }}
//       transition={{ duration: 0.8, delay: 1.0 }}
//       className="text-center mt-20"
//     >
//       <p className={`text-xs ${themeClasses.textMuted} uppercase tracking-widest mb-12 font-medium`}>
//         CONNECTS WITH YOUR FAVORITE TOOLS
//       </p>

//       <div className="grid grid-cols-3 md:grid-cols-6 lg:grid-cols-12 gap-4 max-w-6xl mx-auto">
//         {CONNECTORS.map((connector, index) => (
//           <motion.div
//             key={connector.name}
//             initial={{ opacity: 0, scale: 0.8 }}
//             animate={{ opacity: 1, scale: 1 }}
//             transition={{
//               duration: 0.4,
//               delay: index * 0.03,
//               type: "spring",
//               stiffness: 200,
//             }}
//             className={`p-4 rounded-xl text-center hover:scale-105 transition-all duration-300 cursor-pointer border ${themeClasses.border} ${themeClasses.glass}`}
//             whileHover={{ y: -2 }}
//           >
//             <div className="text-2xl mb-2">{connector.icon}</div>
//             <div className={`text-xs font-medium ${themeClasses.textMuted}`}>{connector.name}</div>
//           </motion.div>
//         ))}
//       </div>
//     </motion.div>
//   )
// }

// export default ConnectorsSection


import React, { useMemo, useEffect, useRef, useState } from "react"
import { motion, useAnimationControls } from "framer-motion"
import { useTheme } from "../context/ThemeProvider"
import { CONNECTORS } from "../utils/constants"

const ConnectorsSection = () => {
  const { isDark } = useTheme()
  const controls = useAnimationControls()
  const [isHovered, setIsHovered] = useState(false)
  const [containerWidth, setContainerWidth] = useState(0)
  const containerRef = useRef(null)

  // Memoized theme styles consistent with your app
  const themeStyles = useMemo(() => ({
    textMuted: isDark ? "text-gray-400" : "text-gray-500",
    text: isDark ? "text-white" : "text-gray-900",
    textSecondary: isDark ? "text-gray-300" : "text-gray-600",
    border: isDark ? "border-gray-800/50" : "border-gray-200/50",
    glass: isDark 
      ? "bg-gray-900/80 backdrop-blur-md" 
      : "bg-white/80 backdrop-blur-md",
    hover: isDark 
      ? "hover:bg-gray-800/50" 
      : "hover:bg-gray-100/50",
    gradient: isDark 
      ? "from-purple-500/10 to-blue-500/10" 
      : "from-purple-500/5 to-blue-500/5",
  }), [isDark])

  // Calculate container width on mount and resize
  useEffect(() => {
    const updateWidth = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth)
      }
    }

    updateWidth()
    window.addEventListener('resize', updateWidth)
    return () => window.removeEventListener('resize', updateWidth)
  }, [])

  // Duplicate connectors for seamless loop
  const duplicatedConnectors = [...CONNECTORS, ...CONNECTORS, ...CONNECTORS]
  const itemWidth = 120 // Width of each connector item
  const totalWidth = duplicatedConnectors.length * itemWidth
  const animationDuration = duplicatedConnectors.length * 0.5 // Adjust speed here

  // Start carousel animation
  useEffect(() => {
    if (!isHovered && totalWidth > 0) {
      controls.start({
        x: [-totalWidth / 3, -totalWidth * 2 / 3],
        transition: {
          duration: animationDuration,
          ease: "linear",
          repeat: Infinity,
          repeatType: "loop"
        }
      })
    } else {
      controls.stop()
    }
  }, [isHovered, controls, totalWidth, animationDuration])

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: { 
        duration: 0.8, 
        delay: 1.0,
        ease: "easeOut"
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: {
        duration: 0.4,
        type: "spring",
        stiffness: 200,
        damping: 20
      }
    }
  }

  return (
    <motion.section
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="text-center mt-20 overflow-hidden"
    >
      <motion.p 
        className={`text-xs ${themeStyles.textMuted} uppercase tracking-widest mb-12 font-medium`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 1.2 }}
      >
        CONNECTS WITH YOUR FAVORITE TOOLS
      </motion.p>

      {/* Carousel Container */}
      <div 
        ref={containerRef}
        className="relative overflow-hidden"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Gradient Fade Effects */}
        <div className={`absolute left-0 top-0 bottom-0 w-20 z-10 bg-gradient-to-r ${
          isDark ? "from-black/80 to-transparent" : "from-white/80 to-transparent"
        } pointer-events-none`} />
        <div className={`absolute right-0 top-0 bottom-0 w-20 z-10 bg-gradient-to-l ${
          isDark ? "from-black/80 to-transparent" : "from-white/80 to-transparent"
        } pointer-events-none`} />

        {/* Moving Carousel */}
        <motion.div
          animate={controls}
          className="flex space-x-4 py-4"
          style={{ width: totalWidth }}
        >
          {duplicatedConnectors.map((connector, index) => (
            <motion.div
              key={`${connector.name}-${index}`}
              variants={itemVariants}
              whileHover={{ 
                // scale: 1.1, 
                y: -4,
                transition: { duration: 0.2 }
              }}
              whileTap={{ scale: 0.95 }}
              className={`group relative flex-shrink-0 w-28 h-28 p-4 rounded-xl text-center cursor-pointer border transition-all duration-300 ${themeStyles.border} ${themeStyles.glass} ${themeStyles.hover}`}
              style={{ minWidth: itemWidth }}
            >
              {/* Hover glow effect */}
              <div className={`absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-gradient-to-br ${themeStyles.gradient}`} />
              
              {/* Content */}
              <div className="relative z-10 flex flex-col items-center justify-center h-full">
                <motion.div 
                  className="text-2xl mb-2 transition-transform duration-200"
                  // whileHover={{ scale: 1.2, rotate: 5 }}
                >
                  {connector.icon}
                </motion.div>
                <div className={`text-xs font-medium transition-colors duration-200 ${themeStyles.textSecondary} group-hover:${themeStyles.text.split(' ')[0]}`}>
                  {connector.name}
                </div>
              </div>

              {/* Hover border glow */}
              <div className={`absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300 ${
                isDark 
                  ? "ring-1 ring-purple-500/30 shadow-lg shadow-purple-500/10" 
                  : "ring-1 ring-purple-500/20 shadow-lg shadow-purple-500/5"
              }`} />
            </motion.div>
          ))}
        </motion.div>

        {/* Pause indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: isHovered ? 1 : 0 }}
          transition={{ duration: 0.2 }}
          className={`absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-medium ${
            isDark 
              ? "bg-gray-800/90 text-gray-300 border border-gray-700/50" 
              : "bg-white/90 text-gray-600 border border-gray-300/50"
          } backdrop-blur-sm`}
        >
          Paused
        </motion.div>
      </div>

      {/* Background decoration */}
      <div className={`absolute inset-0 -z-10 ${
        isDark 
          ? "bg-gradient-to-b from-transparent via-purple-900/5 to-transparent" 
          : "bg-gradient-to-b from-transparent via-purple-100/10 to-transparent"
      } pointer-events-none`} />
    </motion.section>
  )
}

export default ConnectorsSection