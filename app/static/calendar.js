(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.TrainingCalendar = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  const DAY_INDEX = {
    Montag: 0,
    Dienstag: 1,
    Mittwoch: 2,
    Donnerstag: 3,
    Freitag: 4
  };

  function parseIsoDate(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ""))) return null;
    const [year, month, day] = value.split("-").map(Number);
    const date = new Date(year, month - 1, day, 12, 0, 0, 0);
    if (date.getFullYear() !== year || date.getMonth() !== month - 1 || date.getDate() !== day) return null;
    return date;
  }

  function addDays(value, amount) {
    if (!value) return null;
    const date = new Date(value.getTime());
    date.setDate(date.getDate() + amount);
    return date;
  }

  function mondayOfWeek(value) {
    if (!value) return null;
    const monday = new Date(value.getTime());
    const weekday = monday.getDay();
    const distance = weekday === 0 ? -6 : 1 - weekday;
    monday.setDate(monday.getDate() + distance);
    return monday;
  }

  function dateForCalendarDay(startDateIso, week, dayName) {
    const start = parseIsoDate(startDateIso);
    if (!start || !(dayName in DAY_INDEX)) return null;
    const monday = mondayOfWeek(start);
    return addDays(monday, (Math.max(1, Number(week) || 1) - 1) * 7 + DAY_INDEX[dayName]);
  }

  function formatGermanDate(value) {
    if (!value) return "";
    return `${String(value.getDate()).padStart(2, "0")}.${String(value.getMonth() + 1).padStart(2, "0")}.${value.getFullYear()}`;
  }

  function key(value) {
    return value ? `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, "0")}-${String(value.getDate()).padStart(2, "0")}` : "";
  }

  function easterSunday(year) {
    const a = year % 19;
    const b = Math.floor(year / 100);
    const c = year % 100;
    const d = Math.floor(b / 4);
    const e = b % 4;
    const f = Math.floor((b + 8) / 25);
    const g = Math.floor((b - f + 1) / 3);
    const h = (19 * a + b - d - g + 15) % 30;
    const i = Math.floor(c / 4);
    const k = c % 4;
    const l = (32 + 2 * e + 2 * i - h - k) % 7;
    const m = Math.floor((a + 11 * h + 22 * l) / 451);
    const month = Math.floor((h + l - 7 * m + 114) / 31);
    const day = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(year, month - 1, day, 12, 0, 0, 0);
  }

  function holidayHints(value) {
    if (!value) return [];
    const year = value.getFullYear();
    const current = key(value);
    const easter = easterSunday(year);
    const entries = [];
    const add = (country, name, date) => {
      if (key(date) === current) entries.push(`${country}: ${name}`);
    };
    const fixed = (month, day) => new Date(year, month - 1, day, 12, 0, 0, 0);

    // Deutschland: bundesweit geltende gesetzliche Feiertage.
    add("DE", "Neujahr", fixed(1, 1));
    add("DE", "Karfreitag", addDays(easter, -2));
    add("DE", "Ostermontag", addDays(easter, 1));
    add("DE", "Tag der Arbeit", fixed(5, 1));
    add("DE", "Christi Himmelfahrt", addDays(easter, 39));
    add("DE", "Pfingstmontag", addDays(easter, 50));
    add("DE", "Tag der Deutschen Einheit", fixed(10, 3));
    add("DE", "1. Weihnachtstag", fixed(12, 25));
    add("DE", "2. Weihnachtstag", fixed(12, 26));

    // Oesterreich: bundesweit geltende gesetzliche Feiertage.
    add("AT", "Neujahr", fixed(1, 1));
    add("AT", "Heilige Drei Koenige", fixed(1, 6));
    add("AT", "Ostermontag", addDays(easter, 1));
    add("AT", "Staatsfeiertag", fixed(5, 1));
    add("AT", "Christi Himmelfahrt", addDays(easter, 39));
    add("AT", "Pfingstmontag", addDays(easter, 50));
    add("AT", "Fronleichnam", addDays(easter, 60));
    add("AT", "Mariae Himmelfahrt", fixed(8, 15));
    add("AT", "Nationalfeiertag", fixed(10, 26));
    add("AT", "Allerheiligen", fixed(11, 1));
    add("AT", "Mariae Empfaengnis", fixed(12, 8));
    add("AT", "Christtag", fixed(12, 25));
    add("AT", "Stefanitag", fixed(12, 26));

    // Schweiz: nur die auf Bundesebene einheitliche Bundesfeier.
    add("CH", "Bundesfeier", fixed(8, 1));

    return entries;
  }

  return {
    parseIsoDate,
    dateForCalendarDay,
    formatGermanDate,
    holidayHints,
    easterSunday
  };
});
