from flask import Flask, jsonify, Response, make_response, request
import requests
from bs4 import BeautifulSoup
import html
import uuid
import json
import re
import base64
from asgiref.wsgi import WsgiToAsgi
import pprint
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})
asgi_app = WsgiToAsgi(app)


@app.route('/healthz', methods=['GET'])
def health_check():
    return 'OK'
    
@app.route("/api/v1/professional/getCADetails", methods=["POST"])
def getCADetails():
    try:
        membershipNumber = request.json.get("membershipNumber")
        session = requests.Session()

        initialPostData = {
            "t1": membershipNumber
        }

        response = session.post(
            "http://112.133.194.254/lom.asp", data=initialPostData
        )

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')
        tables = soup.find_all('table')

        table = tables[3]
        trows = table.find_all('tr')
        if(trows==0):
            return jsonify({"status": "Chattered Accountant Not Found"})

        name = trows[1].find('b').get_text().strip().replace("          ", " ")
        gender = trows[2].find('b').get_text().strip()
        qualification = trows[3].find('b').get_text().strip()

        indianAddress = trows[4].find_all('b')[0].get_text().strip()
        foreignAddress = trows[4].find_all('b')[1].get_text().strip()
        indianAddress += " " + trows[5].find_all('b')[0].get_text().strip()
        foreignAddress += " " + trows[5].find_all('b')[1].get_text().strip()
        indianAddress += " " + trows[6].find_all('b')[0].get_text().strip()
        foreignAddress += " " + trows[6].find_all('b')[1].get_text().strip()
        indianAddress += " " + trows[7].find_all('b')[0].get_text().strip()
        foreignAddress += " " + trows[7].find_all('b')[1].get_text().strip()
        indianAddress += " " + trows[8].find_all('b')[0].get_text().strip()
        foreignAddress += " " + trows[8].find_all('b')[1].get_text().strip()
        indianAddress += " " + trows[9].find_all('b')[0].get_text().strip()
        foreignAddress += " " + trows[9].find_all('b')[1].get_text().strip()
        # indianAddress += " " + trows[10].find_all('b')[0].get_text()
        foreignAddress += " " + trows[10].find_all('b')[0].get_text().strip()

        copStatus = trows[11].find('b').get_text().strip()
        associateYear = trows[12].find('b').get_text().strip()
        fellowYear = trows[13].find_all('b')[0].get_text().strip()
        regionInIndia = trows[13].find_all('b')[1].get_text().strip()

        jsonResponse = {
            "membershipNumber":membershipNumber,
            "name": name,
            "gender": gender,
            "qualification": qualification,
            "indianAddress": indianAddress,
            "regionInIndia": regionInIndia,
            "foreignAddress": foreignAddress,
            "COPStatus": copStatus,
            "associateYear": associateYear,
            "fellowYear": fellowYear
        }
        # print(response.text)
        return jsonify(jsonResponse)
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Chatterred Accountant Details"})
    
@app.route("/api/v1/company/getCINdetails", methods=["POST"])
def getCINdetails():
    try:
        query = request.json.get("CIN")
        session = requests.Session()

        if(query==''):
            return jsonify({"error": "query cannot be empty"})

        params = {"q": query}

        response = session.get(
            "https://www.quickcompany.in/company/search/",
            params=params
        )

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        listDiv = soup.find('div', id="list_results")

        companyName = listDiv.find('h4').get_text()
        if "No Companies Found" in companyName:
            return jsonify({"error": companyName.replace('\"', '')})
        
        companyLink = listDiv.find('h4').find('a').get('href')

        try:
            buttons = listDiv.find_all('button')
            status = buttons[0].get_text()
            state = buttons[1].get_text()
        except Exception as e:
            if not status:
                status = ""
            if not state:
                state = ""

        response2 = session.get(f"https://www.quickcompany.in{companyLink}")
        
        htmlString = response2.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        directorsDiv = soup.find('div', id="directors")
        
        directorNamesHeading = directorsDiv.find_all('h5')
        designationSpan = directorsDiv.find_all('span')
        directors = []
        for i in range(len(directorNamesHeading)):
            directors.append(
                {
                    "name": directorNamesHeading[i].get_text(),
                    "designation": designationSpan[i].get_text()
                }
            )
        
        informationDiv = soup.find('div', id="information")
        tableRows = informationDiv.find_all('tr')

        data = {}

        for row in tableRows:
            key = row.find_all('td')[0].get_text()
            value = row.find_all('td')[1].get_text()
            data[key] = value
        
        CIN = data.get('CIN', '')
        RegNo = data.get('Registration Number', '')
        dateOfIncorporation = data.get('Date of Incorporation', '')
        RoC = data.get('RoC', '')
        companySubcategory = data.get('Company Sub-Category', '')
        listingStatus = data.get('Listing status', '')
        authorisedCapital = data.get('Authorised Capital', '')
        paidUpCapital = data.get('Paid Up Capital', '')
        dateOfLastAnnualGenMeet = data.get('Date of Last Annual General Meeting', '')
        dateOfLatestBalanceSheet = data.get('Date of Latest Balance Sheet', '')

        pastDirectorsDiv = soup.find('h4', id="past_directors").find_next_sibling('div')

        PdirectorNamesHeading = pastDirectorsDiv.find_all('h5')
        PdesignationSpan = pastDirectorsDiv.find_all('span')
        pastDirectors = []
        for i in range(len(PdirectorNamesHeading)):
            pastDirectors.append(
                {
                    "name": PdirectorNamesHeading[i].get_text(),
                    "designation": PdesignationSpan[i].get_text()
                }
            )

        CINdetail = {
            "companyName": companyName,
            "CIN": CIN,
            "status": status,
            "listingStatus": listingStatus,
            "state": state,
            "registrationNumber": RegNo,
            "Roc": RoC,
            "subCategory": companySubcategory,
            "capital": {
                "authorised": authorisedCapital,
                "paidUp": paidUpCapital
            },
            "dates": {
                "incorporation":dateOfIncorporation,
                "lastAnnualGeneralMeet": dateOfLastAnnualGenMeet,
                "latestBalanceSheet": dateOfLatestBalanceSheet
            },
            "directors": directors,
            "pastDirectors": pastDirectors
        }

        return jsonify(CINdetail)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching CIN Details"})

