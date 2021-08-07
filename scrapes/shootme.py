from datetime import datetime
import csv
import time
from concurrent.futures import as_completed
from requests_futures.sessions import FuturesSession
import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen
from bs4 import BeautifulSoup

listOfUsernames = []
userDict = {}

print("Obtaining F@H Team Stats...")
data = []
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
    data.append(sub_data)
dataFrame = pd.DataFrame(data = data, columns = list_header)
print("Done.")

currentDate = datetime.utcnow()
if currentDate.hour >= 12:
	hour = 12
	earlierOneFilename = 'convertcsvAM.csv'
	laterOneFilename = 'convertcsvPM.csv'
else:
	hour = 0
	earlierOneFilename = 'convertcsvPM.csv'
	laterOneFilename = 'convertcsvAM.csv'

print("Outputting stats to " + laterOneFilename)
dataFrame.to_csv(laterOneFilename, index = False)
print("Done.")
dateOfFold = datetime(currentDate.year, currentDate.month, currentDate.day, hour)

fileCounter = 9
while True:
	try:
		with open('ban' + str(fileCounter)+'.csv', newline='', encoding="utf8") as myFile:
			fileCounter += 1
	except FileNotFoundError:
		break

outputFilename = 'ban' + str(fileCounter) + '.csv'

with open(earlierOneFilename, newline='', encoding="utf8") as myFile:
    reader = csv.reader(myFile)
    for row in reader:
        try:
            userDict[row[2]] = int(row[3])
        except Exception as e:
            print(e)
            pass

with open(laterOneFilename, newline='', encoding="utf8") as myFile:
    reader = csv.reader(myFile)
    i = 0
    for row in reader:
        try:
            if row[2] not in userDict:
                listOfUsernames.append(row[2])
                print(len(listOfUsernames), i, "New Entry", row[2])
            elif int(row[3]) > userDict[row[2]]:
                listOfUsernames.append(row[2])
                print(len(listOfUsernames), i, "Folded", row[2])
        except Exception as e:
            print(e)
            pass
        i += 1

print("userList created. " + str(len(listOfUsernames)) + " entries.")
scrapeStartTime = time.time()

chunkSize = 10
chunks = [listOfUsernames[x:x+chunkSize] for x in range(0, len(listOfUsernames), chunkSize)]
masterList = []
masterList.append(['username','payout','points','total_payout','total_points','total_wus','created_at'])
timeList = [scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime, scrapeStartTime]
scrapeErrorCount = 0

headers = {"User-Agent": "Mozilla/5.0 (X11; CrOS x86_64 12871.102.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.141 Safari/537.36"}
print(str(len(chunks)) + " chunks generated")
print("Outputting to: " + outputFilename)
i = 1
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
                                       user['payments'][0]['work_units']
                                       ])
                    print(user['user']['id'] + ": Folded " + str(user['payments'][0]['score'] - user['payments'][1]['score']) +" points for " + str(user['payments'][0]['amount']) + " BAN")
                else:
                    print(user['user']['id'] + ": No payment found")
            except IndexError:
                pass
            except Exception as e:
                print(response, e)
                scrapeErrorCount += 1
    print("Finished Chunk " + str(i) + " of " + str(len(chunks)) + ". Payouts Found: " + str(len(masterList)))
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

import math

filename = outputFilename

def mainCurveEstimate2(points, price):
    if points >= 42449000:
        output = round((161.1375 + (0.0000693035 * points)), 2)
    elif points >= 10000000:
        output = ((1.4969 * math.pow(10, -12) * math.pow(points, 2)) + (
                    7.9561 * math.pow(10, -6) * points) + 93.1)
    elif points > 2998747:
        output = round((1 / (-0.05651 + (0.9603 * (1 / math.log(points)))) + 0.0361 - price), 2)
    elif points >= 300000:
        output = round(math.exp(-5.061 - math.log(price) + (0.4414 * math.log(points))), 2)
    elif points >= 150000:
        output = round(math.exp(-6.037 - math.log(price) + (0.5223 * math.log(points))), 2)
    elif points >= 30000:
        output = round(math.exp(-7.3263 - math.log(price) + (0.6380 * math.log(points))), 2)
    else:
        output = round(math.exp(-9.5797 - math.log(price) + (0.8545 * math.log(points))), 2)
    if output < 9.85:
        output = 9.85
    return output

def floorCurveEstimate2(points, price):
    output = round(math.exp(-10.24 + math.log(price) + (17.6 * math.log(math.log(math.log(points))))), 2)
    return output
# print(mainCurveEstimate2(90340, 0.0303366204481323))

def thirdCurveEstimate(points, price):
    output = round(math.exp(-15.8968 - math.log(price) + (17.6 * math.log(math.log(math.log(points))))), 2)
    if output < 9.85:
        output = 9.85
    return output

folders = 0
totalPayout = 0
totalPoints = 0
with open(filename, newline='', encoding="utf8") as myFile:
    reader = csv.reader(myFile)
    for row in reader:
        try:
            folders += 1
            totalPoints += int(row[2])
            totalPayout += round(float(row[1]), 2)
        except Exception as e:
            pass

print(folders, round(float(totalPayout), 2), totalPoints)

iterator = 0.0001
maxSuccess = 0
maxSuccessPrice = 0
downwardCount = 0
price = 0.0360
while True:
    abovecount = 0
    count1 = 0
    total = 0
    with open(filename, newline='', encoding="utf8") as myFile:
        reader = csv.reader(myFile)
        for row in reader:
            try:
                if abs(float(row[1]) - mainCurveEstimate2(float(row[2]), price)) < min(0.03 * float(row[1]), 6):
                    count1 += 1
                    pass
                elif abs(float(row[1]) - thirdCurveEstimate(float(row[2]), price)) < 0.03 * float(row[1]):
                    # count1 += 1
                    pass
                else:
                    pass
                if float(row[1])> floorCurveEstimate2(float(row[2]), price):
                    abovecount += 1
            except Exception as e:
                pass
            total += 1
    successRate = round(count1 * 100 / total, 2)
    print(round(price, 6), successRate, round(abovecount * 100 / total, 2))
    if successRate > maxSuccess:
        maxSuccessPrice = price
        maxSuccess = successRate
        price += 0.0001
    else:
        price += 0.0001
        downwardCount += 1
    if downwardCount > 20:
        break

print("Price Guess: ")
print(round(maxSuccessPrice, 4), maxSuccess)
