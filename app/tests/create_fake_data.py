import os

import requests
from dotenv import load_dotenv

load_dotenv()

username = "james"
password = "helloworld"
base = "http://localhost:5000/"


# TODO: Add categories
def create_articles():
    url = f"{base}articles/add"

    lis = [
        {
            "title": "Flashcards",
            "content": """
            <summary>A flashcard or flash card is a card bearing information on both sides, which is intended to be used as an aid in memorization.</summary> Each flashcard bears a question on one side and an answer on the other. Flashcards are often used to memorize vocabulary, historical dates, formulas or any subject matter that can be learned via a question-and-answer format. Flashcards can be virtual (part of a flashcard software), or physical.

Flashcards are an application of the testing effect − the finding that long-term memory is increased when some of the learning period is devoted to retrieving the information through testing with proper feedback. Study habits affect the rate at which a flashcard-user learns, and proper spacing of flashcards has been proven to accelerate learning. A number of <span class='concept'>spaced repetition</span> software programs exist which take advantage of this principle.
            
            """,
            "author": "Wikipedia",
            "published": True,
            "finished_confidence": 5
        },
        {
            "title": "Testing Effect",
            "content": """
                <summary>The testing effect is the finding that long-term memory is often increased when some of the learning period is devoted to retrieving the to-be-remembered information.</summary> The effect is also sometimes referred to as retrieval practice, practice testing, or test-enhanced learning. <span class='concept'>Retrieval practice</span> may be the best way to refer to the testing effect because the benefits of retrieval-related testing are not limited to tests. It can be more broad like flash cards or quizzes.The testing effect on memory should be distinguished from more general practice effects, defined in the APA Dictionary of Psychology (2007) as "any change or improvement that results from practice or repetition of task items or activities." The term testing effect is also sometimes used in a more general sense; The Oxford Dictionary of Psychology (2003) defines a testing effect as "any effect of taking tests on the respondents, a typical example being test sophistication." Whereas psychologists who develop tests for personality and intelligence want to avoid practice effects, cognitive psychologists working with educators have begun to understand how to take advantage of tests—not as an assessment tool, but as a teaching/learning tool.
                """,
            "author": "Wikipedia",
            "published": True,
            "finished_confidence": 5
        },
    ]

    for article in lis:
        r = requests.post(url, json=article, auth=(username, password))
        print(r)


if __name__ == '__main__':
    create_articles()