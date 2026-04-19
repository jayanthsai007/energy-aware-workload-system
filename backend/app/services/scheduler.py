import asyncio
import time
import numpy as np

from app.services.task_queue import get_task, add_task
from app.websocket.connection_manager import manager
from app.database import SessionLocal
from app.models.node_model import Node
from app.models.metrics_model import Metrics
from app.models.task_model import Task

from app.services.script_analyzer import extract_script_features

_scheduler_model = None


def get_scheduler_model():
    global _scheduler_model
    if _scheduler_model is None:
        from ml.models.model_loader import ModelLoader
        _scheduler_model = ModelLoader()
    return _scheduler_model


async def scheduler_loop():
    print("🚀 Scheduler started...")

    # Load pending tasks into queue on startup
    db = SessionLocal()
    try:
        pending_tasks = db.query(Task).filter(Task.status == "pending").all()
        for task in pending_tasks:
            add_task(task)
        print(f"📋 Loaded {len(pending_tasks)} pending tasks into queue")
    except Exception as e:
        print(f"[ERROR] Failed to load pending tasks: {e}")
    finally:
        db.close()

    while True:
        task = get_task()

        if not task:
            await asyncio.sleep(2)
            continue

        db = SessionLocal()

        try:
            # =========================
            # 🔥 REFRESH TASK
            # =========================
            task = db.query(Task).filter_by(id=task.id).first()
            if not task:
                continue

            print(f"[SCHEDULER] Processing task {task.id}")

            # =========================
            # 🔥 RETRY LIMIT
            # =========================
            if task.retry_count >= task.max_retries:
                print(f"[FAILED] Task {task.id} exceeded retries")
                task.status = "failed"
                db.commit()
                continue

            # =========================
            # 🔥 ACTIVE NODES
            # =========================
            nodes = db.query(Node).filter(Node.status == "ACTIVE").all()
            print(f"[SCHEDULER] Found {len(nodes)} active nodes")

            if not nodes:
                print("[SCHEDULER] No active nodes")
                task.retry_count += 1
                task.status = "pending"
                db.commit()
                add_task(task)
                continue

            # =========================
            # 🔥 SCRIPT FEATURES
            # =========================
            script_features = extract_script_features(
                task.script,
                task.language
            )

            node_scores = []

            # =========================
            # 🔍 NODE SCORING
            # =========================
            for node in nodes:

                # 🔥 CRITICAL FIX: check WS connection
                if not await manager.is_node_connected(node.node_id):
                    print(f"[SKIP] Node {node.node_id} not connected")
                    continue

                metrics = (
                    db.query(Metrics)
                    .filter(Metrics.node_id == node.node_id)
                    .order_by(Metrics.timestamp.desc())
                    .limit(10)
                    .all()
                )

                if len(metrics) < 1:  # 🔥 TEMP: lowered for testing
                    print(
                        f"[SKIP] Node {node.node_id} insufficient metrics ({len(metrics)})")
                    continue

                metrics = list(reversed(metrics))

                try:
                    ts = np.array([
                        [
                            m.cpu_usage / 100,
                            m.memory_usage / 100,
                            (m.temperature or 50) / 100,
                            (m.cpu_usage / 100) * 1.5
                        ]
                        for m in metrics
                    ])

                    static = np.array([
                        node.cpu_cores / 16,
                        node.total_memory / 32,
                        node.cpu_frequency / 5
                    ])

                    script = np.array([
                        script_features["file_size"],
                        script_features["line_count"],
                        script_features["imports"],
                        script_features["functions"],
                        script_features["classes"],
                        script_features["language"]
                    ])

                    model = get_scheduler_model()
                    score = model.predict(ts, static, script)

                    cpu_avg = np.mean([m.cpu_usage for m in metrics]) / 100
                    final_score = score + (cpu_avg * 0.05)

                    print(f"[ML] Node {node.node_id} → {final_score:.4f}")

                    node_scores.append((node, final_score))

                except Exception as e:
                    print(f"[ML ERROR] Node {node.node_id}: {e}")
                    continue

            # =========================
            # ❌ NO NODES
            # =========================
            if not node_scores:
                print("[SCHEDULER] No suitable nodes after ML")

                task.retry_count += 1
                task.status = "pending"
                db.commit()

                add_task(task)
                continue

            # =========================
            # SORT BEST NODE
            # =========================
            node_scores.sort(key=lambda x: x[1])

            assigned = False

            # =========================
            # 🚀 ASSIGN TASK
            # =========================
            for node, score in node_scores:
                print(f"[TRY] Node {node.node_id}")

                success = await manager.send_to_node(node.node_id, {
                    "type": "execute",
                    "script": task.script,
                    "language": task.language,
                    "task_id": task.id
                })

                if success:
                    print(f"[ASSIGNED] Task {task.id} → {node.node_id}")

                    task.status = "running"
                    task.assigned_node = node.node_id
                    db.commit()

                    assigned = True

                    # =========================
                    # ⏱ TIMEOUT WATCHER
                    # =========================
                    start_time = time.time()

                    while True:
                        await asyncio.sleep(1)
                        db.refresh(task)

                        # ✅ COMPLETED
                        if task.status == "completed":
                            print(f"[SUCCESS] Task {task.id}")
                            break

                        # ⏱ TIMEOUT
                        if time.time() - start_time > task.timeout:
                            print(f"[TIMEOUT] Task {task.id}")

                            task.retry_count += 1
                            task.status = "pending"
                            task.assigned_node = None
                            db.commit()

                            add_task(task)
                            break

                    break

                else:
                    print(f"[FAIL] Node {node.node_id}")

            # =========================
            # ❌ ALL FAILED
            # =========================
            if not assigned:
                print(f"[SCHEDULER] All nodes failed for {task.id}")

                task.retry_count += 1
                task.status = "pending"
                db.commit()

                add_task(task)

        except Exception as e:
            print("[SCHEDULER ERROR]", e)

        finally:
            db.close()

        await asyncio.sleep(1)
