import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '../common/Button';
import { cn } from '../../utils/cn';

interface ChatInputProps {
  onSendMessage: (message: string, analysisType?: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

const ANALYSIS_TYPES = [
  { value: 'general', label: 'General Chat' },
  { value: 'player_analysis', label: 'Player Analysis' },
  { value: 'trade_analysis', label: 'Trade Analysis' },
  { value: 'lineup_optimization', label: 'Lineup Help' },
  { value: 'waiver_wire', label: 'Waiver Wire' },
  { value: 'injury_analysis', label: 'Injury Analysis' },
  { value: 'breakout_prediction', label: 'Breakout Players' },
];

const QUICK_PROMPTS = [
  'Who should I start this week?',
  'Analyze this trade proposal',
  'What players should I target on waivers?',
  'How is my team looking for playoffs?',
  'Who are the best breakout candidates?',
  'What injuries should I be worried about?',
];

export function ChatInput({ onSendMessage, isLoading, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [analysisType, setAnalysisType] = useState('general');
  const [showQuickPrompts, setShowQuickPrompts] = useState(true);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message.trim(), analysisType);
      setMessage('');
      setShowQuickPrompts(false);
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    setMessage(prompt);
    setShowQuickPrompts(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t bg-white p-4 space-y-4">
      {/* Quick Prompts */}
      {showQuickPrompts && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Quick prompts:</p>
          <div className="flex flex-wrap gap-2">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleQuickPrompt(prompt)}
                className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                disabled={isLoading || disabled}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Analysis Type Selector */}
      <div className="flex items-center gap-2">
        <label htmlFor="analysis-type" className="text-sm font-medium text-gray-700">
          Mode:
        </label>
        <select
          id="analysis-type"
          value={analysisType}
          onChange={(e) => setAnalysisType(e.target.value)}
          className="text-sm border border-gray-300 rounded-md px-2 py-1 bg-white"
          disabled={isLoading || disabled}
        >
          {ANALYSIS_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </div>

      {/* Chat Input */}
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-1 relative">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask me anything about fantasy football..."
            rows={3}
            className={cn(
              'w-full px-3 py-2 border border-gray-300 rounded-lg resize-none',
              'focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500',
              'placeholder:text-gray-400',
              (isLoading || disabled) && 'opacity-50 cursor-not-allowed'
            )}
            disabled={isLoading || disabled}
          />
          <div className="absolute bottom-2 right-2 text-xs text-gray-400">
            Shift + Enter for new line
          </div>
        </div>
        
        <Button
          type="submit"
          disabled={!message.trim() || isLoading || disabled}
          className="self-end"
          size="sm"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </form>
    </div>
  );
}