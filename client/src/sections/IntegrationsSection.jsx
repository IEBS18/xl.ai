// import React from "react"
// import { motion } from "framer-motion"
// import { useTheme } from "../context/ThemeProvider"

// const IntegrationsSection = () => {
//   const { isDark, themeClasses } = useTheme()

//   const integrations = [
//     { name: "Gmail" },
//     { name: "Salesforce" },
//     { name: "Docs" },
//     { name: "Slack" },
//     { name: "Excel" },
//     { name: "PowerPoint" },
//   ]

//   return (
//     <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
//       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
//         <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
//           <motion.div
//             initial={{ opacity: 0, x: -40 }}
//             whileInView={{ opacity: 1, x: 0 }}
//             transition={{ duration: 0.8 }}
//             viewport={{ once: true }}
//           >
//             <h2 className={`text-4xl md:text-5xl font-bold ${themeClasses.text} mb-8 tracking-tight`}>
//               Integrations
//             </h2>

//             <p className={`text-lg ${themeClasses.textSecondary} mb-10 leading-relaxed`}>
//               300+ integrations so you can research, analyze, and create without switching between platforms.
//             </p>

//             <p className={`${themeClasses.text} mb-8 font-medium`}>InsiPredict integrates with:</p>

//             <div className="flex flex-wrap gap-3 mb-10">
//               {integrations.map((integration, index) => (
//                 <motion.span
//                   key={integration.name}
//                   className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.border} ${themeClasses.textSecondary} hover:${themeClasses.text} cursor-pointer hover:scale-105 transition-all duration-300`}
//                   initial={{ opacity: 0, scale: 0.8 }}
//                   whileInView={{ opacity: 1, scale: 1 }}
//                   transition={{ duration: 0.3, delay: index * 0.1 }}
//                   viewport={{ once: true }}
//                   whileHover={{ y: -2 }}
//                 >
//                   {integration.name}
//                 </motion.span>
//               ))}
//             </div>

//             <p className={`${themeClasses.textMuted} text-sm`}>+ many more</p>
//           </motion.div>

//           <motion.div
//             initial={{ opacity: 0, x: 40 }}
//             whileInView={{ opacity: 1, x: 0 }}
//             transition={{ duration: 0.8 }}
//             viewport={{ once: true }}
//             className="relative"
//           >
//             <div className="grid grid-cols-3 gap-8 items-center">
//               {[
//                 [{ delay: 0 }, { delay: 0.1 }],
//                 [{ delay: 0.2 }, { delay: 0.3 }, { delay: 0.4 }],
//                 [{ delay: 0.5 }, { delay: 0.6 }],
//               ].map((column, colIndex) => (
//                 <div key={colIndex} className="space-y-8">
//                   {column.map((item, itemIndex) => (
//                     <motion.div
//                       key={itemIndex}
//                       className={`w-16 h-16 ${themeClasses.surfaceSecondary} rounded-2xl flex items-center justify-center shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group border ${themeClasses.border}`}
//                       initial={{ opacity: 0, scale: 0, rotate: -90 }}
//                       whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
//                       transition={{
//                         duration: 0.6,
//                         delay: item.delay,
//                         type: "spring",
//                         stiffness: 200,
//                       }}
//                       viewport={{ once: true }}
//                       whileHover={{ scale: 1.1, rotate: 3 }}
//                     >
//                       <div
//                         className={`w-8 h-8 ${isDark ? "bg-white" : "bg-black"} rounded group-hover:rotate-12 transition-transform duration-300`}
//                       />
//                     </motion.div>
//                   ))}
//                 </div>
//               ))}
//             </div>
//           </motion.div>
//         </div>
//       </div>
//     </section>
//   )
// }

// export default IntegrationsSection


// import React from "react"
// import { motion } from "framer-motion"
// import { 
//   Mail, 
//   FileText, 
//   MessageSquare, 
//   FileSpreadsheet, 
//   Presentation,
//   Database,
//   Server,
//   Cloud,
//   HardDrive,
//   Cylinder
// } from "lucide-react"
// import { useTheme } from "../context/ThemeProvider"

// const IntegrationsSection = () => {
//   const { isDark, themeClasses } = useTheme()

