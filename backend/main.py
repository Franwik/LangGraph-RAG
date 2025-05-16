from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router as chat_router
from graph_logic import graph_builder

app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(chat_router)