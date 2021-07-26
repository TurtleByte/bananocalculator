import bananopy.banano as ban
from datetime import datetime
import csv
import time
from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
from urllib.request import urlopen
from bs4 import BeautifulSoup

# Loads Dictionary of all known usernames and their associated wallets
addressToUserDict = {}
with open('usernames.csv', newline='', encoding="utf8") as myFile:
    reader = csv.reader(myFile)
    for row in reader:
        addressToUserDict[row[0]] = row[1]

# Checks F@H Stats
listOfUsernamesInTeam = []
print("Obtaining F@H Team Stats...")
list_header = []
soup = BeautifulSoup(urlopen('https://apps.foldingathome.org/teamstats/team234980.html'),'html.parser')
header = soup.find_all("table")[1].find("tr")
for items in header:
    try:
        list_header.append(items.get_text())
    except:
        continue
HTML_data = soup.find_all("table")[1].find_all("tr")[1:]
for element in HTML_data:
    sub_data = []
    for sub_element in element:
        try:
            sub_data.append(sub_element.get_text())
        except:
            continue
    listOfUsernamesInTeam.append(sub_data[2])

# Creating a list of new/missed usernames to obtain their wallets for the dictionary
unknownUsernameCount = 0
toAddToDictionaryList = []
for username in listOfUsernamesInTeam:
    if username.lower() not in addressToUserDict.values() and len(username) == 12 and username.isalnum():
        toAddToDictionaryList.append(username.lower())
scrapeStartTime = time.time()