//   const integrations = [
//     { name: "Gmail", icon: Mail },
//     { name: "Salesforce", icon: Server },
//     { name: "Docs", icon: FileText },
//     { name: "Slack", icon: MessageSquare },
//     { name: "Excel", icon: FileSpreadsheet },
//     { name: "PowerPoint", icon: Presentation },
//     { name: "PostgreSQL", icon: Database },
//     { name: "MySQL", icon: Cylinder },
//     { name: "S3", icon: Cloud },
//     { name: "Blob Storage", icon: HardDrive },
//     { name: "Oracle", icon: Database },
//   ]

//   // Create icon grid with varied arrangements - perfectly balanced
//   const iconGridData = [
//     [
//       { icon: Mail, delay: 0, color: "text-red-500" },
//       { icon: Database, delay: 0.1, color: "text-blue-500" },
//       { icon: FileSpreadsheet, delay: 0.2, color: "text-emerald-500" }
//     ],
//     [
//       { icon: Server, delay: 0.3, color: "text-purple-500" },
//       { icon: MessageSquare, delay: 0.4, color: "text-green-500" },
//       { icon: Cloud, delay: 0.5, color: "text-orange-500" },
//       { icon: Cylinder, delay: 0.6, color: "text-indigo-500" }
//     ],
//     [
//       { icon: FileText, delay: 0.7, color: "text-teal-500" },
//       { icon: Presentation, delay: 0.8, color: "text-pink-500" },
//       { icon: HardDrive, delay: 0.9, color: "text-amber-500" }
//     ]
//   ]

//   return (
//     <section className={`py-20 lg:py-24 ${themeClasses.bg} relative overflow-hidden`}>
//       {/* Background decoration */}
//       <div className="absolute inset-0 pointer-events-none overflow-hidden">
//         <div className={`absolute top-20 right-20 w-32 h-32 rounded-full ${
//           isDark ? "bg-white/5" : "bg-black/5"
//         } blur-3xl`}></div>
//         <div className={`absolute bottom-20 left-20 w-24 h-24 rounded-full ${
//           isDark ? "bg-blue-500/10" : "bg-blue-500/10"
//         } blur-2xl`}></div>
//       </div>

//       <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
//         <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center min-h-[600px]">
          
//           {/* Left Content */}
//           <motion.div
//             initial={{ opacity: 0, x: -40 }}
//             whileInView={{ opacity: 1, x: 0 }}
//             transition={{ duration: 0.8 }}
//             viewport={{ once: true }}
//             className="flex flex-col justify-center space-y-8"
//           >
//             <div className="space-y-6">
//               <h2 className={`text-3xl sm:text-4xl md:text-5xl font-bold ${themeClasses.text} tracking-tight leading-tight`}>
//                 Integrations
//               </h2>

//               <p className={`text-base sm:text-lg ${themeClasses.textSecondary} leading-relaxed max-w-xl`}>
//                 300+ integrations so you can research, analyze, and create without switching between platforms.
//               </p>
//             </div>

//             <div className="space-y-6">
//               <p className={`${themeClasses.text} font-medium text-sm uppercase tracking-wide`}>
//                 InsiPredict integrates with:
//               </p>

//               <div className="flex flex-wrap gap-2 sm:gap-3">
//                 {integrations.map((integration, index) => {
//                   const IconComponent = integration.icon
//                   return (
//                     <motion.div
//                       key={integration.name}
//                       className={`flex items-center space-x-2 px-3 sm:px-4 py-2 rounded-full text-xs sm:text-sm font-medium border transition-all duration-300 cursor-pointer group ${
//                         isDark 
//                           ? "border-white/20 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white hover:border-white/30" 
//                           : "border-black/20 bg-black/5 text-black/70 hover:bg-black/10 hover:text-black hover:border-black/30"
//                       }`}
//                       initial={{ opacity: 0, scale: 0.8 }}
//                       whileInView={{ opacity: 1, scale: 1 }}
//                       transition={{ duration: 0.3, delay: index * 0.03 }}
//                       viewport={{ once: true }}
//                       whileHover={{ y: -2, scale: 1.05 }}
//                     >
//                       <IconComponent className="w-3 h-3 sm:w-4 sm:h-4 group-hover:scale-110 transition-transform duration-200 flex-shrink-0" />
//                       <span className="whitespace-nowrap">{integration.name}</span>
//                     </motion.div>
//                   )
//                 })}
//               </div>

