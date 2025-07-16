
import React, { useState, useEffect, useRef } from 'react';
import { motion, useScroll, useTransform, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Shield,
  Zap,
  Users,
  Database,
  ArrowRight,
  CheckCircle,
  Menu,
  X,
  Globe,
  Lock,
  Cpu,
  BarChart3,
  Sparkles,
  Play,
  Award,
  TrendingUp,
  Star,
  Search,
  FileSpreadsheet,
  Presentation,
  FileText,
  BarChart,
  MessageSquare,
  Send,
  ChevronDown,
  Plus,
  Upload,
  Link,
  Slack,
  Mail,
  Cloud,
  Moon,
  Sun,
  Layers,
  Hexagon,
  Zap as Lightning,
  Eye,
  Code,
  Network,
  LogOut
} from 'lucide-react';
import { useTheme } from '../hook/useTheme';
import { useThemeClasses } from '../hooks/useThemeClasses';
import { useAuth } from '../contexts/AuthContext';
import { Button } from './ui/Button';
import { AuthModal } from './auth/AuthModal';
import WorkingInterface from './WorkingInterface';

export default function LandingPage({ onGetStarted }) {
  const { isDark, toggleTheme } = useTheme();
  const themeClasses = useThemeClasses();
  const { user, logout, isAuthenticated } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [activeTab, setActiveTab] = useState('spreadsheets');
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [authMode, setAuthMode] = useState('login');
  const { scrollYProgress } = useScroll();
  const y = useTransform(scrollYProgress, [0, 1], ['0%', '50%']);

  const connectors = [
    { name: 'Google Sheets', icon: '📊' },
    { name: 'Excel Online', icon: '📈' },
    { name: 'Airtable', icon: '🗃️' },
    { name: 'Notion', icon: '📝' },
    { name: 'MySQL', icon: '🗄️' },
    { name: 'PostgreSQL', icon: '🐘' },
    { name: 'MongoDB', icon: '🍃' },
    { name: 'Salesforce', icon: '☁️' },
    { name: 'HubSpot', icon: '🎯' },
    { name: 'Zapier', icon: '⚡' },
    { name: 'CSV/Excel', icon: '📄' },
    { name: 'API', icon: '🔌' },
  ];

  const tabs = [
    { id: 'spreadsheets', icon: FileSpreadsheet, label: 'Spreadsheets' },
    { id: 'presentations', icon: Presentation, label: 'Presentations' },
    { id: 'documents', icon: FileText, label: 'Documents' },
    { id: 'analyst', icon: BarChart, label: 'Data Analyst' },
    { id: 'search', icon: Search, label: 'Deep & Enterprise Search' },
  ];


  return (
    <div className={`min-h-screen transition-all duration-500 ${themeClasses.bg} ${themeClasses.text}`}>
      
      {/* Header */}
      <header className={`fixed top-0 w-full z-50 ${themeClasses.glass} border-b ${themeClasses.border}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <motion.div 
              className="flex items-center space-x-3"
              whileHover={{ scale: 1.02 }}
              transition={{ type: "spring", stiffness: 400 }}
            >
              <div className="flex items-center space-x-1">
                <div className={`w-6 h-6 ${themeClasses.text} rounded`} />
                <div className={`w-2 h-6 ${themeClasses.text} rounded`} />
              </div>
              <span className={`text-xl font-semibold ${themeClasses.text}`}>InsiPredict</span>
            </motion.div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              <div className="relative group">
                <button className={`flex items-center space-x-1 ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}>
                  <span>Use Cases</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
              </div>
              <a href="#contact" className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}>
                Contact Us
              </a>
              <a href="#pricing" className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}>
                Pricing
              </a>
            </nav>

            <div className="flex items-center space-x-4">
              {/* Theme Toggle */}
              <motion.button
                onClick={toggleTheme}
                className={`p-2 rounded-lg border ${themeClasses.border} hover:scale-110 transition-all duration-300`}
                whileHover={{ rotate: 180 }}
                whileTap={{ scale: 0.9 }}
              >
                <AnimatePresence mode="wait">
                  {isDark ? (
                    <motion.div
                      key="sun"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Sun className="w-5 h-5" />
                    </motion.div>
                  ) : (
                    <motion.div
                      key="moon"
                      initial={{ rotate: -90, opacity: 0 }}
                      animate={{ rotate: 0, opacity: 1 }}
                      exit={{ rotate: 90, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <Moon className="w-5 h-5" />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>

              {isAuthenticated ? (
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                      <span className="text-white text-sm font-medium">
                        {user?.first_name?.[0]}{user?.last_name?.[0]}
                      </span>
                    </div>
                    <span className={`hidden md:inline text-sm font-medium ${themeClasses.text}`}>
                      {user?.first_name} {user?.last_name}
                    </span>
                  </div>
                  <button
                    onClick={logout}
                    className={`p-2 rounded-lg ${themeClasses.textSecondary} hover:${themeClasses.text} hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors`}
                    title="Logout"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <>
                  <button 
                    onClick={() => {
                      setAuthMode('login');
                      setShowAuthModal(true);
                    }}
                    className={`hidden md:inline-flex ${themeClasses.textSecondary} hover:${themeClasses.text} font-medium transition-colors`}
                  >
                    Log in
                  </button>
                  
                  <Button 
                    onClick={() => {
                      setAuthMode('register');
                      setShowAuthModal(true);
                    }}
                    variant="primary" 
                    size="md"
                  >
                    <span>Get Started</span>
                    <ArrowRight className="w-4 h-4" />
                  </Button>
                </>
              )}
              
              {/* Mobile menu button */}
              <button
                className={`md:hidden ${themeClasses.textSecondary}`}
                onClick={() => setIsMenuOpen(!isMenuOpen)}
              >
                {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          <AnimatePresence>
            {isMenuOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className={`md:hidden border-t ${themeClasses.border} py-4`}
              >
                <div className="flex flex-col space-y-4">
                  <a href="#usecases" className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}>
                    Use Cases
                  </a>
                  <a href="#contact" className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}>
                    Contact Us
                  </a>
                  <a href="#pricing" className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors font-medium`}>
                    Pricing
                  </a>
                  {isAuthenticated ? (
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-sm font-medium">
                            {user?.first_name?.[0]}{user?.last_name?.[0]}
                          </span>
                        </div>
                        <span className={`text-sm font-medium ${themeClasses.text}`}>
                          {user?.first_name} {user?.last_name}
                        </span>
                      </div>
                      <button
                        onClick={logout}
                        className={`p-2 rounded-lg ${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}
                        title="Logout"
                      >
                        <LogOut className="w-4 h-4" />
                      </button>
                    </div>
                  ) : (
                    <>
                      <button 
                        onClick={() => {
                          setAuthMode('login');
                          setShowAuthModal(true);
                          setIsMenuOpen(false);
                        }}
                        className={`text-left ${themeClasses.textSecondary} hover:${themeClasses.text} font-medium transition-colors`}
                      >
                        Log in
                      </button>
                      <button 
                        onClick={() => {
                          setAuthMode('register');
                          setShowAuthModal(true);
                          setIsMenuOpen(false);
                        }}
                        className={`text-left ${themeClasses.text} font-medium transition-colors`}
                      >
                        Get Started
                      </button>
                    </>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </header>

      {/* Hero Section - Working Interface or Marketing */}
      <section className="relative pt-20 overflow-hidden">
        {isAuthenticated ? (
          /* Working Interface for Authenticated Users */
          <WorkingInterface />
        ) : (
          /* Marketing Hero for Unauthenticated Users */
          <div className="pb-20">
            {/* Simple gradient background */}
            <div className="absolute inset-0 z-0 opacity-20">
              <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-gradient-to-r from-blue-500/10 to-purple-500/10 rounded-full blur-3xl animate-pulse" />
              <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-gradient-to-r from-purple-500/10 to-pink-500/10 rounded-full blur-3xl animate-pulse" style={{animationDelay: '1s'}} />
            </div>
            
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="text-center max-w-4xl mx-auto mb-20"
              >
                <motion.h1
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.2 }}
                  className={`text-4xl sm:text-5xl md:text-6xl lg:text-7xl xl:text-8xl font-bold ${themeClasses.text} mb-8 leading-tight tracking-tight`}
                >
                  The AI{' '}
                  <span className="italic font-light">Data Analysis</span>{' '}
                  Platform
                </motion.h1>

                <motion.p
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.4 }}
                  className={`text-lg sm:text-xl md:text-2xl ${themeClasses.textSecondary} mb-16 max-w-2xl mx-auto leading-relaxed px-4`}
                >
                  Transform your data into actionable insights with AI-powered analysis
                </motion.p>

                {/* Product Tabs */}
                <motion.div 
                  className="flex flex-wrap justify-center gap-2 sm:gap-3 mb-12 px-4"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.6 }}
                >
                  {tabs.map((tab, index) => (
                    <motion.button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center space-x-1 sm:space-x-2 px-2 sm:px-4 py-2 rounded-lg transition-all duration-300 border ${
                        activeTab === tab.id
                          ? `${themeClasses.button} border-transparent`
                          : `${themeClasses.buttonSecondary} border ${themeClasses.border} bg-transparent`
                      }`}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.5, delay: index * 0.05 }}
                    >
                      <tab.icon className="w-4 h-4" />
                      <span className="text-xs sm:text-sm font-medium">{tab.label}</span>
                    </motion.button>
                  ))}
                </motion.div>

                {/* Auth CTA */}
                <motion.div 
                  className="max-w-2xl mx-auto"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.8, delay: 0.8 }}
                >
                  <div className={`relative ${themeClasses.glass} rounded-2xl shadow-xl border ${themeClasses.border} p-6`}>
                    <div className="flex items-center space-x-4">
                      <input
                        type="text"
                        placeholder="Ask me to analyze your data..."
                        className={`flex-1 ${themeClasses.textSecondary} placeholder:${themeClasses.textMuted} bg-transparent border-none outline-none text-lg`}
                        readOnly
                      />
                      <motion.button 
                        onClick={() => {
                          setAuthMode('register');
                          setShowAuthModal(true);
                        }}
                        className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors p-2 rounded-lg`}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <Send className="w-6 h-6" />
                      </motion.button>
                    </div>
                  </div>
                </motion.div>
              </motion.div>

              {/* Connectors Section */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, delay: 1.0 }}
                className="text-center"
              >
                <p className={`text-xs ${themeClasses.textMuted} uppercase tracking-widest mb-12 font-medium`}>
                  SUPPORTS ALL YOUR DATA SOURCES
                </p>
                
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 lg:grid-cols-12 gap-3 sm:gap-4 max-w-6xl mx-auto">
                  {connectors.map((connector, index) => (
                    <motion.div
                      key={connector.name}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ 
                        duration: 0.4, 
                        delay: index * 0.03,
                        type: "spring",
                        stiffness: 200
                      }}
                      className={`p-3 sm:p-4 rounded-xl text-center hover:scale-105 transition-all duration-300 cursor-pointer border ${themeClasses.border} ${themeClasses.glass}`}
                      whileHover={{ y: -2 }}
                    >
                      <div className="text-xl sm:text-2xl mb-2">{connector.icon}</div>
                      <div className={`text-xs font-medium ${themeClasses.textMuted}`}>
                        {connector.name}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </div>
          </div>
        )}
      </section>

      {/* Marketing Sections - Only show for unauthenticated users */}
      {!isAuthenticated && (
        <>
          {/* Collaboration Section */}
          <section className={`py-24 ${themeClasses.surface} relative overflow-hidden`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <h2 className={`text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-bold ${themeClasses.text} mb-4 leading-tight tracking-tight`}>
              One platform to<br />
              analyze data, together
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-16 items-center">
            {/* Performance Report Mockup */}
            <motion.div
              initial={{ opacity: 0, x: -40 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className={`${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
            >
              <motion.div 
                className={`${themeClasses.surface} p-8 rounded-2xl shadow-2xl border ${themeClasses.border}`}
                whileHover={{ scale: 1.01 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <div className="flex items-center justify-between mb-6">
                  <h3 className={`text-2xl font-semibold ${themeClasses.text}`}>Performance Report</h3>
                  <span className={`text-sm ${themeClasses.textMuted}`}>Q2 2025</span>
                </div>
                
                <div className="space-y-8">
                  <div>
                    <h4 className={`font-medium mb-3 ${themeClasses.text}`}>Summary</h4>
                    <p className={`text-sm ${themeClasses.textSecondary} leading-relaxed`}>
                      Performance metrics show significant improvement across key indicators with notable enhancement in operational efficiency and customer satisfaction.
                    </p>
                  </div>
                  
                  <div>
                    <h4 className={`font-medium mb-6 ${themeClasses.text}`}>Monthly Active Users</h4>
                    <div className="flex items-end space-x-2 h-32">
                      {[...Array(12)].map((_, i) => (
                        <motion.div
                          key={i}
                          className={`${themeClasses.text} rounded-sm flex-1 opacity-80`}
                          style={{ height: `${Math.random() * 80 + 20}%` }}
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

            {/* Chat Interface Mockup */}
            <motion.div
              initial={{ opacity: 0, x: 40 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className={`${themeClasses.surfaceSecondary} p-8 rounded-3xl border ${themeClasses.border}`}
            >
              <div className="flex items-center space-x-3 mb-8">
                <div className={`w-10 h-10 ${themeClasses.surface} rounded-lg flex items-center justify-center border ${themeClasses.border}`}>
                  <MessageSquare className="w-5 h-5" />
                </div>
                <div>
                  <div className={`font-medium ${themeClasses.text}`}>SpreadSheet AI</div>
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
                  <div className={`w-8 h-8 ${themeClasses.surfaceSecondary} rounded-full flex-shrink-0 border ${themeClasses.border}`}></div>
                  <div>
                    <div className={`font-medium text-sm ${themeClasses.text}`}>Tony</div>
                    <div className={`text-sm ${themeClasses.textSecondary}`}>How's the progress on the report team?</div>
                  </div>
                </motion.div>

                <motion.div 
                  className="flex items-start space-x-3"
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 }}
                  viewport={{ once: true }}
                >
                  <div className={`w-8 h-8 ${themeClasses.surfaceSecondary} rounded-full flex-shrink-0 border ${themeClasses.border}`}></div>
                  <div>
                    <div className={`font-medium text-sm ${themeClasses.text}`}>David</div>
                    <div className={`text-sm ${themeClasses.textSecondary}`}>Just gave the task to SpreadSheet AI, should have it soon</div>
                  </div>
                </motion.div>
              </div>

              <motion.div 
                className={`${themeClasses.surface} rounded-xl p-6 border ${themeClasses.border} shadow-lg`}
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
            {[
              {
                title: "Smart data analysis",
                description: "AI-powered insights from your data with natural language queries and automated visualizations",
                icon: Users
              },
              {
                title: "Works with your data",
                description: "InsiPredict connects to any data source you have - from CSV files to complex databases, delivering insights in seconds.",
                icon: Network
              },
              {
                title: "Transparent insights",
                description: "See exactly how conclusions are reached with step-by-step analysis and clear explanations of every insight.",
                icon: Eye
              }
            ].map((feature, index) => (
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
                  className={`w-12 h-12 ${themeClasses.surfaceSecondary} rounded-xl flex items-center justify-center mb-6 mx-auto border ${themeClasses.border}`}
                  whileHover={{ scale: 1.1 }}
                >
                  <feature.icon className={`w-6 h-6 ${themeClasses.text}`} />
                </motion.div>
                <h3 className={`text-xl font-semibold mb-4 ${themeClasses.text}`}>{feature.title}</h3>
                <p className={`${themeClasses.textSecondary} leading-relaxed`}>
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* AI Deliverables Section */}
      <section className={`py-24 ${themeClasses.bg} relative overflow-hidden`}>
        {/* Simple background pattern */}
        <div className="absolute inset-0 z-0 opacity-30">
          <div className="absolute top-1/3 left-1/3 w-72 h-72 bg-gradient-to-r from-indigo-500/10 to-blue-500/10 rounded-full blur-2xl animate-bounce" style={{animationDuration: '8s'}} />
        </div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-20"
          >
            <h2 className={`text-4xl md:text-6xl font-bold ${themeClasses.text} mb-4 leading-tight tracking-tight`}>
              Your data insights,<br />
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
                <span className="font-medium text-sm uppercase tracking-wider">AI Data Analysis</span>
              </div>
              
              <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
                Real-time data insights
              </h3>
              
              <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
                No manual analysis. No complex queries. InsiPredict automatically discovers patterns and generates actionable insights from your data.
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
                    {['⟲', '↶', '↷', '$', '%', '⚡', '⌘', '✓', '⋮'].map((symbol, i) => (
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
                
                <div className={`text-sm ${themeClasses.textMuted} mb-6 font-mono`}>∑ FORECAST (1, B2:B5, A2:A5)</div>
                
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
                        ['1', 'Month', 'Units Sold', 'Revenue ($)', 'COGS ($)'],
                        ['2', 'Apr 2025', '5,083', '609,960', '355,810'],
                        ['3', 'May 2025', '4,925', '591,000', '344,750'],
                        ['4', 'Jun 2025', '4,741', '568,920', '331,870'],
                        ['5', 'Jul 2025', '4,995', '599,400', '349,650']
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
                            <td key={j} className={`p-3 ${i === 0 && (j === 0 || j === 2) ? themeClasses.surfaceSecondary : themeClasses.text}`}>
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
                      <div className={`${themeClasses.button} px-2 py-1 rounded text-xs`}>
                        InsiPredict
                      </div>
                    </div>
                  </div>
                  
                  <div className={`${themeClasses.surfaceSecondary} p-4 rounded-xl border ${themeClasses.border}`}>
                    <p className={`text-sm ${themeClasses.textSecondary}`}>
                      Every insight, a step toward exponential growth. 
                      <span className={`${themeClasses.button} px-1 rounded text-xs ml-1`}>
                        InsiPredict
                      </span> 
                      {" "}turns data into ROI.
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
                <span className="font-medium text-sm uppercase tracking-wider">AI Reports</span>
              </div>
              
              <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
                Comprehensive data reports
              </h3>
              
              <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
                Reports made simple. Any dataset, any question, any format. InsiPredict transforms your data into clear, actionable reports.
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
                <span className="font-medium text-sm uppercase tracking-wider">AI Forecasting</span>
              </div>
              
              <h3 className={`text-3xl md:text-4xl font-bold ${themeClasses.text} mb-6`}>
                Predictive analytics, ready to use
              </h3>
              
              <p className={`text-lg ${themeClasses.textSecondary} leading-relaxed`}>
                InsiPredict generates forecasts and predictions from your historical data with confidence intervals and trend analysis.
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
                <h4 className={`font-bold text-lg mb-6 ${themeClasses.text}`}>Top 5 Enterprise AI Startups to Watch in 2025</h4>
                
                <div className="space-y-4 text-sm">
                  {[
                    { label: 'Comprehensive Analysis' },
                    { label: 'Market Trends' },
                    { label: 'Investment Insights' }
                  ].map((item, i) => (
                    <motion.div 
                      key={item.label}
                      className="flex items-center space-x-3"
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.1 }}
                      viewport={{ once: true }}
                    >
                      <div className={`w-2 h-2 ${themeClasses.text} rounded`}></div>
                      <span className={themeClasses.textSecondary}>{item.label}</span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
              
              <motion.div 
                className={`${themeClasses.surface} rounded-2xl p-8 shadow-2xl transform -rotate-1 hover:rotate-0 transition-all duration-500 mt-4 border ${themeClasses.border}`}
                whileHover={{ scale: 1.02, rotate: 0 }}
              >
                <h4 className={`font-bold text-lg mb-3 ${themeClasses.text}`}>Marketing Budget Proposal — Q2 2025</h4>
                <p className={`text-sm ${themeClasses.textSecondary}`}>Strategic rationale for budget allocation across digital channels...</p>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Integrations Section */}
      <section className={`py-24 ${themeClasses.surface} relative overflow-hidden`}>
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
                Connect to 300+ data sources and analyze everything in one unified platform.
              </p>
              
              <p className={`${themeClasses.text} mb-8 font-medium`}>InsiPredict connects to:</p>
              
              <div className="flex flex-wrap gap-3 mb-10">
                {[
                  { name: 'Gmail' },
                  { name: 'Salesforce' },
                  { name: 'Docs' },
                  { name: 'Slack' },
                  { name: 'Excel' },
                  { name: 'PowerPoint' },
                ].map((integration, index) => (
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
                  [{ delay: 0.5 }, { delay: 0.6 }]
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
                          stiffness: 200
                        }}
                        viewport={{ once: true }}
                        whileHover={{ scale: 1.1, rotate: 3 }}
                      >
                        <div className={`w-8 h-8 ${themeClasses.text} rounded group-hover:rotate-12 transition-transform duration-300`} />
                      </motion.div>
                    ))}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
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
              InsiPredict provides powerful analytics for any business need, from sales forecasting to performance tracking
            </p>
            
            <Button 
              onClick={() => {
                setAuthMode('register');
                setShowAuthModal(true);
              }}
              variant="primary" 
              size="lg"
            >
              Get Started
            </Button>
          </motion.div>
        </div>
      </section>

        </>
      )}

      {/* Authentication Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        initialMode={authMode}
      />

      {/* Footer */}
      <footer className={`${themeClasses.surface} py-20 border-t ${themeClasses.border} relative overflow-hidden`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
            <div className="col-span-1 md:col-span-2">
              <motion.div 
                className="flex items-center space-x-3 mb-8"
                whileHover={{ scale: 1.02 }}
                transition={{ type: "spring", stiffness: 400 }}
              >
                <div className="flex items-center space-x-1">
                  <div className={`w-6 h-6 ${themeClasses.text} rounded`} />
                  <div className={`w-2 h-6 ${themeClasses.text} rounded`} />
                </div>
              </motion.div>
              <p className={`${themeClasses.textSecondary} mb-8 max-w-md leading-relaxed text-lg`}>
                Transform your data into actionable insights with InsiPredict.
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
                {['Home', 'Blog', 'Careers', 'Brand Kit', 'Affiliate'].map((item, index) => (
                  <motion.li 
                    key={item}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <a href="#" className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}>
                      {item}
                    </a>
                  </motion.li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className={`text-lg font-semibold mb-6 ${themeClasses.text}`}>Legal</h3>
              <ul className="space-y-4">
                {['Security', 'Privacy', 'Terms of use'].map((item, index) => (
                  <motion.li 
                    key={item}
                    initial={{ opacity: 0, x: -20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    viewport={{ once: true }}
                  >
                    <a href="#" className={`${themeClasses.textSecondary} hover:${themeClasses.text} transition-colors`}>
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
    </div>
  );
};