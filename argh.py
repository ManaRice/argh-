import sys
import time

class Position:
    '''
        A position is just a place in the Codebox, a coordinate.
        Made to override some operators as + and < for smoother
        code integration.
    '''
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y

    def __str__(self):
        return f"{self.y + 1}, {self.x + 1}"

    def __add__(self, other):
        if type(other) == Direction:
            return Position(self.x + other.xoffset, self.y + other.yoffset)
        if type(other == Position):
            return Position(self.x + other.x, self.y +  other.y)

    def __lt__(self, other):
        if type(other) == Direction:
            return self.x < other.xoffset or self.y < other.yoffset
        if type(other == Position):
            return self.x < other.x or self.y < other.y

    def __IADD__(self, other):
        if type(other) == Direction:
            return Position(self.x + other.xoffset, self.y + other.yoffset)
        if type(other == Position):
            return Position(self.x + other.x, self.y +  other.y)


class Direction:
    '''
        A Direction is an offset to an position that the
        interpreter can use to read the next instruction
        in that direction.
        Used to override some operators just as in Position
    '''
    def __init__(self, xoffset, yoffset):
        self.xoffset = xoffset
        self.yoffset = yoffset

    def __add__(self, other):
        if type(other) == Direction:
            return Direction(self.xoffset + other.xoffset, self.yoffset + other.yoffset)
        if type(other == Position):
            return Position(self.xoffset + other.x, self.yoffset +  other.y)

    def __IADD__(self, other):
        if type(other) == Direction:
            return Direction(self.xoffset + other.xoffset, self.yoffset + other.yoffset)
        if type(other == Position):
            return Position(self.xoffset + other.x, self.yoffset +  other.y)

# Some constants that the instructions and interpreter will use

EOF_CHAR = '\0'
SLOW = False
NORTH = Direction( 0, -1 )
WEST  = Direction( 1,  0 )
SOUTH = Direction( 0,  1 )
EAST  = Direction(-1,  0 )

# Instructions

class Instruction:
    '''
        Base class of an instruction. If there is and instance
        of this class it means that it is not an instruction
        that is runnable (whitespace, symbols etc.). Therefor
        if it is executed it will raise an exception.
    '''
    def __init__(self, char_value):
        self.char_value = char_value

    def handle(self, interpreter):
        raise Exception()

    def __str__(self):
        return chr(self.char_value)

class MoveInstruction(Instruction):
    '''
        Base class of a move instruction. Should not be directly
        instanced anywhere. Will make the interpreter change the
        direction to the specifyed direction. If the move
        instruction is an uppercase one, we will continue until
        the current position constains the same char as on the
        top of the stack.
    '''
    def handle(self, interpreter, dir):
        if chr(self.char_value).islower():
            interpreter.dir = dir
        else:
            interpreter.dir = dir
            interpreter.advance()
            while interpreter.get_current_instruction().char_value != interpreter.stack.peek():
                interpreter.advance()

# The instanceable MoveInstructions
class MoveNorth(MoveInstruction):
    def handle(self, interpreter):
        super().handle(interpreter, NORTH)

class MoveWest(MoveInstruction):
    def handle(self, interpreter):
        super().handle(interpreter, WEST)

class MoveSouth(MoveInstruction):
    def handle(self, interpreter):
        super().handle(interpreter, SOUTH)

class MoveEast(MoveInstruction):
    def handle(self, interpreter):
        super().handle(interpreter, EAST)

# Stack instructions

class StackAdd(Instruction):
    '''
        Will sum up the value of the character above
        (in case of uppercase instruction) or below
        (in case of a lowercase instruction)
        and the top value of the stack
    '''
    def handle(self, interpreter):
        if chr(self.char_value).islower():
            value = interpreter.stack.pop() + interpreter.get_instruction_at(SOUTH).char_value
        else:
            value = interpreter.stack.pop() + interpreter.get_instruction_at(NORTH).char_value

        interpreter.stack.append(value)

