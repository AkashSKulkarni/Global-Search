import time
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import google.generativeai as genai
import re
import random
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

stop_words = set(stopwords.words('english'))

# Add your LinkedIn and Instahyre credentials here
LINKEDIN_USERNAME = 'akash.s.kulkrni@gmail.com'
LINKEDIN_PASSWORD = '1!2@3#4$abcd'

# Set up API key for generative AI
api_list = ["AIzaSyA51WTz0t69sBFs8D2ZmLLypKs6X9rIcEI", "AIzaSyDlCk6V9XXwHEYJSjSC4-g28N69UgNcVYA"]  # Replace with your API keys
api_key = random.choice(api_list)
genai.configure(api_key=api_key)

# Function for text preprocessing
def preprocessing(document):
    text = document.replace('\n', ' ').replace('\t', ' ').lower()
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    tokens = word_tokenize(text)
    tokens = [re.sub(r'[^a-zA-Z\s]', '', token) for token in tokens]
    tokens = [token for token in tokens if token and token not in stop_words]
    preprocessed_text = ' '.join(tokens)
    return preprocessed_text

def title(input_text):
    model = genai.GenerativeModel('gemini-1.5-flash')
    input_prompt = ("You are a skilled Topic Modelling model. Extract the first job title mentioned in the text. "
                    "The output should only include the first job title found, such as CEO, CTO, CFO, etc., "
                    "without any additional explanation or other titles.")
    '''input_prompt = ("You are a skilled Topic Modelling model. Extract the job title(s) mentioned in the text. "
                    "Only return the job title(s) without any additional explanation or context. "
                    "The output should only include titles like CEO, COO, CFO, CIO, CTO, CMO, CHRO, CPO, CISO, CRO, CSO, CCO, CDO, CDAO, CLO, CBO, CGO, CAO, Senior Vice President, Vice President, Executive Vice President, Group Vice President, Global Head of [Department], Managing Director, General Manager, Head of [Department], Senior Director, Chief of Staff, Director of [Department], Director, Associate Vice President, Assistant Vice President, Deputy Director, Senior Manager, Regional Manager, Manager of [Department], Principal Consultant, Lead [Department], Department Head, Operations Manager, Program Manager, Project Manager, Team Lead, and Business Unit Head. if present in the text.")
    input_prompt = ("You are a skilled Topic Modelling model. Get me the job title mentioned in the text. "
                    "The output should be in this way: Job Title. "
                    "Don't give an explanation, just follow the example provided. e.g., CEO, COO, CFO, CIO, CTO, CMO, CHRO, CPO, CISO, CRO, CSO, CCO, CDO, CDAO, CLO, CBO, CGO, CAO, Senior Vice President, Vice President, Executive Vice President, Group Vice President, Global Head of [Department], Managing Director, General Manager, Head of [Department], Senior Director, Chief of Staff, Director of [Department], Director, Associate Vice President, Assistant Vice President, Deputy Director, Senior Manager, Regional Manager, Manager of [Department], Principal Consultant, Lead [Department], Department Head, Operations Manager, Program Manager, Project Manager, Team Lead, and Business Unit Head.")
    '''
    full_prompt = f"{input_prompt}\n\n{input_text}"
    response = model.generate_content(full_prompt, generation_config=genai.GenerationConfig(
        temperature=0.3))
    return response.text.strip()

def check_keywords(title, experience, keywords):
    title_lower = title.lower()
    experience_lower = " ".join(exp.lower() for exp in experience).lower()
    return all(keyword.lower() in title_lower for keyword in keywords) or \
           (keywords[0].lower() in title_lower and keywords[1].lower() in experience_lower)

