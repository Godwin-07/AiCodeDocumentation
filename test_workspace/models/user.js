/**
 * User model for the application.
 * 
 * This module defines the User class and related functions.
 */

/**
 * Represents a user in the system.
 */
class User {
    /**
     * Create a new User instance.
     * 
     * @param {string} id - The unique user ID
     * @param {string} username - The username
     * @param {string} email - The user's email address
     */
    constructor(id, username, email) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.createdAt = new Date();
        this.isActive = true;
    }
    
    /**
     * Activate the user account.
     */
    activate() {
        this.isActive = true;
    }
    
    /**
     * Deactivate the user account.
     */
    deactivate() {
        this.isActive = false;
    }
    
    /**
     * Get the user's display name.
     * 
     * @returns {string} The display name
     */
    getDisplayName() {
        return this.username;
    }
    
    /**
     * Convert the user to a JSON object.
     * 
     * @returns {Object} The user data as a plain object
     */
    toJSON() {
        return {
            id: this.id,
            username: this.username,
            email: this.email,
            createdAt: this.createdAt,
            isActive: this.isActive
        };
    }
}

/**
 * Validate user data before creating a user.
 * 
 * @param {Object} userData - The user data to validate
 * @returns {boolean} True if valid, false otherwise
 */
const validateUserData = (userData) => {
    if (!userData.username || userData.username.length < 3) {
        return false;
    }
    if (!userData.email || !userData.email.includes('@')) {
        return false;
    }
    return true;
};

/**
 * Create a new user from raw data.
 * 
 * @param {Object} data - The raw user data
 * @returns {User|null} A User instance or null if validation fails
 */
function createUser(data) {
    if (!validateUserData(data)) {
        return null;
    }
    return new User(data.id, data.username, data.email);
}

module.exports = {
    User,
    validateUserData,
    createUser
};
