import requests
import collections
import os
from dotenv import load_dotenv
from terminaltables import SingleTable


def get_count_vacancies(languages: list):
    rate_lang = collections.defaultdict(int)
    for language in languages:
        payload = {
            'text': f'программист {language}',
            'area': 1,
            'period': 30,
        }
        response = requests.get(url='https://api.hh.ru/vacancies', params=payload)
        vacancies = response.json()
        rate_lang[language] = vacancies['found']

    return rate_lang


def predict_salary(salary_from, salary_to) -> float:
    if salary_from is not None and salary_from != 0:
        return salary_from * 1.2
    elif salary_to is not None and salary_to != 0:
        return salary_to * 0.8

    return (salary_from + salary_to) / 2


def predict_rub_salary_hh(vacancy):
    block_salary = vacancy['salary']
    if block_salary['currency'] != 'RUR':
        return

    return predict_salary(block_salary['from'], block_salary['to'])


def predict_rub_salary_sj(vacancy):
    salary = predict_salary(vacancy['payment_from'], vacancy['payment_to'])
    if not salary:
        return

    return salary


def get_average_salaries_hh(languages: list):
    average_salaries = collections.defaultdict(dict)
    for language in languages:
        sum_salary, length_salaries, found_salaries = 0, 0, None
        for page in range(10):
            payload = {
                'text': f'Программист {language}',
                'period': 30,
                'area': 1,
                'per_page': 100,
                'page': page,
            }
            try:
                response = requests.get(url='https://api.hh.ru/vacancies', params=payload)
                response.raise_for_status()
            except requests.exceptions.HTTPError as err:
                print(str(err))
                continue
            except requests.exceptions.ConnectTimeout as err:
                print(str(err))
                continue

            vacancies = response.json()['items']
            salaries = [predict_rub_salary_hh(vacancy) for vacancy in vacancies if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR']
            sum_salary += sum(salaries)
            length_salaries += len(salaries)
            found_salaries = response.json()['found']

        average_salary = sum_salary / length_salaries if length_salaries != 0 else sum_salary
        average_salaries[language] = {
            'vacancies_found': found_salaries,
            'vacancies_processed': length_salaries,
            'average_salary': int(average_salary),
        }

    return average_salaries


def get_average_salaries_sj(languages: list):
    headers = {'X-Api-App-Id': os.environ['SUPER_JOB_KEY']}
    average_salaries = collections.defaultdict(dict)

    for language in languages:
        sum_salary, length_salaries, found_salaries = 0, 0, 0
        for page in range(5):
            payload = {
                'catalogues': 48,
                'keyword': f'Программист {language}',
                't': 832,
                'currency': 'rub',
                'page': page,
                'count': 100,
            }
            try:
                response = requests.get(url='https://api.superjob.ru/2.0/vacancies/', headers=headers, params=payload)
                response.raise_for_status()

            except requests.exceptions.HTTPError as err:
                print(str(err))
                continue
            except requests.exceptions.ConnectTimeout as err:
                print(str(err))
                continue

            salaries = []
            for vacancy in response.json()['objects']:
                salary = predict_rub_salary_sj(vacancy)
                if not salary:
                    continue
                salaries.append(salary)
            sum_salary += sum(salaries)
            length_salaries += len(salaries)
            found_salaries += len(response.json()['objects'])

        average_salary = sum_salary / length_salaries if length_salaries != 0 else sum_salary
        average_salaries[language] = {
            'vacancies_found': found_salaries,
            'vacancies_processed': length_salaries,
            'average_salary': int(average_salary),
        }

    return average_salaries


def get_pretty_table(statistic, table_name):
    table_data = [
        ('Языки программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'),
    ]
    for language, stat in statistic.items():
        table_data.append(
            (language, stat['vacancies_found'], stat['vacancies_processed'], stat['average_salary'])
        )
    table_instance = SingleTable(table_data, table_name)
    return table_instance.table


def main():
    load_dotenv()
    programming_languages = ['javascript', 'java', 'python', 'ruby', 'php', 'c++', 'c#', 'go']

    print(get_pretty_table(get_average_salaries_sj(programming_languages), 'SuperJob Moscow'))
    print(get_pretty_table(get_average_salaries_hh(programming_languages), 'HeadHunter Moscow'))


if __name__ == '__main__':
    main()
