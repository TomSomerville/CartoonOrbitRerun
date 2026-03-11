# CartoonOrbitRerun

A Python Flask web application with MySQL database and Peewee ORM.

## Technology Stack

- **Language**: Python 3.8+
- **Framework**: Flask 2.3.3
- **Database**: MySQL
- **ORM**: Peewee 3.16.3
- **Package Manager**: pip

## Project Structure

```
CartoonOrbitRerun/
├── app/
│   ├── __init__.py           # App factory
│   ├── database.py           # Database configuration
│   ├── models.py             # Database models (Peewee)
│   ├── routes.py             # Route blueprints
│   ├── static/               # Static assets (CSS, JS, images)
│   └── templates/            # HTML templates
│       ├── base.html         # Base template
│       ├── index.html        # Index page
│       └── czonehome.html    # Czonehome page
├── config.py                 # Configuration settings
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
└── README.md                 # This file
```

## Features

- **Index Page** (`/` or `/index`): Hello World page
- **Czonehome Page** (`/czonehome`): Hello World page
- **Database Integration**: MySQL with Peewee ORM
- **Configuration Management**: Environment-based config with .env support
- **Blueprint-based Routing**: Modular route organization

## Installation

### Prerequisites

- Python 3.8 or higher
- MySQL Server installed and running
- pip (Python package manager)

### Setup Steps

1. **Create and activate virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Copy `.env.example` to `.env`
   - Update `.env` with your MySQL credentials:
     ```
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=your_password
     DB_NAME=cartoon_orbit
     DB_PORT=3306
     ```

4. **Create MySQL database:**
   ```sql
   CREATE DATABASE cartoon_orbit;
   -- you can also create a dedicated user/ grant privileges if you prefer
   ```

   **Note:** the application will automatically create any tables defined
   in `app/models.py` when the Flask app starts (see `app/__init__.py`).
   If you prefer to create tables manually, run:
   ```powershell
   python -c "from app import create_app; from app.database import db; from app.models import User; app = create_app();
   with app.app_context(): db.create_tables([User])"
   ```

## Running the Application

1. **Activate virtual environment (if not already active):**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. **Run the Flask application:**
   ```powershell
   python run.py
   ```

3. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`
   - Index page: `http://localhost:5000/` or `http://localhost:5000/index`
   - Czonehome page: `http://localhost:5000/czonehome`

## Database Models

### User Model
- `id`: Primary key
- `username`: Unique username
- `email`: Unique email address
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Development

### Adding New Routes

Edit `app/routes.py` to add new routes:
```python
@main_bp.route('/newpage')
def newpage():
    return render_template('newpage.html')
```

### Adding New Models

1. Create model in `app/models.py`
2. Ensure it inherits from `BaseModel`
3. Run database migrations as needed

## Troubleshooting

### Database Connection Error
- Verify MySQL server is running
- Check database credentials in `.env`
- Ensure database exists in MySQL

### Module Not Found
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

## Future Enhancements

- Database migration system
- Authentication and user management
- API endpoints
- Testing suite
- Static file optimization

## License

MIT
