GitHub Commit Monitor Automation
Real-time commit tracking using GitHub API + n8n + Discord/Slack/Teams/Telegram
🚀 Overview

At my workplace, we often struggled with questions like:

Who pushed the latest code?

When was it pushed?

What exactly changed?

To solve this, I built an automated workflow using n8n, GitHub API, and webhooks, which sends instant commit notifications to Discord (and can also work with Slack, Teams, Email, Telegram, etc.).

This automation provides every team member with real-time, structured commit visibility without manual checking.

✅ Features
🔍 Intelligent Commit Detection

Fetches the latest commit via GitHub API

Compares with previously stored commit SHA

Sends notifications only when a new commit is detected

📢 Multi-Platform Notifications

Supports:

Discord (enabled by default)

Slack

Microsoft Teams

Telegram

Email

Any Webhook-compatible service

🧾 Notification Includes:

Commit author

Timestamp

Commit message

SHA

Direct link to commit

(Optional) Changed files

💾 Persistent State

Stores SHA in lastCommit.txt

Prevents duplicate notifications

🛠️ Technologies Used
Technology	Purpose
n8n	Workflow Automation
GitHub API	Commit Data
Discord Webhook	Notifications
JavaScript	Logic inside n8n Code Nodes
Local Storage	Track last commit
📂 Workflow Structure
Cron (every minute)
        │
        ▼
Fetch Latest Commit (GitHub API)
        │
        ▼
Read Last Commit (local file)
        │
        ▼
Compare SHAs
   ┌─────────────┴────────────┐
   │                           │
 SAME COMMIT            NEW COMMIT FOUND
   │                           │
   ▼                           ▼
 Stop Workflow         Build Discord Message
                                │
                                ▼
                       Send Discord Webhook
                                │
                                ▼
                       Update lastCommit.txt
