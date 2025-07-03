"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Button } from "./ui/button"
import { Input } from "./ui/input"
import { Label } from "./ui/label"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs"
import { Progress } from "./ui/progress"
import { Upload, Database, Cloud, FileSpreadsheet, CheckCircle, AlertCircle, FileText, Table } from "lucide-react"
import { useSpreadsheet } from "../lib/spreadsheet-context"

export function DataUploadModal({ open, onOpenChange, onDataUploaded }) {
  const { createSheetsFromFile } = useSpreadsheet()
  const [uploadProgress, setUploadProgress] = useState({
    stage: "idle",
    progress: 0,
    message: "",
  })
  const [fileInfo, setFileInfo] = useState(null)

  const formatFileSize = (bytes) => {
    if (bytes === 0) return "0 Bytes"
    const k = 1024
    const sizes = ["Bytes", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  const getFileType = (file) => {
    if (file.type === "text/csv" || file.name.toLowerCase().endsWith(".csv")) {
      return "CSV"
    } else if (file.name.toLowerCase().endsWith(".xlsx")) {
      return "Excel (XLSX)"
    } else if (file.name.toLowerCase().endsWith(".xls")) {
      return "Excel (XLS)"
    }
    return "Unknown"
  }

  const estimateSheets = (file) => {
    if (file.type === "text/csv" || file.name.toLowerCase().endsWith(".csv")) {
      return 1
    } else if (file.name.toLowerCase().includes(".xlsx") || file.name.toLowerCase().includes(".xls")) {
      return 2 // Simulate multiple sheets for Excel
    }
    return 1
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      const formData = new FormData()
      formData.append("file", file)

      const res = await fetch("http://localhost:5000/api/upload", {
        method: "POST",
        body: formData,
      })

      const result = await res.json()

      if (!result.success) throw new Error(result.message)

      console.log(result.data);

      onDataUploaded?.(result.data)  // 🔁 Send to App.jsx
    } catch (err) {
      alert("Upload failed: " + err.message)
    }
  }


  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Upload className="w-5 h-5" />
            Import Data
          </DialogTitle>
        </DialogHeader>

        {uploadProgress.stage !== "idle" && (
          <div className="mb-4">
            <div className="flex items-center gap-2 mb-2">
              {uploadProgress.stage === "complete" && <CheckCircle className="w-4 h-4 text-green-500" />}
              {uploadProgress.stage === "error" && <AlertCircle className="w-4 h-4 text-red-500" />}
              <span className="text-sm font-medium">{uploadProgress.message}</span>
            </div>
            <Progress value={uploadProgress.progress} className="w-full" />
          </div>
        )}

        {fileInfo && (
          <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="flex items-center gap-3">
              {fileInfo.type === "CSV" ? (
                <FileText className="w-8 h-8 text-green-600" />
              ) : (
                <Table className="w-8 h-8 text-blue-600" />
              )}
              <div className="flex-1">
                <h4 className="font-medium text-sm">{fileInfo.name}</h4>
                <div className="flex items-center gap-4 text-xs text-gray-600 dark:text-gray-400 mt-1">
                  <span>{fileInfo.type}</span>
                  <span>{fileInfo.size}</span>
                  <span>{fileInfo.sheets} sheet(s)</span>
                </div>
              </div>
            </div>
          </div>
        )}

        <Tabs defaultValue="file" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="file" className="flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4" />
              File Upload
            </TabsTrigger>
            <TabsTrigger value="s3" className="flex items-center gap-2">
              <Cloud className="w-4 h-4" />
              Amazon S3
            </TabsTrigger>
            <TabsTrigger value="database" className="flex items-center gap-2">
              <Database className="w-4 h-4" />
              Database
            </TabsTrigger>
          </TabsList>

          <TabsContent value="file" className="space-y-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center"
            >
              <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-semibold mb-2">Upload your file</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Supports CSV, Excel (.xlsx, .xls) files up to 10MB
              </p>
              <Input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
                disabled={uploadProgress.stage === "uploading" || uploadProgress.stage === "processing"}
              />
              <Label htmlFor="file-upload">
                <Button asChild className="cursor-pointer">
                  <span>Choose File</span>
                </Button>
              </Label>
            </motion.div>

            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
              <h4 className="font-medium mb-2 flex items-center gap-2">
                <FileText className="w-4 h-4" />
                File Support:
              </h4>
              <ul className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
                <li>
                  • <strong>CSV files:</strong> Creates 1 sheet with your data
                </li>
                <li>
                  • <strong>Excel files:</strong> Creates multiple sheets (one per Excel sheet)
                </li>
                <li>
                  • <strong>Auto-detection:</strong> Numbers, text, and dates are automatically recognized
                </li>
                <li>
                  • <strong>Performance optimized:</strong> Large files are processed in chunks for smooth experience
                </li>
              </ul>
            </div>
          </TabsContent>

          <TabsContent value="s3" className="space-y-4">
            <div className="text-center p-8 text-gray-500">
              <Cloud className="w-12 h-12 mx-auto mb-4" />
              <p>S3 integration coming soon...</p>
            </div>
          </TabsContent>

          <TabsContent value="database" className="space-y-4">
            <div className="text-center p-8 text-gray-500">
              <Database className="w-12 h-12 mx-auto mb-4" />
              <p>Database integration coming soon...</p>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
