import numpy as np
from pathlib import Path

def main():
    parts = sorted(Path('.').glob('models_part*.npy'))
    print('Found', len(parts), 'parts:')
    for p in parts:
        print(' ', p)
    arrays = [np.load(p) for p in parts]
    full = np.vstack(arrays)
    Path('models').mkdir(exist_ok=True)
    np.save('models/emb_full.npy', full)
    print('Saved models/emb_full.npy shape', full.shape)
    # concatenate jsonl
    parts_meta = sorted(Path('.').glob('models_part*_chunks.jsonl'))
    out_path = Path('models/emb_full_chunks.jsonl')
    with out_path.open('w', encoding='utf8') as out:
        total = 0
        for p in parts_meta:
            with p.open('r', encoding='utf8') as f:
                for line in f:
                    out.write(line)
                    total += 1
    print('Saved', out_path, 'with', total, 'lines')

if __name__ == '__main__':
    main()