def data_scraping(profile_urls, keywords, driver):
    dataset = []

    print(f"Total profiles to scrape: {len(profile_urls)}")

    for profile_url in profile_urls:
        profile_data = {}
        driver.get(profile_url)
        time.sleep(3)

        try:
            profile_data['Name'] = driver.find_element(By.XPATH, '//h1[@class="text-heading-xlarge inline t-24 v-align-middle break-words"]').text
        except NoSuchElementException:
            profile_data['Name'] = 'NA'

        try:
            profile_description = driver.find_element(By.XPATH, '//div[@class="text-body-medium break-words"]').text
            preprocessed_description = preprocessing(profile_description)
            profile_data['Title'] = title(preprocessed_description)
        except NoSuchElementException:
            profile_data['Title'] = 'NA'

        try:
            profile_data['Location'] = driver.find_element(By.XPATH, '//span[@class="text-body-small inline t-black--light break-words"]').text
        except NoSuchElementException:
            profile_data['Location'] = 'NA'

        try:
            contact_info_button = driver.find_element(By.XPATH, '//a[@id="top-card-text-details-contact-info"]')
            contact_info_button.click()
            time.sleep(5)  # Wait for contact info to load
            try:
                linkedin_url_element = driver.find_element(By.XPATH, '//a[contains(@href, "linkedin.com/in/")]')
                profile_data['LinkedIn_URL'] = linkedin_url_element.get_attribute('href')
            except NoSuchElementException:
                profile_data['LinkedIn_URL'] = 'NA'
            try:
                phone_element = driver.find_element(By.XPATH, '//span[@class="t-14 t-black t-normal"]')
                profile_data['Phone'] = phone_element.text
            except NoSuchElementException:
                profile_data['Phone'] = 'NA'
            try:
                email_element = driver.find_element(By.XPATH, '//a[starts-with(@href, "mailto:")]')
                profile_data['Email'] = email_element.get_attribute('href').replace('mailto:', '')
            except NoSuchElementException:
                profile_data['Email'] = 'NA'
            driver.find_element(By.XPATH, '//button[@aria-label="Dismiss"]').click()
            time.sleep(2)  # Wait for the overlay to close
        except NoSuchElementException:
            profile_data['Contact_Info'] = {'LinkedIn_URL': 'NA', 'Phone': 'NA', 'Email': 'NA'}
        except WebDriverException as e:
            print(f"WebDriverException occurred: {e}")
            profile_data['Contact_Info'] = {'LinkedIn_URL': 'NA', 'Phone': 'NA', 'Email': 'NA'}

        try:
            try:
                show_all_experience_button = driver.find_element(By.CSS_SELECTOR, "a[id='navigation-index-see-all-experiences'] span[class='pvs-navigation__text']")
                show_all_experience_button.click()
                time.sleep(5)  # Wait for all experiences to load
                experience_container = driver.find_element(By.XPATH, '//section[@class="artdeco-card pb3"]')
                experience_items = experience_container.find_elements(By.XPATH, './/li')
                experience_info = [item.text for item in experience_items]
                profile_data['Experience'] = experience_info

                driver.find_element(By.XPATH, '//div[@class="presence-entity presence-entity--size-1 m1"]').click()
                time.sleep(5)  # Optional wait for stability after clicking
            except NoSuchElementException:
                try:
                    experience_section_heading = driver.find_element(By.XPATH, '//span[text()="Experience"]/ancestor::section')
                    experience_items = experience_section_heading.find_elements(By.TAG_NAME, 'li')
                    experience_info = [item.text for item in experience_items]
                    profile_data['Experience'] = experience_info
                except NoSuchElementException:
                    profile_data['Experience'] = ['NA']
        except NoSuchElementException:
            profile_data['Experience'] = ['NA']

        try:
            education_section = driver.find_element(By.XPATH, '//span[text()="Education"]/ancestor::section')
            education_items = education_section.find_elements(By.TAG_NAME, 'li')
            education_info = [item.text for item in education_items]
            profile_data['Education'] = education_info
        except NoSuchElementException:
            profile_data['Education'] = ['NA']

        try:
            try:
                show_all_skills_button = driver.find_element(By.XPATH, "//a[contains(@id,'navigation-index-Show-all-') and contains(@id,'skills')]//span[@class='pvs-navigation__text']")
                show_all_skills_button.click()
                time.sleep(5)  # Wait for all skills to load
            except NoSuchElementException:
                try:
                    skills_section = driver.find_element(By.XPATH, "//span[text()='Skills']/ancestor::section")
                    skill_elements = skills_section.find_elements(By.TAG_NAME, 'li')
                    skills = [element.text for element in skill_elements]
                except NoSuchElementException:
                    skills = ['NA']
            else:
                skills = []
                skill_elements = driver.find_elements(By.XPATH, "//body/div[@class='application-outlet']/div[@class='authentication-outlet']/div[@id='profile-content']/div[@class='body']/div[2]/div[1]/div[1]/main[1]/section[1]/div[2]/div[2]/div[1]/div[1]/div[1]")
                for element in skill_elements:
                    skills.append(element.text)
            profile_data['Skills'] = skills
        except NoSuchElementException:
            profile_data['Skills'] = ['NA']

        # Check if the profile matches the keywords criteria
        if check_keywords(profile_data['Title'], profile_data['Experience'], keywords):
            dataset.append(profile_data)
            print(f"Profile matched keywords: {profile_data['Name']}")
        else:
            print(f"Profile did not match keywords: {profile_data['Name']}")

    print(f"Data scraping complete. Found {len(dataset)} matching profiles.")
    return dataset

