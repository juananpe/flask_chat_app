# Flask Chat App with LangGraph Agent and Feedback

A simple Flask web application that demonstrates:
- **LangGraph ReAct Agent**: A chat agent with access to tools (time, calculator, weather)
- **LangSmith Feedback**: User feedback collection using presigned feedback URLs
- **Thumb Up/Down UI**: Simple feedback mechanism without exposing API keys to the client

## Features

- 🤖 Chat with a LangGraph-powered AI agent
- 🛠️ Agent has access to tools: current time, calculator, weather (mock)
- 👍👎 Rate each response with thumbs up/down
- 🔒 Feedback uses presigned URLs (no API keys exposed to frontend)
- 📊 All interactions and feedback are logged to LangSmith

## How Presigned Feedback URLs Work

The key feature of this app is the use of `create_presigned_feedback_token` from LangSmith:

1. **Before the agent runs**, we generate a unique `run_id` using `uuid.uuid4()`
2. **Create presigned tokens** for feedback using this run_id (before the run exists!)
3. **Run the agent** with the pre-generated run_id
4. **Send feedback URLs** to the frontend along with the response
5. **Client submits feedback** by simply making a GET request to the presigned URL

This approach is secure because:
- No API keys are exposed to the client
- Feedback URLs are scoped to a specific run and feedback key
- URLs can be time-limited (optional)

## Setup

1. **Clone or copy the files**

2. **Install dependencies**:
   ```bash
   cd flask_chat_app
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the app**:
   ```bash
   python app.py
   ```

5. **Open in browser**: http://localhost:5000

## Code Structure

```
flask_chat_app/
├── app.py              # Main Flask application with LangGraph agent
├── templates/
│   └── index.html      # Chat UI with feedback buttons
├── requirements.txt    # Python dependencies
├── .env.example        # Example environment variables
└── README.md           # This file
```

## Key Code Snippets

### Creating Presigned Feedback URLs

```python
from langsmith import Client
import uuid

client = Client()

# Pre-generate run ID
run_id = uuid.uuid4()

# Create presigned feedback token BEFORE the run
thumbs_up_token = client.create_presigned_feedback_token(
    run_id,
    "user_feedback",
    feedback_config={
        "type": "continuous",
        "min": 0,
        "max": 1
    }
)

# Build URL with score
thumbs_up_url = f"{thumbs_up_token.url}?score=1&comment=thumbs_up"

# Run the agent with the pre-generated run_id
result = agent.invoke(
    {"messages": [{"role": "user", "content": message}]},
    config={"run_id": run_id}
)
```

### Frontend Feedback Submission

```javascript
// Simply make a GET request to the presigned URL
await fetch(thumbs_up_url, { method: 'GET' });
```

## LangSmith Dashboard

After using the app, you can view:
- All chat interactions in LangSmith traces
- User feedback scores attached to each run
- Analytics on which responses users liked/disliked

Visit [smith.langchain.com](https://smith.langchain.com) to see your project traces.

## Customization

### Adding More Tools

Edit `app.py` to add more tools:

```python
def my_custom_tool(param: str) -> str:
    """Description of what the tool does."""
    return f"Result: {param}"

tools = [get_current_time, calculate, get_weather, my_custom_tool]
```

### Changing the Model

```python
llm = ChatOpenAI(
    model="gpt-4o",  # or any other OpenAI model
    temperature=0.7,
)
```

### Adding More Feedback Types

You can add more feedback types (e.g., relevance, helpfulness):

```python
relevance_token = client.create_presigned_feedback_token(
    run_id,
    "relevance",  # Different feedback key
    feedback_config={"type": "continuous", "min": 1, "max": 5}
)
```

## License

MIT
