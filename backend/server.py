from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our domain-specific routers
from src.routes.generation import router as generation_router
from src.routes.evaluation import router as evaluation_router
from src.routes.history import router as history_router

app = FastAPI(title="AI Architect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Plug in all our modular routes
app.include_router(generation_router)
app.include_router(evaluation_router)
app.include_router(history_router)

@app.get("/health")
async def healt_check():
    return {"status":"healthy","service":"ai-architect-api"}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)