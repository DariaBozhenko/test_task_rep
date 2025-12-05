
import os
import re
import time

from datetime import datetime
from types import SimpleNamespace

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

CURRENT_PATH = os.path.dirname(__file__) # Directory path of the current file

# Add custom CLI option --browser to select browser when running pytest
def pytest_addoption(parser):
    """
    Adds custom command-line options to pytest.
    --browser: Allows choosing the browser for test execution (chrome or firefox).
    """
    parser.addoption(
        "--browser", action="store", default="chrome", help="Browser to use: chrome or firefox"
    )

# Fixture to initialize Selenium WebDriver based on --browser option
@pytest.fixture
def selenium_driver(request):
    """
    Pytest fixture to initialize a Selenium WebDriver based on the selected browser.
    Patches the find_element method to track the last interacted element for debugging.

    Args:
        request: Pytest request object containing configuration.

    Returns:
        WebDriver instance
    """
    browser = request.config.getoption("--browser").lower()

    if browser == "chrome":
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    elif browser == "firefox":
        options = webdriver.FirefoxOptions()
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()), options=options)
        driver.maximize_window()
    else:
        raise ValueError(f"Unsupported browser: {browser}")

    # Patch driver's find_element method to track the last found element for debugging
    original_find_element = driver.find_element

    def patched_find_element(by, value):
        element = original_find_element(by, value)
        request.node._last_element = element  # Save the last found element in the current test node
        return element

    driver.find_element = patched_find_element

    return driver

def camel_to_snake(name):
    """Convert CamelCase to snake_case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


# Fixture to dynamically import page classes and instantiate them with the Selenium driver
@pytest.fixture(scope="function")
def env(request, selenium_driver):
    """
    Fixture to dynamically discover and load all page objects under core/pages.
    Each page module must define a MODULE_CLASSES tuple for instantiation.

    Args:
        request: Pytest request object.
        selenium_driver: Active Selenium WebDriver instance.

    Yields:
        SimpleNamespace containing page object instances as attributes.
    """
    env_instance = SimpleNamespace()


    # Recursively walk through core/pages directory and import all page modules except basepage.py
    for root, dirname, filenames in os.walk(os.path.join(CURRENT_PATH, 'core', 'pages')):
        for f in filenames:
            if f.endswith(".py"):
                rel_path = os.path.relpath(os.path.join(root, f), CURRENT_PATH)
                imported_module = os.path.splitext(rel_path)[0].replace(os.sep, '.')
                new_module = __import__(imported_module, fromlist=[imported_module])
                if not hasattr(new_module, "MODULE_CLASSES"):
                    continue
                for class_name in new_module.MODULE_CLASSES:
                    page_class = getattr(new_module, class_name)
                    instance_name = camel_to_snake(class_name)
                    setattr(env_instance, instance_name, page_class(selenium_driver))

    yield env_instance

# Pytest hook to capture test execution results (setup, call, teardown phases)
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
        Pytest hook to capture the result of each test phase.

        Args:
            item: The test item object.
            call: The current test call context.
        """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)

# Fixture that automatically runs around each test to detect failures and perform debug actions
@pytest.fixture(scope="function", autouse=True)
def test_failed_check(request):
    """
    Fixture to handle failed tests by taking screenshots and scrolling to the last interacted element.

    Args:
        request: Pytest request context.
    """
    request.node._last_element = None
    yield

    driver = request.node.funcargs.get('selenium_driver')
    if not driver:
        return

    if hasattr(request.node, 'rep_setup') and request.node.rep_setup.failed:
        print("❌ Setup failed:", request.node.nodeid)
    elif hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
        print("❌ Test failed:", request.node.nodeid)
        try:
            last_el = getattr(request.node, "_last_element", None)
            if last_el:
                scroll_to_element_with_offset(driver, last_el)
                time.sleep(1) # Pause shortly to allow scrolling to complete
                print("✅ Scrolled to last interacted element.")
            else:
                print("ℹ️ No last element tracked.")
        except Exception as e:
            print(f"⚠️ Could not scroll to element: {e}")

        take_screenshot(driver, request.node.nodeid)

    driver.quit()

# Helper function to save a screenshot with a timestamped filename in screenshots folder
def take_screenshot(driver, nodeid):
    """
    Saves a screenshot of the browser with a timestamped name under the 'screenshots' directory.

    Args:
        driver: WebDriver instance.
        nodeid: ID of the test case.
    """
    screenshots_dir = os.path.join(CURRENT_PATH, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    file_name = f'{nodeid}_{datetime.today().strftime("%Y-%m-%d_%H-%M-%S")}.png'.replace("/", "_").replace("::", "__")
    path = os.path.join(screenshots_dir, file_name)
    driver.save_screenshot(path)
    print(f" Screenshot saved to: {path}")

# Scrolls the page so the specified element is visible with offset for fixed header and padding
def scroll_to_element_with_offset(driver, element, header_height=80, extra_padding=10):
    """
        Scrolls to a specific element in the browser window with optional header offset.

        Args:
            driver: WebDriver instance.
            element: WebElement to scroll to.
            header_height (int): Fixed height offset to adjust for sticky headers.
            extra_padding (int): Additional padding from top.
        """
    try:
        driver.execute_script(f"""
            var el = arguments[0];
            var headerHeight = {header_height};
            var extraPadding = {extra_padding};
            var rect = el.getBoundingClientRect();
            var offset = window.pageYOffset + rect.top - headerHeight - extraPadding;
            window.scrollTo({{ top: offset, behavior: 'instant' }});
        """, element)
    except Exception as e:
        print(f"⚠️ scroll_to_element_with_offset failed: {e}")