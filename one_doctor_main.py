import argparse
import os
import csv
import time
from scraping_a_doctor import scrape_doctolib

def print_doctor_info(doctor_info):
    """Affiche les informations d'un médecin"""
    print("\n" + "="*50)
    for key, value in doctor_info.items():
        if value and value != "Unknown":
            print(f"{key}: {value}")
    print("="*50)

def save_results(doctors, specialty, location):
    """Sauvegarde les résultats dans un CSV"""
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"{specialty}_{location}_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            fields = ["name", "specialty", "address", "availability", "tarif", "convention"]
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for doc in doctors:
                writer.writerow({k: v for k, v in doc.items() if v != "Unknown"})
        print(f"\n✓ Résultats sauvegardés dans {filename}")
        return filename
    except Exception as e:
        print(f"❌ Erreur de sauvegarde: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Scraper Doctolib pour un médecin spécifique")
    parser.add_argument("--specialite", type=str, required=True,
                      help="Spécialité du médecin (ex: pediatre)")
    parser.add_argument("--location", type=str, required=True,
                      help="Ville ou code postal (ex: lyon)")
    
    args = parser.parse_args()
    
    print("\n=== Doctolib Scraper ===")
    print(f"Recherche de {args.specialite} à {args.location}")
    
    try:
        results = scrape_doctolib({
            "query": args.specialite,
            "location": args.location,
            "verbose": True  # Active l'affichage détaillé
        })
        
        if results:
            print("\n=== Résultats trouvés ===")
            for i, doctor in enumerate(results, 1):
                print(f"\nMédecin {i}/{len(results)}")
                print_doctor_info(doctor)
            
            save_results(results, args.specialite, args.location)
        else:
            print("\n❌ Aucun résultat")
            
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")

if __name__ == "__main__":
    main()
