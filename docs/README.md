# Updating the documentation

The documentation will be automatically rebuilt and deployed upon merge to main on Github.

For local development, you can use the provided docker-compose which monitors the files for
changes and automatically updates as you modify the local files.

You can access the documentation preview by starting the service (see below) and opening
[http://localhost:4000](http://localhost:4000) in your browser.


To start:
```bash
cd docs
docker compose up -d --build
```

To stop:
```bash
cd docs
docker compose down
```

