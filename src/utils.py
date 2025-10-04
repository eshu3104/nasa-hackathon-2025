import re, pandas as pd

def load_csv(path="data/SB_publication_PMC.csv"):
    df = pd.read_csv(path)
    # Handle different column names (Title/Link vs title/link)
    if 'Link' in df.columns:
        df['link'] = df['Link'].astype(str)
        df['title'] = df['Title']
    else:
        df['link'] = df['link'].astype(str)
    df['pmcid'] = df['link'].str.extract(r'(PMC\d+)')
    return df
