/**
 * Utility formatting functions for CareerPulse analytics dashboard.
 */

/**
 * Formats a numeric value with thousands separators.
 * Example: 15420 -> "15,420", 99 -> "99"
 */
export function formatNumber(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  const num = typeof value === "number" ? value : Number(value);
  if (isNaN(num)) {
    return String(value);
  }
  return num.toLocaleString();
}

/**
 * Formats an annual salary value into a clean currency string.
 * Example: 161966.64 -> "$161,967", 750000 -> "$750,000"
 */
export function formatCurrency(
  value: number | string | null | undefined,
  compact = false
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  const num = typeof value === "number" ? value : Number(value);
  if (isNaN(num)) {
    return String(value);
  }

  const isNeg = num < 0;
  const abs = Math.abs(num);
  const sign = isNeg ? "-" : "";

  if (compact) {
    if (abs >= 1000000) {
      return `${sign}$${(abs / 1000000).toFixed(1)}M`;
    }
    if (abs >= 1000) {
      return `${sign}$${Math.round(abs / 1000)}k`;
    }
    return `${sign}$${Math.round(abs)}`;
  }

  return `${sign}$${Math.round(abs).toLocaleString()}`;
}

/**
 * Formats a percentage value to a clean representation without misleading precision.
 * Example: 8.0808 -> "8.1%", 35.5 -> "35.5%"
 */
export function formatPercent(
  value: number | string | null | undefined,
  decimals = 1
): string {
  if (value === null || value === undefined || value === "") {
    return "—";
  }
  if (typeof value === "string" && value.endsWith("%")) {
    return value;
  }
  const num = typeof value === "number" ? value : Number(value);
  if (isNaN(num)) {
    return String(value);
  }
  return `${Number(num.toFixed(decimals))}%`;
}

/**
 * Formats an ISO timestamp into a human-readable date and time.
 * Example: "2026-09-19T10:28:48.717422Z" -> "Sep 19, 2026, 10:28 AM"
 */
export function formatDate(date: string | Date | null | undefined): string {
  if (!date) return "—";
  try {
    const d = typeof date === "string" ? new Date(date) : date;
    if (isNaN(d.getTime())) return "—";
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  } catch {
    return "—";
  }
}

/**
 * Calculates percentage of a subset relative to total count.
 * Example: calculatePercentage(14, 99) -> "14.1%"
 */
export function calculatePercentage(
  count: number,
  total: number,
  decimals = 1
): string {
  if (!total || total <= 0 || !count || count <= 0) {
    return "0%";
  }
  const pct = (count / total) * 100;
  return `${Number(pct.toFixed(decimals))}%`;
}

/**
 * Truncates long label strings gracefully for chart axes.
 * Example: "Interaction Design Foundation" (16) -> "Interaction D..."
 */
export function truncateText(text: string, maxLength = 16): string {
  if (!text) return "";
  if (text.length <= maxLength) return text;
  return `${text.slice(0, maxLength - 3)}...`;
}
