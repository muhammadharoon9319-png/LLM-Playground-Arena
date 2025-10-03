# **🏟️ LLM Playground Arena**

**LLM Playground Arena** (also referred to as LM-Arena) is a Flask-based web application designed for the structured **evaluation and benchmarking of Large Language Model (LLM) outputs** through a user voting environment.

It provides a comprehensive system for project management, role-based authentication, model comparison, and results visualization.

## **✨ Core Features**

| Category | Feature | Description |
| :---- | :---- | :---- |
| **Security & Access** | **User Authentication** | Sign up and log in functionality with secure, role-based access control. |
|  | **Roles** | Separate permissions for **Admin** (project creation/results viewing) and **User** (model comparison/voting). |
| **Evaluation** | **Project Management** | Admins can create, upload, and organize evaluation projects using CSV files containing questions and model responses. |
|  | **Model Comparison** | Clean, structured UI for users to vote between competing model outputs based on preference. |
| **Analysis** | **Results Dashboard** | Dedicated interface to track aggregated votes, compare model performance, and analyze user-level voting patterns (Admin only). |

## **⚡ Prerequisites**

To run this application, you will need:

* **Python 3.12** (Recommended)  
* Package manager: pip or conda  
* **Docker** and **Docker Compose** (Required if using Option 2\)

## **⚙️ Installation and Setup**

You have two primary options for running the LLM Playground Arena:

### **Option 1: Run with Python (Recommended for Development)**

1. **Clone the repository:**  
   git clone \[https://github.com/muhammadharoon9319-png/LLM-Playground-Arena.git\](https://github.com/muhammadharoon9319-png/LLM-Playground-Arena.git)  
   cd LLM-Playground-Arena

2. **Set up a virtual environment:** (Recommended to avoid dependency conflicts)  
   \# Using venv  
   python \-m venv venv  
   source venv/bin/activate   \# On Windows: venv\\Scripts\\activate

   \# OR using conda  
   conda create \-n lm\_arena python=3.12  
   conda activate lm\_arena

3. **Install dependencies:**  
   pip install \-r requirements.txt

4. **Run the application:**  
   python app.py

   Access the application at 👉 **http://localhost:5000**

### **Option 2: Run with Docker (Recommended for Production/Easy Deployment)**

1. **Clone the repository:**  
   git clone \[https://github.com/muhammadharoon9319-png/LLM-Playground-Arena.git\](https://github.com/muhammadharoon9319-png/LLM-Playground-Arena.git)  
   cd LLM-Playground-Arena

2. **Build and run using Docker Compose:**  
   docker compose up \--build

   Access the application at 👉 **http://localhost:5000**  
3. **To stop the container:**  
   docker compose down

## **🚀 Usage**

### **1\. Login**

Sign up for a new account or use the default credentials for immediate testing:

* **Admin**: username admin, password admin123  
* **User**: username abdul, password expert1 or username mannan, password expert2

### **2\. Create Projects (Admin Only)**

* Upload a CSV file containing the source questions and corresponding model responses that you wish to compare.  
* Assign a descriptive project name.

### **3\. Compare Models (Voting)**

* Choose an active project.  
* Vote between two model responses presented in the UI based on quality, relevance, or adherence to the prompt.  
* Continue the process until all comparisons within the project are complete.

### **4\. View Results (Admin Only)**

* Analyze aggregated results and voting statistics across the entire project.  
* Track individual user-level voting patterns and contributions.

## **📂 Project Structure**

LLM-Playground-Arena/  
│── app.py               \# Main Flask application logic  
│── templates/           \# HTML templates for the web interface (UI)  
│── requirements.txt     \# List of Python dependencies  
│── Dockerfile           \# Docker image build configuration  
│── docker-compose.yml   \# Docker Compose configuration for running services  
