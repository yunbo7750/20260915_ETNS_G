// Minimal client helper for the calendar API (server-rendered form is the
// primary interface; this is available for future AJAX enhancements).
async function fetchCalendarEvents() {
    const res = await fetch("/api/calendar");
    if (!res.ok) return [];
    return res.json();
}
