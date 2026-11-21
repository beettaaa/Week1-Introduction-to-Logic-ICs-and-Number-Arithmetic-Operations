"use strict";

const DIGITS = "0123456789ABCDEF";
const BASES = [2, 8, 10, 16];
const NAMES = { 2: "Binary", 8: "Octal", 10: "Decimal", 16: "Hexadecimal" };

function parseValue(input, base) {
  let value = input.trim().toUpperCase();
  let negative = false;
  if (value.startsWith("-")) {
    negative = true;
    value = value.slice(1);
  }
  if (!value) throw new Error("Enter a number to continue.");

  let result = 0n;
  const radix = BigInt(base);
  for (const character of value) {
    const digit = DIGITS.indexOf(character);
    if (digit < 0 || digit >= base) {
      throw new Error(`“${character}” is not a valid digit in base ${base}.`);
    }
    result = result * radix + BigInt(digit);
  }
  return negative ? -result : result;
}

function formatValue(value, base) {
  return value.toString(base).toUpperCase();
}

function escapeHTML(value) {
  return String(value).replace(/[&<>"']/g, character => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[character]);
}

function baseRows(value) {
  return BASES.map(base =>
    `<tr><th scope="row">${NAMES[base]}</th><td class="mono">${escapeHTML(formatValue(value, base))}</td></tr>`
  ).join("");
}

function render(targetId, markup) {
  document.getElementById(targetId).innerHTML = markup;
}

function showError(targetId, error) {
  render(targetId, `<p class="err" role="alert">${escapeHTML(error.message)}</p>`);
}

function convertNumber() {
  const input = document.getElementById("cv").value;
  if (!input.trim()) {
    render("cout", "");
    return;
  }
  try {
    const base = Number(document.getElementById("cb").value);
    const result = parseValue(input, base);
    render("cout", `<div class="result-heading">Equivalent values</div><div class="scroll"><table aria-label="Converted values"><tbody>${baseRows(result)}</tbody></table></div>`);
  } catch (error) {
    showError("cout", error);
  }
}

function calculate() {
  const first = document.getElementById("a1").value;
  const second = document.getElementById("a2").value;
  if (!first.trim() && !second.trim()) {
    render("aout", "");
    return;
  }

  const base = Number(document.getElementById("ab").value);
  const operation = document.getElementById("ao").value;
  try {
    const left = parseValue(first, base);
    const right = parseValue(second, base);
    let resultMarkup;

    if (operation === "/") {
      if (right === 0n) throw new Error("Division by zero is undefined. Enter a non-zero second value.");
      const quotient = left / right;
      const remainder = left % right;
      resultMarkup = `<div class="out">Quotient: ${escapeHTML(formatValue(quotient, base))}<br>Remainder: ${escapeHTML(formatValue(remainder, base))}<br><span>All values are expressed in base ${base}.</span></div><h3>Quotient in every supported base</h3><div class="scroll"><table aria-label="Quotient in other bases"><tbody>${baseRows(quotient)}</tbody></table></div>`;
    } else {
      const result = operation === "+" ? left + right : operation === "-" ? left - right : left * right;
      resultMarkup = `<div class="out">${escapeHTML(formatValue(left, base))} ${operation} ${escapeHTML(formatValue(right, base))} = <strong>${escapeHTML(formatValue(result, base))}</strong><br><span>Result shown in base ${base}.</span></div><h3>Your result in every supported base</h3><div class="scroll"><table aria-label="Calculation result in other bases"><tbody>${baseRows(result)}</tbody></table></div>`;
    }
    render("aout", resultMarkup);
  } catch (error) {
    showError("aout", error);
  }
}

function activateTab(button) {
  const selected = button.dataset.tab;
  document.querySelectorAll("[data-tab]").forEach(tab => {
    const active = tab === button;
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  ["ics", "conv", "arith"].forEach(id => {
    document.getElementById(id).hidden = id !== selected;
  });
}

document.addEventListener("DOMContentLoaded", () => {
  ["cv", "cb"].forEach(id => document.getElementById(id).addEventListener("input", convertNumber));
  ["a1", "a2", "ao", "ab"].forEach(id => document.getElementById(id).addEventListener("input", calculate));

  const tabs = [...document.querySelectorAll("[data-tab]")];
  tabs.forEach((button, index) => {
    button.addEventListener("click", () => activateTab(button));
    button.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      let next = index;
      if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
      if (event.key === "ArrowLeft") next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = tabs.length - 1;
      tabs[next].focus();
      activateTab(tabs[next]);
    });
  });
});
