import React from 'react';
import type { YahooDraftPick } from '../../services/yahooTypes';
import { cn } from '../../utils/cn';

interface YahooDraftBoardGridProps {
  draftedPlayers: YahooDraftPick[];
  numTeams: number;
  currentPick: number;
  userTeamKey: string;
}

export const YahooDraftBoardGrid: React.FC<YahooDraftBoardGridProps> = ({
  draftedPlayers,
  numTeams,
  currentPick,
  userTeamKey
}) => {
  const rounds = 15; // Standard number of rounds
  
  // Create grid data
  const grid: (YahooDraftPick | null)[][] = Array(rounds).fill(null).map(() => 
    Array(numTeams).fill(null)
  );

  // Fill grid with drafted players
  draftedPlayers.forEach(pick => {
    const round = pick.round - 1;
    const position = ((pick.pick - 1) % numTeams);
    
    // Handle snake draft
    const actualPosition = round % 2 === 0 ? position : numTeams - 1 - position;
    
    if (round < rounds) {
      grid[round][actualPosition] = pick;
    }
  });

  // Get team position for a given pick number
  const getTeamPosition = (pickNum: number): number => {
    const round = Math.floor((pickNum - 1) / numTeams);
    const position = (pickNum - 1) % numTeams;
    return round % 2 === 0 ? position : numTeams - 1 - position;
  };

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="border px-2 py-1 text-xs font-medium text-left bg-gray-50">
              Round
            </th>
            {Array.from({ length: numTeams }, (_, i) => (
              <th
                key={i}
                className={cn(
                  "border px-2 py-1 text-xs font-medium text-center",
                  i + 1 === parseInt(userTeamKey) ? "bg-primary text-white" : "bg-gray-50"
                )}
              >
                Team {i + 1}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {grid.map((round, roundIndex) => (
            <tr key={roundIndex}>
              <td className="border px-2 py-1 text-xs font-medium bg-gray-50">
                {roundIndex + 1}
              </td>
              {round.map((pick, teamIndex) => {
                const pickNumber = roundIndex * numTeams + 
                  (roundIndex % 2 === 0 ? teamIndex + 1 : numTeams - teamIndex);
                const isCurrentPick = pickNumber === currentPick;
                const isUserPick = pick && pick.team_key === userTeamKey;
                const isFuturePick = pickNumber > currentPick;

                return (
                  <td
                    key={teamIndex}
                    className={cn(
                      "border px-2 py-1 text-xs",
                      isCurrentPick && "bg-yellow-100 animate-pulse",
                      isUserPick && "bg-primary-light",
                      isFuturePick && "bg-gray-50 text-gray-400"
                    )}
                  >
                    {pick ? (
                      <div className="truncate" title={pick.player_name}>
                        {pick.player_name}
                      </div>
                    ) : (
                      <div className="text-center text-gray-400">
                        {isFuturePick ? pickNumber : '-'}
                      </div>
                    )}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};