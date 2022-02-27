from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
import pandas as pd
import PySimpleGUI as sg
import threading
import time
import math

# Selenium setup
PATH = 'C:\Program Files\chromedriver.exe'  # Path to driver
options = webdriver.ChromeOptions()
options.add_experimental_option('excludeSwitches', ['enable-logging'])
driver = webdriver.Chrome(service=Service(PATH), options=options)
driver.set_window_position(0, 0)
driver.set_window_size(500, 650)
handle_of_the_window = driver.current_window_handle
driver.set_window_size(1280, 720)
driver.minimize_window()

def login():
    """Logs into Twitch"""

    # Go to Twitch and click login
    driver.get("https://www.twitch.tv/")
    driver.find_element(
        By.CSS_SELECTOR, "[data-a-target='login-button']").click()

    # Wait for login form to appear and fill in username and password and click on "Login"
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login-username")))
    except:
        driver.quit()

    usernameField = driver.find_element(By.ID, "login-username")
    usernameField.send_keys(values['username'])

    passwordField = driver.find_element(By.ID, "password-input")
    passwordField.send_keys(values['password'])

    driver.find_element(
        By.CSS_SELECTOR, "[data-a-target='passport-login-button']").click()

    # Wait for a response of logging in
    try:
        WebDriverWait(driver, 60).until(EC.presence_of_element_located(
            (By.XPATH, "//h4[text()='Verify login code'] | //strong[text()='That password was incorrect. Please try again.'] | //strong[text()='This username does not exist.'] | //strong[contains(text(), 'recognize this username. Please try again.')] | //a[@id='fc_meta_audio_btn']")))

        # Successfull login enable 2FA
        try:
            WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                (By.XPATH, "//h4[text()='Verify login code']")))

            window['loginmessage'].update(
                'Logged in. Confirm 2FA through email.')

            window['2fa'].update(disabled=False)
            window['CONFIRM'].update(disabled=False)
            window['RESEND CODE'].update(disabled=False)

        except:
            # Incorrect password
            try:
                WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                    (By.XPATH, "//strong[text()='That password was incorrect. Please try again.']")))

                window['loginmessage'].update('Incorrect password.')

            except:
                # Username does not exist
                try:
                    WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                        (By.XPATH, "//strong[text()='This username does not exist.']")))

                    window['loginmessage'].update(
                        'Username does not exist.')

                except:
                    # Incorrectly written usernam
                    try:
                        WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                            (By.XPATH, "//strong[contains(text(), 'recognize this username. Please try again.')]")))

                        window['loginmessage'].update(
                            'Username incorrectly written.')

                    except:
                        # Anti-bot protection. Requires manual intervention. Possibly bugged
                        try:
                            WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                                (By.XPATH, "//a[@id='fc_meta_audio_btn']")))

                            window['loginmessage'].update(
                                'Caught by anti-bot protection. Solve puzzle.')

                            # Unminimize window
                            driver.switch_to.window(handle_of_the_window)
                            driver.set_window_rect(0, 0)

                            # Check for succesfull completion of anti-bot protection
                            WebDriverWait(driver, 300).until(EC.presence_of_element_located(
                                (By.XPATH, "//h4[text()='Verify login code']")))
                            window['loginmessage'].update(
                                'Logged in. Confirm 2FA through email.')
                            window['2fa'].update(disabled=False)
                            window['CONFIRM'].update(disabled=False)

                        except:
                            window['loginmessage'].update(
                                'Unexpected error detected.')
    except:
        window['loginmessage'].update(
            'Error: Could not locate login element.')