//               <p className={`${themeClasses.textMuted} text-sm font-medium`}>
//                 + many more
//               </p>
//             </div>
//           </motion.div>

//           {/* Right Visual Grid */}
//           <motion.div
//             initial={{ opacity: 0, x: 40 }}
//             whileInView={{ opacity: 1, x: 0 }}
//             transition={{ duration: 0.8 }}
//             viewport={{ once: true }}
//             className="flex justify-center lg:justify-end"
//           >
//             <div className="relative w-full max-w-sm lg:max-w-md">
              
//               {/* Icon Grid */}
//               <div className="grid grid-cols-3 gap-4 sm:gap-6 lg:gap-8 justify-items-center">
//                 {iconGridData.map((column, colIndex) => (
//                   <div key={colIndex} className={`flex flex-col space-y-4 sm:space-y-6 lg:space-y-8 ${
//                     colIndex === 1 ? 'justify-center' : colIndex === 0 ? 'justify-start pt-8' : 'justify-end pb-8'
//                   }`}>
//                     {column.map((item, itemIndex) => {
//                       const IconComponent = item.icon
//                       return (
//                         <motion.div
//                           key={itemIndex}
//                           className={`w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-xl lg:rounded-2xl flex items-center justify-center shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group border backdrop-blur-sm ${
//                             isDark 
//                               ? "bg-white/10 border-white/20 hover:bg-white/20 hover:border-white/30" 
//                               : "bg-white/80 border-black/10 hover:bg-white hover:border-black/20"
//                           }`}
//                           initial={{ opacity: 0, scale: 0, rotate: -90 }}
//                           whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
//                           transition={{
//                             duration: 0.6,
//                             delay: item.delay,
//                             type: "spring",
//                             stiffness: 200,
//                             damping: 15
//                           }}
//                           viewport={{ once: true }}
//                           whileHover={{ scale: 1.1, rotate: 3, y: -2 }}
//                         >
//                           <IconComponent
//                             className={`w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8 ${item.color} group-hover:rotate-12 transition-transform duration-300 drop-shadow-sm`}
//                           />
//                         </motion.div>
//                       )
//                     })}
//                   </div>
//                 ))}
//               </div>

//               {/* Floating connection lines - responsive */}
//               <div className="absolute inset-0 pointer-events-none opacity-40">
//                 <svg className="w-full h-full" viewBox="0 0 300 300" preserveAspectRatio="xMidYMid meet">
//                   <motion.path
//                     d="M60,80 Q150,40 240,120"
//                     stroke={isDark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.15)"}
//                     strokeWidth="1.5"
//                     fill="none"
//                     strokeDasharray="4,4"
//                     initial={{ pathLength: 0, opacity: 0 }}
//                     whileInView={{ pathLength: 1, opacity: 1 }}
//                     transition={{ duration: 2, delay: 1.2 }}
//                     viewport={{ once: true }}
//                   />
//                   <motion.path
//                     d="M80,180 Q150,200 220,100"
//                     stroke={isDark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.15)"}
//                     strokeWidth="1.5"
//                     fill="none"
//                     strokeDasharray="4,4"
//                     initial={{ pathLength: 0, opacity: 0 }}
//                     whileInView={{ pathLength: 1, opacity: 1 }}
//                     transition={{ duration: 2, delay: 1.6 }}
//                     viewport={{ once: true }}
//                   />
//                   <motion.path
//                     d="M140,60 Q180,150 120,240"
//                     stroke={isDark ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.15)"}
//                     strokeWidth="1.5"
//                     fill="none"
//                     strokeDasharray="4,4"
//                     initial={{ pathLength: 0, opacity: 0 }}
//                     whileInView={{ pathLength: 1, opacity: 1 }}
//                     transition={{ duration: 2, delay: 2 }}
//                     viewport={{ once: true }}
//                   />
//                 </svg>
//               </div>

//               {/* Glow effects */}
//               <div className="absolute inset-0 pointer-events-none">
//                 <div className={`absolute top-1/4 left-1/4 w-16 h-16 rounded-full ${
//                   isDark ? "bg-blue-500/20" : "bg-blue-500/10"
//                 } blur-xl animate-pulse`}></div>
//                 <div className={`absolute bottom-1/4 right-1/4 w-12 h-12 rounded-full ${
//                   isDark ? "bg-purple-500/20" : "bg-purple-500/10"
//                 } blur-lg animate-pulse`} style={{ animationDelay: '1s' }}></div>
//               </div>
//             </div>
//           </motion.div>

