import csv
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import List, Literal, NamedTuple, Union, Optional

PHONEBOOK_FILE_PATH = Path('pb.csv')
DEFAULT_PAGE_SIZE = 5


def get_answer(
	prompt: str, correct_answers: Union[list, range]) -> str or None:
	"""
	Вспомогательная функция для валидации ввода пользователя
	:param prompt: подсказка которая выводится перед вводом данных
	:param correct_answers: массив или диапазон валидных ответов
	"""
	answer = None
	print(prompt + ' ', end='')
	while answer not in correct_answers:
		answer = input()
		if answer == '':
			return None
		if answer.isnumeric():
			answer = int(answer)
		if answer in correct_answers:
			return answer
		print('Введено неверное значение, попробуйте ещё раз: ', end='')


class SearchCondition(NamedTuple):
	field: str
	text: str


class Field(NamedTuple):
	title_en: str
	title_ru: str


field_map = {
	1: Field('index', '№'),
	2: Field('last_name', 'Фамилия'),
	3: Field('name', 'Имя'),
	4: Field('middle_name', 'Отчество'),
	5: Field('organization', 'Организация'),
	6: Field('work_phone', 'Рабочий телефон'),
	7: Field('private_phone', 'Личный телефон')
}

csv_fields = [field.title_ru for field in field_map.values()]
contact_fields = [field.title_en for field in field_map.values()]


@dataclass
class Contact:
	index: int
	last_name: str = ""
	name: str = ""
	middle_name: str = ""
	organization: str = ""
	work_phone: int = ""
	private_phone: int = ""
	
	@property
	def full_name(self) -> str:
		return f'{self.last_name} {self.name} {self.middle_name}'
	
	@property
	def data_row(self) -> List[str]:
		return list(self.__dict__.values())


class Storage(ABC):
	"""Базовый класс для хранилища"""
	
	def save_all(self, contacts: List[Contact]) -> None:
		"""Сохраняет все переданные контакты в файл"""
		pass
	
	def add_one(self, contact: Contact) -> None:
		"""Добавляет контакт в файл"""
		pass
	
	def read_all(self) -> List[Contact]:
		"""Считывает все контакты из файла"""
		pass


class CsvFileStorage(Storage):
	"""Хранилище на основе csv-файла"""
	
	def __init__(self, file_path: Path):
		self.file_path = file_path
		self._init_storage()
	
	def _init_storage(self) -> None:
		"""
		Проверяет нахождение файла по указанному пути и если файл не найден -
		создаёт его
		"""
		if not self.file_path.exists():
			with open(self.file_path, 'x') as file:
				writer = csv.DictWriter(file, fieldnames=csv_fields)
				writer.writeheader()
	
	def read_all(self) -> List[Contact]:
		with open(self.file_path) as file:
			reader = csv.DictReader(file)
			data = [
				[row[field] for field in csv_fields] for row in reader
			]
			return [Contact(*contact) for contact in data]
	
	def add_one(self, contact: Contact) -> None:
		with open(self.file_path, 'a') as file:
			file.write(','.join(map(str, contact.data_row)))
			print('Файл сохранён')
	
	def save_all(self, contacts: List[Contact]) -> None:
		with open(self.file_path, 'w') as file:
			writer = csv.DictWriter(file, fieldnames=csv_fields)
			rows = [self._to_csv(contact) for contact in contacts]
			writer.writeheader()
			writer.writerows(rows)
			print('Файл сохранён')
	
	@staticmethod
	def _to_csv(contact) -> dict:
		"""Конвертирует поля из датакласса в заголовки для файла csv"""
		csv_field_map = {x[0]: x[1] for x in field_map.values()}
		return {csv_field_map[k]: v for k, v in contact.__dict__.items()}


class ContactFormatter(ABC):
	"""
	Базовый класс для форматирования вывода.
	
	:param name: название формата для вывода в меню
	"""
	name = 'Base formatter'
	
	def print_contacts(
		self, contacts: List[Contact], page_size: int, paginate: bool) -> None:
		"""
		Выводит список контактов в консоль.
		
		Если параметр paginate = True, то вывод происходит постранично с
		количеством строк указанных в параметре page_size
		"""
		raise NotImplementedError


