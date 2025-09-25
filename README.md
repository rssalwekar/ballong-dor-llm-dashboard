# LLM Player Collector & Uploader

This project scrapes player data from a target website, processes it through an LLM for structured parsing, and uploads the results to a Supabase database.  
It can be run locally for testing or deployed to [Modal](https://modal.com) for automated execution.

## 🚀 Deployed App
Live on Modal: **[Ballon d'Or 2025](https://rsalweka--ballon-dor-2025-run.modal.run/)**  

## ⚙️ Setup & Local Run
1. Clone this repository:
   ```bash
   git clone https://github.com/rssalwekar/ballon-dor-llm-dashboard.git
   cd ballon-dor-llm-dashboard

2. Install dependencies using uv:
    ```bash
    uv sync

3. Add environment variables (in a .env file):
    ```bash
    OPENAI_API_KEY=your_openai_api_key
    SUPABASE_URL=your_supabase_url
    SUPABASE_KEY=your_supabase_service_role_key

4. Run the collector & uploader locally:
    ```bash
    uv run collector_uploader.py

5. View debug logs to confirm scraped data, LLM output, and Supabase upload success.

## ☁️ Deployment on Modal
1. Make sure you have Modal installed and logged in.
   
2. Deploy:
    ```bash
    modal deploy modal_deploy.py

3. Your app will be accessible at the Modal URL printed after deployment.

## 📌 Features
- Scrapes raw player data from a website.
- Uses an LLM to clean & structure scraped data into JSON.
- Uploads parsed data directly into a Supabase table.
- Can be run locally or deployed on Modal for automation.
