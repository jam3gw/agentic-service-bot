# Agentic Service Bot

A smart home assistant service bot that handles customer interactions using AI. The bot processes customer requests, manages device operations, and provides responses based on the customer's service level permissions.

## Features

- Natural language processing of customer requests
- Service level-based permission system
- Smart home device management
- Conversation history tracking
- Intelligent request analysis and response generation
- Support for device relocation requests

## Prerequisites

- Python 3.8 or higher
- An Anthropic API key (for Claude LLM integration)

## Project Structure

```
agentic-service-bot/
├── agents/
│   ├── __init__.py
│   └── service_agent.py
├── models/
│   ├── __init__.py
│   ├── customer.py
│   └── request.py
├── utils/
│   ├── __init__.py
│   └── llm_client.py
├── data/
├── config.py
├── main.py
└── requirements.txt
```

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic-service-bot
```

2. Create and activate a virtual environment:
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your Anthropic API key
# Replace 'your-api-key-here' with your actual API key
```

Your `.env` file should look like this:
```
ANTHROPIC_API_KEY=your-api-key-here
ANTHROPIC_MODEL=claude-3-opus-20240229
```

## Running the Program

1. Make sure your virtual environment is activated:
```bash
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

2. Run the main program:
```bash
python main.py
```

3. Interact with the bot by typing your requests. Example requests:
- "Move my smart thermostat to the bedroom"
- "Check the status of my devices"
- Type "exit" or "quit" to end the session

## Debug Mode

The program includes a debug mode that can be enabled in `config.py`. When enabled:
- Type "debug" during the session to see conversation summary
- Additional debugging information will be displayed
- Stack traces will be shown for errors

## Development

The project uses a modular structure:
- `agents/`: Contains the core service agent logic
- `models/`: Contains data models and database interfaces
- `utils/`: Contains utility functions and LLM client
- `data/`: Stores customer and service configuration data

## Error Handling

The program includes robust error handling for:
- Invalid customer IDs
- Unauthorized actions
- API failures
- Invalid request types

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here] 