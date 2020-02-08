import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime
import re
import os
import openpyxl
import requests
from tqdm import tqdm


def logging(text):
    print(text)
    with open('logs.txt', 'a') as f:
        f.write(text + '\n')

  
# читает данные из db sqlite3
def read_from_db(db_connect):
    con = sqlite3.connect(db_connect)

    past_auctions = pd.read_sql_query('select * from past_auctions', con)    
    auctions = pd.read_sql_query('select * from auctions', con)
    
    con.close()  

    return auctions, past_auctions


def make_xlsx_report(auctions, past_auctions, file_out='report.xlsx'):
    date = auctions['date'].tolist() + past_auctions['date'].tolist()
    date = np.unique(date)

    def del_brackets(t):
        # удаляй выражения в скобках
        text = re.sub(r'\([^()]*\)', '', t).strip()  
        if text == '':
            # выбирай выражение в скобках
            text = re.search(r'\([^()]*\)', t).group(0)[1:-1].strip() 

        return text
    
    # удаляй данные в скобках
    auctions['adress_data'] = auctions['adress'].apply(del_brackets)
    past_auctions['adress_data'] = past_auctions['adress'].apply(del_brackets)

    # Добавление данных к адресу
    auctions['adress_data'] = auctions.apply(lambda x: 
        '{}\nком. {}, пл. {} м2'.format(x['adress_data'], x['rooms'], x['square']), axis=1)
    past_auctions['adress_data'] = past_auctions.apply(lambda x: 
        '{}\nком. {}, пл. {} м2'.format(x['adress_data'], x['rooms'], x['square']), axis=1)

    adress = auctions['adress_data'].tolist() + past_auctions['adress_data'].tolist()
    adress = np.unique(adress)

    df = pd.DataFrame(index=adress,columns=date)

    # Заполнение данными таблицы
    for _, row in past_auctions.iterrows():
        date = row['date']
        adress = row['adress_data']
        if row['final_price'] == 0:
            df.loc[adress, date] = '{} /\nНе продано'.format(row['begin_price'])
        else:
            df.loc[adress, date] = '{} /\n{}'.format(row['begin_price'], row['final_price'])
            df.loc[adress, :].fillna('x  x  x\nx  x  x', inplace=True)
        
    for _, row in auctions.iterrows():
        date = row['date']
        adress = row['adress_data']
        df.loc[adress, date] = '{}\n{}'.format(row['price'], row['link'])
                
    df.to_excel(file_out)     
    
    # Format .xlsx file    
    wb = openpyxl.load_workbook(file_out)
    sheet = wb['Sheet1']
    
    for i in range(2, len(df.index) + 2):
        sheet.row_dimensions[i].height = 30
    
    sheet.column_dimensions['A'].width = 20
    for i in range(2, len(df.columns) + 2):
        letter = openpyxl.utils.get_column_letter(i)
        sheet.column_dimensions[letter].width = 10
    
    sheet.freeze_panes = sheet['B2']
    
    wb.save(file_out)    


def geocoder(addr, key):   
    url = 'https://geocode-maps.yandex.ru/1.x'
    params = {'format':'json', 'apikey': key, 'geocode': addr}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print('Non-200 response from yandex geocoder')
    
    coordinates = response.json()["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"]
    lon, lat = coordinates.split(' ')
    
    return lon, lat



