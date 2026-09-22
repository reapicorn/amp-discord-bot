import base64
import requests


class AmpClient:
    """AMP API client. Can target the ADS directly or proxy to a child instance."""

    HEADERS = {"Accept": "application/json"}

    def __init__(self, url: str, user: str, password: str, instance_id: str = None):
        base = url.rstrip("/")
        if instance_id:
            self._api_base = f"{base}/API/ADSModule/Servers/{instance_id}/API"
        else:
            self._api_base = f"{base}/API"
        self._login_url = f"{self._api_base}/Core/Login"
        self._user = user
        self._password = password
        self._label = instance_id or url  # used in log messages

    def _login(self) -> str:
        try:
            r = requests.post(self._login_url, json={
                "username": self._user,
                "password": self._password,
                "token": "",
                "rememberMeToken": "",
                "rememberMe": False,
            }, headers=self.HEADERS, timeout=10)
            r.raise_for_status()
            data = r.json()
            if not data.get("success"):
                raise RuntimeError(f"AMP login failed: {data.get('resultReason', 'unknown')}")
            return data["sessionID"]
        except Exception as e:
            print(f"[amp/{self._label}] Login error: {e}")
            raise

    def _get_session(self) -> str:
        return self._login()

    def call(self, endpoint: str, extra: dict = None) -> dict:
        sid = self._get_session()
        payload = {"SESSIONID": sid}
        if extra:
            payload.update(extra)
        try:
            r = requests.post(f"{self._api_base}/{endpoint}", json=payload,
                              headers=self.HEADERS, timeout=10)
            r.raise_for_status()
            return r.json() if r.text else {}
        except Exception as e:
            print(f"[amp/{self._label}] Error calling {endpoint}: {e}")
            raise

    # ------------------------------------------------------------------ #
    #  Instance management                                                 #
    # ------------------------------------------------------------------ #

    def get_status(self) -> dict:
        return self.call("Core/GetStatus")

    def start(self) -> dict:
        print(f"[amp/{self._label}] Starting server...")
        return self.call("Core/Start")

    def stop(self) -> dict:
        print(f"[amp/{self._label}] Stopping server...")
        return self.call("Core/Stop")

    def restart(self) -> dict:
        print(f"[amp/{self._label}] Restarting server...")
        return self.call("Core/Restart")

    def update(self) -> dict:
        print(f"[amp/{self._label}] Updating server...")
        return self.call("Core/UpdateApplication")

    # ------------------------------------------------------------------ #
    #  File Manager                                                        #
    # ------------------------------------------------------------------ #

    def read_file(self, path: str) -> str:
        """
        Read a file from the instance via FileManagerPlugin/ReadFileChunk.
        Content is returned as Base64 in result.Result — decoded and returned as string.
        path: relative to the instance directory (e.g. "Zomboid/Server/servertest.ini")
        """
        result = self.call("FileManagerPlugin/ReadFileChunk", {
            "Filename": path,
            "Offset": 0,
        })
        encoded = result.get("Result") or result.get("result", "")
        if not encoded:
            print(f"[amp/{self._label}] read_file: empty response for '{path}'")
            return ""
        return base64.b64decode(encoded).decode("utf-8", errors="replace")
