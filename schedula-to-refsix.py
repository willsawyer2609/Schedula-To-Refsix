# TODO: Update string for Fourth Official role.
# TODO: Add Canale Cup and Mens and Womens City Cup match fees.
# TODO: Distinguish between Fourth Official and Assessor.

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
import geckodriver_autoinstaller
import edgedriver_autoinstaller
from selenium import webdriver
from bs4 import BeautifulSoup
import PySimpleGUI as sg
import pandas as pd


def TextElem(text):
    return [sg.Text(text, size=(40, 1))]


def InputElem(key):
    return [sg.InputText(key=key, size=(50, 2))]


def open_form(form_element, browser):
    browser.execute_script("arguments[0].setAttribute('class',"
                           "'form2-section ng-pristine ng-valid open')",
                           form_element)
    return


sg.theme("DarkGrey11")
browsers = ["Google Chrome", "Microsoft Edge", "Firefox"]
layout = [
    TextElem("Enter your Schedula email:"),
    InputElem("schedula-email"),
    TextElem("Enter your Schedula password:"),
    InputElem("schedula-password"),
    TextElem("Enter your REFSIX username:"),
    InputElem("refsix-username"),
    TextElem("Enter your REFSIX password:"),
    InputElem("refsix-password"),
    TextElem("Select your browser:"),
    [sg.InputCombo(browsers, key="browser", size=(48, len(browsers)))],
    [sg.Submit(size=(44, 1))],
]
window = sg.Window("Schedula to Refsix", layout)

while True:
    event, values = window.read()
    if event in ("Submit", sg.WIN_CLOSED):
        window.close()
        break

if values["browser"] == "Google Chrome":
    chromedriver_autoinstaller.install()
    browser = webdriver.Chrome()
elif values["browser"] == "Microsoft Edge":
    edgedriver_autoinstaller.install()
    browser = webdriver.Edge()
elif values["browser"] == "Firefox":
    geckodriver_autoinstaller.install()
    browser = webdriver.Firefox()
browser.maximize_window()

browser.get("https://schedula.sportstg.com/")
schedula_email = browser.find_element_by_xpath("//input[@name='email']")
schedula_email.send_keys(values["schedula-email"])
schedula_password = browser.find_element_by_xpath("//input[@name='password']")
schedula_password.send_keys(values["schedula-password"])
schedula_submit = browser.find_element_by_xpath("//input[@name='btnlogin']")
schedula_submit.click()

browser.implicitly_wait(5)
table = browser.find_element_by_tag_name("table")
content = table.get_attribute("outerHTML")
soup = BeautifulSoup(content, features="html.parser")

matches = pd.read_html(str(soup))[0]
matches = matches.iloc[:, :6]
matches.columns = ["Competition", "Role", "Date", "Time", "Teams", "Venue"]
matches["Home"] = ""
matches["Away"] = ""
matches["Fees"] = ""
matches["Referee"] = ""
matches["Assistant1"] = ""
matches["Assistant2"] = ""
matches["Fourth"] = ""
matches["Assessor"] = ""

fees = pd.read_csv("fees.csv")
fees = fees.set_index(fees["Competition"])
fees = fees.iloc[:, 1:]

for index in range(len(matches)):
    comp = matches.iloc[index, 0]
    role = matches.iloc[index, 1]
    date = matches.iloc[index, 2]
    time = matches.iloc[index, 3]
    home, away = matches.iloc[index, 4].split(" v ")

    # Dates and times are optimised for REFSIX input.
    time = time.replace(" ", "")
    date = date[:-2] + "20" + date[-2:]
    date = date.zfill(10)

    # Competition and team names lose prefixes and suffixes.
    comp = comp[3:]
    if "Business Plaza" in comp:
        comp = comp[15:]
        x = home.index("Bpl")
        y = away.index("Bpl")
    elif "Canale Cup" in comp:
        comp = comp[11:]
        x = home.index("Canale")
        y = away.index("Canale")
    elif "Vilic Law" in comp:
        comp = comp[10:]
        x = home.index("Capital")
        y = away.index("Capital")
    elif comp == "Mens City League Cup":
        x = home.index("Mens")
        y = away.index("Mens")
    elif "Veto Mens" in comp:
        comp = comp[10:]
        x = home.index("Mens")
        y = away.index("Mens")
    elif "Mens U" in comp:
        comp = comp[5:]
        x = home.index("Mens")
        y = away.index("Mens")
    elif "Womens Premier" in comp:
        x = home.index("BWPL")
        y = away.index("BWPL")
    elif "Elaine Watson Cup" in comp:
        comp = comp[:17]
        if "-" in home:
            x = home.index("-")
        else:
            x = home.index("Elaine")
        if "-" in away:
            y = away.index("-")
        else:
            y = away.index("Elaine")
    elif "Womens Capital" in comp:
        x = min(home.index("Women"), home.index("Capital"))
        y = min(away.index("Women"), away.index("Capital"))
    elif comp == "Womens City League Cup":
        x = home.index("Womens")
        y = away.index("Womens")
    elif "Veto Womens" in comp:
        comp = comp[5:]
        x = min(home.index("Women"), home.index("City"))
        y = min(away.index("Women"), away.index("City"))
    elif "Womens Legends" in comp:
        x = home.index("Womens")
        y = away.index("Womens")
    elif "Youth" in comp:
        x = home.index("U1")
        y = away.index("U1")
    elif "Wolff" in comp:
        comp = comp[23:]
        x = home.index("U1")
        y = away.index("U1")
    home = home[:x - 1]
    away = away[:y - 1]

    # Referee names are assigned.
    browser.find_elements_by_link_text("More")[index].click()
    referee_table = browser.find_element_by_xpath("//div[@id="
                                                  "'FixtureAppointmentTable']")
    content = referee_table.get_attribute("outerHTML")
    soup = BeautifulSoup(content, features="html.parser")
    referees = pd.read_html(str(soup))[0]
    referees = referees.iloc[:, 1].dropna().iloc[1::2]

    for official_index, official in enumerate(referees):
        matches.iloc[index, 9 + official_index] = official

    # Enters altered information into DataFrame.
    matches.iloc[index, 0] = comp
    matches.iloc[index, 2] = date
    matches.iloc[index, 3] = time
    matches.iloc[index, 6] = home
    matches.iloc[index, 7] = away
    matches.iloc[index, 8] = fees.loc[comp, role]

    browser.back()


