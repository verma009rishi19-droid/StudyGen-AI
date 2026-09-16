import sys
import os
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
backend_dir = BASE_DIR / "backend"
sys.path.insert(0, str(backend_dir))

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "False").lower() in ("true", "1")
    print("==================================================")
    print("  Starting StudyGen AI Full-Stack Application")
    print(f"  Listening on: http://{host}:{port}")
    print(f"  Docs: http://{host}:{port}/docs")
    print("==================================================")
    uvicorn.run("app.main:app", host=host, port=port, reload=debug)
