from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import os
 
def scrape_doctolib(params):
    # Set up the WebDriver with improved options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--disable-gpu")  # Disable GPU hardware acceleration
    chrome_options.add_argument("--disable-extensions")  # Disable extensions
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])  # Disable logging
   
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    print("Script started...")
   
    wait = WebDriverWait(driver, 20)
   
    try:
        # Construct direct search URL instead of using the form
        specialty = params.get("query", "medecin-generaliste")
        location = params.get("location", "75008")
       
        # Format the URL - ensure the specialty and location are properly formatted
        specialty = specialty.lower().replace(" ", "-")
        location = location.replace(" ", "-")
       
        # Direct URL to search results
        search_url = f"https://www.doctolib.fr/search?location={location}&speciality={specialty}"
       
        print(f"Navigating directly to search URL: {search_url}")
        driver.get(search_url)
        time.sleep(3)  # Wait for page to load
       
        # Accept cookies if popup appears
        try:
            cookie_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accepter') or contains(text(), 'accepter')]")),
                timeout=5
            )
            cookie_button.click()
            print("Accepted cookies")
        except:
            print("No cookies popup found or already accepted")
           
        # Wait for search results to load
        try:
            total_results = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-test='total-number-of-results']")
            ))
            print(f"Found results: {total_results.text}")
        except:
            print("Could not find total results element, but continuing...")
 
        # Get links to doctor profiles
        doctor_links = []
        try:
            # Wait for cards to appear
            cards = wait.until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.dl-search-result, div.dl-card-content")
            ))
           
            print(f"Found {len(cards)} doctor cards")
           
            # Process first 10 cards (or fewer if there aren't that many)
            max_doctors = min(20, len(cards))
           
            for card in cards[:max_doctors]:
                try:
                    # Try to find link with more specific XPath or CSS selector
                    link_element = card.find_element(By.CSS_SELECTOR, "a[href*='/']")
                    link = link_element.get_attribute("href")
                    if link and ("/medecin" in link or "/dentiste" in link or "/sage-femme" in link
                               or link.startswith("https://www.doctolib.fr/")):
                        doctor_links.append(link)
                        print(f"Found doctor link: {link}")
                except Exception as link_error:
                    print(f"Error finding link in card: {link_error}")
                    continue
           
            print(f"Collected {len(doctor_links)} doctor links to visit")
           
        except Exception as cards_error:
            print(f"Error finding doctor cards: {cards_error}")
            return []
 
        # Now scrape each doctor profile
        doctors = []
        for i, url in enumerate(doctor_links):
            try:
                print(f"Visiting doctor {i+1} at URL: {url}")
                driver.get(url)
                time.sleep(2)  # Wait for page to load
 
                doctor_info = {
                    "name": "Unknown",
                    "specialty": "Unknown",
                    "address": "Unknown",
                    "availability": "Unknown",
                    "tarif": "Unknown",
                    "convention": "Unknown"
                }
 
                # Name
                try:
                    name_element = driver.find_element(By.CSS_SELECTOR, "h1.dl-text.dl-text-bold.dl-text-title.dl-text-xl.dl-profile-header-name")
                    doctor_info["name"] = name_element.text.strip()
                except:
                    try:
                        name_element = driver.find_element(By.CSS_SELECTOR, "h1.dl-text.dl-text-bold.dl-text-title.dl-text-xl.dl-profile-header-name")
                        doctor_info["name"] = name_element.text.strip()
                    except Exception as name_error:
                        print(f"Error extracting name: {name_error}")
 
                # Specialty
                try:
                    specialty_element = driver.find_element(By.CSS_SELECTOR, ".dl-profile-header-speciality")
                    doctor_info["specialty"] = specialty_element.text.strip()
                except Exception as specialty_error:
                    print(f"Error extracting specialty: {specialty_error}")
 
                # Address
                try:
                    address_element = driver.find_element(By.CSS_SELECTOR, ".dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-neutral-130")
                   
                    doctor_info["address"] = address_element.text.strip()
                except:
                    try:
                        address_element = driver.find_element(By.CSS_SELECTOR, ".dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-neutral-130")
                        doctor_info["address"] = address_element.text.strip()
                    except:
                        try:
                            # Look for address in location info
                            address_element = driver.find_element(By.CSS_SELECTOR, ".dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-text-neutral-130")
                            doctor_info["address"] = address_element.text.strip()
                        except:
                            try:
                                # Try to find any element containing address information by broader search
                                address_elements = driver.find_elements(By.XPATH,
                                    "//*[contains(@class, 'address') or contains(@class, 'location')]")
                               
                                if address_elements:
                                    for elem in address_elements:
                                        text = elem.text.strip()
                                        if text and any(s in text.lower() for s in ["rue", "avenue", "boulevard", "place"]):
                                            doctor_info["address"] = text
                                            break
                            except Exception as address_error:
                                print(f"Error extracting address: {address_error}")
 
                # Availability
                try:
                    slot_element = driver.find_element(By.CSS_SELECTOR, "div.availabilities-slot")
                    doctor_info["availability"] = slot_element.text.strip()
                except:
                    try:
                        avail_element = driver.find_element(By.CSS_SELECTOR, "div.booking-availabilities")
                        doctor_info["availability"] = avail_element.text.strip()
                    except Exception as avail_error:
                        print(f"Error extracting availability: {avail_error}")
                       
                # Tarif (Price)
                try:
                    tarif_element = driver.find_element(By.CSS_SELECTOR, ".dl-profile-fee")
                    doctor_info["tarif"] = tarif_element.text.strip()
                except Exception as tarif_error:
                    print(f"Error extracting tarif: {tarif_error}")
                   
                # Convention type
                try:
                    convention_element = driver.find_element(By.CSS_SELECTOR, "div.dl-profile-text p")
                    doctor_info["convention"] = convention_element.text.strip()
                except Exception as convention_error:
                    print(f"Error extracting convention: {convention_error}")
 
                doctors.append(doctor_info)
                print(f"Successfully scraped doctor {i+1}: {doctor_info['name']}")
               
            except Exception as visit_error:
                print(f"Error processing doctor {i+1}: {visit_error}")
 
        print(f"\nSuccessfully scraped {len(doctors)} doctors")
       
        # Export results to CSV
        export_to_csv(doctors, specialty, location)
       
        return doctors
 
    except Exception as e:
        print("Error occurred during the scraping process:")
        print(e)
        return []
 
    finally:
        try:
            driver.quit()
            print("Browser closed")
        except:
            print("Error closing browser")
 
def export_to_csv(doctors, specialty, location):
 
    # Create data directory if it doesn't exist
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
   
    # Create DataFrame from doctors list
    df = pd.DataFrame(doctors)
   
    # Generate filename based on search parameters and timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{specialty}_{location}_{timestamp}.csv"
    filepath = os.path.join(data_dir, filename)
   
    # Export to CSV
    df.to_csv(filepath, index=False, encoding='utf-8-sig')
   
    print(f"Results exported to: {filepath}")
