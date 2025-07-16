import React from "react"
import HeroSection from "../sections/HeroSection"
import ConnectorsSection from "../sections/ConnectorsSection"
import CollaborationSection from "../sections/CollaborationSection"
import DeliverablesSection from "../sections/DeliverablesSection"
import IntegrationsSection from "../sections/IntegrationsSection"
import CTASection from "../sections/CTASection"
import Footer from "../sections/Footer"

const LandingPage = ({ 
  isConnected, 
  onSendMessage, 
  fileInputRef, 
  handleFileUpload, 
  triggerFileUpload 
}) => {
  return (
    <>
      <HeroSection
        isConnected={isConnected}
        onSendMessage={onSendMessage}
        onFileUpload={triggerFileUpload}
      />
      
      <ConnectorsSection />
      
      <CollaborationSection />
      
      <DeliverablesSection />
      
      <IntegrationsSection />
      
      <CTASection />
      
      <Footer />

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={handleFileUpload}
        className="hidden"
      />
    </>
  )
}

export default LandingPage