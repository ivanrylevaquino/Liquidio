import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.app.core.config import settings
from backend.app.controllers import auth_controller, user_controller, project_controller, budget_controller

app = FastAPI(
    title="Liquidio - Expense Classification & Liquidation Reporting System",
    description="Backend API for DOST-funded project office at CIT-U",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API route controllers
app.include_router(auth_controller.router)
app.include_router(user_controller.router)
app.include_router(project_controller.router)
app.include_router(budget_controller.router)

@app.get("/api/health", tags=["Health"])
def health_check():
    """System health check endpoint verifying backend connectivity."""
    return {
        "status": "healthy",
        "system": "Liquidio DOST CIT-U",
        "storage_mode": settings.STORAGE_MODE
    }

# Demo mode static file serving:
# Mount static files and handle SPA fallback for non-API routes
FRONTEND_DIST = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

if os.path.exists(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        # Explicitly do NOT handle API or docs routes; let them 404 or route properly
        if (
            full_path.startswith("api")
            or full_path == "docs"
            or full_path == "redoc"
            or full_path.startswith("openapi")
        ):
            raise HTTPException(status_code=404, detail="Not Found")

        file_path = os.path.join(FRONTEND_DIST, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
