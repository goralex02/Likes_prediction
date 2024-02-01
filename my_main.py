import time

import logging

import pandas
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.by import By
import undetected_chromedriver as uc



def check_doubles(filename):
    df = pandas.read_csv(filename)
    df = df.drop(df.columns[0], axis=1)
    # Подсчитываем количество уникальных значений в столбце "author"
    unique_authors_count = df['author'].nunique()

    # Выводим результат
    print("Количество уникальных значений в столбце 'author':", unique_authors_count)
    df = df.drop_duplicates(subset='author')
    df.reset_index(drop=True, inplace=True)
    df.to_csv(f'no_doubles_{filename}', index=True)

class CSV:
    def __init__(self):
        #self.author = []
        #self.prompt = []
        #self.link_to_image = []
        #self.like = []
        self.data = {"author": [], "subsme": [], "subs": [], "like": []}

        self.author_data = {"author": [], "prompt": [], "link_to_image": [], "like": []}
        #self.author_data = {"image": self.link_to_image, "prompt": self.prompt, "like": self.like}

    def __update__(self):
        self.author_data = {"author": [], "prompt": [], "link_to_image": [], "like": []}


    def add_author(self, author: str):
        try:
            self.author_data["author"].append(author)
        except Exception as e:
            logging.error(e)

    """def add_author(self, author: str):
        try:
            self.author.append(author)
        except Exception as e:
            logging.error(e)"""

    """def add_image_to_author(self, image: str, prompt: str, like: str):
        try:
            self.prompt.append(prompt)
            self.like.append(like)
            self.link_to_image.append(image)
        except Exception as e:
            logging.error(e)"""
    
    def add_image_to_author(self, author:str, image: str, prompt: str, like: str):
        try:
            self.author_data["author"].append(author)
            self.author_data["prompt"].append(prompt)
            self.author_data["like"].append(like)
            self.author_data["link_to_image"].append(image)
        except Exception as e:
            logging.error(e)

    def save_author(self, name: str):
        try:
            datasets_folder = "datasets"
            file_path = os.path.join(datasets_folder, f"{name}.csv")
            df = pandas.DataFrame(self.author_data).head(10) #100
            df.to_csv(file_path, index=False)
        except Exception as e:
            logging.error(e)

    def save_authors(self, filename="authors_2.csv"):
        try:
            pandas.DataFrame(self.data).to_csv(filename, index=True)
        except Exception as e:
            logging.error(e)

    def add_author_data(self, author: str, subsme: str, subs: str, like: str):
        try:
            self.data["author"].append(author)
            self.data["subsme"].append(subsme)
            self.data["subs"].append(subs)
            self.data["like"].append(like)
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

    @staticmethod
    def __clear(profile: str):
        if "profile" in profile.split("/"):
            return profile.split("/")[-2]
        return profile.split("/")[1]


    #выкачка информации об авторах
    def __parse_authors_with_info(self):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        authors = soup.find_all(class_="bg-white")

        print(f"Найдено {len(authors)} картинок")

        for author in authors: 
            try:
                author_name = author.find(class_="shrink-0").get("href").strip()
               
                author = self.__clear(author_name)

                self.driver.get(f"https://shedevrum.ai/profile/{author}/")
                time.sleep(1)
                subsme = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[3]/div/div[2]/div[1]/span[1]').text
                subs = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[3]/div/div[2]/div[2]/span[1]').text
                like = self.driver.find_element(By.XPATH, '//*[@id="app"]/div[3]/div/div[2]/div[3]/span[1]').text

                self.csv.add_author_data(author_name, subsme, subs, like)
                print(author_name, subsme, subs, like)

            except Exception as e:
                logging.error(e)

    def main_page_parse_authors_with_info(self, limit: int):
        self.driver.get("https://shedevrum.ai/")
        time.sleep(2)
        logging.info("Парсим...")

        for _ in range(limit):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        try:
            logging.info("Анализируем...")
            self.__parse_authors_with_info()
        except Exception as e:
            logging.error(e)

        logging.info("Сохраняем...")
        self.csv.save_authors()


    #выкачка изображений у автора
    def __parse_data_from_author(self, author: str):
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        images = soup.find_all(class_="bg-white")

        #new
        self.csv.__update__()
        #new

        for image in images:
            try:
                like: str = image.find(
                    class_="font-bold text-button flex gap-[.4rem] items-center select-none cursor-pointer hover-opacity-66 transition-opacity active:opacity-[.45] ml-[1rem] mr-[1rem]").get_text()
                prompt: str = image.find(
                    class_="prompt text-small md:text-base stretch-quaternary opacity-[.66] break-words line-clamp-2 self-center whitespace-pre-wrap").get(
                    "title")
                link_image: str = image.find(class_="aspect-square w-full bg-[#f5f5f5] rounded-[1.2rem]").get("src")

                self.csv.add_image_to_author(author, link_image, prompt.replace("\n", " ").replace("  ", " "), like)

            except Exception as e:
                logging.error(e)
                
    def get_images(self, author_link: str):
        author = self.__clear(author_link)
        self.driver.get(f"https://shedevrum.ai/profile/{author}/")
        time.sleep(2)
        limit = 2 #6
        logging.info("Скроллим...")        
        for _ in range (limit):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        try:
            logging.info("Выкачиваем...")
            self.__parse_data_from_author(author_link)
        except Exception as e:
            logging.error(e) 
        
        logging.info("Сохраняем...")
        self.csv.save_author(author)



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    a = Schedevrum()
    # a.get_image("https://shedevrum.ai/post/39dd04a0b08311ee8d61ba0d8cad0506/")
    #a.get_images("/@wow/")


    csv_path = 'authors_10.csv'  
    df = pandas.read_csv(csv_path)

    for author_value in df['author']:
        print(author_value)
        a.get_images(author_value)
    


    #for _ in range(1):
        #a.main_page_parse_authors_with_info(12)
        #time.sleep(10)
    #a.main_page_parse_authors_with_info(100)
    #check_doubles('authors_2.csv')


