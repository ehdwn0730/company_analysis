import re
import requests

url = "https://www.wanted.co.kr/wd/361660"
r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
r.encoding = "utf-8"
text = r.text
for needle in ["main_tasks", "requirements", "preferred", "주요업무", "자격요건", "우대사항"]:
    print("NEEDLE", needle, text.find(needle))
    for match in re.finditer(needle, text):
        start = max(0, match.start() - 500)
        end = min(len(text), match.end() + 1200)
        print(text[start:end].encode("unicode_escape").decode())
        break