def run_follower():
    """Follow accounts on the CSV file"""

    global followed
    followed = 0
    global skipped
    skipped = 0

    # Loop through every link in csv
    for ind in df.index:
        # Go to link
        link = df[0][ind]
        driver.get(link)
        print(ind + 1, '- Go to', link)

        # Wait for either follow, unfollow button or error message to appear.
        try:
            WebDriverWait(driver, 60).until(EC.presence_of_element_located(
                (By.XPATH, "//button[@data-a-target='follow-button'] | //button[@data-a-target='unfollow-button'] | //p[@data-a-target='core-error-message']")))
            print('Found either (un)follow button or error page.')

            # Give 1 second to find unfollow button or error page. Should be sufficient time, because of previous delay.
            try:
                WebDriverWait(driver, 1).until(EC.presence_of_element_located(
                    (By.XPATH, "//button[@data-a-target='unfollow-button'] | //p[@data-a-target='core-error-message']")))
                print('Unfollow button or error page found. Skip.')
                skipped += 1

            # If no unfollow button or error page was found
            except:
                print('No unfollow button found.')

                # Locate follow button
                elementFB = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//button[@data-a-target='follow-button']")))

                if elementFB:
                    print('Follow button found.')

                    # Click follow button
                    followButton = ActionChains(driver).move_to_element(
                        elementFB).click(elementFB).perform()
                    print('Clicked follow button.')

                    # Check if user is followed
                    elementFollowed = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                        (By.XPATH, "//button[@data-a-target='unfollow-button']")))
                    if elementFollowed:
                        print('Verified followed.')
                        followed += 1
        except:
            print('Did not find anything.')
            skipped += 1

    global ended
    ended = True


# Layout UI
sg.theme('SystemDefault1')

layout = [
    [sg.Frame('Select & Load CSV File', [
        [sg.Text("CSV file:", size=(8, 1), key='csvtext'), sg.Input(
            key="csvpath", size=(63, 1)), sg.FileBrowse(key='csvbrowser')],
        [sg.Text('\n', key="csvmessage")],
        [sg.Button('LOAD')]], size=(610, 140))],

    [sg.Frame('Login To Twitch', [
        [sg.Text('Username:', size=(8, 1), key='usernametext'),
         sg.InputText(key="username", size=(28, 1))],
        [sg.Text('Password:', size=(8, 1), key="passwordtext"),
         sg.InputText(key="password", password_char='*', size=(28, 1))],
        [sg.Text(key="loginmessage")],
        [sg.Button('LOGIN')]], size=(300, 140)),

     sg.Frame('2FA Login Confirmation', [
         [sg.Text('2FA Code:', size=(8, 1)),
          sg.InputText(key="2fa", size=(28, 1), disabled=True)],
         [sg.Text(key="2famessage")],
         [sg.Button('CONFIRM', disabled=True), sg.Button('RESEND CODE', disabled=True)]], size=(300, 140))],

    [sg.Frame('Twitch Autofollower', [
        [sg.ProgressBar(1, key="progressbar", size=(46, 20))],
        [sg.Text('Time:', size=(8, 1)),
         sg.Text(key='time')],
        [sg.Text('Followed:', size=(8, 1)),
         sg.Text(key='follows')],
        [sg.Text('Skipped:', size=(8, 1)),
         sg.Text(key='skipped')],
        [sg.Text(key="starttext")],
        [sg.Button('START', disabled=True)]], size=(610, 200))]
]
window = sg.Window('Twitch Autofollower', layout,
                   size=(640, 500), finalize=True)
window['username'].bind("<Return>", "_Enter")
window['password'].bind("<Return>", "_Enter")
window['2fa'].bind("<Return>", "_Enter")
window['csvpath'].bind("<Return>", "_Enter")
window['csvbrowser'].bind("<Return>", "_Enter")

# Variables needed for updating UI
confirmed = False
loggedIn = False
fileLoaded = False
startTime = False
current_time = 0
hours = 0
minutes = 0
seconds = 0
started = False
ended = False
followed = 0
skipped = 0

