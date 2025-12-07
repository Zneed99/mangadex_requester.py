# mangadex_requester.py
This repository is made to make requests to Mangadex.org
It also now has a secondary source for scraping series that are not updated on mangadex
#

💻 Step 0 — Open PowerShell as Administrator

Press Win + S, type PowerShell

Right-click → Run as Administrator

Navigate to your NSSM folder:

cd "C:\Users\holme\OneDrive\Skrivbord\nssm-2.24-101-g897c7ad\win64"

1️⃣ Remove old service (if it exists)
.\nssm.exe stop MangaDexRequester
.\nssm.exe remove MangaDexRequester confirm


Repeat for any old variants like MangaDexRequester2.0. This avoids conflicts and ensures the new service is clean.

2️⃣ Install the service
.\nssm.exe install MangaDexRequester "C:\Users\holme\AppData\Local\Programs\Python\Python313\python.exe" "C:\Users\holme\mangadex_requester.py\discord_bot.py"


ServiceName → MangaDexRequester

ApplicationPath → Full path to python.exe

Arguments → Full path to your script (discord_bot.py)

3️⃣ Set the working directory
.\nssm.exe set MangaDexRequester AppDirectory "C:\Users\holme\mangadex_requester.py\"


This ensures your bot sees the correct observed_list.json and any other local files.

4️⃣ Start the service
.\nssm.exe start MangaDexRequester

5️⃣ Verify everything

Check that NSSM points to the correct directories:

.\nssm.exe get MangaDexRequester Application
.\nssm.exe get MangaDexRequester AppParameters
.\nssm.exe get MangaDexRequester AppDirectory


✅ They should show:

Application: python.exe path

AppParameters: your script path

AppDirectory: C:\Users\holme\mangadex_requester.py\
