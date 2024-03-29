from . import *

class UserInfo:
    def __init__(self) -> None:
        self.data: Dict[str, str] = {}

    def update(self, key: str, value: str) -> None:
        self.data[key] = value.capitalize()
        
    def reset(self) -> None:
        self.data.clear()

def ask_question(question: str, user_info: UserInfo) -> Generator[Tuple[str, Any], None, None]:
    yield question, user_info.data.get(question)

def process_survey(question_key: str, answer: str, user_info: UserInfo) -> Tuple[bool, bool]:
    user_info.update(question_key, answer)

    required_keys = ["Имя", "Опыт", "Цель", "Дополнительная информация"]
    if all(key in user_info.data for key in required_keys): # Проверка на соответствие ключей
        info = "\n".join([f'{x[0]}: {x[1]}' for x in user_info.data.items()]) # Вывод Dict -> str в удобном формате
        board_choice = f"\nВаша информация:\n{info}\n"
        print(board_choice)
        restart = input("Продолжить? (Введите Enter или '-' для прохождения опроса заново)\n")
 
        if restart == "-":
            print("Хорошо, начнем сначала")
            user_info.reset()
            return False, True # completed: False, restart: True
        return True, False # completed: True, restart: False
    return False, False # completed: False, restart: False

def gpt_generate(user_info: UserInfo) -> str:
    print("Генерирую ответ...\n")

    # Ввод user-промпта
    message = [
        {
            "role": "user", 
            "content": "\n".join([f'{x[0]}: {x[1]}' for x in user_info.data.items()]) # Ввод user_info.data в удобном формате
        }
    ]

    # Ввод system-промпта
    message.append(
        {
            "role": "system", 
            "content": """
                Отвечай объемно и исчерпывающе, исходя из формы ниже.
                Обязательно выводи сначала исходные данные пользователя.
                Имя: [Имя пользователя]
                Опыт: [Уровень опыта пользователя]
                Цель: [Цель использования сноуборда, например, фрирайд]
                Доп. информация: [Любая дополнительная информация, если она предоставлена; если указано "-" или нет данных, этот раздел опускается]

                Разумеется, [имя пользователя], я подберу для тебя идеальный сноуборд! На основании предоставленной информации, рекомендую обратить внимание на сноуборды следующих характеристик:

                - Предпочтительная длина доски: [диапазон длин, соответствующий росту и весу пользователя]
                - Ширина: [диапазон ширины, соответствующий размеру ботинок]
                - Жесткость: [уровень жесткости, предпочтительный для фрирайда и уровня опыта пользователя]
                - Форма: [описание подходящих форм досок для фрирайда и уровня опыта]
                - Технологии: [технологии, которые лучше подойдут для фрирайда и данного уровня опыта]

                Для размера ботинок, учитывая размер ноги пользователя, предлагаю следующие значения: [если это указано в доп.информации].

                Желаю тебе невероятных впечатлений и массу удовольствия на склонах, [имя пользователя]! Пусть каждый твой спуск будет наполнен радостью и мастерством!
            """
        }
    )

    # Генерация GPT запроса
    try:
        completion: ChatCompletion = gpt_client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=message,
            stream=False,
            max_tokens=4096
        )

    except BadRequestError:
        return "Повторите запрос позднее"
    except PermissionDeniedError:
        return "Включите VPN для корректной работы ChatGPT"
    except AuthenticationError:
        return "Неверный ключ API"
    except KeyboardInterrupt: 
        return "Отмена запроса"
    else:
        # Возврат успешной генерации
        return completion.choices[0].message.content
    
def chat_function(user_info: UserInfo) -> str:
    questions = {
        "Как тебя зовут?": "Имя",
        "Какой твой опыт катания на сноуборде?": "Опыт",
        "Для чего тебе нужна новая доска?": "Цель",
        "Любая дополнительная информация? (введи '-', чтобы пропустить)": "Дополнительная информация"
    }
    
    # Удобный вывод в терминал с соответствием ключей
    for question_prompt, question_key in questions.items():
        if question_key not in user_info.data:
            next(ask_question(question_key, user_info)) # использование генератора
            user_answer = input(question_prompt + "\n")
            completed, restart = process_survey(question_key, user_answer, user_info)

            if completed: # успешное прохождение запроса
                return gpt_generate(user_info)
            if restart: # требуется повторное прохождение опроса
                return ""

if __name__ == "__main__":
    user_info = UserInfo() # инициализация объекта класса UserInfo
    gpt_client = Client(api_key=api_key) # инициализация клиента GPT
    
    # Приветственное сообщение
    print("Привет! Я - Робот Алёша, я помогу выбрать тебе доску для сноуборда.\n"\
          "Но сначала мне нужно собрать некоторую информацию о тебе.\n")
    
    # Запуск опроса и генерации GPT
    while True:
        response = chat_function(user_info)
        
        if response:
            print(response)
            break