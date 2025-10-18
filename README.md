# Vendly FastAPI Backend Project
This repository contains the backend code for the Vendly application, built using FastAPI. It provides RESTful APIs for managing products, users, and orders.

## Running the project
To run the project locally, follow these steps:
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd vendly
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the environment variables as needed (refer to `.env.example` for guidance).
5. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
   or run in dev mode:
    ```bash
    fastapi dev main.py
    ```
6. Access the API documentation at `http://localhost:8000/docs`.