from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import chromedriver_autoinstaller
import edgedriver_autoinstaller
import geckodriver_autoinstaller
import PySimpleGUI as sg
import pandas

# Creates GUI.
layout = [
    [sg.Text("Enter your first initial:", size=(50, 1))],
    [sg.InputText(key="-INITIAL-", size=(50, 2))],
    [sg.Text("Enter your last name:", size=(50, 1))],
    [sg.InputText(key="-SURNAME-", size=(50, 2))],
    [sg.Text("Enter your HorizonWebRef username:", size=(50, 1))],
    [sg.InputText(key="-HORIZON_USERNAME-", size=(50, 2))],
    [sg.Text("Enter your HorizonWebRef password:", size=(50, 1))],
    [sg.InputText(key="-HORIZON_PASSWORD-", size=(50, 2))],
    [sg.Text("Enter your REFSIX username:", size=(50, 1))],
    [sg.InputText(key="-REFSIX_USERNAME-", size=(50, 2))],
    [sg.Text("Enter your REFSIX password:", size=(50, 1))],
    [sg.InputText(key="-REFSIX_PASSWORD-", size=(50, 2))],
    [sg.Text("Select your browser:", size=(50, 1))],
    [sg.InputCombo(["Google Chrome", "Microsoft Edge", "Firefox"], key="-BROWSER-", size=(50, 2))],
    [sg.Submit(size=(50, 2))],
    [sg.Text(key="-OUTPUT-", size=(50, 1))]
]

window = sg.Window("HorizonWebRef to Refsix", layout)

while True:
    event, values = window.read()
    if event == "Submit" or event == sg.WIN_CLOSED:
        window["-OUTPUT-"].update("Thank you. Opening " + values["-BROWSER-"] + ".")
        break

# Opens browser.
if values["-BROWSER-"] == "Google Chrome":
    chromedriver_autoinstaller.install()
    browser = webdriver.Chrome()
elif values["-BROWSER-"] == "Microsoft Edge":
    edgedriver_autoinstaller.install()
    browser = webdriver.Edge()
elif values["-BROWSER-"] == "Firefox":
    geckodriver_autoinstaller.install()
    browser = webdriver.Firefox()

browser.maximize_window()

# Opens and signs into HorizonWebRef site.
browser.get("https://www.horizonwebref.com/?pageID=login")
browser.find_element(By.ID, "username").send_keys(values["-HORIZON_USERNAME-"])
browser.find_element(By.ID, "password").send_keys(values["-HORIZON_PASSWORD-"])
browser.find_element(By.ID, "subBtn").click()

# Opens future appointments page.
WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.ID, "gameLink"))).click()
WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.LINK_TEXT, "Schedule Search & Filter"))).click()
table_id = browser.find_element(By.ID, "dateform").find_element(By.TAG_NAME, "table").get_attribute("id")
browser.find_element(By.ID, "menuDisplay"+table_id+"Item3").click()

# Creates DataFrame of schedule table.
content = browser.find_element(By.ID, "schedResults").get_attribute("outerHTML")
soup = BeautifulSoup(content, features="html.parser")
matches = pandas.read_html(str(soup))[0]

# Crops and reindexes DataFrame.
matches.columns = matches.iloc[0,:]
matches = matches.iloc[1:,:]
matches = matches.dropna(axis=1)
matches["Referee"] = ""
matches["Assistant1"] = ""
matches["Assistant2"] = ""
matches["Fourth"] = ""
matches["Observer"] = ""
matches["Role"] = ""

# Edits data in matches DataFrame.
for index in range(len(matches)):
    date = matches.iloc[index, 0]
    time = matches.iloc[index, 1]
    comp = matches.iloc[index, 2]
    home = matches.iloc[index, 3]
    away = matches.iloc[index, 4]
    fees = matches.iloc[index, 6]
    refs = matches.iloc[index, 7]
    # Dates become digits only.
    kodate = ""
    for char in date:
        if char.isdigit():
            kodate += char
    # Times become digits only.
    kotime = ""
    for char in time:
        if char.isdigit():
            kotime += char
    if len(kotime) == 3:
        kotime = "0" + kotime
    # Competition and team names lose prefixes and suffixes.
    comp = comp[5:]
    if "Vilic Law" in comp:
        comp = comp[10:]
        x = home.index("Capital")
        y = away.index("Capital")
    elif "Veto Mens" in comp:
        comp = comp[10:]
        x = home.index("Mens")
        y = away.index("Mens")
    elif "Veto" in comp:
        comp = comp[5:]
        x = home.index("Womens")
        y = away.index("Womens")
    elif "Elaine" in comp:
        comp = comp[:12]
        x = home.index("Elaine")
        y = away.index("Elaine")
    home = home[:x-1]
    away = away[:y-1]
    # Fees lose dollar sign.
    fees = fees[2:]
    # Referee names are separated and assigned.
    indices = []
    for pos, char in enumerate(refs):
        if char == ".":
            indices += [pos - 1]
    if len(indices) == 1:
        referee = refs
        assistant1 = ""
        assistant2 = ""
        fourth = ""
        observer = ""
    elif len(indices) == 2:
        referee = refs[:indices[1]]
        assistant1 = refs[indices[1]:]
        assistant2 = ""
        fourth = ""
        observer = ""
    elif len(indices) == 3:
        referee = refs[:indices[1]]
        assistant1 = refs[indices[1]:indices[2]]
        assistant2 = refs[indices[2]:]
        fourth = ""
        observer = ""
    elif len(indices) == 4:
        referee = refs[:indices[1]]
        assistant1 = refs[indices[1]:indices[2]]
        assistant2 = refs[indices[2]:indices[3]]
        fourth = refs[indices[3]:]
        observer = ""
    elif len(indices) == 5:
        referee = refs[:indices[1]]
        assistant1 = refs[indices[1]:indices[2]]
        assistant2 = refs[indices[2]:indices[3]]
        fourth = refs[indices[3]:indices[4]]
        observer = refs[indices[4]:]
    # Role is determined.
    name = values["-INITIAL-"] + ". " + values["-SURNAME-"]
    if referee == name:
        role = "referee"
    elif assistant1 == name:
        role = "assistant1"
    elif assistant2 == name:
        role = "assistant2"
    elif fourth == name:
        role = "fourth"
    elif observer == name:
        role = "observer"
    # Enters altered information into DataFrame.
    matches.iloc[index, 0] = kodate
    matches.iloc[index, 1] = kotime
    matches.iloc[index, 2] = comp
    matches.iloc[index, 3] = home
    matches.iloc[index, 4] = away
    matches.iloc[index, 6] = fees
    matches.iloc[index, 7] = referee
    matches.iloc[index, 8] = assistant1
    matches.iloc[index, 9] = assistant2
    matches.iloc[index, 10] = fourth
    matches.iloc[index, 11] = observer
    matches.iloc[index, 12] = role

