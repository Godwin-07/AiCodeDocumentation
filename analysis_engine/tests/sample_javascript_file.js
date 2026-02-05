// Sample JavaScript file for testing the parser

/**
 * A simple greeting function
 * @param {string} name - The name to greet
 * @returns {string} The greeting message
 */
function greet(name) {
    return `Hello, ${name}!`;
}

// Add two numbers together
// This is a simple addition function
function add(a, b) {
    return a + b;
}

/**
 * Calculate the area of a rectangle
 */
const calculateArea = (width, height) => {
    return width * height;
};

// Arrow function with default parameter
const greetWithDefault = (name = "World") => {
    return `Hello, ${name}!`;
};

// Single parameter arrow function (no parentheses)
const square = x => x * x;

// Arrow function with rest parameters
const sum = (...numbers) => {
    return numbers.reduce((acc, num) => acc + num, 0);
};

/**
 * A calculator class for basic arithmetic operations
 */
class Calculator {
    /**
     * Constructor for Calculator
     */
    constructor() {
        this.result = 0;
    }

    /**
     * Add two numbers
     * @param {number} a - First number
     * @param {number} b - Second number
     */
    add(a, b) {
        this.result = a + b;
        return this.result;
    }

    // Subtract b from a
    subtract(a, b) {
        this.result = a - b;
        return this.result;
    }

    /**
     * Multiply two numbers
     */
    multiply(a, b) {
        this.result = a * b;
        return this.result;
    }

    // Get the current result
    getResult() {
        return this.result;
    }
}

// A simple user class
class User {
    constructor(name, email) {
        this.name = name;
        this.email = email;
    }

    // Get user info
    getInfo() {
        return `${this.name} (${this.email})`;
    }
}

// Function with complex parameters
function complexParams(a, b = 10, c = "default") {
    return { a, b, c };
}

/**
 * Async function example
 */
const fetchData = async (url) => {
    const response = await fetch(url);
    return response.json();
};
