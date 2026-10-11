import { initShell } from "../app.js";

const user = await initShell();
window.location.replace(user ? "pages/feed.html" : "pages/login.html");
