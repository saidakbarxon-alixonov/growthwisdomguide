                       # 📚 Growth Wisdom Guide

A Django web application for browsing, discovering, and sharing books.

> Built as part of my backend development learning journey.

## ✨ Features

- Browse books
- View detailed book information
- Organize books by category
- User registration and authentication
- Add and share books

<!-- Only keep features that really work. Add new ones as you build them. -->

## 🛠 Technologies Used

| Area | Tools |
| --- | --- |
| Backend | Python, Django |
| Database | SQLite |
| Frontend | HTML, CSS, JavaScript |
| Dev tools | Git, GitHub, PyCharm, django-debug-toolbar |

## 🖼 Screenshots

### Home page
<!-- Paste your existing home page image here -->

### Sign up and login pages
<!-- Paste your existing sign up / login images here -->

### Add book page
<!-- Paste your existing add book images here -->

### Book page
<!-- Paste your existing book page image here -->

### Share page
<!-- Paste your existing share page image here -->

## 🚀 Getting Started

### Requirements

- Python 3.x (write the version you use)
- Git

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/saidakbarxon-alixonov/growthwisdomguide.git
   cd growthwisdomguide
   ```

2. Create and activate a virtual environment:

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create the database tables:

   ```bash
   python manage.py migrate
   ```

5. (Optional) Create an admin account:

   ```bash
   python manage.py createsuperuser
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

7. Open <http://127.0.0.1:8000/> in your browser.

## 📁 Project Structure

```
growthwisdomguide/
├── my_books/        # Django app: books
├── my_project/      # Project settings and main URLs
├── static/          # CSS, JavaScript, images
├── templates/       # HTML templates
├── manage.py
├── requirements.txt
└── README.md
```

<!-- If you have other apps (for example main), add them here with a short comment. -->

## 🎯 Purpose

I created this project to practice Django, authentication, database design, and web application development.

## 📖 What I Learned

- <!-- e.g. how Django templates and base.html layouts work -->
- <!-- e.g. building forms with ModelForm -->
- <!-- e.g. using Git and GitHub from PyCharm -->

## 🗺 Roadmap

- [ ] <!-- next feature you want to build, e.g. book search -->
- [ ] <!-- another idea -->
- [ ] Move `SECRET_KEY` to an environment variable
- [ ] Write tests

## 👤 Author

**Saidakbarxon Alixonov**
GitHub: [@saidakbarxon-alixonov](https://github.com/saidakbarxon-alixonov)











