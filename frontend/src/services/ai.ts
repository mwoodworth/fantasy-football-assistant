import api from './api';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  analysis_type?: string;
  confidence?: number;
}

export interface ChatRequest {
  message: string;
  context?: Record<string, any>;
  conversation_id?: string;
  analysis_type?: string;
}

export interface ChatResponse {
  response: string;
  confidence: number;
  conversation_id?: string;
  analysis_type: string;
  timestamp: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface PlayerAnalysisRequest {
  player_id: number;
  analysis_type?: string;
  context?: Record<string, any>;
}

export interface TradeAnalysisRequest {
  trade_data: Record<string, any>;
  team_context?: Record<string, any>;
}

export class AIService {
  static async sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await api.post('/ai/chat', request);
    return response.data;
  }

  static async analyzePlayer(request: PlayerAnalysisRequest): Promise<any> {
    const response = await api.post('/ai/analyze-player', request);
    return response.data;
  }

  static async analyzeTrade(request: TradeAnalysisRequest): Promise<any> {
    const response = await api.post('/ai/analyze-trade', request);
    return response.data;
  }

  static async getRecommendations(request: Record<string, any>): Promise<any> {
    const response = await api.post('/ai/recommendations/comprehensive', request);
    return response.data;
  }

  static async getQuickRecommendation(request: Record<string, any>): Promise<any> {
    const response = await api.post('/ai/recommendations/quick', request);
    return response.data;
  }

  static async generateWeeklyReport(request: Record<string, any>): Promise<any> {
    const response = await api.post('/ai/reports/weekly', request);
    return response.data;
  }

  static async getSentimentAnalysis(playerId: number, playerName: string): Promise<any> {
    const response = await api.post('/ai/sentiment/analyze', {
      player_id: playerId,
      player_name: playerName,
    });
    return response.data;
  }

  static async predictInjuryRisk(request: Record<string, any>): Promise<any> {
    const response = await api.post('/ai/injury/predict', request);
    return response.data;
  }

  static async predictBreakout(request: Record<string, any>): Promise<any> {
    const response = await api.post('/ai/breakout/predict', request);
    return response.data;
  }

  static async predictGameScript(request: Record<string, any>): Promise<any> {
    const response = await api.post('/ai/game-script/predict', request);
    return response.data;
  }

  static async simulateExpertPanel(request: Record<string, any>): Promise<any> {
    const response = await api.post('/ai/expert-simulation/analyze', request);
    return response.data;
  }
}