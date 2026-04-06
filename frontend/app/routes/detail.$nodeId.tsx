import { useNavigate, useParams } from "react-router";
import { NodeDetail } from "~/components/node-detail";

export default function DetailPage() {
  const { nodeId } = useParams();
  const navigate = useNavigate();

  if (!nodeId) {
    return <div>Node not found</div>;
  }

  return (
    <div className="py-8">
      <NodeDetail nodeId={nodeId} onBack={() => navigate("/")} />
    </div>
  );
}
