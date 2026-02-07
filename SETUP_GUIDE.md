# AWS Cost Monitoring System - Setup Guide

This guide provides detailed step-by-step instructions for setting up the AWS Cost Monitoring System with MCP Protocol.

## Prerequisites

- Python 3.8 or higher
- AWS Account with Cost Explorer enabled
- API key for at least one LLM provider (OpenAI, Anthropic, or Ollama)
- Git (optional, for cloning the repository)

## Step 1: AWS Account Configuration

### 1.1 Enable AWS Cost Explorer

1. Log in to the AWS Management Console
2. Navigate to **AWS Cost Management** → **Cost Explorer**
3. Click **Enable Cost Explorer** if not already enabled
4. Wait 24 hours for initial data to populate

### 1.2 Create IAM User for Cost Access

1. Navigate to **IAM** → **Users** → **Add users**
2. Enter username (e.g., `cost-monitoring-user`)
3. Select **Programmatic access**
4. Click **Next: Permissions**

### 1.3 Attach IAM Policy

Create a custom policy with the following JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "CostExplorerAccess",
      "Effect": "Allow",
      "Action": [
        "ce:GetCostAndUsage",
        "ce:GetCostForecast",
        "ce:GetAnomalies",
        "ce:GetRightsizingRecommendation",
        "ce:GetSavingsPlansPurchaseRecommendation",
        "ce:GetReservationPurchaseRecommendation",
        "ce:GetDimensionValues",
        "ce:GetTags"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CostOptimizationHubAccess",
      "Effect": "Allow",
      "Action": [
        "cost-optimization-hub:ListRecommendations",
        "cost-optimization-hub:GetRecommendation"
      ],
      "Resource": "*"
    }
  ]
}
```

Steps:
1. Go to **IAM** → **Policies** → **Create policy**
2. Click **JSON** tab
3. Paste the policy above
4. Click **Next: Tags** → **Next: Review**
5. Name it `CostMonitoringPolicy`
6. Click **Create policy**
7. Attach this policy to your IAM user

### 1.4 Generate Access Keys

1. Go to the IAM user you created
2. Click **Security credentials** tab
3. Click **Create access key**
4. Select **Application running outside AWS**
5. Click **Next** → **Create access key**
6. **Save the Access Key ID and Secret Access Key** (you won't see them again!)

## Step 2: Python Environment Setup

### 2.1 Create Virtual Environment

```bash
# Navigate to project directory
cd sre-project-3

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 2.2 Install Dependencies

```bash
pip install -r requirements.txt
```

### 2.3 Verify Installation

```bash
python -c "import boto3, openai, anthropic, mcp, rich; print('All dependencies installed successfully!')"
```

## Step 3: LLM Provider Setup

Choose at least one LLM provider:

### Option A: OpenAI (Recommended for beginners)

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to **API keys**
4. Click **Create new secret key**
5. Copy the API key (starts with `sk-`)

### Option B: Anthropic Claude

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the API key

### Option C: Ollama (Local, Free)

