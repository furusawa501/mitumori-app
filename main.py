import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from database import Base, engine
from utils import NotAuthenticated


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("data").mkdir(exist_ok=True)
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ["SECRET_KEY"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(NotAuthenticated)
async def not_authenticated_handler(request: Request, exc: NotAuthenticated):
    return RedirectResponse(url="/login", status_code=302)


from routes import auth, customers, dashboard, invoices, quotes

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(customers.router)
app.include_router(quotes.router)
app.include_router(invoices.router)
