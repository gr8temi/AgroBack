# DB Management Skill

Manage the PostgreSQL database for this Django poultry farm backend.

## Instructions

This is a Dockerized Django project. The database runs as the `db` service (PostgreSQL 15) inside Docker Compose. All Django management commands must run inside the `backend` container.

**Container execution prefix:** `docker compose -f /root/AgroBack/docker-compose.yml exec backend`

### Determine the user's intent and run the appropriate action:

#### 1. "migrate" / "run migrations" / "apply migrations"
Run pending migrations:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py migrate
```
Show which migrations were applied and report the result.

#### 2. "makemigrations" / "create migrations" / "generate migrations"
Generate migration files for model changes. If the user specifies an app name, pass it; otherwise run for all apps:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py makemigrations [app_name]
```
After generating, show the user the migration file contents with the Read tool, then ask if they want to apply it.

#### 3. "migration status" / "show migrations" / "pending migrations"
Show migration status across all apps:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py showmigrations
```

#### 4. "reset db" / "flush" / "wipe database"
**This is destructive — always confirm with the user first.**
Flush the database (delete all data, keep schema):
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py flush --no-input
```
Or for a full reset (drop and recreate):
```
docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS poultry;"
docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -c "CREATE DATABASE poultry OWNER postgres;"
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py migrate
```

#### 5. "seed" / "load fixtures" / "populate" / "sample data"
If the user wants to seed the database with sample data:
- Check for fixture files in any app's `fixtures/` directory.
- If fixtures exist: `docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py loaddata <fixture>`
- If no fixtures exist: ask the user what data they want, then create a management command or fixture file for it.

#### 6. "add" / "create" / "insert" — Add records via the Django ORM

Run one-off ORM commands inside the backend container to create records. Use `python manage.py shell -c "..."` for non-interactive execution.

**Execution pattern:**
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "<python code>"
```

Always import models at the top of the snippet. Use `; ` to separate statements on one line, or use multi-line strings with `$'...'` or heredocs.

**Model quick-reference (use these for all record operations):**

| Model | App | Required fields | Notes |
|---|---|---|---|
| `Farm` | `core` | `name`, `owner` (User FK) | `code` auto-generated. Optional: `base_currency` (default `NGN`). Choices: `NGN`/`USD`/`KES`/`GHS`/`ZAR`/`GBP`/`EUR` |
| `User` | `core` | `username`, `password` | Use `User.objects.create_user(...)`. Roles: `staff`, `manager`, `financial_manager`, `superuser`. Set `farm=` to assign. Permissions auto-set based on role on create |
| `PushToken` | `core` | `user`, `token` | |
| `Flock` | `flocks` | `name`, `breed`, `initial_quantity`, `current_quantity`, `user`, `farm` | Status: `active`/`closed`. Optional: `start_date`, `end_date`, `closure_reason` |
| `FeedLog` | `flocks` | `flock`, `date`, `quantity_kg`, `feed_type` | Optional: `cost`, `currency` (default: farm's `base_currency`) |
| `HealthLog` | `flocks` | `flock`, `date`, `log_type`, `description` | `log_type`: `vaccination`/`medication`/`mortality`/`other`. Optional: `cost`, `currency`, `affected_birds` |
| `EggCollection` | `flocks` | `flock`, `date`, `quantity_collected` | Optional: `damaged` |
| `Transaction` | `finances` | `user`, `farm`, `date`, `type`, `category`, `amount` | `type`: `income`/`expense`. Categories: `feed`/`medication`/`equipment`/`labor`/`utilities`/`bird_purchase`/`egg_sales`/`bird_sales`/`manure_sales`/`other`. Optional: `description`, `related_flock`, `currency` (default: farm's `base_currency`) |
| `ExchangeRate` | `currencies` | `base_currency`, `target_currency`, `rate` | `fetched_at` auto-set. Append-only history. |
| `ReportConfig` | `reports` | `farm` (OneToOne) | Optional: `is_enabled`, `deadline_time` |
| `Question` | `reports` | `config` (ReportConfig FK), `text` | `question_type`: `text`/`number`/`date`/`boolean`. Optional: `is_required`, `input_type`, `sort_order` |
| `DailyReport` | `reports` | `farm`, `user`, `reference_date` | Unique on `(farm, reference_date)` |
| `ReportAnswer` | `reports` | `report` (DailyReport FK), `question` | Set one of: `answer_text`, `answer_number`, `answer_date`, `answer_boolean` |

**Examples:**

Create a user + farm:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from core.models import User, Farm
user = User.objects.create_user(username='john', password='pass1234', role='superuser')
farm = Farm.objects.create(name='Green Acres', owner=user)
user.farm = farm; user.save()
print(f'Created user {user.username} (id={user.id}) and farm {farm.name} (id={farm.id}, code={farm.code})')
"
```

Create a flock:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from core.models import User, Farm
from flocks.models import Flock
from datetime import date
farm = Farm.objects.get(id=1)
user = User.objects.get(id=1)
flock = Flock.objects.create(name='Layer Batch A', breed='ISA Brown', initial_quantity=500, current_quantity=500, user=user, farm=farm, start_date=date.today())
print(f'Created flock {flock.name} (id={flock.id})')
"
```

Add a feed log:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from flocks.models import Flock, FeedLog
from datetime import date
flock = Flock.objects.get(id=1)
log = FeedLog.objects.create(flock=flock, date=date.today(), quantity_kg=25.5, feed_type='Layer Mash', cost=1200.00)
print(f'Created feed log (id={log.id})')
"
```

