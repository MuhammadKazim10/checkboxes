from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Session

from db import SessionLocal, Checkbox, init_db

app = FastAPI()

app.mount("/static",StaticFiles(directory="./static"), name="static")
templates = Jinja2Templates(directory="./templates")


class CheckboxUpdate(BaseModel):
    checked: bool


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


def get_db():
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


@app.on_event("startup")
def startup():
    init_db()


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/checkboxes")
async def get_checkboxes():
    db: Session = SessionLocal()
    try:
        rows = db.query(Checkbox).order_by(Checkbox.id.asc()).all()
        return [{"id": row.id, "checked": row.checked} for row in rows]
    finally:
        db.close()


@app.post("/api/checkboxes/{checkbox_id}")
async def update_checkbox(checkbox_id: int, payload: CheckboxUpdate):
    db: Session = SessionLocal()
    try:
        row = db.query(Checkbox).filter(Checkbox.id == checkbox_id).first()

        if not row:
            raise HTTPException(status_code=404, detail="Checkbox not found")

        row.checked = payload.checked
        db.commit()

        message = {"id": row.id, "checked": row.checked}
        await manager.broadcast(message)

        return {"success": True, **message}
    finally:
        db.close()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)

@app.get("/health")
async def health():
    return {"ok": True}