def scrape_linkedin_profiles(search_query, num_profiles):
    driver = webdriver.Chrome(service=Service())
    driver.maximize_window()

    def user_login():
        nonlocal driver
        driver.get('https://www.linkedin.com/')
        wait = WebDriverWait(driver, 25)
        loginbtn = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="nav__button-secondary btn-md btn-secondary-emphasis"]')))
        loginbtn.click()

        username = wait.until(EC.presence_of_element_located((By.ID, 'username')))
        password = wait.until(EC.presence_of_element_located((By.ID, 'password')))

        username.clear()
        username.send_keys(LINKEDIN_USERNAME)
        password.clear()
        password.send_keys(LINKEDIN_PASSWORD)
        password.send_keys(Keys.ENTER)

        time.sleep(5)

    def perform_search():
        nonlocal driver
        try:
            wait = WebDriverWait(driver, 25)
            search_box = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Search"]')))
            search_box.send_keys(search_query)
            search_box.send_keys(Keys.ENTER)
            time.sleep(5)

            options = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//button[text()="People"]')))
            for option in options:
                if option.text.lower() == 'people':
                    option.click()
                    break
        except Exception as e:
            print(f"An error occurred during search: {e}")
            traceback.print_exc()

    def extract_profile_urls():
        nonlocal driver
        profile_urls = []
        extracted_profiles = 0
        required_profiles = num_profiles * 4  # Extract n*4 profiles
    
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_all_elements_located((By.XPATH, '//a[@class="app-aware-link  scale-down "]')))
    
        while extracted_profiles < required_profiles:
            elements = driver.find_elements(By.XPATH, '//a[@class="app-aware-link  scale-down "]')
            for element in elements:
                url = element.get_attribute('href')
                if url not in profile_urls:
                    profile_urls.append(url)
                    extracted_profiles += 1
                if extracted_profiles >= required_profiles:
                    break
    
            if extracted_profiles >= required_profiles:
                break
    
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
    
            try:
                next_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Next"]')))
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                next_button.click()
                time.sleep(2)
            except TimeoutException:
                print("Timeout occurred while waiting for the Next button to be clickable.")
                break
    
        return profile_urls  # Return all collected profile URLs

    try:
        user_login()
        perform_search()
        profile_urls = extract_profile_urls()
        print(f"Extracted {len(profile_urls)} profiles.")
        scraped_data = data_scraping(profile_urls, search_query.split(','), driver)
        return scraped_data

    except Exception as e:
        print(f"An error occurred during LinkedIn scraping: {e}")
        traceback.print_exc()

    finally:
        driver.quit()
        
