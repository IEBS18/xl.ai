import React from "react"
import MessageTimeline from "./MessageTimeline"
import InputArea from "./InputArea"
import FileInfo from "./FileInfo"
import SampleQuestions from "./SampleQuestions"
import UploadProgress from "./UploadProgress"

const ChatInterface = ({
  messages,
  isAnalyzing,
  isConnected,
  fileUploaded,
  fileInfo,
  onSendMessage,
  messagesEndRef,
  expandedMessages,
  toggleMessageExpansion,
  uploadProgress,
  fileInputRef,
  handleFileUpload,
  triggerFileUpload,
  debugSession,
  manualSessionSync
}) => {
  return (
    <div className="pt-32">
      {/* Messages Timeline */}
      <section className="relative pb-20 overflow-hidden">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <MessageTimeline
            messages={messages}
            isAnalyzing={isAnalyzing}
            expandedMessages={expandedMessages}
            toggleMessageExpansion={toggleMessageExpansion}
            messagesEndRef={messagesEndRef}
          />
        </div>
      </section>

      {/* Sample Questions */}
      {fileUploaded && messages.filter((m) => m.isUser).length === 0 && (
        <SampleQuestions onSelectQuestion={(question) => onSendMessage(question)} />
      )}

      {/* Upload Progress */}
      {uploadProgress > 0 && <UploadProgress progress={uploadProgress} />}

      {/* File Info */}
      {fileUploaded && fileInfo && (
        <FileInfo
          fileInfo={fileInfo}
          onDebug={debugSession}
          onSync={manualSessionSync}
        />
      )}

      {/* Input Area */}
      {fileUploaded && (
        <InputArea
          isConnected={isConnected}
          isAnalyzing={isAnalyzing}
          onSendMessage={onSendMessage}
          onFileUpload={triggerFileUpload}
        />
      )}

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv,.xlsx,.xls"
        onChange={handleFileUpload}
        className="hidden"
      />
    </div>
  )
}

export default ChatInterface