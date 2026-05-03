from collections import deque


def word_score(word):
    if len(word) <= 3:
        return len(word)
    else:
        return 3 + sum(range(2, len(word) - 1))


def validate_turn(word, letters, replacement_count, next_letters):
    # Check if each letter in the word exists in the letters
    for letter in set(word):
        if letter not in letters:
            return False, None

    # Build validation board for the next turn
    validation_board = list(letters)
    for letter in set(word):
        if letter in validation_board:
            validation_board.remove(letter)

    # Replace letters with next letters
    for _ in range(replacement_count):
        if next_letters:
            validation_board.append(next_letters.popleft())
        else:
            validation_board.append(" ")

    return True, "".join(validation_board)


def validate_game(validation_data, next_letters):
    score = 0
    next_letters = deque(next_letters)
    for idx, turn_data in enumerate(validation_data):
        word, letters, replacement_count = turn_data
        print(word)
        print(letters)
        print(replacement_count)
        if replacement_count < 3:
            return 0
        score += word_score(word)
        is_valid, validation_board = validate_turn(
            word, letters, replacement_count, next_letters
        )
        if not is_valid:
            return 0

        # Check if next turn letters are contained in current validation board
        if idx + 1 < len(validation_data):
            next_turn_letters = set(validation_data[idx + 1][1])
            if not all(letter in validation_board for letter in next_turn_letters):
                return 0

    return score


def get_next_letters(puzzleNumber):
    with open("nextletters.txt", "r") as file:
        lines = file.readlines()
        if puzzleNumber < len(lines):
            next_letters = lines[puzzleNumber].strip()
        else:
            next_letters = None
    return next_letters


next_letters = [
    "m",
    "a",
    "n",
    "e",
    "w",
    "qu",
    "i",
    "c",
    "o",
    "m",
    "y",
    "u",
    "s",
    "a",
    "c",
    "m",
    "e",
    "qu",
    "i",
    "w",
    "d",
    "o",
    "t",
    "u",
    "l",
    "s",
    "a",
    "d",
    "e",
    "m",
    "l",
    "i",
    "f",
    "o",
    "p",
    "w",
    "u",
    "g",
    "a",
    "t",
    "w",
    "e",
    "v",
    "i",
    "y",
    "c",
    "o",
    "s",
    "u",
    "n",
]
validation_data = [
    ["suds", "ceosiwptsmeludna", 3],
    ["name", "ceosiwptmmelanna", 4],
    ["quin", "ceosiwptmquilwena", 3],
    ["coma", "ceosiwptmcolwema", 4],
    ["yes", "ceosiwptmyulwesa", 3],
    ["post", "ceosiwptmculwmea", 4],
    ["quid", "ceiwiwqudmculwmea", 3],
    ["toe", "cetwiwoumculwmea", 3],
    ["las", "calwiwsumculwmea", 3],
    ["cum", "cedwiwmumculwmea", 3],
    ["life", "cedwiwmumlilwfea", 4],
    ["pom", "cedwiwmumlpowwua", 3],
    ["wet", "cedwiwtumlgawwua", 3],
    ["glim", "cedwiwvumlgawwua", 4],
    ["cow", "cedwcwvuoyiawwua", 3],
    ["sun", "cedwsnvuuyiawwua", 3],
    ["dev", "cedwvuyiawwua", 3],
]
print(validate_game(validation_data, next_letters))  # Returns True or False
