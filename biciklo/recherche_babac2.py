#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import re
import yaml
import argparse


config_file = 'config.yml'
base_url = 'https://cyclebabac.com/'

sku_pattern = re.compile('\d{2}[-]?\d{3}$')  # accept 12-345 or 12345, but not 123456 or 1234
text_pattern = re.compile('[\w0-9 \"()]+') # accept text, numbers and special characters ", ( and )
price_pattern = re.compile('\d*[.]\d{2}')


def do_the_search(search_text):

    username, password, login_url = load_config(config_file)
    session = create_session(username, password, login_url, base_url)
    result_page, single_result = search_item(session, search_text, base_url)
    soup_results = make_soup(result_page)

    list_products, search_type = parse_results(soup_results, single_result, search_text, sku_pattern, text_pattern, price_pattern)

    return list_products


def load_config(config_file):

    with open(config_file, 'r') as config:
        yml_file = yaml.safe_load(config)

    username = yml_file['login']['username']
    password = yml_file['login']['password']
    login_url = yml_file['login']['url']

    return username, password, login_url


def create_session(username, password, login_url, base_url):

    loggedin_confirmation = 'wordpress_logged_in_'

    with requests.Session() as session:
        headers = {'Cookie': 'wordpress_test_cookie=WP+Cookie+check',
                   'Referer': base_url,
                   'User-Agent': 'Atelier Biciklo'
                   }
        data={
            'log':username, 'pwd':password, 'wp-submit':'Log In',
        }
        response = session.post(login_url, headers=headers, data=data, allow_redirects=False)

        if loggedin_confirmation in response.headers['Set-Cookie']:
            return session
        else:
            print('Could not log in. Exiting.')
            exit(0)


def search_item(session, search_text, base_url):

    product_cat = ''
    post_type = 'product'

    if search_text != None:
        search_dict = {'product_cat': product_cat, 'post_type': post_type, 's': search_text}
    else:
        search_dict = {}

    result_page = session.get(base_url, params=search_dict )

    if result_page.history:
        single_result = True
    else:
        single_result = False

    return result_page, single_result


def make_soup(result_page):

    soup_results = BeautifulSoup(result_page.text, 'lxml')

    return soup_results


def parse_results(soup_results, single_result, search_text, sku_pattern, text_pattern, price_pattern):

    if single_result == True:
        if sku_pattern.match(search_text):
            search_type = 'sku_only'
            search_text = search_text[:2] + '-' + search_text[-3:]
        elif text_pattern.match(search_text):
            search_type = 'single_text'
        else:
            search_type = 'error'
            list_products = None
            # do something to stop the parsing

        list_products = parse_single_result(soup_results, search_text, sku_pattern, price_pattern)

    else:
        if text_pattern.match(search_text):
            search_type = 'multiple_text'
            list_products = parse_multiple_results(soup_results, search_text, sku_pattern, price_pattern)
        else:
            search_type = 'error'
            list_products = None
            # do something to stop the parsing

    return list_products, search_type


def parse_single_result(soup_results, search_text, sku_pattern, price_pattern):

    list_products = []

    item_sku = soup_results.find('span', {'class': 'sku'}).text
    item_name = soup_results.title.text[:-14]
    item_prices = soup_results.find('p', {'class': 'price'})

    if item_prices.find('del') == None:
        item_rebate = False
        item_price = item_prices.find('span', {'class': 'woocommerce-Price-amount amount'}).text

    else:
        item_rebate = True
        price_pattern = re.compile('\d*[.]\d{2}')
        item_price = item_prices.find_all('span', {'class': 'woocommerce-Price-amount amount'})[1].text
        item_price = re.findall(price_pattern, item_price)[0]

    is_instock = soup_results.find('span', {'class': 'stock_wrapper'}).span.text.lstrip().rstrip()

    if is_instock == 'In stock':
        item_instock = 'Yes'
    elif is_instock == 'Out of stock':
        item_instock = 'No'
    else:
        item_instock = 'Don\'t know'

    product_info = build_product_info(item_sku, item_name, item_price, item_instock, item_rebate)

    list_products.append(product_info)

    return list_products


def parse_multiple_results(soup_results, search_text, sku_pattern, price_pattern):

    list_products = []

    section_products = soup_results.find_all('div', {'class': 'kw-details clearfix'})

    for item in section_products:
        product_info = parse_info(item, sku_pattern, soup_results)
        list_products.append(product_info)

    return list_products


def parse_info(item, sku_pattern, soup_results):

    item_sku = item.find('div', {'class': 'mg-brand-wrapper mg-brand-wrapper-sku'}).text.lstrip().rstrip()
    item_sku = re.findall(sku_pattern, item_sku)[0]
    item_name = item.find('h3', {'class': 'kw-details-title text-custom-child'}).text.lstrip().rstrip()
    item_prices = item.find('span', {'class': 'price'})

    if item_prices.find('del') == None:
        item_rebate = False
        item_price = item_prices.find('span', {'class': 'woocommerce-Price-amount amount'}).text.strip('$')

    else:
        item_rebate = True
        price_pattern = re.compile('\d*[.]\d{2}')
        item_price = item_prices.find_all('span', {'class': 'woocommerce-Price-amount amount'})[1].text.strip('$')
        item_price = re.findall(price_pattern, item_price)[0]

    item_instock = 'Don\'t know'

    is_instock = soup_results.find('div', {'class': 'mg-brand-wrapper mg-brand-wrapper-stock'}).text.lstrip().rstrip()[20:]
    if is_instock == 'In stock':
        item_instock = 'Yes'
    elif is_instock == 'Out of stock':
        item_instock = 'No'
    else:
        item_instock = 'Don\'t know'

    product_info = build_product_info(item_sku, item_name, item_price, item_instock, item_rebate)

    return product_info


def build_product_info(item_sku, item_name, item_price, item_instock, item_rebate):

    product_info = {'sku': item_sku,
                    'name': item_name,
                    'price': item_price,
                    'stock': item_instock,
                    'rebate': str(item_rebate)
                    }

    return(product_info)


def print_results(list_products):

    if len(list_products) > 1:
        print('{} items were found'.format(len(list_products)))

    elif len(list_products) == 1:
        print('A single item was found')

    else:
        print('No product found')
        exit(0)

    print('| #Babac | ' + 'Description'.ljust(45, ' ') + ' | Price    | In stock? |')
    print('| ------ | ' + '-'*45 + ' | -------- | --------- |')

    for item in list_products:
        print('| {} | {} | {}$ | {} |'.format(
          item['sku'],
          item['name'].ljust(45, ' ')[:45],
          item['price'].rjust(7),
          item['stock'].ljust(9)
          )
        )


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('search_text', help='indicate which term(s) you are using to search in the Babac catalogue', default='')
    args = parser.parse_args()


    search_text = args.search_text

    username, password, login_url = load_config(config_file)
    session = create_session(username, password, login_url, base_url)
    result_page, single_result = search_item(session, search_text, base_url)
    soup_results = make_soup(result_page)

    list_products, search_type = parse_results(soup_results, single_result, search_text, sku_pattern, text_pattern, price_pattern)

    print_results(list_products)


if __name__ == '__main__':
    main()
