# CSV/Google Sheets DataFrame Query Agent (Project 9)

## Goal

Query CSV files or Google Sheets using natural language via a LangChain Pandas DataFrame agent backed by an LLM.

## API

- Endpoint: POST /api/dataframe/query
- Endpoint: POST /api/dataframe/upload-csv
- Auth: same Bearer token flow as other API routes

Query request body:

```json
{
  "question": "What is the average sales amount?",
  "use_google_sheets": true,
  "csv_file_id": null
}
```

Query response body:

```json
{
  "question": "What is the average sales amount?",
  "answer": "The average sales amount is $5,234.50",
  "data_summary": "Loaded 150 rows × 8 columns",
  "source": "google_sheets",
  "row_count": 150,
  "column_names": ["date", "customer", "amount", ...],
  "generated_at": "2026-05-15T00:00:00Z"
}
```

## How It Works

1. User selects Google Sheets or uploads a CSV file
2. Frontend sends natural language question
3. Backend loads data into Pandas DataFrame via:
   - Google Sheets API (if using Google Sheets)
   - CSV file (if uploaded)
4. LangChain Pandas agent processes the question
5. Agent uses available Pandas tools to analyze data
6. LLM generates natural language answer
7. Response returned with answer and data metadata

## Configuration

- GOOGLE_SHEETS_SPREADSHEET_ID: ID of the Google Sheet to query
- GOOGLE_SERVICE_ACCOUNT_JSON: Service account credentials JSON for Google Sheets API
- CSV_UPLOAD_DIR: Directory to store uploaded CSV files
- DATAFRAME_AGENT_MAX_ITERATIONS: Max iterations for agent execution

## Frontend

The DataFrame Query view is available in the app switcher (green "DataFrame" button).

Two modes:
1. **Google Sheets**: Uses configured GOOGLE_SHEETS_SPREADSHEET_ID
2. **CSV Upload**: Upload a CSV file, then ask questions about it

The LLM agent has access to Pandas operations like filtering, aggregation, sorting, etc.

## Limitations

- Google Sheets: Loads up to 1000 rows and 26 columns
- CSV: Limited by memory and file size
- Agent max iterations prevents infinite loops
- Complex multi-step analysis may require multiple questions
