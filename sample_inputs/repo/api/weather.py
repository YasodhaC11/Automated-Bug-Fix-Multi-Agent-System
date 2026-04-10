import requests
from flask import Blueprint, jsonify

weather_bp = Blueprint('weather', __name__)

def get_weather(city: str):
    """Fetch weather from external API."""
    response = requests.get(
        f"https://api.weatherservice.com/weather?city={city}"
    )
    return response.json()

@weather_bp.route('/api/weather', methods=['GET'])
def route_handler():
    try:
        data = get_weather("London")
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
      