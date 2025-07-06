import { create } from 'zustand';
import { AIService, type ChatMessage } from '../services/ai';

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  conversationId: string | null;
  
  // Actions
  sendMessage: (content: string, analysisType?: string, context?: Record<string, any>) => Promise<void>;
  clearMessages: () => void;
  clearError: () => void;
  addMessage: (message: ChatMessage) => void;
}

const generateMessageId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,
  conversationId: null,

  sendMessage: async (content, analysisType = 'general', context = {}) => {
    const { messages, conversationId } = get();
    
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: generateMessageId(),
      role: 'user',
      content,
      timestamp: new Date(),
      analysis_type: analysisType,
    };

    set({ 
      messages: [...messages, userMessage], 
      isLoading: true, 
      error: null 
    });

    try {
      const response = await AIService.sendChatMessage({
        message: content,
        context,
        conversation_id: conversationId || undefined,
        analysis_type: analysisType,
      });

      // Add assistant response
      const assistantMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(response.timestamp),
        analysis_type: response.analysis_type,
        confidence: response.confidence,
      };

      set((state) => ({ 
        messages: [...state.messages, assistantMessage],
        isLoading: false,
        conversationId: response.conversation_id || state.conversationId,
      }));

    } catch (error: any) {
      console.error('Chat error:', error);
      
      // Add error message
      const errorMessage: ChatMessage = {
        id: generateMessageId(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        analysis_type: 'error',
      };

      set((state) => ({ 
        messages: [...state.messages, errorMessage],
        isLoading: false,
        error: error.response?.data?.detail || 'Failed to send message',
      }));
    }
  },

  clearMessages: () => set({ 
    messages: [], 
    conversationId: null, 
    error: null 
  }),

  clearError: () => set({ error: null }),

  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
}));