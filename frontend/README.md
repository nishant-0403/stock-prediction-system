Frontend (dashboard) notes:
- The dashboard can be implemented as a React app (Tailwind + Charting library like Recharts or Chart.js).
- It should call the regular backend REST API to:
  - register/login users
  - configure notification preferences
  - view real-time predictions & historic model output
- Use websockets (backend) or server-sent events for live updates, or poll the REST API periodically.
