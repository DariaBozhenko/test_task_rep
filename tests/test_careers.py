from selenium.webdriver.support.ui import WebDriverWait


class TestCareers:
    """
        UI test suite for Careers / QA vacancies flow.

        Scenario covered:
          1. Open Insider homepage
          2. Navigate to Careers
          3. Open QA team page
          4. Open all QA jobs
          5. Filter by QA + Istanbul
          6. Verify all jobs match filters
          7. Open first job and verify Lever page opens
        """

    # Expected filter values for QA vacancies
    EXPECTED_DEPARTMENT = "Quality Assurance"
    EXPECTED_LOCATION = "Istanbul, Turkiye"
    EXPECTED_TITLE_SUBSTR = "Quality Assurance"
    def test_qa_careers(self, env):
        """
        End-to-end test for QA careers flow:
        Homepage -> Careers -> QA team -> QA vacancies -> Lever job detail.
        """

        # 1. Open home page and verify it is loaded
        env.home_page.open_home_page()
        assert env.home_page.is_homepage_loaded(), "Homepage is not loaded"

        # 2. Capture the current window handle (for returning later)
        original_window = env.home_page.capture_current_window()

        # 3. Navigate to Careers
        env.career_page.open_careers_page()

        # 4. Wait until URL changes away from the homepage
        env.career_page.wait_until_current_page_changed(env.home_page.BASE_URL)

        # 5. Verify key sections are visible on the Careers page
        assert env.career_page.is_section_displayed("teams"), "The Teams section is not displayed on the page"
        assert env.career_page.is_section_displayed("location"), "The Locations section is not displayed on the page"
        assert env.career_page.is_section_displayed("life_at_insider"), "The Life at Insider section is not displayed on the page"

        # 6. Expand all teams and open the QA team page
        env.career_page.expand_all_teams_list()
        env.career_page.open_qa_team_page()

        # 7. On QA Careers page, click 'See all QA jobs'
        env.qa_career_page.open_all_qa_jobs()

        # 8. Wait until the department filter is set to 'Quality Assurance'
        env.vacancies_page.wait_until_initial_qa_filter_applied()

        # 9. Apply filters on Vacancies page
        env.vacancies_page.filter_jobs(
            department=self.EXPECTED_DEPARTMENT,
            location=self.EXPECTED_LOCATION,
            title_contains=self.EXPECTED_TITLE_SUBSTR,
        )

        # 10. Read all job cards as (title, department, location) rows and assert filters
        rows = env.vacancies_page.get_job_rows()
        assert rows, "No job cards after filtering"

        for title, department, location in rows:
            assert self.EXPECTED_TITLE_SUBSTR in title, \
                f"Job title does not contain '{self.EXPECTED_TITLE_SUBSTR}': '{title}'"
            assert department == self.EXPECTED_DEPARTMENT, \
                f"Unexpected department: '{department}'"
            assert location == self.EXPECTED_LOCATION, \
                f"Unexpected location: '{location}'"

        # 11. Click 'View Role' on the first job card
        env.vacancies_page.click_first_job_view_role()

        # 12. Switch focus to the newly opened Lever window
        env.vacancies_page.switch_to_new_window(original_window, "https://jobs.lever.co")

        # 13. Close Lever window and switch back to the original window
        env.vacancies_page.close_window_and_return_to_original_window(original_window)
