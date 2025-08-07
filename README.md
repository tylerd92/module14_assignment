## Module 14 Assignment

## Running the Application
### Prerequisites
- Python 3.10
- Playwright installed: `pip install playwright`
- Playwright browsers installed: `python3 -m playwright install`

Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

Download the requirements:
```bash
pip install -r requirements.txt
```

Run docker compose:
```bash
docker compose up --build
```

Go to `http://localhost:8000` in your browser.

### Unit and Integration Tests
```bash
pytest # to run all tests
pytest -s -v # for more verbose output
pytest --preserve-db # to preserve the database between tests
pytest --run-slow # to run slow tests
pytest tests/integration # to run integration tests
```

### End-to-End Tests with Playwright
```bash
# Run E2E tests using the convenience script
./run_e2e_tests.sh

# Or run manually (make sure server is running on port 8000)
HEADLESS=true python3 -m pytest tests/e2e/test_playwright_simple.py -v

# Run in non-headless mode (visible browser) for debugging
HEADLESS=false python3 -m pytest tests/e2e/test_playwright_simple.py -v
```

Browse calculations
![image](images/browse_calculations.png)

Create a new calculation
![image](images/create_calculation.png)

View a calculation
![image](images/view_calculation.png)

Edit a calculation
![image](images/edit_calculation.png)

Delete a calculation
![image](images/delete_calculation.png)

GitHub Action Workflow
![image](images/github_actions.png)

Docker Hub
![image](images/docker_hub.png)