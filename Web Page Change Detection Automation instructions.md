This workflow automatically monitors the BBC News homepage for any content changes and sends you an instant alert through Telegram whenever updates occur.
It is ideal for tracking breaking news, political updates, or changes on the BBC front page in real time.

🚀 Features
🔄 1. Auto-Monitor BBC News Homepage

The workflow fetches the HTML content of:

https://www.bbc.com/news


every minute using the Cron trigger.

🧠 2. Smart HTML Change Detection

The workflow compares:

Previously saved HTML

Newly fetched HTML

To avoid false alarms, it cleans both HTML blocks by:

✔ Removing whitespace
✔ Removing <script> tags
✔ Ignoring dynamic ad-timers or JS-generated elements

This ensures alerts only trigger when the real, visible content changes.

💬 3. Instant Telegram Alerts

When the workflow detects a change, it sends a Telegram message:

Changes Detected


You can customize this message as needed.

💾 4. Saves Latest HTML Snapshot

After sending the alert, the automation updates the stored HTML file:

Reads previous file from: HTML_File_Path

Writes new HTML to: HTML_FilePath

(Replace these placeholders with your exact path.)

🧱 Workflow Overview
Cron (every minute)
     ↓
Fetch New HTML (BBC News)
     ↓
Read Old HTML (local file)
     ↓
Compare (clean + diff)
     ↓
If Changed?
     ├── Yes → Send Telegram
     └── Yes → Update Old HTML

📌 Node Descriptions
Node Name	Purpose
Cron	Triggers workflow every minute
Fetch New HTML	Downloads latest BBC News homepage
Read Old HTML	Loads previously saved HTML file
Compare	Cleans + compares old and new HTML
If Changed	Decides whether a Telegram alert should be sent
Send Telegram	Sends the “Changes Detected” message
Update Old HTML	Saves the latest HTML to disk
⚙️ Setup Instructions
1. Prepare Local File Storage

Replace these placeholders in the workflow:

HTML_File_Path
HTML_FilePath


with the actual full path where you want to store the HTML snapshot, such as:

C:\Users\yourname\N8N_files\BBC_News.html


Create the folder manually if it does not exist.

2. Initialize the First HTML File

Before running the workflow:

Create an empty file at your chosen path (e.g. BBC_News.html)

Save it so that Read Old HTML can access it the first time.

3. Configure Telegram

Inside the Send Telegram node:

Field	Replace With
chatId	Your Telegram chat ID
credentials	Your Telegram Bot token

If you don’t have a bot:

Open Telegram

Search @BotFather

Run /newbot and create a bot

Copy token

Add token to n8n Telegram API Credential

Send a message to your bot

Use getUpdates API or a helper bot (e.g. @chatIDrobot) to get chat ID

4. Import Workflow to n8n

Open n8n

Go to Import → Paste JSON

Save and activate workflow

You're ready to monitor BBC News automatically 🚀

🐞 Troubleshooting
❌ Error: File could not be accessed

Check:

Did you create the folder?

Did you create the initial empty file?

Does n8n have permission?

❌ No message arriving on Telegram

Check:

Telegram bot token is correct

You have sent at least one message to the bot

Chat ID is correct

Workflow is active in n8n

❌ Workflow always shows changed = true

BBC updates dynamic content every second.

Fix: Add more cleaning steps (we can tune script if needed).
