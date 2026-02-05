/**
 * Sample JavaScript module for testing the AI Code Documentation Generator.
 * 
 * This module demonstrates various JavaScript code patterns including
 * function declarations, arrow functions, classes, and async functions.
 */

/**
 * Calculate the sum of two numbers.
 * 
 * @param {number} a - The first number
 * @param {number} b - The second number
 * @returns {number} The sum of a and b
 */
function add(a, b) {
    return a + b;
}

/**
 * Calculate the product of two numbers.
 * 
 * @param {number} x - The first number
 * @param {number} y - The second number
 * @returns {number} The product of x and y
 */
const multiply = (x, y) => {
    return x * y;
};

/**
 * Check if a number is even.
 * 
 * @param {number} num - The number to check
 * @returns {boolean} True if the number is even, false otherwise
 */
const isEven = (num) => num % 2 === 0;

/**
 * Shopping cart management class.
 */
class ShoppingCart {
    /**
     * Create a new shopping cart.
     */
    constructor() {
        this.items = [];
        this.total = 0;
    }
    
    /**
     * Add an item to the cart.
     * 
     * @param {string} name - The item name
     * @param {number} price - The item price
     * @param {number} quantity - The quantity to add
     */
    addItem(name, price, quantity) {
        const item = {
            name: name,
            price: price,
            quantity: quantity,
            subtotal: price * quantity
        };
        this.items.push(item);
        this.total += item.subtotal;
    }
    
    /**
     * Remove an item from the cart by name.
     * 
     * @param {string} name - The name of the item to remove
     * @returns {boolean} True if item was removed, false if not found
     */
    removeItem(name) {
        const index = this.items.findIndex(item => item.name === name);
        if (index !== -1) {
            const item = this.items[index];
            this.total -= item.subtotal;
            this.items.splice(index, 1);
            return true;
        }
        return false;
    }
    
    /**
     * Get the total price of all items in the cart.
     * 
     * @returns {number} The total price
     */
    getTotal() {
        return this.total;
    }
    
    /**
     * Clear all items from the cart.
     */
    clear() {
        this.items = [];
        this.total = 0;
    }
}

/**
 * Fetch user data from an API.
 * 
 * @param {string} userId - The ID of the user to fetch
 * @returns {Promise<Object>} A promise that resolves to the user data
 */
async function fetchUserData(userId) {
    try {
        const response = await fetch(`https://api.example.com/users/${userId}`);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching user data:', error);
        throw error;
    }
}

/**
 * Process an array of items asynchronously.
 * 
 * @param {Array} items - The items to process
 * @param {Function} processor - Async function to process each item
 * @returns {Promise<Array>} A promise that resolves to the processed items
 */
const processItemsAsync = async (items, processor) => {
    const results = [];
    for (const item of items) {
        const result = await processor(item);
        results.push(result);
    }
    return results;
};

/**
 * Create a debounced version of a function.
 * 
 * @param {Function} func - The function to debounce
 * @param {number} delay - The delay in milliseconds
 * @returns {Function} The debounced function
 */
function debounce(func, delay) {
    let timeoutId;
    return function(...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => {
            func.apply(this, args);
        }, delay);
    };
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        add,
        multiply,
        isEven,
        ShoppingCart,
        fetchUserData,
        processItemsAsync,
        debounce
    };
}
