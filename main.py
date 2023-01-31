import requests
import collections
import os
from dotenv import load_dotenv
from terminaltables import SingleTable


def predict_salary(salary_from, salary_to) -> float:
    if salary_from and not salary_to:
        return salary_from * 1.2
    if not salary_from and salary_to:
        return salary_to * 0.8

    return (salary_from + salary_to) / 2


def predict_rub_salary_hh(vacancy):
    block_salary = vacancy['salary']
    return predict_salary(block_salary['from'], block_salary['to'])


def predict_rub_salary_sj(vacancy):
    return predict_salary(vacancy['payment_from'], vacancy['payment_to'])


def get_average_salaries_hh(languages: list):
    average_salaries = collections.defaultdict(dict)
    for language in languages:
        sum_salary, length_salaries, found_salaries = 0, 0, None
        page_count, hh_code_city = 10, 1
        for page in range(page_count):
            payload = {
                'text': f'Программист {language}',
                'period': 30,
                'area': hh_code_city,
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

            salaries, vacancies = [], response.json()
            for vacancy in vacancies['items']:
                if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
                    salaries.append(predict_rub_salary_hh(vacancy))

            sum_salary += sum(salaries)
            length_salaries += len(salaries)
            found_salaries = vacancies['found']

        average_salary = sum_salary / length_salaries if length_salaries else sum_salary
        average_salaries[language] = {
            'vacancies_found': found_salaries,
            'vacancies_processed': length_salaries,
            'average_salary': int(average_salary),
        }

    return average_salaries


def get_average_salaries_sj(languages: list, api_key):
    headers = {'X-Api-App-Id': api_key}
    average_salaries = collections.defaultdict(dict)

    for language in languages:
        sum_salary, length_salaries, found_salaries = 0, 0, 0
        page_count, sj_code_programming, sj_code_city = 5, 48, 832
        for page in range(page_count):
            payload = {
                'catalogues': sj_code_programming,
                'keyword': f'Программист {language}',
                't': sj_code_city,
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

            salaries, vacancies = [], response.json()['objects']
            for vacancy in vacancies:
                salary = predict_rub_salary_sj(vacancy)
                if not salary:
                    continue
                salaries.append(salary)
            sum_salary += sum(salaries)
            length_salaries += len(salaries)
            found_salaries += len(vacancies)

        average_salary = sum_salary / length_salaries if length_salaries else sum_salary
        average_salaries[language] = {
            'vacancies_found': found_salaries,
            'vacancies_processed': length_salaries,
            'average_salary': int(average_salary),
        }

    return average_salaries


def get_pretty_table(statistic, table_name):
    table_statistic = [
        ('Языки программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'),
    ]
    for language, stat in statistic.items():
        table_statistic.append(
            (language, stat['vacancies_found'], stat['vacancies_processed'], stat['average_salary'])
        )
    table_instance = SingleTable(table_statistic, table_name)
    return table_instance.table


def main():
    load_dotenv()
    programming_languages = ['javascript', 'java', 'python', 'ruby', 'php', 'c++', 'c#', 'go']

    print(get_pretty_table(get_average_salaries_sj(programming_languages, os.environ['SUPER_JOB_KEY']), 'SuperJob Moscow'))
    print(get_pretty_table(get_average_salaries_hh(programming_languages), 'HeadHunter Moscow'))


if __name__ == '__main__':
    main()
