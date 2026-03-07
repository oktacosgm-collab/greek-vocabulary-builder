import json, re
from pathlib import Path

BASE  = Path(r'C:\Users\oktac\OneDrive\Documents\python codes\greek_vocabulary_learner')
cache = json.load(open(BASE / 'data' / 'enriched_cache.json', encoding='utf-8'))
audio = BASE / 'audio'

ok = partial = missing = 0
for word in cache:
    safe = re.sub(r'[^\w]', '_', word)
    w = (audio / f'{safe}_word.mp3').exists()
    d = (audio / f'{safe}_definition.mp3').exists()
    e = (audio / f'{safe}_example.mp3').exists()
    if w and d and e:
        ok += 1
    elif w or d or e:
        partial += 1
    else:
        missing += 1

print(f'Total words in cache : {len(cache)}')
print(f'Complete all 3 files : {ok}')
print(f'Partial 1-2 files    : {partial}')
print(f'Missing no files     : {missing}')
print()
if ok == len(cache):
    print('All words complete! Ready to run the app.')
else:
    print(f'WARNING: {len(cache)-ok} words still need audio.')