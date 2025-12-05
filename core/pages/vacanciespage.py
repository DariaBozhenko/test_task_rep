import hashlib

from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.support import expected_conditions as EC

from core.pages.basepage import BasePage

MODULE_CLASSES = ('VacanciesPage', )

def hash_content(html):
    """
    Generate MD5 hash of the given HTML string.
    Used to detect changes in the page content by comparing hashes.
    """
    return hashlib.md5(html.encode('utf-8')).hexdigest()

class VacanciesPage(BasePage):
    """
    Page Object representing the Vacancies / Careers page.

    Responsibilities:
        - Interact with department & location filters.
        - Provide access to the list of job cards.
        - Offer higher-level operations like filtering and waiting
        until UI reflects selected filters.
    """
    locators = {
        "job_list_elem": ("ID", "jobs-list"),
        "department_dropdown": ("ID", "select2-filter-by-department-container"),
        "location_dropdown": ("ID", "select2-filter-by-location-container"),
        "jobs_list": ("XPATH", "//div[@id='jobs-list']/div"),

    }
    # -------------------------------------------------------------------------
    # Dropdowns
    # -------------------------------------------------------------------------

    def select_filter_option(self, dropdown_name, option_text, timeout=10):
        """
        Generic helper for the filters on Vacancies page.
        Interacts with the *visible* control and waits for the job list DOM to change.
        """

        if dropdown_name not in self.locators:
            raise KeyError(f"Dropdown '{dropdown_name}' not found in locators")

        locator_type, locator_value = self.locators[dropdown_name]
        by = self.get_by_type(locator_type)
        wait = WebDriverWait(self.driver, timeout)

        # 1) Get the visible control element
        control_element = wait.until(
            EC.presence_of_element_located((by, locator_value)),
            message=f"Dropdown '{dropdown_name}' control not present",
        )
        # Normalize current selection text
        current_text = control_element.text.replace("×\n", "").strip()
        if current_text == option_text:
            return

        # 2) Snapshot job list DOM before opening/choosing option
        html_before = self.get_jobs_list_html()

        # 3) Open dropdown
        control_element.click()

        # 4) Locate and click the desired option in the opened dropdown
        option_xpath = f"//li[contains(normalize-space(), '{option_text}')]"
        option_elem = wait.until(
            EC.element_to_be_clickable((By.XPATH, option_xpath)),
            message=f"Option '{option_text}' not clickable in dropdown '{dropdown_name}'",
        )
        option_elem.click()

        # 5) Wait until job list DOM actually changes
        self.wait_for_job_list_to_change(html_before, timeout=timeout)

    def select_department(self, department_name, timeout=10):
        """
        Select the given department from the department filter.
        """
        self.select_filter_option(
            dropdown_name="department_dropdown",
            option_text=department_name,
            timeout=timeout,
        )

    def select_location(self, location_name, timeout=10):
        """
        Select the given location from the location filter.
        """
        self.select_filter_option(
            dropdown_name="location_dropdown",
            option_text=location_name,
            timeout=timeout,
        )
    # -------------------------------------------------------------------------
    # Job cards accessors
    # -------------------------------------------------------------------------
    def get_job_card_elements(self):
        """
        Return all job card WebElements under the jobs list container.
        """
        locator_type, locator_value = self.locators["jobs_list"]
        return self.get_element_list(locator_value, locator_type)

    def _extract_card_info(self, card_el):
        """
        Given a job card WebElement, extract title, department and location
        using its internal structure.
        """
        title_el = card_el.find_element(By.CLASS_NAME, "position-title")
        dept_el = card_el.find_element(By.CLASS_NAME, "position-department")
        loc_el = card_el.find_element(By.CLASS_NAME, "position-location")

        return {
            "title": title_el.text.strip(),
            "department": dept_el.text.strip(),
            "location": loc_el.text.strip(),
        }

    def get_job_rows(self):
        """
        Return a list of (title, department, location) tuples
        for the current job cards, based on the card's visible text.
        Mirrors the behavior of the old test that did el.text.split('\\n').
        """
        rows = []
        cards = self.get_job_card_elements()
        for el in cards:
            # Split text by lines and strip whitespace
            lines = [line.strip() for line in el.text.split("\n") if line.strip()]
            if len(lines) < 3:
                continue
            title, department, location = lines[0], lines[1], lines[2]
            rows.append((title, department, location))
        return rows

    # -------------------------------------------------------------------------
    # Wait helpers
    # -------------------------------------------------------------------------
    def wait_until_initial_qa_filter_applied(self, timeout=15):
        """
        Wait until the initial auto-applied QA filter is reflected in the UI.

        Observed behaviour:
            - After clicking "See all QA jobs" on QA careers page,
                the real <select id="filter-by-department"> eventually changes
                to "Quality Assurance".

        """

        def dept_is_qa(_):
            # Find the real <select> each time to avoid stale references
            select_elem = self.driver.find_element(By.ID, "filter-by-department")
            selected_text = Select(select_elem).first_selected_option.text.strip()
            return selected_text == "Quality Assurance"

        WebDriverWait(self.driver, timeout).until(
            dept_is_qa,
            message="Department <select> never changed to 'Quality Assurance'",
        )

    def get_jobs_list_html(self):
        """
        Return the innerHTML of the job list container (#jobs-list).
        """
        return self.job_list_elem.get_attribute("innerHTML")

    def wait_for_job_list_to_change(self, previous_html, timeout=10):
        """
        Wait until the innerHTML of #jobs-list changes compared to previous_html.
        This indicates that the job list has been re-rendered after filters.
        """

        # Wait for hash to change
        WebDriverWait(self.driver, timeout).until(
            lambda d: hash_content(
                d.find_element(By.CSS_SELECTOR, "#jobs-list").get_attribute("innerHTML")
            ) != hash_content(previous_html),
            message = f"Job list did not change within {timeout} seconds",
        )

    # -------------------------------------------------------------------------
    # Filter consistency helpers
    # -------------------------------------------------------------------------

    def _compute_jobs_mismatching_filters(self,*,department,location, title_contains):
        """
        PURE helper: read the current job list once and return cards
        that do NOT match the given filters.
        """
        mismatches = []
        cards = self.get_job_card_elements()

        for card in cards:
            info = self._extract_card_info(card)

            if department and info["department"] != department:
                mismatches.append(info)
                continue

            if location and info["location"] != location:
                mismatches.append(info)
                continue

            if title_contains and title_contains not in info["title"]:
                mismatches.append(info)
                continue

        return mismatches

    def all_jobs_match_filters(self, *, department=None, location=None, title_contains=None):
        """
        Check current job cards against the provided filters.

        Pure check: no waiting, just reads the DOM once.
        """
        return not self._compute_jobs_mismatching_filters(
            department=department,
            location=location,
            title_contains=title_contains,
        )

    def filter_jobs(self, department=None, location=None, title_contains=None, timeout=10):
        """
        High-level operation to apply filters and wait until the job list is
        semantically consistent with them.

        Steps:
          - apply department filter (if provided),
          - apply location filter (if provided),
          - then wait until all visible job cards match the filters.
        """

        # If no filters provided, nothing else to wait for
        if not (department or location or title_contains):
            return

        if department:
            self.select_department(
                department_name=department,
                timeout=timeout,
            )
        if location:
            self.select_location(
                location_name=location,
                timeout=timeout,
            )

        # Final stabilization: wait until the visible cards satisfy the filters
        WebDriverWait(self.driver, timeout).until(
            lambda d: self.all_jobs_match_filters(
                department=department,
                location=location,
                title_contains=title_contains,
            ),
            message=(
                "Job cards did not reach a state where all items match the "
                f"filters within {timeout} seconds: "
                f"department={department}, location={location}, "
                f"title_contains={title_contains!r}"
            ),
        )

    # -------------------------------------------------------------------------
    # Click helpers
    # -------------------------------------------------------------------------
    def click_first_job_view_role(self):
        """
        Click the 'View Role' button of the first job card.
        Uses locator-based approach to avoid stale element issues.
        """
        cards = self.get_job_card_elements()
        if not cards:
            raise AssertionError("No job cards available to click 'View Role'")

        first_card = cards[0]
        btn = first_card.find_element(By.CSS_SELECTOR, "a.btn.btn-navy")
        self.click(btn)
