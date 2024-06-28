"""
Main module
"""

import logging
import os
import re
import sys
import typing
from pathlib import Path

from fastapi import FastAPI, HTTPException
from h5grove.fastapi_utils import router, settings  # type: ignore
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request

from plotting_service.auth import get_experiments_for_user, get_user_from_token
from plotting_service.exceptions import AuthError

stdout_handler = logging.StreamHandler(stream=sys.stdout)
logging.basicConfig(
    handlers=[stdout_handler],
    format="[%(asctime)s]-%(name)s-%(levelname)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)
logger.info("Starting Plotting Service")

ALLOWED_ORIGINS = ["*"]
CEPH_DIR = os.environ.get("CEPH_DIR", "/ceph")
logger.info("Setting ceph directory to %s", CEPH_DIR)
settings.base_dir = Path(CEPH_DIR).resolve()
DEV_MODE = bool(os.environ.get("DEV_MODE", False))


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def get() -> typing.Literal["ok"]:
    """
    Health check endpoint
    \f
    :return: "ok"
    """
    return "ok"


@app.middleware("http")
async def check_permissions(request: Request, call_next: typing.Callable[..., typing.Any]) -> typing.Any:
    """
    Middleware that checks the requestee token has permissions for that experiment
    :param request: The request to check
    :param call_next: The next call (the route function called)
    :return: A response
    """
    if DEV_MODE:
        return await call_next(request)
    if request.method == "OPTIONS":
        return await call_next(request)
    if request.url.path in ("/healthz", "/docs"):
        return await call_next(request)

    logger.info(f"Checking permissions for {request.url.path}")
    match = re.search(r"%2FRB(\d+)%2F", request.url.query)
    if match is not None:
        experiment_number = match.group(1)
    else:
        logger.warning(
            f"The requested nexus metadata path {request.url.path} does not include an experiment number. Permissions "
            f"cannot be checked"
        )
        raise HTTPException(400, "Request missing experiment number")

    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        raise HTTPException(401, "Unauthenticated")

    token = auth_header.split(" ")[1]


    try:
        user = get_user_from_token(token)
    except AuthError:
        raise HTTPException(403, detail="Forbidden") from None
    logger.info("Checking role of user")
    if user.role == "staff":
        return await call_next(request)

    logger.info("Checking experiments for user")
    allowed_experiments = get_experiments_for_user(user)
    if experiment_number in allowed_experiments:
        return await call_next(request)

    raise HTTPException(403, detail="Forbidden")


app.include_router(router)
