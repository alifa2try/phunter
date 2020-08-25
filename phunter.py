#!/usr/bin/env python3

# This program crawls websites to gather number and perform OSINT on the numbers using Google. Can also accept single number or list of numbers

try:
	# import modules
	import requests
	import re
	import urllib.parse
	import argparse
	from colorama import Fore, init, Style
	import xlsxwriter
	import sys
	from phonenumbers import carrier
	from phonenumbers import geocoder
	from phonenumbers import timezone
	import phonenumbers
	import json
except KeyboardInterrupt:
    print('[!] Detected CTRL + C ...Now exiting!')
    raise SystemExit
except:
    print('[!] Missing requirements. Try running python3 -m pip install -r requirements.txt')
    raise SystemExit

init() # what is this doing?

# what is this doing?
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# initialize colorama colors
Yellow = Fore.LIGHTYELLOW_EX
Reset = Fore.RESET
Red = Fore.RED
Green = Fore.LIGHTGREEN_EX
Blue = Fore.BLUE
White = Fore.LIGHTWHITE_EX
Style = Style.BRIGHT


def display_banner():
	
	banner_text = '''
   _______    __    __   ____  ____  _____  ___  ___________  _______   _______   
  |   __ "\  /" |  | "\ ("  _||_ " |(\"   \|"  \("     _   ")/"     "| /"      \  
  (. |__) :)(:  (__)  :)|   (  ) : ||.\\   \    |)__/  \\__/(: ______)|:        | 
  |:  ____/  \/      \/ (:  |  | . )|: \.   \\  |   \\_ /    \/    |  |_____/   ) 
  (|  /      //  __  \\  \\ \__/ // |.  \    \. |   |.  |    // ___)_  //      /  
 /|__/ \    (:  (  )  :) /\\ __ //\ |    \    \ |   \:  |   (:      "||:  __   \  
(_______)    \__|  |__/ (__________) \___|\____\)    \__|    \_______)|__|  \___) 
  		v2.0.0
Phone Number Gathering & OSINT Tool
Collects Phone Numbers and Performs OSINT on the Numbers
By Faisal Gama

Contact: info@faisalgama.com
Github: github.com/alifa2try/phunter
Website: faisalgama.com 

	'''
	print(f"{Green}{Style}{banner_text}{White}")


def get_argument():
	parser = argparse.ArgumentParser(description=display_banner())
	parser.add_argument("-d", "--domain", dest='domain', help="Domain to search phone numbers from")
	parser.add_argument("-sn", "--single-number", dest='number', help="Single number to perform OSINT")
	parser.add_argument("-iL", "--input-list", dest='list', help="Input numbers from a list")
	parser.add_argument("-vs", "--verification-service", dest='verification_service', help="Verification service to use for the number (numverify|local)")

	option = parser.parse_args()

	if not option.domain:
		if not option.number:
			if not option.list:
				parser.error(f"{Red}[-] You need to specify a domain, input a single number or input numbers from a list{Reset}")
				raise SystemExit
	
	if not option.verification_service:
		parser.error(f"{Red}[-] You need to specify a verification service")
		raise SystemExit	
	return option	


def extract_links_from_url(url):
	try:
		response = requests.get(url, verify=False)
		return re.findall('(?:href=")(.*?)"', (response.content).decode())
	except UnicodeDecodeError:
		pass	


def extract_phone(url):
	reg1 = re.compile(r'080\d\d\d\d\d\d\d\d')
	reg2 = re.compile(r'080\d\s\d\d\d\s\d\d\d\d')
	reg3 = re.compile(r'\+23480\d\d\d\d\d\d\d\d')
	reg4 = re.compile(r'\+234\s80\d\s\d\d\d\s\d\d\d\d')

	reg_list = [reg1, reg2, reg3, reg4]

	try:	
		response = requests.get(url, verify=False)
		
		matches = []

		for reg in reg_list:
			matches += re.findall(reg, (response.content).decode())  

		return matches
	except UnicodeDecodeError: #r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.com"
		pass