//         </div>
//       </div>
//     </section>
//   )
// }

// export default IntegrationsSection



import React from "react"
import { motion } from "framer-motion"
import { 
  Mail, 
  FileText, 
  MessageSquare, 
  FileSpreadsheet, 
  Presentation,
  Database,
  Server,
  Cloud,
  HardDrive,
  Cylinder
} from "lucide-react"
import { useTheme } from "../context/ThemeProvider"

const IntegrationsSection = () => {
  const { isDark, themeClasses } = useTheme()

  const integrations = [
    { name: "Gmail", icon: Mail },
    { name: "Salesforce", icon: Server },
    { name: "Docs", icon: FileText },
    { name: "Slack", icon: MessageSquare },
    { name: "Excel", icon: FileSpreadsheet },
    { name: "PowerPoint", icon: Presentation },
    { name: "PostgreSQL", icon: Database },
    { name: "MySQL", icon: Cylinder },
    { name: "S3", icon: Cloud },
    { name: "Blob Storage", icon: HardDrive },
    { name: "Oracle", icon: Database },
  ]

  // Create icon grid with varied arrangements - perfectly balanced
  const iconGridData = [
    [
      { icon: Mail, delay: 0, color: "text-red-500" },
      { icon: Database, delay: 0.1, color: "text-blue-500" },
      { icon: FileSpreadsheet, delay: 0.2, color: "text-emerald-500" }
    ],
    [
      { icon: Server, delay: 0.3, color: "text-purple-500" },
      { icon: MessageSquare, delay: 0.4, color: "text-green-500" },
      { icon: Cloud, delay: 0.5, color: "text-orange-500" },
      { icon: Cylinder, delay: 0.6, color: "text-indigo-500" }
    ],
    [
      { icon: FileText, delay: 0.7, color: "text-teal-500" },
      { icon: Presentation, delay: 0.8, color: "text-pink-500" },
      { icon: HardDrive, delay: 0.9, color: "text-amber-500" }
    ]
  ]

  return (
    <section className={`py-20 lg:py-24 ${themeClasses.bg} relative overflow-hidden`}>
      {/* Background decoration */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        <div className={`absolute top-20 right-20 w-32 h-32 rounded-full ${
          isDark ? "bg-white/5" : "bg-black/5"
        } blur-3xl`}></div>
        <div className={`absolute bottom-20 left-20 w-24 h-24 rounded-full ${
          isDark ? "bg-blue-500/10" : "bg-blue-500/10"
        } blur-2xl`}></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-16 items-center min-h-[600px]">
          
          {/* Left Content */}
          <motion.div
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="flex flex-col justify-center space-y-8"
          >
            <div className="space-y-6">
              <h2 className={`text-3xl sm:text-4xl md:text-5xl font-bold ${themeClasses.text} tracking-tight leading-tight`}>
                Integrations
              </h2>

              <p className={`text-base sm:text-lg ${themeClasses.textSecondary} leading-relaxed max-w-xl`}>
                300+ integrations so you can research, analyze, and create without switching between platforms.
              </p>
            </div>

            <div className="space-y-6">
              <p className={`${themeClasses.text} font-medium text-sm uppercase tracking-wide`}>
                InsiPredict integrates with:
              </p>

              <div className="flex flex-wrap gap-2 sm:gap-3">
                {integrations.map((integration, index) => {
                  const IconComponent = integration.icon
                  return (
                    <motion.div
                      key={integration.name}
                      className={`flex items-center space-x-2 px-3 sm:px-4 py-2 rounded-full text-xs sm:text-sm font-medium border transition-all duration-300 cursor-pointer group ${
                        isDark 
                          ? "border-white/20 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white hover:border-white/30" 
                          : "border-black/20 bg-black/5 text-black/70 hover:bg-black/10 hover:text-black hover:border-black/30"
                      }`}
                      initial={{ opacity: 0, scale: 0.8 }}
                      whileInView={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.3, delay: index * 0.03 }}
                      viewport={{ once: true }}
                      whileHover={{ y: -2, scale: 1.05 }}
                    >
                      <IconComponent className="w-3 h-3 sm:w-4 sm:h-4 group-hover:scale-110 transition-transform duration-200 flex-shrink-0" />
                      <span className="whitespace-nowrap">{integration.name}</span>
                    </motion.div>
                  )
                })}
              </div>

              <p className={`${themeClasses.textMuted} text-sm font-medium`}>
                + many more
              </p>
            </div>
          </motion.div>

          {/* Right Visual Grid */}
          <motion.div
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="flex justify-center lg:justify-end"
          >
            <div className="relative w-full max-w-sm lg:max-w-md">
              
              {/* Icon Grid */}
              <div className="grid grid-cols-3 gap-4 sm:gap-6 lg:gap-8 justify-items-center">
                {iconGridData.map((column, colIndex) => (
                  <div key={colIndex} className={`flex flex-col space-y-4 sm:space-y-6 lg:space-y-8 ${
                    colIndex === 1 ? 'justify-center' : colIndex === 0 ? 'justify-start pt-8' : 'justify-end pb-8'
                  }`}>
                    {column.map((item, itemIndex) => {
                      const IconComponent = item.icon
                      return (
                        <motion.div
                          key={itemIndex}
                          className={`w-12 h-12 sm:w-14 sm:h-14 lg:w-16 lg:h-16 rounded-xl lg:rounded-2xl flex items-center justify-center shadow-lg hover:shadow-2xl transition-all duration-300 cursor-pointer group border backdrop-blur-sm ${
                            isDark 
                              ? "bg-white/10 border-white/20 hover:bg-white/20 hover:border-white/30" 
                              : "bg-white/80 border-black/10 hover:bg-white hover:border-black/20"
                          }`}
                          initial={{ opacity: 0, scale: 0, rotate: -90 }}
                          whileInView={{ opacity: 1, scale: 1, rotate: 0 }}
                          transition={{
                            duration: 0.6,
                            delay: item.delay,
                            type: "spring",
                            stiffness: 200,
                            damping: 15
                          }}
                          viewport={{ once: true }}
                          whileHover={{ scale: 1.1, rotate: 3, y: -2 }}
                        >
                          <IconComponent
                            className={`w-6 h-6 sm:w-7 sm:h-7 lg:w-8 lg:h-8 ${item.color} group-hover:rotate-12 transition-transform duration-300 drop-shadow-sm`}
                          />
                        </motion.div>
                      )
                    })}
                  </div>
                ))}
              </div>

              {/* Enhanced floating connection lines - responsive */}
              <div className="absolute inset-0 pointer-events-none opacity-30">
                <svg className="w-full h-full" viewBox="0 0 400 400" preserveAspectRatio="xMidYMid meet">
                  {/* Primary connections - flowing curves */}
                  <motion.path
                    d="M80,100 Q200,60 320,140 Q280,180 200,160 Q120,180 80,200"
                    stroke={isDark ? "rgba(59, 130, 246, 0.4)" : "rgba(59, 130, 246, 0.3)"}
                    strokeWidth="2"
                    fill="none"
                    strokeDasharray="8,4"
                    initial={{ pathLength: 0, opacity: 0 }}
                    whileInView={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 3, delay: 1.2, ease: "easeInOut" }}
                    viewport={{ once: true }}
                  />
                  
                  {/* Secondary connections - organic flow */}
                  <motion.path
                    d="M120,80 Q200,120 280,100 Q320,160 280,220 Q200,240 120,220"
                    stroke={isDark ? "rgba(168, 85, 247, 0.3)" : "rgba(168, 85, 247, 0.25)"}
                    strokeWidth="1.5"
                    fill="none"
                    strokeDasharray="6,3"
                    initial={{ pathLength: 0, opacity: 0 }}
                    whileInView={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 3.5, delay: 1.6, ease: "easeInOut" }}
                    viewport={{ once: true }}
                  />

                  {/* Tertiary connections - subtle network */}
                  <motion.path
                    d="M100,140 Q160,100 240,120 Q300,140 340,180 Q320,240 260,260 Q180,280 120,240 Q80,200 100,140"
                    stroke={isDark ? "rgba(34, 197, 94, 0.25)" : "rgba(34, 197, 94, 0.2)"}
                    strokeWidth="1"
                    fill="none"
                    strokeDasharray="4,6"
                    initial={{ pathLength: 0, opacity: 0 }}
                    whileInView={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 4, delay: 2, ease: "easeInOut" }}
                    viewport={{ once: true }}
                  />

                  {/* Diagonal connections */}
                  <motion.path
                    d="M60,120 Q150,80 240,120 Q300,160 360,140"
                    stroke={isDark ? "rgba(245, 101, 101, 0.2)" : "rgba(245, 101, 101, 0.15)"}
                    strokeWidth="1.5"
                    fill="none"
                    strokeDasharray="10,5"
                    initial={{ pathLength: 0, opacity: 0 }}
                    whileInView={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 2.5, delay: 2.4, ease: "easeInOut" }}
                    viewport={{ once: true }}
                  />

                  <motion.path
                    d="M100,320 Q180,280 260,300 Q320,260 380,280"
                    stroke={isDark ? "rgba(251, 191, 36, 0.25)" : "rgba(251, 191, 36, 0.2)"}
                    strokeWidth="1"
                    fill="none"
                    strokeDasharray="5,8"
                    initial={{ pathLength: 0, opacity: 0 }}
                    whileInView={{ pathLength: 1, opacity: 1 }}
                    transition={{ duration: 3.2, delay: 2.8, ease: "easeInOut" }}
                    viewport={{ once: true }}
                  />

                  {/* Connecting nodes - small circles at intersections */}
                  <motion.circle
                    cx="200"
                    cy="160"
                    r="2"
                    fill={isDark ? "rgba(59, 130, 246, 0.6)" : "rgba(59, 130, 246, 0.5)"}
                    initial={{ scale: 0, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5, delay: 3.2 }}
                    viewport={{ once: true }}
                  />

                  <motion.circle
                    cx="280"
                    cy="140"
                    r="1.5"
                    fill={isDark ? "rgba(168, 85, 247, 0.6)" : "rgba(168, 85, 247, 0.5)"}
                    initial={{ scale: 0, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5, delay: 3.4 }}
                    viewport={{ once: true }}
                  />

                  <motion.circle
                    cx="240"
                    cy="220"
                    r="1.5"
                    fill={isDark ? "rgba(34, 197, 94, 0.6)" : "rgba(34, 197, 94, 0.5)"}
                    initial={{ scale: 0, opacity: 0 }}
                    whileInView={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 0.5, delay: 3.6 }}
                    viewport={{ once: true }}
                  />

                  {/* Data flow particles */}
                  <motion.circle
                    cx="0"
                    cy="0"
                    r="1.5"
                    fill={isDark ? "rgba(59, 130, 246, 0.8)" : "rgba(59, 130, 246, 0.7)"}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0, 1, 0] }}
                    transition={{ duration: 2, repeat: Infinity, delay: 4 }}
                  >
                    <animateMotion dur="4s" repeatCount="indefinite" begin="4s">
                      <mpath href="#primaryPath" />
                    </animateMotion>
                  </motion.circle>

                  {/* Hidden path for particle animation */}
                  <path
                    id="primaryPath"
                    d="M80,100 Q200,60 320,140 Q280,180 200,160 Q120,180 80,200"
                    stroke="none"
                    fill="none"
                  />
                </svg>
              </div>

              {/* Enhanced glow effects with better positioning */}
              <div className="absolute inset-0 pointer-events-none">
                <div className={`absolute top-1/4 left-1/3 w-20 h-20 rounded-full ${
                  isDark ? "bg-blue-500/10" : "bg-blue-500/5"
                } blur-2xl animate-pulse`}></div>
                <div className={`absolute bottom-1/3 right-1/4 w-16 h-16 rounded-full ${
                  isDark ? "bg-purple-500/15" : "bg-purple-500/8"
                } blur-xl animate-pulse`} style={{ animationDelay: '1.5s' }}></div>
                <div className={`absolute top-1/2 left-1/2 w-12 h-12 rounded-full ${
                  isDark ? "bg-green-500/10" : "bg-green-500/5"
                } blur-lg animate-pulse transform -translate-x-1/2 -translate-y-1/2`} style={{ animationDelay: '3s' }}></div>
              </div>
            </div>
          </motion.div>

        </div>
      </div>
    </section>
  )
}

export default IntegrationsSection