import requests
from bs4 import BeautifulSoup

def truncate_scraped_content(content):
    temp=content.split('More About This Property')
    return temp[0]

# URL of the property page
url = "https://housing.com/in/buy/resale/page/16152635"

# Headers to mimic a real browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

# Fetch the webpage
response = requests.get(url, headers=headers,verify=False)

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
            #print(about_section.get_text(strip=True))
        else:
            print("Could not find the property details after the header.")
    else:
        print("Could not find the 'About this Property' section. The page may use JavaScript to load content.")

else:
    print(f"Failed to fetch page. Status code: {response.status_code}")


content = '''About this property

2.5 Acres of Prime Land with 15 Villas Discover a stunning gated community with 15 beautifully designed villas, surrounded by a welcoming neighborhood where all residents are from the USA. Located near Hope Farm. Exclusive gated community offering safety and privacy. Conveniently close to a supermarket for all your daily needs. Modern amenities available within the community. Perfect for those seeking a peaceful and luxurious lifestyle.

More About This Property

One of the finest property in Marathahalli is now available for sale. This is a 4 BHK Villa. Make it yours now. The price of this Villa is Rs 5.5 Cr. Other charges when you move into this property include maintenance, which is Rs 0. This Villa is spacious with a built-up area of 5000 square_feet. A separate servant room available in this Villa. It is a East-facing property with a good view. There are 4 bedrooms and 4 bathroom. This is a gated community. This property is equipped with cctv facility. Health enthusiasts will enjoy the host of special facilities, such as provision for sports facility. Other facilities include Gym, Garden, Sports facility, Swimming pool, Intercom, Clubhouse, Community hall. This property also enjoys power backup facility. This project has regular water supply. Kids area is also present. It is also close to good and reputed hospitals like Jeevika Hospital, Saai Eye Hospital and Eye Plasty Center, Kauvery Hospital Marathahalli Bengaluru. The brokerage amount to be paid is Rs 0'''
print(truncate_scraped_content(content))