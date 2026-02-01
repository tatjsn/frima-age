import requests
import os
import argparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from collections import defaultdict

def pipeline(article_id):
    frima_host = os.environ["HOST"]
    frima_pass = os.environ["PASS"]

    # URLs
    url1 = f"{frima_host}/sale/articles/{article_id}"   # Page with the form
    url2 = f"{frima_host}/sale/articles/{article_id}/edit"   # Endpoint to submit

    # Create a session to store cookies automatically
    session = requests.Session()

    # Step 1: GET the form page
    r = session.get(url1)
    r.raise_for_status()

    # Step 2: Parse CSRF token from HTML
    soup = BeautifulSoup(r.text, "html.parser")
    token_input = soup.find("input", {"name": "authenticity_token"})
    if not token_input:
        raise ValueError("authenticity_token not found on the page")
    csrf_token = token_input["value"]

    # Step 3: Prepare POST data
    data = {
        "utf8": "✓",               # optional
        "_method": "patch",         # if endpoint expects PATCH
        "authenticity_token": csrf_token,
        "password": frima_pass,         # your actual form data
        "button": ""            # optional
    }

    # Step 4: POST to url2 with session cookies
    r2 = session.post(url2, data=data)
    r2.raise_for_status()

    # Step 5: Check result
    print("Status code:", r2.status_code)
    # print("Response snippet:", r2.text)

    # Parse the form in r2
    soup2 = BeautifulSoup(r2.text, "html.parser")
    form = soup2.find("form", id="js-article-form")
    if not form:
        print("No form found in response, nothing to submit")
    else:
        # Get form action URL
        action = form.get("action")
        if not action.startswith("http"):
            # Make it absolute if relative
            from urllib.parse import urljoin
            action = urljoin(url2, action)

        # Collect all input fields
        post_data = defaultdict(list)
        for input_tag in form.find_all("input"):
            name = input_tag.get("name")
            value = input_tag.get("value", "")
            if name:
                post_data[name].append(value)

        post_data["password"].append(frima_pass)

        # Submit the form
        r3 = session.post(action, data=post_data)
        r3.raise_for_status()
        print("Step 6: Submitted form from r2, status:", r3.status_code)
        # print("Response snippet:", r3.text)

if __name__ == '__main__':
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("article_id", type=int, help="article id")
    args = parser.parse_args()
    pipeline(args.article_id)
