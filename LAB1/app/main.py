import os

from fastapi import FastAPI
import redis

app = FastAPI()

db = redis.Redis(
    host="db",
    port=6379,
    decode_responses=True,
)


@app.get("/")
def root():
    counter = db.incr("requests")

    return {
        "message": "Hello from Docker Lab",
        "requests": counter,
        "instance": os.getenv("HOSTNAME"),
    }


@app.get("/health")
def health():
    return {"status": "ok"}