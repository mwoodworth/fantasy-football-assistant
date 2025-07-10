import { useState } from 'react';
import { X, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { Badge } from '../common/Badge';
import { Card } from '../common/Card';
import type { Player } from '../../types/player';
import { cn } from '../../utils/cn';

interface PlayerComparisonProps {
  isOpen: boolean;
  onClose: () => void;
  player1: Player | null;
  player2: Player | null;
  onSelectPlayer: (position: 1 | 2) => void;
}

interface ComparisonRow {
  label: string;
  player1Value: number | string;
  player2Value: number | string;
  unit?: string;
  higherIsBetter?: boolean;
}

export function PlayerComparison({
  isOpen,
  onClose,
  player1,
  player2,
  onSelectPlayer,
}: PlayerComparisonProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'projections' | 'trends'>('overview');

  const getComparisonData = (): ComparisonRow[] => {
    if (!player1 || !player2) return [];

    switch (activeTab) {
      case 'overview':
        return [
          {
            label: 'Position Rank',
            player1Value: player1.positionRank || 'N/A',
            player2Value: player2.positionRank || 'N/A',
            higherIsBetter: false,
          },
          {
            label: 'Average Points',
            player1Value: player1.averagePoints?.toFixed(1) || '0.0',
            player2Value: player2.averagePoints?.toFixed(1) || '0.0',
            unit: 'pts',
            higherIsBetter: true,
          },
          {
            label: 'Projected Points',
            player1Value: player1.projectedPoints?.toFixed(1) || '0.0',
            player2Value: player2.projectedPoints?.toFixed(1) || '0.0',
            unit: 'pts',
            higherIsBetter: true,
          },
          {
            label: 'Ownership',
            player1Value: player1.ownership?.toFixed(1) || '0.0',
            player2Value: player2.ownership?.toFixed(1) || '0.0',
            unit: '%',
            higherIsBetter: true,
          },
          {
            label: 'Start %',
            player1Value: player1.startPercentage?.toFixed(1) || '0.0',
            player2Value: player2.startPercentage?.toFixed(1) || '0.0',
            unit: '%',
            higherIsBetter: true,
          },
        ];
      
      case 'projections':
        return [
          {
            label: 'Season Projection',
            player1Value: player1.projectedTotalPoints?.toFixed(1) || '0.0',
            player2Value: player2.projectedTotalPoints?.toFixed(1) || '0.0',
            unit: 'pts',
            higherIsBetter: true,
          },
          {
            label: 'ROS Projection',
            player1Value: player1.restOfSeasonProjection?.toFixed(1) || '0.0',
            player2Value: player2.restOfSeasonProjection?.toFixed(1) || '0.0',
            unit: 'pts',
            higherIsBetter: true,
          },
          {
            label: 'Draft ADP',
            player1Value: player1.draftAveragePickPosition?.toFixed(1) || 'N/A',
            player2Value: player2.draftAveragePickPosition?.toFixed(1) || 'N/A',
            higherIsBetter: false,
          },
          {
            label: 'Next Game Proj',
            player1Value: player1.nextGameProjection?.toFixed(1) || '0.0',
            player2Value: player2.nextGameProjection?.toFixed(1) || '0.0',
            unit: 'pts',
            higherIsBetter: true,
          },
        ];
      
      case 'trends':
        return [
          {
            label: 'Consistency',
            player1Value: player1.consistencyRating?.toFixed(0) || '0',
            player2Value: player2.consistencyRating?.toFixed(0) || '0',
            unit: '%',
            higherIsBetter: true,
          },
          {
            label: 'Boom %',
            player1Value: player1.boomPercentage?.toFixed(1) || '0.0',
            player2Value: player2.boomPercentage?.toFixed(1) || '0.0',
            unit: '%',
            higherIsBetter: true,
          },
          {
            label: 'Bust %',
            player1Value: player1.bustPercentage?.toFixed(1) || '0.0',
            player2Value: player2.bustPercentage?.toFixed(1) || '0.0',
            unit: '%',
            higherIsBetter: false,
          },
          {
            label: 'Recent Trend',
            player1Value: player1.recentTrend || 'stable',
            player2Value: player2.recentTrend || 'stable',
          },
        ];
      
      default:
        return [];
    }
  };

  const getWinner = (row: ComparisonRow): 1 | 2 | null => {
    if (typeof row.player1Value === 'string' || typeof row.player2Value === 'string') {
      return null;
    }
    
    const val1 = parseFloat(row.player1Value.toString());
    const val2 = parseFloat(row.player2Value.toString());
    
    if (isNaN(val1) || isNaN(val2) || val1 === val2) return null;
    
    if (row.higherIsBetter) {
      return val1 > val2 ? 1 : 2;
    } else {
      return val1 < val2 ? 1 : 2;
    }
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600" />;
      default:
        return <Minus className="w-4 h-4 text-gray-400" />;
    }
  };

  const comparisonData = getComparisonData();

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Player Comparison"
      className="max-w-4xl"
    >
      <div className="space-y-6">
        {/* Player Selection */}
        <div className="grid grid-cols-2 gap-4">
          <Card 
            className={cn(
              "p-4 cursor-pointer border-2 transition-colors",
              player1 ? "border-primary-500 bg-primary-50" : "border-gray-200 hover:border-gray-300"
            )}
            onClick={() => onSelectPlayer(1)}
          >
            {player1 ? (
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">{player1.name}</h3>
                <p className="text-sm text-gray-600">
                  {player1.team} • {player1.position} • #{player1.positionRank}
                </p>
                <Badge
                  variant={player1.injuryStatus === 'Healthy' ? 'success' : 'warning'}
                  size="sm"
                >
                  {player1.injuryStatus}
                </Badge>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-500">Click to select Player 1</p>
              </div>
            )}
          </Card>

          <Card 
            className={cn(
              "p-4 cursor-pointer border-2 transition-colors",
              player2 ? "border-primary-500 bg-primary-50" : "border-gray-200 hover:border-gray-300"
            )}
            onClick={() => onSelectPlayer(2)}
          >
            {player2 ? (
              <div className="space-y-2">
                <h3 className="font-semibold text-lg">{player2.name}</h3>
                <p className="text-sm text-gray-600">
                  {player2.team} • {player2.position} • #{player2.positionRank}
                </p>
                <Badge
                  variant={player2.injuryStatus === 'Healthy' ? 'success' : 'warning'}
                  size="sm"
                >
                  {player2.injuryStatus}
                </Badge>
              </div>
            ) : (
              <div className="text-center py-4">
                <p className="text-gray-500">Click to select Player 2</p>
              </div>
            )}
          </Card>
        </div>

        {/* Comparison Tabs */}
        {player1 && player2 && (
          <>
            <div className="flex gap-2 border-b">
              <button
                className={cn(
                  "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
                  activeTab === 'overview'
                    ? "border-primary-500 text-primary-700"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                )}
                onClick={() => setActiveTab('overview')}
              >
                Overview
              </button>
              <button
                className={cn(
                  "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
                  activeTab === 'projections'
                    ? "border-primary-500 text-primary-700"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                )}
                onClick={() => setActiveTab('projections')}
              >
                Projections
              </button>
              <button
                className={cn(
                  "px-4 py-2 text-sm font-medium border-b-2 transition-colors",
                  activeTab === 'trends'
                    ? "border-primary-500 text-primary-700"
                    : "border-transparent text-gray-600 hover:text-gray-900"
                )}
                onClick={() => setActiveTab('trends')}
              >
                Trends
              </button>
            </div>

            {/* Comparison Table */}
            <div className="space-y-2">
              {comparisonData.map((row, index) => {
                const winner = getWinner(row);
                
                return (
                  <div 
                    key={row.label}
                    className={cn(
                      "grid grid-cols-7 gap-4 items-center p-3 rounded",
                      index % 2 === 0 ? "bg-gray-50" : ""
                    )}
                  >
                    <div className="col-span-3 text-sm font-medium text-gray-700">
                      {row.label}
                    </div>
                    <div 
                      className={cn(
                        "col-span-2 text-center",
                        winner === 1 && "font-semibold text-green-600"
                      )}
                    >
                      {row.label === 'Recent Trend' && getTrendIcon(player1.recentTrend)}
                      <span className="text-sm">
                        {row.player1Value}
                        {row.unit && ` ${row.unit}`}
                      </span>
                    </div>
                    <div 
                      className={cn(
                        "col-span-2 text-center",
                        winner === 2 && "font-semibold text-green-600"
                      )}
                    >
                      {row.label === 'Recent Trend' && getTrendIcon(player2.recentTrend)}
                      <span className="text-sm">
                        {row.player2Value}
                        {row.unit && ` ${row.unit}`}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Recommendation */}
            <Card className="p-4 bg-blue-50 border-blue-200">
              <h4 className="font-semibold text-blue-900 mb-2">Recommendation</h4>
              <p className="text-sm text-blue-800">
                Based on the comparison, {player1.projectedPoints > player2.projectedPoints ? player1.name : player2.name} appears
                to be the better choice for this week, with higher projected points and {
                  player1.consistencyRating > player2.consistencyRating 
                    ? 'better consistency' 
                    : 'comparable performance'
                }.
              </p>
            </Card>
          </>
        )}
      </div>
    </Modal>
  );
}