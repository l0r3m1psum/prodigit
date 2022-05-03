'''A simple program to automate the booking of classrooms at Sapienza during the
pandemic on [Prodigit](https://prodigit.uniroma1.it). Big thanks to Deborah for
doing the initial reverse engineering.'''
import urllib.request, http.cookiejar, json, datetime, multiprocessing.pool, sys

CONFIG_FNAME: str = 'conf.json'

BUILDING_CLASSROOMS_DB: dict[str, dict[str, str]] = {
	'RM018': {
		'AULA 1': 'AULA 1 -- RM018-E01PTEL013',
		'AULA 2': 'AULA 2 -- RM018-E01PTEL026',
		'AULA 3': 'AULA 3 -- RM018-E01PTEL025',
		'AULA 4': 'AULA 4 -- RM018-E01P01L010',
		'AULA 5': 'AULA 5 -- RM018-E01P02L011',
		'AULA 6': 'AULA 6 -- RM018-E01P02L022',
		'AULA 7': 'AULA 7 -- RM018-E01P02L021',
		'AULA 8': 'AULA 8 -- RM018-E01P03L010',
		'AULA 9': 'AULA 9 -- RM018-E01P03L011',
		'AULA 10': 'AULA 10 -- RM018-E01P03L012',
		'LAB A': 'LABORATORIO DIDATTICO DI FISICA (LADIFI) - LAB_ A -- RM018-E01P01L011',
		'LAB B': 'LABORATORIO DIDATTICO DI FISICA (LADIFI) - LAB_ B -- RM018-E01P01L014',
	},
	'RM102': {
		'AULA A1': 'AULA A1 -- RM102-PR1L006',
		'AULA A2': 'AULA A2 -- RM102-E01PR1L007',
		'AULA A3': 'AULA A3 -- RM102-E01PR1L008',
		'AULA A4': 'AULA A 4 -- RM102-E01PR1L009',
		'AULA A5': 'AULA A 5 -- RM102-E01PR1L012',
		'AULA A6': 'AULA A6 -- RM102-E01PR1L013',
		'AULA A7': 'AULA A7 -- RM102-E01PR1L015',
		'AULA B2': 'AULA B2 -- RM102-E01PR1L035',
		'AULA MAGNA': 'AULA MAGNA -- RM102-E01P01L001',
	},
	'RM115': {
		'AULA G0': 'AULA G0 -- RM115-E01PTEL008',
		'AULA G50': 'AULA G50 -- RM115-E01P03L001',
		'AULA MASTER': 'AULA MASTER -- RM115-E01PTEL006',
	},
}

WEEKDAY_TO_NUM: dict[str, int] = {
	'monday': 0,
	'tuesday': 1,
	'wednesday': 2,
	'thursday': 3,
	'friday': 4,
	'saturday': 5,
	'sunday': 6,
}
LAST_WEKDAY: int = WEEKDAY_TO_NUM['sunday']
MAX_DAY_AHEAD_FOR_BOOKING: int = 10

TIMEOUT: int = 10 # seconds
LOGIN_URL: str = 'https://prodigit.uniroma1.it/names.nsf?Login'
BOOKING_URL: str = 'https://prodigit.uniroma1.it/prenotazioni/prenotaaule.nsf/prenotaposto-aula-lezioni'
LOGOUT_URL: str = 'https://prodigit.uniroma1.it/prenotazioni/prenotaaule.nsf?logout'
HEADERS: list[tuple[str, str]] = [
	('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'),
	('Connection', 'keep-alive'),
	('Content-Type', 'application/x-www-form-urlencoded'),
]
CLICK_MAGIC: str = 'C12585E7003519C8.c8e9f943d3b2819fc12587ed0064a0a2/$Body/2.9F0'

def main() -> int:
	try:
		with open(CONFIG_FNAME) as config_file:
			configuration = json.load(config_file)
	except FileNotFoundError as e:
		print('unable to find the configuration file', file=sys.stderr)
		return 1

	# The loging endpoint rediricts us various times, in the last redirect gives
	# as the cookies we need, so to avoid having to keep track of redirections
	# we collect all cookies.
	cj = http.cookiejar.CookieJar()
	opener = urllib.request.build_opener(
		urllib.request.HTTPCookieProcessor(cj)
	)
	opener.addheaders = HEADERS

	# Fetching the cookie needed for authentication
	login_data = urllib.parse.urlencode(configuration['auth']).encode()
	try:
		login_resp = opener.open(LOGIN_URL, login_data, TIMEOUT)
	except urllib.error.URLError as e:
		print('unable to login', file=sys.stderr)
		return 1

	if login_resp.code != http.HTTPStatus.OK:
		print('something went wrong while trying to login', file=sys.stderr)

	for c in cj:
		if c.name == 'LtpaToken':
			ltpa_token = c
			break

	auth_cookie = ('Cookie', f'{ltpa_token.name}={ltpa_token.value}')
	opener.addheaders.append(auth_cookie)

	# We try to book classes starting from next week.
	current_day: int = datetime.datetime.today().weekday()
	day_offset: int = LAST_WEKDAY - current_day + 1
	assert day_offset > 0
	def book_class(booking: list[str]) -> None:
		day_of_week, building, classroom, from_hour, to_hour, description = booking
		classroom: str = BUILDING_CLASSROOMS_DB[building][classroom]
		days_from_now: int = WEEKDAY_TO_NUM[day_of_week] + day_offset
		if days_from_now > MAX_DAY_AHEAD_FOR_BOOKING:
			print(f'unable to book class for {day_of_week}')
			return
		# This order of paramenters seems to be mandatory
		booking_data: bytes = urllib.parse.urlencode([
			('__Click', CLICK_MAGIC),
			('codiceedificio', building),
			('aula', classroom), # must be quoted with plus
			(f'dalleore{days_from_now}', from_hour),
			(f'alleore{days_from_now}', to_hour),
		]).encode() + b'&'

		try:
			booking_resp = opener.open(BOOKING_URL, booking_data, TIMEOUT)
		except urllib.error.URLError as e:
			print(f'unable to book for {description}', file=sys.stderr)
			return

		if booking_resp.code != http.HTTPStatus.OK:
			print('something went wrong while trying to book for {description}', file=sys.stderr)
	with multiprocessing.pool.ThreadPool() as pool:
		pool.map(book_class, configuration['bookings'])

	# No data is needed for logout, just an empty POST request, also not sure if
	# logout is needed at all
	logout_data: bytes = bytes()
	try:
		logout_resp = opener.open(LOGOUT_URL, logout_data, TIMEOUT)
	except urllib.error.URLError as e:
		pass
	print('done! Check your inbox')

if __name__ == '__main__':
	raise SystemExit(main())