# Opens and signs into REFSIX page.
browser.get("https://my.refsix.com/#/login")
browser.implicitly_wait(5)
browser.find_element(By.XPATH, "//input[@type='text']").send_keys(values["-REFSIX_USERNAME-"])
browser.find_element(By.XPATH, "//input[@type='password']").send_keys(values["-REFSIX_PASSWORD-"])
browser.find_element(By.TAG_NAME, "button").click()

# Create new match for each row of DataFrame.
for index in range(len(matches)):
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@href='#/ref/fixture/new']"))).click()
    browser.find_element(By.XPATH, "//input[@name='competition']").send_keys(matches.iloc[index, 2])
    browser.find_element(By.XPATH, "//input[@name='venue']").send_keys(matches.iloc[index, 5])
    browser.find_element(By.XPATH, "//input[@name='fixtureDate']").send_keys(matches.iloc[index, 0] + Keys.ARROW_RIGHT + matches.iloc[index, 1] + "p")
    if matches.iloc[index, 12] == "referee":
        browser.find_element(By.XPATH, "//option[@value='referee']").click()
    elif matches.iloc[index, 12] in ["assistant1", "assistant2"]:
        browser.find_element(By.XPATH, "//option[@value='assistant']").click()
    elif matches.iloc[index, 12] == "fourth":
        browser.find_element(By.XPATH, "//option[@value='fourthOfficial']").click()
    elif matches.iloc[index, 12] == "observer":
        browser.find_element(By.XPATH, "//option[@value='observer']").click()
    browser.find_element(By.XPATH, "//input[@name='homeTeam']").send_keys(matches.iloc[index, 3])
    browser.find_element(By.XPATH, "//input[@name='awayTeam']").send_keys(matches.iloc[index, 4])
    earning_form = browser.find_element(By.XPATH, "//div[@name='earningsForm']")
    browser.execute_script("arguments[0].setAttribute('class','form2-section ng-pristine ng-valid open')", earning_form)
    fees_form = browser.find_element(By.XPATH, "//input[@name='fees']")
    browser.execute_script("arguments[0].scrollIntoView();", fees_form)
    fees_form.send_keys(matches.iloc[index, 6])
    referees_form = browser.find_element(By.XPATH, "//div[@name='matchOfficialsForm']")
    browser.execute_script("arguments[0].setAttribute('class','form2-section ng-pristine ng-valid open')", referees_form)
    # If not referee, enter referee.
    if matches.iloc[index, 12] != "referee":
        browser.find_element(By.XPATH, "//input[@name='matchOfficialsreferee']").send_keys(matches.iloc[index, 7])
    # If not an assistant, enter both.
    if matches.iloc[index, 12] not in ["assistant1", "assistant2"]:
        browser.find_element(By.XPATH, "//input[@name='matchOfficialsassistant1']").send_keys(matches.iloc[index, 8])
        browser.find_element(By.XPATH, "//input[@name='matchOfficialsassistant2']").send_keys(matches.iloc[index, 9])
    # If assistant 1, enter assistant 2.
    elif matches.iloc[index, 12] == "assistant1":
        browser.find_element(By.XPATH, "//input[@name='matchOfficialsassistant2']").send_keys(matches.iloc[index, 9])
    # If assistant 2, enter assistant 1 as assistant 2 in form.
    elif matches.iloc[index, 12] == "assistant2":
        browser.find_element(By.XPATH, "//input[@name='matchOfficialsassistant2']").send_keys(matches.iloc[index, 8])
    # If not fourth, enter fourth.
    if matches.iloc[index, 12] != "fourth":
        browser.find_element(By.XPATH, "//input[@name='matchOfficialsfourthOfficial']").send_keys(matches.iloc[index, 10])
    # If not observer, enter observer.
    if matches.iloc[index, 12] != "observer":
        browser.find_element(By.XPATH, "//input[@name='matchOfficialsobserver']").send_keys(matches.iloc[index, 11])
    browser.find_element(By.XPATH, "//span[@class='primary-buttons']/button").click()
    browser.find_element(By.CLASS_NAME, "header-left").click()

# Add message to confirm completion and display button to close application.
while True:
    event, values = window.read()
    if event == "CLOSE" or event == sg.WIN_CLOSED:
        break

browser.quit()
window.close()
