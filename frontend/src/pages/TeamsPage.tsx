import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';

export function TeamsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Teams</h1>
        <p className="text-gray-600">Manage your fantasy teams</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your Teams</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">Team management features coming soon...</p>
        </CardContent>
      </Card>
    </div>
  );
}