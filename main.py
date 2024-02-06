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

    unique_authors_count = df['author'].nunique()

    print("Количество уникальных значений в столбце 'author':", unique_authors_count)
    df = df.drop_duplicates(subset='author')
    df.reset_index(drop=True, inplace=True)
    df.to_csv(f'no_doubles_{filename}', index=True)

class CSV:
    def __init__(self):
        self.data = {"author": [], "subsme": [], "subs": [], "like": []}
        self.author_data = {"author": [], "prompt": [], "link_to_image": [], "like": []}

    def __update__(self):
        self.author_data = {"author": [], "prompt": [], "link_to_image": [], "like": []}

    def add_author(self, author: str):
        try:
            self.author_data["author"].append(author)
        except Exception as e:
            logging.error(e)
    
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
            df = pandas.DataFrame(self.author_data).head(100) #100
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

        logging.info(f'Найдено {len(images)} изображений')

        self.csv.__update__()

        del images[:2]
        for image in images:
            try:
                
                like: str = image.find(
                    class_="font-bold text-button flex gap-[.4rem] items-center select-none cursor-pointer hover-opacity-66 transition-opacity active:opacity-[.45] ml-[.9rem] mr-[.9rem]").get_text()              
                
                prompt: str = image.find(
                    class_="prompt text-small md:text-base stretch-quaternary text-secondary break-words line-clamp-2 self-center whitespace-pre-wrap").get(
                    "title")
                
                link_image: str = image.find(class_="aspect-square w-full bg-[#f5f5f5] transition-[opacity] duration-500 opacity-100 rounded-[1.2rem]").get("src")

                self.csv.add_image_to_author(author, link_image, prompt.replace("\n", " ").replace("  ", " "), like)

            except Exception as e:
                logging.error(e)
                
    def get_images(self, author_link: str):
        author = self.__clear(author_link)
        self.driver.get(f"https://shedevrum.ai/profile/{author}/")
        time.sleep(3)
        limit = 8 #8 
        logging.info("Скроллим...")        
        for _ in range (limit):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)

        try:
            logging.info("Выкачиваем...")
            self.__parse_data_from_author(author_link)
        except Exception as e:
            logging.error(e) 
        
        logging.info("Сохраняем...")
        self.csv.save_author(author)


    def close_browser_session(self):
            try:
                self.driver.quit()
            except Exception as e:
                logging.error(e)


    def process_datasets_folder(folder_path):
        for filename in os.listdir(folder_path):
            if filename.endswith(".csv"):
                file_path = os.path.join(folder_path, filename)
                try:
                    size = os.path.getsize(file_path)
                    if not size == 0:
                        # Считываем CSV файл
                        df = pandas.read_csv(file_path)
                        # Проверяем количество строк в файле
                        num_rows = len(df) if not df.empty else 0
                        if (num_rows > 49) and (num_rows < 55):
                            # Запускаем a.get_images() для автора
                            author = filename.split(".")[0]  # Извлекаем имя автора из имени файла
                            #a.get_images(f"/profile/{author}/")
                        elif size == 0:
                            author = filename.split(".")[0]  # Извлекаем имя автора из имени файла
                            #a.get_images(f"/profile/{author}/")

                except Exception as e:
                    print(f"Ошибка при обработке файла {filename}: {e}")



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    #a = Schedevrum()


    # a.get_image("https://shedevrum.ai/post/39dd04a0b08311ee8d61ba0d8cad0506/")
    #a.get_images("/@wow/")


    """csv_path = 'authors_1000.csv'  
    df = pandas.read_csv(csv_path)

    df=df.iloc[985:1002]

    for author_value in df['author']:
        print(author_value)
        a.get_images(author_value)"""
    
    #a.get_images("/@eklerika/")


    #for _ in range(1):
        #a.main_page_parse_authors_with_info(12)
        #time.sleep(10)
    #a.main_page_parse_authors_with_info(100)
    #check_doubles('authors_2.csv')

    #import os




    """# Замените 'datasets' на путь к вашей директории с CSV файлами
    datasets_folder_path = 'datasets'
    process_datasets_folder(datasets_folder_path)"""
    #import pandas as pd
    """# 1. Найдем CSV файлы, содержащие менее 5 строк
    small_files = []
    datasets_folder_path = 'datasets'  # Путь к папке с CSV файлами
    for filename in os.listdir(datasets_folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(datasets_folder_path, filename)
            try:
                df = pandas.read_csv(file_path)
                if len(df) < 5:
                    small_files.append(file_path)
            except Exception as e:
                print(f"Ошибка при обработке файла {filename}: {e}")
    print('amogus1')

    # 2. Удалим соответствующих авторов из authors_1000.csv
    authors_1000_path = 'authors_1000.csv'
    df_authors_1000 = pandas.read_csv(authors_1000_path)
    for small_file in small_files:
        #author_name = os.path.basename(small_file).split("//")[1].split(".")[0]
        author_name = os.path.basename(small_file).split(".")[0]
        print(author_name)
        author_name_1 = '/'+author_name+'/'
        author_name_2 = '/profile/'+author_name+'/'
        df_authors_1000 = df_authors_1000[df_authors_1000['author'] != author_name_1]
        df_authors_1000 = df_authors_1000[df_authors_1000['author'] != author_name_2]
    print('amogus2', small_files)
    print (df_authors_1000.head(5))

    # 3. Скопируем необходимое количество авторов из authors_2.csv в authors_1000.csv
    authors_2_path = 'authors_2.csv'
    df_authors_2 = pandas.read_csv(authors_2_path)
    print(df_authors_2.head())
    num_additional_authors = 1000 - len(df_authors_1000)
    df_authors_1000 = pandas.concat([df_authors_1000, df_authors_2.iloc[1000:1000+num_additional_authors]])
    print('amogus3', num_additional_authors)

    # Сохраним обновленный authors_1000.csv

    df_authors_1000_reset = df_authors_1000.reset_index(drop=True)
    df_authors_1000.to_csv(authors_1000_path, index=True)

    # 4. Вызовем a.get_images() для новых авторов
    new_authors = df_authors_2.iloc[1000:1000+num_additional_authors]['author'].tolist()
    for author in new_authors:
        print(author)
        a.get_images(f"/profile/{author}/")
    print('amogus4')"""
    
    #a.close_browser_session()



