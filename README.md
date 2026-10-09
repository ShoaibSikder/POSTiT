# POSTiT

POSTiT is a small social application with a Django REST Framework backend,
PostgreSQL persistence, session authentication, local development media
storage, and a vanilla HTML/CSS/JavaScript frontend. The backend is split into
domain apps rather than a single generic CRUD module.

## Backend structure

| App | Responsibility |
| --- | --- |
| `config` | Environment-specific settings, root URLs, ASGI and WSGI |
| `accounts` | Custom user, registration, session authentication and roles |
| `profiles` | Public profiles, avatars, cover images and profile gallery |
| `posts` | Post lifecycle, images, validation, filtering and engagement queries |
| `comments`, `likes`, `follows` | Separate interaction records and ownership rules |
| `feed` | Chronological posts from the signed-in user and followed accounts |
| `search` | Paginated user and post search, date/author filters, aggregate search activity |
| `notifications` | Persisted follow/like/comment notifications and read state |
| `moderation` | Protected admin APIs, account controls, content moderation and platform limits |
| `audit` | Append-only records of administrator actions |
| `common` | Shared validation, permissions and pagination |

The implementation follows the supplied project document's scope: ordinary
users can manage only their own content, and admin access is checked by the
backend on every protected request. Search activity stores its category,
account, and timestamp, not the user's raw query.

## Windows PowerShell setup

From `POSTiT\Backend`, prepare the environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit the ignored local `.env` privately. Configure `DJANGO_SECRET_KEY` and
`POSTIT_DB_NAME`, `POSTIT_DB_USER`, `POSTIT_DB_PASSWORD`, `POSTIT_DB_HOST`, and
`POSTIT_DB_PORT`. Database credentials and `.env` must never be committed.
Development settings load this local file; production settings require
environment-provided secrets and host configuration.

The first migration already creates the custom `accounts.User` model. Apply
the checked-in migrations only after the PostgreSQL role/database and private
environment values are configured:

```powershell
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Do not run `makemigrations` as a deployment step; migrations are source
controlled. For offline tests, Django uses the project's in-memory SQLite
test settings:

```powershell
$env:DJANGO_SETTINGS_MODULE = "config.settings.test"
$env:PYTHONDONTWRITEBYTECODE = "1"
python manage.py test accounts profiles posts comments likes follows feed search notifications moderation audit common tests
```

## API overview

All application routes use `/api/v1/`. Unsafe session-authenticated browser
requests must send the CSRF cookie token in `X-CSRFToken`.

### Authentication and user content

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `auth/csrf/` | Obtain CSRF token |
| `POST` | `auth/register/` | Create a standard user and start a session |
| `POST` | `auth/login/` | Start a session using username or email |
| `POST` | `auth/logout/` | End the session |
| `GET` | `auth/me/` | View the authenticated account |
| `GET`, `PATCH` | `users/<username>/` | View a public profile; owner-only edit |
| `GET`, `PATCH` | `profiles/me/` | View or edit the current profile |
| `GET`, `POST` | `users/<username>/media/` | List or add the owner's profile gallery media |
| `DELETE` | `profile-media/<id>/` | Remove own gallery media |
| `GET`, `POST` | `posts/` | List or create posts |
| `GET`, `PATCH`, `DELETE` | `posts/<id>/` | Read or manage an owned post |
| `GET` | `users/<username>/posts/` | List a user's posts |
| `GET`, `POST` | `posts/<id>/comments/` | List or add comments |
| `GET`, `PATCH`, `DELETE` | `comments/<id>/` | Read or manage an owned comment |
| `POST`, `DELETE` | `posts/<id>/like/` | Like or unlike a post |
| `POST`, `DELETE` | `users/<username>/follow/` | Follow or unfollow a user |
| `GET` | `users/<username>/followers/` | List followers |
| `GET` | `users/<username>/following/` | List followed accounts |
| `GET` | `feed/` | Personalized, paginated chronological feed |
| `GET` | `search/users/?q=<term>` | Case-insensitive username/name search |
| `GET` | `search/posts/?q=<term>&author=<username>&from=<date>&to=<date>` | Search posts with optional author/date filters |
| `GET` | `notifications/` | List own notifications and unread count |
| `POST` | `notifications/<id>/read/` | Mark an owned notification as read |
| `POST` | `notifications/read-all/` | Mark all own notifications as read |

Lists are paginated (`page` and optional `page_size`, maximum 100). Post
responses include live like/comment counts and the caller's like state. Feed
responses also include `is_own_post`. Profile and post uploads use
`multipart/form-data`; repeated `images` fields attach post images and
`remove_image_ids` removes owned attachments during edits. Only verified JPEG,
PNG, and WebP images are accepted.

During local development, uploaded files are stored under `Backend\media\posts`
or `Backend\media\profiles` (with year/month subdirectories). These directories
are kept in Git with placeholders, while uploaded files remain ignored. In
production, configure protected media storage and serving separately.

### Administrator APIs

All administrator APIs require an active account with both the administrator
role and Django staff permission. They are served under `/admin/`:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `admin/dashboard/` | Global counts and recent administrator actions |
| `GET` | `admin/users/?q=&status=` | Search/filter user accounts |
| `POST` | `admin/users/<id>/ban/`, `unban/`, `deactivate/`, `activate/` | Manage account access; POST body must include a short `reason` |
| `GET`, `DELETE` | `admin/posts/`, `admin/posts/<id>/` | Inspect/remove any post |
| `GET`, `DELETE` | `admin/comments/`, `admin/comments/<id>/` | Inspect/remove any comment |
| `GET` | `admin/media/<post\|profile>/` | Review paginated post or profile gallery media |
| `DELETE` | `admin/media/<post\|profile\|avatar\|cover>/<id>/` | Remove a media item with an audited reason |
| `GET`, `DELETE` | `admin/notifications/`, `admin/notifications/<id>/` | Monitor/filter or remove a notification |
| `GET` | `admin/relationships/` | Inspect aggregate and recent follow activity |
| `GET` | `admin/activity/?from=&to=&type=` | Inspect date/type-filtered activity aggregates |
| `GET` | `admin/audit/?actor=&action=&target=` | Review administrator audit records |
| `GET`, `PUT` | `admin/settings/` | Read/update supported operational limits |

Admin content/media/notification deletion requires a reason, and the action is
recorded with the administrator, target, timestamp, IP when available, and
reason. Audit records have no public write endpoint and are append-only.
Self-service registration cannot grant an admin role. The last active staff
administrator cannot be deactivated or banned. Admin-configured operational
limits are validated against supported ceilings and apply to new uploads and
content.

## Configuration

Image bytes, post image count, profile gallery count, post text length, and
comment text length have conservative development defaults and can be
overridden through the protected admin settings API. Configure the production
web server to serve media safely; Django serves local media only in development.
