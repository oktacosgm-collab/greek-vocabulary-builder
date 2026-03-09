import json
data = json.load(open(r"C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_builder\data\enriched_cache.json", encoding='utf-8'))
verbs = {k:v for k,v in data.items() if v.get('part_of_speech','').lower() == 'verb'}
print(f'Found {len(verbs)} verbs')
first = next(iter(verbs.items()))
print(first[0])
print(json.dumps(first[1], ensure_ascii=False, indent=2))