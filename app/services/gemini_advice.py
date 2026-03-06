from __future__ import annotations

import json

import httpx

from app.core.config import get_settings

settings = get_settings()


class GeminiAdviceService:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    @staticmethod
    def _fallback(snapshot: dict) -> str:
        parts: list[str] = []
        temp = snapshot.get("temperature")
        humidity = snapshot.get("humidity")
        pm25 = snapshot.get("pm25")
        aqi = snapshot.get("aqi")

        if temp is not None:
            if temp >= 32:
                parts.append("Temperature is high, reduce outdoor activity in the afternoon and hydrate more.")
            elif temp <= 10:
                parts.append("Temperature is low, wear layers and keep warm if outdoors.")

        if humidity is not None and humidity >= 80:
            parts.append("Humidity is elevated, improve indoor ventilation to reduce discomfort.")

        if pm25 is not None and pm25 >= 35:
            parts.append("PM2.5 is elevated, consider a mask outdoors and use an air purifier indoors.")
        elif aqi is not None and aqi >= 100:
            parts.append("AQI suggests moderate risk, sensitive groups should limit prolonged outdoor exertion.")

        if not parts:
            return "Conditions look generally stable. Maintain normal outdoor plans and monitor updates every hour."
        return " ".join(parts)

    @staticmethod
    def _prompt(snapshot: dict) -> str:
        return (
            "You are an environmental health assistant. "
            "Given current conditions, provide concise practical advice in 3 short bullet points. "
            "Avoid medical diagnosis and do not mention uncertainty unless data is missing.\n\n"
            f"Location: {snapshot.get('location')}\n"
            f"Observed at (UTC): {snapshot.get('observed_at')}\n"
            f"Temperature C: {snapshot.get('temperature')}\n"
            f"Humidity %: {snapshot.get('humidity')}\n"
            f"Wind speed m/s: {snapshot.get('wind_speed')}\n"
            f"PM2.5: {snapshot.get('pm25')}\n"
            f"PM10: {snapshot.get('pm10')}\n"
            f"AQI: {snapshot.get('aqi')}\n"
        )

    async def generate_advice(self, snapshot: dict) -> tuple[str, str]:
        if not settings.gemini_api_key:
            return self._fallback(snapshot), "fallback-rule"

        url = f"{self.BASE_URL}/models/{settings.gemini_model}:generateContent"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": self._prompt(snapshot),
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 180,
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
                return self._fallback(snapshot), "fallback-rule"
            return advice.strip(), settings.gemini_model
        except Exception:
            return self._fallback(snapshot), "fallback-rule"
