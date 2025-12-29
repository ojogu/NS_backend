from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.util.db import init_db, drop_db
from src.util.redis_client import setup_redis
from fastapi.middleware.cors import CORSMiddleware
from src.util.config import Settings 
from src.util.exception import register_error_handlers
from src.v1.controllers.user import user_router
from src.v1.controllers.courses import courses_router
from src.v1.auth.routes import auth_router
@asynccontextmanager
async def life_span(app: FastAPI):
    """
    Lifecycle event handler for the FastAPI application.

    This asynchronous function is called when the FastAPI application starts up
    and shuts down. It initializes the database on startup and performs cleanup
    on shutdown.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None: This function yields control back to the application after startup.
    """
    
    # print(f"dropping db....")
    # await drop_db()
    # print(f"db dropped")
    
    # Startup: Initialize the database
    print("server is starting....")
    await init_db()
    print("server has started!!")
    
    print("redis is starting....")
    await setup_redis()
    print("redis has started!!")
    yield  # Yield control back to FastAPI
    
    # Shutdown: Perform any necessary cleanup
    print("server is ending.....")

app = FastAPI(
    lifespan=life_span,
    title=Settings.PROJECT_NAME,
    version=Settings.PROJECT_VERSION,
    description=Settings.PROJECT_DESCRIPTION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#register error handlers 
register_error_handlers(app)

#register routers/blueprint
app.include_router(auth_router, prefix=Settings.API_PREFIX)
app.include_router(user_router, prefix=Settings.API_PREFIX)
app.include_router(courses_router, prefix=Settings.API_PREFIX)
# app.include_router(admin_router, prefix=Settings.API_PREFIX)



@app.get("/")
def root():
    """
    Root endpoint for the FastAPI application.

    Returns:
        str: A simple greeting message.
    """
    return {"message": "Hello World"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("main:app",  port=8000, reload=True, host="0.0.0.0")
    