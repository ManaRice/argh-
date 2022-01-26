use std::env;
use std::fs;
use std::process;
use std::cmp::max;
use std::io::{self, Write};
use std::ops::{Add, AddAssign};

#[derive(Clone, Copy)]
struct Position {
    x: i32,
    y: i32
}

impl Position {
    #[allow(dead_code)]
    pub fn to_string(&self) -> String {
        format!("x: {}, y: {}", self.x, self.y)
    }
}

impl AddAssign for Position {
    fn add_assign(&mut self, other: Self) {
        *self = Self {
            x: self.x + other.x,
            y: self.y + other.y,
        };
    }
}

impl Add<Direction> for Position {
    type Output = Self;
    fn add(self, other: Direction) -> Self{
        Self {
            x: self.x + other.xoff as i32,
            y: self.y + other.yoff as i32,
        }
    }
}

impl AddAssign<Direction> for Position {
    fn add_assign(&mut self, other: Direction) {
        *self = Self {
            x: self.x + other.xoff as i32,
            y: self.y + other.yoff as i32,
        };
    }
}

#[derive(Clone, Copy)]
struct Direction {
    xoff: i8,
    yoff: i8
}

impl Direction {
    pub const NORTH: Direction = { Direction { xoff:  0, yoff: -1 }};
    pub const SOUTH: Direction = { Direction { xoff:  0, yoff:  1 }};
    pub const WEST:  Direction = { Direction { xoff:  1, yoff:  0 }};
    pub const EAST:  Direction = { Direction { xoff: -1, yoff:  0 }};

    #[allow(dead_code)]
    pub fn to_string(&self) -> String {

        match (self.xoff, self.yoff) {
            ( 0, -1)  => String::from("North"),
            ( 0,  1)  => String::from("South"),
            ( 1,  0)  => String::from("West"),
            (-1,  0)  => String::from("East"),
            _         => String::from("NOT A VALID DIRECTION!")
        }
    }
}

struct Codebox {
    codebox: Vec<Vec<i32>>
}

impl Codebox {
    pub fn new(file_string: &String) -> Codebox {
        let mut new_codebox = Codebox { codebox: Vec::new() };

        let mut max_width: usize = 0;

        for line in file_string.lines() {

            let mut row = Vec::new();
            for c in line.chars() {

                row.push(c as i32);
            }
            max_width = max(max_width, row.len());
            new_codebox.codebox.push(row);
        }

        for line in new_codebox.codebox.iter_mut() {
            while line.len() < max_width {
                line.push(' ' as i32);
            }
        }

        new_codebox
    }

    pub fn get_instruction(&self, position: &Position) -> Option<&i32> {
        let row = self.codebox.get(position.y as usize);
        if row == None { return None }
        row.unwrap().get(position.x as usize)
    }

    pub fn set_instruction(&mut self, position: &Position, instruction: i32) -> Result<i8, i8> {
        let last_instruction = self.get_instruction(position);
        if last_instruction == None { return Err(1) }
        self.codebox[position.y as usize][position.x as usize] = instruction;
        Ok(0)
    }

    pub fn i32_as_char(val: i32) -> char {
        if val < 255 && val > 0 {
            return (val as u8) as char;
        }
        ' '
    }

    #[allow(dead_code)]
    pub fn to_string(&self) -> String {
        let mut s = String::from("");

        for lines in self.codebox.iter() {
            for c in lines.iter() {
                s.push(Codebox::i32_as_char(*c))
            }
            s.push('\n')
        }
        s
    }
}

struct Interpreter {
    codebox: Codebox,
    direction: Direction,
    position: Position,
    stack: Vec<i32>,
    input: Option<String>,
    running: bool
}

impl Interpreter {

    pub fn new(codebox: Codebox) -> Interpreter {
        Interpreter {
            codebox:   codebox,
            direction: Direction::WEST,
            position:  Position {x: 0, y: 0},
            stack:     Vec::new(),
            input:     None,
            running:   false,
        }
    }

    pub fn run(&mut self) {
        self.running = true;
        while self.running {
            let instruction = self.codebox.get_instruction(&self.position);

            if instruction == None {
                self.argh()
            }

            match Codebox::i32_as_char(*instruction.unwrap()) {
                'h' => self.r#move(Direction::EAST),
                'H' => self.move_until(Direction::EAST),
                'j' => self.r#move(Direction::SOUTH),
                'J' => self.move_until(Direction::SOUTH),
                'k' => self.r#move(Direction::NORTH),
                'K' => self.move_until(Direction::NORTH),
                'l' => self.r#move(Direction::WEST),
                'L' => self.move_until(Direction::WEST),
                'a' => self.stack_add(Direction::SOUTH),
                'A' => self.stack_add(Direction::NORTH),
                'r' => self.stack_reduce(Direction::SOUTH),
                'R' => self.stack_reduce(Direction::NORTH),
                'd' => self.stack_dupe(),
                'D' => self.stack_drop(),
                's' => self.stack_push(Direction::SOUTH),
                'S' => self.stack_push(Direction::NORTH),
                'f' => self.alter_codebox(Direction::SOUTH),
                'F' => self.alter_codebox(Direction::NORTH),
                'e' => self.place_eof(Direction::SOUTH),
                'E' => self.place_eof(Direction::NORTH),
                'g' => self.get_input(Direction::SOUTH),
                'G' => self.get_input(Direction::NORTH),
                'p' => self.print(Direction::SOUTH),
                'P' => self.print(Direction::NORTH),
                'x' => self.turn_right(),
                'X' => self.turn_left(),

                'q' => self.quit(),
                 _  => self.argh()
            }

            self.advance();
        }
    }

