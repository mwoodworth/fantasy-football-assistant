import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';

export function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
        <p className="text-gray-600">Deep dive into your team's performance</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Performance Analytics</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">Analytics dashboard coming soon...</p>
        </CardContent>
      </Card>
    </div>
  );
}