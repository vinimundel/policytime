"""Record a two-minute captioned browser walkthrough of a running local demo."""

import argparse
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


def caption(page, text):
    page.evaluate(
        """text => {
      let box = document.querySelector('#walkthrough-caption');
      if (!box) {
        box = document.createElement('div');
        box.id = 'walkthrough-caption';
        box.style.cssText = 'position:fixed;bottom:18px;left:50%;transform:translateX(-50%);'
          + 'max-width:950px;width:90%;padding:16px 24px;background:#173d32;color:#fffefa;'
          + 'font:17px/1.5 system-ui;z-index:10000;border-radius:9px;box-shadow:0 4px 25px #0002';
        document.body.appendChild(box);
      }
      box.textContent = text;
    }""",
        text,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8017")
    parser.add_argument("--output", type=Path, default=Path("docs/assets/walkthrough.webm"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1280, "height": 900},
            record_video_dir="artifacts/video-raw",
            record_video_size={"width": 1280, "height": 900},
        )
        page = context.new_page()
        started = time.monotonic()
        page.goto(args.url, wait_until="networkidle")
        caption(
            page,
            "PolicyTime finds the policy that applied to a person on an expense date. "
            "This demo uses fictional policies and exact source passages, without an LLM.",
        )
        page.wait_for_timeout(10000)
        page.locator(".workspace-heading").scroll_into_view_if_needed()
        caption(
            page,
            "First: a Brazilian employee's hotel expense on 15 June 2026. "
            "The expense date determines which version applies.",
        )
        page.get_by_role("button", name="Find the applicable policy").click()
        page.locator('[data-outcome="answered"]').wait_for()
        page.wait_for_timeout(12000)
        caption(
            page,
            "The June limit is BRL 180 per night. Open the evidence to inspect "
            "the exact clause and its effective period.",
        )
        page.locator(".sources").scroll_into_view_if_needed()
        page.wait_for_timeout(10000)
        page.get_by_label("Compare with another date").check()
        page.get_by_role("button", name="Find the applicable policy").click()
        page.locator(".result-card").nth(1).wait_for()
        page.locator(".result-card").nth(1).scroll_into_view_if_needed()
        caption(
            page,
            "Move the expense to July: the limit becomes BRL 220. "
            "A newer policy does not rewrite an older expense.",
        )
        page.wait_for_timeout(14000)
        page.get_by_label("Compare with another date").uncheck()
        page.get_by_role("button", name="A contractor's regional exception").click()
        expect(page.locator('[data-outcome="answered"]')).to_have_count(1)
        expect(page.locator(".answer-text")).to_contain_text("BRL 180")
        page.locator("#answer-panel").scroll_into_view_if_needed()
        caption(
            page,
            "For a contractor, an explicit exception replaces only the limit. "
            "Receipt requirements still apply. Policy precedence is computed in Python.",
        )
        page.wait_for_timeout(14000)
        page.locator(".selection-details summary").click()
        page.locator(".selection-details").scroll_into_view_if_needed()
        caption(
            page,
            "The decision trail explains which clauses applied, which were out of date, "
            "and which were replaced by an exception.",
        )
        page.wait_for_timeout(11000)
        page.get_by_role("button", name="Two policies that disagree").click()
        page.locator('[data-outcome="conflict"]').wait_for()
        page.locator("#answer-panel").scroll_into_view_if_needed()
        caption(
            page,
            "These US meals policies disagree without a precedence rule. "
            "PolicyTime surfaces the conflict instead of choosing a convenient answer.",
        )
        page.wait_for_timeout(14000)
        page.goto(args.url + "/policies", wait_until="networkidle")
        caption(
            page,
            "The public library contains 24 synthetic documents, 53 clauses, "
            "six topics and two countries. Every cited source can be inspected.",
        )
        page.wait_for_timeout(10000)
        page.goto(args.url + "/about", wait_until="networkidle")
        caption(
            page,
            "The live architecture adds PostgreSQL hybrid search, PyTorch reranking "
            "and LangChain/Mistral explanations. Evaluation results distinguish each component.",
        )
        remaining = max(0, 120 - (time.monotonic() - started))
        page.wait_for_timeout(remaining * 1000)
        video = page.video
        context.close()
        video.save_as(args.output)
        browser.close()
        print(args.output)


if __name__ == "__main__":
    main()
