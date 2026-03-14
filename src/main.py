from datetime import datetime, timedelta, timezone
from http import HTTPStatus

from aleph.sdk import AlephHttpClient
from aleph.sdk.query.filters import MessageFilter
from aleph_message.models import MessageType, AlephMessage
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.config import config
from src.utils.aleph import fetch_instance_ip
from src.utils.aleph_credits import fetch_aleph_credit_balance, compute_runway_days

app = FastAPI(title="LibertAI Monitoring")


class MonitoringResult(BaseModel):
    status: HTTPStatus
    message: str
    instances_checked: int
    unallocated_instances: int


class InstanceMonitor:
    @staticmethod
    async def fetch_instance_messages(address: str) -> list[AlephMessage]:
        """Fetch instance messages posted by a specific address"""

        async with AlephHttpClient() as client:
            messages = await client.get_messages(
                message_filter=MessageFilter(
                    addresses=[address],
                    message_types=[MessageType.instance],
                    channels=[config.ALEPH_AGENT_CHANNEL],
                )
            )
            return messages.messages

    @staticmethod
    async def monitor_address_instances() -> MonitoringResult:
        """Monitor instances for a specific address"""
        try:
            # Fetch all instance messages for the address
            messages: list[AlephMessage] = await InstanceMonitor.fetch_instance_messages(config.ALEPH_AGENTS_OWNER)

            current_time = datetime.now(timezone.utc)
            threshold_time = current_time - timedelta(minutes=30)

            unallocated_instances: list[str] = []

            for message in messages:
                # Get message creation time
                message_time = message.time

                # Check if message is older than 30 minutes
                if message_time < threshold_time:
                    # Check allocation status
                    try:
                        ip_address = await fetch_instance_ip(message.item_hash)
                    except ValueError:
                        ip_address = None

                    if ip_address is None:
                        # Instance is not allocated
                        unallocated_instances.append(message.item_hash)

            instances_checked = len(messages)
            if unallocated_instances:
                error_message = f"Found {len(unallocated_instances)} unallocated instances older than 30 minutes. Hashes: {', '.join(unallocated_instances)}"
                return MonitoringResult(
                    status=HTTPStatus.SERVICE_UNAVAILABLE,
                    message=error_message,
                    instances_checked=instances_checked,
                    unallocated_instances=len(unallocated_instances),
                )
            else:
                return MonitoringResult(
                    status=HTTPStatus.OK,
                    message=f"All instances ({instances_checked}) are either allocated or newer than 30 minutes",
                    instances_checked=instances_checked,
                    unallocated_instances=0,
                )

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error monitoring instances: {str(e)}")


monitor = InstanceMonitor()


@app.get("/health")
async def health_check():
    """
    Health check endpoint to verify the service is running.
    Returns HTTP 200 OK.
    """
    return {"status": "ok", "message": "LibertAI Monitoring Service is running"}


@app.get("/agent-instances")
async def monitor_instances():
    """
    Monitor instance messages for a specific address.

    Returns HTTP 400 with error message including hashes if any instances
    were published more than 30 minutes ago and are still not allocated.
    """
    result = await monitor.monitor_address_instances()

    raise HTTPException(status_code=result.status, detail=result.message)


@app.get("/aleph-credits")
async def check_aleph_credits(min_balance: float = 0, min_runway_days: float = 0):
    """Check Aleph credit balance and runway for the LibertAI instances address.

    Returns 503 if balance or runway is below the given thresholds.
    """
    address = config.LIBERTAI_INSTANCES_ADDRESS
    try:
        credit_balance, cost_per_second = await fetch_aleph_credit_balance(address)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching Aleph credits: {e}")

    runway_days = compute_runway_days(credit_balance, cost_per_second)

    errors: list[str] = []
    if credit_balance < min_balance:
        errors.append(f"Credit balance {credit_balance:.0f} is below minimum {min_balance:.0f}")
    if runway_days is not None and runway_days < min_runway_days:
        errors.append(f"Runway {runway_days:.1f} days is below minimum {min_runway_days:.1f} days")

    result = {
        "address": address,
        "credit_balance": credit_balance,
        "cost_per_second": cost_per_second,
        "runway_days": runway_days,
    }

    if errors:
        raise HTTPException(status_code=503, detail={"errors": errors, **result})

    return {"status": "ok", **result}
