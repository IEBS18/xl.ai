"use client"

import { createContext, useContext, useState, useCallback, useEffect } from "react"

// Optimized CSV parsing with chunking for large files
const parseCSVAsync = async (csvText) => {
  return new Promise((resolve) => {
    // Use setTimeout to make parsing non-blocking
    setTimeout(() => {
      const lines = csvText.split("\n").filter((line) => line.trim())
      if (lines.length === 0) {
        resolve({ headers: [], data: [] })
        return
      }

      // Parse headers
      const headers = lines[0].split(",").map((h) => h.trim().replace(/"/g, ""))

      // Limit initial data load for performance
      const maxRows = Math.min(lines.length - 1, 1000) // Limit to 1000 rows initially
      const data = []

      // Process data in chunks to avoid blocking
      const chunkSize = 100
      let currentIndex = 1

      const processChunk = () => {
        const endIndex = Math.min(currentIndex + chunkSize, maxRows + 1)

        for (let i = currentIndex; i < endIndex; i++) {
          const line = lines[i]
          if (line && line.trim()) {
            const row = line.split(",").map((cell) => {
              const cleanCell = cell.trim().replace(/"/g, "")
              const numValue = Number.parseFloat(cleanCell)
              return !isNaN(numValue) && cleanCell !== "" ? numValue : cleanCell
            })
            data.push(row)
          }
        }

        currentIndex = endIndex

        if (currentIndex < maxRows + 1) {
          // Continue processing in next tick
          setTimeout(processChunk, 0)
        } else {
          resolve({ headers, data })
        }
      }

      processChunk()
    }, 0)
  })
}

const parseExcelAsync = async (file) => {
  // This is a simplified Excel parser - in production you'd use a library like xlsx
  const text = await file.text()
  const parsed = await parseCSVAsync(text)

  // Simulate multiple sheets for Excel files
  if (file.name.toLowerCase().includes(".xlsx") || file.name.toLowerCase().includes(".xls")) {
    return {
      Sheet1: parsed,
      Sheet2: {
        headers: ["Summary", "Total", "Average"],
        data: [
          ["Total Records", parsed.data.length, "N/A"],
          ["Columns", parsed.headers.length, "N/A"],
        ],
      },
    }
  }

  return { [file.name.replace(/\.[^/.]+$/, "")]: parsed }
}

const SpreadsheetContext = createContext(undefined)

// Helper functions
const getColumnLabel = (index) => {
  let label = ""
  let num = index
  while (num >= 0) {
    label = String.fromCharCode(65 + (num % 26)) + label
    num = Math.floor(num / 26) - 1
  }
  return label
}

const getCellRef = (row, col) => {
  return `${getColumnLabel(col)}${row + 1}`
}

const parseCellRef = (cellRef) => {
  const match = cellRef.match(/^([A-Z]+)(\d+)$/)
  if (!match) throw new Error(`Invalid cell reference: ${cellRef}`)

  const colStr = match[1]
  const rowNum = Number.parseInt(match[2]) - 1

  let col = 0
  for (let i = 0; i < colStr.length; i++) {
    col = col * 26 + (colStr.charCodeAt(i) - 65 + 1)
  }
  col -= 1

  return { row: rowNum, col }
}

// Enhanced formula engine
class FormulaEngine {
  constructor(data, sheet) {
    this.data = data
    this.currentSheet = sheet
  }

  evaluate(formula) {
  try {
    if (!formula.startsWith("=")) return formula;

    let expression = formula.substring(1).toUpperCase();

    // SUM(A1:A10)
    expression = expression.replace(/SUM\(([A-Z]+\d+):([A-Z]+\d+)\)/g, (match, start, end) => {
      return this.calculateSum(start, end).toString();
    });

    // AVG(A1:A10)
    expression = expression.replace(/AVG\(([A-Z]+\d+):([A-Z]+\d+)\)/g, (match, start, end) => {
      return this.calculateAverage(start, end).toString();
    });

    // CORREL(A1:A10,B1:B10)
    expression = expression.replace(/CORREL\(([A-Z]+\d+):([A-Z]+\d+),([A-Z]+\d+):([A-Z]+\d+)\)/g,
      (match, start1, end1, start2, end2) => {
        return this.calculateCorrelation(start1, end1, start2, end2).toString();
      });

    // Replace all cell refs with values
    expression = expression.replace(/[A-Z]+\d+/g, (cellRef) => {
      const cellValue = this.data[this.currentSheet]?.data[cellRef];
      const value = cellValue?.value ?? 0;
      return typeof value === "number" ? value.toString() : "0";
    });

    const result = this.safeEval(expression);
    return isNaN(result) ? "#ERROR!" : result;
  } catch (error) {
    console.error("Formula evaluation error:", error);
    return "#ERROR!";
  }
}


  calculateSum(startCell, endCell) {
    const range = this.getCellRange(startCell, endCell)
    let sum = 0
    range.forEach((cellRef) => {
      const cellValue = this.data[this.currentSheet]?.data[cellRef]
      if (cellValue && typeof cellValue.value === "number") {
        sum += cellValue.value
      }
    })
    return sum
  }

  calculateAverage(startCell, endCell) {
    const range = this.getCellRange(startCell, endCell)
    let sum = 0
    let count = 0
    range.forEach((cellRef) => {
      const cellValue = this.data[this.currentSheet]?.data[cellRef]
      if (cellValue && typeof cellValue.value === "number") {
        sum += cellValue.value
        count++
      }
    })
    return count > 0 ? sum / count : 0
  }

  calculateCorrelation(startCell1, endCell1, startCell2, endCell2) {
    const range1 = this.getCellRange(startCell1, endCell1)
    const range2 = this.getCellRange(startCell2, endCell2)

    const values1 = []
    const values2 = []

    range1.forEach((cellRef) => {
      const cellValue = this.data[this.currentSheet]?.data[cellRef]
      if (cellValue && typeof cellValue.value === "number") {
        values1.push(cellValue.value)
      }
    })

    range2.forEach((cellRef) => {
      const cellValue = this.data[this.currentSheet]?.data[cellRef]
      if (cellValue && typeof cellValue.value === "number") {
        values2.push(cellValue.value)
      }
    })

    if (values1.length !== values2.length || values1.length === 0) return 0

    const mean1 = values1.reduce((a, b) => a + b) / values1.length
    const mean2 = values2.reduce((a, b) => a + b) / values2.length

    let numerator = 0
    let sum1 = 0
    let sum2 = 0

    for (let i = 0; i < values1.length; i++) {
      const diff1 = values1[i] - mean1
      const diff2 = values2[i] - mean2
      numerator += diff1 * diff2
      sum1 += diff1 * diff1
      sum2 += diff2 * diff2
    }

    const denominator = Math.sqrt(sum1 * sum2)
    return denominator === 0 ? 0 : numerator / denominator
  }

  getCellRange(startCell, endCell) {
    const start = parseCellRef(startCell)
    const end = parseCellRef(endCell)
    const range = []

    for (let row = start.row; row <= end.row; row++) {
      for (let col = start.col; col <= end.col; col++) {
        range.push(getCellRef(row, col))
      }
    }
    return range
  }

  safeEval(expression) {
    if (!/^[0-9+\-*/().\s]+$/.test(expression)) {
      throw new Error("Invalid expression")
    }
    return Function('"use strict"; return (' + expression + ")")()
  }
}

// Initialize with financial data
const initializeData = () => {
  const btcEthData = {}

  // BTC USD 2014-2024 data
  const btcHeaders = ["Date", "Close"]
  const btcData = [
    ["09/18/2014", 424.44],
    ["09/19/2014", 394.79],
    ["09/20/2014", 408.9],
    ["09/21/2014", 398.82],
    ["09/22/2014", 400.15],
    ["09/23/2014", 435.79],
    ["09/24/2014", 423.2],
    ["09/25/2014", 411.57],
    ["09/26/2014", 404.42],
    ["09/27/2014", 399.52],
    ["09/28/2014", 377.16],
    ["09/29/2014", 375.47],
    ["09/30/2014", 386.94],
    ["10/01/2014", 383.61],
    ["10/02/2014", 375.07],
    ["10/03/2014", 359.51],
    ["10/04/2014", 328.87],
    ["10/05/2014", 320.51],
    ["10/06/2014", 330.06],
    ["10/07/2014", 336.19],
    ["10/08/2014", 352.34],
    ["10/09/2014", 365.03],
    ["10/10/2014", 361.56],
    ["10/11/2014", 362.3],
    ["10/12/2014", 378.55],
    ["10/13/2014", 390.41],
    ["10/14/2014", 400.87],
    ["10/15/2014", 394.77],
    ["10/16/2014", 382.56],
    ["10/17/2014", 383.76],
    ["10/18/2014", 391.44],
    ["10/19/2014", 389.55],
  ]

  // ETH USD 2017-2024 data
  const ethHeaders = ["Date", "Close"]
  const ethData = [
    ["11/10/2017", 299.25],
    ["11/11/2017", 314.68],
    ["11/12/2017", 307.91],
    ["11/13/2017", 316.72],
    ["11/14/2017", 337.83],
    ["11/15/2017", 333.36],
    ["11/16/2017", 330.92],
    ["11/17/2017", 332.39],
    ["11/18/2017", 347.61],
    ["11/19/2017", 354.39],
    ["11/20/2017", 366.73],
    ["11/21/2017", 360.4],
    ["11/22/2017", 380.65],
    ["11/23/2017", 410.17],
    ["11/24/2017", 474.91],
    ["11/25/2017", 466.28],
    ["11/26/2017", 471.33],
    ["11/27/2017", 480.96],
    ["11/28/2017", 472.9],
    ["11/29/2017", 427.52],
    ["11/30/2017", 440.11],
    ["12/01/2017", 466.54],
    ["12/02/2017", 463.45],
    ["12/03/2017", 465.85],
    ["12/04/2017", 470.2],
    ["12/05/2017", 463.28],
    ["12/06/2017", 428.59],
    ["12/07/2017", 434.41],
    ["12/08/2017", 456.03],
    ["12/09/2017", 473.5],
    ["12/10/2017", 441.72],
    ["12/11/2017", 515.14],
  ]

  // Add BTC data
  btcHeaders.forEach((header, col) => {
    btcEthData[getCellRef(0, col)] = { value: header, type: "text" }
  })

  btcData.forEach((row, rowIndex) => {
    row.forEach((cell, col) => {
      btcEthData[getCellRef(rowIndex + 1, col)] = {
        value: cell,
        type: typeof cell === "number" ? "number" : "text",
      }
    })
  })

  // Add ETH data starting from column D
  ethHeaders.forEach((header, col) => {
    btcEthData[getCellRef(0, col + 3)] = { value: header, type: "text" }
  })

  ethData.forEach((row, rowIndex) => {
    row.forEach((cell, col) => {
      btcEthData[getCellRef(rowIndex + 1, col + 3)] = {
        value: cell,
        type: typeof cell === "number" ? "number" : "text",
      }
    })
  })

  return {
    "BTC vs ETH": { data: btcEthData, rows: 50, cols: 20, charts: [] },
  }
}

export function SpreadsheetProvider({ children, initialData = null }) {
  // const [data, setData] = useState(initialData || {})
  const [activeSheet, setActiveSheet] = useState(
    initialData ? Object.keys(initialData)[0] : null
  )
  const [data, setData] = useState(initialData || {})
  useEffect(() => {
    if (initialData) {
      setData(initialData)
      setActiveSheet(Object.keys(initialData)[0])
    }
  }, [initialData])


  console.log(data, activeSheet);

  const addSheet = (name) => {
    setData((prev) => ({
      ...prev,
      [name]: {
        data: {
          A1: { value: "Column A", type: "text" },
          B1: { value: "Column B", type: "text" },
          C1: { value: "Column C", type: "text" },
        },
        rows: 20,
        cols: 10,
        charts: [],
      },
    }))
  }

  const renameSheet = (oldName, newName) => {
    if (oldName === newName || data[newName]) return

    setData((prev) => {
      const newData = { ...prev }
      newData[newName] = newData[oldName]
      delete newData[oldName]
      return newData
    })

    if (activeSheet === oldName) {
      setActiveSheet(newName)
    }
  }

  const updateCell = useCallback((sheet, cellRef, value, formula, type = "text", imageUrl) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      let finalType = type
      let finalValue = value
      let finalImageUrl = imageUrl

      if (formula && formula.startsWith("=")) {
        finalType = "formula"
        const engine = new FormulaEngine(newData, sheet)
        finalValue = engine.evaluate(formula)
      } else if (typeof value === "string" && isImageUrl(value)) {
        finalType = "image"
        finalImageUrl = value
        finalValue = value
      } else if (typeof value === "string" && !isNaN(Number.parseFloat(value)) && isFinite(Number.parseFloat(value))) {
        finalType = "number"
        finalValue = Number.parseFloat(value)
      }

      newData[sheet] = {
        ...newData[sheet],
        data: {
          ...newData[sheet].data,
          [cellRef]: {
            value: finalValue,
            formula,
            type: finalType,
            imageUrl: finalImageUrl,
          },
        },
      }

      return newData
    })
  }, [])

  const getCellValue = (sheet, cellRef) => {
    return data[sheet]?.data[cellRef]
  }

  const evaluateFormula = useCallback(
    (formula, sheet) => {
      const engine = new FormulaEngine(data, sheet)
      return engine.evaluate(formula)
    },
    [data],
  )

  const recalculateSheet = useCallback(
    (sheet) => {
      setData((prev) => {
        const newData = { ...prev }
        const sheetData = newData[sheet]
        if (!sheetData) return prev

        const engine = new FormulaEngine(newData, sheet)

        Object.entries(sheetData.data).forEach(([cellRef, cellValue]) => {
          if (cellValue.type === "formula" && cellValue.formula) {
            const newValue = engine.evaluate(cellValue.formula)
            newData[sheet].data[cellRef] = {
              ...cellValue,
              value: newValue,
            }
          }
        })

        return newData
      })
    },
    [data],
  )

  const addChart = useCallback((sheet, chartId, title, imageUrl) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      const existingChartIndex = newData[sheet].charts.findIndex((chart) => chart.id === chartId)

      const newChart = {
        id: chartId,
        title,
        imageUrl,
        position: { x: 300 + newData[sheet].charts.length * 50, y: 150 + newData[sheet].charts.length * 50 },
        size: { width: 400, height: 300 },
        isMinimized: false,
        createdAt: new Date(),
      }

      if (existingChartIndex >= 0) {
        // Update existing chart
        newData[sheet].charts[existingChartIndex] = {
          ...newData[sheet].charts[existingChartIndex],
          ...newChart,
        }
      } else {
        // Add new chart
        newData[sheet].charts.push(newChart)
      }

      return newData
    })
  }, [])

  const updateChart = useCallback((sheet, chartId, updates) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      const chartIndex = newData[sheet].charts.findIndex((chart) => chart.id === chartId)
      if (chartIndex >= 0) {
        newData[sheet].charts[chartIndex] = {
          ...newData[sheet].charts[chartIndex],
          ...updates,
        }
      }

      return newData
    })
  }, [])

  const removeChart = useCallback((sheet, chartId) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      newData[sheet].charts = newData[sheet].charts.filter((chart) => chart.id !== chartId)
      return newData
    })
  }, [])

  const getCharts = useCallback(
    (sheet) => {
      return data[sheet]?.charts || []
    },
    [data],
  )

  const isImageUrl = (url) => {
    if (typeof url !== "string") return false
    return (
      (url.startsWith("http") || url.startsWith("data:image")) &&
      (url.includes(".jpg") ||
        url.includes(".jpeg") ||
        url.includes(".png") ||
        url.includes(".gif") ||
        url.includes(".svg") ||
        url.includes(".webp") ||
        url.includes("placeholder") ||
        url.includes("picsum"))
    )
  }

  const addRow = (sheet, index) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      const sheetData = newData[sheet]
      const newSheetData = {}

      Object.entries(sheetData.data).forEach(([cellRef, cellValue]) => {
        const { row, col } = parseCellRef(cellRef)
        if (row >= index) {
          const newCellRef = getCellRef(row + 1, col)
          newSheetData[newCellRef] = cellValue
        } else {
          newSheetData[cellRef] = cellValue
        }
      })

      newData[sheet] = {
        ...sheetData,
        data: newSheetData,
        rows: sheetData.rows + 1,
      }

      return newData
    })
  }

  const addColumn = (sheet, index) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      const sheetData = newData[sheet]
      const newSheetData = {}

      Object.entries(sheetData.data).forEach(([cellRef, cellValue]) => {
        const { row, col } = parseCellRef(cellRef)
        if (col >= index) {
          const newCellRef = getCellRef(row, col + 1)
          newSheetData[newCellRef] = cellValue
        } else {
          newSheetData[cellRef] = cellValue
        }
      })

      newData[sheet] = {
        ...sheetData,
        data: newSheetData,
        cols: sheetData.cols + 1,
      }

      return newData
    })
  }

  const deleteRow = (sheet, index) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      const sheetData = newData[sheet]
      const newSheetData = {}

      Object.entries(sheetData.data).forEach(([cellRef, cellValue]) => {
        const { row, col } = parseCellRef(cellRef)
        if (row < index) {
          newSheetData[cellRef] = cellValue
        } else if (row > index) {
          const newCellRef = getCellRef(row - 1, col)
          newSheetData[newCellRef] = cellValue
        }
      })

      newData[sheet] = {
        ...sheetData,
        data: newSheetData,
        rows: Math.max(1, sheetData.rows - 1),
      }

      return newData
    })
  }

  const deleteColumn = (sheet, index) => {
    setData((prev) => {
      const newData = { ...prev }
      if (!newData[sheet]) return prev

      const sheetData = newData[sheet]
      const newSheetData = {}

      Object.entries(sheetData.data).forEach(([cellRef, cellValue]) => {
        const { row, col } = parseCellRef(cellRef)
        if (col < index) {
          newSheetData[cellRef] = cellValue
        } else if (col > index) {
          const newCellRef = getCellRef(row, col - 1)
          newSheetData[newCellRef] = cellValue
        }
      })

      newData[sheet] = {
        ...sheetData,
        data: newSheetData,
        cols: Math.max(1, sheetData.cols - 1),
      }

      return newData
    })
  }

  const createSheetsFromFile = useCallback(async (file, onProgress) => {
    try {
      onProgress?.(10, "Reading file...")

      let sheetsData

      if (file.type === "text/csv" || file.name.toLowerCase().endsWith(".csv")) {
        onProgress?.(30, "Parsing CSV data...")
        const text = await file.text()
        const parsed = await parseCSVAsync(text)
        const sheetName = file.name.replace(/\.[^/.]+$/, "") || "CSV Data"
        sheetsData = { [sheetName]: parsed }
      } else {
        onProgress?.(30, "Parsing Excel data...")
        sheetsData = await parseExcelAsync(file)
      }

      onProgress?.(60, "Creating sheets...")

      // Create new data structure
      const newData = {}

      // Process sheets one by one to avoid blocking
      const sheetEntries = Object.entries(sheetsData)
      for (let i = 0; i < sheetEntries.length; i++) {
        const [sheetName, sheetContent] = sheetEntries[i]

        onProgress?.(60 + (i / sheetEntries.length) * 30, `Creating sheet: ${sheetName}`)

        // Use setTimeout to yield control
        await new Promise((resolve) => setTimeout(resolve, 0))

        const sheetData = {}

        // Add headers
        sheetContent.headers.forEach((header, col) => {
          sheetData[getCellRef(0, col)] = { value: header, type: "text" }
        })

        // Add data rows in chunks
        const chunkSize = 50
        for (let rowStart = 0; rowStart < sheetContent.data.length; rowStart += chunkSize) {
          const rowEnd = Math.min(rowStart + chunkSize, sheetContent.data.length)

          for (let rowIndex = rowStart; rowIndex < rowEnd; rowIndex++) {
            const row = sheetContent.data[rowIndex]
            row.forEach((cell, col) => {
              const cellType = typeof cell === "number" ? "number" : "text"
              sheetData[getCellRef(rowIndex + 1, col)] = { value: cell, type: cellType }
            })
          }

          // Yield control after each chunk
          await new Promise((resolve) => setTimeout(resolve, 0))
        }

        newData[sheetName] = {
          data: sheetData,
          rows: Math.max(50, sheetContent.data.length + 10),
          cols: Math.max(20, sheetContent.headers.length + 5),
          charts: [],
        }
      }

      onProgress?.(95, "Finalizing...")

      // Update state in next tick to avoid blocking
      await new Promise((resolve) =>
        setTimeout(() => {
          setData(newData)

          // Set the first sheet as active
          const firstSheetName = Object.keys(newData)[0]
          setActiveSheet(firstSheetName)

          resolve(undefined)
        }, 0),
      )

      onProgress?.(100, "Complete!")

      return {
        success: true,
        sheets: Object.keys(newData),
        message: `Successfully loaded ${Object.keys(newData).length} sheet(s)`,
      }
    } catch (error) {
      console.error("File parsing error:", error)
      return { success: false, message: "Failed to parse file. Please check the file format." }
    }
  }, [])

  return (
    <SpreadsheetContext.Provider
      value={{
        data,
        activeSheet,
        setData,
        setActiveSheet,
        addSheet,
        renameSheet,
        updateCell,
        getCellValue,
        addRow,
        addColumn,
        deleteRow,
        deleteColumn,
        evaluateFormula,
        recalculateSheet,
        addChart,
        updateChart,
        removeChart,
        getCharts,
        createSheetsFromFile,
      }}
    >
      {children}
    </SpreadsheetContext.Provider>
  )
}

export const useSpreadsheet = () => {
  const context = useContext(SpreadsheetContext)
  if (!context) {
    throw new Error("useSpreadsheet must be used within SpreadsheetProvider")
  }
  return context
}

export { getCellRef, parseCellRef, getColumnLabel }
