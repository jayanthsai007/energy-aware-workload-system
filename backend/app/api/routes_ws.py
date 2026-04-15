from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.connection_manager import manager
from app.database import SessionLocal
from app.models.node_model import Node
from app.models.execution_metrics_model import ExecutionMetrics
from app.models.task_model import Task

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)

    print("[WS] Client connected")

    node_id = None

    # =========================
    # 🔥 SEND CURRENT NODE STATUS (SAFE)
    # =========================
    db = SessionLocal()
    try:
        nodes = db.query(Node).all()

        for node in nodes:
            try:
                await websocket.send_json({
                    "type": "node_status",
                    "data": {
                        "node_id": node.node_id,
                        "status": node.status
                    }
                })
            except Exception as e:
                print("[WS INIT SEND ERROR]", e)
                break

    finally:
        db.close()

    # =========================
    # 🔥 MAIN LOOP
    # =========================
    try:
        while True:
            data = await websocket.receive_json()

            # =========================
            # 🔥 NODE REGISTRATION
            # =========================
            if data.get("type") == "register":
                node_id = data.get("node_id")
                await manager.register_node(node_id, websocket)

            # =========================
            # 🔥 LOG STREAMING
            # =========================
            elif data.get("type") == "execution_log":
                await manager.broadcast({
                    "type": "execution_log",
                    "data": data.get("data")
                })

            # =========================
            # 🔥 EXECUTION RESULT
            # =========================
            elif data.get("type") == "execution_result":
                print("[WS] Execution result received")

                result = data.get("data", {})
                task_id = result.get("task_id")
                status = result.get("status", "success")

                db = SessionLocal()

                try:
                    # =========================
                    # 🔥 UPDATE TASK STATUS
                    # =========================
                    if task_id:
                        task = db.query(Task).filter(
                            Task.id == task_id).first()

                        if task:
                            if status == "success":
                                task.status = "completed"
                            else:
                                task.status = "failed"

                            # Store execution results
                            task.output = result.get("output", "")
                            task.error = result.get("error", "")
                            task.execution_time = result.get(
                                "execution_time", 0)

                            db.commit()
                            print(
                                f"[TASK] Updated → {task_id} ({task.status})")
                        else:
                            print(f"[TASK] Not found → {task_id}")

                    # =========================
                    # 🔥 STORE ML FEEDBACK
                    # =========================
                    feedback = ExecutionMetrics(
                        node_id=node_id,
                        script_id=task_id or "ws_script",
                        language=result.get("language", "python"),

                        execution_time=result.get("execution_time", 0),

                        cpu_avg=result.get("cpu_avg", 0),
                        cpu_peak=result.get("cpu_peak", 0),

                        memory_avg=result.get("memory_avg", 0),
                        memory_peak=result.get("memory_peak", 0),
                    )

                    db.add(feedback)
                    db.commit()

                    print(f"[FEEDBACK] Stored via WS for node {node_id}")

                except Exception as e:
                    print("[DB ERROR]", e)

                finally:
                    db.close()

                # =========================
                # 🔥 BROADCAST RESULT
                # =========================
                await manager.broadcast({
                    "type": "execution_result",
                    "data": result
                })

    except WebSocketDisconnect:
        print("[WS] Client disconnected")

        # ✅ FIX: async disconnect
        await manager.disconnect(websocket)

    except Exception as e:
        print("[WS ERROR]", e)

        # ✅ Safety cleanup
        await manager.disconnect(websocket)
