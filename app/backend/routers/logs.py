from fastapi import APIRouter, Depends, Query

from dependencies.auth import require_role
from models.user import User
from services import aws_client

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/cloudwatch/groups", summary="Liste des groupes de logs CloudWatch")
def list_groups(
    prefix: str = Query("", description="Filtrer par préfixe"),
    _: User = Depends(require_role("admin")),
):
    return aws_client.list_log_groups(prefix)


@router.get("/cloudwatch/groups/{group_name:path}/streams",
            summary="Liste des streams d'un groupe de logs")
def list_streams(
    group_name: str,
    _: User = Depends(require_role("admin")),
):
    return aws_client.list_log_streams(group_name)


@router.get("/cloudwatch/groups/{group_name:path}/streams/{stream_name:path}/events",
            summary="Événements d'un stream")
def get_events(
    group_name: str,
    stream_name: str,
    limit: int = Query(100, le=1000),
    _: User = Depends(require_role("admin")),
):
    return aws_client.get_log_events(group_name, stream_name, limit)
