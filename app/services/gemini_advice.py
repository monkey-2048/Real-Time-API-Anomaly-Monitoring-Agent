from __future__ import annotations

import httpx

from app.core.config import get_settings

settings = get_settings()


class GeminiAdviceService:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

    async def _fetch_rain_signal(self) -> dict:
        params = {
            "latitude": settings.default_latitude,
            "longitude": settings.default_longitude,
            "current": "rain,showers,precipitation,cloud_cover",
            "timezone": "UTC",
        }
        try:
            async with httpx.AsyncClient(timeout=settings.gemini_timeout_seconds) as client:
                r = await client.get(self.WEATHER_URL, params=params)
                r.raise_for_status()
                current = r.json().get("current", {})
            return {
                "precipitation": current.get("precipitation"),
                "rain": current.get("rain"),
                "showers": current.get("showers"),
                "cloud_cover": current.get("cloud_cover"),
            }
        except Exception:
            return {
                "precipitation": None,
                "rain": None,
                "showers": None,
                "cloud_cover": None,
            }

    @staticmethod
    def _fallback(snapshot: dict, rain_signal: dict) -> str:
        parts: list[str] = []
        temp = snapshot.get("temperature")
        humidity = snapshot.get("humidity")
        pm25 = snapshot.get("pm25")
        aqi = snapshot.get("aqi")

        rain = rain_signal.get("rain") or 0
        showers = rain_signal.get("showers") or 0
        precipitation = rain_signal.get("precipitation") or 0
        cloud_cover = rain_signal.get("cloud_cover") or 0

        if temp is not None:
            if temp >= 30:
                parts.append("Wear light breathable clothes like a thin T-shirt and shorts; bring water.")
            elif temp >= 22:
                parts.append("Wear a light top with a thin outer layer for evening temperature changes.")
            elif temp >= 15:
                parts.append("Wear a long-sleeve top or light jacket for comfort.")
            else:
                parts.append("Wear layered clothing and a warmer jacket.")

        if precipitation > 0 or rain > 0 or showers > 0:
            parts.append("Rain is currently detected. Bring an umbrella or a waterproof jacket.")
        elif cloud_cover >= 75:
            parts.append("Cloud cover is high. Bring a compact umbrella in case rain starts.")

        if pm25 is not None and pm25 >= 35:
            parts.append("PM2.5 is elevated. Consider wearing a mask outdoors and reducing long outdoor stays.")
        elif aqi is not None and aqi >= 100:
            parts.append("Air quality is moderate-risk for sensitive groups. Reduce intense outdoor activity.")

        if humidity is not None and humidity >= 80:
            parts.append("Humidity is high. Choose quick-dry clothes and improve indoor ventilation.")

        if not parts:
            return "Wear normal light daily clothing. Conditions are stable, and no rain signal is currently detected."
        return " ".join(parts)

    @staticmethod
    def _prompt(snapshot: dict, rain_signal: dict) -> str:
        return (
            "You are a practical weather and air-quality assistant. "
            "Return exactly 3 bullet points in English. "
            "Bullet 1: what to wear now. "
            "Bullet 2: rain recommendation (umbrella/raincoat yes or no with reason). "
            "Bullet 3: air quality precaution based on PM2.5/AQI. "
            "Each bullet must be one complete sentence and directly actionable. "
            "Do not include intro or conclusion.\n\n"
            f"Location: {snapshot.get('location')}\n"
            f"Observed at (UTC): {snapshot.get('observed_at')}\n"
            f"Temperature C: {snapshot.get('temperature')}\n"
            f"Humidity %: {snapshot.get('humidity')}\n"
            f"Wind speed m/s: {snapshot.get('wind_speed')}\n"
            f"PM2.5: {snapshot.get('pm25')}\n"
            f"PM10: {snapshot.get('pm10')}\n"
            f"AQI: {snapshot.get('aqi')}\n"
            f"Current precipitation mm: {rain_signal.get('precipitation')}\n"
            f"Current rain mm: {rain_signal.get('rain')}\n"
            f"Current showers mm: {rain_signal.get('showers')}\n"
            f"Current cloud cover %: {rain_signal.get('cloud_cover')}\n"
        )

    async def generate_advice(self, snapshot: dict) -> tuple[str, str]:
        rain_signal = await self._fetch_rain_signal()

        if not settings.gemini_api_key:
            return self._fallback(snapshot, rain_signal), "fallback-rule"

        url = f"{self.BASE_URL}/models/{settings.gemini_model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": self._prompt(snapshot, rain_signal),
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 220,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=settings.gemini_timeout_seconds) as client:
                response = await client.post(
                    url,
                    params={"key": settings.gemini_api_key},
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

            advice = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text")
            )
            if not advice:
                return self._fallback(snapshot, rain_signal), "fallback-rule"
            return advice.strip(), settings.gemini_model
        except Exception:
            return self._fallback(snapshot, rain_signal), "fallback-rule"
