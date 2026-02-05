/**
 * Sample Java file for testing the Java parser
 * This file contains various Java constructs to test parsing
 */
package com.example.test;

import java.util.List;
import java.util.Map;

/**
 * A simple calculator class for basic arithmetic operations
 * Demonstrates class parsing with JavaDoc comments
 */
public class Calculator {
    private int result;
    
    /**
     * Constructor to initialize the calculator
     */
    public Calculator() {
        this.result = 0;
    }
    
    /**
     * Add two integers and return the result
     * @param a First number to add
     * @param b Second number to add
     * @return The sum of a and b
     */
    public int add(int a, int b) {
        return a + b;
    }
    
    /**
     * Subtract b from a
     * @param a The number to subtract from
     * @param b The number to subtract
     * @return The difference
     */
    public int subtract(int a, int b) {
        return a - b;
    }
    
    // Simple method without JavaDoc
    private void reset() {
        this.result = 0;
    }
    
    /**
     * Calculate the sum of an array of numbers
     * @param numbers Array of integers to sum
     * @return The total sum
     */
    public static int sumArray(int[] numbers) {
        int sum = 0;
        for (int num : numbers) {
            sum += num;
        }
        return sum;
    }
    
    /**
     * Process a list of items with generic types
     * @param items List of string items
     * @param config Configuration map
     * @return Processed result
     */
    public String processItems(List<String> items, Map<String, Integer> config) {
        return "processed";
    }
}

/**
 * A utility class with static methods
 */
public class MathUtils {
    
    /**
     * Calculate the factorial of a number
     * @param n The number to calculate factorial for
     * @return The factorial result
     */
    public static long factorial(int n) {
        if (n <= 1) return 1;
        return n * factorial(n - 1);
    }
    
    // Method with varargs
    public static int max(int... numbers) {
        int maximum = Integer.MIN_VALUE;
        for (int num : numbers) {
            if (num > maximum) {
                maximum = num;
            }
        }
        return maximum;
    }
}

// Interface example
interface Drawable {
    void draw();
    void setColor(String color);
}

// Abstract class example
abstract class Shape implements Drawable {
    protected String color;
    
    public abstract double getArea();
    
    public void setColor(String color) {
        this.color = color;
    }
}