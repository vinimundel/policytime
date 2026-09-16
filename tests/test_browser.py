import os
import time
import urllib.error
import urllib.request

import pytest
from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.browser


@pytest.fixture(scope="module")
def browser():
    url = os.environ.get("POLICYTIME_BROWSER_URL")
    if not url:
        pytest.skip("Set POLICYTIME_BROWSER_URL to test the running demo.")
    for _ in range(30):
        try:
            urllib.request.urlopen(f"{url}/readyz", timeout=1).close()
            break
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.2)
    else:
        pytest.fail("The browser-test server did not become ready.")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.mark.parametrize("width,height", [(1440, 1000), (390, 844)])
def test_answer_comparison_and_sources_work_in_browser(browser, width, height):
    page = browser.new_page(viewport={"width": width, "height": height})
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(os.environ["POLICYTIME_BROWSER_URL"], wait_until="networkidle")
    assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth")
    page.get_by_label("Compare with another date").check()
    page.get_by_role("button", name="Find the applicable policy").click()
    expect(page.locator('[data-outcome="answered"]')).to_have_count(2)
    expect(page.locator(".answer-text").nth(0)).to_contain_text("BRL 180")
    expect(page.locator(".answer-text").nth(1)).to_contain_text("BRL 220")
    page.locator(".source-meta a").first.click()
    expect(page.locator("h1")).to_contain_text("H1 2026")
    assert not errors
    page.close()


def test_example_reveals_conflict_instead_of_an_answer(browser):
    page = browser.new_page()
    page.goto(os.environ["POLICYTIME_BROWSER_URL"])
    page.get_by_role("button", name="Two policies that disagree").click()
    expect(page.locator('[data-outcome="conflict"]')).to_be_visible()
    expect(page.locator(".source-item")).to_have_count(2)
    page.close()
