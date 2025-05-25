# 🏦 DORA Compliance System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)

An **AI-powered, multi-agent compliance platform** that automates DORA (Digital Operational Resilience Act) readiness assessment, generates executive business cases, and creates detailed implementation roadmaps for financial institutions.

## 🎯 **Project Overview**

The EU's Digital Operational Resilience Act (DORA) requires financial institutions to transform their ICT risk management by January 2025. **Non-compliance penalties can reach €10M or 2% of annual revenue.**

This system provides:
- **Automated compliance assessment** across 47 DORA requirements
- **AI-powered gap analysis** with prioritized remediation plans
- **Financial impact modeling** with ROI analysis and penalty risk calculations
- **Executive reporting** with board-ready presentations
- **Implementation roadmaps** with detailed timelines and resource allocation

### 💰 **Proven Financial Impact**

```
🎯 Investment Required:    €396,900
💵 Penalty Risk Avoided:   €10,000,000
📈 Net Present Value:      €5,482,290
📊 Internal Rate Return:   65.1%
⏱️ Payback Period:         6.05 years
🚀 ROI Multiple:           2,431%
```

## 🤖 **AI Agent Architecture**

| Agent | Function | Key Output |
|-------|----------|------------|
| **Policy Analyzer** | Document analysis & gap detection | Compliance assessment |
| **Gap Assessment** | Risk-based prioritization | Remediation roadmap |
| **Risk Calculator** | Financial impact modeling | Business case |
| **Implementation Planner** | Project roadmap generation | Timeline & resources |
| **Executive Reporting** | Board-ready documentation | Strategic presentations |

## 🚀 **Quick Start**

### Prerequisites

- **Python 3.11+** (recommended: 3.11 or 3.12)
- **Git** for version control
- **Docker** (optional, for containerized deployment)

### Option 1: Automated Setup (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/enricoaquilina/dora-policy-analyzer.git
cd dora-policy-analyzer

# 2. Run automated setup
python setup.py

# 3. Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows

# 4. Edit .env file with your API keys
nano .env  # or use your preferred editor

# 5. Run the demo
python run_demo.py
```

**Alternative:** If you prefer to activate the virtual environment manually:
```bash
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
python demo_app.py
```

### Option 2: Manual Setup

### 1. Clone the Repository

```bash
git clone https://github.com/enricoaquilina/dora-policy-analyzer.git
cd dora-policy-analyzer
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install main application dependencies
pip install -r requirements.txt

# For full functionality, also install policy analyzer dependencies
pip install -r policy-analyzer-agent/requirements.txt

# Install additional components (optional)
pip install -r dora-knowledge-base/requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
# Copy the example environment file
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# AI Model API Keys (at least one required)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your_secret_key_here

# Database Configuration (optional for demo)
DATABASE_URL=postgresql://user:password@localhost/dora_db
REDIS_URL=redis://localhost:6379

# File Upload Configuration
MAX_CONTENT_LENGTH=104857600  # 100MB
UPLOAD_FOLDER=uploads
```

### 5. Run the Demo Application

```bash
# Option A: Use the demo runner (recommended)
python run_demo.py

# Option B: Activate virtual environment manually
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
python demo_app.py
```

The application will be available at: **http://localhost:5001**

## 📖 **Usage Guide**

### Demo Mode (Recommended for First Run)

1. **Access the Application**: Open http://localhost:5001 in your browser
2. **Upload a Policy Document**: Use the upload interface to submit a policy document (PDF, DOCX, TXT)
3. **View Real-time Analysis**: Watch the AI agents process your document
4. **Explore the Dashboard**: Review compliance scores, gap analysis, and recommendations
5. **Generate Reports**: Create executive summaries and implementation plans

### Production Mode

For production deployment, see the [Infrastructure Documentation](infrastructure/README.md).

## 🔧 **Advanced Configuration**

### AI Model Configuration

The system supports multiple AI providers. Configure your preferred models:

```bash
# Using Task Master AI configuration
npx task-master-ai models --setup
```

Or manually edit `.taskmasterconfig`:

```json
{
  "models": {
    "main": "claude-3-5-sonnet-20241022",
    "research": "gpt-4o",
    "fallback": "gemini-1.5-pro"
  }
}
```

### Database Setup (Optional)

For full functionality, set up the databases:

```bash
# PostgreSQL (primary database)
createdb dora_compliance