# Scrapes Bminer to obtain wallet address
chunkSize = 10
chunks = [toAddToDictionaryList[x:x+chunkSize] for x in range(0, len(toAddToDictionaryList), chunkSize)]
timeList = [scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime]
scrapeErrorCount = 0
headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
print(str(len(chunks)) + " chunks generated")
j = 0
i = 1
for chunk in chunks:
    with FuturesSession() as session:
        futures = [session.get('https://bananominer.com/user_name/' + userName, headers=headers, timeout=20) for userName in chunk]
        for future in as_completed(futures):
            try:
                response = future.result()
                user = response.json()
                addressToUserDict[user['user']['name']] = user['user']['id']
                print(user['user']['id'], user['user']['name'])
                j += 1
            except IndexError:
                pass
            except Exception as e:
                print(response, e)
                scrapeErrorCount += 1
    print("Finished Chunk " + str(i) + " of " + str(len(chunks)) + ". Addresses Found: " + str(j))
    scrapeDuration = time.time() - timeList[i % 10]
    timeList[i % 10] = time.time()
    estimatedTimeRemaining = (scrapeDuration / 10) * (len(chunks) - i)
    totalDuration = time.time() - scrapeStartTime
    print("Time Elapsed: " + str(int(totalDuration // 60)) + "m" + str(
        int(totalDuration % 60)) + "s. Estimated Time Remaining: " + str(int(estimatedTimeRemaining // 60)) + "m" + str(
        int(estimatedTimeRemaining % 60)) + "s.")
    print("Scraping Errors So Far: " + str(scrapeErrorCount))
    i += 1
    time.sleep(0.3)

# Save the expanded username list
with open('usernames.csv', 'w', newline='') as myFile:
    writer = csv.writer(myFile)
    for address in addressToUserDict:
        writer.writerow([address, addressToUserDict[address]])
    myFile.close()

# Querying the Network
numberToGet = 10000
iterator = 0
currentDate = datetime.utcnow()
if currentDate.hour >= 12:
    hour = 12
else:
    hour = 0

dateOfFold = datetime(currentDate.year, currentDate.month, currentDate.day, hour)
dateOfFoldUnix = time.mktime(dateOfFold.timetuple())
print("Querying for Payout on", dateOfFold)
account = "ban_3fo1d1ng6mfqumfoojqby13nahaugqbe5n6n3trof4q8kg5amo9mribg4muo"

tempjson = ban.account_history(account, numberToGet)    
while True:
    print(numberToGet, dateOfFoldUnix, tempjson['history'][-1]['local_timestamp'] - 28800)
    transactionCount = 0
    listOfFolders = []
    for transaction in tempjson['history']:
        if transaction['local_timestamp'] - 28800 > dateOfFoldUnix and transaction['type'] == 'send':
            listOfFolders.append(addressToUserDict[transaction['account']])
            transactionCount += 1
    if tempjson['history'][-1]['local_timestamp'] - 28800 < dateOfFoldUnix:
        break
    else:
        tempjson = ban.account_history(account, numberToGet, head=tempjson['previous'])

print("Total Sends: ", transactionCount)

currentDate = datetime.utcnow()
if currentDate.hour >= 12:
    hour = 12
else:
    hour = 0
dateOfFold = datetime(currentDate.year, currentDate.month, currentDate.day, hour)

fileCounter = 139
while True:
    try:
        with open('ban' + str(fileCounter)+'.csv', newline='', encoding="utf8") as myFile:
            fileCounter += 1
    except FileNotFoundError:
        break
outputFilename = 'ban' + str(fileCounter) + '.csv'


chunkSize = 10
chunks = [listOfFolders[x:x+chunkSize] for x in range(0, len(listOfFolders), chunkSize)]
masterList = []
timeList = [scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime]
scrapeErrorCount = 0
masterList.append(['username','payout','points','total_payout','total_points','total_wus','created_at'])

headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
print(str(len(chunks)) + " chunks generated")
print("Outputting to: " + outputFilename)
i = 1

BANsum = 0
for chunk in chunks:
    with FuturesSession() as session:
        futures = [session.get('https://bananominer.com/user_name/' + userName, headers=headers, timeout=20) for userName in chunk]
        for future in as_completed(futures):
            try:
                response = future.result()
                user = response.json()
                dateString = user['payments'][0]['created_at'][:-1]
                while len(dateString) < 26:
                    dateString += "0"
                payoutTime = datetime.fromisoformat(dateString)
                if payoutTime > dateOfFold:
                    total_payout = 0
                    for payout in user['payments']:
                        total_payout += payout['amount']
                    masterList.append([user['user']['id'],
                                      user['payments'][0]['amount'],
                                       user['payments'][0]['score'] - user['payments'][1]['score'],
                                       round(total_payout, 2),
                                       user['payments'][0]['score'],
                                       user['payments'][0]['work_units'],
									   user['user']['created_at']
                                       ])
                    print(user['user']['id'] + ": Folded " + str(user['payments'][0]['score'] - user['payments'][1]['score']) +" points for " + str(user['payments'][0]['amount']) + " BAN")
                    BANsum += user['payments'][0]['amount']
                else:
                    print(user['user']['id'] + ": No payment found")
            except IndexError:
                pass
            except Exception as e:
                print(response, e)
                scrapeErrorCount += 1
    print("Finished Chunk " + str(i) + " of " + str(len(chunks)) + ". Payouts Found: " + str(len(masterList)) + ". BAN Distributed: " + str(round(BANsum, 2)))
    scrapeDuration = time.time() - timeList[i % 10]
    timeList[i % 10] = time.time()
    estimatedTimeRemaining = (scrapeDuration / 10) * (len(chunks) - i)
    totalDuration = time.time() - scrapeStartTime
    print("Time Elapsed: " + str(int(totalDuration // 60)) + "m" + str(int(totalDuration % 60)) + "s. Estimated Time Remaining: " + str(int(estimatedTimeRemaining // 60)) + "m" + str(int(estimatedTimeRemaining % 60)) + "s.")
    print("Scraping Errors So Far: " + str(scrapeErrorCount))
    i += 1
    time.sleep(0.3)
try:
    scrapeDuration = time.time() - scrapeStartTime
    print("Total Scrape Time: " + str(int(scrapeDuration//60)) + "m" + str(int(scrapeDuration % 60)) + "s")
except Exception as e:
    print(e)
    pass

print("Outputting folders to file " + outputFilename)
with open(outputFilename, 'w', newline='') as myFile:
    writer = csv.writer(myFile)
    for entry in masterList:
        writer.writerow(entry)
    myFile.close()
