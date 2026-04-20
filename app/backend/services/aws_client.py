"""Client boto3 pour CloudWatch Logs (LocalStack ou AWS réel)."""
import boto3

from core.config import settings


def _logs_client():
    kwargs = dict(
        region_name=settings.AWS_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    if settings.AWS_ENDPOINT_URL:
        kwargs["endpoint_url"] = settings.AWS_ENDPOINT_URL
    return boto3.client("logs", **kwargs)


def list_log_groups(prefix: str = "") -> list[dict]:
    client = _logs_client()
    kwargs = {"limit": 50}
    if prefix:
        kwargs["logGroupNamePrefix"] = prefix
    try:
        r = client.describe_log_groups(**kwargs)
        return [
            {
                "name": g["logGroupName"],
                "retention_days": g.get("retentionInDays"),
                "stored_bytes": g.get("storedBytes", 0),
                "created_at": g.get("creationTime"),
            }
            for g in r.get("logGroups", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]


def list_log_streams(group_name: str) -> list[dict]:
    client = _logs_client()
    try:
        r = client.describe_log_streams(
            logGroupName=group_name,
            orderBy="LastEventTime",
            descending=True,
            limit=20,
        )
        return [
            {
                "name": s["logStreamName"],
                "last_event": s.get("lastEventTimestamp"),
                "stored_bytes": s.get("storedBytes", 0),
            }
            for s in r.get("logStreams", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_log_events(group_name: str, stream_name: str, limit: int = 100) -> list[dict]:
    client = _logs_client()
    try:
        r = client.get_log_events(
            logGroupName=group_name,
            logStreamName=stream_name,
            limit=limit,
            startFromHead=False,
        )
        return [
            {"ts": e.get("timestamp"), "message": e.get("message", "").strip()}
            for e in r.get("events", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]
