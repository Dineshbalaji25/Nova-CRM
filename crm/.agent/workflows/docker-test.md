---
description: Run tests inside the Docker container for CI/CD simulation
---

1. Build the Docker images
// turbo
```bash
docker-compose build
```

2. Start the database and redis services in the background
// turbo
```bash
docker-compose up -d db redis
```

3. Run the migrations inside the container
// turbo
```bash
docker-compose run --rm api python manage.py migrate
```

4. Run the tests inside the container
// turbo
```bash
docker-compose run --rm api python manage.py test apps/crm apps/users
```

5. Clean up
// turbo
```bash
docker-compose down
```
