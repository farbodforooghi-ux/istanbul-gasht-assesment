# Istanbul Gasht Store Admin Dashboard

Simple admin dashboard for a small store. Built with Flask and SQLite. This project is an assessment-style app meant to be easy to run and extend.

## What the project does

- Provides a basic admin dashboard showing orders, revenue, and products.
- Lets an admin create, edit, and delete products.
- Shows a recent activity feed and simple sales charts.
- Includes a small admin profile page with avatar upload.
- Uses SQLite for storage and stores uploaded files in static/uploads.

## Why this is useful

- Good starting point for learning how to build an admin panel with Flask.
- Small and readable codebase that is easy to modify.
- Includes example data and an easy DB init route so you can run it locally or deploy quickly.

## Quick start

Requirements
- Python 3.8 or later
- git

Clone and install
```bash
git clone https://github.com/farbodforooghi-ux/istanbul-gasht-assesment.git
cd istanbul-gasht-assesment
python -m venv .venv
source .venv/bin/activate    # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
```

Run locally
```bash
# Option 1 - simple
python app.py

# Option 2 - production style (requires gunicorn)
# The repo includes a Procfile for deployment which uses gunicorn.
gunicorn app:app
```

Open the app
- Visit http://localhost:5000/dashboard or http://127.0.0.1:5000/dashboard

Initialize the database
- There are two easy ways to seed the database:
  - Visit the init route in your browser after starting the app: http://localhost:5000/init-db
  - Or run the provided script if you prefer to run from Python: see init_db.py

Environment notes
- The app uses a SECRET_KEY for session and flash messages. You can set it with:
  - Unix/macOS: export SECRET_KEY="a-secret"
  - Windows (PowerShell): $env:SECRET_KEY = "a-secret"
- The default SQLite file is created as istanbul_gasht_store.db in the project root.
- Uploaded files are stored under static/uploads by default.

## Main routes

- GET / or /dashboard - Dashboard overview
- GET /products - List products
- GET, POST /products/create - Create product
- GET, POST /products/<id>/edit - Edit product
- POST /products/<id>/delete - Delete product
- GET, POST /profile - Edit admin profile
- GET /init-db - Initialize and seed the database (use once)
- GET /uploads/<filename> - Serve uploaded files

## Project layout

- app.py - Main Flask application and routes
- models.py - SQLAlchemy models
- init_db.py - Optional script to initialize DB
- requirements.txt - Python dependencies
- Procfile - For deployment (heroku / Render)
- templates/ - HTML templates used by Flask
- static/ - Static assets and uploads
- istanbul_gasht_store.db - SQLite file created at runtime

## Usage examples

Start app and create sample data
1. Start the app: python app.py
2. Open http://localhost:5000/init-db to create sample admin, products, and orders.
3. Go to http://localhost:5000/dashboard to see KPIs and the sample data.

Create a product via the UI
1. Open http://localhost:5000/products/create
2. Fill in name, price, category, stock, optional description and image
3. Submit to add the product


## Notes and small tips

- This app uses a single admin record (id = 1) by default.
- The /init-db route is convenient for quick demos. Remove or protect it in real deployments.
- Keep SECRET_KEY and other sensitive config in environment variables for production.
