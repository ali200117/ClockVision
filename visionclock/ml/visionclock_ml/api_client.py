import requests

from . import config

TIMEOUT_SECONDS = 5


class BackendError(RuntimeError):
    pass


def _request(method: str, path: str) -> dict:
    url = f"{config.BACKEND_URL}{path}"
    try:
        response = requests.request(method, url, timeout=TIMEOUT_SECONDS)
    except requests.RequestException as error:
        raise BackendError(f"Fikk ikke kontakt med backend på {config.BACKEND_URL}: {error}") from error

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise BackendError(f"{response.status_code} fra backend: {detail}")
    return response.json()


def get_employee(employee_id: int) -> dict:
    return _request("GET", f"/api/employees/{employee_id}")


def clock(employee_id: int) -> dict:
    """Stempler inn eller ut. Backend bestemmer hvilken."""
    return _request("POST", f"/api/employees/{employee_id}/clock")
