import { useEffect, useState } from "react";
import { getMetrics, getExecutions, type Metrics, type ExecutionMetrics } from "~/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "~/components/ui/card";
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { Loader2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "~/components/ui/alert";

export default function Metrics() {
  const [metrics, setMetrics] = useState<Metrics[]>([]);
  const [executions, setExecutions] = useState<ExecutionMetrics[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [metricsData, executionsData] = await Promise.all([
          getMetrics(),
          getExecutions(),
        ]);
        setMetrics(metricsData);
        setExecutions(executionsData);
        setError(null);
      } catch (err) {
        setError("Failed to fetch metrics");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && metrics.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-500" />
          <p className="text-slate-400">Loading metrics...</p>
        </div>
      </div>
    );
  }

  if (error && metrics.length === 0) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const metricsChartData = metrics.slice().reverse().map((m, i) => ({
    index: i,
    cpu: m.cpu,
    memory: m.memory,
    temperature: m.temperature,
  }));

  const executionsChartData = executions.slice().reverse().map((e, i) => ({
    index: i,
    execution_time: e.execution_time,
    cpu_avg: e.cpu_avg,
    memory_avg: e.memory_avg,
  }));

  return (
    <div className="space-y-6 py-8">
      <div>
        <h1 className="text-4xl font-bold">System Metrics</h1>
        <p className="text-slate-400 mt-2">Real-time performance and execution metrics</p>
      </div>

      {/* Device Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Device Metrics</CardTitle>
          <CardDescription>CPU, Memory, and Temperature over time</CardDescription>
        </CardHeader>
        <CardContent>
          {metricsChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={metricsChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="index" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
                <Legend />
                <Line type="monotone" dataKey="cpu" stroke="#3b82f6" strokeWidth={2} dot={false} name="CPU %" />
                <Line type="monotone" dataKey="memory" stroke="#a855f7" strokeWidth={2} dot={false} name="Memory %" />
                <Line type="monotone" dataKey="temperature" stroke="#f97316" strokeWidth={2} dot={false} name="Temp (°C)" />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-400">No metrics data available</p>
          )}
        </CardContent>
      </Card>

      {/* Execution Metrics */}
      <Card>
        <CardHeader>
          <CardTitle>Execution Metrics</CardTitle>
          <CardDescription>Execution time and resource usage statistics</CardDescription>
        </CardHeader>
        <CardContent>
          {executionsChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={executionsChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                <XAxis dataKey="index" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" />
                <Tooltip contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155" }} />
                <Legend />
                <Bar dataKey="execution_time" fill="#3b82f6" name="Execution Time (ms)" />
                <Bar dataKey="cpu_avg" fill="#a855f7" name="CPU Avg %" />
                <Bar dataKey="memory_avg" fill="#f97316" name="Memory Avg %" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-slate-400">No execution data available</p>
          )}
        </CardContent>
      </Card>

      {/* Metrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Latest Metrics</CardTitle>
          <CardDescription>Last 10 metric readings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-2 px-4">CPU %</th>
                  <th className="text-left py-2 px-4">Memory %</th>
                  <th className="text-left py-2 px-4">Temperature °C</th>
                  <th className="text-left py-2 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {metrics.slice(0, 10).map((m, i) => (
                  <tr key={i} className="border-b border-slate-800 hover:bg-slate-900/50">
                    <td className="py-2 px-4">{m.cpu}</td>
                    <td className="py-2 px-4">{m.memory}</td>
                    <td className="py-2 px-4">{m.temperature}</td>
                    <td className="py-2 px-4 text-slate-400 text-xs">{new Date(m.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Execution Table */}
      <Card>
        <CardHeader>
          <CardTitle>Latest Executions</CardTitle>
          <CardDescription>Last 10 execution records</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-2 px-4">Execution Time (ms)</th>
                  <th className="text-left py-2 px-4">CPU Avg %</th>
                  <th className="text-left py-2 px-4">Memory Avg %</th>
                  <th className="text-left py-2 px-4">CPU Peak %</th>
                  <th className="text-left py-2 px-4">Memory Peak %</th>
                  <th className="text-left py-2 px-4">Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {executions.slice(0, 10).map((e, i) => (
                  <tr key={i} className="border-b border-slate-800 hover:bg-slate-900/50">
                    <td className="py-2 px-4">{e.execution_time}</td>
                    <td className="py-2 px-4">{e.cpu_avg}</td>
                    <td className="py-2 px-4">{e.memory_avg}</td>
                    <td className="py-2 px-4">{e.cpu_peak}</td>
                    <td className="py-2 px-4">{e.memory_peak}</td>
                    <td className="py-2 px-4 text-slate-400 text-xs">{new Date(e.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
