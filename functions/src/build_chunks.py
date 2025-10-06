#!/usr/bin/env python3
"""
Build chunks.jsonl file from PMC articles.
Each line contains: {chunk_id, doc_id, pmcid, section, chunk_text, title, url}
"""

import json
import sys
import pandas as pd
from pathlib import Path
from utils import load_csv
from fetch_parse_pmc import fetch_and_cache, parse_pmc_html
from chunking import chunk_section

def build_chunks(csv_path="data/space_bio_608.csv", output_path="data/chunks.jsonl"):
    """Build chunks.jsonl from PMC articles."""
    
    print("Loading CSV data...")
    df = load_csv(csv_path)
    
    print(f"Found {len(df)} articles to process")
    
    chunks_data = []
    chunk_id_counter = 0
    
    for idx, row in df.iterrows():
        pmcid = row['pmcid']
        url = row['link']
        title = row.get('title', 'Unknown Title')
        
        if pd.isna(pmcid) or pmcid == '':
            print(f"Skipping row {idx}: No PMC ID")
            continue
            
        print(f"Processing {pmcid}: {title[:50]}...")
        
        try:
            # Fetch and parse HTML
            html = fetch_and_cache(url, pmcid)
            parsed = parse_pmc_html(html)
            
            # Create doc_id from pmcid
            doc_id = f"doc_{pmcid}"
            
            # Process abstract
            if parsed['abstract']:
                abstract_chunks = chunk_section(parsed['abstract'])
                for chunk_text in abstract_chunks:
                    chunks_data.append({
                        'chunk_id': f"chunk_{chunk_id_counter:06d}",
                        'doc_id': doc_id,
                        'pmcid': pmcid,
                        'section': 'abstract',
                        'chunk_text': chunk_text,
                        'title': title,
                        'url': url
                    })
                    chunk_id_counter += 1
            
            # Process sections
            for section_name, section_text in parsed['sections'].items():
                if section_text.strip():
                    section_chunks = chunk_section(section_text)
                    for chunk_text in section_chunks:
                        chunks_data.append({
                            'chunk_id': f"chunk_{chunk_id_counter:06d}",
                            'doc_id': doc_id,
                            'pmcid': pmcid,
                            'section': section_name,
                            'chunk_text': chunk_text,
                            'title': title,
                            'url': url
                        })
                        chunk_id_counter += 1
            
            # Process funding if available
            if parsed['funding']:
                funding_chunks = chunk_section(parsed['funding'])
                for chunk_text in funding_chunks:
                    chunks_data.append({
                        'chunk_id': f"chunk_{chunk_id_counter:06d}",
                        'doc_id': doc_id,
                        'pmcid': pmcid,
                        'section': 'funding',
                        'chunk_text': chunk_text,
                        'title': title,
                        'url': url
                    })
                    chunk_id_counter += 1
            
            # Process acknowledgements if available
            if parsed['acknowledgements']:
                ack_chunks = chunk_section(parsed['acknowledgements'])
                for chunk_text in ack_chunks:
                    chunks_data.append({
                        'chunk_id': f"chunk_{chunk_id_counter:06d}",
                        'doc_id': doc_id,
                        'pmcid': pmcid,
                        'section': 'acknowledgements',
                        'chunk_text': chunk_text,
                        'title': title,
                        'url': url
                    })
                    chunk_id_counter += 1
                    
        except Exception as e:
            print(f"Error processing {pmcid}: {e}")
            continue
    
    # Write chunks to JSONL file
    print(f"Writing {len(chunks_data)} chunks to {output_path}...")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for chunk in chunks_data:
            f.write(json.dumps(chunk, ensure_ascii=False) + '\n')
    
    print(f"Successfully created {output_path} with {len(chunks_data)} chunks")
    
    # Print summary statistics
    sections = {}
    for chunk in chunks_data:
        section = chunk['section']
        sections[section] = sections.get(section, 0) + 1
    
    print("\nChunk summary by section:")
    for section, count in sorted(sections.items()):
        print(f"  {section}: {count} chunks")

if __name__ == "__main__":
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/SB_publication_PMC.csv"
    output_path = sys.argv[2] if len(sys.argv) > 2 else "data/chunks.jsonl"
    
    build_chunks(csv_path, output_path)
