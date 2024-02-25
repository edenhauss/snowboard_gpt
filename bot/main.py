from config import api_key
from typing import Dict, Tuple, Any, Generator
from openai import Client, BadRequestError, PermissionDeniedError, AuthenticationError
from openai.types.chat.chat_completion import ChatCompletion

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
    if all(key in user_info.data for key in required_keys):
        info = "\n".join([f'{x[0]} - {x[1]}' for x in user_info.data.items()])
        board_choice = f"\nВаша информация:\n{info}\n"
        print(board_choice)
        restart = input("Продолжить? (Введите Enter или '-' для прохождения опроса заново)\n")
 
        if restart == "-":
            print("Хорошо, начнем сначала")
            user_info.reset()
            return False, True
        return True, False
    return False, False

def gpt_generate(user_info: UserInfo) -> str:
    print("Генерирую ответ...\n")

    message = [
        {
            "role": "user", 
            "content": "\n".join([f'{x[0]} - {x[1]}' for x in user_info.data.items()])
        }
    ]

    message.append(
        {
            "role": "system", 
            "content": """Если в ответе нет информации, либо форма не имеет смысла,
            то ответь тем, что не хватает данных, обязательно не помогай в этом случае.
            В ответе обязательно должно быть перечисление информации о пользователе 
            в формате Имя:, Опыт:, Цель:, Доп.информация:(если вписано pass, либо 
            аналогичное, то не выводи доп.информацию). Затем после перечисления 
            информации напиши: 'Разумеется,  <имя пользователя>, я подберу для 
            тебя идеальный сноуборд!'. На основании предоставленной информации, подберите
            подходящие опции сноубордов, учитывая следующие параметры:
            предпочтительная длина доски, ширина, жесткость, форму и технологии,
            которые лучше подойдут для фрирайда и среднего уровня опыта
            пользователя. Также предложите значения для размера ботинок,
            подходящие под размер ноги пользователя. Ответ должен быть полным и объемным.
            В конце ответа пожелай удачи пользователю 
            с ноткой доброжелательности"""
        }
    )
    
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
        return completion.choices[0].message.content
    
def chat_function(user_info: UserInfo) -> str:
    questions = {
        "Как тебя зовут?": "Имя",
        "Какой твой опыт катания на сноуборде?": "Опыт",
        "Для чего тебе нужна новая доска?": "Цель",
        "Любая дополнительная информация? (введи 'pass', чтобы пропустить)": "Дополнительная информация"
    }
    
    for question_prompt, question_key in questions.items():
        if question_key not in user_info.data:
            next(ask_question(question_key, user_info))
            user_answer = input(question_prompt + "\n")
            completed, restart = process_survey(question_key, user_answer, user_info)

            if completed:
                return gpt_generate(user_info)
            if restart:
                return ""

if __name__ == "__main__":
    user_info = UserInfo()
    gpt_client = Client(api_key=api_key)
    print("Привет! Я - Робот Алёша, я помогу выбрать тебе доску для сноуборда.\n"\
          "Но сначала мне нужно собрать некоторую информацию о тебе.\n")
    while True:
        response = chat_function(user_info)
        if response:
            print(response)
            break