# Flask Chat App with LangGraph Agent and Feedback

A simple Flask web application that demonstrates:
- **LangGraph ReAct Agent**: A chat agent with access to tools (time, calculator, weather)
- **LangSmith Feedback**: User feedback collection through a server-side `/feedback` endpoint
- **Thumb Up/Down UI**: Simple feedback mechanism without exposing API keys to the client

## Features

- 🤖 Chat with a LangGraph-powered AI agent
- 🛠️ Agent has access to tools: current time, calculator, weather (mock)
- 👍👎 Rate each response with thumbs up/down
- 🔒 Feedback goes through the Flask backend (no API keys exposed to frontend)
- 📊 All interactions and feedback are logged to LangSmith

## How Feedback Works

1. **Before the agent runs**, the server generates a unique `run_id` using `uuid.uuid4()`
2. **Run the agent** with that pre-generated run_id
3. **Return the run_id** to the frontend along with the response
4. **Client submits feedback** with a `POST /feedback` carrying the run_id and the score
5. **Server records it** in LangSmith with `client.create_feedback`

The LangSmith API key never leaves the server: the browser only knows the run_id.

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
   # Edit .env with your OpenRouter and LangSmith API keys
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

### Running the Agent with a Known Run ID

```python
run_id = uuid.uuid4()

result = agent.invoke(
    {"messages": [{"role": "user", "content": message}]},
    config={"run_id": run_id}
)

return jsonify({"response": response, "run_id": str(run_id)})
```

### Recording Feedback on the Server

```python
langsmith_client.create_feedback(
    run_id,
    key="user_feedback",
    score=float(score),       # 1 = thumbs up, 0 = thumbs down
    comment=comment,
    session_id=LANGSMITH_PROJECT_ID,
)
```

### Frontend Feedback Submission

```javascript
await fetch('/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, score: 1, comment: 'thumbs_up' })
});
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

The app talks to models through [OpenRouter](https://openrouter.ai). Set
`OPENROUTER_MODEL` in `.env` to any OpenRouter model slug:

```bash
OPENROUTER_MODEL=openai/gpt-4o  # defaults to openai/gpt-4.1-mini
```

### Adding More Feedback Types

Use a different feedback `key` (e.g., relevance, helpfulness) when calling
`create_feedback`:

```python
langsmith_client.create_feedback(run_id, key="relevance", score=4)
```

## License

MIT
