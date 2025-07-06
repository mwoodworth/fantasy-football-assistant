import { type ChatMessage } from '../../services/ai';
import { User, Bot, Clock, Zap } from 'lucide-react';
import { cn } from '../../utils/cn';

interface ChatMessageProps {
  message: ChatMessage;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isError = message.analysis_type === 'error';

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-500';
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceText = (confidence?: number) => {
    if (!confidence) return 'Unknown';
    if (confidence >= 0.8) return 'High';
    if (confidence >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <div className={cn(
      'flex gap-3 p-4',
      isUser ? 'justify-end' : 'justify-start'
    )}>
      {!isUser && (
        <div className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isError ? 'bg-red-100' : 'bg-primary-100'
        )}>
          <Bot className={cn(
            'w-4 h-4',
            isError ? 'text-red-600' : 'text-primary-600'
          )} />
        </div>
      )}

      <div className={cn(
        'max-w-[70%] space-y-2',
        isUser ? 'order-last' : ''
      )}>
        <div className={cn(
          'rounded-lg px-4 py-3 text-sm',
          isUser 
            ? 'bg-primary-600 text-white' 
            : isError 
            ? 'bg-red-50 text-red-900 border border-red-200'
            : 'bg-gray-100 text-gray-900'
        )}>
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <Clock className="w-3 h-3" />
            <span>{formatTime(message.timestamp)}</span>
            
            {message.analysis_type && message.analysis_type !== 'general' && (
              <>
                <span>•</span>
                <span className="capitalize">{message.analysis_type.replace('_', ' ')}</span>
              </>
            )}
          </div>

          {!isUser && message.confidence && (
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              <span className={getConfidenceColor(message.confidence)}>
                {getConfidenceText(message.confidence)} confidence
              </span>
            </div>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center">
          <User className="w-4 h-4 text-gray-600" />
        </div>
      )}
    </div>
  );
}