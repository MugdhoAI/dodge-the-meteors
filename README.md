# Dodge the Meteors

A simple arcade survival game built with Scratch for Harvard CS50x Problem Set 0.

## About

Dodge the Meteors is a survival game where you control a spaceship and avoid falling meteors.

You start with 3 lives. Each collision costs one life, while your score increases as you survive. Meteor speed gradually increases, making the game more difficult over time.

## How to play

1. Open `Dodge the Meteors - Mugdho.sb3` in the Scratch editor, at https://scratch.mit.edu, or in the offline Scratch app.
2. Click the green flag. The ship starts at the bottom of the stage with 3 lives and a score of 0.
3. Steer with the arrow keys and dodge the falling meteors.

## Scoring and difficulty

- Each meteor that reaches the bottom of the stage without hitting you adds 1 to your score.
- Each collision costs 1 life and the meteor respawns at the top.
- Every 10 seconds the meteor speed goes up by 1, starting from 5.
- When your lives drop below 1, the backdrop switches to Game Over and the game stops.

## Project layout

- `Dodge the Meteors - Mugdho.sb3`: the game itself, a Scratch 3 project file.
- `tools/validate_sb3.py`: checks that the .sb3 file is a valid archive, that every costume and sound file is present, and that every block reference resolves. Run it with `python3 tools/validate_sb3.py`.
- `tools/dump_scripts.py`: prints every sprite's scripts as readable text, for reviewing the game logic without opening Scratch. Run it with `python3 tools/dump_scripts.py`.
- `tests/`: unit tests for the tools above. Run them with `python3 -m unittest discover -s tests -v`. They need only the Python standard library.
- `docs/known-issues.md`: gameplay issues found by reading the scripts, with steps to fix each one in the Scratch editor.

## Controls

- Left Arrow: Move left
- Right Arrow: Move right
- Up Arrow: Move up
- Down Arrow: Move down

## Features

- Four-direction spaceship movement
- Randomly positioned falling meteors
- Three-life system
- Score tracking
- Increasing difficulty
- Game Over screen
- Custom Scratch block with an input parameter
- Collision detection
- Automatic meteor respawning

## Scratch Concepts

This project demonstrates variables, conditionals, loops, keyboard input, collision detection, random numbers, custom blocks, custom block parameters, game-state handling, and basic abstraction.

## Project File

The main project file is:

Dodge the Meteors - Mugdho.sb3

Open the .sb3 file with the Scratch editor to play or modify the project.

## Course

Harvard CS50x: Introduction to Computer Science

Problem Set 0: Scratch

## Author

Mugdho

GitHub: MugdhoAI

## License

Created for educational purposes as part of CS50x.
