import sys
import os
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
backend_dir = BASE_DIR / "backend"
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    print("==================================================")
    print("  Starting StudyGen AI Full-Stack Application")
    print("  URL: http://127.0.0.1:8000")
    print("  Docs: http://127.0.0.1:8000/docs")
    print("==================================================")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
