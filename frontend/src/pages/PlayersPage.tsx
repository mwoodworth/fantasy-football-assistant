import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';

export function PlayersPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Players</h1>
        <p className="text-gray-600">Search and analyze NFL players</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Player Search</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">Player search and analysis features coming soon...</p>
        </CardContent>
      </Card>
    </div>
  );
}