    fn advance(&mut self) {
        self.position += self.direction;
    }

    fn r#move(&mut self, direction: Direction) {
        self.direction = direction;
    }

    fn move_until(&mut self, direction: Direction) {
        self.r#move(direction);
        self.advance();
        let mut stack_last: Option<&i32>;
        let mut instruction: Option<&i32>;

        loop {
            stack_last = self.stack.last();
            instruction = self.codebox.get_instruction(&self.position);

            if stack_last == None || instruction == None {
                self.argh()
            }

            if stack_last.unwrap() == instruction.unwrap() {
                break;
            }

            self.advance();
        }
    }

    fn stack_add(&mut self, direction: Direction) {
        let instruction = self.codebox.get_instruction(&(self.position + direction));
        let stack_val = self.stack.pop();
        if instruction == None || stack_val == None { self.argh(); }
        self.stack.push(*instruction.unwrap() + stack_val.unwrap());
    }

    fn stack_reduce(&mut self, direction: Direction) {
        let instruction = self.codebox.get_instruction(&(self.position + direction));
        let stack_val = self.stack.pop();
        if instruction == None || stack_val == None { self.argh(); }
        self.stack.push(stack_val.unwrap() - instruction.unwrap());
    }

    fn stack_dupe(&mut self) {
        let instruction_opt = self.stack.last();
        if instruction_opt == None { self.argh(); }
        let instruction = *instruction_opt.unwrap();
        self.stack.push(instruction);
    }

    fn stack_drop(&mut self) {
        let instruction = self.stack.pop();
        if instruction == None { self.argh(); }
    }

    fn stack_push(&mut self, direction: Direction) {
        let instruction = self.codebox.get_instruction(&(self.position + direction));
        if instruction == None { self.argh(); }
        self.stack.push(*instruction.unwrap());
    }

    fn alter_codebox(&mut self, direction: Direction) {
        let instruction = self.stack.pop();
        if instruction == None { self.argh(); }
        let res = self.codebox.set_instruction(&(self.position + direction), instruction.unwrap());
        if res.is_err() { self.argh() }
    }

    fn place_eof(&mut self, direction: Direction) {
        let res = self.codebox.set_instruction(&(self.position + direction), 0);
        if res.is_err() { self.argh() }
    }

    fn get_input(&mut self, direction: Direction) {
        if self.input == None {
            let mut temp_string = String::new();
            let res = io::stdin().read_line(&mut temp_string);
            if res.is_err() { self.argh(); }
            temp_string.push('\0');
            self.input = Some(temp_string);
        }

        let character = self.input.as_ref().unwrap().chars().next();
        if character == None {
            self.input = None;
        }
        else {
            let res = self.codebox.set_instruction(&(self.position + direction), character.unwrap() as i32);
            if res.is_err() { self.argh() }
            self.input.as_mut().unwrap().remove(0);
        }
    }

    fn print(&self, direction: Direction) {
        let instruction = self.codebox.get_instruction(&(self.position + direction));
        if instruction == None { self.argh(); }
        print!("{}", Codebox::i32_as_char(*instruction.unwrap()));
        io::stdout().flush().unwrap();
    }

    fn turn_right(&mut self) {
        if *self.stack.last().unwrap() > 0 {
            match (self.direction.xoff, self.direction.yoff) {
                ( 0, -1)  => self.direction = Direction::WEST,
                ( 0,  1)  => self.direction = Direction::EAST,
                ( 1,  0)  => self.direction = Direction::SOUTH,
                (-1,  0)  => self.direction = Direction::NORTH,
                _         => self.argh()
            }
        }
    }

    fn turn_left(&mut self) {
        if *self.stack.last().unwrap() < 0 {
            match (self.direction.xoff, self.direction.yoff) {
                ( 0, -1)  => self.direction = Direction::EAST,
                ( 0,  1)  => self.direction = Direction::WEST,
                ( 1,  0)  => self.direction = Direction::NORTH,
                (-1,  0)  => self.direction = Direction::SOUTH,
                _         => self.argh()
            }
        }
    }

    fn quit(&mut self) {
        self.running = false;
    }

    fn argh(&self) {
        println!("\nAargh!!");
        process::exit(1);
    }

    #[allow(dead_code)]
    pub fn to_string(&self) -> String{
        format!(
            "{}\nPosition: {}\nDirection: {}",
            self.codebox.to_string(),
            self.position.to_string(),
            self.direction.to_string()
        )
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let filename = &args[1];

    let file_contents = fs::read_to_string(filename).expect("Could not load file!");

    let codebox = Codebox::new(&file_contents);

    let mut interpreter = Interpreter::new(codebox);

    interpreter.run();
}
