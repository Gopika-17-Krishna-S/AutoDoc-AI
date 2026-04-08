# ⚡ AutoDoc AI

AutoDoc AI is a comprehensive Django-based platform that automatically parses Flask and FastAPI backend source code, classifies endpoints, detects system workflows, and presents a beautiful Swagger-style API documentation UI.

It allows teams to quickly understand and document Python codebases directly from GitHub URLs or uploaded source code ZIPs.

## ✨ Features

- **Automated Parsing**: Uses Python's `ast` module to statically analyze code for route decorators (`@app.get`, `@app.route`).
- **Endpoint Classification**: Identifies categories (Auth, Users, Items, Health, Admin, etc.) automatically based on endpoint patterns.
- **Workflow Detection**: Identifies common patterns like "Authentication Workflows" or "CRUD Operations".
- **Premium UI**: Built with a sleek dark-mode glassmorphism design, featuring Google Fonts (Inter, JetBrains Mono) and smooth micro-animations.
- **Project Explorer**: A file-by-file breakdown of what endpoints live in which source files.
- **Secure Access**: Full User Authentication (Register/Login).
- **Export Data**: Download the parsed API documentation as a structured JSON file.

---

## 🚀 Installation & Setup

Follow these steps to get the project running locally on Windows/Linux/Mac.

### 1. Prerequisites
Ensure you have the following installed:
- Python 3.10+
- `pip`
- `git`

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd "Autodoc AI"
```

### 3. Setup Virtual Environment
It's highly recommended to use a virtual environment:

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
Install the required Python packages from the newly generated `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 5. Apply Database Migrations
Initialize the default SQLite3 database with the required tables:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)
To access the Django Admin panel at `http://127.0.0.1:8000/admin/`:
```bash
python manage.py createsuperuser
```

### 7. Run the Local Development Server
```bash
python manage.py runserver
```
The application will now be running at `http://127.0.0.1:8000`.

---

## 📖 How to Use

1. **Register/Login**: Go to the web app and register for a new account.
2. **Create Project**: Click **+ New Project** in the navbar. Provide a name, description, and supply either an uploaded `.zip` of your source code OR a direct link to a GitHub repository `.zip` format.
3. **Parse Code**: Open your newly created project and click the **⚙ Parse Code** button. AutoDoc AI will unzip the file, parse the `.py` files, detect API routes, extract comments, and categorize them.
4. **View APIs**: Click **📄 View API Docs** to see the grouped, Swagger-style API layout.
5. **Explore Files**: Click **🔭 Explorer** to see the exact `.py` files those endpoints came from.
6. **Export**: Export the generated docs natively to JSON!

---

## 🛠 Tech Stack

- **Backend**: Django 4.2+, Django REST Framework
- **Frontend**: Django Templates, HTML5, Vanilla CSS (Glassmorphism & Flexbox/Grid)
- **Database**: SQLite3 (default, easily switchable to PostgreSQL)

## 📌 Architecture
- `autodoc/`: Main Django project configuration settings and URLs.
- `accounts/`: Application handling user authentication via Django's auth system.
- `projects/`: Main app governing `Project` and `APIEndpoint` models, views, and templates.
- `parser/`: Core logic module containing `utils.py` with the Abstract Syntax Tree (`ast.NodeVisitor`) based Python parser.
- `api/`: Initial DRF views infrastructure.
