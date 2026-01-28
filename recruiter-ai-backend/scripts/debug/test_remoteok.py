import httpx

r = httpx.get('https://remoteok.com/api', headers={'User-Agent': 'RecruiterAI/1.0'}, timeout=10)
data = r.json()[1:]  # Skip metadata

# Look for ML jobs
ml_jobs = [j for j in data if 'ml' in j.get('position','').lower() or 'machine' in j.get('position','').lower() or 'data' in j.get('position','').lower()]
print(f'Total jobs: {len(data)}')
print(f'ML/Data jobs found: {len(ml_jobs)}')
for job in ml_jobs[:10]:
    print(f"  - {job.get('position')} @ {job.get('company')}")
