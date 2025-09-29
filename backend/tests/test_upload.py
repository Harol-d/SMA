import requests

# Test directo del endpoint
url = "http://localhost:5000/api/upload_excel"
files = {'file': open('ruta/a/tu/excel/test.xlsx', 'rb')}

response = requests.post(url, files=files)
print("Status:", response.status_code)
print("Response:", response.text)