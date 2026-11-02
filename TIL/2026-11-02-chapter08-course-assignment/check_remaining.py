"""Chapter 08 독립 실습 미실행 케이스 검증 스크립트.
실행 전: python -m uvicorn chapter08.courses:app --reload
실행: python TIL/2026-11-02-chapter08-course-assignment/check_remaining.py
주의: 이 스크립트는 이 대화에서 실행하지 않았으며 아래 결과는 미검증임.
"""
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "http://127.0.0.1:8000"

def call(method, path, body):
    data = json.dumps(body).encode("utf-8")
    request = Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=5) as r:
            return r.status, json.load(r)
    except HTTPError as e:
        return e.code, json.loads(e.read())

cases = [
    ("PATCH nonexistent ID", "PATCH", "/courses/999", {"level": 3}, 404),
    ("PUT required title missing", "PUT", "/courses/2", {"level": 3}, 422),
    ("PATCH wrong level type", "PATCH", "/courses/2", {"level": "abc"}, 422),
    ("PATCH level out of range", "PATCH", "/courses/2", {"level": 9}, 422),
    ("PATCH explicit null", "PATCH", "/courses/2", {"level": None}, 422),
    ("PATCH empty fields", "PATCH", "/courses/2", {}, 400),
]
for name, method, path, body, expected in cases:
    status, response = call(method, path, body)
    verdict = "PASS" if status == expected else "FAIL"
    print(f"{verdict}: {name} expected={expected} actual={status}")
    if verdict == "FAIL":
        print(response)
