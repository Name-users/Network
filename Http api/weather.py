import sys
from dataclasses import dataclass
from typing import List
import requests
import argparse


@dataclass
class ApiException(Exception):
    message: str


def get_weather(city: str, days_count: int, api_key: str) -> List[str]:
    if days_count > 7 or days_count < 1:
        return ['Invalid days count']
    response: requests.Response = None
    try:
        response = requests.get(f'http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&APPID={api_key}')
        lon = response.json()['coord']['lon']
        lat = response.json()['coord']['lat']
        url = f'https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units=metric&appid={api_key}'
        response = requests.get(url)
        result = []
        for i in range(days_count):
            string = '\n'.join([f"{value}: {response.json()['daily'][i]['temp'][value]} °C" for value in ['morn', 'day', 'night']])
            string += f"\nhumidity: {response.json()['daily'][i]['humidity']}\r\n"
            result.append(string)
        return result
    except KeyError:
        raise ApiException(response.json()['message'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='weather.py', description='Http-api weather')
    parser.add_argument('-c', '--city', type=str, default='Ekaterinburg')
    parser.add_argument('-r', '--range', type=int, default=1)
    args = parser.parse_args()
    try:
        api_key = ''
        with open('api_key.txt') as file:   # create this file with your api key
            api_key = file.read().strip()
        for string in get_weather(args.city, args.range, api_key):
            print(string)
    except ApiException as exc:
        print(exc.message)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(0)
