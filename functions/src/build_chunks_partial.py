#!/usr/bin/env python3
"""Create data/chunks.jsonl for the first N rows of the CSV (safe, partial).
Usage: python src/build_chunks_partial.py [N]
"""
import sys
import re
import json
from pathlib import Path
import pandas as pd

from fetch_parse_pmc import fetch_and_cache, parse_pmc_html
from chunking import chunk_section


def pmcid_from_url(url):
    m = re.search(r'(PMC\d+)', url)
    return m.group(1) if m else None


def build_partial(csv_path='data/SB_publication_PMC.csv', out_path='data/chunks.jsonl', n=5, max_tokens=2000):
    df = pd.read_csv(csv_path)
    rows = df.head(n)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)

    chunk_id = 0
    with open(out_path, 'w', encoding='utf-8') as f:
        for _, row in rows.iterrows():
            title = str(row.get('Title') or row.get('title') or '')
            url = str(row.get('Link') or row.get('link') or '')
            pmcid = pmcid_from_url(url) or f'PMC_PART_{_}'
            print(f'Processing {pmcid} {title[:60]}')
            try:
                html = fetch_and_cache(url, pmcid, outdir='models/raw_html')
                parsed = parse_pmc_html(html)

                doc_id = f'doc_{pmcid}'
                # abstract
                if parsed.get('abstract'):
                    for ch in chunk_section(parsed['abstract'], max_tokens=max_tokens):
                        obj = {
                            'chunk_id': f'chunk_{chunk_id:06d}',
                            'doc_id': doc_id,
                            'pmcid': pmcid,
                            'section': 'abstract',
                            'chunk_text': ch,
                            'title': title,
                            'url': url
                        }
                        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                        chunk_id += 1

                for section_name, section_text in parsed.get('sections', {}).items():
                    if section_text and section_text.strip():
                        for ch in chunk_section(section_text, max_tokens=max_tokens):
                            obj = {
                                'chunk_id': f'chunk_{chunk_id:06d}',
                                'doc_id': doc_id,
                                'pmcid': pmcid,
                                'section': section_name,
                                'chunk_text': ch,
                                'title': title,
                                'url': url
                            }
                            f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                            chunk_id += 1

                if parsed.get('funding'):
                    for ch in chunk_section(parsed['funding'], max_tokens=max_tokens):
                        obj = {
                            'chunk_id': f'chunk_{chunk_id:06d}',
                            'doc_id': doc_id,
                            'pmcid': pmcid,
                            'section': 'funding',
                            'chunk_text': ch,
                            'title': title,
                            'url': url
                        }
                        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                        chunk_id += 1

                if parsed.get('acknowledgements'):
                    for ch in chunk_section(parsed['acknowledgements'], max_tokens=max_tokens):
                        obj = {
                            'chunk_id': f'chunk_{chunk_id:06d}',
                            'doc_id': doc_id,
                            'pmcid': pmcid,
                            'section': 'acknowledgements',
                            'chunk_text': ch,
                            'title': title,
                            'url': url
                        }
                        f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                        chunk_id += 1

            except Exception as e:
                print('Error for', url, e)

    print('Wrote', chunk_id, 'chunks to', out_path)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    build_partial(n=n)
