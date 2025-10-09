# Odayssey

Odayssey is a **digital diary web application** designed to provide a diary-like experience, combining habit tracking, task management, and personal journaling into one platform. It also presents a daily motivational replicating the feel of a traditional diary. The goal of the project was to create a personal productivity tool that feels intuitive, lightweight, and easy to use.

The project was built using **Python and Flask** for the backend, **SQLite** for the database, **Flask-SQLAlchemy** for ORM, and standard web technologies such as **HTML, CSS, JavaScript, and Jinja2** templating for the frontend. Some dynamic behaviors, like marking tasks done or toggling habits, are powered by **AJAX calls** to provide a smooth user experience without full page reloads.

---

## Folder & File Overview

- **app.py**  
  This is the core of the application. It contains all Flask routes for handling user registration, login, and interactions with the habit tracker, to-do list, journal, and daily quotes. Routes are organized to separate functionality for each section, such as `/habits`, `/todo`, `/journal`.

- **helpers.py**  
  Contains utility functions that support the main app. For example, the `fetch_quote()` function retrieves a daily motivational quote from an external API and ensures it is cached so that the API is not called repeatedly.

- **requirements.txt**  
  Lists all Python dependencies necessary to run the application, including Flask and Flask-SQLAlchemy.

- **README.md**  
  This file — serves as the main documentation for the project.

- **instance/odayssey.db**  
  The SQLite database storing all user data, including accounts, habits, task lists, journal entries, and cached daily quotes.

- **templates/**  
  Contains all Jinja2 HTML templates:

  - `layout.html` – Base template that includes navigation, common CSS/JS imports, and the page structure.
  - `homepage.html` – Landing page welcoming users to the app.
  - `login.html` & `register.html` – Forms for authentication.
  - `habits.html` – Displays the habit tracker grid with the ability to add, mark done/undone, and remove habits.
  - `todo.html` – Shows the to-do list where users can add tasks, mark them done, remove them, and clear completed tasks.
  - `journal.html` – Provides a simple interface for writing and deleting personal journal entries.

- **static/**  
  Contains all static assets such as CSS, JavaScript, and images:
  - `styles.css` – Custom styling for all pages, including mobile-friendly layouts.
  - any icons or graphics used in the app.

---

## Design Decisions

Several design choices were made to balance **functionality, simplicity, and demonstration efficiency**:

1. **Habit tracker**: A grid per habit was implemented using a dictionary keyed by `(habit_id, day)` for quick lookups of daily completions. This was simpler than building a fully relational query for each date, and it allowed smooth AJAX toggling of habit completion.

2. **To-do list**: Tasks are ordered simply by creation time. Immediate strikethrough feedback when marking a task done was chosen to give a smooth, responsive feel. The completed tasks move to a separate section to avoid clutter.

3. **Journal**: Opted for a minimalistic design where all entries are listed with a delete button. This keeps the feature quick to implement while still functional.

4. **Daily quote**: Caching quotes by date ensures that the API is not overused and that users see the same quote throughout the day. This reinforces the diary experience by providing a consistent “daily reflection” element.

5. **AJAX**: Used selectively for marking tasks done, toggling habits, and removing entries, so that the interface is responsive and avoids full-page reloads, which would disrupt the diary experience.

---

## Usage

1. **Register** a new account or log in with an existing one.
2. **Habit Tracker**: Add habits, mark them done, or remove them. Navigate across months to see persistent habits.
3. **To-Do List**: Add tasks, mark them completed, remove individual tasks, or clear all completed tasks.
4. **Journal**: Write and delete entries to keep a daily log.
5. **Daily Quote**: Each day a motivational quote is shown to encourage reflection and productivity.

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Vikram-04/Odayssey.git
   cd Odayssey
   ```
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app:
   flask run
4. Open a browser at http://127.0.0.1:5000/.

#### Demo video link 🎥: https://youtu.be/EsGTuj6IB4E

### Deployed using render
#### Live Demo: https://odayssey.onrender.com/

#### Odayssey was built as part of CS50x Final Project, emphasizing practical functionality, usability, and a diary-like experience over unnecessary complexity. The design decisions reflect a balance between demonstrating full-stack capability and keeping the app maintainable and straightforward.
