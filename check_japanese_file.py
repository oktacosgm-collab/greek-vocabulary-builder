import json
data = json.load(open(r"C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_builder\data\enriched_cache.json", encoding='utf-8'))
first = next(iter(data.items()))
print(first[0])
print('translation_ja:', first[1].get('translation_ja','MISSING'))
print('definition_ja:', first[1].get('definition_ja','MISSING'))
print('example_english_ja:', first[1].get('example_english_ja','MISSING'))