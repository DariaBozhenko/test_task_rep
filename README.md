# Test Automation Framework

Test automation framework for web UI, API, and load testing using Selenium, pytest, requests, and Locust.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Running Tests

**UI Tests:**
```bash
pytest tests/test_careers.py --browser chrome  # or firefox
```

**API Tests:**
```bash
pytest tests/test_pet_api.py
```

**All Tests:**
```bash
pytest
```

**Load Tests:**
```bash
locust -f tests/locustfile.py
```

## Key Features

- Web UI testing with Selenium (Chrome/Firefox)
- API testing with requests
- Load testing with Locust
- Page Object Model pattern
- Automatic screenshots on failure

## Requirements

- Python 3.7+
- Chrome or Firefox browser
- Dependencies listed in `requirements.txt`
