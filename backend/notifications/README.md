Notifications module:
- Responsible for reading ML signals / indicators and sending messages to users via Telegram.
- Could be implemented as a worker (Celery/RQ) that consumes from a message queue (Redis/RabbitMQ).
- This skeleton uses a polling approach for simplicity.
