import re

def extract_amount_and_currency(text: str):
    # Pattern 1: Khmer payment notification format (e.g., "ចំនួន 11,500 រៀល")
    khmer_amount = extract_khmer_money_amount(text)
    if khmer_amount is not None:
        return '៛', khmer_amount
    
    # Pattern 1b: Khmer dollar format (e.g., "23.25 ដុល្លារ")
    khmer_dollar_amount = extract_khmer_dollar_amount(text)
    if khmer_dollar_amount is not None:
        return '$', khmer_dollar_amount
    
    # Pattern 2: Currency symbol before amount (e.g., "$100", "៛50.25")
    match = re.search(r'([៛$])\s?([\d,]+(?:\.\d+)?)', text)
    if match:
        currency = match.group(1)
        amount_str = match.group(2).replace(',', '')
        try:
            amount = float(amount_str) if '.' in amount_str else int(amount_str)
        except ValueError:
            return None, None
        return currency, amount
    
    # Pattern 3: Amount before currency code (e.g., "65.00 USD", "100.50 KHR")
    match = re.search(r'([\d,]+(?:\.\d+)?)\s+(USD|KHR)', text, re.IGNORECASE)
    if match:
        amount_str = match.group(1).replace(',', '')
        currency_code = match.group(2).upper()
        
        # Convert currency codes to symbols
        currency_map = {
            'USD': '$',
            'KHR': '៛'
        }
        currency = currency_map.get(currency_code, currency_code)
        
        try:
            amount = float(amount_str) if '.' in amount_str else int(amount_str)
        except ValueError:
            return None, None
        return currency, amount
    
    # Pattern 4: Currency code before amount (e.g., "USD 16.00", "KHR 100.50")
    match = re.search(r'(USD|KHR)\s+([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        
        # Convert currency codes to symbols
        currency_map = {
            'USD': '$',
            'KHR': '៛'
        }
        currency = currency_map.get(currency_code, currency_code)
        
        try:
            amount = float(amount_str) if '.' in amount_str else int(amount_str)
        except ValueError:
            return None, None
        return currency, amount
    
    # Pattern 5: "Amount: KHR 562,500" format (payment notification)
    match = re.search(r'Amount:\s+(USD|KHR)\s+([\d,]+(?:\.\d+)?)', text, re.IGNORECASE)
    if match:
        currency_code = match.group(1).upper()
        amount_str = match.group(2).replace(',', '')
        
        # Convert currency codes to symbols
        currency_map = {
            'USD': '$',
            'KHR': '៛'
        }
        currency = currency_map.get(currency_code, currency_code)
        
        try:
            amount = float(amount_str) if '.' in amount_str else int(amount_str)
        except ValueError:
            return None, None
        return currency, amount
    
    return None, None

def extract_khmer_money_amount(text: str) -> float | None:
    """
    Extract money amount from Khmer payment notification text.
    
    Looks for pattern: [number រៀល] regardless of what comes before
    
    Example inputs: 
    - "លោកអ្នកបានទទួលប្រាក់ចំនួន 11,500 រៀល ពីឈ្មោះ SAREACH YUN..."
    - "បានទទួល 5,000 រៀល ពី 096 7772 667 SIN MONOREA..."
    Returns: 11500.0 or 5000.0
    """
    # Pattern: [space number រៀល] - matches space, number, space, then រៀល
    pattern = r'\s([\d,]+(?:\.\d+)?)\s+រៀល'
    match = re.search(pattern, text)
    
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            amount = float(amount_str) if '.' in amount_str else float(amount_str)
            return amount
        except ValueError:
            return None
    
    return None

def extract_khmer_dollar_amount(text: str) -> float | None:
    """
    Extract dollar amount from Khmer payment notification text.
    
    Looks for pattern: [number ដុល្លារ] regardless of what comes before
    
    Example inputs: 
    - "លោកអ្នកបានទទួលប្រាក់ចំនួន 23.25 ដុល្លារ ពីឈ្មោះ PANH BORA..."
    Returns: 23.25
    """
    # Pattern: [space number ដុល្លារ] - matches space, number, space, then ដុល្លារ
    pattern = r'\s([\d,]+(?:\.\d+)?)\s+ដុល្លារ'
    match = re.search(pattern, text)
    
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            amount = float(amount_str) if '.' in amount_str else float(amount_str)
            return amount
        except ValueError:
            return None
    
    return None

def extract_s7pos_final_amount(text: str) -> float | None:
    """
    Extract final amount from s7pos_bot message format.
    
    Looks for pattern: សរុបចុងក្រោយ: [amount] $
    
    Example input:
    - "សរុបចុងក្រោយ: 63.00 $"
    Returns: 63.0
    """
    pattern = r'សរុបចុងក្រោយ:\s*([\d,]+(?:\.\d+)?)\s*\$'
    match = re.search(pattern, text)
    
    if match:
        amount_str = match.group(1).replace(',', '')
        try:
            amount = float(amount_str) if '.' in amount_str else float(amount_str)
            return amount
        except ValueError:
            return None
    
    return None

def extract_s7pos_amount_and_currency(text: str):
    """
    Extract amount and currency specifically for s7pos_bot messages.
    
    Returns tuple (currency, amount) or (None, None) if not found.
    """
    amount = extract_s7pos_final_amount(text)
    if amount is not None:
        return '$', amount
    
    return None, None

def extract_trx_id(message_text: str) -> str | None:
    # Pattern 1: Traditional format "Trx. ID: 123456"
    match = re.search(r'Trx\. ID:\s*([0-9]+)', message_text)
    if match:
        return match.group(1)
    
    # Pattern 2: Hash format "(Hash. abc123def)" or "(Hash. abc123def" (missing closing parenthesis)
    match = re.search(r'\(Hash\.\s*([a-f0-9]+)\)?', message_text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 3: Khmer format "លេខយោង [reference_number]"
    match = re.search(r'លេខយោង\s+([0-9]+)', message_text)
    if match:
        return match.group(1)
    
    # Pattern 4: Khmer transaction format "លេខប្រតិបត្តិការ: 123456"
    match = re.search(r'លេខប្រតិបត្តិការ:\s*([0-9]+)', message_text)
    if match:
        return match.group(1)
    
    # Pattern 5: Advanced Bank of Asia "Txn Hash: abc123def"
    match = re.search(r'Txn Hash:\s*([a-f0-9]+)', message_text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 6: QRPay "Transaction Hash: XXXXXXXX" format
    match = re.search(r'Transaction Hash:\s*([a-f0-9]+)', message_text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    # Pattern 7: Reference ID format "Ref.ID: 123456"
    match = re.search(r'Ref\.ID:\s*([0-9]+)', message_text)
    if match:
        return match.group(1)
    
    # Pattern 8: Transaction ID format "Transaction ID: 099QORT252080682"
    match = re.search(r'Transaction ID:\s*([a-zA-Z0-9]+)', message_text)
    if match:
        return match.group(1)
    
    # Pattern 9: Reference No format "Reference No: 737407541"
    match = re.search(r'Reference No:\s*([0-9]+)', message_text)
    if match:
        return match.group(1)
    
    # Pattern 10: Hash format "Hash: 2e720fc0"
    match = re.search(r'Hash:\s*([a-f0-9]+)', message_text, re.IGNORECASE)
    if match:
        return match.group(1)
    
    return None