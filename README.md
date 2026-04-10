Interview Scheduler AI Agent
============================

An AI-driven automation system that handles interview scheduling end-to-end.
It integrates Gmail, Google Calendar, Telegram, and BigQuery to read interview requests,
check availability, send confirmations, and log metadata for analytics.

------------------------------------------------------------
ARCHITECTURE
------------------------------------------------------------
The Main Orchestrator Agent controls the workflow.

Sub-Agents:
- Gmail Agent: Reads incoming interview request emails
- Calendar Agent: Checks availability and books slots in Google Calendar
- Telegram Agent: Sends confirmations/notifications to candidates or recruiters
- BigQuery Agent: Logs interview metadata for HR analytics

Deployment: Runs on Google Cloud Run with secure credential management
via .env and Google Secret Manager.

------------------------------------------------------------
ARCHITECTURAL DIAGRAM 
------------------------------------------------------------




<img width="1536" height="1024" alt="Copilot_20260409_093620" src="https://github.com/user-attachments/assets/4310217d-a785-45a5-a21b-2110caf460de" />


Flow:
1. Recruiter sends interview request via Gmail
2. Gmail Agent parses the request
3. Calendar Agent checks availability
4. Telegram Agent sends confirmation
5. BigQuery Agent logs metadata for analytics

------------------------------------------------------------
APP UI / WORKFLOW
------------------------------------------------------------

1. Recruiter sends an interview request via Gmail
2. Agent parses the request and extracts candidate details
3. Agent checks Google Calendar for availability
4. Telegram bot sends confirmation to candidate/recruiter
5. Metadata (candidate, company, slot) is logged into BigQuery
6. HR can query BigQuery for insights and reporting

------------------------------------------------------------
SETUP AND DEPLOYMENT
------------------------------------------------------------

Prerequisites:
- Python 3.9+
- Create a new project in Google Cloud Console.
- Cloud shell
- Enable billing for the project
- Google Cloud SDK installed.
- Composio API(authenticated using Composio)
- GitHub account (to fork and clone this repo)
- Gmail API, Google Calendar API, and BigQuery enabled in Composio
- Telegram Bot token and telegram chat ID created via BotFather
  
1. Set your Google Cloud project in Cloud Shell:
   gcloud config set project [PROJECT_ID]

2. Enable required Google Cloud APIs:
   gcloud services enable \
     run.googleapis.com \
     artifactregistry.googleapis.com \
     cloudbuild.googleapis.com \
     aiplatform.googleapis.com \
     compute.googleapis.com

3. Create the .env file with project variables:
   - Set variables
   PROJECT_ID=$(gcloud config get-value project)
   PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
   SA_NAME=lab2-cr-service

   - Generate .env file
   cat <<EOF > .env
   PROJECT_ID=$PROJECT_ID
   PROJECT_NUMBER=$PROJECT_NUMBER
   SA_NAME=$SA_NAME
   SERVICE_ACCOUNT=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com
   MODEL="gemini-2.5-flash"
   EOF

------------------------------------------------------------
LOCAL SETUP
------------------------------------------------------------

1. Clone the repository:
   - git clone https://github.com/<your-username>/interview-scheduler-agent.git
   - cd interview-scheduler-agent

2. Create a virtual environment:
   - python3 -m venv venv
   - source venv/bin/activate

3. Install dependencies:
   - pip install -r requirements.txt

4. Configure Environment Variables
   
   Check created a .env file in the project root:
 
  - TELEGRAM_BOT_TOKEN=your_telegram_token
  - TELEGRAM_CHAT_ID=your_telegram_chat_number
  - GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
  - PROJECT_ID=your_project_id
  - PROJECT_NUMBER=your_project_number
  - SA_NAME=your_lab_name
  - SERVICE_ACCOUNT=your_serviceaccount_id
  - MODEL="gemini-2.0-flash"
  - COMPOSIO_API_KEY=your_compsio_api_id
  - COMPOSIO_USER_ID=your_compsio_user_api_id
  - BIGQUERY_DATASET=interview_dataset
  - BIGQUERY_TABLE=interviews

5. Install ADK:
   pip install google-adk

6. Verify ADK installation:
   adk --help

------------------------------------------------------------
RUN THE AGENT LOCALLY
------------------------------------------------------------
If everything is configured correctly, the agent will start and begin processing interview scheduling tasks.

Navigate to your project directory and run:
   adk run interview_scheduler/
   
- After executing the command:
- The terminal will display a prompt for the user.
- At the prompt, type commands such as check email to begin processing.
- The agent will then open and provide a UI link for verification.
- You will be asked to authenticate; complete the authentication process successfully.
- If there are unread interview scheduling emails, the agent will automatically send a Telegram bot message.
- Once you confirm the request within the required time limit, the agent will:
   - Schedule the meeting
   - Update the Google Calendar with the confirmed slot

7. Deploying to Cloud Run:
   gcloud Run the Google ADK deployment for Cloud Run to build, package,
   and deploy the Interview Scheduler agent; once completed, a service URL will be provided for accessing the deployed application.

------------------------------------------------------------
TEST AT THE UI
------------------------------------------------------------

1. Send a test interview request email to your Gmail
2. Agent parses the request and checks Google Calendar
3. Telegram bot sends confirmation
4. BigQuery logs metadata
5. Query BigQuery to verify logs:
   SELECT * FROM interview_logs LIMIT 10;

------------------------------------------------------------
DISCLAIMER
------------------------------------------------------------

- This project is intended for demo and educational purposes only. Please monitor your Google Cloud billing account carefully, 
  As the application uses Google APIs and services, which may incur charges. 
  Ensure you understand your credit limits and billing policies before deploying or running the agent in production
- Composio integration may also incur billing charges. Please review Composio’s official instructions and pricing details before deploying.
- Do not commit or expose API keys, credentials, or .env files
- Use Google Secret Manager or environment variables for production deployments
- Ensure compliance with your organization’s data privacy and security policies

------------------------------------------------------------
QUICK FORK & RUN
------------------------------------------------------------

1. Fork this repository
2. Clone it locally
3. Add your .env and credentials (not included in repo)
4. Run "adk run interview_scheduler/" to start the agent
5. Deploy to Cloud Run for production use

## License
This project is licensed under the **MIT License** – you are free to use, modify, and distribute it in accordance with the terms of the license.

## Author
Created and maintained by **Supriya Kamatagi**
