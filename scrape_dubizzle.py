import requests
from bs4 import BeautifulSoup
import pandas as pd
import random
import time
import re  # To parse lat, lng from Mapbox URL

# Define a list of different User-Agents to rotate between
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

# Function to make a request with random headers and retry on failure
def make_request(url, timeout=30):  # Increased timeout to 30 seconds
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    retries = 3  # Number of retry attempts
    backoff_factor = 2  # Factor to increase wait time between retries

    for attempt in range(retries):
        try:
            print(f"🟢 Requesting page: {url} (Attempt {attempt + 1})")
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.Timeout:
            print(f"⚠️ Request failed: Timeout after {timeout} seconds. Retrying after a short delay...")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed: {e}. Retrying after a short delay...")

        # Progressive delay with backoff to give server some time
        sleep_time = backoff_factor ** attempt
        time.sleep(random.uniform(sleep_time + 5, sleep_time + 10))  # Longer delay

    print(f"❌ Failed to retrieve {url} after {retries} attempts.")
    return None

# Function to scrape details from the property page
def scrape_property_details(property_url):
    print(f"🔗 Visiting property detail page: {property_url}")
    response = make_request(property_url)
    
    if response is None:
        print(f"❌ Failed to retrieve details for {property_url}")
        return {}

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract relevant details
    details = {}

    # Extract Floor/Level information
    floor = soup.find("span", {"aria-label": "Floor/Level"})
    details['floor'] = floor.text.strip() if floor else None

    # Extract Amenities (usually in list form, e.g., pool, internet, etc.)
    amenities_section = soup.find("div", {"aria-label": "Amenities"})
    amenities = []
    if amenities_section:
        for amenity in amenities_section.find_all("span"):
            amenities.append(amenity.text.strip())
    details['amenities'] = amenities

    # Extract Ad ID
    ad_id = soup.find("span", {"aria-label": "Ad ID"})
    details['ad_id'] = ad_id.text.strip() if ad_id else None

    # Extract Location (Latitude, Longitude from Mapbox URL)
    # Simulate 'See Location' by parsing the Mapbox URL directly
    map_section = soup.find("div", {"aria-label": "Dialog"})
    lat_lng = None
    if map_section:
        map_img = map_section.find("img", {"src": re.compile(r"api\.mapbox\.com")})
        if map_img:
            map_url = map_img["src"]
            # Parse lat and lng from the Mapbox URL
            match = re.search(r"static/([-0-9.]+),([-0-9.]+),", map_url)
            if match:
                lat_lng = (match.group(1), match.group(2))  # lat, lng as a tuple
    details['latitude'] = lat_lng[0] if lat_lng else None
    details['longitude'] = lat_lng[1] if lat_lng else None

    print(f"🗺️ Extracted details: Floor - {details['floor']}, Amenities - {details['amenities']}, Ad ID - {details['ad_id']}, Latitude - {details['latitude']}, Longitude - {details['longitude']}")
    
    # Random delay to avoid being blocked
    time.sleep(random.uniform(2, 5))

    return details

# Function to scrape Dubizzle for property links and details
def scrape_dubizzle():
    url = "https://www.dubizzle.com.eg/en/properties/apartments-duplex-for-rent/shorouk-city/"
    
    print(f"🔍 Starting to scrape the main listing page: {url}")
    response = make_request(url)
    
    if response is None:
        print("❌ Aborting scraping. Unable to fetch the main listing page.")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    properties = []
    
    # Find all <li> elements with aria-class="Listing" & class="undefined"
    listings = soup.find_all("li", {"class": "undefined", "aria-label": "Listing"})

    print(f"🏠 Found {len(listings)} property listings. Extracting URLs and basic details...")
    
    for idx, listing in enumerate(listings, 1):
        try:
            # Get the property details URL
            detail_url = listing.find("a", href=True)["href"]
            full_url = f"https://www.dubizzle.com.eg{detail_url}"

            print(f"🔗 Checking listing {idx}/{len(listings)}: {full_url}")

            # Extract relevant information based on aria-class
            price_section = listing.find("div", {"aria-label": "Price"})
            price = price_section.find_all("span")[0].text.strip() if price_section else None
            price_period = price_section.find_all("span")[1].text.strip() if price_section else None

            subtitle_section = listing.find("div", {"aria-label": "Subtitle"})

            beds = subtitle_section.find("span", {"aria-label": "Beds"}).text.strip() if subtitle_section and subtitle_section.find("span", {"aria-label": "Beds"}) else None
            bathrooms = subtitle_section.find("span", {"aria-label": "Bathrooms"}).text.strip() if subtitle_section and subtitle_section.find("span", {"aria-label": "Bathrooms"}) else None
            area = subtitle_section.find("span", {"aria-label": "Area"}).text.strip() if subtitle_section and subtitle_section.find("span", {"aria-label": "Area"}) else None

            location = listing.find("span", {"aria-label": "Location"}).text.strip() if listing.find("span", {"aria-label": "Location"}) else None
            creation_date = listing.find("span", {"aria-label": "Creation date"}).text.strip() if listing.find("span", {"aria-label": "Creation date"}) else None
            
            # Structure the property details
            property_details = {
                "url": full_url,
                "price": price,
                "price_period": price_period,
                "beds": beds,
                "bathrooms": bathrooms,
                "area": area,
                "location": location,
                "creation_date": creation_date
            }
            
            # Print without URL
            print(f"""
                  [{idx}/{len(listings)}] 
                  🏡 Extracted: 
                  Price: {price} {price_period}
                  Beds: {beds}
                  Bathrooms: {bathrooms}
                  Area: {area}
                  Location: {location}
                  Creation Date: {creation_date}
                  Floor: {property_details['floor']}
                  Amenities: {property_details['amenities']}
                  Ad ID: {property_details['ad_id']}
                  Latitude: {property_details['latitude']}
                  Longitude: {property_details['longitude']}
                  """)
            properties.append(property_details)

            # Random delay to mimic human behavior
            time.sleep(random.uniform(5, 15))  # Increase delay to 5-15 seconds
            
        except Exception as e:
            print(f"⚠️ Error while processing listing {idx}: {e}")
    
    return properties

# Scrape Dubizzle properties
properties = scrape_dubizzle()


for idx, property in enumerate(properties, 1):
    print(f"🔍 Scraping details for property {idx}/{len(properties)}")
    details = scrape_property_details(property["url"])
    print(f"🔍 Scraped details: {details}")
    properties[idx-1].update(details)

# For each property, visit the details page to collect further information
# Save the scraped data into a CSV file
df = pd.DataFrame(properties)
df.to_csv("dubizzle_properties.csv", index=False)

print("✅ Scraping completed and data saved to dubizzle_properties.csv")
