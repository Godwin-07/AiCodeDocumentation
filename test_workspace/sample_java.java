/**
 * Sample Java file for testing the AI Code Documentation Generator.
 * 
 * This file demonstrates various Java code patterns including classes,
 * methods, constructors, and different access modifiers.
 */

package com.example.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * Represents a book in a library system.
 */
public class Book {
    private String title;
    private String author;
    private String isbn;
    private boolean isAvailable;
    
    /**
     * Create a new Book instance.
     * 
     * @param title The title of the book
     * @param author The author of the book
     * @param isbn The ISBN number of the book
     */
    public Book(String title, String author, String isbn) {
        this.title = title;
        this.author = author;
        this.isbn = isbn;
        this.isAvailable = true;
    }
    
    /**
     * Get the title of the book.
     * 
     * @return The book title
     */
    public String getTitle() {
        return title;
    }
    
    /**
     * Get the author of the book.
     * 
     * @return The book author
     */
    public String getAuthor() {
        return author;
    }
    
    /**
     * Get the ISBN of the book.
     * 
     * @return The book ISBN
     */
    public String getIsbn() {
        return isbn;
    }
    
    /**
     * Check if the book is available for checkout.
     * 
     * @return true if available, false otherwise
     */
    public boolean isAvailable() {
        return isAvailable;
    }
    
    /**
     * Mark the book as checked out.
     */
    public void checkout() {
        this.isAvailable = false;
    }
    
    /**
     * Mark the book as returned.
     */
    public void returnBook() {
        this.isAvailable = true;
    }
}

/**
 * Manages a collection of books in a library.
 */
class Library {
    private List<Book> books;
    private String name;
    
    /**
     * Create a new Library instance.
     * 
     * @param name The name of the library
     */
    public Library(String name) {
        this.name = name;
        this.books = new ArrayList<>();
    }
    
    /**
     * Add a book to the library collection.
     * 
     * @param book The book to add
     */
    public void addBook(Book book) {
        books.add(book);
    }
    
    /**
     * Remove a book from the library collection.
     * 
     * @param isbn The ISBN of the book to remove
     * @return true if the book was removed, false if not found
     */
    public boolean removeBook(String isbn) {
        return books.removeIf(book -> book.getIsbn().equals(isbn));
    }
    
    /**
     * Find a book by its ISBN.
     * 
     * @param isbn The ISBN to search for
     * @return The book if found, null otherwise
     */
    public Book findBookByIsbn(String isbn) {
        for (Book book : books) {
            if (book.getIsbn().equals(isbn)) {
                return book;
            }
        }
        return null;
    }
    
    /**
     * Find all books by a specific author.
     * 
     * @param author The author name to search for
     * @return A list of books by the author
     */
    public List<Book> findBooksByAuthor(String author) {
        List<Book> result = new ArrayList<>();
        for (Book book : books) {
            if (book.getAuthor().equalsIgnoreCase(author)) {
                result.add(book);
            }
        }
        return result;
    }
    
    /**
     * Get all available books in the library.
     * 
     * @return A list of available books
     */
    public List<Book> getAvailableBooks() {
        List<Book> available = new ArrayList<>();
        for (Book book : books) {
            if (book.isAvailable()) {
                available.add(book);
            }
        }
        return available;
    }
    
    /**
     * Get the total number of books in the library.
     * 
     * @return The total book count
     */
    public int getTotalBooks() {
        return books.size();
    }
    
    /**
     * Get the name of the library.
     * 
     * @return The library name
     */
    public String getName() {
        return name;
    }
}

/**
 * Utility class for string operations.
 */
class StringUtils {
    
    /**
     * Check if a string is null or empty.
     * 
     * @param str The string to check
     * @return true if the string is null or empty, false otherwise
     */
    public static boolean isEmpty(String str) {
        return str == null || str.trim().isEmpty();
    }
    
    /**
     * Capitalize the first letter of a string.
     * 
     * @param str The string to capitalize
     * @return The capitalized string
     */
    public static String capitalize(String str) {
        if (isEmpty(str)) {
            return str;
        }
        return str.substring(0, 1).toUpperCase() + str.substring(1).toLowerCase();
    }
    
    /**
     * Reverse a string.
     * 
     * @param str The string to reverse
     * @return The reversed string
     */
    public static String reverse(String str) {
        if (isEmpty(str)) {
            return str;
        }
        return new StringBuilder(str).reverse().toString();
    }
}
