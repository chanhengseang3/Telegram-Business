import unittest

from helper.message_parser import extract_amount_and_currency, extract_trx_id


class TestMessageParser(unittest.TestCase):

    def test_aba_khmer__format(self):
        """Test Khmer payment notification format"""
        message = "៛6,500 ត្រូវបានបង់ដោយ CHHE SOKHEAP (*503) នៅថ្ងៃទី 9 ខែកក្កដា ឆ្នាំ 2025 ម៉ោង 16:14 តាម ABA PAY នៅ LONGVEK by K.PHA។ លេខប្រតិបត្តិការ: 175205247086840។ APV: 773843។"

        currency, amount = extract_amount_and_currency(message)
        trx_id = extract_trx_id(message)

        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 6500)
        self.assertEqual(trx_id, '175205247086840')

    def test_aba_eng_format(self):
        """Test Advanced Bank of Asia USD format"""
        message = "10.00 USD was paid to your account: INCOME TENGLAY DEPOT 698594011 on 09 JUL 2025 at 16:01:59 from  Advanced Bank of Asia Ltd. Acc: SAPUTHY KIM 001XXXXXXXX3633 with Ref: FT25190GHKVC, Txn Hash: b117ffd9"

        currency, amount = extract_amount_and_currency(message)
        trx_id = extract_trx_id(message)

        self.assertEqual(currency, '$')
        self.assertEqual(amount, 10.0)
        self.assertEqual(trx_id, 'b117ffd9')

    def test_acleda_khmer_format(self):
        """Test specific Khmer money amount patterns"""
        test_cases = [
            ("លោកអ្នកបានទទួលប្រាក់ចំនួន 11,500 រៀល ពីឈ្មោះ SAREACH YUN", '៛', 11500.0),
            ("បានទទួល 5,000 រៀល ពី 096 7772 667 SIN MONOREA", '៛', 5000.0),
            ("ចំនួន 250.50 រៀល បានទទួល", '៛', 250.5),
        ]

        for message, expected_currency, expected_amount in test_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)

    def test_acleda_eng_format(self):
        """Test specific ACLEDA bank message patterns"""
        test_cases = [
            ("Received 1.38 USD from 015 738 813 Mom Soman, 09-Jul-2025 03:08PM. Ref.ID: 51903055598, at MIK YEK NEA.",
             '$', 1.38),
            ("Received 5,500 KHR from 010 574 279 Pen Chamnab, 10-Jul-2025 07:50AM. Ref.ID: 51910666401, at MIK YEK NEA.",
             '៛', 5500)
        ]

        for message, expected_currency, expected_amount in test_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)

    def test_canadia_eng_format(self):
        """Test specific Khmer money amount patterns"""
        test_cases = [
            ("10.00 USD was paid to your account: INCOME TENGLAY DEPOT 698594011 on 09 JUL 2025 at 17:11:40 from  Advanced Bank of Asia Ltd. Acc: THAVY HONG 001XXXXXXXX2169 with Ref: FT25190WZFTL, Txn Hash: cba162a9",
             '$', 10.0)
        ]

        for message, expected_currency, expected_amount in test_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)

    def test_canadia_khmer_dollar_format(self):
        """Test Canadia Bank Khmer dollar format"""
        test_cases = [
            ("លោកអ្នកបានទទួលប្រាក់ចំនួន 23.25 ដុល្លារ  ពីឈ្មោះ PANH BORA ធនាគារ Canadia Bank Plc តាមការស្កេន  KHQR ថ្ងៃទី ១២ កក្កដា ២០២៥​ ម៉ោង ០៩:០៧ល្ងាច នៅ អាហារដ្ឋានសុនិសា168, SMART-PAY:00060050180 (Hash. 6c648d8",
             '$', 23.25),
            ("ទទួលបាន 15.50 ដុល្លារ ពីអ្នកប្រើប្រាស់", '$', 15.5),
            ("បង់ប្រាក់ចំនួន 100.00 ដុល្លារ", '$', 100.0),
        ]

        for message, expected_currency, expected_amount in test_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                trx_id = extract_trx_id(message)
                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)
                
        # Test transaction ID extraction for the full message
        full_message = "លោកអ្នកបានទទួលប្រាក់ចំនួន 23.25 ដុល្លារ  ពីឈ្មោះ PANH BORA ធនាគារ Canadia Bank Plc តាមការស្កេន  KHQR ថ្ងៃទី ១២ កក្កដា ២០២៥​ ម៉ោង ០៩:០៧ល្ងាច នៅ អាហារដ្ឋានសុនិសា168, SMART-PAY:00060050180 (Hash. 6c648d8"
        trx_id = extract_trx_id(full_message)
        self.assertEqual(trx_id, "6c648d8")

    def test_vathanak_eng_format(self):
        """Test specific Khmer money amount patterns"""
        test_cases = [
            ("""USD 16.00 is paid by CHANTARY MUNY (ABA Bank) via KHQR on 08/07/2025 07:49 PM at HOUSE 59 BY S.MEL
Trx. ID: 001FTRA25189D0JF
Hash: 74f576d0""", '$', 16.0)
        ]

        for message, expected_currency, expected_amount in test_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)

    def test_currency_symbol_before_amount(self):
        """Test currency symbol before amount format"""
        test_cases = [
            ("$100", '$', 100),
            ("៛50.25", '៛', 50.25),
            ("$ 75", '$', 75),
            ("៛ 1,500", '៛', 1500),
        ]

        for message, expected_currency, expected_amount in test_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)

    def test_amount_before_currency_code(self):
        """Test amount before currency code format"""
        test_cases = [
            ("65.00 USD", '$', 65.0),
            ("100.50 KHR", '៛', 100.5),
            ("1,000 usd", '$', 1000),
            ("2,500.75 khr", '៛', 2500.75),
        ]

        for message, expected_currency, expected_amount in test_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)

    def test_sathapana_khqr_format(self):
        """Test sathapana Bank KHQR payment format"""
        message = "The amount 10.50 USD is paid from TIA PHALLA, ACLEDA Bank Plc., Bill No.: 52081784162 | KHQR on 2025-07-27 11.33.00 AM with Transaction ID: 099QORT252080682, Hash: bf3c3602, Shop-name: Dariya Restaurant"
        
        currency, amount = extract_amount_and_currency(message)
        trx_id = extract_trx_id(message)
        
        self.assertEqual(currency, '$')
        self.assertEqual(amount, 10.5)
        self.assertEqual(trx_id, '099QORT252080682')

    def test_payment_notification_format(self):
        """Test payment notification format with Amount:, Reference No:, and Hash:"""
        message = """Dear valued customer, you have received a payment:
Amount: KHR 562,500
Datetime: 2025/08/22, 01:01 pm
Reference No: 737407541
Merchant name: SOU CHENDA
Received from: Oeun Seangleng
Sender's bank: ACLEDA Bank Plc.
Hash: 2e720fc0"""
        
        currency, amount = extract_amount_and_currency(message)
        trx_id = extract_trx_id(message)
        
        self.assertEqual(currency, '៛')
        self.assertEqual(amount, 562500)
        self.assertEqual(trx_id, '737407541')

    def test_transaction_id_patterns(self):
        """Test various transaction ID patterns"""
        test_cases = [
            ("Payment completed. Trx. ID: 123456", "123456"),
            ("Transaction (Hash. abc123def)", "abc123def"),
            ("លេខយោង 987654", "987654"),
            ("លេខប្រតិបត្តិការ: 175205247086840", "175205247086840"),
            ("Transaction completed, Txn Hash: b117ffd9", "b117ffd9"),
            ("TXN HASH: A1B2C3D4", "A1B2C3D4"),  # case sensitive
            ("Received 5,500 KHR from 010 574 279 Pen Chamnab, 10-Jul-2025 07:50AM. Ref.ID: 51910666401, at MIK YEK NEA.", "51910666401"),
            ("The amount 10.50 USD is paid from TIA PHALLA, ACLEDA Bank Plc., Bill No.: 52081784162 | KHQR on 2025-07-27 11.33.00 AM with Transaction ID: 099QORT252080682, Hash: bf3c3602, Shop-name: Dariya Restaurant", "099QORT252080682"),
            ("Reference No: 737407541", "737407541"),
            ("Hash: 2e720fc0", "2e720fc0"),
        ]

        for message, expected_trx_id in test_cases:
            with self.subTest(message=message):
                trx_id = extract_trx_id(message)
                self.assertEqual(trx_id, expected_trx_id)

    def test_no_match_cases(self):
        """Test cases where no matches should be found"""
        no_amount_messages = [
            "This is just a regular message",
            "No money mentioned here",
            "រៀល without amount",
            "USD without number",
        ]

        for message in no_amount_messages:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                self.assertIsNone(currency)
                self.assertIsNone(amount)

        no_trx_messages = [
            "Payment completed successfully",
            "No transaction ID here",
            "Random text message",
        ]

        for message in no_trx_messages:
            with self.subTest(message=message):
                trx_id = extract_trx_id(message)
                self.assertIsNone(trx_id)

    def test_edge_cases(self):
        """Test edge cases and malformed inputs"""
        edge_cases = [
            ("", None, None, None),  # Empty string
            ("$", None, None, None),  # Currency symbol only
            ("123", None, None, None),  # Number only
            ("50 USD extra text", '$', 50, None),  # Valid amount, no trx_id
            ("Invalid amount: $ abc", None, None, None),  # Invalid amount
            ("Received 100 KHR from someone", '៛', 100, None),  # Valid amount, no transaction ID
        ]

        for message, expected_currency, expected_amount, expected_trx_id in edge_cases:
            with self.subTest(message=message):
                currency, amount = extract_amount_and_currency(message)
                trx_id = extract_trx_id(message)

                self.assertEqual(currency, expected_currency)
                self.assertEqual(amount, expected_amount)
                self.assertEqual(trx_id, expected_trx_id)


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)
