
from core.pages.basepage import BasePage

# Used by the env fixture to dynamically discover and load this page class
MODULE_CLASSES = ('CareerPage',)


class CareerPage(BasePage):
    """
    Page Object representing the main Careers entry point
    (navigated via Company → Careers in the header menu).

    Responsibilities:
        - Navigate from the top menu to the Careers page.
        - Expose visibility checks for key sections.
        - Provide actions to expand the teams list and open the QA team page.
    """
    locators = {
            "company_menu_item": ('XPATH', "//a[contains(text(),'Company')]"),
            "careers_submenu_item": ('CSS', "a[href='https://useinsider.com/careers/']"),
            "teams_section": ("ID", "career-find-our-calling"),
            "location_section": ("ID", "career-our-location"),
            "life_at_insider_section": ("CLASS_NAME", "e-swiper-container"),
            "see_all_teams_btn": ("XPATH", "//a[normalize-space()='See all teams']"),
            "qa_team_card": ("XPATH", "//h3[normalize-space()='Quality Assurance']"),

    }

    # -------------------------------------------------------------------------
    # Navigation
    # -------------------------------------------------------------------------
    def open_careers_page(self):
        """
        Navigate from the main site to the Careers page via:
            - header "Company" menu item
            - "Careers" submenu entry
        """
        self.company_menu_item.click_button()
        self.careers_submenu_item.click_button()

    # -------------------------------------------------------------------------
    # Visibility checks
    # -------------------------------------------------------------------------
    def is_section_displayed(self, section_name):
        """Generic method to check section visibility."""
        section = getattr(self, f"{section_name}_section")
        return section.visibility_of_element_located()

    # -------------------------------------------------------------------------
    # Actions on teams
    # -------------------------------------------------------------------------
    def expand_all_teams_list(self):
        """
        Click the 'See all teams' button to expand the teams list.
        """
        self.click(self.see_all_teams_btn)

    def open_qa_team_page(self):
        """
        Click on the 'Quality Assurance' team card to navigate
        to the QA careers page.
        """
        self.click(self.qa_team_card)