browser.get("https://my.refsix.com/#/login")
browser.implicitly_wait(5)
refsix_username = browser.find_element_by_xpath("//input[@type='text']")
refsix_username.send_keys(values["refsix-username"])
refsix_password = browser.find_element_by_xpath("//input[@type='password']")
refsix_password.send_keys(values["refsix-password"])
refsix_submit = browser.find_element_by_tag_name("button")
refsix_submit.click()

for index in range(len(matches)):
    WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH,
                                "//button[@href='#/ref/fixture/new']"))).click()

    comp = matches.iloc[index, 0]
    role = matches.iloc[index, 1]
    date = matches.iloc[index, 2]
    time = matches.iloc[index, 3]
    venue = matches.iloc[index, 5]
    home = matches.iloc[index, 6]
    away = matches.iloc[index, 7]
    fees = matches.iloc[index, 8]
    referee = matches.iloc[index, 9]
    assistant1 = matches.iloc[index, 10]
    assistant2 = matches.iloc[index, 11]
    fourth = matches.iloc[index, 12]
    assessor = matches.iloc[index, 13]

    browser.find_element_by_xpath("//input[@name='competition']").send_keys(comp)
    browser.find_element_by_xpath("//input[@name='venue']").send_keys(venue)

    ko = date + Keys.ARROW_RIGHT + time + "P"
    browser.find_element_by_xpath("//input[@name='fixtureDate']").send_keys(ko)

    referee_xpath = "//option[@value='referee']"
    assistant_xpath = "//option[@value='assistant']"
    fourth_xpath = "//option[@value='fourthOfficial']"
    assessor_xpath = "//option[@value='observer']"

    if role == "Referee":
        browser.find_element_by_xpath(referee_xpath).click()
    elif role in ("AR1", "AR2"):
        browser.find_element_by_xpath(assistant_xpath).click()
    elif role == "Fourth":
        browser.find_element_by_xpath(fourth_xpath).click()
    elif role == "Observer":
        browser.find_element_by_xpath(assessor_xpath).click()

    browser.find_element_by_xpath("//input[@name='homeTeam']").send_keys(home)
    browser.find_element_by_xpath("//input[@name='awayTeam']").send_keys(away)

    earnings_xpath = "//div[@name='earningsForm']"
    open_form(browser.find_element_by_xpath(earnings_xpath), browser)

    fees_form = browser.find_element_by_xpath("//input[@name='fees']")
    browser.execute_script("arguments[0].scrollIntoView();", fees_form)
    fees_form.send_keys(fees)

    officials_xpath = "//div[@name='matchOfficialsForm']"
    open_form(browser.find_element_by_xpath(officials_xpath), browser)

    referee_xpath = "//input[@name='matchOfficialsreferee']"
    assistant1_xpath = "//input[@name='matchOfficialsassistant1']"
    assistant2_xpath = "//input[@name='matchOfficialsassistant2']"
    fourth_xpath = "//input[@name='matchOfficialsfourthOfficial']"
    assessor_xpath = "//input[@name='matchOfficialsobserver']"

    if role != "Referee":
        browser.find_element_by_xpath(referee_xpath).send_keys(referee)
    if role not in ["AR1", "AR2"]:
        browser.find_element_by_xpath(assistant1_xpath).send_keys(assistant1)
        browser.find_element_by_xpath(assistant2_xpath).send_keys(assistant2)
    elif role == "AR1":
        browser.find_element_by_xpath(assistant2_xpath).send_keys(assistant2)
    elif role == "AR2":
        browser.find_element_by_xpath(assistant2_xpath).send_keys(assistant1)
    if role != "Fourth":
        browser.find_element_by_xpath(fourth_xpath).send_keys(fourth)
    if role != "Assessor":
        browser.find_element_by_xpath(assessor_xpath).send_keys(assessor)

    # Submit.
    browser.find_element_by_xpath("//span["
                                  "@class='primary-buttons']/button").click()
    # Back to home.
    browser.find_element_by_class_name("header-left").click()

browser.quit()

earnings = matches["Fees"]
for index in range(len(earnings)):
    earnings[index] = float(earnings[index])
print(f"You will earn ${round(earnings.sum(), 2)} for these matches.")
