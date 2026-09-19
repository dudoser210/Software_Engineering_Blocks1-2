import random
import uuid

from locust import HttpUser, between, task


class UniUser(HttpUser):
    """Traffic always enters through the edge/API Gateway, never a service directly."""

    wait_time = between(0.1, 0.8)

    def on_start(self):
        suffix = uuid.uuid4().hex[:10]
        response = self.client.post(
            "/api/identity/users",
            json={"name": "Load Student", "email": f"load-{suffix}@example.com"},
            name="POST /identity/users",
        )
        response.raise_for_status()
        self.user_id = response.json()["id"]

    @task(4)
    def read_catalog(self):
        self.client.get("/api/catalog/items", name="GET /catalog/items")

    @task(2)
    def create_order(self):
        quantity = random.randint(1, 3)
        self.client.post(
            "/api/orders/orders",
            json={
                "user_id": self.user_id,
                "item_id": random.randint(1, 3),
                "quantity": quantity,
                "total": 120 * quantity,
            },
            name="POST /orders/orders",
        )

    @task(1)
    def read_analytics(self):
        self.client.get("/api/analytics/stats", name="GET /analytics/stats")

