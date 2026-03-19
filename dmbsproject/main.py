from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/room")
def home():
    return FileResponse("rooms.html")

@app.get("/service")
def home():
    return FileResponse("services.html")



