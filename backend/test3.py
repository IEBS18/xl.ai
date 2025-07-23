import requests

html_content = """
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Intelligence Analysis Strategic Outlook 2025-2026</title>
    <style>
        body {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            color: #2d3748;
            font-family: 'Inter', 'Roboto', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.9);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            padding: 40px;
        }

        h1, h2, h3 {
            color: #2d3748;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 20px;
            text-align: center;
        }

        h2 {
            font-size: 2em;
            margin-top: 20px;
        }

        h3 {
            font-size: 1.5em;
            margin-top: 15px;
            margin-bottom: 10px;
        }

        p {
            margin: 10px 0;
        }

        .table-of-contents {
            margin: 30px 0;
            padding: 15px;
            background: #f0f4f8;
            border: 1px solid #d1e0e5;
            border-radius: 8px;
        }

        .toc-item {
            margin-bottom: 10px;
        }

        .chart-container {
            background: #ffffff;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
            border: 1px solid #e9ecef;
        }

        .chart-image {
            width: 100%;
            height: auto;
            max-width: 800px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        @media print {
            body {
                color: #000;
            }

            .container {
                background: none;
                box-shadow: none;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Business Intelligence Analysis Strategic Outlook 2025-2026</h1>

        <div class="table-of-contents">
            <h2>Table of Contents</h2>
            <div class="toc-item"><a href="#executive-summary">Executive Summary</a></div>
            <div class="toc-item"><a href="#background-objectives">Background & Objectives</a></div>
            <div class="toc-item"><a href="#data-sources-methodology">Data Sources & Methodology</a></div>
            <div class="toc-item"><a href="#market-trend-analysis">Market & Trend Analysis</a></div>
            <div class="toc-item"><a href="#analysis-results">Analysis Results</a></div>
            <div class="toc-item"><a href="#strategic-implications">Strategic Implications</a></div>
            <div class="toc-item"><a href="#recommendations-implementation-roadmap">Recommendations & Implementation Roadmap</a></div>
            <div class="toc-item"><a href="#risks-mitigations">Risks & Mitigations</a></div>
            <div class="toc-item"><a href="#appendices">Appendices</a></div>
        </div>

        <h2 id="executive-summary">Executive Summary</h2>
        <p>This report presents an extensive analysis of the data gleaned from 55,500 records over a five-year span, assessing various dimensions critical to the management of hospital resources and patient care in our healthcare system. Key findings include insights into patient demographics, billing practices, and trends in length of stay that inform strategic planning moving forward into 2025-2026. Strategic recommendations based on these insights are framed to enhance service delivery and optimize financial performance.</p>
        <p>The analysis indicates a significant correlation between demographic factors such as age and the length of stay, with broader implications for staffing and resource allocation. Various recommendations are posited to mitigate risks associated with patient care and billing inaccuracies.</p>

        <h2 id="background-objectives">Background & Objectives</h2>
        <p>In the realm of healthcare services, effective management of resources directly contributes to improved patient outcomes and operational efficiency. This report aims to elucidate patterns and trends derived from comprehensive datasets to heighten the understanding of patient demographics, financial dynamics, and healthcare delivery mechanisms.</p>
        
        <h2 id="data-sources-methodology">Data Sources & Methodology</h2>
        <p>The primary dataset comprises 55,500 records captured from May 2019 to May 2024, detailing attributes such as patient demographics, billing amounts, insurance providers, and medical conditions. Data were analyzed using statistical tools to derive insights into patient behaviors and outcomes. The methodology encompassed descriptive statistics and trend analysis.</p>

        <h2 id="market-trend-analysis">Market & Trend Analysis</h2>
        <p>Analysis reveals that the average age of patients admitted is 51.5 years, highlighting a substantial senior demographic that requires targeted healthcare strategies. The average billing amount stands at approximately $25,540, with variability dependent on factors such as length of stay and admission type.</p>
        
        <div class="chart-container">
            <h3>Length of Stay by Age Group</h3>
            <img class="chart-image" src="https://datastorageblobieb.blob.core.windows.net/insi-predict-dev/analysis_20250723_123734/images/plot_124558_1.png" alt="Length of Stay by Age Group"/>
            <p><strong>Figure 1:</strong> Length of Stay categorized by Age Group illustrates the trends observed across different age demographics.</p>
        </div>

        <h2 id="analysis-results">Analysis Results</h2>
        <p>The key findings from the analysis provide clarity on trends impacting hospital management. Notably, there is an upward trend in billing amounts correlated with length of stay, highlighting the need for effective billing processes. Additionally, categorical variables such as 'Medical Condition' reveal varying lengths of stay, suggesting that particular conditions significantly impact resource allocation.</p>
        
        <h2 id="strategic-implications">Strategic Implications</h2>
        <p>The insights derived from the data compel a strategic refocus on resource allocation, staffing, and financial management. The distinct relationship between demographics and healthcare needs necessitates a tailored approach to patient care that accommodates the variability in requirements based on age and medical conditions.</p>
        
        <h2 id="recommendations-implementation-roadmap">Recommendations & Implementation Roadmap</h2>
        <p>To address identified areas for improvement, the following recommendations are proposed:</p>
        <ol>
            <li>Implement age-specific care plans to enhance patient outcomes.</li>
            <li>Optimize billing procedures by leveraging real-time data analytics tools.</li>
            <li>Enhance workforce management to address the staffing needs highlighted by patient demographics.</li>
        </ol>

        <h2 id="risks-mitigations">Risks & Mitigations</h2>
        <p>Potential risks associated with executing the aforementioned recommendations include resistance to change and adoption challenges among staff. To mitigate these risks, it is advisable to conduct training sessions and stakeholder engagement to foster a culture of adaptability.</p>

        <h2 id="appendices">Appendices</h2>
        <p>Additional information, including detailed statistical models and further technical specifications regarding data analysis methodologies, are documented in the appendices.</p>
    </div>
</body>
</html>
```
"""

# Save the HTML to a file first
with open("document.html", "w", encoding="utf-8") as f:
    f.write(html_content)

# Prepare the multipart/form-data payload
with open("document.html", "rb") as html_file:
    files = {
        "files": ("index.html", html_file, "text/html"),
    }

    response = requests.post(
        "http://localhost:3000/forms/chromium/convert/html",
        files=files,
    )

# Save the resulting PDF
if response.status_code == 200:
    with open("output.pdf", "wb") as f:
        f.write(response.content)
    print("PDF saved as output.pdf")
else:
    print(f"Error: {response.status_code}\n{response.text}")