def make_yandex_map(auctions, past_auctions, file_out='yandex.map.csv'):
    date = auctions['date'].tolist() + past_auctions['date'].tolist()
    date = np.unique(date)

    def make_adress(addr, room, sq):
        addr = addr.replace('(реновация)', '')
        temp = addr.split('кв.')
                
        if len(temp) == 2:
            addr, temp = temp
        else:
            try:
                # выбирай выражение в скобках
                addr = re.search(r'\([^()]*\)', addr).group(0)[1:-1]
            except:
                pass
            temp = addr.split('кв.')
            addr = temp[0]
            temp = temp[1]
                    
        return '{}_{}_ком., пл. {}, кв. {}'.format(addr, room, sq, temp)
        
    # Добавление данных к адресу
    auctions['adress_data'] = auctions.apply(lambda x: 
        make_adress(x['adress'], x['rooms'], x['square']), axis=1)
    past_auctions['adress_data'] = past_auctions.apply(lambda x: 
        make_adress(x['adress'], x['rooms'], x['square']), axis=1)

    adress = auctions['adress_data'].tolist() + past_auctions['adress_data'].tolist()
    adress = np.unique(adress)

    df = pd.DataFrame(index=adress,columns=date)

    # Заполнение данными таблицы
    for _, row in past_auctions.iterrows():
        date = row['date']
        adress = row['adress_data']
        if row['final_price'] == 0:
            df.loc[adress, date] = [row['begin_price'], 'Не продано']
        else:
            df.loc[adress, date] = [row['begin_price'], row['final_price']]
        
    for _, row in auctions.iterrows():
        date = row['date']
        adress = row['adress_data']
        df.loc[adress, date] = [row['price'], 'Аукцион']


    # Формирование адресов для Яндекс карт
    df_T = df.T

    latitude, longitude, description, label, placemark_number = [],[],[],[],[]

    with open('yandex.key.txt', 'r') as f:
        key = f.read()

    for col in tqdm(df_T.columns):
        addr, room, other_data = col.split('_')

        # Долгота и широта из адресса
        lon, lat = geocoder(addr, key)
        
        latitude.append(lat)
        longitude.append(lon)

        # Описание
        temp = df_T.loc[df_T[col].isna()==False, col]       
        d = ''
        for i in reversed(range(temp.size)):
            d += '<div>{}: {} | {}</div>'.format(temp.index[i], temp[i][0], temp[i][1])
        d += '<p>' + addr + room + other_data + '</p>'
        description.append(d)
                
        # Заголовок (цена продажи, дата продажи, с какого раза продано)
        if type(temp[-1][1]) == int:
            l = '{:,}'.format(temp[-1][1]).replace(',', '.') + ', {}, {}'.format(temp.index[-1].year, temp.size)
        else:
            l = '{}, {}, {}'.format(temp[-1][1], temp.index[-1].year, temp.size)
        label.append(l)
        
        # Количество квартир
        placemark_number.append(room)
        
    sub = pd.DataFrame({'Latitude':latitude, 
                        'Longitude':longitude,
                        'Description':description, 
                        'Label':label,
                        'Placemark number':placemark_number})

    sub.to_csv(file_out, index=False)



def main():   
    files = os.listdir(path='db')
    if len(files) == 0:
        logging('Scrap data first, run msgr_parser.py')
        return

    files = sorted(files)

    db_connect = 'db/' +  files[-1]
    
    logging('Read data from ' + db_connect + '...')    
    auctions, past_auctions = read_from_db(db_connect)


    logging('Prepare data...')
    def to_float(text):
        t = text.replace(',', '.')
        # удаляй выражения в скобках
        text = re.sub(r'\([^()]*\)', '', t).strip()  
        if text == '':
            # выбирай выражение в скобках
            text = re.search(r'\([^()]*\)', t).group(0)[1:-1].strip() 

        return float(text)
    
    auctions['date'] = auctions['date'].apply(lambda x: datetime.strptime(x[:10], '%d.%m.%Y').date())
    auctions['adress'] = auctions['adress'].apply(lambda x: re.sub(r'\s+', '', x.lower()))
    auctions['rooms'] = auctions['rooms'].astype(int)
    auctions['square'] = auctions['square'].apply(to_float)
    auctions['living_space'] = auctions['living_space'].apply(to_float)
    auctions['price'] = auctions['price'].astype(int)
    auctions['deposit'] = auctions['deposit'].astype(int)
    auctions['step'] = auctions['step'].astype(int)
    
    past_auctions['date'] = past_auctions['date'].apply(lambda x: datetime.strptime(x, '%d.%m.%Y').date())
    past_auctions['adress'] = past_auctions['adress'].apply(lambda x: re.sub(r'\s+', '', x.lower()))
    past_auctions['rooms'] = past_auctions['rooms'].astype(int)
    past_auctions['square'] = past_auctions['square'].apply(to_float)
    past_auctions['living_space'] = past_auctions['living_space'].apply(to_float)    
    past_auctions['begin_price'] = past_auctions['begin_price'].astype(int)
    past_auctions['final_price'] = past_auctions['final_price'].apply(lambda x: int(x) if x.isdigit() else 0)


    # Последние десять дней.
    # date = auctions['date'].tolist() + past_auctions['date'].tolist()
    # date = np.unique(date)
    # past_auctions = past_auctions[past_auctions['date'].isin(date[-10:])]

    logging('Create .xlsx file...')
    make_xlsx_report(auctions, past_auctions)

    logging('Create .csv for Yandex map...')
    make_yandex_map(auctions, past_auctions)

    logging('End.')
        

if __name__ == '__main__':
    main()




