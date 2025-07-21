import { useState, useRef } from "react";
import { MDXEditor } from "@mdxeditor/editor";
import { 
  headingsPlugin, 
  listsPlugin, 
  quotePlugin, 
  thematicBreakPlugin,
  markdownShortcutPlugin,
  linkPlugin,
  linkDialogPlugin,
  imagePlugin,
  tablePlugin,
  codeBlockPlugin,
  codeMirrorPlugin,
  diffSourcePlugin,
  frontmatterPlugin,
  toolbarPlugin,
  UndoRedo,
  BoldItalicUnderlineToggles,
  CodeToggle,
  CreateLink,
  InsertImage,
  InsertTable,
  InsertThematicBreak,
  ListsToggle,
  BlockTypeSelect,
  Separator
} from "@mdxeditor/editor";
import html2pdf from "html2pdf.js";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

// Import MDXEditor CSS styles
import "@mdxeditor/editor/style.css";

export default function RichTextEditorWithDownload({ 
  content = `# Strategic Analysis Report: Sales Performance by Category

---

## 1. Executive Summary

This comprehensive analysis examines the sales performance across different product categories, providing insights into market trends, revenue generation, and strategic recommendations for business growth.

## 2. Key Findings

Our analysis reveals significant variations in performance across categories, with **Technology** and **Electronics** leading in revenue generation while showing opportunities for optimization in *Customer Service* and *Marketing* segments.

## 3. Recommendations

Based on the data analysis, we recommend focusing on high-performing categories while implementing targeted strategies to improve underperforming segments.
`, 
  filename = "strategic-report.pdf" 
}) {
  const [isDownloading, setIsDownloading] = useState(false);
  // Convert HTML to markdown if needed
  const htmlToMarkdown = (html) => {
    return html
      .replace(/<h1[^>]*>(.*?)<\/h1>/g, '# $1')
      .replace(/<h2[^>]*>(.*?)<\/h2>/g, '## $1')
      .replace(/<h3[^>]*>(.*?)<\/h3>/g, '### $1')
      .replace(/<p[^>]*>(.*?)<\/p>/g, '$1\n\n')
      .replace(/<br\s*\/?>/g, '\n')
      .replace(/<\/?\w+[^>]*>/g, '')
      .replace(/\n\s*\n\s*\n/g, '\n\n')
      .trim();
  };

  const initialContent = content.includes('<') ? htmlToMarkdown(content) : content;
  const [markdownContent, setMarkdownContent] = useState(initialContent);
  const reportRef = useRef(null);

  const downloadPDF = async () => {
    if (!reportRef.current) return;
    
    setIsDownloading(true);
    
    try {
      const opt = {
        margin: [0.5, 0.5, 0.5, 0.5],
        filename: filename,
        image: { type: "jpeg", quality: 0.98 },
        html2canvas: { 
          scale: 2,
          useCORS: true,
          letterRendering: true,
          backgroundColor: '#ffffff'
        },
        jsPDF: { 
          unit: "in", 
          format: "a4", 
          orientation: "portrait",
          putOnlyUsedFonts: true,
          floatPrecision: 16
        },
      };
      
      await html2pdf().set(opt).from(reportRef.current).save();
    } catch (error) {
      console.error('PDF generation failed:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  // Convert markdown to HTML for PDF preview
  const markdownToHtml = (markdown) => {
    // Simple markdown to HTML conversion for preview
    return markdown
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
      .replace(/^- (.*$)/gm, '<li>$1</li>')
      .replace(/^(\d+)\. (.*$)/gm, '<li>$1. $2</li>')
      .replace(/^---$/gm, '<hr>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/^(?!<[h|l|b])/gm, '<p>')
      .replace(/$/gm, '</p>')
      .replace(/<p><\/p>/g, '')
      .replace(/<p>(<h[1-6]>)/g, '$1')
      .replace(/(<\/h[1-6]>)<\/p>/g, '$1')
      .replace(/<p>(<hr>)<\/p>/g, '$1')
      .replace(/<p>(<blockquote>.*?<\/blockquote>)<\/p>/g, '$1');
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Main Editor Container */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          {/* Editor Header */}
          <div className="flex items-center justify-between p-2 border-b border-gray-700">
            <h2 className="text-xs font-semibold text-white"></h2>
            <Button 
              onClick={downloadPDF}
              disabled={isDownloading}
              className="bg-black-600 hover:bg-black-800 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
            >
              <Download className="w-4 h-4" />
              {/* {isDownloading ? 'Generating PDF...' : 'Download PDF'} */}
            </Button>
          </div>

          {/* MDX Editor */}
          <div className="bg-white">
            {initialContent ? (
              <MDXEditor
                key={initialContent} // Force re-render when content changes
                markdown={markdownContent}
                onChange={setMarkdownContent}
                plugins={[
                  headingsPlugin({
                    allowedHeadingLevels: [1, 2, 3, 4, 5, 6]
                  }),
                  listsPlugin(),
                  quotePlugin(),
                  thematicBreakPlugin(),
                  markdownShortcutPlugin(),
                  linkPlugin(),
                  linkDialogPlugin(),
                  imagePlugin(),
                  tablePlugin(),
                  codeBlockPlugin({
                    defaultCodeBlockLanguage: 'javascript'
                  }),
                  codeMirrorPlugin({
                    codeBlockLanguages: {
                      javascript: 'JavaScript',
                      python: 'Python',
                      css: 'CSS',
                      html: 'HTML',
                      markdown: 'Markdown'
                    }
                  }),
                  diffSourcePlugin({ 
                    viewMode: 'rich-text',
                    diffMarkdown: initialContent
                  }),
                  frontmatterPlugin(),
                  toolbarPlugin({
                    toolbarContents: () => (
                      <>
                        <UndoRedo />
                        <Separator />
                        <BoldItalicUnderlineToggles />
                        <CodeToggle />
                        <Separator />
                        <BlockTypeSelect />
                        <Separator />
                        <CreateLink />
                        <InsertImage />
                        <Separator />
                        <ListsToggle />
                        <Separator />
                        <InsertTable />
                        <InsertThematicBreak />
                      </>
                    )
                  })
                ]}
                contentEditableClassName="prose prose-slate max-w-none min-h-[500px] p-6"
              />
            ) : (
              <div className="p-6 text-gray-500">
                Loading editor...
              </div>
            )}
          </div>
        </div>

        {/* Hidden PDF Preview */}
        <div 
          ref={reportRef}
          className="hidden"
          style={{ 
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            lineHeight: '1.6',
            backgroundColor: '#ffffff',
            color: '#000000',
            padding: '40px',
            maxWidth: '210mm',
            margin: '0 auto'
          }}
        >
          <div 
            dangerouslySetInnerHTML={{ __html: markdownToHtml(markdownContent) }}
            style={{
              fontSize: '14px',
              lineHeight: '1.6'
            }}
          />
        </div>

        {/* Markdown Preview */}
        {/* <div className="mt-6 bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold text-white">Markdown Preview</h3>
          </div>
          <div className="p-6 bg-gray-900 text-gray-300">
            <pre className="whitespace-pre-wrap text-sm font-mono">
              {markdownContent}
            </pre>
          </div>
        </div> */}
      </div>
    </div>
  );
}