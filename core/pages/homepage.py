
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from core.pages.basepage import BasePage

# Used by the env fixture to dynamically discover and load this page class
MODULE_CLASSES = ('HomePage', )

class HomePage(BasePage):
    """
    Page Object representing the public Insider homepage.

    Responsibilities:
        - Open the homepage.
        - Handle the cookie banner.
        - Provide a simple readiness check (is_homepage_loaded).
    """
    BASE_URL = "https://useinsider.com/"

    locators = {
        "cookies_banner": ("ID", "wt-cli-cookie-banner-title"),
        "accept_cookies_btn": ("ID", "wt-cli-accept-all-btn"),
        "homepage_banner": ("ID", "desktop_hero_24"),
        }

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------
    def open_home_page(self):
        """
        Navigate to the Insider homepage and accept cookies if the banner is displayed.
        """
        self.driver.get(self.BASE_URL)
        self.accept_cookies_if_visible()

    def accept_cookies_if_visible(self, timeout=5):
        # -------------------------------------------------------------------------
        # Cookies handling
        # -------------------------------------------------------------------------
        """
        Click 'Accept cookies' if the cookies banner is present and visible.

        :param timeout: Max time to wait for the banner to appear.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: self.cookies_banner.is_displayed()
            )
            # Use BasePage.click for consistent clicking (with waits/JS fallback)
            self.click(self.accept_cookies_btn)
        except TimeoutException:
            # Banner not shown → nothing to do
            pass

    # -------------------------------------------------------------------------
    # State checks
    # -------------------------------------------------------------------------
    def is_homepage_loaded(self):
        """"
        Check to verify that the homepage main banner is visible.

        To be used directly in assertions:
            assert home_page.is_homepage_loaded()
        """
        try:
            return self.homepage_banner.is_displayed()
        except Exception:
            return False