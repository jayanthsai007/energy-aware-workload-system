# Energy-Aware Workload System

Energy-Aware Workload System is a distributed workload execution platform that monitors node health, collects live device metrics, schedules tasks across available nodes, and visualizes execution behavior in a React dashboard.

The project has three main parts:

- `backend/`: FastAPI server, task routing, node registry, metrics storage, execution history, scheduler scoring, and retraining hooks
- `frontend/`: React dashboard for node monitoring, task visibility, temperature/memory charts, and node detail pages
- `Node_client/`: local node agent and desktop UI used by worker machines to register themselves, send metrics, and run Python/Java tasks

## Features

- Node registration and heartbeat tracking
- Live CPU, memory, and temperature metric collection
- Task dispatch through backend queueing and websocket communication
- Python execution support
- Java execution support through Dockerized executors
- Dashboard for system-wide monitoring
- Node details page with live metric trends and workload visibility
- Execution metrics history and scheduler score display
- SQLite-backed persistence for local development

## Project Structure

```text
energy-aware-workload-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── database.py
│   │   └── main.py
│   ├── ml/
│   ├── node_agent.py
│   ├── build_node_agent_exe.bat
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
├── Node_client/
│   ├── docker/
│   │   ├── java-executor/
│   │   └── python-executor/
│   ├── node_agent.py
│   ├── node_ui.py
│   └── node_config.json
└── README.md
```

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, NumPy, WebSockets
- Frontend: React, React Router, Recharts
- Node execution: Python, Java, Docker
- Local desktop node UI: Tkinter

## Prerequisites

Install these before running the project:

- Python 3.12 or 3.13
- Node.js 18+ and npm
- Docker Desktop
- Java support in Docker only, so a local JDK is not required for `Node_client`

## Backend Setup

Create and activate a virtual environment inside `backend/`.

Windows PowerShell:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install backend dependencies.

If `backend/requirements.txt` is populated in your local copy, use:

```powershell
pip install -r requirements.txt
```

If your `requirements.txt` is still empty, install the packages required by the current codebase:

```powershell
pip install fastapi uvicorn sqlalchemy requests psutil websockets pydantic numpy
```

## Frontend Setup

Install frontend dependencies:

```powershell
cd frontend
npm install
```

The frontend is configured with a proxy to:

```text
http://127.0.0.1:8000
```

## Node Client Setup

The node client is the worker-side application that:

- starts a local API on `http://127.0.0.1:9000`
- connects to the backend websocket
- sends heartbeat and live metrics
- runs Python and Java tasks

No separate package manifest exists for `Node_client`, so it uses your Python environment. Install the packages it imports:

```powershell
pip install fastapi uvicorn requests psutil websockets pydantic
```

## Docker Executors

Java execution uses Docker images from:

- `Node_client/docker/java-executor`
- `Node_client/docker/python-executor`

The current node agent can auto-build missing executor images on demand. If you want to build them manually, run:

```powershell
docker build -t energy-node-python:latest -f Node_client/docker/python-executor/Dockerfile Node_client/docker/python-executor
docker build -t energy-node-java:latest -f Node_client/docker/java-executor/Dockerfile Node_client/docker/java-executor
```

## How to Run the Project

Start the services in this order.

### 1. Start the backend

From `backend/` with the virtual environment activated:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Backend URLs:

- API root: `http://127.0.0.1:8000`
- Health: `http://127.0.0.1:8000/health`

The backend creates a local SQLite database at:

```text
backend/energy.db
```

### 2. Start the frontend

From `frontend/`:

```powershell
npm start
```

Frontend URL:

- `http://127.0.0.1:3000`

### 3. Start the node client

Open a new terminal and run:

```powershell
cd Node_client
python node_ui.py
```

This starts the desktop UI and, if needed, launches the local node agent automatically.

Node client local endpoints:

- Local agent health: `http://127.0.0.1:9000/health`
- Local agent run endpoint: `http://127.0.0.1:9000/run`

## Optional: Run the Simple Backend Node Agent

There is also a separate `backend/node_agent.py` in the repository. It exposes a simpler local execution service and can be run with:

```powershell
cd backend
python node_agent.py
```

By default it runs on:

```text
http://127.0.0.1:8001
```

Most recent task flows in this repo use `Node_client/node_agent.py` together with `Node_client/node_ui.py`.

## Common Workflow

1. Start the backend
2. Start the frontend
3. Start `Node_client/node_ui.py`
4. Wait for the node to register and begin sending heartbeat/metrics
5. Open the dashboard in the browser
6. Submit Python or Java code from the node UI
7. Watch live updates in the dashboard and node details page

## Key Backend Endpoints

- `GET /health`: backend health check
- `GET /active-nodes`: active/online nodes
- `GET /metrics`: latest metrics samples
- `POST /metrics`: ingest node metrics
- `POST /heartbeat`: update node liveness
- `POST /execute`: dispatch a task to a node
- `GET /task/{task_id}`: fetch task status/result
- `GET /execution-metrics`: recent execution history
- `GET /node-inputs`: latest task input per node
- `GET /nodes/{node_id}/composite-score`: scheduler score for a node
- `WS /ws`: node websocket channel for execution dispatch/results

## Notes About Persistence

- The backend uses SQLite for local persistence.
- Nodes, metrics, heartbeats, and execution history are stored in the local database.
- The backend also contains ML-related files under `backend/ml/` for scheduler scoring and retraining workflows.

## Troubleshooting

### Backend does not start

- Make sure the backend virtual environment is active
- Confirm required Python packages are installed
- Check whether port `8000` is already in use

### Frontend cannot fetch data

- Confirm the backend is running on `127.0.0.1:8000`
- Check browser console errors
- Verify the frontend proxy in `frontend/package.json`

### Node UI submits tasks but nothing runs

- Confirm `Node_client/node_ui.py` can reach `http://127.0.0.1:9000/health`
- Confirm the backend is reachable at `http://127.0.0.1:8000/health`
- Ensure Docker Desktop is running for Java execution

### Java tasks fail

- Make sure Docker Desktop is running
- Let the node agent auto-build missing executor images, or build them manually
- Restart the node UI if you recently changed `Node_client/node_agent.py` so the newer agent version is loaded

### No live metrics appear in the dashboard

- Wait for the node to register and send heartbeat
- Confirm `POST /metrics` is succeeding in backend logs
- Keep `Node_client/node_ui.py` and the backend running at the same time

## Development Notes

- Backend app entrypoint: [backend/app/main.py](/abs/path/c:/Users/91960/energy-aware-workload-system/backend/app/main.py)
- Frontend app entrypoint: [frontend/src/App.js](/abs/path/c:/Users/91960/energy-aware-workload-system/frontend/src/App.js)
- Worker agent: [Node_client/node_agent.py](/abs/path/c:/Users/91960/energy-aware-workload-system/Node_client/node_agent.py)
- Desktop node UI: [Node_client/node_ui.py](/abs/path/c:/Users/91960/energy-aware-workload-system/Node_client/node_ui.py)

## Future Improvements

- Add a complete locked backend `requirements.txt`
- Add `.env`-based configuration for ports and backend URL
- Add production deployment instructions
- Add automated tests for task dispatch and live metric streaming