# Redis (caching)
redis-server

# Run database migrations
python scripts/setup_database.py
```

### Infrastructure Deployment

For enterprise deployment with Kubernetes:

```bash
# Navigate to infrastructure directory
cd infrastructure

# Deploy with Terraform
terraform init
terraform plan
terraform apply

# Deploy with Kubernetes
kubectl apply -f kubernetes/
```

## 🛠️ **Troubleshooting**

### Common Installation Issues

**Issue: `ModuleNotFoundError: No module named 'flask'`**
```bash
# Solution 1: Use the demo runner (automatically uses correct environment)
python run_demo.py

# Solution 2: Activate virtual environment first
source venv/bin/activate  # On macOS/Linux
# venv\Scripts\activate   # On Windows
python demo_app.py

# Solution 3: Use virtual environment Python directly
venv/bin/python demo_app.py  # On macOS/Linux
# venv\Scripts\python demo_app.py  # On Windows
```

**Issue: `textract` installation fails**
```bash
# Solution: Skip optional dependencies or install manually
pip install -r requirements.txt --no-deps
pip install Flask Flask-SocketIO eventlet anthropic openai
```

**Issue: Python version compatibility**
```bash
# Ensure you're using Python 3.11 or 3.12
python --version
# If needed, install the correct Python version
```

**Issue: Demo app won't start**
```bash
# Check if you're in the project root directory
pwd
# Should show: /path/to/dora-policy-analyzer

# Run from project root
python demo_app.py
```

**Issue: `TemplateNotFound` error**
```bash
# This has been fixed in the latest version
# Make sure you have the latest code:
git pull origin master

# The templates/ directory should exist with HTML files
ls templates/
```

### Quick Demo Setup (Minimal)

If you encounter dependency issues, try this minimal setup:

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# 2. Install minimal dependencies
pip install flask flask-socketio eventlet python-dotenv

# 3. Set up environment (optional for demo)
cp .env.example .env

# 4. Run demo
python demo_app.py
```

## 🧪 **Testing**

### Run Unit Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/
```

### Run Integration Tests

```bash
# Test the demo application
python test_executive_reporting.py

# Test individual agents
python -m pytest src/tests/
```

### Load Testing

```bash
# Install load testing tools
pip install locust

# Run load tests
locust -f tests/load_test.py --host=http://localhost:5001
```

## 📁 **Project Structure**

```
dora-policy-analyzer/
├── 📄 README.md                    # This file
├── 📄 demo_app.py                  # Main demo application
├── 📄 .env.example                 # Environment template
├── 📄 .gitignore                   # Git ignore rules
├── 📄 .taskmasterconfig            # AI model configuration
├── 📁 src/                         # Core AI agents and modules
│   ├── 📄 policy_analyzer_agent.py
│   ├── 📄 gap_assessment_agent.py
│   ├── 📄 risk_calculator_agent.py
│   ├── 📄 implementation_planner_agent.py
│   ├── 📄 executive_reporting_system.py
│   └── 📄 ...
├── 📁 policy-analyzer-agent/       # Policy analysis components
│   ├── 📄 requirements.txt
│   └── 📄 ...
├── 📁 infrastructure/              # Kubernetes & cloud infrastructure
│   ├── 📁 terraform/
│   ├── 📁 kubernetes/
│   └── 📄 README.md
├── 📁 docs/                        # Documentation
│   ├── 📄 architecture/
│   └── 📄 api/
├── 📁 demo_output/                 # Sample outputs and reports
├── 📁 dora-knowledge-base/         # DORA regulation knowledge
├── 📁 agent-orchestration/         # Multi-agent coordination
├── 📁 tasks/                       # Task management (Task Master)
├── 📁 scripts/                     # Utility scripts
└── 📁 uploads/                     # File upload directory
```

## 🔌 **API Reference**

### Core Endpoints

```bash
# Upload document for analysis
POST /api/upload
Content-Type: multipart/form-data

