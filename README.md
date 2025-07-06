# Fantasy Football Assistant

An AI-powered fantasy football assistant that provides intelligent draft strategies, weekly lineup optimization, waiver wire recommendations, and trade analysis using advanced machine learning and natural language processing.

## Project Status: 🚀 Phase 4 Complete - Advanced Predictive Models

**Current Version**: Phase 4 - Advanced Predictive Models & Expert Simulation  
**Status**: Production-ready backend with comprehensive AI and predictive analytics

## Features

### 🤖 AI-Powered Intelligence
- **Natural Language Chat**: Ask questions about players, strategies, and matchups
- **Automated Weekly Reports**: Comprehensive team analysis with AI insights
- **Sentiment Analysis**: Player news impact assessment with fantasy implications
- **Intelligent Recommendations**: Multi-category AI-driven suggestions for all fantasy decisions
- **Advanced Analytics Dashboard**: Real-time performance metrics and trend analysis

### 🔮 Advanced Predictive Models (NEW!)
- **Injury Risk Prediction**: 6-level risk assessment with prevention recommendations
- **Breakout Player Detection**: Identify undervalued players with 6 breakout types
- **Game Script Prediction**: Predict game flow and player usage impacts
- **Fantasy Expert Simulation**: 6 AI expert personas with consensus analysis

### 📊 Core Fantasy Tools
- **Player Analysis**: ML-powered performance predictions and breakout detection
- **Trade Analyzer**: Multi-dimensional trade evaluation with AI reasoning
- **Lineup Optimizer**: Matchup-based lineup suggestions with confidence scoring
- **Waiver Wire Intelligence**: Prioritized pickup targets with strategic reasoning
- **Injury Monitoring**: Real-time updates with fantasy impact assessment

### 🔄 Data Integration
- **ESPN Integration**: Real-time player statistics and league data
- **ML Pipeline**: XGBoost and scikit-learn models for predictions
- **News Analysis**: Automated sentiment tracking from multiple sources
- **Weather & Conditions**: Game environment impact analysis
- **Historical Data**: Multi-season performance tracking

## Technology Stack

### Backend (Complete)
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: Claude API (Anthropic) + scikit-learn + XGBoost
- **Authentication**: JWT tokens with Bearer authentication
- **Services**: Modular AI service architecture

### APIs & Services
- **ESPN API**: Player statistics and league data
- **Claude API**: Natural language processing and insights
- **ML Models**: Performance prediction and analysis
- **Caching**: Redis-ready optimization layer

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Anthropic API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fantasy-football-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys:
# ANTHROPIC_API_KEY=your_claude_api_key
# DATABASE_URL=postgresql://user:password@localhost/fantasy_db
```

5. Initialize the database:
```bash
alembic upgrade head
```

6. Run the development server:
```bash
uvicorn src.main:app --reload --port 8000
```

7. Access the API:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## API Endpoints

### Authentication
- `POST /api/auth/register` - Create new user account
- `POST /api/auth/login` - Login and get JWT tokens
- `GET /api/auth/me` - Get current user profile

### AI Services
- `POST /api/ai/chat` - Natural language chat with AI
- `POST /api/ai/analyze-player` - Comprehensive player analysis
- `POST /api/ai/analyze-trade` - Trade evaluation with AI insights
- `GET /api/ai/insights/weekly/{team_id}` - Weekly AI-generated reports

### Sentiment Analysis
- `POST /api/ai/sentiment/analyze` - Player news sentiment analysis
- `POST /api/ai/sentiment/league` - League-wide sentiment tracking

### Recommendations
- `POST /api/ai/recommendations/comprehensive` - Full recommendation suite
- `POST /api/ai/recommendations/quick` - Quick targeted suggestions

### Advanced Analytics
- `POST /api/ai/analytics/player` - Player performance analytics
- `POST /api/ai/analytics/team` - Team composition analysis
- `POST /api/ai/analytics/league` - League-wide insights
- `GET /api/ai/analytics/real-time/{entity_type}/{entity_id}` - Live updates

### Injury Prediction (NEW!)
- `POST /api/ai/injury/predict` - Individual player injury risk assessment
- `POST /api/ai/injury/team-risk-assessment` - Team-wide injury analysis
- `GET /api/ai/injury/risk-levels` - Injury risk level descriptions
- `POST /api/ai/injury/history-analysis` - Historical injury pattern analysis

### Breakout Detection (NEW!)
- `POST /api/ai/breakout/predict` - Individual player breakout analysis
- `POST /api/ai/breakout/candidates` - Top breakout candidates identification
- `POST /api/ai/breakout/compare` - Multi-player breakout comparison
- `GET /api/ai/breakout/likelihood-levels` - Breakout likelihood descriptions

### Game Script Prediction (NEW!)
- `POST /api/ai/game-script/predict` - Predict game flow and player usage impacts

### Expert Simulation (NEW!)
- `POST /api/ai/expert-simulation/analyze` - Simulate fantasy expert panel analysis
- `GET /api/ai/expert-simulation/expert-types` - Available expert personas

### Fantasy Management
- `GET /api/fantasy/teams` - User's fantasy teams
- `GET /api/fantasy/players` - Player database
- `GET /api/espn/league/{league_id}` - ESPN league integration

## Project Structure

```
fantasy-football-assistant/
├── src/
│   ├── api/                    # API endpoints
│   │   ├── ai.py              # AI service endpoints (19 endpoints)
│   │   ├── auth.py            # Authentication endpoints
│   │   ├── fantasy.py         # Fantasy management
│   │   └── espn.py            # ESPN integration
│   ├── models/                 # Database models
│   │   ├── user.py            # User model
│   │   └── database.py        # Database connection
│   ├── services/              # Business logic
│   │   ├── ai/                # AI service modules
│   │   │   ├── claude_client.py         # Claude API integration
│   │   │   ├── ml_pipeline.py           # ML models pipeline
│   │   │   ├── sentiment_analyzer.py    # News sentiment analysis
│   │   │   ├── recommendation_engine.py # Intelligent recommendations
│   │   │   ├── weekly_report_generator.py # Automated reports
│   │   │   ├── analytics_dashboard.py   # Advanced analytics
│   │   │   ├── injury_predictor.py      # Injury risk prediction
│   │   │   ├── injury_data_collector.py # Injury training data
│   │   │   ├── breakout_detector.py     # Breakout player detection
│   │   │   ├── game_script_predictor.py # Game script prediction
│   │   │   └── expert_simulator.py      # Fantasy expert simulation
│   │   ├── espn_service.py    # ESPN API integration
│   │   └── auth.py            # Authentication logic
│   ├── utils/                 # Utility functions
│   └── main.py               # FastAPI application
├── tests/                    # Test files
├── models/                   # ML model files
├── data/                     # Data files
├── PHASE3_PLAN.md           # Detailed implementation plan
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Development Progress

