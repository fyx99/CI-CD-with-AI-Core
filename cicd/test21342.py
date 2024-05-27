import time
import random
from blessed import Terminal

# Sample function to generate a random status for demonstration
def generate_status():
    return f"Status: {random.randint(1, 100)}"

# Main function to run the blessed application
def main():
    print("hi")
    print("hi")
    print("hi")
    print("hi")
    print("hi")
    term = Terminal()
    statuses = [generate_status() for _ in range(10)]

    with term.fullscreen():
        while True:
            statuses = [generate_status() for _ in range(10)]

            for i, status in enumerate(statuses):
                with term.location(0, i):
                    print(term.clear_eol + status)

            time.sleep(1)

if __name__ == "__main__":
    main()