from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import uvicorn
from app.config import ASSISTANT_PORT
uvicorn.run("app.main:app",host="127.0.0.1",port=ASSISTANT_PORT,reload=False)
