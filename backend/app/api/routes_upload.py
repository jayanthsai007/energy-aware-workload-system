import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict

router = APIRouter()

UPLOAD_FOLDER = "uploaded_scripts"

# Create folder if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@router.post("/upload-script")
async def upload_script(file: UploadFile = File(...)):

    # Validate file type
    if not file.filename.endswith((".py", ".java")):
        raise HTTPException(status_code=400, detail="Only .py or .java files allowed")

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    # Save file temporarily
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    # -------- METADATA EXTRACTION --------
    file_size_kb = len(content) / 1024

    decoded_content = content.decode("utf-8", errors="ignore")
    lines = decoded_content.splitlines()
    line_count = len(lines)

    # Simple structural analysis
    import_count = sum(1 for line in lines if "import " in line)
    class_count = sum(1 for line in lines if "class " in line)
    function_count = sum(1 for line in lines if "def " in line)

    metadata = {
        "filename": file.filename,
        "file_size_kb": round(file_size_kb, 2),
        "line_count": line_count,
        "import_count": import_count,
        "class_count": class_count,
        "function_count": function_count
    }

    return metadata
