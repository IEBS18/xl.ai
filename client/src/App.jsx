import { useState } from "react"
import { SpreadsheetProvider } from "./lib/spreadsheet-context"
import { SheetsInterface } from "./components/sheets-interface"
import { DataUploadModal } from "./components/data-upload-modal"

function App() {
  const [sheetData, setSheetData] = useState(null)
  const [uploadOpen, setUploadOpen] = useState(true)
  console.log(sheetData);

  return (
    <SpreadsheetProvider initialData={sheetData}>
      <SheetsInterface />
      <DataUploadModal
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        onDataUploaded={(dataFromFlask) => {
          setSheetData(dataFromFlask)
          setUploadOpen(false)
        }}
      />
    </SpreadsheetProvider>
  )
}

export default App