def crawl(url):
	global target_links
	global phone_list
	global verification


	try:
			href_links = extract_links_from_url(url)

			for link in href_links:
				
				link = urllib.parse.urljoin(url, link)

				
				if target_url in link and link not in target_links:
					target_links.append(link)
					
					phones = extract_phone(link)
					
					for phone in phones:

						if not '+234' in phone and not '234' in phone:
							phone = '+234' + phone

						if phone not in phone_list:
							phone_list.append(phone)
							print(f"{Green}[+] Found a number: {phone} on page >> {link}{Reset}")	
							
							if verification == 'numverify':	
								print(f"{White}[+] Next verifying >> {phone} with numverify API{Reset}\n\n")	
								numverify(phone)
							elif verification == 'local':
								print(f"{White}[+] Next verifying >> {phone} with local verification{Reset}\n\n")	
								localverify(phone)
							print(f"{White}[+] Now searching Google for >> {phone}{Reset}\n\n")
							serp_stack(phone)
							global phones_counter
							phones_counter += 1
					crawl(link)	
	except TypeError:
		pass 

	generate_csv_report(phone_list)					


def serp_stack(phone):
	
	global SERPSTACK_key

	access_key = SERPSTACK_key
	
	params = {
	  'access_key': access_key,
	  'query': phone
	}

	api_result = requests.get('http://api.serpstack.com/search', params)

	api_response = api_result.json()

	print("Total results from Google search: ", api_response['search_information']['total_results'])

	for number, result in enumerate(api_response['organic_results'], start=1):
	    print("%s. Found on Page Titled >> %s" % (number, result['title']))
	    print("Page URL >> %s\n\n" % (result['url']))


def generate_csv_report(phones):
	global xlsx_file_name
	global export_phones_list
	global domain
	global workbook
	global report_worksheet

	#csv_sheet_header = "REPORT FOR NUMBERS FOUND ON " + domain.upper()
	
	for phone in phones:
		if phone not in export_phones_list:
			export_phones_list.append(phone)


	# Start from the first cell. Rows and columns are zero indexed.
	row = 1
	col = 0
	i = 0
	try:
		if len(export_phones_list) != 0:
			
			row += 1
			# Iterate over the data and write it out row by row.
			for phone in export_phones_list:
					col = 0
					report_worksheet.write(row, col, phone)
					row += 1
					i += 1

			#Close the excel
			workbook.close()

	except Exception as e:
		print(f"{Red}[-]Error in export_results {e}{Reset}")


def numverify(number):
	
	global NUMVERIFY_key

	access_key = NUMVERIFY_key
	url = 'http://apilayer.net/api/validate?access_key=' + access_key + '&number=' + number
	response = requests.get(url)

	answer = response.json()

	try:
		if answer["valid"] == True:
		    print("[+] Number Verification Results >>")
		    print(f"\n\nNumber: {answer['number']}")
		    print("International format:",answer["international_format"])
		    print("Country prefix:",answer["country_prefix"])
		    print("Country name:",answer["country_name"])
		    print("Location:",answer["location"])
		    print("Carrier:",answer["carrier"])
		    print(f"Line type: {answer['line_type']} \n\n")
		elif answer["valid"] == False:
		    print("\n\n[+] Not a valid number")
	except KeyError:
		print(answer)		    


