import requests
from bs4 import BeautifulSoup

# URL of the property page
url = "https://housing.com/in/buy/resale/page/16152635"

# Headers to mimic a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Fetch the webpage
response = requests.get(url, headers=headers)

# Check if the request was successful
if response.status_code == 200:
    # Parse HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Find the "About this property" section by text
    about_header = soup.find("div", text="About this property")

    if about_header:
        # The actual content is likely in the next div or sibling
        about_section = about_header.find_next_sibling("div")
        if about_section:
            print("About this Property:")
            print(about_section.get_text(strip=True))
        else:
            print("Could not find the property details after the header.")
    else:
        print("Could not find the 'About this Property' section. The page may use JavaScript to load content.")

else:
    print(f"Failed to fetch page. Status code: {response.status_code}")
