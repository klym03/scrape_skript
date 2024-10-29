import csv
import time
import aiohttp
import asyncio
import pandas as pd
import asyncpg
from bs4 import BeautifulSoup
from datetime import datetime
import os
from dotenv.main import load_dotenv
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright

load_dotenv()
DB_CONFIG = {
    "user": os.environ['USER'],
    "password": os.environ['PASSWORD'],
    "database": os.environ['DATABASE'],
    "host": os.environ['HOST'],
    "port": os.environ['PORT'],
}
CSV_OUTPUT = "products.csv"

async def init_db():
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            product_name TEXT,
            breadcrumb TEXT,
            ausfuhrung TEXT,
            supplier_article_number TEXT,
            ean_gtin TEXT,
            article_number TEXT,
            description TEXT,
            supplier TEXT,
            supplier_url TEXT UNIQUE,
            image_url TEXT,
            manufacturer TEXT,
            add_description TEXT,
            timestamp TIMESTAMPTZ
        );
    ''')
    await conn.close()

async def save_to_db(data):
    conn = await asyncpg.connect(**DB_CONFIG)
    await conn.execute('''
        INSERT INTO products (product_name, breadcrumb, ausfuhrung, 
                              supplier_article_number, ean_gtin, article_number, 
                              description, supplier, supplier_url, image_url, 
                              manufacturer, add_description, timestamp) 
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        ON CONFLICT (supplier_url) DO NOTHING;
    ''', data["Product Name"], data["Original Data Column 1 (Breadcrumb)"],
                       data["Original Data Column 2 (Ausführung)"], data["Supplier Article Number"],
                       data["EAN/GTIN"], data["Article Number"], data["Product Description"],
                       data["Supplier"], data["Supplier-URL"], data["Product Image URL"],
                       data["Manufacturer"], data["Original Data Column 3 (Add. Description)"],
                       datetime.now())
    await conn.close()

async def get_scraped_urls():
    conn = await asyncpg.connect(**DB_CONFIG)
    rows = await conn.fetch("SELECT supplier_url FROM products")
    urls = {row["supplier_url"] for row in rows}
    await conn.close()
    return urls

async def fetch_page(session, url):
    try:
        async with session.get(url, ssl=False) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Помилка завантаження {url}: статус {response.status}")
                return None
    except Exception as e:
        print(f"Помилка при завантаженні {url}: {e}")
        return None

async def scrape_catalog(session, url):
    product_links = []

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)

        # Очікування, поки продукти завантажаться на сторінці
        await page.wait_for_selector("div[data-testid='product-card']")

        # Очікування, поки зникне спінер завантаження
        await page.wait_for_selector("div.ant-spin-spinning", state="hidden")

        # Збір посилань на продукти
        product_elements = await page.query_selector_all("div[data-testid='product-card']")
        for product in product_elements:
            link_tag = await product.query_selector("a")
            if link_tag:
                product_url = await link_tag.get_attribute("href")
                if product_url:
                    product_links.append(product_url)
                else:
                    print("URL не знайдено у <a> тегу.")
            else:
                print("Тег <a> не знайдено у продукті.")
                print(await product.inner_html())  # Log the HTML content of the product element

        await browser.close()
    print(f"Знайдено {len(product_links)} посилань на продукти.")
    print(product_links)
    return product_links


async def main():
    catalog_url = "https://store.igefa.de/c/waschraum-hygiene/AycY6LWMba5cXn5esuFfRL"
    async with aiohttp.ClientSession() as session:
        product_links = await scrape_catalog(session, catalog_url)

        if product_links:
            print(f"Знайдено {len(product_links)} товарів.")
        else:
            print("Не вдалося знайти продукти.")

async def scrape_product(session, url):
    html = await fetch_page(session, url)
    if html is None:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    name_tag = soup.find("span", {"data-testid": "productCard_productName"})
    name = name_tag.text if name_tag else "Невідомо"

    print(f"Назва продукту: {name}")

    img_tag = soup.find("div", class_="ProductCard_imageHolder__f4e96").find("img")
    img_url = img_tag['src'] if img_tag else None

    print(f"URL зображення: {img_url}")

    # Зчитуємо артикул товару
    sku_tag = soup.find("div", {"data-testid": "product-information-sku"})
    sku = sku_tag.text if sku_tag else "Невідомо"

    print(f"Артикул: {sku}")

    if name == "Невідомо" and img_url is None and sku == "Невідомо":
        print(f"Не вдалося отримати дані для: {url}")
        return None

    return {
        "Product Name": name,
        "Product Image URL": img_url,
        "Supplier Article Number": sku,
        "Product URL": url
    }

async def save_to_csv(products, filename="products.csv"):
    keys = products[0].keys()
    with open(filename, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=keys)
        writer.writeheader()
        writer.writerows(products)
    print(f"Дані збережено у файл {filename}")

asyncio.run(main())
