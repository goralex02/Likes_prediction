import time

import logging

import pandas

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc


class CSV:
    def __init__(self):
        self.author = []
        self.prompt = []
        self.link_to_image = []
        self.like = []
        self.data = {"author": self.author}
        self.author_data = {"image": self.link_to_image, "prompt": self.prompt, "like": self.like}

    def add_author(self, author: str):
        try:
            self.author.append(author)
        except Exception as e:
            logging.error(e)

    def add_image_to_author(self, image: str, prompt: str, like: str):
        try:
            self.prompt.append(prompt)
            self.like.append(like)
            self.link_to_image.append(image)
        except Exception as e:
            logging.error(e)

    def save_author(self, name: str, subsme: str = None, subs: str = None, like: str = None):
        try:
            pandas.DataFrame(self.author_data).to_csv(f"{name}_{subsme}_{subs}_{like}.csv")
        except Exception as e:
            logging.error(e)

    def save_authors(self):
        try:
            pandas.DataFrame(self.data).to_csv(f"authors.csv")
        except Exception as e:
            logging.error(e)


class Schedevrum:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("user-agent=Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.5) Gecko/20091102 "
                             "Firefox/3.5.5 (.NET CLR 3.5.30728 )")
        self.caps = DesiredCapabilities().CHROME
        self.caps["pageLoadStrategy"] = "eager"
        self.driver = uc.Chrome(use_subprocess=True, options=options, desired_capabilities=self.caps)
        self.csv = CSV()
        logging.info("StartUp")

    def __parse_authors(self):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        images = soup.find_all(class_="bg-white")
        for image in images[-18:]:
            try:

                author = image.find(class_="shrink-0").get("href").strip()
                self.csv.add_author(author)

                print(author)

            except Exception as e:
                logging.error(e)

    def main_page_parse_authors(self):
        self.driver.get("https://shedevrum.ai/")
        time.sleep(2)
        scroll_count = 0
        while True:
            try:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                logging.info("Парсим...")
                if scroll_count % 6 == 0:
                    self.__parse_authors()
                scroll_count += 1

                if scroll_count == 12:
                    break

            except Exception as e:
                logging.error(e)
            finally:
                self.csv.save_authors()

    def __parse_data_from_author(self):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        images = soup.find_all(class_="bg-white")
        for image in images[-18:]:
            try:
                like: str = image.find(
                    class_="font-bold text-button flex gap-[.4rem] items-center select-none cursor-pointer hover-opacity-66 transition-opacity active:opacity-[.45] ml-[1rem] mr-[1rem]").get_text()
                prompt: str = image.find(
                    class_="prompt text-small md:text-base stretch-quaternary opacity-[.66] break-words line-clamp-2 self-center whitespace-pre-wrap").get(
                    "title")
                link_image: str = image.find(class_="aspect-square w-full bg-[#f5f5f5] rounded-[1.2rem]").get("src")

                self.csv.add_image_to_author(link_image, prompt.replace("\n", " ").replace("  ", " "), like)

            except Exception as e:
                logging.error(e)
                
    def get_images(self, author: str):
        author = self.__clear(author)
        self.driver.get(f"https://shedevrum.ai/profile/{author}/")
        time.sleep(2)
        try:
            subsme = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[3]/div/div[2]/div[1]/span[1]').text
            subs = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[3]/div/div[2]/div[2]/span[1]').text
            like = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[3]/div/div[2]/div[3]/span[1]').text
        except Exception as e:
            subsme = None
            subs = None
            like = None
            logging.error(e)

        scroll_count = 0
        while True:
            try:
                if scroll_count % 6 == 0:
                    self.__parse_data_from_author()
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)

                scroll_count += 1

                if self.driver.find_element(By.XPATH, '//*[@id="app"]/div[6]').text:
                    break

            except Exception as e:
                logging.error(e)
            finally:
                self.csv.save_author(author, subsme, subs, like)

    @staticmethod
    def __clear(profile: str):
        if "profile" in profile.split("/"):
            return profile.split("/")[-2]
        return profile.split("/")[1]

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    a = Schedevrum()
    # a.get_image("https://shedevrum.ai/post/39dd04a0b08311ee8d61ba0d8cad0506/")

    #a.get_images("/@moonlight/")
    #for _ in range(1):
        #a.main_page_parse_authors()
        #time.sleep(60)