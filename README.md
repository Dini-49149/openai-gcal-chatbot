# openai-gcal-chatbot

# Interactive Chatbot with Google Calendar Integration

This project is an interactive chatbot application built with Flask that integrates with Google Calendar to manage events such as listing, creating, updating, and deleting events. The chatbot uses OpenAI's GPT-3.5-turbo model to handle natural language queries and perform actions on the user's Google Calendar.

## Features

- **List Events**: Retrieve and display upcoming events from your Google Calendar.
- **Create Event**: Add new events to your Google Calendar by providing details such as title, description, time, and attendees.
- **Update Event**: Modify existing events in your Google Calendar.
- **Delete Event**: Remove events from your Google Calendar.

## Project Structure

```
├── templates/
│ └── chat.html # Frontend HTML template for the chatbot interface
├── api_key.json # Contains OpenAI API key (not included in the repository)
├── client_secret.json # Contains Google OAuth credentials (not included in the repository)
├── app.py # Main Flask application code
├── requirements.txt # Python dependencies

```

## Prerequisites

1. **Google API Credentials**: Create OAuth credentials for the Google Calendar API by following the steps below:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project or select an existing one.
   - Navigate to the **APIs & Services** > **Credentials** section.
   - Click on **Create Credentials** and choose **OAuth 2.0 Client IDs**.
   - Configure the consent screen and add scopes as needed (e.g., `https://www.googleapis.com/auth/calendar`).
   - Download the `client_secret.json` file and place it in the project root directory.
   - For more detailed instructions, refer to the [Google Calendar API Python Quickstart](https://developers.google.com/calendar/quickstart/python).
2. **OpenAI API Key**: Sign up on [OpenAI](https://openai.com) and get your API key. Store this key in a `api_key.json` file.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/interactive-chatbot.git
   cd interactive-chatbot
   ```

2. Create a virtual environment and activate it:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

   ```
3. Install the dependencies:
   ```bash
    pip install -r requirements.txt
   ```
4. Place your `client_secret.json` and `api_key.json` in the project root directory.

## Running the Application

1. Run the Flask application:
  ```bash
    python app.py
   ```
2. Open your browser and navigate to `http://localhost:5000` to interact with the chatbot.

## Google Calendar Authentication

When accessing Google Calendar features for the first time, you'll be redirected to authenticate with your Google account. Once authenticated, a token will be stored locally to manage subsequent requests.

## Future Enhancements

- **Improve User Interface**: Enhance the overall user experience with a more intuitive and interactive design.
- **Support Multiple Calendar Integrations**: Expand the application to support integration with multiple calendars and accounts.
- **Extend Chatbot Functionality**: Add more advanced features to the chatbot to handle a wider variety of complex queries.

## Contributing

If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are warmly welcome.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.








   

