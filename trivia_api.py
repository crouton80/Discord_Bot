import requests
import random
import config


def fetch_question():
    response = requests.get(config.TRIVIA_API_URL).json()
    question_data = response['results'][0]
    
    question = question_data['question']
    correct_answer = question_data['correct_answer']
    all_answers = question_data['incorrect_answers'] + [correct_answer]
    random.shuffle(all_answers)

    return {
        'question': question,
        'correct_answer': correct_answer,
        'all_answers': all_answers
    }
