# ⚽ Soccer Predictor Pro v5.0 - TRANSFORMED Edition

**Professional-Grade Football Prediction System** | **Production-Ready** | **Enterprise Features**

---

## 🎯 Overview

Soccer Predictor Pro is a state-of-the-art football prediction system built with enterprise-grade features. Inspired by F1 Predictor 2026 architecture, this application provides professional-level match predictions using advanced statistical models, machine learning algorithms, and real-world contextual factors.

### ✨ Key Features

- **Advanced Prediction Engine**: Monte Carlo simulations, ELO ratings, and ensemble models
- **Probability Calibration**: Platt Scaling and Temperature Scaling for accurate probability estimates
- **Bayesian Weight Optimization**: Automatic model weight tuning with Optuna
- **Comprehensive Accuracy Tracking**: Brier Score, Log Loss, Expected Calibration Error (ECE)
- **Professional Reports**: HTML, PDF, CSV, JSON, and Excel exports
- **Real-World Context Modeling**: Weather, injuries, referee stats, travel fatigue
- **Multi-Dimensional Team Ratings**: Beyond basic ELO - set pieces, counter attacks, pressure performance
- **Database Persistence**: SQLite with SQLAlchemy ORM for data persistence
- **Web Dashboard**: Interactive Flask-based interface with real-time updates

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  WEB DASHBOARD                       │
│           (Flask + Tailwind CSS + Plotly.js)        │
│  http://127.0.0.1:5000                              │
└──────────────────┬──────────────────────────────────┘
│ REST API (JSON)
┌──────────────────▼──────────────────────────────────┐
│              FLASK APPLICATION LAYER                 │
│         app.py (30+ endpoints)                      │
└──┬────────┬──────────┬───────────┬──────────────────┘
│        │          │           │
┌──▼──┐ ┌──▼────┐ ┌───▼────┐ ┌───▼──────────┐
│Pred │ │Accur  │ │Optimize│ │Report        │
│Engine│ │Tracker│ │(Optuna)│ │Generator     │
└──┬──┘ └──┬────┘ └───┬────┘ └───┬──────────┘
│       │          │           │
└───────┴──────────┴───────────┘
│
┌──────────────────▼──────────────────────────────────┐
│              DATA & MODELS LAYER                     │
│  • Vectorized Monte Carlo (NumPy)                   │
│  • Probability Calibration (Platt/Temperature)      │
│  • Multi-dimensional ELO ratings                    │
│  • Feature engineering pipeline                     │
│  • Context factor modeling                          │
│  • SQLite database (SQLAlchemy ORM)                 │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (tested up to Python 3.14)
- **Node.js** (for frontend builds)
- **Git** (for cloning the repository)

### Installation

#### Option 1: Local Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/soccer-predictor-pro.git
cd soccer-predictor-pro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Build CSS
npm run build

# Create environment file
cp .env.example .env
# Edit .env with your API keys
```

#### Option 2: Docker Installation (Recommended)

```bash
# Build and run with Docker
docker build -t soccer-predictor-pro .
docker run -p 5000:5000 -e FOOTBALL_DATA_API_KEY=your_key_here soccer-predictor-pro
```

### Configuration

Create a `.env` file with the following:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=production

# Database Configuration
DATABASE_URL=sqlite:///soccer_predictor.db

# API Keys (for real data integration)
FOOTBALL_DATA_API_KEY=your_football_data_key
ODDS_API_KEY=your_odds_api_key_optional
RAPIDAPI_KEY=your_rapidapi_key_optional

# Server Configuration
HOST=0.0.0.0
PORT=5000
```

### Running the Application

#### Local Development

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the application
python app.py
```

#### Production (using Gunicorn)

```bash
gunicorn --bind 0.0.0.0:5000 app:create_app
```

#### Docker

```bash
# Build the image
docker build -t soccer-predictor-pro .

# Run the container
docker run -p 5000:5000 -d --env-file .env soccer-predictor-pro
```

The application will be available at `http://localhost:5000`

---

## 🎛️ API Endpoints

### Main Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/predictions` | GET | Match predictions interface |
| `/predictions/match/<id>` | GET | Specific match prediction |
| `/fixtures` | GET | Upcoming fixtures |
| `/leagues` | GET | Available leagues |
| `/export` | GET | Export options |
| `/health` | GET | Health check |

