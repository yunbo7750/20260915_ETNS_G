// Minimal client helper for the cart API (server-rendered form is the
// primary interface; this is available for future AJAX enhancements).
async function fetchCart() {
    const res = await fetch("/api/cart");
    if (!res.ok) return null;
    return res.json();
}