1. Install Ollama:
   - **Windows**: Download from [ollama.ai](https://ollama.ai/)
   - **macOS**: `brew install ollama`
   - **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`

2. Pull the Qwen model:
   ```bash
   ollama pull qwen2.5:latest
   ```

3. Start Ollama server:
   ```bash
   ollama serve
   ```

## Step 4: Environment Configuration

### 4.1 Create .env File

```bash
cp .env.example .env
```

### 4.2 Edit .env File

Open `.env` in a text editor and fill in your credentials:

```env
# AWS Credentials (from Step 1.4)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1

# LLM API Keys (from Step 3)
# Choose one or more:

# Option A: OpenAI
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
DEFAULT_LLM_PROVIDER=openai

# Option B: Anthropic
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
# DEFAULT_LLM_PROVIDER=anthropic

# Option C: Ollama (local)
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=qwen2.5:latest
# DEFAULT_LLM_PROVIDER=ollama

# MCP Server Configuration
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8080

# Logging
LOG_LEVEL=INFO
```

### 4.3 Validate Configuration

```bash
python -c "from config import Config; Config.validate(); print('Configuration valid!')"
```

## Step 5: MCP Server Deployment

### 5.1 Start the MCP Server

```bash
python aws_cost_mcp_server.py
```

You should see:
```
INFO - Starting AWS Cost MCP Server on localhost:8080
 * Running on http://localhost:8080
```

### 5.2 Verify Server Health

In a new terminal:

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{"status": "healthy"}
```

### 5.3 Verify Tools Registration

```bash
curl http://localhost:8080/tools
```

You should see 5 tools listed.

## Step 6: Agent Configuration

### 6.1 Test Agent Connection

In a new terminal (keep MCP server running):

```bash
python agent_orchestrator.py "What is my AWS region?"
```

### 6.2 Run Example Queries

```bash
# Basic cost query
python agent_orchestrator.py "What were my AWS costs last month?"

# Service breakdown
python agent_orchestrator.py "Which AWS services cost the most?"

# Forecast
python agent_orchestrator.py "What will my costs be next month?"
```

## Step 7: Verification

### 7.1 Run Test Suite

```bash
pytest tests/ -v
```

All tests should pass.

### 7.2 Run Example Usage Script

```bash
python example_usage.py
```

This will run through all example scenarios.

### 7.3 Verify Cost Data

```bash
python agent_orchestrator.py "Show me my total AWS costs for the last 7 days"
```

Compare the results with your AWS Cost Explorer console to verify accuracy.

## Step 8: Production Deployment (Optional)

### 8.1 Run MCP Server as a Service

**On Linux (systemd):**

Create `/etc/systemd/system/aws-cost-mcp.service`:

```ini
[Unit]
Description=AWS Cost MCP Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/sre-project-3
Environment="PATH=/path/to/sre-project-3/venv/bin"
ExecStart=/path/to/sre-project-3/venv/bin/python aws_cost_mcp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable aws-cost-mcp
sudo systemctl start aws-cost-mcp
```

**On Windows (NSSM):**

1. Download [NSSM](https://nssm.cc/download)
2. Install service:
   ```cmd
   nssm install AWSCostMCP "C:\path\to\venv\Scripts\python.exe" "C:\path\to\aws_cost_mcp_server.py"
   nssm start AWSCostMCP
   ```

### 8.2 Configure Firewall

If running on a server, configure firewall to allow port 8080:

```bash
# Linux (ufw)
sudo ufw allow 8080/tcp

# Windows
netsh advfirewall firewall add rule name="AWS Cost MCP" dir=in action=allow protocol=TCP localport=8080
```

### 8.3 Use HTTPS (Recommended for production)

Use a reverse proxy like Nginx or Caddy:

**Nginx configuration:**
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Issue: "AWS credentials are required"

**Solution:** Verify `.env` file has correct AWS credentials and is in the project root.

### Issue: "OpenAI API key is required"

**Solution:** Add your OpenAI API key to `.env` or switch to a different provider.

### Issue: "Connection refused" when starting agent

**Solution:** Ensure MCP server is running on the correct port.

### Issue: "No cost data available"

**Solution:** 
- Wait 24 hours after enabling Cost Explorer
- Verify IAM permissions
- Check that you have actual AWS usage

### Issue: Ollama connection error

**Solution:**
```bash
# Ensure Ollama is running
ollama serve

# Verify model is available
ollama list

# Pull model if needed
ollama pull qwen2.5:latest
```

## Next Steps

1. **Customize queries**: Modify `example_usage.py` for your specific needs
2. **Schedule reports**: Use cron/Task Scheduler to run automated reports
3. **Integrate with dashboards**: Export data to Grafana, Tableau, etc.
4. **Set up alerts**: Create cost anomaly alerts
5. **Extend functionality**: Add more AWS services or custom tools

## Support

For additional help:
- Check the main [README.md](README.md)
- Review AWS Cost Explorer documentation
- Open an issue on GitHub
