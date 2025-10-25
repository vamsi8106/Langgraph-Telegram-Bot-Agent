"export $(grep -v '^#' .env | xargs)" - used to configure .env variables


## to run

uv run --active karan-bot-telegram

# make sure your app really points to karandb as karan for automatic table in postgrtes

# need to changes in alembic/env.py 
# need to change sqlalchemy.url path in alembic.ini
alembic revision -m "init" --autogenerate
alembic upgrade head

## promethud and graphana

cd monitoring
docker compose up -d

## after ading new packe in pyproject.toml
uv pip install -e .

## stop all containers nad remove them
docker stop $(docker ps -q)
docker rm $(docker ps -aq)

# Apply file changes, then:
docker compose down
docker compose up -d

# Verify Prometheus is reachable from Grafana container:
docker exec -it grafana sh -lc 'apk add --no-cache curl >/dev/null 2>&1 || true; curl -sf http://prometheus:9090/-/ready && echo OK'

# Check Grafana logs—no provisioning errors:
docker logs --tail=200 grafana | grep -i provisioning

# Open Prometheus targets and Grafana:
xdg-open http://localhost:9090/targets
xdg-open http://localhost:3000/

# Pytest Run
uv run pytest --cov=src/app --cov-report=html
uv run pytest --cov=src/app --cov-config=.coveragerc --cov-report=term-missing