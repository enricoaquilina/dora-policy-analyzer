# DORA Policy Analyzer Agent - Quick Start Guide

## 🚀 Run the MVP Demo in 3 Minutes

This guide gets you from zero to running DORA compliance analysis demos in under 3 minutes.

### Prerequisites

```bash
# Python 3.8+ required
python --version

# Git clone (if needed)
cd Downloads/DCR/policy-analyzer-agent
```

### Step 1: Install Dependencies (60 seconds)

```bash
# Install core requirements
pip install -r requirements.txt

# Install demo dependencies
pip install rich

# Download NLP models
python -m spacy download en_core_web_sm
```

### Step 2: Configure AI Models (30 seconds)

Choose **ONE** of these options:

**Option A: Anthropic Claude (Recommended)**
```bash
export ANTHROPIC_API_KEY="your-claude-api-key-here"
```

**Option B: OpenAI GPT-4**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Option C: Demo Mode (No API Keys)**
```bash
# Uses fallback logic for demonstration
# Limited AI capabilities but functional demo
```

### Step 3: Run the Demo (30 seconds)

```bash
# Launch interactive demo
python demo.py
```

**You'll see this menu:**
```
Demo Scenarios Available:
1. 🚀 Full End-to-End Analysis (CIO Executive Demo)
2. 📊 Executive Dashboard View  
3. 🔍 Detailed Gap Analysis
4. 🔧 Technical Architecture Overview
5. ❌ Exit Demo
```

## 📊 Expected Demo Output

### Executive Summary
```
🎯 OVERALL COMPLIANCE: 73.2% (AMBER)

Document: ICT Risk Management Policy v2.1
Analysis Date: 2025-01-23 14:30:15
Processing Time: 24.7 seconds

Requirements Assessed: 25
Fully Compliant: 15
Critical Gaps: 2
```

### Pillar Breakdown
```
1. ICT Risk Management & Governance    89.3%  🟢 GREEN
2. ICT-Related Incident Management     45.8%  🔴 RED
3. Digital Operational Resilience      72.1%  🟡 AMBER
4. ICT Third-Party Risk Management     51.2%  🔴 RED
5. Information & Intelligence Sharing  91.7%  🟢 GREEN
```

### Critical Gaps
```
[CRITICAL] Article 17.1 - Missing incident classification framework
[CRITICAL] Article 17.3 - Major incident escalation protocols undefined
[HIGH] Article 28.3 - Concentration risk assessment incomplete
```

## 🎯 Real Document Analysis

To analyze your own policy documents:

```python
# Quick analysis script
from src.dora_analyzer import DORAComplianceAnalyzer
import asyncio

async def analyze_my_policy():
    analyzer = DORAComplianceAnalyzer()
    report = await analyzer.analyze_document("path/to/your/policy.pdf")
    
    print(f"Compliance: {report.compliance_percentage:.1f}%")
    print(f"Critical Gaps: {report.critical_gaps}")
    print(f"RAG Status: {report.overall_rag_status.value}")

# Run analysis
asyncio.run(analyze_my_policy())
```

## 📈 Component Testing

Test individual components:

### Document Processing
```bash
python src/document_processor.py path/to/document.pdf --output processed.json
```

### Text Extraction  
```bash
python src/text_extractor.py processed.json --output extracted.json
```

### DORA Analysis
```bash
python src/dora_analyzer.py path/to/document.pdf --output report.json
```

## 🔧 Troubleshooting

### Common Issues

**1. Missing Dependencies**
```bash
# Install additional packages if needed
pip install PyMuPDF python-docx pytesseract
pip install nltk spacy transformers torch
pip install anthropic openai sentence-transformers
```

**2. spaCy Model Missing**
```bash
python -m spacy download en_core_web_sm
```

**3. API Key Errors**
```bash
# Check environment variables
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Or set in Python
import os
os.environ['ANTHROPIC_API_KEY'] = 'your-key-here'
```

**4. OCR Dependencies (Optional)**
```bash
# Install tesseract for OCR (Ubuntu/Debian)
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Performance Tips

**Memory Usage:**
- Minimum: 4GB RAM
- Recommended: 8GB+ RAM for optimal performance

**Processing Speed:**
- PDF documents: ~2-5 seconds per page
- DOCX documents: ~1-2 seconds per page  
- AI analysis: ~15-30 seconds (depends on API response time)

**File Size Limits:**
- Maximum file size: 100MB
- Recommended: <50MB for optimal performance

## 🌐 Integration Examples

### REST API Usage (Future)
```python
import requests

# Upload document for analysis
response = requests.post(
    'http://localhost:8000/analyze',
    files={'document': open('policy.pdf', 'rb')}
)

compliance_report = response.json()
```

### Batch Processing
```python
import os
from src.dora_analyzer import DORAComplianceAnalyzer

async def analyze_multiple_policies():
    analyzer = DORAComplianceAnalyzer()
    
    for filename in os.listdir('policies/'):
        if filename.endswith('.pdf'):
            report = await analyzer.analyze_document(f'policies/{filename}')
            print(f"{filename}: {report.compliance_percentage:.1f}%")
```

## 📋 Demo Script for CIOs

### 5-Minute Executive Presentation

**"Let me show you automated DORA compliance assessment..."**

1. **Launch Demo** (30s)
   ```bash
   python demo.py
   # Select option 1: Full End-to-End Analysis
   ```

2. **Document Processing** (30s)
   - Show multi-format support
   - Real-time processing indicators
   - Quality scoring metrics

3. **AI Analysis** (1m)
   - 25+ DORA requirements assessed
   - Multi-model AI integration
   - Confidence scoring

4. **Executive Dashboard** (2m)
   - Overall compliance percentage
   - RAG status (Red/Amber/Green)
   - Pillar-by-pillar breakdown

5. **Risk Prioritization** (1m)
   - Critical/High/Medium gaps
   - Timeline recommendations
   - Investment estimates

### Key Messages for Stakeholders

**For CIOs:**
- "Reduce regulatory assessment from weeks to minutes"
- "Get audit-ready evidence automatically"  
- "Demonstrate proactive compliance to the board"

**For Risk Teams:**
- "Comprehensive DORA coverage with AI intelligence"
- "Prioritized gap identification with confidence scoring"

**For Auditors:**
- "Complete evidence trail for examinations"
- "Standardized methodology across policies"

## 🎯 Next Steps

1. **Run the demo** to see immediate capabilities
2. **Test with your policies** for real results
3. **Share with stakeholders** for feedback
4. **Plan production deployment** with web interface

---

**Ready to demonstrate AI-powered DORA compliance analysis!**

*For technical support or business inquiries, see the main README.md file.* 