class ConsoleVisitCardFormatter(ContactFormatter):
	"""Класс для вывода контактов в виде визитных карточек"""
	
	name = 'Визитка'
	
	def print_contacts(self, contacts, paginate=True, page_size=1) -> None:
		contact_count = len(contacts)
		for contact in contacts:
			self._print_card(contact, contact_count)
			if paginate and int(contact.index) < contact_count:
				answer = input(
					'Нажмите Enter для продолжения или q для выхода в меню:')
				if answer == 'q':
					return None
	
	@staticmethod
	def _print_card(
		contact: Contact, contact_count: int, card_width=40) -> None:
		print('+', ''.center(card_width, '-'), '+')
		counter = ' '.join([str(contact.index), "/", str(contact_count)])
		print(f'| № {counter.ljust(card_width - 2)} |')
		print('|', contact.full_name.center(card_width), '|')
		print('|', ''.center(card_width), '|')
		if contact.organization:
			print(
				'|',
				(
					'Организация: ' + contact.organization
				).center(card_width),
				'|'
			)
		if contact.work_phone:
			print(
				'|',
				(
					'Рабочий телефон: ' + str(contact.work_phone)
				).center(card_width),
				'|'
			)
		if contact.private_phone:
			print(
				'|',
				(
					'Личный телефон: ' + str(contact.private_phone)
				).center(card_width),
				'|'
			)
		print('+', ''.center(card_width, '-'), '+')


class ConsoleTableFormatter(ContactFormatter):
	"""Класс для вывода контактов в консоль в форме таблицы"""
	name = 'Таблица'
	
	@staticmethod
	def _get_page_size() -> int:
		"""Запрашивает кол-во строк для вывода на странице"""
		print('Сколько записей отображать на одной странице ?')
		new_page_size = get_answer(
			f'Enter - значение по-умолчанию ({DEFAULT_PAGE_SIZE}):',
			range(1, 101)
		)
		if not new_page_size:
			return DEFAULT_PAGE_SIZE
		return new_page_size
	
	def print_contacts(
		self, contacts, page_size=DEFAULT_PAGE_SIZE, paginate=True) -> None:
		if len(contacts) > page_size:
			page_size = self._get_page_size()
		
		# Массивы с максимальными длинами полей по всем строкам с данными
		row_size_arrays = [
			[len(str(field)) for field in contact.data_row]
			for contact in contacts
		]
		# Максимальные длины строк по столбцам заголовка
		header_size_array = [len(field) for field in csv_fields]
		row_size_arrays.append(header_size_array)
		
		# Максимальные длины строк по столбцам данных
		max_column_len = list(
			map(lambda x: max(x), list(zip(*row_size_arrays)))
		)
		
		# Вывод заголовка таблицы
		self._print_table_divider(max_column_len)
		self._print_table_data_row(csv_fields, max_column_len)
		self._print_table_divider(max_column_len)
		
		contact_list = [contact.data_row for contact in contacts]
		
		for row in contact_list:
			self._print_table_data_row(row, max_column_len)
			if (
				paginate and
				int(row[0]) % page_size == 0 and
				int(row[0]) != len(contacts)
			):
				answer = get_answer(
					'Нажмите Enter чтобы продолжить или "q" для выхода',
					['', 'q']
				)
				if answer == 'q':
					break
		self._print_table_divider(max_column_len)
	
	@staticmethod
	def _print_table_data_row(
		data: List[str], column_len_array: List[int]) -> None:
		"""
		Выводит строки с данными из массива data по столбцам с шириной
		указанной соответственно этим столбцам в массиве column_len_array
		"""
		for field, max_len in zip(data, column_len_array):
			print(f"| {str(field).ljust(max_len + 1, ' ')}", end='')
		print('|')
	
	@staticmethod
	def _print_table_divider(column_len_array: List[int]) -> None:
		"""Выводит горизонтальный разделитель таблицы"""
		for column_width in column_len_array:
			print(f"+{'-' * (column_width + 2)}", end='')
		print('+')


