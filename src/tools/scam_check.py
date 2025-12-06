import whois
from urllib.parse import urlparse
from datetime import datetime

def get_domain_age(url: str):
    #extragem domain-ul
    domain = urlparse(url).netloc
    if (domain == ""):
        domain = url
    
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