import { Card, CardContent, CardHeader, CardTitle } from '../components/common/Card';

export function AIAssistantPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">AI Assistant</h1>
        <p className="text-gray-600">Get AI-powered fantasy football insights</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Chat with AI</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">AI chat interface coming soon...</p>
        </CardContent>
      </Card>
    </div>
  );
}