import argparse
from datetime import datetime
from doctolib_scraper import (
    setup_driver,
    accept_cookies,
    search_doctors,
    scrape_doctors,
    save_to_csv
)
from selenium.webdriver.support.ui import WebDriverWait

def validate_date(date_str):
    try:
        return datetime.strptime(date_str, '%d/%m/%Y').strftime('%d/%m/%Y')
    except ValueError:
        raise argparse.ArgumentTypeError(f"Date invalide: {date_str}")

def main():
    parser = argparse.ArgumentParser(description="Scraper Doctolib")
    parser.add_argument("--specialite", type=str, required=True, help="Spécialité médicale")
    parser.add_argument("--lieu", type=str, required=True, help="Localisation")
    parser.add_argument("--max_results", type=int, default=10, help="Nombre maximum de résultats")
    parser.add_argument("--output", type=str, default="resultats_doctolib.csv")
    
    args = parser.parse_args()
    
    driver = None
    try:
        driver = setup_driver()
        wait = WebDriverWait(driver, 15)
        
        print("Accès à Doctolib...")
        driver.get("https://www.doctolib.fr/")
        accept_cookies(driver, wait)
        
        print(f"Recherche des médecins pour: {args.specialite} à {args.lieu}")
        search_success = search_doctors(driver, wait, args.specialite, args.lieu)
        
        if search_success:  # Continuer seulement si la recherche a réussi
            print("Recherche terminée, extraction des données...")
            doctors_data = scrape_doctors(driver, wait)
            
            if doctors_data and len(doctors_data) > 0:
                print(f"\nSauvegarde de {len(doctors_data)} résultats dans {args.output}")
                save_to_csv(doctors_data, args.output)
                
                import os
                if os.path.exists(args.output):
                    print(f"✅ Fichier CSV créé avec succès: {args.output}")
                    print(f"   Nombre de médecins sauvegardés: {len(doctors_data)}")
                else:
                    print("❌ Erreur: Le fichier CSV n'a pas été créé")
            else:
                print("❌ Aucune donnée n'a été extraite.")
        else:
            print("❌ La recherche n'a pas donné de résultats.")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
