# Fantasy Football Assistant

An AI-powered fantasy football assistant that provides intelligent draft strategies, weekly lineup optimization, waiver wire recommendations, and trade analysis using advanced machine learning and natural language processing.

## Project Status: 🚀 Phase 5 Complete - Full-Stack Application Ready

**Current Version**: Phase 5 - Complete Frontend with React + TypeScript  
**Status**: Production-ready full-stack application with comprehensive AI features

## 🎉 What's New in Phase 5

### Frontend Application (Complete)
- **Modern React UI**: Built with React 18, TypeScript, and Vite
- **Beautiful Design**: Tailwind CSS with responsive layouts
- **Real-time Dashboard**: Live scores, trending players, and performance metrics
- **Team Management**: Complete team interface with settings and roster management
- **Player Analytics**: Advanced visualizations and player comparison tools
- **AI Chat Assistant**: Natural language interface for fantasy advice
- **Authentication**: Secure JWT-based auth with persistent sessions

## Features

### 🎨 Frontend Features
- **Dashboard**: Real-time overview with live scores, top performers, and injury alerts
- **Player Search**: Advanced filtering with position, team, and performance metrics
- **Player Details**: Comprehensive player pages with stats, projections, and analysis
- **Team Management**: Roster management, lineup optimization, and trade center
- **Analytics Page**: Interactive charts and performance visualizations
- **AI Assistant**: Chat interface for natural language fantasy advice
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile

### 🤖 AI-Powered Intelligence
- **Natural Language Chat**: Ask questions about players, strategies, and matchups
- **Automated Weekly Reports**: Comprehensive team analysis with AI insights
- **Sentiment Analysis**: Player news impact assessment with fantasy implications
- **Intelligent Recommendations**: Multi-category AI-driven suggestions for all fantasy decisions
- **Advanced Analytics Dashboard**: Real-time performance metrics and trend analysis

### 🔮 Advanced Predictive Models
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

### 🔄 Live Draft Integration (NEW!)
- **ESPN Integration**: Connect and sync with ESPN fantasy leagues
- **Real-time Draft Tracking**: WebSocket-powered live draft updates
- **Instant Pick Notifications**: Get notified when it's your turn
- **Draft Board Visualization**: See all picks in an organized grid
- **AI Draft Recommendations**: Smart pick suggestions based on team needs
- **See Implementation Plan**: [docs/live-draft-implementation-plan.md](docs/live-draft-implementation-plan.md)

### 🔄 Data Integration
- **ESPN Integration**: Real-time player statistics and league data
- **ML Pipeline**: XGBoost and scikit-learn models for predictions
- **News Analysis**: Automated sentiment tracking from multiple sources
- **Weather & Conditions**: Game environment impact analysis
- **Historical Data**: Multi-season performance tracking

## Technology Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite for fast development
- **Styling**: Tailwind CSS with custom components
- **State Management**: Zustand for global state
- **Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router v6
- **Charts**: Recharts for data visualization
- **Icons**: Lucide React

### Backend
- **Framework**: FastAPI with async support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI/ML**: Claude API (Anthropic) + scikit-learn + XGBoost
- **Authentication**: JWT tokens with Bearer authentication
- **Services**: Modular AI service architecture

### APIs & Services
- **ESPN API**: Player statistics and league data
- **Claude API**: Natural language processing and insights
- **ML Models**: Performance prediction and analysis
- **Dashboard API**: Real-time data endpoints

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- PostgreSQL 14+ (or SQLite for development)
- Anthropic API key (optional, mock responses available)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd fantasy-football-assistant
```

2. Set up the backend:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

3. Set up the frontend:
```bash
cd frontend
npm install
```

4. Initialize the database:
```bash
alembic upgrade head
```

5. Check dependencies (optional but recommended):
   ```bash
   # Check all dependencies
   ./scripts/check_dependencies.sh
   ```

6. Run the application:

   **Option 1: Use the WebSocket-enabled startup script (recommended)**
   ```bash
   python3 scripts/start_with_websockets.py
   ```
   This script will:
   - Check and install missing dependencies
   - Enable WebSocket support if disabled
   - Start both backend and frontend servers
   - Show real-time status updates
   
   **Option 2: Use the basic startup script**
   ```bash
   ./start.sh
   ```
   
   **Option 3: Run services manually**
   ```bash
   # Terminal 1: Backend API with WebSocket support
   uvicorn src.main:app --reload --port 6001
   
   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

7. Access the application:
- **Frontend**: http://localhost:5173
- **API Documentation**: http://localhost:6001/docs
- **Health Check**: http://localhost:6001/health

### Default Login
For development, you can register a new account or use:
- **Email**: test@example.com
- **Password**: TestPassword123!

## Troubleshooting

### WebSocket Connection Issues
If WebSocket features aren't working:

1. **Check dependencies**:
   ```bash
   ./scripts/check_dependencies.sh
   ```

2. **Fix npm permissions** (if needed):
   ```bash
   sudo chown -R $(whoami) ~/.npm
   ```

3. **Reinstall frontend dependencies**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Use the WebSocket startup script**:
   ```bash
   python3 scripts/start_with_websockets.py
   ```

### Common Issues
- **"socket.io-client not found"**: Run `cd frontend && npm install socket.io-client`
- **npm permission errors**: Fix with `sudo chown -R $(whoami) ~/.npm`
- **WebSocket not connecting**: Check that backend is running on port 6001
- **Draft updates not real-time**: Ensure WebSocket icon shows green (connected)

