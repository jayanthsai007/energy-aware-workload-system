import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { Button } from "~/components/ui/button";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { ArrowLeft, Cpu, HardDrive, Zap } from "lucide-react";

interface NodeDetailProps {
  nodeId: string;
  onBack: () => void;
}

export function NodeDetail({ nodeId, onBack }: NodeDetailProps) {
  // Generate performance data
  const performanceData = Array.from({ length: 50 }, (_, i) => ({
    index: i,
    cpu: Math.floor(Math.random() * 50 + 30),
    memory: Math.floor(Math.random() * 65 + 30),
  }));

  const cpu = Math.floor(Math.random() * 50 + 30);
  const memory = Math.floor(Math.random() * 65 + 30);
  const energy = Math.floor(Math.random() * 150 + 50);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="outline" size="icon" onClick={onBack}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <h1 className="text-4xl font-bold">Node Details: {nodeId}</h1>
      </div>

      {/* Top Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">CPU Usage</CardTitle>
            <Cpu className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{cpu}%</div>
            <p className="text-xs text-slate-500">Current usage</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Memory Usage</CardTitle>
            <HardDrive className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{memory}%</div>
            <p className="text-xs text-slate-500">Current usage</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Energy</CardTitle>
            <Zap className="h-4 w-4 text-yellow-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{energy}W</div>
            <p className="text-xs text-slate-500">Power consumption</p>
          </CardContent>
        </Card>
      </div>

      {/* Performance Graph */}
      <Card>
        <CardHeader>
          <CardTitle>Performance Metrics</CardTitle>
          <CardDescription>CPU and Memory usage over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="index" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
              <Legend />
              <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} dot={false} name="CPU %" />
              <Line type="monotone" dataKey="memory" stroke="#a855f7" strokeWidth={2} dot={false} name="Memory %" />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Device Specifications */}
      <Card>
        <CardHeader>
          <CardTitle>Device Specifications</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">CPU</p>
              <p className="font-semibold">Intel i7-9700K</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">Memory</p>
              <p className="font-semibold">16 GB DDR4</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">Storage</p>
              <p className="font-semibold">512 GB SSD</p>
            </div>
            <div className="p-3 rounded-lg bg-slate-900 border border-slate-700">
              <p className="text-xs text-slate-400 mb-1">OS</p>
              <p className="font-semibold">Linux Ubuntu</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Model Input */}
      <Card>
        <CardHeader>
          <CardTitle>Model Input</CardTitle>
          <CardDescription>Current metrics for ML model</CardDescription>
        </CardHeader>
        <CardContent>
          <pre className="bg-slate-900 p-4 rounded border border-slate-700 text-sm overflow-x-auto text-slate-300">
            {JSON.stringify(
              {
                node_id: nodeId,
                cpu: cpu,
                memory: memory,
                energy: energy,
                timestamp: new Date().toISOString(),
              },
              null,
              2
            )}
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
