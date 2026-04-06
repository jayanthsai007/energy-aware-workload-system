import { NodeGrid } from "~/components/node-grid";

export function meta() {
  return [
    { title: "Node Dashboard - Energy Aware" },
    { name: "description", content: "Monitor your distributed nodes and their performance" },
  ];
}

export default function Home() {
  return (
    <div className="py-8">
      <NodeGrid />
    </div>
  );
}
