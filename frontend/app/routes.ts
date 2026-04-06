import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/index.tsx"),
  route("metrics", "routes/metrics.tsx"),
  route("detail/:nodeId", "routes/detail.$nodeId.tsx"),
] satisfies RouteConfig;