def localverify(number):
	
	PhoneNumberObject = phonenumbers.parse(number, None)
    
	if not phonenumbers.is_valid_number(PhoneNumberObject):
		print("[-] Invalid phone number!")
	else:    
		number = phonenumbers.format_number(PhoneNumberObject, phonenumbers.PhoneNumberFormat.E164).replace('+', '')
		numberCountryCode = phonenumbers.format_number(PhoneNumberObject, phonenumbers.PhoneNumberFormat.INTERNATIONAL).split(' ')[0]
		countryRequest = json.loads(requests.request('GET', 'https://restcountries.eu/rest/v2/callingcode/{}'.format(numberCountryCode.replace('+', ''))).content)
		numberCountry = countryRequest[0]['alpha2Code']

		localNumber = phonenumbers.format_number(PhoneNumberObject, phonenumbers.PhoneNumberFormat.E164).replace(numberCountryCode, '')
		internationalNumber = phonenumbers.format_number(PhoneNumberObject, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

		print('International format: {}'.format(internationalNumber))
		print('Local format: 0{}'.format(localNumber))
		print('Country code: {}'.format(numberCountryCode))
		print('Location: {}'.format(geocoder.description_for_number(PhoneNumberObject, "en")))
		print('Carrier: {}'.format(carrier.name_for_number(PhoneNumberObject, 'en')))
		print('Area: {}'.format(geocoder.description_for_number(PhoneNumberObject, 'en')))
		for timezoneResult in timezone.time_zones_for_number(PhoneNumberObject):
			print('Timezone: {}'.format(timezoneResult))

		if phonenumbers.is_possible_number(PhoneNumberObject):
			print('The number is valid and possible.')
		else:
			print('The number is valid but might not be possible.')


# Program main body
try:
	target_links = []
	phone_list = []
	export_phones_list = []
	phones_counter = 0
	
	option = get_argument()
	verification = option.verification_service

	api_keys_file = open('key.txt', 'r')
	lines = api_keys_file.readlines()
	api_keys_file.close()

	SERPSTACK_key = lines[0].split(':')[1].split()
	NUMVERIFY_key = lines[1].split(':')[1].split()

	SERPSTACK_key = ''.join(SERPSTACK_key) # convert to a string
	NUMVERIFY_key = ''.join(NUMVERIFY_key) # convert to a string

	
	if option.domain:
		domain = option.domain
		xlsx_file_name = domain + ".xlsx"
		target_url = "https://" + domain
		
		csv_sheet_header = "REPORT FOR NUMBERS FOUND ON " + domain.upper()


		workbook = xlsxwriter.Workbook(xlsx_file_name)
		report_worksheet = workbook.add_worksheet('report')
		header_border = workbook.add_format({"bottom":6, "bottom_color":"#ff0000", "top":1, "top_color":"#ff0000" })
			
		
		report_worksheet.write(0, 5, csv_sheet_header)

		second_header_list = ['NUMBER', 'URL PAGE FOUND ON', 'NUMBER VERIFICATION RESULT', 'GOOGLE SEARCH RESULT']

		start_row = 1
		start_column = 0
		end_column = start_column + len(second_header_list)

		for column_index in range(start_column, end_column):
			report_worksheet.write(start_row, column_index, second_header_list[column_index - start_column], header_border)


		crawl(target_url)
		print(f"\n{Green}[+] Finished hunting down phone numbers and now exiting ...{Reset}")
		print(f"\n{Green}[+] A total of {phones_counter} numbers were hunted down.{Reset}")
	elif option.number:
		if option.verification_service == 'numverify':
			number = '+234' + option.number
			numverify(number)
			print("\n\n")
			serp_stack(option.number)
		elif option.verification_service == 'local':
			number = '+234' + option.number
			localverify(number)
			print("\n\n")
			serp_stack(option.number)	
	elif option.list:
		path = option.list
		file = open(path, 'r') 
		
		while True:

			line = file.readline()
			if not line:
				break
			number = line.strip()

			if option.verification_service == 'numverify':
				if not '234' in number:
					number = '+234' + str(number)
					numverify(number)
					print("\n\n")
					serp_stack(number)
					print("\n\n")
			elif option.verification_service == 'local':
				if not '234' in number:
					number = '+234' + str(number)
					localverify(number)
					print("\n\n")
					serp_stack(number)
					print("\n\n")
					
		file.close()	

except KeyboardInterrupt:
	print(f"\n{Blue}[+] Detected CTRL + C .... Now halting the program{Reset}")
	print(f"\n{Green}[+] A total of {phones_counter} numbers were hunted down.{Reset}")				
