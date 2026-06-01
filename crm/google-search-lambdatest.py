import unittest
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options as ChromeOptions

username = "dineshrbalaji"
access_key = "LT_WvSsxhanwoFvbuLaZ9IUd01eiqvSVlUOP0PPCZI1vPheA43"

options = ChromeOptions()
options.browser_version = "dev"
options.platform_name = "Windows 10"
lt_options = {};
lt_options["username"] = username;
lt_options["accessKey"] = access_key;
lt_options["project"] = "Nova CRM";
lt_options["w3c"] = True;
lt_options["plugin"] = "python-python";
options.set_capability('LT:Options', lt_options);

class FirstSampleTest(unittest.TestCase):
    driver = None

    def setUp(self):
        self.driver = webdriver.Remote(
            command_executor="http://{}:{}@hub.lambdatest.com/wd/hub".format(
                username, access_key
            ),
            options=options,
        )

    # """ You can write the test cases here """
    def test_demo_site(self):
        # try:
        driver = self.driver
        driver.implicitly_wait(10)
        driver.set_page_load_timeout(30)
        driver.set_window_size(1920, 1080)

        # Url
        print("Loading URL")
        driver.get(
            "https://www.google.com/"
        )

        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys("LambdaTest")
        search_box.submit()
        print("Searched for LambdaTest")

        driver.implicitly_wait(3)

        if "LambdaTest" in driver.title:
            driver.execute_script("lambda-status=passed")
            print("Tests are run successfully!")
        else:
            driver.execute_script("lambda-status=failed")

    # tearDown runs after each test case
    def tearDown(self):
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    unittest.main()
