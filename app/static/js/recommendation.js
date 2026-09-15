// Fetches the recommendation feed via the JSON API (used by future
// client-side enhancements; the server-rendered pages work without this).
async function fetchRecommendations(filter) {
    const url = filter ? `/api/recommendations?filter=${encodeURIComponent(filter)}` : "/api/recommendations";
    const res = await fetch(url);
    if (!res.ok) return [];
    return res.json();
}
