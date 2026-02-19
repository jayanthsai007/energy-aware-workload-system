from fastapi import APIRouter
import subprocess
import time
import tempfile
import os

router = APIRouter()


@router.post("/node-execute")
def execute_script(payload: dict):
    script_content = payload.get("script")

    if not script_content:
        return {"status": "error", "message": "No script provided"}

    try:
        start_time = time.time()

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp:
            temp.write(script_content.encode("utf-8"))
            temp_filename = temp.name

        # Execute script
        result = subprocess.run(
            ["python", temp_filename],
            capture_output=True,
            text=True,
            timeout=10
        )

        execution_time = round(time.time() - start_time, 4)

        os.remove(temp_filename)

        return {
            "status": "success",
            "output": result.stdout,
            "error": result.stderr,
            "execution_time": execution_time
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