# Loop to update UI ever 100ms
while True:
    event, values = window.read(timeout=100)

    # If window closes stop program
    if event == sg.WIN_CLOSED:
        break

    # If LOAD button is clicked
    if (event == 'LOAD' or event == "csvpath" + "_Enter" or event == "csvbrowser" + "_Enter") and values["csvpath"] != "" and values["csvpath"][-4:] == ".csv":
        df = pd.read_csv(values["csvpath"], header=None)
        window['csvmessage'].update('CSV file loaded: ...' + values["csvpath"]
                                    [-50:] + '\n' + str(len(df.index)) + ' accounts found to follow.')
        fileLoaded = True
        if loggedIn:
            window['START'].update(disabled=False)

    if (event == 'LOAD' or event == "csvpath" + "_Enter" or event == "csvbrowser" + "_Enter") and values["csvpath"] == "":
        window['csvmessage'].update('\nNo file selected.')

    if (event == 'LOAD' or event == "csvpath" + "_Enter" or event == "csvbrowser" + "_Enter") and values["csvpath"][-4:] != ".csv":
        window['csvmessage'].update(
            '\nThe file you selected was not a CSV file.')

    # If LOGIN button is clicked
    if (event == 'LOGIN' or event == "username" + "_Enter" or event == "password" + "_Enter") and values["username"] != "" and values["password"] != "":
        # Delete current message (does not work)
        window['loginmessage'].update('')
        login()

    if (event == 'LOGIN' or event == "username" + "_Enter" or event == "password" + "_Enter") and values["username"] == "" and values["password"] != "":
        window['loginmessage'].update('No username provided.')

    if (event == 'LOGIN' or event == "username" + "_Enter" or event == "password" + "_Enter") and values["username"] != "" and values["password"] == "":
        window['loginmessage'].update('No password provided.')

    if (event == 'LOGIN' or event == "username" + "_Enter" or event == "password" + "_Enter") and values["username"] == "" and values["password"] == "":
        window['loginmessage'].update('No username and password provided.')

    # If CONFIRM button is clicked
    if (event == 'CONFIRM' or event == "2fa" + "_Enter") and len(values["2fa"]) == 6 and values["2fa"].isdigit():

        confirmationFields = driver.find_elements(
            By.XPATH, "//input[@inputmode='numeric']")

        # If confirmed has been clicked before remove previous input
        if confirmed:
            for field in reversed(confirmationFields):
                field.send_keys(Keys.BACKSPACE)

        confirmed = True

        # Fill in 2FA
        for count, value in enumerate(confirmationFields):
            value.send_keys(values['2fa'][count])

        # Wait for reponse from 2FA
        try:
            WebDriverWait(driver, 60).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//figure[@data-a-target='top-nav-avatar'] | //strong[text() = 'Verification failed']"))
            )

            # Avatar found, user logged in
            try:
                WebDriverWait(driver, 1).until(
                    EC.presence_of_element_located(
                        (By.XPATH, "//figure[@data-a-target='top-nav-avatar']"))
                )

                window['2famessage'].update(
                    'Succesfully logged in.')

                start_time = int(round(time.time()))
                window['2famessage'].update('Succesful confirmation.')

                loggedIn = True

                if fileLoaded:
                    window['START'].update(disabled=False)

            except:
                # Wrong 2FA code was put in
                try:
                    WebDriverWait(driver, 1).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//strong[text() = 'Verification failed']"))
                    )

                    window['2famessage'].update(
                        '2FA code was not correct.')

                except:
                    window['2famessage'].update(
                        'Unexpected error detected.')

        except:
            window['2famessage'].update(
                'Error: Could not locate verification element.')

    if (event == 'CONFIRM' or event == "2fa" + "_Enter") and values["2fa"] == '':
        window['2famessage'].update(
            'No 2FA code provided. Check your email.')

    if (event == 'CONFIRM' or event == "2fa" + "_Enter") and len(values["2fa"]) != 6:
        window['2famessage'].update(
            'A 2FA code has 6 digits.')

    if (event == 'CONFIRM' or event == "2fa" + "_Enter") and not values["2fa"].isdigit():
        window['2famessage'].update(
            'A 2FA code only has digits.')

    # When RESEND CODE button is clicked
    if event == 'RESEND CODE':
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[text() = 'Resend code']"))
        ).click()
        window['2famessage'].update(
            'Code was resent.')

    # If START button is clicked
    if event == 'START':
        started = True
        start_time = int(round(time.time()))
        threading.Thread(target=run_follower).start()

    # If program started following accounts
    if started and not ended:
        # Calculate time
        current_time = int(round(time.time()) - start_time)
        hours = math.floor(current_time / 3600)
        minutes = math.floor((current_time - hours * 3600) / 60)
        seconds = current_time - hours * 3600 - minutes * 60

        # Update UI elements
        window['progressbar'].update_bar((followed + skipped) / len(df.index))
        window['time'].update(
            '{:02d}:{:02d}:{:02d}'.format(hours, minutes, seconds))
        window['follows'].update(str(followed))
        window['skipped'].update(str(skipped))

# When loop ends, close program and browser
driver.quit()
window.close()
