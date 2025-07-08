# workoutapp

This is a 100% vibe-coded workout app intended to be used on my home network. It has 3 parts, each represented by an HTML file: a workout planner, tracker, and analyzer. This app is not intended for public distribution, and needs to be locally hosted behind a router and firewall to be used safely. I VPN into my home network in order to use this. The whole thing is run on a Raspberry Pi. 

Here is the AI Readme Output: 

# Simple Workout Planner & Tracker

This is a lightweight, self-hosted web application for creating, tracking, and analyzing workout routines. It's designed for individuals or small groups (like a couple or friends) who want a straightforward way to manage their training without relying on commercial apps.

The application is composed of three main parts:
1.  **Planner (`index.html`):** A tool to build workout plans from a predefined list of exercises. You can specify sets, target reps, weight, superset groupings, and coach's notes.
2.  **Tracker (`Workout.html`):** An interface to load a saved plan and record your actual performance during a workout session, including reps, weight, and Reps in Reserve (RIR).
3.  **Analysis (`analysis.html`):** A dashboard that visualizes your progress over time, showing charts for maximum weight lifted and total volume for each exercise.

All data is saved as simple `.csv` files on the server, making it easy to view, edit, or back up.

## Features

- **Intuitive Interface:** Clean and simple UI built with Tailwind CSS.
- **Dynamic Workout Building:** Easily add exercises to a plan, set parameters, and save.
- **Real-time Tracking:** Load a plan and fill in your actuals as you work out.
- **Progress Visualization:** Automatically generated charts to track your strength and volume progression.
- **User-Specific Plans:** Create and load plans for different users (e.g., "Zak", "Kate").
- **Template-based Planning:** Import a past workout to use as a template for a new one.
- **Local Data Storage:** All your workout data stays with you, stored in simple CSV files.

## Tech Stack

- **Backend:** Python with Flask (for the web server and API) and Pandas (for data analysis).
- **Frontend:** HTML, Tailwind CSS, and vanilla JavaScript (no complex frameworks).

## Setup and Installation

Follow these steps to get the application running on your local machine or a personal server (like a Raspberry Pi).

### 1. Prerequisites

- Python 3.x
- `pip` (Python's package installer)

### 2. Installation Steps

1.  **Clone or Download:** Get all the project files (`server.py`, `index.html`, etc.) into a single directory on your computer.

2.  **Create Required Directories:** The server needs a few folders to store your data. Create them in the same directory as `server.py`:
    - `planned_workouts/`
    - `finished_workouts/`
    - `api/`

3.  **Create Your Exercise List:** Inside the `api/` folder, create a file named `exercises.csv`. This file will be your master list of all exercises you might want to include in a plan. The planner will read from this file.

    The format is a simple CSV with a single header, `Exercise`. Add each exercise on a new line.

    **Example `api/exercises.csv`:**
    ```csv
    Exercise
    Barbell Bench Press
    Dumbbell Shoulder Press
    Lat Pulldown
    Cable Rows
    Squats
    Deadlifts
    Leg Press
    Bicep Curls
    ```

4.  **Install Python Dependencies:** The Python server relies on Flask and Pandas. Create a file named `requirements.txt` in the project directory with the following content:
    ```
    Flask
    Flask-Cors
    pandas
    ```
    Then, open your terminal or command prompt in the project directory and run:
    ```bash
    pip install -r requirements.txt
    ```

### 3. Running the Application

1.  **Start the Server:** In your terminal, run the Python script:
    ```bash
    python server.py
    ```
    You should see output indicating the server is running, something like `* Running on http://0.0.0.0:5000/`.

2.  **Access in Browser:** Open your web browser and navigate to the main page:
    - **URL:** `http://127.0.0.1:5000/index.html`

## How to Use

1.  **Plan a Workout:**
    - Go to the **Planner** page (`index.html`).
    - Use the "Available Exercises" list on the left to add exercises to your plan.
    - For each exercise, fill in the target sets, reps, and weight. You can also assign it to a superset group (A or B) and add notes.
    - Select a User and a Workout Type from the dropdowns at the bottom.
    - Click **"Save Plan to Server"**. This creates a `.csv` file in your `planned_workouts` folder.

2.  **Track a Workout:**
    - Go to the **Tracker** page (`Workout.html`).
    - Select a user to see their available plans.
    - Choose a plan from the dropdown and click **"Load Selected Plan"**.
    - The workout will appear. As you complete each set, fill in the "Actual Reps", "Actual Weight (kg)", "Notes", and "RIR".
    - Once you're done, click **"Save Tracked Workout"**. This creates a new `.csv` file in your `finished_workouts` folder.

3.  **Analyze Your Progress:**
    - Go to the **Analysis** page (`analysis.html`).
    - The page will automatically load all your tracked workout data.
    - Use the dropdowns to filter by user and select an exercise.
    - The charts will update to show your historical performance for that exercise.




