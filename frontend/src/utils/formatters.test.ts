import { describe, it, expect } from "vitest";
import {
  formatCurrency,
  formatNumber,
  formatPercent,
  formatDate,
  calculatePercentage,
  truncateText,
} from "./formatters";

describe("Formatters Unit Tests", () => {
  describe("formatCurrency", () => {
    it("formats positive compact values correctly", () => {
      expect(formatCurrency(101957.85, true)).toBe("$102k");
      expect(formatCurrency(1500000, true)).toBe("$1.5M");
      expect(formatCurrency(500, true)).toBe("$500");
      expect(formatCurrency(0, true)).toBe("$0");
    });

    it("formats negative compact values with negative sign before dollar sign", () => {
      expect(formatCurrency(-101957.85, true)).toBe("-$102k");
      expect(formatCurrency(-1500000, true)).toBe("-$1.5M");
      expect(formatCurrency(-500, true)).toBe("-$500");
    });

    it("formats standard positive and negative non-compact currency", () => {
      expect(formatCurrency(101957.85, false)).toBe("$101,958");
      expect(formatCurrency(-101957.85, false)).toBe("-$101,958");
      expect(formatCurrency(0, false)).toBe("$0");
    });

    it("handles null, undefined, empty string and NaN gracefully", () => {
      expect(formatCurrency(null)).toBe("—");
      expect(formatCurrency(undefined)).toBe("—");
      expect(formatCurrency("")).toBe("—");
      expect(formatCurrency("not-a-number")).toBe("not-a-number");
    });
  });

  describe("formatNumber", () => {
    it("formats numbers with thousands separators", () => {
      expect(formatNumber(15420)).toBe("15,420");
      expect(formatNumber(99)).toBe("99");
      expect(formatNumber(0)).toBe("0");
    });

    it("handles null and undefined", () => {
      expect(formatNumber(null)).toBe("—");
      expect(formatNumber(undefined)).toBe("—");
      expect(formatNumber("")).toBe("—");
    });
  });

  describe("formatPercent", () => {
    it("formats decimal percentages", () => {
      expect(formatPercent(8.0808)).toBe("8.1%");
      expect(formatPercent(35.5)).toBe("35.5%");
      expect(formatPercent("50%")).toBe("50%");
    });

    it("handles null and undefined", () => {
      expect(formatPercent(null)).toBe("—");
      expect(formatPercent(undefined)).toBe("—");
    });
  });

  describe("calculatePercentage", () => {
    it("calculates percentage accurately", () => {
      expect(calculatePercentage(14, 99)).toBe("14.1%");
      expect(calculatePercentage(85, 99)).toBe("85.9%");
      expect(calculatePercentage(8, 14)).toBe("57.1%");
      expect(calculatePercentage(0, 99)).toBe("0%");
      expect(calculatePercentage(10, 0)).toBe("0%");
    });
  });

  describe("truncateText", () => {
    it("truncates long strings with ellipsis", () => {
      expect(truncateText("Interaction Design Foundation", 16)).toBe("Interaction D...");
      expect(truncateText("Short", 16)).toBe("Short");
      expect(truncateText("", 16)).toBe("");
    });
  });

  describe("formatDate", () => {
    it("formats ISO timestamps", () => {
      const formatted = formatDate("2026-09-19T10:28:48.717422Z");
      expect(formatted).not.toBe("—");
      expect(formatDate(null)).toBe("—");
      expect(formatDate("invalid-date")).toBe("—");
    });
  });
});
