import requests
import json

# Login
login_resp = requests.post('http://localhost:8000/api/auth/login', json={
    'email': 'test@example.com',
    'password': 'test123'
})

if login_resp.status_code != 200:
    print(f'Login failed: {login_resp.status_code}')
    exit(1)

print('✓ Logged in')

# Request with max_papers=7
resp = requests.post(
    'http://localhost:8000/api/research/digest',
    json={'topic': 'AI in healthcare', 'max_papers': 7},
    cookies=login_resp.cookies,
    stream=True,
    timeout=60
)

print(f'Status: {resp.status_code}')

if resp.status_code == 200:
    for line in resp.iter_lines():
        if not line:
            continue
        line_str = line.decode('utf-8')
        
        if 'selected_papers' in line_str:
            print('\n📄 SELECTED_PAPERS EVENT:')
            idx = line_str.find('data: ')
            if idx != -1:
                data_str = line_str[idx+6:]
                data = json.loads(data_str)
                count = len(data.get('papers', []))
                print(f'   ✓ Selected {count} papers (requested max_papers=7)')
                print(f'   Expected: 5-7 papers, Got: {count}')
                
        elif 'papers_found' in line_str:
            print('🔍 PAPERS_FOUND EVENT:')
            idx = line_str.find('data: ')
            if idx != -1:
                data_str = line_str[idx+6:]
                data = json.loads(data_str)
                total = data.get('count')
                print(f'   Found {total} papers total from arXiv')
else:
    print(resp.text[:500])
