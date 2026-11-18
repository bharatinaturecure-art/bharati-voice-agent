# Gemini WhatsApp Bots

A voice-based conversational agent built with **[Pipecat](https://docs.pipecat.ai/)** using the `SmallWebRTCTransport`.

This example also shows how to integrate with the **WhatsApp Business API** to handle **voice calls over WebRTC**.

Any Pipecat bot that uses `SmallWebRTCTransport` can connect to WhatsApp voice calling, simply configure WhatsApp as described here:
- 👉 [**Pipecat WhatsApp Business Calling API**](https://docs.pipecat.ai/guides/features/whatsapp)  

Learn how to run and deploy these bots on Pipecat Cloud.

---

## Setup

### 1. Clone this repository

```bash
git clone https://github.com/daily-co/pcc-gemini-whatsapp.git
cd pcc-gemini-whatsapp
```

### 2. Configure your API keys

Create your `.env` file:

```bash
cp env.example .env
```

Then, add your API keys:

```ini
GOOGLE_API_KEY=

# WhatsApp
WHATSAPP_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_APP_SECRET=

# Local development only
WHATSAPP_WEBHOOK_VERIFICATION_TOKEN=
```

### 3. Set up your virtual environment and install dependencies

```bash
uv sync
```

---

## Run Your Bot Locally

Start your bot:

```bash
uv run bot.py
```

Then open **[http://localhost:7860](http://localhost:7860)** and click **Connect** to start talking to your bot.

> The first startup can take up to ~20 seconds as Pipecat downloads required models and dependencies.

By default, this uses the **SmallWebRTC** prebuilt web UI for quick local testing.

---

### Testing with WhatsApp

If you want to test **WhatsApp calling** instead of the web UI, follow these steps:

1. **Expose your local server** using [ngrok](https://ngrok.com/) or a similar tunneling tool:

   ```bash
   ngrok http --domain=YOUR_NGROK_DOMAIN http://localhost:7860
   ```

2. **Copy the generated HTTPS URL** and set your WhatsApp webhook to:

   ```
   https://YOUR_NGROK_DOMAIN/whatsapp
   ```

   > ✅ **Important:** Always include the `/whatsapp` path at the end of your webhook URL.

3. **Configure your webhook** in your WhatsApp Business account, following the Pipecat documentation:  
   👉 [Configure Webhook — Pipecat WhatsApp Guide](https://docs.pipecat.ai/guides/features/whatsapp#2-configure-webhook)

Once configured, you can make a WhatsApp voice call to your **registered business number** — your Pipecat bot will automatically answer!

---

## Deploy to Production

Turn your local prototype into a scalable, production-ready service with **Pipecat Cloud** — including automatic scaling, monitoring, and global deployment.

### Prerequisites

1. **Sign up for [Pipecat Cloud](https://pipecat.daily.co/sign-up)**  
2. **Install [Docker](https://www.docker.com/)** and create a [Docker Hub](https://hub.docker.com/) account  
3. **Log in to Docker Hub:**

   ```bash
   docker login
   ```

4. **Authenticate with Pipecat Cloud CLI (included in this project):**

   ```bash
   uv run pcc auth login
   ```

> 💡 Tip: Use `pcc` as a shorthand alias for the CLI.

---

### Configure Your Deployment

Edit the `pcc-deploy.toml` file and update the `image` field with your Docker Hub username:

```toml
agent_name = "pcc-gemini-whatsapp"
image = "YOUR_DOCKERHUB_USERNAME/pcc-gemini-whatsapp:0.1" # 👈 Update this line
secret_set = "whatsapp-secrets"

[scaling]
    min_agents = 1
```

#### TOML Settings Explained

| Field | Description |
|-------|--------------|
| `agent_name` | The bot’s name in Pipecat Cloud |
| `image` | Your Docker image (`username/image:version`) |
| `secret_set` | Name of your environment variable set in Pipecat Cloud |
| `min_agents` | Number of bot instances to keep ready (1 = instant start) |

> 🔐 Optional: [Configure `image_credentials`](https://docs.pipecat.ai/deployment/pipecat-cloud/fundamentals/secrets#image-pull-secrets) for private image pulls.

---

### Upload Secrets

Upload your `.env` file securely to Pipecat Cloud:

```bash
uv run pcc secrets set whatsapp-secrets --file .env
```

This creates a secret set named `whatsapp-secrets` and uploads your API keys, matching your TOML configuration.

---

### Build and Deploy

Build and push your Docker image:

```bash
uv run pcc docker build-push
```

Deploy to Pipecat Cloud:

```bash
uv run pcc deploy
```

> For more details, see the [Pipecat Quickstart Guide](https://docs.pipecat.ai/getting-started/quickstart#step-2%3A-deploy-to-production).

---

## Configure WhatsApp Webhook for Production

Before you can receive WhatsApp voice calls in production, you must **set up your webhook** in your WhatsApp Business account.  

Follow the official Pipecat documentation for step-by-step instructions:  
👉 [Configure Webhook — Pipecat WhatsApp Guide](https://docs.pipecat.ai/guides/features/whatsapp#2-configure-webhook)

When configuring for production, use the following format for your webhook URL:
```
https://api.pipecat.daily.co/v1/public/webhooks/$ORGANIZATION_NAME/$AGENT_NAME/whatsapp
```

> ✅ **Tip:**  
> - Replace `$ORGANIZATION_NAME` and `$AGENT_NAME` with the values from your Pipecat Cloud deployment.  
> - Ensure the URL ends with `/whatsapp` — this path is required for correct webhook routing.

---

## Call Your WhatsApp Bot

Once deployed, simply call your registered **WhatsApp Business number** from the WhatsApp app.  
Your Pipecat bot will automatically answer and start the conversation.

---

## What’s Next?

- **🧠 Customize your bot:** Modify `bot.py` to adjust the bot’s personality, responses, or integrations.  
- **📚 Learn more:** Explore [Pipecat’s documentation](https://docs.pipecat.ai/) for advanced features.  
- **💬 Join the community:** Get support and share your work on [Pipecat’s Discord](https://discord.gg/pipecat).  
