import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time

# Function to scrape Dubizzle for property links and details
def scrape_dubizzle():
    url = "https://www.dubizzle.com.eg/en/properties/apartments-duplex-for-rent/shorouk-city/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    print(f"🔍 Starting to scrape the main listing page: {url}")
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    properties = []
    
    # Find all <li> elements with aria-class="Listing"
    listings = soup.find_all("li", {"aria-class": "Listing"})
    print(f"🏠 Found {len(listings)} property listings. Extracting URLs and basic details...")
    
    for idx, listing in enumerate(listings, 1):
        try:
            # Get the property details URL
            detail_url = listing.find("a", href=True)["href"]
            full_url = f"https://www.dubizzle.com.eg{detail_url}"

            # Extract relevant information based on aria-class
            price_section = listing.find("div", {"aria-class": "Price"})
            price = price_section.find_all("span")[0].text.strip() if price_section else None
            price_period = price_section.find_all("span")[1].text.strip() if price_section else None

            beds = listing.find("div", {"aria-class": "Beds"}).find("span").text.strip() if listing.find("div", {"aria-class": "Beds"}) else None
            bathrooms = listing.find("div", {"aria-class": "Bathrooms"}).find("span").text.strip() if listing.find("div", {"aria-class": "Bathrooms"}) else None
            area = listing.find("div", {"aria-class": "Area"}).find("span").text.strip() if listing.find("div", {"aria-class": "Area"}) else None
            location = listing.find("div", {"aria-class": "Location"}).find("span").text.strip() if listing.find("div", {"aria-class": "Location"}) else None
            creation_date = listing.find("div", {"aria-class": "Creation Date"}).find("span").text.strip() if listing.find("div", {"aria-class": "Creation Date"}) else None
            
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
            
            print(f"[{idx}/{len(listings)}] 🏡 Extracted: {property_details['price']} - {property_details['price_period']} | Beds: {property_details['beds']}, Baths: {property_details['bathrooms']}, Area: {property_details['area']} sqm, Location: {property_details['location']}, Listed: {property_details['creation_date']}")
            properties.append(property_details)
        except Exception as e:
            print(f"⚠️ Error while processing listing {idx}: {e}")
    
    return properties

# Function to scrape property details from the detailed page
def scrape_property_details(property_url):
    print(f"🔗 Visiting property detail page: {property_url}")
    response = requests.get(property_url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Extract detailed features like latitude, longitude, furnishing, etc.
    # Example of finding furnishing and lat/long from detail pages, this will vary per site.
    details = {
        "Latitude": soup.find("meta", {"property": "place:location:latitude"})["content"] if soup.find("meta", {"property": "place:location:latitude"}) else None,
        "Longitude": soup.find("meta", {"property": "place:location:longitude"})["content"] if soup.find("meta", {"property": "place:location:longitude"}) else None,
        "Furnishing": soup.find("div", class_="furnishing-status").text.strip() if soup.find("div", class_="furnishing-status") else None,
    }

    print(f"🗺️ Extracted details: Latitude - {details['Latitude']}, Longitude - {details['Longitude']}, Furnishing - {details['Furnishing']}")
    
    # To avoid being flagged as a bot, include a short sleep between requests
    time.sleep(1)

    return details

# Example of scraping properties from Dubizzle
properties = scrape_dubizzle()

# For each property, visit the details page to collect further information
for idx, property in enumerate(properties, 1):
    print(f"\n📄 Processing property {idx}/{len(properties)}...")
    details = scrape_property_details(property["url"])
    property.update(details)

# Save the scraped data into a CSV file
df = pd.DataFrame(properties)
df.to_csv("dubizzle_properties.csv", index=False)

print("✅ Scraping completed and data saved to dubizzle_properties.csv")
