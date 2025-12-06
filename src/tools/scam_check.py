import whois
from urllib.parse import urlparse
from datetime import datetime
import tldextract
import re

def get_domain_age(text_input: str):
    #extragem domain-ul
    domain = ""

    url_pattern = r'(?:https?://)?(?:www\.)?[\w-]+\.\w+(?:\.\w+)*'

    if " " in text_input:
        found_urls = re.findall(url_pattern, text_input)
        if found_urls:
            for canditate in found_urls:
                if "." in canditate and len(canditate) > 4:
                    domain = canditate
                    break
    if not domain:
        domain = text_input.strip()
    
    extracted = tldextract.extract(domain)

    if extracted.domain and extracted.suffix:
        domain = f"{extracted.domain}.{extracted.suffix}"
    else:
        return "SKIP: No valid domain found in the text to analyze."
    #verificam informatiile domain-ului
    try:
        domain_info = whois.whois(domain)
    except Exception as err:
        return f"Domain could not be verified: {str(err)}"
    
    date = domain_info.creation_date

    if not date:
        return f"Error: could not extract the creation date for {domain}"

    #extrag data crearii domeniului
    if (isinstance(date, list)):
        data_initiala = date[0]
    else:
        data_initiala = date
    
    now_date = datetime.now()

    #elimin timezone-ul daca exista
    if data_initiala.tzinfo:
        data_initiala = data_initiala.replace(tzinfo = None)

    #calculez numarul de zile ale domeniului respectiv de la data crearii sale
    delta = now_date - data_initiala
    days_active = delta.days

    #returnez pentru mai departe categoria de risc in functie de cat de vechi este domeniul
    if (days_active < 30):
        return f"HIGH RISK: Domain was created {days_active} ago! (less than a month)"
    elif (days_active < 365):
        return f"WARNING: Domain was created {days_active} ago! (less than a year)"
    else:
        return f"SAFE: Domain was created {days_active} ago!"