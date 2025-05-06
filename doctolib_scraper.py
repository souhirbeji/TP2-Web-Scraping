import time
import random
import os
from tqdm import tqdm
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import csv

def setup_driver():
    """Configure et retourne le driver Selenium"""
    service = Service(ChromeDriverManager().install())
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def accept_cookies(driver, wait):
    """Accepte les cookies si la fenêtre apparaît"""
    try:
        cookie_button = wait.until(EC.element_to_be_clickable((By.ID, "didomi-notice-agree-button")))
        cookie_button.click()
        print("✓ Cookies acceptés")
    except:
        print("Pas de fenêtre de cookies ou délai dépassé.")

def scroll_to_element(driver, element):
    """Défile jusqu'à l'élément et attends qu'il soit cliquable"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        time.sleep(3)  # Pause longue pour laisser la page se stabiliser
    except Exception as e:
        print(f"Erreur lors du défilement: {e}")

def wait_for_results_page(driver, wait, timeout=10):
    """Vérifie si des résultats sont présents sur la page"""
    print("Vérification des résultats...")
    time.sleep(2)  # Bref délai pour le chargement
    
    try:
        # Chercher tous les éléments contenant le mot "résultat"
        result_elements = driver.find_elements(By.CSS_SELECTOR, ".dl-text.dl-text-body.dl-text-bold.dl-text-s")
        
        for element in result_elements:
            text = element.text.lower()
            if "résultats" in text:
                count = int(''.join(filter(str.isdigit, text)))
                print(f"✓ {count} résultats trouvés")
                return True
        
        print("⚠️ Aucun résultat trouvé")
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des résultats: {e}")
        return False

def search_doctors(driver, wait, speciality, location, max_retries=2):
    """Recherche des médecins par spécialité et localisation"""
    print(f"Recherche de {speciality} à {location}...")
    
    for attempt in range(max_retries):
        try:
            # Attendre que la barre de recherche soit visible
            print("Attente de la barre de recherche...")
            search_container = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".searchbar-input-wrapper")))
            
            # Recherche par spécialité
            speciality_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.searchbar-query-input")))
            speciality_input.clear()
            speciality_input.send_keys(speciality)
            print(f"✓ Spécialité saisie: {speciality}")
            time.sleep(3)  # Augmenté pour plus de fiabilité
            
            # Attendre les suggestions de spécialité
            try:
                speciality_suggestions = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".searchbar-suggestion")))
                speciality_suggestions.click()
                print("✓ Suggestion de spécialité sélectionnée")
                time.sleep(2)
            except:
                print("Pas de suggestion pour la spécialité")
            
            # Recherche par lieu
            place_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "input.searchbar-place-input")))
            place_input.clear()
            place_input.send_keys(location)
            print(f"✓ Lieu saisi: {location}")
            time.sleep(3)  # Augmenté pour plus de fiabilité
            
            # Attendre et sélectionner une suggestion de lieu si disponible
            try:
                place_suggestion = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".searchbar-place-suggestion")))
                place_suggestion.click()
                print("✓ Suggestion de lieu sélectionnée")
                time.sleep(2)
            except:
                print("Pas de suggestion pour le lieu")
            
            # Cliquer sur le bouton de recherche
            search_button = wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.searchbar-submit-button")))
            search_button.click()
            print("✓ Bouton de recherche cliqué")
            time.sleep(5)  # Augmenté pour permettre le chargement de la page
            
            # Attendre le chargement de la page de résultats
            if wait_for_results_page(driver, wait):
                print("✓ Page de résultats chargée avec succès")
                return True
            else:
                print(f"Tentative {attempt+1}/{max_retries}: Page de résultats non chargée")
                
                if attempt < max_retries - 1:
                    print("Retour à la page d'accueil et nouvelle tentative...")
                    driver.get("https://www.doctolib.fr/")
                    time.sleep(5)
                    accept_cookies(driver, wait)
                
        except Exception as e:
            print(f"Erreur lors de la recherche (tentative {attempt+1}/{max_retries}): {e}")
            
            if attempt < max_retries - 1:
                print("Retour à la page d'accueil et nouvelle tentative...")
                driver.get("https://www.doctolib.fr/")
                time.sleep(5)
                accept_cookies(driver, wait)
    
    print("❌ Échec de la recherche après plusieurs tentatives")
    return False

def load_more_results(driver, wait):
    """Charge plus de résultats en cliquant sur le bouton 'Afficher plus de résultats'"""
    try:
        load_more_selectors = [
            "button.dl-button-primary:contains('Afficher plus')",
            "button.dl-button-primary",
            ".dl-button-primary",
            "[data-test='load-more-button']"
        ]
        
        for selector in load_more_selectors:
            try:
                # Faire défiler jusqu'en bas de la page
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                
                # Vérifier si le bouton existe
                load_more_buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                for button in load_more_buttons:
                    if "plus" in button.text.lower() or "more" in button.text.lower():
                        print("Chargement de résultats supplémentaires...")
                        scroll_to_element(driver, button)
                        button.click()
                        time.sleep(5)  # Attendre le chargement des nouveaux résultats
                        return True
            except:
                continue
        
        print("Aucun bouton 'Afficher plus' trouvé ou tous les résultats ont été chargés.")
        return False
    except Exception as e:
        print(f"Erreur lors du chargement de résultats supplémentaires: {e}")
        return False

def scrape_doctors(driver, wait, max_results=None):
    """Récupère les informations des médecins sur la page actuelle"""
    doctors_data = []
    
    try:
        # Charger plus de résultats si le nombre maximum n'est pas atteint
        if max_results is None or max_results > 20:
            # Essayer de charger plus de résultats jusqu'à 5 fois
            for i in range(5):
                if not load_more_results(driver, wait):
                    break
                print(f"Page {i+2} de résultats chargée")
                time.sleep(3)
        
        # Essayez différents sélecteurs pour les cartes de médecins
        doctor_cards = []
        card_selectors = [
            "div[data-test='search-result']",
            ".dl-search-result", 
            ".dl-search-result-presentation",
            ".search-result-card"
        ]
        
        for selector in card_selectors:
            try:
                doctor_cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if len(doctor_cards) > 0:
                    print(f"✓ {len(doctor_cards)} médecins trouvés avec le sélecteur: {selector}")
                    break
            except:
                continue
        
        if not doctor_cards:
            print("❌ Aucune carte de médecin trouvée.")
            return doctors_data
        
        # Limiter le nombre de résultats si spécifié
        if max_results and max_results < len(doctor_cards):
            doctor_cards = doctor_cards[:max_results]
            print(f"Limitation à {max_results} résultats.")
        
        # Extraire les données de chaque carte
        for i, card in enumerate(tqdm(doctor_cards, desc="Extraction des données")):
            try:
                # Faire défiler jusqu'à la carte pour s'assurer qu'elle est visible
                scroll_to_element(driver, card)
                
                # Extraire les informations du médecin
                info = extract_doctor_info(card)
                
                # Ajouter à la liste si on a au moins le nom
                if info["Nom complet"] != "Non spécifié":
                    doctors_data.append(info)
                    print(f"✓ Médecin {i+1}/{len(doctor_cards)}: {info['Nom complet']}")
                else:
                    print(f"⚠️ Médecin {i+1}/{len(doctor_cards)}: Informations incomplètes")
                    
            except StaleElementReferenceException:
                print(f"⚠️ Élément devenu périmé, médecin {i+1}/{len(doctor_cards)} ignoré")
                continue
            except Exception as e:
                print(f"⚠️ Erreur pour médecin {i+1}/{len(doctor_cards)}: {e}")
                continue
                
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des médecins: {e}")
    
    print(f"✓ Extraction terminée: {len(doctors_data)} médecins avec données complètes")
    return doctors_data

def extract_doctor_info(card):
    """Extrait les informations d'un médecin à partir de sa carte"""
    info = {
        "Nom complet": "Non spécifié",
        "Spécialité": "Non spécifié",
        "Prochaine disponibilité": "Non spécifié",
        "Secteur d'assurance": "Non spécifié",
        "Prix estimé": "Non spécifié",
        "Rue": "Non spécifié",
        "Code postal": "Non spécifié",
        "Ville": "Non spécifié"
    }
    
    try:
        # Nom (plusieurs sélecteurs possibles)
        name_selectors = [
            "a[data-test='search-result-name']",
            "h3.dl-search-result-name",
            ".dl-search-result-name"
        ]
        
        for selector in name_selectors:
            try:
                name_element = card.find_element(By.CSS_SELECTOR, selector)
                name_text = name_element.text.strip()
                if name_text:
                    info["Nom complet"] = name_text
                    break
            except:
                continue
        
        # Spécialité (plusieurs sélecteurs possibles)
        specialty_selectors = [
            "div.dl-search-result-subtitle",
            ".dl-search-result-specialty",
            "[data-test='search-result-specialty']"
        ]
        
        for selector in specialty_selectors:
            try:
                specialty_element = card.find_element(By.CSS_SELECTOR, selector)
                specialty_text = specialty_element.text.strip()
                if specialty_text:
                    info["Spécialité"] = specialty_text
                    break
            except:
                continue
        
        # Disponibilité
        try:
            availability_selectors = [
                "div[data-test='availability-date']",
                ".availabilities-slot",
                ".dl-search-result-availability"
            ]
            
            for selector in availability_selectors:
                try:
                    availability = card.find_element(By.CSS_SELECTOR, selector)
                    availability_text = availability.text.strip()
                    if availability_text:
                        info["Prochaine disponibilité"] = availability_text
                        break
                except:
                    continue
        except:
            pass
        
        # Adresse
        try:
            address_selectors = [
                "div[data-test='search-result-practice-address']",
                ".dl-text.dl-text-body.dl-text-regular.dl-text-s.dl-search-result-address",
                ".dl-search-result-address"
            ]
            
            for selector in address_selectors:
                try:
                    address_element = card.find_element(By.CSS_SELECTOR, selector)
                    address_text = address_element.text.strip()
                    if address_text:
                        address_parts = address_text.split('\n')
                        
                        if len(address_parts) >= 1:
                            info["Rue"] = address_parts[0].strip()
                            
                        if len(address_parts) >= 2:
                            city_info = address_parts[-1].strip()
                            if ' ' in city_info:
                                postal_code, city = city_info.split(' ', 1)
                                info["Code postal"] = postal_code.strip()
                                info["Ville"] = city.strip()
                        break
                except:
                    continue
        except:
            pass
        
        # Secteur d'assurance et prix
        try:
            price_selectors = [
                ".dl-search-result-price",
                "[data-test='search-result-price']",
                ".dl-text-body"
            ]
            
            for selector in price_selectors:
                try:
                    elements = card.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip().lower()
                        if "conventionné" in text or "secteur" in text:
                            info["Secteur d'assurance"] = element.text.strip()
                        elif "€" in text:
                            info["Prix estimé"] = element.text.strip()
                except:
                    continue
        except:
            pass
        
        time.sleep(1)  # Attendre un peu entre chaque extraction
        return info
        
    except Exception as e:
        print(f"Erreur lors de l'extraction des données: {e}")
        return info

def save_to_csv(doctors_data, filename="resultats_doctolib.csv"):
    """Sauvegarde les informations des médecins dans un fichier CSV"""
    if not doctors_data:
        print("❌ Aucune donnée à sauvegarder.")
        return False
    
    try:
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                "Nom complet", "Spécialité", "Prochaine disponibilité", 
                "Secteur d'assurance", "Prix estimé", "Rue", "Code postal", "Ville"
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for doctor in doctors_data:
                writer.writerow(doctor)
                
        print(f"✅ {len(doctors_data)} médecins sauvegardés dans {filename}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde du CSV: {e}")
        return False