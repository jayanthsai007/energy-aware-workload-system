import { useEffect, useState } from "react";
import { getNodes } from "~/lib/api";
import { type Node } from "~/lib/api";
import { NodeCard } from "./node-card";
import { AlertCircle, Loader2 } from "lucide-react";
import { Alert, AlertDescription } from "~/components/ui/alert";

export function NodeGrid() {
  const [nodes, setNodes] = useState<Node[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchNodes = async () => {
      try {
        setLoading(true);
        const data = await getNodes();
        if (Array.isArray(data) && data.length > 0) {
          setNodes(data);
          setError(null);
        } else {
          setError("No nodes connected");
        }
      } catch (err) {
        setError("Failed to fetch nodes");
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchNodes();
    // Refresh every 10 seconds
    const interval = setInterval(fetchNodes, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-500" />
          <p className="text-slate-400">Loading nodes...</p>
        </div>
      </div>
    );
  }

  if (error && nodes.length === 0) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold">Node Dashboard</h1>
        <p className="text-slate-400 mt-2">Monitor your distributed nodes and their performance</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {nodes.map((node) => (
          <NodeCard key={node.node_id} node={node} />
        ))}
      </div>

      {nodes.length === 0 && !loading && !error && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>No nodes available</AlertDescription>
        </Alert>
      )}
    </div>
  );
}
