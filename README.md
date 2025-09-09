# LM-Arena

LM-Arena is a Flask application that allows users to compare different language model responses in a structured voting environment.

## Features

- User authentication (signup, login)
- Admin and user roles
- Create and manage evaluation projects
- Compare language model outputs through a voting interface
- Track and visualize comparison results

## Prerequisites

- Python 3.12 or Docker
- If using Python: `pip` or `conda` for package management
- If using Docker: Docker and Docker Compose

## Installation and Setup

### Option 1: Run with Python

1. Clone the repository:
   ```bash
   git clone https://github.com/abdul-456/SLM-Fine-Tuning.git
   cd SLM-Fine-Tuning/LM-Arena
   ```

2. Set up a virtual environment (optional but recommended):
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # OR using conda
   conda create -n lm_arena python=3.12
   conda activate lm_arena
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application at http://localhost:5000

### Option 2: Run with Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/abdul-456/SLM-Fine-Tuning.git
   cd SLM-Fine-Tuning/LM-Arena
   ```

2. Build and run the application using Docker Compose:
   ```bash
   docker compose up --build
   ```

3. Access the application at http://localhost:5000

To stop the Docker container:
```bash
docker compose down
```

## Usage

1. **Login**: Use the default credentials to log in or create new:
   - Admin: username `admin` and password `admin123`
   - User: username `abdul` and password `expert1` or username `mannan` and password `expert2` 

   Or sign up for a new account.

2. **Creating Projects (Admin only)**:
   - Upload a CSV file containing questions and model responses
   - Give your project a name

3. **Comparing Models**:
   - Select a project
   - Vote for the better response between two models
   - Continue until all comparisons are complete

4. **Viewing Results (Admin only)**:
   - See overall results and individual user voting patterns

## Project Structure

- `app.py`: Main application file
- `templates/`: HTML templates for the web interface
- `requirements.txt`: Python dependencies
- `Dockerfile`: Docker configuration
- `docker-compose.yml`: Docker Compose configuration
