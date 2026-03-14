import aiohttp


async def fetch_aleph_credit_balance(address: str) -> tuple[float, float]:
    """Fetch credit balance and cost per second for an Aleph address.

    Returns (credit_balance, cost_per_second).
    """
    async with aiohttp.ClientSession() as session:
        balance_url = f"https://api2.aleph.im/api/v0/addresses/{address}/balance"
        costs_url = f"https://api2.aleph.im/api/v0/costs?include_details=0&include_size=true&address={address}"

        async with session.get(balance_url) as resp:
            resp.raise_for_status()
            balance_data = await resp.json()

        async with session.get(costs_url) as resp:
            resp.raise_for_status()
            costs_data = await resp.json()

    credit_balance = float(balance_data["credit_balance"])
    cost_per_second = float(costs_data["summary"]["total_cost_credit"])

    return credit_balance, cost_per_second


def compute_runway_days(credit_balance: float, cost_per_second: float) -> float | None:
    """Compute runway in days. Returns None if cost is zero."""
    if cost_per_second <= 0:
        return None
    return credit_balance / (cost_per_second * 86400)
