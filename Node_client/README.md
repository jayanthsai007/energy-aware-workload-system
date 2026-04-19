# Node Software Packaging

This directory contains the node client software that can be packaged into a single Windows executable.

## Files

- `node_ui.py` - Main UI application (entry point)
- `node_agent.py` - Background agent for execution
- `NodeSoftware.spec` - PyInstaller spec file
- `build_exe.bat` - Build script for creating the executable

## Building the Package

1. Ensure Python dependencies are installed (use backend venv)
2. Run `build_exe.bat` or `pyinstaller NodeSoftware.spec`
3. The executable will be created in `dist/NodeSoftware.exe`

## Features

- ✅ Single executable deployment
- ✅ Automatic agent startup and management
- ✅ Real-time device metrics display
- ✅ Script execution and monitoring
- ✅ WebSocket communication with backend
- ✅ Single instance enforcement
- ✅ First-run setup with permissions

## First Run Setup

On first launch, the software will:

- Create node configuration
- Set up permissions
- Register with backend
- Start background services

## Usage

1. Double-click `NodeSoftware.exe`
2. The UI will start and automatically launch the agent
3. Submit scripts for distributed execution
4. Monitor device metrics in real-time

## Architecture

- **UI (node_ui.py)**: Tkinter-based IDE for script editing
- **Agent (node_agent.py)**: FastAPI server handling backend communication
- **Single WebSocket**: Agent maintains exclusive backend connection
- **Local API**: UI communicates with agent via HTTP on port 9000
