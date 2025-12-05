
from core.pages.basepage import BasePage

# Used by the env fixture to dynamically discover and load this page class
MODULE_CLASSES = ('QaCareerPage', )

class QaCareerPage(BasePage):
    """
    Page Object representing the QA Careers page.

    Responsibilities:
        - Interact with QA-specific page elements.
        - Navigate to the full QA jobs listing page.
    """
    locators = {
        "see_all_qa_jobs_btn": ("XPATH", "//a[normalize-space()='See all QA jobs']")
    }

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------
    def open_all_qa_jobs(self):
        """
        Click the 'See all QA jobs' button to navigate to the vacancies page
        filtered by QA-related roles.
        """
        self.click(self.see_all_qa_jobs_btn)