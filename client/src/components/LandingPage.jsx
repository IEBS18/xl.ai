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
  onFileUpload,
  uploadProgress = 0
}) => {
  return (
    <>
      <HeroSection
        isConnected={isConnected}
        onSendMessage={onSendMessage}
        onFileUpload={onFileUpload}
        uploadProgress={uploadProgress}
      />
      
      <ConnectorsSection />
      
      <CollaborationSection />
      
      <DeliverablesSection />
      
      <IntegrationsSection />
      
      <CTASection />
      
      <Footer />
    </>
  )
}

export default LandingPage