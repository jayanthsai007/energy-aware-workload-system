import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { Badge } from "~/components/ui/badge";
import { Button } from "~/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts";
import { type Node } from "~/lib/api";
import { useNavigate } from "react-router";

interface NodeCardProps {
  node: Node;
  metrics?: number[];
}

export function NodeCard({ node, metrics }: NodeCardProps) {
  const navigate = useNavigate();
  
  // Generate sparkline data for mini chart
  const chartData = (metrics || Array.from({ length: 20 }, () => Math.floor(Math.random() * 70 + 20))).map((value, i) => ({
    x: i,
    cpu: value,
  }));

  const statusColor = node.status?.toLowerCase() === "active" || node.status?.toLowerCase() === "online" 
    ? "bg-green-500/20 text-green-700" 
    : "bg-red-500/20 text-red-700";

  const cpu = Math.floor(Math.random() * 70 + 20);
  const memory = Math.floor(Math.random() * 75 + 20);

  return (
    <Card className="hover:border-blue-500 transition-all hover:shadow-lg">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle className="text-lg">{node.node_id}</CardTitle>
            <CardDescription>CPU: {node.cpu_cores} cores | RAM: {node.memory}GB</CardDescription>
          </div>
          <Badge className={statusColor}>{node.status || "Unknown"}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>CPU Usage</span>
              <span className="font-semibold">{cpu}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{ width: `${cpu}%` }}
              />
            </div>
          </div>

          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Memory Usage</span>
              <span className="font-semibold">{memory}%</span>
            </div>
            <div className="w-full bg-slate-700 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all"
                style={{ width: `${memory}%` }}
              />
            </div>
          </div>
        </div>

        <div className="h-20">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="x" hide />
              <YAxis hide domain={[0, 100]} />
              <Line type="monotone" dataKey="cpu" stroke="#3b82f6" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <Button
          onClick={() => navigate(`/detail/${node.node_id}`)}
          className="w-full"
          variant="outline"
        >
          View Details
        </Button>
      </CardContent>
    </Card>
  );
}