class StackReduce(Instruction):
    '''
        Will take the differance of the character above
        (in case of uppercase instruction) or below
        (in case of a lowercase instruction)
        and the top value of the stack
    '''
    def handle(self, interpreter):
        if chr(self.char_value).islower():
            value = interpreter.stack.pop() - interpreter.get_instruction_at(SOUTH).char_value
        else:
            value = interpreter.stack.pop() - interpreter.get_instruction_at(NORTH).char_value

        interpreter.stack.append(value)

class StackDropDupe(Instruction):
    '''
        Duplicates the top value of the stack
        ( Example:

            if stack == [5]:
                stack == [5, 5]
        )
    '''
    def handle(self, interpreter):
        if chr(self.char_value).islower():
            value = interpreter.stack.peek()
            interpreter.stack.append(value)
        else:
            interpreter.stack.pop()

class StackAppend(Instruction):
    '''
        Append (usually called push) the value
        of the character above or below the
        instruction depending on the case of
        the instruction letter.
    '''
    def handle(self, interpreter):
        if chr(self.char_value).islower():
            value = interpreter.get_instruction_at(SOUTH).char_value
        else:
            value = interpreter.get_instruction_at(NORTH).char_value

        interpreter.stack.append(value)

class CodeboxChange(Instruction):
    '''
        Push the value on top of the stack into
        the codebox above or below the instruction
        depending on the case of the instruction
        letter. That value will now be and instruction
        in the Codebox.
    '''
    def handle(self, interpreter):
        value = interpreter.stack.pop()
        if chr(self.char_value).islower():
            interpreter.set_instruction_at(SOUTH, instruction_create(value))
        else:
            interpreter.set_instruction_at(NORTH, instruction_create(value))

class CodeboxEOF(CodeboxChange):
    '''
        Push the value of EOF character (0)
        the codebox above or below the instruction
        depending on the case of the instruction
        letter. That value will now be and instruction
        in the Codebox. (Often used for checking
        if the input is done)
    '''
    def handle(self, interpreter):
        interpreter.stack.append(ord(EOF_CHAR))
        super().handle(interpreter)


class Userinput(CodeboxChange):
    '''
        Takes the Userinput and places it in a buffer
        that we take one letter from at a time until
        it is empty.
        FIXME: Make Userinput able to take more than one input
        at a time. If the buffer is empty and we encounter another
        Userinput, we will crash (check test/input.agh)
    '''
    def handle(self, interpreter):
        if interpreter.input == None:
            interpreter.input = list(input())
            interpreter.input.append(EOF_CHAR)

        interpreter.stack.append(ord(interpreter.input.pop(0)))
        super().handle(interpreter)

class Print(Instruction):
    def handle(self, interpreter):
        if chr(self.char_value).islower():
            value = interpreter.get_instruction_at(SOUTH).char_value
        else:
            value = interpreter.get_instruction_at(NORTH).char_value
        print(chr(value), end="", flush = True)

class Turn(Instruction):
    def handle(self, interpreter):
        top_value = interpreter.stack.peek()
        if chr(self.char_value).islower():
            if top_value > 0:
                interpreter.turn_right()
        else:
            if top_value < 0:
                interpreter.turn_left()

class Shebang(Instruction):
    def handle(self, interpreter):
        if interpreter.position == Position():
            if interpreter.get_instruction_at(WEST).char_value == ord('!'):
                interpreter.dir = SOUTH
        else:
            super().handle(interpreter)

class Quit(Instruction):
    def handle(self, interpreter):
        interpreter.running = False

