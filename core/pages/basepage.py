
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumpagefactory import PageFactory


class BasePage(PageFactory):
    """
    Base page object for all application pages.

    Responsibilities:
      - Provide common Selenium utilities (clicking, waiting, locating elements).
      - Encapsulate WebDriver access for child page objects.
      - Contain only GENERIC behaviour (NO page-specific logic).
    """

    DEFAULT_TIMEOUT = 10

    def __init__(self, driver):
        """
        :param driver: Selenium WebDriver instance.
        """
        self.driver = driver
        super().__init__()  # initialize PageFactory

    # -------------------------------------------------------------------------
    # Locators / elements
    # -------------------------------------------------------------------------
    def get_by_type(self, locator_type):
        """
        Helper to convert a string locator type into Selenium's By enum.

        :param locator_type: One of "id", "xpath", "name", "css_selector", etc.
        :return: Corresponding selenium.webdriver.common.by.By value.
        :raises ValueError: If the locator type is not supported.
        """
        locator_type = locator_type.upper()
        mapping = {
            "ID": By.ID,
            "XPATH": By.XPATH,
            "NAME": By.NAME,
            "CSS_SELECTOR": By.CSS_SELECTOR,
            "CLASS_NAME": By.CLASS_NAME,
            "LINK_TEXT": By.LINK_TEXT,
            "PARTIAL_LINK_TEXT": By.PARTIAL_LINK_TEXT,
            "TAG_NAME": By.TAG_NAME,
        }

        if locator_type not in mapping:
            raise ValueError(f"Unsupported locator type: {locator_type}")

        return mapping[locator_type]

    def get_element_list(self, locator, locator_type="ID"):
        """
        Find all elements that match the given locator and type.

        :param locator: The locator value (e.g. "#id-value", "//div").
        :param locator_type: One of supported types (default: "ID").
        :return: List of matching WebElements (could be empty).
        """
        by = self.get_by_type(locator_type)
        return self.driver.find_elements(by, locator)

    def wait_for(self, condition, timeout=None, message=""):
        """
        Generic explicit wait wrapper.

        :param condition: Expected condition callable.
        :param timeout: Max wait time (seconds).
        :param message: Optional message on timeout.
        :return: Whatever the condition returns (WebElement or bool).
        """
        wait_time = timeout or self.DEFAULT_TIMEOUT
        return WebDriverWait(self.driver, wait_time).until(condition, message=message)

    # -------------------------------------------------------------------------
    # Clicks / waits
    # -------------------------------------------------------------------------

    def click(self, element):
        """
        Click on an element
        Uses JavaScript click to avoid issues with hidden elements or overlays
        """

        self.driver.execute_script("arguments[0].click();", element)

    def wait_until_current_page_changed(self, old_url, timeout=None):
        """
        Block until the browser URL changes from old_url.

        :param old_url: The previous URL to compare against.
        :param timeout: Optional override for wait timeout (seconds).
        :return: The new URL after change.
        :raises TimeoutException: If the URL does not change in time.
        """
        wait_time = timeout or self.DEFAULT_TIMEOUT

        def url_changed(driver):
            return driver.current_url != old_url

        self.wait_for(
            url_changed,
            timeout=wait_time,
            message=f"URL did not change within {wait_time} seconds: {old_url}",
        )
        return self.driver.current_url

    # -------------------------------------------------------------------------
    # Window / tab handling
    # -------------------------------------------------------------------------
    def capture_current_window(self):
        """
        Capture and return the current window handle.

        :return: The handle of the current window/tab.
        :raises RuntimeError: If more than one window is already open.
        """
        original_window = self.driver.current_window_handle
        open_windows = self.driver.window_handles

        if len(open_windows) != 1:
            raise RuntimeError(
                f"Expected exactly 1 window, found {len(open_windows)}: {open_windows}"
            )

        return original_window

    def switch_to_new_window(self, current_window, expected_url_substring, timeout=None):
        """
        Wait for a new window/tab to open, switch to it,
        and (optionally) wait until its URL contains expected_url_substring.

        :param current_window: Handle of the current/original window.
        :param expected_url_substring: Optional substring expected in new window URL.
        :param timeout: Optional override for wait timeout (seconds).
        :raises TimeoutException: If no new window opens in time
                                  or URL condition is not satisfied.
        """
        wait_time = timeout or self.DEFAULT_TIMEOUT

        # Wait for a new window/tab
        self.wait_for(EC.number_of_windows_to_be(2), timeout=wait_time)

        # Switch to the new window
        for window_handle in self.driver.window_handles:
            if window_handle != current_window:
                self.driver.switch_to.window(window_handle)
                break

        if expected_url_substring:
            self.wait_for(
                EC.url_contains(expected_url_substring),
                timeout=wait_time,
                message=f"New window URL does not contain '{expected_url_substring}'",
            )

    def close_window_and_return_to_original_window(self, original_window):
        """
        Close the current window/tab and switch back to the original window/tab.

        :param original_window: Handle of the window/tab to return to.
        """
        self.driver.close()
        self.driver.switch_to.window(original_window)
