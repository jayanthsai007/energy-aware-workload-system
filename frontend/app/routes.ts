import { type RouteConfig, layout, index, route } from "@react-router/dev/routes";

export default [
  layout("root.tsx", [
    index("routes/index.tsx"),
    route("metrics", "routes/metrics.tsx"),
    route("detail/:nodeId", "routes/detail.$nodeId.tsx"),
  ]),
] satisfies RouteConfig;