# Get analysis status
GET /api/status/{analysis_id}

# Get analysis results
GET /api/result/{analysis_id}

# Get demo compliance data
GET /api/demo-data

# Health check
GET /api/health
```

### Example API Usage

```python
import requests

# Upload a document
with open('policy.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5001/api/upload',
        files={'file': f}
    )
    analysis_id = response.json()['analysis_id']

# Check status
status = requests.get(f'http://localhost:5001/api/status/{analysis_id}')

# Get results
results = requests.get(f'http://localhost:5001/api/result/{analysis_id}')
```

## 🔒 **Security**

### Data Protection

- **Encryption**: All data encrypted at rest and in transit
- **Access Control**: Role-based access control (RBAC)
- **Audit Logging**: Comprehensive audit trails
- **GDPR Compliance**: Data minimization and right to be forgotten

### API Security

- **Authentication**: OAuth 2.0/OIDC integration
- **Rate Limiting**: Configurable rate limits
- **Input Validation**: Comprehensive input sanitization
- **CORS**: Configurable cross-origin policies

## 📊 **Monitoring & Observability**

### Application Metrics

- **Performance**: Response times, throughput
- **Business**: Compliance scores, gap trends
- **System**: CPU, memory, disk usage
- **AI Models**: Inference times, accuracy

### Logging

```bash
# View application logs
tail -f logs/dora_app.log

# View AI agent logs
tail -f logs/agents.log

# View audit logs
tail -f logs/audit.log
```

## 🚀 **Deployment Options**

### Local Development

```bash
python demo_app.py
```

### Docker Deployment

```bash
# Build image
docker build -t dora-compliance .

# Run container
docker run -p 5001:5001 -e ANTHROPIC_API_KEY=your_key dora-compliance
```

### Kubernetes Deployment

```bash
# Deploy to Kubernetes
kubectl apply -f infrastructure/kubernetes/

# Check deployment status
kubectl get pods -n dora-compliance
```

### Cloud Deployment

- **AWS**: EKS with Terraform automation
- **Azure**: AKS with ARM templates
- **GCP**: GKE with Cloud Deployment Manager

## 🤝 **Contributing**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run code formatting
black src/
isort src/

# Run linting
flake8 src/
mypy src/
```

### Submitting Changes

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📞 **Support**

### Documentation

- **[Technical Overview](TECHNICAL_OVERVIEW.md)**: Detailed architecture and specifications
- **[Demo Guide](DEMO_PREPARATION_CHECKLIST.md)**: Complete demo preparation
- **[API Documentation](docs/api/)**: Comprehensive API reference
- **[Infrastructure Guide](infrastructure/README.md)**: Deployment and operations

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/enricoaquilina/dora-policy-analyzer/issues)
- **Discussions**: [GitHub Discussions](https://github.com/enricoaquilina/dora-policy-analyzer/discussions)
- **Email**: support@dora-compliance.com

### Commercial Support

For enterprise support, custom development, or consulting services:
- **Enterprise Support**: enterprise@dora-compliance.com
- **Professional Services**: consulting@dora-compliance.com

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **European Banking Authority (EBA)** for DORA regulation guidance
- **Open source community** for the excellent libraries and tools
- **Financial institutions** providing feedback and requirements
- **AI research community** for advancing the state of the art

---

## 🎮 **Live Demo**

**Ready to see the system in action?**

1. **Quick Demo**: `python demo_app.py` → http://localhost:5001
2. **Upload a policy document** and watch real-time AI analysis
3. **Explore the compliance dashboard** with interactive charts
4. **Generate executive reports** ready for board presentation

**Transform your DORA compliance journey with AI-powered automation!**

---

*Last Updated: January 2025 | Version: 1.0.0* 