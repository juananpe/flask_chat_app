# -*- coding: utf-8 -*-
"""
Flask Chat App with LangGraph Agent and Feedback System

This app demonstrates:
- A basic LangGraph ReAct agent for chat
- Thumb up/down feedback collection, sent to LangSmith through /feedback
"""

import os
import uuid
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langsmith import Client, traceable

# Load environment variables
load_dotenv()

# Verify required environment variables
required_vars = ['OPENROUTER_API_KEY', 'LANGSMITH_API_KEY']
for var in required_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

# Set up LangSmith tracing
os.environ['LANGSMITH_TRACING'] = "true"
os.environ['LANGSMITH_PROJECT'] = os.getenv(
    'LANGSMITH_PROJECT', 'flask-chat-feedback')

# Initialize Flask app
app = Flask(__name__)

# Initialize LangSmith client for feedback
langsmith_client = Client()

# Get the project info to build correct URLs
PROJECT_NAME = os.environ['LANGSMITH_PROJECT']
try:
    _project = langsmith_client.read_project(project_name=PROJECT_NAME)
    # Use EU dashboard URL if LANGCHAIN_ENDPOINT points to EU region
    endpoint = os.getenv('LANGCHAIN_ENDPOINT',
                         'https://api.smith.langchain.com')
    if 'eu.api' in endpoint:
        dashboard_base = 'https://eu.smith.langchain.com'
    else:
        dashboard_base = 'https://smith.langchain.com'
    LANGSMITH_PROJECT_URL = f"{dashboard_base}/o/{_project.tenant_id}/projects/p/{_project.id}"
    LANGSMITH_PROJECT_ID = _project.id
    print(f"📊 LangSmith project URL: {LANGSMITH_PROJECT_URL}")
except Exception as e:
    LANGSMITH_PROJECT_URL = None
    LANGSMITH_PROJECT_ID = None
    print(f"⚠️  Could not fetch LangSmith project info: {e}")

# Initialize the LLM (OpenRouter exposes an OpenAI-compatible API)
llm = ChatOpenAI(
    model=os.getenv('OPENROUTER_MODEL', 'openai/gpt-4.1-mini'),
    api_key=os.environ['OPENROUTER_API_KEY'],
    base_url='https://openrouter.ai/api/v1',
)

# Define some simple tools for the agent


def get_current_time() -> str:
    """Get the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculate(expression: str) -> str:
    """
    Evaluate a mathematical expression.

    Args:
        expression: A mathematical expression like "2 + 2" or "10 * 5"
    """
    try:
        # Only allow safe mathematical operations
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Only basic math operations are allowed"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating: {str(e)}"


def get_weather(location: str) -> str:
    """
    Get weather information for a location (mock implementation).

    Args:
        location: The city or location to get weather for
    """
    # This is a mock implementation - in production you'd use a real weather API
    import random
    conditions = ["sunny", "cloudy", "rainy", "partly cloudy", "windy"]
    temp = random.randint(50, 85)
    condition = random.choice(conditions)
    return f"Weather in {location}: {temp}°F, {condition}"


# Create the ReAct agent with tools
tools = [get_current_time, calculate, get_weather]
agent = create_agent(
    llm,
    tools=tools,
    system_prompt="You are a helpful assistant. You have access to tools for getting the current time, performing calculations, and checking weather. Be friendly and concise in your responses."
)


@traceable(name="chat_with_agent")
def chat_with_agent(user_message: str, run_id: uuid.UUID) -> str:
    """
    Process a user message with the LangGraph agent.

    Args:
        user_message: The user's input message
        run_id: Pre-generated run ID for feedback tracking

    Returns:
        The agent's response text
    """
    result = agent.invoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config={"run_id": run_id}
    )

    # Get the last message (the agent's response)
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        return last_message.content
    return "Sorry, I couldn't generate a response."


@app.route('/')
def index():
    """Render the main chat interface."""
    return render_template('index.html')


@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat messages and return the response with its run_id.

    The run_id is generated up front so the client can later attach
    feedback to this run through the /feedback endpoint.
    """
    data = request.json
    user_message = data.get('message', '')

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    try:
        # Pre-generate the run ID
        run_id = uuid.uuid4()

        print(f"\n{'='*60}")
        print(f"📨 New chat request")
        print(
            f"   User message: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        print(f"   Run ID: {run_id}")
        if LANGSMITH_PROJECT_URL:
            print(f"   LangSmith: {LANGSMITH_PROJECT_URL}?peek={run_id}")
        print(f"{'='*60}\n")

        # Invoke the agent with the pre-generated run_id
        response = chat_with_agent(user_message, run_id)

        print(f"✅ Response generated successfully")

        return jsonify({
            'response': response,
            'run_id': str(run_id),
        })

    except Exception as e:
        print(f"❌ Error processing chat: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/feedback', methods=['POST'])
def submit_feedback():
    """
    Record thumbs up/down feedback for a run in LangSmith.

    The LangSmith API key stays on the server; the client only sends
    the run_id and the score.
    """
    data = request.json
    run_id = data.get('run_id')
    score = data.get('score')  # 1 for thumbs up, 0 for thumbs down
    comment = data.get('comment', '')

    if not run_id or score is None:
        return jsonify({'error': 'Missing run_id or score'}), 400

    try:
        print(
            f"👍 Submitting feedback for run: {run_id}, score: {score}")
        langsmith_client.create_feedback(
            run_id,
            key="user_feedback",
            score=float(score),
            comment=comment,
            session_id=LANGSMITH_PROJECT_ID,
        )
        print(f"✅ Feedback submitted successfully!")
        return jsonify({'success': True, 'message': 'Feedback submitted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    print("Starting Flask Chat App with LangGraph Agent...")
    print("Make sure you have set OPENROUTER_API_KEY and LANGSMITH_API_KEY in your .env file")
    app.run(debug=True, port=5000)
