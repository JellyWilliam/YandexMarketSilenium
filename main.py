import time
import tkinter as tk
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait


class YandexMarket:
    browser = None

    def __init__(self):
        self.init_driver()

    def init_driver(self):
        options = Options()
        # Чтобы драйвер не закрывал браузер при ошибке
        options.add_experimental_option("detach", True)
        # Чтобы драйвер не выводил свои логи
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        # Подставной юзерагент
        # options.add_argument(f"user-agent={UserAgent(use_external_data=True).random}")
        # Запуск в развернутом режиме
        options.add_argument("--start-maximized")
        # Путь до драйвера
        s = Service(str(Path.cwd() / 'yandexdriver.exe'))
        self.browser = webdriver.Chrome(service=s, options=options)

    def scroll(self):
        # Скрипт, который получает высоту страницы
        last_height = self.browser.execute_script("return document.body.scrollHeight")
        while True:
            # Пролистывание страницы вниз (для прогрузки всех товаров на странице)
            self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Ожидание
            time.sleep(0.5)
            # Получение новой высоты страницы (на тот случай, если произойдет ещё подгрузка данных)
            new_height = self.browser.execute_script("return document.body.scrollHeight")
            # Сравнение высоты страницы до и после, если они равны, то выходим из цикла
            if new_height == last_height:
                break
            # Если высоты страниц не равны, то перезаписываем высоту и продолжаем скролить вниз
            last_height = new_height

    def get_main_page(self):
        url_market = "https://market.yandex.ru/"
        # С помощью метода get открываем страницу
        self.browser.get(url_market)
        # Проверяем что мы попали на нужную страницу (возможно потребуется подтвердить вы не робот)
        WebDriverWait(self.browser, 200).until(
            EC.title_contains("Интернет-магазин Яндекс Маркет — покупки с быстрой доставкой"))

    def get_element_web_driver_wait(self, selector, by=By.CSS_SELECTOR, delay=10):
        # Функция, которая проверяет наличие элемента на странице и возвращает его, если он есть
        return WebDriverWait(self.browser, delay).until(EC.visibility_of_element_located((by, selector)))

    def get_smartphone(self):
        # CSS Selector кнопки каталога
        catalog_selector = "#catalogPopupButton"
        # Selector выбора смрартфонов из каталога
        smartphone_selector = "#catalogPopup > div > div > div > div > div > div > div.EH4e7 > div > div > div > div._2HhF1 > div > div > div > div > div > div > div > div:nth-child(1) > div:nth-child(1) > ul > li:nth-child(1) > div > a"

        # Эмитирование нажатия правой кнопки на элемент методом .click()
        self.get_element_web_driver_wait(catalog_selector).click()
        self.get_element_web_driver_wait(smartphone_selector).click()

    def next_page(self, n_page):
        # Получение текущего тайтла старницы
        current_title = self.browser.title
        # Получение текущего url страницы
        current_url = self.browser.current_url
        # Проверка что в ссылке есть параметр номера старницы
        if current_url.find("&page=") == -1:
            # Если параметра нет, то добавляем его
            self.browser.get(f"{current_url}&page={n_page}")
        else:
            # Если он есть, то делаем замену номера траницы
            buf = current_url.split("&page=")
            self.browser.get(f"{buf[0]}&page={n_page}")
        # Поулчаем текущий тайтл
        new_title = self.browser.title
        # Сравниваем с прошлым тайтлом (если страницы 2, а мы хотим 3, то в тайтле отсанется сатрница 2)
        if current_title == new_title:
            # Вывод ошибки, что страница не поменялась, следовательно больше страниц нет
            raise Exception("More page not found")
        # Ожидание подгрузки страницы
        time.sleep(2)

    def parce_page(self, dataset_name, max_pages):
        # Лямбда функции получения XPATH каждого итема на странице
        name_xpath = lambda \
                id: f"/html/body/div[4]/div[2]/div[1]/div[5]/div/div/div/div/div/div/div[5]/div/div/div/div/main/div/div/div/div/div/div/div[{id}]/div/div/div/article/div[3]/div[1]/h3/a"
        parameter_xpath = lambda \
                id: f"/html/body/div[4]/div[2]/div[1]/div[5]/div/div/div/div/div/div/div[5]/div/div/div/div/main/div/div/div/div/div/div/div[{id}]/div/div/div/article/div[3]/div[2]/ul"
        price_xpath = lambda \
                id: f"/html/body/div[4]/div[2]/div[1]/div[5]/div/div/div/div/div/div/div[5]/div/div/div/div/main/div/div/div/div/div/div/div[{id}]/div/div/div/article/div[4]/div[1]/div[1]/div/a/div/span/span[1]"

        # Массивы для записи всех данных
        name_arr = []
        parameter_arr = []
        price_arr = []

        n_page = 2
        while True:
            try:
                self.scroll()
                for i in range(1, 50):
                    try:
                        # Получение текста элемента
                        name_arr.append(self.get_element_web_driver_wait(name_xpath(i), By.XPATH).text)
                        parameter_arr.append(self.get_element_web_driver_wait(parameter_xpath(i), By.XPATH).text)
                        price_arr.append(self.get_element_web_driver_wait(price_xpath(i), By.XPATH).text)
                    except Exception as e:
                        print(f"ID {i} - выдал ошибку:\n{e}")
                        if i != 1:
                            break
                if n_page > max_pages:
                    break
                self.next_page(n_page)
                n_page += 1
            except Exception as e:
                print(e)
                break
        # Скролл старницы вверх
        self.browser.execute_script("window.scrollTo(0, 0);")
        # Создание и запись датафрейма в файл
        pd.DataFrame({"name": name_arr, "parameter": parameter_arr, "price": price_arr}).to_csv(f"{dataset_name}.csv")
        print("Парсинг данных завершен!")

    def search(self, text):
        # CSS Selector поля ввода
        search_selector = "#header-search"
        # Отправка строки в поле поиска
        self.get_element_web_driver_wait(search_selector).send_keys(text)
        # Нажатие кнопки Enter
        self.get_element_web_driver_wait(search_selector).send_keys(Keys.ENTER)
        # Ожидание прогрузки страницы
        time.sleep(2)

    def test(self):
        # Функция для теста
        self.get_main_page()
        self.get_smartphone()
        self.parce_page("Парсинг смартфонов", 3)

    def run(self, search_text, dataset_name, max_pages):
        # Полноценная работа с поиском
        max_pages = max_pages if max_pages > 0 else float("inf")
        self.get_main_page()
        self.search(search_text)
        self.parce_page(dataset_name, max_pages)


yandex_market = None


def gui_init():
    window = tk.Tk()
    window.title("Парсинг страниц с ЯндексМаркета")
    greeting = tk.Label(text="Параметры")
    greeting.pack()

    search_text = tk.StringVar()

    dataset_name = tk.StringVar()

    number_page = tk.IntVar()

    tk.Label(text="Поиск").pack()
    tk.Entry(textvariable=search_text).pack()

    tk.Label(text="Имя датасета").pack()
    tk.Entry(textvariable=dataset_name).pack()

    tk.Label(text="Сколько страниц пройти (0 - все возможные)").pack()
    tk.Entry(textvariable=number_page).pack()

    def start_button(test=False):
        global yandex_market
        if yandex_market is None:
            yandex_market = YandexMarket()
        if test:
            yandex_market.test()
        else:
            yandex_market.run(search_text=search_text.get(), dataset_name=dataset_name.get(),
                              max_pages=number_page.get())

    tk.Button(
        text="Тест",
        command=lambda: start_button(True),
        width=50,
        height=2,
    ).pack()

    tk.Button(
        text="Запуск",
        command=start_button,
        width=50,
        height=2,
    ).pack()

    window.mainloop()


if __name__ == "__main__":
    gui_init()