### ✅ Phase 1: Foundation (Complete)
- ✅ Project structure and database schema
- ✅ User authentication with JWT tokens
- ✅ Core API endpoints
- ✅ ESPN API integration

### ✅ Phase 2: Core Features (Complete)
- ✅ Player database and management
- ✅ Fantasy team integration
- ✅ ESPN league data sync
- ✅ Mock data generation for testing

### ✅ Phase 3: AI Integration (Complete)
- ✅ Claude API integration for natural language processing
- ✅ ML pipeline with XGBoost and scikit-learn
- ✅ Automated insights generation
- ✅ Sentiment analysis for player news
- ✅ Intelligent recommendation engine
- ✅ Weekly report generation
- ✅ Advanced analytics dashboard

### ✅ Phase 4: Advanced Predictive Models (Complete)
- ✅ Injury prediction modeling with 6 risk levels
- ✅ Fantasy expert simulation with 6 expert personas
- ✅ Breakout player detection with multi-factor analysis
- ✅ Game script prediction with 7 script types

### 🔄 Phase 5: Frontend & Polish (Planned)
- 🔄 React frontend with TypeScript
- 🔄 Real-time dashboard
- 🔄 Mobile responsive design
- 🔄 Performance optimization

## Key Features Implemented

### 🎯 AI Chat Interface
Ask natural language questions like:
- "Should I start Josh Allen or Lamar Jackson this week?"
- "What players should I target on waivers?"
- "Analyze this trade: my CMC for their Jefferson and Jacobs"

### 📈 Advanced Analytics
- **Player Metrics**: Performance, consistency, efficiency tracking
- **Team Analysis**: Positional strength, playoff probability
- **League Insights**: Market trends, comparative analysis
- **Real-time Updates**: Live performance monitoring

### 🎪 Intelligent Recommendations
- **Lineup Optimization**: Start/sit decisions with reasoning
- **Waiver Wire Targets**: Prioritized pickup suggestions
- **Trade Opportunities**: AI-identified beneficial trades
- **Strategic Planning**: Season-long advice

### 📊 Automated Reports
- **Weekly Team Analysis**: Comprehensive performance reviews
- **Player Breakdowns**: Individual analysis with predictions
- **Market Intelligence**: League trends and opportunities
- **Confidence Scoring**: Risk assessment for all decisions

## Contributing

This project is actively developed. Current focus areas:
- Frontend development (React/TypeScript)
- Advanced ML model improvements
- Additional data source integrations
- Performance optimization

## License

[To be determined]

## Contact

[Your contact information]

## Acknowledgments

- Anthropic for Claude API
- ESPN for fantasy sports data
- Open source ML community
- Fantasy football analysts and community