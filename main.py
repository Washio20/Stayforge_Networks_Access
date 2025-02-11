from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()


@app.post("/")
async def receive_data(request: Request):
    body = await request.body()
    print(f"Received data: {body.decode('utf-8')}")
    return PlainTextResponse("code=0000")

@app.post("/{device_id}/test")
async def test(device_id: str, request: Request):
    body = await request.body()
    data = body.decode('utf-8')
    print(f"[{device_id}]Received data: {data}")  # 记录收到的数据
    if data == "test_pass":
        return PlainTextResponse("code=0000")
    return
