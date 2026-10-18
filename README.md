# FindBack Lost & Found System

Campus lost-and-found with two views:

- **Student view** — report a lost item (name, photo, where it was missed), search lost/found items, and see when admin marks an item found.
- **Admin view** — receive alerts for new lost reports, search the board, and mark a lost item as found.

## Run the app

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
python -m flask --app backend.app run --debug --port 5000
```

Open `http://localhost:5000`.

## Run with Docker

```powershell
docker build -t cloud:latest .
docker run --name findback -p 8080:8080 -v "${PWD}\backend:/app/backend" cloud:latest
```

Open `http://localhost:8080`. The SQLite database and uploaded images are kept in `backend` on your computer.

## Demo accounts

- Admin: `admin@campus.edu` / `admin123` (choose **Admin view** on the login page)
- Student: create a new account from **Student view**, then sign in
- Admin: create an account from **Admin view**, or use the demo account above

## How the flow works

1. A student reports a lost item with a photo and last-seen location.
2. Admin receives a notification on the admin desk.
3. Admin searches lost/found items and clicks **Mark as found**.
4. Students see the updated **FOUND** status on the board and on My reports.
