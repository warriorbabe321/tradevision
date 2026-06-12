# TradeVision AI - Render Deployment Guide (Updated)

This guide provides exact steps for the owner to update the existing `tradevision` service on Render or create a new one.

## 1. Updating the Existing Service ('tradevision')

Since you already have a service named `tradevision` on Render, follow these steps to ensure it is running the Phase 4 code.

### Step 1: Push the Latest Code
We have synchronized the latest Phase 4 codebase to the following repositories:
*   **Primary (Owner):** `warriorbabe321/CTO-Tradevision`
*   **Internal:** `warriorbabe321/tradevision`

Ensure the code is on the **`main`** branch of the linked repository. If auto-deploy is enabled on Render, pushing to `main` will trigger a build automatically.

### Step 2: Manual Redeploy (If needed)
1.  Go to your [Render Dashboard](https://dashboard.render.com).
2.  Click on the `tradevision` service.
3.  Click the **Manual Deploy** button.
4.  Select **Clear Build Cache & Deploy** to ensure a fresh environment.

---

## 2. Creating a New Web Service (Step-by-Step)

If you need to create a fresh service, follow these exact settings:

1.  **Start**: Click **New +** > **Web Service**.
2.  **Repository**: Connect the `warriorbabe321/CTO-Tradevision` repository.
3.  **General Settings**:
    *   **Name**: `tradevision-ai`
    *   **Region**: `Oregon (US West)` (or closest to you)
    *   **Branch**: `main`
    *   **Runtime**: `Python 3`
4.  **Build & Start Commands**:
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --timeout 120`
5.  **Instance Type**: `Starter` (Recommended for database persistence).

---

## 3. Database Configuration (SQLite & Turso)

The platform automatically detects if it is running on Render and switches to a production-ready database mode.

### Option A: Local SQLite (Simple)
To use a local database file on Render:
1.  **Persistent Disk**: You **must** add a disk to keep data across restarts.
    *   Go to **Settings** > **Disks** > **Add Disk**.
    *   **Name**: `tradevision-data`
    *   **Mount Path**: `/etc/data`
    *   **Size**: `1GB` (Minimum is fine)
2.  **Environment Variable**:
    *   Add `DATABASE_URL` = `/etc/data/tradevision.db` in the **Environment** tab.

### Option B: Turso (Advanced/Scaling)
If you prefer a cloud-hosted SQLite database (Turso):
1.  **Environment Variables**:
    *   `DATABASE_URL`: Your Turso connection URL.
    *   `RENDER`: `true` (Triggers the SQLite-compatible logic).

---

## 4. Required Environment Variables

Ensure these are set in the **Environment** tab of your Render service:

| Key | Value | Note |
| :--- | :--- | :--- |
| `PYTHON_VERSION` | `3.10.12` | Recommended version |
| `RENDER` | `true` | Required for DB detection |
| `SECRET_KEY` | `your-random-secret-key` | For session security |

## 5. Troubleshooting Gunicorn

*   **Bind Error**: The app is configured to bind to `0.0.0.0:$PORT`. Ensure the Start Command includes `--bind 0.0.0.0:$PORT`.
*   **Timeouts**: We added `--timeout 120` to the Start Command because fetching stock data can sometimes take longer than the default 30 seconds.

---

## 6. Verification

Once deployed, visit the site.
1.  **Login**: Use your access key from `access_keys.json`.
2.  **Analyze**: Run an analysis for 'NVDA' or 'AAPL'.
3.  **Dashboard**: Verify that the "Recently Analyzed" section updates, confirming that the database is working.
