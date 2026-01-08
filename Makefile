.PHONY: run stop build migrate migrations superuser test shell bash logs

# Docker Compose Commands (Run from backend/ directory)
DC = docker-compose -f ../docker-compose.yml

run:
	$(DC) up

stop:
	$(DC) down

build:
	$(DC) build

logs:
	$(DC) logs -f backend

# Django Commands (Running inside Docker)
migrate:
	$(DC) exec backend python manage.py migrate

migrations:
	$(DC) exec backend python manage.py makemigrations

superuser:
	$(DC) exec backend python manage.py createsuperuser

test:
	$(DC) exec backend python manage.py test

shell:
	$(DC) exec backend python manage.py shell

bash:
	$(DC) exec backend bash
