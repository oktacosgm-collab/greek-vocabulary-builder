import json, unicodedata

lookup = json.load(open(r"C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_builder\data\wiktionary_lookup.json", encoding='utf-8'))
word   = 'αργυρώνητος'

# Check all normalisation forms
for form in ['NFC', 'NFD', 'NFKC', 'NFKD']:
    n = unicodedata.normalize(form, word)
    print(f"{form}: in lookup = {n in lookup}")

# Find actual key
matches = [k for k in lookup if 'αργυρ' in k]
print(f"\nKeys with αργυρ: {matches}")
if matches:
    k = matches[0]
    print(f"Key  bytes: {[hex(ord(c)) for c in k]}")
    print(f"Word bytes: {[hex(ord(c)) for c in word]}")

# Also check if it was stored differently
print(f"\nDirect lookup result:")
print(lookup.get('αργυρώνητος', 'NOT FOUND'))