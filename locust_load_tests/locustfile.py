from locust import HttpUser, task, between
import random
import urllib.parse


class N11BaseUser(HttpUser):
    host = "https://www.n11.com"
    wait_time = between(2, 5)

    basic_queries = ["laptop", "telefon", "kadın mont"]
    laptop_brand_filters = ["asus", "lenovo", "msi"]
    coat_brand_filters = ["defacto", "koton", "lcw"]
    price_ranges = [
        ("500", "1500"),
        ("15000", "40000"),
        ("20000", "50000"),
    ]
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    def open_homepage(self):
        with self.client.get("/", name="Homepage", timeout=10, catch_response=True, headers=self.DEFAULT_HEADERS) as resp:
            if resp.status_code != 200:
                resp.failure(f"Homepage failed with status {resp.status_code}")

    def header_search(self, query, name_suffix = ""):
        params = {"q": query}
        encoded = urllib.parse.urlencode(params)
        label = f"Search{(' ' + name_suffix) if name_suffix else ''}"
        with self.client.get(f"/arama?{encoded}", name=label, timeout=15, catch_response=True, headers=self.DEFAULT_HEADERS) as resp:
            if resp.status_code != 200:
                resp.failure(f"Search '{query}' failed with status {resp.status_code}")
        return resp

    def paginate(self, query, page, extra_params = None):
        params = {"q": query, "pg": page}
        if extra_params:
            params.update(extra_params)
        encoded = urllib.parse.urlencode(params)
        label = f"Search pagination page {page}"
        with self.client.get(f"/arama?{encoded}", name=label, timeout=15, catch_response=True, headers=self.DEFAULT_HEADERS) as resp:
            if resp.status_code != 200:
                resp.failure(f"Pagination failed for query '{query}', page {page} with status {resp.status_code}")
        return resp

    def apply_filters(self, query, filters, name_suffix = ""):
        params = {"q": query}
        params.update(filters)
        encoded = urllib.parse.urlencode(params, doseq=True)
        label = f"Search filters{(' ' + name_suffix) if name_suffix else ''}"
        with self.client.get(f"/arama?{encoded}", name=label, timeout=15, catch_response=True, headers=self.DEFAULT_HEADERS) as resp:
            if resp.status_code != 200:
                resp.failure(
                    f"Filter request for '{query}' with {filters} failed with status {resp.status_code}"
                )
        return resp

    def apply_sort(self, query, filters, sort_key, name_suffix = ""):
        params = {"q": query, "srt": sort_key}
        if filters:
            params.update(filters)
        encoded = urllib.parse.urlencode(params, doseq=True)
        label = f"Search sort {sort_key}{(' ' + name_suffix) if name_suffix else ''}"
        with self.client.get(f"/arama?{encoded}", name=label, timeout=15, catch_response=True, headers=self.DEFAULT_HEADERS) as resp:
            if resp.status_code != 200:
                resp.failure(
                    f"Sort request for '{query}' with sort '{sort_key}' and filters {filters} "
                    f"failed with status {resp.status_code}"
                )
        return resp

    def auto_suggest(self, prefix):
        """
        Call real auto-suggest endpoint for a given prefix.

        Real URL example:
        https://www.n11.com/arama/tamamla?keyword=ip
        """
        params = {"keyword": prefix}
        encoded = urllib.parse.urlencode(params)
        with self.client.get(
            f"/arama/tamamla?{encoded}",
            name=f"Auto-suggest '{prefix}'",
            timeout=5,
            catch_response=True,
            headers=self.DEFAULT_HEADERS,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(
                    f"Auto-suggest for '{prefix}' failed with status {resp.status_code}"
                )
        return resp

    def search_within_results(self, base_query, refine_query):
        params = {"q": base_query, "iw": refine_query}
        encoded = urllib.parse.urlencode(params)
        with self.client.get(
            f"/arama?{encoded}",
            name=f"Search within results '{base_query}' -> '{refine_query}'",
            timeout=15,
            catch_response=True,
            headers=self.DEFAULT_HEADERS,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(
                    f"Search within results for base '{base_query}' and refine '{refine_query}' "
                    f"failed with status {resp.status_code}"
                )
        return resp


# -------------------------
# LTS01 – Basic Search Flow
# -------------------------

class SearchBasicUser(N11BaseUser):

    @task
    def basic_search_flow(self):
        self.open_homepage()
        query = random.choice(self.basic_queries)
        self.header_search(query, name_suffix="(LTS01)")


# ----------------------------------------
# LTS02 – Search + Pagination + 1 Filter
# ----------------------------------------

class SearchPaginationFilterUser(N11BaseUser):
    query = "laptop"

    @task
    def search_pagination_filter(self):
        self.open_homepage()

        self.header_search(self.query, name_suffix="(LTS02 initial)")

        for page in [2, 3]:
            self.paginate(self.query, page, extra_params=None)

        brand = random.choice(self.laptop_brand_filters)
        filters = {"brand": brand}
        self.apply_filters(self.query, filters, name_suffix="(LTS02 brand)")

        self.paginate(self.query, 2, extra_params=filters)


# -------------------------------------------------
# LTS03 – Multiple Filters + Sorting (Heavy Flow)
# -------------------------------------------------

class SearchMultiFilterSortUser(N11BaseUser):
    query = "kadın mont"

    @task
    def multi_filter_sort_search(self):
        self.open_homepage()
        self.header_search(self.query, name_suffix="(LTS03 initial)")

        brand = random.choice(self.coat_brand_filters)
        price_min, price_max = random.choice(self.price_ranges)

        filters = {
            "brand": brand,
            "category": "kadin_giyim",
            "price_min": price_min,
            "price_max": price_max,
        }

        self.apply_filters(self.query, filters, name_suffix="(LTS03 multi-filters)")
        self.apply_sort(self.query, filters, sort_key="PRICE_LOW", name_suffix="(LTS03 sort)")


# ----------------------------------------------------
# LTS04 & LTS05 – Auto-suggest / Suggestions While Typing
# ----------------------------------------------------

class AutoSuggestUser(N11BaseUser):
    wait_time = between(0.2, 0.5)

    prefixes_sets = [
        ["l", "la", "lap"],
        ["i", "ip", "iph"],
        ["p", "ps", "ps5"],
        ["k", "ka", "kad"],
    ]

    @task
    def auto_suggest_flow(self):
        self.open_homepage()
        prefixes = random.choice(self.prefixes_sets)
        for prefix in prefixes:
            self.auto_suggest(prefix)


# -----------------------------------------
# LTS06 – Search Within Search Results
# -----------------------------------------

class SearchWithinResultsUser(N11BaseUser):
    base_query = "laptop"
    refine_queries = ["gaming", "çanta"]

    @task
    def search_within_results_flow(self):
        self.open_homepage()
        self.header_search(self.base_query, name_suffix="(LTS06 base)")
        refine = random.choice(self.refine_queries)
        self.search_within_results(self.base_query, refine)


# ------------------------------------------------------------------
# LTS07 – Combined: Header Search → Within Results → Filters + Sort
# ------------------------------------------------------------------

class CombinedSearchUser(N11BaseUser):
    base_query = "laptop"
    within_query = "gaming"

    @task
    def combined_search_flow(self):
        self.open_homepage()

        self.header_search(self.base_query, name_suffix="(LTS07 base)")
        self.search_within_results(self.base_query, self.within_query)

        brand = random.choice(self.laptop_brand_filters)
        price_min, price_max = random.choice(self.price_ranges)
        filters = {
            "brand": brand,
            "price_min": price_min,
            "price_max": price_max,
        }

        self.apply_filters(self.base_query, filters, name_suffix="(LTS07 filters after within-results)")
        self.apply_sort(self.base_query, filters, sort_key="PRICE_LOW", name_suffix="(LTS07 sort)")