@app.route("/api/v1/company/getDINdetails", methods=["POST"])
def getDINdetails():
    try:
        DIN = request.json.get("DIN")
        session = requests.Session()

        postData = {
            "directorName": "",
            "din": DIN,
            "displayCaptcha": ""
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

        response = session.post(
            "https://www.mca.gov.in/mcafoportal/showdirectorMasterData.do", data=postData, headers=headers
        )

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')
        masterDiv = soup.find('div', id = 'dirMasterData')
        directorDataTable = masterDiv.find('table', id="directorData")

        din = directorDataTable.find_all('tr')[0].find_all('td')[1].get_text()
        name = directorDataTable.find_all('tr')[1].find_all('td')[1].get_text()

        companyDataTable = masterDiv.find('table', id="companyData")
        companies = []
        tableRows = companyDataTable.find_all('tr')
        
        for i in range(1,len(tableRows)):
            tableData = tableRows[i].find_all('td')
            if(len(tableData)==1):
                break
            CIN = tableData[0].get_text()
            compName = tableData[1].get_text()
            beginDate = tableData[2].get_text()
            endDate = tableData[3].get_text()
            activeCompliance = tableData[4].get_text()
            company = {
                "CIN": CIN,
                "name": compName,
                "beginDate": beginDate,
                "endDate": endDate,
                "activeCompliance": activeCompliance
            }
            companies.append(company)

        llpDataTable = masterDiv.find('table', id="llpData")
        listLLP = []
        tableRows1 = llpDataTable.find_all('tr')

        for i in range(1,len(tableRows1)):
            tableData = tableRows1[i].find_all('td')
            if(len(tableData)==1):
                break
            LLPIN = tableData[0].get_text()
            llpName = tableData[1].get_text()
            beginDate = tableData[2].get_text()
            endDate = tableData[3].get_text()

            llp = {
                "LLPIN": LLPIN,
                "name": llpName,
                "beginDate": beginDate,
                "endDate": endDate
            }
            listLLP.append(llp)   
        
        DINdetails = {
            "name": name,
            "DIN": din,
            "companies": companies,
            "llpList": listLLP
        }

        return jsonify(DINdetails)

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching DIN Details"})

@app.route("/api/v1/NID/get_UDID_details", methods=["POST"])
def get_UDID_details():
    try:
        url = "https://swavlambancard.gov.in/api/rest/trackapplication"
        UDID = request.json.get("UDID_Number")
        session = requests.Session()

        postBody = {
            "udid_number": UDID
        }

        response = session.post(url, json=postBody)

        return jsonify(response.json())
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching UDID Number Details"})
    
@app.route("/api/v1/professional/getDoctorDetails", methods=["POST"])
def getDoctorDetails():
    try:
        registrationNumber = request.json.get("registrationNumber")
        registrationDate = request.json.get("registrationDate")
        session = requests.Session()

        initialPostData = {
            "registrationNo": registrationNumber
        }

        response = session.post(
            "https://www.nmc.org.in/MCIRest/open/getDataFromService?service=searchDoctor",
            data = json.dumps(initialPostData)
        )

        doctors = response.json()

        doctorIndex = -1
        for i in range(len(doctors)):
            if(registrationDate == doctors[i]['regDate']):
                doctorIndex = i

        if(doctorIndex==-1):
            return jsonify({"status": "Doctor Not Found"})
        
        doctor = doctors[doctorIndex]
        
        jsonResponse = {
            "personal": {
                "doctorName": doctor['firstName'],
                "dateOfBirth": doctor['birthDateStr'],
                "fatherName": doctor['parentName'],
                "address": doctor['address'],
                "doctorId": doctor['doctorId']
            },
            "registrationNumber": doctor['registrationNo'],
            "registrationDate": doctor['regDate'],
            "stateMedicalCouncil": doctor['smcName'],
            "stateMedicalCouncilId": doctor['smcId'],
            "education": {
                "doctorDegree": doctor['doctorDegree'],
                "university": doctor['university'],
                "college": doctor['college'],
                "yearOfInfo": doctor['yearInfo'],
                "yearOfPassing": doctor['yearOfPassing']
            }
        }
        return jsonify(jsonResponse)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Doctor Details"})
    

@app.route("/api/v1/professional/getDentistDetails", methods=["POST"])
def getDentistDetails():
    try:
        name = request.json.get("name")
        regNo = request.json.get("registrationNumber")
        state = request.json.get("state")
        session = requests.Session()

        response1 = session.get(
            "https://dciindia.gov.in/DentistDetails.aspx"
        )

        soup = BeautifulSoup(response1.text, 'html.parser')
        
        __VIEWSTATE = soup.find('input', id='__VIEWSTATE').get('value')
        __VIEWSTATEGENERATOR = soup.find('input', id='__VIEWSTATEGENERATOR').get('value')
        __EVENTVALIDATION = soup.find('input', id='__EVENTVALIDATION').get('value')

        initialPostData = {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        "__VIEWSTATE":__VIEWSTATE,
        "__VIEWSTATEGENERATOR": __VIEWSTATEGENERATOR,
        "__EVENTVALIDATION": __EVENTVALIDATION,
            "ctl00$MainContent$txtName": name,
            "ctl00$MainContent$txtRegNo": regNo,
            "ctl00$MainContent$ddlSDC": state,
            "ctl00$MainContent$btnSearch": "Search"
        }

        response = session.post(
            "https://dciindia.gov.in/DentistDetails.aspx", data=initialPostData
        )

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')
        table = soup.find('table', class_='boxtxt')
        if(not table):
            return jsonify({"status": "Doctor Not Found"})

        doctorRow = table.find_all('tr')[1]

        doctorName = doctorRow.find_all('td')[1].get_text()
        registrationNumber = doctorRow.find_all('td')[2].get_text()
        dentalStateCouncil = doctorRow.find_all('td')[3].get_text()

        if(registrationNumber!=regNo):
            return jsonify({"status": "Doctor Not Found"})
        
        jsonResponse = {
            "registrationNumber": regNo,
            "doctorName": doctorName,
            "dentalStateCouncil": dentalStateCouncil
        }
        return jsonify(jsonResponse)
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Dentist Details"})


@app.route("/api/v1/professional/getNurseDetails", methods=["POST"])
def getNurseDetails():
    try:
        nuid = request.json.get("nurseId(nuid)")
        session = requests.Session()

        initialPostData = {
            "nuid": nuid
        }

        session.get(
            "https://nrts.indiannursingcouncil.gov.in/login.nic"
        )

        response = session.post(
            "https://nrts.indiannursingcouncil.gov.in/getvalidusername.nic?method=getvalidnuid_nuid", data=initialPostData
        )

        return jsonify(response.json())

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Nurse Details"})

@app.route("/api/v1/professional/check-email-validity", methods=["POST"])
def check_email_validity():
    try:
        url = "https://www.site24x7.com/tools/email-validator.html"
        post_url = "https://www.site24x7.com/tools/email-validator"
        
        email = request.json.get("email")
        session = requests.Session()
    
        postBody = {
            "emails": email
        }

        response = session.post(post_url, data=postBody)

        emailObject = response.json()

        failedDomain = None

        try:
            failedDomain = emailObject['failed_domains']
            failedDomain = True
        except:
            failedDomain = False
        
        domain = list(emailObject['domainMap'].keys())[0]
        
        if(not failedDomain):
            statusCode = emailObject['results'][domain][email]['status']

            status = ''
            if(statusCode==250):
                status = "Valid"
            else:
                status = "Invalid"
            
            reason = emailObject['results'][domain][email]['reason']
            
            jsonResponse = {
                "email": email,
                "domain": domain,
                "statusCode": statusCode,
                "status": status,
                "description": reason
            }
            print(jsonResponse)

            return jsonify(jsonResponse)
        else:
            jsonResponse = {
                "email": email,
                "domain": domain,
                "statusCode": 404,
                "status": "Invalid",
                "description": "Domain Not Found"
            }
            print(jsonResponse)

            return jsonify(jsonResponse)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in Checking email validity"})
    
@app.route("/api/v1/company/get_fssai_details", methods=["POST"])
def get_fssai_details():
    try:
        url = "https://foscos.fssai.gov.in/gateway/commonauth/commonapi/getsearchapplicationdetails/1"

        licenceNumber = request.json.get("licenceNumber")
        session = requests.Session()

        session.verify = False

        postBody = {
            "flrsLicenseNo": licenceNumber
        }

        response = session.post(url, json=postBody)

        return jsonify(response.json())
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching fssai licence Details"})
    
@app.route("/api/v1/professional/IFSC/getBanks", methods=["GET"])
def getBanks():
    try:
        url = "https://www.policybazaar.com/ifsc/"
        session = requests.Session()

        session.headers = {
            "authority": "www.policybazaar.com",
            "method": "GET",
            "path": "/ifsc/",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7",
            "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

        response = session.get(url)

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        bankOptions = soup.find('select', id="bank")
        options = bankOptions.find_all('option')

        bankValues = []
        for i in range(1,len(options)):
            bank = options[i].get('value')
            bankValues.append(bank)

        jsonResponse = {
            "banks": bankValues,
            "status": "Success"
        }

        return jsonify(jsonResponse)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Bank Names"})
    
@app.route("/api/v1/professional/IFSC/getStates", methods=["POST"])
def getStates():
    try:
        post_url = "https://www.policybazaar.com/templates/policybazaar/getifscval.php"
        bank = request.json.get("bank")
        session = requests.Session()

        session.headers = {
            "authority": "www.policybazaar.com",
            "method": "GET",
            "path": "/ifsc/",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7",
            "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.policybazaar.com/ifsc/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
         
        postData = {
            "task": "getstate",
            "bankname": bank
        }

        response = session.post(post_url, data=postData)

        return jsonify(response.json())

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching State Names which has this Bank"})
    
@app.route("/api/v1/professional/IFSC/getDistricts", methods=["POST"])
def getDistricts():
    try:
        post_url = "https://www.policybazaar.com/templates/policybazaar/getifscval.php"
        bank = request.json.get("bank")
        state = request.json.get("state")
        session = requests.Session()

        session.headers = {
            "authority": "www.policybazaar.com",
            "method": "GET",
            "path": "/ifsc/",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7",
            "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.policybazaar.com/ifsc/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
         
        postData = {
            "task": "getdistrict",
            "bankname": bank,
            "statename": state
        }

        response = session.post(post_url, data=postData)

        return jsonify(response.json())

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching districts of state chosen"})
    
@app.route("/api/v1/professional/IFSC/getBranches", methods=["POST"])
def getBranches():
    try:
        post_url = "https://www.policybazaar.com/templates/policybazaar/getifscval.php"
        bank = request.json.get("bank")
        state = request.json.get("state")
        district = request.json.get("district")
        session = requests.Session()

        session.headers = {
            "authority": "www.policybazaar.com",
            "method": "GET",
            "path": "/ifsc/",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7",
            "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.policybazaar.com/ifsc/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
         
        postData = {
            "task": "getbranch",
            "bankname": bank,
            "statename": state,
            "districtname": district
        }

        response = session.post(post_url, data=postData)

        return jsonify(response.json())

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching branches in the branches"})

@app.route("/api/v1/professional/IFSC/get_ifsc_code", methods=["POST"])
def get_ifsc_code():
    try:
        post_url = "https://www.policybazaar.com/templates/policybazaar/getifscval.php"
        bank = request.json.get("bank")
        state = request.json.get("state")
        district = request.json.get("district")
        branch = request.json.get('branch')
        session = requests.Session()

        session.headers = {
            "authority": "www.policybazaar.com",
            "method": "GET",
            "path": "/ifsc/",
            "scheme": "https",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7",
            "Cache-Control": "max-age=0",
            "Priority": "u=0, i",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Sec-Fetch-User": "?1",
            "Referer": "https://www.policybazaar.com/ifsc/",
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }
         
        postData = {
            "task": "getdetail",
            "bankname": bank,
            "statename": state,
            "districtname": district,
            "branchname": branch
        }

        response = session.post(post_url, data=postData)

        return jsonify(response.json())

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching IFSC Code. Please Retry Again"})
    
@app.route("/api/v1/professional/IFSC/getIFSCDetails", methods=["POST"])
def getIFSCDetails():
    try:
        IFSC = request.json.get("IFSC")
        session = requests.Session()

        response = session.get(
            f"https://ifsc.bankifsccode.com/{IFSC}"
        )

        cleaned_html_string = response.text.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '').replace('\"', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')
        mainDiv = soup.find_all('div', class_="text")
        if(len(mainDiv)==0):
            return jsonify({"status": "IFSC Code Not Found"})
        anchors = mainDiv[2].find_all('a')

        pattern = r'Address: (.*?)State:'
        match = re.search(pattern, mainDiv[2].get_text())
        address = match.group(1).strip()

        bank = anchors[0].get_text()
        state = anchors[1].get_text()
        district = anchors[2].get_text()
        branch = anchors[4].get_text()
        MICR = anchors[6].get_text()
        # print(mainDiv[2].get_text())

        jsonResponse = {
            "IFSC Code": IFSC,
            "bank": bank,
            "branch": branch,
            "MICR": MICR,
            "address": {
                "location": address,
                "district": district,
                "state": state
            },
            "branchCode": IFSC[-6:]
        }

        return jsonify(jsonResponse)

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching IFSC Code Details"})
    
@app.route("/api/v1/company/startup/getCertificate", methods=["POST"])
def getCertificate():
    try:
        url = "https://api.startupindia.gov.in/sih/api/noauth/dpiit/services/validate/certificate"
        
        dipp = request.json.get("dippNumber")  #DIPP141531
        certType = request.json.get("certificateType")
        session = requests.Session()

        session.headers = {
            'authority': 'api.startupindia.gov.in',
            'method': 'POST',
            'path': '/sih/api/noauth/dpiit/services/validate/certificate',
            'scheme': 'https',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9,hi-IN;q=0.8,hi;q=0.7',
            'Content-Length': '75',
            'Content-Type': 'application/json',
            'Origin': 'https://www.startupindia.gov.in',
            'Priority': 'u=1, i',
            'Referer': 'https://www.startupindia.gov.in/',
            'Sec-Ch-Ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
        }

        postBody = {
            "certificateType": certType,
            "dippNumber": dipp,
            "entityName": ""
        }

        response = session.post(url, json=postBody)

        pdfLink = "https://recognition-be.startupindia.gov.in" + response.json()['data']

        jsonResponse = {
            "status": "Successfull",
            "pdfLink": pdfLink
        }

        return jsonify(jsonResponse)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Certificate of Recognization"})

@app.route("/api/v1/NID/check-PAN-aadhaar-linkage", methods=["POST"])
def check_PAN_aadhaar_linkage():
    try:
        post_url = "https://eportal.incometax.gov.in/iec/servicesapi/getEntity"
        
        PAN = request.json.get("PAN")
        aadhaar = request.json.get("aadhaar")
        session = requests.Session()
    
        postBody = {
            "aadhaarNumber": aadhaar,
            "pan": PAN,
            "preLoginFlag": "Y",
            "serviceName": "linkAadhaarPreLoginService"
        }

        response = session.post(post_url, json=postBody)

        objectBody = response.json()

        # linkedAadhaarNumber = objectBody['aadhaarNumber']
        # errors = objectBody['errors']
        # isMigrated = objectBody['isMigrated']
        description = objectBody['messages'][0]['desc']
        print(description)

        withGivenAadhar = None
        withGivenPAN = None
        isPanExist = None
        isAadhaarValid = None
        isPanInactive = None

        if("valid 12 digit Aadhaar" in description):
            isAadhaarValid = False
            jsonResponse = {
                "isPanExist": "Unknown",
                "isAadhaarValid": isAadhaarValid,
                "linkedAadharNumber": "Unknown",
                "linkedPanNumber": "Unknown",
                "isPanLinkedToAdhaar": "Unknown",
                "description": description
            }
            return jsonify(jsonResponse)
        
        if("PAN entered is inactive"in description):
            isAadhaarValid = True
            jsonResponse = {
                "isPanExist": True,
                "isAadhaarValid": isAadhaarValid,
                "linkedAadharNumber": "Unknown",
                "linkedPanNumber": "Unknown",
                "isPanLinkedToAdhaar": False,
                "description": description
            }
            return jsonify(jsonResponse)
        
        if("enter valid Pan Card" in description):
            jsonResponse = {
                "isPanExist": False,
                "isAadhaarValid": "Unknown",
                "linkedAadharNumber": "Unknown",
                "linkedPanNumber": "Unknown",
                "isPanLinkedToAdhaar": "Unknown",
                "description": description
            }
            return jsonify(jsonResponse)
        if(("Your PAN" in description) and ("is already linked to given Aadhaar" in description)):
            jsonResponse = {
                "isPanExist": True,
                "isAadhaarValid": True,
                "linkedAadharNumber": objectBody['aadhaarNumber'],
                "linkedPanNumber": objectBody['pan'],
                "isPanLinkedToAdhaar": True,
                "description": description
            }
            return jsonify(jsonResponse)
        
        if(("Your PAN" in description) and ("is linked to some other Aadhaar" in description)):
            jsonResponse = {
                "isPanExist": True,
                "isAadhaarValid": True,
                "linkedAadharNumber": objectBody['aadhaarNumber'],
                "linkedPanNumber": objectBody['pan'],
                "isPanLinkedToAdhaar": True,
                "description": description
            }
            return jsonify(jsonResponse)
        
        if(("Your Aadhaar Number" in description) and ("is linked to some other PAN" in description)):
            jsonResponse = {
                "isPanExist": True,
                "isAadhaarValid": True,
                "linkedAadharNumber": objectBody['aadhaarNumber'],
                "linkedPanNumber": objectBody['pan'],
                "isPanLinkedToAdhaar": True,
                "description": description
            }
            return jsonify(jsonResponse)
        else:
            jsonResponse = {
                "isPanExist": "Unknown",
                "isAadhaarValid": "Unknown",
                "linkedAadharNumber": "Unknown",
                "linkedPanNumber": "Unknown",
                "isPanLinkedToAdhaar": False,
                "description": description
            }
            return jsonify(jsonResponse)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in Checking the linkage status of PAN and Aadhaar."})

rationSessions = {}

@app.route("/api/v1/NID/ration/getCaptcha", methods=["GET"])
def getCaptcha():
    try:
        baseUrl = "https://nfsa.gov.in/public/"

        session = requests.Session()
        id = str(uuid.uuid4())

        response = session.get("https://nfsa.gov.in/public/frmPublicGetMyRCDetails.aspx")

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')
        imageUrl = baseUrl + soup.find_all('div', class_="form-group")[2].find('img').get('src')

        # ONEKEY = "ctl00$ToolkitScriptManager2"
        # ONEPASS = "ctl00$ContentPlaceHolder1$Updatepanel3|ctl00$ContentPlaceHolder1$btnGetRCDetails"

        postData = {
            "_TSM_HiddenField_": soup.find('input', id="_TSM_HiddenField_").get('value'),
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": soup.find('input', id="__VIEWSTATE").get('value'),
            "__VIEWSTATEGENERATOR": soup.find('input', id="__VIEWSTATEGENERATOR").get('value'),
            "__VIEWSTATEENCRYPTED": soup.find('input', id="__VIEWSTATEENCRYPTED").get('value'),
            "__EVENTVALIDATION": soup.find('input', id="__EVENTVALIDATION").get('value'),
            "ctl00$ucLanguageList1$hdnState": "00",
            "ctl00$txtMainSearch": "",
            "ctl00$ContentPlaceHolder1$ddlSearchType": "R",
            "ctl00$ContentPlaceHolder1$hdnPortalLanguage": "1",
            "ctl00$ContentPlaceHolder1$hdnPortalState": "00",
            "ctl00$hdnMasterState": "00",
            "ctl00$hdnMasterLanguage": "en",
            "ctl00$hdnLoginTimeFromServer": soup.find('input', id="hdnLoginTimeFromServer").get('value'),
            "ctl00$hdnRandomNumberField": soup.find('input', id="hdnRandomNumberField").get('value'),
            "__ASYNCPOST": "false",
            "ctl00$ContentPlaceHolder1$btnGetRCDetails": "Get RC Details"
        }
        loginKeys = {
            "searchKey": "ctl00$ContentPlaceHolder1$txtSearchExpression",
            "captchaKey": "ctl00$ContentPlaceHolder1$txtCaptcha",
        }

        rationSessions[id] = {
            "session": session,
            "postData": postData,
            "loginKeys": loginKeys
        }
        response = session.get(imageUrl)
        captchaBase64 = base64.b64encode(response.content).decode("utf-8")

        # # For Testing Purpose only

        # imageString = f'<img src="data:image/png;base64,{captchaBase64}" alt="captcha">'
        # with open('captcha.html','w') as f:
        #     f.write(imageString)   
        #     f.close()

        # #

        jsonResponse = {
            "sessionId": id,
            "image": "data:image/png;base64," + captchaBase64,
        }

        return jsonify(jsonResponse)

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Captcha"})
    
@app.route("/api/v1/NID/ration/getRationCardDet", methods=["POST"])
def getRationCardDet():
    try:
        sessionId = request.json.get("sessionId")
        rcNo = request.json.get("rationCardNumber")
        captcha = request.json.get("captcha")

        user = rationSessions.get(sessionId)
        postData = user['postData']
        loginKeys = user['loginKeys']
        postData[loginKeys['searchKey']] = rcNo
        postData[loginKeys['captchaKey']] = captcha
        # print(postData)

        session = user['session']

        response = session.post(
            "https://nfsa.gov.in/public/frmPublicGetMyRCDetails.aspx",
            data=postData
        )
        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        labelError = soup.find('span', id="ContentPlaceHolder1_lblErrorMsg").get_text()
        captchaError = soup.find('span', id="ContentPlaceHolder1_lblCaptcha").get_text()
        if(labelError != ""):
            return jsonify({"error": labelError})
        if(captchaError != ""):
            return jsonify({"error": captchaError})

        dataList = soup.find('dl')

        dds = dataList.find_all('dd')

        rationCardNo = dds[0].get_text()
        scheme = dds[1].get_text()
        ONORC = dds[2].get_text()
        HOF = dds[3].get_text()
        address = dds[4].get_text()

        memberTable = soup.find('table')
        memberRows = memberTable.find('tbody').find_all('tr')

        numberOfMembers = len(memberRows)
        members = []

        for i in range(numberOfMembers):
            row = memberRows[i]
            memberId = row.find_all('td')[1].get_text()
            name = row.find_all('td')[2].get_text()
            relationWithHOF = row.find_all('td')[3].get_text()
            uidStatus = row.find_all('td')[4].get_text()

            members.append({
                "memberID": memberId,
                "memberName": name,
                "relationWithHOF": relationWithHOF,
                "uidStatus": uidStatus
            })
        
        jsonResponse = {
            "rationCardNumber": rationCardNo,
            "scheme": scheme,
            "isAllowedForONORC": ONORC,
            "headOfFamily": HOF,
            "address": address,
            "numberOfMembers": numberOfMembers,
            "members": members
        }

        return jsonify(jsonResponse)

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Ration Card Details. Please Retry Again"})
    
VCsessions = {}

@app.route("/api/v1/challan/VC/getCaptcha", methods=["POST"])
def getVCCaptcha():
    try:
        captcha = "https://vcourts.gov.in/virtualcourt/securimage/securimage_show.php"
        stateCode = request.json.get("stateCode")
        session = requests.Session()
        id = str(uuid.uuid4())

        idx = stateCode.find("~")
        v_token = stateCode[idx + 1:]

        initialPostData = {
            "x": "setStateCode",
            "state_code": stateCode,
            "vajax": "Y",
            "v_token": "",
        }

        response = session.post(
            "https://vcourts.gov.in/virtualcourt/indexajax.php", data=initialPostData
        )

        response = session.get(captcha)
        captchaBase64 = base64.b64encode(response.content).decode("utf-8")

        # # For Testing Purpose only

        # imageString = f'<img src="data:image/png;base64,{captchaBase64}" alt="captcha">'
        # with open('captcha.html','w') as f:
        #     f.write(imageString)   
        #     f.close()

        # #

        VCsessions[id] = {
            "session": session,
            "v_token": v_token
        }

        json_response = {
            "sessionId": id,
            "image": "data:image/png;base64," + captchaBase64,
        }

        return jsonify(json_response)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching captcha"})
    

@app.route("/api/v1/challan/VC/getChallanDetails", methods=["POST"])
def getVCChallanDetails():
    try:
        sessionId = request.json.get("sessionId")
        vehicleNo = request.json.get("vehicleNo")
        captcha = request.json.get("captcha")

        user = VCsessions.get(sessionId)

        session = user['session']
        if session is None:
            return jsonify({"error": "Invalid session id"})

        vehiclePostData = {
            "x": "fetchpolicecases",
            "challan_no": "",
            "vehicle_no": vehicleNo,
            "vajax": "Y",
            "v_token": user['v_token'],
            "fcaptcha_code": captcha,
        }

        responseAfterCapctha = session.post(
            "https://vcourts.gov.in/virtualcourt/admin/mobilesearchajax.php",
            data=vehiclePostData,
        )

        soup = BeautifulSoup(responseAfterCapctha.text, 'html.parser')

        viewBtns = soup.find_all('a', class_='viewDetlink')
        onclickTexts = [viewBtn.get('onclick') for viewBtn in viewBtns]

        challanFetchingData = []
        
        for i in range(len(onclickTexts)):
            pattern = re.compile(r"'(.*?)'")
            values = pattern.findall(onclickTexts[i])
            
            data = {
                "ciNo": values[0],
                "partyNo": values[1],
                "efilNo": values[2],
                "archieveFlag":values[3]
            }

            challanFetchingData.append(data)
        
        challans = []
        for i in range(len(challanFetchingData)):

            challanPostData = {
                "cino": challanFetchingData[i]['ciNo'],
                "party_no": challanFetchingData[i]['partyNo'],
                "efilno": challanFetchingData[i]['efilNo'],
                "archive_flag": challanFetchingData[i]['archieveFlag'],
                "vajax": "Y",
                "v_token": user['v_token']
            }
        
            responseAfterData = session.post(
                "https://vcourts.gov.in/virtualcourt/admin/case_history_partywise.php",
                data=challanPostData,
            )
            htmlString = responseAfterData.text
            cleaned_html_string = htmlString.replace('\\n', '').replace('\\r', '').replace('\\t', '').replace('\\', '')
            cleaned_html_string = html.unescape(cleaned_html_string)
            
            soup2 = BeautifulSoup(cleaned_html_string, 'html.parser')
            tables = soup2.find_all('table')

            index = 0
            if(len(tables)==3):
                index = 1
            
            partyDetailsTbody = tables[index].find_all('tbody')
            offenceTbody = tables[index+1].find_all('tbody')

            partyDetailsTrows = partyDetailsTbody[0].find_all('tr')
            statusDetailsTrows = partyDetailsTbody[1].find_all('tr')
            offenceTrows = offenceTbody[0].find_all('tr')
            offenceTdata = offenceTrows[0].find_all('td')

            challanNumber = partyDetailsTrows[3].find_all('td')[1].get_text()
            challanDate = partyDetailsTrows[4].find_all('td')[1].get_text()
            partyName = partyDetailsTrows[5].find_all('td')[1].get_text()
            placeOfOffence = partyDetailsTrows[6].find_all('td')[1].get_text()
            districtName = partyDetailsTrows[7].find_all('td')[1].get_text()

            recievedDate = statusDetailsTrows[0].find_all('td')[1].get_text()
            verifiedDate = statusDetailsTrows[1].find_all('td')[1].get_text()
            allocatedDate = statusDetailsTrows[2].find_all('td')[1].get_text()

            offenceCode = offenceTdata[0].get_text()
            offence = offenceTdata[1].get_text()
            act = offenceTdata[2].get_text()
            section = offenceTdata[3].get_text()
            fine = offenceTdata[4].get_text()

            challan = {
                "partyName": partyName,
                "challanNumber": challanNumber,
                "challanDate": challanDate,
                "amount": fine,
                "placeOfOffence": placeOfOffence,
                "district": districtName,
                "status": {
                    "recievedDate": recievedDate,
                    "verifiedDate": verifiedDate,
                    "allocatedDate": allocatedDate
                },
                "offenceDetails": {
                    "offenceCode":offenceCode,
                    "offence":offence,
                    "act": act,
                    "section": section
                }
            }
            challans.append(challan)

        
        return jsonify({"numberOfChallans":len(challans), "challans": challans})
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Challan Details"})
    
gstSessions = {}

@app.route("/api/v1/company/gst/getCaptcha", methods=["GET"])
def getGSTCaptcha():
    try:
        captcha = "https://services.gst.gov.in/services/captcha"
        session = requests.Session()
        id = str(uuid.uuid4())

        response = session.get(
            "https://services.gst.gov.in/services/searchtp"
        )

        captchaResponse = session.get(captcha)
        captchaBase64 = base64.b64encode(captchaResponse.content).decode("utf-8")

        # For Testing Purpose only

        # imageString = f'<img src="data:image/png;base64,{captchaBase64}" alt="captcha">'
        # with open('captcha.html','w') as f:
        #     f.write(imageString)   
        #     f.close()

        #

        gstSessions[id] = {
            "session": session
        }

        json_response = {
            "sessionId": id,
            "image": "data:image/png;base64," + captchaBase64,
        }

        return jsonify(json_response)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching captcha"})
    

@app.route("/api/v1/company/gst/getGSTDetails", methods=["POST"])
def getGSTDetails():
    try:
        sessionId = request.json.get("sessionId")
        GSTIN = request.json.get("GSTIN")
        captcha = request.json.get("captcha")

        user = gstSessions.get(sessionId)

        session = user['session']
        if session is None:
            return jsonify({"error": "Invalid session id"})

        gstData = {
            "gstin": GSTIN,
            "captcha": captcha,
        }

        response = session.post(
            "https://services.gst.gov.in/services/api/search/taxpayerDetails",
            json=gstData
        )

        return jsonify(response.json())
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching GST Details"})
    
schoolSessions = {}

searchKeys = {
    "udiseCode": "searchTypeOnSearchPage",
    "pinCode": "searchType",
    "name": ""
}

searchCodes = {
    "udiseCode": "2",
    "pinCode": "3",
    "name": "1"
}

@app.route("/api/v1/company/school/getCaptcha", methods=["GET"])
def getSchoolCaptcha():
    try:
        captcha_url = "https://src.udiseplus.gov.in/searchCaptcha"
        session = requests.Session()
        id = str(uuid.uuid4())

        response = session.get(captcha_url)
        captchaBase64 = base64.b64encode(response.content).decode("utf-8")

        # # For Testing Purpose only

        # imageString = f'<img src="data:image/png;base64,{captchaBase64}" alt="captcha">'
        # with open('captcha.html','w') as f:
        #     f.write(imageString)   
        #     f.close()

        # #

        schoolSessions[id] = {
            "session": session
        }

        json_response = {
            "sessionId": id,
            "image": "data:image/png;base64," + captchaBase64,
        }

        return jsonify(json_response)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching captcha"})
    

@app.route("/api/v1/company/school/getSchools", methods=["POST"])
def getSchools():
    try:
        post_url = "https://src.udiseplus.gov.in/searchSchool/byUdiseCodeAndSchoolOnSearchPage"
        
        sessionId = request.json.get("sessionId")
        query = request.json.get("query")
        searchBy = request.json.get("searchBy")
        captcha = request.json.get("captcha")

        user = schoolSessions.get(sessionId)

        session = user['session']
        if session is None:
            return jsonify({"error": "Invalid session id"})
        
        postData = {
            "searchTypeOnSearchPage": searchCodes[searchBy],
            "udiseCode": query,
            "selectDropDown": "",
            # "searchTypeOnSearchPage": "",
            "captcha": captcha
        }

        response = session.post(post_url, data=postData)

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        error = soup.find('div', id="invalidCaptchError").get_text().strip()

        if(error!=""):
            return jsonify({"error": "Invalid Captcha"})
        
        if("InValid Pin" in cleaned_html_string):
            return jsonify({"error": "Invalid PinCode"})
        
        if("InValid UDISE CODE" in cleaned_html_string):
            return jsonify({"error": "InValid UDISE CODE"})

        mainTable = soup.find('table', id="example")
        TRows = mainTable.find_all('tr')

        schools = []

        for i in range(1, len(TRows)):
            tds = TRows[i].find_all('td')

            UDISE_Code = tds[1].get_text().strip()
            schoolName = tds[2].get_text().strip()
            regionDetails = tds[3].get_text().strip().replace('District :', ' District :')
            basicDetails = tds[4].get_text().strip()

            pattern = re.compile(r"State Mgmt. :(.*?)NationalMgmt. :")
            stateMgmt = pattern.findall(basicDetails)[0].strip()
            
            pattern = re.compile(r"NationalMgmt. :(.*?)School Category :")
            nationalMgmt = pattern.findall(basicDetails)[0].strip()

            pattern = re.compile(r"School Category :(.*?)SchoolType :")
            schoolCategory = pattern.findall(basicDetails)[0].strip()

            pattern = re.compile(r"SchoolType :(.*?)PinCode :")
            schoolType = pattern.findall(basicDetails)[0].strip()

            pinCode = basicDetails[-6:]
            
            schoolStatus = tds[5].get_text().strip()

            schools.append({
                "udiseCode": UDISE_Code,
                "schoolName": schoolName,
                "regionDetails": regionDetails,
                "stateMgmt":stateMgmt,
                "nationalMgmt": nationalMgmt,
                "schoolCategory": schoolCategory,
                "schoolType": schoolType,
                "pinCode": pinCode,
                "schoolStatus": schoolStatus
            })

        data = {
            "numberOfSchools": len(TRows)-1,
            "schools": schools
        }
        
        return jsonify(data)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Schools"})
    
tinSessions = {}

@app.route("/api/v1/company/tin/getCaptcha", methods=["GET"])
def getTinCaptcha():
    try:
        captcha = "https://www.tinxsys.com/TinxsysInternetWeb/images/simpleCaptcha.jpg"
        session = requests.Session()
        id = str(uuid.uuid4())

        session.verify = False

        session.post("https://www.tinxsys.com/TinxsysInternetWeb/searchByTin_Inter.jsp",data={"backPage": "searchByTin_Inter.jsp"} )
        response = session.get(captcha)
        captchaBase64 = base64.b64encode(response.content).decode("utf-8")

        # # For Testing Purpose only

        # imageString = f'<img src="data:image/png;base64,{captchaBase64}" alt="captcha">'
        # with open('captcha.html','w') as f:
        #     f.write(imageString)   
        #     f.close()

        # #

        tinSessions[id] = {
            "session": session
        }

        json_response = {
            "sessionId": id,
            "image": "data:image/png;base64," + captchaBase64,
        }

        return jsonify(json_response)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching captcha"})
    

@app.route("/api/v1/company/tin/getTINdetails", methods=["POST"])
def getTINdetails():
    try:
        sessionId = request.json.get("sessionId")
        TIN = request.json.get("TIN")
        captcha = request.json.get("captcha")

        user = tinSessions.get(sessionId)

        session = user['session']
        if session is None:
            return jsonify({"error": "Invalid session id"})

        print(TIN)
        print(captcha)
        params = {
            "tinNumber": TIN,
            "answer": captcha,
            "searchBy": "TIN",
            "backPage": "searchByTin_Inter.jsp"
        }

        response = session.get(
            f"https://www.tinxsys.com/TinxsysInternetWeb/dealerControllerServlet?tinNumber={TIN}&answer={captcha}&searchBy=TIN&backPage=searchByTin_Inter.jsp"
        )
        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '').replace('\\u00a0', '').replace('\"', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        mainTable = soup.find_all('table')[2]

        tableRows = mainTable.find_all('tr')

        try:
            tin = tableRows[1].find_all('td')[1].get_text().strip()
            cstNo = tableRows[2].find_all('td')[1].get_text().strip()
            dealerName = tableRows[3].find_all('td')[1].get_text().strip()
            dealerAddress = tableRows[4].find_all('td')[1].get_text().strip().replace('                         ', ' ').replace('               ', '')
            state = tableRows[5].find_all('td')[1].get_text().strip()
            PAN = tableRows[6].find_all('td')[1].get_text().strip()
            dateOfReg = tableRows[7].find_all('td')[1].get_text().strip()
            regStatus = tableRows[8].find_all('td')[1].get_text().strip()
            validAsOn = tableRows[9].find_all('td')[1].get_text().strip()
        except:
            return jsonify({"error": "Invalid Details"})

        TINdetails = {
            "TIN": tin,
            "CSTNumber": cstNo,
            "PAN": PAN,
            "dealerName": dealerName,
            "dealerAddress": dealerAddress,
            "state": state,
            "dateOfRegistration": dateOfReg,
            "registrationStatus": regStatus,
            "validAsOn": validAsOn
        }
        
        return jsonify(TINdetails)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching TIN Details"})
    
udyamSessions = {}

@app.route("/api/v1/company/udyam/getCaptcha", methods=["GET"])
def getUdyamCaptcha():
    try:
        post_url = "https://udyamregistration.gov.in/Udyam_Verify.aspx"
        captcha_url = "https://udyamregistration.gov.in/Captcha/CaptchaControl.aspx"
        # udyamRegistrationNumber = request.json.get("udyamRegNo")
        session = requests.Session()
        id = str(uuid.uuid4())
        
        session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://udyamregistration.gov.in/Government-India/Ministry-MSME-registration.htm",
            "authority": "udyamregistration.gov.in"
        }

        response = session.get(post_url)

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        postData = {
            "ctl00$sm": "ctl00$ContentPlaceHolder1$UpdatePaneldd1|ctl00$ContentPlaceHolder1$btnVerify",
            "__EVENTTARGET": "",
            "__EVENTARGUMENT": "",
            "__VIEWSTATE": soup.find('input', id="__VIEWSTATE").get('value'),
            "__VIEWSTATEGENERATOR": soup.find('input', id="__VIEWSTATEGENERATOR").get('value'),
            "__VIEWSTATEENCRYPTED": soup.find('input', id="__VIEWSTATEENCRYPTED").get('value'),
            "__EVENTVALIDATION": soup.find('input', id="__EVENTVALIDATION").get('value'),
            "cmbMoreFunction": "0",
            "__ASYNCPOST": "false",
            "ctl00$ContentPlaceHolder1$btnVerify": "Verify",
        }
        loginKeys = {
            "searchKey": "ctl00$ContentPlaceHolder1$txtUdyamNo",
            "captchaKey": "ctl00$ContentPlaceHolder1$txtCaptcha",
        }

        udyamSessions[id] = {
            "session": session,
            "postData": postData,
            "loginKeys": loginKeys
        }

        captchaResponse = session.get(captcha_url)
        captchaBase64 = base64.b64encode(captchaResponse.content).decode("utf-8")

        # # For Testing Purpose only

        # imageString = f'<img src="data:image/png;base64,{captchaBase64}" alt="captcha">'
        # with open('captcha.html','w') as f:
        #     f.write(imageString)   
        #     f.close()

        # # 

        jsonResponse = {
            "sessionId": id,
            "image": "data:image/png;base64," + captchaBase64,
        }

        return jsonify(jsonResponse)
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching captcha"})
    
@app.route("/api/v1/company/udyam/getUdyamDetails", methods=["POST"])
def getUdyamDetails():
    try:
        post_url = "https://udyamregistration.gov.in/Udyam_Verify.aspx"
        url = "https://udyamregistration.gov.in/PrintUdyamApplication.aspx"
        
        sessionId = request.json.get("sessionId")
        udyamRegNo = request.json.get("udyamRegNo")
        captcha = request.json.get("captcha")

        user = udyamSessions.get(sessionId)
        postData = user['postData']
        loginKeys = user['loginKeys']
        postData[loginKeys['searchKey']] = udyamRegNo
        postData[loginKeys['captchaKey']] = captcha
        # print(postData)

        session = user['session']

        responseErr = session.post(
            post_url,
            data=postData
        )

        if("Udyam Registration Number does not exist" in responseErr.text):
            return jsonify({"error": "Udyam Registration Number does not exist"})
        if("Incorrect verification code. Please try again" in responseErr.text):
            return jsonify({"error": "Invalid Captcha"})

        response = session.get(url)

        htmlString = response.text
        cleaned_html_string = htmlString.replace('\n', '').replace('\r', '').replace('\t', '').replace('\\', '')
        cleaned_html_string = html.unescape(cleaned_html_string)

        soup = BeautifulSoup(cleaned_html_string, 'html.parser')

        allTables = soup.find_all('table')

        organizationTable = allTables[2]
        ORows = organizationTable.find_all('tr')

        nameOfEnterprise = ORows[0].find_all('td')[1].get_text().strip()
        organizationType = ORows[1].find_all('td')[1].get_text().strip()
        majorActivity = ORows[1].find_all('td')[3].get_text().strip()
        gender = ORows[2].find_all('td')[1].get_text().strip()
        category = ORows[2].find_all('td')[3].get_text().strip()
        dateOfIncorporation = ORows[3].find_all('td')[1].get_text().strip()
        dateOfCommencement = ORows[3].find_all('td')[3].get_text().strip()

        typeTable = allTables[3]
        TRows = typeTable.find_all('tr')

        enterpriseTypes = []
        for i in range(1,len(TRows)):
            td = TRows[i].find_all('td')

            dataYear = td[1].get_text().strip()
            classificationYear = td[2].get_text().strip()
            enterpriseType = td[3].get_text().strip()
            classificationDate = td[4].get_text().strip()

            enterpriseTypes.append({
                "dataYear": dataYear,
                "classificationDate": classificationDate,
                "classificationYear": classificationYear,
                "enterpriseType": enterpriseType
            })

        plantsTable = allTables[5]
        PRows = plantsTable.find_all('tr')

        plantsLocation = []
        for i in range(1,len(PRows)):
            td = PRows[i].find_all('td')

            unitName = td[1].get_text().strip()
            flat = td[2].get_text().strip()
            building = td[3].get_text().strip()
            town = td[4].get_text().strip()
            city = td[7].get_text().strip()
            pincode = td[8].get_text().strip()
            state = td[9].get_text().strip()
            district = td[10].get_text().strip()
            plantsLocation.append({
                "unitName": unitName,
                "flat": flat,
                "building": building,
                "town": town,
                "city": city,
                "pincode": pincode,
                "district": district,
                "state": state,
            })
        
        addressTable = allTables[7]
        ARows = addressTable.find_all('tr')
        officialAddress = {
            "addressLine1": ARows[0].find_all('td')[1].get_text() + ARows[0].find_all('td')[3].get_text()  + ARows[1].find_all('td')[1].get_text() + ARows[1].find_all('td')[3].get_text() + ARows[2].find_all('td')[1].get_text(),
            "district": ARows[3].find_all('td')[3].get_text().strip(),
            "state": ARows[3].find_all('td')[1].get_text().strip(),
        }

        mobile = ARows[4].find_all('td')[1].get_text().strip()
        email = ARows[4].find_all('td')[3].get_text().strip()

        dateOfRegistration = allTables[9].find_all('tr')[2].find_all('td')[1].get_text().strip()

        data = {
            "udyamRegNo": udyamRegNo,
            "nameOfEnterprise": nameOfEnterprise,
            "organizationType": organizationType,
            "majorActivity": majorActivity,
            "gender": gender,
            "socialCategory": category,
            "mobile": mobile,
            "email": email,
            "dateOfRegistration": dateOfRegistration,
            "officialAddress": officialAddress,
            "enterpriseTypes": enterpriseTypes,
            "dateOfCommencement": dateOfCommencement,
            "dateOfIncorporation": dateOfIncorporation,
            "plantsLocation": plantsLocation
        }

        return jsonify(data)

    except Exception as e:
        print(e)
        return jsonify({"error": "Error in fetching Udyam Registration Number Details"})
    
base_url = "https://parivahan.gov.in"

url = "https://parivahan.gov.in/rcdlstatus/?pur_cd=101"

post_url = "https://parivahan.gov.in/rcdlstatus/vahan/rcDlHome.xhtml"

dl_sessions = {}

def get_data_from_tables(soup):
    data = []
    tables = soup.find_all("table")
    
    for table in tables:
        table_data = {
            "headers": [],
            "data": [],
        }

        thead = table.find("thead")
        if thead is not None:
            ths = thead.find_all("th")
            headers = []
            for th in ths:
                headers.append(th.text)
            table_data["headers"] = headers

        trs = table.find_all("tr")

        for tr in trs:
            row_data = []
            tds = tr.find_all("td")
            for i in range(len(tds)):
                row_data.append(tds[i].text)
            table_data["data"].append(row_data)

        data.append(table_data)
    return data


class DL:
    
    def __init__(self):
        self.post_data = {
            "avax.faces.partial.ajax": "true",
            "javax.faces.partial.execute": "@all",
            "javax.faces.partial.render": "form_rcdl:pnl_show form_rcdl:pg_show form_rcdl:rcdl_pnl",
        }
        self.base_url = "https://parivahan.gov.in"
        self.captcha_url = None
        self.page = None
        self.soup = None
        self.id = str(uuid.uuid4())
        self.session = requests.Session()
        self.session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Content-Type": "application/x-www-form-urlencoded",
        }   

    def initialise(self):
        self.page = self.session.get(url)
        self.soup = BeautifulSoup(self.page.content, "html.parser")
        self.get_default_inputs()

    def get_captcha_url(self):
        # Get the table with class vahan-captcha
        captcha_table = self.soup.find("table", {"class": "vahan-captcha"})
        # Get the img tag
        img = captcha_table.find("img")
        # Get the src attribute
        src = img["src"]
        self.captcha_url = self.base_url + src
        return self.captcha_url

    def get_default_inputs(self):
        form = self.soup.find("form", id="form_rcdl")
        inputs = form.find_all("input")
        print(len(inputs))
        for i in inputs:
            name = ""
            value = ""
            if i.has_attr("name"):
                name = i["name"]
            if i.has_attr("value"):
                value = i["value"]
            if name != "" and value != "":
                self.post_data[name] = value

        buttons = form.find_all('button')
        submitBtnName = buttons[1].get('name')

        self.post_data[submitBtnName] = submitBtnName
        self.post_data['javax.faces.source'] = submitBtnName

        self.captchaInputName = inputs[3].get('name')


@app.route("/api/v1/NID/dl/getCaptcha", methods=["GET"])
def get_dl_captcha():
    try:
        dl = DL()
        dl.initialise()
        captchaSrc = dl.get_captcha_url()
        dl_sessions[dl.id] = dl
        return jsonify({"captcha": captchaSrc, "id": dl.id, "param": dl.post_data})
    
    except Exception as e:
        print(e)
        return jsonify({"error": "Error getting captcha"})


@app.route("/api/v1/NID/dl/get-vehicle-details", methods=["POST"])
def get_vehicle_details():
    try:
        data = request.json
        id = data["sessionId"]
        dl = dl_sessions[id]
        dl.post_data["form_rcdl:tf_dlNO"] = data["dlno"]
        date = data["dob"]
        print(date)

        # date comes in formay yyyy-mm-dd
        # we need to convert it to dd-mm-yyyy
        date = date.split("-")
        date = date[2] + "-" + date[1] + "-" + date[0]
        print(date)

        dl.post_data["form_rcdl:tf_dob_input"] = date
        dl.post_data[dl.captchaInputName] = data["captchaData"]
        response = dl.session.post(post_url, data=dl.post_data)

        soup = BeautifulSoup(response.content, "html.parser")

        # print(soup)

        error_messages = []
        try:
            # Find a div with class ui-messages-error-summary
            errors = soup.find_all("span", {"class": "ui-messages-error-summary"})
            # print(errors)
            for error in errors:
                if error.text:
                    error_messages.append(error.text)

        except:
            print("Error getting error messages")

        print(error_messages)

        if len(error_messages) > 0:
            return jsonify({"errors": error_messages})

        details = None
        try:
            # Find a div with id form_rcdl:pnl_show
            details = soup.find("div", {"id": "form_rcdl:pnl_show"})
        except:
            pass

        if details is None:
            return jsonify({"error": "Error getting vehicle details"})

        # print(str(details))
        del dl_sessions[id]
        return jsonify({"details": get_data_from_tables(details)})
    except Exception as e:
        print(e)
        # close session object
        del dl_sessions[id]

        return jsonify({"error": str(e)})
    
@app.route('/api/v1/NID/electoral/captcha')
def get_electoral_captcha():
    try:
        response = requests.get("https://gateway-voters.eci.gov.in/api/v1/captcha-service/generateCaptcha")
        return response.json()
    except Exception as e:
        print(e)
        return {"error": "Error in fetching captcha"}
    
@app.route("/api/v1/NID/electoral/electoral-search", methods=["post"])
def get_electoral_search():
    try:
        data = request.get_json()
        print(data)
        captcha_id = data.get("captchaId")
        epic_no = data.get("epicNumber")
        state_cd = data.get("stateCd")
        captcha_data = data.get("captchaData")
        post_data = {
            "isPortal": "true",
            "epicNumber": epic_no,
            "stateCd": state_cd,
            "captchaId": captcha_id,
            "captchaData": captcha_data,
            "securityKey": "na"
        }
        
        response = requests.post("https://gateway.eci.gov.in/api/v1/elastic/search-by-epic-from-national-display", json=post_data)
        return response.json()
    except Exception as e:
        print(e)
        return {"error": "Error in fetching electoral search"}
    

validate_url = "https://eportal.incometax.gov.in/iec/guestservicesapi/validateOTP/"

# proxy = {
#     "http": "184.168.124.233:5402",
#     "https": "184.168.124.233:5402",
# }

validate_payload = {
    "panNumber": "",
    "fullName": "",
    "dob": "1996-07-09",
    "mobNo": "",
    "areaCd": "91",
    "otp": "299346",
    "serviceName": "verifyYourPanService",
    "formName": "FO-009-VYPAN",
    "reqId": "FOS004478380700",
}


saveEntityPayload = {
    "panNumber": "ABCDEF1234A",
    "fullName": "ABCD XYZ",
    "dob": "1993-07-02",
    "mobNo": "9999999999",
    "areaCd": "91",
    "serviceName": "verifyYourPanService",
    "formName": "FO-009-VYPAN",
}


local_session = {}


def encode_base64(input_string):
    # Convert string to bytes
    byte_data = input_string.encode("utf-8")
    # Encode bytes to Base64
    base64_encoded = base64.b64encode(byte_data)
    # Convert Base64 bytes back to string
    return base64_encoded.decode("utf-8")


@app.route("/api/v1/NID/pan/validateOTP", methods=["POST"])
def validateOTP():
    session = requests.Session()
    post_url = "https://eportal.incometax.gov.in/iec/guestservicesapi/validateOTP/"
    data = request.get_json()
    try:
        otp = data["otp"]
        reqId = data["reqId"]
        saved_response = local_session[reqId]
        saved_response["otp"] = otp
        response = session.post(post_url, json=saved_response)
        return response.json()
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/api/v1/NID/pan/saveEntity", methods=["post"])
def saveEntity():
    session = requests.Session()
    post_url = "https://eportal.incometax.gov.in/iec/guestservicesapi/saveEntity/"
    request_data = request.get_json()
    request_data["fullName"] = encode_base64(request_data["fullName"])
    try:
        # If using proxy:
        # response = session.post(post_url, json=request_data, proxies=proxy)
        # If not using proxy:
        response = session.post(post_url, json=request_data)
        response_data = response.json()
        pprint.pprint(response_data)
        # Check if reqId is present in response
        if "reqId" not in response_data:
            # Look for error message
            if "messages" in response_data:
                # loop through messages
                for message in response_data["messages"]:
                    # Check if message is of type error
                    if message["type"] == "ERROR":
                        return jsonify({"error": message["desc"]})
            return jsonify({"error": "Something went wrong"})
        reqId = response_data["reqId"]
        request_data["reqId"] = reqId
        local_session[reqId] = request_data
        return response_data
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(asgi_app, host='0.0.0.0', port=5001)