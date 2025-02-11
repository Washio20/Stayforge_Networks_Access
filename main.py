from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()


@app.post("/")
async def receive_data(request: Request):
    body = await request.body()
    print(f"Received data: {body.decode('utf-8')}")  # 记录收到的数据
    return PlainTextResponse("code=0000")


@app.post("/test")
async def test(request: Request):
    body = await request.body()
    print(f"Received data: {body.decode('utf-8')}")  # 记录收到的数据
    return PlainTextResponse("code=0000")


@app.post("/{device_id}/test")
async def test(device_id: str, request: Request):
    body = await request.body()
    print(f"Received data: {body.decode('utf-8')}")  # 记录收到的数据
    return PlainTextResponse("code=0000")