def instruction_create(char_value):
    try:
        if chr(char_value).lower() == 'h':
            return MoveEast(char_value)
        elif chr(char_value).lower() == 'j':
            return MoveSouth(char_value)
        elif chr(char_value).lower() == 'k':
            return MoveNorth(char_value)
        elif chr(char_value).lower() == 'l':
            return MoveWest(char_value)
        elif chr(char_value).lower() == 'a':
            return StackAdd(char_value)
        elif chr(char_value).lower() == 'r':
            return StackReduce(char_value)
        elif chr(char_value).lower() == 'd':
            return StackDropDupe(char_value)
        elif chr(char_value).lower() == 's':
            return StackAppend(char_value)
        elif chr(char_value).lower() == 'f':
            return CodeboxChange(char_value)
        elif chr(char_value).lower() == 'e':
            return CodeboxEOF(char_value)
        elif chr(char_value).lower() == 'g':
            return Userinput(char_value)
        elif chr(char_value).lower() == 'p':
            return Print(char_value)
        elif chr(char_value).lower() == 'x':
            return Turn(char_value)
        elif chr(char_value).lower() == '#':
            return Shebang(char_value)
        elif chr(char_value).lower() == 'q':
            return Quit(char_value)
        else:
            return Instruction(char_value)
    except ValueError:
        return Instruction(char_value)

class Codebox:
    code_box = list()
    def __init__(self, code_box):
        width = 0
        for i, line in enumerate(code_box):
            row = list()
            for j, char in enumerate(line):
                row.append(instruction_create(ord(char)))
            width = max(width, len(row))
            self.code_box.append(row)

        for line in self.code_box:
            while len(line) < width:
                line.append(instruction_create(ord(' ')))

    def get_instruction_at(self, position):

        if position < Position():
            interpreter.argh()
        retult = None
        try:
            result = self.code_box[position.y][position.x]
        except IndexError:
            interpreter.argh()


        return result

    def set_instruction_at(self, position, instruction):
        self.code_box[position.y][position.x] = instruction

    def __str__(self):
        s = ""
        for line in self.code_box:
            for instruction in line:
                s += str(instruction)

        return s

class Stack:
    def __init__(self, stack=list()):
        self.stack = stack

    def append(self, item):
        self.stack.append(item)

    def pop(self, index=-1):
        return self.stack.pop(index)

    def peek(self, index=-1):
        return self.stack[index]

    def __len__(self):
        return len(self.stack)

    def __str__(self):
        return str(self.stack)


class Interpreter:
    def __init__(self, code_box):
        self.code_box = Codebox(code_box)
        self.dir = WEST
        self.position = Position()
        self.stack = Stack()
        self.input = None
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            instruction = self.get_current_instruction()

            try:
                instruction.handle(self)
            except Exception:
                self.argh()

            self.advance()
            if SLOW:
                time.sleep(0.01)

    def get_current_instruction(self):
        return self.code_box.get_instruction_at(self.position)

    def get_instruction_at(self, dir):
        return self.code_box.get_instruction_at(self.position + dir)

    def set_instruction_at(self, dir, instruction):
        self.code_box.set_instruction_at(self.position + dir, instruction)

    def advance(self):
        self.position += self.dir

    def turn_left(self):
        if self.dir == NORTH:
            self.dir = EAST
        elif self.dir == WEST:
            self.dir = NORTH
        elif self.dir == SOUTH:
            self.dir = WEST
        elif self.dir == EAST:
            self.dir = SOUTH

    def turn_right(self):
        if self.dir == NORTH:
            self.dir = WEST
        elif self.dir == WEST:
            self.dir = SOUTH
        elif self.dir == SOUTH:
            self.dir = EAST
        elif self.dir == EAST:
            self.dir = NORTH

    def argh(self):
        print(f"\nargh!!")
        sys.exit(1)

def usage(message):
    print(f"Error: {message}\n")
    print(f"Usage: {sys.argv[0]} <file>")
    sys.exit(1)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        usage("File not provided!")

    code_box = list()

    try:
        with open(sys.argv[1], 'r') as file:
            for line in file.readlines():
                code_box.append(list(line))
    except FileNotFoundError:
        usage("Input file not found!")

    interpreter = Interpreter(code_box)
    try:
        interpreter.run()
    except KeyboardInterrupt:
        print("\nUser exited!")