### Advanced Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/advanced/predict/<match_id>` | GET | Advanced prediction with calibration |
| `/advanced/calibrate/train` | POST | Train probability calibration |
| `/advanced/optimize/weights` | POST | Optimize ensemble weights |
| `/advanced/report/<match_id>/<format>` | GET | Download reports (html/pdf/csv/json/excel) |
| `/advanced/accuracy/dashboard` | GET | Accuracy dashboard data |
| `/advanced/accuracy/metrics` | GET | Current accuracy metrics |
| `/api/v1/matches` | GET | API endpoint for matches |

---

## 📊 Key Metrics Explained

### Brier Score
- Measures mean squared error of predicted probabilities
- Range: 0 to 1 (lower is better)
- Good score: < 0.20, Excellent: < 0.15

### Log Loss
- Confidence-weighted accuracy measure
- Penalizes confident wrong predictions heavily
- Good score: < 1.05

### Expected Calibration Error (ECE)
- Average difference between predicted and actual frequencies
- Range: 0 to 1 (lower is better)
- Good calibration: < 0.05

---

## 🏗️ Project Structure

```
soccer-predictor-pro/
├── app.py                 # Main Flask application
├── run_server.py          # Production server runner
├── state.py               # Session management
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── package.json           # Node.js dependencies
├── Dockerfile             # Docker configuration
├── README.md              # This file
├── TODO.md                # Development roadmap
├── PROJECT_TRANSFORMATION_PLAN.md  # Architecture plan
├── src/
│   └── soccer_predictor/
│       ├── core/          # Core algorithms and models
│       ├── data/          # Data models and processing
│       ├── routes/        # Flask blueprints
│       ├── services/      # Business logic services
│       ├── schemas/       # Data validation schemas
│       ├── static/        # CSS, JS, images
│       ├── templates/     # HTML templates
│       └── utils/         # Utility functions
├── static/                # Compiled static assets
└── templates/             # Rendered templates
```

---

## 🧠 Advanced Features

### 1. Probability Calibration
The system uses Platt Scaling to ensure that predicted probabilities reflect actual frequencies:
- "60% chance of winning" actually means the team wins 60% of the time
- Reduces overconfidence in predictions
- Improves Brier Score and ECE

### 2. Bayesian Weight Optimization
Automatic optimization of ensemble model weights using Optuna:
- Minimizes Brier Score as the objective function
- Weekly auto-tuning capability
- Tracks weight evolution over time

### 3. Contextual Factors
Real-world factors that affect match outcomes:
- Weather conditions
- Referee statistics (cards per game, penalty rate)
- Player injuries and suspensions
- Team motivation (derbies, title deciders, relegation battles)
- Travel distance and rest days

### 4. Multi-Dimensional Team Ratings
Beyond simple ELO ratings:
- Attack/defense strength
- Set-piece effectiveness
- Counter-attack proficiency
- High-pressure performance
- Home/away specific ratings
- Form momentum calculations

---

## 🐳 Docker Configuration

### Building the Image

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    shared-mime-info \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:create_app"]
```

### Docker Compose (Optional)

```yaml
version: '3.8'
services:
  soccer-predictor:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FOOTBALL_DATA_API_KEY=${FOOTBALL_DATA_API_KEY}
      - DATABASE_URL=sqlite:///app/data/soccer_predictor.db
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```

---

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src/soccer_predictor
```

### Test Database

```bash
# Initialize test database
python -m src.soccer_predictor.data.models
```

---

## 🔒 Security

- API keys stored in environment variables only
- SQL injection protection via SQLAlchemy ORM
- Input validation using Flask-WTF
- Secure session management
- Production-ready configuration with disabled debug mode

---

## 📈 Performance

- Vectorized NumPy operations for fast computations
- Efficient database queries with proper indexing
- Caching strategies for repeated calculations
- Asynchronous operations where appropriate

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Areas Needing Help

- Real API integrations (football-data.org, The Odds API)
- Additional calibration methods (Isotonic Regression)
- More context factors (injury severity, tactical matchups)
- Enhanced visualizations (interactive reliability diagrams)
- Performance optimizations (caching, async operations)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **F1 Predictor 2026** - Primary inspiration for architecture
- **Flask Framework** - Web application foundation
- **SQLAlchemy** - Database ORM excellence
- **Optuna** - Bayesian optimization framework
- **Scikit-learn** - Machine learning utilities
- **WeasyPrint** - PDF generation capabilities

---

## 📞 Support

- **Issues**: GitHub Issues tab
- **Documentation**: This README and inline code comments
- **Community**: GitHub Discussions

---

**Built with ❤️ for the football prediction community**

*Version 5.0.0 - Transformed Edition*  
*Last Updated: 2026-07-07*#   S O C C E R _ P R E D I C T O R - 2 6 - 2 7  
 