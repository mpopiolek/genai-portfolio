import requests


class PackageAPI:
    """Integration with package hub API (AIDEVS_API_URL + /api/packages)."""

    def __init__(self, api_key, api_url):
        self.api_key = api_key
        self.api_url = api_url.rstrip("/")

    def check_package(self, package_id):
        payload = {
            "apikey": self.api_key,
            "action": "check",
            "packageid": package_id,
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            return {"error": str(exc), "message": "Cannot reach package API"}

    def redirect_package(self, package_id, destination, code):
        payload = {
            "apikey": self.api_key,
            "action": "redirect",
            "packageid": package_id,
            "destination": destination,
            "code": code,
        }
        try:
            response = requests.post(self.api_url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            return {"error": str(exc), "message": "Package redirect failed"}
