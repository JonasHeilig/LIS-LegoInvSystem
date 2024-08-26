import requests
import json
import xml.etree.ElementTree as ET
import config


def extract_hash(json_data):
    data = json.loads(json_data)
    return data.get('hash') if data.get('status') == 'success' else None


def extract_set_data(json_data):
    data = json.loads(json_data)
    set_info = data['sets'][0]

    pieces = set_info.get('pieces', 0)

    return {
        'setID': set_info.get('setID'),
        'number': set_info.get('number'),
        'name': set_info.get('name'),
        'ean': set_info.get('barcode', {}).get('EAN'),
        'price': set_info.get('LEGOCom', {}).get('DE', {}).get('retailPrice'),
        'pieces': pieces,
        'image_url': set_info['image']['imageURL'],
    }


def get_user_hash():
    url = 'https://brickset.com/api/v3.asmx'
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'https://brickset.com/api/login'
    }

    body = f"""
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <login xmlns="https://brickset.com/api/">
                <apiKey>{config.api_key}</apiKey>
                <username>{config.username}</username>
                <password>{config.password}</password>
            </login>
        </soap:Body>
    </soap:Envelope>
    """

    response = requests.post(url, headers=headers, data=body)
    print("User hash response content:")
    response_content = response.content.decode('utf-8')
    print(response_content)

    if response.status_code == 200:
        try:
            json_part, xml_part = response_content.split('<?xml', 1)
            return extract_hash(json_part.strip())
        except ValueError:
            print("Error splitting response content.")
            return None
    else:
        print(f"HTTP Error: {response.status_code}")
        return None


def get_set_data(query):
    user_hash = get_user_hash()
    if not user_hash:
        return None

    url = 'https://brickset.com/api/v3.asmx'
    headers = {
        'Content-Type': 'text/xml; charset=utf-8',
        'SOAPAction': 'https://brickset.com/api/getSets'
    }

    body = f"""
    <soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
        <soap:Body>
            <getSets xmlns="https://brickset.com/api/">
                <apiKey>{config.api_key}</apiKey>
                <userHash>{user_hash}</userHash>
                <params>{{"query": "{query}"}}</params>
            </getSets>
        </soap:Body>
    </soap:Envelope>
    """

    response = requests.post(url, headers=headers, data=body)
    print("Set data response content:")
    response_content = response.content.decode('utf-8')
    print(response_content)

    if response.status_code == 200:
        try:
            json_part, xml_part = response_content.split('<?xml', 1)
            return extract_set_data(json_part.strip())
        except ValueError:
            print("Error splitting response content.")
            return None
    else:
        print(f"HTTP Error: {response.status_code}")
        return None
