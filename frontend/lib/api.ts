const BASE_URL = "http://127.0.0.1:8000";

// Node types
export interface Node {
  node_id: string;
  status: string;
  cpu_cores: number;
  memory: number;
}

// Metrics types
export interface Metrics {
  cpu: number;
  memory: number;
  temperature: number;
  timestamp: string;
}

// Execution metrics types
export interface ExecutionMetrics {
  execution_time: number;
  cpu_avg: number;
  memory_avg: number;
  cpu_peak: number;
  memory_peak: number;
  timestamp: string;
}

// Model performance types
export interface ModelPerformance {
  [key: string]: any;
}

// Retrain response types
export interface RetrainResponse {
  status: string;
  message: string;
  total_samples: number;
}

export async function getNodes(): Promise<Node[]> {
  try {
    const response = await fetch(`${BASE_URL}/nodes`);
    if (!response.ok) {
      console.error(`Failed to fetch nodes: ${response.statusText}`);
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching nodes:", error);
    return [];
  }
}

export async function getMetrics(): Promise<Metrics[]> {
  try {
    const response = await fetch(`${BASE_URL}/metrics`);
    if (!response.ok) {
      console.error(`Failed to fetch metrics: ${response.statusText}`);
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching metrics:", error);
    return [];
  }
}

export async function getExecutions(): Promise<ExecutionMetrics[]> {
  try {
    const response = await fetch(`${BASE_URL}/execution-metrics`);
    if (!response.ok) {
      console.error(`Failed to fetch executions: ${response.statusText}`);
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching executions:", error);
    return [];
  }
}

export async function getModelPerformance(): Promise<ModelPerformance[]> {
  try {
    const response = await fetch(`${BASE_URL}/model-performance`);
    if (!response.ok) {
      console.error(`Failed to fetch model performance: ${response.statusText}`);
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error("Error fetching model performance:", error);
    return [];
  }
}

export async function retrainModel(): Promise<RetrainResponse | []> {
  try {
    const response = await fetch(`${BASE_URL}/retrain`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok) {
      console.error(`Failed to retrain model: ${response.statusText}`);
      return [];
    }
    return await response.json();
  } catch (error) {
    console.error("Error retraining model:", error);
    return [];
  }
}
