"use strict";

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#question-form");
  if (!form) return;

  const toggle = document.querySelector("#compare-toggle");
  const compareField = document.querySelector("#compare-field");
  const compareDate = document.querySelector("#compare_date");
  toggle.addEventListener("change", () => {
    compareField.hidden = !toggle.checked;
    compareDate.disabled = !toggle.checked;
    compareDate.required = toggle.checked;
  });

  document.querySelectorAll("[data-example]").forEach((button) => {
    button.addEventListener("click", () => {
      form.elements.question.value = button.dataset.question;
      form.elements.expense_date.value = button.dataset.date;
      form.elements.country.value = button.dataset.country;
      form.elements.employment_type.value = button.dataset.employment;
      form.requestSubmit();
    });
  });

  document.body.addEventListener("htmx:sendError", () => {
    const panel = document.querySelector("#answer-panel");
    panel.textContent = "The connection was interrupted. Please try your question again.";
  });

  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id !== "answer-panel" || window.innerWidth > 650) return;
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    event.detail.target.scrollIntoView({behavior: reducedMotion ? "instant" : "smooth", block: "start"});
  });
});