class Phonebook:
	"""
	Класс для работы с телефонным справочником.
	:param formatter: класс для вывода контактов в определённом формате
	:param storage: класс обеспечивающий сохранение справочника
	"""
	
	def __init__(self, formatter: ContactFormatter, storage: Storage):
		self._storage = storage
		self._formatter = formatter
		self._contacts: List[Contact] = self._storage.read_all()
		self._last_index: int = len(self._contacts)
	
	def start(self):
		"""Основной цикл программы"""
		answer = ''
		while answer not in ['q', 'й']:
			self._print_main_menu()
			answer = input('Введите команду: ').lower()
			if answer in ['p', 'з']:
				self._formatter.print_contacts(self._contacts)
			elif answer in ['a', 'ф']:
				self._add_contact()
			elif answer in ['s', 'ы']:
				self._print_find_menu()
			elif answer in ['c', 'с']:
				self._change_contact()
			elif answer in ['d', 'в']:
				self._delete_contact()
			elif answer in ['f', 'а']:
				self._change_formatter()
			elif answer in ['q', 'й']:
				exit()
			else:
				print('Неверная команда')
				continue
			input('Нажмите Enter чтобы вывести меню\n')
	
	def _print_main_menu(self) -> None:
		"""Выводит главное меню"""
		print('-' * 40)
		print(' Телефонный справочник '.center(40, '-'))
		print('-' * 40)
		print(' p - Вывод всех контактов')
		print(' a - Добавить контакт в справочник')
		print(' s - Поиск контакта')
		print(' c - Изменить контакт')
		print(' d - Удалить контакт')
		print(' f - Изменить формат вывода')
		print(' q - Выход')
		print(''.center(40, '-'))
		print(f' Количество контактов в базе: {self._last_index}')
		print(f' Формат вывода: {self._formatter.name}')
		print(f' Количество элементов на странице: {DEFAULT_PAGE_SIZE}')
		print(''.center(40, '-'))
	
	def _add_contact(self) -> None:
		"""Добавляет контакт в справочник"""
		contact = Contact(index=self._last_index + 1)
		self._input_contact_data(contact, mode='add')
		print(''.center(40, '-'))
		print(f'Контакт "{contact.full_name}" успешно добавлен!')
		print(''.center(40, '-'))
		self._last_index += 1
		self._storage.add_one(contact)
	
	def _print_find_menu(self) -> None:
		"""Выполняет поиск"""
		print('Выберите режим поиска:')
		print(' 1 - поиск по всем полям')
		print(' 2 - поиск по определённым полям')
		answer = get_answer('Введите номер пункта:', [1, 2])
		if not answer:
			print()
			return
		if answer == '1':
			self._find_contacts_by_all_fields()
			return
		else:
			self._find_contacts_by_given_fields()
	
	def _find_contacts_by_given_fields(self):
		print('Выберите поля для поиска:')
		for idx, field in field_map.items():
			print(f' {idx} - {field.title_ru.lower()}')
		
		print(
			'Введите номера полей через пробел '
			'(Enter для возврата в меню): ', end='')
		search_field_indexes = self._get_field_indexes()
		if not search_field_indexes:
			print()
			return
		
		search_conditions = self._get_search_conditions(search_field_indexes)
		
		found_contacts = self._find_contacts_by_search_conditions(
			search_conditions)
		
		self._print_search_results(found_contacts)
	
	def _find_contacts_by_all_fields(self) -> None:
		"""Ищет контакты с совпадением в любых полях"""
		search = str(input('\nВведите строку для поиска: ')).lower()
		found_contacts = []
		for contact in self._contacts:
			for value in contact.__dict__.values():
				if search in value.lower() and contact not in found_contacts:
					found_contacts.append(contact)
		self._print_search_results(found_contacts)
	
	def _print_search_results(self, contacts: List[Contact]) -> None:
		"""Выводит результаты поиска"""
		if not contacts:
			print('Ничего не найдено')
			return
		print(f'Найдено совпадений {len(contacts)}:')
		self._formatter.print_contacts(contacts, paginate=False)
	
	def _change_contact(self) -> None:
		"""Изменяет данные контакта"""
		contact = self._get_contact_by_index()
		if not contact:
			return
		self._formatter.print_contacts([contact], paginate=False)
		self._input_contact_data(contact, mode='edit')
		message = f"Контакт '{contact.full_name}' изменён"
		print('-' * len(message))
		print(message)
		print('-' * len(message))
		self._storage.save_all(self._contacts)
	
	def _delete_contact(self) -> None:
		"""Удаляет контакт из справочника"""
		contact = self._get_contact_by_index()
		if not contact:
			return
		self._formatter.print_contacts([contact], paginate=False)
		answer = ''
		while answer not in ['n', 'н', 'y', 'д']:
			answer = input(
				'Вы уверены что хотите '
				'удалить этот контакт (Да/Нет)? '
			).lower()
			if answer in ['n', 'н', 'нет', 'no']:
				return
			elif answer in ['y', 'д', 'да', 'yes']:
				self._contacts.remove(contact)
				print('Контакт удалён')
				self._update_indexes()
				self._storage.save_all(self._contacts)
			else:
				print(
					'Неверный ввод. Введите "д"/"y" для подтвержения '
					'или "н"/"n" для отмены.'
				)
	
	def _change_formatter(self) -> None:
		"""Изменяет формат вывода"""
		if isinstance(self._formatter, ConsoleVisitCardFormatter):
			self._formatter = ConsoleTableFormatter()
		else:
			self._formatter = ConsoleVisitCardFormatter()
		print('Формат вывода изменён')
	
	def _input_contact_data(
		self, contact: Contact, mode: Literal['edit', 'add']) -> None:
		"""Добавленяет новый контакт или изменяет существующий"""
		if mode == 'add':
			print("Введите данные контакта:")
			self._contacts.append(contact)
		elif mode == 'edit':
			print(
				'Введите новые данные контакта\n'
				'(Enter - оставить старое значение,\n'
				'--- - удалить старое значение):')
		for field in field_map.values():
			if field.title_en == 'index':
				continue
			current_value = f"текущее значение: '{getattr(contact, field.title_en)} '" \
				if mode == 'edit' else ''
			data = input(f"{field.title_ru} {current_value}> ")
			if data != '':
				if data == '---':
					data = ''
				setattr(contact, field.title_en, data)
	
	def _get_contact_by_index(self) -> Contact or None:
		"""Возвращает контакт по индексу"""
		index = get_answer(
			'Введите индекс контакта:', range(1, self._last_index + 1))
		if not index:
			return None
		return self._contacts[int(index) - 1]
	
	def _update_indexes(self) -> None:
		"""Обновляет индексы всех контактов при удалении"""
		for idx, contact in enumerate(self._contacts, 1):
			contact.index = idx
		self._last_index = len(self._contacts)
	
	def _get_field_indexes(self) -> List[int]:
		"""Валидирует ввод индексов полей контатка"""
		search_field_indexes = []
		answer = ['_']
		while len(search_field_indexes) != len(answer):
			answer = input()
			answer = answer.split()
			search_field_indexes = list(
				map(
					lambda x: int(x.strip()),
					filter(
						lambda x: x.strip().isnumeric()
						          and int(x) in range(max(field_map.keys())),
						answer
					)
				)
			)
			if len(search_field_indexes) != len(answer):
				print('Введено неверное значение, попробуйте ещё раз: ', end='')
		return search_field_indexes
	
	@staticmethod
	def _get_search_conditions(
		search_field_indexes: List[int]) -> List[SearchCondition]:
		"""Возвращает критерии поиска введённые пользователем"""
		search_conditions = []
		print('Введите текст для поиска')
		for field in search_field_indexes:
			search_field_title = field_map[field].title_ru
			search_field = field_map[field].title_en
			search_text = input(f"Поле '{search_field_title}': ")
			search_conditions.append(
				SearchCondition(search_field, search_text)
			)
		return search_conditions
	
	def _find_contacts_by_search_conditions(
		self, search_conditions: List[SearchCondition]
	) -> List[Optional[Contact]]:
		"""Возвращает контакты соответствующие всем критериям поиска"""
		found_contacts = []
		for contact in self._contacts:
			matched_fields_count = 0
			for search in search_conditions:
				if search.text.lower() in getattr(contact, search.field).lower():
					matched_fields_count += 1
				if matched_fields_count == len(search_conditions) \
					and contact not in found_contacts:
					found_contacts.append(contact)
		return found_contacts


def main():
	pb = Phonebook(
		formatter=ConsoleTableFormatter(),
		storage=CsvFileStorage(Path.cwd() / PHONEBOOK_FILE_PATH)
	)
	pb.start()


if __name__ == "__main__":
	main()
