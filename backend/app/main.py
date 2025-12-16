        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                self.disconnect(connection)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    # Test Redis connection
    try:
        await redis_client.ping()
        print("Connected to Redis")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")

@app.get("/")
async def root():
    return {"message": "CopySignal Backend Running"}

@app.websocket("/ws/signals")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Internal endpoint for Discord Bot to push signals
@app.post("/api/v1/signals")
async def push_signal(signal: Signal):
    # 1. Save to Redis
    await redis_client.set(f"signal:{signal.id}", signal.json(), ex=3600)
    
    # 2. Publish to Redis Channel (for scalability)
    await redis_client.publish("signals", signal.json())
    
    # 3. Broadcast to connected WebSockets
    await manager.broadcast(signal.json())
    
    return {"status": "received", "signal_id": signal.id}
