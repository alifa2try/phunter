#!/usr/bin/env python3

# This program crawls websites


# import modules
import requests
import re
import urllib.parse
import argparse
from colorama import Fore, init, Style
import xlsxwriter

init()

from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

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
  		v1.0
Phone number Hunter
Harvest phone numbers in Nigerian format from all the pages of a target website
By Faisal Gama

Contact: info@faisalgama.com
Github: github.com/alifa2try/phunter
Website: faisalgama.com 

	'''
	print(f"{Green}{Style}{banner_text}{White}")


def get_argument():
	parser = argparse.ArgumentParser(description=display_banner())
	parser.add_argument("domain", help="Domain to search phone numbers from")
	option = parser.parse_args()

	if not option.domain:
		parser.error("[-] You need to specify a domain to search phone numbers from")

	return option.domain	


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

	try:
			href_links = extract_links_from_url(url)

			for link in href_links:
				
				link = urllib.parse.urljoin(url, link)

				
				if target_url in link and link not in target_links:
					target_links.append(link)
					
					phones = extract_phone(link)
					
					for phone in phones:

						if phone not in phone_list:
							phone_list.append(phone)
							print(f"{White}[+] Found a number: {phone}{Reset}")	
							global phones_counter
							phones_counter += 1
					crawl(link)	
	except TypeError:
		pass 

	export_results(phone_list)					


def export_results(phones):
	global xlsx_file_name
	global export_phones_list
	global domain

	csv_sheet_header = "Phone numbers found on " + domain
	
	for phone in phones:
		if phone not in export_phones_list:
			export_phones_list.append(phone)


	# Start from the first cell. Rows and columns are zero indexed.
	row = 0
	col = 0
	i = 0
	try:
		if len(export_phones_list) != 0:
			workbook = xlsxwriter.Workbook(xlsx_file_name)
			worksheet = workbook.add_worksheet()
			worksheet.write(row, col, csv_sheet_header)
			row += 1
			# Iterate over the data and write it out row by row.
			for phone in export_phones_list:
					col = 0
					worksheet.write(row, col, phone)
					row += 1
					i += 1

			#Close the excel
			workbook.close()

	except Exception as e:
		print(f"{Red}[-]Error in export_results {e}{Reset}")


try:
	target_links = []
	phone_list = []
	export_phones_list = []
	phones_counter = 0

	domain = get_argument()
	xlsx_file_name = domain + ".xlsx"
	target_url = "https://" + domain
	crawl(target_url)
	print(f"\n{Green}[+] Finished hunting down phone numbers and now exiting ...{Reset}")
	print(f"\n{Green}[+] A total of {phones_counter} numbers were hunted down.{Reset}")
except KeyboardInterrupt:
	print(f"\n{Blue}[+] Detected CTRL + C .... Now halting the program{Reset}")
	print(f"\n{Green}[+] A total of {phones_counter} numbers were hunted down.{Reset}")				
