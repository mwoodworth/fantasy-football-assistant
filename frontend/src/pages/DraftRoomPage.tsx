import { useParams, useLocation, Navigate } from 'react-router-dom';
import { DraftBoard } from '../components/draft/DraftBoard';

export function DraftRoomPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const location = useLocation();
  
  // Get league data from navigation state
  const { league } = location.state || {};
  
  // Parse sessionId to number if provided
  const sessionIdNum = sessionId ? parseInt(sessionId, 10) : undefined;
  
  // If no league data, redirect back to leagues page
  if (!league || !league.id) {
    return <Navigate to="/espn/leagues" replace />;
  }
  
  return (
    <div className="container mx-auto py-6">
      <DraftBoard 
        sessionId={sessionIdNum} 
        leagueId={league.id} 
      />
    </div>
  );
}