Add a transaction:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from core.models import User, Farm
from finances.models import Transaction
from datetime import date
user = User.objects.get(id=1)
farm = Farm.objects.get(id=1)
tx = Transaction.objects.create(user=user, farm=farm, date=date.today(), type='expense', category='feed', amount=1200.00, description='Layer mash purchase')
print(f'Created transaction (id={tx.id})')
"
```

**When the user asks to add a record:**
1. Identify which model they mean from context.
2. Ask for any required fields they haven't provided.
3. Look up related objects (farm, user, flock) by name or ID as needed — query first if the user gives a name instead of an ID.
4. Construct the ORM snippet and run it.
5. Print the created object's ID and key fields to confirm.

#### 7. "list" / "show" / "query" / "count" / "find" — Query records

Query existing records using the ORM. Same execution pattern as above.

**Examples:**

List all farms:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from core.models import Farm
for f in Farm.objects.all(): print(f'id={f.id} name={f.name} code={f.code} owner={f.owner.username}')
"
```

List flocks for a farm:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from flocks.models import Flock
for f in Flock.objects.filter(farm_id=1): print(f'id={f.id} name={f.name} breed={f.breed} qty={f.current_quantity} status={f.status}')
"
```

Count records:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from flocks.models import Flock, FeedLog, HealthLog, EggCollection
from finances.models import Transaction
from core.models import User, Farm
print(f'Users: {User.objects.count()}')
print(f'Farms: {Farm.objects.count()}')
print(f'Flocks: {Flock.objects.count()}')
print(f'Feed logs: {FeedLog.objects.count()}')
print(f'Health logs: {HealthLog.objects.count()}')
print(f'Egg collections: {EggCollection.objects.count()}')
print(f'Transactions: {Transaction.objects.count()}')
"
```

When the user asks to see or find records, construct the appropriate queryset with filters, ordering, and output formatting.

#### 8. "update" / "edit" / "change" — Update records

Query the record first, modify fields, then save:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from flocks.models import Flock
flock = Flock.objects.get(id=1)
flock.current_quantity = 480
flock.save()
print(f'Updated flock {flock.name}: current_quantity={flock.current_quantity}')
"
```

For bulk updates:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from flocks.models import Flock
updated = Flock.objects.filter(farm_id=1, status='active').update(current_quantity=450)
print(f'Updated {updated} flocks')
"
```

#### 9. "delete" / "remove" — Delete records
**Confirm with the user before deleting.** Show what will be deleted first.

```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell -c "
from flocks.models import FeedLog
log = FeedLog.objects.get(id=5)
print(f'Deleting: {log}')
log.delete()
print('Deleted.')
"
```

#### 11. "shell" / "db shell" / "psql" / "sql"
Open a database shell or run SQL:
- Django ORM shell: `docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py shell`
- Direct psql: `docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -d poultry`
- Run a specific query: `docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -d poultry -c "<SQL>"`

#### 12. "rollback" / "reverse migration" / "undo migration"
Roll back to a specific migration. Ask the user which app and migration to roll back to:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py migrate <app_name> <migration_name>
```
To roll back all migrations for an app: `migrate <app_name> zero`

#### 13. "squash" / "squash migrations"
Squash migrations for an app:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py squashmigrations <app_name> <start> <end>
```

#### 14. "schema" / "show tables" / "describe" / "inspect"
Show database schema information:
- List all tables: `docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -d poultry -c "\dt"`
- Describe a table: `docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -d poultry -c "\d+ <table_name>"`
- Show row counts: `docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -d poultry -c "SELECT schemaname, relname, n_live_tup FROM pg_stat_user_tables ORDER BY n_live_tup DESC;"`

#### 15. "backup" / "dump" / "export"
Dump the database:
```
docker compose -f /root/AgroBack/docker-compose.yml exec -T db pg_dump -U postgres poultry > /root/AgroBack/backup_$(date +%Y%m%d_%H%M%S).sql
```

#### 16. "restore" / "import" / "load dump"
**Destructive — confirm with user first.**
Restore from a SQL dump file:
```
docker compose -f /root/AgroBack/docker-compose.yml exec -T db psql -U postgres -d poultry < <path_to_dump>
```

#### 17. "superuser" / "create admin"
Create a Django superuser:
```
docker compose -f /root/AgroBack/docker-compose.yml exec backend python manage.py createsuperuser
```
Note: this is interactive. Tell the user to run it with `!` prefix, or use the `--noinput` flag with env vars:
```
docker compose -f /root/AgroBack/docker-compose.yml exec -e DJANGO_SUPERUSER_USERNAME=admin -e DJANGO_SUPERUSER_EMAIL=admin@example.com -e DJANGO_SUPERUSER_PASSWORD=admin backend python manage.py createsuperuser --noinput
```

### Key reference

- **DB name:** `poultry`
- **DB user:** `postgres`
- **DB password:** `postgres`
- **DB host (in Docker network):** `db`
- **Apps with migrations:** `core`, `flocks`, `finances`, `reports`, `currencies`
- **Docker Compose file:** `/root/AgroBack/docker-compose.yml`
- **Custom User model:** `core.User` (extends AbstractUser)

### Safety rules

- **Always confirm before destructive operations** (reset, flush, rollback, restore).
- After running migrations, verify with `showmigrations` if anything looks off.
- Before rolling back, warn the user about potential data loss if the migration is not reversible.
- When creating migration files, always show the generated file to the user before applying.
