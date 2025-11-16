🔄 Automated Job Aggregator Workflow (LinkedIn + GitHub + Notion + Discord)

This repository contains an n8n workflow that automatically fetches the latest tech job postings from multiple sources, processes them, stores them in Notion, and optionally sends real-time updates to Discord.

This system is fully automated and can also be triggered manually by Discord commands.

🚀 Features
🔍 1. Multi-Source Job Scraping

The workflow collects jobs from:

LinkedIn (DevOps roles)

LinkedIn (Backend roles)

GitHub Job Boards (daily job posting lists)

🧠 2. Smart Job Normalization

The workflow:

Cleans and normalizes job data

Extracts job ID, title, company, location, and posting date

Fixes incomplete LinkedIn URLs

Standardizes city/state data

➕ 3. Deduplication Against Notion

Before inserting new jobs, the workflow:

Retrieves all existing records from Notion

Compares job IDs

Inserts only new unique jobs

📦 4. Notion Database Integration

Every new job is inserted into a Notion database using:

Title fields

Rich text

URL fields

Timestamp fields

Tags & classify source (Backend, DevOps, GitHub)

🔔 5. Discord Notifications

When new jobs are found:

A Discord webhook sends a structured embed message

Shows company, role, location, employment type, remote option

Includes job URL and posting timestamp

💬 6. Discord Command Trigger

Users can manually trigger a fetch by sending messages like:

!fetch jobs
fetch jobs
find jobs

🕒 7. Runs Every 1 Minute

The Schedule Trigger keeps the workflow running continuously.

🧱 Workflow Architecture
Discord Message Listener → Command Parser
        ↓ (optional trigger)
 Schedule Trigger (1 min)
        ↓
 Pagination Builder → LinkedIn HTTP Requests (Backend + DevOps)
        ↓
 HTML Parser (extract title, company, location, URL)
        ↓
 GitHub Scraper (New-Grad job boards)
        ↓
 Data Normalizer
        ↓
 Existing Jobs from Notion
        ↓
 Merge & Deduplicate
        ↓
 ├─→ Insert New Jobs Into Notion
 └─→ Create Discord Embed Payload → Send to Discord

🛠️ Setup Instructions
1️⃣ Install n8n

Self-hosted or Cloud.

2️⃣ Add Required Credentials
🔹 LinkedIn OAuth

Add a credential named:
LinkedIn_Credential_ID

🔹 Notion API

Add a credential named:
Notion Account

Grant access to your Notion database.

🔹 Discord Bot Credential

Add:
Discord_Credential_ID

Also set:

Guild ID (server ID)

Channel ID

(Optional) Webhook URL

🔹 Notion Database IDs

Replace placeholders:

Notion_Database_ID
Notion_Databse_ID


with your actual database ID.

🧩 Required Node Types
Node	Purpose
Schedule Trigger	Runs workflow every minute
HTTP Request	Fetch LinkedIn + GitHub job data
HTML Extract	Parse job cards from HTML
Notion	Fetch + Insert job entries
Code Nodes	Normalize, dedupe, convert, and build payloads
Discord Bot API	Listen to messages & handle triggers
Discord Webhook	Send job notifications
📬 Discord Notifications Example

Jobs are sent as embeds such as:

🔥 6 New Jobs Found!

Field	Value
🏢 Company	Google
📍 Location	New York, USA
💼 Type	Full-time
🏠 Remote	Hybrid
🔗 URL	linkedin.com/jobs/...
✔️ Security Notes

This version of the workflow includes:

🔒 No API keys

🔒 No OAuth secrets

🔒 No personal Notion URLs

🔒 No Discord webhook URLs

🔒 No credential IDs

🔒 No personal directory paths

Safe to publish publicly.

📎 Importing the Workflow

Copy the JSON in this repository

Go to n8n → Import Workflow → Paste JSON

Replace placeholder IDs with your actual credential and database IDs

Start your workflow! 🚀
