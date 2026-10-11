# POSTiT frontend

The frontend is a lightweight, static HTML/CSS/JavaScript client for the Django REST API in `../Backend`. It follows a member-first social-app flow:

1. Visitors open `index.html` and are sent to sign in.
2. New visitors can create an account from the sign-in screen.
3. A successful sign-in or registration opens the authenticated feed.
4. Members can explore public posts and people, follow accounts, manage their profile and photos, and view or manage notifications.
5. Platform moderation is available only to administrator-role accounts, and the server remains the authority for permissions.

## Run locally

Start Django in one terminal:

```powershell
Set-Location ..\Backend
python manage.py runserver
```

Serve the static frontend from the repository root in a second terminal:

```powershell
python -m http.server 5173 --directory Frontend
```

Open `http://127.0.0.1:5173/` (or serve the frontend on port `3000` or `3002`). The development backend must be running at `http://127.0.0.1:8000`; Django's development CORS/CSRF settings allow all three ports.

The default API origin is `http://127.0.0.1:8000`. To use another backend, open the frontend with `?api=http://your-backend-host:port`; the selected origin is saved in local storage as `postit-api-origin`. You can also clear that key in the browser's local storage to restore the default. Feed suggestions and unread notification counts come from authenticated API endpoints; no sample accounts or posts are bundled in the frontend.

## Pages

- `index.html`: redirects visitors to sign-in and signed-in members to their feed.
- `pages/login.html`, `pages/register.html`: account access.
- `pages/feed.html`: personalized feed, post creation, and post/comment actions.
- `pages/profile.html`: view a profile; owners can edit profile fields, upload profile media, and remove their own gallery images.
- `pages/search.html`: post search and people discovery with follow controls. The People tab lists all active accounts except the signed-in user by default; the search box filters that list.
- `pages/notifications.html`: view notifications and mark one or all as read.
- `pages/admin.html`: dashboard, content/account/media moderation, relationship monitoring, audit log, and platform limits.

## Current backend boundaries

Direct messages, saved posts, password reset, and direct post permalinks are not implemented by the backend. The interface identifies these features as unavailable instead of simulating them. The frontend uses Django session authentication and CSRF protection; requests include credentials and obtain a CSRF token before state-changing actions.

Both light and GitHub-dark themes are available from the theme toggle and persist in local storage. Sign-in and registration use the POSTiT Django session API and database; the reference frontend's sample accounts and browser-only demo session are not used.