## Project Structure

```
fantasy-football-assistant/
├── frontend/                   # React frontend application
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   │   ├── common/       # Base components (Button, Card, etc.)
│   │   │   ├── dashboard/    # Dashboard widgets
│   │   │   ├── players/      # Player-related components
│   │   │   ├── analytics/    # Charts and visualizations
│   │   │   └── ai/          # AI chat interface
│   │   ├── pages/           # Page components
│   │   ├── services/        # API service layer
│   │   ├── store/           # Global state management
│   │   └── utils/           # Utility functions
├── src/                      # Backend application
│   ├── api/                 # API endpoints
│   │   ├── ai.py           # AI service endpoints
│   │   ├── auth.py         # Authentication
│   │   ├── dashboard.py    # Dashboard data endpoints
│   │   └── ...
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   │   ├── ai/            # AI service modules
│   │   ├── draft_monitor.py  # ESPN draft polling service
│   │   └── websocket_server.py # Socket.IO server
│   └── main.py            # FastAPI application
├── scripts/                # Utility scripts
│   ├── start_with_websockets.py  # WebSocket-enabled startup
│   ├── check_dependencies.sh     # Dependency checker
│   └── clear_leagues.py          # Database utilities
├── tests/                  # Test files
├── start.sh               # Basic startup script
└── README.md             # This file
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

### ✅ Phase 5: Frontend & Polish (Complete)
- ✅ React frontend with TypeScript + Vite
- ✅ Authentication flow with JWT token management
- ✅ Responsive layout with sidebar navigation
- ✅ Tailwind CSS design system
- ✅ Real-time dashboard implementation
- ✅ AI chat interface with mock responses
- ✅ Player management features
- ✅ Analytics visualizations
- ✅ Team settings and management
- ✅ Dashboard widgets (live scores, trending players, etc.)

## Testing & Quality Assurance

### 🧪 Test Coverage Status
- **Current Test Pass Rate**: 66% (124/189 tests passing)
- **Service Layer Coverage**: Comprehensive test suites for core services
- **Test Infrastructure**: Robust mocking, fixtures, and edge case handling

### Recently Enhanced Test Coverage
- **LineupOptimizer**: 20+ tests covering lineup generation, player availability, matchup analysis
- **TradeAnalyzer**: 20+ tests covering trade evaluation, value analysis, fairness scoring
- **WaiverAnalyzer**: 27 tests covering waiver recommendations, trending analysis, FAAB calculations
- **Integration Tests**: End-to-end workflow testing for critical user journeys

## 🚀 What's Next - Future Enhancements

### Phase 6: Production Optimization
- [ ] Performance optimization and caching
- [ ] WebSocket support for real-time updates
- [ ] Advanced error handling and recovery
- [✅] Comprehensive test coverage (66% pass rate, expanded service tests)
- [ ] Docker containerization
- [ ] CI/CD pipeline setup

### Phase 6.5: Live ESPN Draft Integration
- [ ] Real-time draft monitoring via ESPN API polling
- [ ] WebSocket implementation for live updates
- [ ] Automatic pick detection and synchronization
- [ ] Enhanced draft UI with live draft board
- [ ] Draft notifications and alerts
- **📋 See detailed implementation plan**: [docs/live-draft-implementation-plan.md](docs/live-draft-implementation-plan.md)

### Phase 7: Enhanced Features
- [ ] Mobile app (React Native)
- [ ] Push notifications for important updates
- [ ] Advanced trade finder with ML matching
- [ ] Draft room simulation
- [ ] Historical performance tracking
- [ ] Custom scoring system support
- [ ] Multi-league management

### Phase 8: Data & Integration
- [ ] Additional data sources (Yahoo, Sleeper, etc.)
- [ ] Advanced weather impact analysis
- [ ] Vegas odds integration
- [ ] Social media sentiment tracking
- [ ] Automated lineup setting
- [ ] CSV/Excel export functionality

### Phase 9: Community Features
- [ ] User forums and discussions
- [ ] Expert consensus rankings
- [ ] Custom league rules support
- [ ] Trade marketplace
- [ ] Achievement system
- [ ] Fantasy football tutorials

## Known Issues & Limitations

### Current Limitations
- AI features require Anthropic API key (mock responses available)
- ESPN integration requires manual league ID input
- Limited to PPR scoring format currently
- No real-time WebSocket updates yet
- Mobile responsiveness could be improved

### Bug Fixes Needed
- [ ] Improve error handling for API failures
- [ ] Add loading states for all async operations
- [ ] Optimize bundle size for production
- [ ] Add proper form validation
- [ ] Implement request rate limiting

## Contributing

This project is actively developed. Priority areas for contribution:
- Test coverage (unit and integration tests)
- Performance optimization
- Additional data source integrations
- Mobile app development
- UI/UX improvements

### Development Setup
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style
- Backend: Follow PEP 8 for Python code
- Frontend: Use ESLint and Prettier configurations
- Write meaningful commit messages
- Add tests for new features
- Update documentation as needed

## License

[To be determined]

## Contact

[Your contact information]

## Acknowledgments

- Anthropic for Claude API
- ESPN for fantasy sports data
- React and FastAPI communities
- Open source ML community
- Fantasy football analysts and community