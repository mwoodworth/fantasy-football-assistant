import { AlertCircle, Calendar, Activity } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../common/Card';
import { Badge } from '../common/Badge';
import { Button } from '../common/Button';
import type { InjuryAlert } from '../../services/dashboard';
import { cn } from '../../utils/cn';

interface InjuryReportWidgetProps {
  injuries?: InjuryAlert[];
  loading?: boolean;
}

export function InjuryReportWidget({ injuries, loading }: InjuryReportWidgetProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Questionable':
        return 'bg-yellow-100 text-yellow-800';
      case 'Doubtful':
        return 'bg-orange-100 text-orange-800';
      case 'Out':
      case 'IR':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: 'low' | 'medium' | 'high') => {
    const baseClasses = 'w-2 h-2 rounded-full';
    switch (severity) {
      case 'high':
        return <div className={cn(baseClasses, 'bg-red-500')} />;
      case 'medium':
        return <div className={cn(baseClasses, 'bg-yellow-500')} />;
      default:
        return <div className={cn(baseClasses, 'bg-green-500')} />;
    }
  };

  const getUrgencyBadge = (severity: 'low' | 'medium' | 'high') => {
    switch (severity) {
      case 'high':
        return (
          <Badge variant="error" size="sm" className="animate-pulse">
            🚨 Urgent
          </Badge>
        );
      case 'medium':
        return (
          <Badge variant="warning" size="sm">
            ⚠️ Monitor
          </Badge>
        );
      default:
        return (
          <Badge variant="success" size="sm">
            ✅ Minor
          </Badge>
        );
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-red-500" />
            Injury Report
          </div>
          {injuries && injuries.length > 0 && (
            <Badge variant="error" size="sm">
              {injuries.length} Alert{injuries.length !== 1 ? 's' : ''}
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="space-y-3">
            {Array.from({ length: 2 }).map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="flex items-start space-x-3">
                  <div className="w-2 h-2 bg-gray-200 rounded-full mt-2"></div>
                  <div className="flex-1 space-y-2">
                    <div className="w-32 h-4 bg-gray-200 rounded"></div>
                    <div className="w-full h-3 bg-gray-200 rounded"></div>
                    <div className="w-24 h-3 bg-gray-200 rounded"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : injuries && injuries.length > 0 ? (
          <div className="space-y-4">
            {injuries.map((injury) => (
              <div
                key={injury.player.id}
                className={cn(
                  'p-3 rounded-lg border-l-4 transition-colors hover:bg-gray-50',
                  injury.severity === 'high' ? 'border-l-red-500 bg-red-50' :
                  injury.severity === 'medium' ? 'border-l-yellow-500 bg-yellow-50' :
                  'border-l-green-500 bg-green-50'
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-3 flex-1">
                    {getSeverityIcon(injury.severity)}
                    
                    <div className="flex-1">
                      {/* Player Info */}
                      <div className="flex items-center space-x-2 mb-1">
                        <span className="font-medium text-sm">{injury.player.name}</span>
                        <Badge className="bg-gray-100 text-gray-700" size="sm">
                          {injury.player.position}
                        </Badge>
                        <span className="text-xs text-gray-500">{injury.player.team}</span>
                        <Badge className={getStatusColor(injury.status)} size="sm">
                          {injury.status}
                        </Badge>
                      </div>

                      {/* Description */}
                      <p className="text-sm text-gray-700 mb-2">{injury.description}</p>

                      {/* Expected Return */}
                      {injury.expectedReturn && (
                        <div className="flex items-center space-x-1 mb-2">
                          <Calendar className="w-3 h-3 text-gray-400" />
                          <span className="text-xs text-gray-600">
                            Expected return: {injury.expectedReturn}
                          </span>
                        </div>
                      )}

                      {/* Recommendation */}
                      <div className="flex items-start space-x-1">
                        <Activity className="w-3 h-3 text-blue-500 mt-0.5 flex-shrink-0" />
                        <span className="text-xs text-blue-700 font-medium">
                          {injury.recommendation}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Urgency Badge */}
                  <div className="ml-2">
                    {getUrgencyBadge(injury.severity)}
                  </div>
                </div>
              </div>
            ))}

            {/* View Full Report Button */}
            <div className="pt-2 border-t">
              <Button variant="outline" size="sm" className="w-full">
                <AlertCircle className="w-4 h-4 mr-2" />
                View Full Injury Report
              </Button>
            </div>
          </div>
        ) : (
          <div className="text-center py-6 text-gray-500">
            <AlertCircle className="w-8 h-8 mx-auto mb-2 text-gray-300" />
            <p className="text-sm">No injury alerts</p>
            <p className="text-xs text-gray-400 mt-1">Your players are healthy! 🎉</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}