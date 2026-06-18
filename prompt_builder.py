def build_prompt(weather_data, user_question):
    return f"""
You are a smart weather assistant.

Weather Data:
City: {weather_data['city']}
Temperature: {weather_data['temperature']}°C
Condition: {weather_data['condition']}

User Question:
{user_question}

Instructions:
- Answer naturally like a human
- Be helpful and short
- Use the weather data to guide your answer
"""