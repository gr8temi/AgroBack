# CluckOps - Backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Django REST Framework backend for managing poultry farm operations, including flock management, financial tracking, user management, and more.

## Features

- **Farm Management**: Multi-farm support with unique farm codes
- **User Management**: Role-based access control (Staff, Manager, Superuser)
- **Flock Management**: Track and manage poultry flocks
- **Financial Tracking**: Monitor farm finances and transactions
- **User Invitation System**: Invite staff with unique codes
- **Password Reset**: Secure password reset via email with 6-digit codes
- **Dynamic Permissions**: Granular permission control for different user roles
- **JWT Authentication**: Secure API authentication using JSON Web Tokens

## Tech Stack

- **Framework**: Django 4.2+
- **API**: Django REST Framework
- **Database**: PostgreSQL
- **Authentication**: djangorestframework-simplejwt
- **CORS**: django-cors-headers

## Prerequisites

- Python 3.8+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

## Installation

### Using Docker (Recommended)

1. Navigate to the project root (parent directory):
   ```bash
   cd /path/to/gemini
   ```

2. Start all services:
   ```bash
   docker-compose up
   ```

3. The backend will be available at `http://localhost:8000`

### Manual Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   export DATABASE_URL=postgresql://user:password@localhost:5432/poultry_db
   export EMAIL_HOST=localhost
   export EMAIL_PORT=1025
   ```

4. Run migrations:
   ```bash
   python manage.py migrate
   ```

5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:
   ```bash
   python manage.py runserver
   ```

## Project Structure

```
backend/
├── config/          # Django project settings
├── core/            # Core app (User, Farm models)
├── flocks/          # Flock management app
├── finances/        # Financial tracking app
├── manage.py        # Django management script
└── requirements.txt # Python dependencies
```

## API Overview

### Authentication Endpoints

- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - Farm owner registration
- `POST /api/auth/forgot-password/` - Request password reset
- `POST /api/auth/reset-password/` - Reset password with code

### Farm & User Endpoints

- `GET /api/farms/` - List farms
- `POST /api/farms/` - Create farm
- `GET /api/users/` - List farm members
- `POST /api/users/invite/` - Invite user to farm

### Flock Endpoints

- `GET /api/flocks/` - List flocks
- `POST /api/flocks/` - Create flock
- `GET /api/flocks/{id}/` - Get flock details

### Finance Endpoints

- `GET /api/finances/` - List financial records
- `POST /api/finances/` - Create financial record

## User Roles & Permissions

- **Superuser**: Full access to all features
- **Manager**: Manage flocks and finances
- **Staff**: View flocks and add logs

Dynamic permissions can be customized per user:
- `can_manage_flocks`
- `can_manage_finances`
- `can_manage_users`
- `can_add_logs`

## Email Configuration

The backend uses email for password reset functionality. In development, MailCatcher is used to capture emails:

- Web Interface: `http://localhost:1080`
- SMTP Server: `localhost:1025`

## Development

### Running Tests

```bash
python manage.py test
```

### Creating Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Accessing Django Admin

1. Create a superuser (if not already created)
2. Visit `http://localhost:8000/admin/`

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | - |
| `EMAIL_HOST` | Email server host | `localhost` |
| `EMAIL_PORT` | Email server port | `1025` |
| `DEBUG` | Django debug mode | `True` |
| `SECRET_KEY` | Django secret key | Auto-generated |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues, questions, or contributions, please open an issue on the repository.
